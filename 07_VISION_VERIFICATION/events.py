"""Event bus for Part 07 (spec 7.22 EVENTS, 7.28 Integration Contract / Part 01 Core).

Every event name listed in the spec is defined here as a constant so callers
and Part 01 Core integration code share one source of truth instead of
hand-typed strings. ``EventBus`` is intentionally tiny (subscribe/emit) with
no external dependency, matching the rest of this package's style.

A process-wide default bus (``default_bus``) is provided so the other
modules in this package can emit events without every caller having to wire
a bus through every constructor. Callers that want isolated buses (e.g. in
tests, or multiple independent agents in one process) can construct their
own ``EventBus()`` and pass it in explicitly wherever this package accepts
an ``event_bus=`` argument.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List


VISION_CAPTURED = "VISION_CAPTURED"
VISION_ANALYSIS_STARTED = "VISION_ANALYSIS_STARTED"
VISION_ANALYSIS_COMPLETED = "VISION_ANALYSIS_COMPLETED"
EVIDENCE_CREATED = "EVIDENCE_CREATED"
EVIDENCE_REDACTED = "EVIDENCE_REDACTED"
VERIFICATION_STARTED = "VERIFICATION_STARTED"
VERIFICATION_VERIFIED = "VERIFICATION_VERIFIED"
VERIFICATION_FAILED = "VERIFICATION_FAILED"
VERIFICATION_UNCERTAIN = "VERIFICATION_UNCERTAIN"
ERROR_DETECTED = "ERROR_DETECTED"
RECOVERY_RECOMMENDED = "RECOVERY_RECOMMENDED"
LOOP_DETECTED = "LOOP_DETECTED"

ALL_EVENTS = frozenset({
    VISION_CAPTURED, VISION_ANALYSIS_STARTED, VISION_ANALYSIS_COMPLETED,
    EVIDENCE_CREATED, EVIDENCE_REDACTED,
    VERIFICATION_STARTED, VERIFICATION_VERIFIED, VERIFICATION_FAILED, VERIFICATION_UNCERTAIN,
    ERROR_DETECTED, RECOVERY_RECOMMENDED, LOOP_DETECTED,
})


class EventBus:
    """Minimal synchronous publish/subscribe bus.

    Handlers run synchronously in subscription order. A handler that raises
    does not stop other handlers or the caller of ``emit`` -- observability
    must never be able to break the underlying operation it is observing.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[dict], None]]] = {}
        self.history: List[dict] = []
        self.record_history = True

    def subscribe(self, event_name: str, handler: Callable[[dict], None]) -> None:
        if event_name not in ALL_EVENTS:
            raise ValueError(f"Unknown event name: {event_name!r}")
        self._subscribers.setdefault(event_name, []).append(handler)

    def emit(self, event_name: str, **payload: Any) -> dict:
        if event_name not in ALL_EVENTS:
            raise ValueError(f"Unknown event name: {event_name!r}")
        event = {
            "event": event_name,
            "emitted_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        if self.record_history:
            self.history.append(event)
        for handler in self._subscribers.get(event_name, ()):
            try:
                handler(event)
            except Exception:
                # Observability must never break the caller's control flow.
                continue
        return event


default_bus = EventBus()
