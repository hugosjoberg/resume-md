# Theming

Themes are CSS files that set custom properties on `:root`. The base stylesheet (`themes/_base.css`) provides all structural rules and reads only via `var(...)`, so a theme is usually just a list of variable overrides.

## Quick start

```bash
cp themes/warm-ink.css themes/my-theme.css
# edit themes/my-theme.css
make THEME=my-theme
```

Drop a new `.css` into `themes/` and you can use it by name immediately — no registration step.

## Variable reference

### Colors

| Variable | Default (`warm-ink`) | Role |
|---|---|---|
| `--accent` | `#6b5947` | The single chromatic accent — name role tag, section headings, links, table labels |
| `--ink` | `#1a1a1a` | Primary body text |
| `--ink-soft` | `#333333` | Bullet text |
| `--body-secondary` | `#555555` | Job title / description text |
| `--meta` | `#777777` | Contact row |
| `--label` | `#999999` | Dates, stack labels |
| `--rule-section` | `#e0dbd5` | Section heading underlines |
| `--rule-header` | `var(--accent)` | The 2px rule below the page header |
| `--paper` | `#faf8f5` | Background color |

### Typography

| Variable | Default | Role |
|---|---|---|
| `--font-body` | `"Helvetica Neue", Arial, sans-serif` | All body type |
| `--font-display` | `"Helvetica Neue", Arial, sans-serif` | Name and section labels |
| `--fs-body` | `10pt` | Body text |
| `--fs-name` | `26pt` | The `<h1>` name |
| `--fs-role` | `9pt` | The role tag under the name |
| `--fs-summary` | `9pt` | The summary paragraph |
| `--fs-contact` | `8pt` | Contact row |
| `--fs-section` | `8pt` | Section headings (uppercase) |
| `--fs-skills-cell` | `9pt` | Skills table values |
| `--fs-skills-label` | `8pt` | Skills table labels |
| `--fs-entry` | `10pt` | Entry heading (company / degree) |
| `--fs-period` | `8pt` | Right-aligned date span |
| `--fs-em` | `9pt` | The `*italic*` line under an entry heading |
| `--fs-bullet` | `9.5pt` | Bullet list items |
| `--fs-stack` | `7.5pt` | "Stack:" line |
| `--fs-desc` | `9pt` | Paragraph after an entry heading |
| `--tracking-name` | `-0.8px` | Display-size letter spacing |
| `--tracking-uppercase` | `2.5px` | Uppercase letter spacing |

### Layout

| Variable | Default | Role |
|---|---|---|
| `--max-width` | `780px` | Screen-only max width (no effect in print) |
| `--page-size` | `A4` | `@page size` — set to `Letter` for US format |
| `--page-margin` | `14mm 16mm` | `@page margin` |
| `--headshot-size` | `68px` | Headshot width/height |
| `--headshot-radius` | `50%` | Headshot border-radius — set to `0` or `4px` for non-circular |
| `--header-border-width` | `2px` | Thickness of the rule under the header |

## Theme-specific tweaks

Variable overrides cover most use cases. For layout-level changes (centered header, multi-column, alternate page break rules), add normal CSS rules below your `:root` block — they'll cascade over the base sheet.

The bundled `modern` theme is a good example:

```css
:root {
  --accent: #2563eb;
  /* ... */
}

/* Beyond variables: a touch more vertical rhythm */
body { padding: 24px 28px; }
h2 { margin-top: 16px; }
h3 { margin-top: 12px; }
```

## Removing the headshot

If you don't want a photo, delete the `<img ... class="headshot" />` element from `resume.md`. The header collapses gracefully. No CSS changes needed.

## US Letter vs. A4

```css
:root {
  --page-size: Letter;
  --page-margin: 0.55in 0.65in;
}
```
