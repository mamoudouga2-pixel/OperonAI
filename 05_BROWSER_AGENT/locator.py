from .semantic import SemanticLocator
from .fallback import LocatorFallback
from .confidence import ConfidenceGate

class LocatorEngine:
    def __init__(self):
        self.f=LocatorFallback(SemanticLocator(),ConfidenceGate())
    def find(self,target,find):
        return self.f.resolve(target,find)
