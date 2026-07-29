"""
Notification tools for the LangGraph agent.

Allows the LLM to proactively send messages to the admin
via Telegram or WhatsApp. These are admin only tools.
"""

from langchain_core.tools import tool

from app.transports.notifier import notifier


def _mark_admin(t):
    """Mark a tool as admin only, bypassing Pydantic field validation."""
    object.__setattr__(t, "requires_admin", True)
    return t


@_mark_admin
@tool
async def send_telegram_notification(message: str) -> str:
    """Send a push notification to the admin's Telegram.

    Use this tool when you need to proactively alert the admin about
    something important, like a failed deployment, an urgent email,
    or a scheduled reminder. The message should be concise and actionable.

    Args:
        message: The notification text to send (plain text, keep under 4000 chars)
    """
    result = await notifier.notify_telegram(message)
    status = result.get("status", "unknown")
    if status == "sent":
        return "Telegram notification sent successfully."
    elif status == "skipped":
        return "Telegram is not configured. Notification was not sent."
    return f"Telegram notification failed: {result.get('detail', 'unknown error')}"


@_mark_admin
@tool
async def send_whatsapp_notification(message: str) -> str:
    """Send a WhatsApp notification to the admin via CallMeBot.

    Use this tool when you need to proactively alert the admin on WhatsApp.
    Good for urgent notifications that need immediate attention, since
    WhatsApp is likely to be noticed faster than Telegram.

    Args:
        message: The notification text to send (plain text, keep under 1000 chars)
    """
    result = await notifier.notify_whatsapp(message)
    status = result.get("status", "unknown")
    if status == "sent":
        return "WhatsApp notification sent successfully."
    elif status == "skipped":
        return "WhatsApp (CallMeBot) is not configured. Notification was not sent."
    return f"WhatsApp notification failed: {result.get('detail', 'unknown error')}"


@_mark_admin
@tool
async def broadcast_notification(message: str) -> str:
    """Send a notification to ALL configured channels (Telegram + WhatsApp).

    Use this for critical alerts that the admin absolutely must see.
    The message is sent to every configured channel simultaneously.

    Args:
        message: The notification text to broadcast (plain text)
    """
    result = await notifier.notify_all(message)
    delivered = result.get("delivered_count", 0)
    return f"Broadcast complete: {delivered}/2 channels delivered successfully."
