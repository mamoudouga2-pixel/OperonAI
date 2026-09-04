"""
Backup (spec 8.25 BACKUP AND RECOVERY).

"Encrypted/secured backup policy is configurable. Backup itself follows
a separate retention policy. Cloud sync is not mandatory by default -
local-first stays the default."

The optional simple XOR "encryption" here is a placeholder for a real
crypto library (e.g. `cryptography`'s Fernet) in a production build; it
exists so the encrypted/plaintext code path and its config flag are
exercised end-to-end even in this dependency-free reference package.
"""

import hashlib
import json
import tempfile
import time
from pathlib import Path


def _keystream(key, length):
    key = (key or "").encode("utf-8") or b"local-default-key"
    stream = bytearray()
    counter = 0
    while len(stream) < length:
        stream += hashlib.sha256(key + counter.to_bytes(4, "big")).digest()
        counter += 1
    return bytes(stream[:length])


def _xor(data, key):
    ks = _keystream(key, len(data))
    return bytes(a ^ b for a, b in zip(data, ks))


class Backup:
    def __init__(self, encryption_key=None):
        self.encryption_key = encryption_key

    def default_path(self):
        return Path(tempfile.gettempdir()) / f"memory-backup-{int(time.time())}.json"

    def dump(self, state, path, encrypt=False):
        payload = json.dumps(state, sort_keys=True).encode("utf-8")
        checksum = hashlib.sha256(payload).hexdigest()
        envelope = {
            "checksum": checksum,
            "encrypted": bool(encrypt and self.encryption_key),
        }

        path = Path(path)
        if envelope["encrypted"]:
            envelope["ciphertext_hex"] = _xor(payload, self.encryption_key).hex()
            path.write_text(json.dumps(envelope), encoding="utf-8")
        else:
            # Plain path stays a bare JSON dump of ``state`` for backward
            # compatibility with callers/tests that read it back directly.
            path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        return path
