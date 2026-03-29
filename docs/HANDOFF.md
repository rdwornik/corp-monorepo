---
Last updated: 2026-03-29T01:13:07Z
---

> **Paste this file into new Claude.ai chats for context. This is the ONLY document a new chat needs.**

# Corporate OS — Master Session Handoff

Update at end of each session: `python scripts/update_handoff.py`

---

## Live Stats

| Metric | Value | Date |
|--------|-------|------|
| Tests passing | 2,412 | 2026-03-29 |
| Vault notes (indexed) | 488   | 2026-03-28 |
| Hybrid classifier accuracy | 93.7%   | 2026-03-26 |
| Tag coverage (mean) | 79.7%   | 2026-03-26 |
| Product Jaccard | 1.000 (idempotent) | 2026-03-26 |
| People NER F1 | 92.7%   | 2026-03-26 |
| Council decisions | 24 | 2026-03-29 |
| ADRs | 24 | 2026-03-29 |
| Gotchas | 37 | 2026-03-28 |

---

## System Overview

**Corporate OS** is a private knowledge management system for a consulting firm (Blue Yonder presales ecosystem). Monorepo at `C:\Users\1028120\Documents\Dev\corp-monorepo`.

**Consolidated layout** (2026-03-29): all 6 former packages unified under `src/corp/`. Single `pyproject.toml`, single `pip install -e .`.

| Module (src/corp/) | CLI | Purpose |
|---------------------|-----|---------|
| `schema/` | `corp-meta` | Schema, taxonomy, naming conventions, `schema.yaml` contract |
| `extractor/` | `cke` | Pure extraction engine — reads docs, writes JSON, no vault writes |
| `cli/`, `ingest/`, `retrieve/` | `corp` | Vault writer, ingest pipeline, retrieval, SQL index, analytics |
| `project/` | `cpe` | Project scope/role classifier |
| `rfp/` | scripts | RFP response generation |
| `opportunity/` | `com` | Opportunity tracking |

**Total: 2,404 tests (0 failed)**

---

## Full Pipeline

```
File
 │
 ├─ light_scan()          [light_scan.py, CKE]
 │   7 format scanners: pptx/docx/pdf/xlsx/csv/txt-md/mp4
 │   → ScanResult(filename_text, content_text, scan_quality: full/degraded/filename_only)
 │
 ├─ Classify (Hybrid, 93.7%)   [doc_type_classifier.py, CKE]
 │   TF-IDF (char n-gram filename + word n-gram content) → regex → LLM fallback (18%)
 │   → type_code (19 types from naming_config.yaml)
 │
 ├─ check_near_duplicate()     [dedup.py, corp-by-os]  ← NOT YET WIRED INTO inbox.py
 │   MinHash 128-perm, word 3-grams, content_signatures table in ops.db
 │   → list of (note_id, similarity_score) or []  (fail-open)
 │
 ├─ Extract (CKE tiered)       [tier_router.py + extractors/, CKE]
 │   Tier 1: local/free (CSV, structured text)
 │   Tier 2: text AI — gemini-2.0-flash-lite ($0.25/1M)  ← updated 2026-03-28
 │   Tier 3: multimodal — gemini-2.0-pro-preview ($4.00/1M)
 │   Haiku enrichment: claude-haiku-4-5 for people NER
 │   → CKE package (JSON: frontmatter + facts + slide_breakdown)
 │
 ├─ post_process_extraction()  [post_process.py, CKE]
 │   schema validation (warn-only), client normalization, tag alias expansion
 │   → normalized JSON with canonical client names
 │
 ├─ Quality Gate               [ingest/quality.py, corp-by-os]
 │   score < 25 → quarantine (22 quarantined)
 │   score 25–49 → soft-fail (ingest with warning)
 │   score 50+ → pass
 │
 ├─ Vault Write                [vault_io.py, corp-by-os]
 │   corp-by-os is SOLE vault writer
 │   → 01_Knowledge/{note_id}.md (flat, no subfolders)
 │   deprecated notes: trust_level=deprecated, stay in vault, excluded from retrieval
 │
 ├─ Index                      [index_builder.py, corp-by-os]
 │   SQLite FTS5, index.db
 │   488 notes + 25 projects + people now indexed
 │   → index.db
 │
 └─ Retrieve                   [query_engine.py + retrieve_engine.py, corp-by-os]
     `corp retrieve "query"` — FTS5 + client/product filters
     `corp prep <client>` — client briefing with OR LIKE variant expansion
     `corp analytics *` — SQL analytics (6/10 benchmark queries)
```

---

## Eval Progression (the story)

| Date | Classifier | Tags (mean) | Product Jaccard | People F1 | Notes |
|------|-----------|-------------|-----------------|-----------|-------|
| 2026-03-26 baseline | 14.5% (45/310) | 0.657 | 0.844 | 0.927 | Regex-only, filename-only features |
| 2026-03-26 +patterns | 51.3% (159/310) | 0.657 | 1.000 | 0.927 | Added 6 high-priority filename patterns |
| 2026-03-26 +tags | 51.3% | 0.753 | 1.000 | 0.927 | Added 3 tags to taxonomy.yaml |
| 2026-03-26 +patterns2 | 57.1% (177/310) | 0.791 | 1.000 | 0.927 | Fixed architecture pattern ordering bug |
| 2026-03-26 +tags2 | 57.1% | 0.797 | 1.000 | 0.927 | Added inventory-ops-agent, logistics-emissions-calculator |
| 2026-03-26 **hybrid** | **93.7%** | 0.797 | 1.000 | 0.927 | Dual TF-IDF vectorizer, +32.3pp over regex |

**Key milestones:**
- 14.5% → 51.3%: Added filename patterns to regex classifier (+36.8pp)
- 51.3% → 57.1%: Fixed architecture/cognitive ordering bug (+5.8pp)
- 57.1% → 93.7%: Hybrid TF-IDF + LogisticRegression dual vectorizer (+36.6pp)
- Product Jaccard locked at 1.000 since first taxonomy fix (idempotent)
- People F1 0.927 stable throughout (Haiku enrichment, no regression)
- 30-day eval checkpoint: **2026-04-25**

---

## Vault State

```
ObsidianVault/
├── 01_Knowledge/       488 active notes (flat — no subfolders)
│                       326 deprecated (trust_level: deprecated, source inaccessible)
│                       22 quarantined (quality_score < 25)
├── 02_Navigate/        9 MOCs (Maps of Content)
│   ├── MOC_Products.md
│   ├── MOC_Clients.md
│   ├── MOC_Domains.md
│   ├── MOC_People.md
│   ├── MOC_Projects.md
│   ├── MOC_RFP.md
│   ├── MOC_Workflows.md
│   ├── MOC_Compliance.md
│   └── MOC_Home.md
├── 10_Projects/        [MyWork mirror — see MyWork State]
└── 30_Templates/       presentation templates registry
```

- **Zero plugins** (Council #17: minimal-core-only policy, no format-modifying plugins)
- Deprecated notes excluded from all retrieval paths (`include_deprecated=False` default)
- Schema: `schema.yaml` in corp-os-meta — 4 required fields, 56 optional, warn-only validation
- Client normalization: 48 aliases in `client_aliases.yaml` (CKE), 77 vault notes migrated

---

## MyWork State

```
C:/Users/1028120/Documents/MyWork/10_Projects/
├── 24 client project folders
├── 595 total files
│   ├── 585 old naming convention (pre-v2)
│   └── 10 naming v2 ({YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext})
└── Sandbox rename: tested, pipeline ready, NOT yet applied
```

- `corp folder-review` currently produces 0 renames = stable state
- 585 files await bulk rename to v2 convention (open decision)

---

## All 24 Council Decisions

| # | Title | Key Decision |
|---|-------|-------------|
| #1 | Knowledge Architecture | Hybrid YAML registry + SQLite FTS5; no unstructured RAG; mandatory provenance |
| #2 | Extraction Quality | Tiered extraction: universal base schema + deep overlays; on-demand only; $2-4/month budget |
| #3 | Model Selection (SUPERSEDED) | Empirical benchmarking required before committing; superseded by #8a |
| #4 | Vault Structure (SUPERSEDED) | Semantic meaning in frontmatter not folders; superseded by #7 |
| #5 | Re-extraction Strategy | Parallel v2 extraction to separate location, quality validation, clean cutover; no nightly automation |
| #6 | Quality Gate | Centralized gate in corp-by-os (graduated pass/soft-fail/hard-fail); CKE never self-approves |
| #7 | Vault Navigation | Flat source notes in 01_Knowledge/; browsable MOC tree in 02_Navigate/; 6 dimensions as tags |
| #8a | Model Tiering | Multi-tier quality-optimized LLM routing; policy-based auto-routing; version-gated re-extraction |
| #8b | Gemini Capabilities | Structured Outputs adopted (JSON schema mandatory); Document Understanding deferred |
| #9 | Knowledge Dimensions | 3 operational zones (Projects/Workflows/Reference) + Security/Compliance; 11 dimensions as tags |
| #10 | Naming Convention | Type-first naming with controlled vocabulary in naming_config.yaml; 220-char path cap |
| #11 | File Distribution Algorithm | Rules-dominant hybrid routing; deterministic rules for common cases; LLM fallback patterns promoted to rules quarterly |
| #12 | Claude Code Patterns | Minimal custom layer; global gotchas.md skill; targeted verification scripts; no third-party Superpowers |
| #13 | Monorepo Architecture | 6 repos → 1 monorepo; subprocess-only cross-package comms; corp-by-os sole vault writer |
| #14 | Naming Convention v2 | `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}`; 19 type codes; 15 client aliases; supersedes #10 |
| #15 | Sandbox Testing | `PipelineConfig` dataclass with `production()`/`sandbox()` classmethods; `SandboxManager` for isolated E2E tests |
| #16 | Eval Metrics | Locked stratified 80/20 split (248/62); baseline frozen at 51.3% / 0.753 tags; 30-day checkpoint |
| #17 | Obsidian Plugins | 8 MOCs as primary navigation; minimal-core-only plugin policy; no format-modifying plugins |
| #18 | Algorithmic Hybrid | Dual-vectorizer TF-IDF + LogisticRegression; JSON only (no pickle); order: TF-IDF → regex → LLM |
| #19 | Light Scan | `light_scan.py` with `ScanResult`; 7 format scanners; tiered fault tolerance; runs before CKE |
| #20 | Vault Rebuild | Re-extract 216 notes via CKE batch (gemini-pro deep); deprecated filter added to retrieval |
| #21 | Ontology Approach | `taxonomy.yaml` as single authoritative tag vocab; `product_aliases.yaml` + `client_aliases.yaml` normalize variants |
| #22 | RFP Federation | How to federate RFP KB (1,325 entries) with vault search (487 notes) — same `index.db`, separate `rfp_entries` FTS5 table, grouped output, default `--source all` |
| #23 | Monorepo Internal Architecture | Split cli.py monolith (3,573 lines → 14 modules); eliminate cke_client.py boundary violation via subprocess; flatten doctor/freshness/extraction/non_project; centralize parse_llm_json in corp-os-meta; delete 4 dead corp-rfp-agent files |
| #24 | MyWork Knowledge Architecture | 7 canonical folders (00_Inbox, 10_Projects, 20_Workflows, 30_Reference, 70_Admin, 80_Compliance, 90_Archive) + hidden .corp for pipeline infra. Removed 30_Templates, 50_RFP, 60_Source_Library. Access-frequency principle. |

Full transcripts: `.ecosystem/council_transcripts/DECISION_NN_*.md`
ADR summaries: `decisions/ADR-NN-*.md` (ADR-01 through ADR-23)

---

## Key Infrastructure

| Artifact | Path | Purpose |
|----------|------|---------|
| `hybrid_classifier.json` | `models/hybrid_classifier.json` (also in CKE data/) | Dual TF-IDF + LogisticRegression, JSON only (no pickle), LRU-cached loader |
| `ops.db` | `%LOCALAPPDATA%/corp-by-os/ops.db` | File registry, routing decisions, MinHash `content_signatures`, ingest events (2,673+ rows) |
| `index.db` | `%LOCALAPPDATA%/corp-by-os/index.db` | FTS5 index: 488 notes + 25 projects + people |
| `schema.yaml` | `src/corp/schema/data/schema.yaml` | Frontmatter contract: 4 required, 56 optional, cardinality caps |
| `naming_config.yaml` | `config/naming_config.yaml` | 19 type codes, 15 client aliases |
| `taxonomy.yaml` | `src/corp/schema/taxonomy.yaml` | Authoritative tag vocabulary |
| `client_aliases.yaml` | `src/corp/extractor/data/client_aliases.yaml` | 48 client alias entries |
| `product_aliases.yaml` | `src/corp/extractor/data/product_aliases.yaml` | Product normalization |
| `paths.toml` | `config/paths.toml` | Centralized path config (vault, mywork, DBs) |
| `eval_history.jsonl` | `eval/eval_history.jsonl` | 21 eval snapshots tracking classifier/tag/product/people metrics |
| `gotchas.md` | `~/.claude/skills/gotchas/gotchas.md` | 37 cross-repo gotchas — CHECK BEFORE MODIFYING ANY PACKAGE |
| `JOURNAL.md` | `JOURNAL.md` | Append-only session log — READ LAST 5 ENTRIES BEFORE STARTING |

---

## corp CLI Commands (43 total)

```
# Projects
corp project list / show <name> / open <name>

# Vault
corp vault validate [project]

# Index
corp index rebuild / stats

# Retrieval
corp retrieve "query"           --client --product --top --format --rfp-only --verbose
corp prep <client>              client briefing with alias expansion
corp query "terms"              search facts/metadata

# Analytics (SQL)
corp analytics report           cross-project dashboard
corp analytics products         Q1: products per client
corp analytics timeline         Q2: notes for client by date
corp analytics clients          Q3: clients per product
corp analytics overlap          Q6: client overlap on product
corp analytics compare          Q9: side-by-side client product sets
corp analytics recent           Q10: most recent note per client

# Ingest
corp ingest [PATH]              route files via content registry
corp ingest-inbox               interactive inbox routing (00_Inbox → destinations)
corp ingest-extractions <path>  ingest CKE output into vault

# Extraction
corp extract <folder>           extract via CKE
corp overnight                  overnight extraction pipeline  --scope --budget --dry-run --batch
corp audit                      read-only MyWork audit        --skip-gemini --budget --model

# Cleanup
corp cleanup-scan               scan for misplaced files, generate moves.yaml
corp apply-moves                execute approved moves
corp cleanup                    disk space analysis           --scope --execute
corp folder-review              scan 10_Projects/, propose renames

# Files/Dedup
corp dedup-report               show near-duplicate pairs (MinHash)
corp files-stats                file registry statistics
corp naming-stats               type code distribution from routing feedback

# Templates
corp template list / scan / select "goal"

# Review
corp finalize                   review/approve staged files
corp classify                   classify quarantined files via Gemini LLM

# Freshness
corp freshness                  check vault note freshness vs source files

# RFP
corp rfp answer "question"      draft answer from KB

# Tasks
corp task add / list / done
corp tasks                      alias for task list

# System
corp doctor                     check all CLIs on PATH, system integrity
corp trust-status               trust_level distribution
corp routing-review             routing override patterns
corp routing-mark-reviewed      mark routing feedback reviewed
corp run <workflow>             execute workflow

# Testing
corp test-pipeline              E2E sandbox smoke test  --live --record --keep-sandbox --verbose
corp chat                       interactive natural language routing
```

---

## SQL Analytics

Built 2026-03-28. 6/10 benchmark queries answered by SQL; 4 require ontology layer.

| Command | Query | Status |
|---------|-------|--------|
| `corp analytics products --client X` | Q1: Distinct products for client | SQL ✓ |
| `corp analytics timeline --client X` | Q2: Notes for client by date | SQL ✓ |
| `corp analytics clients --product X` | Q3: Clients mentioning product | SQL ✓ |
| `corp analytics overlap --product X` | Q6: Clients sharing product interest | SQL ✓ |
| `corp analytics compare --clients "A,B"` | Q9: Side-by-side client product sets | SQL ✓ |
| `corp analytics recent` | Q10: Most recent note per client | SQL ✓ |
| Q4, Q5, Q7, Q8 | Semantic product grouping queries | Needs ontology (Q4 open decision) |

---

## Gemini Models (updated 2026-03-28)

| Tier | Model | Cost | Use |
|------|-------|------|-----|
| Tier 1 | Local/free | $0 | CSV, structured text, simple extraction |
| Tier 2 (text) | `gemini-2.0-flash-lite` | $0.25/1M tokens | Standard text extraction (-75% vs previous) |
| Tier 3 (multimodal) | `gemini-2.0-pro-preview` | $4.00/1M tokens | Presentations, images, complex docs |
| Haiku enrichment | `claude-haiku-4-5` | low | People NER enrichment in CKE |

- API key standard: `GEMINI_API_KEY` (never `GOOGLE_API_KEY`)
- Keys in `C:\Users\1028120\Documents\.secrets\.env`
- ZDR (Zero Data Retention) enforced per ADR-08a

---

## Standalone Repos

| Repo | Tests | Purpose | Status |
|------|-------|---------|--------|
| `ai-council/` | 169 | Multi-provider AI debate framework; 5 providers, 78 debates | Active |
| `corp-ops/` | 73 | OneDrive/SharePoint/GDrive file operations | Active |
| `corp-sca-time-automation/` | — | SharePoint time entry automation | Active |
| `.archived/corp-pdf-toolkit/` | — | PDF extraction toolkit | **Archived** 2026-03-28 (CKE covers this) |

All repos at `C:\Users\1028120\Documents\Dev\`

---

## Architecture Rules (non-negotiable)

1. `ingest/` is SOLE vault writer — no other module writes to ObsidianVault
2. `extractor/` is PURE extraction engine — reads docs, writes JSON, never touches vault
3. Unified `src/corp/` namespace — single `pyproject.toml` at repo root
4. Forward slashes everywhere in databases and path strings
5. No new dependencies without explicit user confirmation
6. `GEMINI_API_KEY` is the standard (not `GOOGLE_API_KEY`)
7. API keys in env vars only — never in config files, never committed
8. NEVER let any operation touch `OneDrive - Blue Yonder` paths
9. Feature branches only — never commit directly to main

---

## Communication Preferences

- **Insight-first** — lead with the answer, not the reasoning
- **Bold key phrases** — scannable output
- **ADHD-optimized** — short paragraphs, bullet points, tables over prose
- **Challenge assumptions** — push back when something smells wrong
- **Minimal diffs** — change only what's needed, nothing more
- **No speculative abstractions** — 3 similar lines > premature abstraction

---

## Prompt Format Standards (from CLAUDE.md)

| Scope | Format |
|-------|--------|
| 1 file, 1 package | Conversational (just talk to Claude Code) |
| 2–3 files, 1 package | Conversational with context |
| 3+ files, 2+ packages | Formal `.md` prompt |
| Architecture decision | AI Council debate |

**Task routing:**
- Tier 1 (Sonnet): ≤5 files, ≤1 layer, existing pattern, automated checks
- Tier 2 (Opus): new abstractions, cross-module, unfamiliar APIs, security

---

## Key File Paths (all Dev/ paths)

```
Monorepo:       C:/Users/1028120/Documents/Dev/corp-monorepo/
Vault:          C:/Users/1028120/Documents/ObsidianVault/
MyWork:         C:/Users/1028120/Documents/MyWork/
Secrets:        C:/Users/1028120/Documents/.secrets/.env
RFP KB:         C:/Users/1028120/Documents/corp_data/rfp_kb/
ops.db:         %LOCALAPPDATA%/corp-by-os/ops.db
index.db:       %LOCALAPPDATA%/corp-by-os/index.db

Monorepo layout:
  config/paths.toml                          centralized paths
  decisions/ADR-NN-*.md                      22 ADR summaries
  .ecosystem/council_transcripts/            22 full debate transcripts
  eval/eval_history.jsonl                    metric snapshots
  models/hybrid_classifier.json             dual TF-IDF model
  JOURNAL.md                                 session log
  scripts/dev-check.ps1                      pre-merge quality gate
  scripts/update_handoff.py                  regenerates this file

Source paths (src/corp/):
  schema/data/schema.yaml                    frontmatter contract
  schema/taxonomy.yaml                       tag vocabulary
  extractor/data/client_aliases.yaml         48 client aliases
  extractor/data/product_aliases.yaml        product normalization
  config/naming_config.yaml                  19 type codes, 15 client aliases
  ingest/dedup.py                            MinHash
  ingest/inbox.py                            ← MinHash NOT YET WIRED HERE
  ingest/light_scan.py                       7-format scanner
```

---

## Open Decisions (what's next)

### ADR-23 Implementation — COMPLETE (2026-03-29)
All 4 phases done. Final step: 6-package consolidation into unified `src/corp/` namespace.
- Phase 1: CLI split (14 modules) ✓
- Phase 2: Subprocess boundary ✓
- Phase 3: Flatten nesting ✓
- Phase 4: Centralize utils + dead code ✓
- Phase 5: Consolidate 6 packages → `src/corp/` ✓ (2,404 tests passing)

### Other open decisions
5. **Ontology Q4** — canonical product map; unblocks 4 remaining benchmark SQL queries
6. **RFP Federation** (ADR-22) — implement `corp rfp-index` + `rfp_entries` FTS5 table + grouped `corp retrieve` output; not yet built
7. **File renames** — bulk rename 585 MyWork files to naming v2 convention
8. **Local AI** — Ollama exploration for offline/private extraction tier
9. **Outlook automation** — email ingestion pipeline
10. **30-day skill eval** — due **2026-04-25** (baseline: 2026-03-26)

---

## Pending Fixes

1. **MinHash not wired** — `check_near_duplicate()` exists in `dedup.py` but not called from `inbox.py` `process_file()` after `light_scan()`
2. **2 Cognitive Friday YAML errors** — `session_id: "cognitive-friday-season-2` unquoted hyphen truncates string; notes skip on ingest
3. **2 low-quality JLR notes** — score 28–29 (threshold 25), need re-extraction with deeper prompt
4. ~~**6 Jinja2 test failures**~~ — resolved during consolidation (template paths updated)
5. ~~**1 flaky timer test**~~ — fixed: switched to `time.perf_counter()` for sub-ms precision

---

## Session Protocol

1. Read last 5 entries from `JOURNAL.md` before starting
2. Check `~/.claude/skills/gotchas/gotchas.md` before modifying any package (41 gotchas)
3. After implementation: self-review — error handling, edge cases, gotchas
4. Before merging: `./scripts/dev-check.ps1`
5. Append 3-line summary to `JOURNAL.md` (Did / Failed / Next)
6. Run `python scripts/update_handoff.py` to refresh this file

**If tests fail with a novel pattern:**
- Check if gotcha already exists → update "Last triggered" date
- If new → add entry (Gotcha / Trigger / Symptom / Fix / Last triggered)
- Fix issue, re-verify, then summarize in session handoff
