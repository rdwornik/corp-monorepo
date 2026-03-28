---
# ADR-22: RFP KB Federation with Vault Search

**Date:** 2026-03-28
**Status:** Accepted
**Council debate:** `.ecosystem/council_transcripts/DECISION_22_rfp_federation.md`
**Panelists:** claude-opus-4-6, gemini-3.1-pro-preview, deepseek-reasoner, grok-4.20-beta
**Synthesizer:** openai (non-participant)

## Context

Two separate knowledge silos existed: the vault (488 notes, FTS5 indexed in `index.db`)
and the RFP KB (1,325 curated entries, separate ChromaDB in `corp-rfp-agent`). Users
running `corp retrieve "WMS picking"` would get vault results only — missing highly
relevant curated RFP answers. `corp prep` had the same blind spot. No unified query
path existed.

## Decision

Federate RFP KB search into `corp retrieve` using a second FTS5 table (`rfp_entries`)
in the existing `index.db`. Default to `--source all`. Present results in grouped,
source-labeled sections with per-source caps rather than a single interleaved ranking.

**What to build:**
1. Add `rfp_entries` FTS5 table to `index.db` (separate table, same file, independent rebuild)
2. Build `corp rfp-index` command: reads `corp_data/rfp_kb/*.md` via normalization adapter, upserts `rfp_entries`. Include `--check` flag to validate 5 random entries parse correctly.
3. Extend `corp retrieve` with `--source vault|rfp|all` flag (default: `all`). Display as grouped sections:
   ```
   RFP KB (curated) — top 3
   1. ...

   Vault Notes — top 5
   1. ...
   ```
4. Extend `corp prep` to include federated retrieval. Inject sources as separate XML blocks in LLM context: `<rfp_answers trust="curated">` and `<vault_context trust="extracted">`.

**What not to do:**
- Do not mathematically interleave BM25/FTS5 scores across tables — corpus statistics differ per table, scores are not comparable
- Do not migrate RFP KB entries into vault as notes — violates single-source-of-truth
- Do not create a separate `rfp_index.db` file — operational overhead exceeds benefit at this scale
- Do not replace `corp-rfp-agent`'s ChromaDB — that package keeps its own search; this is read-through indexing only

## Key constraints

- `corp-rfp-agent` remains the authoritative owner of RFP KB files
- `corp-by-os` owns all writes to `index.db` — RFP indexer runs via `corp rfp-index`, not via rfp-agent directly
- Per-source display caps (default: top 3 RFP, top 5 vault) solve the 2.7:1 cardinality imbalance without hiding federation behind a flag
- Label RFP results with file mtime; flag entries older than 18 months with `[STALE?]`

## Alternatives rejected

- **Separate `rfp_index.db` file** (Proposal A / Gemini): principled isolation but over-engineered for solo-developer, single-file CLI tool at this scale; logical isolation via separate table is sufficient
- **Default `--source vault`** (Grok final position): leaves the original problem intact — users miss RFP answers unless they remember a non-default flag; optional flags are underused in practice
- **Static cross-index score boosts** (DeepSeek/Grok initial): `+0.1` or `1.5×` multipliers on FTS5/BM25 scores are mathematically incoherent across corpora with different document counts and term distributions
- **Migrate RFP KB to vault as notes**: creates sync/reconciliation burden, duplicates data, violates package ownership

## Revisit triggers

- Users consistently skip the RFP section → federation not adding value → consider `--source vault` default
- Users complain that the best result is in the wrong section → implement reciprocal rank fusion
- Combined corpus exceeds 5,000 entries → revisit per-source caps and add relevance thresholds
- `corp-rfp-agent` changes markdown format → `corp rfp-index --check` smoke test should catch this
- If >40% of RFP KB files are unparseable → write one-time normalization script for the KB before proceeding
---
