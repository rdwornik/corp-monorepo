---
date: 2026-06-21
type: audit
scope: foundation-extension verification (read-only)
branch: audit/2026-06-21-foundation-review
status: complete
owner: Rob
---

# Foundation-Extension Verification Pass

> **Read-only audit.** Verifies the open repo/disk-state questions behind a Layer-1
> foundation-extension brief before any implementation. **No code/config/data was
> mutated; nothing was created, deleted, or written under `OneDrive - Blue Yonder`.**
> The only artifact is this document.

## Purpose

A Layer-1 architect (no repo access) produced a brief from `ARCHITECTURE.md` plus a
now-stale MyWork audit, proposing four changes:

1. Generated single-source **manifest** view (`MANIFEST.md` / `corp manifest`)
2. Physical-taxonomy **conformance guard**
3. **Naming v3** (ADR-14 successor: per-TYPE date granularity + optional `_vNN`/`_status`)
4. Declared per-zone **sync policy** (OneDrive Files-On-Demand keyed to mutability class)

This pass grounds each proposal's assumptions against actual code and disk state.
**Headline: three of the four proposals do not survive contact with the repo as the
brief assumed them** (see verdict table). All paths use forward slashes; evidence is
cited as `file:line` or resolved-path + observed state.

---

## 1. Findings (S1–S8)

### S1 — Zone source-of-truth → **SPLIT** (grounds: manifest generator)

`src/corp/schema/folder_names.py` is a deliberate zero-import single source of truth
(`folder_names.py:1-8`) for the **7 canonical top-level zones**: `00_Inbox`,
`10_Projects`, `20_Workflows`, `30_Reference`, `70_Admin`, `80_Compliance`,
`90_Archive` (`folder_names.py:11-17`, tuple at `:28-30`). **But** zone truth is
**split**: `config/content_registry.yaml` independently hardcodes routing destinations
into zones that do **not** exist in `folder_names.py` — `30_Templates`
(`content_registry.yaml:71,80`), `50_RFP` (`:55,63`), `60_Source_Library`
(`:12,26,38,88`). No existing `corp` subcommand renders a "what-goes-where" manifest;
`corp doctor` (`cli/system.py`) is the closest path-aware command and it validates, not
documents.

### S2 — `folder_names.py` → YAML feasibility → **FEASIBLE, no blockers** (grounds: config-in-YAML alignment)

`folder_names.py` holds only static string constants plus `frozenset`/`tuple`
memberships (`SCAN_SKIP_FOLDERS:33-36`, `ALL_MYWORK_FOLDERS:28-30`). There are **zero**
`match` statements, `Enum` definitions, or `Literal[...]` type annotations built over
the constants — i.e. no construct that would break if the values moved to YAML. ~28
production modules import the symbols (e.g. `integrity.py`, `ingest/router.py`,
`ingest/llm_classifier.py`, `schema/pipeline_config.py`), all as plain symbol imports
satisfiable from a YAML-loaded source. The file header itself states *"single source of
truth … Zero imports."* **Conclusion:** the taxonomy can move into `paths.toml` or a
dedicated YAML consumed by `schema.config` without breaking importers; the only test
that would need rework is `tests/schema/test_folder_names.py` (it asserts the Python
constants directly).

### S3 — Declared-vs-actual conformance → **7/7 zones exist; 1 rogue; registry phantoms confirmed** (grounds: conformance guard + the "`02_sources` phantom")

MyWork root resolves to **local** `C:/Users/1028120/Documents/MyWork`
(`config/paths.toml:7`, via `schema/config.py:77-79`). First-hand metadata-only disk
listing of the root:

| Zone | Configured path | Exists? | Source |
|---|---|---|---|
| `00_Inbox` | `…/MyWork/00_Inbox` | **Y** | `folder_names.py:11` |
| `10_Projects` | `…/MyWork/10_Projects` | **Y** | `folder_names.py:12` |
| `20_Workflows` | `…/MyWork/20_Workflows` | **Y** | `folder_names.py:13` |
| `30_Reference` | `…/MyWork/30_Reference` | **Y** | `folder_names.py:14` |
| `70_Admin` | `…/MyWork/70_Admin` | **Y** | `folder_names.py:15` |
| `80_Compliance` | `…/MyWork/80_Compliance` | **Y** | `folder_names.py:16` |
| `90_Archive` | `…/MyWork/90_Archive` | **Y** | `folder_names.py:17` |
| `.corp` (infra) | `…/MyWork/.corp` | **Y** | `folder_names.py:20` |
| `.claude` (harness) | `…/MyWork/.claude` | **Y** | (implicit) |
| `30_Templates` | `…/MyWork/30_Templates` | **N** | `content_registry.yaml` only (phantom) |
| `50_RFP` | `…/MyWork/50_RFP` | **N** | `content_registry.yaml` only (phantom) |
| `60_Source_Library` | `…/MyWork/60_Source_Library` | **N** | `content_registry.yaml` only (phantom) |

**Rogue top-level dirs (present, undeclared) = 1: `15_Extra_Inititives`** (sic — typo'd
in the folder name). All 7 declared zones materialize (100%). The three
`content_registry.yaml` destinations above are absent from disk (confirmed by their
non-appearance in the listing).

**The brief's "`02_sources` phantom" is a namespace error**, not a finding:
`02_sources` is a **vault** zone (`src/corp/models.py`), not a MyWork zone.
`ARCHITECTURE.md` correctly names `vault_io` its sole writer; it is not a MyWork-taxonomy
conformance issue.

### S4 — Existing integrity coverage → **conformance guard is an EXTENSION, not new** (grounds: NEW vs EXTENSION)

`integrity.py::check_all()` already runs:
- `_check_mywork_structure` (`integrity.py:377-406`) — asserts the **7 required zones
  exist** (raises `error` on missing).
- `_check_registry_paths` (`integrity.py:153-212`) — asserts **registry destinations
  exist** under MyWork (raises `warning` on missing — so the 3 phantom zones from S3 are
  *already* surfaced by `corp doctor` today).

| Conformance aspect | Present? | Evidence |
|---|---|---|
| (a) declared zones exist on disk | **Yes** | `integrity.py:377-406`, `:153-212` |
| (b) no rogue top-level dirs | **Absent** | only checks *required* set, never rejects extras |
| (c) filenames conform to ADR-14 | **Absent** | no naming-pattern check anywhere in `check_all()` |

**Delta a guard would add:** rogue-top-level-dir detection (b) + ADR-14 filename
conformance (c), reusing the existing `IntegrityIssue` / `IntegrityReport` scaffold.

### S5 — CKE output placement → **staging-only; splatter is legacy, not regenerating** (grounds: P3 splatter)

Current extraction writes to a staging directory under app data:
`config.app_data_path / "staging" / "ingest" / {id}` (`ingest/router.py:667` for
packages, `:757` for single files), then `move_to_vault(...)` relocates results into a
flat vault subdir (`ingest/extractions.py`). No live code path writes extraction outputs
into scattered per-source directories. **Conclusion:** the stale audit's "one name in
161 directories" is **pre-existing legacy** (GC-able later), **not** an active defect.
Caveats for the implementer: (i) `ARCHITECTURE.md` calls the staging dir `_outputs/`, a
literal that does not appear in code (naming-only drift, see §3); (ii) the exact vault
destination subdir should be re-confirmed before any GC.

### S6 — Routing-feedback loop → **OPEN (logs only, by design)** (grounds: does the registry learn?)

The `routing_feedback` and `registry_suggestions` tables accumulate decisions
(`ops/database.py:128-145`, `:160-169`) but **no code writes back to
`config/content_registry.yaml`** — there is no `yaml.dump`/writer targeting the registry
anywhere; `ops/registry.py` only reads and caches it. The design is explicit at
`ops/database.py:126-127`:

> `-- DECISION (Council 2026-03-25): Manual rules only. No automated learning.`
> `-- Revisit when: loose files > 50/month AND override rate > 40% for 3 months.`

The CLI surfaces overrides for manual review (`routing-review`) and can mark them
reviewed, but never promotes them. **Conclusion:** open loop, human-in-the-loop by
design; the registry does not self-learn.

### S7 — Naming v3 readiness → **flexible impl, needs a policy decision** (grounds: ADR-14 v3)

Implemented grammar `{YYYY-MM}_{TYPE}_{CLIENT}_{Desc}.{ext}` is **token-assembled**
(`ingest/renamer.py:158-160`: `parts = [date, type, client, desc]; "_".join(parts)`),
**not** regex-rigid — regex appears only to detect already-compliant names
(`renamer.py:34`). `{Desc}` is the cleaned original filename stem (`renamer.py:97-108` →
`schema/naming_config.py::clean_description`). Authoritative controlled vocab is
`config/naming_config.yaml` = **22 type codes + 32 client aliases** (not the 19/15 ADR-14
states — see §3). Test coverage: `tests/test_ingest/test_renamer.py`, ~85 tests across 9
classes.

Effort:
- **(a) optional `_vNN` (zero-padded) + `_status` suffix tokens** → **low**: append to the
  token list and widen the compliance regex (`:34`).
- **(b) per-TYPE date granularity** (`YYYY-MM-DD` for deliverable types, no date for
  living/reference) → **medium**: needs a deliverable-vs-living **TYPE classification that
  does not exist yet** (a new field in `naming_config.yaml` + a helper + a conditional at
  `renamer.py:136`).

Backfill count requires a disk scan (code holds no inventory); ADR-14 itself states
*"existing files migrated on-touch (no bulk rename)."*

### S8 — Sync policy + is MyWork OneDrive-backed → **NO; premise invalid** (grounds: sync-policy design)

Only a **binary OneDrive exclusion guard** exists — fail-closed resolve+substring checks
at four mutation sites (`cleanup/disk.py:28-56`, `cleanup/executor.py`,
`actions/_helpers.py`, `project/renderer.py`). There is **no per-zone sync-state**
concept. A per-file cloud-only attribute check exists for dedup overlap only
(`cleanup/disk.py` `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS`), not a policy lever.

**Critically:** the code's MyWork root is **local** — `C:/Users/1028120/Documents/MyWork`
(`config/paths.toml:7`). The `OneDrive - Blue Yonder/MyWork_OneDrive` store is a
**redundant post-migration copy** the code never reads or writes
(`cleanup/disk.py:23-25`: *"redundant copy of local MyWork after migration"*).
**Conclusion:** OneDrive Files-On-Demand cannot govern the operational path, so the
sync-policy proposal's premise (a ~1.1 TB OneDrive-backed store driven by Files-On-Demand)
is **invalid as stated** for the path the code uses.

---

## 2. Readiness verdict

| Item | Verdict | The one fact that determines it |
|---|---|---|
| **manifest-generator** | **NEEDS-DECISION** | `folder_names.py` is a clean zero-import SSOT for 7 zones, but `content_registry.yaml` declares 3 routing-only zones (`30_Templates`/`50_RFP`/`60_Source_Library`) absent from both it **and** disk — a manifest must decide: render `folder_names` only, or reconcile registry destinations (incl. phantoms)? |
| **conformance-guard** | **READY (extension)** | `integrity.py` already asserts required-zone + registry-destination existence; a guard only adds rogue-top-level-dir + ADR-14 filename checks (both absent) on the existing `IntegrityReport` scaffold. |
| **naming-v3** | **NEEDS-DECISION** | Renamer is token-assembled (low effort to extend), but per-TYPE date granularity needs a deliverable-vs-living TYPE classification that doesn't exist yet; and ADR-14's own text is already stale (says 19/15 vs implemented 22/32). |
| **sync-policy** | **BLOCKED** | The operational MyWork root is **local** (`paths.toml:7`); the OneDrive `MyWork_OneDrive` is a redundant copy the code never touches — Files-On-Demand can't govern the path the code uses, invalidating the premise. |

---

## 3. Doc drift (contradicts `ARCHITECTURE.md` / ADR-14 / brief)

1. **`schema/config.py:78`** — `mywork_path()` docstring says *"MyWork root (OneDrive
   project files)"*, but it resolves to **local** `Documents/MyWork` (`paths.toml:7`), and
   `cleanup/disk.py:23` calls the OneDrive store a *"redundant copy of local MyWork after
   migration."* Docstring is stale/misleading.
2. **ADR-14** body says *"19 type codes … 15 client aliases"* with example codes
   `DECK/CERT/QA/PROP` — the authoritative `config/naming_config.yaml` has **22 codes / 32
   aliases**, and those example codes do not appear in it. ADR text lags the YAML it
   declares authoritative.
3. **`ARCHITECTURE.md`** "Accepted Limitations" — *"synthesize.py writes to `_outputs/`
   staging."* Actual staging path is `{app_data_path}/staging/ingest/{id}/`; the literal
   `_outputs/` is not in code (naming-only drift).
4. **Brief input drift** — the stale MyWork audit's "`02_sources` phantom" conflated the
   **vault** namespace with **MyWork**; `02_sources` is a vault zone (`models.py`), not a
   MyWork-conformance finding.

---

## Method & guardrails

- **Read-only** on all code/config/data; the sole write is this document. No fixes,
  refactors, migrations, or folder creation.
- Paths resolved via the repo's own resolver (`schema/config.py` `get_path`: ENV >
  `paths.toml` > defaults). Disk state observed via metadata-only directory listing on the
  **local** MyWork root.
- Nothing written or deleted under `OneDrive - Blue Yonder`; nothing deleted anywhere
  (Invariant #5 / ADR-27).
- Conventions read from the repo, not reconstructed from memory.
