"""
Retrieval cache with invalidation (spec 8.24 CACHE INVALIDATION).

"After a memory delete/update the retrieval cache must be invalidated.
A deleted memory must never be served back to the model from cache."
"""

import time


class RetrievalCache:
    """Tiny in-process TTL cache in front of retrieval calls."""

    def __init__(self, ttl_seconds=60):
        self.ttl_seconds = ttl_seconds
        self._store = {}  # key -> (value, expires_at)

    def get(self, key):
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and expires_at <= time.time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key, value):
        expires_at = time.time() + self.ttl_seconds if self.ttl_seconds else None
        self._store[key] = (value, expires_at)

    def invalidate(self, memory_id):
        """Drop every cache entry that references ``memory_id``.

        Cache keys are opaque query keys, so we scan cached result sets
        for the id rather than assuming id == key. This favours
        correctness (never leak a deleted memory) over cache hit rate.
        """
        stale_keys = []
        for key, (value, _expires_at) in self._store.items():
            if key == memory_id:
                stale_keys.append(key)
                continue
            if isinstance(value, list) and any(
                isinstance(item, dict) and item.get("id") == memory_id
                or isinstance(item, dict) and item.get("memory_id") == memory_id
                for item in value
            ):
                stale_keys.append(key)
        for key in stale_keys:
            self._store.pop(key, None)

    def invalidate_all(self):
        self._store.clear()

    def contains(self, memory_id):
        """True if any cached entry still references ``memory_id``."""
        if memory_id in self._store:
            return True
        for value, _expires_at in self._store.values():
            if isinstance(value, list) and any(
                isinstance(item, dict) and item.get("id") == memory_id
                or isinstance(item, dict) and item.get("memory_id") == memory_id
                for item in value
            ):
                return True
        return False
