import json
from pathlib import Path
class ModelRegistry:
    def __init__(self,path): self.path=Path(path); self.data=json.loads(self.path.read_text()) if self.path.exists() else {}
    def register(self,model_id,info): self.data[model_id]=info; self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps(self.data,indent=2),encoding='utf-8')
    def get(self,model_id): return self.data.get(model_id)
