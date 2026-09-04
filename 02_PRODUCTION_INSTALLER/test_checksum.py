from artifact_manager.checksum import sha256_file
from artifact_manager.validator import validate_file
import hashlib

def test_checksum(tmp_path):
    p=tmp_path/"a"; p.write_bytes(b"hello"); h=hashlib.sha256(b"hello").hexdigest(); assert sha256_file(p)==h; assert validate_file(p,h)
