from pathlib import Path
import json, time, uuid

class TransactionJournal:
    def __init__(self,path): self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
    def append(self,event,**data):
        rec={'id':str(uuid.uuid4()),'timestamp':time.time(),'event':event,**data}
        with self.path.open('a',encoding='utf-8') as f: f.write(json.dumps(rec,sort_keys=True)+'\n')
        return rec
    def read(self):
        if not self.path.exists(): return []
        out=[]
        for line in self.path.read_text(encoding='utf-8').splitlines():
            if line.strip(): out.append(json.loads(line))
        return out
