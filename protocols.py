from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Event:
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None

    def __post_init__(self):
        if not isinstance(self.event_type, str) or not self.event_type.strip():
            raise ValueError("event_type must be non-empty")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dict")

@dataclass(frozen=True)
class FailureReport:
    module_id: str
    reason: str
    retryable: bool = True
    permission_uncertain: bool = False
    safety_uncertain: bool = False
