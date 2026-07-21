"""
FastAPI application factory.

- Lifespan: init DB + LLMs on startup, cleanup on shutdown
- CORS: configured from settings
- Rate limiting: per-user, per-endpoint, per-resource
- Error handlers: ApiError, ValidationError, generic
- Request ID middleware: unique UUID per request for tracing
- Routers: /health, /chat, /admin, /admin/mcp
"""

from __future__ import annotations

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

    yield

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

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.CLIENT_URL] if settings.CLIENT_URL else ["*"],
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

    app.include_router(health_router)
    app.include_router(agent_router)
    app.include_router(admin_router)
    app.include_router(mcp_router)

    return app


app = create_app()
