"""Read-only invariant for the current-state audit tool (single-write-sink proof).

Statically proves that ``scripts/current_state_audit.py`` and
``scripts/_audit_core.py`` contain **no** filesystem-mutation primitive and **no**
shell-out — except the one whitelisted write sink ``_audit_core.write_inventory``
(``Path.write_text``). A shell-out (``subprocess`` / ``os.system`` / ``os.popen``
/ ``os.exec*`` / ``os.spawn*``) would otherwise bypass the Python-primitive check
and leave a hole in the proof, so it is in the denylist too.

Modeled on ``tests/safety/test_vault_writer_invariant.py``: AST walk, classify,
``violations = [...]; assert not violations``, plus embedded self-test fixtures
(synthetic mutations incl. ``mkdir`` and ``subprocess.run`` must be flagged; safe
calls — ``str.replace``, ``open(..., "rb")``, ``os.scandir`` — must not be) and a
performance budget.
"""

from __future__ import annotations

import ast
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_FILES = [
    REPO_ROOT / "scripts" / "current_state_audit.py",
    REPO_ROOT / "scripts" / "_audit_core.py",
]

# The single permitted mutation: (file basename, enclosing function, primitive).
_WHITELIST: frozenset[tuple[str, str, str]] = frozenset(
    {("_audit_core.py", "write_inventory", ".write_text")}
)

# Unambiguous file/dir-mutating Path/file methods (names not shared with str).
_PATH_MUTATORS: frozenset[str] = frozenset(
    {
        "write_text",
        "write_bytes",
        "unlink",
        "rmdir",
        "mkdir",
        "makedirs",
        "touch",
        "symlink_to",
        "hardlink_to",
        "chmod",
        "lchmod",
        "mknod",
    }
)
_SHUTIL_MUTATORS: frozenset[str] = frozenset(
    {
        "copy",
        "copy2",
        "copyfile",
        "copyfileobj",
        "copytree",
        "move",
        "rmtree",
        "copymode",
        "copystat",
        "chown",
    }
)
_OS_MUTATORS: frozenset[str] = frozenset(
    {
        "remove",
        "unlink",
        "rename",
        "renames",
        "replace",
        "mkdir",
        "makedirs",
        "rmdir",
        "removedirs",
        "symlink",
        "link",
        "truncate",
        "ftruncate",
        "mknod",
        "mkfifo",
        "chmod",
        "lchmod",
        "chown",
        "lchown",
        "fchown",
        "utime",
        "write",
        "writev",
        "open",
        "sendfile",
    }
)
_OS_SHELL: frozenset[str] = frozenset({"system", "popen"})
_SUBPROCESS_FUNCS: frozenset[str] = frozenset(
    {
        "run",
        "call",
        "check_call",
        "check_output",
        "Popen",
        "getoutput",
        "getstatusoutput",
    }
)
_WRITE_MODE_CHARS = ("w", "a", "x", "+")
_PERFORMANCE_BUDGET_SECONDS = 5.0


class _Finding:
    __slots__ = ("file", "func", "primitive", "lineno")

    def __init__(self, file: str, func: str | None, primitive: str, lineno: int):
        self.file = file
        self.func = func
        self.primitive = primitive
        self.lineno = lineno

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.file, self.func or "<module>", self.primitive)

    def __repr__(self) -> str:
        return f"{self.file}:{self.lineno} {self.func or '<module>'}() -> {self.primitive}"


def _str_const(node: ast.expr | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _open_mode(call: ast.Call, mode_index: int) -> str | None:
    if len(call.args) > mode_index:
        literal = _str_const(call.args[mode_index])
        if literal is not None:
            return literal
    for kw in call.keywords:
        if kw.arg == "mode":
            return _str_const(kw.value)
    return None


def _is_write_mode(mode: str) -> bool:
    return any(ch in mode for ch in _WRITE_MODE_CHARS)


def _primitive(call: ast.Call) -> str | None:
    """Return a mutation/shell-out label for ``call``, or None if it's read-only."""
    func = call.func
    if isinstance(func, ast.Attribute):
        attr = func.attr
        recv = func.value
        if isinstance(recv, ast.Name):
            rid = recv.id
            if rid == "subprocess" and attr in _SUBPROCESS_FUNCS:
                return f"subprocess.{attr}"
            if rid == "os":
                if attr in _OS_SHELL:
                    return f"os.{attr}"
                if attr.startswith("exec") or attr.startswith("spawn") or attr.startswith(
                    "posix_spawn"
                ):
                    return f"os.{attr}"
                if attr in _OS_MUTATORS:
                    return f"os.{attr}"
            if rid == "shutil" and attr in _SHUTIL_MUTATORS:
                return f"shutil.{attr}"
        if attr in _PATH_MUTATORS:
            return f".{attr}"
        # Path.replace(target) is 1-arg; str.replace(old, new) is >=2-arg (safe).
        if attr == "replace" and len(call.args) == 1 and not call.keywords:
            return ".replace(path)"
        if attr == "rename" and len(call.args) <= 1:
            return ".rename"
        if attr == "open":
            mode = _open_mode(call, 0)
            if mode and _is_write_mode(mode):
                return ".open(write)"
    elif isinstance(func, ast.Name) and func.id == "open":
        mode = _open_mode(call, 1)
        if mode and _is_write_mode(mode):
            return "open(write)"
    return None


def _calls_with_func(tree: ast.AST) -> list[tuple[ast.Call, str | None]]:
    out: list[tuple[ast.Call, str | None]] = []

    def visit(node: ast.AST, func_name: str | None) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit(child, child.name)
            else:
                if isinstance(child, ast.Call):
                    out.append((child, func_name))
                visit(child, func_name)

    visit(tree, None)
    return out


def _scan_findings(source: str, filename: str) -> list[_Finding]:
    tree = ast.parse(source, filename=filename)
    findings: list[_Finding] = []
    for call, func_name in _calls_with_func(tree):
        primitive = _primitive(call)
        if primitive is not None:
            findings.append(_Finding(filename, func_name, primitive, call.lineno))
    return findings


# --------------------------- self-test fixtures --------------------------- #

_FIXTURE_VIOLATIONS = '''
import os
import shutil
import subprocess
from pathlib import Path

def danger(p):
    Path(p).write_text("x")
    Path(p).write_bytes(b"x")
    Path(p).unlink()
    Path(p).mkdir()
    Path(p).replace(p)
    shutil.rmtree(p)
    os.remove(p)
    os.rename(p, p)
    os.system("echo hi")
    os.popen("echo hi")
    subprocess.run(["echo", "hi"])
    with open(p, "w") as f:
        f.write("x")
'''

_FIXTURE_CLEAN = '''
import json
import os
from pathlib import Path

def write_inventory(inv, out, ledger):
    resolved = out.resolve(strict=False)
    norm = str(resolved).replace("\\\\", "/")
    with os.scandir(".") as it:
        for entry in it:
            entry.stat(follow_symlinks=False)
    with open(resolved, "rb") as fh:
        fh.read()
    resolved.write_text(json.dumps({"p": norm}), encoding="utf-8")

def other(p):
    return str(p).replace("\\\\", "/")
'''


# ------------------------------- tests ------------------------------------ #


def test_self_test_flags_mutations_and_shell_outs() -> None:
    findings = _scan_findings(_FIXTURE_VIOLATIONS, "<violations>")
    prims = {f.primitive for f in findings}
    expected = {
        ".write_text",
        ".write_bytes",
        ".unlink",
        ".mkdir",
        ".replace(path)",
        "shutil.rmtree",
        "os.remove",
        "os.rename",
        "os.system",
        "os.popen",
        "subprocess.run",
        "open(write)",
    }
    missing = expected - prims
    assert not missing, f"scanner failed to flag: {missing} (got {prims})"


def test_self_test_ignores_safe_calls() -> None:
    """str.replace (2-arg), open(..., 'rb'), os.scandir, .stat must NOT be flagged."""
    findings = _scan_findings(_FIXTURE_CLEAN, "<clean>")
    prims = [f.primitive for f in findings]
    assert prims == [".write_text"], (
        f"scanner false-positived on safe calls; flagged: {prims}"
    )


def test_audit_tool_is_read_only() -> None:
    """The real tool files contain only the single whitelisted write sink."""
    start = time.monotonic()
    all_findings: list[_Finding] = []
    for path in TOOL_FILES:
        assert path.exists(), f"audit tool file missing: {path}"
        all_findings.extend(
            _scan_findings(path.read_text(encoding="utf-8"), path.name)
        )
    elapsed = time.monotonic() - start

    violations = [f for f in all_findings if f.key not in _WHITELIST]
    assert not violations, (
        "Read-only invariant violations in the audit tool:\n  "
        + "\n  ".join(repr(v) for v in violations)
    )
    # Sanity: the whitelisted write sink must actually be present (guards against
    # a silently-broken scanner that finds nothing).
    assert any(f.key in _WHITELIST for f in all_findings), (
        "scanner found no write sink — it is silently broken: "
        + repr(all_findings)
    )
    assert elapsed < _PERFORMANCE_BUDGET_SECONDS, (
        f"scanner exceeded budget: {elapsed:.2f}s > {_PERFORMANCE_BUDGET_SECONDS}s"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
