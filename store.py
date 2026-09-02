import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

class StateStore:
    def __init__(self, runtime_dir, config):
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.runtime_dir / config.state_file_name
        self.audit_path = self.runtime_dir / config.audit_log_name
        self._lock = RLock()
        self._state = self._load()

    def _default(self):
        return {"schema_version": 1, "application": {}, "modules": {}, "tasks": {}}

    def _load(self):
        if not self.state_path.exists():
            return self._default()
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"cannot load state: {exc}") from exc
        if not isinstance(data, dict):
            raise RuntimeError("state root must be object")
        for key in ("application", "modules", "tasks"):
            if not isinstance(data.get(key, {}), dict):
                raise RuntimeError(f"state.{key} must be object")
        return data

    def _persist(self):
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.state_path)

    def set_application(self, key, value):
        with self._lock:
            self._state.setdefault("application", {})[key] = value
            self._persist()

    def get_application(self, key, default=None):
        with self._lock:
            return self._state.get("application", {}).get(key, default)

    def set_module(self, module_id, value):
        with self._lock:
            self._state.setdefault("modules", {})[module_id] = dict(value)
            self._persist()

    def get_module(self, module_id):
        with self._lock:
            value = self._state.get("modules", {}).get(module_id)
            return dict(value) if isinstance(value, dict) else None

    def set_task(self, task_id, value):
        with self._lock:
            self._state.setdefault("tasks", {})[task_id] = dict(value)
            self._persist()

    def get_task(self, task_id):
        with self._lock:
            value = self._state.get("tasks", {}).get(task_id)
            return dict(value) if isinstance(value, dict) else None

    def audit(self, action, payload):
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "payload": payload,
        }
        with self._lock:
            with self.audit_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
