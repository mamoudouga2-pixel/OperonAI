from errors import E


class SecurityGate:
    def __init__(self, apps):
        # app_id -> trusted, pre-resolved executable/launch path. Never a
        # path supplied directly by model output (6.15).
        self.apps = dict(apps)

    def application(self, app_id):
        if app_id not in self.apps:
            raise RuntimeError(E.APPLICATION_NOT_FOUND)
        return self.apps[app_id]

    def delete(self, approval):
        """6.14 DELETE POLICY — Version 1 has no destructive-delete feature.

        Even an "APPROVED" token does not execute a delete; it only changes
        *why* the request is blocked (missing approval vs. feature not
        implemented in V1). Real reversible/recycle-bin delete is deferred
        to a later version behind Part 09 Security + explicit user approval.
        """
        if approval != "APPROVED":
            raise RuntimeError(E.DELETE_BLOCKED)
        raise RuntimeError(E.DELETE_BLOCKED)
