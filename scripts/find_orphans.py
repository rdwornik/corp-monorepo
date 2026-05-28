"""Orphan source-file scanner.

Enumerates every non-__init__ .py file under a candidate root and reports any
that are not imported, referenced, or registered as an entry point anywhere in
the repository. Audit-only — never edits files.

Usage:
    python scripts/find_orphans.py                     # default paths, write JSON
    python scripts/find_orphans.py --repo-root /path   # override repo root
    python scripts/find_orphans.py --print-only        # skip JSON write

Output:
    .audit/orphan-candidates.json with fields: path, module, last_modified,
    classification_hint.
"""

from __future__ import annotations

import json
import logging
import re
import tomllib
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

console = Console()
logger = logging.getLogger("find_orphans")


@dataclass(frozen=True)
class OrphanCandidate:
    path: Path
    module: str
    last_modified: str
    classification_hint: str


def module_to_dotted_path(file: Path, src_root: Path) -> str:
    """Convert src/corp/foo/bar.py → corp.foo.bar."""
    rel = file.resolve().relative_to(src_root.resolve())
    parts = rel.with_suffix("").parts
    return ".".join(parts)


def enumerate_candidates(candidate_root: Path) -> Iterator[OrphanCandidate]:
    """Yield every .py file under candidate_root except __init__.py, __main__.py, conftest.py."""
    for file in sorted(candidate_root.rglob("*.py")):
        if file.name in {"__init__.py", "__main__.py", "conftest.py"}:
            continue
        mtime = datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc)
        yield OrphanCandidate(
            path=file.resolve(),
            module="",
            last_modified=mtime.isoformat(timespec="seconds"),
            classification_hint="",
        )


def read_entry_point_modules(pyproject_path: Path) -> set[str]:
    """Return the dotted module names registered under [project.scripts]."""
    with pyproject_path.open("rb") as fh:
        data = tomllib.load(fh)
    scripts = data.get("project", {}).get("scripts", {}) or {}
    modules: set[str] = set()
    for target in scripts.values():
        # "corp.cli:cli" → "corp.cli"
        if ":" in target:
            modules.add(target.split(":", 1)[0])
        else:
            modules.add(target)
    return modules


def read_tach_module_roots(tach_path: Path) -> set[str]:
    """Return the `path = "..."` values declared under [[modules]] in tach.toml."""
    with tach_path.open("rb") as fh:
        data = tomllib.load(fh)
    modules = data.get("modules", []) or []
    return {m["path"] for m in modules if "path" in m}


def _scan_files(scan_roots: Iterable[Path]) -> list[Path]:
    """Flatten scan_roots into a list of .py/.toml files to grep."""
    collected: list[Path] = []
    for root in scan_roots:
        if not root.exists():
            continue
        if root.is_file():
            collected.append(root)
            continue
        for pattern in ("*.py", "*.toml"):
            collected.extend(root.rglob(pattern))
    return collected


def _build_module_regex(module: str) -> re.Pattern[str]:
    """Match `corp.foo.bar` surrounded by non-identifier characters.

    Catches: `import corp.foo.bar`, `from corp.foo.bar import ...`,
    string references in entry points, Click invocations, etc.
    """
    return re.compile(rf"(?<![\w.]){re.escape(module)}(?![\w])")


def _build_relative_import_regex(leaf: str) -> re.Pattern[str]:
    """Match relative imports inside the module's parent package.

    Catches: `from . import leaf`, `from .leaf import ...`,
    `from .. import leaf`, `from ..leaf import ...`, including comma-separated
    lists on the same line.
    """
    return re.compile(
        rf"from\s+\.+{re.escape(leaf)}\s+import\b"
        rf"|from\s+\.+\s+import\s+[^\n]*\b{re.escape(leaf)}\b"
    )


def _build_submodule_import_regex(parent: str, leaf: str) -> re.Pattern[str]:
    """Match `from <parent> import <leaf>` including multi-line parenthesized lists.

    Example matched: ``from corp.actions import (\n    deck_actions,\n)``.
    """
    return re.compile(
        rf"from\s+{re.escape(parent)}\s+import\s*(?:\([^)]*\b{re.escape(leaf)}\b[^)]*\)"
        rf"|[^\n(]*\b{re.escape(leaf)}\b)",
        re.MULTILINE,
    )


def find_orphans(
    *,
    candidate_root: Path,
    scan_roots: Iterable[Path],
    src_root: Path,
    entry_point_modules: set[str],
    tach_module_roots: set[str],
) -> list[OrphanCandidate]:
    """Return the list of candidates with zero references anywhere in scan_roots."""
    scan_files = _scan_files(scan_roots)
    orphans: list[OrphanCandidate] = []
    for raw in enumerate_candidates(candidate_root):
        module = module_to_dotted_path(raw.path, src_root)
        if module in entry_point_modules:
            continue
        if module in tach_module_roots:
            # tach declares this as a module boundary; not an orphan
            continue
        abs_pattern = _build_module_regex(module)
        rel_pattern = _build_relative_import_regex(raw.path.stem)
        parent_pkg = raw.path.parent.resolve()
        parent_module = module.rsplit(".", 1)[0] if "." in module else ""
        submodule_pattern = (
            _build_submodule_import_regex(parent_module, raw.path.stem)
            if parent_module
            else None
        )
        # Self-reference doesn't count; compare resolved paths
        found = False
        for sf in scan_files:
            if sf.resolve() == raw.path:
                continue
            try:
                text = sf.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue
            if abs_pattern.search(text):
                found = True
                break
            if submodule_pattern is not None and submodule_pattern.search(text):
                found = True
                break
            # Relative imports are scoped to sibling modules in the same package tree.
            try:
                if parent_pkg in sf.resolve().parents or sf.resolve().parent == parent_pkg:
                    if rel_pattern.search(text):
                        found = True
                        break
            except OSError:
                continue
        if not found:
            hint = _classify(raw.path, module)
            orphans.append(
                OrphanCandidate(
                    path=raw.path,
                    module=module,
                    last_modified=raw.last_modified,
                    classification_hint=hint,
                )
            )
    return orphans


def _classify(path: Path, module: str) -> str:
    name = path.name
    parts = module.split(".")
    if "archive" in parts or "archived" in parts:
        return "archived"
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        text = ""
    if re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', text):
        return "runnable-script"
    if name.startswith("_") and name != "__init__.py":
        return "private-helper"
    if "scripts" in parts:
        return "script-only"
    if path.stat().st_size < 512:
        return "stub-or-placeholder"
    return "candidate-for-deletion"


def _render(orphans: list[OrphanCandidate], total_scanned: int) -> None:
    table = Table(title="Orphan Candidates")
    table.add_column("module", overflow="fold")
    table.add_column("hint")
    table.add_column("last_modified")
    for o in orphans:
        table.add_row(o.module, o.classification_hint, o.last_modified)
    console.print(table)
    console.print(
        f"[bold]{len(orphans)}[/bold] orphan(s) in [bold]{total_scanned}[/bold] candidate files."
    )


@click.command()
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path(__file__).resolve().parents[1],
    help="Repository root (default: parent of scripts/).",
)
@click.option(
    "--candidate-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Directory to scan for orphan candidates (default: <repo-root>/src/corp).",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="JSON output (default: <repo-root>/.audit/orphan-candidates.json).",
)
@click.option("--print-only", is_flag=True, help="Skip JSON write; only print the table.")
def main(
    repo_root: Path, candidate_root: Path | None, output: Path | None, print_only: bool
) -> None:
    """Report source files under src/corp/ that no other file references."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(console=console, show_path=False, show_time=False)],
    )
    repo_root = repo_root.resolve()
    src_root = repo_root / "src"
    candidate_root = (candidate_root or src_root / "corp").resolve()
    output = (output or repo_root / ".audit" / "orphan-candidates.json").resolve()

    entry_points = read_entry_point_modules(repo_root / "pyproject.toml")
    tach_roots = read_tach_module_roots(repo_root / "tach.toml")
    logger.info("repo_root=%s", repo_root)
    logger.info("entry points: %s", sorted(entry_points))
    logger.info("tach module roots: %d", len(tach_roots))

    scan_roots = [
        repo_root / "src",
        repo_root / "tests",
        repo_root / "scripts",
        repo_root / "pyproject.toml",
    ]
    all_candidates = list(enumerate_candidates(candidate_root))
    orphans = find_orphans(
        candidate_root=candidate_root,
        scan_roots=scan_roots,
        src_root=src_root,
        entry_point_modules=entry_points,
        tach_module_roots=tach_roots,
    )

    _render(orphans, total_scanned=len(all_candidates))

    if not print_only:
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {**asdict(o), "path": str(o.path).replace("\\", "/")} for o in orphans
        ]
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info("wrote %s", output)


if __name__ == "__main__":
    main()
