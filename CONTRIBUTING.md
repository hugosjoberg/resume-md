# Contributing

Thanks for considering a contribution. This project is intentionally small in scope — a Markdown-to-PDF resume pipeline with a deliberate design system — so PRs that align with that scope are the easiest to merge.

## Good kinds of contributions

- **New themes** that follow the design system in [`docs/DESIGN.md`](docs/DESIGN.md). Themes should be pure variable-overrides where possible; significant deviation needs justification.
- **Bug fixes** in the `Makefile` or shipped CSS.
- **Doc improvements** — typos, missing variables, clearer examples.
- **Cross-platform fixes** — especially Linux/Windows where macOS-specific paths or commands may have crept in.

## Probably out of scope

- Alternative source formats (asciidoc, rst, JSON-resume). Markdown is the contract.
- Heavy layout features (sidebars, multi-column, infographics). The design philosophy is explicitly against these.
- LinkedIn/Indeed integrations. Out of scope; we build PDFs.
- Re-introducing a Python CLI. We deliberately collapsed back to a `Makefile`.

When in doubt, open an issue first to discuss before sending a PR.

## Local development

```bash
git clone https://github.com/hugosjoberg/resume-md.git
cd resume-md
make check          # verify pandoc + weasyprint are installed
make                # build index.html + resume.pdf
open resume.pdf
```

To test a theme change end-to-end:

```bash
make clean && make THEME=warm-ink && open resume.pdf
make clean && make THEME=classic  && open resume.pdf
make clean && make THEME=modern   && open resume.pdf
```

## Authoring a new bundled theme

1. Read [`docs/DESIGN.md`](docs/DESIGN.md) — the design rules are non-negotiable for bundled themes.
2. Add `themes/<name>.css` (a copy of an existing theme is the fastest start).
3. Add a one-line description as the first comment block.
4. Render the placeholder resume with your theme; attach a screenshot to the PR.
5. Themes should not require font installation — fall back to system fonts.

## Commit style

Short messages with a type prefix where useful: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`. PR bodies should describe the user-visible behavior change.
