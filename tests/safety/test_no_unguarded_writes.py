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


def _iter_own_nodes(func: ast.AST) -> Iterable[ast.AST]:
    """Yield nodes in ``func``'s OWN body, not descending into nested
    function/lambda scopes.

    A ``guard_path`` or a dangerous write inside a nested ``def``/``lambda``
    belongs to that inner scope, not ``func`` — counting it against ``func``
    let "guard in an unrelated nested function" falsely satisfy Rule 1
    (Codex 2026-07-17). Nested functions are still scanned in their own right
    by ``_scan_source``'s top-level ``ast.walk``.
    """
    _SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
    stack: list[ast.AST] = [s for s in getattr(func, "body", []) if not isinstance(s, _SCOPES)]
    while stack:
        node = stack.pop()
        yield node
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _SCOPES):
                continue  # do not descend into a nested scope
            stack.append(child)


def _stmt_terminates(stmt: ast.stmt) -> bool:
    """Whether a single TOP-LEVEL handler statement unconditionally ends the
    flow that would otherwise fall through to the guarded write: a bare
    ``raise``, a ``return``, or a halt call (``sys.exit``/``exit``/``quit``/
    ``os._exit``).

    Only top-level handler statements are inspected — a ``raise``/exit nested
    inside an ``if``/loop is conditional and does NOT guarantee termination,
    so ``if debug: raise`` must not count as unconditional (Codex 2026-07-17).
    """
    if isinstance(stmt, (ast.Raise, ast.Return)):
        return True
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        f = stmt.value.func
        if isinstance(f, ast.Attribute) and f.attr in _UNCONDITIONAL_HALT_CALLS:
            return True
        if isinstance(f, ast.Name) and f.id in _UNCONDITIONAL_HALT_CALLS:
            return True
    return False


def _handler_prevents_continuation(handler: ast.ExceptHandler) -> bool:
    """True iff the handler has a TOP-LEVEL re-raise / return / unconditional
    halt — i.e. no path falls through to the guarded write below the try.

    A conditionally-nested raise/exit (``if x: raise``) does not count: the
    handler can still swallow the error and fall through (Codex 2026-07-17)."""
    return any(_stmt_terminates(s) for s in handler.body)


def _find_neutered_guards(func: ast.AST) -> list[tuple[int, str]]:
    """Rule 2: guard_path() inside a try whose matching handler neuters it."""
    findings: list[tuple[int, str]] = []
    for node in _iter_own_nodes(func):
        if not isinstance(node, ast.Try):
            continue
        guard_lines = [c.lineno for c in _stmt_calls(node.body) if _is_guard_call(c)]
        if not guard_lines:
            continue
        for handler in node.handlers:
            if _handler_catches_guard_error(handler) and not _handler_prevents_continuation(handler):
                findings.extend(
                    (line, "guard_path() neutered: except handler neither re-raises nor "
                           "halts on every path")
                    for line in guard_lines
                )
    return findings


def _scan_source(source: str, filename: str) -> list[_Violation]:
    tree = ast.parse(source, filename=filename)
    violations: list[_Violation] = []

    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        own_nodes = list(_iter_own_nodes(func))

        primitives = [
            (node.lineno, label)
            for node in own_nodes
            if isinstance(node, ast.Call) and (label := _is_dangerous_primitive(node))
        ]
        if not primitives:
            continue

        if func.name in _ALLOWLISTED_FUNCTIONS:
            continue
        if _EXEMPT_DECORATOR_NAME in _decorator_names(func):
            continue

        guard_linenos = sorted(
            node.lineno
            for node in own_nodes
            if isinstance(node, ast.Call) and _is_guard_call(node)
        )

        # Rule 1 (dominance): each dangerous primitive must be preceded, in
        # this function's OWN body, by a guard_path() call. A guard AFTER the
        # write, or one inside a nested function, does not protect it (Codex
        # 2026-07-17). Lexical precedence is the sound-for-the-named-cases
        # heuristic; full every-path CFG dominance (a guard only in one branch
        # of an if) remains an acknowledged ADR-27 limitation deferred to Codex
        # review ("Conditional guard execution").
        for lineno, primitive in primitives:
            if not any(g < lineno for g in guard_linenos):
                violations.append(
                    _Violation(
                        filename, lineno, func.name, primitive,
                        "no guard_path() precedes this write in the same function "
                        "(and no @onedrive_write_exempt)",
                    )
                )

        # Rule 2 (silent neutering): a preceding guard is only real if its
        # try/except does not swallow OneDriveSafetyError and fall through.
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

# Rule 1 dominance: a guard AFTER the write does not protect it.
_FIXTURE_GUARD_AFTER_WRITE = """\
from corp.safety.onedrive import guard_path

def copy_then_guard(src, dst):
    shutil.copy2(src, dst)
    guard_path(dst, reason="too late -- write already happened")
"""

# Rule 1 own-scope: a guard inside a nested function does not protect the
# outer write.
_FIXTURE_GUARD_IN_NESTED_FUNC = """\
from corp.safety.onedrive import guard_path

def outer(src, dst):
    def _unrelated():
        guard_path(dst, reason="wrong scope")
    shutil.copy2(src, dst)
"""

# Rule 2: a conditionally-nested re-raise does not guarantee termination.
_FIXTURE_CONDITIONAL_RERAISE = """\
from corp.safety.onedrive import guard_path, OneDriveSafetyError

def copy_conditional_reraise(src, dst, debug):
    try:
        guard_path(dst, reason="handler only re-raises when debug")
    except OneDriveSafetyError:
        if debug:
            raise
    shutil.copy2(src, dst)
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


def test_self_test_flags_guard_after_write() -> None:
    """Rule 1 dominance: a guard_path() AFTER the write must not satisfy the
    scanner (Codex 2026-07-17)."""
    violations = _scan_source(_FIXTURE_GUARD_AFTER_WRITE, "<fixture-guard-after-write>")
    assert violations, "scanner accepted a guard placed AFTER the write -- dominance is broken"


def test_self_test_flags_guard_in_nested_func() -> None:
    """Rule 1 own-scope: a guard_path() inside a nested function must not
    satisfy the outer function's write (Codex 2026-07-17)."""
    violations = _scan_source(_FIXTURE_GUARD_IN_NESTED_FUNC, "<fixture-guard-nested>")
    assert violations, "scanner accepted a guard in an unrelated nested function"


def test_self_test_flags_conditional_reraise_handler() -> None:
    """Rule 2: a handler that only re-raises inside `if debug:` can still fall
    through to the write and must be flagged (Codex 2026-07-17)."""
    violations = _scan_source(_FIXTURE_CONDITIONAL_RERAISE, "<fixture-conditional-reraise>")
    assert violations, "scanner accepted a conditionally-nested re-raise as unconditional"


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
