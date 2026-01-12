"""Analytics and logging for DSPy agent calls with SQLite backend."""

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class AgentAnalytics:
    """Analytics tracker for DSPy module calls.

    Logs every agent call with:
    - Module name
    - Input/output hashes (for deduplication analysis)
    - Latency in milliseconds
    - Token usage (if available)
    - Success/failure status
    - Timestamp

    Provides aggregated statistics for monitoring and optimization.

    Usage:
        analytics = AgentAnalytics()

        # Log a call
        start = time.time()
        result = module(input)
        latency_ms = int((time.time() - start) * 1000)
        analytics.log_call(
            module_name="triage",
            input_data={"title": "...", "description": "..."},
            output_data=result,
            latency_ms=latency_ms,
            success=True
        )

        # Get stats
        stats = analytics.get_stats(period="day")
        print(f"Total calls: {stats['total_calls']}")
    """

    def __init__(self, db_path: str = "data/analytics.db"):
        """Initialize analytics with SQLite database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    module_name TEXT NOT NULL,
                    input_hash TEXT,
                    output_hash TEXT,
                    latency_ms INTEGER,
                    tokens_used INTEGER DEFAULT 0,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON agent_calls(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_module ON agent_calls(module_name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_success ON agent_calls(success)"
            )

    def _hash_data(self, data: Any) -> str:
        """Generate a hash of data for deduplication analysis.

        Args:
            data: Data to hash (dict, list, or primitive)

        Returns:
            16-character hex hash
        """
        try:
            serialized = json.dumps(data, sort_keys=True, default=str)
        except (TypeError, ValueError):
            serialized = str(data)
        return hashlib.md5(serialized.encode()).hexdigest()[:16]

    def log_call(
        self,
        module_name: str,
        input_data: dict,
        output_data: dict,
        latency_ms: int,
        tokens_used: int = 0,
        success: bool = True,
        error_message: str | None = None,
    ) -> None:
        """Log a module call.

        Args:
            module_name: Name of the DSPy module
            input_data: Input parameters
            output_data: Output result
            latency_ms: Latency in milliseconds
            tokens_used: Number of tokens used (if available)
            success: Whether the call succeeded
            error_message: Error message if failed
        """
        input_hash = self._hash_data(input_data)
        output_hash = self._hash_data(output_data)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO agent_calls
                (timestamp, module_name, input_hash, output_hash, latency_ms, tokens_used, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    module_name,
                    input_hash,
                    output_hash,
                    latency_ms,
                    tokens_used,
                    success,
                    error_message,
                ),
            )

    def _get_since_timestamp(self, period: str) -> str:
        """Get ISO timestamp for period start.

        Args:
            period: "hour", "day", or "week"

        Returns:
            ISO format timestamp
        """
        if period == "hour":
            since = datetime.now() - timedelta(hours=1)
        elif period == "week":
            since = datetime.now() - timedelta(weeks=1)
        else:  # default to day
            since = datetime.now() - timedelta(days=1)
        return since.isoformat()

    def get_stats(self, period: str = "day") -> dict:
        """Get aggregated statistics for a time period.

        Args:
            period: "hour", "day", or "week"

        Returns:
            Dict with total_calls, avg_latency_ms, success_rate, total_tokens
        """
        since = self._get_since_timestamp(period)

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    AVG(latency_ms) as avg_latency,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0) as success_rate,
                    SUM(tokens_used) as total_tokens
                FROM agent_calls
                WHERE timestamp > ?
                """,
                (since,),
            ).fetchone()

        return {
            "total_calls": row[0] or 0,
            "avg_latency_ms": round(row[1] or 0, 2),
            "success_rate": round(row[2] or 0, 2),
            "total_tokens": row[3] or 0,
        }

    def get_module_stats(self, module_name: str, period: str = "day") -> dict:
        """Get statistics for a specific module.

        Args:
            module_name: Name of the module
            period: "hour", "day", or "week"

        Returns:
            Dict with module-specific stats
        """
        since = self._get_since_timestamp(period)

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    AVG(latency_ms) as avg_latency,
                    MIN(latency_ms) as min_latency,
                    MAX(latency_ms) as max_latency,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0) as success_rate,
                    SUM(tokens_used) as total_tokens,
                    COUNT(DISTINCT input_hash) as unique_inputs
                FROM agent_calls
                WHERE timestamp > ? AND module_name = ?
                """,
                (since, module_name),
            ).fetchone()

        return {
            "module_name": module_name,
            "total_calls": row[0] or 0,
            "avg_latency_ms": round(row[1] or 0, 2),
            "min_latency_ms": row[2] or 0,
            "max_latency_ms": row[3] or 0,
            "success_rate": round(row[4] or 0, 2),
            "total_tokens": row[5] or 0,
            "unique_inputs": row[6] or 0,
        }

    def get_hourly_breakdown(self, hours: int = 24) -> list[dict]:
        """Get hourly statistics breakdown.

        Args:
            hours: Number of hours to look back

        Returns:
            List of hourly stat dicts
        """
        since = datetime.now() - timedelta(hours=hours)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    strftime('%Y-%m-%d %H:00', timestamp) as hour,
                    COUNT(*) as total,
                    AVG(latency_ms) as avg_latency,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                    SUM(tokens_used) as tokens
                FROM agent_calls
                WHERE timestamp > ?
                GROUP BY strftime('%Y-%m-%d %H', timestamp)
                ORDER BY hour DESC
                """,
                (since.isoformat(),),
            ).fetchall()

        return [
            {
                "hour": row[0],
                "total_calls": row[1],
                "avg_latency_ms": round(row[2] or 0, 2),
                "success_count": row[3],
                "total_tokens": row[4] or 0,
            }
            for row in rows
        ]

    def get_module_breakdown(self, period: str = "day") -> list[dict]:
        """Get statistics broken down by module.

        Args:
            period: "hour", "day", or "week"

        Returns:
            List of module stat dicts
        """
        since = self._get_since_timestamp(period)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    module_name,
                    COUNT(*) as total,
                    AVG(latency_ms) as avg_latency,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                    SUM(tokens_used) as tokens
                FROM agent_calls
                WHERE timestamp > ?
                GROUP BY module_name
                ORDER BY total DESC
                """,
                (since,),
            ).fetchall()

        return [
            {
                "module_name": row[0],
                "total_calls": row[1],
                "avg_latency_ms": round(row[2] or 0, 2),
                "success_rate": round(row[3] or 0, 2),
                "total_tokens": row[4] or 0,
            }
            for row in rows
        ]

    def get_recent_errors(self, limit: int = 10) -> list[dict]:
        """Get recent failed calls.

        Args:
            limit: Maximum number of errors to return

        Returns:
            List of error details
        """
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT timestamp, module_name, error_message, latency_ms
                FROM agent_calls
                WHERE success = FALSE
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "timestamp": row[0],
                "module_name": row[1],
                "error_message": row[2],
                "latency_ms": row[3],
            }
            for row in rows
        ]

    def cleanup_old_data(self, days: int = 30) -> int:
        """Remove data older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of rows deleted
        """
        cutoff = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM agent_calls WHERE timestamp < ?",
                (cutoff.isoformat(),),
            )
            return cursor.rowcount


# Global analytics instance
analytics = AgentAnalytics()
