"""
Configuração central da aplicação FastAPI.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""

    # App
    APP_NAME: str = "Marketing Manager - Google Ads"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@marketing-manager-db:5432/marketing_manager"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Auth
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Google OAuth2
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Google Ads API
    GOOGLE_ADS_DEVELOPER_TOKEN: str = ""  # TODO: Add your developer token
    GOOGLE_ADS_LOGIN_CUSTOMER_ID: str = ""  # TODO: Add your login customer ID

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
    ]

    # API
    API_V1_PREFIX: str = "/api/v1"
    API_DOCS_URL: str = "/docs"
    API_REDOC_URL: str = "/redoc"

    # Scheduler
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_TIMEZONE: str = "UTC"
    SYNC_SCHEDULE_HOUR: int = 6  # 6 AM
    SYNC_INTERVAL_HOURS: int = 6
    AUTOMATION_RUN_INTERVAL_MINUTES: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).with_name(".env"),
        case_sensitive=True,
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> Any:
        """Aceita formatos comuns de ambientes de deploy para DEBUG."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"debug", "development", "dev", "local"}:
                return True
            if normalized in {"release", "production", "prod"}:
                return False
        return value

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> Any:
        """Suporta CORS em JSON ou CSV simples."""
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return []
            if normalized.startswith("["):
                return json.loads(normalized)
            return [origin.strip() for origin in normalized.split(",") if origin.strip()]
        return value


# Global settings instance
settings = Settings()
