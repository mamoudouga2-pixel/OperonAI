from .session import BrowserSession
from .context import SessionRegistry
from .lifecycle import SessionLifecycle
class BrowserController:
    def __init__(self,adapter,max_concurrent=4):
        self.adapter=adapter; self.registry=SessionRegistry(max_concurrent); self.lifecycle=SessionLifecycle(adapter,self.registry)
    def create_session(self,task_context):
        task_id=task_context.get("task_id")
        if not task_id: raise ValueError("task_id required")
        sid=task_context.get("session_id") or f"BROWSER-{len(self.registry.sessions)+1:03d}"
        return self.lifecycle.create(BrowserSession(sid,task_id))
    def close_session(self,sid): return self.lifecycle.close(sid)
    def health_check(self,sid): return self.adapter.health_check(sid)
