"""Deterministic document type classifier.

Classifies files into doc_types based on folder path and filename patterns.
Does NOT use LLM — pure rules. Fast and free.

doc_type determines extraction depth:
- "architecture", "security", "commercial", "product_doc" -> deep extraction
- "rfp_response" -> deep extraction
- "meeting", "training" -> deep extraction (meeting overlay)
- "general" -> standard extraction (base only)
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Feature flag — set False to disable hybrid TF-IDF and fall back to regex only
USE_TFIDF: bool = True

# Minimum softmax confidence to accept TF-IDF prediction; below this → LLM fallback
TFIDF_CONFIDENCE: float = 0.5

DEEP_DOC_TYPES = {
    "architecture",
    "security",
    "commercial",
    "product_doc",
    "rfp_response",
    "vendor_assessment",
    "discovery",
    "meeting",
    "training",
    "requirements_spec",
    "financial_report",
    "proposal",
    "competitive",
    "workshop",
    "demo",
    "presentation",
}
# master_data is Tier 1 — no deep extraction needed for structured data tables
STANDARD_DOC_TYPES = {"general", "master_data"}

# Filename-based doc_type patterns — checked BEFORE folder/content rules
FILENAME_DOC_TYPE_PATTERNS = [
    # RFP / vendor assessment (highest priority — specific doc types)
    (r"(?i)(RFI|RFP|request.for.(information|proposal))", "rfp_response"),
    (r"(?i)(questionnaire|vendor.assessment|security.assessment|VA\b)", "vendor_assessment"),
    # Security (before training — SOC2/ISO27 certs aren't training materials)
    (r"(?i)(SOC.?[12]|ISO.?27|pentest|vulnerability|encryption|gdpr|compliance.matrix|security.measures?)", "security"),
    # Requirements / specifications
    (r"(?i)(FRS|functional.requirement|user.stor)", "requirements_spec"),
    # Proposals / SOWs
    (r"(?i)(SOW|statement.of.work|PoC.proposal)", "proposal"),
    # Financial / investor docs
    (r"(?i)(annual.report|earnings|financial.report|investor)", "financial_report"),
    # Master data / catalogs (standard depth — no deep extraction)
    (r"(?i)(product.catalog|hierarchy|master.data|item.master|price.list)", "master_data"),
    # Product documentation / technical specs
    (
        r"(?i)(datasheet|user.guide|user.manual|admin.guide|config.guide|release.notes?|changelog|api.reference|technical.reference|spec.sheet|sizing.guide|brand.guide|mapping.matrix|reference.material)",
        "product_doc",
    ),
    # Cognitive content — must precede architecture (Cognitive Shorts/Friday meeting recordings)
    (r"(?i)(cognitive.shorts|cognitive.friday|cognitive.demand)", "training"),
    # Demo-to-Win training packets — must precede demo→presentation rule
    (r"(?i)(demo.?2.?win)", "training"),
    # Security — extended certs/whitepaper (must precede architecture)
    (r"(?i)(iso.?22\d{3}|cyber.?security|security.whitepaper)", "security"),
    # Architecture / technical
    (
        r"(?i)(architecture|technical.overview|system.design|integration.pattern|data.flow|deployment|infrastructure|topology)",
        "architecture",
    ),
    # Competitive
    (r"(?i)(competitive|battlecard|comparison|vs\.)", "competitive"),
    # Training / enablement (expanded)
    (
        r"(?i)(training|enablement|curriculum|course|certification|academy|learning|onboarding|meeting.recording|cognitive.shorts|how.to|guide.for|tutorial|hands.on|lab.exercise|exam\b|quiz\b)",
        "training",
    ),
    # Workshop → meeting (workshops are a type of facilitated meeting)
    (r"(?i)(workshop|lab\b)", "meeting"),
    # Demo / showcase → presentation
    (r"(?i)(demo|demonstration|showcase)", "presentation"),
    # Meeting / debrief (expanded)
    (
        r"(?i)(meeting.notes|minutes|recap|debrief|agenda|standup|interview|briefing|timetable|working.session)",
        "meeting",
    ),
    # Commercial / pricing
    (r"(?i)(commercial\b|pricing|quote\b|subscription\b|saas.fee)", "commercial"),
    # Discovery (keep last — "requirements" moved to requirements_spec)
    (r"(?i)(discovery)", "discovery"),
]


def classify_from_filename(filename: str) -> str | None:
    """Pre-classify doc_type from filename patterns.

    Returns doc_type string if a pattern matches, None otherwise.
    """
    for pattern, doc_type in FILENAME_DOC_TYPE_PATTERNS:
        if re.search(pattern, filename):
            return doc_type
    return None


def classify_doc_type_hybrid(
    filename: str,
    content: str = "",
) -> tuple[str | None, float, str]:
    """Classify doc_type using hybrid TF-IDF → regex pipeline.

    Args:
        filename: Bare filename or filename_text feature string.
        content:  Pre-extracted text content (injected by caller — no light_scan import here).
                  Empty string → filename-only prediction.

    Returns:
        (doc_type, confidence, method) where method is "tfidf", "regex", or "none".
        doc_type is None when no classifier fires above threshold (→ caller uses LLM).
    """
    # --- TF-IDF hybrid (primary) ---
    if USE_TFIDF:
        try:
            from corp.extractor.hybrid_loader import (
                get_cached_model,
                predict_hybrid,
            )

            tfidf_fn, tfidf_ct, clf, _meta = get_cached_model()
            pred, conf = predict_hybrid(tfidf_fn, tfidf_ct, clf, filename, content)
            if conf >= TFIDF_CONFIDENCE:
                logger.debug("TF-IDF: %s (conf=%.2f) for %s", pred, conf, filename)
                return pred, conf, "tfidf"
        except FileNotFoundError:
            logger.debug("Hybrid classifier model not found — falling back to regex")
        except Exception as exc:  # pragma: no cover — unexpected sklearn issues
            logger.warning("Hybrid classifier failed (%s) — falling back to regex", exc)

    # --- Regex fallback ---
    regex_pred = classify_from_filename(filename)
    if regex_pred is not None:
        return regex_pred, 1.0, "regex"

    # --- Extension-based type (binary files — no text content to classify) ---
    ext = Path(filename).suffix.lower()
    _EXTENSION_TYPES: dict[str, str] = {
        ".jpg": "image",
        ".jpeg": "image",
        ".png": "image",
        ".gif": "image",
        ".svg": "image",
        ".mp4": "video",
        ".avi": "video",
        ".mov": "video",
        ".zip": "archive",
        ".7z": "archive",
        ".rar": "archive",
    }
    if ext in _EXTENSION_TYPES:
        return _EXTENSION_TYPES[ext], 0.9, "extension"

    return None, 0.0, "none"


def classify_doc_type(filepath: str, folder_context: str | None = None) -> str:
    """Classify a file's doc_type from its path and name.

    Rules (applied in order, first match wins):
    1. Folder path patterns (most reliable)
    2. Filename patterns
    3. Default: "general"
    """
    path_lower = filepath.lower().replace("\\", "/")
    name_lower = Path(filepath).name.lower()

    # --- Filename pattern rules (highest priority) ---
    filename_match = classify_from_filename(Path(filepath).name)
    if filename_match is not None:
        return filename_match

    # --- Folder path rules ---
    if "01_product_docs" in path_lower or "product_docs" in path_lower:
        return "product_doc"
    if "03_competitive" in path_lower:
        return "commercial"
    if "02_training" in path_lower or "training" in path_lower:
        return "training"
    if "certificate" in path_lower or "security" in path_lower or "compliance" in path_lower:
        return "security"
    if "rfp" in path_lower and ("response" in path_lower or "answer" in path_lower or "submission" in path_lower):
        return "rfp_response"
    if "workshop" in path_lower:
        return "workshop"
    if "discovery" in path_lower or "meeting" in path_lower:
        return "meeting"

    # --- Filename rules ---
    if any(kw in name_lower for kw in ["architecture", "platform", "technical"]):
        return "architecture"
    if any(
        kw in name_lower
        for kw in [
            "sla",
            "soc_2",
            "soc2",
            "iso_27001",
            "iso27001",
            "security",
            "whitepaper",
            "gdpr",
        ]
    ):
        return "security"
    if any(kw in name_lower for kw in ["pricing", "commercial", "service_description", "contract"]):
        return "commercial"
    if any(kw in name_lower for kw in ["rfp_response", "rfp_answer", "rfi_response"]):
        return "rfp_response"
    if any(kw in name_lower for kw in ["workshop", "hands_on", "lab"]):
        return "workshop"
    if any(kw in name_lower for kw in ["meeting", "discovery", "notes", "debrief", "recap"]):
        return "meeting"
    if any(kw in name_lower for kw in ["training", "enablement", "bootcamp"]):
        return "training"
    if any(kw in name_lower for kw in ["demo", "demonstration", "showcase"]):
        return "demo"
    if any(kw in name_lower for kw in ["battlecard", "competitive"]):
        return "competitive"

    return "general"


def should_extract_deep(doc_type: str) -> bool:
    """Whether this doc_type warrants deep (overlay) extraction."""
    return doc_type in DEEP_DOC_TYPES
