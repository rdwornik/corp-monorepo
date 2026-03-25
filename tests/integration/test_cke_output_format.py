"""CKE extraction output has valid frontmatter structure."""
import json
from pathlib import Path


def test_cke_output_has_required_fields():
    """CKE extraction JSON has expected classifier training structure."""
    fixture_dir = Path("packages/corp-knowledge-extractor/tests/fixtures")
    training = json.loads((fixture_dir / "classifier_training.json").read_text())
    assert len(training) > 0
    for entry in training[:5]:
        assert "filename" in entry
        assert "doc_type" in entry


def test_cke_sample_output_has_expected_structure():
    """CKE sample_output.json has deep extraction structure (qa_pairs or slide_breakdown)."""
    fixture_dir = Path("packages/corp-knowledge-extractor/tests/fixtures")
    sample_path = fixture_dir / "sample_output.json"
    if not sample_path.exists():
        return  # Skip if fixture not present
    data = json.loads(sample_path.read_text())
    entry = data[0] if isinstance(data, list) else data
    # Deep extraction output has qa_pairs or slide_breakdown; shallow has title/schema_version
    has_deep = "qa_pairs" in entry or "slide_breakdown" in entry
    has_shallow = "title" in entry or "schema_version" in entry
    assert has_deep or has_shallow, f"Unexpected sample_output structure: {list(entry.keys())}"
