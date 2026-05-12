# Authoring your resume

This is the reference for editing `resume.md`. It's structured as **(1) a YAML frontmatter block at the top with your basic info** and **(2) Markdown sections below it for the body**.

You only ever edit `resume.md`. The HTML structure is generated for you by a tiny Pandoc template (`templates/resume.html`) — you don't need to touch it.

## The frontmatter

The block at the top of `resume.md`, between the two `---` lines, holds your basic info. Edit the values; don't touch the `key:` part on the left.

| Field | Required? | What goes here |
|---|---|---|
| `name` | yes | Your name. Renders as the big `<h1>` heading. |
| `role` | recommended | Your current role / title. Renders in the accent color under your name. Also feeds the browser-tab title. |
| `photo` | optional | Filename of your headshot, sitting next to `resume.md`. Delete this line to skip the photo entirely — the header collapses gracefully. |
| `summary` | optional | A short intro paragraph. Use `\|` to keep your line breaks, or `>` to fold them all into one paragraph. |
| `contact` | optional | A list of items shown in the contact row. One item per line, prefixed with `- `. |

### The `contact` list

Each line is one item. Plain text is fine; for clickable items, use standard Markdown link syntax inside double quotes:

```yaml
contact:
  - "London, UK"
  - "+44 7700 900123"
  - "[jane@example.com](mailto:jane@example.com)"
  - "[LinkedIn](https://www.linkedin.com/in/janedoe/)"
  - "[GitHub](https://github.com/janedoe)"
```

The double quotes are required for lines starting with `[` — YAML treats unquoted `[` as the start of an inline list.

## The body

Everything below the second `---` is normal Markdown. The conventions:

| You write | What it does |
|---|---|
| `## Skills`, `## Experience`, `## Education`, `## Side Projects`, `## Languages` | Section headings. Add or rename freely — they all get the same uppercase rule treatment. |
| `### Company — Date` | Entry heading for a job or degree. The text after the dash is right-aligned as the date timeline. **See "Dashes" below.** |
| `*Senior Software Engineer*` (italic, right under an entry heading) | Job title / role line, rendered in a quieter color. |
| `- bullet point` | Achievement bullets inside an entry. |
| `**Stack:** Go, Rust, PostgreSQL` | The tech-stack line at the bottom of an entry, rendered smaller and grey. |
| `\| **Languages** \| Go, Rust, Python \|` (markdown table) | The skills table. Two columns: bold label, comma-separated values. Add rows freely. |

## Dashes (the one tricky bit)

Entry headings like `### Company — Date` need a special separator between the company and the date — that's what tells the layout to right-align the date.

The separator can be any of:

| Type | What you type | Notes |
|---|---|---|
| Em-dash | `—` | macOS: `Opt+Shift+-`. Visually distinct, but obscure to type. |
| En-dash | `–` | Slightly shorter. Also obscure to type. |
| Two hyphens | `--` | Easiest. Pandoc auto-converts to en-dash on render. |
| Three hyphens | `---` | Also easy. Pandoc auto-converts to em-dash on render. |

**Recommendation: just type `--`** between the company and the date. It works, it looks fine, and you don't have to learn any new key combinations.

```markdown
### Northwind Data -- Jan 2022 – Present
```

If a heading doesn't contain a dash separator (e.g. `### Education`, `### Tinydash`), nothing is right-aligned — the heading is left-as-is. That's the right behavior for section dividers and side projects.

## Skipping the photo

Delete the `photo:` line in the frontmatter. The header layout collapses to text-only — no CSS changes needed.

## Renaming or reordering sections

The `## Skills`, `## Experience`, etc. headings are just normal Markdown `<h2>` tags — rename them, reorder them, or add new ones. The styling is by element, not by section name.

## What `make` does to your file

1. Concatenates `themes/_base.css` and `themes/<theme>.css` into one stylesheet.
2. Runs `pandoc resume.md --template templates/resume.html --lua-filter filters/split-date.lua --css <stylesheet> --embed-resources -o index.html`.
3. Runs `weasyprint index.html resume.pdf`.

The `--lua-filter` is the small (~25-line) script that handles the dash → right-aligned date conversion. The `--template` is the HTML scaffolding around your content. Neither needs to be edited.
