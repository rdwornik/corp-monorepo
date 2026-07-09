# Metadata Charter — Complete Tri-Axial Taxonomy (T1)

**Repo:** corp-monorepo (charter) · vault + registry + index (enforcement surfaces) · **Audience:** functional intake / technical architect
**Status:** brainstorm-phase blueprint (audit-space per DR-14); the canonical-field-set + tag-taxonomy deliverable the operator called *"kluczowe"*
**Date:** 2026-07-08 · **Session:** functional-architect sitting #5 (T1)
**Inputs reconciled (all read in full):** `2026-07-07_EVIDENCE_by-product-docs-tree-analysis.md` (360-family tree, 7 rule classes, v0 tags) · `2026-07-08-dimensions-report-for-corpos-t1.md` (demo-prep: 13 axes, 55-node platform interior, third-axis ruling, Q6 deltas) · `2026-07-07_AUDIT_demo-prep-recon.md` (Pass-D schema provenance) · field-survival chain (deep-vault audit, on main).

---

## 1. Problem

The charter must give every knowledge artifact a canonical field set and a tag taxonomy on **industry × software** plus topic. The v0 tag vocabulary (tree-analysis §II.f) was a **partial clustering** — it tagged the heavy, obvious families and left whole capability classes uncovered (the operator's example: `Blue Yonder Network` had no tag; the gap-scan below finds ~11 more uncovered classes). Separately, v0 flattened `platform` into one bucket although demo-prep's Pass-D work maps its 55-node interior, and it left the industry axis **entangled inside software names** (`IDSP for High Tech`). This charter closes all three: **complete coverage of the 360-family namespace, a decomposed platform, and de-entangled axes** — with an enforcement seam per field so the taxonomy is *held by mechanism, not discipline*.

## 2. Evidence (what the two terrains jointly prove)

**From the Products tree (§II of tree-analysis):** the library is a **release-publishing catalog, not a taxonomy** — 360 L1 families in a flat alphabetical namespace, hierarchy below is mechanical (Family/Version/Help/Flare). File mass is **anti-correlated with product importance** (66% MadCap-Flare scaffolding; flagship TMS = 22 files vs Platform = 8,807) — *never weight the taxonomy by file count*. Seven deterministic name-rule classes exist (§II.b): version tokens, generated-asset filter, heritage-in-parens, product-line prefixes, lifecycle suffixes, acronym map, normalization anti-patterns.

**From demo-prep (dimensions report):** the Pass-D schema is **13 fields, of which 9 are true classifying axes** and 4 are key/constant/provenance (Q1 + BACKLOG [#20]). Only **5 axes were load-bearing** — drove an actual curation decision (Q5): `dedup_status` (MEAS), `asset_type`, `cohort/date`, `depth`-lite, `verdict`; the rest were near-constant or decoration at solo scale. The `platform` product resolves into a **55-node interior** (Q2) with a customer-facing-vs-plumbing (`facing`) flag. The 8-section deck taxonomy is **the topic axis** — specifically the interior of the `platform` node viewed as topics (Q3). demo-prep flagged 6 missing tags and 3 mis-groupings against v0 (Q6), plus a new deterministic rule: the **"on Platform Data Cloud"** suffix marks re-platformed products.

**Joint verdict:** the two sources are complementary at different resolutions — the Products tree is the **breadth** (all 360 product names), demo-prep is the **depth** (the platform interior + field-tested axes). The charter fuses breadth × depth.

## 3. Converged recommendation

### 3.1 Three axes, defined (the charter's spine)

| Axis | What it answers | Values live as | Cardinality |
|---|---|---|---|
| **INDUSTRY** | which vertical the artifact serves | `industry:*` tag, ≥0 per artifact (many products are industry-neutral) | ~8 |
| **SOFTWARE** | which BY product/module | `sw:*` tag, exactly 1 primary + ≥0 secondary | ~40 (§3.3) |
| **TOPIC** | which capability/subject, cross-product | `topic:*` tag, ≥0 per artifact | 8 top + `platform:*` leaves (§3.4) |

**Why three, not two:** the operator named industry × software, but both terrains force a third — the 8 sections and the platform interior are *capabilities that recur across products* (security, ai-ml, integration, analytics), orthogonal to which product ships them (demo-prep Q3, ruling CONFIRMED). Cohort/date (Dallas/Bangalore/Warsaw) is a **fourth, artifact-local** dimension — training vintage — and must **not** be folded into industry (demo-prep closing-Q4).

### 3.2 Canonical field set — separate keys from axes (closes demo-prep [#20])

The Pass-D "11 axes" conflated four kinds of field. The charter formally separates them:

| Class | Fields | Rule |
|---|---|---|
| **KEY** | `id` | stable primary key; never a classifier |
| **PROVENANCE** | `source_path`, `source_site`, `site_id`/`drive_id` (registry link), `created`, `last_verified` | locators + origin; `source_site` is library-level, **not** stamped per-asset (demo-prep Q1.3 KILL) |
| **CLASSIFICATION AXES** | `industry[]`, `sw` + `sw_secondary[]`, `topic[]`, `asset_type`, `depth`, `lifecycle` (§3.5), `phase` (S0–S3) | the taxonomy proper |
| **DECISION / STATE** | `verdict`, `dedup_status`, `demo_usability`, `liveness` | outputs of process, not describers of content |

**Minimal load-bearing set (the anti-decoration ruling, from demo-prep Q5):** an artifact is fully classified by **`id` · `sw` · `topic[]` · `industry[]` · `asset_type` · `phase` · `lifecycle`**. Everything else is either provenance (free, deterministic, keep) or decision-state (populated only when a decision is made — *not* stamped on the ~90% dup/register mass). This is the charter's core economy: **rich metadata only where a decision consumes it.**

### 3.3 SOFTWARE axis — COMPLETE tag set (every one of the 360 families lands)

The gap-scan below assigns **all 360 L1 families** to a `sw:*` tag or a control tag. Tags new since v0 are marked **[NEW]**; v0 corrections from demo-prep are marked **[FIX]**.

**Planning**
- `sw:demand-planning` ← Demand*, Demand Planner/Manager/Decomposition, Cognitive/ML Demand, Luminate Demand Edge, Forecasting for Retail, Event Lift Forecasting, Seasonal Profiling, Attribute Based Planning, Demand Planning by Intellect
- `sw:supply-planning` ← Master Planning, Enterprise/Attribute Supply Planning, Supply Chain Planner/Strategist/Executive, Production Planning and Scheduling, Factory Planner, Finite Capacity Scheduler, Make-to-Order, Build To Order, Manufacturing ABPP/Foundation, Retail ABPP
- `sw:ibp-sop` ← Integrated Business Planning*, Sales and Operations Planning, Executive SnOP Workbench, Enterprise Planning, Consensus Planning, Planning on Demand, Planning RAPIDS
- `sw:scpo` ← SCPO General, Inventory Optimization/Policy Optimization, Replenishment Interval Optimization (SCPO)
- `sw:replenishment` ← Replenishment for Retail, Advanced/Cognitive/Dynamic/Marketplace/Portfolio Replenishment, Vendor Managed Replenishment, Allocation and Replenishment, InStock
- `sw:allocation` **[NEW]** ← Allocation, Dynamic/Intelligent/Cognitive Allocation, Material Allocator, Centralized Availability
- `sw:network-design` **[NEW]** ← Network Optimization, Fulfillment Sourcing Simulator, Channel Clustering

**Retail merchandising**
- `sw:assortment` ← Assortment*, Shelf/Strategic/Efficient Item Assortment, Luminate Assortment(+Mobile), Buying and Assortment Management, Retail.me Assortment Planning
- `sw:space-planning` ← Space*, Planogram*, Floor Planning, Planning Space and Process Orchestration, Shelf
- `sw:category-mgmt` ← Category Management Suite, CategoryAdvisor, Category/Arthur Knowledge Base, Arthur Planning
- `sw:mfp` ← Merchandise Financial Planning*, Merchandise Operations, PKB Merchandise Metric Domain, Retail Planning Dashboard
- `sw:pricing-markdown` ← Price Management, Markdown/Fresh Markdown Optimization, Clearance Price(+on PDC), Strategic/Target/Real-Time/Live Pricing, Dynamic Price Discovery, MDM for Grocery Pricing
- `sw:promotions` ← Promotions Management/Optimization(+on PDC Offer), PromoPlanner, Trade Promotions/Trade Events for Retail, Media Promotions Optimizer

**Execution / logistics**
- `sw:wms` ← Warehouse Management*(+ - Marc/ P), Warehouse Execution System, Warehouse Tasking, Dispatcher WMS/Home Furnishings, Adaptive Fulfillment and Warehousing
- `sw:tms-execution` **[FIX: split from planning]** ← Transportation Management Solution/Manager/- RedPrairie, Real-Time Transportation Cloud, Transportation Fleet Dispatcher/Mobile User
- `sw:transportation-planning` **[NEW: the other half of v0's `tms`]** ← Transportation Modeler/Modeling/Optimization/Planner/Planning/Rating, Transport RFQ, Transportation Bid Collaboration/Insights, Load Building, Fleet Capacity Planner/Management
- `sw:yard-mgmt` **[NEW]** ← Yard Management
- `sw:slotting-sequencing` **[NEW]** ← Slotting, Order Slotting & Scheduling/Sequencing and Slotting (flexis), Sequencing, Order Sequencing
- `sw:workforce-labor` ← Workforce*(+ Mgmt for Retail/Mobile), Warehouse/Advanced Labor *, Labour Capacity UI, Scheduling - Shift Connect, Delivery Capacity UI
- `sw:fulfillment` ← Fulfillment*, Store/DC Fulfillment(+on PDC), Order Fulfillment, In-Store Picking, Drop-off Kiosk, Pick Up Drop Off *, Smart Disposition
- `sw:store-ops` ← Store*(Execution/Insights/Optimizer/Portal), Enterprise Store Operations, Mobile *Connect, Mobile Task Execution, Site/District Manager, Label Designer

**Commerce / order**
- `sw:order-promising` **[FIX: was `order-mgmt`, planning side]** ← Order Promising/Promiser, Order Services, Customer Order Assistant/Visibility, Available-to-Promise
- `sw:oms-execution` **[NEW: demo-prep b5]** ← Distributed Order Management, Customer Order Management, Order Fulfillment (execution)
- `sw:returns` ← Returns Management Service, Returns Orchestration, Online/In-Store Returns, Warehouse Returns*
- `sw:commerce` **[NEW]** ← Web/Direct Commerce, Commerce Suite/Insights and Actions/Exception Workbench, Marketplace(+Replenishment), Inventory Visibility (Commerce), Back-Office System

**Revenue**
- `sw:revenue-optimization` ← Airline/Cargo/Hospitality/Rail/Tour Revenue Optimizer, *Price Optimizer, Travel Price Optimization, Commercial Log/Proposal Optimizer, Media Rate/Revenue *

**Cross-product capability families (the v0 gap — all [NEW])**
- `sw:ai-ml` **[NEW — demo-prep b1, biggest gap]** ← ML Studio, GenAI Studio, Pulse AI, Anomaly Detection, Cognitive Foundation/ML Forecasting/Consensus/Configuration/Data Migration, Precision, GenAI, Scenario Analyzer
- `sw:network-visibility` **[NEW — demo-prep b2, the operator's example]** ← Blue Yonder Network, Control Tower, Track and Trace, Carrier Collaboration, Supply Chain Command Center, Collaborative Supply Execution, Logistics Event Management and Visibility, DC Insights
- `sw:analytics-reporting` **[NEW — demo-prep b3]** ← Reporting(+RedPrairie/& Analytics), Analytics, Report Designer, Performance Analysis(+Web/IDEAS), Performance/Product/Store/Production/Supplier/Customer/Commerce Insights, Product and Market Insights, Analysis and Discovery, Analyst Workbench, Monitor, Monitoring and Diagnostics
- `sw:integration` **[NEW — demo-prep b4]** ← Cognitive Integration Generator, Integration HUB (RedPrairie), Connect(+For SAP HANA), Integrator(+SCE), Cognitive Interface/Configuration Migration, Supply Chain Connect, Data Extractor, Retail Data Model - Planning Integration
- `sw:sourcing-procurement` **[NEW]** ← Strategic/Product Sourcing, Logistics Procurement, Procurement, Negotiate, Sourcing Dashboard, Production and Sourcing Optimization, Transport RFQ
- `sw:sustainability` **[NEW]** ← Logistics Emissions Calculator, Sustainable Supply Chain Manager
- `sw:marketing-advertising` **[NEW]** ← Advertising, Market Manager, Marketing Expense Management, Media Revenue Planning
- `sw:billing-financial` **[NEW]** ← Billing Management, Third Party Billing
- `sw:crm-customer` **[NEW]** ← CRM, Customer Insights, Customer Order Assistant
- `sw:mro` **[NEW]** ← Maintenance, Repair and Overhaul
- `sw:collaboration` **[NEW]** ← Collaborate, Collaboration Portal, Negotiate, Blue Yonder Value Explorer
- `sw:event-mgmt` **[NEW]** ← Event Management, Dynamic Demand Response, Information Alerts - Non Product Specific
- `sw:segmentation` **[NEW]** ← Dynamic Segmentation, Channel Management, Size Scaling, Anomaly Detection (cross-listed)

**Platform (product tag; interior in §3.4)**
- `sw:platform` ← Blue Yonder Platform, Luminate Platform Data Management, Common Services, Mobile Platform, Luminate DC Fulfillment, GenAI/ML Studio (platform-hosted), the 55 Q2 interior nodes

### 3.4 TOPIC axis — the 8 sections + the platform interior (from demo-prep Q2/Q3)

Top level = the 8 canonical sections; leaves = the `platform:*` sub-tags (demo-prep's 55-node map, ready-to-adopt, each carrying a `facing` flag cx/plumb/hybrid):

`topic:architecture` · `topic:data-cloud` (bydm, bydmr, elasticsearch, snowflake, dds, tds, dts, cig, sna, curation, validation…) · `topic:integration` (edo, integration-hub, sap-datashare, ingress-egress…) · `topic:semantic-network` (sna) · `topic:analytics` (das, ras, daas, sigma, datamart, sustainability-insights) · `topic:foundation` (iam, apim, observability, cost-mgmt, security-auditing, env-provisioning) · `topic:experience` (portal, component-library, workflow-orchestrator, process-orchestration, alm) · `topic:ai-ml` (predictive-ml, generative-ai, agentic-orchestrator, agent-marketplace, advisory-agents, snowflake-intelligence, domain-ops-agents) · `topic:saas` · `topic:security`.

**Governance ruling (demo-prep closing-Q1):** adopt topic as a **standalone third axis**, not a nested `platform:*` namespace — because security/ai-ml/analytics/integration recur *beyond* the platform (e.g. WMS security, TMS analytics). A product-scoped nested namespace would re-trap them. The `platform:` leaves become `topic:` values that any product can carry.

### 3.5 Deterministic auto-tagging — the rule engine (deterministic-first, LLM for residual)

Union of the tree's 7 rule classes (§II.b) + demo-prep's additions. **Every rule is DET (path/name only) unless marked JUDG:**

1. **Version collapse** (DET): `YYYY.Q.0.0` | `YYYY.Q` | `Production` | `aspx-demo` → strip to product; emit `version:`.
2. **Generated-asset filter** (DET): anything under `\Data\` | `\content\resources\` | `Help_aspx\` → `asset_type:generated-scaffold`, excluded from the authored corpus.
3. **Heritage** (DET): `(RedPrairie)` `(SCE)` `(SCPO)` `(flexis)` `(IDEAS)` `(ESO)` `by Intellect` `JDA Next` → `heritage:` tag.
4. **Product-line prefix** (DET): `Cognitive *` `Luminate *` `IDSP for *` `Business Analysis for *` `Transportation *` `Warehouse *` `Store *` `Advanced *` `Strategic *` `Mobile *` `Enterprise *` → family grouping.
5. **Industry de-entanglement** (DET): `IDSP for <X>` | `* Retail Prescription` | `* - Industries Prescription` → split `sw:` + `industry:` (the axis-crossing fix, tree §II.d + demo-prep).
6. **"on Platform Data Cloud" suffix** **[NEW — demo-prep closing-Q5]** (DET): `* on Platform Data Cloud` | `* on PDC` → `topic:data-cloud` + `platform-native:true` flag on an otherwise-standalone product.
7. **Lifecycle suffix** (DET): `_OLD` `_old` `-Legacy` `-Internal` ` P` ` - Marc` `-HYB-<hash>` → `lifecycle:{legacy|internal|variant|duplicate}`.
8. **Acronym map** (DET): the union synonym table — WMS TMS SCPO IBP MFP CDP IDSP LDE PDC ABPP SnOP/S&OP ESO SCE MMS PMM MOCA + demo-prep's BYDM BYDMR DDS TDS DTS DAS RaaS DaaS EDO CIG SNA → full-name synonyms.
9. **`facing` flag on platform nodes** **[NEW — demo-prep Q2]** (JUDG, one-time): cx | plumb | hybrid — resolves the `internal-component` over-quarantine [FIX a3].
10. **Residual → LLM** (JUDG): only names that survive rules 1–9 unassigned get an LLM `sw:`/`topic:` proposal → operator ratifies. Target: <15% residual.

### 3.6 Control tags (exclude / quarantine — refined per demo-prep [FIX])

- `ctl:legacy` ← *_OLD, *-Legacy, RedPrairie/JDA-heritage brands (Inforem, WinDSS, SoftGrocer, Flowcasting, MOCA, MMS), `Workforce-Legacy` (0 files), `Assortment Planning_OLD`
- `ctl:internal-plumbing` **[FIX a3: only true plumbing]** ← Approval Server, Job Scheduler, Registry, Environment Manager, Infrastructure Services, Content Server, Common Services — but **NOT** DTS/TDS/DDS/DAS/Inventory Service/Commits Service (these are `sw:platform` + `topic:data-cloud`, `facing:cx/hybrid`)
- `ctl:doc-process` ← PDDOC-Internal (2,048 files), PMGNPD Documentation, Business Analysis for *, Enterprise Architecture, Portfolio/Enterprise Knowledge Base, Portfolio Framework/Component Management
- `ctl:tooling` ← Integration Test Automation Framework (2,904), Magic Deployment Engine, DMS to PDC Migration Toolkit Pipeline, Cognitive Data Migration Tool, Remote Access, Configuration UI, SCM UI
- `ctl:test-stub` ← Test, TestProduct, WAYLAND TEST FOLDER, CT2020, Dropzone
- `ctl:duplicate-collision` ← `Cognitive Interface Migration-HYB-gpzdYOQu8SK` and any `-HYB-<hash>` peer
- `ctl:normalize` ← `Componenet Management` (misspelling→Component), `". xls"` (malformed ext), ampersand-vs-"and" variants

### 3.7 Enforcement seams (held by mechanism)

| Field class | Seam | Fires when |
|---|---|---|
| KEY / PROVENANCE | frontmatter schema validator | any note write; missing `id`/`source_path` → block |
| `sw` (exactly 1 primary) | validator + tag-vocabulary allowlist | unknown `sw:` tag or 0/≥2 primaries → block |
| `topic[]`, `industry[]` | vocabulary allowlist (generated from this charter) | unknown value → warn (proposals allowed, ratify to promote) |
| auto-tag rules 1–8 | deterministic tagger at ingest (W1 restart, DR-6) | every new asset |
| residual rule 10 | LLM proposal → ratification gate | name unassigned after rules 1–9 |
| `lifecycle:legacy/duplicate` | quarantine router | matched → `_quarantine/`, not the live tree |

## 4. Open decisions (operator ratification)

D1 **Topic as standalone axis vs nested `platform:*`** — recommend standalone (§3.4 ruling); confirm. · D2 **`sw` secondary tags** — allow a product to carry `sw_secondary[]` (e.g. `Luminate Assortment` = `sw:assortment` + `sw:platform`) or force single? Recommend allow, cap at 2. · D3 **Per-asset topic tags: all assets or curated-subset-only** — demo-prep Q5 shows full-coverage judgment buys no decision value; recommend curated-subset (COPY+VIDEO+authored), dup/register mass gets `sw`+`asset_type` only. · D4 **Cohort axis** — keep as artifact-local 4th dimension, not folded into industry (confirm). · D5 **The ~11 [NEW] tags** — ratify the names, or rename at the same time as DR-7 zone renames. · D6 **`facing` flag population** — one-time JUDG pass over the 55 platform nodes (demo-prep supplies it) — adopt as-is or re-review.

## 5. NOT-list (over-engineering guards)

- **No file-count weighting** — mass is publishing artifact, not importance (tree §II.c, load-bearing).
- **No per-asset stamping of constants** — `source_site`/`hydration` are library-level (demo-prep Q1 KILL).
- **No topic tags on the ~90% dup/register mass** — decision-value zero there (demo-prep Q5).
- **No nested product-scoped topic namespace** — recurring capabilities re-trap (demo-prep closing-Q1).
- **No LLM-first tagging** — deterministic rules 1–9 do the bulk; LLM only the <15% residual, always ratified.
- **No hand-maintained synonym/tag lists** — generated from this charter, validated at seam.
- **No new taxonomy for cohort/version** beyond a flat field — they are attributes, not axes.
- **No adoption of the raw folder tree as the taxonomy** — it is accreted sediment; the tag set is the curated axis, the tree is only its seed.

## 6. FR-addendum candidates

- **FR-18 (new): Metadata charter** — the field-set classes (§3.2) + tri-axial tag taxonomy (§3.3/3.4) + the vocabulary allowlists as versioned, validator-enforced contracts.
- **FR-19 (new): Deterministic auto-tagger** — rules 1–10 (§3.5) as the ingest-time tagging seam (couples to FR-14 pipeline + DR-6 W1 restart).
- **Amendment to FR-17 (ontology charter):** the Product object's axis is this charter's `sw:*` set; the ontology's `dims` = `industry[] × sw`; `topic[]` becomes a third ontology property.
- **Amendment to FR-10 (registry):** golden-URL `dims` field draws from these exact vocabularies (one source, no divergence).
- **Cross-lane dependency filed:** demo-prep BACKLOG [#10] (author `AI-ML.md`) blocks deeper `topic:ai-ml` leaves; [#20] (axis-vs-key hygiene) resolved here in §3.2.

## 7. Success criteria (brief-level)

The charter holds when: **all 360 L1 families resolve** to a `sw:*` or `ctl:*` tag (the gap-scan in §3.3 is the proof — zero uncovered families, the v0 defect closed) · the platform node carries its 55-leaf `topic:*` interior · industry is de-entangled from every axis-crossing name · rules 1–9 are DET (name-only, no content read) and cover ≥85% of assignments · the vocabulary allowlists are generated and validator-enforced · every field carries its enforcement seam (§3.7). Closure is declared on **complete coverage + enforced vocabulary**, not on "a tag list exists."

## 8. Coverage ledger (the operator's completeness bar)

v0 → charter delta: **12 new `sw:*` tags** (ai-ml, network-visibility, analytics-reporting, integration, sourcing-procurement, sustainability, marketing-advertising, billing-financial, crm-customer, mro, collaboration, event-mgmt, segmentation, allocation, network-design, yard-mgmt, slotting-sequencing, oms-execution, commerce, transportation-planning — split), **3 v0 corrections** (tms split, order-mgmt→order-promising+oms, internal-component narrowed), **55 platform interior leaves added**, **1 new deterministic rule** (on-PDC suffix). The operator's flagged miss (`Blue Yonder Network`) now lands under `sw:network-visibility`. Uncovered families remaining: **0** — every name in the §II full L1 list maps to a `sw:*` or `ctl:*` tag above. (A fresh CC re-harvest against the renamed `_Blue Yonder Products - Product Documentation` folder would only refresh counts; the NAME set — the load-bearing layer — is unchanged by the rename.)

## 9. Sources

Internal (all read in full this sitting): tree-analysis §§I–II + full L1 list; demo-prep dimensions report Q1–Q6 + closing block; demo-prep recon §4 (Pass-D provenance); field-survival chain (deep-vault audit). No external research required — the terrains are the evidence.
