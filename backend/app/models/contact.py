"""ContactMessage model — matches Prisma schema."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ContactMessage(Base):
    __tablename__ = "ContactMessage"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    isRead: Mapped[bool] = mapped_column(Boolean, default=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
