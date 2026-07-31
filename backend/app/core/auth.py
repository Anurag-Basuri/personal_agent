"""
Authentication & Authorization for FastAPI.

Three authentication flows:
  1. User Auth (Google OAuth / Credentials via NextAuth JWT)
  2. Admin Auth (custom admin_id + password, returns admin JWT)
  3. Telegram Admin Auth (whitelist based, no login needed)

Dependencies:
  - get_current_user: Validates any authenticated user (GUEST or ADMIN)
  - get_admin_user: Validates that the caller is an ADMIN (403 otherwise)
"""

from __future__ import annotations

import time

from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.core.logger import agent_logger
from app.models.user import User
from app.repositories.user_repo import user_repo


def _extract_bearer_token(request: Request) -> str | None:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


def _verify_jwt_token(token: str) -> dict:
    """
    Verify a JWT token (NextAuth or admin-issued).
    Returns the decoded payload with email, name, role, etc.
    """
    settings = get_settings()

    if not settings.AUTH_SECRET:
        raise ValueError("AUTH_SECRET is not configured on the backend.")

    try:
        import jwt

        payload = jwt.decode(
            token,
            settings.AUTH_SECRET,
            algorithms=["HS256"]
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid session token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_admin_jwt() -> str:
    """
    Create a signed JWT for the admin user.
    Contains role=ADMIN claim and a 24-hour expiry.
    """
    import jwt

    settings = get_settings()
    payload = {
        "email": settings.ADMIN_EMAIL,
        "name": "Admin",
        "role": "ADMIN",
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,
    }
    return jwt.encode(payload, settings.AUTH_SECRET, algorithm="HS256")


def authenticate_admin(admin_id: str, password: str) -> str | None:
    """
    Validate admin credentials against environment variables.
    Returns a signed JWT on success, None on failure.
    """
    from passlib.context import CryptContext

    settings = get_settings()

    if not settings.ADMIN_ID or not settings.ADMIN_PASSWORD_HASH:
        agent_logger.warn("AUTH", "Admin credentials not configured in .env")
        return None

    if admin_id != settings.ADMIN_ID:
        return None

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    if not pwd_context.verify(password, settings.ADMIN_PASSWORD_HASH):
        return None

    agent_logger.info("AUTH", "Admin authenticated successfully via web login")
    return create_admin_jwt()


async def get_current_user(request: Request) -> User:
    """
    FastAPI Dependency to authenticate users via NextAuth JWT tokens.

    Expects: Authorization: Bearer <jwt_token>

    In DEBUG mode with no token, returns a dev user with ADMIN role.
    """
    settings = get_settings()
    token = _extract_bearer_token(request)

    # Dev Mode Bypass
    if not token and settings.is_debug:
        agent_logger.debug("AUTH", "DEBUG mode: using dev user (no token provided)")
        return await user_repo.get_or_create(
            email="dev@localhost",
            name="Dev User",
            picture="",
            role="ADMIN",
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Send session token as Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify JWT Token
    payload = _verify_jwt_token(token)

    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing email.",
        )

    name = payload.get("name", "")
    picture = payload.get("picture", "")
    role = payload.get("role", "GUEST")

    # Admin emails are automatically promoted to ADMIN role
    if settings.ADMIN_EMAIL and email.lower() == settings.ADMIN_EMAIL.lower():
        role = "ADMIN"

    return await user_repo.get_or_create(
        email=email, name=name, picture=picture, role=role,
    )


async def get_admin_user(request: Request) -> User:
    """
    FastAPI Dependency that ensures the caller is an authenticated ADMIN.
    Returns 403 Forbidden if the user is not an admin.
    """
    user = await get_current_user(request)

    if user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. This endpoint is restricted.",
        )

    return user
