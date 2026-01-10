"""ChromaDB integration for semantic search."""

import logging
from typing import Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ..config import settings

logger = logging.getLogger(__name__)


class ChromaManager:
    """Manager for ChromaDB vector store operations."""

    def __init__(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=settings.chroma_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )

            # Setup embedding function
            if settings.openai_api_key:
                self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=settings.openai_api_key,
                    model_name=settings.embedding_model,
                )
            else:
                # Fallback to default embedding function
                logger.warning(
                    "No OpenAI API key found, using default embedding function"
                )
                self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=settings.chroma_collection,
                embedding_function=self.embedding_fn,
                metadata={"description": "Kanban AI ticket embeddings"},
            )

            logger.info(f"ChromaDB initialized with {self.collection.count()} documents")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise

    def add_ticket(
        self,
        ticket_id: str,
        title: str,
        description: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Add or update a ticket in the vector store.

        Args:
            ticket_id: Unique ticket identifier
            title: Ticket title
            description: Ticket description
            metadata: Additional metadata (priority, labels, etc.)
        """
        try:
            # Combine title and description for embedding
            document = f"{title}\n\n{description}"

            # Prepare metadata
            ticket_metadata = {
                "title": title,
                "description": description,
                **(metadata or {}),
            }

            # Add to collection
            self.collection.upsert(
                ids=[ticket_id],
                documents=[document],
                metadatas=[ticket_metadata],
            )

            logger.debug(f"Added ticket {ticket_id} to vector store")

        except Exception as e:
            logger.error(f"Failed to add ticket {ticket_id}: {str(e)}")
            raise

    def remove_ticket(self, ticket_id: str) -> None:
        """Remove a ticket from the vector store.

        Args:
            ticket_id: Ticket identifier to remove
        """
        try:
            self.collection.delete(ids=[ticket_id])
            logger.debug(f"Removed ticket {ticket_id} from vector store")

        except Exception as e:
            logger.error(f"Failed to remove ticket {ticket_id}: {str(e)}")
            raise

    def search(
        self,
        query: str,
        limit: int = 10,
        filter_metadata: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Search for similar tickets.

        Args:
            query: Search query
            limit: Maximum number of results
            filter_metadata: Optional metadata filters

        Returns:
            List of search results with id, title, description, and score
        """
        try:
            # Perform similarity search
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=filter_metadata,
            )

            # Parse results
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, ticket_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0.0

                    # Convert distance to similarity score (0-1)
                    # ChromaDB returns L2 distance, convert to similarity
                    similarity = 1 / (1 + distance)

                    search_results.append({
                        "id": ticket_id,
                        "title": metadata.get("title", ""),
                        "description": metadata.get("description", ""),
                        "score": round(similarity, 3),
                        "metadata": metadata,
                    })

            logger.debug(f"Search for '{query}' returned {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise

    def get_ticket(self, ticket_id: str) -> Optional[dict[str, Any]]:
        """Get a specific ticket by ID.

        Args:
            ticket_id: Ticket identifier

        Returns:
            Ticket data or None if not found
        """
        try:
            result = self.collection.get(
                ids=[ticket_id],
                include=["metadatas", "documents"],
            )

            if result["ids"]:
                metadata = result["metadatas"][0] if result["metadatas"] else {}
                document = result["documents"][0] if result["documents"] else ""

                return {
                    "id": ticket_id,
                    "document": document,
                    "metadata": metadata,
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get ticket {ticket_id}: {str(e)}")
            raise

    def clear_all(self) -> None:
        """Clear all tickets from the collection.

        Warning: This is destructive and cannot be undone.
        """
        try:
            # Delete the collection
            self.client.delete_collection(name=settings.chroma_collection)

            # Recreate it
            self.collection = self.client.get_or_create_collection(
                name=settings.chroma_collection,
                embedding_function=self.embedding_fn,
                metadata={"description": "Kanban AI ticket embeddings"},
            )

            logger.info("Cleared all tickets from vector store")

        except Exception as e:
            logger.error(f"Failed to clear collection: {str(e)}")
            raise

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics.

        Returns:
            Statistics about the collection
        """
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": settings.chroma_collection,
                "embedding_model": settings.embedding_model,
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            raise
