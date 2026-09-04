import json

from errors import E


class WorkflowRecorder:
    def __init__(self):
        self.steps = []

    def record(self, step):
        self.steps.append(dict(step))

    def build(self, preconditions, expected_final, verification_rules):
        return {
            "environment_preconditions": preconditions,
            "steps": self.steps[:],
            "expected_final_state": expected_final,
            "verification_rules": verification_rules,
        }


class WorkflowSerializer:
    @staticmethod
    def dumps(workflow):
        return json.dumps(workflow, sort_keys=True)

    @staticmethod
    def loads(text):
        return json.loads(text)


class ReplayValidator:
    """6.26 — a recorded workflow may never be blindly replayed."""

    def validate(self, w, current):
        pre = w.get("environment_preconditions", {})
        for k, v in pre.items():
            if current.get(k) != v:
                raise RuntimeError(E.WORKFLOW_REPLAY_UNSAFE)
        return True

    def validate_step(self, step, current_target_state):
        """Re-check a single step's target/precondition before executing it
        again, and refuse to blindly re-run a non-idempotent step whose
        target no longer matches what was recorded."""
        if step.get("idempotent", True):
            return True
        expected = step.get("expected_precondition")
        if expected is not None and current_target_state != expected:
            raise RuntimeError(E.WORKFLOW_REPLAY_UNSAFE)
        return True
