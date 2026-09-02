from datetime import datetime, timezone
from threading import RLock
from communication.protocols import Event
from task_manager.model import ALLOWED_TRANSITIONS, Task

class TaskManager:
    def __init__(self, event_bus, state_store, error_handler, config):
        self.event_bus, self.state_store, self.error_handler, self.config = event_bus, state_store, error_handler, config
        self._tasks, self._lock = {}, RLock()

    def create_task(self, description, metadata=None):
        task = Task.create(description, metadata)
        with self._lock: self._tasks[task.task_id] = task; self._persist(task)
        self.event_bus.publish(Event("task.created", task.to_dict(), task.task_id))
        return task

    def get_task(self, task_id):
        with self._lock:
            if task_id not in self._tasks: raise KeyError(f"unknown task: {task_id}")
            return self._tasks[task_id]

    def transition(self, task_id, new_state):
        task = self.get_task(task_id)
        if new_state not in ALLOWED_TRANSITIONS: raise ValueError("invalid state")
        old = task.state
        if new_state not in ALLOWED_TRANSITIONS[old]:
            self.error_handler.record("INVALID_STATE_TRANSITION", f"{old}->{new_state}", {"task_id": task_id})
            raise ValueError(f"invalid transition: {old}->{new_state}")
        with self._lock:
            task.state = new_state
            task.updated_at = datetime.now(timezone.utc).isoformat()
            self._persist(task)
        self.event_bus.publish(Event("task.state_changed",
                                     {"task_id":task_id,"from":old,"to":new_state}, task_id))
        return task

    def update_task(self, task_id, **metadata):
        task = self.get_task(task_id)
        with self._lock:
            task.metadata.update(metadata)
            task.updated_at = datetime.now(timezone.utc).isoformat()
            self._persist(task)
        return task

    def cancel_task(self, task_id): return self.transition(task_id, "CANCELLED")
    def complete_task(self, task_id): return self.transition(task_id, "SUCCESS")
    def timeout_task(self, task_id): return self.transition(task_id, "TIMEOUT")
    def recover_task(self, task_id): return self.transition(task_id, "RECOVERING")

    def fail_task(self, task_id, reason=""):
        self.update_task(task_id, failure_reason=reason)
        return self.transition(task_id, "FAILED")

    def increment_retry(self, task_id):
        task = self.get_task(task_id)
        with self._lock:
            if task.retry_count >= self.config.max_task_retries:
                raise RuntimeError("task retry budget exhausted")
            task.retry_count += 1
            self._persist(task)
            return task.retry_count

    def _persist(self, task): self.state_store.set_task(task.task_id, task.to_dict())
