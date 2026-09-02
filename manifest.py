import re
from dataclasses import dataclass

ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")

@dataclass(frozen=True)
class ModuleManifest:
    module_id: str
    version: str
    api_version: str
    capabilities: tuple[str, ...]
    permissions: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw):
        if not isinstance(raw, dict):
            raise ValueError("manifest must be an object")
        required = {"module_id", "version", "api_version", "capabilities", "permissions"}
        missing = required - raw.keys()
        if missing:
            raise ValueError(f"missing manifest fields: {sorted(missing)}")
        vals = [raw[k] for k in ("module_id","version","api_version","capabilities","permissions")]
        mid, ver, api, caps, perms = vals
        if not isinstance(mid, str) or not ID_RE.fullmatch(mid):
            raise ValueError("invalid module_id")
        if not all(isinstance(x, str) and x.strip() for x in (ver, api)):
            raise ValueError("version/api_version must be non-empty strings")
        if not isinstance(caps, list) or not all(isinstance(x, str) and x.strip() for x in caps):
            raise ValueError("capabilities must be list[str]")
        if not isinstance(perms, list) or not all(isinstance(x, str) and x.strip() for x in perms):
            raise ValueError("permissions must be list[str]")
        if len(set(caps)) != len(caps) or len(set(perms)) != len(perms):
            raise ValueError("duplicate capabilities/permissions are not allowed")
        return cls(mid, ver, api, tuple(caps), tuple(perms))

    def to_dict(self):
        return {
            "module_id": self.module_id, "version": self.version,
            "api_version": self.api_version, "capabilities": list(self.capabilities),
            "permissions": list(self.permissions)
        }
