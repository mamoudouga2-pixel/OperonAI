from dataclasses import dataclass
@dataclass(frozen=True)
class Intent:
    instruction:str
    target:str|None
    constraints:tuple[str,...]
    expected_result:str|None
    critical_missing:tuple[str,...]
    def to_dict(self): return {"instruction":self.instruction,"target":self.target,"constraints":list(self.constraints),
        "expected_result":self.expected_result,"critical_missing":list(self.critical_missing)}
class InstructionUnderstander:
    def understand(self,instruction,*,target=None,constraints=None,expected_result=None):
        if not isinstance(instruction,str) or not instruction.strip(): raise ValueError("instruction required")
        missing=[]
        if target is None: missing.append("target")
        if expected_result is None: missing.append("expected_result")
        return Intent(instruction,target,tuple(constraints or ()),expected_result,tuple(missing))
