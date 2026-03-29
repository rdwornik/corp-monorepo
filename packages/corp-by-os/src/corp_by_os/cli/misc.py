"""Miscellaneous CLI commands: chat and test-pipeline."""

import sys
from pathlib import Path

import click
from corp_by_os.cli._common import console
from corp_os_meta.pipeline_config import PipelineConfig


@click.command("test-pipeline")
@click.option("--live", is_flag=True, help="Use real CKE API calls (costs money)")
@click.option(
    "--record",
    is_flag=True,
    help="Record live CKE responses as reusable fixture JSONs (implies --live)",
)
@click.option("--keep-sandbox", is_flag=True, help="Keep sandbox directory after run")
@click.option("--verbose", "-v", is_flag=True, help="Enable DEBUG logging during test")
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(dir_okay=False),
    help="Save JSON report to file",
)
@click.pass_obj
def test_pipeline_command(
    obj: dict,
    live: bool,
    record: bool,
    keep_sandbox: bool,
    verbose: bool,
    output: str | None,
) -> None:
    """Run an end-to-end pipeline smoke test in an isolated sandbox.

    Exercises all key pipeline stages (sandbox init, classify/rename, vault
    ingest, index rebuild, retrieve) without touching production data.

    Fixture mode (default): no API calls, runs in ~2s.
      If recorded fixtures exist they are replayed instead of mock notes.
    Live mode (--live): invokes real CKE extraction (costs money).
    Record mode (--record): live mode + saves responses as fixture JSONs.
      Run once to refresh fixtures when CKE models change.

    Examples:

    \b
        corp test-pipeline
        corp test-pipeline --verbose
        corp test-pipeline --live --keep-sandbox
        corp test-pipeline --record
        corp test-pipeline --output report.json
    """
    import json as _json
    from dataclasses import asdict

    from corp_by_os.test_pipeline import format_report, run_pipeline_test

    config = (obj or {}).get("config") or PipelineConfig.production()

    # --record implies --live
    effective_live = live or record

    console.print("[bold cyan]Running pipeline smoke test...[/bold cyan]")
    if record:
        console.print("[bold yellow]Record mode: making real API calls...[/bold yellow]")

    report = run_pipeline_test(
        config=config,
        fixture_mode=not effective_live,
        verbose=verbose,
        keep_sandbox=keep_sandbox,
        record=record,
    )

    format_report(report)

    if record:
        console.print(
            f"Recorded {report.recorded_fixtures} fixtures, total cost ${report.recording_cost:.2f}"
        )

    if output:
        out_path = Path(output)
        report_dict = asdict(report)
        # Path objects not JSON-serialisable — convert to str
        if report_dict.get("sandbox_path") is not None:
            report_dict["sandbox_path"] = str(report_dict["sandbox_path"])
        out_path.write_text(_json.dumps(report_dict, indent=2), encoding="utf-8")
        console.print(f"[dim]Report saved to {out_path}[/dim]")

    sys.exit(0 if report.all_passed else 1)


@click.command("chat")
@click.option("--no-llm", is_flag=True, help="Keyword matching only, no Gemini calls")
def chat_command(no_llm: bool) -> None:
    """Interactive chat — natural language workflow routing."""
    from corp_by_os.chat import chat_loop

    chat_loop(use_llm=not no_llm)
