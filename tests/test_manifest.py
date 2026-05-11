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
