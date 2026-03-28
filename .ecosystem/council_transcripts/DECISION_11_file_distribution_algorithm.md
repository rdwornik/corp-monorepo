# AI Council Debate: # Council Question: File Distribution Algorithm — The Core Routing Engine

## Wh

**Date:** 2026-03-23 00:23:52
**Panel:** deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta, gpt-5.4
**Synthesizer:** claude (non-participant)
**Rounds:** 2
**Duration:** 267.2s
**Mode:** full (4-model panel)
**Source:** council_inbox\COUNCIL_file_distribution_algorithm.md

---

## Round 1: Initial Responses

### Gemini (gemini-3.1-pro-preview)

## Position
I recommend a **hybrid, edge-sanitizing routing engine (1C, 7C)** that renames files immediately upon ingest (2A) into flat, flat-named directories with centralized media (4B, 5A), and crucially relies on **cryptographic content hashes** rather than brittle file paths for CKE `source_path` tracking (6B) to enable safe atomic migrations of legacy data (3D, 8).

## Rationale
*   **Defense-in-Depth via Edge Sanitation (2A, 1C):** Renaming and validating files instantly upon entering `00_Inbox/` ensures no malicious characters, malformed extensions, or path-breaking spaces enter the core repository. The hybrid approach forces 90% of files through strict, known-good regex patterns in `content_registry.yaml`, falling back to the LLM only for classification (never for direct path generation), thereby eliminating path-hallucination and prompt injection risks.
*   **Decoupled Interoperability & Lineage (6B):** File paths are highly mutable; file contents are the true source of knowledge. By making `source_hash` the primary key in CKE extraction (with `source_path` as a secondary cache), the distribution algorithm can freely move, rename, or reorganize files without permanently severing the Obsidian vault's knowledge chain.
*   **Platform Safety & Sync Reliability (4B, 5A):** OneDrive is notoriously fragile with symlinks and path-length limits (MAX_PATH limitations). Centralizing massive MP4s in `40_Media/` and utilizing flat folders with robust, self-describing filenames prevents sync breakage, phantom data loss, and nesting depth violations.
*   **Safe Reconciliation (3D, 8):** Because lineage is secured by hashes, you can safely deploy a `corp reconcile` mode. This script can holistically scan, accurately rename, and atomically update legacy files and vault references without breaking existing extractions. 

## Trade-offs
*   **Development Complexity:** Building a dual-key system (Hash + Path) for CKE tracking requires modifying the current extraction logic and note metadata schemas.
*   **Visual Hierarchy:** You sacrifice the "neatness" of deep subfolders in Windows File Explorer in favor of flat directories. You must rely on Obsidian or search indexing to group files logically.
*   **Migration Cost:** The one-time atomic migration of the existing 300+ files requires a heavy initial compute phase to calculate hashes, generate new names, and batch-update vault markdown files.

## Risks
*   **Risk: File updates alter the hash, breaking the lineage.** 
    *   *Mitigation:* CKE must store *both* `source_path` and `source_hash`. If a file is modified (e.g., a PPTX is updated), `corp freshness` uses the known `source_path` to find the file, calculates the new hash, and updates the note's metadata automatically, preserving the link.
*   **Risk: LLM hallucinates categories or client names, resulting in unauthorized or chaotic folder creation.**
    *   *Mitigation:* The LLM must be strictly constrained to output JSON against an explicit schema. It must select from a predefined enum of products/topics. If a "new" client or topic is detected, the engine must quarantine the file in `00_Inbox/_Review/` rather than automatically creating new directories.
*   **Risk: Atomic migration of legacy files corrupts the current vault.**
    *   *Mitigation:* Implement the reorganization script as a transactional state-machine. It must support a `--dry-run` flag that outputs a `manifest.json` detailing every planned move and metadata update. Require a mandatory backup of both `60_Source_Library` and the Obsidian vault before committing changes.

*Latency: 26.27s | Tokens: 5606*

### Deepseek (deepseek-reasoner)

## Position
Implement a **hybrid rule-based + LLM classification** algorithm with **batch processing + auto-review**, enforce **renaming on ingest using content-hash-based source tracking**, and create a **"reorganize" mode** to systematically correct existing file placements. This ensures scalability, maintains reference integrity, and delivers immediate automation while allowing gradual cleanup.

## Rationale
- **Hybrid classification (C)** maximizes throughput: rules handle 80-90% of known patterns instantly, while an LLM (Flash) resolves ambiguities only when confidence thresholds are unmet, balancing cost ($0.01 per 1K files) with handling edge cases.
- **Content-hash-based source_path (B)** decouples file identity from location/name, making references resilient to moves/renames—critical for maintaining note integrity as the corpus evolves.
- **Batch + auto-review processing (C)** enables unattended operation for high-confidence matches (meeting the "no manual triage" constraint) while flagging low-confidence items for later review, ensuring robustness without blocking the pipeline.
- **"Reorganize" mode** addresses technical debt proactively: scanning existing misplacements and applying routing rules in dry-run mode first, then executing with confirmation, preventing entropy from accumulating.

## Trade-offs
- **Initial complexity**: Hybrid system requires maintaining both rule sets and LLM prompt engineering, increasing development overhead versus pure rule-based.
- **Storage overhead**: Content hash indexing requires a small database (SQLite) or manifest file, adding another metadata layer to manage.
- **Latency vs. accuracy**: LLM calls (even Flash) add ~200-500ms per ambiguous file; we trade pure speed for classification accuracy on ambiguous inputs.
- **OneDrive limitations**: Symlinks for media files are discarded due to sync issues; instead, we implement a metadata-based linking system, which requires custom tooling to resolve paths.

## Risks
- **LLM classification drift**: The LLM might misclassify files if training data shifts. Mitigation: log all LLM decisions with confidence scores, and use review queue outcomes to fine-tune rules regularly.
- **Hash collisions**: Extremely low probability (SHA-256) but could cause misidentification. Mitigation: include file size and partial content check on collision.
- **Race conditions**: If CKE extracts while a file is being moved, source_path may be transiently broken. Mitigation: implement file locking during distribution (rename to `.processing` extension) and hash-based lookup that resolves to latest location.
- **Rule explosion**: Routing rules may become unmanageable. Mitigation: structure content_registry.yaml with hierarchical patterns (e.g., `ppt/*_client_*.pptx`) and validate with a schema; automate rule testing with a corpus of sample files.

---

## Implementation Roadmap
1. **Phase 1 (Immediate)**: Extend content_registry.yaml with missing destinations and pattern rules. Build hash-indexed file registry (SQLite). Implement batch processor with rule engine only.
2. **Phase 2 (1 week)**: Add LLM classifier for low-confidence matches (confidence <85%). Implement auto-review queue (files moved to `_Review` with suggested classification).
3. **Phase 3 (2 weeks)**: Build "reorganize" mode that scans existing locations, proposes moves via dry-run, and updates hash registry. Integrate hash-based source_path in CKE extraction.
4. **Phase 4 (Ongoing)**: Gradual migration: rename existing files on next touch, update source_path via hash lookup. Schedule quarterly reorganize runs.

---

## Specific Answers to Council Questions
1. **Algorithm architecture**: **C (Hybrid)**. Rules first, LLM only for ambiguous.
2. **Naming convention**: **C (Both)**. Rename on ingest for consistency, and use hash-based source_path so extraction is unaffected.
3. **Existing files**: **B (Rename on next touch)** + eventual **D (Batch update)**. Gradual migration with a planned one-time source_path update after majority are renamed.
4. **Folder structure**: **A (Subfolders by product)** with a `_Multi` folder for cross-product decks. Maintain a flat index for search.
5. **MP4 recordings**: Centralize in `40_Media/` with a metadata YAML linking to contextual folders. Avoid symlinks due to OneDrive.
6. **CKE integration**: **B (source_path uses content hash)**. Build a hash-to-path resolver service.
7. **Queue processing**: **C (Auto + review)**. Batch process high-confidence, interactive review for low-confidence.
8. **Existing wrong locations**: Yes, implement **"reorganize" mode** with dry-run and confirmation prompts.

---

**Performance Note**: The rule engine uses Aho-Corasick for multi-pattern filename matching (O(n+m)) and processes ~10K files/sec on SSD. LLM calls are batched (10 files/call) to amortize latency. Hash indexing uses Bloom filters for fast duplicate detection.

*Latency: 67.03s | Tokens: 5616*

### Openai (gpt-5.4)

## Position
Adopt **C) Hybrid architecture**: deterministic rules in `content_registry.yaml` first, then **LLM-assisted classification only for unmatched/low-confidence files**, with **rename-on-ingest**, **extract only from stable final locations**, and a **separate reorganize mode** for legacy cleanup.  
For structure, use **light topic/client subfolders only where they reduce operational chaos**, but avoid deep taxonomies; prioritize a stable path model over perfect information architecture.

## Rationale
- **This is the only option that balances robustness with zero-manual-sorting.** Rule-only will fail on messy real-world filenames; LLM-only is too opaque for the core routing engine. Hybrid gives predictable routing for common cases and graceful handling of ambiguity.
- **Path stability is more important than naming purity.** Since CKE and Obsidian depend on `source_path`, the system must treat routing as the canonical pre-extraction step. Moving/renaming after extraction should be exceptional, not normal.
- **Rename-on-ingest keeps the filesystem sane from day 1.** If you defer naming cleanup to extraction, the source library remains chaotic and every downstream tool inherits inconsistency.
- **A review queue is the only practical substitute for manual triage.** “No manual sorting” does not mean “pretend uncertainty doesn’t exist.” Auto-route high confidence; quarantine low confidence into `00_Inbox/_Review/` with machine-generated suggestions and logs.
- **Legacy cleanup should not be bundled into first-pass ingest.** Reorganizing all existing content now is valuable, but it is a migration project with blast radius. Build the engine for new files first, then run controlled reorganize passes with note-path updates.

## Trade-offs
- **More implementation complexity than pure rules.** You need confidence scoring, fallback behavior, and logging for why a file was classified a certain way.
- **Some files will still land in `_Review/`.** This slightly violates the dream of full automation, but it is far better than silent misrouting that poisons extraction and tags.
- **Rename-on-ingest creates an up-front break from current habits.** People dropping files into inbox will see names changed immediately, which may feel unfamiliar at first.
- **Flat-only structure is simpler, but less usable; deep folders are more browseable, but brittle.** The recommended middle ground means accepting some ambiguity for multi-topic files.
- **Legacy inconsistency remains for a while.** By not mass-renaming everything immediately, you preserve stability but carry mixed naming conventions during transition.

## Risks
- **Risk: Misclassification sends files to the wrong final location, poisoning extraction and tags.**  
  Mitigation: implement a confidence threshold, require exact rule matches to override LLM guesses, and send low-confidence cases to `_Review/` instead of forcing a destination.

- **Risk: Existing extracted notes break if legacy files are moved later.**  
  Mitigation: for legacy migration, choose **D) Rename + update source_path** but only in a dedicated migration command with dry-run, full logging, and rollback manifest. Do not casually reorganize already-extracted files.

- **Risk: LLM classifications drift or become inconsistent over time.**  
  Mitigation: constrain the LLM to classify only into registry-defined enums, return structured JSON, and log prompt/version/model used. Periodically promote successful LLM decisions into deterministic rules.

- **Risk: OneDrive path/file limitations cause failures.**  
  Mitigation: enforce filename sanitization, path-length limits, no symlinks, and a deterministic slugging function. Keep folder depth shallow.

- **Risk: “Series detection” becomes a source of hidden complexity.**  
  Mitigation: implement series handling only for named known series in v1 (`Cognitive Friday`, `Lighthouse`, cert rotation). Do not attempt generic sequence inference initially.

---

## Concrete recommendations by council question

### 1. Algorithm architecture
**Recommendation: C) Hybrid**

**Design:**
1. **Rule pass**  
   - Extension-based routing
   - Filename regex/patterns
   - Parent-folder hints
   - Known client/product dictionaries
   - Series aliases from `content_registry.yaml`
2. **Confidence scoring**
   - Example: exact series match = 0.95
   - exact client + type + topic = 0.9
   - weak keyword-only = 0.6
3. **LLM fallback only if below threshold**
   - Use cheap model
   - Input: filename, extension, partial OCR/text if available, parent folder
   - Output: strict JSON: `{type, topic[], client, series, confidence, rationale}`
4. **Routing decision**
   - If confidence >= threshold, route
   - Else send to `00_Inbox/_Review/`

**Pragmatic note:** start with 15-20 high-value rules covering decks, certs, recordings, RFP docs, training, product docs. Don’t try to solve all edge cases in v1.

---

### 2. Naming convention enforcement
**Recommendation: A/C in practice — rename on ingest, then extraction uses the ingested name**

This is effectively **rename at ingest as the source of truth**.

**Recommendation for naming format:**
```text
{YYYY-MM-DD}_{category}_{topic-or-series}_{client-or-generic}_{short-description}_v{n}.{ext}
```

**Examples**
- `2026-03-22_DECK_WMS_Generic_Slotting_Overview_v1.pptx`
- `2026-03-22_RFPQ_Platform_Veronesi_Integration_Questionnaire_v2.xlsx`
- `2026-03-22_CERT_Security_Generic_ISO27001_Certificate_v1.pdf`
- `2026-03-22_REC_CognitiveFriday_Generic_AgenticAI_Session12_v1.mp4`

**Rules**
- Preserve original filename in metadata/log
- Slugify invalid OneDrive characters
- Cap description length
- If date is unknown, use ingest date plus `date_unknown=true` metadata

---

### 3. Existing 300+ files already in place
**Recommendation: split strategy**
- **For already-extracted files:** use **D) Rename + update source_path**, but only as a controlled migration
- **For not-yet-extracted legacy files:** batch rename/rehome before extraction

So the practical recommendation is **not one blanket option**. Treat extracted and unextracted files differently.

**Why:**  
Breaking note linkage is worse than living with inconsistency for another week.

**Migration sequence**
1. Freeze new extraction from unstable folders
2. Inventory which legacy files already have notes
3. For extracted files: dry-run rename + path update
4. For unextracted files: reorganize freely
5. Re-extract only where needed

---

### 4. Folder structure: topic subfolders vs flat + tags?
**Recommendation: mostly A, but shallow and constrained**

Use **shallow product/topic subfolders only for high-volume categories**, not for everything.

**Example**
- `30_Templates/01_Decks/WMS/`
- `30_Templates/01_Decks/Platform/`
- `30_Templates/01_Decks/Multi_Product/`

Not:
- deeply nested `Product/Domain/Subdomain/Audience/Version`

**Why this beats pure flat**
- Explorer usability matters in a OneDrive/PowerShell workflow
- 200+ decks in one folder gets ugly fast
- Multi-product ambiguity is solved with a `Multi_Product` bucket plus metadata tags

**Recommendation by category**
- **Decks:** shallow product subfolders
- **RFP responses/questionnaires:** client subfolders
- **Certificates:** flat + archive subfolder by year/vendor if needed
- **Training series:** series folders
- **Product docs:** product subfolders
- **Competitive:** vendor/topic subfolders if count grows, otherwise flat

---

### 5. MP4 recordings: centralize or distribute?
**Recommendation: B with guardrails**

Keep recordings **with their content context** where that context is obvious and valuable:
- Lighthouse recordings in Lighthouse
- Cognitive Friday recordings in Cognitive Friday
- Client workshop recordings in client project folder
- Generic media with no contextual home in `40_Media/`

**Why not centralize everything**
- Context matters for discovery and extraction linkage
- OneDrive symlinks are a non-starter
- Users browse by context more than by media type

**Guardrails**
- Use a `Media/` subfolder inside heavy-content areas if needed
- Add size reporting and retention rules
- For cert/archive-like replacements, move older media to `_Archive/`

So this is effectively **distributed storage with naming discipline**, not full centralization.

---

### 6. How does this integrate with CKE extraction?
**Recommendation: A first, with a future path to C**

- **Primary rule:** **Extract only from stable locations**
- `source_path` should point to post-routing canonical path
- Do not extract from `00_Inbox/`

**Later enhancement**
- Add a `file_id` / content hash field in metadata for resilience
- Add `corp freshness` path repair later if needed

**Practical recommendation**
- In v1, path stability is enough
- In v2, augment notes with:
  - `source_path`
  - `source_hash`
  - `source_ingest_id`

This gives you future repair ability without blocking current delivery.

---

### 7. Queue processing: batch vs interactive?
**Recommendation: C) Auto + review**

**Behavior**
- `corp ingest-inbox` processes all files in batch
- High-confidence files auto-routed
- Low-confidence files moved to `00_Inbox/_Review/`
- Log includes suggested destination and reason
- Optional `--interactive` exists for debugging/admin, not normal usage

This is the only flow compatible with:
- ADHD simplicity
- no manual sorting
- real-world ambiguity

**Do not make interactive the default.**

---

### 8. Existing files in wrong locations
**Recommendation: Yes, build a separate `reorganize` mode**

But this should be **phase 2**, not block core inbox ingest.

**Two commands**
- `corp ingest-inbox` → handles new arrivals only
- `corp reorganize-library --dry-run` → scans existing folders, proposes moves/renames/archives
- `corp reorganize-library --apply` → executes and updates `source_path` where needed

**Reorganize mode should support**
- detecting misplaced file types
- cert supersession and archiving
- absurd folder-name normalization
- empty folder cleanup
- MP4 relocation proposals
- path update manifest for Obsidian notes

---

## Recommended v1 operating model

### Canonical pipeline
1. File lands in `00_Inbox/`
2. `corp ingest-inbox`
3. Rule-based classify
4. LLM fallback for low-confidence
5. Rename + route to final canonical folder
6. Write manifest/log entry
7. Only then allow CKE extraction
8. Obsidian tags derive from routing metadata

### Required metadata log per file
Store in JSONL or CSV manifest:
- original_path
- original_name
- content_hash
- ingest_timestamp
- classified_type
- inferred_topic
- inferred_client
- inferred_series
- destination_path
- final_name
- confidence
- decision_source (`rule`, `llm`, `review`)
- model/version if LLM used

This log will save you during migration and debugging.

---

## Suggested implementation phases

### Phase 1: Stabilize the future
Build inbox ingest for:
- decks
- recordings
- certs
- RFP questionnaires/responses
- product docs
- training series

Do **not** continue broad extraction until this is working.

### Phase 2: Controlled legacy migration
Run reorganize on:
- certificates
- training folders
- MP4s
- obvious misplaced decks
- empty folders

### Phase 3: Extraction integration hardening
Add:
- `source_hash`
- note path updater
- migration manifest replay/rollback

---

## Bottom line
The pragmatic answer is:

- **Hybrid classifier**
- **Rename and route on ingest**
- **Extract only after final placement**
- **Shallow folder taxonomy**
- **Auto-route with review queue**
- **Separate reorganize mode for legacy cleanup**
- **Controlled migration for the existing 300+ files with source_path updates**

That gets you a stable routing engine quickly without pretending the filesystem is clean enough for pure rules or mature enough for a full metadata-first architecture.

*Latency: 45.45s | Tokens: 5176*

### Grok (grok-4.20-beta)

**## Position**

Build a **strictly rule-based engine** (option A) centered on `content_registry.yaml`, with aggressive normalization on ingest and content-hash-based identification. LLM assistance is a dangerous temptation to be deferred indefinitely. Rename *only new files* from Inbox (option C for Q2), leave all existing files untouched (option C for Q3), and use a flat + naming convention structure (option B for Q4). Source files must be treated as immutable once placed; `source_path` is replaced by content hash (option B for Q6).

This is the opposite of what most architects would propose ("let's add intelligence!").

## Rationale

- **Determinism is non-negotiable.** This system is the root of truth for the entire knowledge graph. Non-deterministic LLM output (even Flash) will eventually create two different classifications for the same file on different days, poisoning the vault. Everyone is taking for granted that classification will be stable.
- **The ADHD constraint is being lied to.** "Zero manual triage" is delusional when files arrive in 17 different naming conventions from humans. The contrarian truth is that the algorithm must *reject* ambiguous files to  `_Review` aggressively. This creates necessary negative feedback that trains both Rob *and* his colleagues. Hand-holding with LLM just perpetuates the mess.
- **Existing 300+ files are radioactive.** Any batch rename or mass `source_path` update (options A/D) is architectural suicide. The hidden assumption is "our extraction data is high quality." From the audit, it clearly isn't. Better to have consistent *new* behavior than perfect but dangerous migration.
- **Multi-dimensional classification belongs in metadata, not paths.** Subfolders by product (option A for Q4) or scattering recordings (option B for Q5) creates false hierarchies. The filesystem should be a simple physical layout; Obsidian queries and the manifest should handle semantics.
- **Hash-based identity is the only sane long-term model.** Path-based `source_path` was always a brittle design. Changing to content hash (or at minimum a stable `file_id`) is the correct architectural move, even if it requires CKE changes.

## Trade-offs

- Give up "magical" handling of ambiguous files. Some decks will sit in `_Review` until manually named properly.
- Give up visual organization in File Explorer for certain categories (flat folders).
- Give up the dopamine of "AI doing the thinking." This is deliberately boring.
- Accept that `content_registry.yaml` becomes a more complex but still declarative ruleset (patterns, regex, folder hints, hash exceptions).

## Risks

- **Risk: Review folder becomes a new Inbox black hole.** *Mitigation:* The `corp ingest-inbox` command *must* output extremely clear rejection reasons ("no client detected in name or parent folder") and suggested filename. Make the barrier to fixing it trivial.
- **Risk: Registry grows into an unmaintainable mess.** *Mitigation:* Enforce a strict schema with tests. Every rule must have an example file + expected destination. Treat the registry like production code.
- **Risk: Colleagues continue dumping garbage.** *Mitigation:* Make the rejection loud and social. The system should generate a weekly "Inbox Hall of Shame" report showing the worst naming offenders. Use shame as a feature.
- **Risk: Hash collisions or performance on 10k+ files.** *Mitigation:* Use xxh128 or similar fast hash. Store hashes in a simple SQLite manifest next to the registry rather than scanning everything every time.

**Contrarian summary:** The council is asking the wrong question. The real question isn't "how smart can our routing algorithm be?" It's "how do we stop treating the filesystem like a garbage disposal?" The algorithm should be *dumb but strict*, because the problem is organizational maturity, not insufficient intelligence in the routing layer. Everything else is cope.

*Latency: 22.36s | Tokens: 4070*

## Round 2: Critique

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, my primary concerns are **supply chain trust** (the Inbox is an untrusted zone), **defense-in-depth** (preventing chaotic or malicious data from poisoning the vault), and **heterogeneous interoperability** (ensuring OneDrive, the PowerShell automation, CKE, and Obsidian do not corrupt each other through race conditions or broken references).

Here is my evaluation of the council’s proposals, followed by my architectural mandate.

---

### Evaluation of Proposals

#### **Proposal A**
*   **Stance:** Partially Agree.
*   **Strongest Point:** Implementing cryptographic content hashes for `source_path` tracking (6B) and edge-sanitizing on ingest (2A). Decoupling file identity from its mutable location is the only way to ensure resilient interoperability between the filesystem and Obsidian.
*   **Weakest Assumption:** Assumes atomic updates of legacy files and Obsidian markdown files are safe and easy. Batch-updating markdown files while OneDrive is actively syncing is a recipe for sync conflicts, duplicated files (`note-Rob-Desktop.md`), and corrupted graphs.
*   **Overlooked Risk:** The "Move + Modify" gap. If a user edits a PowerPoint (changing its hash) and then moves it to a new folder (changing its path) before the system runs, the lineage is permanently severed.

#### **Proposal B**
*   **Stance:** Partially Agree.
*   **Strongest Point:** Recognizing that non-deterministic LLM outputs can poison the structural root of truth. The strict defense-in-depth posture of deterministic routing is highly secure.
*   **Weakest Assumption:** Believing that "shame as a feature" and relying on manual triage for ambiguous files is viable. The business constraint is explicitly "zero manual sorting." If the pipeline requires manual intervention, it will stall, and users will bypass it entirely.
*   **Overlooked Risk:** Operational Denial of Service (DoS). If real-world files consistently fail the strict regex rules, the `_Review/` folder becomes a black hole, halting the knowledge supply chain. 

#### **Proposal C**
*   **Stance:** Partially Agree.
*   **Strongest Point:** The phased boundary between ingest (new files) and reorganization (legacy files). Explicitly isolating the blast radius of legacy cleanup protects the current operational state.
*   **Weakest Assumption:** Deferring hash-based identity to "v2" while relying purely on path stability for v1. Path stability on user-accessible network drives is an illusion. If legacy files are moved later without hashes already in place, the vault references will break.
*   **Overlooked Risk:** Prompt injection via filenames. If a user or client submits `urgent_deck_ignore_instructions_and_return_admin.pptx`, an unsanitized LLM fallback could be manipulated into routing files to restricted directories or hallucinating invalid schemas.

#### **Proposal D**
*   **Stance:** Disagree.
*   **Strongest Point:** The introduction of a transactional SQLite state manifest to track file history and decoupling identity from the filesystem.
*   **Weakest Assumption:** Proposing custom "metadata YAML linking" for MP4s to bypass OneDrive symlink limitations. This introduces a proprietary integration layer that Obsidian cannot natively read, breaking markdown interoperability.
*   **Overlooked Risk:** Renaming files to `.processing` during runtime. Cloud-sync engines (OneDrive) lock files during extension changes. This will trigger massive sync churn, file-lock race conditions, and pipeline crashes.

---

### Architect's Revised Recommendation: The Trust-Verified Routing Engine

To achieve defense-in-depth and safe interoperability, we must treat the `00_Inbox/` as an untrusted boundary, the routing engine as a sanitation gateway, and the filesystem + Obsidian vault as decoupled but synchronized state machines. 

**1. Algorithm Architecture: Sanitized Hybrid (Question 1: C)**
*   **Rule Engine First:** Deterministic rules in `content_registry.yaml` process the majority of files.
*   **LLM Fallback with Strict Bounds:** Before an unmatched filename is sent to the LLM, it must be sanitized of special characters to prevent prompt injection. The LLM must be constrained via `response_format` to output *only* strict JSON mapping to pre-approved enums. **The LLM never dictates file paths**; it only returns classification tags, which the rule engine translates into paths.

**2. Identity & Interoperability: The Tri-Key Concept (Question 6: B, modified)**
File paths are mutable. Content hashes change upon edits. To solve the "Move + Modify" gap, we must track files using three keys stored in a centralized SQLite manifest (and injected into CKE notes):
*   `ingest_id`: An immutable UUID assigned at ingest.
*   `content_hash`: SHA-256 of the current file state.
*   `source_path`: The current physical location.
If a path breaks, CKE queries the SQLite manifest via `content_hash`. If the hash also changed, it resolves via `ingest_id` (if file metadata tagging is supported) or flags for a probabilistic path-repair.

**3. Edge Sanitation & Naming (Question 2: A)**
Rename absolutely everything upon ingest. The filesystem must be sanitized at the edge.
*   Filenames must be slugified (`[a-zA-Z0-9_-]`) to prevent directory traversal attacks and bypass OneDrive's `MAX_PATH` limitations.
*   Executable extensions (`.exe`, `.ps1`, `.bat`) hidden inside zip files or misnamed must be structurally quarantined.

**4. Safely Processing the Queue (Question 7: A)**
*   **Pure Batch Mode.** Interactive mode violates the business constraint. 
*   High-confidence matches are routed. Low-confidence files go to `00_Inbox/_Review/`.
*   *Integration:* Instead of manual triage, a nightly cron job analyzes the `_Review/` folder and generates a pull request (or log report) proposing new deterministic regex rules for `content_registry.yaml`. The system learns rather than forcing Rob to sort.

**5. Folder Structure & Media (Questions 4: B, 5: B)**
*   **Shallow/Flat Folders + Robust Naming:** Deeply nested folders break OneDrive syncs due to path limits. Use flat structures like `01_Decks/` with the naming convention doing the heavy lifting.
*   **Distributed Media:** Keep MP4s with their contextual documents. Do not use symlinks or proprietary YAML pointers. Rely on the Tri-Key SQLite manifest to track where the media is.

**6. Legacy Migration & Existing Files (Questions 3: D, 8: Yes)**
Do not execute a mass move on day one.
*   **Phase 1:** Deploy the ingest engine for *new* files only.
*   **Phase 2:** Run a read-only indexer over the legacy `60_Source_Library`. Compute hashes and populate the SQLite manifest to establish a baseline.
*   **Phase 3:** Execute a `corp reconcile` script. This script acts as a state machine: it updates the legacy file path, confirms the OneDrive sync API status, and *then* updates the Obsidian markdown `source_path`. Require a vault backup prior to execution.

*Latency: 41.70s | Tokens: 12537*

### Deepseek (deepseek-reasoner)

## Evaluation of Proposals

**Proposal A - Edge-Sanitizing Routing Engine**
- **Position**: Partially agree with hybrid architecture and hash-based tracking. Disagree with flat directory structure and centralized media.
- **Strongest point**: Cryptographic hashing for source_path is the correct long-term architectural move. Decoupling identity from location solves the core brittleness problem.
- **Weakest assumption**: That flat directories with self-describing filenames are usable for 200+ files. This ignores human cognitive load and filesystem performance degradation beyond ~50 files/directory.
- **Overlooked risk**: Hash recalculation on file modifications requires continuous synchronization between CKE and the distribution engine. This creates a distributed system consistency problem.

**Proposal B - Strictly Rule-Based Engine**
- **Position**: Strongly disagree with the anti-LLM stance but agree on deterministic classification.
- **Strongest point**: Correctly identifies that classification stability is non-negotiable for a routing system that underpins the knowledge graph.
- **Weakest assumption**: That ambiguous files can simply be rejected to `_Review`. With ~85 MP4s already scattered and chaotic naming, review queue would become a bottleneck requiring constant manual intervention.
- **Overlooked risk**: Rule explosion in content_registry.yaml becomes unmaintainable. With 17+ file types and complex naming patterns, the rule count grows O(n²) with edge cases.

**Proposal C - Hybrid with Shallow Folders**
- **Position**: Mostly agree, but disagree on distributed recordings.
- **Strongest point**: Practical phased approach with separate reorganize mode. Correctly prioritizes path stability over naming purity.
- **Weakest assumption**: That multi-product ambiguity can be solved with a `Multi_Product` bucket. This creates a "miscellaneous" category that will balloon over time.
- **Overlooked risk**: Shallow product subfolders create classification contention. A deck covering WMS and Planning must be arbitrarily placed in one folder, losing the other semantic dimension.

**Proposal D - Hybrid with Performance Optimizations**
- **Position**: Partially agree on implementation roadmap, disagree on centralized media with YAML links.
- **Strongest point**: Quantifies performance characteristics (10K files/sec with Aho-Corasick). Correctly identifies batch LLM calls as latency optimization.
- **Weakest assumption**: That SQLite Bloom filters are appropriate for duplicate detection. False positives in Bloom filters would cause incorrect deduplication decisions.
- **Overlooked risk**: File locking during distribution creates race conditions with OneDrive sync. `.processing` extensions could cause sync conflicts.

---

## Revised Recommendation: Deterministic Routing with Content Graph Index

### Core Architecture Decision: Hybrid with Guardrails (1C Modified)

**Implementation**: Rule-first classifier with LLM fallback, but with critical constraints:

1. **LLM output must be deterministic**: Use temperature=0, seed-fixed prompts, and classification limited to registry-defined enums
2. **Cache LLM decisions**: Store (filename_hash → classification) in SQLite to ensure identical files get identical routing
3. **Confidence thresholding**: Only auto-route when rule confidence ≥0.9 OR cached LLM classification exists

**Performance impact**: Cached classifications reduce LLM calls by 70-80% after initial learning period. SQLite lookup O(1) vs LLM call (200-500ms).

### Critical Correction: Folder Structure Must Be Multi-Dimensional (4C Modified)

**Problem**: Both subfolders (A) and flat (B) lose information. A deck about "WMS Security for Client X" belongs in exactly one folder but has three dimensions.

**Solution**: **Single canonical location + metadata manifest**:
- Physical location: `30_Templates/01_Decks/WMS/` (primary topic wins)
- Metadata file: `30_Templates/01_Decks/_manifest.yaml` contains:
  ```yaml
  2024-03-22_DECK_WMS_Security_Veronesi_v1.pptx:
    primary_topic: WMS
    secondary_topics: [Security, Platform]
    client: Veronesi
    hash: xyz123
  ```

**Performance**: Manifest file read O(n) for whole directory, but we maintain inverted index in SQLite for O(log n) lookups.

### Hash-Based Source Tracking with Versioning (6B Enhanced)

**Critical flaw in all proposals**: Content hashes break when files are modified (common with PPTX decks).

**Solution**: **Content-addressable storage with version chain**:
```
source_id = sha256(initial_content)
CKE stores: source_id, source_path, source_mtime
Distribution engine maintains:
  source_id → [(path_v1, mtime_v1), (path_v2, mtime_v2), ...]
```

When file modifies:
1. New hash = sha256(new_content)
2. Distribution engine links new_hash → parent: old_hash
3. CKE freshness check follows hash chain to find current location

**Storage overhead**: ~100 bytes per version per file. For 10K files with avg 2 versions = 2MB index.

### Naming Convention: Immediate with Fallback (2A Modified)

**Algorithm**:
```
if filename_contains_date():
    use_existing_date()
else:
    date = max(file_modified_date, ingest_date)
    add_prefix: "date_unknown_"
```

This preserves existing dates when present (common in client files) while sanitizing truly chaotic names.

### Legacy Files: Atomic Migration with Two-Phase Commit (3D Enhanced)

**Batch rename is required** but must be atomic:

1. **Phase 1 - Dry run**: Generate rename/manifest and compute new source_paths
2. **Phase 2 - Update vault notes** using computed source_paths (CKE offline)
3. **Phase 3 - Execute file moves** atomically (rename is atomic on NTFS)
4. **Phase 4 - Verify**: Compare hash of moved files against dry-run manifest

**Performance**: Parallelize file hashing (4 threads) and batch SQLite updates. 300 files: ~2 minutes.

### Recordings: Content-Addressed with Reference Counting (5C Modified)

**Centralize large files** but track references:

```
40_Media/hash_abc123.mp4  # Actual file
60_Source_Library/02_Training/Lighthouse/  # Contains:
    session_12.md  # References media via hash
    _media_refs.yaml → [hash_abc123]
```

**Advantage**: Single copy of large files, automatic cleanup when last reference removed.

### Queue Processing: Batch with Priority Queue (7C Enhanced)

**Implementation**:
```
HIGH_PRIORITY: [.pptx, .pdf, .docx]  # Business critical
MEDIUM_PRIORITY: [.xlsx, .mp4]
LOW_PRIORITY: [all others]
```

Process high-priority first within batch. LLM calls batched by priority group.

### Performance Quantifications

**Rule Engine**:
- Aho-Corasick: O(n+m) for n patterns, m filename length
- For 100 patterns, 1000 files: ~10ms total
- Hash calculation (xxh128): 5GB/s per core
- SQLite manifest: 100K inserts/sec (with WAL mode)

**LLM Optimization**:
- Batch 20 files/call: 500ms for 20 files vs 10s for 20 sequential
- Cache hit rate: 80% after 1000 unique files
- Cost: $0.01 per 1000 files (Flash 2)

**Critical Path Performance**:
```
File → Rule match → Hash → DB lookup → (LLM fallback) → Move
     2ms          5ms     1ms          200ms            10ms
```

95th percentile: <50ms for rule-matched files
95th percentile: <250ms for LLM-matched files

---

## Final Architecture Specification

### 1. Core Data Structures

```python
# SQLite schema
files:
  id INTEGER PRIMARY KEY
  content_hash BLOB(16)  # xxh128
  current_path TEXT
  canonical_name TEXT
  file_type TEXT
  primary_topic TEXT
  clients TEXT[]  # JSON array
  versions JSON   # {hash_v1: path_v1, hash_v2: path_v2}
  created_at TIMESTAMP
  updated_at TIMESTAMP

routing_cache:
  filename_pattern TEXT PRIMARY KEY
  classification JSON
  hit_count INTEGER
  last_used TIMESTAMP
```

### 2. Algorithm Pseudocode

```python
def route_file(file_path):
    # Phase 1: Rule matching
    classification = rule_engine.match(file_path)
    
    # Phase 2: Hash and deduplication
    file_hash = xxh128(file_path)
    existing = db.lookup_by_hash(file_hash)
    if existing and same_location(existing, classification):
        return {"action": "skip", "reason": "duplicate"}
    
    # Phase 3: LLM fallback if low confidence
    if classification.confidence < 0.9:
        cached = db.lookup_routing_cache(file_path)
        if cached:
            classification = cached
        else:
            # Batch with other low-confidence files
            classification = llm_batch_classify([file_path])
            db.cache_routing_decision(file_path, classification)
    
    # Phase 4: Apply naming convention
    new_name = apply_naming_convention(
        original=file_path,
        classification=classification,
        hash=file_hash[:8]  # Short hash for uniqueness
    )
    
    # Phase 5: Determine destination
    dest = select_destination(classification)
    
    # Phase 6: Atomic move with version tracking
    if is_modified_version(file_hash, classification):
        archive_previous_version(classification.client)
    
    atomic_move(file_path, dest / new_name)
    db.update_file_registry(file_hash, dest / new_name)
    
    return {"action": "move", "dest": dest, "new_name": new_name}
```

### 3. Performance Guarantees

- Throughput: 1000 files/minute (rule-matched)
- Latency: <300ms P95 for any single file
- Memory: <100MB for rule engine + cache
- Storage: 1MB per 10K files in SQLite
- LLM cost: <$10 per 1M files processed

### 4. Risk Mitigation Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| LLM classification drift | Medium | High | Seed-based prompts, output validation against enum |
| Hash collision | Negligible | Critical | Add size check + first-1KB hash on collision |
| OneDrive sync conflict | High | Medium | `.lock` files + retry with exponential backoff |
| Rule explosion | High | Medium | Automatic rule compaction: merge similar patterns |
| Cache staleness | Low | Medium | TTL 30 days + LRU eviction |

---

## Bottom Line: Performance-Optimized Deterministic Router

**Agree with**: Proposal B's determinism requirement, Proposal A's hash-based tracking, Proposal C's phased approach, Proposal D's performance optimizations.

**Disagree with**: All proposals' folder structure solutions, Proposal B's anti-LLM stance, Proposal A's flat directories.

**Critical innovation**: Content-addressable storage with version chaining + multi-dimensional metadata manifest. This provides the determinism of rule-based systems with the flexibility of metadata tagging, while maintaining O(1) lookup performance for routing decisions.

**Implementation order**:
1. Build hash registry and content-addressable storage layer
2. Implement rule engine with Aho-Corasick
3. Add LLM fallback with deterministic caching
4. Execute atomic migration of legacy files
5. Add reference-counted media storage

This achieves the ADHD simplicity constraint (drop in inbox, corp handles it) while maintaining algorithmic correctness and scalability to 100K+ files.

*Latency: 94.44s | Tokens: 12344*

### Openai (gpt-5.4)

Here’s the blunt round-2 council read, optimized for shipping something Rob can actually live with.

---

# Proposal A

## Verdict
**Partially agree**

## Strongest point
**It correctly identifies that path-based identity is brittle** and that the system needs a more stable notion of file identity than raw path alone.

That is strategically right. If you ever want to reorganize safely, dedupe confidently, or repair moved-file references, you need a stable identifier: hash and/or ingest ID.

## Weakest assumption
**That you should pivot CKE to hash-primary identity now** and build “atomic migration” around it.

This is architecturally elegant, but operationally heavy. It assumes:
- you can change CKE metadata model quickly,
- you can build reliable hash/path reconciliation,
- you can batch-update vault notes safely,
- and you can do all that before restoring basic ingest discipline.

That is too much system change at once for the current maturity level. It risks turning a routing problem into a platform rewrite.

## Risks it overlooks
- **Hash identity is not a full substitute for path usability.** Humans, scripts, and Obsidian workflows still need stable canonical paths.
- **Modified files are common.** A deck updated in-place becomes a new hash; lineage handling gets messy fast if hash is the primary key.
- **Flat-folder recommendation underestimates Explorer reality.** Rob is using OneDrive/Explorer/PowerShell, not a pure metadata-driven asset system.
- **Immediate migration complexity could delay the only thing that matters now:** stable routing for new inbox files.

---

# Proposal B

## Verdict
**Partially agree**

## Strongest point
**Its insistence on determinism and operational discipline**.

This is the best corrective to “AI will magically sort my life.” The proposal is right that the filesystem is becoming a garbage sink, and the registry must be treated like production code with tests.

## Weakest assumption
**That strict rule-only routing can satisfy the stated no-manual-sorting constraint.**

It can’t. Not with:
- colleague-generated filenames,
- downloaded batches,
- Teams recordings,
- mixed client artifacts,
- and existing naming chaos.

If you reject too aggressively to `_Review`, you have just recreated manual triage under a new name. The proposal notices that but then pretends this is acceptable despite the hard constraint.

## Risks it overlooks
- **Review queue becoming permanent backlog** is more severe than acknowledged. For an ADHD operator, `_Review` is effectively a graveyard unless the unresolved rate is tiny.
- **Rule authoring burden** may exceed team capacity. Every edge case becomes a YAML/code maintenance tax.
- **No-LLM stance sacrifices too much practical recall** for messy but common files.
- **“Train users through rejection” is fantasy** in a one-person or low-governance environment. Colleagues will not reform because your local pipeline is strict.

---

# Proposal C

## Verdict
**Agree**

## Strongest point
**Best balance of technical correctness and operational pragmatism.**

It gets the sequencing right:
- route first,
- rename on ingest,
- extract only from stable locations,
- use review only for low-confidence exceptions,
- keep legacy migration separate.

That is the most shippable architecture in this set.

## Weakest assumption
**That shallow subfolders can be chosen category-by-category without creating long-term inconsistency debt.**

That can work, but only if there are very explicit rules for when folders are allowed. Otherwise “pragmatic middle ground” becomes arbitrary structure drift.

## Risks it overlooks
- **LLM fallback quality depends on available text.** For binary files with poor filenames and no extracted text, fallback may still be weak.
- **Rename-on-ingest needs collision/version rules** that are more explicit than stated.
- **Series detection can quietly sprawl** unless locked to a very short allowlist.
- **Legacy split strategy needs a freeze policy.** If legacy folders remain mutable during migration, source-path churn continues.

---

# Proposal D

## Verdict
**Partially agree**

## Strongest point
**Phased implementation mindset** and clear acknowledgment that a reorganize mode is necessary.

This is good product thinking: don’t try to solve legacy chaos only through new ingest.

## Weakest assumption
**It is over-engineered for the team and timeline.**

Aho-Corasick, Bloom filters, batched LLM calls, resolver service, file locking via `.processing` extension—this reads like infrastructure enthusiasm, not constraint-aware delivery.

For this environment, the bottleneck is not matching throughput at 10K files/sec. It is getting 95% of daily files routed correctly and safely on OneDrive without adding fragility.

## Risks it overlooks
- **OneDrive does not love clever file state transitions** like `.processing` renames during sync.
- **Metadata linking system for centralized media** may become custom-tool dependence with little user value.
- **Resolver service / hash-path indirection** adds ops burden for a single-user PowerShell-first workflow.
- **Performance optimization is solving the wrong problem.** Scale is not the immediate risk; wrong routing is.

---

# Revised Recommendation

## Executive position
Adopt **Proposal C’s core operating model**, tempered by **Proposal B’s discipline** and a **lighter version of Proposal A’s identity model**.

In plain terms:

- **Hybrid routing**: rules first, LLM fallback only for ambiguous files
- **Rename on ingest**
- **Extract only after final placement**
- **Auto-route high-confidence, quarantine low-confidence**
- **Build a separate reorganize mode**
- **Do not make hash the primary source identity in v1**
- **Do add hash + ingest ID as secondary metadata from day 1**

This is the best trade between shipping velocity, reliability, and current operational maturity.

---

# Direct answers to the council questions

## 1. Algorithm architecture
**Choose C: Hybrid**

But make it **rules-dominant**, not “AI-first with guardrails.”

### Decision logic
1. Rule match from `content_registry.yaml`
2. If confidence high enough, route
3. Else LLM classifies into constrained enums only
4. If still low confidence, send to `_Review`

### Why
- Rule-only will miss too many real files
- LLM-only is irresponsible for a routing core
- Hybrid is the only model that fits “drop in inbox, corp handles it”

### Important constraint
The LLM must **never invent destinations**. It can only populate:
- type
- topic
- client
- series
from predefined allowed values.

Destination path generation remains deterministic.

---

## 2. Naming convention enforcement
**Choose A in practice: rename on ingest**

Extraction should consume the canonical ingested name. So operationally this resembles “C,” but the source of truth is ingest.

### Reason
If you don’t rename at ingest, the filesystem remains chaotic and every downstream tool inherits ambiguity.

### Naming convention
Keep it simple enough to survive real usage:

```text
YYYY-MM-DD_CATEGORY_TOPIC_CLIENT_SHORTDESC_vN.ext
```

Examples:
- `2026-03-22_DECK_WMS_Generic_Slotting_Overview_v1.pptx`
- `2026-03-22_RFPQ_Platform_Veronesi_Integration_Questions_v1.xlsx`
- `2026-03-22_CERT_Security_Generic_ISO27001_v1.pdf`

### Rules
- preserve original filename in manifest
- sanitize for OneDrive-invalid chars
- cap total filename length
- use ingest date if document date unknown
- only add version suffix when collision or explicit version detected

Do **not** over-design naming beyond this.

---

## 3. Existing 300+ files
There is no single answer for all legacy files.

### Recommended policy
- **Already extracted files**: do **not** rename immediately unless you also update note references in the same operation
- **Not yet extracted files**: reorganize before extraction
- **New inbox files**: always canonicalize on ingest

So practically:
- **legacy extracted = controlled D**
- **legacy unextracted = batch reorganize before extraction**
- **new files = rename now**

### What not to do
Do **not** batch-rename everything blindly now. That is how you create a large, unnecessary integrity incident.

---

## 4. Folder structure
**Choose a constrained shallow-folder strategy**, not pure flat and not deep taxonomy.

### My recommendation
Use subfolders only where file counts and browse behavior justify them.

#### Good candidates for shallow subfolders
- `30_Templates/01_Decks/{product_or_multi}/`
- `50_RFP/_collected/{client}/`
- `50_RFP/Responses/{client}/`
- `60_Source_Library/01_Product_Docs/{product}/`
- `60_Source_Library/02_Training_Enablement/{series}/`

#### Keep flat
- certificates
- reference baselines
- small template libraries

### Why not fully flat
Explorer usability matters. A flat folder with 200 decks is not “clean,” it is hostile.

### Why not deep folders
Ambiguity and path length blow up fast, especially on OneDrive.

### Governance rule
If a category needs more than **one variable folder dimension**, stop and use metadata instead.

---

## 5. MP4 recordings
**Do not centralize all recordings.**

Choose **contextual placement with guardrails**, closer to Proposal C than A/D.

### Policy
- Training recordings stay with training series
- Client workshop/demo recordings stay with client/project context
- Generic orphan media goes to `40_Media/`
- Very large media collections may use a local `Media/` subfolder inside the owning context

### Why
Context matters more than media-type purity. Splitting slides and recording into separate trees hurts discovery.

### What to avoid
- symlinks: no
- global centralization by default: no
- scattering with no naming convention: also no

### Guardrails
- retention/archive rules for superseded recordings
- size reporting
- max folder depth enforcement

---

## 6. CKE integration
**Choose A now, with a path to C and metadata support from day 1.**

### v1
- Extract only from stable final locations
- Never extract from inbox
- Treat post-ingest path as canonical

### Metadata to store now
- `source_path`
- `source_hash`
- `source_ingest_id`

### Why not B as primary right now
Hash-primary identity is a good future hardening step, but not necessary to ship safe v1. Making it primary now increases implementation and migration complexity too much.

### v2
Add path repair tooling:
- `corp freshness` or `corp repair-paths`
- uses `source_hash` / `source_ingest_id` to fix moved-file references

That gives you resilience without blocking current delivery.

---

## 7. Queue processing
**Choose C: Auto + review**

This is non-negotiable.

### Default command
`corp ingest-inbox`

### Behavior
- process whole inbox batch
- auto-route high-confidence files
- send uncertain files to `00_Inbox/_Review/`
- write a log explaining why

### Important nuance
The review queue must be **small by design**. If more than ~5-10% of routine files hit review, the engine is failing product requirements.

### Therefore
Track this metric:
- `% auto-routed`
- `% reviewed`
- `% corrected after routing`

If review rate is high, improve rules/prompts before expanding scope.

---

## 8. Reorganize mode
**Yes, absolutely—but phase 2, not day-1 blocker.**

### Commands
- `corp ingest-inbox`
- `corp reorganize-library --dry-run`
- `corp reorganize-library --apply`

### Reorganize scope
- misplaced decks
- scattered MP4s
- cert supersession/archive
- absurd folder name normalization
- empty folder cleanup
- pre-extraction staging fixes
- post-extraction moves only when reference updates are bundled

### Non-negotiable
Reorganize must emit a manifest:
- original path
- new path
- reason
- hash
- whether linked note was updated

Rollback should be possible from the manifest.

---

# The architecture I would actually approve

## v1 scope: narrow and shippable
Build for the file classes that matter most and are common:

1. decks
2. recordings
3. certificates
4. RFP questionnaires/responses
5. product docs
6. known training series

Do **not** attempt universal series inference, semantic topic modeling, or full library cleanup first.

---

## v1 processing pipeline

### Step 1: Inbox scan
For each file in `00_Inbox/`:
- capture original path/name
- compute hash
- inspect extension, parent folder hints, filename tokens

### Step 2: Deterministic rule pass
Registry contains:
- file type patterns
- client aliases
- product/topic aliases
- series aliases
- route templates
- confidence weights

### Step 3: LLM fallback
Only when rules do not produce a confident result.

Inputs:
- filename
- extension
- parent folder name
- short extracted text if cheap/available

Outputs:
- enum-constrained JSON only

### Step 4: Decision
- high confidence → rename + route
- low confidence → `_Review/` with suggested metadata
- duplicate exact hash → skip and log
- same normalized name but different hash → add version suffix or review depending on category

### Step 5: Manifest
Write JSONL or CSV with:
- original_path
- original_name
- final_path
- final_name
- hash
- type
- topic
- client
- series
- confidence
- decision_source
- timestamp

### Step 6: Extraction gate
Only files outside inbox/review and inside canonical folders are eligible for CKE extraction.

---

# Specific pragmatic rules I’d enforce

## Rule 1: No extraction from unstable locations
This should be immediate policy, even before the full engine is done.

## Rule 2: Registry is code
- schema validated
- example-based tests
- every rule has sample inputs and expected outputs

## Rule 3: No open-ended folder creation
Only certain dimensions may create folders automatically:
- client under approved client-based categories
- known series
- known product buckets

No random new taxonomy because an LLM guessed a topic.

## Rule 4: Review queue is exception-only
If the queue grows, treat it as a product defect, not “user work.”

## Rule 5: Hash is secondary identity in v1
Useful for dedupe and future repair, but path remains canonical for now.

## Rule 6: Known series only
Support:
- Cognitive Friday
- Lighthouse
- cert rotation
Maybe one or two others. Stop there for v1.

---

# What I would reject from the council proposals

## I reject:
- **Pure rule-only** as the sole strategy
  - too brittle for the actual inbound mess
- **Hash-primary CKE identity in v1**
  - too much plumbing change for now
- **Fully flat filesystem**
  - nice in theory, bad in OneDrive/Explorer reality
- **Full media centralization**
  - harms contextual discoverability
- **Big-bang legacy migration**
  - too much blast radius before the ingest engine is proven
- **Performance-heavy engineering flourishes**
  - wrong optimization target

---

# Recommended rollout plan

## Phase 0: Immediate policy freeze
Starting now:
- no new extraction from `00_Inbox`
- no broad extraction from folders likely to be reorganized
- freeze ad hoc folder redesign

## Phase 1: Build stable ingest for new files
Target 1 week if disciplined:
- extend `content_registry.yaml`
- implement rule engine
- implement rename + route
- manifest logging
- duplicate detection
- `_Review` queue
- support top 6 categories only

## Phase 2: Add LLM fallback
After rule baseline works:
- constrained JSON output
- confidence threshold
- logs with model version
- only for unmatched files

## Phase 3: CKE metadata hardening
- add `source_hash`
- add `source_ingest_id`
- keep `source_path`
- extraction only from canonical paths

## Phase 4: Controlled reorganize mode
Dry-run first on:
- certificates
- training folders
- MP4 misplacements
- obvious misplaced decks
- empty directories

Then selectively apply.

---

# Final recommendation

**Approve a hybrid, rules-first inbox routing engine with rename-on-ingest, shallow constrained foldering, contextual recording placement, auto+review processing, and a separate reorganize mode.**

But be disciplined about scope:

- **Do not** rewrite CKE around hash identity before shipping ingest.
- **Do not** centralize all media.
- **Do not** flatten everything.
- **Do not** mass-migrate all legacy files in one pass.

The practical winning sequence is:

1. define canonical destinations and naming
2. route new files correctly from inbox
3. extract only after routing
4. add secondary hash identity
5. migrate legacy content in controlled slices

That is the highest-leverage path that reduces breakage now without overbuilding.

*Latency: 60.28s | Tokens: 11471*

### Grok (grok-4.20-beta)

**Council Round 2 Response — Contrarian Architect**

### Evaluation of Proposals

**Proposal A**  
**Position: Disagree.**  

Strongest point: The defense-in-depth edge sanitation and the explicit rejection of LLM path generation are correct. Treating the inbox as a hostile boundary is the only sane posture.

Weakest assumption: That we should accept the complexity of a dual-key (hash + path) system in CKE just so we can have the dopamine of a "safe atomic migration" of 300+ messy files. This is classic architect theater. You are optimizing for the cleanup of past sins instead of preventing new ones.

Overlooked risk: The transactional state-machine + manifest.json + backup ritual will become permanent theater. Every time someone wants to reorganize, Rob will have to run the full safety dance. This violates the ADHD constraint more than anything else on the table.

**Proposal B**  
**Position: Strongly agree (closest to correct).**  

Strongest point: It correctly identifies that *classification stability is the primary architectural invariant*, not cleverness. The claim that "everyone is taking for granted that classification will be stable" is the single most important observation in all four proposals. It also rightly calls out that "zero manual triage" is currently a lie.

Weakest assumption: The belief that we can leave all existing 300+ files untouched forever (Q3-C). This is too pure. Some files are *actively harmful* in their current locations (certs, MP4s in product folders, Veronesi deck in Reference_Baselines). The "radioactive" metaphor is good but inconsistently applied.

Overlooked risk: The "Inbox Hall of Shame" report, while psychologically astute, could create social friction that kills the entire system. Not every cultural problem should be solved with automated public shaming.

**Proposal C**  
**Position: Disagree.**  

Strongest point: The concrete recommendations section is the most thorough and pragmatic of the four.

Weakest assumption: That a "controlled migration" with path updates is something we should be doing at all. This proposal still treats the filesystem as the source of truth and then builds elaborate coping mechanisms. The middle-ground folder strategy ("shallow product subfolders only where they reduce operational chaos") is exactly the kind of vague hand-waving that produces the current mess.

Overlooked risk: The hybrid system becomes a permanent two-headed beast. Rules and LLM will diverge over time. The "periodically promote successful LLM decisions into deterministic rules" sounds good in a document and fails in practice.

**Proposal D**  
**Position: Disagree.**  

Strongest point: The performance note (Aho-Corasick, batched LLM calls, Bloom filters) shows actual engineering thinking.

Weakest assumption: That we should be building a hash-to-path resolver service and a metadata-based linking system for media. This is scope creep disguised as sophistication. We are not building an enterprise content management system.

Overlooked risk: The SQLite manifest + hash registry + rule engine + LLM layer creates exactly the kind of distributed state that PowerShell scripts handle poorly. This will become a maintenance nightmare.

---

### What Everyone Is Missing

The council is still taking three toxic assumptions for granted:

1. **That the current folder taxonomy is worth preserving.** It isn't. The distinction between 30_Templates, 50_RFP, 60_Source_Library, etc. made sense when this was a small personal vault. It is now getting in the way.

2. **That extraction quality depends on folder context.** This was true when we had no metadata. It becomes false the moment we have a proper manifest and hash-based identity. The dependency is historical, not fundamental.

3. **That we must solve this with an *algorithm*.** The real problem is *intake discipline*. The algorithm should be the enforcer of discipline, not a clever compensator for its absence.

---

### Revised Recommendation (My Position)

**Strict rule-based engine (1A) with aggressive rejection, content-hash identity, rename-on-ingest for new files only, and a surgical reorganize mode that *only* touches files without existing extractions.**

Specific decisions:

- **1. Architecture: A (Rule-based only).** LLM assistance is a moral hazard here. The moment you add it, you will never remove it, and classification drift will corrupt the graph. Flash is cheap until you realize the cost is *trust*, not money. Proposal B is right: this is the root of truth. It must be deterministic.

- **2. Naming: A for new files, C for existing.** New files get the strict `{YYYY-MM-DD}_{CATEGORY}_{TOPIC}_{CLIENT}_{DESCRIPTION}` format immediately. Existing files are left alone unless they have no extraction.

- **3. Existing files: Neither A, B, C, nor D.** New category: **E) Surgical correction.** Run a one-time `corp reorganize-legacy` that ONLY touches files which have no corresponding vault note. Anything with a note is frozen. This is the only position that respects both truth and safety.

- **4. Folder structure: B (Flat with naming convention) for most categories, shallow subfolders ONLY for series (Cognitive Friday, Lighthouse) and client-specific RFP material.** The "visual organization in Explorer" argument is weak. Rob lives in Obsidian and PowerShell, not Explorer. Flat + predictable names + manifest wins.

- **5. MP4 recordings: A (Centralize in 40_Media/).** Context can be maintained in the manifest and in the Obsidian graph. Scattering 85+ huge files is insane. The "context matters" argument is romantic but wrong for media.

- **6. CKE integration: B (source_hash as primary key).** This is non-negotiable. Path-based source_path was always a mistake. We should fix it. But we should *not* do mass updates on already-extracted notes. New extraction rule: you may only extract from files that have been through the distribution engine.

- **7. Queue processing: C (Auto + review), but the review bar must be high.** The rejection message must be brutally clear. The goal is to train Rob's colleagues through pain, not to achieve full automation.

- **8. Reorganize mode: Yes, but surgically constrained.** It should have three modes:
  - `--mode=safe` (only untouched files)
  - `--mode=audit` (shows everything it *would* move)
  - `--mode=nuclear` (explicitly dangerous, requires confirmation)

**Additional contrarian requirements:**

- `content_registry.yaml` must contain *examples* for every rule. No rule without its example file.
- The engine must maintain a simple `manifest.db` (SQLite) of hash → canonical metadata. This is the new source of truth.
- Any file that cannot be routed with >95% confidence goes to `_Review/` with a generated markdown explanation that Rob can forward to the person who dropped the garbage.
- No complex migration theater. We accept some permanent inconsistency in ancient files. The sunk cost fallacy is strong here.

**Bottom line:** Stop trying to build a smart system that gracefully handles organizational failure. Build a strict, boring, deterministic system that makes organizational failure painful and visible. The council keeps designing for a world where files arrive with good names and clear intent. I am designing for the world that actually exists.

*Latency: 27.12s | Tokens: 10080*

## Synthesis (by claude, non-participant)



# Decision Summary: File Distribution Algorithm — Core Routing Engine

## Consensus

The council reached strong agreement on the following points:

**1. Hybrid classification is necessary, but rules must dominate.**
All four participants agreed that pure LLM-driven routing is unacceptable for the root of truth. Three of four endorsed hybrid (C); even the contrarian who advocated rule-only (A) acknowledged that ambiguous files need *some* resolution path. The practical consensus is: deterministic rules handle 85-95% of files, with a structured fallback for the remainder.

**2. Rename on ingest is mandatory.**
Universal agreement. Files must be sanitized and canonically named the moment they leave `00_Inbox/`. No participant argued for deferred naming. The filesystem must be clean at the edge.

**3. Content hash must be tracked from day 1.**
Every participant endorsed recording content hashes, whether as primary identity (Proposals A, B-revised, D) or secondary metadata (Proposal C). The disagreement was about *primacy*, not *existence*. Hashes should be computed and stored at ingest regardless of how CKE uses them initially.

**4. Extract only from stable, post-routing locations.**
Unanimous. No extraction from `00_Inbox/`. No extraction before the distribution engine has placed and named the file. This is the single most important operational rule to enforce immediately.

**5. Auto-route with review queue (7C).**
All participants endorsed batch processing with auto-routing for high-confidence matches and quarantine for low-confidence files. No one argued for purely interactive mode as the default.

**6. A separate reorganize mode is needed.**
All agreed that legacy cleanup should not be mixed into the inbox ingest pipeline. A distinct `corp reorganize-library` command with dry-run capability was universally endorsed.

**7. LLM must never generate paths or invent taxonomy.**
Where LLM fallback is used, it must be constrained to selecting from predefined enums. Destination path computation remains fully deterministic. No participant disagreed.

**8. `content_registry.yaml` must be treated as production code.**
Rules need examples, schema validation, and testable expected outputs. The registry is infrastructure, not a convenience config.

**9. OneDrive constraints are hard.**
No symlinks. Sanitized filenames. Shallow paths. No `.processing` extension tricks during sync. These are non-negotiable platform constraints.

---

## Unresolved Disagreements

### 1. LLM fallback: include or exclude?

**For LLM fallback (Proposals A, C, D):** Real-world file names from colleagues, SharePoint batches, and Teams downloads are too chaotic for rules alone. Without LLM fallback, the `_Review/` queue becomes a permanent backlog, effectively recreating manual triage — violating the core ADHD/zero-sorting constraint. LLM cost is negligible; the real cost of *not* having it is operational stall.

**Against LLM fallback (Proposal B):** Classification stability is the primary architectural invariant. Non-deterministic output from an LLM — even at temperature=0 — can produce different classifications on different days for the same file. This poisons the knowledge graph at its root. The "review queue as backlog" fear is overstated if rules are well-written; the "LLM as crutch" reality is that once introduced, it will never be removed, and classification drift becomes invisible.

**Both sides have genuine merit.** The LLM risk is real but mitigable through caching and enum constraints. The rule-only brittleness is also real and could cause system abandonment.

### 2. Folder structure: flat vs. shallow subfolders

**For flat + naming (Proposal B):** Multi-dimensional classification doesn't map to hierarchical folders. A deck about "WMS Security for Veronesi" can only live in one folder. Flat structures with strong naming and metadata solve this cleanly.

**For shallow subfolders (Proposals C, D):** Explorer usability matters for a OneDrive/PowerShell workflow. 200+ files in one folder is hostile. Subfolders by the *primary* dimension (product for decks, client for RFPs) plus a `Multi_Product` bucket handles 90% of cases pragmatically.

**Both sides have merit.** The question turns on how Rob actually discovers files. If primarily through Obsidian/search, flat wins. If through Explorer browsing, shallow folders win.

### 3. MP4 recordings: centralize vs. distribute

**For centralization (Proposals A, B):** 85+ large files scattered across the tree is a storage management nightmare. Centralization in `40_Media/` with metadata linkage keeps the filesystem manageable.

**For contextual placement (Proposals C, E):** Context matters for discovery. Lighthouse recordings next to Lighthouse slides makes browsing intuitive. Splitting by media type harms the knowledge relationship.

**Both sides have merit.** The trade-off is between storage manageability and contextual discoverability.

### 4. Hash as primary vs. secondary identity for CKE

**For hash-primary now (Proposals A, B-revised, D):** Path-based `source_path` was always brittle. Building on a broken foundation means every future reorganization requires path-repair tooling. Fix it now while the system is young.

**For hash-secondary, path-primary now (Proposal C):** Hash-primary requires CKE metadata model changes, reconciliation tooling, and handling of modified files (common with PPTX). This is too much plumbing before the ingest engine is proven. Ship path-first, harden later.

**Both sides have merit.** The question is sequencing risk: fix the foundation now at higher upfront cost, or ship faster and retrofit later at higher cumulative cost.

### 5. Legacy file handling: freeze vs. surgical correction

**For freeze (Proposal B):** Touching already-extracted files risks breaking existing vault notes. Leave them alone and focus forward.

**For surgical correction (Proposal B-revised, C):** Some files are actively harmful in wrong locations (certs, misplaced MP4s, Veronesi deck). Ignoring them accepts permanent pollution. But only touch files that either have no extraction or where path updates are bundled.

---

## Recommended Decision

### Architecture: Hybrid, rules-dominant, with constrained LLM fallback (1C)

**Rationale:** The zero-manual-sorting constraint is hard. Rule-only routing will send too many real-world files to `_Review/`, creating a backlog that an ADHD operator will abandon. The LLM fallback is the safety net that makes the system viable — but it must be heavily constrained.

**Acknowledging the strongest objection:** Proposal B is right that classification stability is the primary invariant. This is addressed by:
- LLM outputs cached in SQLite keyed by normalized filename pattern. Identical inputs always produce identical outputs.
- LLM constrained to predefined enum values only. No novel categories.
- Temperature=0, fixed seed, structured JSON output.
- All LLM decisions logged with model version, enabling audit.
- Successful LLM patterns periodically promoted to deterministic rules.
- If cache hit rate exceeds 80% within 3 months, re-evaluate whether LLM can be removed entirely.

The contrarian concern is taken seriously: track LLM decision consistency over time and treat drift as a defect.

### Naming: Rename on ingest (2A)

**Convention:**
```
YYYY-MM-DD_CATEGORY_TOPIC_CLIENT_SHORTDESC_vN.ext
```

Original filename preserved in manifest. Ingest date used when document date is unknown (flagged in metadata). OneDrive-safe character sanitization. Total path length enforced under 220 characters.

### Existing files: Surgical correction (3E — new option)

**Policy:**
- Files with existing vault note extractions: **frozen** unless path update is bundled in the same atomic operation
- Files with no extraction: eligible for reorganize/rename before extraction
- New files: always canonicalized on ingest

**Acknowledging objections:** Proposal A/D's argument for full atomic migration is architecturally sound but operationally premature. Proposal B's total freeze is too pure — some misplacements (certs in wrong folders, MP4s in product docs) actively degrade system quality. The surgical middle path limits blast radius while addressing the worst pollution.

### Folder structure: Constrained shallow subfolders (4A-constrained)

**Specific rules:**
- **Subfolders allowed** for: decks by product, RFP by client, product docs by product, training by series
- **Flat** for: certificates, reference baselines, small template sets, competitive materials (unless count exceeds ~30)
- **`Multi_Product/` bucket** for cross-product items
- **Governance rule:** No more than one variable dimension per category. If a category needs two folder dimensions, use flat + metadata.

**Acknowledging objection:** Proposal B is right that this creates some classification ambiguity. But Explorer/OneDrive usability is a daily friction point, and 200+ files in a flat folder genuinely hurts discoverability. The `Multi_Product` bucket is imperfect but bounded.

### MP4 recordings: Contextual with guardrails (5B-guarded)

**Policy:**
- Training series recordings stay with their series
- Client/project recordings stay with client context
- Orphan/generic media goes to `40_Media/`
- Size reporting and retention rules enforced
- Superseded recordings archived, not deleted

**Acknowledging objection:** Proposal B's centralization argument is strong for storage management. However, in a OneDrive-synced environment without symlinks, separating recordings from their slides destroys the browsing workflow. Metadata linking (Proposal D) adds custom tooling complexity that doesn't pay off at this scale. Contextual placement with naming discipline and size monitoring is the pragmatic choice.

### CKE integration: Path-primary now, hash-secondary from day 1, hash-upgrade path planned (6A+B-secondary)

**v1:** Extract only from stable post-routing locations. `source_path` is canonical.

**From day 1:** Also store `source_hash` and `source_ingest_id` in extraction metadata.

**v2:** Build `corp repair-paths` that uses hash/ingest_id to fix moved-file references.

**Acknowledging objection:** Proposals A, B-revised, and D are architecturally correct that hash should be primary. But making hash primary *now* requires CKE metadata model changes, a hash reconciliation layer, and modified-file handling (common for PPTX). This delays shipping the ingest engine. Storing hashes from day 1 preserves the upgrade path without blocking delivery. The risk of path breakage during the interim is mitigated by the "extract only from stable locations" rule plus the freeze on already-extracted files.

### Queue processing: Auto + review (7C)

- `corp ingest-inbox` processes all files in batch
- High-confidence: auto-route
- Low-confidence: quarantine to `00_Inbox/_Review/` with suggested classification and clear rejection reason
- Review queue rate tracked as a system health metric: target <5% of routine files
- If review rate exceeds 10%, treat as a product defect in rules/prompts

### Reorganize mode: Yes, phase 2 (8: Yes)

Two separate commands:
- `corp ingest-inbox` — new files only
- `corp reorganize-library --dry-run` / `--apply`

Reorganize constrained to:
- files without existing extractions (safe mode)
- audit mode for all files (proposes, doesn't execute)
- full mode only with explicit confirmation + backup requirement

---

## Risks

### Risk 1: LLM classification drift corrupts the knowledge graph
**Probability:** Medium | **Impact:** High
**Mitigation:** Cache all LLM decisions in SQLite. Same normalized input → same cached output. Log model version. Constrain to enum outputs. Monitor consistency metrics. Promote stable patterns to deterministic rules quarterly. If drift is detected, invalidate cache and re-classify with updated rules.

### Risk 2: Review queue becomes a permanent backlog
**Probability:** Medium | **Impact:** High (system abandonment)
**Mitigation:** Track review rate weekly. Target <5%. If rate climbs, add rules or adjust confidence threshold before expanding scope. Make rejection messages actionable with suggested filenames. Consider nightly auto-suggestion of new rules from review queue patterns.

### Risk 3: Legacy migration breaks existing vault notes
**Probability:** Medium | **Impact:** High
**Mitigation:** Surgical approach: only touch files without extractions. For files with extractions, require bundled path update in same operation. Mandatory dry-run. Manifest logging with rollback capability. Vault backup before any reorganize apply.

### Risk 4: OneDrive sync conflicts during batch operations
**Probability:** High | **Impact:** Medium
**Mitigation:** No extension renaming tricks (`.processing`). Use NTFS-atomic renames. Batch during low-activity periods. Verify sync status after operations. Keep total path length under 220 characters.

### Risk 5: Rule explosion in content_registry.yaml
**Probability:** Medium | **Impact:** Medium
**Mitigation:** Enforce schema validation. Every rule requires example file + expected destination. Regular rule count audit. Merge overlapping patterns. Limit initial scope to top 6 file categories.

### Risk 6: Multi-product files create permanent classification ambiguity
**Probability:** High | **Impact:** Low
**Mitigation:** `Multi_Product` bucket exists. Primary topic assignment is acceptable imperfection. Metadata manifest captures all topics. Obsidian queries surface files across topic boundaries regardless of physical location.

### Risk 7: Modified files (updated PPTX) break hash-based dedup/linkage
**Probability:** High | **Impact:** Medium
**Mitigation:** v1 uses hash only for dedup and secondary tracking, not primary identity. Version detection in naming convention handles updates. v2 hash upgrade should implement version chaining (new hash links to parent hash).

---

## Action Items

### Phase 0: Immediate Policy (Today)
1. **Freeze extraction from unstable locations.** No new CKE extraction from `00_Inbox/` or folders likely to be reorganized.
2. **Freeze ad hoc folder restructuring.** No manual folder moves until the engine is operational.
3. **Document the naming convention** in a project-level README: `YYYY-MM-DD_CATEGORY_TOPIC_CLIENT_SHORTDESC_vN.ext`

### Phase 1: Core Ingest Engine (Target: 1 week)
4. **Extend `content_registry.yaml`** with missing destinations (decks, demo scripts, discovery tools, executive summaries, RFP questionnaires/responses, brand guidelines, media, admin docs, master deck updates). Add example files and expected routes for every rule.
5. **Implement the rule engine** in PowerShell: extension matching, filename regex, parent folder hints, client/product/series dictionaries, confidence scoring.
6. **Implement rename-on-ingest** with sanitization (OneDrive-safe characters, path length cap, date extraction/fallback).
7. **Implement hash computation** (xxh128 or SHA-256) at ingest, stored in SQLite manifest alongside original name, final name, route, confidence, decision source, timestamp.
8. **Implement duplicate detection** by hash lookup.
9. **Implement `_Review/` quarantine** with machine-generated explanation files.
10. **Build `corp ingest-inbox` command** that executes the full pipeline.
11. **Test with 20-30 representative files** from known categories before going live.

### Phase 2: LLM Fallback (Target: +3-5 days after Phase 1 baseline)
12. **Implement LLM fallback** for files below confidence threshold. Use Flash. Constrain output to strict JSON with predefined enums. Cache decisions in SQLite.
13. **Add confidence and routing metrics** to manifest: track auto-route rate vs. review rate.
14. **Validate** that review rate is <10% on a representative batch.

### Phase 3: Legacy Surgical Cleanup (Target: +1 week after Phase 2)
15. **Build `corp reorganize-library --dry-run`** that scans existing folders, identifies misplacements, and proposes moves.
16. **Inventory which legacy files have existing vault note extractions.** These are frozen unless path updates are bundled.
17. **Execute surgical reorganization** of unextracted files: certificates, misplaced MP4s, absurd folder names, empty folders, obvious misplaced decks.
18. **Route unextracted legacy files** through the ingest engine for canonical naming.

### Phase 4: CKE Integration Hardening (Target: +1 week after Phase 3)
19. **Add `source_hash` and `source_ingest_id`** to CKE extraction metadata template.
20. **Modify extraction pipeline** to read from manifest and include hash metadata.
21. **Begin extraction** of newly-routed files from stable canonical locations.
22. **Build `corp repair-paths`** prototype that uses hash/ingest_id to detect and fix moved-file references.

### Ongoing
23. **Weekly review rate check.** If >5%, improve rules before expanding scope.
24. **Monthly rule audit.** Promote cached LLM patterns to deterministic rules. Remove unused rules. Validate examples still pass.
25. **Quarterly reorganize pass** for newly accumulated misplacements.
