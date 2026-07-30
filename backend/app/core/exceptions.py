"""
Industry-grade exception hierarchy and FastAPI exception handlers.

All API errors extend ApiError and carry:
  - status_code: HTTP status
  - message: user-facing message
  - errors: optional list of detail strings (e.g. field validation)
  - request_id: injected by handler for tracing
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# Exception Classes
class ApiError(Exception):
    """Base exception for all API errors."""

    def __init__(
        self,
        status_code: int = 500,
        message: str = "Internal server error",
        errors: list[str] | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.errors = errors or []


class BadRequestError(ApiError):
    """400   Malformed request or validation failure."""

    def __init__(self, message: str = "Bad request", errors: list[str] | None = None):
        super().__init__(400, message, errors)


class NotFoundError(ApiError):
    """404   Resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(404, message)


class RateLimitError(ApiError):
    """429   Too many requests."""

    def __init__(self, message: str = "Too many requests. Please try again later."):
        super().__init__(429, message)


class ServiceUnavailableError(ApiError):
    """503   Upstream service down."""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(503, message)


class AgentError(ApiError):
    """500   Agent specific processing failure."""

    def __init__(self, message: str = "Agent failed to process request", errors: list[str] | None = None):
        super().__init__(500, message, errors)


class ConflictError(ApiError):
    """409 - Conflict."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(409, message)


class AuthenticationError(ApiError):
    """401 - Unauthorized."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(401, message)


class ForbiddenError(ApiError):
    """403 - Forbidden."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(403, message)


class ExternalServiceError(ApiError):
    """502 - Bad Gateway."""

    def __init__(self, message: str = "External service error"):
        super().__init__(502, message)


def classify_and_raise(error: Exception) -> None:
    """Classify common errors (like rate limits/timeouts) and raise the correct ApiError."""
    from app.core.logger import agent_logger
    error_msg = str(error)

    is_rate_limit = "Quota" in error_msg or "429" in error_msg
    is_timeout = "timeout" in error_msg.lower() or "TimeoutError" in error_msg

    if is_rate_limit:
        raise RateLimitError("I'm currently experiencing high demand. Please try again in a few moments!")
    elif is_timeout:
        raise ServiceUnavailableError("The request timed out. Please try again.")

    raise AgentError(message=error_msg or "Failed to process request")


# Response Builder
def _error_response(status_code: int, message: str, errors: list[str], request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "errors": errors,
            "request_id": request_id,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


# FastAPI Exception Handlers
def _get_request_id(request: Request) -> str:
    """Get or create a request ID for tracing."""
    return getattr(request.state, "request_id", str(uuid.uuid4()))


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    """Handle all ApiError subclasses."""
    return _error_response(
        status_code=exc.status_code,
        message=exc.message,
        errors=exc.errors,
        request_id=_get_request_id(request),
    )


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors (malformed request bodies)."""
    errors = [f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors()]
    return _error_response(
        status_code=422,
        message="Validation error",
        errors=errors,
        request_id=_get_request_id(request),
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions."""
    from app.core.logger import agent_logger
    from app.config import get_settings

    settings = get_settings()
    request_id = _get_request_id(request)

    # Log the full exception traceback server-side
    agent_logger.error("SYSTEM", f"Unhandled Exception in {request.url.path}", exc, {"request_id": request_id})

    # Classify known errors
    exc_type = type(exc).__name__

    if exc_type == "IntegrityError":
        return _error_response(409, "Resource conflict", [], request_id)
    if exc_type in ("OperationalError", "InterfaceError", "DatabaseError"):
        return _error_response(503, "Database is temporarily unavailable", [], request_id)
    if exc_type in ("ConnectTimeout", "ReadTimeout", "TimeoutError"):
        return _error_response(504, "Upstream service timeout", [], request_id)
    if exc_type == "CircuitOpenError":
        return _error_response(503, "Service temporarily unavailable due to high failure rate", [], request_id)

    # For pure 500s, sanitize the message unless in debug mode
    message = "Unexpected server error"
    if settings.is_debug:
        message = f"{exc_type}: {str(exc)}"

    return _error_response(
        status_code=500,
        message=message,
        errors=[],
        request_id=request_id,
    )

