"""
Restore (spec 8.25): user-confirmed restore, followed by schema
migration/integrity validation.
"""

import hashlib
import json

from errors import BackupRestoreFailed
from .backup import _xor


class Restore:
    def load(self, path, encryption_key=None):
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as exc:
            raise BackupRestoreFailed(str(exc)) from exc

        if isinstance(raw, dict) and set(raw.keys()) >= {"checksum", "encrypted"}:
            if raw["encrypted"]:
                if not encryption_key:
                    raise BackupRestoreFailed("backup is encrypted; no key supplied")
                payload = _xor(bytes.fromhex(raw["ciphertext_hex"]), encryption_key)
            else:
                raise BackupRestoreFailed("malformed backup envelope")

            if hashlib.sha256(payload).hexdigest() != raw["checksum"]:
                raise BackupRestoreFailed("backup checksum mismatch; possible corruption")
            return json.loads(payload.decode("utf-8"))

        return raw

    def validate_schema(self, state, migrations):
        """Confirm the restored state's schema version is one this
        build's migrations know about."""
        version = state.get("schema_version") if isinstance(state, dict) else None
        if version is not None and version > migrations.current():
            raise BackupRestoreFailed(
                f"backup schema version {version} is newer than supported "
                f"{migrations.current()}"
            )
        return True
