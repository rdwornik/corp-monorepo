"""Knowledge query action."""

from __future__ import annotations

import logging

from corp.actions import register_action
from corp.models import StepResult

logger = logging.getLogger(__name__)


@register_action("query_knowledge")
def query_knowledge_action(params: dict[str, str]) -> StepResult:
    """Search facts across all projects."""
    from corp.query_engine import search_facts

    query = params.get("query", params.get("title", ""))
    if not query:
        return StepResult(
            step_index=0,
            description="Query knowledge",
            success=False,
            error="No query provided",
        )

    project_filter = params.get("project")
    results = search_facts(query, project_filter=project_filter)

    if not results:
        return StepResult(
            step_index=0,
            description="Query knowledge",
            success=True,
            output=f"No results for '{query}'",
        )

    lines = [f"Found {len(results)} results for '{query}':"]
    for r in results:
        lines.append(f"  [{r.client}] {r.fact[:120]}")
        if r.source_title:
            lines.append(f"    source: {r.source_title}")

    return StepResult(
        step_index=0,
        description="Query knowledge",
        success=True,
        output="\n".join(lines),
    )
