# Self-Reflect Audit — Functional-Architect Campaign 2026-07-07

> **Date:** 2026-07-08 · **Author:** Claude Code (P10, read-only) · **Subject:** the 2026-07-07 functional-architect campaign (spillover 07-08 P9 included) · **Contract:** zero repo writes; sole output is this file (DR-14 audit-space discipline — Downloads, not canon).
> **Read scope (exhaustive):** corp-monorepo `@main` `02a1b59`; `~/.claude/logs/onedrive-guard.log`; `Downloads/2026-07-0{7,8}_*` names+metadata; the four briefs; the intake; the handoff + brainstorm-backlog; `core-invariants.md`. **Out of scope (not verified):** `.dev-knowledge`, ObsidianVault, `demo-prep` repo internals, any `OneDrive - Blue Yonder` file CONTENT (T0 name-listing only).
> **Precondition (P9 settled):** `git status` clean · `origin/main..main` empty · both at `02a1b59`. P9 complete.

---

## Executive summary (one screen)

- **§1 Plan-vs-achieved:** the campaign shipped **4 of 7** planned briefs (T2/T3/T4/T5 = **DONE**, on main); **T1 metadata charter, the T6 integration brief, and the pre-mortem are PENDING** (no artifact exists anywhere in scope); **T6 recon is DONE but orphaned in Downloads**. Prompt fleet: **P6, P9, guard-ruling = DONE**; **P2/P5/P8-escalation not identifiable in read scope** (browser architect holds the fleet).
- **§4 Cross-brief consistency:** FR numbering **FR-10…FR-17 is unique, contiguous, zero collisions** ✅. **Two real inconsistencies** found: (a) FR-13 `event_type` is defined **two incompatible ways** (adopt-map activity-list vs ontology kinetic-4 enum); (b) obsidian-v2 mislabels the vault amendment as **"FR/DR-2"** when the vault process is FR-5/DR-2 (FR-2 is Ad-hoc Q&A). Plus one low-severity S2 vantage difference.
- **§7 Handover-readiness:** **NOT-READY-CLEAN.** FR-1…9 (intake) + the four briefs are individually strong and derivable, but **three gaps force questions**: (1) the FR-13 `event_type` conflict; (2) **the intake — the technical architect's declared FIRST document — never references FR-10…17** (the briefs were not folded in as addenda; handoff §9 mission item 3 unmet), so the eight new FRs are undiscoverable from the entry point; (3) three PENDING objectives leave named holes (the metadata charter the operator called *"kluczowe"* is one of them).

---

## §1 · Plan vs achieved

**Plan reconstructed from** `Downloads/2026-07-07_HANDOFF_functional-architect.md` §9 (mission) + `Downloads/2026-07-07_BRAINSTORM-BACKLOG_functional-requirements.md` (T1–T6 contract) + JOURNAL sitting-numbers.

Mission (handoff §9): (1) STEP-0 state verification · (2) work backlog T1–T6, one topic/sitting → an architect brief in June-brief format ending with FR-addendum candidates + done-when · (3) **fold accepted briefs into the intake as addenda** · (4) keep the handover contract (technical architect derives ADRs+backlog without asking).

### Topic verdicts

| Objective | Expected output (brainstorm-backlog) | Artifact of record | Verdict |
|---|---|---|---|
| **T1 · Metadata & tagging** (operator: *"kluczowe"*) | metadata charter brief (canonical field set + tag-governance rule + enforcement seam) | **none found** (Downloads + main searched) | **PENDING** |
| **T2 · Ontology north star** | ontology-north-star brief | `docs/audits/2026-07-07_BRIEF_ontology-north-star.md` (on main, sitting #4) | **DONE** |
| **T3 · Obsidian v2** | operating-model v2 brief | `docs/audits/2026-07-07_BRIEF_obsidian-operating-model-v2.md` (on main, sitting #3) | **DONE** |
| **T4 · Golden-URL registry** | registry contract + verifier brief | `docs/audits/2026-07-07_BRIEF_golden-url-registry-knowledge-flow.md` (on main, sitting #1) | **DONE** |
| **T5 · OSS/local-model leverage** | adopt-map brief | `docs/audits/2026-07-07_BRIEF_algorithmic-adopt-map.md` (on main, sitting #2) | **DONE** |
| **T6 · Cross-repo integration** | **demo-prep recon report + integration brief** | recon: `Downloads/2026-07-07_AUDIT_demo-prep-recon.md` (21:20, **orphan**); integration brief: **none** | **PARTIAL** (recon done, self-declares "the last black box *before* the integration brief" — `demo-prep-recon.md:4`; brief pending) |
| **Pre-mortem** | (named as an objective in P10 §1) | **none found** | **PENDING** |

**Sitting order worked:** T4→T5→T3→T2 (sittings #1→#4 per each brief's header line 5). The operator sequenced by pick, not calendar (brainstorm-backlog:4). T1 (first in the list, *kluczowe*) was **not reached**; T6-brief and pre-mortem not reached.

### Mission-item verdicts

| Mission item | Verdict | Evidence |
|---|---|---|
| (1) STEP-0 state verification | **DONE** (implicitly) | briefs cite verified main paths; intake §2 "verified by CC 2026-07-06" |
| (2) briefs in June-brief format | **DONE for 4/7** | §3 quality matrix below |
| (3) **fold accepted briefs into intake as addenda** | **NOT DONE** | `Grep FR-1[0-7]|addend` in intake → **No matches**; the four briefs are standalone in `docs/audits/`, unreferenced by the intake |
| (4) keep handover contract | **PARTIAL** | see §7 — three gaps force questions |

### Prompt fleet

| Prompt | Verdict | Evidence |
|---|---|---|
| **P6** (ingest-briefs worktree) | **DONE** | JOURNAL `[worktree]` entry (L533-539); briefs T2+T3 committed `7f243a0`/`63fe813`, merged to main in P9 `f0a848d` |
| **P9** (great cleanup) | **DONE** | this session; merge `f0a848d` + JOURNAL merge `02a1b59`; seven closure checks pass |
| **P10** (this audit) | **IN PROGRESS** | this file |
| **Guard ruling** (block-onedrive v3) | **DONE** | `core-invariants.md` §1 (v3, 2026-07-08, T0/T1/T2 tiers); guard log = 44 lines, all `T0-ALLOW`, name-only enumeration working |
| **P2 / P5 / P8-escalation** | **NOT IDENTIFIABLE in read scope** | no artifact in corp-monorepo/guard-log/Downloads names maps uniquely to these; the demo-prep recon is plausibly one prompt's output. **Deferred to browser architect** (holds the prompt fleet). Not graded rather than falsely graded. |

---

## §2 · Full artifact inventory

**Legend:** HOME = intended destination per DR-14 (process artifacts → `docs/audits/`) / handoff §5 (control docs → operator-held) / DK prefix → `.dev-knowledge`. **ORPHAN** = produced but never reached its HOME ("dead in Downloads").

| Artifact | Location now | Commit | HOME | NEXT STEP | Flag |
|---|---|---|---|---|---|
| `2026-07-07_BRIEF_golden-url-registry-knowledge-flow.md` | main `docs/audits/` **+** Downloads | `38cb00b` | docs/audits/ | fold into intake as addendum | ✅ homed |
| `2026-07-07_BRIEF_algorithmic-adopt-map.md` | main `docs/audits/` **+** Downloads | `38cb00b` | docs/audits/ | fold into intake | ✅ homed |
| `2026-07-07_BRIEF_obsidian-operating-model-v2.md` | main `docs/audits/` **+** Downloads | `7f243a0`→`f0a848d` | docs/audits/ | fold into intake | ✅ homed |
| `2026-07-07_BRIEF_ontology-north-star.md` | main `docs/audits/` **+** Downloads | `63fe813`→`f0a848d` | docs/audits/ | fold into intake | ✅ homed |
| `2026-07-07_AUDIT_demo-prep-recon.md` | **Downloads only** | — | docs/audits/ (DR-14) *vs* self-declared Downloads (`:10-15`) | pin to docs/audits/ **or** operator ruling | ⚠️ **ORPHAN** + governance ambiguity |
| `2026-07-07_EVIDENCE_by-product-docs-tree-analysis.md` | **Downloads only** (23:54) | — | docs/audits/ | pin or rule operator-held | ⚠️ **ORPHAN** |
| `2026-07-07_DK-EXTRACT_prompt-standards.md` | **Downloads only** (18:55, 45 KB) | — | `.dev-knowledge` (DK prefix) | verify landed in hub (out of scope) | ⚠️ **ORPHAN (unverified home)** |
| `2026-07-07_HANDOFF_functional-architect.md` | Downloads (15:42) | — | operator-held (handoff §5) | keep; it + companion are the ONLY record of the T1–T6 plan | 🟡 by-design off-repo |
| `2026-07-07_BRAINSTORM-BACKLOG_functional-requirements.md` | Downloads (15:42) | — | operator-held | keep; sole FR-addendum tracking source | 🟡 by-design off-repo |
| P9 JOURNAL/merge chain | main | `f0a848d`, `8aae428`, `02a1b59` | repo | — | ✅ homed |

**Orphan headline:** 3 true orphans (`demo-prep-recon`, `by-product-docs-tree`, `DK-EXTRACT`). The two 15:42 control docs are the campaign's only durable plan record and live only in Downloads — **single point of loss** for the T1–T6 contract and the FR-addendum ledger.

---

## §3 · Brief-quality matrix (June-brief contract)

Contract cells (handoff §9 / brainstorm-backlog:4): **Problem · Evidence · Converged recommendation · Open decisions · Success criteria · NOT-list · FR-addendum candidates · Done-when per recommendation.**

| Brief | Problem | Evidence | Conv. rec | Open dec | Success | NOT-list | FR-add | Done-when/rec |
|---|---|---|---|---|---|---|---|---|
| **golden-url (T4)** | ✅ §1 | ✅ §2+§9 | ✅ §3.1-3.5 | ✅ §4 (D1-D5) | ✅ §7 | ✅ §5 | ✅ §6 | ✅ §3.1/3.2/3.3/3.4 each carry Done-when |
| **adopt-map (T5)** | ✅ §1 | 🟡 §2/§8 (embedded, no standalone "Evidence" head) | ✅ §2-§5 | ❌ **no "Open decisions" section** | ✅ §7 | ✅ §2.8 | ✅ §6 | 🟡 §3/§4/§5 Done-when present; §2.1-2.7 use **triggers**, not done-whens |
| **obsidian-v2 (T3)** | ✅ §1 | ✅ §2+§8 | ✅ §3.1-3.8 | ✅ §4 (D1-D4) | ✅ §7 | ✅ §5 | ✅ §6 | ✅ §3.1-3.6 each carry Done-when |
| **ontology (T2)** | ✅ §1 | ✅ §2+§8 | ✅ §3.1-3.5 | ✅ §4 (D1-D3) | ✅ §7 | ✅ §5 | ✅ §6 | 🟡 only §3.5 Done-when; §3.1-3.4 rely on the "Consuming FR (existence test)" column (`ontology:23`) |

**Cell-level misses (file:line):**
- **adopt-map — missing Open-decisions cell.** `2026-07-07_BRIEF_algorithmic-adopt-map.md` runs §5 (telemetry) → §6 (FR-addendum) → §7 (success) with **no "Open decisions" heading**. Deferrals are expressed as per-component *triggers* (e.g. §2.5 line 49, §2.6 line 53) but the discrete contract cell is absent. **Real miss.**
- **adopt-map — done-when granularity.** The map components §2.1–§2.7 carry NOT-lines + triggers, not done-whens; done-whens live only at §3 (line 68), §4 (line 79), §5 (line 85). Contract said "done-when per recommendation." **Partial.**
- **ontology — done-when granularity.** Only §3.5 (line 56) has an explicit Done-when; §3.1–§3.4 substitute the "existence test" column (`:23`). Defensible but not literal contract compliance. **Partial.**
- **golden-url & obsidian-v2 — full compliance.** All eight cells present with per-recommendation done-whens. **Strongest two.**

Overall: no brief is unfit; adopt-map is the weakest on the contract (one missing cell + soft done-whens), obsidian-v2 and golden-url are the reference-grade pair.

---

## §4 · Cross-brief consistency

### FR numbering — FR-10…FR-17

| FR | Brief | Type |
|---|---|---|
| FR-10 Golden-URL registry | golden-url §6 | new |
| FR-11 Scout foraging loop | golden-url §6 (amended by adopt-map §6) | new |
| FR-12 Unified estate lifecycle (S0–S3) | golden-url §6 | new |
| FR-13 Telemetry spine | adopt-map §6 (amended by ontology §6) | new |
| FR-14 Terrain-learning pipeline | adopt-map §6 (amended by ontology §6) | new |
| FR-15 Prep-view contract | obsidian-v2 §6 | new |
| FR-16 Synthesis production rule | obsidian-v2 §6 | new |
| FR-17 Ontology charter | ontology §6 | new |

**Verdict: unique, contiguous, zero collisions** ✅ — and disjoint from the intake's FR-1…FR-9. Amendment cross-refs resolve: adopt-map amends FR-11 (= golden-url's scout ✅), FR-5-class ingest (intake FR-5 ✅); obsidian consumes FR-10+FR-13 ✅; ontology amends FR-13+FR-14 ✅ and its §3.1 object→consuming-FR table (FR-15/10/13/14/7) all resolve ✅.

### Inconsistencies (both sides cited)

1. **FR-13 `event_type` defined two incompatible ways — MEDIUM.**
   - **adopt-map §5** (`algorithmic-adopt-map.md:84`): FR-13 event types = an **activity list** — *"retrieval queries + results + which result was used; scout cycle reports; CKE extraction scores; registry liveness transitions; RFP/deck content-reuse events."*
   - **ontology §3.3 + §6** (`ontology-north-star.md:46-48`, `:73`): FR-13 `event_type` enum = the **kinetic-4** (`ratify`, `prune`, `reuse`, `transition`), asserting *"FR-13 was already designed to log exactly these"* (`:48`).
   - **Conflict:** only `reuse` and `transition`(≈liveness transition) overlap. `retrieval`, `extraction-score`, `scout-cycle` are **not** kinetic actions; `ratify`, `prune` are **not** in adopt-map's list. The ontology brief's "already designed to log exactly these" is an **overreach** — the two enums are not the same set. A technical architect building the FR-13 schema must pick one taxonomy or merge them. **This is the §7 FR-13 blocker.**

2. **obsidian-v2 mislabels the vault amendment as "FR/DR-2" — LOW/MEDIUM.**
   - **obsidian-v2 §6** (`obsidian-operating-model-v2.md:85`): *"Amendment to **FR/DR-2** (vault operating model)."*
   - In the intake, the vault operating model is **FR-5** (knowledge organization, `intake:50`) governed by **DR-2** (vault fate, `intake:78`). **FR-2** is *Ad-hoc Q&A* (`intake:41`). The token "FR/DR-2" read as "FR-2" points to the wrong requirement. Should read **"FR-5 / DR-2."**

3. **S2 vantage difference — LOW (not a defect).**
   - golden-url §3.4 (`:70`) frames S2 ESSENCE Document-centrically (*"a vault note cites it — Note→cites→Document"*); obsidian-v2 frames S2 as the note itself (§3.3, §7). Same state machine, two vantage points — internally consistent, worth one reconciling sentence when folded into canon.

**Positive consistency:** the `dims` (industry × software) property is uniform across all four (golden-url §3.1:39, adopt-map §3:68, obsidian §3.3:38, ontology §3.1:33); S0–S3 is shared vocabulary; the ontology's kinetic-verbs unification is elegant **once the §4-item-1 enum conflict is resolved**.

---

## §5 · Process self-critique (evidence-cited — 6 findings)

1. **`--no-verify` — one authorized instance, caveat fully recorded (CLOSED).**
   *Evidence:* JOURNAL L527-531 (golden-url/adopt-map entry). Operator-authorized; the entry records the full root cause (12 orphaned `python -mpre_commit hook-impl` procs — named `python.exe` not `pre-commit.exe`, so name-kills missed them — holding the store lock) and asserts "no real gate skipped" (all hooks skip `.md` by their `files:` patterns). *Cost:* content commit `38cb00b` bypassed hooks. *Recommendation (already validated):* orphan-drain/fresh-terminal — the P6 `[worktree]` session (JOURNAL L535) and P9 (`f0a848d` ran the full hook set clean) both confirm the hang did **not** recur. Well-handled; leave as a gotcha candidate.

2. **Console-paste garbling + partial reads at Layer-1.**
   *Evidence:* `HANDOFF_functional-architect.md:41` — *"read Wave-2 results via CC session-summaries (several garbled in console paste), NOT the full 12 deliverables"*; `:42` (two Phase-1 audits never read); `:43` (truncated reads). *Cost:* some campaign conclusions rest on garbled/partial source. *Recommendation:* briefs should read the full audits they cite — obsidian-v2 §2 (`:15`) does cite the deep-vault audit directly (partial mitigation); the others lean on prior-evidence pointers.

3. **Orphans — "dead in Downloads."**
   *Evidence:* `git ls-tree main` shows `demo-prep-recon`, `by-product-docs-tree`, `DK-EXTRACT` **not on main** (§2). *Cost:* the T6 recon evidence and the OneDrive tree-analysis are **absent from the evidence library the technical architect reads** (`docs/audits/`). *Recommendation:* pin to `docs/audits/` (P9-style branch→merge) or record an operator-held ruling. Note the governance ambiguity: the recon self-declares Downloads-home (`demo-prep-recon.md:10-15`) which conflicts with DR-14's `docs/audits/` rule — resolve it explicitly.

4. **Addenda never folded into the intake (mission item 3 unmet).**
   *Evidence:* `Grep FR-1[0-7]|addend|pre-mortem|metadata charter` in `intake` → **No matches**; handoff §9(3) required folding accepted briefs in as addenda. *Cost:* the intake (declared "the FIRST document the technical architect reads", `intake:3`) omits FR-10…17 entirely. *Recommendation:* add an "Addenda (FR-10…17)" pointer section to the intake, or ship a one-page brief-manifest. **This is also the §7 headline gap.**

5. **Worktree discipline — strong, one inert residue.**
   *Evidence (positive):* P6 `[worktree]` correctly **anticipated** the JOURNAL append-conflict and resolved-by-stacking (JOURNAL L536); disjoint `.md` adds → no content collision (P9 merge-tree confirmed only JOURNAL conflicted); the `state.yaml` seed step was declared **MOOT, documented not fabricated** (L538) — honest. *Residue:* P9 found an empty **gitignored** `.claude/worktrees/cm-deep-vault` leftover (unrelated deep-vault worktree; not a registered git worktree). *Cost:* negligible. *Recommendation:* `rmdir` on operator ruling (no-delete invariant → not auto-removed).

6. **Guard escalation loop — resolved to a working name-only capability.**
   *Evidence:* `core-invariants.md` §1 (guard **v3**, 2026-07-08; T0-ALLOW / T1-grant-gated-EMPTY / T2-never tiers); guard log = **44 lines, all `T0-ALLOW`** (name/metadata enumeration of the OneDrive product-docs tree works; **all content reads blocked by construction — T1 grant list empty**). The `by-product-docs-tree` evidence file was built from these T0 enumerations (log 23:33-23:47 ↔ file mtime 23:54). *Cost:* any future brief needing OneDrive **content** (not just names) is blocked. *Recommendation:* if content reads become necessary, a **hub ruling** must add a T1 grant (per `core-invariants.md` §6 — global-infra edits are ruling-gated, `.dev-knowledge` BACKLOG #289).

*(Search trail: I looked for `--no-verify` misuse, unrecorded caveats, silent truncation, collision/seeding failures, and guard evasion. The `--no-verify` instance was authorized+recorded; no unrecorded caveat or guard evasion found. 6 findings stand; none are fabricated-positive.)*

---

## §6 · Open-items register (with owners)

### Operator-only
- **Graph consent** (AADSTS65002) — one interactive consent unblocks **both** the scout (FR-11) and X1's upload leg (FR-8); golden-url §3.5 (`:79`).
- **Google Drive re-auth** — X1 Leg B (corp-ops).
- **Vault git remote** — DR-9, *"highest-consequence risk"* (`intake:85`; estate-recon anomaly #1: 259 uncommitted, no remote).
- **Wave-3 re-runs** — workspace manifest, scout pilot, portfolio taxonomy (`intake:32`, §7).
- **Credential rotations** — 4 plaintext exposures (`intake:71`, P5).
- **cm-deep-vault** empty dir removal (P9 PROPOSED).
- **Ruling** on the 3 Downloads orphans (§2): pin vs operator-held.

### Technical-architect phase
- **Write 4 ADRs before backlog:** DR-1, DR-2, DR-10/11, DR-12 (`intake:102`).
- **Derive ADRs + backlog from FR-10…17** — *after* the FR-13 `event_type` conflict (§4-1) is resolved.
- **P4/FR-14** terrain-pipeline build; **ENV-HEAL / heartbeat** watch (P4).
- **Guard grant-projection** re-raise — `.dev-knowledge` BACKLOG #289 (`core-invariants.md` §6).
- **F0 substrate order** (`intake:102`): insurance → vault repair → registry v4.

### Browser-architect lane
- **T1 metadata charter brief** — PENDING (operator: *kluczowe*).
- **T6 integration brief** — PENDING (recon done).
- **Pre-mortem** — PENDING.
- **Fold the four briefs into the intake as addenda** — mission item 3, not done (§5-4).
- **Reconcile FR-13 `event_type`** across adopt-map ↔ ontology (§4-1) before handover.

---

## §7 · Handover-readiness verdict (per-FR)

**Contract (handoff §9(4), intake §0):** *the technical architect derives ADRs + backlog without asking us anything.* Verdict per FR against that bar.

| FR | Readiness | Gap that would force a question |
|---|---|---|
| **FR-1…FR-9** (intake) | ✅ **READY** | ratified, evidence-pointered, done-whens; the pre-existing handover. No change. |
| **FR-10** Registry | 🟡 READY-with-ratification | D1 registry-home path needs operator sign-off (no new folders) — normal ratification, not a defect. |
| **FR-11** Scout | 🟡 READY-with-dependency | auth shape (D2) ties to X1 ADR; Graph consent is operator-only. |
| **FR-12** Unified lifecycle | 🟡 READY-with-dependency | archive leg depends on X1/DR-11 + Graph consent. |
| **FR-13** Telemetry | ❌ **NOT READY** | **`event_type` is defined two incompatible ways** (§4-1). The schema cannot be built without a reconciling decision → **forces a question.** |
| **FR-14** Terrain pipeline | ✅ READY | three paths + contract + done-when; the Claims-provenance upgrade (ontology §6) is an explicit pending-on-evidence, not a hole. |
| **FR-15** Prep-view | ✅ READY | consumes FR-10/FR-13; done-when present. |
| **FR-16** Synthesis rule | ✅ READY | triggers + hard quality bar. |
| **FR-17** Ontology charter | 🟡 READY-with-open | Product-axis hypothesis pending P2 evidence reconciliation (ontology D3 / §7) — flagged open, not silent. |

**Cross-cutting blocker (not per-FR):** the **intake omits FR-10…17 entirely** (§5-4). A technical architect starting at the declared FIRST document would not discover the eight new FRs → forces the question *"are there more requirements than FR-1…9?"* **This is the single highest-leverage fix** and it is cheap (one addenda pointer).

**Overall §7 verdict: NOT-READY-CLEAN.** Three gaps force questions before a no-questions handover is true:
1. **FR-13 `event_type` conflict** (§4-1) — the only per-FR blocker.
2. **Intake does not reference FR-10…17** (§5-4) — discoverability blocker.
3. **Three PENDING objectives** (T1 metadata charter — *kluczowe*; T6 integration brief; pre-mortem) leave named holes; the metadata charter's absence means the canonical field-set FR is unspecified while FR-10/17 already lean on `dims`.

Everything else (registry home, Product-axis, Graph consent) is normal operator ratification, not a readiness defect. **The four delivered briefs are strong; the campaign's shortfall is completeness (4/7) and integration (addenda not folded), not quality.**

---

*End of audit. Zero repo writes performed. Every DONE/defect/inconsistency claim above carries a commit hash, repo path, or file:line anchor.*
