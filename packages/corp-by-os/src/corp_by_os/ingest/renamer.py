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
from dataclasses import dataclass
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


@dataclass
class RenameProposal:
    """A proposed new filename with its components."""

    original_name: str
    proposed_name: str
    components: dict  # date, type, client, description


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
    """
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
