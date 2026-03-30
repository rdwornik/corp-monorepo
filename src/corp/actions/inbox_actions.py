"""Inbox scanning action."""

from __future__ import annotations

import logging

from corp.actions import register_action
from corp.config import get_config
from corp.models import StepResult
from corp.schema.folder_names import INBOX

logger = logging.getLogger(__name__)


@register_action("scan_inbox")
def scan_inbox(params: dict[str, str]) -> StepResult:
    """List files in 00_Inbox/, classify by extension/name."""
    cfg = get_config()
    inbox_path = cfg.projects_root.parent / INBOX

    if not inbox_path.exists():
        return StepResult(
            step_index=0,
            description="Scan inbox",
            success=True,
            output="Inbox directory not found",
        )

    files = [f for f in inbox_path.rglob("*") if f.is_file()]

    if not files:
        return StepResult(
            step_index=0,
            description="Scan inbox",
            success=True,
            output="Inbox is empty",
        )

    classified: dict[str, list[str]] = {}
    for f in files:
        ext = f.suffix.lower() or "(no extension)"
        classified.setdefault(ext, []).append(f.name)

    output_lines = [f"Found {len(files)} files in inbox:"]
    for ext, names in sorted(classified.items()):
        output_lines.append(f"  {ext}: {len(names)} files")
        for name in names[:5]:
            output_lines.append(f"    - {name}")
        if len(names) > 5:
            output_lines.append(f"    ... and {len(names) - 5} more")

    return StepResult(
        step_index=0,
        description="Scan inbox",
        success=True,
        output="\n".join(output_lines),
    )
