"""Preview orchestrator: wires the watcher, the build pipeline, and the
LiveReloadServer together. Most of the heavy lifting lives in
``_preview.server``; this file is just glue + signal handling.
"""

from __future__ import annotations

import threading
import time
import webbrowser
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from ._preview.event_bus import EventBus
from ._preview.server import LiveReloadServer
from .builder import BuildError, build, discover_themes


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _build_and_publish(
    *,
    project_dir: Path,
    theme: str,
    html_name: str,
    pdf_name: str,
    bus: EventBus,
) -> None:
    """Build once. Always publishes exactly one terminal event (reloaded or
    build_error). Non-BuildError exceptions are surfaced as build_error
    events so the watcher cannot die silently on unexpected failures."""
    try:
        result = build(
            project_dir=project_dir,
            theme=theme,
            html_name=html_name,
            pdf_name=pdf_name,
        )
    except BuildError as exc:
        bus.publish({"type": "build_error", "message": str(exc)})
        return
    except Exception as exc:  # noqa: BLE001 — keep the watcher alive
        msg = f"unexpected build error: {exc}"
        print(f"[{_now()}] {msg}")
        bus.publish({"type": "build_error", "message": msg})
        return
    bus.publish({"type": "reloaded", "theme": theme})
    for warning in result.warnings:
        bus.publish({"type": "pandoc_warning", "message": warning})


def _watch_loop(
    *,
    project_dir: Path,
    current_theme: Callable[[], str],
    trigger_rebuild: Callable[[str], None],
    html_name: str,
    pdf_name: str,
    stop: threading.Event,
) -> None:
    """Rebuild whenever resume.md or any theme CSS changes.

    All rebuilds — whether from /__set_theme POST or from a watcher event —
    go through ``trigger_rebuild`` so they share the server's rebuild lock.
    This prevents a save+theme-click race from producing corrupt output
    files or out-of-order events.
    """
    from watchfiles import watch  # local import — only paid when --watch is used

    watch_paths = [project_dir / "resume.md"]
    themes_dir = project_dir / "themes"
    if themes_dir.is_dir():
        watch_paths.append(themes_dir)

    for changes in watch(*watch_paths, stop_event=stop, recursive=True):
        # Ignore changes to the output files we're producing.
        relevant = [
            c for c in changes if Path(c[1]).name not in {html_name, pdf_name}
        ]
        if not relevant:
            continue
        print(f"[{_now()}] change detected → rebuilding…")
        trigger_rebuild(current_theme())


def serve(
    project_dir: Path,
    port: int = 8000,
    watch: bool = False,
    theme: str = "warm-ink",
    html_name: str = "index.html",
    pdf_name: str = "resume.pdf",
    open_browser: bool = True,
    live_reload: bool = True,
) -> None:
    """Serve ``project_dir`` over HTTP on ``port`` until interrupted."""
    if not live_reload:
        # Fall back to the 0.1.0 behavior: plain SimpleHTTPRequestHandler.
        _serve_plain(
            project_dir=project_dir, port=port, html_name=html_name, open_browser=open_browser
        )
        return

    bus = EventBus()
    available_themes = tuple(sorted(discover_themes(project_dir).keys()))

    def rebuild(t: str) -> None:
        _build_and_publish(
            project_dir=project_dir,
            theme=t,
            html_name=html_name,
            pdf_name=pdf_name,
            bus=bus,
        )

    server = LiveReloadServer(
        project_dir=project_dir,
        bus=bus,
        rebuild=rebuild,
        port=port,
        available_themes=available_themes,
        current_theme=theme,
    )

    stop_event = threading.Event()
    watcher: threading.Thread | None = None
    if watch:
        watcher = threading.Thread(
            target=_watch_loop,
            kwargs={
                "project_dir": project_dir,
                "current_theme": server.current_theme,
                "trigger_rebuild": server.trigger_rebuild,
                "html_name": html_name,
                "pdf_name": pdf_name,
                "stop": stop_event,
            },
            daemon=True,
        )
        watcher.start()

    url = f"http://localhost:{port}/{html_name}"
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"[{_now()}] serving {project_dir} on {url}")
    if watch:
        print(f"[{_now()}] watching resume.md and themes/ — Ctrl+C to stop")
    if open_browser:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()

    try:
        while server_thread.is_alive():
            server_thread.join(timeout=0.5)
    except KeyboardInterrupt:
        print()
    finally:
        stop_event.set()
        server.shutdown()
        if watcher is not None:
            watcher.join(timeout=2)
        time.sleep(0.05)


def _serve_plain(
    *,
    project_dir: Path,
    port: int,
    html_name: str,
    open_browser: bool,
) -> None:
    """Equivalent to the v0.1.0 preview behavior; used for --no-live-reload."""
    import http.server
    import socketserver
    from functools import partial

    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(project_dir))
    url = f"http://localhost:{port}/{html_name}"
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"[{_now()}] serving {project_dir} on {url} (no live-reload)")
        if open_browser:
            threading.Timer(0.3, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()
