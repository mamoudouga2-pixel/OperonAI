"""
Memory type -> backing store router (spec 8.4 MEMORY TYPES).
"""

from errors import MemoryWriteBlocked


class MemoryRouter:
    """Maps a memory ``type`` to the logical store name that owns it."""

    MAP = {
        "WORKING_STATE": "working",
        "TASK": "task",
        "STRUCTURED_PERSISTENT": "structured",
        "PREFERENCE": "structured",
        "LONG_TERM_SEMANTIC": "semantic",
        "AUDIT_REFERENCE": "structured",
    }

    def route(self, memory_type):
        if memory_type not in self.MAP:
            raise MemoryWriteBlocked(f"No route for memory type '{memory_type}'")
        return self.MAP[memory_type]

    def stores_for(self, store_name):
        """Reverse lookup: which memory types live in a given store."""
        return [t for t, s in self.MAP.items() if s == store_name]
