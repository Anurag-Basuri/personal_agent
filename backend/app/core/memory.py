"""
Async chat history persistence using SQLAlchemy.

Migrated from monolithic AgentSession history to individual AgentMessage rows.
This enables granular message editing, deletion, and Omni-Memory search capabilities.
"""

from __future__ import annotations

import uuid
from typing import Any, Sequence

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage
)
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.models.agent_session import AgentSession
from app.models.agent_message import AgentMessage

# Note: We remove the JSON in-memory cache because we now rely on DB-level retrieval for granular control.
# If performance drops, implement a Redis cache for message IDs.

class AsyncMessageHistory:
    """
    Async chat message history backed by individual AgentMessage rows.
    """

    def __init__(self, session_id: str, user_id: str | None = None, role: str = "GUEST", transport: str = "WEB"):
        self.session_id = session_id
        self.user_id = user_id
        self.role = role
        self.transport = transport

    async def _ensure_session(self, db: AsyncSession) -> AgentSession:
        """Fetch or create the Session."""
        result = await db.execute(
            select(AgentSession).where(AgentSession.sessionId == self.session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            session = AgentSession(
                id=str(uuid.uuid4()).replace("-", "")[:25],
                sessionId=self.session_id,
                user_id=self.user_id,
                role=self.role,
                transport=self.transport,
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
        
        return session

    def _to_langchain_message(self, db_msg: AgentMessage) -> BaseMessage | None:
        """Convert a DB row into a LangChain BaseMessage."""
        if db_msg.role == "human":
            return HumanMessage(content=db_msg.content or "")
        elif db_msg.role == "ai":
            msg = AIMessage(content=db_msg.content or "")
            if db_msg.tool_calls:
                # Decrypting parsing tool calls is handled by the model, but we need to format it for LC
                # For now, simplistic recovery: 
                import json
                try:
                    msg.additional_kwargs["tool_calls"] = json.loads(db_msg.tool_calls)
                except Exception:
                    pass
            return msg
        elif db_msg.role == "system":
            return SystemMessage(content=db_msg.content or "")
        elif db_msg.role == "tool":
            return ToolMessage(
                content=db_msg.content or "",
                tool_call_id=db_msg.tool_call_id or "",
                name=db_msg.name or ""
            )
        return None

    def _to_db_message(self, msg: BaseMessage, session_db_id: str) -> AgentMessage:
        """Convert a LangChain message into an AgentMessage row."""
        db_msg = AgentMessage(
            session_id=session_db_id,
            content=str(msg.content)
        )
        
        if isinstance(msg, HumanMessage):
            db_msg.role = "human"
        elif isinstance(msg, AIMessage):
            db_msg.role = "ai"
            tool_calls = getattr(msg, "tool_calls", [])
            if tool_calls:
                import json
                db_msg.tool_calls = json.dumps(tool_calls)
        elif isinstance(msg, SystemMessage):
            db_msg.role = "system"
        elif isinstance(msg, ToolMessage):
            db_msg.role = "tool"
            db_msg.tool_call_id = msg.tool_call_id
            db_msg.name = msg.name
        else:
            db_msg.role = "unknown"
            
        return db_msg

    async def get_messages(self) -> list[BaseMessage]:
        """Load messages from DB ordered by creation time."""
        async with async_session() as db:
            session = await self._ensure_session(db)
            
            # Security ownership check
            if session and self.user_id and session.user_id != self.user_id:
                return []

            result = await db.execute(
                select(AgentMessage)
                .where(AgentMessage.session_id == session.id)
                .order_by(AgentMessage.createdAt.asc())
            )
            db_messages = result.scalars().all()
            
            langchain_msgs = []
            for db_msg in db_messages:
                lc_msg = self._to_langchain_message(db_msg)
                if lc_msg:
                    langchain_msgs.append(lc_msg)
            
            return langchain_msgs

    async def add_message(self, message: BaseMessage) -> None:
        """Persist a single message to the database."""
        async with async_session() as db:
            session = await self._ensure_session(db)
            
            db_msg = self._to_db_message(message, session.id)
            db.add(db_msg)
            await db.commit()


    async def clear(self) -> None:
        """Delete all messages for this session."""
        async with async_session() as db:
            session = await self._ensure_session(db)
            await db.execute(
                delete(AgentMessage).where(AgentMessage.session_id == session.id)
            )
            await db.commit()


def get_message_history(
    session_id: str, 
    user_id: str | None = None,
    role: str = "GUEST",
    transport: str = "WEB"
) -> AsyncMessageHistory:
    """Factory — returns an async message history for the given session."""
    return AsyncMessageHistory(session_id, user_id, role, transport)


async def clear_session_memory(session_id: str) -> None:
    """Clear a session's memory."""
    history = AsyncMessageHistory(session_id)
    await history.clear()
