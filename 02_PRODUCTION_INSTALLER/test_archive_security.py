import zipfile
from artifact_manager.archive_security import safe_extract
from common.errors import VerificationError

def test_zip_traversal_rejected(tmp_path):
    z=tmp_path/'x.zip'
    with zipfile.ZipFile(z,'w') as f:f.writestr('../evil.txt','x')
    try: safe_extract(z,tmp_path/'out')
    except VerificationError as e: assert e.code=='SEC_ARCHIVE_PATH_TRAVERSAL'
    else: assert False
