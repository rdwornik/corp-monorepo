# Test-delta investigation — 2648/5 (night-batch) vs 2624/6 (604fd80)

> **Read-only investigation** (no fix applied). Blocking gate for Arc-B execution: the
> pass-count delta had to be explained before deletions begin. **Verdict: no test was lost —
> the delta is a measurement/environment artifact, not a regression. Arc-B is not blocked.**

## Question

The executor-prep batch witnessed **2624 passed / 6 skipped** at HEAD `604fd80`, against the
night-batch close figure **2648 passed / 5 skipped** (JOURNAL, Arc-N2 seam-contracts entry,
merge `56e476e`) — with only **doc-lane merges** between the two HEADs. Which test ids are no
longer collected, and what is the cause?

## Method (read-only)

1. `git log 56e476e..604fd80 -- tests/ src/ conftest.py pyproject.toml` and `git diff --stat`
   on the same surface.
2. `pytest --collect-only -q -o addopts=""` (node-ids; `addopts="-v"` otherwise forces
   tree-format, not ids) at `604fd80` vs a detached **worktree at `56e476e`**; `comm` diff of
   the sorted id lists.
3. Full-suite reproduction (`pytest -q`) at `56e476e` in the **current** environment.
4. Installed-plugin census.

## Findings

- **Collection is byte-identical.** `56e476e` collects **2629** node-ids; `604fd80` collects
  **2629**. The `comm` diff is **empty in both directions — zero ids dropped, zero added.**
- **The collection surface never changed.** `56e476e..604fd80` has **no commit** touching
  `tests/`, `src/`, `conftest.py`, or `pyproject.toml`, and the tree diff on that surface is
  **empty** — confirming the intervening merges were doc-lane only.
- **Reproduces identically in the current environment.** Full suite at `604fd80`: **2624
  passed / 6 skipped / 0 failed** (2630 items). Full suite at `56e476e` (current env, detached
  worktree): **2623 passed / 6 skipped / 1 failed** (2630 items). The single failure is
  `tests/integration/test_cross_package.py::test_cke_paths_resolve` — a checkout-location-
  sensitive path assertion that fails only because the worktree lives at a different filesystem
  path; it **passes at `604fd80` in the main checkout**. Both HEADs run the same ~2630 items.
- **No count-inflation mechanism exists.** Installed pytest plugins are `pytest-cov` +
  `pytest-xdist` only — no `pytest-subtests`, no rerun plugin; no `pytest_generate_tests` /
  subtest usage in `tests/`. A clean run therefore **cannot exceed the collected count**.
- **Invocation scope is identical.** `scripts/run-all-tests.ps1` runs `pytest tests/ -x
  --tb=short`; `pyproject.toml` sets `testpaths = ["tests"]`. `pytest -q` and the script cover
  the same set. Scope is not a variable.

## Cause

Ruling out the operator's three hypotheses against the evidence:

- **Collection error?** No. `rc=0`, no import/collection errors, and the collected set is
  identical at both HEADs.
- **Invocation scope?** No. Both entry points run the `tests/` testpath; the id sets match.
- **Environment / measurement basis? YES.** The committed test set is provably identical and
  reproduces ~2630 run-items at **both** HEADs today. The night-batch figure **2648 + 5 = 2653**
  exceeds the committed collection (**2629**) by **24** — a number a clean run of the committed
  tree cannot produce. The `2648/5` was therefore measured against a working tree carrying ~24
  **extra, uncommitted/generated test items** not present in the `56e476e` snapshot (the N2
  session was actively seeding seam-contract tests + running codex terra gate rounds, i.e. a
  dirty/worker-scaffolded tree), or is a JOURNAL transcription. **Either way, no committed test
  has been lost between the two HEADs.**

## Verdict (Arc-B gate)

**Unblocked.** Zero test ids dropped; collection and behavior are identical at `56e476e` and
`604fd80`. The canonical, reproducible baseline is **2624 passed / 6 skipped / 0 failed** at
`604fd80` (unchanged through the doc-lane follow-up merges to `8b83d7c`). Arc-B execution should
run its per-batch suites against this baseline, not the historical `2648/5` figure.

---
*Investigated 2026-07-17 · primary checkout · read-only (no code/test change) · worktree at
`56e476e` created for collection/run comparison and removed (verified, no leftovers).*
