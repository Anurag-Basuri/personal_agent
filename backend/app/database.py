"""
Async SQLAlchemy engine, session factory, and DB lifecycle helpers.
Updated for PostgreSQL / NeonDB and pgvector.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.is_debug,
    future=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    """FastAPI dependency — yields an async DB session per request."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Create all tables on startup. Safely injects pgvector extension first if using postgres."""
    from app.models import Base  # noqa: F811

    # Only attempt to create extension if we are running Postgres (NeonDB)
    is_postgres = "postgres" in settings.DATABASE_URL

    async with engine.begin() as conn:
        if is_postgres:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Dispose engine on shutdown."""
    await engine.dispose()
