from dataclasses import dataclass
@dataclass(frozen=True)
class Selection:
    adapter_id:str;score:float;reasons:tuple
    def to_dict(self):return {"adapter_id":self.adapter_id,"score":self.score,"reasons":list(self.reasons)}
class ModelSelector:
    def __init__(self,checker):self.checker=checker
    def rank(self,req,profile,adapters,policy=None):
        out=[]
        for a in adapters:
            c=self.checker.check(req,profile,a,policy)
            if not c.compatible:continue
            required=set(req.get("required_capabilities",[]))
            score=100*len(required&set(a.capabilities))-a.ram_gb-a.vram_gb*0.5
            if "lightweight" in a.capabilities:score-=1
            out.append(Selection(a.adapter_id,score,("compatible",)))
        return sorted(out,key=lambda x:(-x.score,x.adapter_id))
    def select(self,req,profile,adapters,policy=None):
        ranked=self.rank(req,profile,adapters,policy)
        if not ranked:raise RuntimeError("UNSUPPORTED_CONFIGURATION: no compatible adapter")
        return ranked[0]
