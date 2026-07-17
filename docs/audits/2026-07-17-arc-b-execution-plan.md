# Arc-B Execution Plan — corp-monorepo (executor architect) · 2026-07-17

> **Status:** APPROVED by the senior architect (Layer-1, via operator) 2026-07-17 — one arc
> approval covering Arc-0 (done, read-only) + Arc-B (the five signed batches). Q-A/Q-B answered
> and riders R1/R2 folded in (§Resolved). This is the execution record of record for Arc-B.
>
> **Model:** Opus (Batches 2/3/4 — boundary precision + widest blast radius; Sonnet acceptable
> for Batches 1/5 only, R1) · **Mode:** plan-then-auto · **Effort:** high.
> **Base HEAD:** `5a3de94` (`main`, clean). **Base prompt:** hub bundle
> `PROMPT_arc-b-execution.md`, amended here only by the predict-then-verify collection gate and
> the pinned pytest-9 baseline (Arc-0) — no batch semantics changed.

---

## 0. Reconciliation vs the base onboarding note — divergences flagged

Reconstruction matched on ROLE, reading map, FIXED set, and the four senior amendments. Genuine
divergences recorded (they do not alter Arc-0/Arc-B scope; they shape §3):

- **OPERATOR VISION** (off-repo, not recoverable from the charter) — three items:
  1. **Sandbox-simulation acceptance bar** — the substrate phase is "done" only when a sandbox
     sim of the full T6 one-client thread runs (Project_Codes → magistrala → vault → Excel/Word
     answer + deck slide). Simulation before optimization. **Phase-level, not Arc-B** (Q-A).
  2. **URL/source registry (FR-10) + source-value scoring is the FOUNDATION STONE** — underpins
     file mgmt, directory mgmt, the magistrala, and every downstream flow; load-bearing, not one
     feature. E5 framing in §3 raised accordingly.
  3. **demo-prep is the connective repo** (403-slide master deck, brand spec v2, section library
     exist) → at the T6 succession **verify and absorb, never rebuild**. Shapes E7/T6, not Arc-B.
- **NOT-list has two framings; the union is honored:**
  - charter §3: no microservices · no service mesh · no message bus
  - base note: no microservices · **no literal PageRank** · reference-not-copy
  - "No literal PageRank" directly constrains the E5 source-value scoring (§3).

## 1. Arc 0 — BLOCKING GATE (read-only; DONE before plan approval)

### 1a. Delta diagnosis (2648/5 night-batch → 2624/6 at `604fd80`, doc-only merges between)
Cause = **environment / measurement basis, NOT a regression. No committed test lost.**
Evidence (`docs/audits/2026-07-17-test-delta-investigation.md`, re-confirmed this session):
collection byte-identical (2629) at `56e476e` and `604fd80`, `comm`-diff empty; the collection
surface (`tests/`/`src/`/`conftest.py`/`pyproject.toml`) has zero commits and zero diff across
those heads. Night `2648+5=2653` exceeds committed collection (2629) by 24 → measured against a
dirty/worker-scaffolded or differently-provisioned tree (e.g. optional deps present), or a
transcription. Trust in the suite is restored.

### 1b. Trusted baseline PINNED at current HEAD `5a3de94`, pytest 9.0.2
- pytest **9.0.2** · Python 3.12.10 · pluggy 1.6.0
- plugins: anyio-4.13.0, hypothesis-6.151.10, cov-7.1.0, xdist-3.8.0, tach-0.35.0
- `addopts = "-v"` · `testpaths = ["tests"]`
- collection (`--collect-only -q`): **2629 node-ids**
- full run (`-q`): **2624 passed, 6 skipped, 0 failed** (156.9s, rc=0)

### 1c. Zero-remainder reconciliation (each term named)
```
2629 collected items  ==  2624 passed + 5 item-level skipped     (comm-diff collect vs run EMPTY)
+  1 collection-phase skip  (tests/test_ingest/test_dedup.py:13 importorskip 'datasketch' absent)
------------------------------------------------------------------
= 2630 total outcomes  =  passed 2624 + skipped 6 + failed 0 + xfailed 0 + xpassed 0
                          + errors 0 + deselected 0
The 6 summary-skips = 5 runtime item-skips (within the 2629) + 1 collection-phase module skip.
```

### 1d. Environment caveats (baseline is env-conditioned) — see standing gate R2
- pytest MAJOR line (8.x → 9.0.2) since the baseline was first witnessed; +anyio/hypothesis/tach
  now live (the investigation recorded cov+xdist only). Collection stable at 2629 across the drift.
- The 2629 count is conditioned on optional deps **absent** (`datasketch`). Installing it would
  collect `test_dedup.py` and raise the count — a likely contributor to the historic 2648.

## 2. Arc B — execute the five SIGNED manifest batches

**Contract** (signed manifest §Execution + hub prompt): branch `feat/arc-b-execution` off `main`;
ONE revertable commit per batch, in order; full suite (`./scripts/run-all-tests.ps1`) after each —
red suite STOPS the arc at that commit; terra codex-review on the **cumulative final diff** before
merge (synchronous, not deferred); `./scripts/dev-check.ps1` before PR; one `--no-ff` merge; push
after gates-green; JOURNAL SHA-anchored; each commit closes its `[#id]`. **Exclusions KEEP:**
`resolve_product_key`, `move_to_vault`, `BatchJobRunner`. No DEFER-field row.

**PRECONDITION:** the green + reconciled Arc-0 re-pin (§1b/1c, DONE) gates Batch 1.

**PREDICT-THEN-VERIFY** — metric = **collect-only node-id count vs the 2629 baseline**, measured
identically each batch; **predicted == actual after each batch or STOP + report, no next batch.**
Full-suite green/red is a separate, parallel gate.

| Batch | # | Deletions (signed rows) | Pred. collect Δ |
|---|---|---|---|
| 1 cost_tracker | 19 | `cost_tracker.py` (whole) + 2-of-23 methods in `test_providers.py` | **−2** (exact) |
| 2 facts repoint | 20 | facts DDL/loader/`facts_count`; `search_facts`→notes_fts; REWRITE facts fixtures | **EXACT-AT-DRAFT** (est. ~0, rewrite-in-place) |
| 3 inbox lane | 21 | `router.py` `_run_extraction`/`_run_package_extraction` (SRC only; boundary witnessed) | **0** (verify no test imports internals) |
| 4 task-mgr cascade | 22 | task_manager + cli/task + task_actions + Task models + chat wiring + tach + `test_task_manager.py` (25) | **−25** (exact) |
| 5 frames limbs | 23 | `frames/tagger.py` + `frames/extractor.py` (SRC only, 0 callers) | **0** (verify no frames test imports them) |

**NET predicted collection: −27 → 2602** (± Batch-2's pinned exact number).

**Batch-specific rules:**
- **Batch 2 EXACT-DELTA:** the "~0" is an estimate, NOT a gate. The executor drafts the fixture
  rewrite, counts the exact node-id Δ it produces, RECORDS that integer in the commit body BEFORE
  running, and — as the one batch whose Δ is not derivable at plan time — **surfaces it to the
  senior before the Batch-2 commit** (Q-B touch 1). Then verify actual == pinned. Run
  `corp index rebuild` after the repoint to clear on-disk `facts`/`facts_fts`/`facts_count` residue.
- **Batch 3:** witness the exact dead-lane boundary and document it in the commit body BEFORE
  cutting; never sever the live `corp ingest` path or `move_to_vault` (6 live sites). **Surface to
  the senior ONLY IF the witness deviates from the manifest premise** — any live reference to the
  internals = STOP + report; a clean witness proceeds without asking (Q-B touch 2).
- **Batch 4:** fires — the operator's zero-use word IS recorded in the signed manifest sign-off.
  One commit for the whole cascade; chat status panel loses the todo count (expected). **Runs at
  Opus-grade attention** — widest blast radius of the arc (R1).
- **Batch 5:** `frames/` package STAYS (`sampler.py`, `scene_detect.py` live).

## 3. Road ahead — headline only (senior read of the map)

- **Arc-C wave 1** (canonical homes not gated on the config capstone): LLM-JSON → `schema.utils`
  (#27), frontmatter → `vault_io` (#26), models+pricing registry BUILT from live per-provider
  dicts (#25).
- **E5 registry FOUNDATION** (OPERATOR VISION #2 — the foundation stone): FR-10 URL/source registry
  + source-value scoring, load-bearing for file/dir/magistrala/downstream. Scoring must **NOT** be
  literal PageRank (NOT-list). Depends-on: #36 scout AFTER #35 registry-v4 gate.
- **Substrate acceptance bar** (OPERATOR VISION #1, Q-A phase-level): sandbox simulation of the T6
  one-client thread — gates SUBSTRATE-PHASE closure (post Arc-C / E5 context), **not** Arc-B.
- **Code-review candidate set** — OUT of Arc-B; a night-batch arc sequenced AFTER Arc-B lands so
  improvement never races the deletions on shared files:
  - CR-1 ADR-27 PR-3 — full-repo Decision-1 scanner + `@onedrive_write_exempt` sweep (deferred N1)
  - CR-2 ADR-27 PR-4 — vault-writer narrowing coverage — confirm/ship
  - CR-3 CKE renderer — isolate `extractor/scripts/run.py` summary renderer → non-circular producer test (R2 follow-up)
  - CR-4 ADR-32 row — README row (named in addendum)
  - CR-5 N1 boundaries — full CFG dominance in AST scanner; `--copy-to-vault` dir-TOCTOU (accepted boundaries)
  - CR-6 N2 boundary — CKE-side stdout label drift across the corp→CKE process boundary
  - (Distinct from the manifest DEFER field — ChromaDB fallbacks, rfp-KB D-7 orphan, RC-14 set —
    a separate FUTURE DELETION manifest, not this review arc.)

## Resolved (senior review 2026-07-17)

- **Q-A → PHASE-LEVEL.** The sandbox-simulation acceptance bar gates substrate-phase closure (post
  Arc-C / E5 context), not Arc-B. **Arc-B closes on its own gates:** per-batch suite green +
  predicted==actual collection Δ + terra clean + `--no-ff` merge + push + JOURNAL.
- **Q-B → ONE arc approval + auto-execution** of the five batches under the STOP gates. Mid-arc
  senior touches are exactly two, both conditional: (1) Batch 2 — surface the pinned exact Δ before
  its commit; (2) Batch 3 — surface ONLY IF the boundary witness deviates from the manifest premise.
  No other per-batch surfacing; the gates are mechanical.
- **R1 — Batch 4 at Opus-grade attention** (same as Batches 2/3); Sonnet acceptable for Batches 1/5 only.
- **R2 — §1d env-conditioned baseline is a STANDING GATE:** every collect-only measurement in this
  arc runs in the pinned interpreter/plugin/optional-dep env; any mid-arc install/upgrade = STOP and
  re-pin before the next batch.

---
*Codified 2026-07-17 · primary checkout · base HEAD `5a3de94` · Layer-1-approved execution plan.
Arc-0 is read-only and complete; Arc-B executes the SIGNED manifest
(`docs/audits/2026-07-17-deletion-manifest-arc-b.md`, sign-off merge `1a014f0`) — A3-R4 defers to it.*

---

## Addendum B — Batch-2 Option-A deviation + PROPOSED `facts_count` amendment (append-only, 2026-07-17)

> Append-only (audits immutable; the signed manifest is NOT touched). Records the senior-ruled
> Batch-2 scope narrowing and files the deferred `facts_count`-column removal into the operator queue.

**Deviation (senior ruling 2026-07-17, Option A).** Signed manifest row 2.1 marks
`projects.facts_count` (the column) for KILL, but a fresh whole-repo re-grep found ~15 live
consumers the manifest's Batch-2 caller analysis never enumerated, and the column is populated from
**vault-note data** (`_insert_project`), independent of the dead facts loader (its `facts_count`
UPDATE never fires — n≡0). Per "no deletion outside a signed row's real scope," row 2.1's authority
does not reach the live column. **Batch 2 executed the narrowed, witnessed-dead scope only:** facts
table + `facts_fts` + triggers + `_load_and_insert_facts` killed; `search_facts` repointed to
`_search_notes_fts`; the two dead facts-table analytics queries (`get_analytics`) and the facts-table
bookkeeping (`total_facts` meta, `IndexStats.facts_indexed`) neutralised to 0 (facts-table-derived,
behaviour-preserving — facts was 0-rows in production); the residue-clearing `DROP TABLE IF EXISTS
facts/facts_fts` kept so `corp index rebuild` clears existing DBs. **`projects.facts_count` and its
~15 consumers were KEPT untouched.**

**PROPOSED amendment — AMD-1 (not a signed KILL; enters the operator queue; does NOT gate Arc-B):**
- **Target:** remove `projects.facts_count` (column) + the `facts_count` model fields
  (`models.py:81,100,287`) + rewire/retire the ~15 consumers (`search_projects` ordering,
  `ProjectResult`, `get_analytics` avg, briefs, monitoring, 2 CLIs, `vault_io`).
- **Class:** live-field removal / behaviour change to `corp projects` + analytics + briefs — NOT
  dead-code; a separate scoped change, own commit.
- **Gate (both required before it can be signed):** (a) **verbatim consumer enumeration**
  (file:line) — produced by the Codex **luna** read-only evidence lane, landing in `docs/audits/`
  and referenced here; (b) **operator sign-off**.
- **Status:** PROPOSED · not scheduled into Arc-B · surfaced to the operator queue 2026-07-17.
  Distinct from the manifest DEFER field (a separate future *deletion* manifest).

---

## Addendum C — Batch-3 DROPPED + PROPOSED premise correction AMD-2 + revised ledger (append-only, 2026-07-17)

> Append-only (signed manifest NOT touched). Records the senior-ruled Batch-3 drop and the
> falsified premise, and restates the arc collection ledger.

**Batch 3 — DROPPED (senior ruling 2026-07-17, Option A).** The boundary witness falsified signed
row 3.1's "dead inbox lane" premise. deep-magistrala §Step 1 (the manifest's own cited evidence)
states both lanes **share** `_run_extraction` (`router.py:720-810`) as the CKE handoff:
`_run_extraction`/`_run_package_extraction` are the registered handlers behind **`corp ingest`**
(Lane A; `cli/ingest.py:19`, registered `cli/__init__.py:128`) **and `corp ingest-inbox`** (Lane B;
`inbox.py:_trigger_extraction:275` → `_run_extraction:304`, registered `cli/__init__.py:129`). The
"never wrote" runtime observation = extraction gated on `is_available()` (**CKE not wired** in the
pre-operational state), **not** dead code. **No cut made** — both functions KEEP.

**PROPOSED premise correction — AMD-2 (records the falsification; enters the operator queue; does
NOT gate Arc-B):**
- **Finding:** signed manifest Batch-3 row 3.1 rests on a mischaracterisation of deep-magistrala
  §Step 1; its KILL targets are **live, shared, core ingest→CKE→vault infrastructure**, not a dead
  lane. This is an "audit say-so ≠ truth" catch (cf. the `BatchJobRunner` KEEP flip).
- **Disposition:** `_run_extraction` + `_run_package_extraction` **KEEP**. Their fate **re-opens
  only at the CKE-wiring decision (post-simulation)** — not in Arc-B.
- **Status:** RECORDED · Batch 3 closed as DROP · signed manifest left immutable (correction by
  this addendum, per critical-rule 3).

**Revised arc collection ledger (senior-restated):**
```
2629 baseline
 -2  Batch 1 (cost_tracker)        -> 2627   [landed b8b958a]
 -2  Batch 2 (facts repoint)       -> 2625   [landed 5bcf899]
 -0  Batch 3 (DROPPED — premise falsified)
-25  Batch 4 (task-manager cascade)-> 2600   [pending]
 -0  Batch 5 (frames limbs)        -> 2600   [pending]
------------------------------------------------
net predicted final collection = 2600
```
