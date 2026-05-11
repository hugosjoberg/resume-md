"""Tests for the project manifest used by `resume-md update`."""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_md.manifest import (
    MANIFEST_RELATIVE_PATH,
    Manifest,
    hash_file,
    load_manifest,
    save_manifest,
)


def test_hash_file_is_stable(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("hello world\n", encoding="utf-8")
    h1 = hash_file(f)
    h2 = hash_file(f)
    assert h1 == h2
    assert h1.startswith("sha256:")


def test_hash_file_differs_for_different_content(tmp_path: Path) -> None:
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("x", encoding="utf-8")
    b.write_text("y", encoding="utf-8")
    assert hash_file(a) != hash_file(b)


def test_save_then_load_roundtrips(tmp_path: Path) -> None:
    m = Manifest(
        resume_md_version="0.2.0",
        tracked_files={"themes/_base.css": "sha256:abc", "Makefile": "sha256:def"},
    )
    save_manifest(tmp_path, m)
    assert (tmp_path / MANIFEST_RELATIVE_PATH).is_file()
    loaded = load_manifest(tmp_path)
    assert loaded == m


def test_load_missing_manifest_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_manifest(tmp_path)


def test_plan_update_actions(tmp_path: Path) -> None:
    """The update planner classifies each tracked file correctly."""
    from resume_md.manifest import UpdateAction, plan_update

    # Set up a fake project: themes/_base.css matches recorded hash (safe to update),
    # themes/warm-ink.css is modified locally (should be skipped if bundled changed).
    base_local = tmp_path / "themes" / "_base.css"
    base_local.parent.mkdir(parents=True)
    base_local.write_text("ORIGINAL\n", encoding="utf-8")
    warmink_local = tmp_path / "themes" / "warm-ink.css"
    warmink_local.write_text("MODIFIED BY USER\n", encoding="utf-8")

    recorded = {
        "themes/_base.css": hash_file(base_local),
        "themes/warm-ink.css": "sha256:original-hash-not-current",
        "missing-locally.txt": "sha256:doesnt-matter",
    }
    bundled_paths = {
        "themes/_base.css": tmp_path / "fake-bundled-base.css",
        "themes/warm-ink.css": tmp_path / "fake-bundled-warmink.css",
        "missing-locally.txt": tmp_path / "fake-bundled-missing.txt",
    }
    bundled_paths["themes/_base.css"].write_text("UPSTREAM CHANGED\n", encoding="utf-8")
    bundled_paths["themes/warm-ink.css"].write_text("UPSTREAM CHANGED TOO\n", encoding="utf-8")
    bundled_paths["missing-locally.txt"].write_text("anything\n", encoding="utf-8")

    plan = plan_update(
        project_dir=tmp_path,
        recorded=recorded,
        bundled=bundled_paths,
    )
    actions = {item.rel_path: item.action for item in plan}
    assert actions["themes/_base.css"] == UpdateAction.UPDATE
    assert actions["themes/warm-ink.css"] == UpdateAction.SKIPPED
    assert actions["missing-locally.txt"] == UpdateAction.MISSING_LOCAL
