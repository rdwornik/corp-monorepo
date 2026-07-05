# Functional Audit — Synthesis for the Architect (Phase 5)

**Date:** 2026-07-05 · **Branch:** `docs/2026-07-05-functional-audit` · **HEAD at audit start:** `fb9b2dd`
**Deliverables in this audit** (one commit each, in order):
1. `docs/audits/2026-07-05-functional-telemetry.md` (`c03b53d`)
2. `docs/audits/2026-07-05-functional-scenarios.md` (`d0f16ba`)
3. `docs/audits/2026-07-05-functional-process-inventory.md` (`b8f9bf1`)
4. `docs/audits/2026-07-05-functional-artifact-lifecycle.md` (`e3aae05`)
5. this file

Read-only discipline held: all DB access `mode=ro`; no OneDrive path touched or traversed; the single execution was the gate-checked sandbox smoke test (isolation proven, cleanup verified).

---

## 1. Verdict table

Assessments are **inputs** to keep/fix/kill/merge decisions reserved for operator + architect.

| ID | Process | Status | One-line evidence | Assessment (input) |
|----|---------|--------|-------------------|--------------------|
| D1 | Opportunity intake | EXISTS-UNTESTED (SF+SharePoint legs MISSING) | 0/29 real project folders have `_knowledge/`; `PROJECTS_ROOT` unset → `./test_projects` | Fix-and-point-at-reality is one config line; the SF/SP legs are new builds — decide if they're wanted at all |
| D2 | Ad-hoc Q&A | DORMANT | Real use 2026-03-26 (JOURNAL "useful output"); index frozen 2026-03-28 | Cheapest revival: refresh index; value gated on W1/W2 restart |
| D3 | RFP answering | EXISTS-UNTESTED + PHANTOM federation | `data/output/`+`data/kb/` never created; ADR-22 "ratified, not built"; RFP KB unreachable by any code path | The priority build target; treat existing stacks as parts inventory, not a working process |
| D4 | Deck production | MISSING (stub only) | `com prep-deck` = `shutil.copy2` of one template; real decks hand-built (newest 2026-07-03) | Honest greenfield; only template-copy plumbing exists |
| D5 | Close-out / archive | EXISTS-UNTESTED (mechanism) + MISSING (trigger) | `90_Archive` empty forever; Stage col read but never consumed; keyword-chat trigger only | Mechanism is salvageable; status-driven trigger + xlsm reconciliation are new work |
| W1 | Capture | DORMANT | Last real ingest 2026-03-27; inbox inflow stopped 2026-04-10; 75 files waiting | Machinery works (sandbox-proven); the stall is operational, not technical |
| W2 | Extract & organize | DORMANT (ALIVE-in-sandbox) | 2,673 notes ingested Mar 26-27, none since; sandbox e2e 5/5 on 2026-07-05; engine still extracts (`output/test` through 06-16) | Restartable at cost of an index rebuild + inbox run; facts pipeline (0 rows ever) is a separate dead limb |
| W3 | Personal enablement | ALIVE (manual) / system-DORMANT | `30_Reference/Training` newest file 2026-07-05; nothing extracted since March | KB lags Rob's real knowledge by 3+ months — the freshest material never enters the system |
| W4 | Publish to team | MISSING | No Graph/SharePoint write code; guards forbid the naive path | Requires a Graph client that doesn't exist; decide want-level first |
| W5 | Company map / taxonomy | DORMANT | Taxonomy curated through March; `notes.products` shows uncanonicalized term leakage | Needed as R1 substrate (product scoping depends on canonical families) |
| X1 | Backup | MISSING (confirmed) | Vault git has **no remote**; rfp_kb + ops.db + .corp unbacked; <100 MB of irreplaceable data | Highest consequence-to-effort ratio in the estate |
| N1 | MyWork hygiene (discovered) | DORMANT | reshape_plan.md 2026-03-13; strongest safety code in repo | Supporting process; revive only in service of W1 |
| N2 | Analytics (discovered) | DORMANT | Built+demoed 2026-03-28 on now-frozen index | Plumbing over W2 |
| N3 | Integrity/freshness (discovered) | EXISTS-UNTESTED | The drift it detects (source_inaccessible notes) is present and unremediated | Would earn its keep in F0 |
| N4 | Task mgmt (discovered) | EXISTS-UNTESTED | No use evidence | Kill-candidate input |
| N5 | Nightly conformance (discovered) | ALIVE | Digests merging through 2026-06-27 (#34) | The only living automation — proves scheduled loops work on this estate |

## 2. Top-10 functional findings (ranked by impact on an RFP-first roadmap: F0 → R1 → R2)

1. **The system has answered zero real RFPs; the "RFP process" is two disjoint part-bins, not a pipeline.** Stack A (`corp rfp answer`) is console Q&A; Stack B (Excel/Word agents) writes documents but isn't CLI-registered, reads only index.db, and its output dir has never existed. → *So-what:* R1 is an integration+completion job around salvageable parts (parsers, write-back, anonymizer), not a from-scratch build — but nothing can be assumed "working" from docs. *Evidence:* scenarios §1.1; `data/output/` absent.
2. **The single highest-value data asset — the 1,329-file RFP KB — is orphaned: no code can reach it.** ADR-22 federation was ratified 2026-03-28 and never built; the ChromaDB fallback points at a directory that doesn't exist; retrieval sees only the 182 `rfp_visible` vault notes. → *So-what:* R1's first architectural decision is where the KB lives (federate vs merge into vault); until then the "knowledge-grounded" promise is 12% real. *Evidence:* scenarios §1.3; telemetry §2.4.
3. **Of the 9 target RFP stages, 4 have no implementation at all on the answering path** (coverage check, dual truth/style retrieval, reuse-vs-derive staleness gate, verify+abstain), and the guardrails that look like they exist — product profiles, `forbidden_claims`, overrides.yaml — **gate nothing at runtime**. → *So-what:* the architect's stage 2/3/4/6 designs are greenfield; do not budget them as "wire-up". *Evidence:* scenarios §1.2 table.
4. **The knowledge loop is dormant, not broken — the freeze is operational.** Sandbox e2e passes 5/5 with post-Council-#24 paths; the CKE engine demonstrably extracted as late as 2026-06-16 (test harness); ingest last ran for real 2026-03-27 and inbox inflow stopped 2026-04-10. → *So-what:* F0 restart is cheap (process the 75-file backlog, rebuild index); no repair project needed before R1. *Evidence:* scenarios §3.4; telemetry §1.2, §2.1.
5. **Trust substrate has decayed while frozen:** the March folder restructure orphaned note→source links (`trust_level: deprecated`, `rebuild_status: source_inaccessible` in sampled notes), 258/488 indexed notes have an empty client, and mojibake duplicates (Würth/WÃ¼rth, Żabka/Å»abka) split client-scoped retrieval. → *So-what:* F0 needs a data-hygiene pass or R1's claim→cite verification stands on rotten provenance. *Evidence:* scenarios Q2; telemetry §1.3.
6. **X1 is confirmed missing and brutally concrete: everything the system exists to accumulate fits in <100 MB and has zero off-machine copies** (vault git has no remote; rfp_kb, ops.db, MyWork/.corp unbacked) — while 18.4 GB of regenerable extraction artifacts sit on the limited disk. → *So-what:* F0 item #1 by consequence/effort; also the audit's clearest quick win. *Evidence:* lifecycle §2.3, §2.1.
7. **Empirical coverage confirms the Planning-rich / everything-else-thin hypothesis with numbers** (see §3): Planning is 67% of the KB corpus and dominates the vault; WMS/TMS have documents but almost no presentations; Workforce/Network/OMS/Commerce/CatMan are THIN-to-ABSENT. → *So-what:* the R2 gap-fill loop has its seed matrix; honest abstention for thin families is mandatory day-one behavior. *Evidence:* telemetry §1.4, §2.4.
8. **The deal loop's only alive-capable fragment (`com new`) is mispointed and unused, and every integration leg is missing:** PROJECTS_ROOT defaults to CWD-relative `./test_projects`; Salesforce = one YAML comment; SharePoint = an unused `msal` extra plus guards that forbid writing to the synced tree; Win/Loss is display-only. → *So-what:* D1/D5 automation is further from reality than the hypothesis assumed; sequence it after R1 unless the operator disagrees. *Evidence:* scenarios §2.
9. **Every "learn from use" surface has zero rows ever** — `routing_feedback`, `registry_suggestions`, `content_signatures`, `facts`, `extractions` — i.e., all feedback/learning machinery is shelf-ware. → *So-what:* the target stage-7 review capture would be the *first* real feedback loop; design it against the evidence that passive capture mechanisms here don't get used. *Evidence:* telemetry §1.2.
10. **Authoritative-looking dead config actively misleads:** `routing_map.yaml` (all targets phantom, reader uncalled), the `02_sources/` invariant naming a zone that never existed on disk, 3 phantom `40_Media` registry destinations, stale `30_Templates/90_System` labels, missing `platform_matrix.json`. → *So-what:* F0 should include a config-truth pass so the architect's backlog isn't derived from phantom authority; this audit's inventory (Phase 3 §c) is the checklist. *Evidence:* scenarios §3.2; process inventory discrepancies.

## 3. Empirical coverage map — THIN/RICH verdicts (policy-matrix seed)

Combining vault notes (488, telemetry §1.4) and RFP KB files (1,329, telemetry §2.4):

| Product family | Vault notes | RFP KB files | Verdict | Note |
|---|---|---|---|---|
| Platform / Azure / integration | 231 + 127 | (cross-cutting) | **RICH** | strongest family; matches "integration questions volatile" priority |
| Demand Planning | 185 | planning: 894 (all planning) | **RICH** | |
| Supply Planning | 101 | ↑ shared | **RICH** | |
| Control Tower | 43 | control_tower: 0 | MIXED | vault-only; KB family empty |
| WMS | 66 | 34 | **THIN-for-RFP** | document-heavy, presentation-thin (9); KB minimal |
| TMS / Logistics | 54 | logistics: 121 | MIXED | KB logistics decent, vault presentation-thin (5) |
| Network Design | 10 | network: 63 | THIN (vault) | KB partially compensates |
| AI/ML | (in platform terms) | aiml: 43 | MIXED | |
| Workforce Mgmt | 12 | 0 | **THIN** | |
| OMS | 9 | 0 | **THIN** | |
| Commerce | 4 | 0 | **THIN** | |
| CatMan / Retail planning (AR/MFP/demand-edge) / SCP-sequencing / IBP / PPS | 0 | 0 (8 empty dirs) | **ABSENT** | honest `[NEEDS INPUT]` territory |

Caveat: `notes.products` terms are uncanonicalized (telemetry §1.4) — counts are term-frequency, not validated family assignments; W5 canonicalization tightens this map.

## 4. Open questions for the operator (evidence could not settle)

1. **RFP KB provenance:** all 1,329 files carry mtime 2026-03-15 and 174 sit in `_staging/`. Is this corpus curated gold (build R1 on it) or an unreviewed draft dump (rebuild it)? Nothing in repo telemetry records how it was produced.
2. **Past-answer style corpus:** the target stage-3/8 "style store" needs seed material. Are submitted RFP responses (e.g. the Rolls-Royce APS response in 00_Inbox, plus whatever is on SharePoint) the intended seed, and who marks submitted-vs-draft?
3. **Was the deal-loop tooling (`com`, Project_Codes integration) consciously abandoned, or stalled by the `PROJECTS_ROOT` misconfiguration?** Determines fix-vs-kill for D1.
4. **Is `corp-ops/sync-mywork.ps1` actually scheduled and running?** (Outside this repo's telemetry.) Determines how much of MyWork is cloud-recoverable — the laptop-loss table assumed cloud-originated files are.
5. **W1 lane choice:** batch `corp ingest` skips rename and dedup entirely; interactive `ingest-inbox` does both but takes operator time. Which is the intended standard for the restart, and should batch gain rename/dedup parity?
6. **The 75-file inbox backlog (newest 2026-04-10):** process, triage, or declare stale?
7. **`15_Extra_Inititives`** (63 files, active May) is outside the 7 canonical zones and invisible to routing — legitimate new zone or misfiling?

---

*Audit complete. Branch `docs/2026-07-05-functional-audit`, 5 deliverable commits, unmerged — handed back for architect review.*
