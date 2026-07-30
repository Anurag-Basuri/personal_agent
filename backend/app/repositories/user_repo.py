"""
UserRepository — all database operations for the User model.

Centralises user CRUD so no raw SQLAlchemy queries leak
into services, API routes, or the auth layer.
"""

from __future__ import annotations

import uuid

from sqlalchemy.future import select

from app.core.logger import agent_logger
from app.database import async_session
from app.models.user import User


class UserRepository:
    """All database operations for User."""

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by their email address."""
        async with async_session() as db:
            result = await db.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        """Fetch a user by their primary key."""
        async with async_session() as db:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()

    async def get_or_create(
        self,
        email: str,
        name: str = "",
        picture: str = "",
        role: str = "GUEST",
    ) -> User:
        """Find existing user by email or create a new one.

        This is the primary entry point used by the auth layer
        to resolve a JWT payload into a User object.
        """
        async with async_session() as db:
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

            if not user:
                user = User(
                    id=str(uuid.uuid4()),
                    email=email,
                    name=name,
                    picture=picture,
                    role=role,
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                agent_logger.info(
                    "AUTH", f"New user created: {email}", {"role": role},
                )

            return user


# Singleton
user_repo = UserRepository()
