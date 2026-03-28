# Ontology Benchmark — MVP SQL Analytics Results

**Date:** 2026-03-28
**Session:** Day 1 quick wins — SQL analytics, no ontology
**Council decision:** #21 — MVP first
**Index state:** 25 projects, 488 notes (after dedup from 813 raw)

---

## Changes implemented

| # | Change | File |
|---|--------|------|
| 1 | Added `people` to `notes_fts` virtual table + INSERT/DELETE triggers | `index_builder.py` |
| 2 | 6 new analytics functions (Q1/Q2/Q3/Q6/Q9/Q10) | `query_engine.py` |
| 3 | `corp analytics` converted to group; 6 subcommands + `report` | `cli.py` |

Index rebuilt after schema change. Tests: **1015 passed, 1 skipped**.

---

## Benchmark results

### Q1 — `corp analytics products --client JLR`
**Status: WORKS**

Returns 7 distinct products for JLR:
- Blue Yonder Control Tower, Logistics Emissions Calculator, OMS, Platform, TMS, WMS, Workforce Management

---

### Q2 — `corp analytics timeline --client JLR`
**Status: WORKS**

Returns 3 dated notes in chronological order:
| Date | Title | Type |
|------|-------|------|
| 2026-03-27 | Blue Yonder RFI Response to JLR Transport... | rfp_response |
| 2026-03-27 | Blue Yonder WMS RFI Response for JLR Spare Parts | rfp_response |
| 2026-03-27 | JLR Blue Yonder WMS/TMS/OMS Maturity Assessment | vendor_assessment |

*Note: limited date range — all notes are recent (2026-03-27). Timeline will grow as older docs are extracted.*

---

### Q3 — `corp analytics clients --product WMS`
**Status: WORKS**

Returns **23 clients** with WMS in their notes: Ahold, Almajdouie Motors, Clicks, Corning, Dollar General, George, Global Logistics Corp, Greencore, Honda, ILS, JLR, Lenzing, Macy's, Michelin, NEOM, PepsiCo, RSG, Rittal, Rossmann, SGDBF, Stellantis, Würth, Żabka.

---

### Q4 — Not implemented
*Not in spec (Q4 = product gaps — needs ontology/schema lookup, not SQL)*

---

### Q5 — Not implemented
*Not in spec (Q5 = deal stage correlations — needs ops.db join)*

---

### Q6 — `corp analytics overlap --product TMS`
**Status: WORKS**

Returns **19 clients** sharing TMS interest with note counts:
| Top clients | Notes |
|-------------|-------|
| Lenzing | 4 |
| LabelVie | 3 |
| PepsiCo | 2 |
| JLR | 2 |
| 15 others | 1 each |

---

### Q7 — Not implemented
*Not in spec*

---

### Q8 — Not implemented
*Not in spec*

---

### Q9 — `corp analytics compare --clients "Michelin,Stellantis"`
**Status: WORKS**

Side-by-side comparison of 18 distinct products across both clients:

| Product | Michelin | Stellantis |
|---------|----------|------------|
| Azure | Y | Y |
| Blue Yonder Platform | Y | Y |
| Blue Yonder TMS | Y | Y |
| Blue Yonder WMS | Y | Y |
| Platform Data Cloud | Y | Y |
| Application Lifecycle Manager | Y | - |
| Blue Yonder Supply Planning | Y | - |
| Blue Yonder Workforce Management | Y | - |
| Demand Planning | Y | - |
| Semantic Network Architect | Y | - |
| Supply Chain Planning | Y | - |
| BYDM Workbench | - | Y |
| ML Studio | - | Y |
| Platform (SaaS) | - | Y |
| Snowflake | - | Y |
| Supply Chain Platform | - | Y |

*Note: some product name normalization needed (e.g. "Platform (SaaS-based" and "unspecified product suite)" are extraction artifacts — needs ontology/normalization layer to clean up)*

---

### Q10 — `corp analytics recent`
**Status: WORKS** *(data correct; display crashes on non-ASCII client names in Windows cp1252 console)*

Returns **50 clients**, one most-recent note each. Sample:
| Date | Client | Most Recent Note |
|------|--------|-----------------|
| 2026-03-27 | Almarai | Almarai Poultry Product Catalog |
| 2026-03-27 | JLR | JLR WMS/TMS/OMS Maturity Assessment |
| 2026-03-27 | Rossmann | Rossmann Tech Session: Platform Architecture |
| 2026-03-22 | Ahold | Blue Yonder Platform Tech Workshop |
| 2026-03-22 | Alfa Laval | Supplier Review: RFP Response |
| 2026-03-22 | Avon | Blue Yonder Cognitive Shorts: Snowflake |

**Known issue:** Windows PowerShell cp1252 encoding crashes Rich table rendering on Żabka/Würth characters. This is a pre-existing console limitation — not a query bug. Fix: run in Windows Terminal with UTF-8 (`chcp 65001`) or set `PYTHONUTF8=1`.

---

## Summary: which questions work vs. need ontology

| Q# | Command | Works? | Notes |
|----|---------|--------|-------|
| Q1 | `corp analytics products --client X` | **YES** | Exact client match required |
| Q2 | `corp analytics timeline --client X` | **YES** | Only notes with date field populated |
| Q3 | `corp analytics clients --product X` | **YES** | Substring match on product field |
| Q4 | Product gaps | **NO** | Needs ontology: canonical product list to diff against |
| Q5 | Deal stage correlations | **NO** | Needs ops.db join |
| Q6 | `corp analytics overlap --product X` | **YES** | Returns clients + note counts |
| Q7 | Topic clusters | **NO** | Needs embedding/clustering |
| Q8 | Competitive intelligence | **NO** | Needs structured competitive data |
| Q9 | `corp analytics compare --clients "A,B"` | **YES** | Raw product strings (normalization needed) |
| Q10 | `corp analytics recent` | **YES** | Display issue on non-ASCII names in legacy console |

**6/10 questions answered by SQL. 4 still need ontology/embeddings/additional data sources.**

---

## What ontology would unlock (remaining 4)

| Q# | What's needed |
|----|---------------|
| Q4 | Canonical product taxonomy → diff client's products against full catalog |
| Q5 | Link notes index → ops.db (deal stage, opportunity status) |
| Q7 | Embeddings on topics/content → cluster related notes semantically |
| Q8 | Source classification by doc_type to identify competitor mentions |

---

## Product name normalization gap (affects Q9 quality)

`corp analytics compare` reveals extraction artifacts in product names:
- `"Platform (SaaS-based"` and `"unspecified product suite)"` — split extraction
- `"Blue Yonder Platform"` vs `"Supply Chain Platform"` — synonym collision

This needs either:
1. A canonical product alias map (fast, ADR-18 approach)
2. LLM normalization pass on ingest (slower, more accurate)
