from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HD_", env_file=".env", extra="ignore")
    database_url: str = "sqlite+aiosqlite:///./hidden_dissatisfaction.db"
    jwt_secret: str = Field("change-me-in-production", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    environment: str = "development"
    evidence_dir: str = "./data/evidence"
    cors_origins: list[str] = []  # explicit allowlist; empty = same-origin only
    max_request_bytes: int = 6 * 1024 * 1024  # 5 MB evidence + multipart overhead
