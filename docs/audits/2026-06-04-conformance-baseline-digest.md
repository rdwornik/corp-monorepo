# corp-monorepo v0 — Conformance Baseline Digest (Dynamic Workflow)

- **Date:** 2026-06-04
- **Author:** Rob (via Claude Code, Opus 4.8 main session)
- **Backlog ref:** advances #81 (semantic-conformance pattern); first child-repo deployment after the .dev-knowledge hub pilot
- **Nature:** read-only documentation-conformance review — **health baseline**. No fixes. Findings are proposals for operator triage.
- **Run ID:** `wf_c8d6ece8-fe6` · **Workflow:** `conformance-corp` (inline, adapted from `conformance-hub.js`)

---

## What this run was

A Dynamic Workflow fanned out **3 read-only verifiers** (Haiku de facto) over corp-monorepo's living docs, an **adversarial skeptic** (default-to-kill) culled false positives, and a **digest** synthesized survivors. Every finding carried a required `evidence_command`; agents were blocked from writing (session `permissions.deny: ["Write","Edit"]` active during the run; fleet-wide `git status --porcelain` tripwire after). **I (Opus, main session) then re-ran every survivor's evidence command against live repo state** — only verified findings enter this digest, each marked **VERIFIED REAL** or **DOWNGRADED**.

Three verifier domains (validated v0 shape — no new domains this run):
- **V1 · JOURNAL vs git** — last 10 entries vs commit history
- **V2 · Living-doc claims vs repo state** — CLAUDE.md / ARCHITECTURE.md / VISION.md factual claims (counts, paths, CLI/module lists, ADR refs) vs actual repo
- **V3 · BACKLOG ↔ commits coherence** — recently closed/added items vs what their commits delivered

---

## Findings

Workflow produced **18 raw → 8 survived skeptic → 5 VERIFIED REAL + 3 DOWNGRADED** by main-session verification. All 5 real findings are the **same class: ARCHITECTURE.md count drift** — stale inventory/LOC counts that the `last_reviewed: 2026-06-02` stamp did not catch. None are behavioral/safety defects; all are doc-vs-reality count mismatches.

```
# | Sev  | Domain       | Finding (claim → live)                              | Evidence (re-run by Opus)                                              | Status
--+------+--------------+-----------------------------------------------------+-----------------------------------------------------------------------+-------------------
F1| med  | living-docs  | ARCHITECTURE.md:367 "notes table (1,972+ notes)"    | sqlite3 index.db 'SELECT COUNT(*) FROM notes' → 488                    | VERIFIED REAL
  |      |              |   → live notes table = 488 (≈4x overstatement)      | (workflow rated high on magnitude; impact is documentation-only)      |
F2| med  | living-docs  | ARCHITECTURE.md:244 "client aliases (15)"           | grep client_aliases: config/naming_config.yaml → 32                   | VERIFIED REAL
  |      |              |   → naming_config.yaml has 32 (+17 drift)           |                                                                       |
F3| low  | living-docs  | ARCHITECTURE.md:240 "inbox.py (1161 LOC)"           | wc -l src/corp/ingest/inbox.py → 951                                  | VERIFIED REAL
  |      |              |   → live 951 (line 514 notes refactor; :240 stale)  |                                                                       |
F4| low  | living-docs  | ARCHITECTURE.md:253 "database.py (705 LOC)"         | wc -l src/corp/ops/database.py → 542                                  | VERIFIED REAL
  |      |              |   → live 542 (line 511 notes refactor; :253 stale)  |                                                                       |
F5| low  | living-docs  | ARCHITECTURE.md:244 "Type codes (19)"               | grep type_codes: config/naming_config.yaml → 22                       | VERIFIED REAL
  |      |              |   → naming_config.yaml has 22                       |                                                                       |
--+------+--------------+-----------------------------------------------------+-----------------------------------------------------------------------+-------------------
D1| —    | living-docs  | ARCHITECTURE.md:160 "actions/ (12 modules)"         | ls src/corp/actions/*.py → 12 files (11 excl __init__.py)             | DOWNGRADED
  |      |              |   → 11 domain modules + __init__ = 12 files         | count defensible either way; not a clear contradiction                |
D2| —    | living-docs  | ARCHITECTURE.md:33,407 "corp (40+ commands)"        | click walk → 54 commands                                              | DOWNGRADED
  |      |              |   → 54 satisfies "40+"; claim is technically true   | understated but not false                                             |
D3| —    | backlog      | [#5] JLR low-quality notes re-extraction "open"     | git log -S JLR (no re-extract commit); JOURNAL:289/295/301 unmet Next | DOWNGRADED
  |      |              |   → item is LEGITIMATELY open; backlog is correct   | "unsupported" = no closure because work is genuinely undone           |
```

---

## Evaluation block (the point of the exercise)

**(a) Net-new real findings vs this repo's existing gates: 5.**
All 5 are ARCHITECTURE.md count drift. Existing gates do **not** cover this class: pre-commit `ruff` (format/lint), `tach` (import layers), `toc-freshness` (TOC block structure, not body counts), `normalize-headers` (log headers), and the safety tests (`test_vault_writer_invariant`, OneDrive guards) all validate *structure/behavior*, none validate *prose counts against live state*. So all 5 are net-new.
- **Planner-seeded honesty note (correction #3):** the "~2,548 vs 2554 tests" example cited during planning was traced to the **run prompt's framing** ("Scale L, ~2,548 tests"), **not** a living-doc claim — `grep` confirms no numeric test-count exists in CLAUDE.md / ARCHITECTURE.md / VISION.md. V2 therefore correctly surfaced **zero** test-count findings. **None of the 5 net-new findings are planner-seeded**; the seeded example never materialized because the repo never made the claim.

**(b) False positives killed by the skeptic: 10 of 18 (56% kill-rate).**
Sound kills include `extract.py (1184 LOC)` and `router.py (893 LOC)` — the doc claims **match live** (my `wc -l` confirms 1184 / 893); the Haiku verifier miscounted and the skeptic correctly re-ran and killed them. `built_in_actions.py (967 LOC)` killed correctly (ARCHITECTURE.md:512 marks it `~~RESOLVED~~`; live is a 21-line shim, consistent with the doc).

**(c) Survivors downgraded by my verification: 3 of 8 (37.5%).** D1 (actions/ count ambiguous), D2 (corp "40+" technically true), D3 ([#5] legitimately open). **Verifier-reliability caveat:** the Haiku V2 produced unreliable raw LOC numbers (inbox 793, database 473, extract 988, router 753 — all wrong vs live 951/542/1184/893). The skeptic corrected inbox/database and killed extract/router, but the raw verifier counts could not be trusted — **the live `wc -l` in the table above is the ground truth.** This is the core argument for mandatory Opus re-verification.

**(d) Cost / time (Haiku-tier costing).**
- Output tokens (balloon metric, `budget.spent()`): **74,968** — half the 150k Scale-L allowance.
- Gross `subagent_tokens`: **246,552** — cache-inflated ≈3.3x; **not** the balloon metric (per correction #2: gross would falsely flag a healthy run).
- Wall time: **762,730 ms ≈ 12.7 min**. Agents: **5**. Tool uses: 196.

**(e) Actual models from jsonl (never trust narration).**
All 5 agents ran `claude-haiku-4-5-20251001`. Per-agent model routing remains **non-functional in CC 2.1.162** — the script set **no** `model` options (no pretense). Verified per-transcript:
```
agent-a0de65dd…  claude-haiku-4-5-20251001   (V*)
agent-a50116c1…  claude-haiku-4-5-20251001
agent-a562f90e…  claude-haiku-4-5-20251001
agent-ad178dd7…  claude-haiku-4-5-20251001
agent-af6a33a7…  claude-haiku-4-5-20251001
```
(reproduce: `grep -oE '"model":"[^"]*"' <agent>.jsonl | sort -u` per transcript under the run dir)

**(f) What a per-repo profile (#82) should tune next run.**
Add a **deterministic count-verifier** for this repo: machine-compute every numeric inventory ARCHITECTURE.md asserts (`wc -l` on cited files, `ls | wc -l` on package dirs, `sqlite3 COUNT(*)` on index.db, `grep | wc -l` on config lists) and diff against the doc — 5/5 real findings were count drift a non-LLM checker catches deterministically. That frees the Haiku verifier for genuinely semantic claims, and sidesteps its demonstrated LOC-miscounting (see c).

---

## Checked-and-clean (so absence is informative)

Verified **correct** (no finding) — confirmed by me where reachable:
- **5 CLIs** exist (`corp`, `corp-meta`, `cke`, `cpe`, `com`); 4-layer Tach model intact; 6 packages consolidated into `src/corp/`
- ADRs referenced in CLAUDE.md exist: ADR-14, ADR-23, ADR-26, ADR-27, ADR-32; pre-commit has ruff + tach
- Safety invariants documented match code: `corp (ingest/)` sole `02_sources/` writer; CKE pure extraction
- `extract.py (1184 LOC)` and `router.py (893 LOC)` claims are **accurate** (skeptic-killed verifier false positives)
- `built_in_actions.py` correctly documented as a re-export shim (`~~RESOLVED~~`, live 21 LOC)
- JOURNAL last-10 vs git: 2026-06-02/03 entries (ruff drift #12, stale-branch resolution, ecosystem unification, LESSONS.md, ADR-71 hooks) all corroborated by commits
- BACKLOG open items #1, #2, #6, #7, #8, #9, #11, #12 properly scoped; Action 6 & 7c closures coherent with ADR-32 / VISION amendment
- `cli/` "18 files" (live 17) and `agents.yaml` "5 agents" (live 5) — minor/non-issues, skeptic-killed

---

## Disposition

**Findings are proposals for operator triage — nothing was fixed.** The 5 VERIFIED REAL items are a single cleanup: refresh ARCHITECTURE.md's stale counts (notes 1,972+→488, client_aliases 15→32, inbox.py 1161→951, database.py 705→542, type_codes 19→22) and re-stamp `last_reviewed`. The 3 DOWNGRADED items need no action (or, for [#5], a grooming decision on whether the JLR re-extraction is still wanted). This digest is corp-monorepo's **conformance health baseline** — the reference all future runs compare against.

**corp-monorepo baseline ESTABLISHED.**
