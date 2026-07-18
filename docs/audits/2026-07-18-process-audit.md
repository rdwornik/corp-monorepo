# Process Audit — Use-Case Dynamic Audit of corp-monorepo

**Date:** 2026-07-17 → 18 (unattended night batch) · **Branch:** `docs/2026-07-17-night-process-audit`
**Mode:** auto / UNATTENDED — frozen probes, fixed nothing, asked nothing.
**Question answered:** *"the user wakes up and asks X — what actually happens?"* — witnessed through the LIVE CLI, verbatim, per use case.

> This is a **process** test, not a quality test. Verdicts describe how the modules run and connect, not whether LLM output is good.

---

## Method & safety (how this was run)

**Sandbox isolation (the safety gate).** Every real asset path resolves from env vars (`ENV > paths.toml > default`, per `schema/config.py` + `pipeline_config.py`). The audit set the anchor vars and let all other paths derive:

```
VAULT_PATH, MYWORK_ROOT (+ MYWORK_PATH alias), APP_DATA_PATH (-> all 3 DBs), RFP_KB_PATH  ->  C:\...\Temp\corp_audit_sb\...
```

A GO/NO-GO gate (`sb_init.py`) built the tree + DBs via the repo's own `SandboxManager` and then asserted **every** env-resolved path (vault, mywork, inbox, ops/index/state DBs, and the `schema.config` accessors) lives under the sandbox root. Result: `ISOLATION_VERIFIED_OK`. Nothing live ran before that passed.

**Tamper baseline.** Real vault (886 files / 42,584,635 bytes), real MyWork, and all 3 real DBs (SHA-256) were snapshotted before any live command. Re-checked after each UC.

**Orchestration.** Opus orchestrator drove every probe **serially and directly** (not fanned out to per-UC workers): the deliverable is verbatim evidence (subagent reports are summarized), the sandbox is shared mutable state (parallel workers would collide), and the chain (UC1→UC2→UC3) is inherently sequential. Read-only recon (CLI surface, isolation mechanism, fixtures) *was* fanned out to 3 subagents up front.

**Real LLM calls** were allowed on live paths and are cost-logged below via the `schema.model_pricing` registry (dogfooded).

---

## LLM cost log (per call, live paths only)

| # | UC | Command / path | Model (actual) | Tokens | Cost (source) | Registry rate ($/1M in/out) |
|---|----|----|----|----|----|----|
| 1 | UC1 | `corp ingest` → CKE `process-manifest` (text tier) | **claude-sonnet-4-6** | 4136 | **$0.0377** (note frontmatter) / $0.0010 (CKE summary — disagree ~37×) | 3.00 / 15.00 |
| 2 | UC3a | `corp rfp answer` (content Q) | gemini-3-flash-preview | not surfaced | $0.0027 (CLI-reported) | 0.50 / 3.00 |
| 3 | UC3b | `corp rfp answer` (metadata Q) | gemini-3-flash-preview | not surfaced | $0.0022 (CLI-reported) | 0.50 / 3.00 |
| 4 | UC4 | `corp prep Lenzing` (brief) | gemini-3-flash-preview | not surfaced | $0.0024 (CLI-reported) | 0.50 / 3.00 |
| 5 | UC5b | `cke process` (synthesis stage) | gemini-3-flash-preview | not surfaced | **not surfaced** (no cost line) | 0.50 / 3.00 |
| 6 | UC8 | `corp classify` ×3 files | gemini-3-flash-preview | not surfaced | **not surfaced** (budget $0.50 printed, spend not) | 0.50 / 3.00 |

**Surfaced total: ~$0.045** across the run (UC1 $0.0377 + UC3a $0.0027 + UC3b $0.0022 + UC4 $0.0024). UC5b synthesis and UC8 ×3 classify calls were live but **printed no cost** — a real observability gap (below). No throttling; every call logged as witnessed.

*Registry dogfood:* `get_price("claude-sonnet-4-6")` = {3.00, 15.00}; `get_price("gemini-3-flash-preview")` = {0.50, 3.00} (per 1M). Because the CLIs surface a `$` but **not** token counts, the registry cost cannot be independently recomputed for any call — the registry can price a model but the tools don't emit the tokens to price.

---

## UC1 — Capture · "Ingest this source into my vault." · Verdict: **WORKS** (with a hard provisioning prerequisite)

**1. Setup.** Sandbox inbox seeded with two fixtures: `Lenzing Planning - Discovery Call 2026-07-15.txt` (2127 b; filename matches registry client key `Lenzing`) and `Meridian Foods - Discovery Call 2026-07-15.txt` (2635 b; no registry match). Both synthetic; the Lenzing one carries the unique chain token **`Project Halcyon`** / "47,000 order-lines/hour".

**2–3. Commands & Output (verbatim, trimmed).**

- `is_available()` gate, both branches:
  - BRANCH A (cke on PATH, as live): `is_available() = (True, '')`
  - BRANCH B (no cke on PATH, bogus CKE_PATH): `is_available() = (False, 'cke not found on PATH and no venv at C:\__no_such_cke_dir__')`
- `corp ingest --dry-run` (first attempt) → **CRASH**: `FileNotFoundError: ...\mywork\.corp\content_registry.yaml` (uncaught, even in dry-run). Registry seeded from repo `config/content_registry.yaml`; retried:
- `corp ingest` (real):
```
Moved: Lenzing... -> 10_Projects/Lenzing_Planning (routed, conf=0.80)
extract_sync: cke.EXE process-manifest ...\appdata\staging\ingest\lenzing-...\manifest.json --max-rpm=80 --resume
extract_sync summary: {'done': 1, 'error': 0, 'skipped': 0, 'total': 1, 'cost': 0.001, 'tiers': {1: 0, 2: 1, 3: 0}}
Moved package: lenzing-... (6 files)
Moved: Meridian... -> 00_Inbox/_Unmatched (quarantined, conf=0.00)
Estimated API cost: $0.0010
| Lenzing...  | routed      | client | 80% | 10_Projects/Lenzing_Planning | Y |
| Meridian... | quarantined | none   |  -  | 00_Inbox/_Unmatched          | - |
```

**4. Witnessed artifacts.**
- Vault note landed at `vault/01_Knowledge/lenzing-.../extract/2026-07-17_lenzing_planning_discovery_call_20260715_9b95.md` (6652 b) — **full frontmatter**: title, domains, topics(8), products(4), people, `model: claude-sonnet-4-6`, `tokens_used: 4136`, `quality_score: 86`, `extraction_cost_usd: 0.0377`, 18 `key_facts` (incl. Project Halcyon / 47,000 lines / synthetic-fixture flag), `entities_mentioned`, `source_hash`, a populated `discovery_overlay`, tags. Package also has `index.md`, `synthesis.md`, `extract.json`, source copy (6 files).
- ops.db: `assets` id1 Lenzing `status=extracted` routed_to `10_Projects/Lenzing_Planning/...`; id2 Meridian `status=quarantined`. `ingest_events`: routed(client,0.8)+extracted; quarantined(none,0.0). **`files` and `extractions` tables EMPTY** (no content-hash identity row, no model/cost history in DB).
- Filesystem: routed source in `10_Projects/Lenzing_Planning/`; quarantined source in `00_Inbox/_Unmatched/`.

**5. Verdict: WORKS** — with the OPEN gate, a routed file produces a deep, well-formed knowledge note end-to-end; an unmatched file quarantines with no note (correct). BUT the path has a **hard prerequisite** that crashes a fresh environment.

**6. Missing pieces / findings.**
- **F1 (blocker for fresh env):** `corp ingest` (even `--dry-run`) raises an **uncaught `FileNotFoundError`** if `<mywork>/.corp/content_registry.yaml` is absent (`ops/registry.py:59`, no try/except, no fallback to the shipped `config/content_registry.yaml`). Neither `SandboxManager` nor first-run setup provisions it.
- **F2:** Cost reporting disagreement — CKE pipeline summary `$0.0010` vs note frontmatter `$0.0377` (~37×). The summary regex-scrape (`_parse_summary`) undercounts the real per-call cost.
- **F3:** ops.db `files` + `extractions` tables not populated by the ingest→extract path → no content-hash identity, no per-model extraction/cost history in the DB (only in frontmatter).
- **F4 (feeds UC2/UC7):** Note lands in `01_Knowledge/…/extract/`. Freshness scans `02_sources/`+`04_evergreen/` (different dirs). Whether the index sees `01_Knowledge` is tested in UC2.
- **F5:** Actual extraction model was `claude-sonnet-4-6` (CKE `text_default` tier), not the corp-default `gemini-3-flash-preview` — ingest's `extract_sync` passes no `--model`, so CKE's own tier router chooses.

**7. Teardown check.** Integrity checkpoint #1 after UC1: all 3 real DB hashes unchanged, real vault unchanged (886/42,584,635), git clean. Sandbox-only confirmed.

---

## UC2 — Find · "Find X in my knowledge." · Verdict: **PARTIAL** (findable by metadata/title only; no body search; facts pipeline absent)

**1. Setup.** Sandbox vault holds the one UC1 knowledge package. Search target = unique token **`Halcyon`** (present only in the new note).

**2–3. Commands & Output (verbatim, trimmed).**
```
corp index rebuild  -> "Indexed 2 CKE notes from vault" -> "1 projects, 0 facts, 2 notes in 0.1s"
corp index stats    -> Projects 1 | Facts 0 | Notes 2
corp retrieve "Halcyon"                 -> results=2 sufficient=False  (both package notes)
corp query    "Halcyon"                 -> 2 results (note titles, labelled "facts")
corp retrieve "peak throughput forecast accuracy" --format json -> total_found: 0, "No results found"
corp retrieve "WMS"          -> results=2   (metadata/topic term)
corp retrieve "stranded stock" -> results=0 (body-only phrase)
corp retrieve "47000"        -> results=0   (body-only number)
```

**4. Witnessed artifacts.** index.db actual schema = `meta, notes, notes_fts(+internals), projects`. **No `facts` / `facts_fts` table exists.** `notes` has 2 rows from the single source: (a) the package `index.md` (client='', type='', rfp_visible=0), (b) the real extract note (type='document', rfp_visible=1). `client=''` on both. `projects` = 1 row.

**5. Verdict: PARTIAL.** The new note **is** findable end-to-end — `corp index rebuild` scans `01_Knowledge/` and `Halcyon` retrieves it. But retrieval matches **only note metadata (title/topics/products)**, not body content, so content-phrased queries (`peak throughput…`, `stranded stock`, `47000`) return 0. The unique-token test passed only because the token is in the title.

**6. Missing pieces / findings.**
- **F6 (retrieval scope):** `corp retrieve`/`corp query` FTS is over `notes_fts` metadata columns only — **no full-text over note body**. Body facts are unsearchable. Directly caps UC3 grounding.
- **F7 (facts pipeline absent):** rebuilt index.db has **no `facts` table**; the note's 18 `key_facts` never become rows. `index stats` "Facts 0" and `corp query` ("facts") hits are actually `notes_fts` matches. (Corroborates ground-truth "facts pipeline 0 rows".)
- **F8 (note inflation):** one source → 2 indexed notes; the package `index.md` is indexed as a low-value rfp_visible=0 note.
- **F9 (client not propagated):** routing key `Lenzing` → note/index `client=''`; analytics-by-client (UC4) will see no client.
- **F10 (retrieval "sufficient" flag):** even the on-topic note yields `sufficient=False` — the signal RFP (UC3) reads to decide whether to answer.

**7. Teardown check.** Read-only + sandbox index writes; real assets rechecked clean at checkpoint #2 (below).

---

## UC3 — RFP answer · "Draft an RFP answer citing my knowledge." · Verdict: **WORKS** (CLI lane grounds from vault — contradicts the "KB-absent → fails" expectation)

**1. Setup.** Same sandbox vault (1 knowledge package, indexed). `data/kb/canonical/RFP_Database_UNIFIED_CANONICAL.json` absent (confirmed no producer).

**2–3. Commands & Output (verbatim, trimmed).**
```
corp rfp answer "How does the solution address peak order-line throughput during holiday peak?"
  -> retrieve results=2 sufficient=False
  -> POST .../gemini-3-flash-preview:generateContent 200 OK
  -> Confidence: MEDIUM (2 sources) | Cost: $0.0027
  -> cited draft: "…targeted to support throughput exceeding 75,000 order-lines per hour
     [Blue Yonder Discovery Call — … (Project Halcyon)] … autoscaling … 15-20 percentage points …"
corp rfp answer "What WMS and Demand Planning capabilities were positioned?"
  -> Confidence: MEDIUM (2 sources) | Cost: $0.0022 | cited draft w/ Key Capabilities + Gaps
```

**4. Witnessed artifacts.** No files written (stdout draft only). Two live Gemini calls (`gemini-3-flash-preview`). Both answers carried inline citations to the two indexed note titles and correctly grounded the 47,000→75,000 throughput, autoscaling, and 15-20pt forecast-accuracy facts from the UC1 note.

**5. Verdict: WORKS.** The user-facing RFP lane (`corp rfp answer` → `retrieve.rfp.answer_rfp`) **does not depend on `data/kb`** — it retrieves from the FTS index + vault and drafts a cited answer via Gemini. At sandbox scale it produced a usable, grounded, cited draft. **This overturns the pre-audit expectation** that UC3 breaks on the orphan KB.

**6. Missing pieces / findings.**
- **F11 (lane disambiguation):** two distinct RFP lanes exist. (a) **`corp rfp answer`** = index+vault-grounded, works. (b) The **Word/Excel RFP agent** (`rfp/llm_router.py` + `rfp_answer_word.py`) is the one that reads the orphan `data/kb/.../RFP_Database_UNIFIED_CANONICAL.json` (no producer; guards on `.exists()` and silently falls back to empty KB). The `data/kb` gap is real but sits on a lane that is **not** the CLI entry point. Not driven here (no simple CLI entry; Excel/Word file in/out).
- **F12 (grounding scale risk):** retrieval reported `sufficient=False` yet drafted anyway. With only 2 notes, weak/metadata matching still surfaced the right note; in a real 800+ note vault the **metadata-only retrieval (F6)** would frequently miss the relevant note, so grounding quality is a scale risk, not proven at scale here.
- **F13 (cost observability):** the RFP CLI prints a `$` cost but **no token counts** → the `model_pricing` registry cannot independently recompute the cost.

**7. Teardown check.** Read-only (LLM calls) + no sandbox writes. Real assets rechecked at checkpoint #2 (below).

---

## UC4 — Project view · "Show my project status / analytics / briefs." · Verdict: **PARTIAL** (surfaces render; the data feeding them is unwired)

**1. Setup.** Sandbox: 1 project (`Lenzing_Planning`), 1 indexed knowledge package, 0 facts. **Isolation note:** the AppConfig gap (F18) was detected *during* this UC — see safety disclosure — and closed before UC5+.

**2–3. Commands & Output (verbatim, trimmed).**
```
corp project list    -> lenzing_planning | Client Lenzing | Status unknown | Vault - | OneDrive Y | Facts -
corp analytics report-> "1 projects, 0 facts indexed | Avg facts/project: 0.0"; dashboard -> vault/00_dashboards/analytics.md
corp analytics recent-> "No dated notes found in index."
cpe show <proj>      -> "No manifest found. Run cpe scan ... first."
corp project show lenzing_planning -> "No project-info.yaml found in vault"; OneDrive: <REAL MyWork path>  (F18)
corp prep Lenzing    -> retrieve client=Lenzing results=0 -> broader results=0 -> gemini 200 -> "Sources: 0 notes | Cost $0.0024"
                        -> brief saved to <sandbox>/mywork/10_Projects/Lenzing_Planning/_corp_prep/prep_Lenzing_*.md
```

**4. Witnessed artifacts.** `vault/00_dashboards/analytics.md` (frontmatter + "Generated from 1 projects, 0 facts"). Brief `.md` written to sandbox project `_corp_prep/`. The `facts_count` consumer sites all render 0/dash.

**5. Verdict: PARTIAL.** Every surface renders without crashing, but on **empty/unwired data**: 0 facts (despite 18 `key_facts`), no vault↔project link, no dated notes, no cpe manifest, brief from 0 sources.

**6. Missing pieces / findings.**
- **F14 (facts_count = 0 across all consumer sites):** analytics "0 facts indexed", project `Facts=-`, brief would show "Facts Extracted: 0" — the 31 `facts_count` consumers render empty because the facts table is never populated (F7).
- **F15:** `analytics recent` = "No dated notes found" though the note has `date: 2026-07-17` — note dates not wired into the recent-notes analytic.
- **F16 (project↔vault link broken):** ingest produces a `01_Knowledge` package but **no `project-info.yaml`**, so `project show` finds nothing in vault and `project list` shows `Vault=-`. The project and its own knowledge note are not linked.
- **F17 (cpe is a disjoint pipeline):** `cpe show/scan/render` operate on their own `_knowledge/manifest.yaml`; corp-ingest output is invisible to cpe. Two non-integrated project pipelines.
- **F18 (config-resolution inconsistency + isolation caveat):** `AppConfig` resolves `projects_root`/`templates_root`/`archive_root` to the **real home-relative MyWork**, ignoring `MYWORK_ROOT` (unlike `PipelineConfig`, which derives them from it). `project show` → `project_resolver` therefore **read-enumerated the real MyWork** before the sandbox env was hardened. **No writes occurred (integrity verified);** fixed by setting `PROJECTS_ROOT`/`TEMPLATES_ROOT`/`ARCHIVE_ROOT` explicitly. Portability bug for any non-default MyWork machine.
- **F19:** `corp prep <client>` retrieved **0 sources** for `Lenzing` — the note's `client=''` (F9) means the project's own rich note is invisible to its brief; the LLM then drafts from nothing.

**7. Teardown check.** Integrity checkpoint #2 (post-UC3/UC4): all real DBs + vault + mywork unchanged, git clean. Sandbox-only confirmed (real-MyWork read-enumeration disclosed; no writes).

---

## UC5 — Knowledge extractor direct · CKE subprocess contract recon · Verdict: **WORKS** (with cross-entry-point inconsistencies)

**1. Setup.** Drove `cke` directly against a sandbox source (`Meridian…txt`, 2635 b). `is_available()` = True (UC1a).

**2–3. Commands & Output (verbatim, trimmed).**
- `cke scan <file> -o uc5_scan.json` → JSON contract:
```
{ "scan_date", "total_files": 1, "results": [ { "path", "filename", "extension", "size_bytes",
  "file_hash": "sha256:…", "tier": 1, "metadata": {"text_chars","text_preview","line_count"}, "error": null } ] }
```
- `cke process <file> --output uc5_out`:
```
Tier 1: small text file (2633 chars)
[INFO] Local extraction ... (2633 chars, no API call)...
[WARNING] Schema contract warnings: type 'note' (allowed: …'notes'/'document'…); quality 'local' (allowed: full/partial/fragment)
[WARNING] Validation failed: ('type',) …; ('quality',) …
[INFO] synthesize: Wrote 2026-07-17_meridian_..._81bf.md
POST .../gemini-3-flash-preview:generateContent 200 OK   (synthesis stage)
Done!  Package: <sandbox>/appdata/uc5_out/Meridian Foods - Discovery Call 2026-07-15
```

**4. Witnessed artifacts.** Package under `appdata/uc5_out/…` (source copy + extract note + synthesis). No cost line printed.

**5. Verdict: WORKS.** Both CKE entry points function; the subprocess contract corp depends on (`process-manifest` → regex-scraped summary) was already witnessed live in UC1.

**6. Missing pieces / findings.**
- **F20:** `cke scan` JSON contract is clean/stable (keys above) — this is the one machine-readable CKE output; corp parses `results[]` in `scan_local`.
- **F21 (inconsistent tiering):** direct `cke process` used **Tier-1 LOCAL (no API)** for the small text file; the ingest `process-manifest` path escalated an equivalent file to **Tier-2 text-AI (claude-sonnet-4-6)**. Same input class, different model/cost depending on entry point.
- **F22 (schema contract drift):** the Tier-1 local extractor emits `type='note'` and `quality='local'` — **both invalid** against the schema enums → validation warnings (non-fatal, note still written). Local extractor and schema disagree.
- **F23 (entry-point cost observability):** `cke process` prints **no** "Estimated API cost"/"Tiers:" block (only `process-manifest` does), and neither surfaces token counts. corp's `_parse_summary` only works against `process-manifest`.
- **F24 (fragile subprocess contract — corroborates ground-truth):** corp reads `process-manifest` results by regex-scraping literal stdout lines ("Done: N", "Estimated API cost: $X"), logic duplicated in `overnight/cke_client.py` and `project/cke_invoker.py`; no test exercises it.

**7. Teardown check.** All writes under `appdata/uc5_out` (sandbox). Real assets unchanged (checkpoint #3 below).

---

## UC6 — Synthesize / deck · "Show my project synthesis / a deck." · Verdict: **PARTIAL / NOT-WIRED** (synthesis works internally; no user command; deck lane is real-data + template-copy only)

**1. Setup.** Synthesis output from the UC1/UC5 packages; deck lane probed read-only (`com`).

**2–3. Commands & Output (verbatim, trimmed).**
- `synthesis.md` (produced by the CKE synthesize stage, LLM-generated): sections **Executive Summary / Key Takeaways / Relationships / Action Items / Open Questions**, correctly grounded ("increase peak throughput from 47,000 to over 75,000 order-lines per hour…", "15-20 percentage point… forecast accuracy").
- `com list` → **53 REAL opportunities** printed from the real `project_codes.xlsx` (Lenzing AG, Alfa Laval, Almarai, …).
- `com prep-deck --help` → "Copy a new presentation template for an existing opportunity" (`--topic` required).

**4. Witnessed artifacts.** `synthesis.md` in each CKE package. No deck created (see verdict).

**5. Verdict: PARTIAL / NOT-WIRED.** Synthesis **works** but only as an internal CKE stage — there is **no `corp synthesize` user command**. The deck lane (`com`) is a **template copy**, not content generation, and it is **not sandboxed** — so it was not driven to a write.

**6. Missing pieces / findings.**
- **F25:** synthesize is internal-only (`extractor/synthesize.build_package`); produces a good `synthesis.md`, but no user-facing command surfaces it and it never reaches the vault as a first-class note.
- **F26 (isolation gap — disclosed):** the `com` opportunity lane resolves `project_codes_excel` from **`PROJECT_CODES_EXCEL`** (set in a `.env` to a **real** path), which the sandbox anchor vars don't cover. `com list` **read 53 real opportunities** (read-only; no write). `com new`/`com prep-deck` call `wb.save(excel_path)` + create folders → would mutate **real** data, so **not run unattended**. Env subsequently hardened (`PROJECT_CODES_EXCEL` → sandbox).
- **F27 (deck = copy, not generation):** `com prep-deck`/`deck_actions.copy_deck_to_project` copy a `.pptx` template into the project; there is **no LLM slide/content generation**. A real deck would need (a) a populated template registry (`30_Templates`), (b) an opportunity row in `project_codes.xlsx`, and (c) content authoring that does not exist today. Demo-prep would have to supply the narrative; the deck lane only files a template.

**7. Teardown check.** Read-only probes; one disclosed real read (`com list`). No writes (integrity checkpoint #3 below).

---

## UC7 — Freshness · "Check my vault freshness." · Verdict: **WORKS** (regression handled; coverage gap on 01_Knowledge)

**1. Setup.** Baseline scan, then planted 4 notes in `02_sources/`: stale (wrong hash), orphaned (missing source), malformed-frontmatter, and a **deliberately unreadable** note (invalid UTF-8 bytes) — the regression case.

**2–3. Commands & Output (verbatim, trimmed).**
```
corp freshness  (baseline) -> "Scanned: 0 notes"  (the UC1 note in 01_Knowledge is NOT scanned)
corp freshness --verbose   (4 notes) ->
  Scanned: 4 | Fresh 0 | Stale 1 | Orphaned 1 | Review due 0 | No source 0 | Errors 2
  error    audit-broken.md     Cannot parse frontmatter
  orphaned audit-orphaned.md   Source file missing: …__no_such_source__.txt
  stale    audit-stale.md      Source file content changed (hash mismatch)
  error    audit-unreadable.md Cannot parse frontmatter      <-- invalid-UTF-8 note, NO crash
```

**4. Witnessed artifacts.** No writes (read-only scan). Two `vault_io: Failed to parse frontmatter, returning raw` warnings for the two error notes; scan completed and tallied `errors=2`.

**5. Verdict: WORKS.** Correct stale/orphaned/error categorization, and the **unreadable-note regression is handled** — the scan does not abort, it counts errors and continues (Arc-C #26 tolerant-None fix verified live).

**6. Missing pieces / findings.**
- **F28 (coverage gap):** freshness scans only `02_sources/` + `04_evergreen/`. The CKE knowledge notes produced by ingest land in **`01_Knowledge/`** and are therefore **never freshness-checked** — the primary knowledge corpus has no staleness tracking.
- **F29 (positive):** the deliberately-unreadable note (invalid UTF-8) and the malformed-frontmatter note were both absorbed as `error` without crashing the scan. Robust.

**7. Teardown check.** All writes under sandbox `02_sources/`. Integrity checkpoint #3 (below) clean.

---

## UC8 — Inbox cleanup / classify · "Clean up / classify my inbox." · Verdict: **WORKS** (records-driven; no cost surfaced)

**1. Setup.** 3 mixed fixtures quarantined + recorded via `corp ingest`: `Meridian…Discovery Call.txt` (meeting), `audit-competitor-brief.txt` (competitive), `audit-invoice-2026-Q3.txt` (finance/admin).

**2–3. Commands & Output (verbatim, trimmed).**
```
corp classify --dry-run   (Model: gemini-3-flash-preview | Budget: $0.50)
  3× POST .../gemini-3-flash-preview:generateContent 200 OK
  Meridian … Discovery Call.txt -> 10_Projects/Meridian_Foods  | meeting     | 85%
  audit-competitor-brief.txt    -> 30_Reference/Competition    | competitive | 85%
  audit-invoice-2026-Q3.txt     -> 70_Admin                    | template    | 80%
  Classified: 3 | staged: 3 | still unmatched: 0
```

**4. Witnessed artifacts.** Dry-run (no moves). 3 live Gemini calls (one per file). No cost line emitted.

**5. Verdict: WORKS.** The LLM classifier assigns destination + category + confidence + reasoning per quarantined file. (First attempt classified only 1/3 — see F30.)

**6. Missing pieces / findings.**
- **F30 (records-driven, not folder-driven):** `corp classify` classifies **ops.db-recorded quarantined assets**, not files sitting in `_Unmatched`. Files dropped straight into `_Unmatched` are invisible until they pass through `corp ingest` (which quarantines + records them). Non-obvious to a user.
- **F31 (cost observability):** `corp classify` prints Model + Budget but **no spend / token counts** → the run's real classify cost is unknowable from the CLI. (Same gap as F13/F23.)
- **F32 (positive):** per-file Gemini classification with destination/category/confidence/reasoning works cleanly across mixed content types.

**7. Teardown check.** Dry-run; sandbox ingest writes only. Integrity checkpoint #3 clean (all real DBs/vault/mywork unchanged, git clean).

---

## UC-X — Chain (UC1 → UC2 → UC3 on one fixture) · Result: **chain COMPLETES; expected UC3 break did NOT occur**

Driven as one flow on the Lenzing/Halcyon fixture:

`corp ingest` → vault note in `01_Knowledge` (F5 model = claude-sonnet-4-6) → `corp index rebuild` (2 notes, 0 facts) → `corp retrieve "Halcyon"` (2 hits, metadata match) → `corp rfp answer "…peak throughput…"` → **cited draft grounded in the ingested note** ($0.0027).

**First break point (verbatim):** there is **no hard break**. The pre-audit expectation — "UC-X breaks at UC3 on the missing `data/kb` producer" — **did not reproduce**: `corp rfp answer` grounds from the FTS index + vault, not `data/kb`, and produced a cited MEDIUM-confidence answer. The chain's real friction is **degradation, not failure**:
1. **Front door (F1):** the chain cannot start on a fresh environment — `corp ingest` crashes until `<mywork>/.corp/content_registry.yaml` is hand-seeded.
2. **Weakest link (F6):** UC2→UC3 grounding survived **only because the search token was in the note title**. Body-phrased retrieval returns 0 (`stranded stock`→0, `47000`→0). At real-vault scale (886 notes) an RFP question in natural language would frequently miss the relevant note.
3. **Hollow middle (F7):** "facts" are never stored (no `facts` table); the chain grounds on note **metadata + the LLM re-reading the note**, not a facts KB.

**Against SIM-1** ("ingest → vault → cited retrieval + draft Content-Manifest entry"): the **ingest → vault → cited-retrieval → draft** legs are achieved at sandbox scale. The **"Content-Manifest entry"** artifact is **not** produced by any witnessed path (no producer) — the one genuinely missing SIM-1 output.

---

## Gap list — RANKED by what blocks SIM-1 (tomorrow's work queue)

**SIM-1 = ingest → vault → cited retrieval + draft Content-Manifest entry.** Ranked most-blocking first.

| Rank | Gap | Blocks | Fix shape (small → large) |
|---|---|---|---|
| **1** | **F1** — `corp ingest` crashes (uncaught `FileNotFoundError`) with no `<mywork>/.corp/content_registry.yaml`; no fallback to shipped `config/content_registry.yaml`, no bootstrap | Ingest front door on any fresh env | Fall back to repo `config/` copy + friendly error; seed on first run |
| **2** | **F6** — retrieval FTS is over note **metadata only** (title/topics/products), not body | "Cited retrieval" — the core of SIM-1 | Add note-body to `notes_fts`, or restore a `facts` FTS as the retrieval surface |
| **3** | **F7** — facts pipeline absent: no `facts` table; 18 `key_facts` never become rows; `facts_count=0` at all 31 consumer sites | Grounded/citable facts + all analytics | Wire `key_facts` → `facts`/`facts_fts` on index rebuild |
| **4** | **F16 + F9** — ingest writes no `project-info.yaml`; note `client=''` → project↔vault unlinked, briefs find 0 sources | "Show my project" + the Content-Manifest entry | Emit `project-info.yaml` on ingest; propagate routing client into note frontmatter |
| **5** | **F8** — one source → two indexed notes (package `index.md` indexed as a note) | Retrieval/citation cleanliness | Exclude package `index.md`/`synthesis.md` from the note indexer |
| **6** | **—** | *(the "Content-Manifest entry" itself has no producer — build it once 1–5 land)* | New producer emitting the manifest entry |
| — SIM-2 — | **F11** orphan `data/kb` (Word/Excel RFP agent, no producer); **F21/F22** CKE tier inconsistency + local-extractor schema drift (`type='note'`/`quality='local'`) | KB-grounded RFP federation (later) | KB producer; unify CKE tiering + fix local-extractor enums |
| — Hygiene — | **F18** AppConfig≠PipelineConfig roots (portability + sandbox leak); **F26** `com` reads/writes real `project_codes.xlsx` unsandboxed; **F28** freshness blind to `01_Knowledge`; **F2/F13/F23/F31** LLM cost/token not surfaced | Isolation, portability, observability | Single config resolver; add `PROJECT_CODES_EXCEL`/roots to the config surface; extend freshness to `01_Knowledge`; print tokens+cost |

---

## Education block — 5 lines a product owner reads with coffee

1. **The spine works.** Drop a source in → it routes, extracts a rich Sonnet-written knowledge note, and you can get a **cited RFP draft** back. Ingest → vault → cited-draft runs end-to-end (for pennies — ~$0.045 for the whole night).
2. **But search only reads titles, not contents.** Ask for "stranded stock" or "47,000" and you get **nothing**; it only found the note because "Halcyon" was in the title. In a real 886-note vault this misses most content.
3. **"Facts" are a mirage.** The system extracts 18 facts per note into frontmatter but **stores 0** — every "facts" count and analytic reads 0. The RFP answer worked by re-reading the note, not from a facts database.
4. **The expected RFP failure didn't happen.** The "missing knowledge-base producer" everyone worried about sits on a *different, secondary* lane (Word/Excel); the everyday `corp rfp answer` works from the vault.
5. **Build first:** (1) stop ingest crashing on a missing config + ship it; (2) make search read note **bodies** (or turn the facts pipeline on) so retrieval finds content; (3) link each project to its own notes. Do those three and SIM-1 is real.

---

## Safety & isolation disclosure (full)

- **No real asset was written or deleted.** Real vault (886 files / 42,584,635 bytes), all 3 real DBs (SHA-256), and MyWork root mtime were **identical** at every checkpoint (#1 post-UC1, #2 post-UC4, #3 post-UC8) and at teardown. `git` tree clean throughout.
- **Two disclosed READ-only leaks** via lanes that bypass the sandbox env (both surfaced *by* the audit, both read-only, neither wrote):
  1. **F18** — `corp project show` → `project_resolver` used `AppConfig.projects_root`, which ignored `MYWORK_ROOT` and **read-enumerated the real MyWork/10_Projects** (listed folder names). Closed mid-run by setting `PROJECTS_ROOT`/`TEMPLATES_ROOT`/`ARCHIVE_ROOT`; re-verified `ISOLATION_VERIFIED_OK (both configs)`.
  2. **F26** — `com list` read the real `project_codes.xlsx` (53 opportunities) because the opportunity lane resolves `PROJECT_CODES_EXCEL` from a `.env`, not the anchor vars. Env hardened afterward; **no `com` write command was run** (would have mutated real data).
- **Method caveat for future runs:** the GO/NO-GO gate must verify **AppConfig and the opportunity config**, not just `PipelineConfig` — the sandbox recipe needs `PROJECTS_ROOT`/`TEMPLATES_ROOT`/`ARCHIVE_ROOT`/`PROJECT_CODES_EXCEL` set explicitly (the repo's own `conftest` sets the roots; the opportunity var is undocumented).
- **Teardown confirmed.** Sandbox (`C:\…\Temp\corp_audit_sb`) removed and verified gone; no stray `corp_audit*`/`audit-*` artifacts remain in system temp. Final post-teardown integrity check: all real assets byte-identical to the pre-run baseline. **No leftovers.**

---

## Verdict summary

| UC | Story | Verdict | One-line |
|---|---|---|---|
| UC1 | Capture | **WORKS*** | Routes + extracts a deep note; *crashes on a fresh env until `.corp/content_registry.yaml` is seeded (F1) |
| UC2 | Find | **PARTIAL** | Findable by title/metadata only; no body search; no `facts` table |
| UC3 | RFP answer | **WORKS** | Cited draft from the vault — the expected KB-absence break did **not** occur |
| UC4 | Project view | **PARTIAL** | Surfaces render but on empty data (0 facts, no project↔vault link) |
| UC5 | CKE direct | **WORKS** | `scan` JSON stable; tiering + cost differ by entry point; local-extractor schema drift |
| UC6 | Synthesize/deck | **PARTIAL / NOT-WIRED** | Synthesis is internal-only; deck lane is real-data + template-copy |
| UC7 | Freshness | **WORKS** | Correct categories; unreadable-note regression handled; blind to `01_Knowledge` |
| UC8 | Classify | **WORKS** | Per-file LLM classification; records-driven; no cost surfaced |
| UC-X | Chain | **COMPLETES** | ingest→vault→cited-draft runs; degrades (not breaks) at retrieval scope (F6) |

*Run unattended 2026-07-17→18; fixed nothing, wired nothing, wrote nothing outside the sandbox.*
