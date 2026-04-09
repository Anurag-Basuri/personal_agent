import uuid
import json
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.models.base import Base
from app.core.encryption import encrypt_string, decrypt_string

class EncryptedString(TypeDecorator):
    """Transparently encrypts value on save, decrypts on load."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any | None, dialect: Any) -> str | None:
        if value is None:
            return None
        # Convert objects like list/dict (e.g. tool calls) to string before encryption
        if not isinstance(value, str):
            value = json.dumps(value)
        return encrypt_string(value)

    def process_result_value(self, value: str | None, dialect: Any) -> Any | None:
        if value is None:
            return None
        decrypted = decrypt_string(value)
        return decrypted


from pgvector.sqlalchemy import Vector

class AgentMessage(Base):
    """
    Individual Agent Message Model.
    Replaces the monolithic `history` block to allow Granular control (delete, edit)
    and Omni-Memory (semantic search across individual messages).
    Content is encrypted at rest using AES-GCM.
    """
    __tablename__ = "AgentMessage"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("AgentSession.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # "user", "ai", "system", "tool"
    role: Mapped[str] = mapped_column(String, nullable=False)
    
    # The actual message text, completely encrypted in the database
    content: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    
    # Mathematical Representation for Omni-Memory Semantic Search
    embedding: Mapped[Vector | None] = mapped_column(Vector(768), nullable=True)
    
    # Store tool calls or results. Also encrypted.
    tool_calls: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(String, nullable=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)  # Tool name for tool messages

    tokens_used: Mapped[int] = mapped_column(default=0)
    
    createdAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    session = relationship("AgentSession", back_populates="messages")
