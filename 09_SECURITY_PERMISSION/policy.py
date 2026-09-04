class PermissionPolicy:
    def __init__(self,capabilities=None):self.capabilities=capabilities or {}
    def has_capability(self,worker,cap):return cap in self.capabilities.get(worker,set())
