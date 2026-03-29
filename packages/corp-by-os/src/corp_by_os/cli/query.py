"""Query and folder-review CLI commands."""

import sys
from pathlib import Path

import click
from corp_by_os.cli._common import console, logger
from rich.table import Table


@click.command("query")
@click.argument("search_terms", required=False, default=None)
@click.option("--project", "-p", default=None, help="Filter by project")
@click.option("--product", default=None, help="Filter by product")
@click.option("--topic", default=None, help="Filter by topic")
@click.option("--limit", "-n", default=20, help="Max results")
def query_command(
    search_terms: str | None,
    project: str | None,
    product: str | None,
    topic: str | None,
    limit: int,
) -> None:
    """Search across project facts and metadata."""
    from corp_by_os.index_builder import get_index_path

    if not get_index_path().exists():
        console.print("[yellow]No index. Run `corp index rebuild` first.[/yellow]")
        sys.exit(1)

    if search_terms:
        from corp_by_os.query_engine import search_facts

        results = search_facts(search_terms, project_filter=project, limit=limit)
        if not results:
            console.print(f"[yellow]No results for '{search_terms}'[/yellow]")
            return

        table = Table(title=f"Facts matching '{search_terms}'", show_lines=True)
        table.add_column("Client", style="cyan", width=20)
        table.add_column("Fact", style="white")
        table.add_column("Source", style="dim", width=25)

        for r in results:
            table.add_row(r.client, r.fact[:150], r.source_title[:25] if r.source_title else "")

        console.print(table)
        console.print(f"[dim]{len(results)} results[/dim]")

    elif product or topic:
        from corp_by_os.query_engine import search_projects

        products_list = [product] if product else None
        topics_list = [topic] if topic else None
        results = search_projects(products=products_list, topics=topics_list)

        if not results:
            console.print("[yellow]No matching projects.[/yellow]")
            return

        table = Table(title="Matching Projects", show_lines=False)
        table.add_column("Project", style="cyan")
        table.add_column("Client", style="white")
        table.add_column("Status", style="green")
        table.add_column("Products", style="dim")
        table.add_column("Facts", justify="right")

        for r in results:
            table.add_row(
                r.project_id,
                r.client,
                r.status,
                ", ".join(r.products[:3]),
                str(r.facts_count),
            )

        console.print(table)
        console.print(f"[dim]{len(results)} projects[/dim]")
    else:
        console.print("[yellow]Provide search terms or --product/--topic filter.[/yellow]")
        sys.exit(1)


@click.command("folder-review")
@click.option(
    "--path",
    default=None,
    type=click.Path(exists=True, file_okay=False),
    help="Projects root to scan (default: MyWork/10_Projects/)",
)
def folder_review_command(path: str | None) -> None:
    """Scan 10_Projects/ folders and propose renames.  Report only — no files modified."""
    from corp_by_os.ingest.renamer import FolderRenameProposal, propose_folder_name

    if path:
        root = Path(path)
    else:
        import tomllib

        _paths_toml = Path(__file__).parents[4] / "config" / "paths.toml"
        with _paths_toml.open("rb") as fh:
            _cfg = tomllib.load(fh)
        root = Path(_cfg["paths"]["mywork"]) / "10_Projects"

    if not root.exists():
        console.print(f"[red]Path not found: {root}[/red]")
        raise SystemExit(1)

    folders = sorted(d for d in root.iterdir() if d.is_dir() and not d.name.startswith("."))
    if not folders:
        console.print("[yellow]No subfolders found.[/yellow]")
        return

    console.print(f"[dim]Scanning {len(folders)} folders in {root}...[/dim]\n")

    proposals: list[FolderRenameProposal] = []
    for folder in folders:
        try:
            proposals.append(propose_folder_name(folder))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not process %s: %s", folder.name, exc)

    table = Table(title="Folder Review — Proposed Renames", show_lines=True)
    table.add_column("Current Name", style="cyan", no_wrap=False, max_width=40)
    table.add_column("Proposed Name", style="green", no_wrap=False, max_width=40)
    table.add_column("Kind", justify="center")
    table.add_column("Span", justify="right")
    table.add_column("Files", justify="right")
    table.add_column("Status", justify="center")

    changes = 0
    for p in proposals:
        kind = "[yellow]EVENT[/yellow]" if p.is_event else "PROJECT"
        span = f"{p.span_days:.0f}d"
        if p.consolidate:
            status = "[yellow]review: consolidate?[/yellow]"
        elif p.unchanged:
            status = "[dim]same[/dim]"
        else:
            status = "[bold green]RENAME[/bold green]"
            changes += 1
        table.add_row(p.original_name, p.proposed_name, kind, span, str(p.file_count), status)

    console.print(table)
    console.print(
        f"\n[dim]{len(proposals)} folders | {changes} would rename | "
        "report only — no files modified[/dim]"
    )
