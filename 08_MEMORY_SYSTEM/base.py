"""
VectorStoreAdapter contract (spec 8.9).

"Core/Boss code must never call Qdrant-specific queries directly." All
vector backends (Qdrant, a future pgvector/FAISS backend, etc.) must
implement this interface so they're interchangeable behind
``vector_storage.registry``.
"""

from abc import ABC, abstractmethod


class VectorStoreAdapter(ABC):
    @abstractmethod
    def health_check(self):
        """Return True if the backend is reachable and usable."""

    @abstractmethod
    def upsert(self, records):
        """records: list of {"id", "vector", "metadata"}."""

    @abstractmethod
    def search(self, query, filters, limit=10):
        """Return up to ``limit`` records matching ``filters``,
        ranked by relevance to ``query``."""

    @abstractmethod
    def delete(self, ids):
        """Delete records by id."""

    @abstractmethod
    def delete_namespace(self, namespace):
        """Delete every record whose metadata.namespace == namespace."""

    @abstractmethod
    def snapshot(self):
        """Return a serializable snapshot for backup."""

    @abstractmethod
    def restore(self, snapshot):
        """Restore state from a snapshot produced by ``snapshot()``."""
