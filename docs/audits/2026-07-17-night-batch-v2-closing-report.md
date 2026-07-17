# Night Batch v2 — Closing Report (unattended)

**Date:** 2026-07-17 · **Repo:** corp-monorepo · **Mode:** auto/unattended · **Orchestrator:** Opus (dynamic-workflow: fresh-context Sonnet workers per arc, Haiku read-only fan-out, orchestrator-owned serial git + clause-by-clause verification)

## Headline

**All four units merged to `main` — zero blockers.** Step 0 + Arc N1 + Arc N2 + Arc N3. Working tree clean. No pushes (local main only). Every merge `--no-ff`, serial, never two in flight. No `--no-verify`, no OneDrive-zone writes, no deletions.

## Baseline note (read first)

The brief's stated baseline **2,583 passed / 6 skipped** was the ground-truth audit's figure on the *older* HEAD `14a1b09`. The **actual pre-batch tree** (HEAD `f46a781`) measures **2,607 passed / 5 skipped** (rc=0), witnessed at session start. All deltas below are measured against the empirical **2,607 / 5**. Final tree: **2,648 passed / 5 skipped** (rc=0) → **+41** (N1 +39, N2 +2), no regressions, no new skips.

## Merge SHAs

| Unit | Merge SHA | Kind | Codex gate |
|---|---|---|---|
| Step 0 — Codex edge-diff reconciliation | `52ad79f` | docs | n/a (doc-only) |
| Arc N1 — ADR-27 Decision 1 (P0 safety) | `b971488` | code | terra, 4 rounds → 0 Crit/High |
| Arc N2 — seam-contract tests | `56e476e` | tests | terra, 3 rounds → 0 Crit/High |
| Arc N3 — ADR pack (PROPOSED) | `28345d0` | docs | n/a (doc-only) |
| Session-close JOURNAL wrap | `542d16a` | docs | n/a |

---

## Step 0 — Codex edge-diff reconciliation → MERGED `52ad79f`

Content rules — all met:
- **PASS** — Downloads `2026-07-16_codex-edge-diff.md` pinned verbatim into `docs/audits/2026-07-16-codex-edge-diff.md` (byte-identical, own commit `b1e1c80`).
- **PASS** — Append-only reconciliation addendum on the ground-truth audit (immutability amendment marker; original §1c tables untouched), own commit `1f09573`.
- **PASS** — Static 89 + subprocess 6 double-derivation agreement recorded; sole static dispute `__main__→cli` noted as a relative-import definitional frame (changed nothing).
- **PASS** — 39 Codex data-READ bindings tabled; **10-of-39 (~26%) independently spot-verified by a Haiku read-only agent → 10/10 CONFIRMED** against source.
- **PASS** — Disputed data edges (sandbox/test_pipeline writes, project→vault) recorded in BOTH normalization frames, resolved none. The project→vault dispute ("arbitrary input, no production binding") independently confirms the Arc-N1 D6 hole.

---

## Arc N1 — ADR-27 Decision 1 completion (P0 safety) → MERGED `b971488`

Frozen acceptance contract — clause-by-clause:
1. **PASS** — `src/corp/safety/onedrive.py` at tach **foundation** (`utility=true`); `tach check` green.
2. **PASS** — Zero remaining local guard implementations; the four sites are one-line delegations to `guard_path`.
3. **PASS** — `--copy-to-vault` raises `OneDriveSafetyError` (OneDrive dest) and `PathTraversalError` (outside-vault-root dest); both asserted by new `CliRunner` tests (+ a happy-path control + a symlink-refusal test). Hardened past the brief: also defeats a pre-existing **hard link** at the destination via an atomic temp-write + `os.replace`.
4. **PASS** — New AST scanner `tests/safety/test_no_unguarded_writes.py` covers the project vault-write path; existing `test_vault_writer_invariant.py` still covers `actions/`. Scanner is sound (own-scope + lexical dominance, top-level-halt detection, `os.replace` coverage) with anti-vacuity self-tests.
5. **PASS** — Full suite **2,646 / 5** (rc=0), +39, no regressions.
6. **PASS** — `cleanup/errors.py` is a re-export shim (both `OneDriveSafetyError` + `PathTraversalError`); all importers unchanged.

**Codex terra gate: 4 rounds, converged to 0 Critical / 0 High.** The gate did real work — 7 concrete fixes it drove:
- R1 (2C+3H): symlink bypass, renderer detection-narrowing, scanner Rule-1 dominance, scanner Rule-2 conditional-termination, scanner-scope. → fixed the 4 defects; scope reframed.
- R2 (1C+2H): **hard-link** truncation vector (beyond symlinks), arbitrary `.exit()` methods, launcher pin. → fixed (atomic `os.replace`, exact `sys.exit`/`os._exit` match).
- R3 (1H): the atomic-write `os.replace` was invisible to the scanner's `.replace` heuristic. → fixed (recognize `os.*` before the str-heuristic).
- R4: **0 findings** — convergence confirmed.

Decisions/deviations (recorded per unattended rules):
- **Scanner scope** = `project/cli.py` for this batch (contract clause 4 met via it + the existing actions/ scanner). Full-repo Decision-1 coverage = ADR-27 **PR-3** (a ~40-site `@onedrive_write_exempt` sweep) — deliberately deferred (blast radius; out of this batch's scope). Codex accepted the scoping from R2 on.
- **Two beyond-ADR-27-spec codex items declined, documented as accepted design boundaries:** (a) full every-path CFG dominance + guard-argument association — exceeds ADR-27's presence-based Rule 1 (already met + strengthened), and the conditional-guard case is the ADR's own acknowledged limitation; (b) directory-level TOCTOU on a local single-user CLI — out of threat model. Both recorded inline in the code.
- **Renderer detection preserved** (not narrowed): added a `strict=` param so the renderer keeps its broad `onedrive` net while the canonical sites stay `"OneDrive - Blue Yonder"`-only.

---

## Arc N2 — seam-contract tests (ruling-independent) → MERGED `56e476e`

Frozen acceptance contract — clause-by-clause:
1. **PASS** — `corp retrieve --format json` producer↔consumer test is UNMOCKED at the crossing (real subprocess; `subprocess.run` never patched). Non-vacuous (asserts non-empty + `note_id`/`confidence`/`relevance_score`/`content`/`title`). Pinned to THIS checkout's corp: fixture steers the child via `VAULT_PATH`/`APP_DATA_PATH` env + prepends the interpreter's scripts dir and this checkout's `src/` to PATH/PYTHONPATH, with an import probe asserting the child's `corp.__file__` is under `src/` (a stale global corp cannot false-pass).
2. **PASS** — `overnight/cke_client.extract_sync` ↔ CKE stdout contract test drives a fake cke (real `subprocess.run` + real `_parse_summary`; only `_resolve_cke_cmd` steered — no mock on the crossing or on `_run_extraction`); asserts `{total,done,error,skipped,cost,tiers}`.
3. **PASS** — `rg _TEST_SCHEMA tests/` → **0 hits** (killed across 5 files, not 2 — all carried the replica, and two had already drifted). All now import `index_builder._SCHEMA`. retrieve tests green.
4. **PASS** — Full suite **2,648 / 5** (rc=0). **Codex terra: 3 rounds → 0 Crit/High.**

Codex verdicts: R1 (2H: seam skip/unrelated-CLI, fake-cke circularity) → R2 (1H: launcher-vs-package pin) → R3 **0 findings**. Decisions:
- **Fake-cke scope documented + accepted:** the test pins the corp-side `_parse_summary` contract. Catching CKE-side label drift would need a production refactor to isolate the inline summary renderer (`extractor/scripts/run.py:758-775`) and crosses the deliberate corp→CKE process boundary — out of this tests-only arc. Tracked as a follow-up.

---

## Arc N3 — ADR pack (PROPOSED) → MERGED `28345d0`

Frozen acceptance contract — clause-by-clause:
- **PASS** — Four ADRs exist, **all Status: Proposed** (operator ratifies), plain-markdown header per template, each citing its DR row + evidence pointers + a testable **Done-when**:
  - **ADR-33** (DR-1) RFP↔KB federation via `INDEX_EXTRA_ROOTS`; formally supersedes ADR-22 (status-flip deferred to ratification); honors ground-truth **D-7** (`data/kb/canonical` JSON is an orphan → target is the markdown KB).
  - **ADR-34** (DR-2) vault kept as essence layer + obsidian-v2 two-layer LINK/VIEW amendment by reference.
  - **ADR-35** (DR-10+DR-11, one doc) corp-ops separate repo + private remote; dual-leg upload-only backup (BY OneDrive **Graph API** upload-only + Google Drive) + heartbeat + **restore drill**.
  - **ADR-36** (DR-12) storage topology; write boundaries tied to the ADR-27 `corp.safety.onedrive` guards.
- **PASS** — No edits to ARCHITECTURE.md / CLAUDE.md / VISION.md / BACKLOG.md; **ADR-22 not edited** (supersession is a ratification-time action). README got 4 rows.
- **PASS** — Pre-commit gates green. No codex gate (doc-only), correctly skipped.
- Note: the N3 worker **independently re-verified** that `corp.safety.onedrive` exists on the branch (contradicting the stale 2026-07-16 audit snapshot, which predates the N1 merge) and honestly scoped ADR-36's scanner-enforcement caveat.

**Operator ratification actions (morning):** flip each ADR Proposed→Accepted; on ADR-33 ratification, flip ADR-22's status line to "Superseded by ADR-33" (the one sanctioned in-place ADR edit, ADR-94).

---

## Blockers

**None.** All four units merged. No arc left uncommitted or unmerged.

## Guardrails honored

Serial `--no-ff` merges (never two in flight) · no origin pushes · no `--no-verify` · no OneDrive-zone writes/deletes (the guard hook did block one codex command that combined the literal zone string with a redirect token — reworded, not bypassed) · no code/test/file deletions · `src/corp/safety/` was the only new folder (operator-approved on record).

## Follow-ups seeded (not done here)

- ADR-27 **PR-3**: full-repo no-unguarded-writes scanner + the `@onedrive_write_exempt` exemption sweep.
- Isolate `extractor/scripts/run.py` summary renderer → a non-circular cke producer↔consumer contract test.
- Pre-existing gap noted in passing: **ADR-32 has no row** in `docs/decisions/README.md` (unrelated to this batch; left untouched).
- Ratify the ADR pack + wire DR-1/2/10/11/12 into BACKLOG per intake §8.

## Artifacts (in-repo evidence)

Codex gate reviews: `docs/audits/2026-07-17-codex-adr27-safety-n1{,-r2,-r3,-r4}.md`, `docs/audits/2026-07-17-codex-seam-contracts-n2{,-r2,-r3}.md`. Step-0 reconciliation: `docs/audits/2026-07-16-codex-edge-diff.md` + Addendum A on the ground-truth audit. JOURNAL: four 2026-07-17 entries (SHA-anchored).
