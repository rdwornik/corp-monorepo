"""Shared helpers for built-in actions.

These utility functions are used across multiple action domains.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from corp.config import get_config
from corp.safety.onedrive import guard_path

logger = logging.getLogger(__name__)


def _project_display_name(proj) -> str:
    """Get original-casing folder name from a ProjectSummary."""
    if proj.onedrive_path:
        return proj.onedrive_path.name
    if proj.vault_path:
        return proj.vault_path.name
    return proj.project_id


def _slugify(text: str) -> str:
    """Convert text to a project slug."""
    return text.lower().replace(" ", "_").replace("-", "_")


def _resolve_project_id(project: str, params: dict[str, str]) -> str:
    """Resolve a project name to a project_id."""
    if not project:
        # Build from client + product matching com new's {client}_{product} pattern
        client = params.get("client", "")
        product = params.get("product", "")
        if client:
            folder_name = client if not product else f"{client}_{product}"
            return folder_name.lower()
        return ""

    # Try fuzzy resolution
    try:
        from corp.project_resolver import resolve_project

        resolved = resolve_project(project)
        if resolved:
            return resolved.project_id
    except (ImportError, ValueError, KeyError, OSError) as e:
        logger.debug("Project resolution fallback to slug: %s", e)

    return _slugify(project)


def _resolve_project_path(
    project: str,
    params: dict[str, str],
    *,
    writable: bool = False,
) -> Path | None:
    """Resolve a project name to its on-disk path.

    When ``writable=True``, the resolver refuses to return a path under the
    synced tree ("OneDrive - Blue Yonder") and raises
    :class:`corp.safety.onedrive.OneDriveSafetyError`. Read-intent callers
    (``copy_to_vault_action``) leave the default so they can still stage
    content. Write-intent callers (``archive_project``) must opt in.
    """
    # Check if project_path was provided directly
    if "project_path" in params:
        path = Path(params["project_path"])
        if path.exists():
            _guard_writable(path, writable)
            return path

    if not project:
        return None

    try:
        from corp.project_resolver import resolve_project

        resolved = resolve_project(project)
        if resolved and resolved.onedrive_path:
            _guard_writable(resolved.onedrive_path, writable)
            return resolved.onedrive_path
    except (ImportError, OSError) as e:
        logger.debug("OneDrive path not resolvable for %s: %s", project, e)

    # Try direct path
    cfg = get_config()
    for folder in cfg.projects_root.iterdir():
        if folder.is_dir() and folder.name.lower() == project.lower():
            _guard_writable(folder, writable)
            return folder

    return None


def _guard_writable(path: Path, writable: bool) -> None:
    """Raise if ``writable=True`` and ``path`` is under the synced tree.

    Thin wrapper over :func:`corp.safety.onedrive.guard_path` (ADR-27
    Decision 1 centralization) — delegates the resolve-then-substring check
    there now. Kept as a named function, preserving its ``writable``-gated
    semantics, so the existing call sites above and test importers do not
    need to change. No-op when ``writable=False`` (read-intent callers).
    """
    if not writable:
        return
    guard_path(path, reason="actions write-intent")


def _serialize_issues(issues: list[dict[str, str]]) -> str:
    """Serialize issues list to YAML string for passing between steps."""
    return yaml.dump(issues, default_flow_style=False)


def _deserialize_issues(issues_str: str) -> list[dict[str, str]]:
    """Deserialize issues from YAML string."""
    try:
        data = yaml.safe_load(issues_str)
        return data if isinstance(data, list) else []
    except Exception:
        return []
