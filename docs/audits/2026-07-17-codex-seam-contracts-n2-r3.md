# Codex Review — seam-contracts-n2-r3

**Date:** 2026-07-17
**Branch:** `test/seam-contracts-seed`
**HEAD:** `739e424`
**Diff range:** `main..test/seam-contracts-seed`
**Codex version:** codex-cli 0.144.5
**Mode:** diff-review

---

## Focus

Convergence re-review (tests-only). The retrieve-seam test now pins the child to THIS checkout's corp PACKAGE, not just the launcher: the fixture prepends the checkout src/ to PYTHONPATH (inherited by subprocess.run), and the test probes [sys.executable -c import corp] asserting the child's corp.__file__ is under src/. The real corp-retrieve child inherits the same os.environ, so the probe reflects what it imports. Confirm the stale-editable/global-corp false-pass risk is closed while keeping the real subprocess boundary.
The cke stdout-contract test's fake-cke scope (pins the corp-side _parse_summary; CKE-side label drift deferred as it needs an out-of-scope production refactor across the corp->CKE subprocess boundary) was accepted last round.
Report only genuinely NEW realistic defects in the shipped tests.

---

## Findings
```text
## CRITICAL
(none)

## HIGH
(none)

## MEDIUM
(none)

## LOW
(none)
```

The `PYTHONPATH` pin and child import probe close the stale editable/global `corp` false-pass risk while preserving the real subprocess boundary. All 71 scoped tests collect successfully.
