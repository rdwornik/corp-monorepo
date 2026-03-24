"""Tests for taxonomy normalization."""

from corp_os_meta.normalize import load_taxonomy, normalize_frontmatter, normalize_terms


def test_alias_resolution():
    taxonomy = load_taxonomy()
    result = normalize_terms(["DR", "SLAs"], taxonomy, "topics")
    assert "Disaster Recovery" in result.normalized
    assert "SLA" in result.normalized
    assert len(result.changes) == 2


def test_deduplication():
    taxonomy = load_taxonomy()
    result = normalize_terms(
        ["DR", "Disaster Recovery", "disaster recovery planning"], taxonomy, "topics"
    )
    assert result.normalized.count("Disaster Recovery") == 1
    assert result.duplicates_removed == 2


def test_unknown_terms_preserved():
    taxonomy = load_taxonomy()
    result = normalize_terms(["Brand New Concept"], taxonomy, "topics")
    assert "Brand New Concept" in result.normalized
    assert "Brand New Concept" in result.unknown


def test_product_normalization():
    taxonomy = load_taxonomy()
    result = normalize_terms(["BY WMS", "Azure"], taxonomy, "products")
    assert "Blue Yonder WMS" in result.normalized
    assert "Azure" in result.normalized


def test_full_frontmatter_normalization():
    taxonomy = load_taxonomy()
    data = {
        "title": "Yonder SaaS Overview",
        "topics": ["DR", "TAM"],
        "products": ["BY Platform"],
    }
    normalized, changes, unknown = normalize_frontmatter(data, taxonomy)
    assert normalized["title"] == "Blue Yonder SaaS Overview"
    assert "Disaster Recovery" in normalized["topics"]
    assert "Blue Yonder Platform" in normalized["products"]
