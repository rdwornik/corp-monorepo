"""Built-in action registry — domain-split per clean architecture.

Each domain module registers its actions via the @register_action decorator.
This package replaces the monolithic built_in_actions.py.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from corp.models import StepResult

logger = logging.getLogger(__name__)

# --- Action registry ---

_ACTIONS: dict[str, Callable[[dict[str, str]], StepResult]] = {}


def register_action(name: str) -> Callable:
    """Decorator to register a built-in action."""

    def decorator(fn: Callable[[dict[str, str]], StepResult]) -> Callable:
        _ACTIONS[name] = fn
        return fn

    return decorator


def get_action(name: str) -> Callable[[dict[str, str]], StepResult] | None:
    """Look up a registered action by name."""
    return _ACTIONS.get(name)


# Import all domain modules to trigger @register_action decorators.
# These imports MUST be at the bottom, after register_action is defined.
from corp.actions import (  # noqa: E402, F401
    analytics_actions,
    archive_actions,
    brief_actions,
    deck_actions,
    inbox_actions,
    index_actions,
    knowledge_actions,
    monitoring_actions,
    task_actions,
    vault_actions,
)
