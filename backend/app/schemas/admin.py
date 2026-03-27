"""Pydantic schemas for admin endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AgentSessionOut(BaseModel):
    """Single session in the admin list."""

    id: str
    sessionId: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
