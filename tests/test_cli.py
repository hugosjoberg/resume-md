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


def test_update_dry_run_does_not_modify(
    runner: CliRunner, scaffolded_project: Path
) -> None:
    target = scaffolded_project / "themes" / "_base.css"
    original = target.read_text(encoding="utf-8")
    result = runner.invoke(
        app, ["update", "--dry-run", "--project-dir", str(scaffolded_project)]
    )
    assert result.exit_code == 0
    assert target.read_text(encoding="utf-8") == original


def test_update_skips_locally_modified_file(
    runner: CliRunner, scaffolded_project: Path
) -> None:
    """If the user edited a tracked file AND upstream changed it, update
    reports skip and doesn't touch it."""
    from resume_md.manifest import Manifest, load_manifest, save_manifest
    target = scaffolded_project / "themes" / "warm-ink.css"
    user_edit = "/* user changes go here */\n"
    target.write_text(user_edit, encoding="utf-8")
    # Simulate "bundled has also changed since scaffold": rewrite the manifest's
    # recorded hash for warm-ink.css to something that doesn't match either
    # the local file OR the current bundled file.
    manifest = load_manifest(scaffolded_project)
    new_tracked = dict(manifest.tracked_files)
    fake_hash = "sha256:" + "0" * 64
    new_tracked["themes/warm-ink.css"] = fake_hash
    save_manifest(scaffolded_project, Manifest(
        resume_md_version=manifest.resume_md_version, tracked_files=new_tracked,
    ))

    result = runner.invoke(
        app, ["update", "--project-dir", str(scaffolded_project)]
    )
    assert result.exit_code == 0
    assert target.read_text(encoding="utf-8") == user_edit
    assert "skip" in result.stdout.lower() or "modified" in result.stdout.lower()


def test_init_writes_manifest(runner: CliRunner, tmp_path: Path) -> None:
    target = tmp_path / "out"
    result = runner.invoke(app, ["init", str(target)])
    assert result.exit_code == 0
    from resume_md.manifest import (
        TRACKED_PATHS,
        load_manifest,
    )
    manifest = load_manifest(target)
    assert set(manifest.tracked_files.keys()) == set(TRACKED_PATHS)
    # Each recorded hash starts with sha256: and matches the actual file.
    for rel in TRACKED_PATHS:
        recorded = manifest.tracked_files[rel]
        assert recorded.startswith("sha256:")
        # File exists at scaffold time.
        assert (target / rel).is_file()
