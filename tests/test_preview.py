"""End-to-end tests for the live-reload preview server."""

from __future__ import annotations

import json
import socket
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from resume_md._preview.event_bus import EventBus
from resume_md._preview.server import LiveReloadServer


def _free_port() -> int:
    """Grab an unused localhost port."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def live_server(scaffolded_project: Path):
    """Yield (server, bus, base_url) with a running LiveReloadServer."""
    bus = EventBus()
    port = _free_port()

    def rebuild(theme: str) -> None:
        """Test stub: don't actually build, just publish a 'reloaded' event."""
        bus.publish({"type": "reloaded", "theme": theme})

    server = LiveReloadServer(
        project_dir=scaffolded_project,
        bus=bus,
        rebuild=rebuild,
        port=port,
        available_themes=("warm-ink", "classic", "modern"),
        current_theme="warm-ink",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # Wait briefly for the server to bind.
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.02)
    yield server, bus, f"http://127.0.0.1:{port}"
    server.shutdown()
    thread.join(timeout=2)


def test_state_endpoint_returns_themes(live_server) -> None:
    _, _, base = live_server
    with urllib.request.urlopen(f"{base}/__state", timeout=2) as resp:
        assert resp.status == 200
        body = json.loads(resp.read().decode("utf-8"))
    assert body["current_theme"] == "warm-ink"
    assert set(body["available_themes"]) == {"warm-ink", "classic", "modern"}


def test_events_endpoint_streams_published_events(live_server) -> None:
    _, bus, base = live_server
    req = urllib.request.Request(f"{base}/__events")
    with urllib.request.urlopen(req, timeout=2) as resp:
        # Server announces an initial "connected" event so we know our
        # subscriber is registered before we publish.
        first_block = _read_sse_block(resp, timeout=2.0)
        assert first_block["type"] == "connected"

        bus.publish({"type": "reloaded", "theme": "modern"})
        block = _read_sse_block(resp, timeout=2.0)
        assert block == {"type": "reloaded", "theme": "modern"}


def _read_sse_block(resp, timeout: float) -> dict:
    """Read one `event: X\\ndata: {json}\\n\\n` block from an SSE stream."""
    deadline = time.monotonic() + timeout
    payload_lines: list[str] = []
    while time.monotonic() < deadline:
        line = resp.readline()
        if not line:
            raise TimeoutError("SSE stream closed before producing a block")
        text = line.decode("utf-8").rstrip("\n").rstrip("\r")
        if text == "":  # blank line terminates a block
            if payload_lines:
                data = "".join(payload_lines)
                return json.loads(data)
            continue
        if text.startswith("data: "):
            payload_lines.append(text[len("data: ") :])
    raise TimeoutError("no SSE block within timeout")


def test_set_theme_endpoint_triggers_rebuild_and_emits_event(live_server) -> None:
    _, bus, base = live_server
    # Open an SSE stream so we can observe the resulting event.
    sse_req = urllib.request.Request(f"{base}/__events")
    with urllib.request.urlopen(sse_req, timeout=2) as sse:
        _read_sse_block(sse, timeout=2.0)  # connected

        body = json.dumps({"theme": "modern"}).encode("utf-8")
        req = urllib.request.Request(
            f"{base}/__set_theme",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2) as post_resp:
            assert post_resp.status == 200

        event = _read_sse_block(sse, timeout=2.0)
        assert event == {"type": "reloaded", "theme": "modern"}


def test_set_theme_rejects_unknown_theme(live_server) -> None:
    _, _, base = live_server
    body = json.dumps({"theme": "does-not-exist"}).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/__set_theme",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req, timeout=2)
    assert exc_info.value.code == 400


def test_events_handler_thread_exits_after_client_disconnects(live_server) -> None:
    """SSE handler thread must wake within a bounded time after the browser
    disconnects, otherwise subscribers leak across reloads.

    We rely on the heartbeat in _handle_events: when the client closes the
    socket, the next heartbeat write raises OSError and the handler exits.
    """
    server, bus, base = live_server

    # Open and immediately close an SSE connection to trigger handler thread
    # startup-then-disconnect. To keep the test fast we shorten the heartbeat
    # implicit timeout by sending a regular event right after disconnect so
    # the handler's `queue.get` returns (the socket write then fails).
    req = urllib.request.Request(f"{base}/__events")
    resp = urllib.request.urlopen(req, timeout=2)
    _ = _read_sse_block(resp, timeout=2.0)  # connected
    assert bus.subscriber_count() == 1
    resp.close()

    # Wake the handler with published events.  On some platforms (macOS) the
    # first write after a client close succeeds because the kernel still
    # accepts data into its send buffer; the OSError surfaces on the *next*
    # write attempt.  Publishing two events in quick succession ensures the
    # handler makes at least two write calls so the broken-pipe error is
    # raised and the subscription is cleaned up promptly.
    bus.publish({"type": "reloaded", "theme": "warm-ink"})
    time.sleep(0.05)
    bus.publish({"type": "reloaded", "theme": "warm-ink"})

    deadline = time.monotonic() + 3.0
    while bus.subscriber_count() > 0 and time.monotonic() < deadline:
        time.sleep(0.05)
    assert bus.subscriber_count() == 0, "SSE handler did not clean up subscription"


def test_set_theme_rejects_malformed_content_length(live_server) -> None:
    _, _, base = live_server
    # urllib won't let us set Content-Length to a non-numeric value, so use
    # raw socket I/O.
    host, _, port = base.removeprefix("http://").partition(":")
    port = int(port)
    raw = (
        b"POST /__set_theme HTTP/1.1\r\n"
        b"Host: 127.0.0.1\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: abc\r\n"
        b"\r\n"
    )
    with socket.create_connection((host, port), timeout=2) as s:
        s.sendall(raw)
        response = s.recv(4096).decode("utf-8", errors="replace")
    assert response.startswith("HTTP/1.0 400") or response.startswith("HTTP/1.1 400"), response


def test_set_theme_rejects_non_object_body(live_server) -> None:
    _, _, base = live_server
    body = b"null"
    req = urllib.request.Request(
        f"{base}/__set_theme",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req, timeout=2)
    assert exc_info.value.code == 400


def test_set_theme_rejects_array_body(live_server) -> None:
    _, _, base = live_server
    body = b'["modern"]'
    req = urllib.request.Request(
        f"{base}/__set_theme",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req, timeout=2)
    assert exc_info.value.code == 400


def test_index_html_gets_client_injection(live_server, scaffolded_project) -> None:
    _, _, base = live_server
    # Write a minimal index.html so the handler has something to serve.
    (scaffolded_project / "index.html").write_text(
        "<html><body><p>hi</p></body></html>", encoding="utf-8"
    )
    with urllib.request.urlopen(f"{base}/index.html", timeout=2) as resp:
        body = resp.read().decode("utf-8")
    assert "__resume_md_client_css" in body
    assert "__rmd_bar" in body
    # Injection must happen before </body>.
    assert body.index("__rmd_bar") < body.index("</body>")


def test_non_html_files_are_not_modified(live_server, scaffolded_project) -> None:
    _, _, base = live_server
    (scaffolded_project / "fixture.css").write_text("body { color: red; }", encoding="utf-8")
    with urllib.request.urlopen(f"{base}/fixture.css", timeout=2) as resp:
        body = resp.read().decode("utf-8")
    assert body == "body { color: red; }"
