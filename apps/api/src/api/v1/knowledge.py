from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.db.session import get_db
from apps.api.src.schemas.knowledge import KnowledgeSearchRequest, KnowledgeSearchResponse
from apps.api.src.services.retrieval.engine import HybridRetrievalEngine
from apps.api.src.core.logging import logger

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge & Retrieval"])


@router.post("/search", response_model=KnowledgeSearchResponse, summary="Hybrid RAG Search over Lenny's Podcast Transcripts")
async def search_knowledge(
    request: KnowledgeSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Executes a hybrid retrieval query over podcast transcripts using:
    - Cosine vector similarity via pgvector
    - Full-text search via PostgreSQL tsvector
    - Reciprocal Rank Fusion (RRF)
    - Metadata filtering and citation provenance
    """
    try:
        engine = HybridRetrievalEngine(db_session=db)
        filters_dict = request.filters.model_dump(exclude_none=True) if request.filters else {}
        result = await engine.search(
            query=request.query,
            top_k=request.top_k,
            filters=filters_dict,
        )
        return result
    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge retrieval failed: {str(e)}",
        )
