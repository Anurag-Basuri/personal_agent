"""
FastAPI application factory.

- Lifespan: init DB + LLMs on startup, cleanup on shutdown
- CORS: configured for portfolio (public) and agent (authenticated) domains
- Rate limiting: per-user, per-endpoint, per-resource
- Error handlers: ApiError, ValidationError, generic
- Request ID middleware: unique UUID per request for tracing
- Background tasks: periodic public session cleanup
- Routers: /api/public, /health, /chat, /admin, /admin/mcp
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.config import get_settings
from app.core.exceptions import (
    ApiError,
    api_error_handler,
    generic_error_handler,
    validation_error_handler,
)
from app.database import close_db, init_db


# ─── Background Session Cleanup ─────────────────────────────────

async def _public_session_cleanup_loop():
    """Periodic background task that deletes inactive public chatbot sessions.

    Runs every 30 minutes. Deletes sessions with no activity for 1+ hour.
    Only targets public (unauthenticated) sessions — user sessions are never touched.
    """
    from app.core.logger import agent_logger
    from app.repositories.session_repo import session_repo
    from app.agent.public_service import get_message_counter

    while True:
        try:
            await asyncio.sleep(30 * 60)  # 30 minutes
            deleted = await session_repo.delete_inactive_public_sessions(
                max_inactivity_minutes=60,
            )
            if deleted > 0:
                agent_logger.info(
                    "CLEANUP",
                    f"🧹 Deleted {deleted} inactive public sessions",
                )

                # Also clear the in-memory message counters for cleaned sessions
                # (The counter keys will naturally expire, but this is more immediate)
                counter = get_message_counter()
                # Note: we can't know exactly which session_ids were deleted here,
                # but the counter's stale entries are harmless and will be
                # overwritten on new sessions.
        except asyncio.CancelledError:
            break
        except Exception as e:
            from app.core.logger import agent_logger
            agent_logger.warn("CLEANUP", f"Session cleanup error (non-fatal): {e}")
            await asyncio.sleep(60)  # Retry in 1 minute on error


# ─── Lifespan ────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    settings = get_settings()
    print(f"[server] Starting Personal Agent API (port={settings.PORT})")

    # Init DB tables
    await init_db()
    print("[server] Database initialized")

    # Eagerly initialize LLMs so startup logs are accurate
    from app.agent.llm import init_llms_eagerly, get_provider_info
    init_llms_eagerly()
    providers = get_provider_info()
    print(f"[server] LLM cascade: {len(providers)} tiers configured")

    # Initialize MCP Client
    from app.mcp.client import mcp_manager
    await mcp_manager.startup()
    print(f"[server] MCP: {mcp_manager.connected_count} servers connected, {len(mcp_manager.get_tools())} tools discovered")

    # Initialize Telegram Bot
    from app.transports.telegram import build_telegram_app
    telegram_app = build_telegram_app()
    if telegram_app:
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        print("[server] Telegram bot started and polling")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(_public_session_cleanup_loop())
    print("[server] Public session cleanup task started (every 30 min)")

    yield

    # Cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    print("[server] Session cleanup task stopped")

    # Shutdown MCP connections
    await mcp_manager.shutdown()
    print("[server] MCP connections closed")

    # Shutdown
    if telegram_app:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
        print("[server] Telegram bot stopped")

    await close_db()
    print("[server] Database connection closed")


# ─── App Factory ──────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Personal Agent API",
        description="AI-powered personal agent with tool calling, RAG, and multi-transport support.",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ─── Middleware ───────────────────────────────────────────

    # CORS — allow both portfolio domain and agent domain
    allowed_origins = []
    if settings.CLIENT_URL:
        allowed_origins.append(settings.CLIENT_URL)
    if settings.PORTFOLIO_URL:
        allowed_origins.append(settings.PORTFOLIO_URL)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins if allowed_origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID middleware
    from app.middlewares.request_id import RequestIdMiddleware
    app.add_middleware(RequestIdMiddleware)

    # ─── Exception Handlers ──────────────────────────────────
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # ─── Routers ─────────────────────────────────────────────
    from app.api.admin import router as admin_router
    from app.api.agent import router as agent_router
    from app.api.health import router as health_router
    from app.api.mcp import router as mcp_router
    from app.api.public import router as public_router

    # Public portfolio chatbot (no auth)
    app.include_router(public_router)

    # Authenticated endpoints
    app.include_router(health_router)
    app.include_router(agent_router)
    app.include_router(admin_router)
    app.include_router(mcp_router)

    return app


app = create_app()
