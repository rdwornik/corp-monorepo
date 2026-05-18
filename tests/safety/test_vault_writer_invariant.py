"""Vault single-writer invariant (ADR-27 Decision 2).

Walks every module under ``src/corp/actions/`` and, for each file-mutation
primitive whose target path is rooted at ``<something>.vault_path``, resolves
the path's first segment (zone) and its leaf filename, then maps the
``(zone, leaf)`` pair to one of the three ADR-27 action-write categories —
``DASHBOARDS``, ``METADATA``, or ``BRIEFS`` — and asserts that category is
whitelisted by :func:`corp.vault_io.is_writable_by_actions`.

Classification table (per ADR-27 line 122; ``index.md`` evidence: see the
``actions/vault_actions.py`` stub writer and the codebase's universal
``SKIP_FILENAMES = {"synthesis.md", "index.md"}`` treatment in
``freshness_scanner.py``/``integrity.py``/``ingest/extractions.py``):

============================  ===========================  ===========
top-level zone segment        leaf filename                 → category
============================  ===========================  ===========
``dashboards`` (or alias)     any                           DASHBOARDS
``projects``                  ``project-info.yaml``         METADATA
``projects``                  ``index.md``                  METADATA
``projects``                  ``brief.md``                  BRIEFS
``projects``                  anything else                 VIOLATION
``02_sources`` / other        any                           VIOLATION
============================  ===========================  ===========

Writes to non-whitelisted categories — notably ``02_sources/`` — must route
through :func:`corp.vault_io.write_note`.

Self-tests: embedded fixture strings exercise each branch (a SOURCES
violation, a clean METADATA write, an unclassified PROJECTS-zone leaf). A
silently-broken scanner fails its own test.
"""

from __future__ import annotations

import ast
import time
from pathlib import Path
from typing import Iterable

import pytest
from corp.models import VaultZone
from corp.vault_io import is_writable_by_actions

ACTIONS_DIR = Path(__file__).resolve().parents[2] / "src" / "corp" / "actions"

# Path methods that mutate the receiver's file/directory.
_PATH_MUTATOR_METHODS: frozenset[str] = frozenset(
    {"write_text", "write_bytes", "replace", "unlink", "rmdir"}
)

# shutil functions: name → index of the destination path arg.
_SHUTIL_DESTINATION: dict[str, int] = {
    "copy": 1,
    "copy2": 1,
    "copytree": 1,
    "move": 1,
    "rmtree": 0,
}

# os functions: name → index of the mutating path arg.
_OS_DESTINATION: dict[str, int] = {
    "remove": 0,
    "unlink": 0,
    "rename": 1,
}

# Open modes that mutate the file.
_OPEN_WRITE_MODES: frozenset[str] = frozenset({"w", "wb", "a", "ab", "x", "xb"})

# Aliases for known string literals that don't match a VaultZone value exactly.
# Codifies the documented drift in analytics_actions.py:99 (uses "00_dashboards"
# instead of VaultZone.DASHBOARDS = "dashboards"). The drift itself is tracked
# separately.
_ZONE_ALIASES: dict[str, VaultZone] = {
    "00_dashboards": VaultZone.DASHBOARDS,
}

# Leaf filename → action-write category, when the structural zone is PROJECTS.
# Derived from ADR-27 line 122 (DASHBOARDS, METADATA, BRIEFS) plus the
# index.md classification rationale in the PR-4 JOURNAL entry.
_PROJECTS_LEAF_CATEGORY: dict[str, VaultZone] = {
    "project-info.yaml": VaultZone.METADATA,
    "index.md": VaultZone.METADATA,
    "brief.md": VaultZone.BRIEFS,
}

# Performance budget for the full scan.
_PERFORMANCE_BUDGET_SECONDS = 5.0


class _MutationFinding:
    __slots__ = ("file", "lineno", "primitive", "zone", "leaf", "category", "note")

    def __init__(
        self,
        file: str,
        lineno: int,
        primitive: str,
        zone: VaultZone | None,
        leaf: str | None,
        category: VaultZone | None,
        note: str = "",
    ) -> None:
        self.file = file
        self.lineno = lineno
        self.primitive = primitive
        self.zone = zone
        self.leaf = leaf
        self.category = category
        self.note = note

    def __repr__(self) -> str:
        zone_name = self.zone.name if self.zone else "?"
        cat_name = self.category.name if self.category else "UNCLASSIFIED"
        return (
            f"{self.file}:{self.lineno} {self.primitive} "
            f"zone={zone_name} leaf={self.leaf!r} -> {cat_name}"
            f"{(' ' + self.note) if self.note else ''}"
        )


def _build_locals_map(func: ast.AST) -> dict[str, ast.expr]:
    """Map local Name targets to their last assigned expression in this function."""
    locals_map: dict[str, ast.expr] = {}
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    locals_map[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            if isinstance(node.target, ast.Name):
                locals_map[node.target.id] = node.value
    return locals_map


def _collect_path_segments(
    expr: ast.expr,
    locals_map: dict[str, ast.expr],
    depth: int = 0,
) -> tuple[ast.expr, list[ast.expr]]:
    """Return ``(base_expr, segments)`` for a ``base / s1 / s2 / ...`` path.

    Resolves intermediate local-variable references. Returns the leftmost
    non-resolvable expression as ``base_expr`` and the right-hand operands of
    every ``/`` in left-to-right order.
    """
    if depth > 50:
        return expr, []
    while isinstance(expr, ast.Name) and expr.id in locals_map:
        expr = locals_map[expr.id]
        depth += 1
        if depth > 50:
            return expr, []
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Div):
        base, segs = _collect_path_segments(expr.left, locals_map, depth + 1)
        return base, segs + [expr.right]
    return expr, []


def _is_vault_path_base(expr: ast.expr) -> bool:
    """``something.vault_path`` — any object whose attribute is ``vault_path``."""
    return isinstance(expr, ast.Attribute) and expr.attr == "vault_path"


def _resolve_segment_to_zone_value(seg: ast.expr) -> str | None:
    """Return the string value of a path segment, if statically resolvable."""
    if isinstance(seg, ast.Constant) and isinstance(seg.value, str):
        return seg.value
    if isinstance(seg, ast.Attribute):
        # VaultZone.X.value
        if (
            seg.attr == "value"
            and isinstance(seg.value, ast.Attribute)
            and isinstance(seg.value.value, ast.Name)
            and seg.value.value.id == "VaultZone"
        ):
            try:
                return VaultZone[seg.value.attr].value
            except KeyError:
                return None
        # Bare VaultZone.X (StrEnum members are str-compatible).
        if isinstance(seg.value, ast.Name) and seg.value.id == "VaultZone":
            try:
                return VaultZone[seg.attr].value
            except KeyError:
                return None
    return None


def _zone_value_to_zone(zone_value: str) -> VaultZone | None:
    try:
        return VaultZone(zone_value)
    except ValueError:
        return _ZONE_ALIASES.get(zone_value)


def _resolve_leaf_filename(segments: list[ast.expr]) -> str | None:
    """Return the trailing static-string filename of a path chain, or None.

    Walks segments right-to-left and returns the first :class:`ast.Constant`
    string. If the rightmost segment is dynamic (a Name or f-string), the leaf
    is treated as unresolved → conservative violation by the caller.
    """
    if not segments:
        return None
    last = segments[-1]
    if isinstance(last, ast.Constant) and isinstance(last.value, str):
        return last.value
    return None


def _classify(zone: VaultZone | None, leaf: str | None) -> VaultZone | None:
    """Map a (zone, leaf) pair to an ADR-27 action-write category, or None.

    None means the write is not authorized by ADR-27 line 122.
    """
    if zone is None:
        return None
    if zone == VaultZone.DASHBOARDS:
        return VaultZone.DASHBOARDS
    if zone == VaultZone.PROJECTS:
        if leaf is None:
            return None  # dynamic leaf — conservative violation
        return _PROJECTS_LEAF_CATEGORY.get(leaf)
    return None  # SOURCES, KNOWLEDGE, SYSTEM, GUIDES, TEMPLATES, etc.


def _extract_path_arg(call: ast.Call) -> tuple[ast.expr | None, str]:
    """Return ``(path_expression, primitive_label)`` for a mutation Call, or
    ``(None, "")`` if this Call isn't a mutation primitive we track."""
    func = call.func
    if isinstance(func, ast.Attribute):
        if func.attr in _PATH_MUTATOR_METHODS:
            return func.value, f"Path.{func.attr}"
        if (
            isinstance(func.value, ast.Name)
            and func.value.id == "shutil"
            and func.attr in _SHUTIL_DESTINATION
        ):
            idx = _SHUTIL_DESTINATION[func.attr]
            if idx < len(call.args):
                return call.args[idx], f"shutil.{func.attr}"
        if (
            isinstance(func.value, ast.Name)
            and func.value.id == "os"
            and func.attr in _OS_DESTINATION
        ):
            idx = _OS_DESTINATION[func.attr]
            if idx < len(call.args):
                return call.args[idx], f"os.{func.attr}"
    if isinstance(func, ast.Name) and func.id == "open":
        if len(call.args) >= 2:
            mode = call.args[1]
            if (
                isinstance(mode, ast.Constant)
                and isinstance(mode.value, str)
                and mode.value in _OPEN_WRITE_MODES
            ):
                return call.args[0], "open(..., write-mode)"
    return None, ""


def _unwrap_str_call(expr: ast.expr) -> ast.expr:
    """``str(path)`` → unwrap to ``path`` for path-arg analysis."""
    if (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Name)
        and expr.func.id == "str"
        and len(expr.args) == 1
    ):
        return expr.args[0]
    return expr


def _scan_source(source: str, filename: str) -> Iterable[_MutationFinding]:
    """Yield findings for every vault-rooted mutation in ``source``."""
    tree = ast.parse(source, filename=filename)
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        locals_map = _build_locals_map(func)
        for node in ast.walk(func):
            if not isinstance(node, ast.Call):
                continue
            path_expr, primitive = _extract_path_arg(node)
            if path_expr is None:
                continue
            base, segments = _collect_path_segments(
                _unwrap_str_call(path_expr), locals_map
            )
            if not _is_vault_path_base(base):
                continue  # out-of-vault mutation; not in scope
            if not segments:
                yield _MutationFinding(
                    filename, node.lineno, primitive,
                    zone=None, leaf=None, category=None,
                    note="(no segments after vault_path)",
                )
                continue
            zone_value = _resolve_segment_to_zone_value(segments[0])
            zone = _zone_value_to_zone(zone_value) if zone_value else None
            leaf = _resolve_leaf_filename(segments)
            category = _classify(zone, leaf)
            yield _MutationFinding(
                filename, node.lineno, primitive,
                zone=zone, leaf=leaf, category=category,
            )


def _iter_action_sources() -> Iterable[tuple[Path, str]]:
    for path in sorted(ACTIONS_DIR.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        yield path, path.read_text(encoding="utf-8")


def _is_violation(f: _MutationFinding) -> bool:
    return f.category is None or not is_writable_by_actions(f.category)


# --- Self-test fixtures (ADR-27 self-test pattern, lines 62-63) ---

_SELF_TEST_FIXTURE_VIOLATION_SOURCES = """\
from corp.models import VaultZone

def write_to_sources(cfg, project_id):
    notes_dir = cfg.vault_path / VaultZone.SOURCES.value / project_id
    note_path = notes_dir / "evil.md"
    note_path.write_text("frontmatter-less garbage")
"""

_SELF_TEST_FIXTURE_VIOLATION_PROJECTS_UNCLASSIFIED = """\
from corp.models import VaultZone

def write_random_to_projects(cfg, project_id):
    weird = cfg.vault_path / VaultZone.PROJECTS.value / project_id / "weird.md"
    weird.write_text("not metadata, not a brief")
"""

_SELF_TEST_FIXTURE_CLEAN_METADATA = """\
from corp.models import VaultZone

def write_project_info(cfg, project_id):
    info = cfg.vault_path / VaultZone.PROJECTS.value / project_id / "project-info.yaml"
    info.write_text("status: active")
"""


# --- Tests ---


def test_self_test_detects_sources_violation() -> None:
    """The scanner must flag a deliberate ``02_sources/`` write."""
    findings = list(
        _scan_source(_SELF_TEST_FIXTURE_VIOLATION_SOURCES, "<fixture-sources>")
    )
    assert findings, "scanner found no mutations in the SOURCES violation fixture"
    violations = [f for f in findings if _is_violation(f)]
    assert violations, (
        "scanner did not flag the deliberate SOURCES write — the scanner "
        "itself is broken: " + repr(findings)
    )


def test_self_test_detects_unclassified_projects_leaf() -> None:
    """A write to ``projects/{pid}/`` with a non-whitelisted leaf must be flagged."""
    findings = list(
        _scan_source(
            _SELF_TEST_FIXTURE_VIOLATION_PROJECTS_UNCLASSIFIED,
            "<fixture-projects-unclassified>",
        )
    )
    assert findings, "scanner found no mutations in the unclassified-leaf fixture"
    violations = [f for f in findings if _is_violation(f)]
    assert violations, (
        "scanner did not flag an unclassified PROJECTS-zone leaf — the "
        "leaf-filename classification is broken: " + repr(findings)
    )


def test_self_test_passes_clean_metadata_write() -> None:
    """A write to ``projects/{pid}/project-info.yaml`` (METADATA) must pass."""
    findings = list(
        _scan_source(_SELF_TEST_FIXTURE_CLEAN_METADATA, "<fixture-metadata>")
    )
    violations = [f for f in findings if _is_violation(f)]
    assert not violations, (
        "scanner false-positive on a whitelisted METADATA write: " + repr(violations)
    )
    assert any(f.category == VaultZone.METADATA for f in findings), (
        f"scanner did not classify a project-info.yaml write as METADATA: {findings!r}"
    )


def test_actions_modules_target_only_whitelisted_categories() -> None:
    """Every vault-rooted mutation in src/corp/actions/ must classify to a
    whitelisted ADR-27 category (DASHBOARDS, METADATA, BRIEFS)."""
    start = time.monotonic()
    all_findings: list[_MutationFinding] = []
    for path, source in _iter_action_sources():
        all_findings.extend(_scan_source(source, str(path)))
    elapsed = time.monotonic() - start

    violations = [f for f in all_findings if _is_violation(f)]

    assert not violations, (
        "Vault writer invariant violations (ADR-27 Decision 2):\n  "
        + "\n  ".join(repr(v) for v in violations)
    )
    assert elapsed < _PERFORMANCE_BUDGET_SECONDS, (
        f"Scanner exceeded performance budget: {elapsed:.2f}s "
        f"> {_PERFORMANCE_BUDGET_SECONDS}s"
    )


def test_scanner_finds_expected_action_writes() -> None:
    """Sanity: the scanner must find the inventoried writes.

    Guards against the scanner silently scanning zero files or losing its
    classification rules. ADR-27 inventory referenced eight sites; we expect
    to see the seven file-write primitives (one of the eight is a ``mkdir``
    which is not flagged) plus dashboard writes.
    """
    all_findings: list[_MutationFinding] = []
    for path, source in _iter_action_sources():
        all_findings.extend(_scan_source(source, str(path)))
    assert len(all_findings) >= 5, (
        f"Scanner found only {len(all_findings)} vault-rooted mutations; "
        f"expected >= 5. Findings: " + repr(all_findings)
    )
    # The three categories should each be represented at least once.
    categories = {f.category for f in all_findings if f.category}
    assert VaultZone.DASHBOARDS in categories, (
        f"no DASHBOARDS writes found — expected at least analytics/monitoring: "
        f"{all_findings!r}"
    )
    assert VaultZone.METADATA in categories, (
        f"no METADATA writes found — expected project-info.yaml + index.md: "
        f"{all_findings!r}"
    )
    assert VaultZone.BRIEFS in categories, (
        f"no BRIEFS writes found — expected brief.md: {all_findings!r}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
