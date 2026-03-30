"""Monitoring actions: attention scanning and dashboard generation."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from corp.actions import register_action
from corp.config import get_config
from corp.models import StepResult, VaultZone

from ._helpers import (
    _deserialize_issues,
    _project_display_name,
    _serialize_issues,
)

logger = logging.getLogger(__name__)


@register_action("scan_attention")
def scan_attention(params: dict[str, str]) -> StepResult:
    """Scan all projects for stale/missing/incomplete items."""
    from corp.vault_io import list_projects, read_project_info

    projects = list_projects()
    issues: list[dict[str, str]] = []

    for proj in projects:
        # Use actual folder name (original casing) for display
        display_name = _project_display_name(proj)

        # Check: no vault presence
        if not proj.has_vault and proj.has_onedrive:
            issues.append(
                {
                    "project": display_name,
                    "severity": "MEDIUM",
                    "issue": "No vault presence (exists in OneDrive only)",
                }
            )
            continue

        # Read project info for deeper checks
        info = read_project_info(proj.project_id)

        if info is None:
            if proj.has_vault:
                issues.append(
                    {
                        "project": display_name,
                        "severity": "HIGH",
                        "issue": "Missing project-info.yaml",
                    }
                )
            continue

        # Check: no extraction
        if info.facts_count == 0:
            issues.append(
                {
                    "project": display_name,
                    "severity": "HIGH",
                    "issue": "No extraction (facts_count = 0)",
                }
            )

        # Check: stale extraction
        if info.last_extracted:
            try:
                last = datetime.strptime(info.last_extracted, "%Y-%m-%d").date()
                if (date.today() - last) > timedelta(days=30):
                    issues.append(
                        {
                            "project": display_name,
                            "severity": "MEDIUM",
                            "issue": f"Stale extraction (last: {info.last_extracted})",
                        }
                    )
            except ValueError:
                pass

        # Check: missing products
        if not info.products:
            issues.append(
                {
                    "project": display_name,
                    "severity": "LOW",
                    "issue": "Missing products list",
                }
            )

        # Check: missing contacts
        if not info.people:
            issues.append(
                {
                    "project": display_name,
                    "severity": "LOW",
                    "issue": "Missing contacts/people list",
                }
            )

    # Store issues in params for dashboard generation
    params["_attention_issues"] = _serialize_issues(issues)
    params["_attention_project_count"] = str(len(projects))

    return StepResult(
        step_index=0,
        description="Scan attention",
        success=True,
        output=f"Scanned {len(projects)} projects, found {len(issues)} issues",
    )


@register_action("generate_attention_dashboard")
def generate_attention_dashboard(params: dict[str, str]) -> StepResult:
    """Write 00_dashboards/attention.md with findings."""
    cfg = get_config()
    issues = _deserialize_issues(params.get("_attention_issues", "[]"))
    project_count = params.get("_attention_project_count", "0")

    # Build markdown
    lines = [
        "---",
        "title: Attention Dashboard",
        "document_type: dashboard",
        f'date: "{date.today().isoformat()}"',
        f'generated: "{date.today().isoformat()}"',
        "source_tool: corp-by-os",
        "tags: [dashboard, auto-generated]",
        "---",
        "",
        "# Attention Dashboard",
        "",
        f"Scanned **{project_count}** projects on {date.today().isoformat()}.",
        "",
    ]

    if not issues:
        lines.append("All projects look healthy.")
    else:
        # Group by severity
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            sev_issues = [i for i in issues if i["severity"] == severity]
            if sev_issues:
                lines.append(f"## {severity}")
                lines.append("")
                lines.append("| Project | Issue |")
                lines.append("|---|---|")
                for issue in sev_issues:
                    lines.append(f"| {issue['project']} | {issue['issue']} |")
                lines.append("")

    dashboard_path = cfg.vault_path / VaultZone.DASHBOARDS.value / "attention.md"
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text("\n".join(lines), encoding="utf-8")

    return StepResult(
        step_index=0,
        description="Generate attention dashboard",
        success=True,
        output=f"Wrote {dashboard_path} ({len(issues)} issues)",
    )
