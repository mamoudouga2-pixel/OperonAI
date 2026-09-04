import json, os, uuid
from datetime import datetime, timezone
from pathlib import Path
from common.models import InstallationSnapshot

def now(): return datetime.now(timezone.utc).isoformat()
class InstallationState:
    def __init__(self, path, snapshot=None): self.path=Path(path); self.snapshot=snapshot or InstallationSnapshot(str(uuid.uuid4()),timestamp=now())
    @property
    def current_stage(self): return self.snapshot.current_stage
    @current_stage.setter
    def current_stage(self,v): self.snapshot.current_stage=v; self.snapshot.timestamp=now()
    @property
    def mode(self): return self.snapshot.mode
    @mode.setter
    def mode(self,v): self.snapshot.mode=v
    @property
    def completed_components(self): return self.snapshot.completed_components
    @property
    def pending_components(self): return self.snapshot.pending_components
    @property
    def failed_components(self): return self.snapshot.failed_components
    def save(self, path=None):
        p=Path(path or self.path); p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+".tmp"); tmp.write_text(json.dumps(self.snapshot.to_dict(),indent=2),encoding="utf-8"); os.replace(tmp,p)
    @classmethod
    def load(cls,path):
        p=Path(path)
        if not p.exists(): return cls(p)
        try: data=json.loads(p.read_text(encoding="utf-8")); return cls(p,InstallationSnapshot(**data))
        except Exception: return cls(p)
