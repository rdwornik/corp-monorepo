# Package Architecture Audit — Corp Monorepo
**Date:** 2026-03-28
**Branch:** investigate/package-architecture-audit
**Purpose:** Factual evidence for Council #23 — consolidate vs. maintain 6-package structure
**Constraint:** Read-only investigation. No code changed.

---

## 1. Executive Summary

The monorepo contains 6 packages totalling **151 source files / 29,600 source lines / 2,153 tests**. One package (corp-by-os) accounts for **53% of all source lines** (15,724 of 29,600) and has drifted into a monolith: its `cli.py` alone is 3,573 lines with 71 commands. One confirmed subprocess boundary violation exists in `overnight/cke_client.py`, which directly imports corp-knowledge-extractor without declaring it as a dependency. The remaining 5 packages have clean, well-scoped boundaries — the problem is not the number of packages, it's the internal structure of corp-by-os and the 13 shared filename collisions that make navigation difficult.

---

## 2. Per-Package Profiles

### 2.1 corp-os-meta

| Attribute | Value |
|-----------|-------|
| Layout | **Flat** — `corp_os_meta/` directly under package root (no `src/`) |
| Source files | 10 |
| Source lines | 995 |
| Test files | 11 |
| Test lines | 940 |
| Test/source ratio | **0.94** |
| CLI entry | `corp-meta` → `corp_os_meta.cli:main` |
| Corp-* deps (declared) | None (dependency root) |
| Corp-* deps (actual imports) | None |
| Avg path depth | 3.00 |
| Max path depth | 3 |

**Largest files:** `products.py` (212), `normalize.py` (193), `cli.py` (191), `models.py` (177), `validate.py` (132)

**Role:** Schema/taxonomy root. Pydantic models (`NoteFrontmatter`, `PipelineConfig`), taxonomy normalization, validation. All other packages with structured output depend on this.

**Structural notes:** Flat layout is intentional — corp-os-meta is a pure library. Lowest depth in the repo. No dead code detected.

---

### 2.2 corp-knowledge-extractor (CKE)

| Attribute | Value |
|-----------|-------|
| Layout | `src/corp_knowledge_extractor/` + top-level `scripts/` |
| Source files | 41 |
| Source lines | 6,575 |
| Test files | 58 |
| Test lines | 7,381 |
| Test/source ratio | **1.12** (best in repo) |
| CLI entry | `cke` → `scripts.run:cli` |
| Corp-* deps (declared) | corp-os-meta |
| Corp-* deps (actual imports) | corp-os-meta (5 import sites) |
| Avg path depth | 4.37 |
| Max path depth | 5 (`frames/`, `slides/`) |

**Largest files:** `extract.py` (1,564), `batch_api.py` (639), `post_process.py` (625), `synthesize.py` (553), `merge_session.py` (440)

**Sub-directories:** `frames/` (3 files: sampler, extractor, scene_detect), `slides/` (2 files: renderer, pdf_converter), `providers/` (AI abstraction layer)

**Role:** Pure extraction engine. Input in, structured knowledge out. Does not write to vault, does not route, does not orchestrate.

**Structural notes:** Best-tested package in the repo (7,381 test lines vs 6,575 source lines). `extract.py` at 1,564 lines is large but coherent — it is the Gemini extraction core. `frames/tagger.py` is unreferenced by any other module (see §5).

---

### 2.3 corp-by-os

| Attribute | Value |
|-----------|-------|
| Layout | `src/corp_by_os/` with 8 sub-packages |
| Source files | 64 |
| Source lines | 15,724 |
| Test files | 52 |
| Test lines | 11,410 |
| Test/source ratio | **0.73** |
| CLI entry | `corp` → `corp_by_os.cli:cli` |
| Corp-* deps (declared) | corp-os-meta |
| Corp-* deps (actual imports) | corp-os-meta (15 sites) + corp-knowledge-extractor (10 sites — **VIOLATION**) |
| Avg path depth | 4.77 |
| Max path depth | 6 (`extraction/non_project/`) |

**Largest files:** `cli.py` (3,573 🔴), `ingest/inbox.py` (1,116), `built_in_actions.py` (966), `ingest/router.py` (849), `index_builder.py` (726)

**Sub-directories and sizes:**
| Sub-package | Files | Notes |
|-------------|-------|-------|
| `ingest/` | 10 | Core ingest pipeline — naming, routing, classification |
| `extraction/` | 8 | CKE invocation, overnight batch, non-project extraction |
| `extraction/non_project/` | 3 | Adds depth level 6 |
| `overnight/` | 8 | Batch processing incl. `cke_client.py` (violation) |
| `ops/` | 4 | Ops utilities |
| `cleanup/` | 6 | Vault cleanup rules |
| `doctor/` | 2 | Vault health checks |
| `freshness/` | 2 | Freshness scoring |
| `retrieve/` | 4 | Vault retrieval |

**Role:** Root orchestrator and sole vault writer. Manages all ingest, vault operations, workflows, chat, analytics, freshness, cleanup, doctor, extract.

**Structural notes:** This is the primary navigability problem. `cli.py` with 71 commands is the largest file in the entire repo by a factor of 2.3×. The `doctor/` and `freshness/` sub-packages each have only 2 files — they could be inlined. The `extraction/non_project/` sub-dir creates unnecessary depth level 6. `__main__.py` is unreferenced (see §5).

---

### 2.4 corp-project-extractor (CPE)

| Attribute | Value |
|-----------|-------|
| Layout | `src/corp_project_extractor/` (flat under src/) |
| Source files | 10 |
| Source lines | 1,665 |
| Test files | 3 |
| Test lines | 661 |
| Test/source ratio | **0.40** (lowest in repo 🔴) |
| CLI entry | `cpe` → `corp_project_extractor.cli:cli` |
| Corp-* deps (declared) | (none explicitly declared) |
| Corp-* deps (actual imports) | None (invokes CKE via subprocess — correct) |
| Avg path depth | 4.00 |
| Max path depth | 4 |

**Largest files:** `extractors.py` (496), `cli.py` (417), `renderer.py` (289), `classifier.py` (212), `manifest_generator.py` (188)

**Role:** Project-oriented extraction orchestrator. Classifies files into project types, generates manifests, invokes `cke process-manifest` via subprocess.

**Structural notes:** Correct subprocess usage — `cke_invoker.py` calls CKE via subprocess with no Python imports across the boundary. Test coverage is the weakest in the repo (3 test files, 45 tests). No corp-* imports — fully standalone.

---

### 2.5 corp-rfp-agent

| Attribute | Value |
|-----------|-------|
| Layout | `src/corp_rfp_agent/` + `src/corp_rfp_agent/anonymization/` |
| Source files | 16 |
| Source lines | 3,535 |
| Test files | 10 |
| Test lines | 1,882 |
| Test/source ratio | **0.53** |
| CLI entry | **None** (no `[project.scripts]`) |
| Corp-* deps (declared) | (none) |
| Corp-* deps (actual imports) | None (calls `corp retrieve` via subprocess — correct) |
| Avg path depth | 4.38 |
| Max path depth | 5 (`anonymization/`) |

**Largest files:** `rfp_excel_agent.py` (857), `rfp_answer_word.py` (802), `answer_selector.py` (637), `rfp_feedback.py` (525), `llm_router.py` (452)

**Argparse scripts (not Click, no entry point):** `rfp_excel_agent.py`, `rfp_answer_word.py`, `llm_router.py`, `rfp_feedback.py`, `validate_profiles.py`, `kb_to_markdown.py`, `anonymization/clean_kb.py`

**Role:** AI-powered RFP answering engine. Reads Excel/Word RFPs, retrieves context from vault via `corp retrieve`, generates answers via Gemini/Claude/GPT, writes back to file.

**Structural notes:** Structurally different from all other packages — no Click CLI entry point, all scripts use argparse, no corp-* Python imports. It is a consumer of corp-by-os output (knowledge base) via subprocess only. 7 scripts that could each be a subcommand of a unified `rfp` CLI. 4 unreferenced modules (see §5).

---

### 2.6 corp-opportunity-manager (COM)

| Attribute | Value |
|-----------|-------|
| Layout | `src/corp_opportunity_manager/` (flat under src/) |
| Source files | 10 |
| Source lines | 1,106 |
| Test files | 7 |
| Test lines | 641 |
| Test/source ratio | **0.58** |
| CLI entry | `com` → `corp_opportunity_manager.cli:cli` |
| Corp-* deps (declared) | (none) |
| Corp-* deps (actual imports) | None (fully standalone) |
| Avg path depth | 4.00 |
| Max path depth | 4 |

**Largest files:** `chat.py` (347), `cli.py` (265), `folder_standards.py` (185), `llm_client.py` (181), `excel_manager.py` (152)

**Role:** Opportunity folder management. Creates standardized folder structures, manages opportunity metadata, provides LLM-powered intent parsing.

**Structural notes:** Cleanest package in terms of isolation — zero corp-* dependencies, well-scoped purpose, appropriate size. `cli.py` is not imported directly (it's the `com` entry point — not dead code).

---

## 3. Cross-Package Dependencies

### 3.1 Dependency Graph

```
corp-os-meta (v1.0.0)   ← DEPENDENCY ROOT
  ↑ (5 import sites)
corp-knowledge-extractor (v0.8.0)
  ↑ (10 import sites — BOUNDARY VIOLATION)
corp-by-os (v0.3.0)   ← SOLE VAULT WRITER
  ↑
  ├── cpe (subprocess: cke process-manifest)
  ├── corp-rfp-agent (subprocess: corp retrieve)
  └── (no dependency from COM or CPE on corp-by-os Python API)

corp-project-extractor (v0.1.0) — subprocess-only consumer
corp-rfp-agent (v0.3.0) — subprocess-only consumer
corp-opportunity-manager (v0.2.0) — fully standalone
```

### 3.2 Declared vs Actual Dependencies

| Package | Declared corp-* deps | Actual corp-* imports | Delta |
|---------|---------------------|----------------------|-------|
| corp-os-meta | none | none | ✅ |
| corp-knowledge-extractor | corp-os-meta | corp-os-meta | ✅ |
| corp-by-os | corp-os-meta | corp-os-meta + CKE | 🔴 **CKE undeclared** |
| corp-project-extractor | none | none (subprocess only) | ✅ |
| corp-rfp-agent | none | none (subprocess only) | ✅ |
| corp-opportunity-manager | none | none | ✅ |

### 3.3 The Boundary Violation — `overnight/cke_client.py`

**File:** `packages/corp-by-os/src/corp_by_os/overnight/cke_client.py` (180 lines)

**Violation:** Direct Python imports of CKE modules:
```python
from corp_knowledge_extractor.batch_api import ...
from corp_knowledge_extractor.manifest import ...
from corp_knowledge_extractor.inventory import ...
from corp_knowledge_extractor.tier_router import ...
from corp_knowledge_extractor.batch import ...
from corp_knowledge_extractor.scan import ...
```

**Acknowledged in docstring:** *"Thin wrapper around CKE — direct import, no subprocess."*

**Mitigation:** All imports are lazy (inside function bodies, not module-level). Has `is_available()` guard — gracefully degrades if CKE not installed.

**Risk:** `pip install corp-by-os` alone is insufficient for overnight functionality. CKE is not in corp-by-os `[project.dependencies]`, so this coupling is invisible to package management.

**Options:** (a) Declare CKE as optional dep in corp-by-os `pyproject.toml` — formalizes the violation but makes it explicit. (b) Refactor to subprocess call pattern — restores boundary, minor performance cost. (c) Accept as deliberate design for performance-critical overnight path.

### 3.4 Subprocess Boundary Usage (correct patterns)

| Package | Subprocess target | File |
|---------|-------------------|------|
| corp-project-extractor | `cke process-manifest` | `cke_invoker.py` |
| corp-rfp-agent | `corp retrieve --format json` | `vault_adapter.py` |
| corp-by-os | `cke process-manifest` (in cli.py) | `cli.py` |

### 3.5 Integration Tests

7 integration tests at repo root cover cross-package contracts:

| Test file | Coverage |
|-----------|----------|
| `test_cke_output_format.py` | CKE output schema |
| `test_cross_package.py` | Multi-package flows |
| `test_inbox_classify_route.py` | Ingest classification |
| `test_property_based.py` | Property-based contract tests |
| `test_retrieve_contract.py` | Retrieve CLI contract |
| `test_trust_level_contract.py` | Trust level propagation |
| `test_vault_ingest_contract.py` | Vault write contracts |

---

## 4. Duplication Report

### 4.1 Shared Filenames (13 collisions)

These filenames exist in multiple packages, creating navigation ambiguity:

| Filename | Packages that have it |
|----------|-----------------------|
| `cli.py` | corp-os-meta, corp-by-os, corp-project-extractor, corp-rfp-agent (argparse), corp-opportunity-manager |
| `models.py` | corp-by-os, corp-project-extractor, corp-opportunity-manager |
| `config.py` | corp-by-os, corp-project-extractor, corp-opportunity-manager |
| `utils.py` | corp-os-meta, corp-knowledge-extractor, corp-by-os |
| `classifier.py` | corp-by-os (ingest), corp-project-extractor |
| `manifest.py` | corp-knowledge-extractor, corp-project-extractor |
| `router.py` | corp-by-os (ingest), corp-by-os (intent) |
| `renderer.py` | corp-knowledge-extractor (slides), corp-project-extractor |
| `_paths.py` | corp-knowledge-extractor, corp-rfp-agent |
| `chat.py` | corp-by-os, corp-opportunity-manager |
| `llm_router.py` | corp-by-os, corp-rfp-agent |
| `scanner.py` | corp-by-os (ingest), corp-knowledge-extractor |
| `dedup.py` | corp-by-os, corp-knowledge-extractor |

**Navigation impact:** A search for `utils.py` returns 3 results; `cli.py` returns 5 results; `models.py` returns 3. These are all generic names — the packages could benefit from prefixed filenames or namespace-aware search tooling.

### 4.2 Confirmed Function Duplication

**`parse_llm_json(text: str) -> dict`**

| Location | Lines | Strategy |
|----------|-------|----------|
| `corp-os-meta/corp_os_meta/utils.py` | 67 | Canonical — strip fences → direct parse → trailing comma → regex → json-repair |
| `corp-knowledge-extractor/src/corp_knowledge_extractor/utils.py` | 97 | Copy + `log.error()` before raise + `normalize_string_list()` added |

CKE's version has diverged (adds error logging before raise, adds `normalize_string_list`). CKE already imports `from corp_os_meta import parse_llm_json` in some files — the local copy is redundant but diverged. Should be consolidated: move `normalize_string_list` to corp-os-meta utils, then CKE can drop its local copy.

### 4.3 Dataclass Name Collisions (10 class names appear in 2+ packages)

These names collide across packages but are safely namespaced at runtime:

| Class name | Count | Packages |
|------------|-------|---------|
| `Classification` | 3 | corp-by-os (ingest), corp-project-extractor, corp-rfp-agent (implicit) |
| `ExtractionResult` | 2 | corp-knowledge-extractor, corp-project-extractor |
| `Manifest` | 2 | corp-knowledge-extractor, corp-project-extractor |
| `AppConfig` | 2 | corp-by-os (config), corp-opportunity-manager |
| `ProjectInfo` | 2 | corp-by-os (models), corp-os-meta (pipeline) |
| `StepResult` | 2 | corp-by-os (workflow), corp-knowledge-extractor (batch) |
| `FileInfo` | 2 | corp-knowledge-extractor, corp-by-os |
| `ScanResult` | 2 | corp-by-os, corp-knowledge-extractor |
| `IngestResult` | 2 | corp-by-os, corp-knowledge-extractor |
| `Stats` | 2 | corp-by-os, corp-knowledge-extractor |

**Runtime impact:** None — namespacing prevents conflicts. **Developer impact:** Moderate — IDE "go to definition" ambiguity; potential confusion when reading code that uses these names.

### 4.4 Shared Config Patterns

All packages use YAML config under `config/`. Common config files:

| Pattern | Packages |
|---------|---------|
| `config/settings.yaml` or `config.yaml` | CKE, corp-by-os, corp-project-extractor |
| `config/prompts/` | CKE, corp-rfp-agent |
| `config/` product/naming definitions | corp-rfp-agent, corp-by-os |

No config is shared across package boundaries (each reads its own). This is correct — no consolidation needed here.

---

## 5. Dead Code

### 5.1 Confirmed Unreferenced Modules

| File | Package | Evidence | Verdict |
|------|---------|----------|---------|
| `src/corp_rfp_agent/anonymization/clean_kb.py` | corp-rfp-agent | Not imported anywhere; argparse main guard | One-time KB cleaning script, retained for re-use |
| `src/corp_rfp_agent/anonymization/scan_kb.py` | corp-rfp-agent | Not imported anywhere; argparse main guard | One-time KB scanning script, retained for re-use |
| `src/corp_rfp_agent/kb_to_markdown.py` | corp-rfp-agent | Not imported anywhere; argparse main guard | One-time migration script (KB JSON → markdown) |
| `src/corp_rfp_agent/_paths.py` | corp-rfp-agent | Not imported by any module in package | Path definitions — may be unused after refactor |
| `src/corp_knowledge_extractor/frames/tagger.py` | CKE | Not imported by any module in package | Frame tagging — may be invoked dynamically |

### 5.2 False Positives (Entry Points, Not Dead)

| File | Package | Why it appears unreferenced | Actual status |
|------|---------|----------------------------|---------------|
| `src/corp_project_extractor/cli.py` | CPE | Entry point — invoked via `cpe` command | **Active** |
| `src/corp_opportunity_manager/cli.py` | COM | Entry point — invoked via `com` command | **Active** |
| `src/corp_by_os/__main__.py` | corp-by-os | `python -m corp_by_os` pattern | **Active** (or intentional stub) |

### 5.3 Known Structural Debt (from CLAUDE.md / STRUCTURAL_DEBT.md)

- 246 bare `print()` calls across 9 src files in corp-rfp-agent (should be `logging.*` or Rich)
- `validate_profiles.py --merge` references deleted `merge_profiles.py` — dead CLI flag
- `rfp_answer_word.py` has `sys.path.insert` hack — holdover from pre-packaging era
- `data/kb/verified/` retained as backup after vault integration

---

## 6. Navigability Analysis

### 6.1 Path Depth Per Package

| Package | Avg Depth | Max Depth | Files |
|---------|-----------|-----------|-------|
| corp-os-meta | **3.00** | 3 | 10 |
| corp-project-extractor | 4.00 | 4 | 10 |
| corp-opportunity-manager | 4.00 | 4 | 10 |
| corp-knowledge-extractor | 4.37 | 5 | 41 |
| corp-rfp-agent | 4.38 | 5 | 16 |
| corp-by-os | **4.77** | **6** | 64 |

Depth measured as directory levels from repo root (`packages/corp-by-os/src/corp_by_os/extraction/non_project/xyz.py` = depth 6).

### 6.2 Depth Distribution

- Depth 3: 10 files (all corp-os-meta — flat layout advantage)
- Depth 4: ~50 files (standard `src/pkg_name/module.py`)
- Depth 5: ~70 files (sub-packages: ingest/, anonymization/, frames/, slides/, providers/)
- Depth 6: ~6 files (corp-by-os only: `extraction/non_project/`)

### 6.3 Hypothetical Flat Structure

If all 151 source files were merged into a single package with no sub-directories:
- Depth would be uniform 2 (`flat_pkg/module.py`)
- But 151 files in one flat namespace would create severe naming collisions (the 13 duplicate filenames would all conflict)
- Conclusion: depth is mostly justified by the sub-package divisions; the issue is the filename collision problem, not the depth itself

### 6.4 Navigability Pain Points

1. **`cli.py` proliferation** — 5 packages have a `cli.py`. Searching `cli.py` is ambiguous.
2. **corp-by-os depth 6** — `extraction/non_project/` creates unnecessary nesting; those 3 files could live at depth 5 without loss of clarity.
3. **corp-by-os sub-packages of 2 files** — `doctor/` and `freshness/` each have exactly 2 files. These don't warrant sub-package status.
4. **`overnight/` name** — the boundary violation lives here; the name doesn't signal CKE coupling.

---

## 7. CLI Analysis

### 7.1 Entry Points Summary

| Package | Command | Framework | Location | Lines |
|---------|---------|-----------|----------|-------|
| corp-os-meta | `corp-meta` | Click | `corp_os_meta/cli.py` | 191 |
| corp-knowledge-extractor | `cke` | Click | `scripts/run.py` | ~200 |
| corp-by-os | `corp` | Click | `src/corp_by_os/cli.py` | **3,573** 🔴 |
| corp-project-extractor | `cpe` | Click | `src/corp_project_extractor/cli.py` | 417 |
| corp-rfp-agent | **(none)** | — | — | — |
| corp-opportunity-manager | `com` | Click | `src/corp_opportunity_manager/cli.py` | 265 |

### 7.2 corp-by-os CLI Monolith

`cli.py` has **71 `@command` decorators** in a single 3,573-line file. Command groups:

| Group | Commands (approx) | Domain |
|-------|-------------------|--------|
| `project` | ~8 | Project management |
| `vault` | ~6 | Vault operations |
| `ingest` | ~8 | File ingestion |
| `index` | ~5 | Index management |
| `query` / `retrieve` | ~5 | Retrieval |
| `task` | ~5 | Task management |
| `workflow` | ~4 | Workflow execution |
| `analytics` | ~4 | Usage analytics |
| `template` | ~3 | Template management |
| `extract` / `overnight` | ~6 | Extraction orchestration |
| `cleanup` / `audit` | ~4 | Maintenance |
| `chat` / `rfp` / `freshness` | ~4 | Advanced features |
| `doctor` | ~4 | Health checks |

**Comparison:** corp-project-extractor's `cli.py` (417 lines, Clean) has ~12 commands in the same framework. corp-by-os is 8.6× longer. The commands exist across independent domains that share only vault access.

### 7.3 corp-rfp-agent — Missing CLI Entry Point

corp-rfp-agent is the **only package with no `[project.scripts]` entry point**. Seven argparse-based scripts run as `python src/rfp_excel_agent.py ...`. This means:
- Scripts are not accessible after `pip install` without knowing the source path
- No unified namespace for `rfp` operations
- Inconsistent with all other packages' Click/entry-point pattern

---

## 8. Line Count Summary

| Package | Src Files | Src Lines | Test Files | Test Lines | Test/Src | Tests (#) |
|---------|-----------|-----------|------------|------------|----------|-----------|
| corp-os-meta | 10 | 995 | 11 | 940 | 0.94 | 118 |
| corp-knowledge-extractor | 41 | 6,575 | 58 | 7,381 | **1.12** | 838 |
| corp-by-os | 64 | 15,724 | 52 | 11,410 | 0.73 | 926 |
| corp-project-extractor | 10 | 1,665 | 3 | 661 | **0.40** | 45 |
| corp-rfp-agent | 16 | 3,535 | 10 | 1,882 | 0.53 | 155 |
| corp-opportunity-manager | 10 | 1,106 | 7 | 641 | 0.58 | 62 |
| **TOTAL** | **151** | **29,600** | **141** | **22,915** | **0.77** | **2,153** |

**corp-by-os accounts for 53% of all source lines** despite being 1 of 6 packages.

---

## 9. Observations

### 9.1 What Is Justified Complexity

- **6 separate packages** — each has a distinct role with clean conceptual boundary (schema root, extractor, orchestrator, project classifier, RFP engine, opportunity manager). The boundary discipline is sound in 5 of 6 packages.
- **CKE's `extract.py` at 1,564 lines** — the Gemini extraction API is genuinely complex (Tier 1/2/3 routing, multimodal, retry logic, fact enrichment). Not a monolith candidate.
- **corp-by-os's `ingest/` sub-package (10 files)** — naming config, router, classifier, dedup, renamer, scanner are all legitimately separate concerns within the ingest domain.
- **`overnight/` grouping** — makes sense as a conceptual unit, even if the CKE coupling is the issue.

### 9.2 What Is Accidental Complexity

1. **`cli.py` monolith in corp-by-os (3,573 lines, 71 commands)** — The biggest navigability problem in the repo. Corp-by-os has grown to own: ingest, vault, index, query, workflow, task, analytics, template, extract, overnight, cleanup, audit, freshness, chat, rfp, doctor. These are at minimum 5 separable domains. A developer trying to find "how does freshness scoring work" must search through a 3,573-line file.

2. **`doctor/` and `freshness/` sub-packages with 2 files each** — Creating a sub-package for 2 files adds import path depth without adding conceptual clarity. `from corp_by_os.freshness.scorer import score_note` vs `from corp_by_os.freshness_scorer import score_note` — the latter is cleaner.

3. **Undeclared CKE dependency in corp-by-os** — The boundary violation itself is debatable (performance argument is real), but the undeclared dependency is a pure bug: `pip install corp-by-os` will silently break overnight without CKE.

4. **corp-rfp-agent's argparse scripts** — 7 standalone scripts with no unified entry point. Any developer who pip-installs the package cannot find the commands without reading the source tree.

5. **`parse_llm_json` duplication** — Two copies of the same 4-strategy parser in corp-os-meta and CKE. CKE already imports corp-os-meta for schemas; it could import the parser too.

6. **`extraction/non_project/` depth 6** — 3 files sit at the deepest nesting level in the repo. The sub-directory name does not add clarity (vs. just naming the files `extract_non_project_*.py` at depth 5).

### 9.3 Overall Assessment

The 6-package split itself is not the problem Rob experiences navigating. The problems are:
1. corp-by-os has become the "everything else" package — it needs internal decomposition, not package-level splitting
2. Filename collisions make IDE search unreliable (`cli.py` ×5, `utils.py` ×3, `models.py` ×3)
3. corp-rfp-agent is structurally inconsistent with the rest of the ecosystem (no entry point, argparse, no corp-* imports)

Consolidating packages would reduce the boundary violations from 1 to 0 (by eliminating the boundary), but would not address the cli.py monolith or filename collisions — those would get worse.

---

## 10. Questions for Council #23

### Q1: Formalize or eliminate the CKE boundary violation?

`overnight/cke_client.py` directly imports CKE as a deliberate performance choice (avoiding subprocess overhead for batch processing). Two options:
- **Option A (Formalize):** Add CKE as optional dependency in corp-by-os `pyproject.toml`: `corp-knowledge-extractor = {optional = true}`. The import already gracefully degrades — this just makes the dep explicit.
- **Option B (Eliminate):** Refactor to subprocess call pattern. Aligns with architecture rules but adds latency for batch operations.

*Which approach does Council prefer?*

### Q2: Split corp-by-os into domain packages?

53% of source lines in one package, with a 3,573-line CLI and 8 sub-packages suggests corp-by-os has become a catch-all. Natural split candidates:
- **corp-vault** (vault reads/writes, index, models) — the core
- **corp-ingest** (naming, routing, classification, renaming) — moves as a unit
- **corp-by-os** (orchestrator, workflows, chat, overnight) — slimmed down

*Is this worth the refactor cost? What's the pain threshold?*

### Q3: Give corp-rfp-agent a proper CLI entry point?

All other packages have Click entry points accessible after `pip install`. corp-rfp-agent has 7 argparse scripts invokable only via `python src/...`. A unified `rfp` CLI (`rfp answer`, `rfp feedback`, `rfp validate`) would align it with the rest of the ecosystem.

*Is this a cosmetic concern, or does it block adoption/automation?*

### Q4: Consolidate `parse_llm_json` to corp-os-meta?

CKE already imports corp-os-meta. Removing the duplicate `parse_llm_json` from CKE reduces the two-copy drift risk. The `normalize_string_list` helper currently unique to CKE would move to corp-os-meta utils.

*Approve the consolidation? Any objections to making corp-os-meta's utils.py slightly larger?*

### Q5: Address the cli.py monolith before or after package restructure?

The 3,573-line `cli.py` is the most immediate navigability pain point. It could be split into Click sub-group modules (e.g., `cli/ingest_commands.py`, `cli/vault_commands.py`) without any package restructure — a pure internal refactor of corp-by-os that doesn't change the external API. This could happen independently of any Council #23 package decision.

*Should the cli.py split be a pre-condition for Council #23, or a separate workstream?*

---

*Audit generated by Claude Code (claude-sonnet-4-6) on 2026-03-28. All claims traceable to actual file reads and grep outputs in the investigation session.*
