from pathlib import Path
from urllib.request import Request,urlopen
import json
from download_manager.http_policy import validate_url
from artifact_manager.trust import TrustStore,verify_signed_manifest
from artifact_manager.manifest_reader import read_manifest
class OnlineManifestClient:
    def __init__(self,trust_store): self.trust_store=trust_store
    def fetch(self,url,key_id,signature,allowed_hosts):
        validate_url(url,allowed_hosts,True)
        req=Request(url,headers={'Accept':'application/json'},method='GET')
        with urlopen(req,timeout=30) as r: data=r.read()
        p=Path(__file__).with_name('_downloaded_manifest.json'); p.write_bytes(data)
        try: verify_signed_manifest(p,key_id,signature,self.trust_store); return read_manifest(p)
        finally: p.unlink(missing_ok=True)
