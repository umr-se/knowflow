from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5433/knowflow"

    # Local generation through Ollama. No cloud API key is required.
    ollama_base_url: str = "http://localhost:11434"
    chat_model: str = "qwen2.5:1.5b"
    llm_temperature: float = 0.2
    llm_timeout_seconds: int = 120
    max_context_chars: int = 12000

    # Small CPU-friendly embedding model (~80 MB, 384 dimensions).
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    cors_origins: str = "http://localhost:3000"
    chunk_size: int = 900
    chunk_overlap: int = 150
    retrieval_top_k: int = 5
    min_retrieval_score: float = 0.20
    max_upload_mb: int = 30

    # Keep embedding/model download caches local to the project when running directly.
    hf_home: str = str(PROJECT_DIR / "models" / "huggingface")
    transformers_cache: str = str(PROJECT_DIR / "models" / "huggingface")

    model_config = SettingsConfigDict(
        # Root .env is useful for Docker-style development; backend/.env can
        # override it for local FastAPI development. Real process env wins.
        env_file=(PROJECT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load environment-backed settings only when a module actually needs them."""
    return Settings()
