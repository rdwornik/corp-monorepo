---
last_reviewed: 2026-07-13
status: active
owner: Rob
---

@.claude/CLAUDE-FLOOR.md

# CLAUDE.md
<!-- scope: meta -->
<!-- version: 2.8 — 2026-07-13 -->

> **Session contract for Claude Code in this repo.** Read on every session start (auto). Single canonical agent-instruction file (≤200 lines). Per ADR-53.
>
> **For universal rules:** read `../.dev-knowledge/protocols/ESSENTIALS.md` and `../.dev-knowledge/protocols/PLAYBOOK.md`.

> **Section ownership (methodology boundary):** sections marked `owner=hub` are fleet methodology tracked from the `.dev-knowledge` hub; `owner=repo` sections are project-local. The machine-readable owner map is the `<!-- methodology:… owner=… -->` markers on each section below; sanctioned divergences from hub-generic expectations are recorded in `.methodology.yaml`.

## 1. First read (session start)
<!-- methodology:start id=first-read owner=hub -->

In order, read:
1. This file (you're here)
2. The hub methodology protocol `ESSENTIALS.md` — Rob's universal working style (read at the hub `.dev-knowledge/protocols/` set; hub-pointer, never copied into a consumer)
3. The hub methodology protocol `PLAYBOOK.md` — universal protocols (only sections relevant to the current task; same hub `.dev-knowledge/protocols/` location)
4. Most recent `docs/handoffs/*/` bundle — start with its `HANDOFF_BOOT.md` (v5 bundles' operator session entry: slug · purpose · mode; older bundles use `README.md`), then the canonical operator runbook `docs/handoffs/README.md` — if continuing prior session
5. Last 5 entries of `JOURNAL.md`

If ESSENTIALS or PLAYBOOK are unavailable, proceed with this file alone but flag it.
<!-- methodology:end id=first-read -->
<!-- methodology:start id=first-read-corp-addendum owner=repo -->

**corp-local overrides (owner=repo):**
- The hub `ESSENTIALS.md`/`PLAYBOOK.md` (items 2–3) are read at `../.dev-knowledge/protocols/` — corp is a consumer, hub-pointer only.
- Item 4 handoff bundles: corp carries **no local `docs/handoffs/`** (ADR-36 read-only contract). Read the most recent corp-monorepo bundle at `../.dev-knowledge/docs/handoffs/` instead.
- 6. `VISION.md` — project purpose and scope.
<!-- methodology:end id=first-read-corp-addendum -->

## 2. Repo identity
<!-- methodology:start id=repo-identity owner=repo -->

- **Name:** `corp-monorepo`
- **Purpose:** Corporate OS — AI-powered knowledge management for Blue Yonder presales (ingest corporate source material → LLM extraction → Obsidian vault notes → FTS5 search; five CLIs drive all operations)
- **Status:** `active`
<!-- methodology:end id=repo-identity -->

## 3. Architecture
<!-- methodology:start id=repo-architecture owner=repo -->

See `ARCHITECTURE.md` for the structural model; read it before structural changes (required per ADR-51 — mandatory for every repo).

Key facts (abbreviated; `ARCHITECTURE.md` is authoritative):
- Unified `src/corp/` namespace — 6 former packages consolidated; one `pyproject.toml`
- 4-layer dependency model: `interface > orchestration > core > foundation` (Tach-enforced)
- 5 CLIs: `corp`, `corp-meta`, `cke`, `cpe`, `com`
<!-- methodology:end id=repo-architecture -->

## 4. Conventions

- **Naming:** `snake_case` Python, `kebab-case` markdown, UPPERCASE living docs; files: `{YYYY-MM}_{TYPE}_{CLIENT}_{Desc}.{ext}` (ADR-14)
<!-- methodology:start id=conventions-commit-branch owner=hub -->
- **Commits & branches:** Branch prefixes are `feat/ fix/ docs/ chore/` (these four only). Commit **types** follow Conventional Commits and additionally include `refactor` and `test` — commit types are **not** branch prefixes. Never commit directly to `main`: branch → `--no-ff` merge.
<!-- methodology:end id=conventions-commit-branch -->
- **Testing:** `pytest -x --tb=short`; run `./scripts/run-all-tests.ps1` before merging
- **Linting:** pre-commit hooks — ruff (formatting/linting) + tach (dependency layers)
- **Config:** centralized in `config/paths.toml`; `GEMINI_API_KEY` is standard (not `GOOGLE_API_KEY`); ENV > config > default
- **Methodology:** `.methodology.yaml` (root) declares corp's sanctioned methodology divergences; read by the hub Informant at the fixed path `<repo-root>/.methodology.yaml` — keep at root, do not move to `config/`.
- **Engagement:** 1 file/1 module → conversational; 2-3 files/1 module → conversational with context; 3+ files/2+ modules → formal `.md` prompt; architecture decision → AI Council debate

**Out of scope for this repo:**
- Client/pre-sales data → Obsidian vault
- Cross-repo lessons → `../.dev-knowledge/LESSONS.md`
<!-- methodology:start id=conventions-output-formatting owner=hub -->
- **Output formatting (render-layer):** Claude does **not** emit box-drawing glyphs — the Claude Code TUI *paints* plain markdown pipe-tables (`| col | col |`) as Unicode borders (`┌─┬─┐ │ └─┴─┘`) **client-side at render time**. So a bare table looks clean in the terminal but copies into browser chat as costly border glyphs (~3× the tokens), and a rule that merely bans Claude from *writing* box-drawing is a no-op (Claude already doesn't). The working fix is at the render layer: any report the operator copies out must be (1) **flat** — plain markdown or `key: value` / bullet lists, no column-padding spaces — **and** (2) **wrapped in a triple-backtick code fence**, which makes the TUI render it raw/un-painted so the copied text carries no borders. Same fenced-block discipline already used for Scale-S snippets (ESSENTIALS) and downloadable prompts (§2). Persistent diagrams live on the separate human-facing visualization surface (ADR-59; the ADR-51 amendment 2026-07-05 moved Mermaid out of canonical `ARCHITECTURE.md` — its codemap is now compact text), out of scope. Full rationale + `/session-summary` reconciliation: PLAYBOOK §8 "Output the operator copies into browser chat".
<!-- methodology:end id=conventions-output-formatting -->

## 5. Critical rules
<!-- methodology:start id=critical-rules-records owner=hub -->
1. **`LESSONS.md` and `logs/TOKEN-LOG.md` are append-only** — never edit old entries; only append (ADR-29, ADR-39)
2. **`JOURNAL.md` is append-only newest-first** — prepend at session wrap or workday close
3. **ADRs, transcripts, handoffs, and audits are immutable** — supersede with a new file or an in-file amendment marker; never edit in place. **ADR ratification exception (ADR-94):** an ADR's *status line* MAY be edited in place on ratification (e.g. Proposed → Accepted) — the status line is metadata, not decision content. This exception is ADR-specific and covers the status line only; ADR decision content, and transcripts / handoffs / audits in full, remain immutable.
<!-- methodology:end id=critical-rules-records -->
<!-- methodology:start id=critical-rules-repo-vault owner=repo -->
4. **corp (ingest/) is SOLE writer for `02_sources/` `.md` notes** (ADR-27; `actions/*` may write DASHBOARDS, METADATA, BRIEFS directly; all others via `vault_io.write_note()`). Enforced by `tests/safety/test_vault_writer_invariant.py`.
5. **CKE (extractor/) is PURE extraction engine** — no vault writes, no database writes.
<!-- methodology:end id=critical-rules-repo-vault -->
<!-- methodology:start id=critical-rules-consistency owner=hub -->
6. **Keep files consistent** — ESSENTIALS summarizes PLAYBOOK, not copies it; divergence causes drift
<!-- methodology:end id=critical-rules-consistency -->
<!-- methodology:start id=critical-rules-repo-safety owner=repo -->
7. **API keys in env vars ONLY** — loaded from `~/Documents/.secrets/.env`; NEVER in config files or code.
8. **OneDrive exclusion** — NEVER let cleanup or audit touch `OneDrive - Blue Yonder` paths (fail-closed guards at every mutation site; see ARCHITECTURE.md §OneDrive safety guards).
<!-- methodology:end id=critical-rules-repo-safety -->
<!-- methodology:start id=critical-rules-no-leftovers owner=hub -->
9. **No leftovers** — any automated or scratch-creating process (parallel-session worktree, temp file, scratch dir) removes **and verifies removal of** everything it created before it counts as done; cleanup fires even on abort. The provision→cleanup round-trip must leave the tree identical. See PLAYBOOK §Session-boundaries "No leftovers"
<!-- methodology:end id=critical-rules-no-leftovers -->
<!-- methodology:start id=critical-rules-repo-health owner=repo -->
10. **Run `./scripts/run-all-tests.ps1` before merging; `./scripts/dev-check.ps1` before PR.**
11. **Check `~/.claude/skills/gotchas/` before modifying any module.**
12. **Forward slashes everywhere** in databases and stored paths.

> **§5 rule-count divergence (noted):** the owner=hub records/consistency/no-leftovers rules occupy fixed slots 1–3, 6, 9; corp's 7 substantive project rules (vault-writer, CKE-pure, API-keys, OneDrive, run-tests, gotchas, forward-slashes) fill 4, 5, 7, 8, 10–12. Total exceeds the template's "≤10" guideline — a deliberate corp divergence: corp legitimately carries more safety rules (OneDrive/vault invariants cannot drop). Substance unchanged; pure renumber.

**Graduated learned rules (verify lines are mandatory — gotchas system):**

- Never run `pip install` from `_archived_*` repos — overwrites monorepo CLI entry points. Only install from corp-monorepo root.
  `verify: Grep("pip install", path="corp-monorepo/") → confirm no install instructions point to archived repos`
- git subtree branches must NEVER be rebased — always merge. Rebase → duplicate commits and lost history.
  `verify: manual (process rule — check before any rebase on monorepo branches)`
- CKE output must be staged in `scope/client/package/` hierarchy BEFORE running `corp ingest-extractions`. Flat dirs → 0 notes ingested.
  `verify: Grep("ingest-extractions", path="corp-monorepo/") → check any docs/scripts for flat-dir usage`
- `status.json` concurrent reads must use try/except with 2-3 retries — CKE writes while polling reads cause JSONDecodeError.
  `verify: Grep("json.loads", path="corp-monorepo/src/corp/") → confirm retry wrapper exists`
<!-- methodology:end id=critical-rules-repo-health -->

## 6. Session start protocol
<!-- methodology:start id=session-start-protocol owner=hub -->

1. `git status` — clean working tree?
2. `git log --oneline -5` — recent context
3. Read most recent handoff if continuing prior session
4. Check `BACKLOG.md` for in-progress items
5. `pytest --collect-only` — test discovery sanity check
6. Wait for Rob's prompt — never improvise

If any check fails → stop and ask Rob before proceeding.

Verify after updates: ESSENTIALS ↔ PLAYBOOK alignment; ENVIRONMENT ↔ `~/.claude/` state; SESSION_SETUP ↔ PLAYBOOK process changes; JOURNAL reflects last session.
<!-- methodology:end id=session-start-protocol -->
<!-- methodology:start id=session-end-corp owner=repo -->

**Session end:** **Prepend** (newest-first) an entry to `JOURNAL.md` (ADR-49 shape, cutover 2026-05-18):
`### YYYY-MM-DD — <topic>` then `- Did:` / `- Result:` / `- Changes:` / `- Abandoned:` / `- Next:`.
`Changes:` is the sole change record (no CHANGELOG). Append-only newest-first; never edit prior entries.

**Handoffs:** Generated in `.dev-knowledge` per the hub `HANDOFF_PROCESS.md` (**v5**; ADR-62 ratified the earlier v4 process, since superseded) — NOT in this repo (ADR-36 read-only contract).
Trigger: in Claude Code at `.dev-knowledge`, say "Make handoff for corp-monorepo".
<!-- methodology:end id=session-end-corp -->

## 7. Slash commands available
<!-- methodology:start id=commands-repo-roster owner=repo -->

User-level (`~/.claude/commands/`):
- `/session-summary` — generate handoff at session end
- `/codex-review` — invoke Codex review

Repo-level (`./.claude/commands/`):
- `/override` — bypass the ADR-85 session-end gate for this HEAD (explicit, logged; seb's only escape — `--no-verify` does not bypass a Stop hook)

Plugin (`tier1-lifecycle@dev-knowledge-methodology`, project scope): `/review-closures`, `/ship`
<!-- methodology:end id=commands-repo-roster -->

## 8. Skills active
<!-- methodology:start id=skills-repo-roster owner=repo -->

**User skills** (`~/.claude/skills/`):
- `gotchas` — universal dev gotchas (encoding, shell safety, test framework)

**Built-in / plugin skills** (loaded automatically by the harness):
- `verify` — bundled/plugin skill; domain-specific verification; run after pytest passes

**Repo skills** (`./.claude/skills/`):
- `gotchas` — corp-monorepo patterns (CKE, vault ops, OneDrive safety, Graph API). **Read before changes.**
<!-- methodology:end id=skills-repo-roster -->

## 9. Hooks active
<!-- methodology:start id=hooks-repo-roster owner=repo -->

Pre-commit (from `.pre-commit-config.yaml`; all three hook stages installed via `default_install_hook_types`, stage-less hooks scoped by `default_stages: [pre-commit]`):
- ruff — linting and formatting
- tach-check — dependency layer enforcement (`interface > orchestration > core > foundation`)
- normalize-headers — dated-log header normalization (JOURNAL/LESSONS)
- floor-hash-verify — `.claude/CLAUDE-FLOOR.md` matches its sha256 sidecar (methodology v1.2.0, ADR-93)
- canonical_freshness — `last_reviewed` A2 gate, always_run; a stale-edited canonical doc BLOCKS the commit (methodology v1.2.0, ADR-85/81)
- validate-audit-casing — `docs/audits/*.md` lowercase-kebab casing gate (ADR-101 R4, prospective-only; enumerated skip-set)
- validate-backlog — `BACKLOG.md` story-map schema gate (plugin twin, ADR-78; E/S-agnostic floor validator)
- backlog-id-on-close — commit-msg gate: requires `[#id]` in the message when a `BACKLOG.md` task line is removed (hub-sourced, v1.3.1)
- block-ff-push — pre-push gate: refuses a direct-to-main / fast-forward push to `main`; a `--no-ff` merge passes (hub-sourced, v1.3.1; core-invariant #5 prevent organ)

Other:
- `~/.claude/settings.json` (user-level): SessionStart hook — runs `surface-closures.ps1` (Tier-1 lifecycle closure surfacing, ADR-70).
- `./.claude/settings.json` (project-level): SessionStart — `scripts/surface-conformance.ps1` (nightly-conformance surfacing, fail-soft) + the methodology floor guard (`python .claude/check_floor_hash.py --require-present`) + the arm leg (`python -m pre_commit install`); Stop — `scripts/session_end_backpressure.py` (ADR-85 session-end gate; JOURNAL SHA-anchor hard block, `/override` is the only escape). All merge with the user-level hooks.
<!-- methodology:end id=hooks-repo-roster -->

## 10. Anti-patterns specific to Claude Code in this repo
<!-- methodology:start id=antipatterns-universal owner=hub -->

- **Editing old LESSONS.md or logs/TOKEN-LOG.md entries** — append-only; editing corrupts the institutional record
- **Adding orchestration scripts** — Layer 2 invariant: validators only, no scripts that drive state in child repos
- **Narrating or managing AGENTS.md** — AGENTS.md is retired (ADR-53); CLAUDE.md is the single instruction file
- **Duplicating content between files** — ESSENTIALS summarizes PLAYBOOK, not copies; drift is the failure mode
- **Putting executable rules in this repo** — those belong in `~/.claude/` with `verify:` lines
- **Running validators with no args** — vacuous pass; always pass `--all` or specific paths
<!-- methodology:end id=antipatterns-universal -->
<!-- methodology:start id=antipatterns-repo owner=repo -->

- The Codex reviewer config is global (`~/.codex/AGENTS.md`, ADR-54); corp-monorepo has no per-repo `AGENTS.md`. Updates to the global config go in `../.dev-knowledge/codex/AGENTS.md`.
- Don't assume module paths from old package names (`corp_by_os`, `corp_os_meta`, `corp_knowledge_extractor`) — all are now under `src/corp/`
- Don't run `pip install` from `_archived_*` repos — overwrites monorepo entry points
- Don't skip `scope/client/package/` hierarchy when staging CKE output for `corp ingest-extractions`
- Don't read `status.json` without try/except + retry (concurrent write risk from CKE)
- Don't bypass pre-commit with `--no-verify` — tach violations are real architecture violations
<!-- methodology:end id=antipatterns-repo -->

## 11. Recent ADRs binding here
<!-- methodology:start id=recent-adrs-roster owner=repo -->

Full list: `docs/decisions/README.md`. **ADR namespaces:** corp-local ADRs (`docs/decisions/`) and ecosystem ADRs (`.dev-knowledge/docs/decisions/`) number independently — they collide on ADR-27 (corp: vault writer; `.dev-knowledge`: scope tagging). References below are namespace-prefixed.

**Local (corp `docs/decisions/`):**
- corp ADR-14: Naming convention v2 — `{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}`
- corp ADR-23: Monorepo internal architecture — flatten, centralize, delete dead code
- corp ADR-27: Vault writer narrowed — `ingest/` SOLE writer for `02_sources/`; actions/* exempt for DASHBOARDS, METADATA, BRIEFS

**Ecosystem (`.dev-knowledge/docs/decisions/`):**
- `.dev-knowledge` ADR-36: Session handoffs generated in `.dev-knowledge` only (read-only contract for this repo)
- `.dev-knowledge` ADR-62: v4 handoff process ratification (supersedes ADR-42 v3) — bundles at `.dev-knowledge/docs/handoffs/{YYYY-MM-DD}-corp-monorepo-{type}/`
- `.dev-knowledge` ADR-49: JOURNAL.md entry shape (cutover 2026-05-18) — `Did/Result/Changes/Abandoned/Next`
- `.dev-knowledge` ADR-51: ARCHITECTURE.md convention — read before structural changes (universal)
- `.dev-knowledge` ADR-53: CLAUDE.md as single canonical agent-instruction file (supersedes ADR-52)
<!-- methodology:end id=recent-adrs-roster -->

## 12. Section history
<!-- methodology:start id=section-history owner=repo -->

- v1.0 (pre-2026-05-19) — original pre-template CLAUDE.md (Project Scale / Architecture / Development / Safety sections)
- v2.1 (2026-05-19) — rewritten to v2.1 12-section template per ADR-53; architecture content homed in ARCHITECTURE.md; §3 is pointer; §2 Purpose added; §10 AGENTS.md guard added
- v2.2 (2026-05-27) — struck tier-residue prose (§2 Scale line removed; §3/§11 "Scale M+" → "universal" per tier-system deprecation); §11 ADR references namespace-prefixed (corp vs `.dev-knowledge`; ADR-27 collision noted)
- v2.3 (2026-07-07) — genuine end-to-end re-read + `last_reviewed` re-stamp (executes hub #100). §9 reconciled to the live config: `normalize-headers` + the hub-pinned TOC hooks were unlisted, and the project-level SessionStart hook (`surface-conformance.ps1`) was missing alongside the user-level one. Methodology-adoption reconcile (floor @-include, mesh hooks, `/override`) follows in the [#14] ratify arc as v2.4.
- v2.4 (2026-07-07) — methodology corpus v1.2.0 adopted (hub deploy, [#14] / hub #221 n=2): floor `@.claude/CLAUDE-FLOOR.md` include (carrier-written, above §1), §7 gains `/override` + the tier1-lifecycle plugin commands, §9 gains floor-hash-verify + canonical_freshness pre-commit gates, the floor SessionStart legs, and the seb Stop gate. Same-day re-read basis as v2.3.
- v2.5 (2026-07-10) — §4 Conventions gains a **Methodology** bullet permanently answering the recurring `.methodology.yaml`-root question (verdict sheet 2026-07-11 menu 8; text from the QA root-hygiene brief §3.2-A). Genuine end-to-end re-read + `last_reviewed` re-stamp per the canonical_freshness A2 gate.
- v2.6 (2026-07-11) — methodology **v1.3.1** rollout (hub ADR-101 hermetization; ai-council-parity). Pre-commit hub hook-source repointed to the canonical GitHub URL and bumped `v1.2.0 → v1.3.1`, adding the **`block-ff-push`** pre-push gate (witnessed refusing a direct-to-main push; a `--no-ff` merge passes) and the **`backlog-id-on-close`** commit-msg gate — §9 reconciled. v1.3.1 (not v1.3.0) armed because the v1.3.0 tag predated the #318/#319 range-reconstruction fixes (tag-ancestry verified). **Form-A boundary markers** (hub #312 / ADR-101) grandfathered onto §1–§12 as additive `<!-- methodology:start/end id=… owner=hub|repo -->` HTML comments — **body prose byte-identical** (marker-only). `owner=hub` = `first-read` (§1), `conventions-commit-branch` (§4 sub-span), `session-start-protocol` (§6 sub-span); the rest `owner=repo`. corp lacks the hub `critical-rules-records` content (LESSONS append-only / ADRs immutable), so that owner=hub region is a known GAP left for a later reconciliation pass. Human-visible boundary note added above §1; the section→owner machine map is the markers themselves (`.methodology.yaml` holds only divergence waivers, +`hub-codemap-hooks` this rollout). Root `INSTALL.md` carried byte-identical from the hub tier1-lifecycle canonical (interim manual copy — will drift until the hub #315 durable carrier lands). §Authority ADR-31/Layer-2 citation split (D4). Genuine end-to-end re-read; `last_reviewed` re-stamped 2026-07-11.
- v2.7 (2026-07-11) — **[#326]** consumer leg: ToC block + both Mermaid diagrams stripped from `ARCHITECTURE.md` (CC-facing; codemap Mermaid → textual edge list, layer-chain diagram → one-line prose). Gate cascade in the same commit: the `toc-freshness`/`toc-generate` hub-hook bindings withdrawn from `.pre-commit-config.yaml` (hooks stay hub-available; only corp's binding removed), §9 roster de-listed the toc bullet, and a `hub-toc-hooks` waiver added to `.methodology.yaml` (expected to retire once the manifest re-scopes the toc hooks off the fleet-generic set). #326 stays open (referenced, not closed). Genuine end-to-end re-read; `last_reviewed` re-stamped 2026-07-11.
- v2.8 (2026-07-13) — **T1 canonical baseline adoption** (content-parity inventory consumer leg; hub audit `2026-07-13-technical-content-parity-inventory.md`, A/B rows). Five GAP owner=hub regions materialized verbatim from `templates/claude-regions/`: `conventions-output-formatting` (§4), `critical-rules-records` (§5 rules 1–3), `critical-rules-consistency` (§5 rule 6), `critical-rules-no-leftovers` (§5 rule 9), `antipatterns-universal` (§10). Three already-present owner=hub regions overwritten to hub verbatim with adjacent owner=repo addenda preserving corp specifics: `first-read` (§1; corp handoff-location + VISION item 6 relocated to a `first-read-corp-addendum` span), `conventions-commit-branch` (§4; hub single-line branch/type rule, corp's `refactor/`-branch prose dropped — naming clarification, no substance lost), `session-start-protocol` (§6). **§5 rule-count divergence noted** (12 rules + graduated block > "≤10" guideline — corp legitimately carries more safety rules). **C2 defect fix:** §6 session-end line `Append` → **Prepend (newest-first)**, aligning with hub records-rule 2. §8 taxonomy re-categorized (user / built-in-plugin / repo skills, each naming provenance). §9 set-matched to live `.pre-commit-config.yaml`: added `validate-audit-casing` + the new `validate-backlog` (plugin twin, ADR-78 — wired this arc). Genuine end-to-end re-read; `last_reviewed` re-stamped 2026-07-13.
<!-- methodology:end id=section-history -->

---

**Last updated:** 2026-07-13  
**Maintained by:** Rob
