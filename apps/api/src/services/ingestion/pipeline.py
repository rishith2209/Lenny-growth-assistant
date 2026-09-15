import os
import re
import json
import uuid
import tempfile
import git
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.core.config import settings
from apps.api.src.core.logging import logger
from apps.api.src.db.models import Episode, TranscriptChunk, IngestionRun, utcnow
from apps.api.src.services.ingestion.parser import TranscriptParser, ParsedEpisode
from apps.api.src.services.ingestion.chunker import SpeakerAwareChunker, TranscriptChunkDTO
from apps.api.src.services.ingestion.embedder import IngestionEmbedder


class IngestionPipeline:
    def __init__(
        self,
        db_session: AsyncSession,
        source_repo: Optional[str] = None,
        cache_dir: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        self.db = db_session
        self.source_repo = source_repo or settings.TRANSCRIPT_SOURCE_REPO
        self.cache_dir = cache_dir or settings.TRANSCRIPT_CACHE_DIR
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL
        self.parser = TranscriptParser()
        self.chunker = SpeakerAwareChunker()
        self.embedder = IngestionEmbedder(model=self.embedding_model)

    def fetch_or_clone_repo(self) -> Tuple[str, str]:
        """
        Clones or fetches the transcripts repository to a local cache directory.
        Returns: (local_repo_path, head_commit_sha)
        """
        os.makedirs(self.cache_dir, exist_ok=True)
        repo_path = os.path.join(self.cache_dir, "lennys-podcast-transcripts")

        if os.path.exists(os.path.join(repo_path, ".git")):
            logger.info(f"Fetching latest changes from {self.source_repo}...")
            repo = git.Repo(repo_path)
            try:
                repo.remotes.origin.fetch()
                repo.git.checkout("HEAD")
            except Exception as e:
                logger.warning(f"Could not fetch remote, using cached HEAD: {e}")
        else:
            logger.info(f"Cloning {self.source_repo} into {repo_path} (shallow clone)...")
            repo = git.Repo.clone_from(
                self.source_repo,
                repo_path,
                depth=1,
                no_single_branch=False,
            )

        head_commit = repo.head.commit.hexsha
        logger.info(f"Repository HEAD commit is {head_commit}")
        return repo_path, head_commit

    def discover_episodes(self, repo_path: str) -> List[Tuple[str, str, Optional[str]]]:
        """
        Dynamically discovers episode transcripts and metadata.
        Returns list of (slug, transcript_file_path, optional_metadata_file_path).
        """
        episodes_dir = os.path.join(repo_path, "episodes")
        discovered: List[Tuple[str, str, Optional[str]]] = []

        if not os.path.exists(episodes_dir):
            # Fallback: scan root directory if structure differs
            episodes_dir = repo_path

        for root, dirs, files in os.walk(episodes_dir):
            for file in files:
                if file.endswith(".md") or file.endswith(".txt"):
                    # Ignore root README.md or LICENSE files
                    if file.lower() in ["readme.md", "license", "license.md", "contributing.md"]:
                        continue

                    transcript_path = os.path.join(root, file)
                    base_name = os.path.splitext(file)[0]
                    # If file is inside an episode folder (e.g. episodes/elena-verna/transcript.md)
                    if base_name.lower() in ["transcript", "content"] and root != episodes_dir:
                        slug = os.path.basename(root)
                    else:
                        slug = base_name

                    # Check for matching JSON sidecar in same dir
                    json_path = os.path.join(root, f"{base_name}.json")
                    if not os.path.exists(json_path):
                        json_path = os.path.join(root, "metadata.json")
                    meta_path = json_path if os.path.exists(json_path) else None

                    discovered.append((slug, transcript_path, meta_path))

        logger.info(f"Dynamically discovered {len(discovered)} episode transcripts.")
        return discovered

    async def is_already_ingested(self, commit_sha: str) -> bool:
        """Check if this commit has already been successfully ingested (Idempotency check)."""
        result = await self.db.execute(
            select(IngestionRun).where(
                IngestionRun.commit_sha == commit_sha,
                IngestionRun.status == "completed",
                IngestionRun.embedding_model == self.embedding_model,
            )
        )
        return result.scalar_one_or_none() is not None

    async def run(
        self,
        limit: Optional[int] = None,
        force: bool = False,
    ) -> IngestionRun:
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        started_at = utcnow()

        repo_path, commit_sha = self.fetch_or_clone_repo()

        # Idempotency check
        if not force and await self.is_already_ingested(commit_sha):
            logger.info(f"Commit {commit_sha} is already ingested with model {self.embedding_model}. Skipping.")
            run = IngestionRun(
                id=run_id,
                source_url=self.source_repo,
                commit_sha=commit_sha,
                status="completed",
                error_summary="Skipped: already ingested (idempotent)",
                started_at=started_at,
                finished_at=utcnow(),
            )
            return run

        # Create running record
        ingestion_run = IngestionRun(
            id=run_id,
            source_url=self.source_repo,
            commit_sha=commit_sha,
            status="running",
            embedding_model=self.embedding_model,
            started_at=started_at,
        )
        self.db.add(ingestion_run)
        await self.db.commit()

        discovered = self.discover_episodes(repo_path)
        if limit:
            discovered = discovered[:limit]

        total_episodes_saved = 0
        total_chunks_saved = 0
        errors: List[str] = []

        try:
            for slug, transcript_path, meta_path in discovered:
                try:
                    with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
                        transcript_text = f.read()

                    meta_dict: Dict = {}
                    if meta_path and os.path.exists(meta_path):
                        with open(meta_path, "r", encoding="utf-8", errors="replace") as f:
                            meta_dict = self.parser.parse_metadata_file(f.read())

                    parsed_episode = self.parser.parse_episode(slug, transcript_text, meta_dict)
                    chunks = self.chunker.chunk_episode(parsed_episode)

                    if not chunks:
                        continue

                    # Generate vector embeddings in batch
                    chunk_texts = [c.content for c in chunks]
                    embeddings = await self.embedder.embed_chunks(chunk_texts)

                    # Upsert Episode record
                    existing_ep = await self.db.get(Episode, parsed_episode.id)
                    if existing_ep:
                        existing_ep.title = parsed_episode.title
                        existing_ep.guest = parsed_episode.guest
                        existing_ep.description = parsed_episode.description
                        existing_ep.youtube_url = parsed_episode.youtube_url
                        existing_ep.video_id = parsed_episode.video_id
                        existing_ep.publish_date = parsed_episode.publish_date
                        existing_ep.duration_seconds = parsed_episode.duration_seconds
                        existing_ep.raw_metadata = parsed_episode.raw_metadata
                    else:
                        ep = Episode(
                            id=parsed_episode.id,
                            slug=parsed_episode.slug,
                            title=parsed_episode.title,
                            guest=parsed_episode.guest,
                            youtube_url=parsed_episode.youtube_url,
                            video_id=parsed_episode.video_id,
                            publish_date=parsed_episode.publish_date,
                            duration_seconds=parsed_episode.duration_seconds,
                            description=parsed_episode.description,
                            channel=parsed_episode.channel,
                            view_count=parsed_episode.view_count,
                            keywords=parsed_episode.keywords,
                            raw_metadata=parsed_episode.raw_metadata,
                        )
                        self.db.add(ep)

                    # Replace chunks for this episode cleanly
                    await self.db.execute(delete(TranscriptChunk).where(TranscriptChunk.episode_id == parsed_episode.id))

                    for chunk_dto, emb in zip(chunks, embeddings):
                        chunk_record = TranscriptChunk(
                            id=chunk_dto.id,
                            episode_id=parsed_episode.id,
                            chunk_index=chunk_dto.chunk_index,
                            speaker=chunk_dto.speaker,
                            start_time_seconds=chunk_dto.start_time_seconds,
                            end_time_seconds=chunk_dto.end_time_seconds,
                            timestamp_formatted=chunk_dto.timestamp_formatted,
                            content=chunk_dto.content,
                            content_hash=chunk_dto.content_hash,
                            token_count=chunk_dto.token_count,
                            metadata_=chunk_dto.metadata,
                            embedding_model=self.embedding_model,
                            embedding=emb,
                        )
                        self.db.add(chunk_record)

                    await self.db.commit()
                    total_episodes_saved += 1
                    total_chunks_saved += len(chunks)
                    logger.info(f"Ingested episode '{parsed_episode.title}' ({len(chunks)} chunks).")

                except Exception as ep_err:
                    await self.db.rollback()
                    err_msg = f"Error ingesting episode '{slug}': {ep_err}"
                    logger.error(err_msg)
                    errors.append(err_msg)

            # Update final run record
            final_status = "completed" if not errors else ("completed_with_errors" if total_episodes_saved > 0 else "failed")
            ingestion_run.status = final_status
            ingestion_run.episode_count = total_episodes_saved
            ingestion_run.chunk_count = total_chunks_saved
            ingestion_run.error_summary = "\n".join(errors) if errors else None
            ingestion_run.finished_at = utcnow()
            await self.db.commit()

            return ingestion_run

        except Exception as e:
            await self.db.rollback()
            ingestion_run.status = "failed"
            ingestion_run.error_summary = str(e)
            ingestion_run.finished_at = utcnow()
            await self.db.commit()
            raise
