from dataclasses import dataclass
@dataclass(frozen=True)
class Plan:
    steps:tuple[dict,...]
    max_steps:int
    max_retries:int
    max_runtime_s:float
    def to_dict(self): return {"steps":[dict(x) for x in self.steps],"max_steps":self.max_steps,"max_retries":self.max_retries,"max_runtime_s":self.max_runtime_s}
class Planner:
    def build(self,intent,*,steps=None,max_steps=20,max_retries=2,max_runtime_s=300):
        if intent.critical_missing: raise ValueError("CLARIFICATION_REQUIRED: "+", ".join(intent.critical_missing))
        steps=steps or [{"action":"execute","target":intent.target,"expected_result":intent.expected_result}]
        if len(steps)>max_steps: raise ValueError("plan exceeds maximum steps")
        return Plan(tuple(dict(s) for s in steps),max_steps,max_retries,float(max_runtime_s))
