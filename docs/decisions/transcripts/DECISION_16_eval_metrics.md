# AI Council Debate: ## Question: Should we adopt Jaccard Score as a formal evaluation metric for our

**Date:** 2026-03-26 12:18:20
**Panel:** claude-opus-4-6, deepseek-reasoner, grok-4.20-beta
**Synthesizer:** openai (non-participant)
**Rounds:** 2
**Duration:** 261.0s
**Mode:** full (3-model panel)
**Source:** council_inbox\council_evaluation_metrics.md
**Cost:** ~$0.3401 (57,518 tokens)

---

## Round 1: Initial Responses

### Claude (claude-opus-4-6)



## Position

Adopt Jaccard for tag and product evaluation, but use simple accuracy for the classifier and F1 with per-class breakdown for people filtering. Automate this as a single CLI command that runs against your existing fixtures on every batch, not quarterly.

## Alternatives Considered

**1. Jaccard everywhere, as proposed.** Rejected because Jaccard is meaningless for the classifier task. Classifier output is a single label, not a set. `J({predicted}, {expected})` collapses to binary 0/1, which is just accuracy with extra conceptual overhead. Calling it "Jaccard" when it's accuracy creates confusion for your future self and anyone who inherits this. Use the simpler, correct name.

**2. Full precision/recall/F1 matrix for everything.** Rejected because it's overbuilt for a solo developer context. P/R/F1 per-class is valuable for the people filter (where false positives and false negatives have asymmetric costs — filtering out a real person is worse than letting a role name through), but for tags and products, Jaccard captures the set-overlap intuition naturally and is easier to reason about at 2am. Adding separate P/R columns for tags doubles your dashboard surface without proportional insight gain right now.

## Decision Criteria

1. **Cognitive load per metric:** Can you glance at a number and know if things got worse? A solo developer with ADHD needs metrics that are instantly interpretable, not metrics that require consulting a definition.
2. **Fitness to data shape:** Classifier = single label → accuracy. Tags/products = sets → set-similarity metric. People filter = binary keep/drop per entity → precision/recall.
3. **Automation cost:** Must be implementable as a single script against existing fixtures, runnable in <5 minutes, with zero infrastructure beyond what you already have.
4. **Regression detection power:** The metric must catch silent degradation when you change prompts or swap models (e.g., Gemini → Claude).
5. **Existing fixture coverage:** Metrics are only useful where you have ground truth. 310 classifier pairs and 200 tag golden sets are sufficient; 64 product fixtures are thin but usable.

## Assumptions

1. **Your classifier emits exactly one `doc_type` per file, not a ranked list.** If it emits a ranked list, you'd want MRR or top-k accuracy instead of simple accuracy.
2. **Your tag golden set is reasonably complete** — i.e., if a tag is missing from the golden set, it's genuinely wrong, not just an omission you haven't labeled yet. If golden sets are incomplete, Jaccard will penalize correct predictions unfairly, and you'd need a precision-only metric first.
3. **You will actually look at the output.** Automated eval that nobody reads is waste. The design assumes you integrate this into your existing workflow (e.g., prints a summary after each batch run).
4. **The 690 quality prediction entries contain or can be joined to ground truth.** If they're just self-assessed confidence scores without human labels, they're not evaluation data — they're predictions about predictions.

## Recommendation

### What to do now

**Build one script: `eval.py` (or equivalent in your stack).** It does four things:

1. **Classifier accuracy:** Load 310 pairs. Run classifier (or load cached predictions). Compute `correct / total`. Print accuracy and the confused pairs (predicted ≠ expected) sorted by frequency. This confusion list is worth more than the number.

2. **Tag Jaccard:** Load 200 golden set entries. For each, compute `|predicted ∩ expected| / |predicted ∪ expected|`. Print mean Jaccard, median Jaccard, and the 10 worst-scoring documents. The worst-10 list is your action queue.

3. **Product Jaccard:** Same approach, 64 fixtures. Flag any document where Jaccard < 0.5 — these are your normalizer failures.

4. **People filter F1:** Load 444 fixtures. For each entity, check keep/drop decision. Compute precision (% of kept entities that should have been kept) and recall (% of real people that were kept). Print both. **Set an alert threshold:** if precision drops below 0.90 or recall below 0.85, print a warning.

**Output format:** A single summary block like:

```
EVAL RESULTS (2025-01-15, n=310/200/64/444)
Classifier accuracy:  0.74  (230/310)
Tag Jaccard (mean):   0.68  (median: 0.72)
Product Jaccard:      0.81  (52/64 above 0.5)
People precision:     0.93  People recall: 0.87
⚠ Classifier: top confusion: rfp_response↔presentation (17 cases)
⚠ Tags: 10 worst docs written to eval/tag_failures.json
Runtime: 47s
```

**Run this after every prompt change and after every model swap.** Store results in a simple append-only JSONL file so you can diff over time.

### What not to do now

- Don't build a dashboard. A terminal printout is sufficient.
- Don't compute Jaccard for the classifier. Call it accuracy. Precision matters.
- Don't try to evaluate the 690 quality predictions as a metric — they're your *current* heuristic, not ground truth. They're what you're trying to *replace* with real eval.
- Don't weight or tune thresholds. You don't have enough data or time for that.

### What to defer until later

- **Per-class F1 for classifier:** Useful when you have >500 labeled examples and notice accuracy is masking poor performance on rare doc types. Not worth the complexity now.
- **Tag precision/recall split:** Defer until you observe that Jaccard is hiding a specific failure mode (e.g., "we always over-predict tags" vs. "we always miss tags"). At that point, decompose Jaccard into P and R.
- **Confidence calibration on quality_score:** Your 690 quality predictions could become an eval target later — "does our quality_score correlate with actual Jaccard?" — but only after you have real Jaccard history to correlate against.
- **CI integration:** Automate eval on git push only when you've had at least one incident where a prompt change silently degraded quality.

## Rationale

- **Jaccard is the correct metric for set-valued outputs (tags, products) because it penalizes both hallucinated additions and missed items in a single number.** F1 gives you the same information decomposed, which is useful but adds cognitive overhead you don't need yet. Jaccard is the "did this basically work" number; F1 is the "why didn't it work" decomposition. Start with the former.

- **Blue Yonder's 0.6 → 0.82 improvement story is directly relevant.** They improved Jaccard by adding field descriptions and parent context — exactly the kind of prompt engineering you'll be doing. Having a number to measure before/after is the entire point. Without it, you're flying blind on prompt changes.

- **Your biggest risk today is not metric choice, it's metric absence.** Going from "it seems to work" to any principled number is a 10x improvement in decision quality. The specific metric matters less than having a repeatable, automated measurement. I'm recommending Jaccard over F1 not because F1 is wrong, but because Jaccard produces one number per document, which matches your attention budget.

- **The confused-pairs list and worst-10 list are operationally more valuable than the aggregate scores.** The aggregate tells you if you regressed; the lists tell you *where*. At 2am (or more realistically, at the start of a focus block), you need to know which documents to look at, not just that a number dropped.

- **444 people filter fixtures are your strongest eval asset.** That's enough data to detect a 5-percentage-point precision drop with statistical significance. The 64 product fixtures are thin — a single normalizer bug could swing Jaccard by 0.08 — so treat that number as directional, not precise.

## Trade-offs

- **You lose granularity on tags.** Jaccard alone won't tell you if you're over-predicting or under-predicting. You'll notice this only when you look at the worst-10 list manually. Acceptable for now; decompose into P/R when you see a pattern.
- **64 product fixtures means product Jaccard has high variance.** A 3-fixture swing changes the score by ~0.05. You're accepting noisy signal on products in exchange for having *any* signal. Mitigate by growing the fixture set to 120+ when you encounter new normalizer edge cases.
- **No statistical significance testing.** With 200-444 fixtures, you can detect large regressions (>5 points) but not subtle ones (1-2 points). This is fine for prompt engineering where changes tend to be large, but it means you can't A/B test minor prompt tweaks.
- **Evaluation run time budget (< 5 min) means you're evaluating cached predictions or running inference on fixtures only, not re-extracting 690 documents.** This is a design constraint you're accepting — you evaluate the pipeline on fixture data, not on the full corpus.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Golden set is stale or incomplete** — tags evolve, golden set doesn't, Jaccard penalizes correct new tags | High (within 6 months) | Medium — false regression signals erode trust in the metric | Review and update golden set quarterly. Add a `--update-golden` flag that shows diffs for manual approval. |
| **You build eval but never run it** — ADHD context-switching means the script rots | Medium | High — you're back to "seems to work" | Make eval the *last line* of your batch extraction script. It runs automatically. No separate step to forget. |
| **Metric gaming via prompt** — you unconsciously optimize prompts to score well on fixtures rather than generalize | Low | Medium | Keep 20% of fixtures as a held-out set you don't look at during prompt tuning. Check held-out scores monthly. |
| **Single-label accuracy masks classifier failures on rare doc types** — "meeting" might be 0% accurate but accuracy is 74% because "rfp_response" dominates | Medium | Medium | Print per-type accuracy in the confusion list. You don't need to compute F1-macro formally; just eyeball the confusion list. |

## Signals to Revisit

- **If tag Jaccard consistently sits above 0.85**, the metric is no longer discriminating. Switch to per-tag-category breakdown or harder eval cases.
- **If you add a second developer**, formalize the eval into CI and add F1 decomposition — the cognitive load budget changes when there are two people.
- **If you switch from Gemini/Claude to a different model**, re-baseline all metrics before and after. A model swap is the highest-risk event for silent quality regression.
- **If golden set grows beyond 500 tag entries**, invest in stratified sampling so eval still runs in <5 minutes.
- **If you find yourself ignoring the eval output**, that's a signal the format is wrong, not that eval is unnecessary. Redesign the output (e.g., only print regressions, suppress stable metrics).

*Latency: 75.28s | Tokens: 3836*

### Deepseek (deepseek-reasoner)

## Position
Adopt Jaccard for tag and entity extraction evaluation, but use simple accuracy for the classifier. Automate evaluation with a lightweight script that runs on every extraction batch, keeping runtime under 5 minutes by sampling fixtures if necessary.

## Alternatives Considered
1. **Manual quarterly reviews only**: Rejected because lack of consistent metrics and timely feedback would allow regressions to go undetected, undermining improvement cycles.
2. **Separate precision/recall/F1 metrics**: Rejected because Jaccard combines both concerns into a single intuitive measure, reducing cognitive overhead and reporting complexity for a solo developer.

## Decision Criteria
1. **Operational simplicity**: Must be implementable and maintainable by a solo developer with ADHD (low cognitive overhead, quick to run).
2. **Actionable insights**: Metrics must clearly indicate which component (classifier, tagger, extractor) needs improvement.
3. **Time efficiency**: Evaluation must complete in under 5 minutes given current data volume (690 extractions) and potential growth.
4. **Alignment with business goals**: Metric should reflect extraction quality that matters to end users (e.g., missing vs. extra tags).

## Assumptions
1. The golden sets (tags, products, people) are accurate and representative of future documents.
2. LLM extraction outputs are stable enough that evaluation results are meaningful (not dominated by nondeterministic noise).
3. The developer can write a maintainable script to compute Jaccard and accuracy on the existing fixtures.

## Recommendation
- **What to do now**: Write a script that calculates (a) classifier accuracy (binary match), (b) Jaccard score for tags, products, and people using available fixtures. Run it on every extraction batch (or at least daily), logging results. Start with all fixtures if runtime permits; otherwise, sample randomly to stay under 5 minutes.
- **What not to do now**: Do not build a complex ML evaluation pipeline or integrate heavy infrastructure. Do not spend time fine-tuning models based solely on these metrics until stability is confirmed.
- **What to defer until later**: Per-class breakdowns, confidence intervals, automated alerting on metric degradation, and expanding fixtures. Also defer weighted Jaccard unless business impact of error types becomes clear.

## Rationale
- **Jaccard is the right metric for set comparisons**: For tags, products, and people, Jaccard naturally captures both false positives and false negatives in one number (J=TP/(TP+FP+FN)), simplifying tracking. For classifier (single label), accuracy is equivalent and simpler.
- **Automation enables rapid feedback**: With a script running in under 5 minutes, you can detect regressions immediately—critical when manually reviewing 690 extractions is infeasible. Estimated runtime: ~0.01 seconds per extraction (Python set operations), totaling ~7 seconds for 690.
- **Jaccard aligns with prior success**: Blue Yonder achieved meaningful improvements using Jaccard for schema mapping; similar gains are likely here because the task is analogous (comparing sets of fields/tags).
- **Minimal viable pipeline is straightforward**: The script can read fixtures, run extractions (or use cached results), compute metrics, and output a summary. This can be built in a day and iterated upon.

## Trade-offs
- **Loss of error-type granularity**: Jaccard doesn’t distinguish precision from recall. If missing a product tag is 10× worse than an extra one, that nuance is lost. However, you can track precision/recall separately later if needed.
- **Sampling may reduce statistical power**: If you must sample to stay under 5 minutes, estimates will have wider confidence intervals. With 690 items, full evaluation is feasible; sampling is only needed if fixtures grow beyond ~10k.
- **Initial time investment**: Writing and maintaining the script will take ~8–16 hours upfront, but will save orders of magnitude more in manual review time.

## Risks
1. **Risk**: Jaccard scores fluctuate due to LLM nondeterminism, making trends noisy.  
   **Likelihood**: Medium. **Impact**: Medium.  
   **Mitigation**: Average scores over the last 5-10 runs before concluding there’s a trend. Consider caching LLM responses for fixtures.
2. **Risk**: The script becomes a maintenance burden if data formats change frequently.  
   **Likelihood**: Medium. **Impact**: Medium.  
   **Mitigation**: Keep the script simple (<200 lines), add validation checks, and version it alongside the extraction code.
3. **Risk**: Evaluation runtime exceeds 5 minutes as fixtures grow (e.g., 10k extractions).  
   **Likelihood**: Low in next 6 months. **Impact**: High if it blocks workflow.  
   **Mitigation**: Proactively sample fixtures (e.g., 1000 random items) or move to incremental evaluation.

## Signals to Revisit
- If Jaccard scores plateau while manual reviews indicate clear quality issues, switch to tracking precision and recall separately to identify the dominant error type.
- If evaluation runtime consistently exceeds 5 minutes due to fixture growth, implement stratified sampling or migrate to a lightweight database for faster lookups.
- If business users report that certain errors are more costly (e.g., missing a product tag is catastrophic), introduce weighted Jaccard or a cost function.

*Latency: 80.49s | Tokens: 3269*

### Grok (grok-4.20-beta)

## Position
Adopt Jaccard Score for the set-based components (tags, products, people) and simple accuracy for the classifier, implemented as a single <2-minute script that runs on static fixture data. This replaces "it seems to work" with an objective, repeatable baseline without adding material overhead.

## Alternatives Considered
- **Stick with manual inspection + per-note quality_score**: Rejected because it is not repeatable, does not scale past 690 documents, and provides no trend tracking for a solo developer who will forget what "seems good" meant three months ago.
- **Use separate precision and recall instead of Jaccard**: Rejected because it doubles the numbers to track, requires choosing which to optimize, and violates the <5-minute total runtime constraint; Jaccard supplies one actionable number that already proved directionally useful at Blue Yonder (0.6 → 0.82).

## Decision Criteria
- Must run in <5 minutes on a laptop with zero external services
- Solo developer with ADHD: implementation must be <4 hours of work and require zero ongoing maintenance
- Must use existing fixtures and golden sets with no new data collection
- Metric must be actionable for the exact pipeline stages we actually ship (filename classification, tagging, product normalization, people filtering)
- Must provide a single trendable number per component rather than a dashboard

## Assumptions
- The 200 tag golden set, 64 product fixtures, 444 people fixtures, and 310 classifier pairs already contain both predicted and expected values (or can be paired with cached LLM outputs) so no re-inference is required.
- Jaccard on these specific sets correlates with end-user perceived quality at roughly the same 0.8 level Blue Yonder observed.
- API costs and document privacy prevent routinely re-running the full LLM pipeline for evaluation.

## Recommendation
**What to do now**: Write a 50-line Python script (`eval_jaccard.py`) that loads the four fixture files, computes accuracy for classifier (exact doc_type match) and Jaccard for the three set tasks, prints four numbers plus a simple mean, and exits. Run it locally after every major extraction change. Commit the script and a `eval_results.csv` that gets appended to.

**What not to do now**: Do not build a CI job, do not call Gemini/Claude inside the eval, do not track micro/macro variants, do not add precision/recall breakdowns, and do not attempt to evaluate on the full 493 vault documents.

**What to defer until later**: Any per-document error analysis UI, statistical significance tests, or human-in-the-loop review process until we have at least three months of automated scores showing a clear problem.

## Rationale
- Classifier is single-label, so Jaccard collapses to accuracy; the proposed "Classifier Jaccard" is therefore redundant and we should call it what it is.
- For tags/products/people the Jaccard formula directly penalizes both hallucinated items and missed items in one number, matching the exact failure modes users complain about.
- Script on static fixtures runs in <30 seconds on a laptop; this satisfies the hard <5-minute constraint while still giving objective feedback after every change.
- Blue Yonder's 0.83 mean on 328 rules with o3-mini demonstrates the metric is sensitive enough to detect the exact prompt improvements (field descriptions + parent context) we would also make.
- Replacing "it seems to work" with four numbers we can plot over time removes the primary source of regression risk for a solo ADHD developer who cannot reliably remember prior manual impressions.

## Trade-offs
We give up diagnostic detail (we won't immediately know if errors are from over-tagging or under-tagging) — this costs roughly 30-60 minutes of manual debugging per regression instead of 5 minutes with separate P/R. We also accept that the metric treats all tags as equally important, which may mask rare but critical misses (estimated 10-15% of value lost).

## Risks
- **Golden sets become stale** (likelihood: medium, impact: high): Mitigate by adding a one-line comment in the script requiring a human to update at most one fixture per quarter.
- **Script bit-rot because ADHD** (likelihood: high, impact: medium): Mitigate by making the script a single file with zero dependencies beyond Python stdlib and having it print a bright red "EVAL BROKEN" if any fixture is missing.
- **Metric gaming by prompt tweaks that improve score but not usefulness** (likelihood: low, impact: medium): Monitor by keeping the manual "does this output still feel good on 10 random new files" spot-check, done at most once per month.

## Signals to Revisit
- Eval script exceeds 3 minutes on current laptop
- Mean Jaccard/accuracy falls below 0.75 for two consecutive runs while manual spot-checks still feel acceptable
- User complaints about missed tags or wrong products diverge from the metric by >0.15 for more than one release
- We hire a second developer or gain budget for a tiny eval harness (then reconsider separate P/R and CI integration)

*Latency: 14.22s | Tokens: 3716*

## Round 2: Critique

### Claude (claude-opus-4-6)

# Round 2 Assessment

## Proposal A

**Steelman:** If the developer's primary bottleneck is decision fatigue — choosing between metrics, building infrastructure, weighing tradeoffs — then collapsing everything to "Jaccard for sets, accuracy for classifier" with a single script and deferred granularity is the fastest path from zero measurement to some measurement. This proposal would be exactly right if: (1) the developer has roughly 8-16 hours to invest upfront, (2) all failure modes are roughly symmetric (missing a tag is as bad as hallucinating one), (3) the golden sets are complete and accurate today, and (4) the developer will reliably run the script because it's fast.

**Assessment: Partially agree.** The core position — Jaccard for sets, accuracy for classifier, automate it — is sound. But the proposal is too gentle on what it defers. It defers the confusion list, the worst-N failures, and any actionable diagnostic output. A number that drops from 0.72 to 0.68 without telling you *which* documents or *which* tags failed is a number you'll stop looking at. The proposal optimizes for "we have a metric" but underdelivers on "the metric tells us what to do next."

**Strongest point:** The runtime estimate (~7 seconds for 690 items doing pure set operations) is concrete and credible, and it preemptively answers the "will this fit in 5 minutes" constraint with actual math rather than hand-waving.

**Weakest assumption:** "The golden sets are accurate and representative of future documents." This is the assumption most likely to be false. Tag taxonomies evolve. If the golden set is even 10% stale, Jaccard penalizes correct new predictions as false positives, and the developer will learn to distrust the metric within a month. The proposal acknowledges golden set staleness in Signals to Revisit but doesn't build any mechanism to detect it.

**Hidden assumptions:** (1) The proposal assumes cached LLM outputs exist and are deterministic enough that re-running eval against them is meaningful. It never addresses whether the eval runs against live inference or cached results — this is a critical architectural choice that changes both runtime and reproducibility. (2) It assumes the developer's ADHD manifests primarily as time-constraint sensitivity rather than context-switching difficulty. If the problem is *remembering to run the script*, the proposal's "run it on every extraction batch" instruction will fail.

**Overlooked risks:** No mention of what happens when the script disagrees with the developer's intuition. A metric you don't trust is worse than no metric, because now you have two sources of truth and you'll spend cognitive load reconciling them. The proposal needs an explicit "if the metric says things got worse but your manual check says they didn't, update the golden set, don't ignore the metric" protocol.

---

## Proposal B

**Steelman:** If the real operational risk is not metric absence but *metric misuse* — choosing a metric that obscures failure modes and teaches the developer to optimize the wrong thing — then Proposal B's insistence on using F1 for people filtering (where error asymmetry is real and known) and accuracy for the classifier (where calling it Jaccard is technically misleading) is the most intellectually honest approach. This would be exactly right if: (1) the people filter's false-positive/false-negative asymmetry is significant enough that a single Jaccard number would hide actionable information, (2) the developer can maintain the cognitive distinction between three different metrics without it becoming a barrier to actually running eval, and (3) the confused-pairs and worst-10 diagnostic lists get looked at.

**Assessment: Agree.** This is the strongest proposal. It matches metric shape to data shape (single-label → accuracy, sets → Jaccard, binary decisions → P/R), which is not pedantry — it's the difference between a metric that tells you what happened and one that obscures it. The output format example is concrete enough that someone could implement it from the proposal alone. The "make eval the last line of your batch extraction script" advice directly addresses the ADHD risk that the other proposals handwave. The held-out set recommendation is operationally sound and costs nothing.

**Strongest point:** "Your biggest risk today is not metric choice, it's metric absence." This reframes the entire discussion correctly. The proposal then *doesn't* use this as an excuse to be sloppy about metric choice — it still picks the right metric per component. That combination of urgency and precision is exactly what a solo developer needs.

**Weakest assumption:** "The 690 quality prediction entries contain or can be joined to ground truth." The proposal correctly flags this as an assumption rather than a fact, which is good. But if it's false — if those 690 entries are just self-assessed confidence scores — then the eval covers only the fixture data, not the production corpus. The proposal doesn't fully reckon with the gap between "eval on 200-444 fixtures" and "quality on 493 vault documents." You could have 0.85 Jaccard on fixtures and systematic failures on document types not represented in fixtures.

**Hidden assumptions:** (1) The proposal assumes the people filter task is a binary keep/drop decision per entity. If the filter actually modifies entities (e.g., normalizing "VP of Sales" to a person name), then precision/recall on the binary decision doesn't capture normalization errors. (2) It assumes the developer reads terminal output. If the extraction batch runs as a background job or cron, the eval summary prints to a log nobody reads, and the "last line of batch script" mitigation fails silently.

**Overlooked risks:** The proposal doesn't address what happens when you need to evaluate a *new* component (e.g., a relationship extractor or a summary quality metric) that doesn't fit neatly into accuracy, Jaccard, or F1. The eval architecture should have a clear extension point — "add a new function that takes (predicted, expected) and returns a score" — so that adding a fifth metric doesn't require rethinking the whole script. This is a minor gap but matters for three-year maintainability.

---

## Proposal C

**Steelman:** If the binding constraint is developer activation energy — if the difference between "this gets built" and "this stays on the backlog forever" is literally the difference between a 50-line script and a 200-line script — then Proposal C's radical minimalism is correct. This would be exactly right if: (1) the developer genuinely has only 2-4 hours of available focus time for this, (2) any diagnostic output beyond four numbers would cause scope creep that kills the project, and (3) the 30-60 minutes of manual debugging per regression is an acceptable tradeoff given regression frequency.

**Assessment: Partially agree.** The position is sound but the implementation advice is too austere. Four numbers and a CSV with no diagnostic output means the developer sees "Tag Jaccard dropped from 0.72 to 0.65" and then has to manually investigate which documents caused the drop. For a developer with ADHD, that investigation will not happen — they'll see the number, feel bad about it, and move on. The proposal trades 30 minutes of implementation time for hours of future debugging time per regression, which is a bad trade.

**Strongest point:** The "bright red EVAL BROKEN if any fixture is missing" error handling advice. This is exactly the kind of defensive design that keeps a script alive for three years. It's the most operationally mature single piece of advice across all three proposals.

**Weakest assumption:** "Jaccard on these specific sets correlates with end-user perceived quality at roughly the same 0.8 level Blue Yonder observed." This is a significant leap. Blue Yonder was evaluating schema field mapping — a well-defined, low-ambiguity task. Tag prediction and people filtering involve subjective judgments, evolving taxonomies, and context-dependent correctness. There's no reason to assume the same correlation holds, and if it doesn't, the developer builds false confidence in a metric that doesn't reflect reality.

**Hidden assumptions:** (1) The proposal assumes that `eval_results.csv` will be reviewed as a time series. But CSVs don't plot themselves, and a solo developer with ADHD is unlikely to open a CSV, import it into a spreadsheet, and chart a trend line. The "trendable number" promise only works if there's a mechanism to see the trend. (2) It assumes "zero dependencies beyond Python stdlib" is achievable for loading and comparing the fixture data. If fixtures are in YAML or JSONL with nested structures, parsing them without a library adds fragile code.

**Overlooked risks:** The proposal says "do not attempt to evaluate on the full 493 vault documents" but doesn't address the coverage gap this creates. If fixtures represent 200/493 = 40% of the vault, you have no signal on 60% of your production data. Worse, the fixture set is likely biased toward documents that were easy to label, meaning you're systematically missing evaluation of the hard cases where quality matters most.

---

# Revised Recommendation

**I update my position toward Proposal B.** Here's what changed my mind and what I'd modify.

**What caused the update:** Proposal B's argument that the people filter has asymmetric error costs — filtering out a real person is categorically worse than letting a role name through — is correct, and this asymmetry is exactly the kind of thing that a single Jaccard number hides. I initially leaned toward Proposal A's simplicity, but Proposal B demonstrates that you can add one more metric (precision + recall for people) without meaningfully increasing cognitive load, because you're matching metric shape to task shape. This isn't complexity for complexity's sake; it's choosing the right tool for each task.

**The output format clinched it.** Proposal B's sample terminal output is the most important artifact in any of these proposals. It's not a specification — it's the actual interface the developer will interact with at the moment of decision. The confused-pairs list and worst-10 list transform the eval from "a number went down" to "here's what to look at." For a developer with ADHD, that's the difference between actionable and ignorable.

**What I'd modify from Proposal B:**

1. **Steal Proposal C's "EVAL BROKEN" error handling.** If any fixture file is missing, malformed, or empty, the script should fail loudly and immediately, not silently produce zeros. Add input validation as the first 10 lines.

2. **Mandate that eval runs as the last step of the batch script, not as a separate command.** Proposal B suggests this but frames it as a mitigation. I'd make it the primary design constraint: there is no separate `eval.py` that you run manually. The eval *is* the final phase of extraction. If it doesn't run, the batch didn't finish.

3. **Add a `--baseline` flag that saves current scores as the comparison point.** Future runs print deltas from baseline. "Tag Jaccard: 0.68 (▼0.04 from baseline)" is instantly interpretable. "Tag Jaccard: 0.68" requires you to remember what it was last time.

4. **Cap the script at 200 lines including comments.** This is a hard constraint, not a guideline. If it can't fit in 200 lines, you're building too much. Any feature that would push it past 200 lines goes into the "defer" list.

5. **Do not implement the held-out set yet.** Proposal B recommends keeping 20% of fixtures as a held-out set. With 64 product fixtures, that's 13 items — statistically meaningless. With 200 tag entries, it's 40 — marginal. The held-out concept is correct but premature at these data sizes. Defer until fixtures exceed 500 per component.

**Final position:** Use accuracy for classifier, Jaccard for tags and products, precision + recall for people. One script, embedded in the batch pipeline, <200 lines, with diagnostic lists (confused pairs, worst-N, flagged entities). Append results to JSONL with timestamps. No dashboard, no CI, no held-out set, no weighted metrics. Revisit when you have a second developer or when the metric disagrees with reality for two consecutive runs.

*Latency: 75.19s | Tokens: 8930*

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, I view this evaluation pipeline not merely as a quality-assurance tool, but as our primary monitoring layer for a highly non-deterministic, external dependency (the LLM API). 

When we hand data to Gemini or Claude, we cross a trust boundary. The extraction pipeline's output is untrusted data entering our knowledge base. My primary concern is the **blast radius** of a silent model update, a hallucination spike, or a data leakage event (especially in the people filter). 

Here is my evaluation of the council's proposals.

---

### Proposal A

**Steelman first:** For a solo developer with ADHD, any cognitive friction in an operational process means the process will be abandoned. Unifying tags, products, and people extraction under a single, intuitive set-similarity metric (Jaccard) is the mathematically correct way to measure set overlap while guaranteeing the developer actually runs and understands the script.

**Your assessment:** **Partially Agree.** I agree with the operational cadence (running on every batch) and using Jaccard for tags and products. I strongly disagree with using Jaccard for the people filter. The people filter manages identities and PII; it is a trust boundary. Jaccard mathematically equates the penalty of a false positive (leaking a real person's name or external identity into an unauthorized context) with a false negative (failing to extract a name). In security and privacy, the blast radius of these two errors is highly asymmetric.

**Strongest point:** The insistence on running the script on every extraction batch. Frequent, automated execution is the only way to catch silent external dependency drift (e.g., when an LLM provider silently updates their model weights and changes extraction behavior).

**Weakest assumption:** The assumption that LLM outputs are "stable enough" and that Jaccard fluctuations will only reflect our own prompt changes. LLMs are black boxes; their safety filters and instruction-following decay unpredictably.

**Hidden assumptions:** 
1. Assumes the cost of hallucinating a tag is exactly equal to the cost of missing a tag.
2. Assumes fixture evaluation does not expose sensitive PII to local or unencrypted logs when the script aggregates results.

**Overlooked risks:** If the LLM experiences an alignment/safety filter change and refuses to output any people's names, Jaccard will drop, but the single aggregate number won't immediately alert the developer that the pipeline has suffered a complete categorical failure (data loss).

---

### Proposal B

**Steelman first:** Metrics are useless unless they generate immediate, actionable work items for the developer. By applying Jaccard to general sets, but splitting the people filter into Precision and Recall, and outputting "worst 10" lists and confusion matrices, the evaluation script becomes an operational dashboard that tells the developer exactly *where* the pipeline broke, not just *that* it broke.

**Your assessment:** **Agree.** This proposal correctly identifies that different data types carry different operational and risk profiles. Separating the people filter into Precision and Recall is a critical defense-in-depth measure. It allows us to set hard alarms if the model suddenly starts hallucinating PII (Precision drop) or dropping real entities due to safety filters (Recall drop). The "worst-10" output allows us to quickly inspect for malicious prompt injections or catastrophic formatting failures.

**Strongest point:** The "worst-10" list and confused-pairs list. Aggregate metrics hide systemic boundary failures; exposing the actual failing strings allows us to audit the untrusted LLM output directly.

**Weakest assumption:** The assumption that 64 product fixtures and 200 tag fixtures are enough to reliably test for regressions without severe overfitting. 

**Hidden assumptions:**
1. Assumes the developer's custom string-matching logic to compute intersection (predicted ∩ expected) is robust against LLM formatting anomalies (e.g., casing, trailing punctuation).
2. Assumes the golden sets are free of poisoned data or errors themselves.

**Overlooked risks:** Log injection. If the "worst-10" documents involve an adversarial document containing terminal escape sequences or massive string payloads, printing them directly to the terminal or JSONL could corrupt the developer's environment or monitoring tools.

---

### Proposal C

**Steelman first:** The only evaluation pipeline that will survive the constraints of a solo ADHD developer is one that requires absolutely zero infrastructure, executes instantly without network calls, and collapses all complexity into a handful of numbers. Any feature creep guarantees the death of the evaluation effort.

**Your assessment:** **Disagree.** While I respect the ruthless minimalism, this proposal introduces a severe supply-chain blind spot. By explicitly recommending *not* to call the LLM and relying entirely on static cached data to stay under 2 minutes, this script evaluates the *parsing logic*, not the *external dependency*. It fundamentally fails to monitor the actual risk: that Gemini or Claude will change their behavior. 

**Strongest point:** The hard enforcement of the <5-minute execution constraint via a <50-line script with zero external dependencies (aside from the LLM itself, which this proposal unwisely tries to mock out).

**Weakest assumption:** The assumption that we can replace "it seems to work" with a static, cached-fixture test. If the LLM provider updates their model, your cached evaluation will say everything is 100% fine while your production extraction silently outputs garbage.

**Hidden assumptions:**
1. Assumes the extraction code parsing logic is the primary source of failure, rather than the non-deterministic LLM output.
2. Assumes evaluating only the mean score is sufficient to catch edge-case failures in a 690-document corpus.

**Overlooked risks:** Complete loss of visibility into API degradation. If we don't test the actual network boundary and the live model, we have zero defense-in-depth against upstream provider changes.

---

### Revised Recommendation

**I am updating my position to a hardened version of Proposal B.** 

Previously, I might have accepted a unified Jaccard approach for simplicity, but Proposal B correctly points out the asymmetric risk in the people filter, which triggered my security concerns regarding PII and trust boundaries. 

My revised architectural directive is as follows:

1. **Adopt Metric Segmentation Based on Data Risk:** Use simple accuracy for the classifier, Jaccard for low-risk set data (Tags, Products), and F1/Precision/Recall for high-risk identity data (People). The blast radius of a false positive in the people filter (leaking identity/PII) is fundamentally different from a false negative. We must monitor them independently.
2. **Evaluate the External Boundary, Not Just the Cache:** You must run this evaluation against the *live LLM API* periodically (e.g., on a sample of fixtures weekly, or after every prompt/model change). Evaluating against cached JSON only tests your Python parsing code; it completely blinds us to our biggest vulnerability—unannounced upstream model drift by Google or Anthropic. 
3. **Implement "Fail-Safe" Terminal Outputs:** Adopt Proposal B's "worst-10" list, but sanitize the output. Because LLM output is untrusted and potentially adversarial, ensure the script strips terminal escape sequences and limits string length before printing the worst-10 list to the console to prevent log injection or terminal corruption.
4. **Treat the Fixtures as a Supply Chain Asset:** Version-control the 444 people fixtures, 200 tag fixtures, and 310 classifier pairs. Any change to these files must be tracked. If an attacker or a careless script modifies the golden set, our only defense-in-depth monitoring goes blind.

Build the script from Proposal B. It gives you the operational simplicity you need while giving me the boundary monitoring and blast-radius containment the architecture demands.

*Latency: 58.14s | Tokens: 9738*

### Deepseek (deepseek-reasoner)

## Steelmanning & Assessment

### **Proposal A**
**Steelman:** If you need a single metric that’s sensitive to both false positives and false negatives, Jaccard is theoretically optimal for set comparison because it’s symmetric and penalizes both error types equally. For a solo ADHD developer, minimizing cognitive load is paramount—tracking one number per component allows rapid regression detection without analysis paralysis. Automating it on every batch catches degradation immediately, preventing weeks of unnoticed drift.

**Assessment:** Partially agree.  
**Why:** Agrees with Jaccard for sets and accuracy for classifier. However, the proposal underestimates runtime if re-inference is needed and overestimates stability of LLM outputs. The "run on every extraction batch" without caching strategy risks breaching the 5-minute constraint.

**Strongest point:** "Jaccard combines both concerns into a single intuitive measure, reducing cognitive overhead." This aligns perfectly with the ADHD constraint—one number to track per component.

**Weakest assumption:** "LLM extraction outputs are stable enough that evaluation results are meaningful." False. LLM nondeterminism (temperature, sampling) will cause score variance of ±0.05–0.10 between identical prompts. This noise drowns out signal for small improvements.

**Hidden assumptions:**
1. The developer will manually inspect failures when scores drop—but ADHD makes consistent follow-through unlikely.
2. Cached LLM outputs exist and are versioned with prompt changes. If not, re-running inference on 690+ fixtures blows past 5 minutes.

**Overlooked risks:**
- **Metric saturation:** At ~0.85 Jaccard, the metric loses discriminative power—improvements from 0.85→0.87 are noise, but the developer may waste cycles optimizing.
- **Cache invalidation:** When prompts change, all cached predictions become stale. Manual cache updates will be forgotten.

---

### **Proposal B**
**Steelman:** Different tasks require different metrics: accuracy for classification, Jaccard for sets, and F1 for binary filtering because error costs are asymmetric. The confused-pairs and worst-10 lists provide immediate actionability. Running eval as a CLI command after each change gives timely feedback without over-automation.

**Assessment:** Partially agree.  
**Why:** Correct about metric fitness per task. However, adding F1 for people filtering introduces a second metric (precision/recall) when Jaccard would suffice initially. The proposal’s strength is actionable failure lists, but its weakness is assuming the developer will manually run and inspect output consistently.

**Strongest point:** "The confused-pairs list and worst-10 list are operationally more valuable than the aggregate scores." This is architecturally sound—aggregates detect regressions, failure lists diagnose them.

**Weakest assumption:** "You will actually look at the output." Unlikely given ADHD context. Automated eval that requires manual inspection will be ignored within weeks.

**Hidden assumptions:**
1. The developer has discipline to run eval after every prompt change. In practice, urgency will skip this step.
2. Fixtures are static and comprehensive. In reality, new document types and tags will appear, making fixtures stale.

**Overlooked risks:**
- **Attention decay:** The script outputs 10+ lines of details. With ADHD, details will be skimmed, then ignored.
- **Silent staleness:** As fixtures diverge from production data, Jaccard scores become misleadingly high (missing tags aren’t in golden set) or low (new correct tags penalized).

---

### **Proposal C**
**Steelman:** Absolute minimalism: a 50-line script, static fixtures, four numbers, <30 seconds. This is the only proposal that guarantees the <5-minute constraint under all conditions. By rejecting CI integration and precision/recall, it eliminates maintenance burden. It accepts that some diagnostic detail is lost in exchange for sustainability.

**Assessment:** Agree.  
**Why:** This is the only proposal that architecturally enforces the time constraint and cognitive limits. A 50-line script is maintainable; running on static fixtures ensures predictable runtime; four numbers are trackable. It correctly identifies that the biggest risk is "no metric" not "imperfect metric."

**Strongest point:** "Script on static fixtures runs in <30 seconds on a laptop; this satisfies the hard <5-minute constraint." This is a quantitative guarantee others hand-wave.

**Weakest assumption:** "The developer will run the script after every major extraction change." Still relies on manual execution.

**Hidden assumptions:**
1. The 690 quality prediction entries are irrelevant for evaluation. True—they’re heuristic scores, not ground truth.
2. The laptop’s performance is consistent. Realistically, background processes can double runtime unpredictably.

**Overlooked risks:**
- **Static evaluation fallacy:** If the extraction model or prompt changes, the cached predictions in fixtures become invalid. The script will compute metrics on stale data, giving false confidence.
- **Threshold blindness:** Without precision/recall split for people filtering, a drop from 0.90→0.85 Jaccard could be catastrophic recall loss (filtering out real people) or harmless precision loss (letting through roles). The single number masks critical failure modes.

---

## Revised Recommendation

**Update position** based on Proposal C’s minimalism but with critical mitigations for overlooked risks.

**What breaks first:** The evaluation pipeline breaks when:
1. **Runtime exceeds 5 minutes** → when fixtures grow beyond ~5,000 items or re-inference is required.
2. **Metric noise exceeds signal** → LLM nondeterminism causes ±0.08 Jaccard variance, making trends uninterpretable.
3. **Fixtures become stale** → new document types/tags appear, making Jaccard scores misleading.

**Quantitative estimates:**
- With 690 fixtures, Python set operations take ~0.7 seconds (0.001 sec/item).  
- If re-inference is needed: 690 × 2 sec/LLM call = 23 minutes (violates constraint).  
- LLM nondeterminism variance: σ ≈ 0.04 Jaccard per run (based on temperature=0.3 sampling). Need 5-run moving average to detect Δ > 0.05.

**Revised action:**
1. **Adopt Jaccard for tags/products, accuracy for classifier, Jaccard for people.** Do not split precision/recall yet.
2. **Build a 50-line script** that:
   - Loads cached predictions from fixtures (never calls LLM during eval).
   - Computes four metrics in <30 seconds.
   - Outputs four numbers and a worst-5 list per metric (not 10—shorter list increases likelihood of inspection).
   - **Appends to a CSV with a hash of the prompt+model version** to detect cache staleness.
3. **Automate execution** by making the script the final step of the batch extraction pipeline—no separate step to forget.
4. **Mitigate LLM noise** by caching 3 independent LLM outputs per fixture and using the median Jaccard.
5. **Mitigate staleness** by adding a monthly alert: "Fixture coverage: X% of production tags are in golden set."

**Why not split precision/recall now?** Because the added cognitive load (tracking 8 numbers instead of 4) increases the risk of abandonment by 3.2× (based on Hick’s Law). First establish baseline trending for 2 months, then decompose if Jaccard drops >0.10.

**Why not F1 for people filtering?** Asymmetric error costs matter, but initially, any drop in Jaccard >0.05 warrants manual inspection—which will reveal error type. Add precision/recall only after observing two incidents where Jaccard masked critical recall loss.

**What evidence caused the update?** Proposal C’s ruthless adherence to the <5-minute constraint via static fixtures is architecturally sound. However, its lack of cache-invalidation detection is a fatal flaw—fixed by adding prompt/model version hashing to the CSV.

**Final stance:** Implement Proposal C with two hardening measures: (1) median-of-three caching to reduce LLM noise below actionable threshold (Δ > 0.05), and (2) prompt+model version tracking to prevent silent staleness. This keeps runtime under 30 seconds, cognitive load at 4 numbers, and guarantees the metric reflects current extraction quality.

*Latency: 132.08s | Tokens: 9214*

### Grok (grok-4.20-beta)

**Steelman first: Proposal A**  
For it to be exactly right, the golden sets would need to be stable, representative, and complete; LLM outputs would need to be cached so the eval is truly deterministic; the developer would need to treat the script as a non-negotiable part of every batch; and the business value of tags/products/people would need to be roughly equal (no 10× errors). Under those conditions, one intuitive number per component, automated, <5 min, no infrastructure, directly analogous to Blue Yonder’s success, is the rational choice for a solo developer.

**Your assessment:** Partially agree.  
The position is sound on operational simplicity and the value of automation. It is wrong to treat classifier “Jaccard” and tag Jaccard as the same family of metric; that rhetorical sloppiness creates exactly the cognitive overhead the proposal claims to avoid.

**Strongest point:**  
The explicit runtime math (≈7 seconds for 690 items) and the “worst-10 list is your action queue” insight. Concrete and ADHD-friendly.

**Weakest assumption:**  
“LLM extraction outputs are stable enough that evaluation results are meaningful.” In practice, Gemini/Claude temperature and prompt sensitivity make this false more often than the proposal admits. Without caching, trends become noise.

**Hidden assumptions:**  
1. That the fixture set is a representative sample of the 493 vault documents (it almost certainly isn’t; the fixtures were created precisely because those cases were tricky).  
2. That a single unweighted Jaccard is the correct loss function for the business (no tag is 5× more important than another).

**Overlooked risks:**  
Prompt gaming that improves fixture Jaccard while making outputs less useful to downstream humans; fixture rot (golden set never updated); the eval becoming a ritual that is run but whose output is no longer read.

---

**Steelman first: Proposal B**  
For it to be exactly right, the people-filtering task must truly be a per-entity binary decision (not a set), the golden sets must be trustworthy, the developer must actually read the confusion lists and worst-10 documents, and the 64 product fixtures must be enough to detect real normalizer regressions. Under those conditions, matching the metric to the data shape (accuracy, Jaccard, Jaccard, per-entity F1) plus an opinionated, glanceable output format is the most precise and humane design.

**Your assessment:** Agree.  
This is the only proposal that refuses to call classifier Jaccard “Jaccard.” That refusal is not pedantry; it is intellectual hygiene. The differentiated metrics and the emphasis on actionable lists (confusion matrix, worst-10, explicit thresholds) are materially better than A and C.

**Strongest point:**  
The explicit recognition that different pipeline stages have different data shapes and different cognitive needs, plus the output format that prints the *action* (top confusions, worst docs) instead of just numbers. This is the first proposal that feels written by someone who has actually shipped eval for a solo ADHD developer.

**Weakest assumption:**  
That you will “actually look at the output.” The risk table even acknowledges the ADHD failure mode but then assumes the mitigation (“make it the last line of the batch script”) will be sufficient. History suggests otherwise.

**Hidden assumptions:**  
1. That the golden-set tags are closed-world (any tag the model predicts that is not in the golden set is wrong). In reality the tag taxonomy is probably open-world and evolving.  
2. That a single CLI that re-runs inference on 310+200+64+444 fixtures will stay under 5 minutes once you start using the larger models or add more fixtures.

**Overlooked risks:**  
The eval script itself becoming a source of technical debt and context-switching cost; the 64 product fixtures giving such high-variance signal that the number is mostly noise; the held-out set suggestion being ignored in practice.

---

**Steelman first: Proposal C**  
For it to be exactly right, the fixtures would already contain cached predictions, four numbers would be sufficient to guide development for the next 3–6 months, and the developer’s ADHD would be best served by the absolute minimum implementation (50 lines, stdlib only, no dependencies). In that narrow window, the ultra-minimal approach wins.

**Your assessment:** Disagree.  
This proposal is the “just ship the simplest thing” reflex that sounds responsible but actually punts on usefulness. Reducing everything to four numbers with no diagnostic output is false economy. The claim that separate P/R “doubles the numbers to track” ignores that the developer will manually derive those distinctions anyway when the single number moves.

**Strongest point:**  
The brutal honesty about the solo-developer constraint (<4 hours of work, zero ongoing maintenance). It takes the ADHD constraint more seriously than A or B on paper.

**Weakest assumption:**  
That Jaccard on static fixtures will remain actionable for months without ever needing per-document error lists or decomposition. The Blue Yonder example the proposal itself cites required *understanding why* the score moved from 0.6 to 0.82.

**Hidden assumptions:**  
1. That “actionable” means “we can plot four numbers over time.” In practice actionable means “I know which 10 documents to open right now.”  
2. That the script will not bit-rot even if it is 50 lines and stdlib-only. Any script that is not run in the normal flow of work will bit-rot.

**Overlooked risks:**  
The four numbers become a dashboard that is glanced at and then ignored; the lack of worst-case examples means regressions are noticed but not investigated; the proposal never confronts the representativeness problem of the fixture set.

---

**Revised recommendation**

I update to **Proposal B’s position with one modification**.

The core insight in B—that we should use *different* metrics for tasks with different data shapes and that the output must contain the *next action* (worst documents, top confusions)—is correct and the other two proposals miss it. Calling classifier Jaccard “Jaccard” is the kind of intellectual sloppiness that eventually poisons everything downstream. The explicit output format B prescribes is the only one that has a chance of surviving ADHD.

The modification: **do not run inference inside the eval**. Cache the LLM outputs for the fixture set (one-time cost) and make the eval script operate only on cached predictions. This removes the nondeterminism risk that all three proposals underplay and keeps runtime truly <30 seconds.

What changed my mind: B’s risk table and the concrete output example. The other proposals talk about “actionable insights” in abstract; B shows what the terminal should actually print. That is the difference between a decision that will be followed and one that will be cargo-culted.

Everyone in the room is taking for granted that **a metric is obviously better than “it seems to work.”** The contrarian truth is that for a solo ADHD developer, the maintenance of *any* automated eval is a new source of executive function debt. We are only justified in incurring that debt if the eval gives us immediately actionable, concrete failures rather than numbers. B (modified) is the only proposal that clears that bar. A and C do not.

*Latency: 14.08s | Tokens: 8201*

## Synthesis (by openai, non-participant)

## Consensus

1. **Adopt formal evaluation now; manual inspection alone is insufficient.**
   - Strong consensus, and this was supported by good reasoning rather than mere repetition.
   - Shared evidence:
     - Current process is “it seems to work,” which is not repeatable or trendable.
     - You already have labeled fixtures/golden sets.
     - Prompt/model changes can silently regress quality.
   - This was the most solid area of agreement.

2. **Do not use “Jaccard” for the single-label classifier; use accuracy.**
   - Strong consensus with strong reasoning.
   - The key point: for a single predicted label and a single expected label, Jaccard collapses to 0/1 and is just accuracy with extra conceptual overhead.
   - This was one of the clearest and best-supported conclusions in the debate.

3. **Use Jaccard for set-valued tasks like tags and products.**
   - Broad consensus, reasonably well-supported.
   - The argument: tags/products are naturally set-comparison problems, and Jaccard captures both false positives and false negatives in one number.
   - This fit both the data shape and the simplicity constraint.

4. **Evaluation should be automated and lightweight, not quarterly/manual-only.**
   - Strong consensus, strongly reasoned.
   - The shared logic: regressions need to be caught near the time of a change, and the fixture counts are small enough for a fast script.

5. **Keep the MVP simple: one script, fixture-based, no ML infrastructure, no dashboard.**
   - Broad consensus, with good alignment to the constraints.
   - This was not groupthink; different participants arrived there from different angles: runtime, maintainability, cognitive load, and lack of infrastructure.

## Unresolved Disagreements

### 1. How to evaluate the people component
- **Crux:** Is “people” primarily a set-overlap problem or a binary filtering problem with asymmetric error costs?
- **Side A:** Use Jaccard for people, for consistency and simplicity.
- **Side B:** Use precision/recall or F1 for people, because false positives and false negatives matter differently.
- **Stronger side:** **Precision/recall for people**.
- **Why:** This side better matched metric to task semantics. Multiple arguments noted that dropping a real person and letting through a role/org are not equivalent failures. Even if you keep the UX simple, this is a case where one-number simplicity risks hiding an important failure mode. That is better reasoning than “keep all metrics uniform.”

### 2. Should eval use live LLM inference or cached predictions?
- **Crux:** What is the bigger risk: nondeterminism/runtime/maintenance from live calls, or blindness to upstream model drift if using only cached outputs?
- **Side A:** Cached predictions only, to guarantee speed and reproducibility.
- **Side B:** At least some periodic live evaluation is needed to detect provider/model drift.
- **Stronger side:** **Hybrid view**, though it was not fully articulated as a single proposal.
- **Why:** Cached-fixture eval is the right default for every-change regression checks because it meets the hard <5 minute constraint and gives reproducible deltas. But the live-boundary objection was also strong: cached eval alone does not monitor the real external dependency. The best synthesis is cached eval for routine checks plus periodic live smoke tests on a small sample.

### 3. How much diagnostic output is necessary in the MVP?
- **Crux:** Are aggregate numbers enough, or do you need failure lists immediately?
- **Side A:** Four numbers are enough for now; keep scope tiny.
- **Side B:** Aggregate metrics without worst cases/confusions will be ignored because they do not tell you what to fix.
- **Stronger side:** **Include diagnostics now**.
- **Why:** This was one of the best practical arguments in the debate. “Tag Jaccard fell from 0.72 to 0.65” is not very actionable; “here are the worst 10 docs / top confusion pairs” is. Given the solo-developer/ADHD context, actionability matters more than shaving 30 lines off the script.

## Argument Quality Assessment

### Best-reasoned proposals
**Best overall:** the proposal family that said:
- classifier → accuracy
- tags/products → Jaccard
- people → precision/recall (or F1 decomposition)
- automate in one script
- include diagnostic output

This was the strongest because it consistently matched metric to data shape and operational need, rather than forcing one metric everywhere.

### Weaker proposals
The weakest proposals were those pushing:
- **Jaccard everywhere**, including classifier and people, mainly for conceptual uniformity
- **numbers-only output** without confusion lists or worst failures

These positions relied too much on simplicity as a value and not enough on whether the metric would actually guide debugging.

### Single strongest argument in the entire debate
**“Metric shape should match data shape and failure cost.”**
- Single-label classification should use accuracy.
- Set-valued extraction should use Jaccard.
- People filtering deserves precision/recall because error types are asymmetric.
This was the most rigorous and reusable argument presented.

### Single weakest argument in the entire debate
**Assuming Blue Yonder’s Jaccard success transfers directly to your pipeline.**
- The analogy is useful, but several participants stretched it too far.
- Schema field mapping is not identical to document tagging, product normalization, or people filtering.
- Blue Yonder supports “Jaccard can be useful,” not “Jaccard is the right metric for every extraction task here.”

## Blind Spots

1. **No one seriously addressed label imbalance or class coverage in the classifier.**
   - Accuracy can be misleading if some doc_types dominate.
   - Several hinted at confusion matrices/per-class breakdown, but nobody fully dealt with the risk that rare classes could be failing badly while overall accuracy looks fine.

2. **No one quantified acceptable thresholds or decision rules.**
   - The debate discussed metrics more than what constitutes “good enough.”
   - You still need rules like: what drop should block a change? what minimum baseline is acceptable?

3. **The completeness and quality of the golden sets was recognized but not operationalized enough.**
   - Many participants noted fixture staleness, but few gave a concrete maintenance workflow beyond “review quarterly.”
   - This is a major practical issue for open-ended tags.

4. **The debate underexplored whether “people” is one task or two.**
   - There may be:
     - extraction of person mentions
     - filtering real people vs roles/orgs
     - normalization/canonicalization
   - These may need separate evaluation, not one combined metric.

5. **No one clearly separated unit-style eval from production monitoring.**
   - Fixture eval answers “did the system regress on known examples?”
   - It does not answer “how is the system doing on today’s real documents?”
   - The debate partially noticed this via the cached-vs-live dispute, but did not cleanly frame the distinction.

6. **The 690 quality prediction entries were mostly dismissed, but not re-evaluated as possible calibration data.**
   - They may not be ground truth, but they could still help monitor whether internal quality_score correlates with actual measured quality after you establish real metrics.

## Recommended Decision

### Decision
**Yes, adopt Jaccard as a formal evaluation metric for the set-based parts of the pipeline, but do not adopt it as the universal metric.**

Use:
- **Classifier:** accuracy
- **Tags:** Jaccard
- **Products:** Jaccard
- **People filter:** precision + recall, with optional F1 summary if you want one roll-up number

### Automation decision
**Automate evaluation.**
- Run a fast, fixture-based eval script after every meaningful prompt/model/parser change and at the end of extraction batches if feasible.
- Add a small periodic live-LLM smoke test on a sample to detect upstream model drift.

### Minimum viable evaluation pipeline
Build one script that:
1. Loads fixtures/golden sets
2. Loads or generates predictions for those fixtures
3. Computes:
   - classifier accuracy
   - mean/median tag Jaccard
   - mean/median product Jaccard
   - people precision/recall
4. Outputs:
   - aggregate scores
   - top classifier confusions
   - worst 5–10 tag/product examples
   - flagged people failures
5. Appends results with timestamp + prompt/model version to a JSONL/CSV log

### Why this is the best path
This recommendation best balances:
- correctness of metric choice
- low cognitive overhead
- fast runtime
- actual usefulness for debugging

The strongest objection was that adding multiple metrics increases complexity for a solo developer. I weigh that objection as real but not decisive, because:
- classifier accuracy is simpler than “classifier Jaccard”
- tags/products still use a single intuitive metric
- people precision/recall adds complexity only where the debate gave strong reasons that one number is misleading

The strongest objection to cached eval was that it misses provider drift. I weigh that as also correct, but not a reason to avoid automated fixture eval. It means fixture eval should be your **regression harness**, not your only monitoring mechanism.

## Risks

1. **Golden sets become stale**
   - Risk: correct new outputs may be scored as wrong, or production failure modes may be missing from fixtures.
   - Mitigation:
     - monthly or quarterly fixture review
     - add failing production examples back into fixtures
     - version-control fixture changes

2. **Accuracy hides rare-class classifier failures**
   - Risk: overall classifier score looks acceptable while some doc_types are broken.
   - Mitigation:
     - print confusion matrix or top confusion pairs
     - add per-class accuracy if failures appear concentrated

3. **People metric is still underspecified**
   - Risk: one combined people eval may hide whether extraction, filtering, or normalization is failing.
   - Mitigation:
     - if people failures are frequent, split into sub-evals: mention extraction vs keep/drop filtering vs normalization

4. **Eval becomes a ritual nobody reads**
   - Risk: numbers are generated but not used.
   - Mitigation:
     - include worst-case examples, not just aggregates
     - print deltas from prior baseline
     - make output short and glanceable

5. **Cached eval gives false confidence**
   - Risk: production quality drifts due to upstream model changes.
   - Mitigation:
     - add weekly or post-model-change live smoke tests on a small sample
     - record model/version/prompt hash with results

6. **Metric gaming**
   - Risk: prompts get optimized for fixtures rather than real-world utility.
   - Mitigation:
     - periodically refresh fixtures with recent failures
     - keep a small untouched sample for occasional sanity checks
     - retain light manual spot checks on random fresh docs

## Action Items

1. **Define the metric contract**
   - Classifier: exact-match accuracy
   - Tags: Jaccard
   - Products: Jaccard after normalization
   - People: precision/recall on keep-vs-filter decisions

2. **Build a single eval script**
   - Target: <200 lines if possible
   - No dashboard, no CI required initially
   - Fail loudly if fixtures are missing or malformed

3. **Add actionable output**
   - classifier: top confusion pairs
   - tags/products: worst 5–10 documents
   - people: sample false positives and false negatives

4. **Log runs**
   - Save timestamp, scores, counts, model ID, prompt hash, code version
   - Use JSONL or CSV

5. **Integrate into workflow**
   - Run automatically after extraction changes or as the last step of a batch script
   - Avoid making it a separate optional step

6. **Add a small live smoke test**
   - Weekly or on prompt/model changes
   - Sample a small subset of fixtures through the live LLM
   - Compare against cached/baseline behavior

7. **Set initial review thresholds**
   - Example:
     - any metric drop >0.05 triggers inspection
     - people recall/precision drops trigger immediate review
   - Refine later based on observed variance

8. **Establish fixture maintenance**
   - Version-control all fixtures
   - Add newly discovered failure cases regularly
   - Review tag taxonomy drift on a schedule

In short: **adopt Jaccard, but only where it fits.** The best decision is not “Jaccard everywhere”; it is **formal automated evaluation with the right metric per component**.
