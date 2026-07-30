"""Health check endpoint with detailed subsystem status reporting."""

import time

from fastapi import APIRouter

from app.core.degradation import system_health
from app.core.responses import success_response

router = APIRouter(prefix="/api", tags=["Health"])

_start_time = time.time()


@router.get("/health")
async def health_check():
    """Detailed health check reporting status of all subsystems.

    Reports: database, LLM cascade, MCP servers, and RAG availability.
    Suitable for uptime monitoring tools that need to detect partial outages.
    """
    uptime_seconds = round(time.time() - _start_time)

    from app.agent.llm import get_provider_info
    from app.mcp.client import mcp_manager
    from app.rag.vector_store import RAG_AVAILABLE

    health_status = system_health.get_status()

    # Database connectivity check
    db_ok = False
    try:
        from app.database import _get_engine
        from sqlalchemy import text
        engine = _get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # LLM providers summary
    llm_providers = get_provider_info()

    # Aggregate subsystem statuses for monitoring
    subsystems = {
        "database": "up" if db_ok else "down",
        "llm_cascade": "up" if llm_providers else "down",
        "llm_tiers_available": len(llm_providers),
        "mcp": "up" if mcp_manager.connected_count > 0 else "degraded",
        "mcp_connected": mcp_manager.connected_count,
        "mcp_total_tools": len(mcp_manager.get_tools()),
        "rag": "up" if RAG_AVAILABLE else "unavailable",
    }

    # Overall status: healthy only if DB and at least one LLM are up
    if not db_ok:
        overall = "unhealthy"
    elif not llm_providers:
        overall = "degraded"
    elif mcp_manager.connected_count == 0:
        overall = "degraded"
    else:
        overall = health_status["level"]

    return success_response(
        data={
            "status": overall,
            "subsystems": subsystems,
            "capabilities": health_status["capabilities"],
            "llm_providers": llm_providers,
            "mcp_servers": mcp_manager.get_status(),
            "version": "2.0.0",
            "runtime": "python/fastapi",
            "uptime_seconds": uptime_seconds,
        },
        message="Server is healthy" if overall != "unhealthy" else "Server is degraded",
    )

