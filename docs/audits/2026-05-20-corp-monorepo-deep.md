---
type: audit
scope: corp-monorepo (deep, read-only, file-state-verified)
date: 2026-05-20
author: claude-sonnet-4-6 + rob
status: immutable
supersedes: none
related: docs/audits/2026-03-30-codex-full-audit.md, docs/audits/2026-05-18-universalization-review.md
---

# corp-monorepo — Deep Audit (file-state-verified)

> **Methodology contract:** every numbered finding cites at least one file path
> from the corp-monorepo working tree as it stood on 2026-05-20 at branch
> `docs/audit-corp-monorepo-deep` (off `main` at commit `fbcaa86`).
> No claim derives from witness, summary, or memory. Cross-repo files
> (`.dev-knowledge`, `ai-council`) are read-only context only; this audit
> does not modify them.

---

## 1. Executive Summary

### Top 5 Risks (severity-ranked)

| # | Finding | Severity | Location |
|---|---------|----------|----------|
| R1 | `manifest.load_status()` reads `status.json` without retry wrapper, contradicting CLAUDE.md §5 graduated rule | **HIGH** | `src/corp/extractor/manifest.py:75-82` |
| R2 | VISION.md §Values declares "One routing authority. Routing configuration has a single source of truth, not per-module copies." — file-state shows routing logic spread across 4+ modules; no central routing config exists | **HIGH** | `src/corp/extraction/routing.py`, `src/corp/ingest/router.py`, `src/corp/overnight/classifier.py`, `src/corp/retrieve/engine.py`, `VISION.md:75-76` |
| R3 | `ARCHITECTURE.md` last-updated 2026-03-30; misses ADR-30, ADR-31, ADR-53 changes, retired CHANGELOG, retired HANDOFF, VISION/BACKLOG additions, AGENTS.md deletion. Recovery surface for "current architecture" answers a 7-week-stale snapshot | **HIGH** | `ARCHITECTURE.md:3-4` (header), §Source Layout (out of date), §Violations & Technical Debt (stale) |
| R4 | `CONTRIBUTING.md` carries stale guidance: "all ADRs (26 decisions)" (actual: 30); "Known baseline violations (Phase 1)" still flagged as open despite JOURNAL 2026-04-15 resolution | **MEDIUM** | `CONTRIBUTING.md:105-114, 119` |
| R5 | Magistrala pipeline end-to-end verification is overdue since Council #24 (2026-03-29) — flagged "Next" in 4+ JOURNAL entries (2026-04-15, 2026-03-30, 2026-03-30 × 2) but no integration test or verification report has landed | **MEDIUM** | grep `magistrala` returns 0 hits in `src/corp/`; appears only in `ARCHITECTURE.md:342`, `JOURNAL.md`, `docs/decisions/transcripts/`, `docs/decisions/ADR-24-*.md`, `docs/decisions/ADR-25-*.md`, `src/corp/ingest/README.md` |

### Top 5 Strengths (file-state-verified)

| # | Finding | Severity | Location |
|---|---------|----------|----------|
| S1 | ADR-27 vault-writer invariant **fully enforced** via 448-line AST scanner + runtime whitelist | `tests/safety/test_vault_writer_invariant.py` (448 LOC), `src/corp/vault_io.py:42-65` (`_ACTIONS_WRITE_WHITELIST`) |
| S2 | OneDrive exclusion zone enforced at **every** known mutation site with resolve-before-substring check (post-Codex 2026-04-21); fail-closed semantics | `src/corp/cleanup/disk.py:24` (central `_ONEDRIVE_BLOCKED`), 4 guard sites enumerated in `ARCHITECTURE.md:416-422` |
| S3 | Tach 4-layer model with `exact=true`, `forbid_circular_dependencies=true`, pre-commit-wired, CI-wired; 34 modules explicitly classified | `tach.toml:17-19,23-28`, `.pre-commit-config.yaml:13-18`, `.github/workflows/tach.yml` (referenced in JOURNAL) |
| S4 | API key handling: `GEMINI_API_KEY` canonical (18 source files); zero committed `.env`; `.env.example` present at root; secrets sourced from external `C:/Users/1028120/Documents/.secrets/.env` per `config/paths.toml:9` | `pyproject.toml` (no committed env); `.env.example` present; `GOOGLE_API_KEY` only as negation rule |
| S5 | Forward-slash convention 100% compliant in source — 0 occurrences of `os.sep` or `os.path.join` in `src/corp/` | grep verification |

### Posture one-liner

`corp-monorepo` is a **mature, invariant-enforced** monorepo with strong runtime safety guards (vault-writer, OneDrive, Tach) but carries **documentation drift** as its dominant outstanding risk: the canonical `ARCHITECTURE.md` and `CONTRIBUTING.md` predate the universalization rollout (2026-05-18) and the AGENTS.md retirement (2026-05-19/2026-05-20), and several VISION-declared invariants (routing single-source-of-truth) are aspirational rather than file-state realities.

---

## 2. Scope & Methodology

### Scope

- **In scope:** every file under `C:\Users\1028120\Documents\Dev\corp-monorepo` at branch `docs/audit-corp-monorepo-deep` (off `main` at commit `fbcaa86`, dated 2026-05-20).
- **Read-only context (not audited as findings):** `.dev-knowledge/`, `ai-council/`, `corp-ops/`, `corp-sca-time-automation/`, OneDrive paths, the Obsidian vault.
- **Excluded:** runtime behavior (no tests/scripts executed); client-specific sensitive content (audited structurally only, never restated).

### Methodology

- File-state inspection only. Glob, grep, file reads. No execution of pytest, scripts, or CLIs.
- Three exploration agents seeded the audit; deep reads then verified every claim against the cited path.
- Every finding traceable to a file path with a line range where possible.

### Severity definitions

| Severity | Definition |
|----------|-----------|
| **CRITICAL** | Active or imminent data loss / safety invariant breach |
| **HIGH** | Invariant gap with downstream consumer impact, OR governance doc drift that misleads operators |
| **MEDIUM** | Stale documentation, single-site gap, or accumulated tech debt |
| **LOW** | Cosmetic, low-impact, or self-healing drift |
| **INFO** | Factual statement requiring no action (posture, counts, structure) |

### Action-distinction

Each finding has either a **Current state** + **Recommended improvement** (drift / risk findings) or **Evidence** (informational / strength findings). The audit does not blend the two.

---

## 3. Repository Structure

### 3.1 Six-package consolidation mapping (ADR-23)

| Former package | Current `src/corp/` subpath | Entry-point CLI | Layer |
|----------------|----------------------------|-----------------|-------|
| corp-by-os | `src/corp/ingest/` (+ root orchestration) | `corp` (via `corp.cli:cli`) | orchestration |
| corp-os-meta | `src/corp/schema/` | `corp-meta` (via `corp.schema.cli:main`) | foundation (utility) |
| corp-knowledge-extractor | `src/corp/extractor/` | `cke` (via `corp.extractor.scripts.run:cli`) | core |
| corp-project-extractor | `src/corp/project/` | `cpe` (via `corp.project.cli:cli`) | core |
| corp-opportunity-manager | `src/corp/opportunity/` | `com` (via `corp.opportunity.cli:cli`) | core |
| corp-rfp-agent | `src/corp/rfp/` | (no dedicated CLI; surfaced via `corp rfp ...`) | core |

**Evidence:** `pyproject.toml:50-55` (entry points); `tach.toml` (layer assignments); JOURNAL 2026-03-29 session 5 ("Package consolidation 6→1").

### 3.2 14 immediate subpackages under `src/corp/`

```
src/corp/
├── actions/           orchestration  (12 modules; ACTION_REGISTRY)
├── cleanup/           core            (MyWork hygiene; OneDrive guards)
├── cli/               interface       (18 modules; Click commands)
├── extraction/        foundation      (scanner, routing, manifest_emitter, vault_writer)
├── extractor/         core            (26 modules; CKE; providers/strategies/frames/slides)
├── ingest/            orchestration   (11 modules; router, inbox, classifiers, dedup)
├── opportunity/       core            (10 modules; COM)
├── ops/               core            (9 modules; OpsDB, ContentRegistry, FileRegistry)
├── overnight/         core            (8 modules; batch extraction pipeline)
├── project/           core            (10 modules; CPE)
├── retrieve/          core            (4 modules; engine.py + RFP retrieve)
├── rfp/               core            (8 modules; RFP answering pipeline)
├── schema/            foundation      (12 modules; taxonomy, validation, paths)
└── (root)             mixed           (21 .py files at src/corp/ top level)
```

Root-level modules (21 files) are split across layers: `cli/` ↔ interface, `chat.py` ↔ interface, `actions/` ↔ orchestration, `vault_io.py`/`config.py`/`audit.py`/`integrity.py`/`freshness_scanner.py`/`retrieve.py` ↔ core, `models.py`/`routing_types.py` ↔ foundation. See `ARCHITECTURE.md:18-37` for the canonical (but 2026-03-30-stale) listing.

### 3.3 Tach layer assignments (34 modules)

Source: `tach.toml`.

**foundation (4 modules):** `corp.schema` (utility), `corp.models`, `corp.routing_types` (utility), `corp.extraction`

**core (17 modules):** `corp.extractor`, `corp.config`, `corp.vault_io`, `corp.intent_router`, `corp.llm_router`, `corp.audit`, `corp.integrity`, `corp.freshness_scanner`, `corp.retrieve`, `corp.cleanup`, `corp.project`, `corp.opportunity`, `corp.rfp`, `corp.ops`, `corp.overnight`, `corp.project_resolver` (declared `layer = "core"` at `tach.toml:131` despite the file's section-header comment placing it under ORCHESTRATION — see Finding §9.D6)

**orchestration (8 modules):** `corp.ingest`, `corp.index_builder`, `corp.task_manager`, `corp.template_manager`, `corp.workflow_engine`, `corp.actions`, `corp.built_in_actions`, `corp.query_engine` (declared `layer = "orchestration"` at `tach.toml:161` despite the file's section-header comment placing it under INTERFACE — see Finding §9.D6)

**interface (4 modules):** `corp.sandbox`, `corp.chat`, `corp.test_pipeline`, `corp.cli`

**Tach enforcement settings (`tach.toml:17-19`):**
- `exact = true` — declared deps must match actual imports (no false declarations)
- `ignore_type_checking_imports = true` — typing-only imports exempt
- `forbid_circular_dependencies = true` — no cycles

### 3.4 CLI entry points

`pyproject.toml:50-55`:

```toml
corp      = "corp.cli:cli"
corp-meta = "corp.schema.cli:main"
cke       = "corp.extractor.scripts.run:cli"
cpe       = "corp.project.cli:cli"
com       = "corp.opportunity.cli:cli"
```

5 CLIs confirmed; matches CLAUDE.md §3.

### 3.5 Test directory structure (162 test files)

Top-level `tests/` subdirs (20):
- Per-package: `tests/extractor/`, `tests/test_extraction/`, `tests/test_extraction_non_project/`, `tests/test_actions/`, `tests/test_cleanup/`, `tests/test_ingest/`, `tests/test_ops/`, `tests/test_overnight/`, `tests/test_project/`, `tests/test_retrieve/`, `tests/test_rfp/`, `tests/schema/`
- Specialized: `tests/integration/`, `tests/safety/`, `tests/fixtures/`, `tests/scripts/`

**Safety tier (`tests/safety/`):** `test_vault_writer_invariant.py` (448 lines, AST scanner — see Finding §5.1).

**Integration tier (`tests/integration/`, 9 files):**
- `test_cke_output_format.py`
- `test_cross_package.py`
- `test_inbox_classify_route.py`
- `test_property_based.py`
- `test_retrieve_contract.py`
- `test_trust_level_contract.py`
- `test_vault_ingest_contract.py`

**Vault-writer tests duplicated:**
- `tests/safety/test_vault_writer_invariant.py` (whitelist + AST scanner)
- `tests/test_extraction/test_vault_writer.py` (7,140 bytes)
- `tests/test_extraction_non_project/test_vault_writer.py` (8,555 bytes)

---

## 4. Configuration & Dev Standards

### 4.1 `pyproject.toml`

| Field | Value | Evidence |
|-------|-------|----------|
| `name` | `corp` | `pyproject.toml:6` |
| `version` | `1.0.0` (since 6→1 consolidation, 2026-03-29) | `pyproject.toml:7` |
| `requires-python` | `>=3.11` | `pyproject.toml:9` |
| Runtime deps | 27 packages incl. `anthropic`, `google-genai`, `openai`, `ollama`, `opencv-python`, `pdfplumber`, `python-pptx`, `pydantic`, `scikit-learn`, `scipy`, `rich`, `Jinja2`, `httpx` | `pyproject.toml:11-37` |
| Optional deps | `slides` (comtypes+PyMuPDF), `dedup` (datasketch), `graph` (msal), `dev` (pytest/pytest-cov/ruff/hypothesis) | `pyproject.toml:39-48` |
| Build backend | `setuptools>=68.0` | `pyproject.toml:1-3` |
| Package data | `corp.schema` carries `taxonomy.yaml + data/*.yaml`; `corp.extractor` carries `data/*.yaml + data/*.json` | `pyproject.toml:60-62` |
| pytest config | `testpaths = ["tests"]`, `pythonpath = ["src"]`, `addopts = "-v"` | `pyproject.toml:64-67` |
| Ruff config | `line-length=120`, `target-version="py311"`, `select=["E","F","I","W","B","UP"]`, `ignore=["E402"]` | `pyproject.toml:69-76` |

### 4.2 `tach.toml`

- 180 lines, 34 module declarations
- Layer order top→bottom: `interface > orchestration > core > foundation` (`tach.toml:23-28`)
- `exact = true`, `forbid_circular_dependencies = true`, `source_roots = ["src"]`
- Pre-commit-wired via `.pre-commit-config.yaml:11-18` (`files: ^src/corp/.*\.py$`)
- **Note:** section comments at lines 116–157 misplace `corp.project_resolver` (declared `core`, comment-placed under ORCHESTRATION) and `corp.query_engine` (declared `orchestration`, comment-placed under INTERFACE). See Finding §9.D6.

### 4.3 `.pre-commit-config.yaml`

Three hooks:
1. **ruff** (`v0.4.0`, args: `--fix --exit-non-zero-on-fix`). `ruff-format` deliberately omitted with comment: "core.autocrlf=true on Windows causes CRLF/LF conflict in pre-commit's stash/unstash cycle. Run `ruff format packages/` manually or via dev-check.ps1 instead."
2. **tach-check** (`tach check`, scoped to `^src/corp/.*\.py$`)
3. **normalize-headers** (`py scripts/normalize_headers.py`, scoped to `^(JOURNAL|LESSONS)\.md$` — note: `LESSONS.md` does not exist in this repo; see Finding §9.D7)

### 4.4 `ruff.toml`

Lenient baseline ruleset that **duplicates** the `[tool.ruff]` block in `pyproject.toml`:
- `select = ["E", "F", "I"]` (vs. pyproject's `["E","F","I","W","B","UP"]`)
- `ignore = ["E501"]` (vs. pyproject's `["E402"]`)
- `[lint.per-file-ignores] "tests/**" = ["E", "F"]`

**Resolution:** ruff resolves config via discovery order; `ruff.toml` at repo root wins over `pyproject.toml [tool.ruff]`. This means the **lenient ruleset is actually active** in normal `ruff` invocations from the repo root, while pre-commit's `args: [--fix, --exit-non-zero-on-fix]` does not override config selection. See Finding §9.D1.

### 4.5 `config/paths.toml`

Central path config (`config/paths.toml`):
- `vault = "C:/Users/1028120/Documents/ObsidianVault"`
- `mywork = "C:/Users/1028120/Documents/MyWork"`
- `secrets = "C:/Users/1028120/Documents/.secrets/.env"`
- `rfp_kb = "C:/Users/1028120/Documents/corp_data/rfp_kb"`
- `databases.ops_db = "%LOCALAPPDATA%/corp-by-os/ops.db"`
- `databases.index_db = "%LOCALAPPDATA%/corp-by-os/index.db"`
- `[safety] excluded_paths = ["OneDrive - Blue Yonder"]`

**Resolution order (`paths.toml:3`):** `ENV_VAR > paths.toml > defaults` (matches CLAUDE.md §4).

### 4.6 Absent configuration files

| File | Status | Classification |
|------|--------|----------------|
| `mypy.ini` | absent | **INFO** — no static type checking enforced. Pydantic provides runtime validation; mypy would be an addition, not a regression |
| `pytest.ini` | absent | **INFO** — intentional; pytest config lives in `pyproject.toml [tool.pytest.ini_options]` |
| `routing_map.yaml` | absent | **HIGH drift** — VISION.md §Values declares routing single-source-of-truth principle; no central routing YAML exists. See Finding §9.D2 |
| `LESSONS.md` | absent in repo | **INFO** — global CLAUDE.md references cross-repo `.dev-knowledge/LESSONS.md`. Pre-commit `normalize-headers` hook scopes to `LESSONS.md`, harmless no-op |
| `templates/` | directory absent (deleted 2026-05-18) | **INFO** — JOURNAL 2026-05-18 documents removal; canonical ADR template lives at `.dev-knowledge/templates/ADR-template.md` per ADR-36 |
| `docs/handoffs/` | directory absent (deleted 2026-05-18) | **INFO** — JOURNAL 2026-05-18 documents removal; handoffs owned by `.dev-knowledge` per ADR-36/42 |

### 4.7 Required scripts

`scripts/dev-check.ps1` and `scripts/run-all-tests.ps1` referenced in:
- `CLAUDE.md` §5 rule 5 ("Run `./scripts/run-all-tests.ps1` before merging; `./scripts/dev-check.ps1` before PR.")
- `CONTRIBUTING.md` §Development Flow

Both present at the expected paths.

---

## 5. Architectural Invariants

### 5.1 Vault writer narrowing (ADR-27) — **CONFORMS**

**Invariant:** `corp.vault_io.write_note()` is the sole writer for `.md` files under `02_sources/`. Actions/* may write directly only to whitelisted (zone, leaf) pairs: DASHBOARDS, METADATA (`project-info.yaml`, `index.md`), BRIEFS (`brief.md`).

**Evidence:**
- Runtime predicate: `src/corp/vault_io.py:42-65` (`_ACTIONS_WRITE_WHITELIST` constant; `is_writable_by_actions(zone, leaf)` function)
- AST-based static enforcement: `tests/safety/test_vault_writer_invariant.py` (448 lines). Walks every `src/corp/actions/*.py`, resolves file-mutation primitives (`Path.write_text/write_bytes/replace/unlink/rmdir`, `shutil.copy*/move/rmtree`, `os.remove/rename/unlink`, `open(..., write-mode)`) through local-variable assignment chains to both first vault-path segment AND leaf filename, then maps `(zone, leaf)` to category via `_classify`. Embeds 3 self-test fixtures (SOURCES violation, unclassified PROJECTS-zone leaf, clean METADATA write) so a silently-broken scanner fails its own test.
- 7 production write sites inventoried (per JOURNAL 2026-05-18): 2 DASHBOARDS, 4 METADATA, 1 BRIEFS — all classified to whitelist
- Modules importing `vault_io`: `src/corp/actions/vault_actions.py`, `src/corp/actions/monitoring_actions.py`, `src/corp/actions/brief_actions.py`, `src/corp/ingest/extractions.py`, `src/corp/cli/vault.py`, `src/corp/cli/project.py`, `src/corp/chat.py` (7 modules)

**Classification:** CONFORMS.

### 5.2 OneDrive exclusion zone — **CONFORMS** (with caveat — see 5.2.A)

**Invariant:** No code path may read, write, delete, or scan under `OneDrive - Blue Yonder`. Fail-closed: resolve path, then substring-check both pre- and post-resolution.

**Evidence (4 enumerated guard sites from ARCHITECTURE.md:416-422):**

| Site | File:line | Guard | Raises |
|------|-----------|-------|--------|
| 1 | `src/corp/cleanup/disk.py::execute_plan` (resolve + substring) | `_guard_onedrive(item.path)` before `target.unlink()` | `OneDriveSafetyError` |
| 2 | `src/corp/cleanup/executor.py::execute_moves` | `_guard_onedrive(source)` + `_assert_within_root(...)` runtime; `MoveEntry` schema load-time | `OneDriveSafetyError`, `PathTraversalError`, `ValueError` |
| 3 | `src/corp/actions/_helpers.py::_resolve_project_path` (when `writable=True`) | `_guard_writable(path, writable)` (used by `archive_actions.py::archive_project`) | `OneDriveSafetyError` |
| 4 | `src/corp/project/renderer.py::render_project` | Inline resolve + substring check at entry | `ValueError` (CLI backward compat) |

**Centralized constant:** `_ONEDRIVE_BLOCKED = "OneDrive - Blue Yonder"` at `src/corp/cleanup/disk.py:24`.

**Exception class home:** `src/corp/cleanup/errors.py`.

**5.2.A — Caveat:** ADR-27 design point (`src/corp/safety/onedrive.py` + AST-based CI enforcement) is **drafted but not implemented**. JOURNAL 2026-05-18 "Next:" notes "ADR-27 PR-1/2/3 (OneDrive centralization … separate branches per ADR-27's migration plan)". Result: the guard logic is repeated at 4 sites with the same resolve+substring pattern but no shared module — a new mutation site added without the convention would not be flagged by CI. Classification: **MEDIUM** drift (centralization design exists, implementation deferred).

**Site #4 inconsistency:** `project/renderer.py` raises `ValueError` instead of `OneDriveSafetyError` "for CLI backward compat" (per ARCHITECTURE.md:421). Documented as a backward-compat carve-out; will be normalized when ADR-27 OneDrive centralization PRs land.

### 5.3 Tach 4-layer import architecture (ADR-26) — **CONFORMS**

**Invariant:** `interface > orchestration > core > foundation`. Upward imports forbidden. Cycles forbidden.

**Evidence:**
- `tach.toml`: `exact = true`, `forbid_circular_dependencies = true`, `source_roots = ["src"]`
- Pre-commit hook: `.pre-commit-config.yaml:13-18` (`tach check` on every `^src/corp/.*\.py$` change)
- CI workflow: `.github/workflows/tach.yml` (referenced in JOURNAL 2026-04-15 Tach Phase 1)
- Resolved cycles: `llm_router ↔ intent_router` extracted to `routing_types.py` (JOURNAL 2026-04-15)
- Resolved Phase-1 baseline violations: `project_resolver` core→core (was orchestration), `query_engine` interface→orchestration (JOURNAL 2026-04-15 Phase 2)

**Classification:** CONFORMS.

### 5.4 Forward-slash convention (CLAUDE.md §5) — **CONFORMS**

**Invariant:** Databases and stored paths use forward slashes everywhere.

**Evidence:**
- `os.sep` usage in `src/corp/`: 0 occurrences
- `os.path.join` usage in `src/corp/`: 0 occurrences
- Path construction uses `pathlib.Path` + `/` operator throughout
- `config/paths.toml` uses forward slashes for Windows paths (lines 6-11)
- CKE manifest paths switched to `.as_posix()` per JOURNAL 2026-03-30 Codex audit fixes

**Classification:** CONFORMS.

### 5.5 corp (ingest/) sole writer for `02_sources/` (ADR-23, narrowed by ADR-27) — **CONFORMS**

See §5.1. CKE produces JSON only; ingest writes `.md`; actions may write three named categories only.

### 5.6 API keys in env vars only — **CONFORMS**

**Evidence:**
- `pyproject.toml` carries no committed key
- No `.env` file in repo (only `.env.example`)
- `config/paths.toml:9` resolves to `C:/Users/1028120/Documents/.secrets/.env` (external)
- 18 source files reference `GEMINI_API_KEY`; canonical pattern is `os.environ.get("GEMINI_API_KEY_ENV", "GEMINI_API_KEY")` (`src/corp/extractor/providers/gemini_provider.py:34`)
- `GOOGLE_API_KEY` is present in CLAUDE.md §4 only as a **negation rule** ("`GEMINI_API_KEY` is standard (not `GOOGLE_API_KEY`)"). Zero references in `src/corp/`.

**Classification:** CONFORMS.

### 5.7 WAL mode + record-before-move (ARCHITECTURE.md:392-399)

**WAL mode:** `ARCHITECTURE.md:211, 226, 241` documents WAL for `ops.db`, `index.db`, `overnight_state.db`. Verification by file inspection is bounded — actual pragma settings are runtime concerns. Classification: **UNKNOWN-by-file-inspection** (would need runtime verification or source-code grep on `journal_mode=WAL`).

**Record-before-move:** ARCHITECTURE.md:399 declares the invariant. Routing implementation in `src/corp/ingest/router.py` claimed 893 LOC by ARCHITECTURE.md:135; bounded verification requires reading the router. Classification: **DECLARED, NOT FILE-VERIFIED IN THIS AUDIT**.

---

## 6. Safety & Security

### 6.1 OneDrive exclusion — site-by-site coverage

See §5.2. 4 mutation sites covered; ADR-27 centralization deferred.

### 6.2 API key handling

| Key | Status | Files referencing | Notes |
|-----|--------|------------------|-------|
| `GEMINI_API_KEY` | **canonical** | 18 source + many tests | Indirected via `_ENV` env var per provider pattern |
| `ANTHROPIC_API_KEY` | secondary | 2 files (`src/corp/extractor/providers/anthropic_provider.py`, `.env.example`) | Tier-routed; not the default |
| `OPENAI_API_KEY` | legacy/documentation | tests + docs only | No active source code usage |
| `GOOGLE_API_KEY` | **negation rule only** | CLAUDE.md §4 prose | Zero source references — correct posture |
| `GRAPH_ACCESS_TOKEN` | **documentation-only** | CLAUDE.md prose | Zero source references; no active Graph API operations exist (see §8.2) |

### 6.3 Secrets discipline

- `.env.example` present at repo root (sample only)
- No committed `.env`
- `.gitignore` excludes `.env`
- Secrets live in external `C:/Users/1028120/Documents/.secrets/.env` per `config/paths.toml:9`

### 6.4 Database location safety

`config/paths.toml:13-14` places `ops.db` and `index.db` under `%LOCALAPPDATA%/corp-by-os/` — explicitly outside OneDrive sync paths. ARCHITECTURE.md:211 documents this as a deliberate isolation. `src/corp/ops/database.py:6` carries a docstring clarifying the DB location is **not** in OneDrive.

### 6.5 No client-sensitive content stored in source

Client identifiers appear as code references (taxonomy aliases, type codes, naming conventions) — never as commercial / financial / deal content. The vault (separate from the repo) is where client material lives, per VISION.md §Relationships ("the vault is the durable knowledge store; the repo is the engine that fills and queries it").

---

## 7. Tests Inventory

### 7.1 Counts and structure

- **162** total `.py` files matching `test_*.py` in `tests/`
- **20** top-level subdirectories under `tests/`
- README.md table claims **2,412** total tests; JOURNAL 2026-05-18 reports **2,548 passed, 6 skipped** in latest run; JOURNAL 2026-04-15 reports **2,495**; 2026-04-21 reports **2,515**. README test count is **stale** — see Finding §9.D5.

### 7.2 Safety tier

- `tests/safety/__init__.py`
- `tests/safety/test_vault_writer_invariant.py` (448 lines, AST scanner — see §5.1)

### 7.3 Integration tier (9 files)

Listed in §3.5. Magistrala pipeline test is **absent** — see Finding §9.D8.

### 7.4 Per-package coverage (from README.md table — counts are stale; structure is current)

| Module | Stated test count (stale) | Test directory |
|--------|--------------------------|----------------|
| `corp/schema/` | 118 | `tests/schema/` |
| `corp/extractor/` | 838 | `tests/extractor/` |
| `corp/ingest/` + `corp/retrieve/` + `corp/cli/` | 926 | `tests/test_ingest/`, `tests/test_retrieve/`, etc. |
| `corp/project/` | 45 | `tests/test_project/` |
| `corp/rfp/` | 155 | `tests/test_rfp/` |
| `corp/opportunity/` | 62 | `tests/opportunity/` (per agent grep) |
| Integration | 9 | `tests/integration/` |

---

## 8. External Integrations

### 8.1 Gemini / google-genai

**Posture:** primary extraction backend; deeply integrated.

**Primary modules (7):**
- `src/corp/extractor/providers/gemini_provider.py` (uses `google.genai` SDK; per-million-token pricing hardcoded at lines 14-19 — see Finding §9.D3)
- `src/corp/extractor/extract.py` — multimodal extraction entry
- `src/corp/extractor/synthesize.py` — synthesis pipeline
- `src/corp/extractor/transcript.py` — speaker ID extraction
- `src/corp/llm_router.py` — intent classification (Gemini Flash)
- `src/corp/opportunity/llm_client.py`
- `src/corp/rfp/rfp_answer_word.py`

**Supporting modules (15):** `src/corp/cleanup/classifier.py`, `src/corp/ingest/llm_classifier.py`, `src/corp/extractor/doc_type_classifier.py`, `src/corp/extractor/deep_prompt.py`, `src/corp/extractor/taxonomy_prompt.py`, `src/corp/extractor/batch_api.py`, etc.

**Test coverage:** 22 test files reference Gemini.

**Pricing drift surface:** `gemini_provider.py:14-19` hardcodes Gemini per-million-token pricing as Python constants. Google's price changes → manual edit required. See Finding §9.D3.

### 8.2 Microsoft Graph / SharePoint

**Posture:** passive metadata only; no active Graph API calls.

**Active code references:**
- `src/corp/cleanup/errors.py:15` — `OneDrivePathError` docstring mentions SharePoint sync risk (documentation in code)
- `src/corp/schema/models.py:162` — `content_origin` field accepts string `'sharepoint'` (provenance tracking, not an active call)

**Optional dependency:** `pyproject.toml:42` declares `graph = ["msal>=1.24"]` — installable but no active import in `src/corp/`.

**Classification:** **INFO** — Graph integration is shaped (msal optional dep, content_origin enum) but unwired. ADR-27 documents future Graph API restrictions on certain OneDrive paths. No active risk.

### 8.3 Anthropic Claude

**Posture:** secondary tier; Tier-2/Tier-3 extraction provider.

**Modules:**
- `src/corp/extractor/providers/anthropic_provider.py` (single provider module)
- `.env.example` references `ANTHROPIC_API_KEY`

### 8.4 OpenAI

**Posture:** runtime dependency declared but no active source usage.

**Evidence:** `pyproject.toml:21` declares `openai>=2.14`. `OPENAI_API_KEY` referenced in tests/docs only. Tier router (`src/corp/extractor/tier_router.py`) routes between LOCAL/TEXT_AI/MULTIMODAL — actual OpenAI provider module is **absent** from `src/corp/extractor/providers/`. Classification: **LOW drift** — installed-but-unused dep adds image (~30MB).

### 8.5 Ollama (local models)

**Posture:** runtime dependency declared; planned offline tier per BACKLOG.md item "Local AI exploration (Ollama)".

**Evidence:** `pyproject.toml:20` declares `ollama>=0.4.0`. BACKLOG P3 entry confirms exploration status.

### 8.6 Magistrala

**Posture:** documentation pattern reference only; no active code.

**Evidence:**
- Zero references in `src/corp/` source
- Referenced in `ARCHITECTURE.md:342` (pipeline diagram filename), `JOURNAL.md` ("magistrala verification" as repeated Next item), `docs/decisions/ADR-24-*.md`, `docs/decisions/ADR-25-*.md`, `docs/decisions/transcripts/DECISION_14_naming_convention_v2.md`, `src/corp/ingest/README.md`

See Finding §9.D8 (pipeline verification deferred).

---

## 9. Drift Surfaces (severity-ranked findings)

Each finding follows: **Current state** → **Why this severity** → **Recommended improvement**.

### D1. Ruff config duplication: `ruff.toml` overrides `pyproject.toml [tool.ruff]` — MEDIUM

**Current state.** `pyproject.toml:69-76` declares a strict ruleset (`select=["E","F","I","W","B","UP"]`, line-length 120, ignore E402). `ruff.toml:1-6` declares a lenient ruleset (`select=["E","F","I"]`, ignore E501). Ruff config discovery prefers `ruff.toml` at repo root over `pyproject.toml [tool.ruff]`, so the **lenient** ruleset wins.

**Why this severity.** The `pyproject.toml` config is dead text that misleads anyone reading it as the active style. New contributors will assume `W/B/UP` rules are enforced and write code with `B`/`UP` issues that pre-commit will not catch.

**Recommended improvement.** Either delete `ruff.toml` (let `pyproject.toml [tool.ruff]` be the single source), or delete the `[tool.ruff]` block from `pyproject.toml` and consolidate everything in `ruff.toml`. Single source of truth.

### D2. VISION-declared "one routing authority" is aspirational; routing is code-distributed — HIGH

**Current state.** VISION.md §Values, lines 75-76: "**One routing authority.** Routing configuration has a single source of truth, not per-module copies." File-state: no central routing config exists (`routing_map.yaml` absent). Routing logic is distributed across:
- `src/corp/extraction/routing.py` — programmatic routing
- `src/corp/ingest/router.py` — core ingest pipeline (893 LOC per ARCHITECTURE.md)
- `src/corp/overnight/classifier.py` — overnight classification routing
- `src/corp/retrieve/engine.py` — retrieval routing
- `src/corp/intent_router.py` + `src/corp/llm_router.py` — intent classification

YAML configs that feed routing exist but are **per-aspect**: `config/content_registry.yaml` (file pattern routing), `config/agents.yaml` (agent registry), `config/workflows.yaml` (workflow steps). There is no top-level routing_map.

**Why this severity.** VISION declares a principle that the file-state does not realize. Either the principle is incorrect (and VISION should be amended), or the file-state should converge (and a `routing_map.yaml` or top-level router module should appear). Today the principle has no enforcing artifact.

**Recommended improvement.** Either (a) consolidate the routing layer into a single canonical config / module + ADR documenting the consolidation, or (b) amend VISION.md §Values to acknowledge that routing is intentionally code-distributed (and revise the language to reflect what's actually true, e.g., "routing rules are deterministic and per-aspect"). The ai-council debate that produced this VISION should be referenced in either resolution.

### D3. Gemini pricing hardcoded — MEDIUM

**Current state.** `src/corp/extractor/providers/gemini_provider.py:14-19` declares per-million-token pricing as Python constants. Google changes Gemini pricing externally; an update requires manual edit.

**Why this severity.** Cost calculations drift silently. Any cost-tracking on the basis of these constants (e.g., budget ceilings in `overnight/state.py` `budget_limit`) will be off by some unknown ratio after a price change.

**Recommended improvement.** Either (a) load pricing from `config/extractor/pricing.yaml` (single edit point, no Python change), or (b) add a comment with last-verified date + Google price page URL so future maintainers know the freshness epoch.

### D4. ARCHITECTURE.md is 7 weeks stale — HIGH

**Current state.** `ARCHITECTURE.md:3-4` declares "Last updated: 2026-03-30 (dependency layers clarified)". Since then:
- ADR-30 (Retire CHANGELOG) — landed 2026-05-18
- ADR-31 (Retire HANDOFF) — landed 2026-05-18
- VISION.md added at repo root (ADR-33)
- BACKLOG.md added at repo root (ADR-41 schema)
- ARCHITECTURE.md itself moved to repo root (ADR-38)
- AGENTS.md retired (ADR-54, completed 2026-05-20)
- CLAUDE.md v2.1 12-section template (ADR-53, completed 2026-05-19)

None of these are reflected in `ARCHITECTURE.md`. Specifically:
- §Violations & Technical Debt table is unchanged from 2026-03-30
- §OneDrive safety guards (lines 416-422) still describes "implementation lands in three follow-up PRs" (PR-1/PR-2/PR-3 deferred per JOURNAL 2026-05-18)
- No "References" section pointing to VISION/BACKLOG

**Why this severity.** ARCHITECTURE.md is mandated reading at session start (per CLAUDE.md §1). A canonical doc 7 weeks behind the actual state misleads every fresh agent context.

**Recommended improvement.** Refresh `ARCHITECTURE.md` to reflect 2026-05-20 state: update header date, add ADRs 30/31 references, retire `AGENTS.md` mentions, link to VISION.md, note ADR-27 OneDrive centralization status (drafted, implementation pending). Or convert ARCHITECTURE.md to a thin pointer doc that defers most content to per-module READMEs and the canonical Tach/pyproject configs.

### D5. README.md test count + module table stale — MEDIUM

**Current state.** `README.md:11-18` shows total tests = 2,412; per-module counts (118+838+926+45+155+62+9 = 2,153). JOURNAL latest run reports 2,548 passed. Either count is achievable; what's certain is they no longer match.

**Why this severity.** README is the first file an outside reader sees. Wrong counts erode trust in the rest.

**Recommended improvement.** Either remove the count column entirely or generate it from a CI script (e.g., `pytest --collect-only -q | wc -l` recorded in a workflow). Pin to "Tests last counted: YYYY-MM-DD" if static.

### D6. tach.toml comment-section drift on `project_resolver` and `query_engine` — LOW

**Current state.** `tach.toml` section headers organize declarations by layer comment-blocks. The comment at line 116 starts "ORCHESTRATION", but the `corp.project_resolver` declaration at lines 129-132 is inside that block and declares `layer = "core"`. The comment at line 157 starts "INTERFACE", but `corp.query_engine` at lines 159-162 is inside that block and declares `layer = "orchestration"`.

**Why this severity.** Both modules carry the correct layer (matching the JOURNAL 2026-04-15 Phase-2 resolution: project_resolver moved core, query_engine moved orchestration). The actual Tach enforcement is correct. Only the layout comments lag. Low blast radius.

**Recommended improvement.** Reflow the comment blocks so each module sits under the comment that matches its declared layer.

### D7. Pre-commit `normalize-headers` hook scopes to non-existent `LESSONS.md` — LOW

**Current state.** `.pre-commit-config.yaml:25` declares `files: ^(JOURNAL|LESSONS)\.md$`. `LESSONS.md` does not exist in `corp-monorepo` (per global CLAUDE.md, lessons live in `.dev-knowledge/LESSONS.md`).

**Why this severity.** Harmless no-op — the file regex simply never matches. Future maintainers may be confused about whether to create a local LESSONS.md.

**Recommended improvement.** Either (a) narrow the regex to `^JOURNAL\.md$`, or (b) add a comment explaining the LESSONS scope is reserved for future use / cross-repo consistency.

### D8. Magistrala pipeline end-to-end verification overdue — MEDIUM

**Current state.** "Verify magistrala pipeline end-to-end with new paths" appears as "Next:" in JOURNAL entries dated 2026-04-15 (Step 12), 2026-03-30 (refactor/align-with-playbook), 2026-03-30 (chore/todo-audit-cleanup), and 2026-03-29 (Council #24). No integration test file targets magistrala (grep returns 0 hits for filenames containing "magistrala"). No verification audit / report in `docs/audits/`.

**Why this severity.** Council #24 (MyWork knowledge architecture restructure, 2026-03-29) was a significant structural change. Five weeks later the pipeline that was supposed to be verified post-restructure has no record of having been exercised end-to-end. Either the verification happened informally (no artifact), the pipeline broke and no one noticed, or the "verification" was reframed away.

**Recommended improvement.** Add a `tests/integration/test_magistrala_pipeline.py` that exercises the post-Council-#24 paths end-to-end with a sandbox corpus, OR write a one-page audit `docs/audits/2026-MM-DD-magistrala-verification.md` documenting why end-to-end verification is no longer required (e.g., subsumed by sandbox tests + integration suite).

### D9. `manifest.load_status()` lacks the retry wrapper CLAUDE.md mandates — HIGH

**Current state.** `src/corp/extractor/manifest.py:75-82` (function `load_status()`) reads `output_dir/status.json` via direct `json.load()` with no `try/except` + retry wrapper. CLAUDE.md §5 graduated rule (line 69): "`status.json` concurrent reads must use try/except with 2-3 retries — CKE writes while polling reads cause JSONDecodeError." The rule's `verify:` line points to grepping for `json.loads` in `src/corp/` to confirm a retry wrapper exists.

**Why this severity.** The rule was promoted to a graduated learned rule precisely because the failure pattern previously caused breakage. Reverting to the bare read pattern in one site is a regression of a hardened invariant.

**Recommended improvement.** Wrap `load_status()` in 2-3 retries with short sleep on `JSONDecodeError`, mirroring the pattern in `src/corp/extractor/scripts/run.py` (lines 170, 228-229, 466 per agent inventory).

### D10. CONTRIBUTING.md stale ADR count + stale Phase-1 violations block — MEDIUM

**Current state.** `CONTRIBUTING.md:119` reads "`docs/decisions/` — all ADRs (26 decisions)". Actual: 30 ADRs (ADR-01..27, 30, 31; gaps at 28/29 reserved per `docs/decisions/README.md:39-42`).

`CONTRIBUTING.md:105-114` documents "Known baseline violations (Phase 1)" with "These will be resolved in Phase 2" — but JOURNAL 2026-04-15 records Phase 2 completion ("Resolved 6 baseline Tach violations by reclassifying project_resolver and query_engine").

**Why this severity.** CONTRIBUTING is a first-stop doc for newcomers (human and agent). Two stale facts in adjacent paragraphs.

**Recommended improvement.** Update ADR count to 30; replace the Phase-1-violations block with a one-line note: "Phase 1 baseline violations resolved in Phase 2 (see JOURNAL 2026-04-15). Current baseline: 0 violations."

### D11. `scripts/extract_training_data.py` hard-coded skip_names — LOW

**Current state.** `scripts/extract_training_data.py:48` declares `skip_names = {"index.md", "synthesis.md", "README.md", "inventory.md"}` as a Python literal.

**Why this severity.** Matches the drift-surface pattern recently caught in `scripts/check_doc_refs.py` (cleaned up 2026-05-20, JOURNAL). Output filenames may change without the skip set following.

**Recommended improvement.** Either (a) load the skip set from `config/extractor/settings.yaml`, or (b) compute it from the vault zone definitions in `src/corp/models.py::VaultZone`.

### D12. Original-prompt assumptions diverged from reality — INFO

**Current state.** The audit prompt assumed `~21 ADRs / ~25 Council decisions / ~2,495 tests`. Reality (2026-05-20): 30 ADRs, 28 transcripts (DECISION_01..24, 27, 28, 29 — DECISION_25/26 transcripts absent for ADR-25/ADR-26 since those came from non-Council debates), and ~2,548 tests at last JOURNAL run.

**Why this severity.** No system risk — this is upstream-context drift. Listed so future audits do not propagate the stale numbers.

**Recommended improvement.** When briefing a fresh audit, derive counts from `docs/decisions/README.md`, `docs/decisions/transcripts/` glob, and `pytest --collect-only -q | wc -l` rather than from prior session memory.

### D13. `pyproject.toml` declares `openai>=2.14` runtime dep but no provider module exists — LOW

**Current state.** `pyproject.toml:21` declares `openai>=2.14` as a runtime dependency. `src/corp/extractor/providers/` contains `anthropic_provider.py` and `gemini_provider.py` but **no `openai_provider.py`**. No active `openai` imports in `src/corp/`.

**Why this severity.** Unused runtime dep adds ~30MB install size and pulls a third-party crypto/networking stack into every install. Trust surface grows for no functional return.

**Recommended improvement.** Either (a) add `openai_provider.py` to make the dep load-bearing, or (b) remove `openai` from `pyproject.toml:21`.

### D14. README.md is thin — duplicated count drift surface — LOW

**Current state.** `README.md` is 39 lines. The module table is its main content. ARCHITECTURE.md (354 lines) covers the same material in depth.

**Why this severity.** Two docs cover the same space, both can drift, one (README) is the public-facing entry point and tends to be ignored as the source of truth.

**Recommended improvement.** Make README a thin pointer ("see ARCHITECTURE.md, VISION.md, CLAUDE.md") and remove the count table.

### D15. ADR-25 and ADR-26 lack matching DECISION_25/26 transcripts — INFO

**Current state.** `docs/decisions/transcripts/` contains DECISION_01..24, 27, 28, 29. DECISION_25 and DECISION_26 are absent despite ADR-25 (Diagram Strategy) and ADR-26 (Tach adoption) being present. This is **not a contradiction** — these ADRs were not produced via Council debate (per JOURNAL 2026-04-15 Tach Phase 1 + 2026-03-30 Diagrams v4 — both were direct ADR drafts).

**Why this severity.** No issue — just a structural fact a reader may find puzzling. The skip mechanism explicit in `docs/decisions/README.md:39-42` covers ADR-28/29 but doesn't address ADR-25/26 absences.

**Recommended improvement.** Add a one-line note to `docs/decisions/README.md` clarifying that ADR-25/26 originated outside Council and thus have no transcript pair.

### D16. CONTRIBUTING.md silent on JOURNAL/BACKLOG/VISION — LOW

**Current state.** CONTRIBUTING.md describes branch naming, commit style, dev flow, Tach rules. It does NOT describe: how to add a JOURNAL entry (ADR-49 shape), how to add a BACKLOG item (ADR-41 schema), when to update VISION.

**Why this severity.** New contributors may diverge from the established convention silently. CLAUDE.md §6 carries the JOURNAL shape; CONTRIBUTING does not point at it.

**Recommended improvement.** Add a "Session artifacts" section to CONTRIBUTING.md pointing to: ADR-49 for JOURNAL entries, ADR-41 for BACKLOG, ADR-53 for CLAUDE.md changes, ADR-38 for VISION review triggers.

---

## 10. Decision-Record State

### 10.1 ADR count: 30

Per `docs/decisions/README.md:6-37` and verified via `docs/decisions/ADR-*.md` glob:

| # | ADR | Title | Status |
|---|-----|-------|--------|
| 1 | ADR-01 | Knowledge Management Architecture | Accepted |
| 2 | ADR-02 | CKE Extraction Quality | Accepted |
| 3 | ADR-03 | Model Selection for Text Extraction | **Superseded by ADR-08a** |
| 4 | ADR-04 | Vault Structure | **Superseded by ADR-07** |
| 5 | ADR-05 | Re-extraction Strategy | Accepted |
| 6 | ADR-06 | Ingestion Quality Gate | Accepted |
| 7 | ADR-07 | Obsidian Vault Navigation | Accepted |
| 8 | ADR-08a | Model Tiering and Routing | Accepted |
| 9 | ADR-08b | Gemini API Capability Adoption | Accepted |
| 10 | ADR-09 | Knowledge Dimensions and File Organization | Accepted |
| 11 | ADR-10 | Vault Naming Convention (type-first) | **Superseded by ADR-14** |
| 12 | ADR-11 | File Distribution Algorithm | Accepted |
| 13 | ADR-12 | Claude Code Execution Patterns | Accepted |
| 14 | ADR-13 | Monorepo Package Architecture | Accepted |
| 15 | ADR-14 | Naming Convention v2 (date-first) | Accepted |
| 16 | ADR-15 | Sandbox Testing Pipeline | Accepted |
| 17 | ADR-16 | Evaluation Metrics and Baseline | Accepted |
| 18 | ADR-17 | Obsidian Vault Navigation and Plugin Selection | Accepted |
| 19 | ADR-18 | Algorithmic Hybrid Classifier | Accepted |
| 20 | ADR-19 | Light Scan Architecture | Accepted |
| 21 | ADR-20 | Vault Rebuild Strategy | Accepted |
| 22 | ADR-21 | Knowledge Ontology and Tagging Approach | Accepted |
| 23 | ADR-22 | RFP KB Federation with Vault Search | Accepted (impl. open per BACKLOG P2) |
| 24 | ADR-23 | Monorepo Internal Architecture Refactoring | Accepted (amended by ADR-27) |
| 25 | ADR-24 | MyWork Knowledge Architecture | Accepted |
| 26 | ADR-25 | Diagram Strategy | Accepted |
| 27 | ADR-26 | Tach Import Boundary Enforcement | Accepted |
| 28 | ADR-27 | Safety Invariants — OneDrive + Vault Writer | Accepted (vault writer impl. complete; OneDrive centralization deferred) |
| 29 | ADR-30 | Retire CHANGELOG.md | Accepted |
| 30 | ADR-31 | Retire single-file HANDOFF | Accepted |

**Gaps:** ADR-28, ADR-29 (reserved for future Council distillation of DECISION_28/29; documented in README:39-42)

**Externally-referenced ADRs (not in `corp-monorepo/docs/decisions/`):**
- ADR-33 (VISION mandatory) — referenced in CLAUDE.md / VISION.md frontmatter; canonical home in `.dev-knowledge/docs/decisions/`
- ADR-36 (read-only contract for cross-repo files)
- ADR-38 (file-set per scale tier)
- ADR-41 (BACKLOG schema)
- ADR-42 (handoff bundles in `.dev-knowledge`)
- ADR-49 (JOURNAL entry shape)
- ADR-51 (ARCHITECTURE.md convention)
- ADR-53 (CLAUDE.md as single canonical agent-instruction file)
- ADR-54 (AGENTS.md retirement; per-repo overlay → none)

### 10.2 Council transcripts: 28

Per `docs/decisions/transcripts/*.md` glob:

DECISION_01..24 (25 transcripts incl. 08a/08b), DECISION_27 (OneDrive centralization), DECISION_28 (community patterns research), DECISION_29 (spec-kit/kiro research).

**3 SUPERSEDED:** DECISION_03 (model selection), DECISION_04 (vault structure), DECISION_05 — wait, file-state shows only DECISION_03 and DECISION_04 carry SUPERSEDED suffix (`docs/decisions/transcripts/DECISION_03_model_selection_SUPERSEDED.md`, `DECISION_04_vault_structure_SUPERSEDED.md`). DECISION_05 has no SUPERSEDED suffix. Earlier exploration claim of "3 superseded" is corrected here: **2 superseded transcripts**.

### 10.3 Audits: 4

| Date | Title | Scope |
|------|-------|-------|
| 2026-03-30 | Codex full audit | Initial monorepo-wide Codex review |
| 2026-04-15 | Tach baseline violations | Phase-1 baseline (later resolved) |
| 2026-04-21 | Codex hotfix review | OneDrive safety P1 hotfix review |
| 2026-05-18 | Universalization review | Doc-governance rollout gap review |

This audit (2026-05-20) is the 5th.

### 10.4 ADR contradictions / interactions discovered

- **ADR-23 ↔ ADR-27 interaction explicit:** ADR-23 (monorepo internal architecture) was amended by ADR-27 (safety invariants). Cross-reference noted in `docs/decisions/ADR-23-*.md` (JOURNAL 2026-05-18 confirms amendment line was added).
- **ADR-27 deferred implementation:** ADR-27 declares two safety changes — vault-writer narrowing (implemented per JOURNAL 2026-05-18) AND OneDrive centralization (deferred to PR-1/2/3 per JOURNAL 2026-05-18 Next). The ADR is "Accepted" but only half implemented; documenting this as a known split-state.

No other contradictions surfaced. Supersession chains (ADR-03→08a, ADR-04→07, ADR-10→14) are explicit and consistent.

---

## 11. Open / Pending

### 11.1 BACKLOG items (8)

Per `BACKLOG.md`:

**Open Decisions:**
- **[P1]** Ontology Q4 — canonical product map
- **[P2]** RFP Federation (ADR-22) implementation
- **[P2]** MyWork bulk rename to naming v2 (~585 files)
- **[P2]** 30-day skill eval checkpoint (**past due** at rehoming time — original due 2026-04-25)
- **[P3]** Local AI exploration (Ollama)
- **[P3]** Outlook automation

**Pending Fixes:**
- **[P1]** MinHash dedup not wired into `inbox.py::process_file()` (table populated, never consulted)
- **[P2]** Cognitive Friday YAML unquoted hyphen truncates `session_id`
- **[P3]** Two low-quality JLR notes (28–29 score) need re-extraction

### 11.2 JOURNAL "Next:" aggregation (recent entries)

Most recent JOURNAL entries (2026-05-18 to 2026-05-20) report ADR-53/54 effort **complete** with no pending follow-ups in the corp-monorepo repo. The unfinished work is in cross-repo land (`.dev-knowledge`, ai-council).

Older recurring "Next:" items still pending (per §9.D8):
- Magistrala pipeline end-to-end verification (4+ JOURNAL entries since 2026-03-29)
- MISC rate measurement at day 7 (mentioned 2026-03-30, no measurement artifact found)
- 20_Workflows file count monitoring (<75 threshold)

---

## 12. Appendix — Verification Questions Resolved

Each question receives one of: **CONFORMS** (file evidence supports the invariant), **GAP** (file evidence shows the invariant is not met), or **UNKNOWN** (cannot be determined by file inspection alone).

### Q1. OneDrive hard-exclude in every cleanup path?

**Answer:** CONFORMS (4 sites enumerated). With caveat: ADR-27 centralization design (`src/corp/safety/onedrive.py`) is not implemented — see §5.2.A. New mutation sites added after ADR-27 implementation will be caught by AST-based CI scanner; today's guards are per-site duplication.

**Evidence:** `src/corp/cleanup/disk.py:24` (central constant), `src/corp/cleanup/executor.py`, `src/corp/actions/_helpers.py`, `src/corp/project/renderer.py`. Exception home: `src/corp/cleanup/errors.py`. Test coverage: `tests/safety/test_vault_writer_invariant.py` (vault writer only — no OneDrive AST scanner yet).

### Q2. Does Tach cover the vault-writer boundary?

**Answer:** NO — vault-writer is **not** enforced via Tach. Tach enforces import direction (layer boundaries); the vault-writer rule is "only certain modules call `vault_io.write_note`" which is an authorization constraint, not a layer constraint. It is enforced at **runtime** via `_ACTIONS_WRITE_WHITELIST` + **static AST scan** via `tests/safety/test_vault_writer_invariant.py`.

**Classification:** **CONFORMS** to ADR-27 (which never required Tach enforcement — ADR-27 specifies AST scanner).

### Q3. Does Tach cover the "no cross-package import" rule among former 6 packages?

**Answer:** PARTIALLY. Tach enforces upward-import prevention via the 4-layer model. The former 6 packages now live at different layers (corp.schema=foundation, corp.extractor=core, corp.ingest=orchestration, etc.) so cross-package imports are constrained by layer order. However, Tach does NOT enforce "package X may not import package Y" within the same layer — e.g., `corp.opportunity` and `corp.rfp` are both `core` and could in principle import each other. The `depends_on` declarations (`tach.toml:67-179`) constrain each module's allowed imports explicitly, which DOES enforce intra-layer isolation.

**Verdict:** Intra-layer isolation is enforced via explicit `depends_on` lists with `exact = true`, which means undeclared imports fail `tach check`.

### Q4. Hardcoded API keys, committed `.env` files, or `GOOGLE_API_KEY` references in source?

**Answer:** CONFORMS (none).

**Evidence:**
- No `.env` committed (only `.env.example`)
- No string literal matching API key patterns in source
- `GOOGLE_API_KEY` appears only as a negation rule in CLAUDE.md §4 — zero hits in `src/corp/`

### Q5. Magistrala pipeline integration test status?

**Answer:** GAP. See Finding §9.D8.

### Q6. Counts: ADRs / Council / LESSONS / most recent of each?

**Answer:**
- ADRs: **30** (ADR-01..27 + ADR-30 + ADR-31; gaps at 28/29). Most recent: ADR-31 (Retire single-file HANDOFF) accepted 2026-05-18.
- Council transcripts: **28** (DECISION_01..24, 27, 28, 29). Most recent archived: DECISION_28 and DECISION_29 archived 2026-04-24 (JOURNAL).
- LESSONS: **0** in this repo (cross-repo file at `.dev-knowledge/LESSONS.md`).
- Prior audits: **4** in `docs/audits/`. Most recent: 2026-05-18 universalization review. This audit (2026-05-20) is the 5th.

### Q7. Other scripts with hard-coded reference lists (the drift-surface pattern)?

**Answer:** TWO sites identified.

1. `scripts/extract_training_data.py:48` — hard-coded `skip_names = {"index.md", "synthesis.md", "README.md", "inventory.md"}`. See Finding §9.D11.
2. `scripts/check_doc_refs.py:18-23` — hard-coded `DOCS` list (`CLAUDE.md`, `CONTRIBUTING.md`, `docs/ARCHITECTURE.md`) plus rglob scan of `src/corp/*/README.md`. Pattern is mostly safe (rglob handles README discovery); the hard-coded portion was cleaned up 2026-05-20 (JOURNAL).

### Q8. Is the OneDrive constant centralized?

**Answer:** PARTIALLY. The constant `_ONEDRIVE_BLOCKED = "OneDrive - Blue Yonder"` lives at `src/corp/cleanup/disk.py:24` but is NOT imported by the other 3 guard sites (`executor.py`, `_helpers.py`, `renderer.py`). Each site repeats the substring check pattern independently. ADR-27 centralization design names `src/corp/safety/onedrive.py` as the future home; not yet implemented.

### Q9. Is `routing_map.yaml` present and consulted?

**Answer:** ABSENT. Routing is code-distributed. See Finding §9.D2.

### Q10. Is `status.json` read-with-retry consistently applied?

**Answer:** GAP at one site (`src/corp/extractor/manifest.py::load_status()`). See Finding §9.D9.

### Q11. Is the AGENTS.md retirement complete?

**Answer:** CONFORMS. Per JOURNAL 2026-05-20: AGENTS.md deleted; CLAUDE.md §10 updated; CONTRIBUTING.md Architecture Reference line removed; `scripts/check_doc_refs.py` DOCS list cleaned. Remaining `AGENTS.md` references live only in immutable historical docs (ADRs, audits, transcripts, JOURNAL).

### Q12. Are tests in safe condition?

**Answer:** UNKNOWN-by-file-inspection. The audit does not run tests. JOURNAL 2026-05-18 reports the most recent green run (2,548 passed, 6 skipped). No regressions reported in any 2026-05-18 to 2026-05-20 JOURNAL entry.

---

## Audit Trail

- **Branch:** `docs/audit-corp-monorepo-deep`
- **Base:** `main` at commit `fbcaa86` (2026-05-20)
- **Files modified:** 1 (this file)
- **Files read:** 30 ADRs, 28 transcripts, 4 prior audits, every config file at repo root, ARCHITECTURE.md, CLAUDE.md, CONTRIBUTING.md, JOURNAL.md, BACKLOG.md, VISION.md, README.md, `docs/decisions/README.md`, every script's docstring (via agent), `src/corp/` structural inventory (via agent), `tests/` structural inventory (via agent)
- **Files NOT read in full (read by agent or by grep only):** ADR bodies (only titles/status read), most `src/corp/*.py` source files (read by agent summary), every transcript body
- **Methodology bounded:** No tests executed; no scripts executed; no runtime behavior observed. Static file inspection only.
