"""HTML/JS/CSS bundle injected into served `index.html` during preview.

Kept as a single Python string so the dev-only UI never lands in scaffolded
projects (it isn't under templates/). The injection happens in
``_preview.server.LiveReloadHandler``.

Keep this file under ~250 LOC and free of build steps. It runs in modern
evergreen browsers only; we don't need to support legacy targets.
"""

from __future__ import annotations

CLIENT_HTML = """\
<style id="__resume_md_client_css">
  .__rmd-bar {
    position: fixed; bottom: 16px; right: 16px; z-index: 2147483646;
    font: 12px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: rgba(20, 20, 20, 0.92); color: #f5f5f5;
    padding: 8px 12px; border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    display: flex; align-items: center; gap: 8px;
  }
  .__rmd-bar select {
    background: transparent; color: inherit;
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 4px; padding: 2px 6px; font: inherit;
  }
  .__rmd-bar select:focus { outline: 1px solid #4f8eff; }
  .__rmd-status { opacity: 0.7; font-size: 11px; }
  .__rmd-overlay {
    position: fixed; inset: 0; z-index: 2147483647;
    background: rgba(0, 0, 0, 0.75); color: #f5f5f5;
    display: flex; align-items: center; justify-content: center;
    padding: 24px;
  }
  .__rmd-overlay-box {
    max-width: 720px; width: 100%; background: #1a1a1a;
    padding: 20px 24px; border-radius: 8px;
    border-left: 4px solid #e0433a;
    font: 13px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
    white-space: pre-wrap; max-height: 80vh; overflow: auto;
  }
  .__rmd-overlay-title {
    font: 600 14px -apple-system, sans-serif; color: #e0433a;
    margin: 0 0 12px;
  }
  .__rmd-toast {
    position: fixed; bottom: 64px; right: 16px; z-index: 2147483645;
    background: rgba(204, 132, 31, 0.95); color: #1a1a1a;
    padding: 8px 14px; border-radius: 6px;
    font: 12px/1.4 -apple-system, sans-serif;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    max-width: 360px; transition: opacity 0.3s ease;
  }
</style>

<div class="__rmd-bar" id="__rmd_bar">
  <span class="__rmd-status" id="__rmd_status">connecting…</span>
</div>

<script id="__resume_md_client_js">
(function () {
  const STORAGE_KEY = "__resume_md_theme";
  const bar = document.getElementById("__rmd_bar");
  const status = document.getElementById("__rmd_status");

  function setStatus(text) { status.textContent = text; }

  function reload() {
    setStatus("reloading…");
    location.reload();
  }

  function connect() {
    const src = new EventSource("/__events");
    src.onopen = () => setStatus("live");
    src.onerror = () => setStatus("disconnected — retrying…");
    src.addEventListener("reloaded", reload);
  }

  connect();
})();
</script>
"""
