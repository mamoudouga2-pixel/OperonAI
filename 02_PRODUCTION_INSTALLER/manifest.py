from common.models import Component
from common.errors import ManifestError
class Manifest:
    def __init__(self,components,metadata=None): self.components=components; self.metadata=metadata or {}
    @classmethod
    def from_dict(cls,d):
        if not isinstance(d,dict) or not isinstance(d.get("components"),list): raise ManifestError("Manifest must contain components[]")
        comps=[Component.from_dict(x) for x in d["components"]]; ids=[c.component_id for c in comps]
        if len(ids)!=len(set(ids)): raise ManifestError("Duplicate component_id")
        return cls(comps,d.get("metadata",{}))

def validate_manifest(components):
    for c in components:
        if c.size_bytes<0: raise ManifestError(f"Invalid size for {c.component_id}")
        if c.sha256 and len(c.sha256)!=64: raise ManifestError(f"Invalid SHA-256 for {c.component_id}")
    return True
