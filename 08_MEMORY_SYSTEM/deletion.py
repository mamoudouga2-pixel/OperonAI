"""
Coordinated cross-store deletion (spec 8.20, 8.21, 8.27 CONSISTENCY).

"Distributed transactions across multiple stores cannot be assumed;
write/delete workflows must be idempotent and compensating-recovery
aware." DeletionCoordinator runs every store's delete function for
every id, tracks partial failures, and hands them to the reconciliation
job rather than silently swallowing them.
"""

from errors import DeletePartial


class DeletionCoordinator:
    def __init__(self, reconciliation_log=None):
        self.reconciliation_log = reconciliation_log

    def delete(self, ids, stores):
        """``stores``: dict of store_name -> callable(id).

        Deletion is attempted against every store for every id even if
        one store fails, so a single bad backend doesn't leave the
        others out of sync more than necessary. Failures are collected
        and raised together as DELETE_PARTIAL.
        """
        failed = []
        for name, delete_fn in stores.items():
            for memory_id in ids:
                try:
                    delete_fn(memory_id)
                except Exception as exc:  # noqa: BLE001 - any backend error counts
                    failed.append({"store": name, "memory_id": memory_id, "error": str(exc)})

        if failed:
            if self.reconciliation_log is not None:
                for entry in failed:
                    self.reconciliation_log.record(entry)
            raise DeletePartial(f"{len(failed)} deletion(s) failed", failures=failed)
        return True
