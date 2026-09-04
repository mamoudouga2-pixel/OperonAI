from events import default_bus, VISION_CAPTURED
from .providers import DefaultDesktopProvider


class WindowCapture:
    def __init__(self, provider=None, event_bus=None):
        self.provider = provider or DefaultDesktopProvider()
        self.event_bus = event_bus or default_bus

    def capture(self, request=None):
        request = request or {}
        result = self.provider.capture_window(request)
        self.event_bus.emit(VISION_CAPTURED, source="desktop", kind="window", request=request)
        return result
