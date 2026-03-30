"""Index rebuild action."""

from __future__ import annotations

import logging

from corp.actions import register_action
from corp.models import StepResult

logger = logging.getLogger(__name__)


@register_action("rebuild_index")
def rebuild_index_action(params: dict[str, str]) -> StepResult:
    """Rebuild the cross-project SQLite index."""
    from corp.index_builder import rebuild_index

    stats = rebuild_index()
    return StepResult(
        step_index=0,
        description="Rebuild index",
        success=True,
        output=(
            f"Indexed {stats.projects_indexed} projects, "
            f"{stats.facts_indexed} facts in {stats.rebuild_duration:.1f}s"
        ),
    )
