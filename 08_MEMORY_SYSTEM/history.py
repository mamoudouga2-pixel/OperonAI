"""Append-only per-task event log (used for audit and debugging)."""


class TaskHistory:
    def __init__(self):
        self.data = {}

    def append(self, task_id, event):
        self.data.setdefault(task_id, []).append(dict(event))

    def get(self, task_id):
        return list(self.data.get(task_id, []))

    def clear(self, task_id):
        self.data.pop(task_id, None)
