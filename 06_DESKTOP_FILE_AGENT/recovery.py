from errors import E, RETRYABLE


class RetryPolicy:
    RETRYABLE = RETRYABLE

    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    def can_retry(self, error, attempt):
        return error in self.RETRYABLE and attempt < self.max_retries


class LoopDetector:
    """Tracks (action signature, resource-state signature) pairs; the same
    action repeated against the same state past `limit` times means the
    agent is stuck, not making progress — stop instead of looping forever."""

    def __init__(self, limit=3):
        self.limit = limit
        self.seen = {}

    def observe(self, action, state):
        k = (action, state)
        self.seen[k] = self.seen.get(k, 0) + 1
        if self.seen[k] > self.limit:
            raise RuntimeError(E.LOOP_DETECTED)
        return self.seen[k]


class Recovery:
    """6.27 RECOVERY — Failure -> classify -> re-check state -> bounded
    retry -> verify -> escalate if unresolved.

    `op()` performs one attempt and returns the result.
    `state_fn()` returns a hashable snapshot of the resource state, used
    both for the loop detector's signature and to detect that a previous
    attempt already partially completed (so `op` should itself be written
    idempotently, e.g. FileAgent.move_idempotent).
    """

    def __init__(self, retry_policy=None, loop_detector=None):
        self.retry = retry_policy or RetryPolicy()
        self.loop = loop_detector or LoopDetector()

    def run(self, action_signature, op, state_fn=lambda: None, verify=lambda result: True):
        attempt = 0
        while True:
            state = state_fn()
            self.loop.observe(action_signature, state)
            try:
                result = op()
            except RuntimeError as ex:
                code = str(ex)
                if not self.retry.can_retry(code, attempt):
                    raise
                attempt += 1
                continue
            if not verify(result):
                raise RuntimeError(E.VERIFICATION_REQUIRED)
            return result
