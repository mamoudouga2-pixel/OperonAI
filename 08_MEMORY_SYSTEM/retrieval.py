"""
Scoped retrieval with freshness/quality filtering (spec 8.16).

    query -> permission/scope filter -> metadata filter
          -> similarity retrieval -> freshness/quality check
          -> return limited context
"""

from working_memory.expiration import is_expired


class Retriever:
    def __init__(self, store, min_confidence=0.0):
        self.store = store
        self.min_confidence = min_confidence

    def search(self, query, scope, limit=10, namespace=None, min_confidence=None):
        filters = {"user_scope": scope}
        if namespace is not None:
            filters["namespace"] = namespace

        results = self.store.search(query, filters, limit)

        threshold = self.min_confidence if min_confidence is None else min_confidence
        fresh = []
        for record in results:
            metadata = record.get("metadata", record)
            if is_expired(metadata.get("expires_at")):
                continue
            if metadata.get("confidence") is not None and metadata["confidence"] < threshold:
                continue
            fresh.append(record)
        return fresh[:limit]
