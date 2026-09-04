from artifact_manager.manifest_reader import read_manifest
class UpdateManifest:
    def __init__(self,manifest): self.manifest=manifest
    @classmethod
    def load(cls,path): return cls(read_manifest(path))
