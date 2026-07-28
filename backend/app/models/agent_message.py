import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base





# Conditional pgvector Import
# pgvector is only available when using PostgreSQL. On SQLite, we use a
# nullable Text column as a no op placeholder for the embedding field.
_vector_column_type = None
try:
    from app.config import get_settings as _get_settings
    _settings = _get_settings()
    if _settings.is_postgres:
        from pgvector.sqlalchemy import Vector
        _vector_column_type = Vector(768)
except Exception:
    pass


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

    # The actual message text
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Mathematical Representation for Omni Memory Semantic Search
    # On PostgreSQL: Vector(768) column for pgvector similarity search
    # On SQLite: nullable Text column (no op, embeddings disabled)
    if _vector_column_type is not None:
        embedding = mapped_column(_vector_column_type, nullable=True)
    else:
        embedding: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Store tool calls or results.
    tool_calls: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # Tool name for tool messages
    name: Mapped[str | None] = mapped_column(String, nullable=True)

    tokens_used: Mapped[int] = mapped_column(default=0)

    createdAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    session = relationship("AgentSession", back_populates="messages")
