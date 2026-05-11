# Changelog

All notable changes to resume-md will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] — 2026-05-11

### Added
- Live-reload preview: `resume-md preview --watch` now auto-refreshes the browser on every save (Server-Sent Events).
- In-browser theme picker: a floating dropdown lets you switch between bundled and project-local themes without leaving the browser.
- Build-error overlay rendered in-browser when the markdown breaks, plus toast notifications for pandoc warnings.
- `resume-md theme new <name> [--from <base>]` — scaffold a new theme stylesheet from any existing theme.
- `resume-md theme vars [--theme <name>]` — list CSS variables and their effective overrides.
- `resume-md update [--dry-run]` — sync upstream infrastructure files (themes, workflows) into existing projects without overwriting user edits. Backed by a per-project `.resume-md/manifest.json`.
- Captured pandoc stderr is now surfaced via the new `ErrorFormatter` in both the terminal and the browser overlay, with friendly messages for the most common failures (missing source, parse errors with line context, missing images).
- Pandoc warnings (previously swallowed) are now printed in yellow on stderr and shown as in-browser toasts.

### Changed
- `resume-md preview` enables live-reload by default. Pass `--no-live-reload` to restore the 0.1.0 behavior (plain `SimpleHTTPRequestHandler`).

### Fixed
- Multi-line pandoc warnings are now captured intact (continuation lines were previously dropped).
- The CSS cascade order between `_base.css` and theme files is now correct (theme `:root` overrides base `:root`).

## [0.1.0] — 2026-05-11

Initial release. Markdown → Pandoc → WeasyPrint → PDF + standalone HTML, with three bundled themes (warm-ink, classic, modern).
