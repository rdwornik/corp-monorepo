"""Task management actions."""

from __future__ import annotations

import logging

from corp.actions import register_action
from corp.models import StepResult

logger = logging.getLogger(__name__)


@register_action("add_task")
def add_task_action(params: dict[str, str]) -> StepResult:
    """Create a task note — delegates to task_manager."""
    from corp.task_manager import add_task

    title = params.get("title", "")
    if not title:
        return StepResult(
            step_index=0,
            description="Add task",
            success=False,
            error="Missing 'title' parameter",
        )

    path = add_task(
        title=title,
        project_id=params.get("project"),
        deadline=params.get("deadline"),
        priority=params.get("priority", "medium"),
    )

    return StepResult(
        step_index=0,
        description="Add task",
        success=True,
        output=f"Created task: {path.name}",
    )


@register_action("list_tasks")
def list_tasks_action(params: dict[str, str]) -> StepResult:
    """List tasks — delegates to task_manager."""
    from corp.task_manager import list_tasks

    tasks = list_tasks(
        status_filter=params.get("status", "todo"),
        project_filter=params.get("project"),
    )

    if not tasks:
        return StepResult(
            step_index=0,
            description="List tasks",
            success=True,
            output="No tasks found",
        )

    lines = [f"Found {len(tasks)} tasks:"]
    for t in tasks:
        deadline_str = f" (due: {t.deadline})" if t.deadline else ""
        project_str = f" [{t.project}]" if t.project else ""
        lines.append(f"  [{t.priority.value.upper()}] {t.title}{project_str}{deadline_str}")

    return StepResult(
        step_index=0,
        description="List tasks",
        success=True,
        output="\n".join(lines),
    )
