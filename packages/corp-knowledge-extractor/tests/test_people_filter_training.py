"""Test people filter against real extraction data.

Fixtures generated from 690 CKE extraction outputs. Verifies that
filter_people correctly separates real people from roles/organizations.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "people_filter.json"

if FIXTURES_PATH.exists():
    ALL_PEOPLE = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
else:
    ALL_PEOPLE = []


def test_people_fixtures_exist() -> None:
    """Verify fixture file exists with reasonable data."""
    assert FIXTURES_PATH.exists(), "people_filter.json not found"
    assert len(ALL_PEOPLE) >= 50, f"Expected 50+ people, got {len(ALL_PEOPLE)}"


def test_fixture_has_type_distribution() -> None:
    """Fixture data includes both real people and filtered entries."""
    types = {p["type"] for p in ALL_PEOPLE}
    assert "real_person" in types
    assert types & {"role", "organization"}, f"Only found types: {types}"


def test_filter_people_no_crashes() -> None:
    """filter_people handles all real people strings without error."""
    from corp_knowledge_extractor.post_process import filter_people

    all_names = [p["input"] for p in ALL_PEOPLE]
    # Should not raise
    kept, filtered = filter_people(all_names)
    assert len(kept) + len(filtered) == len(all_names)


def test_filter_people_keeps_most_entries() -> None:
    """Most extraction people entries are real people, not roles."""
    from corp_knowledge_extractor.post_process import filter_people

    all_names = [p["input"] for p in ALL_PEOPLE]
    kept, filtered = filter_people(all_names)
    keep_rate = len(kept) / len(all_names) if all_names else 0
    # Expect at least 60% are real people (not roles/orgs)
    assert keep_rate >= 0.60, (
        f"Too many filtered: {len(filtered)}/{len(all_names)} "
        f"({1 - keep_rate:.0%} filtered)"
    )


def test_pure_role_titles_filtered() -> None:
    """Pure role titles (no person name) should be filtered."""
    from corp_knowledge_extractor.post_process import filter_people

    pure_roles = [
        "Technical Account Manager",
        "Global demand planner",
        "Commercial BU head",
        "Supply chain analyst",
        "Project Manager",
    ]
    kept, filtered = filter_people(pure_roles)
    # At least most pure roles should be filtered
    assert len(filtered) >= 3, (
        f"Expected most pure roles filtered, got {len(filtered)}/{len(pure_roles)}"
    )


def test_named_people_with_roles_kept() -> None:
    """People with real names + role descriptions should be kept."""
    from corp_knowledge_extractor.post_process import filter_people

    named_people = [
        "Amy Wilkes (Supply Chain Degree Apprentice)",
        "Satish Kalpathy (VP, PMG Head)",
        "John Smith",
        "Maria Garcia (Director of Engineering)",
    ]
    kept, filtered = filter_people(named_people)
    # At least most named people should be kept
    assert len(kept) >= 3, (
        f"Expected most named people kept, got {len(kept)}/{len(named_people)}: "
        f"filtered={filtered}"
    )


def test_high_frequency_people_are_real() -> None:
    """People appearing in 5+ extractions are likely real (not role titles)."""
    from corp_knowledge_extractor.post_process import filter_people

    frequent = [p["input"] for p in ALL_PEOPLE if p["count"] >= 5]
    if not frequent:
        pytest.skip("No people with 5+ occurrences")

    kept, filtered = filter_people(frequent)
    keep_rate = len(kept) / len(frequent)
    assert keep_rate >= 0.70, (
        f"Too many frequent people filtered: {len(filtered)}/{len(frequent)}"
    )
