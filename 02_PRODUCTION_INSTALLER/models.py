from dataclasses import dataclass, field, asdict
from typing import Any

COMPONENT_STATES = ["UNKNOWN","DISCOVERED","AVAILABLE","DOWNLOADING","DOWNLOADED","VERIFYING","VERIFIED","INSTALLING","INSTALLED","CONFIGURING","READY","FAILED","CORRUPTED","OUTDATED","REMOVED"]

@dataclass(frozen=True)
class Component:
    component_id: str
    component_type: str
    version: str
    platform: str = "any"
    architecture: str = "any"
    required: bool = True
    size_bytes: int = 0
    download_url: str | None = None
    sha256: str | None = None
    signature: str | None = None
    signature_algorithm: str = "ed25519"
    dependencies: tuple[str, ...] = ()
    minimum_app_version: str | None = None
    maximum_app_version: str | None = None
    payload_type: str = "file"
    install_mode: str = "copy"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d):
        d=dict(d); d["dependencies"]=tuple(d.get("dependencies", [])); return cls(**d)

@dataclass
class InstallationSnapshot:
    installation_id: str
    current_stage: str = "NEW"
    completed_components: list[str] = field(default_factory=list)
    pending_components: list[str] = field(default_factory=list)
    failed_components: list[str] = field(default_factory=list)
    timestamp: str = ""
    mode: str = "fresh"
    schema_version: int = 1
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self): return asdict(self)
