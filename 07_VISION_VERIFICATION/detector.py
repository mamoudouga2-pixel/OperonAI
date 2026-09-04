import hashlib
import json

from events import default_bus, LOOP_DETECTED


class LoopDetectedError(RuntimeError):
    """Subclasses RuntimeError so existing `except RuntimeError` /
    `assertRaisesRegex(RuntimeError, "LOOP_DETECTED")` call sites keep working."""

    def __init__(self, signature, count):
        super().__init__(f"LOOP_DETECTED: signature {signature} repeated {count} times")
        self.signature = signature
        self.count = count


class LoopDetector:
    """Repeated-action loop detection (spec 7.19)."""

    def __init__(self, limit=3, event_bus=None):
        self.limit = limit
        self.seen = {}
        self.event_bus = event_bus or default_bus

    def observe(self, action, target, state, outcome):
        raw = json.dumps([action, target, state, outcome], sort_keys=True, default=str).encode()
        sig = hashlib.sha256(raw).hexdigest()
        self.seen[sig] = self.seen.get(sig, 0) + 1
        if self.seen[sig] > self.limit:
            self.event_bus.emit(LOOP_DETECTED, signature=sig, count=self.seen[sig],
                                 action=str(action), target=str(target))
            raise LoopDetectedError(sig, self.seen[sig])
        return sig

    def reset(self):
        self.seen.clear()
