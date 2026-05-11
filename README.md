# resume-md

Print-quality PDF resumes from a single Markdown file. Pandoc + WeasyPrint with a deliberate, themeable design system.

You write Markdown. You run one command. You get:

- a polished `resume.pdf` ready to send,
- a single self-contained `index.html` you can host anywhere or open in a browser.

No layout editor, no proprietary format, no lock-in. Your resume is plain text under version control.

## Why

Most resume tools optimize for the wrong things: drag-and-drop layouts, "creative" templates, or full-page sidebars that look fine on a 27" monitor and break in print. The result is usually generic, badly typeset, and impossible to keep in git.

`resume-md` starts from the opposite end — a single Markdown file, a small CSS theme system, and a deterministic build pipeline.

See [`docs/PRODUCT.md`](docs/PRODUCT.md) for the design philosophy and [`docs/DESIGN.md`](docs/DESIGN.md) for the visual system.

## Install

`resume-md` is a Python CLI that wraps Pandoc and WeasyPrint.

```bash
# 1. Install Pandoc (resume-md cannot ship this — it's a separate binary)
brew install pandoc                # macOS
# sudo apt-get install pandoc      # Debian/Ubuntu

# 2. Install resume-md (WeasyPrint comes bundled)
pipx install resume-md
```

Verify everything is wired up:

```bash
resume-md doctor
```

## Quick start

```bash
resume-md init my-resume
cd my-resume
resume-md build               # writes index.html and resume.pdf
resume-md preview --watch     # serves locally, rebuilds on save
```

Edit `resume.md`, drop a headshot in (or remove the `<img>` element), and re-run `build` whenever you want.

### Live preview

`resume-md preview --watch` does three things:

- Auto-refreshes the browser on every save (no Cmd+R).
- Shows a floating theme picker — switch between bundled and project-local themes without leaving the browser.
- Displays a build-error overlay when the markdown breaks, plus toast notifications for pandoc warnings.

Run with `--no-live-reload` to serve static files only (the 0.1.0 behavior).

## CLI

| Command | What it does |
|---|---|
| `resume-md init [PATH]` | Scaffold a new resume project (default `./resume`). |
| `resume-md build [--theme NAME]` | Generate `index.html` + `resume.pdf`. |
| `resume-md preview [--watch]` | Serve locally with live-reload; `--watch` also rebuilds on file changes. |
| `resume-md themes` | List bundled + project-local themes. |
| `resume-md theme new <NAME> [--from <BASE>]` | Scaffold a new theme stylesheet in your project. |
| `resume-md theme vars [--theme <NAME>]` | List CSS variables (and effective overrides for a theme). |
| `resume-md update [--dry-run]` | Sync upstream infrastructure files into an existing project. |
| `resume-md doctor` | Verify Pandoc and WeasyPrint are available. |

Run `resume-md <command> --help` for full options.

## Themes

Three themes ship by default:

| | | |
|---|---|---|
| ![warm-ink](examples/screenshots/warm-ink.png) | ![classic](examples/screenshots/classic.png) | ![modern](examples/screenshots/modern.png) |
| **`warm-ink`** (default) — Helvetica Neue + warm ochre accent on paper-tinted background. The original design. | **`classic`** — Charter/Georgia serif, black on white, no chromatic accent. Conservative, academic. | **`modern`** — Inter sans-serif, blue accent, more whitespace. Tech-recruiter friendly. |

Switch with `resume-md build --theme classic`.

Authoring a new theme is mostly setting CSS variables — see [`docs/themes.md`](docs/themes.md) for the variable reference.

## Auto-build on push (optional)

Every scaffolded project includes `.github/workflows/build-pdf.yaml`. On every push to `main`, it:

1. Installs Pandoc and `resume-md` on the runner.
2. Runs `resume-md build`.
3. Uploads `resume.pdf` and `index.html` as workflow artifacts.

On a tag push (`v*`), it additionally attaches the PDF to a GitHub Release. Delete the workflow file to opt out.

## Sharing the HTML

`resume-md build` produces a single self-contained `index.html` (the headshot is base64-embedded, CSS is inlined). Drop it in any static host — GitHub Pages, Netlify, your own server — or attach to an email. No external assets to forget.

## Architecture

```
resume.md ──► pandoc ──► index.html ──► weasyprint ──► resume.pdf
                ▲                  ▲
                │                  └── single self-contained file
                │                      (CSS inlined, images embedded)
                │
                └── _base.css + theme.css concatenated
```

Two binaries do all the real work; the Python CLI just orchestrates them and ships the themes.

## Requirements

- Python 3.10+
- Pandoc 2.x or 3.x
- A POSIX-y operating system (macOS and Linux are tested; Windows likely works under WSL).

## Development

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

[MIT](LICENSE).

## Credits

The design system originated as Hugo Sjöberg's personal resume styling. The themes in this repository are extracted, documented, and generalized from that work.
