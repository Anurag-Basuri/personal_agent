"""
FastAPI application factory.

- Lifespan: init DB + LLMs on startup, cleanup on shutdown
- CORS: configured from settings
- Rate limiting: via slowapi
- Error handlers: ApiError, ValidationError, generic
- Request ID middleware: unique UUID per request for tracing
- Routers: /health, /chat, /admin
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.core.exceptions import (
    ApiError,
    api_error_handler,
    generic_error_handler,
    validation_error_handler,
)
from app.database import close_db, init_db


# ─── Rate Limiter ────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)


# ─── Lifespan ────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    settings = get_settings()
    print(f"[server] Starting Personal Agent API (port={settings.PORT})")

    # Init DB tables
    await init_db()
    print("[server] Database initialized")

    # Warm up LLM factory (imports trigger init)
    from app.core.llm_factory import llm_info  # noqa: F401
    print(f"[server] LLM mode: {llm_info.mode}")

    yield

    # Shutdown
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

    # ─── State ────────────────────────────────────────────────
    app.state.limiter = limiter

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
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # ─── Exception Handlers ──────────────────────────────────
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # ─── Routers ─────────────────────────────────────────────
    from app.api.health import router as health_router
    from app.api.agent import router as agent_router
    from app.api.admin import router as admin_router

    app.include_router(health_router)
    app.include_router(agent_router)
    app.include_router(admin_router)

    return app


app = create_app()
