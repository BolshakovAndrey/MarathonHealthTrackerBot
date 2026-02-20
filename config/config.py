from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    BOT_TOKEN: str
    APP_ENV: str = "development"
    TIMEZONE: str = "Europe/Belgrade"

    # SQLite (local)
    DATABASE_PATH: str = "data/health_tracker.db"

    # PostgreSQL (Railway production/staging)
    DATABASE_URL: Optional[str] = None

    # Sentry (только production)
    SENTRY_DSN: Optional[str] = None

    ENABLE_DEBUG: bool = False

    @field_validator("APP_ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}")
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def use_postgres(self) -> bool:
        return self.DATABASE_URL is not None


settings = Settings()
