# Deep Audit E — Deal Loop (Wave 2)

**Date:** 2026-07-05 · **Branch:** `docs/deep-dealloop` · **Baseline HEAD:** `2753601` (Phase-1 functional audit merged)
**Scope:** D1 intake and D5 close-out, post-Phase-1. Operator ruling in scope: `com` is **unfinished, not unwanted — verdict FIX**.
**Method:** read-only. No `com`/`cpe`/action execution; `Project_Codes.xlsm` opened `read_only=True` (openpyxl); no OneDrive path traversed; MyWork/vault inspected by directory listing only. Every claim carries file:line or command-level evidence.

**One-line verdict:** the deal loop is a nearly-complete local machine pointed at a test address — 5 config lines revive `com new`→folder→workbook write-back, the CPE bridge is intact (2 one-line fixes), the archive mechanism works but has no trigger, and the only genuinely missing pieces are the workbook⇄folder addressing contract and both cloud legs (SF = manual paste today, SP = guard-forbidden pending a Graph client).

---

## Step 1 — COM trace and the "finished" definition

### 1.1 Function-level trace (`src/corp/opportunity/`, 1,451 lines, 9 modules)

| Command | What it actually does | Evidence |
|---|---|---|
| `com new CLIENT -p PRODUCT` | Validates stage against config enum → `create_opportunity()`: mkdir `{client}_{product}` under `projects_root` (verbatim case), create `_knowledge/`, copy deck template renamed `{client}_{date}_{topic}.pptx`, write `_knowledge/project-info.yaml` (client/product/contact/stage/created/folder_name) + `notes.md` stub → `_try_update_excel()`: substring-match account in col C, write folder path to col M | `cli.py:41-99`, `folder_manager.py:22-128`, `excel_manager.py:97-123` |
| `com list` | If `PROJECT_CODES_EXCEL` set+exists: read all workbook rows, display Account/Opportunity/Stage/Folder. Else fallback: list `projects_root` subdirs with has-`_knowledge` flag | `cli.py:102-129`, `excel_manager.py:126-152` |
| `com show CLIENT` | Prefix-match folder in `projects_root`, dump `_knowledge/project-info.yaml` keys verbatim | `cli.py:132-157` |
| `com prep-deck CLIENT -t TOPIC` | Prefix-match folder, `shutil.copy2` the ONE configured `discovery_deck` template renamed into it. No content generation | `cli.py:160-201` |
| `com chat` | Gemini (`gemini-3-flash-preview`) intent parse → 8 intents routed to the same functions + `create_subfolder` (RFP/Meetings/Implementation trees) + `check_structure` (naming/metadata audit) | `chat.py:32-310`, `llm_client.py:13-60`, `folder_standards.py:37-133` |

Unit capability is real: 891 test lines across 7 files (`tests/opportunity/`), including Excel round-trip and folder creation. What was never done is pointing it at reality.

### 1.2 Where `PROJECTS_ROOT` bites — exact fix shape

`opportunity/config.py:63-68` resolves paths as `ENV var → repo-root-relative test default`:

```python
projects_root = Path(os.environ.get("PROJECTS_ROOT", str(project_root / "test_projects")))
archive_root  = Path(os.environ.get("ARCHIVE_ROOT",  str(project_root / "test_archive")))
templates_root= Path(os.environ.get("TEMPLATES_ROOT",str(project_root / "test_templates")))
excel_path_str= os.environ.get("PROJECT_CODES_EXCEL", "")   # unset → None → Excel legs silently skipped
```

Measured state: **no `.env` exists at repo root** (`ls .env` → not found) and `test_projects/`, `test_archive/`, `test_templates/` don't exist either. Consequences today: `com list/show/prep-deck/chat` report "Projects root not found"; `com new` would `mkdir(parents=True)` **inside the repo** at `<repo>/test_projects/`; both Excel touchpoints no-op. (Correction to Phase-1: the default is repo-root-relative via `Path(__file__).parents`, not CWD-relative.)

**Fix shape: pure config, but 5 lines, not 1** — no code change:

```
# repo-root .env (loaded by opportunity/config.py:48-53 AND corp/config.py:70 — same var names, so one file fixes both)
PROJECTS_ROOT=C:/Users/1028120/Documents/MyWork/10_Projects
ARCHIVE_ROOT=C:/Users/1028120/Documents/MyWork/90_Archive
TEMPLATES_ROOT=C:/Users/1028120/Documents/MyWork/20_Workflows/Master_Deck
PROJECT_CODES_EXCEL=C:/Users/1028120/Documents/MyWork/30_Reference/Project_Codes.xlsm
```

plus **one template pointer fix**: `config/opportunity/default.yaml:8` names `Blue_Yonder_Corporate_Presentation_Deck.pptx`; the real file is `20_Workflows/Master_Deck/Blue_Yonder_Corporate_Presentation_Deck_MARCH.pptx` (verified on disk) — edit the YAML value or rename the file.

Two contract-level facts qualify the "one config line" hope:

1. **Shared env-var namespace (helpful):** `corp/config.py:78-89` reads the *same* `PROJECTS_ROOT`/`ARCHIVE_ROOT`/`TEMPLATES_ROOT` names but already defaults to the REAL paths (`MyWork/10_Projects`, `MyWork/90_Archive`, `MyWork/20_Workflows`). Setting the env vars aligns both configs; the only side effect to note is `TEMPLATES_ROOT=…/Master_Deck` also narrows `corp.config.templates_root` (consumed only by dormant `template_manager` — see Step 6).
2. **`config/paths.toml` gap (the durable form):** the ecosystem's central path config (`paths.toml:5-14`) has `vault/mywork/secrets/rfp_kb` keys but **no projects/archive/templates/workbook keys**, and `opportunity/config.py` never reads it. The contract change — add 4 keys to `paths.toml` and port `AppConfig` to it — is the ADR-worthy version; the `.env` route is the 5-minute version.

### 1.3 What the module says the FINISHED tool was meant to be

- **Full lifecycle states, not just intake:** stage enum `discovery…won/lost/archived` (`config/opportunity/default.yaml:30-38`) — yet `com` has no verb to *change* stage and no archive verb.
- **Workbook as peer, not master:** `com new` writes col M and the panel's "Next steps" tells the operator to update the workbook (`cli.py:96`); `excel_manager.py:1-17` documents the full A–M layout including `E: Link to SF`.
- **A deal-knowledge model far beyond project-info.yaml:** `config/project/schemas/facts_template.yaml` (shipped with CPE, **zero code readers** — grep empty, present since the pre-monorepo package) models `opportunity_id: "" # Salesforce OP-number`, stage, timeline (first_contact→decision_expected), requirements, integrations, competitors, commercial, risks, security, team. This is the intended "finished" data contract for a deal folder.
- **Orchestrated, not standalone:** `config/workflows.yaml:5-26` `new_opportunity` = `com new` + `create_vault_skeleton` + `validate_project`; `config/agents.yaml:6-16` registers all 5 verbs with `confirmation: [new]`.

### 1.4 Minimal-completion spec candidate (evidence-based input, not design)

The smallest COM that serves D1 — "create canonical project folder at the right address + seed `_knowledge/project-info.yaml`":

| # | Element | Status | Evidence |
|---|---|---|---|
| 1 | `.env` with 4 path vars (above) | config only | `opportunity/config.py:63-68` |
| 2 | Template pointer fix (`_MARCH` mismatch) | 1 YAML line or 1 rename | `default.yaml:8` vs disk |
| 3 | Folder + `_knowledge/project-info.yaml` + `notes.md` creation | **already built & unit-tested** | `folder_manager.py:22-128`, `tests/opportunity/test_folder_manager.py` |
| 4 | Workbook col-M write-back | **already built**; requires row pre-exists + workbook closed (write path has no locked-file fallback, `excel_manager.py:107-110`) | `excel_manager.py:97-123` |
| 5 | Naming reconciliation with the 29 real folders | **NOT built** — `{client}_{product}` verbatim-case covers ~18/29 real names; multi-product (`Jaguar_Land_Rover_TMS_WMS_OMS`), acronym (`CCI`, `QDF`, `SGDBF`), and delimiter (`Wickes - J2CC`) forms fall outside the pattern; case gotcha already logged (folders verbatim vs vault lowercase) | Step 3 §3.4 table; `.claude/skills/gotchas` "Folder naming" |

Items 1–2 revive the tool; item 5 is the only *new* work D1-minimum needs, and it is the same addressing problem Step 3 measures. Explicitly NOT needed for D1-minimum: `com chat`/LLM layer, `prep-deck`, `folder_standards` audit, stage tracking.

---

## Step 2 — CPE status and drift

### 2.1 What `cpe` is (`src/corp/project/`, 2,163 lines)

`scan` (classify files → `_knowledge/manifest.yaml`), `extract` (local text extraction), `extract-cke` (generate `_knowledge/cke_manifest.json` → subprocess `cke process-manifest`), `render` (CKE `extract.json` files → `project-info.yaml` + `facts.yaml` + `index.md`), `show`, `run` (scan→extract→render). `cli.py:87-328`.

### 2.2 Interface drift vs current CKE: **NONE at the contract level**

| Contract surface | CPE side | CKE side (current) | Verdict |
|---|---|---|---|
| Command | `process-manifest` (`cke_invoker.py:72`) | `@cli.command("process-manifest")` `extractor/scripts/run.py:675` | match |
| Flags | `--max-rpm N`, `--resume` (`cke_invoker.py:74-79`) | `run.py:677-678` (plus additive `--force`, `--batch`, tier opts) | match |
| Manifest schema | `schema_version:1`, `files[].{id,path,doc_type,name,client,project}`, `output_dir` (`manifest_generator.py:144-162`) | `Manifest.from_file` requires exactly `schema_version==1`, `id`, `path`, `output_dir`; rest optional (`extractor/manifest.py:44-73`) | match |
| CKE resolution | venv → `cke` on PATH → `sys.executable run.py` (`cke_invoker.py:26-47`) | monorepo installs `cke` entry point (`pyproject.toml:53`) | works |

Git history confirms: since March the only changes to `extractor/manifest.py` + `run.py` are the `status.json` retry fix (`1a057f2`, satisfies the CLAUDE.md §5 learned rule), docstring and constant hygiene. The March–June churn did not touch this interface. **The Lenzing-pilot-era pipeline still matches.**

### 2.3 Real drift list (all small, all local to CPE)

1. **`clients.yaml` path bug — alias resolution silently dead.** `manifest_generator.py:107` computes `Path(__file__).parent.parent.parent / "config" / "clients.yaml"` = `src/config/clients.yaml` (does not exist). The real file is `config/project/clients.yaml` (exists, 6 aliases incl. `Jaguar: "Jaguar Land Rover"`). Consequence: client names in CKE manifests degrade to the folder's first token (`Jaguar`, `Penguin`) unless `--client` is passed. One-line fix.
2. **`cpe render` clobbers COM's `project-info.yaml` with a different schema.** COM writes `{client, product, contact, stage, created, folder_name}` (`opportunity/models.py:34-43`); render overwrites the same file with `{project, status, rendered_at, files_processed, topics, products, people, doc_type_distribution, opportunity{…}}` (`renderer.py:108-143`). "com compatible" (`renderer.py:5`) is true only in the display sense — `com show` dumps arbitrary keys (`cli.py:150-152`) so it won't crash, but COM's seeded fields (contact, stage, created) are **lost on first render**. Ownership decision required before both run on the same folders.
3. **`index.md` Dataview block queries the phantom zone:** `FROM "02_sources"` (`renderer.py:288`) — the vault zone that never existed on disk (Phase-1 discrepancy c-2); real notes live in `01_Knowledge`. Cosmetic (Obsidian query returns empty), one line.
4. **`config/project/default.yaml` paths block** expands `${PROJECTS_ROOT}`/`${ARCHIVE_ROOT}` (`project/config.py:92-100`) — unset today, resolving to literal `${…}` strings; harmless because every `cpe` command takes an explicit path argument, but the same `.env` from Step 1 makes it truthful.

### 2.4 Use and revival cost

Zero real-world runs: `find 10_Projects -name manifest.yaml` → none; 0/29 folders have `_knowledge/` at all. The renderer carries the 2026-04-21 fail-closed OneDrive guard (`renderer.py:38-52`), so running it against local MyWork folders is safe by construction.

**Revival cost: LOW.** = Step-1 `.env` (shared) + fix #1 (+ optionally #2's ownership decision before mixing with COM) + `cpe run` per folder. Reference cost: `config/agents.yaml:25` estimates $0.20/project → ~$6 for all 29 folders. CPE is the cheapest living bridge between deal folders and the knowledge loop.

---

## Step 3 — Project_Codes.xlsm de-facto contract

Read-only inspection (openpyxl `read_only=True, keep_vba=True`), 2026-07-05. File: `MyWork/30_Reference/Project_Codes.xlsm`.

### 3.1 Physical shape

- **Sheets:** `Main` (active; 13 cols × 53 rows; **52 data rows**) and `Raw` — row 1 reads *"56 items • Sorted by Opportunity Owner • Filtered by Stage, …"*: a pasted **Salesforce list-view export**. The workbook *is* the manual SF leg.
- **Seeding:** col K `Date Added` = `2026-03-05` on every sampled row — single one-time seeding; freshness since then is manual curation.

### 3.2 Column contract (Main) — measured fill rates

| Col | Header | Fill | Notes / who reads it today |
|---|---|---|---|
| A | (empty) | — | padding; code indexes are 0-based from it (`excel_manager.py:31-36`) |
| B | Name | 52/52 | SE name ("Robert Dwornik") — no code reader |
| C | Account Name | 52/52 | **join key** — `find_row_by_client` case-insensitive *substring* match (`excel_manager.py:80-82`); displayed by `com list` |
| D | Opportunity Name | 52/52 | displayed |
| E | Link to SF | **52/52** | `https://blueyonder.lightning.force.com/…` — no code reader |
| F | Booking Amount | — | no code reader |
| G | JDA Industry | 52/52 | read into `ProjectRow.industry`, displayed nowhere |
| H | **Stage** | 52/52 | read for `com list` display only — **nothing consumes it** |
| I | Close Date | 52/52 | SF's close date (2025-02 → 2027-08) — no code reader |
| J | JDA OpptyID2 | **52/52** | `OP-0######` — the stable key `facts_template.yaml:7` was designed for; no code reader |
| K | Date Added | 52/52 | no code reader |
| L | Next Step | — | no code reader |
| M | **Folder Link** | **0/52** | the `com new` write-back column — never once written (matches zero-use verdict); header itself absent until first write (`excel_manager.py:115-117`) |

Sole code toucher of the workbook anywhere in the repo: `corp.opportunity.excel_manager` (+ its config/chat callers) — repo-wide grep confirms.

### 3.3 Stage vocabulary — the real close-out signal

Distinct col-H values (counts): `Solution` 20, `Disqualified` 13, `Negotiate` 5, `Prove Value` 5, `Loss` 4, `Qualify` 4, `Won` 1.

This is **Salesforce's stage vocabulary, not COM's** (`discovery/qualification/rfp/proposal/negotiation/won/lost/archived`, `default.yaml:30-38`) and not the archive `REASON_KEYWORDS` (`won/lost/cancelled/on_hold`, `intent_router.py:52-62`). A Win/Loss→archive trigger keys on **H ∈ {Won, Loss, Disqualified}** — 18 rows qualify today (1 Won: Honda Motor Europe · 4 Loss · 13 Disqualified) — and needs an explicit stage→reason map (`Won→won`, `Loss→lost`, `Disqualified→cancelled`?) as a decision input, plus col I as the archive-year source *from the workbook*, not file timestamps (operator standing rule).

### 3.4 Addressing mismatches — the problem in miniature

Applying the code's own join semantics (folder first token as substring of Account Name) across 29 folders × 52 accounts: **18 resolve, 11 fail.**

| Failure class | Folders | Root cause |
|---|---|---|
| Acronym folder vs full account | `CCI_Planning` (Coca-Cola Icecek A.S.), `QDF_CatMan` (QATAR DUTY FREE), `SGDBF_Retail` (Saint-Gobain Distribution Bâtiment France), `IFM_Planning` (no candidate) | operator abbreviates; workbook carries legal names |
| Folder with no workbook row | `Essity_TMS`, `Tata_Steel_J2CC`, `Unilever_AnR`, `Wickes - J2CC` | deals not in the 2026-03-05 SF snapshot (or added outside it) |
| Orthography | `Wurth_Retail` vs `Wuerth International AG`; `Zabka_Retail` vs `Żabka Polska Sp. z o.o.`; `LabelVie_TMS` vs `Label'Vie SA` | ASCII-folding / apostrophes — same mojibake-class problem the vault already has |
| Delimiter breaks tokenizing | `Wickes - J2CC` (space-dash, no underscore) | folder ignores the `{client}_{product}` convention entirely |

Reverse gap: workbook rows with no folder — incl. the only **Won** deal (Honda). `config/project/clients.yaml` already models the alias solution (`Jaguar → "Jaguar Land Rover"`) but has 6 entries and, per Step 2.3-1, is unreachable by the code that wants it. The ingest side solved this same problem with `get_client_variants` (`naming_config`, per repo gotcha) — reuse candidate.

### 3.5 De-facto contract statement

> `Project_Codes.xlsm[Main]` is an operator-curated snapshot of Rob's SF opportunity list, seeded 2026-03-05 from a pasted list view (`Raw`), keyed by legal Account Name (C) with SF URL (E) and OP-number (J) present on every row; Stage (H) tracks SF stage words; col M is reserved for tool-written folder links and has never been written. Any automation must treat C as fuzzy, J as the stable key, H as the close-out signal, and the whole file as manually refreshed.

---

## Step 4 — Archive mechanics and trigger design inputs

### 4.1 What exists (mechanism: EXISTS-UNTESTED, guarded, complete)

`archive_project` action (`actions/archive_actions.py:20-86`): resolve project → **`_guard_writable`** (resolve(strict=False) + dual substring check, fail-closed `OneDriveSafetyError`, `_helpers.py:103-134`) → `shutil.move` folder to `archive_root/{year}/` (dest-exists refusal = idempotence guard) → stamp `status/archive_reason/archive_date/archive_notes` into the **vault** copy of `project-info.yaml`. Safety regression tests exist (`tests/test_actions/test_archive_onedrive_safety.py`, 3 tests).

Workflow wiring (`config/workflows.yaml:115-134`): `cpe render {project_path}` (final knowledge snapshot) → `archive_project` → `update_archive_metadata`, `confirmation: true`; engine aborts on first failed step (`workflow_engine.py:196-198`).

### 4.2 What invokes it today — two surfaces, both operator-initiated

1. `corp chat` → trigger phrases `archiwizuj/archive/zamknij projekt/close project` + reason keywords (`workflows.yaml:117`, `intent_router.py:52-62`), path resolved via `project_resolver` fuzzy scoring over `projects_root` (`chat.py:128-136`, `project_resolver.py:19-49`).
2. **`corp run archive_project --project X --reason won`** — direct CLI (`cli/workflow.py:13-66`). *Correction to Phase-1's "keyword chat only".*

Nothing scheduled, nothing status-driven. Use: `90_Archive/` contains zero entries ever (verified).

### 4.3 Dead/misdocumented legs found

- **Vault stamp is a permanent no-op:** both actions write to `vault_path / VaultZone.PROJECTS / …` = `ObsidianVault/projects/` — a zone that **does not exist** in the vault (verified listing: `00_Home/01_Knowledge/02_Navigate/99_System` only). `info_file.exists()` is always False → silently skipped. The `create_vault_skeleton` step of `new_opportunity` (never run) is what would have created it.
- Docstrings say `80_Archive` (`archive_actions.py:22,128`); the real constant is `ARCHIVE = "90_Archive"` (`folder_names.py:17`) — comment rot only, code is correct.

### 4.4 What a status-driven trigger needs (evidence-derived inputs, not design)

| Ingredient | State | Evidence |
|---|---|---|
| Read Stage col | **exists** — `list_projects` already returns `stage` per row | `excel_manager.py:126-152` |
| Workbook = source of truth | operator standing rule; col I supplies the close date, col H the state — **never file timestamps** | Step 3.3 |
| Row→folder join | **missing** — col M empty 0/52; name matching fails 11/29 (Step 3.4). Chicken-and-egg: col M was to be populated by the very tool that never ran | `excel_manager.py:36`, Step 3 |
| Stage→reason map | **missing** — {Won,Loss,Disqualified} → {won,lost,cancelled?} decision; `Disqualified` (13 rows, largest closed class) has no obvious mapping | Step 3.3, `intent_router.py:52-62` |
| Invocation | **exists** — call the `archive_project` workflow; abort-on-failure and `confirmation: true` already there | §4.1 |
| Idempotence | **exists** (dest-exists refusal) + trigger must skip already-archived rows (needs a marker: col M rewrite, or a new col) | `archive_actions.py:51-57` |
| Scheduling precedent | N5 nightly conformance proves scheduled loops run on this estate | Phase-1 synthesis §1 |

### 4.5 OneDrive constraint on "archive everywhere"

Local-only by construction: `_guard_writable` refuses any resolved path containing the exclusion-zone string, so archiving the SharePoint-synced copy of a deal folder is **intentionally impossible**. Per the lifecycle audit (§2.2, `2026-07-05-functional-artifact-lifecycle.md`): *"any future … 'archive everywhere' (D5) leg cannot be implemented as writes into the synced tree; it must go through a Graph API client that does not yet exist."* The D5 ambition therefore decomposes into: local archive (buildable now) + SharePoint leg (gated on the Step-5 Graph decision).

---

## Step 5 — Missing legs, enumerated exactly

### 5.1 Salesforce — complete trace inventory (confirms and extends Phase-1)

Repo-wide sweep (`salesforce|lightning.force`, all source/config/docs, .venv/.git excluded):

| # | Trace | Nature |
|---|---|---|
| 1 | `config/project/schemas/facts_template.yaml:7` — `opportunity_id: ""  # Salesforce OP-number` | the one YAML comment Phase-1 found; zero code readers |
| 2 | `config/extractor/taxonomy_review.yaml:622` — `- Salesforce` | extracted unknown term (data noise, not integration) |
| 3 | `src/corp/opportunity/excel_manager.py:8` — docstring `E: Link to SF` | column documentation |
| 4 | The workbook itself: 52 `lightning.force.com` URLs (col E) + 52 `OP-######` ids (col J) + the `Raw` sheet SF list-view paste | **the de-facto SF integration is a human copy-paste** |

No SF client code, no `simple_salesforce`/API dep anywhere. The trigger for D1 ("AM adds Rob to an Opportunity Team") reaches the system only when Rob pastes/updates the workbook.

### 5.2 SharePoint / Graph

- `pyproject.toml:42` — `graph = ["msal>=1.24"]` optional extra: **zero imports of msal anywhere** (repo-wide grep). Declared intent, nothing more.
- No `graph`/`office365`/`azure` imports in `src/` or `scripts/`. The only SharePoint-related code posture is *negative*: 4 fail-closed guards + `'onedrive'/'sharepoint'` as source-location labels (`schema/models.py:162`; lifecycle audit §2.2).

### 5.3 Reference implementation to reuse (cite, don't copy)

`corp-sca-time-automation/src/sharepoint.py` — the ecosystem's one **working** Graph client (writes SCA time entries to a SharePoint list):

- **Auth:** `get_access_token()` fallback chain — `GRAPH_ACCESS_TOKEN` env → `az account get-access-token --resource https://graph.microsoft.com` (subprocess, `shell=True` per the az-on-Windows gotcha) → clean `SystemExit` telling the user to `az login`. **No msal, no app registration** — it rides the corporate az CLI session.
- **Transport:** plain `requests` against `graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items`; site/list ids in config.
- Implication: the monorepo's `msal>=1.24` extra was the wrong guess; the proven on-this-machine pattern is az-CLI-delegated tokens + requests. Any COM SharePoint leg (create Teams-channel folder, publish archive copy) starts from this file's pattern.

### 5.4 Want-level decision inputs per leg (not designs)

| Leg | Value to D1/D5 | Build-cost class | Cheapest alternative that keeps the value |
|---|---|---|---|
| **SF read** (opportunity list/stage into the system) | kills the manual paste; makes Stage col live → real close-out trigger; OP-number as stable key | M–L and **environment-gated** (corporate SF API access/SSO unknown; nothing in-repo proves it's obtainable) | keep the workbook as the interface (cost ≈ 0); improve the paste ritual; trigger reads H as today |
| **SP write** (publish/archive to team SharePoint) | completes "archive everywhere"; enables W4 later | M (Graph client + site/list ids + az-token pattern proven next door) | none locally — guards forbid the naive path by design; defer until local D5 loop proves valuable |
| **SF write-back** (stage changes from system → SF) | out of hypothesis scope; SF is upstream master | L, high risk | don't |

---

## Step 6 — N4 kill confirmation + template reality

### 6.1 `task_manager` — kill-candidate verdict **CONFIRMED**

- **Capability:** vault-note tasks in `vault/dashboards/tasks/` (`task_manager.py:23-26`), full CLI (`corp task add/list/done`, `corp tasks` — `cli/__init__.py:11-14`), `add_task`/`list_tasks` workflows + intent routing, bilingual slugifier with 80+ Polish stop words (`task_manager.py:36-114`) — substantial build effort.
- **Use — zero, on every axis checked:** the vault has **no `dashboards/` zone at all** (listing verified: `_assets/_quarantine/00_Home/01_Knowledge/02_Navigate/99_System` only) → not one task note was ever created; JOURNAL mentions `task_manager.py` only twice, both as *maintenance objects* (error-handling narrowing; `TaskStatus.TODO` as a TODO-audit false positive) — never as a used feature; tasks don't touch ops.db, so vault absence *is* the telemetry; Phase-1 found no use either.
- Evidence-side conclusion: N4 is triple-shelf-ware — built, wired into chat/CLI/workflows, never once invoked with intent. Nothing in 4 months of JOURNAL contradicts the kill. (Removal itself is an operator deletion decision per P0 rules.)

### 6.2 `template_manager` — what it actually manages, and the deck-brief Q4 answer

- **Types managed** (by extension inference, `template_manager.py:29-33,134-145`): `presentation` (.pptx), `questionnaire` (.xlsx), `document` (.docx), `data` (.csv/.json), `demo_script` (.docx in "Demo Scripts" dirs). **`.potx` is not a recognized extension** — a real brand template (`BlueYonder-Powerpoint-Template_2025-…usecases.potx`, found inside `10_Projects/Wurth_Retail/`) could never register.
- **Registry:** `vault/.corp/template_registry.yaml` (`_registry_path()`, `template_manager.py:70-75`; `CORP_INFRA=".corp"`). Measured: **the file exists nowhere** — not in the vault (no `.corp/` there), not in `MyWork/.corp/` (holds `config.json`, `content_registry.yaml`, `routing_map.yaml`, `solution_matrix.json` only). `load_registry()` → `[]` always; `select_template()` → fallback/None; `corp template scan` has never been run to completion anywhere it left a trace.
- **Stale labels confirmed:** scans `cfg.templates_root` (default `MyWork/20_Workflows`) but hardcodes the recorded path prefix as `30_Templates/` (`template_manager.py:186,349`) and the docstring claims `90_System/template_registry.yaml` (`:3`) — three different names for directories that don't exist under those names.
- **Deck-brief Q4 — final word: NO deck template is registered anywhere.** `KM_v2` exists as `30_Reference/Training/2026_Platform_Training_Warsaw/Platform Overview_KM_v2.pptx` — outside every configured templates root, invisible to `scan_templates` even if it ran. The only template pointer that any live config holds is `config/opportunity/default.yaml:8` → `Blue_Yonder_Corporate_Presentation_Deck.pptx`, a broken pointer (real file has `_MARCH` suffix). The `.potx` sits unregistrable in a project folder. Template management for decks is: one stale YAML string plus one dormant, empty-registry subsystem.

---

## Backlog-seed table

Inputs for post-R1 sequencing — evidence-backed, decisions flagged. Sizes are gut-feel (XS ≤ 1h, S ≤ ½ day, M ≤ 2 days, L > 2 days).

| Seed | Goal (functional) | Evidence | Depends on | Size gut-feel | Decision required first? |
|---|---|---|---|---|---|
| E1. Point COM at reality | `.env` 4 path vars + template pointer fix; `com new/list/show` work against MyWork | Step 1.2 | — | **XS** | No — operator already ruled FIX |
| E2. Fix `clients.yaml` lookup path | CPE alias resolution live (`config/project/clients.yaml` actually read) | Step 2.3-1 | — | **XS** | No |
| E3. `project-info.yaml` ownership contract | COM seed + CPE render coexist without clobbering (merge vs namespace decision) | Step 2.3-2 | E1 | S | **Yes** — schema ownership |
| E4. Workbook⇄folder addressing contract | Every folder resolves to a workbook row (aliases; OP-number J as stable key; reuse `get_client_variants`) | Step 3.4 | E1 | S–M | **Yes** — canonical key + normalize-vs-alias choice |
| E5. Col-M backfill for 29 existing folders | Workbook rows link to real folders; join for E7 becomes trivial | Step 3.2 (M = 0/52) | E1, E4 | S | Yes — retro-link tool vs manual paste |
| E6. Vault leg: create-or-drop | Either `create_vault_skeleton` runs (vault `projects/` zone exists) or archive stamp steps are removed | Step 4.3 | — | S | **Yes** — vault zone model |
| E7. Status-driven archive trigger | `corp deals sync`-style read of col H → propose archives for {Won,Loss,Disqualified}, confirm, run existing workflow | Steps 3.3, 4.4 | E4 (+E5) | M | **Yes** — stage→reason map; Disqualified policy; confirmation UX |
| E8. CPE revival run | `cpe run` across 29 folders → manifests + `_knowledge` + facts (~$6 total) | Step 2.4 | E1–E3 | S | No (cost trivial) |
| E9. SF leg want-level | Decide: build SF read integration vs keep workbook-as-interface | Step 5.4 | — | decision only | **Yes** — and env-gated (API access unproven) |
| E10. SP/Graph leg want-level | Decide: build Graph client (az-token pattern per corp-sca-time-automation) for archive-everywhere/W4 | Steps 4.5, 5.3 | E7 proves local loop first | decision only (build M) | **Yes** |
| E11. Kill N4 (task_manager + CLI + workflows + intents) | Remove triple-shelf-ware; shrink chat surface | Step 6.1 | — | XS (removal) | **Yes** — deletion needs operator sign-off |
| E12. template_manager disposition | Kill, or repoint at a real templates dir + add `.potx` — only in service of the D4 design, which Phase-1 called honest greenfield | Step 6.2 | D4 design | decision only | **Yes** |

---

*End of Deep Audit E. Read-only discipline held: writes in this session = this file + the companion HTML process map. JOURNAL entry deferred to the merge session per the Wave-2 "deliverables-only writes" rule.*
