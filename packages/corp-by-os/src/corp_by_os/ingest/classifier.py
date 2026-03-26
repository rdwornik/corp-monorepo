"""File classifier for interactive inbox ingestion.

Wraps ContentRegistry matching with file metadata detection
to produce rich Classification results for the interactive UI.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from corp_by_os.ops.registry import ContentRegistry, RegistryMatch

logger = logging.getLogger(__name__)

# Human-readable size units
_SIZE_UNITS = [(1 << 30, "GB"), (1 << 20, "MB"), (1 << 10, "KB")]


def _human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    for threshold, unit in _SIZE_UNITS:
        if size_bytes >= threshold:
            return f"{size_bytes / threshold:.1f} {unit}"
    return f"{size_bytes} B"


@dataclass(frozen=True)
class FileInfo:
    """Detected metadata about a file."""

    path: Path
    filename: str
    extension: str
    size_bytes: int
    size_human: str


@dataclass(frozen=True)
class Classification:
    """Result of classifying a file for inbox routing."""

    file_info: FileInfo
    matches: list[RegistryMatch]
    best_match: RegistryMatch | None
    needs_human: bool  # True if confidence < threshold
    detected_client: str | None


def detect_file_info(file_path: Path) -> FileInfo:
    """Gather metadata about a file."""
    stat = file_path.stat()
    return FileInfo(
        path=file_path,
        filename=file_path.name,
        extension=file_path.suffix.lower(),
        size_bytes=stat.st_size,
        size_human=_human_size(stat.st_size),
    )


def classify(
    file_path: Path,
    registry: ContentRegistry,
    *,
    confidence_threshold: float = 0.75,
) -> Classification:
    """Classify a file using the content registry.

    Returns a Classification with the best match and whether
    human review is needed (confidence below threshold).
    """
    info = detect_file_info(file_path)

    # Collect matches from all sources
    matches: list[RegistryMatch] = []

    # Get the single best match from registry (it already prioritises
    # series > client > rules > fallback internally)
    best = registry.match_file(info.filename, info.extension)
    if best.matched:
        matches.append(best)

    # Also try client detection separately if best wasn't a client match,
    # so we can report detected_client even when series wins.
    detected_client: str | None = None
    if best.method == "client":
        detected_client = best.metadata.get("project")
    else:
        # Peek at client patterns directly
        client_match = registry._match_client(info.filename)
        if client_match.matched:
            detected_client = client_match.metadata.get("project")
            if client_match not in matches:
                matches.append(client_match)

    # If no match at all, include the fallback result
    if not matches:
        matches.append(best)  # the fallback (matched=False)

    best_match = matches[0] if matches and matches[0].matched else None
    needs_human = best_match is None or best_match.confidence < confidence_threshold

    return Classification(
        file_info=info,
        matches=matches,
        best_match=best_match,
        needs_human=needs_human,
        detected_client=detected_client,
    )
