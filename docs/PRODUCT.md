# Product brief

## Who this is for

Engineers and designers who care about how their resume looks but don't want to spend a weekend in Word or InDesign. They write everywhere else in Markdown — code comments, docs, GitHub issues — and resent doing one document in a different tool.

## Why this exists

Most resume tools optimize for the wrong things: drag-and-drop layouts, "creative" templates, or full-page sidebars that look fine on a 27" monitor and break in print. The result is usually generic, badly typeset, and impossible to keep in version control.

This project starts from the opposite end: a single Markdown file, a small CSS theme system, and a deterministic build pipeline. You edit text, you run one command, you get a print-quality PDF and a single self-contained HTML file you can host or email.

## Brand personality

Precise, confident, understated. The tool should feel like it was made by someone who cares about craft but doesn't need to show off. Quiet competence over loud decoration.

## Design principles

1. **Content density over decoration.** Every pixel serves the reader's scan path. No ornament for its own sake.
2. **Hierarchy through typography.** Weight, size, and spacing do the work. Color is supporting, never leading.
3. **Print-native.** Designed for PDF first, works well on screen second. No features that break in print.
4. **Signal through restraint.** An engineer's resume should demonstrate precision, not visual flair.
5. **Scannable at speed.** A recruiter glancing for 15 seconds should find name, current role, key numbers, and tech stack without scrolling.

## Anti-references

Generic Word templates. ATS-targeted resumes that strip all formatting. Single-page resumes that cram everything into a sidebar and a wall of body text. Anything that draws attention to the design itself rather than the content.

## Accessibility and inclusion

- WCAG AA contrast ratios on default themes.
- No reliance on color alone for information.
- Print-friendly: no background colors that waste ink or disappear in grayscale.
- Headshot is optional — the layout works without it.
