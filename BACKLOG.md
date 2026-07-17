# corp-monorepo BACKLOG

## Big picture

corp-monorepo is **Corporate OS** — the knowledge extraction, ingestion, and retrieval
engine for Blue Yonder presales. This backlog is organized on the **product axis** of the A3
target-architecture ruling (`docs/audits/2026-07-17-a3-target-architecture-ruling.md`, R1–R10):
first a safe substrate, then engine hygiene (the signed Arc-B kills + Arc-C canonical homes),
then seam contracts, then — elevated by **R10** — the knowledge loop and the vault/ontology
essence layer ahead of the RFP rewrite, and finally ops/models/docs.

**Themes (backbone), in R10 priority sequence:** [E1] Substrate & safety · [E2] Engine hygiene
(Arc B/C) · [E3] Seam contracts & testing · [E5] Knowledge loop · [E6] Vault & ontology ·
[E4] Retrieval & RFP · [E7] Ops, models & docs.

> **Sequence vs. identity (R10, D3):** theme **ids** (`[E1]`…`[E7]`) are stable identities;
> the **file sequence** carries priority. R10 elevates the knowledge loop (E5/E6) above the RFP
> rewrite (E4), so `[E4]` deliberately appears after `[E6]` — this is intended, not a mis-order.

---

## [E1] Substrate & safety (F0)
> As a maintainer, I want the safety substrate and pre-R1 correctness fixes in place, so every later arc builds on a floor that can't leak or silently drop data.

### [S1] Land the F0 substrate and pre-R1 fixes
So that the vault-writer scanner covers the whole repo, the extraction path stops mis-scoring and silently dropping, and the backup topology is sanctioned.
- [#16] [P1][M] Extend the ADR-27 PR-3 vault-writer scanner to full-repo coverage + run the exemption sweep · Done when: the scanner runs over the whole tree and every write outside the `01_Knowledge` writer / actions whitelist is either flagged or exempted with a recorded reason · refs ADR-27, R7
- [#17] [P1][S] Fix the score-inversion bug + add the silent filter-drop retry in the extraction path · Done when: extraction scores rank the right way and a filtered-out candidate is retried (not silently dropped), covered by a regression test · refs code-quality audit (pre-R1)
- [#18] [P2][M] ADR-35 amendment — backup leg-2 → personal OneDrive (operator's second account) replacing the auth-blocked Google-Drive leg; Google demoted to optional leg-3 · Done when: an amending/superseding ADR (or the sanctioned in-file append-only amendment marker) records leg-2→personal-OneDrive as Accepted, and the X1 build targets it — no free edit of the Accepted ADR body · refs ADR-35 · CLAUDE.md §5 rule 3 (ADR immutability — supersede via new/amending ADR, not in-place edit)

---

## [E2] Engine hygiene (Arc B/C)
> As a maintainer, I want the signed dead code cut and every stray responsibility given one canonical home, so the engine is lean and the layer graph is honest.

### [S2] Execute the signed Arc-B kills (one revertable commit per batch)
So that each signed KILL row lands as an independently-revertable commit per the signed manifest.
- [#21] [P2][S] Arc-B batch 3 — KILL the dead inbox lane in `ingest/router.py` (`_run_extraction`/`_run_package_extraction`); `move_to_vault` KEEPS · Done when: the dead-lane boundary is witnessed then cut, `move_to_vault`'s 6 live sites intact, suite green · refs signed manifest Batch 3 · R4
- [#22] [P2][M] Arc-B batch 4 — KILL the N4 task-manager cascade (`task_manager.py`, `cli/task.py`, `actions/task_actions.py`, Task models, chat wiring, tach, 25 tests) per the recorded operator zero-use word · Done when: the cascade is removed, tach/chat de-wired, suite green · refs signed manifest Batch 4 (gated → signed KILL) · R4
- [#23] [P2][S] Arc-B batch 5 — KILL `extractor/frames/tagger.py` + `extractor/frames/extractor.py` (0 callers); `frames/` package stays · Done when: both modules removed, `frames/` package intact, suite green · refs signed manifest Batch 5 · R4

### [S3] Unify canonical homes and clear engine debt (Arc C)
So that config/vocabulary/pricing/frontmatter/LLM-JSON/CKE-invoker each resolve to one home per R5, and the residual hygiene debt is cleared.
- [#24] [P2][M] Move vocabulary → `schema` · Done when: vocabulary constants live under `schema` and importers are migrated, tach clean · refs R5
- [#25] [P2][M] Build one models+pricing registry from the live per-provider dicts (`ANTHROPIC_PRICING`, `GEMINI_PRICING`) · Done when: a single registry is the source of truth and both providers read from it (no per-file dicts) · refs R5 (registry to be BUILT)
- [#26] [P2][M] Move frontmatter → `vault_io` · Done when: frontmatter read/write lives in `vault_io` and importers are migrated, tach clean · refs R5
- [#27] [P2][S] Move LLM-JSON helpers → `schema.utils` · Done when: LLM-JSON parsing lives in `schema.utils` and importers are migrated · refs R5
- [#28] [P2][M] Merge the CKE invoker to ONE (`project/cke_invoker` + `overnight/cke_client`) with an explicit subprocess contract · Done when: a single corp-side invoker drives CKE and the old two are gone · refs R2, R5
- [#29] [P2][L] Migrate `config` → the `PipelineConfig` family (migrate all `corp.config` importers) — the capstone unification · Done when: production config resolves through `PipelineConfig` and `corp.config` importers are migrated, tach clean · depends-on: #21, #22, #23 · refs R5 (cut before unify)
- [#30] [P3][S] Un-exempt `src/corp/test_pipeline.py` from the tach layer exemptions · Done when: the tach exemption is removed and the layer check passes · refs R8
- [#31] [P3][M] RC-14 broader dead-code sweep as its own future manifest · Done when: a signable RC-14 sweep manifest is produced (execution is a separate signed arc) · refs code-quality audit RC-14 (DEFER)
- [#11] [P3][M] Remove verified dead code from the 2026-04-17 audit (re-confirmed live 2026-06-03): dead PDF helpers `extractor/extract.py:_try_pdf_multimodal`/`_try_pptx_pdf_multimodal` + zombie `tests/extractor/test_pdf_multimodal.py`; orphan `extractor/frames/extractor.py`/`tagger.py`; duplicate `_log_ingest_event`; unpackaged `extractor/scripts/{batch_compress,compress_video,preprocess_audio}.py` · Done when: each is deleted or wired and a re-run audit is clean · refs dead-code-audit 2026-04-17 (H1–H4, M1, M3)
- [#12] [P3][S] Ruff-format the committed `src/` tree so `dev-check.ps1` stops mutating the working tree · Done when: `ruff format --check src/` and `ruff check src/` both exit 0 · refs dev-check gotcha (2026-06-03)
- [#13] [P3][M] Sanitize fixtures and archives of real internal paths (`scripts/phase2_plan.json`, `tests/extractor/fixtures/*`, `models/classifier_train.json`, `docs/archive/2026-03-26_VAULT_MANIFEST.json`) — replace real OneDrive/MyWork paths + recording titles with synthetic equivalents · Done when: the pre-push sensitivity sweep shows zero real internal paths in tracked files · refs sensitivity sweep 2026-06-06

---

## [E3] Seam contracts & testing (Arc D)
> As a maintainer, I want the module seams contract-tested and each process runnable end-to-end in a sandbox, so refactors can't silently break a boundary.

### [S4] Contract-test the seams and stand up sandbox e2e
So that the T6 seams have contract tests, CKE's summary-renderer is isolated and non-circular, and every process runs e2e in a sandbox.
- [#32] [P2][M] Add T6 seam contract tests A/C/D/E · Done when: each of seams A/C/D/E has a contract test that fails on a boundary violation · refs T6 brief (N2)
- [#33] [P2][M] Isolate the CKE summary-renderer + add a non-circular producer test · Done when: the renderer is a separate unit and a test proves the producer→renderer path is non-circular · refs R2 follow-up, T6
- [#34] [P2][M] Stand up sandbox end-to-end runs per process · Done when: each process (ingest, extract, retrieve, rfp) has a green sandbox e2e run · refs P2 pillar

---

## [E5] Knowledge loop (W1 restart / R2 — ELEVATED per R10)
> As an operator, I want the knowledge-capture loop restarted and source value scored, so the system learns where valuable knowledge lives and pulls it in first.

### [S5] Restart the knowledge-capture loop
So that the registry gates on quality, the scout forages under a bandit queue, magistrala routes drops, and the outstanding ingest fixes land.
- [#35] [P1][M] Registry v4 gate + zone renames (DR-6/7) · Done when: the registry dry-run gate is >80% and zones are renamed per DR-6/7 · refs DR-6/7, FR-3
- [#36] [P1][L] Scout foraging pilot (FR-11) with a bandit-governed queue · Done when: the scout runs a pilot cycle and the bandit queue orders candidates by predicted yield · depends-on: #35 · refs FR-11 (bandit queue)
- [#37] [P1][M] Restart magistrala inbox-drop routing · Done when: an inbox drop routes to the right zone via magistrala without manual handling · refs FR-3
- [#3] [P1][S] Wire `check_near_duplicate()` (`ingest/dedup.py`, MinHash) into `inbox.py::process_file()` after `light_scan()` · Done when: the `content_signatures` table is consulted at ingest, fail-open · refs HANDOFF Pending Fixes #1
- [#4] [P2][S] Fix the Cognitive-Friday `session_id` truncation (unquoted hyphen in `session_id: "cognitive-friday-season-2`) — quote at source or normalize on ingest · Done when: the two skipped notes ingest · refs HANDOFF Pending Fixes #2 (routed to E5 as a data/ingest fix — D1)
- [#5] [P3][S] Re-extract the two low-quality JLR notes (score 28–29 vs threshold 25) with a deeper prompt (P3: polish) · Done when: both clear the comfort band · refs HANDOFF Pending Fixes #3
- [#6] [P2][M] Bulk-rename ~585 MyWork files to naming v2 `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}` (sandbox pipeline tested) · Done when: the cutover runs + `corp folder-review` stays at 0 renames · refs ADR-14
- [#7] [P2][M] Build an Outlook email-ingestion pipeline into the ingest path · Done when: inbox email content ingests without manual file routing · refs HANDOFF Open Decisions #9

### [S6] Score and map source value
So that every registry record carries a value score, the scout consumes it, and one report answers "where do valuable files live".
- [#38] [P2][M] Source-value scoring v1 — a deterministic per-record score (type/recency/curation/operator-priors) with a neighbor-propagation prior · Done when: every registry record carries a `value_score` and the scout's bandit queue consumes it · refs FR-11/FR-14
- [#39] [P2][M] Terrain analytics — a heatmap/report over the FR-13 observation events · Done when: one report answers "where do valuable files live" · refs FR-13
- [#40] [P1][S] Registry day-1 seed — three operator golden sources (Cognitive Fridays · BY Product Documentation · BY Platform, under the BY OneDrive) entered with max priors · Done when: the three seeds resolve via Graph METADATA listing only; the scout NEVER filesystem-traverses the synced "OneDrive - Blue Yonder" tree (hydration invariant) · refs FR-10, core-invariant #1

---

## [E6] Vault & ontology (ADR-34, FR-15–19)
> As an analyst, I want the vault essence layer, its ontology, and its metadata charter enforced, so notes form a navigable, synthesized knowledge spine.

### [S7] Build the essence layer, ontology, and metadata charter
So that the vault has a generated spine + prep-view, a synthesis rule, an enforced metadata charter with auto-tagging, and a telemetry spine feeding the learning loop.
- [#41] [P1][M] Vault spine + prep-view (FR-15) · Done when: a generated MOC spine exists and the prep-view contract renders it · refs FR-15, ADR-34
- [#42] [P2][M] Synthesis production rule (FR-16) · Done when: the synthesis rule produces a synthesized note from its source set on a real example · refs FR-16
- [#43] [P2][M] Metadata-charter enforcement (FR-18) + deterministic auto-tagger (FR-19) · Done when: the charter is enforced at write time and the auto-tagger tags deterministically · refs FR-18/FR-19
- [#44] [P2][M] Ontology day-1 slice (FR-17) · Done when: a first ontology slice is canonicalized at the index-build seam · refs FR-17
- [#45] [P1][M] FR-13 telemetry spine per the reconciliation doc · Done when: one `event_class`-discriminated write path validates a kinetic-action AND an observation event · refs FR-13 reconciliation (`docs/audits/2026-07-17-fr13-event-schema-reconciliation.md`)
- [#46] [P2][S] FR-18 source-record metadata class — fields `value_score`, `location`, `modified`, `last-verified` · Done when: source records carry the four fields and the charter validates them · refs FR-18
- [#47] [P3][S] FR-20 Content Manifest — CANDIDATE row (P3: candidate; unratified, originates here not in the intake) · Done when: FR-20 is ratified or explicitly dropped by an operator ruling · refs A3 ruling doc (candidate)

---

## [E4] Retrieval & RFP (R1)
> As an analyst, I want RFP + vault retrieval unified and the RFP composer rebuilt, so every benchmark query resolves through one grounded path.

### [S8] Unify retrieval and rewrite the RFP composer
So that federation lands, `rfp/` is a composition target with salvaged mechanics, the answer-policy matrix is wired, and the store/provenance questions are resolved.
- [#48] [P2][M] Implement ADR-33 INDEX_EXTRA_ROOTS federation · Done when: RFP KB and vault retrieve through one federated index path · refs ADR-33 (supersedes ADR-22)
- [#49] [P2][L] Rewrite `rfp/` as a composition target (R3), salvaging anonymization + Excel/Word mechanics + selector scoring · Done when: the composer produces a grounded RFP answer via the rebuilt path; KB-JSON path stays dead · refs R3, ADR-33, ground-truth D-7
- [#50] [P2][M] Wire the answer-policy matrix v1 (DR-13) · Done when: the reuse-vs-derive gate + verify/abstain policy is enforced on a composed answer · refs DR-13
- [#51] [P3][S] Author the section-library ⟷ RFP-store ADR (T6 D1) · Done when: an ADR records the section-library/RFP-store boundary · refs T6 D1
- [#52] [P3][S] Resolve the KB provenance question (unparks here) · Done when: a recorded decision fixes KB provenance handling · refs A3 ruling doc
- [#1] [P2][M] Define the canonical product map that resolves the semantic product-grouping queries (Q4/Q5/Q7/Q8) · Done when: the 4 ontology-blocked benchmark queries answer · refs HANDOFF Open Decisions #5
- [#2] [P2][M] Implement `corp rfp-index` + the `rfp_entries` FTS5 table + grouped `corp retrieve --source all` · Done when: RFP KB (1,325 entries) and vault (~488 notes) retrieve through one path · refs ADR-22 (superseded by ADR-33 — fold into #48)

---

## [E7] Ops, models & docs
> As a maintainer, I want the as-is docs rewritten once the engine settles, model tiers evaluated, and ops loose ends closed, so the repo's self-description matches reality.

### [S9] Rewrite the as-is docs and close ops/model loose ends
So that ARCHITECTURE/CLAUDE match the post-Arc-B/C tree, the skill-eval checkpoint runs, and the model/README loose ends close.
- [#53] [P2][L] Arc-E: rewrite the project `CLAUDE.md` layer + `ARCHITECTURE.md` codemap ONCE, after Arc B/C land (R9 gate) · Done when: both docs describe the post-execution tree and pass the freshness gate · depends-on: #29 · refs R9
- [#54] [P3][S] Add the ADR-32 README row · Done when: the README reflects ADR-32 · refs ADR-32
- [#8] [P2][S] Run the 30-day skill-eval checkpoint against the locked stratified 80/20 split (ADR-16; baseline 2026-03-26, past due) · Done when: the checkpoint runs by 2026-07-31 and classifier/tag/product/people drift is reported · refs ADR-16
- [#9] [P3][M] Evaluate Ollama for an offline/private extraction tier · Done when: a feasibility decision is recorded · refs HANDOFF Open Decisions #8

---

**About this file** — ADR-66 story-map (Big Picture → Theme → User Story → Task). Stories are
human (goal + `So that`); tasks carry `[#id] [P][size] · Done when · refs` and optional
`· depends-on: #a, #b` hard-precedence edges. Done tasks **leave** (ADR-65); git + the JOURNAL
are the implementation record. Reorganized 2026-07-17 from the operational axis (old E1–E5) onto
the **product axis** of the A3 target-architecture ruling
(`docs/audits/2026-07-17-a3-target-architecture-ruling.md`).

**Grooming log:** 2026-05-18 (stream-format seed) · 2026-06-02 (story-map migration) · 2026-06-03
(added Safety theme; #10–#12) · 2026-06-06 (#13) · 2026-07-07 (#14 added+closed) · 2026-07-13 (T1
canonical baseline: `[E1]`–`[E5]` + `[S1]`–`[S5]` ids; wired `validate-backlog`, ADR-78) ·
2026-07-16 (#15 added+closed) · **2026-07-17 (product-axis rebuild — A3 ruling).** Reorganized
onto the A3 product axis (7 themes E1–E7 in R10 priority sequence E1→E2→E3→E5→E6→E4→E7; theme ids
are identities, sequence is priority). New tasks #16–#54. All prior open tasks preserved with new
homes — absorbed-id map: #1,#2→E4 (#2's ADR-22 superseded by ADR-33); #3,#4,#5,#6,#7→E5 (#4 routed
to E5 as a data/ingest fix, D1); #8,#9→E7 (#8 re-dated 2026-07-31); #11,#12,#13→E2. **#10 CLOSED**
this rebuild (ADR-65): the path-traversal guards are implemented (`cleanup/executor.py` — `MoveEntry`
load-time rejection of `..`/absolute on source/destination/proposed_name + `_assert_within_root`
resolve/relative_to at both join sites, firing before any `unlink`/`shutil.move`) and test-covered
(`tests/test_cleanup/test_onedrive_safety_p1_2.py`, 7 tests); Done-when met, item leaves the file.
#14/#15 remain closed (retired earlier). Next quarterly: 2026-10-01.
