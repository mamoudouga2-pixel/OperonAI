"""Long-term semantic memory: embedding, retrieval and consolidation."""

from .consolidation import Consolidator
from .embedding import EmbeddingAdapter
from .retrieval import Retriever
from .semantic_store import SemanticStore

__all__ = ["SemanticStore", "EmbeddingAdapter", "Retriever", "Consolidator"]
