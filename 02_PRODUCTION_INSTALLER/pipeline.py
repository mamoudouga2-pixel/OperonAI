from dataclasses import dataclass
from pathlib import Path
import shutil
from download_manager.downloader import Downloader
from download_manager.quarantine import Quarantine
from artifact_manager.validator import validate_file
from artifact_manager.archive_security import safe_extract
from common.errors import InstallerError,VerificationError
@dataclass
class PipelineContext:
    paths: object
    downloader: Downloader
    quarantine: Quarantine
class ComponentPipeline:
    def __init__(self,context): self.ctx=context
    def run(self,component,component_impl=None):
        if component.size_bytes:
            from .disk_space import estimate,require_space
            require_space(estimate(component.size_bytes,component.size_bytes//4,component.size_bytes//2,component.size_bytes,256*1024*1024,self.ctx.paths.base))
        # DISCOVER/RESOLVE/PREFLIGHT
        artifact=self._acquire(component)
        try: validate_file(artifact,component.sha256,component.signature,component.metadata.get('public_key'))
        except Exception as exc:
            self.ctx.quarantine.put(artifact,'VERIFICATION_FAILED',component.download_url,component.component_id); raise VerificationError(str(exc),'SEC_SIGNATURE_INVALID') from exc
        stage=self.ctx.paths.staging/component.component_id
        if stage.exists(): shutil.rmtree(stage)
        stage.mkdir(parents=True,exist_ok=True)
        if component.payload_type in {'zip','tar','archive'}: safe_extract(artifact,stage)
        else: shutil.copy2(artifact,stage/artifact.name)
        result=True if component_impl is None else component_impl.install(stage)
        if result is False: raise InstallerError('Component install failed','INS_COMPONENT_FAILED')
        health=True if component_impl is None else component_impl.health_check()
        if isinstance(health,dict): health=health.get('healthy',False)
        if not health: raise InstallerError('Component health check failed','UPD_HEALTH_FAILED')
        return stage
    def _acquire(self,component):
        if component.metadata.get('local_artifact'): return Path(component.metadata['local_artifact'])
        if not component.download_url: raise InstallerError('No artifact source','DL_SOURCE_UNAVAILABLE')
        dest=self.ctx.paths.cache/component.component_id/f'{component.component_id}-{component.version}.artifact'
        dest.parent.mkdir(parents=True,exist_ok=True)
        return self.ctx.downloader.download(component.download_url,dest,expected_size=component.size_bytes or None,expected_sha256=component.sha256)
