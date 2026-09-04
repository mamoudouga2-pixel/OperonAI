import hashlib
import itertools
from datetime import datetime, timezone


class EvidenceStore:
    """Collects immutable evidence records for actions and observations."""

    def __init__(self):
        self._counter = itertools.count(1)
        self.records = {}

    def create(self, kind, target_ref=None, result_ref=None, content_hash=None):
        eid = f"EVID-{next(self._counter):03d}"
        rec = {
            "evidence_id": eid,
            "kind": kind,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_ref": target_ref,
            "result_ref": result_ref,
            "hash": content_hash,
        }
        self.records[eid] = rec
        return rec

    @staticmethod
    def hash_file(path):
        """SHA-256 of a file's bytes, used as the immutable reference (6.21)."""
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
