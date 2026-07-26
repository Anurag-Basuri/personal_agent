"""
TTL Cache — in-memory cache with time-to-live expiration.

A simple, thread-safe cache backed by a Python dictionary.
No external dependencies (Redis, Memcached) required.

Usage:
    # 5 minute default
    cache = TTLCache(default_ttl=300)
    cache.set("user:123:memories", data, ttl=600)
    # None if expired
    result = cache.get("user:123:memories")
    cache.delete("user:123:memories")
    cache.delete_pattern("user:123:*")
"""

from __future__ import annotations

import threading
import time
from typing import Any


class TTLCache:
    """
    Thread-safe in-memory cache with Time-To-Live expiration.

    Each entry stores: (value, expiry_timestamp).
    Expired entries are lazily cleaned on access and periodically
    pruned when the cache exceeds the max_size threshold.
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Args:
            default_ttl: Default time-to-live in seconds for entries.
            max_size: Maximum number of entries before triggering a prune.
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self._hits: int = 0
        self._misses: int = 0

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value by key.
        Returns the default if the key doesn't exist or has expired.
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return default

            value, expiry = entry
            if time.time() > expiry:
                # Expired lazy delete
                del self._store[key]
                self._misses += 1
                return default

            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Store a value with a TTL.

        Args:
            key: Cache key.
            value: Value to store.
            ttl: Time-to-live in seconds. Uses default_ttl if not specified.
        """
        effective_ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + effective_ttl

        with self._lock:
            self._store[key] = (value, expiry)

            # Prune if over max size
            if len(self._store) > self.max_size:
                self._prune()

    def delete(self, key: str) -> bool:
        """Delete a specific key or pattern. Returns True if keys were deleted."""
        if key.endswith("*"):
            return self.delete_pattern(key) > 0

        with self._lock:
            return self._store.pop(key, None) is not None

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a prefix pattern.

        The pattern should end with '*' — e.g., "user:123:*"
        will delete "user:123:memories", "user:123:summary", etc.
        """
        if not pattern.endswith("*"):
            return self.delete(pattern) and 1 or 0

        # Remove the trailing *
        prefix = pattern[:-1]
        count = 0
        with self._lock:
            keys_to_delete = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._store[k]
                count += 1
        return count

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._store.clear()

    def _prune(self) -> None:
        """Remove all expired entries. Called internally under lock."""
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired_keys:
            del self._store[k]

    @property
    def size(self) -> int:
        """Number of entries (may include expired ones not yet pruned)."""
        return len(self._store)

    def get_stats(self) -> dict:
        """Return cache statistics for monitoring."""
        total = self._hits + self._misses
        return {
            "size": self.size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 2) if total > 0 else 0.0,
        }


# Application wide cache singleton
app_cache = TTLCache(default_ttl=300, max_size=500)
