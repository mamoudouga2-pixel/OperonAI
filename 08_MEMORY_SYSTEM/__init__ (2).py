"""Pluggable vector storage for long-term semantic memory."""

from .base import VectorStoreAdapter
from .qdrant_adapter import QdrantAdapter
from .registry import VectorRegistry

__all__ = ["VectorStoreAdapter", "QdrantAdapter", "VectorRegistry"]
