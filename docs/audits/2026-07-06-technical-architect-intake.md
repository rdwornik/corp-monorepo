# Technical Architect Intake — Functional Handover Entry Point

> **Consumed by:** ADR-33, ADR-34, ADR-35, ADR-36 (DR-2/10/11/12) + `docs/audits/2026-07-17-a3-target-architecture-ruling.md` → BACKLOG E5/E6 (FR-10–20). Fully consumed + superseded → archival candidate (S13 / #66).

> **Date:** 2026-07-06 · **Authored by:** functional architect (content) + Claude Code (path verification, evidence cross-references) · **Status:** ratified handover — this is the FIRST document the technical architect reads.
>
> All Reading-Map paths verified against `main` on 2026-07-06. Evidence pointers (`Evidence:` lines) were added by opening the cited audit files, not guessed. Anything not yet existing is marked `[pending]`.

## 0. How to use this document

You are the technical architect. Nothing described here is implemented unless marked WORKS. Your deliverables are: (a) ADRs for the decisions flagged `ADR-needed`, (b) a backlog derived from the functional requirements below plus the backlog-seed tables inside each deep audit. The path here was: big picture → evidence-based detail (12 audit deliverables) → back to big picture (this document). The operator (Rob, solo pre-sales engineer) and the functional architect have already answered every question they intend to answer; open items are explicitly listed in §7.

## 1. The system in one screen

Corporate OS automates a solo pre-sales engineer's workload at Blue Yonder EMEA. Two loops: a **deal loop** (Salesforce → Excel "main" → local deal home → production of RFP answers / decks / Q&A → manual outbound upload → Win/Loss archive) and a **knowledge loop** (SharePoint/Teams source terrain → scouted capture → routing → LLM extraction → Obsidian vault essence → indexed retrieval feeding BOTH productions), plus a **memory layer** (dual-destination backup, disk management). Empirical ground truth: the machinery was built and briefly used (March 2026), then froze; extraction works and is cheap (cents per project); the RFP process has never answered a real RFP end-to-end; the highest-value data (1,329-file answer KB) was unreachable by code until decision DR-1. Economics: ~3 RFPs/month, 30–40 deals/year, 2–5 manual days per RFP today.

## 2. Reading Map (verified by CC, 2026-07-06)

All paths repo-relative to `corp-monorepo` unless noted. Every `.md` listed below exists on `main`; `.html` companions exist where stated.

| Document | Path | What it answers |
|---|---|---|
| Phase-1 functional audit (5 files: telemetry, scenarios, process-inventory, artifact-lifecycle, synthesis) | `docs/audits/2026-07-05-functional-telemetry.md` · `-scenarios.md` · `-process-inventory.md` · `-artifact-lifecycle.md` · `-synthesis.md` | What exists vs what is used; verdict per process; laptop-loss analysis |
| Deep audit: RFP | `docs/audits/2026-07-05-deep-rfp.md` + `.html` | Two-stack reality, 9-stage parts inventory, KB quality, federation options, 14 backlog seeds |
| Deep audit: vault + metadata | `docs/audits/2026-07-05-deep-vault-metadata.md` + `.html` | Field-survival chain, S1 contract break, hygiene scope with appendix lists, operating-model rulings |
| Deep audit: magistrala/capture | `docs/audits/2026-07-05-deep-magistrala.md` + `.html` | Lane parity, config truth (registry/routing phantoms), 75-file inbox triage, restart gates |
| Deep audit: extraction | `docs/audits/2026-07-05-deep-extraction.md` + `.html` | Grounding gap, tier/cost truth, output→vault contract, kills evidence |
| Deep audit: deal loop | `docs/audits/2026-07-05-deep-dealloop.md` + `.html` | COM fix shape, Project_Codes contract, archive trigger inputs, missing SF/SP legs |
| Deep audit: MyWork estate | `docs/audits/2026-07-05-deep-mywork.md` + `.html` | Zone census, naming conformance ~1%, templates, workspace class |
| Estate recon | `docs/audits/2026-07-05-estate-recon.md` | Merge state, four-root snapshot, anomalies |
| As-is process map | `docs/audits/2026-07-06-process-map-asis.md` + `.html` | The ratified end-to-end flow with open markers [?] — **verified: persisted 2026-07-06** |
| Estate baseline | `docs/audits/2026-06-16-current-state-architecture-audit.md` (machine-readable companion: `...-audit-inventory.json`) | 1.1 TB OneDrive estate measurements |
| X1 backup proposal | `corp-ops` repo: `docs/audits/2026-07-05-x1-backup-proposal.md` *(corrected — sits under `docs/audits/`, not `docs/`)* | Dual-leg backup design, feasibility evidence, restore drill |
| May arrive (Wave 3) | workspace manifest (in the Warsaw workspace, outside repo) `[pending]` · scout pilot report `[pending]` · portfolio taxonomy `[pending]` | Live deck-factory inventory · SharePoint foraging economics · deal-weighted coverage gaps |

## 3. Functional requirements — processes

Format: goal · trigger · target flow · key rules. Each FR carries evidence pointers (added by CC) and maps to backlog seeds inside the corresponding deep audit.

**FR-1 · RFP answering (priority).** Goal: 2–5 manual days → hours, at ~3 RFPs/month, without style drift and without stale or cross-product facts. Trigger: client RFP (always Excel, sometimes Word). Target flow (9 stages): parse → classify (category × product × answer-policy) → coverage check (honest `[NEEDS INPUT]` when the product family is thin) → dual retrieval (truth: product-scoped ‖ style: product-agnostic) → reuse-vs-derive gate (rules-first: `source_hash` mismatch, `valid_to` expiry, category volatility — no ML day one) → compose (facts = content, precedent = form; length/formality knobs) → verify + abstain (claim→cite once grounding exists; forbidden_claims live at runtime) → operator review with accept/edit/reject captured (the system's first real feedback loop) → write-back + anonymize; approved answers enter the style store with fresh hashes. Ratified answer-policy matrix v1: security/compliance = stable + fully portable → REUSE; corporate = stable + portable → REUSE; integration/architecture = volatile + product-locked → DERIVE; functional capabilities = product-locked → DERIVE (precedent as form only); commercial/pricing = highly volatile → DERIVE or ABSTAIN; deployment/methodology = medium + partially portable → REUSE-with-verification. Pilot closure metric: next real RFP (prefer WMS/TMS) end-to-end; measure accept-without-edit %, honest abstains, zero cross-product fact leakage, hours vs baseline.
*Evidence:* `deep-rfp.md` §Step 1–2 (two disjoint stacks), §Step 3 (parts inventory vs the 9 target stages), §4.1–4.6 (KB corpus quality, staleness demonstration, style-store signals), §Step 6 (forbidden_claims/overrides seams, stage-7 capture point today), §Backlog-seed table (R1 inputs); `functional-scenarios.md` §1.1–1.3 (S1 nine-stage map); `functional-synthesis.md` §3 (THIN/RICH coverage map — policy-matrix seed); `functional-telemetry.md` §2.4 (RFP KB footprint, 1,329 files).

**FR-2 · Ad-hoc Q&A.** Goal: "someone brings me 10 questions, not in Excel" answered from the same knowledge with controllable length/tone, chatbot-experience. Same retrieval + compose stages as FR-1, conversational surface (see P1).
*Evidence:* `functional-process-inventory.md` §D2 (ad-hoc Q&A / discovery — as-built `corp retrieve`/`corp query`/`corp prep`/`corp chat` surfaces); `deep-rfp.md` §Step 1 (the `corp rfp answer` retrieval/compose stack FR-2 shares).

**FR-3 · Knowledge capture.** Goal: nothing valuable is lost, nothing worthless is hoarded. Two intakes: (a) **scout** — foraging over the SharePoint terrain: metadata-first survey, budgeted content peeks, value map, shortlist → operator GO → one-way copy-out to staging; source is read-only; economics reported (files touched vs total); (b) **inbox drop** — operator drops a file (or tells the system via P1), magistrala routes it: classify → rename (naming convention) → route → record-before-move. Standard lane = batch, hardened to parity (rename+dedup+quarantine). Hard gate before any restart: routing registry rewritten against real zones (dry-run match >80%). Active-deal materials and credential files are blacklisted from extraction.
*Evidence:* `deep-magistrala.md` §Step 1 (Lane A/B trace + parity table), §Step 2 (routing_map/content_registry phantom vs live, naming drift), §Step 3 (75-item inbox triage table), §Step 4 (dedup surfaces), §Step 5 (restart-readiness checklist); `functional-scenarios.md` §3 (S3 static trace + §3.4 sandboxed e2e run); `functional-process-inventory.md` §W1; `process-map-asis.md` (SCOUT flow + staging path). Scout pilot report `[pending: Wave 3]`.

**FR-4 · Extraction.** Goal: documents/video → structured facts, cheap (proven: cents). Required addition: per-fact **source-span grounding** (claim anchored to source snippet) — prerequisite for FR-1's claim→cite. Scoped on-demand runs for product gap-fill (coverage-map-driven), scheduled not remembered.
*Evidence:* `deep-extraction.md` §1.3 (grounding GAP confirmed), §Step 2 (tier routing + cost truth; §2.4 per-file cost), §Step 4 (output→vault EMIT contract), §5.3 (facts-pipeline kill evidence), §Step 6 (R2 gap-fill readiness; §6.2 cost basis, §6.3 what's missing to make it a mechanism); `functional-process-inventory.md` §W2.

**FR-5 · Knowledge organization (the essence layer).** Goal: the operator's drill-down map — industry (retail·manufacturing·3PL) × software (planning·execution·platform) → topic → notes. Mechanics: vault KEPT (DR-2) under the amended operating model: lifecycle S0→S3 as frontmatter (never location), generated MOC spine with static wikilinks (top-30 hubs cover 78% of dangling links), taxonomy canonicalized at the index-build seam, retrieval serves BOTH FR-1 and FR-7. Data-trust repair scope is quantified in the vault audit (S1 contract fix 0%→87% via two mechanical changes; mojibake; 258 clientless; 326 deprecated re-triage; 325 dedup-loser deletion with manifest).
*Evidence:* `deep-vault-metadata.md` §1.2 (field-survival table), §2.2 (S0–S3 mapping of the vault today), §2.3 (link-graph baseline — top-30 hubs), §3.1–3.5 (hygiene H1–H5, quantified: 258 clientless, 326 deprecated, mojibake pairs), §Step 4 (taxonomy canonicalization scope), §Step 5 (operating-model evaluation, element-by-element), §Backlog-seed table + Appendix A (affected-note lists incl. 325 dedup losers); `functional-process-inventory.md` §W5.

**FR-6 · Deal lifecycle.** Goal: from Salesforce assignment to archived deal with zero "where does this go" decisions. Reality-ratified model: SF is manual via the Project_Codes workbook (col E SF-URL = canonical key; col M folder links to backfill); deal home = local `10_Projects` as MASTER, team SharePoint as the collaboration mirror, outbound uploads MANUAL via OneDrive shortcuts (automation never writes to the synced tree); Win/Loss status (never timestamps) drives archiving — local trigger to build; cloud-side behavior is open item [?4]. COM is fixed by configuration (5 lines), owns `project-info.yaml`.
*Evidence:* `deep-dealloop.md` §1.2 (exact COM fix shape — `PROJECTS_ROOT` config), §Step 3 (Project_Codes de-facto contract, measured fill rates, stage vocabulary §3.3), §Step 4 (archive mechanics + status-driven trigger inputs §4.4; OneDrive constraint §4.5), §Step 5 (missing SF/SP legs, enumerated; want-level decision inputs §5.4); `functional-process-inventory.md` §D1, §D5; `functional-scenarios.md` §2 (S2 split-CLI reality).

**FR-7 · Deck production (deferred lane, design-ready).** Goal: branded, grounded, cited decks. The Warsaw workspace proves the behavior manually (5 customers, gated, cited); the target shares the grounded-content-manifest seam with FR-1 (one compose mechanism, three output channels: Excel/Word/PPT). Deliberately sequenced after FR-1.
*Evidence:* `deep-mywork.md` §1 (the real production studio lives in `30_Reference/Training/Warsaw`, not the declared hot zone); `deep-dealloop.md` §6.2 (template reality + deck-brief Q4 answer); `functional-process-inventory.md` §D4; `functional-scenarios.md` §2.3 (`com prep-deck`) + §4 (deck-brief Q1–Q5). Workspace manifest `[pending: Wave 3]`.

**FR-8 · Memory & backup.** Goal: nothing irreplaceable exists in one place; disk stays managed. X1: precious set (<100 MB: vault, answer KB, DBs, live config) → two legs: BY OneDrive via Graph upload-only (in-tenant; never the local synced folder; never delete) + Google Drive (corp-ops module); scheduled + heartbeat + restore drill as part of done. Extension: working MyWork (~10 GB deal documents) gets a delta backup leg via the same Graph upload-only pattern. Disk: regenerable artifacts (18.4 GB extraction outputs) are cleanup candidates; **nothing is ever deleted from MyWork** (operator carve-out).
*Evidence:* `corp-ops/docs/audits/2026-07-05-x1-backup-proposal.md` §1 (feasibility verdicts + spike evidence), §2 (measured precious set), §3 (mechanism: snapshot, Leg A Graph push-only, Leg B Google Drive, fail-loud alerting §3.5, restore test §3.6), §5 (operator prerequisites); `functional-artifact-lifecycle.md` §2.1 (disk budget — regenerable extraction outputs), §2.2 (OneDrive constraint map), §2.3 (laptop-loss thought experiment); `functional-process-inventory.md` §X1 (silent-failed backup task); `estate-recon.md` §Anomaly list #1 (vault unbacked: no remote, 259 uncommitted changes).

**FR-9 · Conversational front-door.** Goal: the operator talks to the system — "here's an Excel, route it" / "10 questions, shorter answers" / "status?". Interface = Claude Code initially; later a cheap-API or local model. This revives the existing `corp chat` + intent-router surface rather than building new.
*Evidence:* `deep-dealloop.md` §4.2 (`corp chat` → trigger phrases → `intent_router.py` → `workflows.yaml`, the working orchestration path); `functional-process-inventory.md` §D2 and §Discrepancy list item 2 (chat/intent/workflow orchestration layer discovered in code, absent from hypothesis).

## 4. Cross-cutting pillars (universal requirements — every process must satisfy them)

- **P1 · Conversational layer:** an LLM interface manages the whole flow; no memorized CLI incantations required of the operator.
- **P2 · Testability:** every process has an end-to-end test and runs in the existing sandbox pattern (proven 5/5) — the system tests itself. *(Evidence: `functional-scenarios.md` §3.4 — the sandboxed e2e run.)*
- **P3 · Revertability + change audit:** every create/update/delete is recorded and reversible (record-before-move, manifests-before-deletion, git); process dependencies are visible, not tribal.
- **P4 · Scheduled loops + heartbeat:** nothing depends on the operator remembering; absence-of-success is the alarm signal (evidence: the only surviving automation is scheduled; a silent-failed backup task rotted for 4 months — `functional-process-inventory.md` §X1).
- **P5 · Secrets hygiene as mechanism:** secrets never in files; an automated sweep in the scheduled conformance loop (evidence: four independent plaintext exposures found — `deep-mywork.md` §3 (`databricks.token` file, live PAT + OAuth client ids in `README.md`) + backlog item F-2, and `deep-magistrala.md` §Step 3 triage row 11 (`Credentials.xlsx` in the inbox)).

## 5. Decision register (ratified — supersedes the interim decision docket)

| ID | Decision | Outcome | ADR-needed | Evidence |
|----|----------|---------|------------|----------|
| DR-1 | RFP ↔ answer-KB access | Activate the built `INDEX_EXTRA_ROOTS` federation (tested, one env var); formally supersede ADR-22 | **YES** | `deep-rfp.md` §Step 5, esp. Option (a′) — the built-but-dormant `INDEX_EXTRA_ROOTS` variant |
| DR-2 | Vault fate | KEEP as the essence layer — conditional on the amended operating model (S0–S3 frontmatter, generated spine, scheduled promotion + heartbeat) | **YES** | `deep-vault-metadata.md` §Step 5 (operating-model evaluation), §2.2–2.3 (S0–S3 + link-graph baseline) |
| DR-3 | Deletions | Allowed: 325 vault dedup-losers (manifest-first) + dead code. Forbidden: anything in MyWork (196 twin pairs STAY). Tombstones archived via frontmatter, never deleted | no | `deep-vault-metadata.md` §2.1 + backlog item V3 + Appendix A (325 dedup losers); `deep-mywork.md` §2 (196 byte-identical twin pairs, ~756 MB) |
| DR-4 | Kills | facts pipeline (0 rows ever; repoint `corp query` to notes_fts) · Lane B `move_to_vault` (never completed a write) · N4 task manager (zero use) | no | `deep-extraction.md` §5.3 (facts kill-or-fix evidence); `deep-magistrala.md` §Step 1 Lane B; `deep-dealloop.md` §6.1 (N4 kill CONFIRMED) |
| DR-5 | Answer-layer uplift | Stop discarding `key_facts`/overlays at ingest — index them (they are FR-1 fuel) | no | `deep-extraction.md` §4.3 (EMIT field table); `deep-vault-metadata.md` §1.2 (field-survival table — where fields die) |
| DR-6 | W1 restart | Gated on registry v4 (>80% dry-run match); standard lane = batch with parity; inbox processed with active-deal + credentials blacklist; Rolls-Royce APS routed as FR-1 pilot seed, never extracted | no | `deep-magistrala.md` §2b (registry live-vs-phantom, 17/22 match), §Step 3 triage table row 1 (Rolls-Royce APS = R1 pilot seed, do NOT auto-extract), §Step 5 (restart gates) |
| DR-7 | Zones | `15_Extra_Inititives` → `15_Workspaces`; broader zone renames happen at the registry-v4 moment; final names = operator input (open) | no | `deep-mywork.md` §3 (`15_Extra_Inititives` disposition evidence), §6 (addressing-kernel inputs) |
| DR-8 | Deal-loop integrations | SF and SharePoint automation legs DEFERRED; workbook remains the manual SF interface; COM config fix + archive trigger proceed | no | `deep-dealloop.md` §Step 5 (§5.4 want-level decision inputs per leg), §1.2 (COM fix), §4.4 (trigger inputs) |
| DR-9 | Insurance actions (first implementation items) | Vault git commit (259 pending changes, no remote — highest-consequence risk) + X1 activation after two operator auth steps | no | `estate-recon.md` §Root D + §Anomaly list #1 (259 uncommitted, no remote, last commit 2026-03-26); `corp-ops/docs/audits/2026-07-05-x1-backup-proposal.md` §5 (the two operator prerequisites) |
| DR-10 | corp-ops placement | Stays a separate repo; gets a private remote | **YES** (topology) | `estate-recon.md` §Part 1 (corp-ops spike state) |
| DR-11 | Backup topology | Dual-leg (BY OneDrive Graph upload-only + Google Drive), scheduled + heartbeat, remotes never pruned, restore drill in done-contract; MyWork delta leg as extension | **YES** (with DR-10) | `corp-ops/docs/audits/2026-07-05-x1-backup-proposal.md` §3 (mechanism design incl. §3.5 fail-loud, §3.6 restore test), §4 (closure metric) |
| DR-12 | Storage topology | Dev = engine · MyWork = local master workbench · `MyWork_OneDrive` = navigation hub (Teams/SP shortcuts) + sharing surface (planned `Sharing_Files` folder) — NOT a code surface · wider SharePoint = read-only source terrain · vault = essence | **YES** | `estate-recon.md` §Part 2 (four-root reconnaissance); `deep-mywork.md` §1 (zone census), §5 (live-config vs repo-config split); `functional-artifact-lifecycle.md` §2.2 (OneDrive constraint map) |
| DR-13 | Answer-policy matrix v1 | Ratified as FR-1's classifier taxonomy (table in FR-1); refine after first pilot | folded into DR-1 ADR | `functional-synthesis.md` §3 (THIN/RICH coverage map — policy-matrix seed); `deep-rfp.md` §4.5 (per-stratum verdicts) |
| DR-14 | Process views/dashboards | Methodology undecided — the process map lives in `docs/audits/`, canonical files untouched | no (open) | `process-map-asis.md` (the artifact itself, persisted 2026-07-06) |

## 6. Operator ground truth (answers you cannot find in code)

Work happens locally in MyWork; the finished deliverable is uploaded MANUALLY via OneDrive shortcuts to the deal's Teams SharePoint — automation never writes into the synced tree. Submitted RFP responses live in local project folders (style-store seed). `MyWork_OneDrive` is actively used by the human as the SharePoint navigation hub even though code never touches it. The operator's zone-naming pain is real (only `10_Projects` is intuitive); rename input pending. Deletion carve-out: MyWork is untouchable. Cost posture: LLM budget is not a constraint; operator attention is.

## 7. Open items (the complete list — nothing else is pending from us)

[?4] Win/Loss behavior on the SharePoint side (nothing/move/tag) · final zone names (operator) · Wave-3 results (workspace manifest, scout pilot, portfolio taxonomy) may arrive and enrich FR-3/FR-7 and the coverage map · process-map file — **verified persisted** (`docs/audits/2026-07-06-process-map-asis.md`), no longer pending.

## 8. Suggested derivation order (dependency, not calendar)

F0 substrate (DR-9 insurance → vault data-trust repair per FR-5 scope → registry v4 + zone renames) → R1 = FR-1 build (sequence inside the RFP audit's seed table; score-inversion fix first) → R2 = coverage gap-fill loop (FR-4) → deal loop (FR-6) → deck lane (FR-7). Write the four ADRs (DR-1, DR-2, DR-10/11, DR-12) before the backlog — they anchor everything. Every backlog item inherits the operator's rule: **a necessary condition ("done when"), testable, per item — no exceptions.**

## 9. Addenda — FR-10…FR-19 (FA campaign 2026-07-07/08)

> **Why this exists.** §3 above defines FR-1…FR-9 only. The FA (functional-architecture) campaign of 2026-07-07/08 added **ten more functional requirements — FR-10…FR-19 — across five architect briefs** in `docs/audits/`. Until now they were invisible from this canonical entry point (the FA-campaign self-review §5-4/§7 flagged this as "the single highest-leverage fix… one addenda pointer"). This section is that pointer: it does **not** restate the briefs — it routes to them. Each brief's own `## 6. FR-addendum candidates` is the source of the scope; each brief's `## 7. Success criteria (brief-level)` is the done-when. **No renumbering has been applied** (see note [3]).

| FR | Scope (one line, from the brief's §6) | Owning brief (`docs/audits/`) | Done-when pointer |
|----|----------------------------------------|-------------------------------|-------------------|
| FR-10 | Golden-URL registry — record contract (§3.1), one-source-N-views generation (§3.2), schema validation as the enforcement seam | `2026-07-07_BRIEF_golden-url-registry-knowledge-flow.md` | that brief §7 |
| FR-11 | Scout foraging loop — probe/forage/queue/promote cycle (§3.3) under P4 heartbeat; registry as sole target list; ratification-gated growth | `2026-07-07_BRIEF_golden-url-registry-knowledge-flow.md` | that brief §7 (amended by adopt-map §6: bandit-governed queue) |
| FR-12 | Unified estate lifecycle — S0–S3 phase field spanning files and notes (§3.4); amends DR-2 upward to the whole estate | `2026-07-07_BRIEF_golden-url-registry-knowledge-flow.md` | that brief §7 |
| FR-13 | Telemetry spine — §5 schema + emit points; the data prerequisite for the entire learning roadmap | `2026-07-07_BRIEF_algorithmic-adopt-map.md` | that brief §5 inline "Done when:" + §7 — **but see note [1]** |
| FR-14 | Terrain-learning pipeline — §4 sample→extract→dedup→cluster→reconcile contract, three data paths | `2026-07-07_BRIEF_algorithmic-adopt-map.md` | that brief §7 (amended by ontology §6: Claims-with-provenance) |
| FR-15 | Prep-view contract — Client-MOC dossier template + ROOT cockpit composition (§3.3), consuming FR-10 (registry dims) + FR-13 (reuse telemetry) | `2026-07-07_BRIEF_obsidian-operating-model-v2.md` | that brief §7 |
| FR-16 | Synthesis production rule — triggers + quality bar (§3.6), consuming FR-13/FR-14 outputs | `2026-07-07_BRIEF_obsidian-operating-model-v2.md` | that brief §7 |
| FR-17 | Ontology charter — object/link/action tables (§3.1–3.3) + shared-property contract as a versioned, validator-enforced docs contract | `2026-07-07_BRIEF_ontology-north-star.md` | that brief §7 |
| FR-18 | Metadata charter — field-set classes (§3.2) + tri-axial tag taxonomy (§3.3/3.4) + vocabulary allowlists as versioned, validator-enforced contracts | `2026-07-08_BRIEF_metadata-charter-T1.md` | that brief §7 |
| FR-19 | Deterministic auto-tagger — rules 1–10 (§3.5) as the ingest-time tagging seam (couples to FR-14 pipeline + DR-6 W1 restart) | `2026-07-08_BRIEF_metadata-charter-T1.md` | that brief §7 |

**Notes:**

[1] **FR-13 carries a semantic conflict, now resolved.** The adopt-map brief (owner) defines `event_type` as an *open* activity vocabulary; the ontology brief (§6) amends it to a *closed* four-value kinetic enum. These are incompatible definitions of the same field — the FA-campaign self-review §4-1/§7's only per-FR blocker. The ratified reconciliation (two-level `event_class × event_type`) is recorded in **`2026-07-17-fr13-event-schema-reconciliation.md`**; read it alongside FR-13, not the two briefs in isolation.

[2] **obsidian-v2 §6 mislabel.** That brief's §6 amendment line reads "Amendment to FR/DR-2 (vault operating model)". This should read **FR-5 / DR-2** — FR-2 is *Ad-hoc Q&A* (§3 above); the vault operating model is **FR-5**. The correction is recorded here so the amendment is not mis-attributed; the brief itself is left unedited (immutability).

[3] **No FR-number collisions.** Each new number FR-10…FR-19 is claimed as "new" by exactly one owning brief; the overlaps visible above (FR-10, FR-11, FR-13, FR-14, FR-17) are labeled "Amendment to…" cross-references, **not** competing ownership claims. The self-review audited only FR-10…17; FR-18/FR-19 were added later by `2026-07-08_BRIEF_metadata-charter-T1.md`, so the true current range is **FR-10…FR-19 (ten FRs)**.
