"""
End-to-end scenarios (spec 8.32 END-TO-END TESTS):

1. User preference saved -> retrieved only in authorized scope.
2. Task crashes -> checkpoint -> current state validation -> safe resume.
3. User says forget -> structured/vector/cache deletion -> retrieval
   test returns nothing.
4. Vector backend unavailable -> health failure -> safe degraded
   behaviour.
5. Plugin attempts cross-namespace memory access -> denied.
"""

import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _pathfix  # noqa: F401

from memory_manager.manager import MemoryManager
from memory_manager.policy import MemoryPolicy
from memory_manager.router import MemoryRouter
from memory_manager.cache import RetrievalCache
from structured_storage.sqlite_adapter import SQLiteAdapter
from structured_storage.repository import Repository
from user_preferences.preferences import Preferences
from long_term_memory.semantic_store import SemanticStore
from long_term_memory.embedding import EmbeddingAdapter
from vector_storage.qdrant_adapter import QdrantAdapter
from task_memory.checkpoint import CheckpointStore
from task_memory.task_store import TaskStore
from working_memory.state_store import StateStore
from forgetting.forget import Forgetter
from forgetting.verification import DeletionVerifier
from errors import MemoryScopeDenied, MemoryWriteBlocked, VectorStoreUnavailable


def build_manager():
    repo = Repository(SQLiteAdapter())
    vector = QdrantAdapter()
    semantic = SemanticStore(vector, EmbeddingAdapter())
    stores = {
        "working": StateStore(),
        "task": TaskStore(),
        "structured": repo,
        "semantic": semantic,
    }
    manager = MemoryManager(
        policy=MemoryPolicy(),
        router=MemoryRouter(),
        stores=stores,
        cache=RetrievalCache(),
    )
    return manager, repo, vector, semantic


class TestScenario1PreferenceScoping(unittest.TestCase):
    """User preference saved -> retrieved only in authorized scope."""

    def test_preference_visible_only_to_owning_scope(self):
        _manager, repo, _vector, _semantic = build_manager()
        prefs = Preferences(repo)
        prefs.set(
            {
                "memory_id": "PREF-1",
                "user_scope": "U1",
                "namespace": "preferences",
                "summary": "prefers metric units",
                "provenance": {"source": "USER_EXPLICIT"},
                "retention_policy": "USER_CONTROLLED",
                "sensitivity": "NORMAL",
            }
        )
        self.assertEqual(repo.get("PREF-1", scope="U1")["memory_id"], "PREF-1")
        with self.assertRaises(MemoryScopeDenied):
            repo.get("PREF-1", scope="U2")


class TestScenario2CrashCheckpointResume(unittest.TestCase):
    """Task crashes -> checkpoint -> state validation -> safe resume."""

    def test_resume_allowed_only_if_world_state_unchanged(self):
        checkpoints = CheckpointStore()
        checkpoints.save(
            task_id="TASK-1",
            completed_steps=["open_browser", "navigate"],
            evidence_refs=["screenshot-1"],
            plan_version=1,
            safe_resume_point="post_navigate",
            state_fingerprint="page-hash-AAA",
        )
        # Simulated crash + restart: environment re-checked before resume.
        resumed = checkpoints.resume("TASK-1", current_fingerprint="page-hash-AAA")
        self.assertEqual(resumed["safe_resume_point"], "post_navigate")

    def test_resume_blocked_if_real_world_state_diverged(self):
        checkpoints = CheckpointStore()
        checkpoints.save(
            task_id="TASK-2",
            completed_steps=["fill_form"],
            evidence_refs=[],
            plan_version=1,
            safe_resume_point="post_fill",
            state_fingerprint="page-hash-AAA",
        )
        # The browser/page changed since the checkpoint was taken.
        with self.assertRaises(MemoryWriteBlocked):
            checkpoints.resume("TASK-2", current_fingerprint="page-hash-BBB")


class TestScenario3ForgetCommand(unittest.TestCase):
    """User says forget -> structured/vector/cache deletion -> retrieval
    test returns nothing."""

    def test_forget_removes_memory_from_every_store(self):
        manager, repo, _vector, semantic = build_manager()
        memory = {
            "memory_id": "M1",
            "user_scope": "U1",
            "namespace": "facts",
            "type": "LONG_TERM_SEMANTIC",
            "summary": "lives in Dhaka",
            "provenance": {"source": "USER_EXPLICIT"},
            "retention_policy": "USER_CONTROLLED",
            "sensitivity": "NORMAL",
        }
        manager.write(memory)
        # Also mirror the fact into structured storage, as a real forget
        # flow would need to clear every store that references the id.
        repo.save({**memory, "type": "AUDIT_REFERENCE"})
        self.assertTrue(manager.retrieve("Dhaka", scope="U1"))

        forgetter = Forgetter(repo, semantic, manager.cache, verifier=DeletionVerifier())
        self.assertTrue(forgetter.forget("M1"))

        self.assertIsNone(repo.get("M1"))
        self.assertEqual(semantic.search("Dhaka", {"memory_id": "M1"}), [])
        # A fresh retrieval (post cache-invalidation) must not resurrect it.
        results = manager.retrieve("Dhaka", scope="U1")
        self.assertFalse(any(r["metadata"]["memory_id"] == "M1" for r in results))


class TestScenario4VectorBackendUnavailable(unittest.TestCase):
    """Vector backend unavailable -> health failure -> safe degraded
    behaviour (no silent data loss, no crash of the whole manager)."""

    def test_outage_reported_and_write_fails_safely(self):
        manager, _repo, vector, _semantic = build_manager()
        vector.set_outage(True)
        self.assertFalse(vector.health_check())

        with self.assertRaises(VectorStoreUnavailable):
            manager.write(
                {
                    "memory_id": "M1",
                    "user_scope": "U1",
                    "namespace": "facts",
                    "type": "LONG_TERM_SEMANTIC",
                    "summary": "some fact",
                    "provenance": {"source": "USER_EXPLICIT"},
                    "retention_policy": "USER_CONTROLLED",
                    "sensitivity": "NORMAL",
                }
            )
        # Recovery: once the backend is healthy again, writes succeed.
        vector.set_outage(False)
        self.assertTrue(vector.health_check())
        manager.write(
            {
                "memory_id": "M1",
                "user_scope": "U1",
                "namespace": "facts",
                "type": "LONG_TERM_SEMANTIC",
                "summary": "some fact",
                "provenance": {"source": "USER_EXPLICIT"},
                "retention_policy": "USER_CONTROLLED",
                "sensitivity": "NORMAL",
            }
        )
        self.assertTrue(manager.retrieve("some fact", scope="U1"))


class TestScenario5PluginNamespaceIsolation(unittest.TestCase):
    """Plugin attempts cross-namespace memory access -> denied."""

    def test_plugin_scoped_namespace_cannot_read_other_namespace(self):
        manager, _repo, _vector, _semantic = build_manager()
        manager.write(
            {
                "memory_id": "M1",
                "user_scope": "U1",
                "namespace": "user_core_facts",
                "type": "LONG_TERM_SEMANTIC",
                "summary": "personal medical note",
                "provenance": {"source": "USER_EXPLICIT"},
                "retention_policy": "USER_CONTROLLED",
                "sensitivity": "NORMAL",
            }
        )
        # A plugin only ever queries within its own granted namespace.
        plugin_results = manager.retrieve(
            "personal medical note", scope="U1", namespace="plugin_weather_widget"
        )
        self.assertEqual(plugin_results, [])


if __name__ == "__main__":
    unittest.main()
