"""AgentSession model — matches Prisma schema."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AgentSession(Base):
    __tablename__ = "AgentSession"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    sessionId: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    
    # Role tracking for RBAC (GUEST, ADMIN)
    role: Mapped[str] = mapped_column(String, default="GUEST", nullable=False)
    # Transport tracking for Omni-Memory (WEB, TELEGRAM, WHATSAPP)
    transport: Mapped[str] = mapped_column(String, default="WEB", nullable=False)
    
    createdAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Authenticated user scope via NextAuth
    from sqlalchemy import ForeignKey
    from sqlalchemy.orm import relationship
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    user = relationship("User", back_populates="sessions")
    
    # Individual granular messages
    messages = relationship("AgentMessage", back_populates="session", cascade="all, delete-orphan")
