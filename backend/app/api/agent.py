"""Agent chat endpoints."""

from fastapi import APIRouter, Request, Depends

from app.core.exceptions import AgentError, RateLimitError
from app.core.logger import agent_logger
from app.core.memory import clear_session_memory
from app.core.responses import success_response
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.agent import ChatRequest, ChatResponseData, ResetRequest, ResetResponseData
from app.services.agent import process_user_message

router = APIRouter(prefix="/chat", tags=["Agent"])


@router.post("/")
async def send_message(
    body: ChatRequest, 
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Send a message to the AI agent and receive a response."""
    request_id = getattr(request.state, "request_id", "")

    try:
        response = await process_user_message(
            message=body.message,
            session_id=body.sessionId,
            current_url=body.currentUrl,
            user_id=current_user.id
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
            raise RateLimitError(
                "I'm currently experiencing high demand. Please try again in a few moments!"
            )

        raise AgentError(
            message=error_msg or "Agent failed to process message",
            errors=["AgentController.send_message"],
        )


@router.post("/reset")
async def reset_session(
    body: ResetRequest, 
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Clear agent session memory."""
    request_id = getattr(request.state, "request_id", "")

    await clear_session_memory(body.sessionId)
    agent_logger.info("MEMORY", "Session memory cleared", {"session_id": body.sessionId})

    return success_response(
        data=ResetResponseData(cleared=True).model_dump(),
        message="Agent session memory cleared",
        request_id=request_id,
    )
