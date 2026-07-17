# ADR-33: RFP KB federation via INDEX_EXTRA_ROOTS (supersedes ADR-22)

- **Status:** Proposed
- **Date:** 2026-07-17
- **Decision tier:** Technical-architect intake triage (Path A), 2026-07-06 decision register DR-1
- **Supersedes:** ADR-22 (RFP KB Federation with Vault Search) — takes effect on ratification only; see Consequences.
- **Related:** ground-truth D-7 (`docs/audits/2026-07-16-architecture-ground-truth.md` §6)
- **Intake:** `docs/audits/2026-07-06-technical-architect-intake.md`, DR-1
- **Decommission:** none — ADR-22's `rfp_entries`-table design was never built, so there is nothing on disk to remove; the orphan JSON path (see Context) is not decommissioned by this ADR, only scoped out of it.
- **Source:** 2026-07-06 technical-architect intake decision register (ratified); evidence in `docs/audits/2026-07-05-deep-rfp.md` §Step 5

## Context

Two separate knowledge silos exist for RFP answering: the Obsidian vault (index.db `notes`/`notes_fts`, 488 notes) and a 1,329-file curated RFP answer-KB corpus at `corp_data/rfp_kb/*.md` (uniform 9-field frontmatter: `trust_level`, `products`, `category`, etc.). ADR-22 (2026-03-28) ratified a federation design — a separate `rfp_entries` FTS5 table, a new `corp rfp-index` command, and a `--source vault|rfp|all` flag with grouped, capped display — explicitly rejecting index-time merge ("Do not... mathematically incoherent" scoring across corpora). That design remains **entirely unbuilt**: no `rfp_entries` table, no `rfp-index` command exists anywhere in `src/` (`docs/audits/2026-07-05-deep-rfp.md` headline #2).

Meanwhile a second, lighter mechanism was built and unit-tested but never switched on: `rebuild_index` already loops `config.index_extra_roots` (`index_builder.py:214-221`), `_index_cke_notes` already handles rfp_kb frontmatter (`index_builder.py:636-640`), `_compute_rfp_visible` rule 3 already treats `trust_level: verified` KB entries as always-visible (`index_builder.py:584,596-597`), and `tests/test_index_builder.py:450-498` tests exactly this scenario end-to-end. The single switch — env var `INDEX_EXTRA_ROOTS` (`config.py:100`) — has never been set; the index today holds only the 488 vault notes (`meta.last_rebuild` = 2026-03-28).

Today's effective RFP-answerable pool is **39 notes** — not 1,329, and not even the nominal 182 `rfp_visible=1` rows: 143 of those 182 carry `confidence='deprecated'`, which retrieval excludes by default (`docs/audits/2026-07-05-deep-vault-metadata.md` §2.4). The 1,329-file KB is the highest-value data in the estate and is currently unreachable by any retrieval path.

Context has also changed since ADR-22 was ratified: `corp-rfp-agent` — which ADR-22 named the "authoritative owner of RFP KB files" and whose ChromaDB it deliberately preserved — has since been archived into the monorepo, and that ChromaDB no longer exists (`docs/audits/2026-07-05-deep-rfp.md` §Step 5 preamble). The ownership constraint ADR-22 built its decision around is stale.

**Ground-truth note (must be honored by anyone wiring to this ADR):** `data/kb/canonical/RFP_Database_UNIFIED_CANONICAL.json` — a *different* KB representation consumed by `rfp/llm_router.py:54,211-213` and `rfp_answer_word.py:69,332-333` — is an **orphan input with no producer anywhere in-repo**, and `data/kb/` does not exist on disk in this checkout (`docs/audits/2026-07-16-architecture-ground-truth.md` §6 D-7). This ADR's federation target is exclusively the **markdown KB corpus** at `corp_data/rfp_kb/*.md` — **not** the JSON path. The JSON path's disposition (repair a producer, or kill the consumers) is delegated to the R1 (FR-1) rewrite decision and is explicitly out of scope here; it must not be silently wired to this ADR's federation mechanism.

## Decision

Activate the built-but-dormant index-time federation:

1. Set `INDEX_EXTRA_ROOTS=<path to corp_data/rfp_kb>` and run `corp index rebuild`. This merges the markdown RFP-KB corpus into the existing `notes`/`notes_fts` tables in `index.db`, using the already-unit-tested code path (`tests/test_index_builder.py:450-498`).
2. This **formally supersedes ADR-22.** ADR-22 chose deliberate corpus *separation* (a second `rfp_entries` table, no cross-corpus score interleaving — the exact thing it rejected). `INDEX_EXTRA_ROOTS` does the opposite: an index-time *merge* into the single `notes` table with interleaved BM25 ranking across both corpora. This is a genuine reversal of ADR-22's core design choice, not an incremental extension, and is named as such.
3. The federation target is the markdown KB corpus (`corp_data/rfp_kb/*.md`) only. The orphan `data/kb/canonical/*.json` consumer path (ground-truth D-7) is explicitly out of scope for this decision.

## Consequences

**Positive:**
- One env var + one rebuild reaches all 1,329 KB files (1,155 of them `trust_level: verified`) from `corp retrieve --rfp-only`, closing the highest-value/least-reachable gap in the estate at near-zero build cost (`a′` sizing: **S**, vs option `a`'s **M** or option `b`'s **L** — `docs/audits/2026-07-05-deep-rfp.md` Backlog-seed RFP-1).
- `_staging/` KB drafts (174 files, `trust_level: draft`) are correctly excluded by construction — the same rule that already protects vault notes (`index_builder.py:594-595`).
- KB entries are immune to the dedup-by-hash pass (`_dedup_notes_by_hash` skips empty `source_hash`; KB entries carry none) — no risk of mass-deletion on rebuild.

**Negative / risks:**
- Implements exactly what ADR-22 rejected: interleaved BM25 across corpora with different term statistics. 1,329 KB rows would dominate a 488-note corpus and shift IDF statistics for *every* consumer of `corp retrieve`/`corp prep`, not only RFP answering — using this mechanism as-is is an architectural decision by default, now made explicit and owned by this ADR instead of happening by accident.
- Frontmatter mapping is lossy: `notes` has no `category` column; KB titles are synthesized from `id`; question-variants/keywords (distiller output) are dropped. Style-store-relevant structure does not survive the merge.
- `trust_level: verified` over-claims for 97 KB files (network + wms strata, `docs/audits/2026-07-05-deep-rfp.md` §4.5) — these will rank as top-tier "verified" results despite failing a quality read.
- Per-entry staleness cannot ride file mtime (all 1,329 files share mtime 2026-03-15) — a `last_reviewed`/`valid_to`-based staleness gate remains separate, unbuilt work (RFP-14 in the deep-rfp backlog-seed table).
- On ratification, **ADR-22's status line must be updated to "Superseded by ADR-33."** That edit is a ratification-time action for the operator; this Proposed-status ADR does not perform it (CLAUDE.md §5 rule 3 — ADRs are immutable except the status-line ratification exception, ADR-94).

## Done-when

- With `INDEX_EXTRA_ROOTS` set to the `corp_data/rfp_kb` path and `corp index rebuild` run, verified (`trust_level: verified`) KB entries are observably returned by `corp retrieve --rfp-only` alongside vault notes — necessary condition: the KB row count in `notes` is greater than zero post-rebuild, and at least one KB-sourced note appears in a `--rfp-only` result for a query known to match KB content.
- The orphan `data/kb/canonical/*.json` path's disposition is tracked as a named, open decision owned by R1/FR-1 — not left silently dangling, and not silently wired into this federation.

## Alternatives considered

- **Option (a) — Federate at query time (ADR-22 as originally ratified):** new `rfp_entries` FTS5 table, `corp rfp-index` command, `--source vault|rfp|all` grouped display, no score interleaving. Sound in principle; unbuilt (**M** sizing: table + command + flag + display + prep injection). Rejected for this decision on cost grounds, not merit — remains a candidate for a later revisit (see Revisit trigger).
- **Option (b) — Merge KB into vault as notes:** directly contradicts ADR-22's "do not migrate" rule; requires a net-new ingest lane (none exists today); risks content overlap with the 39 existing extracted rfp_visible notes; concentrates all irreplaceable data (KB + vault) into a single store that, as of ADR-35, has no backup. Rejected as **L** effort with the highest blast radius.

## Revisit trigger

If the interleaved-BM25 risk materializes in practice (KB rows visibly dominating unrelated `corp retrieve`/`corp prep` results, or the 97-file network/wms over-claim surfacing above better vault content), revisit toward Option (a)'s isolated-table design.

## References

- `docs/audits/2026-07-05-deep-rfp.md` §Step 5, esp. Option (a′) (the built-but-dormant `INDEX_EXTRA_ROOTS` variant), §4.5 (per-stratum trust verdicts), Backlog-seed RFP-1/RFP-14
- Ground-truth D-7: `docs/audits/2026-07-16-architecture-ground-truth.md` §6 (orphan `data/kb/canonical/*.json`, no in-repo producer, `data/kb/` absent on disk)
- `docs/decisions/ADR-22-rfp-kb-federation.md` (superseded design; referenced, not edited)
- `docs/audits/2026-07-06-technical-architect-intake.md` §5 DR-1 row
