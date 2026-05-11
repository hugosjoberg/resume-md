"""Tests for the ErrorFormatter: turns pandoc/weasyprint stderr into
actionable terminal output (and the same text powers the in-browser overlay)."""

from __future__ import annotations

from pathlib import Path

from resume_md.errors import ErrorFormatter, FormattedError


def test_format_missing_source_file() -> None:
    formatter = ErrorFormatter(project_dir=Path("/tmp/x"))
    result = formatter.format(
        "pandoc: resume.md: openBinaryFile: does not exist (No such file or directory)"
    )
    assert isinstance(result, FormattedError)
    assert "resume.md not found" in result.message
    assert "resume-md init" in result.message


def test_format_pandoc_parse_error_with_line_context(tmp_path: Path) -> None:
    source = tmp_path / "resume.md"
    source.write_text("line one\nline two — has a problem\nline three\n", encoding="utf-8")
    formatter = ErrorFormatter(project_dir=tmp_path)
    stderr = 'Error at "resume.md" line 2, column 14:\nunexpected character'
    result = formatter.format(stderr)
    assert "line 2" in result.message
    assert "line two" in result.message
    # surrounding context shows neighbors
    assert "line one" in result.message
    assert "line three" in result.message


def test_format_missing_image_warning() -> None:
    formatter = ErrorFormatter(project_dir=Path("/tmp/x"))
    result = formatter.format(
        "[WARNING] Could not fetch resource 'headshot.svg': openBinaryFile: does not exist"
    )
    assert "headshot.svg" in result.message
    assert "remove" in result.message or "supply" in result.message


def test_format_unknown_stderr_falls_through() -> None:
    formatter = ErrorFormatter(project_dir=Path("/tmp/x"))
    raw = "something pandoc said that we don't recognize"
    result = formatter.format(raw)
    # Raw text preserved when we can't match a pattern.
    assert raw in result.message


def test_format_empty_stderr() -> None:
    formatter = ErrorFormatter(project_dir=Path("/tmp/x"))
    result = formatter.format("")
    assert result.message  # non-empty fallback
