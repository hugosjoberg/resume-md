# Template-repo redesign

## Summary

Collapse `resume-md` from a Python-distributable CLI into a pure GitHub template repo. The user clicks "Use this template," gets their own copy, edits `resume.md` and `themes/*.css`, runs `make generate` locally, and gets a print-quality `resume.pdf` plus a self-contained `index.html`. No Python package, no CLI, no PyPI, no GitHub Actions.

## Why

The initial release shipped a five-subcommand CLI (`init`, `build`, `preview`, `themes`, `doctor`), a theme registry walking `importlib.resources`, an init-scaffolding command that `cp -r`s a `templates/` directory, an HTTP preview server with file-watching, and a pytest suite. The actual build work is ~30 lines: concatenate two CSS files, invoke `pandoc`, invoke `weasyprint`. Everything else exists to support a distribution model — a pip-installable CLI with a scaffolding command — that doesn't match how a single-resume project is realistically consumed.

The natural consumption pattern is: fork (or "Use this template") → edit Markdown → run `make`. The simplification removes a layer of indirection without losing any user-visible capability.

## Scope

### In scope

- Promote the existing template payload (`src/resume_md/templates/*`) to the repo root.
- Make the existing `Makefile` the only build path. Fix one cascade-order bug; add `preview` and `check` targets.
- Replace the auto-extracted `<title>` with a YAML frontmatter `title:` field in `resume.md`.
- Delete the Python package, tests, build artifacts, duplicate `resume/` working directory, and both GitHub Actions workflows.
- Rewrite `README.md` and `CONTRIBUTING.md` to describe the template-repo flow.
- Scrub remaining CLI references from `docs/`.

### Non-goals

- No PyPI package, no console-script, no `pipx install` path.
- No `resume-md` CLI in any form.
- No GitHub Actions for building.
- No file watcher / live reload.
- No backward-compatibility shim for users of the v0 CLI (this is a fresh-release reset).

## Final repo layout

```
resume.md              # source of truth; starts with YAML title frontmatter
headshot.svg           # demo headshot referenced from resume.md
themes/
  _base.css            # structural rules: page size, typography baseline, spacing
  warm-ink.css         # default theme
  classic.css
  modern.css
Makefile               # the entire build pipeline
.gitignore
README.md
CONTRIBUTING.md
LICENSE
docs/
  PRODUCT.md
  DESIGN.md
  themes.md
  superpowers/specs/   # design specs (incl. this one)
examples/
  screenshots/         # warm-ink.png, classic.png, modern.png for README
```

## Build pipeline

`make generate` runs the pipeline:

1. `cat themes/_base.css themes/$(THEME).css > .build/style.css` — base first, theme last, so theme rules override (the cascade order documented in `src/resume_md/builder.py:131-132`).
2. `pandoc resume.md --standalone --css .build/style.css --embed-resources -o index.html`
3. `weasyprint index.html resume.pdf`

`THEME` defaults to `warm-ink`; override with `make generate THEME=classic`.

`make preview` runs `generate` then opens `index.html` in the default browser (`open` or `xdg-open`).

`make check` verifies `pandoc` and `weasyprint` are on `PATH`.

`make clean` removes `.build/`, `index.html`, `resume.pdf`.

## Title handling

`resume.md` begins with:

```markdown
---
title: "Jane Doe — Senior Software Engineer"
---
```

Pandoc's `--standalone` reads this and sets `<title>` in the emitted HTML. The existing inline HTML header (`<h1>Jane Doe</h1>`, `<span class="role">…</span>`) stays — it's what the CSS targets. The frontmatter exists solely to satisfy Pandoc and silence its warning about missing title.

## Theme system

Three themes ship in `themes/`: `warm-ink.css` (default), `classic.css`, `modern.css`. The shared `themes/_base.css` provides structural rules consumed via `var(...)`; each theme overrides variables on `:root`.

To author a new theme: copy any existing theme, edit the variables, run `make generate THEME=<name>`. Full variable reference in `docs/themes.md`.

## Deletions

| Path | Reason |
|---|---|
| `src/` | Python package no longer distributed. |
| `tests/` | No code to test. |
| `pyproject.toml`, `uv.lock` | Not packaging. |
| `dist/` | Artifacts of the removed package. |
| `.github/workflows/ci.yaml` | Tested the Python package. |
| `.github/workflows/release.yaml` | Released the Python package. |
| `resume/` (top-level) | Duplicate of the template payload; its contents *become* the repo root. |

## Verification

1. `make check` → both tools resolvable.
2. `make clean && make generate` → no errors; `index.html` and `resume.pdf` written at repo root.
3. Open `resume.pdf` — first page renders, headshot embedded, fonts correct.
4. `make generate THEME=classic` and `THEME=modern` — both succeed; PDFs reflect the theme.
5. `grep -r "pipx install resume-md\|resume-md init\|resume-md build" -- ':!docs/superpowers/specs'` returns nothing.
6. `git ls-files` shows no `src/`, `tests/`, `pyproject.toml`, `uv.lock`, `dist/`, top-level `resume/`, or `.github/workflows/*.yaml`.
