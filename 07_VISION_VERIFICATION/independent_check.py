class IndependentCheck:
    """Thin seam between Verifier and PostconditionEngine (spec 7.12):
    kept as its own class so a caller can substitute a different independent
    check strategy without touching Verifier."""

    def __init__(self, postconditions, rule_engine=None):
        self.postconditions = postconditions
        self.rule_engine = rule_engine

    def check(self, expected_state, current_state):
        return self.postconditions.check(expected_state, current_state)

    def check_detailed(self, expected_state, current_state):
        ok, missing = self.postconditions.check_detailed(expected_state, current_state)
        if ok and self.rule_engine is not None:
            for name, fn in (expected_state.get("custom_rules") or {}).items():
                if not self.rule_engine.evaluate(fn, current_state):
                    ok = False
                    missing.append(f"CUSTOM_RULE:{name}")
        return ok, missing
