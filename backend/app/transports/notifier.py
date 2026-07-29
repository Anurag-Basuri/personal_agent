"""
Unified Notification Service.

Provides a single interface to push messages to the admin across
all configured channels (Telegram, WhatsApp). The agent and the
automation system use this instead of calling transports directly.

Uses lazy imports to avoid circular dependency with the agent tools.
"""

from __future__ import annotations

import asyncio

from app.core.logger import agent_logger


class Notifier:
    """
    Unified notification dispatcher.

    Sends messages to one or all configured channels.
    Each channel fails independently so a broken WhatsApp config
    does not prevent Telegram from working.
    """

    async def notify_telegram(self, message: str) -> dict:
        """Push a message to the admin's Telegram chat."""
        from app.transports.telegram import send_telegram_push
        return await send_telegram_push(message)

    async def notify_whatsapp(self, message: str) -> dict:
        """Push a message to the admin's WhatsApp via CallMeBot."""
        from app.transports.whatsapp import send_whatsapp_message
        return await send_whatsapp_message(message)

    async def notify_all(self, message: str) -> dict:
        """
        Push a message to ALL configured channels simultaneously.

        Each channel runs concurrently and fails independently.
        Returns a summary of which channels succeeded.
        """
        agent_logger.info("NOTIFIER", f"Broadcasting notification ({len(message)} chars)")

        telegram_result, whatsapp_result = await asyncio.gather(
            self.notify_telegram(message),
            self.notify_whatsapp(message),
            return_exceptions=True,
        )

        # Handle exceptions from gather
        if isinstance(telegram_result, Exception):
            agent_logger.error("NOTIFIER", f"Telegram failed in broadcast: {telegram_result}")
            telegram_result = {"status": "error", "detail": str(telegram_result)}
        if isinstance(whatsapp_result, Exception):
            agent_logger.error("NOTIFIER", f"WhatsApp failed in broadcast: {whatsapp_result}")
            whatsapp_result = {"status": "error", "detail": str(whatsapp_result)}

        delivered_count = sum(
            1 for r in [telegram_result, whatsapp_result]
            if isinstance(r, dict) and r.get("status") == "sent"
        )

        agent_logger.info("NOTIFIER", f"Broadcast complete: {delivered_count}/2 channels delivered")

        return {
            "telegram": telegram_result,
            "whatsapp": whatsapp_result,
            "delivered_count": delivered_count,
        }


# Singleton
notifier = Notifier()
