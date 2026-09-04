import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _pathfix  # noqa: F401

from task_memory.checkpoint import CheckpointStore
from errors import MemoryNotFound, MemoryWriteBlocked


class TestCheckpointStore(unittest.TestCase):
    def setUp(self):
        self.store = CheckpointStore()

    def test_save_returns_checkpoint(self):
        cp = self.store.save("T1", ["step1"], ["ev1"], 1, "step1_done", "fp-a")
        self.assertEqual(cp["safe_resume_point"], "step1_done")
        self.assertEqual(cp["completed_steps"], ["step1"])

    def test_resume_with_matching_fingerprint_succeeds(self):
        self.store.save("T1", ["step1"], [], 1, "step1_done", "fp-a")
        resumed = self.store.resume("T1", "fp-a")
        self.assertEqual(resumed["safe_resume_point"], "step1_done")

    def test_resume_with_changed_fingerprint_blocked(self):
        self.store.save("T1", ["step1"], [], 1, "step1_done", "fp-a")
        with self.assertRaises(MemoryWriteBlocked):
            self.store.resume("T1", "fp-changed")

    def test_resume_unknown_task_not_found(self):
        with self.assertRaises(MemoryNotFound):
            self.store.resume("no-such-task", "fp-a")

    def test_clear_removes_checkpoint(self):
        self.store.save("T1", [], [], 1, "x", "fp")
        self.store.clear("T1")
        self.assertIsNone(self.store.latest("T1"))


if __name__ == "__main__":
    unittest.main()
