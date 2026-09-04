class RuleEngine:
    """Evaluates a caller-supplied predicate against current state.

    This is the escape hatch for postcondition checks that don't fit the
    declarative type/value shape in ``postcondition.py`` (spec 7.15's
    "Boolean conditions" is broad enough to include arbitrary logic).
    Wired into ``IndependentCheck.check_detailed`` via
    ``expected_state["custom_rules"]`` -- previously this class existed but
    nothing in the codebase ever called it.
    """

    def evaluate(self, fn, state):
        return bool(fn(state))
