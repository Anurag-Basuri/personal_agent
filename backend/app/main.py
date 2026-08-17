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
import logging
from contextlib import asynccontextmanager

# Suppress noisy third party loggers before anything else imports them
for _noisy in ("sqlalchemy.engine", "httpx", "httpcore", "watchfiles", "langgraph"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


from dotenv import load_dotenv
# Load .env into os.environ so MCP client and other OS-level tools can access them
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.config import get_settings
from app.core.exceptions import (
    ApiError,
    api_error_handler,
    generic_error_handler,
    validation_error_handler,
)
from app.database import close_db, init_db


# Background Session Cleanup
async def _public_session_cleanup_loop():
    """Periodic background task that deletes inactive public chatbot sessions.

    Runs every 24 hours. Deletes sessions with no activity for 1+ hour.
    Only targets public (unauthenticated) sessions — user sessions are never touched.
    """
    from app.core.logger import agent_logger
    from app.repositories.session_repo import session_repo
    from app.agent.public_service import get_message_counter

    while True:
        try:
            # 24 hours
            await asyncio.sleep(24 * 60 * 60)
            deleted = await session_repo.delete_inactive_public_sessions(
                max_inactivity_minutes=60,
            )
            if deleted > 0:
                agent_logger.info(
                    "CLEANUP",
                    f"🧹 Deleted {deleted} inactive public sessions",
                )

                # Also clear the in memory message counters for cleaned sessions
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
            # Retry in 1 minute on error
            await asyncio.sleep(60)


async def _rag_sync_loop():
    """Periodic background task that re ingests portfolio data into the vector store.

    Runs every N hours (configured by RAG_SYNC_INTERVAL_HOURS).
    Acts as a safety net so the agent's knowledge stays current even if
    the webhook from the portfolio CMS is not configured.
    """
    from app.core.logger import agent_logger
    from app.rag.vector_store import RAG_AVAILABLE

    if not RAG_AVAILABLE:
        # No point running if RAG isn't available
        return

    settings = get_settings()
    interval_seconds = settings.RAG_SYNC_INTERVAL_HOURS * 3600

    while True:
        try:
            await asyncio.sleep(interval_seconds)
            agent_logger.info("RAG", "🔄 Periodic RAG sync triggered")
            from app.rag.ingester import run_ingestion
            await run_ingestion()
        except asyncio.CancelledError:
            break
        except Exception as e:
            agent_logger.warn("RAG", f"Periodic RAG sync error (non-fatal): {e}")
            # Retry in 5 minutes on error
            await asyncio.sleep(300)


# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    import time as _time

    from app.core.logger import agent_logger, _Colors

    boot_start = _time.time()
    settings = get_settings()
    C = _Colors

    agent_logger.banner()

    # Database & RAG
    agent_logger.section("Database")
    await init_db()
    db_type = "PostgreSQL" if settings.is_postgres else "SQLite"
    agent_logger.status_line("Engine", db_type)
    agent_logger.status_line("Status", "Tables verified")
    
    from app.rag.vector_store import init_embeddings_eagerly
    init_embeddings_eagerly()

    # LLM Cascade
    agent_logger.section("LLM Cascade")
    from app.agent.llm import thinker, reasoner
    providers = thinker.get_provider_info() + reasoner.get_provider_info()
    for p in providers:
        agent_logger.status_line(f"Tier {p['tier']}", f"{p['provider']}/{p['model']}")
    if not providers:
        agent_logger.status_line("Status", "No LLM providers configured!", ok=False)

    # MCP Servers
    agent_logger.section("MCP Servers")
    from app.mcp.client import mcp_manager
    asyncio.create_task(mcp_manager.startup())
    agent_logger.status_line("MCP Manager", "Connecting in background")

    # Transports
    agent_logger.section("Transports")
    try:
        from app.transports.telegram import build_telegram_app
        telegram_app = build_telegram_app()
        if telegram_app:
            await telegram_app.initialize()
            await telegram_app.start()
            await telegram_app.updater.start_polling()
            agent_logger.status_line("Telegram", "Polling")
        else:
            agent_logger.status_line("Telegram", "Not configured", ok=False)
    except Exception as e:
        telegram_app = None
        agent_logger.status_line("Telegram", f"Failed: {e}", ok=False)

    # Background Tasks
    agent_logger.section("Background Tasks")
    cleanup_task = asyncio.create_task(_public_session_cleanup_loop())
    agent_logger.status_line("Session Cleanup", "every 24h")

    try:
        rag_sync_task = asyncio.create_task(_rag_sync_loop())
        interval = settings.RAG_SYNC_INTERVAL_HOURS
        display_interval = "1 week" if interval == 168 else f"{interval}h"
        agent_logger.status_line("RAG Sync", f"every {display_interval}")
    except Exception as e:
        rag_sync_task = None
        agent_logger.status_line("RAG Sync", f"Failed to start: {e}", ok=False)

    # Boot complete
    boot_ms = round((_time.time() - boot_start) * 1000)
    print(f"\n {C.DIM}{'─' * 52}{C.RESET}")
    print(f" {C.BOLD}{C.BRIGHT_GREEN}✓ Ready{C.RESET} {C.DIM}in {boot_ms}ms{C.RESET}")
    print(f" {C.DIM}  http://127.0.0.1:{settings.PORT}{C.RESET}")
    print(f" {C.DIM}{'─' * 52}{C.RESET}\n")

    yield

    # Shutdown
    print(f"\n {C.DIM}{'─' * 52}{C.RESET}")
    print(f" {C.BOLD}{C.BRIGHT_YELLOW}⏻ Shutting down...{C.RESET}")

    cleanup_task.cancel()
    if rag_sync_task:
        rag_sync_task.cancel()
    for task in [cleanup_task, rag_sync_task]:
        if not task: continue
        try:
            await task
        except asyncio.CancelledError:
            pass
    agent_logger.status_line("Background tasks", "stopped")

    # Shutdown MCP connections
    await mcp_manager.shutdown()
    agent_logger.status_line("MCP connections", "closed")

    # Shutdown
    if telegram_app:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
        agent_logger.status_line("Telegram bot", "stopped")

    await close_db()
    agent_logger.status_line("Database", "closed")
    print(f" {C.DIM}{'─' * 52}{C.RESET}\n")


# App Factory
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

    # Middleware
    # CORS allow both portfolio domain and agent domain
    allowed_origins = []
    if settings.CLIENT_URL:
        allowed_origins.append(settings.CLIENT_URL)
    if settings.PORTFOLIO_URL:
        allowed_origins.append(settings.PORTFOLIO_URL)
    if settings.PORTFOLIO_FRONTEND_URL:
        allowed_origins.append(settings.PORTFOLIO_FRONTEND_URL)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins if allowed_origins else ["*"],
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|172\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+):\d+$" if settings.DEBUG else None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After",
        ],
    )

    # Request ID middleware (first so others can use it)
    from app.middlewares.request_id import RequestIdMiddleware
    app.add_middleware(RequestIdMiddleware)
    
    # Request logging middleware
    from app.middlewares.request_logging import RequestLoggingMiddleware
    app.add_middleware(RequestLoggingMiddleware)

    # Exception Handlers
    from fastapi import HTTPException, Request
    from app.core.exceptions import _error_response, _get_request_id
    
    async def custom_http_exception_handler(request: Request, exc: HTTPException):
        return _error_response(
            status_code=exc.status_code,
            message=str(exc.detail),
            errors=[],
            request_id=_get_request_id(request)
        )

    app.add_exception_handler(HTTPException, custom_http_exception_handler)
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # Routers
    from app.api.admin import router as admin_router
    from app.api.admin_auth import router as admin_auth_router
    from app.api.admin_chat import router as admin_chat_router
    from app.api.admin_health import router as admin_health_router
    from app.api.agent import router as agent_router
    from app.api.health import router as health_router
    from app.api.mcp import router as mcp_router
    from app.api.public import router as public_router
    from app.api.reindex import router as reindex_router
    from app.api.auth import router as auth_router
    from app.api.automations import router as automations_router

    # Public portfolio chatbot (no auth)
    app.include_router(public_router)

    # User auth endpoints (register, verify)
    app.include_router(auth_router)

    # Agent endpoints (normal logged-in users, restricted tools)
    app.include_router(agent_router)

    # Admin endpoints (full access, admin auth required)
    app.include_router(admin_auth_router)
    app.include_router(admin_chat_router)
    app.include_router(admin_health_router)
    app.include_router(admin_router)
    app.include_router(mcp_router)

    # Infrastructure endpoints
    app.include_router(health_router)
    app.include_router(reindex_router)

    # Cron automation endpoint (secret protected, no JWT auth)
    app.include_router(automations_router)

    return app


app = create_app()
