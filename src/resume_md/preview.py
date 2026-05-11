"""Local preview server with optional file-watching rebuild."""

from __future__ import annotations

import http.server
import socketserver
import threading
import time
import webbrowser
from datetime import datetime
from functools import partial
from pathlib import Path

from .builder import BuildError, build


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _watch_loop(
    project_dir: Path,
    theme: str,
    html_name: str,
    pdf_name: str,
    stop: threading.Event,
) -> None:
    """Rebuild whenever resume.md or any theme CSS changes.

    Imported lazily so users who never use --watch don't pay the watchfiles
    import cost.
    """
    from watchfiles import watch

    watch_paths = [project_dir / "resume.md"]
    themes_dir = project_dir / "themes"
    if themes_dir.is_dir():
        watch_paths.append(themes_dir)

    for changes in watch(*watch_paths, stop_event=stop, recursive=True):
        # Ignore changes to the output files we're producing — avoid
        # rebuild loops.
        relevant = [
            c for c in changes if Path(c[1]).name not in {html_name, pdf_name}
        ]
        if not relevant:
            continue
        print(f"[{_now()}] change detected → rebuilding…")
        try:
            build(
                project_dir=project_dir,
                theme=theme,
                html_name=html_name,
                pdf_name=pdf_name,
            )
            print(f"[{_now()}] rebuilt. refresh your browser.")
        except BuildError as exc:
            print(f"[{_now()}] build failed: {exc}")


def serve(
    project_dir: Path,
    port: int = 8000,
    watch: bool = False,
    theme: str = "warm-ink",
    html_name: str = "index.html",
    pdf_name: str = "resume.pdf",
    open_browser: bool = True,
) -> None:
    """Serve `project_dir` over HTTP on `port` until interrupted."""
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(project_dir))

    stop_event = threading.Event()
    watcher: threading.Thread | None = None
    if watch:
        watcher = threading.Thread(
            target=_watch_loop,
            args=(project_dir, theme, html_name, pdf_name, stop_event),
            daemon=True,
        )
        watcher.start()

    url = f"http://localhost:{port}/{html_name}"
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"[{_now()}] serving {project_dir} on {url}")
        if watch:
            print(f"[{_now()}] watching resume.md and themes/ — Ctrl+C to stop")
        if open_browser:
            # Slight delay so the server is ready before the browser hits it.
            threading.Timer(0.3, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()  # newline after ^C
        finally:
            stop_event.set()
            if watcher is not None:
                # watchfiles returns promptly when stop_event is set.
                watcher.join(timeout=2)
            # Tiny pause helps the console flush cleanly before shell prompt.
            time.sleep(0.05)
