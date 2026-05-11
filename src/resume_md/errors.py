"""Render pandoc/weasyprint stderr into actionable messages.

The same FormattedError feeds both the terminal output and the in-browser
overlay, so a user sees identical text whether they're looking at the
console or the preview window.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_MISSING_SOURCE_RE = re.compile(
    r"resume\.md: openBinaryFile: does not exist", re.IGNORECASE
)
_PANDOC_LINE_RE = re.compile(
    r'(?:Error|error) at "(?P<file>[^"]+)" line (?P<line>\d+), column (?P<col>\d+):',
)
_MISSING_IMAGE_RE = re.compile(
    r"Could not fetch resource '(?P<path>[^']+)'", re.IGNORECASE
)


@dataclass(frozen=True)
class FormattedError:
    """Rendered, user-facing error text. ``raw`` preserved for `--debug`."""

    message: str
    raw: str


class ErrorFormatter:
    """Turn raw stderr from the build pipeline into a friendly message."""

    def __init__(self, project_dir: Path) -> None:
        self._project_dir = project_dir

    def format(self, stderr: str) -> FormattedError:
        if not stderr.strip():
            return FormattedError(
                message="Build failed (no error details captured).",
                raw=stderr,
            )

        if _MISSING_SOURCE_RE.search(stderr):
            return FormattedError(
                message=(
                    "resume.md not found — run `resume-md init` to scaffold "
                    "a project here, or check the project directory."
                ),
                raw=stderr,
            )

        m = _PANDOC_LINE_RE.search(stderr)
        if m:
            file_name = m.group("file")
            line_no = int(m.group("line"))
            context = self._line_context(file_name, line_no)
            return FormattedError(
                message=f"{stderr.strip()}\n\n{context}",
                raw=stderr,
            )

        m = _MISSING_IMAGE_RE.search(stderr)
        if m:
            path = m.group("path")
            return FormattedError(
                message=(
                    f"{path} not found — remove the <img> tag from resume.md "
                    f"or supply a file at this path."
                ),
                raw=stderr,
            )

        # Unknown pattern: surface the raw stderr unchanged.
        return FormattedError(message=stderr.strip(), raw=stderr)

    def _line_context(self, file_name: str, line_no: int) -> str:
        path = self._project_dir / file_name
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return ""
        lo = max(0, line_no - 2)
        hi = min(len(lines), line_no + 1)
        out = []
        for i in range(lo, hi):
            marker = "→" if (i + 1) == line_no else " "
            out.append(f"  {marker} {i + 1:4} | {lines[i]}")
        return "\n".join(out)
