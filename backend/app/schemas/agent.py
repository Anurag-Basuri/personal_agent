"""Pydantic schemas for agent chat endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /chat request body."""

    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    sessionId: str = Field(..., min_length=1, description="Session identifier")
    currentUrl: str | None = Field(None, description="Page the user is currently viewing")


class ChatResponseData(BaseModel):
    """Data payload inside success response."""

    reply: str
    intents: list[str] = []
    sessionId: str


class ResetRequest(BaseModel):
    """POST /chat/reset request body."""

    sessionId: str = Field(..., min_length=1, description="Session to clear")


class ResetResponseData(BaseModel):
    """Data payload for reset response."""

    cleared: bool = True
