"""
MemoryRepository — all database operations for AgentMemory.

Handles persistent user memories: preferences, facts, interests,
and conversation summaries.
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.cache import app_cache
from app.core.logger import agent_logger
from app.database import async_session
from app.models.agent_memory import AgentMemory


class MemoryRepository:
    """All database operations for AgentMemory (preferences, facts, summaries)."""

    async def get_user_memories(
        self,
        user_id: str,
        types: list[str] | None = None,
        min_confidence: float = 0.6,
        limit: int = 10,
    ) -> list[AgentMemory]:
        """Fetch persistent memories for a user, filtered by type and confidence."""
        if not user_id:
            return []

        # Check cache first
        cache_key = f"memories:{user_id}"
        cached = app_cache.get(cache_key)
        if cached is not None:
            agent_logger.debug("CACHE", f"Hit for {cache_key}")
            return cached

        try:
            async with async_session() as db:
                stmt = (
                    select(AgentMemory)
                    .where(
                        AgentMemory.user_id == user_id,
                        AgentMemory.confidence >= min_confidence,
                    )
                    .order_by(AgentMemory.updatedAt.desc())
                    .limit(limit)
                )

                if types:
                    stmt = stmt.where(AgentMemory.type.in_(types))

                result = await db.execute(stmt)
                memories = list(result.scalars().all())

            # Cache for 5 minutes
            app_cache.set(cache_key, memories, ttl=300)
            return memories
        except Exception as e:
            agent_logger.warn("MEMORY", f"Failed to load user memories: {e}")
            return []

    async def get_session_summary(self, user_id: str, session_id: str) -> str | None:
        """Get the latest conversation summary for a session."""
        if not user_id:
            return None

        # Check cache first
        cache_key = f"summary:{session_id}"
        cached = app_cache.get(cache_key)
        if cached is not None:
            agent_logger.debug("CACHE", f"Hit for {cache_key}")
            return cached

        try:
            async with async_session() as db:
                result = await db.execute(
                    select(AgentMemory)
                    .where(
                        AgentMemory.user_id == user_id,
                        AgentMemory.source_session_id == session_id,
                        AgentMemory.type == "summary",
                    )
                    .order_by(AgentMemory.createdAt.desc())
                    .limit(1)
                )
                summary = result.scalar_one_or_none()
                content = summary.content if summary else None

            # Cache even None (prevents repeated DB hits for sessions with no summary)
            app_cache.set(cache_key, content, ttl=300)
            return content
        except Exception as e:
            agent_logger.warn("MEMORY", f"Failed to load session summary: {e}")
            return None

    async def save_summary(
        self, user_id: str, session_id: str, summary: str
    ) -> None:
        """Persist a conversation summary."""
        if not user_id or not summary:
            return

        try:
            async with async_session() as db:
                mem = AgentMemory(
                    user_id=user_id,
                    source_session_id=session_id,
                    type="summary",
                    content=summary,
                    confidence=1.0,
                )
                db.add(mem)
                await db.commit()

            # Invalidate caches
            app_cache.delete(f"summary:{session_id}")
            app_cache.delete(f"memories:{user_id}")
        except Exception as e:
            agent_logger.error("MEMORY", f"Failed to persist summary: {e}")

    async def save_preferences(
        self, user_id: str, session_id: str, preferences: list[dict]
    ) -> int:
        """
        Persist extracted preferences/facts.
        Returns the number of preferences actually saved.
        """
        if not user_id or not preferences:
            return 0

        saved = 0
        try:
            async with async_session() as db:
                for pref in preferences:
                    content = pref.get("content", "")
                    pref_type = pref.get("type", "preference")
                    confidence = pref.get("confidence", 0.7)

                    if content and confidence >= 0.5:
                        mem = AgentMemory(
                            user_id=user_id,
                            source_session_id=session_id,
                            type=pref_type,
                            content=content,
                            confidence=confidence,
                        )
                        db.add(mem)
                        saved += 1

                await db.commit()

            # Invalidate user memories cache
            app_cache.delete(f"memories:{user_id}")
        except Exception as e:
            agent_logger.error("MEMORY", f"Failed to persist preferences: {e}")

        return saved

    async def delete_all_for_user(self, user_id: str) -> int:
        """Delete ALL memories (summaries, preferences, facts) for a user.

        Used by the delete-all endpoint to give the user a clean slate.
        """
        if not user_id:
            return 0

        try:
            from sqlalchemy import delete as sql_delete

            async with async_session() as db:
                result = await db.execute(
                    sql_delete(AgentMemory).where(AgentMemory.user_id == user_id)
                )
                await db.commit()
                deleted = result.rowcount or 0

            # Invalidate cache
            app_cache.delete(f"memories:{user_id}")
            agent_logger.info("MEMORY", f"Deleted {deleted} memories for user", {
                "user_id": user_id,
            })
            return deleted
        except Exception as e:
            agent_logger.error("MEMORY", f"Failed to delete user memories: {e}")
            return 0


# Singleton
memory_repo = MemoryRepository()
