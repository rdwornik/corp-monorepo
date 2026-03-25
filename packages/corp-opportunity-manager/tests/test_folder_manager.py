"""Tests for folder creation and project scaffolding."""

from datetime import date

import pytest
import yaml

from corp_opportunity_manager.config import AppConfig
from corp_opportunity_manager.folder_manager import create_opportunity
from corp_opportunity_manager.models import OpportunityConfig


def test_create_opportunity_creates_folder(app_config: AppConfig):
    opp = OpportunityConfig(client="Lenzing", product="Planning", date=date(2026, 3, 5))
    result = create_opportunity(app_config, opp)

    assert result.folder_path.exists()
    assert result.folder_path.name == "Lenzing_Planning"


def test_create_opportunity_creates_knowledge_dir(app_config: AppConfig):
    opp = OpportunityConfig(client="Lenzing", product="Planning")
    result = create_opportunity(app_config, opp)

    knowledge_dir = result.folder_path / "_knowledge"
    assert knowledge_dir.exists()


def test_create_opportunity_copies_deck(app_config: AppConfig):
    opp = OpportunityConfig(client="Lenzing", product="Planning", date=date(2026, 3, 5))
    result = create_opportunity(app_config, opp)

    assert result.deck_path is not None
    assert result.deck_path.exists()
    assert result.deck_path.name == "Lenzing_2026-03-05_Discovery.pptx"


def test_create_opportunity_writes_project_info(app_config: AppConfig):
    opp = OpportunityConfig(
        client="Honda",
        product="WMS",
        contact="Jane Doe (VP Logistics)",
        stage="rfp",
        date=date(2026, 3, 5),
    )
    result = create_opportunity(app_config, opp)

    assert result.info_path.exists()
    with open(result.info_path, "r") as f:
        info = yaml.safe_load(f)
    assert info["client"] == "Honda"
    assert info["product"] == "WMS"
    assert info["contact"] == "Jane Doe (VP Logistics)"
    assert info["stage"] == "rfp"


def test_create_opportunity_writes_notes_stub(app_config: AppConfig):
    opp = OpportunityConfig(client="Lenzing", product="Planning")
    result = create_opportunity(app_config, opp)

    assert result.notes_path.exists()
    content = result.notes_path.read_text()
    assert "Lenzing" in content
    assert "Planning" in content


def test_create_opportunity_raises_if_folder_exists(app_config: AppConfig):
    opp = OpportunityConfig(client="Lenzing", product="Planning")
    create_opportunity(app_config, opp)

    with pytest.raises(FileExistsError):
        create_opportunity(app_config, opp)


def test_create_opportunity_no_template(app_config: AppConfig):
    """When template file doesn't exist, deck_path should be None."""
    app_config.templates = {"discovery_deck": "nonexistent.pptx"}
    opp = OpportunityConfig(client="Test", product="WMS")
    result = create_opportunity(app_config, opp)

    assert result.deck_path is None
    assert result.folder_path.exists()
