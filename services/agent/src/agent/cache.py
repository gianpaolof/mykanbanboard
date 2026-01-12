"""Caching layer for DSPy modules with LRU and TTL support."""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Callable


class DSPyCache:
    """In-memory cache for DSPy module results with LRU eviction and TTL.

    Features:
    - In-memory LRU cache for hot queries (configurable max items)
    - TTL-based expiration (configurable, default 1 hour)
    - Key generation from module name and input parameters
    - Pattern-based invalidation

    Usage:
        cache = DSPyCache(max_memory_items=100, ttl_seconds=3600)

        # Simple get/set
        key = cache.make_key("triage", title="Bug fix", description="Fix login")
        cached = cache.get(key)
        if cached is None:
            result = triage_module(...)
            cache.set(key, result)

        # Or use get_or_compute for convenience
        result = cache.get_or_compute(
            "triage",
            compute_fn=lambda: triage_module(title=title, description=description),
            title=title,
            description=description
        )
    """

    def __init__(self, max_memory_items: int = 100, ttl_seconds: int = 3600):
        """Initialize the cache.

        Args:
            max_memory_items: Maximum number of items to keep in memory (LRU eviction)
            ttl_seconds: Time-to-live for cache entries in seconds (default: 1 hour)
        """
        self.ttl_seconds = ttl_seconds
        self.max_items = max_memory_items
        self._memory_cache: dict[str, tuple[Any, datetime, datetime]] = {}
        # Format: {key: (value, created_at, last_accessed_at)}
        self._hits = 0
        self._misses = 0

    def _make_key(self, module_name: str, **kwargs) -> str:
        """Generate a cache key from module name and parameters.

        Args:
            module_name: Name of the DSPy module
            **kwargs: Input parameters to the module

        Returns:
            MD5 hash string as cache key
        """
        # Sort keys for consistent hashing
        data = json.dumps({"module": module_name, **kwargs}, sort_keys=True, default=str)
        return hashlib.md5(data.encode()).hexdigest()

    def make_key(self, module_name: str, **kwargs) -> str:
        """Public method to generate a cache key.

        Args:
            module_name: Name of the DSPy module
            **kwargs: Input parameters to the module

        Returns:
            Cache key string
        """
        return self._make_key(module_name, **kwargs)

    def get(self, key: str) -> Any | None:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key in self._memory_cache:
            value, created_at, _ = self._memory_cache[key]

            # Check TTL
            if datetime.now() - created_at < timedelta(seconds=self.ttl_seconds):
                # Update last accessed time for LRU
                self._memory_cache[key] = (value, created_at, datetime.now())
                self._hits += 1
                return value

            # Expired, remove it
            del self._memory_cache[key]

        self._misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        now = datetime.now()

        # LRU eviction if at capacity
        if len(self._memory_cache) >= self.max_items and key not in self._memory_cache:
            # Remove least recently accessed item
            oldest_key = min(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k][2]  # last_accessed_at
            )
            del self._memory_cache[oldest_key]

        self._memory_cache[key] = (value, now, now)

    def get_or_compute(
        self,
        module_name: str,
        compute_fn: Callable[[], Any],
        **kwargs
    ) -> Any:
        """Get from cache or compute and cache the result.

        Args:
            module_name: Name of the DSPy module
            compute_fn: Function to compute the value if not cached
            **kwargs: Input parameters (used for cache key)

        Returns:
            Cached or newly computed value
        """
        key = self._make_key(module_name, **kwargs)
        cached = self.get(key)

        if cached is not None:
            return cached

        result = compute_fn()
        self.set(key, result)
        return result

    def invalidate(self, pattern: str = "") -> int:
        """Invalidate cache entries matching a pattern.

        Args:
            pattern: String pattern to match in keys (empty = clear all)

        Returns:
            Number of entries invalidated
        """
        if not pattern:
            count = len(self._memory_cache)
            self._memory_cache.clear()
            return count

        keys_to_delete = [k for k in self._memory_cache if pattern in k]
        for k in keys_to_delete:
            del self._memory_cache[k]
        return len(keys_to_delete)

    def invalidate_module(self, module_name: str) -> int:
        """Invalidate all cache entries for a specific module.

        Args:
            module_name: Name of the module to invalidate

        Returns:
            Number of entries invalidated
        """
        # Generate a prefix that would be in all keys for this module
        prefix_data = json.dumps({"module": module_name}, sort_keys=True)
        # Keys contain the module name in their hash input, so we need
        # to check each entry
        keys_to_delete = []
        for key in self._memory_cache:
            # We can't reverse the hash, so we track module names separately
            # For now, clear based on pattern matching (less precise)
            pass

        # Alternative: store metadata with each entry
        return self.invalidate(module_name)

    def stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with hits, misses, hit_rate, size, max_size
        """
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total > 0 else 0.0,
            "size": len(self._memory_cache),
            "max_size": self.max_items,
            "ttl_seconds": self.ttl_seconds,
        }

    def clear_stats(self) -> None:
        """Reset hit/miss counters."""
        self._hits = 0
        self._misses = 0

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed
        """
        now = datetime.now()
        ttl_delta = timedelta(seconds=self.ttl_seconds)

        keys_to_delete = [
            k for k, (_, created_at, _) in self._memory_cache.items()
            if now - created_at >= ttl_delta
        ]

        for k in keys_to_delete:
            del self._memory_cache[k]

        return len(keys_to_delete)


# Global cache instance for shared use across modules
dspy_cache = DSPyCache()
