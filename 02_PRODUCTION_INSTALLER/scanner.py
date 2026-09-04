from pathlib import Path
from artifact_manager.checksum import sha256_file
class RepairScanner:
    def scan(self,root,expected):
        root=Path(root); issues=[]
        for rel,meta in expected.items():
            expected_hash=meta if isinstance(meta,str) else meta.get('sha256')
            p=root/rel
            if not p.exists(): issues.append({'path':rel,'problem':'MISSING_FILE','issue':'missing','repairable':True})
            elif expected_hash and sha256_file(p).lower()!=expected_hash.lower(): issues.append({'path':rel,'problem':'HASH_MISMATCH','issue':'corrupted','repairable':True})
        return issues
