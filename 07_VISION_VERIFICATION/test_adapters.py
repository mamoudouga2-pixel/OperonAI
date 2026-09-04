import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from adapters.registry import AdapterRegistry
from adapters.ocr_adapter import OCRAdapterImpl, OCRUnavailableError
from adapters.vision_model_adapter import VisionModelAdapter
from events import EventBus


class BadVisionAdapter:
    def analyze(self, x):
        raise RuntimeError("model crashed")


class GoodVisionAdapter:
    def analyze(self, x):
        return {"elements": [{"role": "button", "text": "OK"}], "errors": [], "loading": False, "confidence": .9, "uncertainty_reason": None}


class RealOCRAdapterTests(unittest.TestCase):
    def test_reads_real_rendered_text(self):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (300, 80), color="white")
        d = ImageDraw.Draw(img)
        d.text((10, 25), "Submit Success", fill="black")
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        ocr = OCRAdapterImpl()
        result = ocr.read({"data": buf.getvalue()})
        self.assertIn("Submit", result["ocr_text"])
        self.assertGreater(len(result["elements"]), 0)
        self.assertGreater(result["confidence"], 0)

    def test_rejects_empty_data(self):
        with self.assertRaises(OCRUnavailableError):
            OCRAdapterImpl().read({"data": b""})

    def test_blank_image_reports_uncertainty_not_a_crash(self):
        from PIL import Image
        img = Image.new("RGB", (50, 50), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = OCRAdapterImpl().read({"data": buf.getvalue()})
        self.assertEqual(result["elements"], [])
        self.assertEqual(result["uncertainty_reason"], "no_text_detected")


class VisionModelAdapterTests(unittest.TestCase):
    def test_base_class_is_a_documented_extension_point_not_usable_directly(self):
        with self.assertRaises(NotImplementedError):
            VisionModelAdapter().analyze(b"x")


class AdapterRegistryTests(unittest.TestCase):
    def test_falls_back_from_vision_to_real_ocr_when_vision_fails(self):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (200, 50), color="white")
        ImageDraw.Draw(img).text((5, 15), "Loading", fill="black")
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        registry = AdapterRegistry()
        registry.register_vision(BadVisionAdapter())
        registry.register_ocr(OCRAdapterImpl())
        result = registry.analyze({"data": buf.getvalue()})
        self.assertIn("Loading", result["ocr_text"])
        # diagnostics captured the vision failure even though overall call succeeded
        self.assertEqual(len(registry.last_errors), 1)
        self.assertEqual(registry.last_errors[0]["kind"], "vision")

    def test_prefers_vision_over_ocr_when_vision_succeeds(self):
        registry = AdapterRegistry()
        registry.register_vision(GoodVisionAdapter())
        registry.register_ocr(OCRAdapterImpl())
        result = registry.analyze(b"irrelevant-for-good-adapter")
        self.assertEqual(result["elements"][0]["text"], "OK")

    def test_raises_model_adapter_failure_when_everything_fails(self):
        registry = AdapterRegistry()
        registry.register_vision(BadVisionAdapter())
        with self.assertRaisesRegex(RuntimeError, "MODEL_ADAPTER_FAILURE"):
            registry.analyze(b"x")

    def test_emits_analysis_events(self):
        bus = EventBus()
        registry = AdapterRegistry(event_bus=bus)
        registry.register_vision(GoodVisionAdapter())
        registry.analyze(b"x")
        events = [e["event"] for e in bus.history]
        self.assertIn("VISION_ANALYSIS_STARTED", events)
        self.assertIn("VISION_ANALYSIS_COMPLETED", events)


if __name__ == "__main__":
    unittest.main()
