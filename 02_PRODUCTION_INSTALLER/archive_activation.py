from pathlib import Path
from .atomic import AtomicActivation
class ArchiveActivation:
    def __init__(self,paths): self.atomic=AtomicActivation(paths.current,paths.staging,paths.base/'previous',paths.base/'failed')
    def activate(self,health_ok=True):
        if not health_ok: self.atomic.mark_failed(); return False
        self.atomic.activate(); return True
    def rollback(self):
        if not self.atomic.previous.exists(): return False
        import shutil,os
        if self.atomic.current.exists(): shutil.rmtree(self.atomic.current)
        os.replace(self.atomic.previous,self.atomic.current); return True
