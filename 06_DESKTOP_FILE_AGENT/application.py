from errors import E


class ApplicationLauncher:
    def __init__(self, security_gate, adapter, desktop, evidence=None):
        self.security = security_gate
        self.adapter = adapter
        self.desktop = desktop
        self.evidence = evidence

    def launch(self, sid, app_id):
        """Resolve app_id -> trusted path via the security registry (never
        an arbitrary/model-supplied path), launch it, then verify a window
        actually came up before reporting success (6.15)."""
        path = self.security.application(app_id)
        window = self.adapter.launch(path)
        if not window:
            raise RuntimeError(E.WINDOW_NOT_FOUND)
        self.desktop.set_window(sid, window, app_id)
        if self.evidence is not None:
            self.evidence.create(kind="APPLICATION_LAUNCHED", target_ref=app_id, result_ref=str(window))
        return window
