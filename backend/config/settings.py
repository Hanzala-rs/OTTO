from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # PostgreSQL
    postgres_url: str = "postgresql://otto_user:changeme@localhost:5432/otto"

    # Qdrant
    qdrant_url: str = "http://localhost:8333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "documents"
    qdrant_timeout: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379"
    session_ttl_seconds: int = 1800

    # LLM — Groq free tier
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.2
    # LiteLLM proxy (OpenAI-compatible) — owns retries, rpm limits and fallbacks
    llm_proxy_url: str = "http://litellm:4000"
    llm_proxy_key: str = ""
    llm_proxy_model: str = "otto-llm"
    llm_voice_model: str = "otto-llm-fast"

    # Embeddings
    embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    # Whisper STT
    whisper_model: str = "small"

    # Monitoring
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "otto-rag"

    # CORS
    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
