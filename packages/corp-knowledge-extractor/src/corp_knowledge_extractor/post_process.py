"""
Post-processor for extraction results.
Delegates to corp_os_meta for normalization, validation, and link generation.
Adds CKE-specific logic: unknown term logging to local file.
"""

import functools
import logging
import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field

from corp_os_meta import (
    normalize_frontmatter,
    validate_frontmatter,
    generate_links_line,
    ValidationResult,
)
from corp_os_meta.models import NoteFrontmatter
from corp_os_meta.normalize import load_taxonomy
from corp_knowledge_extractor.utils import normalize_string_list

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data file loading (cached)
# ---------------------------------------------------------------------------


def _data_dir() -> Path:
    """Data files live alongside the package source code."""
    return Path(__file__).parent / "data"


@functools.lru_cache(maxsize=1)
def _load_product_exclusions() -> set[str]:
    """Load product exclusion list (competitors, infrastructure, generic)."""
    path = _data_dir() / "product_exclusions.yaml"
    if not path.exists():
        return set()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    excluded = set()
    for category in data.values():
        if isinstance(category, list):
            excluded.update(name.lower() for name in category)
    return excluded


@functools.lru_cache(maxsize=1)
def _load_product_aliases() -> dict[str, str]:
    """Load product alias mapping (case-insensitive lookup)."""
    path = _data_dir() / "product_aliases.yaml"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {k.lower(): v for k, v in data.get("aliases", {}).items()}


@functools.lru_cache(maxsize=1)
def _load_client_aliases() -> dict[str, str]:
    """Load client alias mapping (case-insensitive lookup)."""
    path = _data_dir() / "client_aliases.yaml"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {k.lower(): v for k, v in data.get("aliases", {}).items()}


# ---------------------------------------------------------------------------
# Type enforcement
# ---------------------------------------------------------------------------


def enforce_type_from_extension(result: dict, source_path: str) -> dict:
    """Override content type based on file extension.

    File extension is the ground truth for document type — LLM classification
    can misidentify DOCX/XLSX as "presentation" etc.
    """
    ext = Path(source_path).suffix.lower()
    TYPE_MAP = {
        ".docx": "document",
        ".xlsx": "spreadsheet",
        ".csv": "spreadsheet",
        ".pdf": "document",
        ".pptx": "presentation",
        ".mp4": "presentation",
        ".mkv": "presentation",
        ".avi": "presentation",
    }
    if ext in TYPE_MAP:
        result["content_type"] = TYPE_MAP[ext]
        if "type" in result:
            result["type"] = TYPE_MAP[ext]
    return result


def normalize_company_names(text: str) -> str:
    """Fix known LLM company name duplications."""
    if not text:
        return text
    text = re.sub(r"(?i)\b(Blue\s+){2,}Yonder\b", "Blue Yonder", text)
    return text


# ---------------------------------------------------------------------------
# Fix 1: Product exclusion (competitors, infrastructure, generic)
# ---------------------------------------------------------------------------


def filter_products(products: list[str]) -> tuple[list[str], list[str]]:
    """Split products into real BY products and excluded entities.

    Returns (real_products, excluded_entities). Excluded items are
    reclassified to entities_mentioned, not lost.
    """
    exclusions = _load_product_exclusions()
    real_products = []
    entities = []
    for p in products:
        if p.lower().strip() in exclusions:
            entities.append(p)
        else:
            real_products.append(p)
    return real_products, entities


# ---------------------------------------------------------------------------
# Fix 2: Product name normalization (alias mapping from YAML)
# ---------------------------------------------------------------------------

# Inline fallback for when YAML file is missing (tests, standalone)
_BUILTIN_PRODUCT_ALIASES = {
    "demand planning": "Blue Yonder Demand Planning",
    "supply planning": "Blue Yonder Supply Planning",
    "control tower": "Blue Yonder Control Tower",
    "wms": "Blue Yonder WMS",
    "tms": "Blue Yonder TMS",
    "oms": "Blue Yonder OMS",
    "platform": "Blue Yonder Platform",
}


def normalize_product_names(products: list[str]) -> list[str]:
    """Normalize short product names to canonical Blue Yonder forms.

    Applied after corp-os-meta normalization to catch remaining short forms.
    Deduplicates: ["Demand Planning", "Blue Yonder Demand Planning"] → ["Blue Yonder Demand Planning"]
    """
    alias_map = _load_product_aliases() or _BUILTIN_PRODUCT_ALIASES
    result = []
    seen: set[str] = set()
    for p in products:
        canonical = alias_map.get(p.strip().lower(), p)
        if canonical.lower() not in seen:
            result.append(canonical)
            seen.add(canonical.lower())
    return result


# ---------------------------------------------------------------------------
# Fix 3: People field cleanup (filter roles and organizations)
# ---------------------------------------------------------------------------

ROLE_PATTERNS = [
    re.compile(r"(?i)^(technical |senior |chief |lead |head of |director |manager |vp |vice president)"),
    re.compile(
        r"(?i)(manager|director|officer|engineer|architect|consultant|analyst|specialist|coordinator|executive|administrator)$"
    ),
    re.compile(r"(?i)^(customer |project |account |solution |support |sales )"),
]

ORG_PATTERNS = [
    re.compile(r"(?i)(inc\.|corp\.|ltd\.|gmbh|ag$|sa$|plc$|llc$|group$|company$)"),
    re.compile(r"(?i)^(blue yonder|lenzing|pepsico|jaguar|jlr|michelin|sap|oracle)$"),
]

# Words that look like names but are actually role/modifier words
_ROLE_WORDS = {
    "technical",
    "senior",
    "chief",
    "lead",
    "head",
    "director",
    "manager",
    "vice",
    "president",
    "customer",
    "project",
    "account",
    "solution",
    "support",
    "sales",
    "supply",
    "chain",
    "global",
    "regional",
    "general",
}

# Short uppercase tokens that are org suffixes, not name parts
_ORG_SUFFIXES = {"ag", "sa", "plc", "llc", "inc", "ltd", "gmbh", "corp"}


def _has_person_name(text: str) -> bool:
    """Check if text contains a likely real person name.

    Requires at least two capitalized words where at least one is NOT
    a common role/modifier word or org suffix.
    """
    words = text.split()
    cap_words = [w for w in words if w[0:1].isupper() and len(w) > 1]
    if len(cap_words) < 2:
        return False
    non_role = [w for w in cap_words if w.lower() not in _ROLE_WORDS and w.lower().rstrip(".") not in _ORG_SUFFIXES]
    return len(non_role) >= 2


def filter_people(people: list[str]) -> tuple[list[str], list[str]]:
    """Separate real people from roles and organizations.

    Returns (real_people, filtered_out).
    """
    real_people = []
    filtered = []
    for person in people:
        clean = person.split("(")[0].strip()
        is_role = any(p.search(clean) for p in ROLE_PATTERNS)
        is_org = any(p.search(clean) for p in ORG_PATTERNS)
        has_name = _has_person_name(clean)

        if is_org and not has_name:
            filtered.append(person)
        elif is_role and not has_name:
            filtered.append(person)
        else:
            real_people.append(person)
    return real_people, filtered


# ---------------------------------------------------------------------------
# Fix 4: Client alias normalization
# ---------------------------------------------------------------------------


def normalize_client(client: str) -> str:
    """Normalize client name using alias mapping."""
    if not client:
        return client
    aliases = _load_client_aliases()
    return aliases.get(client.lower().strip(), client)


@dataclass
class PostProcessResult:
    """Result of post-processing with metadata about what changed."""

    data: dict
    links_line: str
    validation_result: ValidationResult
    validated_note: NoteFrontmatter | None
    changes: list[str] = field(default_factory=list)
    unknown_terms: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


def post_process_extraction(
    raw_result: dict,
    source_tool: str = "knowledge-extractor",
    source_file: str = "",
    client: str | None = None,
    project: str | None = None,
) -> PostProcessResult:
    """Apply corp-os-meta normalization and validation to raw extraction result.

    Args:
        raw_result: Raw dict from Gemini extraction (parsed JSON)
        source_tool: Tool identifier for frontmatter
        source_file: Original file path/name
        client: Override client from manifest (takes precedence over Gemini)
        project: Override project from manifest (takes precedence over Gemini)

    Returns:
        PostProcessResult with normalized data, links line, and validation status
    """
    # Ensure required fields for corp-os-meta
    raw_result.setdefault("source_tool", source_tool)
    raw_result.setdefault("source_file", source_file)
    raw_result.setdefault("schema_version", 2)

    # Manifest-provided client/project override Gemini's guess
    if client:
        raw_result["client"] = client
    if project:
        raw_result["project"] = project

    # Map CKE field names to corp-os-meta field names if needed
    if "content_type" in raw_result and "type" not in raw_result:
        raw_result["type"] = raw_result.pop("content_type")

    # Map Gemini quality values to schema enum (full|partial|fragment)
    _quality_map = {"high": "full", "medium": "partial", "low": "fragment"}
    if "quality" in raw_result:
        raw_result["quality"] = _quality_map.get(raw_result["quality"], raw_result["quality"])

    # Schema v2 defaults — safe values if LLM didn't produce them
    raw_result.setdefault("confidentiality", "internal")
    raw_result.setdefault("authority", "tribal")
    raw_result.setdefault("layer", "learning")
    raw_result.setdefault("source_type", "documentation")
    raw_result.setdefault("domains", [])

    # Normalize list fields: LLMs sometimes return dicts instead of strings
    for list_field in ("topics", "products", "people", "domains"):
        if list_field in raw_result and isinstance(raw_result[list_field], list):
            raw_result[list_field] = normalize_string_list(raw_result[list_field])

    # Fix duplicated company names (Gemini sometimes doubles "Blue Yonder")
    for str_field in ("title", "summary"):
        val = raw_result.get(str_field, "")
        if val:
            raw_result[str_field] = normalize_company_names(val)

    # Normalize using corp-os-meta taxonomy
    taxonomy = load_taxonomy()
    normalized_data, changes, unknown = normalize_frontmatter(raw_result, taxonomy)

    # Apply company name normalization after corp-os-meta (it may copy raw strings)
    for str_field in ("title", "summary"):
        val = normalized_data.get(str_field, "")
        if val:
            normalized_data[str_field] = normalize_company_names(val)

    # Normalize short product names to canonical Blue Yonder forms
    if "products" in normalized_data and isinstance(normalized_data["products"], list):
        normalized_data["products"] = normalize_product_names(normalized_data["products"])

    # Filter out competitors, infrastructure, and generic terms from products
    if "products" in normalized_data and isinstance(normalized_data["products"], list):
        real_products, excluded = filter_products(normalized_data["products"])
        normalized_data["products"] = real_products
        if excluded:
            existing = normalized_data.get("entities_mentioned", [])
            normalized_data["entities_mentioned"] = existing + excluded
            logger.info("Moved non-BY products to entities_mentioned: %s", excluded)

    # Filter roles and organizations from people
    if "people" in normalized_data and isinstance(normalized_data["people"], list):
        real_people, filtered_out = filter_people(normalized_data["people"])
        normalized_data["people"] = real_people
        if filtered_out:
            logger.info("Filtered non-person entries from people: %s", filtered_out)

    # Normalize client aliases
    if normalized_data.get("client"):
        normalized_data["client"] = normalize_client(normalized_data["client"])

    if changes:
        logger.info("Normalized: %s", ", ".join(changes))
    if unknown:
        logger.info("Unknown terms: %s", unknown)
        _log_unknown_terms(unknown)

    # Enforce type from file extension (overrides LLM classification)
    if source_file:
        normalized_data = enforce_type_from_extension(normalized_data, source_file)

    # Validate using corp-os-meta
    validation_result, validated_note, issues = validate_frontmatter(normalized_data)

    if issues:
        logger.warning("Validation issues: %s", issues)

    # Generate deterministic links line
    links_line = ""
    if validated_note:
        links_line = generate_links_line(validated_note)
    else:
        # Quarantined — still generate links from raw data for the note
        links_parts = []
        for topic in normalize_string_list(normalized_data.get("topics") or []):
            links_parts.append(f"[[{topic}]]")
        for product in normalize_string_list(normalized_data.get("products") or []):
            links_parts.append(f"[[{product}]]")
        for person in normalize_string_list(normalized_data.get("people") or []):
            name = person.split("(")[0].strip()
            links_parts.append(f"[[{name}]]")
        links_line = "**Links:** " + " . ".join(links_parts) if links_parts else ""

    return PostProcessResult(
        data=normalized_data,
        links_line=links_line,
        validation_result=validation_result,
        validated_note=validated_note,
        changes=changes,
        unknown_terms=unknown,
        issues=issues,
    )


def _normalize_tag(value: str) -> str:
    """Normalize tag value: lowercase, hyphens, strip special chars."""
    tag = value.lower()
    tag = tag.replace("&", "").replace("_", "-").replace(" ", "-")
    tag = re.sub(r"[^a-z0-9\-/]", "", tag)
    tag = re.sub(r"-+", "-", tag).strip("-")
    return tag


MAX_TAGS = 12


def generate_tags(frontmatter: dict, max_tags: int = MAX_TAGS) -> list[str]:
    """Generate hierarchical tags from frontmatter fields.

    Tags are priority-ordered: client > product > topic > domain > type > source.
    Capped at max_tags (default 12) to reduce noise.
    """
    tags = []

    # Client first (highest priority — scoping context)
    client = frontmatter.get("client")
    if client:
        tags.append(f"client/{_normalize_tag(client)}")

    for product in frontmatter.get("products") or []:
        tags.append(f"product/{_normalize_tag(product)}")

    for topic in frontmatter.get("topics") or []:
        tags.append(f"topic/{_normalize_tag(topic)}")

    for domain in frontmatter.get("domains") or []:
        tags.append(f"domain/{_normalize_tag(domain)}")

    doc_type = frontmatter.get("doc_type")
    if doc_type:
        tags.append(f"type/{_normalize_tag(doc_type)}")

    source_type = frontmatter.get("source_type")
    if source_type:
        tags.append(f"source/{_normalize_tag(source_type)}")

    # Deduplicate preserving order
    seen: set[str] = set()
    deduped = [t for t in tags if not (t in seen or seen.add(t))]

    return cap_tags(deduped, max_tags)


def cap_tags(tags: list[str], max_tags: int = MAX_TAGS) -> list[str]:
    """Keep most informative tags, cap at max_tags.

    Tags are already in priority order from generate_tags().
    """
    return tags[:max_tags]


# BY product short-forms and legacy names → canonical taxonomy slugs.
# Used in validate_tags to recognise known aliases without requiring normalisation.
_TAG_ALIASES: dict[str, str] = {
    # Core BY product short forms
    "product/wms": "product/blue-yonder-wms",
    "product/tms": "product/blue-yonder-tms",
    "product/oms": "product/blue-yonder-oms",
    "product/demand-planning": "product/blue-yonder-demand-planning",
    "product/demand-planning-module": "product/blue-yonder-demand-planning",
    "product/demand-planning-tool": "product/blue-yonder-demand-planning",
    "product/demand-supply-planning-dsp": "product/blue-yonder-demand-planning",
    "product/demand-and-supply-planning": "product/blue-yonder-demand-planning",
    "product/dsp": "product/blue-yonder-demand-planning",
    "product/idsp-integrated-demand-supply-inventory-planning": "product/blue-yonder-demand-planning",
    "product/supply-planning": "product/blue-yonder-supply-planning",
    "product/supply-planning-platform": "product/blue-yonder-supply-planning",
    "product/supply-planning-solution": "product/blue-yonder-supply-planning",
    "product/control-tower": "product/blue-yonder-control-tower",
    "product/platform": "product/blue-yonder-platform",
    "product/platform-data-cloud": "product/blue-yonder-platform",
    "product/platform-demand-planning-module": "product/blue-yonder-platform",
    "product/platform-demand-planning-supply-planning-allocation-replenishment": "product/blue-yonder-platform",
    "product/platform-sop": "product/blue-yonder-platform",
    "product/platform-supply-planning-module": "product/blue-yonder-platform",
    "product/supply-chain-planning-platform": "product/blue-yonder-platform",
    "product/supply-chain-platform": "product/blue-yonder-platform",
    "product/sop-platform": "product/blue-yonder-platform",
    "product/sop-module": "product/blue-yonder-supply-planning",
    "product/network-design": "product/blue-yonder-network-design",
    "product/transportation-modeling": "product/blue-yonder-tms",
    # IBP / S&OP platform variants (all refer to BY Platform capability)
    "product/integrated-business-planning": "product/blue-yonder-platform",
    "product/integrated-business-planning-ibp": "product/blue-yonder-platform",
    "product/integrated-planning-tool": "product/blue-yonder-platform",
    "product/ibp": "product/blue-yonder-platform",
    "product/sales-operations-planning": "product/blue-yonder-supply-planning",
    "product/siop-sales-inventory-operations-planning-tool": "product/blue-yonder-supply-planning",
    # JDA = legacy Blue Yonder brand name (pre-2020 acquisition)
    "product/jda": "product/blue-yonder-platform",
    "product/jda-platform": "product/blue-yonder-platform",
    "product/jda-sop": "product/blue-yonder-supply-planning",
    "product/jda-supply-chain-planning-system": "product/blue-yonder-platform",
    "product/jda-tactical-planning": "product/blue-yonder-supply-planning",
}


def validate_tags(tags: list[str]) -> list[dict]:
    """Validate tags against corp-os-meta taxonomy.

    Returns list of {"tag": str, "valid": bool, "reason": str}.
    All tags are kept regardless of validity — this is informational only.
    """
    try:
        taxonomy = load_taxonomy()
    except Exception:
        logger.warning("Could not load taxonomy, skipping tag validation")
        return [{"tag": t, "valid": True, "reason": "unvalidated"} for t in tags]

    VALID_PREFIXES = {"product/", "topic/", "domain/", "client/", "type/", "source/"}

    results = []
    for tag in tags:
        # Check prefix
        prefix_valid = any(tag.startswith(p) for p in VALID_PREFIXES)
        if not prefix_valid:
            logger.warning("Tag with unknown prefix: %s", tag)
            results.append({"tag": tag, "valid": False, "reason": "unknown_prefix"})
            continue

        # Resolve known aliases to canonical form before taxonomy lookup
        canonical = _TAG_ALIASES.get(tag, tag)
        prefix, _, value = canonical.partition("/")

        # Check value against taxonomy known values
        known_values = _get_known_values(taxonomy, prefix)
        if known_values and value not in known_values:
            logger.warning("Tag value not in taxonomy: %s", tag)
            results.append({"tag": tag, "valid": True, "reason": "unvalidated"})
        else:
            results.append({"tag": tag, "valid": True, "reason": "validated"})

    return results


def _get_known_values(taxonomy: dict, prefix: str) -> set:
    """Get known normalized values for a tag prefix from taxonomy."""
    TAXONOMY_MAP = {
        "product": "products",
        "topic": "topics",
        "domain": "domains",
        "client": "clients",
        "type": "document_types",
        "source": "source_types",
    }
    key = TAXONOMY_MAP.get(prefix, "")
    values = taxonomy.get(key, [])
    if isinstance(values, list):
        result = set()
        for v in values:
            if isinstance(v, dict):
                result.add(_normalize_tag(v.get("name", "")))
            elif isinstance(v, str):
                result.add(_normalize_tag(v))
        return result
    return set()


def _log_unknown_terms(terms: list[str]):
    """Append unknown terms to local review file for batch approval."""
    from corp_knowledge_extractor._paths import CONFIG_DIR

    review_path = CONFIG_DIR / "taxonomy_review.yaml"
    data = {"pending": []}
    if review_path.exists():
        with open(review_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {"pending": []}

    existing = set(data.get("pending", []))
    added = []
    for term in terms:
        if term not in existing:
            data["pending"].append(term)
            added.append(term)

    if added:
        with open(review_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        logger.info("Added to taxonomy_review.yaml: %s", added)
