"""Shared pytest fixtures."""

from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path

import pytest

pandoc_required = pytest.mark.skipif(
    shutil.which("pandoc") is None,
    reason="pandoc is not installed in this environment",
)


@pytest.fixture
def scaffolded_project(tmp_path: Path) -> Path:
    """Copy the bundled templates into a temporary directory."""
    target = tmp_path / "resume"
    target.mkdir()

    with resources.as_file(resources.files("resume_md").joinpath("templates")) as src_root:
        src = Path(src_root)
        for item in src.rglob("*"):
            rel = item.relative_to(src)
            dest = target / rel
            if item.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

    from resume_md.manifest import (
        TRACKED_PATHS,
        Manifest,
        hash_file,
        save_manifest,
    )
    tracked: dict[str, str] = {}
    for rel in TRACKED_PATHS:
        bundled = src / rel
        if bundled.is_file():
            tracked[rel] = hash_file(bundled)
    save_manifest(target, Manifest(resume_md_version="0.2.0", tracked_files=tracked))

    return target
