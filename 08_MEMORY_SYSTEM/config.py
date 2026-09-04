"""
Configuration for the memory subsystem (spec section 8.30).

Local-first defaults: everything works fully offline with the built-in
adapters. A real deployment can override any of this via a JSON file or
an explicit dict, e.g.::

    cfg = MemoryConfig.load("memory.config.json")
"""

import json

DEFAULT_CONFIG = {
    "memory": {
        "working_ttl_minutes": 60,
        "max_retrieval_items": 10,
        "require_provenance": True,
        "default_local_only": True,
    },
    "vector": {
        "enabled": True,
        "backend": "adapter-selected",
    },
    "retention": {
        "task_history_days": 30,
        "cleanup_interval_minutes": 60,
    },
}


def _deep_merge(base, override):
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class MemoryConfig:
    """Thin, validated wrapper around the JSON config contract."""

    def __init__(self, data=None):
        self._data = _deep_merge(DEFAULT_CONFIG, data or {})

    @classmethod
    def load(cls, path=None, overrides=None):
        data = {}
        if path is not None:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        if overrides:
            data = _deep_merge(data, overrides)
        return cls(data)

    def as_dict(self):
        return json.loads(json.dumps(self._data))

    # Convenience accessors -------------------------------------------------
    @property
    def working_ttl_minutes(self):
        return self._data["memory"]["working_ttl_minutes"]

    @property
    def max_retrieval_items(self):
        return self._data["memory"]["max_retrieval_items"]

    @property
    def require_provenance(self):
        return self._data["memory"]["require_provenance"]

    @property
    def default_local_only(self):
        return self._data["memory"]["default_local_only"]

    @property
    def vector_enabled(self):
        return self._data["vector"]["enabled"]

    @property
    def task_history_days(self):
        return self._data["retention"]["task_history_days"]

    @property
    def cleanup_interval_minutes(self):
        return self._data["retention"]["cleanup_interval_minutes"]
