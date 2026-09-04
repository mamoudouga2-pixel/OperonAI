import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from capture.artifact_store import ArtifactStore
from capture.screen_capture import ScreenCapture
from capture.window_capture import WindowCapture
from capture.providers import CaptureUnavailableError
from events import EventBus, VISION_CAPTURED


class FakeProvider:
    def capture_screen(self, request):
        return {"data": b"PNGDATA", "width": 800, "height": 600, "format": "png"}

    def capture_window(self, request):
        if not request.get("bbox"):
            raise CaptureUnavailableError("no bbox")
        return {"data": b"PNGDATA", "width": 200, "height": 100, "format": "png",
                "window_id": request.get("window_id")}


class ArtifactStoreTests(unittest.TestCase):
    def test_save_read_delete_roundtrip(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            store = ArtifactStore(d + "/sub")
            path = store.save("a.bin", b"hello")
            self.assertTrue(store.exists("a.bin"))
            self.assertEqual(store.read("a.bin"), b"hello")
            self.assertTrue(store.delete("a.bin"))
            self.assertFalse(store.exists("a.bin"))

    def test_permission_controlled_paths(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            store = ArtifactStore(d + "/sub", dir_mode=0o700, file_mode=0o600)
            path = store.save("a.bin", b"x")
            self.assertEqual(oct(os.stat(store.root).st_mode & 0o777), "0o700")
            self.assertEqual(oct(os.stat(path).st_mode & 0o777), "0o600")

    def test_rejects_unsafe_names(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            store = ArtifactStore(d)
            with self.assertRaises(ValueError):
                store.save("../escape.bin", b"x")


class ScreenWindowCaptureTests(unittest.TestCase):
    def test_screen_capture_uses_injected_provider_and_emits_event(self):
        bus = EventBus()
        sc = ScreenCapture(provider=FakeProvider(), event_bus=bus)
        result = sc.capture({})
        self.assertEqual(result["width"], 800)
        self.assertEqual([e["event"] for e in bus.history], [VISION_CAPTURED])

    def test_window_capture_requires_bbox_from_caller(self):
        wc = WindowCapture(provider=FakeProvider())
        with self.assertRaises(CaptureUnavailableError):
            wc.capture({"window_id": "W1"})
        result = wc.capture({"window_id": "W1", "bbox": (0, 0, 100, 100)})
        self.assertEqual(result["window_id"], "W1")

    def test_default_provider_fails_clearly_without_a_display(self):
        # This sandbox is headless; assert the error is the documented,
        # catchable CaptureUnavailableError rather than an opaque crash.
        sc = ScreenCapture()
        with self.assertRaises(CaptureUnavailableError):
            sc.capture({})


if __name__ == "__main__":
    unittest.main()
