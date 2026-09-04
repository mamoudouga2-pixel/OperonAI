class CompatibilityResult:
    def __init__(self,compatible,reasons):self.compatible=bool(compatible);self.reasons=tuple(reasons)
    def to_dict(self):return {"compatible":self.compatible,"reasons":list(self.reasons)}

class CompatibilityChecker:
    def check(self,requirement,profile,adapter,policy=None):
        req=requirement or {}; reasons=[]
        required=set(req.get("required_capabilities",[]))
        missing=sorted(required-set(adapter.capabilities))
        if missing:reasons.append("missing capabilities: "+", ".join(missing))
        if profile.ram_gb<float(req.get("min_ram_gb",0)):reasons.append("insufficient system RAM")
        if profile.ram_gb<adapter.ram_gb:reasons.append("adapter RAM requirement exceeds hardware")
        if profile.gpu.vram_gb<max(float(req.get("min_vram_gb",0)),adapter.vram_gb):
            reasons.append("insufficient GPU VRAM")
        if int(req.get("context_budget",0))>adapter.context_budget:reasons.append("context budget unsupported")
        if policy and not policy.permits(adapter):reasons.append("blocked by performance/user policy")
        return CompatibilityResult(not reasons,reasons)
