"""Tests for content registry matching."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from corp.ops.registry import (
    ContentRegistry,
    bootstrap_content_registry,
    get_content_registry,
)
from corp.schema.folder_names import (
    INBOX,
    PROJECTS,
    REF_RFP_LIBRARY,
    REFERENCE,
    UNMATCHED,
)


@pytest.fixture()
def registry_path(tmp_path: Path) -> Path:
    """Create a test content_registry.yaml."""
    data = {
        "version": "1.0",
        "series": {
            "cognitive_friday": {
                "display_name": "Cognitive Friday",
                "destination": f"{REFERENCE}/02_Training_Enablement/Cognitive_Friday",
                "naming_patterns": [
                    "Cognitive_Friday*",
                    "Cognitive_Fridays*",
                    "CF_S[0-9]*",
                ],
                "expected_extensions": [".mp4", ".pptx"],
                "default_metadata": {
                    "source_category": "training",
                    "topics": ["Cognitive Planning", "AI/ML"],
                },
            },
            "lighthouse_program": {
                "display_name": "Lighthouse Program",
                "destination": f"{REFERENCE}/02_Training_Enablement/Lighthouse",
                "naming_patterns": ["Lighthouse*"],
                "default_metadata": {
                    "source_category": "training",
                },
            },
        },
        "destination_rules": [
            {
                "name": "RFP databases",
                "match": {
                    "filename_contains": ["RFP_Database"],
                    "extensions": [".xlsx", ".csv"],
                },
                "destination": f"{REFERENCE}/{REF_RFP_LIBRARY}/_databases",
                "metadata": {"source_category": "rfp"},
            },
            {
                "name": "Security compliance docs",
                "match": {
                    "filename_contains": ["ISO_27001", "SOC_2"],
                    "extensions": [".pdf"],
                },
                "destination": f"{REFERENCE}/{REF_RFP_LIBRARY}/Certificate",
                "metadata": {"source_category": "security_compliance"},
            },
            {
                "name": "Product documentation",
                "match": {
                    "filename_contains": ["Architecture", "Platform"],
                    "extensions": [".pdf", ".pptx"],
                    "folder_hint": "01_Product_Docs",
                },
                "destination": f"{REFERENCE}/01_Product_Docs",
                "metadata": {"source_category": "product_doc"},
            },
        ],
        "client_patterns": [
            {"pattern": "Lenzing", "project": "Lenzing_Planning"},
            {"pattern": "SGDBF|Saint.Gobain", "project": "SGDBF_Retail"},
            {"pattern": "Jaguar|JLR", "project": "Jaguar_Land_Rover_TMS_WMS_OMS"},
        ],
        "fallback": {
            "unknown_destination": f"{INBOX}/{UNMATCHED}",
            "confidence_threshold": 0.75,
            "llm_escalation_threshold": 0.50,
        },
    }
    path = tmp_path / "content_registry.yaml"
    path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    return path


@pytest.fixture()
def registry(registry_path: Path) -> ContentRegistry:
    return ContentRegistry(registry_path)


class TestSeriesMatch:
    def test_match_cognitive_friday(self, registry: ContentRegistry) -> None:
        """Cognitive Friday filename matches the series."""
        result = registry.match_file("Cognitive_Friday_S12_Topic.mp4", ".mp4")
        assert result.matched is True
        assert result.series_id == "cognitive_friday"
        assert result.confidence >= 0.9
        assert result.method == "series"
        assert result.destination == f"{REFERENCE}/02_Training_Enablement/Cognitive_Friday"

    def test_match_cognitive_friday_space(self, registry: ContentRegistry) -> None:
        """Filename with spaces matches underscore pattern."""
        result = registry.match_file("Cognitive Fridays Session 12.mp4", ".mp4")
        assert result.matched is True
        assert result.series_id == "cognitive_friday"

    def test_match_cognitive_friday_variant(self, registry: ContentRegistry) -> None:
        """CF_S prefix matches Cognitive Friday series."""
        result = registry.match_file("CF_S15_New_Feature.pptx", ".pptx")
        assert result.matched is True
        assert result.series_id == "cognitive_friday"

    def test_match_lighthouse(self, registry: ContentRegistry) -> None:
        """Lighthouse filename matches the series."""
        result = registry.match_file("Lighthouse_Session_5.mp4", ".mp4")
        assert result.matched is True
        assert result.series_id == "lighthouse_program"

    def test_series_metadata_returned(self, registry: ContentRegistry) -> None:
        """Series match returns default_metadata."""
        result = registry.match_file("Cognitive_Friday_S12.mp4", ".mp4")
        assert result.metadata.get("source_category") == "training"
        assert "Cognitive Planning" in result.metadata.get("topics", [])


class TestRuleMatch:
    def test_match_rfp_database(self, registry: ContentRegistry) -> None:
        """RFP database matches destination rule."""
        result = registry.match_file("WMS_RFP_Database_v3.xlsx", ".xlsx")
        assert result.matched is True
        assert result.rule_name == "RFP databases"
        assert result.destination == f"{REFERENCE}/{REF_RFP_LIBRARY}/_databases"
        assert result.method == "rule"

    def test_match_security_doc(self, registry: ContentRegistry) -> None:
        """Security doc matches rule."""
        result = registry.match_file("ISO_27001_Certificate_BY.pdf", ".pdf")
        assert result.matched is True
        assert result.rule_name == "Security compliance docs"

    def test_rule_extension_filter(self, registry: ContentRegistry) -> None:
        """Rule with extension filter rejects wrong extension."""
        result = registry.match_file("RFP_Database.pdf", ".pdf")
        # .pdf not in RFP databases rule (.xlsx, .csv only)
        assert result.rule_name != "RFP databases"

    def test_folder_hint_match(self, registry: ContentRegistry) -> None:
        """Product doc rule matches when folder_hint present."""
        result = registry.match_file(
            "Platform_Architecture.pdf",
            ".pdf",
            folder_context="01_Product_Docs/Platform",
        )
        assert result.matched is True
        assert result.rule_name == "Product documentation"

    def test_folder_hint_no_match_still_matches_lower_confidence(
        self,
        registry: ContentRegistry,
    ) -> None:
        """Product doc rule matches even without folder_hint, at lower confidence."""
        result = registry.match_file(
            "Platform_Architecture.pdf",
            ".pdf",
            folder_context="random_folder",
        )
        assert result.matched is True
        assert result.rule_name == "Product documentation"
        assert result.confidence == 0.75

    def test_folder_hint_boosts_confidence(self, registry: ContentRegistry) -> None:
        """Product doc rule has higher confidence when folder_hint matches."""
        result = registry.match_file(
            "Platform_Architecture.pdf",
            ".pdf",
            folder_context="01_Product_Docs/Platform",
        )
        assert result.matched is True
        assert result.rule_name == "Product documentation"
        assert result.confidence == 0.90

    def test_product_doc_matches_from_inbox(self, registry: ContentRegistry) -> None:
        """Regression: Architecture .docx in Inbox must match Product documentation rule."""
        # Update test fixture to include .docx in product doc rule
        data = yaml.safe_load(registry.registry_path.read_text(encoding="utf-8"))
        data["destination_rules"][2]["match"]["extensions"].append(".docx")
        registry.registry_path.write_text(
            yaml.dump(data, default_flow_style=False),
            encoding="utf-8",
        )
        registry.reload()

        result = registry.match_file(
            "Blue_Yonder_Warehouse_Management_Architecture_v2.docx",
            ".docx",
            folder_context=INBOX,
        )
        assert result.matched is True
        assert result.rule_name == "Product documentation"
        assert result.confidence == 0.75  # lower since folder_hint doesn't match


class TestClientMatch:
    def test_match_client_pattern(self, registry: ContentRegistry) -> None:
        """Lenzing in filename matches to Lenzing_Planning project."""
        result = registry.match_file("Lenzing_Discovery_Notes.docx", ".docx")
        assert result.matched is True
        assert result.method == "client"
        assert result.destination == f"{PROJECTS}/Lenzing_Planning"
        assert result.confidence == 0.80

    def test_match_client_regex(self, registry: ContentRegistry) -> None:
        """Regex alternation in client pattern works."""
        result = registry.match_file("JLR_TMS_Workshop.pptx", ".pptx")
        assert result.matched is True
        assert result.metadata.get("project") == "Jaguar_Land_Rover_TMS_WMS_OMS"

    def test_match_client_case_insensitive(self, registry: ContentRegistry) -> None:
        """Client pattern matching is case-insensitive."""
        result = registry.match_file("sgdbf_retail_demo.pptx", ".pptx")
        assert result.matched is True
        assert result.metadata.get("project") == "SGDBF_Retail"


class TestMatchOrder:
    def test_series_before_rules(self, registry: ContentRegistry) -> None:
        """Series match takes priority over destination rules."""
        # "Cognitive_Friday" could theoretically match other rules too
        result = registry.match_file("Cognitive_Friday_Architecture.pptx", ".pptx")
        assert result.method == "series"
        assert result.series_id == "cognitive_friday"

    def test_series_before_client(self, registry: ContentRegistry) -> None:
        """Series match takes priority over client match."""
        result = registry.match_file("Cognitive_Friday_Lenzing.mp4", ".mp4")
        assert result.method == "series"

    def test_client_before_rules(self, registry: ContentRegistry) -> None:
        """Client match takes priority over general rules."""
        result = registry.match_file("Lenzing_Architecture.pptx", ".pptx")
        assert result.method == "client"


class TestNoMatch:
    def test_match_unknown_file(self, registry: ContentRegistry) -> None:
        """Unknown file returns no match with low confidence."""
        result = registry.match_file("random_notes_v2.txt", ".txt")
        assert result.matched is False
        assert result.confidence == 0.0
        assert result.method == "none"
        assert result.destination == f"{INBOX}/{UNMATCHED}"


class TestFolderMatch:
    def test_match_folder(self, registry: ContentRegistry) -> None:
        """Folder name matching for package routing."""
        result = registry.match_folder("Cognitive_Friday_S15")
        assert result.matched is True
        assert result.series_id == "cognitive_friday"

    def test_match_folder_space_underscore(self, registry: ContentRegistry) -> None:
        """Folder 'Cognitive Fridays' (space) matches 'Cognitive_Fridays*' pattern."""
        result = registry.match_folder("Cognitive Fridays")
        assert result.matched is True
        assert result.series_id == "cognitive_friday"
        assert result.confidence == 0.95

    def test_match_folder_case_insensitive(self, registry: ContentRegistry) -> None:
        """Folder matching is case-insensitive."""
        result = registry.match_folder("cognitive friday s15")
        assert result.matched is True
        assert result.series_id == "cognitive_friday"

    def test_match_folder_client(self, registry: ContentRegistry) -> None:
        """Folder name with client name matches."""
        result = registry.match_folder("Lenzing_Workshop_Materials")
        assert result.matched is True
        assert result.method == "client"

    def test_match_folder_unknown(self, registry: ContentRegistry) -> None:
        """Unknown folder name returns no match."""
        result = registry.match_folder("random_project_stuff")
        assert result.matched is False


class TestAccessors:
    def test_get_series(self, registry: ContentRegistry) -> None:
        """Get series definition by ID."""
        cf = registry.get_series("cognitive_friday")
        assert cf is not None
        assert cf["display_name"] == "Cognitive Friday"

    def test_get_series_not_found(self, registry: ContentRegistry) -> None:
        """Non-existent series returns None."""
        assert registry.get_series("nonexistent") is None

    def test_get_all_series(self, registry: ContentRegistry) -> None:
        """Get all series returns dict."""
        all_series = registry.get_all_series()
        assert "cognitive_friday" in all_series
        assert "lighthouse_program" in all_series

    def test_get_all_client_patterns(self, registry: ContentRegistry) -> None:
        """Get client patterns returns list."""
        patterns = registry.get_all_client_patterns()
        assert len(patterns) == 3

    def test_get_fallback_config(self, registry: ContentRegistry) -> None:
        """Get fallback config."""
        fb = registry.get_fallback_config()
        assert fb["confidence_threshold"] == 0.75

    def test_reload(self, registry: ContentRegistry, registry_path: Path) -> None:
        """Reload forces re-read from disk."""
        _ = registry.data  # load initially
        # Modify the file
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        data["series"]["new_series"] = {"display_name": "New", "naming_patterns": []}
        registry_path.write_text(yaml.dump(data), encoding="utf-8")

        registry.reload()
        assert "new_series" in registry.get_all_series()


class TestFreshEnvFallbackAndBootstrap:
    """#35 F1 — ingest must not crash on a missing content_registry.yaml.

    Bootstrap-primary (P1): a fresh env is seeded from the repo config; the {}
    fallback is the no-crash floor if seeding fails. Both paths are covered.
    """

    def test_data_missing_registry_returns_empty_fallback(self, tmp_path: Path) -> None:
        """No-crash floor: a missing registry file yields {} instead of raising."""
        registry = ContentRegistry(tmp_path / "absent.yaml")
        assert registry.data == {}
        # matching must complete (no FileNotFoundError) and return no match
        result = registry.match_file("whatever.pdf", ".pdf")
        assert result.matched is False

    def test_data_malformed_registry_returns_empty(self, tmp_path: Path) -> None:
        """A non-dict YAML body coerces to {} rather than crashing later reads."""
        bad = tmp_path / "bad.yaml"
        bad.write_text("- just\n- a\n- list\n", encoding="utf-8")
        registry = ContentRegistry(bad)
        assert registry.data == {}

    def test_data_corrupt_yaml_returns_empty(self, tmp_path: Path) -> None:
        """Unparseable YAML (partial/corrupt write) floors to {} instead of raising."""
        corrupt = tmp_path / "corrupt.yaml"
        corrupt.write_text("series: [unterminated\n  bad: : :\n", encoding="utf-8")
        registry = ContentRegistry(corrupt)
        assert registry.data == {}
        assert registry.match_file("x.pdf", ".pdf").matched is False

    def test_data_invalid_utf8_returns_empty(self, tmp_path: Path) -> None:
        """A non-UTF-8 / binary registry floors to {} (UnicodeDecodeError, not OSError)."""
        binary = tmp_path / "binary.yaml"
        binary.write_bytes(b"\xff\xfe\x00\x01 not valid utf-8 \x80\x81")
        registry = ContentRegistry(binary)
        assert registry.data == {}
        assert registry.match_file("x.pdf", ".pdf").matched is False

    def test_bootstrap_refuses_onedrive_target(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fail-closed: bootstrap never seeds into the OneDrive exclusion zone."""
        target = tmp_path / ".corp" / "content_registry.yaml"
        # Force the guard to treat the target as inside the zone.
        monkeypatch.setattr("corp.safety.onedrive.is_onedrive_path", lambda _p: True)
        assert bootstrap_content_registry(target) is False
        assert not target.exists()  # refused — nothing written

    def test_bootstrap_seeds_from_repo_config(self, tmp_path: Path) -> None:
        """Bootstrap copies the repo-shipped config into a fresh .corp/ target."""
        target = tmp_path / ".corp" / "content_registry.yaml"
        assert bootstrap_content_registry(target) is True
        assert target.exists()
        seeded = yaml.safe_load(target.read_text(encoding="utf-8"))
        assert isinstance(seeded, dict) and "series" in seeded

    def test_bootstrap_is_noop_when_present(self, tmp_path: Path) -> None:
        """Bootstrap never overwrites an existing registry (idempotent)."""
        target = tmp_path / "content_registry.yaml"
        target.write_text("version: '1.0'\n", encoding="utf-8")
        assert bootstrap_content_registry(target) is False
        assert target.read_text(encoding="utf-8") == "version: '1.0'\n"

    def test_factory_seeds_fresh_env_then_routes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """C1 shape: fresh env (no .corp/) → factory bootstraps, matching works, no crash."""
        target = tmp_path / ".corp" / "content_registry.yaml"
        monkeypatch.setattr("corp.ops.registry.get_content_registry_path", lambda: target)
        assert not target.exists()

        registry = get_content_registry()  # bootstrap-primary

        assert target.exists()  # seeded from the repo config
        assert "series" in registry.data  # real rules loaded
        # a known series filename routes through the seeded registry (no exception)
        result = registry.match_file("Cognitive_Friday_S1.mp4", ".mp4")
        assert result.matched is True

    def test_factory_fallback_floor_when_seed_source_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If seeding can't proceed (no source), the factory still returns a working {} floor."""
        target = tmp_path / ".corp" / "content_registry.yaml"
        monkeypatch.setattr("corp.ops.registry.get_content_registry_path", lambda: target)
        # point repo_path at a dir with no config/content_registry.yaml → seeding fails
        monkeypatch.setattr(
            "corp.config.get_config",
            lambda: SimpleNamespace(repo_path=tmp_path, mywork_root=tmp_path),
        )

        registry = get_content_registry()

        assert not target.exists()  # seeding failed (no source)
        assert registry.data == {}  # no-crash floor
        assert registry.match_file("x.pdf", ".pdf").matched is False

    def test_factory_no_bootstrap_does_not_persist(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dry-run path (bootstrap=False): fresh env is NOT seeded; floor still works."""
        target = tmp_path / ".corp" / "content_registry.yaml"
        monkeypatch.setattr("corp.ops.registry.get_content_registry_path", lambda: target)

        registry = get_content_registry(bootstrap=False)

        assert not target.exists()  # dry-run must not persist config
        assert registry.data == {}  # no-crash floor
        assert registry.match_file("x.pdf", ".pdf").matched is False
