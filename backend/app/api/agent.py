"""
Agent chat endpoints for normal logged-in users.

Key rules:
  - Session ID is auto-generated from user.id (one conversation per account)
  - 50-message-per-session cap
  - Uses restricted portfolio-safe tools only (no MCP, no admin tools)
  - Persistent memory (preferences, summaries) across sessions
  - Delete-all endpoint to wipe conversation and start fresh
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import StreamingResponse

from app.agent.agent_service import (
    UserAgentResponse,
    get_user_message_counter,
    process_user_agent_message,
    process_user_agent_message_stream,
)
from app.core.auth import get_current_user
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
    AgentChatRequest,
    AgentChatResponseData,
    EditMessageRequest,
    HistoryResponseData,
    MessageResponseItem,
    ResetResponseData,
)

router = APIRouter(prefix="/api/agent/chat", tags=["Agent"])


def _get_user_session_id(user: User) -> str:
    """Generate a deterministic session ID from the user's primary key."""
    return f"agent_session_{user.id}"


@router.post("/")
async def send_message(
    body: AgentChatRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(rate_limit("chat")),
):
    """Send a message to the AI agent and receive a response.

    Session is auto-generated from the user's account (one conversation per user).
    Normal users get portfolio-safe tools only, with persistent memory.
    """
    request_id = getattr(request.state, "request_id", "")
    session_id = _get_user_session_id(current_user)

    try:
        response = await process_user_agent_message(
            message=body.message,
            session_id=session_id,
            user_id=current_user.id,
            current_url=body.currentUrl,
        )

        return success_response(
            data=AgentChatResponseData(
                reply=response.reply,
                sessionId=response.session_id,
                messagesRemaining=response.messages_remaining,
            ).model_dump(by_alias=True),
            message="Message processed successfully",
            request_id=request_id,
        )

    except Exception as e:
        agent_logger.error("CTRL", "User chat request failed", e, {
            "session_id": session_id,
        })
        classify_and_raise(e)


@router.post("/stream")
async def user_stream_message(
    body: AgentChatBody,
    request: Request,
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(rate_limit("chat")),
):
    """Send a message to the AI agent and stream the response token-by-token."""
    session_id = _get_user_session_id(current_user)

    try:
        generator = process_user_agent_message_stream(
            message=body.message,
            session_id=session_id,
            user_id=current_user.id,
            request=request,
            current_url=body.currentUrl,
        )

        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store"}
        )

    except Exception as e:
        agent_logger.error("CTRL", "User chat stream request failed", e, {
            "session_id": session_id,
        })
        classify_and_raise(e)


@router.post("/reset")
async def reset_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(rate_limit("chat_reset")),
):
    """Clear the user's agent session memory and restart the conversation."""
    request_id = getattr(request.state, "request_id", "")
    session_id = _get_user_session_id(current_user)

    await clear_session_memory(session_id)

    # Reset the in-memory message counter
    counter = get_user_message_counter()
    counter.reset(session_id)

    agent_logger.info("MEMORY", "User session memory cleared", {"session_id": session_id})
    return success_response(
        data=ResetResponseData(cleared=True).model_dump(),
        message="Conversation cleared. You can start fresh!",
        request_id=request_id,
    )


@router.delete("/delete-all")
async def delete_all_history(
    request: Request,
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(rate_limit("chat_reset")),
):
    """Permanently delete ALL chat history and memories for this user.

    This is the nuclear option. Wipes messages, session, summaries,
    and preferences. The user starts with a completely blank slate.
    """
    request_id = getattr(request.state, "request_id", "")
    session_id = _get_user_session_id(current_user)

    # Clear message history
    await clear_session_memory(session_id)

    # Clear persistent memories (summaries, preferences, facts)
    await memory_repo.delete_all_for_user(current_user.id)

    # Reset in-memory counter
    counter = get_user_message_counter()
    counter.reset(session_id)

    agent_logger.info("MEMORY", "ALL user data deleted", {"user_id": current_user.id})
    return success_response(
        data={"deleted": True},
        message="All conversation history and memories permanently deleted.",
        request_id=request_id,
    )


@router.get("/history")
async def get_history(
    request: Request,
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(rate_limit("chat_history")),
):
    """Retrieve the user's chat history."""
    request_id = getattr(request.state, "request_id", "")
    session_id = _get_user_session_id(current_user)

    session = await session_repo.get_by_session_id_and_user(session_id, current_user.id)

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
        message="History retrieved successfully",
        request_id=request_id,
    )


@router.delete("/message/{message_id}")
async def delete_message(
    message_id: str = Path(...),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(rate_limit("chat_message_edit")),
):
    """Delete a specific message from the conversation."""
    request_id = getattr(request.state, "request_id", "")

    session = await message_repo.get_session_for_message(message_id)

    if not session:
        raise HTTPException(status_code=404, detail="Message not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    await message_repo.delete_by_id(message_id)

    return success_response(data={"deleted": True}, message="Message removed.", request_id=request_id)


@router.put("/message/{message_id}")
async def edit_message(
    body: EditMessageRequest,
    message_id: str = Path(...),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(rate_limit("chat_message_edit")),
):
    """Edit a message content."""
    request_id = getattr(request.state, "request_id", "")

    session = await message_repo.get_session_for_message(message_id)

    if not session:
        raise HTTPException(status_code=404, detail="Message not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    await message_repo.update_content(message_id, body.new_content)

    return success_response(data={"edited": True}, message="Message updated.", request_id=request_id)
