import pytest
import uuid
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from apps.api.src.core.config import settings
from apps.api.src.db.models import Episode, TranscriptChunk
from apps.api.src.services.retrieval.engine import HybridRetrievalEngine
from apps.api.src.providers.ollama import OllamaProvider


@pytest.mark.asyncio
async def test_postgres_pgvector_hybrid_retrieval_integration():
    """
    Real integration test executing:
    1. Database connectivity & vector extension check
    2. Real vector embedding generation via Ollama (nomic-embed-text)
    3. Database record insertion (Episode + TranscriptChunks)
    4. pgvector cosine similarity search (<=>)
    5. tsvector lexical search (@@ plainto_tsquery)
    6. Reciprocal Rank Fusion (RRF) calculation
    7. Metadata filtering
    8. Tear-down cleanup
    """
    # Create test engine bound to the current async test event loop
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # 1. Check DB & Extension
        ext_check = await session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';"))
        ext = ext_check.scalar()
        assert ext == "vector", "pgvector extension must be installed and active"

        test_ep_id = f"test_ep_{uuid.uuid4().hex[:8]}"
        provider = OllamaProvider()

        # Clean up any leftover test episodes
        await session.execute(delete(Episode).where(Episode.id.like("test_ep_%")))
        await session.commit()

        # 2. Generate real embeddings via Ollama nomic-embed-text
        chunk1_text = f"Elena Verna: B2B product-led growth relies heavily on self-serve product loops and activation metrics. unique_{test_ep_id}"
        chunk2_text = f"Andy Johns: Sustainable growth comes from retention and expansion rather than top of funnel acquisition. unique_{test_ep_id}"

        embeddings = await provider.get_embeddings([chunk1_text, chunk2_text], model="nomic-embed-text")
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 768, "nomic-embed-text must produce 768-dimensional vectors"

        try:
            # 3. Insert test episode
            test_ep = Episode(
                id=test_ep_id,
                slug=test_ep_id,
                title="Integration Test Episode on Product-Led Growth and Retention",
                guest="Elena Verna",
                youtube_url="https://youtube.com/watch?v=integration_test",
                channel="Lenny's Podcast",
            )
            session.add(test_ep)

            # Insert test chunks with real embeddings
            c1 = TranscriptChunk(
                id=f"{test_ep_id}_0000",
                episode_id=test_ep_id,
                chunk_index=0,
                speaker="Elena Verna",
                start_time_seconds=10.0,
                end_time_seconds=45.0,
                timestamp_formatted="00:10",
                content=chunk1_text,
                content_hash=f"hash_1_{uuid.uuid4().hex}",
                token_count=25,
                embedding_model="nomic-embed-text",
                embedding=embeddings[0],
            )
            c2 = TranscriptChunk(
                id=f"{test_ep_id}_0001",
                episode_id=test_ep_id,
                chunk_index=1,
                speaker="Andy Johns",
                start_time_seconds=50.0,
                end_time_seconds=95.0,
                timestamp_formatted="00:50",
                content=chunk2_text,
                content_hash=f"hash_2_{uuid.uuid4().hex}",
                token_count=22,
                embedding_model="nomic-embed-text",
                embedding=embeddings[1],
            )
            session.add_all([c1, c2])
            await session.commit()

            # 4. Execute Hybrid Retrieval Engine
            retrieval_engine = HybridRetrievalEngine(db_session=session, embedding_model="nomic-embed-text")

            # Query A: Target PLG / Self-serve
            res_plg = await retrieval_engine.search(query="How does self-serve product-led growth work?", top_k=2)
            assert res_plg.total_results > 0
            top_plg = res_plg.results[0]
            assert top_plg.episode_id == test_ep_id
            assert top_plg.provenance.guest == "Elena Verna"
            assert top_plg.provenance.timestamp_formatted == "00:10"
            assert top_plg.semantic_score > 0.5
            assert top_plg.rrf_score > 0.0

            # Query B: Test metadata filtering
            res_filtered = await retrieval_engine.search(
                query="growth metrics",
                top_k=2,
                filters={"guest": "Elena Verna"},
            )
            assert len(res_filtered.results) > 0
            for r in res_filtered.results:
                assert r.guest == "Elena Verna"

        finally:
            # 8. Clean up test records
            await session.execute(delete(Episode).where(Episode.id == test_ep_id))
            await session.commit()

    await engine.dispose()
