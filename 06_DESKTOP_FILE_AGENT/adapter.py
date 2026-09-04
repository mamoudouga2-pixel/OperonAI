from abc import ABC, abstractmethod

from errors import E
from evidence import EvidenceStore


class DesktopAdapter(ABC):
    """6.29 — platform differences (Windows/macOS/Linux) live entirely
    behind this contract; upper layers never touch a platform API directly.
    """

    @abstractmethod
    def launch(self, app_path): ...

    @abstractmethod
    def screenshot(self): ...

    @abstractmethod
    def click(self, target): ...

    @abstractmethod
    def type(self, text): ...

    @abstractmethod
    def focus(self, app_id): ...


class MockAdapter(DesktopAdapter):
    """Deterministic in-memory adapter for tests/CI (no real display).

    A `future_adapters/` package is where real platform implementations
    (e.g. a pyautogui-based adapter) are added; they must satisfy the same
    DesktopAdapter contract so the rest of Part 06 never changes.
    """

    def __init__(self, launchable=None, fail_screenshot=False):
        self.launchable = set(launchable or [])
        self.fail_screenshot = fail_screenshot
        self.clicks = []
        self.typed = []

    def launch(self, app_path):
        if app_path not in self.launchable:
            return None
        return {"app": app_path, "window_id": f"WIN-{app_path}"}

    def screenshot(self):
        if self.fail_screenshot:
            raise RuntimeError(E.SCREEN_OBSERVATION_FAILED)
        return b"\x89PNG-mock-bytes"

    def click(self, target):
        self.clicks.append(target)
        return True

    def type(self, text):
        self.typed.append(text)
        return True

    def focus(self, app_id):
        if app_id not in self.launchable:
            return None
        return {"app": app_id, "window_id": f"WIN-{app_id}"}


class ScreenObserver:
    """6.18 SCREEN OBSERVATION — capture only; interpretation is Part 07."""

    def __init__(self, adapter, evidence=None):
        self.adapter = adapter
        self.evidence = evidence or EvidenceStore()

    def capture(self):
        import hashlib
        try:
            raw = self.adapter.screenshot()
        except Exception:
            raise RuntimeError(E.SCREEN_OBSERVATION_FAILED)
        h = hashlib.sha256(raw).hexdigest() if isinstance(raw, (bytes, bytearray)) else None
        rec = self.evidence.create(kind="SCREEN_OBSERVATION", content_hash=h)
        return {"evidence_id": rec["evidence_id"], "raw": raw, "hash": h}
