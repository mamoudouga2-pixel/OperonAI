"""
Consent tracking for actions that require explicit user approval, e.g.
retaining a USER_APPROVED_INFERENCE memory permanently (spec 8.12, 8.13).
"""

import time


class Consent:
    def __init__(self):
        self.values = {}

    def grant(self, scope, reason=None):
        self.values[scope] = {"granted": True, "granted_at": time.time(), "reason": reason}

    def revoke(self, scope):
        self.values.pop(scope, None)

    def allowed(self, scope):
        entry = self.values.get(scope)
        return bool(entry and entry.get("granted"))
