from .staged_update import StagedUpdate
from .rollback import Rollback
from .version_manager import is_newer
class Updater:
    def __init__(self,paths): self.paths=paths; self.staged=StagedUpdate(paths)
    def prepare(self,source=None): return self.staged.stage(source)
    def activate(self,health_ok=True): return self.staged.activate(health_ok)
    def rollback(self): return Rollback(self.paths).execute()
    def update(self,current,target,source,health_ok=True):
        """source must point to the fully-prepared new-version payload
        (e.g. an extracted/verified artifact directory) to be staged and
        atomically activated. Passing the current install as source would
        make this a no-op, so it is required rather than defaulted."""
        if not is_newer(current,target): return {"status":"not_newer"}
        self.prepare(source)
        if not self.activate(health_ok): return {"status":"activation_failed","version":target}
        return {"status":"staged_and_activated","version":target}
