"""
Validation and quarantine routing for note frontmatter.
"""

import logging
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from corp.schema.folder_names import QUARANTINE

from .models import Confidentiality, NoteFrontmatter

logger = logging.getLogger(__name__)


class ValidationResult(str, Enum):
    VALID = "valid"  # write to vault
    WARNINGS = "warnings"  # write to vault with warnings logged
    QUARANTINE = "quarantine"  # write to _quarantine/


_SCHEMA_PATH = Path(__file__).parent / "data" / "schema.yaml"


@lru_cache(maxsize=1)
def _load_schema() -> dict[str, Any]:
    with open(_SCHEMA_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def validate_against_schema(data: dict[str, Any]) -> list[str]:
    """Warn-only check against schema.yaml contract.

    Never blocks — returns a list of warning strings (empty if clean).
    Complements Pydantic validation: catches unknown fields, cardinality
    violations, and allowed-value mismatches that Pydantic would silently
    coerce or ignore.
    """
    schema = _load_schema()
    warnings: list[str] = []

    required = set(schema.get("required_fields", []))
    optional = set(schema.get("optional_fields", []))
    known_fields = required | optional
    allowed_values: dict[str, list[str]] = schema.get("allowed_values", {})
    cardinality: dict[str, dict[str, int]] = schema.get("cardinality", {})

    # Missing required fields
    for field in required:
        if not data.get(field):
            warnings.append(f"missing required field: {field!r}")

    # Unknown fields (not in required + optional) — helps catch schema drift
    for key in data:
        if key not in known_fields:
            warnings.append(f"unknown field: {key!r}")

    # Allowed-value checks
    for field, allowed in allowed_values.items():
        val = data.get(field)
        if val is not None and str(val) not in allowed:
            warnings.append(f"field {field!r} has unexpected value {val!r} (allowed: {allowed})")

    # Cardinality checks
    for field, limits in cardinality.items():
        val = data.get(field)
        if isinstance(val, list):
            max_len = limits.get("max")
            if max_len is not None and len(val) > max_len:
                warnings.append(f"field {field!r} has {len(val)} items (max {max_len})")

    return warnings


def validate_frontmatter(
    data: dict,
) -> tuple[ValidationResult, NoteFrontmatter | None, list[str]]:
    """Validate frontmatter dict against schema.

    Returns: (result_status, parsed_model_or_None, list_of_issues)
    """
    issues = []

    try:
        note = NoteFrontmatter(**data)
    except ValidationError as e:
        issues = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        logger.warning(f"Validation failed: {issues}")
        return ValidationResult.QUARANTINE, None, issues

    # Check for warnings (non-fatal)
    if not note.topics:
        issues.append("No topics extracted — note may be hard to find in graph")
    if not note.summary:
        issues.append("No summary — note may lack context")
    if not note.domains:
        issues.append("No domains — note won't appear in domain queries")
    if note.confidentiality == Confidentiality.CONFIDENTIAL and not note.client:
        issues.append("Confidential note without client name")

    if issues:
        note.validation_warnings = issues
        return ValidationResult.WARNINGS, note, issues

    return ValidationResult.VALID, note, []


def get_output_path(
    base_vault_dir: Path,
    note_filename: str,
    validation_result: ValidationResult,
) -> Path:
    """Determine where to write the note based on validation result."""
    if validation_result == ValidationResult.QUARANTINE:
        return base_vault_dir / QUARANTINE / note_filename
    return base_vault_dir / note_filename


def generate_links_line(note: NoteFrontmatter) -> str:
    """Generate deterministic Links line from validated frontmatter."""
    parts = []
    for topic in note.topics:
        parts.append(f"[[{topic}]]")
    for product in note.products:
        parts.append(f"[[{product}]]")
    for person in note.people:
        name = person.split("(")[0].strip()
        parts.append(f"[[{name}]]")
    return "**Links:** " + " . ".join(parts) if parts else ""
