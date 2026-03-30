"""Shared types for intent/LLM routing.

Extracted to break the llm_router <-> intent_router circular dependency.
Both modules import from here instead of from each other.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Intent:
    """Routing result from user input."""

    workflow_id: str | None = None  # None = chitchat/unclear
    parameters: dict = field(default_factory=dict)
    confidence: float = 0.0
    source: str = "none"  # "keyword" | "llm" | "none"
    response_text: str | None = None  # for chitchat/clarification
