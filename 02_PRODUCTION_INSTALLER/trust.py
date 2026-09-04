from pathlib import Path
from dataclasses import dataclass
import json
from .signature import verify_ed25519
from .checksum import sha256_file
from common.errors import ManifestError, VerificationError

@dataclass(frozen=True)
class TrustedSourcePolicy:
    allowed_hosts: frozenset[str]
    max_redirects:int=3
    require_https:bool=True

class TrustStore:
    def __init__(self,path=None,embedded_keys=None):
        self.path=Path(path) if path else None; self.keys={k:v for k,v in (embedded_keys or {}).items()}
        if self.path and self.path.exists(): self.keys.update(json.loads(self.path.read_text()).get('keys',{}))
    def get(self,key_id): return self.keys.get(key_id)
    def rotate(self,old_key_id,new_key_id,new_public_key,rotation_signature):
        old=self.get(old_key_id)
        if not old: raise VerificationError('Unknown old trust key')
        payload=(new_key_id+':'+new_public_key).encode()
        import base64
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(base64.b64decode(old)).verify(base64.b64decode(rotation_signature),payload)
        self.keys[new_key_id]=new_public_key
        if self.path:
            self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps({'keys':self.keys},indent=2))

def verify_signed_manifest(manifest_path, key_id, signature, trust:TrustStore):
    key=trust.get(key_id)
    if not key: raise VerificationError('Untrusted signing key', 'SEC_UNTRUSTED_SOURCE')
    try: verify_ed25519(Path(manifest_path), signature, key)
    except Exception as e: raise VerificationError(str(e),'SEC_SIGNATURE_INVALID') from e
    return True
