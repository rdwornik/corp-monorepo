# Changelog

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
