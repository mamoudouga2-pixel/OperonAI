import json, os
from .defaults import DEFAULT_CONFIG

def generate_config(paths,manifest):
    cfg=json.loads(json.dumps(DEFAULT_CONFIG));
    for c in getattr(manifest,"components",manifest):
        if c.component_type.lower()=="runtime": cfg["runtime"].update(c.metadata.get("settings",{}))
        if c.component_type.lower()=="browser": cfg["browser"]["component_id"]=c.component_id
        if c.component_type.lower()=="model": cfg.setdefault("models",[]).append(c.component_id)
    cfg["paths"]={"app":str(paths.app),"runtime":str(paths.runtime),"models":str(paths.models),"browser":str(paths.browser),"user_data":str(paths.user_data)}
    paths.config.write_text(json.dumps(cfg,indent=2),encoding='utf-8'); return cfg
