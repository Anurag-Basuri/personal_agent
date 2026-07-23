"""Pydantic schemas for the public portfolio chatbot endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PublicChatRequest(BaseModel):
    """POST /api/public/chat request body."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Visitor's message",
    )
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Ephemeral session ID (from browser sessionStorage)",
    )
    current_url: str | None = Field(
        None,
        description="Page the visitor is currently viewing on the portfolio site",
    )


class PublicChatResponseData(BaseModel):
    """Data payload inside the public chat success response."""

    reply: str
    session_id: str
    messages_remaining: int = Field(
        ...,
        description="Number of messages the visitor can still send in this session",
    )
