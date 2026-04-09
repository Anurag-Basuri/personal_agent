import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class User(Base):
    """NextAuth synchronized User model."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)
    picture: Mapped[str] = mapped_column(String, nullable=True)
    
    # Role tracking for RBAC (GUEST, ADMIN)
    role: Mapped[str] = mapped_column(String, default="GUEST", nullable=False)
    
    createdAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    sessions = relationship("AgentSession", back_populates="user", cascade="all, delete-orphan")
