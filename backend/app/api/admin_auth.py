"""
Admin authentication endpoint.

Provides a dedicated login flow for the admin user (Anurag).
Completely separate from the normal user Google OAuth / credentials flow.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import authenticate_admin
from app.core.logger import agent_logger
from app.core.responses import success_response

router = APIRouter(prefix="/api/admin", tags=["Admin Auth"])


class AdminLoginRequest(BaseModel):
    """POST /api/admin/login request body."""
    admin_id: str = Field(..., min_length=1, description="The admin identifier")
    password: str = Field(..., min_length=1, description="The admin password")


class AdminLoginResponseData(BaseModel):
    """Successful admin login response."""
    token: str
    role: str = "ADMIN"


@router.post("/login")
async def admin_login(body: AdminLoginRequest):
    """Authenticate as admin using custom ID + password.

    Returns a signed JWT with role=ADMIN on success.
    This JWT must be sent as a Bearer token for all /api/admin/* endpoints.
    """
    token = authenticate_admin(body.admin_id, body.password)

    if not token:
        agent_logger.warn("AUTH", f"Failed admin login attempt for ID: {body.admin_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials.",
        )

    return success_response(
        data=AdminLoginResponseData(token=token).model_dump(),
        message="Admin authenticated successfully",
    )
