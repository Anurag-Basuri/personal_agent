"""
Admin health dashboard endpoint.

Provides a comprehensive view of the system's health, including
LLM cascade status, MCP server connections, circuit breaker states,
and overall degradation level.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import get_admin_user
from app.core.degradation import system_health
from app.core.responses import success_response
from app.mcp.client import mcp_manager
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["Admin Health"])


@router.get("/health")
async def admin_health_dashboard(admin_user: User = Depends(get_admin_user)):
    """Comprehensive system health dashboard for the admin.

    Returns status of all subsystems: LLMs, MCPs, circuit breakers, and health flags.
    """
    # Overall system health (degradation level + capabilities)
    health_status = system_health.get_status()

    # MCP Server Status
    mcp_status = mcp_manager.get_status()
    mcp_tools_count = len(mcp_manager.get_tools())
    mcp_connected = sum(1 for s in mcp_status.values() if s == "connected")
    mcp_failed = sum(1 for s in mcp_status.values() if s == "error")

    # Circuit Breaker States
    from app.agent.core.nodes import _llm_breakers
    breaker_status = {}
    for tier, breaker in _llm_breakers.items():
        breaker_status[f"tier_{tier}"] = {
            "name": breaker.name,
            "state": breaker.state,
            "failure_count": breaker._failure_count,
            "failure_threshold": breaker.failure_threshold,
        }

    return success_response(
        data={
            "degradation_level": health_status["level"],
            "capabilities": health_status["capabilities"],
            "subsystems": health_status["subsystems"],
            "llm_cascade": {
                "tiers_up": health_status["llm_tiers_up"],
                "tiers_total": health_status["llm_tiers_total"],
            },
            "mcp_servers": {
                "status": mcp_status,
                "connected": mcp_connected,
                "failed": mcp_failed,
                "total_tools": mcp_tools_count,
            },
            "circuit_breakers": breaker_status,
        },
        message="System health report",
    )
