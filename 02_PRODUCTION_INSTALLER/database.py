import sqlite3
from pathlib import Path
class Database:
    def __init__(self,path): self.path=Path(path)
    def initialize(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS installer_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
            db.commit()
    def backup(self,path):
        import shutil; shutil.copy2(self.path,path)
