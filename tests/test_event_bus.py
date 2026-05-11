"""Tests for the thread-safe EventBus used by the preview server."""

from __future__ import annotations

import contextlib
import threading
import time

from resume_md._preview.event_bus import EventBus


def test_single_subscriber_receives_published_event() -> None:
    bus = EventBus()
    with bus.subscribe() as queue:
        bus.publish({"type": "reloaded"})
        event = queue.get(timeout=1.0)
    assert event == {"type": "reloaded"}


def test_multiple_subscribers_each_get_every_event() -> None:
    bus = EventBus()
    with bus.subscribe() as q1, bus.subscribe() as q2:
        bus.publish({"type": "reloaded", "n": 1})
        bus.publish({"type": "reloaded", "n": 2})
        assert q1.get(timeout=1.0) == {"type": "reloaded", "n": 1}
        assert q1.get(timeout=1.0) == {"type": "reloaded", "n": 2}
        assert q2.get(timeout=1.0) == {"type": "reloaded", "n": 1}
        assert q2.get(timeout=1.0) == {"type": "reloaded", "n": 2}


def test_unsubscribed_queue_stops_receiving() -> None:
    bus = EventBus()
    sub = bus.subscribe().__enter__()
    bus.publish({"type": "a"})
    assert sub.get(timeout=1.0) == {"type": "a"}
    bus.unsubscribe(sub)
    bus.publish({"type": "b"})
    assert sub.empty()


def test_subscriber_count_drops_after_context_exit() -> None:
    bus = EventBus()
    assert bus.subscriber_count() == 0
    with bus.subscribe():
        assert bus.subscriber_count() == 1
    assert bus.subscriber_count() == 0


def test_concurrent_publishers_do_not_lose_events() -> None:
    bus = EventBus()
    n_publishers = 10
    n_events_each = 50
    expected_total = n_publishers * n_events_each

    def publisher(idx: int) -> None:
        for i in range(n_events_each):
            bus.publish({"type": "x", "publisher": idx, "i": i})

    with bus.subscribe() as q:
        threads = [threading.Thread(target=publisher, args=(i,)) for i in range(n_publishers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        received = []
        deadline = time.monotonic() + 3.0
        while len(received) < expected_total and time.monotonic() < deadline:
            with contextlib.suppress(Exception):
                received.append(q.get(timeout=0.1))
        assert len(received) == expected_total
