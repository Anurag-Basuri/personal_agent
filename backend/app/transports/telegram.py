"""
Telegram Transport Layer — Admin-Only.

Handles receiving messages from Telegram, validating users via a whitelist,
mapping chats to the admin's real User row, and sending responses back.

Only whitelisted Telegram user IDs (admin) can interact with the bot.
The bot uses the full admin agent service with ALL tools and MCP access.
"""

from __future__ import annotations

import json
import time
import logging

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from app.agent.service import process_user_message_stream
from app.config import get_settings
from app.core.logger import agent_logger

logger = logging.getLogger("telegram.bot")


async def _get_admin_user_id() -> str | None:
    """Get or create the admin User row and return its ID.

    Links the Telegram admin to the same User row used by web admin login.
    """
    settings = get_settings()
    if not settings.ADMIN_EMAIL:
        return None

    from app.repositories.user_repo import user_repo
    admin_user = await user_repo.get_or_create(
        email=settings.ADMIN_EMAIL,
        name="Anurag",
        role="ADMIN",
    )
    return admin_user.id


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming Telegram messages."""
    settings = get_settings()
    user = update.effective_user
    chat = update.effective_chat
    message_text = update.message.text

    if not user or not chat or not message_text:
        return

    # Auth: Only whitelisted user IDs can use the bot
    allowed_ids = settings.telegram_allowed_ids
    if allowed_ids and user.id not in allowed_ids:
        agent_logger.warn("TELEGRAM", f"Unauthorized access attempt from user {user.id}")
        await update.message.reply_text(
            "Access Denied. You are not authorized to use this bot.\n"
            f"Your Telegram ID is: `{user.id}`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    elif not allowed_ids:
        agent_logger.warn("TELEGRAM", "No TELEGRAM_ALLOWED_USER_IDS set. Telegram bot disabled for safety.")
        await update.message.reply_text("Bot is not configured. Contact the administrator.")
        return

    # Session Mapping: Use admin's real User row
    session_id = f"admin_tg_{chat.id}"
    admin_user_id = await _get_admin_user_id()

    if not admin_user_id:
        agent_logger.warn("TELEGRAM", "ADMIN_EMAIL not set. Cannot link Telegram to admin account.")
        await update.message.reply_text("Admin account not configured. Set ADMIN_EMAIL in .env.")
        return

    agent_logger.info("TELEGRAM", f"Admin message from {user.first_name}", {
        "session_id": session_id,
        "message_preview": message_text[:50],
    })

    # Process Message through the full admin agent (ALL tools + MCP)
    try:
        reply_message = await update.message.reply_text("Thinking...")

        generator = process_user_message_stream(
            message=message_text,
            session_id=session_id,
            request=None,
            user_id=admin_user_id,
        )

        current_text = ""
        last_edit_time = time.time()
        tool_status = ""

        async for chunk in generator:
            if not chunk.startswith("data: "):
                continue

            data_str = chunk[6:].strip()
            if not data_str:
                continue

            try:
                event = json.loads(data_str)
                kind = event.get("type")

                if kind == "token":
                    current_text += event.get("content", "")
                elif kind == "tool_start":
                    tool_status = f"\n\nCalling {event.get('name')}..."
                elif kind == "tool_end":
                    tool_status = ""

            except json.JSONDecodeError:
                continue

            # Throttle edits to 0.8 seconds (Telegram limit is ~1/sec)
            now = time.time()
            if now - last_edit_time > 0.8:
                display_text = current_text + tool_status
                if not display_text.strip():
                    continue
                try:
                    # Use plain text for intermediate streaming edits to avoid
                    # unclosed markdown entity errors from partial tokens.
                    await reply_message.edit_text(display_text)
                    last_edit_time = now
                except Exception as e:
                    if "Message is not modified" not in str(e):
                        agent_logger.debug("TELEGRAM", f"Intermediate edit skipped: {e}")

        # Final edit: attempt Markdown formatting, fall back to plain text
        display_text = current_text.strip()
        if not display_text:
            display_text = "I couldn't process that properly."

        try:
            await reply_message.edit_text(display_text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            try:
                await reply_message.edit_text(display_text)
            except Exception as e:
                if "Message is not modified" not in str(e):
                    agent_logger.error("TELEGRAM", "Final edit failed", e)

    except Exception as e:
        agent_logger.error("TELEGRAM", f"Error processing message: {e}", e)
        await update.message.reply_text("Sorry, I encountered an internal error while processing that.")


async def telegram_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unexpected errors from Telegram polling or handlers."""
    from telegram.error import Conflict, NetworkError
    if isinstance(context.error, Conflict):
        # A conflict occurs when multiple bot processes poll the same token concurrently
        agent_logger.warn("TELEGRAM", "Telegram polling conflict detected. Multiple instances or rapid reloads may be active.")
        return
    if isinstance(context.error, NetworkError):
        # Network disconnects during long polling are normal and automatically recovered
        agent_logger.warn("TELEGRAM", f"Telegram network error: {context.error}")
        return
    agent_logger.error("TELEGRAM", f"Telegram error: {context.error}", context.error)


def telegram_polling_error_callback(exc: Exception) -> None:
    """Handle low level network retry loop errors during Telegram update polling."""
    from telegram.error import Conflict, NetworkError
    if isinstance(exc, Conflict):
        # Log concise warning when multiple instances or rapid restarts poll simultaneously
        agent_logger.warn("TELEGRAM", "Polling conflict: another instance is active with this bot token. Retrying...")
        return
    if isinstance(exc, NetworkError):
        # Transient network issues during polling are automatically retried
        agent_logger.warn("TELEGRAM", f"Polling network glitch: {exc}")
        return
    agent_logger.warn("TELEGRAM", f"Polling error: {exc}")


def build_telegram_app() -> Application | None:
    """Build and configure the Telegram Bot Application."""
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        agent_logger.info("TELEGRAM", "TELEGRAM_BOT_TOKEN not set. Telegram bot disabled.")
        return None

    try:
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        # Handle all text messages
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Handle start command
        application.add_handler(MessageHandler(filters.COMMAND, handle_message))

        # Register error handler for clean conflict and network recovery
        application.add_error_handler(telegram_error_handler)

        return application
    except Exception as e:
        agent_logger.error("TELEGRAM", f"Failed to build Telegram application: {e}", e)
        return None


async def start_telegram_polling(telegram_app: Application) -> None:
    """Start Telegram update polling with clean error callback to avoid loud tracebacks."""
    await telegram_app.updater.start_polling(error_callback=telegram_polling_error_callback)


async def send_telegram_push(text: str) -> dict:
    """
    Send a push notification to the admin's Telegram chat.

    Independent of the polling-based bot handler.
    Uses the raw Telegram Bot API to initiate an outbound message.
    """
    import httpx
    from app.core.retry import retry_with_backoff

    settings = get_settings()

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_ADMIN_CHAT_ID:
        agent_logger.warn("TELEGRAM", "Push not configured (missing BOT_TOKEN or ADMIN_CHAT_ID)")
        return {"status": "skipped", "detail": "Telegram push not configured"}

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    async def _do_send() -> httpx.Response:
        async with httpx.AsyncClient(timeout=15.0) as client:
            return await client.post(url, json={
                "chat_id": settings.TELEGRAM_ADMIN_CHAT_ID,
                "text": text,
            })

    try:
        response = await retry_with_backoff(
            _do_send,
            max_retries=2,
            base_delay=2.0,
            retryable_exceptions=(TimeoutError, ConnectionError, httpx.TimeoutException),
            operation_name="Telegram:Push",
        )

        if response.status_code == 200:
            agent_logger.info("TELEGRAM", "Push notification sent successfully")
            return {"status": "sent", "detail": "Message delivered via Telegram"}

        agent_logger.warn("TELEGRAM", f"Telegram API returned HTTP {response.status_code}", {
            "response": response.text[:200]
        })
        return {"status": "failed", "detail": f"HTTP {response.status_code}"}

    except Exception as e:
        agent_logger.error("TELEGRAM", f"Failed to send push notification: {e}")
        return {"status": "error", "detail": str(e)}
