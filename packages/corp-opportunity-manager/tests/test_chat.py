"""Tests for chat session — intent routing and helpers."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from corp_opportunity_manager.chat import ChatSession, _parse_date
from corp_opportunity_manager.config import AppConfig
from corp_opportunity_manager.models import IntentResult


@pytest.fixture
def app_config(tmp_path: Path) -> AppConfig:
    """AppConfig pointing at temp directories."""
    projects = tmp_path / "projects"
    projects.mkdir()
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "BY_Discovery_Template.pptx").write_bytes(b"FAKE_PPTX")

    return AppConfig(
        projects_root=projects,
        archive_root=tmp_path / "archive",
        templates_root=templates,
        project_codes_excel=None,
        naming={
            "folder_pattern": "{client}_{product}",
            "pptx_pattern": "{client}_{date}_{topic}.pptx",
            "date_format": "%Y-%m-%d",
        },
        templates={"discovery_deck": "BY_Discovery_Template.pptx"},
        folder_structure={"create_dirs": ["_knowledge"]},
        stages=["discovery", "qualification", "rfp"],
        products=["Planning", "WMS", "TMS"],
    )


@pytest.fixture
def session(app_config: AppConfig) -> ChatSession:
    """ChatSession with a string-buffer console for testing."""
    console = Console(file=MagicMock(), force_terminal=True, width=120)
    return ChatSession(app_config, console)


class TestIntentRouting:
    """Test that intents get routed to correct handlers."""

    @patch("corp_opportunity_manager.chat.parse_intent")
    def test_create_opportunity_route(self, mock_parse, session: ChatSession):
        mock_parse.return_value = IntentResult(
            intent="create_opportunity",
            entities={"client": "TestCo", "product": "Planning"},
            response_text="Created!",
        )
        session._process("New opportunity TestCo Planning")

        # Verify folder was created
        assert (session.config.projects_root / "TestCo_Planning").exists()
        assert (
            session.config.projects_root / "TestCo_Planning" / "_knowledge" / "project-info.yaml"
        ).exists()

    @patch("corp_opportunity_manager.chat.parse_intent")
    def test_list_projects_route(self, mock_parse, session: ChatSession):
        # Create a project first
        (session.config.projects_root / "Lenzing_Planning").mkdir()
        (session.config.projects_root / "Lenzing_Planning" / "_knowledge").mkdir(parents=True)

        mock_parse.return_value = IntentResult(
            intent="list_projects",
            entities={},
            response_text="Here are your projects:",
        )
        session._process("List all projects")
        # No exception = success (output goes to mock console)

    @patch("corp_opportunity_manager.chat.parse_intent")
    def test_show_project_route(self, mock_parse, session: ChatSession):
        # Create project with files
        proj = session.config.projects_root / "Lenzing_Planning"
        proj.mkdir()
        (proj / "_knowledge").mkdir()
        (proj / "_knowledge" / "project-info.yaml").write_text("client: Lenzing\n")
        (proj / "Lenzing_2026-03-06_Discovery.pptx").write_bytes(b"FAKE")

        mock_parse.return_value = IntentResult(
            intent="show_project",
            entities={"client": "Lenzing"},
            response_text="Showing Lenzing files",
        )
        session._process("Show Lenzing")

    @patch("corp_opportunity_manager.chat.parse_intent")
    def test_create_subfolder_route(self, mock_parse, session: ChatSession):
        proj = session.config.projects_root / "Lenzing_Planning"
        proj.mkdir()

        mock_parse.return_value = IntentResult(
            intent="create_subfolder",
            entities={"client": "Lenzing", "folder_type": "rfp"},
            response_text="Created RFP structure",
        )
        session._process("Got an RFP from Lenzing")
        assert (proj / "RFP" / "Original").exists()

    @patch("corp_opportunity_manager.chat.parse_intent")
    def test_check_structure_route(self, mock_parse, session: ChatSession):
        proj = session.config.projects_root / "Lenzing_Planning"
        proj.mkdir()

        mock_parse.return_value = IntentResult(
            intent="check_structure",
            entities={"client": "Lenzing"},
            response_text="Checking...",
        )
        session._process("Check Lenzing structure")

    @patch("corp_opportunity_manager.chat.parse_intent")
    def test_chitchat_route(self, mock_parse, session: ChatSession):
        mock_parse.return_value = IntentResult(
            intent="chitchat",
            entities={},
            response_text="Hello! I can help you manage opportunities.",
        )
        session._process("Hello")

    @patch("corp_opportunity_manager.chat.parse_intent")
    def test_clarify_route(self, mock_parse, session: ChatSession):
        mock_parse.return_value = IntentResult(
            intent="clarify",
            entities={},
            response_text="Could you be more specific?",
        )
        session._process("do something")

    @patch("corp_opportunity_manager.chat.parse_intent")
    def test_missing_client_shows_llm_response(self, mock_parse, session: ChatSession):
        mock_parse.return_value = IntentResult(
            intent="create_opportunity",
            entities={"client": None, "product": None},
            response_text="Which client and product?",
        )
        session._process("Create new opportunity")
        # Should show the LLM's clarification, not crash


class TestHistory:
    """Test conversation history management."""

    @patch("corp_opportunity_manager.chat.parse_intent")
    def test_history_grows(self, mock_parse, session: ChatSession):
        mock_parse.return_value = IntentResult(
            intent="chitchat",
            entities={},
            response_text="Hi!",
        )
        session._process("Hello")
        assert len(session.history) == 2  # user + assistant

        session._process("How are you?")
        assert len(session.history) == 4


class TestHelpers:
    """Test helper functions."""

    def test_parse_date_valid(self):
        assert _parse_date("2026-03-15") == date(2026, 3, 15)

    def test_parse_date_none(self):
        assert _parse_date(None) == date.today()

    def test_parse_date_invalid(self):
        assert _parse_date("not-a-date") == date.today()

    @patch("corp_opportunity_manager.chat.parse_intent")
    def test_prep_deck_creates_file(self, mock_parse, session: ChatSession):
        # Create project folder first
        proj = session.config.projects_root / "Lenzing_Planning"
        proj.mkdir()

        mock_parse.return_value = IntentResult(
            intent="prep_deck",
            entities={"client": "Lenzing", "topic": "Demo", "date": "2026-03-15"},
            response_text="Created deck",
        )
        session._process("Prep demo deck for Lenzing March 15")
        assert (proj / "Lenzing_2026-03-15_Demo.pptx").exists()

    @patch("corp_opportunity_manager.chat.parse_intent")
    def test_prep_deck_no_project(self, mock_parse, session: ChatSession):
        mock_parse.return_value = IntentResult(
            intent="prep_deck",
            entities={"client": "NonExistent", "topic": "Demo"},
            response_text="Created deck",
        )
        session._process("Prep deck for NonExistent")
        # Should print error, not crash
