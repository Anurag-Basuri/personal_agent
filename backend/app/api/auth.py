"""
Internal Authentication Endpoints.

These endpoints are used by the Next.js frontend (NextAuth) to handle
Credentials based authentication (Email / Password).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext

from app.database import get_db
from app.models.user import User
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.responses import success_response
import uuid

router = APIRouter(prefix="/api/agent/auth", tags=["Internal Auth"])

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class VerifyRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
async def register_user(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user with email and password."""
    # Check if user exists
    result = await db.execute(select(User).where(User.email == body.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise ConflictError("Email already registered.")

    # Hash the password
    hashed_password = pwd_context.hash(body.password)

    new_user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        name=body.name,
        hashed_password=hashed_password,
        role="GUEST"
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return success_response(
        data={"id": new_user.id, "email": new_user.email, "name": new_user.name},
        message="User registered successfully"
    )

@router.post("/verify")
async def verify_user(body: VerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify email and password for NextAuth CredentialsProvider."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("Invalid email or password.")

    if not user.hashed_password:
        raise AuthenticationError("Please sign in with Google.")

    if not pwd_context.verify(body.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password.")

    return success_response(
        data={"id": user.id, "email": user.email, "name": user.name},
        message="Credentials verified"
    )
