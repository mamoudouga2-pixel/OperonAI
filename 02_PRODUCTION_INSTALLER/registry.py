import json, os
from pathlib import Path
class ComponentRegistry:
    def __init__(self,path): self.path=Path(path); self.data=json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
    def register(self,component,info):
        self.data[component.component_id]={"version":component.version,"type":component.component_type,**info}; self.path.parent.mkdir(parents=True,exist_ok=True); tmp=self.path.with_suffix('.tmp'); tmp.write_text(json.dumps(self.data,indent=2),encoding='utf-8'); os.replace(tmp,self.path)
    def get(self,cid): return self.data.get(cid)
