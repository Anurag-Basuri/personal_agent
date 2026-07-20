"""
MessageRepository — all database operations for AgentMessage.

Centralises message CRUD so encryption, ordering, and ownership
checks happen in exactly one place.
"""

from __future__ import annotations

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.agent_message import AgentMessage
from app.models.agent_session import AgentSession
from app.core.cache import app_cache


class MessageRepository:
    """All database operations for AgentMessage."""

    async def get_by_session(self, session_db_id: str) -> list[AgentMessage]:
        """Fetch all messages for a session, ordered by creation time."""
        async with async_session() as db:
            result = await db.execute(
                select(AgentMessage)
                .where(AgentMessage.session_id == session_db_id)
                .order_by(AgentMessage.createdAt.asc())
            )
            return list(result.scalars().all())

    async def get_by_id(self, message_id: str) -> AgentMessage | None:
        """Fetch a single message by its primary key."""
        async with async_session() as db:
            result = await db.execute(
                select(AgentMessage).where(AgentMessage.id == message_id)
            )
            return result.scalar_one_or_none()

    async def get_session_for_message(self, message_id: str) -> AgentSession | None:
        """Fetch the session that owns a given message (for ownership checks)."""
        async with async_session() as db:
            result = await db.execute(
                select(AgentMessage).where(AgentMessage.id == message_id)
            )
            msg = result.scalar_one_or_none()
            if not msg:
                return None

            session_result = await db.execute(
                select(AgentSession).where(AgentSession.id == msg.session_id)
            )
            return session_result.scalar_one_or_none()

    async def create(self, msg: AgentMessage) -> AgentMessage:
        """Persist a new message row."""
        async with async_session() as db:
            db.add(msg)
            await db.commit()
            await db.refresh(msg)

        # Invalidate session history cache
        app_cache.delete(f"history:{msg.session_id}")
        return msg

    async def update_content(self, message_id: str, new_content: str) -> bool:
        """
        Update a message's content.
        The EncryptedString TypeDecorator handles re-encryption automatically.
        Returns True if the message was found and updated.
        """
        async with async_session() as db:
            result = await db.execute(
                select(AgentMessage).where(AgentMessage.id == message_id)
            )
            msg = result.scalar_one_or_none()
            if not msg:
                return False

            msg.content = new_content
            await db.commit()

            # Invalidate session history cache
            app_cache.delete(f"history:{msg.session_id}")
            return True

    async def delete_by_id(self, message_id: str) -> bool:
        """Delete a single message. Returns True if deleted."""
        # Fetch first to know session_id for cache invalidation
        msg = await self.get_by_id(message_id)
        async with async_session() as db:
            result = await db.execute(
                delete(AgentMessage).where(AgentMessage.id == message_id)
            )
            await db.commit()
            deleted = result.rowcount > 0

        if deleted and msg:
            app_cache.delete(f"history:{msg.session_id}")
        return deleted

    async def delete_all_for_session(self, session_db_id: str) -> int:
        """Bulk delete all messages in a session. Returns count deleted."""
        async with async_session() as db:
            result = await db.execute(
                delete(AgentMessage).where(AgentMessage.session_id == session_db_id)
            )
            await db.commit()

        app_cache.delete(f"history:{session_db_id}")
        return result.rowcount


# Singleton
message_repo = MessageRepository()
