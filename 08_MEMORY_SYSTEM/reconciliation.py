"""
Reconciliation job (spec 8.27 CONSISTENCY).

"A write/delete that fails midway must be detected and reconciled by a
reconciliation job, since distributed transactions across multiple
stores cannot be assumed."
"""

import time


class ReconciliationLog:
    """Durable-ish (in-memory here) record of partial failures, so a
    background job can retry or surface them for manual review."""

    def __init__(self):
        self._entries = []

    def record(self, entry):
        entry = dict(entry)
        entry.setdefault("recorded_at", time.time())
        entry.setdefault("resolved", False)
        self._entries.append(entry)
        return entry

    def pending(self):
        return [e for e in self._entries if not e["resolved"]]

    def resolve(self, memory_id, store):
        for entry in self._entries:
            if entry.get("memory_id") == memory_id and entry.get("store") == store:
                entry["resolved"] = True


class ReconciliationJob:
    """Retries pending failed store operations using the same
    idempotent delete/upsert functions that failed originally."""

    def __init__(self, log, stores):
        self.log = log
        self.stores = stores  # store_name -> callable(memory_id)

    def run(self):
        resolved, still_failing = [], []
        for entry in self.log.pending():
            fn = self.stores.get(entry["store"])
            if fn is None:
                still_failing.append(entry)
                continue
            try:
                fn(entry["memory_id"])
                self.log.resolve(entry["memory_id"], entry["store"])
                resolved.append(entry)
            except Exception:
                still_failing.append(entry)
        return {"resolved": resolved, "still_failing": still_failing}
