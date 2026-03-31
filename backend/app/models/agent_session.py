"""AgentSession model — matches Prisma schema."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AgentSession(Base):
    __tablename__ = "AgentSession"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    sessionId: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    history: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    createdAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Authenticated user scope via NextAuth
    from sqlalchemy import ForeignKey
    from sqlalchemy.orm import relationship
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="sessions")
