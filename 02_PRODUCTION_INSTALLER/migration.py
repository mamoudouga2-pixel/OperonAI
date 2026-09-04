import sqlite3, shutil
from pathlib import Path
class Migration:
    def __init__(self,db_path): self.db_path=Path(db_path)
    def backup(self,backup_path):
        backup=Path(backup_path); backup.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(self.db_path,backup); return backup
    def run_transaction(self,sql,validate=None):
        with sqlite3.connect(self.db_path) as db:
            db.execute('BEGIN')
            try:
                db.executescript(sql)
                if validate: validate(db)
                db.commit()
            except Exception:
                db.rollback(); raise
    def restore(self,backup_path): shutil.copy2(backup_path,self.db_path)
    def run(self,sql): return self.run_transaction(sql)
