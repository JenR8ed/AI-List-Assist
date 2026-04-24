# core/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-List-Assist FARM Migration"

    # Strictly piped from Windows via WSLENV. No local .env loading.
    NEON_DATABASE_URL: str = os.getenv("NEON_DATABASE_URL", "")
    STITCH_TOKEN: str = os.getenv("STITCH_TOKEN", "")

    @property
    def async_database_url(self) -> str:
        """Converts standard postgresql:// to asyncpg:// for async SQLModel"""
        if self.NEON_DATABASE_URL and self.NEON_DATABASE_URL.startswith("postgresql://"):
            return self.NEON_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.NEON_DATABASE_URL

# Instantiate globally
settings = Settings()
