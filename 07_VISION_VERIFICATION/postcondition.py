"""Postcondition engine (spec 7.15).

Supports the condition types the spec lists explicitly (boolean, expected
text/value, URL/window/application state, file existence, DOM property,
visual confirmation) plus AND/OR composition. Composition is now genuinely
recursive -- a "condition" entry may itself be a nested {"operator":...,
"conditions":[...]} group, not just a flat leaf -- so callers can express
(A AND B) OR (C AND D), which the previous flat-only version could not
represent at all.

``check_detailed`` additionally returns *which* leaf conditions failed
(spec 7.13's ``missing_conditions`` output field needs real content, not a
constant placeholder), and unknown condition types are reported distinctly
from conditions that were evaluated and failed, instead of silently
counting as "failed" with no way to tell a typo from a real mismatch.
"""


class UnknownConditionType(Exception):
    def __init__(self, condition_type):
        super().__init__(f"unknown postcondition type: {condition_type!r}")
        self.condition_type = condition_type


class PostconditionEngine:
    LEAF_CHECKS = (
        "FILE_EXISTS", "SOURCE_STATE", "EXPECTED_TEXT", "URL", "WINDOW",
        "NO_ERROR", "LOADING_FALSE", "DOM_STATE", "VISUAL_CONFIRMATION",
        "CONFIRMATION_ID_EXISTS", "RECORD_EXISTS", "BOOL",
    )

    def check(self, conditions, state):
        """Backward-compatible boolean-only entry point."""
        ok, _missing = self.check_detailed(conditions, state)
        return ok

    def check_detailed(self, conditions, state):
        """Returns (overall_bool, [missing_condition_descriptions])."""
        return self._eval_group(conditions, state)

    def _eval_group(self, group, state):
        op = group.get("operator", "AND")
        results = []
        missing = []
        for c in group.get("conditions", []):
            if "operator" in c and "conditions" in c:
                ok, sub_missing = self._eval_group(c, state)
                results.append(ok)
                if not ok:
                    missing.extend(sub_missing)
            else:
                ok = self.one(c, state)
                results.append(ok)
                if not ok:
                    missing.append(self._describe(c))
        overall = all(results) if op == "AND" else any(results) if results else True
        # For OR groups that pass, don't report sibling failures as missing.
        if op == "OR" and overall:
            missing = []
        return overall, missing

    def one(self, c, s):
        t = c.get("type")
        if t == "FILE_EXISTS":
            return bool(s.get("files", {}).get(c["path"], False))
        if t == "SOURCE_STATE":
            return s.get("source_state") == c.get("expected")
        if t == "EXPECTED_TEXT":
            return c.get("expected") in s.get("text", [])
        if t == "URL":
            return s.get("url") == c.get("expected")
        if t == "WINDOW":
            return s.get("window_id") == c.get("expected")
        if t == "NO_ERROR":
            return not s.get("errors")
        if t == "LOADING_FALSE":
            return s.get("loading") is False
        if t == "DOM_STATE":
            # e.g. {"type":"DOM_STATE","selector":"#status","property":"innerText","expected":"Saved"}
            dom = s.get("dom", {})
            node = dom.get(c.get("selector"), {})
            return node.get(c.get("property")) == c.get("expected")
        if t == "VISUAL_CONFIRMATION":
            # e.g. {"type":"VISUAL_CONFIRMATION","role":"button","text":"Success","min_confidence":0.8}
            min_conf = c.get("min_confidence", 0.75)
            for element in s.get("elements", []):
                role_ok = (c.get("role") is None) or element.get("role") == c.get("role")
                text_ok = (c.get("text") is None) or element.get("text") == c.get("text")
                if role_ok and text_ok and element.get("confidence", 0) >= min_conf:
                    return True
            return False
        if t == "CONFIRMATION_ID_EXISTS":
            return bool(s.get("confirmation_id"))
        if t == "RECORD_EXISTS":
            return c.get("record_id") in s.get("records", [])
        if t == "BOOL":
            return bool(s.get(c.get("key")))
        raise UnknownConditionType(t)

    def _describe(self, c):
        t = c.get("type", "UNKNOWN")
        detail = c.get("expected", c.get("path", c.get("text", "")))
        return f"{t}:{detail}" if detail not in (None, "") else t
