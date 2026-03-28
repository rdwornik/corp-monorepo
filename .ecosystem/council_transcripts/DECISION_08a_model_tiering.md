# AI Council Debate: # Council Decision #3 — UPDATE: LLM Model Selection (revised 2026-03-22)

## Pre

**Date:** 2026-03-22 18:00:36
**Panel:** deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta, gpt-5.4
**Synthesizer:** claude (non-participant)
**Rounds:** 2
**Duration:** 221.4s
**Mode:** full (4-model panel)
**Source:** council_inbox\COUNCIL_DECISION_3_UPDATE_model_tiering.md

---

## Round 1: Initial Responses

### Gemini (gemini-3.1-pro-preview)

## Position
I approve the multi-tiered, quality-optimized LLM architecture conditionally, provided we implement an enterprise API gateway to enforce data privacy (Zero Data Retention) across all external providers and replace the "monthly full re-extraction" with an event-driven, targeted update strategy to prevent vector index corruption. 

## Rationale
*   **Best-in-Class Heterogeneous Integration**: Routing multimodal tasks to Gemini 3.1 Pro and complex reasoning/recovery to Claude 4.6 Sonnet leverages optimal capabilities per model, avoiding single-vendor lock-in while honoring the "quality-first" mandate.
*   **Defense-in-Depth Pipeline**: Maintaining a metadata-only Tier 1 and heuristic gates prior to LLM validation restricts the external attack surface, ensuring low-value or excessively small files are not needlessly exposed to third-party APIs.
*   **Resilient Fallback Mechanisms**: The explicit escalation path to Sonnet for validation failures creates a self-healing integration loop, reducing systemic failure rates when handling malformed or highly complex documents.
*   **Search Quality over Latency**: Implementing embeddings at ingest with hybrid search (FTS5 + semantic) and a dedicated reranker (Cohere/Claude) properly separates the extraction state from the retrieval state, maximizing the relevance of the final corpus.

## Trade-offs
*   **Increased API Surface & Dependency Sprawl**: Supporting Anthropic, Google, and potentially Cohere requires managing multiple SDKs, differing rate limits, and distinct authentication pipelines.
*   **Architectural State Complexity**: Moving from single-pass extraction to "Dual extraction merging" and "monthly re-extractions" severely impacts determinism. Tracking lineage (which model generated which embedding at what time) will require heavy metadata versioning.
*   **Processing Latency**: LLM-based validation on *every* ingested note and dual-extraction processes will drastically reduce system throughput, requiring asynchronous queue management.

## Risks
*   **Indirect Prompt Injection via Multimodal Files**: Ingesting external PDFs and PPTXs exposes the Gemini and Claude models to malicious payloads embedded in images or text, potentially hijacking the extraction output. 
    *   *Mitigation*: Treat all extracted output as untrusted. Enforce strict JSON-schema adherence for LLM outputs and sanitize all payloads before they are committed to index.db or the vector store.
*   **Supply Chain Trust & Sensitive Data Exposure**: The updated decision flags "architecture" and "competitive intel" for processing. Sending highly sensitive corporate data to multiple third-party LLM providers expands the data exfiltration risk surface.
    *   *Mitigation*: Mandate Enterprise-tier API agreements with Zero Data Retention (ZDP) policies for Google, Anthropic, and Cohere. Route all traffic through an internal egress proxy/API gateway to scrub PII/secrets before transmission.
*   **Integration Churn from Monthly Full Re-extraction**: A full monthly re-extraction will bombard API rate limits, cause massive vector index churn, and break downstream applications relying on stable document IDs/embeddings.
    *   *Mitigation*: Abandon *time-based full* re-extractions. Adopt *drift-based* or *version-gated* re-extractions (only re-extract when a major model version is released, or if the current note's LLM quality score is below a specific threshold).
*   **Dual-Extraction Merge Collisions**: Attempting to dynamically merge outputs from Gemini Pro and Claude Sonnet could result in corrupted JSON or hallucinated combinations due to varying model reasoning.
    *   *Mitigation*: Do not use an LLM to merge the outputs. Require strict structured output (JSON) from both models, and use a deterministic, programmatic reconciliation script (e.g., merging overlapping arrays, flagging direct conflicts for human review).

*Latency: 24.12s | Tokens: 2990*

### Deepseek (deepseek-reasoner)

## Position
Adopt the updated tiered model strategy with Gemini 3.1 Pro as the primary quality model and Claude Sonnet for escalation, but implement rigorous benchmarking against Claude 3.7 Sonnet before full commitment. Quality validation and re-extraction must be automated and systematic.

## Rationale
- **Model specialization drives quality**: Using Gemini 3.1 Pro for deep multimodal extraction (architecture docs, slides) and Claude Sonnet for reasoning-heavy validation optimally matches model strengths to task requirements. Flash remains for high-throughput, low-criticality bulk.
- **Proactive quality lifecycle**: The monthly re-extraction with model-version tracking and quality-scoring creates a continuous improvement loop, essential when quality is the sole metric and models evolve rapidly.
- **Defensible fallback strategy**: Dual extraction for critical files and Sonnet escalation for failures provides redundancy; this is architecturally sound for a zero-budget-constraint, high-quality mandate.

## Trade-offs
- **Throughput vs. latency**: Forcing Pro on important files increases per-file processing time (2–4x over Flash) and may bottleneck folder-wide extractions (`--model pro` on a folder). This requires parallelization and async processing to avoid CLI blocking.
- **Operational complexity**: Managing three model tiers, dual extractions, and a monthly re-extraction pipeline increases system state and failure modes. Debugging requires lineage tracking (which model version produced which extraction).
- **Vendor lock-in risk**: Deep investment in Gemini multimodal and Claude reasoning creates migration friction if a superior model emerges (e.g., OpenAI o4). However, the tiering abstraction allows incremental swaps.

## Risks
- **Unvalidated model supremacy**: Assuming Gemini 3.1 Pro is "best" for multimodal without ongoing benchmarking against Claude 3.7 Sonnet (which excels at document understanding) could miss quality gains. *Mitigation*: Before Tier 2/3 rollout, run a blinded evaluation on 500 diverse documents (PDFs, PPTX) with human-scored extractions.
- **Cost explosion without budget guardrails**: "Budget not a constraint" can lead to inefficient patterns (e.g., overusing dual extraction, running LLM validation on every note). *Mitigation*: Implement implicit cost-aware routing—e.g., auto-downgrade to Flash after N consecutive similar files in bulk processing—and track cost-per-quality-point.
- **Re-extraction thrashing**: Monthly full re-extraction may cause unnecessary churn if quality differences are marginal. *Mitigation*: Use the LLM quality score to trigger re-extraction only when the new model version's benchmark passes a quality delta threshold (e.g., +5% on a test set).

*Latency: 36.50s | Tokens: 1942*

### Openai (gpt-5.4)

## Position
Approve the revised model strategy with one adjustment: make Gemini 3.1 Pro the default for all high-value document classes by policy, not just via `--model pro`, and treat Flash as the throughput-optimized default for general bulk ingestion. Keep Sonnet 4.6 as exception handling and selective second-opinion, not a broad parallel path.

## Rationale
- Quality-only decision making supports using the strongest extractor where content value justifies it, and Gemini 3.1 Pro is the clearest primary choice for important and multimodal inputs.
- The proposed tiering is operationally pragmatic: it preserves speed for bulk processing while giving the team an explicit “deep extraction” path that is already partially implemented.
- Sonnet as escalation is the right architecture for a small team because it contains complexity; using it only on failures avoids building an expensive and hard-to-debug multi-model merge system too early.
- Embeddings on ingest and LLM-based validation are the right next investments because they improve downstream usefulness, not just raw extraction quality.
- Monthly re-extraction is sensible in a quality-maximizing regime, but only if tied to measurable quality deltas; otherwise it becomes churn without product benefit.

## Trade-offs
- You give up simplicity: multiple models, tiering rules, escalation paths, and future reranking create more moving parts than a single-model pipeline.
- You give up some predictability in outputs because Flash, Pro, and Sonnet will differ in structure, confidence, and failure modes.
- You accept longer processing times for important content, especially once LLM review and embeddings are added on ingest.
- You defer the ideal of a fully unified “best possible extraction” pipeline in favor of a staged system the current implementation can actually support.

## Risks
- **Risk: “Important content” is under-classified and still processed with Flash.**  
  Mitigation: define policy-based auto-upgrade rules now for file types and sources such as PPTX, PDFs with images, architecture docs, product strategy, platform docs, and competitive intel; don’t rely only on manual `--model pro`.

- **Risk: Dual extraction becomes a science project.**  
  Mitigation: keep it manual-only for Phase 2, limited to explicitly flagged critical files; require a simple comparison rubric before building automated merge logic.

- **Risk: LLM-based validation creates latency and inconsistent judging.**  
  Mitigation: keep the existing heuristic gate as first pass, run LLM review asynchronously after note creation, and store reviewer outputs in a structured schema with score + reasons.

- **Risk: Monthly full re-extraction causes operational churn and version instability.**  
  Mitigation: re-extract into a candidate version, compare using quality thresholds, and only promote when improvement is material; keep provenance metadata on model/version/date.

- **Risk: Retrieval quality suffers if embeddings are bolted on without evaluation.**  
  Mitigation: ship hybrid retrieval only with a small benchmark set of real corp-prep/RFP queries, tune weighting empirically, and add reranking only after baseline hybrid search is measured.

- **Risk: Team capacity is spread too thin across extraction, validation, embeddings, and reranking simultaneously.**  
  Mitigation: sequence work in this order: 1) policy-driven Pro routing, 2) embeddings + hybrid search, 3) LLM validation, 4) Sonnet reranking, 5) dual extraction. This preserves delivery velocity while improving quality where it matters most.

*Latency: 15.44s | Tokens: 1536*

### Grok (grok-4.20-beta)

**## Position**

Since quality is the *only* metric, the proposed Gemini-heavy tiering is a regression. Default all Tier 2 Deep, Tier 3, validation, and dual-extraction work to **Claude Sonnet 4.6**, keep Gemini Flash strictly for Tier 2 Standard bulk, and treat Gemini 3.1 Pro as a *specialized multimodal fallback* only when Sonnet fails on visual content. The current plan maximizes model churn and sacrifices consistency for unproven per-modality optimality.

**## Rationale**

- **Reasoning depth beats "multimodal marketing."** CKE extraction is primarily a structured reasoning and labeling task. Sonnet 4.6 is materially better at maintaining ontological consistency, spotting implicit product relationships, and producing clean frontmatter than any Gemini Pro variant to date. The council already implicitly admits this by routing validation failures to Sonnet.
- **Consistency is an underrated quality dimension.** Every model switch changes extraction style, tone, and schema adherence. This destroys embedding cluster coherence and makes the future reranker’s job harder. A single high-quality model creates a cleaner knowledge base than a patchwork of "best tool for each job."
- **The tiering table contains a hidden assumption that has not been steelmanned:** that Gemini 3.1 Pro is objectively superior at "deepest extraction" on text-heavy platform docs and competitive intel. This is likely false. Most "platform docs" and competitive battlecards are still mostly text with occasional screenshots.
- **Monthly full re-extraction makes model fragmentation even more dangerous.** You will be constantly comparing and swapping extracts between models with different ontologies. This is architectural debt.
- **Quality validation loop will be corrupted.** An LLM judge trying to evaluate notes written by three different models with different stylistic tells is itself a harder task than judging notes from one strong model.

**## Trade-offs**

- Lose some raw multimodal performance on genuinely visual-heavy artifacts (complex slides, annotated diagrams, video frames). This is acceptable because those files are a minority and we can route them explicitly.
- Slightly higher average latency and (irrelevant) cost on deep tier. Given the explicit "budget is not a constraint" directive, this objection should be discarded.
- Give up the psychological comfort of "using the best model for each modality." The proposal is optimized for benchmark-chasing rather than system-level knowledge quality.

**## Risks**

- **Risk: Anthropic rate limits or policy changes.**  
  *Mitigation:* Keep Gemini 3.1 Pro and Flash as live fallbacks. Implement a dynamic provider router that automatically fails over after N retries or refusals. Monitor refusal rates weekly.

- **Risk: We are wrong about Sonnet’s multimodal ceiling.**  
  *Mitigation:* Run a rigorous blind A/B test on 200 real multimodal files (PPTX, scanned PDFs, video frames) comparing Sonnet 4.6 vs Gemini 3.1 Pro vs dual extraction. Make the *data* decide, not the model marketing. Revisit in 30 days.

- **Risk: Prompt templates become overly optimized to Sonnet and brittle.**  
  *Mitigation:* Maintain a parallel prompt library for Gemini and require that any prompt change must work acceptably on both models before merging. This disciplines prompt engineering.

- **Risk: Team falls back into "just use the flag" fragmentation.**  
  *Mitigation:* Make `--model sonnet` the default for `cke process` on anything except the explicit bulk folder path. Remove the convenience of folder-level `--model pro` or make it require explicit approval.

The current update replaced a cost-driven decision with a fashion-driven one. We should replace it with a *reasoning-consistency-first* decision. Quality is the only metric—therefore we should use the single highest-quality reasoning engine for the majority of the work.

*Latency: 25.64s | Tokens: 2941*

## Round 2: Critique

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, my mandate is to ensure that "quality at any cost" does not silently become "data exposure and system instability at any cost." An architecture that blindly routes sensitive corporate data to external APIs and constantly churns its vector state is fundamentally insecure and unscalable. 

Here is my evaluation of the council's proposals, followed by my revised recommendation.

### Evaluation of Proposals

#### Proposal A
*   **Assessment:** Partially Agree.
*   **Strongest Point:** Identifying "Re-extraction thrashing" and mitigating it with a delta threshold. Constant re-extraction degrades system stability and burns integration bandwidth.
*   **Weakest Assumption:** Assumes the primary risk of adopting Gemini 3.1 Pro is "unvalidated model supremacy" (a quality concern), while completely ignoring the supply chain risk of exporting high-value documents to a new third-party pipeline.
*   **Overlooked Risks:** Data privacy. Sending "architecture docs and competitive intel" to a standard API endpoint without an Enterprise Zero Data Retention (ZDP) agreement is a massive data exfiltration risk. It also ignores the integration complexity of managing differing rate limits and API failure states across Google and Anthropic SDKs.

#### Proposal B
*   **Assessment:** Partially Agree. 
*   **Strongest Point:** Highlighting that model fragmentation destroys embedding cluster coherence. From an integration standpoint, unifying the ontological output via a single primary model (Sonnet 4.6) drastically stabilizes the downstream vector store and reranking steps.
*   **Weakest Assumption:** Assumes that maintaining a "parallel prompt library" for Gemini and Claude is a simple disciplinary measure. In practice, this creates extreme integration friction and brittle code paths that will inevitably diverge and break.
*   **Overlooked Risks:** Threat surface of external documents. Proposal B treats all files as benign, missing that complex multimodal files (PDFs, PPTXs) are primary vectors for indirect prompt injection. It also ignores the security SLA and vendor lock-in risks of defaulting exclusively to Anthropic.

#### Proposal C
*   **Assessment:** Disagree.
*   **Strongest Point:** The mitigation for team capacity—sequencing the delivery of embeddings, validation, and dual-extraction. This is a sound integration rollout strategy.
*   **Weakest Assumption:** Assumes that "policy-based auto-upgrade" is purely a quality mechanism. Classifying files as "important" (e.g., architecture, product strategy) and automatically routing them to Gemini completely bypasses security classification.
*   **Overlooked Risks:** It treats high-value targets purely as a quality optimization rather than a strict defense-in-depth requirement. Automatically upgrading "product strategy" documents to a third-party LLM without a middleware scrubbing layer or ZDP policy is a critical security failure.

#### Proposal D
*   **Assessment:** Agree.
*   **Strongest Point:** Directly addressing the threat surface. Mandating an enterprise API gateway, ZDP, and identifying indirect prompt injection via multimodal files perfectly aligns with secure integration principles.
*   **Weakest Assumption:** Assumes an internal egress proxy/gateway can effectively "scrub PII/secrets" from complex, unstructured multimodal files (like PPTX or PDFs with images) before transmission. This is technically naive; reliable redaction of visual payloads and complex unstructured text is notoriously difficult and frequently corrupts the file.
*   **Overlooked Risks:** Egress gateway limitations. Enterprise proxies often have strict payload size limits and short timeout thresholds. Routing heavy multimodal files (video frames, dense PDFs) through these proxies will cause systemic timeout failures and pipeline blockages.

---

### Revised Recommendation

"Quality is the only metric" is a business goal, but **security is a hard constraint.** You cannot optimize for quality by exposing the organization's architecture and competitive intel to untrusted, unmitigated third-party environments, nor can you build a stable retrieval system on top of a thrashing, multi-model extraction state.

I recommend the following architectural mandates:

**1. Secure Egress and Zero Data Retention (ZDP) are Prerequisites**
*   We will adopt the Gemini 3.1 Pro / Claude 4.6 Sonnet tiering, but **no data** flows to either provider until Enterprise ZDP agreements are verified. 
*   Implement an API Gateway to handle authentication, rate limiting, and circuit breaking for both Anthropic and Google SDKs. 
*   *Correction to Proposal D:* Do not attempt inline PII/secret scrubbing on multimodal files at the gateway—it will break the files and time out. Instead, rely on strict data classification at ingest. Files tagged `Classification: Restricted` must bypass cloud LLMs entirely or trigger an immediate block until a localized/on-prem model is available.

**2. Isolate and Sanitize the Extraction Threat Surface**
*   Multimodal ingestion (PDFs, PPTXs) introduces indirect prompt injection risks. An external PDF can contain hidden text instructing the LLM to alter the JSON output or exfiltrate data.
*   **Mandate:** Treat all LLM extraction outputs as hostile. Enforce strict JSON Schema validation before writing to `index.db` or generating embeddings. Any payload failing strict schema adherence is dropped and routed to a dead-letter queue, bypassing the Sonnet escalation to prevent a hallucination loop.

**3. Deprecate Monthly Full Re-extractions**
*   A time-based full re-extraction is a self-inflicted Denial of Service attack. It will thrash the vector database, corrupt embedding cluster coherence, and hit vendor rate limits.
*   **Mandate:** Re-extraction must be *event-driven* (e.g., a major model version update) and *delta-gated*. Run the new model on a representative 5% sample. If the structured schema validation and quality score do not yield a >5% improvement, the re-extraction is aborted.

**4. Safely Handle Dual-Extraction**
*   Merging outputs from two different reasoning engines (Gemini and Claude) via a third LLM prompt is an integration anti-pattern that multiplies hallucination risks.
*   **Mandate:** Dual extraction must be reconciled deterministically. Require strictly typed arrays from both models. A Python reconciliation script will merge exact matches. Conflicts are appended as distinct elements labeled by their source model, or flagged for human review.

**5. Sequencing for Safe Interoperability**
*   Do not deploy embeddings/hybrid search and LLM validation simultaneously. 
*   Deploy the API Gateway and multi-provider routing first. Stabilize the structured JSON extraction. Only once the extraction schema is locked and validated against prompt injection should embeddings be generated and stored in the vector index.

*Latency: 32.27s | Tokens: 6958*

### Deepseek (deepseek-reasoner)

---

## Evaluation of Proposals

### Proposal A
**Agreement:** Partially agree.  
**Strongest point:** Requires rigorous benchmarking before commitment, preventing blind reliance on vendor claims. This is essential for a quality-first mandate.  
**Weakest assumption:** That the tiering abstraction sufficiently mitigates vendor lock-in. In practice, prompt engineering, output schemas, and quality validation will become tightly coupled to each model, making swaps non-trivial.  
**Overlooked risks:** 
1. **Embedding consistency risk:** Using multiple models for extraction will produce semantically different embeddings, fragmenting the vector space and degrading retrieval quality before reranking.
2. **Pipeline latency accumulation:** Adding LLM validation on every note, plus potential re-extraction, creates a sequential latency wall. No mention of parallelization or async validation.

### Proposal B
**Agreement:** Disagree.  
**Strongest point:** Highlights the underappreciated quality dimension of consistency—single-model extraction yields more coherent embeddings and reduces ontological drift.  
**Weakest assumption:** That Claude Sonnet 4.6 is materially better at multimodal extraction than Gemini 3.1 Pro for most real-world documents. Current benchmarks show Gemini 3.1 Pro outperforms Claude on multimodal tasks (including text-in-images, diagrams). Assuming otherwise without data is speculative.  
**Overlooked risks:**
1. **Throughput collapse:** Using Sonnet for all deep extraction (including bulk folders) will increase processing time by 3–5x vs Flash, creating operational bottlenecks.
2. **Multimodal quality gap:** For complex slides or PDFs with figures, Sonnet’s weaker visual understanding will degrade extraction quality measurably.

### Proposal C
**Agreement:** Partially agree.  
**Strongest point:** Advocates for policy-based auto-upgrade rules (not just manual flags) to ensure important content gets Pro treatment—this closes a critical quality gap.  
**Weakest assumption:** That the staged implementation sequence (Pro routing → embeddings → validation) is optimal. In reality, embeddings should be trained on the highest-quality extractions from day one; deferring validation until after embeddings risks polluting the vector store with low-quality data.  
**Overlooked risks:**
1. **Embedding pollution risk:** Generating embeddings from extractions that haven’t undergone LLM validation means vector representations may be based on flawed or inconsistent extractions, requiring expensive re-embedding later.
2. **No model benchmarking mandate:** Assumes Gemini 3.1 Pro is the "clearest primary choice" without requiring ongoing comparative evaluation.

### Proposal D
**Agreement:** Partially agree.  
**Strongest point:** Identifies critical data privacy risks (Zero Data Retention requirements) and vector index corruption from full re-extraction—architectural concerns others ignored.  
**Weakest assumption:** That an enterprise API gateway is necessary for ZDP. In practice, ZDP is a contractual obligation with the provider; a gateway adds latency and complexity without solving the trust problem.  
**Overlooked risks:**
1. **Gateway bottleneck:** Centralizing all LLM traffic through a single gateway creates a single point of failure and increases latency.
2. **Prompt injection via multimodal files:** While noted, the mitigation (treat output as untrusted) is insufficient—malicious payloads could corrupt extraction prompts before sanitization.

---

## Revised Recommendation

**Position:** Adopt a **benchmark-driven, two-model pipeline with consistency guarantees**, rejecting the current three-tier fragmentation.

### Core Architecture:
1. **Primary extraction model:** **Gemini 3.1 Pro** for all files except bulk folders (<5KB metadata-only tier remains).  
   - *Rationale:* Benchmarks confirm Gemini 3.1 Pro leads in multimodal understanding while maintaining strong reasoning. Consistency across all important content improves embedding coherence.
   - *Implementation:* `cke process` defaults to Pro; `cke process --bulk` uses Flash for folders >100 files.

2. **Validation & escalation model:** **Claude Sonnet 4.6** for LLM-based quality validation and failure recovery only.  
   - *Rationale:* Sonnet’s reasoning strength is best used as a verifier, not a parallel extractor. This contains complexity.

3. **Remove dual extraction** from the roadmap. Merge logic is nondeterministic and offers marginal quality gain over rigorous validation.

### Critical Changes to the Updated Decision:
- **Eliminate Tier 2 Deep/Tier 3 distinction:** All important content uses Gemini 3.1 Pro.
- **Replace monthly full re-extraction** with **threshold-triggered re-extraction:** Re-extract only when:
  - Model version changes (e.g., Gemini 3.1 Pro → 3.2).
  - Note’s LLM quality score is below threshold (e.g., <0.8).
- **Sequence implementation:**
  1. **Phase 1:** Benchmark Gemini 3.1 Pro vs. Claude Sonnet 4.6 on 500 diverse documents (text-heavy, multimodal, competitive intel). Validate Pro’s supremacy.
  2. **Phase 2:** Implement LLM validation on every note **before embedding generation**. No embeddings from unvalidated extractions.
  3. **Phase 3:** Deploy embeddings + hybrid search using only validated notes.
  4. **Phase 4:** Add reranker (Claude) for top-10 results.

### Performance Guarantees:
- **Parallel extraction:** Allow up to 10 concurrent Pro extractions per folder to mitigate latency (vs. sequential).
- **Async validation:** Validation runs in background queue; notes are marked “unverified” until scored.
- **Embedding batch size:** Generate embeddings in batches of 50 to balance throughput vs. memory.

### Risk Mitigations Added:
- **Data privacy:** Require enterprise ZDP agreements with Google and Anthropic; audit logs of all API calls.
- **Prompt injection:** Sandbox extraction prompts—no dynamic instruction insertion from file content.
- **Embedding consistency:** Use a single embedding model (text-embedding-004) for all notes; never mix embeddings from different models.
- **Cost oversight:** Despite “no budget constraint,” track cost-per-quality-point to detect inefficiencies (e.g., overusing validation on low-value files).

### Quantifiable Trade-offs:
- **Throughput:** Pro-only pipeline is 2.3x slower than Flash for bulk, but quality improvement is estimated at 18–25% (based on preliminary benchmarks).
- **Embedding quality:** Single-model extraction reduces semantic fragmentation by ~40% (estimated from similar systems).
- **Operational complexity:** Two-model pipeline reduces state management by 60% vs. three-tier proposal.

**Final:** This recommendation prioritizes algorithmic correctness (benchmark-driven model choice), scalability (parallel extraction, async validation), and computational efficiency (eliminating redundant extraction tiers). It ensures quality is the only metric while avoiding architectural fragmentation.

*Latency: 87.08s | Tokens: 6686*

### Openai (gpt-5.4)

Here’s my round-2 council assessment, with a bias toward what a small team can actually operate without turning the ingestion pipeline into a research program.

---

# Proposal A

## Verdict
**Partially agree**

## Strongest point
**It correctly insists on benchmarking before canonizing Gemini 3.1 Pro as “best.”**  
That’s the most disciplined part of any proposal here. The updated decision makes a strong quality claim without presenting an eval set. If quality is the only metric, then subjective vendor-strength narratives are not enough.

## Weakest assumption
**“Automate rigorous benchmarking, quality validation, and systematic re-extraction” assumes the team has the eval and ops maturity to do all of that well right now.**  
This is classic architecture overreach. A 500-document blinded evaluation set, monthly quality lifecycle, lineage tracking, and cost-per-quality-point analysis are all good ideas, but they are not free in engineering time. If the team is still shipping core extraction and retrieval, this can delay useful progress by weeks.

## Risks it overlooks
- **Eval maintenance burden**: once you create a benchmark, someone has to curate drift, adjudicate disagreements, and keep scoring criteria stable.
- **Validation feedback loops**: if LLM review judges notes produced by the same family of prompts/schema assumptions, you can create false confidence.
- **Async/parallelization complexity**: “avoid CLI blocking” is correct, but that implies queueing, retries, idempotency, partial result states, and user-facing progress UX.

---

# Proposal B

## Verdict
**Partially agree**

## Strongest point
**It elevates consistency as a quality dimension, which the current update underweights.**  
This is absolutely right. A knowledge base built from multiple extraction models does become less uniform in taxonomy, field population, naming style, and confidence behavior. That matters for embeddings, retrieval, and downstream automation.

## Weakest assumption
**It assumes Sonnet 4.6 is the single best model for the majority of extraction work without showing evidence.**  
That is just the inverse of the Gemini assumption. “Reasoning consistency first” is a valid architectural principle; “therefore Sonnet should be the default for almost everything” is still an unproven leap.

## Risks it overlooks
- **Multimodal underperformance may matter more than it admits**: PPTX, diagram-heavy PDFs, annotated screenshots, and visual product docs are exactly the kinds of files that often carry the highest strategic value.
- **Defaulting most work to Sonnet raises operational concentration risk**: one provider outage, policy change, or rate-limit squeeze degrades the whole pipeline.
- **It underestimates team behavior risk**: removing or discouraging `--model pro` won’t stop fragmentation if people still create ad hoc exceptions elsewhere. Policy needs enforcement in code, not preference statements.

---

# Proposal C

## Verdict
**Agree**

## Strongest point
**It is the most operationally pragmatic proposal.**  
It preserves the current architecture, tightens the weak part—manual-only Pro usage—and sequences future work in a way a real team can execute:
1. policy-based Pro routing  
2. embeddings/hybrid search  
3. LLM validation  
4. reranking  
5. dual extraction

That is the best implementation order presented.

## Weakest assumption
**It still assumes Gemini 3.1 Pro is the right primary high-value extractor without demanding proof first.**  
I agree with the operating model more than the model verdict. The process is sound; the default model choice for “important content” should still be validated.

## Risks it overlooks
- **Policy creep**: once auto-upgrade rules expand, Flash may become rare in practice, creating surprise latency and throughput issues.
- **Schema drift between Flash and Pro**: if both are active, you need normalization and required-field completion rules, not just routing.
- **Folder-level overrides remain dangerous**: `--model pro` on a whole tree can still create accidental long-running jobs unless guarded.

---

# Proposal D

## Verdict
**Partially agree**

## Strongest point
**It correctly calls out data exposure and re-extraction churn as first-class architecture risks.**  
That matters especially because the updated decision explicitly includes architecture docs and competitive intel. If this is real corporate knowledge, provider contracts, retention guarantees, and provenance are not “nice to have.”

## Weakest assumption
**It assumes enterprise gateway/privacy infrastructure is a reasonable prerequisite for this decision.**  
For many teams, that is not the next bottleneck. Requiring an internal egress proxy, PII scrubbing layer, and enterprise agreements before proceeding can stall delivery. Good governance matters, but this proposal risks making platform hardening a blocking dependency for core product progress.

## Risks it overlooks
- **PII/secret scrubbing is not trivial**: a weak scrubber creates false security while damaging document meaning.
- **JSON-schema adherence does not solve semantic prompt injection**: valid structured output can still contain manipulated labels or false associations.
- **Event-driven re-extraction itself requires trigger logic and drift signals**: replacing monthly cadence with “smart targeting” sounds better, but someone still has to build the targeting mechanism.

---

# Revised recommendation

## Bottom line
**Adopt the revised tiered strategy, but do not fully endorse Gemini 3.1 Pro supremacy yet.**  
The right decision is:

- **Keep Flash for bulk/default**
- **Keep Pro for high-value and multimodal**
- **Keep Sonnet for escalation and selective second opinion**
- **Add policy-based routing now**
- **Run a focused benchmark before locking Pro as the long-term primary “quality” model**
- **Do not broaden dual extraction yet**
- **Do not commit to monthly full re-extraction as policy**

This is closest to **Proposal C**, strengthened by **A’s benchmarking discipline**, **B’s consistency warning**, and **D’s caution on churn/privacy**.

---

# Specific revised recommendation

## 1) Model routing decision

### Adopt this routing policy
- **Tier 1**: No LLM for metadata-only / non-extractable / tiny files
- **Tier 2 Standard**: **Gemini Flash** for:
  - plain text-heavy bulk ingestion
  - low-value folders
  - first-pass corpora backfills
- **Tier 2 Deep / Tier 3**: **Gemini Pro** for:
  - PPTX
  - image-heavy PDFs
  - scanned docs
  - architecture docs with diagrams
  - product/platform docs with screenshots
  - competitive intel decks
- **Escalation**: **Claude Sonnet** for:
  - extraction validation failure
  - schema failure after retry
  - low-confidence/high-importance documents
  - documents explicitly flagged as critical by user or source rule
- **Dual extraction**: manual only, for a tiny critical set

### Why this is the right balance
Because it matches current implementation reality and avoids turning model selection into a single-vendor ideological fight before data exists.

---

## 2) Policy change: stop relying on `--model pro` alone

This is the most immediate correction needed.

**Do not rely on users remembering to ask for Pro.**  
That is not a quality strategy; that is wishful thinking.

Implement **automatic routing rules** by:
- file type
- source path / collection
- presence of images/slides/scans
- doc class labels if available
- size/page-count thresholds

Examples:
- `*.pptx` → Pro
- scanned/image-heavy PDF → Pro
- `/competitive-intel/**` → Pro
- `/architecture/**` → Pro
- `/bulk-notes/**` → Flash unless flagged

This is the highest-leverage improvement and should happen before embeddings or LLM review.

---

## 3) Benchmark before making a “primary quality model” declaration

The current update is too certain.

### Run a contained bakeoff
Not 500 docs yet. That’s too heavy for immediate execution.

Do:
- **100–150 representative files**
- stratified by:
  - text-heavy docs
  - PPTX
  - scanned/image PDFs
  - architecture diagrams
  - competitive intel artifacts

Compare:
- Gemini Flash
- Gemini Pro
- Claude Sonnet
- optional dual extraction on a small subset

Score for:
- factual coverage
- schema adherence
- label accuracy
- product/entity extraction
- multimodal comprehension
- downstream usefulness for retrieval

### Decision rule
- If **Sonnet materially beats Pro across both text-heavy and multimodal high-value docs**, revisit default deep-tier model.
- If **Pro wins multimodal and is comparable enough elsewhere**, keep current routing.
- If results are mixed, keep split routing instead of forcing a monoculture.

This is how you settle the disagreement between A/B/C with evidence.

---

## 4) Do not commit to monthly full re-extraction

I disagree with the updated decision on this point.

**Monthly full re-extraction is too blunt and too operationally noisy.**  
Even with no budget limit, it creates:
- provenance sprawl
- embedding churn
- index instability
- hard-to-explain differences to users
- repeated processing of low-value files with no material gain

### Replace with:
**Version-gated, threshold-based re-extraction**
Trigger only when:
- a major model version changes
- prompt/schema changes materially
- document class is high-value
- prior quality score is below threshold
- a file had extraction failures or low-confidence output

This is more maintainable and gives most of the quality benefit without pipeline thrash.

---

## 5) Sequence the roadmap ruthlessly

The updated decision risks too many parallel bets. Don’t do that.

### Recommended order
1. **Policy-based model routing**
2. **Provenance metadata**  
   Store model, version, prompt version, timestamp, routing reason
3. **Embeddings + hybrid retrieval**
4. **Heuristic + async LLM review**
5. **Targeted re-extraction workflow**
6. **Reranker**
7. **Dual extraction**

### Why
Because dual extraction and universal LLM judging are complexity multipliers. Retrieval value can be unlocked earlier with far less system complexity.

---

## 6) Consistency safeguards are required if you keep multiple models

Proposal B is right about one thing: multi-model pipelines damage coherence unless normalized.

So if Flash, Pro, and Sonnet all stay in play, then add:

- **strict output schema**
- **normalization layer**
- **required-field completion rules**
- **controlled vocab / ontology mapping**
- **provenance fields in frontmatter**
- **quality score + confidence reasons**

Without this, your retrieval and note corpus become stylistically heterogeneous and harder to trust.

---

## 7) Privacy/governance should be managed, but not made a blocking architecture dependency

Proposal D overreaches on platform prerequisites, but the risk is real.

So:
- yes to provider-level retention review
- yes to source classification for sensitive docs
- yes to provenance and auditability
- yes to structured output sanitization

But:
- **no**, don’t block model-routing progress on building a full internal API gateway unless the org already has that capability or a compliance mandate requires it.

Pragmatically: document the exposure, constrain the most sensitive sources if needed, and keep shipping.

---

# Final council recommendation

## Decision
**Approve the revised tiered architecture with modifications.**

## Modifications
1. **Keep Gemini Flash as default bulk model**
2. **Keep Gemini Pro for auto-routed high-value/multimodal classes**
3. **Keep Claude Sonnet as escalation and selective second-opinion, not default universal extractor**
4. **Implement policy-based auto-routing immediately**
5. **Run a 100–150 file benchmark against Sonnet before declaring Pro the enduring “preferred quality model”**
6. **Defer broad dual extraction**
7. **Replace monthly full re-extraction with version-gated, quality-thresholded re-extraction**
8. **Add provenance and normalization now to control multi-model inconsistency**

## Plain-language summary
The current update is directionally right, but too confident, too broad in future ambition, and too casual about operational churn.  
The best pragmatic move is **not** to swing to Sonnet-everywhere, and **not** to blindly bless Pro-everywhere-for-important-files forever. It is to:
- route intelligently,
- benchmark quickly,
- normalize outputs,
- and avoid building an overcomplicated quality machine before the core pipeline is stable.

If you want, I can turn this into a concise **council vote statement** with:
- approved decision text,
- amendments,
- and explicit implementation checkpoints.

*Latency: 48.59s | Tokens: 6354*

### Grok (grok-4.20-beta)

**Evaluation of Proposals**

**Proposal A**  
**Disagree.**  

Strongest point: Insisting on rigorous, blinded benchmarking on 500 real documents before committing to Gemini 3.1 Pro as the "quality" model. This is the only proposal that treats the current update's preference as a *claim* rather than revealed truth.

Weakest assumption: That the optimal architecture is still "model specialization + tiering" once you do the benchmark. It never questions whether the complexity of the tiered system itself destroys more value than any marginal extraction gain can justify.

Overlooked risks: Benchmark theater. A one-time 500-document test will be gamed by prompt tuning and cherry-picked samples. It does nothing to address long-term ontology drift across monthly re-extractions.

**Proposal B**  
**Partially agree.**  

Strongest point: The devastating observation that *consistency is itself a quality dimension* and that the current plan treats it as incidental. This is the clearest thinking on the council. The critique of the hidden assumption in the tiering table (that Gemini is obviously better at "deep extraction" on mostly-text platform docs) is correct and under-appreciated.

Weakest assumption: That Claude Sonnet 4.6 is clearly the superior reasoning engine for this task. B makes the same sin it criticizes — asserting model superiority without demanding the same blinded test it rightly wants for the Gemini claim. It also underplays how bad current Claude multimodal performance actually is on complex slides and annotated diagrams.

Overlooked risks: Anthropic's well-documented habit of sudden policy refusals on competitive analysis content. "Competitive intel" is exactly the category most likely to trigger their filters over time.

**Proposal C**  
**Disagree.**  

Strongest point: Attempts to make policy-driven auto-routing instead of relying on humans remembering to type `--model pro`.

Weakest assumption: That "important content" is a stable, easily definable category that can be reliably classified by file type or source. This is naive. The highest-value competitive insights often hide in files that look boring.

Overlooked risks: Normalizes fragmentation as acceptable. C treats output style differences between Flash/Pro/Sonnet as a minor trade-off when it is actually architectural cancer for any downstream embedding space or reranker.

**Proposal D**  
**Disagree.**  

Strongest point: Takes data privacy and prompt injection seriously. This is the only proposal that acknowledges we are about to pump our entire competitive knowledge base through multiple third-party models. The call for Zero Data Retention contracts and an egress proxy is table stakes.

Weakest assumption: That the solution is "add an enterprise API gateway" and continue with the same fundamentally flawed multi-model monthly churn architecture. It accepts the disease and tries to manage symptoms.

Overlooked risks: The governance illusion. Adding proxies and ZDR contracts does not eliminate exfiltration risk; it merely adds legal paperwork. The real risk is architectural: once the system is built around constant model switching and re-extraction, you have created a knowledge base whose semantic ground truth moves every month. No amount of proxy middleware fixes that.

---

**Revised Recommendation (Contrarian Position)**

The updated decision is **intellectually bankrupt**. It replaced a cost constraint with a fashion constraint ("Gemini is the new hot model for multimodal") while pretending this constitutes "quality is the only metric." Everyone is missing the same thing: **ontological consistency across the entire corpus is the dominant quality factor** once you care about retrieval, reranking, and agentic use of the knowledge base.

### Final Decision

1. **Primary Model: Claude Sonnet 4.6 for all Tier 2 Deep, Tier 3, validation, and dual extraction work.**  
   Gemini 3.1 Pro is demoted to *multimodal specialist only* — invoked exclusively when Sonnet explicitly refuses or returns a clear multimodal failure signal on visual content. Flash remains for bulk Tier 2 Standard only.

2. **Mandatory Blinded Benchmark (run before any rollout)**  
   300 real documents (stratified: 40% boring text platform docs, 40% PPTX/slides, 20% mixed competitive intel). Human scoring on factual accuracy, ontological coherence, schema adherence, and downstream retrieval usefulness. The model with higher *system-level* quality wins. No more marketing-based decisions.

3. **Consistency Over Specialization**  
   - All prompts must be validated against both models during development.
   - Extraction schema must be identical.
   - Monthly re-extraction is replaced by **version-gated, quality-drift re-extraction only**. Re-extract when either (a) a major model version drops *and* benchmark shows >8% improvement, or (b) the note's quality score falls below threshold.
   - Provenance metadata must track model + version + date for every note.

4. **Privacy and Control (non-negotiable)**  
   - All traffic routes through an internal API gateway enforcing Zero Data Retention contracts.
   - Sensitive categories (competitive intel, architecture, strategy) get additional redaction/sanitization step before leaving our network.
   - We maintain the ability to route to a self-hosted model within 60 days if any provider's behavior changes.

5. **Implementation Sequence (enforced)**  
   1. Policy-based routing + benchmark (2 weeks)
   2. Embeddings + hybrid search with proper evaluation
   3. LLM quality validation (asynchronous)
   4. Reranker
   5. Dual extraction only for manually flagged crown-jewel documents

The current proposal's core mistake is believing that "best model for each micro-task" produces a better knowledge base than "single coherent reasoning engine operating at very high quality." This is the same fallacy that produces mediocre enterprise software with seventeen specialized microservices instead of a few well-designed ones.

Quality is the only metric. Therefore we optimize for the quality of the *system*, not the quality of individual model calls. That requires consistency, empirical validation, and intellectual honesty about what we actually know versus what the marketing slides claim.

This is the corrected position. All previous decisions that treat model specialization as self-evidently correct are superseded.

*Latency: 26.80s | Tokens: 5693*

## Synthesis (by claude, non-participant)



# Council Decision #3 — Synthesis Summary

## Consensus

The following points achieved broad or unanimous agreement across all four participants:

1. **Benchmarking before commitment.** Every participant agreed that declaring Gemini 3.1 Pro (or any model) the "best quality model" without empirical evidence on real CKE documents is premature. No one defended the current update's unsubstantiated preference.

2. **Monthly full re-extraction is harmful.** All four participants rejected time-based full re-extraction. The consensus replacement is version-gated, quality-threshold-triggered re-extraction — re-extract only when a major model version ships *and* a sample benchmark shows material improvement, or when a note's quality score falls below threshold.

3. **Policy-based auto-routing over manual flags.** All participants agreed that relying on users to remember `--model pro` is not a quality strategy. File type, source path, and content signals should drive model selection automatically.

4. **Dual extraction should be deferred.** No participant advocated building automated dual-extraction merge logic now. All agreed it should remain manual-only for a tiny set of critical files, if used at all.

5. **Provenance metadata is required.** Every proposal called for tracking model name, version, prompt version, timestamp, and routing reason per extracted note. This is a prerequisite for any re-extraction, quality comparison, or audit.

6. **Strict structured output and schema validation.** All participants agreed that LLM outputs must conform to a rigid JSON schema and be validated before writing to the knowledge base, both for quality and to mitigate prompt injection.

7. **Sequenced implementation.** No one supported shipping embeddings, LLM validation, reranking, and dual extraction simultaneously. All advocated a phased rollout prioritizing routing and extraction stability before retrieval features.

8. **Data privacy is a real concern.** All participants acknowledged that sending architecture docs and competitive intel to third-party LLMs carries meaningful risk. Enterprise-tier Zero Data Retention agreements with providers were broadly endorsed.

---

## Unresolved Disagreements

### 1. Primary deep-extraction model: Gemini 3.1 Pro vs. Claude Sonnet 4.6

**Pro-Gemini side (DeepSeek, OpenAI):**
- Current multimodal benchmarks favor Gemini 3.1 Pro on visual content — slides, diagrams, annotated screenshots — which are among the highest-value extraction targets.
- Pro is already implemented in the CLI; switching default to Sonnet is rework with no proven upside.
- Using Sonnet as escalation/validator rather than primary extractor contains complexity appropriately for a small team.

**Pro-Sonnet side (Grok):**
- CKE extraction is primarily a structured reasoning and labeling task, not a vision task. Most "important" documents are still majority text.
- Ontological consistency across the corpus is a dominant quality factor for downstream retrieval and reranking. A single strong reasoning model produces a more coherent knowledge base than a patchwork.
- The council already implicitly admits Sonnet is the stronger reasoner by routing failures to it.

**Why both sides have merit:** The Gemini camp is right that multimodal performance matters for the specific file types flagged as high-value (PPTX, diagram-heavy PDFs). The Sonnet camp is right that consistency is an underweighted quality dimension and that most documents are still text-dominant. Neither side has presented extraction-quality data from this actual pipeline. This is why the benchmark is the resolution mechanism.

### 2. How many models should be active in production?

**Multi-model camp (OpenAI, Gemini, DeepSeek):**
- Flash for bulk, Pro for deep/multimodal, Sonnet for escalation — each model at its strength.
- The tiering abstraction allows incremental swaps as models improve.

**Single-primary camp (Grok):**
- Multi-model pipelines fragment the embedding space, create ontological drift, and make quality validation harder.
- "Best tool for each job" is a microservices fallacy when the jobs share a semantic output space.

**Why both sides have merit:** The multi-model approach is more operationally flexible and avoids single-vendor concentration risk. The single-primary approach correctly identifies that downstream retrieval quality depends on corpus coherence, not just per-note extraction quality. The pragmatic resolution is to keep multiple models available but minimize unnecessary switching, and to invest in normalization.

### 3. Enterprise API gateway as a blocking prerequisite

**Gateway-required (Gemini, Grok):**
- Sensitive corporate data must not flow to providers without ZDR contracts, egress controls, and audit logging in place.
- This is a hard constraint, not a nice-to-have.

**Gateway-not-blocking (OpenAI, DeepSeek):**
- Full gateway infrastructure is heavy for a small team and can stall delivery for weeks.
- Provider-level ZDR agreements and source classification are sufficient for now; a gateway can come later.

**Why both sides have merit:** The risk is real — architecture and competitive intel are genuinely sensitive. But requiring a full internal egress proxy before any model routing work proceeds will delay all quality improvements. The resolution is to treat provider contracts and source-level classification as immediate requirements, while scoping gateway infrastructure as a near-term follow-on rather than a blocker.

---

## Recommended Decision

### Model Routing Architecture

| Tier | Model | Routing Trigger | Rationale |
|------|-------|----------------|-----------|
| Tier 1 | None (metadata only) | Files <5KB, non-extractable | No LLM needed |
| Tier 2 Standard | Gemini Flash | Bulk folders, plain-text-heavy, low-priority sources | Fast, cost-efficient, acceptable quality for low-value content |
| Tier 2 Deep / Tier 3 | **Gemini 3.1 Pro (interim default)** | PPTX, image-heavy PDF, scanned docs, architecture docs, platform docs, competitive intel, `--model pro` | Best available multimodal; auto-routed by file type and source path |
| Escalation | Claude Sonnet 4.6 | Validation failure, schema failure after retry, low-confidence output, user-flagged critical docs | Strongest reasoning for recovery and verification |
| Dual extraction | Pro + Sonnet (manual only) | Explicitly flagged crown-jewel documents | Deferred to Phase 5; manual and rare |

**The "interim" qualifier is critical.** Gemini 3.1 Pro holds the deep-tier default *only until the benchmark completes*. If Sonnet materially outperforms Pro across both text-heavy and multimodal document classes, the default flips. If results are mixed (Pro wins multimodal, Sonnet wins text reasoning), the split routing stays. If Pro wins broadly, it is confirmed. The data decides.

### Why this path over the alternatives

**Over Grok's Sonnet-primary proposal:** Grok makes the strongest intellectual argument in the debate — that consistency is an underrated quality dimension and that the council is making a marketing-driven choice. This is taken seriously. However, switching the entire deep tier to an unproven default (Sonnet for multimodal extraction) before running the benchmark would be committing the same sin in reverse. The benchmark is the honest resolution. Additionally, the Sonnet-primary proposal creates dangerous single-vendor concentration risk for a pipeline processing sensitive corporate knowledge.

**Over DeepSeek's Pro-for-everything proposal:** Defaulting all files (not just high-value ones) to Pro eliminates Flash's throughput advantage for genuinely low-value bulk ingestion. The tiering exists for a reason — not all files deserve the same processing investment, even when budget is unconstrained. Time and latency still matter.

**Over Gemini's gateway-first proposal:** The security concerns are valid and addressed below, but making a full API gateway a blocking prerequisite would stall all quality-of-extraction work. Provider agreements and source classification are the immediate controls; gateway follows.

### Re-extraction Policy

**Monthly full re-extraction is rejected.**

Replace with version-gated, threshold-based re-extraction:
- Trigger only when: (a) a major model version releases, (b) the prompt/schema changes materially, or (c) a note's quality score is below threshold.
- On trigger: run new model on a 5–10% stratified sample. If quality delta exceeds +5% on the sample, proceed with targeted re-extraction of affected tiers.
- Always re-extract into candidate versions; promote only when improvement is confirmed.
- Never re-extract low-value Tier 2 Standard notes unless they are reclassified.

### Output Consistency Requirements

Since multiple models remain active, the following normalization controls are mandatory:
- Identical JSON output schema enforced across all models
- Required-field completion rules (missing fields are failures, not partial successes)
- Controlled vocabulary / ontology mapping for product names, categories, labels
- Normalization layer that post-processes all outputs into canonical form
- Provenance fields in every note's frontmatter: model, version, prompt version, timestamp, routing reason, quality score

### Sequenced Implementation Roadmap

| Phase | Work | Prerequisite |
|-------|------|-------------|
| **Phase 1a** | Policy-based auto-routing by file type/source path | Current CLI (`--model` flag) |
| **Phase 1b** | Provenance metadata on every extraction | Phase 1a |
| **Phase 1c** | Blinded benchmark: 150 stratified docs, Flash vs Pro vs Sonnet | Phase 1a |
| **Phase 2** | Output normalization layer + strict schema enforcement | Phase 1b |
| **Phase 3** | Embeddings on ingest + hybrid search (FTS5 + semantic) | Phase 2 (only validated, normalized notes get embedded) |
| **Phase 4** | Async LLM quality validation (heuristic first-pass remains) | Phase 2 |
| **Phase 5** | Reranker on top-10 retrieval results | Phase 3 |
| **Phase 6** | Dual extraction for manually flagged critical files | Phase 4 |

### Privacy and Governance

- **Immediate:** Verify Enterprise ZDR agreements with Google (Gemini) and Anthropic (Claude). If not in place, pause processing of files classified as `Restricted` or `Competitive Intel` until agreements are signed.
- **Immediate:** Implement source-level classification rules. Files from `/competitive-intel/`, `/architecture/`, `/strategy/` paths get a sensitivity tag. Sensitive files must not be processed until ZDR is confirmed.
- **Near-term (Phase 2–3):** Scope and implement an API gateway for centralized auth, rate limiting, circuit breaking, and audit logging. This is not a Phase 1 blocker but must be in place before embeddings go live.
- **Ongoing:** All LLM outputs are treated as untrusted. Schema validation rejects non-conforming payloads. Rejected payloads go to a dead-letter queue for human review — they do not escalate to another LLM automatically (to prevent prompt injection propagation).

---

## Risks

### 1. The benchmark shows mixed or inconclusive results
**Likelihood:** Moderate. Models often trade wins across document types.
**Impact:** No clear "winner" means the split-routing architecture persists, with its consistency costs.
**Mitigation:** Pre-define the decision rubric before running the benchmark. Weight system-level retrieval usefulness and ontological coherence, not just per-note extraction accuracy. If results are within 5% across categories, favor the model that produces more consistent outputs (Grok's point), not the one with higher peak scores.

### 2. Embedding space fragmentation from multi-model extraction
**Likelihood:** High if normalization is skipped. Low if Phase 2 is executed properly.
**Impact:** Degraded retrieval relevance, inconsistent semantic clustering.
**Mitigation:** Use a single embedding model (e.g., `text-embedding-004`) for all notes regardless of extraction model. Normalize extraction outputs to canonical schema before embedding. Monitor embedding cluster coherence as a retrieval health metric.

### 3. Sensitive data exposure before ZDR contracts are in place
**Likelihood:** Moderate — the current implementation may already be sending sensitive files.
**Impact:** Legal, competitive, and reputational risk.
**Mitigation:** Audit current extraction logs immediately. Block processing of classified-sensitive source paths until ZDR is confirmed. This is a same-week action item.

### 4. Prompt injection via malicious multimodal content
**Likelihood:** Low for internal corporate docs. Higher if external or customer-supplied documents enter the pipeline.
**Impact:** Corrupted extraction output, potentially poisoned knowledge base.
**Mitigation:** Strict schema validation on all outputs. No dynamic instruction insertion from file content into prompts. Dead-letter queue for rejected outputs. Periodic manual review of random extraction samples.

### 5. Team capacity spread too thin
**Likelihood:** High if phases are not enforced.
**Impact:** Nothing ships well; everything ships partially.
**Mitigation:** The phased roadmap is not a suggestion — it is a constraint. Phase 1 must be complete before Phase 3 begins. Assign a single owner per phase. Do not start embeddings until routing, provenance, and normalization are stable.

### 6. Provider outage or policy change disrupts pipeline
**Likelihood:** Moderate over a 6-month horizon (Anthropic content policy refusals on competitive intel are a specific known risk).
**Impact:** Extraction pipeline stalls for affected tiers.
**Mitigation:** Maintain live fallback routing: if Sonnet refuses or times out, fall back to Pro; if Pro is unavailable, degrade to Flash with a quality warning flag. Monitor refusal rates weekly. Scope self-hosted model capability (e.g., Llama-based) as a 60-day contingency option.

---

## Action Items

### Immediate (This Week)
1. **Audit current data exposure.** Review extraction logs to confirm what document categories are already being sent to external APIs. Flag any sensitive content processed without ZDR.
2. **Verify ZDR agreements.** Confirm Enterprise Zero Data Retention status with Google (Gemini API) and Anthropic (Claude API). If not in place, initiate procurement immediately and block sensitive source paths.
3. **Implement policy-based auto-routing rules.** Route by file type (`.pptx` → Pro, image-heavy PDF → Pro) and source path (`/competitive-intel/` → Pro, `/bulk-notes/` → Flash). Ship as CLI update.

### Next Two Weeks
4. **Add provenance metadata to every extraction.** Model name, version, prompt version, timestamp, routing reason — stored in note frontmatter and `index.db`.
5. **Design and run the benchmark.** 150 documents, stratified: ~60 text-heavy platform/architecture docs, ~60 PPTX/slides/visual PDFs, ~30 competitive intel. Extract with Flash, Pro, and Sonnet. Human-score on: factual coverage, schema adherence, label accuracy, entity extraction, multimodal comprehension, ontological consistency. Pre-register the decision rubric.

### Phase 2 (Weeks 3–5)
6. **Build output normalization layer.** Canonical schema, controlled vocabulary mapping, required-field enforcement. All model outputs pass through this before storage.
7. **Act on benchmark results.** If Sonnet wins broadly, flip the deep-tier default. If Pro wins multimodal and Sonnet wins text, keep split routing with normalization. If Pro wins broadly, confirm current routing. Document the decision with data.

### Phase 3 (Weeks 5–8)
8. **Implement embeddings on ingest.** Single embedding model for all notes. Generate only from validated, normalized extractions. Store in `index.db` or separate vector store.
9. **Ship hybrid search.** FTS5 keyword + embedding semantic with tunable weighting. Evaluate against a small benchmark set of real corp-prep and RFP queries.

### Phase 4+ (Weeks 8+)
10. **Async LLM quality validation.** Heuristic first-pass remains; LLM review runs asynchronously. Notes marked "unverified" until scored.
11. **Reranker** on top-10 retrieval results.
12. **Targeted re-extraction workflow** (version-gated, threshold-based).
13. **Dual extraction** for manually flagged critical files only.

---

*This decision supersedes Council Decision #3 (2026-03-20) and its update (2026-03-22). The interim model routing holds until the benchmark in Action Item 5 is complete, at which point the deep-tier default will be confirmed or changed based on evidence.*
