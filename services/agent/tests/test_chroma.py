"""Tests for ChromaDB integration."""

import pytest
from src.db.chroma import ChromaManager


@pytest.fixture
def chroma_manager():
    """Create ChromaManager instance for testing."""
    manager = ChromaManager()
    # Clear any existing data
    manager.clear_all()
    yield manager
    # Cleanup after tests
    manager.clear_all()


class TestChromaManager:
    """Tests for ChromaManager."""

    def test_initialization(self, chroma_manager):
        """Test ChromaDB initialization."""
        assert chroma_manager.client is not None
        assert chroma_manager.collection is not None

    def test_add_ticket(self, chroma_manager):
        """Test adding a ticket to vector store."""
        chroma_manager.add_ticket(
            ticket_id="test-1",
            title="Fix login bug",
            description="Users cannot login on Safari",
            metadata={"priority": "high", "labels": ["bug", "auth"]},
        )

        # Verify ticket was added
        stats = chroma_manager.get_stats()
        assert stats["total_documents"] == 1

    def test_get_ticket(self, chroma_manager):
        """Test retrieving a specific ticket."""
        # Add ticket
        chroma_manager.add_ticket(
            ticket_id="test-2",
            title="Add dark mode",
            description="Implement dark mode theme",
        )

        # Retrieve it
        ticket = chroma_manager.get_ticket("test-2")
        assert ticket is not None
        assert ticket["id"] == "test-2"
        assert "metadata" in ticket

    def test_remove_ticket(self, chroma_manager):
        """Test removing a ticket."""
        # Add ticket
        chroma_manager.add_ticket(
            ticket_id="test-3",
            title="Update docs",
            description="Update documentation",
        )

        # Remove it
        chroma_manager.remove_ticket("test-3")

        # Verify it's gone
        ticket = chroma_manager.get_ticket("test-3")
        assert ticket is None

    @pytest.mark.skip(reason="Requires OpenAI API key for embeddings")
    def test_search_similar_tickets(self, chroma_manager):
        """Test semantic search."""
        # Add multiple tickets
        chroma_manager.add_ticket(
            ticket_id="test-4",
            title="Fix authentication bug",
            description="Login fails on Safari",
        )
        chroma_manager.add_ticket(
            ticket_id="test-5",
            title="Add OAuth support",
            description="Implement Google OAuth",
        )
        chroma_manager.add_ticket(
            ticket_id="test-6",
            title="Optimize database queries",
            description="Slow queries on users table",
        )

        # Search for auth-related tickets
        results = chroma_manager.search("authentication login issues", limit=2)

        assert len(results) <= 2
        # Should find auth-related tickets first
        assert results[0]["id"] in ["test-4", "test-5"]

    def test_update_ticket(self, chroma_manager):
        """Test updating a ticket."""
        # Add ticket
        chroma_manager.add_ticket(
            ticket_id="test-7",
            title="Original title",
            description="Original description",
        )

        # Update it
        chroma_manager.add_ticket(
            ticket_id="test-7",
            title="Updated title",
            description="Updated description",
        )

        # Verify update
        ticket = chroma_manager.get_ticket("test-7")
        assert ticket["metadata"]["title"] == "Updated title"

    def test_get_stats(self, chroma_manager):
        """Test getting collection statistics."""
        # Add some tickets
        for i in range(3):
            chroma_manager.add_ticket(
                ticket_id=f"test-{i}",
                title=f"Ticket {i}",
                description=f"Description {i}",
            )

        stats = chroma_manager.get_stats()
        assert stats["total_documents"] == 3
        assert "collection_name" in stats
        assert "embedding_model" in stats

    def test_clear_all(self, chroma_manager):
        """Test clearing all tickets."""
        # Add some tickets
        for i in range(5):
            chroma_manager.add_ticket(
                ticket_id=f"test-{i}",
                title=f"Ticket {i}",
                description=f"Description {i}",
            )

        # Clear all
        chroma_manager.clear_all()

        # Verify empty
        stats = chroma_manager.get_stats()
        assert stats["total_documents"] == 0
