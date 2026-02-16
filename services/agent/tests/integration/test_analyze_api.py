"""Integration tests for /api/agent/analyze endpoint."""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

pytestmark = pytest.mark.anyio


class TestAnalyzeEndpoint:
    """Test /api/agent/analyze endpoint."""

    async def test_analyze_with_valid_ticket(self, client, sample_ticket, mock_analyze_response):
        """POST /api/agent/analyze should return comprehensive analysis."""
        with patch('src.api.routes.DynamicMultiHopAnalyzer') as mock_analyzer:
            mock_instance = Mock()
            mock_instance.forward = Mock(return_value=mock_analyze_response)
            mock_analyzer.return_value = mock_instance

            request_data = {
                "ticket_id": sample_ticket["ticket_id"],
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

    @pytest.mark.slow
    async def test_analyze_timeout_60s(self, client, sample_ticket):
        """Analyze should timeout after 60s (per Q4 answer: fail completely)."""
        import asyncio

        with patch('src.api.routes.DynamicMultiHopAnalyzer') as mock_analyzer:
            async def slow_analyze(*args, **kwargs):
                await asyncio.sleep(65)  # Longer than 60s timeout
                return Mock()

            mock_instance = Mock()
            mock_instance.forward = Mock(side_effect=slow_analyze)
            mock_analyzer.return_value = mock_instance

            request_data = {
                "ticket_id": sample_ticket["ticket_id"],
                "title": sample_ticket["title"],
                "description": sample_ticket["description"],
            }

            response = client.post("/api/agent/analyze", json=request_data)

            # Should fail completely with 504 (not return partial results)
            assert response.status_code == 504

    async def test_analyze_partial_hop_failure(self, client, sample_ticket):
        """Partial hop failure should return 504 (per Q4 answer)."""
        with patch('src.api.routes.DynamicMultiHopAnalyzer') as mock_analyzer:
            # Simulate hop 2 failure
            mock_instance = Mock()
            mock_instance.forward = Mock(side_effect=Exception("Hop 2 failed"))
            mock_analyzer.return_value = mock_instance

            request_data = {
                "ticket_id": sample_ticket["ticket_id"],
                "title": sample_ticket["title"],
                "description": sample_ticket["description"],
            }

            response = client.post("/api/agent/analyze", json=request_data)

            # Should fail completely, not return partial results
            assert response.status_code in [500, 504]
