"""FR-10 source-registry schema tests — seam F (fail-closed round-trip).

Guards intake-16 §1.3/§4: a declaration missing an A1/A2 anchor or carrying an
out-of-enum value is REJECTED (never silently defaulted), and a valid record
round-trips YAML declaration -> validated record -> canonical dict -> record.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from corp.ops.source_registry import (
    SourceDeclaration,
    SourceRegistryError,
    load_source_registry,
    to_dict,
    validate_declaration,
)


def _valid_raw(**overrides) -> dict:
    raw = {
        "id": "by-platform",
        "name": "Blue Yonder Platform — Documents",
        "site_id": "bytenant.sharepoint.com,guid-a,guid-b",
        "drive_id": "b!drive-guid",
        "path_hint": "General/Platform",
        "web_url": "https://bytenant.sharepoint.com/sites/platform",
        "local_hint": "OneDrive - Blue Yonder/Platform",
        "what_it_holds": "Platform product documentation",
        "owner_team": "Platform",
        "dims": {"industry": ["retail"], "software": ["luminate"]},
        "topics": ["platform", "architecture"],
        "phase": "REGISTERED",
        "curation_level": "golden",
        "operator_prior": "max",
        "added_by": "operator",
    }
    raw.update(overrides)
    return raw


class TestValidateDeclaration:
    def test_valid_record_validates(self) -> None:
        decl = validate_declaration(_valid_raw())
        assert isinstance(decl, SourceDeclaration)
        assert decl.id == "by-platform"
        assert decl.site_id.startswith("bytenant")

    def test_defaults_applied_for_optional_fields(self) -> None:
        decl = validate_declaration(
            {"id": "x", "name": "X", "site_id": "s", "drive_id": "d"}
        )
        assert decl.phase == "REGISTERED"
        assert decl.operator_prior == "normal"
        assert decl.curation_level == "candidate"
        assert decl.added_by == "operator"
        assert decl.archive_pointer is None

    @pytest.mark.parametrize("missing", ["id", "name", "site_id", "drive_id"])
    def test_missing_required_anchor_fails_closed(self, missing: str) -> None:
        raw = _valid_raw()
        del raw[missing]
        with pytest.raises(SourceRegistryError, match=missing):
            validate_declaration(raw)

    @pytest.mark.parametrize("field_name", ["site_id", "drive_id"])
    def test_empty_a1_a2_anchor_fails_closed(self, field_name: str) -> None:
        with pytest.raises(SourceRegistryError):
            validate_declaration(_valid_raw(**{field_name: "  "}))

    def test_invalid_operator_prior_fails_closed(self) -> None:
        with pytest.raises(SourceRegistryError, match="operator_prior"):
            validate_declaration(_valid_raw(operator_prior="urgent"))

    def test_invalid_phase_fails_closed(self) -> None:
        with pytest.raises(SourceRegistryError, match="phase"):
            validate_declaration(_valid_raw(phase="S9"))

    def test_invalid_curation_level_fails_closed(self) -> None:
        with pytest.raises(SourceRegistryError, match="curation_level"):
            validate_declaration(_valid_raw(curation_level="gold"))

    def test_unknown_field_fails_closed(self) -> None:
        with pytest.raises(SourceRegistryError, match="unknown"):
            validate_declaration(_valid_raw(siteId="typo"))

    def test_non_mapping_fails_closed(self) -> None:
        with pytest.raises(SourceRegistryError):
            validate_declaration(["not", "a", "mapping"])  # type: ignore[arg-type]


class TestRoundTrip:
    def test_declaration_round_trips_through_canonical_dict(self) -> None:
        decl = validate_declaration(_valid_raw())
        assert validate_declaration(to_dict(decl)) == decl

    def test_to_dict_emits_all_fields_stable(self) -> None:
        decl = validate_declaration(_valid_raw())
        keys = list(to_dict(decl))
        assert keys[:4] == ["id", "name", "site_id", "drive_id"]
        assert "operator_prior" in keys


class TestLoadSourceRegistry:
    def test_missing_file_yields_empty(self, tmp_path: Path) -> None:
        assert load_source_registry(tmp_path / "nope.yaml") == []

    def test_loads_valid_sources(self, tmp_path: Path) -> None:
        p = tmp_path / "source_registry.yaml"
        p.write_text(
            "sources:\n"
            "  - id: by-platform\n"
            "    name: BY Platform\n"
            "    site_id: site-a\n"
            "    drive_id: drive-a\n"
            "    operator_prior: max\n"
            "  - id: cognitive-fridays\n"
            "    name: Cognitive Fridays\n"
            "    site_id: site-b\n"
            "    drive_id: drive-b\n",
            encoding="utf-8",
        )
        records = load_source_registry(p)
        assert [r.id for r in records] == ["by-platform", "cognitive-fridays"]

    def test_duplicate_id_fails_closed(self, tmp_path: Path) -> None:
        p = tmp_path / "dup.yaml"
        p.write_text(
            "sources:\n"
            "  - {id: a, name: A, site_id: s, drive_id: d}\n"
            "  - {id: a, name: A2, site_id: s2, drive_id: d2}\n",
            encoding="utf-8",
        )
        with pytest.raises(SourceRegistryError, match="duplicate"):
            load_source_registry(p)

    def test_invalid_record_in_file_fails_closed(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.yaml"
        p.write_text(
            "sources:\n  - {id: a, name: A, drive_id: d}\n",  # missing site_id (A1)
            encoding="utf-8",
        )
        with pytest.raises(SourceRegistryError, match="site_id"):
            load_source_registry(p)

    def test_non_mapping_root_fails_closed(self, tmp_path: Path) -> None:
        p = tmp_path / "list.yaml"
        p.write_text("- just\n- a\n- list\n", encoding="utf-8")
        with pytest.raises(SourceRegistryError):
            load_source_registry(p)
