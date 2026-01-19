"""Caching layer for expensive context operations.

Caches:
- Global context (per board, long TTL)
- Relevant tickets (per query, short TTL)
- Embeddings computations
"""

import time
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from functools import wraps
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A single cache entry with expiration."""
    value: Any
    created_at: float
    expires_at: float
    hits: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        return time.time() > self.expires_at

    def access(self) -> Any:
        """Access the entry and increment hit count."""
        self.hits += 1
        return self.value


class ContextCache:
    """LRU cache for context data with TTL support.

    Supports different TTLs for different types of data:
    - Global context: 5 minutes (board structure rarely changes)
    - Similar tickets: 1 minute (may change with new tickets)
    - Embeddings: 10 minutes (stable once computed)
    """

    # Default TTLs in seconds
    DEFAULT_TTLS = {
        "global_context": 300,      # 5 minutes
        "similar_tickets": 60,      # 1 minute
        "label_context": 120,       # 2 minutes
        "embeddings": 600,          # 10 minutes
        "board_stats": 180,         # 3 minutes
        "default": 60,              # 1 minute default
    }

    def __init__(
        self,
        max_entries: int = 1000,
        default_ttl: int = 60,
    ):
        """Initialize the cache.

        Args:
            max_entries: Maximum number of entries to store
            default_ttl: Default TTL in seconds
        """
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.is_expired:
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            return entry.access()

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        cache_type: str = "default",
    ) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (overrides type-based TTL)
            cache_type: Type of cache entry (for TTL lookup)
        """
        if ttl is None:
            ttl = self.DEFAULT_TTLS.get(cache_type, self.default_ttl)

        now = time.time()
        entry = CacheEntry(
            value=value,
            created_at=now,
            expires_at=now + ttl,
        )

        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_entries:
                self._evict_lru()

            self._cache[key] = entry

    def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was found and removed
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all entries matching a pattern.

        Args:
            pattern: Pattern to match (simple prefix matching)

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_remove = [
                k for k in self._cache.keys() if k.startswith(pattern)
            ]
            for key in keys_to_remove:
                del self._cache[key]
            return len(keys_to_remove)

    def invalidate_board(self, board_id: str) -> int:
        """Invalidate all cache entries for a board.

        Args:
            board_id: Board ID to invalidate

        Returns:
            Number of entries invalidated
        """
        return self.invalidate_pattern(f"board:{board_id}")

    def clear(self) -> None:
        """Clear the entire cache."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return

        # Find entry with oldest access (lowest hits or oldest creation)
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].hits, self._cache[k].created_at)
        )
        del self._cache[lru_key]
        self._stats["evictions"] += 1

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            now = time.time()
            expired_keys = [
                k for k, v in self._cache.items()
                if v.expires_at < now
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

            return {
                "entries": len(self._cache),
                "max_entries": self.max_entries,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "hit_rate": round(hit_rate, 3),
            }


def cached(
    cache_type: str = "default",
    ttl: Optional[int] = None,
    key_prefix: str = "",
):
    """Decorator for caching function results.

    Args:
        cache_type: Type of cache for TTL determination
        ttl: Optional explicit TTL
        key_prefix: Prefix for cache keys

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        # Each decorated function gets its own cache instance
        func_cache = ContextCache()

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = func_cache._generate_key(
                key_prefix or func.__name__,
                *args,
                **kwargs
            )

            # Try to get from cache
            result = func_cache.get(key)
            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            func_cache.set(key, result, ttl=ttl, cache_type=cache_type)

            return result

        # Attach cache to wrapper for manual control
        wrapper.cache = func_cache
        wrapper.clear_cache = func_cache.clear

        return wrapper

    return decorator


def async_cached(
    cache_type: str = "default",
    ttl: Optional[int] = None,
    key_prefix: str = "",
):
    """Decorator for caching async function results.

    Args:
        cache_type: Type of cache for TTL determination
        ttl: Optional explicit TTL
        key_prefix: Prefix for cache keys

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        func_cache = ContextCache()

        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = func_cache._generate_key(
                key_prefix or func.__name__,
                *args,
                **kwargs
            )

            result = func_cache.get(key)
            if result is not None:
                return result

            result = await func(*args, **kwargs)
            func_cache.set(key, result, ttl=ttl, cache_type=cache_type)

            return result

        wrapper.cache = func_cache
        wrapper.clear_cache = func_cache.clear

        return wrapper

    return decorator


# Global cache instance for shared use
_global_cache: Optional[ContextCache] = None


def get_global_cache() -> ContextCache:
    """Get the global cache instance (singleton)."""
    global _global_cache
    if _global_cache is None:
        _global_cache = ContextCache(max_entries=2000)
    return _global_cache
