"""
Google OAuth 2.0 Authentication for FastAPI.

Verifies Google ID tokens sent as Bearer tokens from the Next.js frontend.
In DEBUG mode, creates a dev user when no token is present for easy testing.
"""

import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import get_settings
from app.core.logger import agent_logger
from app.database import get_db
from app.models.user import User


def _extract_bearer_token(request: Request) -> str | None:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


def _verify_google_id_token(token: str) -> dict:
    """
    Verify a Google ID token using Google's official library.
    Returns the decoded payload with email, name, picture, etc.
    """
    settings = get_settings()

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        # verify_oauth2_token validates:
        #   - Signature (via Google's public keys)
        #   - Expiration
        #   - Issuer (accounts.google.com)
        #   - Audience (your client ID)
        payload = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=settings.AUTH_GOOGLE_CLIENT_ID if settings.AUTH_GOOGLE_CLIENT_ID else None,
        )

        # Additional safety checks
        issuer = payload.get("iss", "")
        if issuer not in ("accounts.google.com", "https://accounts.google.com"):
            raise ValueError(f"Invalid issuer: {issuer}")

        return payload

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI Dependency to authenticate users via Google OAuth 2.0 ID tokens.

    Expects: Authorization: Bearer <google_id_token>

    In DEBUG mode, if no token is present, a dev user is auto-created
    so the server can be tested without the frontend running.
    """
    settings = get_settings()
    token = _extract_bearer_token(request)

    # ─── Dev Mode Bypass ────────────────────────────────────────
    if not token and settings.is_debug:
        agent_logger.debug("AUTH", "🔓 DEBUG mode: using dev user (no token provided)")
        return await _get_or_create_user(
            db,
            email="dev@localhost",
            name="Dev User",
            picture="",
            role="ADMIN",
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Send Google ID token as Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ─── Verify Google ID Token ─────────────────────────────────
    payload = _verify_google_id_token(token)

    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing email.",
        )

    if not payload.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified by Google.",
        )

    name = payload.get("name", "")
    picture = payload.get("picture", "")

    return await _get_or_create_user(db, email=email, name=name, picture=picture)


async def _get_or_create_user(
    db: AsyncSession,
    email: str,
    name: str = "",
    picture: str = "",
    role: str = "GUEST",
) -> User:
    """Find existing user by email or create a new one."""
    result = await db.execute(select(User).where(User.email == email))
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
        agent_logger.info("AUTH", f"✨ New user created: {email}", {"role": role})

    return user
