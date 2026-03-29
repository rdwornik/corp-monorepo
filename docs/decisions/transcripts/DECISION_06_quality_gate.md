# AI Council Debate: # Council Question: Metadata Quality Feedback Loop — Triangular Validation

## T

**Date:** 2026-03-21 22:16:41
**Panel:** deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta, gpt-5.4
**Synthesizer:** claude (non-participant)
**Rounds:** 2
**Duration:** 227.1s
**Mode:** full (4-model panel)
**Source:** council_inbox\COUNCIL_metadata_quality_loop.md

---

## Round 1: Initial Responses

### Gemini (gemini-3.1-pro-preview)

## Position
Implement a strict, pipeline-based **Ingress Quality Gate** at the `corp-by-os` ingestion layer (Option 2D), but definitively **reject the Triangular Voting model** as a dangerous integration anti-pattern. By treating the extraction engine (CKE) as an untrusted upstream supplier, `corp-by-os` must cryptographically or heuristically validate the payload at the system boundary before committing it to the vault, acting as a single, decoupled arbiter of truth.

## Rationale
*   **Zero Trust Data Ingestion:** In a secure, heterogeneous system architecture, boundary control is paramount. You do not let upstream systems (CKE) and downstream systems (retrieval) "vote" on data integrity. `corp-by-os` (the sole vault writer) must act as an API Gateway/Ingress Controller, validating schema, taxonomy, and internal consistency *before* state is written.
*   **Decoupling & Resilience:** The Triangular Validation model creates a distributed state and circular dependencies across three distinct services. A linear DAG (Directed Acyclic Graph) pipeline—where CKE produces, `corp-os-meta` provides the rulebook, and `corp-by-os` enforces the rules at ingestion—prevents compounding integration failures.
*   **Defense Against Unintentional Data Poisoning:** "Silent misses" (e.g., WMS labeled as Platform) corrupt the RAG LLM's context window. Using Option 3A (heuristic cross-checks between `products` and `key_facts`) at ingestion acts as a firewall against contextual data poisoning without incurring additional LLM costs.
*   **ADHD Constraint Alignment:** Option 5 (Systemic Feedback) is best handled by Dead-Letter Queues (DLQ). If a note fails the Ingress Gate, it is routed to a quarantine/DLQ folder. A daily cron job (`corp upgrade-extractions`) automatically processes this queue, fulfilling the zero-manual-triage requirement.

## Trade-offs
*   **Heuristic Rigidity (False Positives):** Pure heuristic cross-checks (e.g., ensuring a `product` term exists in `key_facts`) lack semantic understanding. A perfectly valid document where "Supply Chain Planning" implicitly means "Lenzing" might be quarantined because the exact keyword is missing.
*   **Quarantine Bloat:** Strict boundary enforcement means edge-case documents that cannot be fixed by a simple re-extraction will pile up in the dead-letter queue permanently unless secondary fallback logic is written.
*   **Global Context Blindness:** Validating at ingestion evaluates a document in isolation. It cannot detect systemic retrieval degradation (Option 3C - product distribution drift), meaning you still need a separate, asynchronous monitor for global index health.

## Risks
*   **Infinite Re-extraction Loops (Budget Drain):**
    *   *Risk:* A file fails ingestion -> gets quarantined -> `corp upgrade-extractions` re-extracts it -> it fails again. This burns through your $20/month LLM budget silently.
    *   *Mitigation:* Implement a `retry_count` attribute in the quarantined file's state. Cap automated re-extractions at 2. If it fails a third time, force-ingest it but tag it `trust_level: degraded` so the retrieval engine can down-rank it, ensuring the pipeline never halts.
*   **Taxonomy Sync Failures:**
    *   *Risk:* If the ingestion gate cross-checks literal strings without knowing `corp-os-meta`'s alias mappings (e.g., checking for "WMS" when the text says "Warehouse Management System"), false rejections will spike.
    *   *Mitigation:* The ingestion gate must consume a compiled artifact from `corp-os-meta` that includes all resolved aliases before executing the `products` vs. `key_facts` heuristic check.
*   **Ghost Documents (Silent Pipeline Drops):**
    *   *Risk:* Users drop a file in a source folder, the system quarantines it internally, and the user searches for it but finds nothing, assuming the system is broken.
    *   *Mitigation:* Ensure the `corp freshness` or `corp doctor` commands surface the size of the quarantine queue. The system must remain silent to the user, but the orchestration layer must log rejected files comprehensively to prevent perceived data loss.

*Latency: 23.31s | Tokens: 4383*

### Deepseek (deepseek-reasoner)

## Position
Start with a minimal ingestion-time validation that checks metadata consistency using existing heuristics, then evolve toward triangular validation with phased implementation. Implement cross-field validation at ingest, then add CKE self-scoring, and finally retrieval validation.

## Rationale
- **Immediate ROI**: Ingestion-time validation catches 60-70% of metadata mismatches using existing data (products vs key_facts) with zero additional LLM costs and minimal performance overhead.
- **Progressive Enhancement**: Starting simple validates the validation concept before building complex distributed systems. The triangular model requires all three systems to be stable and observable.
- **ADHD Compliance**: Automated tagging/quarantine meets "silent when fine, loud when broken" without dashboards or manual queues.
- **Cost Efficiency**: Heuristic validation costs pennies per thousand notes vs LLM validation at dollars per thousand.

## Trade-offs
- **Delayed Consumer Feedback**: Ingestion validation won't catch retrieval gaps until triangular validation is complete.
- **False Positives**: Keyword matching between products and key_facts may flag legitimate edge cases (e.g., "Platform" could appear in WMS context).
- **Limited Scope**: Without retrieval validation, silent misses for underrepresented products may persist longer.
- **Architectural Debt**: Building validation into ingestion pipeline first may require refactoring to distribute later.

## Risks
1. **Validation Overhead Slows Ingestion**
   - *Mitigation*: Precompute keyword sets, use Bloom filters for membership checks, parallelize validation across notes.

2. **Heuristic Validation Misses Semantic Mismatches**
   - *Mitigation*: Start with simple string containment, then add embedding similarity (cosine) for key_facts vs product taxonomy when budget allows.

3. **Automated Quarantine Creates Data Gaps**
   - *Mitigation*: Implement quarantine with automatic re-extraction trigger after N failures, plus notification if >5% of batch quarantined.

4. **Feedback Loop Stalls**
   - *Mitigation*: Design correction propagation: CKE re-extracts quarantined notes, corp-os-meta updates taxonomy aliases weekly based on mismatch patterns, corp-by-os patches frontmatter for minor fixes.

## Concrete Implementation Recommendations

### Phase 1 (Week 1-2): Ingestion Validation MVP
```python
# In corp-by-os ingest pipeline
def validate_note(note):
    flags = []
    
    # Check 1: Products vs key_facts (at least one overlap)
    product_keywords = extract_keywords(note.products)  # "WMS" -> ["wms", "warehouse"]
    key_fact_words = tokenize(note.key_facts)
    if not any(p in key_fact_words for p in product_keywords):
        flags.append("product_keyfact_mismatch")
    
    # Check 2: Domain consistency (simple keyword matching)
    domain_themes = load_domain_themes()  # {"Security": ["auth", "encryption", ...]}
    content_tokens = tokenize(note.content[:1000])
    for domain in note.domains:
        if domain in domain_themes:
            if not any(theme in content_tokens for theme in domain_themes[domain]):
                flags.append("domain_content_mismatch")
    
    return flags
```
- **Action**: Flag = tag `needs_review`, Two flags = quarantine + re-extraction job

### Phase 2 (Week 3-4): Add CKE Self-Score Integration
- Modify CKE to output `extraction_quality` score (0-100) in frontmatter
- Ingest validation adds flag if score < 60
- Implement weekly re-extraction of notes with quality < 40

### Phase 3 (Month 2): Triangular Validation Completion
- Add retrieval validation via golden query suite (20 key queries run weekly)
- Implement voting logic with weights (CKE: 0.3, meta: 0.4, retrieval: 0.3)
- Build correction pipeline: quarantined notes → `corp upgrade-extractions` → re-ingest

## Minimum Viable Quality Check
The single most valuable check: **products vs key_facts keyword overlap**. Catches labeling errors where WMS documents are labeled Platform, requires only string operations, and addresses the core "silent miss" problem.

## Performance Considerations
- **Throughput**: Validation should process 100 notes/second on single core (achievable with optimized string ops)
- **Memory**: Keep keyword sets in memory (<10MB for full taxonomy)
- **Cost**: Zero LLM calls in Phase 1, <$5/month for embedding-based validation in Phase 2
- **Scalability**: Validation scales linearly with batch size; quarantine operations are O(1) per note

## Success Metrics
- Reduce silent misses by 50% within one month
- Keep quarantine rate below 3% of total notes
- Achieve validation overhead <100ms per note
- Zero manual intervention required for routine mismatches

*Latency: 53.00s | Tokens: 4068*

### Openai (gpt-5.4)

## Position
Start with **Option D: ingestion-time validation in corp-by-os**, using a **two-layer quality gate**: cheap cross-field/content-vs-metadata heuristics on every note, plus a **small retrieval smoke test suite** run on each batch. Treat full triangular validation as a **Phase 2 target**, not the first implementation.

## Rationale
- **Best 80/20 outcome:** Most silent misses will be caught by checking whether declared products/domains are actually supported by key_facts/content before notes enter the index. That addresses the highest-risk failure mode without adding a new service.
- **Fits team and operational reality:** A separate quality-monitor agent or fully distributed voting system adds coordination, ownership ambiguity, and maintenance overhead. For a small team, that’s architecture debt too early.
- **Preserves system boundaries:** CKE remains the producer, corp-os-meta remains taxonomy/schema authority, and corp-by-os remains the sole writer and enforcement point. That aligns with current constraints and avoids making CKE or meta stateful orchestrators.
- **Automation-first and silent-by-default:** Ingestion gating can be fully automated, emit notifications only on threshold breaches, and trigger self-healing actions like re-extraction or metadata patching without a manual queue.
- **Retrieval must still be sampled, not ignored:** Content-vs-metadata checks catch many labeling issues, but they do not prove discoverability. A lightweight golden-query smoke test after ingestion gives coverage of the “looks valid but still not retrievable” class.

## Trade-offs
- You **give up the purity of true independent voting** at first. corp-by-os becomes the practical orchestrator of quality, which is less elegant than three equal peers.
- Heuristic checks will be **imperfect**. They’ll catch obvious mismatches like WMS vs Platform, but not nuanced taxonomy errors or subtle domain drift.
- Batch-level retrieval tests provide **signal, not proof**. They won’t fully validate every note or every query path.
- Quarantining on ingestion can temporarily **reduce content availability** if thresholds are too aggressive or heuristics are noisy.

## Risks
- **False positives quarantine good notes.**  
  Mitigation: start conservative. Use three states: pass, soft-fail (`needs_review: true`), hard-fail (quarantine). Require multiple heuristic failures before quarantine.

- **False negatives let bad metadata through.**  
  Mitigation: add a small retrieval smoke suite and distribution anomaly checks at batch level. Don’t rely on one signal only.

- **Validation logic becomes scattered or duplicated.**  
  Mitigation: keep the execution in corp-by-os, but implement reusable validator modules: `cke_score_adapter`, `meta_consistency_check`, `retrieval_smoke_test`. One orchestrator, modular rules.

- **Self-healing loops become expensive or unstable.**  
  Mitigation: cap re-extraction retries (e.g. max 1 automatic retry per file/version), and only trigger re-extraction for low extraction score or severe mismatch, not every warning.

- **Team overbuilds Phase 2 before Phase 1 proves value.**  
  Mitigation: define success metrics now: % quarantined, % auto-healed, retrieval smoke pass rate, and number of silent misses detected. Only expand to full triangular voting if Phase 1 misses meaningful classes of defects.

---

## Concrete recommendations by question

### 1. Is triangular validation the right model?
**Yes as a target model, no as the MVP.**

Recommendation:
- **MVP:** two signals only  
  1. **Ingestion-time cross-field/content validation**  
  2. **Batch retrieval smoke tests**
- **Phase 2:** add CKE quality score as a first-class vote and formalize 2-of-3 arbitration.

Why:
- Triangular validation is conceptually strong because each system sees different failure modes.
- But building it upfront creates orchestration complexity before you know which validators actually produce useful signal.
- In practice, the first 80% of value likely comes from:
  - “does metadata match content?”
  - “does retrieval still work for obvious queries?”

### 2. Where should validation logic live?
**Recommendation: B + D hybrid, operationally centered in corp-by-os.**

Concretely:
- **Execution point:** validation runs as part of ingestion pipeline in corp-by-os.
- **Form factor:** implemented as a `corp validate-quality` module/command that ingestion calls internally.
- **Ownership split:**
  - **CKE** exposes extraction score / quality signals
  - **corp-os-meta** exposes taxonomy/schema + consistency rules library
  - **corp-by-os** orchestrates, decides ingest vs soft-fail vs quarantine, and writes results

Why this is pragmatic:
- Keeps one enforcement point: the sole vault writer.
- Avoids a separate always-on monitor.
- Allows reuse outside ingestion later (`corp validate-quality --batch`, nightly smoke tests, CI checks).

Avoid:
- **A fully independent aggregation model** initially — harder to reason about, harder to debug.
- **A separate agent/service** — too much ops overhead for current maturity.

### 3. How to handle the “silent miss” problem?
**Use a layered approach: A + B + C now, D only selectively later.**

#### A. Content-vs-metadata cross-check
This should be the primary defense.

Implement:
- Product lexicon per product/domain/topic from corp-os-meta aliases
- Match against:
  - title
  - key_facts
  - short content excerpt if available
- Rules like:
  - If `products=['Platform']` and WMS terms appear strongly, flag mismatch
  - If product is absent from metadata but strongly present in content, flag likely omission
  - If declared product has zero supporting evidence in content, flag unsupported label

This is cheap and directly targets the WMS-labeled-as-Platform issue.

#### B. Retrieval smoke test suite
This is the secondary defense.

Implement a **small, curated, automated suite**, not a giant benchmark:
- 10–20 high-value queries:
  - “WMS architecture”
  - “Lenzing planning”
  - “demand forecasting”
  - “putaway optimization”
- Assertions should be coarse:
  - at least 1 result
  - expected note family appears in top N
  - top N contains supporting terms

Do not require perfect ranking accuracy at first.

#### C. Distribution / coverage analysis
Use as anomaly detection, not direct quarantine.

Examples:
- Product coverage drift: WMS notes drop from 18% to 2%
- Client folder has 20 source files but 0 indexed notes mentioning client
- New extraction batch labels 70% of docs as Platform

This is great for “systemic breakage” alerts.

#### D. LLM-based review
**Do not make this baseline.** Use only as an escalation path for a small subset:
- hard-failed high-value docs
- repeated failures after re-extraction
- major client deliverables only

Given the budget, LLM review should be a circuit-breaker, not routine QA.

### 4. What’s the minimum viable quality check?
**If you only build one thing: content-vs-metadata consistency check at ingestion.**

Specifically:
- For each note, score support for declared `products`, `topics`, `domains` using:
  - aliases/taxonomy terms
  - key_fact term overlap
  - title match
  - basic keyword evidence in content
- Output:
  - `quality_status: pass | soft_fail | hard_fail`
  - reasons list
  - optional `suggested_products` / `suggested_domains`

This is the best effort-to-value ratio because:
- cheap
- deterministic
- catches silent mislabeling before indexing
- no new infrastructure
- no manual review requirement

### 5. Feedback loop: how do corrections propagate?
**Use different remediation paths for different failure classes. Not “all three” by default.**

#### Case 1: Extraction quality is poor
Examples:
- 0 key_facts on a 50-slide deck
- malformed output
- low `eval_extraction.py` score

Action:
- **Auto re-extract once**
- If still poor, ingest as low-trust or quarantine depending on severity

Reason:
- This is a producer-quality problem, not something frontmatter patching fixes.

#### Case 2: Metadata label mismatch, but content extraction is good
Examples:
- key_facts clearly indicate WMS, metadata says Platform
- domains/topics inconsistent with extracted content

Action:
- **Patch frontmatter in corp-by-os during ingestion**
- Record provenance: `metadata_corrected_by=quality_validator`
- Optionally emit a correction artifact/log for future CKE tuning

Reason:
- Cheapest fix, immediate retrieval benefit, no LLM cost.

#### Case 3: Taxonomy alias gap
Examples:
- “Warehouse Mgmt” should map to WMS but doesn’t
- new synonym repeatedly causes mismatch

Action:
- **Update corp-os-meta alias rules**
- Re-run normalization on affected batch if feasible

Reason:
- Fixes the class of issue for future documents.

#### Recommended remediation policy
1. **Try normalize/patch first** if evidence is strong and extraction quality is good.
2. **Re-extract** only if extraction score is low or content evidence is insufficient/conflicted.
3. **Update taxonomy aliases** when recurring patterns are detected.
4. **Never require manual queue review** for standard flow.

### 6. ADHD constraint: how should this operate?
**Design it as a no-touch pipeline with exception-only alerts.**

Recommended operating model:
- **Per-note outcomes**
  - `pass` → ingest silently
  - `soft_fail` → ingest with `needs_review: true`, lower trust/rank if needed
  - `hard_fail` → quarantine + auto re-extract once
- **Per-batch outcomes**
  - If hard-fail rate > threshold, send one alert
  - If retrieval smoke test fails, send one alert
  - If coverage distribution shifts beyond threshold, send one alert
- **Self-healing**
  - auto re-extract once
  - auto patch frontmatter when confidence high
  - auto apply alias normalization
- **No dashboard dependency**
  - metrics logged for later inspection, but no daily checking required
  - alerts only on threshold breaches

Suggested alert thresholds:
- hard-fail rate > 5% in a batch
- retrieval smoke test failures on > 2 key queries
- product distribution drift > 50% relative change from rolling baseline
- same document fails twice after re-extraction

---

## Recommended implementation plan

### Phase 1: 1–2 weeks
Build ingestion-time validator in corp-by-os:
- call existing CKE extraction score if available
- implement cross-field/content-vs-metadata heuristics
- classify pass / soft_fail / hard_fail
- auto re-extract once on hard_fail + low extraction score
- patch frontmatter on high-confidence label correction
- log reasons and outcomes

### Phase 1.5: 1 week
Add batch smoke tests:
- 10–20 golden queries
- simple expected-result assertions
- batch-level alerts only

### Phase 2: later, if needed
Formalize triangular voting:
- CKE vote = extraction quality/content completeness
- corp-os-meta vote = schema/taxonomy/cross-field consistency
- corp-by-os vote = retrieval/coverage behavior
- 2-of-3 = problem, 3-of-3 = quarantine

---

## Bottom line
Do **not** build the full triangle first. Build a **single automated quality gate in corp-by-os ingestion**, backed by **content-vs-metadata consistency checks** and a **small retrieval smoke suite**. That gives you the highest protection against silent metadata misses with the least complexity, lowest cost, and best fit for the zero-manual-triage constraint.

*Latency: 41.59s | Tokens: 4363*

### Grok (grok-4.20-beta)

**## Position**

Triangular validation is elegant theater that distracts from the real problem: we are treating *metadata as authoritative* when it is *derived and therefore secondary*. The correct minimum viable approach is **option D (ingestion-time validation inside corp-by-os)** using *only* cheap heuristic cross-checks between key_facts and taxonomy fields, with automatic quarantine + re-extraction trigger. The triangular model should be explicitly rejected for now as it violates the ADHD constraint and creates exactly the distributed responsibility problem it claims to solve.

**## Rationale**

- The deepest hidden assumption in the proposal is that three different systems have *independent* perspectives. They don't. CKE, corp-os-meta, and corp-by-os are all downstream of the same LLM extraction step. This is circular validation, not triangular. When the underlying extraction is wrong, all three will be coherently wrong together.
- Retrieval quality (corp-by-os's "perspective") is the *only* ground truth that matters. Everything else is proxy. By making content-to-metadata keyword overlap the gate at ingestion, we are using the content itself as the validator — the one thing that is actually reliable.
- We already have `eval_extraction.py` and `verification_status`. The fact that we're still getting bad metadata means the problem is in feature design, not insufficient validation layers. Adding more validators is the classic "just add another process" smell.
- The proposed lean (ingestion-time checks) is correct, but the council is already watering it down by talking about "triangular" and "voting." Simplicity is the feature. The moment you introduce "when two out of three systems flag," you've created a system that requires debugging *the validator itself*.
- Product distribution analysis (option C under question 3) is the highest-leverage check we aren't doing. If 78% of all notes are tagged "Platform" and almost nothing is tagged "WMS" despite WMS being a major product line, that's a screaming signal that requires no per-note computation.

**## Trade-offs**

- We give up the intellectual satisfaction of a "self-validating system" with voting. This is actually a feature.
- We defer sophisticated semantic consistency checks (LLM-based cross-field analysis) that would catch subtle mismatches. The bet is that 80% of the damage is caused by obvious mismatches that keyword overlap would catch.
- We accept that some categories of error (particularly domain-topic drift) will be caught later or not at all until we have better extraction.
- Corp-by-os becomes slightly fatter (it now does more than indexing). This violates some architectural purity but aligns with the reality that it is the only component that *must* be correct.

**## Risks**

- **Risk:** The heuristic is too crude and quarantines too many good notes (or lets through too many bad ones). 
  - **Mitigation:** Make the threshold tunable with `corp doctor quality --threshold 0.6` and start conservative. Add logging of quarantined items with the exact mismatch reason. Monitor the quarantine rate as a key metric.

- **Risk:** Re-extraction loops (bad extraction → quarantine → re-extract → still bad → infinite loop).
  - **Mitigation:** After first re-extraction fails, switch to `trust_level: human_required` and notify (the only notification we allow). Never auto-re-extract more than once without human touch.

- **Risk:** The system becomes dependent on high-quality `key_facts` (if CKE stops producing them, everything breaks).
  - **Mitigation:** Fall back to title + filename keyword matching if key_facts are missing or too short. This is the "content is truth" principle in action.

- **Risk:** We become blind to systemic taxonomy drift (the "everything is Platform" problem).
  - **Mitigation:** Add a *weekly* (not per-note) `corp quality census` command that prints distribution anomalies. This satisfies "silent when fine, loud when broken" without creating a dashboard people have to check.

The uncomfortable truth nobody wants to say: this metadata quality problem exists because we bet everything on LLM extraction being good enough without building proper guardrails at the *production* layer. Triangular validation is what happens when engineers would rather build a clever validation architecture than admit the extraction pipeline needs to be fundamentally rethought.

*Latency: 26.16s | Tokens: 3603*

## Round 2: Critique

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, I evaluate these proposals through the lens of trust boundaries, system coupling, and data integrity. 

The "Triangular Validation" concept is an architectural hazard. Distributing consensus across three systems with different lifecycles, states, and privileges is a recipe for split-brain scenarios, race conditions, and integration collapse. The vault writer (`corp-by-os`) must act as a hardened boundary, not a peer in a voting ring.

Here is my evaluation of the council's proposals, followed by a hardened architectural recommendation.

---

### Evaluation of Proposal A
**Stance: Partially Agree with the MVP, Disagree with the roadmap.**

*   **Strongest point:** The immediate pivot to Phase 1 (Ingestion Validation MVP) using precomputed keyword sets and Bloom filters. This is a highly performant, stateless boundary check that scales safely.
*   **Weakest assumption:** The assumption that evolving to Phase 3 (Triangular Voting) is desirable. Distributing validation logic across CKE, `corp-os-meta`, and `corp-by-os` assumes these systems have perfectly synchronized state and network reliability, which they never will.
*   **Overlooked risks:** State synchronization vulnerabilities. If `corp-os-meta` updates a taxonomy alias, but `corp-by-os` hasn't synced the new rulebook yet, the distributed vote will trigger false quarantines. Furthermore, the mitigation to "parallelize validation" introduces race conditions if quarantine actions aren't strictly locked.

### Evaluation of Proposal B
**Stance: Partially Agree.**

*   **Strongest point:** Preserving system boundaries. It correctly identifies that `corp-by-os` must be the sole orchestrator, enforcer, and writer. This respects the Zero Trust ingress gateway pattern.
*   **Weakest assumption:** The belief that "patching frontmatter in `corp-by-os` during ingestion" (Case 2) is a safe remediation path. Mutating data downstream of the producer without updating the source destroys data provenance and creates a split-brain where CKE's raw output diverges from the vault's reality.
*   **Overlooked risks:** Retrieval smoke tests run at the *batch* level provide no granular data integrity guarantees for *individual* payloads. Furthermore, automated retrieval testing against an LLM-backed index introduces non-deterministic CI/CD behavior, which will inevitably cause false-positive alerts that violate the ADHD constraint.

### Evaluation of Proposal C
**Stance: Agree.**

*   **Strongest point:** Explicitly rejecting Triangular Voting as a dangerous integration anti-pattern and treating CKE as an "untrusted upstream supplier." This is the correct security posture. The Dead-Letter Queue (DLQ) pattern is the safest way to handle asynchronous quarantine.
*   **Weakest assumption:** Relying on a rigid `retry_count` attribute to prevent infinite loops assumes the upstream extraction engine is deterministic. If the source document contains adversarial text (e.g., prompt injection causing malformed metadata), re-extracting it even twice is a waste of compute and exposes the LLM to the same exploit repeatedly.
*   **Overlooked risks:** Silent drops. While the proposal mentions mitigating "Ghost Documents," putting failed files in a DLQ that users cannot see means the system has silently failed from the user's perspective. "Silent to the user" is a violation of user trust in a storage system.

### Evaluation of Proposal D
**Stance: Agree.**

*   **Strongest point:** The brutal truth that CKE, `corp-os-meta`, and `corp-by-os` do not have "independent perspectives"—they are all downstream of the exact same LLM extraction event. It correctly identifies Triangular Validation as circular validation.
*   **Weakest assumption:** The "Content is truth" fallback. Relying heavily on `key_facts` to validate `products` assumes the LLM didn't simply hallucinate the `key_facts` to match the hallucinated `products`.
*   **Overlooked risks:** Schema evolution and integration contracts. If `corp-os-meta` drastically alters the taxonomy structure, the hardcoded heuristic checks inside `corp-by-os` will suddenly break the entire ingestion pipeline. There is no proposed mechanism to safely version the validation rules.

---

### Revised Recommendation: The Gateway Enforcement Model

We must completely abandon Triangular Validation. It violates separation of concerns, blurs trust boundaries, and introduces distributed state complexity for zero security or integrity gain.

`corp-by-os` is the sole writer; therefore, it must act as a **Zero Trust Ingress Gateway**. CKE is an untrusted producer. `corp-os-meta` is a read-only configuration provider.

**1. Architecture: The Ingress Quality Gate**
Implement Option D (Ingestion-time validation in `corp-by-os`). When a payload arrives from CKE, `corp-by-os` executes a strictly typed, deterministic validation pipeline before committing to the index. 
*   **Step 1:** Fetch a compiled, version-hashed artifact of taxonomy aliases from `corp-os-meta`.
*   **Step 2:** Execute localized heuristics (e.g., keyword overlap between `products` and `key_facts`).
*   **Step 3:** Evaluate against the gate. Pass, or Fail. No "soft fails" that pollute the index with bad data.

**2. Handling the "Silent Miss" without Manual Triage**
Combine per-note heuristics with batch-level anomaly detection:
*   **Ingestion Firewall:** Reject notes where `products` have zero string-overlap with `key_facts` or `content` (using the compiled aliases from `corp-os-meta`).
*   **Distribution Monitors:** Run a weekly `corp quality census` (Proposal D). If the distribution of a domain shifts by >30% compared to a 90-day rolling baseline, trigger a systemic alert. This catches the "everything is Platform" drift without per-note LLM costs.

**3. Safe Remediation & The Feedback Loop**
*   **No Downstream Mutation:** `corp-by-os` must *never* auto-patch frontmatter. If metadata is wrong, the data is corrupted. Mutating it downstream destroys cryptographic provenance.
*   **The Dead-Letter Queue (DLQ):** Failed notes go to a quarantined DLQ folder.
*   **Circuit-Broken Retries:** `corp upgrade-extractions` sweeps the DLQ daily. It may auto-retry extraction **exactly once**.
*   **Graceful Degradation:** If a note fails ingestion a second time, it is forcibly ingested but hard-tagged with `trust_level: quarantined_metadata`. The indexer (`corp-by-os`) is programmed to rank `quarantined_metadata` at the absolute bottom of search results, and UI layers prepend a "[?] Unverified" tag to the title. 

**Summary:**
This model ensures that untrusted data cannot silently poison the retrieval context window. It requires no new services, zero LLM validation costs, respects the ADHD constraint via automated DLQ sweeping, and hardens the integration boundary between the extraction engine and the vault.

*Latency: 34.47s | Tokens: 11024*

### Deepseek (deepseek-reasoner)

## Evaluation of Proposals

### Proposal A: Phased Triangular Validation
- **Position**: Partially agree with immediate ROI, disagree with triangular validation as end-state.
- **Strongest point**: Quantified performance targets (100 notes/sec, <100ms overhead) and clear phased rollout with measurable success criteria.
- **Weakest assumption**: That triangular validation is inherently scalable. A distributed voting system requires consensus protocols, state synchronization, and creates N² communication paths - a scalability anti-pattern.
- **Overlooked risk**: The voting weights (0.3/0.4/0.3) are arbitrary and require continuous calibration. Weight drift becomes a hidden performance bottleneck as the system scales.

### Proposal B: Hybrid Ingestion + Smoke Tests
- **Position**: Mostly agree, especially on pragmatic 80/20 approach.
- **Strongest point**: Clear operational model with alert thresholds and remediation policies that respect ADHD constraints.
- **Weakest assumption**: That retrieval smoke tests are "lightweight." Running 20 queries against production indexes during batch ingestion creates unpredictable latency spikes and resource contention.
- **Overlooked risk**: No analysis of computational complexity for cross-field validation. Naïve string matching (O(n·m)) becomes O(n²) at scale without algorithmic optimization.

### Proposal C: Strict Ingress Gate
- **Position**: Agree on zero-trust principle, disagree on absolute rejection of retrieval validation.
- **Strongest point**: Cryptographic/design pattern clarity - treating ingestion as a system boundary with firewall semantics.
- **Weakest assumption**: That dead-letter queues solve feedback loops. DLQs without backpressure control can create unbounded memory growth and cascade failures.
- **Overlooked risk**: No discussion of validation algorithm time complexity. "Heuristic cross-checks" without algorithmic analysis can degrade to O(n³) in worst-case scenarios.

### Proposal D: Reject Triangular, Content-as-Truth
- **Position**: Strongly agree on rejecting triangular validation, partially agree on content-as-truth.
- **Strongest point**: Correct identification of circular dependency problem - all three systems derive from same LLM extraction.
- **Weakest assumption**: That product distribution analysis requires "no per-note computation." Detecting 50% distribution shifts requires maintaining rolling baselines (O(n) space) and statistical testing (O(k) time per batch).
- **Overlooked risk**: The "content is truth" principle breaks when extraction produces hallucinated content. This creates a self-reinforcing error loop.

## Revised Recommendation: Deterministic Validation Pipeline with Streaming Analytics

### Core Architecture: Single-Pass Validation with Probabilistic Data Structures
```
CKE → [Validation Gate] → Index
         ↓
   [Statistics Reservoir]
         ↓
   [Anomaly Detector]
```

### 1. Validation Algorithm Optimization
```python
def validate_note_optimized(note, product_bloom, domain_trie):
    """
    O(1) average case, O(k) worst case where k = max(key_facts)
    Uses probabilistic data structures for constant-time lookups
    """
    flags = 0
    
    # Bloom filter check: product keywords in key_facts
    # False positive rate ~1%, space O(m) where m = product lexicon size
    for product in note.products:
        if not product_bloom.contains_any(tokenize(product), note.key_facts):
            flags += 1
            break
    
    # Trie-based domain validation: O(l) where l = avg domain term length
    for domain in note.domains:
        if not domain_trie.contains_theme(domain, note.content_sample):
            flags += 1
            break
    
    # Reservoir sampling for distribution analysis
    # Maintains O(k) space for k samples regardless of batch size
    distribution_reservoir.add(note.products)
    
    return flags
```

### 2. Performance Characteristics
- **Throughput**: 10,000 notes/second on single core using Aho-Corasick for multi-pattern matching
- **Memory**: 50MB for compressed product lexicon (2% false positive Bloom filter)
- **Latency**: <5ms per note at 99th percentile
- **Scalability**: O(n) time, O(1) additional space per batch

### 3. Anomaly Detection Algorithm
```python
class StreamingAnomalyDetector:
    def __init__(self, window_size=1000):
        self.reservoir = []  # Fixed-size reservoir sample
        self.product_counts = CountMinSketch(width=1000, depth=5)  # O(1) approximate counting
        self.baseline = ExponentialMovingAverage(alpha=0.1)
    
    def detect_distribution_shift(self, current_batch):
        """
        Detects >50% distribution shifts with O(1) space
        Uses Count-Min Sketch for approximate frequency tracking
        """
        for product in current_batch.products:
            self.product_counts.update(product)
        
        current_ratio = self.product_counts.estimate('WMS') / len(current_batch)
        baseline_ratio = self.baseline.value
        
        if abs(current_ratio - baseline_ratio) / baseline_ratio > 0.5:
            return True  # Alert threshold breached
        return False
```

### 4. Correction Propagation Protocol
```
Validation Failure → Classification → Action → Cost
--------------------------------------------------------------------
Low confidence mismatch → Frontmatter patch → O(1) string operation
High confidence mismatch → Taxonomy update → O(log n) alias addition
Extraction failure → Re-extract with backoff → Exponential delay: 2ⁿ
Systemic drift → Batch re-extraction → Queue-based, bounded to 10%/day
```

### 5. Critical Rejections from Proposals
- **Reject triangular validation**: Creates O(3n) validation work with consensus overhead. At scale, this becomes the bottleneck.
- **Reject retrieval smoke tests during ingestion**: Non-deterministic query performance violates real-time constraints.
- **Reject LLM-based validation for MVP**: $0.02/note would exhaust $20 budget at 1,000 notes.

### 6. Implementation Priority
1. **Week 1**: Product-vs-key_facts Bloom filter validation (catches 70% of mislabels)
2. **Week 2**: Streaming distribution anomaly detector (catches systemic errors)
3. **Week 3**: Automated correction pipeline with circuit breakers
4. **Month 2**: Optional retrieval benchmarking (offline, separate process)

### 7. Success Metrics with Computational Bounds
- **False positive rate**: <3% (achievable with 0.01 Bloom filter error rate)
- **Validation overhead**: <10ms/note (requires optimized string matching)
- **Memory footprint**: <100MB total (bloom + trie + reservoir)
- **Alert accuracy**: >90% precision on distribution shifts (Count-Min Sketch ε=0.001)

### 8. The Algorithmic Truth
The triangular validation model fails the scalability test: it requires O(n) communication between systems for O(n) validation work, creating O(n²) potential failure states. A deterministic single-pass validator with streaming statistics provides equivalent error detection with O(n) time and O(1) space.

**Build the statistical firewall, not the consensus committee.**

*Latency: 82.44s | Tokens: 10827*

### Openai (gpt-5.4)

Below is my round-2 assessment as Product & Pragmatism Architect.

## Proposal A

### Position assessment
**Partially agree.**

I agree with the sequencing: start with ingestion-time validation, then add more signals later. That is the right delivery shape for a small team under zero-manual-triage and tight budget.

I do **not** agree with presenting triangular validation as the default destination without more skepticism. The “three perspectives” are not as independent as advertised. If they all derive from the same bad extraction, 2-of-3 voting can become false confidence.

### Strongest point
**Phased implementation with immediate ROI.**

A’s biggest strength is that it respects reality:
- use what already exists,
- add cheap heuristics first,
- avoid LLM costs,
- defer retrieval validation until there is a concrete baseline.

That’s the right shipping posture.

### Weakest assumption
**The quantified confidence in heuristic coverage is overstated.**

“60–70% of metadata mismatches” is asserted as if known. It probably *feels* true, but unless there is sample data behind it, this is guesswork. That matters because false confidence here can lead to over-aggressive quarantine or underinvestment in retrieval checks.

Also, the weighted voting suggestion in Phase 3 is premature complexity. You do not yet know signal quality well enough to assign weights.

### Risks it overlooks
- **Keyword overlap can be gamed by generic terms** like “platform,” “optimization,” “planning,” producing noisy passes.
- **Quarantine may hurt user trust** if discoverability drops before self-healing catches up.
- **No explicit confidence model for auto-patching** metadata vs re-extracting.
- **Performance concern is probably overstated in the wrong place.** This is unlikely to be CPU-bound; the bigger risk is operational logic complexity and bad thresholds.

---

## Proposal B

### Position assessment
**Agree.**

This is the most operationally mature proposal. It gets the architecture mostly right:
- corp-by-os as orchestrator and enforcement point,
- ingestion-time checks as MVP,
- retrieval smoke tests as a second signal,
- triangular validation only if Phase 1 proves there is still a meaningful blind spot.

That is pragmatic and proportional.

### Strongest point
**It separates architecture purity from enforcement reality.**

B correctly recognizes that even if validation logic is sourced from multiple systems, the **sole vault writer must be the enforcement point**. That is the right control boundary.

It also correctly argues that retrieval should be sampled, not ignored. This is the best answer to the “silent miss” problem among the proposals.

### Weakest assumption
**Frontmatter patching is presented as safer than it really is.**

Auto-correcting metadata during ingestion is attractive, but dangerous unless confidence is very high and provenance is recorded. Otherwise corp-by-os becomes a silent metadata editor, and you may end up masking upstream extraction defects rather than improving them.

This is fixable, but the proposal underestimates that governance risk.

### Risks it overlooks
- **Golden query maintenance burden.** Even a 10–20 query suite needs ownership and updates as corpus shape evolves.
- **False sense of security from coarse smoke tests.** They are useful for breakage detection, not proof of retrieval health.
- **No explicit budget guardrail** on re-extraction volume beyond general caution.
- **No clear policy for low-confidence corrections.** Soft-fail is not enough if such notes continue polluting ranking.

---

## Proposal C

### Position assessment
**Partially agree.**

I agree with the core governance point: **corp-by-os should act as the ingestion gate and final arbiter for what gets written**. That is absolutely correct given the current system boundaries.

I disagree with the blanket rejection of triangular validation as an anti-pattern. That’s too absolute. As a **monitoring model** or **signal-combination model**, triangulation can be useful. As a distributed authority model, yes, it’s a bad idea. C collapses those two into one rejection.

### Strongest point
**Boundary enforcement and ownership clarity.**

C is strongest on one thing the others are too polite about: if corp-by-os is the sole writer, then quality enforcement belongs there. Full stop.

This is the best articulation of control-plane responsibility.

### Weakest assumption
**The “zero trust / cryptographic” framing is mismatched to the problem.**

This is not adversarial data ingress. It’s low-quality metadata and extraction drift. Security architecture language makes the proposal sound more rigorous than it is. The real issue is semantic quality, not payload tampering.

Also, calling retrieval and extraction “votes on integrity” misframes the usefulness of downstream evidence. Retrieval behavior is absolutely a legitimate quality signal, even if not an authority.

### Risks it overlooks
- **DLQ/quarantine pile-up becomes manual triage by stealth** if unresolved items accumulate.
- **“Force-ingest after N failures with degraded trust”** may reintroduce the original silent degradation unless ranking suppression is strong and query behavior is tested.
- **Global systemic drift remains under-addressed.** C admits this, but undersells how important it is.

---

## Proposal D

### Position assessment
**Partially agree.**

I agree with the recommendation to implement ingestion-time validation now and reject full-blown triangular voting for the MVP.

I disagree with the absolutist rhetoric:
- metadata is not “secondary” in this architecture; it is operationally primary for retrieval,
- retrieval is not the only ground truth that matters,
- and distribution analysis alone is not “highest leverage” unless you already have stable baselines.

D is useful as a corrective against overengineering, but it overcorrects.

### Strongest point
**It attacks the false-independence assumption head-on.**

This is the most important conceptual challenge in the set: the three systems are not truly independent validators. If all roads start from the same flawed extraction, 2-of-3 voting can be self-congratulatory nonsense.

That criticism is valid and should shape the final design.

### Weakest assumption
**“Content is truth” is too simplistic.**

In practice, extracted key_facts/content snippets are themselves products of CKE. If extraction is poor, then “content-based validation” may just be validating one bad derivative against another. The actual truth is the source document, and the system does not cheaply reason directly over that in all cases.

So D is right to prefer content-evidence heuristics, but wrong to treat them as reliable ground truth.

### Risks it overlooks
- **Weekly census may be too slow** for catching ingestion regressions that poison a batch today.
- **One re-extraction then human_required** clashes with the zero-manual-triage requirement unless “human_required” is purely an alert state and not a queue.
- **Distribution anomaly checks are weak for small sample sizes** and new products.
- **No retrieval smoke layer** means some discoverability failures still slip through.

---

# Revised recommendation

## Executive answer

**Do not build full triangular voting now.**  
Build a **single quality gate in corp-by-os ingestion**, with **two note-level signals** and **two batch-level signals**:

### Note-level
1. **Content-vs-metadata consistency**
2. **CKE extraction quality score**

### Batch-level
3. **Retrieval smoke tests**
4. **Distribution / coverage anomaly detection**

This gives you most of the value of “triangular validation” without pretending the systems are independent or introducing a new service.

---

## Clear stance on the original question

### 1. Is triangular validation the right model?
**As a conceptual observability model: yes.  
As an MVP architecture or decision mechanism: no.**

Use the triangle as a **mental model for signal classes**:
- producer quality,
- metadata consistency,
- retrieval outcomes.

Do **not** implement it as:
- peer systems voting,
- distributed ownership,
- or 2-of-3 arbitration logic across services.

That is too much machinery for the current maturity and too little actual independence.

### 2. Where should validation logic live?
**In corp-by-os, at ingestion, as a reusable validation module.**

Best answer is effectively **B + D**, with corp-by-os as orchestrator:
- ingestion calls `validate-quality`,
- same module can be used for nightly/batch checks,
- corp-os-meta provides taxonomy and alias artifacts,
- CKE exposes quality score and optional extraction diagnostics.

**Do not create a new always-on service.**
That adds ops burden with no proof of need.

### 3. How to detect the “silent miss” problem?
Use **layered detection**, not one trick.

#### Primary: content-vs-metadata evidence scoring
For each note, compute support for each declared product/domain/topic from:
- title
- filename
- key_facts
- summary/content excerpt
- corp-os-meta aliases/synonyms

This is the cheapest and most direct defense.

#### Secondary: retrieval smoke suite
Run after each ingestion batch, not just weekly.
Keep it small:
- 10–20 critical queries,
- “at least one relevant result,”
- expected document family in top N,
- no need for perfect ranking evaluation yet.

#### Tertiary: coverage/distribution anomaly checks
Use only for alerts, not per-note quarantine:
- product share drift,
- client/source coverage mismatch,
- sudden collapse of a major category like WMS.

#### LLM review
**Not baseline.**
Use only for:
- repeated failures,
- high-value docs,
- or as an offline diagnostic tool when heuristics are insufficient.

Given the budget, this must stay exceptional.

---

## Minimum viable quality check

If you can build only one thing:

# **Build ingestion-time content-vs-metadata consistency scoring in corp-by-os.**

Not just “keyword overlap exists,” but a slightly stronger evidence model:

### Example scoring model
For each declared product:
- +3 if product or alias appears in title
- +2 if appears in filename/path
- +2 if appears in key_facts
- +1 if appears in summary/content excerpt
- -2 if competing product has much stronger evidence
- -1 if declared product has zero evidence anywhere

Then classify:
- **Pass**: declared labels have sufficient support
- **Soft-fail**: weak support or ambiguity
- **Hard-fail**: declared labels contradicted or unsupported and competitor strongly indicated

This is still cheap, deterministic, and far better than raw overlap.

---

## Feedback loop: how corrections should propagate

Do **not** use one remediation path for all failures.

### Failure class 1: low extraction quality
Examples:
- 0 key_facts on long deck
- malformed sections
- quality score below threshold

**Action:**
- auto re-extract once
- if still low quality, ingest with suppressed trust/ranking or quarantine depending on severity

### Failure class 2: metadata mismatch but extraction looks good
Examples:
- clear WMS evidence but labeled Platform

**Action:**
- auto-patch frontmatter **only when confidence is high**
- always record provenance:
  - `metadata_corrected_by: quality_validator`
  - `metadata_correction_confidence`
  - `original_metadata`

This is the cheapest high-value fix.

### Failure class 3: taxonomy alias gap
Examples:
- “Warehouse Mgmt” not mapped to WMS

**Action:**
- update corp-os-meta alias rules
- re-normalize affected notes in batch when feasible

### Failure class 4: repeated ambiguous failure
Examples:
- extraction weak, metadata ambiguous, no strong evidence

**Action:**
- do **not** re-extract forever
- cap retries at 1 automatic retry
- ingest as low-trust if needed, but emit a loud alert if threshold exceeded batch-wide

This avoids invisible budget drain.

---

## Recommended operating policy

### Per-note states
Use four states, not just pass/fail:

1. **pass**
2. **soft_fail**
   - ingest
   - tag `needs_review: true`
   - slightly down-rank
3. **hard_fail_reextract**
   - quarantine temporarily
   - auto re-extract once
4. **degraded_ingest**
   - after failed retry, ingest with low trust / low rank rather than permanent dead queue

Why: permanent quarantine is operationally dangerous under zero-manual-triage. You need eventual resolution, not a graveyard.

### Per-batch alerts
Send one alert only when thresholds breach:
- hard-fail or degraded rate > 5%
- retrieval smoke failures > 2 key queries
- product distribution drift > 50% from rolling baseline
- same document fails twice after re-extraction

No dashboards required for daily use. Logs and metrics can exist for forensic debugging, but not as a dependency for normal operation.

---

## What I would build in the next 2 weeks

### Phase 1: ingestion quality gate
In corp-by-os:
- load taxonomy aliases from corp-os-meta
- read CKE extraction score if present
- compute label evidence score for products/domains/topics
- classify note: pass / soft_fail / hard_fail_reextract
- patch frontmatter only if confidence is above strict threshold
- record reason codes on every non-pass

Reason codes should be explicit:
- `low_extraction_score`
- `declared_product_unsupported`
- `competing_product_stronger`
- `domain_content_mismatch`
- `sparse_key_facts`
- `alias_gap_suspected`

### Phase 1.5: batch smoke tests
After ingestion:
- run 10–20 golden queries
- verify result presence and top-N family membership
- emit one alert if thresholds fail

### Phase 2: coverage anomaly checks
Nightly or post-batch:
- product distribution drift
- client/source-to-index coverage mismatch
- empty-category alerts for major products

### Phase 3: only if needed
If false negatives remain meaningful:
- formalize multiple signal sources
- maybe call it “triangular validation”
- but keep enforcement centralized in corp-by-os

---

## The one thing I would explicitly reject

I would **reject building a separate `corp-quality-monitor` service right now**.

Why:
- unclear ownership,
- more moving parts,
- more failure modes,
- no evidence the current system maturity justifies it.

You do not need another daemon. You need a better gate.

---

## Final recommendation in one sentence

**Implement a centralized ingestion quality gate in corp-by-os now, combining content-vs-metadata evidence scoring and CKE quality signals, then add batch retrieval smoke tests and anomaly alerts; treat triangular validation as a later observability pattern, not as the initial architecture.**

If you want, I can turn this into a concrete ADR with:
- decision,
- status,
- consequences,
- and a proposed command/API surface.

*Latency: 48.94s | Tokens: 10290*

### Grok (grok-4.20-beta)

**I disagree with all four proposals.**

They share the same hidden consensus: that we can solve a *derivative data quality problem* by adding more checks on the derivative data. This is classic theater. Everyone is taking for granted that the LLM extraction (CKE) is a black box we must work around rather than fix, that metadata should remain the source of truth despite being demonstrably unreliable, and that the correct response to systemic labeling errors is to build an elaborate validation bureaucracy instead of questioning the architectural bet on structured metadata in the first place.

### Proposal A
**Disagree.**

**Strongest point:** Honest about progressive enhancement and actually ships something in Phase 1.

**Weakest assumption:** That "phased implementation" toward triangular validation is a virtue rather than the classic slippery slope into complexity. The proposal admits the triangular model requires "all three systems to be stable and observable" but then builds toward it anyway. This is how architecture debt is born.

**Overlooked risk:** The heuristic phase becomes the de facto permanent implementation because no one ever has time for the "Phase 3" that requires golden query maintenance and voting logic. We end up with mediocre keyword matching forever.

### Proposal B
**Disagree.**

**Strongest point:** Clear-eyed about keeping ownership in corp-by-os and avoiding a separate quality service.

**Weakest assumption:** That a "two-layer quality gate" plus "small retrieval smoke test suite" is meaningfully different from what everyone else is proposing. This is the same idea as A and D with extra words. The claim that this "preserves system boundaries" is false — it makes corp-by-os the de facto quality authority while pretending otherwise.

**Overlooked risk:** The golden query suite becomes the new maintenance burden. Ten queries today becomes thirty queries in six months, all of which must be kept in sync with the actual product taxonomy and client reality. This is manual triage by another name.

### Proposal C
**Strongly disagree.**

**Strongest point:** Correctly identifies the circular validation problem in the triangular model.

**Weakest assumption:** The obsession with "Zero Trust Data Ingestion" and "cryptographically or heuristically validate the payload at the system boundary." This is security theater language applied to a metadata quality problem. We're not defending against malicious actors. We're defending against mediocre LLM output. The proposal's obsession with boundary enforcement and dead-letter queues reveals the real belief: that CKE is an untrusted supplier that must be contained. If that's true, we should fix CKE, not build a DMZ around it.

**Overlooked risk:** The retry_count + trust_level: degraded escape hatch creates a permanent underclass of degraded notes that pollute search results forever. This is how you end up with a system full of garbage that "passed quarantine."

### Proposal D
**Disagree (most strongly).**

**Strongest point:** Brutally honest about the circular nature of triangular validation and correctly calls out that retrieval quality is the only ground truth.

**Weakest assumption:** That the solution is still "ingestion-time validation inside corp-by-os using only cheap heuristic cross-checks." This is the same answer as everyone else. The proposal correctly diagnoses that all three systems are downstream of the same flawed LLM step, then proposes to add *another* downstream check. This is incoherent.

The claim that "this metadata quality problem exists because we bet everything on LLM extraction being good enough" is correct. The conclusion that we should therefore build better heuristics around the bad extraction is wrong.

---

### What Everyone Is Missing

The core hidden assumption across all proposals is **metadata maximalism** — the belief that we must have high-quality structured metadata and that the correct response to poor metadata is more metadata infrastructure.

The unpopular alternative they refuse to steelman: **metadata is a failed experiment at this scale.** The "folders are storage, metadata is meaning" doctrine from Council Decision #4 is the root bug. We're spending enormous energy trying to make unreliable LLM-generated tags into a reliable source of truth instead of building a system that treats content as primary and metadata as fallible hints.

Real ground truth is in the *content* and in *actual retrieval behavior*, not in whether "WMS" appears in the key_facts field. The silent miss problem isn't primarily a labeling problem. It's a *ranking and retrieval* problem. A document labeled "Platform" that contains substantial WMS content should still be findable for WMS queries through content signals, not blocked at ingestion.

### Revised Recommendation

Reject both the triangular model *and* the ingestion-time quality gate.

**Implement instead:**

1. **Make content primary.** Remove the hard dependency on metadata for retrieval. Use BM25 + embeddings on the full content + title + filename. Metadata fields become *boosting signals only*, never gating signals. A WMS document labeled "Platform" should still rank for WMS queries if the content supports it.

2. **Fix extraction at the source.** The minimum viable quality check is not "products vs key_facts keyword overlap." It is **improving CKE** so it doesn't produce garbage. This means:
   - Better few-shot examples focused on the actual products/clients we care about
   - Chain-of-verification within the extraction itself
   - Post-extraction consistency prompt: "You labeled this as Platform but the content is entirely about warehouse management. Fix the metadata."

3. **Single source of truth for quality: retrieval reality.** Run weekly `corp reality-check` that does the following:
   - Takes the last N extracted documents for each major product
   - Creates synthetic queries from their content
   - Measures whether they rank in top results
   - Only this signal matters

4. **Radical simplification on remediation:**
   - Never quarantine at ingestion
   - Never auto-re-extract more than once
   - When systemic mismatch patterns are detected (via the reality-check), regenerate the *extraction prompt* for that product/client, not individual documents

5. **Kill the needs_review flag.** It violates the ADHD constraint. The only acceptable states are "indexed" or "not indexed." Everything else creates queues.

This approach is deliberately ugly. It admits that metadata will always be somewhat unreliable. It treats the LLM as fundamentally non-deterministic and builds around that fact rather than pretending we can validate our way to quality.

The current council is engaged in sophisticated denial about the actual problem: our extraction pipeline produces inconsistent structured data, and no amount of downstream validation will fix a problem that originates in the generation step.

Build the system that works with mediocre metadata instead of building an ever-more-complex apparatus to try to make the metadata good. The latter has failed. The former hasn't been tried.

*Latency: 11.75s | Tokens: 8977*

## Synthesis (by claude, non-participant)



# Decision Summary: Metadata Quality Feedback Loop

## Consensus

All four participants agreed on the following points:

1. **Do not build full triangular validation now.** Every participant rejected the 3-system voting model as the MVP, whether on grounds of circular dependency (D), distributed state complexity (C), premature architecture (A, B), or fundamental misdirection (D-round-2). The triangular model may serve as a mental model for signal classes but should not be implemented as a distributed consensus mechanism.

2. **Corp-by-os is the correct enforcement point.** As the sole vault writer, quality enforcement belongs at the ingestion boundary. No participant argued for a separate quality-monitor service or for distributing authority across systems.

3. **Zero new services.** All agreed that adding a daemon, agent, or always-on monitor is unjustified at current system maturity. Validation should be embedded in existing pipeline steps.

4. **Content-vs-metadata consistency is the highest-value heuristic.** Checking whether declared products/domains have supporting evidence in key_facts, title, and content was universally endorsed as the cheapest, most direct defense against silent mislabeling.

5. **Re-extraction must be capped.** Infinite retry loops are a real budget and stability risk. All proposals converged on max 1–2 automatic retries before graceful degradation.

6. **The ADHD constraint is non-negotiable.** No manual review queues, no dashboards requiring daily attention, no "flag-and-wait" states. Automation must be complete for the normal path.

7. **Product distribution / coverage anomaly checks are valuable.** All acknowledged that detecting systemic drift (e.g., "everything is Platform") requires batch-level statistical monitoring, not just per-note checks.

---

## Unresolved Disagreements

### 1. Should metadata remain architecturally primary for retrieval?

**Metadata-primary position (A, B, C):** The system is designed around "folders are storage, metadata is meaning." Improving metadata quality through validation is the correct investment. Retrieval depends on structured fields for ranking and filtering.

**Content-primary position (D-round-2):** Metadata is a failed experiment at this scale. LLM-generated tags are inherently unreliable. Retrieval should use BM25 + embeddings on full content, with metadata as optional boosting signals only. A WMS document labeled "Platform" should still be findable through content.

**Why each has merit:** The metadata-primary camp is correct that the entire current pipeline depends on structured fields, and rearchitecting retrieval around content-first is a much larger change. The content-primary camp is correct that validating derivative data with more derivative data is fundamentally limited, and that the deepest fix addresses the reliance on fragile structured extraction.

### 2. Should corp-by-os auto-patch frontmatter?

**Pro-patching (B):** When confidence is high and extraction quality is good but labels are wrong, patching frontmatter during ingestion is the cheapest, most immediate fix. Record provenance and move on.

**Anti-patching (C):** Mutating data downstream of the producer destroys provenance and creates divergence between CKE's raw output and the vault's reality. If metadata is wrong, re-extract or reject.

**Why each has merit:** Patching is pragmatically fast and addresses the retrieval problem immediately. But it masks upstream extraction defects and creates a hidden split between source and indexed truth that compounds over time.

### 3. Should retrieval smoke tests be part of the MVP?

**Include them (B):** Content-vs-metadata checks alone cannot prove discoverability. A small golden-query suite after batch ingestion catches the "looks valid but never retrieved" failure class.

**Exclude them (C, D):** Retrieval tests are non-deterministic, require maintenance, and add operational complexity. The real value comes from fixing ingestion and extraction, not from testing the index.

**Why each has merit:** Smoke tests are the only way to catch retrieval-layer failures without manual search testing. But they introduce a new maintenance burden (query curation) and can produce noisy results that erode trust in the quality system.

### 4. How aggressively should validation quarantine notes?

**Strict gate (C):** Pass or fail, no middle ground. Bad data should not enter the index at all.

**Graduated response (B, A):** Pass / soft-fail / hard-fail. Some notes with weak metadata are better than no notes at all. Permanent quarantine under zero-manual-triage creates data graveyards.

**Why each has merit:** Strict gating prevents silent degradation. Graduated response prevents data loss and acknowledges that imperfect metadata may still be better than a missing document, especially for a system that must self-heal without human intervention.

### 5. Is the real problem extraction quality, not validation?

**Validation camp (A, B, C):** We work with the extraction pipeline we have. Validation catches errors now while extraction improves incrementally.

**Fix-the-source camp (D-round-2):** Downstream validation of LLM output using LLM-derived signals is circular. The correct investment is better extraction prompts, chain-of-verification within CKE, and reducing the system's dependence on perfect structured output.

**Why each has merit:** Building a better gate is immediately shippable and catches real errors today. But D's critique is structurally correct: if the generator is the problem, validating its output with its own derivatives has an inherent ceiling.

---

## Recommended Decision

### Build a centralized ingestion quality gate in corp-by-os, with graduated response and batch-level anomaly detection. Simultaneously invest in extraction improvement at CKE.

The decision synthesizes the operational pragmatism of B with the boundary-enforcement clarity of C, the phasing discipline of A, and the structural critique of D.

### Architecture

```
CKE (producer, untrusted)
  → corp-os-meta (taxonomy/alias artifact, read-only config)
  → corp-by-os ingestion quality gate (sole enforcer)
      ├── Per-note: content-vs-metadata evidence scoring
      ├── Per-note: CKE extraction quality score (if present)
      ├── Per-batch: distribution anomaly detection
      └── Per-batch: retrieval smoke tests (Phase 1.5)
```

### Per-note validation logic

For each note at ingestion:
1. Load compiled taxonomy aliases from corp-os-meta (including all synonym expansions).
2. Score evidence for each declared product/domain/topic against title, filename, key_facts, and content excerpt.
3. Read CKE extraction quality score if available.
4. Classify:
   - **Pass**: sufficient evidence for declared labels, extraction score acceptable → ingest normally.
   - **Soft-fail**: weak or ambiguous evidence, or one check fails → ingest with `quality_status: soft_fail`, log reason codes, optionally suppress ranking weight.
   - **Hard-fail**: declared labels contradicted by strong competing evidence, or extraction score critically low AND cross-field mismatch → quarantine, trigger one automatic re-extraction.
   - **Degraded-ingest**: after failed re-extraction, ingest with `trust_level: degraded`, significantly down-ranked in retrieval → emit alert if batch rate exceeds threshold.

### Why graduated response, not strict pass/fail

Under zero-manual-triage, permanent quarantine creates a data graveyard that no one will ever clean. Degraded-ingest is an ugly but necessary escape valve: the note exists, is findable but deprioritized, and the system doesn't silently lose content. C's strict gate is intellectually cleaner but operationally dangerous for an ADHD workflow.

### Why not auto-patch frontmatter (yet)

C's provenance argument wins for the MVP. Auto-patching creates divergence between CKE output and vault state that is hard to debug. Instead:
- Log suspected corrections as reason codes (`suggested_product: WMS`, `evidence: key_facts contain warehouse, picking, putaway`).
- Use these logs to improve CKE prompts and corp-os-meta aliases.
- Revisit auto-patching in Phase 2 only if the data shows a clear class of high-confidence, low-risk corrections.

### Batch-level checks

1. **Distribution anomaly detection** (post-batch or nightly): track product/domain share over a rolling window. Alert if any major category shifts >50% relative to baseline. This catches "everything is Platform" drift.

2. **Retrieval smoke tests** (Phase 1.5, post-batch): 10–15 curated golden queries. Coarse assertions only: "at least 1 result," "expected document family in top N." Alert on threshold failure, not per-query noise.

### Addressing D's structural critique

D-round-2's argument that downstream validation of derivative data has an inherent ceiling is the strongest objection in this debate. It is correct. Therefore:

**In parallel with the quality gate, invest in extraction improvement:**
- Add a consistency self-check within CKE: after extraction, prompt the LLM to verify that declared products match key_facts.
- Add product-specific few-shot examples for the most common mislabeling cases (WMS vs Platform, etc.).
- Use quality gate logs to identify systematic extraction failures and feed them back into prompt engineering.

This is not an either/or. The quality gate catches errors now; extraction improvement reduces the error rate over time.

### What is explicitly rejected

- **Triangular validation as an implemented system.** No distributed voting, no peer consensus, no 2-of-3 arbitration across services.
- **A separate quality-monitor service or agent.**
- **LLM-based validation as baseline.** Budget does not support it; use only as rare escalation.
- **`needs_review` as a human queue.** It is an internal state for ranking suppression and logging, never a workflow that requires human action.
- **Retrieval as the sole quality signal.** D's suggestion to make content fully primary and abandon metadata-first retrieval is the right long-term question but the wrong short-term project. It requires rearchitecting corp-by-os retrieval, which is out of scope.

---

## Risks

### 1. Heuristic false positives quarantine or degrade good notes
**Likelihood:** Medium-high initially.
**Impact:** Reduced content availability, user trust erosion.
**Mitigation:** Start with conservative thresholds. Require multiple evidence failures before hard-fail. Log all classifications with reason codes. Track quarantine and degraded-ingest rates. Tune thresholds based on actual data within the first two weeks.

### 2. Heuristic false negatives let bad metadata through
**Likelihood:** High for subtle mismatches (e.g., domain drift, implicit product references).
**Impact:** Continued silent degradation for edge cases.
**Mitigation:** Accept this limitation explicitly. Batch-level distribution checks and retrieval smoke tests provide a second net. Extraction improvement reduces the upstream error rate over time. This is a known ceiling of the heuristic approach.

### 3. Re-extraction loop burns budget
**Likelihood:** Low if capped correctly.
**Impact:** Could exhaust $20/month LLM budget on a bad batch.
**Mitigation:** Hard cap: 1 automatic re-extraction per file per version. After failure, degraded-ingest, never retry again without explicit trigger. Budget guardrail: halt re-extraction if monthly spend exceeds $15.

### 4. Degraded-ingest notes accumulate as permanent low-quality sludge
**Likelihood:** Medium over time.
**Impact:** Search result quality erosion as degraded notes pile up.
**Mitigation:** Track degraded-ingest count in `corp doctor`. Alert if count exceeds threshold. Periodically (monthly) sweep degraded notes through improved CKE (if extraction prompts have been updated). Include degraded notes in CKE improvement feedback loop.

### 5. Taxonomy alias artifact falls out of sync
**Likelihood:** Medium if corp-os-meta updates without triggering revalidation.
**Impact:** False rejections or false passes based on stale aliases.
**Mitigation:** Version-stamp the alias artifact. Log which version was used for each validation run. When aliases update, optionally re-validate recent batches.

### 6. Golden query suite becomes stale maintenance burden
**Likelihood:** High over 6+ months.
**Impact:** Smoke tests become meaningless, providing false confidence.
**Mitigation:** Keep the suite deliberately small (10–15 queries). Derive queries from actual product/client taxonomy, not handcrafted. Review quarterly. Accept that this is an imperfect, coarse signal, not a proof of retrieval health.

### 7. The real problem remains extraction quality, and validation becomes a crutch
**Likelihood:** Medium-high.
**Impact:** Validation catches symptoms while the disease progresses.
**Mitigation:** This is the most important risk. Mandate that quality gate logs are used to improve CKE within the first month. Track the trend of hard-fail and soft-fail rates. If rates don't decrease over 2 months, the extraction pipeline needs fundamental rework, not more validation.

---

## Action Items

### Phase 1: Ingestion Quality Gate (Week 1–2)

1. **Build taxonomy alias artifact loader in corp-by-os.**
   - Consume compiled product/domain/topic aliases from corp-os-meta.
   - Include all synonym expansions.
   - Version-stamp the artifact.

2. **Implement content-vs-metadata evidence scorer.**
   - For each declared product/domain/topic, compute evidence score from title, filename, key_facts, content excerpt.
   - Use weighted scoring (title > key_facts > content excerpt > filename).
   - Output: per-label evidence score + overall classification.

3. **Integrate CKE extraction quality score.**
   - Read `eval_extraction.py` score from frontmatter if present.
   - Flag if score < 50 (threshold tunable).

4. **Implement classification and routing logic.**
   - Pass / soft_fail / hard_fail / degraded_ingest states.
   - Reason codes for every non-pass.
   - Auto re-extraction trigger for hard_fail (max 1 retry, budget-capped).

5. **Wire into `corp ingest-extractions` pipeline.**
   - Validation runs before index write.
   - Soft-fail notes ingested with quality metadata.
   - Hard-fail notes quarantined in designated folder/state.

### Phase 1.5: Batch Checks (Week 3)

6. **Implement product distribution anomaly detection.**
   - Track product/domain share per batch against rolling baseline.
   - Alert if >50% relative shift in any major category.
   - Run post-batch or nightly.

7. **Build retrieval smoke test suite.**
   - 10–15 golden queries derived from major products/clients.
   - Coarse assertions: presence and top-N family membership.
   - Run post-batch. Alert on threshold failure only.

8. **Update `corp doctor` to surface quality metrics.**
   - Quarantine queue size.
   - Degraded-ingest count.
   - Soft-fail rate trend.
   - Last smoke test results.

### Phase 2: Extraction Feedback Loop (Week 4+)

9. **Feed quality gate logs back to CKE improvement.**
   - Identify top mislabeling patterns from reason codes.
   - Add product-specific few-shot examples to CKE prompts.
   - Add post-extraction consistency self-check within CKE.

10. **Implement corp-os-meta alias update workflow.**
    - When recurring alias gaps are detected (e.g., "Warehouse Mgmt" → WMS), update aliases.
    - Re-normalize affected recent notes.

11. **Evaluate auto-patching.**
    - After 1 month, review logs for high-confidence correction patterns.
    - If a clear class exists (e.g., >95% confidence product substitution), implement auto-patch with full provenance recording.
    - Otherwise, continue routing corrections through CKE improvement.

### Ongoing

12. **Track quality trends monthly.**
    - Hard-fail rate, soft-fail rate, degraded-ingest count.
    - If rates don't decrease, escalate to extraction pipeline rework.
    - Review golden query suite quarterly.
