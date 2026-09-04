"""Default capture provider (spec 7.2, 7.6).

``ScreenCapture``/``WindowCapture`` only depend on the small provider
protocol (``capture_screen`` / ``capture_window``) -- exactly like the
adapter-based vision design in 7.6, no specific backend is a hard
dependency. ``DefaultDesktopProvider`` is one concrete implementation,
built on Pillow's ``ImageGrab`` because Pillow is already a project
dependency (no new package required).

Platform support (this is ``ImageGrab``'s own documented behavior, not a
limitation added here): native on Windows and macOS; on Linux it requires
an active X11/Wayland-XWayland display plus one of ``scrot``/``maim``, or
``python-xlib`` installed. Headless CI/container environments without a
display will raise -- callers should catch that and either skip
screen-dependent steps or inject a different provider (see
``ScreenCapture``/``WindowCapture`` constructors).
"""
from __future__ import annotations
import io
import time


class CaptureUnavailableError(RuntimeError):
    """Raised when no display/backend is available to grab pixels from."""


class DefaultDesktopProvider:
    """Real screen/window pixel capture backed by ``PIL.ImageGrab``."""

    def capture_screen(self, request: dict | None = None) -> dict:
        request = request or {}
        try:
            from PIL import ImageGrab
        except ImportError as exc:  # pragma: no cover - Pillow is a hard dep here
            raise CaptureUnavailableError("Pillow is required for DefaultDesktopProvider") from exc
        try:
            bbox = request.get("bbox")  # (left, top, right, bottom), optional
            image = ImageGrab.grab(bbox=bbox, all_screens=request.get("all_screens", True))
        except Exception as exc:
            raise CaptureUnavailableError(
                "Screen capture failed -- no display available in this environment, "
                "or the platform needs an extra backend (see module docstring). "
                "Inject a different capture provider if this is a headless host."
            ) from exc
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return {
            "data": buf.getvalue(),
            "width": image.width,
            "height": image.height,
            "captured_at": time.time(),
            "format": "png",
        }

    def capture_window(self, request: dict | None = None) -> dict:
        """Best-effort window capture.

        True "grab this specific OS window by handle" is platform-specific
        (win32gui on Windows, Quartz on macOS, wmctrl/xdotool on X11) and is
        deliberately out of scope for this default provider, exactly as
        vision *models* are kept out of ``adapters/`` per 7.6 -- callers
        that need it should resolve the window's bounding box with a
        platform-specific locator and pass it as ``request['bbox']``; this
        provider then performs the pixel grab for that region.
        """
        request = request or {}
        bbox = request.get("bbox")
        if not bbox:
            raise CaptureUnavailableError(
                "capture_window requires request['bbox']=(left,top,right,bottom) resolved "
                "by a platform-specific window locator (win32gui / Quartz / wmctrl). "
                "DefaultDesktopProvider only performs the pixel grab, not window enumeration."
            )
        result = self.capture_screen({"bbox": bbox, "all_screens": False})
        result["window_id"] = request.get("window_id")
        return result
