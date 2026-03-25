"""Magistrala classifier produces valid type codes and destinations."""

from corp_by_os.ingest.naming_config import get_type_code, load_naming_config


def test_all_type_codes_are_uppercase():
    config = load_naming_config()
    for code in config["type_codes"]:
        assert code == code.upper(), f"Type code {code} not uppercase"


def test_all_client_aliases_are_uppercase():
    config = load_naming_config()
    for alias in config["client_aliases"]:
        assert alias == alias.upper(), f"Client alias {alias} not uppercase"


def test_known_filename_patterns_classify():
    """Known RFI/VA/Workshop patterns get correct type codes."""
    assert get_type_code(None, "Digital Property RFI - Transport.docx") == "RFI"
    assert get_type_code(None, "JLR_VA Questionnaire.xlsx") == "VA"
    assert get_type_code(None, "Workshop Feb 2026.pptx") in ("MEET", "WORK")
    assert get_type_code("presentation", "overview.pptx") == "PRES"


def test_type_codes_have_labels():
    """Every type code has a non-empty label."""
    config = load_naming_config()
    for code, spec in config["type_codes"].items():
        assert spec.get("label"), f"Type code {code} missing label"
