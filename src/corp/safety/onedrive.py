"""Centralized OneDrive safety guards (ADR-27 Decision 1).

Foundation-layer module (Tach) — no ``corp.*`` imports of its own, importable
from every other layer. Single source of truth for the resolve-then-substring
"OneDrive - Blue Yonder" exclusion check that was previously duplicated at
four call sites (``cleanup/disk.py``, ``cleanup/executor.py``,
``actions/_helpers.py``, ``project/renderer.py``) after hotfix
``onedrive-safety-p1`` (merged 2026-04-21). See INCIDENT 2026-03-14 for the
class of bug these guards prevent, and
``docs/decisions/ADR-27-safety-invariants.md`` (Decision 1) for the design
rationale and the AST-scanner enforcement in
``tests/safety/test_no_unguarded_writes.py``.

Public API:
  * ``OneDriveSafetyError`` — raised when a path is refused as synced-tree.
  * ``PathTraversalError`` — raised when a path escapes its expected root.
  * ``is_onedrive_path(path)`` — predicate form (never raises).
  * ``guard_path(path, *, reason=...)`` — the primary guard; raises.
  * ``guard_within_root(path, root, *, reason=...)`` — pure containment check.
  * ``onedrive_write_exempt(reason=...)`` — no-op tag decorator consumed only
    by the AST scanner.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeVar

# The canonical exclusion-zone substring. Same literal every guard site used
# independently before centralization.
_ONEDRIVE_BLOCKED = "OneDrive - Blue Yonder"

_F = TypeVar("_F", bound=Callable[..., object])


class OneDriveSafetyError(RuntimeError):
    """A write/delete was refused because it targeted a OneDrive-synced path.

    OneDrive - Blue Yonder paths are treated as read-only by design: any
    mutation there risks corrupting synced SharePoint copies and cannot be
    undone locally. Callers must stage files outside OneDrive before writing.
    """


class PathTraversalError(RuntimeError):
    """A path resolved outside its expected root directory.

    Raised when an untrusted or user-supplied path (a ``moves.yaml`` entry, a
    CLI ``--copy-to-vault`` destination, etc.) escapes the root it is
    expected to stay within, after resolution.
    """


def _resolve_candidates(path: str | Path) -> list[str]:
    """Return ``[original_str, resolved_str]``, resolving fail-closed.

    Propagates whatever ``OSError``/``RuntimeError`` ``Path.resolve`` raises
    so callers can translate an unresolvable path into their own fail-closed
    behavior.
    """
    return [str(path), str(Path(path).resolve(strict=False))]


def _matches_zone(candidates: list[str], *, strict: bool) -> bool:
    """Whether any candidate string names the synced-tree exclusion zone.

    ``strict=True`` (default) matches ONLY the canonical corporate zone
    ``"OneDrive - Blue Yonder"`` — the policy-defined exclusion zone every
    other guard site uses (``core-invariants.md``, the ``block-onedrive``
    hook, ADR-27). ``strict=False`` ADDITIONALLY matches a case-insensitive
    ``"onedrive"`` substring, preserving the broader net that
    ``project/renderer.py`` applied before centralization (any personal
    ``~/OneDrive`` too), so unifying the renderer onto this module does not
    narrow its protection (Codex review 2026-07-17).
    """
    if any(_ONEDRIVE_BLOCKED in c for c in candidates):
        return True
    if not strict:
        return any("onedrive" in c.lower() for c in candidates)
    return False


def is_onedrive_path(path: str | Path, *, strict: bool = True) -> bool:
    """Return True if ``path`` names or resolves into the OneDrive exclusion zone.

    Checks the original string form and the ``.resolve(strict=False)`` form
    so a Windows junction, symlink, or alias whose text omits the zone but
    whose resolved target lands inside it cannot bypass the check. Fails
    closed: if resolution itself raises ``OSError``/``RuntimeError``, the
    path is treated as unverifiable and therefore unsafe (returns True).

    ``strict`` (see :func:`_matches_zone`): ``True`` matches only the
    canonical ``"OneDrive - Blue Yonder"`` zone; ``False`` also matches any
    case-insensitive ``"onedrive"`` path (the renderer's pre-centralization
    breadth).
    """
    try:
        candidates = _resolve_candidates(path)
    except (OSError, RuntimeError):
        return True
    return _matches_zone(candidates, strict=strict)


def guard_path(path: str | Path, *, reason: str, strict: bool = True) -> None:
    """Refuse any write/delete that lands inside a synced tree.

    Checks both the original string form and the resolved form so a Windows
    junction, symlink, or configured alias cannot bypass the substring check
    (Codex review H-C1/H-C2, 2026-04-21). Fails closed if ``Path.resolve``
    itself raises — an unresolvable path is treated as unverifiable, so
    refused.

    Args:
        path: The path to check.
        reason: Short description of the operation being guarded, included
            in the raised error for auditability.
        strict: ``True`` (default) refuses only the canonical
            ``"OneDrive - Blue Yonder"`` zone; ``False`` also refuses any
            case-insensitive ``"onedrive"`` path (used by
            ``project/renderer.py`` to preserve its pre-centralization
            breadth — see :func:`_matches_zone`).

    Raises:
        OneDriveSafetyError: If ``path`` is (or resolves to) a synced-tree
            path, or if it cannot be resolved at all.
    """
    original = str(path)
    try:
        candidates = _resolve_candidates(path)
    except (OSError, RuntimeError) as exc:
        raise OneDriveSafetyError(
            f"BLOCKED: cannot resolve {original!r} to verify synced-tree "
            f"safety ({reason}): {exc}"
        ) from exc

    if _matches_zone(candidates, strict=strict):
        raise OneDriveSafetyError(
            f"BLOCKED: refusing to mutate synced path {path} "
            f"(resolved candidates: {candidates}); reason: {reason}. "
            "See INCIDENT 2026-03-14 (ADR-27 centralization)."
        )


def guard_within_root(path: str | Path, root: str | Path, *, reason: str) -> None:
    """Raise if ``path`` resolves outside ``root``.

    Pure containment helper — no config import, no OneDrive check. Resolves
    both ``path`` and ``root`` with ``.resolve(strict=False)`` and fails
    closed (raises) if either resolution itself raises.

    Args:
        path: The path that must land inside ``root``.
        root: The expected containing root.
        reason: Short description of the containment requirement, included
            in the raised error for auditability.

    Raises:
        PathTraversalError: If ``path`` escapes ``root``, or either path
            cannot be resolved.
    """
    try:
        resolved_path = Path(path).resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise PathTraversalError(
            f"cannot resolve {str(path)!r} to verify containment ({reason}): {exc}"
        ) from exc
    try:
        resolved_root = Path(root).resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise PathTraversalError(
            f"cannot resolve root {str(root)!r} to verify containment ({reason}): {exc}"
        ) from exc

    if not resolved_path.is_relative_to(resolved_root):
        raise PathTraversalError(
            f"path escapes expected root ({reason}): "
            f"{path} -> {resolved_path} (root={resolved_root})"
        )


def onedrive_write_exempt(*, reason: str) -> Callable[[_F], _F]:
    """No-op tag decorator consumed only by the AST scanner.

    Marks a function as deliberately exempt from the "must call guard_path"
    scanner rule (``tests/safety/test_no_unguarded_writes.py``), making
    exemptions grep-able and code-reviewable. Does not alter runtime
    behavior — the decorated function is returned unchanged.

    Args:
        reason: Required — why this function is exempt. Stored on the
            function as ``_onedrive_write_exempt_reason`` for introspection.
    """

    def decorator(func: _F) -> _F:
        func._onedrive_write_exempt_reason = reason  # type: ignore[attr-defined]
        return func

    return decorator
