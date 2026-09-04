import pytest
from artifact_manager.validator import validate_file
from common.errors import VerificationError

def test_checksum_mismatch(tmp_path):
    p=tmp_path/"x"; p.write_bytes(b"x")
    with pytest.raises(VerificationError): validate_file(p,"0"*64)
