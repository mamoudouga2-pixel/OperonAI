from dataclasses import dataclass,asdict
@dataclass(frozen=True)
class SecurityDecision:
    action_id:str; decision:str; risk_level:str; requires_approval:bool; policy_id:str; reasons:list; constraints:dict; expires_at:str|None=None
    def to_dict(self): return asdict(self)
