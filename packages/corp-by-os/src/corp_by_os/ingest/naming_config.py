"""Load and cache naming configuration (Decision #14).

Provides type code resolution, client alias lookup, and description
cleaning from naming_config.yaml.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parents[3] / "config" / "naming_config.yaml"


@lru_cache(maxsize=1)
def load_naming_config() -> dict:
    """Load naming_config.yaml with caching."""
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(f"naming_config.yaml not found at {_CONFIG_PATH}")
    return yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8"))


def get_type_code(
    doc_type: str | None = None,
    filename: str = "",
    source_category: str | None = None,
) -> str:
    """Get type code from filename hints, doc_type, or source_category.

    Priority: filename_hint > doc_type > source_category fallback > MISC
    """
    config = load_naming_config()
    type_codes = config["type_codes"]
    filename_lower = filename.lower()

    # 1. Filename hints (most specific — e.g., "RFI" in filename → RFI, not RFP)
    for code, spec in type_codes.items():
        hint = spec.get("filename_hint")
        if hint and re.search(hint, filename_lower):
            return code

    # 2. doc_type mapping (from CKE classifier or extraction result)
    if doc_type:
        for code, spec in type_codes.items():
            if spec.get("doc_type") == doc_type:
                return code

    # 3. source_category from content_registry metadata (backward compat)
    if source_category:
        # Map old source_category values to new type codes
        _LEGACY_MAP = {
            "training": "TRAIN",
            "product_doc": "PROD",
            "competitive": "COMP",
            "rfp": "RFP",
            "security_compliance": "SEC",
            "meeting": "MEET",
            "demo": "DEMO",
            "architecture": "ARCH",
            "brand": "PRES",
        }
        if source_category in _LEGACY_MAP:
            return _LEGACY_MAP[source_category]

    return config["fallback"]["unknown_type"]


def get_client_variants(client_name: str) -> list[str]:
    """Get all known name variants for a client (alias-aware matching).

    Given "JLR" or "Jaguar Land Rover", returns every name in the same
    alias group from naming_config.yaml. Used by the retrieval engine so
    that searching for "JLR" also matches notes tagged "Jaguar Land Rover".

    Falls back to [client_name] when no alias group is found.
    """
    config = load_naming_config()
    client_lower = client_name.lower().strip()

    for names in config["client_aliases"].values():
        names_lower = [n.lower() for n in names]
        if client_lower in names_lower:
            return list(names)

    return [client_name]


def get_client_alias(client_name: str | None) -> str:
    """Get short client alias from full name.

    Returns configured alias if found, auto-generated 5-char code otherwise,
    or fallback for None.
    """
    config = load_naming_config()

    if not client_name:
        return config["fallback"]["unknown_client"]

    client_lower = client_name.lower().strip()
    # Also try the first part before underscore (classifier gives "Lenzing_Planning")
    client_first = client_lower.split("_")[0]

    for alias, names in config["client_aliases"].items():
        names_lower = [n.lower() for n in names]
        if client_lower in names_lower or client_first in names_lower:
            return alias

    # Auto-generate: first 5 chars uppercase, strip non-alpha
    auto = re.sub(r"[^A-Za-z]", "", client_name)[:5].upper()
    return auto or config["fallback"]["unknown_client"]


def clean_description(original_stem: str) -> str:
    """Clean filename stem into description component.

    Strips special chars, removes noise words, truncates at word boundary.
    """
    config = load_naming_config()
    rules = config["description_rules"]

    # Strip special chars (keep letters, digits, spaces, underscores)
    desc = re.sub(rules["strip_pattern"], " ", original_stem)

    # Split, remove noise words, rejoin
    words = desc.split()
    noise = set(rules.get("noise_words", []))
    words = [w for w in words if w not in noise and w.strip()]

    separator = rules["word_separator"]
    result = separator.join(words)

    # Truncate at word boundary
    max_len = rules["max_length"]
    if len(result) > max_len:
        result = result[:max_len].rsplit(separator, 1)[0]

    return result or "Untitled"
