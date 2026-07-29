"""
WhatsApp Transport — CallMeBot Integration.

Sends WhatsApp messages to the admin using the free CallMeBot API.
This is a one way notification channel (outbound only).

Setup:
  1. Save CallMeBot's number (+34 623 80 11 90) to your phone contacts
  2. Send "I allow callmebot to send me messages" to the bot on WhatsApp
  3. Copy the API key the bot replies with
  4. Set CALLMEBOT_PHONE and CALLMEBOT_API_KEY in your .env
"""

from __future__ import annotations

import urllib.parse

import httpx

from app.core.logger import agent_logger
from app.core.retry import retry_with_backoff


_CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"


async def _send_request(phone: str, apikey: str, text: str) -> httpx.Response:
    """Fire the CallMeBot GET request."""
    encoded_text = urllib.parse.quote(text)
    url = f"{_CALLMEBOT_URL}?phone={phone}&text={encoded_text}&apikey={apikey}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.get(url)


async def send_whatsapp_message(text: str) -> dict:
    """
    Send a WhatsApp notification to the admin via CallMeBot.

    Returns a dict with status and detail for structured logging.
    """
    from app.config import get_settings
    settings = get_settings()

    if not settings.CALLMEBOT_PHONE or not settings.CALLMEBOT_API_KEY:
        agent_logger.warn("WHATSAPP", "CallMeBot not configured (missing CALLMEBOT_PHONE or CALLMEBOT_API_KEY)")
        return {"status": "skipped", "detail": "CallMeBot not configured"}

    try:
        response = await retry_with_backoff(
            _send_request,
            settings.CALLMEBOT_PHONE,
            settings.CALLMEBOT_API_KEY,
            text,
            max_retries=2,
            base_delay=2.0,
            retryable_exceptions=(TimeoutError, ConnectionError, httpx.TimeoutException),
            operation_name="WhatsApp:CallMeBot",
        )

        if response.status_code == 200:
            agent_logger.info("WHATSAPP", "✅ WhatsApp notification sent successfully")
            return {"status": "sent", "detail": "Message delivered via CallMeBot"}

        agent_logger.warn("WHATSAPP", f"CallMeBot returned HTTP {response.status_code}", {
            "response": response.text[:200]
        })
        return {"status": "failed", "detail": f"HTTP {response.status_code}"}

    except Exception as e:
        agent_logger.error("WHATSAPP", f"Failed to send WhatsApp notification: {e}")
        return {"status": "error", "detail": str(e)}
