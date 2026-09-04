import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _pathfix  # noqa: F401

from retention.policy import RetentionPolicy
from retention.cleanup import Cleanup
from forgetting.deletion import DeletionCoordinator
from forgetting.verification import DeletionVerifier
from errors import DeletePartial, DeleteVerificationFailed


class TestRetentionPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = RetentionPolicy(task_history_days=30)

    def test_explicit_expiry_wins(self):
        self.assertTrue(self.policy.expired({"expires_at": "2000-01-01T00:00:00+00:00"}))

    def test_user_controlled_never_expires_without_explicit_ttl(self):
        self.assertFalse(self.policy.expired({"retention_policy": "USER_CONTROLLED"}))

    def test_ephemeral_without_ttl_is_eligible_for_cleanup(self):
        self.assertTrue(self.policy.expired({"retention_policy": "EPHEMERAL"}))

    def test_task_retention_respects_history_window(self):
        old = {"retention_policy": "TASK_RETENTION", "created_at": "2000-01-01T00:00:00+00:00"}
        self.assertTrue(self.policy.expired(old))


class TestCleanup(unittest.TestCase):
    def test_cleanup_drops_expired_keeps_fresh(self):
        records = [
            {"memory_id": "old", "expires_at": "2000-01-01T00:00:00+00:00"},
            {"memory_id": "new", "retention_policy": "USER_CONTROLLED"},
        ]
        survivors = Cleanup().run(records, RetentionPolicy())
        self.assertEqual([r["memory_id"] for r in survivors], ["new"])


class TestDeletionCoordinator(unittest.TestCase):
    def test_all_stores_succeed(self):
        calls = []
        coordinator = DeletionCoordinator()
        result = coordinator.delete(["M1"], {"a": calls.append, "b": calls.append})
        self.assertTrue(result)
        self.assertEqual(calls, ["M1", "M1"])

    def test_partial_failure_raises_and_logs(self):
        class Log:
            def __init__(self):
                self.entries = []

            def record(self, entry):
                self.entries.append(entry)

        log = Log()
        coordinator = DeletionCoordinator(reconciliation_log=log)

        def failing(_):
            raise RuntimeError("backend down")

        with self.assertRaises(DeletePartial):
            coordinator.delete(["M1"], {"a": lambda i: None, "b": failing})
        self.assertEqual(len(log.entries), 1)
        self.assertEqual(log.entries[0]["store"], "b")


class TestDeletionVerifier(unittest.TestCase):
    def test_fails_if_structured_record_remains(self):
        class Structured:
            def get(self, _):
                return {"memory_id": "M1"}

        class Semantic:
            def search(self, *a, **k):
                return []

        class Cache:
            def contains(self, _):
                return False

        with self.assertRaises(DeleteVerificationFailed):
            DeletionVerifier().verify("M1", Structured(), Semantic(), Cache())

    def test_passes_when_all_clear(self):
        class Empty:
            def get(self, _):
                return None

            def search(self, *a, **k):
                return []

            def contains(self, _):
                return False

        self.assertTrue(DeletionVerifier().verify("M1", Empty(), Empty(), Empty()))


if __name__ == "__main__":
    unittest.main()
