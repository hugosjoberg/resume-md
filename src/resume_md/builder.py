"""Resume build pipeline: Markdown → HTML (Pandoc) → PDF (WeasyPrint)."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

_H1_RE = re.compile(r"<h1[^>]*>([^<]+)</h1>", re.IGNORECASE)
_ROLE_RE = re.compile(r'class="role"[^>]*>([^<]+)</span>', re.IGNORECASE)

_ROOT_BLOCK_RE = re.compile(r":root\s*\{([^}]*)\}", re.DOTALL)
_VAR_DECL_RE = re.compile(r"^\s*(--[a-zA-Z0-9-]+)\s*:\s*(.+?)\s*;?\s*$", re.MULTILINE)


def parse_root_vars(css_text: str) -> dict[str, str]:
    """Extract `--name: value` declarations from every `:root { ... }` block.

    Later blocks override earlier ones (matches CSS cascade for same-specificity
    rules). Returns a dict in declaration order (Python 3.7+ dict ordering).
    """
    declarations: dict[str, str] = {}
    for block in _ROOT_BLOCK_RE.finditer(css_text):
        body = block.group(1)
        for decl in _VAR_DECL_RE.finditer(body):
            declarations[decl.group(1)] = decl.group(2).strip()
    return declarations


def _parse_pandoc_warnings(stderr: str) -> tuple[str, ...]:
    """Pull `[WARNING] ...` entries out of pandoc's stderr.

    Continuation lines (whitespace-indented, immediately following a
    `[WARNING]` header) are folded into the warning they continue, so a
    multi-line warning is reported as a single entry. Other lines (status,
    info, blank) are ignored. Order is preserved.
    """
    entries: list[str] = []
    for line in stderr.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("[WARNING]"):
            entries.append(stripped[len("[WARNING]"):].strip())
        elif entries and line and line[0] in (" ", "\t"):
            entries[-1] += " " + stripped
    return tuple(entries)


def _extract_page_title(source: Path) -> str:
    """Pull a reasonable HTML <title> from the resume's name + role block.

    Pandoc warns when no title is set; this avoids that warning without
    forcing users to add YAML front-matter for something the file already
    carries (the H1 + role span).
    """
    text = source.read_text(encoding="utf-8")
    name_match = _H1_RE.search(text)
    if not name_match:
        return source.stem
    name = name_match.group(1).strip()
    role_match = _ROLE_RE.search(text)
    if role_match:
        return f"{name} — {role_match.group(1).strip()}"
    return name


PACKAGED_THEMES = ("warm-ink", "classic", "modern")


class BuildError(RuntimeError):
    """Raised when a required step in the build pipeline fails."""


@dataclass(frozen=True)
class BuildResult:
    html_path: Path
    pdf_path: Path
    warnings: tuple[str, ...] = ()


def discover_themes(project_dir: Path) -> dict[str, Path]:
    """Return name → CSS path for every theme available to this project.

    Project-local themes (project_dir/themes/*.css) shadow packaged ones with
    the same stem. The shared `_base.css` is excluded — it's structural, not a
    theme on its own.
    """
    themes: dict[str, Path] = {}

    with resources.as_file(resources.files("resume_md").joinpath("templates/themes")) as packaged:
        for css in sorted(Path(packaged).glob("*.css")):
            if css.stem.startswith("_"):
                continue
            themes[css.stem] = css

    local_dir = project_dir / "themes"
    if local_dir.is_dir():
        for css in sorted(local_dir.glob("*.css")):
            if css.stem.startswith("_"):
                continue
            themes[css.stem] = css

    return themes


def _resolve_base_css(project_dir: Path) -> Path:
    local_base = project_dir / "themes" / "_base.css"
    if local_base.is_file():
        return local_base
    with resources.as_file(
        resources.files("resume_md").joinpath("templates/themes/_base.css")
    ) as packaged:
        return Path(packaged)


def _check_pandoc() -> str:
    if shutil.which("pandoc") is None:
        raise BuildError(
            "pandoc is not on PATH. Install it: brew install pandoc (macOS) "
            "or apt-get install pandoc (Debian/Ubuntu)."
        )
    result = subprocess.run(
        ["pandoc", "--version"], capture_output=True, text=True, check=True
    )
    return result.stdout.splitlines()[0]


def build(
    project_dir: Path,
    theme: str = "warm-ink",
    source: str = "resume.md",
    html_name: str = "index.html",
    pdf_name: str = "resume.pdf",
) -> BuildResult:
    """Build HTML and PDF artifacts inside `project_dir`.

    Concatenates `themes/_base.css` with the chosen theme stylesheet, then runs:

        pandoc --standalone --css <combined> --embed-resources <source> -o <html>
        weasyprint <html> <pdf>

    `--embed-resources` inlines CSS and base64-embeds image references, so the
    resulting HTML is a single self-contained file (suitable for sharing or
    hosting on GitHub Pages directly).
    """
    project_dir = project_dir.resolve()
    source_path = project_dir / source
    if not source_path.is_file():
        raise BuildError(f"Source file not found: {source_path}")

    themes = discover_themes(project_dir)
    if theme not in themes:
        available = ", ".join(sorted(themes)) or "(none)"
        raise BuildError(f"Unknown theme {theme!r}. Available: {available}.")

    _check_pandoc()

    base_css = _resolve_base_css(project_dir)
    theme_css = themes[theme]
    html_path = project_dir / html_name
    pdf_path = project_dir / pdf_name

    # Base first, theme last: both files declare :root with the same
    # specificity, so the later one wins in the cascade. The theme is meant
    # to *override* base defaults, so it must be written second.
    with tempfile.NamedTemporaryFile(
        "w", suffix=".css", delete=False, encoding="utf-8"
    ) as combined:
        combined.write("/* base */\n")
        combined.write(base_css.read_text(encoding="utf-8"))
        combined.write(f"\n/* theme: {theme} */\n")
        combined.write(theme_css.read_text(encoding="utf-8"))
        combined_path = Path(combined.name)

    page_title = _extract_page_title(source_path)

    try:
        proc = subprocess.run(
            [
                "pandoc",
                str(source_path),
                "--standalone",
                "--css",
                str(combined_path),
                "--embed-resources",
                "--metadata",
                f"pagetitle={page_title}",
                "-o",
                str(html_path),
            ],
            check=True,
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        detail = f"\n{stderr}" if stderr else ""
        raise BuildError(f"pandoc failed (exit {exc.returncode}).{detail}") from exc
    finally:
        combined_path.unlink(missing_ok=True)

    warnings = _parse_pandoc_warnings(proc.stderr or "")

    # WeasyPrint as a library — avoids a second process and surfaces real
    # Python exceptions when something is malformed.
    try:
        from weasyprint import HTML
    except ImportError as exc:  # pragma: no cover - dependency declared
        raise BuildError(
            "weasyprint is not importable. Reinstall resume-md (pipx install resume-md)."
        ) from exc

    HTML(filename=str(html_path)).write_pdf(target=str(pdf_path))

    return BuildResult(html_path=html_path, pdf_path=pdf_path, warnings=warnings)
