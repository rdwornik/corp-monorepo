# Changelog

### 2026-04-22
- ADR-27 drafted: combined OneDrive safety centralization + vault writer invariant amendment
- Decision 1 sourced from AI Council 2026-04-22 (Option C, 3-of-4 consensus)
- Decision 2 Option B (narrow invariant with zone whitelist; codifies actual working architecture at 8 action write sites)
- Implementation prompts follow (3 PRs for OneDrive, 1 for vault writer)
- `docs/ARCHITECTURE.md` cross-referenced; invariant wording itself unchanged until implementation PRs land

### 2026-04-21 (hotfix)
- OneDrive safety hotfix: P1-1 execute_plan guard, P1-2 moves.yaml schema + traversal guard, P1-3 _resolve_project_path writable kwarg
- Three regression tests added, verified failing on main before fixes (pytest 2495 -> 2507 green; zero regressions)
- Docs: ARCHITECTURE.md + .claude/skills/gotchas/gotchas.md updated; AGENTS.md deferred to ADR-27
- P2 (vault single-writer) remains open — handled in ADR-27
- Amendment: resolve paths before substring check in all 4 OneDrive guard sites (disk.py, _helpers.py, executor.py, renderer.py) — addresses Codex review H-C1/H-C2 and pre-existing same-class bugs
- Split schema vs runtime traversal tests to assert exact exception per layer (Codex review M-C1)
- Amendment test delta: 2507 -> 2515 green (+6 symlink bypass tests, +2 runtime-guard unit tests)
- Codex re-review pending before merge

## [1.0.0] - 2026-03-28

### Changed
- Project meta-files restructured per Playbook: `.ecosystem/` eliminated, content moved to `docs/` and `docs/decisions/transcripts/`; root `decisions/` moved to `docs/decisions/`; `MASTER_HANDOFF.md` renamed to `docs/HANDOFF.md`

### Changed (prior)
- **Consolidated 6 packages into unified `src/corp/` namespace** (ADR-23)
  - `corp-os-meta` → `src/corp/schema/`
  - `corp-knowledge-extractor` → `src/corp/extractor/`
  - `corp-by-os` → `src/corp/ingest/`, `src/corp/retrieve/`, `src/corp/cli/`
  - `corp-project-extractor` → `src/corp/project/`
  - `corp-rfp-agent` → `src/corp/rfp/`
  - `corp-opportunity-manager` → `src/corp/opportunity/`
- Single `pyproject.toml` at repo root replaces 6 per-package `pyproject.toml` files
- Single `pip install -e ".[dev,llm]"` replaces 6 separate installs
- All 5 CLI entry points (`corp`, `cke`, `cpe`, `corp-meta`, `com`) retained

### Removed
- `packages/` directory and all per-package scaffolding
- Per-package `venv/`, `.gitignore`, `pyproject.toml`, `README.md` files

### Tests
- 2,412 tests unified under `tests/` (formerly split across 6 `tests/` directories)
