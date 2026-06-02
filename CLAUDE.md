# CLAUDE.md
<!-- scope: meta -->
<!-- version: 2.2 — 2026-05-27 -->

> **Session contract for Claude Code in this repo.** Read on every session start (auto). Single canonical agent-instruction file (≤200 lines). Per ADR-53.
>
> **For universal rules:** read `../.dev-knowledge/protocols/ESSENTIALS.md` and `protocols/PLAYBOOK.md`.

## 1. First read (session start)

In order, read:
1. This file (you're here)
2. `../.dev-knowledge/protocols/ESSENTIALS.md` — Rob's universal working style
3. `../.dev-knowledge/protocols/PLAYBOOK.md` — universal protocols (only sections relevant to current task)
4. Most recent corp-monorepo handoff bundle in `../.dev-knowledge/docs/handoffs/` if continuing prior session (ADR-36 — corp carries no local handoffs dir)
5. Last 5 entries of `JOURNAL.md`
6. `VISION.md` — project purpose and scope

**Skip if not applicable** — but always read 1–2.

## 2. Repo identity

- **Name:** `corp-monorepo`
- **Purpose:** Corporate OS — AI-powered knowledge management for Blue Yonder presales (ingest corporate source material → LLM extraction → Obsidian vault notes → FTS5 search; five CLIs drive all operations)
- **Status:** `active`

## 3. Architecture

See `ARCHITECTURE.md` for the structural model; read it before structural changes (required per ADR-51 — mandatory for every repo).

Key facts (abbreviated; `ARCHITECTURE.md` is authoritative):
- Unified `src/corp/` namespace — 6 former packages consolidated; one `pyproject.toml`
- 4-layer dependency model: `interface > orchestration > core > foundation` (Tach-enforced)
- 5 CLIs: `corp`, `corp-meta`, `cke`, `cpe`, `com`

## 4. Conventions

- **Naming:** `snake_case` Python, `kebab-case` markdown, UPPERCASE living docs; files: `{YYYY-MM}_{TYPE}_{CLIENT}_{Desc}.{ext}` (ADR-14)
- **Commits:** Conventional Commits — `feat:/fix:/docs:/chore:/refactor:/test:`
- **Branches:** `feat/`, `fix/`, `refactor/`, `chore/`, `docs/` off `main`; never commit to `main` directly
- **Testing:** `pytest -x --tb=short`; run `./scripts/run-all-tests.ps1` before merging
- **Linting:** pre-commit hooks — ruff (formatting/linting) + tach (dependency layers)
- **Config:** centralized in `config/paths.toml`; `GEMINI_API_KEY` is standard (not `GOOGLE_API_KEY`); ENV > config > default
- **Engagement:** 1 file/1 module → conversational; 2-3 files/1 module → conversational with context; 3+ files/2+ modules → formal `.md` prompt; architecture decision → AI Council debate

**Out of scope for this repo:**
- Client/pre-sales data → Obsidian vault
- Cross-repo lessons → `.dev-knowledge/LESSONS.md`

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

1. `/boot` (loads skills, memory, recent commits)
2. `git status` — clean working tree?
3. `git log --oneline -5` — recent context
4. Read most recent handoff if continuing
5. Read last 5 entries of `JOURNAL.md`
6. Wait for Rob's prompt — never improvise

**Session end:** Append entry to `JOURNAL.md` (ADR-49 shape, cutover 2026-05-18):
`### YYYY-MM-DD — <topic>` then `- Did:` / `- Result:` / `- Changes:` / `- Abandoned:` / `- Next:`.
`Changes:` is the sole change record (no CHANGELOG). Append-only; never edit prior entries.

**Handoffs:** Generated in `.dev-knowledge` per ADR-62/HANDOFF_PROCESS.md (v4 canonical; supersedes ADR-42 v3) — NOT in this repo (ADR-36 read-only contract).
Trigger: in Claude Code at `.dev-knowledge`, say "Make handoff for corp-monorepo".

## 7. Slash commands available

User-level (`~/.claude/commands/`):
- `/session-summary` — generate handoff at session end
- `/boot` — load context, skills, memory
- `/codex-review` — invoke Codex review
- `/evolve` — evolution audit

Repo-level (`./.claude/commands/`): none currently

## 8. Skills active

User-level (`~/.claude/skills/`):
- `gotchas` — universal dev gotchas (encoding, shell safety, test framework)
- `verify` — domain-specific verification; run after pytest passes
- `boot` — session boot; loads memory, verifies rules, checks trends

Repo-level (`./.claude/skills/`):
- `gotchas` — corp-monorepo patterns (CKE, vault ops, OneDrive safety, Graph API). **Read before changes.**

## 9. Hooks active

Pre-commit (from `.pre-commit-config.yaml`):
- ruff — linting and formatting
- tach — dependency layer enforcement (`interface > orchestration > core > foundation`)

Other (`.claude/settings.json`):
- Session startup hook — loads learned rules (6 lines)

## 10. Anti-patterns specific to Claude Code in this repo

- The Codex reviewer config is global (`~/.codex/AGENTS.md`, ADR-54); corp-monorepo has no per-repo `AGENTS.md`. Updates to the global config go in `.dev-knowledge/codex/AGENTS.md`.
- Don't assume module paths from old package names (`corp_by_os`, `corp_os_meta`, `corp_knowledge_extractor`) — all are now under `src/corp/`
- Don't run `pip install` from `_archived_*` repos — overwrites monorepo entry points
- Don't skip `scope/client/package/` hierarchy when staging CKE output for `corp ingest-extractions`
- Don't read `status.json` without try/except + retry (concurrent write risk from CKE)
- Don't bypass pre-commit with `--no-verify` — tach violations are real architecture violations

## 11. Recent ADRs binding here

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

## 12. Section history

- v1.0 (pre-2026-05-19) — original pre-template CLAUDE.md (Project Scale / Architecture / Development / Safety sections)
- v2.1 (2026-05-19) — rewritten to v2.1 12-section template per ADR-53; architecture content homed in ARCHITECTURE.md; §3 is pointer; §2 Purpose added; §10 AGENTS.md guard added
- v2.2 (2026-05-27) — struck tier-residue prose (§2 Scale line removed; §3/§11 "Scale M+" → "universal" per tier-system deprecation); §11 ADR references namespace-prefixed (corp vs `.dev-knowledge`; ADR-27 collision noted)

---

**Last updated:** 2026-05-27  
**Maintained by:** Rob
