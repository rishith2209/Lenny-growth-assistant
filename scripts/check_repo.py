import os
import asyncio
from apps.api.src.db.session import AsyncSessionLocal
from apps.api.src.services.ingestion.pipeline import IngestionPipeline

async def main():
    async with AsyncSessionLocal() as session:
        pipeline = IngestionPipeline(session)
        repo_path, commit_sha = pipeline.fetch_or_clone_repo()
        print(f"Repo path: {repo_path}, Commit: {commit_sha}")
        discovered = pipeline.discover_episodes(repo_path)
        print(f"Total discovered files: {len(discovered)}")
        for slug, t_path, m_path in discovered[:5]:
            print(f"Slug: {slug} | File: {t_path} | Meta: {m_path}")
        
        # Check why any slug is 'transcript'
        transcript_slugs = [d for d in discovered if d[0] == "transcript"]
        print(f"Slugs named 'transcript': {len(transcript_slugs)}")
        for item in transcript_slugs[:5]:
            print(item)

if __name__ == "__main__":
    asyncio.run(main())
