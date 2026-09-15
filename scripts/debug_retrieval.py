import asyncio
import traceback
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from apps.api.src.core.config import settings
from apps.api.src.services.retrieval.engine import HybridRetrievalEngine


async def test():
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession)
    async with session_factory() as session:
        re = HybridRetrievalEngine(db_session=session)
        try:
            res = await re.search("product-led growth", top_k=2)
            print("SEARCH RESULT TOTAL:", res.total_results)
            for r in res.results:
                print(r.chunk_id, r.semantic_score, r.lexical_score, r.rrf_score)
        except Exception as e:
            traceback.print_exc()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test())
