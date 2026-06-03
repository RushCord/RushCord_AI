from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_api_key: str

    openai_api_key: str
    openai_chat_model: str = "llama-3.3-70b-versatile"
    openai_summary_model: str = "llama-3.3-70b-versatile"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_whisper_model: str = "whisper-1"

    aws_region: str
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    dynamodb_table_name: str = "ott"

    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection: str = "chat_embeddings"

    request_timeout_seconds: int = 20
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:8081,http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
