from threading import RLock
from communication.protocols import Event

class ApplicationController:
    STATES = {"STOPPED","RUNNING","PAUSED","SHUTTING_DOWN"}

    def __init__(self, module_manager, task_manager, event_bus, health_monitor, state_store):
        self.module_manager, self.task_manager = module_manager, task_manager
        self.event_bus, self.health_monitor, self.state_store = event_bus, health_monitor, state_store
        self._state = state_store.get_application("state", "STOPPED")
        if self._state not in self.STATES: self._state = "STOPPED"
        self._lock = RLock()

    @property
    def state(self):
        with self._lock: return self._state

    def start(self):
        with self._lock:
            if self._state == "RUNNING": return
            if self._state == "SHUTTING_DOWN": raise RuntimeError("shutdown in progress")
            self._state = "RUNNING"; self._persist()
        self.event_bus.publish(Event("application.started", {}))

    def pause(self):
        with self._lock:
            if self._state != "RUNNING": raise RuntimeError("application must be RUNNING")
            self._state = "PAUSED"; self._persist()
        self.event_bus.publish(Event("application.paused", {}))

    def resume(self):
        with self._lock:
            if self._state != "PAUSED": raise RuntimeError("application must be PAUSED")
            self._state = "RUNNING"; self._persist()
        self.event_bus.publish(Event("application.resumed", {}))

    def shutdown(self):
        with self._lock:
            if self._state == "STOPPED": return
            self._state = "SHUTTING_DOWN"; self._persist()
        for module_id in self.module_manager.list_modules():
            self.module_manager.stop(module_id)
        with self._lock:
            self._state = "STOPPED"; self._persist()
        self.event_bus.publish(Event("application.stopped", {}))

    def _persist(self): self.state_store.set_application("state", self._state)
