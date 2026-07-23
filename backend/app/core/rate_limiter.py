"""
Multi-tier Rate Limiter — per-user, per-endpoint, per-resource.

Replaces the generic slowapi IP-based limiter with identity-aware
rate limiting that understands user roles and endpoint costs.

Tiers:
  1. Per-User Identity: limits based on authenticated user ID (not IP)
  2. Per-Endpoint: different limits for expensive vs cheap endpoints
  3. Per-Resource (LLM Budget): separate tracking for LLM/tool invocations
"""

from __future__ import annotations

import threading
import time

from fastapi import HTTPException, Request, status

from app.core.logger import agent_logger


class SlidingWindowCounter:
    """
    Thread-safe sliding window rate limiter.

    Tracks request counts within a rolling time window using
    a simple list of timestamps.
    """

    def __init__(self):
        self._windows: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, dict]:
        """
        Check if a request is within the rate limit.

        Args:
            key: Unique identifier (e.g., "user:123:chat")
            max_requests: Maximum requests allowed in the window
            window_seconds: Window duration in seconds

        Returns:
            (allowed, info_dict) where info_dict contains remaining, reset time, etc.
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            if key not in self._windows:
                self._windows[key] = []

            # Remove expired timestamps
            self._windows[key] = [t for t in self._windows[key] if t > cutoff]

            current_count = len(self._windows[key])

            info = {
                "limit": max_requests,
                "remaining": max(0, max_requests - current_count - 1),
                "reset": int(cutoff + window_seconds),
                "window": window_seconds,
            }

            if current_count >= max_requests:
                info["remaining"] = 0
                return False, info

            # Record this request
            self._windows[key].append(now)
            return True, info

    def get_count(self, key: str, window_seconds: int) -> int:
        """Get current request count for a key within the window."""
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            timestamps = self._windows.get(key, [])
            return sum(1 for t in timestamps if t > cutoff)

    def cleanup(self, max_age: int = 3600) -> int:
        """Remove stale entries older than max_age seconds."""
        cutoff = time.time() - max_age
        removed = 0
        with self._lock:
            keys_to_remove = []
            for key, timestamps in self._windows.items():
                self._windows[key] = [t for t in timestamps if t > cutoff]
                if not self._windows[key]:
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del self._windows[key]
                removed += 1
        return removed


# ─── Global counter instance ────────────────────────────────────
_counter = SlidingWindowCounter()


# ─── Endpoint rate limit configs ─────────────────────────────────

# Format: {endpoint_name: {role: (max_requests, window_seconds)}}
ENDPOINT_LIMITS: dict[str, dict[str, tuple[int, int]]] = {
    "chat": {
        "ADMIN": (20, 60),      # 20 req/min for owner
        "GUEST": (5, 60),       # 5 req/min for portfolio visitors
    },
    "public_chat": {
        "ADMIN": (30, 60),      # Admin testing the public endpoint
        "GUEST": (10, 60),      # 10 req/min per IP for public visitors
    },
    "chat_history": {
        "ADMIN": (60, 60),      # Read-only, cheap
        "GUEST": (20, 60),
    },
    "chat_reset": {
        "ADMIN": (10, 60),
        "GUEST": (3, 60),
    },
    "chat_message_edit": {
        "ADMIN": (30, 60),
        "GUEST": (5, 60),
    },
    "mcp_reload": {
        "ADMIN": (5, 60),       # Prevents reconnection storms
        "GUEST": (0, 60),       # Guests can't access MCP admin
    },
    "admin": {
        "ADMIN": (30, 60),
        "GUEST": (0, 60),
    },
}

# LLM budget limits (per-resource, not per-endpoint)
LLM_BUDGET_LIMITS: dict[str, tuple[int, int]] = {
    "llm_primary": (100, 3600),     # 100 calls/hour for primary LLM
    "llm_fallback": (200, 3600),    # 200 calls/hour for fallback
    "tool_execution": (50, 3600),   # 50 tool calls/hour per tool
}


def _get_user_identifier(request: Request) -> tuple[str, str]:
    """
    Extract user ID and role from the request.
    Returns (identifier, role).
    """
    # Check if auth has already set the user on the request
    user = getattr(request.state, "current_user", None)
    if user:
        return f"user:{user.id}", getattr(user, "role", "GUEST")

    # Fallback to IP for unauthenticated requests
    host = request.client.host if request.client else "unknown"
    return f"ip:{host}", "GUEST"


def rate_limit(endpoint: str):
    """
    FastAPI dependency for per-endpoint, per-user rate limiting.

    Usage:
        @router.post("/")
        async def handler(
            ...,
            _rate: None = Depends(rate_limit("chat")),
        ):
    """
    async def _check_rate_limit(request: Request) -> None:
        identifier, role = _get_user_identifier(request)
        limits = ENDPOINT_LIMITS.get(endpoint, {})
        role_limit = limits.get(role)

        if role_limit is None:
            # No explicit limit defined — use a generous default
            role_limit = (60, 60)

        max_requests, window = role_limit

        # Zero limit means access denied for this role
        if max_requests == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for your role.",
            )

        key = f"{identifier}:{endpoint}"
        allowed, info = _counter.is_allowed(key, max_requests, window)

        if not allowed:
            agent_logger.warn("RATE_LIMIT", f"Rate limit hit: {key}", info)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {info['window']}s. "
                       f"Limit: {info['limit']} requests per {info['window']}s.",
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["window"]),
                },
            )

    return _check_rate_limit


def check_llm_budget(resource: str, identifier: str = "global") -> bool:
    """
    Check if an LLM/tool invocation is within budget.

    Called from within the LangGraph nodes (not as a FastAPI dependency).
    Returns True if allowed, False if budget exhausted.
    """
    limits = LLM_BUDGET_LIMITS.get(resource)
    if not limits:
        return True  # No limit defined

    max_calls, window = limits
    key = f"budget:{identifier}:{resource}"
    allowed, info = _counter.is_allowed(key, max_calls, window)

    if not allowed:
        agent_logger.warn("RATE_LIMIT", f"LLM budget exhausted: {resource}", info)

    return allowed


def get_rate_limit_stats() -> dict:
    """Return rate limiter stats for monitoring."""
    return {
        "endpoint_limits": {
            endpoint: {role: {"max": lim[0], "window": lim[1]} for role, lim in roles.items()}
            for endpoint, roles in ENDPOINT_LIMITS.items()
        },
        "llm_budget_limits": {
            resource: {"max": lim[0], "window": lim[1]}
            for resource, lim in LLM_BUDGET_LIMITS.items()
        },
    }
