"""
WorkingMemory: current-task scratch state (spec 8.5 WORKING MEMORY).

"Large private files should not be copied wholesale into working
context by default" - callers should pass references, not raw file
contents, in ``content``.
"""

from .expiration import expires_in


class WorkingMemory:
    def __init__(self, store, default_ttl_minutes=60):
        self.store = store
        self.default_ttl_minutes = default_ttl_minutes

    def put(self, memory, ttl_minutes=None):
        entry = dict(memory)
        entry["type"] = "WORKING_STATE"
        entry.setdefault("version", 1)
        entry.setdefault(
            "expires_at", expires_in(ttl_minutes or self.default_ttl_minutes)
        )
        return self.store.upsert(entry)

    def get(self, memory_id):
        return self.store.get(memory_id)

    def delete(self, memory_id):
        return self.store.delete(memory_id)

    def cleanup(self, expired_fn):
        return self.store.cleanup(expired_fn)
