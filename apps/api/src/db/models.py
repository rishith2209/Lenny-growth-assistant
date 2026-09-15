import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    UniqueConstraint,
    Computed,
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(String(128), primary_key=True)  # e.g., slug / directory name
    slug = Column(String(256), unique=True, nullable=False, index=True)
    title = Column(String(512), nullable=False)
    guest = Column(String(256), nullable=True, index=True)
    youtube_url = Column(String(512), nullable=True)
    video_id = Column(String(64), nullable=True, index=True)
    publish_date = Column(String(64), nullable=True, index=True)
    duration_seconds = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    channel = Column(String(256), nullable=True)
    view_count = Column(Integer, nullable=True)
    keywords = Column(JSON, nullable=True)
    raw_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    chunks = relationship("TranscriptChunk", back_populates="episode", cascade="all, delete-orphan")


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id = Column(String(128), primary_key=True)  # e.g., {episode_id}_{chunk_index}
    episode_id = Column(String(128), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    speaker = Column(String(256), nullable=True, index=True)
    start_time_seconds = Column(Float, nullable=True)
    end_time_seconds = Column(Float, nullable=True)
    timestamp_formatted = Column(String(32), nullable=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    token_count = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    embedding_model = Column(String(128), nullable=False, default="nomic-embed-text")
    embedding = Column(Vector(768), nullable=True)
    search_vector = Column(
        TSVECTOR,
        Computed("to_tsvector('english', content)", persisted=True),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    episode = relationship("Episode", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("episode_id", "chunk_index", name="uq_episode_chunk_index"),
        Index("ix_chunks_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_chunks_speaker_episode", "episode_id", "speaker"),
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_url = Column(String(512), nullable=False)
    commit_sha = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="running")  # running, completed, completed_with_errors, failed
    episode_count = Column(Integer, nullable=False, default=0)
    chunk_count = Column(Integer, nullable=False, default=0)
    embedding_model = Column(String(128), nullable=False, default="nomic-embed-text")
    embedding_dimensions = Column(Integer, nullable=False, default=768)
    pipeline_version = Column(String(32), nullable=False, default="1.0.0")
    error_summary = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True, default=lambda: f"conv_{uuid.uuid4().hex[:12]}")
    title = Column(String(256), nullable=True)
    user_metadata = Column(JSON, nullable=False, default=dict)
    provider = Column(String(64), nullable=False, default="ollama")
    model = Column(String(64), nullable=False, default="llama3.1:8b")
    status = Column(String(32), nullable=False, default="active")  # active, archived, error
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")
    artifacts = relationship("Artifact", back_populates="session", cascade="all, delete-orphan", order_by="Artifact.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(64), primary_key=True, default=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    session_id = Column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=False, default=dict)
    provider = Column(String(64), nullable=True)
    model = Column(String(64), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    cost_inr = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    session = relationship("Session", back_populates="messages")
    artifacts = relationship("Artifact", back_populates="message")


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String(64), primary_key=True, default=lambda: f"art_{uuid.uuid4().hex[:12]}")
    session_id = Column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(64), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True)
    artifact_type = Column(String(32), nullable=False, default="essay")  # essay, markdown, html, json
    title = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    rendered_html = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=False, default=dict)
    word_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    session = relationship("Session", back_populates="artifacts")
    message = relationship("Message", back_populates="artifacts")

