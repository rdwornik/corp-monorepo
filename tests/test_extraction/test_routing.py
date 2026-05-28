"""Tests for extraction/routing.py — resolves MyWork folders to vault routes."""

from __future__ import annotations

from pathlib import Path

import pytest

from corp.extraction.routing import RouteInfo, RoutingError, resolve_route


def _basic_routing_map():
    return {
        "routes": {
            "10_Projects": {
                "vault_target": "01_Knowledge",
                "provenance": "projects",
                "subfolders": {
                    "Lenzing": {"content_type": "client_project"},
                },
            },
            "30_Reference": {
                "vault_target": "01_Knowledge",
                "provenance": "reference",
            },
        },
        "provenance_map": {
            "internal": ["projects", "reference"],
            "client": ["client_project"],
        },
    }


class TestResolveRoute:
    def test_top_level_route(self, tmp_path):
        mywork = tmp_path / "MyWork"
        folder = mywork / "10_Projects"
        folder.mkdir(parents=True)

        result = resolve_route(folder, _basic_routing_map(), mywork_root=mywork)
        assert isinstance(result, RouteInfo)
        assert result.vault_target == "01_Knowledge"
        assert result.content_origin == "mywork"
        assert result.routing_confidence == 1.0

    def test_subfolder_override(self, tmp_path):
        mywork = tmp_path / "MyWork"
        folder = mywork / "10_Projects" / "Lenzing"
        folder.mkdir(parents=True)

        result = resolve_route(folder, _basic_routing_map(), mywork_root=mywork)
        assert result.source_category == "client_project"
        assert result.provenance_scope == "client"

    def test_subfolder_without_override_uses_default(self, tmp_path):
        mywork = tmp_path / "MyWork"
        folder = mywork / "10_Projects" / "UnknownClient"
        folder.mkdir(parents=True)

        result = resolve_route(folder, _basic_routing_map(), mywork_root=mywork)
        assert result.source_category == "projects"

    def test_unknown_route_raises(self, tmp_path):
        mywork = tmp_path / "MyWork"
        folder = mywork / "99_Unknown"
        folder.mkdir(parents=True)

        with pytest.raises(RoutingError, match="No route defined"):
            resolve_route(folder, _basic_routing_map(), mywork_root=mywork)

    def test_folder_outside_mywork_raises(self, tmp_path):
        mywork = tmp_path / "MyWork"
        mywork.mkdir()
        outside = tmp_path / "Other" / "folder"
        outside.mkdir(parents=True)

        with pytest.raises(RoutingError, match="not under MyWork root"):
            resolve_route(outside, _basic_routing_map(), mywork_root=mywork)

    def test_no_mywork_root_uses_folder_name(self, tmp_path):
        folder = tmp_path / "30_Reference"
        folder.mkdir()

        result = resolve_route(folder, _basic_routing_map(), mywork_root=None)
        assert result.vault_target == "01_Knowledge"
        assert result.source_category == "reference"

    def test_empty_routing_map(self, tmp_path):
        folder = tmp_path / "SomeFolder"
        folder.mkdir()

        with pytest.raises(RoutingError, match="No route defined"):
            resolve_route(folder, {"routes": {}}, mywork_root=None)


class TestInvertProvenanceMap:
    def test_invert_creates_category_to_scope(self):
        from corp.extraction.routing import _invert_provenance_map

        pmap = {
            "internal": ["projects", "reference"],
            "client": ["client_project", "rfp"],
        }
        result = _invert_provenance_map(pmap)
        assert result["projects"] == "internal"
        assert result["reference"] == "internal"
        assert result["client_project"] == "client"
        assert result["rfp"] == "client"

    def test_empty_provenance_map(self):
        from corp.extraction.routing import _invert_provenance_map

        assert _invert_provenance_map({}) == {}
