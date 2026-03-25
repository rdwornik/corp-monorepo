"""Property-based tests using Hypothesis.

Tests that core functions hold invariants across arbitrary inputs, not just
hand-picked examples. Focuses on crash-freedom and semantic invariants.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Strategy helpers
# ---------------------------------------------------------------------------

# Filenames: printable ASCII, no path separators, non-empty
_filename_chars = st.characters(
    whitelist_categories=("Lu", "Ll", "Nd"),
    whitelist_characters=" _-.",
)
_filename_st = st.text(_filename_chars, min_size=1, max_size=60).map(str.strip).filter(bool)

# Simple word-like terms (letters + digits, no spaces) — safe for regex use
_word_st = st.from_regex(r"[A-Za-z][A-Za-z0-9]{1,12}", fullmatch=True)

_ROOT = Path("/fake/project")

# ---------------------------------------------------------------------------
# 1. CPE classifier: never crashes on any filename
# ---------------------------------------------------------------------------


@given(filename=_filename_st, ext=st.sampled_from([".docx", ".pptx", ".xlsx", ".pdf", ".csv", ".txt", ""]))
@settings(max_examples=200)
def test_cpe_classify_file_never_crashes(filename, ext):
    """classify_file must not raise for any filename + extension combination."""
    from corp_project_extractor.classifier import classify_file

    file_path = _ROOT / f"{filename}{ext}"
    result = classify_file(file_path, _ROOT)
    assert result is not None


# ---------------------------------------------------------------------------
# 2. CPE classifier: result always has valid structure
# ---------------------------------------------------------------------------


@given(filename=_filename_st, ext=st.sampled_from([".docx", ".pptx", ".xlsx", ".pdf", ".csv", ""]))
@settings(max_examples=150)
def test_cpe_classify_file_always_returns_valid_classification(filename, ext):
    """Every Classification result satisfies the structural contract."""
    from corp_project_extractor.classifier import DOC_ROLES, classify_file

    file_path = _ROOT / f"{filename}{ext}"
    r = classify_file(file_path, _ROOT)

    assert r.category in DOC_ROLES, f"Unknown category: {r.category}"
    assert r.doc_role in ("source_of_truth", "supporting", "obsolete"), (
        f"Unknown doc_role: {r.doc_role}"
    )
    assert 0.0 <= r.confidence <= 1.0, f"Confidence out of range: {r.confidence}"
    assert r.reason, "reason must be non-empty"
    assert isinstance(r.is_junk, bool)
    # is_junk must match category
    assert r.is_junk == (r.category == "Junk"), (
        f"is_junk={r.is_junk} inconsistent with category={r.category}"
    )


# ---------------------------------------------------------------------------
# 3. corp-by-os clean_description: never crashes, never returns empty
# ---------------------------------------------------------------------------


@given(stem=st.text(min_size=0, max_size=200))
@settings(max_examples=300)
def test_clean_description_never_crashes_and_never_returns_empty(stem):
    """clean_description must return a non-empty string for any input."""
    from corp_by_os.ingest.naming_config import clean_description, load_naming_config

    load_naming_config.cache_clear()
    result = clean_description(stem)

    assert isinstance(result, str), "result must be a str"
    assert result, f"result must not be empty (input={stem!r})"


# ---------------------------------------------------------------------------
# 4. RFP anonymize → deanonymize roundtrip
# ---------------------------------------------------------------------------

# Terms: non-empty words, no regex metacharacters (re.escape handles them,
# but we keep tests simple by avoiding edge cases in replacement logic)
_term_st = st.from_regex(r"[A-Za-z][A-Za-z0-9]{2,15}", fullmatch=True)
_terms_st = st.lists(_term_st, min_size=1, max_size=3, unique=True)

CORE_BLOCKLIST = "corp_rfp_agent.anonymization.core.get_blocklist"
CORE_SESSION = "corp_rfp_agent.anonymization.core.get_session"
_DEFAULT_SESSION = {"customer_name": "", "placeholder": "[CUSTOMER]"}


@given(terms=_terms_st, extra=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")), min_size=0, max_size=80))
@settings(max_examples=150)
def test_rfp_anonymize_deanonymize_roundtrip(terms, extra):
    """anonymize followed by deanonymize restores all replaced terms."""
    from corp_rfp_agent.anonymization.core import anonymize, deanonymize

    # Build input text that definitely contains each term as a whole word
    text = " ".join(terms) + " " + extra

    with patch(CORE_BLOCKLIST, return_value=terms), patch(
        CORE_SESSION, return_value=_DEFAULT_SESSION
    ):
        anon_text, mapping = anonymize(text)

    # Each term in the mapping must not appear in the anonymized text
    for placeholder, original in mapping.items():
        assert original not in anon_text, (
            f"Term {original!r} still visible after anonymize"
        )
        assert placeholder in anon_text, (
            f"Placeholder {placeholder!r} missing from anonymized text"
        )

    # Roundtrip: deanonymize should restore original terms
    with patch(CORE_SESSION, return_value=_DEFAULT_SESSION):
        restored = deanonymize(anon_text, mapping)

    for original in mapping.values():
        assert original in restored, (
            f"Term {original!r} not restored after deanonymize"
        )


# ---------------------------------------------------------------------------
# 5. RFP anonymize: mapping keys are always valid placeholders
# ---------------------------------------------------------------------------


@given(terms=_terms_st)
@settings(max_examples=100)
def test_rfp_anonymize_placeholders_are_well_formed(terms):
    """Every placeholder in the mapping follows the [CUSTOMER*] naming scheme."""
    from corp_rfp_agent.anonymization.core import anonymize

    text = " ".join(terms)

    with patch(CORE_BLOCKLIST, return_value=terms), patch(
        CORE_SESSION, return_value=_DEFAULT_SESSION
    ):
        _, mapping = anonymize(text)

    for placeholder in mapping:
        assert placeholder.startswith("[CUSTOMER"), (
            f"Placeholder {placeholder!r} does not start with [CUSTOMER"
        )
        assert placeholder.endswith("]"), (
            f"Placeholder {placeholder!r} does not end with ]"
        )
