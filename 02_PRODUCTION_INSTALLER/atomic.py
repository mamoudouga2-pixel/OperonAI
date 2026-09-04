from pathlib import Path
import os, shutil
class AtomicActivation:
    def __init__(self,current,staging,previous,failed): self.current=Path(current); self.staging=Path(staging); self.previous=Path(previous); self.failed=Path(failed)
    def activate(self):
        if not self.staging.exists(): raise RuntimeError('staging missing')
        if self.previous.exists(): shutil.rmtree(self.previous)
        if self.current.exists(): os.replace(self.current,self.previous)
        try: os.replace(self.staging,self.current)
        except Exception:
            if self.previous.exists() and not self.current.exists(): os.replace(self.previous,self.current)
            raise
    def mark_failed(self):
        if self.staging.exists():
            self.failed.mkdir(parents=True,exist_ok=True)
            target=self.failed/('failed-'+str(len(list(self.failed.iterdir()))))
            os.replace(self.staging,target)
