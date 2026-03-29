"""CLI entry point for corp-by-os.

Commands:
    corp project list [--status active]
    corp project show <name>
    corp project open <name>
    corp vault validate [project]
    corp doctor
    corp run <workflow> [PARAMS]
    corp run --list
    corp task add "Title" [--project X] [--deadline DATE] [--priority high]
    corp task list [--status todo] [--project X]
    corp task done "Title"
    corp tasks
    corp index rebuild [--project X]
    corp index stats
    corp query "search terms" [--project X] [--product Y] [--topic Z]
    corp analytics report
    corp analytics products --client CLIENT
    corp analytics timeline --client CLIENT
    corp analytics clients --product PRODUCT
    corp analytics overlap --product PRODUCT
    corp analytics compare --clients "C1,C2"
    corp analytics recent
    corp template list
    corp template scan
    corp template select "goal description"
    corp extract <folder> [--batch] [--dry-run] [--output-dir PATH]
    corp overnight [--scope SCOPE] [--budget N] [--dry-run] [--batch]
    corp cleanup-scan [--output PATH]
    corp apply-moves <moves-file> [--dry-run]
    corp cleanup [--scope all|duplicates|overlap|artifacts] [--execute]
    corp audit [--skip-gemini] [--budget 0.30]
    corp ingest [PATH] [--dry-run] [--no-extract]
    corp finalize [--approve-all]
    corp chat [--no-llm]
    corp retrieve "query" [--client X] [--product Y] [--top N] [--format json|table]
    corp prep <client> [--model M] [--output DIR]
    corp rfp answer "question" [--client X] [--product Y] [--model M]
    corp freshness [--verbose]
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import click
from corp_by_os.cli._common import CHECK, DASH, console, logger
from corp_by_os.cli.analytics import (
    analytics_group,
    dedup_report_command,
    files_stats_command,
    naming_stats_command,
)
from corp_by_os.cli.index import index_group
from corp_by_os.cli.misc import chat_command, test_pipeline_command
from corp_by_os.cli.project import project
from corp_by_os.cli.query import folder_review_command, query_command
from corp_by_os.cli.retrieve import prep_cmd, retrieve_cmd
from corp_by_os.cli.rfp import rfp_group
from corp_by_os.cli.system import doctor, routing_mark_reviewed, routing_review, trust_status
from corp_by_os.cli.task import task_group, tasks_shortcut
from corp_by_os.cli.template import template_group
from corp_by_os.cli.vault import vault
from corp_by_os.cli.workflow import run_workflow
from corp_by_os.config import get_config
from corp_os_meta.pipeline_config import PipelineConfig
from rich.panel import Panel
from rich.table import Table


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Corp-by-os — root orchestrator for the agent ecosystem."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")
    ctx.ensure_object(dict)
    ctx.obj["config"] = PipelineConfig.production()


cli.add_command(project)
cli.add_command(vault)
cli.add_command(template_group)
cli.add_command(index_group)
cli.add_command(rfp_group)
cli.add_command(task_group)
cli.add_command(tasks_shortcut)
cli.add_command(doctor)
cli.add_command(trust_status)
cli.add_command(routing_review)
cli.add_command(routing_mark_reviewed)
cli.add_command(run_workflow)
cli.add_command(query_command)
cli.add_command(folder_review_command)
cli.add_command(analytics_group)
cli.add_command(dedup_report_command)
cli.add_command(files_stats_command)
cli.add_command(naming_stats_command)
cli.add_command(test_pipeline_command)
cli.add_command(chat_command)
cli.add_command(retrieve_cmd)
cli.add_command(prep_cmd)

# --- Extract ---


EXTRACT_EXTENSIONS = [
    ".pptx",
    ".ppt",
    ".pdf",
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".csv",
    ".txt",
    ".md",
    ".msg",
    ".eml",
    ".mp4",
    ".mkv",
    ".mp3",
    ".wav",
]


@cli.command("extract")
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
@click.option("--batch", is_flag=True, help="Use Gemini Batch API (50% cheaper, slower)")
@click.option("--dry-run", is_flag=True, help="Build manifest but don't extract")
@click.option("--output-dir", default=None, type=click.Path(), help="Override output directory")
def extract_command(
    folder: str,
    batch: bool,
    dry_run: bool,
    output_dir: str | None,
) -> None:
    """Extract knowledge from a MyWork folder via CKE."""
    from corp_by_os.extraction.non_project.folder_policy import load_policy
    from corp_by_os.extraction.non_project.manifest_emitter import build_manifest, write_manifest
    from corp_by_os.extraction.non_project.routing import resolve_route
    from corp_by_os.extraction.non_project.scanner import scan_folder
    from corp_by_os.overnight.cke_client import is_available

    cfg = get_config()
    folder_path = Path(folder).resolve()
    mywork_root = cfg.mywork_root

    # Load routing
    routing_map_path = mywork_root / "90_System" / "routing_map.yaml"
    if not routing_map_path.exists():
        console.print(f"[red]routing_map.yaml not found: {routing_map_path}[/red]")
        sys.exit(1)

    import yaml

    with open(routing_map_path, encoding="utf-8") as f:
        routing_map = yaml.safe_load(f)

    route = resolve_route(folder_path, routing_map, mywork_root=mywork_root)
    console.print(f"[dim]Route: {route.vault_target} (scope={route.provenance_scope})[/dim]")

    # Load policy
    policy = load_policy(folder_path)
    if not policy.enabled:
        console.print(
            "[yellow]Extraction disabled for this folder (folder_manifest.yaml).[/yellow]"
        )
        sys.exit(1)

    extensions = policy.allow_extensions or EXTRACT_EXTENSIONS
    console.print(f"[dim]Scanning {folder_path}...[/dim]")
    scan_results = scan_folder(folder_path, allow_extensions=extensions)

    if not scan_results:
        console.print("[yellow]No extractable files found.[/yellow]")
        return

    console.print(f"Found [bold]{len(scan_results)}[/bold] files")

    # Build manifest
    out_dir = Path(output_dir) if output_dir else cfg.app_data_path / "staging" / folder_path.name
    manifest = build_manifest(
        scan_results,
        route,
        policy,
        out_dir,
        project_name=folder_path.name,
        mywork_root=mywork_root,
    )

    manifest_path = out_dir / "manifest.json"
    write_manifest(manifest, manifest_path)
    console.print(f"Manifest: {manifest_path} ({len(manifest['files'])} entries)")

    if dry_run:
        console.print("[yellow]Dry run — manifest written, no extraction.[/yellow]")
        return

    # Check CKE availability
    ok, err = is_available()
    if not ok:
        console.print(f"[red]CKE not available: {err}[/red]")
        sys.exit(1)

    from corp_by_os.overnight.cke_client import extract_batch, extract_sync

    console.print(f"[bold]Starting extraction ({'batch' if batch else 'sync'})...[/bold]")
    if batch:
        result = extract_batch(manifest_path)
    else:
        result = extract_sync(manifest_path)

    done = result.get("done", 0)
    errors = result.get("error", 0)
    cost = result.get("cost", 0.0)
    console.print(
        f"[green]Done: {done}[/green], errors: {errors}, cost: ${cost:.4f}",
    )

    # Move to vault
    if done > 0:
        from corp_by_os.extraction.vault_writer import move_to_vault

        moved = move_to_vault(out_dir, cfg.vault_path, route.vault_target)
        console.print(f"[green]Moved {moved} files to vault ({route.vault_target})[/green]")


# --- Overnight ---


OVERNIGHT_SCOPES: dict[str, list[str]] = {
    "all-non-project": ["30_Templates", "50_RFP", "60_Source_Library"],
    "source-library": ["60_Source_Library"],
    "rfp": ["50_RFP"],
    "templates": ["30_Templates"],
    "full-reshape": [],  # Special: uses CKE scan, not folder-based extraction
}


@cli.command("overnight")
@click.option(
    "--scope",
    default="all-non-project",
    type=click.Choice(list(OVERNIGHT_SCOPES.keys())),
    help="Which folders to process",
)
@click.option("--budget", default=1.0, type=float, help="Max spend in USD")
@click.option("--dry-run", is_flag=True, help="Preflight + scan only, no extraction")
@click.option("--batch", is_flag=True, help="Use Gemini Batch API (50% cheaper)")
@click.option(
    "--auto-threshold", default=0.90, type=float, help="Auto-approve confidence threshold"
)
@click.option("--reset", is_flag=True, help="Clear all pending files from state DB and exit")
@click.pass_obj
def overnight_command(
    obj: dict,
    scope: str,
    budget: float,
    dry_run: bool,
    batch: bool,
    auto_threshold: float,
    reset: bool,
) -> None:
    """Run overnight extraction and reshape pipeline."""
    config = (obj or {}).get("config") or PipelineConfig.production()
    if reset:
        from corp_by_os.overnight.state import OvernightState

        state = OvernightState(config=config)
        cleared = state.conn.execute("DELETE FROM files WHERE status = 'pending'").rowcount
        state.conn.commit()
        console.print(f"[green]Cleared {cleared} pending files from state DB.[/green]")
        state.close()
        return

    from corp_by_os.overnight.preflight import run_preflight

    cfg = get_config()
    mywork_root = cfg.mywork_root

    # --- Preflight ---
    console.print("[bold]Preflight checks...[/bold]")
    errors = run_preflight(
        mywork_root=mywork_root,
        vault_root=cfg.vault_path,
        app_data_path=cfg.app_data_path,
    )
    if errors:
        for err in errors:
            console.print(f"  [red]FAIL[/red] {err}")
        sys.exit(1)
    console.print("  [green]All checks passed[/green]")

    if scope == "full-reshape":
        _run_full_reshape(mywork_root, cfg, budget, dry_run, auto_threshold, config=config)
    else:
        _run_folder_extraction(scope, mywork_root, cfg, budget, dry_run, batch, config=config)


def _run_folder_extraction(
    scope: str,
    mywork_root: Path,
    cfg: AppConfig,  # noqa: F821
    budget: float,
    dry_run: bool,
    batch: bool,
    config: PipelineConfig | None = None,
) -> None:
    """Extraction flow for named folder scopes."""
    import uuid

    from corp_by_os.overnight.cke_client import is_available
    from corp_by_os.overnight.monitor import OvernightMonitor
    from corp_by_os.overnight.state import OvernightState

    run_id = f"overnight-{scope}-{uuid.uuid4().hex[:8]}"
    state = OvernightState(config=config)
    monitor = OvernightMonitor(run_id)

    state.create_run(run_id, scope=scope, budget=budget)
    monitor.log_event("run_started", scope=scope, budget=budget)

    folders = OVERNIGHT_SCOPES[scope]
    console.print(f"[bold]Scope:[/bold] {scope} -> {', '.join(folders)}")

    # Scan folders
    from corp_by_os.overnight.safety import is_safe_for_upload

    total_files = 0
    for folder_name in folders:
        folder_path = mywork_root / folder_name
        if not folder_path.exists():
            console.print(f"  [yellow]Skipping {folder_name} (not found)[/yellow]")
            continue

        from corp_by_os.extraction.non_project.scanner import scan_folder

        results = scan_folder(folder_path, allow_extensions=EXTRACT_EXTENSIONS)
        safe_count = 0
        for sr in results:
            ok, reason = is_safe_for_upload(sr.absolute_path)
            if ok:
                state.add_file(run_id, str(sr.absolute_path), file_hash="", tier="pending")
                safe_count += 1
            else:
                logger.debug("Safety blocked: %s (%s)", sr.relative_path, reason)

        console.print(f"  {folder_name}: {safe_count} files (of {len(results)} scanned)")
        total_files += safe_count

    monitor.heartbeat({"total_files": total_files, "scope": scope})

    if total_files == 0:
        console.print("[yellow]No files to process.[/yellow]")
        state.complete_run(run_id, status="completed")
        return

    if dry_run:
        console.print(f"[yellow]Dry run — {total_files} files would be processed.[/yellow]")
        state.complete_run(run_id, status="dry_run")
        report = monitor.write_morning_report(state)
        console.print(f"[dim]Report: {report}[/dim]")
        state.close()
        return

    # Check CKE
    ok, err = is_available()
    if not ok:
        console.print(f"[red]CKE not available: {err}[/red]")
        state.complete_run(run_id, status="error")
        state.close()
        sys.exit(1)

    console.print(f"[bold]Processing {total_files} files (budget=${budget:.2f})...[/bold]")
    monitor.log_event("extraction_started", total_files=total_files)

    # Build per-folder manifests and extract
    import yaml
    from corp_by_os.extraction.non_project.folder_policy import PolicyError, load_policy
    from corp_by_os.extraction.non_project.manifest_emitter import build_manifest, write_manifest
    from corp_by_os.extraction.non_project.routing import resolve_route
    from corp_by_os.extraction.vault_writer import move_to_vault
    from corp_by_os.overnight.cke_client import extract_batch, extract_sync

    routing_map_path = mywork_root / "90_System" / "routing_map.yaml"
    with open(routing_map_path, encoding="utf-8") as f:
        routing_map = yaml.safe_load(f)

    for folder_name in OVERNIGHT_SCOPES[scope]:
        folder_path = mywork_root / folder_name
        if not folder_path.exists():
            continue

        try:
            route = resolve_route(folder_path, routing_map, mywork_root=mywork_root)
            policy = load_policy(folder_path)
        except (PolicyError, Exception) as exc:
            console.print(f"  [yellow]{folder_name}: skipping ({exc})[/yellow]")
            continue

        extensions = policy.allow_extensions or EXTRACT_EXTENSIONS
        scan_results = scan_folder(folder_path, allow_extensions=extensions)
        if not scan_results:
            continue

        out_dir = cfg.app_data_path / "staging" / folder_name
        manifest = build_manifest(
            scan_results,
            route,
            policy,
            out_dir,
            project_name=folder_name,
            mywork_root=mywork_root,
        )
        manifest_path = out_dir / "manifest.json"
        write_manifest(manifest, manifest_path)

        # Check budget
        cumulative = state.get_cumulative_cost(run_id)
        if cumulative >= budget:
            console.print(f"[yellow]Budget exhausted (${cumulative:.4f} >= ${budget:.2f})[/yellow]")
            break

        console.print(f"  Extracting {folder_name} ({len(scan_results)} files)...")
        monitor.log_event("folder_started", folder=folder_name, files=len(scan_results))

        try:
            if batch:
                result = extract_batch(manifest_path)
            else:
                result = extract_sync(manifest_path)
        except Exception as exc:
            console.print(f"    [red]Extraction failed: {exc}[/red]")
            logger.exception("Extraction failed for %s", folder_name)
            # Mark folder files as error in state DB
            _update_folder_file_statuses(
                state,
                run_id,
                folder_path,
                "error",
                error=str(exc),
            )
            monitor.log_event("folder_error", folder=folder_name, error=str(exc))
            continue

        done = result.get("done", 0)
        errors = result.get("error", 0)
        cost = result.get("cost", 0.0)
        console.print(f"    Done: {done}, errors: {errors}, cost: ${cost:.4f}")
        monitor.log_event("folder_completed", folder=folder_name, done=done, cost=cost)

        # Update state DB — mark pending files for this folder as done
        per_file_cost = cost / max(done, 1) if cost > 0 else 0.0
        _update_folder_file_statuses(
            state,
            run_id,
            folder_path,
            "done",
            cost=per_file_cost,
        )

        # Move to vault
        if done > 0:
            moved = move_to_vault(out_dir, cfg.vault_path, route.vault_target)
            console.print(f"    Moved {moved} files to vault")

    state.sync_run_counters(run_id)
    state.complete_run(run_id)
    monitor.mark_complete()
    report = monitor.write_morning_report(state)
    console.print("\n[green]Overnight run complete.[/green]")
    console.print(f"[dim]Report: {report}[/dim]")

    stats = state.get_run_stats(run_id)
    console.print(
        f"  Files: {stats['processed_files']} done, "
        f"{stats['failed_files']} failed, "
        f"cost: ${stats['actual_cost']:.4f}",
    )
    state.close()

    # --- Freshness phase (appended, non-fatal) ---
    _run_freshness_phase(cfg)


def _update_folder_file_statuses(
    state: OvernightState,  # noqa: F821
    run_id: str,
    folder_path: Path,
    status: str,
    *,
    cost: float | None = None,
    error: str | None = None,
) -> int:
    """Update state DB for all pending files whose path starts with folder_path.

    Returns count of files updated.
    """
    folder_prefix = str(folder_path).replace("/", "\\")  # normalize for Windows
    pending = state.get_pending_files(run_id)
    updated = 0
    for f in pending:
        # Match files that belong to this folder
        if f["path"].startswith(folder_prefix):
            state.update_file_status(
                f["id"],
                status,
                cost=cost,
                error=error,
            )
            updated += 1
    return updated


def _run_full_reshape(
    mywork_root: Path,
    cfg: AppConfig,  # noqa: F821
    budget: float,
    dry_run: bool,
    auto_threshold: float,
    config: PipelineConfig | None = None,
) -> None:
    """Full MyWork reshape: scan → dedup → classify → plan.

    Each phase is isolated — a failure in dedup or classify does NOT
    lose the scan results. The pipeline continues with what it has.
    """
    import uuid

    from corp_by_os.overnight.cke_client import is_available, scan_local
    from corp_by_os.overnight.monitor import OvernightMonitor
    from corp_by_os.overnight.safety import is_safe_for_upload
    from corp_by_os.overnight.state import OvernightState

    run_id = f"reshape-{uuid.uuid4().hex[:8]}"
    state = OvernightState(config=config)
    monitor = OvernightMonitor(run_id)
    state.create_run(run_id, scope="full-reshape", budget=budget)
    monitor.log_event("run_started", scope="full-reshape", budget=budget)

    # --- Phase 1: Scan (fatal if this fails — nothing to work with) ---
    console.print("[bold]Phase 1: Local scan...[/bold]")

    ok, err = is_available()
    if not ok:
        console.print(f"[red]CKE not available for scan: {err}[/red]")
        sys.exit(1)

    try:
        scan_results = scan_local(mywork_root)
        console.print(f"  Scanned {len(scan_results)} files")
    except Exception as exc:
        console.print(f"[red]Phase 1 scan failed: {exc}[/red]")
        logger.exception("Phase 1 scan failed")
        return

    # Safety filter
    safe_results = []
    for sr in scan_results:
        ok, _ = is_safe_for_upload(Path(sr["path"]))
        if ok:
            safe_results.append(sr)
    console.print(f"  After safety filter: {len(safe_results)} files")

    # --- Phase 2: Dedup (non-fatal — fall back to all files as unique) ---
    console.print("[bold]Phase 2: Dedup...[/bold]")
    dup_groups: list = []
    try:
        from corp_by_os.overnight.dedup import deduplicate

        unique, dup_groups = deduplicate(safe_results)
        if dup_groups:
            wasted = sum(g.total_wasted_bytes for g in dup_groups)
            console.print(
                f"  Found {len(dup_groups)} duplicate groups "
                f"({wasted / (1024 * 1024):.1f} MB wasted)"
            )
        console.print(f"  Unique files: {len(unique)}")
    except Exception as exc:
        console.print(f"[red]Phase 2 dedup failed: {exc}[/red]")
        logger.exception("Phase 2 dedup failed")
        unique = safe_results
        console.print(f"  Continuing with all {len(unique)} files as unique")

    # --- Phase 3: Classify (non-fatal — produce plan with what we have) ---
    console.print("[bold]Phase 3: Classify...[/bold]")
    classifications: list = []
    try:
        import yaml
        from corp_by_os.overnight.classifier import classify_batch as reshape_classify

        routing_map_path = mywork_root / "90_System" / "routing_map.yaml"
        if routing_map_path.exists():
            with open(routing_map_path, encoding="utf-8") as f:
                routing_map = yaml.safe_load(f)
        else:
            routing_map = {"folders": {}}

        classifications = reshape_classify(unique, routing_map)
        console.print(f"  Files needing action: {len(classifications)}")
    except Exception as exc:
        console.print(f"[red]Phase 3 classify failed: {exc}[/red]")
        logger.exception("Phase 3 classify failed")

    # --- Phase 4: Plan + report (non-fatal) ---
    auto_approve: list = []
    needs_review: list = []

    if classifications:
        auto_approve = [c for c in classifications if c.confidence >= auto_threshold]
        needs_review = [c for c in classifications if c.confidence < auto_threshold]
        console.print(f"  Auto-approve (>={auto_threshold}): {len(auto_approve)}")
        console.print(f"  Needs review: {len(needs_review)}")

    try:
        plan_path = _write_reshape_plan(
            classifications,
            dup_groups,
            auto_threshold,
            cfg.app_data_path,
        )
        console.print(f"\n[bold]Plan:[/bold] {plan_path}")
    except Exception as exc:
        console.print(f"[red]Plan generation failed: {exc}[/red]")
        logger.exception("Plan generation failed")

    if dry_run:
        console.print("[yellow]Dry run — no changes applied.[/yellow]")
        return

    if auto_approve:
        if click.confirm(f"Apply {len(auto_approve)} auto-approved actions?", default=True):
            _execute_reshape_actions(auto_approve, mywork_root)
        else:
            console.print("[yellow]Skipped.[/yellow]")

    if needs_review:
        console.print(
            f"[dim]{len(needs_review)} items need manual review — see plan file.[/dim]",
        )

    # Register scanned files in state DB and finalize
    for sr in safe_results:
        state.add_file(run_id, str(sr["path"]), file_hash=sr.get("file_hash", ""), tier="reshape")
    # Mark all as done (reshape doesn't extract, it classifies + moves)
    for f in state.get_pending_files(run_id):
        state.update_file_status(f["id"], "done")

    state.sync_run_counters(run_id)
    state.complete_run(run_id)
    monitor.mark_complete()
    report = monitor.write_morning_report(state)
    console.print(f"\n[dim]Report: {report}[/dim]")
    state.close()

    # --- Freshness phase (appended, non-fatal) ---
    _run_freshness_phase(cfg)


def _run_freshness_phase(cfg: AppConfig) -> None:  # noqa: F821
    """Run freshness scan as a non-fatal overnight phase.

    Scans vault notes against source files, writes report to 90_System.
    """
    import json as _json

    from corp_by_os.freshness.scanner import scan_vault_freshness

    console.print("\n[bold]Freshness scan...[/bold]")
    try:
        summary = scan_vault_freshness(cfg.vault_path, cfg.mywork_root)
    except Exception as exc:
        console.print(f"  [red]Freshness scan failed: {exc}[/red]")
        logger.exception("Freshness scan failed")
        return

    console.print(
        f"  Scanned: {summary.total_scanned} | "
        f"Fresh: {summary.fresh} | "
        f"Stale: {summary.stale} | "
        f"Orphaned: {summary.orphaned} | "
        f"Review due: {summary.review_due}",
    )

    if summary.no_source:
        console.print(f"  [dim]Legacy (no source): {summary.no_source}[/dim]")
    if summary.errors:
        console.print(f"  [yellow]Errors: {summary.errors}[/yellow]")

    # Save report
    report_dir = cfg.mywork_root / "90_System"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "freshness_report.json"

    report_data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_scanned": summary.total_scanned,
        "fresh": summary.fresh,
        "stale": summary.stale,
        "orphaned": summary.orphaned,
        "review_due": summary.review_due,
        "no_source": summary.no_source,
        "errors": summary.errors,
        "issues": [
            {
                "note_path": r.note_path,
                "source_path": r.source_path,
                "status": r.status,
                "reason": r.reason,
            }
            for r in summary.results
            if r.status not in ("fresh", "no_source")
        ],
    }
    report_path.write_text(
        _json.dumps(report_data, indent=2),
        encoding="utf-8",
    )
    console.print(f"  [dim]Report: {report_path}[/dim]")


def _write_reshape_plan(
    classifications: list,
    dup_groups: list,
    auto_threshold: float,
    app_data_path: Path,
) -> Path:
    """Write a markdown reshape plan for review."""
    from datetime import datetime

    plan_path = app_data_path / "reshape_plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# MyWork Reshape Plan",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]

    # Duplicates section
    if dup_groups:
        lines.append("## Duplicate Groups")
        lines.append("")
        for g in dup_groups:
            lines.append(f"- **{g.canonical['path']}** ({g.match_type}, {g.similarity:.0%})")
            for d in g.duplicates:
                lines.append(f"  - {d['path']}")
        lines.append("")

    # Auto-approve section
    auto = [c for c in classifications if c.confidence >= auto_threshold]
    if auto:
        lines.append(f"## Auto-Approve ({len(auto)} actions, confidence >= {auto_threshold})")
        lines.append("")
        for c in auto:
            action = ""
            if c.proposed_name:
                action += f"rename → {c.proposed_name}"
            if c.proposed_folder:
                action += f" move → {c.proposed_folder}"
            lines.append(
                f"- `{c.current_path}` — {action.strip()} ({c.confidence:.0%}, {c.reasoning})"
            )
        lines.append("")

    # Needs review section
    review = [c for c in classifications if c.confidence < auto_threshold]
    if review:
        lines.append(f"## Needs Review ({len(review)} actions)")
        lines.append("")
        for c in review:
            action = ""
            if c.proposed_name:
                action += f"rename → {c.proposed_name}"
            if c.proposed_folder:
                action += f" move → {c.proposed_folder}"
            lines.append(
                f"- `{c.current_path}` — {action.strip()} ({c.confidence:.0%}, {c.reasoning})"
            )
        lines.append("")

    if not classifications and not dup_groups:
        lines.append("No actions needed — all files are clean.")

    plan_path.write_text("\n".join(lines), encoding="utf-8")
    return plan_path


def _execute_reshape_actions(actions: list, mywork_root: Path) -> None:
    """Execute auto-approved reshape actions (renames and moves).

    current_path in each action is RELATIVE to mywork_root.
    """
    import shutil

    if not mywork_root.is_absolute():
        raise ValueError(f"mywork_root must be absolute, got: {mywork_root}")

    renamed = 0
    moved = 0
    for c in actions:
        src = mywork_root / c.current_path
        if not src.exists():
            console.print(f"  [yellow]Not found: {src}[/yellow]")
            continue

        # Rename
        if c.proposed_name and c.proposed_name != src.name:
            dst = src.parent / c.proposed_name
            if not dst.exists():
                src.rename(dst)
                console.print(f"  Renamed: {src.name} → {c.proposed_name}")
                renamed += 1
                src = dst  # Update for potential move

        # Move
        if c.proposed_folder:
            dest_dir = mywork_root / c.proposed_folder
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / src.name
            if not dest_file.exists():
                shutil.move(str(src), str(dest_file))
                console.print(f"  Moved: {src.name} → {c.proposed_folder}")
                moved += 1

    console.print(f"[green]Applied: {renamed} renames, {moved} moves[/green]")


# --- Cleanup ---


@cli.command("cleanup-scan")
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(),
    help="Output path for moves.yaml (default: .corp/moves.yaml)",
)
def cleanup_scan_command(output: str | None) -> None:
    """Scan MyWork for misplaced files and generate move proposals."""
    from corp_by_os.cleanup.classifier import classify_batch as cleanup_classify
    from corp_by_os.cleanup.proposer import generate_proposals
    from corp_by_os.cleanup.scanner import scan_problematic_files

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


@cli.command("apply-moves")
@click.argument("moves_file", required=False, default=None, type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Preview without executing")
def apply_moves_command(moves_file: str | None, dry_run: bool) -> None:
    """Execute approved moves from moves.yaml."""
    from corp_by_os.cleanup.executor import execute_moves

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


@cli.command("cleanup")
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
    from corp_by_os.cleanup.disk import (
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


# --- Audit ---


@cli.command("audit")
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

    from corp_by_os.audit import (
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
            from corp_by_os.audit import _get_gemini_client

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


# --- Ingest ---


@cli.command("ingest")
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
    from corp_by_os.ingest.router import (
        IngestResult,
        PackageIngestResult,
        ingest_all,
        ingest_file,
        ingest_folder,
    )
    from corp_by_os.ops.database import OpsDB
    from corp_by_os.ops.registry import ContentRegistry, get_content_registry_path

    config = (obj or {}).get("config") or PipelineConfig.production()
    cfg = get_config()
    ops = OpsDB(config=config)
    registry = ContentRegistry(get_content_registry_path())

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


# --- Ingest Inbox (interactive) ---


@cli.command("ingest-inbox")
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
    from corp_by_os.ingest.inbox import (
        _list_events,
        _scan_inbox_files,
        _undo_event,
        process_file,
    )
    from corp_by_os.ops.database import OpsDB
    from corp_by_os.ops.registry import ContentRegistry, get_content_registry_path

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

    registry = ContentRegistry(get_content_registry_path())

    if dry_run:
        console.print("[yellow]Dry run — no files will be moved or extracted.[/yellow]\n")

    # Determine files to process
    if path:
        files = [Path(path).resolve()]
    else:
        inbox = cfg.mywork_root / "00_Inbox"
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


@cli.command("finalize")
@click.option("--approve-all", is_flag=True, help="Move all staged files to final destinations")
@click.pass_obj
def finalize_command(obj: dict, approve_all: bool) -> None:
    """Review and approve staged files.

    Files below the confidence threshold are staged in _Staging/ directories.
    This command lists them for review and moves approved files to their
    final destinations.
    """
    from corp_by_os.ingest.router import finalize_file, get_staged_files
    from corp_by_os.ops.database import OpsDB

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


@cli.command("classify")
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
    from corp_by_os.ingest.llm_classifier import classify_quarantined_batch
    from corp_by_os.ops.database import OpsDB
    from corp_by_os.ops.registry import ContentRegistry, get_content_registry_path

    config = (obj or {}).get("config") or PipelineConfig.production()
    cfg = get_config()
    ops = OpsDB(config=config)
    registry = ContentRegistry(get_content_registry_path())

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

    staged = sum(1 for r in results if r["classification"].destination != "00_Inbox/_Unmatched")
    unmatched = len(results) - staged
    console.print(
        f"\n[bold]Classified: {len(results)} | "
        f"staged: {staged} | still unmatched: {unmatched}[/bold]"
    )

    if not dry_run and staged > 0:
        console.print("\nRun [bold]corp finalize[/bold] to review staged files.")

    ops.close()


# --- Freshness ---


@cli.command("freshness")
@click.option("--verbose", is_flag=True, help="Show all results, not just issues")
def freshness_cmd(verbose: bool) -> None:
    """Check freshness of vault notes against source files.

    Scans all vault notes and reports which ones are stale,
    orphaned, or due for review.

    Examples:

        corp freshness

        corp freshness --verbose
    """
    from corp_by_os.freshness.scanner import scan_vault_freshness

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


# --- Ingest Extractions ---


@cli.command("ingest-extractions")
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
    from corp_by_os.ingest.extractions import ingest_extractions

    config = (obj or {}).get("config") or PipelineConfig.production()
    cfg = get_config()

    try:
        from corp_by_os.ops.database import OpsDB

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
            from corp_by_os.index_builder import rebuild_index as do_rebuild

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


if __name__ == "__main__":
    cli()
