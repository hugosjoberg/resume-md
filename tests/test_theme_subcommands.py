"""Tests for `resume-md theme new` and `resume-md theme vars`."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from resume_md.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_theme_new_creates_file_from_warm_ink(
    runner: CliRunner, scaffolded_project: Path
) -> None:
    result = runner.invoke(
        app,
        ["theme", "new", "sage", "--project-dir", str(scaffolded_project)],
    )
    assert result.exit_code == 0, result.stdout
    new_css = scaffolded_project / "themes" / "sage.css"
    assert new_css.is_file()
    text = new_css.read_text(encoding="utf-8")
    assert "Theme: sage" in text
    # CSS variables are inherited from warm-ink.
    assert "--accent" in text


def test_theme_new_from_explicit_base(
    runner: CliRunner, scaffolded_project: Path
) -> None:
    result = runner.invoke(
        app,
        [
            "theme", "new", "navy", "--from", "modern",
            "--project-dir", str(scaffolded_project),
        ],
    )
    assert result.exit_code == 0
    text = (scaffolded_project / "themes" / "navy.css").read_text(encoding="utf-8")
    assert "Theme: navy" in text
    # modern's accent is #2563eb.
    assert "#2563eb" in text


def test_theme_new_refuses_overwrite(
    runner: CliRunner, scaffolded_project: Path
) -> None:
    existing = scaffolded_project / "themes" / "warm-ink.css"
    result = runner.invoke(
        app,
        ["theme", "new", "warm-ink", "--project-dir", str(scaffolded_project)],
    )
    assert result.exit_code != 0
    # File untouched.
    assert "warm-ink" in existing.read_text(encoding="utf-8")


def test_theme_new_force_overwrites(
    runner: CliRunner, scaffolded_project: Path
) -> None:
    target = scaffolded_project / "themes" / "classic.css"
    original = target.read_text(encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "theme", "new", "classic", "--from", "modern", "--force",
            "--project-dir", str(scaffolded_project),
        ],
    )
    assert result.exit_code == 0
    after = target.read_text(encoding="utf-8")
    assert after != original
    assert "Theme: classic" in after
