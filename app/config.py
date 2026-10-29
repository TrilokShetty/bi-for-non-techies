"""Central settings loaded from environment / .env."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paths and runtime knobs for the assistant.

    Why pydantic-settings: one place for env overrides without scattering
    os.getenv calls, which makes Docker vs local runs easier to reason about.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

    # LLM provider: "ollama" (local) or "groq" (hosted free tier)
    LLM_PROVIDER: str = "ollama"

    # Ollama (local LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # Groq (hosted). Key lives only in .env, never in code.
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Paths (all under project root so the project is self-contained)
    DOCUMENTS_DIR: Path = PROJECT_ROOT / "data" / "documents"
    DATABASE_PATH: Path = PROJECT_ROOT / "data" / "retail.db"
    SCHEMA_PATH: Path = PROJECT_ROOT / "data" / "schema.md"
    VECTORDB_PATH: Path = PROJECT_ROOT / "vectordb"
    CHECKPOINT_DB: Path = PROJECT_ROOT / "checkpoints.db"

    # RAG / agent controls
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVAL_K: int = 4
    MAX_RETRIES: int = 2
    SQL_ROW_LIMIT: int = 50


settings = Settings()
