---
# Phase 4 — Pending Items Resolution Report

**Date:** 2026-03-28
**Branch:** chore/phase4-pending-cleanup-2026-03-28
**Predecessor:** Phase 3 (ADR-22, .ecosystem/ governance, docs/ date-prefixing) — merged to main at 063f184

---

## Item 1: 01_Product_Docs v2 vs v3 Per-Note Quality Comparison

### Background

Both `_outputs/v2/source_library/01_Product_Docs/` and `_outputs/v3/source_library/01_Product_Docs/`
contain exactly 36 extraction JSONs from the same 36 source documents. All 36 sources appear in
both versions — there are no v2-only or v3-only sources. v2 was produced by CKE v0.4.0/v0.5.0;
v3 by the same version range (both use schema_version=2).

### Comparison Methodology

Matching key: `source_file` basename (stem). Metrics compared per note:
- `fact_count` (len of facts array)
- `topics` count (what earlier notes called "tags")
- `products` count
- `domains` count
- `people` count

No `quality_score` field exists in either version (field not present in either v2 or v3 JSONs).
No `provenance`/`source_hash` field exists in either version at this schema level.

Winner declared by: fact_count primary; topics+products as tiebreaker.

### Results

| Source (stem) | v2 facts | v3 facts | v2 topics | v3 topics | v2 prod | v3 prod | Winner |
|---------------|----------|----------|-----------|-----------|---------|---------|--------|
| 2023_March_BY_WMS_HWSizing_ILS | 20 | 20 | 8 | 8 | 2 | 3 | v3 |
| ARB_Planning_Architecture_Reivew_(monthly) | 5 | 9 | 6 | 5 | 3 | 3 | v3 |
| ARB_Review_-_MDAP_as_a_Service_(MaaS) | 8 | 9 | 6 | 4 | 4 | 3 | v3 |
| Annex_7_-_TEMP_DSI_2481_Convention_Cybersécurité | 30 | 30 | 8 | 8 | 0 | 0 | v3 |
| BYPlatform-Architecture | 49 | 40 | 8 | 8 | 4 | 4 | **v2** |
| BlueYonder_StandardEntities | 41 | 77 | 8 | 8 | 3 | 3 | v3 |
| Blue_Yonder_&_Snowflake_Data_Sharing_&_Architecture | 15 | 9 | 8 | 8 | 4 | 4 | **v2** |
| Blue_Yonder_-_SAP_Template_2 | 38 | 34 | 8 | 8 | 3 | 3 | **v2** |
| Blue_Yonder_Brand_Guidelines_2025.1.1 | 35 | 36 | 8 | 8 | 2 | 2 | v3 |
| Blue_Yonder_Warehouse_Management_Architecture_v2 | 32 | 30 | 8 | 8 | 2 | 3 | **v2** |
| Cognitive_Demand_Data_Requirements | 28 | 27 | 4 | 5 | 1 | 2 | **v2** |
| DMS_-_Ingestion_Service | 25 | 25 | 6 | 6 | 2 | 1 | tie |
| Data_Requirements | 10 | 13 | 7 | 6 | 4 | 3 | v3 |
| Deep_Meta_Learning | 8 | 15 | 6 | 6 | 4 | 2 | v3 |
| Diagram_WMS_Integration_2026-01 | 1 | 1 | 4 | 3 | 2 | 1 | tie |
| Enterprise_Data_Orchestration_Pitch_Deck | 5 | 21 | 8 | 7 | 4 | 2 | v3 |
| Episode_1_-_Platform_Overview_and_Foundation | 35 | 33 | 8 | 8 | 4 | 4 | **v2** |
| Gabriel__Rey_CB-_Interop | 7 | 12 | 8 | 8 | 4 | 4 | v3 |
| Generic_Cognitive_Planning_Reference_Material | 47 | 11 | 8 | 8 | 4 | 4 | **v2** |
| KYP_'23_Spring_Edition,_EP_#1_-_Platform_Overview | 66 | 50 | 8 | 8 | 4 | 4 | **v2** |
| KYP_'23_Spring_Edition,_EP_#2_-_Data_Services | 30 | 29 | 8 | 8 | 4 | 4 | **v2** |
| LifeScience_session1v2 | 7 | **0** | 8 | 0 | 4 | 0 | **v2** |
| MachineLearning_DemandEdge_Reality | 10 | 15 | 7 | 5 | 4 | 3 | v3 |
| Noatum_Tech_presentation_27oct2023 | 41 | 41 | 8 | 8 | 4 | 4 | v3 |
| Oracle_Mapping_Matrix | 35 | 31 | 8 | 8 | 4 | 3 | **v2** |
| Platform_Editedv2 | 10 | **0** | 8 | 0 | 4 | 0 | **v2** |
| Platform_Usage_by_Product | 23 | 35 | 8 | 8 | 4 | 4 | v3 |
| Platform_and_Cognitive_-_High_Level_Architecture | 10 | 7 | 8 | 5 | 4 | 4 | **v2** |
| SAP_Mapping_Matrix | 40 | 40 | 8 | 8 | 2 | 2 | v3 |
| SAP_Mapping_Matrix_2 | 51 | 62 | 8 | 8 | 4 | 4 | v3 |
| Security_Slides_Edited | 14 | 14 | 4 | 4 | 1 | 1 | v3 |
| WFM_Requerimientos_a_cumplimentar_English_Translation | 64 | 54 | 8 | 8 | 2 | 2 | **v2** |
| WMS_-_PDC_-_Reference_Document | 20 | 20 | 4 | 5 | 2 | 2 | v3 |
| WMS_Best_Practices_Guide | 0 | 0 | 0 | 0 | 0 | 0 | v3 (tiebreak) |
| index | 0 | 0 | 0 | 0 | 0 | 0 | v3 (tiebreak) |
| synthesis | 0 | 0 | 0 | 0 | 0 | 0 | v3 (tiebreak) |

### Summary

| Metric | V2 | V3 |
|--------|----|----|
| Wins | 14 | 20 |
| Ties | 2 | 2 |
| Total facts | 860 | 850 |
| Avg topics/note | 6.6 | 5.9 |
| Avg products/note | 2.9 | 2.4 |

### Key Findings

**v3 is NOT a clear upgrade.** v3 wins more notes by count but has fewer total facts and lower
average topic/product coverage. The result is mixed:

- **Critical v2-only content:** `LifeScience_session1v2` (7 facts in v2, 0 in v3) and
  `Platform_Editedv2` (10 facts in v2, 0 in v3). These are extraction failures in v3 — v2 must
  be kept for these two sources.
- **Clear v3 winners:** `BlueYonder_StandardEntities` (41→77 facts), `Enterprise_Data_Orchestration_Pitch_Deck`
  (5→21 facts), `Deep_Meta_Learning` (8→15 facts), `SAP_Mapping_Matrix_2` (51→62 facts).
- **Clear v2 winners:** `Generic_Cognitive_Planning_Reference_Material` (47→11), `KYP_'23_Spring_Edition_EP_#1`
  (66→50), `BYPlatform-Architecture` (49→40).

### Recommendation (for Rob to confirm)

Do NOT delete either v2 or v3 wholesale. If per-note deletion is desired, use winners table
above. The two v3-empty files (`LifeScience_session1v2`, `Platform_Editedv2`) are the most
important: preserve v2 for those two regardless of overall decision.

---

## Item 2: Cognitive_Friday Vault Cross-Reference

### Extractions Found

| Extraction file | Source type | Source title |
|-----------------|-------------|--------------|
| `Cognitive Friday S4E1 - Journey to the Cloud.json` | .mp4 video | Blue Yonder Cognitive Friday Season 4: Journey 2 Cognitive Cloud |
| `Cognitive Friday S4E1 J2CC.json` | .pptx slides | Blue Yonder Journey 2 Cognitive Cloud Training - Cognitive Friday Season 4 |

Both are Season 4 Episode 1 from the same event (mp4 recording + pptx deck).

### Vault Status

| Extraction | Vault note exists? | Vault path |
|------------|--------------------|------------|
| S4E1 - Journey to the Cloud (mp4) | **YES** | `01_Knowledge/Cognitive Friday S4E1 - Journey to the Cloud.md` |
| S4E1 J2CC (pptx) | **YES** | `01_Knowledge/Cognitive Friday S4E1 J2CC.md` (+ session note: `session_cognitive-friday-s4e1-j2cc.md`) |

**All Cognitive_Friday extractions are already ingested into the vault.** No action required.

Note: Vault also contains `Cognitive Friday Season 2 - Product Analytics Program.md` — this has
no corresponding extraction in `_outputs/misc/Cognitive_Friday/`. That note was ingested separately
or manually; no extraction output exists for it.

---

## Item 3: .sandbox/ Summary

See `.ecosystem/archive/2026-03-28_SANDBOX_REVIEW_SUMMARY.md` for full report.

### TL;DR

- 119-file (20%) sample of MyWork/10_Projects/ run through classification + rename pipeline
- 2.4 GB sandbox, 123 files, output dir empty (apply step never run)
- 53% of files unclassifiable → fall back to MISC type
- 19 HIGH-similarity pairs, all space/underscore variants
- Pipeline mechanics work; `sandbox_apply.py` does not exist yet
- No files in MyWork/ were modified

---

## Item 4: Rebuild Script Archival

**Scripts moved to `scripts/archive/`:**

| Script | Purpose |
|--------|---------|
| `build_rebuild_batch.py` | Generated rebuild batch job for .ecosystem/rebuild_staging/ |
| `build_pilot_batch.py` | Generated pilot batch job (blue_yonder_integration_workshop subset) |
| `rebuild_complete.py` | Orchestrated full rebuild run — spawned CKE extraction pipeline |
| `rebuild_finalize.py` | Read rebuild_complete_output.log, produced finalization summary |

**References checked:** Only `.ecosystem/archive/2026-03-28_REPO_INVESTIGATION.md` references
these scripts (historical context). `rebuild_complete.py` and `rebuild_finalize.py` reference
each other internally. No active scripts, tests, or config files reference them. Safe to archive.

**Cross-reference note:** The rebuild output log (`.ecosystem/rebuild_complete_output.log`) may
still exist if the rebuild was run. Scripts are archived, not deleted — can be recovered if needed.

---

## Open Items After Phase 4

The following items were explicitly deferred — require Rob's confirmation:

1. **Per-note v2/v3 deletion** — use winners table above; two v3-empty files (LifeScience,
   Platform_Editedv2) must stay in v2 regardless.
2. **misc/Cognitive_Friday/ deletion** — both extractions are in vault; safe to delete extraction
   output dir (Rob confirms).
3. **Long-term _outputs/ archival** — 18 GB remains after Phase 2 cleanup; v2 and v3 are the
   bulk. Deferred to after vault ingestion decisions.
4. **sandbox_apply.py** — needs to be built before full MyWork/10_Projects/ rename can run.
5. **doc_type_classifier.py pattern expansion** — address the 53% MISC rate before full rename.

---
_Report generated: 2026-03-28_
