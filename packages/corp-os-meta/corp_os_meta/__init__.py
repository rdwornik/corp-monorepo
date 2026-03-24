"""corp_os_meta — Shared metadata schema for corp-by-os agent ecosystem."""

from .models import (
    SCHEMA_VERSION,
    Authority,
    Confidentiality,
    DocumentType,
    DomainEnum,
    Layer,
    NoteFrontmatter,
    QualityLevel,
    SourceType,
)
from .normalize import load_taxonomy, normalize_frontmatter, normalize_terms
from .overlays import (
    OVERLAY_MAP,
    ArchitectureOverlay,
    CommercialOverlay,
    MeetingOverlay,
    RFPOverlay,
    SecurityOverlay,
)
from .products import (
    classify_source_tier,
    expand_product_query,
    get_children,
    get_parent,
    get_product_display_name,
    get_source_reliability,
    is_platform_service,
    resolve_product_key,
)
from .utils import parse_llm_json
from .validate import (
    ValidationResult,
    generate_links_line,
    get_output_path,
    validate_frontmatter,
)

__all__ = [
    "NoteFrontmatter",
    "DocumentType",
    "SourceType",
    "Layer",
    "Confidentiality",
    "Authority",
    "DomainEnum",
    "QualityLevel",
    "SCHEMA_VERSION",
    "normalize_frontmatter",
    "load_taxonomy",
    "normalize_terms",
    "validate_frontmatter",
    "ValidationResult",
    "get_output_path",
    "generate_links_line",
    "parse_llm_json",
    "resolve_product_key",
    "get_product_display_name",
    "is_platform_service",
    "get_source_reliability",
    "classify_source_tier",
    "get_parent",
    "get_children",
    "expand_product_query",
    "ArchitectureOverlay",
    "SecurityOverlay",
    "CommercialOverlay",
    "RFPOverlay",
    "MeetingOverlay",
    "OVERLAY_MAP",
]
