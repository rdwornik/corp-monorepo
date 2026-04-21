"""Safety exceptions for cleanup and action mutations.

Raised fail-closed when a write/delete operation targets a protected path.
See INCIDENT 2026-03-14 (OneDrive synced files deleted by cleanup) for the
class of bug these exceptions prevent.
"""

from __future__ import annotations


class OneDriveSafetyError(RuntimeError):
    """A write/delete was refused because it targeted a OneDrive-synced path.

    OneDrive - Blue Yonder paths are treated as read-only by design: any
    mutation there risks corrupting synced SharePoint copies and cannot be
    undone locally. Callers must stage files outside OneDrive before writing.
    """


class PathTraversalError(RuntimeError):
    """A path resolved outside its expected root directory.

    Raised when an entry in moves.yaml (or equivalent untrusted source)
    contains ``..`` segments, absolute paths, or otherwise escapes
    ``mywork_root`` after resolution.
    """
