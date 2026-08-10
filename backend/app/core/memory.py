"""
Async chat history persistence using SQLAlchemy.

Migrated from monolithic AgentSession history to individual AgentMessage rows.
This enables granular message editing, deletion, and Omni-Memory search capabilities.

Refactored to use the Repository Pattern — all raw SQLAlchemy queries
are now delegated to SessionRepository and MessageRepository.
"""

from __future__ import annotations

import json

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.models.agent_message import AgentMessage
from app.repositories.message_repo import message_repo
from app.repositories.session_repo import session_repo


class AsyncMessageHistory:
    """
    Async chat message history backed by individual AgentMessage rows.
    """

    def __init__(self, session_id: str, user_id: str | None = None, role: str = "GUEST", transport: str = "WEB"):
        self.session_id = session_id
        self.user_id = user_id
        self.role = role
        self.transport = transport

    def _to_langchain_message(self, db_msg: AgentMessage) -> BaseMessage | None:
        """Convert a DB row into a LangChain BaseMessage."""
        if db_msg.role == "human":
            return HumanMessage(content=db_msg.content or "")
        elif db_msg.role == "ai":
            tool_calls = []
            if db_msg.tool_calls:
                try:
                    tool_calls = json.loads(db_msg.tool_calls)
                except Exception:
                    pass
            return AIMessage(content=db_msg.content or "", tool_calls=tool_calls)
        elif db_msg.role == "system":
            return SystemMessage(content=db_msg.content or "")
        elif db_msg.role == "tool":
            return ToolMessage(
                content=db_msg.content or "",
                tool_call_id=db_msg.tool_call_id or "",
                name=db_msg.name or "",
            )
        return None

    def _to_db_message(self, msg: BaseMessage, session_db_id: str) -> AgentMessage:
        """Convert a LangChain message into an AgentMessage row."""
        db_msg = AgentMessage(
            session_id=session_db_id,
            content=str(msg.content),
        )

        if isinstance(msg, HumanMessage):
            db_msg.role = "human"
        elif isinstance(msg, AIMessage):
            db_msg.role = "ai"
            tool_calls = getattr(msg, "tool_calls", [])
            if tool_calls:
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
        session = await session_repo.get_or_create(
            self.session_id, self.user_id, self.role, self.transport
        )

        # Security ownership check
        if self.user_id and session.user_id != self.user_id:
            return []

        db_messages = await message_repo.get_by_session(session.id)

        langchain_msgs = []
        for db_msg in db_messages:
            lc_msg = self._to_langchain_message(db_msg)
            if lc_msg:
                langchain_msgs.append(lc_msg)

        return langchain_msgs

    async def add_message(self, message: BaseMessage) -> None:
        """Persist a single message to the database."""
        session = await session_repo.get_or_create(
            self.session_id, self.user_id, self.role, self.transport
        )
        db_msg = self._to_db_message(message, session.id)
        await message_repo.create(db_msg)

    async def clear(self) -> None:
        """Delete all messages for this session."""
        session = await session_repo.get_or_create(
            self.session_id, self.user_id, self.role, self.transport
        )
        await message_repo.delete_all_for_session(session.id)


def get_message_history(
    session_id: str,
    user_id: str | None = None,
    role: str = "GUEST",
    transport: str = "WEB",
) -> AsyncMessageHistory:
    """Factory   returns an async message history for the given session."""
    return AsyncMessageHistory(session_id, user_id, role, transport)


async def clear_session_memory(session_id: str) -> None:
    """Clear a session's memory."""
    history = AsyncMessageHistory(session_id)
    await history.clear()
