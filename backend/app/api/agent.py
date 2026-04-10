"""Agent chat endpoints with advanced granular controls."""

from fastapi import APIRouter, Request, Depends, Query, HTTPException, Path

from app.core.exceptions import AgentError, RateLimitError
from app.core.logger import agent_logger
from app.core.memory import clear_session_memory, get_message_history
from app.core.responses import success_response
from app.core.auth import get_current_user
from app.models.user import User

from app.database import async_session
from sqlalchemy import select, delete
from app.models.agent_message import AgentMessage
from app.models.agent_session import AgentSession

from app.schemas.agent import (
    ChatRequest, ChatResponseData, 
    ResetRequest, ResetResponseData,
    EditMessageRequest, HistoryResponseData, MessageResponseItem
)
from app.agent.service import process_user_message

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
            raise RateLimitError("I'm currently experiencing high demand. Please try again in a few moments!")

        raise AgentError(message=error_msg or "Agent failed to process message")


@router.post("/reset")
async def reset_session(
    body: ResetRequest, 
    request: Request,
    current_user: User = Depends(get_current_user)
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


# --- 🚨 New CRUD Granular Endpoints 🚨 ---

@router.get("/history")
async def get_history(
    session_id: str = Query(..., description="The session ID to retrieve"),
    request: Request = None,
    current_user: User = Depends(get_current_user)
):
    """Retrieve fine-grained history for the UI."""
    request_id = getattr(request.state, "request_id", "")
    
    # We use a pure SQLAlchemy query directly to expose the granular text and IDs to the frontend
    # Since memory.py converts them back to LangChain objects which obfuscates the DB IDs.
    async with async_session() as db:
        result = await db.execute(
            select(AgentSession).where(AgentSession.sessionId == session_id, AgentSession.user_id == current_user.id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return success_response(data={"messages": []}, message="No history found", request_id=request_id)
            
        msg_result = await db.execute(
            select(AgentMessage).where(AgentMessage.session_id == session.id).order_by(AgentMessage.createdAt.asc())
        )
        db_messages = msg_result.scalars().all()
        
        output = []
        for m in db_messages:
            output.append(MessageResponseItem(
                id=m.id,
                role=m.role,
                content=m.content or "", # Transparently decrypted here via TypeDecorator!
                created_at=m.createdAt.isoformat()
            ))

    return success_response(
        data=HistoryResponseData(messages=output).model_dump(),
        message="History retrieved successfully",
        request_id=request_id
    )

@router.delete("/message/{message_id}")
async def delete_message(
    message_id: str = Path(...),
    request: Request = None,
    current_user: User = Depends(get_current_user)
):
    """Users can delete their own prompts to shape the memory block."""
    request_id = getattr(request.state, "request_id", "")
    
    async with async_session() as db:
        # Secure fetch to ensure user owns this message's session
        result = await db.execute(select(AgentMessage).where(AgentMessage.id == message_id))
        msg = result.scalar_one_or_none()
        
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")
            
        session_res = await db.execute(select(AgentSession).where(AgentSession.id == msg.session_id))
        session = session_res.scalar_one_or_none()
        
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized attempt to delete message")
            
        await db.execute(delete(AgentMessage).where(AgentMessage.id == message_id))
        await db.commit()
        
    return success_response(data={"deleted": True}, message="Message removed from memory.", request_id=request_id)

@router.put("/message/{message_id}")
async def edit_message(
    body: EditMessageRequest,
    message_id: str = Path(...),
    request: Request = None,
    current_user: User = Depends(get_current_user)
):
    """Edit a message. Useful for correcting typos before a LangGraph re-run."""
    request_id = getattr(request.state, "request_id", "")
    
    async with async_session() as db:
        result = await db.execute(select(AgentMessage).where(AgentMessage.id == message_id))
        msg = result.scalar_one_or_none()
        
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")
            
        session_res = await db.execute(select(AgentSession).where(AgentSession.id == msg.session_id))
        session = session_res.scalar_one_or_none()
        
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized attempt to edit message")
            
        # The encrypted decorator handles re-encryption automatically
        msg.content = body.new_content 
        await db.commit()
        
    return success_response(data={"edited": True}, message="Message updated in memory.", request_id=request_id)
