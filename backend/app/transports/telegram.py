"""
Telegram Transport Layer — Phase 2: Telegram Bot Integration.

Handles receiving messages from Telegram, validating users via a whitelist,
mapping chats to unique LangGraph sessions, and sending responses back.
"""

from __future__ import annotations

import logging
from telegram import Update
from telegram.constants import ParseMode, ChatAction
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from app.config import get_settings
from app.agent.service import process_user_message
from app.core.logger import agent_logger

logger = logging.getLogger("telegram.bot")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming Telegram messages."""
    settings = get_settings()
    user = update.effective_user
    chat = update.effective_chat
    message_text = update.message.text
    
    if not user or not chat or not message_text:
        return

    # ─── Auth / Filtering ───
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
        agent_logger.warn("TELEGRAM", "No TELEGRAM_ALLOWED_USER_IDS set. Operating in PUBLIC mode!")

    # ─── Session Mapping ───
    # We use tg_chat_{chat.id} as the session_id so we get separate history per chat
    session_id = f"tg_chat_{chat.id}"
    
    # We use Telegram user ID (as string) as the system user_id to isolate memory
    user_id = f"tg_user_{user.id}"

    agent_logger.info("TELEGRAM", f"Message from {user.first_name} (ID: {user.id})", {
        "session_id": session_id,
        "message_preview": message_text[:50]
    })

    # ─── Process Message ───
    try:
        # Send typing action to Telegram while LLM processes
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        
        # Process through our LangGraph agent service
        # Telegram users act as ADMIN for now if they pass the whitelist
        response = await process_user_message(
            message=message_text,
            session_id=session_id,
            user_id=user_id
        )

        reply = response.reply

        # ─── Format & Send ───
        # Telegram MarkdownV2 requires aggressive escaping, so we use HTML or plain text.
        # Fallback to plain text if Markdown/HTML parsing fails.
        try:
            await update.message.reply_text(reply)
            # Alternatively, if we wanted to support basic Markdown, we could use ParseMode.MARKDOWN
            # but it is fragile with LLM outputs containing raw symbols.
        except Exception as e:
            agent_logger.error("TELEGRAM", "Failed to send formatted message, falling back to raw.", e)
            await update.message.reply_text(reply)
            
    except Exception as e:
        agent_logger.error("TELEGRAM", f"Error processing message: {e}", e)
        await update.message.reply_text("Sorry, I encountered an internal error while processing that.")


def build_telegram_app() -> Application | None:
    """Build and configure the Telegram Bot Application."""
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        agent_logger.info("TELEGRAM", "TELEGRAM_BOT_TOKEN not set. Telegram bot disabled.")
        return None

    try:
        # Build the application
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        
        # Add a handler for all text messages
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Also handle /start command just like normal text
        application.add_handler(MessageHandler(filters.COMMAND, handle_message))

        return application
    except Exception as e:
        agent_logger.error("TELEGRAM", f"Failed to build Telegram application: {e}", e)
        return None
