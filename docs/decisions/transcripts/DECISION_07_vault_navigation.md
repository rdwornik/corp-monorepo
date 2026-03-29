# AI Council Debate: # Council Question: Vault Navigation & UX — How Rob Actually Uses Obsidian

## T

**Date:** 2026-03-22 15:00:15
**Panel:** deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta, gpt-5.4
**Synthesizer:** claude (non-participant)
**Rounds:** 2
**Duration:** 369.6s
**Mode:** full (4-model panel)
**Source:** council_inbox\COUNCIL_vault_navigation_v2.md

---

## Round 1: Initial Responses

### Gemini (gemini-3.1-pro-preview)

## Position
I recommend **Option D (Flat storage + Auto-generated MOCs)**, powered by programmatic hierarchical tagging at the CKE extraction layer and a strictly minimized plugin stack (Dataview, Omnisearch, Homepage). This architecture decouples storage from presentation, ensuring robust integration with automated pipelines (`corp-by-os`, `corp retrieve`) while delivering a low-friction, zero-maintenance drill-down experience for the user.

## Rationale
*   **Decoupled Storage & Presentation (Interoperability):** A flat `01_knowledge/` folder ensures highly resilient automated ingest. Scripts do not need to manage complex directory trees or resolve path changes, preventing broken links and database synchronization errors between the filesystem and the FTS5 SQLite index. Multi-product notes (e.g., "WMS + Planning") naturally exist in one place.
*   **Deterministic Auto-Generation (Zero Maintenance):** MOCs and Dashboards must be auto-generated via a cron or trigger-based script (e.g., `corp generate-mocs`). Relying on manual curation guarantees failure for an ADHD persona. Generating MOCs from metadata ensures the UI is an always-accurate reflection of the underlying data structure.
*   **Native Hierarchical Tagging (Defense-in-Depth):** CKE must generate normalized, hierarchical tags (e.g., `#client/lenzing`, `#domain/industry/retail`, `#product/wms`). This lights up Obsidian's native capabilities (Sidebar Tag Pane, Graph View coloring, Native Search) *without* relying on 3rd-party plugins. It solves the 6-dimension taxonomy natively. 
*   **Strict File Naming Convention (Data Lineage):** Enforcing `{date}_{source_filename_normalized}.md` at the ingest level prevents filesystem collisions, ensures chronological sorting fallbacks, and maintains auditability back to the source system without requiring complex internal metadata lookups.
*   **Minimized Attack Surface (Supply Chain Trust):** The plugin stack is restricted to **Homepage** (for the entry dashboard), **Omnisearch** (for robust FTS), and **Dataview** (for dynamic MOCs). We explicitly reject Folder Note, Breadcrumbs, and Excalidraw to limit third-party code execution, minimize Obsidian Sync conflicts (staying well under 100MB), and prevent UI-blocking bugs.

## Trade-offs
*   **Useless File Explorer:** The native Obsidian left-sidebar file tree becomes an unreadable wall of 4000+ notes. The user must rely entirely on the Homepage, Search, and Tag pane for navigation.
*   **Lack of Artisanal Curation:** Auto-generated MOCs mean notes are grouped strictly by metadata. You lose the human-curated "storytelling" aspect of custom index notes.
*   **Dataview Dependency:** While we limit plugins, we create a hard dependency on Dataview for visual dashboards. If Dataview breaks in an Obsidian update, complex UI navigation temporarily degrades to flat tag-searches.

## Risks
*   **Risk: "Tag Explosion" and Taxonomy Drift.** CKE LLM extractions might hallucinate new tags (e.g., creating `#product/wms`, `#product/WMS-cloud`, `#product/warehouse`), destroying the MOC structure. 
    *   *Mitigation:* CKE must validate tags against a hardcoded, enumerated taxonomy list before writing the markdown frontmatter. Ingest scripts should drop or map unknown tags to a `#needs-review` bucket.
*   **Risk: File Path Length Limits and Collisions.** `{date}_{source_filename}.md` can exceed Windows maximum path lengths if source files are deeply nested or verbosely named. 
    *   *Mitigation:* The `corp-by-os` ingest script must explicitly truncate filenames (e.g., to 64 characters) and append a short hash (e.g., `..._a7b2.md`) to guarantee uniqueness and system safety.
*   **Risk: Plugin Supply Chain Compromise.** Dataview and Omnisearch possess deep read access to all vault data. A malicious update could exfiltrate proprietary pre-sales intel.
    *   *Mitigation:* Disable auto-updates for Obsidian community plugins. The architecture council should vet major plugin version updates in a staging environment before pushing to the production vault configuration.
*   **Risk: Graph View Performance/Noise.** With 4000+ notes dynamically linked by multi-dimensional tags, the built-in Graph View may become an unreadable "hairball" that consumes excess memory.
    *   *Mitigation:* Pre-configure the Obsidian Graph View settings in the `.obsidian/workspace` file to default to local graph depth (e.g., 2 degrees of separation) and color-code strictly by the top-level `#domain/` and `#product/` tags.

*Latency: 29.61s | Tokens: 5326*

### Deepseek (deepseek-reasoner)

## Position
Adopt a **flat file structure with auto-generated MOC (Map of Content) notes** (Option D) and **comprehensive hierarchical tags** to enable multi‑dimensional, zero‑maintenance navigation. Use a curated plugin stack (Dataview, Breadcrumbs, Homepage, Omnisearch) to surface drill‑down paths and a dashboard homepage for rapid daily workflow.

## Rationale
- **Computational efficiency & scalability:** A flat folder (`01_knowledge/`) with indexed frontmatter fields (products, clients, domains) allows `corp retrieve` (FTS5) and Dataview queries to run over 4000+ notes with minimal I/O overhead; MOCs are virtual views that avoid file duplication and can be regenerated on ingest.
- **Multi‑dimensional access without restructuring:** Hierarchical tags (e.g., `product/wms`, `client/lenzing`, `domain/security`) enable native Obsidian tag‑pane navigation and graph coloring, while MOCs provide curated dashboards for each dimension (products, clients, domains, etc.). This satisfies Rob’s drill‑down pattern and future expansion across six knowledge dimensions.
- **Zero‑maintenance ADHD‑friendly UX:** Auto‑generation of tags and MOCs by `corp generate‑mocs` at ingest time ensures no manual filing; a homepage dashboard aggregates recent notes, stale alerts, and quick links—reducing cognitive load to under 60 seconds for common tasks.

## Trade‑offs
- **Graph‑view performance:** With 4000+ notes, the global graph may become a hairball; mitigation requires heavy filtering by tags or MOCs, limiting its utility for broad exploration.
- **Dataview query latency:** Complex queries across thousands of notes may take hundreds of milliseconds; we accept this for the flexibility of virtual MOCs, but will monitor and pre‑compute if needed.
- **Sidebar navigation complexity:** The flat folder makes the file‑tree sidebar useless; we compensate with tag‑pane navigation and Breadcrumbs hierarchy, but users accustomed to folder‑based browsing must adapt.
- **Initial setup overhead:** Implementing auto‑generation scripts for tags and MOCs requires upfront development; however, this is a one‑time cost that eliminates daily curation.

## Risks
1. **Tag explosion:** Uncontrolled tag generation could lead to thousands of unique tags, degrading tag‑pane usability.  
   *Mitigation:* Normalize tags to a predefined taxonomy (e.g., only from `corp‑os‑meta` fields) and use hierarchical prefixes (`product/`, `client/`, `domain/`) to keep the namespace organized.

2. **MOC staleness:** If the auto‑generation script fails or lags, MOCs become outdated, breaking navigation.  
   *Mitigation:* Run `corp generate‑mocs` as part of the ingest pipeline, with a fallback daily job; include version‑tracking in MOC frontmatter to detect drift.

3. **Sync bandwidth:** Obsidian Sync’s 100 MB limit could be exceeded if attachments (images, diagrams) grow unchecked.  
   *Mitigation:* Store large media externally (e.g., cloud storage) and link them; compress images on ingest; monitor vault size with alerts.

4. **Plugin conflicts:** Adding multiple plugins may cause performance issues or sync conflicts.  
   *Mitigation:* Start with the core four (Dataview, Breadcrumbs, Homepage, Omnisearch); test incrementally; disable unused plugins.

5. **Linking density:** To make the graph view useful, notes must be linked to MOCs and each other. Without automated back‑linking, the graph remains sparse.  
   *Mitigation:* Auto‑insert `[[MOC_Product_WMS]]` in notes based on frontmatter during ingest, and encourage linking in extraction templates.

## Implementation Details
- **Folder structure:** `01_knowledge/` (flat), `00_mocs/` (auto‑generated MOC notes), `02_templates/`, `03_attachments/`.
- **Tag taxonomy:** Hierarchical, lowercase, hyphen‑delimited (e.g., `product/wms`, `client/lenzing`, `domain/security`, `industry/retail`). Generated by CKE or `corp‑by‑os` from frontmatter fields.
- **File naming:** `{date}_{source_filename_normalized}.md` (e.g., `2026‑03‑22_SGDBF_Architectural_Requirements.md`). Renamed on ingest.
- **Homepage dashboard:** `Home.md` with Dataview queries for: recent notes (last 7 days), upcoming clients (from calendar integration), stale‑note alerts, and quick‑links to top‑level MOCs.
- **MOC generation:** Each MOC (`MOC_Product_WMS.md`, `MOC_Client_Lenzing.md`, `MOC_Domain_Security.md`) contains a Dataview table querying the relevant tag, grouped by note type (training, RFP, etc.). Regenerated on every ingest.
- **Plugin configuration:**
  - **Dataview:** Index `products`, `clients`, `domains`, `tags` frontmatter.
  - **Breadcrumbs:** Define parent‑child relationships via frontmatter (e.g., `parent: [[MOC_Product_WMS]]`), auto‑populated during ingest.
  - **Homepage:** Set `Home.md` as default.
  - **Omnisearch:** Enable fuzzy matching and PDF indexing.

*Latency: 111.09s | Tokens: 6010*

### Openai (gpt-5.4)

## Position
Choose **D: flat storage + MOC-driven navigation**, with a small **hybrid UX layer**: top-level navigation notes for Products, Clients, Domains, Recent, and Quality; auto-generated child MOCs for key entities like WMS, Planning, Lenzing, Security. Keep files physically flat for automation and multi-classification, but make the **user experience feel hierarchical** through MOCs, tags, and a homepage.

## Rationale
- **Matches Rob’s mental model without breaking automation.** Rob thinks in drill-down trees; the system should present trees at the navigation layer, not force trees into storage. Flat storage avoids arbitrary placement for notes that belong to both WMS and Planning, or both Lenzing and Security.
- **Zero-maintenance is non-negotiable.** With 2k–4k notes and ADHD constraints, hand-filing and hand-curated navigation will decay fast. Auto-generated MOCs and dashboards are the only sustainable baseline.
- **Supports multiple dimensions cleanly.** Products, clients, domains, topics, competitive, and source type are all valid access paths. MOCs + tags let one note appear in all relevant paths without duplication.
- **Preserves future flexibility.** If this expands beyond Rob into services, marketing, or exec knowledge, flat + metadata + MOCs scales better than a folder tree optimized for one role.
- **Best cost/value ratio for this team maturity.** It delivers strong UX without requiring a complex plugin ecosystem, custom scripting-heavy hierarchy logic, or ongoing librarian work.

## Trade-offs
- You give up the simplicity of “just browse folders and you’re done.” The sidebar alone won’t be enough; the homepage and MOCs become the primary UX.
- Auto-generated MOCs will be **useful but somewhat generic**. They won’t have the editorial quality of hand-curated battlecards or account plans unless selectively enhanced later.
- Dataview becomes a critical dependency for the best experience. If queries break or metadata quality slips, navigation quality drops.
- Native Obsidian UX will still feel a bit “system-driven” versus a fully bespoke knowledge app. This is a pragmatic compromise, not perfection.

## Risks
- **Risk: Metadata quality is inconsistent, so MOCs are noisy or incomplete.**  
  Mitigation: enforce required frontmatter at ingest for `products`, `clients`, `domains`, `topics`, `source_type`, `created`, `modified`, `quality/confidence`. Validate in `corp-by-os` before writing notes.
- **Risk: Too many MOCs create clutter and choice paralysis.**  
  Mitigation: only expose 5 top-level entry points on the homepage: **Products, Clients, Domains, Recent, Quality**. Everything else is second-level.
- **Risk: Homepage/dashboard becomes slow or fragile with 4k notes.**  
  Mitigation: keep homepage queries simple and bounded; avoid giant full-vault tables on the landing page. Use summary counts + recent lists + links to deeper MOCs.
- **Risk: Rob ignores MOCs and falls back to search because navigation feels indirect.**  
  Mitigation: optimize the click path: Home → Client/Product MOC → filtered sections. Also install Omnisearch so search is a first-class backup, not a failure mode.
- **Risk: Tags explode into an unmanageable mess.**  
  Mitigation: use a **prefixed taxonomy** with controlled vocab only, generated automatically at ingest. No free-form user tagging.

---

## Concrete recommendations

### 1) Folder structure
Use this:

```text
00_Home/
  Home.md
  Products.md
  Clients.md
  Domains.md
  Recent.md
  Quality.md

01_Knowledge/
  [all extracted notes flat]

02_MOCs/
  products/
    WMS.md
    Planning.md
    Platform.md
  clients/
    Lenzing.md
    Michelin.md
    SGDBF.md
  domains/
    Security.md
    Industry_Knowledge.md
    Technology.md
    Sales_Customer_Executive.md
  topics/
    Disaster_Recovery.md
    Competitive.md

03_Templates/
04_Attachments/   (or external links only, to protect sync size)
99_System/
```

Why this specific shape:
- **Knowledge stays flat** for ingest simplicity and multi-dimensional retrieval.
- **MOCs are separated** so the sidebar becomes useful: Rob can browse `02_MOCs/products/WMS`, `02_MOCs/clients/Lenzing`, etc.
- This gives a visible tree in the sidebar **without misusing folders as classification**.

I would **not** use product-first folders for actual notes. That creates endless edge cases for multi-product notes.

---

### 2) Navigation pattern
The main path should be:

```text
Open Obsidian
→ Home.md opens automatically
→ Click Products / Clients / Domains / Recent / Quality
→ Click specific MOC (e.g. Lenzing, WMS, Security)
→ Use section blocks on the MOC to drill deeper
→ Open source note
```

Target click paths:
- **Before client call:** Home → Clients → Lenzing → “Meeting History / Products in Scope / Open Questions”
- **RFP prep:** Home → Products → WMS → “RFP Answers” + “Topics: Disaster Recovery”
- **Learn product:** Home → Products → Platform → “Overview / Architecture / Training / Demo”
- **After meeting:** Home → Recent → latest extracted notes → also visible from Michelin MOC
- **Competitive intel:** Home → Domains or Topics → Competitive → filtered by product/vendor

Design each MOC as a **stacked page**, not just a raw Dataview table.

Example `WMS.md` layout:
1. Short overview
2. Key subtopics
3. Architecture notes
4. Training materials
5. RFP answers
6. Competitive intel
7. Client-specific WMS references
8. Recent additions

That is much better UX than a single giant table.

---

### 3) Auto-generation vs hand-curation
Recommendation: **auto-generate all core MOCs**, then allow **light hand-editing only in the intro section**.

Practical split:
- **Auto-generated:** entity MOCs, homepage summaries, recent/staleness dashboards, section queries
- **Hand-curated:** 3–10 strategic pages only, such as:
  - top products: WMS, Planning, Platform
  - top accounts: Lenzing, Michelin
  - one competitive landing page
  - maybe one “Pre-Sales Command Center”

Why:
- Fully hand-curated won’t survive.
- Fully auto-generated can feel sterile.
- Hybrid lets the system do 95% of the maintenance while preserving a little human context where it matters most.

So yes: implement `corp generate-mocs`.

---

### 4) Plugin stack: the 5 that give 80% of value
My recommended stack:

1. **Dataview**  
   Mandatory. Powers MOCs, homepage, recent/staleness, product/client rollups.

2. **Homepage**  
   Critical for ADHD and speed. Obsidian should open directly to a useful command center, not a random last note.

3. **Omnisearch**  
   Strong fallback path when Rob remembers a phrase but not the taxonomy. Search should complement navigation, not compete with it.

4. **Templater**  
   Useful for generating consistent MOC shells and any manual notes Rob creates. Also helps standardize curated pages.

5. **Folder Note**  
   Optional but high-value if you want clickable folders for `Products`, `Clients`, `Domains` indexes. Nice UX polish.

Plugins I would **not prioritize initially**:
- **Breadcrumbs**: conceptually attractive, but likely more complexity than value right now. You already have hierarchy via MOCs and links.
- **Kanban**: useful only if Rob actively manages opportunities in Obsidian; likely not core to this knowledge UX.
- **Calendar**: nice-to-have, not top 5.
- **Excalidraw**: good for later, but not required to solve navigation.
- **Graph View plugin enhancements**: defer.

If you want a strict top 4, drop Folder Note.

---

### 5) Knowledge graph
Recommendation: **do not treat Graph View as a primary navigation tool**. It is secondary, useful only if you improve linking and tags.

For this use case, Graph becomes useful only when:
- every note has generated links to:
  - related product MOC
  - related client MOC
  - related domain MOC
  - maybe related topic MOC
- tags are generated consistently
- MOCs act as hubs, giving the graph visible clusters

Without that, Graph is just confetti.

Practical use:
- good for spotting clusters and orphan notes
- good for “what’s connected to WMS + Security + Michelin?”
- not good for “I have a call in 30 minutes”

So: support it, but don’t design around it.

---

### 6) Homepage
Homepage should be a **command center**, not a giant report.

Recommended sections:

#### Top row
- **This Week’s Clients**
- **Recent Notes Added**
- **Stale Notes**
- **Open Coverage Gaps**

#### Main navigation
Big links/buttons:
- Products
- Clients
- Domains
- Recent
- Quality

#### Quick access blocks
- Recent client activity
- Recently updated products
- Competitive intel added this week
- Saved links to top MOCs: WMS, Planning, Platform, Lenzing, Michelin

#### Search
- one visible prompt: “Use Omnisearch for exact phrase / keyword recall”

The homepage should answer:
- What changed?
- What matters this week?
- Where do I click next?

It should **not** dump 100 rows of Dataview output.

---

### 7) The “WMS + Planning” problem
Do **not** solve this with folders. Solve it with metadata, tags, and MOCs.

For a note relevant to both:
```yaml
products:
  - WMS
  - Planning
topics:
  - disaster-recovery
domains:
  - technology
clients:
  - SGDBF
source_type: rfp
```

Then:
- `WMS.md` queries all notes where `contains(products, "WMS")`
- `Planning.md` queries all notes where `contains(products, "Planning")`

Same note, appears in both paths, no duplication.

This is the strongest argument against product-first note storage.

---

## Tags decision

### Should tags be auto-generated?
Yes. **Auto-generate tags from frontmatter at ingest time in corp-by-os**.

Why ingest-time, not later:
- guarantees Obsidian-native navigation immediately
- keeps note files self-contained
- avoids a second repair step
- easier to debug when metadata/tag output is deterministic

### Tag taxonomy
Use **prefixed tags**, not flat tags.

Recommended pattern:
- `#product/wms`
- `#product/planning`
- `#client/lenzing`
- `#domain/technology`
- `#domain/sales-customer-executive`
- `#topic/disaster-recovery`
- `#source/rfp`
- `#source/meeting`
- `#competitor/oracle`
- `#competitor/manhattan-associates`

Why prefixed:
- avoids collisions
- keeps tag pane navigable
- supports future expansion across business functions
- makes graph coloring and search more powerful

Do **not** use unprefixed `#wms #security #lenzing`. That gets messy at scale.

---

## File naming decision
Yes, **rename files on ingest** to enforce consistency.

Recommended filename:
```text
YYYY-MM-DD_source-filename-normalized.md
```

If collisions are possible:
```text
YYYY-MM-DD_source-filename-normalized_shortid.md
```

Example:
```text
2026-03-22_sgdbf_architectural_requirements.md
```

Why:
- chronological sorting
- predictable links
- easier deduping
- cleaner sidebar/search results

Also keep source traceability in frontmatter:
```yaml
source_filename: SGDBF_Architectural_Requirements.pdf
source_path: ...
ingested_at: 2026-03-22T10:15:00Z
```

---

## Minimum structure now that won’t block future expansion

Top-level navigation categories should be:
1. **Products**
2. **Clients**
3. **Domains**
4. **Recent**
5. **Quality**

That is enough now, and extensible later.

The six broader knowledge dimensions should live primarily under **Domains**, using both MOCs and tags:
- Industry Knowledge
- Product Knowledge
- Implementation/Services
- Technology
- Sales/Customer/Executive
- Marketing

That means a note can be reached through:
- Product path
- Client path
- Domain path
- Topic path
- Search
- Graph

This is exactly what you want for future multi-role use without restructuring the vault.

---

## Final pragmatic blueprint

If I were making the call for a small team shipping soon, I’d do this in phases:

### Phase 1: Ship now
- Flat `01_Knowledge`
- `00_Home` + `02_MOCs`
- Auto-generated MOCs for products, clients, domains
- Homepage plugin
- Dataview + Omnisearch
- Auto-generated prefixed tags
- Standardized filenames on ingest

### Phase 2: UX polish
- Improve top 10 MOCs with human-written intros
- Add Recent and Quality dashboards
- Add Folder Note for cleaner browsing
- Add graph grouping/colors once links/tags are stable

### Phase 3: Advanced curation
- Strategic hand-curated pages for major accounts/products
- Coverage gap reporting
- stale-note scoring
- maybe competitive battlecard landing pages

That gets Rob to a **sub-60-second path to relevant knowledge** without creating a maintenance burden the team cannot sustain.

*Latency: 46.66s | Tokens: 5519*

### Grok (grok-4.20-beta)

**## Position**

Use **dimension-first folders** (the 6 broad knowledge dimensions) as the primary sidebar hierarchy, with **Folder Notes** as the clickable "MOC" for each node, **auto-generated prefixed tags**, and **Breadcrumbs** for explicit parent/child relationships. Reject both pure flat + Dataview (A/D) and pure product-first (B). This is the only approach that matches how an ADHD pre-sales engineer actually *orients* in a large vault.

## Rationale

- **The sidebar is the only navigation Rob will reliably use.** Every Obsidian power user says "just use search/MOCs," but Rob has ADHD and opens the vault to *work*, not to admire his system. A visible tree that matches his mental model (Industry → Product → Client) beats "open dashboard then run 17 Dataview queries" every single time.
- **The 6 dimensions already exist in the taxonomy.** We're ignoring a perfectly good ontology because the community fetishizes flat vaults. Making `Industry`, `Product`, `Implementation`, `Technology`, `Sales`, `Marketing` the top-level folders costs almost nothing and immediately gives future functions (marketing, services) their own clean entrypoints.
- **Tags + folders are not mutually exclusive.** The council keeps treating this as an either/or. Auto-generate both `tags: product/wms, client/lenzing, domain/security` *and* put the note in the most relevant dimension folder (with symlinks or Folder Notes handling the multi-belonging problem). This gives native tag pane, graph coloring, and sidebar browsing simultaneously.
- **Folder Notes + Breadcrumbs beats pure MOCs.** A folder called "WMS" that *is* the note (via Folder Note plugin) gives Rob the drill-down pattern he described with zero extra clicks. Breadcrumbs lets him define `parent: [[WMS]]` even when the note lives in multiple dimensions.
- **Zero daily maintenance is non-negotiable.** The only sustainable path is `corp-by-os` doing the renaming (`2026-03-22_lenzing_wms_disaster_recovery.md`) *and* injecting both frontmatter *and* the `tags:` field at ingest time. Hand-curated MOCs will die within three weeks.

## Trade-offs

- Gives up the "pure Zettelkasten" purity that Obsidian Twitter worships. Some notes will live in one dimension folder even though they touch multiple.
- Slightly higher cognitive load on the ingest pipeline (corp-by-os must make smart folder decisions).
- Dataview queries become slightly more complex because notes are no longer in one flat folder (but still totally workable).
- Sacrifices the "everything is a query" idealism for pragmatic human navigation.

## Risks

- **Risk: Folder sprawl / poor auto-routing decisions.**  
  *Mitigation:* Make the dimension assignment deterministic in corp-by-os based on the existing `domains` field from CKE. Add a fallback "Misc" folder + weekly report of ambiguous notes.

- **Risk: Tag taxonomy drift.**  
  *Mitigation:* Lock the taxonomy in code (`product/`, `client/`, `industry/`, `domain/`). Generate the `tags:` field automatically. Never let Rob create tags manually.

- **Risk: Performance with 4000+ notes in Dataview.**  
  *Mitigation:* Be extremely disciplined about `WHERE` clauses. Use `dv.pages("#product/wms")` instead of string matching. Monitor query speed; have a fallback "WMS Index" note with pre-rendered tables if needed.

- **Risk: Rob ignores the system.**  
  *Mitigation:* The homepage (using Homepage plugin) should be a *single* dashboard that shows: this week's calls, new notes by dimension, stale notes, and one-click links to the 6 dimension folders. First thing he sees every morning must be useful in <10 seconds.

**Recommended plugin stack (exactly 5):**
- Dataview (non-negotiable)
- Folder Note
- Breadcrumbs
- Homepage
- Omnisearch

Skip Kanban, Calendar, Excalidraw, Graph (for now). The built-in Graph only becomes useful *after* we have consistent `[[links]]` and tagged notes. It is not a starting point.

**Homepage design:** A single "Monday Morning" note with:
- This week's client calls (hardcoded or templated)
- "New this week" per dimension
- Stale content alerts
- Quick links to the 6 dimension folders

This structure directly supports the drill-down pattern Rob described while remaining compatible with automated ingest and future business functions. Everything else the council is debating is rearranging deck chairs.

*Latency: 20.92s | Tokens: 4357*

## Round 2: Critique

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, my evaluation of these proposals is grounded in system resilience, data lineage, and minimizing threat surfaces. We are integrating an LLM extraction pipeline (CKE), an automated ingest script (`corp-by-os`), a local Obsidian vault with a strict 100MB sync limit, and an external FTS5 search index (`corp retrieve`). 

Any architectural decision that introduces dynamic file paths, arbitrary code execution via community plugins, or complex script-driven data mutation is a critical risk to interoperability and supply chain security.

Here is my evaluation of the council's proposals.

---

### Evaluation of Proposal A
**Position:** Partially Agree (Flat + MOCs is correct, but hybrid manual/auto generation is dangerous).
*   **Strongest point:** Decoupling storage from navigation (Flat storage + virtual MOCs). This is integration-safe. It allows `corp retrieve` to index stable file paths without worrying about nested folder structures changing.
*   **Weakest assumption:** The "hybrid UX layer" where Rob hand-edits the intros of auto-generated MOCs. If `corp generate-mocs` runs deterministically on a schedule, it will overwrite Rob's manual edits unless the script includes complex, brittle logic to parse and preserve specific text blocks. This guarantees eventual data loss.
*   **Overlooked risks:** Supply chain risk via **Templater**. Templater allows arbitrary JavaScript execution and filesystem writes from within Obsidian. Installing it to generate "consistent MOC shells" when an external script (`corp-by-os`) is already responsible for generation is an unnecessary expansion of the attack surface.

### Evaluation of Proposal B
**Position:** Partially Agree (Right physical architecture, but over-engineers the metadata).
*   **Strongest point:** Acknowledging the Obsidian Sync 100MB limit and explicitly proposing external cloud storage for heavy attachments. This is a critical operational integration requirement that others missed.
*   **Weakest assumption:** Assumes the **Breadcrumbs** plugin adds enough value to justify injecting proprietary `parent: [[...]]` relationships into the frontmatter. This tightly couples our automated ingest pipeline to the schema of a third-party Obsidian plugin, creating vendor lock-in and integration fragility. 
*   **Overlooked risks:** Data mutation risk. The proposal suggests auto-inserting `[[MOC_Product_WMS]]` links *directly into the body* of the notes during ingest. Automated scripts mutating the body text of LLM-extracted markdown introduces a high risk of corrupting the source extraction. Integration scripts should strictly manipulate frontmatter, never the core payload.

### Evaluation of Proposal C
**Position:** Agree (Highly aligned with secure integration principles).
*   **Strongest point:** The explicit focus on minimizing the plugin attack surface (Supply Chain Trust) and enforcing system-safe constraints like filename length truncation and taxonomy validation at the ingest layer. It correctly identifies that Dataview and Omnisearch possess deep read access and require vetted updates.
*   **Weakest assumption:** Assumes that leaving the native file explorer as a "useless wall of 4000+ notes" will not severely impact user adoption. Even for an ADHD user heavily reliant on search, having zero physical grouping can be disorienting if the Dataview plugin fails to load or requires an update.
*   **Overlooked risks:** Single Point of Failure (SPOF). By relying entirely on Dataview for all drill-down navigation, a single breaking update to the Dataview plugin instantly degrades the entire vault to a flat folder of unlinked text files.

### Evaluation of Proposal D
**Position:** Disagree (Introduces severe integration and data integrity risks).
*   **Strongest point:** Recognizing the psychological reality of the user: visible file trees provide immediate spatial orientation without relying on third-party plugin rendering (like Dataview).
*   **Weakest assumption:** Assumes `corp-by-os` can deterministically route a highly multi-dimensional note (e.g., covering WMS, Lenzing, and Security) into a *single* primary dimension folder without creating a messy "Misc" bucket or relying on symlinks. 
*   **Overlooked risks:** Broken integrations. Moving files across folders dynamically (if a note's primary dimension changes) breaks absolute paths in the `corp retrieve` database. Furthermore, it advocates for the **Folder Note** plugin, which hijacks native UI behaviors and often creates filesystem conflicts with sync engines like Obsidian Sync. Using symlinks inside an Obsidian vault is a known anti-pattern that frequently causes infinite sync loops and application crashes.

---

### Revised Architect Recommendation

To satisfy Rob’s UX requirements while enforcing defense-in-depth, strict data lineage, and safe interoperability between heterogeneous systems, the architecture must rely on **dumb storage and smart, decoupled indexes**. 

We will implement **Option D (Flat Storage + Auto-generated MOCs)** with strict security guardrails.

**1. Filesystem & Storage (The "Dumb" Layer)**
*   **Structure:** `01_knowledge/` must remain completely flat. Folders are an operating system primitive, not a database tagging system. 
*   **Naming Convention:** Enforce `{YYYY-MM-DD}_{source_filename_sanitized}_{short_hash}.md`. Truncate at 64 characters. The short hash (e.g., `a7b2`) prevents filesystem collision and race conditions during high-volume asynchronous ingest.
*   **Media:** Block `.png`/`.pdf` from syncing to Obsidian Sync. `corp-by-os` must host media on a secure internal web server and inject standard Markdown web links (`![image](https://corp-media/...)`) into the notes. This guarantees we never breach the 100MB vault limit.

**2. Ingestion & Taxonomy (The Integration Layer)**
*   **Read-Only Payload:** `corp-by-os` writes the Markdown body exactly as extracted by CKE. No regex replacements, no auto-injected `[[links]]` in the body.
*   **Hardcoded Validation:** `corp-by-os` must validate all CKE-generated domains/products against a static list. Hallucinated taxonomy tags are routed to a `#taxonomy-anomaly` tag, preventing tag explosion.
*   **Native Tags:** `corp-by-os` generates a native `tags:` array in the frontmatter using hierarchical prefixes: `#product/wms`, `#client/lenzing`, `#domain/industry/retail`. This provides immediate, zero-plugin visual filtering in Obsidian's native UI.

**3. Presentation & UX (The "Smart" Layer)**
*   **Zero-Touch MOCs:** `corp generate-mocs` runs on the ingestion server, outputting flat Markdown tables to a `00_mocs/` folder. **Do not use the Dataview plugin for core MOC rendering.** Pre-rendering MOCs as static markdown tables via the external script ensures that even if Obsidian plugins break, the drill-down navigation still works perfectly for Rob. 
*   **Dashboard:** Use **Dataview** *only* on the Homepage for ephemeral data (e.g., "Notes extracted in the last 48 hours", "Stale notes"). 
*   **Plugin Allowlist:** 
    1.  **Omnisearch** (For robust FTS).
    2.  **Homepage** (To enforce the start screen).
    3.  **Dataview** (Strictly scoped to the Homepage dashboard).
*   **Plugin Denylist:** Templater, Folder Note, Breadcrumbs, Excalidraw. We will not allow plugins that execute arbitrary JS, hijack file system behaviors, or define proprietary metadata schemas. 

**Summary for Rob's Workflow:**
When Rob opens Obsidian, the Homepage plugin loads `Home.md`. Dataview shows his daily calendar and recent extracts. He clicks the pre-rendered `MOC_Clients.md` link, clicks `Lenzing`, and sees a static, auto-generated index of all Lenzing notes. The system requires zero manual maintenance, utilizes native Obsidian tag trees, scales cleanly to 4000+ notes, and eliminates supply chain and integration risks.

*Latency: 37.50s | Tokens: 12891*

### Deepseek (deepseek-reasoner)

## Assessment of Proposals

### Proposal A: Flat + MOC Hybrid
**Position:** Partially agree with core architecture, disagree with implementation specifics.

**Strongest point:** Pragmatic recognition that auto-generated MOCs are non-negotiable for zero-maintenance. Correctly identifies metadata quality as the critical dependency.

**Weakest assumption:** That separating MOCs into `02_MOCs/` subfolders improves sidebar browsing. This creates a parallel hierarchy requiring manual synchronization with actual taxonomy. Performance cost: every Dataview query in a MOC must scan 4000+ flat files anyway—folder separation adds no efficiency while adding cognitive load.

**Overlooked risks:**
1. **Query performance degradation:** Unoptimized Dataview queries on 4000+ notes will cause observable UI lag (200-500ms per query). Homepage with 5-6 queries could take 2+ seconds to render.
2. **Memory overhead:** Each MOC regenerates queries on open, creating redundant computation. With 50+ MOCs, this wastes RAM during extended sessions.
3. **Taxonomy synchronization risk:** Hardcoded `02_MOCs/products/WMS.md` must match tag `#product/wms`. Drift between folder names and tags creates dead navigation.

### Proposal B: Flat + Hierarchical Tags + Breadcrumbs
**Position:** Partially agree on tags, disagree on Breadcrumbs.

**Strongest point:** Explicit computational efficiency analysis—recognizes FTS5 indexing benefits of flat storage and quantifies Dataview latency (hundreds of ms). Correctly identifies sync bandwidth as a constraint.

**Weakest assumption:** That Breadcrumbs adds meaningful hierarchy without maintenance cost. Breadcrumbs requires `parent` frontmatter fields, creating another metadata dependency. ADHD users won't maintain these relationships manually, and auto-population adds ingest complexity for marginal UX gain.

**Overlooked risks:**
1. **Graph performance at scale:** 4000+ nodes with multi-dimensional links becomes unrenderable (>10s load time) without aggressive filtering. Not addressed.
2. **Plugin conflict surface:** Breadcrumbs + Dataview + Omnisearch have overlapping query mechanisms that could conflict or duplicate work.
3. **No query optimization strategy:** Accepting "hundreds of milliseconds" per query is insufficient—homepage with 10 queries could freeze UI for 3+ seconds.

### Proposal C: Flat + Minimal Plugins + Strict Taxonomy
**Position:** Mostly agree—most architecturally sound.

**Strongest point:** Supply chain security analysis and explicit rejection of unnecessary plugins. Recognizing that CKE must enforce taxonomy at extraction (not later) prevents tag explosion. File naming with collision handling shows production thinking.

**Weakest assumption:** That tag pane alone provides sufficient navigation. For ADHD visual browsing, tag pane with 1000+ tags becomes another "wall" requiring search within tags.

**Overlooked risks:**
1. **Ingest pipeline complexity:** CKE validation against hardcoded taxonomy requires version synchronization between taxonomy updates and extraction model.
2. **No fallback for failed Dataview:** If Dataview breaks, the entire navigation collapses. No layered degradation strategy.
3. **Memory consumption:** Graph view with 4000 nodes colored by tags requires ~200MB RAM—could crash Obsidian on lower-end machines.

### Proposal D: Dimension-First Folders
**Position:** Disagree—architecturally regressive.

**Strongest point:** Correct observation that sidebar is primary navigation for ADHD users. Understanding that "open dashboard then run queries" adds cognitive load.

**Weakest assumption:** That folder-based classification can handle multi-dimensional notes without duplication or symlinks. This either forces arbitrary single-folder placement (breaking other dimensions) or requires symlinks (doubling storage, breaking sync, complicating ingest). Performance impact: `corp retrieve` FTS5 must now traverse multiple folder levels, increasing query latency 30-50%.

**Overlooked risks:**
1. **Folder assignment algorithm complexity:** Determining "most relevant dimension" requires NLP or scoring heuristics—prone to misclassification.
2. **Multi-product note problem unsolved:** Note about WMS+Planning must go somewhere—whichever dimension gets it becomes incomplete.
3. **Future restructuring cost:** When dimensions evolve (e.g., adding "AI/ML" as new domain), notes must be physically moved.

## Revised Recommendation

**Core Architecture:** Flat storage (`knowledge/`) with **auto-generated prefixed tags** and **virtual MOCs via dynamic queries**, but with **Folder Notes for sidebar navigation without classification**.

### 1. Folder Structure (Performance-Optimized)
```
knowledge/           # All extracted notes flat (4000+ files)
  _mocs/            # Auto-generated MOC notes (not folders)
  _dashboards/      # Homepage and summary views
templates/          # System templates
attachments/        # External links only
```

**Why:** Single flat folder minimizes file system traversal for both Dataview and FTS5. `_mocs/` subfolder keeps auto-generated content separate but accessible. No dimension folders—classification happens via tags only.

### 2. Navigation Pattern (Click-Optimized)
```
Open Obsidian → Home.md (auto)
→ Click sidebar folder "MOCs" (virtual via Folder Note plugin)
→ See expandable tree: Products/ Clients/ Domains/ Recent/ Quality
→ Click "Products > WMS" (actually opens `_mocs/WMS.md`)
→ See pre-rendered Dataview sections (cached queries)
```

**Performance trick:** Use Folder Note plugin to make `_mocs/` appear as a folder with clickable subfolders (Products, Clients, etc.) without actual nested directories. Each "folder" is a note with queries filtered by tag prefix.

### 3. Auto-Generation Strategy
- **CKE extracts and normalizes** to controlled taxonomy
- **corp-by-os ingests:**
  1. Renames file: `YYYY-MM-DD_{source_slug}.md`
  2. Generates prefixed tags: `#product/wms`, `#client/lenzing`, `#domain/security`
  3. **Pre-computes MOCs:** Runs `corp generate-mocs` to create `_mocs/WMS.md` with **cached query results** as static lists (not live queries)
  4. Updates homepage dashboards with summary counts

**Why pre-computed:** Eliminates Dataview query latency at navigation time. Trade-off: MOCs are stale until next ingest. Acceptable because ingest runs daily.

### 4. Plugin Stack (Minimal + Performant)
1. **Dataview** (essential for dynamic queries in curated pages only)
2. **Folder Note** (enables sidebar navigation without actual folders)
3. **Homepage** (sets command center as default)
4. **Omnisearch** (fallback search with better FTS5 integration than native)
5. **Templater** (for consistent manual note creation)

**Reject Breadcrumbs:** Adds parent-child maintenance without sufficient UX gain.
**Reject Graph enhancements:** Not reliable at 4000+ nodes.

### 5. Knowledge Graph Utility
**Only useful if:**
- Notes auto-link to relevant MOC notes (`[[_mocs/WMS]]`)
- Graph view defaults to **local graph** (depth=2) centered on current note
- Colors by top-level tag prefix (`product/`, `client/`, `domain/`)

Implement auto-linking during ingest: each note gets `[[_mocs/WMS]]` for each product tag.

### 6. Homepage Design (60-second ready)
```markdown
## This Week ({{Monday date}})
- **Client Calls Today:** [[Lenzing]], [[Michelin]]
- **New Notes (7d):** 42 [[Recent]]
- **Stale Alerts:** 3 notes >6mo [[Quality]]

## Navigate
📦 **Products:** WMS | Planning | Platform  
👥 **Clients:** Lenzing | Michelin | SGDBF  
🌐 **Domains:** Security | Industry | Technology  
🕒 **Recent Notes** | ⚠️ **Quality Check**

## Quick Search
{{Omnisearch widget}}
```

### 7. Multi-Product Solution
**Never duplicate files.** Use:
- Tags: `#product/wms` `#product/planning`
- Auto-links: `[[_mocs/WMS]]` `[[_mocs/Planning]]`
- MOC queries: `WMS.md` searches `#product/wms`, `Planning.md` searches `#product/planning`

Both MOCs show the note. No storage duplication.

### 8. Performance Quantification
- **File operations:** Flat folder = O(1) path resolution vs O(n) folder tree traversal
- **Query latency:** Pre-computed MOCs = 50ms load vs 300ms+ for Dataview queries
- **Sync overhead:** No symlinks/duplicates = minimal storage (~100MB for 4000 notes)
- **Memory:** Local graph only = ~50MB vs 200MB+ for full graph

### 9. Risk Mitigation
1. **Metadata quality:** CKE must validate against enumerated taxonomy; unknown tags go to `#needs-review`
2. **Query breakdown:** Homepage uses simple static links; only MOCs use Dataview
3. **Performance decay:** Schedule weekly re-indexing of Omnisearch and Dataview
4. **Taxonomy drift:** Version taxonomy file; CKE rejects notes with invalid tags

## Implementation Priority

**Phase 1 (Week 1):**
- Implement corp-by-os with tag generation and file renaming
- Create homepage with static links
- Install Folder Note + Omnisearch

**Phase 2 (Week 2):**
- Implement `corp generate-mocs` with pre-computed queries
- Set up auto-linking during ingest
- Configure local graph defaults

**Phase 3 (Week 3):**
- Add stale note detection
- Create quality dashboard
- Optimize query caching

This architecture delivers:
- **Sub-2-second navigation** from vault open to target note
- **Zero daily maintenance** (all auto-generated)
- **Scalable to 10k+ notes** (flat storage + pre-computed indices)
- **Multi-dimensional access** without duplication
- **ADHD-friendly visual browsing** via Folder Note sidebar

The key insight: **Pre-compute navigation indices at ingest time** rather than querying live. This trades slight staleness (acceptable for knowledge base) for massive UX performance gains.

*Latency: 147.64s | Tokens: 13311*

### Openai (gpt-5.4)

Here’s the blunt council read, optimized for shipping reality.

---

# Proposal A

## Position: **Partially agree**

A is the closest to workable. Flat storage + MOCs is the right core architecture. But it overestimates how much Rob will tolerate a “dashboard-first” interaction model if the sidebar remains mostly abstract. It’s good architecture; slightly less good day-to-day UX.

## Strongest point
**Separating storage from navigation is the right move.**  
That cleanly solves the WMS+Planning problem, keeps ingest simple, and avoids creating endless routing edge cases for automation.

## Weakest assumption
**That Rob will happily navigate primarily through MOCs and homepage links.**  
Maybe sometimes. But in practice, users with ADHD often fall back to the most visible, low-friction UI element: the sidebar and search. If the file tree is “not the classification layer,” you need to make sure the MOC tree itself is sidebar-browsable and dead simple, or he’ll ignore it.

## Risks it overlooks
- **MOC proliferation becomes its own clutter problem.** Even if notes are flat, 300+ MOC files can become another wall of stuff unless indexes are layered carefully.
- **Dataview brittleness in daily use.** If metadata quality is uneven, Rob won’t say “the taxonomy is immature”; he’ll say “Obsidian is unreliable.”
- **No explicit stance on how much curated content is realistic.** “Light hand-editing” sounds nice until nobody owns it.

---

# Proposal B

## Position: **Partially agree**

The flat + MOC direction is sound. The plugin stack is not. Breadcrumbs is unnecessary complexity for this team and this problem.

## Strongest point
**Good emphasis on hierarchical tags as a native backup navigation layer.**  
That matters. Depending entirely on Dataview is fragile; native tags give resilience and improve search, tag pane, and graph filtering.

## Weakest assumption
**That Breadcrumbs adds enough value to justify operational complexity.**  
It doesn’t, not now. Breadcrumbs is great when you have disciplined parent/child curation. This team does not have the maturity or appetite for maintaining semantic hierarchies beyond what can be generated automatically. MOCs already provide the drill-down. Breadcrumbs is a second hierarchy system you’ll have to debug.

## Risks it overlooks
- **Parent-child auto-generation can create nonsense.** If Breadcrumbs is fed mechanically, you’ll get formally correct but cognitively useless hierarchies.
- **Plugin burden.** Every extra plugin is another support surface, sync risk, and “why is this weird today?” moment.
- **Tag pane limits.** Hierarchical tags help, but with many clients/topics, native tag browsing can still get noisy.

---

# Proposal C

## Position: **Partially agree**

C is technically disciplined and operationally sane. But it is too purist about minimizing plugins and too dismissive of sidebar UX.

## Strongest point
**Excellent focus on deterministic ingest, taxonomy control, and operational safety.**  
This is the most production-minded proposal. The warnings about taxonomy drift, path length, collisions, and plugin supply chain are valid.

## Weakest assumption
**That Rob can live without a useful sidebar/tree experience.**  
No. “Use homepage + search + tag pane” is architecturally neat but behaviorally wrong for the user described. The file explorer being useless is not an acceptable UX outcome if visual browsing is a stated requirement.

## Risks it overlooks
- **Search becomes the de facto primary UX.** That undermines the whole “tree of knowledge” requirement.
- **Tag pane is not a substitute for drill-down pages.** Tags are filters, not explanations.
- **Over-minimizing plugins can hurt usability more than it helps security.** This is an internal vault, not a zero-trust production runtime.

---

# Proposal D

## Position: **Disagree**

This is the most user-sympathetic proposal, but it asks the ingest pipeline to do too much and creates long-term classification debt. It optimizes for a comforting sidebar at the expense of system integrity.

## Strongest point
**It takes the sidebar seriously.**  
That’s important. Many Obsidian designs ignore that users browse what they can see.

## Weakest assumption
**That auto-routing notes into one “most relevant” dimension folder is sustainable and low-risk.**  
It isn’t. This is exactly how you create ambiguity, inconsistent placement, and future arguments about where things belong. Multi-dimensional knowledge does not want a primary physical home chosen by heuristic. Especially not at 2k–4k notes with zero-maintenance constraints.

## Risks it overlooks
- **Misfiled notes silently degrade trust.** A wrong folder is more damaging than a missing query result because users assume folders are authoritative.
- **Cross-dimension duplication pressure.** Once users expect folder browseability, they’ll want things to appear in multiple places physically.
- **Symlink/folder-note style workarounds increase complexity fast.** Nice in theory; annoying in a real sync’d vault.
- **Future taxonomy shifts become painful.** If the ontology evolves, physical placement becomes migration work.

---

# Revised recommendation

## Decision
Choose **D-from-the-earlier-options: flat storage + MOC-driven navigation**, but implement it as a **visible navigation layer in folders** so the sidebar is useful.

In other words:

- **Keep knowledge notes physically flat**
- **Put generated navigation notes in a clear folder tree**
- **Do not use folders to classify source notes**
- **Do use folders to classify navigation entry points**

That’s the pragmatic middle ground between A/C and D.

---

# What I recommend

## 1) Folder structure

Use this:

```text
00_Home/
  Home.md

01_Knowledge/
  [all source notes flat]

02_Navigate/
  Products/
    Products.md
    WMS.md
    Planning.md
    Platform.md
    TMS.md
  Clients/
    Clients.md
    Lenzing.md
    Michelin.md
    SGDBF.md
  Domains/
    Domains.md
    Industry_Knowledge.md
    Product_Knowledge.md
    Implementation_Services.md
    Technology.md
    Sales_Customer_Executive.md
    Marketing.md
  Topics/
    Topics.md
    Disaster_Recovery.md
    Security.md
    Competitive.md
  Recent/
    Recent.md
  Quality/
    Quality.md

03_Templates/
04_Attachments/
99_System/
```

### Why this is the right compromise
- Rob gets a **real sidebar tree**
- Ingest remains simple because source notes stay flat
- Multi-product/client/domain notes appear in multiple places via queries
- Future expansion is easy
- No arbitrary physical filing decisions for source notes

This is the key adjustment I’d make versus Proposals A/B/C:  
**make the navigation layer itself browsable in the sidebar.**

---

## 2) Navigation pattern

Rob should not have to “figure out the system.” The click path must be obvious.

### Primary path
```text
Open Obsidian
→ Home.md
→ Click Products / Clients / Domains / Recent / Quality
→ Click entity page (e.g. Lenzing or WMS)
→ Use sectioned MOC page
→ Open note
```

### Sidebar path
```text
Left sidebar
→ 02_Navigate
→ Clients
→ Lenzing
```

### Search fallback
```text
Cmd/Ctrl+O or Omnisearch
→ type phrase/vendor/topic
→ open note or MOC
```

The important thing:  
**homepage, sidebar, and search must all converge on the same MOC pages.**  
Not three different systems.

---

## 3) MOCs: auto-generated first, selectively curated later

### Base rule
**Auto-generate all MOCs.** No debate.

### But:
Allow a fixed hand-curated intro block at the top of selected pages:
- top 5 products
- top 10 clients
- competitive landing page
- maybe one “Pre-Sales Command Center”

Everything below that is generated.

### Why
- Fully manual dies
- Fully generated can feel sterile
- Mixed model is the only maintainable compromise

### Practical implementation
Generated pages should preserve content between markers:

```md
<!-- BEGIN CURATED -->
[human-written summary, key links, call prep notes]
<!-- END CURATED -->

<!-- BEGIN GENERATED -->
[dataview sections]
<!-- END GENERATED -->
```

That keeps regeneration safe.

---

## 4) Plugin stack: keep it lean

My recommendation: **4 plugins, maybe 5**

### Must-have
1. **Dataview**  
   Non-negotiable. Powers MOCs and dashboards.

2. **Homepage**  
   Essential for fast start and reducing context switching.

3. **Omnisearch**  
   Necessary because people remember phrases, not taxonomies.

4. **Folder Note**  
   Useful if you want index notes for navigation folders. Not mandatory, but good UX.

### Optional 5th
5. **Templater**  
   Only if you need reliable generation templates or manual note shells.

## Do not prioritize now
- **Breadcrumbs** — too much semantic hierarchy overhead for too little gain
- **Kanban** — separate workflow problem
- **Calendar** — nice but not core
- **Excalidraw** — useful later, not navigation-critical

I disagree with B and D here: **Breadcrumbs is not worth it in phase 1.**

---

## 5) Homepage design

This should be a **command center**, not a report dump.

## Homepage should show:
- **This week / key clients**
- **Recent notes added in last 7 days**
- **Stale notes or low-confidence notes**
- **Quick links:** Products, Clients, Domains, Recent, Quality
- **Pinned shortcuts:** WMS, Planning, Platform, Lenzing, Michelin
- **Search hint:** “Use Omnisearch for exact phrases”

## It should not show:
- giant 100-row tables
- the whole universe of notes
- fancy widgets nobody maintains

The homepage exists to answer:
1. What changed?
2. What matters now?
3. Where do I click next?

---

## 6) Tags: yes, auto-generate them

## Decision
Generate tags **at ingest time in corp-by-os**, not later.

Why:
- deterministic
- visible immediately in Obsidian
- easier to debug
- avoids post-processing drift

## Taxonomy
Use **prefixed hierarchical tags**, not flat tags.

Example:

```yaml
tags:
  - product/wms
  - product/planning
  - client/lenzing
  - domain/technology
  - topic/disaster-recovery
  - source/rfp
  - competitor/oracle
```

### Why prefixed wins
- no collisions
- cleaner tag pane
- future-proof for multiple business functions
- graph/search are much more usable

### Guardrail
Only generate tags from controlled vocab fields.  
No free-form tag creation by users.

---

## 7) File naming: enforce it on ingest

Yes, rename files on ingest.

Recommended format:

```text
YYYY-MM-DD_source-filename-normalized.md
```

With collision safety:

```text
YYYY-MM-DD_source-filename-normalized_shortid.md
```

Example:

```text
2026-03-22_sgdbf_architectural_requirements_a7b2.md
```

Also store traceability in frontmatter:

```yaml
source_filename: SGDBF_Architectural_Requirements.pdf
source_path: ...
ingested_at: 2026-03-22T10:15:00Z
```

One tweak to prior proposals: **add a short ID by default or when needed**, because source filenames are not reliably unique in enterprise content.

---

## 8) Knowledge graph: secondary only

Graph View is **not** a primary navigation tool here.

It becomes useful only if:
- tags are consistent
- notes link to their related MOCs
- MOCs act as hubs

Then it can help with:
- spotting orphan notes
- seeing clusters around WMS / Security / Lenzing
- quality review

But it is not how Rob should prep for a call in 30 minutes.

So the answer is:
- **support graph**
- **don’t design around graph**

---

## 9) The WMS + Planning problem

Solved entirely by metadata + MOCs + tags.

Example:

```yaml
products:
  - WMS
  - Planning
clients:
  - SGDBF
domains:
  - Technology
topics:
  - Disaster Recovery
tags:
  - product/wms
  - product/planning
  - client/sgdbf
  - domain/technology
  - topic/disaster-recovery
```

Then:
- WMS MOC shows it
- Planning MOC shows it
- SGDBF MOC shows it
- Disaster Recovery MOC shows it

No duplication. No ambiguity. No filing drama.

This is why Proposal D’s dimension-folder routing is the wrong abstraction for source notes.

---

# What I’d actually ship in phases

## Phase 1: 1–2 weeks, real MVP
- Flat `01_Knowledge`
- `00_Home` and `02_Navigate` folder tree
- Auto-generated MOCs for:
  - products
  - clients
  - domains
  - top topics
- Dataview + Homepage + Omnisearch
- Auto-generated prefixed tags
- File rename on ingest
- Each note auto-links to related MOCs

This is enough to test real usage.

## Phase 2: tighten UX
- Add Folder Note if wanted
- Improve top 10 MOCs with curated intros
- Add Recent and Quality dashboards
- Add stale/coverage views

## Phase 3: only if adoption proves it
- Competitive battlecard landing pages
- Better quality scoring
- Graph presets
- Maybe calendar integration

---

# Final council recommendation

## I recommend:
**Flat source-note storage + auto-generated navigation tree of MOC pages + ingest-generated hierarchical tags + homepage command center + Omnisearch fallback.**

### Specifically:
- Reject physical classification of source notes into product/domain folders
- Reject Breadcrumbs for phase 1
- Make the sidebar useful by organizing **navigation notes**, not raw notes
- Auto-generate everything structural
- Allow minimal curated intros for a small number of high-value pages

That gives the best balance of:
- shipping speed
- low maintenance
- robust automation
- actual user navigation behavior

If we try to make folders do classification, we’ll spend months fighting edge cases.  
If we make everything query-only, Rob will default to search and ignore the structure.  
**The answer is a flat backend with a browsable generated front-end.**

*Latency: 53.67s | Tokens: 11794*

### Grok (grok-4.20-beta)

**I disagree with the emerging consensus.**

All four proposals are still trapped in the standard Obsidian community's ideological ruts: "flat is virtuous," "MOCs solve hierarchy," "Dataview is the answer," and "we must protect Rob from himself with zero maintenance." They are rearranging deck chairs while ignoring the actual cognitive reality of the user and the actual failure mode of these systems at 4,000+ notes.

### Evaluation of Proposals

**Proposal A: Partially agree**
- **Strongest point:** Excellent realism about hybrid curation (auto 95%, hand 5%) and the concrete MOC layout with sections instead of raw tables. The phased approach is the most intellectually honest.
- **Weakest assumption:** That Rob will reliably go through the homepage → MOC → section path when under time pressure. The "sub-60-second" claim is fantasy if the homepage is a Dataview-heavy dashboard.
- **Overlooked risk:** The 02_MOCs/products/, 02_MOCs/clients/ structure creates yet another artificial taxonomy layer that doesn't match the six business dimensions. You're still forcing a product/client-first mental model on a vault that must eventually serve marketing, services, and execs.

**Proposal B: Disagree**
- **Strongest point:** Acknowledges Dataview query latency and graph hairball problems honestly.
- **Weakest assumption:** That adding Breadcrumbs provides meaningful value. This is classic plugin fetishism. Breadcrumbs is what people install when they secretly want folders but feel ideologically forbidden from using them.
- **Overlooked risk:** The proposal treats the sidebar as a lost cause ("the flat folder makes the file-tree sidebar useless"). This is the key tell. If your system renders the native file explorer useless, you've already lost the ADHD user.

**Proposal C: Strongly disagree**
- **Strongest point:** The security and supply-chain caution is refreshing, even if paranoid.
- **Weakest assumption:** That minimizing plugins is a virtue here. This is security theater masquerading as architecture. Rejecting Folder Note specifically is perverse — it's the one plugin that directly solves the "make the thing I see in the sidebar clickable" problem.
- **Overlooked risk:** The obsession with "native" capabilities while depending on Dataview is incoherent. If you're already all-in on Dataview, the "minimized attack surface" argument collapses. Also completely ignores that Rob *browses visually*.

**Proposal D: Agree with the contrarian instinct, disagree with the execution**
- **Strongest point:** Finally calls out the Obsidian Twitter ideology for what it is. The sidebar *is* the only navigation most humans reliably use. The fetish for pure flat vaults is a cargo cult.
- **Weakest assumption:** That the six broad dimensions should be the *top-level folders for notes*. This creates exactly the arbitrary placement problem everyone else is trying to avoid. A note about retail demand forecasting in a WMS RFP for Lenzing doesn't cleanly belong in one dimension folder.
- **Overlooked risk:** Poor auto-routing decisions will create constant "which folder?" churn in the ingest pipeline. The proposal underestimates how noisy this gets.

### What Everyone Is Missing

1. **The ADHD navigation reality:** Rob will use whatever is most visible and requires least friction *in the moment*. When he has 25 minutes before a Lenzing call, he will not open a dashboard and run queries. He will scan the sidebar or click something that looks like a folder named "Lenzing" or "WMS."

2. **The metadata quality problem:** All proposals assume CKE will produce clean, consistent `products`, `clients`, `domains`. This is delusional. LLM extraction is probabilistic. Any system that falls apart when metadata is imperfect is fragile by design.

3. **The "tree vs lattice" tension:** Rob's drill-down pattern is a *tree* (WMS → Architecture → DR). The knowledge itself is a *lattice* (one note belongs to multiple dimensions). The correct answer is to *present* trees while *storing* a lattice. Everyone is arguing about storage.

4. **Future users are not "future users" — they are cohabitants.** The vault must serve pre-sales *now* and services/marketing *soon* without becoming incomprehensible to either.

### My Revised Recommendation (Contrarian Position)

**Folder structure: Limited dimension-first with aggressive flattening inside**

```text
00_Home/
01_Knowledge/
  Industry/
  Product/
  Implementation/
  Technology/
  Sales_Customer_Executive/
  Marketing/
  _Uncategorized/   (for metadata failures)
02_MOCs/            (only for cross-cutting or strategic pages)
03_Templates/
04_Attachments/
99_System/
```

Notes go into *one* dimension folder based on the *primary* domain from metadata (deterministic rule in corp-by-os). They get prefixed tags for all secondary dimensions. This gives Rob a usable sidebar *today* while still allowing multi-dimensional discovery via tags and MOCs.

This is not "pure" anything. It is pragmatic. The "pure flat" people are wrong for this use case. The "full folder hierarchy" people are also wrong.

**Navigation pattern:** Sidebar + Folder Notes as primary, MOCs as secondary, search as tertiary. 
- Click `Product/WMS/` (Folder Note) → gets the overview + Dataview sections.
- Breadcrumbs show the conceptual parent even if the file lives elsewhere.
- Homepage is *minimal* — basically "today's calls + new notes by dimension + search bar." No giant Dataview tables.

**Auto-generation:** Auto-generate the MOCs and the *structure* of dimension index notes. Allow light human editing only on the top 8-10 most important ones. `corp generate-mocs` runs on ingest and only touches the generated sections (clearly marked with `%% GENERATED %%`).

**Plugin stack (exactly 4):**
- Dataview (unavoidable)
- Folder Note (makes the sidebar actually work)
- Homepage (minimal dashboard)
- Omnisearch (the escape hatch)

Reject Breadcrumbs (too much complexity), reject Graph View as primary (it's a diagnostic tool, not a daily driver), reject Kanban/Calendar/Excalidraw for now.

**Knowledge graph:** Only useful *after* we have consistent backlinks to the dimension MOCs. Color strictly by top-level dimension tag. Use it to find orphans and bad metadata, not for daily work.

**Homepage:** Brutally simple. Three sections:
1. This week's calls (hardcoded or from simple query)
2. New this week by dimension (6 small lists)
3. Search bar with Omnisearch

**The "WMS + Planning" problem:** Primary dimension wins for folder placement. Tags and MOCs handle the rest. A note can live in `Product/` but appear in both WMS and Planning MOCs via queries.

**Tags:** Auto-generated at ingest, prefixed, hierarchical where it makes sense (`#product/wms`, `#client/lenzing`, `#domain/industry/retail`). But tags are the *secondary* system. The sidebar is primary.

**File naming:** Yes, enforce `YYYY-MM-DD_source-normalized_hash.md` on ingest. No debate.

**The six dimensions:** They *are* the top-level navigation. This is the part of Proposal D I agree with. Pretending products and clients are the only dimensions is short-term thinking. The taxonomy already exists — use it.

This is not the "correct" Obsidian architecture according to the internet. It is the correct architecture for *this specific human* with *this specific job* and *this specific cognitive style* in a vault that must serve *multiple future functions*.

Everything else the council is debating is aesthetic preference disguised as architecture.

*Latency: 29.84s | Tokens: 11049*

## Synthesis (by claude, non-participant)



# Architectural Decision Summary: Vault Navigation & UX

## Consensus

The council reached strong agreement on the following points:

**1. Source notes must be stored flat (or near-flat) for automation integrity.**
All four participants agreed that classifying source notes into deep folder hierarchies creates untenable edge cases for multi-dimensional notes (the "WMS + Planning" problem), breaks automated ingest pipelines, and introduces migration debt when taxonomies evolve. Even the contrarian position (Grok) acknowledged that full folder hierarchy "is also wrong" and proposed only a single level of dimension folders with flat contents inside.

**2. Auto-generation of navigation artifacts is non-negotiable.**
Given ADHD constraints and 2,000–4,000+ notes, every participant agreed that hand-curated navigation will decay and die. MOCs, dashboards, and index pages must be generated programmatically by `corp generate-mocs` or equivalent, triggered at ingest time.

**3. Tags must be auto-generated, prefixed, and taxonomy-controlled.**
Universal agreement on: generate `tags:` in frontmatter at ingest time from CKE metadata; use hierarchical prefixes (`#product/wms`, `#client/lenzing`, `#domain/security`); validate against a hardcoded controlled vocabulary; route unknown values to `#needs-review` or equivalent.

**4. File naming must be enforced on ingest.**
All agreed on `YYYY-MM-DD_source-filename-normalized.md` with collision handling (short hash suffix). Source traceability preserved in frontmatter.

**5. The multi-product/multi-dimension problem is solved by metadata, not folders.**
Tags + MOC queries ensure a note about WMS and Planning appears in both navigation paths without duplication or symlinks.

**6. Dataview is essential but creates a critical dependency.**
All acknowledged this is unavoidable. Mitigation strategies varied (pre-rendered static tables vs. live queries) but the dependency was universally recognized.

**7. Homepage plugin is required.**
Obsidian must open to a useful command center, not the last-viewed note. All four proposed this.

**8. Omnisearch is the necessary escape hatch.**
Search must be a first-class parallel navigation path, not a failure mode. Users remember phrases, not taxonomies.

**9. Graph View is secondary, not a daily navigation tool.**
Useful for diagnostics (orphans, clusters, metadata quality) only after tags and links are consistent. Not how Rob preps for a call.

**10. The six knowledge dimensions (Industry, Product, Implementation, Technology, Sales/Customer/Executive, Marketing) should be first-class navigation categories.**
All agreed these already exist in the taxonomy and should be surfaced, not just products and clients.

---

## Unresolved Disagreements

### 1. Should the sidebar file tree be a primary navigation surface?

**Pro-sidebar (Grok, partially OpenAI):** The sidebar is the most visible, lowest-friction UI element. ADHD users grab whatever is immediately visible. A flat `01_Knowledge/` folder with 4,000 files renders the most prominent Obsidian UI element useless. Putting navigation notes in browsable folder structures gives Rob something to click without opening a dashboard first.

**Anti-sidebar-for-notes (Gemini, DeepSeek):** Folders are an OS primitive, not a classification system. Any attempt to route notes into folders creates arbitrary placement decisions, misfiling risk, and migration debt. The sidebar should be replaced by homepage + tag pane + search as the primary surfaces.

**Why both have merit:** The pro-sidebar camp correctly identifies that ignoring the sidebar is a UX failure for a visual browser. The anti-sidebar camp correctly identifies that classifying *source notes* into folders is an integration and maintenance hazard. The resolution — which OpenAI arrived at most clearly — is to make *navigation notes* browsable in the sidebar while keeping source notes flat.

### 2. Should MOCs use live Dataview queries or pre-rendered static tables?

**Live queries (OpenAI, Grok):** Simpler to implement. Always current when viewed. Standard Obsidian pattern.

**Pre-rendered static tables (DeepSeek, Gemini round 2):** Eliminates query latency at read time. Provides degraded but functional navigation even if Dataview breaks. Better performance at 4,000+ notes.

**Why both have merit:** Pre-rendering is more resilient and faster at scale. Live queries are simpler to implement and always current. The practical difference matters most on the homepage (where multiple queries stack) and less on individual MOC pages (where a single scoped query is fast enough).

### 3. Folder Note plugin: valuable or risky?

**Pro (OpenAI, Grok, DeepSeek):** Makes navigation folders clickable as index notes. Directly solves "click WMS folder → see WMS overview." High UX value for low complexity.

**Anti (Gemini):** Hijacks native filesystem behaviors, creates sync conflicts, expands attack surface. Unnecessary if MOCs are standalone notes.

**Why both have merit:** Gemini's sync concern is legitimate for some configurations, but Folder Note is a mature, widely-used plugin with minimal real-world sync issues in Obsidian Sync. The UX benefit is concrete and immediate.

### 4. Breadcrumbs plugin: worth the complexity?

**Pro (DeepSeek round 1, Grok round 1):** Provides explicit parent-child hierarchy in frontmatter. Enables "WMS > Architecture > DR" drill-down navigation.

**Anti (OpenAI, Gemini, DeepSeek round 2, Grok round 2):** Adds metadata maintenance burden, creates plugin-specific schema coupling, provides marginal value over MOC-based navigation. All four participants ultimately converged on rejecting it for phase 1.

### 5. Should source notes live in dimension folders (shallow) or fully flat?

**Shallow dimension folders (Grok):** Put notes in one of six dimension folders based on primary domain. Gives the sidebar real content to browse. Accept that placement is imperfect; tags handle the rest.

**Fully flat (Gemini, DeepSeek, OpenAI):** Any folder-based routing for source notes introduces classification heuristics that will misfire, creating trust erosion and maintenance debt. Navigation should be entirely virtual.

**Why both have merit:** Grok is right that 4,000 files in one folder is genuinely bad UX in the sidebar. The flat camp is right that routing decisions will be wrong often enough to cause problems. The tension is real and unresolvable by pure logic — it depends on how much Rob actually uses the sidebar to browse raw notes vs. navigation pages.

---

## Recommended Decision

### Architecture: Flat source notes + browsable navigation tree + auto-generated tags

Adopt **Option D (flat storage + MOC-driven navigation)** with **a visible navigation folder tree for MOC/index notes** (the key UX adjustment OpenAI championed), auto-generated prefixed tags, and a minimal plugin stack.

```text
00_Home/
  Home.md

01_Knowledge/
  [all source notes flat, 4000+ files]

02_Navigate/
  Products/
    Products.md          ← index: links to all product MOCs
    WMS.md               ← sectioned MOC with Dataview queries
    Planning.md
    Platform.md
    TMS.md
  Clients/
    Clients.md
    Lenzing.md
    Michelin.md
    SGDBF.md
  Domains/
    Domains.md
    Industry_Knowledge.md
    Implementation_Services.md
    Technology.md
    Sales_Customer_Executive.md
    Marketing.md
  Topics/
    Topics.md
    Disaster_Recovery.md
    Security.md
    Competitive.md
  Recent/
    Recent.md
  Quality/
    Quality.md

03_Templates/
04_Attachments/           ← minimal; large media linked externally
99_System/
```

### Rationale

This structure resolves the core tension in the debate:

1. **Source notes stay flat** — no classification routing, no misfiling, no migration debt, `corp-by-os` writes to one directory, `corp retrieve` indexes stable paths. This satisfies Gemini's integration safety requirements and DeepSeek's performance analysis.

2. **Navigation notes live in a browsable tree** — Rob sees `02_Navigate/Products/WMS` in the sidebar and can click it. This satisfies Grok's and OpenAI's insistence that the sidebar must be useful. The tree reflects Rob's mental model (Products | Clients | Domains | Recent | Quality) without forcing source notes into arbitrary physical locations.

3. **Tags provide the lattice, folders provide the tree** — one note with `#product/wms` and `#product/planning` appears in both WMS.md and Planning.md via queries. The file lives in `01_Knowledge/`. No duplication, no symlinks.

4. **The six knowledge dimensions are first-class** — they appear under Domains in the navigation tree and as tag prefixes. Future users (marketing, services) get their own entry points without restructuring.

### Addressing the strongest objections

**Grok's objection: "The sidebar is useless with flat source notes."**
Acknowledged and partially addressed. The `02_Navigate/` tree gives the sidebar real structure. However, I did not adopt Grok's recommendation to put source notes into dimension folders because: (a) the multi-dimension classification problem is genuinely hard to automate reliably, (b) misfiled notes erode trust faster than an abstract sidebar improves it, and (c) the navigation tree provides the visual browsability Grok rightly demands without the classification risk. If Rob finds himself wanting to browse raw notes by folder, that signal should trigger a Phase 2 reassessment, not an upfront architecture commitment.

**Gemini's objection: "Folder Note hijacks filesystem behavior and expands attack surface."**
Acknowledged but overweighed. Folder Note is a mature, stable plugin with high adoption. The UX benefit (clicking a folder opens its index note) is substantial for this user profile. The sync risk is low with Obsidian Sync specifically. Include it as optional but recommended.

**DeepSeek's objection: "Live Dataview queries will be slow on the homepage."**
Acknowledged and mitigated. The homepage should use bounded, simple queries (recent 7 days, count summaries, stale alerts) not full-vault scans. Individual MOC pages use scoped queries (`WHERE contains(products, "WMS")`) which perform well even at 4,000 notes. If performance degrades, pre-rendering MOC tables at ingest time is a valid Phase 2 optimization — but it adds build complexity that isn't justified until latency is measurably problematic.

### Plugin stack (4 required, 1 recommended)

| Plugin | Role | Status |
|---|---|---|
| **Dataview** | Powers MOCs, dashboards, homepage queries | Required |
| **Homepage** | Opens to command center on launch | Required |
| **Omnisearch** | Fuzzy search fallback for phrase recall | Required |
| **Folder Note** | Makes navigation folders clickable as index notes | Recommended |
| **Templater** | Standardizes manual note creation shells | Optional Phase 2 |

**Rejected for Phase 1:** Breadcrumbs (unnecessary overhead), Kanban (different problem), Calendar (nice-to-have), Excalidraw (not navigation), Graph enhancements (premature).

### Tag taxonomy

Auto-generated at ingest by `corp-by-os` from CKE frontmatter fields:

```yaml
tags:
  - product/wms
  - product/planning
  - client/lenzing
  - domain/technology
  - topic/disaster-recovery
  - source/rfp
  - competitor/manhattan-associates
```

Validated against enumerated controlled vocabulary. Unknown values tagged `#needs-review`.

### File naming

Enforced on ingest:
```
YYYY-MM-DD_source-filename-normalized_shortid.md
```
Example: `2026-03-22_sgdbf_architectural_requirements_a7b2.md`

Short hash included by default for collision safety. Source traceability in frontmatter.

### MOC generation strategy

- **Auto-generate all MOCs** via `corp generate-mocs` on every ingest run
- **Allow curated intro blocks** on top 10–15 high-value pages only, preserved between `<!-- BEGIN CURATED -->` / `<!-- END CURATED -->` markers
- **MOC layout**: sectioned pages (overview, subtopics, architecture, training, RFPs, competitive, client references, recent) — not raw Dataview table dumps

### Homepage design

Minimal command center:

```
## This Week
- Client calls: Lenzing (Tue), SGDBF (Thu)
- New notes (7d): 14
- Stale alerts: 2

## Navigate
Products | Clients | Domains | Recent | Quality

## Quick Access
WMS | Planning | Platform | Lenzing | Michelin | SGDBF

## Search
Use Cmd+O or Omnisearch for keyword/phrase recall
```

No giant tables. No heavy queries. Answer three questions: What changed? What matters? Where do I click?

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Metadata quality inconsistency from CKE** | High | High — MOCs show wrong/incomplete results | Validate against controlled vocab at ingest; route unknowns to `#needs-review`; build quality dashboard showing untagged/low-confidence notes |
| **Dataview plugin breaks on Obsidian update** | Medium | High — navigation degrades to flat files + search | Disable auto-update for community plugins; test major updates in staging; keep MOC structure comprehensible as plain markdown even without rendering |
| **Tag taxonomy drift over time** | Medium | Medium — tag pane becomes noisy, queries miss notes | Lock taxonomy in code; version the vocabulary file; reject or remap unknown tags at ingest |
| **Homepage query latency at 4,000+ notes** | Medium | Medium — slow open experience frustrates daily use | Keep homepage queries bounded (7-day window, count-only, top-10 lists); move to pre-rendered summaries if latency exceeds 2 seconds |
| **MOC auto-generation overwrites curated content** | Low | High — Rob loses hand-written context | Use explicit `<!-- BEGIN/END CURATED -->` markers; `corp generate-mocs` must parse and preserve these blocks; add integration test |
| **Obsidian Sync exceeds 100MB** | Low | Medium — sync breaks or slows | Store large media externally (cloud links); compress images on ingest; monitor vault size with alerts at 70MB |
| **Rob ignores the system and just searches** | Medium | Low — system still works, just underutilized | Acceptable outcome. Omnisearch is a valid primary path. Optimize MOCs based on actual usage patterns in Phase 2 |
| **Future users (marketing, services) find structure confusing** | Low | Medium | The six-dimension navigation under Domains provides entry points for all functions; tag prefixes allow role-specific filtering |

---

## Action Items

### Phase 1: Ship the foundation (Week 1–2)

1. **Implement folder structure** as specified above. Create `00_Home/`, `01_Knowledge/`, `02_Navigate/` with subdirectories for Products, Clients, Domains, Topics, Recent, Quality.

2. **Update `corp-by-os` ingest pipeline:**
   - Write all source notes to `01_Knowledge/` flat
   - Rename files to `YYYY-MM-DD_source-normalized_shortid.md`
   - Generate `tags:` array in frontmatter from CKE `products`, `clients`, `domains`, `topics` fields using prefixed taxonomy
   - Validate all tag values against enumerated vocabulary file; unknown values → `#needs-review`

3. **Implement `corp generate-mocs`:**
   - Generate MOC notes in `02_Navigate/` tree for each known product, client, domain, and topic
   - Each MOC contains sectioned Dataview queries (overview, architecture, training, RFPs, competitive, recent)
   - Preserve content between `<!-- BEGIN CURATED -->` / `<!-- END CURATED -->` markers
   - Run automatically after each ingest batch

4. **Create `Home.md`** with bounded Dataview queries for recent notes (7d), stale alerts, and static navigation links to top-level MOCs.

5. **Install plugins:** Dataview, Homepage, Omnisearch, Folder Note. Pin plugin versions. Disable auto-update.

6. **Create controlled vocabulary file** (`99_System/taxonomy.yml` or equivalent) listing all valid products, clients, domains, topics, competitors, source types. Referenced by both CKE validation and `corp-by-os`.

### Phase 2: UX polish (Week 3–4)

7. **Write curated intros** for top 5 product MOCs (WMS, Planning, Platform, TMS, BY Commerce) and top 5 client MOCs.

8. **Add Recent dashboard** (`02_Navigate/Recent/Recent.md`) with date-bucketed Dataview queries.

9. **Add Quality dashboard** (`02_Navigate/Quality/Quality.md`) showing low-confidence notes, untagged notes, stale notes (>6 months without update).

10. **Configure Graph View defaults:** local graph depth 2, color by top-level tag prefix (`product/`, `client/`, `domain/`). Save as workspace preset.

11. **Measure and optimize:** track homepage load time, MOC query latency, and Rob's actual navigation patterns. If homepage exceeds 2s render, move to pre-rendered summary counts.

### Phase 3: Strategic expansion (Month 2+)

12. **Competitive battlecard landing pages** — curated MOCs for top 3–5 competitors with auto-generated supporting note lists.

13. **Coverage gap reporting** — which products/clients have fewer than N notes? Surface in Quality dashboard.

14. **Evaluate Templater** for manual note creation standardization, if Rob creates notes directly in Obsidian.

15. **Reassess folder strategy** based on 30 days of real usage data. If Rob never browses `02_Navigate/` in the sidebar and exclusively uses search, simplify. If he wants to browse source notes by dimension, consider shallow dimension folders for `01_Knowledge/` as a Phase 3 experiment.
