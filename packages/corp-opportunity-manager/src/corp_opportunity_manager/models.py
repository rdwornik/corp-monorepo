"""Data models for opportunity management."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


@dataclass
class OpportunityConfig:
    """User input for creating a new opportunity."""

    client: str
    product: str
    contact: str = ""
    stage: str = "discovery"
    topic: str = "Discovery"
    date: date = field(default_factory=date.today)


@dataclass
class ProjectInfo:
    """Metadata about a created project, persisted to project-info.yaml."""

    client: str
    product: str
    contact: str
    stage: str
    created: str
    folder_name: str
    folder_path: str

    def to_yaml_dict(self) -> dict:
        """Return dict suitable for YAML serialization."""
        return {
            "client": self.client,
            "product": self.product,
            "contact": self.contact,
            "stage": self.stage,
            "created": self.created,
            "folder_name": self.folder_name,
        }


@dataclass
class CreationResult:
    """Summary of everything created by `com new`."""

    project_info: ProjectInfo
    folder_path: Path
    deck_path: Path | None
    info_path: Path
    notes_path: Path


# --- Phase 2: Chat agent models ---


@dataclass
class IntentResult:
    """Parsed intent from the LLM."""

    intent: str
    entities: dict[str, str | None]
    response_text: str
    needs_confirmation: bool = False
    confidence: float = 1.0


@dataclass
class StructureIssue:
    """A problem found during folder structure audit."""

    issue_type: str  # missing_folder, non_standard_name, misplaced_file
    path: str
    suggestion: str
