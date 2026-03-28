# AI Council Debate: # Council Question: Obsidian Vault Structure — Folders vs Dimensions

## Context

**Date:** 2026-03-20 19:25:18
**Panel:** deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta, gpt-5.4
**Synthesizer:** claude (non-participant)
**Rounds:** 2
**Duration:** 298.7s
**Mode:** full (4-model panel)
**Source:** council_inbox\COUNCIL_vault_structure_dimensions.md

---

## Round 1: Initial Responses

### Gemini (gemini-3.1-pro-preview)

## Position
I strongly recommend **Option D (Hybrid: Flat Extracted + Curated Structure)**. From an integration and systems architecture perspective, this structure correctly decouples storage routing (the physical layer) from semantic meaning (the logical layer), enforcing strict trust boundaries between automated ingestion pipelines and human-authored content.

## Rationale
*   **Enforces Trust Boundaries (Q2 & 5-year test):** By separating `knowledge/` (machine-generated, high-volume) from `guides/` and `projects/` (human-curated, high-value), you isolate the blast radius of ingestion errors. Extracted data should be treated as an immutable cache; human data is your mutable state. Folders should reflect data lifecycle and governance, not semantic meaning.
*   **Eliminates Routing Brittleness (Q4):** `routing_map.yaml` becomes effectively static. The CKE pipeline dumps all extractions into `knowledge/`, eliminating the integration risk of ingestion pipelines failing because a folder was renamed to fit a new mental model. A full, idempotent `corp index rebuild` is vastly superior to event-driven tracking—it avoids state desyncs and race conditions, and rebuilding an SQLite FTS5 index for 5,000 notes takes milliseconds.
*   **Zero-Triage Scalability (Q1):** With your ADHD constraint, any system requiring manual categorization is an architectural threat. Moving to flat extraction forces reliance on metadata and Dataview dashboards. This is the only paradigm that survives the 5-year / 20,000-note test. File trees are an anti-pattern for multidimensional knowledge retrieval.
*   **Schema-Driven Extensibility (Q3):** Semantic folders are a 1D constraint on an nD reality. When adding new dimensions (e.g., "industry_vertical"), they must be added as *new fields* in the frontmatter schema, governed strictly by the `corp-os-meta` taxonomy. Overloading existing fields like `domains` leads to data pollution. `corp-os-meta` acts as the single source of truth (the API contract) for what metadata is valid.

## Trade-offs
*   **File Explorer Utility:** You permanently forfeit the ability to casually browse the `knowledge/` folder using the native file tree. A single folder with 3,000+ notes will be visually overwhelming and visually useless.
*   **Dashboard Dependency:** You are shifting the cognitive load from "where do I put this?" to "how do I query this?". Your Dataview dashboards (`00_dashboards`) transition from being a "nice-to-have" feature to mission-critical infrastructure for human orientation.
*   **Namespace Collisions:** In a flat folder, file names must be globally unique. Extracted notes must rely on robust, deterministic naming conventions (e.g., `[Source Abbreviation] - [Topic] - [Timestamp]`) to prevent pipeline overwrite errors.

## Risks
*   **Obsidian UI Performance Collapse:** Rendering 5,000+ files in a single folder can cause the native Obsidian File Explorer to lag, especially on mobile devices via Obsidian Sync. 
    *   *Mitigation:* Use Obsidian's native settings or the "Hider" plugin to physically hide the `knowledge/` folder from the file explorer view. Navigate exclusively via the Quick Switcher, Search, and Dataview dashboards.
*   **Metadata Drift / Taxonomy Sprawl:** Allowing arbitrary creation of new frontmatter fields will slowly degrade the FTS5 search reliability and clutter the system.
    *   *Mitigation:* Implement strict schema validation in the CKE extraction pipeline. The pipeline should reject or flag notes with metadata keys not explicitly defined in `corp-os-meta/taxonomy.yaml`. All new dimensions require a formal commit to `corp-os-meta`. 
*   **Dataview Query Bottlenecks:** Dataview queries evaluating 5,000+ notes dynamically on load can severely degrade Obsidian's startup and rendering time.
    *   *Mitigation:* Since you already have an FTS5 index (SQLite) powered by `corp retrieve`, do not rely purely on Obsidian Dataview for heavy lifting. Expose the SQLite index to Obsidian via a custom plugin or local API, or limit Dataview queries strictly by indexable fields (e.g., `FROM "knowledge" WHERE contains(client, "X")`) rather than complex runtime string evaluations.

*Latency: 24.91s | Tokens: 4740*

### Deepseek (deepseek-reasoner)

## Position
Recommend **Option D (Hybrid flat + curated)** with one modification: split the flat `knowledge/` folder into **date-based subfolders** (e.g., `knowledge/2025/`) to avoid Obsidian UI performance degradation while preserving metadata‑based retrieval.

## Rationale
- **Decouples storage from meaning**: Folders become a **storage‑layer concern** (origin + date), while dimensions remain in frontmatter metadata. This eliminates the folder‑vs‑metadata conflict.
- **Scales to 20k+ notes**: Date‑based partitioning prevents filesystem/UI slowdowns (Obsidian can lag with 3k+ files in one folder) while keeping routing rules simple (`knowledge/*` → same metadata processing).
- **Future‑proofs dimension expansion**: New attributes (industry vertical, competitive positioning) become metadata fields, not folder restructures. The corp‑os‑meta taxonomy governs values, ensuring consistency.
- **Aligns with actual usage patterns**: Retrieval already uses FTS5 + metadata; human browsing uses Dataview dashboards. Folders serve only as a stable, low‑cognitive‑load filing system.

## Trade-offs
- **Loss of semantic folder browsing**: Users cannot intuitively browse by topic in the file tree—they must use Dataview dashboards or saved searches.
- **Increased reliance on metadata quality**: Mis‑tagged notes become “lost” since folder location provides no semantic fallback. Requires robust extraction validation.
- **Minor routing‑map complexity**: Date‑based subfolders require a wildcard pattern (`knowledge/*/*`) but remain far simpler than per‑category routing.

## Risks
1. **Obsidian performance with flat folders**: >3k notes in one folder can cause UI lag. *Mitigation*: Date‑based subfolders (year/month) keep per‑folder count <500; automated note mover plugin can file notes by creation date.
2. **Metadata schema drift**: Uncontrolled addition of dimensions leads to inconsistent tagging. *Mitigation*: Enforce dimension changes via corp‑os‑meta taxonomy PRs; run weekly validation scripts to report missing/ambiguous tags.
3. **Over‑reliance on Dataview**: If Dataview queries break, knowledge discovery halts. *Mitigation*: Maintain a fallback keyword‑based search dashboard and export critical views as static markdown quarterly.
4. **Source‑origin context loss**: Date‑based folders obscure whether a note came from training vs. competitive docs. *Mitigation*: Keep `source_type` as a required frontmatter field; add a Dataview dashboard grouping by source_type.

**Implementation order**:  
1. Move existing notes to `knowledge/2024/` and `knowledge/2025/` by created date.  
2. Update routing_map.yaml to route all CKE extractions to `knowledge/{year}/`.  
3. Create Dataview dashboards for each major dimension (products, domains, source_type).  
4. Archive old folders but keep redirect notes (via Obsidian `redirect` plugin) for 90 days.

*Latency: 76.45s | Tokens: 4495*

### Openai (gpt-5.4)

## Position
Choose **Option D: hybrid flat extracted + curated structure**, with one refinement: keep extracted knowledge in a single `knowledge/` folder, keep human-authored assets in `guides/`, and treat **folders as operational containers only, never as semantic classification**.  
For scale, govern meaning entirely through frontmatter schema and corp-os-meta taxonomies, not through subfolders.

## Rationale
- **It matches how retrieval already works.** Your FTS5 + frontmatter stack ignores folders, so semantic foldering would create a second, weaker classification system that competes with the real one.
- **It minimizes cognitive and operational overhead for a solo operator.** With one vault writer, zero manual triage, and ADHD constraints, the right design is the one with the fewest places to make mistakes: `extracted -> knowledge`, `project -> projects/{client}`, `manual -> guides`.
- **It separates “how a note is produced” from “what a note means.”** That is the key architectural distinction. Folder = lifecycle/ownership container. Metadata = dimensions. Mixing the two is what causes brittleness.
- **It scales better to future dimensions.** Industry, implementation pattern, GTM, competitive angle, methodology, and verticals are all orthogonal dimensions. Adding them as metadata is cheap; encoding them in folders will force repeated restructures.
- **It is the most survivable option for the 5-year test.** At 20,000 notes, any semantic folder tree becomes either too shallow to be useful or too deep to maintain. A flat operational structure plus dashboards, search, and metadata still works.

## Trade-offs
- **You give up casual sidebar browsing of extracted notes.** A folder with 3,000-5,000 notes is not pleasant to scroll. You are explicitly choosing search, bookmarks, dashboards, and filtered views over tree navigation.
- **Obsidian UX becomes more metadata-dependent.** If frontmatter quality degrades, discoverability degrades. This puts pressure on extraction quality and taxonomy hygiene.
- **You lose the illusion of neat categorization.** Some users feel more comfortable seeing `competitive/`, `training/`, `product_docs/`; this structure will feel less “organized” at first even though it is more correct architecturally.
- **Dataview dashboards become a core UX dependency.** If dashboards are poor, stale, or incomplete, the flat structure will feel hostile.
- **Curated vs extracted becomes the main visible distinction.** That’s good operationally, but it may not satisfy every instinct to “browse by topic.”

## Risks
- **Risk: The flat `knowledge/` folder becomes unusable in the Obsidian sidebar.**  
  **Mitigation:** Design for “never browse `knowledge/` directly.” Create landing dashboards by product, topic, domain, source_type, trust_level, and recent additions. Pin/bookmark those views. Treat the sidebar as file storage, not navigation.

- **Risk: Metadata drift makes retrieval worse over time.**  
  **Mitigation:** Establish a lightweight schema governance model:
  - fixed core fields: `products`, `topics`, `domains`, `source_type`, `trust_level`, `client`
  - new orthogonal dimensions become new fields, not overloaded `domains`
  - controlled vocabularies live in `corp-os-meta`
  - add validation during extraction/indexing to reject or warn on unknown values

- **Risk: `domains` becomes a junk drawer as new concepts emerge.**  
  **Mitigation:** Do **not** keep stretching `domains` to absorb implementation, vertical, GTM, or PM concepts. Use:
  - `domains` for broad capability areas only
  - new field for genuinely new axes, e.g. `industries`, `implementation_patterns`, `competitive_context`, `gtm_motion`, `methodologies`
  - `taxonomy.yaml` for allowed values and aliases within each field

- **Risk: Folder renames or moves still break routing assumptions.**  
  **Mitigation:** Simplify routing so there are very few routable destinations. Full event-driven tracking is unnecessary for a solo-user vault. A full `corp index rebuild` is sufficient if:
  - rebuild is fast enough to run on demand
  - note identity is based on stable note IDs/content hashes, not paths alone
  - path changes trigger re-scan reconciliation during rebuild

- **Risk: Future scale to 20,000 notes exposes performance or management pain.**  
  **Mitigation:** Future-proof now by:
  - keeping only 5-6 top-level folders
  - avoiding semantic subfolder growth
  - standardizing frontmatter schema early
  - building dashboards from metadata, not path conventions
  - ensuring indexing/search treat path as incidental metadata, not identity

---

### Concrete recommendations to the 5 questions

#### 1) Flat vs hierarchical for extracted knowledge?
**Recommendation:** Flat is acceptable and preferable for extracted knowledge.

Why:
- Obsidian folder browsing is not your primary retrieval model.
- Human browsability at 5,000 notes should come from dashboards/search, not file trees.
- Hierarchy gives false comfort but poor truthfulness in a multi-dimensional knowledge base.

Practical rule:
- `knowledge/` = flat
- `projects/{client}/` = hierarchical, because client scope is naturally singular and operationally useful
- `guides/` = small curated structure, hand-organized as needed

#### 2) Should folders reflect source-origin or semantic-meaning?
**Recommendation:** Neither, for extracted notes. Use folders for **operational role**, not meaning.

That means:
- `knowledge/` = machine-generated/extracted knowledge
- `projects/` = client-scoped working material
- `guides/` = human-authored reusable content
- `dashboards/`, `templates/`, `system/` = support layers

If you feel a need to preserve source-origin, store it in metadata:
- `source_type`
- possibly `source_origin` or `source_collection`
- original file/path reference in frontmatter

This is better than subfolders because source-origin can still be queried without creating routing sprawl.

#### 3) Dimension expansion strategy
**Recommendation:** Use a **3-tier governance model**:

1. **New field in frontmatter** when the concept is a new orthogonal axis  
   Examples: `industries`, `implementation_patterns`, `competitive_context`, `methodologies`

2. **New value in an existing field** only when it truly belongs to that axis  
   Example: adding a new `source_type` value like `analyst_report`

3. **taxonomy.yaml / corp-os-meta update** whenever the field uses controlled vocab or aliases  
   This should be the canonical registry for allowed values, aliases, normalization, and descriptions

Decision rule:
- If the concept answers a different question, create a new field.
- If it answers the same question with another option, add a new value.
- If users may say it multiple ways, add taxonomy aliases.

Example:
- `retail` is not a domain; it is an **industry**
- `SAP CPI` is not a domain; likely a **technology** or **implementation_pattern**
- `competitive displacement` is not a domain; it belongs in **competitive_context**
- `rapid deployment` is not a domain; it belongs in **delivery_motion** or **implementation_pattern**

This is the key to avoiding a bloated `domains` field.

#### 4) Dynamic folder awareness
**Recommendation:** A full rebuild remains sufficient; do not build event-driven tracking now.

Why:
- Solo user
- single writer
- low operational maturity requirement
- folder paths are no longer semantically important in the recommended model

What to do instead:
- Keep routing destinations very stable and few
- Make `corp index rebuild` cheap and reliable
- Store path as metadata, but not as business logic
- Use stable note IDs in frontmatter if possible, so moves/renames do not create identity ambiguity

Event-driven tracking is a premature complexity unless rebuild time becomes painful or multiple tools start writing concurrently.

#### 5) The 5-year test
**Recommendation:** The structure that survives is:

```text
vault/
  knowledge/      # all extracted knowledge, flat
  projects/       # client-scoped notes, subfolder per client
  guides/         # curated human-authored reusable notes
  dashboards/     # dataview and navigation surfaces
  templates/
  system/
```

Why this survives:
- top-level folders stay stable even as dimensions explode
- dimensions are schema, not filesystem
- new note types don’t require reclassification of old notes
- dashboards can evolve continuously without moving files
- the architecture remains understandable to future-you

---

### Final pragmatic call
Your lean is right.  
Adopt **Option D**, but be disciplined about one principle:

> **Folders answer “who/what process owns this note?” Metadata answers “what is this note about?”**

If you hold that line, the vault remains understandable, automation stays simple, and you avoid a painful refactor at 5,000+ notes.

*Latency: 32.19s | Tokens: 4118*

### Grok (grok-4.20-beta)

**Position**

Reject the hybrid-flat consensus (Option D) and the assumption that "folders are just for humans and therefore disposable." Use **semantic top-level folders based on the 8 stable knowledge domains**, with everything else (source origin, client, topics, etc.) living exclusively in metadata. The vault becomes:

```
vault/
  dashboards/
  guides/           # human-authored only
  projects/         # per-client subfolders
  Platform & Architecture/
  Supply Chain Planning/
  WMS & Logistics/
  Commerce & OMS/
  Data & Analytics/
  Security & Compliance/
  Integration & APIs/
  Business & Commercial/
  system/
```

Notes are filed into exactly one domain folder by `corp-by-os` at extraction time using the canonical `KNOWLEDGE_DOMAINS` list. All other dimensions are metadata only.

**Rationale**

- The 8 domains are the *only* dimension that has proven stable and mutually exclusive enough to survive the 5-year test. Everything else Rob has identified (industry verticals, implementation patterns, competitive positioning, GTM, etc.) is inherently multi-dimensional and will explode into 50+ overlapping values. Using folders for the stable dimension and metadata for the volatile ones is the only sane separation.
- Human spatial memory is not optional, even for someone with ADHD. "I know this is a WMS integration thing" maps to muscle memory in the sidebar. Pure Dataview dashboards and graph view work great until you have 20,000 notes and need to *explore* rather than *retrieve*. The consensus pretends Rob will only ever search. History shows knowledge workers still browse.
- Source-origin folders (Options B and C) are actively misleading. A training deck that contains the single best explanation of SAP CPI integration does not belong in "training/" for the next 8 years of Rob's career. The folder should tell you what the note *is about*, not where the bits originally came from.
- Routing complexity is overstated. The domain classifier is deterministic (one field in corp-os-meta). `routing_map.yaml` becomes trivial and stable. Folder renames become rare events instead of constant ones.
- Obsidian's own features (graph, Dataview, bookmarks, starred) work *better* with sensible folders than against them. A note in "WMS & Logistics/" still shows up in every relevant dashboard via metadata.

**Trade-offs**

- Give up the aesthetic purity of "flat extracted knowledge." Some notes will be filed in a domain that feels slightly imperfect. This is acceptable because the retrieval engine ignores folders anyway.
- Give up the fantasy of zero folder maintenance. There will be occasional moves when the domain classifier is wrong (rare).
- Give up the ability to see "all extracted notes in chronological order" in the file explorer. This is solved by Dataview or a simple `created` sort in the sidebar if truly needed.
- Slightly higher cognitive load when the extraction pipeline decides the domain (but this is the same load that already exists in choosing `domains` frontmatter).

**Risks and Mitigations**

- **Risk: Domain classifier is consistently wrong.**  
  Mitigation: Make `corp-by-os` write the chosen domain in frontmatter *and* folder. Add a Dataview table dashboard called "Domain Misclassifications" that shows notes where folder and frontmatter disagree. Review once per quarter.

- **Risk: One note genuinely belongs in multiple domains.**  
  Mitigation: Force single domain at folder level (the primary one). Use the `domains` frontmatter array for secondary memberships. This is the correct separation of concerns.

- **Risk: Rob stops maintaining the 8 domains and they drift.**  
  Mitigation: The domains are defined in `corp-os-meta` as the single source of truth. The routing code literally cannot create a folder outside that list. Governance is enforced by code.

- **Risk: 5,000+ notes still feels overwhelming in the sidebar.**  
  Mitigation: Collapse all folders by default. Use Obsidian's "Folder Note" plugin + MOCs at the top of each domain folder. The dashboards already planned for every dimension remain the primary entry point.

- **Risk: Future Rob in 2031 hates the 8 domains.**  
  Mitigation: They are the only dimension that comes from the *product taxonomy itself*. Blue Yonder is unlikely to restructure its entire portfolio into 47 new top-level categories. This is the least volatile possible choice.

The hidden assumption everyone is making is that because the *machine* retrieval doesn't need folders, *humans* don't need them either. This is classic engineer brain. The machine should serve the human, not the other way around. Structure the filesystem for the wetware. Let metadata serve the silicon.

*Latency: 15.02s | Tokens: 4453*

## Round 2: Critique

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, my primary concerns with any knowledge management ecosystem are **trust boundaries, supply chain integrity of ingested data, and the interoperability contract** between the extraction pipeline (CKE), the storage layer (Obsidian), and the retrieval engine (FTS5). 

Semantic folders represent a brittle integration pattern. They tightly couple the physical storage layer to the logical business layer. When semantic definitions change, the physical integration breaks. 

Here is my architectural evaluation of the council's proposals, flagging threat surfaces and integration risks first.

---

### Evaluation of Proposal A (Date-based subfolders)
* **Position:** Partially Agree (Agree with hybrid structure; disagree with date-based partitioning).
* **Strongest point:** Correctly identifies the physical limitation of the client application (Obsidian UI degradation with >3,000 files in a single directory).
* **Weakest assumption:** Assumes chronological creation date is a stable routing metric for pre-sales knowledge. It conflates the *ingestion event* with the *asset lifecycle*. 
* **Overlooked risks (Threat/Integration):** 
    * **Sync Conflicts and Link Rot:** If a note is updated later and a script moves it to a new year's folder, internal markdown links break, and Obsidian Sync may generate duplicate file conflicts.
    * **State Desync:** Date-based routing requires wildcard pathing (`knowledge/*/*`). If the CKE pipeline and Obsidian write simultaneously across different date boundaries, you risk race conditions and orphaned files.

### Evaluation of Proposal B (Strict Trust Boundaries)
* **Position:** Strongly Agree.
* **Strongest point:** Perfectly identifies that folders must represent **data lifecycle and governance (trust boundaries)** rather than semantic meaning. Treating extracted data as an "immutable cache" and human data as "mutable state" is textbook system architecture.
* **Weakest assumption:** Dismisses the Obsidian file explorer as "visually useless" without providing a resilient fallback. If the FTS5 SQLite index or Dataview plugins crash, the user is left blind in an unnavigable system.
* **Overlooked risks (Threat/Integration):** 
    * **Namespace Collisions:** A massive flat folder introduces a high risk of file overwrite vulnerabilities. If the CKE pipeline extracts two documents with similar titles from different source systems, one overwrites the other. Strict, hash-appended deterministic naming is required, which this proposal only briefly mentions.

### Evaluation of Proposal C (Operational Containers & 3-Tier Governance)
* **Position:** Agree.
* **Strongest point:** The "3-tier governance model" for dimension expansion is an excellent, interoperable API contract. It establishes strict rules for when to alter the schema (new field) vs. the payload (new value), ensuring the FTS5 engine doesn't break over time.
* **Weakest assumption:** Assumes `corp index rebuild` is infinitely scalable and cheap. Scanning and parsing 20,000 markdown files over a synced filesystem will eventually hit I/O bottlenecks or trigger Obsidian Sync rate limits.
* **Overlooked risks (Threat/Integration):**
    * **Ingestion Validation:** The proposal suggests adding validation to reject unknown values but relies on the user not to manually mess it up. Without a pre-commit hook or pipeline-enforced schema validation, malformed metadata *will* enter the vault, silently failing FTS5 queries.

### Evaluation of Proposal D (Semantic Top-Level Folders)
* **Position:** Strongly Disagree.
* **Strongest point:** Recognizes the reality of human spatial memory and the risk of complete reliance on a secondary index (Dataview/FTS5) for system navigation.
* **Weakest assumption:** Dangerously assumes the "8 knowledge domains" are permanently stable. Corporate product suites undergo M&A, divestitures, and re-branding constantly. Tying physical infrastructure to marketing/product taxonomy is an architectural anti-pattern that guarantees future refactoring.
* **Overlooked risks (Threat/Integration):**
    * **Ingestion Hallucination Vulnerability:** By forcing the CKE extraction pipeline to determine the physical folder via an LLM/classifier, you introduce a non-deterministic failure point into your physical routing. If the AI misclassifies a file, it is written to the wrong path. 
    * **Coupled Failure Domains:** If `routing_map.yaml` must be updated every time Blue Yonder acquires a new product vertical, the integration pipeline becomes the bottleneck for the knowledge worker.

---

### Revised Recommendation: The "Trust-Zoned Hybrid" Architecture

To ensure defense-in-depth, zero integration brittleness, and safe scalability to 20,000 notes, you must decouple physical storage from semantic logic while enforcing strict data validation. 

Adopt **Option D**, but implemented as **Security & Lifecycle Trust Zones**. 

**1. Physical Structure (The Trust Zones)**
Folders will purely define the authorization, mutation, and source-trust levels of the data. 
```text
vault/
  01_extracted_cache/  # Trust Level: Machine. Immutable by user. Flat.
  02_curated_state/    # Trust Level: Human. Mutable. Hierarchical.
  03_client_projects/  # Trust Level: Confidential. Scoped by client entity.
  00_dashboards/       # View Layer.
  90_system/           # Config and Schemas.
```
*   *Integration Rule:* The CKE pipeline writes **only** to `01_extracted_cache`. `routing_map.yaml` is hardcoded to this single destination. It never needs updating.
*   *Security Rule:* Notes in `01_extracted_cache` must have collision-resistant filenames (e.g., `[Source_ID] - [Title] - [ShortHash].md`) to prevent pipeline overwrites.

**2. Metadata as the API Contract (Interoperability)**
Implement Proposal C's 3-tier governance model, but enforce it at the ingestion boundary.
*   `corp-os-meta/taxonomy.yaml` is your schema definition. 
*   **The Pipeline Shield:** The CKE pipeline *must* validate the extracted metadata against `taxonomy.yaml` *before* writing to Obsidian. If a dimension is missing or invalid, it is tagged `status: triage_failed` but still written to the cache. This prevents poison-pill data from corrupting your FTS5 index.

**3. Resolving the Flat-Folder UI Threat**
Do not use date-based subfolders. Do not use semantic subfolders. 
If Obsidian's UI degrades with 5,000+ files in `01_extracted_cache`, implement **Source-System Partitioning** (a variation of Option C) strictly as an operational partition, not a semantic one:
```text
vault/
  01_extracted_cache/
    sys_sharepoint/
    sys_confluence/
    sys_local_rfp/
```
Source-system origin is a physically immutable property of the data payload. It never changes, requires zero LLM classification, and evenly distributes file counts without introducing semantic coupling.

**4. Event-Driven vs. Full Rebuilds**
Stick to idempotent `corp index rebuilds`. Event-driven file tracking over a synced filesystem (Obsidian Sync) is highly susceptible to race conditions and missed filesystem events. Relying on FTS5 to drop and rebuild the SQLite index is fundamentally safer and guarantees the search index perfectly matches the physical state of the vault.

**Summary:**
Do not build your filesystem for your human spatial memory if it compromises your data pipeline. Build the filesystem for pipeline resilience and collision avoidance. Use Dataview and FTS5 to build the interface for your brain.

*Latency: 34.91s | Tokens: 10517*

### Deepseek (deepseek-reasoner)

## Evaluation of Proposals

**Proposal A (Date-partitioned flat)**
- **Agree partially** with the performance rationale, but disagree with date-based partitioning.
- **Strongest point:** Acknowledges Obsidian UI performance degradation with >3k files in one folder—a real but overstated risk.
- **Weakest assumption:** That date-based folders solve performance without semantic cost. Dates are irrelevant for browsing; they add navigation friction without solving the core human-orientation problem.
- **Overlooked risks:** 
  1. Date-based partitioning forces chronological thinking in a system where relevance is domain/context-dependent.
  2. Routing complexity increases (wildcards, year-boundary logic) for negligible benefit.
  3. Creates false sense of organization—still doesn’t help human browsing by topic/product.

**Proposal B (Strict flat + trust boundaries)**
- **Agree** with core principle, but disagree on UI mitigation strategy.
- **Strongest point:** Correctly enforces trust boundaries between machine-generated and human-curated content—critical for scalability.
- **Weakest assumption:** That hiding the `knowledge/` folder solves UI performance. Obsidian’s core indexing and graph rendering still process all files; hiding merely shifts cognitive load elsewhere.
- **Overlooked risks:**
  1. Complete reliance on dashboards creates a single point of failure in knowledge discovery.
  2. No fallback navigation for when dashboards break (plugin conflicts, query errors).
  3. Ignores human spatial memory entirely—contradicts established UX principles for knowledge workers.

**Proposal C (Flat + operational folders)**
- **Agree strongly** with governance model, but disagree on dismissing human browsing needs.
- **Strongest point:** The 3-tier dimension governance model (new field vs. new value vs. taxonomy) is architecturally sound and prevents metadata sprawl.
- **Weakest assumption:** That “never browse `knowledge/` directly” is sustainable. Humans need multiple discovery paths; forcing one interaction mode reduces resilience.
- **Overlooked risks:**
  1. Assumes Dataview dashboards will always work perfectly at scale (they won’t—query performance degrades).
  2. Doesn’t address the psychological cost of losing visual hierarchy for a solo operator with ADHD.

**Proposal D (Domain-folders + metadata)**
- **Disagree** on semantic folders, but agree on human spatial needs.
- **Strongest point:** Correctly identifies that human spatial memory matters and that pure flat structures ignore real-world browsing behavior.
- **Weakest assumption:** That the 8 domains are stable enough for folder classification. In pre-sales, notes regularly span domains (e.g., “SAP CPI integration” touches Platform, WMS, Integration, and Security).
- **Overlooked risks:**
  1. Forces arbitrary single-domain assignment for multi-domain notes.
  2. Increases routing complexity and folder maintenance.
  3. Creates semantic competition: folder vs. metadata domain field.

## Revised Recommendation

**Adopt a modified Option C with performance-optimized browsing layers, not date-based partitioning.**

### Core Structure
```
vault/
  knowledge/                    # All machine-extracted notes (flat)
    .index/                    # Hidden folder for navigation aids
      by_product/              # Symbolic links or stub notes
      by_domain/               # Manually maintained MOCs
      by_source/               # Source-type overviews
  projects/{client}/           # Client-scoped notes
  guides/                      # Human-authored playbooks
  dashboards/                  # Dataview queries
  templates/
  system/
```

### Critical Modifications

1. **Keep `knowledge/` flat** for extraction pipeline simplicity and routing stability.
2. **Add a hidden `.index/` subfolder** containing:
   - Manually maintained Map-of-Content (MOC) notes for each major dimension (products, domains, source types).
   - These MOCs use Dataview queries but are human-readable overviews.
   - Optionally, use Obsidian’s “folder notes” plugin to make each MOC act as a folder surrogate.
3. **Implement strict performance optimizations:**
   - Configure Obsidian to collapse `knowledge/` by default in file explorer.
   - Use `corp retrieve` as primary search, not Dataview live queries.
   - Cache dashboard results as static notes weekly.
4. **Dimension governance per Proposal C’s 3-tier model:**
   - New orthogonal axes → new frontmatter fields.
   - New values within existing axes → taxonomy.yaml updates.
   - All changes require corp-os-meta PR with validation scripts.

### Rationale

1. **Solves UI performance without semantic compromise:**  
   Hiding `knowledge/` and providing curated MOCs in `.index/` gives human-orientation points without polluting the extraction pipeline. This is superior to date-based folders (Proposal A) or domain-folders (Proposal D).

2. **Preserves trust boundaries (Proposal B’s strength):**  
   Machine-extracted content remains immutable and separate from human-curated navigation aids. The `.index/` folder is manually updated, providing a clear separation.

3. **Addresses human spatial memory (Proposal D’s insight):**  
   MOCs in `.index/` serve as “virtual folders” that can be organized multi-dimensionally. For example, a “WMS SAP Integration” note appears in:
   - `.index/by_product/WMS.md`
   - `.index/by_domain/Integration & APIs.md`
   - `.index/by_source/training.md`
   
   Without actually moving the file.

4. **Scalable to 20k notes:**  
   The flat `knowledge/` folder scales indefinitely. Navigation scales via MOCs that can be split hierarchically (e.g., `.index/by_product/WMS/Integration.md`).

5. **Minimal routing complexity:**  
   Extraction pipeline still dumps to `knowledge/` flat. Only one routing rule. MOCs are manually updated during taxonomy changes (infrequent).

### Implementation Sequence

1. **Phase 1 (Foundation):**
   - Move all extracted notes to `knowledge/` (flat).
   - Update routing_map.yaml to single rule: `extracted → knowledge/`.
   - Run `corp index rebuild` to validate.

2. **Phase 2 (Navigation):**
   - Create `.index/` with initial MOCs using Dataview queries.
   - Configure Obsidian to hide `knowledge/` from sidebar.
   - Pin key MOCs to Obsidian’s starred items.

3. **Phase 3 (Performance):**
   - Implement weekly dashboard caching.
   - Add validation script for metadata consistency.
   - Set up `corp retrieve` as default Quick Switcher command.

4. **Phase 4 (Governance):**
   - Document dimension addition process in corp-os-meta.
   - Create template for new MOCs when dimensions are added.

### Quantifiable Trade-offs

| Aspect | Flat + MOCs | Date-folders | Domain-folders |
|--------|-------------|--------------|----------------|
| Routing rules | 1 | 1 + wildcards | 8 + updates |
| Notes moved on restructure | 0 | Up to 100% | Up to 100% |
| Human browsing paths | Multi-dimensional (via MOCs) | Chronological only | Single dimension |
| Extraction pipeline complexity | Minimal | Date parsing required | Domain classifier required |
| UI performance | Optimized via hiding | Good per-folder | Good per-folder |
| Metadata drift impact | High (mitigated by validation) | High | Medium (folder as fallback) |

### Final Decision

**Reject date-based and domain-based folders.** They add operational complexity without solving the core human-orientation problem. Instead, implement a **flat storage layer with curated navigation overlays** via MOCs. This maintains:
- Zero manual triage for extraction
- Multi-dimensional discovery
- Human spatial memory through virtual organization
- Minimal routing brittleness
- Scalability to 20k+ notes

The key insight: *Folders should not classify content; they should classify access patterns.* Machine extraction needs one access pattern (dump and index). Human navigation needs another (multi-dimensional browsing). These can be separated in the architecture without coupling.

---

**Bottom line:** Flat `knowledge/` + `.index/` MOCs provides the algorithmic efficiency of Option C with the human-centric design of Option D, while avoiding the performance pitfalls of pure flat and the semantic rigidity of domain-folders.

*Latency: 122.86s | Tokens: 10594*

### Openai (gpt-5.4)

Here’s the blunt council read, proposal by proposal.

---

## Proposal A

### Verdict
**Partially agree.**

I agree with the core recommendation: **Option D is the right baseline**.  
I do **not** agree that date-based subfolders are the right default refinement.

### Strongest point
Its strongest point is the **pragmatic performance hedge**: if Obsidian’s file explorer gets ugly with thousands of files, partitioning by year/month is a cheap way to reduce UI pain **without reintroducing semantic foldering**.

That is a real operational concern, not theory.

### Weakest assumption
The weakest assumption is that **date is a useful storage partition for this workflow**.

Rob does not think in “what note was created in 2025?” He thinks in:
- client
- product
- integration
- industry
- competitive angle
- source credibility

Date folders solve a machine/UI issue, but they create a human-facing tree that is basically meaningless. That matters because once a folder exists, people implicitly use it.

Also, the proposal smuggles in complexity:
- date-derived routing
- backfill/migration logic
- note mover automation
- redirects/archive behavior

That’s more moving parts for a solo operator than the benefit justifies.

### Risks it overlooks
- **Chronology is not stable truth.** Notes may be regenerated, updated, or merged. Which date matters: source date, extraction date, modified date, note creation date?
- **Date folders become accidental navigation.** They won’t help browse, and they’ll clutter the tree.
- **Redirect plugin / archive workflow is overengineered** for a single-user vault with full rebuild capability.
- It assumes **performance issues are proven**, when they may not be. This should be tested, not designed around preemptively.

---

## Proposal B

### Verdict
**Partially agree.**

I agree with the **Option D recommendation**, the separation of extracted vs curated, and the idea that **schema beats folders**.  
I disagree with some of its implementation confidence and a bit of architectural absolutism.

### Strongest point
Its strongest point is the framing of **folders as governance/lifecycle boundaries rather than semantic categories**:
- extracted = machine-produced, high-volume
- guides/projects = human-curated, high-value

That is the cleanest and most operationally durable distinction in the whole debate.

Also correct: **do not overload `domains`**. New orthogonal concepts need new fields.

### Weakest assumption
The weakest assumption is this line of thinking:  
> “FTS5 rebuild for 5,000 notes takes milliseconds.”

Maybe. Maybe not. Depends on:
- disk
- note size
- frontmatter parsing
- hashing
- normalization
- SQLite write settings
- validation steps
- whether attachments/references are traversed

For a solo system, full rebuild is still the right answer. But the proposal is **too casual about runtime claims**. Don’t promise performance you haven’t measured.

Second weak assumption: suggesting a **custom plugin or local API** to expose SQLite inside Obsidian is a maturity leap. That’s not pragmatic unless dashboard pain becomes severe. It introduces:
- maintenance burden
- plugin fragility
- security/IT scrutiny
- coupling to local runtime behavior

For one user, this is likely overbuilding.

### Risks it overlooks
- **Flat-folder filename collision risk** is noted, but not pushed far enough. With 20k notes, naming discipline becomes critical.
- **Sync UX**: Obsidian Sync with huge noisy folders can be annoying even if retrieval works.
- **Dashboard dependence** is acknowledged, but there’s no practical fallback UX beyond “build better infrastructure.”
- It underestimates the value of a **small number of meaningful top-level containers** for orientation.

---

## Proposal C

### Verdict
**Agree.**

This is the best of the four overall. It is the most balanced, least ideological, and most aligned to the actual constraints:
- solo operator
- zero manual triage
- metadata-first retrieval
- low operational complexity
- future dimension growth

### Strongest point
Its strongest point is the cleanest principle stated in the whole set:

> **Folders = operational role. Metadata = meaning.**

That is the right architectural line.

It also gives the best governance answer:
- new field for new axis
- new value for same axis
- taxonomy update for normalization/aliases

That’s concrete and workable.

### Weakest assumption
The weakest assumption is that a **single flat `knowledge/` folder is operationally acceptable long-term without qualification**.

Architecturally, yes.  
In day-to-day Obsidian UX, maybe not.

A folder with 3,000–5,000 files may be survivable if Rob never browses it. But humans do sometimes browse accidentally, and Obsidian’s file explorer becomes part of the lived experience whether intended or not.

So I agree with flat as the model, but I would not present it as risk-free.

### Risks it overlooks
- **Attachment/reference clutter** if extracted notes carry assets or embedded media later.
- **Globally unique naming** becomes non-negotiable at scale.
- **Operational debugging**: when a pipeline issue occurs, some kind of source-origin traceability beyond `source_type` may be needed, e.g. `source_path`, `source_id`, `origin_collection`.
- **Dashboard upkeep**: someone has to maintain these dashboards as dimensions proliferate. Since Rob is solo, the dashboard surface should stay intentionally small.

---

## Proposal D

### Verdict
**Disagree.**

This is the most human-centered argument, but the recommendation is wrong for this system.

### Strongest point
Its strongest point is the challenge to the council’s blind spot:

> Humans still need orientation, not just retrieval.

That is true. Engineers often over-rotate to “search solves everything.” Rob will need wayfinding, not just exact-match retrieval.

Also fair: source-origin folders are a bad semantic proxy.

### Weakest assumption
The weakest assumption is the core one:  
> the 8 domains are stable and mutually exclusive enough to serve as top-level semantic folders.

They are not.

Even in the current context:
- “WMS SAP Integration” can credibly sit under:
  - WMS & Logistics
  - Integration & APIs
  - Platform & Architecture
  - Business & Commercial if used in positioning
- implementation methodology, competitive strategy, vertical, delivery patterns, PM concerns all cut across those domain folders

This proposal reintroduces exactly the problem Rob already identified: **one-dimensional placement competing with metadata**.

Worse, it encourages future-you to ask “which domain folder should this live in?” That is manual or classifier complexity for little gain.

And “primary domain in folder, secondary domains in metadata” sounds tidy but creates silent distortion:
- the folder implies primacy
- users anchor on placement
- reclassification churn returns

### Risks it overlooks
- **Classifier quality debt**: assigning one primary domain at extraction time is easy to get wrong at scale.
- **Taxonomy drift in the folder tree** when product strategy evolves.
- **Folder semantics become policy**, which makes future changes expensive.
- **Routing brittleness does return**, just in slower motion.
- **Human orientation can be solved better with dashboards/MOCs/bookmarks** than by pretending multidimensional content has one home.

This proposal correctly identifies a real need—human orientation—but chooses the wrong mechanism.

---

# Revised recommendation

## Recommendation
Adopt **Option D**, but with a stricter, more operationally realistic design:

```text
vault/
  knowledge/      # all extracted knowledge notes
  projects/       # client-scoped notes, subfolder per client
  guides/         # human-authored reusable playbooks, scripts, demo guides
  dashboards/     # navigation surfaces, MOCs, Dataview views
  templates/
  system/
```

## Core rule
**Folders reflect operational ownership and lifecycle.  
Metadata reflects meaning.**

That means:
- `knowledge/` = machine-generated/extracted corpus
- `projects/` = client-bound working set
- `guides/` = curated reusable human knowledge
- everything semantic lives in frontmatter

Do **not** use folders for:
- product
- domain
- topic
- industry
- competitive context
- implementation pattern
- GTM motion

Those are dimensions, not storage locations.

---

## What I’d change from your current lean

### 1. Keep `knowledge/` flat by default — but treat file explorer as non-primary UX
I would **start flat**, not preemptively split by date or domain.

Why:
- simplest routing
- easiest future migration
- no fake semantics
- no unnecessary folder logic

But be honest: flat only works if you **intentionally stop using the sidebar as your main navigator**.

So the UX plan must be explicit:
- bookmarks for key dashboards
- Quick Switcher for direct access
- search-first workflow
- dashboard landing pages by product/domain/client/source/trust/recent

If performance or file-explorer pain appears later, add a **non-semantic partition** only then.

### 2. If partitioning becomes necessary, use a machine partition, not a semantic one
If Obsidian chokes on one huge folder, the least-worst fallback is a **purely operational shard** like:

```text
knowledge/a-f/
knowledge/g-l/
knowledge/m-r/
knowledge/s-z/
```

or

```text
knowledge/00/
knowledge/01/
...
knowledge/19/
```

I would choose this **over date folders** because:
- it is clearly non-semantic
- it is stable
- it avoids accidental human interpretation
- it scales indefinitely

Date folders imply meaning. Hash/alphabet partitions don’t.

That said: **do not add this now unless testing proves you need it**.

### 3. Add one more metadata field: `origin_collection`
Current `source_type` is too coarse for operational traceability.

You likely want:
- `source_type`: documentation, meeting, training, rfp, etc.
- `origin_collection`: source_library, meeting_recordings, rfp_set, project_docs, training_enablement, etc.
- `source_path` or `source_ref`: original file/path/ID
- optional `note_id`: stable generated identifier

This gives you source-origin queryability **without source-origin folders**.

### 4. Introduce stable note identity now
Before 5,000 notes, define a stable ID field, e.g.:
- `note_id`
- or deterministic hash from source + chunk + title

Why:
- moves/renames stop mattering
- rebuilds are cleaner
- duplicate detection becomes possible
- cross-links survive generation changes better

This matters more than folder cleverness.

### 5. Governance model for dimensions: make it lightweight and strict
Use this rule set:

#### Add a new field when:
the concept answers a new question.

Examples:
- `industries`
- `implementation_patterns`
- `competitive_context`
- `gtm_motion`
- `methodologies`
- maybe `technologies`

#### Add a new value when:
it is just another member of an existing axis.

Examples:
- new `source_type`
- new `trust_level`
- new `product`

#### Update taxonomy aliases when:
people use multiple names for the same thing.

Examples:
- “SAP CPI” / “Cloud Platform Integration”
- “retail” / “specialty retail” if normalized
- product abbreviations

#### Do not:
- dump everything into `domains`
- create folders for new dimensions
- allow ad hoc frontmatter keys to proliferate

Minimal governance artifact:
- one canonical schema file
- one taxonomy registry
- one validator in extraction/indexing

That is enough for a solo system.

---

## Answers to the 5 council questions

### 1) Flat vs hierarchical for extracted knowledge?
**Flat wins.**  
Hierarchy for extracted notes gives false confidence and future migration pain.

But flat only works if:
- navigation is dashboard/search-first
- file names are robust
- metadata quality is enforced

If Obsidian file-explorer performance becomes unacceptable, add **non-semantic sharding**, not semantic folders.

### 2) Should folders reflect source-origin or semantic-meaning?
**Neither for extracted notes.**  
Use folders for operational role only.

If forced to choose between those two, **source-origin is less wrong than semantic meaning**, because it is stable and unambiguous. But I would still keep it in metadata, not folders.

### 3) Dimension expansion strategy
Use a **field/value/taxonomy** decision model:

- **new field** = new orthogonal axis
- **new value** = same axis, more options
- **taxonomy update** = canonical values + aliases + normalization

Examples:
- `retail` → `industries`
- `SAP CPI` → likely `technologies` or `implementation_patterns`
- `displacement` → `competitive_context`
- `phased rollout` → `implementation_patterns` or `delivery_motion`

Do not mutate `domains` into a junk drawer.

### 4) Dynamic folder awareness
**Full rebuild is sufficient.**  
Do not build event-driven tracking.

For this team shape and maturity:
- one writer
- on-demand rebuild
- path not part of semantics

That is enough.

But rebuild correctness depends on:
- stable note IDs
- path treated as incidental metadata, not identity
- duplicate reconciliation during rebuild

### 5) The 5-year test
The structure that survives is the one with the **fewest semantic promises baked into the filesystem**.

That means:
- stable top-level operational folders
- meaning in metadata
- dashboard surfaces evolving over time
- schema discipline from now

Any semantic folder tree will eventually become legacy taxidermy.

---

# Final council recommendation

## Adopt this structure

```text
vault/
  knowledge/
  projects/
  guides/
  dashboards/
  templates/
  system/
```

## Add these rules

### Required frontmatter
- `note_id`
- `products`
- `topics`
- `domains`
- `source_type`
- `origin_collection`
- `trust_level`
- `client` when applicable
- `source_ref` or `source_path`

### Routing
- extracted CKE output → `knowledge/`
- client/project material → `projects/{client}/`
- manually authored reusable content → `guides/`

### Navigation
- never rely on browsing `knowledge/`
- create dashboards for:
  - by product
  - by domain
  - by client
  - by source type
  - by trust level
  - recent additions
  - review/untagged/validation exceptions

### Governance
- new semantic axis = new field
- controlled values live in `corp-os-meta`
- validation rejects unknown keys/values or flags them
- no new folders for semantic growth

### Fallback if flat folder becomes painful
Only if testing proves necessary, shard `knowledge/` with a **non-semantic partition**.  
Not by domain. Not by source type. Prefer hash/alphabet buckets.

---

## Bottom line
Your instinct was right: **Option D is the only one that truly respects multidimensional knowledge and solo-operator reality.**

What I learned from the other proposals:
- from A: performance pain is real, but date folders are the wrong first fix
- from B: lifecycle separation is valuable, but don’t overengineer plugins/APIs
- from C: the folder-role vs metadata-meaning distinction is the right principle
- from D: humans do need orientation, but semantic folders are the wrong tool for that in this system

So my firm recommendation is:

> **Choose Option D, keep extracted notes flat, make dashboards the real UX, enforce schema governance early, and only introduce non-semantic sharding if measured Obsidian performance forces it.**

That will ship now and still make sense in 2031.

*Latency: 54.44s | Tokens: 10018*

### Grok (grok-4.20-beta)

**Contrarian Analysis**

### Proposal A
**Position:** Disagree.

**Strongest point:** Correctly identifies Obsidian UI performance as a real constraint (3k+ files in one folder *does* degrade the experience on desktop and especially mobile Sync). The date-based partitioning is a pragmatic engineering compromise.

**Weakest assumption:** That the only two choices for partitioning are "semantic meaning" or "date." This is a false dichotomy. It still treats the filesystem as a mere storage layer while pretending the human being navigating it is an append-only database query machine. It inherits the consensus blind spot that spatial memory and casual browsing are luxuries rather than core cognitive tools.

**Risks overlooked:** Date-based folders create their own form of semantic drift. A 2023 note about SAP CPI integration becomes psychologically "old" simply by living in `knowledge/2023/`, even if the knowledge is evergreen. This subtly discourages the very long-term knowledge asset mindset Rob claims to want.

### Proposal B
**Position:** Strongly disagree.

**Strongest point:** The trust boundary argument between extracted and curated content is excellent. Separating machine-generated cache from human-authored mutable state is architecturally sound.

**Weakest assumption:** The religious belief that "file trees are an anti-pattern for multidimensional knowledge." This is engineer cosplay. It assumes Rob will *only* retrieve via precise queries and never explore, meander, or use the vault as an external brain. The claim that dashboards will fully replace browsing is the same hubris that killed every previous "pure metadata" knowledge system.

**Risks overlooked:** Complete dashboard dependency creates a single point of failure. When (not if) the Dataview queries become slow or the dashboards grow cluttered, Rob will have no fallback except full-text search in a sea of 5,000 identically unorganized notes. The "hide the folder with a plugin" mitigation is particularly pathetic — you're literally hiding your own knowledge from yourself because your architecture can't handle human psychology.

### Proposal C
**Position:** Disagree.

**Strongest point:** Best articulation of the operational container concept ("folders answer who/what process owns this note"). This is genuinely insightful.

**Weakest assumption:** That operational containers and semantic meaning can be cleanly separated without losing something important. The claim that "this is more correct architecturally" reveals the classic architect's disease: optimizing for theoretical purity over observed human behavior. The repeated assertion that Rob will simply "never browse knowledge/ directly" is wishful thinking disguised as principle.

**Risks overlooked:** The "just make better dashboards" solution scales poorly with cognitive load. At 20k notes, the maintenance burden of high-quality dashboards across 50 dimensions becomes its own form of technical debt. This proposal underestimates how much lightweight spatial organization reduces the need for perfect metadata.

### Proposal D
**Position:** Partially agree — this is the only proposal that isn't delusional about human cognition.

**Strongest point:** Brutally correct in calling out the "classic engineer brain" assumption that because the *machine* doesn't need folders, the *human* doesn't either. This is the central hidden assumption the other three proposals take for granted. The observation that the 8 domains are the *only* stable dimension is also strong.

**Weakest assumption:** That the 8 domains should be the *top-level folders*. This is too rigid. Forcing every note into exactly one domain folder creates the exact problem Rob already has — a note about "WMS SAP Integration" doesn't want to live in only one of those buckets.

**Risks overlooked:** Governance burden. Even with code enforcement, the quarterly "Domain Misclassifications" dashboard becomes its own maintenance task. Also underestimates how much Blue Yonder's product taxonomy *will* evolve over 5-7 years.

---

### Revised Recommendation

The consensus is wrong. They have correctly identified that semantic meaning is multi-dimensional and therefore ill-suited to folders, but then made the catastrophic leap that folders should therefore be reduced to operational buckets or dates. This is throwing out the baby with the bathwater.

**What everyone is missing:** Folders are not primarily for *classification*. They are for *orientation and priming*. They are a lightweight cognitive scaffold. The human brain uses physical location as a memory cue. Eliminating this entirely in favor of "just use dashboards" is the knowledge management equivalent of saying "why do you need rooms in your house when you have a perfect inventory system?"

**The steelmanned unpopular alternative:** Use a **shallow two-level operational-semantic hybrid** that acknowledges both machine and human needs without trying to make the filesystem do pure taxonomy work.

Proposed structure:

```
vault/
  00_dashboards/
  01_projects/           # per-client subfolders (naturally singular)
  02_knowledge/
    platform/
    planning/
    wms-logistics/
    commerce/
    data-analytics/
    security/
    integration/
    business/
    # (these are deliberately short, stable, and match the 8 domains)
  03_guides/             # human-authored only, can have organic substructure
  04_templates/
  90_system/
```

**Key principles:**

1. The 8 domains exist as *shallow* folders under `02_knowledge/` *not* because they perfectly classify content, but because they provide orientation. A note can be primarily filed under "integration" while having `domains: [WMS & Logistics, Integration & APIs]` in frontmatter. The folder is the primary orientation, metadata is the full truth.

2. Routing remains extremely simple and stable. The classifier only chooses from 8 options. This is not the routing hell the flat advocates fear.

3. Extracted notes still go to `02_knowledge/` by default. No date subfolders (this is premature optimization). If performance becomes an issue at 8k+ notes, *then* we add year partitioning *within* each domain.

4. New dimensions (industries, implementation patterns, competitive contexts, etc.) are *strictly* metadata. Never folders. The 8 domains are the only ones allowed filesystem representation because they are uniquely stable.

5. For question 3 (dimension expansion): New orthogonal dimensions get their own frontmatter field *and* an entry in `corp-os-meta`. `domains` remains sacred. Governance is code + quarterly validation.

6. For question 4: Full rebuild is sufficient. The routing_map only cares about the 8 domains + the other top-level folders. Moves between domains are rare and should be slightly painful — they represent a meaningful reorientation of the knowledge.

**The 5-year test:** This structure survives because it makes a *principled* compromise with human psychology instead of declaring war on it. The flat advocates are optimizing for the machine. Proposal D optimizes for theoretical taxonomic purity. This optimizes for the actual user — a solo ADHD technical pre-sales engineer who needs both retrieval *and* orientation.

The hidden consensus assumption is that structure should be dictated by what the computer finds easiest to process. That is backwards. The computer exists to serve the wetware, not the other way around.

*Latency: 20.62s | Tokens: 8520*

## Synthesis (by claude, non-participant)



# Decision Summary: Obsidian Vault Structure

## Consensus

All four participants agreed on the following points:

1. **Option D (Hybrid flat + curated) is the correct baseline.** Every participant either recommended Option D outright or built their counterproposal on its foundation. No one defended Options A, B, or C as originally stated.

2. **Semantic meaning belongs in metadata, not folders.** Universal agreement that multi-dimensional knowledge (products, topics, domains, industries, competitive context, implementation patterns, etc.) cannot be faithfully represented by a folder hierarchy. Frontmatter metadata is the correct carrier for meaning. No dissent.

3. **The `domains` field must not become a junk drawer.** All participants agreed that new orthogonal concepts (industry verticals, implementation patterns, competitive context, GTM motion) require new frontmatter fields, not overloading of the existing `domains` field. The 3-tier governance model (new field / new value / taxonomy alias) was endorsed by every participant.

4. **Source-origin folders are a poor long-term design.** Options B and C were rejected by all. Organizing by "where the bits came from" creates misleading classification that degrades over the life of the note.

5. **Full `corp index rebuild` is sufficient; event-driven tracking is premature.** With a single writer, on-demand rebuild, and paths not part of retrieval semantics, no one argued for filesystem event tracking.

6. **Trust boundaries matter.** Separating machine-extracted content from human-authored content is architecturally correct and operationally valuable. All agreed on distinct containers for extracted knowledge, client projects, and curated guides.

7. **`routing_map.yaml` must be simplified and stabilized.** Fewer routing destinations = fewer breakage points. All agreed the current coupling between folder names and routing rules is a liability.

8. **Date-based subfolders are the wrong partitioning strategy.** Three of four participants explicitly rejected date partitioning. Dates imply staleness for evergreen knowledge, add routing complexity, and provide no browsing value for a pre-sales workflow.

9. **Stable note identity should be introduced early.** Multiple participants recommended a `note_id` or deterministic hash to decouple note identity from file path, enabling clean rebuilds and duplicate detection.

---

## Unresolved Disagreements

### The Central Dispute: Should the 8 knowledge domains become folders?

This is the only structural question where the council genuinely split. It is substantive and deserves careful adjudication.

**The flat camp (Gemini, OpenAI, DeepSeek)** argues:

- The 8 domains are *not* mutually exclusive. A "WMS SAP Integration" note credibly belongs in WMS & Logistics, Integration & APIs, and Platform & Architecture simultaneously. Forcing single-folder assignment reintroduces the original problem.
- Domain classification at extraction time requires either an LLM classifier (non-deterministic, error-prone) or manual triage (violates the ADHD/zero-triage constraint).
- Folders create implicit semantic primacy that competes with the metadata truth. Users anchor on placement.
- Blue Yonder's product taxonomy will evolve over 5-7 years. Domain folders become legacy structure.
- Human orientation is better served by dashboards, MOCs, bookmarks, and Quick Switcher than by a folder tree that can only express one dimension.

**The domain-folder camp (Grok)** argues:

- Human spatial memory is not optional. "I know this is a WMS thing" is faster than constructing a Dataview query.
- Pure flat structures have been tried repeatedly in PKM and knowledge management systems. They consistently degrade into "everything is findable but nothing is discoverable."
- The 8 domains come from Blue Yonder's own product taxonomy — the most stable dimension available.
- Imperfect classification is acceptable when retrieval ignores folders anyway. The folder is a cognitive hint, not a contract.
- Dashboard-only navigation is a single point of failure. When dashboards break, degrade, or become cluttered, the user has no fallback in a flat structure.
- Telling a knowledge worker to "never browse the folder" is designing against human nature.

**Why each side has merit:**

The flat camp is architecturally correct: multi-dimensional content does not belong in single-dimensional containers, and forced classification adds operational overhead that compounds over time. The domain-folder camp is psychologically correct: humans need spatial orientation, and dashboards are not a perfect substitute for the ambient awareness that lightweight folder structure provides. Both positions are backed by real evidence from knowledge management practice.

---

### Secondary Disagreement: What to do if flat folders cause Obsidian UI pain

- **DeepSeek (Round 2)** proposed hidden `.index/` MOC folders as virtual navigation overlays.
- **OpenAI** proposed non-semantic sharding (alphabetical/hash buckets) only if performance testing proves the need.
- **Gemini** proposed source-system partitioning (`sys_sharepoint/`, `sys_confluence/`) as an operational shard.
- **Grok** proposed domain subfolders as the partition, arguing it kills two birds.

All agree the problem is real. They disagree on the right fallback.

---

## Recommended Decision

### Adopt Option D with flat `knowledge/`, explicit navigation infrastructure, and a defined escalation path.

```
vault/
  knowledge/          # All CKE-extracted notes, flat
  projects/           # Client-scoped, subfolder per client
  guides/             # Human-authored playbooks, discovery scripts, demo guides
  dashboards/         # Dataview views, MOCs, navigation surfaces
  templates/          # Obsidian note templates
  system/             # routing_map.yaml, config, schemas
```

### Core architectural rule

> **Folders define operational ownership and data lifecycle. Metadata defines meaning.**

This means:
- `knowledge/` = machine-produced extraction corpus
- `projects/{client}/` = client-bound working material
- `guides/` = human-curated reusable content
- `dashboards/` = navigation and discovery surfaces
- All semantic dimensions (products, topics, domains, industries, competitive context, implementation patterns, GTM, methodologies) live **exclusively** in frontmatter metadata, governed by `corp-os-meta`

### Routing
- CKE extraction → `knowledge/`
- CPE project extraction → `projects/{client}/`
- Manual authoring → `guides/`
- `routing_map.yaml` has exactly 3 rules. It does not change when dimensions change.

### Addressing the strongest objection: human orientation

Grok's argument — that humans need spatial orientation and that "just use dashboards" is insufficient — is the strongest objection to this recommendation. I weigh it seriously but ultimately rule against domain folders for three reasons:

1. **The ADHD/zero-triage constraint is a hard constraint, not a preference.** Domain classification at extraction time requires either manual assignment (unacceptable) or an automated classifier (non-deterministic, error-prone, adds pipeline complexity). Every misclassification creates a note in the wrong folder that Rob will never fix. Over 5,000 notes, classification drift becomes structural rot.

2. **The "folder as cognitive hint" argument only works if the hint is usually right.** With notes that genuinely span 2-3 domains, the folder will be wrong or misleading roughly 30-50% of the time. A wrong hint is worse than no hint.

3. **The orientation need is real but solvable without semantic folders.** The solution is to treat `dashboards/` as first-class navigation infrastructure, not an afterthought. This means:
   - **MOC (Map of Content) notes** for each major product, domain, and client — living in `dashboards/`, populated by Dataview queries
   - **Bookmarked landing pages** pinned in Obsidian's sidebar
   - **Quick Switcher** as the primary entry point (Obsidian's Cmd/Ctrl+O)
   - **Starred/bookmarked** notes for active work
   - **Graph view** filtered by metadata for exploration

   This provides multi-dimensional orientation (not single-dimensional), and it works at 20,000 notes where folder trees become unmanageable regardless.

The bet this recommendation makes: **investing in dashboard/MOC quality is more durable than investing in folder classification quality.** If that bet is wrong, the escalation path below provides a recovery option.

### Escalation path: if flat `knowledge/` becomes painful

If Obsidian UI performance degrades measurably (lag in file explorer, slow graph render, sync issues), or if Rob finds the flat folder genuinely hostile to daily work after 60 days of use:

**First resort:** Hide `knowledge/` from Obsidian's file explorer. Navigate exclusively via dashboards, search, and Quick Switcher. This is cheap and reversible.

**Second resort:** Add non-semantic sharding inside `knowledge/`:
```
knowledge/
  a-f/
  g-l/
  m-r/
  s-z/
```
Alphabetical by filename. Clearly non-semantic. Stable. No routing logic changes (wildcard `knowledge/*/`). No false classification. This is preferred over date-based, source-based, or domain-based partitioning because it carries zero semantic implication.

**Do not** escalate to domain folders unless a fundamentally different argument emerges. The problems with domain folders (classification overhead, single-dimension constraint, taxonomy drift, routing brittleness) do not diminish with scale — they worsen.

---

## Risks

### 1. Flat `knowledge/` folder degrades Obsidian UI performance
**Likelihood:** Moderate (probable above 5,000 notes on desktop; higher on mobile).
**Impact:** Daily UX friction.
**Mitigation:** Follow the escalation path. Test with current 2,230 notes. Measure file explorer render time. Set a threshold (e.g., >2 second lag = escalate). Hide folder from explorer as first step.

### 2. Dashboard/MOC dependency becomes a single point of failure
**Likelihood:** Moderate. Dataview queries can slow down, break on plugin updates, or become stale.
**Impact:** Knowledge discovery halts if dashboards are the only navigation path.
**Mitigation:**
- Keep `corp retrieve` (FTS5 CLI) as the primary retrieval tool — it is independent of Obsidian plugins.
- Maintain a small set of high-quality dashboards (8-12), not dozens.
- Cache critical dashboard views as static markdown monthly (automated via script).
- Obsidian's native search and Quick Switcher always work regardless of plugin state.

### 3. Metadata quality degrades over time
**Likelihood:** High if unchecked. Extraction pipelines produce imperfect metadata.
**Impact:** Retrieval accuracy silently declines. Notes become "lost" in a flat folder with bad tags.
**Mitigation:**
- Implement schema validation in the CKE pipeline: reject or flag notes with unknown field values.
- Run a weekly validation script that reports notes with missing required fields, unknown values, or empty critical metadata.
- Create a `dashboards/triage.md` view showing notes with `trust_level: draft` or validation failures.
- `corp-os-meta/taxonomy.yaml` is the single source of truth for allowed values. All pipeline writes validate against it.

### 4. Namespace collisions in flat folder
**Likelihood:** Moderate at 5,000+ notes; high at 20,000.
**Impact:** Pipeline overwrites existing notes silently.
**Mitigation:**
- Enforce deterministic, collision-resistant naming: `[SourceAbbrev] - [Title] - [ShortHash].md`
- Include `note_id` in frontmatter (content hash or UUID) for identity independent of filename.
- Rebuild process should detect and flag duplicate `note_id` values.

### 5. `domains` field becomes a junk drawer despite governance intentions
**Likelihood:** Moderate. Solo operator under time pressure may take shortcuts.
**Impact:** FTS5 queries return noisy results; dimension semantics blur.
**Mitigation:**
- Enforce the 3-tier rule in pipeline code, not just documentation.
- Pipeline rejects `domains` values not in the canonical list.
- Quarterly review: run a script that reports all distinct values per field. Flag unexpected growth.

### 6. Rob finds the system psychologically hostile without folder-based orientation
**Likelihood:** Unknown. This is a genuine human factors risk that cannot be fully predicted.
**Impact:** Reduced vault usage, reversion to ad hoc file management, loss of trust in the system.
**Mitigation:**
- Invest heavily in dashboards/MOCs during Phase 2 (see Action Items).
- Give the flat structure a 60-day honest trial before escalating.
- If the need for spatial orientation persists, consider domain-based MOC pages (not folders) pinned as bookmarks — these provide the cognitive hint without the classification overhead.

---

## Action Items

### Phase 1: Foundation (Week 1-2)

1. **Restructure vault to target layout:**
   ```
   vault/
     knowledge/
     projects/
     guides/
     dashboards/
     templates/
     system/
   ```
   - Move all notes from `02_sources/` and `04_evergreen/` → `knowledge/`
   - Move `01_projects/` → `projects/`
   - Move `03_playbooks/` → `guides/`
   - Move `00_dashboards/` → `dashboards/`
   - Move `05_templates/` → `templates/`
   - Move `90_System/` → `system/`

2. **Simplify `routing_map.yaml`** to exactly 3 routing rules:
   - `extracted → knowledge/`
   - `project → projects/{client}/`
   - `manual → guides/`

3. **Run `corp index rebuild`** and verify all notes are correctly indexed from new paths.

4. **Add `note_id` field to frontmatter schema.** Generate deterministic IDs for all existing notes (hash of source + title + first 200 chars, or UUID). Update CKE pipeline to generate `note_id` for new extractions.

5. **Add `origin_collection` field to frontmatter schema.** Values: `source_library`, `rfp`, `meeting_recordings`, `project_docs`, `training_enablement`, `manual`. Backfill from current folder origin before migration.

### Phase 2: Navigation Infrastructure (Week 2-3)

6. **Create MOC (Map of Content) notes in `dashboards/`:**
   - One per product line (WMS, Planning, Platform, etc.)
   - One per knowledge domain (the 8 domains)
   - One per active client
   - One for "Recent Additions" (last 30 days)
   - One for "Needs Review" (trust_level: draft or validation failures)
   - Each MOC uses a Dataview query filtered on the relevant metadata field

7. **Pin/bookmark key MOCs** in Obsidian's sidebar bookmarks panel.

8. **Configure Obsidian file explorer:**
   - Collapse `knowledge/` by default
   - Optionally hide via CSS snippet or Hider plugin if browsing proves distracting

9. **Test Quick Switcher + Search workflow** as primary navigation for 2 weeks. Document friction points.

### Phase 3: Governance & Validation (Week 3-4)

10. **Update `corp-os-meta/taxonomy.yaml`** with:
    - All current fields and their allowed values
    - New fields: `origin_collection`, `note_id`
    - Planned future fields documented as `status: planned` (e.g., `industries`, `implementation_patterns`, `competitive_context`)

11. **Add schema validation to CKE pipeline:**
    - Validate all frontmatter keys against taxonomy schema
    - Validate all field values against allowed values
    - Unknown keys/values → write note but tag `status: validation_failed`
    - Missing required fields → write note but tag `status: incomplete`

12. **Create `dashboards/triage.md`** — Dataview query showing all notes with `status: validation_failed` or `status: incomplete`.

13. **Document the dimension governance rule** in `system/GOVERNANCE.md`:
    - New question = new field
    - Same question, new answer = new value
    - Multiple names for same thing = taxonomy alias
    - All changes require `corp-os-meta` update + validation script run

### Phase 4: Monitoring & Escalation (Month 2+)

14. **60-day checkpoint:** Evaluate whether flat `knowledge/` is working.
    - Measure: Obsidian file explorer performance, daily workflow friction, retrieval accuracy
    - Decision gate: if unacceptable, implement alphabetical sharding as described in escalation path

15. **Monthly: Run taxonomy health check script.**
    - Report distinct values per field
    - Flag fields with >30% growth month-over-month
    - Flag notes with empty required fields

16. **Quarterly: Review and update MOCs.** Add new MOCs for any newly created dimensions. Archive MOCs for deprecated concepts.
