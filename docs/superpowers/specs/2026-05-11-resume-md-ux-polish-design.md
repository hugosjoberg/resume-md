# Design: resume-md UX polish — preview as a dev environment + theming ergonomics

## Context

resume-md 0.1.0 shipped with five commands (`init`, `build`, `preview`, `themes`, `doctor`) and a working pipeline. A fresh-eyes audit of the user journey identified two clusters of friction that hurt repeat-use ergonomics:

- **Edit-loop quality** — `preview --watch` rebuilds on save but the browser doesn't refresh automatically; switching themes requires Ctrl+C + restart; build errors surface as Python tracebacks; pandoc warnings are swallowed by `subprocess.run`.
- **Theming ergonomics** — authoring a new theme is "copy and edit"; the CSS variable surface is undocumented in-CLI; upstream improvements to `_base.css` and bundled themes never reach existing scaffolded projects.

This spec covers the agreed scope (the "Full polish pass" approach): an SSE-backed dev environment for `preview`, three new CLI subcommands (`theme new`, `theme vars`, `update`), and CLI/browser error formatting.

## Goals

1. `preview --watch` updates the browser automatically on every save — no manual refresh.
2. Users can switch themes from the preview UI without leaving the browser.
3. Build errors render inline in the browser AND in the terminal, with parsed line numbers when possible.
4. Pandoc warnings (currently silent) surface in both terminal and browser.
5. Scaffolding a new theme is a one-line command.
6. The CSS variable surface is discoverable from the CLI.
7. Upstream improvements to bundled templates can be synced into existing projects without overwriting user edits.

## Non-goals

Explicit non-goals so we don't scope-creep:

- HTTPS or non-localhost preview access — preview stays bound to `127.0.0.1`.
- Multi-resume project mode.
- A general project config file (e.g. `.resume-md/config.toml`).
- Hot-reload of manifest changes; `update` is invoked manually.
- Browser-side automated testing (Playwright). Manual smoke per `CONTRIBUTING.md`.

## Architecture

### 1. Live-reload preview channel

Three internal endpoints layered onto the existing `http.server`. The `__` prefix namespaces them away from user-served content.

| Endpoint | Direction | Purpose |
|---|---|---|
| `GET /__events` | server → browser (SSE) | Stream of `reloaded`, `build_error`, `pandoc_warning` events |
| `POST /__set_theme` | browser → server | `{"theme": "modern"}` — triggers rebuild, emits `reloaded` on success |
| `GET /__state` | browser → server | Current theme + available themes (for the picker UI) |

When serving `index.html`, the handler appends a `<script>` block just before `</body>` that:

- Opens an `EventSource` to `/__events`.
- On `reloaded`: `location.reload()`.
- On `build_error`: shows a translucent overlay with the error.
- On `pandoc_warning`: shows a non-blocking toast (auto-dismisses in 5s).
- Renders a floating theme picker (bottom-right) that POSTs to `/__set_theme` and persists selection in `localStorage`.

### 2. Module decomposition

```
src/resume_md/
├── preview.py            (existing — slimmed to orchestration)
└── _preview/
    ├── __init__.py
    ├── event_bus.py      # thread-safe pub/sub, ~30 LOC
    ├── server.py         # custom handler + endpoint routing + script injection, ~180 LOC
    └── client.py         # injected JS + CSS as a Python string, ~150 LOC
```

`preview.py` becomes the orchestrator: build state, watcher thread, server thread, signal handling, browser launch.

The client bundle lives as a Python string (not as a file under `templates/`) so it's not copied into scaffolded projects.

### 3. Concurrency model

- Watcher thread → calls `build()` → publishes `reloaded` or `build_error` to `EventBus`.
- `POST /__set_theme` handler → calls `build()` under a `threading.Lock`; publishes the same events.
- One SSE handler thread per connected browser → blocks on its subscriber `queue.Queue` and writes each event as `data: {json}\n\n`.
- Rebuilds are serialized via the lock. Concurrent requests for the same theme are coalesced; for different themes, queued.

### 4. Manifest-based update tracking

`init` writes `.resume-md/manifest.json` recording the SHA-256 of every shipped infrastructure file at the time of scaffold:

```json
{
  "resume_md_version": "0.1.0",
  "tracked_files": {
    "themes/_base.css": "sha256:…",
    "themes/warm-ink.css": "sha256:…",
    "themes/classic.css": "sha256:…",
    "themes/modern.css": "sha256:…",
    ".github/workflows/build-pdf.yaml": "sha256:…",
    "Makefile": "sha256:…"
  }
}
```

`resume-md update` decides per-file actions:

| Current matches recorded hash? | Bundled changed? | Action |
|---|---|---|
| yes | yes | update file, refresh recorded hash |
| yes | no | no-op |
| no (user-modified) | yes | skip, report |
| no (user-modified) | no | refresh recorded hash (trust the user version) |
| missing locally | n/a | no-op |

Tracked files are infrastructure only. Explicitly NOT tracked: `resume.md`, `headshot.svg`, anything in the project root that isn't shipped. We never touch user content or build output.

`--dry-run` prints the plan without writing.

## CLI surface

```
resume-md
├── init           (existing — also writes .resume-md/manifest.json)
├── build          (existing — wraps errors via friendly formatter)
├── preview        (existing — live-reload by default; --no-live-reload skips
│                   the SSE handler + script injection and serves index.html
│                   verbatim, equivalent to the 0.1.0 behavior)
├── themes         (existing — unchanged; lists available themes)
├── doctor         (existing — unchanged)
├── theme          (new sub-app)
│   ├── new <name> [--from <base>] [--force]
│   └── vars [--theme <name>]
└── update [--dry-run]
```

`themes` (plural list verb) and `theme` (singular operate-on verb) coexist. They're different verbs serving different intents.

### `resume-md theme new <name> [--from <base>] [--force]`

Copies `themes/<base>.css` to `<project>/themes/<name>.css`, rewriting the leading comment block to name the new theme. Resolves `--from` via `discover_themes()` so it works against bundled OR project-local themes. Default `--from warm-ink`. Refuses to overwrite without `--force`.

### `resume-md theme vars [--theme <name>]`

Parses the `:root` block from `_base.css` and prints all CSS variables with their default values. With `--theme NAME`, also prints the effective value after the theme overlays — making the override surface discoverable from the CLI. Regex-based parser; we control the CSS file format, so a full parser is unnecessary.

### `resume-md update [--dry-run]`

Syncs tracked files using the manifest rules above. Reports per-file actions; exits 0 on success even when files were skipped.

## Error handling

### Friendly CLI error formatting

Today, a `BuildError` raised from a pandoc failure surfaces as `build failed: pandoc failed (exit 2).` with stderr discarded.

Changes:

1. Switch the pandoc subprocess call to capture stderr (`capture_output=True`), keep `check=True`.
2. On `CalledProcessError`, attach captured stderr to the `BuildError` message.
3. A small `ErrorFormatter` recognizes common patterns:

| Source error | Rendered as |
|---|---|
| `resume.md: openBinaryFile: does not exist` | `resume.md not found — run \`resume-md init\` to scaffold a project here` |
| `at "resume.md" line N, column M:` | The error + lines N-1..N+1 of the source for context |
| Missing image warnings | `headshot.svg not found — remove the <img> from resume.md or supply a file at this path` |

WeasyPrint's `WARNING` lines (`Ignored \`X\` at line:col, unknown property`) are suppressed by default; a `--debug` flag re-enables full output.

The terminal formatter and the in-browser overlay share the same `BuildError → render` path so messages match in both places.

### Pandoc warnings surfaced

Same plumbing. Capture stderr on every build; lines starting with `[WARNING]` are published as `pandoc_warning` events to the EventBus (browser toast) AND printed to the terminal prefixed `pandoc:`. Most common case in practice: missing image references.

## Testing strategy

### Unit

- `event_bus.py`: thread-safe pub/sub — subscribe, publish, unsubscribe-on-disconnect, multiple subscribers receive same event.
- `manifest.py`: load / save / hash, pure functions over `tmp_path`.
- `theme new` / `theme vars`: `CliRunner` assertions over produced file / stdout.
- `ErrorFormatter`: feed canned stderr samples, assert rendered output.

### Integration

One end-to-end preview test in `tests/test_preview.py`:

1. Use the existing `scaffolded_project` fixture.
2. Start the preview server in a daemon thread on a free port (grabbed via `socket.socket()`).
3. `GET /__state` → 200, returns three themes.
4. Connect to `GET /__events`, then `POST /__set_theme {"theme": "modern"}` → assert a `reloaded` event arrives within 5s.
5. Mangle `resume.md`, trigger rebuild via the watcher → assert `build_error` event.
6. Stop the server cleanly.

Bounded waits on event arrival, no flake-prone sleeps.

### Browser

Manual smoke documented in `CONTRIBUTING.md` as a checklist for PRs that touch `_preview/client.py`: open preview, edit `resume.md`, verify auto-refresh; click theme picker, verify each theme renders; break the markdown, verify overlay; fix it, verify overlay clears.

### CI impact

No new CI lanes. Existing `pytest -q` job on Linux (with pandoc installed) picks up the new tests. The integration test requires pandoc, gated by the existing `pandoc_required` marker.

## Design decisions and rationale

- **SSE + POST over WebSocket**: stdlib-native, no new dependencies. The duplex needs are minimal (a few events per second at most).
- **Internal endpoint prefix `__events`**: namespacing without configuration. Collision with user files is unlikely; we document it.
- **Single manifest file (`.resume-md/manifest.json`)**: simpler than per-file metadata; survives `git add .` naturally.
- **Tracked files set: infrastructure only**: `resume.md` and content files are explicitly excluded so `update` is always safe.
- **Inline client bundle as a Python string**: keeps dev-only UI out of `templates/` and therefore out of scaffolded projects.

## Risks and mitigations

- **Concurrent rebuild requests during a slow build**: serialized via lock; second request coalesced if duplicate, queued otherwise.
- **SSE connections leaking subscribers when the browser closes**: SSE handler cleans up its queue in a `finally` block.
- **Manifest drift if a user removes a tracked file**: `update` treats missing locally as no-op; no error.
- **Pandoc parse errors with no line number**: fall through to raw stderr display via the formatter.
- **User adds files to `themes/` that collide with bundled names**: `discover_themes()` already prefers project-local — no change needed.

## File map

New files:

- `src/resume_md/_preview/__init__.py`
- `src/resume_md/_preview/event_bus.py`
- `src/resume_md/_preview/server.py`
- `src/resume_md/_preview/client.py`
- `src/resume_md/manifest.py`
- `src/resume_md/errors.py` — `ErrorFormatter`
- `tests/test_event_bus.py`
- `tests/test_preview.py`
- `tests/test_manifest.py`
- `tests/test_theme_subcommands.py`
- `tests/test_errors.py`

Modified files:

- `src/resume_md/preview.py` — slim down to orchestration
- `src/resume_md/cli.py` — register new subcommands; wrap error path
- `src/resume_md/builder.py` — capture stderr always; expose warnings; integrate with EventBus
- `src/resume_md/templates/...` — no changes to shipped templates
- `CONTRIBUTING.md` — add the browser test checklist

## Estimated effort

5–7 days for a focused implementation pass:

- Days 1–2: Live-reload mechanism (`event_bus`, `server`, client bundle).
- Day 3: Theme toggle UI + error overlay polish.
- Day 4: `theme new` + `theme vars`.
- Day 5: Manifest + `update`.
- Days 6–7: Error formatter + tests + docs.
