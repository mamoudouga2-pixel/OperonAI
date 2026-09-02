from dataclasses import dataclass
from threading import RLock
from communication.protocols import Event, FailureReport
from module_manager.manifest import ModuleManifest

@dataclass
class ModuleRecord:
    manifest: ModuleManifest
    start_fn: object = None
    stop_fn: object = None
    health_fn: object = None
    status: str = "REGISTERED"
    failures: int = 0

class ModuleManager:
    def __init__(self, event_bus, state_store, error_handler, config):
        self.event_bus, self.state_store = event_bus, state_store
        self.error_handler, self.config = error_handler, config
        self._modules, self._lock = {}, RLock()

    def register(self, manifest, *, start_fn=None, stop_fn=None, health_fn=None):
        m = manifest if isinstance(manifest, ModuleManifest) else ModuleManifest.from_dict(manifest)
        if m.api_version != self.config.api_version:
            raise ValueError("incompatible module api_version")
        with self._lock:
            if m.module_id in self._modules:
                raise ValueError(f"module already registered: {m.module_id}")
            self._modules[m.module_id] = ModuleRecord(m, start_fn, stop_fn, health_fn)
            self._persist(m.module_id)
        self.event_bus.publish(Event("module.registered", {"module_id": m.module_id}))
        return m

    def list_modules(self):
        with self._lock: return sorted(self._modules)

    def status(self, module_id):
        return self._get(module_id).status

    def start(self, module_id):
        rec = self._get(module_id)
        try:
            if rec.start_fn: rec.start_fn()
            with self._lock: rec.status = "RUNNING"; self._persist(module_id)
            self.event_bus.publish(Event("module.started", {"module_id": module_id}))
            return True
        except Exception as exc:
            self.handle_failure(FailureReport(module_id, str(exc)))
            return False

    def stop(self, module_id):
        rec = self._get(module_id)
        try:
            if rec.stop_fn: rec.stop_fn()
            with self._lock: rec.status = "STOPPED"; self._persist(module_id)
            self.event_bus.publish(Event("module.stopped", {"module_id": module_id}))
            return True
        except Exception as exc:
            self.error_handler.record("STOP_FAILURE", exc, {"module_id": module_id})
            with self._lock: rec.status = "UNHEALTHY"; self._persist(module_id)
            return False

    def restart(self, module_id):
        self.stop(module_id)
        return self.start(module_id)

    def health_check(self, module_id):
        rec = self._get(module_id)
        try:
            healthy = bool(rec.health_fn()) if rec.health_fn else rec.status == "RUNNING"
            reason = "ok" if healthy else "health check returned false"
        except Exception as exc:
            healthy, reason = False, f"health check exception: {exc}"
        with self._lock:
            rec.status = "HEALTHY" if healthy else "UNHEALTHY"
            self._persist(module_id)
        return {"module_id": module_id, "healthy": healthy, "status": rec.status, "reason": reason}

    def handle_failure(self, report):
        rec = self._get(report.module_id)
        if report.permission_uncertain or report.safety_uncertain:
            with self._lock: rec.status = "FAIL_CLOSED"; self._persist(report.module_id)
            self.error_handler.fail_closed("uncertain permission/safety state",
                                           {"module_id": report.module_id, "reason": report.reason})
            return {"action": "fail_closed", "attempts": rec.failures}

        with self._lock:
            rec.failures += 1
            attempt = rec.failures
        self.error_handler.record("WORKER_FAILURE", report.reason,
                                  {"module_id": report.module_id, "attempt": attempt})
        if not report.retryable or attempt > self.config.max_module_retries:
            with self._lock: rec.status = "UNHEALTHY"; self._persist(report.module_id)
            self.event_bus.publish(Event("module.failed", {"module_id": report.module_id, "attempts": attempt}))
            return {"action": "mark_unhealthy", "attempts": attempt}

        ok = self.restart(report.module_id)
        verified = self.health_check(report.module_id)["healthy"] if ok else False
        return {"action": "restarted" if verified else "fallback",
                "attempts": attempt, "verified": verified}

    def _get(self, module_id):
        with self._lock:
            if module_id not in self._modules: raise KeyError(f"unknown module: {module_id}")
            return self._modules[module_id]

    def _persist(self, module_id):
        r = self._modules[module_id]
        self.state_store.set_module(module_id, {
            "manifest": r.manifest.to_dict(), "status": r.status, "failures": r.failures
        })
