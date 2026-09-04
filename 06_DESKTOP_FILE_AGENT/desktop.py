from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from errors import E


@dataclass
class Session:
    session_id: str
    task_id: str
    status: str = "READY"
    active_window: object = None
    focused_application: object = None
    permissions: tuple = ()
    started_at: str = ""

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return asdict(self)


class DesktopController:
    def __init__(self):
        self.sessions = {}

    def create(self, task_id, session_id=None):
        sid = session_id or f"DESKTOP-{len(self.sessions) + 1:03d}"
        if sid in self.sessions:
            raise RuntimeError(E.DESKTOP_SESSION_FAILED)
        s = Session(sid, task_id)
        self.sessions[sid] = s
        return s

    def close(self, sid):
        return bool(self.sessions.pop(sid, None))

    def _get(self, sid):
        if sid not in self.sessions:
            raise RuntimeError(E.DESKTOP_SESSION_FAILED)
        return self.sessions[sid]

    # ---------------------------------------------------- window state --
    def set_window(self, sid, window, app_id):
        """6.16 — record the currently active window/focused application
        for this session (called after a launch or a successful focus)."""
        s = self._get(sid)
        s.active_window = window
        s.focused_application = app_id
        return s

    def require_window(self, sid, expected):
        s = self._get(sid)
        if s.active_window != expected:
            raise RuntimeError(E.WINDOW_NOT_FOUND)
        return True

    def verify_foreground(self, sid, expected_app):
        """6.16 — before sending input, confirm the expected application is
        actually the one focused, to prevent input going to the wrong app."""
        s = self._get(sid)
        if s.focused_application != expected_app:
            raise RuntimeError(E.WINDOW_NOT_FOUND)
        return True

    def recover_focus(self, sid, adapter, expected_app, max_attempts=1):
        """6.16 — safe, bounded recovery when focus is lost: ask the
        platform adapter to refocus the expected application."""
        for _ in range(max_attempts):
            window = adapter.focus(expected_app)
            if window:
                return self.set_window(sid, window, expected_app)
        raise RuntimeError(E.WINDOW_NOT_FOUND)
