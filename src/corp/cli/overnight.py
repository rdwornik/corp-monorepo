"""Overnight extraction and reshape pipeline command."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import click

from corp.cli._common import console, logger
from corp.cli.extract import EXTRACT_EXTENSIONS
from corp.config import get_config
from corp.schema.pipeline_config import PipelineConfig

OVERNIGHT_SCOPES: dict[str, list[str]] = {
    "all-non-project": ["30_Templates", "50_RFP", "60_Source_Library"],
    "source-library": ["60_Source_Library"],
    "rfp": ["50_RFP"],
    "templates": ["30_Templates"],
    "full-reshape": [],  # Special: uses CKE scan, not folder-based extraction
}


@click.command("overnight")
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
        from corp.overnight.state import OvernightState

        state = OvernightState(config=config)
        cleared = state.conn.execute("DELETE FROM files WHERE status = 'pending'").rowcount
        state.conn.commit()
        console.print(f"[green]Cleared {cleared} pending files from state DB.[/green]")
        state.close()
        return

    from corp.overnight.preflight import run_preflight

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

    from corp.overnight.cke_client import is_available
    from corp.overnight.monitor import OvernightMonitor
    from corp.overnight.state import OvernightState

    run_id = f"overnight-{scope}-{uuid.uuid4().hex[:8]}"
    state = OvernightState(config=config)
    monitor = OvernightMonitor(run_id)

    state.create_run(run_id, scope=scope, budget=budget)
    monitor.log_event("run_started", scope=scope, budget=budget)

    folders = OVERNIGHT_SCOPES[scope]
    console.print(f"[bold]Scope:[/bold] {scope} -> {', '.join(folders)}")

    # Scan folders
    from corp.overnight.safety import is_safe_for_upload

    total_files = 0
    for folder_name in folders:
        folder_path = mywork_root / folder_name
        if not folder_path.exists():
            console.print(f"  [yellow]Skipping {folder_name} (not found)[/yellow]")
            continue

        from corp.extraction.scanner import scan_folder

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

    from corp.extraction.folder_policy import PolicyError, load_policy
    from corp.extraction.manifest_emitter import build_manifest, write_manifest
    from corp.extraction.routing import resolve_route
    from corp.extraction.vault_writer import move_to_vault
    from corp.overnight.cke_client import extract_batch, extract_sync

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

    from corp.overnight.cke_client import is_available, scan_local
    from corp.overnight.monitor import OvernightMonitor
    from corp.overnight.safety import is_safe_for_upload
    from corp.overnight.state import OvernightState

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
        from corp.overnight.dedup import deduplicate

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

        from corp.overnight.classifier import classify_batch as reshape_classify

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

    from corp.freshness_scanner import scan_vault_freshness

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
