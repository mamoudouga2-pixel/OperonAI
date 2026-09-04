"""
Reference vector store adapter (spec 8.9, 8.10).

Ships as an in-process, dependency-free implementation so the memory
package works fully offline and in unit tests. In production this class
is swapped for a real Qdrant client behind the exact same
VectorStoreAdapter interface - callers never notice the difference.
"""

import math

from errors import VectorStoreUnavailable
from .base import VectorStoreAdapter


def _cosine(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class QdrantAdapter(VectorStoreAdapter):
    def __init__(self, embedder=None):
        self.records = {}
        self.embedder = embedder
        self._simulated_outage = False

    # --- test/ops hook, not part of the VectorStoreAdapter contract ----
    def set_outage(self, is_down):
        self._simulated_outage = is_down

    def _check_up(self):
        if self._simulated_outage:
            raise VectorStoreUnavailable("vector backend is unreachable")

    def health_check(self):
        return not self._simulated_outage

    def upsert(self, records):
        self._check_up()
        for record in records:
            self.records[record["id"]] = dict(record)
        return True

    def search(self, query, filters, limit=10):
        self._check_up()
        candidates = [
            record
            for record in self.records.values()
            if all(record.get("metadata", {}).get(k) == v for k, v in filters.items())
        ]

        if self.embedder is not None and query:
            query_vector = self.embedder.embed(query)
            candidates = sorted(
                candidates,
                key=lambda r: _cosine(query_vector, r.get("vector")),
                reverse=True,
            )

        return candidates[:limit]

    def delete(self, ids):
        self._check_up()
        for record_id in ids:
            self.records.pop(record_id, None)

    def delete_namespace(self, namespace):
        self._check_up()
        for record_id, record in list(self.records.items()):
            if record.get("metadata", {}).get("namespace") == namespace:
                self.records.pop(record_id, None)

    def snapshot(self):
        return {k: dict(v) for k, v in self.records.items()}

    def restore(self, snapshot):
        self.records = {k: dict(v) for k, v in snapshot.items()}
