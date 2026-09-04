import os
class ResourceMonitor:
    def __init__(self,profile,policy):self.profile=profile;self.policy=policy;self._active=0
    def acquire(self):
        if self._active>=self.policy.max_concurrent_tasks:raise RuntimeError("CONCURRENCY_LIMIT: task limit reached")
        self._active+=1
    def release(self):self._active=max(0,self._active-1)
    def snapshot(self):
        return {"ram_gb":self.profile.ram_gb,"vram_gb":self.profile.gpu.vram_gb,
                "active_tasks":self._active,"max_concurrent_tasks":self.policy.max_concurrent_tasks,
                "low_resource_mode":self.policy.low_resource(self.profile)}
    def pressure(self,ram_used_gb=0,vram_used_gb=0):
        return {"ram_pressure":ram_used_gb/max(self.policy.max_ram_gb,0.001),
                "vram_pressure":vram_used_gb/max(self.policy.max_vram_gb,0.001)}
