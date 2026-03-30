"""Analytics CLI commands."""

import json
import sys

import click
from rich.panel import Panel
from rich.table import Table

from corp.cli._common import console
from corp.config import get_config
from corp.schema.pipeline_config import PipelineConfig


@click.group("analytics")
def analytics_group() -> None:
    """SQL analytics over the notes index. Run `corp index rebuild` first."""


@analytics_group.command("report")
def analytics_report_command() -> None:
    """Show cross-project analytics dashboard (facts + projects)."""
    from corp.index_builder import get_index_path
    from corp.query_engine import get_analytics

    if not get_index_path().exists():
        console.print("[yellow]No index. Run `corp index rebuild` first.[/yellow]")
        sys.exit(1)

    report = get_analytics()

    # Write dashboard
    from corp.built_in_actions import _write_analytics_dashboard

    _write_analytics_dashboard(report)

    console.print(
        Panel(
            f"[bold]{report.total_projects}[/bold] projects, "
            f"[bold]{report.total_facts}[/bold] facts indexed\n"
            f"Avg facts/project: {report.avg_facts_per_project}",
            title="Cross-Project Analytics",
            border_style="blue",
        )
    )

    if report.top_topics:
        table = Table(title="Top Topics", show_lines=False)
        table.add_column("Topic", style="cyan")
        table.add_column("Facts", justify="right")
        for topic, count in report.top_topics[:10]:
            table.add_row(topic, str(count))
        console.print(table)

    if report.top_products:
        table = Table(title="Top Products", show_lines=False)
        table.add_column("Product", style="cyan")
        table.add_column("Projects", justify="right")
        for product, count in report.top_products[:10]:
            table.add_row(product, str(count))
        console.print(table)

    if report.product_bundles:
        table = Table(title="Common Bundles", show_lines=False)
        table.add_column("Bundle", style="cyan")
        table.add_column("Count", justify="right")
        for bundle, count in report.product_bundles[:5]:
            table.add_row(bundle, str(count))
        console.print(table)

    if report.projects_by_status:
        table = Table(title="Projects by Status", show_lines=False)
        table.add_column("Status", style="cyan")
        table.add_column("Count", justify="right")
        for status, count in sorted(report.projects_by_status.items()):
            table.add_row(status, str(count))
        console.print(table)

    cfg = get_config()
    dashboard = cfg.vault_path / "00_dashboards" / "analytics.md"
    console.print(f"\n[dim]Dashboard: {dashboard}[/dim]")


@analytics_group.command("products")
@click.option("--client", required=True, help="Client name (exact match)")
def analytics_products(client: str) -> None:
    """Q1: Distinct products mentioned in notes for a client."""
    from corp.index_builder import get_index_path
    from corp.query_engine import notes_products_for_client

    if not get_index_path().exists():
        console.print("[yellow]No index. Run `corp index rebuild` first.[/yellow]")
        sys.exit(1)

    products = notes_products_for_client(client)
    if not products:
        console.print(f"[yellow]No products found for client '{client}'.[/yellow]")
        return

    table = Table(title=f"Products — {client}", show_lines=False)
    table.add_column("Product", style="cyan")
    for p in products:
        table.add_row(p)
    console.print(table)
    console.print(f"[dim]{len(products)} distinct products[/dim]")


@analytics_group.command("timeline")
@click.option("--client", required=True, help="Client name (exact match)")
def analytics_timeline(client: str) -> None:
    """Q2: Notes for a client ordered by date."""
    from corp.index_builder import get_index_path
    from corp.query_engine import notes_timeline_for_client

    if not get_index_path().exists():
        console.print("[yellow]No index. Run `corp index rebuild` first.[/yellow]")
        sys.exit(1)

    notes = notes_timeline_for_client(client)
    if not notes:
        console.print(f"[yellow]No dated notes found for client '{client}'.[/yellow]")
        return

    table = Table(title=f"Timeline — {client}", show_lines=False)
    table.add_column("Date", style="green", width=12)
    table.add_column("Title", style="white")
    table.add_column("Products", style="cyan")
    table.add_column("Type", style="dim", width=14)
    for n in notes:
        table.add_row(n["date"], n["title"], n["products"], n["doc_type"] or n["type"])
    console.print(table)
    console.print(f"[dim]{len(notes)} notes[/dim]")


@analytics_group.command("clients")
@click.option("--product", required=True, help="Product name (substring match)")
def analytics_clients(product: str) -> None:
    """Q3: Distinct clients whose notes mention a product."""
    from corp.index_builder import get_index_path
    from corp.query_engine import notes_clients_for_product

    if not get_index_path().exists():
        console.print("[yellow]No index. Run `corp index rebuild` first.[/yellow]")
        sys.exit(1)

    clients = notes_clients_for_product(product)
    if not clients:
        console.print(f"[yellow]No clients found with product '{product}'.[/yellow]")
        return

    table = Table(title=f"Clients with '{product}'", show_lines=False)
    table.add_column("Client", style="cyan")
    for c in clients:
        table.add_row(c)
    console.print(table)
    console.print(f"[dim]{len(clients)} clients[/dim]")


@analytics_group.command("overlap")
@click.option("--product", required=True, help="Product name (substring match)")
def analytics_overlap(product: str) -> None:
    """Q6: Clients sharing interest in a product, with note counts."""
    from corp.index_builder import get_index_path
    from corp.query_engine import notes_overlap_for_product

    if not get_index_path().exists():
        console.print("[yellow]No index. Run `corp index rebuild` first.[/yellow]")
        sys.exit(1)

    rows = notes_overlap_for_product(product)
    if not rows:
        console.print(f"[yellow]No overlap data found for product '{product}'.[/yellow]")
        return

    table = Table(title=f"Client Overlap — '{product}'", show_lines=False)
    table.add_column("Client", style="cyan")
    table.add_column("Notes", justify="right")
    for client, cnt in rows:
        table.add_row(client, str(cnt))
    console.print(table)
    console.print(f"[dim]{len(rows)} clients share interest in '{product}'[/dim]")


@analytics_group.command("compare")
@click.option("--clients", required=True, help="Comma-separated client names")
def analytics_compare(clients: str) -> None:
    """Q9: Side-by-side product sets for multiple clients."""
    from corp.index_builder import get_index_path
    from corp.query_engine import notes_compare_clients

    if not get_index_path().exists():
        console.print("[yellow]No index. Run `corp index rebuild` first.[/yellow]")
        sys.exit(1)

    client_list = [c.strip() for c in clients.split(",") if c.strip()]
    if len(client_list) < 2:
        console.print("[red]Provide at least 2 comma-separated client names.[/red]")
        sys.exit(1)

    comparison = notes_compare_clients(client_list)

    # Find all products across all clients
    all_products: set[str] = set()
    for prods in comparison.values():
        all_products.update(prods)
    all_products_sorted = sorted(all_products)

    table = Table(title="Client Product Comparison", show_lines=True)
    table.add_column("Product", style="cyan")
    for c in client_list:
        table.add_column(c, justify="center")

    for product in all_products_sorted:
        row = [product]
        for c in client_list:
            row.append("Y" if product in comparison[c] else "-")
        table.add_row(*row)

    console.print(table)
    console.print(
        f"[dim]{len(all_products_sorted)} distinct products across {len(client_list)} clients[/dim]"
    )


@analytics_group.command("recent")
def analytics_recent() -> None:
    """Q10: Most recent note per client."""
    from corp.index_builder import get_index_path
    from corp.query_engine import notes_recent

    if not get_index_path().exists():
        console.print("[yellow]No index. Run `corp index rebuild` first.[/yellow]")
        sys.exit(1)

    rows = notes_recent()
    if not rows:
        console.print("[yellow]No dated notes found in index.[/yellow]")
        return

    table = Table(title="Most Recent Note per Client", show_lines=False)
    table.add_column("Date", style="green", width=12)
    table.add_column("Client", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Products", style="dim")
    for r in rows:
        table.add_row(r["date"], r["client"], r["title"], r["products"])
    console.print(table)
    console.print(f"[dim]{len(rows)} clients[/dim]")


@click.command("dedup-report")
@click.option(
    "--threshold",
    default=0.6,
    show_default=True,
    type=float,
    help="Minimum Jaccard similarity to report (0–1).",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json"]),
    default="table",
    show_default=True,
)
@click.pass_obj
def dedup_report_command(obj: dict, threshold: float, fmt: str) -> None:
    """Show near-duplicate file pairs detected by MinHash.

    Reads content_signatures stored in ops.db and surfaces candidate
    pairs above the similarity threshold for human review.
    No files are deleted — this is a report only.
    """
    try:
        from corp.ingest.dedup import get_dedup_report
    except ImportError:
        console.print('[red]datasketch not installed.[/red] Run: pip install "corp[dedup]"')
        return

    from corp.ops.database import OpsDB

    config = (obj or {}).get("config") or PipelineConfig.production()
    db = OpsDB(config=config)
    try:
        pairs = get_dedup_report(db, threshold=threshold)
    except Exception as exc:
        console.print(f"[red]Error generating dedup report:[/red] {exc}")
        db.close()
        return
    finally:
        db.close()

    if fmt == "json":
        data = [
            {
                "path_a": p.path_a,
                "filename_a": p.filename_a,
                "path_b": p.path_b,
                "filename_b": p.filename_b,
                "similarity": p.similarity,
            }
            for p in pairs
        ]
        console.print_json(json.dumps(data))
        return

    if not pairs:
        console.print(
            f"[green]No near-duplicate pairs found[/green] "
            f"(threshold={threshold}, {_count_signatures(config)} signatures stored)."
        )
        return

    table = Table(
        title=f"Near-Duplicate Pairs  (threshold={threshold})",
        show_lines=True,
    )
    table.add_column("File A", style="cyan", no_wrap=False, max_width=50)
    table.add_column("File B", style="cyan", no_wrap=False, max_width=50)
    table.add_column("Sim", justify="right", width=6)

    for pair in pairs:
        sim_style = "red bold" if pair.similarity >= 0.9 else "yellow"
        table.add_row(
            pair.filename_a,
            pair.filename_b,
            f"[{sim_style}]{pair.similarity:.3f}[/{sim_style}]",
        )

    console.print(table)
    console.print(
        f"\n[dim]{len(pairs)} candidate pair(s). Review and decide — no auto-deletion.[/dim]"
    )


def _count_signatures(config) -> int:
    """Return number of stored content signatures (fail-open → 0)."""
    from corp.ops.database import OpsDB

    db = OpsDB(config=config)
    try:
        return db.conn.execute("SELECT COUNT(*) FROM content_signatures").fetchone()[0]
    except Exception:
        return 0
    finally:
        db.close()


@click.command("files-stats")
@click.pass_obj
def files_stats_command(obj: dict) -> None:
    """Show file registry statistics."""
    from corp.ops.database import OpsDB

    config = (obj or {}).get("config") or PipelineConfig.production()
    ops = OpsDB(config=config)
    conn = ops.conn

    total_files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    total_extractions = conn.execute("SELECT COUNT(*) FROM extractions").fetchone()[0]
    extracted = conn.execute("SELECT COUNT(DISTINCT file_id) FROM extractions").fetchone()[0]
    never_extracted = total_files - extracted
    total_cost = conn.execute("SELECT COALESCE(SUM(cost_cents), 0) FROM extractions").fetchone()[0]

    table = Table(title="File Registry")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Files known", str(total_files))
    table.add_row("Extracted", str(extracted))
    table.add_row("Never extracted", str(never_extracted))
    table.add_row(
        "Total extractions",
        f"{total_extractions}  [dim](including re-extractions)[/dim]",
    )
    table.add_row("Total cost", f"${total_cost / 100:.2f}")

    console.print(table)
    ops.close()


@click.command("naming-stats")
@click.pass_obj
def naming_stats_command(obj: dict) -> None:
    """Show naming convention type code distribution from routing feedback."""
    from collections import Counter

    from corp.ops.database import OpsDB
    from corp.schema.naming_config import get_type_code, load_naming_config

    pipeline_config = (obj or {}).get("config") or PipelineConfig.production()
    ops = OpsDB(config=pipeline_config)
    rows = ops.conn.execute(
        "SELECT filename FROM routing_feedback ORDER BY timestamp DESC"
    ).fetchall()

    if not rows:
        console.print("[dim]No routing feedback yet.[/dim]")
        ops.close()
        return

    type_counts: Counter = Counter()
    for (filename,) in rows:
        code = get_type_code(filename=filename)
        type_counts[code] += 1

    total = sum(type_counts.values())
    config = load_naming_config()
    threshold = config["fallback"]["misc_review_threshold"]

    table = Table(title=f"Naming Convention Stats ({total} files)")
    table.add_column("Type Code", style="bold")
    table.add_column("Label")
    table.add_column("Count", justify="right")
    table.add_column("%", justify="right")

    for code, count in type_counts.most_common():
        pct = count / total * 100
        label = config["type_codes"].get(code, {}).get("label", "")
        style = "red bold" if code == "MISC" and pct > threshold * 100 else ""
        table.add_row(code, label, str(count), f"{pct:.0f}%", style=style)

    console.print(table)

    misc_count = type_counts.get("MISC", 0)
    misc_rate = misc_count / total if total else 0
    if misc_rate > threshold:
        console.print(
            f"\n[yellow]Warning:[/yellow] MISC rate is {misc_rate:.0%} "
            f"(threshold: {threshold:.0%}). Review unclassified files."
        )

    ops.close()
