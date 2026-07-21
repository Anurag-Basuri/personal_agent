"""
Shared test fixtures for the Personal Agent backend test suite.

Provides:
  - In-memory async SQLite engine and session factory
  - Per-test DB setup/teardown (creates and drops all tables)
  - Overridden settings fixture with safe defaults
  - FastAPI TestClient fixture
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models import Base

# ─── Event Loop ──────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ─── Database ────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db_engine():
    """Create an in-memory async SQLite engine per test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Provide a transactional DB session that rolls back after each test."""
    session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


# ─── Settings Override ───────────────────────────────────────────

@pytest.fixture
def mock_settings():
    """
    Override get_settings() to return safe test defaults.

    Usage:
        def test_something(mock_settings):
            mock_settings.DEBUG = True
            # ... test code uses the overridden settings
    """
    from app.config import Settings

    test_settings = Settings(
        PORT=4000,
        DEBUG=True,
        CLIENT_URL="http://localhost:3000",
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        AGENT_NAME="TestAgent",
        GITHUB_USERNAME="test-user",
        LEETCODE_USERNAME="test-user",
        AUTH_SECRET="test-secret",
        OMNI_MEMORY_KEY="",
        HF_TOKEN="",
        GROQ_API_KEY="",
        GITHUB_TOKEN="",
        TELEGRAM_BOT_TOKEN="",
        TELEGRAM_ALLOWED_USER_IDS="",
    )

    with patch("app.config.get_settings", return_value=test_settings):
        yield test_settings
