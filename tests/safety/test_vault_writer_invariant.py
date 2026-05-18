"""Vault single-writer invariant (ADR-27 Decision 2).

Walks every module under ``src/corp/actions/`` and, for each file-mutation
primitive whose target path is rooted at ``<something>.vault_path``, resolves
the first path segment to a :class:`~corp.models.VaultZone` and asserts the
zone is whitelisted by :func:`corp.vault_io.is_writable_by_actions`.

Writes to non-whitelisted zones (notably ``SOURCES`` / ``02_sources/``) must
route through :func:`corp.vault_io.write_note`.

Self-test: an embedded fixture string contains a deliberate ``02_sources/``
violation; if the scanner does not flag it, this test itself fails.
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

# shutil functions: (name, index of destination path arg).
_SHUTIL_DESTINATION: dict[str, int] = {
    "copy": 1,
    "copy2": 1,
    "copytree": 1,
    "move": 1,
    "rmtree": 0,
}

# os functions: (name, index of mutating path arg).
_OS_DESTINATION: dict[str, int] = {
    "remove": 0,
    "unlink": 0,
    "rename": 1,
}

# Open modes that mutate the file.
_OPEN_WRITE_MODES: frozenset[str] = frozenset({"w", "wb", "a", "ab", "x", "xb"})

# Aliases for known string literals that don't match a VaultZone value exactly.
# This codifies the documented drift in analytics_actions.py:99 (uses
# "00_dashboards" instead of VaultZone.DASHBOARDS = "dashboards"). The drift
# itself is tracked separately; the scanner must still pass against current
# main. See ADR-27 PR-4 JOURNAL entry, "Next:".
_ZONE_ALIASES: dict[str, VaultZone] = {
    "00_dashboards": VaultZone.DASHBOARDS,
}

# Performance budget for the full scan.
_PERFORMANCE_BUDGET_SECONDS = 5.0


class _MutationFinding:
    __slots__ = ("file", "lineno", "primitive", "zone_value", "zone", "note")

    def __init__(
        self,
        file: str,
        lineno: int,
        primitive: str,
        zone_value: str | None,
        zone: VaultZone | None,
        note: str = "",
    ) -> None:
        self.file = file
        self.lineno = lineno
        self.primitive = primitive
        self.zone_value = zone_value
        self.zone = zone
        self.note = note

    def __repr__(self) -> str:
        return (
            f"{self.file}:{self.lineno} {self.primitive} → "
            f"zone={self.zone.name if self.zone else self.zone_value!r}"
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

    Resolves intermediate local variable references. Returns the leftmost
    non-resolvable expression as ``base_expr`` and the right-hand operands of
    every ``/`` in left-to-right order. ``segments`` is empty if ``expr`` is
    not a path-join chain (or once base is reached).
    """
    if depth > 50:
        return expr, []
    # Resolve Name through locals_map (with cycle guard via depth).
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


def _extract_path_arg(call: ast.Call) -> tuple[ast.expr | None, str]:
    """Return ``(path_expression, primitive_label)`` for a mutation Call, or
    ``(None, "")`` if this Call isn't a mutation we care about."""
    func = call.func
    # Method calls on a receiver: receiver.METHOD(...)
    if isinstance(func, ast.Attribute):
        if func.attr in _PATH_MUTATOR_METHODS:
            return func.value, f"Path.{func.attr}"
        # shutil.X(...)
        if (
            isinstance(func.value, ast.Name)
            and func.value.id == "shutil"
            and func.attr in _SHUTIL_DESTINATION
        ):
            idx = _SHUTIL_DESTINATION[func.attr]
            if idx < len(call.args):
                return call.args[idx], f"shutil.{func.attr}"
        # os.X(...)
        if (
            isinstance(func.value, ast.Name)
            and func.value.id == "os"
            and func.attr in _OS_DESTINATION
        ):
            idx = _OS_DESTINATION[func.attr]
            if idx < len(call.args):
                return call.args[idx], f"os.{func.attr}"
    # Bare open(path, "w") — only flag with literal write mode.
    if isinstance(func, ast.Name) and func.id == "open":
        if len(call.args) >= 2:
            mode = call.args[1]
            if (
                isinstance(mode, ast.Constant)
                and isinstance(mode.value, str)
                and any(ch in _OPEN_WRITE_MODES for ch in (mode.value,))
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
                    filename, node.lineno, primitive, None, None,
                    note="(no segments after vault_path)",
                )
                continue
            zone_value = _resolve_segment_to_zone_value(segments[0])
            zone = _zone_value_to_zone(zone_value) if zone_value else None
            yield _MutationFinding(
                filename, node.lineno, primitive, zone_value, zone
            )


def _iter_action_sources() -> Iterable[tuple[Path, str]]:
    for path in sorted(ACTIONS_DIR.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        yield path, path.read_text(encoding="utf-8")


# --- Self-test fixture (ADR-27 lines 62–63 pattern) ---

_SELF_TEST_FIXTURE_VIOLATION = """\
from corp.models import VaultZone

def write_to_sources(cfg, project_id):
    notes_dir = cfg.vault_path / VaultZone.SOURCES.value / project_id
    note_path = notes_dir / "evil.md"
    note_path.write_text("frontmatter-less garbage")
"""

_SELF_TEST_FIXTURE_CLEAN = """\
from corp.models import VaultZone

def write_to_projects(cfg, project_id):
    info = cfg.vault_path / VaultZone.PROJECTS.value / project_id / "info.yaml"
    info.write_text("ok: true")
"""


# --- Tests ---


def test_self_test_fixture_detects_violation() -> None:
    """The scanner must flag a deliberate 02_sources/ write in fixture code.

    If this fails, the scanner is silently broken and the production scan
    cannot be trusted (ADR-27 self-test requirement).
    """
    findings = list(
        _scan_source(_SELF_TEST_FIXTURE_VIOLATION, "<fixture-violation>")
    )
    assert findings, "scanner failed to find ANY mutation in the violation fixture"
    violations = [
        f for f in findings if f.zone is None or not is_writable_by_actions(f.zone)
    ]
    assert violations, (
        "scanner did not flag the deliberate SOURCES write in the self-test "
        "fixture — the scanner itself is broken: " + repr(findings)
    )


def test_self_test_fixture_passes_clean_write() -> None:
    """The clean fixture (PROJECTS write) must not be flagged."""
    findings = list(_scan_source(_SELF_TEST_FIXTURE_CLEAN, "<fixture-clean>"))
    violations = [
        f for f in findings if f.zone is None or not is_writable_by_actions(f.zone)
    ]
    assert not violations, (
        "scanner false-positive on a whitelisted (PROJECTS) write: "
        + repr(violations)
    )


def test_actions_modules_target_only_whitelisted_zones() -> None:
    """Every vault-rooted mutation in src/corp/actions/ must target a
    whitelisted zone (ADR-27 Decision 2)."""
    start = time.monotonic()
    all_findings: list[_MutationFinding] = []
    for path, source in _iter_action_sources():
        all_findings.extend(_scan_source(source, str(path)))
    elapsed = time.monotonic() - start

    violations = [
        f for f in all_findings if f.zone is None or not is_writable_by_actions(f.zone)
    ]

    assert not violations, (
        "Vault writer invariant violations (ADR-27 Decision 2):\n  "
        + "\n  ".join(repr(v) for v in violations)
    )
    assert elapsed < _PERFORMANCE_BUDGET_SECONDS, (
        f"Scanner exceeded performance budget: {elapsed:.2f}s "
        f"> {_PERFORMANCE_BUDGET_SECONDS}s"
    )


def test_scanner_finds_expected_action_writes() -> None:
    """Sanity: the scanner must find at least one vault write in actions/.

    Guards against the scanner silently scanning zero files (e.g. wrong path,
    misnamed __init__.py exclusion).
    """
    all_findings: list[_MutationFinding] = []
    for path, source in _iter_action_sources():
        all_findings.extend(_scan_source(source, str(path)))
    assert len(all_findings) >= 5, (
        f"Scanner found only {len(all_findings)} vault-rooted mutations in "
        f"src/corp/actions/; expected >= 5 per ADR-27 inventory. Findings: "
        + repr(all_findings)
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
