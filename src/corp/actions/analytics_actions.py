"""Analytics actions: report generation and dashboard writing."""

from __future__ import annotations

import logging
from datetime import date

from corp.actions import register_action
from corp.config import get_config
from corp.models import StepResult

logger = logging.getLogger(__name__)


@register_action("show_analytics")
def show_analytics_action(params: dict[str, str]) -> StepResult:
    """Generate cross-project analytics and write dashboard."""
    from corp.query_engine import get_analytics

    report = get_analytics()
    _write_analytics_dashboard(report)

    lines = [
        f"Projects: {report.total_projects}, Facts: {report.total_facts}",
        f"Avg facts/project: {report.avg_facts_per_project}",
    ]
    if report.top_topics:
        lines.append("Top topics: " + ", ".join(f"{t}({c})" for t, c in report.top_topics[:5]))
    if report.top_products:
        lines.append("Top products: " + ", ".join(f"{p}({c})" for p, c in report.top_products[:5]))

    return StepResult(
        step_index=0,
        description="Show analytics",
        success=True,
        output="\n".join(lines),
    )


def _write_analytics_dashboard(report) -> None:
    """Write 00_dashboards/analytics.md with report data."""
    cfg = get_config()
    today = date.today().isoformat()

    lines = [
        "---",
        "title: Cross-Project Analytics",
        f'date: "{today}"',
        f'generated: "{today}"',
        "source_tool: corp-by-os",
        "tags: [dashboard, auto-generated, analytics]",
        "---",
        "",
        "# Cross-Project Analytics",
        "",
        f"*Generated from {report.total_projects} projects, "
        f"{report.total_facts} facts on {today}.*",
        "",
    ]

    if report.top_topics:
        lines.append("## Top Topics")
        lines.append("")
        lines.append("| Topic | Facts |")
        lines.append("|---|---|")
        for topic, count in report.top_topics:
            lines.append(f"| {topic} | {count} |")
        lines.append("")

    if report.top_products:
        lines.append("## Product Distribution")
        lines.append("")
        lines.append("| Product | Projects |")
        lines.append("|---|---|")
        for product, count in report.top_products:
            lines.append(f"| {product} | {count} |")
        lines.append("")

    if report.product_bundles:
        lines.append("## Common Product Bundles")
        lines.append("")
        lines.append("| Bundle | Count |")
        lines.append("|---|---|")
        for bundle, count in report.product_bundles:
            lines.append(f"| {bundle} | {count} |")
        lines.append("")

    if report.projects_by_status:
        lines.append("## Projects by Status")
        lines.append("")
        lines.append("| Status | Count |")
        lines.append("|---|---|")
        for status, count in sorted(report.projects_by_status.items()):
            lines.append(f"| {status} | {count} |")
        lines.append("")

    dashboard_path = cfg.vault_path / "00_dashboards" / "analytics.md"
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text("\n".join(lines), encoding="utf-8")
