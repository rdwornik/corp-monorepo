"""Shared helpers for built-in actions.

These utility functions are used across multiple action domains.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from corp.cleanup.errors import OneDriveSafetyError
from corp.config import get_config

logger = logging.getLogger(__name__)

_ONEDRIVE_BLOCKED = "OneDrive - Blue Yonder"


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
    :class:`corp.cleanup.errors.OneDriveSafetyError`. Read-intent callers
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

    Checks both the original string form and the resolved form so a
    Windows junction / symlink / configured alias cannot bypass the
    substring check (Codex review H-C2, 2026-04-21). Fails closed if
    ``Path.resolve`` itself raises (unresolvable = unverifiable = refused).

    Mirrors ``cleanup/executor._guard_onedrive`` and
    ``cleanup/disk._guard_onedrive`` so future centralization (ADR-27)
    can replace all three sites with one import.
    """
    if not writable:
        return

    original = str(path)
    candidates = [original]
    try:
        candidates.append(str(path.resolve(strict=False)))
    except (OSError, RuntimeError) as exc:
        raise OneDriveSafetyError(
            f"BLOCKED: cannot resolve {original!r} to verify synced-tree "
            f"safety for write-intent operation: {exc}"
        ) from exc

    if any(_ONEDRIVE_BLOCKED in c for c in candidates):
        raise OneDriveSafetyError(
            f"BLOCKED: refusing write-intent resolution of synced path: {path} "
            f"(resolved candidates: {candidates}). "
            "See INCIDENT 2026-03-14 and project/renderer.py (2026-03-30). "
            "Stage the project to a local path before writing."
        )


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
