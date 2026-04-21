"""Execute approved moves from moves.yaml.

Only acts on entries with approved: true. Skips everything else.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

import yaml

from corp.cleanup.errors import OneDriveSafetyError, PathTraversalError

log = logging.getLogger(__name__)

_ONEDRIVE_BLOCKED = "OneDrive - Blue Yonder"


def _guard_onedrive(path: Path) -> None:
    """Raise if path is under a synced tree — hard safety guard.

    Checks both the original and resolved string forms so a Windows
    junction or symlink cannot bypass the substring check (Codex review
    follow-up, 2026-04-21). Fails closed if ``Path.resolve`` itself raises.

    Mirrors the sibling guards in ``cleanup/disk`` and
    ``actions/_helpers`` pending ADR-27 centralization.
    """
    original = str(path)
    candidates = [original]
    try:
        candidates.append(str(Path(path).resolve(strict=False)))
    except (OSError, RuntimeError) as exc:
        raise OneDriveSafetyError(
            f"BLOCKED: cannot resolve {original!r} to verify synced-tree "
            f"safety: {exc}"
        ) from exc

    if any(_ONEDRIVE_BLOCKED in c for c in candidates):
        raise OneDriveSafetyError(
            f"BLOCKED: Cannot modify synced path: {path} "
            f"(resolved candidates: {candidates}). "
            "Synced paths are read-only. See gotchas for details."
        )


def _is_absolute_like(s: str) -> bool:
    """True for anything that looks absolute on POSIX or Windows.

    Catches ``/foo``, ``C:\\foo``, ``C:/foo``, and UNC ``\\\\host\\share``.
    ``Path.is_absolute()`` alone is platform-dependent; we need both views.
    """
    if not s:
        return False
    if PurePosixPath(s).is_absolute():
        return True
    try:
        return PureWindowsPath(s).is_absolute()
    except ValueError:
        return False


def _has_parent_traversal(s: str) -> bool:
    """True if any path segment (split on / or \\) is ``..``."""
    if not s:
        return False
    normalized = s.replace("\\", "/")
    return any(seg == ".." for seg in normalized.split("/"))


@dataclass
class MoveEntry:
    """Schema for a single entry in moves.yaml.

    Validates at load time: no absolute paths, no parent-traversal
    segments, required fields present. The runtime guard in
    :func:`execute_moves` is a second layer in case callers construct
    entries programmatically.
    """

    source: str
    action: str
    destination: str
    proposed_name: str
    approved: bool | None = None
    reason: str = ""
    confidence: float = 0.0

    def __post_init__(self) -> None:
        # source is always required when approved=True; validate it unconditionally
        # so schema tests catch bad YAML before the approval check filters it out.
        if not isinstance(self.source, str) or not self.source:
            raise ValueError("moves.yaml entry: source is required and must be a string")
        if _is_absolute_like(self.source):
            raise ValueError(
                f"moves.yaml entry: source is absolute (must be relative to mywork_root): "
                f"{self.source!r}"
            )
        if _has_parent_traversal(self.source):
            raise ValueError(
                f"moves.yaml entry: source contains parent traversal (..): {self.source!r}"
            )

        # destination and proposed_name may be empty for action=keep.
        for field_name, value in (
            ("destination", self.destination),
            ("proposed_name", self.proposed_name),
        ):
            if not value:
                continue
            if _is_absolute_like(value):
                raise ValueError(
                    f"moves.yaml entry: {field_name} is absolute: {value!r}"
                )
            if _has_parent_traversal(value):
                raise ValueError(
                    f"moves.yaml entry: {field_name} contains parent traversal (..): {value!r}"
                )

    @classmethod
    def from_dict(cls, entry: dict) -> MoveEntry:
        """Build a MoveEntry from a raw dict (e.g. yaml.safe_load output)."""
        return cls(
            source=entry.get("source", ""),
            action=entry.get("action", "keep"),
            destination=entry.get("destination", ""),
            proposed_name=entry.get("proposed_name", ""),
            approved=entry.get("approved"),
            reason=entry.get("reason", ""),
            confidence=float(entry.get("confidence", 0.0) or 0.0),
        )


def _assert_within_root(path: Path, root: Path, field: str) -> None:
    """Fail closed if ``path`` resolves outside ``root``.

    Second-layer runtime guard: the schema should have caught any ``..``
    or absolute path, but this catches symlink / junction escapes and any
    programmatic construction that bypassed the schema.
    """
    try:
        resolved = path.resolve(strict=False)
    except OSError as exc:
        raise PathTraversalError(
            f"moves.yaml {field} could not be resolved: {path}: {exc}"
        ) from exc
    root_resolved = root.resolve(strict=False)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise PathTraversalError(
            f"moves.yaml {field} escapes mywork_root: "
            f"{path} -> {resolved} (root={root_resolved})"
        ) from exc


@dataclass
class ExecutionResult:
    """Summary of move execution."""

    moved: int = 0
    deleted: int = 0
    skipped: int = 0
    failed: int = 0


def execute_moves(
    moves_path: Path,
    mywork_root: Path,
    dry_run: bool = False,
) -> ExecutionResult:
    """Execute approved moves from moves.yaml.

    Only executes entries where approved is explicitly true.
    Skips approved: false, approved: null, or missing approved field.
    """
    mywork_root = mywork_root.resolve()

    with open(moves_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    raw_entries = data.get("moves", [])
    # Load-time schema: rejects ``..``, absolute paths, empty source.
    # Validates every entry (even approved=false) so operators catch bad YAML
    # before selectively approving lines.
    entries = [MoveEntry.from_dict(e) for e in raw_entries]
    result = ExecutionResult()

    for entry in entries:
        if entry.approved is not True:
            result.skipped += 1
            continue

        source_rel = entry.source
        action = entry.action
        dest_folder = entry.destination
        proposed_name = entry.proposed_name

        source = mywork_root / source_rel.replace("/", "\\")
        # Runtime guard: belt-and-suspenders against symlink/junction escapes.
        _assert_within_root(source, mywork_root, field="source")

        if not source.exists():
            log.warning("Source not found, skipping: %s", source_rel)
            result.failed += 1
            continue

        _guard_onedrive(source)

        if action == "delete":
            if dry_run:
                log.info("[DRY RUN] Would delete: %s", source_rel)
            else:
                source.unlink()
                log.info("Deleted: %s", source_rel)
            result.deleted += 1

        elif action == "move":
            dest_dir = mywork_root / dest_folder.replace("/", "\\")
            dest_file = dest_dir / (proposed_name or source.name)
            _assert_within_root(dest_dir, mywork_root, field="destination")
            _assert_within_root(dest_file, mywork_root, field="destination")

            if dry_run:
                log.info(
                    "[DRY RUN] Would move: %s -> %s/%s",
                    source_rel,
                    dest_folder,
                    proposed_name or source.name,
                )
            else:
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(dest_file))
                log.info(
                    "Moved: %s -> %s/%s",
                    source_rel,
                    dest_folder,
                    proposed_name or source.name,
                )
            result.moved += 1

        elif action == "keep":
            result.skipped += 1

        else:
            log.warning("Unknown action '%s' for %s", action, source_rel)
            result.skipped += 1

    return result
