"""Profile and SocialLink models — matches Prisma schema."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Profile(Base):
    __tablename__ = "Profile"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    header: Mapped[str | None] = mapped_column(String, nullable=True)
    bio: Mapped[str | None] = mapped_column(String, nullable=True)
    skills: Mapped[str | None] = mapped_column(String, nullable=True)
    openToWork: Mapped[bool] = mapped_column(Boolean, default=False)
    availableFrom: Mapped[str | None] = mapped_column(String, nullable=True)
    noticePeriod: Mapped[str | None] = mapped_column(String, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    socialLinks: Mapped[list["SocialLink"]] = relationship(back_populates="profile", lazy="selectin")


class SocialLink(Base):
    __tablename__ = "SocialLink"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    profileId: Mapped[str] = mapped_column(String, ForeignKey("Profile.id"), nullable=False)

    profile: Mapped["Profile"] = relationship(back_populates="socialLinks")
