# HANDOFF — Functional Architect (Corporate OS)

**Date:** 2026-07-07 · **From:** closing browser session (process consolidation + audit waves) · **To:** fresh functional-architect chat (Fable)
**Companion file:** `2026-07-07_BRAINSTORM-BACKLOG_functional-requirements.md` — the unexhausted topics the new session will work.

---

## 1. Role & operating contract (binding, learned the hard way this session)

- You are the **functional architect**: understand processes → consolidate → design functionally → document (audits, ADR inputs, functional requirements) → hand to the **technical architect**, who derives ADRs + backlog and implements. **You implement nothing.** CC executes; you review CC's output — never treat it as authoritative.
- **Every decision and every step gets a testable necessary condition — "Done when: …" — no exceptions.** Operator's core rule; a step without its condition verified is not done.
- **No timeline words** (today/tomorrow/first thing). Sequence by dependency only; the operator decides when.
- **Low cognitive load for the operator:** human language, one question at a time, decisions made in your lane with his veto — he is a peer, not a menu of 17 switches (that mistake was made and corrected this session).
- Chat in Polish; all artifacts/prompts/docs in English. Prompts = downloadable `.md`, self-contained.
- Hard invariants: never write/delete/traverse-with-hydration under `OneDrive - Blue Yonder`; **nothing is ever deleted from MyWork**; deletions elsewhere need explicit sign-off + manifest-first; feature branches, independently revertable commits; no new folders without approval.

## 2. What the closing session accomplished (the arc)

Hypothesis process map (deal loop D1–D5, knowledge loop W1–W5, backup X1) → **Phase-1 functional audit** (measured USE, not capability: system frozen since late March; only scheduled automation alive) → **Wave 2: six parallel deep audits** (RFP, vault+metadata, magistrala, extraction, deal loop, MyWork estate; worktree-isolated, read-only, evidence to file:line) → estate recon + merge closure → **as-is process map ratified with the operator** (his corrections: retrieval feeds BOTH RFP and deck production; MyWork_OneDrive = navigation hub, not dead copy) → **decision docket → ratified decision register (14 DR)** → **handover package designed**: technical-architect intake (9 FRs, pillars P1–P5, reading map) + code-quality audit — both delivered as prompts.

Headline findings the new session must hold: zero real RFPs ever answered; the 1,329-file answer KB was code-unreachable (fix decided: `INDEX_EXTRA_ROOTS` federation + ADR superseding ADR-22); guardrails (`forbidden_claims`) were dead YAML; effective RFP corpus = 39 notes of 488 indexed; one template bug fails 100% of notes against their own contract (two mechanical fixes → 87%); vault has no git remote (highest-consequence risk); the system's seams are broken while 2,588 tests stay green — **contracts-at-seams are first-class citizens in all target design**; only scheduled loops survive, and scheduled-without-heartbeat rots silently (a backup task failed quietly for 4 months).

## 3. System in one screen

Solo pre-sales engineer (Blue Yonder EMEA). **Deal loop:** Salesforce → Project_Codes.xlsm "main" (col E = SF-URL key) → local `MyWork/10_Projects` as MASTER + team-SharePoint mirror → production (RFP Excel/Word, decks, Q&A) → deliverable uploaded MANUALLY via OneDrive shortcuts → Win/Loss status archives (trigger missing). **Knowledge loop:** SharePoint terrain (1.1 TB chaos) →(scout, designed)→ inbox (frozen, 75 files) → magistrala (works in sandbox 5/5; restart gated on registry v4) → CKE extraction (works, cents) → vault (850 disk/488 indexed/39 usable) → FTS5 retrieval → feeds BOTH productions. **Memory:** X1 dual backup (BY OneDrive Graph upload-only + Google Drive) feasibility proven, blocked on 2 operator auth steps. Economics: ~3 RFPs/month, 30–40 deals/year, 2–5 manual days per RFP.

## 4. Ratified decisions (compressed; the intake document is canonical if merged)

DR-1 KB federation via `INDEX_EXTRA_ROOTS` + supersede ADR-22 (**ADR needed**) · DR-2 vault KEPT under amended operating model — scheduled loops + spine + S0–S3 frontmatter (**ADR needed**) · DR-3 deletions: 325 vault dedup-losers OK manifest-first; MyWork untouchable · DR-4 kills: facts pipeline, Lane B, N4 task-manager · DR-5 stop discarding key_facts/overlays at ingest · DR-6 W1 restart: registry-v4 gate, batch lane with parity, active-deal + credentials blacklist · DR-7 `15_Extra_Inititives`→`15_Workspaces`; zone renames at v4 time, names = operator input pending · DR-8 SF/SP legs deferred, workbook stays the manual interface; COM fixed by config · DR-9 insurance first: vault commit + X1 · DR-10 corp-ops separate + private remote (**ADR**) · DR-11 backup topology (**ADR**, with DR-10) · DR-12 storage topology: Dev=engine, MyWork=local master, MyWork_OneDrive=hub+sharing, SharePoint=read-only terrain, vault=essence (**ADR**) · DR-13 answer-policy matrix v1 ratified · DR-14 views/dashboards methodology undecided — process artifacts live in `docs/audits/`, canon untouched.

## 5. Repo navigation (corp-monorepo, `docs/audits/` is the evidence library)

Entry point: `2026-07-06-technical-architect-intake.md` **[verify it exists — see §6]**. Then: `2026-07-05-functional-{telemetry,scenarios,process-inventory,artifact-lifecycle,synthesis}.md` (Phase 1) · `2026-07-05-deep-{rfp,vault-metadata,magistrala,extraction,dealloop,mywork}.md` + `.html` (Wave 2; each ends with a backlog-seed table) · `*estate-recon*.md` · `*process-map-asis*` (may be pending) · `2026-06-16-current-state-architecture-audit.md` (estate baseline). In `corp-ops`: `docs/2026-07-05-x1-backup-proposal.md`. Off-repo, operator-held: `DECISION_DOCKET.md` (superseded by the intake's register) + the June architect briefs (re-uploaded to the new chat as needed: file-management foundation + converged, extension advisory, rfp-agent brief, deck-production merged, obsidian operating model, extractor research brainstorm).

## 6. STEP 0 for the new chat — verify state, assume nothing

Execution status of the final prompts is **unknown** to the closing session. Before any work, have CC report: (1) does `docs/audits/2026-07-06-technical-architect-intake.md` exist on main? (2) does the code-quality audit exist (`*code-quality-audit*`)? (3) does the process map exist (`*process-map-asis*`)? (4) Wave-3 results: workspace manifest (in the Warsaw workspace, outside repo), scout pilot report, portfolio taxonomy — which ran? (5) vault: committed? remote? (6) X1: auth steps done, build started? (7) `git log --oneline -15` on main. Anything missing = its delivered prompt is still in the operator's Downloads, re-runnable as-is.

## 7. Honest gaps & black boxes (disclosed by the closing session on request)

1. **Deep-audit full texts:** the closing session read Wave-2 results via CC session-summaries (several garbled in console paste), NOT the full 12 deliverables. Appendix lists (258 clientless, 326 deprecated), full backlog-seed tables and ALL `.html` maps were never read by Layer-1. The new chat should read the full audits it works against.
2. **Never read at all:** `2026-07-05-functional-scenarios.md` and `2026-07-05-functional-process-inventory.md` (Phase 1) — known only via the synthesis.
3. **Truncated reads:** the 2026-06-21 extractor brainstorm (middle section — decision matrices A–D — missing) and `WORKSPACE_MASTER_REFERENCE.md` (first ~80 of ~274 lines).
4. **`demo-prep` repo: never examined this session.** The operator's deck-generation pipeline repo (CC-bootstrapped, branding ingest, canonical section library per his prior work) was outside all audits; the intake's deck lane (FR-7) leans on the Warsaw workspace evidence only and may underrepresent demo-prep. High-priority gap — see backlog T6.
5. **No repo access at Layer-1, ever:** all code claims are CC-mediated evidence; the closing session never saw source directly.
6. **Unconfirmed executions** (§6) and one open map question: [?4] Win/Loss behavior on the SharePoint side.
7. Context clearing: early tool results (old-chat searches, some file views) were dropped mid-session; their conclusions survive in the artifacts, raw content does not.

## 8. Operator ground truth + pillars

Ground truth: local-first work; manual outbound uploads; OneDrive = shortcuts hub + sharing (planned `Sharing_Files` folder); working MyWork wants a backup leg (Graph upload-only, never the synced tree); zone names hard to navigate (only `10_Projects` intuitive); LLM budget unconstrained, operator attention is the scarce resource; four credential exposures found → rotations are operator-only actions.
Pillars (every design must satisfy): **P1** conversational LLM front-door (CC first, cheap/local model later) · **P2** testability — e2e test + sandbox per process · **P3** revertability + change audit + visible dependencies · **P4** scheduled loops + heartbeat (absence-of-success alarms) · **P5** secrets hygiene as mechanism.

## 9. Mission of the next session

(1) STEP 0 state verification. (2) Work the brainstorm backlog (companion file) — one topic per sitting, each producing an architect brief in the June-brief format, ending with FR-addendum candidates + done-when criteria. (3) Fold accepted briefs into the intake as addenda (audit-space, not canon). (4) Keep the handover contract: the technical architect must be able to derive ADRs + backlog without asking us anything.
