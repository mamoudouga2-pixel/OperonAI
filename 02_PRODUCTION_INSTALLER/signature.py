import base64, binascii
from common.errors import VerificationError

def verify_ed25519(file_path,signature,public_key):
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.hazmat.primitives import serialization
        sig=base64.b64decode(signature); key_bytes=base64.b64decode(public_key)
        key=Ed25519PublicKey.from_public_bytes(key_bytes); data=open(file_path,"rb").read(); key.verify(sig,data); return True
    except ImportError as e: raise VerificationError("Ed25519 verification requires optional 'cryptography' package") from e
    except Exception as e: raise VerificationError(f"Signature verification failed: {e}") from e
