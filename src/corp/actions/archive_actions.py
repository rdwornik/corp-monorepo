"""Archive actions: project archival and metadata updates."""

from __future__ import annotations

import logging
import shutil
from datetime import date

import yaml

from corp.actions import register_action
from corp.config import get_config
from corp.models import StepResult, VaultZone

from ._helpers import _resolve_project_id, _resolve_project_path

logger = logging.getLogger(__name__)


@register_action("archive_project")
def archive_project(params: dict[str, str]) -> StepResult:
    """Move project folder to 80_Archive/{year}/, update metadata."""
    cfg = get_config()
    project = params.get("project", "")
    reason = params.get("reason", "")
    notes = params.get("notes", "")

    if not project:
        return StepResult(
            step_index=0,
            description="Archive project",
            success=False,
            error="Missing 'project' parameter",
        )

    project_path = _resolve_project_path(project, params)
    if not project_path or not project_path.exists():
        return StepResult(
            step_index=0,
            description="Archive project",
            success=False,
            error=f"Project folder not found: {project}",
        )

    # Move to archive
    year = str(date.today().year)
    archive_dir = cfg.archive_root / year
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / project_path.name

    if dest.exists():
        return StepResult(
            step_index=0,
            description="Archive project",
            success=False,
            error=f"Archive destination already exists: {dest}",
        )

    shutil.move(str(project_path), str(dest))

    # Update project-info.yaml in vault if it exists
    project_id = _resolve_project_id(project, params)
    vault_dir = cfg.vault_path / VaultZone.PROJECTS.value / project_id
    info_file = vault_dir / "project-info.yaml"
    if info_file.exists():
        try:
            with open(info_file, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            data["status"] = "archived"
            data["archive_reason"] = reason
            data["archive_date"] = date.today().isoformat()
            if notes:
                data["archive_notes"] = notes
            info_file.write_text(
                yaml.dump(data, default_flow_style=False, allow_unicode=True),
                encoding="utf-8",
            )
        except (OSError, yaml.YAMLError) as e:
            logger.warning("Failed to update project-info.yaml: %s", e)

    return StepResult(
        step_index=0,
        description="Archive project",
        success=True,
        output=f"Archived {project_path.name} to {dest}",
    )


@register_action("update_archive_metadata")
def update_archive_metadata(params: dict[str, str]) -> StepResult:
    """Update vault metadata after archiving."""
    project = params.get("project", "")
    project_id = _resolve_project_id(project, params)

    cfg = get_config()
    vault_dir = cfg.vault_path / VaultZone.PROJECTS.value / project_id
    info_file = vault_dir / "project-info.yaml"

    if not info_file.exists():
        return StepResult(
            step_index=0,
            description="Update archive metadata",
            success=True,
            output="No vault metadata to update",
        )

    try:
        with open(info_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        data["status"] = "archived"
        info_file.write_text(
            yaml.dump(data, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
    except (OSError, yaml.YAMLError) as e:
        return StepResult(
            step_index=0,
            description="Update archive metadata",
            success=False,
            error=str(e),
        )

    return StepResult(
        step_index=0,
        description="Update archive metadata",
        success=True,
        output=f"Updated metadata for {project_id}",
    )
