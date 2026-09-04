import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _pathfix  # noqa: F401

from structured_storage.sqlite_adapter import SQLiteAdapter
from structured_storage.repository import Repository
from user_preferences.preferences import Preferences
from user_preferences.consent import Consent
from memory_manager.cache import RetrievalCache
from memory_manager.conflict import ConflictResolver
from memory_manager.router import MemoryRouter
from errors import MemoryWriteBlocked


class TestPreferences(unittest.TestCase):
    def test_version_increments_on_overwrite(self):
        prefs = Preferences(Repository(SQLiteAdapter()))
        first = prefs.set({"memory_id": "P1", "user_scope": "U1", "summary": "dark mode"})
        second = prefs.set(first)
        self.assertEqual(first["version"], 1)
        self.assertEqual(second["version"], 2)

    def test_delete_removes_preference(self):
        prefs = Preferences(Repository(SQLiteAdapter()))
        prefs.set({"memory_id": "P1", "user_scope": "U1"})
        prefs.delete("P1")
        self.assertIsNone(prefs.get("P1"))


class TestConsent(unittest.TestCase):
    def test_grant_and_revoke(self):
        consent = Consent()
        self.assertFalse(consent.allowed("infer:habits"))
        consent.grant("infer:habits")
        self.assertTrue(consent.allowed("infer:habits"))
        consent.revoke("infer:habits")
        self.assertFalse(consent.allowed("infer:habits"))


class TestRetrievalCache(unittest.TestCase):
    def test_invalidate_drops_matching_entries(self):
        cache = RetrievalCache(ttl_seconds=60)
        cache.set("q1", [{"id": "M1"}, {"id": "M2"}])
        self.assertIsNotNone(cache.get("q1"))
        cache.invalidate("M1")
        self.assertIsNone(cache.get("q1"))

    def test_untouched_entries_survive(self):
        cache = RetrievalCache(ttl_seconds=60)
        cache.set("q1", [{"id": "M1"}])
        cache.set("q2", [{"id": "M2"}])
        cache.invalidate("M1")
        self.assertIsNone(cache.get("q1"))
        self.assertIsNotNone(cache.get("q2"))


class TestConflictResolver(unittest.TestCase):
    def test_no_existing_record_inserts(self):
        action, _ = ConflictResolver().resolve(None, {"memory_id": "M1"})
        self.assertEqual(action, "insert")

    def test_same_id_versions(self):
        existing = {"memory_id": "M1", "version": 1, "provenance": {"source": "USER_EXPLICIT"}}
        incoming = {"memory_id": "M1", "provenance": {"source": "USER_EXPLICIT"}}
        action, merged = ConflictResolver().resolve(existing, incoming)
        self.assertEqual(action, "version")
        self.assertEqual(merged["version"], 2)

    def test_lower_authority_source_rejected(self):
        existing = {"memory_id": "M1", "provenance": {"source": "USER_EXPLICIT"}}
        incoming = {"memory_id": "M2", "provenance": {"source": "USER_APPROVED_INFERENCE"}}
        action, kept = ConflictResolver().resolve(existing, incoming)
        self.assertEqual(action, "reject")
        self.assertEqual(kept, existing)

    def test_lower_authority_rejected_even_with_same_id(self):
        existing = {"memory_id": "M1", "version": 1, "provenance": {"source": "USER_EXPLICIT"}}
        incoming = {"memory_id": "M1", "provenance": {"source": "USER_APPROVED_INFERENCE"}}
        action, kept = ConflictResolver().resolve(existing, incoming)
        self.assertEqual(action, "reject")
        self.assertEqual(kept, existing)

    def test_equal_authority_different_id_same_content_merges(self):
        existing = {
            "memory_id": "M1",
            "summary": "likes tea",
            "provenance": {"source": "USER_EXPLICIT"},
        }
        incoming = {
            "memory_id": "M2",
            "summary": "likes tea",
            "provenance": {"source": "USER_EXPLICIT"},
        }
        action, merged = ConflictResolver().resolve(existing, incoming)
        self.assertEqual(action, "merge")
        self.assertEqual(merged["audit"]["merged_from"], "M2")

    def test_equal_authority_different_id_different_content_versions(self):
        existing = {
            "memory_id": "M1",
            "version": 1,
            "summary": "likes tea",
            "provenance": {"source": "USER_EXPLICIT"},
        }
        incoming = {
            "memory_id": "M2",
            "summary": "likes coffee",
            "provenance": {"source": "USER_EXPLICIT"},
        }
        action, merged = ConflictResolver().resolve(existing, incoming)
        self.assertEqual(action, "version")
        self.assertEqual(merged["version"], 2)


class TestRouter(unittest.TestCase):
    def test_known_type_routes(self):
        self.assertEqual(MemoryRouter().route("PREFERENCE"), "structured")

    def test_unknown_type_blocked(self):
        with self.assertRaises(MemoryWriteBlocked):
            MemoryRouter().route("NOT_A_TYPE")


if __name__ == "__main__":
    unittest.main()
