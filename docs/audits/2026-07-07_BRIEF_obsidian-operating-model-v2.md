# Obsidian Operating Model v2 — Second Brain as Pre-Sales Cockpit (T3)

> **Consumed by:** ADR-34 (vault essence layer — v2 amendment incorporated by reference) + `docs/audits/2026-07-06-technical-architect-intake.md` → BACKLOG #41, #42 (FR-15/16).

**Repo:** corp-monorepo / ObsidianVault · **Audience:** functional intake / technical architect
**Status:** brainstorm-phase blueprint (audit-space per DR-14) · **Date:** 2026-07-07 · **Session:** functional-architect sitting #3
**Supersedes-in-part:** June operating-model brief (S0–S3, MOC spine) — v2 folds in the deep-vault audit's AMEND rulings and adds the creative layer the operator asked for. The consolidation closure metric is UNCHANGED.

---

## 1. Problem

v1 gave the vault a lifecycle (S0–S3) and a navigation spine (ROOT → MOCs). The audit then measured it against reality and returned AMEND: the MOCs are dataview-only and therefore **link-blind** (invisible to backlinks, orphan checks, and the graph — the tree existed only as query output, not as edges); the 48h S0 SLA had no enforcement mechanism; the spine was to be hand-authored although 78% of it is derivable from the top-30 dangling-link hubs; and contract reconciliation is an unmet prerequisite. Separately, the operator's dissatisfaction stands: v1 made the vault *organized*, not *useful* — it never answered what a pre-sales engineer actually sees before a client meeting, when synthesis happens, or how rot is detected without ceremony.

## 2. Evidence

**Audit rulings (internal, docs/audits/2026-07-05-deep-vault-metadata):** spine generatable from top-30 dangling-link hubs at 78% coverage · MOCs dataview-only → link-blind · 48h SLA works only with scheduled enforcement · contract reconciliation prerequisite · effective corpus 39/488 notes usable.

**Research pass (2026-07, sources §8):** Obsidian **Bases** is now a core plugin — database views (table/cards/list/map) over frontmatter properties, saved as `.base` files, embeddable in any note via `![[File.base#View]]`, with formulas for computed columns and view-level filters. Decisive properties for us: (a) **in-place editing writes back to the note's frontmatter** (a dashboard doubles as a metadata-repair surface); (b) **fast at 20k-note scale**, far beyond our 850; (c) **`this` in an embedded base refers to the host note** — one template base renders a different dossier in every client note; (d) the official CLI's `base:query` works on `.base` FILES (not inline blocks) — dashboards become machine-readable for CC and Python; (e) the kepano obsidian-skills set includes a dedicated Bases-authoring skill, so CC can build and maintain dashboards natively. Direction of travel in the ecosystem: Dataview migrates to Bases for view-type use cases; converters exist.

## 3. Converged recommendation

### 3.1 Two-layer architecture — the fix for link-blindness (core v2 correction)

**Rule: links carry structure; Bases carry sight. Never the reverse.**

- **LINK layer** — every tree edge (ROOT→domain MOC→topic MOC→note ownership) is a **static wikilink**, generated inside sentinel markers. This makes the tree visible to backlinks, `orphans`/`unresolved`/`deadends` CLI audits, and the graph — restoring exactly what dataview-only MOCs destroyed. The navigability invariants (S2 ≤3 hops from ROOT, 0 orphans, one owning MOC) are checkable again because they exist as *edges*.
- **VIEW layer** — every dashboard, list, and browsing surface is an embedded `.base` view. Views are regenerable decoration; deleting every base loses zero structure.
**Done when:** the CLI orphan/unresolved audit runs green against the link layer alone, with all `.base` files temporarily removed as the test.

### 3.2 Spine bootstrap — generated proposal, ratified by the operator

Generate ROOT + domain-MOC skeletons from the top-30 dangling-link hubs (78% coverage per audit); the operator ratifies/renames domains in one sitting; the residual 22% is backfilled per domain slice. Same propose→ratify pattern as the golden-URL registry — no hand-authoring from a blank page, no silent self-organization.
**Done when:** ratified spine committed; every hub in the top-30 resolves to exactly one owning MOC.

### 3.3 The prep-view — what the ROOT actually shows a pre-sales engineer

ROOT = 5-line hand-authored orientation + embedded base views, in this order of prominence:

1. **Next-meeting dossier** — the flagship. A `Client-MOC` template with an embedded base filtered on `client == this.file.name`: the client's S2 notes, open-deal note, last-touched decks/answers (from reuse telemetry), and golden-URL registry entries matching the client's industry dims. One template, N clients, zero per-client maintenance — this is what "second brain" means for this job: *walk into the meeting already briefed by your own past work*.
2. **Health strip** — per-phase counts (S0/S1/S2), S0 items older than 24h (amber) / 48h (red), orphan count, unresolved count.
3. **Rot queue** (§3.5) and **promotion-run report link** (latest).
**Done when:** the dossier renders correctly for one real client with ≥5 S2 notes, and the operator confirms it beats his current pre-meeting routine.

### 3.4 Enforcement, not presence — the 48h SLA and the scheduled loops

The SLA exists only as a **scheduled sweeper** (P4: scheduled + heartbeat): daily-ish promotion run (S0→S1→S2 per v1 §2, unchanged), flagging/tombstoning S0 >48h; weekly CLI audit run (orphans/unresolved/reachability) where violations are defects with owners. Absence-of-success alarms per the heartbeat pattern — a sweeper that silently stops IS the failure mode that killed the last backup.
**Done when:** the sweeper's heartbeat file updates on schedule for a full cycle, and one forced miss raises the alarm.

### 3.5 Rot scoring — the cheapest honest signal is already specified elsewhere

No new infrastructure: the telemetry spine (adopt-map brief, FR-13) already logs retrieval-result-use per note. **Rot = S2 note with 0 retrieval-uses AND 0 new backlinks over N cycles** → surfaces in a monthly PRUNE-review base view. Usage is the only honest rot signal; age alone is prejudice, and any richer signal costs more than the decision it informs.
**Done when:** after one month of ambient telemetry, the rot view yields its first candidate list and the operator PRUNE-reviews it (tombstone or re-link).

### 3.6 Synthesis production — three triggers, one quality bar

Synthesis notes (the output tier) are produced when any trigger fires, never on inspiration:
- **T-cluster:** ≥N S2 notes share an induced topic (BERTopic reconciliation table, adopt-map §4) with no synthesis note owning the cluster.
- **T-co-retrieval:** telemetry shows the same note-set repeatedly co-retrieved for answers — the system is already synthesizing ad hoc; make it a note.
- **T-retro:** deal closes (win/loss) → retro run mines the deal's answers/decks into candidate syntheses.
**Quality bar (hard):** ≥2 cited sources · states a claim, not a list · exactly one owning MOC · passes frontmatter contract. Fails the bar → stays a draft in S1.
**Done when:** each trigger has fired at least once and produced a bar-passing synthesis note.

### 3.7 Vault ↔ style stores — WHAT vs HOW

The vault stores **WHAT** (citable essence, one truth store per DR-2/DR-12). Style stores per output lane (RFP answers, deck sections in demo-prep) store **HOW** (voice, layout, structure precedents). The Content Manifest (T6) is the bridge that pairs a WHAT with a lane's HOW. The vault never stores formatting precedents; style stores never store facts without a vault citation. The "one precedent store, two views" question stays open pending the demo-prep recon (T6).

### 3.8 Prerequisite gate (unchanged from audit)

Contract reconciliation (the template bug failing 100% of notes against their own contract; two mechanical fixes → 87%) precedes any backfill. No promotion runs against a broken validator — enforcement against a wrong contract is worse than none.

## 4. Open decisions

D1 Domain names for the spine (operator input at ratification, ties to DR-7 zone-naming) · D2 N for rot cycles and synthesis-cluster threshold (start N=2 cycles / 4 notes; tune from first reports) · D3 whether Client-MOC dossiers live under 02_Navigate or a new class (new folder needs approval) · D4 Dataview retirement pace — migrate view-type queries to Bases opportunistically vs. one sweep (recommend opportunistic; converter exists).

## 5. NOT-list

- No structure in Bases/Dataview — views are sight, links are bone (§3.1 rule is absolute).
- No hand-authored MOC link sections outside sentinels (v1 rule, kept).
- No new rot infrastructure — FR-13 events only.
- No inline base code blocks for real dashboards — `.base` files only (CLI `base:query` can't see inline blocks; inline = throwaway note-local views only).
- No graph-view dependence — the graph becomes readable as a side effect and stays an observation layer.
- No whole-vault promotion passes — domain slices with quarantine (v1 rule, kept).

## 6. FR-addendum candidates

- **Amendment to FR/DR-2 (vault operating model):** two-layer link/view architecture (§3.1) + spine bootstrap from hub analysis (§3.2) + scheduled-sweeper enforcement (§3.4) replace v1's corresponding sections.
- **FR-15 (new): Prep-view contract** — the Client-MOC dossier template + ROOT cockpit composition (§3.3), consuming FR-10 (registry dims) and FR-13 (reuse telemetry).
- **FR-16 (new): Synthesis production rule** — triggers + quality bar (§3.6), consuming FR-13/FR-14 outputs.

## 7. Success criteria (brief-level)

Consolidation closure metric UNCHANGED from v1: 100% of S2 reachable from ROOT in ≤3 hops · 0 orphans / 0 unresolved among S2 · S0 max-age ≤48h · baseline-vs-final inventory archived. v2 adds: §3.1 link-layer-only audit green · one real-client prep-view accepted by the operator · rot queue live from real telemetry · three synthesis triggers each proven once.

## 8. Sources (research pass)

- Bases core plugin, views, embedding, `.base` files: help.obsidian.md (Introduction to Bases, Views, Create a base); got.md Bases guide (2026-03).
- In-place editing writes back to frontmatter, 20k-note performance, `base:query` on `.base` files only, embedded-`this` context: dsebastien.net (2026); blog.optional.page Bases tips (2025-11).
- Dataview→Bases migration direction + converter: effortlessacademic.com (2026-03); kevsrobots.com.
- CC authoring path: kepano/obsidian-skills — obsidian-bases SKILL (schema, filters, formulas, views).
- Internal: deep-vault-metadata audit rulings; June operating-model brief; adopt-map brief (FR-13/FR-14).
