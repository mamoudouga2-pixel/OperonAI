from pathlib import Path
import json, time
class Quarantine:
    def __init__(self,root): self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
    def put(self,artifact,reason,source=None,artifact_id=None):
        src=Path(artifact); target=self.root/(artifact_id or src.name)
        target.mkdir(parents=True,exist_ok=True)
        dest=target/src.name
        src.replace(dest)
        (target/'metadata.json').write_text(json.dumps({'artifact_id':artifact_id,'reason':reason,'timestamp':time.time(),'original_source':source},indent=2),encoding='utf-8')
        return dest
