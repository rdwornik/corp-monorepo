"""Cleanup and audit CLI commands."""

import json
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.panel import Panel
from rich.table import Table

from corp.cli._common import console
from corp.config import get_config


@click.command("cleanup-scan")
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(),
    help="Output path for moves.yaml (default: .corp/moves.yaml)",
)
def cleanup_scan_command(output: str | None) -> None:
    """Scan MyWork for misplaced files and generate move proposals."""
    from corp.cleanup.classifier import classify_batch as cleanup_classify
    from corp.cleanup.proposer import generate_proposals
    from corp.cleanup.scanner import scan_problematic_files

    cfg = get_config()
    mywork_root = cfg.mywork_root

    console.print(f"[dim]Scanning {mywork_root}...[/dim]")
    files = scan_problematic_files(mywork_root)

    if not files:
        console.print("[green]No problematic files found.[/green]")
        return

    console.print(f"Found [bold]{len(files)}[/bold] files to classify")

    # Classify with Gemini
    console.print("[dim]Classifying files with Gemini...[/dim]")
    classifications = cleanup_classify(files)

    # Generate proposals
    output_path = Path(output) if output else mywork_root / "90_System" / ".corp" / "moves.yaml"
    generate_proposals(classifications, output_path)

    # Summary
    moves = sum(1 for c in classifications if c.action == "move")
    deletes = sum(1 for c in classifications if c.action == "delete")
    keeps = sum(1 for c in classifications if c.action == "keep")

    console.print(
        Panel(
            f"Move: {moves}  |  Delete: {deletes}  |  Keep: {keeps}\n\n"
            f"Review: {output_path}\n"
            "Set [bold]approved: true[/bold] on entries to execute, then run:\n"
            "  [cyan]corp apply-moves[/cyan]",
            title="Cleanup Proposals",
            border_style="blue",
        )
    )


@click.command("apply-moves")
@click.argument("moves_file", required=False, default=None, type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Preview without executing")
def apply_moves_command(moves_file: str | None, dry_run: bool) -> None:
    """Execute approved moves from moves.yaml."""
    from corp.cleanup.executor import execute_moves

    cfg = get_config()
    mywork_root = cfg.mywork_root

    if moves_file:
        moves_path = Path(moves_file)
    else:
        moves_path = mywork_root / "90_System" / ".corp" / "moves.yaml"

    if not moves_path.exists():
        console.print(f"[red]Moves file not found: {moves_path}[/red]")
        console.print("[dim]Run `corp cleanup-scan` first.[/dim]")
        sys.exit(1)

    if dry_run:
        console.print("[yellow]Dry run — previewing only:[/yellow]")

    result = execute_moves(moves_path, mywork_root, dry_run=dry_run)

    console.print(
        Panel(
            f"Moved: {result.moved}  |  Deleted: {result.deleted}  |  "
            f"Skipped: {result.skipped}  |  Failed: {result.failed}",
            title="Execution Result",
            border_style="green" if result.failed == 0 else "red",
        )
    )


@click.command("cleanup")
@click.option(
    "--scope",
    type=click.Choice(["duplicates", "overlap", "artifacts", "all"]),
    default="all",
    help="What to clean up",
)
@click.option("--execute", is_flag=True, help="Actually delete (default is plan-only)")
def cleanup_cmd(scope: str, execute: bool) -> None:
    """Analyze and clean up disk space.

    Default: produces a cleanup plan for review.
    With --execute: carries out approved deletions.

    Examples:

        corp cleanup                              # Full analysis, plan only

        corp cleanup --scope duplicates           # Just find duplicates

        corp cleanup --scope artifacts --execute  # Clean extraction artifacts
    """
    from corp.cleanup.disk import (
        APPDATA_GUIDANCE,
        PAGEFILE_GUIDANCE,
        CleanupPlan,
        execute_plan,
        find_duplicates,
        find_extraction_artifacts,
        find_onedrive_overlap,
        find_staging_artifacts,
    )

    cfg = get_config()
    plans: list[tuple[str, CleanupPlan]] = []

    if scope in ("overlap", "all"):
        console.print("[bold]Scanning OneDrive overlap...[/bold]")
        overlap = find_onedrive_overlap(cfg.mywork_root)
        if overlap.total_files > 0:
            plans.append(("OneDrive Overlap", overlap))

    if scope in ("duplicates", "all"):
        console.print("[bold]Scanning for duplicates...[/bold]")
        dupes = find_duplicates(cfg.mywork_root)
        if dupes.total_files > 0:
            plans.append(("Duplicates", dupes))

    if scope in ("artifacts", "all"):
        console.print("[bold]Scanning extraction artifacts...[/bold]")
        artifacts = find_extraction_artifacts(cfg.mywork_root)
        if artifacts.total_files > 0:
            plans.append(("CKE Artifacts", artifacts))

        staging = find_staging_artifacts(cfg.app_data_path)
        if staging.total_files > 0:
            plans.append(("Staging Artifacts", staging))

    if not plans:
        console.print("[green]No cleanup opportunities found.[/green]")
        if scope == "all":
            console.print(f"\n{APPDATA_GUIDANCE}")
            console.print(f"\n{PAGEFILE_GUIDANCE}")
        return

    # Display findings
    grand_total_bytes = 0
    grand_total_files = 0

    for label, plan in plans:
        table = Table(title=f"{label} ({plan.total_files} files, {plan.total_mb:.1f} MB)")
        table.add_column("File", style="cyan", max_width=50)
        table.add_column("Size", justify="right", width=10)
        table.add_column("Reason", style="dim", max_width=45)

        # Show first 20 items, summarize the rest
        for item in plan.items[:20]:
            size_str = f"{item.size_bytes / 1024 / 1024:.1f} MB"
            table.add_row(item.filename, size_str, item.reason)
        if len(plan.items) > 20:
            table.add_row(
                f"... and {len(plan.items) - 20} more",
                "",
                "",
            )

        console.print(table)
        grand_total_bytes += plan.total_bytes
        grand_total_files += plan.total_files

    grand_mb = grand_total_bytes / 1024 / 1024
    grand_gb = grand_total_bytes / 1024**3

    console.print(
        f"\n[bold]Total reclaimable: {grand_total_files} files, "
        f"{grand_mb:.0f} MB ({grand_gb:.1f} GB)[/bold]",
    )

    if execute:
        console.print("\n[yellow]Executing cleanup...[/yellow]")
        log_path = cfg.mywork_root / "90_System" / "cleanup_log.jsonl"
        total_deleted = 0
        total_failed = 0

        for label, plan in plans:
            deleted, failed = execute_plan(plan, log_path, dry_run=False)
            total_deleted += deleted
            total_failed += failed
            console.print(
                f"  {label}: {deleted} deleted, {failed} failed",
            )

        console.print(
            f"\n[bold]Done: {total_deleted} deleted, {total_failed} failed[/bold]",
        )
        console.print(f"  Log: {log_path}")
    else:
        console.print(
            "\n[dim]This is a plan only. Run with --execute to carry out deletions.[/dim]",
        )

    if scope == "all":
        console.print(f"\n{APPDATA_GUIDANCE}")
        console.print(f"\n{PAGEFILE_GUIDANCE}")


@click.command("audit")
@click.option(
    "--skip-gemini",
    is_flag=True,
    help="Skip Gemini analysis, scan + coverage only",
)
@click.option(
    "--budget",
    default=0.30,
    type=float,
    help="Max Gemini spend in USD (default $0.30)",
)
@click.option(
    "--model",
    default="gemini-3-flash-preview",
    type=str,
    help="Gemini model for analysis",
)
def audit_command(skip_gemini: bool, budget: float, model: str) -> None:
    """Full read-only audit of MyWork — scan, analyze, report."""

    from corp.audit import (
        ANALYSIS_FOLDERS,
        analyze_folder,
        build_report,
        check_vault_coverage,
        scan_mywork,
    )

    cfg = get_config()
    mywork_root = cfg.mywork_root
    system_dir = mywork_root / "90_System"
    system_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Scan ---
    console.print("[bold]Step 1: Scanning MyWork...[/bold]")
    all_files = scan_mywork(mywork_root)
    console.print(f"  Scanned [bold]{len(all_files)}[/bold] files")

    total_gb = sum(f["size_bytes"] for f in all_files) / (1024**3)
    console.print(f"  Total size: {total_gb:.2f} GB")

    # Save raw scan
    scan_path = system_dir / "full_scan.json"
    with open(scan_path, "w", encoding="utf-8") as fh:
        json.dump(all_files, fh, indent=2, ensure_ascii=False)
    console.print(f"  Raw scan: {scan_path}")

    # Per-folder summary
    from collections import Counter as _Counter

    folder_counts = _Counter(f["folder_l1"] for f in all_files)
    for folder, count in folder_counts.most_common():
        size = sum(f["size_mb"] for f in all_files if f["folder_l1"] == folder)
        console.print(f"    {folder}: {count} files ({size:.0f} MB)")

    # --- Step 2: Gemini analysis ---
    analyses: list[dict] = []
    gemini_responses: list[dict] = []

    if skip_gemini:
        console.print("\n[yellow]Step 2: Gemini analysis skipped (--skip-gemini)[/yellow]")
    else:
        console.print(
            f"\n[bold]Step 2: Gemini analysis (budget=${budget:.2f}, model={model})...[/bold]"
        )

        try:
            from corp.audit import _get_gemini_client

            client = _get_gemini_client()
        except RuntimeError as exc:
            console.print(f"  [red]Cannot init Gemini: {exc}[/red]")
            console.print(
                "  [dim]Continuing without analysis. Use --skip-gemini to suppress.[/dim]"
            )
            skip_gemini = True
            client = None

        if not skip_gemini:
            # Group files by L1 folder
            by_folder: dict[str, list[dict]] = {}
            for f in all_files:
                l1 = f["folder_l1"]
                if l1 not in by_folder:
                    by_folder[l1] = []
                by_folder[l1].append(f)

            for folder_name in ANALYSIS_FOLDERS:
                files = by_folder.get(folder_name, [])
                if not files:
                    continue

                console.print(f"  Analyzing {folder_name} ({len(files)} files)...")
                result = analyze_folder(folder_name, files, client, model)
                analyses.append(result)
                gemini_responses.append(
                    {
                        "folder": folder_name,
                        "raw_response": result.get("raw_response"),
                        "error": result.get("error"),
                    }
                )

                if result["analysis"]:
                    score = result["analysis"].get("structure_score", "?")
                    console.print(f"    Structure: {score}")
                    items = result["analysis"].get("action_items", [])
                    if items:
                        console.print(f"    Action items: {len(items)}")
                elif result["error"]:
                    console.print(f"    [red]Error: {result['error']}[/red]")

            # Save raw Gemini responses
            responses_path = system_dir / "mywork_audit_gemini_responses.json"
            with open(responses_path, "w", encoding="utf-8") as fh:
                json.dump(gemini_responses, fh, indent=2, ensure_ascii=False)
            console.print(f"\n  Gemini responses: {responses_path}")

    # --- Step 3: Vault coverage ---
    console.print("\n[bold]Step 3: Vault coverage check...[/bold]")
    coverage = check_vault_coverage(all_files, cfg.vault_path)
    console.print(f"  Vault notes found: {coverage['total_vault_notes']}")
    console.print(f"  Files with extraction: {coverage['extracted_count']}")
    console.print(f"  Files without extraction: {coverage['not_extracted_count']}")

    if coverage.get("by_folder"):
        console.print("  Coverage by folder:")
        for folder, counts in sorted(coverage["by_folder"].items()):
            ext = counts.get("extracted", 0)
            not_ext = counts.get("not_extracted", 0)
            pct = (ext / (ext + not_ext) * 100) if (ext + not_ext) > 0 else 0
            console.print(f"    {folder}: {ext}/{ext + not_ext} ({pct:.0f}%)")

    # --- Step 4: Build report ---
    console.print("\n[bold]Step 4: Building report...[/bold]")
    report = build_report(all_files, analyses, coverage)

    date_str = datetime.now().strftime("%Y%m%d")
    report_path = system_dir / f"mywork_audit_{date_str}.json"
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False, default=str)

    console.print(f"  Report: {report_path}")
    console.print(
        f"\n[green]Audit complete: {report['total_files']} files, "
        f"{report['total_size_gb']} GB, "
        f"{len(report.get('media_inventory', []))} media files, "
        f"{len(report.get('duplicate_candidates', []))} duplicate groups[/green]"
    )
