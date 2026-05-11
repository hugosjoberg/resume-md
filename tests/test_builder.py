"""End-to-end build pipeline tests.

These tests run real `pandoc` + `weasyprint` invocations, so they verify the
shell-out and the import path actually work — not just the wrappers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_md.builder import (
    BuildError,
    _extract_page_title,
    _parse_pandoc_warnings,
    build,
    discover_themes,
)

from .conftest import pandoc_required


def test_discover_themes_lists_bundled(tmp_path: Path) -> None:
    themes = discover_themes(tmp_path)
    assert {"warm-ink", "classic", "modern"} <= set(themes)
    assert all(themes[name].is_file() for name in themes)


def test_discover_themes_includes_project_local(scaffolded_project: Path) -> None:
    local = scaffolded_project / "themes" / "custom.css"
    local.write_text(":root { --accent: red; }\n")
    themes = discover_themes(scaffolded_project)
    assert "custom" in themes
    assert themes["custom"] == local


def test_extract_page_title_pulls_name_and_role(tmp_path: Path) -> None:
    md = tmp_path / "resume.md"
    md.write_text(
        '<h1>Ada Lovelace</h1>\n<span class="role">Mathematician</span>\n',
        encoding="utf-8",
    )
    assert _extract_page_title(md) == "Ada Lovelace — Mathematician"


def test_extract_page_title_falls_back_to_filename(tmp_path: Path) -> None:
    md = tmp_path / "fallback.md"
    md.write_text("just plain markdown\n", encoding="utf-8")
    assert _extract_page_title(md) == "fallback"


@pandoc_required
def test_build_default_theme_produces_outputs(scaffolded_project: Path) -> None:
    result = build(project_dir=scaffolded_project)
    assert result.html_path.is_file()
    assert result.pdf_path.is_file()
    assert result.pdf_path.stat().st_size > 1024  # non-trivial PDF
    html = result.html_path.read_text(encoding="utf-8")
    assert "<style>" in html  # CSS inlined by --embed-resources
    assert "Jane Doe" in html


@pandoc_required
@pytest.mark.parametrize("theme", ["warm-ink", "classic", "modern"])
def test_build_each_bundled_theme(scaffolded_project: Path, theme: str) -> None:
    result = build(project_dir=scaffolded_project, theme=theme)
    assert result.pdf_path.is_file() and result.pdf_path.stat().st_size > 1024


@pandoc_required
def test_themes_produce_distinct_output(scaffolded_project: Path) -> None:
    """Regression: catches the cascade-order bug where the base stylesheet
    was concatenated after the theme and silently overrode it.

    Both the base sheet and a non-default theme declare `--accent`. The
    theme's value must appear *last* in the inlined CSS, otherwise the
    base value wins and the theme is effectively a no-op.
    """
    base_accent = "#6b5947"  # set in themes/_base.css
    cases = {
        "classic": "#1a1a1a",
        "modern": "#2563eb",
    }
    for theme, theme_accent in cases.items():
        result = build(project_dir=scaffolded_project, theme=theme)
        html = result.html_path.read_text(encoding="utf-8")
        base_idx = html.find(f"--accent: {base_accent}")
        theme_idx = html.find(f"--accent: {theme_accent}")
        assert base_idx >= 0, f"{theme}: base accent missing from inlined CSS"
        assert theme_idx >= 0, f"{theme}: theme accent missing from inlined CSS"
        assert base_idx < theme_idx, (
            f"{theme}: theme CSS must come AFTER base CSS in the cascade "
            f"(base at {base_idx}, theme at {theme_idx})"
        )


def test_build_rejects_unknown_theme(scaffolded_project: Path) -> None:
    with pytest.raises(BuildError, match="Unknown theme"):
        build(project_dir=scaffolded_project, theme="does-not-exist")


def test_build_rejects_missing_source(tmp_path: Path) -> None:
    # tmp_path has no resume.md.
    with pytest.raises(BuildError, match="Source file not found"):
        build(project_dir=tmp_path)


@pandoc_required
def test_pandoc_failure_propagates_stderr(scaffolded_project: Path) -> None:
    """A malformed source surfaces pandoc's stderr via BuildError.message,
    so the friendly formatter has something to work with."""
    source = scaffolded_project / "resume.md"
    # Write a YAML block with an unclosed string — pandoc parse error.
    source.write_text('---\ntitle: "broken\n---\n# Hi\n', encoding="utf-8")
    with pytest.raises(BuildError) as exc_info:
        build(project_dir=scaffolded_project)
    msg = str(exc_info.value)
    assert "pandoc" in msg.lower()
    # The captured stderr from pandoc should mention either the line or 'YAML'.
    assert ("line" in msg.lower()) or ("yaml" in msg.lower())


@pandoc_required
def test_successful_build_surfaces_pandoc_warnings(scaffolded_project: Path) -> None:
    """Missing image warning is captured and returned via the build result."""
    # Delete the placeholder headshot so pandoc warns on the <img> ref.
    (scaffolded_project / "headshot.svg").unlink()
    result = build(project_dir=scaffolded_project)
    assert result.pdf_path.is_file()
    assert any("headshot" in w.lower() for w in result.warnings), (
        f"expected a warning mentioning headshot; got {result.warnings!r}"
    )


def test_parse_pandoc_warnings_folds_continuation_lines() -> None:
    """Multi-line warnings are stitched together into one tuple entry."""
    stderr = (
        "[INFO] some info\n"
        "[WARNING] Could not fetch resource headshot.svg:\n"
        "  Falling back to alt text\n"
        "  More context on a second continuation line\n"
        "[WARNING] Another warning\n"
        "trailing line that should be ignored\n"
    )
    warnings = _parse_pandoc_warnings(stderr)
    assert len(warnings) == 2
    assert "headshot.svg" in warnings[0]
    assert "Falling back to alt text" in warnings[0]
    assert "More context" in warnings[0]
    assert warnings[1] == "Another warning"
