"""
app/core/config.py
Centralised settings loaded from environment variables via pydantic-settings.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_provider: str = Field(default="groq", description="openai | anthropic | groq")
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    groq_api_key: str = Field(default="")
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    groq_model: str = "llama3-70b-8192"

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"

    # Vector DB
    chroma_persist_dir: str = "./data/chroma_db"

    # SQL DB
    database_url: str = "sqlite+aiosqlite:///./data/screening.db"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Knowledge Base
    knowledge_base_dir: str = "./knowledge_base"
    chunk_size: int = 800
    chunk_overlap: int = 150

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def active_model(self) -> str:
        mapping = {
            "openai": self.openai_model,
            "anthropic": self.anthropic_model,
            "groq": self.groq_model,
        }
        return mapping.get(self.llm_provider, self.groq_model)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
