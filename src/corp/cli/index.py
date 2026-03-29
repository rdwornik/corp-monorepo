"""Index CLI commands."""

import sys

import click
from rich.table import Table

from corp.cli._common import console
from corp.schema.pipeline_config import PipelineConfig


@click.group("index")
def index_group() -> None:
    """Manage the cross-project search index."""


@index_group.command("rebuild")
@click.option("--project", "-p", default=None, help="Update single project only")
@click.pass_obj
def index_rebuild(obj: dict, project: str | None) -> None:
    """Rebuild the SQLite index from all projects."""
    from corp.index_builder import rebuild_index, update_project

    config = (obj or {}).get("config") or PipelineConfig.production()

    if project:
        console.print(f"[dim]Updating index for {project}...[/dim]")
        ok = update_project(project, config=config)
        if ok:
            console.print(f"[green]Updated {project} in index.[/green]")
        else:
            console.print(f"[red]Project '{project}' not found.[/red]")
            sys.exit(1)
    else:
        console.print("[dim]Rebuilding full index...[/dim]")
        stats = rebuild_index(config=config)
        console.print(
            f"[green]Indexed {stats.projects_indexed} projects, "
            f"{stats.facts_indexed} facts, "
            f"{stats.notes_indexed} notes[/green] in {stats.rebuild_duration:.1f}s",
        )
        console.print(f"[dim]{stats.index_path}[/dim]")


@index_group.command("stats")
def index_stats() -> None:
    """Show index stats."""
    from corp.index_builder import get_index_path, get_index_stats

    path = get_index_path()
    if not path.exists():
        console.print("[yellow]No index found. Run `corp index rebuild` first.[/yellow]")
        return

    stats = get_index_stats()
    size_mb = path.stat().st_size / (1024 * 1024)

    table = Table(title="Index Stats", show_header=False, box=None)
    table.add_column("Key", style="cyan", width=25)
    table.add_column("Value", style="white")

    table.add_row("Path", str(path))
    table.add_row("Size", f"{size_mb:.2f} MB")
    table.add_row("Projects", stats.get("total_projects", "?"))
    table.add_row("Facts", stats.get("total_facts", "?"))
    table.add_row("Notes", stats.get("total_notes", "?"))
    table.add_row("Last rebuild", stats.get("last_rebuild", "never"))
    table.add_row("Rebuild duration", f"{stats.get('rebuild_duration_seconds', '?')}s")

    console.print(table)
