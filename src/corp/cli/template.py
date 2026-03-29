"""Template CLI commands."""

import click
from corp_by_os.cli._common import console
from corp_by_os.config import get_config
from rich.table import Table


@click.group("template")
def template_group() -> None:
    """Manage presentation templates."""


@template_group.command("list")
def template_list() -> None:
    """Show all registered templates."""
    from corp_by_os.template_manager import load_registry

    templates = load_registry()
    if not templates:
        console.print("[yellow]No templates registered. Run `corp template scan` first.[/yellow]")
        return

    table = Table(title="Template Registry", show_lines=False)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Type", style="green", width=14)
    table.add_column("Size", justify="right", width=8)
    table.add_column("Tags", style="dim")

    for t in templates:
        size_str = f"{t.size_mb:.1f}MB" if t.size_mb >= 1 else f"{t.size_mb * 1024:.0f}KB"
        table.add_row(
            t.id,
            t.name,
            t.type,
            size_str,
            ", ".join(t.tags[:5]),
        )

    console.print(table)
    console.print(f"\n[dim]{len(templates)} templates[/dim]")


@template_group.command("scan")
def template_scan() -> None:
    """Scan 30_Templates/, update registry."""
    from corp_by_os.template_manager import save_registry, scan_templates

    cfg = get_config()
    console.print(f"[dim]Scanning {cfg.templates_root}...[/dim]")

    templates = scan_templates()
    if not templates:
        console.print("[yellow]No template files found.[/yellow]")
        return

    path = save_registry(templates)
    console.print(f"[green]Registered {len(templates)} templates[/green] -> {path}")

    # Show summary
    by_type: dict[str, int] = {}
    for t in templates:
        by_type[t.type] = by_type.get(t.type, 0) + 1
    for ttype, count in sorted(by_type.items()):
        console.print(f"  {ttype}: {count}")


@template_group.command("select")
@click.argument("goal")
def template_select(goal: str) -> None:
    """Show which template would be selected for a goal."""
    from corp_by_os.template_manager import load_registry, select_template

    templates = load_registry()
    if not templates:
        console.print("[yellow]No templates registered. Run `corp template scan` first.[/yellow]")
        return

    selected = select_template(goal, templates)
    if selected:
        console.print(f"[green]Selected:[/green] {selected.name}")
        console.print(f"  ID: {selected.id}")
        console.print(f"  Type: {selected.type}")
        console.print(f"  File: {selected.file}")
        console.print(f"  Tags: {', '.join(selected.tags)}")
        console.print(f"  Use cases: {', '.join(selected.use_cases)}")
    else:
        console.print("[yellow]No matching template found.[/yellow]")
