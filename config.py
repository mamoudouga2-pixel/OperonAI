from dataclasses import dataclass

@dataclass(frozen=True)
class CoreConfig:
    api_version: str = "1"
    max_module_retries: int = 3
    max_task_retries: int = 3
    event_handler_limit: int = 10_000
    event_payload_limit: int = 1_000_000
    state_file_name: str = "state.json"
    audit_log_name: str = "audit.jsonl"

    def __post_init__(self):
        if not isinstance(self.api_version, str) or not self.api_version:
            raise ValueError("api_version must be non-empty")
        for name in ("max_module_retries", "max_task_retries"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")
        if self.event_handler_limit < 1 or self.event_payload_limit < 1:
            raise ValueError("event limits must be positive")
