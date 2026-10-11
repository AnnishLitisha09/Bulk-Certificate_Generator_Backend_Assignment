"""
Application configuration module.
Loads settings from environment variables or .env file using Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings."""

    APP_NAME: str = "Bulk Certificate Generator"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database configuration
    DATABASE_URL: str = "sqlite:///./bulk_certificates.db"

    # Storage configuration
    STORAGE_DIR: str = "storage/certificates"

    # Batch limit
    MAX_BATCH_SIZE: int = 500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def storage_path(self) -> Path:
        """Return the resolved storage directory Path and ensure it exists."""
        path = Path(self.STORAGE_DIR).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
