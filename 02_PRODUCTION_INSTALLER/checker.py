"""Spec §3 requires a dedicated `integrity_checker/` module.

The actual checksum/signature primitives live in `artifact_manager`
(checksum.py, signature.py, validator.py) so download_manager and
artifact_manager can share them without a circular import. This module
is the documented, spec-named entry point for integrity verification
and simply re-exposes that shared implementation.
"""
from artifact_manager.checksum import sha256_file
from artifact_manager.signature import verify_ed25519
from artifact_manager.validator import validate_file
from common.errors import VerificationError


class IntegrityChecker:
    """Verified artifact ছাড়া install নয় (spec §4) — single call site
    that enforces checksum + optional signature verification and raises
    VerificationError (fail-closed) on any mismatch."""

    def verify(self, path, expected_sha256=None, signature=None, public_key=None):
        return validate_file(path, expected_sha256, signature, public_key)

    def checksum(self, path):
        return sha256_file(path)


__all__ = ["IntegrityChecker", "sha256_file", "verify_ed25519", "validate_file", "VerificationError"]
