"""
Repository: the only interface upper layers should use to talk to
structured storage (spec 8.7 - keeps the DB implementation swappable).
"""

from errors import MemoryNotFound, MemoryScopeDenied


class Repository:
    def __init__(self, adapter):
        self.adapter = adapter

    def save(self, memory):
        return self.adapter.upsert(memory)

    def upsert(self, memory):
        """Alias so Repository satisfies the same upsert/get/search
        interface MemoryManager uses uniformly across all stores."""
        return self.save(memory)

    def get(self, memory_id, scope=None):
        record = self.adapter.get(memory_id)
        if record is None:
            return None
        if scope is not None and record.get("user_scope") != scope:
            raise MemoryScopeDenied(memory_id=memory_id)
        return record

    def require(self, memory_id, scope=None):
        record = self.get(memory_id, scope=scope)
        if record is None:
            raise MemoryNotFound(memory_id=memory_id)
        return record

    def delete(self, memory_id):
        return self.adapter.delete(memory_id)

    def search(self, scope, namespace=None):
        return self.adapter.search(scope, namespace=namespace)

    def health_check(self):
        return self.adapter.health_check()
