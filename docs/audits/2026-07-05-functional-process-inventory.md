# Functional Audit — Process Inventory vs Hypothesis (Phase 3)

**Date:** 2026-07-05 · **Branch:** `docs/2026-07-05-functional-audit` · **HEAD:** `fb9b2dd` (+2 audit commits)
**Inputs:** `2026-07-05-functional-telemetry.md` (Phase 1), `2026-07-05-functional-scenarios.md` (Phase 2). Status words per the audit vocabulary; each card triangulates Capability (code) / Intent (docs) / Use (telemetry).

---

## Deal loop

### D1 — Opportunity intake
```
Trigger:            AM adds Rob to a Salesforce Opportunity Team (manual awareness today)
Steps (as-built):   manual `com new CLIENT -p PRODUCT` → local folder scaffold + deck-template copy
                    + _knowledge/{project-info.yaml,notes.md} → optional xlsm col-M folder-link write-back
Artifacts:          {Client}_{Product}/ folder, project-info.yaml, renamed deck copy, xlsm col M
Capability:         opportunity/cli.py:41-99, folder_manager.py:22-79, excel_manager.py:55-123
Intent:             VISION "opportunity preparation"; ARCHITECTURE CLI table (`com new/list/show`)
Use:                ZERO — 0/29 real 10_Projects folders have _knowledge/; test_projects/ exists nowhere;
                    no JOURNAL use entry
Status:             EXISTS-UNTESTED (and misconfigured: PROJECTS_ROOT unset → defaults to CWD-relative
                    ./test_projects, opportunity/config.py:63 — would not touch real 10_Projects)
Break/limit points: Salesforce trigger MISSING (no SF code); SharePoint team leg MISSING (msal extra
                    declared, pyproject.toml:42, nothing imports it); xlsm row must pre-exist (no row creation)
```

### D2 — Ad-hoc Q&A / discovery
```
Trigger:            technical question from AM/client (integration, architecture, SaaS/Azure)
Steps (as-built):   `corp retrieve "query"` / `corp query` / `corp prep <client>` / `corp chat`
                    → FTS5 BM25 over index.db notes → trust-weighted ranking → optional LLM brief
Artifacts:          console results with [Title] citations; prep_<client>_<ts>.md under _corp_prep/
Capability:         retrieve/engine.py:105-310, retrieve/prep.py, query_engine.py, chat.py
Intent:             VISION "cross-project search"; ARCHITECTURE Data Flow step 9
Use:                REAL in March (JOURNAL 2026-03-26 "JLR real usage test (useful output)";
                    retrieve smoke queries during pilots). Nothing since; index frozen 2026-03-28
Status:             DORMANT
Break/limit points: index 3+ months stale vs MyWork reality; answers capped at 30 notes; no length/form
                    knobs beyond the prep prompt; 258/488 notes have empty client field; mojibake client
                    duplicates (Würth/WÃ¼rth, Żabka/Å»abka) split client-scoped hits
```

### D3 — RFP / questionnaires (priority process)
```
Trigger:            client RFP/RFI/security questionnaire arrives (Excel, sometimes Word)
Steps (as-built):   TWO disjoint stacks — A: `corp rfp answer "<q>"` console one-off;
                    B: standalone rfp_excel_agent.py / rfp_answer_word.py (not CLI-registered)
                    → parse doc → single-product flag → index.db retrieval → LLM per question →
                    write answers into document copy
Artifacts:          answered .xlsx/.docx copy (target data/output/ — absent); console answers
Capability:         cli/rfp.py:14; rfp/rfp_excel_agent.py, rfp_answer_word.py, llm_router.py,
                    vault_adapter.py; retrieve/rfp.py
Intent:             ADR-22 federation (rfp_entries + corp rfp-index) — "ratified, not built" (BACKLOG:20);
                    9-stage target process (architect hypothesis)
Use:                ZERO real RFPs — data/output/ and data/kb/ absent; no JOURNAL entry; RFP KB frozen
                    2026-03-15; ~3 RFPs/month handled manually meanwhile
Status:             EXISTS-UNTESTED (stacks) + PHANTOM (ADR-22 federation, forbidden_claims gating,
                    review capture, style store)
Break/limit points: target stages 2,3,4,6 and style-store half of 8 MISSING (scenarios §1.2); RFP KB
                    (1,329 files) unreachable by both stacks; product profiles dead at answer time;
                    platform_matrix.json absent → --solution choices empty; security-questionnaire
                    variant has no dedicated path (registry routes them to 80_Compliance as W1 capture)
```

### D4 — Demo / deck production
```
Trigger:            demo/presentation needed for a deal
Steps (as-built):   `com prep-deck` = shutil.copy2 of ONE static corporate template renamed into the
                    project folder (opportunity/cli.py:160-201). No content, no KB grounding
Artifacts:          renamed template copy; (real decks are hand-built in MyWork — newest 2026-07-03)
Capability:         opportunity/cli.py:160-201; template_manager.py (registry of .pptx/.xlsx/.docx;
                    stale 30_Templates/90_System labels; no .potx; no KM_v2 registered)
Intent:             VISION "presentation / deck drafting" as pipeline outcome
Use:                ZERO through the system; heavy MANUAL deck work in 10_Projects (July 2026 files)
Status:             MISSING (as hypothesized KB-grounded production; the stub is EXISTS-UNTESTED)
Break/limit points: no assembly engine, no brand-template management, no KB→slide path; the deck the
                    operator actually ships is produced entirely outside the system
```

### D5 — Close-out (Win/Loss → archive everywhere)
```
Trigger:            hypothesis: xlsm Stage → Closed Won/Lost. As-built: typing "archive <project> won"
                    into `corp chat`
Steps (as-built):   intent_router keyword match → workflows.yaml archive_project → cpe render →
                    shutil.move folder → archive_root/{year}/ → stamp vault project-info.yaml
Artifacts:          moved folder under 90_Archive/{year}/, status=archived metadata
Capability:         actions/archive_actions.py:20-128; workflows.yaml:115-134; intent_router.py:52-62
Intent:             hypothesis D5; ARCHITECTURE actions list
Use:                ZERO — MyWork/90_Archive has 0 files ever; no JOURNAL entry
Status:             EXISTS-UNTESTED (mechanism); MISSING (status-driven trigger; xlsm/SF/SharePoint
                    reconciliation)
Break/limit points: Stage col H read for display only, nothing consumes it; archiving a OneDrive-synced
                    copy is blocked by design (fail-closed guard) so "archive everywhere" cannot include
                    the SharePoint leg; `com` itself has no archive verb
```

---

## Knowledge loop

### W1 — Capture (files land → classified → renamed → routed)
```
Trigger:            file saved into MyWork/00_Inbox
Steps (as-built):   batch `corp ingest` (no rename) or interactive `corp ingest-inbox` (rename+review)
                    → ContentRegistry match → ops.db record → move to zone
Artifacts:          routed files in 10/20/30/80 zones; ops.db assets/ingest_events rows
Capability:         ingest/router.py, inbox.py, registry.py, renamer.py, dedup.py (interactive-only)
Intent:             ARCHITECTURE Data Flow steps 1-5; naming convention ADR-14
Use:                REAL Mar 14-27 (2,726 events, ~22 interactive routes); inbox inflow stopped
                    2026-04-10; 75 files waiting now
Status:             DORMANT
Break/limit points: 3 phantom 40_Media destinations in content_registry.yaml; batch lane skips rename
                    and dedup; MinHash fails open (content_signatures=0 rows ever); learning surfaces
                    (routing_feedback rows=0 forever) never fed
```

### W2 — Extract & organize (docs → facts → vault notes → FTS)
```
Trigger:            routed source files (or bulk CKE output)
Steps (as-built):   CKE subprocess (tiered LOCAL/TEXT_AI/MULTIMODAL, Gemini) → staged notes →
                    ingest-extractions → vault 01_Knowledge (hardcoded) → MANUAL corp index rebuild
Artifacts:          .md notes with rich provenance frontmatter; index.db notes/notes_fts; _outputs/ JSON
Capability:         extractor/* (engine ALIVE per output/test through 2026-06-16), overnight/*,
                    ingest/extractions.py, vault_writer.py, index_builder.py
Intent:             VISION core purpose; ARCHITECTURE Data Flow 6-9; Council #20 vault rebuild
Use:                HEAVY Mar 12-28 (601 overnight files, 2,673 notes ingested, 488 indexed, $0.24);
                    ZERO since; sandbox e2e 5/5 PASS 2026-07-05 (fixture mode)
Status:             DORMANT (engine proven ALIVE-in-sandbox; facts pipeline BROKEN-by-absence: facts=0,
                    extractions table never written)
Break/limit points: no auto index rebuild after ingest; March folder restructure orphaned source links
                    (trust_level=deprecated, rebuild_status=source_inaccessible in sampled notes);
                    routing_map.yaml + 02_sources/04_evergreen zones are dead config (no runtime reader);
                    4 overnight runs stuck 'running' forever (no janitor)
```

### W3 — Personal enablement (learning new products)
```
Trigger:            training sessions, product releases (e.g. Platform Training Warsaw, July 2026)
Steps (as-built):   MANUAL filing into 30_Reference/Training (newest file 2026-07-05); system-side:
                    training doc_type notes exist (23+2) from March extractions
Artifacts:          30_Reference/Training tree; training-tagged vault notes
Capability:         no dedicated process; W1/W2 would serve it if alive
Intent:             hypothesis W3 ("correlated with deck material")
Use:                ACTIVE manually; ZERO through the system since March
Status:             ALIVE as manual behavior; system support DORMANT
Break/limit points: newest learning material never extracted → KB lags Rob's actual knowledge by 3+ months
```

### W4 — Publish to team (curated knowledge → team SharePoint)
```
Trigger:            hypothesis: curated content worth sharing
Steps (as-built):   NONE. No Graph/SharePoint write code; the only SharePoint posture is fail-closed
                    guards REFUSING writes to the synced tree
Artifacts:          none
Capability:         none (pyproject msal extra unused)
Intent:             hypothesis W4 only — no ADR/VISION commitment found
Use:                n/a
Status:             MISSING
Break/limit points: entire process absent; guards make the naive implementation (write into synced
                    folder) intentionally impossible
```

### W5 — Company map (industry × product-line taxonomy)
```
Trigger:            continuous curation
Steps (as-built):   schema/taxonomy.yaml + products.py aliases + normalize.py; unknown terms preserved
                    into taxonomy_review.yaml for review; naming-stats MISC-rate warning
Artifacts:          taxonomy YAMLs, product alias map, taxonomy_review.yaml queue
Capability:         schema/normalize.py, schema/products.py, extractor/taxonomy_prompt.py
Intent:             VISION "shared schema/taxonomy"; JOURNAL 2026-03-28 "Ontology Q4 (canonical product
                    map)" — planned, not evidenced done
Use:                curated during March (tag additions JOURNAL 2026-03-26); frozen since; coverage map
                    shows uncanonicalized product terms leaking into notes.products
Status:             DORMANT
Break/limit points: notes.products not normalized to canonical families (Phase-1 §1.4 long tail);
                    review queue has no evidence of triage since March
```

---

## Cross-cutting

### X1 — Continuous backup to Google Drive
```
Trigger:            hypothesis: continuous
Steps (as-built):   NONE. No Google Drive/rclone/backup code or config anywhere in repo
Artifacts:          none
Capability:         none. Partial accidental mitigation: corp-monorepo itself pushed to private GitHub
                    (rdwornik/corp-monorepo, JOURNAL 2026-06-06)
Intent:             hypothesis X1 ("believed entirely missing") — confirmed
Use:                n/a
Status:             MISSING (confirmed)
Break/limit points: vault is a git repo with NO remote (last commit 2026-03-26); MyWork (10.9 GB),
                    corp_data/rfp_kb, and all 3 DBs have no off-machine copy (see Phase 4)
```

---

## Discovered processes (in code/telemetry, absent from hypothesis)

### N1 — MyWork hygiene / reshape (cleanup)
```
Trigger:            operator-invoked (`corp cleanup-scan`, `corp apply-moves`, `corp audit`, dedup-report)
Steps (as-built):   scan MyWork → classify misplaced files → propose moves.yaml → guarded execute
Artifacts:          reshape_plan.md (554 KB, 2026-03-13), moves plans; OneDrive-overlap report capability
Capability:         cleanup/{scanner,classifier,proposer,executor,disk}.py with the strongest safety
                    engineering in the repo (MoveEntry schema, _guard_onedrive, path-traversal checks)
Use:                March reshape only (overnight 'full-reshape' dry-run 2026-03-12; reshape_plan.md)
Status:             DORMANT — judged a real (supporting) business process: it exists because capture
                    quality depends on tree hygiene
```

### N2 — Cross-project analytics
```
Trigger:            operator-invoked `corp analytics report/products/timeline/clients/overlap/...`
Steps (as-built):   SQL over index.db (6/10 benchmark queries at build time, JOURNAL 2026-03-28)
Status:             DORMANT (built+demoed 2026-03-28, index frozen since) — plumbing on top of W2;
                    only useful if the index lives
```

### N3 — Vault/system integrity & freshness
```
Trigger:            operator-invoked (`corp doctor`, `corp freshness`, `corp vault validate`)
Steps (as-built):   integrity.check_all cross-system checks; freshness_scanner stale/orphan detection
                    (source_hash/mtime vs vault notes)
Status:             EXISTS-UNTESTED as routine (no scheduled use evidence); the very drift it detects
                    (deprecated/source_inaccessible notes) is present and unremediated
```

### N4 — Task management via vault (`corp task add/list/done`)
```
Status:             EXISTS-UNTESTED — no telemetry or JOURNAL evidence of use; judged plumbing/experiment,
                    not a live business process
```

### N5 — Nightly documentation-conformance loop (governance)
```
Trigger:            scheduled cloud routine (01:15Z) + GitHub Action triage
Steps (as-built):   3 verifiers → skeptic → digest → auto-merge/issue (conformance-corp.js,
                    nightly-conformance-triage.yml)
Use:                digests landing through 2026-06-27 (#34) — the ONLY automated loop that runs
Status:             ALIVE — but it is meta-governance (docs conformance), not a pre-sales business process
```

---

## Discrepancy list

**(a) Hypothesis rows with no code at all**
1. X1 backup — nothing (vault git has no remote).
2. W4 publish-to-team — nothing; guards actively prevent the naive version.
3. D1/D5 Salesforce leg — nothing beyond a YAML comment.
4. D1/D5 SharePoint leg — nothing beyond an unused `msal` optional dep and a printed reminder.
5. D4 KB-grounded deck assembly — nothing (stub copy only).

**(b) Code with no hypothesis row**
1. cleanup/ hygiene subsystem (N1) — substantial, safety-hardened, dormant.
2. analytics CLI (N2), integrity/doctor/freshness (N3), task manager (N4), chat/intent/workflow orchestration layer (the `corp chat` surface wrapping actions).
3. sandbox/test-pipeline harness (proven alive; the audit used it).
4. anonymization middleware (built for D3 but reachable only via the unused Excel agent flag).
5. Nightly conformance loop (N5) — alive governance automation.

**(c) Docs/config claim more than code delivers**
1. **ADR-22 federation** — "ratified"; `rfp_entries`/`corp rfp-index` never built; RFP KB unreachable (BACKLOG.md:20 admits it; CLAUDE.md/ARCHITECTURE still list ADR-22 among governing ADRs without the caveat).
2. **CLAUDE.md §5 / ADR-27 / ARCHITECTURE invariant #1** name `02_sources/` — a zone that exists only in dead config (`routing_map.yaml`) and legacy enums; real writer targets `01_Knowledge`.
3. **ARCHITECTURE Data Flow** draws steps 1→9 as one chain; in reality step 9 (index) requires a separate manual command, step 3's registry contains phantom destinations, and step 6's CKE handoff is an external-binary subprocess.
4. **routing_map.yaml** (MyWork/.corp) — entire file is authoritative-looking dead config: reader has no runtime caller, all targets phantom.
5. **template_manager docstrings** — `30_Templates`/`90_System` labels match nothing on disk.
6. **`com` CLI presence in ARCHITECTURE CLI reference** implies a working opportunity lifecycle; PROJECTS_ROOT default points it at `./test_projects`.
7. **config/rfp/product_profiles + overrides.yaml** read like runtime guardrails; they gate nothing at answer time.

---

*End of Phase 3.*
