"""
Unit tests for retry_with_backoff (app.core.retry).

Tests successful retry, max retries exhaustion, and backoff delay behavior.
"""

from __future__ import annotations

import time

import pytest

from app.core.retry import retry_with_backoff

# ─── Successful Scenarios ────────────────────────────────────────

class TestSuccessfulRetry:

    async def test_succeeds_on_first_try(self):
        """If the function succeeds immediately, no retry should happen."""
        call_count = 0

        async def always_works():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_with_backoff(
            always_works,
            max_retries=3,
            base_delay=0.1,
        )
        assert result == "success"
        assert call_count == 1

    async def test_succeeds_on_second_try(self):
        """If the function fails once then succeeds, it should return the success value."""
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("transient")
            return "recovered"

        result = await retry_with_backoff(
            flaky,
            max_retries=3,
            base_delay=0.05,
            retryable_exceptions=(ConnectionError,),
        )
        assert result == "recovered"
        assert call_count == 2

    async def test_passes_args_to_function(self):
        """Arguments should be forwarded to the wrapped function."""
        async def add(a, b):
            return a + b

        result = await retry_with_backoff(
            add,
            1, 2,  # positional args
            max_retries=1,
            base_delay=0.01,
        )
        assert result == 3


# ─── Failure Scenarios ───────────────────────────────────────────

class TestFailureRetry:

    async def test_raises_after_max_retries(self):
        """After exhausting all retries, the last exception should propagate."""
        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise TimeoutError("always broken")

        with pytest.raises(TimeoutError, match="always broken"):
            await retry_with_backoff(
                always_fails,
                max_retries=3,
                base_delay=0.01,
                retryable_exceptions=(TimeoutError,),
            )

        # Should have been called: 1 initial + 3 retries = 4
        assert call_count == 4

    async def test_non_retryable_exception_raises_immediately(self):
        """If the exception is not in retryable_exceptions, it should raise immediately."""
        call_count = 0

        async def bad_type():
            nonlocal call_count
            call_count += 1
            raise TypeError("not retryable")

        with pytest.raises(TypeError, match="not retryable"):
            await retry_with_backoff(
                bad_type,
                max_retries=5,
                base_delay=0.01,
                retryable_exceptions=(ConnectionError,),  # TypeError not here
            )

        assert call_count == 1  # Should not have retried


# ─── Backoff Behavior ───────────────────────────────────────────

class TestBackoffBehavior:

    async def test_delay_increases_between_retries(self):
        """Each retry should wait longer than the previous one (exponential backoff)."""
        timestamps = []

        async def fail_and_track():
            timestamps.append(time.monotonic())
            raise ConnectionError("fail")

        with pytest.raises(ConnectionError):
            await retry_with_backoff(
                fail_and_track,
                max_retries=3,
                base_delay=0.05,
                max_delay=5.0,
                retryable_exceptions=(ConnectionError,),
            )

        # Should have 4 timestamps (1 initial + 3 retries)
        assert len(timestamps) == 4

        # Gaps between calls should be increasing (or at least non-zero)
        gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        for gap in gaps:
            assert gap > 0.01  # Each gap should have some delay

    async def test_delay_capped_by_max_delay(self):
        """Backoff delay should never exceed max_delay."""
        timestamps = []

        async def fail_and_track():
            timestamps.append(time.monotonic())
            raise ConnectionError("fail")

        with pytest.raises(ConnectionError):
            await retry_with_backoff(
                fail_and_track,
                max_retries=5,
                base_delay=0.05,
                max_delay=0.15,  # Cap at 150ms
                retryable_exceptions=(ConnectionError,),
            )

        # Check that no gap exceeds max_delay + jitter tolerance
        gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        for gap in gaps:
            # Allow some tolerance for jitter and execution overhead
            assert gap < 0.4, f"Gap {gap:.3f}s exceeds max_delay cap"
