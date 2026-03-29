# Dead Code Verification — Phase 0 / Step 6
**Date:** 2026-03-28
**Scope:** `packages/corp-rfp-agent` — 4 confirmed dead files from architecture audit
**Purpose:** Verify absence of live Python imports before Phase 4/Q5 deletion

---

## Files under review

| File | Path | Status |
|------|------|--------|
| `clean_kb.py` | `src/corp_rfp_agent/anonymization/clean_kb.py` | Dead — no imports |
| `scan_kb.py` | `src/corp_rfp_agent/anonymization/scan_kb.py` | Dead — no imports |
| `kb_to_markdown.py` | `src/corp_rfp_agent/kb_to_markdown.py` | Dead — has 1 live reference (see below) |
| `_paths.py` | `src/corp_rfp_agent/_paths.py` | Dead — no imports |

## Verification results

### clean_kb.py
- **Python imports:** None found anywhere in the monorepo
- **`__init__.py` export:** Not exported from `anonymization/__init__.py` (only `AnonymizationMiddleware` is)
- **Documentation references:** `CLAUDE.md`, `docs/archive/2026-03-15_CODE_REVIEW_REPORT.md`, `docs/STRUCTURAL_DEBT.md` (documentation only, not executable)
- **Verdict: Confirmed dead. Safe to delete.**

### scan_kb.py
- **Python imports:** None found anywhere in the monorepo
- **`__init__.py` export:** Not exported from `anonymization/__init__.py`
- **Documentation references:** `CLAUDE.md`, `docs/archive/2026-03-15_CODE_REVIEW_REPORT.md` (documentation only)
- **Verdict: Confirmed dead. Safe to delete.**

### kb_to_markdown.py
- **Python imports:** None (`from.*kb_to_markdown` or `import.*kb_to_markdown`) found anywhere
- **Live reference found:** `tests/test_cli_smoke.py:13` invokes it as a script:
  ```python
  [sys.executable, "src/corp_rfp_agent/kb_to_markdown.py", "--help"],
  ```
- **Verdict: Confirmed dead as a library module. The smoke test reference is a test that validates the dead script still runs. Deleting `kb_to_markdown.py` requires simultaneously removing its entry from `test_cli_smoke.py`.**

### _paths.py
- **Python imports:** No `from.*_paths` or `import.*_paths` found within `corp-rfp-agent/src/`
- **Cross-package `_paths.py` matches:** Many files across the monorepo contain `_paths.py` matches, but these all refer to `_paths.py` files in *other packages* (corp-by-os, corp-knowledge-extractor, corp-os-meta) — not to `corp_rfp_agent._paths`
- **Verification:** `grep -rn "from corp_rfp_agent._paths"` → zero results
- **Verdict: Confirmed dead. Safe to delete.**

## Phase 4 deletion checklist

When executing Q5 (ADR-23):

1. Delete `packages/corp-rfp-agent/src/corp_rfp_agent/anonymization/clean_kb.py`
2. Delete `packages/corp-rfp-agent/src/corp_rfp_agent/anonymization/scan_kb.py`
3. Delete `packages/corp-rfp-agent/src/corp_rfp_agent/kb_to_markdown.py`
4. **Update `packages/corp-rfp-agent/tests/test_cli_smoke.py`** — remove `kb_to_markdown.py` entry from `COMMANDS` list (line 13)
5. Delete `packages/corp-rfp-agent/src/corp_rfp_agent/_paths.py`
6. Run `py -m pytest packages/corp-rfp-agent/` to confirm test suite passes (should be 155 tests)

## Notes

- The audit (`2026-03-28_PACKAGE_ARCHITECTURE_AUDIT.md`) originally flagged these as "confirmed dead" — this verification confirms that finding
- `kb_to_markdown.py` is a standalone script (not a library), but its smoke test coupling means it needs a coordinated delete
- Git history preserves all 4 files post-deletion (per ADR-23 decision rationale)
- No references outside corp-rfp-agent package found (no cross-package coupling to clean up)
