"""
Application settings — validated via Pydantic Settings.

Reads from .env file and environment variables.
Uses lru_cache for singleton pattern.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration for the application, validated at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Server ──────────────────────────────────────────────────
    PORT: int = 4000
    DEBUG: bool = False
    CLIENT_URL: str = "http://localhost:3000"

    # ─── Database ────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"

    # ─── AI Providers ────────────────────────────────────────────
    GEMINI_API_KEY: str | None = None
    HF_TOKEN: str | None = None

    # ─── External APIs ───────────────────────────────────────────
    GITHUB_TOKEN: str | None = None

    @property
    def is_debug(self) -> bool:
        return self.DEBUG


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance — cached after first call."""
    return Settings()
