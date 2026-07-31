"""Pydantic schemas for agent chat endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """POST /api/agent/chat/ request body.

    Note: sessionId is NOT accepted from client.
    It is auto-generated from the user's account ID.
    """
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    currentUrl: str | None = Field(None, description="Page the user is currently viewing")


class AgentChatResponseData(BaseModel):
    """Data payload inside success response for agent chat."""
    reply: str
    sessionId: str
    messagesRemaining: int


class ResetResponseData(BaseModel):
    """Response for session reset."""
    cleared: bool = True


class EditMessageRequest(BaseModel):
    """PUT /chat/message/{id} request body."""
    new_content: str = Field(..., min_length=1, description="The updated text content of the message.")


class MessageResponseItem(BaseModel):
    """Represents a single granular message."""
    id: str
    role: str
    content: str
    created_at: str


class HistoryResponseData(BaseModel):
    """Data payload for /chat/history response."""
    messages: list[MessageResponseItem]
