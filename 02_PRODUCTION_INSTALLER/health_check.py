from .ollama_adapter import OllamaAdapter

def aggregate_health(paths,manifest):
    runtime_ok=True; model_required=[]
    for c in getattr(manifest,"components",manifest):
        if c.component_type.lower()=="runtime": runtime_ok=OllamaAdapter(paths.runtime/"ollama").health_check().get('healthy',False) if c.metadata.get("runtime_name","ollama")=="ollama" else True
        if c.component_type.lower()=="model": model_required.append(c)
    return runtime_ok and paths.user_data.exists() and paths.browser.exists()
