"""
Cleanup pass (spec 8.19, 8.26 FAILURE RECOVERY).

Backs up anything it's about to delete first, so a bad policy run is
recoverable rather than destructive.
"""


class Cleanup:
    def __init__(self, backup=None):
        self.backup = backup

    def run(self, records, policy):
        """Return the surviving records; anything expired is dropped
        (and backed up first, if a Backup instance was supplied)."""
        survivors = []
        expired = []
        for record in records:
            if policy.expired(record):
                expired.append(record)
            else:
                survivors.append(record)

        if expired and self.backup is not None:
            self.backup.dump({"expired_at_cleanup": expired}, self.backup.default_path())

        return survivors

    def expired_ids(self, records, policy):
        return [r["memory_id"] for r in records if policy.expired(r)]
