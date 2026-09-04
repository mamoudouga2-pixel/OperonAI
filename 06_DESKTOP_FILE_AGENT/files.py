import errno
import os
import shutil
from pathlib import Path

from errors import E
from evidence import EvidenceStore

_INVALID_NAME_PARTS = {"", ".", ".."}


def _valid_name(name):
    return name not in _INVALID_NAME_PARTS and "/" not in name and chr(92) not in name


class FileAgent:
    def __init__(self, policy, max_items=10000, max_depth=8, evidence=None, is_locked=None):
        self.p = policy
        self.max_items = max_items
        self.max_depth = max_depth
        self.evidence = evidence or EvidenceStore()
        # Pluggable lock-detection hook: real lock detection is OS/API specific
        # (Windows share-violation, flock on POSIX, etc). Tests/adapters can
        # inject a real implementation; default assumes nothing is locked.
        self._is_locked = is_locked or (lambda path: False)

    # ---------------------------------------------------------- scanning --
    def scan(self, root):
        """6.8 FILE SCANNING — bounded, restricted-subtree-pruning walk."""
        b = self.p.validate(root, True)
        out = []
        base = len(b.parts)
        try:
            for cur, dirs, fs in os.walk(b, followlinks=False):
                cur_path = Path(cur)
                depth = len(cur_path.parts) - base
                if depth >= self.max_depth:
                    dirs[:] = []
                listed = list(dirs) + fs
                # 6.9: never descend into a restricted subtree, even if it
                # lives underneath an otherwise-allowed root. The entry
                # itself is still listed above (visible), just not walked.
                dirs[:] = [d for d in dirs if not self.p.is_restricted(cur_path / d)]
                for n in listed:
                    q = cur_path / n
                    out.append({
                        "path": str(q.resolve(strict=False)),
                        "name": n,
                        "is_dir": q.is_dir(),
                    })
                    if len(out) >= self.max_items:
                        return out
        except PermissionError:
            raise RuntimeError(E.PERMISSION_DENIED)
        return out

    # -------------------------------------------------------------- misc --
    def mkdir(self, parent, name):
        if not _valid_name(name):
            raise RuntimeError(E.PATH_NOT_ALLOWED)
        p = self.p.validate(parent, True)
        q = self.p.validate(p / name)
        if q.exists():
            raise RuntimeError(E.DESTINATION_EXISTS)
        try:
            q.mkdir()
        except PermissionError:
            raise RuntimeError(E.PERMISSION_DENIED)
        return q

    def _target(self, x):
        return self.p.validate(x, True)

    @staticmethod
    def _fingerprint(p):
        st = p.stat()
        return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)

    def _check_not_locked(self, p):
        if self._is_locked(p):
            raise RuntimeError(E.FILE_LOCKED)

    def _check_unchanged(self, p, fingerprint):
        """6.23 CONFLICT DETECTION — source changed after planning."""
        if not p.exists() or self._fingerprint(p) != fingerprint:
            raise RuntimeError(E.SOURCE_CHANGED)

    # -------------------------------------------------------------- copy --
    def copy(self, source, destination, expected_fingerprint=None):
        s = self._target(source)
        self._check_not_locked(s)
        if expected_fingerprint is not None:
            self._check_unchanged(s, expected_fingerprint)
        d = self.p.validate(destination)
        if d.exists() and not self.p.allow_overwrite:
            raise RuntimeError(E.DESTINATION_EXISTS)
        if not d.parent.exists():
            raise RuntimeError(E.FILE_NOT_FOUND)
        try:
            shutil.copy2(s, d)
        except PermissionError:
            raise RuntimeError(E.PERMISSION_DENIED)
        except OSError as ex:
            if ex.errno in (errno.EBUSY, errno.ETXTBSY):
                raise RuntimeError(E.FILE_LOCKED)
            raise RuntimeError(E.COPY_FAILED)
        if not d.exists() or d.stat().st_size != s.stat().st_size or not s.exists():
            raise RuntimeError(E.COPY_FAILED)
        return self.result("FILE_COPIED", s, d)

    # -------------------------------------------------------------- move --
    def move(self, source, destination, expected_fingerprint=None):
        s = self._target(source)
        self._check_not_locked(s)
        if expected_fingerprint is not None:
            self._check_unchanged(s, expected_fingerprint)
        d = self.p.validate(destination)
        if d.exists() and not self.p.allow_overwrite:
            raise RuntimeError(E.DESTINATION_EXISTS)
        if not d.parent.exists():
            raise RuntimeError(E.FILE_NOT_FOUND)
        try:
            shutil.move(str(s), str(d))
        except PermissionError:
            raise RuntimeError(E.PERMISSION_DENIED)
        except OSError as ex:
            if ex.errno in (errno.EBUSY, errno.ETXTBSY):
                raise RuntimeError(E.FILE_LOCKED)
            raise RuntimeError(E.MOVE_FAILED)
        if not d.exists() or s.exists():
            raise RuntimeError(E.MOVE_FAILED)
        return self.result("FILE_MOVED", s, d)

    def move_idempotent(self, source, destination):
        """6.12 / 6.27 — safe to call again after a crash: if the source is
        already gone and the destination already matches, treat as success
        instead of re-attempting (which would raise FILE_NOT_FOUND) or
        silently duplicating work."""
        s_path = self.p.validate(source)
        d_path = self.p.validate(destination)
        if not s_path.exists() and d_path.exists():
            return self.result("FILE_MOVED", s_path, d_path, changed=False)
        return self.move(source, destination)

    # ------------------------------------------------------------ rename --
    def rename(self, source, new_name):
        s = self._target(source)
        self._check_not_locked(s)
        if not _valid_name(new_name):
            raise RuntimeError(E.RENAME_FAILED)
        d = self.p.validate(s.parent / new_name)
        if d.exists():
            raise RuntimeError(E.DESTINATION_EXISTS)
        try:
            s.rename(d)
        except PermissionError:
            raise RuntimeError(E.PERMISSION_DENIED)
        except OSError:
            raise RuntimeError(E.RENAME_FAILED)
        if s.exists() or not d.exists():
            raise RuntimeError(E.RENAME_FAILED)
        return self.result("FILE_RENAMED", s, d)

    # ---------------------------------------------------------- evidence --
    def result(self, event, source, dest, changed=True):
        content_hash = None
        if changed and dest.exists() and dest.is_file():
            content_hash = EvidenceStore.hash_file(dest)
        ev = self.evidence.create(
            kind=event,
            target_ref=str(source),
            result_ref=str(dest),
            content_hash=content_hash,
        )
        return {
            "action_id": event,
            "status": "SUCCESS",
            "changed": changed,
            "evidence_ids": [ev["evidence_id"]],
            "data": {"source": str(source), "destination": str(dest)},
            "error": None,
        }
