"""Retrieve and prep CLI commands."""

import logging
from pathlib import Path

import click
from rich.table import Table

from corp.cli._common import DASH, console
from corp.config import get_config
from corp.schema.folder_names import CORP_INFRA, PROJECTS


@click.command("retrieve")
@click.argument("query")
@click.option("--client", default=None, help="Filter by client name")
@click.option("--product", default=None, help="Filter by product")
@click.option("--top", default=10, type=int, help="Number of results")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (json for machine consumption)",
)
@click.option("--rfp-only", is_flag=True, help="Only return RFP-safe notes.")
@click.option("--verbose", is_flag=True, help="Show doc_type, quality, and score per result.")
def retrieve_cmd(
    query: str,
    client: str | None,
    product: str | None,
    top: int,
    output_format: str,
    rfp_only: bool,
    verbose: bool,
) -> None:
    """Search the knowledge base.

    Retrieves notes matching the query with optional metadata filters.

    Examples:

        corp retrieve "Platform Architecture"

        corp retrieve "WMS integration" --client Lenzing

        corp retrieve "demand planning" --format json
    """
    from corp.index_builder import get_index_path
    from corp.retrieve.engine import RetrievalFilter, retrieve

    cfg = get_config()
    filters = RetrievalFilter(
        client=client,
        products=[product] if product else None,
        rfp_only=rfp_only,
    )

    # Suppress logging for clean JSON stdout
    if output_format == "json":
        logging.getLogger().setLevel(logging.WARNING)

    result = retrieve(
        query=query,
        db_path=get_index_path(),
        vault_root=cfg.vault_path,
        filters=filters,
        top_n=top,
    )

    if output_format == "json":
        import json as json_mod

        output = {
            "query": result.query,
            "total_found": result.total_found,
            "sufficient": result.sufficient,
            "coverage_gaps": result.coverage_gaps,
            "notes": [
                {
                    "note_id": note.note_id,
                    "title": note.title,
                    "client": note.client,
                    "project_id": note.project_id,
                    "content": note.content,
                    "topics": note.topics,
                    "products": note.products,
                    "domains": note.domains,
                    "source_type": note.source_type,
                    "note_type": note.note_type,
                    "confidence": note.confidence,
                    "relevance_score": note.relevance_score,
                    "source_path": note.note_path,
                    "extracted_at": note.extracted_at,
                    "citation": note.citation,
                    "overlay_data": note.overlay_data,
                }
                for note in result.notes
            ],
        }
        click.echo(json_mod.dumps(output, indent=2, ensure_ascii=False))
        return

    if not result.notes:
        console.print(f"[yellow]No results for '{query}'[/yellow]")
        if result.coverage_gaps:
            for gap in result.coverage_gaps:
                console.print(f"  [dim]{gap}[/dim]")
        return

    table = Table(
        title=f"Knowledge: '{query}'" + (f" [client={client}]" if client else ""),
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="cyan", max_width=50)
    table.add_column("Client", max_width=15)
    table.add_column("Type", style="dim", max_width=12)
    table.add_column("Trust", style="dim", max_width=10)
    if verbose:
        table.add_column("DocType", style="dim", max_width=12)
        table.add_column("Score", style="dim", max_width=8)
    else:
        table.add_column("Topics", max_width=30)

    for i, note in enumerate(result.notes, 1):
        if verbose:
            table.add_row(
                str(i),
                note.title,
                note.client or DASH,
                note.source_type or DASH,
                note.confidence or DASH,
                note.note_type or DASH,
                f"{note.relevance_score:.1f}",
            )
        else:
            table.add_row(
                str(i),
                note.title,
                note.client or DASH,
                note.source_type or DASH,
                note.confidence or DASH,
                ", ".join(note.topics[:3]) or DASH,
            )

    console.print(table)
    console.print(
        f"\n  Found: {result.total_found} | "
        f"Shown: {len(result.notes)} | "
        f"Sufficient: {'Yes' if result.sufficient else 'No'}",
    )
    if result.coverage_gaps:
        console.print(f"  Gaps: {', '.join(result.coverage_gaps)}")


@click.command("prep")
@click.argument("client")
@click.option("--model", default="gemini-3-flash-preview", help="LLM model for synthesis")
@click.option(
    "--output", default=None, help="Output directory (default: project folder or 90_System)"
)
def prep_cmd(client: str, model: str, output: str | None) -> None:
    """Prepare a client briefing for an upcoming meeting.

    Retrieves all knowledge about the client and generates
    a structured briefing with key facts, talking points,
    and knowledge gaps.

    The briefing is saved as a markdown file.

    Examples:

        corp prep Lenzing

        corp prep SGDBF

        corp prep "Alfa Laval"
    """
    from corp.index_builder import get_index_path
    from corp.retrieve.prep import generate_prep

    cfg = get_config()

    if output:
        output_dir = Path(output)
    else:
        projects_dir = cfg.mywork_root / PROJECTS
        matching = (
            [
                d
                for d in projects_dir.iterdir()
                if d.is_dir() and client.lower().replace(" ", "_") in d.name.lower()
            ]
            if projects_dir.exists()
            else []
        )
        if matching:
            output_dir = matching[0] / "_corp_prep"
        else:
            output_dir = cfg.mywork_root / CORP_INFRA / "_corp_prep"

    console.print(f"[bold]Preparing briefing for: {client}[/bold]")
    console.print("Retrieving knowledge...")

    briefing = generate_prep(
        client=client,
        db_path=get_index_path(),
        vault_root=cfg.vault_path,
        output_dir=output_dir,
        model=model,
    )

    console.print("\n[bold green]Briefing generated![/bold green]")
    console.print(f"  Sources: {briefing.source_count} notes")
    console.print(f"  Cost: ${briefing.cost:.4f}")
    console.print(f"  Saved: {output_dir}")

    if briefing.coverage_gaps:
        console.print("\n[yellow]Knowledge gaps:[/yellow]")
        for gap in briefing.coverage_gaps:
            console.print(f"  • {gap}")

    if not briefing.retrieval.sufficient:
        console.print(
            f"\n[red]Warning: Limited knowledge about {client}. Briefing may be incomplete.[/red]",
        )
