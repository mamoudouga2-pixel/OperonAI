from dataclasses import dataclass,asdict
import json, os
from pathlib import Path
@dataclass
class DownloadState:
    url:str; destination:str; bytes_downloaded:int=0; total_bytes:int|None=None; etag:str|None=None; status:str="pending"
    def save(self,path):
        p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix('.tmp'); t.write_text(json.dumps(asdict(self),indent=2),encoding='utf-8'); os.replace(t,p)
    @classmethod
    def load(cls,path): return cls(**json.loads(Path(path).read_text(encoding='utf-8')))
