import sys, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _pathfix  # noqa: F401

from working_memory.state_store import StateStore
from working_memory.expiration import is_expired, expires_in
from working_memory.manager import WorkingMemory


class TestExpiration(unittest.TestCase):
    def test_no_expiry_never_expires(self):
        self.assertFalse(is_expired(None))
        self.assertFalse(is_expired(""))

    def test_past_timestamp_is_expired(self):
        self.assertTrue(is_expired("2000-01-01T00:00:00+00:00"))

    def test_future_timestamp_not_expired(self):
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        self.assertFalse(is_expired(future))

    def test_expires_in_produces_future_timestamp(self):
        ts = expires_in(30)
        self.assertFalse(is_expired(ts))


class TestStateStore(unittest.TestCase):
    def test_upsert_get_delete(self):
        store = StateStore()
        store.upsert({"memory_id": "M1", "content": {"x": 1}})
        self.assertEqual(store.get("M1")["content"], {"x": 1})
        store.delete("M1")
        self.assertIsNone(store.get("M1"))

    def test_cleanup_removes_only_expired(self):
        store = StateStore()
        store.upsert({"memory_id": "expired", "expires_at": "2000-01-01T00:00:00+00:00"})
        store.upsert({"memory_id": "fresh", "expires_at": None})
        removed = store.cleanup(is_expired)
        self.assertEqual(removed, ["expired"])
        self.assertIsNone(store.get("expired"))
        self.assertIsNotNone(store.get("fresh"))


class TestWorkingMemory(unittest.TestCase):
    def test_put_defaults_ttl_and_version(self):
        wm = WorkingMemory(StateStore(), default_ttl_minutes=60)
        entry = wm.put({"memory_id": "WM1", "task_id": "T1", "content": {}})
        self.assertEqual(entry["type"], "WORKING_STATE")
        self.assertEqual(entry["version"], 1)
        self.assertFalse(is_expired(entry["expires_at"]))

    def test_delete_removes_entry(self):
        wm = WorkingMemory(StateStore())
        wm.put({"memory_id": "WM1"})
        wm.delete("WM1")
        self.assertIsNone(wm.get("WM1"))


if __name__ == "__main__":
    unittest.main()
