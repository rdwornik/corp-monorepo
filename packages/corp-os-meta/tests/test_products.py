"""Tests for product key resolution and source reliability."""

from corp_os_meta.products import (
    classify_source_tier,
    expand_product_query,
    get_children,
    get_parent,
    get_product_display_name,
    get_source_reliability,
    is_platform_service,
    resolve_product_key,
)

# ── Product resolution ──────────────────────────────────────────


def test_resolve_exact_match():
    assert resolve_product_key("Blue Yonder WMS") == "wms"


def test_resolve_case_insensitive():
    assert resolve_product_key("blue yonder wms") == "wms"


def test_resolve_variant():
    assert resolve_product_key("WMS Classic") == "wms_classic"


def test_resolve_variant_native():
    assert resolve_product_key("Platform Native Warehouse Management") == "wms_native"


def test_resolve_platform_service():
    assert resolve_product_key("Analytics") == "analytics"


def test_resolve_bare_wms():
    assert resolve_product_key("WMS") == "wms"


def test_resolve_bare_platform():
    assert resolve_product_key("Platform") == "platform"


def test_resolve_bare_control_tower():
    assert resolve_product_key("Control Tower") == "control_tower"


def test_resolve_unknown():
    assert resolve_product_key("Nonexistent Product") is None


def test_resolve_fuzzy():
    """Close match still resolves."""
    assert resolve_product_key("BY WMS") == "wms"


def test_resolve_fuzzy_warehouse_management():
    """Fuzzy: 'Warehouse Management' resolves to wms."""
    assert resolve_product_key("Warehouse Management") == "wms"


# ── Alias resolution ──────────────────────────────────────────


def test_alias_planning():
    assert resolve_product_key("planning") == "demand_planning"


def test_alias_logistics():
    assert resolve_product_key("logistics") == "tms"


def test_alias_catman():
    assert resolve_product_key("catman") == "category_management"


def test_alias_commerce():
    assert resolve_product_key("commerce") == "oms"


def test_alias_scp():
    assert resolve_product_key("scp") == "supply_planning"


# ── Sub-product resolution ─────────────────────────────────────


def test_resolve_sub_product_key():
    """Sub-product keys resolve to themselves."""
    assert resolve_product_key("wms_billing") == "wms_billing"


def test_resolve_sub_product_logistics():
    assert resolve_product_key("logistics_carrier") == "logistics_carrier"


# ── Parent lookup ──────────────────────────────────────────────


def test_get_parent_wms_billing():
    assert get_parent("wms_billing") == "wms"


def test_get_parent_logistics_carrier():
    assert get_parent("logistics_carrier") == "tms"


def test_get_parent_top_level():
    """Top-level products have no parent."""
    assert get_parent("wms") is None


def test_get_parent_unknown():
    assert get_parent("nonexistent") is None


# ── Children lookup ────────────────────────────────────────────


def test_get_children_wms():
    children = get_children("wms")
    assert "wms_native" in children
    assert "wms_billing" in children
    assert "wms_labor" in children
    assert "wms_robotics" in children
    assert "wms_tasking" in children
    assert "flexis_other" in children
    assert "flexis_slotting" in children
    assert len(children) == 7


def test_get_children_tms():
    children = get_children("tms")
    assert "logistics_carrier" in children
    assert "logistics_load" in children
    assert len(children) == 7


def test_get_children_no_children():
    """Products with no sub-products return empty list."""
    assert get_children("analytics") == []


# ── Query expansion ────────────────────────────────────────────


def test_expand_product_query_wms():
    expanded = expand_product_query("wms")
    assert expanded[0] == "wms"
    assert "wms_billing" in expanded
    assert "wms_native" in expanded
    assert len(expanded) == 8  # wms + 7 children


def test_expand_product_query_leaf():
    """Leaf products expand to just themselves."""
    expanded = expand_product_query("analytics")
    assert expanded == ["analytics"]


def test_expand_product_query_demand_planning():
    expanded = expand_product_query("demand_planning")
    assert expanded[0] == "demand_planning"
    assert "planning_ibp" in expanded
    assert "retail_demand_edge" in expanded
    assert len(expanded) == 10  # demand_planning + 9 children


# ── Display names ───────────────────────────────────────────────


def test_display_name():
    assert get_product_display_name("wms") == "Blue Yonder WMS"


def test_display_name_variant():
    assert get_product_display_name("wms_classic") == "WMS Classic"


def test_display_name_unknown():
    assert get_product_display_name("nonexistent") is None


# ── Platform service ────────────────────────────────────────────


def test_is_platform_service_true():
    assert is_platform_service("analytics") is True


def test_is_platform_service_false():
    assert is_platform_service("wms") is False


def test_is_platform_service_unknown():
    assert is_platform_service("nonexistent") is False


# ── Source reliability ──────────────────────────────────────────


def test_reliability_official():
    assert get_source_reliability("official_architecture_doc") == 1.0


def test_reliability_sales():
    assert get_source_reliability("sales_deck") == 0.4


def test_reliability_unknown():
    assert get_source_reliability("unknown_tier") == 0.1


# ── Source classification ───────────────────────────────────────


def test_classify_architecture_doc():
    assert (
        classify_source_tier("BYPlatform-Architecture.pdf")
        == "official_architecture_doc"
    )


def test_classify_training():
    assert (
        classify_source_tier("Module_1.pptx", source_type="training")
        == "training_material"
    )


def test_classify_release_notes():
    assert classify_source_tier("Release_Notes_v3.pdf") == "release_notes"


def test_classify_sales_deck():
    assert (
        classify_source_tier("Q4_Sales_Deck.pptx", source_type="presentation")
        == "sales_deck"
    )


def test_classify_fallback_source_type():
    """source_type mapping used when no filename pattern matches."""
    assert (
        classify_source_tier("random_file.pdf", source_type="training")
        == "training_material"
    )
