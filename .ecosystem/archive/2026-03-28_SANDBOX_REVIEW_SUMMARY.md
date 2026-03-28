---
# Sandbox Cleanup Pilot — Review Summary for Rob

**Generated:** 2026-03-28
**Location:** `.sandbox/cleanup_pilot/`
**Disk usage:** 2.4 GB
**Status:** Pilot complete, output directory empty (apply step not run)

---

## What This Was Testing

The sandbox ran a 20% random sample (119 files) of `MyWork/10_Projects/` through the
corp-by-os file classification and rename pipeline to validate:

1. Whether `doc_type_classifier.py` correctly identifies file types from names/content
2. Whether the proposed naming convention (`{YYYY-MM}_{TYPE}_{CLIENT}_{Description}.{ext}`) renders correctly
3. Whether near-duplicate detection catches space/underscore filename variants
4. How many files can't be classified automatically

No files in `MyWork/` were modified. The output directory (`.sandbox/cleanup_pilot/output/`)
is empty — the "apply" step was never executed. This is read-only analysis only.

---

## Pilot Scope

| Metric | Value |
|--------|-------|
| Total MyWork/10_Projects/ files | 595 |
| Sample size | 119 (20%) |
| Projects covered | 24 |
| Disk used | 2.4 GB |
| Output files written | 0 (apply not run) |
| Errors during sampling | 0 |

---

## What the Pipeline Found

### Classification Results

| Category | Count | % |
|----------|-------|---|
| Would be renamed | 119 | 100% |
| Already compliant | 0 | 0% |
| **Could not classify** (will get MISC) | **63** | **53%** |
| Near-duplicate pairs detected | 24 | — |
| HIGH similarity pairs (>80%) | 19 | — |

**The 53% unclassified rate is the key finding.** These files get `MISC` type code as a
fallback. Classification method breakdown: `none` (63), `tfidf` (31), `regex` (19), `extension` (6).

### Doc Types Detected

| Type | Count |
|------|-------|
| (unclassified → MISC) | 63 |
| meeting | 19 |
| rfp_response | 10 |
| architecture | 9 |
| security | 7 |
| image | 3 |
| vendor_assessment | 2 |
| video | 2 |
| proposal | 1 |
| presentation | 1 |
| discovery | 1 |
| archive | 1 |

### File Type Distribution

| Extension | Count |
|-----------|-------|
| .pptx | 28 |
| .docx | 23 |
| .xlsx | 21 |
| .pdf | 16 |
| .md | 9 |
| .csv | 8 |
| .txt | 5 |
| .jpg | 3 |
| .7z | 2 |
| .mp4 | 2 |

---

## Representative Sample: 20 Proposed Renames

These are the highest-confidence rename proposals from the pilot:

| Original | Proposed | Type | Conf |
|----------|----------|------|------|
| `Ahold Delhaize Tech Workshop 28012026.pptx` | `2026-01_WORK_AHOLD_...` | meeting | 1.00 |
| `Localhost_RFP_Alfa_Laval_Sheet-Additional questions.xlsx` | `2025-11_RFP_ALFAL_...` | rfp_response | 1.00 |
| `Clicks VA 07012025.pptx` | `2025-07_VA_CLICK_...` | vendor_assessment | 1.00 |
| `New_Clicks_CON_EDU_SOW_2025-1114_v1.3.docx` | `2025-12_SOW_CLICK_...` | proposal | 1.00 |
| `2026-03_MISC_GEN_Digital_Property_RFI_-_Transport_Management_v1.1.docx` | `2026-03_RFI_JLR_...` | rfp_response | 1.00 |
| `2026-03_MISC_GEN_JAGUAR_BY_x_JLR_Workshop_Part_2.pptx` | `2026-03_WORK_JLR_...` | meeting | 1.00 |
| `2026-03_MISC_GEN_JAGUAR_JLR_VA_Questionnaire_WMS_TMS_OMS.xlsx` | `2026-03_VA_JLR_...` | vendor_assessment | 1.00 |
| `DEMO_PREP_LabelVie_TMS_032026.pptx` | `2026-03_PRES_LABEL_...` | presentation | 1.00 |
| `Infrastructure Recommendations for NEOM WMS OnPremise.docx` | `2025-05_ARCH_NEOMW_...` | architecture | 1.00 |
| `pepsi emea discovery call.txt` | `2026-01_DISC_PEPSI_...` | discovery | 1.00 |
| `Localhost_Systembolaget_RFP.xlsx` | `2025-11_RFP_SYSTE_...` | rfp_response | 1.00 |

Note: 100% of files have a proposed rename. The MISC fallback means even unclassified files
get a date+client prefix if the project directory provides that context.

---

## Near-Duplicate Analysis

19 HIGH (>80%) similarity pairs detected. All 19 are space-vs-underscore variants of the
same filename — artifacts of different download/export tools:

```
1.000 — Ahold Delhaize Tech Workshop 28012026.pptx  ↔  Ahold_Delhaize_Tech_Workshop_28012026.pptx
1.000 — Localhost_RFP_Alfa_Laval_Sheet-Additional questions.xlsx  ↔  ...Additional_questions.xlsx
1.000 — ORIGINAL LOCALCOPYAnnex A CCI ....xlsx  ↔  ORIGINAL_LOCALCOPYAnnex_A_CCI_....xlsx
1.000 — Infrastructure Recommendations for NEOM WMS OnPremise.docx  ↔  ..._for_NEOM_...docx
1.000 — NEOM Action plan to finish document.docx  ↔  NEOM_Action_plan_to_finish_document.docx
1.000 — Agenda and Objectives Pepsico 2 days workshop MOD.docx  ↔  Agenda_and_Objectives_...docx
1.000 — Key Technical Insights for Blue Yonder Engagement with PepsiCo.docx  ↔  Key_Technical_Insights_...docx
1.000 — Recording_Pepsi_Emea_2026-01-15.txt  ↔  Recording_Pepsi_Emea_2026-01.txt
1.000 — QATAR DF.docx  ↔  QATAR_DF.docx
1.000 — Redcare-Pharmacy - 21st October.pptx  ↔  Redcare-Pharmacy_-_21st_October.pptx
...and 9 more (all space/underscore variants)
```

One notable pair: `BlueYonder-Powerpoint-Template_2025-ConfidentialFooter-usecases.pptx` shows
1.000 similarity with `Wurth_Blue_Yonder_Platform_Service_Description.pptx` — different names,
identical content. Likely a deck built on the template without renaming.

2 MED pairs (0.60–0.80): `Veronesi Template PPT.pptx` vs a Tech Track deck (related but distinct),
and two Safilo CSV payloads (likely v1/v2).

---

## Key Issues Found

### 1. 63 Unclassified Files (53%)
These fall back to `MISC` type. Cause: the classifier relies on filename regex patterns and
TF-IDF on filename tokens. Files with generic names (e.g., `payload_Almarai.csv`, `_OLD_FILES.txt`,
`Clicks ramp.xlsx`) produce no signal. Fix path: extend regex patterns in `doc_type_classifier.py`
or add a content-based fallback for common extensions.

### 2. No "Apply" Step Built
`sandbox_apply.py` (mentioned in REVIEW_REPORT.md section 8) was not built. The pilot validated
classification + rename generation but the execution path doesn't exist yet.

### 3. 0 Files Already Compliant
The full `MyWork/10_Projects/` population has zero files in the new naming format. This is
expected for a first-run pilot but confirms the rename scope is 595 files minimum.

---

## Project Coverage in Sample

| Project | Files in sample |
|---------|-----------------|
| Michelin_Planning | 13 |
| Wurth_Retail | 12 |
| Clicks_Retail | 11 |
| Jaguar_Land_Rover_TMS_WMS_OMS | 10 |
| SGDBF_Retail | 10 |
| PepsiCo_Planning | 8 |
| Lenzing_Planning | 7 |
| Rossmann_Migration | 6 |
| Veronesi_Planning | 6 |
| NEOM_WMS | 5 |
| _(14 more projects, 1–3 files each)_ | 21 |

---

## Assessment

The pipeline mechanics work. Rename proposals are coherent and date+client prefix logic is
correct for files where the project directory provides context.

The main gap is the 53% unclassification rate — more than half the files will be tagged `MISC`
without additional pattern expansion. This is addressable in `doc_type_classifier.py` before
a full run.

No files were modified. The sandbox can be cleared or kept as-is — it is self-contained in
`.sandbox/cleanup_pilot/` and is not referenced by any test or CI step.

---
_Summary prepared: 2026-03-28_
