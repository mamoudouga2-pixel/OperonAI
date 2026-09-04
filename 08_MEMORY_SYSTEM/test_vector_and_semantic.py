import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _pathfix  # noqa: F401

from vector_storage.qdrant_adapter import QdrantAdapter
from long_term_memory.embedding import EmbeddingAdapter
from long_term_memory.semantic_store import SemanticStore
from long_term_memory.consolidation import Consolidator
from memory_manager.policy import MemoryPolicy
from errors import VectorStoreUnavailable


class TestQdrantAdapter(unittest.TestCase):
    def setUp(self):
        self.v = QdrantAdapter()

    def test_upsert_search_delete(self):
        self.v.upsert([{"id": "A", "vector": [1, 0], "metadata": {"namespace": "n1"}}])
        self.assertEqual(len(self.v.search("", {"namespace": "n1"})), 1)
        self.v.delete(["A"])
        self.assertEqual(self.v.search("", {"namespace": "n1"}), [])

    def test_delete_namespace(self):
        self.v.upsert([{"id": "A", "vector": [1], "metadata": {"namespace": "n1"}}])
        self.v.upsert([{"id": "B", "vector": [1], "metadata": {"namespace": "n2"}}])
        self.v.delete_namespace("n1")
        remaining_ids = [r["id"] for r in self.v.search("", {})]
        self.assertEqual(remaining_ids, ["B"])

    def test_snapshot_restore(self):
        self.v.upsert([{"id": "A", "vector": [1], "metadata": {}}])
        snap = self.v.snapshot()
        fresh = QdrantAdapter()
        fresh.restore(snap)
        self.assertEqual(len(fresh.search("", {})), 1)

    def test_simulated_outage_blocks_operations(self):
        self.v.set_outage(True)
        self.assertFalse(self.v.health_check())
        with self.assertRaises(VectorStoreUnavailable):
            self.v.upsert([{"id": "A", "vector": [1], "metadata": {}}])
        with self.assertRaises(VectorStoreUnavailable):
            self.v.search("", {})


class TestSemanticStore(unittest.TestCase):
    def test_upsert_stamps_embedding_version(self):
        store = SemanticStore(QdrantAdapter(), EmbeddingAdapter(version="v-test"))
        result = store.upsert(
            {"memory_id": "M1", "user_scope": "U1", "namespace": "n", "summary": "likes tea"}
        )
        self.assertEqual(result["embedding_version"], "v-test")


class TestConsolidator(unittest.TestCase):
    def test_rejects_missing_provenance(self):
        items = [{"summary": "x", "retention_policy": "USER_CONTROLLED"}]
        self.assertEqual(Consolidator().consolidate(items, MemoryPolicy()), [])

    def test_rejects_unapproved_inference(self):
        items = [
            {
                "summary": "x",
                "retention_policy": "USER_CONTROLLED",
                "provenance": {"source": "USER_APPROVED_INFERENCE"},
            }
        ]
        self.assertEqual(Consolidator().consolidate(items, MemoryPolicy()), [])

    def test_deduplicates_repeated_observations(self):
        item = {
            "memory_id": "M1",
            "summary": "prefers dark mode",
            "retention_policy": "USER_CONTROLLED",
            "provenance": {"source": "USER_EXPLICIT"},
        }
        items = [item, dict(item, memory_id="M2"), dict(item, memory_id="M3")]
        result = Consolidator().consolidate(items, MemoryPolicy())
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
