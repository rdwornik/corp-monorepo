"""Vault-related actions: skeleton creation, validation, copy."""

from __future__ import annotations

import logging

import yaml

from corp.actions import register_action
from corp.config import get_config
from corp.models import StepResult, VaultZone

from ._helpers import _resolve_project_id, _resolve_project_path

logger = logging.getLogger(__name__)


@register_action("create_vault_skeleton")
def create_vault_skeleton(params: dict[str, str]) -> StepResult:
    """Create 01_projects/{project_id}/ with project-info.yaml stub."""
    cfg = get_config()
    client = params.get("client", "")
    product = params.get("product", "")

    if not client:
        return StepResult(
            step_index=0,
            description="Create vault skeleton",
            success=False,
            error="Missing 'client' parameter",
        )

    # Build project_id matching com new's {client}_{product} pattern, then lowercase
    folder_name = client if not product else f"{client}_{product}"
    project_id = folder_name.lower()

    project_dir = cfg.vault_path / VaultZone.PROJECTS.value / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create project-info.yaml stub
    info_file = project_dir / "project-info.yaml"
    if not info_file.exists():
        info = {
            "project_id": project_id,
            "client": client,
            "status": "active",
            "products": [product] if product else [],
            "topics": [],
            "domains": [],
            "files_processed": 0,
            "facts_count": 0,
            "last_extracted": None,
        }
        info_file.write_text(
            yaml.dump(info, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
        logger.info("Created project-info.yaml at %s", info_file)

    # Create empty index.md
    index_file = project_dir / "index.md"
    if not index_file.exists():
        index_file.write_text(
            f"---\ntitle: {client} Project Overview\n"
            f"document_type: project_overview\n---\n\n"
            f"# {client}\n\nProject overview — auto-generated.\n",
            encoding="utf-8",
        )

    return StepResult(
        step_index=0,
        description="Create vault skeleton",
        success=True,
        output=f"Created vault skeleton at {project_dir}",
    )


@register_action("validate_project")
def validate_project(params: dict[str, str]) -> StepResult:
    """Validate a project's vault structure."""
    from corp.vault_io import validate_vault

    project = params.get("project", params.get("client", ""))
    project_id = _resolve_project_id(project, params)

    report = validate_vault(project_id=project_id)

    if report.is_valid:
        return StepResult(
            step_index=0,
            description="Validate project",
            success=True,
            output=f"Valid: {report.notes_checked} notes checked, {report.notes_valid} valid",
        )
    else:
        issues_str = "\n".join(f"  {i.level}: {i.message}" for i in report.issues)
        return StepResult(
            step_index=0,
            description="Validate project",
            success=False,
            output=f"{report.notes_checked} notes checked",
            error=f"Validation issues:\n{issues_str}",
        )


@register_action("copy_to_vault")
def copy_to_vault_action(params: dict[str, str]) -> StepResult:
    """Copy _knowledge/ and notes to vault zones."""
    from corp.vault_io import copy_to_vault

    project = params.get("project", "")
    project_id = _resolve_project_id(project, params)
    project_path = _resolve_project_path(project, params)

    if not project_path:
        return StepResult(
            step_index=0,
            description="Copy to vault",
            success=False,
            error=f"Could not resolve project path for '{project}'",
        )

    copied_total = 0

    # Copy _knowledge/ -> 01_projects/{project_id}/
    knowledge_dir = project_path / "_knowledge"
    if knowledge_dir.exists():
        copied = copy_to_vault(knowledge_dir, VaultZone.PROJECTS, project_id)
        copied_total += len(copied)

    # Copy _extracted/notes/ -> 02_sources/{project_id}/
    notes_dir = project_path / "_extracted" / "notes"
    if notes_dir.exists():
        copied = copy_to_vault(notes_dir, VaultZone.SOURCES, project_id)
        copied_total += len(copied)

    return StepResult(
        step_index=0,
        description="Copy to vault",
        success=True,
        output=f"Copied {copied_total} files to vault",
    )
