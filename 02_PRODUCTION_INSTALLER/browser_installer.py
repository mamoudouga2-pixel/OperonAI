from pathlib import Path
from artifact_manager.validator import ensure_component_artifact
from artifact_manager.archive_security import safe_extract
class BrowserInstaller:
    def __init__(self,paths): self.paths=paths
    def install(self,component):
        profile=self.paths.browser/'automation_profile'; profile.mkdir(parents=True,exist_ok=True)
        if component.metadata.get('local_artifact') or component.download_url:
            artifact=ensure_component_artifact(component,self.paths.cache)
            runtime_dir=self.paths.browser/'runtime'; runtime_dir.mkdir(parents=True,exist_ok=True)
            if artifact.suffix.lower() in {'.zip','.tar','.gz','.tgz'}: safe_extract(artifact,runtime_dir)
            else: (runtime_dir/artifact.name).write_bytes(artifact.read_bytes())
        binary=component.metadata.get('binary')
        if binary and not Path(binary).exists(): raise RuntimeError('Browser binary missing after installation')
        (profile/'profile.marker').write_text('controlled-profile\n',encoding='utf-8')
        return True
