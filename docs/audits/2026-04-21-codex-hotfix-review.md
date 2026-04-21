# Codex Review — Hotfix OneDrive Safety (P1-1 / P1-2 / P1-3)

**Date:** 2026-04-21
**Branch:** `hotfix/onedrive-safety-p1`
**Diff range:** `main..hotfix/onedrive-safety-p1`
**Mode:** diff review (`/review diff`)
**Reviewer:** Codex CLI
**Source hotfix prompt:** `PROMPT_onedrive_safety_hotfix.md`
**Verification source:** `docs/audits/2026-04-21-p1-verification.md`

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High     | 2 |
| Medium   | 1 |
| Low      | 0 |

No Critical findings. Two HIGH findings are the same bug class (substring-based OneDrive guard bypassable by symlink/junction). One MEDIUM finding on test layering.

---

## CRITICAL

(none)

---

## HIGH

### H-C1 — OneDrive guard is path-string based

**File:** `src/corp/cleanup/disk.py:34`

**What:** `execute_plan()` only blocks paths whose literal string contains `OneDrive - Blue Yonder`.

**Why:** A symlink/junction or configured alias to the synced tree can produce a plan item whose text does not contain that substring, and `target.unlink()` would still mutate the OneDrive-backed target.

**Fix direction:** Resolve the target path before the OneDrive check and guard against the resolved path as well as the original path.

### H-C2 — Writable project guard misses symlink/junction aliases

**File:** `src/corp/actions/_helpers.py:109`

**What:** `_guard_writable()` checks `str(path)` without resolving the path first.

**Why:** `archive_project()` now passes `writable=True`, but a `project_path` or configured `projects_root` alias/junction into OneDrive can bypass the substring check and still allow write-intent archival against a synced tree.

**Fix direction:** Resolve writable candidate paths before checking for the synced-tree marker, and treat resolution failures as fail-closed for writable operations.

---

## MEDIUM

### M-C1 — Traversal tests allow the wrong layer to satisfy runtime coverage

**File:** `tests/test_cleanup/test_onedrive_safety_p1_2.py:53`

**What:** The runtime regression tests accept either `PathTraversalError` or `ValueError`.

**Why:** These tests can pass solely because `MoveEntry` rejects the YAML at load time, without proving `_assert_within_root()` catches programmatic or symlink/junction escape cases.

**Fix direction:** Split schema-validation tests from runtime-guard tests, and assert the exact exception type expected from each layer.

---

## LOW

(none)

---

## Codex Notes

- `MoveEntry` does reject nested forms like `foo/../../bar` because `_has_parent_traversal()` checks every slash/backslash-delimited segment.
- The remaining unguarded `_resolve_project_path()` callers appear read/copy-oriented, while `archive_project()` is the write-intent caller.

---

## Action summary

- **Merge blocker:** Yes. 2 HIGH findings require fix before merge.
- **Same bug class:** Both HIGH findings (H-C1, H-C2) are substring-based guards bypassable by symlink/junction. Single fix pattern (`.resolve()` before substring check) applies to both.
- **Related pre-existing guards:** Same bug class likely exists in `executor.py:74` and `project/renderer.py` (both added 2026-03-30). Amendment should address all four sites consistently.
- **Next:** `PROMPT_hotfix_amendment.md` resolves H-C1, H-C2, and M-C1. Re-run `/review` after amendment before merging.
