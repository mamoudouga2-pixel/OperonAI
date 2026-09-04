import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _pathfix  # noqa: F401

from memory_manager.policy import MemoryPolicy
from errors import MemoryProvenanceInvalid, MemorySensitivityBlocked, MemoryWriteBlocked


class TestMemoryPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = MemoryPolicy()
        self.base = {
            "memory_id": "M1",
            "provenance": {"source": "USER_EXPLICIT"},
            "retention_policy": "USER_CONTROLLED",
            "sensitivity": "NORMAL",
            "summary": "likes tea",
        }

    def test_missing_provenance_rejected(self):
        with self.assertRaises(MemoryProvenanceInvalid):
            self.policy.validate({"retention_policy": "USER_CONTROLLED"})

    def test_unknown_provenance_source_rejected(self):
        with self.assertRaises(MemoryProvenanceInvalid):
            self.policy.validate({**self.base, "provenance": {"source": "GUESS"}})

    def test_unapproved_inference_rejected(self):
        with self.assertRaises(MemoryProvenanceInvalid):
            self.policy.validate(
                {**self.base, "provenance": {"source": "USER_APPROVED_INFERENCE"}}
            )

    def test_approved_inference_allowed(self):
        self.assertTrue(
            self.policy.validate(
                {
                    **self.base,
                    "provenance": {"source": "USER_APPROVED_INFERENCE", "approved": True},
                }
            )
        )

    def test_invalid_retention_policy_rejected(self):
        with self.assertRaises(MemoryWriteBlocked):
            self.policy.validate({**self.base, "retention_policy": "FOREVER"})

    def test_explicit_secret_sensitivity_rejected(self):
        with self.assertRaises(MemorySensitivityBlocked):
            self.policy.validate({**self.base, "sensitivity": "SECRET"})

    def test_secret_shaped_content_autoblocked_even_if_untagged(self):
        with self.assertRaises(MemorySensitivityBlocked):
            self.policy.validate({**self.base, "sensitivity": "NORMAL", "summary": "api_key=abc123"})

    def test_valid_memory_passes(self):
        self.assertTrue(self.policy.validate(self.base))

    def test_redact_masks_secrets_in_summary(self):
        redacted = self.policy.redact({**self.base, "summary": "password=hunter2"})
        self.assertIn("[REDACTED]", redacted["summary"])
        self.assertNotIn("hunter2", redacted["summary"])


if __name__ == "__main__":
    unittest.main()
