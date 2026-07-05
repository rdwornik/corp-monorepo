# Deep Audit F — MyWork Estate & Naming (Wave 2)

**Date:** 2026-07-05 · **Branch:** `docs/deep-mywork` · **Mode:** read-only measurement
**Method:** metadata scan (names, sizes, mtimes, extensions) of local `C:/Users/1028120/Documents/MyWork` (`config/paths.toml:7`); file contents opened ONLY for Step-3 sampling (2 files in `15_Extra_Inititives`) plus one SHA-256 pair-hash for the Step-5 divergence check. **No OneDrive path traversed**; mirror figures cited from `docs/audits/2026-06-16-current-state-architecture-audit.md`. Nothing renamed, moved, deleted, or written outside `docs/audits/`.
**Baselines:** 2026-07-05 functional audit (Phases 1–5, merged `2753601`), 2026-06-16 current-state audit, 2026-06-21 foundation review. Authoritative vocabularies: `src/corp/schema/folder_names.py` (7 zones + `.corp`), `config/naming_config.yaml` (22 type codes, 32 client aliases), ADR-14, ADR-24.

**One-line verdict: the estate is a 2,236-file / ~10.2 GB working tree in which ADR-14 penetration is 10 files (0.4% — all March `MISC_GEN` fallback renames), the declared hot zone (20_Workflows) is cold while the real production studio lives inside 30_Reference/Training/Warsaw, 10_Projects carries 196 byte-identical space↔underscore twin pairs (~756 MB), 90_Archive is an empty shell, and the only actively maintained registry (`Project_Codes.xlsm`, mtime 2026-06-19) sits unbacked in 30_Reference.**

---

## 1. Zone-by-zone functional census

Scan of 2026-07-05. "Declared" = `folder_names.py` + ADR-24. Root-level reality: the 7 canonical zones + `.corp` + `.claude` + rogue `15_Extra_Inititives` + loose `CLAUDE.md`/`README.md` (confirms foundation review S3).

| Zone | Files | Dirs | Size | Oldest | Median | Newest | Dominant types |
|---|---:|---:|---:|---|---|---|---|
| 00_Inbox | 75 | 14 | 221 MB | 2025-01-29 | 2026-02-21 | 2026-04-10 | .xlsx 37, .pdf 15, .docx 7 |
| 10_Projects | 620 | 73 | 6.11 GB | 2020-09-30 | 2025-04-14 | 2026-07-03 | .pptx 135, .xlsx 112, .pdf 111 |
| 20_Workflows | 30 | 5 | 217 MB | 2026-03-30 | 2026-03-30 | 2026-05-05 | .pptx 19, .docx 4 |
| 30_Reference | 1,356 | 81 | 3.54 GB | 2025-12-31 | 2026-04-28 | **2026-07-05** | .png 1,116; by bytes: .mp4 7 files/2.0 GB |
| 70_Admin | 17 | 8 | 0.8 MB | 2025-12-16 | 2026-03-03 | 2026-03-26 | .png 8, .pdf 4 |
| 80_Compliance | 29 | 5 | 13.7 MB | 2024-06-05 | 2026-01-15 | 2026-04-24 | .pdf 24 |
| 90_Archive | **0** | **0** | 0 | — | — | — | — |
| `.corp` | 46 | 6 | 9.4 MB | 2026-02-19 | 2026-03-14 | 2026-03-30 | .md 20, .jsonl 10, .json 9 |
| 15_Extra_Inititives | 63 | 9 | 84.4 MB | 2026-03-10 | 2026-04-01 | 2026-05-15 | .png 15, .py 13, .pptx 10 |
| **Total** | **2,236** | | **~10.2 GB** | | | | |

### What each zone is REALLY used for

- **00_Inbox — a frozen capture backlog, not an intake.** Declared: temporary intake, magistrala entry point, with `_Staging`/`_Unmatched`/`_quarantine` sub-locations (`folder_names.py:23-25`). Reality: newest file 2026-04-10 (inflow stopped; matches W1 DORMANT); an **undeclared `raw/`** (40 files, 199 MB) and **undeclared `_Review/`**; declared `_Staging` and `_quarantine` **do not exist** (`_Unmatched` exists, empty). 50 of 75 files are SharePoint-named RFP responses ("Blue Yonder Response to … RFP …") — i.e. the inbox is currently a **style-corpus parking lot** (synthesis open question #2), not a routing queue. Triage tooling relics at root (`_triage_log.jsonl` 0 bytes, `_triage_schema.yaml`, `folder_manifest.yaml`, all 2026-03-11).
- **10_Projects — active deal work + de-facto archive + duplicate churn.** Declared: active client work in `{Client}_{Product}/`. Reality: 29 project folders, and the shape matches — but (a) 84% of bytes sit in 3 projects whose newest file is March (Clicks 3.39 GB/462 files newest 03-11, Wurth 1.06 GB, Michelin 0.8 GB) — **stale projects are archived in place** because 90_Archive is unused; (b) oldest file 2020-09-30 (Clicks history imported wholesale); (c) **196 same-directory space↔underscore twin pairs, byte-identical sizes, ~756 MB wasted** (e.g. `Ahold Delhaize Tech Workshop 28012026.pptx` + `Ahold_Delhaize_Tech_Workshop_28012026.pptx`) — the residue of a half-applied normalization pass; (d) 3 Office `~$` lock files; (e) one empty shell (`Penguin_Random_House_WMS_TMS`, 0 files). Genuinely alive: `Unilever_AnR` (07-03), `Tata_Steel_J2CC` (06-24), `SGDBF_Retail` (05-19), `Wickes - J2CC` (05-14), `Essity_TMS` (05-13), `Veronesi_Planning` (05-05).
- **20_Workflows — the declared HOT ZONE is cold.** Declared (ADR-24): "HOT ZONE: master decks, demo scripts, tech presentations, workshop kits"; revisit-signal at >75 files. Reality: **30 files**, `Master_Deck/` holds **3 files / 9.4 MB**, median mtime 2026-03-30 (the restructure day — most content hasn't been touched since it was moved here), newest 05-05. The function this zone declares is actually performed inside 30_Reference/Warsaw (below). Verdict: **purpose inverted — a display case, not a workshop.**
- **30_Reference — declared "evergreen knowledge", actually the live production studio.** 1,302 of 1,356 files (96%) and 2.87 GB sit in **`Training/2026_Platform_Training_Warsaw/`** — not reference material but an active build workspace: 19 generator `.py` scripts (deck builders, plus `Cortina/_build_response*.py`, `_rfp_retrieve.py`, `_verify*.py` — **RFP-response production by script**), `_PPTX_TEMPLATE_KIT/` (06-02), `_extracted/` (1,027 hand-extraction artifacts — the `slide_NN.png`/pages sprawl), `_extra/` + Essity workshop dir (2.3 GB of .mp4/.wav recordings), per-client build dirs (Cortina, wurth, unilever, tsuk, comedy), participant admin, and **personal H1_FY26 self-review decks**. `WORKSPACE_MASTER_REFERENCE.md` modified **today** (2026-07-05) — this is where W3/deck work actually happens. The remaining ~54 files are true reference (Branding 484 MB, RFP_Library 214 MB, Products, Architecture, Competition) — plus two loose root files: `Platform_Usage_by_Product.xlsx` and **`Project_Codes.xlsm` (mtime 2026-06-19 — the estate's only actively-maintained registry, living in the wrong zone and unbacked)**.
- **70_Admin — matches purpose, trivially small.** Benefits claims, Workday goals, invoices. 17 files, 0.8 MB, dormant since 03-26.
- **80_Compliance — matches purpose.** 27 SOC/ISO certificates and reports under `Certificates/` (corporate filenames, self-describing), oldest 2024. Quietly accreting (04-24).
- **90_Archive — an empty shell; the archive function never ran.** 0 files, 0 dirs. **Discrepancy:** JOURNAL 2026-03-29 records "moved 9 stale projects to archive" — nothing is there now, and both the 2026-06-16 audit and Phase-4 lifecycle found it empty. Where those 9 projects went is not resolvable read-only; needs operator memory (candidates: subsequent cleanup, move into the OneDrive mirror, or reversal).
- **`.corp` — March incident-forensics freezer + live-ish config, frozen 2026-03-30.** 4 root configs (see §5), `.audit/` = 20 forensic/migration reports (03-12→03-24, incl. `template_rfp_audit.md`, `migration_log.md`), `.logs/` = overnight logs + **`cleanup_log.jsonl` (2.16 MB, mtime 2026-03-14 — the incident day)** + `moves.yaml`, `.scripts/` = 3 estate-side .ps1 scanners, `_corp_prep/` = 2 JLR briefs. Note the **double-nested `.corp/.logs/.corp/`** — relic of the `90_System/.corp` → `.corp` flattening. Zero backup (X1).
- **15_Extra_Inititives — see §3.** Rogue, misspelled, 63 files, newest 05-15.

**Zone-purpose drift flags:** (1) deck/RFP production in 30_Reference instead of 20_Workflows; (2) archive-in-place inside 10_Projects while 90_Archive is empty; (3) `Project_Codes.xlsm` (admin registry) in 30_Reference; (4) personal self-review decks (70_Admin material) inside Warsaw; (5) Inbox sub-location contract (declared vs disk) broken both directions; (6) code (`.py`) in 30_Reference and 15_Extra — no declared home for workspace-class code+deck initiatives anywhere in the taxonomy.

---

## 2. Naming conformance, measured (the kernel baseline)

Regex built from `config/naming_config.yaml`: `^{YYYY}-{MM}_{22 type codes}_{32 alias codes + GEN}_{Desc}.{ext}` applied to every filename in each zone.

| Zone | Files | ADR-14 conforming | % | Bar |
|---|---:|---:|---:|---|
| 00_Inbox | 75 | 0 | 0.0% | RED |
| 10_Projects | 620 | 10 | 1.6% | RED |
| 20_Workflows | 30 | 0 | 0.0% | RED |
| 30_Reference | 1,356 | 0 | 0.0% | RED |
| 70_Admin | 17 | 0 | 0.0% | RED |
| 80_Compliance | 29 | 0 | 0.0% | RED |
| 90_Archive | 0 | — | n/a | — |
| `.corp` | 46 | 0 | 0.0% | RED |
| 15_Extra_Inititives | 63 | 0 | 0.0% | RED |
| **Estate** | **2,236** | **10** | **0.4%** | **RED** |

Two qualifiers that matter for the kernel:

1. **All 10 conforming files are `2026-03_MISC_GEN_*`** — fallback type + fallback client from the March ingest runs (e.g. `2026-03_MISC_GEN_JAGUAR_Blue_Yonder_Overview_for_JLR.pptx`, which even embeds the client in the description while coding it GEN). **Organic ADR-14 adoption is zero**; the convention exists only where the renamer ran, and where it ran it produced fallbacks, not taxonomy.
2. Excluding machine-owned names (tool artifacts + config/data files, 1,241 files), the **document-only baseline is 10/995 = 1.0%**.

The 2026-06-16 audit's "44% match no clean convention, 5–6 coexist" is refined here to **six measured conventions plus ADR-14**:

| # | Convention | Example | Estate share | Where it dominates |
|---|---|---|---:|---|
| N1 | Tool-generated artifact names | `slide_01.png`, `page_003.png` | 1,114 (49.8%) | 30_Reference (Warsaw `_extracted/`, previews) |
| N2 | Underscored_TitleCase (no date/type grammar) | `Ahold_Delhaize_Tech_Workshop_28012026.pdf` | 611 (27.3%) | 20_Workflows 97%, 10_Projects 57%, 80_Compliance 55%, 15_Extra 59% |
| N3 | SharePoint-native natural language (spaces) | `Blue Yonder Response to Alfa Laval RFP November 2025.docx` | 349 (15.6%) | 00_Inbox 67%, 10_Projects 37% |
| N4 | Machine lowercase (config/data/scripts) | `routing_map.yaml`, `bydm_tariff1008482_entity.csv` | 127 (5.7%) | `.corp` 96% |
| N5 | Date-first `YYYYMMDD` | `20251003 Clicks A&R Consolidated Pricing Calculator v2025_09_a.xlsx` | 12 (0.5%) | Clicks only |
| N6 | Type-first v1 relics (ADR-10 era) | `RFP_Database_AIML.xlsx`, `DEMO_PREP_LabelVie_TMS_032026.pptx` | 13 (0.6%) | RFP_Library databases |
| — | **ADR-14 v2** | `2026-03_MISC_GEN_…` | **10 (0.4%)** | 10_Projects (March ingest only) |

N2 and N3 are largely the **same files twice**: the 196 equal-size same-directory twin pairs in 10_Projects are an N3 original + N2 underscore copy sitting side by side (~756 MB redundant). Any conformance-lift plan that "renames spaces to underscores" has already been half-run once and left this residue — evidence for the foundation rule: **route new, never bulk-rename old.**

---

## 3. `15_Extra_Inititives` disposition evidence

63 files / 84.4 MB / 9 dirs; window 2026-03-10 → 2026-05-15 (all post-restructure — this zone was *created by use* after Council #24 removed `20_Extra_Initiatives` from the spec, ADR-24 "Removed from spec"). Contents-sampling used (permitted): `Karthik_Revlon_Databrick_Demo/README.md` and `_audit/WORKSPACE_AUDIT.md`.

| Subdir | Files | Size | Newest | What it is (evidence) |
|---|---:|---:|---|---|
| `Karthik_Revlon_Databrick_Demo/` | 57 | 45.7 MB | 2026-04-28 | **Self-contained, demo-ready integration workspace** (Rob + Karthik, Mar–Apr): 13 `.py` notebooks/generators, 6 deck versions (`Databricks_BY_Integration_Options` v3→v6+final), BY template extract kit, realm configs, 14 solution screenshots, own `CLAUDE.md`, `README.md` (= handoff doc), `.vscode/`, and its own audit (`WORKSPACE_AUDIT.md`, 2026-04-28: "production-ready pre-sales demo… four validated integration patterns"). Client = **Revlon (`REVL` is in the alias vocabulary)**. ⚠️ That audit also flags, and this scan confirms: **plaintext credentials on disk** (`databricks.token`, and a live PAT + OAuth client ids inside `README.md` — values not reproduced here). |
| `MBO/` | 3 | 32.6 MB | 2026-05-15 | 3 platform-overview decks (`MBO_BYDM_BYDMR_Steaming_to_Buk_v1.pptx`, `MBO_Databricks_BY_Integration_Options.pptx`, `MBO_Platform_Overview_Essity_v1.pptx`). Two are **derivatives of the Karthik deck line**; one also exists (different size/version) at Warsaw root — cross-zone version fork. Newest content in the zone. |
| `SCA time calendar/` | 3 | 6.0 MB | 2026-04-02 | Time-entry training deck (pptx+pdf) + `transcript.docx` — **internal admin training**, unrelated to the other two. |

**Assessment (decision is the operator's):** this is **not one coherent initiative** — it is three unrelated items — but they share one property the taxonomy cannot express: **internal, non-deal, workspace-shaped work** (exactly the species of the Warsaw folder in 30_Reference). Two defensible dispositions:

- **(A) Legitimize as `15_Initiatives` (spelling fixed), defined as the internal/non-deal workspace zone.** Pro: gives Warsaw-class workspaces a declared home too (fixes drift flag #1/#6); honors ADR-24's access-frequency logic (these are weekly-touch items). Con: reverses an explicit Council #24 removal; needs `folder_names.py` + routing + `SCAN_SKIP` decisions.
- **(B) Migrate and delete the zone:**

| Item | Maps to | Rationale | Friction |
|---|---|---|---|
| `Karthik_Revlon_Databrick_Demo/` | `10_Projects/Revlon_Databricks_Demo/` (as an atomic workspace) | Client-attributed (REVL), deal-adjacent demo | It's a *workspace* (code+creds+decks); 10_Projects currently holds only documents. Credential cleanup first. |
| `MBO/` decks | `20_Workflows/Technical_Presentations/` | They ARE tech presentations — the declared hot-zone content | Version-fork with Warsaw copy must be reconciled first |
| `SCA time calendar/` | `70_Admin/` (or 30_Reference/Training if kept as training material) | Internal admin training | none |

Either way, **F0 must first revoke/relocate the plaintext Databricks PAT** — that seed does not wait for the disposition decision.

---

## 4. Template inventory — where templates ACTUALLY live

Search: every `.potx/.dotx/.xltx` + `*template*`/`*master*` names, all zones. **Finding: no `.dotx`/`.xltx` anywhere; exactly one `.potx`; no template lives in a declared template home, because no declared template home exists** (ADR-24 removed `30_Templates`; nothing replaced it).

| Template asset | Lives in | Size / mtime | Status |
|---|---|---|---|
| `BlueYonder-Powerpoint-Template_2025-RestrictedFooter-usecases.potx` | `10_Projects/Wurth_Retail/` | **371.7 MB**, 2025-06-15 | The only real PowerPoint template file in the estate — the official corporate deck template, **buried in one client's project folder**, plus a 364 MB `.7z` sibling (03-11) |
| `BlueYonder-Powerpoint-Template 2025-ConfidentialFooter-usecases.pptx` (+underscore twin) | `10_Projects/Wurth_Retail/` | 1.9 MB ×2, 2026-01-21 | Confidential-footer variant, duplicated by the twin-pair problem |
| `_PPTX_TEMPLATE_KIT/` (`_BY_template_clean.pptx` 8.2 MB + `00_MASTER_PROMPT.md`) | `30_Reference/Training/…Warsaw/` | 2026-06-02 | **The current, actively-used template** — a generator kit (template + master prompt), newest of the `_BY_template_clean` line |
| `_BY_template_clean.pptx` (2 older copies) | Warsaw root; `15_Extra/Karthik…/` | 6.5 MB each, 2026-03-31 | Stale ancestors of the kit (identical size to each other) |
| `[Internal]_My_Technology_Template.docx` | `30_Reference/RFP_Library/Template_Word/` | 0.76 MB, 2026-03-30 | The only Word template; only template in anything resembling a declared home |
| `Veronesi Template PPT.pptx` (+underscore twin) | `10_Projects/Veronesi_Planning/` | **45.9 MB ×2**, 2025-12-12 | Client-branded template, twin-pair duplicated |
| `Clicks-Group-PPT-Template.pptx` ×2 | two `10_Projects/Clicks_Retail/` subdirs | 7.5 MB each, 2023 | Stale client templates |
| `Wurth_Cloud_Approval_Application_Template.xlsx` | `10_Projects/Wurth_Retail/RFI/` | 2025-07-21 | Client form, not a BY template |
| (`RFP_Database_Master.xlsx`, `WMS_RFP_Database_Master.xlsx`) | `30_Reference/RFP_Library/Databases/` | 2026-03-30 | "Master" **data**, matched by search, not templates |

**Registry ground truth:** `src/corp/template_manager.py:3,75` scans `30_Templates/` and maintains `90_System/template_registry.yaml` — **both zones are phantoms** (`30_Templates` never existed on disk, ADR-24 removed it from spec; `90_System` was deleted 2026-03-29), and **no `template_registry.yaml` exists anywhere in MyWork** (full `.corp` listing, §5 — the Phase-4 lifecycle table's "template_registry" in `.corp` is not on disk; only `.corp/.audit/template_rfp_audit.md` is). The template *manager* is therefore 100% disconnected from where templates actually live. This is the join point with Audit E's template_manager finding (Audit E unmerged at time of writing — evidence here is first-hand: `template_manager.py`, `tests/test_template_manager.py:109`).

**Current-vs-stale verdict:** current = Warsaw `_PPTX_TEMPLATE_KIT` (deck generation) + the Wurth-buried `.potx` (official corporate skeleton). Stale = the two March `_BY_template_clean` copies, 2023 Clicks templates, and every twin duplicate. The "Warsaw-folder chaos" from the deck brief is confirmed as: the current template SSOT is an undeclared subdirectory of a training workspace inside a reference zone.

---

## 5. Live-config (`.corp`) vs repo-config split — the estate facts

Full `.corp` inventory (46 files, 9.4 MB, frozen 2026-03-30) vs repo `config/`:

| `.corp` item | mtime | Repo twin | Estate fact |
|---|---|---|---|
| `content_registry.yaml` (21,376 B) | 2026-03-23 | `config/content_registry.yaml` (4,775 B, last commit 2026-03-29 = the consolidation move `572d7a6`) | **DIVERGED** — SHA-256 differs; live copy is 4.5× the repo copy. Two authorities exist; which one code reads is Audit B's question — the estate fact is a split brain, both halves stale since March. |
| `routing_map.yaml` (2,352 B) | 2026-03-30 | **none** | Orphan live config — no repo twin, no git history, no backup. (Phase-5 synthesis #10 flags its content as phantom-target dead config.) |
| `config.json` (392 B) | 2026-03-10 | **none** | Orphan machine config |
| `solution_matrix.json` (10 KB) | 2026-02-19 | **none** | Orphan — oldest file in `.corp`, predates the restructure |
| `.audit/` — 20 files, 7.2 MB | 03-12 → 03-24 | n/a | March forensic corpus: `full_scan.json` (2.3 MB), `preflight_manifest.json` (3.8 MB), migration/restructure/cleanup logs, `template_rfp_audit.md`, `mywork_audit*` — unique operational history |
| `.logs/` — 17 files, 2.1 MB | 03-12 → 03-14 | n/a | **`cleanup_log.jsonl` (2.16 MB, mtime 2026-03-14 = the OneDrive incident day)** + `moves.yaml` + overnight logs — the incident forensics themselves; also the `.logs/.corp/` double-nesting relic |
| `.scripts/` — 3 .ps1 | 03-16 → 03-21 | none (repo `scripts/` has different tooling) | Estate-side scanners (`ecosystem_scan`, `extraction_audit`, `preflight_scan`) — orphan code |
| `_corp_prep/` — 2 briefs | 2026-03-26 | n/a | Generated deliverables (JLR) |

**What the foundation must treat as precious operational state (zero backup today, per lifecycle X1):** the four root configs (the live registry half of the split brain + 3 orphans), the incident forensics in `.logs/`, the `.audit/` history — **plus, from §1, `30_Reference/Project_Codes.xlsm` (mtime 2026-06-19, the only registry still being edited) which the lifecycle audit's precious-set should explicitly include.** Everything else in the estate is either cloud-recoverable or regenerable; this set (~10 MB + 130 KB) is not.

---

## 6. Addressing-kernel inputs (for the architect)

**The rule this must honor (foundation brief, confirmed by measurement):** *route new material, never reorganize old; validator-enforced, near-zero maintenance.* The estate supplies the proof: the one bulk-normalization attempt left 196 duplicate pairs (§2), ADR-14 itself says "migrated on-touch (no bulk rename)", and the forward-only gotcha is already a learned rule. The kernel's conformance metric must therefore be **cohort-based (files born after kernel activation)**, measured against this audit's 0.4%/1.0% baseline — not against the legacy stock.

### Per zone: what a deterministic address must encode

| Zone | Address must encode | Current naming already suffices? | Where the kernel adds value |
|---|---|---|---|
| 00_Inbox | disposition state (route-target, triage status), provenance | No — but names are transient here | HIGH — routing is the zone's entire purpose; address = pipeline state, not filename |
| 10_Projects | canonical client (alias), engagement/product, doc role, date | Folder level: partially (`{Client}_{Product}` mostly holds). File level: no | HIGH — client canonicalization + role/date on *new* files; twin-dedup is a precondition (else every address has two referents) |
| 20_Workflows | type + **currency** (master vs superseded) | Subfolder structure suffices; volume tiny | MEDIUM — version/currency state, not renaming |
| 30_Reference | **liveness class**: evergreen doc vs workspace | Evergreen ~54 files: corporate names self-describe. Warsaw: no | HIGH — but as a **workspace carve-out**: address the workspace as one atomic unit (like a repo), never its 1,301 internal tool-named files |
| 70_Admin | nothing beyond zone | Yes (17 files) | NONE |
| 80_Compliance | doc class + year + audit scope | Yes — SOC/ISO corporate names already encode it | LOW — leave as-is; validator whitelist |
| 90_Archive | provenance (origin zone/project) + close date | Zone is empty — design-time freedom | Design the address grammar BEFORE the archive trigger (D5) first populates it |
| `.corp` | machine-owned | Yes | NONE — declared exempt zone |
| 15_Extra | workspace-class atomic unit | n/a | Pending §3 disposition |

**Estate-wide implication:** 49.8% of files are tool-generated artifact names (N1) and 5.7% machine names (N4) — **the kernel should govern the ~1,000 human-document files and explicitly exempt machine/workspace-owned names**, or its conformance metric drowns in noise it should never touch.

### Project-folder ↔ Project_Codes / vocabulary mismatch classes

(From the Step-1 sample of all 29 project folders vs `naming_config.yaml` aliases; `Project_Codes.xlsm` itself not opened — binary, and its column contract is Audit E's scope, unmerged at time of writing.)

| Class | Pattern | Instances (sample) |
|---|---|---|
| M1 | Folder uses full client name, vocabulary uses alias | `Jaguar_Land_Rover_TMS_WMS_OMS` (JLR), `Ahold_Delhaize_CatMan` (AHOLD), `Alfa_Laval_Planning` (ALFAL), `Penguin_Random_House_WMS_TMS` (PENGU), `Stellantis_Mopar_E2E` (STELL) |
| M2 | Client absent from the 32-alias vocabulary entirely | `Unilever_AnR`, `Wickes - J2CC`, `Tata_Steel_J2CC`, `Essity_TMS` — **4 of 29 folders (14%), all recently active**; Warsaw adds Cortina/tsuk |
| M3 | Format outlier breaking `{Client}_{Product}` | `Wickes - J2CC` (spaces + hyphen) |
| M4 | Multi-product compound where the grammar expects one product | `…TMS_WMS_OMS`, `…WMS_TMS`, `…_E2E` |
| M5 | Case/verbatim drift vs lowercase `project_id` convention | all folders TitleCase; `com new` creates verbatim case (known gotcha) |
| M6 | Structural noise | empty shell folder (Penguin, 0 files); `folder_manifest.yaml` relics at zone roots; `~$` lock files |

**Where naming already suffices vs kernel value, summarized:** leave 80_Compliance, 70_Admin, `.corp`, and workspace interiors alone (validator whitelist); spend the kernel on (i) inbox routing state, (ii) new-file addressing in 10_Projects/20_Workflows with a **completed alias vocabulary** (M2 is a hard blocker — 14% of active clients are unaddressable today), (iii) the workspace-as-atomic-unit concept, and (iv) the 90_Archive grammar before D5 fills it.

---

## 7. Backlog-seed table (F0 inputs)

| Seed | Goal (functional) | Evidence | Depends on | Size gut-feel | Decision required first? |
|---|---|---|---|---|---|
| F-1 Precious-set backup | Off-machine copy of `.corp` (4 configs + forensics) **+ `Project_Codes.xlsm`** + vault/rfp_kb (extends X1) | §5; lifecycle §2.3 | — | S | No — highest consequence/effort ratio, already operator-flagged |
| F-2 Credential revocation | Revoke/rotate the Databricks PAT; remove `databricks.token` + creds from `15_Extra` README | §3 (workspace's own audit flagged it 04-28) | — | S | No (revocation); file removal = operator confirm |
| F-3 Twin-pair dedup | Retire 196 byte-identical space↔underscore duplicates (~756 MB) in 10_Projects | §2 | F-1 | S–M | **YES** — deletions; verify-hash-then-remove plan per pair |
| F-4 `15_Extra` disposition | Legitimize as `15_Initiatives` vs migrate per §3 table | §3 | F-2 | S | **YES** — operator ruling (reverses/upholds Council #24) |
| F-5 Workspace-class concept | Declare "workspace" as an addressable atomic unit (Warsaw, Karthik); exempt interiors from naming | §1, §6 | F-4 | M | **YES** — taxonomy addition |
| F-6 Template SSOT | One declared template home; rescue the 371 MB `.potx` from `Wurth_Retail`; retire stale `_BY_template_clean` copies; fix or kill `template_manager.py` phantom paths | §4 | F-5 | M | **YES** — home choice + template_manager fix-vs-kill (join Audit E) |
| F-7 Inbox contract repair | Align `folder_names.py` sub-locations with disk (`_Staging`/`_quarantine` phantom; `raw/`, `_Review` undeclared) before W1 restart | §1 | — | S | No — code-side truth fix |
| F-8 Registry split-brain | Resolve `content_registry.yaml` divergence (repo 4.8 KB vs live 21.4 KB) to one authority | §5 | Audit B's consumption verdict | S | **YES** — which half is truth |
| F-9 Alias vocabulary completion | Add Unilever, Wickes, Tata Steel, Essity (+ Warsaw clients) to `naming_config.yaml`; define folder↔alias contract (M1–M5) | §6 | — | S | No — additive config |
| F-10 Kernel conformance policy | Adopt cohort-based conformance metric vs this baseline (0.4% all / 1.0% docs-only); validator scope = new material + exempt zones | §2, §6 | F-4–F-9 | M | **YES** — the F0 kernel decision itself |
| F-11 Archive activation | Resolve the 90_Archive JOURNAL discrepancy (9 projects "moved" 03-29, zone empty); design archive address grammar + D5 trigger; then archive the 3 stale giants in 10_Projects | §1, §6 | F-10 | M | **YES** — operator memory + D5 design |

---

*Read-only discipline held: sole writes are this file and its HTML sibling. OneDrive untouched; mirror figures by citation only.*
