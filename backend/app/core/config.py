from typing import List, Union, Optional
from pydantic import field_validator, model_validator
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
    DATABASE_URL: Optional[str] = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "logsentinel"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Optional[str]) -> Optional[str]:
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    @model_validator(mode="after")
    def validate_database_configuration(self) -> "Settings":
        if not self.DATABASE_URL:
            if not self.POSTGRES_PASSWORD:
                raise ValueError(
                    "Database credentials missing: Please provide DATABASE_URL or POSTGRES_PASSWORD in your environment or .env file."
                )
            from urllib.parse import quote_plus
            self.DATABASE_URL = (
                f"postgresql+psycopg2://{self.POSTGRES_USER}:{quote_plus(self.POSTGRES_PASSWORD)}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self


    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
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
