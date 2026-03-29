"""RFP CLI commands."""

import click

from corp.cli._common import console
from corp.config import get_config


@click.group("rfp")
def rfp_group():
    """RFP response tools."""


@rfp_group.command("answer")
@click.argument("question")
@click.option("--client", default=None, help="Client context for tailored answer")
@click.option("--product", default=None, help="Filter by product area")
@click.option("--model", default="gemini-3-flash-preview", help="LLM model")
def rfp_answer_cmd(
    question: str,
    client: str | None,
    product: str | None,
    model: str,
) -> None:
    """Draft an RFP answer using the knowledge base.

    Searches all extracted knowledge for relevant information
    and generates a professional RFP response with citations.

    Examples:

        corp rfp answer "Describe your SaaS deployment model"

        corp rfp answer "How does data integration work?" --client Lenzing

        corp rfp answer "What AI/ML capabilities?" --product "Cognitive Demand Planning"
    """
    from corp.index_builder import get_index_path
    from corp.retrieve.rfp import answer_rfp

    cfg = get_config()

    console.print(f"[bold]RFP Question:[/bold] {question}")
    console.print("Searching knowledge base...")

    result = answer_rfp(
        question=question,
        db_path=get_index_path(),
        vault_root=cfg.vault_path,
        client=client,
        product=product,
        model=model,
    )

    conf_style = {
        "high": "green",
        "medium": "yellow",
        "low": "red",
        "insufficient": "red bold",
    }.get(result.confidence, "")

    console.print(
        f"\n[{conf_style}]Confidence: {result.confidence.upper()}"
        f"[/{conf_style}] ({result.source_count} sources)",
    )
    console.print(f"Cost: ${result.cost:.4f}")

    console.print("\n" + "-" * 60)
    console.print(result.answer_text)
    console.print("-" * 60)

    if result.coverage_gaps:
        console.print("\n[yellow]Knowledge gaps:[/yellow]")
        for gap in result.coverage_gaps:
            console.print(f"  - {gap}")

    if result.confidence == "insufficient":
        console.print("\n[red]Not enough knowledge to answer this question.[/red]")
        console.print("Consider ingesting relevant documents first (corp ingest).")
