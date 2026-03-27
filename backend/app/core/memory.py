"""
Async chat history persistence using SQLAlchemy.

Port of PrismaChatMessageHistory — stores serialized LangChain messages
in the AgentSession table with an in-memory cache.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from langchain_core.messages import (
    BaseMessage,
    messages_from_dict,
    messages_to_dict,
)
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.agent_session import AgentSession

MAX_HISTORY_MESSAGES = 20
CACHE_TTL_SECONDS = 60

# ─── In-Memory Cache ─────────────────────────────────────────────

_session_cache: dict[str, dict[str, Any]] = {}


def _prune_cache() -> None:
    now = time.time()
    expired = [k for k, v in _session_cache.items() if now - v["ts"] > CACHE_TTL_SECONDS]
    for k in expired:
        del _session_cache[k]


# ─── Message History ──────────────────────────────────────────────


class AsyncMessageHistory:
    """
    Async chat message history backed by SQLAlchemy.

    Mirrors the Node.js PrismaChatMessageHistory with:
    - In-memory cache (60s TTL)
    - Message trimming to last N
    - Upsert persistence
    """

    def __init__(self, session_id: str):
        self.session_id = session_id

    async def get_messages(self) -> list[BaseMessage]:
        """Load messages from cache or DB."""
        # Check cache
        cached = _session_cache.get(self.session_id)
        if cached and time.time() - cached["ts"] < CACHE_TTL_SECONDS:
            return cached["messages"]

        async with async_session() as db:
            result = await db.execute(
                select(AgentSession).where(AgentSession.sessionId == self.session_id)
            )
            session = result.scalar_one_or_none()

        if not session or not session.history:
            return []

        try:
            parsed = json.loads(session.history) if isinstance(session.history, str) else session.history
            all_messages = messages_from_dict(parsed)
        except (json.JSONDecodeError, Exception):
            return []

        # Trim
        trimmed = all_messages[-MAX_HISTORY_MESSAGES:] if len(all_messages) > MAX_HISTORY_MESSAGES else all_messages

        # Update cache
        _session_cache[self.session_id] = {"messages": trimmed, "ts": time.time()}
        return trimmed

    async def add_message(self, message: BaseMessage) -> None:
        """Persist a message (adds to existing history)."""
        # Get current messages (from cache if possible)
        cached = _session_cache.get(self.session_id)
        current = list(cached["messages"]) if cached else await self.get_messages()
        current.append(message)

        # Trim
        trimmed = current[-MAX_HISTORY_MESSAGES:] if len(current) > MAX_HISTORY_MESSAGES else current

        # Serialize
        stored = json.dumps(messages_to_dict(trimmed))

        # Upsert
        async with async_session() as db:
            result = await db.execute(
                select(AgentSession).where(AgentSession.sessionId == self.session_id)
            )
            session = result.scalar_one_or_none()

            if session:
                session.history = stored
            else:
                session = AgentSession(
                    id=str(uuid.uuid4()).replace("-", "")[:25],
                    sessionId=self.session_id,
                    history=stored,
                )
                db.add(session)

            await db.commit()

        # Refresh cache
        _session_cache[self.session_id] = {"messages": trimmed, "ts": time.time()}

    async def clear(self) -> None:
        """Delete session and clear cache."""
        _session_cache.pop(self.session_id, None)
        async with async_session() as db:
            await db.execute(
                delete(AgentSession).where(AgentSession.sessionId == self.session_id)
            )
            await db.commit()


def get_message_history(session_id: str) -> AsyncMessageHistory:
    """Factory — returns an async message history for the given session."""
    _prune_cache()
    return AsyncMessageHistory(session_id)


async def clear_session_memory(session_id: str) -> None:
    """Clear a session's memory."""
    history = AsyncMessageHistory(session_id)
    await history.clear()
