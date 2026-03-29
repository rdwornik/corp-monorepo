"""Workflow CLI commands."""

import sys

import click
from rich.panel import Panel
from rich.table import Table

from corp.cli._common import CHECK, DASH, console
from corp.project_resolver import resolve_project


@click.command("run")
@click.argument("workflow", required=False, default=None)
@click.option("--list", "list_workflows", is_flag=True, help="List available workflows")
@click.option("--dry-run", is_flag=True, help="Preview without executing")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option("--client", default=None, help="Client name")
@click.option("--product", default=None, help="Product name")
@click.option("--contact", default=None, help="Contact name")
@click.option("--project", default=None, help="Project name/ID")
@click.option("--topic", default=None, help="Topic/subject")
@click.option("--date", default=None, help="Date (YYYY-MM-DD)")
@click.option("--reason", default=None, help="Reason (for archive)")
@click.option("--notes", default=None, help="Additional notes")
@click.option("--title", default=None, help="Task title")
@click.option("--deadline", default=None, help="Deadline (YYYY-MM-DD)")
@click.option("--priority", default=None, help="Priority (high/medium/low)")
@click.option("--status", default=None, help="Status filter")
def run_workflow(
    workflow: str | None,
    list_workflows: bool,
    dry_run: bool,
    confirm: bool,
    **kwargs: str | None,
) -> None:
    """Execute a workflow or list available workflows."""
    from corp.workflow_engine import (
        execute_workflow,
        load_workflows,
        preview_workflow,
    )

    workflows = load_workflows()

    if list_workflows or workflow is None:
        _show_workflow_list(workflows)
        return

    if workflow not in workflows:
        console.print(f"[red]Unknown workflow: {workflow}[/red]")
        console.print(f"[dim]Available: {', '.join(workflows.keys())}[/dim]")
        sys.exit(1)

    wf = workflows[workflow]

    # Build params from CLI options
    params = {k: v for k, v in kwargs.items() if v is not None}

    # Resolve project path if project is specified
    if "project" in params:
        resolved = resolve_project(params["project"])
        if resolved and resolved.onedrive_path:
            params["project_path"] = str(resolved.onedrive_path)

    # Preview
    if dry_run:
        preview = preview_workflow(wf, params)
        console.print(Panel(preview, title="Dry Run", border_style="yellow"))
        return

    # Show what we're about to do
    _show_workflow_panel(wf, params)

    # Confirmation
    if wf.confirmation and not confirm:
        if not click.confirm("Proceed?", default=True):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    # Execute
    result = execute_workflow(wf, params)

    # Show results
    for step in result.steps:
        status = "[green]OK[/green]" if step.success else "[red]FAIL[/red]"
        duration = f"({step.duration_seconds:.1f}s)" if step.duration_seconds > 0 else ""
        console.print(
            f"  Step {step.step_index + 1}/{len(wf.steps)}: "
            f"{step.description}... {status} {duration}"
        )
        if step.output and not step.success:
            console.print(f"    [dim]{step.output}[/dim]")
        if step.error:
            console.print(f"    [red]{step.error}[/red]")

    # Summary
    if result.success:
        console.print(
            Panel(
                f"All {len(result.steps)} steps succeeded in {result.duration_seconds:.1f}s",
                title="Complete",
                border_style="green",
            )
        )
    else:
        failed = [s for s in result.steps if not s.success]
        console.print(
            Panel(
                f"{len(failed)} step(s) failed. See errors above.",
                title="Failed",
                border_style="red",
            )
        )
        sys.exit(1)


def _show_workflow_list(workflows: dict) -> None:
    """Display available workflows in a table."""
    table = Table(title="Available Workflows", show_lines=False)
    table.add_column("Workflow", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Confirm", justify="center", width=8)
    table.add_column("Cost", style="dim", width=15)

    for wf_id, wf in sorted(workflows.items()):
        table.add_row(
            wf_id,
            wf.description,
            CHECK if wf.confirmation else DASH,
            wf.cost_estimate or "free",
        )

    console.print(table)


def _show_workflow_panel(wf, params: dict) -> None:
    """Show a panel with workflow details before execution."""
    lines = [f"[bold]{wf.description}[/bold]"]

    if params:
        lines.append("")
        for k, v in params.items():
            if not k.startswith("_"):
                lines.append(f"  {k}: {v}")

    if wf.cost_estimate:
        lines.append(f"\n  Cost estimate: {wf.cost_estimate}")

    lines.append(f"\n  Steps: {len(wf.steps)}")
    for i, step in enumerate(wf.steps, 1):
        tag = f"[{step.agent}]" if step.agent else ""
        lines.append(f"    {i}. {tag} {step.description}")

    console.print(Panel("\n".join(lines), title=f"Workflow: {wf.id}", border_style="blue"))
