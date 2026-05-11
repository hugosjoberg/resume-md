# Contributing

Thanks for considering a contribution. This project is intentionally small in scope — a Markdown-to-PDF resume pipeline with a deliberate design system — so PRs that align with that scope are the easiest to merge.

## Good kinds of contributions

- **New themes** that follow the design system in [`docs/DESIGN.md`](docs/DESIGN.md). Themes should be pure variable-overrides where possible; significant deviation needs justification.
- **Bug fixes** in the build pipeline, CLI, or watchers.
- **Tests** for any of the above.
- **Doc improvements** — typos, missing variables, clearer examples.
- **Cross-platform fixes** — especially Linux/Windows where macOS-specific code may have crept in.

## Probably out of scope

- Alternative source formats (asciidoc, rst, JSON-resume). Markdown is the contract.
- Heavy layout features (sidebars, multi-column, infographics). The design philosophy is explicitly against these.
- LinkedIn/Indeed integrations. Out of scope; we build PDFs.

When in doubt, open an issue first to discuss before sending a PR.

## Development setup

```bash
git clone https://github.com/hugosjoberg/resume-md.git
cd resume-md
pipx install -e . --python python3.13  # or 3.10+
pip install -e ".[dev]"                # optional, for ruff + pytest
```

Run the test suite:

```bash
pytest
ruff check
```

Smoke-test a build from a fresh scaffold:

```bash
resume-md init /tmp/dev-test --force
cd /tmp/dev-test && resume-md build && open resume.pdf
```

## Authoring a new bundled theme

1. Read [`docs/DESIGN.md`](docs/DESIGN.md) — the design rules are non-negotiable for bundled themes.
2. Add `src/resume_md/templates/themes/<name>.css`.
3. Add a one-line description as the first comment block.
4. Render the placeholder resume with your theme; attach a screenshot to the PR.
5. Themes should not require font installation — fall back to system fonts.

## Commit style

Short messages with a type prefix where useful: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`. PR bodies should describe the user-visible behavior change.

## Browser smoke checklist

Run this when you touch `src/resume_md/_preview/client.py` or
`src/resume_md/_preview/server.py`. Automated tests cover the server logic;
this checklist covers the browser-side UI.

```bash
rm -rf /tmp/rm-smoke
resume-md init /tmp/rm-smoke
cd /tmp/rm-smoke && resume-md build && resume-md preview --watch
```

In the browser:

- [ ] **Auto-refresh**: edit `resume.md`, save, page should reload within ~1s.
- [ ] **Theme picker**: open the dropdown in the bottom-right, switch to each
      theme. Each renders cleanly.
- [ ] **Theme persists**: refresh the page manually — the picker remembers
      your last selection.
- [ ] **Error overlay**: break the markdown (e.g. open a YAML block with `---`
      and never close it). The overlay should appear with the error.
- [ ] **Overlay clears**: fix the markdown. The overlay should disappear on
      the next successful build.
- [ ] **Pandoc warning toast**: delete `headshot.svg`, save. A yellow toast
      should appear with `pandoc: ... headshot.svg ...`. It dismisses after ~5s.
- [ ] **`--no-live-reload`**: stop the server, restart with
      `resume-md preview --no-live-reload`. The page renders without the
      floating picker — and editing `resume.md` does NOT trigger a refresh.
