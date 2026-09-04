from pathlib import Path
class PathPolicy:
    def __init__(self,allowed_roots,protected_roots=None):
        self.roots=[Path(x).expanduser().resolve() for x in allowed_roots]
        self.protected=[Path(x).expanduser().resolve() for x in (protected_roots or [])]
    def validate(self,path):
        p=Path(path).expanduser().resolve()
        if any(p==r or r in p.parents for r in self.protected):raise RuntimeError("PROTECTED_PATH_DENIED")
        if any(p==r or r in p.parents for r in self.roots):return True
        raise RuntimeError("PERMISSION_SCOPE_INVALID")
