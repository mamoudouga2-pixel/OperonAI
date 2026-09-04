from dataclasses import dataclass,asdict
import datetime,hashlib,json
@dataclass
class Evidence:
    evidence_id:str; type:str; task_id:str; action_id:str; source:str; path:str; timestamp:str; hash:str
    def to_dict(self): return asdict(self)
class ObservationManager:
    def __init__(self,adapter): self.adapter=adapter; self.seq=0
    def before_after(self,sid,before,after): return {"before":before,"after":after,"url":after.get("url"),"title":after.get("title")}
    def evidence(self,sid,task_id,action_id):
        self.seq+=1; shot=self.adapter.screenshot(sid); digest=hashlib.sha256(shot.get("bytes",b"")).hexdigest()
        return Evidence(f"EVID-{self.seq:03d}","SCREENSHOT",task_id,action_id,"browser",shot["path"],
                        datetime.datetime.now(datetime.timezone.utc).isoformat(),digest)
