import json
from pathlib import Path
from dependency_manager.manifest import Manifest

def read_manifest(path): return Manifest.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
