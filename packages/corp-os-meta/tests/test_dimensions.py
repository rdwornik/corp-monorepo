"""Tests for knowledge dimension schema and normalization."""

from datetime import date, timedelta

from corp_os_meta import NoteFrontmatter, ValidationResult, validate_frontmatter
from corp_os_meta.models import (
    SCHEMA_VERSION,
    Authority,
    Confidentiality,
    Layer,
    SourceType,
)
from corp_os_meta.normalize import (
    calculate_valid_to,
    load_taxonomy,
    normalize_frontmatter,
    normalize_terms,
)


class TestSchema:
    def test_schema_version_is_2(self):
        assert SCHEMA_VERSION == 2

    def test_defaults_for_backward_compatibility(self):
        """Existing v1 notes should validate with defaults for new fields."""
        note = NoteFrontmatter(
            title="Old Note",
            date=date(2026, 2, 1),
            type="presentation",
            source_tool="knowledge-extractor",
            source_file="test.mkv",
        )
        assert note.confidentiality == Confidentiality.INTERNAL
        assert note.authority == Authority.TRIBAL
        assert note.layer == Layer.LEARNING
        assert note.source_type == SourceType.DOCUMENTATION
        assert note.domains == []
        assert note.schema_version == 2

    def test_full_v2_note(self):
        note = NoteFrontmatter(
            title="Lenzing WMS Requirements",
            date=date(2026, 3, 1),
            type="rfp",
            topics=["WMS", "Demand Planning"],
            products=["Blue Yonder WMS"],
            people=["Karthik"],
            domains=["Product", "Delivery & Implementation"],
            source_type="opportunity",
            layer="operational",
            confidentiality="confidential",
            authority="approved",
            client="Lenzing AG",
            project="Lenzing_Planning",
            source_tool="project-extractor",
            source_file="lenzing_rfp.pdf",
            valid_to=date(2026, 9, 1),
            summary="WMS requirements for Lenzing SIOP implementation.",
        )
        assert note.client == "Lenzing AG"
        assert note.confidentiality == Confidentiality.CONFIDENTIAL
        assert len(note.domains) == 2

    def test_domain_cap_at_3(self):
        note = NoteFrontmatter(
            title="Test",
            date=date(2026, 1, 1),
            type="document",
            domains=["Product", "Competitive", "Commercials"],
            source_tool="test",
            source_file="test.md",
        )
        assert len(note.domains) == 3


class TestDomainNormalization:
    def test_domain_alias_resolution(self):
        taxonomy = load_taxonomy()
        result = normalize_terms(["GTM", "pricing", "CS"], taxonomy, "domains")
        assert "Go-to-Market" in result.normalized
        assert "Commercials" in result.normalized
        assert "Customer Success" in result.normalized

    def test_domain_dedup(self):
        taxonomy = load_taxonomy()
        result = normalize_terms(["GTM", "Go-to-Market", "sales"], taxonomy, "domains")
        assert result.normalized.count("Go-to-Market") == 1

    def test_unknown_domain(self):
        taxonomy = load_taxonomy()
        result = normalize_terms(["Quantum Physics"], taxonomy, "domains")
        assert "Quantum Physics" in result.unknown


class TestTemporalValidity:
    def test_commercials_90_days(self):
        taxonomy = load_taxonomy()
        base = date(2026, 3, 1)
        valid_to = calculate_valid_to(["Commercials"], base, taxonomy)
        assert valid_to == base + timedelta(days=90)

    def test_shortest_period_wins(self):
        """When note has multiple domains, use shortest validity."""
        taxonomy = load_taxonomy()
        base = date(2026, 3, 1)
        valid_to = calculate_valid_to(["Commercials", "Product"], base, taxonomy)
        assert valid_to == base + timedelta(days=90)

    def test_stable_domain_no_expiry(self):
        taxonomy = load_taxonomy()
        base = date(2026, 3, 1)
        valid_to = calculate_valid_to(["Industry & Supply Chain"], base, taxonomy)
        assert valid_to is None

    def test_mixed_stable_and_volatile(self):
        """If one domain has expiry and another doesn't, use the expiry."""
        taxonomy = load_taxonomy()
        base = date(2026, 3, 1)
        valid_to = calculate_valid_to(
            ["Industry & Supply Chain", "Competitive"], base, taxonomy
        )
        assert valid_to == base + timedelta(days=90)

    def test_auto_calculation_in_normalize(self):
        """normalize_frontmatter should auto-calculate valid_to."""
        taxonomy = load_taxonomy()
        data = {
            "title": "Pricing Update",
            "date": date(2026, 3, 1),
            "domains": ["Commercials"],
            "topics": [],
            "products": [],
        }
        normalized, _, _ = normalize_frontmatter(data, taxonomy)
        assert normalized["valid_to"] == date(2026, 3, 1) + timedelta(days=90)


class TestValidation:
    def test_confidential_without_client_warns(self):
        data = {
            "title": "Secret Note",
            "date": date(2026, 1, 1),
            "type": "document",
            "confidentiality": "confidential",
            "source_tool": "test",
            "source_file": "test.md",
            "summary": "Something confidential.",
            "topics": ["SLA"],
            "domains": ["Product"],
        }
        result, note, issues = validate_frontmatter(data)
        assert result == ValidationResult.WARNINGS
        assert any("client" in i.lower() for i in issues)

    def test_valid_v2_note(self):
        data = {
            "title": "Test",
            "date": date(2026, 1, 1),
            "type": "presentation",
            "topics": ["SLA"],
            "domains": ["Product"],
            "summary": "Test note.",
            "confidentiality": "internal",
            "source_tool": "test",
            "source_file": "test.md",
        }
        result, note, issues = validate_frontmatter(data)
        assert result == ValidationResult.VALID
