# corp-monorepo Universalization Gap Review

**Date:** 2026-05-18
**Subject repo:** `C:\Users\1028120\Documents\Dev\corp-monorepo`
**Branch:** `docs/universalization-review`
**Baseline HEAD:** `5d9bbf8` (`main`, clean)
**Author:** Claude Code (Opus 4.7) — read-only review session
**Purpose:** Evidence-based gap analysis of corp-monorepo against the
current ecosystem way of working. Drives the universalization execution
spec.

> **Review only.** No file moves, deletions, demotions, or content edits
> have been made in this session. Every gap below is recorded as
> `current state → standard → gap → remediation`; the remediation is a
> proposal for a follow-up execution session, not a commitment made here.

---

## 1. Method

### 1.1 The standard

Sources (read-only, in `C:\Users\1028120\Documents\Dev\.dev-knowledge`):

- `protocols/ESSENTIALS.md` — daily cheat sheet, JOURNAL shape, commit
  standard, three-layer flow, supersession rule.
- `protocols/PLAYBOOK.md` §"Project Scale Tiers" + §"Documentation file
  types and session continuity" + §"Supersession & decommissioning" +
  §"Handoff format spec".
- `docs/decisions/ADR-33-vision-universalization.md` — Standard-tier
  `VISION.md` mandatory for Scale-L.
- `docs/decisions/ADR-38-universal-repo-architecture.md` (incl. **A3
  amendment, 2026-05-11**) — Scale-L mandatory file set;
  `ARCHITECTURE.md` MUST be at repo root.
- `docs/decisions/ADR-48-trim-documentation-governance.md` — audit
  trimmed to structural-only; ADR-46/47 demoted; ADR-27 scope-tags
  retired; governance-admission rule.
- `docs/decisions/ADR-49-consolidate-past-recording-files.md` —
  `CHANGELOG.md` and `BACKLOG_ARCHIVE.md` removed; JOURNAL becomes the
  single human past-narrative with
  `Did / Result / Changes / Abandoned / Next` shape.
- `docs/decisions/ADR-50-machine-document-encoding.md` — restricted
  structured markdown for machine-layer files.
- `docs/audits/2026-05-17-corp-monorepo-governance-rollout-plan.md` —
  prior plan; its discovery checklist is reused below, not re-derived.

Concretely, **"universalized, current way of working" for a Scale-L
repo** means:

1. Mandatory files present (ADR-38 §"Mandatory documentation",
   table at L:94–101): `README.md`, `VISION.md` (Standard tier),
   `ARCHITECTURE.md` **at repo root** (A3), `BACKLOG.md`,
   `docs/decisions/`, `pyproject.toml`, `src/`. Note that
   `CHANGELOG.md` is mandatory in ADR-38 §"Mandatory documentation"
   but RETIRED by ADR-49 — the live standard is ADR-49.
2. `VISION.md` frontmatter has `tier: standard`, plus `version`,
   `last_reviewed`, `owner`, `status` (ADR-33 §"Mandatory sections").
3. `JOURNAL.md` per-entry shape:
   `Did / Result / Changes / Abandoned / Next`
   (ESSENTIALS:290–296; ADR-49 §"Decision").
4. Commit messages carry the load `CHANGELOG.md` used to —
   Conventional Commits with non-trivial bodies
   (ESSENTIALS:250–267).
5. No enforced doc-format checks beyond structural file/section
   presence (ADR-48 §"Decision"). Cosmetic uniformity via auto-format
   normalizer, not audit.
6. Scope-tag vocabulary is informal metadata; existing tags stay,
   nothing enforces them (ADR-48 §"Decision"; rollout-plan §2.5).
7. Decommissioning discipline: any ADR that supersedes or relocates
   names the obsolete artifact in a `Decommission:` field
   (ESSENTIALS:186–194).
8. Machine-layer files use restricted structured markdown
   (ADR-50 §"Decision").
9. Workflow / session-start / handoff guidance in CLAUDE.md and
   AGENTS.md references current artifacts only — no `.ecosystem/`
   paths, no retired files, no stale numbers.

### 1.2 Baseline (the "before" state)

| Check | Result |
|---|---|
| `git status` | clean |
| HEAD | `5d9bbf8` on `main`; review branch `docs/universalization-review` created |
| `pytest --collect-only -q` | **2,521 tests collected** in 15.5s |
| `tach check` | `[OK] All modules validated!` |
| `ruff check src/` | 1 error (import-organize, fixable) |
| `ruff check src/ tests/` | 87 errors (import-organize across tests, fixable) |
| Full `pytest -x` run | not executed in review session (collection is sufficient to confirm test health for a read-only audit) |

The 87 ruff errors are import-ordering on test files — unrelated to the
universalization gaps below and not in scope for the rollout.

### 1.3 Discovery results (using rollout-plan §4.1 checklist)

| Item | Observed state |
|---|---|
| `CHANGELOG.md` | EXISTS, 42 lines, last entry 2026-04-22 (ADR-27 note), oldest 2026-03-28 `[1.0.0]`. Semver lineage present. |
| `BACKLOG_ARCHIVE.md` | ABSENT — no file in repo. |
| `BACKLOG.md` | ABSENT — no file in repo. |
| `VISION.md` | **ABSENT — no file anywhere in repo.** (Grep glob `**/*.md` → zero matches for `VISION.md`.) |
| `ARCHITECTURE.md` | at `docs/ARCHITECTURE.md:1`, 428 lines. **NOT at repo root → non-compliant with ADR-38 A3.** |
| `JOURNAL.md` | EXISTS at root, 237 lines. **Latest entry 2026-04-15** (`JOURNAL.md:8`). Shape: `Did / Failed / Next` (`JOURNAL.md:9–11`). **Both stale and wrong shape.** |
| `docs/HANDOFF.md` | EXISTS, 456 lines. `Last updated: 2026-03-29T01:13:07Z` (`docs/HANDOFF.md:2`). |
| `docs/handoffs/` | EXISTS with a single legacy handoff: `2026-04-15-handoff.md`. |
| `LESSONS.md` | Universal-only (lives in `.dev-knowledge`). Not expected per-repo — correct. |
| `docs/decisions/` ADRs | 29 files matching `ADR-*.md` (ADR-01..ADR-26 + ADR-08a/b split + two ADR-27 files). |
| ADR `Decommission:` field | **Zero ADRs carry a `Decommission:` field** (grep returns no matches in `docs/decisions/*.md`). |
| `docs/decisions/README.md` index | **Stops at ADR-21** (`docs/decisions/README.md:29`). ADR-22..ADR-27 not indexed. |
| ADR-27 collision | `ADR-27-council-onedrive-centralization.md` (a transcript) and `ADR-27-safety-invariants.md` (the actual ADR) share number ADR-27. |
| Council #28 / #29 | Transcripts only (`docs/decisions/transcripts/DECISION_28_*.md`, `DECISION_29_*.md`); no ADR distillations. |
| Scope tags | grep for `<!-- scope: ` / `[scope:` across the whole repo → **2 hits** (`.claude/skills/gotchas/gotchas.md:285,292`), both meta-references to the ai-council repo, not corp-monorepo's own scope-tagging. Effectively absent. |
| Audit-check scripts | `scripts/dev-check.ps1` (pre-merge gate), `scripts/run-all-tests.ps1` (test runner), `scripts/update_handoff.py` (HANDOFF.md regenerator). **No `scripts/validate_*.py` or `scripts/audit_*.py` doc-format scripts exist.** |
| Pre-commit hooks | `.pre-commit-config.yaml` runs ruff + `tach check`. **No scope-tag validator, no doc-format check.** |
| `scripts/update_handoff.py` | Touches `docs/HANDOFF.md`, reads `JOURNAL.md`'s "N passed" string. Does NOT reference CHANGELOG.md. |
| `.claude/skills/` | One skill: `gotchas/` (`SKILL.md`, `gotchas.md` 293 lines, last updated 2026-03-30). |
| `corp-monorepo.code-workspace` | Present at root; `**/CHANGELOG.md` referenced in workspace settings (`corp-monorepo.code-workspace:74`). |
| `CLAUDE.md` | 94 lines. Declares Scale L implicitly via test count and module table. Names "Council Decisions: 24" while 27 numbered ADRs exist (`CLAUDE.md:54`). |
| `AGENTS.md` | 130 lines. Codex-review focused. No reference to past-recording files. |
| `CONTRIBUTING.md` | 121 lines. References `docs/ARCHITECTURE.md` at L:118. No CHANGELOG mention. |

### 1.4 Reference-drift evidence

| Source | Quote | Problem |
|---|---|---|
| `CLAUDE.md:54` | `## Council Decisions: 24 (ADR summaries in 'docs/decisions/'…)` | 27 numbered ADRs exist; transcripts for #28/#29 exist. Number is stale. |
| `docs/HANDOFF.md:23–24` | `Council decisions \| 24 \| 2026-03-29` and `ADRs \| 24 \| 2026-03-29` | Same stale count, plus the file's `Last updated:` is itself 2026-03-29. |
| `docs/HANDOFF.md:194` | `Full transcripts: '.ecosystem/council_transcripts/DECISION_NN_*.md'` | `.ecosystem/` eliminated 2026-03-30 (per CHANGELOG.md:23). Path no longer exists. |
| `docs/HANDOFF.md:195` | `ADR summaries: 'decisions/ADR-NN-*.md' (ADR-01 through ADR-23)` | Wrong directory and stale range — actual is `docs/decisions/ADR-01..ADR-27`. |
| `docs/HANDOFF.md:393–394` | `decisions/ADR-NN-*.md` and `.ecosystem/council_transcripts/` | Same drift repeated. |
| `docs/HANDOFF.md:213` | `Gotchas \| 37` | Counted 2026-03-28 in same file's row dates; `.claude/skills/gotchas/gotchas.md` is now 293 lines updated 2026-03-30. |
| `docs/HANDOFF.md:447` | `Check '~/.claude/skills/gotchas/gotchas.md' before modifying any package (41 gotchas)` | "41 gotchas" disagrees with `Gotchas \| 37` two rows above in the same file. Both numbers unverified. |
| `docs/decisions/README.md:29` (table end) | index stops at ADR-21 | ADR-22..ADR-27 unindexed. |
| `docs/ARCHITECTURE.md:1–3` | `Last updated: 2026-03-30` | Stale relative to ADR-27 (2026-04-22) which it cross-references. (`docs/ARCHITECTURE.md` was modified in commit `1b6c293` but its own header was not bumped.) |
| `docs/HANDOFF.md:392` | `decisions/ADR-NN-*.md   22 ADR summaries` | "22 summaries" — stale even by 2026-03-29 standards. |
| `CHANGELOG.md` | `# Changelog` then 2026-04-22 / 2026-04-21 / `[1.0.0] 2026-03-28` entries | Will be retired per ADR-49; trim-time work. |

The 2026-04-21 audit also flagged a `docs/ARCHITECTURE.md:423–426`
reference to a non-existent file and a
`docs/diagrams/conventions.yaml:18–23` layer-name drift; not re-verified
this session since they are adjacent to (not part of) the universalization
scope.

---

## 2. Gap analysis (current state → standard → gap → remediation)

### 2.1 `VISION.md` absent (GATE)

- **Current state:** No `VISION.md` anywhere in the repo (`Grep VISION\.md --glob '**/*.md'` → zero matches).
- **Standard:** ADR-33 §"Mandate" + §"Mandatory sections" — any repo with ≥1 dependent MUST have `VISION.md`. Scale-L → **Standard tier** with all 6 sections (Vision, Scope, Values, Relationships, Lifecycle, References) plus frontmatter (`version`, `last_reviewed`, `owner`, `status`, `tier: standard`). PLAYBOOK Scale-tier matrix (PLAYBOOK.md:557) also marks `VISION.md` "required" for Scale L (per ADR-33).
- **Gap:** Absent entirely. This is the **single hardest blocker** in the rollout plan §5 ("STOP conditions") — every other phase is gated on it.
- **Remediation:** Standalone VISION-creation session **before** the trim rollout. Operator-driven; may warrant AI Council debate per the `.dev-knowledge` model. The execution prompt for that session is separate and out of scope of THIS review.

### 2.2 `ARCHITECTURE.md` at wrong location (ADR-38 A3)

- **Current state:** `docs/ARCHITECTURE.md:1` (428 lines). Repo root has no `ARCHITECTURE.md`.
- **Standard:** ADR-38 A3 (2026-05-11): "`ARCHITECTURE.md` MUST be placed at repo root, NOT nested in `docs/` or any subdirectory."
- **Gap:** Non-compliant location.
- **Remediation:** Move `docs/ARCHITECTURE.md` → `ARCHITECTURE.md` (root). Update inbound references: `CONTRIBUTING.md:118`, `docs/HANDOFF.md` (multiple), `README.md:36` (says "See `CLAUDE.md`" actually — no direct ref), CLAUDE.md (no current ref). Single commit on the rollout branch. **Rollout-plan §6.3 explicitly defers this** — flag here, route to a separate session OR fold into a follow-up phase of the rollout once VISION lands.

### 2.3 `BACKLOG.md` absent

- **Current state:** No `BACKLOG.md` in repo.
- **Standard:** ADR-38 Mandatory documentation table (`BACKLOG.md` YES at Scale M+); PLAYBOOK §"Tier mandate" (PLAYBOOK.md:1923) — M and L repos MANDATORY. ADR-49 retains BACKLOG.md (only `BACKLOG_ARCHIVE.md` is retired).
- **Gap:** Missing for a Scale-L repo. Open items currently live in `docs/HANDOFF.md` §"Open Decisions" (`docs/HANDOFF.md:414–431`) and §"Pending Fixes" (`docs/HANDOFF.md:434–440`).
- **Remediation:** Create empty `BACKLOG.md` at repo root following the `.dev-knowledge` schema (`P{N}` priority tags, `[open|superseded]` status, dated entries). Seed with the existing HANDOFF.md "Open Decisions" + "Pending Fixes" items.

### 2.4 `JOURNAL.md` shape is the old `Did / Failed / Next`

- **Current state:** `JOURNAL.md:9–11` shows
  `- **Did:** … / - **Failed:** … / - **Next:** …`. Same shape throughout all entries.
- **Standard:** ADR-49 §"Decision" + ESSENTIALS:290–296 — per-entry shape is `Did / Result / Changes / Abandoned / Next`. The `Changes:` line is load-bearing because CHANGELOG.md is retired.
- **Gap:** Wrong shape across the whole file. Append-only invariant means existing entries are NOT rewritten; the change is forward-only.
- **Remediation:** Update the JOURNAL intro blockquote (`JOURNAL.md:3–4`) to describe the new shape and mark the cutover date. New entries adopt `Did / Result / Changes / Abandoned / Next`. No backfill.

### 2.5 `JOURNAL.md` is stale (one month of commits unrecorded)

- **Current state:** Latest entry `2026-04-15` (`JOURNAL.md:8`). Recent commits go through `5d9bbf8` on 2026-04-24+ (ADR-27 drafting, Council #28/#29 archival, OneDrive hotfix landing).
- **Standard:** ESSENTIALS §"Ending a Session" — JOURNAL entry per session.
- **Gap:** Roughly one month of work (OneDrive safety hotfix, ADR-27 drafting, Council #28/#29 transcripts) is in `git log` but not in `JOURNAL.md`.
- **Remediation:** Add catch-up entries (one combined entry is acceptable for the gap window, using the new shape). Source the content from `git log` and `CHANGELOG.md`'s 2026-04-21/22 entries. Forward-only after that.

### 2.6 `CHANGELOG.md` not retired

- **Current state:** `CHANGELOG.md` exists (42 lines, semver lineage from `[1.0.0] 2026-03-28`).
- **Standard:** ADR-49 §"Decision" — `CHANGELOG.md` removed. Change record = descriptive Conventional-Commits messages + `Changes:` line in each JOURNAL entry.
- **Gap:** File still present; conflicts with ADR-49.
- **Remediation:** Retire per rollout-plan §3.3. Operator preservation policy (rollout-plan §9.1): default to **hard delete** with deletion-commit body listing prior structure. Update one workspace reference (`corp-monorepo.code-workspace:74`). Add a lightweight decision-note in `docs/decisions/` with a `Decommission:` field pointing to `CHANGELOG.md` + disposition. **Note the ADR-38 ↔ ADR-49 conflict (rollout-plan §6.2):** ADR-38's mandatory table still lists CHANGELOG. The rollout proceeds per ADR-49; a follow-up ADR-38 amendment in `.dev-knowledge` is operator-timed.

### 2.7 `docs/HANDOFF.md` heavily stale + reference-drift

- **Current state:** `Last updated: 2026-03-29T01:13:07Z` (`docs/HANDOFF.md:2`). Cites `.ecosystem/` paths that were removed 2026-03-30 (CHANGELOG.md:23). Cites `decisions/` instead of `docs/decisions/`. Test count `2,412` vs current `2,521`. ADR range "ADR-01 through ADR-23". Council decisions "24". Gotchas count disagrees with itself ("37" vs "41" in same file).
- **Standard:** PLAYBOOK §"Handoff format spec" (PLAYBOOK.md:615+) — the legacy single-file format is preserved as-is; the **new** folder-per-session format is the going-forward standard. `docs/HANDOFF.md` (the master, regenerated by `scripts/update_handoff.py`) is a corp-monorepo-local pattern that pre-dates the ecosystem handoff spec.
- **Gap:** Two coexisting patterns with no canonicality declaration — flagged in rollout-plan §3.7 as **adjacent debt, NOT in scope** for the trim. But the staleness + reference-drift in `docs/HANDOFF.md` itself is in scope wherever the trim touches the file.
- **Remediation:** Within the trim, only touch references the trim itself disturbs (CHANGELOG mentions, the JOURNAL-shape line in §"Session Protocol" 444–450, the `41 gotchas` line). A separate "handoff-pattern reconciliation" session decides whether `docs/HANDOFF.md` should be regenerated, frozen, or deprecated entirely in favour of the folder-per-session pattern.

### 2.8 ADR `Decommission:` field absent across all ADRs

- **Current state:** Zero ADRs carry `Decommission:`. ADR-14 supersedes ADR-10 (silently); ADR-08a supersedes ADR-03 (silently); ADR-07 supersedes ADR-04 (silently); ADR-26 (Tach) supersedes the 7-layer model documented in ARCHITECTURE.md (silently).
- **Standard:** ESSENTIALS §"Supersession closes the loop" (lines 186–194) + PLAYBOOK §"Supersession & decommissioning" (lines 598–614) — every supersession/relocation MUST carry a `Decommission:` field. Non-empty field becomes a BACKLOG item until removed.
- **Gap:** Discipline absent across the existing 29 ADR files. Most supersessions are historical and their obsolete artifacts have already been removed — so the missing `Decommission:` is documentary debt, not active orphan-risk.
- **Remediation:** Forward-only adoption. The trim adds the `Decommission:` field to the ADR template (rollout-plan §7 Phase 6). New ADRs use it. Retroactive backfill across 29 ADRs is **out of scope** unless operator explicitly requests it. Document this scope decision in the rollout's closing JOURNAL entry.

### 2.9 ADR-27 number collision

- **Current state:** Two files share ADR-27: `docs/decisions/ADR-27-council-onedrive-centralization.md` (which is actually a debate transcript, not an ADR — first line "# AI Council Debate") and `docs/decisions/ADR-27-safety-invariants.md` (the real ADR).
- **Standard:** ADR numbering convention: each ADR-NN is a single file (`docs/decisions/transcripts/DECISION_NN_*.md` is the parallel transcripts namespace, per PLAYBOOK file-type taxonomy).
- **Gap:** A transcript is mis-filed as an ADR (`ADR-27-council-onedrive-centralization.md` belongs under `docs/decisions/transcripts/` as `DECISION_27_*.md`).
- **Remediation:** Move the transcript to `docs/decisions/transcripts/DECISION_27_onedrive_centralization.md` (and rename to match the naming pattern). The actual ADR (`ADR-27-safety-invariants.md`) cross-references it at L:7. Update that line. Adjacent to but not blocking the rollout — recommend folding into Phase 4 (ADR demotions) or a dedicated decommissioning-debt phase.

### 2.10 `docs/decisions/README.md` index stops at ADR-21

- **Current state:** `docs/decisions/README.md:29` ends the table at ADR-21. ADR-22 through ADR-27 (six ADRs, including the Tach-adoption decision that drives the layer architecture and the safety-invariants decision) are unindexed.
- **Standard:** No explicit ADR for index-currency, but the index file's own §"How to add a new ADR" (`docs/decisions/README.md:31–37`) instructs to add a row when a new ADR lands — discipline that has lapsed.
- **Gap:** Index lags reality by six ADRs.
- **Remediation:** Add rows for ADR-22..ADR-27 (mark statuses, supersession links). One commit, mechanical.

### 2.11 CLAUDE.md / HANDOFF.md numerical drift

- **Current state:** `CLAUDE.md:54` says "Council Decisions: 24"; `docs/HANDOFF.md:23–24` says 24 (Council) and 24 (ADRs); both dated 2026-03-29. The 2026-04-21 audit also catalogued this.
- **Standard:** ADR-50 §"Decision" — machine-layer files use restricted structured markdown; numerical claims must be current or absent. CLAUDE.md is a machine-layer file (PLAYBOOK file-type taxonomy:531).
- **Gap:** Numbers are stale. Worse, they're load-bearing — agents reading CLAUDE.md as session context will start from wrong premises.
- **Remediation:** Either bump the numbers and add a `last_verified:` line, or remove the count and replace with `see docs/decisions/`. Default per `.dev-knowledge` pattern: remove brittle counts; reference the source-of-truth directory.

### 2.12 CLAUDE.md does not declare Scale tier explicitly

- **Current state:** `CLAUDE.md` declares architecture and CLIs but **never says `## Project Scale: L`**. The scale is inferable from the test count (2,404 in `CLAUDE.md:29`, now 2,521).
- **Standard:** PLAYBOOK §"Project Scale Tiers" line 329: "Every project declares its scale in its CLAUDE.md: `## Project Scale: L`".
- **Gap:** Tier not declared in the structured form the standard expects.
- **Remediation:** Add the one-line `## Project Scale: L` declaration at the top of CLAUDE.md. Five-second edit.

### 2.13 CLAUDE.md "Session Handoff" section references retired pattern

- **Current state:** `CLAUDE.md:79–88` describes a session-handoff pattern that pastes `docs/HANDOFF.md` into new Claude.ai chats and runs `python scripts/update_handoff.py` to refresh it.
- **Standard:** PLAYBOOK §"Handoff format spec" — the folder-per-session pattern (`docs/handoffs/{date}-{slug}/`) is the going-forward standard. The single-file `docs/HANDOFF.md` master is corp-monorepo-local and out of step with the ecosystem-wide spec.
- **Gap:** CLAUDE.md mandates the local pattern but doesn't acknowledge the ecosystem pattern. This is the same "two coexisting handoff patterns" debt flagged in rollout-plan §3.7.
- **Remediation:** Adjacent debt — defer to a dedicated handoff-pattern reconciliation session. The trim does not touch the section's structure, only its content (e.g., if CHANGELOG appears here, it's removed).

### 2.14 CLAUDE.md "Session Protocol" + `docs/HANDOFF.md` Session Protocol both say `Did/Failed/Next`

- **Current state:** `CLAUDE.md:73–77` and `docs/HANDOFF.md:444–451` both prescribe the old JOURNAL shape implicitly (by referencing the existing JOURNAL pattern).
- **Standard:** ADR-49 / ESSENTIALS:290–296 — `Did / Result / Changes / Abandoned / Next`.
- **Gap:** Both prescriptive documents point at the wrong shape.
- **Remediation:** Update both in the rollout's JOURNAL-shape phase (rollout-plan §7 Phase 7).

### 2.15 No `VISION.md` reading on session start in CLAUDE.md / AGENTS.md

- **Current state:** Neither file instructs the agent to read `VISION.md` first.
- **Standard:** ADR-33 §"Enforcement" §"Secondary baseline (now)" — "AGENTS.md / CLAUDE.md in each child repo MUST require reading `VISION.md` as part of session start ('Read first' section)."
- **Gap:** Missing — partly because `VISION.md` itself does not yet exist (§2.1). Blocked by §2.1.
- **Remediation:** Once `VISION.md` lands, both CLAUDE.md and AGENTS.md gain a "Read first: `VISION.md`, then this file" line. Couple with §2.1 in the VISION-creation session.

### 2.16 AGENTS.md is Codex-only, not cross-tool

- **Current state:** `AGENTS.md:1–7` self-describes as a Codex-only review config. Layer architecture mostly correctly reflected in `AGENTS.md:43–53`.
- **Standard:** PLAYBOOK file-type taxonomy line 533: AGENTS.md = "Cross-tool canonical governance" for Claude Code, Codex, Cursor, Aider — not Codex-specific.
- **Gap:** Scope-mismatch. AGENTS.md as Codex-only is a holdover; the universal pattern is a single canonical AGENTS.md governance file consumed by every coding agent.
- **Remediation:** **Conceptual gap, not a trim deliverable.** Two options: (a) rename AGENTS.md → `CODEX.md` and create a new cross-tool AGENTS.md, or (b) widen AGENTS.md to be the universal canonical file (with a Codex-review section). Option (b) is consistent with the ecosystem direction (ai-council does not have AGENTS.md per Council #28 gap). Decision deferred — route to a separate operator question, not folded into the trim.

### 2.17 Scope-tag enforcement absent (no remediation needed)

- **Current state:** grep across the entire repo for `<!-- scope: ` and `[scope:` returns 2 hits, both in `.claude/skills/gotchas/gotchas.md` and both referencing `ai-council` as the affected repo. corp-monorepo's own files carry no scope tags. `.pre-commit-config.yaml` carries no scope-tag validator.
- **Standard:** ADR-48 §"Decision" — scope-tag enforcement retired across the ecosystem; existing tags stay as informal metadata.
- **Gap:** None. corp-monorepo never adopted the vocabulary.
- **Remediation:** Phase 5 of the rollout (rollout-plan §7) is a **no-op**. Record in the discovery doc as such.

### 2.18 No `BACKLOG_ARCHIVE.md` to retire (no remediation needed)

- **Current state:** No `BACKLOG_ARCHIVE.md` anywhere.
- **Standard:** ADR-49 retires the file.
- **Gap:** None.
- **Remediation:** Phase 3 (rollout-plan §7) is a **no-op**.

### 2.19 No doc-format audit scripts to retire (no remediation needed)

- **Current state:** `scripts/` contains `dev-check.ps1` (pre-merge gate: ruff + tests + tach), `run-all-tests.ps1`, `update_handoff.py`, plus operational scripts (`extract_training_data.py`, `eval.py`, `enrich_training_data.py`, `archive_scan.py`, `sandbox_*.py`, etc.). **None enforce doc-format checks.**
- **Standard:** ADR-48 §"Decision" — doc-format checks trimmed.
- **Gap:** None.
- **Remediation:** Phase 1 (rollout-plan §7) is a **no-op**. Record as such.

### 2.20 No deterministic header normalizer

- **Current state:** No script equivalent to `.dev-knowledge/scripts/normalize_headers.py`. Cosmetic header drift is uncorrected.
- **Standard:** ADR-48 §"Decision" + rollout-plan §2.1 — cosmetic uniformity handled by an auto-format normalizer (write-time), not an audit check.
- **Gap:** Missing.
- **Remediation:** Port `normalize_headers.py` into corp-monorepo's `scripts/`, wire to `.pre-commit-config.yaml` as an auto-format hook. Per rollout-plan §7 Phase 6.

### 2.21 No ADR template carrying `Decommission:` field

- **Current state:** No `templates/` directory at repo root; no ADR template. ADR creation has been copy-paste from an existing ADR (per `docs/decisions/README.md:32`).
- **Standard:** ESSENTIALS:186–194 (supersession rule) + rollout-plan §2.6 — `templates/ADR-template.md` MUST carry the `Decommission:` field.
- **Gap:** Missing.
- **Remediation:** Add `templates/ADR-template.md` with the field templated. Update `docs/decisions/README.md` §"How to add a new ADR" to reference the template. Per rollout-plan §7 Phase 6.

### 2.22 `.claude/skills/gotchas/` is current; no other skills

- **Current state:** Only one skill: `gotchas/` (`SKILL.md` + `gotchas.md` 293 lines, header `Last updated: 2026-03-30`). Pre-commit + tach already enforced separately. No `skills/audit/`, `skills/verify/`, etc.
- **Standard:** PLAYBOOK doesn't mandate any specific per-repo skills — skills are tooling adopted as need arises. The `.dev-knowledge`-wide skills (`boot`, `evolve`, `session-summary`, etc.) are user-scope (`~/.claude/skills/`) and don't need to be duplicated.
- **Gap:** No structural gap. Operationally, `gotchas.md` has a 2026-03-30 timestamp despite the 2026-04-21/22 OneDrive hotfix and ADR-27 drafting — the file may have new entries that aren't dated, but no structural review can confirm without reading every entry. **Out of scope for this review.**
- **Remediation:** None for the trim. A separate "gotchas hygiene" session may want to verify `Last triggered:` dates against the 2026-04 work.

### 2.23 Workflow documentation: thin / scattered

- **Current state:** Workflow guidance lives across CLAUDE.md (§"Development", §"Session Protocol", §"Session Handoff"), CONTRIBUTING.md (§"Development Flow", §"Import Boundary Rules"), and `docs/HANDOFF.md` (§"Session Protocol"). No single workflow document.
- **Standard:** PLAYBOOK is the universal workflow document; per-repo workflow lives in CLAUDE.md + CONTRIBUTING.md (per PLAYBOOK file-type taxonomy). The current split is consistent with the standard.
- **Gap:** Not a structural gap — but the split documents disagree on JOURNAL shape and reference retired patterns (§2.4, §2.14). Those are content gaps, not structure gaps.
- **Remediation:** Already covered by §2.4 + §2.14. No new action.

### 2.24 `docs/archive/` is large frozen historical record (informational, not a gap)

- **Current state:** `docs/archive/` contains 32 dated reports/handoffs from 2026-03-20..2026-03-30 (initial monorepo restructure era). All `.md` and `.json/.log` files.
- **Standard:** No standard against frozen archives; PLAYBOOK §"audits vs research" treats `docs/audits/` as immutable point-in-time and `docs/archive/` is the same kind of frozen storage.
- **Gap:** None.
- **Remediation:** Leave in place. Not in scope.

---

## 3. Remediation summary (grouped into workstreams)

The gaps cluster into **five workstreams** that the universalization
execution should plan around. Workstream A is the blocker; B–E run
sequentially behind it.

### Workstream A — VISION.md creation (GATE)

| Gap | Action |
|---|---|
| §2.1 `VISION.md` absent | Standalone session: write Standard-tier `VISION.md` for corp-monorepo (full 6 sections + frontmatter). Possible AI Council debate. |
| §2.15 (depends on §2.1) | Add "Read first: VISION.md" line to CLAUDE.md + AGENTS.md within the same session. |

**Blocking:** All other workstreams. Per rollout-plan §4.3 STOP
conditions, the trim cannot start without this.

### Workstream B — Past-recording consolidation (the ADR-49 trim)

| Gap | Action |
|---|---|
| §2.6 CHANGELOG.md retirement | Hard delete + decision-note with `Decommission:` field. Update `corp-monorepo.code-workspace:74`. |
| §2.4 JOURNAL shape adoption | Update JOURNAL intro to the new shape; forward-only. |
| §2.5 JOURNAL stale | Catch-up entries for 2026-04-15..2026-05-18 in the new shape. |
| §2.14 CLAUDE.md / HANDOFF.md prescribe wrong JOURNAL shape | Update prescriptive lines in both. |
| §2.3 BACKLOG.md absent | Create empty `BACKLOG.md` at root; seed from `docs/HANDOFF.md` §"Open Decisions" + §"Pending Fixes". |
| §2.18 BACKLOG_ARCHIVE.md retirement | No-op — record as such. |
| §2.19 audit-script trim | No-op — record as such. |

### Workstream C — Decommissioning discipline + ADR hygiene

| Gap | Action |
|---|---|
| §2.21 ADR template missing | Add `templates/ADR-template.md` carrying `Decommission:`. |
| §2.20 Header normalizer missing | Port `normalize_headers.py` from `.dev-knowledge`; wire as pre-commit auto-format hook. |
| §2.10 docs/decisions/README.md index lags by 6 ADRs | Add rows for ADR-22..ADR-27. |
| §2.9 ADR-27 number collision | Move transcript to `docs/decisions/transcripts/DECISION_27_*.md`. |
| §2.8 No `Decommission:` field on existing ADRs | Forward-only — do not backfill. |

### Workstream D — Numerical / reference drift cleanup (trim-touched only)

| Gap | Action |
|---|---|
| §2.11 CLAUDE.md / HANDOFF.md stale counts | Remove brittle counts or replace with directory references. |
| §2.12 CLAUDE.md missing `Project Scale: L` | One-line add. |
| §2.7 `docs/HANDOFF.md` reference-drift | Update only the lines the trim itself touches (CHANGELOG mentions, JOURNAL-shape, gotchas count). Adjacent drift (`.ecosystem/` paths, ADR range) deferred to a separate cleanup unless operator opts in per rollout-plan §9.5. |

### Workstream E — Adjacent / out-of-scope (route to separate sessions)

| Gap | Action |
|---|---|
| §2.2 `ARCHITECTURE.md` at `docs/` not root (ADR-38 A3) | Defer per rollout-plan §6.3 — separate move-and-update-refs session. |
| §2.13 / §2.7 / §2.16 Handoff-pattern coexistence | Defer per rollout-plan §3.7. |
| §2.16 AGENTS.md scope (Codex-only vs cross-tool) | Defer — operator question. |
| §2.22 Skills hygiene (`gotchas.md` last-triggered dates) | Defer. |
| 2026-04-21 audit `docs/ARCHITECTURE.md:423–426` non-existent ref | Defer unless operator expands per rollout-plan §9.5. |
| 2026-04-21 audit `docs/diagrams/conventions.yaml:18–23` layer-name drift | Defer. |

### Headline counts

- **24 distinct gaps** identified (§2.1..§2.24).
- **4 are no-ops** that just need to be recorded (§2.17, §2.18, §2.19, §2.24).
- **1 is a hard blocker / GATE** for everything else (§2.1).
- **5 are adjacent / out-of-scope** for the universalization trim (§2.2, §2.13, §2.16, §2.22, §2.24).
- **14 are in-scope concrete remediation items** distributed across Workstreams A–D.

---

## 4. Verification (for the executing session, not this one)

When the trim rollout completes, the post-trim verification should
confirm (per rollout-plan §7 Phase 8):

- `VISION.md` present at root, `tier: standard`, frontmatter parseable.
- `ARCHITECTURE.md` location decision recorded (root vs deferred).
- `BACKLOG.md` present at root.
- `CHANGELOG.md` absent.
- `BACKLOG_ARCHIVE.md` absent.
- `JOURNAL.md` intro describes `Did/Result/Changes/Abandoned/Next`.
- `templates/ADR-template.md` present with `Decommission:` field.
- `scripts/normalize_headers.py` present and wired to pre-commit.
- `docs/decisions/README.md` indexes through ADR-27.
- `tach check`, `pytest -x`, `ruff check src/` all green.
- `git status` clean.

These are the success criteria for the execution session. THIS review
does not run them — they are recorded as the target state.

---

## 5. References

- `.dev-knowledge/protocols/ESSENTIALS.md` — JOURNAL shape, commit standard, supersession rule.
- `.dev-knowledge/protocols/PLAYBOOK.md` §"Project Scale Tiers", §"Documentation file types and session continuity", §"Supersession & decommissioning", §"Handoff format spec".
- `.dev-knowledge/docs/decisions/ADR-33-vision-universalization.md`.
- `.dev-knowledge/docs/decisions/ADR-38-universal-repo-architecture.md` (incl. A3 amendment 2026-05-11).
- `.dev-knowledge/docs/decisions/ADR-48-trim-documentation-governance.md`.
- `.dev-knowledge/docs/decisions/ADR-49-consolidate-past-recording-files.md`.
- `.dev-knowledge/docs/decisions/ADR-50-machine-document-encoding.md`.
- `.dev-knowledge/docs/audits/2026-05-17-corp-monorepo-governance-rollout-plan.md` — prior delta analysis and discovery checklist; reused here.
- Existing `docs/audits/2026-04-21-corp-monorepo-operating-model-analysis.md` — historical, treated as superseded by THIS review.

---

**End of review.** Next step (separate operator action): author the
execution prompt for Workstream A (VISION.md creation), then the
execution prompt for Workstreams B–D as a rollout sequence.
