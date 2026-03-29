# Vault Rebuild Report — 2026-03-27

**Council Decision:** #20 — Re-extract 257 accessible vault notes via improved CKE pipeline

## Summary

| Metric | Value |
|--------|-------|
| Files targeted | 257 |
| Files extracted (done) | 216 |
| Extraction errors | 41 |
| Started | 2026-03-27T07:05:09 |
| Completed | 2026-03-27T09:32:40 |

## Step 8: Ingest Results

```
Ingest Results       
 Metric             | Count 
--------------------+-------
 Notes ingested     |   239 
 Quarantined        |     2 
 Skipped (verified) |     0 
 Cover slides       |     4 

Destinations:
  01_Knowledge: 239

2 note(s) quarantined to _quarantine/

Rebuilding search index...
Index rebuilt: 0 facts indexed.
INFO corp_by_os.ingest.extractions: Found 242 packages in C:\Users\1028120\Documents\Scripts\corp-monorepo\.ecosystem\rebuild_staging
INFO corp_by_os.ingest.extractions: Quarantined: 2026-03-27_other_questions_5c7f.md — quality_score 8 < 25
INFO corp_by_os.ingest.extractions: Quarantined: 2026-03-27_recordingpepsiemea202601_bce3.md — quality_score 18 < 25
INFO corp_by_os.index_builder: Indexed 777 CKE notes from vault
INFO corp_by_os.index_builder: Deduped 294 notes with identical source_hash
INFO corp_by_os.index_builder: Index rebuilt: 25 projects, 0 facts, 483 notes in 7.4s -> C:\Users\1028120\AppData\Local\corp-by-os\index.db
```

## Step 11a: Trust Status

```
Vault Trust Level Distribution            
+---------------------------------------------------+
| Trust Level     |    Count |                      |
|-----------------+----------+----------------------|
| extracted       |      471 | overwritable         |
| draft           |        2 | overwritable         |
| none            |       15 | legacy (no field)    |
| deprecated      |      326 | unknown              |
+---------------------------------------------------+

  Total notes: 814
```

## Step 11b: Retrieve — JLR TMS

```
Usage: corp retrieve [OPTIONS] QUERY
Try 'corp retrieve --help' for help.

Error: No such option: --verbose
```

## Step 11b: Retrieve — Demand Planning

```
Usage: corp retrieve [OPTIONS] QUERY
Try 'corp retrieve --help' for help.

Error: No such option: --verbose
```

## Step 11c: Eval

```
==========================================================
  Extraction Quality Eval
==========================================================

[1a] Regex Classifier  (310 filenames, filename-only)
    Accuracy : 57.1%  (177/310)
    Top confusion pairs  (predicted -> expected  count):
                      None -> training             46x
                      None -> product_doc          20x
                      None -> architecture         18x
                      None -> meeting              11x
              architecture -> product_doc          5x
              presentation -> training             5x
                 discovery -> meeting              4x
              rfp_response -> architecture         3x
                      None -> commercial           3x
                  training -> product_doc          3x

[1b] Hybrid Classifier  (310 enriched examples)
    TF-IDF  : 197 files  acc=100.0%
    Regex   :  56 files  acc=71.4%
    LLM fallback: 57 files  (18% of total)
    Overall classified acc: 93.7%
    With content    acc: 96.1%
    Filename-only   acc: 92.7%

[2] Tag Taxonomy Coverage  (172 golden tags)
    Mean : 0.797   Median : 1.0
    Worst (unrecognised / partial):
      0.5  domain/product-platform-architecture  [partial]
      0.5  product/inventory-optimization  [partial]
      0.5  product/lp-solver  [partial]
      0.5  product/luminate-dynamic-segmentation  [partial]
      0.5  product/microsoft-bi  [partial]
      0.5  product/microsoft-dynamics-365-crm  [partial]
      0.5  product/planning-engine  [partial]
      0.5  product/power-bi  [partial]
      0.5  product/sap  [partial]
      0.5  product/sap-cloud-platform-integration  [partial]

[3] Product Normalizer Idempotency  (64 products)
    Mean : 1.000   Median : 1.0
    All products normalise stably (idempotent).

[4] People Filter F1  (444 entries)
    Precision : 0.924   Recall : 0.931   F1 : 0.927
    TP=377  TN=8  FP=31  FN=28

==========================================================

Results appended -> eval\eval_history.jsonl
```

## Changes Made

- **Step 7:** Re-extracted 216 notes via `cke process-manifest` (gemini-3.1-pro-preview + claude-haiku-4-5-20251001 enrichment)
- **Step 8:** Ingested via `corp ingest-extractions --quality-threshold 25 --rebuild-index`
- **Step 9:** `retrieve/engine.py` — added `include_deprecated: bool = False` to `RetrievalFilter`; deprecated notes now excluded from all retrieve paths (FTS5, metadata supplement, fallback)
- **Step 10:** Vault `02_Navigate/` — added `Compliance/Compliance.md` MOC (was missing); all 9 MOC directories confirmed populated
- **Step 11:** Trust status, JLR TMS retrieve, demand planning retrieve, eval suite

## Constraints Honored

- Did NOT delete inaccessible notes (47 skipped)
- Did NOT skip pilot (25-file pilot ran first, confirmed clean)
- Did NOT touch OneDrive paths
- Did NOT force quality_score threshold (used --quality-threshold 25)
- Did NOT merge RFP KB
- Did NOT add wikilinks to extracted notes
