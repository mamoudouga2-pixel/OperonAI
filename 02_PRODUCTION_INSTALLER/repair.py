import shutil, os
from pathlib import Path
from .scanner import RepairScanner
from .repair_report import RepairReport
from .redownload import Redownloader
class RepairSystem:
    def __init__(self,paths): self.paths=paths
    def repair(self,component_files):
        root=self.paths.app; report=RepairReport(); issues=RepairScanner().scan(root,{k:v.get("sha256") for k,v in component_files.items()})
        for issue in issues:
            rel=issue["path"]
            spec=component_files[rel]
            try:
                dest=root/rel; dest.parent.mkdir(parents=True,exist_ok=True); tmp=dest.with_suffix(dest.suffix+'.repair')
                Redownloader().fetch(spec["url"],tmp,spec.get("sha256"),spec.get("signature"),spec.get("public_key")); os.replace(tmp,dest); report.repaired.append(rel)
            except Exception: report.failed.append(rel)
        return report
