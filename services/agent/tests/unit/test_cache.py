"""Unit tests for src/agent/cache.py – DSPyCache."""

from datetime import timedelta
from unittest.mock import patch

import pytest
import time_machine

from src.agent.cache import DSPyCache, dspy_cache


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXED_NOW = "2026-02-17 12:00:00"


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestDSPyCacheInit:
    """Tests for DSPyCache.__init__."""

    def test_default_values(self):
        cache = DSPyCache()
        assert cache.max_items == 100
        assert cache.ttl_seconds == 3600
        assert cache._memory_cache == {}
        assert cache._hits == 0
        assert cache._misses == 0

    def test_custom_values(self):
        cache = DSPyCache(max_memory_items=50, ttl_seconds=60)
        assert cache.max_items == 50
        assert cache.ttl_seconds == 60


# ---------------------------------------------------------------------------
# make_key / _make_key
# ---------------------------------------------------------------------------


class TestMakeKey:
    """Tests for key generation."""

    def test_returns_string(self):
        cache = DSPyCache()
        key = cache.make_key("triage", title="Bug", description="desc")
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hex digest

    def test_deterministic(self):
        cache = DSPyCache()
        key1 = cache.make_key("triage", title="Bug", description="desc")
        key2 = cache.make_key("triage", title="Bug", description="desc")
        assert key1 == key2

    def test_different_params_produce_different_keys(self):
        cache = DSPyCache()
        key1 = cache.make_key("triage", title="Bug A")
        key2 = cache.make_key("triage", title="Bug B")
        assert key1 != key2

    def test_different_module_names_produce_different_keys(self):
        cache = DSPyCache()
        key1 = cache.make_key("triage", title="Bug")
        key2 = cache.make_key("decompose", title="Bug")
        assert key1 != key2

    def test_kwarg_order_does_not_matter(self):
        """Keys are sorted, so kwarg order must not affect the result."""
        cache = DSPyCache()
        key1 = cache.make_key("mod", a="1", b="2")
        key2 = cache.make_key("mod", b="2", a="1")
        assert key1 == key2

    def test_public_and_private_produce_same_key(self):
        cache = DSPyCache()
        assert cache.make_key("m", x=1) == cache._make_key("m", x=1)


# ---------------------------------------------------------------------------
# set / get
# ---------------------------------------------------------------------------


class TestSetGet:
    """Tests for cache get and set operations."""

    def test_set_and_get_returns_value(self):
        cache = DSPyCache()
        cache.set("key1", {"result": 42})
        assert cache.get("key1") == {"result": 42}

    def test_get_missing_returns_none(self):
        cache = DSPyCache()
        assert cache.get("nonexistent") is None

    def test_miss_increments_misses(self):
        cache = DSPyCache()
        cache.get("missing")
        assert cache._misses == 1

    def test_hit_increments_hits(self):
        cache = DSPyCache()
        cache.set("k", "v")
        cache.get("k")
        assert cache._hits == 1
        assert cache._misses == 0

    def test_overwrite_existing_key(self):
        cache = DSPyCache()
        cache.set("k", "first")
        cache.set("k", "second")
        assert cache.get("k") == "second"

    def test_none_value_is_not_storable_as_cache_miss(self):
        """Storing None is possible but get returns None, which is indistinguishable
        from a cache miss. This test documents that behaviour."""
        cache = DSPyCache()
        cache.set("k", None)
        # get() returns None – treated as a miss because cached is None
        result = cache.get("k")
        assert result is None

    def test_get_expired_entry_returns_none(self):
        cache = DSPyCache(ttl_seconds=10)
        with time_machine.travel(FIXED_NOW) as traveller:
            cache.set("k", "value")
            traveller.shift(timedelta(seconds=11))
            result = cache.get("k")
        assert result is None

    def test_expired_entry_is_removed_from_cache(self):
        cache = DSPyCache(ttl_seconds=10)
        with time_machine.travel(FIXED_NOW) as traveller:
            cache.set("k", "value")
            traveller.shift(timedelta(seconds=11))
            cache.get("k")
        assert "k" not in cache._memory_cache

    def test_not_yet_expired_entry_is_returned(self):
        cache = DSPyCache(ttl_seconds=60)
        with time_machine.travel(FIXED_NOW) as traveller:
            cache.set("k", "alive")
            traveller.shift(timedelta(seconds=59))
            result = cache.get("k")
        assert result == "alive"

    def test_get_updates_last_accessed_time(self):
        cache = DSPyCache(ttl_seconds=3600)
        with time_machine.travel(FIXED_NOW) as traveller:
            cache.set("k", "v")
            _, _, first_accessed = cache._memory_cache["k"]
            traveller.shift(timedelta(seconds=5))
            cache.get("k")
            _, _, second_accessed = cache._memory_cache["k"]
        assert second_accessed > first_accessed


# ---------------------------------------------------------------------------
# LRU eviction
# ---------------------------------------------------------------------------


class TestLRUEviction:
    """Tests for LRU eviction when cache is at capacity."""

    def test_evicts_least_recently_accessed_when_full(self):
        cache = DSPyCache(max_memory_items=3, ttl_seconds=3600)

        with time_machine.travel(FIXED_NOW) as traveller:
            cache.set("a", 1)
            traveller.shift(timedelta(seconds=1))
            cache.set("b", 2)
            traveller.shift(timedelta(seconds=1))
            cache.set("c", 3)

            # Access "a" to make it recently used
            traveller.shift(timedelta(seconds=1))
            cache.get("a")

            # Adding "d" should evict "b" (least recently accessed)
            traveller.shift(timedelta(seconds=1))
            cache.set("d", 4)

        assert "b" not in cache._memory_cache
        assert "a" in cache._memory_cache
        assert "c" in cache._memory_cache
        assert "d" in cache._memory_cache

    def test_no_eviction_when_updating_existing_key(self):
        cache = DSPyCache(max_memory_items=2, ttl_seconds=3600)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("a", 99)  # Update existing – should NOT evict
        assert len(cache._memory_cache) == 2
        assert cache.get("a") == 99

    def test_cache_size_does_not_exceed_max_items(self):
        cache = DSPyCache(max_memory_items=5, ttl_seconds=3600)
        for i in range(10):
            cache.set(f"key_{i}", i)
        assert len(cache._memory_cache) <= 5


# ---------------------------------------------------------------------------
# get_or_compute
# ---------------------------------------------------------------------------


class TestGetOrCompute:
    """Tests for get_or_compute convenience method."""

    def test_calls_compute_fn_on_miss(self):
        cache = DSPyCache()
        compute_called = []

        def compute():
            compute_called.append(True)
            return {"result": "computed"}

        result = cache.get_or_compute("mod", compute, title="T")
        assert result == {"result": "computed"}
        assert len(compute_called) == 1

    def test_does_not_call_compute_fn_on_hit(self):
        cache = DSPyCache()
        compute_called = []

        def compute():
            compute_called.append(True)
            return {"result": "computed"}

        cache.get_or_compute("mod", compute, title="T")
        cache.get_or_compute("mod", compute, title="T")
        assert len(compute_called) == 1  # Only called once

    def test_stores_result_after_compute(self):
        cache = DSPyCache()
        cache.get_or_compute("mod", lambda: "value", x=1)
        key = cache.make_key("mod", x=1)
        assert cache.get(key) == "value"

    def test_returns_cached_value_on_second_call(self):
        cache = DSPyCache()
        first = cache.get_or_compute("mod", lambda: {"v": 1}, title="T")
        second = cache.get_or_compute("mod", lambda: {"v": 999}, title="T")
        assert second == first == {"v": 1}


# ---------------------------------------------------------------------------
# invalidate
# ---------------------------------------------------------------------------


class TestInvalidate:
    """Tests for cache invalidation."""

    def test_invalidate_all_with_empty_pattern(self):
        cache = DSPyCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        count = cache.invalidate("")
        assert count == 3
        assert cache._memory_cache == {}

    def test_invalidate_all_default_arg(self):
        cache = DSPyCache()
        cache.set("x", 1)
        count = cache.invalidate()
        assert count == 1

    def test_invalidate_with_pattern(self):
        cache = DSPyCache()
        # Manually plant keys that contain the pattern
        cache._memory_cache["abc123"] = ("v1", None, None)
        cache._memory_cache["abc456"] = ("v2", None, None)
        cache._memory_cache["xyz789"] = ("v3", None, None)
        count = cache.invalidate("abc")
        assert count == 2
        assert "xyz789" in cache._memory_cache

    def test_invalidate_returns_zero_when_no_match(self):
        cache = DSPyCache()
        cache.set("key", "val")
        count = cache.invalidate("nomatch")
        assert count == 0

    def test_invalidate_module_delegates_to_invalidate(self):
        """invalidate_module calls self.invalidate(module_name)."""
        cache = DSPyCache()
        cache._memory_cache["contains_triage_here"] = ("v", None, None)
        cache._memory_cache["other"] = ("v2", None, None)
        count = cache.invalidate_module("triage")
        assert count == 1
        assert "other" in cache._memory_cache


# ---------------------------------------------------------------------------
# stats / clear_stats
# ---------------------------------------------------------------------------


class TestStats:
    """Tests for cache statistics."""

    def test_initial_stats(self):
        cache = DSPyCache()
        s = cache.stats()
        assert s["hits"] == 0
        assert s["misses"] == 0
        assert s["hit_rate"] == 0.0
        assert s["size"] == 0
        assert s["max_size"] == 100
        assert s["ttl_seconds"] == 3600

    def test_hit_rate_calculation(self):
        cache = DSPyCache()
        cache.set("k", "v")
        cache.get("k")   # hit
        cache.get("k")   # hit
        cache.get("nope")  # miss
        s = cache.stats()
        assert s["hits"] == 2
        assert s["misses"] == 1
        assert s["hit_rate"] == round(2 / 3, 4)

    def test_size_reflects_cache_length(self):
        cache = DSPyCache()
        cache.set("a", 1)
        cache.set("b", 2)
        assert cache.stats()["size"] == 2

    def test_clear_stats_resets_counters(self):
        cache = DSPyCache()
        cache.set("k", "v")
        cache.get("k")
        cache.get("missing")
        cache.clear_stats()
        s = cache.stats()
        assert s["hits"] == 0
        assert s["misses"] == 0

    def test_hit_rate_zero_when_no_requests(self):
        cache = DSPyCache()
        assert cache.stats()["hit_rate"] == 0.0


# ---------------------------------------------------------------------------
# cleanup_expired
# ---------------------------------------------------------------------------


class TestCleanupExpired:
    """Tests for cleanup_expired."""

    def test_removes_only_expired_entries(self):
        cache = DSPyCache(ttl_seconds=10)
        with time_machine.travel(FIXED_NOW) as traveller:
            cache.set("old", "v1")
            traveller.shift(timedelta(seconds=5))
            cache.set("fresh", "v2")
            traveller.shift(timedelta(seconds=6))  # total: 11s since "old", 6s since "fresh"
            count = cache.cleanup_expired()
        assert count == 1
        assert "old" not in cache._memory_cache
        assert "fresh" in cache._memory_cache

    def test_returns_zero_when_nothing_expired(self):
        cache = DSPyCache(ttl_seconds=3600)
        cache.set("k", "v")
        count = cache.cleanup_expired()
        assert count == 0

    def test_cleanup_empty_cache(self):
        cache = DSPyCache()
        assert cache.cleanup_expired() == 0

    def test_cleanup_removes_all_when_all_expired(self):
        cache = DSPyCache(ttl_seconds=1)
        with time_machine.travel(FIXED_NOW) as traveller:
            cache.set("a", 1)
            cache.set("b", 2)
            traveller.shift(timedelta(seconds=2))
            count = cache.cleanup_expired()
        assert count == 2
        assert cache._memory_cache == {}


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------


class TestGlobalInstance:
    """Tests for the module-level dspy_cache singleton."""

    def test_global_cache_is_dspy_cache_instance(self):
        assert isinstance(dspy_cache, DSPyCache)

    def test_global_cache_has_default_settings(self):
        assert dspy_cache.max_items == 100
        assert dspy_cache.ttl_seconds == 3600
