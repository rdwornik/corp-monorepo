---
last_reviewed: 2026-07-11
status: active
owner: Rob
---

@.claude/CLAUDE-FLOOR.md

# CLAUDE.md
<!-- scope: meta -->
<!-- version: 2.6 — 2026-07-11 -->

> **Session contract for Claude Code in this repo.** Read on every session start (auto). Single canonical agent-instruction file (≤200 lines). Per ADR-53.
>
> **For universal rules:** read `../.dev-knowledge/protocols/ESSENTIALS.md` and `../.dev-knowledge/protocols/PLAYBOOK.md`.

> **Section ownership (methodology boundary):** sections marked `owner=hub` are fleet methodology tracked from the `.dev-knowledge` hub; `owner=repo` sections are project-local. The machine-readable owner map is the `<!-- methodology:… owner=… -->` markers on each section below; sanctioned divergences from hub-generic expectations are recorded in `.methodology.yaml`.

## 1. First read (session start)
<!-- methodology:start id=first-read owner=hub -->

In order, read:
1. This file (you're here)
2. `../.dev-knowledge/protocols/ESSENTIALS.md` — Rob's universal working style
3. `../.dev-knowledge/protocols/PLAYBOOK.md` — universal protocols (only sections relevant to current task)
4. Most recent corp-monorepo handoff bundle in `../.dev-knowledge/docs/handoffs/` if continuing prior session (ADR-36 — corp carries no local handoffs dir)
5. Last 5 entries of `JOURNAL.md`
6. `VISION.md` — project purpose and scope

**Skip if not applicable** — but always read 1–2.
<!-- methodology:end id=first-read -->

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
- **Commits:** Conventional Commits — `feat:/fix:/docs:/chore:/refactor:/test:`
- **Branches:** `feat/`, `fix/`, `refactor/`, `chore/`, `docs/` off `main`; never commit to `main` directly
<!-- methodology:end id=conventions-commit-branch -->
- **Testing:** `pytest -x --tb=short`; run `./scripts/run-all-tests.ps1` before merging
- **Linting:** pre-commit hooks — ruff (formatting/linting) + tach (dependency layers)
- **Config:** centralized in `config/paths.toml`; `GEMINI_API_KEY` is standard (not `GOOGLE_API_KEY`); ENV > config > default
- **Methodology:** `.methodology.yaml` (root) declares corp's sanctioned methodology divergences; read by the hub Informant at the fixed path `<repo-root>/.methodology.yaml` — keep at root, do not move to `config/`.
- **Engagement:** 1 file/1 module → conversational; 2-3 files/1 module → conversational with context; 3+ files/2+ modules → formal `.md` prompt; architecture decision → AI Council debate

**Out of scope for this repo:**
- Client/pre-sales data → Obsidian vault
- Cross-repo lessons → `../.dev-knowledge/LESSONS.md`

## 5. Critical rules

1. **corp (ingest/) is SOLE writer for `02_sources/` `.md` notes** (ADR-27; `actions/*` may write DASHBOARDS, METADATA, BRIEFS directly; all others via `vault_io.write_note()`). Enforced by `tests/safety/test_vault_writer_invariant.py`.
2. **CKE (extractor/) is PURE extraction engine** — no vault writes, no database writes.
3. **API keys in env vars ONLY** — loaded from `~/Documents/.secrets/.env`; NEVER in config files or code.
4. **OneDrive exclusion** — NEVER let cleanup or audit touch `OneDrive - Blue Yonder` paths (fail-closed guards at every mutation site; see ARCHITECTURE.md §OneDrive safety guards).
5. **Run `./scripts/run-all-tests.ps1` before merging; `./scripts/dev-check.ps1` before PR.**
6. **Check `~/.claude/skills/gotchas/` before modifying any module.**
7. **Forward slashes everywhere** in databases and stored paths.

**Graduated learned rules (verify lines are mandatory — gotchas system):**

- Never run `pip install` from `_archived_*` repos — overwrites monorepo CLI entry points. Only install from corp-monorepo root.
  `verify: Grep("pip install", path="corp-monorepo/") → confirm no install instructions point to archived repos`
- git subtree branches must NEVER be rebased — always merge. Rebase → duplicate commits and lost history.
  `verify: manual (process rule — check before any rebase on monorepo branches)`
- CKE output must be staged in `scope/client/package/` hierarchy BEFORE running `corp ingest-extractions`. Flat dirs → 0 notes ingested.
  `verify: Grep("ingest-extractions", path="corp-monorepo/") → check any docs/scripts for flat-dir usage`
- `status.json` concurrent reads must use try/except with 2-3 retries — CKE writes while polling reads cause JSONDecodeError.
  `verify: Grep("json.loads", path="corp-monorepo/src/corp/") → confirm retry wrapper exists`

## 6. Session start protocol
<!-- methodology:start id=session-start-protocol owner=hub -->

1. `git status` — clean working tree?
2. `git log --oneline -5` — recent context
3. Read most recent handoff if continuing
4. Read last 5 entries of `JOURNAL.md`
5. Wait for Rob's prompt — never improvise
<!-- methodology:end id=session-start-protocol -->

**Session end:** Append entry to `JOURNAL.md` (ADR-49 shape, cutover 2026-05-18):
`### YYYY-MM-DD — <topic>` then `- Did:` / `- Result:` / `- Changes:` / `- Abandoned:` / `- Next:`.
`Changes:` is the sole change record (no CHANGELOG). Append-only; never edit prior entries.

**Handoffs:** Generated in `.dev-knowledge` per ADR-62/HANDOFF_PROCESS.md (v4 canonical; supersedes ADR-42 v3) — NOT in this repo (ADR-36 read-only contract).
Trigger: in Claude Code at `.dev-knowledge`, say "Make handoff for corp-monorepo".

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

User-level (`~/.claude/skills/`):
- `gotchas` — universal dev gotchas (encoding, shell safety, test framework)

Bundled/plugin skills (loaded automatically by harness):
- `verify` — domain-specific verification; run after pytest passes

Repo-level (`./.claude/skills/`):
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
- toc-freshness / toc-generate — ARCHITECTURE.md TOC staleness check, hub-sourced (`repo: https://github.com/rdwornik/dev-knowledge` @ v1.3.1 = the deployed methodology version)
- backlog-id-on-close — commit-msg gate: requires `[#id]` in the message when a `BACKLOG.md` task line is removed (hub-sourced, v1.3.1)
- block-ff-push — pre-push gate: refuses a direct-to-main / fast-forward push to `main`; a `--no-ff` merge passes (hub-sourced, v1.3.1; core-invariant #5 prevent organ)

Other:
- `~/.claude/settings.json` (user-level): SessionStart hook — runs `surface-closures.ps1` (Tier-1 lifecycle closure surfacing, ADR-70).
- `./.claude/settings.json` (project-level): SessionStart — `scripts/surface-conformance.ps1` (nightly-conformance surfacing, fail-soft) + the methodology floor guard (`python .claude/check_floor_hash.py --require-present`) + the arm leg (`python -m pre_commit install`); Stop — `scripts/session_end_backpressure.py` (ADR-85 session-end gate; JOURNAL SHA-anchor hard block, `/override` is the only escape). All merge with the user-level hooks.
<!-- methodology:end id=hooks-repo-roster -->

## 10. Anti-patterns specific to Claude Code in this repo
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
<!-- methodology:end id=section-history -->

---

**Last updated:** 2026-07-11  
**Maintained by:** Rob
