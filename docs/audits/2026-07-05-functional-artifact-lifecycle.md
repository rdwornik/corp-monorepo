# Functional Audit — Artifact & Storage Lifecycle (Phase 4)

**Date:** 2026-07-05 · **Branch:** `docs/2026-07-05-functional-audit` · **HEAD:** `fb9b2dd` (+3 audit commits)
**Method:** read-only; sizes from Phase-1 local scans; OneDrive estate figures cited from `docs/audits/2026-06-16-current-state-architecture-audit.md` (present on main) — the mirror was NOT traversed in this audit.

---

## 1. Artifact classes: born → lives → moves → backup tier → size → regenerable → risk

| # | Artifact class | Born where | Lives where | Moves when/how | Sync/backup tier | Measured size | Regenerable? | Risk |
|---|---|---|---|---|---|---|---|---|
| 1 | Client source docs (originals) | SharePoint/Teams/email | OneDrive synced mirror (excluded zone) + team SharePoint | Manual save-as into `MyWork/00_Inbox` for capture (`corp-ops/sync-mywork.ps1` also mirrors OneDrive→MyWork one-way) | Cloud (SharePoint) for team material | mirror: 159,826 files / 1.1 TB, 96% cloud-only (2026-06-16 audit) | n/a (cloud is master) | LOW for team docs; local-only personal files inside the mirror were the historical incident class |
| 2 | Routed working copies (MyWork zones) | W1 routing or manual filing | `MyWork/{10_Projects,20,30,80}` | W1 route (dormant since 03-27); manual daily edits (alive) | **NONE** — local disk only (except whatever sync-mywork mirrors FROM cloud; anything authored locally has no upstream) | ~10.9 GB / ~2,240 files (10_Projects 6.6 GB, 30_Reference 3.8 GB) | Partially (cloud-originated files re-downloadable; locally-authored decks/responses NOT) | **HIGH** — active deal work with no off-machine copy |
| 3 | Extraction outputs / staging | CKE runs | repo `data/_outputs/` (v2 11.3 GB, v3 6.9 GB, golden_set 107 MB); `%LOCALAPPDATA%/corp-by-os/{staging,overnight_staging}` (~KB) | ingest-extractions consumes them into vault; otherwise inert since 2026-03-26 | None (`.gitignore:31,34` excludes `_outputs/`) | **18.4 GB** | YES (re-extraction; March full runs cost cents–dollars) | LOW value / HIGH disk cost — top disposable candidate (report only) |
| 4 | Vault notes (knowledge base) | W2 ingest → `01_Knowledge` | `ObsidianVault/` (850 .md + assets) | frozen since 2026-03-27; index reads them | **Local git repo with NO remote** (last commit 2026-03-26) | ~48 MB | Partially — re-extractable only where `source_path` still resolves; sampled notes already show `rebuild_status: source_inaccessible` after the March folder restructure | **HIGH** — the system's entire accumulated knowledge, one disk failure from gone |
| 5 | Operational DBs | pipeline writes | `%LOCALAPPDATA%/corp-by-os/{ops,index,overnight_state}.db` | frozen 2026-03-28 | None | ~2.9 MB | index.db YES (`corp index rebuild` from vault); **ops.db NO** (immutable audit trail = history, not derivable); overnight_state semi | MEDIUM — small but ops.db history unrecoverable |
| 6 | RFP KB entries | one-off build, all mtime 2026-03-15 | `Documents/corp_data/rfp_kb/` (1,329 .md, 17 family dirs) | never moved since; **no runtime consumer** (scenarios §1.3) | None | 1.7 MB | Unclear — provenance of the build not in repo telemetry; treat as NOT regenerable | **HIGH value-density** — curated Q&A corpus, unreachable by code AND unbacked |
| 7 | Generated deliverables | Stack-B agents → `data/output/` (absent); `corp prep` → `_corp_prep/`; real decks/answers hand-made | `MyWork/10_Projects/**` (manual), `MyWork/.corp/_corp_prep` | shipped to clients via mail/SharePoint manually | None locally | included in #2 | Answers/decks NOT regenerable (operator judgment embedded) | HIGH (same disk as #2) |
| 8 | Trained models & fixtures | scripts/train_classifier | repo `models/` (git-tracked), `tests/fixtures/` | retrain on new data (script exists) | **GitHub** (private remote, pushed 2026-06-06) | ~1.3 MB | YES | LOW |
| 9 | Audit/governance docs | sessions like this one | repo `docs/audits/`, JOURNAL, ADRs | committed + pushed | **GitHub** | ~5 MB | n/a | LOW |
| 10 | Config (paths.toml, content_registry.yaml in-repo copy, naming_config, product profiles) | repo | repo `config/` (git) + **live copies in `MyWork/.corp/`** (routing_map.yaml, content_registry.yaml, template_registry) | `.corp` copies edited operationally, NOT git-tracked | repo half: GitHub; `.corp` half: none | ~10 MB (.corp) | .corp half NO | MEDIUM — the registry that actually routes lives outside the repo |

## 2. Storage & survival analysis

### 2.1 Local disk budget — top consumers (report only; nothing deleted)

| Rank | Item | Size | Disposable? |
|---|---|---|---|
| 1 | `data/_outputs/v2/` | 11.3 GB | YES — superseded extraction generation (v3 exists; vault ingested both) |
| 2 | `data/_outputs/v3/` | 6.9 GB | YES after confirming vault ingest complete (2,673 notes ingested 03-26/27) |
| 3 | `MyWork/10_Projects` | 6.6 GB | NO — active deal work |
| 4 | `MyWork/30_Reference` | 3.8 GB | NO (source library) |
| 5 | repo `.venv/` | 550 MB | YES — regenerable |
| 6 | `MyWork/00_Inbox` | 232 MB | NO — unprocessed capture backlog (75 files) |
| 7 | `MyWork/20_Workflows` | 228 MB | NO |
| 8 | `data/_outputs/golden_set/` | 107 MB | KEEP — curated review set |
| 9 | `MyWork/15_Extra_Inititives` | 89 MB | NO |
| 10 | repo `.git/` | 85 MB | NO |

Headline: **~18.7 GB (≈60% of the ecosystem's non-OneDrive footprint) is regenerable extraction/venv artifacts**; the actually-precious local data (vault 48 MB + rfp_kb 1.7 MB + ops.db 1.4 MB + .corp 10 MB) is **under 100 MB** and has zero backup.

### 2.2 OneDrive constraint map (from code + config only)

| Surface | What it does | Evidence |
|---|---|---|
| `config/paths.toml [safety]` | declares `excluded_paths = ["OneDrive - Blue Yonder"]` | `paths.toml:18-20` |
| 4 fail-closed mutation guards | resolve(strict=False) + dual substring check before any delete/move/write; raise `OneDriveSafetyError`/`ValueError` | `cleanup/disk.py::execute_plan`, `cleanup/executor.py::execute_moves`, `actions/_helpers.py::_guard_writable` (used by archive), `project/renderer.py:38-52` (ARCHITECTURE §OneDrive safety guards) |
| Reads FROM the mirror | only two sanctioned paths: `corp-ops/scripts/sync-mywork.ps1` (enumerated in `~/.claude/rules/core-invariants.md`) and the 2026-06-16 audit tool's opt-in `--include-onedrive` | core-invariants.md; JOURNAL 2026-06-16 |
| Writes TO the mirror | none anywhere; `schema/models.py:162` keeps 'onedrive'/'sharepoint' only as source-location labels | S2 trace grep: no msal/graph/office365 imports |
| Session-level | `block-onedrive` PreToolUse hook (Bash+PowerShell) at the agent-harness layer | `~/.claude/settings.json` (user gotchas 2026-06-05) |

Consequence for process design: any future "publish to team" (W4) or "archive everywhere" (D5) leg **cannot** be implemented as writes into the synced tree; it must go through a Graph API client that does not yet exist.

### 2.3 Laptop-loss thought experiment

Assumptions stated: (i) GitHub remotes survive; (ii) SharePoint/OneDrive cloud content survives; (iii) `sync-mywork.ps1` mirrors cloud→local only, so cloud-originated MyWork files are re-downloadable but locally-authored files inside MyWork have no upstream; (iv) no other backup mechanism exists (none was found in code, config, or scheduled tasks examined).

**If the machine died today:**

| Survives | Lost forever |
|---|---|
| corp-monorepo incl. this audit, models/, fixtures (GitHub `rdwornik/corp-monorepo`, private, pushed) | **ObsidianVault** — 850 notes + git history (no remote): the entire extracted knowledge base |
| Team documents that exist on SharePoint (re-download) | **corp_data/rfp_kb** — 1,329 curated RFP KB files |
| Cloud-originated MyWork mirror content | **ops.db** ingest audit trail; overnight run history; index.db (regenerable only if the vault survived — it doesn't) |
| | **Locally-authored MyWork content** — decks, RFP responses in progress, `_corp_prep` briefs, `Project_Codes.xlsm` col-M links, anything never uploaded back to SharePoint |
| | **MyWork/.corp** live routing/registry config (10 MB, not the repo copy) |
| | 00_Inbox backlog (75 files) if sourced from mail/local |

The X1 gap is therefore concrete: **everything the system was built to accumulate (vault + RFP KB) fits in <60 MB and would be a total loss**, while 18.4 GB of regenerable artifacts occupy the disk. A one-line mitigation (git remote for the vault, plus any file-level backup of `corp_data` and `.corp`) would close the highest-consequence risk in the ecosystem — noted as input for the architect; no action taken in this audit.

---

*End of Phase 4. No files moved, deleted, or written outside this deliverable.*
