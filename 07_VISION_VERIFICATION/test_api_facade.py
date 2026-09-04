import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import api
from events import EventBus


class ApiFacadeIntegrationTests(unittest.TestCase):
    """Exercises the spec 7.23 public API as a whole -- this facade, and
    5 of its 9 functions under their spec-mandated names, did not exist
    in any form before."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        api.configure(evidence_root=self._tmp.name, event_bus=EventBus())

    def tearDown(self):
        self._tmp.cleanup()

    def test_health_check_reports_all_subsystems(self):
        health = api.health_check()
        expected_subsystems = {
            "evidence_store", "vision_ocr_adapters",
            "capture_backend_importable", "ocr_backend_importable", "event_bus",
        }
        self.assertEqual(set(health["subsystems"]), expected_subsystems)
        self.assertEqual(health["subsystems"]["evidence_store"]["ok"], True)

    def test_collect_evidence_then_verify_end_to_end_through_the_facade(self):
        ev = api.collect_evidence({
            "task_id": "T1", "action_id": "A1", "source": "browser",
            "data": b"screenshot-bytes", "description": "form confirmation screen",
        })
        result = api.verify({
            "verification_id": "VER-1", "task_id": "T1", "action_id": "A1",
            "expected_state": {"operator": "AND", "conditions": [
                {"type": "EXPECTED_TEXT", "expected": "Success"}, {"type": "NO_ERROR"},
            ]},
            "current_state": {"text": ["Success"], "errors": [], "evidence_age_ms": 1},
            "evidence": [{"evidence_id": ev.evidence_id, "source": "browser"}],
        })
        self.assertEqual(result["status"], "VERIFIED")

    def test_detect_classify_recommend_chain(self):
        errors = api.detect_error({"text": ["permission denied"]})
        self.assertEqual(errors, ["PERMISSION"])
        failure_class = api.classify_failure(errors[0])
        self.assertEqual(failure_class, "PERMISSION")
        recovery = api.recommend_recovery({"failure": failure_class, "partial": False})
        self.assertEqual(recovery, "STOP")

    def test_analyze_then_ground_chain_with_real_ocr_fallback(self):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (300, 60), color="white")
        ImageDraw.Draw(img).text((10, 20), "Submit", fill="black")
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        api.configure(evidence_root=self._tmp.name, ocr_adapters=None)  # default OCR adapter
        observation = api.analyze({"data": buf.getvalue()})
        # OCR casing can vary by rendered font/size; match case-insensitively.
        self.assertTrue(any("submit" in e.get("text", "").lower() for e in observation["elements"]))

        hit = api.ground({"text": "Submit"}, {"elements": observation["elements"]})
        self.assertIsNotNone(hit)  # GroundingMatcher's fuzzy text scoring also tolerates the casing difference


if __name__ == "__main__":
    unittest.main()
