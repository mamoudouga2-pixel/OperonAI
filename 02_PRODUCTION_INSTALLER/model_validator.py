from pathlib import Path
from artifact_manager.checksum import sha256_file
from common.errors import VerificationError
def validate_model_file(path,expected_sha256=None,min_bytes=1):
    p=Path(path)
    if not p.is_file() or p.stat().st_size<min_bytes: raise VerificationError('Invalid model artifact','SEC_CHECKSUM_MISMATCH')
    if expected_sha256 and sha256_file(p).lower()!=expected_sha256.lower(): raise VerificationError('Model checksum mismatch','SEC_CHECKSUM_MISMATCH')
    return True
