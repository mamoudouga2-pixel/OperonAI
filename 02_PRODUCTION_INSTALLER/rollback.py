import os,shutil
class Rollback:
    def __init__(self,paths): self.paths=paths; self.previous=paths.base/'previous'
    def execute(self):
        if not self.previous.exists(): return False
        if self.paths.current.exists(): shutil.rmtree(self.paths.current)
        os.replace(self.previous,self.paths.current); return True
