import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _pathfix  # noqa: F401

from structured_storage.sqlite_adapter import SQLiteAdapter
from structured_storage.repository import Repository
from structured_storage.migrations import Migrations
from errors import MemoryNotFound, MemoryScopeDenied


class TestSQLiteAdapter(unittest.TestCase):
    def setUp(self):
        self.db = SQLiteAdapter()
        self.mem = {
            "memory_id": "M1",
            "user_scope": "U1",
            "namespace": "preferences",
            "type": "PREFERENCE",
            "content": {"x": 1},
        }

    def test_health_check_ok(self):
        self.assertTrue(self.db.health_check())

    def test_upsert_and_get_roundtrip(self):
        self.db.upsert(self.mem)
        self.assertEqual(self.db.get("M1")["memory_id"], "M1")

    def test_upsert_is_idempotent_update(self):
        self.db.upsert(self.mem)
        updated = dict(self.mem, content={"x": 2})
        self.db.upsert(updated)
        self.assertEqual(self.db.get("M1")["content"], {"x": 2})
        self.assertEqual(len(self.db.all_ids()), 1)

    def test_delete_removes_record(self):
        self.db.upsert(self.mem)
        self.db.delete("M1")
        self.assertIsNone(self.db.get("M1"))

    def test_search_filters_by_scope_and_namespace(self):
        self.db.upsert(self.mem)
        self.db.upsert(dict(self.mem, memory_id="M2", user_scope="U2"))
        results = self.db.search("U1")
        self.assertEqual([r["memory_id"] for r in results], ["M1"])

    def test_snapshot_restore_roundtrip(self):
        self.db.upsert(self.mem)
        snap = self.db.snapshot()
        fresh = SQLiteAdapter()
        fresh.restore(snap)
        self.assertEqual(fresh.get("M1")["memory_id"], "M1")

    def test_migrations_applied_once(self):
        version_before = Migrations().apply(self.db.db)
        version_after = Migrations().apply(self.db.db)
        self.assertEqual(version_before, version_after)


class TestRepository(unittest.TestCase):
    def setUp(self):
        self.repo = Repository(SQLiteAdapter())
        self.mem = {"memory_id": "M1", "user_scope": "U1", "type": "STRUCTURED_PERSISTENT", "content": {}}

    def test_require_raises_not_found(self):
        with self.assertRaises(MemoryNotFound):
            self.repo.require("missing")

    def test_get_enforces_scope(self):
        self.repo.save(self.mem)
        with self.assertRaises(MemoryScopeDenied):
            self.repo.get("M1", scope="OTHER_USER")

    def test_get_same_scope_allowed(self):
        self.repo.save(self.mem)
        self.assertEqual(self.repo.get("M1", scope="U1")["memory_id"], "M1")


if __name__ == "__main__":
    unittest.main()
