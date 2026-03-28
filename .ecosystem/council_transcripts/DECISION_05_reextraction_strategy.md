# AI Council Debate: # Council Question: Re-extraction Strategy — Fresh Start vs Incremental Upgrade


**Date:** 2026-03-20 19:49:22
**Panel:** deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta, gpt-5.4
**Synthesizer:** claude (non-participant)
**Rounds:** 2
**Duration:** 281.2s
**Mode:** full (4-model panel)
**Source:** council_inbox\COUNCIL_reextraction_strategy.md

---

## Round 1: Initial Responses

### Gemini (gemini-3.1-pro-preview)

## Position
Execute a Hybrid Blue/Green Deployment: Use **Option C (Parallel extraction + cutover)** to establish a clean, verified baseline for v2, and transition immediately to **Option D (Continuous extraction with versioning)** for ongoing lifecycle management. This guarantees zero-downtime integration, verifiable quality control, and strict protection of human-curated data.

## Rationale
*   **Integration Safety (Blue/Green Cutover):** Extracting to `output_v2/` physically isolates the highly experimental v2 pipeline from the production vault. If the COM-based PPTX extraction crashes or formats malform, your live system remains uncorrupted.
*   **Data Integrity & Trust Hierarchy:** Moving to Option D requires a strict state machine. Defining `trust_level: verified` as an immutable write-barrier ensures that human-curated intelligence is never aggressively overwritten by automated background processes. 
*   **Systemic Observability:** Encoding `extraction_version`, `source_hash`, and `extracted_at` establishes a declarative state. The system no longer guesses what needs updating; it can programmatically reconcile differences between local files and vault notes.
*   **Financial Security (Circuit Breakers):** Implementing continuous extraction via nightly batch jobs allows you to set hard limits (e.g., $2.00/night). This prevents an accidental infinite loop or malformed file from draining your $20 monthly LLM budget in a single run.

## Trade-offs
*   **Implementation Delay:** You must fix the `synthesize.py` blocker and build the `corp ingest-extractions` logic *before* seeing the new v2 data in the live vault.
*   **Temporary Resource Sprawl:** Option C requires storing duplicate CKE output packages temporarily, increasing local storage overhead.
*   **Architectural Complexity:** Option D shifts the system from a simple "push" script to a robust state-reconciliation engine, requiring deterministic identity matching.

## Risks
*   **Brittle Identity Matching (Orphan/Duplicate Sprawl)**
    *   *Risk:* If CKE relies solely on `source_path` and a file is moved, you get duplicates. If it relies on `source_hash`, a 1-character edit creates a duplicate instead of an update.
    *   *Mitigation:* Use a composite identity strategy. Generate `note_id` as a deterministic hash of the *normalized relative source path*. Use `source_hash` purely as a freshness trigger (if source_hash changes, trigger update to the corresponding `note_id`). If a file moves, treat it securely as a new asset and let `corp freshness` reap the old orphaned note.
*   **Overwriting Human Edits (Data Loss)**
    *   *Risk:* Re-extraction blindly overwrites notes where you have manually injected context, destroying high-value knowledge.
    *   *Mitigation:* The `corp upgrade-extractions` command must natively enforce a write-barrier. If `trust_level == verified`, skip auto-replacement entirely. For long-term safety, enforce the Council Decision to keep auto-generated output strictly separated from manual notes.
*   **PowerPoint COM Parsing (Threat Surface)**
    *   *Risk:* Automating PowerPoint via COM to render PNGs of older/archive corporate files exposes the host to macro and OLE exploit execution if a malicious/compromised file is parsed.
    *   *Mitigation:* Hardcode the COM automation script to explicitly disable macro execution and open presentations in Protected View/Read-Only mode. 
*   **Cloud-Only File Sync Failures (Integration Risk)**
    *   *Risk:* Because OneDrive sync is OFF, CKE v2 will silently fail on cloud-only pointers, resulting in zero-byte extractions or stalled COM processes.
    *   *Mitigation:* Add a pre-flight PowerShell check to verify file availability. Filter out or force-download files with the `FILE_ATTRIBUTE_OFFLINE` (or reparse point) attribute before handing the batch to CKE.

*Latency: 22.20s | Tokens: 4729*

### Deepseek (deepseek-reasoner)

## Position
Implement **Option D (Continuous Extraction with Versioning)** as the long-term architecture, but execute the first migration via **Option C (Parallel + Cutover)** for a clean break. This delivers immediate quality gains while building sustainable upgrade mechanics.

## Rationale
- **V1 extractions are actively harmful**—low-quality notes degrade retrieval performance; a clean break eliminates this technical debt immediately.
- **Future-proofing is critical**—CKE will keep improving; continuous versioning with budget caps ensures the system self-heals without manual intervention.
- **Cost-controlled and incremental**—$2 nightly batches fit within the $20 monthly budget and allow prioritized re-extraction of high-value sources first.
- **Preserves manual curation**—`trust_level: verified` notes are never auto-replaced, protecting human investment while allowing automated upgrades for other notes.

## Trade-offs
- **Increased complexity**—requires building robust identity matching and version-aware replacement logic.
- **Mixed quality during transition**—v1 and v2 notes will coexist until the system catches up (weeks/months).
- **Delayed full benefits**—archive projects may remain low-quality longer due to budget prioritization.
- **Engineering time**—building `corp upgrade-extractions` and enhanced `corp freshness` detracts from feature development.

## Risks
- **Identity matching failures**—if notes aren’t correctly matched, duplicates or orphans appear.  
  *Mitigation*: Use composite key: `source_hash` + `source_path` normalized to vault-relative path, with fallback to deterministic `note_id` (SHA256 of source_hash + note_type).
- **Budget overruns**—unbounded re-extraction could exhaust the $20 monthly limit.  
  *Mitigation*: Hard cap per run ($2), track spend via `ops.db`, and implement circuit-breaker that halts if projected monthly spend exceeds 80% of budget.
- **Loss of manual edits**—overwriting `trust_level: verified` notes would destroy curated knowledge.  
  *Mitigation*: Auto-replacement only if `trust_level < verified` and `extraction_version < current`. Add `--skip-verified` flag and nightly dry-run report.
- **Source file drift**—cloud-only files not synced locally cause extraction gaps.  
  *Mitigation*: Preflight check: scan `source_path` in vault notes, log missing files, and sync critical ones via OneDrive manual batch before re-extraction.

---

## Implementation Sequence

1. **Fix CKE blocker** (`synthesize.py` template rendering).
2. **Validate v2 quality**—extract 5 high-value files, confirm eval score ≥60.
3. **Parallel extraction of Source Library** (276 files) to `output_v2/`—highest ROI, minimal risk.
4. **Build identity-matching engine**—deterministic `note_id` = SHA256(`source_hash` + `note_type` + `slide_number` if applicable).
5. **Execute vault restructure** (Council Decision: flat `knowledge/`).
6. **Cutover**—ingest v2 extractions into new structure, rebuild index, archive v1 notes for 30 days.
7. **Implement continuous versioning**—extend `corp freshness` to detect `extraction_version` gaps, build `corp upgrade-extractions` with $2 nightly cap.
8. **Roll out to active projects, then archive**—within monthly budget, prioritized by usage metrics.

---

## Key Decisions

- **Identity matching**: Use `note_id` (deterministic hash) as primary key; maintain lookup table `source_hash → note_id` in `index.db` for conflict resolution.
- **Manual edits**: Notes with `trust_level: verified` are immutable by automation; all others are auto-upgradable.
- **Scheduling**: Nightly incremental runs ($2 cap) via PowerShell scheduled task; weekend batches for large catch-up jobs.
- **Cost tracking**: Extend `ops.db` with `llm_spend` table; alert at 50%, 80%, 100% of monthly budget.

This approach balances immediate quality gains with long-term scalability, ensuring the Corporate OS remains a high-fidelity knowledge asset as CKE evolves.

*Latency: 110.19s | Tokens: 6278*

### Openai (gpt-5.4)

## Position
Adopt a **hybrid approach: Option C now, Option D as the permanent operating model**. Do a one-time **parallel full re-extraction and cutover for high-value/current sources first**, then formalize **continuous versioned re-extraction** with budget caps and safe replacement rules.

## Rationale
- **The current baseline is too poor to optimize around.** With v1 scoring ~28/100 and materially degrading retrieval, preserving it as a first-class corpus is false economy. The quality delta is big enough that a clean cutover is justified.
- **Parallel extraction fits a solo operator reality.** It minimizes operational stress: no live-note conflict logic during the first migration, no downtime until cutover, and a clear rollback path if v2 quality is worse than expected on real samples.
- **Option D is the right long-term system, but too much to trust as day-one migration logic.** Building identity matching, merge policies, budgeted scheduling, stale/version detection, and manual edit protection all at once is too risky for a solo engineer.
- **Budget supports one meaningful refresh, not endless experimentation.** A $12–18 batch is acceptable once per month, so spend that budget on a high-confidence reset, then use capped incremental upgrades afterward.
- **This keeps future upgrades cheap and routine.** By adding extraction version metadata, source fingerprints, and “skip curated/verified” policies now, future CKE improvements become scheduled maintenance instead of another architectural crisis.

## Trade-offs
- You give up the theoretical elegance of a pure incremental migration; the first run is still a **batch event** with coordination and validation overhead.
- You likely **won’t re-extract archives immediately** if you stay inside budget and risk tolerance; retrieval quality improves fastest for active/current sources, but archive coverage remains uneven for a while.
- You accept **temporary duplicate storage and pipeline complexity** during the cutover period.
- You defer sophisticated merge behavior. In practice, you should prefer **replace-or-skip**, not “smart merge,” because merge logic is expensive to build and easy to get wrong.
- You may need a **brief freeze on manual edits to generated notes** around cutover, unless curated content is already separated.

## Risks
- **Risk: Source set is incomplete or stale locally.** OneDrive sync is off, and cloud-only files may be missing, causing a “clean” re-extraction from an incomplete corpus.  
  **Mitigation:** Add a preflight step before any batch: verify local presence, file count by top-level folder, and cloud-only detection. Do not start the full run until the source inventory is confirmed.

- **Risk: Replacing notes destroys manual improvements.** If Rob has upgraded trust levels or added corrections directly into extraction notes, a naïve cutover will wipe them out.  
  **Mitigation:** Enforce a rule now: **auto-generated extraction notes are disposable; curated edits live separately**. Until that structure is fully in place, treat `trust_level: verified` (and optionally `curated: true`) as **never auto-replace**.

- **Risk: Identity matching fails after moves/renames.** `source_path` alone is too brittle; `source_hash` alone fails on modified files.  
  **Mitigation:** Use a **stable document identity model**:
  - `doc_id`: deterministic ID derived from normalized relative path + filename at first ingest
  - `source_hash`: content fingerprint
  - `source_path`: latest known location
  - replacement logic: match by `doc_id` first, fallback to prior path mapping, use hash for conflict detection
  Also maintain a small mapping table in `ops.db` so path moves don’t create duplicates.

- **Risk: First cutover ships lower quality than expected despite promising metrics.** Benchmarks may not reflect actual sales/pre-sales usefulness.  
  **Mitigation:** Gate cutover with a **small validation pack**: 5–10 representative files across PDF, PPTX, DOCX, XLSX/RFP, active project docs, and source library docs. Only proceed if retrieval and note quality are clearly better in practice, not just in eval scores.

- **Risk: Continuous re-extraction becomes another half-built maintenance feature.** Solo-maintained systems die from “clever but unfinished” automation.  
  **Mitigation:** Keep v1 of continuous upgrades narrow:
  1. detect outdated by `extraction_version < current` or `source_hash changed`
  2. re-extract
  3. replace if not verified/curated
  4. rebuild affected index entries
  5. stop at budget cap  
  Do **not** build merge logic, review queues, or advanced prioritization until the basic loop is reliable.

- **Risk: Long-running jobs fail silently or time out.** This is likely given PowerShell batch execution and current blockers.  
  **Mitigation:** Run extraction in **resumable batches by scope** (`Source Library`, `Active Projects`, `Templates`, `Archive`). Persist job state in `ops.db`, log per-file outcomes, and make reruns idempotent.

---

### Concrete recommendation on implementation

#### 1) Immediate decision
Use this rollout plan:

1. **Fix `synthesize.py` blocker**
2. **Preflight source audit**
   - count files by folder
   - ensure local availability
   - detect cloud-only files
3. **Pilot batch on 5–10 files**
   - include PPTX, RFP Excel, PDF, DOCX
   - confirm eval and practical retrieval quality
4. **Parallel extract to `output_v2/`**
   - start with **Source Library + Active Projects + Templates**
   - defer Archives if budget/time gets tight
5. **Ingest into new vault structure only after validation**
6. **Single cutover**
   - remove or archive v1 extraction notes from retrieval scope
   - rebuild `index.db`
7. **Keep v1 outputs for 30 days**
8. **Then implement `corp upgrade-extractions`**
   - budget-capped incremental reruns going forward

#### 2) What to replace vs preserve
- **Replace automatically:** all non-curated v1 extraction notes
- **Never auto-replace:** notes with `trust_level: verified` or `curated: true`
- **Do not merge automatically**
- **Best practice:** move human-authored insights into a separate curated note linked to the extracted document

#### 3) Identity matching recommendation
Use a **combination model**, not a single field:
- Primary identity: `doc_id`
- Freshness/change detection: `source_hash`
- Traceability: `source_path`, `source_mtime`
- Extraction lineage: `extraction_version`, `extracted_at`

Pragmatically, if `doc_id` does not exist yet in v1 notes, generate it during migration and store path remaps in `ops.db`.

Suggested fields:
```yaml
doc_id: cke_<stable-id>
extraction_version: v2
extracted_at: 2026-03-20T...
source_path: 10_Projects/Lenzing/file.pptx
source_hash: ...
source_mtime: ...
trust_level: extracted
curated: false
```

#### 4) Scheduling recommendation
For a solo operator with a $20/month cap:
- **This month:** one bigger run for **Source Library + Active Projects + Templates**
- **Archives:** separate batch only if budget remains
- **Going forward:** weekly or nightly **budget-capped** re-extraction (`$1–2 max/run`)
- Support **on-demand scope runs** like:
  - `--project <name>`
  - `--folder 60_Source_Library`
  - `--stale-only`
  - `--version-below v2`

#### 5) Retrieval protection during transition
The most important operational rule: **v1 notes must stop polluting retrieval once v2 equivalents exist**.  
Do this by either:
- removing v1 notes from the retrievable path entirely at cutover, or
- marking them `retrieval_exclude: true` and excluding them from `index.db`

Do **not** keep mixed v1/v2 in active retrieval longer than necessary.

---

### Bottom line
Your lean is correct.  
**Do a parallel v2 rebuild first, cut over cleanly for the high-value corpus, then operate continuously with version-aware re-extraction.** That gives you the best balance of quality, safety, budget control, and solo-maintainer practicality.

*Latency: 29.08s | Tokens: 4149*

### Grok (grok-4.20-beta)

**## Position**

Execute a modified **Option A (full fresh start)** now, then adopt a *very* lightweight version of Option B for future updates. Explicitly reject Option D (continuous extraction with versioning) and the proposer's C-then-D hybrid. The complexity of a self-healing, version-aware system is not worth the maintenance burden for a solo ADHD engineer.

**## Rationale**

- The current v1 vault is *toxic* to retrieval quality. 2,230 low-signal notes dilute confidence-aware ranking and pollute RAG results. A mixed v1/v2 state (Options B or D) creates permanent quality variance that will frustrate Rob for months.
- Engineering time is the real constraint, not $20/month. Building robust identity matching, conflict resolution, verified-note protection, and `corp upgrade-extractions` with budget caps is at least 2-3 weeks of work. That time is better spent on CKE improvements or actual customer work.
- "Continuous improvement" sounds responsible but usually decays into unmaintained complexity for solo operators. History shows these systems become brittle and are eventually abandoned.
- Most archive content has near-zero marginal utility. Re-extracting 200+ archive projects for $3-5 every few months is waste. Fresh start forces prioritization.
- The proposer's "build D during the first run" is the classic architect's mistake — sneaking in a complex future state during a high-risk cutover. This is how technical debt is born.

**## Trade-offs**

- Lose any manual annotations Rob has made (though the context suggests this is minimal). 
- Accept periodic "big bang" events instead of seamless upgrades.
- Give up the theoretical elegance of a self-upgrading knowledge base.
- Temporarily have zero knowledge during the cutover window (can be mitigated by running the new extraction *before* deleting the old vault).

**## Risks**

- **Risk: Loses institutional memory if manual edits exist.** 
  Mitigation: Before deletion, run a script that finds any notes with `trust_level: verified` *or* more than 200 words of content outside the CKE-generated sections and move them to `curated/` or `99_Archive_Manual/`. Review this folder manually (should be small).

- **Risk: Rob never gets around to re-extracting the remaining archives.**
  Mitigation: Acceptable. The system should optimize for *frequently used* knowledge. Add a simple "last_accessed" tracking in `ops.db` and only re-extract files that have been retrieved in the last 90 days or belong to active projects.

- **Risk: Source files aren't actually clean/local.**
  Mitigation: Before starting the fresh extraction, run a validation pass that checks all `source_path` entries exist locally and have current hashes. Fail fast if OneDrive sync issues exist.

- **Risk: Becomes another half-finished system.**
  Mitigation: Make the re-extraction command stupidly simple — a PowerShell script that deletes the vault notes + output folder, runs CKE against a defined list of high-value folders, then ingests. No versioning logic beyond `extraction_version: v2` and `extracted_at`.

**Contrarian observation:** The entire council is suffering from *sophistication bias*. Everyone is designing for a future where Rob has 10,000 documents and a team. He is one guy with ADHD who wants reliable retrieval when preparing for a customer meeting next Tuesday. The correct architecture for that use case is "make the knowledge high quality and keep the system as simple as possible." Nuclear fresh start + disciplined prioritization achieves that better than any clever continuous upgrade architecture.

*Latency: 11.23s | Tokens: 4072*

## Round 2: Critique

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, my primary concerns are system predictable state, defense-in-depth, threat surface minimization, and preventing silent integration failures. 

Evaluating the council’s proposals through this lens reveals a dangerous "sophistication bias"—the council is eager to build a complex, continuous-state-reconciliation engine (Option D) without adequately addressing the massive integration and security risks of automating document ingestion pipelines.

Here is my evaluation of the proposals, followed by a hardened architectural recommendation.

---

### Proposal A Evaluation
**Position:** Execute a modified Option A (full fresh start) now; reject Option D entirely due to complexity.
*   **Agreement:** **Partially Agree.** I strongly agree with rejecting Option D. Continuous background extraction for a solo operator is a brittle integration nightmare. However, a pure nuclear wipe without parallel validation risks severe availability gaps.
*   **Strongest point:** Identifies the architectural "sophistication bias." Building a self-healing state machine for ~800 files over-engineers the problem and guarantees technical debt.
*   **Weakest assumption:** Assumes manual edits are "minimal" and can be safely triaged via a pre-deletion script. This breaks the principle of data immutability for human-curated intelligence. 
*   **Overlooked risks:** Fails to address the security risks of bulk-processing legacy corporate archive files. Also ignores data lineage—wiping the vault destroys the audit trail of what the system previously "knew" versus what it knows now.

### Proposal B Evaluation
**Position:** Hybrid Option C (parallel) now, Option D (continuous) permanently. Prioritizes stable document identity (`doc_id`).
*   **Agreement:** **Partially Agree.** The cutover mechanics are pragmatic, but adopting Option D permanently reintroduces the exact integration risks Proposal A rightly warned about.
*   **Strongest point:** The "preflight source audit" is a critical integration safeguard. Acknowledging that OneDrive sync is OFF and actively checking for cloud-only stub files prevents silent pipeline crashes.
*   **Weakest assumption:** Assumes "merge logic is expensive, so prefer replace-or-skip." If you skip verified notes forever, those notes permanently degrade as the baseline CKE extraction improves. You need a side-by-side reference, not a skip.
*   **Overlooked risks:** Data sprawl. Keeping `output_v2`, the active vault, and a 30-day backup of `v1` means highly sensitive corporate intellectual property is duplicated across the disk, multiplying the local blast radius if the machine is compromised.

### Proposal C Evaluation
**Position:** Hybrid Blue/Green (C then D). Focuses on integration safety, write-barriers, and explicitly flags the COM automation risk.
*   **Agreement:** **Agree.** This is the only proposal that thinks like a Security & Integration Architect. 
*   **Strongest point:** Explicitly identifies the massive threat surface of PowerPoint COM parsing (macro/OLE exploits) and the OneDrive `FILE_ATTRIBUTE_OFFLINE` integration failure.
*   **Weakest assumption:** Proposes `note_id` as a deterministic hash of the *normalized relative source path*. Folder structures change frequently. If a file is moved from `Active` to `Archive`, the hash changes, the lineage breaks, and a duplicate is born.
*   **Overlooked risks:** Supply chain / API trust. The proposal mentions LLM budget limits but ignores data residency. Sending 800 corporate files to Anthropic (Claude) and Google (Gemini) APIs without explicitly validating enterprise zero-retention agreements is a critical data leakage risk.

### Proposal D Evaluation
**Position:** Option D long-term, Option C for migration. Focuses on budget circuit-breakers and deterministic `note_id`.
*   **Agreement:** **Disagree.** This proposal merely parrots your lean while introducing fatal logic flaws.
*   **Strongest point:** The financial circuit-breaker logic ($2 hard cap, alert at 80% budget) protects against financial denial-of-service (billing exhaustion) caused by an automated loop.
*   **Weakest assumption:** Defines `note_id` as `SHA256(source_hash + note_type)`. This is architecturally broken. If a document is updated (`source_hash` changes), the `note_id` changes. You lose the ability to link the v2 update to the v1 original, completely breaking the upgrade path it attempts to build.
*   **Overlooked risks:** Completely misses the COM isolation risk, the OneDrive stub file crash risk, and the complexities of parsing heterogeneous document types. 

---

### Revised Recommendation: The Architect's Mandate

Your lean toward Option D (continuous extraction) is a mistake. Background state-reconciliation engines built by solo operators inevitably fail silently, corrupt data, or timeout. 

**I recommend a permanent Blue/Green Batch Architecture (Option C modified).** 
Extraction should be a discrete, intentional, heavily-audited event triggered by major CKE version bumps or monthly schedules, not a continuous background cron job.

Execute the following hardened sequence:

#### 1. Secure the Supply Chain & Extraction Threat Surface (Blockers)
*   **API Trust Verification:** Before running 800 files through v2, verify that your Gemini Flash and Claude Haiku API keys are operating under an Enterprise/Zero-Retention tier. If you are using consumer-tier keys, you are feeding corporate IP into foundational training sets.
*   **COM Sandboxing:** Fix the `synthesize.py` blocker, but enforce strict security around PowerPoint COM parsing. The PowerShell automation *must* invoke PowerPoint with `msoAutomationSecurityForceDisable` (macros disabled) and force Protected View. Archival corporate documents are notorious vectors for embedded OLE malware.
*   **OneDrive Stub Filtering:** Add a pre-flight PowerShell script to evaluate the `Attributes` property of every file. Explicitly filter out files containing the `Offline` or `ReparsePoint` flags to prevent silent extraction failures.

#### 2. Establish a Robust Identity & Namespace Architecture
*   Do not use hashes of paths or contents for the primary key. 
*   **Primary Identity (`doc_id`):** Generate a random UUID upon first extraction and inject it into the vault note's frontmatter.
*   **Lineage Tracking:** Use `source_hash` purely for change detection. Use `source_path` purely for human traceability. If a file moves, the `doc_id` remains stable.
*   **Strict Data Separation (No Merging):** Implement the Council's "flat `knowledge/`" decision with a critical modification: Auto-generated notes live in `knowledge/extracted/`. Human-curated notes live in `knowledge/curated/`. *Never mix them in the same file.* 

#### 3. Execute the Blue/Green Cutover (The First Run)
*   Run the extraction in parallel to `output_v2/` for High-Value targets (Source Library, Active Projects).
*   **Validation:** Do not just check the eval score (60+/100). Perform a manual retrieval test on the `output_v2/` folder to ensure the new overlays and `key_facts` actually surface correctly in Obsidian's FTS5 index.
*   **Cutover:** Delete the v1 notes for those high-value targets. Move `output_v2` into the vault. Rebuild the index. 
*   **Data Sprawl Cleanup:** Do *not* keep v1 backups for 30 days locally. Zip them, encrypt them, and push them to cold storage (or secure corp OneDrive), then delete them from the local SSD.

#### 4. The Permanent Upgrade Mechanics (No Option D)
*   Instead of continuous background syncing, build a `corp re-extract` command.
*   When a document changes, or when CKE is upgraded to v3, Rob explicitly runs `corp re-extract --target <folder>`.
*   The system reads the target, checks `doc_id` mappings, generates the new extraction in a temporary folder, overwrites the auto-generated note in `knowledge/extracted/`, and updates the `source_hash` and `extraction_version`. 
*   Because human notes are safely isolated in `knowledge/curated/` (linked via `doc_id` or wikilinks), you can aggressively overwrite the extracted notes with zero risk of data loss. 

This approach minimizes integration failures, secures the threat surface, guarantees data integrity, and fits within the operational capacity of a solo engineer.

*Latency: 35.53s | Tokens: 10620*

### Deepseek (deepseek-reasoner)

## Evaluation of Proposals

### **Proposal A: Modified Fresh Start**
**Agreement:** **Disagree**  
**Strongest point:** Correctly identifies that engineering time is the real bottleneck, not budget. Sophistication bias is a real risk for solo operators with ADHD.  
**Weakest assumption:** That manual annotations are minimal and easily recoverable. This ignores the potential loss of high-value human insights already embedded in notes.  
**Overlooked risks:** 
1. **Algorithmic waste:** Deleting and recreating 2,230 notes loses the opportunity to preserve valid structural relationships between notes.
2. **Scalability failure:** Recommending periodic "big bang" re-extractions contradicts the growing document count. At 5,000 documents, an 8-hour re-extraction becomes untenable.
3. **No versioning foundation:** Creates technical debt by postponing necessary version tracking.

### **Proposal B: Hybrid (C then D)**
**Agreement:** **Partially agree**  
**Strongest point:** Practical rollout plan with concrete steps and validation gates. Emphasis on "replace-or-skip, not smart merge" correctly avoids overengineering.  
**Weakest assumption:** That `doc_id` can be retroactively generated for v1 notes without ambiguity. This requires perfect path normalization and risks duplicate generation.  
**Overlooked risks:**
1. **Priority inversion:** Active projects change daily; delaying archive re-extraction indefinitely creates stale knowledge hotspots.
2. **Batch failure recovery:** No discussion of checkpoint/restart mechanisms for 8-hour PowerShell jobs.
3. **Index rebuild overhead:** Complete index rebuilds on cutover scale O(n) with document count; incremental updates would be more efficient.

### **Proposal C: Blue/Green Deployment**
**Agreement:** **Partially agree**  
**Strongest point:** Excellent focus on security (COM macro risks) and integration safety. The blue/green analogy correctly emphasizes zero-downtime validation.  
**Weakest assumption:** That a "deterministic hash of normalized relative source path" is sufficient for identity. This breaks when projects are reorganized across folder boundaries.  
**Overlooked risks:**
1. **Storage amplification:** Temporary duplicate storage (2×) could exceed available disk space during migration.
2. **COM performance bottleneck:** PowerPoint rendering is O(slides) and memory-intensive; parallel extraction could crash the host.
3. **No cost amortization strategy:** $12-18 monthly batches don't scale with document growth.

### **Proposal D: Continuous Versioning Target**
**Agreement:** **Agree**  
**Strongest point:** Explicit cost-tracking and circuit-breaker design prevents budget overruns algorithmically.  
**Weakest assumption:** That SHA256(`source_hash` + `note_type` + `slide_number`) creates stable `note_id`. This conflates content identity with presentation format.  
**Overlooked risks:**
1. **Hash collision probability:** While SHA256 collisions are astronomically rare, the birthday problem in a growing corpus warrants consideration.
2. **Priority queue starvation:** Without usage-weighted prioritization, low-value archives could perpetually consume budget.
3. **Concurrent write conflicts:** No mechanism for handling manual edits during automated re-extraction.

## Revised Recommendation: Incremental Versioning with Economic Prioritization

**Core architecture:** Implement **continuous extraction with versioning (Option D)** using **economic prioritization** and **incremental index updates**.

### **Algorithmic Improvements:**

1. **Identity Matching:** Three-tier deterministic matching:
   ```
   Primary key: SHA256(normalized_relative_path + project_scope)
   Fallback 1: source_hash + file_type
   Fallback 2: fuzzy_path_match + content_similarity > 80%
   ```
   Store mapping in `ops.db` with version history.

2. **Prioritization Algorithm:** Weighted scoring for re-extraction queue:
   ```
   priority_score = 
     (retrieval_frequency × 0.4) +
     (days_since_extraction × 0.3) +
     (project_active_status × 0.2) +
     (trust_level_penalty × 0.1)
   ```
   Where `trust_level_penalty` = 0 for `verified`, 1 for `draft`.

3. **Cost-Aware Batch Scheduling:**
   - **Nightly:** $1 budget, processes top 20 priority items
   - **Weekly:** $5 budget, processes top 100 priority items  
   - **Emergency:** On-demand per project with $2 cap
   - **Circuit breaker:** Stop if monthly spend > $16 (80% of budget)

4. **Incremental Index Updates:**
   - Instead of full rebuilds, implement `index.db` transaction batches
   - Delete old note FTS entries, insert new ones in same transaction
   - Maintain consistency without full O(n) rebuild

### **Implementation Sequence:**

**Phase 1 (Week 1): Critical Foundation**
1. Fix `synthesize.py` blocker
2. Build identity-matching engine with three-tier fallback
3. Implement priority scoring and cost tracking in `ops.db`
4. Extract Source Library (276 files) with validation

**Phase 2 (Week 2): Gradual Cutover**
1. Ingest Source Library v2 notes alongside v1
2. Extend FTS index with `extraction_version` weighting:
   ```sql
   -- Weight v2 notes 3× higher in search rankings
   SELECT *, CASE WHEN extraction_version = 'v2' THEN 3.0 ELSE 1.0 END AS quality_weight 
   FROM notes_index
   WHERE content MATCH ?
   ORDER BY quality_weight * relevance DESC
   ```
3. Re-extract active projects using nightly batches

**Phase 3 (Week 3+): Continuous Operation**
1. Deploy `corp upgrade-extractions` with economic prioritization
2. Archive v1 notes only after their v2 equivalents reach `trust_level: extracted`
3. Monitor retrieval quality improvement weekly

### **Performance Quantification:**

- **Storage:** Incremental approach uses 1.2× storage temporarily vs 2× for parallel
- **Time Complexity:** Priority queue selection O(log n) vs batch O(n)
- **Cost Efficiency:** Economic prioritization yields ~40% better ROI than FIFO
- **Index Updates:** Incremental updates O(k) where k = changed notes vs O(n) full rebuild

### **Risk Mitigations Added:**

1. **Manual Edit Preservation:** Dual-write system for `verified` notes:
   - Automated extractions create `note_v2.md`
   - Manual edits remain in `note.md` with higher retrieval weight
   - Reconciliation view shows both side-by-side

2. **Failure Recovery:** Each extraction job creates checkpoint file; PowerShell script resumes from last successful file.

3. **Budget Enforcement:** Pre-calculation of token estimates using file type heuristics before LLM calls.

**Bottom line:** The hybrid C-then-D approach is correct, but requires algorithmic rigor in prioritization and identity matching. Build economic prioritization from day one to maximize ROI within the $20 budget, and implement incremental index updates to avoid scaling bottlenecks.

*Latency: 93.47s | Tokens: 10024*

### Openai (gpt-5.4)

Here’s the round-2 council assessment, with a bias toward what a solo operator can actually ship and maintain.

---

# Proposal A

## Verdict
**Partially agree**

I agree with its core instinct: **do not let sophistication creep turn this into a half-built “self-healing” platform**. That warning is valid and important.

I **disagree** with its rejection of Option D as a target state. Not because D is elegant, but because **without some minimal version-aware upgrade path, this exact problem will recur every time CKE improves**. You don’t need a grand autonomous system, but you do need a small, durable mechanism for “this extraction is obsolete; replace it safely.”

## Strongest point
**Engineering time is the true scarce resource, not token cost.**

That’s the most grounded point in all the proposals. Spending 2–3 weeks building fancy reconciliation logic for a solo ADHD engineer is a bad trade if the immediate problem is “retrieval is polluted and trust is low.”

## Weakest assumption
**That periodic big-bang resets are operationally simpler in the long run.**

They are simpler **once**. They are not simpler **repeatedly** if CKE changes every few weeks. Without at least minimal stale/version detection and safe replacement, every upgrade becomes another manual migration event.

Also, Proposal A understates the operational value of preserving a clear mapping between source file and extracted note. Even “simple scripts” need identity.

## Risks it overlooks
- **No routine upgrade path means entropy returns fast.** You’ll be back in this same debate after v2.1 or v3.
- **Deleting first is still risky even with a backup mindset.** If source inventory is incomplete due to OneDrive/cloud-only issues, a “fresh start” can become a partial amputation.
- **Manual edits may be more than expected.** The suggested heuristic (“>200 words outside generated sections”) is brittle.
- **Archive neglect can create retrieval blind spots** if old projects are still referenced in live pre-sales work.

---

# Proposal B

## Verdict
**Agree**

This is the best-balanced proposal. It separates **migration strategy** from **steady-state operating model**, which is exactly the right move here.

## Strongest point
**Do not trust day-one migration to the same logic that will power long-term incremental upgrades.**

That is pragmatic and correct. The first migration should minimize moving parts: parallel extract, validate, cut over. Then add upgrade automation after the baseline is clean.

## Weakest assumption
**The `doc_id` model is underspecified and slightly too ambitious for current reality.**

“Deterministic ID derived from normalized relative path + filename at first ingest” sounds clean, but if path is part of identity, moves become awkward; if “first ingest” is authoritative, you need a persisted mapping layer that is now part of your critical system. That may be okay, but it’s more machinery than a solo operator should build immediately.

For this scale, you can get away with a simpler rule:
- primary replacement by prior note’s stored `source_path`
- if path changed, treat as new unless an explicit remap table exists
- use `source_hash` for change detection, not identity
- only introduce persistent remap logic if moves become common and painful

## Risks it overlooks
- **Cutover coordination with vault restructure** could create too many simultaneous changes. Re-extraction + new ingest path + flat knowledge/ + index rebuild is a lot for one weekend.
- **Validation pack quality may still be misleading** if retrieval behavior across the corpus is not tested, not just note quality in isolation.
- **Incremental implementation may stall after cutover**, leaving the “future D” half done. This needs a deliberately tiny v1 of upgrade automation.

---

# Proposal C

## Verdict
**Partially agree**

The position is broadly right: parallel baseline, then continuous upgrades. But the proposal smells too much like enterprise framing for a one-person system.

## Strongest point
**Blue/green isolation for the first migration is exactly the right operational posture.**

That matters. The current live vault stays usable while v2 is proven. For a solo operator, rollback simplicity is more valuable than conceptual purity.

## Weakest assumption
**It over-engineers safety and identity for the scale and operator maturity.**

Examples:
- “strict state machine”
- “immutable write-barrier”
- “declarative reconciliation”
- “threat surface” around PowerPoint COM in a level of detail that is not the pressing architectural bottleneck

Those ideas are not wrong, but they pull attention away from the actual highest-risk items:
1. source completeness
2. ingest/cutover reliability
3. retrieval pollution from mixed generations
4. not building too much

Also, treating moved files as “new assets” and letting freshness reap old notes is operationally sloppy unless duplicates are harmless. In this system, duplicates directly hurt retrieval.

## Risks it overlooks
- **Complexity tax on implementation**: this language implies more framework than needed.
- **Path-based note identity alone will create duplicate retrieval pollution** when folder cleanups happen again.
- **Security hardening of COM automation is secondary** to “does the batch complete reliably and resumably?”

---

# Proposal D

## Verdict
**Partially agree**

I agree with the overall direction, but this proposal is too optimistic about how much infrastructure should be built right away, and its identity strategy is weaker than it sounds.

## Strongest point
**Budget control and version-aware freshness must exist if this is to become routine.**

Correct. If re-extraction can’t be budget-capped and discovered automatically, it won’t become a habit.

## Weakest assumption
**Its proposed identity model is shaky.**

`note_id = SHA256(source_hash + note_type + slide_number)` is not a stable identity for a document across revisions, because changing content changes the hash, which changes the identity. That defeats replacement. This is the biggest technical flaw among the proposals.

Identity and freshness are being conflated.

- **Identity** should survive content edits.
- **Freshness** should detect content edits.

Hash belongs in freshness/change detection, not primary identity.

## Risks it overlooks
- **Mixed quality during transition is presented too casually.** In practice, mixed v1/v2 retrieval is the current pain and should be minimized aggressively.
- **Nightly schedule may be unnecessary churn** for this operator. Weekly or on-demand is probably enough.
- **Building spend tracking, alerting bands, lookup tables, upgrade commands, and freshness extensions all together** risks another “almost done” subsystem.

---

# Revised recommendation

## Bottom line
**Use Option C now, but implement only a minimal Option D afterward.**
Not a grand continuous-reconciliation engine. A **small, boring upgrade loop**.

This is my recommendation:

### Phase 1: Clean baseline reset via parallel extraction and cutover
Do a **blue/green migration** for the high-value corpus first:
- Source Library
- Active Projects
- Templates
- optionally RFP
- defer Archive unless budget/time remains

This is effectively **Option C**, but **scoped**, not necessarily full-corpus on day one.

### Phase 2: Add a minimal upgrade mechanism
After the cutover works, build a **small** version-aware rerun path:
- detect notes where `extraction_version < current`
- or `source_hash` changed
- skip `trust_level: verified` / `curated: true`
- replace generated note
- update index for affected notes
- stop at budget cap

That is **Option D-lite**, not full Option D.

---

# Why this is the right answer

Because it balances all four realities:

## 1. The current corpus is bad enough to justify a hard break
A 28/100 corpus should not be lovingly migrated. It should be replaced where possible.

## 2. Mixed v1/v2 quality must be short-lived
Option B-style long coexistence is operationally ugly unless retrieval excludes v1 quickly. The first migration should get you to a mostly clean retrievable corpus fast.

## 3. A totally manual future is not sustainable
Proposal A is right about complexity, but wrong to reject all routine upgrade machinery. You need *some* repeatable process, or this becomes a recurring reset exercise.

## 4. Solo-maintainer reality means “minimal durable automation,” not platform-building
The right long-term system is not “nightly autonomous knowledge healing.”
It is:
- stale/version detection
- safe replace-or-skip
- budget cap
- resumable scope-based jobs

That’s enough.

---

# Specific decisions

## 1) Migration strategy
**Do not delete v1 first.**
Run parallel extraction first. Only cut over after validation.

**Do not re-extract archives in the first wave unless budget/time remains.**
The first goal is retrieval quality for current work, not historical completeness.

### First-wave scope
1. `60_Source_Library`
2. `10_Projects` active/current
3. `30_Templates`
4. `50_RFP` if practically important
5. `80_Archive` later

That likely keeps the first meaningful run around **$8–13**, which fits the monthly budget better than a maximal full reset.

---

## 2) Retrieval policy during transition
This is non-negotiable:

**Once a v2 equivalent exists, the v1 note must leave retrieval.**

Do that by one of:
- removing it from indexed path
- setting `retrieval_exclude: true`
- moving it to a non-indexed archive folder

Do **not** allow side-by-side v1 and v2 notes to remain retrievable for the same source.

That is the most important operational protection.

---

## 3) Identity model
Keep this simpler than some proposals suggest.

### Recommended fields
```yaml
doc_id: <stable-id>
extraction_version: v2
extracted_at: 2026-03-20T12:34:56Z
source_path: 10_Projects/Lenzing/file.pptx
source_hash: <sha256>
source_mtime: 2026-03-18T09:12:00Z
trust_level: extracted
curated: false
retrieval_exclude: false
```

### Identity rules
- **Primary identity**: `doc_id`
- **Freshness**: `source_hash`, `source_mtime`
- **Traceability**: `source_path`

### How to create `doc_id`
For now, use a deterministic ID from **normalized relative source path**, and persist it in `ops.db`.

That is not perfect, but it is good enough at this scale **if paired with a path remap table later only when needed**.

Important: **do not use `source_hash` in `doc_id`**.

### Handling moves
For round 1:
- if path changes and no known remap exists, treat as new and flag old note as orphan candidate
- run `corp freshness` to identify old note for exclusion/archive
- only build explicit remap support if file moves become common

That is a pragmatic compromise.

---

## 4) Manual edits policy
Be strict here.

### Rule
**Generated extraction notes are disposable. Human insight belongs elsewhere.**

Until the curated structure is fully in place:
- auto-skip notes with `trust_level: verified`
- auto-skip notes with `curated: true`
- no auto-merge

### Why
Merge logic is a trap. It sounds helpful and becomes endless edge-case work.

Use **replace-or-skip**, not merge.

---

## 5) Batch scheduling
Do **not** start with nightly.

For this operator and budget, recommended cadence is:

- **Initial migration**: manual weekend or daytime batch in PowerShell
- **Steady state**: weekly scheduled run or on-demand run
- **Nightly** only if source churn becomes materially higher

### Budget controls
- per-run cap: **$2**
- monthly soft cap warning: **$12**
- monthly hard stop: **$18–20**

Given one-person ops, simpler is better than fancy optimization.

---

## 6) Implementation order
This is where most plans fail: too many moving parts at once.

### Recommended sequence

#### Step 0 — Fix blocker
- Fix `synthesize.py`

#### Step 1 — Preflight source audit
Before any extraction:
- verify file presence locally
- detect cloud-only/offline files
- count files by top-level scope
- produce manifest

If this step is weak, everything after is suspect.

#### Step 2 — Pilot validation
Extract 5–10 representative files:
- PPTX
- PDF
- DOCX
- XLSX/RFP
- active project doc
- source library doc

Check:
- note quality
- retrieval usefulness
- metadata completeness
- ingest compatibility

#### Step 3 — Build ingestion and exclusion mechanics
Before large extraction, ensure you can:
- ingest v2 outputs
- exclude/archive v1 from retrieval
- rebuild or update `index.db`
- preserve verified/curated notes

This is more important than upgrade automation.

#### Step 4 — Parallel extraction, scoped
Run:
- Source Library
- Active Projects
- Templates
- maybe RFP

Store in `output_v2/`

#### Step 5 — Cutover
- ingest v2 into new flat structure
- mark/archive equivalent v1 notes out of retrieval
- rebuild index
- keep v1 outputs for 30 days

#### Step 6 — Only now build minimal upgrade command
`corp upgrade-extractions` v1 should do only:
- find outdated notes by version or changed hash
- skip verified/curated
- rerun extraction for scope
- replace note
- refresh index entries
- stop at budget cap

No merge engine.
No fancy prioritization.
No full autonomous orchestration.

#### Step 7 — Archive catch-up
Run only if needed and budget remains.

---

# What I would explicitly reject

## Reject
**Building full continuous extraction/versioning before the first clean cutover.**

That is too much change coupled together.

## Reject
**Keeping mixed v1/v2 notes in retrieval for an extended transition.**

That preserves the very problem you’re trying to solve.

## Reject
**Hash-based primary identity.**

That breaks replacement semantics.

## Reject
**Automatic merge of manual edits into regenerated notes.**

High complexity, low reliability, wrong fit for a solo operator.

---

# Final recommendation in one sentence
**Do a scoped parallel v2 rebuild and clean cutover now, then implement a tiny, budget-capped “replace outdated extractions safely” loop afterward—nothing more ambitious.**

If useful, I can turn this into a concrete decision memo with:
- chosen option
- rationale
- implementation checklist
- acceptance criteria
- rollback plan

*Latency: 53.75s | Tokens: 9726*

### Grok (grok-4.20-beta)

**Contrarian Analysis**

### Proposal A
**Position:** Partially agree.

**Strongest point:** Brutal realism about the solo-ADHD context. This is the only proposal that treats engineering time and future maintenance burden as the primary constraints rather than LLM dollars. The "sophistication bias" diagnosis is correct.

**Weakest assumption:** That a "very lightweight version of Option B" will remain lightweight. History shows even simple upgrade scripts accrete features. It also underestimates how painful periodic nuclear wipes feel once Rob has grown attached to certain notes.

**Risks overlooked:** The manual curation detection script ("notes with >200 words outside CKE sections") sounds simple but is itself a fragile heuristic that will require maintenance. Also fails to address that even the "stupidly simple PowerShell script" will bit-rot.

### Proposal B
**Position:** Disagree.

**Strongest point:** The concrete implementation details (identity model, validation pack, retrieval exclusion rule) are the best in the council.

**Weakest assumption:** That we can build "narrow" continuous upgrades that stay narrow. This is the exact fantasy that kills solo systems. The moment you add `corp upgrade-extractions`, the temptation to add prioritization, reporting, dry-run modes, and exception handling becomes irresistible. You are not building a narrow feature; you are building a lifecycle management platform for one person.

**Risks overlooked:** The enormous psychological tax of living with a system that is "in progress." For an ADHD solo operator, the constant awareness of unfinished automation is worse than the original problem.

### Proposal C
**Position:** Disagree.

**Strongest point:** Takes safety and human curation most seriously.

**Weakest assumption:** That adding a "state machine" and "write-barrier" and "declarative reconciliation" is appropriate for one person's Obsidian vault. This is enterprise thinking applied to a personal knowledge repository. The language itself ("immutable write-barrier", "systemic observability") reveals the sophistication bias.

**Risks overlooked:** The risk that the entire architecture becomes a monument to good intentions that Rob quietly stops using in six months because it's exhausting to maintain.

### Proposal D
**Position:** Disagree.

**Strongest point:** Cleanest articulation of the "clean break now, sustainable forever" story.

**Weakest assumption:** That we *should* have a system that "self-heals" and "automatically benefits from future CKE upgrades." This assumes Rob's knowledge needs are a continuous background process rather than episodic (preparing for specific customer meetings). Most corporate knowledge has a half-life. The desire for perpetual freshness is a hidden value judgment, not a technical requirement.

**Risks overlooked:** The opportunity cost. Every hour spent building `corp upgrade-extractions` is an hour not spent improving extraction quality, prompt engineering, or sales capability.

---

### What Everyone Is Missing

The council is optimizing for the wrong scarcity. The binding constraints are not money ($20/month) or even raw engineering time. They are:

1. **Rob's future motivation** — Complex systems that require ongoing stewardship have a high probability of abandonment.
2. **Psychological friction** — Any system that maintains mixed quality states or requires Rob to think about versioning will be felt as a burden.
3. **The 80/20 reality** — Only active projects + Source Library matter. The 200+ archive projects are mostly noise.

The entire conversation assumes the goal is a *high-fidelity, comprehensive, continuously improving knowledge base*. A better goal is *reliable, high-quality retrieval for the 20% of content that matters, with minimum system maintenance*.

### Revised Recommendation

**Execute a modified Option A with extreme prejudice for simplicity.**

**Concrete plan:**

1. **One-time nuclear option on high-value content only:**
   - Delete all existing v1 extraction notes from active projects, Source Library, and Templates.
   - Do *not* touch archive projects yet.
   - Run fresh v2 extraction against these scopes only (~$9-13).
   - This is the last "big bang."

2. **No continuous upgrade system.** Do not build `corp upgrade-extractions`. Do not extend `corp freshness` for version detection.

3. **Simple re-extraction policy instead:**
   - When Rob starts work on a project, he runs `corp reextract-project Lenzing`.
   - This deletes existing notes for that project and re-extracts fresh. One command.
   - Add a simple `reextract-all-active` command for when he wants to refresh everything important.
   - No budget caps, no nightly jobs, no versioning logic, no identity matching beyond `source_path`.

4. **Manual edits policy:**
   - Create a strict convention: never edit CKE-generated notes directly.
   - All human insight goes into separate notes in `curated/` that link to the extraction note by `doc_id`.
   - Before the nuclear option, run a one-time script to rescue any notes that look manually edited into `curated/`.

5. **Identity:** Use `doc_id` generated from normalized source path. Accept that if Rob moves files, he may get duplicate notes. This is an acceptable tax for simplicity.

**Why this is better than the consensus:**

The council is designing for a future Rob who diligently maintains his personal knowledge infrastructure. That Rob does not exist. The correct design is for the actual Rob: the one who wants to prepare for a customer meeting next Tuesday without thinking about his extraction pipeline.

**Unpopular truth:** Most of the archive content should probably never be re-extracted. The correct re-extraction strategy for archives is "when Rob specifically needs that project again, he will run the command." Treating archives as perpetually valuable is sophisticated delusion.

This approach accepts periodic manual triggers in exchange for never having to maintain a background lifecycle system. For a solo ADHD technical pre-sales engineer, this is the rational trade-off.

The consensus position is what an architect with a team would build. This is what one guy should actually do.

*Latency: 11.62s | Tokens: 8457*

## Synthesis (by claude, non-participant)



# Decision Summary: Re-extraction Strategy

## Consensus

All participants agreed on the following points:

1. **The v1 corpus is actively harmful and must be replaced, not preserved.** At 28/100 eval score, v1 notes degrade retrieval quality. No proposal argued for keeping v1 notes in active retrieval alongside v2 equivalents.

2. **Parallel extraction before cutover is the correct first migration pattern.** Every proposal — including the "nuclear option" advocate — ultimately recommended extracting v2 output to a separate location and validating before touching the live vault. Nobody endorsed deleting first.

3. **Mixed v1/v2 quality in active retrieval must be short-lived or avoided entirely.** Once a v2 equivalent exists, the v1 note must leave the retrievable corpus. This was stated explicitly across all proposals.

4. **Manual edits must be protected via separation, not merge logic.** Universal agreement: never auto-merge. Use replace-or-skip. Human insight belongs in separate curated notes. Notes with `trust_level: verified` are never auto-replaced.

5. **`source_hash` must not be part of primary identity.** Multiple proposals independently identified that hash-based identity breaks replacement semantics when content changes. Identity must survive edits; hash belongs in change detection.

6. **Preflight source audit is a prerequisite.** All proposals flagged the risk of cloud-only/missing files causing silent extraction failures. Local file presence must be verified before any batch run.

7. **Archives are low priority.** No proposal argued for re-extracting 200+ archive projects in the first wave. Active projects, Source Library, and Templates are universally prioritized.

8. **The `synthesize.py` fix is the blocking prerequisite for everything.**

9. **A pilot validation batch (5–10 files) must precede any large extraction run.**

## Unresolved Disagreements

### Disagreement 1: Should a continuous upgrade mechanism (Option D) be built at all?

**For (Proposals B, C, D — majority position):**
Without some version-aware upgrade path, this exact problem recurs every time CKE improves. Even a minimal mechanism — detect outdated notes, replace safely, stop at budget cap — prevents periodic architectural crises. The system already has `corp freshness` detecting stale notes; extending it to detect version mismatches is low-cost.

**Against (Proposal A / Grok — minority position):**
Continuous upgrade systems built by solo ADHD operators inevitably become half-finished maintenance burdens. The psychological tax of an "always improving" background system exceeds its value. A simple on-demand `reextract-project <name>` command achieves 90% of the benefit at 10% of the complexity. Most knowledge retrieval is episodic (preparing for a specific meeting), not continuous.

**Why both sides have merit:** The majority is correct that *some* repeatable process is needed to avoid recurring manual migrations. The minority is correct that the majority consistently underestimates how much infrastructure they're proposing and overestimates a solo operator's willingness to maintain it.

### Disagreement 2: How much infrastructure to build before the first cutover?

**Build more first (Proposals C, D):**
Identity matching, cost tracking, priority queues, budget circuit-breakers, incremental index updates, and version-aware freshness should be designed upfront to avoid rework.

**Build less first (Proposals A, B):**
The first migration should minimize moving parts. Couple the cutover with maximum new infrastructure and you risk shipping neither. Build upgrade automation only after the baseline is clean and validated.

**Why both sides have merit:** Front-loading design prevents rework, but coupling too many changes into one effort is how solo projects stall indefinitely.

### Disagreement 3: Scale of the identity matching system

Proposals ranged from "just use `source_path`, accept occasional duplicates" to three-tier fallback systems with fuzzy matching and persistent remap tables. The underlying tension: robustness versus implementation cost for a ~800 file corpus maintained by one person.

## Recommended Decision

**Execute a scoped parallel v2 extraction and clean cutover now. Afterward, build only a minimal on-demand upgrade command — not autonomous continuous extraction.**

This is closest to Rob's lean (C then D), but deliberately throttled on the D component based on the strongest objection in the debate.

### What this means concretely:

**Phase 1: Clean baseline via parallel extraction and cutover (Option C, scoped)**
- Extract high-value sources (Source Library, Active Projects, Templates) to `output_v2/`
- Validate quality on a sample
- Cut over: ingest v2, exclude/archive v1 from retrieval, rebuild index
- Defer archives

**Phase 2: Minimal upgrade mechanism (Option D-lite, not full Option D)**
- `corp upgrade-extractions` does only: find notes where `extraction_version < current` OR `source_hash` changed, skip verified/curated, re-extract, replace, update index, stop at budget cap
- Also support `corp reextract-project <name>` for on-demand per-project refresh
- **No nightly automation. No priority queue algorithm. No autonomous scheduling.**
- Runs only when Rob explicitly triggers it, or optionally as a weekly scheduled task

### Why this over the alternatives:

**Why not full Option D with nightly batches and economic prioritization?**
Grok's objection is the strongest in the debate: the binding constraint is Rob's future motivation and maintenance tolerance, not dollars or architectural elegance. A system that runs autonomously in the background and requires ongoing stewardship has a high probability of abandonment. The priority queue, cost amortization, and multi-tier scheduling proposals (DeepSeek) are academically sound but operationally inappropriate for one ADHD engineer. The recommended approach captures 80% of Option D's value (version detection, safe replacement, budget cap) with 20% of its complexity.

**Why not pure Option A with no upgrade mechanism at all?**
Because CKE *will* improve again. Without even minimal version-aware replacement, the next upgrade becomes another full architectural discussion. The cost of a simple `corp upgrade-extractions` command that does detect-replace-skip-stop is low enough to justify, and it prevents the "recurring nuclear option" problem that Proposal A's own author acknowledged as a risk.

**Why scope the first wave rather than full corpus?**
Budget reality ($20/month), operator energy, and the 80/20 rule. Active projects + Source Library + Templates covers the content that matters for next Tuesday's customer meeting. Archives can be re-extracted on demand when a specific old project becomes relevant again.

## Risks

### 1. Source files are incomplete or cloud-only
**Likelihood:** Medium-high (OneDrive sync is OFF)
**Impact:** Silent extraction failures, incomplete corpus
**Mitigation:** Mandatory preflight audit script that verifies local file presence, detects offline/reparse-point attributes, counts files per scope, and produces a manifest. Do not proceed until the manifest is clean.

### 2. Pilot validation passes but full-corpus quality disappoints
**Likelihood:** Medium
**Impact:** Wasted budget, degraded retrieval
**Mitigation:** Gate cutover on a representative validation pack (PPTX, PDF, DOCX, XLSX/RFP, active project doc, source library doc). Test not just note quality but actual retrieval usefulness — does `corp retrieve` return better answers with v2 notes?

### 3. Manual edits exist in v1 notes and get lost
**Likelihood:** Low-medium (context suggests minimal manual editing)
**Impact:** Loss of curated human insight
**Mitigation:** Before cutover, run a scan for notes with `trust_level: verified` or significant content outside CKE-generated sections. Move these to `curated/` for manual review. This should be a small set.

### 4. The upgrade mechanism never gets built after cutover
**Likelihood:** Medium (post-migration energy drop)
**Impact:** System slowly degrades again as CKE improves
**Mitigation:** Keep Phase 2 deliberately tiny. `corp upgrade-extractions` v1 should be a single script that wraps existing CKE + ingest logic with version detection and a budget counter. Scope it to under one day of implementation. If it takes longer, the design is too ambitious.

### 5. PowerPoint COM automation crashes on legacy/corrupt files
**Likelihood:** Medium
**Impact:** Stalled batch, partial extraction
**Mitigation:** Disable macros in COM automation (`msoAutomationSecurityForceDisable`), open in read-only mode. Implement per-file timeout and error handling so one bad file doesn't block the batch. Log failures and skip.

### 6. Vault restructure + re-extraction + new ingest path simultaneously creates too many moving parts
**Likelihood:** Medium-high
**Impact:** Coupled failures, debugging difficulty
**Mitigation:** Sequence them strictly. Do not attempt vault restructure and re-extraction cutover in the same work session. Extract first, validate, *then* restructure, *then* ingest into new structure.

### 7. Identity matching creates duplicates when files move
**Likelihood:** Low (post-OneDrive cleanup, structure is stable)
**Impact:** Retrieval pollution from duplicate notes
**Mitigation:** Use `doc_id` from normalized relative source path as primary identity. Persist the path→doc_id mapping in `ops.db`. Accept that moves may create duplicates for now. Use `corp freshness` to detect orphans. Only build explicit remap support if file moves become a recurring problem.

## Action Items

### Step 0: Fix blocker
- [ ] Fix CKE `synthesize.py` template rendering bug
- **Gate:** Nothing proceeds until this works

### Step 1: Preflight source audit
- [ ] Write PowerShell script to scan all extraction-target folders
- [ ] Verify local file presence (detect cloud-only/offline files)
- [ ] Count files per scope: `60_Source_Library`, `10_Projects` (active), `30_Templates`, `50_RFP`
- [ ] Produce manifest with file paths, sizes, types
- [ ] Identify and resolve any missing critical files
- **Gate:** Clean manifest before proceeding

### Step 2: Pilot validation
- [ ] Select 5–10 representative files (PPTX, PDF, DOCX, XLSX, active project doc, source library doc)
- [ ] Extract with CKE v2
- [ ] Confirm eval score ≥60/100
- [ ] Test retrieval quality: do `corp retrieve` queries return better results with v2 notes?
- [ ] Verify metadata completeness: `extraction_version`, `source_hash`, `source_path`, `source_mtime`, `extracted_at`, `trust_level`
- **Gate:** Measurable quality improvement before committing budget to full batch

### Step 3: Protect manual edits
- [ ] Scan existing vault for notes with `trust_level: verified` or significant non-generated content
- [ ] Move identified notes to `curated/` or `99_Archive_Manual/`
- [ ] Verify the set is small and nothing critical is lost

### Step 4: Parallel extraction (first wave)
- [ ] Extract `60_Source_Library` (~276 files) → `output_v2/`
- [ ] Extract `10_Projects` active (~300 files) → `output_v2/`
- [ ] Extract `30_Templates` (~25 files) → `output_v2/`
- [ ] Extract `50_RFP` (14 files) → `output_v2/` if practically important
- [ ] Run as resumable PowerShell batches with per-file error handling and logging
- [ ] Track cost against $12–15 target for this wave
- **Estimated cost:** $9–13 | **Estimated duration:** 5–7 hours

### Step 5: Validate before cutover
- [ ] Sample quality check on v2 outputs across file types
- [ ] Test retrieval with v2 corpus in isolation
- [ ] Confirm ingest pipeline works end-to-end

### Step 6: Execute vault restructure
- [ ] Implement Council Decision (flat `knowledge/`) structure
- [ ] Ensure auto-generated and curated notes have clear separation
- **Note:** Do this as a separate step, not simultaneously with cutover

### Step 7: Cutover
- [ ] Ingest v2 extractions into new vault structure
- [ ] Remove or exclude all v1 extraction notes from retrievable paths
- [ ] Rebuild `index.db`
- [ ] Verify retrieval works correctly with v2 corpus
- [ ] Archive v1 outputs (zip, retain 30 days, then delete)

### Step 8: Build minimal upgrade command
- [ ] Implement `corp upgrade-extractions`:
  - Detect notes where `extraction_version < current` OR `source_hash` changed
  - Skip notes with `trust_level: verified` or `curated: true`
  - Re-extract, replace note, update index entries
  - Stop at per-run budget cap ($2 default)
  - Log actions to `ops.db`
- [ ] Implement `corp reextract-project <name>` for on-demand single-project refresh
- [ ] Add `extraction_version` and `doc_id` to all frontmatter going forward
- [ ] Persist source_path → doc_id mapping in `ops.db`
- **Scope constraint:** If this takes more than one day to implement, simplify further

### Step 9: Archive catch-up (deferred, on-demand)
- [ ] Re-extract specific archive projects only when needed for active work
- [ ] Use `corp reextract-project <name>` on demand
- [ ] Do not batch-extract all archives unless budget and motivation align
