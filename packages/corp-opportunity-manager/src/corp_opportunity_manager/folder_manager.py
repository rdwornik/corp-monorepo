"""Folder creation, template copying, and project scaffolding."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import yaml

from corp_opportunity_manager.config import AppConfig
from corp_opportunity_manager.models import CreationResult, OpportunityConfig, ProjectInfo
from corp_opportunity_manager.templates import deck_filename, folder_name

logger = logging.getLogger(__name__)


def create_opportunity(config: AppConfig, opp: OpportunityConfig) -> CreationResult:
    """Create a new opportunity: folder, deck copy, metadata files.

    Returns a CreationResult summarizing everything created.

    Raises:
        FileExistsError: If the project folder already exists.
        FileNotFoundError: If the templates root doesn't exist.
    """
    # Build folder path
    name = folder_name(
        opp.client,
        opp.product,
        pattern=config.naming.get("folder_pattern", "{client}_{product}"),
    )
    project_dir = config.projects_root / name

    if project_dir.exists():
        raise FileExistsError(f"Project folder already exists: {project_dir}")

    # Create project folder + configured subdirectories
    project_dir.mkdir(parents=True)
    logger.info("Created project folder: %s", project_dir)

    for subdir in config.folder_structure.get("create_dirs", []):
        (project_dir / subdir).mkdir(parents=True, exist_ok=True)
        logger.debug("Created subdirectory: %s", subdir)

    # Copy deck template
    deck_path = _copy_deck_template(config, opp, project_dir)

    # Write metadata files
    knowledge_dir = project_dir / "_knowledge"
    knowledge_dir.mkdir(exist_ok=True)

    info_path = knowledge_dir / "project-info.yaml"
    notes_path = knowledge_dir / "notes.md"

    project_info = ProjectInfo(
        client=opp.client,
        product=opp.product,
        contact=opp.contact,
        stage=opp.stage,
        created=opp.date.isoformat(),
        folder_name=name,
        folder_path=str(project_dir),
    )

    _write_project_info(info_path, project_info)
    _write_notes_stub(notes_path, opp)

    return CreationResult(
        project_info=project_info,
        folder_path=project_dir,
        deck_path=deck_path,
        info_path=info_path,
        notes_path=notes_path,
    )


def _copy_deck_template(
    config: AppConfig, opp: OpportunityConfig, project_dir: Path
) -> Path | None:
    """Copy the discovery deck template into the project folder, renamed."""
    template_name = config.templates.get("discovery_deck", "")
    if not template_name:
        logger.warning("No discovery_deck template configured; skipping deck copy.")
        return None

    source = config.templates_root / template_name
    if not source.exists():
        logger.warning("Deck template not found at %s; skipping deck copy.", source)
        return None

    dest_name = deck_filename(
        client=opp.client,
        topic=opp.topic,
        dt=opp.date,
        date_format=config.naming.get("date_format", "%Y-%m-%d"),
        pattern=config.naming.get("pptx_pattern", "{client}_{date}_{topic}.pptx"),
    )
    dest = project_dir / dest_name
    shutil.copy2(source, dest)
    logger.info("Copied deck template to %s", dest)
    return dest


def _write_project_info(path: Path, info: ProjectInfo) -> None:
    """Write project-info.yaml metadata file."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(info.to_yaml_dict(), f, default_flow_style=False, sort_keys=False)
    logger.info("Wrote project info to %s", path)


def _write_notes_stub(path: Path, opp: OpportunityConfig) -> None:
    """Write an empty notes.md stub with frontmatter."""
    content = f"""---
client: {opp.client}
product: {opp.product}
created: {opp.date.isoformat()}
---

# {opp.client} - {opp.product} Notes

"""
    path.write_text(content, encoding="utf-8")
    logger.info("Wrote notes stub to %s", path)
