"""
User Authentication Endpoints (Agent Website).

These endpoints are used by the Next.js frontend (NextAuth) to handle
Credentials-based authentication (Email / Password).

Uses UserRepository for all database operations (Repository Pattern).
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
import bcrypt

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.responses import success_response
from app.repositories.user_repo import user_repo

router = APIRouter(prefix="/api/agent/auth", tags=["User Auth"])


class RegisterRequest(BaseModel):
    """POST /api/agent/auth/register request body."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class VerifyRequest(BaseModel):
    """POST /api/agent/auth/verify request body."""
    email: EmailStr
    password: str = Field(..., min_length=1)


@router.post("/register")
async def register_user(body: RegisterRequest):
    """Register a new user with email and password.

    All registered users get role=GUEST. Admin access is separate.
    """
    existing = await user_repo.get_by_email(body.email)
    if existing:
        raise ConflictError("Email already registered.")

    hashed_password = bcrypt.hashpw(body.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = await user_repo.create_with_password(
        email=body.email,
        name=body.name,
        hashed_password=hashed_password,
    )

    return success_response(
        data={"id": user.id, "email": user.email, "name": user.name},
        message="User registered successfully",
    )


@router.post("/verify")
async def verify_user(body: VerifyRequest):
    """Verify email and password for NextAuth CredentialsProvider."""
    user = await user_repo.get_by_email(body.email)

    if not user:
        raise AuthenticationError("Invalid email or password.")

    if not user.hashed_password:
        raise AuthenticationError("Please sign in with Google.")

    if not bcrypt.checkpw(body.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise AuthenticationError("Invalid email or password.")

    return success_response(
        data={"id": user.id, "email": user.email, "name": user.name},
        message="Credentials verified",
    )
