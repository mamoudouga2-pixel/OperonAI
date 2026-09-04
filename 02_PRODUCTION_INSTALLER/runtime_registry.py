class RuntimeRegistry:
    def __init__(self,adapters=None): self.adapters=adapters or {}
    def register(self,name,adapter): self.adapters[name]=adapter
    def get(self,name): return self.adapters[name]
