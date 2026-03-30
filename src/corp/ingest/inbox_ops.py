"""Pure business logic for inbox ingestion — no Rich UI dependencies.

Extracted from inbox.py to separate concerns:
- inbox_ops.py: file scanning, moving, logging, registration (this file)
- inbox.py: Rich interactive UI, orchestration, Click command
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

from corp.ingest.classifier import Classification
from corp.ingest.router import _SKIP_EXTENSIONS, _SKIP_NAMES, compute_file_hash
from corp.ops.database import OpsDB
from corp.schema.folder_names import INBOX

logger = logging.getLogger(__name__)

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
    folder_l1 = dest_parts[0] if dest_parts else INBOX
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
    from corp.ops.file_registry import FileRegistry

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
