from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid

STATES = ("NEW","PLANNING","WAITING_APPROVAL","RUNNING","VERIFYING","RECOVERING",
          "SUCCESS","FAILED","CANCELLED","TIMEOUT")

ALLOWED_TRANSITIONS = {
    "NEW": {"PLANNING","CANCELLED"},
    "PLANNING": {"WAITING_APPROVAL","RUNNING","CANCELLED","FAILED"},
    "WAITING_APPROVAL": {"RUNNING","CANCELLED","FAILED"},
    "RUNNING": {"VERIFYING","RECOVERING","SUCCESS","FAILED","CANCELLED","TIMEOUT"},
    "VERIFYING": {"SUCCESS","RECOVERING","FAILED","CANCELLED","TIMEOUT"},
    "RECOVERING": {"RUNNING","VERIFYING","FAILED","CANCELLED","TIMEOUT"},
    "SUCCESS": set(),"FAILED": set(),"CANCELLED": set(),"TIMEOUT": set()
}

def now(): return datetime.now(timezone.utc).isoformat()

@dataclass
class Task:
    task_id: str
    description: str
    state: str = "NEW"
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)
    retry_count: int = 0
    metadata: dict = field(default_factory=dict)

    @classmethod
    def create(cls, description, metadata=None):
        if not isinstance(description, str) or not description.strip():
            raise ValueError("description must be non-empty")
        return cls(str(uuid.uuid4()), description.strip(), metadata=metadata or {})

    def to_dict(self):
        return self.__dict__.copy()
