"""
Circuit Breaker — prevents cascading failures by short-circuiting
calls to failing services.

States:
  CLOSED    → normal operation, calls pass through
  OPEN      → service is down, calls are instantly rejected
  HALF_OPEN → cooldown expired, one probe request is allowed through
"""

from __future__ import annotations

import time

from app.core.logger import agent_logger


class CircuitOpenError(Exception):
    """Raised when a call is rejected because the circuit is OPEN."""

    def __init__(self, breaker_name: str):
        self.breaker_name = breaker_name
        super().__init__(f"Circuit '{breaker_name}' is OPEN — call rejected.")


class CircuitBreaker:
    """
    Generic async circuit breaker for any callable.

    Args:
        name: Identifier for logging (e.g. "HuggingFace", "GitHub API").
        failure_threshold: Consecutive failures before tripping OPEN.
        recovery_timeout: Seconds to wait in OPEN before trying HALF_OPEN.
        expected_exceptions: Exception types that count as "failures".
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: int = 60,
        expected_exceptions: tuple[type[Exception], ...] = (Exception,),
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions

        # Internal state
        # CLOSED | OPEN | HALF_OPEN
        self._state: str = "CLOSED"
        self._failure_count: int = 0
        self._last_failure_time: float = 0.0
        self._success_count: int = 0
        self._total_rejections: int = 0

    @property
    def state(self) -> str:
        """Current state, accounting for automatic OPEN → HALF_OPEN transition."""
        if self._state == "OPEN":
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                self._state = "HALF_OPEN"
                agent_logger.info(
                    "CIRCUIT",
                    f"⚡ '{self.name}' transitioning OPEN → HALF_OPEN after {elapsed:.0f}s",
                )
        return self._state

    async def call(self, func, *args, **kwargs):
        """
        Execute `func` through the circuit breaker.

        Raises CircuitOpenError if the circuit is OPEN and cooldown
        hasn't expired yet.
        """
        # triggers auto-transition check
        current_state = self.state

        if current_state == "OPEN":
            self._total_rejections += 1
            raise CircuitOpenError(self.name)

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure(e)
            raise

    def _on_success(self) -> None:
        """Record a successful call — reset failure count."""
        if self._state == "HALF_OPEN":
            agent_logger.info(
                "CIRCUIT",
                f"✅ '{self.name}' probe succeeded — resetting to CLOSED",
            )
        self._state = "CLOSED"
        self._failure_count = 0
        self._success_count += 1

    def _on_failure(self, error: Exception) -> None:
        """Record a failed call — possibly trip to OPEN."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == "HALF_OPEN":
            # Probe failed — go back to OPEN
            self._state = "OPEN"
            agent_logger.warn(
                "CIRCUIT",
                f"❌ '{self.name}' probe FAILED — back to OPEN for {self.recovery_timeout}s",
                {"error": str(error)[:100]},
            )
        elif self._failure_count >= self.failure_threshold:
            self._state = "OPEN"
            agent_logger.warn(
                "CIRCUIT",
                f"🔴 '{self.name}' tripped OPEN after {self._failure_count} consecutive failures",
                {"error": str(error)[:100], "recovery_timeout": self.recovery_timeout},
            )

    def get_status(self) -> dict:
        """Return a status dict for health/admin endpoints."""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "total_rejections": self._total_rejections,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }
