"""Vault CLI commands."""

import sys

import click
from corp_by_os.cli._common import console
from corp_by_os.project_resolver import resolve_project
from corp_by_os.vault_io import validate_vault
from corp_os_meta.pipeline_config import PipelineConfig
from rich.table import Table


@click.group()
def vault() -> None:
    """Vault operations."""


@vault.command("validate")
@click.argument("project", required=False, default=None)
@click.pass_obj
def vault_validate(obj: dict, project: str | None) -> None:
    """Validate vault structure and frontmatter."""
    config = (obj or {}).get("config") or PipelineConfig.production()
    project_id = None
    if project:
        resolved = resolve_project(project)
        if resolved:
            project_id = resolved.project_id
        else:
            console.print(f"[red]No project matching '{project}' found.[/red]")
            sys.exit(1)

    console.print("[dim]Running validation...[/dim]")
    report = validate_vault(project_id=project_id, config=config)

    if report.is_valid and not report.issues:
        console.print(
            f"[green]OK[/green] -- {report.notes_checked} notes checked, {report.notes_valid} valid"
        )
        return

    # Show issues
    table = Table(title="Validation Issues", show_lines=False)
    table.add_column("Level", style="bold", width=8)
    table.add_column("Path", style="dim")
    table.add_column("Issue", style="white")

    for issue in report.issues:
        level_style = "red" if issue.level == "error" else "yellow"
        table.add_row(
            f"[{level_style}]{issue.level}[/{level_style}]",
            str(issue.path.name),
            issue.message,
        )

    console.print(table)
    console.print(
        f"\n[dim]{report.notes_checked} notes checked, "
        f"{report.notes_valid} valid, {len(report.issues)} issues[/dim]"
    )
