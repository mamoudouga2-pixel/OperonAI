from threading import RLock
from typing import Callable, Any
import json
from communication.protocols import Event
from configuration.config import CoreConfig

Handler = Callable[[Event], Any]

class EventBus:
    def __init__(self, config: CoreConfig):
        self.config = config
        self._handlers: dict[str, list[Handler]] = {}
        self._lock = RLock()

    def subscribe(self, event_type: str, handler: Handler) -> None:
        if not event_type or not callable(handler):
            raise ValueError("valid event_type and callable handler required")
        with self._lock:
            bucket = self._handlers.setdefault(event_type, [])
            if handler not in bucket:
                bucket.append(handler)
            if len(bucket) > self.config.event_handler_limit:
                bucket.pop()
                raise RuntimeError("event handler limit exceeded")

    def unsubscribe(self, event_type: str, handler: Handler) -> None:
        with self._lock:
            bucket = self._handlers.get(event_type, [])
            if handler in bucket:
                bucket.remove(handler)
            if not bucket:
                self._handlers.pop(event_type, None)

    def publish(self, event: Event) -> list[Any]:
        size = len(json.dumps(event.payload, ensure_ascii=False, default=str).encode())
        if size > self.config.event_payload_limit:
            raise ValueError("event payload exceeds configured limit")
        with self._lock:
            handlers = tuple(self._handlers.get(event.event_type, ()))
        results = []
        for handler in handlers:
            results.append(handler(event))
        return results
