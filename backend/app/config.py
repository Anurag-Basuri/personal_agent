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

    # Server
    PORT: int = 4000
    DEBUG: bool = False
    # Agent website origin
    CLIENT_URL: str = "http://localhost:3000"
    # Portfolio website origin (for CORS)
    PORTFOLIO_URL: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    # Optional: separate portfolio database
    PORTFOLIO_DB_URL: str = ""

    # AI Providers
    HF_TOKEN: str = ""
    GROQ_API_KEY: str = ""

    # External APIs
    GITHUB_TOKEN: str = ""

    # Customization / Identity
    AGENT_NAME: str = "Agent"
    GITHUB_USERNAME: str = ""
    LEETCODE_USERNAME: str = ""

    # Security & Auth
    AUTH_SECRET: str = ""
    # Google OAuth Client ID for ID token verification
    AUTH_GOOGLE_CLIENT_ID: str = ""
    # Base64 AES GCM 256 bit key
    OMNI_MEMORY_KEY: str = ""
    # Shared secret for RAG reindex webhook
    REINDEX_SECRET: str = ""

    # RAG Sync
    # Background RAG re ingestion interval
    RAG_SYNC_INTERVAL_HOURS: int = 6

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    # Comma separated list of allowed Telegram user IDs
    TELEGRAM_ALLOWED_USER_IDS: str = ""

    @property
    def telegram_allowed_ids(self) -> list[int]:
        if not self.TELEGRAM_ALLOWED_USER_IDS:
            return []
        try:
            return [int(x.strip()) for x in self.TELEGRAM_ALLOWED_USER_IDS.split(",") if x.strip()]
        except ValueError:
            return []

    @property
    def is_debug(self) -> bool:
        return self.DEBUG

    @property
    def is_postgres(self) -> bool:
        """Check if the database is PostgreSQL (vs SQLite)."""
        return "postgres" in self.DATABASE_URL.lower()


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance   cached after first call."""
    return Settings()
