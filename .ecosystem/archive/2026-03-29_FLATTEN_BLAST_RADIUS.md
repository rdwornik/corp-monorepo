# Package Structure Flattening — Blast Radius Analysis

**Date:** 2026-03-29
**Branch:** investigate/flatten-package-structure
**Mode:** Read-only investigation — no files modified

---

## 1. Current State

### Navigation depth (repo root → first real source file)

| Package | Python name | Current path | Levels deep |
|---------|-------------|--------------|-------------|
| corp-by-os | `corp_by_os` | `packages/corp-by-os/src/corp_by_os/ingest/inbox.py` | 7 |
| corp-knowledge-extractor | `corp_knowledge_extractor` | `packages/corp-knowledge-extractor/src/corp_knowledge_extractor/…` | 7 |
| corp-opportunity-manager | `corp_opportunity_manager` | `packages/corp-opportunity-manager/src/corp_opportunity_manager/…` | 7 |
| corp-project-extractor | `corp_project_extractor` | `packages/corp-project-extractor/src/corp_project_extractor/…` | 7 |
| corp-rfp-agent | `corp_rfp_agent` | `packages/corp-rfp-agent/src/corp_rfp_agent/…` | 7 |
| **corp-os-meta** | `corp_os_meta` | `packages/corp-os-meta/corp_os_meta/…` | **6** ← ALREADY FLAT |

**Key finding:** corp-os-meta is the outlier — it already uses a flat `packages/corp-os-meta/corp_os_meta/` structure with no `src/` level. All other 5 packages use the `src/` layout.

### Top-level dirs per package

| Package | Top-level dirs |
|---------|---------------|
| corp-by-os | `src/`, `tests/`, `config/`, `scripts/`, `tasks/`, `docs/` |
| corp-knowledge-extractor | `src/`, `tests/`, `config/`, `scripts/`, `tasks/`, `templates/`, `docs/` |
| corp-os-meta | `corp_os_meta/`, `tests/`, `tasks/`, `docs/` |
| corp-opportunity-manager | `src/`, `tests/`, `config/`, `tasks/`, `docs/` |
| corp-project-extractor | `src/`, `tests/`, `config/`, `tasks/`, `schemas/`, `docs/` |
| corp-rfp-agent | `src/`, `tests/`, `config/`, `scripts/`, `tasks/`, `prompts/`, `data/`, `docs/` |

---

## 2. What Would Break — Inventory

### Python import coupling (cross-package)

| Importer | Imported | Files | Type |
|----------|----------|-------|------|
| corp-by-os | `corp_os_meta` | ~5 files | Direct Python import |
| corp-knowledge-extractor | `corp_os_meta` | ~7 files | Direct Python import |
| corp-by-os → CKE/CPE/COM/RFA | (all) | subprocess | CLI calls, NOT imports |

**Key finding:** Python import coupling is limited to `corp_os_meta` (37 total import lines across corp-by-os + CKE combined). All other cross-package calls go through subprocess/CLI — they do not care about src/ layout.

### Hard-coded `packages/` path references

| File | Line(s) | What it does | Impact if `packages/` renamed |
|------|---------|-------------|-------------------------------|
| `packages/corp-by-os/config/agents.yaml` | 8, 20, 30, 39, 65 | 5 subprocess agent `path:` entries | BREAKS agent orchestration |
| `packages/corp-by-os/scripts/enrich_training_data.py` | 27, 74 | Fixture path + sys.path injection for src/ | BREAKS training data script |

**Only `agents.yaml` and `enrich_training_data.py` contain hard-coded `packages/` references in active code.** Archive docs in `.ecosystem/archive/` reference `packages/` but are historical — not code.

### pyproject.toml packaging config

| Package | `where =` | Change needed? |
|---------|-----------|----------------|
| corp-by-os | `["src"]` | Yes (Option A) |
| corp-knowledge-extractor | `["src", "."]` | Yes (Option A) — note: already includes "." |
| corp-opportunity-manager | `["src"]` | Yes (Option A) |
| corp-project-extractor | `["src"]` | Yes (Option A) |
| corp-rfp-agent | `["src"]` + `pythonpath = ["src"]` in pytest | Yes (Option A) — also update pytest config |
| corp-os-meta | No `where =` (auto-discovery) | No change needed |

### .py file counts (git mv scope for src/ removal)

| Package | .py files under src/ |
|---------|---------------------|
| corp-by-os | 78 |
| corp-knowledge-extractor | 40 |
| corp-by-os (tests) | ~60 |
| corp-rfp-agent | 12 |
| corp-opportunity-manager | 10 |
| corp-project-extractor | 10 |
| **Total source files to move** | **~150** |

Note: Tests and configs do not move — only files under `src/`.

---

## 3. Options Evaluated

### Option A — Remove `src/` only

```
Before: packages/corp-by-os/src/corp_by_os/ingest/inbox.py   (7 levels)
After:  packages/corp-by-os/corp_by_os/ingest/inbox.py        (6 levels)
```

| Dimension | Count | Detail |
|-----------|-------|--------|
| Files to `git mv` | ~150 | All `.py` files under each package's `src/` |
| pyproject.toml changes | 5 | `where = ["src"]` → `where = ["."]` (5 packages; corp-os-meta unchanged) |
| pytest config changes | 1 | corp-rfp-agent: remove `pythonpath = ["src"]` |
| Python import changes | **0** | Import paths (`from corp_by_os.ingest…`) are unchanged — they reference the Python package name, not the filesystem path |
| `packages/` ref changes | **0** | `packages/` folder stays; only `src/` disappears |
| agents.yaml changes | 0 | Unaffected |
| enrich_training_data.py changes | 1 | Remove the `sys.path.insert(…/src)` line (line 74); fixture path (line 27) unaffected |
| CLAUDE.md / docs | 1 | One path example in root CLAUDE.md references `src/corp_by_os/` |
| Editable reinstall required | Yes | `pip install -e .` in all 5 packages after change |
| **Risk** | **Low** | Python imports don't change; only packaging + filesystem layout |
| **Nav gain** | 7 → 6 | -1 level |

**Verdict:** Minimal blast radius. Only filesystem + packaging plumbing changes. No Python code touches. But only saves 1 level of depth — from 7 to 6.

---

### Option B — Move packages to repo root (remove `packages/` wrapper)

```
Before: packages/corp-by-os/src/corp_by_os/ingest/inbox.py   (7 levels)
After:  corp-by-os/src/corp_by_os/ingest/inbox.py             (6 levels)
```

| Dimension | Count | Detail |
|-----------|-------|--------|
| Files to `git mv` | ~341 | ALL .py files across 6 packages |
| pyproject.toml changes | 0 | Internal paths unaffected |
| Python import changes | **0** | Import paths unchanged |
| agents.yaml changes | **5** | Every `path: "packages/X"` → `path: "X"` |
| enrich_training_data.py | **2** | Both hard-coded `packages/` paths |
| CLAUDE.md changes | **3+** | Root CLAUDE.md + package CLAUDE.md files |
| Gotchas / .ecosystem docs | Many | Historical archive docs, handoff docs |
| run-all-tests.ps1 | Check needed | May reference `packages/` |
| Editable reinstall | Yes | All 6 packages |
| **Risk** | **Medium** | Many config/doc updates; easy to miss one reference |
| **Nav gain** | 7 → 6 | -1 level (same gain as Option A!) |

**Verdict:** More churn than Option A for the same 1-level gain. Not worth it unless combined with Option A.

---

### Option A + B combined — Remove both `src/` and `packages/`

```
Before: packages/corp-by-os/src/corp_by_os/ingest/inbox.py   (7 levels)
After:  corp-by-os/corp_by_os/ingest/inbox.py                 (5 levels)
```

| Dimension | Count |
|-----------|-------|
| Files to `git mv` | ~150 (src/) + rename 6 dirs |
| Python import changes | 0 |
| Hard config updates | ~8 (agents.yaml ×5, enrich×2, rfp pytest×1) |
| Doc updates | Multiple (CLAUDE.md, archive) |
| **Risk** | Medium |
| **Nav gain** | 7 → 5 | -2 levels |

Saves 2 levels. Still has the redundancy problem: navigating `corp-by-os/corp_by_os/` still looks silly (two nearly identical names).

---

### Option C — Single flat `src/` at repo root

```
Before: packages/corp-by-os/src/corp_by_os/ingest/inbox.py   (7 levels)
After:  src/corp_by_os/ingest/inbox.py                        (4 levels)
```

| Dimension | Count | Detail |
|-----------|-------|--------|
| Files to `git mv` | ~150 | All src/ content merged into one repo-level `src/` |
| pyproject.toml | Major rework | 6 separate pyproject.toml → single top-level? Or keep per-package pyproject.toml with `packages = [{include = "corp_by_os", from = "../../src"}]`? |
| Tests | Major restructure | All 6 `tests/` dirs merge or per-package tests can't find fixtures easily |
| Python imports | 0 | Same imports |
| agents.yaml | 5 | Path references change |
| Per-package configs | Would need restructure | `packages/X/config/` has no obvious new home |
| Independent releases | Breaks | Can no longer `pip install packages/corp-by-os/` independently |
| CI / test isolation | Breaks | One package's test deps now bleed into another |
| **Risk** | **High** | Breaks per-package independence, a monorepo architectural invariant |
| **Nav gain** | 7 → 4 | -3 levels |

**Verdict:** Maximum depth gain but violates the architectural invariant that each package is independently installable and testable. Would require a fundamental pyproject.toml rearchitecture. Not worth it.

---

### Option D — Rename `packages/` → `pkg/` or `lib/`

```
Before: packages/corp-by-os/src/corp_by_os/ingest/inbox.py   (7 levels)
After:  pkg/corp-by-os/src/corp_by_os/ingest/inbox.py         (7 levels)
```

**Nav gain:** 0 levels (just shorter folder name). Pure churn. Reject.

---

## 4. The Real Problem — Redundant double-naming

The deepest annoyance isn't actually the depth — it's the visual redundancy:

```
packages/corp-by-os/src/corp_by_os/
         ^^^^^^^^^^       ^^^^^^^^^^
         (dash)           (underscore, same thing)
```

Navigating to code means passing through two "corp-by-os" segments. The Python packaging convention requires `corp_by_os/` as the importable package name inside `src/` — this can't change without breaking imports. What can change is the outer structure.

---

## 5. Recommendation

**Best option: A only (remove `src/`)**

- Saves 1 level (7 → 6)
- Zero Python code changes
- ~5 config changes total
- Low risk
- ~1 hour of work

**If 2 levels is worth the extra effort: Option A + B combined**

- Saves 2 levels (7 → 5)
- Still zero Python import changes
- ~10 config changes + CLAUDE.md updates
- Medium risk
- ~2-3 hours including doc updates

**Do not pursue Option C** — it would require restructuring per-package pyproject.toml files and breaks independent installability, which is an architectural invariant (#14 in ADR).

### The honest assessment

Navigability at 6 or 5 levels is marginally better than 7. The real win would come from IDE "jump to definition" being instant — the filesystem depth matters less in VS Code than in a bare file explorer. If the primary pain point is _file explorer navigation_, Option A is the right-sized change. If the pain point is _cognitive load of typing long import paths_, the imports don't change under any option.

---

## Appendix: Full file list for Option A (what would move)

```
git mv packages/corp-by-os/src/corp_by_os           packages/corp-by-os/corp_by_os
git mv packages/corp-knowledge-extractor/src/corp_knowledge_extractor  packages/corp-knowledge-extractor/corp_knowledge_extractor
git mv packages/corp-opportunity-manager/src/corp_opportunity_manager  packages/corp-opportunity-manager/corp_opportunity_manager
git mv packages/corp-project-extractor/src/corp_project_extractor      packages/corp-project-extractor/corp_project_extractor
git mv packages/corp-rfp-agent/src/corp_rfp_agent   packages/corp-rfp-agent/corp_rfp_agent
# corp-os-meta: already flat, no change needed
```

Config changes needed for Option A:
1. `packages/corp-by-os/pyproject.toml` — `where = ["src"]` → `where = ["."]`
2. `packages/corp-knowledge-extractor/pyproject.toml` — `where = ["src", "."]` → `where = ["."]`
3. `packages/corp-opportunity-manager/pyproject.toml` — `where = ["src"]` → `where = ["."]`
4. `packages/corp-project-extractor/pyproject.toml` — `where = ["src"]` → `where = ["."]`
5. `packages/corp-rfp-agent/pyproject.toml` — `where = ["src"]` → `where = ["."]`, remove `pythonpath = ["src"]`
6. `packages/corp-by-os/scripts/enrich_training_data.py` line 74 — remove `sys.path.insert(…/src)` line
