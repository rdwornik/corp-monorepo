"""Tests for LLM client — mocked Gemini responses."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


def _make_mock_response(data: dict) -> MagicMock:
    """Create a mock Gemini response object."""
    mock = MagicMock()
    mock.text = json.dumps(data)
    return mock


def _make_client_mock(response_data: dict) -> MagicMock:
    """Create a mock genai.Client whose models.generate_content returns structured data."""
    client = MagicMock()
    client.models.generate_content.return_value = _make_mock_response(response_data)
    return client


class TestParseIntent:
    """Test intent parsing with mocked Gemini."""

    @patch("corp_opportunity_manager.llm_client._get_client")
    def test_create_opportunity_english(self, mock_get_client):
        mock_get_client.return_value = _make_client_mock(
            {
                "intent": "create_opportunity",
                "entities": {
                    "client": "Lenzing",
                    "product": "Planning",
                    "contact": "Jan Kowalski",
                },
                "response_text": "Created Lenzing_Planning/",
                "needs_confirmation": False,
                "confidence": 0.95,
            }
        )

        from corp_opportunity_manager.llm_client import parse_intent

        result = parse_intent("New opportunity: Lenzing, IBP, contact Jan Kowalski", [])
        assert result.intent == "create_opportunity"
        assert result.entities["client"] == "Lenzing"
        assert result.entities["product"] == "Planning"
        assert result.confidence == 0.95

    @patch("corp_opportunity_manager.llm_client._get_client")
    def test_create_opportunity_polish(self, mock_get_client):
        mock_get_client.return_value = _make_client_mock(
            {
                "intent": "create_opportunity",
                "entities": {
                    "client": "Siemens",
                    "product": "WMS",
                    "contact": "Hans Mueller",
                },
                "response_text": "Stworzone: Siemens_WMS/",
                "needs_confirmation": False,
                "confidence": 0.9,
            }
        )

        from corp_opportunity_manager.llm_client import parse_intent

        result = parse_intent("Mam nowe opportunity, firma Siemens, WMS, kontakt Hans Mueller", [])
        assert result.intent == "create_opportunity"
        assert result.entities["client"] == "Siemens"

    @patch("corp_opportunity_manager.llm_client._get_client")
    def test_prep_deck(self, mock_get_client):
        mock_get_client.return_value = _make_client_mock(
            {
                "intent": "prep_deck",
                "entities": {
                    "client": "Honda",
                    "topic": "Technical Deep Dive",
                    "date": "2026-03-15",
                },
                "response_text": "Created Honda_2026-03-15_Technical_Deep_Dive.pptx",
                "needs_confirmation": False,
                "confidence": 0.92,
            }
        )

        from corp_opportunity_manager.llm_client import parse_intent

        result = parse_intent("Prepare a technical deep dive deck for Honda, March 15", [])
        assert result.intent == "prep_deck"
        assert result.entities["date"] == "2026-03-15"

    @patch("corp_opportunity_manager.llm_client._get_client")
    def test_list_projects(self, mock_get_client):
        mock_get_client.return_value = _make_client_mock(
            {
                "intent": "list_projects",
                "entities": {},
                "response_text": "Here are your active projects:",
                "needs_confirmation": False,
                "confidence": 0.98,
            }
        )

        from corp_opportunity_manager.llm_client import parse_intent

        result = parse_intent("Show me all my projects", [])
        assert result.intent == "list_projects"

    @patch("corp_opportunity_manager.llm_client._get_client")
    def test_ambiguous_input(self, mock_get_client):
        mock_get_client.return_value = _make_client_mock(
            {
                "intent": "clarify",
                "entities": {"client": "Lenzing"},
                "response_text": "What would you like to do with Lenzing?",
                "needs_confirmation": False,
                "confidence": 0.3,
            }
        )

        from corp_opportunity_manager.llm_client import parse_intent

        result = parse_intent("Zrob cos z Lenzing", [])
        assert result.intent == "clarify"
        assert result.confidence < 0.5

    @patch("corp_opportunity_manager.llm_client._get_client")
    def test_malformed_json_response(self, mock_get_client):
        client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "not valid json {"
        client.models.generate_content.return_value = mock_resp
        mock_get_client.return_value = client

        from corp_opportunity_manager.llm_client import parse_intent

        result = parse_intent("test", [])
        assert result.intent == "clarify"
        assert result.confidence == 0.0

    @patch("corp_opportunity_manager.llm_client._get_client")
    def test_api_error(self, mock_get_client):
        client = MagicMock()
        client.models.generate_content.side_effect = RuntimeError("API unavailable")
        mock_get_client.return_value = client

        from corp_opportunity_manager.llm_client import parse_intent

        result = parse_intent("test", [])
        assert result.intent == "clarify"
        assert "error" in result.response_text.lower()

    @patch("corp_opportunity_manager.llm_client._get_client")
    def test_create_subfolder(self, mock_get_client):
        mock_get_client.return_value = _make_client_mock(
            {
                "intent": "create_subfolder",
                "entities": {"client": "Lenzing", "folder_type": "rfp"},
                "response_text": "Created RFP/ structure in Lenzing_Planning/",
                "needs_confirmation": False,
                "confidence": 0.9,
            }
        )

        from corp_opportunity_manager.llm_client import parse_intent

        result = parse_intent("Dostalem RFP od Lenzing", [])
        assert result.intent == "create_subfolder"
        assert result.entities["folder_type"] == "rfp"

    @patch("corp_opportunity_manager.llm_client._get_client")
    def test_check_structure(self, mock_get_client):
        mock_get_client.return_value = _make_client_mock(
            {
                "intent": "check_structure",
                "entities": {"client": "Lenzing"},
                "response_text": "Checking Lenzing folder structure...",
                "needs_confirmation": False,
                "confidence": 0.88,
            }
        )

        from corp_opportunity_manager.llm_client import parse_intent

        result = parse_intent("Sprawdz strukture Lenzing", [])
        assert result.intent == "check_structure"

    @patch("corp_opportunity_manager.llm_client._get_client")
    def test_conversation_history_passed(self, mock_get_client):
        mock_get_client.return_value = _make_client_mock(
            {
                "intent": "chitchat",
                "entities": {},
                "response_text": "Hello!",
                "needs_confirmation": False,
                "confidence": 1.0,
            }
        )

        from corp_opportunity_manager.llm_client import parse_intent

        history = [
            {"role": "user", "text": "Hi"},
            {"role": "assistant", "text": "Hello!"},
        ]
        parse_intent("How are you?", history)

        # Verify history was included in the call
        call_args = mock_get_client.return_value.models.generate_content.call_args
        contents = call_args[1]["contents"]
        assert len(contents) >= 3  # history + current message
