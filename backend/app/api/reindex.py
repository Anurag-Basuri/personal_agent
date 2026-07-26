"""RAG Reindex webhook endpoint.

Provides a secure endpoint that can be called by the portfolio CMS
to trigger a re-ingestion of portfolio data into the vector store.

Usage:
    POST /api/admin/reindex
    Headers: X-Reindex-Secret: <your_secret>
    Response: 202 Accepted (ingestion runs in background)
"""

import asyncio

from fastapi import APIRouter, Header, HTTPException

from app.config import get_settings
from app.core.logger import agent_logger
from app.core.responses import success_response

router = APIRouter(prefix="/api/admin", tags=["Admin RAG"])


async def _run_ingestion_background():
    """Run the RAG ingestion pipeline in the background."""
    try:
        from app.rag.ingester import run_ingestion
        await run_ingestion()
        agent_logger.info("RAG", "✅ Background re-ingestion completed successfully")
    except Exception as e:
        agent_logger.error("RAG", f"❌ Background re-ingestion failed: {e}")


@router.post("/reindex")
async def trigger_reindex(
    x_reindex_secret: str = Header(..., alias="X-Reindex-Secret"),
):
    """Trigger a RAG vector store re ingestion.

    Protected by a shared secret header. Call this from your portfolio
    CMS after any data update (profile save, project publish, etc.).
    """
    settings = get_settings()

    if not settings.REINDEX_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Reindex endpoint is not configured. Set REINDEX_SECRET in .env.",
        )

    if x_reindex_secret != settings.REINDEX_SECRET:
        raise HTTPException(status_code=403, detail="Invalid reindex secret.")

    # Fire and forget don't block the webhook response
    asyncio.create_task(_run_ingestion_background())

    agent_logger.info("RAG", "🔄 Reindex triggered via webhook — running in background")

    return success_response(
        data={"status": "accepted"},
        message="Re-ingestion triggered and running in the background.",
        status_code=202,
    )
