from pathlib import Path
import json
from artifact_manager.manifest_reader import read_manifest
from artifact_manager.trust import verify_signed_manifest,TrustStore
from artifact_manager.validator import validate_file
class OfflineBundleInstaller:
    def __init__(self,bundle_dir,paths): self.bundle=Path(bundle_dir); self.paths=paths
    def verify_bundle(self,trust_store=None,key_id=None,signature=None):
        manifest=self.bundle/'manifest/install_manifest.json'; checks=self.bundle/'manifest/checksums.json'
        if not manifest.exists() or not checks.exists(): raise ValueError('Invalid offline bundle')
        if trust_store and key_id and signature: verify_signed_manifest(manifest,key_id,signature,trust_store)
        checksums=json.loads(checks.read_text(encoding='utf-8'))
        for rel,meta in checksums.items(): validate_file(self.bundle/rel,meta.get('sha256'))
        read_manifest(manifest)
        return True
    def install(self,trust_store=None,key_id=None,signature=None):
        self.verify_bundle(trust_store,key_id,signature)
        return read_manifest(self.bundle/'manifest/install_manifest.json')
