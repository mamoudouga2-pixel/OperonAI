import time
from pathlib import Path


class RetentionPolicy:
    """Artifact retention (spec 7.11: 'Artifact retention policy Part 08/09-এর
    সঙ্গে সামঞ্জস্যপূর্ণ হবে' -- consistent with Part 08/09's policy).

    The previous version only exposed a bare age comparison with no way to
    actually enforce it. ``sweep`` performs real deletion of expired
    artifacts from an ``ArtifactStore``-backed directory, and is the piece
    Part 08/09 integration can call on a schedule.
    """

    def __init__(self, max_age_ms):
        self.max_age_ms = max_age_ms

    def allowed(self, age_ms, max_age_ms=None):
        limit = self.max_age_ms if max_age_ms is None else max_age_ms
        return age_ms <= limit

    def sweep(self, store, now_ms=None):
        """Delete artifacts under ``store.root`` older than max_age_ms.
        Returns the list of deleted filenames."""
        now_ms = now_ms if now_ms is not None else time.time() * 1000
        deleted = []
        root = Path(store.root)
        for path in root.glob("*"):
            if not path.is_file():
                continue
            age_ms = now_ms - path.stat().st_mtime * 1000
            if not self.allowed(age_ms):
                store.delete(path.name)
                deleted.append(path.name)
        return deleted
