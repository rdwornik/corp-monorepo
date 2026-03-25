"""Gemini Flash client for intent parsing and conversational responses."""

from __future__ import annotations

import json
import logging
import os

from corp_opportunity_manager.models import IntentResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an opportunity management assistant for a pre-sales engineer at Blue Yonder.
You manage project folders, presentations, and metadata.

Available actions:
- create_opportunity: Create new opportunity (folder + deck + metadata)
  Required: client, product. Optional: contact, stage, topic.
- prep_deck: Create presentation from template
  Required: client, topic. Optional: date.
- show_project: Show project files and status
  Required: client.
- list_projects: List all active opportunities
  No entities needed.
- create_subfolder: Create standard subfolder (RFP, Meetings, etc.)
  Required: client, folder_type (rfp, meetings, implementation).
- check_structure: Audit folder structure against standards
  Required: client.
- chitchat: General conversation, greetings, questions about capabilities.
- clarify: When the request is ambiguous, ask for clarification.

Product mapping (normalize user input to these values):
- "IBP", "SIOP", "S&OP", "planning", "demand", "supply", "DSP", "IDSP" -> "Planning"
- "WMS", "warehouse" -> "WMS"
- "TMS", "transport", "freight" -> "TMS"
- "category management", "catman", "assortment" -> "CatMan"
- "network", "network design" -> "Network"
- "platform" -> "Platform"

Naming conventions:
- Folders: {Client}_{Product} (e.g., Lenzing_Planning)
- Presentations: {Client}_{Date}_{Topic}.pptx (e.g., Lenzing_2026-03-15_Discovery.pptx)
- Dates: YYYY-MM-DD
- Meeting folders: YYYY.MM.DD - {topic}

Respond in the SAME LANGUAGE the user uses (Polish or English).

Return ONLY valid JSON (no markdown, no code fences):
{
  "intent": "create_opportunity|prep_deck|show_project|list_projects|create_subfolder|check_structure|chitchat|clarify",
  "entities": {
    "client": "string or null",
    "product": "normalized product name or null",
    "contact": "string or null",
    "topic": "string or null",
    "date": "YYYY-MM-DD or null",
    "folder_type": "rfp|meetings|implementation or null",
    "stage": "string or null"
  },
  "response_text": "Human-friendly response to show the user",
  "needs_confirmation": false,
  "confidence": 0.95
}
"""


def _get_client():
    """Lazily import and configure the google.genai client."""
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not set. Run 'keys list' in PowerShell. "
            "Keys should be in Documents/.secrets/.env"
        )

    return genai.Client(api_key=api_key)


def parse_intent(
    user_message: str,
    conversation_history: list[dict[str, str]],
    project_context: str = "",
) -> IntentResult:
    """Send user message to Gemini and parse the structured intent response.

    Args:
        user_message: The raw user input.
        conversation_history: List of {"role": "user"|"assistant", "text": "..."} dicts.
        project_context: Optional string describing current project state.

    Returns:
        IntentResult with parsed intent, entities, and response text.
    """
    from google.genai import types

    client = _get_client()
    model_name = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")

    # Build conversation contents
    contents: list[types.Content] = []

    if project_context:
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=f"[Context: {project_context}]")],
            )
        )
        contents.append(
            types.Content(
                role="model",
                parts=[types.Part(text="Understood. I have the project context.")],
            )
        )

    for turn in conversation_history:
        role = "model" if turn["role"] == "assistant" else "user"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part(text=turn["text"])],
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text=user_message)],
        )
    )

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        temperature=0.3,
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )
        raw = response.text.strip()
        logger.debug("Gemini raw response: %s", raw)

        data = json.loads(raw)

        return IntentResult(
            intent=data.get("intent", "clarify"),
            entities=data.get("entities", {}),
            response_text=data.get("response_text", ""),
            needs_confirmation=data.get("needs_confirmation", False),
            confidence=data.get("confidence", 0.5),
        )

    except json.JSONDecodeError as e:
        logger.warning("Failed to parse Gemini JSON: %s — raw: %s", e, raw)
        return IntentResult(
            intent="clarify",
            entities={},
            response_text=f"I had trouble understanding that. Could you rephrase? (parse error: {e})",
            needs_confirmation=False,
            confidence=0.0,
        )
    except Exception as e:
        logger.error("Gemini API error: %s", e)
        return IntentResult(
            intent="clarify",
            entities={},
            response_text=f"LLM error: {e}",
            needs_confirmation=False,
            confidence=0.0,
        )
