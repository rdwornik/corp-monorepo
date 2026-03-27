"""Naming convention for inbox-ingested files (Decision #14).

Pattern: YYYY-MM_TYPE_CLIENT_Description.ext

Where:
- YYYY-MM     = file date (from mtime or current date)
- TYPE        = type code from naming_config.yaml (PRES, RFP, TRAIN, etc.)
- CLIENT      = client alias (JLR, LENZ, GEN for unknown)
- Description = sanitized original filename
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from corp_by_os.ingest.classifier import Classification
from corp_by_os.ingest.naming_config import (
    clean_description,
    get_client_alias,
    get_type_code,
)

logger = logging.getLogger(__name__)

# Max filename length (Windows path safety — MyWork root is ~45 chars)
_MAX_NAME_LENGTH = 120
_MAX_FOLDER_NAME_LENGTH = 40

# Already-compliant pattern: YYYY-MM_TYPE_CLIENT_  (prevents double-prefixing)
_COMPLIANT_RE = re.compile(r"^20\d{2}-\d{2}_[A-Z]+_[A-Z]+_")


@dataclass
class RenameProposal:
    """A proposed new filename with its components."""

    original_name: str
    proposed_name: str
    components: dict  # date, type, client, description


@dataclass
class FolderRenameProposal:
    """A proposed new folder name with classification metadata."""

    original_name: str
    proposed_name: str
    is_event: bool  # True = event folder (all files within 7 days)
    span_days: float
    client_alias: str
    type_code: str  # leading type for event folders; "PROJECT" for project folders
    file_count: int
    unchanged: bool = field(init=False)

    def __post_init__(self) -> None:
        self.unchanged = self.original_name == self.proposed_name


def _sanitize(text: str) -> str:
    """Sanitize text for use in filenames."""
    # Replace spaces and special chars with underscores
    result = re.sub(r"[^\w\-.]", "_", text)
    # Collapse multiple underscores
    result = re.sub(r"_+", "_", result)
    # Strip leading/trailing underscores
    return result.strip("_")


def _infer_type(classification: Classification) -> str:
    """Infer content type code from classification metadata and filename."""
    filename = classification.file_info.filename
    doc_type = None
    source_category = None

    if classification.best_match is not None:
        meta = classification.best_match.metadata
        source_category = meta.get("source_category")
        doc_type = meta.get("doc_type")

    return get_type_code(
        doc_type=doc_type,
        filename=filename,
        source_category=source_category,
    )


def _infer_client(classification: Classification) -> str:
    """Get client alias from classification."""
    return get_client_alias(classification.detected_client)


def _extract_description(
    filename: str,
    series_id: str | None,
    user_context: str | None,
) -> str:
    """Extract a description from the original filename.

    user_context is an extraction hint, NOT a rename source.
    The filename always comes from the original file.
    """
    stem = Path(filename).stem
    return clean_description(stem)


def propose_name(
    file_path: Path,
    classification: Classification,
    user_context: str | None = None,
) -> RenameProposal:
    """Propose a new filename following Decision #14 convention.

    Pattern: YYYY-MM_TYPE_CLIENT_Description.ext

    Returns the original filename unchanged if it already matches the
    compliant pattern (prevents double-prefixing on re-runs).
    """
    original_filename = classification.file_info.filename

    # Skip already-compliant files
    if _COMPLIANT_RE.match(original_filename):
        return RenameProposal(
            original_name=original_filename,
            proposed_name=original_filename,
            components={"date": "", "type": "", "client": "", "description": ""},
        )

    # Date from file mtime
    try:
        mtime = file_path.stat().st_mtime
        date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m")
    except OSError:
        date_str = datetime.now().strftime("%Y-%m")

    type_code = _infer_type(classification)
    client_code = _infer_client(classification)
    series_id = classification.best_match.series_id if classification.best_match else None

    description = _extract_description(
        classification.file_info.filename,
        series_id,
        user_context,
    )

    # Log MISC for taxonomy review
    if type_code == "MISC":
        logger.info(
            "MISC classification for %s — review needed",
            classification.file_info.filename,
        )

    # Build name: date_type_client_description.ext
    parts = [date_str, type_code, client_code, description]
    extension = classification.file_info.extension
    proposed_stem = "_".join(parts)

    # Truncate if needed (leave room for extension)
    max_stem = _MAX_NAME_LENGTH - len(extension)
    if len(proposed_stem) > max_stem:
        proposed_stem = proposed_stem[:max_stem]
        # Don't end on underscore
        proposed_stem = proposed_stem.rstrip("_")

    proposed_name = f"{proposed_stem}{extension}"

    return RenameProposal(
        original_name=classification.file_info.filename,
        proposed_name=proposed_name,
        components={
            "date": date_str,
            "type": type_code,
            "client": client_code,
            "description": description,
        },
    )


def _clean_folder_description(folder_name: str, client_alias: str) -> str:
    """Strip client tokens from folder name and return a clean description part."""
    # Remove special chars, normalise to words
    words = re.sub(r"[^a-zA-Z0-9]", " ", folder_name).split()
    # Drop tokens that belong to the client alias (case-insensitive, ≤6 chars)
    alias_lower = client_alias.lower()
    filtered = [w for w in words if w.lower() != alias_lower and len(w) > 1]
    result = "_".join(filtered)
    return result[:30].rstrip("_") or "Project"


def _infer_folder_type(files: list[Path]) -> str:
    """Return the most common non-MISC type code from a list of file paths."""
    from collections import Counter

    counts: Counter[str] = Counter()
    for f in files:
        code = get_type_code(filename=f.name)
        if code not in ("MISC", "IMG", "VID", "ARCH"):
            counts[code] += 1
    if counts:
        return counts.most_common(1)[0][0]
    return "MISC"


def propose_folder_name(folder: Path) -> FolderRenameProposal:
    """Propose a new name for a 10_Projects subfolder.

    Detection rules:
    - Files spanning >30 days  → PROJECT folder (no date prefix)
    - Files all within 7 days  → EVENT folder (YYYY-MM_TYPE_CLIENT_Desc)
    - 7–30 days                → treated as PROJECT (conservative)

    Folder pattern (project):  CLIENT_Description
    Folder pattern (event):    YYYY-MM_TYPE_CLIENT_Description
    Max 40 chars, underscores only.
    """
    files = [
        f
        for f in folder.rglob("*")
        if f.is_file() and not f.name.startswith(".")
    ]

    if not files:
        return FolderRenameProposal(
            original_name=folder.name,
            proposed_name=folder.name,
            is_event=False,
            span_days=0.0,
            client_alias="GEN",
            type_code="PROJECT",
            file_count=0,
        )

    mtimes = [f.stat().st_mtime for f in files]
    span_days = (max(mtimes) - min(mtimes)) / 86400

    is_event = span_days <= 7

    client_alias = get_client_alias(folder.name)
    desc = _clean_folder_description(folder.name, client_alias)

    if is_event:
        date_str = datetime.fromtimestamp(min(mtimes)).strftime("%Y-%m")
        type_code = _infer_folder_type(files)
        stem = f"{date_str}_{type_code}_{client_alias}_{desc}"
    else:
        type_code = "PROJECT"
        stem = f"{client_alias}_{desc}"

    proposed = stem[:_MAX_FOLDER_NAME_LENGTH].rstrip("_")
    # Ensure no double underscores
    proposed = re.sub(r"_+", "_", proposed)

    return FolderRenameProposal(
        original_name=folder.name,
        proposed_name=proposed,
        is_event=is_event,
        span_days=round(span_days, 1),
        client_alias=client_alias,
        type_code=type_code,
        file_count=len(files),
    )
