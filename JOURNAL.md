# Journal — corp-monorepo

> Append-only log. Never edit old entries.
> Per-entry shape (per ADR-49, cutover 2026-05-18):
> `### YYYY-MM-DD — <session topic>` header, then bullets:
> `- Did:` what was actually done
> `- Result:` outcome / state on disk
> `- Changes:` short list of files / areas touched (this is the change record — there is no CHANGELOG anymore)
> `- Abandoned:` items deliberately dropped (each non-trivial drop also gets a short note in `docs/decisions/`; do not record reasoning inline here)
> `- Next:` follow-ups
> Entries above the cutover date use the older `Did / Failed / Next` shape and are preserved as-is.
> Claude Code: read last 5 entries before starting work.

---

### 2026-06-06 — Nightly conformance routine (build + live contract proof)
- Did: Stood up corp-monorepo's self-contained nightly conformance routine by porting the hub's proven pattern (marker contract D+C, fail-closed Action triage, read-only proposals), fully self-contained per ADR-72 (no hub reference on the cloud executing path). Four envelope parts committed in-repo: (1) `.claude/workflows/conformance-corp.js` — 3 read-only verifiers fan out [V1 JOURNAL↔git, V2 living-doc structural claims (paths/commands/hooks/names), V3 DETERMINISTIC count-verifier] → adversarial skeptic → digest; Sonnet verifiers / Opus skeptic / Opus digest pinned per stage; code computes counts + builds the marker `<!-- counts: raw=N survived=N killed=N -->`, Stage-3 prompt-pins it, in-script validation throws on mismatch (mechanism D, native path); (2) `scripts/render_conformance_digest.py` — stdlib-only code-owned WRITE path (the executing-path backstop, since the .js validator is inert on the cloud spec-orchestration fallback) that recomputes+writes the marker and the Action-matched headers, fail-closed on disagreement; (3) `.github/workflows/nightly-conformance-triage.yml` — fail-closed parser reading ONLY the marker (`|| true` + emptiness/integer checks → unparseable-digest issue; reachability fix per LESSONS 2026-06-05), diff-guard (exactly one ADDED digest), 0 survivors → squash-merge, >0 → merge + `nightly-triage` issue with Findings/Next-Actions body; (4) `scripts/surface-conformance.ps1` — READ-ONLY fail-soft SessionStart surfacing (PS 5.1 empty-array gotcha handled), wired as a repo-local SessionStart hook in `.claude/settings.json` (merges with user-level hooks). Fixtures GENERATED from the real renderer + a both-ends parser test (`tests/test_nightly_triage_parser.py`, regexes extracted LIVE from the .yml). Then ran the synthetic end-to-end contract proof (hub Test-A): PR #1 on `claude/conformance-2099-12-31`, one generator-shaped survivor digest.
- Result: **All five contract criteria proven LIVE** — (a) diff-guard PASS, (b) marker-derived counts (survived=2 parsed from the code-owned marker → issue titled "2 survivor(s)"), (c) auto-merge (PR #1 squash-merged by github-actions + branch auto-deleted), (d) triage issue body carries Findings (High/Med/Low) + Next-Actions with Killed/Checked-clean correctly excluded, (e) SessionStart banner `[triage] 1 nightly finding await: #2`. Full suite green pre-merge: 2559 passed / 6 skip. Proof artifacts cleaned: synthetic digest removed from main, issue #2 deleted, branch auto-deleted, no `claude/*` remotes left (PR #1 remains as a labeled-synthetic merged record, un-deletable by design). Tree clean, `main` synced. **This routine's first SCHEDULED run is the n=2 candidate for the hub's #84 gate.** Step ordering note: the build was merged to `main` BEFORE the proof (not after) because GitHub runs `pull_request` Actions such that the diff-guard's auto-merge happy path requires the Action already on `main`; "before any schedule" (operator-created Routine) is still satisfied.
- **#86.3 ruling recorded (for the hub's later bookkeeping):** each cloud-routine repo carries its OWN adapted orchestration committed in-repo; the hub remains the canonical template for the local loop; template updates propagate at rollout moments, not at runtime. Ratified by the operator pasting this session's prompt; closes hub #86 sub-decision 3 under ADR-72.
- Changes: `.claude/workflows/conformance-corp.js` (new), `scripts/render_conformance_digest.py` (new), `.github/workflows/nightly-conformance-triage.yml` (new), `scripts/surface-conformance.ps1` (new), `.claude/settings.json` (SessionStart hook), `tests/test_nightly_triage_parser.py` + `tests/fixtures/nightly-triage/*` (new), `.claude/skills/gotchas/gotchas.md` (gh-api 404-on-stdout gotcha), this JOURNAL entry. Branch `feat/nightly-conformance` merged `--no-ff` and pushed; cleanup branch `chore/remove-synthetic-proof-digest` merged `--no-ff`.
- Abandoned: nothing. (Hub-side bookkeeping — #86.3 recorded, #86 close, n=2 evidence — rides the next hub session per ADR-41; not touched here.)
- Next: Operator creates the cloud Routine from the build's setup block (daily 01:15Z, env Trusted, branch-prefix `claude/conformance-*` restriction ON, model pins) at claude.ai/code/routines; operator confirms the Claude GitHub App is authorized for `rdwornik/corp-monorepo` (cannot be verified from CLI). First scheduled run = n=2 evidence for hub #84.

### 2026-06-06 — Remote bookkeeping: GitHub push + sensitivity sweep record
- Did: Ran a read-only pre-push sensitivity sweep across all 723 tracked files (client names, secrets, personal paths, logs). Pushed repo to private GitHub remote `rdwornik/corp-monorepo`. Added BACKLOG item #13 to sanitize real internal paths from fixtures and archives.
- Result: Remote `rdwornik/corp-monorepo` (private) up to date as of 2026-06-06. Sweep found: secrets CLEAN (zero committed values); client names present in config/source/fixtures (informational for private repo); personal paths (`1028120`, OneDrive paths) in `config/paths.toml`, scripts, and test fixtures — recorded as informational, remediation tracked in BACKLOG #13.
- Changes: `JOURNAL.md` (this entry), `BACKLOG.md` (added #13 sanitize-fixtures-archives item).
- Abandoned: —
- Next: Sanitize real internal paths per BACKLOG #13 when scoped.

### 2026-06-06 — Scoped CLAUDE.md conformance deep-audit (#75 closeout)
- Did: Ran a scoped CLAUDE.md conformance deep-audit (Dynamic Workflow, #75) against §6–§9, checking for stale references left by the machinery-c3 cleanup (2026-06-05). Identified 6 proposals (P1–P6): P1 `/boot` removed from §6 step 1 and §7; P2 `/evolve` removed from §7; P3 `verify` re-pointed as bundled/plugin skill (not user-dir); P4 `boot` skill bullet deleted from §8; P5 SessionStart hook description corrected to reflect `surface-closures.ps1` (ADR-70) instead of the stale "loads learned rules" description; P6(a) retry wrapper added to `load_status()` in `manifest.py` (2–3 retries, small backoff) per the §5 graduated rule. Variant (b) (soften the rule) was declined by operator — (a) ratified and implemented. Test stub added to `tests/extractor/test_manifest.py` covering concurrent-read / transient-failure case.
- Result: §6–§9 CLAUDE.md accurate as of 2026-06-06. §5 verify line passes — `load_status` has retry wrapper. Branch `chore/75-audit-closeout`, merged `--no-ff`.
- Changes: `JOURNAL.md` (this entry), `CLAUDE.md` (§6–§9 refresh, P1–P5), `src/corp/extractor/manifest.py` (retry wrapper in `load_status`), `tests/extractor/test_manifest.py` (transient-failure retry test).
- Abandoned: P6 variant (b) — soften the §5 graduated rule (operator declined; rule stands, code updated instead).
- Next: #75 closed. Continue ecosystem audit schedule per hub backlog.

### 2026-06-04 — Refresh drifted ARCHITECTURE.md counts (closes baseline F1–F5)
- Did/Result: Re-read ARCHITECTURE.md end-to-end, re-verified every count live; fixed 6 drifts (inbox 1161→951, database 705→542, type codes 19→22, client aliases 15→32, notes 1,972+→488, agents 5→6 — the agents one was mis-cleared by the baseline's hyphen-blind grep) and left the verified-correct ones (extract 1184, router 893, cli 18, actions 12, 5 repos, corp 40+); re-stamped last_reviewed 2026-06-04; deleted merged `docs/conformance-baseline`. Branch `docs/architecture-count-refresh`, merged `--no-ff`. Count-checker NOT built (that's #82/#84).

### 2026-06-04 — Conformance baseline review (Dynamic Workflow, advances #81)
- Did: Ran the read-only documentation-conformance pattern (validated on the .dev-knowledge hub, #81) on corp-monorepo for the first time — a Dynamic Workflow fanned out 3 verifiers (JOURNAL vs git, living-doc claims vs repo state, BACKLOG↔commits) → adversarial skeptic → digest; then Opus main-session re-ran every survivor's evidence command against live state. Write/Edit denied for the run (subagents auto-write otherwise); fleet-wide `git status --porcelain` tripwire clean (target repo untouched; dirty siblings predate the run by hours/months).
- Result: 18 raw → 8 survived skeptic → 5 VERIFIED REAL + 3 DOWNGRADED. All 5 real findings are one class — ARCHITECTURE.md count drift: notes 1,972+→488, client_aliases 15→32, inbox.py 1161→951, database.py 705→542, type_codes 19→22 (no existing gate covers prose counts). Downgraded: actions/ "12" (=12 files incl __init__), corp "40+" (54, technically true), [#5] JLR (legitimately open). All 5 agents ran Haiku 4.5 (per-agent routing still non-functional, CC 2.1.162; no model options set). Output spend 75k/150k; gross 247k is cache-inflated. Gate green: 2548 pass / 6 skip, ruff clean, no src/ churn (dev-check avoided per mutation gotcha). No fixes applied — findings are operator-triage proposals.
- Changes: `docs/audits/2026-06-04-conformance-baseline-digest.md` (new), this JOURNAL entry. Branch `docs/conformance-baseline`, merged `--no-ff` (no push). Hub/siblings NOT modified.
- Abandoned: nothing (single-pass baseline; new verifier domains + per-repo profile #82 are iteration 2).
- Next: Operator triage of the 5 count-drift findings (refresh ARCHITECTURE.md counts, re-stamp last_reviewed); #82 — add a deterministic count-verifier so non-LLM checks catch this class pre-emptively.

### 2026-06-03 — Track ruff drift as BACKLOG item
- Did: Added BACKLOG `[#12]` to track that committed `src/` has drifted from the current ruff config — `dev-check.ps1` runs `ruff format`+`ruff check --fix` in-place and reformats ~106 files on every invocation, surfaced 2026-06-03 during stale-branch resolution.
- Result: `[#12] [P3][S]` in BACKLOG "Safety & code health" theme; drift not yet cleaned (that's the task).
- Changes: `BACKLOG.md` (#12 added, grooming-log updated), `JOURNAL.md` (this entry). Branch `docs/backlog-ruff-drift`, merged `--no-ff` (no push). `src/` untouched.
- Abandoned: nothing.
- Next: Execute #12 — run ruff format+fix, review diff, commit.

### 2026-06-03 — Resolve 3 unmerged branches (preserve-then-delete)
- Did: Closed the 3 stale unmerged branches surfaced by the fleet sweep without losing content. Triaged every P1/P2 finding in `verify/codex-p1-findings` (superset of `feature/dead-code-audit`) and `chore/extract-p1-2-to-backlog-2026-05-28` against the current tree, extracted only still-live findings fresh into BACKLOG (current ADR-66 form), then force-deleted all three.
- Result: Preserved — **#10** path-traversal security finding (`cleanup/executor.py:68,85`, `is_relative_to`=0, STILL LIVE; was added in pre-migration old-format on the unmerged branch so it was absent from the current BACKLOG) and **#11** consolidated dead-code cleanup (H1–H4/M1/M3, all re-confirmed live 2026-06-03), under a new "Safety & code health" theme. Dropped as not-carried-over — P1-1 (`disk.py:351` `_guard_onedrive` FIXED), P1-3 (`_resolve_project_path(writable=True)`→`_guard_writable` FIXED), P2 vault single-writer (SUPERSEDED by ADR-27's actions/* carve-out, enforced by `test_vault_writer_invariant.py`), and the one-time audit scan artifacts (`.audit/*`, `find_orphans.py`, vulture/ruff dumps).
- Changes: `BACKLOG.md` (5th theme + #10/#11 + backbone/grooming-log), `JOURNAL.md` (this entry). Branch `chore/close-stale-branches`, merged `--no-ff` (no push). Then `git branch -D` of all three stale branches.
- Abandoned: P1-1/P1-3/P2 findings (verified already fixed/superseded in current code — not regressions); audit tooling branches' scan output (point-in-time artifacts).
- Next: Schedule #10 (security) for a hotfix; #11 dead-code cleanup is P3 backlog.

### 2026-06-03 — Consume hub doc-tooling hooks (ADR-71 pilot, first consumer)
- Did: First real consumer of the `.dev-knowledge` doc-tooling hook source repo (ADR-71). Added a `repo: ../.dev-knowledge` / `rev: 69558c7` stanza to `.pre-commit-config.yaml` consuming the hub's `toc-freshness` + `toc-generate` hooks (single-sourced, version-pinned). Inserted `<!-- TOC:START/END -->` markers in the 551-line ARCHITECTURE.md and generated a 40+ entry nested TOC via `toc-generate` (manual stage). Verified the gate fires: FAIL on missing markers, FAIL on stale TOC (throwaway header), PASS when fresh.
- Result: ADR-71 consumption contract validated end-to-end for the TOC path — consume ✓ / regen ✓ / gate ✓. Anchors GitHub-correct (`[CORE]` tags stripped from link text, kept in slug). corp gates stayed green: ruff + tach clean, pytest baseline held. **Codemap path DEFERRED, not done:** corp's codemap is hand-authored (ADR-51 amendment, "not generator-managed") and the hub generator produces a strictly-worse 13-node ALL-orphan graph (0 edges, 0 layers) on corp's single-package `src/corp/` layout — edge match keys on first dotted import component (`corp` ≠ bare names) and tach layer keys are dotted vs bare nodes. Recommendation: do NOT flip ADR-71 to "validated" yet; the codemap generator needs a hub-side fix first.
- Changes: `.pre-commit-config.yaml` (TOC hook stanza + pin/deferral note, `d764c79`); `ARCHITECTURE.md` (TOC markers + generated block, `3bf0192`); `.claude/skills/gotchas/gotchas.md` (codemap-generator-incompatibility gotcha); this JOURNAL entry. Branch `feat/consume-doctools-hooks`, merged `--no-ff` (no push). Hub NOT modified (consumed read-only).
- Abandoned: Codemap hook consumption + frozen→live regen (would overwrite curated diagram with broken orphan graph; blocked by hub generator limitation, ratified with operator).
- Next: Hub-side: teach the codemap generator to handle `corp.`-prefixed imports + dotted tach keys, then revisit corp codemap adoption + flip ADR-71 status. Rollout continues: ai-council, then corp-ops + corp-sca (need pre-commit bootstrapped first).

---

### 2026-06-02 — Ecosystem unification to the 7-file canonical standard (ADR-38 A6)

- Did: Unified corp-monorepo to the locked `.dev-knowledge` canonical standard (ADR-38 A6). Built `LESSONS.md` (seeded with two real corp lessons: ruff hook-version mismatch, VISION-routing drift). Added ARCHITECTURE §Key conventions/§Authority and governance/§Validators and enforcement/§Governing ADRs. Case-fixed CONTRIBUTING headings (`Branch naming`/`Commit style`) + added §Handoff process + a Backlog-id note. Migrated `BACKLOG.md` from the ADR-41/47 stream schema to the ADR-66 story-map; changed this file's H1 to the canonical `# Journal`.
- Result: `.dev-knowledge` structural audit passes (was 4 FAILs: missing LESSONS; ARCHITECTURE/CONTRIBUTING/JOURNAL spine gaps). 9 open backlog items preserved across 4 themes.
- Changes: `LESSONS.md` (new), `ARCHITECTURE.md`, `CONTRIBUTING.md`, `BACKLOG.md`, `JOURNAL.md` (this entry + H1).
- Backlog migration bridge (ADR-65 — done items leave; full text in git history at the pre-migration commit): three items already CLOSED before this migration left the active file —
  - *Action 7c — ruff select strictness* (closed 2026-05-28): kept lenient select `["E","F","I"]` as baseline (ADR-32); pre-commit ruff bumped to v0.15.8, 89 phantom I001 violations cleared.
  - *Action 6 — VISION §Values routing, resolved via Path B* (closed 2026-05-28, commit `0a9410c`): VISION §Values amended to "Deterministic per-domain routing"; deep-audit D2 closed.
  - *Action 6 — VISION §Values routing, original entry* (the preserved-for-history duplicate of the above).
- Abandoned: none — every open item preserved. The stale "story-map is `.dev-knowledge`-scoped, corp stays on ADR-41" BACKLOG note was removed (superseded by ADR-38 A6, which binds the story-map to all repos with proportional depth).
- Next: corp-ops + corp-sca-time-automation unification.

---

### 2026-06-02 — Coherence cleanup (follow-up to G1)
- Did: Doc-only cleanup on branch `chore/coherence-cleanup` — fixed CLAUDE.md §1 handoff ref to point at `../.dev-knowledge/docs/handoffs/` (ADR-36/60; corp carries no local handoffs dir); grounded 3 `check_doc_refs.py` `backtick:missing` cross-repo refs by adding the resolvable `../` prefix (PLAYBOOK/LESSONS/codex-AGENTS; targets verified to exist); added `last_reviewed: 2026-06-02` frontmatter to CLAUDE.md + CONTRIBUTING.md after genuine re-read (drift fixed first, then stamped); removed the regenerable git-ignored `.audit/` scratch.
- Result: `audit_repo` **11/11 PASS, 0 WARN, 0 FAIL** (was 10 PASS/1 WARN); `check_doc_refs.py` broken **3→0**; pytest 2524 passed/7 skipped + ruff clean after each commit; CLAUDE.md 156 lines (≤200); working tree fully clean. Merged `--no-ff`; branch deleted.
- Changes: `CLAUDE.md` (§1 handoff ref `931bcc6`; 3 cross-repo refs `6d11002`; +frontmatter `7f4351f`); `CONTRIBUTING.md` (+frontmatter `7f4351f`); removed `.audit/` (untracked); this JOURNAL entry.
- Abandoned: Nothing.
- Next: corp-monorepo universalization conformance complete — machine floor 11/11, coherence layer earned.

### 2026-06-02 — Universalization coherence audit (child-repo G1)
- Did: Ran the per-child-repo universalization coherence audit (G1) on branch `chore/universalization-conformance` off `main`. Imported `.dev-knowledge/scripts/audit.py` read-only and ran `audit_repo` (did NOT run the writing CLI). Performed the deeper coherence layer the 10 machine checks don't cover: BACKLOG schema vs current standard, ARCHITECTURE invariants vs code reality, CLAUDE.md ADR-currency, cross-doc coherence, freshness. Grounded every finding file:line; classified MECHANICAL vs DECISION-REQUIRED.
- Result: Machine floor moved from 1 FAIL → **GREEN (no FAILs)**; `canonical_freshness` FAIL → WARN (only the 2 standard-tolerated "no last_reviewed" WARNs on CLAUDE.md/CONTRIBUTING.md remain — child-repo-safe per the standard). 4 mechanical fixes landed (one revertable commit each). ARCHITECTURE re-read confirmed layer assignments match `tach.toml` exactly; VISION §Values routing claims verified against code (`extraction/routing.py` reads MyWork-resident `routing_map.yaml`; ContentRegistry; overnight/classifier; retrieve FTS5). 2524 passed / 7 skipped (baseline held). HARD criterion (coherence) **met** for everything in scope; the one open coherence question (BACKLOG vs ADR-64/65/66) was escalated, not guessed — operator chose **option C (status quo)**, so corp BACKLOG stays on ADR-41/47 with an additive `.dev-knowledge`-scoped clarifying note (no entries changed, no content removed). Operator gave merge GO.
- Changes: `VISION.md` (last_reviewed 2026-05-27→2026-06-02, `539333b`); `ARCHITECTURE.md` (last_reviewed bump, `1d336d5`); `CONTRIBUTING.md` (ADR count 30→31, `4c96e43`); `CLAUDE.md` (§6+§11 handoff refs ADR-42 v3→ADR-62 v4, `3482547`); `BACKLOG.md` (additive ADR-64/65/66 scope note, `af22bed`); this JOURNAL entry. Merged to `main` `--no-ff`; branch deleted.
- Abandoned: Story-map adoption (ADR-66) and done-items-leave purge (ADR-64 D1/ADR-65) for corp — operator chose C. Determination stands: ADR-64/65/66 are framed for `.dev-knowledge`'s own backlog and enforced only by `.dev-knowledge`-local hooks; cross-repo adoption is not mandated (ADR-62 precedent). The 3 retained `[closed]` items (one "preserved for history") were NOT removed (C = no deletion). Also not done: `last_reviewed` frontmatter on CLAUDE.md/CONTRIBUTING.md (WARN is standard-tolerated; scope creep).
- Next: G1 complete for corp-monorepo. Pre-existing observations (not in scope, for a future session): `check_doc_refs.py` flags 3 `backtick:missing` cross-repo refs in CLAUDE.md (exit 0, non-blocking); CLAUDE.md §1 line 15 points at local `docs/handoffs/*.md` which corp lacks (handoffs live in `.dev-knowledge`).

### 2026-05-28 — Resolve Action 6 (VISION §Values routing) via Path B
- Did: Deep-read all four "routing" modules (`extraction/routing.py`, `ingest/router.py`, `overnight/classifier.py`, `retrieve/engine.py`) to determine whether VISION's "one routing authority" claim reflected hidden duplication (Path A — consolidate) or aspirational drift (Path B — amend). Confirmed Path B: no cross-imports, no shared dispatch table, disjoint inputs/outputs, four genuinely distinct domain concerns sharing only the word "routing". Amended VISION.md §Values to "Deterministic per-domain routing" with inline provenance note preserving the Council-origin original. Closed BACKLOG Action 6 entry. Deep-audit finding D2 (HIGH) closed.
- Result: VISION.md §Values lines 73-74 replaced with accurate per-domain description + provenance HTML comment. BACKLOG Action 6 marked closed with summary; original entry preserved for history. Branch `docs/action6-vision-routing-2026-05-28` (1 commit: `0a9410c`) awaiting operator merge. No code changes; pytest unaffected (2524 prior).
- Changes: `VISION.md` (§Values routing value amended); `BACKLOG.md` (Action 6 closed); this JOURNAL entry.
- Abandoned: Path A (consolidate). Determination confirmed no duplication exists — consolidation would be a new architectural decision, not a drift fix; not warranted.
- Next: Operator merges `docs/action6-vision-routing-2026-05-28` to main (no Codex review — docs-only). Deep-audit D2 HIGH now closed; remaining audit findings tracked separately.

---

### 2026-05-28 — Close Action 7c (ruff strictness → ADR-32) + investigate Action 6 (VISION routing)
- Did: Closed the open ruff-select-strictness question (Action 7c from the universalization mega-session) by authoring ADR-32. Investigated Action 6 (VISION §Values "one routing authority" vs. actual distributed routing — deep audit D2 / CM-CF4) and produced a scope report with a recommendation. No code changes; docs only.
- Result: ADR-32 (`docs/decisions/ADR-32-ruff-select-strictness.md`) documents the lenient `["E","F","I"]` select as the intentional, accurate baseline. Repo is 0-error under this config (89 I001 violations cleared by the 2026-05-28 hook bump v0.4.0→v0.15.8). ADR-59 corp-monorepo visual-pattern retrofit is now unblocked. Action 6 investigation findings and recommendation (Path B — amend VISION.md, no Council needed) captured in BACKLOG Action 6 entry. Branch `docs/close-7c-investigate-action6-2026-05-28` awaiting operator merge.
- Changes: created `docs/decisions/ADR-32-ruff-select-strictness.md`; updated `BACKLOG.md` (closed Action 7c entry + new Action 6 entry with investigation findings); this JOURNAL entry.
- Abandoned: Action 6 implementation — investigation + report only per directive; operator must confirm Path A (Council) vs Path B (focused VISION.md edit) before any change.
- Next: Operator chooses Path A or B for Action 6. Path B = one focused session to amend VISION.md §Values lines 73-74; no Council. Path A = convene Council. Either way, merge this branch first. ADR-59 corp-monorepo retrofit is also unblocked.

---

### 2026-05-25 — ADR-27 implementation status audit
- Did: Read-only audit on branch `audit/adr27-status` resolving the two independent ADR-27 questions the prior handoff conflated — (Q1) is the ADR doc merged to `main`, (Q2) is the OneDrive implementation present. Verified via `git ls-files`/`git log`/`git merge-base`/`grep` against HEAD `32a47f8`; no execution, no source edits. Determined routing **branch (a)**.
- Result: Q1 — ADR doc PRESENT in `main` (commits `a6e3942`, `a5a6789` both confirmed ancestors); operator memory "drafted-on-branch, no merge witness" was stale, handoff's VERIFIED claim correct. Q2 — SPLIT: Decision 2/PR-4 (vault-writer invariant) already DONE (`tests/safety/test_vault_writer_invariant.py`), but Decision 1/PR-1–3 (OneDrive centralization) ABSENT — no `src/corp/safety/onedrive.py`, no `tests/safety/test_no_unguarded_writes.py`, zero `from corp.safety` imports. Three drift sites confirmed and split by remediation profile: `renderer.py:42,48` ValueError (documented intent, PR-2), `deck_actions.py:104→117` unguarded write (undocumented gap — flagged to not survive a "PR-2 done" closure), errors-module location `cleanup/errors.py` vs `safety/onedrive.py` (structural, PR-1+PR-3). Audit at `docs/audits/2026-05-25-adr27-status.md`.
- Changes: created `docs/audits/2026-05-25-adr27-status.md`.
- Abandoned: Nothing — audit-only scope; no implementation, no drift patches, no ADR drafting per directive.
- Next: ADR-27 Decision 1 PR-1 (foundation module `src/corp/safety/onedrive.py` at Tach foundation layer + no-cycle check). Open question for Rob: `docs/audits/2026-04-21-p1-verification.md` (cited in ADR §Related-work) is absent from `main` — recover/recreate or correct the citation.

---

### 2026-05-20 — Conformance gap audit: corp-monorepo vs `.dev-knowledge`
- Did: Authored read-only conformance-gap audit of corp-monorepo against every `.dev-knowledge` standard (ADRs 27–54 + PLAYBOOK/ESSENTIALS conventions + dev standards + Codex reviewer config + BACKLOG cross-references) on branch `docs/audit-corp-monorepo-conformance-gap`. Read all 28 `.dev-knowledge` ADRs directly (after a Phase-1 standards-side Explore agent's inventory was found incomplete — missed ~15 ADRs and mislabeled ADR-50 as Tach enforcement when it's actually machine-document encoding). Spot-verified corp-monorepo state: CLAUDE.md (148 lines, v2.1, 12 sections), VISION.md (Standard tier + scale L frontmatter + 6 mandatory sections), ARCHITECTURE.md at root (per ADR-38 A4), `tach.toml` (4 layers, 34 modules, `exact=true`), `.pre-commit-config.yaml` (ruff + tach + normalize-headers, no scope-tagging), BACKLOG.md (ADR-41 schema), JOURNAL.md (ADR-49 shape), `docs/decisions/` (30 corp ADRs), no AGENTS.md (deleted 2026-05-20 per ADR-54). Per the 2026-05-20 design decision (AskUserQuestion), included a dedicated section flagging corp's local ADRs that interact with or numerically collide with `.dev-knowledge` ADRs.
- Result: `docs/audits/2026-05-20-conformance-gap-vs-dev-knowledge.md` landed (single commit). Distribution: 17 CONFORMS, 3 PARTIAL, 2 GAP, 16 N/A, 2 UNKNOWN across the `.dev-knowledge` ADR set. The two GAPs are both communication/discoverability, not logic conflicts: (1) `.dev-knowledge` BACKLOG Cross-stream P2 "Phase 2 universalization rollout" still labels corp-monorepo "not yet started" while the 2026-05-18 work substantively executed Phase 2 — stale upstream label, **not corp-actionable**; (2) ADR-numbering namespace collision risk — corp's local ADR-27/30/31 share numbers with `.dev-knowledge` ADR-27/30/31 governing entirely different decisions, and CLAUDE.md §11 mixes both namespaces without prefix qualification. Three recommendations, all P3: disambiguate CLAUDE.md §4 vault-vs-repo naming, prefix CLAUDE.md §11 ADR references with their source namespace, flag upstream BACKLOG to refresh the stale label. No P1/P2 corp-side gaps surfaced — material conformance posture is strong.
- Changes: created `docs/audits/2026-05-20-conformance-gap-vs-dev-knowledge.md`.
- Abandoned: Nothing. Two PARTIALs (ADR-51 codemap auto-generation + CI freshness check, ADR-34 vault-vs-repo wording) and two UNKNOWNs (ADR-40 algorithmic tier verification, ADR-51 CI freshness check existence) all gated on upstream `.dev-knowledge` tooling — explicitly noted as such, not directives.
- Next: Triage the three P3 recommendations during the next opportunistic corp-monorepo session (lowest-cost is R1 + R2 — both are CLAUDE.md edits under 15 min combined).

---

### 2026-05-20 — Deep audit: corp-monorepo (file-state-verified)
- Did: Authored read-only deep audit of corp-monorepo on branch `docs/audit-corp-monorepo-deep`. Three Explore agents seeded the inventory (configs/ADRs, src/corp/ structure + tests, integrations + invariants), then deep reads verified every claim against cited file paths. Audit doc covers 12 sections — exec summary, scope/methodology, repo structure, config & dev standards, architectural invariants, safety & security, tests inventory, external integrations, 16 drift surfaces (severity-ranked), decision-record state (30 ADRs / 28 transcripts / 4 prior audits enumerated), open/pending items from BACKLOG/JOURNAL, and a 12-question verification appendix with CONFORMS/GAP/UNKNOWN classifications. Methodology contract: no execution, no source modifications, every claim file-path-cited.
- Result: `docs/audits/2026-05-20-corp-monorepo-deep.md` landed (803 lines, single commit). Top 5 risks: (R1 HIGH) `manifest.load_status()` lacks status.json retry wrapper at `src/corp/extractor/manifest.py:75-82`; (R2 HIGH) VISION-declared "one routing authority" is aspirational — routing code-distributed across 4+ modules; (R3 HIGH) ARCHITECTURE.md last updated 2026-03-30, missing 7 weeks of governance changes; (R4 MEDIUM) CONTRIBUTING.md stale on ADR count and Phase-1 violations; (R5 MEDIUM) magistrala pipeline end-to-end verification overdue since Council #24. Top 5 strengths: ADR-27 vault-writer invariant fully enforced (448-line AST scanner + runtime whitelist), OneDrive guards at all 4 known mutation sites with resolve-before-substring fail-closed semantics, Tach 4-layer model fully wired (exact=true + forbid_circular_dependencies=true + pre-commit + CI), GEMINI_API_KEY canonical with zero committed secrets, forward-slash convention 100% compliant (0 os.sep / os.path.join in src/corp/).
- Changes: created `docs/audits/2026-05-20-corp-monorepo-deep.md`.
- Abandoned: Nothing. Deferred to future sessions per drift findings: D1 (ruff config duplication), D3 (Gemini pricing externalization), D4 (ARCHITECTURE.md refresh), D5 (README count drift), D8 (magistrala integration test), D9 (load_status retry fix), D10 (CONTRIBUTING refresh).
- Next: Triage the 16 drift findings; D9 (status.json retry) is the only one with active-regression-of-a-graduated-rule character and merits the soonest fix.

---

### 2026-05-19 — CLAUDE.md rewrite to v2.1 (Chunk 5, ADR-53 conformance)
- Did: Rewrote corp-monorepo CLAUDE.md from pre-template structure to the v2.1 12-section template on branch `docs/chunk5-corp-monorepo-claude-md-v21`. Confirmed ARCHITECTURE.md already contains all architecture content (Source Layout, CLI Reference, Configuration Architecture, Key Invariants, Dependency Layers) — no ARCHITECTURE.md changes needed. Distributed all current content per the approved disposition map: architecture → §3 pointer; conventions → §4; critical rules + 4 learned rules with verify: lines → §5; session protocol + handoff pointer → §6; ADRs → §11. Added two approved additions: §2 Purpose line (from VISION.md) and §10 AGENTS.md durable guard (Codex review config — outside ADR-53 scope).
- Result: CLAUDE.md is ADR-53 conformant at v2.1; all rules preserved; no content dropped; AGENTS.md untouched. Line count ~172 (under 200 budget).
- Changes: `CLAUDE.md` rewritten to v2.1 12-section template. `ARCHITECTURE.md` unchanged (no gaps found).
- Abandoned: Nothing — AGENTS.md deliberately untouched (Codex code-review config, not an ADR-53 instruction contract).
- Next: `.dev-knowledge` correction of mislabeled ARCHITECTURE.md entry (separate session in `.dev-knowledge` repo).

---

### 2026-05-20 — Delete corp-monorepo AGENTS.md entirely (ADR-54 complete)
- Did: Deleted `AGENTS.md` on branch `docs/delete-corp-monorepo-agents-md`. Confirmed `ARCHITECTURE.md` carries the vault-writer invariant (Key Invariants §1, line 393) before deleting the pointer. The stale-package-references check was already present in `CLAUDE.md` §10 — no relocation needed. Rewrote `CLAUDE.md` §10 bullet to a factual note (no per-repo `AGENTS.md`; global config at `~/.codex/AGENTS.md`, ADR-54). Removed stale `AGENTS.md` entry from `CONTRIBUTING.md` Architecture Reference. Found and removed stale `AGENTS.md` entry from `scripts/check_doc_refs.py` DOCS list (the `if not doc.exists(): continue` guard made it harmless, but it was a live script with a dead reference). Verified final grep: all remaining `AGENTS.md` references are in historical/immutable docs (ADRs, audits, transcripts, JOURNAL).
- Result: `AGENTS.md` deleted; corp-monorepo has no per-repo Codex overlay — consistent with `.dev-knowledge` and `ai-council`. ADR-53/ADR-54 effort complete.
- Changes: deleted `AGENTS.md`; `CLAUDE.md` §10 bullet updated; `CONTRIBUTING.md` Architecture Reference line removed; `scripts/check_doc_refs.py` DOCS list cleaned.
- Abandoned: Nothing.
- Next: ADR-53/ADR-54 effort is complete across all repos.

---

### 2026-05-19 — Retire AGENTS.md to thin per-repo Codex overlay (ADR-54)
- Did: Reduced `corp-monorepo/AGENTS.md` from 133-line full Codex reviewer config to a 17-line per-repo overlay on branch `docs/retire-corp-monorepo-agents-md`. Verified all Architecture Context sub-parts (repo structure, module table, dependency rule, layer list, invariants, databases, config) are covered by `ARCHITECTURE.md` — nothing dropped without coverage. Retained exactly two genuinely repo-specific review rules: vault-writer invariant as an active-check pointer to `ARCHITECTURE.md`/ADR-27 (not a restatement — avoids creating a drift pair), and stale package-name references (`corp_by_os`, `corp_os_meta`, `corp_knowledge_extractor`). Corrected `CLAUDE.md` §10 guard, which previously said "Do NOT modify/delete AGENTS.md" — now accurately describes AGENTS.md as a per-repo overlay with the global config at `~/.codex/AGENTS.md` (ADR-54). Updated `CONTRIBUTING.md` line 121 reference. Left all historical/immutable docs (ADRs, audits, transcripts, JOURNAL) untouched.
- Result: `AGENTS.md` is 17 lines; `CLAUDE.md` §10 is accurate; `CONTRIBUTING.md` reference updated. No repo-specific review rules dropped. No drift pairs introduced.
- Changes: `AGENTS.md` (133→17 lines); `CLAUDE.md` §10 bullet corrected; `CONTRIBUTING.md` Architecture Reference line updated.
- Abandoned: Nothing.
- Next: ADR-54 is complete across corp-monorepo. No follow-ups needed in this repo.

---

### 2026-05-18 — Rollout cleanup: three audit loose ends closed
- Did: Ran post-rollout completeness audit against the 2026-05-18 universalization gap-review; confirmed 23/24 gap-items closed; identified three loose ends and executed cleanup on branch `docs/rollout-cleanup`. (1) Deleted `docs/handoffs/2026-04-15-handoff.md` (sole occupant; contradicted ADR-36/42 by keeping a handoff in a target repo). (2) Deleted `templates/ADR-template.md` (per-repo template not mandated by ADR-38 and already silently drifted from `.dev-knowledge/templates/ADR-template.md` — missing `Amends:` and `Source:` fields); repointed `docs/decisions/README.md` step 1 at the `.dev-knowledge` canonical, mirroring the cross-repo phrasing CLAUDE.md uses for ADR-42 handoffs. (3) Promoted the two date-prefixed decommission notes to numbered ADRs in the canonical template shape: `2026-05-18-retire-changelog.md` → `ADR-30-retire-changelog.md`; `2026-05-18-retire-single-file-handoff.md` → `ADR-31-retire-single-file-handoff.md`. Skipped ADR-28/29 (reserved for future distillations of `DECISION_28_community_patterns_research` and `DECISION_29_spec_kit_kiro_research` — pairing convention preserved); README.md carries a one-paragraph note explaining the skip.
- Result: `docs/handoffs/` and `templates/` directories gone (both became empty after their sole file was removed). `docs/decisions/README.md` indexes ADR-01..ADR-27 plus ADR-30, ADR-31. The canonical ADR template lives only in `.dev-knowledge/templates/` per ADR-36 read-only contract. Four commits on `docs/rollout-cleanup`, each narrow + revertable; pre-commit ruff/tach/header-normalizer skipped (no `.py` or dated-log files touched after the JOURNAL step itself). Universalization rollout complete.
- Changes: deleted `docs/handoffs/2026-04-15-handoff.md`; deleted `templates/ADR-template.md`; edited `docs/decisions/README.md` (repoint step 1, add ADR-30/31 rows + skip-note); deleted `docs/decisions/2026-05-18-retire-changelog.md` and `docs/decisions/2026-05-18-retire-single-file-handoff.md`; created `docs/decisions/ADR-30-retire-changelog.md` and `docs/decisions/ADR-31-retire-single-file-handoff.md`.
- Abandoned: ADR-28/29 squatting (reserved for future Council distillations of `DECISION_28`/`DECISION_29`). `/review` skipped intentionally — pure doc/meta, zero code logic, Codex would have nothing to assess.
- Next: None — universalization rollout complete. Merge `docs/rollout-cleanup` into `main` with `--no-ff`.

### 2026-05-18 — ADR-27 PR-4 vault-writer invariant narrowing
- Did: Added `VaultZone.METADATA` and `VaultZone.BRIEFS` as semantic action-write categories in `src/corp/models.py` (values `"metadata"` / `"briefs"` — NOT physical vault directories; `resolve_vault_path` raises `ValueError` if either is passed). Added `is_writable_by_actions` predicate to `src/corp/vault_io.py` with whitelist `{DASHBOARDS, METADATA, BRIEFS}` matching ADR-27 line 122 verbatim. Implemented AST scanner at `tests/safety/test_vault_writer_invariant.py` that walks every `src/corp/actions/*.py`, resolves each file-mutation primitive (`Path.write_text`/`write_bytes`/`replace`/`unlink`/`rmdir`, `shutil.copy*`/`move`/`rmtree`, `os.remove`/`rename`/`unlink`, `open(..., write-mode)`) through local-variable assignment chains to both its first vault-path segment AND its leaf filename, then maps the `(zone, leaf)` pair to a category via `_classify`. PROJECTS-zone writes are only authorized for three leaves — `project-info.yaml` + `index.md` (→ METADATA) and `brief.md` (→ BRIEFS); any other PROJECTS-zone leaf is flagged. Embeds three self-test fixtures (SOURCES violation, unclassified PROJECTS-zone leaf, clean METADATA write) so a silently-broken scanner fails its own test. Tolerates the `00_dashboards` string-literal drift in `analytics_actions.py` via `_ZONE_ALIASES` (drift itself out of scope). Narrowed the "SOLE vault writer" wording in ARCHITECTURE.md, CLAUDE.md, AGENTS.md, README.md to "sole writer for `02_sources/` `.md` notes" and named the three categories explicitly; added "Amended by ADR-27" line on ADR-23.
- Result: Scanner finds the 7 inventoried write sites and classifies all to whitelisted ADR-27 categories — 2 DASHBOARDS (`analytics.md`, `attention.md`), 4 METADATA (3× `project-info.yaml` + 1× `index.md`), 1 BRIEFS (`brief.md`). Zero `02_sources/` violations and zero unclassified PROJECTS-zone leaves. No production code rewrites were needed (ADR-27 line 149's inventory claim holds). Full suite: 2548 passed, 6 skipped, no regressions. `tach check` green. Predicate sanity: DASHBOARDS/METADATA/BRIEFS accepted; PROJECTS/SOURCES/SYSTEM rejected. `resolve_vault_path(VaultZone.METADATA, ...)` raises with a clear ADR-27 reference. Injected-violation rerun: scanner correctly flagged `cfg.vault_path / "projects" / "smuggle.md"` at the exact `file:lineno` with `zone=PROJECTS leaf='smuggle.md' -> UNCLASSIFIED`, then reverted to a clean tree.
- Changes: `src/corp/models.py` (VaultZone.METADATA + BRIEFS), `src/corp/vault_io.py` (predicate, whitelist, resolve_vault_path guard), `tests/safety/__init__.py` (new), `tests/safety/test_vault_writer_invariant.py` (new — AST scanner with leaf-filename classification + three self-tests), `ARCHITECTURE.md`, `CLAUDE.md`, `AGENTS.md`, `README.md`, `docs/decisions/ADR-23-monorepo-internal-architecture.md` (amendment cross-ref).
- Abandoned: Looser `{DASHBOARDS, PROJECTS}` whitelist (an earlier draft on this branch) — rejected because PROJECTS is a superset of METADATA+BRIEFS and would authorize any `projects/{pid}/*` write, broader than ADR-27 line 122's explicit named whitelist.
- Next: ADR-27 PR-1/2/3 (OneDrive centralization — `src/corp/safety/onedrive.py`, four guard-site migrations, `renderer.py` `ValueError`→`OneDriveSafetyError`, `deck_actions.py:104` gap, `test_no_unguarded_writes.py` AST scanner — separate branches per ADR-27's migration plan). Resolve the `dashboards/` vs `00_dashboards/` directory drift in `analytics_actions.py:99` in a separate chore branch.

### 2026-05-18 — Universalization rollout (VISION, gap review, ARCHITECTURE relocation, handoff retirement)
- Did: Added Standard-tier `VISION.md` at repo root (ADR-33) and updated `CLAUDE.md` + `AGENTS.md` to require it on session start. Ran the universalization gap review and archived the report under `docs/audits/`. Relocated `ARCHITECTURE.md` to repo root per ADR-38 A3. Retired the legacy single-file handoff: deleted `docs/HANDOFF.md` and `scripts/update_handoff.py`, seeded `BACKLOG.md` from the open items, repointed CLAUDE.md's Session Handoff section at the `.dev-knowledge` ADR-42 convention, and added `docs/decisions/2026-05-18-retire-single-file-handoff.md`.
- Result: Repo aligned with universal Corporate-OS doc layout — VISION at root, ARCHITECTURE at root, BACKLOG at root, JOURNAL append-only, handoffs owned by `.dev-knowledge`. Branches `docs/add-vision`, `docs/universalization-review`, `docs/architecture-to-root`, `docs/handoff-retirement` merged into `main` via `--no-ff`.
- Changes: `VISION.md` (new), `ARCHITECTURE.md` (relocated to root), `BACKLOG.md` (new), `CLAUDE.md`, `AGENTS.md`, deleted `docs/HANDOFF.md` and `scripts/update_handoff.py`, added `docs/audits/<gap-review>.md` and `docs/decisions/2026-05-18-retire-single-file-handoff.md`.
- Abandoned: None.
- Next: Workstream B (this branch — retire `CHANGELOG.md`, JOURNAL shape adoption, JOURNAL catch-up). Workstream C — ADR template + `Decommission:` field, header normalizer port, `docs/decisions/README.md` index ADR-22..27, ADR-27 number collision.

### 2026-04-24 — Council #28 / #29 research debate transcripts archived
- Did: Archived AI Council #28 and #29 research-debate transcripts into `docs/decisions/transcripts/`.
- Result: Council transcript history kept current; canonical filenames preserved per the manual-archival convention.
- Changes: `docs/decisions/transcripts/` (two new council-out files for #28 and #29).
- Abandoned: None.
- Next: ADR-27 implementation prompts (OneDrive centralization + vault writer amendment).

### 2026-04-22 — ADR-27 drafted: OneDrive safety centralization + vault writer invariant amendment
- Did: Drafted ADR-27 combining two decisions — OneDrive safety centralization (Option C, sourced from AI Council 2026-04-22, 3-of-4 consensus) and the vault-writer invariant amendment (Option B, narrow invariant with zone whitelist; codifies the actual working architecture at 8 action write sites). Cross-referenced `ARCHITECTURE.md` and archived the council transcript. Invariant wording itself unchanged until implementation PRs land (3 PRs for OneDrive, 1 for vault writer).
- Result: ADR-27 lands in `docs/decisions/` with the council transcript archived. Implementation deferred to follow-up PRs.
- Changes: `docs/decisions/ADR-27-*.md` (new), `docs/decisions/transcripts/` (council OneDrive debate), `ARCHITECTURE.md` (cross-reference), `CHANGELOG.md` (recorded ADR-27 drafting — this was the final use of the changelog before retirement).
- Abandoned: None.
- Next: 3 OneDrive implementation PRs + 1 vault-writer narrowing PR per ADR-27.

### 2026-04-21 — OneDrive safety P1 hotfix (+ symlink-bypass amendment)
- Did: Landed three regression tests (verified failing on `main` before fixes), then shipped P1-1 `execute_plan` guard, P1-2 `moves.yaml` schema + traversal guard, and P1-3 `_resolve_project_path` writable kwarg. After Codex review flagged H-C1/H-C2, amended all four OneDrive guard sites (`disk.py`, `_helpers.py`, `executor.py`, `renderer.py`) to resolve paths *before* the substring check, and split schema-vs-runtime traversal tests to assert the exact exception per layer (Codex M-C1). Merged `hotfix/onedrive-safety-p1` to `main`. Docs updated in `ARCHITECTURE.md` and `.claude/skills/gotchas/gotchas.md`; `AGENTS.md` deferred to ADR-27.
- Result: 2495 → 2515 tests green; +6 symlink-bypass tests, +2 runtime-guard unit tests; zero regressions. P2 (vault single-writer) deliberately deferred to ADR-27.
- Changes: `src/corp/.../cleanup` (disk.py, executor.py), `src/corp/.../actions` (_helpers.py, built_in_actions), `src/corp/project/renderer.py`, new regression tests under `tests/`, `ARCHITECTURE.md`, `.claude/skills/gotchas/gotchas.md`, `docs/audits/` (Codex review + re-review outputs), `CHANGELOG.md`.
- Abandoned: P2 (vault single-writer) intentionally deferred to ADR-27 — see ADR-27 entry below for follow-up.
- Next: ADR-27 to consolidate OneDrive centralization + vault-writer invariant.

## 2026-04-15 (Step 12 — 4-layer taxonomy reconciliation)
- **Did:** Replaced 7-layer (L0-L6/L0-L9) model with 4-layer Tach taxonomy (foundation/core/orchestration/interface) in AGENTS.md, ARCHITECTURE.md, and 5 per-module READMEs (cli, schema, extraction, opportunity, project). Single source of truth: tach.toml. Zero stale references remaining in living docs. docs/archive, docs/decisions, docs/audits preserved as frozen historical record.
- **Failed:** Nothing.
- **Next:** Magistrala verification — pipeline still unverified end-to-end since Council #24 MyWork restructure.

## 2026-04-15 (Tach Phase 2)
- **Did:** Resolved 6 baseline Tach violations by reclassifying project_resolver (orchestration→core) and query_engine (interface→orchestration). Ran tach sync to clean stale depends_on entries (exact=true flagged them as unused after reclassification). tach check clean. Zero Python changes.
- **Failed:** Nothing.
- **Next:** Step 12 — reconcile AGENTS.md and ARCHITECTURE.md to use 4-layer taxonomy (foundation/core/orchestration/interface). Currently docs describe 7-layer model, tach.toml uses 4-layer. Active confusion source.

### 2026-04-15 — Tach adoption Phase 1
- **Did:** Bootstrapped tach.toml with 4 layers (foundation/core/orchestration/interface), 34 modules. corp.ingest correctly classified as orchestration (not core) after Codex audit found 3 upward deps in router.py:18,653,743. Ran tach sync — found 6 baseline violations in 3 dependency pairs (intent_router→project_resolver, llm_router→project_resolver, actions→query_engine); documented in docs/audits/2026-04-15-tach-baseline-violations.md. Wired tach check into pre-commit (local hook, triggers only on src/corp/*.py changes) and created .github/workflows/tach.yml (pinned v0.34.0). Added CONTRIBUTING.md with tach sync cultural rules. Replaced AGENTS.md import-direction check with Tach reference. Created ADR-26. **2495 tests passing, 0 failed.** 8 commits, merged to main.
- **Failed:** `always_run: true` in pre-commit hook blocked non-Python commits — removed; hook now triggers only when src/corp/*.py files are staged (correct behavior).
- **Next (Step 12, separate PR):** Update AGENTS.md + ARCHITECTURE.md to use 4-layer taxonomy (foundation/core/orchestration/interface) replacing 7-layer model. Two tach reclassifications resolve all 6 baseline violations: corp.project_resolver core→orchestration(wait, core), corp.query_engine interface→orchestration. See docs/audits/2026-04-15-tach-baseline-violations.md.

### 2026-03-30 — Diagrams v4 Pipeline
- **Did:** Audited per-module READMEs: 12 existed, 1 generated (actions/). Created docs/diagrams/conventions.yaml (style guide, 31 lines). Generated 3 C4 diagrams from ARCHITECTURE.md: system-context (4 internal + 7 external nodes, 11 edges), container-module (4 layers, 14 nodes, 13 edges, vertical layout), magistrala-pipeline (4 phases, 15 nodes, side-channel DBs). All diagrams use 13px font, dark mode themeVariables, classDef colors per layer. Rendered SVGs via mmdc 11.12.0. Removed orphaned README.md from docs/diagrams/. Process: ARCHITECTURE.md + conventions.yaml -> .mermaid -> .svg (Council #25). **2495 tests passing, 0 failed.** 7 commits, merged to main (fast-forward).
- **Failed:** render-diagrams.ps1 Join-Path fix (step 8) was already applied in prior commit 9db4302 — no-op.
- **Next:** Magistrala verification. MISC rate measurement.

## 2026-03-30 (Codex audit fixes)
- **Did:** Fixed 6 findings from first Codex audit: (1) rfp_only filter dropped during product expansion in retrieve() — 1-line bug fix; (2) naming_config.py moved from ingest/ to schema/ — fix layer violation, shim left in ingest/ for compat, all 8 import sites updated; (3) schema normalize --in-place deprecated — now reports instead of writing vault files directly; (4) OneDrive safety guard added to project/renderer.py; (5) note paths in retrieve engine now resolved against vault_root, silent OSError catches now log at DEBUG; (6) CKE manifest paths switched to .as_posix() — forward slashes per invariant. **2495 tests passing, 0 failed.** Merged to main.
- **Failed:** Nothing.
- **Next:** Magistrala verification. MISC rate measurement.

### 2026-03-30 — P0+P1 error handling + scripts fix (Code Quality Audit)
- **Did:** Fixed all 15 error-handling items from audit: 5 critical `except Exception: pass` → specific types + logging (`built_in_actions.py` × 3, `ingest/router.py` × 2); 9 high-severity broad catches narrowed (`integrity.py` × 5, `vault_io.py` × 3, `task_manager.py`, `index_builder.py` × 5, `retrieve/engine.py`). Fixed 4 broken scripts (`packages/` → `tests/extractor/fixtures/`; stale `sys.path` inserts removed; REPO_ROOT depth fixed). Archived 6 one-time migration scripts to `scripts/archive/`. Added `__main__` guards to 3 scripts. Removed hardcoded username from `project/cli.py`. `llm_router.py:212` kept broad — google-genai raises unknown exception hierarchy, already logs. Work landed on `feat/project-scoped-gotchas` (pre-commit stash cycle switched branches after 2nd commit). **2412 tests passing, 0 failed.**
- **Failed:** `llm_router.py` narrowed exception broke `test_api_failure` (mock raises bare `Exception`); reverted. Pre-commit stash/restore switched active branch mid-session — all commits on `feat/project-scoped-gotchas` instead of `fix/p0-p1-error-handling-scripts`.
- **Next:** Merge `feat/project-scoped-gotchas` to main. P2: refactor `extract_knowledge()` (235 lines), `process_file()` (218 lines), `ingest_folder()` (216 lines). Standardize config access pattern.

## 2026-03-29 session 5 — Package consolidation (6 → 1 unified src/corp/)
- **Did:** Completed `feat/consolidate-packages` branch: 4 prior commits moved all 6 packages to `src/corp/`, unified `pyproject.toml`, updated all imports to `corp.*` namespace, removed old `packages/` directory. This session: fixed 6 remaining test failures (RFP CLI smoke cwd resolution 2→3 levels, naming_config test missing `extension_hint` check, `light_scan` `time.time()`→`time.perf_counter()` for Windows precision). Updated CLAUDE.md, `config/agents.yaml`, `.ecosystem/MASTER_HANDOFF.md` for new layout. Verified zero old import references (`corp_os_meta|corp_knowledge_extractor|corp_by_os` etc = 0 matches). All 4 CLIs working (`corp`, `cke`, `cpe`, `com`). **2,404 tests passing, 0 failed.** Merged to main.
- **Failed:** Ruff pre-commit auto-fixed `batch_api.py` on first commit attempt — re-staged and committed successfully.
- **Next:** Corp-rfp-agent Click CLI migration. 30-day skill eval (due 2026-04-25). MinHash wiring. Ontology Q4. RFP Federation (ADR-22).

## 2026-03-29 session 4 — Council #23 Phase 3+4 (ADR-23 Q3/Q4/Q5)
- **Did:** Flattened 3 sub-packages: `doctor/integrity.py` → `integrity.py`, `freshness/scanner.py` → `freshness_scanner.py`, `extraction/non_project/` (5 files) → `extraction/`. Max path depth 6→3 (relative to src). Centralized `parse_llm_json` + `normalize_string_list` in corp-os-meta: added `log.error` before raise; moved `normalize_string_list` from CKE utils to corp-os-meta; deleted CKE `utils.py` entirely (8 import sites updated). Deleted 4 confirmed dead files in corp-rfp-agent: `clean_kb.py`, `scan_kb.py`, `kb_to_markdown.py`, `_paths.py` (test_cli_smoke.py updated). corp-os-meta: 133 pass; CKE: 863 pass; rfp-agent: 179 pass; corp-by-os: 990 pass.
- **Failed:** Pre-commit ruff caught `UP038` (`isinstance(x, (int, float))` → `int | float`) in `contract.py` — fixed manually. Cherry-pick workflow needed to align doctor/freshness commits across phase2/phase3 branches due to background task switching branches accidentally.
- **Next:** Corp-rfp-agent Click CLI migration. 30-day skill eval (due 2026-04-25). MinHash wiring. Ontology Q4.

## 2026-03-29 session 3 — Phase 2 subprocess boundary fix (ADR-23 Q1)
- **Did:** Rewrote `overnight/cke_client.py` (180 → 280 lines) to use subprocess instead of direct CKE imports. Enforces architecture rule: corp-by-os → CKE must use process boundary. `is_available()` uses `shutil.which("cke")`; `extract_batch`/`extract_sync` run `cke process-manifest` with `capture_output=True, encoding="utf-8", errors="replace"` and regex-parse stdout summary ("Done: N", "Errors: N", etc.); `scan_local` uses `cke scan -o <tmp.json>`; `load_cke_config()` reads settings.yaml directly; `estimate_cost()` → NotImplementedError (dead function, no callers). 1015 tests pass, 1 skip. Branch: `feat/phase2-subprocess-boundary`, commits `663a05d` + `775a7d3`. Zero remaining `corp_knowledge_extractor` runtime imports in corp-by-os.
- **Failed:** Ruff E402 (`import os as _os` after constant) — moved `os` import to top-level block.
- **Next:** Merge `feat/phase2-subprocess-boundary` to main. Phase 3 (ADR-23 Q2 remaining) or ADR-22 (RFP federation).

## 2026-03-29 session 2 — Phase 1 CLI modularization (ADR-23 Q2)
- **Did:** Split `cli.py` (3,574 lines, 71 commands) into `cli/` package with `__init__.py` + `_common.py` + 16 domain modules (project, vault, template, index, rfp, task, system, workflow, query, analytics, misc, retrieve, extract, cleanup, ingest, overnight). `__init__.py` thinned to 131 lines (imports + group def + 33 add_command calls). Updated 4 test files (patch targets for get_config; overnight private helper imports). 1014 tests passing. CLI snapshot captured to `eval/cli_snapshot_phase1/` — only invocation name differs vs baseline. Merged via feat/phase1-cli-modularization (commits f7d94ab → 06eb571).
- **Failed:** Ruff pre-commit hook auto-fixed files on first attempt (import sorting, blank lines) — required re-stage and re-commit. Pattern documented.
- **Next:** Phase 2 (further CLI refactoring per ADR-23) or other ADR-23 Q2 work.

## 2026-03-29 session 1 — Council #23 Phase 0 prerequisites
- **Did:** Completed all Phase 0 gates for ADR-23: CKE call volume (3/run, no batching needed), cli.py shared state audit (71 commands, 14-module split plan), CLI help snapshot (55 files in `eval/cli_snapshot_2026-03-28/`), dead code verification (4 corp-rfp-agent files confirmed dead; `kb_to_markdown.py` needs coordinated test update on deletion). MASTER_HANDOFF.md updated (Council 22→23, ADR-23 entry, Open Decisions phases 1–4). Merged `chore/council23-phase0-prerequisites` to main.
- **Failed:** Pre-existing ruff E501 (`query_engine.py:389,423`) and integration test (`IMG` type code) — not introduced, not fixed.
- **Next:** Phase 1 (CLI split): create `cli/` directory with 14 domain modules + `_common.py`; use `eval/cli_snapshot_2026-03-28/` as regression baseline.

## 2026-03-28 session 4 — archive naming cleanup
- **Did:** Enforced `{YYYY-MM-DD}_{TYPE}_{description}.ext` naming on all `.ecosystem/archive/` files. Renamed 13 non-compliant files (date-at-end and undated variants). All 22 archive files now comply. Merged `chore/archive-naming-cleanup` to main.
- **Failed:** -
- **Next:** Per-note v2/v3 deletions (Rob confirms). RFP federation (ADR-22). sandbox_apply.py + doc_type_classifier pattern expansion. MinHash wire into inbox.

## 2026-03-28 session 3 — Phase 4 pending cleanup
- **Did:** v2/v3 01_Product_Docs quality comparison (36 notes matched) — v3 wins 20/36 but NOT clear upgrade: 2 v3-empty files (LifeScience_session1v2, Platform_Editedv2) must keep v2; total facts nearly equal (860 v2 / 850 v3). Cognitive_Friday vault cross-ref: both extractions already ingested. Sandbox review summary for Rob (2.4 GB, 53% MISC rate, apply step not built). 4 rebuild scripts archived to scripts/archive/. Phase 4 resolution report written. All tests green (1015+863+183+133+124+62). Merged chore/phase4 to main.
- **Failed:** -
- **Next:** Per-note v2/v3 deletions (Rob confirms). RFP federation (ADR-22). sandbox_apply.py + doc_type_classifier pattern expansion. MinHash wire into inbox.

## 2026-03-28 session 2 — repo audit + cleanup + governance
- **Did:** Full monorepo audit (plans archived). Phase 2 safe deletions (5 GB freed). Phase 3 governance: ADR-22 written, docs/ date-prefixed, .ecosystem/ root clean, CLAUDE.md + MASTER_HANDOFF.md counts updated (21→22 ADRs). All tests passing. Merged chore/phase3 to main.
- **Failed:** -
- **Next:** Implement ADR-22, .sandbox/ review (Rob), v2/v3 _outputs/ audit.

### 2026-03-28
- **Did:** SQL analytics MVP (6/10 benchmark queries). People added to FTS. Gemini 2.0 Flash-Lite for Tier 2 (-75% cost). Scripts/ to Dev/ migration (11 files, 2673 DB rows). .ecosystem consolidated. ADRs synced (#13-#21). Phase 1 cleanup (archives deleted). Corp-pdf-toolkit archived. Council #22 RFP federation debate. Venvs recreated. Full health check passed.
- **Failed:** -
- **Next:** Ontology Q4 (canonical product map). RFP federation implementation. File renames (585 files). MinHash wire into inbox.

## 2026-03-27 MinHash near-duplicate detection

- **Did:** Implemented `ingest/dedup.py` — MinHash signatures (128 perms, word 3-grams), `content_signatures` table in ops.db, `check_near_duplicate()` pipeline hook (after light_scan, before CKE), `get_dedup_report()` for `corp dedup-report` CLI command. Installed datasketch 1.9.0. 24 new tests, all pass. Full suite: **992 passed, 1 skipped**.
- **Design:** Signatures upsert on re-ingest. LSH index is rebuilt in-memory per query (acceptable for current vault size). Never auto-deletes — report only. `check_near_duplicate` is fail-open (ImportError/any exception → empty list, no pipeline disruption). `datasketch` added as optional dep `[dedup]`.
- **Next:** Wire `check_near_duplicate()` into `inbox.py` process_file() after light_scan call. Consider persisting LSH index if query latency grows with vault size.

## 2026-03-26 hybrid TF-IDF classifier pipeline

- **Did:** Full dual-vectorizer hybrid classifier — 8 steps: (1) Locked stratified 80/20 train/test split (`create_classifier_split.py` → 248 train, 62 test). (2) Trained `LogisticRegression` with char n-gram filename vectorizer + word n-gram content vectorizer, JSON serialization (no pickle) — CV 85.5% combined, +3.2pp content uplift. (3) JSON loader `hybrid_loader.py` with `lru_cache`, zero pickle risk. (4) One-time test eval: **85.5% hybrid vs 53.2% regex (+32.3pp)**, 0 high-confidence errors; at 0.5 threshold → 100% acc on 45% of files, 18% LLM fallback. (5) `classify_doc_type_hybrid()` integrated into `doc_type_classifier.py` — TF-IDF → regex → None pipeline with `USE_TFIDF` flag. (6) `eval.py` updated with three-way comparison section (1b). (7) 11 tests in `test_hybrid_classifier.py`. (8) Full suite: **863 CKE tests pass**. Merged `feat/hybrid-classifier` to main.
- **Errors:** ruff E402 on multi-line imports needed `# noqa` on `from ... import (` line not inner line. ruff E741 ambiguous `l` → `lbl`. `multi_class` removed in sklearn 1.7+ (lbfgs multinomial default).
- **Next:** Wire `classify_doc_type_hybrid()` into live extraction pipeline (inventory.py or tier_router.py). Consider expanding enriched training set for higher content %.

## 2026-03-26 light_scan module + classifier/tag improvements

- **Did:** (1) Classifier: added 6 high-priority filename patterns to `doc_type_classifier.py` (cognitive.shorts/friday, demo2win, iso22301/cybersecurity, extended product_doc/architecture terms) — accuracy 51.3% → **57.1%** (+18 correct, 0 false positives). Fixed architecture pattern ordering bug (cognitive content was matching architecture before training). (2) Tags: added `inventory-ops-agent`, `logistics-emissions-calculator`, `demand-edge` to `taxonomy.yaml` + `_TAG_ALIASES` + `product_aliases.yaml` — mean tag score 0.791 → **0.797**. (3) Light scan: implemented `light_scan.py` (Council Decision #19) — `ScanResult` dataclass with separate `filename_text`/`content_text` feature spaces, 7 format scanners (pptx/docx/pdf/xlsx/csv/txt-md/mp4), tiered fault tolerance (`full`/`degraded`/`filename_only`). 25 tests all pass. (4) Enrichment: `enrich_training_data.py` retroactively scanned 310 training examples — 82 (26%) enriched with real content, 228 filename-only fallback. Output: `classifier_training_enriched.json`. Merged `feat/light-scan` to main. **968 tests pass**.
- **Errors:** ruff pre-commit blocked twice (redundant `"r"` mode, line-too-long E501) — fixed and recommitted. Unicode `→` in log string broke Windows cp1252 console — fixed to plain text.
- **Next:** Use `content_text` + `filename_text` dual-vectorizer in classifier training. Consider running enrich on machines with more source files available.

## 2026-03-26 client normalization migration

- **Did:** Full client normalization migration on branch `fix/client-normalization-migration`. (1) Vault audit: 583 notes, 22 distinct client values, key splits found (Lenzing AG/Group, JLR/Jaguar Land Rover, Pepsi variants, SGDBF long-forms, etc.). (2) Expanded `client_aliases.yaml` in CKE from 8 to 48 entries covering all vault variants. (3) Added `get_client_variants()` to corp-by-os + OR LIKE expansion in retrieve engine — `corp prep "JLR"` now finds 3 sources (was 1). (4) Created `scripts/migrate_client_names.py` (dry-run + --apply); applied migration: 77 vault notes normalised. (5) Rebuilt index: 493 notes. (6) Added `schema.yaml` contract to corp-os-meta + `validate_against_schema()` (warn-only). (7) Wired schema check into CKE `post_process_extraction()`. Eval: no regression. 970 tests pass (6 pre-existing Jinja2 failures unrelated).
- **Errors:** 6 pre-existing test failures (TemplateNotFound: meta.yaml.j2) — not caused by this work, present on main too.
- **Next:** Merge `fix/client-normalization-migration` to main. Consider fixing the 6 pre-existing Jinja2 template test failures separately.

## 2026-03-26 early morning (continued)
- **Did:** v2 bulk ingest (387 notes, 493 total indexed, 25 projects). Vault now has real data. corp retrieve returns 30 results across topics.
- **Failed:** 2 Cognitive Friday YAML parse errors (unquoted hyphen in session_id)
- **Next:** Git hygiene (179 uncommitted ruff files). RFP KB + vault merge (Council). Obsidian optimization. 30-day eval (2026-04-25).

## 2026-03-26 v2 bulk ingest

- **Did:** Ran v2 bulk ingest (387 notes ingested, 2 YAML errors, 0 quarantined). Index rebuild: 583 vault notes found → 90 deduped by source_hash → 493 unique notes indexed (25 projects). Net new unique v2 notes: ~292. `corp retrieve "demand planning"` → 30 results, Sufficient (unchanged from v3-only — engine caps at 30). Vault now fully populated with v3 + v2 extractions.
- **Errors:** 2 YAML parse failures (`Cognitive Friday Season 2` files — `session_id: "cognitive-friday-season-2` unquoted hyphen truncates string). Notes skipped, not quarantined.
- **Next:** Re-extract the 2 failing Cognitive Friday notes (fix YAML), re-extract low-quality JLR notes (score 28–29), run `scripts/extract_training_data.py` to refresh fixtures, RFP KB + vault merge decision (Council).

## 2026-03-26 v3 bulk ingest, IndexStats fix, gotcha added

- **Did:** Fixed `IndexStats.total_facts` AttributeError in cli.py:3099 (was `total_facts`, correct attr is `facts_indexed`). 39/39 ingest tests pass. Added CKE path structure gotcha to `~/.claude/skills/gotchas/gotchas.md`. Ran v3 bulk ingest: 203 notes ingested (2 deduped identical source_hash → 201 unique), 0 quarantined, 0 skipped, index rebuilt in 2.0s (201 notes, 25 projects, 0 facts). `corp retrieve "demand planning"` → 30 results, Sufficient. `corp retrieve "WMS picking methodologies"` → 28 results, Sufficient (was 2 JLR-only before).
- **Quality distribution:** Only 3/203 notes have quality_score (the 3 JLR pilot notes at 28/29/85). All 200 pre-quality-era notes pass gate by design (None → pass). Vault now has 210 total notes (203 v3 + 7 pre-existing).
- **Next:** Run `scripts/extract_training_data.py` to refresh fixtures from new v3 extractions. Consider re-extracting low-quality JLR notes (score 28–29) with deeper prompt.

## 2026-03-26 JLR pilot end-to-end ingest

- **Did:** Ran JLR pilot ingest — diagnosed path structure mismatch (`jlr_pilot/` is flat, `ingest-extractions` expects `scope/client/pkg/extract/` hierarchy). Created `jlr_staged/projects/Jaguar_Land_Rover_TMS_WMS_OMS/` with 3 packages. Dry-run confirmed 3→01_Knowledge, 0 quarantined. Live ingest succeeded. Index rebuilt. `corp retrieve "JLR TMS"` returns 3/3. `corp retrieve "WMS picking methodologies"` returns 2/2 (Sufficient: No — needs more WMS depth coverage). Minor display bug: `IndexStats.total_facts` AttributeError post-rebuild (cosmetic only).
- **Issues:** `jlr_pilot/` flat structure incompatible with `ingest-extractions` — requires wrapping in `projects/CLIENT/` scope. Two low-quality notes (score 28–29) passed because DEFAULT_QUALITY_THRESHOLD=25. Full v3 ingest (203 notes) pending — would address health check finding of empty 01_Knowledge vault.
- **Next:** Run full v3 ingest to populate vault. Fix `IndexStats.total_facts` display bug in CLI. Consider re-extracting the 2 low-quality JLR notes with a deeper prompt.

## 2026-03-26 ecosystem health check

- **Did:** Read-only comprehensive health audit across 8 phases: test results (2,291/2,298 pass, 7 skip), CLI ops (7 agents OK), sandbox E2E (5/5 pass), CKE outputs (749 notes, 613 JSON, 20.2GB), databases (ops.db 1,116 rows, index.db 2,677 rows), vault (1,325 indexed notes but 01_Knowledge empty — investigate), git history (438 commits, main clean, 6 active branches), MyWork (794 files). Generated `.ecosystem/archive/2026-03-26_HEALTH_CHECK.md` report.
- **Issues:** 277 ruff linting errors found (213 auto-fixed, 64 remaining E402/E501 formatting); vault 01_Knowledge empty despite index.db showing 1,325 notes (routing mismatch?); live E2E test timeout expected (real API calls).
- **Next:** Investigate vault note storage paths. Fix E402 imports. Update training fixtures. Monitor live test performance.

## 2026-03-25 night session
- **Did:** Monorepo complete (6 packages, 2,153 tests). Naming convention v2 (19 type codes, 15 client aliases). Code review fixes (2 critical, 4 high). Training data fixtures from 690 extractions. Routing feedback table. Trust_level protection. Vault ingest pipeline.
- **Failed:** Standalone repo folder rename blocked by Windows file locks. CKE had 6 pre-existing test failures (fixed).
- **Next:** Integration tests, pre-commit hooks, coverage gaps (CPE classifier, RFP anonymization), pilots.

## 2026-03-25 late night
- **Did:** Workflow improvements: JOURNAL.md, integration tests (6 new → 23 total), pre-commit hooks (ruff), dev-check.ps1, session-start.ps1, Session Protocol + Prompt Decision Rule in CLAUDE.md.
- **Failed:** sample_output.json is deep extraction format (qa_pairs/slide_breakdown), not frontmatter — test adapted accordingly.
- **Next:** Coverage gaps (CPE classifier, RFP anonymization), Hypothesis tests, ADR conversion.

## 2026-03-25 continuation
- **Did:** 79 CPE classifier tests (all 20 priority rules, priority ordering, edge cases). 25 RFP anonymization tests (core + middleware, all patched via mock). 5 Hypothesis property-based tests. 14 ADRs distilled from AI Council debates into decisions/.
- **Failed:** \bpayload\b doesn't match payload_inbound (underscore is \w — word boundary lesson). \bstrategy\b doesn't match supply_chain_strategy same reason. Fixed test inputs.
- **Next:** Run dev-check.ps1 full quality gate, consider adding hypothesis to monorepo pyproject.toml dev deps.

## 2026-03-25 full day session
- **Did:** Monorepo complete (6 packages, 2,276 tests). CKE v0.8.0 namespace migrated. Naming convention v2 (19 types, 15 clients). Code review (20 issues found, 8 fixed). Training data fixtures (690 notes → 7 fixtures). Coverage gaps filled (CPE +79, RFP +25). Hypothesis tests. 14 ADRs. Workflow improvements (JOURNAL, integration tests, pre-commit, dev-check). Closed learning loop with Last triggered. VERIFY-LOG. Settings optimized (opusplan, haiku subagents). 3 Council decisions (monorepo, routing feedback, naming, workflow optimization).
- **Failed:** Standalone repo folder rename blocked by Windows file locks. Baseline tasks for skill evaluation — skills deployed before baseline.
- **Next:** Pilots (JLR vault ingest → corp prep → corp retrieve). 30-day skill evaluation (2026-04-25). Local LLM exploration. AI Council CLI integration. Obsidian optimization.
## 2026-03-25 sandbox phase 1
- **Did:** PipelineConfig dataclass in corp-os-meta (production() + sandbox() classmethods, 10 tests). Threaded config through vault_io (resolve_vault_path, list_projects, validate_vault), index_builder (rebuild_index, update_project), ops/database (OpsDB), overnight/state (OvernightState). All functions backward-compatible (None → production()). index_extra_roots added to PipelineConfig for INDEX_EXTRA_ROOTS env var. Path audit confirmed hardcoded paths isolated to legacy AppConfig only.
- **Failed:** noqa inside triple-quoted SQL string doesn't work (comment becomes part of the SQL). Fixed by reformatting the CASE expressions across 2 lines.
- **Next:** Phase 2: sandbox fixture in conftest.py, migrate test monkeypatching to PipelineConfig.sandbox(), thread CLI entry points via Click ctx.obj.

## 2026-03-25 sandbox phase 2
- **Did:** Step 1: Threaded PipelineConfig through 13 CLI commands via @click.pass_context on root group + @click.pass_obj on each command. Backward-compatible (fallback to production()). Step 2: SandboxManager in sandbox.py — create(), _init_databases() (delegates to real OpsDB/OvernightState/index_builder _SCHEMA), stage_files(), snapshot_production(), teardown() with retry, context() CM. Step 3: fixture corpus (5 minimal files + manifest.json with expected type_code/client). Step 4: sandbox + sandbox_with_corpus fixtures in conftest.py. 925 tests passing throughout. Merged feat/sandbox-phase2 to main.
- **Failed:** ruff E501 on 3 pre-existing long lines touched by the merge context (fixed). ruff changed import sort order in conftest.py on second hook run (staged and re-committed).
- **Next:** Migrate existing test monkeypatching to use sandbox fixture. Add integration tests that use sandbox_with_corpus to exercise ingest → OpsDB roundtrip.

## 2026-03-25 sandbox phase 3
- **Did:** test_pipeline.py module (StepResult, PipelineTestReport, run_pipeline_test(), format_report(), 5 step functions). `corp test-pipeline` CLI command with --live/--keep-sandbox/--verbose/--output. 9 tests (sandbox isolation, report structure, keep_sandbox, format_report). All 2,153+ tests passing. Manual smoke test: 5/5 steps pass in ~0.1s. Merged feat/test-pipeline-command to main.
- **Failed:** ruff E501 on 3 lines across cli.py + test_pipeline.py (long Rich markup strings) — fixed with if/else blocks. Corpus type codes DECK/NOTE absent from naming_config.yaml — used deterministic SOW/PRES/LENZ/JLR/GEN checks instead.
- **Next:** Live mode (--live flag exercises real CKE API). Migrate existing monkeypatching tests to use sandbox fixture. Integration tests using sandbox_with_corpus for ingest → OpsDB roundtrip.

## 2026-03-26 test-pipeline --record
- **Did:** Added `--record` flag to `corp test-pipeline`. `--record` implies `--live`, calls real CKE API per corpus file, saves `{hash[:12]}_{tier}.json` fixtures + `manifest.json` to `tests/fixtures/pipeline/recorded/`. Future fixture runs replay from these JSONs. PipelineTestReport gains `recorded_fixtures`/`recording_cost` fields. CLI prints "Recorded N fixtures, total cost $X.XX". 2 new tests (fields default + graceful CKE-unavailable skip). 936 passed, 1 skipped. Merged feat/test-pipeline-record to main.
- **Failed:** Nothing new — "file modified since read" on test_pipeline.py due to ruff auto-format between sessions (existing gotcha).
- **Next:** Live pilots (corp test-pipeline --live → verify against real CKE). Migrate existing monkeypatching to sandbox fixture. Integration tests for ingest → OpsDB roundtrip.

## 2026-03-26 early morning
- **Did:** Health check (HEALTHY), JLR pilot (3 notes ingested, retrieve works), v3 bulk ingest (201 notes, 0 quarantined), IndexStats bug fixed, gotcha added
- **Failed:** jlr_pilot flat structure required manual staging (gotcha added)
- **Next:** v2 bulk ingest (763 notes), RFP KB + vault merge decision (Council), Obsidian optimization, 30-day eval

## 2026-03-26 morning
- **Did:** Eval baseline (classifier 51.3%, tags 0.753). JLR real usage test (useful output). Client alias fix (retrieve + prep). Obsidian setup (8 MOCs, plugin recs). Lint cleanup. v2/v3 bulk ingest (493→587 vault notes). Context scope in ROUTING.md.
- **Failed:** Classifier still 51.3% (filename-only ceiling, LLM needed for 70%+)
- **Next:** Council CLI integration. Obsidian plugins install. Lenzing normalization. RFP KB + vault merge.

### 2026-03-28
- **Did:** SQL analytics MVP (6/10 benchmark queries). People added to FTS. Gemini 2.0 Flash-Lite for Tier 2 (-75% cost). Scripts/ to Dev/ migration (11 files, 2673 DB rows). .ecosystem consolidated. ADRs synced (#13-#21). Phase 1 cleanup (archives deleted). Corp-pdf-toolkit archived. Council #22 RFP federation debate. Venvs recreated. Full health check passed.
- **Failed:** -
- **Next:** Ontology Q4 (canonical product map). RFP federation implementation. File renames (585 files). MinHash wire into inbox.

## 2026-03-28 session 2 — repo audit + cleanup + governance
- **Did:** Full monorepo audit (2026-03-28_CLEANUP_PLAN.md, 2026-03-28_REPO_INVESTIGATION.md → archived). Phase 2 safe deletions: rebuild_staging (2 GB), misc/01_Product_Docs temp_frames (2.4 GB), Python caches (~0.3 GB), flattened _outputs/_outputs/ nesting. Phase 3 governance: ADR-22 written (RFP KB federation), docs/ phase reports date-prefixed, .ecosystem/ root clean (only MASTER_HANDOFF.md remains), CLAUDE.md council count 21→22, MASTER_HANDOFF.md ADR count + council #22 summary updated.
- **Failed:** -
- **Next:** Implement ADR-22 (corp rfp-index + rfp_entries table + grouped corp retrieve). .sandbox/ review (Rob). v2/v3 _outputs/ per-note quality audit (01_Product_Docs only).

## 2026-03-27 vault rebuild (Council Decision #20)

- **Did:** Re-extracted 216 vault notes via CKE batch (gemini-3.1-pro-preview, deep mode). Ingested with quality-threshold 25, index rebuilt. Added `include_deprecated` filter to retrieve engine — deprecated notes excluded from all query paths. Added missing Compliance MOC. All 943 corp-by-os tests passing.
- **Errors:** 41 extraction errors, Haiku enrichment failures on all files (non-fatal, expected — returns empty JSON), `source_type=presentation` schema mismatch (pre-existing warn-only).
- **Next:** Monitor trust-status drift. Consider `source_type` enum expansion for presentation/workshop. Eval baseline updated.

### 2026-03-29 — refactor/centralize-hardcoded-paths

- **Did:** Zero-blast-radius refactor centralizing all MyWork/vault folder name strings into `src/corp/schema/folder_names.py`. Replaced hardcoded literals across 20+ files in 4 batches (4 commits). Added `INBOX`, `PROJECTS`, `TEMPLATES`, `RFP`, `SOURCE_LIBRARY`, `ADMIN`, `ARCHIVE`, `SYSTEM`, `STAGING`, `UNMATCHED`, `QUARANTINE`, `ALL_MYWORK_FOLDERS`, `SCAN_SKIP_FOLDERS` constants. Final grep confirms zero hardcoded folder literals remain in `src/corp/` outside the canonical module.
- **Gotcha:** Ruff pre-commit hook reformats import blocks in-place, causing "unstaged files" conflicts. Fix: always re-stage (git add) the modified file after a ruff-failed commit, then recommit. Happened 4× during this session.
- **Tests:** 2412 passed, 6 skipped throughout all batches (no regressions).
- **Next:** Step 5 (YAML config annotation), Step 6 (test assertion literals), merge to main.

### 2026-03-29 — fix/stale-docs-post-consolidation

- **Did:** Cleaned up all stale references from the 6-package → unified `src/corp/` consolidation. Tier 1: fixed `run-all-tests.ps1` (6-package loop → single `pytest tests/`) and `dev-check.ps1` (`packages/` → `src/`). Tier 2: rewrote README.md for unified layout, updated MASTER_HANDOFF.md (council count 22→23, gotcha count 37→41), fixed ADR-14 config path, updated 20 verify: paths in `~/.claude/skills/gotchas/gotchas.md`. Tier 3: fixed `.env.example` (stale CKE_PATH comment), fixed `.gitignore` (`packages/cke/_outputs/` → `data/_outputs/`), moved 3 phase reports from `docs/` to `.ecosystem/archive/`, removed empty `docs/`, created `CHANGELOG.md` with 1.0.0 consolidation summary.
- **Commits:** `453a0e3` (Tier 1), `39b95cb` (Tier 2), `7350265` (Tier 3), merged to main.
- **Failed:** -
- **Next:** Step 5 (YAML config annotation), Step 6 (test assertion literals), merge `refactor/centralize-hardcoded-paths` to main.

### 2026-03-29 — Council #24: MyWork Knowledge Architecture

- **Did:** Implemented Council #24 binding decisions. Rewrote `folder_names.py` (7 canonical folders + `.corp`). Removed TEMPLATES/SOURCE_LIBRARY/RFP/SYSTEM constants; added WORKFLOWS/REFERENCE/COMPLIANCE/CORP_INFRA + subfolder constants. Updated 17 source files (classifier routing, overnight scopes, integrity checks, path flattening SYSTEM/.corp/X → .corp/X). Updated all test files. Added 16 missing client aliases. Restructured MyWork on disk: created 90_Archive + .corp, moved 9 stale projects to archive, migrated pipeline infra from 90_System to .corp, deleted empty 40_Media and 90_System, merged legacy subdirs in 20_Workflows and 30_Reference.
- **Tests:** 2412 passed, 6 skipped (no regressions across all steps).
- **Next:** Verify magistrala pipeline end-to-end with new paths. Measure MISC rate at day 7. Monitor 20_Workflows file count (<75 threshold).

### 2026-03-30 — refactor/align-with-playbook

- **Did:** Eliminated `.ecosystem/`. Moved: `MASTER_HANDOFF.md` → `docs/HANDOFF.md`, `archive/` (32 files) → `docs/archive/`, `council_transcripts/` (25 files) → `docs/decisions/transcripts/`, root `decisions/` (25 ADRs + README) → `docs/decisions/`. Updated all active references in `CLAUDE.md`, `update_handoff.py`, `extract_training_data.py`, `quarantine_fragments.py`, `tag_legacy_notes.py`, `docs/decisions/README.md`, `scripts/archive/*.py`. Updated `.gitignore` (`.ecosystem/rebuild_staging/` → `docs/staging/`). One convention, universally applied.
- **Failed:** Nothing.
- **Next:** Verify magistrala pipeline end-to-end with new paths. Measure MISC rate at day 7. Monitor 20_Workflows file count (<75 threshold).

### 2026-03-30 — fix/stale-package-references

- **Did:** Purged all stale old-package name references following the 6→1 consolidation. 4 commits: (1) fixed 3 broken runtime paths in `cke_client.py`, `cke_invoker.py`, `extract_training_data.py`; (2) renamed agent keys in `agents.yaml`/`workflows.yaml` to CLI names (com, cpe, rfp); (3) updated `CLAUDE.md` source layout and CLI table; (4) updated docstrings in ~25 src/ files. Preserved intentionally: `%LOCALAPPDATA%/corp-by-os/` paths, `source_tool`/`generated_by` DB values, 3 excluded files. 20 remaining grep hits all confirmed intentional.
- **Failed:** Nothing — 2495 tests passed.
- **Next:** Merge fix/stale-package-references → main.

### 2026-03-30 — chore/todo-audit-cleanup

- **Did:** Full TODO/FIXME/HACK audit across all repo files. Found zero actual comment markers anywhere in the codebase. All 10 hits were false positives: (1) `TaskStatus.TODO` enum values in `models.py`/`task_manager.py`/tests — legitimate code; (2) English noun "hacks" (e.g., "sys.path hacks") in frozen `docs/archive/` and `docs/decisions/transcripts/` — accurate technical prose; (3) "XXXX" substring in a template filename embedded in JSON data/fixture files. No docs needed editing. Added `todo-tree.filtering.excludeGlobs` to `corp-monorepo.code-workspace` — excludes `docs/archive/`, `docs/decisions/`, `*.json`, `JOURNAL.md`, `CHANGELOG.md`, `.venv`, `__pycache__`, `models/`, `data/`, `eval/`. Also added `todo-tree.general.tags` and `defaultHighlight` for explicit tag config. Merged to main.
- **Failed:** Nothing.
- **Next:** Verify magistrala pipeline end-to-end with new paths. Measure MISC rate at day 7. Monitor 20_Workflows file count (<75 threshold).

### 2026-05-18 — docs: universalization rollout complete

- Did: Completed the full doc-governance universalization rollout across corp-monorepo (gap-review §2.x series). Five workstreams: (A) wrote `VISION.md` at repo root; (B) relocated `ARCHITECTURE.md` to root, retired single-file handoff (`docs/HANDOFF.md`) and `BACKLOG.md`; (C) ADR hygiene — added `Decommission:` field to ADR template (`templates/ADR-template.md`), indexed ADR-22..27 in `docs/decisions/README.md`, resolved ADR-27 number collision (old transcript moved to `docs/decisions/transcripts/`), ported `scripts/normalize_headers.py` with pre-commit hook; (D) fixed named numerical drift in `CLAUDE.md` (replaced hardcoded test count and council-decisions count with source-of-truth references), added `## Project Scale: L` declaration, ported audit tools `scripts/find_orphans.py` and `scripts/check_doc_refs.py` (with `tests/scripts/test_find_orphans.py`) from `verify/codex-p1-findings` branch tip. Full suite green throughout: 2,526 passed, 6 skipped on final run.
- Result: All in-scope gap-review remediations landed. CLAUDE.md carries no stale hardcoded counts. Project Scale declared. Two on-demand audit CLIs available (write `.audit/*.json`; not wired into pre-commit).
- Changes: `VISION.md` (new), `ARCHITECTURE.md` (root, formerly `docs/ARCHITECTURE.md`), `docs/HANDOFF.md` (retired), `BACKLOG.md` (retired), `templates/ADR-template.md` (new), `scripts/normalize_headers.py` (new), `.pre-commit-config.yaml` (hook added), `docs/decisions/README.md` (ADR-22..27 indexed), `docs/decisions/transcripts/ADR-27-*.md` (moved from collision path), `CLAUDE.md` (stale counts → source refs; `## Project Scale: L` added), `scripts/find_orphans.py` (new), `scripts/check_doc_refs.py` (new), `tests/scripts/test_find_orphans.py` (new).
- Abandoned: Backfill of `Decommission:` field into existing ADRs — forward-only policy (§2.8); no-op workstreams §2.17 (scope-tags), §2.18 (BACKLOG_ARCHIVE), §2.19 (doc-format scripts) — confirmed out-of-scope; Workstream-E deferred items (dangling `ARCHITECTURE.md:423` reference, `conventions.yaml` layer-name drift) — remain deferred per gap-review §3-E.
- Next: P2 — implement vault single-writer invariant (ADR-27 enforcement).

### 2026-06-04 — graphify pilot (#88) REJECTED

- Did/Result: Ran the #88 project-scoped graphify pilot on `chore/graphify-pilot` (security review SAFE, code-only graph build, graph-query-vs-grep measurements, maintenance assessment); operator REJECTED against the kill criterion (grep cheaper 2.5–5.6× + higher quality 3/3; maintenance conflicts with hub governance). Pilot branch deleted, `.graphify-venv` removed; report preserved on main with the ruling appended. No graphify trace on main beyond the audit report.
- Changes: `docs/audits/2026-06-04-graphify-pilot.md` (new), this entry.
- Next: none — backlog #88 resolved (reject).
