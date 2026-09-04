from .compatibility import compatible
from common.errors import DependencyConflict
class Resolver:
    def __init__(self,components,app_version="1.1.0"): self.components=components; self.app_version=app_version
    def validate(self):
        for c in self.components:
            if not compatible(c,self.app_version): raise DependencyConflict(f"App version incompatible with {c.component_id}")
        return True
