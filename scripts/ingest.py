import asyncio
import argparse
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.api.src.db.session import AsyncSessionLocal
from apps.api.src.services.ingestion.pipeline import IngestionPipeline
from apps.api.src.core.logging import logger


async def main():
    parser = argparse.ArgumentParser(description="Lenny Growth Assistant — Podcast Ingestion Pipeline")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of episodes to ingest (for testing)")
    parser.add_argument("--force", action="store_true", help="Force re-ingestion even if commit matches")
    parser.add_argument("--repo", type=str, default=None, help="Custom repository URL or path")
    parser.add_argument("--model", type=str, default=None, help="Embedding model name")
    args = parser.parse_args()

    print("=" * 70)
    print(" LENNY GROWTH ASSISTANT — PODCAST INGESTION PIPELINE")
    print("=" * 70)

    async with AsyncSessionLocal() as session:
        pipeline = IngestionPipeline(
            db_session=session,
            source_repo=args.repo,
            embedding_model=args.model,
        )

        try:
            print(f"Starting ingestion (limit={args.limit}, force={args.force})...")
            run = await pipeline.run(limit=args.limit, force=args.force)
            print("\n" + "=" * 70)
            print(" INGESTION RUN COMPLETED")
            print("=" * 70)
            print(f"Run ID:        {run.id}")
            print(f"Commit SHA:    {run.commit_sha}")
            print(f"Status:        {run.status}")
            print(f"Episodes:      {run.episode_count}")
            print(f"Chunks:        {run.chunk_count}")
            print(f"Embed Model:   {run.embedding_model}")
            if run.error_summary:
                print(f"Notes/Errors:  {run.error_summary}")
            print("=" * 70)
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
