# Codex Review — seam-contracts-n2

**Date:** 2026-07-17
**Branch:** `test/seam-contracts-seed`
**HEAD:** `1948755`
**Diff range:** `main..test/seam-contracts-seed`
**Codex version:** codex-cli 0.144.5
**Mode:** diff-review

---

## Focus

Tests-only diff (Arc N2 seam-contract seeds). Assess for correctness/soundness of the tests as merge-gate blockers:
- tests/rfp/test_vault_adapter_cli_seam.py drives the real corp retrieve --format json subprocess into vault_adapter._retrieve_via_cli, unmocked (no patch on subprocess.run), steering the child via VAULT_PATH/APP_DATA_PATH env. Is the seam genuinely pinned and non-vacuous (asserts non-empty + the note_id/confidence/relevance_score/content keys)? Any flakiness or false-pass risk?
- tests/test_overnight/test_cke_client_stdout_contract.py drives real extract_sync against a fake cke script, monkeypatching only _resolve_cke_cmd (resolution), asserting the parsed total/done/error/skipped/cost/tiers dict. Is _parse_summary genuinely exercised?
- Five tests/test_retrieve/*.py files replaced hand-copied _TEST_SCHEMA replicas with an import of corp.index_builder._SCHEMA. Any behavior change or broken insert from using the canonical schema?
No production code changed.

---

## Findings
Two High-severity merge blockers found.

```text
## CRITICAL

(none)

## HIGH

### HIGH tests/rfp/test_vault_adapter_cli_seam.py:100 — Seam test can skip or execute an unrelated CLI

What: The test skips when `corp` is absent and otherwise executes whichever `corp` binary appears first on PATH, without pinning it to the current checkout.
Why: A source-only environment can silently omit the seam gate, while a stale/global installation can pass even if the checked-out producer is broken.
Fix direction: Treat a missing CLI as failure and invoke a test-owned entry point tied to the current interpreter and checkout, while retaining the real subprocess boundary.

### HIGH tests/test_overnight/test_cke_client_stdout_contract.py:38 — Synthetic producer makes the contract test circular

What: `_FAKE_CKE_SCRIPT` hand-copies the exact labels expected by `_parse_summary`; the real CKE summary-producing code is never exercised.
Why: `_parse_summary` itself is genuinely exercised, but a real producer drift such as `Done:` becoming `Completed:` leaves this test green—the precise regression it claims to catch.
Fix direction: Generate stdout through the real CKE formatter/CLI under controlled dependencies, or isolate the production summary renderer and contract-test its output against `_parse_summary`.

## MEDIUM

(none)

## LOW

(none)
```

The canonical `_SCHEMA` replacements introduce no broken inserts or material behavior changes in the five retrieval test files: their inserts name columns explicitly, and the additional FTS columns safely receive `NULL`.
