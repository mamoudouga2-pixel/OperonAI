import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from screen_understanding.analyzer import ScreenAnalyzer
from screen_understanding.element_detector import ElementDetector
from screen_understanding.text_reader import TextReader
from screen_understanding.state_classifier import StateClassifier


class FakeRegistry:
    def __init__(self, payload):
        self.payload = payload

    def analyze(self, observation):
        return self.payload


class ScreenAnalyzerTests(unittest.TestCase):
    def test_aggregates_into_the_full_7_5_output_contract(self):
        payload = {"elements": [{"role": "button", "text": "Submit", "confidence": .9}],
                   "errors": [], "loading": False, "confidence": .9, "uncertainty_reason": None}
        analyzer = ScreenAnalyzer(FakeRegistry(payload))
        out = analyzer.analyze({})
        for key in ("elements", "errors", "loading", "confidence", "uncertainty_reason"):
            self.assertIn(key, out)
        self.assertEqual(out["state"], "READY")
        self.assertEqual(out["text"], ["Submit"])

    def test_merges_adapter_errors_with_independently_detected_errors(self):
        payload = {"elements": [{"role": "text", "text": "permission denied"}],
                   "errors": ["ADAPTER_FLAGGED"], "loading": False, "confidence": .5, "uncertainty_reason": None}
        analyzer = ScreenAnalyzer(FakeRegistry(payload))
        out = analyzer.analyze({})
        self.assertIn("ADAPTER_FLAGGED", out["errors"])
        self.assertIn("PERMISSION", out["errors"])
        self.assertEqual(out["state"], "ERROR")

    def test_no_elements_produces_uncertainty_reason(self):
        payload = {"elements": [], "errors": [], "loading": False, "confidence": 0, "uncertainty_reason": None}
        analyzer = ScreenAnalyzer(FakeRegistry(payload))
        out = analyzer.analyze({})
        self.assertEqual(out["uncertainty_reason"], "no_elements_detected")
        self.assertEqual(out["state"], "UNCERTAIN")


class SubComponentTests(unittest.TestCase):
    def test_element_detector(self):
        self.assertEqual(ElementDetector().detect({"elements": [{"role": "x"}]}), [{"role": "x"}])

    def test_text_reader_skips_empty_text(self):
        elements = {"elements": [{"text": "hi"}, {"text": ""}, {}]}
        self.assertEqual(TextReader().read(elements), ["hi"])

    def test_state_classifier_precedence_loading_over_error(self):
        sc = StateClassifier()
        self.assertEqual(sc.classify({"loading": True, "errors": ["x"]}), "LOADING")
        self.assertEqual(sc.classify({"loading": False, "errors": ["x"]}), "ERROR")
        self.assertEqual(sc.classify({"loading": False, "errors": [], "uncertainty_reason": "why"}), "UNCERTAIN")
        self.assertEqual(sc.classify({"loading": False, "errors": []}), "READY")


if __name__ == "__main__":
    unittest.main()
