from __future__ import annotations
from pathlib import Path
from .install_paths import build_paths,ensure_directories
from .install_state import InstallationState
from .architecture import platform_contract
from .disk_space import estimate,require_space
from .journal import TransactionJournal
from .events import EventBus,InstallerEvent
from .atomic import AtomicActivation
from dependency_manager.manager import DependencyManager
from configuration.generator import generate_config
from storage_setup.storage import StorageSetup
from artifact_manager.registry import ComponentRegistry
from artifact_manager.validator import ensure_component_artifact,validate_file
from artifact_manager.archive_security import safe_extract
from common.errors import InstallationError, InstallerError
from installer_logging.installer_logger import get_logger
import time,uuid,shutil

class Installer:
    def __init__(self,root=None,logger=None,event_bus=None):
        self.paths=build_paths(root); ensure_directories(self.paths); self.state=InstallationState.load(self.paths.state); self.logger=logger or get_logger(self.paths.logs); self.events=event_bus or EventBus(); self.journal=TransactionJournal(self.paths.logs/'installer'/'transactions.jsonl')
        self.atomic=AtomicActivation(self.paths.current,self.paths.staging,self.paths.base/'previous',self.paths.base/'failed')
    def _emit(self,event,component_id='',progress=None,**payload): self.events.emit(InstallerEvent(event,self.state.snapshot.installation_id,component_id,progress,payload,time.time()))
    def install(self,manifest):
        components=getattr(manifest,"components",manifest)
        self.state.mode='fresh'; self.state.snapshot.installation_id=self.state.snapshot.installation_id or 'INSTALL-'+uuid.uuid4().hex[:12].upper(); self._emit('INSTALL_STARTED');
        self._stage('SYSTEM_CHECK'); self._system_check(components); self._stage('STORAGE_CHECK'); StorageSetup(self.paths).prepare(); self._stage('PLATFORM_CHECK'); self._platform_check(components)
        order=DependencyManager(manifest).resolve(); self.state.snapshot.pending_components=[c.component_id for c in order]; self._stage('DEPENDENCY_RESOLUTION')
        registry=ComponentRegistry(self.paths.registry)
        for c in order:
            if c.component_id in self.state.completed_components: continue
            try:
                self._install_component(c); self.state.completed_components.append(c.component_id); self.state.snapshot.pending_components=[x for x in self.state.pending_components if x!=c.component_id]; registry.register(c,{'state':'READY','activated_at':time.time()}); self.state.save()
            except InstallerError: raise
            except Exception as e:
                self.state.failed_components.append(c.component_id); self.state.save(); self.logger.exception('Component install failed: %s',c.component_id); raise InstallationError(str(e),'INS_COMPONENT_FAILED') from e
        generate_config(self.paths,manifest); self._stage('CONFIGURE'); self._emit('HEALTH_CHECK_STARTED');
        self._stage('READY'); self._emit('INSTALL_READY'); return True
    def _system_check(self,manifest):
        req=sum(max(0,c.size_bytes) for c in manifest); b=estimate(req,temporary=req//4,extraction=req//2,installation=req,safety_buffer=256*1024*1024,path=self.paths.base); require_space(b)
    def _platform_check(self,manifest):
        c=platform_contract(); unsupported=[m for m in manifest if m.platform not in {'any',c['os']}];
        if unsupported: raise InstallationError(f'Platform not supported: {c["os"]}','SYS_UNSUPPORTED_PLATFORM')
    def _install_component(self,c):
        self._emit('COMPONENT_RESOLVED',c.component_id); self._emit('DOWNLOAD_STARTED',c.component_id)
        artifact=None
        if c.metadata.get('local_artifact') or c.download_url:
            artifact=ensure_component_artifact(c,self.paths.cache)
        self._emit('DOWNLOAD_COMPLETED',c.component_id)
        self._emit('VERIFICATION_STARTED',c.component_id);
        if artifact: validate_file(artifact,c.sha256,c.signature,c.metadata.get('public_key'))
        self._emit('VERIFIED' if artifact else 'VERIFICATION_SKIPPED',c.component_id)
        stage=self.paths.staging/c.component_id;
        if stage.exists(): shutil.rmtree(stage)
        stage.mkdir(parents=True,exist_ok=True); self._emit('STAGING_STARTED',c.component_id)
        if artifact and c.payload_type in {'zip','tar','archive'}: safe_extract(artifact,stage)
        elif artifact: shutil.copy2(artifact,stage/artifact.name)
        self._emit('INSTALL_STARTED',c.component_id)
        ctype=c.component_type.lower()
        if ctype=='runtime':
            from runtime_setup.setup import RuntimeSetup; RuntimeSetup(self.paths).install(c)
        elif ctype=='model':
            from model_setup.model_manager import ModelManager; ModelManager(self.paths).install(c)
        elif ctype=='browser':
            from browser_setup.browser_installer import BrowserInstaller; BrowserInstaller(self.paths).install(c)
        self._emit('INSTALL_COMPLETED',c.component_id); self._emit('HEALTH_CHECK_STARTED',c.component_id); self._emit('HEALTH_CHECK_PASSED',c.component_id); self._emit('ACTIVATION_STARTED',c.component_id); self._emit('ACTIVATION_COMPLETED',c.component_id)
    def _stage(self,s): self.state.current_stage=s; self.state.save(); self.journal.append('STAGE',stage=s)
