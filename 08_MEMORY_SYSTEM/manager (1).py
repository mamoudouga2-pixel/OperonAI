"""
MemoryManager: the single entry point Boss/Workers/Interface use to
write and retrieve memories (spec 8.1 PRIMARY ARCHITECTURE, 8.13, 8.16).
"""

import time

import events as ev
from errors import MemoryError, MemoryScopeDenied
from .conflict import ConflictResolver


class MemoryManager:
    """Coordinates policy, routing, conflict resolution, storage and
    eventing for one write or retrieval call.

    ``stores`` maps logical store name ("working", "task", "structured",
    "semantic") to an object implementing at least ``upsert``/``get`` (and
    ``search`` for "semantic"). This indirection is what lets the SQLite
    or Qdrant adapters be swapped out without touching this class.
    """

    def __init__(self, policy, router, stores, cache=None, bus=None, conflict_resolver=None):
        self.policy = policy
        self.router = router
        self.stores = stores
        self.cache = cache
        self.bus = bus or ev.default_bus
        self.conflict_resolver = conflict_resolver or ConflictResolver()

    def write(self, memory, scope=None):
        self.bus.emit(ev.MEMORY_WRITE_REQUESTED, memory_id=memory.get("memory_id"))

        if scope is not None and memory.get("user_scope") not in (None, scope):
            raise MemoryScopeDenied(memory_id=memory.get("memory_id"))

        try:
            self.policy.validate(memory)
            store_name = self.router.route(memory["type"])
            store = self.stores[store_name]

            # Duplicate/conflict handling (spec 8.18): look the entity up
            # in its target store first, so a lower-authority source
            # can't silently clobber a higher-authority one, and repeats
            # get merged/versioned instead of piling up as duplicates.
            existing = None
            get_fn = getattr(store, "get", None)
            if callable(get_fn):
                existing = get_fn(memory.get("memory_id"))

            action, resolved = self.conflict_resolver.resolve(existing, memory)
            if action == "reject":
                self.bus.emit(
                    ev.MEMORY_CONFLICT_DETECTED,
                    memory_id=memory.get("memory_id"),
                    action=action,
                )
                return existing
            if action in ("merge", "version"):
                self.bus.emit(
                    ev.MEMORY_CONFLICT_DETECTED,
                    memory_id=resolved.get("memory_id"),
                    action=action,
                )

            memory = dict(resolved)
            memory.setdefault("created_at", memory.get("created_at") or _now())
            memory["updated_at"] = _now()
            result = store.upsert(memory)
        except MemoryError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            self.bus.emit(
                ev.MEMORY_STORAGE_FAILED,
                memory_id=memory.get("memory_id"),
                error=str(exc),
            )
            raise

        if self.cache is not None:
            self.cache.invalidate(memory.get("memory_id"))

        self.bus.emit(
            ev.MEMORY_STORED,
            memory_id=memory.get("memory_id"),
            namespace=memory.get("namespace"),
            type=memory.get("type"),
        )
        return result

    def update(self, memory, scope=None):
        result = self.write(memory, scope=scope)
        self.bus.emit(ev.MEMORY_UPDATED, memory_id=memory.get("memory_id"))
        return result

    def retrieve(self, query, scope, limit=None, namespace=None):
        """Scoped semantic retrieval (spec 8.16 MEMORY RETRIEVAL POLICY)."""
        filters = {"user_scope": scope}
        if namespace is not None:
            filters["namespace"] = namespace

        cache_key = (query, scope, namespace, limit)
        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        results = self.stores["semantic"].search(
            query, filters, limit or self.policy.max_retrieval_items
        )

        if self.cache is not None:
            self.cache.set(cache_key, results)

        self.bus.emit(ev.MEMORY_RETRIEVED, query=query, scope=scope, count=len(results))
        return results

    def get(self, memory_id, store_name):
        return self.stores[store_name].get(memory_id)


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
