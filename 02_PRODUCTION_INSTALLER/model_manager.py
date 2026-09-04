from .model_registry import ModelRegistry
from .model_downloader import ModelDownloader
from .model_validator import validate_registration
from runtime_setup.ollama_adapter import OllamaAdapter
class ModelManager:
    def __init__(self,paths): self.paths=paths; self.registry=ModelRegistry(paths.models/"registry.json"); self.runtime=OllamaAdapter(paths.runtime/"ollama")
    def install(self,component):
        if not self.runtime.health_check().get('healthy') and not self.runtime.start(): raise RuntimeError("Local model runtime unavailable")
        name=component.metadata.get("model_name") or component.metadata.get("ollama_model")
        if not name: raise ValueError(f"No model_name declared for {component.component_id}")
        try:self.runtime.pull_model(name)
        except Exception as e:
            if component.metadata.get("fallback_model"): self.runtime.pull_model(component.metadata["fallback_model"]); name=component.metadata["fallback_model"]
            else: raise
        reg={"model_id":component.component_id,"runtime":"local","artifact_id":component.component_id,"version":component.version,"capabilities":component.metadata.get("capabilities",[]),"minimum_ram_gb":component.metadata.get("minimum_ram_gb"),"minimum_vram_gb":component.metadata.get("minimum_vram_gb"),"model_name":name}
        validate_registration(reg); self.registry.register(component.component_id,reg); return True
