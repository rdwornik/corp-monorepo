"""
Pydantic models defining the frontmatter contract for all corporate-os notes.
Schema version 2: adds knowledge dimensions (domains, layers, confidentiality, authority, temporal validity).
"""

import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = 2


class DocumentType(str, Enum):
    PRESENTATION = "presentation"
    MEETING = "meeting"
    TRAINING = "training"
    DEMO = "demo"
    WORKSHOP = "workshop"
    RFP = "rfp"
    CONTRACT = "contract"
    EMAIL = "email"
    NOTES = "notes"
    DOCUMENT = "document"
    REPORT = "report"
    TUTORIAL = "tutorial"
    SECURITY_QUESTIONNAIRE = "security_questionnaire"
    SPREADSHEET = "spreadsheet"
    VENDOR_ASSESSMENT = "vendor_assessment"
    DISCOVERY = "discovery"


class SourceType(str, Enum):
    OPPORTUNITY = "opportunity"
    RFP = "rfp"
    MEETING = "meeting"
    TRAINING = "training"
    DOCUMENTATION = "documentation"
    RELEASE_NOTE = "release_note"
    RESEARCH = "research"
    INTERNAL_UPDATE = "internal_update"


class Layer(str, Enum):
    OPERATIONAL = "operational"
    LEARNING = "learning"
    REFERENCE = "reference"


class Confidentiality(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class Authority(str, Enum):
    AUTHORITATIVE = "authoritative"
    APPROVED = "approved"
    TRIBAL = "tribal"


class QualityLevel(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    FRAGMENT = "fragment"


class DomainEnum(str, Enum):
    PRODUCT = "Product"
    PLATFORM_ARCHITECTURE = "Platform & Architecture"
    DELIVERY_IMPLEMENTATION = "Delivery & Implementation"
    CUSTOMER_SUCCESS = "Customer Success"
    GO_TO_MARKET = "Go-to-Market"
    COMMERCIALS = "Commercials"
    COMPETITIVE = "Competitive"
    INDUSTRY_SUPPLY_CHAIN = "Industry & Supply Chain"


class NoteFrontmatter(BaseModel):
    """Required and optional frontmatter fields for all corporate-os notes.

    Schema v2: Knowledge dimensions for personal business mastery.
    Every tool must produce frontmatter that validates against this model.
    Tool-specific fields go in tool_meta.
    """

    # ── Required ──────────────────────────────────────────────────
    title: str
    date: Optional[datetime.date] = None
    type: DocumentType
    topics: list[str] = Field(default_factory=list, max_length=8)
    schema_version: int = SCHEMA_VERSION
    source_tool: str
    source_file: str

    # ── Knowledge Dimensions (v2) ─────────────────────────────────
    source_type: SourceType = SourceType.DOCUMENTATION
    layer: Layer = Layer.LEARNING
    domains: list[str] = Field(default_factory=list, max_length=3)
    confidentiality: Confidentiality = Confidentiality.INTERNAL
    authority: Authority = Authority.TRIBAL

    # ── Temporal Validity (v2) ────────────────────────────────────
    valid_to: Optional[datetime.date] = None
    last_verified: Optional[datetime.date] = None

    # ── Context ───────────────────────────────────────────────────
    products: list[str] = Field(default_factory=list, max_length=4)
    people: list[str] = Field(default_factory=list, max_length=3)
    client: str | None = None
    project: str | None = None

    # ── Standard Optional ─────────────────────────────────────────
    language: str = "en"
    quality: QualityLevel = QualityLevel.FULL
    summary: str | None = None
    duration_min: int | None = None
    model: str | None = None
    tokens_used: int | None = None
    confidence: float | None = None
    trust_level: str | None = None
    """Content trust level: 'verified' | 'extracted' | 'generated' | 'draft' | None (legacy)."""

    tags: list[str] = Field(default_factory=list)

    # ── Deep Extraction (v2.2) ───────────────────────────────────
    extraction_version: int | None = None
    """1 = legacy shallow, 2 = structured deep"""

    depth: str | None = None
    """'standard' or 'deep'"""

    doc_type: str | None = None
    """Document classification for overlay selection: architecture, security, commercial, etc."""

    key_facts: list[str] | None = None
    """Specific, citable facts extracted from the document."""

    entities_mentioned: list[str] | None = None
    """Companies, products, people mentioned in the document."""

    needs_review: bool | None = None
    """True if extraction confidence is low and human review is recommended."""

    # ── Freshness Tracking (v2.2) ──────────────────────────────────
    source_path: str | None = None
    """Canonical path to the source file."""

    source_hash: str | None = None
    """SHA-256 hash of the source file."""

    source_mtime: str | None = None
    """File modification time in ISO 8601 format."""

    extracted_at: str | None = None
    """Extraction timestamp in ISO 8601 format."""

    # ── Content Routing & Provenance (v2.1) ────────────────────────
    content_origin: str | None = None
    """Where the source file lives: 'mywork', 'onedrive', 'sharepoint'"""

    source_category: str | None = None
    """Content classification. Values managed by routing_map.yaml, not enforced here."""

    source_locator: str | None = None
    """Canonical path to source file, e.g. '30_Templates/01_Presentation_Decks/Platform_Overview.pptx'"""

    routing_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    """Classification confidence 0.0-1.0. 1.0 = manually placed, <1.0 = auto-classified"""

    # ── Tool-specific namespace ───────────────────────────────────
    tool_meta: dict[str, Any] = Field(default_factory=dict)

    # ── Validation metadata ───────────────────────────────────────
    validation_warnings: list[str] = Field(default_factory=list, exclude=True)
