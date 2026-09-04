import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _pathfix  # noqa: F401

from memory_manager.manager import MemoryManager
from memory_manager.policy import MemoryPolicy
from memory_manager.router import MemoryRouter
from memory_manager.cache import RetrievalCache
from working_memory.state_store import StateStore
from task_memory.task_store import TaskStore
from structured_storage.sqlite_adapter import SQLiteAdapter
from structured_storage.repository import Repository
from long_term_memory.semantic_store import SemanticStore
from long_term_memory.embedding import EmbeddingAdapter
from vector_storage.qdrant_adapter import QdrantAdapter
from events import EventBus
from errors import MemoryProvenanceInvalid, MemoryScopeDenied


def build_manager(bus=None):
    stores = {
        "working": StateStore(),
        "task": TaskStore(),
        "structured": Repository(SQLiteAdapter()),
        "semantic": SemanticStore(QdrantAdapter(), EmbeddingAdapter()),
    }
    manager = MemoryManager(
        policy=MemoryPolicy(),
        router=MemoryRouter(),
        stores=stores,
        cache=RetrievalCache(),
        bus=bus or EventBus(),
    )
    return manager, stores


class TestMemoryManagerWriteRoute(unittest.TestCase):
    def test_preference_routes_to_structured_and_emits_events(self):
        bus = EventBus()
        manager, stores = build_manager(bus)
        manager.write(
            {
                "memory_id": "P1",
                "user_scope": "U1",
                "namespace": "preferences",
                "type": "PREFERENCE",
                "content": {"theme": "dark"},
                "provenance": {"source": "USER_EXPLICIT"},
                "retention_policy": "USER_CONTROLLED",
                "sensitivity": "NORMAL",
            }
        )
        self.assertIsNotNone(stores["structured"].get("P1"))
        event_names = [e["event"] for e in bus.history()]
        self.assertIn("MEMORY_WRITE_REQUESTED", event_names)
        self.assertIn("MEMORY_STORED", event_names)

    def test_long_term_semantic_routes_to_vector_store(self):
        manager, stores = build_manager()
        manager.write(
            {
                "memory_id": "M1",
                "user_scope": "U1",
                "namespace": "facts",
                "type": "LONG_TERM_SEMANTIC",
                "summary": "user prefers tea over coffee",
                "provenance": {"source": "USER_EXPLICIT"},
                "retention_policy": "USER_CONTROLLED",
                "sensitivity": "NORMAL",
            }
        )
        results = manager.retrieve("tea", scope="U1")
        self.assertEqual(len(results), 1)

    def test_policy_violation_blocks_write(self):
        manager, _stores = build_manager()
        with self.assertRaises(MemoryProvenanceInvalid):
            manager.write({"memory_id": "X", "type": "PREFERENCE", "user_scope": "U1"})

    def test_scope_mismatch_denied(self):
        manager, _stores = build_manager()
        with self.assertRaises(MemoryScopeDenied):
            manager.write(
                {
                    "memory_id": "P1",
                    "user_scope": "OTHER",
                    "type": "PREFERENCE",
                    "provenance": {"source": "USER_EXPLICIT"},
                    "retention_policy": "USER_CONTROLLED",
                    "sensitivity": "NORMAL",
                },
                scope="U1",
            )


class TestRetrievalCacheInvalidationAcrossWrites(unittest.TestCase):
    def test_cache_served_then_invalidated_on_update(self):
        manager, stores = build_manager()
        base = {
            "memory_id": "M1",
            "user_scope": "U1",
            "namespace": "facts",
            "type": "LONG_TERM_SEMANTIC",
            "summary": "likes dogs",
            "provenance": {"source": "USER_EXPLICIT"},
            "retention_policy": "USER_CONTROLLED",
            "sensitivity": "NORMAL",
        }
        manager.write(base)
        first = manager.retrieve("dogs", scope="U1")
        self.assertEqual(len(first), 1)

        # Update the same memory; the retrieval cache must not serve the
        # stale pre-update result on the next query for this key.
        manager.update(dict(base, summary="loves dogs and cats"))
        second = manager.retrieve("dogs", scope="U1")
        self.assertEqual(second[0]["metadata"]["summary"], "loves dogs and cats")


class TestNamespaceIsolation(unittest.TestCase):
    def test_retrieval_scoped_to_user(self):
        manager, _stores = build_manager()
        for scope in ("U1", "U2"):
            manager.write(
                {
                    "memory_id": f"M-{scope}",
                    "user_scope": scope,
                    "namespace": "facts",
                    "type": "LONG_TERM_SEMANTIC",
                    "summary": "shared topic",
                    "provenance": {"source": "USER_EXPLICIT"},
                    "retention_policy": "USER_CONTROLLED",
                    "sensitivity": "NORMAL",
                }
            )
        u1_results = manager.retrieve("shared topic", scope="U1")
        self.assertEqual([r["metadata"]["memory_id"] for r in u1_results], ["M-U1"])


if __name__ == "__main__":
    unittest.main()


class TestConflictHandlingWiredIntoManager(unittest.TestCase):
    """Spec 8.18: conflict resolution must actually run during write(),
    not just exist as an unused utility class.

    Note on scope: MemoryManager looks up "existing" by exact
    memory_id, so this wiring catches re-writes of the *same* logical
    record (versioning instead of blind overwrite) and lets
    ConflictResolver's authority ranking apply when that happens.
    Cross-id duplicate *content* detection (two different memory_ids
    describing the same fact) is not implemented — that would need a
    namespace/entity index this package doesn't build yet. Don't test
    for something this layer doesn't do.
    """

    def test_repeated_write_of_same_id_versions_not_duplicates(self):
        manager, stores = build_manager()
        record = {
            "memory_id": "M1",
            "user_scope": "U1",
            "namespace": "facts",
            "type": "LONG_TERM_SEMANTIC",
            "summary": "likes jazz",
            "provenance": {"source": "USER_EXPLICIT"},
            "retention_policy": "USER_CONTROLLED",
            "sensitivity": "NORMAL",
        }
        first = manager.write(record)
        second = manager.write(record)
        self.assertEqual(first["version"], 1)
        self.assertEqual(second["version"], 2)

    def test_lower_authority_rewrite_of_same_id_is_rejected(self):
        manager, stores = build_manager()
        manager.write(
            {
                "memory_id": "P1",
                "user_scope": "U1",
                "namespace": "preferences",
                "type": "PREFERENCE",
                "summary": "wants email digests weekly",
                "provenance": {"source": "USER_EXPLICIT"},
                "retention_policy": "USER_CONTROLLED",
                "sensitivity": "NORMAL",
            }
        )
        # Same memory_id, but from a lower-authority source with a
        # different claim: must not silently overwrite the
        # user-explicit original.
        result = manager.write(
            {
                "memory_id": "P1",
                "user_scope": "U1",
                "namespace": "preferences",
                "type": "PREFERENCE",
                "summary": "wants email digests daily",
                "provenance": {"source": "USER_APPROVED_INFERENCE", "approved": True},
                "retention_policy": "USER_CONTROLLED",
                "sensitivity": "NORMAL",
            }
        )
        self.assertEqual(result["summary"], "wants email digests weekly")
        self.assertEqual(stores["structured"].get("P1")["summary"], "wants email digests weekly")
