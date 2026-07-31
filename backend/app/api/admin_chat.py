"""
Admin chat endpoints.

Full unrestricted access to ALL tools, MCP servers, Google Workspace,
and the complete ADMIN_PERSONA prompt. Only accessible by the admin user.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Request

from app.agent.service import process_user_message
from app.core.auth import get_admin_user
from app.core.exceptions import classify_and_raise
from app.core.logger import agent_logger
from app.core.memory import clear_session_memory
from app.core.rate_limiter import rate_limit
from app.core.responses import success_response
from app.models.user import User
from app.repositories.memory_repo import memory_repo
from app.repositories.message_repo import message_repo
from app.repositories.session_repo import session_repo
from app.schemas.agent import (
    EditMessageRequest,
    HistoryResponseData,
    MessageResponseItem,
    ResetResponseData,
)

router = APIRouter(prefix="/api/admin/chat", tags=["Admin Chat"])


def _get_admin_session_id(user: User) -> str:
    """Generate a deterministic session ID for the admin."""
    return f"admin_session_{user.id}"


class AdminChatRequest:
    """Dependency that extracts the message from the request body."""
    pass


from pydantic import BaseModel, Field


class AdminChatBody(BaseModel):
    """POST /api/admin/chat request body."""
    message: str = Field(..., min_length=1, max_length=5000, description="Admin message")
    currentUrl: str | None = Field(None, description="Current page URL")


class AdminChatResponseData(BaseModel):
    """Admin chat response payload."""
    reply: str
    sessionId: str


@router.post("/")
async def admin_send_message(
    body: AdminChatBody,
    request: Request,
    admin_user: User = Depends(get_admin_user),
    _rate: None = Depends(rate_limit("admin_chat")),
):
    """Send a message to the admin's unrestricted AI agent.

    Full access to ALL tools including MCP servers, Google Workspace,
    deployment tools, and every capability in the system.
    """
    request_id = getattr(request.state, "request_id", "")
    session_id = _get_admin_session_id(admin_user)

    try:
        response = await process_user_message(
            message=body.message,
            session_id=session_id,
            user_id=admin_user.id,
            current_url=body.currentUrl,
        )

        return success_response(
            data=AdminChatResponseData(
                reply=response.reply,
                sessionId=response.session_id,
            ).model_dump(by_alias=True),
            message="Admin message processed",
            request_id=request_id,
        )

    except Exception as e:
        agent_logger.error("ADMIN", "Admin chat request failed", e, {
            "session_id": session_id,
        })
        classify_and_raise(e)


@router.post("/reset")
async def admin_reset_session(
    request: Request,
    admin_user: User = Depends(get_admin_user),
):
    """Clear the admin's chat session memory."""
    request_id = getattr(request.state, "request_id", "")
    session_id = _get_admin_session_id(admin_user)

    await clear_session_memory(session_id)

    agent_logger.info("ADMIN", "Admin session memory cleared", {"session_id": session_id})
    return success_response(
        data=ResetResponseData(cleared=True).model_dump(),
        message="Admin session cleared",
        request_id=request_id,
    )


@router.get("/history")
async def admin_get_history(
    request: Request,
    admin_user: User = Depends(get_admin_user),
):
    """Retrieve the admin's full chat history."""
    request_id = getattr(request.state, "request_id", "")
    session_id = _get_admin_session_id(admin_user)

    session = await session_repo.get_by_session_id_and_user(session_id, admin_user.id)

    if not session:
        return success_response(data={"messages": []}, message="No history found", request_id=request_id)

    db_messages = await message_repo.get_by_session(session.id)

    output = [
        MessageResponseItem(
            id=m.id,
            role=m.role,
            content=m.content or "",
            created_at=m.createdAt.isoformat(),
        )
        for m in db_messages
    ]

    return success_response(
        data=HistoryResponseData(messages=output).model_dump(),
        message="Admin history retrieved",
        request_id=request_id,
    )


@router.delete("/message/{message_id}")
async def admin_delete_message(
    message_id: str = Path(...),
    request: Request = None,
    admin_user: User = Depends(get_admin_user),
):
    """Admin can delete any message from the conversation."""
    request_id = getattr(request.state, "request_id", "")

    session = await message_repo.get_session_for_message(message_id)

    if not session:
        raise HTTPException(status_code=404, detail="Message not found")

    await message_repo.delete_by_id(message_id)

    return success_response(data={"deleted": True}, message="Message removed.", request_id=request_id)
