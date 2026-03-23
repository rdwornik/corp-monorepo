"""Naming convention for inbox-ingested files (Decision #10).

Pattern: YYYY-MM_TYPE_TOPIC[_CLIENT]_Description.ext

Where:
- YYYY-MM  = file date (from mtime or current date)
- TYPE     = content type code (TRAINING, PRODUCT, etc.)
- TOPIC    = normalized topic from classification
- CLIENT   = optional, from client pattern match
- Description = sanitized original name or user description
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from corp_by_os.ingest.classifier import Classification

# Type codes — derived from source_category in registry metadata
_TYPE_MAP: dict[str, str] = {
    "training": "TRAINING",
    "product_doc": "PRODUCT",
    "competitive": "COMPETITIVE",
    "rfp": "RFP",
    "security_compliance": "COMPLIANCE",
    "meeting": "MEETING",
    "demo": "DEMO",
    "architecture": "ARCH",
    "brand": "BRAND",
}

# Topic codes — derived from series/rule metadata or keywords
_TOPIC_MAP: dict[str, str] = {
    "cognitive planning": "PLATFORM",
    "ai/ml": "PLATFORM",
    "platform": "PLATFORM",
    "enablement": "ENABLEMENT",
    "wms": "WMS",
    "warehouse": "WMS",
    "tms": "TMS",
    "transport": "TMS",
    "planning": "PLANNING",
    "demand": "PLANNING",
    "supply": "PLANNING",
    "retail": "RETAIL",
    "network": "NETWORK",
    "catman": "CATMAN",
    "category": "CATMAN",
}

# Max filename length (Windows path safety — MyWork root is ~45 chars)
_MAX_NAME_LENGTH = 120


@dataclass
class RenameProposal:
    """A proposed new filename with its components."""

    original_name: str
    proposed_name: str
    components: dict  # date, type, topic, client, description


def _sanitize(text: str) -> str:
    """Sanitize text for use in filenames."""
    # Replace spaces and special chars with underscores
    result = re.sub(r"[^\w\-.]", "_", text)
    # Collapse multiple underscores
    result = re.sub(r"_+", "_", result)
    # Strip leading/trailing underscores
    return result.strip("_")


def _infer_type(classification: Classification) -> str:
    """Infer content type code from classification metadata."""
    if classification.best_match is None:
        return "MISC"

    meta = classification.best_match.metadata
    source_cat = meta.get("source_category", "")
    if source_cat in _TYPE_MAP:
        return _TYPE_MAP[source_cat]

    # Fallback: check series destination for hints
    dest = classification.best_match.destination or ""
    if "Training" in dest:
        return "TRAINING"
    if "Product" in dest:
        return "PRODUCT"
    if "Competitive" in dest:
        return "COMPETITIVE"
    if "RFP" in dest:
        return "RFP"

    return "MISC"


def _infer_topic(classification: Classification, user_context: str | None = None) -> str:
    """Infer topic code from classification or user context."""
    # Check user context first (most specific)
    if user_context:
        context_lower = user_context.lower()
        for keyword, code in _TOPIC_MAP.items():
            if keyword in context_lower:
                return code

    # Check metadata topics
    if classification.best_match:
        meta = classification.best_match.metadata
        topics = meta.get("topics", [])
        for topic in topics:
            topic_lower = topic.lower()
            for keyword, code in _TOPIC_MAP.items():
                if keyword in topic_lower:
                    return code

        # Check products
        products = meta.get("products", [])
        for product in products:
            product_lower = product.lower()
            for keyword, code in _TOPIC_MAP.items():
                if keyword in product_lower:
                    return code

    return "GEN"


def _infer_client(classification: Classification) -> str | None:
    """Extract client code from classification."""
    if classification.detected_client:
        # Take the first part before underscore as short code
        parts = classification.detected_client.split("_")
        return parts[0].upper() if parts else None
    return None


def _extract_description(
    filename: str,
    series_id: str | None,
    user_context: str | None,
) -> str:
    """Extract a description from the original filename or user context."""
    # Strip extension
    stem = Path(filename).stem

    # If user provided context, use first few words
    if user_context:
        words = user_context.split()[:6]
        return _sanitize("_".join(words))

    # Use the original stem, sanitized
    return _sanitize(stem)


def propose_name(
    file_path: Path,
    classification: Classification,
    user_context: str | None = None,
) -> RenameProposal:
    """Propose a new filename following Decision #10 convention.

    Pattern: YYYY-MM_TYPE_TOPIC[_CLIENT]_Description.ext
    """
    # Date from file mtime
    try:
        mtime = file_path.stat().st_mtime
        date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m")
    except OSError:
        date_str = datetime.now().strftime("%Y-%m")

    type_code = _infer_type(classification)
    topic_code = _infer_topic(classification, user_context)
    client_code = _infer_client(classification)
    series_id = classification.best_match.series_id if classification.best_match else None

    description = _extract_description(
        classification.file_info.filename,
        series_id,
        user_context,
    )

    # Build name components
    parts = [date_str, type_code, topic_code]
    if client_code:
        parts.append(client_code)
    parts.append(description)

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
            "topic": topic_code,
            "client": client_code,
            "description": description,
        },
    )
