"""Project brief generation action."""

from __future__ import annotations

import logging
from datetime import date

import yaml

from corp.actions import register_action
from corp.config import get_config
from corp.models import StepResult, VaultZone

from ._helpers import _resolve_project_id

logger = logging.getLogger(__name__)


@register_action("generate_project_brief")
def generate_project_brief(params: dict[str, str]) -> StepResult:
    """Read facts.yaml + project-info.yaml, generate 1-pager markdown."""
    from corp.vault_io import read_project_info

    cfg = get_config()
    project = params.get("project", "")
    project_id = _resolve_project_id(project, params)

    info = read_project_info(project_id)
    if info is None:
        return StepResult(
            step_index=0,
            description="Generate project brief",
            success=False,
            error=f"No project-info.yaml found for '{project_id}'",
        )

    # Try to read facts.yaml
    facts: list[dict] = []
    project_dir = cfg.vault_path / VaultZone.PROJECTS.value / project_id
    facts_file = project_dir / "facts.yaml"
    if facts_file.exists():
        try:
            with open(facts_file, encoding="utf-8") as f:
                facts_data = yaml.safe_load(f)
            if isinstance(facts_data, list):
                facts = facts_data[:20]  # top 20 facts for brief
        except (yaml.YAMLError, OSError) as e:
            logger.warning("Failed to parse facts.yaml for %s: %s", project_id, e)

    # Build brief
    lines = [
        "---",
        f'title: "{info.client} — Project Brief"',
        "document_type: brief",
        f'generated: "{date.today().isoformat()}"',
        "tags: [brief, auto-generated]",
        "---",
        "",
        f"# {info.client} — Project Brief",
        "",
        f"**Status:** {info.status}",
        f"**Products:** {', '.join(info.products) if info.products else 'N/A'}",
        f"**Topics:** {', '.join(info.topics) if info.topics else 'N/A'}",
        f"**Domains:** {', '.join(info.domains) if info.domains else 'N/A'}",
        f"**Files Processed:** {info.files_processed}",
        f"**Facts Extracted:** {info.facts_count}",
        f"**Last Extraction:** {info.last_extracted or 'Never'}",
        "",
    ]

    if info.people:
        lines.append("## Key People")
        lines.append("")
        for person in info.people:
            lines.append(f"- {person}")
        lines.append("")

    if facts:
        lines.append("## Key Facts")
        lines.append("")
        for fact in facts:
            if isinstance(fact, dict):
                text = fact.get("text", fact.get("fact", str(fact)))
                lines.append(f"- {text}")
            else:
                lines.append(f"- {fact}")
        lines.append("")

    brief_md = "\n".join(lines)

    # Write to vault
    brief_path = project_dir / "brief.md"
    brief_path.parent.mkdir(parents=True, exist_ok=True)
    brief_path.write_text(brief_md, encoding="utf-8")

    return StepResult(
        step_index=0,
        description="Generate project brief",
        success=True,
        output=f"Brief written to {brief_path}",
    )
