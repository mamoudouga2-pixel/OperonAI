import os
import stat
from pathlib import Path


class ArtifactStore:
    """File-backed artifact store with permission-controlled paths (spec 7.11:
    'Evidence path access permission-controlled হবে')."""

    def __init__(self, root, dir_mode=0o700, file_mode=0o600):
        self.root = Path(root)
        self.dir_mode = dir_mode
        self.file_mode = file_mode
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, self.dir_mode)

    def save(self, name, data):
        if "/" in name or "\\" in name or name in (".", ".."):
            raise ValueError(f"unsafe artifact name: {name!r}")
        path = self.root / name
        path.write_bytes(data)
        os.chmod(path, self.file_mode)
        return str(path)

    def read(self, name):
        path = self.root / name
        return path.read_bytes()

    def exists(self, name):
        return (self.root / name).exists()

    def delete(self, name):
        path = self.root / name
        if path.exists():
            path.unlink()
            return True
        return False
