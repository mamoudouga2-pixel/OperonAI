from pathlib import Path
import shutil, os
from installer_engine.atomic import AtomicActivation
class StagedUpdate:
    def __init__(self,paths):
        self.paths=paths; self.previous=paths.base/'previous'; self.failed=paths.base/'failed'; self.atomic=AtomicActivation(paths.current,paths.staging,self.previous,self.failed)
    def stage(self,source=None):
        if self.paths.staging.exists(): shutil.rmtree(self.paths.staging)
        if source is None: source=self.paths.current
        shutil.copytree(Path(source),self.paths.staging,dirs_exist_ok=True); return self.paths.staging
    def activate(self,health_ok=True):
        if not health_ok: self.atomic.mark_failed(); return False
        self.atomic.activate(); return True
