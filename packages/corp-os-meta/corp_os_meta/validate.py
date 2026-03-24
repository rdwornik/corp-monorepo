"""
Validation and quarantine routing for note frontmatter.
"""

import logging
from enum import Enum
from pathlib import Path

from pydantic import ValidationError

from .models import Confidentiality, NoteFrontmatter

logger = logging.getLogger(__name__)


class ValidationResult(str, Enum):
    VALID = "valid"  # write to vault
    WARNINGS = "warnings"  # write to vault with warnings logged
    QUARANTINE = "quarantine"  # write to _quarantine/


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
        return base_vault_dir / "_quarantine" / note_filename
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
