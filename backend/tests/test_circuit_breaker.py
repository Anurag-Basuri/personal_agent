"""
Unit tests for CircuitBreaker (app.core.circuit_breaker).

Tests the three-state machine: CLOSED → OPEN → HALF_OPEN → CLOSED.
"""

from __future__ import annotations

import asyncio

import pytest

from app.core.circuit_breaker import CircuitBreaker, CircuitOpenError


@pytest.fixture
def breaker():
    """A circuit breaker with low thresholds for fast testing."""
    return CircuitBreaker(
        name="TestBreaker",
        failure_threshold=2,
        recovery_timeout=0.3,  # 300ms for fast tests
        expected_exceptions=(ValueError, RuntimeError),
    )


# ─── CLOSED State ────────────────────────────────────────────────

class TestClosedState:
    """Tests for the normal CLOSED state."""

    async def test_successful_call_passes_through(self, breaker):
        """A normal async function should be called and return its value."""

        async def success():
            return "ok"

        result = await breaker.call(success)
        assert result == "ok"

    async def test_single_failure_stays_closed(self, breaker):
        """One failure should not trip the circuit."""

        async def fail_once():
            raise ValueError("transient")

        with pytest.raises(ValueError):
            await breaker.call(fail_once)

        # Breaker should still be CLOSED (threshold is 2)
        assert breaker.state == "CLOSED"

    async def test_failure_counter_resets_on_success(self, breaker):
        """A success after a failure should reset the failure count."""

        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("first call fails")
            return "recovered"

        # First call fails
        with pytest.raises(ValueError):
            await breaker.call(flaky)
        assert breaker.state == "CLOSED"

        # Second call succeeds — counter should reset
        result = await breaker.call(flaky)
        assert result == "recovered"
        assert breaker.state == "CLOSED"


# ─── OPEN State ──────────────────────────────────────────────────

class TestOpenState:
    """Tests for the tripped OPEN state."""

    async def test_trips_open_after_threshold(self, breaker):
        """After N consecutive failures, the breaker should trip OPEN."""

        async def always_fail():
            raise ValueError("permanent failure")

        for _ in range(breaker.failure_threshold):
            with pytest.raises(ValueError):
                await breaker.call(always_fail)

        assert breaker.state == "OPEN"

    async def test_open_state_rejects_instantly(self, breaker):
        """While OPEN, calls should raise CircuitOpenError without executing the function."""

        async def always_fail():
            raise ValueError("boom")

        # Trip the breaker
        for _ in range(breaker.failure_threshold):
            with pytest.raises(ValueError):
                await breaker.call(always_fail)

        # Now it's OPEN — should reject instantly
        with pytest.raises(CircuitOpenError) as exc_info:
            await breaker.call(always_fail)

        assert "TestBreaker" in str(exc_info.value)

    async def test_unexpected_exception_does_not_count(self, breaker):
        """Exceptions NOT in expected_exceptions should still propagate but NOT count toward tripping."""

        async def type_error():
            raise TypeError("unexpected")

        with pytest.raises(TypeError):
            await breaker.call(type_error)

        # TypeError is not in expected_exceptions, so failure count should be 0
        assert breaker.state == "CLOSED"


# ─── HALF_OPEN State ────────────────────────────────────────────

class TestHalfOpenState:
    """Tests for the recovery probe HALF_OPEN state."""

    async def test_transitions_to_half_open_after_timeout(self, breaker):
        """After recovery_timeout elapses, the breaker should allow a probe call."""

        async def always_fail():
            raise ValueError("fail")

        # Trip the breaker
        for _ in range(breaker.failure_threshold):
            with pytest.raises(ValueError):
                await breaker.call(always_fail)

        assert breaker.state == "OPEN"

        # Wait for recovery timeout
        await asyncio.sleep(breaker.recovery_timeout + 0.1)

        # The next call should be attempted (HALF_OPEN probe)
        # If it succeeds, circuit closes
        async def probe_success():
            return "recovered"

        result = await breaker.call(probe_success)
        assert result == "recovered"
        assert breaker.state == "CLOSED"

    async def test_half_open_failure_reopens(self, breaker):
        """If the probe call in HALF_OPEN fails, the breaker should go back to OPEN."""

        async def always_fail():
            raise ValueError("still failing")

        # Trip the breaker
        for _ in range(breaker.failure_threshold):
            with pytest.raises(ValueError):
                await breaker.call(always_fail)

        # Wait for recovery timeout
        await asyncio.sleep(breaker.recovery_timeout + 0.1)

        # Probe fails — should re-open
        with pytest.raises(ValueError):
            await breaker.call(always_fail)

        assert breaker.state == "OPEN"
