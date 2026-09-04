from events import default_bus, RECOVERY_RECOMMENDED


class RecoveryStrategy:
    """Recovery recommendation (spec 7.18).

    The ``partial`` flag was previously accepted but never read -- 7.18
    explicitly calls for determining partial completion *before* choosing
    a strategy, so a partially-completed action now prefers a
    reconcile/resume style recommendation over a blind full retry/replan
    where that distinction is meaningful.
    """

    BASE = {
        "TRANSIENT": "RETRY_DIFFERENT_SAFE_STRATEGY",
        "CONFLICT": "REPLAN",
        "PERMISSION": "STOP",
        "TARGET_NOT_FOUND": "REGROUND",
        "WRONG_STATE": "REPLAN",
        "NETWORK": "RETRY",
        "MODEL_UNCERTAINTY": "STOP",
        "VERIFICATION_FAILURE": "RECAPTURE",
        "SECURITY_BLOCK": "STOP",
        "UNKNOWN": "ESCALATE",
    }

    # Overrides that only apply when the action partially completed --
    # these classes have a meaningfully different safe strategy when some
    # of the work already happened vs. when nothing happened at all.
    PARTIAL_OVERRIDES = {
        "TRANSIENT": "RESUME_FROM_CHECKPOINT",
        "CONFLICT": "RECONCILE_PARTIAL_STATE",
        "WRONG_STATE": "RECONCILE_PARTIAL_STATE",
        "VERIFICATION_FAILURE": "RECAPTURE_AND_RECONCILE",
    }

    def __init__(self, event_bus=None):
        self.event_bus = event_bus or default_bus

    def recommend(self, failure, partial=False):
        recommendation = (
            self.PARTIAL_OVERRIDES.get(failure) if partial else None
        ) or self.BASE.get(failure, "ESCALATE")
        self.event_bus.emit(RECOVERY_RECOMMENDED, failure=failure, partial=partial, recommendation=recommendation)
        return recommendation
