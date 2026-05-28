"""Tests for cleanup proposer."""

from __future__ import annotations

from pathlib import Path

import yaml

from corp.cleanup.classifier import Classification
from corp.cleanup.proposer import generate_proposals
from corp.cleanup.scanner import FileInfo
from corp.schema.folder_names import INBOX, WORKFLOWS


def _make_classification(name: str, action: str, dest: str, confidence: float) -> Classification:
    """Helper to create a Classification for testing."""
    return Classification(
        file_info=FileInfo(
            path=Path(f"/fake/{name}"),
            name=name,
            extension=Path(name).suffix,
            size_bytes=1024,
            current_folder=INBOX,
            relative_path=f"{INBOX}/{name}",
        ),
        action=action,
        destination_folder=dest,
        proposed_name=name,
        reason="Test reason",
        confidence=confidence,
    )


def test_generate_proposals_yaml(tmp_path):
    """Proposals written as valid YAML with required fields."""
    classifications = [
        _make_classification("a.pptx", "move", f"{WORKFLOWS}/01_Presentation_Decks", 0.9),
        _make_classification("b.log", "delete", "DELETE", 0.8),
        _make_classification("c.txt", "keep", INBOX, 0.5),
    ]

    out = tmp_path / "moves.yaml"
    generate_proposals(classifications, out)

    assert out.exists()
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert "moves" in data
    assert len(data["moves"]) == 3

    # Check required fields on each entry
    for entry in data["moves"]:
        assert "source" in entry
        assert "action" in entry
        assert "destination" in entry
        assert "confidence" in entry
        assert "approved" in entry
        assert entry["approved"] is None  # human fills this in


def test_proposals_sorted_by_confidence(tmp_path):
    """High confidence proposals appear first."""
    classifications = [
        _make_classification("low.txt", "move", "somewhere", 0.3),
        _make_classification("high.pptx", "move", "somewhere", 0.95),
        _make_classification("mid.pdf", "move", "somewhere", 0.7),
    ]

    out = tmp_path / "moves.yaml"
    generate_proposals(classifications, out)

    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    confidences = [e["confidence"] for e in data["moves"]]
    assert confidences == sorted(confidences, reverse=True)


def test_proposals_summary(tmp_path):
    """Summary section has correct counts."""
    classifications = [
        _make_classification("a.pptx", "move", "dest", 0.9),
        _make_classification("b.log", "delete", "DELETE", 0.8),
        _make_classification("c.txt", "keep", INBOX, 0.5),
        _make_classification("d.pptx", "move", "dest", 0.7),
    ]

    out = tmp_path / "moves.yaml"
    generate_proposals(classifications, out)

    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["summary"]["total"] == 4
    assert data["summary"]["moves"] == 2
    assert data["summary"]["deletes"] == 1
    assert data["summary"]["keeps"] == 1
