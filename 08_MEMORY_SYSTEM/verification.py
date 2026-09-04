"""
Delete verification (spec 8.21 DELETE VERIFICATION).

    - Structured record deleted
    - Vector record deleted
    - Relevant cache invalidated
    - Future retrieval no longer returns the target record
"""

from errors import DeleteVerificationFailed


class DeletionVerifier:
    def verify(self, memory_id, structured, semantic, cache):
        if structured.get(memory_id) is not None:
            raise DeleteVerificationFailed("structured record still present", memory_id=memory_id)
        if semantic.search("", {"memory_id": memory_id}, 10):
            raise DeleteVerificationFailed("vector record still present", memory_id=memory_id)
        if cache.contains(memory_id):
            raise DeleteVerificationFailed("cache still references record", memory_id=memory_id)
        return True
