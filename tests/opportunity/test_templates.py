"""Tests for naming convention logic."""

from datetime import date

from corp_opportunity_manager.templates import deck_filename, folder_name


def test_folder_name_default():
    assert folder_name("Lenzing", "Planning") == "Lenzing_Planning"


def test_folder_name_custom_pattern():
    assert folder_name("Honda", "WMS", pattern="{client}-{product}") == "Honda-WMS"


def test_deck_filename_default():
    result = deck_filename("Lenzing", "Discovery", dt=date(2026, 3, 5))
    assert result == "Lenzing_2026-03-05_Discovery.pptx"


def test_deck_filename_custom_topic():
    result = deck_filename("Honda", "Technical Deep Dive", dt=date(2026, 4, 10))
    assert result == "Honda_2026-04-10_Technical Deep Dive.pptx"


def test_deck_filename_uses_today_when_no_date():
    result = deck_filename("Test")
    assert result.startswith("Test_")
    assert result.endswith("_Discovery.pptx")
