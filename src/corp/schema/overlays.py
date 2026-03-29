"""Structured extraction overlay schemas.

These define the type-specific fields extracted from high-value documents.
CKE populates them during deep extraction. Corp-by-os validates and queries them.
"""

from pydantic import BaseModel


class ArchitectureOverlay(BaseModel):
    """Overlay for architecture/technical documents."""

    components: list[dict] | None = None
    integration_points: list[dict] | None = None
    data_flow: str | None = None
    apis: list[dict] | None = None
    deployment_model: str | None = None
    scalability: str | None = None
    tech_stack: list[str] | None = None
    environments: str | None = None


class SecurityOverlay(BaseModel):
    """Overlay for security/compliance documents."""

    certifications: list[dict] | None = None
    encryption: dict | None = None
    data_residency: str | None = None
    compliance_frameworks: list[str] | None = None
    access_control: str | None = None
    audit_capabilities: str | None = None
    dr_rto: str | None = None
    dr_rpo: str | None = None


class CommercialOverlay(BaseModel):
    """Overlay for commercial/pricing documents."""

    pricing_model: str | None = None
    pricing_metrics: list[dict] | None = None
    sla_tiers: list[dict] | None = None
    contract_terms: str | None = None
    support_tiers: list[dict] | None = None
    environment_strategy: str | None = None


class RFPOverlay(BaseModel):
    """Overlay for RFP response documents."""

    questions_answered: list[dict] | None = None
    capabilities_demonstrated: list[str] | None = None
    gaps_identified: list[str] | None = None
    competitive_positioning: str | None = None


class MeetingOverlay(BaseModel):
    """Overlay for meeting notes/discovery sessions."""

    attendees: list[str] | None = None
    decisions_made: list[str] | None = None
    action_items: list[dict] | None = None
    questions_raised: list[str] | None = None
    concerns_expressed: list[str] | None = None
    next_steps: list[str] | None = None


# Map doc_type -> overlay class
OVERLAY_MAP: dict[str, type] = {
    "architecture": ArchitectureOverlay,
    "product_doc": ArchitectureOverlay,
    "security": SecurityOverlay,
    "commercial": CommercialOverlay,
    "rfp_response": RFPOverlay,
    "meeting": MeetingOverlay,
    "training": MeetingOverlay,
}
