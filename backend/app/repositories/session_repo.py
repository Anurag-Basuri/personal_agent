"""
SessionRepository — all database operations for AgentSession.

Centralises session CRUD so no raw SQLAlchemy queries leak
into services, API routes, or the memory layer.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select

from app.database import async_session
from app.models.agent_session import AgentSession


class SessionRepository:
    """All database operations for AgentSession."""

    async def get_by_session_id(self, session_id: str) -> AgentSession | None:
        """Fetch a session by its public session ID."""
        async with async_session() as db:
            result = await db.execute(
                select(AgentSession).where(AgentSession.sessionId == session_id)
            )
            return result.scalar_one_or_none()

    async def get_by_session_id_and_user(
        self, session_id: str, user_id: str
    ) -> AgentSession | None:
        """Fetch a session scoped to a specific user (ownership check)."""
        async with async_session() as db:
            result = await db.execute(
                select(AgentSession).where(
                    AgentSession.sessionId == session_id,
                    AgentSession.user_id == user_id,
                )
            )
            return result.scalar_one_or_none()

    async def get_or_create(
        self,
        session_id: str,
        user_id: str | None = None,
        role: str = "GUEST",
        transport: str = "WEB",
    ) -> AgentSession:
        """Fetch an existing session or create a new one."""
        async with async_session() as db:
            result = await db.execute(
                select(AgentSession).where(AgentSession.sessionId == session_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                session = AgentSession(
                    id=str(uuid.uuid4()).replace("-", "")[:25],
                    sessionId=session_id,
                    user_id=user_id,
                    role=role,
                    transport=transport,
                )
                db.add(session)
                await db.commit()
                await db.refresh(session)

            return session

    async def list_by_user(
        self, user_id: str, page: int = 1, limit: int = 10
    ) -> tuple[list[AgentSession], int]:
        """Paginated list of sessions for a user."""
        skip = (page - 1) * limit
        async with async_session() as db:
            stmt = (
                select(AgentSession)
                .where(AgentSession.user_id == user_id)
                .order_by(AgentSession.updatedAt.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(stmt)
            sessions = list(result.scalars().all())

            count_result = await db.execute(
                select(func.count(AgentSession.id)).where(
                    AgentSession.user_id == user_id
                )
            )
            total = count_result.scalar() or 0

        return sessions, total

    async def delete_by_id(self, session_id: str, user_id: str | None = None) -> bool:
        """
        Delete a session by its DB primary key.
        If user_id is provided, also checks ownership.
        Returns True if a row was deleted.
        """
        async with async_session() as db:
            conditions = [AgentSession.id == session_id]
            if user_id:
                conditions.append(AgentSession.user_id == user_id)

            result = await db.execute(
                select(AgentSession).where(*conditions)
            )
            session = result.scalar_one_or_none()

            if not session:
                return False

            await db.execute(delete(AgentSession).where(AgentSession.id == session_id))
            await db.commit()
            return True


# Singleton
session_repo = SessionRepository()
