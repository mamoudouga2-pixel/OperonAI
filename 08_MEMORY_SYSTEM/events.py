"""
Memory subsystem events (spec section 8.28).

The memory module never talks to other Part-0X modules directly; it
emits events on a small in-process bus. Part 01 (Core) or the Interface
layer is expected to subscribe. This keeps the memory package usable
standalone (e.g. in unit tests) without a running multi-agent runtime.
"""

from collections import defaultdict


# --- Event names -----------------------------------------------------
MEMORY_WRITE_REQUESTED = "MEMORY_WRITE_REQUESTED"
MEMORY_STORED = "MEMORY_STORED"
MEMORY_UPDATED = "MEMORY_UPDATED"
MEMORY_RETRIEVED = "MEMORY_RETRIEVED"
MEMORY_EXPIRED = "MEMORY_EXPIRED"
MEMORY_FORGET_REQUESTED = "MEMORY_FORGET_REQUESTED"
MEMORY_DELETED = "MEMORY_DELETED"
MEMORY_DELETE_VERIFIED = "MEMORY_DELETE_VERIFIED"
MEMORY_CONFLICT_DETECTED = "MEMORY_CONFLICT_DETECTED"
MEMORY_CONSOLIDATION_STARTED = "MEMORY_CONSOLIDATION_STARTED"
MEMORY_CONSOLIDATION_COMPLETED = "MEMORY_CONSOLIDATION_COMPLETED"
MEMORY_STORAGE_FAILED = "MEMORY_STORAGE_FAILED"

ALL_EVENTS = {
    MEMORY_WRITE_REQUESTED,
    MEMORY_STORED,
    MEMORY_UPDATED,
    MEMORY_RETRIEVED,
    MEMORY_EXPIRED,
    MEMORY_FORGET_REQUESTED,
    MEMORY_DELETED,
    MEMORY_DELETE_VERIFIED,
    MEMORY_CONFLICT_DETECTED,
    MEMORY_CONSOLIDATION_STARTED,
    MEMORY_CONSOLIDATION_COMPLETED,
    MEMORY_STORAGE_FAILED,
}


class EventBus:
    """Minimal synchronous pub/sub bus.

    Deliberately dependency-free: Part 08 must keep working even if the
    full multi-agent runtime (Part 01 Core) is not present, e.g. during
    unit testing or when the memory package is reused standalone.
    """

    def __init__(self):
        self._subscribers = defaultdict(list)
        self._history = []

    def subscribe(self, event_name, handler):
        self._subscribers[event_name].append(handler)
        return handler

    def unsubscribe(self, event_name, handler):
        if handler in self._subscribers.get(event_name, []):
            self._subscribers[event_name].remove(handler)

    def emit(self, event_name, **payload):
        if event_name not in ALL_EVENTS:
            raise ValueError(f"Unknown memory event: {event_name}")
        event = {"event": event_name, **payload}
        self._history.append(event)
        for handler in list(self._subscribers.get(event_name, [])):
            handler(event)
        return event

    def history(self, event_name=None):
        if event_name is None:
            return list(self._history)
        return [e for e in self._history if e["event"] == event_name]


# A process-wide default bus. Individual components may still construct
# their own EventBus() for isolation in tests.
default_bus = EventBus()
