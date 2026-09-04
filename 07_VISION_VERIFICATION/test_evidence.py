import sys
import tempfile
import time
import os
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evidence.collector import EvidenceCollector
from evidence.retention import RetentionPolicy
from evidence.hashing import sha256_bytes
from evidence.metadata import Evidence
from capture.artifact_store import ArtifactStore


class EvidenceCollectorTests(unittest.TestCase):
    def test_redaction_status_reflects_reality_not_a_constant(self):
        with tempfile.TemporaryDirectory() as d:
            c = EvidenceCollector(ArtifactStore(d))
            redacted = c.collect("T", "A", "desktop", b"x", "password token")
            clean = c.collect("T", "A", "desktop", b"y", "clicked submit")
            self.assertEqual(redacted.redaction_status, "APPLIED")
            self.assertEqual(redacted.description, "<REDACTED>")
            self.assertEqual(clean.redaction_status, "NOT_NEEDED")
            self.assertEqual(clean.description, "clicked submit")

    def test_shape_based_secret_detection_catches_unlabeled_tokens(self):
        with tempfile.TemporaryDirectory() as d:
            c = EvidenceCollector(ArtifactStore(d))
            jwt_like = "session is eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
            ev = c.collect("T", "A", "desktop", b"x", jwt_like)
            self.assertEqual(ev.redaction_status, "APPLIED")

    def test_evidence_type_parameter_is_honored(self):
        with tempfile.TemporaryDirectory() as d:
            c = EvidenceCollector(ArtifactStore(d))
            ev = c.collect("T", "A", "browser", b"x", "dom snapshot", evidence_type="DOM_SNAPSHOT")
            self.assertEqual(ev.type, "DOM_SNAPSHOT")

    def test_invalid_type_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            c = EvidenceCollector(ArtifactStore(d))
            with self.assertRaises(ValueError):
                c.collect("T", "A", "browser", b"x", "d", evidence_type="NOT_REAL")

    def test_hash_matches_stored_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            c = EvidenceCollector(ArtifactStore(d))
            ev = c.collect("T", "A", "desktop", b"exact-bytes", "d")
            self.assertEqual(ev.hash, sha256_bytes(b"exact-bytes"))


class RetentionPolicyTests(unittest.TestCase):
    def test_allowed_boolean(self):
        rp = RetentionPolicy(max_age_ms=1000)
        self.assertTrue(rp.allowed(500))
        self.assertFalse(rp.allowed(1500))

    def test_sweep_deletes_only_expired_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            store = ArtifactStore(d)
            old_path = store.save("old.bin", b"x")
            store.save("new.bin", b"y")
            old_time = time.time() - 60
            os.utime(old_path, (old_time, old_time))
            rp = RetentionPolicy(max_age_ms=10_000)
            deleted = rp.sweep(store)
            self.assertEqual(deleted, ["old.bin"])
            self.assertFalse(store.exists("old.bin"))
            self.assertTrue(store.exists("new.bin"))


class MetadataTests(unittest.TestCase):
    def test_evidence_to_dict_round_trips_all_fields(self):
        e = Evidence("E1", "T1", "A1", "SCREENSHOT", "desktop", "2026-01-01T00:00:00+00:00",
                     "/path", "abc123", "desc", "NOT_NEEDED")
        d = e.to_dict()
        self.assertEqual(d["evidence_id"], "E1")
        self.assertEqual(d["redaction_status"], "NOT_NEEDED")


if __name__ == "__main__":
    unittest.main()
