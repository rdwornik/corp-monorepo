"""Tests for scripts/find_orphans.py — orphan source file scanner.

Scanner is audit-only: it never edits files, only reports candidates.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "find_orphans.py"


@pytest.fixture(scope="module")
def find_orphans_module():
    """Load scripts/find_orphans.py as a module (not a package)."""
    spec = importlib.util.spec_from_file_location("find_orphans", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["find_orphans"] = module
    spec.loader.exec_module(module)
    return module


def test_module_to_dotted_path(find_orphans_module):
    """Converts src/corp/foo/bar.py to corp.foo.bar."""
    m = find_orphans_module
    src_root = REPO_ROOT / "src"
    file = REPO_ROOT / "src" / "corp" / "schema" / "models.py"
    assert m.module_to_dotted_path(file, src_root) == "corp.schema.models"


def test_module_to_dotted_path_top_level(find_orphans_module):
    """Converts src/corp/audit.py to corp.audit."""
    m = find_orphans_module
    src_root = REPO_ROOT / "src"
    file = REPO_ROOT / "src" / "corp" / "audit.py"
    assert m.module_to_dotted_path(file, src_root) == "corp.audit"


def test_excludes_init_files(find_orphans_module, tmp_path):
    """__init__.py files must be excluded from candidates."""
    m = find_orphans_module
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    init_file = tmp_path / "src" / "pkg" / "__init__.py"
    init_file.write_text("")
    regular = tmp_path / "src" / "pkg" / "mod.py"
    regular.write_text("")
    candidates = list(m.enumerate_candidates(tmp_path / "src" / "pkg"))
    paths = {c.path for c in candidates}
    assert regular.resolve() in paths
    assert init_file.resolve() not in paths


def test_excludes_conftest(find_orphans_module, tmp_path):
    """conftest.py is pytest magic; must be excluded."""
    m = find_orphans_module
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    conf = tmp_path / "src" / "pkg" / "conftest.py"
    conf.write_text("")
    regular = tmp_path / "src" / "pkg" / "real.py"
    regular.write_text("")
    candidates = list(m.enumerate_candidates(tmp_path / "src" / "pkg"))
    paths = {c.path for c in candidates}
    assert regular.resolve() in paths
    assert conf.resolve() not in paths


def test_cli_entry_points_recognized(find_orphans_module):
    """pyproject.toml entry points are resolved to file paths."""
    m = find_orphans_module
    src_root = REPO_ROOT / "src"
    entry_points = m.read_entry_point_modules(REPO_ROOT / "pyproject.toml")
    # Must contain at least the 5 known CLIs (corp, corp-meta, cke, cpe, com)
    assert "corp.cli" in entry_points
    assert "corp.schema.cli" in entry_points
    assert "corp.extractor.scripts.run" in entry_points
    assert "corp.project.cli" in entry_points
    assert "corp.opportunity.cli" in entry_points


def test_tach_module_roots_recognized(find_orphans_module):
    """tach.toml module paths are harvested as do-not-flag roots."""
    m = find_orphans_module
    roots = m.read_tach_module_roots(REPO_ROOT / "tach.toml")
    # Current tach.toml declares 32 modules; sanity-check a few canonical ones.
    assert "corp.schema" in roots
    assert "corp.cli" in roots
    assert "corp.ingest" in roots


def test_reports_zero_references_as_orphan(find_orphans_module, tmp_path):
    """A file with no importers anywhere is flagged as orphan."""
    m = find_orphans_module
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    # Orphan: defined but never imported
    orphan = tmp_path / "src" / "pkg" / "ghost.py"
    orphan.write_text("def ghost(): return 'boo'\n")
    # Non-orphan: referenced in another file
    live = tmp_path / "src" / "pkg" / "live.py"
    live.write_text("def hi(): return 1\n")
    (tmp_path / "tests" / "use.py").write_text("from pkg.live import hi\n")
    # Run
    scan_roots = [tmp_path / "src", tmp_path / "tests"]
    orphans = m.find_orphans(
        candidate_root=tmp_path / "src" / "pkg",
        scan_roots=scan_roots,
        src_root=tmp_path / "src",
        entry_point_modules=set(),
        tach_module_roots=set(),
    )
    orphan_paths = {o.path for o in orphans}
    assert orphan.resolve() in orphan_paths
    assert live.resolve() not in orphan_paths


def test_relative_import_in_package_init_counts_as_reference(find_orphans_module, tmp_path):
    """`from . import mod` in a sibling __init__.py must NOT be flagged as orphan."""
    m = find_orphans_module
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("from . import mod\n")
    mod = pkg / "mod.py"
    mod.write_text("def hi(): return 1\n")
    orphans = m.find_orphans(
        candidate_root=pkg,
        scan_roots=[tmp_path / "src"],
        src_root=tmp_path / "src",
        entry_point_modules=set(),
        tach_module_roots=set(),
    )
    assert all(o.path != mod.resolve() for o in orphans)


def test_relative_dotted_import_counts_as_reference(find_orphans_module, tmp_path):
    """`from .mod import something` must NOT flag mod as orphan."""
    m = find_orphans_module
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("from .mod import thing\n")
    mod = pkg / "mod.py"
    mod.write_text("thing = 1\n")
    orphans = m.find_orphans(
        candidate_root=pkg,
        scan_roots=[tmp_path / "src"],
        src_root=tmp_path / "src",
        entry_point_modules=set(),
        tach_module_roots=set(),
    )
    assert all(o.path != mod.resolve() for o in orphans)


def test_absolute_submodule_import_with_parens_counts_as_reference(
    find_orphans_module, tmp_path
):
    """`from pkg import (a, b, c)` spanning multiple lines must count each submodule."""
    m = find_orphans_module
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text(
        "from pkg import (\n    first,\n    second,\n    third,\n)\n"
    )
    for name in ("first", "second", "third"):
        (pkg / f"{name}.py").write_text("x = 1\n")
    orphans = m.find_orphans(
        candidate_root=pkg,
        scan_roots=[tmp_path / "src"],
        src_root=tmp_path / "src",
        entry_point_modules=set(),
        tach_module_roots=set(),
    )
    orphan_names = {o.module for o in orphans}
    for name in ("first", "second", "third"):
        assert f"pkg.{name}" not in orphan_names


def test_entry_point_files_never_flagged(find_orphans_module, tmp_path):
    """Files registered as CLI entry points in pyproject are never orphans."""
    m = find_orphans_module
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    entry_file = tmp_path / "src" / "pkg" / "cli.py"
    entry_file.write_text("def cli(): pass\n")
    orphans = m.find_orphans(
        candidate_root=tmp_path / "src" / "pkg",
        scan_roots=[tmp_path / "src"],
        src_root=tmp_path / "src",
        entry_point_modules={"pkg.cli"},
        tach_module_roots=set(),
    )
    assert all(o.path != entry_file.resolve() for o in orphans)
