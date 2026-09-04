from __future__ import annotations
import subprocess, time, os
class ProcessManager:
    def __init__(self): self.processes={}
    def start(self,name,cmd,cwd=None,env=None,hidden=False):
        existing=self.processes.get(name)
        if existing and existing.poll() is None:return existing
        p=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=subprocess.DEVNULL if hidden else subprocess.PIPE,stderr=subprocess.DEVNULL if hidden else subprocess.PIPE,text=True)
        self.processes[name]=p; return p
    def is_running(self,name):
        p=self.processes.get(name); return bool(p and p.poll() is None)
    def stop(self,name,timeout=5,force=True):
        p=self.processes.get(name)
        if not p:return True
        if p.poll() is not None:return True
        p.terminate()
        try:p.wait(timeout)
        except subprocess.TimeoutExpired:
            if not force:return False
            p.kill(); p.wait(timeout=max(timeout,1))
        return p.poll() is not None
