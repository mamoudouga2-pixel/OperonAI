from dataclasses import dataclass,asdict
from datetime import datetime,timezone
@dataclass
class Evidence:
 evidence_id:str;task_id:str;action_id:str;type:str;source:str;created_at:str;path:str;hash:str;description:str;redaction_status:str
 def to_dict(self): return asdict(self)
def now(): return datetime.now(timezone.utc)
