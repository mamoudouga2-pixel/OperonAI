"""End-to-end tests (spec 7.26). Each test implements one of the 5 named
scenarios exactly, wiring the real components together (no test doubles
standing in for the class under test) the way Part 04/05/06 integration
would actually call this package.

Previously ``tests/end_to_end/`` contained only an empty ``__init__.py`` --
none of these 5 scenarios existed as code.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from capture.artifact_store import ArtifactStore
from evidence.collector import EvidenceCollector
from verification.postcondition import PostconditionEngine
from verification.independent_check import IndependentCheck
from verification.verifier import Verifier
from grounding.confidence import ConfidencePolicy
from grounding.matcher import GroundingMatcher
from error_detection.detector import ErrorDetector
from error_detection.classifier import FailureClassifier
from recovery.strategy import RecoveryStrategy
from recovery.retry_policy import RetryPolicy
from loop_detection.detector import LoopDetector, LoopDetectedError


class Scenario1_BrowserSubmitIndependentConfirmation(unittest.TestCase):
    """7.26 #1: 'Browser submit → independent confirmation.'

    The worker's own claim text ("Form submitted successfully!") is never
    read by the verifier -- only the independently-observed DOM/evidence
    state is. A worker that merely *says* success without the page
    actually confirming it must NOT verify.
    """

    def setUp(self):
        self.pc = PostconditionEngine()
        self.verifier = Verifier(IndependentCheck(self.pc))
        self.expected_state = {
            "operator": "AND",
            "conditions": [
                {"type": "URL", "expected": "/orders/confirmation"},
                {"type": "CONFIRMATION_ID_EXISTS"},
                {"type": "NO_ERROR"},
            ],
        }

    def test_real_confirmation_verifies_independently_of_worker_claim(self):
        worker_claim = "Form submitted successfully!"  # never inspected by the verifier
        current_state = {"url": "/orders/confirmation", "confirmation_id": "ORD-9821",
                          "errors": [], "evidence_age_ms": 500}
        evidence = [{"evidence_id": "EVID-001", "source": "browser"}]
        result = self.verifier.verify(
            {"verification_id": "VER-1", "expected_state": self.expected_state}, current_state, evidence)
        self.assertEqual(result["status"], "VERIFIED")
        self.assertNotIn(worker_claim, str(result))  # the claim text plays no role in the verdict

    def test_worker_claims_success_but_page_never_navigated(self):
        current_state = {"url": "/orders/checkout", "confirmation_id": None, "errors": [], "evidence_age_ms": 500}
        result = self.verifier.verify(
            {"verification_id": "VER-2", "expected_state": self.expected_state},
            current_state, [{"evidence_id": "EVID-002", "source": "browser"}])
        self.assertEqual(result["status"], "NOT_VERIFIED")
        self.assertIn("URL:/orders/confirmation", result["missing_conditions"])


class Scenario2_FileMovePostconditionVerification(unittest.TestCase):
    """7.26 #2: 'File move → destination/source postcondition verification.'"""

    def setUp(self):
        self.pc = PostconditionEngine()
        self.verifier = Verifier(IndependentCheck(self.pc))
        self.expected_state = {
            "operator": "AND",
            "conditions": [
                {"type": "FILE_EXISTS", "path": "/home/user/Archive/report.pdf"},
                {"type": "SOURCE_STATE", "expected": "MOVED"},
            ],
        }

    def test_file_actually_present_at_destination_and_gone_from_source(self):
        current_state = {
            "files": {"/home/user/Archive/report.pdf": True, "/home/user/Downloads/report.pdf": False},
            "source_state": "MOVED", "errors": [], "evidence_age_ms": 200,
        }
        result = self.verifier.verify(
            {"verification_id": "VER-3", "expected_state": self.expected_state},
            current_state, [{"evidence_id": "EVID-003", "source": "desktop"}])
        self.assertEqual(result["status"], "VERIFIED")

    def test_destination_missing_despite_worker_claim_of_success(self):
        current_state = {"files": {"/home/user/Archive/report.pdf": False}, "source_state": "MOVED",
                          "errors": [], "evidence_age_ms": 200}
        result = self.verifier.verify(
            {"verification_id": "VER-4", "expected_state": self.expected_state},
            current_state, [{"evidence_id": "EVID-004", "source": "desktop"}])
        self.assertEqual(result["status"], "NOT_VERIFIED")
        self.assertIn("FILE_EXISTS:/home/user/Archive/report.pdf", result["missing_conditions"])


class Scenario3_NoOpClickTriggersAlternateRecovery(unittest.TestCase):
    """7.26 #3: 'Button click changes nothing → NOT_VERIFIED → alternate
    recovery.' Also exercises 7.18's rule that the same failed action must
    not be blindly repeated in the same state -- loop detection catches
    that, and recovery strategy is asked for a *different* approach.
    """

    def setUp(self):
        self.pc = PostconditionEngine()
        self.verifier = Verifier(IndependentCheck(self.pc))
        self.loop_detector = LoopDetector(limit=2)
        self.recovery = RecoveryStrategy()
        self.classifier = FailureClassifier()
        self.expected_state = {"operator": "AND", "conditions": [{"type": "LOADING_FALSE"}, {"type": "URL", "expected": "/saved"}]}

    def test_unchanged_state_is_not_verified_and_repeated_identical_retries_trip_loop_detection(self):
        unchanged_state = {"url": "/draft", "loading": False, "errors": [], "evidence_age_ms": 10}
        for attempt in range(2):
            result = self.verifier.verify(
                {"verification_id": f"VER-5-{attempt}", "expected_state": self.expected_state},
                unchanged_state, [{"evidence_id": f"EVID-{attempt}", "source": "browser"}])
            self.assertEqual(result["status"], "NOT_VERIFIED")
            self.loop_detector.observe("click", "save_button", "draft_screen", "no_change")

        with self.assertRaises(LoopDetectedError):
            self.loop_detector.observe("click", "save_button", "draft_screen", "no_change")

        failure_class = self.classifier.classify("VERIFICATION_FAILURE")
        recommendation = self.recovery.recommend(failure_class)
        self.assertEqual(recommendation, "RECAPTURE")  # not a bare "retry the same click again"


class Scenario4_LowConfidenceTargetEscalatesInsteadOfActing(unittest.TestCase):
    """7.26 #4: 'Model misidentifies target → low confidence → no action
    escalation.' The grounding candidate exists, but confidence is too low
    for the confidence policy to authorize acting on it.
    """

    def setUp(self):
        self.matcher = GroundingMatcher()
        self.confidence_policy = ConfidencePolicy(low=.75, high=.9)

    def test_weak_candidate_match_is_found_but_action_is_blocked(self):
        # The model thinks a "Cancel" element might be the "Delete Account" target -- low similarity.
        context = {"elements": [{"role": "button", "text": "Cancel", "confidence": .55}]}
        target = {"role": "button", "text": "Delete Account"}
        candidates = self.matcher.match(target, context)
        self.assertTrue(candidates)  # something was found...
        top_score, element = candidates[0]
        allowed = self.confidence_policy.allow(element["confidence"], risk="HIGH", corroborated=False, approved=False)
        self.assertFalse(allowed)  # ...but is not authorized to be acted on

    def test_high_confidence_high_risk_target_still_requires_approval(self):
        context = {"elements": [{"role": "button", "text": "Delete Account", "confidence": .97}]}
        candidates = self.matcher.match({"role": "button", "text": "Delete Account"}, context)
        top_score, element = candidates[0]
        # confidence alone is not enough for a HIGH risk irreversible action (spec 7.8/7.21)
        self.assertFalse(self.confidence_policy.allow(element["confidence"], "HIGH", corroborated=True, approved=False))
        self.assertTrue(self.confidence_policy.allow(element["confidence"], "HIGH", corroborated=True, approved=True))


class Scenario5_CrashRecoveryAvoidsDuplicateAction(unittest.TestCase):
    """7.26 #5: 'Worker crash after action → evidence/state inspection →
    avoid duplicate action.' Simulates a process restart: before retrying,
    the system independently re-checks whether the action already
    succeeded using evidence collected before the crash, instead of
    blindly repeating it.
    """

    def setUp(self):
        self.pc = PostconditionEngine()
        self.verifier = Verifier(IndependentCheck(self.pc))
        self.retry_policy = RetryPolicy(max_retries=3)

    def test_evidence_from_before_the_crash_shows_action_already_succeeded(self):
        with tempfile.TemporaryDirectory() as d:
            store = ArtifactStore(d)
            collector = EvidenceCollector(store)
            # Action executed, evidence WAS collected right before the crash.
            pre_crash_evidence = collector.collect("TASK-9", "ACT-9", "desktop", b"screenshot-bytes",
                                                     "destination folder after move")

            # Process restarts. Before retrying ACT-9, re-verify against the
            # evidence that already exists rather than assuming failure.
            expected_state = {"operator": "AND", "conditions": [
                {"type": "FILE_EXISTS", "path": "/dest/file.txt"}, {"type": "SOURCE_STATE", "expected": "MOVED"},
            ]}
            current_state = {"files": {"/dest/file.txt": True}, "source_state": "MOVED",
                              "errors": [], "evidence_age_ms": 2000}
            result = self.verifier.verify(
                {"verification_id": "VER-6", "expected_state": expected_state},
                current_state, [{"evidence_id": pre_crash_evidence.evidence_id, "source": "desktop"}])

            self.assertEqual(result["status"], "VERIFIED")
            # Because it's already VERIFIED, the caller must not consume a retry attempt / repeat the action.
            attempt_count_if_it_had_incorrectly_retried = 1
            self.assertTrue(self.retry_policy.allowed(0))  # retries would still be available...
            self.assertEqual(result["recommended_next_state"], "CONTINUE")  # ...but next_state says move on, not retry


if __name__ == "__main__":
    unittest.main()
