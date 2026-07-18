# Algorithmic Adopt-Map — Formalizing the Chaos Problem (T5 × T2/T4+ core)

> **Consumed by:** `docs/audits/2026-07-06-technical-architect-intake.md` + intake-16 (§2 scoring) → BACKLOG #38, #39 (FR-11/FR-14).

**Repo:** corp-monorepo · **Audience:** functional intake / technical architect
**Status:** brainstorm-phase blueprint (audit-space per DR-14; nothing implemented)
**Date:** 2026-07-07 · **Session:** functional-architect sitting #2 · **Companion:** `2026-07-07_BRIEF_golden-url-registry-knowledge-flow.md`

---

## 1. Problem, formalized

The operator's raw statement: hundreds of GB of chaotic corporate material; the system must LEARN the terrain, catch essence, connect it, and keep learning — with solvers, predictive components, and local models where they genuinely earn their keep. This brief converts the intuition ("Monte Carlo, komiwojażer, solvery, lokalne modele") into named problem classes, each mapped to a concrete OSS candidate and an adoption trigger. Governing rules: adopt-before-build (ratified), solo sizing (Council #10), over-engineering is the documented #1 killer.

**The single most important structural fact:** every learning surface in the estate currently has **0 rows**. No algorithm below can learn from data that was never emitted. Therefore §5 (telemetry spine) is the only component with an unconditional "adopt now" — everything else has a trigger.

## 2. The map — problem → mathematical class → OSS → trigger

### 2.1 Exploration order under budget → **Multi-Armed Bandit** (not TSP — an honest downgrade)

- **Operator instinct:** komiwojażer / traveling salesman. Correct family, wrong member. The academic form of "visit locations to maximize reward within a budget" is the **Orienteering Problem / budgeted prize-collecting TSP** (prize-maximization under a knapsack-type travel budget). But OP's hardness comes from *routing structure* — travel costs between locations. Our scout has no meaningful travel cost: every Graph probe costs roughly the same. Strip the routing and OP collapses into: *which locations to sample next, given uncertain yields, learning as you go* — the textbook **multi-armed bandit** (exploration/exploitation under sequential decisions).
- **Fit to our problem:** each golden root / candidate subtree = an arm; a cycle's exploration budget = pulls; realized yield (useful docs found, per §3 scoring) = reward. Thompson sampling naturally handles new arms (new golden URLs arriving — the operator's "kolejkowość") and decays stale beliefs.
- **OSS:** **MABWiser** (Fidelity; epsilon-greedy, UCB1, Thompson sampling, contextual LinUCB; parallelizable) — or a ~50-line hand-rolled Beta-Bernoulli Thompson sampler, which at 6–30 arms is honestly sufficient. Adopt-before-build says try MABWiser first; sizing says don't be ashamed of the 50 lines.
- **Trigger:** the moment the scout loop exists and has >1 cycle of yield data. Day-1 the queue can be round-robin; bandit replaces it at cycle 3+.
- **NOT:** OR-Tools routing/OP solvers — only if per-location exploration costs ever diverge by an order of magnitude (e.g., throttled sites); no evidence today.

### 2.2 Knowing what's in 1.1 TB without reading it → **Monte Carlo / stratified sampling**

- **Class:** statistical estimation. Instead of crawling the terrain, draw a stratified random sample per stratum (site × library × age-band), extract the sample, and estimate per-stratum yield distributions with confidence intervals. This is how the model "learns what's inside" at 1/1000th of the cost — and it directly feeds the bandit's priors (§2.1) and the yield scores in the registry brief.
- **OSS:** none needed — numpy + a sampling design. The engineering is the *design* (strata, sample size per stratum, estimator), not the library.
- **Trigger:** immediately available on the data paths in §4; this is the cheapest high-information action in the whole map.

### 2.3 Collapsing redundancy → **MinHash LSH (Jaccard) near-duplicate detection**

- **Class:** probabilistic similarity sketching. MinHash signatures + locality-sensitive hashing find near-duplicate documents at massive scale without pairwise comparison — the standard technique for dedup in web-scale corpora.
- **Fit:** corporate terrain is full of deck-version sprawl (v1/v2/final/FINAL2) and mirrored copies; the vault already surfaced 325 dedup-losers (DR-3). Dedup-at-ingest keeps the essence store from re-importing noise; dedup-on-terrain-sample estimates the true (unique) size of a location — a direct input to yield scoring.
- **OSS:** **datasketch** (v2.0.x; MinHash + MinHashLSH; scales to hundreds of millions of docs with optional Redis/Cassandra backends — we need none of that at our size).
- **Trigger:** first terrain sample (§4) — run dedup on the sample as part of the learning pipeline; adopt at ingest when W1 restarts (DR-6 batch lane).
- **NOT:** semantic dedup via embeddings day-1 — MinHash is cheaper and catches the dominant failure mode (copy sprawl); semantic near-dup only if MinHash demonstrably misses.

### 2.4 Chaos → candidate topics (proto-ontology induction) → **local embeddings + density clustering**

- **Class:** unsupervised structure discovery. Pipeline: local sentence embeddings → UMAP dimensionality reduction → HDBSCAN density clustering → c-TF-IDF topic labels. HDBSCAN's decisive property for chaotic data: it does NOT force documents into clusters — outliers stay outliers, so noise doesn't corrupt topics.
- **Fit:** this is the mechanical bridge from T4+ terrain to T1/T2. Bottom-up induced topics from real documents get reconciled against the top-down industry × software dimensions: matches confirm the taxonomy, orphan clusters propose new tags, and persistent outliers ARE the map of "chaos we don't understand yet." The ontology (T2) stops being a whiteboard exercise and starts being fitted to data.
- **OSS:** **BERTopic** (sentence-transformers `all-MiniLM-L6-v2` runs fully local; UMAP + HDBSCAN + c-TF-IDF; modular — every stage swappable). First LOCAL-model milestone in the estate, and it's an embedding model, not a chat model — the honest entry point.
- **Trigger:** ≥ ~200 extracted documents available (sample from §4 + existing vault S2 notes qualify already: 488 indexed notes are a valid first corpus).
- **NOT:** LLM-labeled taxonomies as the source of truth — induced topics PROPOSE, the operator's charter (T1) DISPOSES.

### 2.5 Retrieval upgrade → **vector search next to FTS5** — NOT YET

- **Class:** approximate nearest-neighbor over embeddings (FAISS/HNSW class). Deferred behind rules-first: FTS5 is unmeasured against real queries because there are ~0 real queries logged. Trigger: telemetry (§5) showing FTS5 miss-rate on actual retrieval attempts. Adopting vector search before measuring FTS5 is résumé-driven.

### 2.6 Local conversational front-door (P1) → **local small LLM** — NOT YET, with a defined runway

- **Class:** intent routing + short grounded Q&A on a consumer-hardware model (Ollama-class runtime). Honest quality bar: router + retriever-reader over the vault, never a CC replacement. Trigger: telemetry showing a volume of trivial queries whose CC cost is felt. Runway note: §2.4's local embedding model is the same infrastructure family — adopt embeddings first, chat model second.

### 2.7 Predictive control plane (P(stale), contradiction, rerank) → **already specified, stays deferred**

The RFP brief's control plane (TF-IDF/SetFit classifier, gradient-boosted P(stale), NLI contradiction, LTR rerank) remains the target architecture — all behind rules-first day-1 and all starved by the 0-rows fact. This brief adds nothing to it except its data supply (§5).

### 2.8 Explicit rejections (NOT-list, map-level)

- **Terraform / IaC** — no infrastructure-provisioning problem exists in a solo local-first estate. Named-technology ≠ problem.
- **OR-Tools solvers generally** — adopted only against a real constrained-optimization problem; none identified. Candidate future trigger: multi-deal calendar/utilization optimization, IF it ever hurts.
- **Graph databases / Palantir machinery** — T2's NOT-list, in force in advance.
- **Any learning component before its data exists** — the 0-rows rule beats all ambition.

## 3. Yield score v1 (making §2.1's "reward" concrete)

Per sampled/foraged location: `yield = w1·doc_density + w2·recency + w3·type_value (recordings/pptx/docx weights) + w4·dim_match (industry×software name/content match) − w5·dup_rate (§2.3)`. Equal weights day-1 (registry brief D5); recalibrated from realized usage once telemetry flows. Done when: two consecutive scout cycles rank locations and the operator's spot-check agrees with the top-3/bottom-3.

## 4. Terrain-learning pipeline — how the model learns "co jest w środku"

Three data paths, ordered by availability (no timeline; dependency order):

- **Path A — the 75 frozen inbox files.** Sample zero. Available now, zero new access. Run: CKE extract → MinHash dedup → BERTopic cluster → induced-topic report vs dims.
- **Path B — operator hand-pick.** A stratified sample per golden root (~20–30 docs each), hand-dropped to the inbox. This matches the operator's stated model: hand-picked paths initially, automation later. Unblocks the full pipeline without any auth work.
- **Path C — scout Monte Carlo, server-side.** Post-Graph-consent: the scout samples (never crawls) per §2.2 design. The automation end-state.

**Pipeline contract (all paths):** sample manifest → extraction → dedup stats → cluster report (topics, outliers, per-stratum yield estimates) → reconciliation table (induced topics × industry/software dims × existing tags). Output feeds: T1 metadata charter (evidence for the minimal field set), T2 ontology (fitted object/topic candidates), T4+ registry (yield priors).
**Done when:** one full pipeline run on Path A produces the reconciliation table and at least one induced topic the operator confirms as real-but-previously-unnamed (the "did we learn anything" test).

## 5. Telemetry spine — the one unconditional ADOPT-NOW

Logs are future training data; absence of logs is the reason every learning surface has 0 rows. Emit from day one, JSONL, append-only, one schema:
`{ts, event_type, subject_id, context{}, outcome{}}` for at minimum: retrieval queries + results + which result was used; scout cycle reports (predicted vs realized yield); CKE extraction scores; registry liveness transitions; RFP/deck content-reuse events. No consumers required yet — the spine exists so that §2.1's priors, §2.5's trigger, §2.6's trigger, and §2.7's models all have a table to read the day their trigger fires.
**Done when:** the event log exists, a schema validator passes on every emit path, and one week of ambient use produces ≥1 event of ≥3 types.

## 6. FR-addendum candidates

- **FR-13 (new): Telemetry spine** — §5 schema + emit points; the data prerequisite for the entire learning roadmap.
- **FR-14 (new): Terrain-learning pipeline** — §4 sample→extract→dedup→cluster→reconcile contract, three data paths.
- **Amendment to FR-11 (scout):** exploration queue is bandit-governed (Thompson sampling) from cycle 3+; yield score v1 per §3.
- **Amendment to FR-5-class ingest decisions (DR-5/DR-6):** MinHash dedup gate at ingest when W1 restarts.

## 7. Success criteria (brief-level)

The map holds if: Path-A pipeline run completes with a reconciliation table (§4 done-when) · telemetry spine emits per §5 done-when · scout queue upgrade path (round-robin → bandit) is specified with its trigger in FR-11 · every deferred component in §2 carries a measurable trigger, not a vibe. Closure on these, not on "libraries installed."

## 8. Sources (research pass, 2026-07)

- Orienteering / budgeted prize-collecting TSP: arXiv OP survey (2512.16865); MOR 2020 (Paul et al.); ScienceDirect k-TSP/orienteering.
- Bandits: MABWiser docs (fidelity.github.io/mabwiser) — policies incl. Thompson sampling, UCB1, contextual.
- MinHash LSH: datasketch (PyPI v2.0.0, ekzhu.com docs); RefinedWeb (arXiv 2306.01116) as the at-scale precedent.
- Topic induction: BERTopic (maartengr.github.io/BERTopic; PyPI) — sentence-transformers → UMAP → HDBSCAN → c-TF-IDF, outlier-aware clustering.
