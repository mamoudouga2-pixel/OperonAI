"""
User preferences (spec 8.14 USER PREFERENCES).

Own namespace, versioned on overwrite, user can view/change/delete.
"""


class Preferences:
    def __init__(self, repo):
        self.repo = repo

    def set(self, memory):
        memory = dict(memory)
        memory["type"] = "PREFERENCE"
        memory.setdefault("namespace", "preferences")
        existing = self.repo.get(memory["memory_id"])
        memory["version"] = int(existing.get("version", 0)) + 1 if existing else 1
        return self.repo.save(memory)

    def get(self, memory_id):
        return self.repo.get(memory_id)

    def delete(self, memory_id):
        return self.repo.delete(memory_id)

    def list_for_scope(self, scope):
        return self.repo.search(scope, namespace="preferences")
