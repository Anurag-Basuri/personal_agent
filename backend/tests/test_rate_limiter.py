"""
Unit tests for SlidingWindowCounter and rate_limit (app.core.rate_limiter).

Tests the sliding window counter, LLM budget checks, and cleanup behavior.
"""

from __future__ import annotations

import threading
import time

import pytest

from app.core.rate_limiter import SlidingWindowCounter, check_llm_budget


@pytest.fixture
def counter():
    """A fresh SlidingWindowCounter per test."""
    return SlidingWindowCounter()


# ─── Sliding Window Counter ─────────────────────────────────────

class TestSlidingWindowCounter:

    def test_allows_within_limit(self, counter):
        """Requests within the limit should be allowed."""
        for i in range(5):
            allowed, info = counter.is_allowed("user:1:chat", max_requests=5, window_seconds=60)
            if i < 5:
                assert allowed is True
            assert info["limit"] == 5

    def test_rejects_after_limit(self, counter):
        """Once the limit is hit, subsequent requests should be rejected."""
        for _ in range(3):
            counter.is_allowed("user:1:test", max_requests=3, window_seconds=60)

        allowed, info = counter.is_allowed("user:1:test", max_requests=3, window_seconds=60)
        assert allowed is False
        assert info["remaining"] == 0

    def test_window_resets_after_time(self, counter):
        """After the window expires, requests should be allowed again."""
        # Fill the limit
        for _ in range(2):
            counter.is_allowed("user:1:short", max_requests=2, window_seconds=0.2)

        # Should be blocked
        allowed, _ = counter.is_allowed("user:1:short", max_requests=2, window_seconds=0.2)
        assert allowed is False

        # Wait for window to expire
        time.sleep(0.3)

        # Should be allowed again
        allowed, info = counter.is_allowed("user:1:short", max_requests=2, window_seconds=0.2)
        assert allowed is True

    def test_different_keys_are_independent(self, counter):
        """Rate limits for different keys should not interfere."""
        # Fill key1 completely
        for _ in range(3):
            counter.is_allowed("user:1:chat", max_requests=3, window_seconds=60)

        # key1 should be blocked
        allowed1, _ = counter.is_allowed("user:1:chat", max_requests=3, window_seconds=60)
        assert allowed1 is False

        # key2 should still be allowed
        allowed2, _ = counter.is_allowed("user:2:chat", max_requests=3, window_seconds=60)
        assert allowed2 is True

    def test_get_count(self, counter):
        """get_count should return the number of requests in the window."""
        for _ in range(3):
            counter.is_allowed("user:1:test", max_requests=10, window_seconds=60)

        count = counter.get_count("user:1:test", window_seconds=60)
        assert count == 3

    def test_info_dict_structure(self, counter):
        """The info dict should contain limit, remaining, reset, and window keys."""
        _, info = counter.is_allowed("user:1:test", max_requests=10, window_seconds=60)
        assert "limit" in info
        assert "remaining" in info
        assert "reset" in info
        assert "window" in info
        assert info["limit"] == 10
        assert info["remaining"] == 9

    def test_cleanup_removes_stale_entries(self, counter):
        """cleanup() should remove entries older than max_age."""
        counter.is_allowed("old:key", max_requests=10, window_seconds=0.1)
        time.sleep(0.2)

        removed = counter.cleanup(max_age=0.1)
        assert removed >= 1
        assert counter.get_count("old:key", window_seconds=60) == 0


# ─── Thread Safety ───────────────────────────────────────────────

class TestCounterThreadSafety:

    def test_concurrent_requests(self, counter):
        """Multiple threads hitting the same key should not exceed the limit."""
        allowed_count = 0
        denied_count = 0
        lock = threading.Lock()

        def make_request():
            nonlocal allowed_count, denied_count
            allowed, _ = counter.is_allowed("concurrent:test", max_requests=10, window_seconds=60)
            with lock:
                if allowed:
                    allowed_count += 1
                else:
                    denied_count += 1

        threads = [threading.Thread(target=make_request) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly 10 should have been allowed, 10 denied
        assert allowed_count == 10
        assert denied_count == 10


# ─── LLM Budget ─────────────────────────────────────────────────

class TestLLMBudget:

    def test_unknown_resource_always_allowed(self):
        """If a resource has no defined budget, it should always be allowed."""
        assert check_llm_budget("nonexistent_resource") is True

    def test_budget_respects_defined_limits(self):
        """check_llm_budget should respect the limits defined in LLM_BUDGET_LIMITS."""
        # Note: this test depends on the global _counter state, so it may
        # interact with other tests. In a production codebase, you'd inject
        # the counter as a dependency.
        result = check_llm_budget("llm_primary", identifier="test_budget")
        assert result is True  # First call should always be allowed
