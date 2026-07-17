# ADR-34: Vault kept as the essence layer under the amended operating model

- **Status:** Proposed
- **Date:** 2026-07-17
- **Decision tier:** Technical-architect intake triage (Path A), 2026-07-06 decision register DR-2
- **Related:** `docs/audits/2026-07-07_BRIEF_obsidian-operating-model-v2.md` (the v2 amendment this ADR incorporates by reference)
- **Intake:** `docs/audits/2026-07-06-technical-architect-intake.md`, DR-2
- **Decommission:** none — the dataview-only MOCs (`02_Navigate/`) are amended (gain static wikilinks), not removed; no file is deleted by this ADR.
- **Source:** 2026-07-06 technical-architect intake decision register (ratified); evidence in `docs/audits/2026-07-05-deep-vault-metadata.md` §Step 5 and `docs/audits/2026-07-07_BRIEF_obsidian-operating-model-v2.md`

## Context

The vault (`ObsidianVault/`, 848 files, 813 notes in `01_Knowledge/`) is the system's single essence/"WHAT" layer for pre-sales knowledge. An earlier operating-model brief (v1) proposed an S0→S3 frontmatter lifecycle plus a ROOT→domain-MOC→topic-MOC navigation spine. The 2026-07-05 deep vault audit measured v1 against the actual vault and returned AMEND on 3 of its 5 elements (`docs/audits/2026-07-05-deep-vault-metadata.md` §Step 5):

- **Link-blindness (element 1):** the flat-folder half of v1 holds (813/848 notes sit in one flat `01_Knowledge/` zone), but the link-tree half is 0% built: **813/813 (100%) of notes are orphans**, 0 notes are MOC-reachable, and all 9 `02_Navigate` MOCs are dataview queries (`FROM "01_Knowledge" ... GROUP BY product`) that render as navigation in the Obsidian app but contribute **zero edges** to the link graph — invisible to backlinks, to any orphan/unresolved CLI audit, and to the graph view (§2.3). Feasibility is good: 8,262 dangling wikilink instances exist across 787 distinct targets, and the top-30 targets alone cover 6,417 of them (78%) — the future spine's node list is already named by data that exists today.
- **48h S0 SLA with no enforcement mechanism (element 2):** the S1 contract as written fails 813/813 notes (0%) because the extraction template renames `source_file`→`source`, contradicting the Pydantic model it was validated against seconds earlier; two mechanical fixes raise this to 87%, a full enum-mapping table to ~99% (§2.2). An age-based SLA with no running mechanism is, per the audit, "a dead rule on arrival" — capture has been dormant since 2026-03-27.
- **Hand-authored spine (element 5):** the brief's spine was to be manually authored; the audit found 78% of it is already derivable mechanically from the dangling-link data, and that a dedup-loser/S3-tombstone triage pass must precede any backfill — the real backfill universe is ~487 notes, not 850, once 325 dedup-losers and 326 de-facto S3 tombstones are subtracted.

A follow-on brief (v2, `docs/audits/2026-07-07_BRIEF_obsidian-operating-model-v2.md`) resolves the link-blindness AMEND with a two-layer architecture, incorporating Obsidian's now-core **Bases** plugin (database views over frontmatter, embeddable, in-place editing writes back to frontmatter).

## Decision

**Keep the vault** as the system's single essence/"WHAT" layer (DR-2), conditional on adopting the amended operating model in full:

1. **S0→S3 frontmatter lifecycle** (shape unchanged from v1): S0 RAW (<48h) → S1 STRUCTURED (passes the — now-repaired — frontmatter contract) → S2 CONSOLIDATED (linked, 0 unresolved, owned by exactly one MOC) → S3 ARCHIVED (tombstoned, never deleted). Prerequisite: contract reconciliation (the `source_file`/`source` rename mismatch + an enum-mapping table for `type`/`source_type`/`quality`) must land before any promotion job runs — enforcement against a broken validator is worse than none.
2. **A generated navigation spine, not hand-authored:** ROOT + domain-MOC skeletons are *generated* from the top-30 dangling-link hubs (78% coverage), then the operator ratifies/renames domains in one sitting; the residual 22% backfills per domain slice (obsidian-v2 brief §3.2).
3. **Two-layer LINK/VIEW architecture** (the v2 brief's core correction, incorporated by reference): **"links carry structure; Bases carry sight — never the reverse."**
   - **LINK layer:** every tree edge (ROOT→domain MOC→topic MOC→note ownership) is a **static wikilink**, generated inside sentinel markers — visible to backlinks, to `orphans`/`unresolved`/`deadends` CLI audits, and to the graph.
   - **VIEW layer:** every dashboard/browsing surface is an embedded `.base` view (Obsidian Bases core plugin) — regenerable decoration; deleting every `.base` file loses zero structure.
4. **Scheduled promotion + heartbeat, not aspiration:** a daily-ish promotion sweep (S0→S1→S2, flagging/tombstoning S0 >48h) and a weekly link-integrity audit (orphans/unresolved/reachability), each with an absence-of-success heartbeat — a sweeper that silently stops is exactly the failure mode that let the estate's last backup rot for 4 months undetected (obsidian-v2 brief §3.4).

## Consequences

**Positive:**
- Resolves the audit's AMEND verdicts with evidence-driven fixes rather than re-authoring the brief from scratch: the spine's node list is already 78%-named by real dangling-link data, and the two-layer split makes the tree checkable by tooling that was previously blind to it (dataview MOCs contributed 0 edges).
- `index.db` is explicitly named as a derived cache in the model (audit §5 "must-address" list) — rebuild becomes a mandatory post-step of every lifecycle transition, closing the gap where S3-equivalent notes (326 de-facto tombstones) leak into `rfp_visible=1` (143 of 182 rows) and are saved only by a downstream retrieve-time filter.
- Obsidian 1.12.4 and the `Obsidian.com` CLI are already present on this machine (feasibility EXISTS-UNTESTED, not EXISTS-MISSING) — the mechanical layer this decision depends on does not need to be procured.

**Negative / risks:**
- The CLI link-integrity audits (orphans/unresolved/deadends) do not see dataview relationships — until the LINK-layer amendment lands, they under-report navigability exactly as measured today (100% orphan rate). This is a known, accepted gap during the transition, not a new one.
- Real backfill universe is **not** 850 notes — it is ~487 (850 minus 325 dedup-losers minus 326 tombstones minus 22 quarantine, per the audit's own accounting) — undercounting this risks the "81% of effort spent on tombstones" trap the audit flags for the clientless-backfill work specifically.
- `deprecated` — the trust_level carried by 40% of the vault and the single most load-bearing value in the S0-S3/`rfp_visible` interaction — is not in `schema.yaml`'s allowed values today; the schema must be extended for S3 to be non-fictional.
- Dataview→Bases is explicitly NOT a big-bang migration (obsidian-v2 brief §5 NOT-list); opportunistic, domain-sliced execution means the two systems coexist for an unspecified transition period.

## Done-when

- The CLI orphan/unresolved audit runs **green against the link layer alone**, with all `.base` files temporarily removed as the test (obsidian-v2 brief §3.1 — the decisive proof that structure lives in links, not views).
- The ratified spine is committed with **every one of the top-30 dangling-link hubs resolving to exactly one owning MOC** (obsidian-v2 brief §3.2).
- The scheduled sweeper's heartbeat file updates on schedule for **one full cycle**, and a forced miss demonstrably raises the alarm (obsidian-v2 brief §3.4).

## Alternatives considered

- **Kill the vault, rebuild elsewhere:** not evaluated as a live alternative in the intake — the vault's content (813 notes, 6 load-bearing fields already flowing to the answer layer) was not in question, only its operating model. Not pursued.
- **v1 operating model as originally briefed** (hand-authored spine, dataview-only MOCs, aspirational 48h SLA): superseded in substance by the audit's AMEND findings and the v2 brief before this ADR was drafted; retained here only as the "what changed" baseline in Context.

## References

- `docs/audits/2026-07-05-deep-vault-metadata.md` §Step 5 (operating-model evaluation, element-by-element) and §2.2–2.3 (S0–S3 mapping + link-graph baseline)
- `docs/audits/2026-07-07_BRIEF_obsidian-operating-model-v2.md` §3.1 (two-layer LINK/VIEW architecture), §3.2 (spine bootstrap), §3.4 (enforcement — scheduled sweeper + heartbeat)
- `docs/audits/2026-07-06-technical-architect-intake.md` §5 DR-2 row
