import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from error_detection.detector import ErrorDetector
from error_detection.classifier import FailureClassifier
from recovery.strategy import RecoveryStrategy
from recovery.retry_policy import RetryPolicy
from loop_detection.detector import LoopDetector, LoopDetectedError
from events import EventBus, ALL_EVENTS, LOOP_DETECTED


class ErrorDetectorTests(unittest.TestCase):
    def setUp(self):
        self.d = ErrorDetector()

    def test_textual_categories(self):
        self.assertEqual(self.d.detect({"text": ["An error occurred"]}), ["VISIBLE_ERROR"])
        self.assertIn("NETWORK", self.d.detect({"text": ["connection failed, offline"]}))
        self.assertIn("SESSION_EXPIRED", self.d.detect({"text": ["please sign in again"]}))

    def test_previously_undetectable_structured_categories(self):
        self.assertIn("UNEXPECTED_DIALOG", self.d.detect({"text": [], "dialog_present": True}))
        self.assertIn("WRONG_WINDOW", self.d.detect({"text": [], "expected_window_id": "W1", "window_id": "W2"}))
        self.assertIn("FILE_CONFLICT", self.d.detect({"text": [], "file_conflict": True}))
        self.assertIn("TARGET_DISAPPEARED", self.d.detect({"text": [], "target_expected": True, "target_present": False}))

    def test_dialog_expected_suppresses_false_positive(self):
        self.assertNotIn("UNEXPECTED_DIALOG", self.d.detect({"text": [], "dialog_present": True, "dialog_expected": True}))


class FailureClassifierTests(unittest.TestCase):
    def test_all_ten_spec_classes_reachable(self):
        fc = FailureClassifier()
        mapping_inputs = ["LOADING_TIMEOUT", "UNEXPECTED_DIALOG", "PERMISSION", "WRONG_WINDOW",
                           "VISIBLE_ERROR", "NETWORK", "MODEL_UNCERTAINTY", "VERIFICATION_FAILURE",
                           "SECURITY_BLOCK", "totally-unknown-signal"]
        produced = {fc.classify(x) for x in mapping_inputs}
        self.assertEqual(produced, set(fc.ALL_CLASSES))


class RecoveryStrategyTests(unittest.TestCase):
    def test_partial_flag_changes_recommendation_where_applicable(self):
        rs = RecoveryStrategy()
        self.assertEqual(rs.recommend("TRANSIENT", partial=False), "RETRY_DIFFERENT_SAFE_STRATEGY")
        self.assertEqual(rs.recommend("TRANSIENT", partial=True), "RESUME_FROM_CHECKPOINT")

    def test_partial_flag_is_a_noop_for_classes_without_an_override(self):
        rs = RecoveryStrategy()
        self.assertEqual(rs.recommend("PERMISSION", partial=True), "STOP")

    def test_emits_recovery_recommended_event(self):
        bus = EventBus()
        rs = RecoveryStrategy(event_bus=bus)
        rs.recommend("NETWORK")
        self.assertEqual(bus.history[0]["event"], "RECOVERY_RECOMMENDED")


class RetryPolicyTests(unittest.TestCase):
    def test_bounded_retries(self):
        rp = RetryPolicy(3)
        self.assertTrue(rp.allowed(2))
        self.assertFalse(rp.allowed(3))


class LoopDetectorTests(unittest.TestCase):
    def test_raises_after_limit_and_is_a_runtime_error_subclass(self):
        d = LoopDetector(2)
        d.observe("a", "t", "s", "x")
        d.observe("a", "t", "s", "x")
        with self.assertRaises(LoopDetectedError):
            d.observe("a", "t", "s", "x")
        # backward compat: still catchable as bare RuntimeError with the old message pattern
        d2 = LoopDetector(1)
        d2.observe("a", "t", "s", "x")
        with self.assertRaisesRegex(RuntimeError, "LOOP_DETECTED"):
            d2.observe("a", "t", "s", "x")

    def test_emits_loop_detected_event(self):
        bus = EventBus()
        d = LoopDetector(1, event_bus=bus)
        d.observe("a", "t", "s", "x")
        with self.assertRaises(RuntimeError):
            d.observe("a", "t", "s", "x")
        self.assertEqual(bus.history[0]["event"], LOOP_DETECTED)

    def test_reset_clears_history(self):
        d = LoopDetector(1)
        d.observe("a", "t", "s", "x")
        d.reset()
        d.observe("a", "t", "s", "x")  # should not raise, history was cleared


class EventBusTests(unittest.TestCase):
    def test_rejects_unknown_event_names(self):
        bus = EventBus()
        with self.assertRaises(ValueError):
            bus.emit("NOT_A_REAL_EVENT")

    def test_subscribers_receive_emitted_events(self):
        bus = EventBus()
        received = []
        bus.subscribe(LOOP_DETECTED, received.append)
        bus.emit(LOOP_DETECTED, signature="abc")
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["signature"], "abc")

    def test_handler_exception_does_not_propagate(self):
        bus = EventBus()
        bus.subscribe(LOOP_DETECTED, lambda e: (_ for _ in ()).throw(RuntimeError("boom")))
        bus.emit(LOOP_DETECTED)  # must not raise

    def test_all_twelve_spec_events_defined(self):
        self.assertEqual(len(ALL_EVENTS), 12)


if __name__ == "__main__":
    unittest.main()
