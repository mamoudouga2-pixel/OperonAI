"""
Retention policy (spec 8.19 RETENTION POLICY).

    EPHEMERAL       -> task/session end or TTL
    TASK_RETENTION  -> configurable task-history period
    USER_CONTROLLED -> retained until user deletes
    EXPIRING        -> automatic deletion at expires_at
    SECURITY/AUDIT  -> separate policy-defined retention
"""

from datetime import datetime, timedelta, timezone

CLASSES_WITH_NO_INHERENT_TTL = {"USER_CONTROLLED"}


class RetentionPolicy:
    def __init__(self, task_history_days=30, audit_days=90):
        self.task_history_days = task_history_days
        self.audit_days = audit_days

    def expired(self, memory, now=None):
        """True if ``memory`` should be purged right now."""
        now = now or datetime.now(timezone.utc)
        expires_at = memory.get("expires_at")
        if expires_at:
            return self._parse(expires_at) <= now

        retention = memory.get("retention_policy")
        if retention in CLASSES_WITH_NO_INHERENT_TTL:
            return False
        if retention == "TASK_RETENTION":
            return self._older_than(memory, self.task_history_days, now)
        if retention == "SECURITY/AUDIT":
            return self._older_than(memory, self.audit_days, now)
        # EPHEMERAL/EXPIRING with no explicit expires_at is treated as
        # already eligible for cleanup - it should never have been
        # written without one.
        return retention in ("EPHEMERAL", "EXPIRING")

    def _older_than(self, memory, days, now):
        created_at = memory.get("created_at")
        if not created_at:
            return False
        return self._parse(created_at) <= now - timedelta(days=days)

    @staticmethod
    def _parse(ts):
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
