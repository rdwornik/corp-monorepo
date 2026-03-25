"""corp retrieve returns structured results that RFP agent can parse."""


def test_retrieved_note_has_required_fields():
    """RetrievedNote dataclass has title, content, and relevance_score fields."""
    from corp_by_os.retrieve.engine import RetrievedNote

    assert hasattr(RetrievedNote, "__dataclass_fields__")
    fields = RetrievedNote.__dataclass_fields__
    assert "title" in fields
    assert "content" in fields
    assert "relevance_score" in fields


def test_retrieval_result_has_notes_field():
    """RetrievalResult dataclass has notes collection."""
    from corp_by_os.retrieve.engine import RetrievalResult

    assert hasattr(RetrievalResult, "__dataclass_fields__")
    fields = RetrievalResult.__dataclass_fields__
    assert "notes" in fields


def test_naming_config_type_codes_have_doc_types_or_hints():
    """Every type code (except MISC) has either a doc_type or filename_hint."""
    from corp_by_os.ingest.naming_config import load_naming_config

    config = load_naming_config()
    for code, spec in config["type_codes"].items():
        if code == "MISC":
            continue  # MISC is explicitly the catch-all with no doc_type
        has_anchor = spec.get("doc_type") or spec.get("filename_hint")
        assert has_anchor, f"Type code {code} has neither doc_type nor filename_hint"
