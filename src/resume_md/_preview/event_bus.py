"""Thread-safe in-process pub/sub used to fan rebuild events out to every
connected browser via Server-Sent Events.

Each subscriber gets its own bounded `queue.Queue`. Publishers iterate over
subscribers under a lock and `put_nowait` into each queue; a slow subscriber
that fills its queue drops events for itself only — it never blocks publishers
or other subscribers.
"""

from __future__ import annotations

import contextlib
import queue
import threading
from typing import Any

# Generous per-subscriber buffer. The events we publish are tiny (≤200 bytes)
# and browsers consume them as fast as the loopback interface can deliver,
# so this is effectively "never overflow under normal use."
_QUEUE_MAXSIZE = 512


class _Subscription:
    """Context manager wrapper for a subscriber queue."""

    def __init__(self, bus: EventBus, q: queue.Queue[dict[str, Any]]) -> None:
        self._bus = bus
        self._queue = q

    def __enter__(self) -> queue.Queue[dict[str, Any]]:
        return self._queue

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self._bus.unsubscribe(self._queue)


class EventBus:
    """Fan-out pub/sub for preview events.

    Events are arbitrary JSON-serializable dicts (typically
    ``{"type": "reloaded" | "build_error" | "pandoc_warning", ...}``).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: list[queue.Queue[dict[str, Any]]] = []

    def publish(self, event: dict[str, Any]) -> None:
        with self._lock:
            targets = list(self._subscribers)
        for q in targets:
            # Slow subscriber: drop this event for them and move on.
            with contextlib.suppress(queue.Full):
                q.put_nowait(event)

    def subscribe(self) -> _Subscription:
        q: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=_QUEUE_MAXSIZE)
        with self._lock:
            self._subscribers.append(q)
        return _Subscription(self, q)

    def unsubscribe(self, q: queue.Queue[dict[str, Any]]) -> None:
        with self._lock, contextlib.suppress(ValueError):
            self._subscribers.remove(q)

    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)
