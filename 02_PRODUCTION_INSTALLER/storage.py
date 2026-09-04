from .directories import ensure
from .database import Database
class StorageSetup:
    def __init__(self,paths): self.paths=paths
    def prepare(self): ensure(self.paths); Database(self.paths.user_data/"worker.db").initialize(); return True
