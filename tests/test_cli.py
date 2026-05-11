"""CLI surface tests using Typer's CliRunner."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from resume_md import __version__
from resume_md.cli import app

from .conftest import pandoc_required


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_version_flag(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_themes_lists_bundled(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(app, ["themes", "--project-dir", str(tmp_path)])
    assert result.exit_code == 0
    for name in ("warm-ink", "classic", "modern"):
        assert name in result.stdout
    assert "(default)" in result.stdout


def test_init_creates_files(runner: CliRunner, tmp_path: Path) -> None:
    target = tmp_path / "out"
    result = runner.invoke(app, ["init", str(target)])
    assert result.exit_code == 0, result.stdout
    assert (target / "resume.md").is_file()
    assert (target / "themes" / "_base.css").is_file()
    assert (target / "themes" / "warm-ink.css").is_file()
    assert (target / ".github" / "workflows" / "build-pdf.yaml").is_file()


def test_init_skips_existing_files_without_force(
    runner: CliRunner, tmp_path: Path
) -> None:
    target = tmp_path / "out"
    target.mkdir()
    (target / "resume.md").write_text("PRESERVED\n", encoding="utf-8")

    result = runner.invoke(app, ["init", str(target)])
    assert result.exit_code == 0
    assert (target / "resume.md").read_text(encoding="utf-8") == "PRESERVED\n"


def test_init_force_overwrites(runner: CliRunner, tmp_path: Path) -> None:
    target = tmp_path / "out"
    target.mkdir()
    (target / "resume.md").write_text("OLD\n", encoding="utf-8")

    result = runner.invoke(app, ["init", str(target), "--force"])
    assert result.exit_code == 0
    assert "Jane Doe" in (target / "resume.md").read_text(encoding="utf-8")


@pandoc_required
def test_build_runs_end_to_end(
    runner: CliRunner, scaffolded_project: Path
) -> None:
    result = runner.invoke(
        app, ["build", "--project-dir", str(scaffolded_project)]
    )
    assert result.exit_code == 0, result.stdout
    assert (scaffolded_project / "resume.pdf").is_file()


@pandoc_required
def test_doctor_succeeds_when_tools_present(runner: CliRunner) -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "pandoc" in result.stdout
    assert "weasyprint" in result.stdout
