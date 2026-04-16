"""
AgentMemory model — persistent memory for preferences, facts, and conversation summaries.

Phase 5: Memory & Summarization.
Stores extracted knowledge that persists across sessions.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AgentMemory(Base):
    """
    Persistent agent memory — stores facts, preferences, and summaries
    extracted from conversations.
    
    Types:
      - "preference": User preference (e.g., "prefers Python over Java")
      - "fact": Factual information about the user
      - "interest": User's area of interest
      - "summary": Conversation summary for a session
    """
    __tablename__ = "AgentMemory"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    # Which user this memory belongs to (nullable for anonymous/guest sessions)
    user_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    
    # Source session where this memory was extracted from
    source_session_id: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Type: "preference", "fact", "interest", "summary"
    type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    
    # The actual memory content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Confidence score (0.0 - 1.0) — how confident the extraction was
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Timestamps
    createdAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
