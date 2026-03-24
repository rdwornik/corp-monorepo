"""Tests for deep extraction schema additions (v2.2) and overlay models."""

from datetime import date


from corp_os_meta import (
    DocumentType,
    NoteFrontmatter,
    ArchitectureOverlay,
    SecurityOverlay,
    CommercialOverlay,
    RFPOverlay,
    MeetingOverlay,
    OVERLAY_MAP,
)


# ── Base schema backward compat ──────────────────────────────────


def test_base_schema_backward_compat():
    """Existing notes without v2.2 fields still validate."""
    note = NoteFrontmatter(
        title="Legacy Note",
        date=date(2026, 1, 1),
        type=DocumentType.DOCUMENT,
        topics=["Disaster Recovery"],
        source_tool="knowledge-extractor",
        source_file="test.pdf",
    )
    assert note.extraction_version is None
    assert note.depth is None
    assert note.doc_type is None
    assert note.key_facts is None
    assert note.entities_mentioned is None
    assert note.needs_review is None
    assert note.source_path is None
    assert note.source_hash is None
    assert note.source_mtime is None
    assert note.extracted_at is None


def test_base_schema_with_v2_fields():
    """Notes with extraction_version, depth, doc_type validate."""
    note = NoteFrontmatter(
        title="Deep Note",
        date=date(2026, 3, 14),
        type=DocumentType.DOCUMENT,
        topics=["Platform Architecture"],
        source_tool="knowledge-extractor",
        source_file="architecture.pdf",
        extraction_version=2,
        depth="deep",
        doc_type="architecture",
        key_facts=["System uses PostgreSQL 15", "RPO is 4 hours"],
        entities_mentioned=["Blue Yonder", "SAP"],
        needs_review=False,
    )
    assert note.extraction_version == 2
    assert note.depth == "deep"
    assert note.doc_type == "architecture"
    assert len(note.key_facts) == 2
    assert len(note.entities_mentioned) == 2
    assert note.needs_review is False


def test_freshness_fields():
    """source_path, source_hash, source_mtime, extracted_at validate."""
    note = NoteFrontmatter(
        title="Fresh Note",
        date=date(2026, 3, 14),
        type=DocumentType.DOCUMENT,
        source_tool="knowledge-extractor",
        source_file="test.pdf",
        source_path="C:/Users/docs/test.pdf",
        source_hash="abc123def456" * 5 + "ab",
        source_mtime="2026-03-14T10:30:00",
        extracted_at="2026-03-14T11:00:00",
    )
    assert note.source_path == "C:/Users/docs/test.pdf"
    assert note.source_hash is not None
    assert note.source_mtime == "2026-03-14T10:30:00"
    assert note.extracted_at == "2026-03-14T11:00:00"


# ── Overlay models ───────────────────────────────────────────────


def test_overlays_all_optional():
    """Each overlay validates with all fields None."""
    assert ArchitectureOverlay() is not None
    assert SecurityOverlay() is not None
    assert CommercialOverlay() is not None
    assert RFPOverlay() is not None
    assert MeetingOverlay() is not None


def test_architecture_overlay_populated():
    """Architecture overlay validates with realistic data."""
    overlay = ArchitectureOverlay(
        components=[
            {
                "name": "Order Service",
                "description": "Handles orders",
                "role": "backend",
            },
        ],
        integration_points=[
            {"system": "SAP ERP", "method": "REST API", "protocol": "HTTPS"},
        ],
        data_flow="Events flow from OMS to WMS via Kafka",
        apis=[
            {
                "endpoint": "/api/v2/orders",
                "purpose": "Order CRUD",
                "auth_method": "OAuth2",
            },
        ],
        deployment_model="multi-tenant",
        scalability="Horizontal auto-scaling, 10k orders/min",
        tech_stack=["Java", "Spring Boot", "PostgreSQL", "Kafka"],
        environments="3 environments: dev, staging, prod",
    )
    assert len(overlay.components) == 1
    assert overlay.deployment_model == "multi-tenant"
    assert len(overlay.tech_stack) == 4


def test_security_overlay_populated():
    """Security overlay validates with realistic data."""
    overlay = SecurityOverlay(
        certifications=[
            {"name": "SOC 2 Type II", "status": "current", "expiry": "2027-01-15"},
            {"name": "ISO 27001", "status": "current", "expiry": "2026-12-01"},
        ],
        encryption={"at_rest": "AES-256", "in_transit": "TLS 1.3"},
        data_residency="EU (Frankfurt), US (Virginia)",
        compliance_frameworks=["GDPR", "SOC 2", "ISO 27001"],
        access_control="RBAC with SSO/SAML",
        audit_capabilities="Full audit trail, 7-year retention",
        dr_rto="4 hours",
        dr_rpo="1 hour",
    )
    assert len(overlay.certifications) == 2
    assert overlay.encryption["at_rest"] == "AES-256"
    assert overlay.dr_rto == "4 hours"


def test_commercial_overlay_populated():
    """Commercial overlay validates with realistic data."""
    overlay = CommercialOverlay(
        pricing_model="Per-user, tiered",
        pricing_metrics=[
            {"metric": "Named Users", "description": "Active users per month"}
        ],
        sla_tiers=[{"tier_name": "Gold", "uptime": "99.9%", "penalty": "5% credit"}],
        contract_terms="3-year minimum, annual billing",
        support_tiers=[{"tier": "Premium", "response_time": "1 hour", "scope": "24/7"}],
        environment_strategy="Shared infrastructure, isolated tenants",
    )
    assert overlay.pricing_model == "Per-user, tiered"
    assert len(overlay.sla_tiers) == 1


def test_rfp_overlay_populated():
    """RFP overlay validates with realistic data."""
    overlay = RFPOverlay(
        questions_answered=[
            {
                "question_summary": "DR capabilities?",
                "answer_summary": "RTO 4h, RPO 1h",
                "confidence": "high",
            },
        ],
        capabilities_demonstrated=["Multi-tenant SaaS", "Real-time analytics"],
        gaps_identified=["No on-premise option"],
        competitive_positioning="Strongest in warehouse management",
    )
    assert len(overlay.questions_answered) == 1
    assert len(overlay.gaps_identified) == 1


def test_meeting_overlay_populated():
    """Meeting overlay validates with realistic data."""
    overlay = MeetingOverlay(
        attendees=["John Smith", "Jane Doe"],
        decisions_made=["Go with Option B"],
        action_items=[
            {"owner": "John", "action": "Draft proposal", "deadline": "2026-03-20"}
        ],
        questions_raised=["What is the budget?"],
        concerns_expressed=["Timeline is tight"],
        next_steps=["Schedule follow-up"],
    )
    assert len(overlay.attendees) == 2
    assert len(overlay.action_items) == 1


def test_overlay_map_covers_doc_types():
    """All expected doc_types have overlay mappings."""
    expected = {
        "architecture",
        "product_doc",
        "security",
        "commercial",
        "rfp_response",
        "meeting",
        "training",
    }
    assert set(OVERLAY_MAP.keys()) == expected


def test_overlay_map_returns_correct_classes():
    """OVERLAY_MAP points to correct overlay classes."""
    assert OVERLAY_MAP["architecture"] is ArchitectureOverlay
    assert OVERLAY_MAP["product_doc"] is ArchitectureOverlay
    assert OVERLAY_MAP["security"] is SecurityOverlay
    assert OVERLAY_MAP["commercial"] is CommercialOverlay
    assert OVERLAY_MAP["rfp_response"] is RFPOverlay
    assert OVERLAY_MAP["meeting"] is MeetingOverlay
    assert OVERLAY_MAP["training"] is MeetingOverlay
