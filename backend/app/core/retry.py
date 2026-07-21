"""
Retry with Exponential Backoff + Jitter.

Retries a failing async function with increasing delays to handle
transient errors (network glitches, temporary 503s) without
hammering the recovering service.

Delay formula: min(base_delay * 2^attempt + random_jitter, max_delay)
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Callable, Coroutine
from typing import Any

from app.core.logger import agent_logger


async def retry_with_backoff(
    func: Callable[..., Coroutine[Any, Any, Any]],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    operation_name: str = "operation",
    **kwargs: Any,
) -> Any:
    """
    Retry an async function with exponential backoff + jitter.

    Args:
        func: The async callable to retry.
        max_retries: Maximum number of retry attempts (0 = no retries, just one attempt).
        base_delay: Initial delay in seconds before the first retry.
        max_delay: Cap on the delay — never waits longer than this.
        retryable_exceptions: Only these exception types trigger a retry.
                              All others propagate immediately.
        operation_name: Human-readable name for logging.

    Returns:
        The return value of `func` on success.

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e

            if attempt == max_retries:
                agent_logger.warn(
                    "RETRY",
                    f"❌ '{operation_name}' failed after {max_retries + 1} attempts",
                    {"error": str(e)[:100]},
                )
                raise

            # Exponential backoff: base * 2^attempt, capped at max_delay
            # Jitter: random value between 0 and base_delay
            delay = min(
                base_delay * (2 ** attempt) + random.uniform(0, base_delay),
                max_delay,
            )

            agent_logger.debug(
                "RETRY",
                f"⏳ '{operation_name}' attempt {attempt + 1}/{max_retries + 1} failed — "
                f"retrying in {delay:.1f}s",
                {"error": str(e)[:80]},
            )

            await asyncio.sleep(delay)

    # Should never reach here, but satisfy type checkers
    if last_exception:
        raise last_exception
