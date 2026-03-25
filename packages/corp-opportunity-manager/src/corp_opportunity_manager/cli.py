"""Click CLI — entry point for `com` command."""

from __future__ import annotations

import io
import logging
import sys
from datetime import date, datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from corp_opportunity_manager.config import load_config
from corp_opportunity_manager.folder_manager import create_opportunity
from corp_opportunity_manager.models import OpportunityConfig

# Force UTF-8 output on Windows to handle international characters in data
_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
console = Console(file=_stdout)
logger = logging.getLogger("corp_opportunity_manager")


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def cli(verbose: bool) -> None:
    """Corp Opportunity Manager — pre-sales opportunity lifecycle tool."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


@cli.command()
@click.argument("client")
@click.option("--product", "-p", required=True, help="Product area (e.g. Planning, WMS).")
@click.option("--contact", "-c", default="", help="Primary contact name and role.")
@click.option("--stage", "-s", default="discovery", help="Opportunity stage.")
@click.option("--topic", "-t", default="Discovery", help="Deck topic for the template copy.")
@click.option("--date", "date_str", default=None, help="Date override (YYYY-MM-DD).")
def new(
    client: str, product: str, contact: str, stage: str, topic: str, date_str: str | None
) -> None:
    """Create a new opportunity with folder, deck, and metadata."""
    config = load_config()

    # Validate stage
    if stage not in config.stages:
        console.print(f"[red]Invalid stage '{stage}'. Valid: {', '.join(config.stages)}[/red]")
        sys.exit(1)

    # Parse date
    opp_date = date.today()
    if date_str:
        try:
            opp_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            console.print("[red]Invalid date format. Use YYYY-MM-DD.[/red]")
            sys.exit(1)

    opp = OpportunityConfig(
        client=client,
        product=product,
        contact=contact,
        stage=stage,
        topic=topic,
        date=opp_date,
    )

    try:
        result = create_opportunity(config, opp)
    except FileExistsError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    # Try to update Excel if configured
    _try_update_excel(config, client, result.folder_path)

    # Rich output
    deck_display = result.deck_path.name if result.deck_path else "(no template found)"
    lines = [
        f"  Folder: [cyan]{result.folder_path}[/cyan]",
        f"  Deck:   [cyan]{deck_display}[/cyan]",
        f"  Info:   [cyan]{result.info_path.name}[/cyan]",
        f"  Notes:  [cyan]{result.notes_path.name}[/cyan]",
        "",
        f"  Client:  [bold]{client}[/bold]",
        f"  Product: {product}",
        f"  Contact: {contact or '(none)'}",
        f"  Stage:   {stage}",
        f"  Created: {opp_date.isoformat()}",
        "",
        "  [dim]Next steps:[/dim]",
        "  [dim]  -> Add Teams channel link to project folder[/dim]",
        "  [dim]  -> Review briefing book when received[/dim]",
        "  [dim]  -> Update project_codes.xlsx with folder link[/dim]",
    ]
    panel = Panel("\n".join(lines), title=f"New Opportunity: {client}", border_style="green")
    console.print(panel)


@cli.command(name="list")
def list_cmd() -> None:
    """List active opportunities from project_codes.xlsx."""
    config = load_config()

    if not config.project_codes_excel or not config.project_codes_excel.exists():
        console.print("[yellow]No project_codes.xlsx configured or file not found.[/yellow]")
        # Fallback: list project folders
        _list_from_folders(config)
        return

    from corp_opportunity_manager.excel_manager import list_projects

    rows = list_projects(config.project_codes_excel)
    if not rows:
        console.print("[yellow]No projects found in spreadsheet.[/yellow]")
        return

    table = Table(title="Active Opportunities")
    table.add_column("Account", style="bold")
    table.add_column("Opportunity")
    table.add_column("Stage")
    table.add_column("Folder")

    for row in rows:
        table.add_row(row.account_name, row.opportunity_name, row.stage, row.folder_link or "-")

    console.print(table)


@cli.command()
@click.argument("client")
def show(client: str) -> None:
    """Show details for an opportunity by client name."""
    config = load_config()

    # Find the project folder
    matching = _find_project_folder(config, client)
    if not matching:
        console.print(f"[red]No project folder found matching '{client}'.[/red]")
        sys.exit(1)

    project_dir = matching
    info_file = project_dir / "_knowledge" / "project-info.yaml"

    if info_file.exists():
        import yaml

        with open(info_file, "r", encoding="utf-8") as f:
            info = yaml.safe_load(f)
        lines = [f"  [bold]{k}:[/bold] {v}" for k, v in info.items()]
        lines.append(f"\n  Path: [cyan]{project_dir}[/cyan]")
        panel = Panel("\n".join(lines), title=f"Opportunity: {client}", border_style="blue")
        console.print(panel)
    else:
        console.print(f"[yellow]Folder exists but no project-info.yaml: {project_dir}[/yellow]")


@cli.command(name="prep-deck")
@click.argument("client")
@click.option("--topic", "-t", required=True, help="Deck topic (e.g. 'Technical Deep Dive').")
@click.option("--date", "date_str", default=None, help="Date override (YYYY-MM-DD).")
def prep_deck(client: str, topic: str, date_str: str | None) -> None:
    """Copy a new presentation template for an existing opportunity."""
    config = load_config()

    matching = _find_project_folder(config, client)
    if not matching:
        console.print(f"[red]No project folder found matching '{client}'.[/red]")
        sys.exit(1)

    opp_date = date.today()
    if date_str:
        try:
            opp_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            console.print("[red]Invalid date format. Use YYYY-MM-DD.[/red]")
            sys.exit(1)

    from corp_opportunity_manager.templates import deck_filename

    template_name = config.templates.get("discovery_deck", "")
    source = config.templates_root / template_name if template_name else None

    if not source or not source.exists():
        console.print(f"[red]Deck template not found: {source}[/red]")
        sys.exit(1)

    import shutil

    dest_name = deck_filename(
        client=client,
        topic=topic,
        dt=opp_date,
        date_format=config.naming.get("date_format", "%Y-%m-%d"),
        pattern=config.naming.get("pptx_pattern", "{client}_{date}_{topic}.pptx"),
    )
    dest = matching / dest_name
    shutil.copy2(source, dest)
    console.print(f"[green]Created deck:[/green] [cyan]{dest}[/cyan]")


def _find_project_folder(config, client: str) -> Path | None:
    """Find a project folder matching the client name (prefix match)."""
    if not config.projects_root.exists():
        return None
    client_lower = client.lower()
    for d in sorted(config.projects_root.iterdir()):
        if d.is_dir() and d.name.lower().startswith(client_lower):
            return d
    return None


def _list_from_folders(config) -> None:
    """Fallback: list project folders when no Excel is available."""
    if not config.projects_root.exists():
        console.print(f"[red]Projects root not found: {config.projects_root}[/red]")
        return

    dirs = [d for d in sorted(config.projects_root.iterdir()) if d.is_dir()]
    if not dirs:
        console.print("[yellow]No project folders found.[/yellow]")
        return

    table = Table(title="Project Folders")
    table.add_column("Folder", style="bold")
    table.add_column("Has Metadata")

    for d in dirs:
        has_meta = "yes" if (d / "_knowledge" / "project-info.yaml").exists() else "no"
        table.add_row(d.name, has_meta)

    console.print(table)


@cli.command()
def chat() -> None:
    """Start an interactive chat session with the opportunity agent."""
    config = load_config()

    try:
        from corp_opportunity_manager.chat import ChatSession
    except ImportError as e:
        console.print(f"[red]Missing dependency for chat: {e}[/red]")
        console.print("[yellow]Install with: pip install -e '.[llm]'[/yellow]")
        sys.exit(1)

    session = ChatSession(config, console)
    session.run()


def _try_update_excel(config, client: str, folder_path: Path) -> None:
    """Attempt to find and update the client's row in project_codes.xlsx."""
    if not config.project_codes_excel or not config.project_codes_excel.exists():
        return

    from corp_opportunity_manager.excel_manager import find_row_by_client, update_folder_link

    row = find_row_by_client(config.project_codes_excel, client)
    if row:
        update_folder_link(config.project_codes_excel, row.row_number, str(folder_path))
        console.print(f"[green]Updated Excel row {row.row_number} with folder link.[/green]")
    else:
        console.print("[dim]No matching row in project_codes.xlsx (add manually).[/dim]")
