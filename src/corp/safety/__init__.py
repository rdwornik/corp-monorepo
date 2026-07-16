"""corp.safety — Foundation-layer safety guards (ADR-27).

Centralizes the OneDrive-synced-tree exclusion guard and path-containment
check that were previously duplicated across ``cleanup/disk.py``,
``cleanup/executor.py``, ``actions/_helpers.py``, and ``project/renderer.py``.
See ``docs/decisions/ADR-27-safety-invariants.md`` (Decision 1).
"""

from .onedrive import (
    OneDriveSafetyError,
    PathTraversalError,
    guard_path,
    guard_within_root,
    is_onedrive_path,
    onedrive_write_exempt,
)

__all__ = [
    "OneDriveSafetyError",
    "PathTraversalError",
    "guard_path",
    "guard_within_root",
    "is_onedrive_path",
    "onedrive_write_exempt",
]
