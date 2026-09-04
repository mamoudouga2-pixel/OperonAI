"""
Long-term semantic memory store (spec 8.8 LONG-TERM SEMANTIC MEMORY).

    Memory Write
      -> classify -> redact/filter -> policy decision -> embed
      -> store vector + metadata
"""


class SemanticStore:
    def __init__(self, vector, embedder):
        self.v = vector
        self.e = embedder

    def upsert(self, memory):
        text = memory.get("summary") or memory.get("content") or ""
        record = {
            "id": memory["memory_id"],
            "vector": self.e.embed(text),
            "metadata": memory,
        }
        memory = dict(memory)
        memory["embedding_version"] = self.e.version
        record["metadata"] = memory
        self.v.upsert([record])
        return memory

    def get(self, memory_id):
        """Point lookup by id, used by conflict resolution and by
        anything that needs "does this memory already exist" without
        doing a similarity search. Implemented via a metadata-equality
        filter rather than a backend-specific id index, so it works
        against any VectorStoreAdapter (spec 8.9: no backend-specific
        queries above this layer).
        """
        results = self.v.search("", {"memory_id": memory_id}, limit=1)
        return results[0]["metadata"] if results else None

    def search(self, query, filters, limit=10):
        return self.v.search(query, filters, limit)

    def delete(self, memory_id):
        self.v.delete([memory_id])

    def delete_namespace(self, namespace):
        self.v.delete_namespace(namespace)
