"""Agent chat endpoints with advanced granular controls."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from app.agent.service import process_user_message
from app.core.auth import get_current_user
from app.core.exceptions import AgentError, RateLimitError
from app.core.logger import agent_logger
from app.core.memory import clear_session_memory
from app.core.rate_limiter import rate_limit
from app.core.responses import success_response
from app.models.user import User
from app.repositories.message_repo import message_repo
from app.repositories.session_repo import session_repo
from app.schemas.agent import (
    ChatRequest,
    ChatResponseData,
    EditMessageRequest,
    HistoryResponseData,
    MessageResponseItem,
    ResetRequest,
    ResetResponseData,
)

router = APIRouter(prefix="/api/agent/chat", tags=["Agent"])


@router.post("/")
async def send_message(
    body: ChatRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(rate_limit("chat")),
):
    """Send a message to the AI agent and receive a response."""
    request_id = getattr(request.state, "request_id", "")

    try:
        response = await process_user_message(
            message=body.message,
            session_id=body.sessionId,
            current_url=body.currentUrl,
            user_id=current_user.id,
        )

        agent_logger.debug("CTRL", "Agent Reply", {
            "reply": response.reply[:100],
            "session_id": response.session_id,
        })

        return success_response(
            data=ChatResponseData(
                reply=response.reply,
                intents=[],
                sessionId=response.session_id,
            ).model_dump(by_alias=True),
            message="Message processed successfully by Agent",
            request_id=request_id,
        )

    except Exception as e:
        error_msg = str(e)
        is_rate_limit = "Quota" in error_msg or "429" in error_msg
        is_timeout = "timeout" in error_msg.lower() or "TimeoutError" in error_msg

        agent_logger.error("CTRL", "Request failed", e, {
            "session_id": body.sessionId,
            "category": "RATE_LIMIT" if is_rate_limit else "TIMEOUT" if is_timeout else "INTERNAL",
        })

        if is_rate_limit:
            raise RateLimitError("I'm currently experiencing high demand. Please try again in a few moments!")

        raise AgentError(message=error_msg or "Agent failed to process message")


@router.post("/reset")
async def reset_session(
    body: ResetRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(rate_limit("chat_reset")),
):
    """Clear whole agent session memory."""
    request_id = getattr(request.state, "request_id", "")
    await clear_session_memory(body.sessionId)
    agent_logger.info("MEMORY", "Session memory cleared", {"session_id": body.sessionId})
    return success_response(
        data=ResetResponseData(cleared=True).model_dump(),
        message="Agent session memory cleared",
        request_id=request_id,
    )


# Granular CRUD Endpoints
@router.get("/history")
async def get_history(
    session_id: str = Query(..., description="The session ID to retrieve"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(rate_limit("chat_history")),
):
    """Retrieve fine grained history for the UI."""
    request_id = getattr(request.state, "request_id", "")

    session = await session_repo.get_by_session_id_and_user(session_id, current_user.id)

    if not session:
        return success_response(data={"messages": []}, message="No history found", request_id=request_id)

    db_messages = await message_repo.get_by_session(session.id)

    output = [
        MessageResponseItem(
            id=m.id,
            role=m.role,
            # Transparently decrypted via TypeDecorator
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
    """Users can delete their own prompts to shape the memory block."""
    request_id = getattr(request.state, "request_id", "")

    session = await message_repo.get_session_for_message(message_id)

    if not session:
        raise HTTPException(status_code=404, detail="Message not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized attempt to delete message")

    await message_repo.delete_by_id(message_id)

    return success_response(data={"deleted": True}, message="Message removed from memory.", request_id=request_id)


@router.put("/message/{message_id}")
async def edit_message(
    body: EditMessageRequest,
    message_id: str = Path(...),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(rate_limit("chat_message_edit")),
):
    """Edit a message. Useful for correcting typos before a LangGraph re run."""
    request_id = getattr(request.state, "request_id", "")

    session = await message_repo.get_session_for_message(message_id)

    if not session:
        raise HTTPException(status_code=404, detail="Message not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized attempt to edit message")

    await message_repo.update_content(message_id, body.new_content)

    return success_response(data={"edited": True}, message="Message updated in memory.", request_id=request_id)
