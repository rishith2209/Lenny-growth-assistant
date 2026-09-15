import asyncio
from apps.api.src.db.session import AsyncSessionLocal
from apps.api.src.db.models import Episode, TranscriptChunk, IngestionRun
from sqlalchemy import select, func

async def check():
    async with AsyncSessionLocal() as session:
        ep_count = (await session.execute(select(func.count(Episode.id)))).scalar()
        ch_count = (await session.execute(select(func.count(TranscriptChunk.id)))).scalar()
        runs = (await session.execute(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(3))).scalars().all()
        print(f"Total Episodes in DB: {ep_count}")
        print(f"Total Chunks in DB: {ch_count}")
        for r in runs:
            print(f"Run {r.id}: status={r.status}, episodes={r.episode_count}, chunks={r.chunk_count}, started={r.started_at}, finished={r.finished_at}")

if __name__ == "__main__":
    asyncio.run(check())
