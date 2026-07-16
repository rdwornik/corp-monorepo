"""Deprecated re-export shim for cleanup/action safety exceptions.

``OneDriveSafetyError`` and ``PathTraversalError`` moved to
``corp.safety.onedrive`` as part of ADR-27 Decision 1 (OneDrive guard
centralization). This module is kept for one release cycle (ADR-27
"Neutral" consequence) so existing importers — ``corp.cleanup.disk``,
``corp.cleanup.executor``, ``corp.actions._helpers``,
``scripts/_audit_core.py``, and their tests — keep working unchanged. New
code should import directly from ``corp.safety.onedrive``.

See INCIDENT 2026-03-14 (OneDrive synced files deleted by cleanup) for the
class of bug these exceptions prevent.
"""

from __future__ import annotations

from corp.safety.onedrive import OneDriveSafetyError, PathTraversalError  # noqa: F401

__all__ = ["OneDriveSafetyError", "PathTraversalError"]
