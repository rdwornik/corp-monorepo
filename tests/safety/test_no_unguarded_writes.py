"""No-unguarded-writes AST scanner (ADR-27 Decision 1 CI enforcement).

Walks the AST of each file in ``ROOTS`` and, for every function containing a
call to a dangerous write/delete primitive, requires that the SAME function
also call :func:`corp.safety.onedrive.guard_path` somewhere in its body, be
decorated ``@onedrive_write_exempt(reason=...)``, or be explicitly
allowlisted -- else it is a violation (Rule 1). A ``guard_path()`` call
found inside a ``try`` block whose matching exception handler neither
re-raises nor unconditionally halts execution (``sys.exit`` / ``exit`` /
``os._exit`` / ``quit``) is also a violation -- the "silent-neutering"
attack vector closed by Rule 2 (ADR-27 line 61). A handler that calls
``sys.exit()`` on guard failure is treated the same as a re-raise: both
guarantee the guarded write below is never reached, which is the actual
safety property Rule 2 protects. Flagging ``sys.exit()`` handlers as
violations would penalize this repo's own established CLI idiom (catch a
domain error, print a clean message, ``sys.exit(1)`` -- see
``corp.project.cli.render``'s pre-existing ``(FileNotFoundError, ValueError)``
handling) without any actual safety benefit.

Scope rationale: ``ROOTS`` covers only ``src/corp/project/cli.py`` -- the D6
surface this batch closes (the ``cpe render --copy-to-vault`` write). Full
repo-wide Decision-1 coverage (auditing every write primitive across all of
``src/corp/`` and running the exemption-decoration sweep needed to make that
green) is ADR-27 PR-3 and is explicitly OUT OF SCOPE for this batch. Widening
``ROOTS`` to the rest of ``src/corp/`` is tracked as follow-up work under
ADR-27's migration plan, not silently expanded here.

Modeled on ``tests/safety/test_vault_writer_invariant.py``: AST walk,
``violations = [...]; assert not violations``, embedded self-test fixtures
(a deliberately-unguarded fixture the scanner MUST flag, a guarded one it
MUST pass -- plus Rule-2- and exemption-specific fixtures), and a
performance-budget test.
"""

from __future__ import annotations

import ast
import time
from pathlib import Path
from typing import Iterable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOTS: list[Path] = [REPO_ROOT / "src" / "corp" / "project" / "cli.py"]

# Path methods that mutate the receiver's file/directory. NOTE: "replace" is
# ambiguous with str.replace (see _is_dangerous_primitive) -- disambiguated
# by argument count, not excluded here.
_PATH_MUTATOR_METHODS: frozenset[str] = frozenset(
    {"write_text", "write_bytes", "replace", "unlink", "rmdir"}
)

_SHUTIL_PRIMITIVES: frozenset[str] = frozenset(
    {"rmtree", "move", "copy", "copy2", "copytree"}
)

_OS_PRIMITIVES: frozenset[str] = frozenset({"remove", "rename", "unlink"})

_OPEN_WRITE_MODES: frozenset[str] = frozenset({"w", "wb", "a", "ab", "x", "xb"})

_GUARD_CALL_NAME = "guard_path"
_EXEMPT_DECORATOR_NAME = "onedrive_write_exempt"

# Exception names whose handler is treated as catching OneDriveSafetyError
# (either directly, or via a broad ancestor/catch-all). Intra-function,
# name-based -- not real type resolution (see ADR-27 acknowledged
# limitations: this is AST enforcement, not a type checker).
_CATCHES_GUARD_ERROR_NAMES: frozenset[str] = frozenset(
    {"OneDriveSafetyError", "RuntimeError", "Exception", "BaseException"}
)

# Calls that unconditionally halt execution -- treated the same as a
# re-raise for Rule 2 (see module docstring).
_UNCONDITIONAL_HALT_CALLS: frozenset[str] = frozenset({"exit", "quit", "_exit"})

# (function name) allowlisted to skip Rule 1 entirely, distinct from the
# @onedrive_write_exempt decorator mechanism. Empty for this batch's scope --
# the mechanism exists per the ADR-27 design ("or an allowlisted helper") but
# nothing in ROOTS currently needs it.
_ALLOWLISTED_FUNCTIONS: frozenset[str] = frozenset()

_PERFORMANCE_BUDGET_SECONDS = 10.0


class _Violation:
    __slots__ = ("file", "lineno", "func", "primitive", "note")

    def __init__(self, file: str, lineno: int, func: str, primitive: str, note: str) -> None:
        self.file = file
        self.lineno = lineno
        self.func = func
        self.primitive = primitive
        self.note = note

    def __repr__(self) -> str:
        return f"{self.file}:{self.lineno} {self.func}() {self.primitive} -- {self.note}"


def _is_dangerous_primitive(call: ast.Call) -> str:
    """Return a label for a dangerous write/delete primitive, or "" if not one.

    ``.replace(...)`` is ambiguous between ``str.replace`` (2-3 args:
    old, new[, count]) and ``Path.replace`` (1 arg: target) -- disambiguated
    by argument count so ``str(x).replace("\\\\", "/")`` (seen at
    project/cli.py's extract command) is not a false positive.
    """
    func = call.func
    if isinstance(func, ast.Attribute):
        if func.attr == "replace":
            if len(call.args) == 1 and not call.keywords:
                return "Path.replace"
            return ""
        if func.attr in _PATH_MUTATOR_METHODS:
            return f"Path.{func.attr}"
        if (
            isinstance(func.value, ast.Name)
            and func.value.id == "shutil"
            and func.attr in _SHUTIL_PRIMITIVES
        ):
            return f"shutil.{func.attr}"
        if (
            isinstance(func.value, ast.Name)
            and func.value.id == "os"
            and func.attr in _OS_PRIMITIVES
        ):
            return f"os.{func.attr}"
    if isinstance(func, ast.Name) and func.id == "open" and len(call.args) >= 2:
        mode = call.args[1]
        if (
            isinstance(mode, ast.Constant)
            and isinstance(mode.value, str)
            and mode.value in _OPEN_WRITE_MODES
        ):
            return "open(..., write-mode)"
    return ""


def _is_guard_call(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Name) and func.id == _GUARD_CALL_NAME:
        return True
    return isinstance(func, ast.Attribute) and func.attr == _GUARD_CALL_NAME


def _decorator_names(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names: set[str] = set()
    for dec in func.decorator_list:
        node = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def _stmt_calls(stmts: Iterable[ast.stmt]) -> Iterable[ast.Call]:
    for stmt in stmts:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call):
                yield node


def _handler_catches_guard_error(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True  # bare `except:` catches everything
    type_nodes = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    for t in type_nodes:
        name = t.attr if isinstance(t, ast.Attribute) else getattr(t, "id", None)
        if name in _CATCHES_GUARD_ERROR_NAMES:
            return True
    return False


def _handler_prevents_continuation(handler: ast.ExceptHandler) -> bool:
    """True if the handler re-raises or unconditionally halts -- i.e. does
    NOT silently swallow the guard failure and fall through to the write."""
    for node in ast.walk(handler):
        if isinstance(node, ast.Raise):
            return True
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and f.attr in _UNCONDITIONAL_HALT_CALLS:
                return True
            if isinstance(f, ast.Name) and f.id in _UNCONDITIONAL_HALT_CALLS:
                return True
    return False


def _find_neutered_guards(func: ast.AST) -> list[tuple[int, str]]:
    """Rule 2: guard_path() inside a try whose matching handler neuters it."""
    findings: list[tuple[int, str]] = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Try):
            continue
        guard_lines = [c.lineno for c in _stmt_calls(node.body) if _is_guard_call(c)]
        if not guard_lines:
            continue
        for handler in node.handlers:
            if _handler_catches_guard_error(handler) and not _handler_prevents_continuation(handler):
                findings.extend(
                    (line, "guard_path() neutered: except handler neither re-raises nor halts")
                    for line in guard_lines
                )
    return findings


def _scan_source(source: str, filename: str) -> list[_Violation]:
    tree = ast.parse(source, filename=filename)
    violations: list[_Violation] = []

    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        primitives = [
            (node.lineno, label)
            for node in ast.walk(func)
            if isinstance(node, ast.Call) and (label := _is_dangerous_primitive(node))
        ]
        if not primitives:
            continue

        if func.name in _ALLOWLISTED_FUNCTIONS:
            continue
        if _EXEMPT_DECORATOR_NAME in _decorator_names(func):
            continue

        has_guard_call = any(
            isinstance(node, ast.Call) and _is_guard_call(node) for node in ast.walk(func)
        )
        if not has_guard_call:
            violations.extend(
                _Violation(
                    filename, lineno, func.name, primitive,
                    "no guard_path() call and no @onedrive_write_exempt in this function",
                )
                for lineno, primitive in primitives
            )
            continue

        violations.extend(
            _Violation(filename, lineno, func.name, "guard_path", note)
            for lineno, note in _find_neutered_guards(func)
        )

    return violations


# --- Self-test fixtures -----------------------------------------------------

_FIXTURE_UNGUARDED = """\
import shutil

def copy_without_guard(src, dst):
    shutil.copy2(src, dst)
"""

_FIXTURE_GUARDED = """\
from corp.safety.onedrive import guard_path

def copy_with_guard(src, dst):
    guard_path(dst, reason="test fixture: guarded")
    shutil.copy2(src, dst)
"""

_FIXTURE_EXEMPT = """\
from corp.safety.onedrive import onedrive_write_exempt

@onedrive_write_exempt(reason="test fixture: exempt")
def copy_exempt(src, dst):
    shutil.copy2(src, dst)
"""

_FIXTURE_NEUTERED = """\
from corp.safety.onedrive import guard_path, OneDriveSafetyError

def copy_neutered(src, dst):
    try:
        guard_path(dst, reason="test fixture: neutered")
    except OneDriveSafetyError:
        pass
    shutil.copy2(src, dst)
"""

_FIXTURE_EXITS_CLEANLY = """\
import sys
from corp.safety.onedrive import guard_path, OneDriveSafetyError

def copy_exits_on_guard_failure(src, dst):
    try:
        guard_path(dst, reason="test fixture: sys.exit is not neutering")
    except OneDriveSafetyError as e:
        print(e)
        sys.exit(1)
    shutil.copy2(src, dst)
"""

_FIXTURE_STR_REPLACE_NOT_FLAGGED = """\
def normalize(path_str):
    # str.replace, NOT Path.replace -- must not be flagged (2 args).
    return path_str.replace("a", "b")
"""


def test_self_test_flags_unguarded_write() -> None:
    violations = _scan_source(_FIXTURE_UNGUARDED, "<fixture-unguarded>")
    assert violations, "scanner did not flag an unguarded dangerous primitive -- scanner is broken"


def test_self_test_passes_guarded_write() -> None:
    violations = _scan_source(_FIXTURE_GUARDED, "<fixture-guarded>")
    assert not violations, f"scanner false-positived on a guarded write: {violations!r}"


def test_self_test_passes_exempt_write() -> None:
    violations = _scan_source(_FIXTURE_EXEMPT, "<fixture-exempt>")
    assert not violations, f"scanner false-positived on an @onedrive_write_exempt write: {violations!r}"


def test_self_test_flags_neutered_guard() -> None:
    violations = _scan_source(_FIXTURE_NEUTERED, "<fixture-neutered>")
    assert violations, "scanner did not flag a silently-neutered guard_path() call (Rule 2)"


def test_self_test_passes_guard_handler_that_exits() -> None:
    """A handler that calls sys.exit() on guard failure is NOT neutering --
    execution never reaches the dangerous primitive below it, the same
    safety property as a re-raise. Mirrors this batch's own cli.py pattern."""
    violations = _scan_source(_FIXTURE_EXITS_CLEANLY, "<fixture-exits-cleanly>")
    assert not violations, f"scanner false-positived on a sys.exit() guard handler: {violations!r}"


def test_self_test_ignores_str_replace() -> None:
    """str.replace (2 args) must not be mistaken for Path.replace (1 arg)."""
    violations = _scan_source(_FIXTURE_STR_REPLACE_NOT_FLAGGED, "<fixture-str-replace>")
    assert not violations, f"scanner false-positived on str.replace: {violations!r}"


def test_no_unguarded_writes_in_scoped_roots() -> None:
    start = time.monotonic()
    all_violations: list[_Violation] = []
    for root in ROOTS:
        source = root.read_text(encoding="utf-8")
        all_violations.extend(_scan_source(source, str(root)))
    elapsed = time.monotonic() - start

    assert not all_violations, (
        "Unguarded OneDrive-unsafe write primitives (ADR-27 Decision 1):\n  "
        + "\n  ".join(repr(v) for v in all_violations)
    )
    assert elapsed < _PERFORMANCE_BUDGET_SECONDS, (
        f"Scanner exceeded performance budget: {elapsed:.2f}s > {_PERFORMANCE_BUDGET_SECONDS}s"
    )


def test_scanner_finds_the_expected_primitive() -> None:
    """Sanity: confirms the scanner actually found project/cli.py's render()
    shutil.copy2 -- guards against the scanner silently scanning zero
    files/functions (a broken scanner that finds nothing would also report
    zero violations)."""
    source = ROOTS[0].read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(ROOTS[0]))
    found = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _is_dangerous_primitive(node) == "shutil.copy2"
    ]
    assert found, "scanner found no shutil.copy2 call in project/cli.py -- expected the copy-to-vault write"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
