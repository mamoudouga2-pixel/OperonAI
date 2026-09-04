"""
Embedding adapter (spec 8.10 EMBEDDING ARCHITECTURE).

"Embedding model is also adapter-based. Embedding version metadata must
be recorded so re-indexing after a model change is deliberate."

The default implementation is a deterministic hash-based pseudo-embedding
with no external dependencies, so long-term memory works fully offline.
Swap in a real local embedding model by implementing the same
``embed(text) -> list[float]`` interface and bumping ``version``.
"""

import hashlib


class EmbeddingAdapter:
    def __init__(self, version="local-hash-v1", dimensions=4):
        self.version = version
        self.dimensions = dimensions

    def embed(self, text):
        digest = hashlib.sha256(str(text).encode("utf-8")).hexdigest()
        chunk = 64 // self.dimensions if self.dimensions <= 8 else 8
        return [
            int(digest[i : i + chunk], 16) / 16 ** chunk
            for i in range(0, chunk * self.dimensions, chunk)
        ]


class EmbeddingVersionMismatch(RuntimeError):
    """Raised when a stored vector's embedding_version differs from the
    adapter's current version, signalling that re-indexing is needed."""
