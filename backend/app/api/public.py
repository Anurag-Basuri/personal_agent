"""
Public portfolio chatbot endpoints.

These endpoints require NO authentication. They serve the embedded
chat widget on the portfolio website. Sessions are ephemeral
(cleaned up after 1 hour of inactivity) and capped at 20 messages.

Route prefix: /api/public
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.agent.public_service import process_public_message
from app.core.exceptions import AgentError, RateLimitError, classify_and_raise
from app.core.logger import agent_logger
from app.core.rate_limiter import rate_limit
from app.core.responses import success_response
from app.schemas.public import PublicChatRequest, PublicChatResponseData

router = APIRouter(prefix="/api/public", tags=["Public Portfolio Chatbot"])


@router.post("/chat")
async def public_chat(
    body: PublicChatRequest,
    request: Request,
    _rate: None = Depends(rate_limit("public_chat")),
):
    """Send a message to the portfolio chatbot.

    No authentication required. Session is ephemeral and scoped
    to the visitor's browser tab via sessionStorage.

    Returns the agent's reply and how many messages remain in
    this session (out of the 20-message cap).
    """
    request_id = getattr(request.state, "request_id", "")

    try:
        response = await process_public_message(
            message=body.message,
            session_id=body.session_id,
            current_url=body.current_url,
        )

        return success_response(
            data=PublicChatResponseData(
                reply=response.reply,
                session_id=response.session_id,
                messages_remaining=response.messages_remaining,
            ).model_dump(),
            message="Message processed",
            request_id=request_id,
        )

    except ValueError as e:
        # Message cap exceeded
        raise HTTPException(
            status_code=429,
            detail=str(e),
        )

    except Exception as e:
        agent_logger.error("PUBLIC", "Public chat request failed", e, {
            "session_id": body.session_id[:16] + "...",
        })
        classify_and_raise(e)


@router.get("/health")
async def public_health():
    """Lightweight health check for the portfolio chat widget.

    Returns a simple status so the widget knows the backend is alive.
    Does not expose internal system details.
    """
    return success_response(
        data={"status": "ok"},
        message="Portfolio chatbot is operational",
    )
