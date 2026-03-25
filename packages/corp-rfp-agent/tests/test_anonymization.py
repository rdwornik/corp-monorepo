"""Tests for anonymization/core.py and anonymization/middleware.py.

All tests patch get_blocklist() and get_session() so they never touch the real
anonymization.yaml or session state.
"""

from __future__ import annotations

from unittest.mock import patch


# Patch targets — core.py imports from .config, so patch at the usage site
CORE_BLOCKLIST = "corp_rfp_agent.anonymization.core.get_blocklist"
CORE_SESSION = "corp_rfp_agent.anonymization.core.get_session"

DEFAULT_SESSION = {"customer_name": "", "placeholder": "[CUSTOMER]"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patch(blocklist: list[str], session: dict | None = None):
    """Context-manager pair: patch blocklist + session for core.py."""
    s = session or DEFAULT_SESSION
    return (
        patch(CORE_BLOCKLIST, return_value=blocklist),
        patch(CORE_SESSION, return_value=s),
    )


# ---------------------------------------------------------------------------
# core.anonymize — basic cases
# ---------------------------------------------------------------------------


def test_anonymize_empty_string_returns_unchanged():
    from corp_rfp_agent.anonymization.core import anonymize

    with patch(CORE_BLOCKLIST, return_value=["Acme"]), patch(
        CORE_SESSION, return_value=DEFAULT_SESSION
    ):
        text, mapping = anonymize("")
    assert text == ""
    assert mapping == {}


def test_anonymize_no_match_returns_original_text():
    from corp_rfp_agent.anonymization.core import anonymize

    bl_patch, sess_patch = _patch(["Acme"])
    with bl_patch, sess_patch:
        text, mapping = anonymize("Hello Blue Yonder world")

    assert text == "Hello Blue Yonder world"
    assert mapping == {}


def test_anonymize_single_term_replaces_with_placeholder():
    from corp_rfp_agent.anonymization.core import anonymize

    bl_patch, sess_patch = _patch(["Acme"])
    with bl_patch, sess_patch:
        text, mapping = anonymize("Acme needs WMS integration")

    assert "Acme" not in text
    assert "[CUSTOMER]" in text
    assert mapping["[CUSTOMER]"] == "Acme"


def test_anonymize_two_terms_get_numbered_placeholders():
    from corp_rfp_agent.anonymization.core import anonymize

    bl_patch, sess_patch = _patch(["Acme", "GlobalCorp"])
    with bl_patch, sess_patch:
        text, mapping = anonymize("Acme and GlobalCorp both need WMS")

    # Both should be replaced and each gets a unique numbered placeholder
    assert "Acme" not in text
    assert "GlobalCorp" not in text
    assert len(mapping) == 2
    placeholders = list(mapping.keys())
    # Numbered form: [CUSTOMER_1], [CUSTOMER_2]
    assert all("_1" in p or "_2" in p for p in placeholders)


def test_anonymize_case_insensitive():
    from corp_rfp_agent.anonymization.core import anonymize

    bl_patch, sess_patch = _patch(["Acme"])
    with bl_patch, sess_patch:
        text, mapping = anonymize("acme needs help with ACME system")

    assert "acme" not in text.lower()
    assert len(mapping) == 1


def test_anonymize_word_boundary_no_partial_match():
    """'Acme' should NOT replace inside 'AcmeCorp' — word boundary \b applies."""
    from corp_rfp_agent.anonymization.core import anonymize

    bl_patch, sess_patch = _patch(["Acme"])
    with bl_patch, sess_patch:
        text, mapping = anonymize("AcmeCorp is our client")

    # \b between 'e' and 'C' in 'AcmeCorp' is NOT a boundary (both \w)
    assert "AcmeCorp" in text
    assert mapping == {}


def test_anonymize_empty_blocklist_is_passthrough():
    from corp_rfp_agent.anonymization.core import anonymize

    bl_patch, sess_patch = _patch([])
    with bl_patch, sess_patch:
        text, mapping = anonymize("Acme needs help")

    assert text == "Acme needs help"
    assert mapping == {}


def test_anonymize_blank_term_in_blocklist_skipped():
    from corp_rfp_agent.anonymization.core import anonymize

    bl_patch, sess_patch = _patch(["", "Acme", ""])
    with bl_patch, sess_patch:
        text, mapping = anonymize("Acme is the client")

    # Blank entries are skipped; Acme still replaced
    assert "Acme" not in text
    assert len(mapping) == 1


# ---------------------------------------------------------------------------
# core.deanonymize
# ---------------------------------------------------------------------------


def test_deanonymize_empty_string_returns_unchanged():
    from corp_rfp_agent.anonymization.core import deanonymize

    with patch(CORE_SESSION, return_value=DEFAULT_SESSION):
        result = deanonymize("")
    assert result == ""


def test_deanonymize_mapping_restores_original():
    from corp_rfp_agent.anonymization.core import deanonymize

    mapping = {"[CUSTOMER]": "Acme"}
    with patch(CORE_SESSION, return_value=DEFAULT_SESSION):
        result = deanonymize("[CUSTOMER] needs WMS", mapping)

    assert result == "Acme needs WMS"


def test_deanonymize_without_mapping_uses_session_customer():
    from corp_rfp_agent.anonymization.core import deanonymize

    session = {"customer_name": "GlobalCorp", "placeholder": "[CUSTOMER]"}
    with patch(CORE_SESSION, return_value=session):
        result = deanonymize("[CUSTOMER] needs WMS")

    assert result == "GlobalCorp needs WMS"


def test_deanonymize_no_placeholder_in_text_unchanged():
    from corp_rfp_agent.anonymization.core import deanonymize

    mapping = {"[CUSTOMER]": "Acme"}
    with patch(CORE_SESSION, return_value=DEFAULT_SESSION):
        result = deanonymize("Blue Yonder supports WMS", mapping)

    assert result == "Blue Yonder supports WMS"


def test_deanonymize_numbered_placeholders_restored():
    from corp_rfp_agent.anonymization.core import deanonymize

    mapping = {"[CUSTOMER_1]": "Acme", "[CUSTOMER_2]": "GlobalCorp"}
    with patch(CORE_SESSION, return_value=DEFAULT_SESSION):
        result = deanonymize("[CUSTOMER_1] and [CUSTOMER_2] both use WMS", mapping)

    assert result == "Acme and GlobalCorp both use WMS"


# ---------------------------------------------------------------------------
# core.check
# ---------------------------------------------------------------------------


def test_check_empty_text_returns_empty_list():
    from corp_rfp_agent.anonymization.core import check

    with patch(CORE_BLOCKLIST, return_value=["Acme"]):
        result = check("")
    assert result == []


def test_check_returns_found_terms():
    from corp_rfp_agent.anonymization.core import check

    with patch(CORE_BLOCKLIST, return_value=["Acme", "GlobalCorp"]):
        result = check("Acme needs WMS")

    assert "Acme" in result
    assert "GlobalCorp" not in result


def test_check_multiple_occurrences_all_reported():
    from corp_rfp_agent.anonymization.core import check

    with patch(CORE_BLOCKLIST, return_value=["Acme"]):
        result = check("Acme asked about Acme licensing")

    assert len(result) == 2


def test_check_no_terms_found_returns_empty_list():
    from corp_rfp_agent.anonymization.core import check

    with patch(CORE_BLOCKLIST, return_value=["Acme"]):
        result = check("Blue Yonder provides the solution")

    assert result == []


def test_check_does_not_modify_text():
    """check() is read-only — original text untouched."""
    from corp_rfp_agent.anonymization.core import check

    original = "Acme needs WMS integration"
    with patch(CORE_BLOCKLIST, return_value=["Acme"]):
        check(original)

    assert original == "Acme needs WMS integration"


# ---------------------------------------------------------------------------
# middleware.AnonymizationMiddleware
# ---------------------------------------------------------------------------


def test_middleware_before_returns_anonymized_text_and_context():
    from corp_rfp_agent.anonymization.middleware import AnonymizationMiddleware

    mw = AnonymizationMiddleware(enabled=True)
    bl_patch, sess_patch = _patch(["Acme"])
    with bl_patch, sess_patch:
        clean, ctx = mw.before("Acme needs WMS")

    assert "Acme" not in clean
    assert "mapping" in ctx
    assert "original" in ctx
    assert ctx["original"] == "Acme needs WMS"


def test_middleware_after_restores_original_term():
    from corp_rfp_agent.anonymization.middleware import AnonymizationMiddleware

    mw = AnonymizationMiddleware(enabled=True)
    bl_patch, sess_patch = _patch(["Acme"])
    with bl_patch, sess_patch:
        clean, ctx = mw.before("Acme needs WMS")

    with patch(CORE_SESSION, return_value=DEFAULT_SESSION):
        final = mw.after(f"{clean} and more context", ctx)

    assert "Acme" in final
    assert "[CUSTOMER]" not in final


def test_middleware_before_disabled_is_passthrough():
    from corp_rfp_agent.anonymization.middleware import AnonymizationMiddleware

    mw = AnonymizationMiddleware(enabled=False)
    text, ctx = mw.before("Acme needs WMS")

    assert text == "Acme needs WMS"
    assert ctx == {}


def test_middleware_after_disabled_is_passthrough():
    from corp_rfp_agent.anonymization.middleware import AnonymizationMiddleware

    mw = AnonymizationMiddleware(enabled=False)
    result = mw.after("some llm answer [CUSTOMER]", {"mapping": {"[CUSTOMER]": "Acme"}})

    assert result == "some llm answer [CUSTOMER]"


def test_middleware_after_empty_context_is_passthrough():
    from corp_rfp_agent.anonymization.middleware import AnonymizationMiddleware

    mw = AnonymizationMiddleware(enabled=True)
    result = mw.after("answer with [CUSTOMER]", {})

    # empty context → no deanonymization
    assert result == "answer with [CUSTOMER]"


def test_middleware_roundtrip_preserves_semantics():
    """before() + after() round-trip: final answer has original client name restored."""
    from corp_rfp_agent.anonymization.middleware import AnonymizationMiddleware

    mw = AnonymizationMiddleware(enabled=True)
    question = "What WMS features does Acme need?"

    bl_patch, sess_patch = _patch(["Acme"])
    with bl_patch, sess_patch:
        clean_q, ctx = mw.before(question)

    # Simulate LLM echoing the placeholder back
    llm_answer = clean_q.replace("need?", "need? Blue Yonder can help.")

    with patch(CORE_SESSION, return_value=DEFAULT_SESSION):
        final = mw.after(llm_answer, ctx)

    assert "Acme" in final
    assert "[CUSTOMER]" not in final


def test_middleware_no_blocklist_terms_round_trip_unchanged():
    """When no terms match, before+after leaves text identical."""
    from corp_rfp_agent.anonymization.middleware import AnonymizationMiddleware

    mw = AnonymizationMiddleware(enabled=True)
    question = "What does Blue Yonder offer for WMS?"

    bl_patch, sess_patch = _patch(["Acme"])
    with bl_patch, sess_patch:
        clean_q, ctx = mw.before(question)

    assert clean_q == question
    assert ctx["mapping"] == {}
