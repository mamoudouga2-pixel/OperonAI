import hashlib
from pathlib import Path

def sha256_file(path,chunk=1024*1024):
    h=hashlib.sha256();
    with Path(path).open("rb") as f:
        while b:=f.read(chunk): h.update(b)
    return h.hexdigest()
