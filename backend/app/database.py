"""
Async SQLAlchemy engine, session factory, and DB lifecycle helpers.
Updated for PostgreSQL / NeonDB and pgvector.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

# Lazy initialization to prevent loading settings at import time
# before .env has been loaded by main.py
_engine = None
_async_session = None


def _get_engine():
    """Return the async engine, creating it on first call."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.is_debug,
            future=True,
            pool_pre_ping=True,
        )
    return _engine


def _get_session_factory():
    """Return the session factory, creating it on first call."""
    global _async_session
    if _async_session is None:
        _async_session = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session


class _LazySessionFactory:
    """Proxy that lazily initializes the session factory on first call.

    Repositories import and call this as: async with async_session() as db:
    On first invocation, it creates the engine and sessionmaker.
    Subsequent calls reuse the cached sessionmaker.
    """

    def __call__(self):
        """Create and return a new async session."""
        return _get_session_factory()()


async_session = _LazySessionFactory()


async def get_db():
    """FastAPI dependency — yields an async DB session per request."""
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables on startup. Safely injects pgvector extension first if using postgres."""
    from app.models import Base

    settings = get_settings()
    engine = _get_engine()

    # Only attempt to create extension if we are running Postgres (NeonDB)
    is_postgres = "postgres" in settings.DATABASE_URL

    async with engine.begin() as conn:
        if is_postgres:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose engine on shutdown."""
    global _engine, _async_session
    engine = _get_engine()
    await engine.dispose()
    _engine = None
    _async_session = None

