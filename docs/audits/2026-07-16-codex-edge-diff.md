# Codex edge diff — 2026-07-16

Model: `gpt-5.6-sol` (local Codex `sol` configuration)

Independent derivation scope: Python source under `src/corp/` only. The derivation did not read `ARCHITECTURE.md` or `docs/audits/2026-07-16-architecture-ground-truth.md`. A separate comparison pass read only `src/corp/` and the audit's §1.

Comparison normalization:

- Static: distinct unit-level absolute `from corp.*` / `import corp.*` edges. Relative imports are excluded per the task definition.
- CLI: distinct unit-level subprocess edges to `corp`, `cke`, `cpe`, `com`, `corp-meta`, or a dynamically configured agent CLI. External-tool subprocesses are excluded.
- Data: distinct unit × production-store × direction tuples. Defaults bound to Vault/MyWork count; temporary sandbox/test-pipeline analogues and arbitrary caller-supplied destinations do not.

## Edges Codex found that the audit missed

### Static imports

None.

### Subprocess / CLI

None.

### Data edges

#### ops.db

- `ops.db → ops` READ — `src/corp/ops/database.py:225,463-483`.

#### index.db

- `index.db → index_builder` READ — `src/corp/index_builder.py:322`.
- `index.db → actions` READ — `src/corp/actions/analytics_actions.py:18-20`; `src/corp/actions/knowledge_actions.py:16-28`.
- `actions → index.db` WRITE — `src/corp/actions/index_actions.py:16-18`.
- `index.db → cli` READ — `src/corp/cli/analytics.py:24-30`; `src/corp/cli/index.py:48-55`.
- `cli → index.db` WRITE — `src/corp/cli/index.py:22-36`.
- `ingest → index.db` WRITE — `src/corp/ingest/inbox.py:550-553`.

#### overnight_state.db

- `overnight_state.db → cli` READ — `src/corp/cli/overnight.py:205,260,286`.

#### Vault filesystem

- `vault → actions` READ — `src/corp/actions/brief_actions.py:39-43`; `src/corp/actions/archive_actions.py:63-67`.
- `vault → chat` READ — `src/corp/chat.py:205-209`.
- `vault → cli` READ — `src/corp/cli/system.py:116-134`.
- `cli → vault` WRITE — `src/corp/cli/extract.py:129-131`; `src/corp/cli/overnight.py:248-250`.
- `vault → extraction` READ — `src/corp/extraction/vault_writer.py:86-93`.
- `vault → ingest` READ — `src/corp/ingest/extractions.py:248-252`; `src/corp/ingest/inbox_ops.py:215-230`.
- `vault → integrity` READ — `src/corp/integrity.py:327-332`.
- `vault → intent_router` READ — `src/corp/intent_router.py:355-365`, via production-default `resolve_project`.
- `vault → overnight` READ — `src/corp/overnight/preflight.py:45-48,67-69`.
- `vault → project_resolver` READ — `src/corp/project_resolver.py:105-112`.
- `vault → retrieve` READ — `src/corp/retrieve/engine.py:441,457`.
- `vault → task_manager` READ — `src/corp/task_manager.py:197,274,317`.
- `vault → template_manager` READ — `src/corp/template_manager.py:211-215`.

#### MyWork filesystem

- `MyWork → actions` READ — `src/corp/actions/inbox_actions.py:18-29`.
- `actions → MyWork` WRITE — `src/corp/actions/archive_actions.py:47-59`.
- `MyWork → chat` READ — `src/corp/chat.py:205-209`.
- `MyWork → cli` READ — `src/corp/cli/cleanup.py:32-35`; `src/corp/cli/extract.py:53-63`.
- `MyWork → extraction` READ — production binding at `src/corp/cli/extract.py:80-95`; scan at `src/corp/extraction/scanner.py:44-68,133`.
- `MyWork → extractor` READ — production manifest binding at `src/corp/cli/extract.py:89-95`; consumption at `src/corp/extractor/extract.py:577,585`.
- `MyWork → freshness_scanner` READ — `src/corp/freshness_scanner.py:160-184`.
- `MyWork → ingest` READ — `src/corp/ingest/router.py:111-125,671`.
- `MyWork → integrity` READ — `src/corp/integrity.py:393-394,414-430`.
- `MyWork → intent_router` READ — `src/corp/intent_router.py:301-303,355-358`, via production-default project resolution.
- `MyWork → llm_router` READ — `src/corp/llm_router.py:131-133`, via production-default project listing.
- `MyWork → ops` READ — `src/corp/ops/registry.py:24-26,59`.
- `MyWork → overnight` READ — `src/corp/overnight/monitor.py:66-68`; `src/corp/overnight/preflight.py:55-60`.
- `MyWork → project_resolver` READ — `src/corp/project_resolver.py:55-61,120-122`.
- `MyWork → retrieve` READ — default binding and directory scan at `src/corp/cli/retrieve.py:187-200`.
- `retrieve → MyWork` WRITE — default output binding at `src/corp/cli/retrieve.py:200`; write at `src/corp/retrieve/prep.py:170`.
- `MyWork → template_manager` READ — `src/corp/template_manager.py:157-168,350-358`.
- `MyWork → vault_io` READ — `src/corp/vault_io.py:309-310`.

## Edges the audit has that Codex disputes

### Static imports

- `__main__ → cli` — `src/corp/__main__.py:1` is the relative import `from .cli import cli`, outside the task's absolute-`corp.*` definition.

### Subprocess / CLI

None.

### Data edges

- `sandbox → ops.db` WRITE, `sandbox → index.db` WRITE, and `sandbox → overnight_state.db` WRITE — these are temporary sandbox copies, excluded from the production-store map (`src/corp/sandbox.py:71-86`).
- `test_pipeline → MyWork` WRITE and `test_pipeline → vault` WRITE — these operate on the temporary sandbox pipeline, not the production filesystems (`src/corp/test_pipeline.py:314-316,436-474,524-527`).
- `project → vault` WRITE — the destination is only arbitrary `--copy-to-vault` input and has no production/default vault binding (`src/corp/project/cli.py:284-289`).

## Agreements — count only

- Static: **89**
- Subprocess / CLI: **6**
- Data: **32**
- Total: **127**

Data-set arithmetic after applying the normalization above:

- Codex: ops.db **7** + index.db **11** + overnight_state.db **4** + Vault **24** + MyWork **25** = **71**.
- Audit, normalized in-scope set: ops.db **6** + index.db **5** + overnight_state.db **3** + Vault **11** + MyWork **7** = **32**.
- Intersection: **6 + 5 + 3 + 11 + 7 = 32**.
