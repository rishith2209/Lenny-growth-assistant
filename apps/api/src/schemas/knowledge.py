from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProvenanceCitation(BaseModel):
    chunk_id: str
    episode_id: str
    episode_title: str
    guest: Optional[str] = None
    start_time_seconds: Optional[float] = None
    end_time_seconds: Optional[float] = None
    timestamp_formatted: Optional[str] = None
    youtube_url: Optional[str] = None
    source_commit: str = "main"
    speaker: Optional[str] = None


class RetrievedChunkResponse(BaseModel):
    chunk_id: str
    episode_id: str
    episode_title: str
    guest: Optional[str] = None
    content: str
    speaker: Optional[str] = None
    start_time_seconds: Optional[float] = None
    end_time_seconds: Optional[float] = None
    timestamp_formatted: Optional[str] = None
    provenance: ProvenanceCitation
    semantic_score: float
    lexical_score: float
    rrf_score: float


class KnowledgeSearchFilters(BaseModel):
    episode_id: Optional[str] = None
    guest: Optional[str] = None
    speaker: Optional[str] = None


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="The search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to return")
    filters: Optional[KnowledgeSearchFilters] = None


class KnowledgeSearchResponse(BaseModel):
    query: str
    total_results: int
    confidence_score: float
    confidence_tier: str  # 'high', 'medium', 'low', 'unsupported'
    results: List[RetrievedChunkResponse]
    execution_time_ms: int
