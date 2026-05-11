"""HTTP server that serves built artifacts plus three internal endpoints:

- ``GET  /__state``     — JSON describing current/available themes
- ``GET  /__events``    — Server-Sent Events stream of rebuild events
- ``POST /__set_theme`` — JSON `{"theme": "..."}`, triggers a rebuild

All other requests are served as static files from ``project_dir``.
"""

from __future__ import annotations

import http.server
import json
import queue
import socketserver
import threading
from collections.abc import Callable, Sequence
from functools import partial
from pathlib import Path

from .client import CLIENT_HTML  # noqa: F401
from .event_bus import EventBus

_SSE_HEADERS = (
    ("Content-Type", "text/event-stream"),
    ("Cache-Control", "no-cache, no-transform"),
    ("Connection", "keep-alive"),
    ("X-Accel-Buffering", "no"),
)


class LiveReloadServer:
    """Thin wrapper around ThreadingTCPServer with our handler wired in."""

    def __init__(
        self,
        *,
        project_dir: Path,
        bus: EventBus,
        rebuild: Callable[[str], None],
        port: int,
        available_themes: Sequence[str],
        current_theme: str,
        host: str = "127.0.0.1",
    ) -> None:
        self._project_dir = project_dir
        self._bus = bus
        self._rebuild = rebuild
        self._available_themes = tuple(available_themes)
        self._current_theme = current_theme
        self._rebuild_lock = threading.Lock()

        handler_cls = partial(
            LiveReloadHandler,
            directory=str(project_dir),
            server_state=self,
        )

        self._httpd = socketserver.ThreadingTCPServer((host, port), handler_cls)
        self._httpd.daemon_threads = True
        self._httpd.allow_reuse_address = True

    # State accessors used by the handler.
    @property
    def project_dir(self) -> Path:
        return self._project_dir

    @property
    def bus(self) -> EventBus:
        return self._bus

    @property
    def available_themes(self) -> tuple[str, ...]:
        return self._available_themes

    def current_theme(self) -> str:
        return self._current_theme

    def set_current_theme(self, theme: str) -> None:
        self._current_theme = theme

    def trigger_rebuild(self, theme: str) -> None:
        # Serialize rebuilds; concurrent same-theme requests get coalesced
        # by virtue of the lock — the second caller just waits for the first.
        with self._rebuild_lock:
            self._rebuild(theme)

    # Lifecycle.
    def serve_forever(self) -> None:
        self._httpd.serve_forever()

    def shutdown(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()


class LiveReloadHandler(http.server.SimpleHTTPRequestHandler):
    """Adds /__state, /__events, /__set_theme; otherwise serves files."""

    def __init__(self, *args, server_state: LiveReloadServer, **kwargs) -> None:
        self._state = server_state
        super().__init__(*args, **kwargs)

    # http.server's logging goes to stderr in a noisy format. Quiet it.
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return

    def do_GET(self) -> None:  # noqa: N802 — http.server convention
        if self.path == "/__state":
            self._handle_state()
            return
        if self.path == "/__events":
            self._handle_events()
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 — http.server convention
        if self.path == "/__set_theme":
            self._handle_set_theme()
            return
        self.send_error(404, "Not found")

    def _handle_set_theme(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON body")
            return
        theme = payload.get("theme")
        if not isinstance(theme, str) or theme not in self._state.available_themes:
            self.send_error(400, f"Unknown theme: {theme!r}")
            return

        self._state.set_current_theme(theme)
        try:
            self._state.trigger_rebuild(theme)
        except Exception as exc:  # noqa: BLE001 — propagate detail to user
            self._state.bus.publish({"type": "build_error", "message": str(exc)})
            self.send_error(500, f"Rebuild failed: {exc}")
            return

        body = b'{"ok":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_state(self) -> None:
        body = json.dumps(
            {
                "current_theme": self._state.current_theme(),
                "available_themes": list(self._state.available_themes),
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_events(self) -> None:
        self.send_response(200)
        for k, v in _SSE_HEADERS:
            self.send_header(k, v)
        self.end_headers()
        try:
            with self._state.bus.subscribe() as queue_:
                self._write_sse({"type": "connected"})
                while True:
                    try:
                        event = queue_.get(timeout=15.0)
                    except queue.Empty:
                        # Heartbeat: keeps the connection alive through proxies
                        # AND surfaces OSError on a dead socket, so the handler
                        # thread cannot leak when the browser disconnects
                        # silently. The leading colon makes the line an SSE
                        # comment that the client ignores.
                        self._write_sse_raw(": ping\n\n")
                        continue
                    self._write_sse(event)
        except OSError:
            return

    def _write_sse(self, event: dict) -> None:
        data = json.dumps(event)
        chunk = f"data: {data}\n\n".encode()
        self.wfile.write(chunk)
        self.wfile.flush()

    def _write_sse_raw(self, text: str) -> None:
        """Write a pre-formatted SSE chunk directly (used for heartbeats)."""
        self.wfile.write(text.encode("utf-8"))
        self.wfile.flush()
