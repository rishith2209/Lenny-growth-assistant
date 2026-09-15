"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-14 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. Episodes table
    op.create_table(
        "episodes",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("slug", sa.String(length=256), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("guest", sa.String(length=256), nullable=True),
        sa.Column("youtube_url", sa.String(length=512), nullable=True),
        sa.Column("video_id", sa.String(length=64), nullable=True),
        sa.Column("publish_date", sa.String(length=64), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("channel", sa.String(length=256), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("raw_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_episodes_slug", "episodes", ["slug"], unique=True)
    op.create_index("ix_episodes_guest", "episodes", ["guest"])
    op.create_index("ix_episodes_publish_date", "episodes", ["publish_date"])
    op.create_index("ix_episodes_video_id", "episodes", ["video_id"])

    # 2. Transcript Chunks table
    op.create_table(
        "transcript_chunks",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("episode_id", sa.String(length=128), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("speaker", sa.String(length=256), nullable=True),
        sa.Column("start_time_seconds", sa.Float(), nullable=True),
        sa.Column("end_time_seconds", sa.Float(), nullable=True),
        sa.Column("timestamp_formatted", sa.String(length=32), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("embedding_model", sa.String(length=128), nullable=False, server_default="nomic-embed-text"),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', content)", persisted=True),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("episode_id", "chunk_index", name="uq_episode_chunk_index"),
    )
    op.create_index("ix_transcript_chunks_episode_id", "transcript_chunks", ["episode_id"])
    op.create_index("ix_transcript_chunks_speaker", "transcript_chunks", ["speaker"])
    op.create_index("ix_transcript_chunks_content_hash", "transcript_chunks", ["content_hash"])
    op.create_index("ix_chunks_search_vector", "transcript_chunks", ["search_vector"], postgresql_using="gin")
    op.create_index("ix_chunks_speaker_episode", "transcript_chunks", ["episode_id", "speaker"])

    # HNSW vector index for cosine distance
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw ON transcript_chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);"
    )

    # 3. Ingestion Runs table
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="running"),
        sa.Column("episode_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding_model", sa.String(length=128), nullable=False, server_default="nomic-embed-text"),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=False, server_default="768"),
        sa.Column("pipeline_version", sa.String(length=32), nullable=False, server_default="1.0.0"),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_runs_commit_sha", "ingestion_runs", ["commit_sha"])

    # 4. Sessions table
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=True),
        sa.Column("user_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("provider", sa.String(length=64), nullable=False, server_default="ollama"),
        sa.Column("model", sa.String(length=64), nullable=False, server_default="llama3.1:8b"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # 5. Messages table
    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=64), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("cost_inr", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_session_id", "messages", ["session_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("sessions")
    op.drop_table("ingestion_runs")
    op.drop_table("transcript_chunks")
    op.drop_table("episodes")
    op.execute("DROP EXTENSION IF EXISTS vector;")
