"""Project manifest: tracks the SHA-256 of every shipped infrastructure file
at scaffold time so `resume-md update` can refresh them without overwriting
user edits.

Stored at ``.resume-md/manifest.json`` inside the user's project.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

MANIFEST_RELATIVE_PATH = ".resume-md/manifest.json"

# Files tracked by the manifest. NOT tracked: resume.md, headshot.svg,
# build outputs, anything the user owns.
TRACKED_PATHS: tuple[str, ...] = (
    "themes/_base.css",
    "themes/warm-ink.css",
    "themes/classic.css",
    "themes/modern.css",
    ".github/workflows/build-pdf.yaml",
    "Makefile",
)


@dataclass(frozen=True)
class Manifest:
    resume_md_version: str
    tracked_files: dict[str, str] = field(default_factory=dict)


def hash_file(path: Path) -> str:
    """Return a hex-encoded SHA-256 of the file at *path*, prefixed with ``sha256:``."""
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(8192), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def save_manifest(project_dir: Path, manifest: Manifest) -> None:
    path = project_dir / MANIFEST_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(manifest), indent=2) + "\n", encoding="utf-8")


def load_manifest(project_dir: Path) -> Manifest:
    path = project_dir / MANIFEST_RELATIVE_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    return Manifest(
        resume_md_version=data["resume_md_version"],
        tracked_files=dict(data.get("tracked_files", {})),
    )
