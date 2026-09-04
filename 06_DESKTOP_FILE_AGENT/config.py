"""6.34 CONFIGURATION — default values. Callers may override any subset."""

DEFAULT_CONFIG = {
    "desktop": {
        "max_action_retries": 3,
        "default_timeout_ms": 10000,
        "max_scan_items": 10000,
        "max_scan_depth": 8,
    },
    "files": {
        "allow_overwrite": False,
        "delete_requires_approval": True,
    },
    "security": {
        "restricted_roots": True,
    },
}


def merged(overrides=None):
    """Shallow-merge overrides on top of DEFAULT_CONFIG (two levels deep)."""
    cfg = {k: dict(v) for k, v in DEFAULT_CONFIG.items()}
    for k, v in (overrides or {}).items():
        cfg.setdefault(k, {})
        cfg[k].update(v)
    return cfg
