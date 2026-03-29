# AI Council Debate: ## Question: Should we adopt a Palantir-style ontology layer for our corporate k

**Date:** 2026-03-28 15:14:28
**Panel:** claude-opus-4-6, deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta
**Synthesizer:** openai (non-participant)
**Rounds:** 2
**Duration:** 272.6s
**Panel Mode:** full (4-model panel)
**Debate Mode:** pick
**Source:** council_inbox\council_ontology_approach.md
**Cost:** ~$0.4935 (84,268 tokens)

---

## Round 1: Initial Responses

### Claude (claude-opus-4-6)



## Position

Build a **minimum viable ontology** using SQLite junction tables (Option B: entities + relationships), run as a post-processing step over existing notes, and generate Obsidian wikilinks from the entity graph. Do not adopt a Palantir-style ontology layer, graph database, or embeddings.

## Alternatives Considered

**Full knowledge graph with Neo4j (Option C).** Rejected because it introduces a heavy operational dependency for 488 notes, requires learning Cypher, and creates a system that a solo developer will stop maintaining within 3 months. The 2am question: if Neo4j crashes, your entire knowledge retrieval path is down and you're debugging JVM heap settings. The cognitive load alone makes this a non-starter for a solo ADHD workflow.

**Vector embeddings only, skip explicit ontology (Option D/Question 7B).** Rejected because your actual pain points are *entity resolution* and *relationship tracking* — "which client discussed which product" — not "find me semantically similar documents." Embeddings solve a different problem. A vector search for "Blue Yonder WMS" would surface relevant docs, but wouldn't tell you that JLR discussed it in 5 meetings with an evolving requirements arc. Embeddings are a complement to structured entities, not a substitute. Defer to later.

## Decision Criteria

1. **Time to tangible value**: Must produce visible improvement in `corp retrieve` and `corp prep` within 1 week of effort.
2. **Operational simplicity**: SQLite only, no new runtime dependencies, no new services to keep alive.
3. **Pipeline safety**: Must not modify existing extraction or break current 488-note corpus.
4. **Cognitive sustainability**: A solo developer with ADHD will abandon anything that requires ongoing manual curation. The system must be self-maintaining via automation.
5. **Scale appropriateness**: 488 notes growing ~50/month means ~1,100 notes in 12 months. The solution must be right-sized for 500–2,000 notes, not 2 million.

## Assumptions

1. **The alias YAML files are reasonably complete.** If product_aliases.yaml (20 entries) and client_aliases.yaml (48 entries) cover <50% of actual entities in the corpus, the entity resolution step will produce a sparse, misleading graph. This assumption can be validated in day 1 by running extraction over a sample.
2. **Frontmatter fields already contain extractable entity references.** The existing `products`, `clients`, `topics` YAML fields can be parsed to populate entity/relationship tables without re-running CKE. If frontmatter is too inconsistent or sparse, you'd need a re-extraction pass, adding 2–3 days.
3. **The primary retrieval interface remains CLI (`corp retrieve`).** If the primary interface shifts to Obsidian graph view or a web UI, the rendering layer changes significantly.
4. **Relationship cardinality is modest.** With ~500 notes, ~20 products, ~48 clients, and maybe ~100 people, the entity table is small (hundreds of rows) and the relationship table is manageable (low thousands). SQLite junction tables handle this trivially.

## Recommendation

### What to do now (Week 1)

**Step 1: Entity tables in index.db (Day 1–2)**

Add three tables to your existing SQLite `index.db`:

```sql
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    canonical_name TEXT NOT NULL UNIQUE,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('client','product','person','topic','decision')),
    aliases TEXT, -- JSON array
    first_seen DATE,
    last_seen DATE,
    note_count INTEGER DEFAULT 0
);

CREATE TABLE note_entities (
    note_path TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    role TEXT, -- 'mentioned', 'primary_subject', 'decided_by'
    confidence REAL DEFAULT 1.0,
    FOREIGN KEY (entity_id) REFERENCES entities(id),
    PRIMARY KEY (note_path, entity_id)
);

CREATE TABLE entity_relationships (
    id INTEGER PRIMARY KEY,
    source_entity_id INTEGER NOT NULL,
    target_entity_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL, -- 'discussed', 'decided', 'requires', 'competes_with'
    context_note TEXT, -- note_path where this relationship was observed
    observed_date DATE,
    FOREIGN KEY (source_entity_id) REFERENCES entities(id),
    FOREIGN KEY (target_entity_id) REFERENCES entities(id)
);

CREATE INDEX idx_ne_entity ON note_entities(entity_id);
CREATE INDEX idx_er_source ON entity_relationships(source_entity_id);
CREATE INDEX idx_er_target ON entity_relationships(target_entity_id);
```

**Step 2: Hydration script (Day 2–3)**

Write `corp ontology build` that:
1. Reads `product_aliases.yaml` and `client_aliases.yaml` → populates `entities` table with canonical names and aliases.
2. Scans all 488 notes' YAML frontmatter → resolves each `products`, `clients`, `people` field against the alias tables → writes to `note_entities`.
3. For every note that mentions both a client AND a product, writes a `(client, 'discussed', product)` row to `entity_relationships` with the note as context.
4. Computes `first_seen`, `last_seen`, `note_count` per entity.

This is a batch job. Run it idempotently (DELETE + re-INSERT or UPSERT). Target: runs in <10 seconds over 488 notes.

**Step 3: Entity-aware retrieval (Day 3–4)**

Extend `corp retrieve` so that:
- `corp retrieve --entity "JLR"` returns all notes linked to the JLR entity, ordered by date.
- `corp retrieve --entity "JLR" --related products` returns all products discussed with JLR, with note counts and date ranges.
- `corp retrieve --timeline "JLR"` returns JLR notes in chronological order with a one-line summary each — this directly solves "how did JLR requirements evolve across 5 meetings?"

Under the hood, this is just SQL joins. No graph database needed.

**Step 4: Wikilink injection (Day 4–5)**

Write `corp ontology link` that:
1. For each note, looks up its entities in `note_entities`.
2. For each entity, finds other notes sharing that entity (co-occurrence).
3. Appends a `## Related` section at the bottom of each markdown note with Obsidian wikilinks: `- [[note-about-jlr-workshop-2024-03]] (JLR, Blue Yonder WMS)`.
4. This makes Obsidian's native graph view immediately useful — 488 isolated nodes become a connected graph.

Use a clear delimiter (`<!-- ontology:related:start -->` / `<!-- ontology:related:end -->`) so the section is idempotently regenerable and clearly machine-authored.

**Step 5: Auto-generated MOCs (Day 5)**

Write `corp ontology moc` that generates Map of Content notes:
- One MOC per client with >3 notes: `_MOC_JLR.md` listing all JLR notes chronologically, products discussed, decisions made.
- One MOC per product with >5 mentions: `_MOC_Blue_Yonder_WMS.md` listing all notes mentioning it, grouped by client.

These are generated artifacts. Prefix with `_MOC_` so they sort to the top and are visually distinct.

### What NOT to do now

- **Do not change the folder structure.** Folders stay as-is. The ontology lives in the database, surfaced via wikilinks and MOCs. Restructuring 488 files into ontology-driven folders is high risk, breaks existing links, and the ontology database already provides the navigational structure you want.
- **Do not switch CKE to write to the entity table during extraction (Option 5B).** Keep CKE writing frontmatter as today. The ontology layer reads from frontmatter. This preserves the principle that notes are self-contained documents, not database views. If the ontology DB corrupts, you lose nothing — rebuild from notes.
- **Do not add embeddings or vector search.** This is a separate capability with separate infrastructure (embedding model, vector storage, query pipeline). It compounds scope and doesn't address the stated pain points (entity resolution, relationships, temporal ordering).
- **Do not install Neo4j, DuckDB, or any new database engine.**

### What to defer

- **Embeddings (semantic search)**: Revisit after ontology has been in use for 2 months and you've identified specific retrieval failures that keyword + entity search can't solve.
- **Pipeline-integrated entity extraction**: Once the ontology proves valuable, add a hook so CKE writes to `note_entities` as a side-effect during extraction. For now, batch rebuild is fine at this scale.
- **Person entity resolution**: People names are harder than products/clients (name variants, roles change). Start with client + product entities only. Add people when you have a `person_aliases.yaml` with enough coverage.
- **Relationship type refinement**: Start with just `discussed`. Add `decided`, `requires`, `competes_with` when you have concrete retrieval queries that need them.

## Rationale

- **Your pain is relational, not dimensional.** "Which client discussed which product in which meeting" is a join across three structured fields you already extract. This is a SQL problem, not a graph problem, not an embeddings problem. Three SQLite tables solve it with zero new dependencies.

- **488 notes × 20 products × 48 clients ≈ trivial cardinality.** The entity table will have ~150 rows. The relationship table will have ~2,000 rows. SQLite handles this in microseconds. You won't need a graph database until you're well past 50,000 relationships, which at 50 notes/month is years away.

- **Post-processing preserves pipeline safety.** The ontology layer reads from existing notes and writes to a separate DB. If it breaks, your notes are untouched. If you abandon it, nothing else changes. This is the key architectural property: the ontology is a *derived view*, not a *source of truth*.

- **Wikilinks + MOCs give immediate Obsidian value.** The single highest-impact change is turning 488 disconnected nodes in Obsidian's graph view into a connected graph. Auto-generated `## Related` sections and MOCs achieve this with zero manual curation, directly addressing the "document graveyard" problem.

- **Batch rebuild idempotency means low maintenance burden.** `corp ontology build` can be run anytime (after new notes arrive, after alias files are updated). No incremental state to manage, no migration scripts, no consistency issues. This is critical for ADHD sustainability — if you forget to run it for a month, just run it once and you're current.

## Trade-offs

- **No semantic search.** You won't find "supply chain optimization" when searching for "logistics improvement." Estimated impact: ~10% of retrieval queries would benefit from semantic matching. Acceptable given keyword + entity search covers the explicit use case of "what did JLR say about Blue Yonder."

- **No automatic entity discovery.** New products/clients not in alias files won't be resolved. You'll need to periodically update `product_aliases.yaml` and `client_aliases.yaml`. Estimated maintenance: ~15 minutes per month to review unresolved entity mentions from a validation report (`corp ontology validate` — add this as a Day 5 bonus).

- **Relationships are inferred from co-occurrence, not extracted from text.** "JLR discussed Blue Yonder WMS" is inferred because both appear in the same note, not because the text says "JLR evaluated Blue Yonder WMS." This means some false positives (a note mentions JLR and BY WMS in unrelated sections). At 488 notes, the signal-to-noise ratio is high enough that this is acceptable.

- **No real-time indexing.** New notes aren't in the ontology until you run `corp ontology build`. At 50 notes/month, running it weekly (or hooking it to the end of your existing pipeline) is sufficient.

## Risks

1. **Alias file coverage is too low** (Likelihood: medium, Impact: high). If `product_aliases.yaml` covers only 40% of product mentions, the entity graph will be sparse and unreliable. *Mitigation*: Day 1 validation — run entity extraction over all 488 notes, report unresolved mentions, bulk-add aliases before building the graph. Budget an extra half-day for this.

2. **Wikilink injection corrupts notes** (Likelihood: low, Impact: high). Appending markdown to 488 notes is a bulk file mutation. *Mitigation*: Git commit before link injection. Use clear delimiters for idempotent regeneration. Run on a copy first. Add a `--dry-run` flag that reports changes without writing.

3. **You build it, use it for a week, then abandon it** (Likelihood: medium, Impact: medium). ADHD risk — the initial build is fun, the ongoing alias maintenance is not. *Mitigation*: The MOCs and wikilinks persist in the vault even if you never run the tool again. The value is partially locked in at generation time. Add `corp ontology build` to the existing pipeline's post-processing so it runs automatically.

4. **Scope creep into graph database or embeddings** (Likelihood: medium, Impact: medium). The temptation to "do it properly" with Neo4j or vector search will be strong. *Mitigation*: This document is your architectural decision record. SQLite junction tables until you have >5,000 notes or a concrete retrieval failure that proves they're insufficient.

## Signals to Revisit

- **Retrieval failure rate**: If >20% of `corp retrieve` queries fail to find relevant notes despite entity search, evaluate embeddings.
- **Note count >2,000**: At this scale, batch rebuild may exceed 30 seconds and relationship queries may benefit from graph indexing. Re-evaluate SQLite vs. a lightweight graph layer.
- **Alias maintenance becomes a bottleneck**: If you're spending >30 min/month updating alias files, invest in LLM-assisted entity resolution (use CKE to suggest canonical names for unknown entities).
- **Multi-user access**: If anyone else needs to query this system, the CLI-only interface won't suffice. At that point, consider a lightweight API layer.
- **You find yourself manually tracing relationships** that the co-occurrence model misses — e.g., "JLR's decision on WMS was influenced by the Tesco pilot" spanning notes with no shared entities. This is where a graph DB or embeddings would actually earn their keep.

*Latency: 89.28s | Tokens: 5528*

### Gemini (gemini-3.1-pro-preview)

## Position
Implement a Minimal Viable Ontology (MVO) strictly within your existing SQLite infrastructure using junction tables, and decouple this entirely from your physical file system to eliminate the blast radius of automated extraction errors. 

## Alternatives Considered
- **Neo4j / Dedicated Graph DB:** Rejected. Introducing a standalone Java-based graph database requires managing new network ports, access controls, and JVM memory, drastically expanding your attack surface and supply chain footprint for a scale that absolutely does not warrant it.
- **Local Vector Embeddings (Semantic Search):** Rejected for now. Pulling in PyTorch, HuggingFace sentence-transformers, and underlying C++ dependencies massively inflates your supply chain risk and introduces "black box" non-deterministic matching, which is harder to debug than structured SQL at this early stage.

## Decision Criteria
1. **Blast Radius / Data Integrity:** A failure, hallucination, or bug in the ontology generation must never corrupt the raw Vault documents or alter the file system.
2. **Supply Chain Footprint:** Minimizing new external dependencies, specifically avoiding large ML libraries or standalone database engines.
3. **Implementation Realism:** A solo developer must be able to deploy, audit, and see value from the system within 7 days.
4. **Scale Appropriateness:** Solutions must be optimized for ~500-5000 documents, not Palantir's multi-million document enterprise scale.

## Assumptions
1. Your CKE pipeline reliably outputs semi-structured data to YAML frontmatter, meaning the Markdown files can act as a fully self-contained source of truth.
2. You have a mechanism (e.g., cron or file watcher) to trigger lightweight scripts when documents are added or changed.
3. SQLite queries, including recursive Common Table Expressions (CTEs) for traversing relationships, will execute in single-digit milliseconds at a scale of <10,000 notes.

## Recommendation

**What to do now:**
- **Add to `index.db`:** Create structured `entities` (id, type, canonical_name) and `relationships` (source_id, target_id, relation_type, document_id) tables in your existing SQLite database.
- **Post-Process Only:** Keep the extraction pipeline exactly as-is. Build an independent, asynchronous post-processing script that reads YAML frontmatter, resolves entities via your `aliases.yaml`, and strictly overwrites the SQLite entity/relationship tables. 
- **Generate MOCs:** Run a secondary script that queries `index.db` to automatically generate Obsidian Maps of Content (MOCs) as read-only Markdown files (e.g., `_Auto/Client_JLR.md` containing dynamic `[[wikilinks]]` to the relevant meetings and products).

**What not to do now:**
- **Do NOT restructure your folders:** Keep the flat/simple folder structure. Restructuring physical files based on an automated ontology introduces a catastrophic blast radius—a rogue script could scramble your entire knowledge base and break all external/relative links.
- **Do NOT inject relationships into existing notes:** Obsidian should remain a "dumb" viewer of the raw notes and the auto-generated MOCs. Do not automatically append data to your original Markdown files.

**What to defer until later:**
- **Vector Embeddings / Semantic Search:** Defer until explicit, keyword-alias-based entity resolution fails to capture obvious connections, or until your manual `aliases.yaml` file exceeds ~500 entries.

## Rationale
- **Strict Blast Radius Containment:** By treating the ontology as a read-only projection (an index) generated *after* the vault pipeline completes, an extraction bug simply results in a bad SQLite table. You can drop the tables and rebuild them with zero risk to your primary data.
- **Zero-Dependency Graph Architecture:** SQLite junction tables are perfectly adequate for graph traversal at this scale. A SQL query joining `Clients → Meetings → Products` will execute in <5ms, providing the exact same data structures as a Palantir ontology without the enterprise security overhead or new attack surfaces.
- **Auditable Trust Boundaries:** Palantir's core value isn't a proprietary database engine; it is strict normalization. By enforcing your `product_aliases.yaml` list before writing to the SQLite `entities` table, you create a hardened trust boundary that prevents "dirty data" (e.g., "BY WMS" vs "Blue Yonder") from polluting downstream queries.
- **Rapid Time-to-Value:** Writing a Python script to parse existing YAML and insert it into SQLite takes hours, not days. Generating purely automated MOC files inside a dedicated Obsidian folder instantly satisfies the "relationship tracking" and "temporal ordering" requirements using Dataview or basic Markdown lists.

## Trade-offs
- **Graph Visualization:** You give up native visual graph querying (like Neo4j Bloom). You will have to rely on Obsidian's built-in local graph view (driven by your generated MOCs) or write custom SQL queries.
- **Fuzzy Discovery:** Without embeddings, you rely on explicit aliases. If "Project Phoenix" and "Migration Initiative" are the same thing but lack a shared alias, the system will not connect them.

## Risks
- **Entity Proliferation (Database Poisoning):** CKE extracts too many unique, garbage entities, bloating the SQLite tables and making MOCs useless.
  * *Mitigation (Likelihood: High, Impact: Medium):* Implement a strict schema validation step. Only allow entities that map to known types (Client, Product, Person). Run a weekly query for orphaned entities (entities with <2 relationships) to prune garbage or identify missing aliases.
- **State Desynchronization:** The `index.db` gets out of sync with the Vault if file deletions or renames are missed.
  * *Mitigation (Likelihood: Medium, Impact: Low):* Treat the ontology tables as ephemeral. Nuke and rebuild the `entities` and `relationships` tables from the Markdown source of truth on a nightly basis. At 488 files, this rebuild will take roughly 1-2 seconds.

## Signals to Revisit
- If maintaining the `aliases.yaml` file takes more than 1 hour per week, it is time to assume the supply chain risk of an external ML dependency and implement vector embeddings for automated semantic clustering.
- If recursive SQLite CTEs for entity traversal begin exceeding 500ms (highly unlikely before 100,000 entities), revisit adopting a dedicated graph database.

*Latency: 35.88s | Tokens: 5033*

### Deepseek (deepseek-reasoner)

## Position
Build a lightweight entity registry and relationship tracking layer in SQLite, implemented as a post-processing step on existing extraction output, without modifying the core pipeline. Defer semantic embeddings and graph databases until explicit relationship queries demonstrate value.

## Alternatives Considered
1. **Full Palantir-style ontology with graph database**: Rejected because it introduces disproportionate complexity (Neo4j dependency, graph query learning curve) for <500 notes where the primary pain point is discoverability, not relationship analytics.
2. **Semantic embeddings only (skip explicit ontology)**: Rejected because it addresses different problems (meaning search) while leaving the core issue of unresolved entities and missed connections between notes unsolved.

## Decision Criteria
1. **Immediate value within 1 week** - Must unblock existing workflow bottlenecks with minimal implementation time.
2. **Zero-risk to existing pipeline** - Cannot break classification, extraction, or retrieval that already works at 93.7% accuracy.
3. **SQLite-first ecosystem** - Prefer leveraging existing operational databases over new dependencies.
4. **Solo-developer sustainable** - Solution must be maintainable with ADHD constraints (clear boundaries, incremental progress).
5. **Obsidian-compatible output** - Must enhance, not break, the current note-taking workflow.

## Assumptions
1. The primary pain point is discoverability of related notes, not complex relationship analytics (e.g., "show me all meetings where Client X discussed Product Y" is valuable; "calculate centrality metrics for product adoption" is not).
2. Entity resolution can be sufficiently solved by extending existing alias files with manual curation, not requiring machine learning deduplication.
3. Note growth rate (~50/month) will not necessitate distributed graph computation for at least 18 months.

## Recommendation
**What to do now:**
1. Add `entity_registry` and `note_entity_relationships` tables to `ops.db` with schema:
   - `entities`: id, canonical_name, type, aliases (JSON), first_seen, last_seen, note_count
   - `relationships`: note_id, entity_id, entity_type, relationship_type (primary, mentioned), confidence
2. Create a post-processing script that:
   - Processes all existing 488 notes' frontmatter to populate entities table using existing alias files
   - Generates backlinks section in each note: `## Linked Entities` with wikilinks to entity MOC notes
   - Creates entity MOC notes (e.g., `Product/Blue-Yonder-WMS.md`) listing all related notes
3. Extend `corp retrieve` to support entity-based search: `--entity product:"Blue Yonder"`

**What not to do now:**
- Do not modify the CKE extraction pipeline to write directly to entity tables
- Do not introduce graph database dependencies
- Do not change folder structure (keep MyWork as is)
- Do not implement vector embeddings

**What to defer until later:**
- Graph database migration (only if relationship queries become complex)
- Automated temporal graph building
- Semantic embeddings (requires GPU/optimized CPU inference)
- Dynamic folder structures based on ontology

## Rationale
- **SQLite handles current scale efficiently**: At 500 notes with ~10 entities/note, we'll have ~5k entity-note relationships. SQLite with proper indexes supports millisecond queries for all likely access patterns (filter by entity, count relationships).
- **Post-processing is safe and reversible**: Building on existing frontmatter means if the ontology layer fails, the pipeline still produces usable notes. This satisfies the "don't break existing pipeline" constraint.
- **Entity MOCs solve the immediate discoverability problem**: Creating `Product/Blue-Yonder-WMS.md` that lists all 15 notes mentioning it addresses the "isolated notes" complaint directly in Obsidian within hours of implementation.
- **Manual alias curation scales to ~2k entities**: With current 68 aliases (20 product + 48 client), adding 5-10 new entities/month is sustainable for a solo developer. Automated entity resolution becomes necessary only at >2000 unique entities.

## Trade-offs
- **Relationship richness limited to "note mentions entity"**: We lose the ability to capture entity-entity relationships (e.g., "Client X purchased Product Y") without extending the extraction pipeline. Estimated capture rate: 70% of valuable relationships vs. 95% with deeper extraction.
- **Query performance degrades at ~50k relationships**: SQLite with proper indexes handles this scale, but complex graph traversals (3+ hops) become inefficient above this point. At current growth, we have 18 months before hitting this limit.
- **Manual entity curation overhead**: ~30 minutes/week to review new entities and aliases vs. fully automated approach.

## Risks
1. **Entity explosion from poor resolution** (Medium likelihood/Medium impact): Without automated resolution, we might create duplicate entities for similar names. Mitigation: Weekly `entity-dedupe` CLI command with fuzzy matching suggestions.
2. **Obsidian performance degradation** (Low likelihood/High impact): Adding 5k wikilinks across 500 notes could slow Obsidian graph rendering. Mitigation: Generate entity MOCs but don't add reciprocal links to all notes initially; use Dataview queries instead.
3. **Abandoned ontology due to curation fatigue** (High likelihood/Medium impact): Solo developer might stop maintaining entity registry. Mitigation: Build curation into existing workflow (e.g., `corp prep` prompts for new entity aliases).

## Signals to Revisit
- When entity-based search accounts for >40% of `corp retrieve` queries (currently 0%)
- When note count exceeds 2,000 with consistent relationship complexity
- When users regularly ask "how is X related to Y across more than 2 notes?"
- When manual entity curation exceeds 1 hour/week consistently

*Latency: 83.64s | Tokens: 4339*

### Grok (grok-4.20-beta)

**## Position**
Do not adopt a Palantir-style ontology layer. Implement only a minimal, read-only entity table in the existing SQLite ops.db as a post-processing step on the current pipeline; everything else is overengineering for a solo practitioner with 488 notes.

**## Alternatives Considered**
- Full entity + relationship graph (option B/C): Rejected because it requires maintaining a second source of truth that will drift within weeks given ADHD context-switching and the "must show value in 1 week" constraint.
- Vector embeddings only (option D): Rejected because it solves a different problem (fuzzy semantic search) while leaving the core entity-resolution pain ("is Blue Yonder WMS the same as BY WMS?") untouched; we already have 93.7% classification and aliases.

**## Decision Criteria**
- Must deliver measurable value to corp retrieve or corp prep within 7 days
- Zero new persistent dependencies (SQLite only)
- Must not require changes to the existing File → CKE → Vault pipeline
- Maintenance burden must be <2 hours per month for a solo ADHD developer
- Must improve retrieval precision on the current 488-note corpus by at least 30% on the 20 most frequent clients/products

**## Assumptions**
- The primary retrieval failure mode is entity aliasing and "which notes mention X", not missing implicit relationships or complex graph traversal.
- The user will continue to interact with the knowledge base primarily through the existing CLI tools and Obsidian Dataview, not through a new ontology query language.
- Note growth remains ~50/month for the next 12 months (i.e. <1,200 total notes).
- Frontmatter extraction quality remains high enough that post-processing can reliably normalize entities.

**## Recommendation**
- **What to do now**: Add two tables to ops.db (`entities` and `mentions`). Write a one-time `build_entity_index.py` script that reads every markdown file's frontmatter + product_aliases.yaml/client_aliases.yaml, canonicalizes names, populates the tables, and adds a `[[entity:canonical-name]]` wikilink at the bottom of each note. Hook it into the existing "Route" step as an optional post-processor that runs in <4 seconds for the current corpus. Update `corp retrieve` to offer `--by-entity Client:Jaguar` as a first-class filter.
- **What not to do now**: Do not create any relationship tables, do not change folder structure, do not add embeddings, do not touch Obsidian graph view or MOCs, do not make notes "views" of the database.
- **What to defer until later**: Any explicit relationship modeling, temporal sequencing, Neo4j, NetworkX, JSON relationship columns, or schema inference.

**## Rationale**
- Entity resolution is already 80% solved (aliases + CKE); surfacing it takes ~3 days and directly fixes the "Blue Yonder WMS vs BY Warehouse Management" problem cited.
- 488 notes × average 4.2 entity mentions = ~2,050 rows; SQLite junction table queries remain <10ms on a laptop.
- Adding `[[entity:...]]` wikilinks gives immediate Obsidian value (backlinks, Dataview tables) with zero new UI.
- Delivering a working `--by-entity` filter in corp retrieve within a week satisfies the "show value immediately" constraint; full ontology would take 4-6 weeks.
- At current growth rate, the entity table remains useful until ~2,500 notes; Palantir's ontology only becomes dominant at 50k+ documents.

**## Trade-offs**
- Give up rich "Client → discussed → Product → produced → Decision" queries (estimated 60% of Palantir value) in exchange for 10× lower maintenance burden and 4-week faster time-to-value.
- Lose automatic temporal ordering of JLR requirements; will still require manual Dataview date sorting (acceptable at <500 notes).

**## Risks**
- **Entity drift** (canonical name changes but old notes aren't updated): likelihood medium (40%), impact medium. Mitigate with a `rebuild-entity-index` command that always runs from source frontmatter.
- **User ignores the new filter and keeps using keyword search**: likelihood high (60%), impact low. Mitigate by making `--by-entity` the default output format for `corp retrieve Client:Jaguar`.
- **ADHD paralysis from scope creep**: likelihood high if we chose full ontology. Current minimal approach reduces this to near-zero.

**## Signals to Revisit**
- Note count exceeds 1,500 with >30% of queries requiring multi-hop questions ("show every decision for every product at JLR").
- `corp retrieve` precision on entity-based queries stays below 75% after 4 weeks of use.
- User begins consistently asking for relationship-style questions that the entity table cannot answer.
- Budget appears for a junior analyst or GPU workstation, changing the "solo ADHD" constraint.

*Latency: 13.06s | Tokens: 3868*

## Round 2: Critique

### Claude (claude-opus-4-6)

# Council Round 2 Assessment

## Proposal A: Lightweight Entity Registry + Relationship Tracking (Post-Processing)

**Steelman:** This proposal is exactly right if: (1) the primary retrieval failures are caused by entity aliasing gaps, not missing relationships; (2) the developer will actually curate entity MOCs and find them useful in Obsidian; (3) the 30-minute/week manual curation estimate is accurate and sustainable; and (4) the distinction between "entity registry" and "relationship tracking" creates a natural expansion path that the developer will actually follow rather than abandon. In a world where the developer has moderate discipline and the retrieval problem is predominantly "find all notes about X," this is well-calibrated.

**Assessment: Partially Agree.** The entity registry is sound. The relationship table (`note_entity_relationships`) is prudent to include in schema but premature to populate with typed relationships. The proposal correctly identifies post-processing as the safe path. But it hedges — it includes relationship infrastructure while recommending against populating it deeply, which means you're shipping dead schema. More importantly, it underestimates the risk of entity MOC generation becoming stale and misleading.

**Strongest point:** "Post-processing is safe and reversible" — this is the single most important architectural property. The ontology is a derived view, not a source of truth. If it breaks, notes are untouched. This is what the 2am engineer needs to hear.

**Weakest assumption:** "Entity resolution can be sufficiently solved by extending existing alias files with manual curation." At 488 notes, there are likely hundreds of entity mentions that don't match any of the 68 existing aliases. The proposal budgets 30 minutes/week for this, but the initial backfill — identifying and aliasing hundreds of unresolved mentions across 488 notes — will take multiple hours and is exactly the kind of tedious task that an ADHD developer will start and not finish. If this assumption fails, the entity registry is sparse and the MOCs are incomplete, undermining trust in the entire system.

**Hidden assumptions:**
1. **Entity MOCs are the right Obsidian surface.** The proposal assumes that a developer who has 488 flat notes will actually navigate via auto-generated MOC files. But MOCs only work if you open them. If the developer's primary workflow is `corp retrieve` from the CLI, the MOCs are write-only artifacts nobody reads.
2. **The existing frontmatter entity fields are consistently populated and correctly extracted.** If CKE's entity extraction is spotty (some notes have `products: []`, some have free-text product names not in the alias file), the hydration script will produce a graph that's missing large chunks of reality.

**Overlooked risks:**
- **Silent incompleteness.** The entity registry will look functional but miss 30-40% of real connections because alias coverage is low. The developer won't know what's missing — the system will appear to work but give a false sense of completeness. This is worse than having no ontology at all because it creates unjustified confidence.

---

## Proposal B: Minimum Viable Ontology (Entities + Relationships + Wikilinks + MOCs)

**Steelman:** This proposal is exactly right if: (1) the developer will execute all five steps in sequence within one week without getting derailed; (2) co-occurrence-based relationship inference (client + product in same note = "discussed") has an acceptable false-positive rate; (3) wikilink injection into 488 existing files can be done safely and idempotently; (4) the auto-generated MOCs actually get used; and (5) the developer hooks `corp ontology build` into the pipeline and runs it consistently. In a world where execution is reliable and the developer's retrieval needs are genuinely relational ("what did JLR say about Blue Yonder across meetings"), this is the highest-value option.

**Assessment: Partially Agree.** This is the most thorough and operationally detailed proposal. The five-day plan is realistic in scope. The SQL schema is correct. The wikilink injection with delimiter-based idempotency is well-designed. But it's overscoped for Week 1 — five distinct deliverables (entity tables, hydration script, entity-aware retrieval, wikilink injection, MOC generation) in five days is a plan that looks achievable on paper but will collide with real-world friction. For an ADHD developer, shipping three of five steps and abandoning the last two is the modal outcome. The proposal should have identified which three steps deliver 80% of the value and made the other two explicitly optional.

**Strongest point:** "Your pain is relational, not dimensional." This is the sharpest diagnostic in any proposal. The problem is structured — entity resolution and co-occurrence joins — not fuzzy. Framing this as a SQL problem, not a graph problem, not an embeddings problem, is exactly right and should guide all subsequent decisions.

**Weakest assumption:** "Co-occurrence-based relationships are acceptable." The proposal infers "JLR discussed Blue Yonder WMS" because both appear in the same note's frontmatter. But a meeting note might mention 4 clients and 6 products — that's 24 inferred "discussed" relationships per note, most of which are noise. If the average note has 3 clients and 4 products, you get ~12 false relationships per note × 488 notes = ~5,800 relationships of which perhaps 60% are spurious. The relationship table becomes untrustworthy. The proposal acknowledges this ("some false positives") but underestimates the scale at which it undermines the whole system's credibility.

**Hidden assumptions:**
1. **Wikilink injection is non-destructive in practice.** The proposal adds `## Related` sections to 488 existing markdown files. Even with delimiters, this changes file modification timestamps, triggers Obsidian re-indexing, creates large git diffs, and may interact poorly with any other tools that watch these files. The proposal treats this as low-risk, but bulk-modifying 488 source files is a fundamentally different operation than writing to a database.
2. **The developer's retrieval patterns are entity-centric.** The `--entity "JLR" --related products` interface assumes the developer thinks in entities. But the current workflow is keyword search — the developer types what they remember ("that meeting about warehouse stuff in March"), not structured entity queries. The new interface may not match how the developer actually thinks.

**Overlooked risks:**
- **Git history pollution.** If `corp ontology link` is run frequently, each run creates a diff across hundreds of files (even if content is identical, regenerating the Related section changes file content). This makes `git log` and `git diff` useless for tracking actual human edits vs. machine regeneration. For a knowledge base where you might want to understand what *you* wrote vs. what the system generated, this is a real problem. Mitigation would be to keep machine-generated content in separate files (MOCs only), not injected into source notes.

---

## Proposal C: Minimal Entity Table Only (No Relationships)

**Steelman:** This proposal is exactly right if: (1) 80%+ of retrieval failures are caused by entity aliasing (searching for "BY WMS" when the note says "Blue Yonder Warehouse Management"); (2) the developer genuinely won't maintain anything more complex than two SQLite tables; (3) Dataview date-sorting in Obsidian is sufficient for temporal ordering; and (4) the value of relationship tracking is genuinely low at 488 notes because the developer already has enough context in their head to connect entities manually. In a world where the developer's real problem is just "find all notes about X regardless of what X is called," this is the highest-ROI, lowest-risk option.

**Assessment: Partially Agree.** This is the most honest proposal about the developer's constraints. It refuses to scope-creep. It correctly identifies that entity resolution is the 80/20. But it's too minimal — by refusing to include even a `note_entities` junction table with co-occurrence, it leaves the "which clients discussed which products" question completely unanswered, which is explicitly stated as a core pain point. The proposal is right about what to build first but wrong about what to stop at.

**Strongest point:** "Give up rich 'Client → discussed → Product → produced → Decision' queries (estimated 60% of Palantir value) in exchange for 10× lower maintenance burden and 4-week faster time-to-value." This is the clearest trade-off statement in any proposal and it's honest about what's being sacrificed.

**Weakest assumption:** "The primary retrieval failure mode is entity aliasing and 'which notes mention X', not missing implicit relationships." The problem statement explicitly describes pain points that are relational: "which client discussed which product in which meeting," "how did JLR requirements evolve across 5 meetings." If these are real and frequent pain points — not aspirational ones — then entity aliasing alone doesn't solve them. A pure entity table with no relationship structure means the developer still has to manually cross-reference notes to answer relational questions.

**Hidden assumptions:**
1. **The developer has a reliable mental model of entity relationships.** By not tracking relationships, this proposal assumes the developer can hold the connection graph in their head ("I know JLR discussed Blue Yonder because I was there"). This is true today at 488 notes. At 1,200 notes (12 months from now), it won't be, and the proposal's signals to revisit (1,500 notes, 30% multi-hop queries) are too late — by the time you're asking multi-hop questions and failing, you've already lost months of relationship data that should have been captured.
2. **`[[entity:canonical-name]]` wikilinks are useful.** Injecting `[[entity:Blue-Yonder-WMS]]` at the bottom of a note is only useful if that entity page exists and has content. The proposal says to add wikilinks but explicitly says "do not touch Obsidian graph view or MOCs." So you get red (unresolved) wikilinks in Obsidian, which is worse than no wikilinks at all because it trains the developer to ignore them.

**Overlooked risks:**
- **The entity table solves a problem the developer doesn't actually have.** If the developer's real friction is "I can't find that meeting note from March" rather than "I can't find all notes about Blue Yonder," the entity table adds zero value. The proposal never validates which retrieval failures actually occur — it assumes entity aliasing is the bottleneck without evidence.

---

## Proposal D: Minimal Viable Ontology in SQLite with Strict Blast Radius

**Steelman:** This proposal is exactly right if: (1) data integrity is the highest-priority constraint (which it should be for a solo developer with no backup operator); (2) the "nuke and rebuild" approach to ontology tables is sustainable and fast enough at scale; (3) auto-generated MOCs in a dedicated `_Auto/` folder provide sufficient navigational value without wikilink injection; and (4) the strict separation between source files and derived views is the property that will matter most in three years when the developer has forgotten how the system works. In a world where the biggest risk is a rogue script corrupting the knowledge base and the developer not noticing for weeks, this proposal's safety model is superior.

**Assessment: Partially Agree.** This proposal has the best operational safety model of any proposal. The strict separation between source files and derived artifacts, the "nuke and rebuild" approach to ontology tables, and the explicit refusal to inject content into existing notes are all correct. The "blast radius" framing is exactly how a systems architect should think about this. But it's too cautious on the implementation side — it recommends entities and relationships in schema but doesn't provide a concrete implementation plan with the same specificity as Proposal B. It also shares Proposal B's co-occurrence problem without acknowledging it.

**Strongest point:** "Do NOT inject relationships into existing notes. Obsidian should remain a 'dumb' viewer of the raw notes and the auto-generated MOCs." This is the single most important architectural decision in all four proposals. Source notes are the source of truth. Everything else is derived. If you internalize one principle, it's this one.

**Weakest assumption:** "You have a mechanism (e.g., cron or file watcher) to trigger lightweight scripts when documents are added or changed." For a solo developer with ADHD, cron jobs and file watchers are maintenance liabilities, not features. They break silently, produce confusing errors when the environment changes, and add operational surface area. The assumption that this infrastructure exists and works reliably is the kind of thing that seems trivial in architecture and becomes an ongoing irritant in production. The proposal should instead recommend manual or pipeline-triggered invocation.

**Hidden assumptions:**
1. **The developer will actually look at auto-generated MOCs in `_Auto/`.** There's an implicit assumption that creating files in a dedicated folder will change the developer's workflow. But if the developer's habit is `corp retrieve` from the terminal, auto-generated Obsidian files in a subfolder are invisible. The proposal doesn't connect the MOCs to the CLI retrieval workflow.
2. **"Entity Proliferation" is the primary data quality risk.** The proposal focuses on too many garbage entities but doesn't address the opposite risk: too few entities because frontmatter extraction is sparse or alias coverage is low. Under-extraction is more likely than over-extraction to be the actual failure mode.

**Overlooked risks:**
- **The `_Auto/` folder becomes a graveyard.** If auto-generated MOCs aren't integrated into the developer's actual workflow (CLI retrieval, prep workflow), they'll accumulate silently and never be read. The proposal creates artifacts without creating a path to consumption. After 3 months, the `_Auto/` folder has 60+ MOC files that nobody opens, and the developer concludes the ontology "didn't work" — not because the data was wrong, but because the interface was wrong.

---

# Revised Recommendation

## What Changed My Mind

Proposal D's "blast radius" framing is superior to my original thinking. I was previously aligned most closely with Proposal B's scope, but Proposal D correctly identifies that **injecting wikilinks into source notes is an unnecessary risk**. The strongest argument across all proposals is Proposal D's principle: source notes are sacrosanct; everything derived lives in separate artifacts and databases.

Proposal B's diagnostic — "your pain is relational, not dimensional" — is the sharpest framing of the problem and remains correct.

Proposal C's honesty about ADHD sustainability is a necessary corrective to Proposal B's five-day plan, which is likely to produce three completed steps and two abandoned ones.

## Revised Position

**Build an entity-and-relationship layer in SQLite as a post-processing step. Never modify source notes. Surface the ontology through the CLI first, Obsidian MOCs second.**

### Specifically:

**Week 1, Days 1-3: Entity infrastructure (hard requirement)**

Add to `index.db`:
- `entities` table (id, canonical_name, entity_type, aliases as JSON)
- `note_entities` table (note_path, entity_id, role, confidence)
- Hydration script that reads frontmatter + alias YAML files, populates both tables
- **Day 1 prerequisite**: Run a coverage audit. Before building anything, scan all 488 notes and report what percentage of `products` and `clients` frontmatter values resolve against existing aliases. If coverage is below 60%, spend Day 1 extending alias files. Do not proceed with a sparse entity table — it will create false confidence.

Command: `corp ontology build` — idempotent, nuke-and-rebuild, runs in <5 seconds.

**Week 1, Days 3-5: Entity-aware CLI retrieval (hard requirement)**

- `corp retrieve --entity "JLR"` — all notes linked to JLR entity
- `corp retrieve --entity "JLR" --related products` — all products co-occurring with JLR, with note counts
- `corp retrieve --timeline "JLR"` — JLR notes in chronological order

This is where the value lands. Not in Obsidian. Not in MOCs. In the CLI, where the developer actually works.

**Week 2 (optional, do only if Week 1 is complete and useful):**

- `entity_relationships` table (source_entity_id, target_entity_id, relationship_type, context_note_path) — populated by co-occurrence only, with the explicit caveat that this table is noisy
- Auto-generated MOCs in `_Auto/` folder — one per client with >3 notes, one per product with >5 mentions. Clearly machine-generated. Never edited by hand.
- `corp ontology validate` — reports unresolved entity mentions, suggests alias additions

**What NOT to do:**

- **Do not inject wikilinks, Related sections, or any content into existing markdown files.** Source notes are the source of truth. Period. If the ontology DB corrupts, you rebuild from notes. If you've also modified the notes, your rebuild source is contaminated.
- **Do not restructure folders.**
- **Do not add Neo4j, DuckDB, vector embeddings, or any new runtime dependency.**
- **Do not add cron jobs or file watchers.** Hook `corp ontology build` to the end of the existing pipeline, or run it manually. Cron is a silent failure mode for a solo developer.
- **Do not build relationship type refinement** (decided, requires, competes_with) until you have at least 5 concrete retrieval queries that co-occurrence can't answer.

### The 2am Test

If this system breaks at 2am:
- Source notes are untouched. The vault is intact.
- `corp retrieve` with keyword search still works (FTS5 is independent).
- The fix is: `corp ontology build` — nuke and rebuild from source. Takes 5 seconds.
- If `index.db` is corrupted: delete it, rebuild from markdown files. The notes are the source of truth.
- No external services, no JVM, no model inference, no network dependencies.

### What Convinced Me to Change

1. **Proposal D's blast radius principle** convinced me that wikilink injection into source notes (which I would have included) is wrong. The value doesn't justify the risk. Auto-generated MOCs in a separate folder are safer and nearly as useful.

2. **Proposal C's minimalism** convinced me that the relationship table should be Week 2, not Week 1. Ship entity resolution first. Validate that it's useful. Then add relationships. Proposal B's five-step plan in five days is a recipe for abandonment.

3. **Proposal B's diagnostic** ("relational, not dimensional") convinced me that embeddings remain correctly deferred and that the CLI retrieval interface — not Obsidian — is where the ontology should first surface.

4. **No proposal adequately addressed the alias coverage risk.** If the existing 68 aliases cover only 50% of entity mentions, every downstream artifact is incomplete. I've added a mandatory Day 1 coverage audit that none of the other proposals include. This is the single highest-risk assumption in all four proposals and it must be validated before building anything.

### Signals to Revisit

- Alias maintenance exceeds 30 minutes/month → invest in LLM-suggested entity resolution
- Co-occurrence false positive rate exceeds 40% in the relationship table → either add extraction-based relationship typing or drop the relationship table
- Note count exceeds 2,000 → evaluate whether batch rebuild is still fast enough
- Developer stops running `corp ontology build` for >2 weeks → the system has failed the ADHD sustainability test; simplify further or automate via pipeline hook
- >20% of retrieval queries require semantic matching that entity + keyword search can't serve → evaluate embeddings

*Latency: 116.38s | Tokens: 14091*

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, I view this system through the lens of data integrity, trust boundaries, and blast radius. The Markdown vault is your authoritative source of truth. The extraction pipeline is an automated, potentially faulty actor. Any architecture that allows the automated actor to mutate the authoritative source of truth is fundamentally flawed and introduces an unacceptable blast radius.

Here is my evaluation of the proposals on the table.

---

### Proposal A

**Steelman first:** If we assume the automated extraction and injection scripts are flawlessly written and will never encounter an edge case, baking the relational graph directly into the Markdown files (via inline wikilinks) maximizes portability. The knowledge graph becomes completely independent of any external database or tooling, achieving perfect interoperability.

**Your assessment:** Disagree with Position. Modifying raw, human-authored Markdown notes via an automated post-processing script violates the principle of isolating blast radius. A buggy regex, an unhandled encoding issue, or a misconfigured loop will corrupt the original vault data. 

**Strongest point:** The reliance on manual alias curation over automated machine learning. Human-in-the-loop validation for entity resolution acts as a strong trust boundary, preventing "database poisoning" from automated hallucinations.

**Weakest assumption:** The assumption that post-processing source files is "safe and reversible." Unstructured text mutation is inherently brittle. If you don't use strict transactional rollbacks (impossible with flat Markdown files), a script failure mid-execution leaves the vault in a corrupted, half-processed state.

**Hidden assumptions:** 
1. Assumes Obsidian's native graph cannot be utilized without inline wikilinks (it can, via centralized Map of Content files).
2. Assumes the developer will religiously review git diffs before committing automated changes, which fails in practice for solo developers with ADHD.

**Overlooked risks:** Sync conflicts. If the batch script runs while Obsidian is syncing via a third-party service (e.g., iCloud/Dropbox), file-locking collisions can result in data loss or duplicated files.

---

### Proposal B

**Steelman first:** A highly structured, locally hosted SQL approach using junction tables correctly models a graph without heavy graph DB dependencies. By using strict HTML comment delimiters (`<!-- start -->`), automated edits to the notes can be made idempotent, mitigating some of the risk of unstructured text manipulation.

**Your assessment:** Partially agree. I strongly agree with the architectural decision to use SQLite junction tables and reject embeddings/Neo4j (minimizing supply chain and dependency surface). However, I vehemently disagree with Step 4 (Wikilink injection). Delimiters are not a sufficient security control for data integrity.

**Strongest point:** Identifying that the core problem is relational (SQL joins) rather than dimensional (vector embeddings). This successfully avoids a massive ML supply chain dependency while solving the exact use case presented.

**Weakest assumption:** Assuming that delimiter-based text injection is safe. A user manually editing a note might accidentally delete or alter the `<!-- ontology:related:end -->` tag. The next time the batch script runs, it will truncate or overwrite human-authored text.

**Hidden assumptions:** 
1. Assumes co-occurrence (mentioning a client and product in the same note) reliably implies a meaningful relationship, ignoring the risk of false-positive data poisoning as notes grow longer.
2. Assumes frontmatter is uniformly formatted enough to be parsed without throwing fatal exceptions during the batch run.

**Overlooked risks:** Obsidian search pollution. Appending `## Related` sections to every note injects metadata into the main text body, which will artificially inflate keyword search relevance and degrade native search precision.

---

### Proposal C

**Steelman first:** The absolute minimal viable product. By brutally cutting scope—avoiding relationships entirely and focusing strictly on entity resolution—we minimize schema complexity, limit the amount of code that needs to be maintained, and eliminate graph-traversal performance concerns entirely.

**Your assessment:** Disagree. This proposal accepts the operational risk of mutating source files (appending wikilinks) without delivering the core Palantir-style value (relationship traversal). It exposes the system to the blast radius of file mutation but leaves the primary architectural pain point (isolated concepts) unsolved.

**Strongest point:** The rigid insistence on staying within the current operational scale (<500 notes) and acknowledging the severe limitations of a solo ADHD developer's maintenance capacity.

**Weakest assumption:** Assuming that entity resolution alone (without relationship modeling) improves retrieval precision enough to justify altering the architectural pipeline. Knowing *that* Blue Yonder WMS is mentioned is useless if you cannot query *which client* discussed it.

**Hidden assumptions:** 
1. Assumes flat entity wikilinks are structurally different or more useful than the YAML frontmatter tags already present in the documents. 
2. Assumes users will naturally adopt CLI filters (`--by-entity`) over their habitual keyword search behaviors.

**Overlooked risks:** Users will inevitably attempt to hack relationships into this flat schema (e.g., creating fake entities like `[[JLR-BlueYonder-Meeting]]`), destroying the normalization of the entity table and breaking the system's integrity.

---

### Proposal D

**Steelman first:** Treating the ontology as an ephemeral, read-only projection (CQRS pattern) is the only way to mathematically guarantee the integrity of the original Vault. By isolating generated MOCs to a separate `_Auto/` directory, the system provides graph connectivity without risking a single byte of human-authored source data.

**Your assessment:** Agree. This proposal properly identifies the Markdown Vault as a critical trust zone and the extraction pipeline as an untrusted actor. It provides the required graph capability while strictly containing the blast radius.

**Strongest point:** The architectural decoupling of the authoritative source (Markdown) from the generated index (SQLite + Auto-MOCs). If the system hallucinates, you simply drop the tables, delete the `_Auto/` folder, and rebuild. Zero risk to primary data.

**Weakest assumption:** Assuming the auto-generated MOCs will provide a sufficiently rich, frictionless user experience in Obsidian compared to inline contextual links. Users may find jumping to an MOC jarring compared to clicking a link directly at the bottom of a note.

**Hidden assumptions:** 
1. Assumes the cron job or file watcher triggering the script will run reliably and not create race conditions during rapid file saving.
2. Assumes the user will remember to exclude the `_Auto/` folder from certain Obsidian plugins to avoid circular dependencies.

**Overlooked risks:** Scalability of the MOC rebuild process. Tearing down and rebuilding hundreds of markdown files for every ontology update is viable at 488 notes, but will cause noticeable I/O thrashing and Obsidian indexing lag at 2,000+ notes.

---

### Revised Recommendation

**I am maintaining my position (Proposal D) with critical schema adoption from Proposal B.** 

The other proposals failed to change my mind regarding the mutation of source files. Automatically appending data to human-authored Markdown files is an architectural anti-pattern. If a script fails, corrupts a file, or a user accidentally deletes a delimiter, your data is compromised. Defense-in-depth requires strict unidirectional data flow. 

However, Proposal B's explicit SQLite schema (`entities`, `note_entities`, `entity_relationships`) is technically superior to my original vague definition of the tables. I am updating my position to incorporate that specific schema.

**The Final Architecture:**

1. **Strict Read-Only Projection (Zero Blast Radius):** The Markdown Vault remains the ultimate source of truth. The ontology layer is an ephemeral, derivative view. The pipeline reads the YAML frontmatter, resolves aliases, and populates `index.db`. **It never writes to the original notes.**
2. **Adopt Proposal B's Schema:** Implement the exact three-table SQLite schema proposed in B. It elegantly handles the relational data without requiring Neo4j or vector ML libraries, keeping the supply chain footprint at zero.
3. **Out-of-Band MOC Generation:** Instead of injecting `## Related` links into existing notes (as A, B, and C propose), create an `_Ontology/` folder in Obsidian. A script will dynamically generate read-only Markdown files (e.g., `_Ontology/Client_JLR.md`) containing the backlinks and relationships. If the script fails, you delete the `_Ontology/` folder. Your core vault is untouched. 
4. **Co-occurrence Inference:** Adopt Proposal B's logic of inferring relationships via note co-occurrence, but run it asynchronously. 

This gives you the Palantir-style relational querying you want, via standard SQL and native Obsidian graphs, with an absolute mathematical guarantee that your source documents cannot be corrupted by the automated system.

*Latency: 47.41s | Tokens: 13094*

### Deepseek (deepseek-reasoner)

---

## Steelmanning Each Proposal

### **Proposal A**
**Steelman:** If the primary value is discoverability of related notes via entity-based search—not complex relationship analytics—and the solo developer’s cognitive load must be minimized, then a minimal entity table with backlinks solves 80% of the pain immediately. The proposal’s incremental approach (entity table first, relationships later) is the safest path to value without overengineering.

**Assessment:** *Partially agree.* The proposal correctly identifies SQLite as sufficient and post‑processing as safe, but it under‑specifies relationship capture, which is core to the stated problem (“which client discussed which product in which meeting?”). Deferring all relationship modeling misses the point.

**Strongest point:** *Zero‑risk to existing pipeline.* By treating the ontology as a read‑only derived layer, it guarantees no regression in current functionality—a critical constraint.

**Weakest assumption:** “Entity resolution can be sufficiently solved by extending existing alias files with manual curation.” At 50 notes/month, new entities will appear faster than manual curation can keep up. Within 3 months, the entity registry will drift, degrading search recall.

**Hidden assumptions:**
1. The user’s primary retrieval pattern is “find all notes about entity X,” not “find connections between X and Y.”
2. Obsidian performance is not impacted by adding thousands of wikilinks.

**Overlooked risks:**
- *Query‑pattern lock‑in:* If the CLI only supports entity‑based note retrieval, users will not ask relationship‑based questions even if they need them, creating a false sense of sufficiency.
- *Co‑occurrence blindness:* Without explicit relationships, notes that mention the same entity but discuss different contexts will be falsely linked, adding noise.

---

### **Proposal B**
**Steelman:** If the pain is fundamentally relational (client–product–meeting triples) and the scale is trivial (~500 notes, ~2k relationships), then SQLite junction tables are the simplest complete solution. Generating wikilinks and MOCs delivers immediate Obsidian value without new dependencies, directly addressing the “isolated notes” problem.

**Assessment:** *Agree.* This is the most balanced: it captures relationships via co‑occurrence, uses existing infrastructure, and delivers tangible improvements in both CLI and Obsidian within a week. It respects the solo‑developer constraint while solving the core problem.

**Strongest point:** *Directly addresses the stated pain points with minimal new complexity.* It answers “which client discussed which product” with a SQL join, not a graph database.

**Weakest assumption:** “Alias YAML files are reasonably complete.” This is the same as Proposal A’s weak assumption, but Proposal B at least includes a validation step. If coverage is low, the relationship graph will be sparse.

**Hidden assumptions:**
1. Co‑occurrence in the same note is a reliable proxy for a meaningful relationship.
2. The user will run the batch rebuild regularly (or it will be automated).

**Overlooked risks:**
- *Relationship inferencing false positives:* Two entities mentioned in the same note but unrelated (e.g., “JLR” and “Blue Yonder” in separate sections) will create a spurious “discussed” edge.
- *Wikilink injection scalability:* At 5k wikilinks, Obsidian’s graph view may become a hairball, reducing utility.

---

### **Proposal C**
**Steelman:** If the solo developer’s highest priority is minimizing long‑term maintenance and the only real problem is entity aliasing, then a read‑only entity table with wikilinks is the absolute minimum that moves the needle. Anything more risks abandonment.

**Assessment:** *Disagree.* It ignores the explicit requirement for relationship tracking and temporal ordering. The proposal’s own success metric—“improve retrieval precision by at least 30% on the 20 most frequent clients/products”—is unlikely to be met without relationships.

**Strongest point:** *Lowest maintenance burden.* By doing almost nothing, it guarantees the developer won’t be overwhelmed.

**Weakest assumption:** “The primary retrieval failure mode is entity aliasing, not missing implicit relationships.” The problem statement explicitly lists relationship tracking as a core issue.

**Hidden assumptions:**
1. The user will not ask multi‑hop questions because the scale is small.
2. Temporal ordering can be handled manually via Dataview (but the problem states this as a pain point).

**Overlooked risks:**
- *Premature optimization for developer comfort at the expense of user value.* The system may remain unusable for the stated needs.
- *No path to evolution:* The minimal design offers no upgrade path when relationship queries inevitably arise.

---

### **Proposal D**
**Steelman:** If data integrity is the overriding concern—no automated system should risk corrupting the vault—then a strictly decoupled ontology stored only in SQLite, with generated MOCs as separate files, is the safest. It provides relationship tracking without touching original notes.

**Assessment:** *Partially agree.* The blast‑radius containment is wise, and generating MOCs as separate files is clean. However, avoiding wikilinks in notes reduces Obsidian’s native connectivity, which is a key benefit.

**Strongest point:** *Strict blast‑radius containment.* The ontology is a disposable index; a bug can only corrupt the database, not the source notes.

**Weakest assumption:** “SQLite CTEs will execute in single‑digit milliseconds at <10,000 notes.” This is true for simple joins, but recursive graph traversals (e.g., “show me all decisions influenced by product X”) may degrade earlier.

**Hidden assumptions:**
1. The user will tolerate a separation between original notes and generated MOCs, possibly requiring two different mental models.
2. The pipeline can trigger ontology rebuilds reliably (cron/file watcher).

**Overlooked risks:**
- *Out‑of‑sync MOCs:* If the rebuild isn’t triggered, MOCs become stale, leading to confusion.
- *Lack of bidirectional linking:* Without wikilinks in notes, the Obsidian graph view remains disconnected, undermining the goal of a “connected knowledge base.”

---

## Revised Recommendation

**I update my position to align with Proposal B, with critical modifications from Proposal D.**

**Why the update?**  
Proposal B correctly identifies that the core pain is relational, not just entity‑based, and that SQLite junction tables are sufficient for the scale. However, Proposal D’s emphasis on blast‑radius containment is essential for a solo developer who cannot afford data corruption. The combined approach:

1. **Build the SQLite ontology exactly as Proposal B outlines** (entities, note_entities, entity_relationships), but treat it as a *disposable cache*.
2. **Generate MOCs as separate files** (per Proposal D) rather than injecting wikilinks into original notes. This preserves vault integrity while providing navigational structure.
3. **Extend `corp retrieve` with relationship queries** (e.g., `--relationship client:JLR product:Blue-Yonder`).
4. **Run ontology rebuild as a post‑processing step** that can be triggered manually or via pipeline hook, with a full rebuild taking <10 seconds at current scale.

**What this solves:**
- *Relationships captured:* Client‑product‑meeting triples are stored and queryable.
- *Obsidian value:* MOCs provide at‑a‑glance entity‑centric views.
- *Zero risk to pipeline:* Original notes remain untouched; the ontology is a derived layer.
- *Scalability to ~2k notes:* SQLite handles this; if performance degrades, we can revisit.

**What this rejects:**
- *Graph databases:* Unnecessary for 2k relationships.
- *Vector embeddings:* Deferred until explicit semantic‑search failures emerge.
- *Folder restructuring:* Too risky; ontology lives in the database and MOCs.

**Breakpoint analysis:**  
What breaks first? At ~50k relationship rows, SQLite queries for 3‑hop traversals may exceed 100 ms. That’s 2+ years at current growth. The solo developer will hit cognitive maintenance limits (alias curation) before hitting technical limits. Therefore, the system includes a `corp ontology validate` command to flag unresolved entities weekly, keeping curation under 30 minutes.

**Final architecture:**  
- **Source of truth:** Vault markdown files with YAML frontmatter.
- **Derived layer:** SQLite ontology tables (rebuildable from source).
- **Presentation layer:** Generated MOCs in `_MOCs/` folder, CLI relationship queries.
- **Failure mode:** If ontology generation breaks, vault remains intact; CLI falls back to FTS5 search.

**Signal to pivot:**  
When alias maintenance exceeds 1 hour/week, invest in LLM‑assisted entity resolution. When note count exceeds 2,000 with complex relationship queries, evaluate a lightweight graph layer (e.g., SQLite with closure tables or DuckDB for analytic queries). Until then, SQLite junction tables are the right tool.

*Latency: 124.78s | Tokens: 12502*

### Grok (grok-4.20-beta)

**Steelman A:** For it to be exactly right, the dominant failure mode must be "I can't see which notes share the same real-world thing," alias coverage must already be >70%, the developer must actually enjoy periodic curation, and Obsidian backlinks/MOCs must be the preferred navigation method. Under those conditions, a lightweight derived index that never touches the extraction pipeline is the rational 80/20.

**Assessment:** Partially agree with its Position. The safety of post-processing and SQLite choice are correct, but the proposal still underestimates how quickly "lightweight" entity maintenance becomes soul-crushing for an ADHD solo operator.

**Strongest point:** Post-processing is safe and reversible. This is the only architectural property that actually respects the "must not break existing pipeline" constraint.

**Weakest assumption:** "Manual alias curation scales to ~2k entities" and will stay at 30 minutes/week. This is false. It becomes the new inbox. The moment the developer has a busy client week, the aliases drift, the entity table becomes garbage, and the whole layer is abandoned.

**Hidden assumptions:** 
1. That the value of the system is primarily in *retrieval* rather than in *forcing cleaner thinking during note creation*.
2. That Obsidian's graph view and wikilinks are desirable rather than a noisy mess once you have thousands of machine-generated links.

**Overlooked risks:** Progressive degradation of the entity table over months (not catastrophic failure), leading to false confidence in "we have an ontology" when it's actually 40% accurate. Also, the risk that adding `## Linked Entities` sections pollutes the human voice of the notes.

---

**Steelman B:** For it to be exactly right, relationships must be mostly inferable from co-occurrence in frontmatter, the developer must treat `corp ontology build` as a reliable weekly ritual, and the primary use case must be "show me everything about JLR" rather than fuzzy or temporal questions. In that world, three SQLite tables plus generated MOCs is perfect.

**Assessment:** Disagree. This is the most dangerous proposal. It looks responsible but is classic solo-developer scope creep disguised as minimalism. The moment you have `entity_relationships`, `role`, `confidence`, and multiple relationship types, you've built a half-assed graph database in SQLite and will hate maintaining the inference rules.

**Strongest point:** The explicit rejection of embeddings and Neo4j for the wrong reasons (scale, learning curve) but correct conclusion. The pain is relational, not semantic.

**Weakest assumption:** That frontmatter is consistent enough to infer meaningful `discussed`/`decided` relationships. The current CKE pipeline was not designed for this. The inferred graph will be full of garbage.

**Hidden assumptions:** 
1. That the developer will keep the inference logic in sync with how they actually write notes.
2. That having the ontology in `index.db` separate from the notes is cleaner than it actually is (you now have two sources of truth that will diverge).

**Overlooked risks:** The "idempotent regeneration" of markdown sections is brittle and will create git noise or merge conflicts. Also, the proposal ignores that ADHD developers are unusually bad at "just run this script weekly."

---

**Steelman C:** For it to be exactly right, the core problem must be *entity resolution* and nothing else. If "is Blue Yonder WMS the same as BY WMS" is 80% of the pain, then a simple canonical entity table plus `--by-entity` filter is the correct intervention. Everything else is masturbation.

**Assessment:** Agree with its Position. This is the only intellectually honest proposal. The others are dressing up their desire to build a toy Palantir.

**Strongest point:** Brutal prioritization. It correctly identifies that even "lightweight relationships" is too much for the current evidence and constraints.

**Weakest assumption:** That a 30% improvement in retrieval precision on the top 20 clients/products will feel meaningful. It might not. The user may still experience the vault as a graveyard.

**Hidden assumptions:** 
1. That the user *wants* to interact with entities as first-class objects. They might actually want temporal narratives ("show me the evolution of JLR's WMS requirements").
2. That keeping notes as the sole source of truth is obviously correct. Palantir's deepest insight was that the *ontology* becomes the source of truth and documents are merely evidence.

**Overlooked risks:** The system becomes yet another index the user ignores, like the existing quality score in frontmatter that probably isn't used.

---

**Steelman D:** For it to be exactly right, the dominant fear must be "automated scripts will corrupt my precious markdown files." If blast radius and supply-chain minimalism are the primary values, then treating the vault as immutable and the ontology as a pure projection is correct.

**Assessment:** Disagree. This is fear-driven architecture. The obsession with "never touch the markdown" is a hidden perfectionism that will prevent the system from ever becoming useful.

**Strongest point:** The explicit recognition that folders should not be restructured. Everyone else tiptoes around this; D states it clearly.

**Weakest assumption:** That SQLite recursive CTEs will be pleasant to use or that the developer will write them. They won't. The query interface will be terrible.

**Hidden assumptions:** 
1. That the current markdown files with YAML frontmatter are high-quality enough to serve as the single source of truth forever.
2. That generating MOCs as read-only artifacts is better than having the relationships actually *in* the notes where Obsidian can use them natively.

**Overlooked risks:** The ontology becomes completely detached from the user's daily workflow. If it's only in `index.db` and some auto-generated `_Auto/` folder, it will be treated as an external tool rather than the knowledge base itself.

---

**Revised Recommendation**

I update my position. The correct answer is **a more aggressive version of C, not A, B, or D**.

Everyone is taking for granted that we should build *more structure on top of the existing notes*. The real contrarian move is to admit the current note format is the problem. The pipeline already extracts structured data. We should stop treating the markdown files as sacred containers and start treating the SQLite database as the primary knowledge store, with notes as *views* or *evidence attachments*.

But we should do the absolute minimum of that: **only the entity table (C)**, no relationship tables, no wikilink injection into existing notes, no MOCs. Just canonical entities with back-references to the original note paths.

The evidence that changed my mind is the collective hidden assumption across A, B, and D that "of course we keep appending more generated sections to the markdown files." This is how personal knowledge bases die. The moment the generated sections become outdated or the regeneration script has a bug, the notes become noisy and the user stops trusting the system.

**What to do instead:** Implement exactly C's entity table as a derived index. Make `corp retrieve --entity` the *default* way to interact with the system. Use Dataview in Obsidian to query the generated entity MOCs if you must, but do not pollute the original notes. Accept that this is a thin layer of normalization, not an ontology.

This is the only approach that can be built in <1 week, abandoned without guilt, and still deliver value. Everything else is solo-developer cosplay of Palantir.

*Latency: 17.12s | Tokens: 10911*

## Synthesis (by openai, non-participant)

## Consensus

### 1) Do **not** adopt a full Palantir-style ontology stack
**Consensus level:** Strong  
**Why:** Nearly everyone independently argued that Neo4j/full graph DBs, heavy ontology infrastructure, and Palantir-scale architecture are disproportionate for 488 notes, one developer, SQLite preference, minimal dependencies, and a 1-week value horizon.

This was **evidence-based**, not mere echoing:
- Scale is small: hundreds of notes, not millions.
- Existing pain points are narrow and concrete: aliasing, relationship lookup, timelines.
- Existing infra already supports a simpler solution: YAML frontmatter, aliases, SQLite, FTS5.

### 2) Use **SQLite** and keep the ontology as a **derived/post-processing layer**
**Consensus level:** Very strong  
**Why:** Most participants converged on:
- SQLite tables are enough for current scale.
- The new layer should be rebuildable from notes/frontmatter.
- It should not break the current pipeline.

This was also well-reasoned:
- Current corpus and expected growth are trivial for indexed SQL joins.
- A rebuildable derived index minimizes operational risk.
- It fits the “solo dev with ADHD” constraint better than another service or DB.

### 3) Defer **embeddings/vector search**
**Consensus level:** Strong  
**Why:** Most argued semantic search solves a different problem than the one described. The current pain is mostly:
- entity resolution
- note-to-note connection
- “which client discussed which product”
- timeline reconstruction

That is a good argument. Embeddings may help later, but they are not the first bottleneck.

### 4) Do **not** restructure folders around the ontology
**Consensus level:** Strong  
**Why:** Most participants said folder structure should remain simple; ontology belongs in the DB/query layer, not physical file placement.

This is well-supported:
- Folder reorg creates blast radius.
- It does not solve canonicalization or relationship modeling.
- It risks breaking workflows for little immediate gain.

### 5) Keep the current extraction pipeline intact; add ontology as **post-processing first**
**Consensus level:** Strong  
**Why:** Most participants preferred reading current frontmatter and alias files rather than rewriting CKE immediately.

This was one of the better-supported points:
- safer
- reversible
- faster to implement
- easier to abandon if not useful

---

## Unresolved Disagreements

### 1) Should the MVP include **relationships**, or only **entities**?
#### The crux
Is the main problem actually:
- **entity normalization/searchability** (“BY WMS” = “Blue Yonder WMS”), or
- **relational querying** (“which client discussed which product in which meeting?”)

#### Sides
- **Entity-only camp:** grok strongly, some minimalists implicitly
- **Entity + relationships camp:** claude, gemini, deepseek

#### Stronger side: **Entity + relationships**, but narrowly scoped
**Why:** The problem statement itself is relational. The user explicitly called out:
- no relationship tracking
- no temporal ordering
- no cross-note links
- “which client discussed which product in which meeting?”

An entity-only table would fix aliasing and filtering but would **not** address the central stated pain.  
However, the strongest version of the relationship argument was **not** “full graph”; it was “simple co-occurrence/junction-table relationships in SQLite.”

That said, opponents raised a valid objection: naive co-occurrence can create noisy false relationships. So the winning position is **relationships, but only simple, documented, low-trust ones initially**.

---

### 2) Should the system write generated links/sections back into source notes?
#### The crux
Is the extra usability from inline wikilinks worth the risk and noise of mutating the vault?

#### Sides
- **Mutate notes:** early claude/deepseek/grok variants supported wikilink injection
- **Do not mutate notes:** gemini strongly; revised claude and revised deepseek moved here

#### Stronger side: **Do not mutate source notes**
**Why:** This was the most convincing architectural dispute in the debate.
Reasons:
- Source notes are your durable truth.
- Bulk mutation creates git noise, sync risk, stale generated content, and hidden corruption risk.
- Separate generated artifacts (DB + MOCs) preserve recoverability.
- The same value can be surfaced via CLI and generated MOCs without touching originals.

This was one of the clearest cases where a minority-strengthened argument moved others.

---

### 3) Should Obsidian be a primary surface for the ontology, or should CLI come first?
#### The crux
Where will the value actually be consumed?

#### Sides
- **CLI-first:** revised claude especially
- **Obsidian/MOC-heavy:** several earlier proposals
- **Obsidian as dumb viewer:** gemini leaning this way

#### Stronger side: **CLI first, Obsidian second**
**Why:** The debate correctly noted that generated MOCs or graph views are only valuable if they match actual usage. The prompt says primary interfaces are:
- corp retrieve
- corp prep
- Obsidian

But many proposals assumed Obsidian artifacts would automatically matter. That was weakly evidenced. The better-grounded position is:
- land the value first in `corp retrieve` / `corp prep`
- then add generated MOCs as secondary affordances

---

### 4) Build relationship typing now, or only basic co-occurrence?
#### The crux
Can frontmatter/supporting extraction support trustworthy typed relations like `discussed`, `decided`, `requires`?

#### Sides
- **Basic co-occurrence only for now:** most mature proposals
- **Typed relationships soon:** some early richer ontology suggestions

#### Stronger side: **Basic co-occurrence/context-backed links only**
**Why:** The debate exposed a real issue: co-occurrence can be noisy, and typed semantic relationships inferred from frontmatter are likely low-trust. Given the 1-week constraint, stronger typing should be deferred until there are concrete query failures and better extraction signals.

---

## Argument Quality Assessment

### Best-reasoned proposals
#### 1) **Revised Claude**
Best overall synthesis:
- correctly diagnosed the problem as relational, not semantic
- kept scope bounded to SQLite/post-processing
- shifted away from source-note mutation after hearing better arguments
- added the crucial **alias coverage audit** before implementation
- prioritized CLI value over decorative graph features

This was the strongest proposal because it combined:
- technical fit
- operational safety
- implementation realism
- direct alignment with the actual pain points

#### 2) **Gemini**
Strongest on **architecture safety / blast radius**:
- source notes as trust boundary
- ontology as disposable projection
- no mutation of raw notes
- low dependency footprint

Gemini was less strong on workflow usability, but strongest on system integrity.

#### 3) **Deepseek revised**
Good practical middle ground:
- SQLite tables
- generated separate MOCs
- rebuildable derived layer
- sensible breakpoints and scaling discussion

### Weaker proposals
#### Early/strict **entity-only** proposals
These were coherent on scope control and maintainability, but they underfit the stated problem. They solved aliasing while leaving the central relational questions unsolved.

#### Proposals advocating note mutation
These weakened themselves by underestimating:
- git churn
- stale generated sections
- source-of-truth contamination
- sync/editor edge cases

---

### Single strongest argument in the entire debate
**“Your pain is relational, not dimensional.”**  
This was the key insight. It explains why:
- embeddings are not first priority
- graph DBs are unnecessary
- entity normalization alone is insufficient
- SQLite joins are enough

It directly maps the architecture to the actual user pain.

### Single weakest argument in the entire debate
A tie between:
1. **“Manual alias curation will stay lightweight/sustainable”** as an untested assumption, and
2. **“Co-occurrence relationships are acceptable by default”** without measuring false-positive rate.

Both are weak because they are central assumptions with little evidence. The debate improved when participants started demanding validation instead of assuming these.

---

## Blind Spots

### 1) No one seriously evaluated **whether current frontmatter quality is good enough**
Everyone assumed the existing YAML is structured enough to support a reliable ontology build. That may be false. The debate mentioned alias coverage, but not:
- missing fields
- inconsistent dates
- multi-value formatting inconsistencies
- extraction omissions by doc type

This is a major implementation risk.

### 2) The debate underexplored **temporal modeling**
The prompt explicitly asks about “how did JLR requirements evolve across 5 meetings?”  
Most proposals answered with “sort notes by date,” which may be enough initially, but nobody deeply addressed:
- what date field is authoritative?
- meeting date vs file date vs extracted event date
- how to represent requirement evolution or decision supersession

### 3) No one defined **success metrics** sharply enough
A few proposals suggested thresholds, but the debate lacked a concrete evaluation plan like:
- top 10 retrieval tasks before/after
- reduction in manual searching time
- percentage of unresolved entities
- precision of co-occurrence relationships on a sampled set

Without this, it is easy to build something that feels sophisticated but adds little value.

### 4) No one seriously considered a **hybrid “entity pages as generated notes, but no relationship table yet”** experiment
The debate polarized between entity-only and entity+relationship. A staged test plan could have been clearer:
- build entities + note_entities first
- add timeline queries
- sample relationship inference before creating a formal relationship table

### 5) Little discussion of **person entities**
Several mentioned deferring people, which is reasonable, but no one deeply justified when person resolution becomes worth it or how much ambiguity it introduces compared with products/clients.

---

## Recommended Decision

### Decision
**Do not adopt a full Palantir-style ontology layer.**  
Instead, build a **minimum viable ontology in SQLite** as a **derived, rebuildable post-processing layer**, consisting of:

1. **Canonical entity registry**
2. **Note-to-entity junction table**
3. **Optional, low-trust entity-to-entity co-occurrence table** only after validation
4. **CLI-first retrieval features**
5. **Separate generated MOCs/pages if useful**
6. **No mutation of source notes**
7. **No folder restructuring**
8. **No embeddings yet**

### Why this is the best path
It best matches the strongest arguments in the debate:
- The problem is relational.
- But the scale does not justify Palantir-style machinery.
- SQLite is enough.
- The ontology should be a derived view, not a source of truth.
- The first value should show up in `corp retrieve`/`corp prep`, not in an elaborate graph UI.
- Source-note mutation is an unnecessary risk.

### Minimum viable scope
#### Week-1 MVP
- `entities`
- `note_entities`
- alias resolution / canonicalization
- entity-aware retrieval
- chronological views per client/product

#### Week-2 only if MVP proves useful
- `entity_relationships` via simple co-occurrence with context note/date
- generated MOCs in separate folder
- validation/reporting for unresolved entities

### Strongest objections, and why they were outweighed

#### Objection: “Even relationships are overengineering; do entity-only.”
**Why outweighed:**  
The prompt’s main pain points are explicitly relational. Entity-only would improve search but leave the hardest questions manual.

#### Objection: “Co-occurrence relationships will be noisy.”
**Why partly accepted:**  
This is true. That’s why relationships should be:
- delayed until after entity MVP or at least validated
- clearly labeled as inferred
- backed by context note/date
- not treated as high-trust semantic truth

#### Objection: “Don’t make SQLite into a fake graph DB.”
**Why outweighed:**  
A few indexed tables and joins are not “fake graph DB overengineering”; they are the simplest way to represent exactly the needed queries at this scale.

#### Objection: “Obsidian integration may be low-value.”
**Accepted.**  
Therefore Obsidian should be secondary, not primary. CLI-first resolves this concern.

---

## Risks

### 1) Alias coverage is too low, producing a sparse or misleading ontology
**Mitigation:**
- Run a corpus-wide alias coverage audit before building the ontology
- Refuse to treat ontology outputs as trustworthy until coverage is above a defined threshold
- Add unresolved-entity reporting

### 2) Frontmatter quality is inconsistent
**Mitigation:**
- Validate required fields and formats during build
- Produce a data quality report by note/doc_type
- Fall back gracefully: unresolved values remain raw mentions, not canonical entities

### 3) Co-occurrence creates false relationships
**Mitigation:**
- Start with note-to-entity links only
- If adding entity-to-entity relationships, label them `inferred_from_same_note`
- Store context note/date
- Sample-check precision before exposing broadly in CLI

### 4) The ontology becomes another abandoned side system
**Mitigation:**
- Keep it rebuildable and tiny
- Integrate value into existing commands (`corp retrieve`, `corp prep`)
- Avoid any manual upkeep beyond alias review
- Prefer pipeline hook over cron if automating

### 5) Generated artifacts clutter Obsidian
**Mitigation:**
- Put all generated pages in a dedicated `_Ontology/` or `_Auto/` folder
- Make them disposable
- Do not write into human-authored notes

### 6) Success is not measurable, so scope drifts
**Mitigation:**
- Define 5–10 real retrieval questions now
- benchmark before/after
- stop after MVP if improvement is small

---

## Action Items

### Day 0: Define success
1. Write down **10 representative retrieval questions**, e.g.:
   - What products has JLR discussed?
   - Show JLR meetings in chronological order.
   - Which notes mention Blue Yonder WMS under any alias?
   - Which clients have discussed Manhattan vs Blue Yonder?

2. Define MVP success metrics:
   - unresolved entity rate
   - time-to-answer for the 10 queries
   - sample precision on entity resolution
   - sample precision on inferred relationships if added

### Day 1: Audit data quality
3. Build a **coverage audit** over all 488 notes:
   - percent of `client` values resolved to canonical client
   - percent of `products` resolved
   - missing/invalid date fields
   - empty or inconsistent frontmatter fields by doc_type

4. Expand alias files enough to clear a minimum threshold.

### Days 2–3: Implement the MVP schema
5. Add SQLite tables:
   - `entities`
   - `note_entities`

Suggested minimal schema:
- `entities(id, canonical_name, entity_type, aliases_json, first_seen, last_seen, note_count)`
- `note_entities(note_path, entity_id, role, confidence, observed_date)`

6. Create `corp ontology build`:
   - idempotent
   - nuke-and-rebuild or UPSERT-based
   - reads frontmatter + alias yaml
   - outputs validation summary

### Days 3–4: Surface value in CLI
7. Extend `corp retrieve` with:
   - `--entity "JLR"`
   - `--entity "Blue Yonder WMS"`
   - `--timeline "JLR"`
   - related-entity summaries from shared notes

8. Extend `corp prep` to use entity summaries/timelines where helpful.

### Day 5: Validate usefulness
9. Re-run the 10 benchmark queries and compare:
   - time saved
   - correctness
   - whether any important query still requires manual note trawling

### Week 2 only if Week 1 is successful
10. Add a cautious `entity_relationships` table for **inferred co-occurrence**:
   - `source_entity_id`
   - `target_entity_id`
   - `relationship_type` = `co_occurs_in_note`
   - `context_note`
   - `observed_date`

11. Expose relationship queries in CLI only after sampling their precision.

12. Optionally generate separate `_Ontology/` MOCs/pages for high-value entities.  
**Do not modify source notes.**

### Explicitly defer
13. Defer:
   - Neo4j
   - embeddings/vector search
   - folder restructuring
   - making notes into DB views
   - rich typed semantic relationships

---

Bottom line: **Adopt a lightweight SQLite-based ontology layer, not a Palantir-style ontology platform.** Build **entities first, relationships cautiously, CLI first, source notes untouched.**
