# Design system

This document captures the visual design system that underpins the bundled themes. If you're customizing CSS or authoring a new theme, this is the rulebook.

## 1. Overview

**Creative north star: "The Architect's Letterhead."**

The default `warm-ink` theme carries the quiet authority of precision stationery: heavy paper stock, considered ink placement, nothing decorative. Every element earns its space through function. The design signals engineering competence not by showing off, but by demonstrating the same restraint and structure the reader would expect from well-architected code.

The system rejects anything that draws attention to the design itself rather than the content. No gradients, no icons, no color blocks, no sidebars. The typography and spacing do all the work.

Key characteristics:

- **Print-native**: designed for PDF first, screen second.
- **Monochromatic base with a single accent**, used sparingly.
- **Hierarchy built entirely through type weight, size, and spacing.**
- **Dense but scannable**: a recruiter finds the key numbers in 15 seconds.

The other shipped themes (`classic`, `modern`) follow the same structural rules but exchange the palette and typeface.

## 2. Colors

A near-monochromatic palette warmed (in `warm-ink`) by a single ink-tone accent. The warmth comes from tinting the neutrals and background away from pure grey toward parchment.

### `warm-ink` palette

- **`--accent` `#6b5947`** — Warm ink. The sole accent. Used only for the name role tag, links, and section rule lines. Its rarity is the point: when it appears, it guides the eye.
- **`--ink` `#1a1a1a`** — Primary body text. Not pure black; slightly warm to reduce harshness on paper-white.
- **`--body-secondary` `#555555`** — Job titles and descriptions.
- **`--meta` `#777777`** — Contact row metadata.
- **`--label` `#999999`** — Dates, stack labels.
- **`--rule-section` `#e0dbd5`** — Section dividers.
- **`--paper` `#faf8f5`** — Background. Not `#fff`; a faint warm tint like quality uncoated stock.

### Named rules

- **The Single Ink Rule.** The accent color is the only chromatic color in the system. It appears on no more than 5% of the page surface. If you're reaching for a second color, reconsider the hierarchy instead.
- **No pure black/white.** Both are harsh in print and on screen. Use slightly tinted neutrals.

## 3. Typography

Themes ship with two typefaces: a Swiss-rational sans (`warm-ink`, `modern`) and a serif (`classic`). The font never calls attention to itself. All personality comes from weight contrast and spacing, not from the typeface.

### Hierarchy (default sizes, in points)

- **Display** (700, 26pt, line-height 1.0, -0.8px tracking): Name only. One instance per page.
- **Section heading** (700, 8pt, uppercase, 2.5px tracking, accent color): EXPERIENCE, EDUCATION, SKILLS. Letterspacing + uppercase creates formality without shouting.
- **Entry heading** (600, 10pt): Company names and degree titles. Paired with the period right-aligned on the same row.
- **Body** (400, 10pt, line-height 1.4): Bullet points and short paragraphs.
- **Description** (400, 9pt): One-paragraph context under entry headings.
- **Label / meta** (400, 7.5–9pt): Dates, contact info, stack listings. Quiet metadata that doesn't compete with body text.

### Named rules

- **The Weight-Not-Color Rule.** Hierarchy is expressed through font-weight steps (400 → 500 → 600 → 700) and size steps, never through color differentiation between text elements. Color distinguishes role (accent vs. body), not importance.

## 4. Elevation

Flat. No shadows anywhere. Depth is conveyed through typographic weight and spacing alone. The only structural dividers are the 2px rule under the header and 1px rules under section headings, which act as visual anchors, not container boundaries.

- **The No-Shadow Rule.** This is a document, not an interface. Shadows imply interactivity or layering that doesn't exist here. If something needs visual separation, increase the whitespace.

## 5. Components

### Section heading

Structured and assured. The uppercase letterspaced title with a firm bottom rule creates clear waypoints for scanning.

- No container; text + 1px bottom border.
- 12px above, 5px below.
- Default font: 8pt uppercase, 2.5px tracking, accent color.

### Entry header (`h3`)

A flex row with company name left-aligned and the date period right-aligned. The split layout is the primary navigational affordance: readers scan the right edge for dates.

- Layout: `display: flex; justify-content: space-between; align-items: baseline`.
- Company: 600 weight, 10pt.
- Period: 8pt, label color, wrapped in a `.period` span set inline via Pandoc (`[Jan 2022 – Present]{.period}`).

### Skills table

A two-column definition list rendered from a Markdown table: category label (120px fixed) and values.

- First column: 600 weight, accent color, uppercase, 8pt.
- Second column: 400 weight, ink-soft, 9pt.

### Headshot

Circular crop of a profile photo, anchored top-right of the header.

- Default shape: circle (`border-radius: 50%`).
- Default size: 68×68px.
- `object-fit: cover`.
- Omit the `<img class="headshot" …>` element entirely if you don't want a photo — the header gracefully collapses.

### Contact row

A single-line flex-wrap of contact items separated by gaps.

- Typography: 8pt, meta color.
- Links: accent color, no underline (underline on hover only).
- Gap: 12px horizontal between items.

## 6. Do's and don'ts

### Do

- **Do** keep the accent color sparingly applied (name role tag, section headings, links). Its scarcity creates hierarchy.
- **Do** keep the background subtly off-white. The warmth is essential for print comfort.
- **Do** test every change by exporting the PDF. If it doesn't look right at 100% on A4/Letter, it's wrong.
- **Do** maintain the right-aligned date pattern on every entry. Recruiters scan the right margin for timeline.
- **Do** keep body text at 9.5–10pt. Smaller loses readability in print; larger wastes vertical space.

### Don't

- **Don't** add a second chromatic color. One ink, one voice.
- **Don't** use icons, logos, or decorative elements. Content density is the feature.
- **Don't** add sidebars, columns, or non-linear layouts. Linear top-to-bottom scanning is fastest for recruiters.
- **Don't** use background colors or color blocks for sections. This is a document, not a dashboard.
- **Don't** draw attention to the design itself rather than the content. If someone notices the styling before the achievements, the design has failed.
- **Don't** use pure `#000` or `#fff`. Both are harsh in print and on screen.

## 7. Authoring a new theme

A theme is just a CSS file that sets variables on `:root`. To create one:

1. Copy any `themes/<name>.css` to `themes/<your-theme>.css`.
2. Override the variables you want to change.
3. Run `make THEME=<your-theme>`.

See [`themes.md`](themes.md) for the full variable reference.
