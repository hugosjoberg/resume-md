"""Project manifest: tracks the SHA-256 of every shipped infrastructure file
at scaffold time so `resume-md update` can refresh them without overwriting
user edits.

Stored at ``.resume-md/manifest.json`` inside the user's project.
"""

from __future__ import annotations

import enum
import hashlib
import json
from collections.abc import Mapping
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


class UpdateAction(str, enum.Enum):
    UPDATE = "update"            # safe to refresh — recorded hash matches local
    NO_CHANGE = "no-change"      # bundled identical to recorded; skip silently
    SKIPPED = "skipped"          # user-modified; do not touch
    HASH_REFRESH = "hash-refresh"  # user-modified, bundled unchanged: trust user, update recorded
    MISSING_LOCAL = "missing"    # file deleted by user; no-op


@dataclass(frozen=True)
class UpdatePlanItem:
    rel_path: str
    action: UpdateAction
    bundled_path: Path | None
    new_hash: str | None


def plan_update(
    *,
    project_dir: Path,
    recorded: Mapping[str, str],
    bundled: Mapping[str, Path],
) -> list[UpdatePlanItem]:
    """Decide what to do with each tracked file.

    Iterates the union of recorded keys and bundled keys so that newly-tracked
    files added in later package versions are delivered to projects scaffolded
    against older versions.

    Args:
        project_dir: where the user's project lives.
        recorded: rel_path → recorded sha256 from manifest (may be missing
            entries that were added to bundled in newer versions).
        bundled: rel_path → packaged template path inside resume_md.
    """
    items: list[UpdatePlanItem] = []
    all_keys = set(recorded) | set(bundled)
    for rel in sorted(all_keys):
        recorded_hash = recorded.get(rel)
        bundled_path = bundled.get(rel)
        local_path = project_dir / rel

        if not local_path.is_file():
            if bundled_path is not None and bundled_path.is_file() and recorded_hash is None:
                # New tracked file not yet in user's project — copy it in.
                bundled_hash = hash_file(bundled_path)
                items.append(
                    UpdatePlanItem(rel, UpdateAction.UPDATE, bundled_path, bundled_hash)
                )
            else:
                items.append(UpdatePlanItem(rel, UpdateAction.MISSING_LOCAL, bundled_path, None))
            continue
        if bundled_path is None or not bundled_path.is_file():
            items.append(UpdatePlanItem(rel, UpdateAction.NO_CHANGE, None, None))
            continue

        local_hash = hash_file(local_path)
        bundled_hash = hash_file(bundled_path)

        # New tracked file the user happens to already have:
        # treat as already-present, record current local hash.
        if recorded_hash is None:
            if local_hash == bundled_hash:
                items.append(
                    UpdatePlanItem(rel, UpdateAction.HASH_REFRESH, bundled_path, local_hash)
                )
            else:
                # User has their own version of a file we now track. Don't clobber.
                items.append(
                    UpdatePlanItem(rel, UpdateAction.HASH_REFRESH, bundled_path, local_hash)
                )
            continue

        user_modified = local_hash != recorded_hash
        bundled_changed = bundled_hash != recorded_hash

        if not user_modified and bundled_changed:
            items.append(
                UpdatePlanItem(rel, UpdateAction.UPDATE, bundled_path, bundled_hash)
            )
        elif not user_modified and not bundled_changed:
            items.append(UpdatePlanItem(rel, UpdateAction.NO_CHANGE, bundled_path, None))
        elif user_modified and bundled_changed:
            items.append(UpdatePlanItem(rel, UpdateAction.SKIPPED, bundled_path, None))
        else:  # user_modified and not bundled_changed
            items.append(
                UpdatePlanItem(rel, UpdateAction.HASH_REFRESH, bundled_path, local_hash)
            )
    return items
