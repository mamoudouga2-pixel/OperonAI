class SessionLifecycle:
    def __init__(self,adapter,registry): self.adapter=adapter; self.registry=registry
    def create(self,session):
        self.registry.add(session)
        try:
            self.adapter.create_context(session.session_id)
            return session
        except Exception:
            self.registry.remove(session.session_id); raise
    def close(self,sid):
        try: self.adapter.close_context(sid)
        finally: self.registry.remove(sid)
