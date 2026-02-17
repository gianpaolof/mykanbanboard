import pytest
from unittest.mock import patch, Mock

pytestmark = pytest.mark.anyio


class TestTriageLabels:
    """Integration tests for /api/triage labels field."""

    async def test_labels_field_returns_clean_list(self, client, sample_ticket):
        """Should return clean list of label strings."""
        with patch('src.api.routes.TriageModule') as mock_module:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.__dict__ = {
                "priority": "high",
                "labels": ["bug", "auth"],
                "effort_estimate": "m",
                "reasoning": "Security issue"
            }
            mock_instance.forward = Mock(return_value=mock_result)
            mock_module.return_value = mock_instance

            response = client.post("/api/triage", json=sample_ticket)
            assert response.status_code == 200
            data = response.json()
            assert data["labels"] == ["bug", "auth"]
            assert all(isinstance(label, str) for label in data["labels"])

    async def test_filters_bound_methods_from_labels(self, client, sample_ticket):
        """Should filter bound method strings from labels."""
        with patch('src.api.routes.TriageModule') as mock_module:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.__dict__ = {
                "priority": "high",
                "labels": [
                    "<bound method Example.labels of Prediction(",
                    "bug",
                    "auth"
                ],
                "effort_estimate": "m",
                "reasoning": "Security issue"
            }
            mock_instance.forward = Mock(return_value=mock_result)
            mock_module.return_value = mock_instance

            response = client.post("/api/triage", json=sample_ticket)
            assert response.status_code == 200
            data = response.json()
            assert "<bound method" not in str(data["labels"])
            assert data["labels"] == ["bug", "auth"]

    async def test_filters_reasoning_fragments(self, client, sample_ticket):
        """Should filter reasoning text from labels."""
        with patch('src.api.routes.TriageModule') as mock_module:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.__dict__ = {
                "priority": "high",
                "labels": [
                    "bug",
                    "This is because authentication is broken",
                    "auth"
                ],
                "effort_estimate": "m",
                "reasoning": "Security issue"
            }
            mock_instance.forward = Mock(return_value=mock_result)
            mock_module.return_value = mock_instance

            response = client.post("/api/triage", json=sample_ticket)
            assert response.status_code == 200
            data = response.json()
            assert data["labels"] == ["bug", "auth"]

    async def test_handles_callable_labels(self, client, sample_ticket):
        """Should call bound method if labels is callable."""
        with patch('src.api.routes.TriageModule') as mock_module:
            mock_instance = Mock()
            mock_result = Mock()
            # Set labels as a callable that returns the list
            mock_result.labels = lambda: ["bug", "auth"]
            mock_result.__dict__ = {
                "priority": "high",
                "effort_estimate": "m",
                "reasoning": "Security issue"
            }
            mock_instance.forward = Mock(return_value=mock_result)
            mock_module.return_value = mock_instance

            response = client.post("/api/triage", json=sample_ticket)
            assert response.status_code == 200
            data = response.json()
            assert data["labels"] == ["bug", "auth"]

    async def test_handles_empty_labels(self, client, sample_ticket):
        """Should return empty list for None labels."""
        with patch('src.api.routes.TriageModule') as mock_module:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.__dict__ = {
                "priority": "medium",
                "labels": None,
                "effort_estimate": "m",
                "reasoning": "No labels needed"
            }
            mock_instance.forward = Mock(return_value=mock_result)
            mock_module.return_value = mock_instance

            response = client.post("/api/triage", json=sample_ticket)
            assert response.status_code == 200
            data = response.json()
            assert data["labels"] == []

    async def test_removes_duplicates_and_html(self, client, sample_ticket):
        """Should remove duplicates and filter HTML in same request."""
        with patch('src.api.routes.TriageModule') as mock_module:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.__dict__ = {
                "priority": "high",
                "labels": [
                    "bug",
                    "<script>alert('xss')</script>",
                    "bug",  # Duplicate
                    "auth",
                    "<b>urgent</b>"  # HTML
                ],
                "effort_estimate": "m",
                "reasoning": "Security issue"
            }
            mock_instance.forward = Mock(return_value=mock_result)
            mock_module.return_value = mock_instance

            response = client.post("/api/triage", json=sample_ticket)
            assert response.status_code == 200
            data = response.json()
            assert data["labels"] == ["bug", "auth"]
            assert len(data["labels"]) == 2
