# AI Council Debate: ## Question: Where should we replace pure-LLM approaches with algorithmic/ML met

**Date:** 2026-03-26 17:46:58
**Panel:** claude-opus-4-6, deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta
**Synthesizer:** openai (non-participant)
**Rounds:** 2
**Duration:** 317.9s
**Panel Mode:** full (4-model panel)
**Debate Mode:** pick
**Source:** council_inbox\council_algorithmic_hybrid.md
**Cost:** ~$0.4613 (81,770 tokens)

---

## Round 1: Initial Responses

### Claude (claude-opus-4-6)



## Position

Implement three algorithmic replacements in strict sequence — TF-IDF classification, MinHash dedup, and logistic regression quality scoring — each gated behind confidence thresholds with LLM fallback, using only scikit-learn and datasketch as new dependencies.

## Alternatives Considered

**1. Go broad: implement 5+ candidates simultaneously.**
Rejected. Solo developer with ADHD managing 6 packages and 2,276 tests. Parallel workstreams on ML features will produce half-finished implementations that rot. The 2am risk: five different model files, five different retraining scripts, five different confidence thresholds to understand. Cognitive load is the binding constraint, not technical capability.

**2. Go deep on embeddings: prioritize sentence-transformers + FAISS for semantic retrieval.**
Rejected despite being the most technically exciting option. sentence-transformers pulls ~2GB of PyTorch dependencies onto a Windows machine with no GPU. Inference on all-MiniLM-L6-v2 on CPU takes ~50ms/sentence — fine for single queries, but indexing 493+ vault notes during batch processing will blow the 5-minute budget without careful batching. FTS5 is already working. This is a Phase 2 investment after the cheap wins are proven. The ROI per hour of developer effort is much lower than the top three.

## Decision Criteria

1. **Effort-to-impact ratio for a solo developer** — can it be implemented in a single focused session (2-4 hours) and show measurable improvement via the existing eval framework?
2. **Dependency weight** — does it require PyTorch/GPU or only scikit-learn/pure-Python?
3. **Operational simplicity at 2am** — can a future maintainer understand the fallback logic without reading a research paper?
4. **Data sufficiency** — do we have enough labeled examples for the method to outperform the current approach with statistical confidence?
5. **Additive/reversible** — can it be feature-flagged so the existing pipeline is never broken?

## Assumptions

1. **The 310 labeled filename→doc_type pairs have at least 5 examples per class for the top 80% of document types.** If most classes have <3 examples, TF-IDF won't generalize and the ranking changes — you'd start with quality scoring instead.
2. **The 690 quality entries have feature distributions that aren't degenerate** (i.e., not 95% one class). If quality is heavily imbalanced, logistic regression needs stratified sampling or the threshold math breaks down.
3. **Near-duplicate documents actually exist in meaningful quantity in the corpus.** If SHA256 dedup is catching everything already, MinHash adds complexity for no gain. Spot-check 50 random vault pairs before building this.
4. **scikit-learn model persistence (joblib) is acceptable for model storage** — no need for a model registry or versioning system at this scale.

## Recommendation

### What to do now (Phase 1 — weeks 1-3, one feature per week)

**Week 1: TF-IDF Classification with LLM fallback**
- Train `TfidfVectorizer` on the 310 filename→doc_type pairs. Use character n-grams (3,5) since filenames are short and noisy.
- Classifier: `SGDClassifier` with log loss (lightweight logistic regression variant) or plain `LogisticRegression` with `max_iter=1000`.
- **Pattern A: Algorithm first, LLM fallback.** Classify with the model. If `predict_proba` max < 0.7, route to LLM. Log both predictions always (for eval).
- Persist model with `joblib`. Retrain script: one CLI command, < 30 seconds.
- Eval: run against held-out 20% of the 310 pairs. Measure accuracy, then compare LLM-call reduction rate.
- **Feature flag:** `USE_TFIDF_CLASSIFIER=true` in config. Default off until eval passes.

**Week 2: MinHash/LSH Near-Duplicate Detection**
- `datasketch.MinHash` with 128 permutations on document shingles (word 3-grams).
- `datasketch.MinHashLSH` with threshold 0.6 (tunable) for candidate retrieval.
- Insert into pipeline between Extract and Vault: after content is available, before writing.
- **Pattern: Algorithm only, no LLM involved.** This is a similarity computation, not a judgment call.
- Output: candidate duplicate pairs with Jaccard estimate. Flag for human review initially; don't auto-deduplicate.
- Single new dependency: `datasketch` (pure Python, no C extensions, ~50KB).

**Week 3: Logistic Regression Quality Scoring**
- Features from frontmatter: `extension`, `doc_type`, `depth`, `fact_count`, `topic_count`, `word_count`. One-hot encode categoricals.
- `LogisticRegression` or `GradientBoostingClassifier` (still scikit-learn, still fast).
- 690 examples is plenty for 6-10 features. Cross-validate with `StratifiedKFold(n_splits=5)`.
- **Pattern C: Algorithm replaces heuristic formula entirely.** The current heuristic has no learning capability. This is a strict upgrade.
- Log predicted quality alongside current heuristic score for 2 weeks before switching default.

### What NOT to do now

- **BERTopic / topic modeling for tags.** Requires PyTorch or at minimum gensim (heavy). LDA with 200 tags and 493 documents will produce incoherent topics. Wait until corpus is 2,000+ notes.
- **Sentence embeddings / FAISS.** Too heavy for Windows no-GPU. Defer to Phase 2 when the GMKtec with AI accelerator is available and proven.
- **Hungarian algorithm for field mapping.** Interesting but premature optimization. You don't have a canonical knowledge base schema stable enough to map to yet.
- **BM25 replacing FTS5.** FTS5 already uses BM25-like ranking internally (it literally implements an Okapi BM25 variant since SQLite 3.2x). Adding `rank-bm25` in Python on top is slower than letting SQLite do it natively. The real retrieval upgrade is embeddings, which is Phase 2.

### What to defer (Phase 2 — month 2-3)

- **Jaccard/cosine tag similarity** — implement after the tag taxonomy stabilizes. Right now you have 200 tags; wait until you have co-occurrence data from 1,000+ tagged documents.
- **Sentence embeddings** — when GMKtec hardware is available OR corpus exceeds 1,500 notes. Use `all-MiniLM-L6-v2` (22M params, runs fine on CPU for <2,000 docs, just not for real-time batch processing of 50 files).
- **Hybrid retrieval (FTS5 + vector)** — only after embeddings are working.

### Implementation pattern for all Phase 1 features

```
config.yaml:
  classifiers:
    tfidf:
      enabled: true
      confidence_threshold: 0.7
      fallback: "llm"
      model_path: "models/tfidf_classifier.joblib"
      last_trained: "2025-01-15"
      training_examples: 310
```

Every algorithmic step:
1. Loads model from `joblib` file (< 1MB each)
2. Makes prediction + confidence score
3. If confidence < threshold → routes to LLM fallback
4. Logs both scores to eval data regardless
5. Feature flag controls whether algorithm result or LLM result is used for downstream

### New dependencies (total)

```
scikit-learn>=1.3  # already acceptable per constraints
datasketch>=1.6    # pure Python, ~50KB, MinHash/LSH only
joblib>=1.3        # comes with scikit-learn
```

That's it. No PyTorch. No GPU. No new infrastructure.

## Rationale

- **310 examples for text classification is solidly above the minimum viable threshold.** Logistic regression on TF-IDF features typically needs 50-100 examples per class to stabilize. If you have 10 document types with ~30 examples each, expect 85-92% accuracy on held-out data. Every file that scores above 0.7 confidence saves one LLM API call (~$0.001-0.01). At 50 files/batch, that's 35-45 saved LLM calls per batch assuming 70-90% hit rate.

- **MinHash dedup is a categorically different capability, not an optimization.** SHA256 catches exact matches. MinHash with threshold 0.6 catches "same document, re-exported from Notion with different timestamps in the header" or "same article saved from two browsers." This is a net-new capability that no amount of LLM tuning provides. `datasketch` is pure Python, no compilation issues on Windows, and LSH query time is O(1) regardless of corpus size.

- **690 examples for quality prediction with 6-10 features is a textbook good fit for logistic regression.** Rule of thumb: you want 10-20 examples per feature. With 6 features, you need 60-120 minimum. You have 690. The current heuristic formula is hand-tuned and can't improve with data. Even a mediocre model will outperform it within a month as you add 50 examples/month.

- **The "algorithm first, LLM fallback" pattern is operationally the simplest to debug.** At 2am, the on-call question is: "why was this document misclassified?" The answer is always: check the confidence score in the log. If confidence was > 0.7, the model was wrong (retrain). If confidence was < 0.7, the LLM was wrong (different problem). Clean separation of concerns.

- **BM25 replacement of FTS5 is a trap.** SQLite FTS5's `rank` function already implements BM25. Adding `rank-bm25` in Python means loading all documents into Python memory, tokenizing in Python, and ranking in Python — strictly slower than letting SQLite's C implementation do it. The actual retrieval improvement comes from semantic embeddings, which require Phase 2 hardware.

## Trade-offs

- **Model staleness.** Unlike LLMs that generalize to unseen categories, TF-IDF classifiers must be retrained when new document types appear. At 50 new examples/month, you need a monthly retrain cadence or the confidence threshold will silently route more and more traffic to the LLM fallback. Mitigation: add a CI check that retrains and reports accuracy weekly.

- **No semantic understanding in Phase 1.** TF-IDF on filenames captures lexical patterns ("invoice_2024.pdf" → invoice) but not semantic ones ("Q3 financial summary" → invoice). The LLM fallback handles these cases, but you're paying for them. Expected: 15-25% of files still hit LLM for classification.

- **Two prediction systems to maintain.** Every feature-flagged algorithm doubles the code paths through the pipeline. With 3 features in Phase 1, that's 3 additional model files, 3 retraining scripts, and 3 confidence thresholds to tune. Manageable but non-zero.

- **Giving up the possibility of a single unified embedding approach.** A sentence-transformers-based pipeline could potentially replace classification, retrieval, dedup, and tag similarity with one model. By building three separate classical approaches, you create local optima that may resist consolidation later. Acceptable tradeoff: the classical approaches work today, the unified approach requires hardware you don't have.

## Risks

1. **Class imbalance in the 310 classification examples (Likelihood: Medium, Impact: High).** If 150 of 310 examples are "article" and 5 are "receipt," the model will always predict "article." Mitigation: check class distribution before training. Use `class_weight='balanced'` in LogisticRegression. If any class has <5 examples, exclude it from the model and route directly to LLM.

2. **Overfitting with 690 examples and a solo developer tuning (Likelihood: Medium, Impact: Medium).** The temptation is to tune hyperparameters on the test set. Mitigation: strict train/test split (80/20) created once and committed to the repo. Never touch the test set during development. Use 5-fold cross-validation on the training set only. Report test set accuracy exactly once per model version.

3. **MinHash false positives flagging non-duplicates (Likelihood: Medium, Impact: Low).** With threshold 0.6, documents that share common boilerplate (headers, footers) may appear as duplicates. Mitigation: Phase 1 outputs candidates for human review only. Do not auto-deduplicate. Tune threshold upward (0.7, 0.8) based on false positive rate.

4. **Feature flag proliferation creating untested code paths (Likelihood: Low, Impact: High).** If algorithm is enabled in dev but disabled in prod (or vice versa), bugs hide. Mitigation: CI runs tests with all algorithm flags both on and off. That's 2^3 = 8 combinations, but only 2 matter: all-on and all-off.

5. **scikit-learn model loading on cold start adding latency (Likelihood: Low, Impact: Low).** A TF-IDF + LogReg model is ~1-5MB and loads in <100ms. Not a real risk at this scale, but worth noting: do not use pickle, use joblib, and pin scikit-learn version in requirements to avoid deserialization failures after upgrades.

## Signals to Revisit

- **If TF-IDF classification accuracy on held-out test set is below 80%**, the 310 examples may be insufficient or the label space too fragmented. Revisit by consolidating document types or gathering more examples before continuing.
- **If LLM fallback rate exceeds 40%**, the confidence threshold is too high or the model too weak. The cost savings don't justify the added complexity. Either lower the threshold (accepting more errors) or revert to LLM-only.
- **If the GMKtec AMD AI accelerator becomes available and benchmarks show >10 embeddings/second on all-MiniLM-L6-v2**, accelerate Phase 2 immediately. Sentence embeddings would subsume TF-IDF classification and FTS5 retrieval, making two Phase 1 investments obsolete — but they'd have already paid for themselves in learning and eval infrastructure.
- **If corpus grows past 2,000 vault notes**, revisit BERTopic for tag generation. Below that, topic models produce noise.
- **If monthly example growth drops below 20/month**, the training data is stagnating and model retraining provides diminishing returns. Switch focus to active learning: use model uncertainty to prioritize which documents to label next.

*Latency: 93.84s | Tokens: 5404*

### Gemini (gemini-3.1-pro-preview)

## Position
Implement local, deterministic `scikit-learn` models (TF-IDF, Logistic Regression) as a primary routing and classification layer, using external LLMs exclusively as an untrusted fallback mechanism to drastically reduce external attack surface, supply chain risk, and API dependency.

## Alternatives Considered
- **Fully local semantic models (Sentence-Transformers/PyTorch):** Rejected. The supply chain sprawl of the PyTorch/HuggingFace ecosystem is massive. Combined with the lack of a GPU on Windows, this introduces severe CPU throttling risks that will violate your 5-minute batch constraint.
- **Parallel processing (Algorithm + LLM, combining scores):** Rejected. Sending data to the external LLM API anyway negates the data privacy, security, and cost benefits. The blast radius of an API outage or compromised downstream LLM provider remains unchanged.

## Decision Criteria
- **Blast Radius & Data Exposure:** Minimizing the volume of sensitive internal knowledge sent across external API boundaries.
- **Supply Chain Integrity:** Keeping the dependency tree shallow and heavily audited (avoiding sprawling ML frameworks).
- **Execution Determinism:** Ensuring pipeline failures are predictable, transparent, and debuggable for a solo developer.
- **Compute Constraints:** Execution must stay under 5 minutes for 50 files on a Windows CPU.
- **Data Sufficiency:** Models must train reliably without overfitting on a highly constrained dataset (<700 examples).

## Assumptions
- The 690 available examples are accurately labeled, free of malicious data (poisoning), and representative of your production distribution.
- The existing SQLite FTS5 implementation is currently sufficient for base retrieval, making BM25 an optimization rather than a strict necessity.
- You currently send file contents or metadata to third-party APIs (Claude/Gemini) for mundane classification, representing an unnecessary latent data exfiltration risk.

## Recommendation

**What to do now:**
- Adopt **Pattern A (Algorithm first, LLM fallback)**. Treat the local algorithm as a trusted local gateway. If `confidence < threshold` (e.g., 0.85), fall back to the untrusted external LLM.
- Implement **Candidate 1 (TF-IDF + Cosine for Classification)** and **Candidate 5 (Logistic Regression for Quality)**. Use `scikit-learn`. 
- Implement **Candidate 3 (MinHash/LSH for Near-Duplicate Detection)** using `datasketch`. This acts as a pipeline firewall, preventing duplicate documents from consuming external API calls or poisoning the index.
- Standardize your ML stack strictly on `scikit-learn`, `numpy`, and `datasketch`. 

**What not to do now:**
- Do not implement Candidate 4 (BERTopic) or Candidate 6 (Sentence Embeddings). Do not introduce `PyTorch`, `transformers`, or `FAISS`. Your Windows CPU constraint makes this a performance risk, and the supply chain footprint is unjustifiable for the ROI.
- Do not build complex ML training pipelines. Use simple Python scripts that retrain the `.pkl` model artifacts on pipeline startup or via a manual `make train` command.

**What to defer until later:**
- Defer Candidate 2 (BM25) and Candidate 8 (Field Mapping). Your FTS5 SQLite implementation is already local and zero-dependency; replacing it introduces library risk (`Tantivy` requires Rust bindings) for minimal immediate security or architectural gain.
- Defer local embeddings until the GMKtec mini PC with AMD AI accelerator is fully integrated, isolated, and proven stable in your environment.

## Rationale
- **Zero-Data-Exfiltration First Pass:** By using TF-IDF and LogReg for classification and quality scoring, up to 80% of your routine pipeline tasks can be resolved locally. This mathematically shrinks your external trust boundary and reduces the impact of a Gemini/Claude API compromise or outage.
- **Supply Chain Defense:** `scikit-learn` has a highly scrutinized, stable dependency tree. Deep learning libraries introduce hundreds of transitive dependencies, frequent CVEs, and massive binary downloads, which are dangerous for a solo developer to monitor.
- **Overfitting Mitigation via Fallback:** 690 examples are entirely sufficient for low-dimensional models like Logistic Regression or TF-IDF. By using strict probability thresholds, you mitigate the risk of overfitting: the model handles the "fat head" of your distribution safely, while the LLM acts as the exception handler for the "long tail."
- **Determinism Limits Blast Radius:** Classical ML fails predictably. If TF-IDF misclassifies a file, you can inspect the exact weights. LLMs fail non-deterministically (hallucinations, prompt drift), making automated pipeline errors vastly harder to audit and contain.

## Trade-offs
- **Semantic Flexibility:** You give up the "semantic magic" of modern embeddings (e.g., recognizing that "revenue" and "income" are related) in the initial pipeline stages, relying instead on exact statistical term matching.
- **Maintenance Overhead:** You must maintain a mechanism to retrain the `scikit-learn` vectorizers as your vocabulary changes, whereas an LLM dynamically adapts to new terminology.

## Risks
- **Concept Drift:** As you ingest new types of documents, the static TF-IDF/LogReg models will lose accuracy. 
  *Mitigation:* Monitor the fallback rate. If the local model triggers the LLM fallback >20% of the time, trigger an alert to retrain the model with the latest data.
- **Threshold Tuning Sensitivity:** Setting the confidence threshold too low will result in silent misclassifications; setting it too high will route everything to the LLM, defeating the purpose. 
  *Mitigation:* Use your `eval.py` framework to run a precision-recall curve on your 310 classifier pairs. Set the threshold to ensure 99% precision, accepting a lower recall (which just falls back to the LLM).

## Signals to Revisit
- **Hardware Upgrade:** The successful commissioning of the AMD AI accelerator PC, providing reliable local compute. This would justify revisiting Candidate 6 (Sentence Embeddings) using a local, quantized model isolated on that hardware.
- **Data Scaling:** When the dataset exceeds ~5,000 labeled examples, local lightweight embedding fine-tuning becomes mathematically viable and structurally sound.
- **API Policy Changes:** If Claude/Gemini alter their data retention policies in a way that violates your threat model, you will be forced to move all generation (Pattern C) to local hardware, regardless of performance constraints.

*Latency: 41.62s | Tokens: 5072*

### Deepseek (deepseek-reasoner)

## Position
Replace LLM-based classification with TF-IDF/cosine similarity using a confidence threshold fallback to LLM, and implement BM25 to augment keyword retrieval; defer more complex ML until after measuring impact on our specific evaluation set.

## Alternatives Considered
1. **Replace tag generation with BERTopic first** – Rejected because topic modeling on 690 documents will produce unstable topics without careful curation, and the LLM currently provides acceptable tag quality; this is a higher-risk, higher-effort change with less certain ROI.
2. **Implement sentence embeddings for semantic retrieval immediately** – Rejected because without a GPU, inference latency for 50-file batches could exceed pipeline limits, and FTS5+BM25 likely captures 80% of our retrieval needs with minimal overhead.

## Decision Criteria
1. **Greatest cost/latency reduction per implementation hour** – Target steps with highest LLM call volume and simplest algorithmic replacement.
2. **Minimal pipeline disruption** – Changes must be additive and benchmarked against existing eval data before switching.
3. **Operational simplicity on Windows CPU** – No GPU-dependent models in first iteration.
4. **Clear evaluation pathway** – Must show measurable improvement on our 310–690 labeled examples.

## Assumptions
1. Classification and retrieval account for >60% of LLM calls in the current pipeline (if false, ROI drops).
2. Filename patterns and document content contain enough signal for TF-IDF/BM25 to achieve >85% accuracy vs. LLM baseline (if false, fallback rate will be high).
3. The solo developer can manage two additional libraries (scikit-learn, rank-bm25) without breaking the monorepo’s dependency management.

## Recommendation
**What to do now:**
1. Implement TF-IDF + cosine similarity for classification with a confidence threshold (e.g., cosine < 0.7 → LLM fallback). Train on the 310 filename–doc_type pairs.
2. Add BM25 retrieval alongside FTS5, using the same index. Compare precision@5 against current FTS5 results on a held-out set of 50 queries.
3. Run the existing evaluation suite to measure: (a) reduction in LLM classification calls, (b) classification accuracy delta, (c) retrieval relevance improvement.

**What not to do now:**
1. Do not replace LLM tag generation with topic modeling—maintain LLM as generator, but consider adding a tag-deduplication step using Jaccard on existing tags.
2. Do not introduce GPU-dependent models (sentence-transformers, BERTopic) until latency and hardware constraints are resolved.

**What to defer until later:**
1. MinHash for near-duplicate detection—exact hash covers 95% of current duplicates; implement only when near-duplicate volume justifies it.
2. Logistic regression for quality prediction—wait until we have >1,500 quality-labeled examples to avoid overfitting.
3. Hungarian algorithm for field mapping—defer until extraction volume increases 10×.

## Rationale
- **Classification is the lowest-hanging fruit**: 310 labeled examples are sufficient for TF-IDF on filenames. Expect ~70% of classifications to be above confidence threshold, reducing LLM calls by 50–70% (saving $0.02–0.03 per file). Implementation time: 1–2 days.
- **BM25 improves retrieval without breaking FTS5**: BM25 consistently outperforms raw TF-IDF and basic FTS5 ranking. rank-bm25 library is lightweight and can be run in parallel with existing FTS5. Expected 15–20% improvement in precision@5 for ambiguous queries.
- **Confidence thresholds manage risk**: By falling back to LLM when algorithmic confidence is low, we avoid catastrophic accuracy drops. Threshold can be tuned based on eval results.
- **Windows CPU constraints respected**: Both TF-IDF and BM25 run efficiently on CPU; no large neural models required.

## Trade-offs
- **Loss of zero-shot generalization**: TF-IDF cannot classify unseen filename patterns as well as LLM, but fallback covers this.
- **Increased code complexity**: Two additional libraries and confidence-logic branching.
- **Modest latency add**: TF-IDF vectorization adds ~10 ms per file; BM25 adds ~5 ms per query—acceptable within 5-minute batch budget.

## Risks
1. **TF-IDF overfits to current 310 examples** – Likelihood: medium. Impact: low (fallback catches errors). Mitigation: use character n-grams (2–5) instead of words, and evaluate on a time-split holdout.
2. **BM25 performance degrades on very short queries** – Likelihood: low. Impact: medium. Mitigation: retain FTS5 as fallback for queries <3 terms.
3. **Dependency conflicts with scikit-learn** – Likelihood: low. Impact: high. Mitigation: test in isolated conda environment before integrating.

## Signals to Revisit
1. Classification LLM fallback rate >40% after threshold tuning – indicates insufficient signal in filenames; reconsider feature engineering or revert to LLM.
2. Retrieval latency exceeds 2 seconds per query on the GMKtec mini PC – switch to Tantivy (Rust) for BM25.
3. Labeled examples grow beyond 2,000 – revisit logistic regression for quality prediction and sentence embeddings for retrieval.

*Latency: 77.50s | Tokens: 3795*

### Grok (grok-4.20-beta)

## Position
Implement algorithm-first hybrids for classification and quality scoring using TF-IDF and logistic regression, with LLM fallback only on low confidence. Defer all embedding and topic-modeling approaches. This is the only combination that satisfies solo-developer constraints while delivering measurable wins against the existing 310 and 690 labeled examples.

## Alternatives Considered
**All-local-embeddings (sentence-transformers + FAISS for classification, retrieval, and tagging):** Rejected because it introduces PyTorch, model downloads, and CPU-heavy inference that violates the <5 min batch constraint on a Windows machine with no GPU; the 690 examples are insufficient to justify the complexity tax.
**Keep pure LLM with heavier caching:** Rejected because the evaluation data already shows LLM variance on tagging and quality scoring; the hypothesis that "consistency matters" is correct here, and deterministic algorithms trained on our own data will beat prompt engineering alone.

## Decision Criteria
- Implementation effort must be <2 days of focused work for a solo ADHD developer
- Must leverage the existing 310 classifier pairs and 690 quality labels immediately
- Must run on Windows 11 Python 3.11 with no GPU and minimal new dependencies
- Must be additive (existing eval.py must show improvement without breaking the pipeline)
- Pipeline latency for 50-file batch must stay under 5 minutes

## Assumptions
- The 690 quality labels and 310 classifier pairs are reasonably consistent and representative of future documents.
- LLM API cost and latency are material enough that even 60-70% reduction in calls is worth the integration effort.
- We will not receive a GPU-equipped machine in the next 3 months.
- The existing heuristic quality formula is noisy enough that a simple classifier can outperform it.

## Recommendation
**What to do now:** 
- Add a scikit-learn TfidfVectorizer trained on the 310 filename→doc_type pairs; use cosine similarity with a 0.65 threshold (tune once on 5-fold CV). LLM only on miss/low-confidence. 
- Train a LogisticRegression on the 690 quality examples using the existing features (extension, doc_type, depth, fact_count, topic_count); output probability as quality score. 
- Add exact MinHash/LSH deduplication (datasketch) using 5-character shingles on normalized text for near-duplicates.

**What not to do now:** 
- Do not add sentence-transformers, BERTopic, chromadb, FAISS, or rank-bm25. 
- Do not replace FTS5 retrieval yet.

**What to defer until later:** 
- Semantic retrieval, topic modeling for tags, and any Hungarian-style field mapping. Revisit only after we have 2000+ examples and a clear eval regression on the current changes.

## Rationale
- TF-IDF on filenames alone typically reaches 82-88% accuracy with <500 samples on technical document sets; this directly cuts the most frequent LLM call in the pipeline.
- Logistic regression on the exact 690 rows takes <30 seconds to train, gives calibrated probabilities, and removes the only LLM call that was already using a heuristic fallback.
- MinHash with 128 permutations adds ~40ms per document but catches the 15-25% of near-duplicates that SHA256 misses, based on typical knowledge-base distributions.
- Total new dependencies are exactly two: scikit-learn (already acceptable) and datasketch (<1 MB, pure Python). 
- All three changes can be wrapped in "if enabled" flags and measured immediately in eval.py, satisfying the "additive only" constraint.

## Trade-offs
Gives up semantic understanding in classification (LLM catches synonyms/context that TF-IDF misses) — expect 8-12% of files to still hit LLM fallback. Loses the "magic" of LLM tag invention, forcing us to map discovered topics to our existing taxonomy later. Adds ~150-200 lines of Python but removes roughly 0.7 LLM calls per document on average, saving ~$0.015 per file at current Claude pricing.

## Risks
- Overfitting on 690 examples (likelihood: medium, impact: high). Mitigate with 5-fold CV and requiring >0.15 improvement on hold-out set before merging.
- Threshold tuning becomes its own maintenance burden (likelihood: medium, impact: medium). Mitigate by making threshold a config value and adding a weekly eval job.
- datasketch producing false positives on very short documents (likelihood: low, impact: low). Mitigate by minimum length gate (ignore docs <200 chars).
- Solo developer abandons the ML code (likelihood: high given ADHD constraint). Mitigate by keeping each component <80 lines and fully isolated.

## Signals to Revisit
- Eval.py shows <12% reduction in LLM calls or <0.12 F1 improvement on quality scoring after two weeks of real data.
- We acquire a GPU or the GMKtec mini PC demonstrates <800ms inference for all-MiniLM-L6-v2 on our corpus.
- Labeled data growth drops below 30 examples/month, invalidating the "improves with data" premise.
- Production batch time for 50 files exceeds 4 minutes with the new code.

*Latency: 14.59s | Tokens: 3934*

## Round 2: Critique

### Claude (claude-opus-4-6)



## Evaluation of Proposals

---

### Proposal A

**Steelman:** If classification accounts for the majority of LLM calls, and BM25 provides a meaningful retrieval improvement over FTS5, then this two-target approach delivers the highest cost reduction per hour invested while keeping scope manageable for a solo developer. The strength is disciplined restraint — do two things well rather than three things poorly.

**Assessment: Partially agree.** The classification recommendation is sound and well-reasoned. The BM25 recommendation is actively wrong, and including it as a co-equal priority item is a mistake that would waste one of the developer's limited focused sessions.

**Strongest point:** The confidence threshold tuning advice — specifically, using character n-grams (2–5) for filenames and time-split holdout rather than random split. This shows genuine understanding of the data characteristics. Filenames are short, noisy strings where character-level features outperform word-level features, and time-split prevents the model from learning temporal artifacts.

**Weakest assumption:** "BM25 could give better results than raw FTS5 MATCH." FTS5 already implements BM25 ranking internally. SQLite's FTS5 rank function uses an Okapi BM25 variant. Adding `rank-bm25` in Python means loading documents into Python memory and ranking in Python — which is strictly slower than the C implementation already running inside SQLite. This isn't an optimization; it's a regression. The proposal expects "15–20% improvement in precision@5" which has no basis if the underlying algorithm is the same.

**Hidden assumptions:** (1) That retrieval quality is actually a bottleneck worth investing in right now. The proposal never validates whether users are dissatisfied with FTS5 results or whether retrieval precision is currently measured at all. Without a retrieval evaluation set, "compare precision@5 on a held-out set of 50 queries" requires creating that evaluation set first — effort the proposal doesn't account for. (2) That the existing regex-first classification path has been measured for how many calls actually fall through to the LLM. The "assume >60% of LLM calls" is a guess, and the real number determines whether this whole exercise is worthwhile.

**Overlooked risks:** No mention of what happens when new document types are introduced. The TF-IDF model can't classify categories it wasn't trained on, and the fallback-to-LLM pattern silently degrades into LLM-for-everything if the label space drifts. Needs a monitoring hook for "new LLM classifications that don't match any trained category" to trigger retraining.

---

### Proposal B

**Steelman:** If the primary concern is operational risk from external API dependencies — outages, data exfiltration, policy changes, supply chain attacks — then framing algorithmic replacement as a security boundary reduction is exactly right. This proposal would be perfectly correct if the pipeline processes sensitive or regulated data where every external API call represents genuine compliance exposure, and if minimizing blast radius trumps retrieval quality and feature velocity.

**Assessment: Partially agree.** The security framing is valuable and the other proposals underweight it. However, the proposal overweights threat modeling at the expense of practical ROI analysis. A solo developer building a personal knowledge management pipeline is not facing APT-level data exfiltration threats from Gemini API calls. The security lens is intellectually honest but practically miscalibrated for this context.

**Strongest point:** "Classical ML fails predictably. If TF-IDF misclassifies a file, you can inspect the exact weights. LLMs fail non-deterministically." This is the best articulation in any proposal of why determinism matters for operability. At 2am, the difference between "the feature weight for 'invoice' was 0.3 and the threshold was 0.7" versus "the LLM hallucinated a different category because the prompt context window shifted" is the difference between a 5-minute fix and a 2-hour investigation.

**Weakest assumption:** "You currently send file contents or metadata to third-party APIs for mundane classification, representing an unnecessary latent data exfiltration risk." This assumes the data in the pipeline is sensitive enough to warrant treating API calls as a security event. For a personal knowledge management system processing articles, notes, and documents, the actual privacy exposure of filename strings sent to a classification API is negligible. If this assumption is false, the entire security framing collapses and the proposal loses its differentiating rationale — it becomes proposal A with different justification and an added LogReg recommendation.

**Hidden assumptions:** (1) That `scikit-learn`'s dependency tree is materially safer than `sentence-transformers`. While true in terms of transitive dependency count, `scikit-learn` itself depends on `numpy`, `scipy`, and `joblib`, which have had their own CVEs. The security comparison is one of degree, not kind, but the proposal presents it as categorical. (2) That the confidence threshold of 0.85 (notably higher than every other proposal's 0.65-0.7) is achievable. At 0.85, the fallback rate on 310 training examples could easily be 40-50%, which defeats the stated goal. The proposal optimizes for precision at the expense of recall in a way that may not actually reduce LLM calls meaningfully.

**Overlooked risks:** The proposal recommends logistic regression on the 690 quality examples without checking for class imbalance or feature degeneracy. If quality scores cluster heavily (e.g., 80% "good"), the model learns to predict "good" for everything, which is useless. The proposal's security rigor is not matched by its statistical rigor.

---

### Proposal C

**Steelman:** If the developer's ADHD is the true binding constraint, and the risk of abandonment exceeds the risk of technical suboptimality, then the "<80 lines per component, fully isolated" design philosophy is the correct optimization target. This proposal would be exactly right if the primary failure mode of this project is not "wrong algorithm" but "abandoned implementation," and if the 690 quality examples have clean, well-distributed feature values that make logistic regression a near-trivial win.

**Assessment: Partially agree.** The constraint awareness is the best of any proposal. The <80 lines per component rule is genuinely insightful. The three-item scope is right. But the specific items include MinHash dedup, which has uncertain ROI because the proposal itself acknowledges this is based on "typical knowledge-base distributions" rather than measured duplicates in this corpus.

**Strongest point:** "Solo developer abandons the ML code (likelihood: high given ADHD constraint). Mitigate by keeping each component <80 lines and fully isolated." No other proposal treats abandonment risk as a first-class architectural concern. This is exactly the kind of honesty that makes systems survive three years. Code that exists and is simple beats code that is optimal and unfinished.

**Weakest assumption:** "MinHash with 128 permutations adds ~40ms per document but catches the 15-25% of near-duplicates that SHA256 misses, based on typical knowledge-base distributions." The 15-25% figure is from general literature, not from this corpus. If the actual near-duplicate rate is 2-3% (which is plausible for a single-user knowledge base where one person is curating the input), MinHash adds complexity for minimal gain. The proposal itself identifies this as a risk area ("likelihood: low, impact: low") but still recommends building it in Phase 1.

**Hidden assumptions:** (1) That the confidence threshold of 0.65 is aggressive enough to provide meaningful LLM call reduction. At 0.65, you'll capture more files algorithmically, but the error rate among those captures will be higher. The proposal says "tune once on 5-fold CV" but doesn't specify the optimization target — are we tuning for precision (fewer wrong algorithmic classifications) or recall (fewer LLM fallbacks)? These are in tension. (2) That existing quality labels are ground truth. If the 690 quality entries were generated by the current heuristic formula, training a model on them just learns to replicate the heuristic — a common bootstrapping trap. The proposal doesn't verify whether the labels come from human judgment or from the formula being replaced.

**Overlooked risks:** No discussion of what happens if the TF-IDF model and the LLM disagree on a classification that the model rates as high-confidence. This is the "silent wrong answer" scenario. The proposal's logging strategy ("log both scores to eval data regardless") partially addresses this, but there's no mechanism to surface disagreements for review. A simple alert — "model predicted X with 0.91 confidence, LLM predicted Y" — would catch model degradation before it corrupts the pipeline.

---

### Proposal D

**Steelman:** If the pipeline will be maintained by engineers who didn't build it, and operational clarity at 2am is the primary design constraint, then the explicit weekly cadence, config-driven feature flags, and "check the confidence score in the log" debugging model make this the most maintainable option at three years. This proposal would be exactly right if: (a) the class distribution in the 310 examples is balanced enough for TF-IDF to generalize, (b) near-duplicates actually exist in meaningful quantity, (c) the 690 quality labels are independent of the heuristic formula being replaced, and (d) the developer can sustain one feature per week for three weeks.

**Assessment: This is my proposal.** I continue to agree with its position, but the other proposals have surfaced specific points that warrant adjustment.

**Strongest point:** The BM25/FTS5 analysis. Identifying that SQLite FTS5 already implements BM25 internally is a critical technical insight that prevents wasted effort. Proposals A's BM25 recommendation would have the developer build a slower Python reimplementation of something SQLite already does in C.

**Weakest assumption:** Same as the one Proposal C correctly identifies implicitly — the assumption that near-duplicates exist in meaningful quantity in this specific corpus. I recommended MinHash in Week 2 without validating this. If SHA256 catches 98% of duplicates already, MinHash is wasted effort.

**Hidden assumptions:** (1) That a weekly cadence of shipping one ML feature is realistic for a solo ADHD developer who is also maintaining 6 packages and 2,276 tests. The proposal prescribes "one feature per week" but doesn't account for the context-switching cost of going from test maintenance to ML training to eval framework in the same week. (2) That `joblib` model persistence is stable across `scikit-learn` minor version upgrades. In practice, `joblib`-serialized models break when `scikit-learn` upgrades change internal class structures. The proposal mentions pinning scikit-learn version but doesn't address what happens when a security patch forces an upgrade.

**Overlooked risks:** I didn't address the label provenance question. If the 690 quality labels were generated by the existing heuristic formula, logistic regression will learn the heuristic, not improve upon it. This needs verification before Week 3 starts.

---

## Revised Recommendation

I update my position on two specific points. Everything else stands.

**Change 1: Move MinHash from Week 2 to "deferred, pending validation."**

Proposals A and C both correctly (if indirectly) challenge whether near-duplicates are a real problem in this corpus. Proposal A defers MinHash entirely; Proposal C includes it but calls the risk "low/low." I was wrong to put it in Week 2 without empirical validation. The correct approach: before building MinHash, manually inspect 50 random vault note pairs for near-duplicate content. If fewer than 5% show near-duplicate characteristics, defer MinHash entirely and move logistic regression quality scoring to Week 2.

**What caused this update:** Proposal C's admission that the 15-25% near-duplicate figure comes from general literature, not this corpus. I was building a capability to solve a problem we haven't verified exists.

**Change 2: Add a label provenance check before logistic regression quality scoring.**

Proposal C's hidden assumption about quality labels potentially being generated by the heuristic formula is a real risk I missed. Before training the logistic regression model, verify: are the 690 quality labels from human judgment, or from the heuristic formula? If the latter, the model will converge to replicating the heuristic, which is pointless.

**What caused this update:** Realizing that I recommended replacing a heuristic with ML trained on the heuristic's own outputs. That's circular. If the labels are heuristic-derived, either collect 100+ human quality judgments first, or defer quality scoring entirely.

**What did NOT change:**

- **TF-IDF classification remains Week 1.** All four proposals agree on this. It is the clear highest-ROI item.
- **BM25 remains explicitly excluded.** Proposal A's recommendation to add `rank-bm25` is wrong. FTS5 already does BM25. No other proposal challenged my analysis on this point, because the technical fact is clear.
- **Sentence-transformers, BERTopic, FAISS, and PyTorch remain excluded from Phase 1.** All four proposals agree. No GPU, no heavy dependencies.
- **The "algorithm first, LLM fallback" pattern remains the standard.** Proposals B and C agree. The debugging story at 2am is clean: check confidence score, determine which system made the decision, investigate accordingly.
- **The dependency list remains scikit-learn + datasketch only** (with datasketch deferred pending duplicate validation).
- **Feature flags, dual logging, and strict train/test split discipline all remain.**

**Revised Phase 1 sequence:**

- **Week 1:** TF-IDF classification with LLM fallback. Exactly as originally specified.
- **Week 1.5 (half-day):** Validate near-duplicate prevalence (manual inspection of 50 pairs). Validate quality label provenance (are they human or heuristic-derived?).
- **Week 2:** If near-duplicates >5%, build MinHash. If quality labels are human-sourced, build logistic regression quality scoring. If neither condition is met, extend classification eval and begin collecting human quality labels.
- **Week 3:** Whichever of MinHash or quality scoring wasn't done in Week 2, if its precondition is now met.

The confidence threshold for TF-IDF classification: start at **0.70** (Proposal A's recommendation), not 0.65 (Proposal C — too aggressive, risks silent errors) or 0.85 (Proposal B — too conservative, defeats the purpose). Tune using the precision-recall curve from `eval.py` on the 310 pairs with 5-fold cross-validation, optimizing for **95% precision** at the chosen threshold. The remaining files go to LLM. Accept this cost.

**On Proposal B's security framing:** I agree that determinism and debuggability are operationally critical — that argument strengthened my position. I disagree that security/data-exfiltration should be the primary motivating frame for this decision. The actual motivations are cost, latency, consistency, and maintainability, roughly in that order. Security is a nice side effect, not the driver.

*Latency: 92.86s | Tokens: 13007*

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, my primary lens is risk. Every external LLM call is an exfiltration vector and a reliance on a third-party supply chain. Every new library is an expansion of our local attack surface. When we transition from zero-shot LLMs to local ML, we aren't just saving money—we are pulling our trust boundary back inside our own perimeter. 

Here is my evaluation of the council's proposals.

---

### Proposal A

**Steelman first:** This proposal focuses tightly on immediate ROI, leveraging the two most standard text algorithms (TF-IDF and BM25) to tackle the highest-volume LLM calls (classification, retrieval) while explicitly avoiding hardware-bound models that would break pipeline execution time.

**Your assessment:** Disagree with the Position. While I support reducing LLM reliance via TF-IDF, introducing `rank-bm25` in Python is an architectural misstep. It pulls retrieval out of a robust, hardened C-engine (SQLite) into Python memory, increasing our operational blast radius (OOM crashes) for a capability SQLite FTS5 already natively possesses. 

**Strongest point:** The use of strict confidence thresholds to manage risk, cleanly routing low-confidence edge cases to the LLM to prevent catastrophic classification failures.

**Weakest assumption:** Assumes BM25 in Python will outperform or efficiently augment SQLite FTS5 without causing unacceptable memory spikes during the ingestion of 50-file batches.

**Hidden assumptions:** Assumes API cost and latency are the only drivers for moving away from LLMs, completely ignoring the data privacy and security risks of broadcasting internal filenames and metadata to external endpoints.

**Overlooked risks:** Memory exhaustion and denial of service (DoS). Loading the entire document corpus into Python memory to compute BM25 scores will likely blow past the 5-minute batch constraint and crash the pipeline as the vault grows.

---

### Proposal B

**Steelman first:** This proposal perfectly frames the problem as an attack surface reduction exercise. By using local algorithms as a firewall and treating external LLMs strictly as untrusted fallbacks, it mathematically minimizes data exfiltration and API dependency risks while enforcing strict supply chain discipline.

**Your assessment:** Agree with the Position. Treating external dependencies as untrusted and keeping the supply chain shallow (`scikit-learn`, `datasketch`) directly serves defense-in-depth principles. This is the correct architectural mindset.

**Strongest point:** The recognition that execution determinism limits the blast radius. Classical ML fails predictably and auditably; LLMs fail non-deterministically via unpreventable prompt drift, hallucinations, or upstream provider silent updates.

**Weakest assumption:** Assumes the 690 examples are accurately labeled, representative, and completely free of data poisoning. If the training data contains maliciously crafted or anomalous files designed to skew the TF-IDF weights, the local firewall is compromised from the inside.

**Hidden assumptions:** Assumes that moving to local ML models doesn't just shift the attack surface from "prompt injection" (LLM) to "adversarial ML examples" (e.g., keyword stuffing to bypass local classification).

**Overlooked risks:** Model serialization vulnerabilities. Using `scikit-learn` in a pipeline usually implies `pickle` or `joblib`, which are inherently unsafe formats.

---

### Proposal C

**Steelman first:** This is the ultimate pragmatist's roadmap. It correctly identifies the exact three high-ROI, low-dependency algorithms (TF-IDF, LogReg, MinHash) that fit the solo-developer constraints, require zero GPU, and can be evaluated immediately.

**Your assessment:** Partially agree. I agree entirely with the selection of the three algorithms, but I disagree with the lack of security framing. It treats the pipeline optimization purely as a latency/cost exercise, missing the systemic risk reduction of localizing the processing.

**Strongest point:** MinHash with 128 permutations for near-deduplication. This acts as a brilliant pipeline firewall, dropping redundant, spam, or subtly mutated documents before they ever reach the extraction or vault phases, starving downstream LLM calls of garbage data.

**Weakest assumption:** Assumes a solo ADHD developer will rigorously maintain threshold tuning and 5-fold cross-validation over time without automated guardrails.

**Hidden assumptions:** Assumes quality scoring via Logistic Regression based on 5 simple metadata features cannot be easily gamed by a malicious or malformed file (e.g., stuffing fake headers to inflate `fact_count`).

**Overlooked risks:** Hardcoding a static threshold (e.g., 0.65). If the distribution of document types shifts, a static threshold will silently route an increasing volume of files back to the external LLM, effectively reopening the API attack surface without triggering an alarm.

---

### Proposal D

**Steelman first:** A highly mature, battle-tested engineering plan. It correctly calls out the BM25 trap (SQLite already implements it), respects the solo developer's cognitive load by strictly sequencing the work into weekly phases, and precisely defines the operational mechanics.

**Your assessment:** Partially agree. I strongly agree with the strict sequencing and the absolute rejection of Python BM25 and heavy embedding libraries. However, I vehemently disagree with the cavalier endorsement of `joblib` for model storage. 

**Strongest point:** Exposing the BM25 replacement of FTS5 as a trap. Recognizing that SQLite FTS5 natively implements Okapi BM25 ranking prevents us from adding a redundant, vulnerable dependency.

**Weakest assumption:** *"scikit-learn model persistence (joblib) is acceptable for model storage."* This is fundamentally incorrect and dangerous from a security perspective.

**Hidden assumptions:** Assumes the local filesystem where the pipeline runs is entirely isolated. If an external file can trigger a path traversal or directory write, an attacker can overwrite the local `.joblib` file.

**Overlooked risks:** Arbitrary Code Execution (ACE) via insecure deserialization. `joblib` is just a wrapper for `pickle`. If an attacker manipulates the persisted model artifact, the next pipeline startup will execute malicious code with the pipeline's privileges.

---

### Revised Recommendation

I am **updating my position**. I am maintaining my core philosophy (aligned with Proposal B) that local ML must be treated as a strict security firewall to reduce our API attack surface. However, I am adopting the specific feature set of Proposal C (TF-IDF, MinHash, LogReg) and the operational sequencing of Proposal D, while **forcefully vetoing Proposal D's insecure persistence mechanism.**

Do not split the difference on security to save 10 lines of code. Here is the architecture we will deploy:

**1. Establish the Local Firewall (Algorithm First, LLM Fallback)**
Implement TF-IDF for Classification and Logistic Regression for Quality Scoring. By running these locally, we restrict the flow of sensitive internal telemetry to Gemini/Claude. The LLM is no longer the core engine; it is an untrusted fallback mechanism used strictly when the deterministic model confidence drops below a monitored threshold.

**2. Implement MinHash as a "Denial of Wallet" Defense**
Deploy `datasketch` MinHash immediately before the Extract phase. Beyond just cleaning the vault, this prevents adversarial flooding—where ingested near-duplicates trigger runaway LLM extraction costs and exhaust our API quotas. 

**3. Reject BM25 and Embeddings (For Now)**
Keep retrieval strictly inside SQLite FTS5. Introducing `rank-bm25` or `sentence-transformers` right now expands our supply chain dependency tree, introduces massive binary blobs, and risks memory exhaustion, all of which increase the blast radius of a pipeline failure.

**4. CRITICAL MANDATE: Zero-Pickle Serialization**
You will **not** use `joblib` or `pickle` to save the trained `scikit-learn` models, as suggested in Proposal D. Loading a compromised `.pkl` or `.joblib` file results in instant Arbitrary Code Execution. 
* **The Fix:** For TF-IDF and Logistic Regression, write a simple script to extract the vocabulary dictionary, the IDF arrays, and the regression weights (`clf.coef_`, `clf.intercept_`), and save them as plain JSON. On pipeline startup, load the JSON and inject the arrays into empty `scikit-learn` objects. This completely neutralizes the deserialization attack vector.

**5. Monitor Fallback Rates as Anomaly Detection**
Treat the "Algorithm → LLM Fallback Rate" as a core security and observability metric. If the fallback rate spikes from 15% to 45%, do not assume the model just needs retraining. Treat it as a potential indicator of concept drift, format evasion, or data poisoning in the ingestion pipeline.

*Latency: 65.45s | Tokens: 14081*

### Deepseek (deepseek-reasoner)

## Steelmanning Each Proposal

### Proposal A
**Steelman:** If classification and retrieval are the dominant LLM call sources (>60%), and TF-IDF/BM25 achieve >85% accuracy with our specific data patterns, this delivers maximum cost reduction with minimal complexity. The additive approach lets us measure improvement before committing.

**Assessment:** Partially agree with Position.  
- **Why:** Correctly identifies classification as lowest-hanging fruit and respects Windows CPU constraints. However, overly optimistic about BM25 gains without acknowledging FTS5 already implements BM25 ranking.

**Strongest point:** "Classification is the lowest-hanging fruit" – 310 labeled filename examples are perfect for TF-IDF with character n-grams. This yields immediate LLM call reduction with clear evaluation.

**Weakest assumption:** "BM25 consistently outperforms raw TF-IDF and basic FTS5 ranking."  
- **What breaks:** SQLite FTS5's `rank` function already implements an Okapi BM25 variant. The Python `rank-bm25` library would duplicate tokenization in Python rather than SQLite C, likely slowing retrieval. Misunderstanding of FTS5 capabilities.

**Hidden assumptions:**
1. That retrieval relevance is currently problematic enough to justify immediate optimization (vs. classification which has known LLM cost).
2. That the solo developer can easily maintain parallel retrieval systems (FTS5 + BM25) without confusion.

**Overlooked risks:** 
- Adding BM25 creates two retrieval code paths with different ranking behaviors → confusion during debugging.
- No discussion of retraining cadence for TF-IDF model as new document types appear.

### Proposal B
**Steelman:** If data privacy/security is paramount and even small API leaks are unacceptable, then minimizing external calls via deterministic local models provides maximum risk reduction. The supply-chain argument is valid for solo developer maintaining a secure pipeline.

**Assessment:** Disagree with Position.  
- **Why:** Over-indexes on security for a knowledge management pipeline where documents likely aren't sensitive. The "zero-data-exfiltration" goal adds complexity without proportional benefit given the context.

**Strongest point:** "Classical ML fails predictably" – crucial for solo developer debugging. LLM hallucinations create opaque failures; TF-IDF misclassifications are inspectable.

**Weakest assumption:** "The existing SQLite FTS5 implementation is currently sufficient."  
- **What breaks:** If retrieval is already problematic (implied by including BM25 in candidate list), dismissing it for security reasons ignores user-facing quality issues.

**Hidden assumptions:**
1. That the threat model includes significant risk from LLM API data exposure (likely overblown for internal documents).
2. That the developer prioritizes security over performance/cost in equal measure.

**Overlooked risks:**
- **Concept drift without detection:** No mention of monitoring fallback rate trends to trigger retraining.
- **False sense of security:** Local models can still leak patterns via model inversion if deployed elsewhere.

### Proposal C
**Steelman:** If the binding constraint is truly ADHD focus and implementation must be <2 days total, then three focused algorithms with clear fallback patterns deliver measurable wins without cognitive overload.

**Assessment:** Partially agree with Position.  
- **Why:** Correctly identifies that classification + quality scoring + dedup are the three highest-ROI candidates. However, underestimates MinHash implementation complexity for a solo developer.

**Strongest point:** "All three changes can be wrapped in 'if enabled' flags and measured immediately" – respects the additive constraint and existing eval framework.

**Weakest assumption:** "MinHash with 128 permutations adds ~40ms per document."  
- **What breaks:** This assumes optimal implementation with LSH indexing. Initial naive pairwise comparisons on 493 vault notes would be O(n²) and blow the 5-minute batch budget.

**Hidden assumptions:**
1. That the developer can implement MinHash/LSH correctly on first try without getting bogged down in parameter tuning.
2. That near-duplicates are common enough to justify Week 2 priority (needs validation).

**Overlooked risks:**
- **MinHash parameter sensitivity:** Choice of permutations, shingle size, and LSH bands dramatically affects precision/recall. Requires iterative tuning.
- **Three separate model persistence mechanisms** (TF-IDF, Logistic Regression, MinHash) each with different retraining triggers.

### Proposal D
**Steelman:** If cognitive load is the true bottleneck (ADHD + solo developer + 6 packages), then strict sequencing of one algorithm per week with production-ready feature flagging prevents overwhelm while delivering validated improvements.

**Assessment:** Agree with Position.  
- **Why:** Most realistic about implementation pacing, dependency management, and operational simplicity. Correctly identifies that BM25 replacement is a trap given FTS5's existing capabilities.

**Strongest point:** "BM25 replacement of FTS5 is a trap" – shows deep understanding that SQLite FTS5 already implements BM25 ranking. Avoids unnecessary work.

**Weakest assumption:** "The 310 labeled filename→doc_type pairs have at least 5 examples per class for the top 80% of document types."  
- **What breaks:** If class distribution is highly imbalanced (common in real document sets), TF-IDF will need `class_weight='balanced'` or will always predict majority class.

**Hidden assumptions:**
1. That the developer can maintain weekly discipline for three consecutive weeks without interruption.
2. That joblib model persistence is acceptable long-term (no versioning, no drift detection beyond fallback rate).

**Overlooked risks:**
- **Model versioning collisions:** If pipeline runs while retraining script executes, corrupted model files could break production.
- **No rollback mechanism** beyond feature flags – if a model produces systematic errors, discovery might be delayed.

## Revised Recommendation

**I update my position based on Proposal D's superior sequencing and realistic assessment of FTS5/BM25, but with critical modifications addressing overlooked risks.**

### Updated Position
Implement three algorithmic replacements in strict sequence—TF-IDF classification, MinHash dedup, logistic regression quality scoring—each behind confidence thresholds with LLM fallback. However, **reorder sequence based on risk/effort** and add explicit monitoring for concept drift.

### What Changed My Mind
Proposal D's revelation that **"SQLite FTS5's rank function already implements BM25"** was the decisive technical insight. Multiple proposals wasted energy on BM25 without understanding current capabilities. This demonstrates the need for deeper system analysis before prescribing solutions.

### Specific Updates to Proposal D

**Sequence Change:**
1. **Week 1: Logistic Regression Quality Scoring** (not TF-IDF classification)
   - Why: 690 examples with 6-10 features is the most statistically robust dataset. Model trains in <30 seconds, provides immediate value replacing heuristic formula, and has lowest risk of overfitting.
   - Implementation: Use `LogisticRegressionCV` with built-in cross-validation to auto-tune regularization.

2. **Week 2: TF-IDF Classification with Character n-grams**
   - Why: After quality scoring validates the ML approach, tackle classification with clear fallback to LLM.
   - Critical add: **Automatic class imbalance detection** - if any class has <5 examples, route directly to LLM for that class.

3. **Week 3: MinHash/LSH but ONLY as batch job**
   - Why: Near-duplicate detection shouldn't block the pipeline. Implement as separate `find_duplicates.py` script that runs nightly, outputs candidate pairs for human review.
   - Never auto-deduplicate in pipeline Phase 1.

**New Critical Components:**
- **Model Registry Lite:** Store each model with version hash and training date in `models/{algorithm}/{timestamp}/`. Pipeline always loads latest unless explicitly pinned.
- **Drift Detection:** Weekly job compares fallback rates week-over-week. >10% increase triggers alert to retrain.
- **Evaluation Lockbox:** Create immutable test split (20% of each dataset) committed to repo. Never tune on this data.

**Dependency Strategy:**
```
scikit-learn>=1.3  # All classical ML
datasketch>=1.6    # MinHash only
numpy>=1.24        # Already implicit
joblib>=1.3        # Model persistence
```

**Absolutely Avoid (Phase 1):**
- `rank-bm25` (FTS5 already does BM25)
- `sentence-transformers` (wait for GMKtec validation)
- `BERTopic`/`gensim` (need >2,000 documents)
- `FAISS`/`chromadb` (GPU/embedding complexity)

### Pattern Selection Per Task
- **Classification:** Pattern A (Algorithm first, LLM fallback on confidence <0.7)
- **Quality Scoring:** Pattern C (Algorithm replaces heuristic entirely - no LLM involved)
- **Dedup:** Pattern A (Algorithm only, no LLM - output candidates for human review)
- **Retrieval:** No change to FTS5 (it's already local BM25)

### What Breaks First and at What Scale
1. **TF-IDF classification** breaks when novel document types appear (0 examples in training).  
   - **Failure mode:** High fallback rate → LLM costs return.  
   - **Threshold:** ~20% of documents are new types.  
   - **Mitigation:** Weekly retrain with newly labeled data.

2. **Logistic Regression quality scoring** breaks with feature distribution shift.  
   - **Failure mode:** Systematic over/under-prediction on new document formats.  
   - **Threshold:** When `fact_count` or `topic_count` ranges double.  
   - **Mitigation:** Monitor prediction distribution vs. actual labels.

3. **MinHash/LSH** breaks with very short documents (<200 chars).  
   - **Failure mode:** High false positive rate on boilerplate.  
   - **Threshold:** Document length <200 chars.  
   - **Mitigation:** Length filter before dedup.

### Signals to Abort
- **Week 1:** If logistic regression doesn't outperform heuristic formula on test set by >0.15 F1 score, abort ML pipeline entirely - data quality insufficient.
- **Week 2:** If TF-IDF classification fallback rate >40% after threshold tuning, revert to LLM-only for classification.
- **Week 3:** If MinHash produces >30% false positives in manual review, disable and stick with SHA256 exact hash.

### Final Answer to Panel Questions
1. **Best ROI ranking:** Logistic Regression quality (690 examples) > TF-IDF classification (310 examples) > MinHash dedup (categorical improvement) > everything else.
2. **Minimum viable:** scikit-learn defaults + character n-grams for TF-IDF + 5-fold CV + single confidence threshold.
3. **Replace vs augment:** Classification→A, Quality→C, Dedup→A, Retrieval→no change, Tags→defer.
4. **Libraries:** scikit-learn + datasketch only. No PyTorch, no transformers, no BM25 libraries.
5. **690 enough?** Yes for logistic regression (10:1 ratio), marginal for TF-IDF classification (need ~5 per class), no for topic modeling (need 2,000+).
6. **Overfitting risk:** High. Mitigate with: (1) immutable test set, (2) LogisticRegressionCV, (3) no hyperparameter tuning on test set.
7. **GPU requirements:** BERTopic/sentence-transformers impractical on Windows CPU. Wait for GMKtec validation.
8. **CIG connection:** Embeddings + cosine similarity is their Phase 2. Our Phase 1 (classical ML) validates the "algorithm first" pattern before investing in embedding infrastructure.

**The throughput-minded architect's verdict:** Start with logistic regression quality scoring. If it beats the heuristic on your 690 examples, continue. If not, LLMs remain your best option given data constraints. Don't solve problems you don't have (BM25). Build one algorithm at a time, measure rigorously, and maintain the escape hatch of LLM fallback for every probabilistic decision.

*Latency: 168.39s | Tokens: 13192*

### Grok (grok-4.20-beta)

**Steelman of Proposal A:**  
If classification truly dominates LLM spend, filenames carry strong lexical signal, the 310 pairs are clean and representative, and the solo developer will actually maintain a retraining cadence, then TF-IDF + cosine with a tuned fallback plus BM25 augmentation delivers the highest ROI with almost zero technical risk. Everything else is correctly deprioritized.

**Assessment:** Partially agree.  
The position is sane and pragmatic, but it still buys the consensus premise that “we should replace LLM calls with classical ML wherever we have a few hundred examples.” That premise is shaky.

**Strongest point:**  
Explicitly calls out that BM25 is an optimization, not a necessity, and that FTS5 already does something very close. This is the only proposal that doesn’t treat BM25 as obviously better.

**Weakest assumption:**  
That classification and retrieval are >60% of LLM calls. If the real cost center is actually tag generation or extraction, the entire ROI calculation collapses.

**Hidden assumptions:**  
1. The 310 filename→doc_type pairs were labeled by humans or by an LLM that was doing a good job; they are not self-reinforcing LLM slop.  
2. A solo ADHD developer will reliably retrain the model every time the vocabulary drifts instead of just turning the feature flag off.

**Overlooked risks:**  
Evaluation contamination. With only 310 examples and an eval.py that the same developer owns, it is extremely easy to iterate until the numbers look good on the hold-out set without realizing the test set leaked into feature decisions.

---

**Steelman of Proposal B:**  
If the dominant risk is actually data exfiltration or supply-chain attack rather than cost or latency, then treating the LLM as an untrusted fallback and keeping the trusted path inside an auditable scikit-learn + datasketch perimeter is the only logically consistent position. Everything else is security theater.

**Assessment:** Disagree.  
This proposal imports a threat model that was never stated in the original question. The council is debating a knowledge management pipeline, not a classified intelligence system. Elevating “data exfiltration risk of filenames” to first principle is scope creep.

**Strongest point:**  
The supply-chain critique of the PyTorch/Hugging Face ecosystem is correct and under-discussed. Those dependency trees are genuinely terrifying for a solo maintainer.

**Weakest assumption:**  
That the 690 quality labels are “free of malicious data (poisoning).” If the labels themselves came from Claude/Gemini, the poisoning already happened upstream of any model we train.

**Hidden assumptions:**  
1. That deterministic failure is always preferable to stochastic failure for a knowledge pipeline whose entire purpose is to surface fuzzy, incomplete information.  
2. That a solo developer will audit scikit-learn updates and datasketch’s C extensions more rigorously than they currently audit LLM prompt changes.

**Overlooked risks:**  
The system becomes brittle in exactly the places humans are bad at noticing. When the TF-IDF model silently starts routing everything to fallback because new document types appeared, the security benefit disappears while the maintenance tax remains.

---

**Steelman of Proposal C:**  
If implementation effort must be <2 days and we refuse to add any dependency that feels heavy, then the smallest possible winning set is TF-IDF classification + logistic regression on quality + MinHash dedup, all behind flags. Anything more violates the ADHD/solo constraint.

**Assessment:** Disagree.  
This is the most cargo-cult “minimal” proposal. It still adds three separate ML components, each with its own threshold and retraining story, while claiming to be low complexity. That is self-deception.

**Strongest point:**  
Forcing every change to be measurable in eval.py within days is correct discipline.

**Weakest assumption:**  
That 690 examples with 6–10 hand-crafted features will produce a meaningfully better quality scorer than the existing heuristic. Quality is not a simple function of fact_count and depth; the model will just memorize the heuristic.

**Hidden assumptions:**  
The author assumes that “we will not receive a GPU-equipped machine in the next 3 months” is a constraint rather than a variable. Hardware arrives when it arrives; designing around its permanent absence is how technical debt gets baked in.

**Overlooked risks:**  
Flag proliferation + ADHD maintainer = most flags will be left in the “experimental” state forever. The codebase ends up with three parallel implementations, none of which are trusted.

---

**Steelman of Proposal D:**  
If cognitive load is the true bottleneck, then sequencing three tiny, isolated, feature-flagged classical models (one per week) with ruthless deferral of everything else is the only way a single ADHD developer survives the next quarter without burning out or producing unmaintainable spaghetti.

**Assessment:** Disagree.  
This is the most honest about complexity but then immediately proposes three new systems. It fails its own decision criteria.

**Strongest point:**  
The explicit “Phase 1 = weeks 1-3, one feature per week” framing and the 2am debuggability test are excellent.

**Weakest assumption:**  
That class imbalance in the 310 examples is the main risk. The deeper risk is that the document taxonomy itself is unstable and the labels are arbitrary.

**Hidden assumptions:**  
1. That writing three separate retraining scripts and three joblib files is simpler than improving the existing LLM prompt + caching layer.  
2. That SQLite FTS5’s built-in BM25 ranking is good enough, while simultaneously believing classical ML will be better everywhere else. Inconsistent.

**Overlooked risks:**  
The “we’ll just retrain monthly” plan dies the first time the developer is in flow on something else. Six months later the models are stale, fallback rate is 90%, and no one remembers which threshold controls what.

---

**Revised Recommendation**

The other proposals did not change my mind; they reinforced the core error.

**Everyone is taking for granted that the labeled data is trustworthy and that replacing LLM calls with trained models is obviously good.** Both are false.

**New position:** Do not train *any* models on the current 310/690 examples. The data is too small, likely noisy or LLM-contaminated, and the maintenance burden of retraining cycles is incompatible with a solo ADHD developer.

**Implement only two things, in this order:**

1. **MinHash/LSH deduplication (Candidate 3)** using datasketch on 4-5 character shingles. This requires *zero* training data, is purely algorithmic, catches the exact failure mode SHA256 misses, and acts as a firewall. Do it this week. No confidence threshold, no fallback, no model file.

2. **Replace the quality heuristic with a deterministic rule-based scorer** (deeper length, entity density, heading structure, presence of citations). Train nothing. If you want to use the 690 examples at all, use them only to tune the rule weights once, then throw the data away.

**For classification and retrieval:** Keep the current regex + LLM fallback and FTS5. Add aggressive caching and prompt compression before you add any learned model. Only after we have >2,000 high-quality human-labeled examples *and* the GMKtec hardware is actually running should we revisit embeddings.

**Libraries:** datasketch only. scikit-learn is banned until we have a human-labeled dataset at least 5× larger and a second maintainer.

This is the least popular option. It rejects the entire “classical ML will save us” narrative. It is also the only one that survives first contact with a solo developer’s real life.

*Latency: 18.94s | Tokens: 10981*

## Synthesis (by openai, non-participant)

## Consensus

### Strong consensus
1. **Start with classical methods for classification before anything else.**
   - Nearly all serious proposals converged on **TF-IDF over filenames with LLM fallback** as the best first experiment.
   - This was supported by actual fit-to-problem reasoning:
     - filenames are short/noisy, so **character n-grams** are appropriate
     - 310 labeled examples is plausibly enough for a lightweight classifier
     - classification is a narrow task where deterministic models can cover the common cases
     - fallback keeps risk low

2. **Do not prioritize embeddings / BERTopic / PyTorch-heavy approaches now.**
   - Broad agreement that **sentence-transformers, BERTopic, FAISS, chromadb, PyTorch** are too heavy for the current constraints:
     - solo developer
     - Windows CPU
     - no GPU
     - <5 min batch target
   - This consensus was evidence-based, not just echoing.

3. **Do not replace FTS5 with Python BM25.**
   - The strongest technical consensus was that **SQLite FTS5 already uses BM25-style ranking**, so adding `rank-bm25` in Python is likely redundant or worse.
   - This was one of the best-grounded points in the debate.

4. **Use additive rollout, feature flags, and evaluation rather than hard replacement.**
   - Most proposals agreed on:
     - feature-flagging
     - keeping existing pipeline intact
     - logging algorithm confidence and outcomes
     - evaluating before switching defaults

5. **Prefer “algorithm first, LLM fallback” over all-at-once replacement.**
   - For classification especially, the preferred pattern was:
     - algorithm handles high-confidence head cases
     - LLM handles uncertain/novel tail cases

### Weaker / more assumption-driven consensus
6. **Logistic regression for quality scoring is promising.**
   - Many participants liked it because 690 examples is enough for low-dimensional tabular ML.
   - But this depended on an unverified assumption: **what are the labels actually measuring, and where did they come from?**
   - So this consensus is less secure than the classification consensus.

---

## Unresolved Disagreements

### 1. Should quality scoring be an early ML target?
**Crux:** Are the 690 quality labels independent, human-meaningful targets, or are they mostly derived from the current heuristic?

- **Pro-ML side:** Logistic regression is a good fit for 690 examples and a few structured features; it is cheap, simple, and likely better than a hand-tuned heuristic.
- **Skeptical side:** If labels come from the heuristic being replaced, the model just learns the heuristic; if “quality” is poorly grounded, the exercise is circular.

**Stronger argument:** **Skeptical side.**
- Reason: it identified a concrete failure mode that could make the entire effort pointless.
- The pro side had good statistical-fit reasoning, but only if label provenance is sound.

### 2. Should MinHash near-duplicate detection be Phase 1?
**Crux:** Do near-duplicates occur often enough in this corpus to justify the work?

- **Pro-MinHash side:** It adds a capability SHA256 cannot provide and is lightweight.
- **Skeptical side:** ROI is speculative; no one showed evidence that near-duplicates are a real current pain point.

**Stronger argument:** **Skeptical side.**
- Reason: the anti-MinHash position demanded corpus-specific validation instead of relying on generic literature.

### 3. How aggressive should the project be about replacing LLMs?
**Crux:** Is the main objective cost/latency/consistency, or security/privacy/risk reduction?

- **Security-framed side:** Push as much as possible local-first to reduce API exposure.
- **Pragmatic ROI side:** Security is secondary here; optimize for maintainability, speed, cost, and measurable gains.

**Stronger argument:** **Pragmatic ROI side.**
- Reason: it better matches the stated problem and constraints. The security framing was coherent but imported a stronger threat model than the prompt justified.

### 4. Should you train any ML at all yet?
**Crux:** Is the dataset trustworthy and large enough to justify model maintenance burden?

- **Train-now side:** Yes, at least for TF-IDF classification, likely also for quality.
- **Do-not-train side:** No, data may be noisy/LLM-derived, and solo-maintainer cost may outweigh gains.

**Stronger argument:** **Train-now for classification; caution for quality.**
- Reason: classification has a narrow input surface, clear labels, low implementation burden, and an easy fallback pattern.
- The blanket “ban scikit-learn” argument was too absolute and underweighted the low-risk nature of a small classification pilot.

---

## Argument Quality Assessment

### Best-reasoned proposals
**Best overall:** the proposal that recommended:
- **TF-IDF classification first**
- **explicitly rejecting Python BM25 because FTS5 already does BM25**
- **deferring heavy embedding stacks**
- **feature-flagged rollout**
- **adding label-provenance and duplicate-prevalence checks before committing to quality scoring / MinHash**

Why it was best:
- It matched constraints well
- It distinguished what is known from what is assumed
- It updated its own recommendation when challenged
- It focused on reversibility and operational simplicity

**Second-best reasoning:** the more pragmatic minimal-scope proposal that emphasized:
- small isolated components
- immediate measurability in `eval.py`
- ADHD-aware implementation discipline

It was strong on execution realism, weaker on evidentiary support for MinHash.

### Weaker proposals
1. **The BM25-augmentation proposal**
   - Main weakness: it failed to account for the key technical fact that **FTS5 already implements BM25-style ranking**.
   - That undercut one of its central recommendations.

2. **The hard-security proposal**
   - Strong on dependency caution and determinism.
   - Weak because it over-weighted a threat model not established by the prompt.

3. **The “train nothing yet” proposal**
   - Useful as a cautionary minority view.
   - But too categorical: it treated all ML as equally risky and ignored the unusually low-risk fit of TF-IDF classification with fallback.

### Single strongest argument in the debate
**“Do not add Python BM25 to replace/augment FTS5, because SQLite FTS5 already implements BM25-style ranking.”**

Why strongest:
- Specific
- Technically grounded
- High leverage
- Prevents wasted work

### Single weakest argument in the debate
**“Ban scikit-learn until you have 5× more human-labeled data and a second maintainer.”**

Why weakest:
- Overgeneralized across tasks with very different complexity/risk
- Ignored that TF-IDF classification is cheap, reversible, and does not require a heavy ML pipeline
- Offered caution, but not calibrated caution

---

## Blind Spots

The debate missed or underexplored several important points:

1. **No one quantified actual LLM call distribution by pipeline step.**
   - This is a major omission.
   - ROI depends heavily on whether classification, tagging, extraction, or some other stage drives most cost/latency.

2. **No one seriously addressed evaluation design for retrieval.**
   - People argued about retrieval methods without an existing query relevance dataset.
   - Without labeled queries, retrieval changes are hard to judge.

3. **Tag generation was not deeply decomposed.**
   - The debate mostly jumped from “LLM tags” to “BERTopic,” which is too large a leap.
   - Missing middle-ground options:
     - tag candidate extraction from a controlled vocabulary
     - multi-label TF-IDF/logistic baseline
     - keyword/keyphrase extraction + taxonomy mapping
   - This is a significant blind spot because tagging is one of the explicitly LLM-heavy steps.

4. **The distinction between filename-only classification and content-aware classification was not explored enough.**
   - If many filenames are poor, TF-IDF-on-filename may plateau quickly.
   - No one proposed a staged approach:
     - filename-only model first
     - then add cheap metadata/content snippets if needed

5. **Model calibration was mentioned but not really addressed.**
   - “Confidence threshold” was central to many proposals, but probability calibration for small models was not discussed.
   - Raw classifier probabilities may be poorly calibrated.

6. **Operational retraining workflow was under-specified.**
   - Many mentioned retraining cadence, but little detail on:
     - who labels fallback cases
     - how examples get added
     - how drift gets detected and corrected
   - For a solo developer, this is crucial.

7. **Most participants assumed labels are decent.**
   - Label quality/provenance came up for quality scoring, but should also be checked for classification and tags.

---

## Recommended Decision

### Decision
**Implement one Phase 1 algorithmic replacement now: TF-IDF-based classification with LLM fallback.**

**Do not implement BM25 replacement.**
**Do not implement embeddings / BERTopic / FAISS / PyTorch now.**
**Do not commit yet to logistic regression quality scoring or MinHash dedup until two validation checks are done.**

### Why
This is the clearest high-ROI, low-complexity move supported by the debate.

It best satisfies the stated constraints:
- solo developer
- additive only
- fast
- low dependency load
- immediately measurable with existing eval framework

It also has the safest replacement pattern:
- deterministic model for common cases
- LLM fallback for uncertain cases
- minimal breakage risk

### Specific recommendation by candidate

1. **TF-IDF + cosine / linear classifier for classification**  
   **Do now.**  
   Pattern: **A — Algorithm first, LLM fallback**

2. **BM25 for retrieval**  
   **Do not do now.**  
   Keep FTS5. Revisit retrieval only when you have retrieval eval data and a concrete deficiency.

3. **MinHash/LSH for near-duplicate detection**  
   **Defer pending validation.**  
   First measure whether near-duplicates are common enough to matter.  
   Pattern if adopted: **Algorithm only**

4. **Topic modeling for tag generation**  
   **Do not do now.**  
   BERTopic/LDA is too heavy/unstable for current scale and constraints.

5. **Logistic regression for quality prediction**  
   **Conditional next step, only after label provenance check.**  
   Pattern: **C — Algorithm replaces heuristic**, but only if labels are meaningful and independent.

6. **Sentence embeddings for semantic retrieval**  
   **Defer.**  
   Revisit only after hardware and need are both validated.

7. **Jaccard/cosine for tag similarity**  
   **Defer.**  
   Needs more stable tag co-occurrence data and a clearer use case.

8. **Hungarian algorithm / embedding field mapping**  
   **Defer.**  
   Premature relative to current needs and data maturity.

### Why not choose the broader “top 3 now” plan?
Because the strongest objections were right:
- **MinHash ROI is unproven in this corpus**
- **quality scoring may be circular if labels are heuristic-derived**

So the best decision is not “three features now”; it is **one implementation plus two validation gates**.

### What would change this recommendation?
If you discover:
- classification is a tiny fraction of LLM spend, or
- quality labels are clean and human-derived while classification data is weak,

then quality scoring might move up. But based on the debate, classification remains the safest first move.

---

## Risks

1. **TF-IDF classifier underperforms due to class imbalance or poor filenames**
   - Mitigation:
     - inspect class counts first
     - use character n-grams
     - use stratified CV or time-split holdout
     - route low-confidence and unsupported classes to LLM

2. **Confidence threshold is mis-set**
   - Too low: silent bad classifications
   - Too high: no cost savings
   - Mitigation:
     - optimize threshold for high precision, not max accuracy
     - log fallback rate and error rate
     - review disagreements

3. **Model drift as new document types appear**
   - Mitigation:
     - monitor fallback rate by week
     - log unseen/novel categories
     - retrain on new labeled examples periodically

4. **Quality-scoring effort becomes circular**
   - Mitigation:
     - verify label provenance before training anything
     - if labels are heuristic-derived, collect human judgments first

5. **MinHash turns into unnecessary complexity**
   - Mitigation:
     - do a cheap prevalence study before implementation
     - if duplicate prevalence is low, skip it

6. **Feature-flagged paths accumulate maintenance burden**
   - Mitigation:
     - add only one algorithmic path at a time
     - require measurable benefit before keeping it

7. **Overfitting / self-deception during evaluation**
   - Mitigation:
     - freeze a holdout set
     - tune only on training folds
     - report one final test result per model version

---

## Action Items

### Immediate
1. **Measure current LLM usage by pipeline step**
   - Count calls, latency, and cost for:
     - classification
     - rename
     - routing
     - extract
     - tag
   - This was a key missing input.

2. **Implement TF-IDF classification pilot**
   - Use `scikit-learn`
   - Start simple:
     - `TfidfVectorizer(analyzer="char", ngram_range=(3,5))`
     - linear classifier (`LogisticRegression` or `SGDClassifier(loss="log_loss")`)
   - Train on the 310 filename → doc_type examples
   - Feature-flag it
   - Fallback to LLM below threshold

3. **Create a locked evaluation split**
   - Freeze a test split now
   - Do not tune on it

4. **Tune for precision-first behavior**
   - Choose threshold to maintain high precision
   - Accept lower recall because fallback exists

5. **Log every decision**
   - filename
   - model prediction
   - confidence
   - fallback yes/no
   - LLM result if invoked
   - eventual accepted label

### Before any second algorithm
6. **Check quality label provenance**
   - Determine whether the 690 labels are:
     - human judgments
     - heuristic outputs
     - LLM-generated labels
   - If not independent, do not train a replacement model yet

7. **Check near-duplicate prevalence**
   - Sample corpus pairs or likely duplicate candidates
   - Estimate whether near-duplicates are frequent enough to justify MinHash

### Likely next step if checks pass
8. **If quality labels are sound, test logistic regression for quality**
   - Use only existing structured features first
   - Compare against heuristic baseline
   - Only keep if it clearly beats heuristic on holdout data

9. **If near-duplicate prevalence is meaningful, add MinHash as review-only**
   - Don’t auto-delete or auto-merge
   - Output candidate pairs for review first

### Explicit deferrals
10. **Do not spend time now on**
   - Python BM25
   - BERTopic/LDA/NMF for tags
   - sentence-transformers / FAISS / chromadb
   - Hungarian field mapping

If you want, I can turn this into a **ranked roadmap table for all 8 candidates** with columns: ROI, effort, data sufficiency, replacement pattern, and recommended timing.
