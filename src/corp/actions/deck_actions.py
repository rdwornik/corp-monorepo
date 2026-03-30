"""Deck/template actions: template selection and copy."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from corp.actions import register_action
from corp.config import get_config
from corp.models import StepResult

from ._helpers import _resolve_project_path

logger = logging.getLogger(__name__)


@register_action("select_template_for_deck")
def select_template_for_deck(params: dict[str, str]) -> StepResult:
    """Select the best template for a presentation topic."""
    from corp.template_manager import load_registry, select_template

    topic = params.get("topic", "")
    template_id = params.get("template_id", "")

    templates = load_registry()
    if not templates:
        return StepResult(
            step_index=0,
            description="Select template",
            success=False,
            error="No templates in registry. Run `corp template scan` first.",
        )

    if template_id:
        # User explicitly chose a template
        match = [t for t in templates if t.id == template_id]
        if match:
            selected = match[0]
        else:
            return StepResult(
                step_index=0,
                description="Select template",
                success=False,
                error=f"Template '{template_id}' not found. Run `corp template list`.",
            )
    else:
        selected = select_template(topic, templates)
        if selected is None:
            return StepResult(
                step_index=0,
                description="Select template",
                success=False,
                error="No matching template found.",
            )

    # Pass selection to next step via params
    params["_selected_template_id"] = selected.id
    params["_selected_template_path"] = selected.path
    params["_selected_template_file"] = selected.file
    params["_selected_template_name"] = selected.name

    return StepResult(
        step_index=0,
        description="Select template",
        success=True,
        output=f"Selected: {selected.name} ({selected.id})",
    )


@register_action("copy_deck_to_project")
def copy_deck_to_project(params: dict[str, str]) -> StepResult:
    """Copy selected template to project folder with naming convention."""
    from corp.template_manager import copy_template, load_registry

    template_id = params.get("_selected_template_id", "")
    if not template_id:
        return StepResult(
            step_index=0,
            description="Copy deck",
            success=False,
            error="No template selected (missing _selected_template_id).",
        )

    project = params.get("project", "")
    topic = params.get("topic", "presentation")
    deck_date = params.get("date", date.today().isoformat())
    if deck_date == "today":
        deck_date = date.today().isoformat()

    # Load template info
    templates = load_registry()
    match = [t for t in templates if t.id == template_id]
    if not match:
        return StepResult(
            step_index=0,
            description="Copy deck",
            success=False,
            error=f"Template '{template_id}' not in registry.",
        )
    template = match[0]

    # Resolve destination
    dest_dir = _resolve_project_path(project, params)
    if not dest_dir:
        # Fallback: use projects_root / project
        cfg = get_config()
        dest_dir = cfg.projects_root / project

    # Build filename: {Client}_{Date}_{Topic}.ext
    client = params.get("client", project.split("_")[0] if "_" in project else project)
    topic_slug = topic.replace(" ", "_").title()
    ext = Path(template.file).suffix
    new_name = f"{client}_{deck_date}_{topic_slug}{ext}"

    try:
        result_path = copy_template(template, dest_dir, new_name)
        return StepResult(
            step_index=0,
            description="Copy deck",
            success=True,
            output=f"Copied to {result_path}",
        )
    except FileNotFoundError as e:
        return StepResult(
            step_index=0,
            description="Copy deck",
            success=False,
            error=str(e),
        )
    except OSError as e:
        return StepResult(
            step_index=0,
            description="Copy deck",
            success=False,
            error=f"Copy failed: {e}",
        )
