"""Task plan/result store (spec 8.4 TASK_MEMORY)."""


class TaskStore:
    def __init__(self):
        self.data = {}

    def upsert(self, memory):
        self.data[memory["memory_id"]] = dict(memory)
        return memory

    def get(self, memory_id):
        item = self.data.get(memory_id)
        return dict(item) if item is not None else None

    def delete(self, memory_id):
        self.data.pop(memory_id, None)

    def for_task(self, task_id):
        return [dict(v) for v in self.data.values() if v.get("task_id") == task_id]
