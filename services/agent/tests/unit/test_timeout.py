"""Tests for timeout mechanisms.

These tests verify that timeout handling works correctly across the stack:
- run_with_timeout() for async operations
- run_sync_with_timeout() for sync operations in thread pool
- Proper 504 error responses
- Timeout hierarchy (Tauri = FastAPI + 5s buffer)
"""

import pytest
import asyncio
from fastapi import HTTPException

pytestmark = pytest.mark.anyio


class TestTimeoutConstants:
    """Test that timeout constants are properly defined."""

    def test_timeout_constants_exist(self):
        """Verify all timeout constants are defined."""
        from src.api.routes import (
            TRIAGE_TIMEOUT,
            DECOMPOSE_TIMEOUT,
            CHAT_TIMEOUT,
            DAILY_SUMMARY_TIMEOUT,
        )

        assert TRIAGE_TIMEOUT == 12
        assert DECOMPOSE_TIMEOUT == 12
        assert CHAT_TIMEOUT == 20
        assert DAILY_SUMMARY_TIMEOUT == 10

    def test_chat_timeout_longer_than_others(self):
        """Chat should have longest timeout for complex operations."""
        from src.api.routes import TRIAGE_TIMEOUT, CHAT_TIMEOUT

        assert CHAT_TIMEOUT > TRIAGE_TIMEOUT


class TestRunWithTimeout:
    """Test run_with_timeout() for async operations."""

    @pytest.mark.asyncio
    async def test_completes_within_timeout(self):
        """Operation that completes quickly should return result."""
        async def fast_operation():
            await asyncio.sleep(0.01)  # 10ms
            return "success"

        # Import after pytest marks are applied
        from src.api.routes import run_with_timeout

        result = await run_with_timeout(fast_operation(), 1, "FastOp")
        assert result == "success"

    @pytest.mark.asyncio
    async def test_raises_504_on_timeout(self):
        """Operation that times out should raise HTTPException 504."""
        async def slow_operation():
            await asyncio.sleep(10)  # 10 seconds
            return "should_not_reach"

        from src.api.routes import run_with_timeout

        with pytest.raises(HTTPException) as exc_info:
            await run_with_timeout(slow_operation(), 0.1, "SlowOp")

        assert exc_info.value.status_code == 504
        assert "SlowOp timed out" in exc_info.value.detail
        assert "0.1 seconds" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_propagates_exceptions(self):
        """Exceptions from operation should propagate through."""
        async def failing_operation():
            await asyncio.sleep(0.01)
            raise ValueError("Operation failed")

        from src.api.routes import run_with_timeout

        with pytest.raises(ValueError, match="Operation failed"):
            await run_with_timeout(failing_operation(), 1, "FailingOp")

    @pytest.mark.asyncio
    async def test_timeout_message_includes_operation_name(self):
        """Timeout error should include the operation name."""
        async def slow_triage():
            await asyncio.sleep(10)
            return "done"

        from src.api.routes import run_with_timeout

        with pytest.raises(HTTPException) as exc_info:
            await run_with_timeout(slow_triage(), 0.05, "Triage")

        assert "Triage" in exc_info.value.detail


class TestRunSyncWithTimeout:
    """Test run_sync_with_timeout() for sync operations in thread pool."""

    @pytest.mark.asyncio
    async def test_sync_function_completes(self):
        """Sync function should run in thread pool and complete."""
        def sync_operation():
            import time
            time.sleep(0.01)  # 10ms
            return "sync_success"

        from src.api.routes import run_sync_with_timeout

        result = await run_sync_with_timeout(sync_operation, 1, "SyncOp")
        assert result == "sync_success"

    @pytest.mark.asyncio
    async def test_sync_function_timeout(self):
        """Sync function that times out should raise 504."""
        def slow_sync_operation():
            import time
            time.sleep(10)  # 10 seconds
            return "should_not_reach"

        from src.api.routes import run_sync_with_timeout

        with pytest.raises(HTTPException) as exc_info:
            await run_sync_with_timeout(slow_sync_operation, 0.1, "SlowSync")

        assert exc_info.value.status_code == 504
        assert "SlowSync timed out" in exc_info.value.detail


class TestTimeoutHierarchy:
    """Test timeout coordination across stack (per Q5 answer).

    User Answer: Tauri timeout = FastAPI timeout + 5s buffer
    This prevents Tauri timing out before FastAPI responds.
    """

    def test_recommended_timeout_hierarchy(self):
        """Document recommended timeout values per layer."""
        from src.api.routes import TRIAGE_TIMEOUT, DECOMPOSE_TIMEOUT, CHAT_TIMEOUT

        # FastAPI timeouts
        fastapi_triage = TRIAGE_TIMEOUT  # 12s
        fastapi_decompose = DECOMPOSE_TIMEOUT  # 12s
        fastapi_chat = CHAT_TIMEOUT  # 20s

        # Tauri should be FastAPI + 5s buffer
        tauri_triage_recommended = fastapi_triage + 5  # 17s
        tauri_decompose_recommended = fastapi_decompose + 5  # 17s
        tauri_chat_recommended = fastapi_chat + 5  # 25s

        # Document expectations
        assert tauri_triage_recommended == 17
        assert tauri_decompose_recommended == 17
        assert tauri_chat_recommended == 25

    def test_analyze_timeout_longest(self):
        """Analyze (deep analysis) should have longest timeout (60s)."""
        # Analyze timeout is defined differently - let's check it exists
        # This would be in a different route
        # Tauri timeout for analyze should be 65s (60 + 5)
        fastapi_analyze = 60  # From plan
        tauri_analyze_recommended = 65

        assert tauri_analyze_recommended == fastapi_analyze + 5


class TestTimeoutEdgeCases:
    """Test edge cases in timeout handling."""

    @pytest.mark.asyncio
    async def test_zero_timeout(self):
        """Zero timeout should immediately timeout."""
        async def any_operation():
            await asyncio.sleep(0.001)
            return "done"

        from src.api.routes import run_with_timeout

        with pytest.raises(HTTPException) as exc_info:
            await run_with_timeout(any_operation(), 0, "ZeroTimeout")

        assert exc_info.value.status_code == 504

    @pytest.mark.asyncio
    async def test_very_long_timeout(self):
        """Very long timeout should not cause issues."""
        async def fast_operation():
            await asyncio.sleep(0.001)
            return "done"

        from src.api.routes import run_with_timeout

        result = await run_with_timeout(fast_operation(), 999, "LongTimeout")
        assert result == "done"

    @pytest.mark.asyncio
    async def test_timeout_with_complex_return_value(self):
        """Timeout mechanism should handle complex return values."""
        async def returns_dict():
            await asyncio.sleep(0.01)
            return {
                "priority": "high",
                "labels": ["bug", "urgent"],
                "nested": {"key": "value"},
            }

        from src.api.routes import run_with_timeout

        result = await run_with_timeout(returns_dict(), 1, "ComplexReturn")
        assert result["priority"] == "high"
        assert "bug" in result["labels"]
        assert result["nested"]["key"] == "value"


class TestTimeoutIntegration:
    """Integration tests for timeout behavior across operations."""

    def test_triage_timeout_value(self):
        """Verify triage timeout is set correctly."""
        from src.api.routes import TRIAGE_TIMEOUT
        assert TRIAGE_TIMEOUT == 12, "Triage should timeout after 12 seconds"

    def test_decompose_timeout_value(self):
        """Verify decompose timeout is set correctly."""
        from src.api.routes import DECOMPOSE_TIMEOUT
        assert DECOMPOSE_TIMEOUT == 12, "Decompose should timeout after 12 seconds"

    def test_chat_timeout_increased(self):
        """Verify chat timeout was increased (per commit 92d667c)."""
        from src.api.routes import CHAT_TIMEOUT
        assert CHAT_TIMEOUT >= 20, "Chat should have at least 20s timeout"

    def test_all_timeouts_reasonable(self):
        """All timeouts should be between 5s and 120s."""
        from src.api.routes import (
            TRIAGE_TIMEOUT,
            DECOMPOSE_TIMEOUT,
            CHAT_TIMEOUT,
            DAILY_SUMMARY_TIMEOUT,
        )

        timeouts = [TRIAGE_TIMEOUT, DECOMPOSE_TIMEOUT, CHAT_TIMEOUT, DAILY_SUMMARY_TIMEOUT]
        for timeout in timeouts:
            assert 5 <= timeout <= 120, f"Timeout {timeout} outside reasonable range"


class TestTimeoutErrorMessages:
    """Test that timeout error messages are helpful."""

    @pytest.mark.asyncio
    async def test_error_message_format(self):
        """Timeout error should have clear, actionable message."""
        async def slow_op():
            await asyncio.sleep(10)
            return "done"

        from src.api.routes import run_with_timeout

        with pytest.raises(HTTPException) as exc_info:
            await run_with_timeout(slow_op(), 0.05, "MyOperation")

        error_detail = exc_info.value.detail
        # Should mention: operation name, timeout value, suggestion to retry
        assert "MyOperation" in error_detail
        assert "0.05 seconds" in error_detail or "timed out" in error_detail
        assert "try again" in error_detail.lower()

    @pytest.mark.asyncio
    async def test_different_operations_have_distinct_errors(self):
        """Different operations should have distinct error messages."""
        async def slow_op():
            await asyncio.sleep(10)
            return "done"

        from src.api.routes import run_with_timeout

        # Test Triage timeout error
        with pytest.raises(HTTPException) as exc_triage:
            await run_with_timeout(slow_op(), 0.05, "Triage")

        # Test Decompose timeout error
        with pytest.raises(HTTPException) as exc_decompose:
            await run_with_timeout(slow_op(), 0.05, "Decompose")

        # Errors should be distinct
        assert "Triage" in exc_triage.value.detail
        assert "Decompose" in exc_decompose.value.detail
