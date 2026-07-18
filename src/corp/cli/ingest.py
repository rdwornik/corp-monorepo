"""Ingest, finalize, classify, freshness, and ingest-extractions CLI commands."""

from pathlib import Path

import click
from rich.table import Table

from corp.cli._common import CHECK, DASH, console
from corp.config import get_config
from corp.schema.folder_names import INBOX, UNMATCHED
from corp.schema.pipeline_config import PipelineConfig


@click.command("ingest")
@click.argument("path", required=False, default=None, type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Match and report without moving files")
@click.option("--no-extract", is_flag=True, help="Route only, skip CKE extraction")
@click.pass_obj
def ingest_command(
    obj: dict,
    path: str | None,
    dry_run: bool,
    no_extract: bool,
) -> None:
    """Route incoming files and folders to their destinations via content registry.

    Without PATH, scans entire 00_Inbox (files + folders).
    With PATH, ingests a specific file or directory of files.
    """
    from corp.ingest.router import (
        IngestResult,
        PackageIngestResult,
        ingest_all,
        ingest_file,
        ingest_folder,
    )
    from corp.ops.database import OpsDB
    from corp.ops.registry import get_content_registry

    config = (obj or {}).get("config") or PipelineConfig.production()
    cfg = get_config()
    ops = OpsDB(config=config)
    registry = get_content_registry()

    extract = not no_extract

    if dry_run:
        console.print("[yellow]Dry run — no files will be moved or extracted.[/yellow]")

    file_results: list[IngestResult] = []
    package_results: list[PackageIngestResult] = []

    if path:
        target = Path(path).resolve()
        if target.is_file():
            result = ingest_file(
                target,
                cfg.mywork_root,
                ops,
                registry,
                extract=extract,
                dry_run=dry_run,
            )
            file_results.append(result)
        elif target.is_dir():
            # Explicit directory path → ingest as folder package
            pkg_result = ingest_folder(
                target,
                cfg.mywork_root,
                ops,
                registry,
                extract=extract,
                dry_run=dry_run,
            )
            package_results.append(pkg_result)
    else:
        file_results, package_results = ingest_all(
            cfg.mywork_root,
            ops,
            registry,
            extract=extract,
            dry_run=dry_run,
        )

    if not file_results and not package_results:
        console.print("[yellow]No files to process.[/yellow]")
        ops.close()
        return

    action_styles = {
        "routed": "green",
        "staged": "yellow",
        "quarantined": "red",
        "skipped": "dim",
        "error": "bold red",
    }

    # Package results table
    if package_results:
        pkg_table = Table(
            title="Package Results" + (" (DRY RUN)" if dry_run else ""),
            show_lines=False,
        )
        pkg_table.add_column("Folder", style="cyan", max_width=35)
        pkg_table.add_column("Action", style="bold")
        pkg_table.add_column("Destination", max_width=45)
        pkg_table.add_column("Match", style="dim")
        pkg_table.add_column("Conf", justify="right")
        pkg_table.add_column("Files", justify="right")
        pkg_table.add_column("Size", justify="right")
        pkg_table.add_column("Extracted", justify="center")

        for r in package_results:
            style = action_styles.get(r.action, "white")
            match_info = r.match_method
            if r.match_series:
                match_info += f"/{r.match_series}"
            pkg_table.add_row(
                r.folder_name,
                f"[{style}]{r.action}[/{style}]",
                r.destination_path or DASH,
                match_info,
                f"{r.confidence:.0%}" if r.confidence > 0 else DASH,
                str(r.file_count),
                f"{r.total_size_mb:.1f}MB",
                CHECK if r.extracted else DASH,
            )

        console.print(pkg_table)

    # File results table
    if file_results:
        table = Table(
            title="File Results" + (" (DRY RUN)" if dry_run else ""),
            show_lines=False,
        )
        table.add_column("File", style="cyan", no_wrap=True, max_width=40)
        table.add_column("Action", style="bold")
        table.add_column("Method", style="dim")
        table.add_column("Conf", justify="right")
        table.add_column("Destination", style="dim", max_width=50)
        table.add_column("Extracted", justify="center")

        for r in file_results:
            style = action_styles.get(r.action, "white")
            table.add_row(
                r.filename,
                f"[{style}]{r.action}[/{style}]",
                r.match_method,
                f"{r.confidence:.0%}" if r.confidence > 0 else DASH,
                r.destination_path or DASH,
                CHECK if r.extracted else DASH,
            )

        console.print(table)

    # Summary
    actions: dict[str, int] = {}
    total_cost = 0.0
    all_errors: list[str] = []
    total_items = len(file_results) + len(package_results)

    for r in file_results:
        actions[r.action] = actions.get(r.action, 0) + 1
        total_cost += r.extraction_cost
        if r.error:
            all_errors.append(f"{r.filename}: {r.error}")

    for r in package_results:
        actions[r.action] = actions.get(r.action, 0) + 1
        total_cost += r.extraction_cost
        if r.error:
            all_errors.append(f"{r.folder_name}: {r.error}")

    summary_parts = [f"Total: {total_items}"]
    if package_results:
        summary_parts.append(f"packages: {len(package_results)}")
    for action, count in sorted(actions.items()):
        summary_parts.append(f"{action}: {count}")
    if total_cost > 0:
        summary_parts.append(f"cost: ${total_cost:.4f}")

    console.print(f"\n[bold]{' | '.join(summary_parts)}[/bold]")

    if all_errors:
        console.print(f"\n[red]{len(all_errors)} error(s):[/red]")
        for err in all_errors:
            console.print(f"  {err}")

    ops.close()


@click.command("ingest-inbox")
@click.option(
    "--path",
    type=click.Path(exists=True),
    default=None,
    help="Process a specific file instead of scanning Inbox.",
)
@click.option("--dry-run", is_flag=True, help="Show what would happen without moving files.")
@click.option("--auto", is_flag=True, help="Auto-accept high-confidence matches (>=0.90).")
@click.option("--undo", type=int, default=None, help="Undo a previous ingest by event ID.")
@click.option(
    "--full", is_flag=True, help="With --undo: also remove vault package and rebuild index."
)
@click.option("--skip-extract", is_flag=True, help="Route file but skip CKE extraction.")
@click.option("--list", "list_events", is_flag=True, help="Show ingest history.")
@click.option("--list-all", is_flag=True, help="Show all ingest history (no limit).")
@click.option(
    "--destination",
    type=str,
    default=None,
    help="Default destination for all files (e.g. 10_Projects/JLR).",
)
@click.pass_obj
def ingest_inbox_command(
    obj: dict,
    path: str | None,
    dry_run: bool,
    auto: bool,
    undo: int | None,
    full: bool,
    skip_extract: bool,
    list_events: bool,
    list_all: bool,
    destination: str | None,
) -> None:
    """Interactively route files from 00_Inbox to their canonical locations.

    Processes one file at a time with Rich UI: classify, confirm
    destination, rename, move, then trigger CKE extraction.
    """
    from corp.ingest.inbox import (
        _list_events,
        _scan_inbox_files,
        _undo_event,
        process_file,
    )
    from corp.ops.database import OpsDB
    from corp.ops.registry import get_content_registry

    config = (obj or {}).get("config") or PipelineConfig.production()
    cfg = get_config()
    ops = OpsDB(config=config)

    # List mode
    if list_events or list_all:
        _list_events(ops, limit=999999 if list_all else 20)
        ops.close()
        return

    # Undo mode
    if undo is not None:
        _undo_event(undo, ops, cfg.mywork_root, full=full)
        ops.close()
        return

    registry = get_content_registry()

    if dry_run:
        console.print("[yellow]Dry run — no files will be moved or extracted.[/yellow]\n")

    # Determine files to process
    if path:
        files = [Path(path).resolve()]
    else:
        inbox = cfg.mywork_root / INBOX
        files = _scan_inbox_files(inbox)

    if not files:
        console.print("[yellow]No files to process in 00_Inbox/.[/yellow]")
        ops.close()
        return

    console.print(f"[bold]Found {len(files)} file(s) to process.[/bold]\n")

    # Process each file
    stats: dict[str, int] = {"routed": 0, "skipped": 0}

    for i, file_path in enumerate(files, 1):
        console.print(f"[dim]── File {i}/{len(files)} ──[/dim]")
        action = process_file(
            file_path,
            cfg.mywork_root,
            registry,
            ops,
            dry_run=dry_run,
            auto=auto,
            skip_extract=skip_extract,
            default_destination=destination,
        )

        if action == "quit":
            console.print("\n[yellow]Quit. Remaining files not processed.[/yellow]")
            break

        stats[action] = stats.get(action, 0) + 1
        console.print()

    # Summary
    parts = [f"Processed {sum(stats.values())}/{len(files)}"]
    for action_name, count in sorted(stats.items()):
        if count > 0:
            parts.append(f"{action_name}: {count}")
    console.print(f"\n[bold]{' | '.join(parts)}[/bold]")

    ops.close()


@click.command("finalize")
@click.option("--approve-all", is_flag=True, help="Move all staged files to final destinations")
@click.pass_obj
def finalize_command(obj: dict, approve_all: bool) -> None:
    """Review and approve staged files.

    Files below the confidence threshold are staged in _Staging/ directories.
    This command lists them for review and moves approved files to their
    final destinations.
    """
    from corp.ingest.router import finalize_file, get_staged_files
    from corp.ops.database import OpsDB

    config = (obj or {}).get("config") or PipelineConfig.production()
    cfg = get_config()
    ops = OpsDB(config=config)

    staged = get_staged_files(cfg.mywork_root)

    if not staged:
        console.print("[green]No staged files awaiting review.[/green]")
        ops.close()
        return

    console.print(f"\n[bold]{len(staged)} staged file(s) awaiting review:[/bold]\n")

    table = Table(show_lines=False)
    table.add_column("#", style="dim", justify="right")
    table.add_column("File", style="cyan")
    table.add_column("Destination", style="dim")

    for i, s in enumerate(staged, 1):
        table.add_row(str(i), s["filename"], s["parent_destination"])

    console.print(table)

    if approve_all:
        console.print("\n[yellow]Approving all staged files...[/yellow]")
        ok_count = 0
        for s in staged:
            ok = finalize_file(Path(s["path"]), cfg.mywork_root, ops)
            if ok:
                ok_count += 1
                console.print(
                    f"  [green]{CHECK}[/green] {s['filename']} -> {s['parent_destination']}"
                )
            else:
                console.print(f"  [red]FAIL[/red] {s['filename']}")
        console.print(f"\n[bold]Finalized: {ok_count}/{len(staged)}[/bold]")
    else:
        console.print(
            "\nRun [bold]corp finalize --approve-all[/bold] to move all to final destinations."
        )

    ops.close()


@click.command("classify")
@click.option("--model", default="gemini-3-flash-preview", help="Gemini model for classification")
@click.option("--budget", default=0.50, type=float, help="Maximum API spend ($)")
@click.option("--dry-run", is_flag=True, help="Classify without moving files")
@click.pass_obj
def classify_command(obj: dict, model: str, budget: float, dry_run: bool) -> None:
    """Classify quarantined files using Gemini LLM.

    Reads files in _Unmatched (quarantined by corp ingest),
    classifies each using Gemini Flash, and stages them
    at the classified destination for review via corp finalize.

    Example workflow:

        corp ingest                  # Some files quarantined
        corp classify --dry-run      # Preview LLM classifications
        corp classify                # Classify and stage
        corp finalize --approve-all  # Commit staged files
    """
    from corp.ingest.llm_classifier import classify_quarantined_batch
    from corp.ops.database import OpsDB
    from corp.ops.registry import get_content_registry

    config = (obj or {}).get("config") or PipelineConfig.production()
    cfg = get_config()
    ops = OpsDB(config=config)
    registry = get_content_registry()

    if dry_run:
        console.print("[yellow]Dry run — classifying without moving files.[/yellow]")

    console.print(f"[dim]Model: {model} | Budget: ${budget:.2f}[/dim]")

    results = classify_quarantined_batch(
        ops,
        registry,
        cfg.mywork_root,
        model=model,
        budget=budget,
        dry_run=dry_run,
    )

    if not results:
        console.print("[green]No quarantined files to classify.[/green]")
        ops.close()
        return

    table = Table(
        title="LLM Classifications" + (" (DRY RUN)" if dry_run else ""),
        show_lines=False,
    )
    table.add_column("File", style="cyan", max_width=35)
    table.add_column("Destination", max_width=45)
    table.add_column("Category", style="dim")
    table.add_column("Conf", justify="right")
    table.add_column("Reasoning", style="dim", max_width=40)

    for r in results:
        c = r["classification"]
        conf_style = "green" if c.confidence >= 0.5 else "yellow"
        table.add_row(
            r["filename"],
            c.destination,
            c.source_category,
            f"[{conf_style}]{c.confidence:.0%}[/{conf_style}]",
            c.reasoning[:40] if c.reasoning else DASH,
        )

    console.print(table)

    staged = sum(1 for r in results if r["classification"].destination != f"{INBOX}/{UNMATCHED}")
    unmatched = len(results) - staged
    console.print(
        f"\n[bold]Classified: {len(results)} | "
        f"staged: {staged} | still unmatched: {unmatched}[/bold]"
    )

    if not dry_run and staged > 0:
        console.print("\nRun [bold]corp finalize[/bold] to review staged files.")

    ops.close()


@click.command("freshness")
@click.option("--verbose", is_flag=True, help="Show all results, not just issues")
def freshness_cmd(verbose: bool) -> None:
    """Check freshness of vault notes against source files.

    Scans all vault notes and reports which ones are stale,
    orphaned, or due for review.

    Examples:

        corp freshness

        corp freshness --verbose
    """
    from corp.freshness_scanner import scan_vault_freshness

    cfg = get_config()

    console.print("[bold]Scanning vault freshness...[/bold]")
    summary = scan_vault_freshness(cfg.vault_path, cfg.mywork_root)

    # Summary panel
    console.print(
        f"\n  Scanned: {summary.total_scanned} notes\n"
        f"  Fresh: [green]{summary.fresh}[/green] | "
        f"Stale: [red]{summary.stale}[/red] | "
        f"Orphaned: [red]{summary.orphaned}[/red] | "
        f"Review due: [yellow]{summary.review_due}[/yellow] | "
        f"No source: [dim]{summary.no_source}[/dim] | "
        f"Errors: [yellow]{summary.errors}[/yellow]",
    )

    # Issues table
    issues = [r for r in summary.results if r.status not in ("fresh", "no_source")]

    if verbose:
        display = summary.results
    else:
        display = issues

    if not display:
        console.print("\n[green]All notes are fresh.[/green]")
        return

    table = Table(title="Freshness Results" if verbose else "Issues Found")
    table.add_column("Status", style="bold", width=12)
    table.add_column("Note", no_wrap=True)
    table.add_column("Reason")

    status_styles = {
        "stale": "red",
        "orphaned": "red",
        "review_due": "yellow",
        "error": "yellow",
        "fresh": "green",
        "no_source": "dim",
    }

    for r in display:
        style = status_styles.get(r.status, "")
        note_name = Path(r.note_path).name
        table.add_row(
            f"[{style}]{r.status}[/{style}]",
            note_name,
            r.reason,
        )

    console.print(table)


@click.command("ingest-extractions")
@click.argument("cke_output_path", type=click.Path(exists=True, file_okay=False))
@click.option("--dry-run", is_flag=True, help="Show what would be ingested")
@click.option("--force", is_flag=True, help="Overwrite even verified notes")
@click.option(
    "--quality-threshold", default=25, type=int, help="Min quality_score to accept (0-100)"
)
@click.option("--rebuild-index", is_flag=True, help="Rebuild FTS5 search index after ingest")
@click.pass_obj
def ingest_extractions_cmd(
    obj: dict,
    cke_output_path: str,
    dry_run: bool,
    force: bool,
    quality_threshold: int,
    rebuild_index: bool,
) -> None:
    """Ingest CKE extraction output into the vault.

    Reads CKE output packages, validates frontmatter, applies quality gate,
    and copies accepted notes to vault/01_Knowledge/ (flat). Cover slides go
    to _assets/. Failed notes go to _quarantine/. Respects trust_level=verified.

    Examples:

        corp ingest-extractions /path/to/cke/output

        corp ingest-extractions /path/to/cke/output --dry-run

        corp ingest-extractions /path/to/cke/output --rebuild-index

        corp ingest-extractions /path/to/cke/output --quality-threshold 50
    """
    from corp.ingest.extractions import ingest_extractions

    config = (obj or {}).get("config") or PipelineConfig.production()
    cfg = get_config()

    try:
        from corp.ops.database import OpsDB

        ops = OpsDB(config=config)
    except Exception:
        ops = None

    if dry_run:
        console.print("[yellow]Dry run — no files will be written.[/yellow]")
    if force:
        console.print("[yellow]Force mode — verified notes will be overwritten.[/yellow]")

    result = ingest_extractions(
        cke_output_path=Path(cke_output_path).resolve(),
        vault_root=cfg.vault_path,
        dry_run=dry_run,
        force=force,
        quality_threshold=quality_threshold,
        ops_db=ops,
    )

    table = Table(title="Ingest Results", show_edge=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right")
    table.add_row("Notes ingested", str(result.notes_ingested))
    table.add_row("Quarantined", str(result.notes_quarantined))
    table.add_row("Skipped (verified)", str(result.notes_skipped_verified))
    table.add_row("Cover slides", str(result.covers_copied))
    if result.errors:
        table.add_row("[red]Errors[/red]", f"[red]{len(result.errors)}[/red]")
    console.print(table)

    if result.by_dest:
        console.print("\n[bold]Destinations:[/bold]")
        for dest, count in sorted(result.by_dest.items()):
            console.print(f"  {dest}: {count}")

    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for err in result.errors:
            console.print(f"  {err}")

    if result.notes_quarantined > 0:
        console.print(
            f"\n[yellow]{result.notes_quarantined} note(s) quarantined to _quarantine/[/yellow]"
        )

    if result.notes_ingested > 0 and not dry_run and rebuild_index:
        console.print("\n[dim]Rebuilding search index...[/dim]")
        try:
            from corp.index_builder import rebuild_index as do_rebuild

            stats = do_rebuild(config=config)
            console.print(f"[green]Index rebuilt: {stats.facts_indexed} facts indexed.[/green]")
        except Exception as e:
            console.print(f"[red]Index rebuild failed: {e}[/red]")
    elif result.notes_ingested > 0 and not dry_run:
        console.print("\n[dim]Run `corp index rebuild` to update the search index.[/dim]")

    if ops is not None:
        try:
            ops.close()
        except Exception:
            pass
