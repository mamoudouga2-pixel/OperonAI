from __future__ import annotations
import json, shutil, subprocess, time, platform
from pathlib import Path
from urllib.request import Request,urlopen
from .runtime_adapter import RuntimeAdapter
from .process_manager import ProcessManager
from artifact_manager.validator import ensure_component_artifact, validate_file
from artifact_manager.archive_security import safe_extract
from common.errors import InstallationError

class OllamaAdapter(RuntimeAdapter):
    def __init__(self,root,process_manager=None):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True); self.pm=process_manager or ProcessManager(); self.bin=self._discover_bin(); self.base_url='http://127.0.0.1:11434'; self.version_cache=None
    def _discover_bin(self): return shutil.which('ollama') or str(self.root/'ollama')
    def discover(self):
        p=shutil.which('ollama')
        return p or (Path(self.root/'ollama').exists())
    def resolve(self,component): return component
    def install(self,component):
        artifact=ensure_component_artifact(component,self.root.parent/'cache')
        target_dir=self.root/'active'; target_dir.mkdir(parents=True,exist_ok=True)
        if artifact.suffix.lower() in {'.zip','.tar','.gz','.tgz'}: safe_extract(artifact,target_dir)
        else:
            target=target_dir/'ollama'; target.write_bytes(artifact.read_bytes()); target.chmod(0o755)
        candidates=list(target_dir.rglob('ollama'))
        self.bin=str(candidates[0]) if candidates else self._discover_bin()
        if not Path(self.bin).exists() and not shutil.which('ollama'): raise InstallationError('Ollama binary missing','RUN_INSTALL_FAILED')
        return True
    def configure(self,settings):
        self.base_url=settings.get('base_url',self.base_url); return True
    def _api(self,path,method='GET',payload=None,timeout=15):
        data=json.dumps(payload).encode() if payload is not None else None
        req=Request(self.base_url+path,data=data,method=method,headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=timeout) as r:
            raw=r.read().decode(); return json.loads(raw) if raw else {}
    def start(self):
        if self.health_check()['healthy']: return True
        if not Path(self.bin).exists() and not shutil.which('ollama'): return False
        try:self.pm.start('ollama',[self.bin,'serve'],hidden=True)
        except OSError:return False
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            if self.health_check()['healthy']:return True
            time.sleep(.5)
        return False
    def stop(self): return self.pm.stop('ollama',timeout=5,force=True)
    def restart(self): return self.stop() and self.start()
    def get_version(self):
        try:
            v=self._api('/api/version').get('version'); self.version_cache=v; return v
        except Exception:return None
    def installed_models(self):
        try:return self._api('/api/tags').get('models',[])
        except Exception:return []
    def pull_model(self,name): return self._api('/api/pull','POST',{'name':name,'stream':False},timeout=3600)
    def chat(self,model,prompt): return self._api('/api/generate','POST',{'model':model,'prompt':prompt,'stream':False},timeout=120)
    def inference_available(self,model=None):
        models=self.installed_models(); names={m.get('name') for m in models if isinstance(m,dict)}
        if model and model not in names:return False
        return bool(names) or model is None
    def health_check(self,model=None):
        try:
            ver=self.get_version(); endpoint=ver is not None; infer=self.inference_available(model)
            return {'healthy':bool(endpoint and infer),'runtime_version':ver,'endpoint_available':endpoint,'inference_available':infer}
        except Exception as e:return {'healthy':False,'runtime_version':None,'endpoint_available':False,'inference_available':False,'error':str(e)}
    def repair(self,component):
        self.stop(); return self.install(component) and self.start()
    def uninstall(self,managed_exclusively=True):
        if not managed_exclusively:return False
        self.stop(); import shutil as _s; _s.rmtree(self.root,ignore_errors=True); return True
