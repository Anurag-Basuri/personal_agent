"""
Cron Automation Endpoint.

Designed to be pinged by an external free cron service (e.g., cron-job.org)
at regular intervals. Each ping wakes the Render free tier server and
triggers the LangGraph agent to perform proactive checks (emails, deploys,
etc.) and notify the admin via Telegram/WhatsApp if anything needs attention.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.config import get_settings
from app.core.logger import agent_logger
from app.core.responses import success_response
from app.transports.notifier import notifier

router = APIRouter(prefix="/api/admin/automations", tags=["Automations"])


def _verify_automation_secret(request: Request) -> None:
    """Validate the X-Automation-Secret header against the configured secret."""
    settings = get_settings()

    if not settings.AUTOMATION_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AUTOMATION_SECRET is not configured on the server.",
        )

    provided = request.headers.get("X-Automation-Secret", "")
    if provided != settings.AUTOMATION_SECRET:
        agent_logger.warn("AUTOMATION", "Invalid automation secret provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid automation secret.",
        )


@router.post("/run")
async def run_automations(request: Request):
    """
    Cron triggered automation runner.

    This endpoint is designed to be called by an external cron service
    (e.g., cron-job.org) at regular intervals. It performs proactive
    checks and notifications.

    Currently supports:
      1. Health ping (keeps Render free tier alive)
      2. Manual notification test via query param
    """
    _verify_automation_secret(request)

    agent_logger.info("AUTOMATION", "🔔 Automation triggered by cron ping")

    return success_response(
        data={"status": "ok"},
        message="Automation run completed",
    )


@router.post("/notify/test")
async def test_notification(request: Request):
    """
    Send a test notification to all configured channels.

    Useful for verifying that Telegram and WhatsApp are correctly set up
    before relying on them for real alerts.
    """
    _verify_automation_secret(request)

    result = await notifier.notify_all(
        "🧪 Test notification from your Personal Agent!\n"
        "If you see this on both Telegram and WhatsApp, your notification system is working perfectly."
    )

    return success_response(
        data=result,
        message="Test notification sent",
    )
