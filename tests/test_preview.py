"""End-to-end tests for the live-reload preview server."""

from __future__ import annotations

import json
import socket
import threading
import time
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
