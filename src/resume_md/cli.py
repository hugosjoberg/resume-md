"""resume-md command-line interface."""

from __future__ import annotations

import re
import shutil
import subprocess
from importlib import resources
from pathlib import Path
from typing import NoReturn

import typer

from . import __version__
from . import builder as _builder
from .builder import BuildError, discover_themes

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help=(
        "Print-quality PDF resumes from a single Markdown file. "
        "Pandoc + WeasyPrint with a deliberate, themeable design system."
    ),
)


def _fail_with_formatted(exc: BuildError, project_dir: Path) -> NoReturn:
    """Render a BuildError via ErrorFormatter and exit with code 1.

    Annotated ``NoReturn`` so static analyzers know the caller's flow stops
    here — otherwise references to ``result`` after the ``except`` block read
    as possibly-unbound.
    """
    from .errors import ErrorFormatter

    formatted = ErrorFormatter(project_dir=project_dir).format(str(exc))
    typer.secho(f"build failed: {formatted.message}", fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1) from exc


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"resume-md {__version__}")
        raise typer.Exit()


@app.callback()
def _main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Top-level CLI options."""


@app.command()
def init(
    path: Path = typer.Argument(
        Path("resume"),
        help="Directory to scaffold (will be created if missing).",
    ),
    force: bool = typer.Option(
        False, "--force", help="Overwrite files in PATH if they already exist."
    ),
) -> None:
    """Scaffold a new resume project from the bundled template."""
    target = path.resolve()
    target.mkdir(parents=True, exist_ok=True)

    with resources.as_file(resources.files("resume_md").joinpath("templates")) as templates:
        src = Path(templates)
        for item in src.rglob("*"):
            rel = item.relative_to(src)
            dest = target / rel
            if item.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
                continue
            if dest.exists() and not force:
                typer.echo(f"  skip {rel} (already exists; pass --force to overwrite)")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
            typer.echo(f"  write {rel}")

    # Write .resume-md/manifest.json with the hashes of the BUNDLED files —
    # not the local files. Recording bundled hashes is what lets `update`
    # detect user modifications: a local hash that differs from the recorded
    # (bundled) hash means the user edited the file. Recording the local
    # hashes here would silently bless user edits and `update` would later
    # overwrite them.
    from .manifest import TRACKED_PATHS, Manifest, hash_file, save_manifest
    tracked: dict[str, str] = {}
    with resources.as_file(resources.files("resume_md").joinpath("templates")) as templates_dir:
        for rel in TRACKED_PATHS:
            bundled_path = Path(templates_dir) / rel
            if bundled_path.is_file():
                tracked[rel] = hash_file(bundled_path)
    save_manifest(target, Manifest(resume_md_version=__version__, tracked_files=tracked))

    typer.echo(f"\nScaffolded resume project at {target}")
    typer.echo("Next steps:")
    typer.echo(f"  cd {target}")
    typer.echo("  resume-md doctor   # verify pandoc is installed")
    typer.echo("  resume-md build    # generate index.html + resume.pdf")


@app.command(name="build")
def build(
    theme: str = typer.Option(
        "warm-ink", "--theme", "-t", help="Theme name. See `resume-md themes`."
    ),
    project_dir: Path = typer.Option(
        Path("."), "--project-dir", "-C", help="Project directory (default: cwd)."
    ),
) -> None:
    """Generate index.html and resume.pdf in the project directory."""
    target = project_dir.resolve()
    try:
        result = _builder.build(project_dir=target, theme=theme)
    except BuildError as exc:
        _fail_with_formatted(exc, target)

    for warning in result.warnings:
        typer.secho(f"pandoc: {warning}", fg=typer.colors.YELLOW, err=True)
    typer.echo(f"wrote {result.html_path}")
    typer.echo(f"wrote {result.pdf_path}")


@app.command()
def preview(
    port: int = typer.Option(8000, "--port", "-p", help="HTTP port to listen on."),
    watch: bool = typer.Option(
        False, "--watch", "-w", help="Rebuild on changes to resume.md or themes/."
    ),
    theme: str = typer.Option(
        "warm-ink", "--theme", "-t", help="Theme to use when rebuilding (with --watch)."
    ),
    project_dir: Path = typer.Option(
        Path("."), "--project-dir", "-C", help="Project directory (default: cwd)."
    ),
    no_open: bool = typer.Option(
        False, "--no-open", help="Don't open a browser window automatically."
    ),
    no_live_reload: bool = typer.Option(
        False,
        "--no-live-reload",
        help="Disable browser auto-refresh and theme picker; serve static files only.",
    ),
) -> None:
    """Serve the built HTML on localhost. Use --watch for live rebuild."""
    from .preview import serve

    target = project_dir.resolve()
    if not (target / "index.html").is_file():
        typer.echo("index.html not found — running build first…")
        try:
            _builder.build(project_dir=target, theme=theme)
        except BuildError as exc:
            _fail_with_formatted(exc, target)

    serve(
        project_dir=target,
        port=port,
        watch=watch,
        theme=theme,
        open_browser=not no_open,
        live_reload=not no_live_reload,
    )


@app.command()
def themes(
    project_dir: Path = typer.Option(
        Path("."), "--project-dir", "-C", help="Project directory (default: cwd)."
    ),
) -> None:
    """List available themes (bundled + project-local)."""
    found = discover_themes(project_dir.resolve())
    if not found:
        typer.echo("No themes found.")
        raise typer.Exit(code=1)

    width = max(len(name) for name in found)
    for name, path in sorted(found.items()):
        # First non-blank comment line in the file is treated as its description.
        description = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip(" \t/*")
            if stripped and not stripped.startswith("Theme:"):
                description = stripped
                break
        marker = " (default)" if name == "warm-ink" else ""
        typer.echo(f"  {name:<{width}}  {description}{marker}")


theme_app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Operate on a single theme (scaffold, inspect variables).",
)
app.add_typer(theme_app, name="theme")


_THEME_HEADER_RE = re.compile(
    r"^/\*[\s\S]*?\*/\s*", re.MULTILINE
)


@theme_app.command(name="new")
def theme_new(
    name: str = typer.Argument(..., help="Name of the new theme (filename stem)."),
    from_: str = typer.Option(
        "warm-ink", "--from", help="Base theme to copy from. See `resume-md themes`."
    ),
    force: bool = typer.Option(
        False, "--force", help="Overwrite an existing theme file."
    ),
    project_dir: Path = typer.Option(
        Path("."), "--project-dir", "-C", help="Project directory (default: cwd)."
    ),
) -> None:
    """Scaffold a new theme file in <project>/themes/<name>.css."""
    target_dir = project_dir.resolve()
    themes = discover_themes(target_dir)
    if from_ not in themes:
        available = ", ".join(sorted(themes)) or "(none)"
        typer.secho(
            f"unknown base theme {from_!r}. Available: {available}.",
            fg=typer.colors.RED, err=True,
        )
        raise typer.Exit(code=1)
    source = themes[from_]

    destination = target_dir / "themes" / f"{name}.css"
    if destination.exists() and not force:
        typer.secho(
            f"{destination} already exists. Pass --force to overwrite.",
            fg=typer.colors.RED, err=True,
        )
        raise typer.Exit(code=1)
    destination.parent.mkdir(parents=True, exist_ok=True)

    source_text = source.read_text(encoding="utf-8")
    # Rewrite the leading /* ... */ comment block to name the new theme.
    new_header = (
        f"/*\n * Theme: {name}\n *\n"
        f" * Scaffolded from {from_}. Override variables on :root below to\n"
        f" * customize colors, fonts, and spacing.\n */\n\n"
    )
    if _THEME_HEADER_RE.match(source_text):
        body = _THEME_HEADER_RE.sub("", source_text, count=1)
    else:
        body = source_text
    destination.write_text(new_header + body, encoding="utf-8")

    typer.echo(f"wrote {destination} (based on {from_})")
    typer.echo(f"next: edit {destination} and run `resume-md build --theme {name}`")


@theme_app.command(name="vars")
def theme_vars(
    theme: str | None = typer.Option(
        None, "--theme", "-t",
        help="Show effective values after this theme overlays the base.",
    ),
    project_dir: Path = typer.Option(
        Path("."), "--project-dir", "-C", help="Project directory (default: cwd)."
    ),
) -> None:
    """List every CSS variable from _base.css with default (and effective) values."""
    target = project_dir.resolve()
    base_css = _builder._resolve_base_css(target)
    base_vars = _builder.parse_root_vars(base_css.read_text(encoding="utf-8"))

    overlay_vars: dict[str, str] = {}
    if theme:
        themes = discover_themes(target)
        if theme not in themes:
            available = ", ".join(sorted(themes)) or "(none)"
            typer.secho(
                f"unknown theme {theme!r}. Available: {available}.",
                fg=typer.colors.RED, err=True,
            )
            raise typer.Exit(code=1)
        overlay_vars = _builder.parse_root_vars(themes[theme].read_text(encoding="utf-8"))

    name_w = max(len(k) for k in base_vars) if base_vars else 0
    default_w = max(len(v) for v in base_vars.values()) if base_vars else 0

    header_cols = ["Variable", "Default"]
    if theme:
        header_cols.append(f"Effective ({theme})")
    typer.echo("  ".join(
        [header_cols[0].ljust(name_w), header_cols[1].ljust(default_w), *header_cols[2:]]
    ))
    for name, value in base_vars.items():
        cols = [name.ljust(name_w), value.ljust(default_w)]
        if theme:
            cols.append(overlay_vars.get(name, value))
        typer.echo("  ".join(cols))


@app.command()
def doctor() -> None:
    """Verify that required tools are installed and importable."""
    ok = True

    pandoc_path = shutil.which("pandoc")
    if pandoc_path is None:
        typer.secho("✗ pandoc: not found on PATH", fg=typer.colors.RED)
        typer.echo("    install: brew install pandoc (macOS) | apt-get install pandoc (Linux)")
        ok = False
    else:
        version = subprocess.run(
            ["pandoc", "--version"], capture_output=True, text=True, check=False
        ).stdout.splitlines()[0]
        typer.secho(f"✓ pandoc: {version} ({pandoc_path})", fg=typer.colors.GREEN)

    try:
        import weasyprint  # noqa: F401
    except ImportError:
        typer.secho("✗ weasyprint: not importable", fg=typer.colors.RED)
        typer.echo("    reinstall: pipx install resume-md")
        ok = False
    else:
        typer.secho(
            f"✓ weasyprint: {weasyprint.__version__} (Python module)",
            fg=typer.colors.GREEN,
        )

    if not ok:
        raise typer.Exit(code=1)


@app.command()
def update(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print the plan without modifying files."
    ),
    project_dir: Path = typer.Option(
        Path("."), "--project-dir", "-C", help="Project directory (default: cwd)."
    ),
) -> None:
    """Sync tracked infrastructure files from the installed package version."""
    import shutil as _shutil
    from importlib import resources as _resources

    from .manifest import (
        TRACKED_PATHS,
        Manifest,
        UpdateAction,
        load_manifest,
        plan_update,
        save_manifest,
    )

    target = project_dir.resolve()
    try:
        manifest = load_manifest(target)
    except FileNotFoundError:
        typer.secho(
            "no .resume-md/manifest.json — run `resume-md init` first"
            " or this project predates manifests.",
            fg=typer.colors.RED, err=True,
        )
        raise typer.Exit(code=1) from None

    with _resources.as_file(_resources.files("resume_md").joinpath("templates")) as templates_dir:
        bundled = {rel: Path(templates_dir) / rel for rel in TRACKED_PATHS}
        plan = plan_update(
            project_dir=target,
            recorded=manifest.tracked_files,
            bundled=bundled,
        )

        updated_count = 0
        skipped_count = 0
        new_tracked = dict(manifest.tracked_files)

        for item in plan:
            if item.action == UpdateAction.UPDATE:
                typer.echo(f"  update  {item.rel_path}")
                if not dry_run and item.bundled_path is not None and item.new_hash is not None:
                    dest = target / item.rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    _shutil.copy2(item.bundled_path, dest)
                    new_tracked[item.rel_path] = item.new_hash
                updated_count += 1
            elif item.action == UpdateAction.SKIPPED:
                typer.echo(f"  skip    {item.rel_path} (locally modified)")
                skipped_count += 1
            elif item.action == UpdateAction.HASH_REFRESH:
                if not dry_run and item.new_hash is not None:
                    new_tracked[item.rel_path] = item.new_hash
                # silent — no user-visible change
            elif item.action == UpdateAction.MISSING_LOCAL:
                typer.echo(f"  miss    {item.rel_path} (removed locally — leaving alone)")
            # NO_CHANGE: silent

        if not dry_run and new_tracked != manifest.tracked_files:
            save_manifest(target, Manifest(
                resume_md_version=__version__, tracked_files=new_tracked,
            ))

    suffix = " (dry run — no files written)" if dry_run else ""
    typer.echo(f"{updated_count} updated, {skipped_count} skipped{suffix}")


if __name__ == "__main__":  # pragma: no cover
    app()
