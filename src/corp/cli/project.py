"""Project management CLI commands."""

import os
import sys

import click
from rich.table import Table

from corp.cli._common import CHECK, DASH, console
from corp.project_resolver import resolve_project
from corp.schema.pipeline_config import PipelineConfig
from corp.vault_io import list_projects, read_project_info


@click.group()
def project() -> None:
    """Manage projects."""


@project.command("list")
@click.option("--status", "-s", default=None, help="Filter by status (active, rfp, won, etc.)")
@click.pass_obj
def project_list(obj: dict, status: str | None) -> None:
    """List all projects with metadata status."""
    config = (obj or {}).get("config") or PipelineConfig.production()
    projects = list_projects(status_filter=status, config=config)

    if not projects:
        console.print("[yellow]No projects found.[/yellow]")
        return

    table = Table(title="Projects", show_lines=False)
    table.add_column("Project", style="cyan", no_wrap=True)
    table.add_column("Client", style="white")
    table.add_column("Status", style="green")
    table.add_column("Vault", justify="center")
    table.add_column("OneDrive", justify="center")
    table.add_column("Facts", justify="right")

    for p in projects:
        table.add_row(
            p.project_id,
            p.client,
            p.status,
            CHECK if p.has_vault else DASH,
            CHECK if p.has_onedrive else DASH,
            str(p.facts_count) if p.facts_count else DASH,
        )

    console.print(table)
    console.print(f"\n[dim]{len(projects)} projects total[/dim]")


@project.command("show")
@click.argument("name")
def project_show(name: str) -> None:
    """Show project details (fuzzy name match)."""
    resolved = resolve_project(name)

    if not resolved:
        console.print(f"[red]No project matching '{name}' found.[/red]")
        sys.exit(1)

    if resolved.score < 1.0:
        console.print(f"[dim]Matched: {resolved.folder_name} (score: {resolved.score:.1f})[/dim]")

    # Try to read project-info.yaml
    info = read_project_info(resolved.project_id)

    if info:
        table = Table(title=f"Project: {info.client}", show_header=False, box=None)
        table.add_column("Field", style="cyan", width=18)
        table.add_column("Value", style="white")

        table.add_row("Project ID", info.project_id)
        table.add_row("Client", info.client)
        table.add_row("Status", info.status)
        table.add_row("Products", ", ".join(info.products) if info.products else "–")
        table.add_row("Topics", ", ".join(info.topics) if info.topics else "–")
        table.add_row("Domains", ", ".join(info.domains) if info.domains else "–")
        table.add_row("Files Processed", str(info.files_processed))
        table.add_row("Facts", str(info.facts_count))
        table.add_row("Last Extracted", info.last_extracted or "–")

        if info.region:
            table.add_row("Region", info.region)
        if info.industry:
            table.add_row("Industry", info.industry)
        if info.people:
            table.add_row("People", ", ".join(info.people))

        console.print(table)
    else:
        console.print(
            f"[yellow]No project-info.yaml found in vault for {resolved.folder_name}[/yellow]"
        )

    console.print()
    if resolved.onedrive_path:
        console.print(f"[dim]OneDrive:[/dim] {resolved.onedrive_path}")
    if resolved.vault_path:
        console.print(f"[dim]Vault:[/dim]    {resolved.vault_path}")


@project.command("open")
@click.argument("name")
def project_open(name: str) -> None:
    """Open project folder in Explorer (fuzzy name match)."""
    resolved = resolve_project(name)

    if not resolved:
        console.print(f"[red]No project matching '{name}' found.[/red]")
        sys.exit(1)

    path = resolved.onedrive_path or resolved.vault_path
    if not path:
        console.print(f"[red]No folder found for {resolved.folder_name}[/red]")
        sys.exit(1)

    console.print(f"Opening {path}")
    os.startfile(str(path))
