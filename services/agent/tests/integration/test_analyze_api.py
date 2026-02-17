"""Integration tests for /api/agent/analyze endpoint.

DynamicMultiHopAnalyzer.forward() returns a dict (not a Prediction object).
The route uses result.get(...) to extract values.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException


def _make_analyze_result(
    context_summary: str = "Found 3 similar authentication tickets.",
    key_themes: list | None = None,
    patterns: list | None = None,
    dependencies: str = "PostgreSQL database, Redis for sessions",
    insights: str = "Consider using existing OAuth library",
    recommendations: list | None = None,
    complexity: str = "high",
) -> dict:
    """Return a dict matching what DynamicMultiHopAnalyzer.forward() returns."""
    return {
        "context_summary": context_summary,
        "key_themes": key_themes if key_themes is not None else ["OAuth", "Security"],
        "patterns": patterns if patterns is not None else ["JWT is common", "2FA needed"],
        "dependencies": dependencies,
        "insights": insights,
        "recommendations": recommendations if recommendations is not None else [
            "Use Authlib for OAuth",
            "Implement JWT with refresh tokens",
        ],
        "complexity": complexity,
    }


class TestAnalyzeEndpoint:
    """Test /api/agent/analyze endpoint."""

    def test_analyze_with_valid_ticket(self, client, sample_ticket, mock_chromadb):
        """POST /api/agent/analyze should return comprehensive analysis."""
        with patch("src.api.routes.DynamicMultiHopAnalyzer") as mock_analyzer:
            mock_analyzer.return_value.return_value = _make_analyze_result()

            request_data = {
                "title": sample_ticket["title"],
                "description": sample_ticket["description"],
            }

            response = client.post("/api/agent/analyze", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Should have all analysis components
            assert "context_summary" in data
            assert "key_themes" in data
            assert "patterns" in data
            assert "insights" in data
            assert "recommendations" in data
            assert "complexity" in data

    def test_analyze_recommendations_joined_as_string(self, client, sample_ticket, mock_chromadb):
        """Recommendations list should be joined into a single string."""
        with patch("src.api.routes.DynamicMultiHopAnalyzer") as mock_analyzer:
            mock_analyzer.return_value.return_value = _make_analyze_result(
                recommendations=["Use Authlib", "Add rate limiting", "Enable 2FA"],
            )

            response = client.post(
                "/api/agent/analyze",
                json={"title": sample_ticket["title"], "description": ""},
            )

        assert response.status_code == 200
        data = response.json()
        # Route joins list with "; "
        assert isinstance(data["recommendations"], str)
        assert "Use Authlib" in data["recommendations"]

    def test_analyze_empty_recommendations(self, client, sample_ticket, mock_chromadb):
        """Empty recommendations list should yield empty string."""
        with patch("src.api.routes.DynamicMultiHopAnalyzer") as mock_analyzer:
            mock_analyzer.return_value.return_value = _make_analyze_result(
                recommendations=[],
            )

            response = client.post(
                "/api/agent/analyze",
                json={"title": sample_ticket["title"], "description": ""},
            )

        assert response.status_code == 200
        assert response.json()["recommendations"] == ""

    def test_analyze_missing_title_returns_422(self, client, mock_chromadb):
        """Missing title should return 422."""
        response = client.post(
            "/api/agent/analyze",
            json={"description": "Some description"},
        )
        assert response.status_code == 422

    def test_analyze_empty_title_returns_422(self, client, mock_chromadb):
        """Empty title should return 422 (min_length=1)."""
        response = client.post(
            "/api/agent/analyze",
            json={"title": "", "description": ""},
        )
        assert response.status_code == 422

    def test_analyze_module_exception_returns_500(self, client, sample_ticket, mock_chromadb):
        """Module exception should return 500."""
        with patch("src.api.routes.DynamicMultiHopAnalyzer") as mock_analyzer:
            mock_analyzer.return_value.side_effect = Exception("Hop 2 failed")

            response = client.post(
                "/api/agent/analyze",
                json={"title": sample_ticket["title"], "description": ""},
            )

        assert response.status_code in [500, 504]

    def test_analyze_with_board_context(self, client, sample_ticket, mock_chromadb):
        """Board context should be accepted without validation errors."""
        with patch("src.api.routes.DynamicMultiHopAnalyzer") as mock_analyzer:
            mock_analyzer.return_value.return_value = _make_analyze_result()

            response = client.post(
                "/api/agent/analyze",
                json={
                    "title": sample_ticket["title"],
                    "description": sample_ticket["description"],
                    "board_context": {
                        "board_id": "board-1",
                        "board_name": "My Board",
                        "columns": [],
                        "labels": [],
                        "total_tickets": 0,
                    },
                },
            )

        assert response.status_code == 200

    def test_analyze_response_key_themes_is_list(self, client, sample_ticket, mock_chromadb):
        """key_themes in response should be a list."""
        with patch("src.api.routes.DynamicMultiHopAnalyzer") as mock_analyzer:
            mock_analyzer.return_value.return_value = _make_analyze_result(
                key_themes=["Security", "Authentication", "Performance"],
            )

            response = client.post(
                "/api/agent/analyze",
                json={"title": sample_ticket["title"], "description": ""},
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["key_themes"], list)

    @pytest.mark.slow
    def test_analyze_timeout_60s(self, client, sample_ticket, mock_chromadb):
        """Analyze should timeout after 60s (fail completely)."""
        with patch("src.api.routes.run_sync_with_timeout") as mock_timeout:
            mock_timeout.side_effect = HTTPException(
                status_code=504,
                detail="Analyze timed out after 60 seconds. Please try again.",
            )

            response = client.post(
                "/api/agent/analyze",
                json={"title": sample_ticket["title"], "description": ""},
            )

        assert response.status_code == 504

    def test_analyze_partial_hop_failure(self, client, sample_ticket, mock_chromadb):
        """Partial hop failure should return 500 (not partial results)."""
        with patch("src.api.routes.DynamicMultiHopAnalyzer") as mock_analyzer:
            mock_analyzer.return_value.side_effect = Exception("Hop 2 failed")

            response = client.post(
                "/api/agent/analyze",
                json={"title": sample_ticket["title"], "description": ""},
            )

        assert response.status_code in [500, 504]
