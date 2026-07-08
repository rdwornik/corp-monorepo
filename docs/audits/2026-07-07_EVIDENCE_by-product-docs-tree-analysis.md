# EVIDENCE — Blue Yonder Product-Documentation Tree: Harvest + Structural Analysis

- **Date:** 2026-07-07
- **Source library:** `C:\Users\1028120\OneDrive - Blue Yonder\Blue Yonder Products - Product Documentation`
- **Method:** T0 names/metadata enumeration ONLY (`Get-ChildItem` / `Measure-Object` / `Group-Object`). **No file content was opened, read, hashed, copied, or hydrated at any point.** Every zone command was scrutinized and appended to `~/.claude/logs/onedrive-guard.log` as `T0-ALLOW` (this run: 2026-07-07T23:33–23:47, log lines 5–44).
- **Purpose (operator framing):** folder NAMES encode the product map of Blue Yonder. This file is the evidence base + pre-analysis for the T1 metadata charter and T2 ontology (dims: **industry x software**, per `docs/audits/2026-07-07_BRIEF_algorithmic-adopt-map.md`).
- **Status of the tag vocabulary (Part II.f):** PROPOSAL only — the operator ratifies in T1.

## Totals

| Metric | Value | Source command (logged) |
|---|---|---|
| Directories (recursive) | **8,255** | `... -Directory -Recurse \| Measure-Object` |
| Files | **77,319** | `... -File -Recurse \| Measure-Object` |
| Top-level families (L1) | **360** | `... -Directory -Recurse -Depth 0 \| Measure-Object` |
| Max depth | **10 levels** below the library root | `-Depth 9` cumulative = 8,255 = total |
| Distinct file extensions | **45** | `... -File -Recurse \| Group-Object Extension` |

---

# PART I — Tree + Counts

## I.1 Shape of the tree (the structural grammar)

The tree is **not** a hand-curated hierarchy. Every heavy path obeys one recurring, machine-generated grammar:

```
Blue Yonder Products - Product Documentation/            [root]
+-- <Product Family>/                                    [L1 - 360 folders, a FLAT product namespace]
    +-- <Version>/                                       [L2 - ~4,838 folders; the VERSION axis]
    |     e.g. 2023.4.0.0 / 2024.1.0.0 / ... / 2026.2 / "Production"
        +-- <Guide or Help title>/                       [L3]
            +-- Help/  |  Help_aspx/                      [L4 - DUAL publish format = 2x mass]
                +-- content/  |  Data/                    [L5 - MadCap Flare WebHelp output]
                    +-- resources/images/ ... 32x32/     [L6-L10 - generated assets]
```

Worked examples (verbatim from the top-40 harvest):

```
Integrated Business Planning\Production\Help\Data                                     (1,325 files)
Integrated Business Planning\Production\Help_aspx\Data                                (1,325 files)  <- dual-format twin
Blue Yonder Platform\2023.4.0.0\Synchronizing Execution\Data                         (632 files)
Commits Service\2026.2.0.0\Help\Data                                                 (614 files)
IDSP for High Tech Electronics\2024.3.0.0\Data                                       (323 files)
Assortment Optimization\2024.4.0.0\Assortment Optimization 2024.4.0.0 Help\Assortment Optimization Help\content\resources\images\32x32   (deep spike)
```

**Depth distribution** (per-level directory counts, derived from cumulative `-Depth k` counts):

| Level | Dirs | Note |
|---|---|---|
| L1 (families) | 360 | flat product namespace |
| L2 | **4,838** | version + top-guide folders — the bulk of ALL folders |
| L3 | 569 | only a minority descend past the version folder |
| L4 | 701 | Help / Help_aspx |
| L5 | 735 | content / Data |
| L6 | 666 | resources |
| L7 | 335 | images |
| L8–L9 | 50 | deep asset dirs |
| L10 | 1 | single deepest branch |

Shape verdict: **shallow-and-wide with a few deep Flare spikes.** 59% of all folders sit at L2 (versions), and the fan-out collapses hard after that (4,838 -> 569 at L3): most version folders hold PDFs directly and go no deeper; a minority (the Flare-published families) spike down to L10. Average family fan-out = 4,838 / 360 = **13.4 direct children**, but heavily skewed (Blue Yonder Platform, IBP, the IDSP family carry dozens of versioned children; hundreds of families have 1–3).

## I.2 Per-folder counts

### Top-20 heaviest folders by file count (of top-40 harvested)

| Files | Folder (relative to library root) |
|---|---|
| 1,325 | `Integrated Business Planning\Production\Help\Data` |
| 1,325 | `Integrated Business Planning\Production\Help_aspx\Data` |
| 921 | `Demand and Supply Planning\aspx-demo\Data` |
| 693 | `Inventory Service\2026.2.0.0\Help\Data` |
| 632 | `Blue Yonder Platform\2023.4.0.0\Synchronizing Execution\Data` |
| 614 | `Commits Service\2026.2.0.0\Help\Data` |
| 611 | `Commits Service\2026.1.0.0\Help\Data` |
| 460 | `Blue Yonder Platform\2025.2.0.0\Synchronizing Execution - Internal\Data` |
| 457 | `Integrated Business Planning\Production\Help\content\resources\images` |
| 457 | `Integrated Business Planning\Production\Help_aspx\content\resources\images` |
| 434 | `Blue Yonder Platform\2025.1.0.0\Synchronizing Execution - Internal\Data` |
| 430 | `Blue Yonder Platform\2024.4.0.0\Synchronizing Execution\Data` |
| 418 | `Integration Test Automation Framework\2025.4.0.0\Data` |
| 379 | `Blue Yonder Platform\2024.3.0.0\Synchronizing Execution\Data` |
| 379 | `Blue Yonder Platform\2025.4\Planning Execution Interoperability - Internal\Data` |
| 345 | `Merchandise Financial Planning Retail Prescription\2025.2.0.0\Data` |
| 343 | `Integration Test Automation Framework\2025.1.0.0\Data` |
| 330 | `Blue Yonder Platform\2025.2.0.0\Planning Execution Interoperability - Internal\Data` |
| 323 | `IDSP for High Tech Electronics\2024.3.0.0\Data` |
| 321 | `Merchandise Financial Planning Retail Prescription\2025.4.0.0\Data` |

Every single one is a `\Data` or `\content\resources\images` folder — i.e. **MadCap Flare WebHelp output, not authored documents.** The heaviest human-authored granularity is invisible at this level because it is buried under generated assets.

### Per-family recursive file counts (24 families measured directly)

| Files | Family | Class |
|---|---|---|
| 8,807 | Blue Yonder Platform | platform |
| 4,646 | Integrated Business Planning | planning |
| 3,664 | Demand and Supply Planning | planning |
| 2,904 | Integration Test Automation Framework | **internal test tooling (not a product)** |
| 2,676 | IDSP for High Tech Electronics | industry-prescription |
| 2,418 | IDSP for Consumer Industries | industry-prescription |
| 2,048 | PDDOC-Internal | **internal doc-production area (not a product)** |
| 2,017 | Commits Service | platform microservice |
| 1,769 | Replenishment for Retail | retail planning |
| 1,708 | Merchandise Financial Planning Retail Prescription | industry-prescription |
| 1,513 | Inventory Service | platform microservice |
| 785 | Assortment Optimization | retail planning |
| 163 | Space Planning | retail (space) |
| 162 | SCPO General | supply planning |
| 109 | Warehouse Management Solution | execution (flagship) |
| 63 | Category Management Suite | retail (category) |
| 43 | Luminate Demand Edge | planning (flagship) |
| 34 | Assortment Planning_OLD | **legacy** |
| 22 | Transportation Management Solution | execution (flagship) |
| 9 | Blue Yonder Orchestrator_old | **legacy** |
| 2 | Test | **test placeholder** |
| 1 | TestProduct | **test placeholder** |
| 1 | WAYLAND TEST FOLDER | **test placeholder** |
| 0 | Workforce-Legacy | **DEAD — 0 files at any depth** |

These 24 families hold ~35,600 files (~46% of the corpus); the remaining 336 families average ~124 files each (mostly per-version PDFs).

## I.3 The full L1 product map (360 families, verbatim, on-disk order)

Measured families annotated `[N files]`. Everything else is name-only (T0).

Adaptive Fulfillment and Warehousing · Advanced Labor Forecasting · Advanced Replenishment · Advanced Store Replenishment · Advanced Warehouse Replenishment · Advertising · Airline Price Optimizer · Airline Revenue Optimizer · Allocation · Allocation and Replenishment · Analysis and Discovery · Analyst Workbench · Analytics · Anomaly Detection · Approval Server · Arthur Knowledge Base · Arthur Planning · Assortment · **Assortment Optimization [785]** · Assortment Planning · **Assortment Planning_OLD [34]** · Attribute Based Planning · Back-Office System · Billing Management · Blue Yonder Network · **Blue Yonder Orchestrator_old [9]** · **Blue Yonder Platform [8,807]** · Blue Yonder Value Explorer · Build To Order · Business Analysis · Business Analysis for Merchandise Management System · Business Analysis for Portfolio Merchandise Management · Business Analysis for Store Operations · Business Analysis for Transportation · Business Analysis for Warehouse · Buying and Assortment Management · Cargo Revenue Optimizer · Carrier · Carrier Collaboration · Category Knowledge Base · **Category Management Suite [63]** · CategoryAdvisor · CDP LDE Side by Side · CDP-IDSP Interop · Centralized Availability · Channel Clustering · Channel Management · Clearance Price · Clearance Pricing on Platform Data Cloud · Cognitive Allocation · Cognitive Configuration Migration · Cognitive Consensus Planning · Cognitive Data Migration Tool · Cognitive Demand Planning · Cognitive Foundation · Cognitive Integration Generator · Cognitive Interface Migration · Cognitive Interface Migration-HYB-gpzdYOQu8SK · Cognitive ML Forecasting · Cognitive Planning Validation · Cognitive Replenishment · Cognitive Supplier Ordering · Collaborate · Collaboration Portal · Collaborative Supply Execution · Commerce Exception Workbench · Commerce Insights and Actions · Commerce Suite · Commercial Log Optimizer · Commercial Proposal Optimizer · **Commits Service [2,017]** · Common Services · CompassCONTRACT · Componenet Management · Component and Supplier Management · Component Management · Configuration UI · Connect · Connect For SAP HANA · Content Server · Contract Management · Control Tower · CRM · Cruise Management System · CT2020 · Customer Insights · Customer Order Assistant · Customer Order Management · Customer Order Visibility · Data Extractor · DC Insights · Delivery Capacity UI · Demand · **Demand and Supply Planning [3,664]** · Demand and Supply Planning - Industries Prescription · Demand Decomposition · Demand Manager · Demand Planner · Demand Planning by Intellect · Direct Commerce · Dispatcher Home Furnishings · Dispatcher WMS · Distributed Order Management · Distribution Center Fulfillment on Platform Data Cloud · District Manager · DMS to PDC Migration Toolkit Pipeline · Drop-off Kiosk · Dropzone · Dynamic Allocation · Dynamic Demand Response · Dynamic Price Discovery · Dynamic Segmentation · Efficient Item Assortment · Enterprise Architecture · Enterprise Knowledge Base · Enterprise Planning · Enterprise Project Planner · Enterprise Store Operations · Enterprise Supply Planning · Environment Manager · Event Lift Forecasting · Event Management · Executive SnOP Workbench · Factory Planner · Finite Capacity Scheduler · Fleet Capacity Planner · Fleet Management · FLEX Technology · Floor Planning · Flowcasting · Forecasting for Retail · Freight Capacity Optimization · Freight Order Management · Freight Pay · Fresh Markdown Optimization · Fulfillment · Fulfillment Sourcing Simulator · GenAI Studio · Hospitality Revenue Optimizer · Hub · IDEAS for AWR · IDSP for Aftermarket and Industrial Distributors · IDSP for Automotive and Industrial Suppliers · **IDSP for Consumer Industries [2,418]** · **IDSP for High Tech Electronics [2,676]** · In-Store Picking · In-Store Returns Processing · Inforem · Information Alerts - Non Product Specific · Infrastructure Services · InStock · **Integrated Business Planning [4,646]** · Integrated Business Planning Offer · Integration HUB (RedPrairie) · **Integration Test Automation Framework [2,904]** · Integrator · Integrator (SCE) · Intelligent Allocation · Intelligent Rebalancer · Inventory Optimization (SCPO) · Inventory Policy Optimization · **Inventory Service [1,513]** · Inventory Visibility (Commerce) · JDA Next · Job Scheduler · Label Designer · Labour Capacity UI · Load Building · Logistics Emissions Calculator · Logistics Event Management and Visibility · Logistics Procurement · Luminate Assortment · Luminate Assortment Mobile · Luminate DC Fulfillment · **Luminate Demand Edge [43]** · Luminate Demand Edge for Distribution and Manufacturing · Luminate Live Pricing · Luminate Platform Data Management · Luminate Store Execution-Food Preparation · Magic Deployment Engine · Maintenance, Repair and Overhaul · Make-to-Order · Manufacturing ABPP · Manufacturing Foundation · Markdown Optimization · Market Manager · Marketing Expense Management · Marketplace · Marketplace Replenishment · Master Planning · Material Allocator · MDM for Grocery Pricing · Media Promotions Optimizer · Media Rate Optimizer · Media Revenue Planning · Merchandise Financial Planning · **Merchandise Financial Planning Retail Prescription [1,708]** · Merchandise Management for Home Furnishings · Merchandise Operations · Merchandise Performance Analysis (IDEAS) · ML Studio · MMS · Mobile Employee Connect · Mobile Manager Connect · Mobile Platform · Mobile Shift Connect · Mobile Task Execution · MOCA · Monitor · Monitoring and Diagnostics · Negotiate · Network Optimization · Online Returns · Order Fulfillment · Order Promiser · Order Promising · Order Sequencing (flexis) · Order Sequencing and Slotting · Order Services · Order Slotting & Scheduling (flexis) · Parcel · **PDDOC-Internal [2,048]** · Performance Analysis · Performance Analysis Web · Performance Management for Retail · Performance Management for Supply Chain · Pick Up Drop Off Check-Out Integrations · PKB Merchandise Metric Domain · Planning on Demand · Planning RAPIDS · Planning Space and Process Orchestration · Planogram Collaboration · Planogram Generator · Platform · PMGNPD Documentation · PMM · Portfolio Component Management · Portfolio Framework · Portfolio Knowledge Base · Portfolio Replenishment Optimization · Precision · Price Management · Procurement · Product and Market Insights · Product Insights · Product Sourcing · Production and Sourcing Optimization · Production Insights · Production Planning and Scheduling · PromoPlanner · Promotions Management · Promotions Management and Promotions Optimization on PDC Offer · Promotions Optimization · Pulse AI · Rail Revenue Optimizer · Real Time Pricing on Platform Data Cloud · Real-Time Transportation Cloud · Registry · Remote Access · Replenishment Demand Insights · **Replenishment for Retail [1,769]** · Replenishment Interval Optimization (SCPO) · Replenishment Supply Insights · Report Designer · Reporting · Reporting (RedPrairie) · Reporting & Analytics · Retail ABPP · Retail Data Model - Planning Integration · Retail Planning Dashboard · Retail.me Assortment Planning · Returns Management Service · Returns Orchestration · Robotics Hub · Sales and Operations Planning · SCE Shared · Scenario Analyzer · Scheduling - Shift Connect · SCM UI · **SCPO General [162]** · SCPO-LDE LSF Demand Edge Integration Adapter · Seasonal Profiling · Sequencing · Shelf Assortment · Site Manager · Size Scaling · Slotting · Smart Disposition · SoftGrocer · Sourcing Dashboard · Space Automation · Space Automation Professional · Space Management · **Space Planning [163]** · Space Planning Solution · Space Planning Web · Store · Store Execution Mobile (ESO) · Store Execution-Fuel and Forecourt Management · Store Fulfillment · Store Fulfillment on Platform Data Cloud · Store Insights · Store Optimizer · Store Portal · Strategic Assortment · Strategic Pricing · Strategic Sourcing · Strategic Space · Supplier Insights · Supply · Supply Chain Command Center · Supply Chain Connect · Supply Chain Executive · Supply Chain Planner · Supply Chain Strategist · Sustainable Supply Chain Manager · Target Pricing · Task · Task Management · **Test [2]** · **TestProduct [1]** · Third Party Billing · Tour Revenue Optimizer · Track and Trace · Trade Events for Retail · Trade Promotions Management · Transport RFQ · Transportation Bid Collaboration · Transportation Fleet Dispatcher · Transportation Insights · Transportation Management - RedPrairie · **Transportation Management Solution [22]** · Transportation Manager · Transportation Mobile User · Transportation Modeler · Transportation Modeling · Transportation Optimization · Transportation Planner · Transportation Planning · Transportation Rating · Travel Price Optimization · Vendor Managed Replenishment · Warehouse Execution System · Warehouse Labor Management · Warehouse Management · Warehouse Management - Marc · Warehouse Management P · **Warehouse Management Solution [109]** · Warehouse Returns · Warehouse Returns Processing · Warehouse Tasking · Warehousing Data as a Service · **WAYLAND TEST FOLDER [1]** · Web Commerce · WinDSS · Workforce · Workforce Management for Retail (RedPrairie) · Workforce Management Mobile · **Workforce-Legacy [0]** · Yard Management

> Note on the full 8,255-node tree: it is **not** rendered node-by-node. The full L2+ tree is ~7,900 machine-generated version/Flare folders whose shape is already fully characterized by the grammar (I.1) and the depth distribution; rendering it verbatim would be ~8,000 lines of `2024.3.0.0\Help\Data\...` with no judgment content, and the harvest channel truncates at 30k chars per read. The L1 map above IS the analytically load-bearing layer (the operator's ruling: the folder NAMES are the product map).

---

# PART II — Structural Analysis

## II.a Segmentation — how BY organizes its product world

**Judgment: it doesn't — not structurally.** The top level is a single **flat, alphabetical namespace of 360 product/module names** with zero grouping folders. There is no `Planning/` vs `Execution/` vs `Platform/` partition, no audience split (customer vs internal), no product-line grouping. Evidence: L1 runs `Adaptive Fulfillment...` -> `Yard Management` alphabetically, interleaving customer products (`Airline Revenue Optimizer`), internal microservices (`Commits Service`, `Approval Server`), doc-process areas (`PDDOC-Internal`, `Business Analysis for Warehouse`), and test stubs (`WAYLAND TEST FOLDER`) as peers.

The only real hierarchy is **below** L1, and it is purely mechanical: `Family / Version / Help-format / Flare-output`. So the organizing principle is **"one folder per documented thing, versioned, accreted over time"** — a **release-publishing catalog**, not a functional taxonomy. Segmentation must therefore be *inferred* from names, not read from structure. Inferring, the 360 cluster into ~8 domains (counts approximate, from name matching):

- **Supply-chain planning** (`Demand*`, `Master Planning`, `Sales and Operations Planning`, `Integrated Business Planning*`, `SCPO*`, `Enterprise Supply Planning`, `Factory Planner`, `Production Planning and Scheduling`)
- **Retail merchandising/planning** (`Assortment*`, `Space*`/`Planogram*`, `Category*`, `Merchandise Financial Planning*`, `Markdown*`/`Clearance*`/`*Pricing`, `Allocation*`, `Replenishment*`)
- **Logistics execution** (`Warehouse Management*`, `Warehouse Tasking/Execution`, `Transportation *` (~14 folders), `Yard Management`, `Labor*`, `Fulfillment*`, `Store Fulfillment*`)
- **Commerce / OMS** (`Distributed Order Management`, `Order Promising`/`Promiser`, `Customer Order*`, `Returns*`, `Web Commerce`, `Direct Commerce`)
- **Platform / infrastructure** (`Blue Yonder Platform`, `Luminate Platform Data Management`, `Common Services`, `*Service`, `Job Scheduler`, `Registry`, `Environment Manager`, `Infrastructure Services`)
- **Revenue / price optimization** (`Airline/Cargo/Hospitality/Rail/Tour Revenue Optimizer`, `*Price Optimizer`, `Travel Price Optimization`)
- **Industry prescriptions** (`IDSP for *`, `* - Industries Prescription`, `* Retail Prescription`) — see II.d
- **Internal / doc-process / test** (`PDDOC-Internal`, `PMGNPD Documentation`, `Business Analysis for *`, `Integration Test Automation Framework`, `Test*`, `WAYLAND TEST FOLDER`)

## II.b Naming conventions — raw material for deterministic auto-tagging

Strong, machine-parseable regularities (each is a candidate deterministic rule):

1. **Version tokens (L2):** `YYYY.Q.0.0` (e.g. `2024.3.0.0`), short form `YYYY.Q` (`2025.4`), and word forms (`Production`, `aspx-demo`). -> deterministic `version:` extraction + "collapse all versions to one product" rule.
2. **Doc-output markers (L4–L10):** `Help`, `Help_aspx`, `Data`, `content`, `resources`, `images`, `32x32`. -> deterministic **"generated-asset, not authored content"** filter; anything under `\Data\` or `\content\resources\` is Flare output.
3. **Brand/lineage in parentheses:** `(RedPrairie)`, `(SCE)`, `(SCPO)`, `(flexis)`, `(Commerce)`, `(IDEAS)`, `(ESO)`, `by Intellect`, `JDA Next` — encodes acquisition heritage. -> `heritage:` tag.
4. **Product-line prefixes:** `Cognitive *` (~15 families), `Luminate *` (~8), `IDSP for *` (~5), `Business Analysis for *` (~6), `Transportation *` (~14), `Warehouse *`, `Store *`, `Advanced *`, `Strategic *`, `Mobile *`, `Enterprise *`. -> prefix-based family grouping.
5. **Lifecycle suffixes:** `_OLD`, `_old`, `-Legacy`, `-Internal`, ` P`, ` - Marc`, and the sync-collision suffix `-HYB-<hash>` (`Cognitive Interface Migration-HYB-gpzdYOQu8SK`). -> `legacy:` / `internal:` / `duplicate:` flags.
6. **Acronym set:** MMS, PMM, MOCA, WMS, TMS, SCPO, IBP, MFP, CDP, IDSP, LDE, PDC, ABPP, SnOP/S&OP, ESO, SCE. -> acronym<->full-name synonym map.
7. **Anti-patterns to normalize:** misspelling `Componenet Management`; ampersand vs "and" (`Order Slotting & Scheduling` vs `Order Sequencing and Slotting`); the malformed extension `". xls"` (leading space) — see II.e.

## II.c Shape stats — where the mass actually sits

- **Mass is generated, not authored.** By extension: `.js` 23,445 (30.3%) + `.png` 17,249 (22.3%) + `.aspx` 5,039 + `.css` 2,539 + `.svg` 1,659 + `.gif` 747 + `.htm` 365 + `.mcwebhelp` 119 + `.chm` 9 + `.swf` 33 = **~51,200 files (~66%) are MadCap-Flare/WebHelp portal scaffolding.** The `.js` mass is Flare's per-topic search-index chunks (that is why the heaviest folders are all `\Data`). The **authored** layer is `.pdf` 22,412 (29%) + Office `.doc/.docx/.ppt/.pptx/.xls/.xlsx` ~965 (~1.2%). So ~30% of the corpus is real documents; ~66% is publish output; the rest is media/archives.
- **Mass by folder is dominated by dual-format doubling.** `Help` + `Help_aspx` per version doubles the footprint wherever both exist (IBP: 1,325+1,325, 457+457, 298+298).
- **Mass by family is anti-correlated with product prominence** (the single most important finding): the heaviest families are **platform/planning/integration/internal** (Blue Yonder Platform 8,807; IBP 4,646; Demand & Supply Planning 3,664; Integration Test Automation Framework 2,904; IDSP 2,676/2,418; PDDOC-Internal 2,048; Commits Service 2,017), while **flagship customer products are thin** (Transportation Management Solution 22; Luminate Demand Edge 43; Category Management Suite 63; Warehouse Management Solution 109). File weight measures **which team publishes Flare WebHelp per version into this library**, NOT product importance.
- **Depth:** wide at L2 (4,838 = 59% of folders), shallow thereafter; max depth 10, reached by a single Flare asset branch.

> **Load-bearing consequence for T2:** do NOT weight the ontology by file count. Counts reflect the documentation-publishing pipeline, not the product portfolio's shape or importance.

## II.d Taxonomy-axis verdict (industry x software)

**Verdict: the tree maps SUBSTANTIALLY but NOT CLEANLY onto the SOFTWARE axis. Usable as a seed, not adoptable as-is.**

- **Clean matches (the majority ~75%):** genuine BY software products/modules that drop straight onto the software axis — `Warehouse Management*`, `Transportation *`, `Demand Planning`, `Master Planning`, `SCPO*`, `Assortment*`, `Space Planning*`, `Category Management Suite`, `Merchandise Financial Planning`, `Order Promising`, `Blue Yonder Platform`, `Luminate *`, the `*Revenue Optimizer` family.
- **Axis-crossing entries (the industry axis is folded INTO the name):** `IDSP for High Tech Electronics` / `IDSP for Consumer Industries` / `IDSP for Automotive and Industrial Suppliers` / `IDSP for Aftermarket and Industrial Distributors`, `Demand and Supply Planning - Industries Prescription`, `Merchandise Financial Planning Retail Prescription`. These are **software x industry products in a single folder** — direct evidence that the operator's two axes are *entangled* in the source, and a rules layer must split them (`software:demand-supply-planning` + `industry:high-tech`).
- **Fits NEITHER axis (must be excluded or given a third axis):**
  - internal platform components — `Commits Service`, `Inventory Service`, `Approval Server`, `Common Services`, `Job Scheduler`, `Registry`, `Environment Manager`, `Infrastructure Services`, `Content Server`;
  - doc-process / org folders — `PDDOC-Internal` (2,048 files!), `PMGNPD Documentation`, `Business Analysis for *`, `Enterprise Architecture`;
  - tooling — `Integration Test Automation Framework` (2,904), `Magic Deployment Engine`, `Data Extractor`, `DMS to PDC Migration Toolkit Pipeline`;
  - test/placeholder — `Test`, `TestProduct`, `WAYLAND TEST FOLDER`, `CT2020`.
- **Not a maintained ontology.** Duplicates, rebrands, `_OLD` pockets, misspellings, and a sync-collision hash folder all coexist as L1 peers (II.e). This is **accreted publishing sediment with a strong product signal underneath**, not a curated axis. T2 can *seed* the software axis from these names but must run a normalize -> de-duplicate -> de-entangle-industry -> drop-non-product pass first.

## II.e Anomalies

- **Dead branch (0 files at depth):** `Workforce-Legacy` — folder exists, **0 files** at any depth (confirmed by recursive count). The clearest "organizational-sediment" artifact.
- **Near-dead / test stubs:** `TestProduct` (1), `WAYLAND TEST FOLDER` (1), `Test` (2), `Blue Yonder Orchestrator_old` (9), `CT2020`, `Dropzone`.
- **Legacy pockets (naming-flagged):** `Assortment Planning_OLD` (34), `Blue Yonder Orchestrator_old` (9), `Workforce-Legacy` (0), `* (RedPrairie)`, `JDA Next`, plus heritage brands `Inforem`, `WinDSS`, `SoftGrocer`, `Flowcasting`, `MOCA`, `MMS`.
- **Duplicated / fragmented concepts under different names** (same product, many peer folders — a de-dup target and the reason flagship counts look thin):
  - Warehouse Mgmt: `Warehouse Management`, `Warehouse Management Solution`, `Warehouse Management - Marc`, `Warehouse Management P`, `Warehouse Execution System`, `Dispatcher WMS`.
  - Transportation: ~14 `Transportation *` folders + `Real-Time Transportation Cloud` + `Freight *` + `Carrier *`.
  - Assortment: `Assortment`, `Assortment Optimization`, `Assortment Planning`, `Assortment Planning_OLD`, `Strategic Assortment`, `Shelf Assortment`, `Efficient Item Assortment`, `Luminate Assortment(+ Mobile)`, `Buying and Assortment Management`, `Retail.me Assortment Planning`.
  - Space: `Space Automation`, `Space Automation Professional`, `Space Management`, `Space Planning`, `Space Planning Solution`, `Space Planning Web`, `Strategic Space`, `Planning Space and Process Orchestration`.
  - Component: `Componenet Management` (misspelled), `Component Management`, `Component and Supplier Management`, `Portfolio Component Management`.
- **Sync-collision artifact:** `Cognitive Interface Migration-HYB-gpzdYOQu8SK` sitting beside `Cognitive Interface Migration` — a OneDrive/SharePoint `-HYB-<hash>` conflict-rename promoted to a first-class L1 "product."
- **Dual-format doubling:** `Help` + `Help_aspx` twins inflate file mass ~2x wherever both exist.
- **Data-hygiene tells:** malformed extension `". xls"` (leading space, 1 file); misspelling `Componenet`.

## II.f Candidate product-tag vocabulary v0 — PROPOSAL (operator ratifies in T1)

Derived deterministically from L1 name clusters. `tag <- source folders (examples)`. **Not decided — a ratification proposal.**

**Software-axis product tags**
- `wms` <- Warehouse Management*, Warehouse Execution System, Warehouse Tasking, Dispatcher WMS
- `tms` <- Transportation Management*, Transportation Planner/Modeler/Optimization/Rating, Real-Time Transportation Cloud
- `demand-planning` <- Demand, Demand Planner/Manager, Cognitive Demand Planning, Luminate Demand Edge, Forecasting for Retail
- `supply-planning` <- Master Planning, Enterprise Supply Planning, Supply Chain Planner, Production Planning and Scheduling
- `ibp-sop` <- Integrated Business Planning*, Sales and Operations Planning, Executive SnOP Workbench
- `scpo` <- SCPO General, Inventory Optimization (SCPO), Replenishment Interval Optimization (SCPO)
- `replenishment` <- Replenishment for Retail, Advanced/Cognitive/Dynamic Replenishment, Vendor Managed Replenishment
- `assortment` <- Assortment*, Shelf/Strategic/Efficient Item Assortment, Luminate Assortment
- `space-planning` <- Space Planning*, Space Management, Space Automation*, Planogram*
- `category-mgmt` <- Category Management Suite, CategoryAdvisor, Category Knowledge Base
- `mfp` <- Merchandise Financial Planning*
- `pricing-markdown` <- Price Management, Markdown Optimization, Clearance Price*, Strategic/Target Pricing, Fresh Markdown Optimization
- `promotions` <- Promotions Management/Optimization*, PromoPlanner, Trade Promotions Management
- `order-mgmt` <- Distributed Order Management, Order Promising/Promiser, Customer Order*, Order Services
- `fulfillment` <- Fulfillment*, Store Fulfillment*, Distribution Center Fulfillment*, Adaptive Fulfillment and Warehousing
- `returns` <- Returns Management Service, Returns Orchestration, Online/In-Store Returns, Warehouse Returns*
- `store-ops` <- Store*, Enterprise Store Operations, Store Execution*, Mobile *Connect
- `workforce-labor` <- Workforce*, Warehouse Labor Management, Advanced Labor Forecasting, Labour Capacity UI
- `revenue-optimization` <- Airline/Cargo/Hospitality/Rail/Tour Revenue Optimizer, *Price Optimizer, Travel Price Optimization
- `platform` <- Blue Yonder Platform, Luminate Platform Data Management, Common Services, Mobile Platform

**Industry-axis tags (de-entangled from folder names)**
- `industry:high-tech` <- IDSP for High Tech Electronics
- `industry:consumer` <- IDSP for Consumer Industries
- `industry:automotive` <- IDSP for Automotive and Industrial Suppliers
- `industry:aftermarket-distribution` <- IDSP for Aftermarket and Industrial Distributors
- `industry:retail` <- * Retail Prescription, Forecasting/Replenishment/Performance Management for Retail
- `industry:manufacturing` <- Manufacturing ABPP/Foundation, Factory Planner, Make-to-Order, Build To Order

**Control tags (exclude / quarantine — do NOT enter the product ontology)**
- `legacy` <- *_OLD, *_old, *-Legacy, * (RedPrairie), JDA Next, Inforem, WinDSS, SoftGrocer
- `internal-component` <- *Service, Approval Server, Common Services, Job Scheduler, Registry, Environment Manager, Infrastructure Services
- `doc-process` <- PDDOC-Internal, PMGNPD Documentation, Business Analysis for *, Enterprise Architecture
- `tooling` <- Integration Test Automation Framework, Magic Deployment Engine, Data Extractor, *Migration Toolkit*
- `test-stub` <- Test, TestProduct, WAYLAND TEST FOLDER, CT2020
- `duplicate-collision` <- *-HYB-<hash>

---

## Provenance / reproducibility

- All counts from `Get-ChildItem` metadata enumeration (T0). Zero file-content access; guard v3 logged every command as `T0-ALLOW`.
- Directory/file/family/depth totals and the extension histogram are **exhaustive** (full-tree recursive counts). The top-40 heaviest folders and the 24 per-family counts are **direct measurements**. Per-level dir counts are **derived** from cumulative `-Depth k` counts (exact). Domain groupings in II.a and the II.f vocabulary are **name-based inference** over the exhaustive L1 list — flagged as proposal, not measurement.
- One approximation stated honestly: the L2 count (4,838) mixes true version folders with a minority of top-level guide folders; not separated (would require calculated grouping, which the T0 allow-list forbids).
