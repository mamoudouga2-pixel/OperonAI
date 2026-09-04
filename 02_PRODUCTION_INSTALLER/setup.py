from .ollama_adapter import OllamaAdapter
class RuntimeSetup:
    def __init__(self,paths): self.paths=paths; self.registry={"ollama":OllamaAdapter(paths.runtime/"ollama")}
    def adapter_for(self,component): return self.registry.get(component.metadata.get("runtime_name","ollama"))
    def install(self,component):
        a=self.adapter_for(component)
        if not a.install(component): raise RuntimeError(f"Failed to install runtime {component.component_id}")
        a.configure(component.metadata.get("settings",{}));
        if not a.start(): raise RuntimeError("Runtime health check failed after installation")
        return True
