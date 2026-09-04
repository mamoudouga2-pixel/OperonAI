import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from grounding.matcher import GroundingMatcher
from grounding.confidence import ConfidencePolicy
from grounding.candidate import Candidate


class GroundingMatcherTests(unittest.TestCase):
    def setUp(self):
        self.gm = GroundingMatcher()

    def test_exact_match_scores_highest(self):
        ctx = {"elements": [{"role": "button", "text": "Submit"}]}
        result = self.gm.match({"role": "button", "text": "Submit"}, ctx)
        self.assertAlmostEqual(result[0][0], 0.65)

    def test_fuzzy_text_still_matches_reasonably(self):
        ctx = {"elements": [{"role": "button", "text": "Submit Form"}]}
        result = self.gm.match({"role": "button", "text": "Submit"}, ctx)
        self.assertGreater(result[0][0], 0.5)

    def test_surrounding_context_and_task_context_contribute(self):
        ctx = {"elements": [{"role": "button", "text": "OK"}],
               "surrounding_text": ["Are you sure?"], "task_context": "confirm_delete"}
        target = {"role": "button", "text": "OK", "nearby_text": "Are you sure?", "task_context": "confirm_delete"}
        result = self.gm.match(target, ctx)
        self.assertAlmostEqual(result[0][0], 0.35 + 0.30 + 0.15 + 0.10)

    def test_coordinate_only_fallback_picks_smallest_containing_box(self):
        elements = [
            {"bounding_box": {"x": 0, "y": 0, "width": 500, "height": 500}},
            {"bounding_box": {"x": 10, "y": 10, "width": 40, "height": 20}},
        ]
        hit = self.gm.ground_by_coordinates(20, 20, elements)
        self.assertEqual(hit, elements[1])

    def test_coordinate_fallback_returns_none_when_nothing_contains_point(self):
        elements = [{"bounding_box": {"x": 0, "y": 0, "width": 10, "height": 10}}]
        self.assertIsNone(self.gm.ground_by_coordinates(500, 500, elements))


class ConfidencePolicyTests(unittest.TestCase):
    def test_low_risk_only_needs_threshold(self):
        cp = ConfidencePolicy(low=.75, high=.9)
        self.assertTrue(cp.allow(.8, "LOW"))
        self.assertFalse(cp.allow(.5, "LOW"))

    def test_high_risk_needs_corroboration_and_approval(self):
        cp = ConfidencePolicy(low=.75, high=.9)
        self.assertFalse(cp.allow(.99, "HIGH", corroborated=True, approved=False))
        self.assertFalse(cp.allow(.99, "HIGH", corroborated=False, approved=True))
        self.assertTrue(cp.allow(.99, "HIGH", corroborated=True, approved=True))

    def test_unknown_risk_level_fails_closed_as_high_not_open_as_low(self):
        cp = ConfidencePolicy(low=.75, high=.9)
        self.assertFalse(cp.allow(.99, "TYPO", corroborated=True, approved=False))
        self.assertTrue(cp.allow(.99, "TYPO", corroborated=True, approved=True))

    def test_backward_compatible_positional_constructor(self):
        cp = ConfidencePolicy(.75, .9)
        self.assertEqual(cp.low, .75)
        self.assertEqual(cp.high, .9)


class CandidateTests(unittest.TestCase):
    def test_dataclass_fields(self):
        c = Candidate(role="button", text="OK", bounding_box={"x": 0, "y": 0, "width": 1, "height": 1}, confidence=.9)
        self.assertIsNone(c.window_id)


if __name__ == "__main__":
    unittest.main()
