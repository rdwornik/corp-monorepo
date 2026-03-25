"""Interactive inbox ingestion — the Magistrala (Distribution Bus).

Processes files from 00_Inbox one at a time with Rich interactive UI:
detect → classify → present → context → rename → route → extract.

This is the INTERACTIVE counterpart to `corp ingest` (which is batch).
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

import click
from corp_by_os.ingest.classifier import Classification, classify
from corp_by_os.ingest.renamer import RenameProposal, propose_name
from corp_by_os.ingest.router import _SKIP_EXTENSIONS, _SKIP_NAMES, compute_file_hash
from corp_by_os.ops.database import OpsDB
from corp_by_os.ops.registry import ContentRegistry
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

# Files to skip during inbox scan
_GITKEEP = {".gitkeep"}


def _scan_inbox_files(inbox_path: Path) -> list[Path]:
    """Scan inbox for processable files (not folders, not infrastructure)."""
    if not inbox_path.exists():
        return []

    files: list[Path] = []
    for entry in sorted(inbox_path.iterdir()):
        if entry.name in _SKIP_NAMES or entry.name in _GITKEEP:
            continue
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            continue  # inbox-inbox is file-only; folders handled by `corp ingest`
        if entry.suffix.lower() in _SKIP_EXTENSIONS:
            continue
        files.append(entry)

    return files


def _present_file(
    classification: Classification,
    rename: RenameProposal,
) -> None:
    """Show Rich panel with file info, match, and proposed name."""
    info = classification.file_info
    best = classification.best_match

    # Header
    lines = [
        f"[bold cyan]FILE:[/bold cyan] {info.filename}",
        f"[dim]Size: {info.size_human} | Type: {info.extension} | In: 00_Inbox/[/dim]",
    ]

    # Match info
    if best and best.matched:
        conf_color = "green" if best.confidence >= 0.75 else "yellow"
        match_label = best.series_id or best.rule_name or best.method
        lines.append("")
        lines.append(
            f"[bold]Match:[/bold] {match_label}"
            f"  [{conf_color}][{best.confidence:.2f}][/{conf_color}]"
        )
        lines.append(f"[bold]→[/bold] {best.destination}/")
        if best.metadata:
            meta_parts = []
            if best.metadata.get("source_category"):
                meta_parts.append(best.metadata["source_category"])
            for t in best.metadata.get("topics", []):
                meta_parts.append(t)
            if meta_parts:
                lines.append(f"[dim]Metadata: {', '.join(meta_parts)}[/dim]")
    else:
        lines.append("")
        lines.append("[bold red]No match found.[/bold red] Cannot classify this file.")

    # Client detection
    if classification.detected_client:
        lines.append(f"[dim]Client detected: {classification.detected_client}[/dim]")

    # Proposed name
    lines.append("")
    lines.append(f"[bold]Proposed name:[/bold] {rename.proposed_name}")

    console.print(Panel("\n".join(lines), border_style="blue"))


def _prompt_action(
    needs_human: bool,
    has_destination: bool = True,
    dest_was_set: bool = False,
) -> str:
    """Show action menu and get user choice.

    When needs_human=True and has_destination=False (no match, no override),
    [a]ccept is hidden — user must set destination first via [d].
    After [d] sets a destination, default flips to [a].
    """
    if needs_human and not has_destination:
        console.print(
            "[yellow]No match — set a destination with [d] or add [c]ontext.[/yellow]"
        )
        console.print(
            "  [green]\\[d][/green]estination  "
            "[blue]\\[c][/blue]ontext  "
            "[red]\\[s][/red]kip  "
            "[red]\\[q][/red]uit"
        )
        return Prompt.ask(">", choices=["d", "c", "s", "q"], default="d")

    if needs_human:
        console.print(
            "[yellow]Low confidence — please confirm or override.[/yellow]"
        )

    console.print(
        "  [green]\\[a][/green]ccept  "
        "[yellow]\\[e][/yellow]dit name  "
        "[cyan]\\[d][/cyan]estination  "
        "[blue]\\[c][/blue]ontext  "
        "[red]\\[s][/red]kip  "
        "[red]\\[q][/red]uit"
    )

    # Default: [a] if high confidence or destination was just set
    if not needs_human or dest_was_set:
        default = "a"
    else:
        default = "d"

    return Prompt.ask(
        ">",
        choices=["a", "e", "d", "c", "s", "q"],
        default=default,
    )


def _get_user_context() -> str:
    """Prompt for extraction context."""
    console.print(
        "\n[bold]Context for extraction[/bold] (what is this file about?):"
    )
    context = Prompt.ask(">")
    console.print("[green]Context saved as extraction hint.[/green]")
    return context


def _get_custom_destination(mywork_root: Path | None = None) -> str | None:
    """Prompt for a custom destination path.

    Validates path exists or offers to create it.
    Returns the destination string, or None if cancelled.
    """
    console.print(
        "\n[bold]Destination path[/bold] (relative to MyWork, "
        "e.g. 10_Projects/Jaguar_Land_Rover_TMS_WMS_OMS):"
    )
    dest = Prompt.ask(">").strip().rstrip("/")
    if not dest:
        console.print("  [dim]Cancelled.[/dim]")
        return None

    if mywork_root:
        full_path = mywork_root / dest
        if not full_path.exists():
            create = Prompt.ask(
                f"  [yellow]{dest}[/yellow] doesn't exist. Create?",
                choices=["y", "n"],
                default="y",
            )
            if create == "y":
                full_path.mkdir(parents=True, exist_ok=True)
                console.print(f"  [green]Created: {dest}[/green]")
            else:
                console.print("  [dim]Cancelled.[/dim]")
                return None

    return dest


def _get_custom_name(current: str) -> str:
    """Prompt for a custom filename."""
    console.print(f"\n[bold]Current proposed name:[/bold] {current}")
    console.print("[dim]Enter new name (with extension):[/dim]")
    name = Prompt.ask(">", default=current)
    return name.strip()


def _move_file(
    file_path: Path,
    destination_rel: str,
    new_name: str,
    mywork_root: Path,
) -> Path:
    """Move file to destination with new name. Returns final path."""
    dest_dir = mywork_root / destination_rel
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / new_name

    # Handle name collision
    if dest_file.exists():
        stem = Path(new_name).stem
        suffix = Path(new_name).suffix
        counter = 1
        while dest_file.exists():
            dest_file = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    shutil.move(str(file_path), str(dest_file))
    return dest_file


def _log_ingest_event(
    ops: OpsDB,
    file_path: Path,
    dest_file: Path,
    mywork_root: Path,
    classification: Classification,
    original_name: str,
    new_name: str,
    user_context: str | None,
    extraction_triggered: bool,
) -> int:
    """Log the ingest event to ops.db. Returns event_id."""
    source_rel = str(file_path.relative_to(mywork_root.resolve())).replace("\\", "/")
    dest_rel = str(dest_file.relative_to(mywork_root.resolve())).replace("\\", "/")

    info = classification.file_info
    best = classification.best_match

    # Upsert asset — use dest_file for stat since source may already be moved
    mtime = datetime.fromtimestamp(dest_file.stat().st_mtime).isoformat(timespec="seconds")
    dest_parts = dest_rel.split("/")
    folder_l1 = dest_parts[0] if dest_parts else "00_Inbox"
    folder_l2 = dest_parts[1] if len(dest_parts) > 1 else None

    asset_id = ops.upsert_asset(
        path=source_rel,
        filename=original_name,
        extension=info.extension,
        size_bytes=info.size_bytes,
        mtime=mtime,
        folder_l1=folder_l1,
        folder_l2=folder_l2,
    )

    # Update path to new location
    ops.update_asset_path(source_rel, dest_rel)

    # Build reasoning
    reasoning_parts = ["ingest-inbox interactive"]
    if best:
        reasoning_parts.append(f"match={best.method}")
        if best.series_id:
            reasoning_parts.append(f"series={best.series_id}")
        if best.rule_name:
            reasoning_parts.append(f"rule={best.rule_name}")
    if user_context:
        reasoning_parts.append(f"context={user_context[:80]}")

    ops.update_asset_status(
        dest_rel,
        "routed",
        routed_to=dest_rel,
        routed_method=best.method if best else "manual",
        routed_confidence=best.confidence if best else 0.0,
        reasoning="; ".join(reasoning_parts),
    )

    # Log the move event specifically for undo
    event_id = ops.log_event(
        action="ingest_inbox_route",
        asset_id=asset_id,
        source_path=source_rel,
        destination_path=dest_rel,
        method=best.method if best else "manual",
        confidence=best.confidence if best else 0.0,
        reasoning="; ".join(reasoning_parts),
        reversible=True,
    )

    return event_id


def _remove_vault_package(vault_note_path: str, config=None) -> None:
    """Remove existing vault package to make way for re-extraction."""
    from corp_os_meta.pipeline_config import PipelineConfig

    if config is None:
        config = PipelineConfig.production()
    pkg_path = config.vault_path / vault_note_path.replace("/", "\\")

    if pkg_path.exists():
        if pkg_path.is_dir():
            shutil.rmtree(pkg_path)
        else:
            pkg_path.unlink()
        console.print(f"  [yellow]Removed: {vault_note_path}[/yellow]")


def _read_model_from_vault_note(
    vault_note_path: str,
    vault_root: Path,
) -> str | None:
    """Read model field from vault note frontmatter."""
    import yaml

    note_dir = vault_root / vault_note_path.replace("/", "\\")
    # CKE output may be a directory with extract/*.md or a direct .md file
    search_dirs = [note_dir / "extract", note_dir]
    for search in search_dirs:
        if not search.exists():
            continue
        for md_file in search.glob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8", errors="replace")
                if text.startswith("---"):
                    end = text.find("---", 3)
                    if end > 0:
                        fm = yaml.safe_load(text[3:end])
                        if fm and "model" in fm:
                            return fm["model"]
            except Exception:
                continue
    return None


def _check_dedup(
    file_path: Path,
    ops: OpsDB,
    *,
    auto: bool = False,
) -> str | None:
    """Check if file is already known in the registry. Call BEFORE move.

    Dedup is about file IDENTITY (content hash), not extraction status.
    If the same hash is in the registry, it's a duplicate.

    Returns:
        None       — proceed with route + extract
        "skip"     — file already handled, skip entirely
    """
    from corp_by_os.ops.file_registry import FileRegistry

    content_hash = compute_file_hash(file_path)
    registry = FileRegistry(ops.conn)
    file_record = registry.get_by_hash(content_hash)

    if file_record is None:
        return None  # New file, proceed normally

    latest = registry.latest_extraction(file_record.file_id)

    if latest:
        # Known + extracted
        if auto:
            console.print(
                f"  [dim]Already extracted, skipping: "
                f"{latest.vault_note_path}[/dim]"
            )
            _log_dedup_skip(
                ops, file_path, content_hash, "already_extracted_auto", latest.vault_note_path
            )
            return "skip"

        console.print(
            f"  [yellow]Already extracted:[/yellow] {latest.vault_note_path}"
        )
        console.print(
            f"  [dim]Model: {latest.model} | "
            f"Date: {latest.extracted_at}[/dim]"
        )
        console.print("  [bold][s][/bold]kip  [bold][r][/bold]e-extract")
        answer = Prompt.ask(">", choices=["s", "r"], default="s")

        if answer == "s":
            console.print("  [dim]Skipped — existing note kept.[/dim]")
            _log_dedup_skip(
                ops, file_path, content_hash, "already_extracted_user_skip", latest.vault_note_path
            )
            return "skip"

        # User chose re-extract: remove old vault package
        if latest.vault_note_path:
            console.print("  [dim]Removing old extraction...[/dim]")
            _remove_vault_package(latest.vault_note_path)
        return None  # Proceed with route + extract

    else:
        # Known + NOT extracted (routed with --skip-extract previously)
        dest = file_record.current_path or "unknown"
        if auto:
            console.print(
                f"  [dim]File already routed to {dest}, skipping.[/dim]"
            )
            _log_dedup_skip(ops, file_path, content_hash, "already_routed_auto", dest)
            return "skip"

        console.print(
            f"  [yellow]File already routed:[/yellow] {dest}"
        )
        console.print(
            "  [bold][s][/bold]kip  [bold][e][/bold]xtract now"
        )
        answer = Prompt.ask(">", choices=["s", "e"], default="s")

        if answer == "s":
            console.print("  [dim]Skipped.[/dim]")
            _log_dedup_skip(ops, file_path, content_hash, "already_routed_user_skip", dest)
            return "skip"

        # User wants to extract — proceed (file will be re-registered
        # at its new location after move)
        return None


def _log_dedup_skip(
    ops: OpsDB,
    file_path: Path,
    content_hash: str,
    reason: str,
    existing_path: str | None,
) -> None:
    """Record dedup skip in ops.db for traceability."""
    try:
        source = str(file_path).replace("\\", "/")
        ops.log_event(
            action="dedup_skip",
            source_path=source,
            destination_path=existing_path,
            reasoning=f"hash={content_hash[:12]}; {reason}",
            reversible=False,
        )
    except Exception as e:
        logger.warning("Failed to log dedup skip: %s", e)


def _register_file(file_path: Path, ops: OpsDB) -> None:
    """Register a routed file in the FileRegistry. Call AFTER move."""
    from corp_by_os.ops.file_registry import FileRegistry

    content_hash = compute_file_hash(file_path)
    source_path = str(file_path.resolve()).replace("\\", "/")
    registry = FileRegistry(ops.conn)
    registry.register_file(
        content_hash=content_hash,
        filename=file_path.name,
        path=source_path,
        size_bytes=file_path.stat().st_size,
    )


def _log_routing_feedback(
    ops: OpsDB,
    file_path: Path,
    classification: object,
    *,
    final_destination: str,
    was_overridden: bool,
    routing_method: str,
    user_context: str | None = None,
) -> None:
    """Log routing decision to ops.db. Fail-open — never blocks routing."""
    try:
        cls_dest = None
        cls_conf = None
        client = None
        if hasattr(classification, "best_match") and classification.best_match:
            cls_dest = classification.best_match.destination
            cls_conf = classification.best_match.confidence
        if hasattr(classification, "client") and classification.client:
            client = classification.client

        ops.log_routing_decision(
            filename=file_path.name,
            extension=file_path.suffix,
            file_size_bytes=file_path.stat().st_size if file_path.exists() else 0,
            classifier_destination=cls_dest,
            classifier_confidence=cls_conf,
            final_destination=final_destination,
            was_overridden=was_overridden,
            routing_method=routing_method,
            user_context=user_context,
            client=client,
        )
    except Exception as e:
        logger.warning("Failed to log routing feedback: %s", e)


def _trigger_extraction(
    file_path: Path,
    mywork_root: Path,
    ops: OpsDB,
    user_context: str | None,
    event_id: int | None = None,
    config=None,  # PipelineConfig | None
) -> bool:
    """Run CKE extraction and record result in FileRegistry.

    Assumes file is already registered and dedup was checked earlier.
    """
    from corp_by_os.ops.file_registry import FileRegistry

    try:
        from corp_by_os.ingest.router import _run_extraction

        content_hash = compute_file_hash(file_path)
        mtime_str = datetime.fromtimestamp(
            file_path.stat().st_mtime
        ).isoformat(timespec="seconds")

        rel_path = str(
            file_path.relative_to(mywork_root.resolve())
        ).replace("\\", "/")
        asset = ops.get_asset(rel_path)
        asset_id = asset["id"] if asset else None

        from corp_os_meta.pipeline_config import PipelineConfig

        if config is None:
            config = PipelineConfig.production()

        vault_note, cost = _run_extraction(
            file_path, mywork_root, ops, asset_id, content_hash, mtime_str,
            user_context=user_context,
            config=config,
        )

        if vault_note:
            console.print(f"  [green]Extracted → {vault_note}[/green]")

            # Record extraction in registry
            model = (
                _read_model_from_vault_note(vault_note, config.vault_path)
                or "unknown"
            )
            cost_cents = int(cost * 100) if cost else None
            registry = FileRegistry(ops.conn)
            file_record = registry.get_by_hash(content_hash)
            if file_record:
                registry.record_extraction(
                    file_id=file_record.file_id,
                    model=model,
                    vault_note_path=vault_note,
                    cost_cents=cost_cents,
                )

            # Store vault path on the event for full undo
            if event_id is not None:
                ops.conn.execute(
                    "UPDATE ingest_events SET vault_note_path = ? WHERE id = ?",
                    (vault_note.replace("\\", "/"), event_id),
                )
                ops.conn.commit()
            return True
        else:
            console.print("  [yellow]Extraction returned no output.[/yellow]")
            return False
    except Exception as exc:
        console.print(f"  [red]Extraction failed: {exc}[/red]")
        logger.error("Extraction failed for %s: %s", file_path.name, exc)
        return False


def _list_events(ops: OpsDB, limit: int = 20) -> None:
    """Show recent ingest-inbox events from ops.db as a Rich table."""
    rows = ops.conn.execute(
        """SELECT id, action, source_path, destination_path,
                  method, confidence, timestamp, reverted, vault_note_path
           FROM ingest_events
           WHERE action = 'ingest_inbox_route'
           ORDER BY id DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()

    if not rows:
        console.print("[yellow]No ingest-inbox events found.[/yellow]")
        return

    table = Table(title=f"Ingest History (last {limit})")
    table.add_column("ID", style="bold", justify="right")
    table.add_column("Date", style="dim")
    table.add_column("Status", style="bold")
    table.add_column("File", style="cyan", max_width=40, no_wrap=True)
    table.add_column("Destination", max_width=50)

    active_count = 0
    undone_count = 0

    for row in rows:
        event = dict(row)
        event_id = str(event["id"])
        # Extract short date from ISO timestamp
        ts = event.get("timestamp", "")
        date_short = ts[:10] if len(ts) >= 10 else ts

        is_reverted = bool(event.get("reverted"))
        if is_reverted:
            status = "[yellow]undone[/yellow]"
            undone_count += 1
        else:
            status = "[green]active[/green]"
            active_count += 1

        # Extract filename from source_path
        source = event.get("source_path", "")
        filename = Path(source).name if source else "?"

        dest = event.get("destination_path", "")
        # Show directory only (strip filename)
        dest_dir = str(Path(dest).parent).replace("\\", "/") if dest else ""

        table.add_row(event_id, date_short, status, filename, dest_dir)

    console.print(table)
    console.print(
        f"\n[dim]Total: {len(rows)} events "
        f"({active_count} active, {undone_count} undone)[/dim]"
    )


def _undo_event(
    event_id: int,
    ops: OpsDB,
    mywork_root: Path,
    full: bool = False,
    *,
    vault_path: Path | None = None,
    app_data_path: Path | None = None,
) -> bool:
    """Undo a previous ingest-inbox event by moving file back to Inbox.

    If full=True, also removes the vault package in 01_Knowledge/,
    cleans up staging artifacts, and rebuilds the index.
    vault_path/app_data_path override config for testing.
    """
    # Find the event
    row = ops.conn.execute(
        "SELECT * FROM ingest_events WHERE id = ?",
        (event_id,),
    ).fetchone()

    if row is None:
        console.print(f"[red]Event {event_id} not found.[/red]")
        return False

    event = dict(row)

    if event["reverted"]:
        console.print(f"[yellow]Event {event_id} already reverted.[/yellow]")
        return False

    if not event["reversible"]:
        console.print(f"[red]Event {event_id} is not reversible.[/red]")
        return False

    if event["action"] != "ingest_inbox_route":
        console.print(
            f"[red]Event {event_id} is not an ingest-inbox event "
            f"(action={event['action']}).[/red]"
        )
        return False

    dest_path = event["destination_path"]
    source_path = event["source_path"]

    if not dest_path or not source_path:
        console.print("[red]Event missing source/destination paths.[/red]")
        return False

    # Resolve to absolute paths
    dest_abs = mywork_root / dest_path.replace("/", "\\")
    inbox = mywork_root / "00_Inbox"

    if not dest_abs.exists():
        console.print(f"[red]File not found at destination: {dest_path}[/red]")
        return False

    # Extract original filename from source_path
    original_name = Path(source_path).name
    restore_path = inbox / original_name

    # Handle collision in inbox
    if restore_path.exists():
        stem = Path(original_name).stem
        suffix = Path(original_name).suffix
        counter = 1
        while restore_path.exists():
            restore_path = inbox / f"{stem}_{counter}{suffix}"
            counter += 1

    try:
        shutil.move(str(dest_abs), str(restore_path))
        ops.revert_event(event_id)

        # Update asset path back
        restore_rel = str(restore_path.relative_to(mywork_root.resolve())).replace("\\", "/")
        ops.update_asset_path(dest_path, restore_rel)

        console.print(
            f"[green]Undone:[/green] {dest_abs.name} → 00_Inbox/{restore_path.name}"
        )
    except OSError as exc:
        console.print(f"[red]Undo failed: {exc}[/red]")
        return False

    # Full revert: remove vault package + staging + rebuild index
    if full:
        _full_revert(
            event, mywork_root,
            vault_path=vault_path, app_data_path=app_data_path,
        )

    return True


def _full_revert(
    event: dict,
    mywork_root: Path,
    *,
    vault_path: Path | None = None,
    app_data_path: Path | None = None,
    config=None,  # PipelineConfig | None
) -> None:
    """Remove vault package and staging artifacts, rebuild index.

    vault_path and app_data_path default to values from PipelineConfig.production().
    """
    if vault_path is None or app_data_path is None:
        from corp_os_meta.pipeline_config import PipelineConfig

        if config is None:
            config = PipelineConfig.production()
        vault_path = vault_path or config.vault_path
        app_data_path = app_data_path or config.app_data_path

    # Step 1: Remove vault package if we know where it is
    vault_note = event.get("vault_note_path")
    if vault_note:
        vault_abs = vault_path / vault_note.replace("/", "\\")
        if vault_abs.exists():
            if vault_abs.is_dir():
                shutil.rmtree(vault_abs)
            else:
                vault_abs.unlink()
            console.print(f"  [yellow]Removed vault package: {vault_note}[/yellow]")
        else:
            console.print(f"  [dim]Vault path not found: {vault_note}[/dim]")
    else:
        console.print("  [dim]No vault package path recorded — skipping.[/dim]")

    # Step 2: Remove staging artifacts
    staging_base = app_data_path / "staging" / "ingest"
    if staging_base.exists():
        source_path = event.get("source_path", "")
        original_stem = Path(source_path).stem if source_path else ""
        if original_stem:
            # Staging dirs use entry_id derived from filename
            norm_stem = original_stem.lower().replace(" ", "_").replace("-", "_")
            for pkg_dir in staging_base.iterdir():
                if pkg_dir.is_dir() and norm_stem[:20] in pkg_dir.name.lower():
                    shutil.rmtree(pkg_dir)
                    console.print(
                        f"  [yellow]Removed staging: {pkg_dir.name}[/yellow]"
                    )
                    break

    # Step 3: Rebuild index
    try:
        from corp_by_os.index_builder import rebuild_index

        console.print("  [dim]Rebuilding index...[/dim]")
        stats = rebuild_index()
        console.print(
            f"  [green]Index rebuilt: {stats.notes_indexed} notes[/green]"
        )
    except Exception as exc:
        console.print(f"  [red]Index rebuild failed: {exc}[/red]")
        logger.error("Index rebuild during full undo failed: %s", exc)


def process_file(
    file_path: Path,
    mywork_root: Path,
    registry: ContentRegistry,
    ops: OpsDB,
    *,
    dry_run: bool = False,
    auto: bool = False,
    skip_extract: bool = False,
    default_destination: str | None = None,
) -> str:
    """Process a single file interactively. Returns action taken.

    Actions: 'routed', 'skipped', 'quit'

    default_destination: pre-set destination for all files (--destination flag).
    Classifier still runs for metadata, but destination is overridden.
    """
    # Step 0: Dedup check BEFORE classify/move (by content hash)
    dedup = _check_dedup(file_path, ops, auto=auto)
    if dedup == "skip":
        return "skipped"

    # Step 1-2: Detect + Classify
    fallback = registry.get_fallback_config()
    threshold = fallback.get("confidence_threshold", 0.75)
    classification = classify(file_path, registry, confidence_threshold=threshold)

    # Step 3: Propose name
    rename = propose_name(file_path, classification)

    # Determine destination: --destination flag > classifier
    override_dest = default_destination

    # Auto mode: accept high-confidence matches or --destination override
    auto_dest = override_dest or (
        classification.best_match.destination
        if classification.best_match and classification.best_match.confidence >= 0.90
        else None
    )
    if auto and auto_dest:
        if dry_run:
            console.print(
                f"[dim]AUTO [dry-run]: {file_path.name} → "
                f"{auto_dest}/ "
                f"as {rename.proposed_name}[/dim]"
            )
            return "routed"

        dest = auto_dest
        final_path = _move_file(file_path, dest, rename.proposed_name, mywork_root)
        _register_file(final_path, ops)
        event_id = _log_ingest_event(
            ops, file_path, final_path, mywork_root,
            classification, file_path.name, rename.proposed_name,
            None, not skip_extract,
        )
        _log_routing_feedback(
            ops, file_path, classification,
            final_destination=dest,
            was_overridden=bool(override_dest),
            routing_method="batch_flag" if default_destination else "classifier_auto",
        )
        console.print(
            f"[green]AUTO:[/green] {file_path.name} → {dest}/{rename.proposed_name}"
        )
        if not skip_extract:
            _trigger_extraction(
                final_path, mywork_root, ops, None, event_id=event_id
            )
        return "routed"

    # Step 4: Present to user
    _present_file(classification, rename)

    # Interactive loop
    user_context: str | None = None
    current_dest = override_dest or (
        classification.best_match.destination
        if classification.best_match and classification.best_match.matched
        else None
    )
    current_name = rename.proposed_name
    dest_was_set = False  # Tracks if user explicitly set destination via [d]

    while True:
        choice = _prompt_action(
            classification.needs_human,
            has_destination=current_dest is not None,
            dest_was_set=dest_was_set,
        )

        if choice == "q":
            return "quit"

        if choice == "s":
            console.print(f"[dim]Skipped: {file_path.name}[/dim]")
            return "skipped"

        if choice == "c":
            user_context = _get_user_context()
            # Context stored for extraction, does NOT change filename.
            # But if context mentions a known client, suggest that project.
            if not current_dest or classification.needs_human:
                client_match = registry._match_client(user_context)
                if client_match.matched and client_match.destination:
                    console.print(
                        f"  [cyan]Suggested destination:[/cyan] "
                        f"{client_match.destination}"
                    )
                    use_it = Prompt.ask(
                        "  Use this destination?",
                        choices=["y", "n"],
                        default="y",
                    )
                    if use_it == "y":
                        current_dest = client_match.destination
                        dest_was_set = True
            continue

        if choice == "e":
            current_name = _get_custom_name(current_name)
            continue

        if choice == "d":
            new_dest = _get_custom_destination(mywork_root)
            if new_dest is not None:
                current_dest = new_dest
                dest_was_set = True
            continue

        if choice == "a":
            if not current_dest:
                console.print("[red]No destination set. Use [d] to set one.[/red]")
                continue

            if dry_run:
                console.print(
                    f"[yellow]DRY RUN:[/yellow] Would move {file_path.name} → "
                    f"{current_dest}/{current_name}"
                )
                return "routed"

            # Execute: move + register + log + extract
            try:
                final_path = _move_file(
                    file_path, current_dest, current_name, mywork_root
                )
            except OSError as exc:
                console.print(f"[red]Move failed: {exc}[/red]")
                continue

            _register_file(final_path, ops)

            event_id = _log_ingest_event(
                ops, file_path, final_path, mywork_root,
                classification, file_path.name, current_name,
                user_context, not skip_extract,
            )

            _log_routing_feedback(
                ops, file_path, classification,
                final_destination=current_dest,
                was_overridden=dest_was_set,
                routing_method="manual_override" if dest_was_set else (
                    "batch_flag" if default_destination else "classifier_auto"
                ),
                user_context=user_context,
            )

            console.print(
                f"[green]Routed:[/green] {current_dest}/{final_path.name}"
                f"  [dim](event #{event_id})[/dim]"
            )

            if not skip_extract:
                _trigger_extraction(
                    final_path, mywork_root, ops, user_context, event_id=event_id
                )

            return "routed"


@click.command("ingest-inbox")
@click.option(
    "--path",
    type=click.Path(exists=True),
    default=None,
    help="Process a specific file instead of scanning Inbox.",
)
@click.option("--dry-run", is_flag=True, help="Show what would happen without moving files.")
@click.option(
    "--auto",
    is_flag=True,
    help="Auto-accept high-confidence matches (>=0.90).",
)
@click.option(
    "--undo",
    type=int,
    default=None,
    help="Undo a previous ingest by event ID.",
)
@click.option(
    "--skip-extract",
    is_flag=True,
    help="Route file but skip CKE extraction.",
)
def ingest_inbox(
    path: str | None,
    dry_run: bool,
    auto: bool,
    undo: int | None,
    skip_extract: bool,
) -> None:
    """Interactively route files from 00_Inbox to their canonical locations.

    Processes one file at a time with Rich UI: classify, confirm
    destination, rename, move, then trigger CKE extraction.
    """
    from corp_by_os.ops.registry import get_content_registry_path
    from corp_os_meta.pipeline_config import PipelineConfig

    cfg = PipelineConfig.production()
    ops = OpsDB()
    registry = ContentRegistry(get_content_registry_path())

    # Undo mode
    if undo is not None:
        _undo_event(undo, ops, cfg.mywork_root)
        ops.close()
        return

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
        )

        if action == "quit":
            console.print("\n[yellow]Quit. Remaining files not processed.[/yellow]")
            break

        stats[action] = stats.get(action, 0) + 1
        console.print()  # blank line between files

    # Summary
    parts = [f"Processed {sum(stats.values())}/{len(files)}"]
    for action, count in sorted(stats.items()):
        if count > 0:
            parts.append(f"{action}: {count}")
    console.print(f"\n[bold]{' | '.join(parts)}[/bold]")

    ops.close()
