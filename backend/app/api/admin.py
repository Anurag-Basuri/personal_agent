"""Admin endpoints for managing agent sessions."""

from fastapi import APIRouter, Depends, Request

from app.core.auth import get_current_user
from app.core.responses import paginated_response, success_response
from app.models.user import User
from app.repositories.session_repo import session_repo
from app.schemas.admin import AgentSessionOut

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/agent-sessions")
async def get_agent_sessions(
    request: Request,
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
):
    """List all agent sessions (paginated)."""
    request_id = getattr(request.state, "request_id", "")

    sessions, total = await session_repo.list_by_user(current_user.id, page, limit)

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
    current_user: User = Depends(get_current_user),
):
    """Delete a specific agent session."""
    request_id = getattr(request.state, "request_id", "")

    deleted = await session_repo.delete_by_id(session_id, user_id=current_user.id)

    if not deleted:
        return success_response(
            data=None,
            message="Session already deleted",
            request_id=request_id,
        )

    return success_response(
        data=None,
        message="Agent session deleted successfully",
        request_id=request_id,
    )
