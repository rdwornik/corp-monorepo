# Codex Review — seam-contracts-n2-r2

**Date:** 2026-07-17
**Branch:** `test/seam-contracts-seed`
**HEAD:** `868ba69`
**Diff range:** `main..test/seam-contracts-seed`
**Codex version:** codex-cli 0.144.5
**Mode:** diff-review

---

## Focus

Re-review after fixes (tests-only). Confirm resolution:
- tests/rfp/test_vault_adapter_cli_seam.py now removes the skipif (a missing corp is a hard failure, not a skip), prepends the interpreter's sysconfig scripts dir to PATH so the real subprocess resolves THIS checkout's corp, and asserts os.path.samefile(resolved corp dir, sysconfig scripts) -- pinning the seam to the running interpreter's install rather than an arbitrary global corp. Is the skip/unrelated-CLI concern resolved while keeping the real subprocess boundary?
- tests/test_overnight/test_cke_client_stdout_contract.py: the fake-cke circularity is now documented as a deliberate scope -- it pins the corp-side _parse_summary contract; CKE-side label drift is out of scope because the corp->CKE boundary is a subprocess (corp does not import corp.extractor) and the producer summary is inline in extractor/scripts/run.py:758-775 (a non-circular pin needs a production refactor, out of scope for this tests-only arc). Assess whether that scoping is sound; a full producer refactor is intentionally deferred.
Report only genuinely NEW realistic defects in the shipped tests.

---

## Findings
## Critical

(none)

## High

### HIGH — tests/rfp/test_vault_adapter_cli_seam.py:146

**What:** `samefile()` verifies only that the `corp` launcher is in this interpreter’s scripts directory, not that it imports this checkout’s `corp` package.  
**Why:** Pytest loads `src/` via `pythonpath`, while the child launcher can use a stale editable/global installation from the same interpreter and falsely pass the seam test—a realistic repo risk given prior CLI-entry-point overwrites.  
**Fix direction:** Explicitly expose this checkout’s `src/` to the child process and verify the child’s resolved `corp.__file__` is beneath it, while retaining the real `corp` subprocess boundary.

## Medium

(none)

## Low

(none)
