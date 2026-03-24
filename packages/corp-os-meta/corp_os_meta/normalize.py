"""
Taxonomy loading and term normalization.
Reads taxonomy.yaml, builds alias lookup, normalizes extracted terms.
"""

import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_TAXONOMY_CACHE: dict | None = None
_TAXONOMY_PATH: Path | None = None


@dataclass
class NormalizationResult:
    """What changed during normalization."""

    normalized: list[str]  # final list of canonical terms
    changes: list[str]  # "DR → Disaster Recovery"
    unknown: list[str]  # terms not in taxonomy
    duplicates_removed: int  # count of deduped terms


def get_taxonomy_path() -> Path:
    """Find taxonomy.yaml — inside this package."""
    return Path(__file__).parent / "taxonomy.yaml"


def load_taxonomy(path: Path | None = None) -> dict:
    """Load and cache taxonomy. Called once per process."""
    global _TAXONOMY_CACHE, _TAXONOMY_PATH
    path = path or get_taxonomy_path()
    if _TAXONOMY_CACHE is not None and _TAXONOMY_PATH == path:
        return _TAXONOMY_CACHE
    with open(path, "r", encoding="utf-8") as f:
        _TAXONOMY_CACHE = yaml.safe_load(f)
    _TAXONOMY_PATH = path
    return _TAXONOMY_CACHE


def preprocess(term: str) -> str:
    """Normalize term for fuzzy-tolerant matching.

    Strip/casefold, remove parentheticals, normalize &→and,
    collapse whitespace, strip trailing 's' (for terms >3 chars, not 'ss').
    """
    result = term.strip().casefold()
    result = re.sub(r"\s*\([^)]*\)", "", result)  # remove parenthetical
    result = result.replace(" & ", " and ")
    result = re.sub(r"\s+", " ", result).strip()  # collapse whitespace
    if len(result) > 3 and result.endswith("s") and not result.endswith("ss"):
        result = result[:-1]
    return result


def build_alias_map(
    taxonomy: dict, section: str
) -> tuple[dict[str, str], dict[str, str]]:
    """Build lookup maps: exact (lowered) and preprocessed."""
    exact_map = {}
    preprocessed_map = {}

    for entry in taxonomy.get(section, []):
        canonical = entry["name"]
        exact_map[canonical.lower()] = canonical
        preprocessed_map[preprocess(canonical)] = canonical

        for alias in entry.get("aliases", []):
            exact_map[alias.lower()] = canonical
            preprocessed_map[preprocess(alias)] = canonical

    return exact_map, preprocessed_map


def normalize_terms(
    values: list[str], taxonomy: dict, section: str
) -> NormalizationResult:
    """Normalize terms: exact match first, then preprocessed fallback."""
    exact_map, preprocessed_map = build_alias_map(taxonomy, section)

    normalized = []
    changes = []
    unknown = []
    seen = set()
    dupes = 0

    for val in values:
        canonical = exact_map.get(val.lower())  # exact match
        if not canonical:
            canonical = preprocessed_map.get(preprocess(val))  # preprocessed

        if canonical:
            if canonical in seen:
                dupes += 1
                continue
            normalized.append(canonical)
            seen.add(canonical)
            if val != canonical:
                changes.append(f"{val} -> {canonical}")
        else:
            if val in seen:
                dupes += 1
                continue
            normalized.append(val)
            seen.add(val)
            unknown.append(val)

    return NormalizationResult(
        normalized=normalized,
        changes=changes,
        unknown=unknown,
        duplicates_removed=dupes,
    )


def apply_term_normalization(text: str, taxonomy: dict) -> str:
    """Apply simple find-replace normalization to text."""
    for old, new in taxonomy.get("term_normalization", {}).items():
        text = text.replace(old, new)
    return text


def calculate_valid_to(
    domains: list[str], base_date: date, taxonomy: dict
) -> date | None:
    """Auto-calculate valid_to from domain + validity matrix.

    Uses the SHORTEST validity period among all domains.
    Returns None if all domains have null validity (no expiry).
    """
    matrix = taxonomy.get("validity_matrix", {})
    periods = [matrix[d] for d in domains if matrix.get(d) is not None]
    if not periods:
        return None
    return base_date + timedelta(days=min(periods))


def normalize_frontmatter(
    data: dict, taxonomy: dict | None = None
) -> tuple[dict, list[str], list[str]]:
    """Normalize all taxonomy-controlled fields in frontmatter dict.

    Returns: (normalized_data, all_changes, all_unknown_terms)
    """
    taxonomy = taxonomy or load_taxonomy()
    all_changes = []
    all_unknown = []

    # Normalize topics
    if "topics" in data and data["topics"]:
        result = normalize_terms(data["topics"], taxonomy, "topics")
        data["topics"] = result.normalized
        all_changes.extend(result.changes)
        all_unknown.extend(result.unknown)

    # Normalize products
    if "products" in data and data["products"]:
        result = normalize_terms(data["products"], taxonomy, "products")
        data["products"] = result.normalized
        all_changes.extend(result.changes)
        all_unknown.extend(result.unknown)

    # Normalize domains
    if "domains" in data and data["domains"]:
        result = normalize_terms(data["domains"], taxonomy, "domains")
        data["domains"] = result.normalized
        all_changes.extend(result.changes)
        all_unknown.extend(result.unknown)

    # Auto-calculate valid_to if not manually set
    if "valid_to" not in data or data.get("valid_to") is None:
        if data.get("domains"):
            note_date = data.get("date", date.today())
            if isinstance(note_date, str):
                note_date = date.fromisoformat(note_date)
            data["valid_to"] = calculate_valid_to(data["domains"], note_date, taxonomy)

    # Apply term normalization to text fields
    for field in ["title", "summary"]:
        if field in data and isinstance(data[field], str):
            data[field] = apply_term_normalization(data[field], taxonomy)

    # Enforce caps
    caps = taxonomy.get("caps", {})
    for field, cap in caps.items():
        if field in data and isinstance(data[field], list) and len(data[field]) > cap:
            logger.warning(f"Truncating {field}: {len(data[field])} -> {cap}")
            data[field] = data[field][:cap]

    if all_changes:
        logger.info(f"Normalized: {', '.join(all_changes)}")
    if all_unknown:
        logger.info(f"Unknown terms (not in taxonomy): {all_unknown}")

    return data, all_changes, all_unknown
