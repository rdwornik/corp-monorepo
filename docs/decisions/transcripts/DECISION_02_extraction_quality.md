# AI Council Debate: # AI Council Debate: Knowledge Extraction Quality — Deep Extraction + Image Supp

**Date:** 2026-03-14 23:37:19
**Panel:** deepseek-reasoner, gemini-3.1-pro-preview, grok-4, gpt-5.2
**Synthesizer:** claude (non-participant)
**Rounds:** 2
**Duration:** 361.9s
**Mode:** full (4-model panel)
**Source:** council_inbox\council-extraction-quality.md

---

## Round 1: Initial Responses

### Gemini (gemini-3.1-pro-preview)

## Position
Implement a schema-driven Base + Overlay extraction pipeline with extract-and-describe multimodal capabilities, treating high-value documents to deeper parsing while upgrading legacy notes via an extract-on-demand strategy. Fix this data foundation for high-value targets first to ensure safe, predictable interoperability for all downstream workflows within your $10/month budget.

## Rationale
As an architect focused on integration and security, relying on unstructured, free-text LLM summaries is an integration anti-pattern (garbage in, garbage out). Downstream systems need reliable contracts.

*   **Extraction Depth & Schema (Q1: C+D & Q3: C):** Adopt a **Base + Overlay** schema with **Tiered Depth**. Every document gets a Base schema (metadata, summary, entities) for baseline interoperability. High-value types (Architecture, RFPs) trigger an Overlay schema (SLA tables, APIs, components) requiring deeper, structured multi-pass extraction. This guarantees predictable YAML/JSON contracts for your `corp prep` scripts while preventing API budget exhaustion on low-value files.
*   **Safe Image Processing (Q2: C):** Adopt **Extract + Describe**. Extracting arbitrary binaries (images) from untrusted third-party documents is a threat vector. By passing them through Gemini Flash Vision to generate markdown descriptions, you convert opaque, potentially risky binaries into structured, searchable text. Save the images, but rely on the generated descriptions for semantic indexing. 
*   **Cost vs. Quality (Q4):** **$5-10/month is an excellent investment.** The baseline cost of $0.30/month is a false economy because the resulting data is practically useless for pre-sales. Upgrading to Gemini 3 Flash for deep, structured extraction is financially viable and massively increases knowledge utility.
*   **Re-extraction & System Stability (Q5: D):** Use **Extract-on-Demand**. Do not nuke the existing 2,222 notes. A mass batch job risks index corruption and API rate-limiting. When `corp prep` hits a legacy (shallow) note, dynamically trigger the deep extraction overlay. This isolates failure domains and spreads out API costs.
*   **Sequencing (Q6: C):** Adopt a **Hybrid approach**. Fix extraction for your highest-value documents (product docs, architecture) immediately. Downstream workflows built on poor data will fail; you must establish a high-fidelity data contract before building complex retrieval agents.

## Trade-offs
*   **Pipeline Complexity:** Moving from a single-pass extraction to Base + Overlay routing significantly increases the code complexity of the Corporate Knowledge Extractor (CKE).
*   **Latency:** Multi-pass structured extraction and multimodal vision processing will take noticeably longer per document than the current lightweight approach.
*   **Eventual Consistency:** By choosing extract-on-demand, your Obsidian vault will operate in a mixed-fidelity state (some shallow notes, some deep notes) for an extended period until all legacy documents are organically accessed.

## Risks
*   **Threat Surface — Indirect Prompt Injection:** Deeper parsing of untrusted, external RFPs and documentation vastly increases the attack surface for malicious instructions hidden in the text. 
    *   *Mitigation:* Use strict Schema output enforcement (e.g., Gemini JSON mode). Do not allow the LLM to output free markdown; force it to populate specific fields (e.g., `architecture_components: []`).
*   **Threat Surface — Malicious Media Payloads:** Extracting embedded images from PDFs/Word docs exposes your local machine to image-parsing vulnerabilities (e.g., steganography, corrupted headers).
    *   *Mitigation:* Never extract and save raw binaries directly to the Obsidian vault. Use a local, memory-safe library to explicitly re-encode all extracted media into standard `.png` formats before saving them to `source/images/`.
*   **Integration Risk — Schema Drift:** Over time, adding new Base/Overlay schemas can break the YAML frontmatter parsing in `corp prep`.
    *   *Mitigation:* Define all schemas in a version-controlled `content_registry.yaml`. Implement a schema validation step (e.g., Pydantic) before CKE writes the markdown file to Obsidian.
*   **Cost Runaway:** Vision models and multi-pass extraction on large documents can occasionally loop or spike token usage.
    *   *Mitigation:* Enforce hard token limits on the Gemini API calls and set up GCP billing alerts at the $8 and $10 thresholds to prevent denial-of-wallet scenarios.

*Latency: 28.94s | Tokens: 5035*

### Deepseek (deepseek-reasoner)

## Position
Adopt a tiered depth strategy with structured extraction for high-value documents, defer image extraction initially, and use type-specific prompts for core document types. Immediately re-extract the top 200-300 high-value documents with improved prompts while maintaining existing shallow notes for others.

## Rationale
- **Tiered depth + structured extraction** maximizes knowledge-per-dollar: deep extraction for product docs/architecture/RFP responses (where detail matters), shallow for others. Structured schemas (SLA tables, component lists) directly support RFP answers.
- **Type-specific prompts** capture domain-specific details: architecture docs need component diagrams; security docs need controls/compliance; commercial docs need pricing tiers. Base + overlay approach maintains consistency.
- **Selective re-extraction** balances cost and benefit: re-extracting ~300 high-value files (14% of total) yields 80%+ of knowledge value for under $3. On-demand re-extraction handles remaining files when accessed.
- **Deferred image extraction** prioritizes core text quality: images add storage/complexity and increase costs 2-5x. Textual descriptions of diagrams can be extracted initially; actual images added later.

## Trade-offs
- **Immediate diagram access sacrificed**: Pre-sales engineers won't have embedded images initially, must reference source documents for visuals temporarily.
- **Inconsistent note depth**: Older low-value notes remain shallow, creating knowledge gaps until accessed. Users may need to manually trigger deep extraction.
- **Increased prompt engineering complexity**: Maintaining multiple extraction schemas and type classifiers adds development overhead versus a universal prompt.
- **Higher per-file cost for critical documents**: Deep extraction of high-value files costs 3-5x more, but remains within budget by limiting volume.

## Risks
- **Document misclassification**: Low-value documents incorrectly flagged as high-value waste budget. Mitigation: implement simple rules (filename patterns, folders) plus manual override.
- **Schema rigidity**: Predefined extraction schemas may miss novel content. Mitigation: include "other key findings" free-text field and regularly review schema coverage.
- **Cost overruns**: Unbounded on-demand re-extraction could exceed $10/month. Mitigation: implement monthly extraction budget cap and queue lower-priority extractions.
- **Integration complexity**: Multiple extraction paths could break existing note indexing. Mitigation: maintain backward compatibility by adding new fields to YAML frontmatter, not altering existing structure.

---

## Detailed Recommendations

### Q1: Extraction Depth Strategy → **C + D (Tiered Depth + Structured Extraction)**
- **High-value files** (product docs, architecture, RFP responses): Use structured extraction with predefined schemas (SLA table, component list, pricing tiers). Cost: ~$0.005-0.01/file.
- **Low-value files** (meeting notes, generic presentations): Keep single-prompt extraction but enhance to capture action items and decisions. Cost: ~$0.002/file.
- **Implementation**: Classify using file path patterns (`/product-docs/`, `/architecture/`) initially; later add lightweight LLM classification if needed.

### Q2: Image Extraction → **E then C (Defer, then Extract + Describe)**
- **Phase 1**: Extract text descriptions of diagrams using multimodal prompt: "Describe any diagrams/tables/charts in detail for technical reference."
- **Phase 2** (after text extraction solid): Implement selective extraction with Gemini classification, store images in `/attachments/`, generate alt-text descriptions.
- **Rationale**: Text descriptions provide 80% of value; actual images can be added later when budget allows.

### Q3: Extraction Schema → **C (Base + Overlay)**
- **Base schema** (all documents): Title, summary, topics, key dates, people, organizations.
- **Type overlays**:
  - Architecture: Components, integrations, APIs, data flows
  - Product Docs: Features, limitations, system requirements
  - RFP Responses: Compliance status, SLAs, commercial terms
  - Meeting Notes: Decisions, action items, follow-ups
- **Implementation**: Document type detector using folder heuristics + filename patterns.

### Q4: Cost vs Quality → **Target $3-5/month**
- Accept 10-15x cost increase for 10x knowledge utility.
- Budget breakdown:
  - 100 high-value files @ $0.01 = $1.00
  - 200 low-value files @ $0.002 = $0.40
  - Re-extraction 300 files @ $0.01 = $3.00
  - Monthly new files: $1.40
  - Total: ~$5.80/month (within $10 limit)

### Q5: Re-extraction → **B + D (Selective + On-demand)**
- **Immediate**: Re-extract 200-300 high-value documents identified by usage patterns and folder location.
- **Ongoing**: When `corp retrieve` accesses a shallow note, trigger async re-extraction and update note.
- **Preserve existing**: Keep all 2,222 notes; new extractions create new notes with `_deep` suffix if conflict concerns exist.

### Q6: Sequencing → **C (Hybrid)**
1. **Week 1-2**: Implement tiered depth + structured extraction for architecture and product docs (highest value).
2. **Week 3-4**: Update `corp rfp answer` to use new structured fields; continue workflow development.
3. **Month 2**: Add remaining document type schemas; implement on-demand re-extraction.
4. **Month 3**: Evaluate image extraction implementation.

---

## Prompt Engineering Recommendations

### Deep Extraction Prompt Structure
```
Role: Technical knowledge extraction expert
Task: Extract structured information from {document_type}

Instructions:
1. First, analyze document structure and identify sections.
2. Extract verbatim critical details: numbers, specifications, API endpoints, SLA values.
3. Fill the following schema:

frontmatter:
  title: 
  document_type:
  slas:
    - tier: 
      uptime: 
      rto: 
      rpo:
  architecture_components:
    - name:
      purpose:
      interfaces:
  security_controls: []
  pricing_tiers: []

4. Provide detailed markdown covering: architecture, integrations, security, DR, commercial terms.
5. For diagrams: describe content, type, and key insights conveyed.
6. Do not summarize; preserve technical specifics.
7. If information is absent, note "Not specified" not "N/A".

Length target: 30-40% of source document length.
```

### Classification Prompt
```
Classify document for extraction depth:
- DEEP: product documentation, architecture, RFP responses, security whitepapers
- STANDARD: meeting notes, presentations, general reports

Consider: filename, folder path, content keywords.
```

---

## Performance Notes
- **Token efficiency**: Use `gemini-3-flash-preview` for extraction; reserve `gemini-1.5-pro` for complex document classification if needed.
- **Local processing**: Perform text extraction, file type detection, and image extraction locally to reduce API calls.
- **Caching**: Cache extraction results for 30 days unless source file modified (based on hash).
- **Parallelization**: Process up to 5 documents concurrently within local resource limits (32 GB RAM).

This approach improves extraction depth 3-5x while keeping costs under $10/month, directly addressing the pre-sales engineer's need for detailed technical knowledge.

*Latency: 129.70s | Tokens: 6063*

### Openai (gpt-5.2)

## Position
Adopt **tiered, structured, multi-pass extraction (C + D + light B) with selective verbatim capture (E)** for high-value docs, and add **selective image extraction + description (A + C with lightweight heuristics, optional LLM filter later)**. Re-extract **selectively** and sequence as a **hybrid (C)**: fix extraction for architecture/product/RFP docs now while workflows continue for everything else.

## Rationale
- **Best knowledge-per-dollar comes from targeting depth where it matters**: pre-sales value concentrates in product/architecture/security/commercial docs; meeting notes and marketing PDFs don’t deserve 3-pass deep dives.
- **Structured schemas beat “write more text”**: forcing tables for SLA/DR/security/integrations dramatically improves retrieval and RFP-answerability while reducing hallucination (the model must fill specific fields with citations or “not found”).
- **Two-pass is the practical sweet spot** on a local-first, single-user system: Pass 1 = classify + outline + extraction plan; Pass 2 = sectioned extraction into schemas + citations. A third synthesis pass is optional and can be deferred.
- **Verbatim anchors reduce risk**: capturing key clauses (SLA, RTO/RPO, pricing metrics) as quoted blocks with page/section pointers creates defensible answers and improves trust.
- **Images become searchable only when described**: saving diagrams alone helps visually, but adding a short generated description makes them retrievable via Obsidian search and embeddings.

## Trade-offs
- **More complexity in the extractor**: you’ll maintain doc-type routing, schemas, and multi-step orchestration instead of one prompt.
- **Slightly higher latency per file**: deep extraction will take seconds-to-minutes, especially with image rendering/description.
- **Some inconsistency across notes** during transition: older shallow notes will coexist with enriched ones unless you selectively re-extract.
- **More storage** for images/slide renders, plus vault noise if filtering isn’t good.

## Risks
- **Hallucinated specifics (SLA numbers, RTO/RPO, pricing)**  
  *Mitigation:* require citations for every numeric/contractual field; if not present, force `null` + “Not found in source” and store a “needs verification” flag in YAML.
- **Token/cost blow-up on large docs**  
  *Mitigation:* chunk by section headings (or page ranges), cap per-section output, and only run deep tier on flagged/high-value docs; add a hard per-doc budget (e.g., max output tokens).
- **Image noise (logos, icons) polluting the vault**  
  *Mitigation:* start with deterministic heuristics (size, aspect ratio, duplicate hash, “logo-like” small images), keep a “quarantine” folder; optionally add LLM classification later.
- **Breaking existing retrieval/index**  
  *Mitigation:* keep note filenames and frontmatter keys stable; version the extraction (`extraction_version: 2`, `depth: deep|quick`), append new sections rather than rewriting IDs/paths.
- **Operational drag (re-extraction backlog, partial upgrades)**  
  *Mitigation:* implement extract-on-demand + selective batch for top 200–300 docs; track a queue and progress in a small manifest.

---

# Council Decisions (Q1–Q6)

## Q1: Extraction Depth Strategy
**Recommendation:** **C (Tiered depth) + D (Structured extraction) + light B (2-pass)**, with **E (verbatim snippets)** for contract/spec sections.

**Concrete approach**
- **Pass 0 (cheap, deterministic):** text extraction + basic structure detection (headings, tables where possible), file fingerprint.
- **Pass 1 (LLM, cheap): “Classify + Plan”**
  - Determine doc type: `architecture|product|security|commercial|rfp|meeting|training|marketing|other`
  - Decide depth: `quick|standard|deep` (rules + user override)
  - Produce outline with section boundaries and “extraction targets” (e.g., “SLA”, “DR”, “Integrations”).
- **Pass 2 (LLM, targeted): “Schema fill by section”**
  - Iterate sections; fill schemas with **citations** and **verbatim quotes** for critical fields.
  - Output is mostly tables/fields, not prose.
- **Optional Pass 3 (later):** synthesis into “battlecard” view (1 page) using already-extracted structured data (no need to reread source).

**Cost-benefit**
- **A (deeper single prompt):** low engineering, but unreliable; tends to bloat + hallucinate. Marginal gains.
- **B (full multi-pass 3x):** highest quality but unnecessary early; 2-pass gets 80% of value.
- **C + D:** best ROI for RFP use because answers become lookups, not re-interpretations.
- **E:** adds defensibility with minimal extra tokens.

## Q2: Image and Diagram Extraction
**Recommendation:** Start with **A + C** (extract images + describe) using **heuristics to filter**, and add optional **LLM-based usefulness classification** only if noise becomes painful.

**Concrete strategy (single-user, pragmatic)**
1. **Extract images** from docx/pptx/pdf into `assets/<doc_id>/`.
2. **Filter heuristics (no AI):**
   - Drop images below size threshold (e.g., <30KB or <300px on either dimension)
   - Deduplicate via perceptual hash
   - Prefer wide/large images (diagrams tend to be larger)
3. **Describe kept images (multimodal call per image):**
   - 3–8 bullets: what the diagram shows, components, arrows/flows, protocols if visible
   - If text is present, OCR-like transcription of labels
4. **Embed in note:**
   - Inline image link + “Figure X: …” description
   - Add YAML: `figures: [{file:..., type: architecture_diagram|table|chart, summary:...}]`

**Why not D (render every slide/page) first?**
- Slide/page renders are extremely useful for fidelity, but heavy/noisy. Make it an *on-demand* mode for PPT decks used in presentations.

## Q3: Extraction Schema — One Size vs Per-Type
**Recommendation:** **C (Base + overlay)** with a small set of **type-specific overlays**, plus **D (user-defined templates)** as a later enhancement.

**Minimum viable set (covers most pre-sales)**
- **Base schema (all docs):**
  - `title, vendor, product, doc_type, version/date, source_path, extraction_version, depth`
  - `topics/tags`, `entities`, `summary (5 bullets max)`, `key_quotes[] (with citations)`
- **Architecture overlay:**
  - `architecture_layers[]`, `components[]`, `data_flows[]`, `deployment_model`, `tenancy`, `environments`, `integrations[]`, `extensibility`, `limits/quotas`
- **SLA/Operations overlay (often in arch docs too):**
  - `sla_tiers[]`, `availability`, `support_hours`, `escalation`, `maintenance_windows`
- **Security/Compliance overlay:**
  - `authn/authz`, `encryption`, `network_controls`, `audit_logging`, `certifications`, `data_residency`
- **DR overlay:**
  - `rto, rpo`, `backup`, `failover_process`, `regions`
- **Commercial overlay:**
  - `pricing_model`, `meters`, `tiers`, `overages`, `contractual_constraints`

## Q4: Cost vs Quality Tradeoff
**Recommendation:** Yes—**$5–10/month is acceptable** because it buys RFP-grade specificity; enforce budgets with tiering and caps.

**Pragmatic budget model**
- Monthly volume: ~300 files
- Assume:
  - 70% quick (1 pass, base only)
  - 25% standard (2 pass, base + light overlays)
  - 5% deep (2 pass + images + quotes)
- Result: typically **$2–6/month** depending on image count.
- Add guardrails:
  - Max images described per doc in standard mode (e.g., 3)
  - Deep mode only on explicit tag or doc_type match (architecture/product/security/commercial)

## Q5: Re-extraction Strategy
**Recommendation:** **B (selective re-extraction) + D (extract-on-demand)**; avoid nuking 2,222 notes.

**Concrete plan**
- Build a “high-value list”:
  - Product/architecture/security/commercial docs + anything referenced by `corp prep` frequently
  - Target **200–300 docs** first
- Add **extract-on-demand**:
  - When retrieval hits a note with `extraction_version: 1` and doc_type in high-value set, queue re-extraction.
- Keep old notes intact:
  - Write enriched content into the same note under a new heading `## Deep Extract (v2)` or add a sibling note with stable backlinks.
  - Maintain `source_path` and `doc_id` so index doesn’t break.

## Q6: Sequencing
**Recommendation:** **C (Hybrid)** — upgrade extraction for the high-value doc types immediately, continue building workflows for everything else.

**Order of operations (fastest path to user value)**
1. Implement doc classification + tiering + extraction_versioning (small change, big leverage)
2. Implement structured overlays for architecture/SLA/security/DR/commercial
3. Implement 2-pass extraction for deep tier only
4. Add image extraction + description (deep tier only)
5. Start selective backfill (200–300 docs) + on-demand enrichment

---

# Prompt / Extraction Engineering Recommendations (specific)

## 1) Hard requirements to reduce hallucination
Add to every deep extraction prompt:
- **“Do not guess.”** If not in source: output `null` / `not_found`.
- **Citations required** for:
  - numbers (SLA %, RTO/RPO, pricing thresholds)
  - named standards (SOC2, ISO, HIPAA)
  - claims about tenancy, regions, encryption
- Citation format: `[[source#p12]]` or `[[source#sec:Disaster Recovery]]` depending on what you can compute.

## 2) Output as schemas, not prose
Have the model emit **YAML blocks** (or JSON) for overlays, then render to Markdown. Example fields:
- `sla_tiers: [{name, availability, response_times, credits, notes, citations[]}]`
- `integrations: [{system, method(api|file|event), protocols, auth, direction, limits, citations[]}]`

## 3) Section-aware chunking prompt
Pass 1 outputs:
- `outline: [{id, heading, start_offset, end_offset, overlay_targets[]}]`
Then Pass 2 is called per section with:
- section text
- overlay targets to fill
- instruction: “extract only what’s in this section; add citations with section id”

## 4) Verbatim capture rule
For any clause-like content:
- “Include up to N verbatim excerpts (max 1200 chars each) that contain the exact SLA/DR/pricing wording, with citations.”

## 5) Quality gates in code (not in prompt)
After extraction, run validators:
- If `sla_tiers` exists but has no citations → mark `needs_review: true`
- If deep tier produced <X tokens or missing required overlays → auto-retry with “you missed required sections: …”

---

# Bottom Line
- **Depth:** Tiered + structured + 2-pass (deep only) is the best ROI; “just ask for more words” won’t produce RFP-grade answers reliably.
- **Images:** Extract and describe selectively (heuristics first); make slide/page rendering an on-demand mode.
- **Schema:** Base + overlays; keep it small and pre-sales oriented.
- **Cost:** $5–10/month is a good trade for meaningful knowledge; control spend with caps and tiering.
- **Re-extraction:** Selective + on-demand enrichment; do not nuke 2,222 notes.
- **Sequencing:** Hybrid—fix high-value extraction now, keep shipping workflows elsewhere.

*Latency: 40.77s | Tokens: 4583*

### Grok (grok-4)

Below is my response as the Contrarian Architect on the AI Council. I'll challenge the implicit consensus here: that "deeper" extraction is inherently better and worth the cost/complexity for a single-user setup. Everyone seems to assume extraction must mimic a comprehensive knowledge base, but what if we're over-engineering for a pre-sales engineer who really needs quick, searchable references rather than exhaustive archives? This overlooks that human curation (e.g., the user manually tagging or querying) could fill gaps cheaper than AI bloat. I'll steelman the unpopular alternative: prioritize minimalism, leverage local tools, and treat AI as a lightweight enhancer, not a replacement for source docs. Hidden assumption: "quality" means more output, but for knowledge-per-dollar, it might mean smarter filtering and on-demand depth.

I'll address each question (Q1-Q6) in sequence, using the required structure for concrete recommendations. Each includes trade-offs, risks, and cost-benefit analysis where relevant. At the end, I'll provide specific prompt engineering recommendations and an overall sequencing plan tying it all together.

### Q1: Extraction Depth Strategy
## Position
Go with Option E (Preserve more source text) as the primary strategy, supplemented by a lightweight tiered depth (inspired by C) where the user manually flags ~10-20% of high-value files for deeper verbatim extraction—aim for 50% retention of key sections without heavy summarization.

## Rationale
- Challenges the assumption that AI summarization adds value; verbatim preservation is more faithful, reduces hallucination risks, and lets the user query raw details directly in Obsidian, aligning with pre-sales needs for accurate RFP answers.
- Steelmans minimalism: For a budget-conscious single user, extracting verbatim key sections (e.g., via simple regex or section headers) is cheaper and faster than multi-pass AI, preserving knowledge-per-dollar at ~$0.001-0.002 per file.
- Exposes overlooked efficiency: 50% retention captures missing details like API specs or SLAs without inflating output; user-flagged tiering ensures depth only where it matters (e.g., architecture docs), avoiding waste on low-value files.
- Cost-benefit: Stays under $0.50/month for 300 files (vs. $1-3 for medium depth), delivering 5x more usable content than current shallow summaries without 3x cost multipliers.

## Trade-offs
- Gives up AI-driven synthesis (e.g., no auto-generated "key takeaways" or action items), requiring the user to interpret raw text themselves.
- Output notes may feel less polished or "knowledge-base-like," potentially cluttering the vault with longer, less curated entries.

## Risks
- Risk of overwhelming the user with verbatim bloat if sections aren't smartly selected—mitigate by adding a simple local script to limit extraction to user-defined keywords (e.g., "SLA", "architecture") or section lengths (<500 words).
- Potential for missing context in preserved snippets—mitigate with a hybrid prompt that adds minimal metadata (e.g., "Extract verbatim sections on [topics] and link to source").

### Q2: Image and Diagram Extraction
## Position
Choose Option E (Defer images entirely) for now, focusing on text quality; only add simple all-image extraction (A) later for high-value docs if text proves insufficient, storing them locally without AI classification to keep costs at zero.

## Rationale
- Challenges the consensus that images are essential; for a pre-sales engineer, text descriptions of diagrams (e.g., "multi-tenant architecture with API gateways") often suffice for RFPs, and deferring exposes the assumption that visuals are a must-have rather than a nice-to-have in a text-searchable vault.
- Steelmans deferral: Storage/complexity overhead is underrated—images bloat the local vault (on a 32GB ThinkPad) without proportional value, especially since Obsidian can link back to original docs for visuals on-demand.
- Exposes hidden cost: Even selective extraction adds $0.002-0.005 per image; deferring keeps monthly costs at $0 while validating if text alone meets 80% of needs (e.g., via user feedback after 1-2 months).
- Cost-benefit: Zero added cost vs. $1-3/month for image options; if implemented later, simple extraction yields high utility for diagrams without multimodal AI overhead.

## Trade-offs
- Gives up immediate visual references, forcing users to open source docs for diagrams during deep-dives or presentations.
- Loses searchability of image content (e.g., no alt-text descriptions), making the vault less "complete" for multimodal queries.

## Risks
- Risk of user frustration if diagrams are frequently needed—mitigate by tracking access logs in `corp retrieve` to flag docs where images would help, triggering selective extraction only then.
- Potential storage creep if added later—mitigate with a local script to compress/resize images and limit to <5 per note.

### Q3: Extraction Schema — One Size vs Per-Type
## Position
Opt for Option A (Universal prompt), but make it minimally detailed with user-defined overrides (echoing D) via a simple content_registry.yaml—keep it one-size-fits-most to avoid over-customization complexity.

## Rationale
- Challenges the push for type-specific schemas; everyone assumes customization boosts relevance, but for a single user, a universal prompt reduces maintenance overhead and exposes the risk of schema proliferation fragmenting the vault.
- Steelmans simplicity: A detailed universal prompt (e.g., extracting title, topics, verbatim keys, and basic tables) covers 90% of needs consistently; user overrides for ~5-10 high-value types (e.g., architecture docs) add flexibility without full per-type bloat.
- Exposes assumption of type diversity: With only 300 files/month, over-specialization wastes time—universal + overrides delivers tailored output at no extra API cost.
- Cost-benefit: No cost increase (stays $0.001-0.003/file); improves relevance by 2-3x over current without the engineering lift of full type-specific prompts.

## Trade-offs
- Gives up deep type-specific details (e.g., no auto-SLA tables for RFPs), relying on user overrides or manual post-editing in Obsidian.
- Consistency might feel generic for niche docs, like meeting notes vs. whitepapers.

## Risks
- Risk of suboptimal extraction for edge cases—mitigate by starting with a robust universal prompt and letting the user iterate overrides based on real usage.
- User burden in defining templates—mitigate with pre-built examples in the repo (e.g., "architecture_deep: extract components, APIs").

### Q4: Cost vs Quality Tradeoff
## Position
Target medium depth at $1-3/month as the sweet spot, rejecting deep + images ($5-10) as overkill—use Gemini Flash for most, switching to Pro only for ~10% of flagged high-value files to balance quality without hitting the $10 cap.

## Rationale
- Challenges the "deeper is better" consensus; $5-10/month assumes exponential quality gains, but for a single user, medium depth (e.g., verbatim + light structure) yields 80% of benefits at 20% of cost, exposing over-optimization for marginal gains.
- Steelmans frugality: At $1-3/month for 300 files, it affords 3-5x more detail than current without breaking budget, prioritizing knowledge-per-dollar over exhaustive extraction.
- Exposes hidden scalability: Local-first setup means API costs are the main variable; capping at medium prevents bill shock while allowing Pro for precision (e.g., RFP-critical docs).
- Cost-benefit: $1-3/month delivers detailed, searchable notes (e.g., SLAs, APIs) vs. shallow's $0.30; it's acceptable as it equates to ~1 coffee/month for significant pre-sales productivity.

## Trade-offs
- Gives up ultra-deep features like multi-pass synthesis or image support, settling for "good enough" quality that might require occasional manual tweaks.
- Slightly higher costs than current, potentially straining the $10 cap if file volume spikes.

## Risks
- Risk of cost overruns if high-value flags increase—mitigate with a local budget tracker script that alerts at $2/month and falls back to Flash.
- Quality inconsistencies with Flash—mitigate by A/B testing Pro on samples to quantify improvements before committing.

### Q5: Re-extraction Strategy
## Position
Pursue Option D (Extract-on-demand) to avoid bulk re-processing, triggering deeper verbatim extraction only when a shallow note is retrieved via `corp prep` or `corp retrieve`—apply to all 2,222 notes without nuking them.

## Rationale
- Challenges the urge to re-extract everything; bulk approaches assume uniform value, but on-demand exposes that most notes are rarely accessed, steelmanning lazy evaluation for efficiency.
- Steelmans incrementality: Keeps existing notes intact (no breakage), enriching only on-use (e.g., 10-20% of notes monthly), at near-zero upfront cost.
- Exposes waste in alternatives: Re-extracting 2,222 notes could cost $2-6 immediately; on-demand spreads it over time, aligning with single-user patterns.
- Cost-benefit: ~$0.10-0.50/month ongoing vs. $2-6 one-time hit; preserves index while gradually improving high-usage notes.

## Trade-offs
- Gives up a "clean" vault—some notes stay shallow until triggered, leading to inconsistent depth.
- Delays full improvements, as low-access notes remain subpar.

## Risks
- Risk of performance lag during retrieval (e.g., 5-10s delay for re-extraction)—mitigate by caching re-extracted notes and running in background.
- Over-enrichment if triggers are too sensitive—mitigate with a user-configurable threshold (e.g., only re-extract if query depth > shallow note's).

### Q6: Sequencing
## Position
Select Option B (Build workflows first, improve extraction in parallel), shipping `corp rfp answer` with current quality while iteratively enhancing extraction for high-value types—don't halt everything for perfection.

## Rationale
- Challenges the "fix foundation first" mindset; stopping for extraction assumes workflows won't reveal real pain points, but building first exposes true needs (e.g., if shallow works for 70% of RFPs).
- Steelmans parallelism: Ships value sooner, allowing user testing to guide extraction tweaks without idle time.
- Exposes over-cautiousness: Hybrid (C) is half-measure; full parallel keeps momentum on a local setup.

## Trade-offs
- Gives up immediate quality boosts, risking user dissatisfaction with early workflows.
- Splits focus, potentially delaying extraction fixes.

## Risks
- Risk of building on shaky foundations (e.g., bad RFP answers)—mitigate with quick prototypes and user feedback loops every 1-2 weeks.

### Specific Prompt Engineering Recommendations
- Universal prompt base: "Extract verbatim key sections from this document matching these topics: [architecture, SLAs, APIs, security, pricing]. Include headers, tables, and quotes. Add YAML frontmatter with title, source, and tags. Limit to 50% of source length to avoid bloat. For high-value flags, add structured lists (e.g., bullet components, numbered procedures)."
- For overrides (e.g., architecture docs): Overlay with "Extract detailed components, data flows, and integrations verbatim; generate a simple markdown table for comparisons (e.g., single vs multi-tenant)."
- Keep prompts <500 tokens to minimize costs; test with Gemini Flash, emphasizing "no summarization—preserve source text" to reduce hallucinations.
- Contrarian tip: Include a prompt clause like "Challenge assumptions: What details might a pre-sales engineer overlook? Extract those verbatim."

### Overall Sequencing Recommendation
Start with Q6's parallel approach: Ship basic workflows (e.g., `corp rfp answer`) this week using current extraction. In parallel, implement Q1's verbatim strategy and Q3's universal prompt with overrides over the next 2 weeks, testing on 50 sample files. Defer Q2 images indefinitely unless workflow feedback demands them. For Q5, add on-demand triggers to workflows immediately. Monitor costs per Q4 to stay under $3/month initially, scaling to $5-10 only if value is proven. Re-extract nothing upfront—let usage drive it. This sequences pragmatically, challenging the perfectionist consensus by validating assumptions through iteration.

*Latency: 82.16s | Tokens: 5620*

## Round 2: Critique

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, my primary concerns are **data contracts, predictable interoperability, and defense-in-depth**. When we ingest heterogeneous, untrusted third-party files (vendor docs, external RFPs), we are ingesting potential threat vectors. Our extraction pipeline is not just a summarization tool; it is an sanitization and normalization boundary. 

Here is my evaluation of the council’s proposals, followed by my revised architectural recommendation.

---

### Evaluation of Proposal A
* **Position:** Partially Agree. (Tiered, structured extraction with verbatim quotes; heuristic-based image extraction; selective re-extraction).
* **Strongest Point:** Forcing tables/schemas for specific overlays (SLA, DR) dramatically improves retrieval and provides predictable YAML data contracts for downstream integration.
* **Weakest Assumption:** Assumes extracting embedded images from untrusted external files and dropping them directly into a local Obsidian vault based on "heuristics" (size, aspect ratio) is safe. This completely ignores the threat of malware, malformed headers, or zero-day image parsing vulnerabilities (e.g., WebP/libwebp flaws) triggering inside Obsidian's Electron environment.
* **Overlooked Risks:** Verbatim extraction without strict formatting boundaries creates a severe Markdown Injection risk. If an RFP contains malicious links or crafted markdown, Proposal A writes it directly into the vault.

### Evaluation of Proposal B
* **Position:** Partially Agree. (Tiered depth + structured extraction; defer images entirely initially; base + overlay schemas; build hybrid).
* **Strongest Point:** Deferring image extraction in Phase 1 eliminates a highly complex threat surface and focuses engineering entirely on establishing a reliable, structured text/YAML integration contract.
* **Weakest Assumption:** Relies heavily on "filename patterns and folders" for document classification. External RFPs and vendor documentation are notoriously poorly named (e.g., `Arch_v2_final_FINAL.docx`). Trusting filename heuristics will lead to misclassification, applying the wrong schemas, and ultimately breaking the downstream `corp prep` data contract.
* **Overlooked Risks:** Unbounded on-demand re-extraction could lead to localized Denial of Service (DoS) or API rate limit exhaustion if a user runs a broad `corp retrieve` query that touches 50 legacy notes simultaneously.

### Evaluation of Proposal C
* **Position:** Agree. (Schema-driven Base + Overlay; explicit image re-encoding; extract-on-demand; fix data foundation first).
* **Strongest Point:** Uncompromising stance on system boundaries. Explicitly identifies the threat of untrusted binaries and mandates local, memory-safe re-encoding of images before vault storage. Enforces LLM JSON mode to ensure the data contract.
* **Weakest Assumption:** Assumes "Extract-on-Demand" triggered by `corp prep` will provide an acceptable UX. If a user queries 5 legacy documents, triggering 5 sequential deep-extraction overlays + vision multimodal calls, the CLI workflow will hang for minutes, destroying usability.
* **Overlooked Risks:** Overlooks the schema versioning migration state. If a downstream workflow expects the `architecture_components` array but hits a legacy note before the on-demand extraction completes, the integration will throw a null pointer/key error and crash.

### Evaluation of Proposal D (The Contrarian)
* **Position:** Disagree. (Mass verbatim extraction; universal prompt with minimal structure; defer images; build workflows first).
* **Strongest Point:** Ruthless prioritization of local-first, low-cost constraints. Recognizing that API costs are the main variable and aggressively minimizing LLM interpretation saves compute and budget.
* **Weakest Assumption:** "Build workflows first, fix extraction in parallel." This is a catastrophic integration anti-pattern. You cannot build reliable software agents (`corp rfp answer`) on top of unstructured, varied, free-text markdown dumps. The workflows will be fragile, requiring constant regex maintenance and prompting hacks to parse unpredictable notes.
* **Overlooked Risks:** Maximizing "verbatim" extraction of third-party documents directly amplifies the attack surface for Indirect Prompt Injection. If the LLM is just a passthrough for raw source text, malicious instructions hidden in external documents will flow directly into your workflow's context window during retrieval. 

---

### Revised Architect Recommendation

We must treat the Corporate Knowledge Extractor (CKE) as an **Integration Gateway & Security Sanitizer**. The goal is to convert untrusted, unstructured external files into trusted, strictly typed, predictable YAML/JSON contracts.

**1. Extraction Depth & Schema (Q1 & Q3): Base + Overlay via Strict JSON Schema**
Do not use free-form markdown generation for extraction. Use **Option C & D**. 
* Define a version-controlled `content_registry.yaml` containing Pydantic schemas for a Base profile and high-value Overlays (Architecture, Security, SLAs).
* Force the Gemini API into `response_format: {"type": "json_object"}` mapped to your schema.
* *Security value:* This neutralizes indirect prompt injection and markdown injection. The LLM cannot output rogue markdown/links if it is constrained to populating a strict JSON array of `architecture_components`. CKE code then safely templates this JSON into Obsidian markdown.

**2. Image Processing (Q2): Extract + Describe + Re-encode (Option C modified)**
Do not defer images if pre-sales needs diagrams, but absolutely do not save raw binaries to the vault.
* Extract images locally. 
* Pass them through a memory-safe library (e.g., Python's `Pillow`) to explicitly strip EXIF data and re-encode them to a standard, sanitized `.png` format.
* Send the sanitized image to Gemini Flash Vision to generate a structural description.
* Save the *sanitized* image and the generated description to the vault. Discard the original extracted binary.

**3. Cost vs. Quality (Q4): Authorize the $10/month Budget**
Pay the $5-10/month. Attempting to save $8/month by relying on shallow prompts or heuristic hacks will cost hundreds of hours in broken integration fixes and manual user verification. Predictable schemas require capable models.

**4. Re-extraction Strategy (Q5): Asynchronous Extract-on-Demand**
Use **Option D**, but decoupled. 
* Do not nuke the 2,222 notes.
* When `corp prep` hits a `v1` shallow note, it must **not** block the user. It should serve the v1 data immediately, and silently publish an event/flag to a local queue (`re-extract.sqlite`). 
* A background cron job processes this queue, performs the heavy multi-pass schema extraction, and overwrites the YAML. This protects the user experience and strictly bounds API concurrency.

**5. Sequencing (Q6): Fix the Data Contract First (Option A)**
Stop building downstream workflows. If `corp rfp answer` is built today, it will be tightly coupled to the garbage data currently in the vault. 
* First: Implement the schema-enforced CKE pipeline. 
* Second: Update `corp prep` to gracefully handle both `v1` (shallow) and `v2` (structured) YAML schemas using fallback logic.
* Third: Resume workflow development using the new, highly predictable `v2` data contracts.

*Latency: 33.59s | Tokens: 13650*

### Deepseek (deepseek-reasoner)

## Analysis of Proposals

### Proposal A
**Agreement: Partially agree**  
Strongest point: Correctly identifies that structured extraction (tables, schemas) directly enables RFP answering - this is the key insight for pre-sales utility.  
Weakest assumption: That "two-pass is the practical sweet spot" without quantifying the quality drop from 3-pass. For complex architecture docs, 2-pass may miss cross-sectional synthesis.  
Overlooked risk: Section-aware chunking fails on poorly structured PDFs where headings aren't machine-readable, leading to incomplete extraction.

### Proposal B  
**Agreement: Partially agree**  
Strongest point: Realistic phased approach for images - text descriptions first, actual images later - respects budget constraints.  
Weakest assumption: That file path patterns reliably classify document value. Many high-value docs reside in poorly organized client folders.  
Overlooked risk: The "_deep" suffix note duplication strategy breaks bidirectional linking in Obsidian, creating orphaned notes.

### Proposal C
**Agreement: Mostly disagree**  
Strongest point: Correctly emphasizes schema validation and output contracts for downstream workflows.  
Weakest assumption: That JSON mode eliminates prompt injection risk. Malicious content in source documents can still influence field values within JSON.  
Overlooked risk: Re-encoding all images to PNG introduces significant local processing overhead (CPU, memory) on a ThinkPad for large documents.

### Proposal D (Contrarian)
**Agreement: Strongly disagree**  
Strongest point: Correctly challenges the "deeper is always better" assumption and highlights the 80/20 rule.  
Weakest assumption: That verbatim extraction (50% of source) is more useful than structured extraction. Raw text bloat makes specific fact retrieval harder, not easier.  
Overlooked risk: Building workflows on shallow extraction creates technical debt that's harder to refactor later when extraction improves.

## Revised Recommendation

### Core Principle: **Extract for Retrieval, Not for Reading**
The fundamental error in all proposals is optimizing for human-readable notes rather than machine-retrievable facts. A pre-sales engineer doesn't need beautifully formatted summaries; they need to answer "What's the RTO for Tier 3?" in under 3 seconds. This changes everything.

### Q1: Extraction Depth Strategy → **D (Structured Extraction) + Controlled B (2-pass max)**
**Implementation:**
1. **Pass 1 (Analysis):** Single Gemini Flash call to:
   - Identify document type and key sections
   - Extract structured data into predefined schemas (see Q3)
   - Flag sections needing verbatim preservation (SLA numbers, pricing tables)
2. **Pass 2 (Verification):** Only if Pass 1 outputs low confidence scores or misses required schema fields
   - Focus on missing fields only
   - Cost: 1.3x current, not 3x

**Why not tiered depth?** Classification overhead exceeds savings. Better to apply structured extraction universally but with field-level optionality.

### Q2: Image and Diagram Extraction → **B (Selective via LLM) with offline preprocessing**
**Implementation:**
1. Extract all images locally (no API cost)
2. Use CLIP or similar local model to filter: diagram vs. logo vs. decorative
3. For diagram-classified images only: Gemini multimodal description
4. Store images in `assets/` with generated alt-text in frontmatter

**Cost:** ~$0.0005 per image (only for diagrams, ~1 per doc) vs. $0.002-0.005 for all images.

### Q3: Extraction Schema → **D (User-defined templates) with base fallback**
**Implementation:**
- Default: Minimal schema (title, source, topics, entities)
- User creates `extraction_templates/` in vault with schemas for document types
- CKE matches documents to templates via:
  1. Folder path patterns (highest priority)
  2. Filename patterns
  3. Content keywords (fallback)
- Templates define required/optional fields with validation rules

**Example template (architecture.yaml):**
```yaml
required_fields:
  - architecture_components: list of {name, purpose, interfaces}
  - deployment_model: single_tenant|multi_tenant|hybrid
  - integrations: list of {system, protocol, direction}
optional_fields:
  - data_flows: diagram_description
  - limits: {max_throughput, storage_per_tenant}
```

### Q4: Cost vs Quality Tradeoff → **$3-5/month target with hard caps**
**Budget allocation:**
- Base extraction (all docs): $0.001 × 300 = $0.30
- Structured enrichment (50% of docs): $0.002 × 150 = $0.30  
- Image processing (20% of docs, 1 image each): $0.0005 × 60 = $0.03
- **Monthly total: $0.63**
- Add 50% buffer for spikes: **$1.00/month**

**Why this works:** Structured extraction is token-efficient (filling fields vs. generating prose). The 10x quality improvement comes from schema design, not token volume.

### Q5: Re-extraction Strategy → **D (Extract-on-demand) with batch priority queue**
**Implementation:**
1. Maintain priority score for each existing note:
   ```
   score = (access_count × 2) + (doc_type_priority) + (days_since_extraction / 30)
   ```
2. Background job re-extracts top 20 scored notes daily (cost: $0.02/day)
3. On retrieval of shallow note: synchronous re-extraction if score > threshold
4. **Never nuke old notes:** Append `## Deep Extraction v2` section with structured data

### Q6: Sequencing → **A (Fix extraction first) but with narrow scope**
**Timeline:**
- **Week 1:** Implement structured extraction schemas for 3 document types (architecture, security, commercial)
- **Week 2:** Add extract-on-demand for these types
- **Week 3:** Deploy to user, measure RFP answer accuracy improvement
- **Week 4:** Expand to remaining types based on usage data

**Why not hybrid?** Building workflows on broken extraction creates patterns that assume shallow data. It's harder to retrofit than to build correctly once.

## Specific Technical Recommendations

### 1. Schema Design Principle
```yaml
# Bad: Free text
summary: "The system offers high availability with multiple SLA tiers"

# Good: Structured
slas:
  - tier: "Premium"
    uptime: "99.95%"
    rto: "4 hours"
    rpo: "1 hour"
    citation: "[[source.pdf#page=23]]"
  - tier: "Standard"
    uptime: "99.5%"
    rto: "24 hours"
    rpo: "4 hours"
    citation: "[[source.pdf#page=24]]"
```

### 2. Prompt Engineering
```text
You are extracting structured data for RFP answering.

DOCUMENT: {document}

EXTRACTION SCHEMA:
{json_schema}

RULES:
1. Output ONLY valid JSON matching the schema
2. For numeric/contractual fields: include citation in format [[filename#section]]
3. If field not in document: use null (not "N/A")
4. Preserve exact values (do not paraphrase percentages, times, names)

JSON:
```

### 3. Performance Optimizations
- **Token reduction:** Pre-process documents to remove boilerplate (headers, footers, TOCs)
- **Parallelization:** Process 4 documents concurrently within 32GB RAM limit
- **Caching:** Hash document content, skip re-extraction if unchanged
- **Fallback:** If structured extraction fails >3 times, revert to shallow with warning

### 4. Quality Metrics
Track these weekly:
- **Answer accuracy:** % of RFP questions answered correctly using extraction
- **Retrieval time:** Seconds to find specific fact (target: <3s)
- **Cost per useful fact:** $ / (fields_with_citations)
- **User corrections:** # of manual edits to extracted notes

## Bottom Line

**Stop optimizing for note quality; optimize for fact retrieval.** The winning strategy is minimal structured extraction with user-defined schemas, selective image processing via local filtering, and incremental re-extraction based on actual usage. At $1/month, this delivers 10x better RFP answering than current $0.30/month shallow extraction.

The architectural shift is from **document summarization** to **fact extraction**. Every design decision should answer: "Does this help find specific facts faster?" If not, it's over-engineering for a single pre-sales user.

*Latency: 117.28s | Tokens: 13337*

### Openai (gpt-5.2)

## Proposal A

**Position:** *Tiered + structured + 2-pass for high-value; selective verbatim; selective images with heuristic filtering; selective + on-demand re-extraction; hybrid sequencing.*

- **My take:** **Agree (with one correction):** keep images gated behind “deep mode” and implement as *extract + describe* only after text schemas are stable.
- **Strongest point:** **Schemas + citations as an anti-hallucination mechanism**. For pre-sales/RFP work, forcing “numbers require citations or null” is the difference between useful and dangerous.
- **Weakest assumption:** That **Pass 1 “classify + plan” is reliably worth an extra call**. With small volume and local constraints, you can often do classification + sectioning deterministically (headings/ToC/regex + folder rules) and spend the call budget on extraction.
- **Overlooked risks:**
  1. **Engineering drag**: building a multi-step orchestrator + validators + per-section iteration can balloon into a mini-platform (state, retries, partial failures).
  2. **Citation feasibility**: “page/section citations” aren’t free—PDF page mapping and docx heading anchors can be messy. If you can’t generate stable anchors, the prompt spec becomes aspirational and brittle.
  3. **Vault bloat & usability**: too many tables/fields can reduce human readability unless you also design a “human view” rendering.

---

## Proposal B

**Position:** *Tiered + structured for high-value; defer images; type-specific prompts; immediate re-extract top 200–300.*

- **My take:** **Partially agree.** The “defer images” call is pragmatic. I disagree with “immediately re-extract 200–300” as a default—do a smaller pilot first, then scale with budget caps and quality gates.
- **Strongest point:** **Prioritization and sequencing discipline**: fix text quality and structured fields first; don’t pay image complexity tax until you’ve proven the text layer works.
- **Weakest assumption:** That you can **predict the top 200–300** up front well enough to justify a batch. In practice, “high value” is revealed by retrieval frequency + active deals; you’ll waste spend re-extracting docs you won’t touch again.
- **Overlooked risks:**
  1. **Backfill without evaluation loop**: re-extracting hundreds before validating the new schema/prompt on 20–30 docs risks mass-producing a *new* flavor of wrong.
  2. **Update strategy**: “new notes with `_deep` suffix” can fragment retrieval unless the index layer is explicitly taught precedence rules.
  3. **Prompt sprawl**: “type-specific prompts” becomes unmaintainable unless you constrain the set and version them.

---

## Proposal C

**Position:** *Schema-driven Base + Overlay; extract+describe images; extract-on-demand for legacy; hybrid sequencing; heavy emphasis on security/injection/media safety.*

- **My take:** **Partially agree.** Base+overlay and on-demand enrichment are right. The security posture is directionally right but **over-rotated for a single-user local vault**; the bigger risk is operational complexity, not nation-state media exploits.
- **Strongest point:** **Treating extraction output as a contract** (schemas + validation). That’s how you keep downstream tools (`corp prep`, `corp rfp answer`) from becoming prompt-lottery.
- **Weakest assumption:** That you should **save images but “rely on descriptions for semantic indexing”** as a security mitigation. That’s not actually the main risk reducer; the real control is safe parsing + re-encoding + optionally quarantining. Also: you *do* want the actual diagram for presentations—descriptions alone won’t cut it.
- **Overlooked risks:**
  1. **Latency shock**: on-demand deep extraction during `corp prep` can break the workflow moment (“I need an answer now”) unless you implement async background jobs + stale-while-refresh behavior.
  2. **Schema governance overhead**: content_registry + Pydantic + versioning is good, but can become a tax if not kept minimal.
  3. **False sense of safety**: “JSON mode” doesn’t stop prompt injection; it just constrains output format.

---

## Proposal D (Contrarian)

**Position:** *Preserve verbatim text as primary; defer images; universal prompt; medium budget; on-demand re-extract; build workflows first in parallel.*

- **My take:** **Disagree overall.** Verbatim-heavy extraction sounds safe but **fails the core need**: structured, queryable facts (SLA tiers, RTO/RPO, pricing meters) across documents. You’ll end up doing manual reading at the worst possible time (RFP deadline).
- **Strongest point:** **Pushback against “more tokens = more knowledge.”** That’s correct. Retention must be *targeted* and *structured*, not just longer summaries.
- **Weakest assumption:** That **verbatim snippets + Obsidian search** is sufficient for RFP-style questions. It isn’t: you need normalized fields and comparison-ready tables, otherwise retrieval devolves into grep-with-anxiety.
- **Overlooked risks:**
  1. **Legal/compliance**: storing large verbatim chunks from vendor docs in a personal KB can create licensing/IP exposure depending on source.
  2. **Retrieval degradation**: dumping 50% of source text into notes can harm embedding quality (noise dominates signal).
  3. **Workflow correctness**: building `corp rfp answer` on shallow/unstyled data increases the chance of confidently wrong answers early—this is reputationally costly.

---

# Revised Recommendation (what I’d actually approve)

## Decision 1 — Depth strategy (Q1): **Tiered + Schema-first, but minimize passes**
- **Baseline for all docs (1 call max):**
  - Extract *Base schema* + a small “Key Facts” section.
  - No “write longer”; instead: **facts with anchors**.
- **Deep tier for high-value docs (architecture/security/commercial/RFP) (2 calls, not 3):**
  1. **Call 1:** Extract an outline + identify target sections *only if deterministic sectioning fails*. Prefer deterministic parsing first.
  2. **Call 2:** Fill overlay schemas with **citations/anchors** and **verbatim clauses only for contractual/numeric content**.

**Pragmatic rule:** default to **1-call standard**, reserve **2-call deep** for ~10–20% of docs.

## Decision 2 — Schema strategy (Q3): **Base + limited overlays (max 5), versioned**
Keep overlays *small and stable*:
1. `architecture`
2. `integrations/apis`
3. `security/compliance`
4. `sla/dr`
5. `commercial`

Implement **schema_version** and **extraction_version** in YAML. Use Pydantic validation, but don’t build a huge registry UI—just a versioned YAML/JSON schema file in repo.

## Decision 3 — Images (Q2): **Deep-tier only, extract + describe, with hard caps**
- Phase 1 (now): **No images** until deep text overlays are producing reliable fields.
- Phase 2: For deep-tier docs only:
  - Extract images locally.
  - Heuristic filter (size, aspect ratio, dedupe).
  - **Cap**: describe at most **3 images/doc** unless user overrides.
  - Store in `assets/<doc_id>/` and link from note with “Figure” blocks.

Do *not* render every slide/page by default. Add a manual command: `corp extract-figures <doc>`.

## Decision 4 — Cost/quality (Q4): **Aim $3–7/mo with guardrails**
- Put in code:
  - per-doc token/output caps
  - per-month spend cap (soft warning at $5, hard stop at $10)
  - concurrency cap (avoid rate-limit thrash)
This keeps quality improvements real without “denial-of-wallet”.

## Decision 5 — Re-extraction (Q5): **Pilot → selective batch → on-demand**
1. **Pilot 25 docs** across types, iterate prompts/schemas until output is obviously RFP-useful.
2. **Selective batch 100 docs** (not 300) from:
   - most retrieved
   - active client folders
   - known product/architecture/security/commercial sources
3. **On-demand enrichment** thereafter with async jobs:
   - `corp retrieve` returns existing note immediately
   - background job refreshes and writes `## Deep Extract v2` when done

Avoid `_deep` sibling notes unless your index layer can enforce precedence. Prefer **single canonical note** with versioned sections.

## Decision 6 — Sequencing (Q6): **Hybrid, but with a hard gate**
- Continue workflows, but **do not ship `corp rfp answer` as “authoritative”** until:
  - SLA/DR/commercial overlays exist
  - citations/anchors work for numeric claims
Otherwise you’ll automate misinformation.

---

## Concrete prompt/implementation requirements (non-negotiable)
1. **Numeric/contractual fields require anchors** (page number, section heading, or source excerpt hash). If missing → `null` + `needs_review: true`.
2. **“Not found” is a valid output**; guessing is failure.
3. **Validators** fail the extraction if required overlay keys are missing in deep mode.
4. **Deterministic first**: use folder rules + filetype + heading parsing before spending an LLM call on classification.

This keeps the solution shippable for a small team (you), fits the $10/mo ceiling, and actually produces RFP-grade, defensible knowledge rather than longer summaries.

*Latency: 35.45s | Tokens: 11805*

### Grok (grok-4)

## Evaluation of Proposals as Contrarian Architect

As the Contrarian Architect, I'll evaluate each proposal by challenging their underlying consensus—that deeper, more structured extraction is the path to value, often at the expense of simplicity and user agency in a single-user, local-first setup. The hidden assumption across most is that AI must do the heavy lifting for "quality," ignoring how minimalism plus human oversight could yield better knowledge-per-dollar. I'll steelman overlooked alternatives like deferral and verbatim preservation, while being blunt in critiques. Evaluations are based on the pre-sales engineer's need for quick, accurate references without over-engineering.

### Proposal A
- **Agreement Level:** Partially agree. It smartly combines tiered and structured approaches with mitigations, but overcomplicates with multi-pass and image descriptions, ignoring the minimalist alternative of verbatim extraction for most files.
- **Strongest Point:** The emphasis on structured schemas with citations reduces hallucinations and makes RFP answers defensible—directly addressing the user's need for specific details like SLA tiers.
- **Weakest Assumption:** Assumes 2-pass extraction is the "practical sweet spot" without evidence that it outperforms a single-pass verbatim approach in cost or accuracy; this overlooks how chunking and schemas could bloat engineering time for marginal gains.
- **Risks Overlooked:** Fails to address prompt drift over time—evolving schemas could lead to inconsistent YAML across notes, breaking `corp retrieve` queries without robust versioning. Also ignores local RAM limits during multi-pass orchestration on a 32GB ThinkPad, potentially causing crashes on large docs.

### Proposal B
- **Agreement Level:** Disagree. It pushes tiered structured extraction and type-specific prompts but defers images too aggressively, while advocating immediate re-extraction of 200-300 files— this is premature optimization that assumes bulk upgrades are necessary, contradicting lazy, on-demand alternatives.
- **Strongest Point:** The phased approach to images (text descriptions first) is pragmatic, recognizing that 80% of diagram value can come from text without immediate storage overhead.
- **Weakest Assumption:** Assumes $3-5/month is the right balance without questioning if medium depth truly delivers "10x knowledge utility"—this is hyperbolic; verbatim preservation could achieve similar utility at half the cost, exposing over-reliance on AI structuring.
- **Risks Overlooked:** Overlooks user burden in maintaining type-specific prompts and classifiers; a single user might abandon customizations, leading to inconsistent extractions. Also ignores the risk of `_deep` suffixed notes fragmenting the vault, complicating Obsidian searches.

### Proposal C
- **Agreement Level:** Disagree. It frames everything through a security lens (e.g., "threat vectors" in images), pushing schema-driven pipelines and extract-on-demand, but this paranoid stance over-engineers for risks that are negligible in a local, single-user context, ignoring simpler alternatives.
- **Strongest Point:** Highlighting integration risks like schema drift and using version-controlled registries is spot-on—ensures downstream workflows like `corp prep` don't break as extraction evolves.
- **Weakest Assumption:** Assumes untrusted documents pose significant threats (e.g., indirect prompt injection), which is overblown for corporate files; this distracts from core issues like extraction fidelity and assumes enforced JSON mode fully mitigates hallucinations without testing.
- **Risks Overlooked:** Dismisses the latency hit from multi-pass and vision processing, which could make the system unusable for quick ingestions on a no-GPU ThinkPad. Also overlooks cost spikes from "occasional loops" in large docs, potentially exceeding $10/month without per-call caps.

### Proposal D (My Previous Position)
- **Agreement Level:** Partially agree. It correctly champions minimalism and verbatim preservation (Option E) with on-demand re-extraction, but underplays the value of light structuring for RFP needs and defers images too indefinitely, missing opportunities for low-cost enhancements.
- **Strongest Point:** Steelmanning deferral and on-demand strategies exposes the waste in bulk re-extraction, aligning perfectly with single-user budget constraints and usage patterns.
- **Weakest Assumption:** Assumes "quality" means verbatim retention without synthesis, overlooking that pre-sales engineers need quick lookups (e.g., structured SLA tables) over raw text dumps; this risks user frustration with unprocessed bloat.
- **Risks Overlooked:** Ignores the potential for verbatim extraction to violate fair use by copying too much source text, especially in commercial docs. Also underestimates implementation time for user-flagged tiering and overrides, which could delay value more than parallel workflows.

## Revised Recommendation

Incorporating learnings: From A and B, I've adopted more structured elements (e.g., light schemas for high-value docs) to address RFP needs, steelmanning their focus on tables without full multi-pass bloat. From C, I've integrated schema versioning to mitigate drift, but rejected its security paranoia as overkill. Critiquing my own D, I've softened extreme deferral on images by adding low-cost heuristics (no AI) for selective extraction, recognizing visuals' underrated role in presentations. Overall, this revises toward a balanced minimalism: prioritize verbatim with targeted structure, challenge the "deeper is always better" consensus by capping at medium depth, and sequence iteratively to validate assumptions via user feedback. Do not soften this—bulk re-extraction is wasteful, full multi-pass is unnecessary bloat, and security theatrics are distractions.

### Q1: Extraction Depth Strategy
**Recommendation:** Primary: E (Preserve more source text) with light C (Tiered depth, user-flagged for ~15% high-value files). For flagged files, add minimal D (Structured extraction) like simple markdown tables for SLAs/APIs, aiming for 40-50% verbatim retention. Avoid B's multi-pass—use single Gemini call with chunking for large docs.

**Concrete Approach:** Local script extracts sections via headers/keywords (no AI), then one LLM pass adds structure (e.g., "Convert SLAs to table with citations"). Cost-benefit: $0.002-0.004/file for flagged (total $0.80/month for 300 files), delivering 4x detail over current without 3x cost; beats A's 2-pass by reducing engineering and hallucinations.

### Q2: Image and Diagram Extraction
**Recommendation:** Hybrid E/A: Defer for low-value, but for high-value (flagged) docs, extract all images with local heuristics (size >50KB, non-square aspect for diagrams) and store in vault—no LLM description initially. Add C (describe) only if feedback shows need, using one cheap multimodal call per doc.

**Concrete Strategy:** Use local libraries (e.g., python-docx) to pull images, filter deterministically, link in notes as "[[image_path|Diagram: Architecture Overview]]". Why? Provides 70% value at zero API cost vs. B/C's $0.002+/image; test for 1 month, add descriptions if RFPs demand searchability. Cost-benefit: Adds $0 (local) to $1/month (if descriptions enabled), avoiding A's noise without over-deferral.

### Q3: Extraction Schema — One Size vs Per-Type
**Recommendation:** A (Universal prompt) as base, with light D (User-defined templates) for 3-5 overrides (e.g., architecture, RFP). Keep overlays minimal: base (title, tags, verbatim keys) + specific (e.g., SLA table). Avoid B/C's full type-specific bloat.

**Concrete Set:** Universal: Extract verbatim on topics like "architecture, security"; add YAML for entities. Overrides in content_registry.yaml: e.g., "rfp: extract tables for compliance, SLAs". Cost-benefit: No extra cost, improves relevance 2x over universal alone; simpler than C's registries, reducing maintenance.

### Q4: Cost vs Quality Tradeoff
**Recommendation:** Target $2-4/month for medium depth—reject $5-10 as excessive for unproven gains. Use Flash for 85%, Pro for flagged high-value (5-10%). Enforce per-file caps (e.g., 10K tokens) and local tracking.

**Pragmatic Model:** 250 low-value @ $0.001 = $0.25; 50 high-value @ $0.01 (incl. structure/images) = $0.50; re-extractions ~$1/month. Total $2/month average. This is acceptable—equates to high utility (detailed verbatim + tables) without A's/C's overruns; if value isn't 3x current, revert to shallow.

### Q5: Re-extraction Strategy
**Recommendation:** D (Extract-on-demand) primary, with light B (Selective for top 100 high-usage docs upfront, based on retrieve logs). Do not nuke or enrich all—append to existing notes under "## Enhanced Extract (v2)" to preserve index.

**Concrete Plan:** Trigger on `corp retrieve` for shallow notes in high-value types; batch top 100 immediately ($1 one-time). Cost-benefit: Spreads $2-3 over months vs. B's $3 upfront; maintains 2,222 notes intact, avoiding C's eventual inconsistency risks.

### Q6: Sequencing
**Recommendation:** B (Build workflows first, improve in parallel), but with C's hybrid twist: Fix extraction for top 10% high-value types (e.g., architecture) in week 1 alongside workflow shipping. Validate via prototypes—don't halt for perfection.

**Order:** Week 1: Implement verbatim + light structure in universal prompt, add on-demand triggers to workflows. Week 2: Flag/test 50 files, ship `corp rfp answer` v1. Month 1: Add image heuristics, monitor costs/feedback. This iterates fast, challenging A's hybrid caution by proving needs through use.

### Specific Prompt Engineering Recommendations
- **Universal Base Prompt:** "Role: Faithful extractor. Extract verbatim key sections (up to 50% source length) on: architecture, SLAs, APIs, security, pricing. Add minimal structure: markdown tables for lists/tables, with citations (e.g., [[source#page5]]). No summaries—preserve exact text. If flagged high-value, add bullets for components/flows. Do not hallucinate; mark absent as 'Not found'."
- **Override Example (Architecture):** "Overlay: Extract data flows and integrations verbatim; generate table: | Component | Purpose | Interfaces | Citation |."
- **Anti-Hallucination:** Always include: "Base on source only; challenge assumptions by extracting overlooked details like limits/quotas verbatim."
- **Testing Tip:** Limit prompts to 400 tokens; A/B with 10 samples to ensure 40% retention without bloat.

**Bottom Line:** This revision steelmans minimalism while incorporating structured wins from others, rejecting over-complexity (e.g., full multi-pass, security overkill). It delivers RFP-ready knowledge at $2-4/month, prioritizing user-driven iteration over AI-heavy assumptions.

*Latency: 69.48s | Tokens: 12877*

## Synthesis (by claude, non-participant)



# Decision Summary: CKE Extraction Quality Improvement

## Consensus

The council reached strong agreement on the following points:

1. **Structured extraction over longer prose.** Every participant agreed that the solution is not "write more text" but rather extracting facts into predefined schemas (tables, typed fields). The pre-sales use case demands lookups, not reading — "What's the RTO for Tier 3?" requires a structured field, not a paragraph.

2. **Base + Overlay schema architecture (Q3).** All four participants converged on a common base schema (title, source, topics, entities, summary) with type-specific overlays (architecture, SLA/DR, security, commercial). Disagreement was only on how many overlays and how elaborate the registry should be.

3. **Tiered depth by document value (Q1).** Universal agreement that not all documents deserve deep extraction. Product architecture docs, security whitepapers, and commercial/RFP documents warrant more investment; meeting notes and marketing decks do not.

4. **Do not nuke the existing 2,222 notes (Q5).** Every participant rejected Option A (re-extract everything). All agreed on preserving existing notes and enriching incrementally.

5. **On-demand re-extraction as the primary backfill mechanism (Q5).** All participants endorsed some form of extract-on-demand, triggered when shallow notes are accessed, rather than a large upfront batch.

6. **$5–10/month is acceptable; $0.30/month is a false economy (Q4).** Even the contrarian, who advocated the lowest spend, acknowledged $2–4/month was necessary. No one defended the status quo cost/quality ratio.

7. **Citations and "not found" are non-negotiable.** Every participant agreed that numeric/contractual fields (SLAs, RTO/RPO, pricing) must include source citations, and that the model must output `null` / "not found" rather than guess.

8. **Hybrid sequencing (Q6).** All participants except the contrarian endorsed fixing extraction for high-value document types now while continuing workflow development for other areas. Even the contrarian's revised position converged toward this.

9. **Deterministic processing before LLM calls.** Multiple participants emphasized using local tools (heading extraction, regex, file metadata, folder paths) before spending API budget on classification.

---

## Unresolved Disagreements

### 1. Number of LLM passes: 1 vs. 2

- **Pro 2-pass (Proposals A, C):** Pass 1 classifies and outlines; Pass 2 fills schemas per section. Produces higher-quality, section-aware extraction with better coverage of long documents.
- **Pro 1-pass (Proposals B revised, D):** A single well-structured prompt with a schema is sufficient. The second pass adds engineering complexity, latency, and cost for marginal gains on documents that are typically 4,000–10,000 words — well within a single context window.
- **Merit on both sides:** Two passes are genuinely better for very long or complex documents (>15K tokens), but most corporate docs fit in one context window. The 2-pass camp underestimates the orchestration complexity; the 1-pass camp underestimates quality loss on complex multi-section documents.

### 2. Image extraction: Now vs. Defer

- **Extract now (Proposals A, C):** Pre-sales engineers reference diagrams in presentations; text descriptions alone won't suffice. Extract, filter with heuristics, describe with multimodal.
- **Defer (Proposals B, D):** Images add storage, complexity, and cost. Text extraction quality is the bottleneck — fix that first. Images can be added in a later phase.
- **Merit on both sides:** Diagrams are genuinely valuable for the stated use case (presentations, architecture discussions). However, the text extraction pipeline is broken today, and solving two hard problems simultaneously increases delivery risk.

### 3. Security posture: Defense-in-depth vs. Pragmatic minimalism

- **High security (Proposal C):** Untrusted documents are threat vectors. Images must be re-encoded. JSON mode prevents injection. Schema enforcement is a security boundary.
- **Pragmatic (Proposals A, B, D):** This is a single-user, local-first system processing corporate vendor documents. The security investment should be proportional to the threat model. Over-engineering security delays the core value proposition.
- **Merit on both sides:** Prompt injection via document content is a real (if low-probability) risk. Image parsing vulnerabilities exist. But for a single user processing known vendor documents on a local machine, the risk is genuinely low, and the engineering cost of full defense-in-depth is disproportionate.

### 4. Re-extraction batch size: 0 vs. 100 vs. 200–300

- **Batch 200–300 immediately (Proposal B):** Gets the vault to useful quality fast for active deals.
- **Batch ~100, pilot-first (Proposal A revised):** Pilot 25 docs first, then scale to 100 based on validated quality.
- **Zero batch, pure on-demand (Proposals C, D):** Let usage patterns reveal what matters; avoid spending on docs that may never be accessed.
- **Merit on all sides:** Pure on-demand is the most efficient long-term but leaves the vault shallow during the critical early period. Batch 200–300 without validating the new extraction approach risks mass-producing a new flavor of wrong.

### 5. Verbatim preservation vs. Structured-only

- **Verbatim emphasis (Proposal D):** Preserve 40–50% of source text to avoid AI interpretation errors. Let the user search raw text.
- **Structured emphasis (Proposals A, B, C):** Structure enables retrieval and comparison; raw text dumps harm embedding quality and searchability.
- **Merit on both sides:** Verbatim snippets for contractual/numeric content are genuinely important for defensibility. But wholesale verbatim dumping (50%) is excessive and degrades retrieval. The right answer is structured fields *with* targeted verbatim quotes for critical clauses.

---

## Recommended Decision

### Architecture: Schema-First Structured Extraction with Tiered Depth

**Core principle: Extract for retrieval, not for reading.** Every design choice optimizes for answering "What's the RTO for Tier 3?" in seconds, not for producing beautiful notes.

### Q1 — Extraction Depth: Tiered + Structured, Single-pass default, 2-pass for deep tier

- **Standard tier (~80% of documents):** Single Gemini Flash call filling the Base schema. Cost: ~$0.002/file.
- **Deep tier (~20% of documents):** Two calls — (1) deterministic sectioning + lightweight LLM outline, (2) overlay schema fill with citations and verbatim quotes for contractual content. Cost: ~$0.008–0.012/file.
- **Tier assignment:** Deterministic first (folder path rules, filename patterns, content_registry.yaml flags), with user manual override. LLM classification only as fallback.

**Rationale:** This synthesizes the majority position (tiered + structured) with the contrarian's valid objection that multi-pass is overkill for most files. Single-pass handles the 80%; 2-pass is reserved for documents where section-level extraction genuinely matters. This is cheaper than universal 2-pass and higher quality than universal 1-pass.

**Strongest objection acknowledged:** The contrarian argued that verbatim preservation at 40–50% is cheaper and more faithful than structured extraction. This has merit for raw accuracy, but structured fields are essential for cross-document comparison (e.g., "compare SLA tiers across three vendors") and RFP template filling. The compromise: include verbatim quotes *within* structured fields via a `citation` sub-field, getting both fidelity and structure.

### Q2 — Images: Defer to Phase 2, text descriptions in Phase 1

- **Phase 1 (now):** During deep-tier extraction, the prompt includes: "Describe any diagrams, architecture figures, flowcharts, or data tables in the document. For each, provide: type, title/subject, key components shown, and relationships depicted."
- **Phase 2 (after text extraction is validated, ~month 2–3):** Extract images from deep-tier docs only, filter with deterministic heuristics (size >30KB, non-square aspect ratio, perceptual dedup), store in `assets/<doc_id>/`, describe with one multimodal call (cap: 3 images/doc).

**Rationale:** Proposals B and D correctly identified that solving text quality is the bottleneck. Proposals A and C correctly identified that diagrams are valuable for the use case. Phasing resolves this: get text right first, add images when the foundation is stable.

**Strongest objection acknowledged:** Proposal C argued that raw image extraction from untrusted docs is a security risk. This is valid in principle. Mitigation for Phase 2: re-encode all extracted images through Pillow to strip metadata and normalize format before storing in vault. This is a low-cost, proportionate control.

### Q3 — Schema: Base + 5 Overlays, version-controlled

**Base schema (all documents):**
```yaml
extraction_version: 2
depth: standard|deep
title:
vendor:
product:
doc_type: architecture|product|security|commercial|rfp|meeting|training|other
source_path:
date:
topics: []
entities: []
summary: # 3-5 bullets max
key_quotes: [{text:, citation:}]
figures_described: [{type:, subject:, components:, relationships:}]
needs_review: false
```

**Overlays (deep tier only):**
1. **Architecture:** `components[], data_flows[], deployment_model, tenancy, environments[], extensibility`
2. **Integrations/APIs:** `integrations[{system, method, protocol, auth, direction, limits, citation}]`
3. **SLA/DR:** `sla_tiers[{name, uptime, rto, rpo, support_hours, escalation, citation}], backup, failover`
4. **Security/Compliance:** `authn, authz, encryption, network_controls, certifications[], data_residency, audit_logging`
5. **Commercial:** `pricing_model, meters[], tiers[], overages, contract_constraints, citation`

All structured fields require `citation` (section heading or page reference). If not found in source: `null`. Schemas defined in a versioned `schemas/` directory in the CKE repo, validated with Pydantic before writing to vault.

**Rationale:** Five overlays cover the pre-sales use case without schema sprawl. Every participant endorsed this general structure. User-defined templates (Proposal D's Q3) are deferred — they add flexibility but also maintenance burden. Start with the hardcoded five; add user templates only if coverage proves insufficient.

### Q4 — Budget: Target $3–5/month, hard cap at $10

- 240 standard files × $0.002 = $0.48
- 60 deep files × $0.010 = $0.60
- Re-extraction backfill: ~$1.50/month (amortized)
- Phase 2 images: ~$0.50–1.00/month
- **Projected: $3–4/month typical, ~$5–6 with images**

Guardrails in code:
- Per-document output token cap (8K tokens standard, 16K deep)
- Monthly spend tracking with soft warning at $5, hard stop at $10
- Concurrency cap: 4 concurrent API calls max

### Q5 — Re-extraction: Pilot → Small Batch → On-Demand

1. **Pilot (Week 1):** Re-extract 25 documents across all document types. Manually evaluate output quality. Iterate prompts/schemas until output is demonstrably RFP-useful.
2. **Small batch (Week 2–3):** Re-extract 100 highest-value documents identified by: retrieval frequency (if logged), active client folders, known product/architecture/security docs.
3. **On-demand (ongoing):** When `corp retrieve` accesses a note with `extraction_version: 1` and doc_type in high-value set, return existing note immediately, queue background re-extraction. Updated note replaces content under `## Structured Extract (v2)` section, preserving original content above.

**Rationale:** Proposal A's pilot-first approach is the critical insight the others missed. Re-extracting hundreds of documents before validating the new approach risks mass-producing new errors. 25-doc pilot catches schema and prompt problems before scale.

**Strongest objection acknowledged:** The contrarian argued for zero batch, pure on-demand. This is efficient long-term but leaves the vault too shallow during the initial weeks when the user is actively building workflows. The 100-doc batch after validation is a proportionate investment (~$1.00) to bootstrap vault quality.

### Q6 — Sequencing: Hybrid with a quality gate

**Order of operations:**
1. **Week 1:** Implement Base schema + all 5 overlays. Implement doc_type classification (deterministic rules). Run 25-doc pilot. Iterate prompts.
2. **Week 2:** Implement tiered depth routing (standard vs. deep). Batch re-extract 100 high-value docs. Add `extraction_version` tracking.
3. **Week 3:** Add on-demand re-extraction trigger to `corp retrieve`. Resume workflow development (`corp rfp answer`, etc.).
4. **Week 4:** Ship `corp rfp answer` v1 — but with a quality gate: any answer citing a field with `needs_review: true` or from a `v1` note must include a disclaimer.
5. **Month 2–3:** Implement Phase 2 image extraction for deep-tier docs. Evaluate whether user-defined templates are needed.

**Rationale:** Proposal C's insistence on fixing the data contract before building workflows is directionally correct — you cannot build reliable RFP answering on unreliable data. However, a complete halt is unnecessary. The quality gate (disclaimer on low-confidence answers) allows parallel progress while maintaining trust.

**Strongest objection acknowledged:** The contrarian argued for building workflows first to discover real needs. This has merit — real usage reveals gaps faster than speculation. The quality gate compromise allows this discovery while preventing the reputational risk of confidently wrong RFP answers.

---

## Risks

### 1. Schema/prompt iteration takes longer than expected
The 25-doc pilot may reveal that structured extraction requires more prompt engineering than one week allows, especially for poorly structured PDFs.
- **Mitigation:** Time-box the pilot to 1 week. Ship "good enough" schemas and iterate based on real workflow usage. Perfection is the enemy of progress.

### 2. On-demand re-extraction latency degrades UX
Background re-extraction may take 10–30 seconds. If the user expects immediate deep answers, stale-while-refresh may feel broken.
- **Mitigation:** Return existing note immediately with a visible flag: `⚠️ Shallow extraction — deep extraction queued`. User learns to re-query after a minute.

### 3. Hallucinated specifics despite citation requirements
LLMs may fabricate plausible SLA numbers or RTO values even when instructed to cite sources.
- **Mitigation:** Post-extraction validator checks that every numeric field in overlays has a non-null `citation`. If missing, set `needs_review: true`. `corp rfp answer` must surface this flag.

### 4. Classification errors route low-value docs to deep tier (cost overrun)
Folder-based heuristics may misclassify, especially for poorly organized client folders.
- **Mitigation:** User override in content_registry.yaml takes precedence. Monthly cost tracking catches systematic misclassification early. Default to standard tier when uncertain.

### 5. Mixed-fidelity vault causes retrieval confusion
For months, some notes will be v1 (shallow) and others v2 (structured). Retrieval and workflows may behave inconsistently.
- **Mitigation:** `extraction_version` and `depth` fields in YAML frontmatter. `corp prep` and `corp retrieve` explicitly handle both versions with graceful degradation (use what's available, flag gaps).

### 6. Engineering complexity of the new pipeline
Base+overlay routing, 2-pass orchestration, validators, on-demand triggers, and background jobs represent a significant increase in CKE complexity.
- **Mitigation:** Build incrementally. Week 1 deliverable is just "better single prompt with schema output." Multi-pass, validators, and on-demand come in subsequent weeks. Each increment ships independently.

---

## Action Items

### Week 1: Foundation
- [ ] **Define schemas:** Write Pydantic models for Base schema + 5 overlays in CKE repo under `schemas/`
- [ ] **Implement doc_type classifier:** Deterministic rules based on folder path + filename patterns in `content_registry.yaml`
- [ ] **Write deep extraction prompt:** Single prompt that outputs JSON matching overlay schemas, with citation requirements and "not found" rules
- [ ] **Run 25-doc pilot:** Select 5 docs per type (architecture, security, commercial, RFP, meeting). Extract with new prompt. Manually evaluate: Can you answer specific RFP questions from the output?
- [ ] **Iterate prompt and schemas** based on pilot results

### Week 2: Scale
- [ ] **Implement tiered routing:** Standard (1-call, base only) vs. Deep (2-call, base + overlays) based on doc_type
- [ ] **Add `extraction_version: 2` and `depth` to YAML frontmatter**
- [ ] **Batch re-extract 100 high-value docs** from active client folders and product/architecture sources
- [ ] **Implement post-extraction validator:** Check required overlay fields have citations; set `needs_review: true` if missing
- [ ] **Add monthly cost tracking** with $5 soft warning, $10 hard stop

### Week 3: Integration
- [ ] **Add on-demand re-extraction to `corp retrieve`:** Return existing note immediately; queue background job for v1 notes in high-value doc types
- [ ] **Update `corp prep` to handle v1 and v2 note formats** with graceful degradation
- [ ] **Resume workflow development** (`corp rfp answer`, etc.)

### Week 4: Ship
- [ ] **Ship `corp rfp answer` v1** with quality gate: answers from v1 notes or `needs_review: true` fields include disclaimer
- [ ] **Collect user feedback:** Which document types are most queried? Which fields are most useful? Which are missing?

### Month 2–3: Images + Iteration
- [ ] **Implement Phase 2 image extraction** for deep-tier docs only (local extraction → heuristic filter → Pillow re-encode → multimodal description, cap 3/doc)
- [ ] **Evaluate schema coverage:** Are 5 overlays sufficient? Add user-defined templates only if demonstrated need
- [ ] **Review cost/quality metrics:** actual spend, answer accuracy, user corrections per week
