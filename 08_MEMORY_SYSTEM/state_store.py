"""
In-memory ephemeral state store backing working memory (spec 8.5).

Deliberately process-local: working memory is not meant to survive a
restart. Anything that must survive belongs in task memory or
structured storage instead.
"""


class StateStore:
    def __init__(self):
        self.data = {}

    def upsert(self, memory):
        self.data[memory["memory_id"]] = dict(memory)
        return memory

    def get(self, memory_id):
        item = self.data.get(memory_id)
        return dict(item) if item is not None else None

    def delete(self, memory_id):
        self.data.pop(memory_id, None)

    def all(self):
        return [dict(v) for v in self.data.values()]

    def cleanup(self, expired_fn):
        """Delete every entry for which ``expired_fn(expires_at)`` is
        True. Returns the ids that were removed."""
        removed = []
        for memory_id, memory in list(self.data.items()):
            if expired_fn(memory.get("expires_at")):
                self.delete(memory_id)
                removed.append(memory_id)
        return removed
