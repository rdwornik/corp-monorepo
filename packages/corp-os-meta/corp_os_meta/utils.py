"""Shared utilities for the corp ecosystem."""

import json
import logging
import re

log = logging.getLogger(__name__)


def parse_llm_json(text: str) -> dict:
    """Parse JSON from LLM output using 4 strategies.

    Handles common LLM issues:
    - Markdown code fences (```json ... ```)
    - Preamble text before JSON
    - Trailing commas before } or ]
    - Minor JSON syntax errors (via json-repair if available)

    Strategies (tried in order):
    1. Strip markdown fences, parse directly
    2. Remove trailing commas, parse
    3. Regex extract first JSON object from surrounding prose
    4. json-repair library (if available)

    Returns parsed dict/list. Raises ValueError if all strategies fail.
    """
    # Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: remove trailing commas before } or ]
    cleaned = re.sub(r",\s*([}\]])", r"\1", text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: extract first {...} block from surrounding prose
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            try:
                return json.loads(re.sub(r",\s*([}\]])", r"\1", match.group()))
            except json.JSONDecodeError:
                pass

    # Strategy 4: json-repair (handles unescaped inner quotes, etc.)
    try:
        from json_repair import repair_json

        repaired = repair_json(text, return_objects=True)
        if isinstance(repaired, dict) and repaired:
            log.debug("json-repair recovered malformed JSON")
            return repaired
    except Exception:
        pass

    raise ValueError("Failed to parse LLM JSON response")
