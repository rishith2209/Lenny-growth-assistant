from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"
    PI_BRIDGE_URL: str = "http://localhost:4001"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/lenny_growth"
    DATABASE_SYNC_URL: str = "postgresql://postgres:postgres@127.0.0.1:5433/lenny_growth"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    PRIMARY_MODEL: str = "llama3.1:8b"
    FALLBACK_MODEL: str = "qwen3:4b"
    REASONING_MODEL: str = "qwen3:8b"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIMENSIONS: int = 768

    # Pi Agent
    PI_AGENT_VERSION: str = "0.74.2"
    PI_SESSION_TIMEOUT_SECONDS: int = 300

    # Ingestion
    TRANSCRIPT_SOURCE_REPO: str = "https://github.com/ChatPRD/lennys-podcast-transcripts.git"
    TRANSCRIPT_CACHE_DIR: str = ".cache/transcripts"
    INGEST_BATCH_SIZE: int = 32

    # Optional Commercial Providers (Disabled for ₹0 default demo)
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None


settings = Settings()
