from pathlib import Path
import shutil, os
from installer_engine.atomic import AtomicActivation
from common.errors import InstallerError
class TransactionalUpdate:
    def __init__(self,paths,journal=None):
        self.paths=paths; self.journal=journal; self.previous=paths.base/'previous'; self.failed=paths.base/'failed'
        self.atomic=AtomicActivation(paths.current,paths.staging,self.previous,self.failed)
    def stage_from(self,source):
        if self.paths.staging.exists(): shutil.rmtree(self.paths.staging)
        shutil.copytree(Path(source),self.paths.staging)
        if self.journal:self.journal.append('STAGING_COMPLETED')
    def activate(self):
        self.atomic.activate();
        if self.journal:self.journal.append('ACTIVATION_COMPLETED')
    def rollback(self):
        if not self.previous.exists(): raise InstallerError('No previous version','UPD_ROLLBACK_FAILED')
        if self.paths.current.exists(): shutil.rmtree(self.paths.current)
        os.replace(self.previous,self.paths.current)
        if self.journal:self.journal.append('ROLLBACK_COMPLETED')
