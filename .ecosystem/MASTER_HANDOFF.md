---
Last updated: 2026-03-28T19:48:50Z
---

> **Paste this file into new Claude.ai chats for context.**

# Corporate OS — Master Session Handoff

This is a living document. Update at end of each session:
```
python scripts/update_handoff.py
```

---

## Live Stats

| Metric | Value |
|--------|-------|
| Vault notes (indexed) | 488      |
| Tests passing | 992      |
| Hybrid classifier accuracy | 93.7%      |
| Tag coverage (mean) | 79.7%      |
| People NER F1 | 92.7%      |
| Eval timestamp | 2026-03-27      |

---

## System Overview

**Corporate OS** is a private knowledge management system for a consulting firm (Blue Yonder ecosystem). 6 packages in a monorepo at `C:\Users\1028120\Documents\Dev\corp-monorepo`.

| Package | CLI | Purpose |
|---------|-----|---------|
| corp-os-meta | `corp-meta` | Schema, taxonomy, naming conventions |
| corp-knowledge-extractor | `cke` | Pure extraction engine — reads docs, writes JSON |
| corp-by-os | `corp` | Vault writer, ingest pipeline, retrieval, index |
| corp-project-extractor | `cpe` | Project scope/role classifier |
| corp-rfp-agent | scripts | RFP response generation |
| corp-opportunity-manager | `com` | Opportunity tracking |

**Architecture invariants (non-negotiable):**
- `corp-by-os` is SOLE vault writer
- `CKE` is PURE extraction engine — no vault writes
- Subprocess boundaries between packages (no cross-imports)
- Forward slashes everywhere in paths/databases

---

## Current State (as of 2026-03-28)

### Completed
- **MinHash dedup** (2026-03-27): `ingest/dedup.py` — 128-perm MinHash, `content_signatures` table in ops.db, `check_near_duplicate()` pipeline hook (after light_scan, before CKE), `corp dedup-report` CLI. 24 new tests. `datasketch` added as optional dep `[dedup]`.
- **Hybrid TF-IDF classifier** (2026-03-26): Dual-vectorizer (char n-gram filename + word n-gram content), 93.7% accuracy vs 57.1% regex-only, 18% LLM fallback. `USE_TFIDF` flag in `doc_type_classifier.py`.
- **Light scan module** (2026-03-26): `light_scan.py` — 7 format scanners (pptx/docx/pdf/xlsx/csv/txt-md/mp4), tiered fault tolerance (`full`/`degraded`/`filename_only`), `ScanResult` dataclass with dual feature spaces.
- **Client normalization** (2026-03-26): 48 aliases in `client_aliases.yaml`, 77 vault notes migrated, `schema.yaml` contract in corp-os-meta.
- **Full vault ingest** (2026-03-26): 493 unique notes indexed (25 projects). v2 + v3 extractions merged.
- **Naming convention v2** (2026-03-25): `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}`, 19 type codes, 15 client aliases. Council Decision #14.

### Active / In-Progress
- `check_near_duplicate()` implemented but **not yet wired** into `inbox.py` process_file()
- 2 Cognitive Friday notes skip on YAML parse error (unquoted hyphen in `session_id`)
- 2 low-quality JLR notes (score 28–29) not re-extracted

### Known Issues
- 6 pre-existing Jinja2 test failures (`TemplateNotFound: meta.yaml.j2`) — not caused by recent work
- LSH index rebuilt in-memory per query (acceptable for current vault size, may need persistence at scale)

---

## Next Steps

1. Wire `check_near_duplicate()` into `inbox.py` `process_file()` after `light_scan` call
2. Fix 2 Cognitive Friday YAML parse errors (unquoted hyphen in `session_id`)
3. Re-extract 2 low-quality JLR notes (score 28–29) with deeper prompt
4. Run `scripts/extract_training_data.py` to refresh CKE + corp-by-os fixtures
5. Fix 6 pre-existing Jinja2 test failures
6. 30-day skill evaluation due: **2026-04-25**

---

## Council Decisions (21 total — ADR summaries in `decisions/`, full transcripts in `.ecosystem/council_transcripts/`)

| # | Decision |
|---|----------|
| #14 | Naming convention v2 — `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}` |
| #13 | Hybrid classifier replaces pure regex (TF-IDF → regex → LLM cascade) |
| #12 | Light scan as pre-extraction step (Council Decision #19 in journal) |
| #11 | Client normalization: single canonical name, aliases in CKE |
| #10 | Subprocess boundary between packages — no Python cross-imports |

---

## Key Config

- Paths: `config/paths.toml`
- Naming: `packages/corp-by-os/config/naming_config.yaml` (19 type codes, 15 client aliases)
- DBs: `%LOCALAPPDATA%/corp-by-os/ops.db` (ingest ops), `%LOCALAPPDATA%/corp-by-os/index.db` (retrieval)
- API key standard: `GEMINI_API_KEY` (not GOOGLE_API_KEY)
- Eval history: `eval/eval_history.jsonl`
- Vault: `C:/Users/1028120/Documents/ObsidianVault`

---

## Session Protocol

1. Read last 5 entries from `JOURNAL.md` before starting
2. Check `~/.claude/skills/gotchas/gotchas.md` before modifying any package
3. After implementation: self-review (error handling, edge cases, gotchas)
4. Before merging: `./scripts/dev-check.ps1`
5. Append 3-line summary to `JOURNAL.md`
6. Run `python scripts/update_handoff.py` to refresh this file
