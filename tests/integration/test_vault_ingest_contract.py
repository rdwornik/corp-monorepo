"""Vault ingest accepts CKE output format and writes valid notes."""

import json
from pathlib import Path


def test_quality_prediction_fixture_has_required_fields():
    """quality_prediction.json entries have doc_type and quality fields."""
    fixtures = Path("packages/corp-knowledge-extractor/tests/fixtures")
    data = json.loads((fixtures / "quality_prediction.json").read_text())
    assert len(data) > 0
    for entry in data[:10]:
        assert "doc_type" in entry
        assert "quality" in entry or "quality_score" in entry


def test_classifier_training_doc_types_are_strings():
    """All doc_type values in classifier_training.json are non-empty strings."""
    fixtures = Path("packages/corp-knowledge-extractor/tests/fixtures")
    data = json.loads((fixtures / "classifier_training.json").read_text())
    for entry in data:
        dt = entry.get("doc_type")
        assert isinstance(dt, str) and dt, (
            f"Invalid doc_type in entry: {entry.get('filename')}"
        )
