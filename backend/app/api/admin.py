"""Admin endpoints for managing agent sessions."""

from fastapi import APIRouter, Request, Depends

from sqlalchemy import func, select, delete

from app.core.exceptions import NotFoundError
from app.core.responses import paginated_response, success_response
from app.core.auth import get_current_user
from app.models.user import User
from app.database import async_session
from app.models.agent_session import AgentSession
from app.schemas.admin import AgentSessionOut

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/agent-sessions")
async def get_agent_sessions(
    request: Request, 
    page: int = 1, 
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """List all agent sessions (paginated)."""
    request_id = getattr(request.state, "request_id", "")
    skip = (page - 1) * limit

    async with async_session() as db:
        # Get paginated sessions filtering by current_user.id
        stmt = (
            select(AgentSession)
            .where(AgentSession.user_id == current_user.id)
            .order_by(AgentSession.updatedAt.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        sessions = result.scalars().all()

        # Get total count
        count_result = await db.execute(select(func.count(AgentSession.id)))
        total = count_result.scalar() or 0

    items = [AgentSessionOut.model_validate(s).model_dump() for s in sessions]

    return paginated_response(
        items=items,
        total=total,
        page=page,
        limit=limit,
        message="Agent sessions retrieved successfully",
        request_id=request_id,
    )


@router.delete("/agent-sessions/{session_id}")
async def delete_agent_session(
    session_id: str, 
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Delete a specific agent session."""
    request_id = getattr(request.state, "request_id", "")

    async with async_session() as db:
        result = await db.execute(
            select(AgentSession).where(
                AgentSession.id == session_id,
                AgentSession.user_id == current_user.id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            # Idempotent — already deleted is OK
            return success_response(
                data=None,
                message="Session already deleted",
                request_id=request_id,
            )

        await db.execute(delete(AgentSession).where(AgentSession.id == session_id))
        await db.commit()

    return success_response(
        data=None,
        message="Agent session deleted successfully",
        request_id=request_id,
    )
