from abc import ABC,abstractmethod

class RuntimeAdapter(ABC):
    @abstractmethod
    def discover(self): ...
    @abstractmethod
    def install(self): ...
    @abstractmethod
    def load(self): ...
    @abstractmethod
    def unload(self): ...
    @abstractmethod
    def generate(self,prompt,**kwargs): ...
    @abstractmethod
    def health_check(self): ...
    @abstractmethod
    def metadata(self): ...

class BaseAdapter(RuntimeAdapter):
    def __init__(self,adapter_id,capabilities,*,ram_gb=0,vram_gb=0,context_budget=4096):
        if not isinstance(adapter_id,str) or not adapter_id.strip():raise ValueError("invalid adapter_id")
        caps=frozenset(str(x) for x in capabilities if str(x).strip())
        if not caps:raise ValueError("capabilities required")
        if min(float(ram_gb),float(vram_gb))<0 or int(context_budget)<1:raise ValueError("invalid requirements")
        self.adapter_id=adapter_id;self.capabilities=caps;self.ram_gb=float(ram_gb)
        self.vram_gb=float(vram_gb);self.context_budget=int(context_budget);self.loaded=False
    def discover(self):return self.metadata()
    def install(self):return True
    def load(self):self.loaded=True;return True
    def unload(self):self.loaded=False;return True
    def health_check(self):return self.loaded
    def metadata(self):return {"adapter_id":self.adapter_id,"capabilities":sorted(self.capabilities),
        "ram_gb":self.ram_gb,"vram_gb":self.vram_gb,"context_budget":self.context_budget}
    def generate(self,prompt,**kwargs):
        if not self.loaded:raise RuntimeError("runtime not loaded")
        if not isinstance(prompt,str) or not prompt.strip():raise ValueError("prompt required")
        return {"adapter_id":self.adapter_id,"output":prompt,"kwargs":dict(kwargs)}

class ReasoningLanguageAdapter(BaseAdapter):pass
class VisionAdapter(BaseAdapter):pass
class EmbeddingAdapter(BaseAdapter):pass
class LightweightFallbackAdapter(BaseAdapter):pass
class RemoteAdapter(BaseAdapter):
    def __init__(self,*a,**k):super().__init__(*a,**k)
