import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from verification.postcondition import PostconditionEngine, UnknownConditionType
from verification.independent_check import IndependentCheck
from verification.verifier import Verifier
from verification.rule_engine import RuleEngine


def base_request(expected_state=None, **extra):
    req = {
        "verification_id": "VER-001", "task_id": "TASK-001", "action_id": "ACT-001",
        "claim": "Form submitted",
        "expected_state": expected_state or {
            "operator": "AND",
            "conditions": [{"type": "EXPECTED_TEXT", "expected": "Success"}, {"type": "NO_ERROR"}, {"type": "LOADING_FALSE"}],
        },
    }
    req.update(extra)
    return req


class PostconditionEngineTests(unittest.TestCase):
    def setUp(self):
        self.pc = PostconditionEngine()

    def test_nested_or_of_and_groups(self):
        nested = {"operator": "OR", "conditions": [
            {"operator": "AND", "conditions": [{"type": "URL", "expected": "/a"}, {"type": "NO_ERROR"}]},
            {"operator": "AND", "conditions": [{"type": "URL", "expected": "/b"}, {"type": "NO_ERROR"}]},
        ]}
        self.assertTrue(self.pc.check(nested, {"url": "/b", "errors": []}))
        self.assertFalse(self.pc.check(nested, {"url": "/c", "errors": []}))

    def test_missing_conditions_names_the_real_failures(self):
        ok, missing = self.pc.check_detailed(
            {"operator": "AND", "conditions": [{"type": "EXPECTED_TEXT", "expected": "Success"}, {"type": "NO_ERROR"}]},
            {"text": [], "errors": ["bad"]},
        )
        self.assertFalse(ok)
        self.assertEqual(set(missing), {"EXPECTED_TEXT:Success", "NO_ERROR"})

    def test_new_condition_types(self):
        self.assertTrue(self.pc.one({"type": "VISUAL_CONFIRMATION", "role": "button", "text": "Success", "min_confidence": .8},
                                     {"elements": [{"role": "button", "text": "Success", "confidence": .92}]}))
        self.assertTrue(self.pc.one({"type": "CONFIRMATION_ID_EXISTS"}, {"confirmation_id": "C1"}))
        self.assertFalse(self.pc.one({"type": "CONFIRMATION_ID_EXISTS"}, {}))
        self.assertTrue(self.pc.one({"type": "RECORD_EXISTS", "record_id": "R1"}, {"records": ["R1"]}))
        self.assertTrue(self.pc.one({"type": "DOM_STATE", "selector": "#s", "property": "innerText", "expected": "Saved"},
                                     {"dom": {"#s": {"innerText": "Saved"}}}))

    def test_unknown_condition_type_raises_distinctly(self):
        with self.assertRaises(UnknownConditionType):
            self.pc.one({"type": "TYPO"}, {})


class VerifierStateTests(unittest.TestCase):
    def setUp(self):
        self.pc = PostconditionEngine()
        self.v = Verifier(IndependentCheck(self.pc))

    def test_verified(self):
        r = self.v.verify(base_request(), {"text": ["Success"], "errors": [], "loading": False, "evidence_age_ms": 1},
                           [{"evidence_id": "E1"}])
        self.assertEqual(r["status"], "VERIFIED")
        self.assertEqual(r["missing_conditions"], [])

    def test_not_verified_reports_real_missing_conditions(self):
        r = self.v.verify(base_request(), {"text": [], "errors": [], "loading": False, "evidence_age_ms": 1},
                           [{"evidence_id": "E1"}])
        self.assertEqual(r["status"], "NOT_VERIFIED")
        self.assertIn("EXPECTED_TEXT:Success", r["missing_conditions"])

    def test_uncertain_no_evidence(self):
        r = self.v.verify(base_request(), {}, [])
        self.assertEqual(r["status"], "UNCERTAIN")

    def test_uncertain_stale_by_clock(self):
        r = self.v.verify(base_request(), {"text": ["Success"], "errors": [], "loading": False, "evidence_age_ms": 99999},
                           [{"evidence_id": "E1"}])
        self.assertEqual(r["status"], "UNCERTAIN")
        self.assertEqual(r["recommended_next_state"], "RECAPTURE")

    def test_uncertain_stale_by_action_ordering(self):
        r = self.v.verify(base_request(),
                           {"text": ["Success"], "errors": [], "loading": False, "evidence_age_ms": 1,
                            "action_occurred_after_evidence": True},
                           [{"evidence_id": "E1"}])
        self.assertEqual(r["status"], "UNCERTAIN")

    def test_uncertain_timeout(self):
        r = self.v.verify(base_request(),
                           {"text": ["Success"], "errors": [], "loading": False, "evidence_age_ms": 1, "processing_ms": 999999},
                           [{"evidence_id": "E1"}])
        self.assertEqual(r["status"], "UNCERTAIN")
        self.assertIn("timeout", r["reason"].lower())

    def test_blocked_high_risk_without_corroboration_or_approval(self):
        req = base_request(risk="HIGH", sources=["desktop", "browser"])
        r = self.v.verify(req, {"text": ["Success"], "errors": [], "loading": False, "evidence_age_ms": 1, "confidence": .95},
                           [{"evidence_id": "E1", "source": "desktop"}])
        self.assertEqual(r["status"], "BLOCKED")
        self.assertIn("multi_source_corroboration", r["missing_conditions"])
        self.assertIn("human_approval", r["missing_conditions"])

    def test_verified_high_risk_with_corroboration_and_approval(self):
        req = base_request(risk="HIGH", sources=["desktop", "browser"])
        r = self.v.verify(req, {"text": ["Success"], "errors": [], "loading": False, "evidence_age_ms": 1,
                                 "confidence": .95, "approved": True},
                           [{"evidence_id": "E1", "source": "desktop"}, {"evidence_id": "E2", "source": "browser"}])
        self.assertEqual(r["status"], "VERIFIED")

    def test_error_state_on_invalid_condition_type(self):
        req = base_request(expected_state={"operator": "AND", "conditions": [{"type": "NOT_A_REAL_TYPE"}]})
        r = self.v.verify(req, {"evidence_age_ms": 1}, [{"evidence_id": "E1"}])
        self.assertEqual(r["status"], "ERROR")

    def test_uncertain_is_never_treated_as_success(self):
        r = self.v.verify(base_request(), {}, [])
        self.assertNotEqual(r["status"], "VERIFIED")


class RuleEngineIntegrationTests(unittest.TestCase):
    def test_custom_rule_can_fail_verification_even_when_postconditions_pass(self):
        pc = PostconditionEngine()
        checker = IndependentCheck(pc, rule_engine=RuleEngine())
        v = Verifier(checker)
        req = base_request(expected_state={
            "operator": "AND",
            "conditions": [{"type": "NO_ERROR"}],
            "custom_rules": {"amount_matches": lambda s: s.get("amount") == 42},
        })
        r = v.verify(req, {"errors": [], "amount": 41, "evidence_age_ms": 1}, [{"evidence_id": "E1"}])
        self.assertEqual(r["status"], "NOT_VERIFIED")
        self.assertIn("CUSTOM_RULE:amount_matches", r["missing_conditions"])


if __name__ == "__main__":
    unittest.main()
