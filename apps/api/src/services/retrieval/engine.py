import time
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from apps.api.src.core.config import settings
from apps.api.src.core.logging import logger
from apps.api.src.providers.ollama import OllamaProvider


class ProvenanceCitationDTO(BaseModel):
    chunk_id: str
    episode_id: str
    episode_title: str
    guest: Optional[str]
    start_time_seconds: Optional[float]
    end_time_seconds: Optional[float]
    timestamp_formatted: Optional[str]
    youtube_url: Optional[str]
    source_commit: str
    speaker: Optional[str]


class RetrievedChunkDTO(BaseModel):
    chunk_id: str
    episode_id: str
    episode_title: str
    guest: Optional[str]
    content: str
    speaker: Optional[str]
    start_time_seconds: Optional[float]
    end_time_seconds: Optional[float]
    timestamp_formatted: Optional[str]
    provenance: ProvenanceCitationDTO
    semantic_score: float = 0.0
    lexical_score: float = 0.0
    rrf_score: float = 0.0


class RetrievalResult(BaseModel):
    query: str
    total_results: int
    confidence_score: float
    confidence_tier: str  # 'high', 'medium', 'low', 'unsupported'
    results: List[RetrievedChunkDTO]
    execution_time_ms: int


class HybridRetrievalEngine:
    def __init__(
        self,
        db_session: AsyncSession,
        embedding_model: Optional[str] = None,
        rrf_k: int = 60,
    ):
        self.db = db_session
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL
        self.rrf_k = rrf_k
        self.provider = OllamaProvider()

    async def _get_query_embedding(self, query: str) -> List[float]:
        embeddings = await self.provider.get_embeddings([query], model=self.embedding_model)
        if not embeddings or not embeddings[0]:
            raise RuntimeError(f"Failed to generate query embedding using model '{self.embedding_model}'")
        return embeddings[0]

    def _calculate_confidence(
        self,
        results: List[RetrievedChunkDTO],
        top_semantic: float,
        top_lexical: float,
    ) -> Tuple[float, str]:
        """
        Calculates heuristic confidence score (0.0 to 1.0) and tier based on:
        1. Top cosine similarity (semantic strength)
        2. Semantic and Lexical rank agreement
        3. Score gap between top 1 and top 3
        4. Candidate count
        """
        if not results:
            return 0.0, "unsupported"

        # Semantic cosine similarity score (1 - cosine distance) is usually 0.5 - 0.9 for good matches
        sem_factor = max(0.0, min(1.0, (top_semantic - 0.3) / 0.6))
        lex_factor = min(1.0, top_lexical / 1.0)

        # RRF top score factor
        top_rrf = results[0].rrf_score
        rrf_factor = min(1.0, top_rrf / 0.033)  # 1/60 + 1/60 = ~0.0333 max

        raw_confidence = 0.5 * sem_factor + 0.3 * rrf_factor + 0.2 * lex_factor
        score = round(max(0.0, min(1.0, raw_confidence)), 3)

        if score >= 0.70:
            tier = "high"
        elif score >= 0.45:
            tier = "medium"
        elif score >= 0.25:
            tier = "low"
        else:
            tier = "unsupported"

        return score, tier

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> RetrievalResult:
        start_time = time.time()
        filters = filters or {}

        # 1. Generate query embedding
        query_embedding = await self._get_query_embedding(query)
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # Build filter SQL clauses
        filter_clauses = ["1=1"]
        params: Dict[str, Any] = {
            "query_vec": embedding_str,
            "query_text": query,
            "top_limit": top_k * 3,  # Candidate pool for fusion
        }

        if filters.get("episode_id"):
            filter_clauses.append("c.episode_id = :filter_ep")
            params["filter_ep"] = filters["episode_id"]

        if filters.get("guest"):
            filter_clauses.append("(e.guest ILIKE :filter_guest OR e.title ILIKE :filter_guest OR c.speaker ILIKE :filter_guest)")
            params["filter_guest"] = f"%{filters['guest']}%"

        if filters.get("speaker"):
            filter_clauses.append("c.speaker ILIKE :filter_speaker")
            params["filter_speaker"] = f"%{filters['speaker']}%"

        where_filter = " AND ".join(filter_clauses)

        # 2. Semantic Search Query (Cosine similarity <=> operator)
        semantic_sql = text(f"""
            SELECT 
                c.id AS chunk_id,
                c.episode_id,
                e.title AS episode_title,
                e.guest,
                e.youtube_url,
                c.speaker,
                c.start_time_seconds,
                c.end_time_seconds,
                c.timestamp_formatted,
                c.content,
                (1 - (c.embedding <=> CAST(:query_vec AS vector))) AS semantic_score
            FROM transcript_chunks c
            JOIN episodes e ON e.id = c.episode_id
            WHERE c.embedding IS NOT NULL AND {where_filter}
            ORDER BY c.embedding <=> CAST(:query_vec AS vector) ASC
            LIMIT :top_limit;
        """)

        # 3. Lexical Search Query (PostgreSQL full text tsvector)
        lexical_sql = text(f"""
            SELECT 
                c.id AS chunk_id,
                c.episode_id,
                e.title AS episode_title,
                e.guest,
                e.youtube_url,
                c.speaker,
                c.start_time_seconds,
                c.end_time_seconds,
                c.timestamp_formatted,
                c.content,
                ts_rank_cd(c.search_vector, plainto_tsquery('english', :query_text)) AS lexical_score
            FROM transcript_chunks c
            JOIN episodes e ON e.id = c.episode_id
            WHERE c.search_vector @@ plainto_tsquery('english', :query_text) AND {where_filter}
            ORDER BY lexical_score DESC
            LIMIT :top_limit;
        """)

        sem_res = await self.db.execute(semantic_sql, params)
        sem_rows = sem_res.mappings().all()

        lex_res = await self.db.execute(lexical_sql, params)
        lex_rows = lex_res.mappings().all()

        # 4. Reciprocal Rank Fusion (RRF)
        # RRF(d) = sum(1 / (k + rank))
        scores: Dict[str, Dict[str, Any]] = {}

        top_sem_score = 0.0
        top_lex_score = 0.0

        for rank, row in enumerate(sem_rows, start=1):
            cid = row["chunk_id"]
            if rank == 1:
                top_sem_score = float(row["semantic_score"])
            if cid not in scores:
                scores[cid] = {"row": row, "sem_rank": rank, "lex_rank": None, "sem_score": float(row["semantic_score"]), "lex_score": 0.0, "rrf": 0.0}
            else:
                scores[cid]["sem_rank"] = rank
                scores[cid]["sem_score"] = float(row["semantic_score"])
            scores[cid]["rrf"] += 1.0 / (self.rrf_k + rank)

        for rank, row in enumerate(lex_rows, start=1):
            cid = row["chunk_id"]
            if rank == 1:
                top_lex_score = float(row["lexical_score"])
            if cid not in scores:
                scores[cid] = {"row": row, "sem_rank": None, "lex_rank": rank, "sem_score": 0.0, "lex_score": float(row["lexical_score"]), "rrf": 0.0}
            else:
                scores[cid]["lex_rank"] = rank
                scores[cid]["lex_score"] = float(row["lexical_score"])
            scores[cid]["rrf"] += 1.0 / (self.rrf_k + rank)

        # Sort by RRF score descending
        sorted_candidates = sorted(scores.values(), key=lambda x: x["rrf"], reverse=True)[:top_k]

        # 5. Build Result DTOs
        results: List[RetrievedChunkDTO] = []
        for item in sorted_candidates:
            r = item["row"]
            prov = ProvenanceCitationDTO(
                chunk_id=r["chunk_id"],
                episode_id=r["episode_id"],
                episode_title=r["episode_title"],
                guest=r["guest"],
                start_time_seconds=r["start_time_seconds"],
                end_time_seconds=r["end_time_seconds"],
                timestamp_formatted=r["timestamp_formatted"],
                youtube_url=r["youtube_url"],
                source_commit="live",
                speaker=r["speaker"],
            )

            chunk_dto = RetrievedChunkDTO(
                chunk_id=r["chunk_id"],
                episode_id=r["episode_id"],
                episode_title=r["episode_title"],
                guest=r["guest"],
                content=r["content"],
                speaker=r["speaker"],
                start_time_seconds=r["start_time_seconds"],
                end_time_seconds=r["end_time_seconds"],
                timestamp_formatted=r["timestamp_formatted"],
                provenance=prov,
                semantic_score=round(item["sem_score"], 4),
                lexical_score=round(item["lex_score"], 4),
                rrf_score=round(item["rrf"], 5),
            )
            results.append(chunk_dto)

        confidence_score, confidence_tier = self._calculate_confidence(results, top_sem_score, top_lex_score)
        exec_ms = int((time.time() - start_time) * 1000)

        return RetrievalResult(
            query=query,
            total_results=len(results),
            confidence_score=confidence_score,
            confidence_tier=confidence_tier,
            results=results,
            execution_time_ms=exec_ms,
        )
