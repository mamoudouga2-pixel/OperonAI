from dataclasses import dataclass,field
@dataclass
class RepairReport:
    repaired:list[str]=field(default_factory=list); failed:list[str]=field(default_factory=list); skipped_user_data:list[str]=field(default_factory=list)
