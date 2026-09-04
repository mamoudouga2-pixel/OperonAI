from pathlib import Path
import shutil
from .checksum import sha256_file
from .signature import verify_ed25519
from common.errors import VerificationError

def validate_file(path,expected_sha256=None,signature=None,public_key=None):
    p=Path(path)
    if not p.is_file(): raise VerificationError(f"Artifact missing: {p}")
    if expected_sha256 and sha256_file(p).lower()!=expected_sha256.lower(): raise VerificationError(f"Checksum mismatch: {p}")
    if signature and public_key: verify_ed25519(p,signature,public_key)
    elif signature or public_key: raise VerificationError("Both signature and public_key are required")
    return True

def ensure_component_artifact(component,cache_dir):
    p=Path(cache_dir)/component.component_id/Path(component.metadata.get("artifact_name",f"{component.component_id}-{component.version}"));
    if component.metadata.get("local_artifact"):
        src=Path(component.metadata["local_artifact"]); p.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,p)
    validate_file(p,component.sha256,component.signature,component.metadata.get("public_key")); return p
