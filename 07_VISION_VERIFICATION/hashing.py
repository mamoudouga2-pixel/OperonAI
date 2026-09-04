import hashlib
def sha256_bytes(data): return hashlib.sha256(data).hexdigest()
