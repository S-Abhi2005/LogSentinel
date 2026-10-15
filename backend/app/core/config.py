import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "LogSentinel — Cloud Log Intelligence"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "logsentinel-super-secret-jwt-key-2026-secure-auth-dev"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:abhi%40321@localhost:5432/logsentinel"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "logsentinel"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "abhi@321"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str) -> str:
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v  # type: ignore
        raise ValueError(v)

    # Ingestion Constraints & Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 1200
    MAX_BATCH_SIZE: int = 500
    MAX_LOG_MESSAGE_BYTES: int = 32768
    MAX_METADATA_BYTES: int = 65536
    INACTIVITY_CHECK_INTERVAL_SECONDS: int = 60

    # Initial Admin Bootstrap
    INITIAL_ADMIN_EMAIL: str = "admin@logsentinel.local"
    INITIAL_ADMIN_PASSWORD: str = "AdminSecurePass123!"
    INITIAL_ADMIN_FULL_NAME: str = "Super Administrator"


settings = Settings()
