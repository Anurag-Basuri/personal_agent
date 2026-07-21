"""
Unit tests for TTLCache (app.core.cache).

Tests set/get, TTL expiration, pattern-based deletion, and thread safety.
"""

from __future__ import annotations

import threading
import time

import pytest

from app.core.cache import TTLCache


@pytest.fixture
def cache():
    """A fresh TTLCache instance per test."""
    return TTLCache(default_ttl=1)  # 1 second default for fast tests


# ─── Basic Operations ────────────────────────────────────────────

class TestBasicOperations:

    def test_set_and_get(self, cache):
        """Store a value and retrieve it."""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key_returns_none(self, cache):
        """Getting a non-existent key should return None."""
        assert cache.get("nonexistent") is None

    def test_get_missing_key_returns_default(self, cache):
        """Getting a non-existent key with a default should return the default."""
        assert cache.get("nonexistent", default="fallback") == "fallback"

    def test_overwrite_value(self, cache):
        """Setting the same key twice should overwrite."""
        cache.set("key1", "old")
        cache.set("key1", "new")
        assert cache.get("key1") == "new"

    def test_stores_various_types(self, cache):
        """Cache should store lists, dicts, None, and other types."""
        cache.set("list", [1, 2, 3])
        cache.set("dict", {"a": 1})
        cache.set("none", None)
        cache.set("num", 42)

        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"a": 1}
        assert cache.get("none") is None  # This is tricky — None is both stored and "missing"
        assert cache.get("num") == 42


# ─── TTL Expiration ──────────────────────────────────────────────

class TestTTLExpiration:

    def test_value_expires_after_ttl(self, cache):
        """A value should become inaccessible after its TTL expires."""
        cache.set("short", "data", ttl=0.2)  # 200ms
        assert cache.get("short") == "data"

        time.sleep(0.3)  # Wait past TTL
        assert cache.get("short") is None

    def test_custom_ttl_overrides_default(self, cache):
        """Per-key TTL should override the cache's default TTL."""
        cache.set("long", "data", ttl=5)
        cache.set("short", "data", ttl=0.2)

        time.sleep(0.3)
        assert cache.get("short") is None
        assert cache.get("long") == "data"


# ─── Deletion ────────────────────────────────────────────────────

class TestDeletion:

    def test_delete_single_key(self, cache):
        """Delete should remove a specific key."""
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_delete_nonexistent_key_is_safe(self, cache):
        """Deleting a key that doesn't exist should not raise."""
        cache.delete("nonexistent")  # Should not throw

    def test_pattern_delete_with_wildcard(self, cache):
        """delete('prefix:*') should remove all keys matching the prefix."""
        cache.set("user:1:name", "Alice")
        cache.set("user:1:email", "alice@example.com")
        cache.set("user:2:name", "Bob")
        cache.set("other:key", "safe")

        cache.delete("user:1:*")

        assert cache.get("user:1:name") is None
        assert cache.get("user:1:email") is None
        assert cache.get("user:2:name") == "Bob"  # Not matching the pattern
        assert cache.get("other:key") == "safe"

    def test_clear_all(self, cache):
        """clear() should remove everything."""
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None


# ─── Thread Safety ───────────────────────────────────────────────

class TestThreadSafety:

    def test_concurrent_writes(self, cache):
        """Multiple threads writing simultaneously should not corrupt the cache."""
        errors = []

        def writer(thread_id):
            try:
                for i in range(100):
                    cache.set(f"t{thread_id}:k{i}", f"v{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # Spot-check that values are correct
        assert cache.get("t0:k0") == "v0"
        assert cache.get("t4:k99") == "v99"

    def test_concurrent_read_write(self, cache):
        """Reads and writes happening concurrently should not raise."""
        cache.set("shared", "initial")
        errors = []

        def writer():
            try:
                for i in range(200):
                    cache.set("shared", f"write-{i}")
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for _ in range(200):
                    cache.get("shared")  # Should never raise
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
