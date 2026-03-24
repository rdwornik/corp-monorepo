"""Tests for preprocessing layer."""

from corp_os_meta.normalize import preprocess, normalize_terms, load_taxonomy


class TestPreprocess:
    def test_parenthetical_removal(self):
        assert (
            preprocess("Service Level Agreements (SLAs)") == "service level agreement"
        )

    def test_casefold(self):
        assert preprocess("Disaster Recovery") == "disaster recovery"

    def test_ampersand_normalization(self):
        assert preprocess("Risk & Compliance") == "risk and compliance"

    def test_whitespace_collapse(self):
        assert preprocess("  Supply   Chain   Planning  ") == "supply chain planning"

    def test_plural_strip_long_term(self):
        assert preprocess("agreements") == "agreement"

    def test_plural_no_strip_short_term(self):
        """Short terms like WMS, TMS should NOT be depluralized."""
        assert preprocess("WMS") == "wms"
        assert preprocess("TMS") == "tms"

    def test_plural_no_strip_double_s(self):
        """Words ending in 'ss' should NOT be stripped."""
        assert preprocess("business") == "business"

    def test_combined(self):
        """All transformations together."""
        assert (
            preprocess("  Service Level Agreements (SLAs)  ")
            == "service level agreement"
        )


class TestPreprocessedMatching:
    def test_sla_with_parenthetical(self):
        """The original failure case: 'Service Level Agreements (SLAs)' should match SLA."""
        taxonomy = load_taxonomy()
        result = normalize_terms(
            ["Service Level Agreements (SLAs)"], taxonomy, "topics"
        )
        assert "SLA" in result.normalized
        assert len(result.unknown) == 0

    def test_exact_match_still_works(self):
        """Exact matching should still take priority."""
        taxonomy = load_taxonomy()
        result = normalize_terms(["DR"], taxonomy, "topics")
        assert "Disaster Recovery" in result.normalized

    def test_plural_variation(self):
        """Plural of known alias should match."""
        taxonomy = load_taxonomy()
        result = normalize_terms(["Service Level Agreements"], taxonomy, "topics")
        assert "SLA" in result.normalized

    def test_genuinely_unknown_term(self):
        """Terms that don't match even after preprocessing stay unknown."""
        taxonomy = load_taxonomy()
        result = normalize_terms(["Quantum Computing"], taxonomy, "topics")
        assert "Quantum Computing" in result.unknown
