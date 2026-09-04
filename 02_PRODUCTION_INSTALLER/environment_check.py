import os, shutil
from installer_engine.architecture import platform_contract

def check(paths):
    return {"platform":platform_contract(),"python":True,"disk_free":shutil.disk_usage(paths.base).free,"directories":paths.base.exists()}
