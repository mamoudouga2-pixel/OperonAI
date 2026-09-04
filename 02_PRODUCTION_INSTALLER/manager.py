from .manifest import validate_manifest
from .dependency_graph import DependencyGraph
from .resolver import Resolver
class DependencyManager:
    def __init__(self,manifest): self.manifest=manifest; self.components=getattr(manifest,"components",manifest)
    def resolve(self): validate_manifest(self.components); Resolver(self.components).validate(); return DependencyGraph(self.components).topo_sort()
