class SessionRegistry:
    def __init__(self,max_concurrent=4): self.sessions={}; self.max_concurrent=max_concurrent
    def add(self,session):
        if len(self.sessions)>=self.max_concurrent: raise RuntimeError("PERMISSION_BLOCKED: concurrent session limit")
        if session.session_id in self.sessions: raise ValueError("duplicate session")
        self.sessions[session.session_id]=session
    def get(self,sid):
        if sid not in self.sessions: raise KeyError(sid)
        return self.sessions[sid]
    def remove(self,sid): return self.sessions.pop(sid,None)
