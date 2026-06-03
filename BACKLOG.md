# corp-monorepo BACKLOG

## Big picture

corp-monorepo is **Corporate OS** — the knowledge extraction, ingestion, and retrieval
engine for the consultancy's content (vault notes + the RFP knowledge base). The backlog
advances four themes toward complete analytics coverage, reliable ingest, automated file
lifecycle, and measured model quality.

**Themes (backbone):** Knowledge retrieval & analytics · Ingest reliability · File lifecycle & inbox automation · Model evaluation & local tiers · Safety & code health

---

## Knowledge retrieval & analytics
> As an analyst, I want every benchmark query answerable across all knowledge sources, so retrieval is complete and unified.

### Close the analytics benchmark and unify RFP + vault retrieval
So that the remaining benchmark queries resolve and RFP/vault content shares one retrieval path.
- [#1] [P1][M] Define the canonical product map that resolves the semantic product-grouping queries (Q4/Q5/Q7/Q8) · Done when: the 4 ontology-blocked benchmark queries answer · refs HANDOFF Open Decisions #5
- [#2] [P2][M] Implement `corp rfp-index` + the `rfp_entries` FTS5 table in `index.db` + grouped `corp retrieve --source all` (ADR-22) · Done when: RFP KB (1,325 entries) and vault (~488 notes) retrieve through one path · refs ADR-22 (ratified, not built)

---

## Ingest reliability
> As a maintainer, I want ingest to never silently drop or duplicate content, so the knowledge base stays trustworthy.

### Stop ingest from dropping or re-ingesting content
So that every source file ingests once, cleanly, with near-duplicate detection active.
- [#3] [P1][S] Wire `check_near_duplicate()` (`ingest/dedup.py`, MinHash) into `inbox.py::process_file()` after `light_scan()` · Done when: the `content_signatures` table is consulted at ingest, fail-open · refs HANDOFF Pending Fixes #1
- [#4] [P2][S] Fix the Cognitive Friday `session_id` truncation (unquoted hyphen in `session_id: "cognitive-friday-season-2`) — quote at source or normalize on ingest · Done when: the two skipped notes ingest · refs HANDOFF Pending Fixes #2
- [#5] [P3][S] Re-extract the two low-quality JLR notes (score 28–29 vs threshold 25) with a deeper prompt · Done when: both clear the comfort band · refs HANDOFF Pending Fixes #3

---

## File lifecycle & inbox automation
> As an operator, I want file naming and inbox sources under the automated pipeline, so content flows in without manual routing.

### Bring MyWork naming and Outlook content into the pipeline
So that MyWork files follow naming v2 and email content ingests without manual handling.
- [#6] [P2][M] Bulk-rename ~585 MyWork files to naming v2 `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}` (sandbox pipeline tested) · Done when: the cutover runs + `corp folder-review` stays at 0 renames · refs ADR-14
- [#7] [P3][M] Build an Outlook email-ingestion pipeline into the ingest path · Done when: inbox email content ingests without manual file routing · refs HANDOFF Open Decisions #9

---

## Model evaluation & local tiers
> As a maintainer, I want model quality measured and an offline tier available, so drift is caught and sensitive material has a private path.

### Run the skill-eval checkpoint and explore a local extraction tier
So that classifier/tag/product/people drift is caught and offline-only material has a non-Gemini path.
- [#8] [P2][S] Run the 30-day skill-eval checkpoint against the locked stratified 80/20 split (ADR-16; baseline 2026-03-26, past due) · Done when: the checkpoint runs + drift is reported · refs ADR-16
- [#9] [P3][M] Evaluate Ollama for an offline/private extraction tier · Done when: a feasibility decision is recorded · refs HANDOFF Open Decisions #8

---

## Safety & code health
> As a maintainer, I want known security gaps closed and verified dead code removed, so the cleanup pipeline can't escape its root and the tree stays lean.

### Harden the cleanup pipeline and clear verified dead code
So that untrusted `moves.yaml` specs can't traverse outside their root and abandoned modules stop misleading readers.
- [#10] [P2][S] Add path-traversal guards to `cleanup/executor.py:68,85` — `source.resolve().is_relative_to(mywork_root)` gating at both join sites + a Pydantic schema for `moves.yaml` entries rejecting `..` segments and absolute paths at load time + traversal tests in `tests/test_cleanup/test_executor.py` · Done when: a `..`-bearing or absolute `moves.yaml` entry raises before any `unlink`/`shutil.move`, covered by tests · refs Codex P1-2 (verify-p1-2.md, 2026-04-21) — ADR-27 covers the OneDrive guard only, not this traversal class
- [#12] [P3][S] Ruff-format the committed `src/` tree — `ruff format src/` + `ruff check src/ --fix` reformat ~106 files on every `dev-check.ps1` run, indicating committed source has drifted from the current ruff config/version; running the gate mutates the working tree as a side-effect · Done when: `ruff format --check src/` and `ruff check src/` both exit 0 (no changes); `dev-check.ps1` no longer mutates the tree · refs dev-check gotcha (2026-06-03, `.claude/skills/gotchas/gotchas.md`)
- [#11] [P3][M] Remove verified dead code from the 2026-04-17 audit (re-confirmed still-live 2026-06-03): dead PDF helpers `extractor/extract.py:_try_pdf_multimodal`/`_try_pptx_pdf_multimodal` + zombie `tests/extractor/test_pdf_multimodal.py`; orphan modules `extractor/frames/extractor.py` (+ remove ARCHITECTURE.md:219 row) and `extractor/frames/tagger.py`; duplicate `_log_ingest_event` (`ingest/inbox_ops.py:70` vs `ingest/extractions.py:335`); unpackaged `extractor/scripts/{batch_compress,compress_video,preprocess_audio}.py` · Done when: each is deleted or wired/registered and a re-run audit is clean · refs dead-code-audit 2026-04-17 (H1–H4, M1, M3)

---

**About this file** — ADR-66 story-map (Big Picture → Theme → User Story → Task), migrated
2026-06-02 from the ADR-41/47 stream schema per ADR-38 A6 (canonical backlog form, all
repos). Stories are human (goal + `So that`); tasks carry `[#id] [P][size] · Done when · refs`.
Done tasks **leave** (ADR-65); git is the implementation record. The 3 items closed before
this migration (ruff-select Action 7c; VISION-routing Action 6 ×2) left the active file per
ADR-65 — recorded in the 2026-06-02 JOURNAL migration entry, full text in git history.

**Grooming log:** 2026-05-18 (stream-format seed from retired `docs/HANDOFF.md`) · 2026-06-02 (story-map migration; 9 open items preserved, 3 closed items retired) · 2026-06-03 (added "Safety & code health" theme; preserved #10 path-traversal security, #11 dead code from stale branches; added #12 ruff drift). Next quarterly: 2026-07-01.
