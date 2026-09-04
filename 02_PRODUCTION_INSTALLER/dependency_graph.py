from common.errors import DependencyConflict
class DependencyGraph:
    def __init__(self,components): self.nodes={c.component_id:c for c in components}
    def topo_sort(self):
        temp,set_done=set(),set(); out=[]
        def visit(cid):
            if cid in set_done:return
            if cid in temp: raise DependencyConflict(f"Dependency cycle detected at {cid}")
            if cid not in self.nodes: raise DependencyConflict(f"Missing dependency: {cid}")
            temp.add(cid)
            for dep in self.nodes[cid].dependencies: visit(dep)
            temp.remove(cid); set_done.add(cid); out.append(self.nodes[cid])
        for cid in self.nodes: visit(cid)
        return out
