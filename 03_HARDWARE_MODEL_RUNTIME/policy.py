from dataclasses import dataclass
@dataclass(frozen=True)
class PerformancePolicy:
    max_ram_gb:float
    max_vram_gb:float
    max_concurrent_tasks:int
    max_context_tokens:int
    low_resource_ram_threshold_gb:float=2.0
    allow_remote:bool=False
    def __post_init__(self):
        if min(self.max_ram_gb,self.max_vram_gb,self.max_concurrent_tasks,self.max_context_tokens)<0:raise ValueError("limits cannot be negative")
        if self.max_concurrent_tasks<1 or self.max_context_tokens<1:raise ValueError("invalid concurrency/context")
    def low_resource(self,profile):return profile.ram_gb<=self.low_resource_ram_threshold_gb
    def permits(self,a):
        if a.ram_gb>self.max_ram_gb or a.vram_gb>self.max_vram_gb:return False
        if "remote" in a.capabilities and not self.allow_remote:return False
        if a.context_budget>self.max_context_tokens:return False
        return True
