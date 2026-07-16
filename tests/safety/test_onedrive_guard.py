"""Unit tests for the centralized OneDrive safety guard (ADR-27 Decision 1).

Covers ``corp.safety.onedrive`` in isolation. The four migrated call sites
(``cleanup/disk.py``, ``cleanup/executor.py``, ``actions/_helpers.py``,
``project/renderer.py``) keep their own regression tests in
``tests/test_cleanup/`` and ``tests/test_actions/`` — this file is the
single source of truth for the guard primitives themselves.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from corp.safety.onedrive import (
    OneDriveSafetyError,
    PathTraversalError,
    guard_path,
    guard_within_root,
    is_onedrive_path,
    onedrive_write_exempt,
)

_RESOLVED_ONEDRIVE = Path(
    "C:/Users/1028120/OneDrive - Blue Yonder/MyWork_OneDrive/real/target.txt"
)


class TestGuardPath:
    def test_raises_on_onedrive_path(self, tmp_path: Path) -> None:
        fake = tmp_path / "OneDrive - Blue Yonder" / "MyWork" / "file.txt"
        with pytest.raises(OneDriveSafetyError, match="synced|OneDrive"):
            guard_path(fake, reason="test")

    def test_noop_on_clean_path(self, tmp_path: Path) -> None:
        clean = tmp_path / "MyWork" / "file.txt"
        guard_path(clean, reason="test")  # must not raise

    def test_raises_on_resolved_onedrive_via_symlink(self, tmp_path: Path) -> None:
        """A junction/symlink whose text hides the zone but resolves into it."""
        fake = tmp_path / "looks_innocent_junction"
        fake.touch()

        def _fake_resolve(self, strict: bool = False) -> Path:  # noqa: ARG001
            return _RESOLVED_ONEDRIVE

        with patch.object(Path, "resolve", _fake_resolve):
            with pytest.raises(OneDriveSafetyError, match="synced|OneDrive"):
                guard_path(fake, reason="test")

    def test_fails_closed_on_resolve_oserror(self, tmp_path: Path) -> None:
        fake = tmp_path / "unresolvable"
        fake.touch()

        def _raising_resolve(self, strict: bool = False) -> Path:  # noqa: ARG001
            raise OSError("UNC path resolution failed")

        with patch.object(Path, "resolve", _raising_resolve):
            with pytest.raises(OneDriveSafetyError, match="resolve|verify"):
                guard_path(fake, reason="test")

    def test_reason_appears_in_error_message(self, tmp_path: Path) -> None:
        fake = tmp_path / "OneDrive - Blue Yonder" / "file.txt"
        with pytest.raises(OneDriveSafetyError, match="a very specific reason"):
            guard_path(fake, reason="a very specific reason")


class TestIsOneDrivePath:
    def test_true_for_onedrive_path(self, tmp_path: Path) -> None:
        fake = tmp_path / "OneDrive - Blue Yonder" / "MyWork" / "file.txt"
        assert is_onedrive_path(fake) is True

    def test_false_for_clean_path(self, tmp_path: Path) -> None:
        clean = tmp_path / "MyWork" / "file.txt"
        assert is_onedrive_path(clean) is False

    def test_true_on_resolve_failure(self, tmp_path: Path) -> None:
        fake = tmp_path / "unresolvable"

        def _raising_resolve(self, strict: bool = False) -> Path:  # noqa: ARG001
            raise OSError("boom")

        with patch.object(Path, "resolve", _raising_resolve):
            assert is_onedrive_path(fake) is True

    def test_never_raises(self, tmp_path: Path) -> None:
        """Predicate form — must not raise even on a synced path."""
        fake = tmp_path / "OneDrive - Blue Yonder" / "file.txt"
        assert is_onedrive_path(fake) is True  # no exception


class TestStrictParam:
    """strict=True (default) matches only the canonical 'OneDrive - Blue Yonder'
    zone; strict=False also matches any case-insensitive 'onedrive' path,
    preserving project/renderer.py's pre-centralization breadth (Codex
    2026-07-17)."""

    def test_personal_onedrive_matched_only_when_broad(self, tmp_path: Path) -> None:
        # 'OneDrive' but NOT the canonical 'OneDrive - Blue Yonder' zone.
        personal = tmp_path / "OneDrive" / "personal" / "notes.md"
        assert is_onedrive_path(personal, strict=True) is False
        assert is_onedrive_path(personal, strict=False) is True

    def test_guard_path_strict_true_allows_personal_onedrive(self, tmp_path: Path) -> None:
        personal = tmp_path / "OneDrive" / "notes.md"
        guard_path(personal, reason="strict canonical only")  # default strict=True: no raise

    def test_guard_path_strict_false_refuses_personal_onedrive(self, tmp_path: Path) -> None:
        personal = tmp_path / "OneDrive" / "notes.md"
        with pytest.raises(OneDriveSafetyError, match="synced|OneDrive"):
            guard_path(personal, reason="broad", strict=False)

    def test_canonical_zone_matched_under_both_modes(self, tmp_path: Path) -> None:
        canonical = tmp_path / "OneDrive - Blue Yonder" / "file.txt"
        assert is_onedrive_path(canonical, strict=True) is True
        assert is_onedrive_path(canonical, strict=False) is True


class TestGuardWithinRoot:
    def test_passes_for_inside_path(self, tmp_path: Path) -> None:
        root = tmp_path / "vault"
        inside = root / "sub" / "file.md"
        guard_within_root(inside, root, reason="test")  # must not raise

    def test_raises_for_outside_path(self, tmp_path: Path) -> None:
        root = tmp_path / "vault"
        outside = tmp_path / "elsewhere" / "file.md"
        with pytest.raises(PathTraversalError, match="escapes"):
            guard_within_root(outside, root, reason="test")

    def test_pure_no_config_dependency(self, tmp_path: Path) -> None:
        """guard_within_root must work with arbitrary roots — no config import."""
        root = tmp_path / "any_root_at_all"
        inside = root / "child"
        guard_within_root(inside, root, reason="test")  # must not raise

    def test_root_itself_is_within_root(self, tmp_path: Path) -> None:
        root = tmp_path / "vault"
        guard_within_root(root, root, reason="test")  # must not raise


class TestOnedriveWriteExempt:
    def test_returns_function_unchanged(self) -> None:
        def my_func(x: int) -> int:
            return x + 1

        decorated = onedrive_write_exempt(reason="test exemption")(my_func)
        assert decorated is my_func
        assert decorated(1) == 2

    def test_stores_reason_for_introspection(self) -> None:
        @onedrive_write_exempt(reason="grep-able reason string")
        def my_func() -> None:
            pass

        assert my_func._onedrive_write_exempt_reason == "grep-able reason string"
