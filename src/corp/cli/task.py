"""Task CLI commands."""

import sys

import click
from rich.panel import Panel

from corp.cli._common import console
from corp.project_resolver import resolve_project


@click.group("task")
def task_group() -> None:
    """Manage tasks."""


@task_group.command("add")
@click.argument("title")
@click.option("--project", "-p", default=None, help="Associated project")
@click.option("--deadline", "-d", default=None, help="Deadline (YYYY-MM-DD)")
@click.option("--priority", default="medium", type=click.Choice(["high", "medium", "low"]))
def task_add(title: str, project: str | None, deadline: str | None, priority: str) -> None:
    """Create a new task."""
    from corp.task_manager import add_task

    project_id = None
    if project:
        resolved = resolve_project(project)
        project_id = resolved.project_id if resolved else project

    path = add_task(title=title, project_id=project_id, deadline=deadline, priority=priority)
    console.print(f"[green]Created:[/green] {path.name}")


@task_group.command("list")
@click.option("--status", "-s", default="todo", help="Filter by status")
@click.option("--project", "-p", default=None, help="Filter by project")
@click.option("--all", "show_all", is_flag=True, help="Show all statuses")
def task_list(status: str, project: str | None, show_all: bool) -> None:
    """List tasks sorted by priority and deadline."""
    from corp.task_manager import list_tasks

    status_filter = None if show_all else status
    tasks = list_tasks(status_filter=status_filter, project_filter=project)

    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        return

    # Group by priority
    by_priority: dict[str, list] = {"high": [], "medium": [], "low": []}
    for t in tasks:
        by_priority.setdefault(t.priority.value, []).append(t)

    lines: list[str] = []
    priority_labels = {
        "high": "[red]HIGH[/red]",
        "medium": "[yellow]MEDIUM[/yellow]",
        "low": "[dim]LOW[/dim]",
    }

    for prio in ["high", "medium", "low"]:
        group = by_priority.get(prio, [])
        if not group:
            continue
        lines.append(f"\n  {priority_labels[prio]}")
        for t in group:
            deadline_str = f"  ({t.deadline})" if t.deadline else ""
            project_str = f" [dim][{t.project}][/dim]" if t.project else ""
            marker = "[green]x[/green]" if t.status.value == "done" else "[ ]"
            lines.append(f"   {marker} {t.title}{project_str}{deadline_str}")

    console.print(Panel("\n".join(lines), title="My Tasks", border_style="blue"))
    console.print(f"[dim]{len(tasks)} tasks[/dim]")


@task_group.command("done")
@click.argument("title")
def task_done(title: str) -> None:
    """Mark a task as complete (fuzzy title match)."""
    from corp.task_manager import complete_task

    if complete_task(title):
        console.print(f"[green]Completed:[/green] {title}")
    else:
        console.print(f"[red]No matching task found:[/red] {title}")
        sys.exit(1)


@click.command("tasks")
@click.option("--status", "-s", default="todo", help="Filter by status")
@click.option("--all", "show_all", is_flag=True, help="Show all statuses")
def tasks_shortcut(status: str, show_all: bool) -> None:
    """Shortcut for 'corp task list'."""
    from corp.task_manager import list_tasks

    status_filter = None if show_all else status
    tasks = list_tasks(status_filter=status_filter)

    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        return

    by_priority: dict[str, list] = {"high": [], "medium": [], "low": []}
    for t in tasks:
        by_priority.setdefault(t.priority.value, []).append(t)

    lines: list[str] = []
    priority_labels = {
        "high": "[red]HIGH[/red]",
        "medium": "[yellow]MEDIUM[/yellow]",
        "low": "[dim]LOW[/dim]",
    }

    for prio in ["high", "medium", "low"]:
        group = by_priority.get(prio, [])
        if not group:
            continue
        lines.append(f"\n  {priority_labels[prio]}")
        for t in group:
            deadline_str = f"  ({t.deadline})" if t.deadline else ""
            project_str = f" [dim][{t.project}][/dim]" if t.project else ""
            lines.append(f"   [ ] {t.title}{project_str}{deadline_str}")

    console.print(Panel("\n".join(lines), title="My Tasks", border_style="blue"))
    console.print(f"[dim]{len(tasks)} tasks[/dim]")
