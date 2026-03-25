"""Thin wrapper around CKE — direct import, no subprocess.

Imports CKE's BatchJobRunner (batch API) and BatchProcessor (sync)
directly. CKE is pip-installed in the monorepo, so normal imports work.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def is_available() -> tuple[bool, str]:
    """Check if CKE is importable. Returns (ok, error_message)."""
    try:
        import corp_knowledge_extractor.batch_api  # noqa: F401
        import corp_knowledge_extractor.manifest  # noqa: F401

        return True, ""
    except ImportError as exc:
        return False, str(exc)


def load_cke_config() -> dict[str, Any]:
    """Load CKE's own configuration (settings, processing, etc.)."""
    from config.config_loader import load_config  # type: ignore[import-untyped]

    return load_config()


def estimate_cost(manifest_path: Path) -> dict[str, Any]:
    """Estimate extraction cost without running anything.

    Returns: {total_cost, tier_breakdown: {1: n, 2: n, 3: n}, file_count}
    """
    from corp_knowledge_extractor.inventory import FileType, SourceFile  # type: ignore[import-untyped]
    from corp_knowledge_extractor.manifest import Manifest  # type: ignore[import-untyped]
    from corp_knowledge_extractor.tier_router import estimate_batch_cost  # type: ignore[import-untyped]

    m = Manifest.from_file(manifest_path)
    source_files = []
    for entry in m.files:
        ft = (
            FileType(entry.doc_type)
            if entry.doc_type in FileType.__members__.values()
            else FileType.DOCUMENT
        )
        source_files.append(
            SourceFile(
                path=entry.path,
                type=ft,
                size_bytes=entry.path.stat().st_size if entry.path.exists() else 0,
                name=entry.name or entry.id,
            )
        )

    return estimate_batch_cost(source_files)


def extract_batch(
    manifest_path: Path,
    model: str | None = None,
    poll_interval: int = 60,
    timeout: int = 28800,
    resume: bool = True,
) -> dict[str, Any]:
    """Submit manifest to Gemini Batch API via CKE's BatchJobRunner.

    Args:
        manifest_path: Path to CKE-compatible manifest JSON.
        model: Gemini model override (None = use CKE default).
        poll_interval: Seconds between batch status checks.
        timeout: Max wait time in seconds (default 8h).
        resume: Skip already-completed files.

    Returns: {total, done, error, skipped, cost, tiers}
    """
    from corp_knowledge_extractor.batch_api import BatchJobRunner  # type: ignore[import-untyped]
    from corp_knowledge_extractor.manifest import Manifest  # type: ignore[import-untyped]

    config = load_cke_config()
    if model:
        config["model_override"] = model

    m = Manifest.from_file(manifest_path)
    runner = BatchJobRunner(
        manifest=m,
        config=config,
        resume=resume,
    )

    logger.info(
        "Starting batch extraction: %d files, poll=%ds, timeout=%ds",
        len(m.files),
        poll_interval,
        timeout,
    )
    return runner.run(poll_interval=poll_interval, timeout=timeout)


def extract_sync(
    manifest_path: Path,
    model: str | None = None,
    max_rpm: int = 80,
    resume: bool = True,
) -> dict[str, Any]:
    """Synchronous extraction via CKE's BatchProcessor (fallback).

    Args:
        manifest_path: Path to CKE-compatible manifest JSON.
        model: Gemini model override.
        max_rpm: Max requests per minute.
        resume: Skip already-completed files.

    Returns: {total, done, error, skipped, cost, tiers}
    """
    from corp_knowledge_extractor.batch import BatchProcessor  # type: ignore[import-untyped]
    from corp_knowledge_extractor.manifest import Manifest  # type: ignore[import-untyped]

    config = load_cke_config()
    if model:
        config["model_override"] = model

    m = Manifest.from_file(manifest_path)
    processor = BatchProcessor(
        manifest=m,
        config=config,
        max_rpm=max_rpm,
        resume=resume,
    )

    logger.info(
        "Starting sync extraction: %d files, max_rpm=%d",
        len(m.files),
        max_rpm,
    )
    return processor.process_all()


def scan_local(
    path: Path,
    recursive: bool = True,
    exclude: tuple[str, ...] = (
        "80_Archive",
        ".corp",
        "_knowledge",
        ".venv",
        "__pycache__",
        ".git",
    ),
) -> list[dict]:
    """Run CKE Tier 1 local scan — no API calls, fully local.

    Scans files and extracts metadata (title, hash, text preview, tier)
    using CKE's scan module directly.

    Args:
        path: Directory to scan.
        recursive: Scan subdirectories.
        exclude: Folder names to skip.

    Returns:
        List of FileScanResult dicts with keys:
        path, filename, extension, size_bytes, file_hash, tier, metadata, error
    """
    from dataclasses import asdict

    from corp_knowledge_extractor.scan import scan_path  # type: ignore[import-untyped]

    results = scan_path(path, recursive=recursive, exclude=exclude)
    return [asdict(r) for r in results]
