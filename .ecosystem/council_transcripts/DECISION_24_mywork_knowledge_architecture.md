# AI Council Debate: # AI Council Debate #24 — MyWork Knowledge Architecture

**Repo:** `C:\Users\102

**Date:** 2026-03-29 21:06:47
**Panel:** deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta, gpt-5.4
**Synthesizer:** claude (non-participant)
**Rounds:** 2
**Duration:** 355.9s
**Panel Mode:** full (4-model panel)
**Debate Mode:** pick
**Source:** council_inbox\PROMPT_council24_mywork_architecture.md
**Cost:** ~$0.4920 (90,064 tokens)

---

## Round 1: Initial Responses

### Gemini (gemini-3.1-pro-preview)

## Position
Realign the MyWork architecture into strictly bounded zones based on access frequency and system isolation, establishing folders as state-based physical boundaries and tags as logical discovery vectors. 

## Alternatives Considered
- **Alt 1: Domain/Topic-Mapped Root Folders.** Categorizing root folders by the 11 tag dimensions (e.g., `Products`, `Clients`, `Compliance`). Rejected because it violates the access frequency constraint, increases cognitive load for the ADHD user, and massively increases the blast radius if the classification pipeline miscategorizes a file.
- **Alt 2: Flat "Dump" Structure with Pure Tagging.** Placing everything into a single workspace folder and relying entirely on Obsidian/tags for navigation. Rejected because raw client files (PPTX/XLSX) are not renamed and require OS-level spatial grouping; additionally, mixing system config with untrusted client files creates an unacceptable security and operational risk.

## Decision Criteria
1. **Blast Radius & System Isolation:** Preventing user error or untrusted client files from interfering with pipeline configuration and execution.
2. **Access Frequency / Cognitive Friction:** Optimizing physical paths for an ADHD/autistic user requiring zero-friction access to daily tools.
3. **Pipeline Predictability:** Eliminating the 3-way configuration mismatch to establish a single source of truth.
4. **Primary vs. Secondary Navigation:** Strictly separating Access State (folders) from Knowledge Dimensions (tags).

## Assumptions
1. The 53% MISC classification rate is heavily skewed by the 16 missing client aliases in `naming_config.yaml`, and updating this config will correct the routing without requiring architectural changes to the classifier.
2. The Corporate OS pipeline executes with OS-level permissions capable of reading/writing to hidden directories (e.g., `.corp`).
3. The RFP LLM agent requires read-only access to historical reference data and does not need to write back to the reference library during normal operation.

## Recommendation
**What to do now:**
- Define the canonical top-level structure in `folder_names.py` and `routing_map.yaml`:
  - `00_Inbox` (Ingestion & quarantine pipeline boundary).
  - `10_Projects` (Active client work; isolated subfolders per client).
  - `20_Daily` (High-frequency hot zone: master decks, demo scripts, templates).
  - `30_Reference` (Evergreen, read-only cold zone: product docs, competitor data).
    - `30_Reference/RFP_Library` (Past answers sorted by format for the RFP agent).
  - `70_Admin` (Corporate/HR files).
  - `80_Archive` (Completed/stale projects).
  - `.corp` (Hidden directory containing `routing_map.yaml`, `Project_Codes.xlsm`, and pipeline infra).
- Execute a one-time migration to move the 8 stale projects from `10_Projects` to `80_Archive`.
- Map the 16 missing clients in `naming_config.yaml` to ensure the router can place files into the correct `10_Projects` subfolders.

**What not to do now:**
- Do not enforce the v2 naming convention on raw client documents (this preserves forensic integrity of the client-provided source files).
- Do not create or retain empty structural placeholders (`40_Media`, `50_RFP`, `60_Source_Library`, `80_Compliance`, `90_System`).
- Do not create nested directories inside `20_Daily`.

**What to defer until later:**
- OneDrive synchronization patterns and exclusions.
- Automated cron-based archiving of projects (manual archive is sufficient while establishing the new baseline).

## Rationale
- **Infrastructure Isolation (Blast Radius):** Moving pipeline configuration (`90_System`) into a hidden `.corp` directory isolates the routing infrastructure from user space. If the user accidentally deletes or moves files during daily operations, the pipeline configuration remains intact, preventing a 100% routing failure.
- **State-Based vs. Semantic Grouping:** Physical folders dictate *Access State* (Ingestion, Active, Daily, Cold, Archived). The 11 extraction dimensions (Product, Domain, Topic, etc.) dictate *Content Semantics* via tags. This guarantees that if the semantic classifier fails, the file still lands in the correct security/state boundary (e.g., `10_Projects/ClientName`).
- **RFP Agent Dependency Management:** By moving RFP reference material into `30_Reference/RFP_Library`, we treat it as an immutable dependency for the LLM agent. Active RFP responses stay in `10_Projects/{client}`. This maintains a strict trust boundary between validated historical answers and unverified, in-flight work.
- **Cognitive Optimization:** Flattening master decks and demo scripts into a top-level `20_Daily` folder guarantees O(1) retrieval complexity for the user's highest-value assets, directly addressing the ADHD friction requirement.
- **Archive Segregation:** 32% of current projects are stale (8 out of 25). Moving these to `80_Archive` minimizes the `10_Projects` directory footprint, reducing search space and index bloat for local pipeline operations.

## Trade-offs
- By flattening daily materials into `20_Daily`, you sacrifice structural categorization for speed. If this folder exceeds ~50 files, visual scanning will degrade, shifting the cognitive load from "navigation" to "search".
- Archiving projects physically breaks absolute file paths. Any local Excel or PowerPoint files in `10_Projects` that statically link to files in other projects will break when moved to `80_Archive`.

## Risks
- **Risk:** Hardcoded paths in external scripts or integrations still expect `90_System`, `50_RFP`, or `60_Source_Library`, causing pipeline crashes upon deployment.
  - *Likelihood:* High. *Impact:* High (Pipeline outage).
  - *Mitigation:* Implement symlinks from the old folder names to the new locations for a 14-day deprecation window, while updating the external scripts.
- **Risk:** The "Clicks_Retail" outlier (77% of project files) creates an unmanageable subdirectory within `10_Projects`, degrading performance or navigation.
  - *Likelihood:* Certain. *Impact:* Medium.
  - *Mitigation:* Treat project subfolders as opaque to the top-level structure rules. The user may nest folders inside `10_Projects/Clicks_Retail` as needed; the pipeline must blindly route to the root of the client folder and rely on the Obsidian vault for deep extraction.

## Signals to Revisit
- The classification pipeline's MISC rate remains >20% even after the 16 missing client aliases are added to the configuration.
- The `20_Daily` folder exceeds 50 items, indicating it is being used as a dump rather than a curated hot-zone.
- The RFP LLM agent requires write access to update its own knowledge base, which would require splitting `30_Reference/RFP_Library` into isolated read/write directories to maintain trust boundaries.

*Latency: 35.97s | Tokens: 5912*

### Deepseek (deepseek-reasoner)

## Position
Adopt a 5-folder structure organized by access frequency, with daily tools at the root and nested archives for stale content. This resolves the configuration mismatch while prioritizing zero-friction access for high-ADHD workflow.

## Alternatives Considered
1. **Keep existing 3-zone structure (Projects/Workflows/Reference)** — Rejected because it doesn’t address the RFP library need or clean up the system/admin confusion, leaving the pipeline mismatch unresolved.
2. **Create separate folders for each taxonomy dimension** — Rejected because it would create >10 top-level folders, increase cognitive load, and violate the “flat hot-zone” principle for daily files.

## Decision Criteria
1. **Access frequency alignment** — Daily-use files must be reachable in ≤1 click.
2. **Pipeline-consistency** — All folders in `folder_names.py` must exist on disk.
3. **Cognitive load minimization** — ≤8 top-level folders; avoid “someday” folders.
4. **Archive/stale handling** — Clear mechanism to move cold projects out of active view.
5. **RFP agent usability** — Past answers organized by format, not buried in client folders.

## Assumptions
1. Rob’s daily tools (master deck, demo scripts) are used across multiple clients, justifying a shared top-level folder.
2. The pipeline can classify files into the new structure with ≥85% accuracy after fixing client aliases.
3. Stale projects (>90 days inactive) can be moved automatically without breaking references.

## Recommendation
**What to do now:**
1. Update `folder_names.py` to exactly these 5 folders:
   - `00_Inbox` (temporary landing)
   - `10_Active` (active client projects, ≤90 days)
   - `20_Tools` (master deck, demo scripts, presentation templates – flat, no subfolders)
   - `30_Knowledge` (evergreen reference + RFP library with subfolders `by_format/` and `by_topic/`)
   - `90_Archive` (stale projects, compliance, admin – subfolders: `projects/`, `compliance/`, `admin/`)
2. Delete empty/dead folders (`40_Media`, `80_Compliance` from disk).
3. Move pipeline config files from `90_System` into a hidden `.corp/` subfolder within `90_Archive`.

**What not to do now:**
- Do not create separate folders for Sales/Services departments.
- Do not implement deep nesting within `20_Tools` (keep it flat).
- Do not change the v2 naming convention or taxonomy dimensions.

**What to defer until later:**
- Subfolder taxonomy within `30_Knowledge/by_topic/` (can evolve organically).
- Automated OneDrive sync pattern (separate scope).

## Rationale
- **Reduces MISC rate from 53% to <15%** by eliminating missing folders and adding client aliases for all 25 known clients.
- **Meets zero-friction requirement** – daily tools are at `MyWork/20_Tools/` (one click from root), no deeper than `MyWork/10_Active/{client}/` for active projects.
- **Cleans up system mess** – pipeline config hidden in `.corp/`, user-facing reference files moved to `30_Knowledge`.
- **Solves RFP library need** – past answers in `30_Knowledge/by_format/{excel,word,pptx}/` accessible to RFP agent, active responses remain in `10_Active/{client}/`.
- **Prevents future staleness** – automatic move of projects >90 days inactive to `90_Archive/projects/` keeps `10_Active` lean (~12 clients at any time).

## Trade-offs
- **Loss of granularity** – Admin, compliance, and archived projects are grouped under one `90_Archive` folder, requiring one extra click to reach.
- **Increased file moves** – ~8 stale projects (32% of current projects) will be relocated during migration.
- **Tool sprawl risk** – `20_Tools` could become a dumping ground; must enforce “flat and curated” discipline.

## Risks
1. **Pipeline classification accuracy drops** if client aliases aren’t updated for all 16 missing clients (likelihood: medium, impact: medium). Mitigation: Add aliases as a prerequisite step.
2. **Daily tools become disorganized** if `20_Tools` isn’t kept flat (likelihood: high, impact: low). Mitigation: Weekly cleanup script that flags new subfolders.
3. **Archive fragmentation** if projects in `90_Archive/projects/` are still referenced by active symlinks (likelihood: low, impact: high). Mitigation: Use junction points on Windows, not copies.

## Signals to Revisit
- MISC classification rate remains >20% after two pipeline runs.
- Rob reports >2 clicks to access daily tools more than once per week.
- `20_Tools` contains >50 files, indicating need for subcategorization.
- RFP agent cannot find past answers due to format-based organization (track success rate on RFP tasks).

*Latency: 115.31s | Tokens: 6580*

### Openai (gpt-5.4)

## Position
Adopt a 7-folder, access-frequency-first structure centered on `10_Projects`, `20_Workflows`, and `30_Reference`, with RFP reference material embedded inside `30_Reference` and pipeline internals hidden under `90_System\.corp`. This is the smallest realistic change that fixes the routing mismatch, matches Rob’s actual behavior, and can be implemented by one team without creating another overengineered taxonomy.

## Alternatives Considered
1. **Reinstate the code-defined structure (`30_Templates`, `50_RFP`, `60_Source_Library`, `80_Archive`) as separate top-level folders.**  
   Rejected because it preserves a conceptual model Rob already said is wrong: it separates daily-use artifacts from their working context, duplicates `30_Reference`/`60_Source_Library`, and adds cognitive overhead for a user who needs zero-friction retrieval.

2. **Go fully flat with only Inbox / Projects / Reference / System and push everything else into tags.**  
   Rejected because it is too coarse for actual operations: Rob explicitly distinguishes reusable daily tools from evergreen reference, admin from work content, and active projects from stale ones. A 4-folder model would reduce routing precision and make manual browsing worse.

## Decision Criteria
1. **Fit to Rob’s real access patterns**: daily-use content must be reachable in 1-2 clicks; infrequent content can be deeper.
2. **Implementation realism**: must be codable in `folder_names.py`, routable, and maintainable without a major migration program.
3. **Reduction of classification/routing failure**: current 53% MISC rate is unacceptable; structure must eliminate spec/disk mismatch.
4. **Low cognitive load**: no speculative folders, no duplicate concepts, no more than 10 top-level folders.
5. **Operational clarity**: user-facing content must be separated from pipeline internals; stale project handling must be explicit.

## Assumptions
1. Rob primarily browses by **work context first** (active client, reusable asset, evergreen knowledge), not by metadata dimension alone.
2. The pipeline can support a small number of deterministic routing changes without a full classifier redesign.
3. `20_Workflows` currently represents genuinely reusable working assets/process artifacts, not just misc overflow.
4. Archive can be implemented as a substructure under projects rather than requiring a top-level `80_Archive`.

## Recommendation
**What to do now**
- Standardize on these canonical top-level folders in `folder_names.py`:
  - `00_Inbox` — temporary intake, should usually be near-empty
  - `10_Projects` — active and client-specific opportunity work
  - `20_Workflows` — high-frequency reusable working assets Rob uses to execute presales work
  - `30_Reference` — evergreen source library and knowledge hub
  - `70_Admin` — personal corporate admin
  - `80_Compliance` — security/compliance artifacts that need controlled separation
  - `90_System` — machine-facing/system support files only; pipeline internals under `90_System\.corp\`
- Define `10_Projects` structure as:
  - `10_Projects\Active\{Client}\`
  - `10_Projects\Stale\{Client}\`
  - `10_Projects\Archive\{Client}\`
- Define `20_Workflows` as a **shallow hot zone** for daily-use assets:
  - examples: master decks, demo scripts, standard technical presentations, workshop kits, frequently reused calculators
  - keep depth to max 2 levels below top
- Define `30_Reference` as the evergreen hub, with moderate nesting by primary browse axis:
  - `30_Reference\Products\`
  - `30_Reference\Architecture\`
  - `30_Reference\Competition\`
  - `30_Reference\Branding\`
  - `30_Reference\RFP_Library\Excel\`
  - `30_Reference\RFP_Library\Word\`
  - `30_Reference\RFP_Library\PowerPoint\`
  - `30_Reference\Compliance\` only if needed for reusable reference copies; controlled originals remain in `80_Compliance`
- Update router/classifier so `30_Reference` replaces `60_Source_Library`, and `50_RFP` is removed as a top-level destination.

**What not to do now**
- Do not create separate top-level folders for `Templates`, `RFP`, `Source_Library`, or `Archive`.
- Do not preserve `40_Media`; remove it from spec.
- Do not mix `Project_Codes.xlsm`, `solution_matrix`, or similar pipeline support assets with user-browsed reference files in visible `90_System` root.
- Do not try to map all 11 taxonomy dimensions to folders.

**What to defer until later**
- Alias cleanup for the 16 clients missing in `naming_config.yaml`.
- Any automated stale-project lifecycle policy beyond simple date-based movement.
- Fine-grained subfolder tuning inside `30_Reference` based on 60-90 days of actual access telemetry.
- OneDrive/original-vs-local sync policy.

## Rationale
- **This fixes the current failure mode with minimal moving parts.** Today 4 canonical folders do not exist on disk and 3 real folders are absent from code, directly contributing to a 53% MISC rate. Aligning code, routing, and disk around the existing successful concepts is the fastest path to a meaningful drop in routing errors.
- **Rob’s stated daily-use pattern argues for `20_Workflows` as a hot zone, not `30_Templates`.** “Master deck, technical presentations, demo scripts” are not passive templates; they are operational tools. Renaming them as templates encourages burying them. Keeping them in a shallow workflow zone better matches actual retrieval behavior.
- **`30_Reference` already has user legitimacy and should absorb “source library” and RFP reference.** Rob explicitly said `30_Reference` “IS my source library.” Creating `60_Source_Library` in parallel would duplicate concepts and increase browse time. Embedding `RFP_Library` inside reference matches the stated need: active responses stay with projects, reusable past answers live in evergreen knowledge.
- **Archive should be a project lifecycle state, not a top-level concept.** With only 25 projects total and 9 active, a separate top-level archive adds one more root choice for little benefit. `Active / Stale / Archive` under `10_Projects` gives enough operational control without fragmenting navigation.
- **Separation of user files and machine files is essential for maintainability.** `90_System` is currently polluted with both pipeline config and human reference materials. Moving internals to `90_System\.corp\` reduces accidental browsing noise and lowers the chance of users manually editing operational files.

## Trade-offs
- You give up a **clean top-level separation of RFP content**; some teams prefer a dedicated `50_RFP`. Cost: slightly less obvious visibility for RFP as a domain, but lower duplication and better consistency with project/reference split.
- You give up a **purely taxonomy-driven folder model**. Some metadata dimensions will only exist as tags, not folders. Cost: certain niche browse paths require search or Obsidian rather than manual file navigation.
- You accept a **7-folder root instead of an even smaller 4-5 folder root**. Cost: a bit more top-level complexity, but still under the 10-folder cap and materially better operational fit.
- You keep **both `80_Compliance` and compliance tags**, which creates some conceptual overlap. Cost: users must understand that folders represent handling sensitivity, while tags represent knowledge classification.

## Risks
- **Risk: `20_Workflows` becomes a junk drawer.**  
  Likelihood: Medium. Impact: High.  
  Mitigation: define admission criteria now—only high-frequency reusable execution assets belong there; client-specific material stays in projects; evergreen background knowledge goes to reference.

- **Risk: Ambiguity between `30_Reference\Compliance` and `80_Compliance`.**  
  Likelihood: Medium. Impact: Medium.  
  Mitigation: document a strict rule: `80_Compliance` holds controlled/sensitive/official artifacts; `30_Reference` may hold sanitized reusable reference copies only if needed.

- **Risk: MISC rate remains high even after folder alignment because alias coverage is weak.**  
  Likelihood: High. Impact: High.  
  Mitigation: treat folder restructuring and alias cleanup as separate workstreams; expect a meaningful but incomplete improvement from structure alone. Prioritize adding aliases for the 16 missing clients immediately after ADR acceptance.

- **Risk: Project lifecycle folders (`Active/Stale/Archive`) require manual upkeep and are ignored.**  
  Likelihood: Medium. Impact: Medium.  
  Mitigation: use a simple rule such as “no file activity in 90 days → Stale; closed opportunity or >180 days inactive → Archive,” and automate movement later if needed.

- **Risk: Existing links or scripts assume old top-level names.**  
  Likelihood: Medium. Impact: Medium.  
  Mitigation: update `folder_names.py` as the source of truth first, then router map, then any path-dependent scripts; avoid partial rollout.

## Signals to Revisit
- Rob reports that he still cannot reach daily assets in 1-2 clicks, especially decks/demo content.
- `20_Workflows` exceeds manageable breadth, e.g. >150 files with frequent “where does this go?” confusion.
- `30_Reference\RFP_Library` grows large enough that format-only organization is no longer sufficient, e.g. repeated search failures or >300 artifacts.
- MISC classification remains above ~20% after folder alignment and alias remediation, indicating the issue is classifier logic rather than structure.
- Compliance or governance requirements tighten enough that RFP/security content needs stricter physical segregation than this model provides.

*Latency: 39.25s | Tokens: 4369*

### Grok (grok-4.20-beta)

## Position
Implement a strict access-frequency structure with exactly six visible top-level folders (00_Inbox, 10_Projects, 20_Reference, 30_Admin, 40_Compliance, 50_Archive) plus a hidden .corp/ dotfolder for all pipeline infrastructure. 20_Reference becomes the daily zero-friction hub containing master decks, technical presentations, demo scripts, product docs, competitive materials, and RFP past answers organized by format; this overrides both the existing code/yaml/disk mismatch and Council #9’s 3-zone model because both assume organizational or theoretical categories instead of Rob’s actual reach-for-file behavior.

## Alternatives Considered
**Council #9 3-zone (Projects/Workflows/Reference + Compliance):** Rejected because it forces an artificial Workflows folder Rob never mentioned, buries daily master materials three levels deep in Reference, and keeps system files visible—directly contradicting his ADHD-driven need for immediate access and his explicit statement that 30_Reference *is* the source library.

**Current actual disk structure (20_Workflows, 30_Reference, 80_Compliance, 90_System):** Rejected because it retains an empty 40_Media folder, mixes pipeline config with reference files (creating the exact mess Rob called out), and still produces 53% MISC rate by not matching the classification code; it optimizes for “might be useful” folders rather than measured access frequency (77% of project files in one client, daily master decks).

## Decision Criteria
- Zero-friction access for daily-used files (master decks, presentations, demos)
- Cognitive load limit (maximum 7 visible top-level folders)
- Elimination of the 53% MISC classification rate by aligning folder_names.py, routing_map.yaml, and disk
- Strict separation of pipeline/system files from user-facing content
- Structure depth must reflect access frequency tiers (daily/weekly at top level, monthly+ nested or archived)

## Assumptions
- Rob’s self-reported daily/weekly vs. rarely-used distinction is accurate and stable; if his actual access patterns differ materially, the frequency tiers collapse.
- The Obsidian vault + 11 tag dimensions can handle secondary discovery, so physical folders only need to support primary reach behavior.
- Numbered prefixes (00_, 10_, 20_) remain the dominant Explorer sorting method; if Rob switches to search-first navigation, the numbering scheme loses its value.
- Pipeline classification accuracy will improve rather than degrade when the target folder set shrinks from 9 to 6 visible folders.

## Recommendation
**What to do now:**  
Update `folder_names.py` to declare exactly the six folders plus `.corp`. Revise `routing_map.yaml` to send daily master materials, product docs, competitive content, and past RFP answers (by format) to `20_Reference`, admin files to `30_Admin`, compliance to `40_Compliance`, and any file >90 days old or project status “completed” to `50_Archive`. Move existing pipeline config, Project_Codes.xlsm, solution_matrix, and all 90_System content into `.corp/`. Run a one-time migration script against the current 6.6 GB to relocate the 8 stale projects and misclassified reference files. Update classifier rules to treat `20_Reference` as the default “evergreen” bucket instead of MISC.

**What not to do now:**  
Do not create separate folders for Templates, Source_Library, RFP, Workflows, or Media. Do not add subfolders under 20_Reference beyond one level for RFP formats. Do not map any of the 11 taxonomy dimensions to top-level physical folders. Do not touch OneDrive sync logic.

**What to defer until later:**  
Detailed subfolder taxonomy inside 20_Reference, automated archive policy based on last-access metadata, and any vault-level MOC changes. Revisit only after 30-day MISC rate and access telemetry are measured.

## Rationale
- Daily master decks/presentations currently require 3+ clicks; placing them at 20_Reference root reduces this to 1 click for the 462 most-accessed files (77% of project-related volume).
- Merging Source_Library and RFP reference into 20_Reference eliminates the four canonical folders that do not exist on disk, directly targeting the 53% MISC rate.
- .corp/ dotfolder hides ~15-20% of current 90_System content (config, scripts, Project_Codes.xlsm) without changing Rob’s Explorer view, solving the “messy 90_System” complaint.
- Moving 8 stale projects (>90 days) out of 10_Projects keeps the active set at ~9 folders instead of 25, preventing visual noise that disproportionately affects ADHD users.
- Limiting to 6 visible folders meets the explicit “no more than 10” constraint while still covering 100% of Rob’s described workflow categories.

## Trade-offs
- Lose visual separation for Templates and pure RFP responses (now live inside 20_Reference or its single-level subfolders), adding ~10-15 seconds of in-folder search time for ~5% of files.
- Sacrifice theoretical purity of Council #9’s 3-zone model for actual observed behavior, making future org-chart-driven requests harder to accommodate.
- Archive folder requires periodic manual or scripted moves instead of fully automatic routing (estimated 2 hours per quarter).

## Risks
- **Reference becomes a dumping ground** (likelihood 45%, impact high): 20_Reference grows beyond 300 files and loses its “daily hub” character. Mitigate with explicit subfolder conventions for RFP formats and a quarterly 15-minute cleanup rule enforced in pipeline.
- **Classification accuracy drops after rule changes** (likelihood 25%, impact medium): MISC rate temporarily rises above 53%. Mitigate by running the existing audit set through the new router before committing and adding 10 golden test cases.
- **Rob ignores the new structure** (likelihood 20%, impact high): Continues saving directly to OneDrive or desktop. Mitigate by having him sign off on the exact folder purposes in the ADR and adding a simple desktop shortcut to 20_Reference.

## Signals to Revisit
- MISC classification rate fails to drop below 25% after 30 days of production use.
- Rob reports spending >3 minutes per week “hunting” for master decks or RFP answers (measured via self-report or folder access logs).
- File count in 20_Reference exceeds 350 without subfolder usage.
- New telemetry shows daily access patterns have shifted (e.g., certain reference subcategories now used more than projects).
- Rob’s role changes such that compliance or admin files become daily drivers.

*Latency: 31.03s | Tokens: 7829*

## Round 2: Critique

### Gemini (gemini-3.1-pro-preview)

As a Security & Integration Architect, my evaluation of any folder structure rests on its function as a series of **trust boundaries, state boundaries, and blast zones**. When the Corporate OS pipeline or the RFP LLM agent interacts with these directories, the physical structure dictates what gets executed, what gets ingested, and what gets overwritten. 

Mixing pipeline configuration with user reference files (`90_System`'s current state) is a catastrophic failure of system isolation. Relying on a semantic classifier to route execution-critical daily tools is an unacceptable routing risk. 

Here is my architectural evaluation of the proposals.

---

### Proposal A
**Steelman first:** Rob conceptually separates his active execution tools ("workflows") from his evergreen knowledge ("reference"). Allowing him a dedicated, shallow hot-zone (`20_Workflows`) while cleanly separating pipeline internals (`90_System\.corp`) perfectly balances his cognitive needs with operational stability and minimizes the need for an entirely new paradigm.

**Your assessment:** Partially agree. I agree with separating daily workflows from reference material, but keeping `90_System` visible *just* to hold a hidden `.corp` folder is a dangerous half-measure. It leaves an attractive nuisance for the user to drop files into, which the pipeline might attempt to execute or classify.

**Strongest point:** Explicitly calling out the missing client aliases as a separate execution dependency from the folder restructure. Structural changes won't fix a 53% MISC rate if the classifier literally doesn't know the client names.

**Weakest assumption:** Assuming users won't put arbitrary files in `90_System` if it is left as a visible root folder, thus re-polluting the pipeline's blast radius.

**Hidden assumptions:** Assumes the pipeline can reliably distinguish between a "Workflow" (an execution asset) and a "Reference" (an evergreen asset) using purely semantic LLM classification, which is a highly subjective boundary.

**Overlooked risks:** Pipeline execution permissions. If the pipeline runs on `20_Workflows` and `30_Reference` identically without strict write-protections on evergreen content, a rogue classifier bug could overwrite or misroute critical daily tools into the cold zone.

---

### Proposal B
**Steelman first:** If we treat directories as strict security and trust boundaries, hiding pipeline config in a root `.corp` and isolating the RFP LLM agent to a read-only `30_Reference/RFP_Library` provides maximum defense-in-depth against both pipeline bugs and LLM hallucinations.

**Your assessment:** Agree. This is the most architecturally sound proposal. By defining folders as "Access State" (trust/physical boundaries) and tags as "Content Semantics" (logical vectors), it prevents semantic classifier failures from breaking security and workflow boundaries. 

**Strongest point:** Treating the `RFP_Library` as an immutable dependency for the LLM agent while keeping in-flight RFP responses quarantined in `10_Projects`. This prevents unverified data from poisoning the LLM's context window.

**Weakest assumption:** Assumes the classifier can blindly route files to `10_Projects/Clicks_Retail` without needing to parse or understand the massive, unmanaged subdirectory structure that holds 77% of the project files.

**Hidden assumptions:** Assumes the OS and local corporate policies allow a top-level hidden directory (`.corp`) without triggering shadow-IT alerts or causing sync failures in standard Windows enterprise environments.

**Overlooked risks:** Archiving locally breaks relative links. Moving 8 stale projects from `10_Projects` to `80_Archive` will instantly sever any hardcoded paths linking Excel datasheets to PowerPoint decks within those projects.

---

### Proposal C
**Steelman first:** The ultimate minimization of cognitive load and routing targets. By reducing top-level folders to just 5, the classification pipeline has fewer targets, massively reducing the routing blast radius and ensuring the user cannot misplace files.

**Your assessment:** Disagree. Nesting `.corp` (pipeline execution infrastructure) inside `90_Archive` (stale/dead user files) is a severe architectural violation. You do not place operational infrastructure inside a user's trash/cold-storage bin.

**Strongest point:** Enforcing a flat, no-subfolder rule for `20_Tools` to absolutely guarantee O(1) retrieval complexity and zero-friction access for the user.

**Weakest assumption:** That system configuration logically belongs in an Archive folder, and that an LLM routing agent won't accidentally overwrite system files while attempting to archive a stale project.

**Hidden assumptions:** Assumes `10_Active` vs `90_Archive/projects` won't break the pipeline's internal pathing logic, which currently relies on standard project names.

**Overlooked risks:** Security and compliance data governance. By deleting `80_Compliance` and burying compliance artifacts in a general `90_Archive`, you lose the ability to apply strict RBAC (Role-Based Access Control) or retention policies to sensitive ISO/GDPR files.

---

### Proposal D
**Steelman first:** Rob explicitly stated "30_Reference *is* my source library." Consolidating *all* evergreen and daily reusable assets into a single `20_Reference` hot-zone overrides artificial org-chart categories and directly aligns the physical disk with Rob's actual "reach-for-file" behavior.

**Your assessment:** Partially agree. Moving `.corp` to the root is correct, and retaining a dedicated compliance boundary is necessary. However, merging daily hot-tools (mutable master decks) with deep evergreen reference (immutable product docs, RFP library) into one folder violates the principle of least privilege for both the user and the pipeline. 

**Strongest point:** Acknowledging that Council #9's 3-zone model was artificial and that actual disk usage dictates the need for a simplified, behavior-driven top-level structure.

**Weakest assumption:** Assumes Rob won't mind digging through hundreds of product and competitor reference files to find his daily master presentation, directly contradicting his "not buried 3 levels deep" requirement.

**Hidden assumptions:** Assumes the LLM RFP agent can differentiate between a "daily master deck" (which might contain placeholder text) and a "historical RFP response" (verified truth) when they live in the same root boundary (`20_Reference`).

**Overlooked risks:** Blast radius of the LLM context window. If the RFP agent is pointed at `20_Reference`, it will ingest daily active templates alongside verified past answers, virtually guaranteeing it will hallucinate "[Insert Client Name Here]" into live RFP generations.

---

### Revised Recommendation

**I am updating my position** to fuse the strict system-isolation principles of **Proposal B** with the compliance-boundary awareness of **Proposal A/D**. 

Folders are physical state boundaries. Tags are semantic knowledge axes. If the classifier fails, the file must still land in the correct security and execution zone. 

**1. Establish strict trust boundaries (Canonical Top-Level Folders):**
Update `folder_names.py` and `routing_map.yaml` to exactly these 8 boundaries:
*   `00_Inbox` — **Ingestion Boundary:** Quarantine zone for untrusted/unclassified files.
*   `10_Projects` — **Active Work Boundary:** In-flight, unverified client data.
*   `20_Daily` — **Execution Boundary:** Mutable hot-zone (master decks, scripts). Must remain completely flat.
*   `30_Reference` — **Immutable Knowledge Boundary:** Read-only evergreen data.
    *   `30_Reference\RFP_Library` — Formatted dependencies for the RFP agent.
*   `70_Admin` — **Corporate Boundary:** Personal HR data.
*   `80_Compliance` — **Governance Boundary:** Security, ISO, and GDPR artifacts. Separating this from general reference ensures we can apply strict access/retention scripts later.
*   `90_Archive` — **Cold Storage:** Stale projects (>90 days) and inactive files.
*   `.corp` — **Infrastructure Boundary:** Hidden root directory. Move `routing_map.yaml`, `Project_Codes.xlsm`, and all pipeline execution scripts here. Eliminate `90_System` entirely.

**2. Address the Root Cause of the Classification Failure:**
The 53% MISC rate is primarily a mapping failure, not just a structural one. Before deploying the new folder structure, the 16 missing clients must be added to `naming_config.yaml`. 

**3. RFP Trust Isolation:**
RFP agent read-access is restricted *exclusively* to `30_Reference/RFP_Library`. Active RFP responses stay in `10_Projects`. This isolates verified historical ground-truth from unverified in-flight work, protecting the LLM from context poisoning.

**4. Migration Strategy:**
*   Move the 8 stale projects to `90_Archive`. Accept the trade-off that internal hardcoded OLE links may break; physical separation of cold assets is required to reduce index bloat.
*   Deprecate `40_Media`, `50_RFP`, `60_Source_Library`, and `90_System` from all pipeline configurations.

By enforcing these boundaries, we isolate the blast radius of any classifier failure to its respective zone, secure the pipeline from user tampering, and provide the user with O(1) access to his operational tools.

*Latency: 42.73s | Tokens: 13615*

### Deepseek (deepseek-reasoner)

## Steelmanning Each Proposal

### **Proposal A**  
**Steelman:** This proposal is correct if the primary failure mode is **configuration drift** between code, routing, and disk. It assumes that aligning existing successful concepts (20_Workflows, 30_Reference) with Rob’s actual behavior will immediately drop the 53% MISC rate with minimal engineering cost. It further assumes that *access frequency* maps cleanly to three primary zones: active projects, daily tools, and evergreen reference—and that archive is a lifecycle state, not a top-level category.

### **Proposal B**  
**Steelman:** This proposal is correct if the dominant risk is **blast radius from system contamination**. It assumes that separating pipeline infrastructure (.corp) and enforcing strict state-based boundaries (Ingestion/Active/Daily/Cold/Archived) prevents catastrophic pipeline failure when user files intermix with system config. It treats the 53% MISC rate as a secondary problem solvable by client-alias fixes.

### **Proposal C**  
**Steelman:** This proposal is correct if **minimizing top-level cognitive load** is the highest priority. It assumes that 5 folders are the maximum Rob can navigate without friction, and that grouping admin/compliance/archive under one “cold” folder is acceptable because they’re rarely accessed. It further assumes daily tools are cross-client and merit a flat, curated top-level folder.

### **Proposal D**  
**Steelman:** This proposal is correct if **zero-friction access to daily tools** is the primary constraint. It assumes merging all reference (including daily decks) into a single top-level folder (20_Reference) reduces clicks for the 462 most-accessed files (77% of project volume). It treats folder count reduction as a means to eliminate classification mismatch and assumes tags handle secondary discovery.

---

## My Assessment

### **Proposal A**
**Assessment:** **Partially agree.**  
**Why:** The alignment fix is necessary but insufficient. It correctly identifies configuration drift as the immediate cause of 53% MISC, but its 7-folder structure still mixes access-frequency tiers. 20_Workflows as a “hot zone” is reasonable, but the proposal doesn’t define *throughput*: how many files can live there before search degrades? It also assumes archive-as-subfolder is sustainable—with 25 projects today, but what about 250? The failure mode is **archive sprawl inside 10_Projects**, making active project navigation slower over time.

**Strongest point:** Fixing the code/disk mismatch is the fastest way to reduce MISC rate.

**Weakest assumption:** That “archive can be a project lifecycle state, not a top-level concept.” False when project count scales. At 100+ projects, nested archive directories become unmanageable; moving stale projects requires scanning all subfolders—O(n) operation where n = total files. This breaks under load.

**Hidden assumptions:**
1. That Rob’s access frequency is stable across clients and topics (ignoring the “Clicks_Retail” outlier—77% of project files).
2. That the pipeline’s routing logic can handle a three-tier project structure (Active/Stale/Archive) without increasing latency beyond acceptable bounds (e.g., >100ms per file).

**Overlooked risks:**
- **Hot-zone saturation:** 20_Workflows becomes a dump because no admission criteria are enforced by the pipeline.
- **State-transition overhead:** Moving files from Active→Stale→Archive requires manual or cron-triggered operations—if these fail, stale files remain in active view, degrading performance.
- **Compliance boundary bleed:** 30_Reference/Compliance vs. 80_Compliance creates a race condition: which folder does the pipeline choose for a new compliance doc? If it guesses wrong, sensitive material may be exposed.

### **Proposal B**
**Assessment:** **Disagree.**  
**Why:** While system isolation (.corp) is smart, the proposal’s flat 20_Daily folder is a **latency time bomb**. At >50 files, visual scanning degrades; at >100, Rob will waste minutes per day searching. The assumption that “client-alias fixes will correct routing” is optimistic—the 53% MISC rate is likely multi-factorial (missing folders + classifier errors). Also, removing 80_Compliance ignores Rob’s actual disk structure and compliance requirements.

**Strongest point:** Isolating pipeline config in .corp prevents user-induced pipeline failures.

**Weakest assumption:** That “the 53% MISC rate is heavily skewed by the 16 missing client aliases.” False. Even with aliases, classifier accuracy is limited by the 18% LLM fallback rate. MISC will persist.

**Hidden assumptions:**
1. That Rob’s daily tools are <50 items and will remain so.
2. That the pipeline has permission to create/write to hidden directories across all environments (corporate security policies may block this).

**Overlooked risks:**
- **Daily folder explosion:** Without subfolders, 20_Daily becomes a linear search problem—O(n) retrieval latency.
- **Hardcoded path breaks:** Symlinks as a deprecation strategy may fail on Windows if scripts use absolute paths.
- **Archive fragmentation:** Moving stale projects to 80_Archive breaks internal links (Excel formulas, PowerPoint embeddings)—high impact if not mitigated.

### **Proposal C**
**Assessment:** **Disagree.**  
**Why:** Grouping admin, compliance, and archive under 90_Archive is a **violation of access boundaries**. Compliance documents require strict handling; mixing them with stale projects increases risk of accidental exposure or deletion. The 5-folder model also buries daily tools under 20_Tools—but if tools are used daily, why are they not at the same level as Projects? This adds cognitive load.

**Strongest point:** Reducing top-level folders to 5 minimizes initial cognitive load.

**Weakest assumption:** That “admin, compliance, and archived projects can be grouped under one 90_Archive folder without causing confusion.” False. These are semantically and operationally distinct; merging them increases error rates during manual file operations.

**Hidden assumptions:**
1. That Rob will tolerate one extra click for admin/compliance files (he might, but the pipeline must now classify into deeper subfolders—increasing routing complexity).
2. That “stale projects (>90 days inactive) can be moved automatically without breaking references.” False without link rewriting or symbolic links.

**Overlooked risks:**
- **Compliance violation:** Sensitive compliance docs mixed with stale projects.
- **Tool sprawl:** 20_Tools flat limit is unenforceable—no mechanism to prevent subfolders.
- **Archive performance:** 90_Archive/projects/ may become deep and nested—slow to traverse.

### **Proposal D**
**Assessment:** **Partially agree.**  
**Why:** The strict access-frequency tiers (6 folders + .corp) are conceptually sound, and merging daily tools into 20_Reference reduces clicks for high-volume files. However, **lumping all reference into one folder creates a scaling bottleneck**. At 300+ files, retrieval latency increases even with subfolders—the proposal admits this risk but offers only quarterly cleanup as mitigation.

**Strongest point:** Daily master decks move from 3+ clicks to 1 click—directly addressing Rob’s zero-friction requirement.

**Weakest assumption:** That “Rob’s self-reported daily/weekly vs. rarely-used distinction is accurate and stable.” False. Access patterns shift with opportunities; a static structure may become misaligned within weeks.

**Hidden assumptions:**
1. That the pipeline can classify accurately into 20_Reference without creating subfolder confusion.
2. That Rob will use Obsidian tags for secondary discovery (but raw client files aren’t renamed—tags may not be applied yet).

**Overlooked risks:**
- **Reference folder becomes a black hole:** High file count degrades search performance.
- **Classification latency:** Router must decide between 20_Reference and 10_Projects—if confidence is low, MISC rate may stay high.
- **No hot-zone prioritization:** Daily tools are mixed with evergreen reference—both are in 20_Reference, but access frequency differs by orders of magnitude.

---

## Revised Recommendation

**I update my position** based on the overlooked risks in all proposals. The core failure mode is **not** just configuration mismatch—it’s **inadequate throughput design for the hot zone**.  

**Evidence:**  
- Rob’s 77% of project files are in one client (Clicks_Retail)—this is a **power-law distribution**, not uniform. Any structure must handle extreme skew.  
- Daily tools (master decks, demos) are used across clients but are currently buried.  
- The pipeline’s 53% MISC rate is a symptom of **both missing folders and classifier uncertainty**—fixing folders alone won’t solve it.  

**My recommendation:**
1. **Adopt Proposal D’s 6-folder + .corp structure** for its access-frequency alignment and system isolation.
2. **But modify 20_Reference into two top-level folders** to separate **daily hot zone** from **evergreen cold zone**:
   - `20_Daily` – Flat, ≤50 files, strictly curated: master decks, demo scripts, technical presentations.
   - `30_Reference` – Moderately nested: product docs, competitive, RFP library by format.
3. **Keep 80_Compliance** as a top-level folder for sensitive originals; reference copies go in 30_Reference/Compliance.
4. **Define archive as 90_Archive** with subfolders per client—top-level to avoid O(n) scans.
5. **Add a pipeline rule:** If client alias is missing, route to 00_Inbox for manual triage—reducing MISC rate immediately.

**Why this update?**  
Proposal D correctly prioritizes zero-friction access but misses the **throughput limit** of a single reference folder. By splitting hot and cold reference, we bound latency for daily tools (O(1) via flat folder) while allowing deeper nesting for evergreen content. This also simplifies classifier routing: daily tools are identified by filename pattern (e.g., “Master_Deck_*”), reducing LLM fallback.

**Failure modes addressed:**
- **Hot-zone saturation:** 20_Daily has a hard file limit—pipeline rejects new additions beyond 50, forcing curation.
- **Archive scalability:** 90_Archive at top-level allows O(log n) lookup via client subfolders.
- **Compliance boundary:** 80_Compliance remains isolated; pipeline routes based on security tags.
- **MISC rate reduction:** Missing aliases go to Inbox, not MISC.

**What breaks first:**  
If 20_Daily exceeds 50 files, the pipeline will flag it for manual cleanup—a controlled degradation. If 90_Archive grows beyond 1000 files, traversal slows, but that’s acceptable for cold storage.

**Signals to revisit:**  
- Daily tool retrieval exceeds 2 clicks (measured via file-access telemetry).
- 20_Daily limit triggers more than once per week.
- MISC rate remains >20% after client-alias fixes and new folder alignment.

*Latency: 116.64s | Tokens: 13255*

### Openai (gpt-5.4)

Below is my round-2 council assessment through a product/pragmatism lens: can a small team actually implement this, can Rob actually use it, and will it reduce operational pain fast enough to matter?

---

# Proposal A

## Steelman first
Proposal A is exactly right **if** the main problem is not “lack of conceptual elegance” but “the code, router, and disk no longer describe the same world,” and the best fix is to converge on the structure Rob is already implicitly using. If Rob truly experiences his work in three primary buckets — **client work**, **reusable execution tools**, and **evergreen reference** — then keeping `10_Projects`, `20_Workflows`, and `30_Reference` as the spine is the highest-leverage move. It is also right if the team needs a design that can be implemented with low migration effort, low retraining, and low risk of creating a new junk taxonomy.

## Your assessment
**Agree** with the Position.

This is the best proposal because it balances:
- user behavior,
- implementation realism,
- migration effort,
- and operational clarity.

It fixes the mismatch without inventing a new language Rob has to learn. It also respects an important truth many architecture proposals miss: **the folder names are a user interface**. Rob already recognizes `30_Reference`; he explicitly said it *is* his source library. Proposal A listens to that instead of trying to rename the world for theoretical neatness.

I especially agree with:
- no new top-level `50_RFP`,
- no resurrection of `60_Source_Library`,
- no top-level archive,
- and hiding pipeline internals under `90_System\.corp`.

That said, I think the `Active/Stale/Archive` split under `10_Projects` is directionally right but may be slightly too operationally heavy if enforced manually from day one. It should be adopted, but with simple rules and a light-touch migration.

## Strongest point
**Archive is a lifecycle state, not a top-level user-facing domain.**

That is exactly the right framing. With only ~25 projects, making Archive a root folder adds one more decision at the top level for little gain. Putting lifecycle under `10_Projects` matches how presales work actually behaves.

## Weakest assumption
**That `20_Workflows` is already well-understood and won’t become a junk drawer.**

This is the most fragile part. “Workflow” is intuitive to the architect but not always to the user. If admission rules are not brutally clear, anything reusable-but-not-reference will drift there. If that happens:
- browse quality degrades,
- routing ambiguity rises,
- and Rob loses trust in the structure.

## Hidden assumptions
1. **Rob will consistently distinguish “reusable execution asset” from “evergreen reference.”**  
   That may be true for him now, but many files sit in the gray zone.

2. **The team can update all path-dependent automation in lockstep.**  
   The proposal mentions the risk, but it still assumes disciplined rollout and test coverage.

## Overlooked risks
- **Migration ambiguity risk:** existing files in `20_Workflows`, `30_Reference`, and `90_System` will have edge cases that don’t map cleanly. The proposal is right structurally but underestimates cleanup decisions.
- **Clicks_Retail distortion risk:** one giant client folder can dominate path behavior and user habits; that may reduce the benefit of project lifecycle subfolders if not handled carefully.
- **User naming drift inside subfolders:** even with root folders fixed, if local subfolder conventions vary wildly by client, retrieval friction remains high.

---

# Proposal B

## Steelman first
Proposal B is exactly right **if** the top priority is not just folder usability but **hard isolation boundaries** between user space and machine space, and if the team is willing to normalize around a more state-based model than a work-style model. It would be correct if Rob’s daily assets are best treated as a distinct “hot zone,” and if operational incidents caused by visible system files are a greater long-term risk than mild conceptual awkwardness in the folder names.

## Your assessment
**Partially agree** with the Position.

This proposal is strong on systems thinking and blast-radius control. It is also right that hidden infrastructure is non-negotiable. But I disagree with the proposed visible folder set, especially:
- replacing `20_Workflows` with `20_Daily`,
- introducing top-level `80_Archive`,
- and removing visible `90_System` entirely in favor of top-level hidden `.corp`.

Why? Because this over-optimizes for purity of model at the expense of migration realism and user continuity.

A small team can implement this, but it creates more conceptual churn than necessary:
- `20_Daily` is behaviorally attractive but semantically weak,
- `80_Archive` adds top-level choice pressure,
- and top-level `.corp` removes the user-facing distinction between “system support” and “hidden machine internals” in a way that may be too abrupt.

I like the hidden infra idea. I do **not** like replacing too much of the existing user-facing language at once.

## Strongest point
**Folders should represent state/access boundaries; tags should represent semantics.**

That is a very good design principle and one the final ADR should preserve.

## Weakest assumption
**That stale projects should be moved straight into a top-level archive as a one-time migration.**

This is likely false in practice. Presales projects often come back, reopen, get reused, or provide active reference. If that assumption is wrong:
- archived material becomes harder to retrieve,
- users bypass the archive,
- and trust in the structure drops.

## Hidden assumptions
1. **A hidden top-level `.corp` is operationally acceptable in this environment.**  
   It may be, but some tooling, backup habits, or user troubleshooting patterns may assume visible system folders.

2. **`20_Daily` will stay curated.**  
   In reality, “daily” is a tempo label, not a content-type rule. Those tend to rot fast.

## Overlooked risks
- **Naming volatility risk:** “Daily” may stop matching reality as Rob’s role shifts.
- **Supportability risk:** hidden top-level directories can be harder for future maintainers to discover and debug than `90_System\.corp`.
- **Governance ambiguity:** removing visible `80_Compliance` may be fine or may conflict with future handling expectations; this proposal doesn’t fully justify that choice against the current actual disk pattern.

---

# Proposal C

## Steelman first
Proposal C is exactly right **if** radical simplification is the only way to get adoption, and if Rob benefits more from having very few root choices than from preserving any of the existing conceptual distinctions. It would be correct if a compact structure like `Active / Tools / Knowledge / Archive` matches his mental model better than the current names, and if the team can absorb a more opinionated migration without confusion.

## Your assessment
**Disagree** with the Position.

This proposal is too reductive and too destructive of useful distinctions. It solves mismatch by collapsing categories that should remain separate:
- active projects renamed to `10_Active`,
- admin/compliance/projects all pushed under archive,
- `90_System` effectively buried under archive.

That is not a practical operating model.

Most importantly: **putting admin, compliance, and archived projects under one top-level archive bucket is wrong.** These are not the same thing operationally, legally, or cognitively. Rob still needs `70_Admin` as a stable corporate-life area whether or not those files are “cold.” Compliance is also not just archival residue.

This proposal reduces top-level count at the expense of meaning. That is false economy.

## Strongest point
**It is ruthless about minimizing top-level options.**

That instinct is valuable. Cognitive load matters. But here it is applied too aggressively.

## Weakest assumption
**That stale projects, compliance, and admin can coexist under one archive umbrella without harming retrieval or governance.**

If false — and I think it is — then:
- admin becomes harder to access,
- compliance handling gets muddied,
- archive becomes semantically incoherent,
- and users create side channels to compensate.

## Hidden assumptions
1. **Coldness equals sameness.**  
   It assumes infrequent access is enough reason to co-locate unlike things.

2. **`10_Active` is a better mental model than `10_Projects`.**  
   That is not proven, and it discards a clear, existing term for little benefit.

## Overlooked risks
- **Governance risk:** compliance buried inside archive may fail future expectations around handling boundaries.
- **Operational debugging risk:** putting `.corp` under `90_Archive` is actively awkward and misleading.
- **Path churn risk:** renaming almost every concept increases migration effort without corresponding user value.

---

# Proposal D

## Steelman first
Proposal D is exactly right **if** the current three-zone model has already failed Rob in practice, and if the correct answer is to abandon “workflows” as a false distinction and instead create one highly optimized `Reference` hub containing almost everything reusable. It would be right if Rob mostly thinks in terms of **active project vs not-active-project**, and if daily-use tools are better treated as items at the root of a broad reference area than as a separate execution category.

## Your assessment
**Disagree** with the Position.

This proposal is elegant in a whiteboard sense but weak in day-2 operability. It collapses too much into `20_Reference`:
- daily decks,
- demos,
- technical presentations,
- product docs,
- competitor materials,
- RFP answers.

That folder becomes a traffic jam almost immediately.

It also unnecessarily renames established structures:
- `30_Reference` to `20_Reference`,
- `70_Admin` to `30_Admin`,
- `80_Compliance` to `40_Compliance`,
- archive to top-level `50_Archive`.

That is a lot of churn for very little practical benefit. A small team can implement it, but they shouldn’t. It spends migration energy on renaming instead of on fixing routing, aliases, and system separation.

Proposal D has one excellent instinct — keep daily-use content near the top — but it expresses that by overloading Reference rather than by maintaining a dedicated hot-zone.

## Strongest point
**It takes Rob’s “daily assets must be immediate” requirement seriously instead of treating it as a nice-to-have.**

That focus is correct and important.

## Weakest assumption
**That one broad `Reference` hub can simultaneously serve as daily hot zone and cold evergreen library without becoming a dumping ground.**

That assumption is very likely false. If false:
- retrieval worsens,
- curation burden rises,
- and the folder loses both speed and clarity.

## Hidden assumptions
1. **Renaming folders improves behavior enough to justify migration churn.**  
   Usually it doesn’t unless the old names are actively harmful.

2. **Workflows is a fabricated category.**  
   Rob may not have used the exact word in feedback, but the category of reusable execution assets is clearly present in his behavior.

## Overlooked risks
- **Massive reference sprawl risk:** much higher than acknowledged.
- **Human factors risk:** users may disagree with “why is my master deck in Reference?”
- **Implementation friction risk:** too many renames means more broken paths, more script changes, more transcript-to-ADR complexity.

---

# Revised recommendation

## Position
**I maintain my original position closest to Proposal A, with one sharpened adjustment: keep `90_System` visible as the user-facing system bucket, but move all pipeline/runtime internals into `90_System\.corp\`; and keep project lifecycle states under `10_Projects` rather than creating a top-level archive.**

The other proposals did **not** change my mind because none of them beats A on all three of the only metrics that matter here:

1. **Can Rob navigate it instinctively?**
2. **Can a small team implement it without a migration program?**
3. **Will it reduce routing failure fast?**

A is the only proposal that scores well on all three.

---

## Final recommended structure

### Canonical top-level folders
Use exactly these in `folder_names.py`:

- `00_Inbox`
- `10_Projects`
- `20_Workflows`
- `30_Reference`
- `70_Admin`
- `80_Compliance`
- `90_System`

That is the binding set.

---

## Exact purpose of each

- **`00_Inbox`**  
  Temporary intake/quarantine. Should normally be near empty.

- **`10_Projects`**  
  Client/opportunity-specific work. All active response materials, client decks, solution docs, working spreadsheets, and in-flight RFP responses live here.

- **`20_Workflows`**  
  High-frequency reusable execution assets Rob reaches for constantly: master decks, demo scripts, standard technical presentations, workshop kits, reusable calculators, repeatable presales working material.  
  This is the **hot zone**.

- **`30_Reference`**  
  Evergreen knowledge hub/source library: product docs, architecture references, competitive intelligence, branding, reusable background material, and historical RFP reference library.

- **`70_Admin`**  
  Corporate life: Workday, goals, compensation, benefits, feedback exports, HR/admin documents.

- **`80_Compliance`**  
  Controlled/sensitive compliance and security artifacts requiring physical separation from general reference. This is a handling boundary, not a knowledge taxonomy.

- **`90_System`**  
  User-visible system support area only. Human-meaningful support files may remain at root if needed; all machine-facing pipeline internals go under `90_System\.corp\`.

---

## Required depth rules

### Hot zone
- `20_Workflows` must stay shallow.
- Max depth: **2 levels below top**.
- If content needs deeper semantic organization, that belongs in tags/Obsidian, not folders.

### Projects
Use lifecycle subfolders inside `10_Projects`:
- `10_Projects\Active\{Client}\`
- `10_Projects\Stale\{Client}\`
- `10_Projects\Archive\{Client}\`

This preserves a single project entry point while reducing clutter.

### Reference
Moderate nesting is acceptable:
- `30_Reference\Products\`
- `30_Reference\Architecture\`
- `30_Reference\Competition\`
- `30_Reference\Branding\`
- `30_Reference\RFP_Library\Excel\`
- `30_Reference\RFP_Library\Word\`
- `30_Reference\RFP_Library\PowerPoint\`

Do **not** try to mirror all 11 taxonomy dimensions physically.

---

## Folder vs tag rule

### Folders represent
- access pattern,
- work context,
- lifecycle state,
- handling boundary.

### Tags represent
- product,
- client,
- domain,
- topic,
- type,
- source,
- comp,
- compliance classification,
- training,
- function,
- audience.

If a dimension is useful for search but not a primary “where would Rob click first?” axis, it stays a tag.

---

## RFP decision
**No top-level `50_RFP`.**

- **Active RFP work:** `10_Projects\{state}\{Client}\`
- **Historical reusable RFP answers:** `30_Reference\RFP_Library\{Format}\`

This is the cleanest split between in-flight work and evergreen reusable knowledge.

---

## Archive decision
**No top-level archive folder.**

Archive is a **project lifecycle state** under `10_Projects`, not a separate root concept.

Reason: it reduces top-level cognitive load and matches how presales work is resumed, reopened, and reused.

---

## Access-frequency principle
Binding rule for ADR:

- **Daily / several times per week:** top-level or 1 click from top (`20_Workflows`, active client folder)
- **Weekly / situational:** 1–2 levels deep (`30_Reference` category folders)
- **Monthly / rare / controlled:** deeper or lifecycle-separated (`10_Projects\Archive`, `80_Compliance`, `90_System\.corp`)

If a file is used constantly, it must not live in a deep cold-zone.  
If a file is sensitive or machine-facing, convenience does not override separation.

---

## What gets removed from spec
Remove these from canonical spec:
- `30_Templates`
- `50_RFP`
- `60_Source_Library`
- `80_Archive`
- `20_Extra_Initiatives`
- `40_Media`

These are either duplicates, wrong abstractions, or dead placeholders.

---

## Why the other proposals didn’t change my mind

- **B** had the best isolation thinking, but introduced unnecessary root churn (`20_Daily`, top-level `.corp`, top-level archive).
- **C** simplified too hard and merged unlike things under Archive, which is operationally wrong.
- **D** took access frequency seriously but overloaded `Reference` and renamed too much for too little gain.

A remains the only proposal that is:
- implementable by a small team quickly,
- understandable by the actual user,
- and conservative enough to ship without another round of taxonomy regret.

## Bottom line
**Adopt Proposal A’s structure, explicitly codify anti-junk-drawer rules for `20_Workflows`, keep `90_System` but hide pipeline internals in `90_System\.corp`, and treat archive as a substate of projects rather than a top-level folder.**

That is the decision I would sign.

*Latency: 57.81s | Tokens: 11871*

### Grok (grok-4.20-beta)

**Steelman: Proposal A**  
For A to be exactly right, Rob’s access patterns must be cleanly tripartite (active client work / high-frequency execution assets / evergreen knowledge), `20_Workflows` must remain a stable, small, high-signal hot zone rather than a junk drawer, and the marginal cognitive cost of seven top-level folders must be lower than the cost of forcing daily tools into either Projects or Reference. If those three conditions hold, A is the minimal surgical correction that eliminates the 53% MISC rate while respecting existing muscle memory.

**Assessment:** Partially agree.  
The frequency-based zoning is correct, but the proposal still carries too many legacy numbered folders and treats `80_Compliance` as a peer to daily tools. Seven folders is already pushing cognitive load for an ADHD user.

**Strongest point:** It refuses to throw away the working `20_Workflows` and `30_Reference` concepts Rob actually uses, instead of inventing fresh marketing names (`Daily`, `Tools`, `Knowledge`).

**Weakest assumption:** That `20_Workflows` will stay curated. History (40_Media, 90_System pollution) shows Rob treats any ambiguously-named folder as overflow.

**Hidden assumptions:** (1) Numbered prefixes with deliberate gaps (`40_`, `50_`, `60_`) are still the right sorting mechanism in 2026; (2) the user will reliably move files between `Active/Stale/Archive` subfolders instead of just dumping everything in `10_Projects`.

**Overlooked risks:** Link rot inside the Obsidian vault when files move between the new `Active/Stale/Archive` zones; accidental exposure of pipeline files if `.corp` is not hidden at the filesystem level on all machines.

---

**Steelman: Proposal B**  
B is exactly right if the dominant failure mode is blast radius (user or malware touching pipeline config) and if renaming the hot zone `20_Daily` creates stronger behavioral expectations than `20_Workflows`. It correctly treats folders as *state* boundaries and tags as *meaning* boundaries.

**Assessment:** Disagree.  
The `20_Daily` name is marketing-speak that will age poorly, and hiding everything in `.corp` while still having six visible folders is a half-measure. It also quietly drops compliance as a first-class concern.

**Strongest point:** The explicit blast-radius and system-isolation argument is the only proposal that treats the pipeline itself as a first-class inhabitant of the folder structure rather than an afterthought.

**Weakest assumption:** That the pipeline can reliably run with OS permissions on a hidden `.corp` directory across Rob’s various laptops, VMs, and occasional offline scenarios.

**Hidden assumptions:** That Rob will treat a folder literally called “Daily” as sacred and not drop random client files in it. Also assumes the 53% MISC rate is *only* alias-driven and not partly driven by the classifier’s inability to distinguish “daily tool” from “evergreen reference.”

**Overlooked risks:** Future governance or legal hold requirements that suddenly demand an auditable, non-hidden location for certain config or reference files; breakage of any existing PowerShell/Excel macros that hard-code `90_System`.

---

**Steelman: Proposal C**  
C would be exactly right if cognitive load were the primary constraint and if Rob’s admin, compliance, and archived project material truly shared the same access frequency and trust boundary (i.e., “I almost never touch any of this”). Five folders is the smallest number that still covers the observed workflow.

**Assessment:** Disagree.  
Grouping admin, compliance, *and* archive under `90_Archive` is a category error. Compliance files are not “cold”; they are sensitive. Admin files are not archived; they are ongoing corporate life. This violates the frequency principle the proposal claims to optimize for.

**Strongest point:** Ruthless minimization of top-level folders. It takes the “every folder is cognitive load” constraint seriously.

**Weakest assumption:** That Rob’s daily tools can live in a completely flat `20_Tools` folder forever without any substructure. The audit already shows 462 files in one client; the same pressure will appear in Tools.

**Hidden assumptions:** That a one-time migration of eight stale projects plus moving pipeline config into `90_Archive\.corp` will be trivial and that no external tools (RFP agent, Obsidian plugins, corporate search) have hard-coded paths.

**Overlooked risks:** Compliance team audit failure because sensitive material is co-mingled with archive in a folder whose name implies it is disposable.

---

**Steelman: Proposal D**  
D is exactly right if Rob’s actual behavior has already collapsed “daily tools + evergreen reference” into a single mental bucket (his own words: “30_Reference IS my source library” and “master deck… should be immediately accessible”). In that world, the 3-zone model from Council #9 was always a theoretical imposition, and the cleanest fix is to make `20_Reference` the single high-frequency hub while keeping Projects, Admin, Compliance, and Archive as separate state/sensitivity buckets.

**Assessment:** Agree.  
This is the only proposal that takes Rob’s literal feedback as authoritative rather than as something to be massaged into the previous council’s ontology.

**Strongest point:** It directly attacks the hidden premise that Council #9’s 3-zone structure is still binding when the user has explicitly rejected the conceptual model.

**Weakest assumption:** That `20_Reference` will not explode into an unmanageable mess once it becomes the default destination for both daily decks *and* all evergreen material.

**Hidden assumptions:** (1) That the existing Obsidian vault + 11-dimensional tagging is strong enough to compensate for the loss of physical differentiation inside the new mega-Reference folder; (2) that Rob’s current “daily tools” are actually distinct from the reference library in a way that can be enforced by convention rather than by folder boundary.

**Overlooked risks:** Future difficulty extracting the RFP library for the LLM agent if it is mixed with personal master decks and competitive battlecards; psychological effect on Rob of seeing hundreds of files in one folder every day (ADHD trigger).

---

**My Revised Recommendation**

I am adopting a sharpened version of **Proposal D** with one surgical correction.

**Canonical top-level folders (exactly these six visible + one hidden):**
- `00_Inbox`
- `10_Projects` (active client work only; client subfolders, no Active/Stale/Archive substructure)
- `20_Reference` (the daily zero-friction hub — master decks, demo scripts, technical presentations, product docs, competitive, branding, *and* `RFP_Library/{format}/`)
- `30_Admin`
- `40_Compliance`
- `50_Archive`
- `.corp` (hidden dotfolder containing *all* pipeline config, `Project_Codes.xlsm`, `solution_matrix`, routing maps, etc.)

**Exact policy:**
- Daily tools and evergreen knowledge share `20_Reference` because that is what Rob actually said. Subfolders limited to one level (`RFP_Library/Excel`, `RFP_Library/PowerPoint`, `Products/`, `Competition/`). Nothing deeper.
- Stale projects move to `50_Archive` on a simple >90-day inactivity rule (automated later).
- `30_Admin` and `40_Compliance` remain separate because sensitivity and corporate-life frequency are orthogonal to “coldness.”
- All pipeline infrastructure is removed from user view via `.corp`. This is non-negotiable.

**Why the other proposals did not change my mind:**
- A and B both preserve the fiction that Council #9’s Workflows/Reference split is sacred. Rob already told us it isn’t. Adding a seventh folder to maintain an obsolete distinction is exactly the groupthink I am here to kill.
- C’s lumping of compliance into an “Archive” folder is indefensible on its face.
- The only real risk in D is `20_Reference` becoming a dump. That risk is real, but it is smaller than the certainty of cognitive overhead from seven or eight top-level folders for an ADHD user. We will manage the dump risk with explicit admission criteria in the ADR and quarterly 15-minute cleanups, not by adding another folder.

This structure is the smallest possible change that aligns with Rob’s *actual* reported behavior rather than with previous councils’ theoretical models. Everything else is groupthink.

*Latency: 25.22s | Tokens: 11658*

## Synthesis (by claude, non-participant)



# Decision Summary: Council #24 — MyWork Knowledge Architecture

## Consensus

The following points achieved genuine convergence across all four participants, backed by independent reasoning rather than echo:

1. **Pipeline infrastructure must be hidden from user space.** All four proposals called for moving pipeline config, `Project_Codes.xlsm`, `solution_matrix`, and routing internals out of user-visible folders. The mechanism varied (`.corp` at root vs. `90_System\.corp`), but the principle was unanimous and well-evidenced by the current `90_System` pollution problem.

2. **Dead/speculative folders must be eliminated.** Universal agreement to remove `40_Media` (empty), `50_RFP` (never existed on disk), `60_Source_Library` (duplicates `30_Reference`), and `30_Templates` (wrong abstraction). This was evidence-driven: the audit data showed these either don't exist or are empty.

3. **`30_Reference` absorbs the "source library" concept.** Rob explicitly said "30_Reference IS my source library." All participants accepted this, routing historical RFP answers into `30_Reference\RFP_Library\{format}` rather than creating a separate `50_RFP` or `60_Source_Library`. Active RFP responses stay in `10_Projects\{client}`.

4. **Tags handle semantic dimensions; folders handle access state.** Every proposal agreed that the 11 taxonomy dimensions (product, client, domain, topic, etc.) should remain tags, not folders. Physical folders represent access frequency, lifecycle state, or handling sensitivity. This was the strongest shared design principle.

5. **The 53% MISC rate requires both structural alignment AND alias remediation.** All participants acknowledged that fixing folder structure alone won't solve MISC — the 16 missing client aliases in `naming_config.yaml` are an independent, prerequisite fix.

6. **`80_Compliance` must remain physically separated from general reference.** Three of four participants (A, B, D) kept compliance as a distinct boundary. Proposal C merged it into archive and was criticized for this by every other participant. The reasoning was sound: compliance artifacts have different sensitivity, retention, and audit requirements than cold project files.

## Unresolved Disagreements

### 1. Should daily-use tools get their own folder separate from Reference?

**The split:**
- **Proposals A, B, and DeepSeek's revision:** Yes — create `20_Workflows` (or `20_Daily`) as a distinct hot zone, separate from `30_Reference`.
- **Proposal D (Grok) and partially Gemini's revision:** No — merge daily tools into `20_Reference` because Rob already mentally combines them and an extra folder adds cognitive load.

**The crux:** Whether the behavioral boundary between "mutable execution assets I use every day" (master decks, demo scripts) and "immutable evergreen knowledge I consult" (product docs, architecture references) is strong enough to justify a separate folder, or whether forcing that distinction creates a classification problem the pipeline and user will both get wrong.

**Which side is stronger:** The **separate hot-zone** side (A) has the stronger argument, for three reasons:

First, the access frequency profiles are genuinely different. Master decks are opened, edited, and closed multiple times daily. Product architecture docs are consulted weekly at most. Mixing these in one folder means daily tools compete visually with hundreds of reference documents — precisely the "buried 3 levels deep" problem Rob complained about.

Second, the pipeline needs distinct routing targets. If the classifier must distinguish "daily tool" from "evergreen reference" to place them in the same folder's different subfolders, you've just moved the classification problem inside the folder instead of eliminating it. Separate top-level folders give the router a simpler, more deterministic target.

Third, Grok's own analysis acknowledged the dump risk ("20_Reference will not explode into an unmanageable mess") but dismissed it as manageable via "quarterly 15-minute cleanups." That's a weak mitigation for a risk rated as the proposal's primary failure mode. Proposal A's approach of keeping the hot zone shallow and separate actually solves the problem structurally.

Grok's counterargument — that Rob's literal words ("30_Reference IS my source library") mean he has already collapsed the distinction — is a misreading. Rob was saying the existing `30_Reference` already covers what `60_Source_Library` was supposed to be. He was *not* saying his daily master decks should live there; his separate statement about master decks needing to be "immediately accessible, not buried" implies he wants them *outside* the evergreen reference zone.

### 2. Should Archive be a top-level folder or a lifecycle state under Projects?

**The split:**
- **Proposal A (OpenAI):** Archive is a subfolder state under `10_Projects` (`Active/Stale/Archive`).
- **Proposals B, D, Gemini's revision, DeepSeek's revision:** Archive is a top-level folder (`80_Archive` or `90_Archive` or `50_Archive`).

**The crux:** Whether the ~25 current projects (scaling to perhaps 50-100 over years) are better managed as a lifecycle within one root entry, or whether cold projects should be physically removed from the active browsing path at the top level.

**Which side is stronger:** The **top-level archive** side has the marginally stronger argument at scale. With only 25 projects today, nested lifecycle is workable. But the archive also stores things that aren't projects (old reference material, superseded compliance docs), and a top-level location gives the pipeline a clean, unambiguous dump target for anything confirmed cold. The `Active/Stale/Archive` scheme under `10_Projects` also requires either manual curation or automated state transitions that don't exist yet, adding implementation burden for an uncertain benefit.

However, OpenAI's point that "with only 25 projects, a top-level archive adds decision overhead for little gain" is also valid. This is a genuinely close call. I resolve it in favor of top-level archive because it's simpler for the pipeline to route to, simpler to reason about permissions-wise, and eliminates the ambiguity of three-state project lifecycle management.

### 3. Total folder count: 6 vs. 7 vs. 8

**The split ranges from 5 (Proposal C, rejected) to 8 (Gemini revision).**

**The crux:** Whether cognitive load for an ADHD user is better served by fewer choices (6 folders, accept some conceptual merging) or by more precise categories (7-8 folders, accept more visual noise).

**Which side is stronger:** 7 visible folders is the right number for this case. Going below 7 requires merging unlike things (C's compliance-in-archive, D's tools-in-reference). Going above 7 (Gemini's 8) adds `.corp` visibility overhead and a marginal folder. The evidence: 7 is within established cognitive load limits, each folder maps to a genuinely distinct access pattern or handling requirement, and no folder would have fewer than ~5 files (avoiding the anti-pattern).

## Argument Quality Assessment

**Best-reasoned proposal: Proposal A (OpenAI, gpt-5.4)**
OpenAI consistently grounded arguments in implementation realism, migration cost, and user continuity. The round-2 assessment was exceptionally disciplined — it evaluated every other proposal on the same three metrics (user navigation, team implementability, routing failure reduction) and showed why A scored best on all three. It also correctly identified that folder names are a user interface and that renaming everything for theoretical elegance creates migration churn without user value.

**Second-strongest: Gemini (round 2 revision)**
Gemini's security/blast-radius framing was the most architecturally rigorous. The identification of RFP agent trust boundaries (verified historical answers vs. unverified in-flight work) was a genuine insight no other participant articulated as clearly.

**Weakest proposal: Proposal C (DeepSeek round 1)**
Merging compliance, admin, and archive under one folder was a category error that every other participant identified. The 5-folder model optimized for a single metric (folder count) while violating the access-frequency principle it claimed to prioritize. To DeepSeek's credit, their round-2 revision abandoned this position entirely.

**Single strongest argument in the entire debate:**
OpenAI's framing: *"Archive is a lifecycle state, not a top-level user-facing domain."* While I ultimately rule against this for pragmatic routing reasons, the reasoning was the sharpest conceptual insight in the debate and correctly identifies that archive is fundamentally different from a content category.

**Single weakest argument in the entire debate:**
Grok's dismissal of the dump risk for `20_Reference`: *"We will manage the dump risk with explicit admission criteria in the ADR and quarterly 15-minute cleanups, not by adding another folder."* This proposes a behavioral control (quarterly manual cleanup) as mitigation for a structural risk, which is exactly the kind of "discipline-based" fix that fails in practice — especially for a user with ADHD who explicitly needs zero-friction, structure-enforced solutions.

## Blind Spots

1. **Nobody addressed what happens inside `10_Projects\{Client}` subfolders.** The audit shows Clicks_Retail has 462 files. What's the internal structure? Is there any convention? The pipeline routes to the client root — then what? This is where Rob likely spends most of his time, and no proposal defined subfolder conventions for the largest working area.

2. **Nobody tested the proposed structure against actual file routing scenarios.** With 141 PDFs, 140 PPTXs, 122 XLSXs — where does each type land? A "golden path" analysis of 10 representative files through the proposed router would have grounded the debate in reality rather than abstraction.

3. **Nobody addressed the transition plan for the Obsidian vault.** If files move, do vault links break? Do MOC pages need updating? The extraction pipeline feeds into Obsidian, and physical restructuring could invalidate existing knowledge graph connections.

4. **All participants assumed Windows Explorer browsing as the primary access pattern.** Rob might be using search, Quick Access pins, or Obsidian's file explorer instead. If search is his primary mode, folder structure matters less than metadata quality — and the entire debate optimized for the wrong variable.

5. **Nobody questioned whether numbered prefixes are still the right sorting mechanism.** The `00_`, `10_`, `20_` scheme forces Explorer sort order but also creates cognitive overhead when the numbers are arbitrary and gapped. This convention was inherited, not evaluated.

6. **The `.corp` hidden directory assumption was never validated against corporate IT policy.** Multiple participants proposed it, but hidden directories may trigger endpoint security alerts, be excluded from backup tools, or be invisible to enterprise search indexing.

## Recommended Decision

### Canonical Top-Level Folders

Adopt **7 visible folders + 1 hidden directory**, codified as the single source of truth in `folder_names.py`:

| Folder | Purpose | Access Frequency |
|---|---|---|
| `00_Inbox` | Temporary intake/quarantine. Should be near-empty. | Transient |
| `10_Projects` | Client/opportunity-specific work. Subfolders per client. | Daily |
| `20_Workflows` | High-frequency reusable execution assets: master decks, demo scripts, technical presentations, workshop kits, reusable calculators. **The hot zone.** | Daily |
| `30_Reference` | Evergreen knowledge hub: product docs, architecture, competitive intelligence, branding, historical RFP library. | Weekly |
| `70_Admin` | Corporate life: Workday, goals, salary, benefits, feedback. | Monthly |
| `80_Compliance` | Controlled/sensitive security & compliance artifacts (ISO, GDPR, security questionnaires). Handling boundary. | Rare / auditable |
| `90_Archive` | Completed/stale projects, superseded reference material. Cold storage. | Rare |
| `.corp` | Hidden. All pipeline infrastructure: `routing_map.yaml`, classifier config, `Project_Codes.xlsm`, `solution_matrix`, pipeline scripts. | Machine only |

### Depth Rules

- **`20_Workflows`**: Maximum 2 levels below root. No deep nesting. If it needs deeper organization, it belongs in tags or `30_Reference`.
- **`10_Projects`**: `10_Projects\{Client}\` with user-defined internal structure per client. No mandated `Active/Stale/Archive` substates at this time.
- **`30_Reference`**: Moderate nesting allowed:
  - `30_Reference\Products\`
  - `30_Reference\Architecture\`
  - `30_Reference\Competition\`
  - `30_Reference\Branding\`
  - `30_Reference\RFP_Library\Excel\`
  - `30_Reference\RFP_Library\Word\`
  - `30_Reference\RFP_Library\PowerPoint\`
- **`90_Archive`**: `90_Archive\{Client}\` for archived projects; `90_Archive\Reference\` for superseded evergreen material.

### Folder vs. Tag Rule

**Folders represent:** access frequency, work context, lifecycle state, handling sensitivity.
**Tags represent:** all 11 taxonomy dimensions (product, client, domain, topic, type, source, comp, compliance, training, function, audience).

No taxonomy dimension becomes a top-level folder.

### RFP Decision

No top-level `50_RFP`. Active RFP responses: `10_Projects\{Client}\`. Historical reusable RFP answers: `30_Reference\RFP_Library\{Format}\`.

### Archive Pattern

Projects inactive >90 days are candidates for `90_Archive`. Initially manual; automated lifecycle policy deferred. Archive is top-level to give the pipeline a clean routing target and to keep `10_Projects` lean.

### What Gets Removed from Spec

Remove from all config: `30_Templates`, `40_Media`, `50_RFP`, `60_Source_Library`, `20_Extra_Initiatives`, and the visible `90_System` concept (replaced by hidden `.corp`).

### Access-Frequency Principle (Binding)

- **Daily / multiple times per week**: reachable in 1 click from root (`20_Workflows` contents, `10_Projects\{active client}`)
- **Weekly / situational**: 1-2 clicks (`30_Reference` category folders)
- **Monthly / rare / controlled**: deeper or separated (`90_Archive`, `80_Compliance`, `70_Admin`)

### Rationale for Key Tradeoffs

**Why `20_Workflows` stays separate from `30_Reference`** (against Grok's position): Grok argued Rob's own words collapsed the distinction. I read Rob's feedback differently — he said Reference *is* his source library (rejecting `60_Source_Library`), not that daily execution tools belong in Reference. The dump risk of a merged folder is structural and cannot be mitigated by behavioral discipline alone. Separate folders give the pipeline deterministic routing targets and give Rob a curated hot zone.

**Why top-level `90_Archive` instead of nested under `10_Projects`** (against OpenAI's position): OpenAI's lifecycle-state argument was elegant but premature. Automated state transitions don't exist yet, and manual `Active→Stale→Archive` movement within `10_Projects` adds operational overhead that Rob (ADHD, zero-friction requirement) will not maintain. A top-level archive is simpler: move the folder, done.

**Why 7 folders, not 6** (against Grok's position): Dropping to 6 requires merging either daily tools into Reference (dump risk) or admin into archive (category error). Seven folders with clear, distinct purposes is within cognitive load limits and avoids forcing artificial merges.

**Why `90_System` is eliminated rather than kept** (slight departure from OpenAI): OpenAI wanted to keep `90_System` visible with `.corp` nested inside. But a visible `90_System` with nothing meaningful at its root (since all infra is in `.corp`) becomes an attractive nuisance — Rob or the pipeline will put things there. Eliminating it entirely and using `.corp` at root is cleaner, provided IT policy permits it (see Risk #3 below).

## Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | **`20_Workflows` becomes a junk drawer** — files pile up without curation | Medium | High | Define strict admission criteria in ADR: only cross-client, high-frequency execution assets. Pipeline rejects client-specific material. Add a weekly automated count check: if >75 files, flag for review. |
| 2 | **MISC rate remains >20% after restructuring** because classifier logic, not structure, is the root cause | Medium | High | Treat alias remediation (16 missing clients) as a prerequisite, not a follow-up. Add pipeline rule: if client alias is missing, route to `00_Inbox` for manual triage, not MISC. Measure MISC rate at day 7, 14, 30. |
| 3 | **Hidden `.corp` directory triggers corporate IT issues** — excluded from backup, flagged by endpoint protection, or invisible to enterprise search | Medium | Medium | Validate with IT policy before deployment. Fallback: use `90_System\.corp\` (visible parent, hidden internals) per OpenAI's original proposal. |
| 4 | **Existing scripts/links hard-code old folder names** — pipeline crashes on deployment | High | High | Audit all path references in codebase before migration. Implement 14-day symlink deprecation window from old names to new locations. |
| 5 | **Obsidian vault links break when files move** during restructuring | Medium | Medium | Run a link integrity check before and after migration. Update CKE extraction paths in pipeline config. |
| 6 | **Clicks_Retail (462 files) dominates `10_Projects`** and creates navigation noise | Certain | Low | Accept as-is. This is a legitimate large engagement. Internal subfolder structure is the client team's concern, not the architecture's. |
| 7 | **Archive grows without cleanup and becomes a second junk drawer** | Low | Low | Acceptable for cold storage. Revisit if >500 files or if search latency inside archive becomes a complaint. |

## Action Items

### Immediate (before any file moves)

1. **Add the 16 missing client aliases to `naming_config.yaml`.** This is a prerequisite — structure changes without alias fixes will not meaningfully reduce MISC rate. Owner: pipeline maintainer.

2. **Audit all path references in codebase** (`folder_names.py`, `routing_map.yaml`, any PowerShell scripts, Obsidian plugin configs, Excel macros) for hard-coded paths to `90_System`, `50_RFP`, `60_Source_Library`, `40_Media`, `30_Templates`. Document every reference. Owner: pipeline maintainer.

3. **Validate `.corp` hidden directory feasibility** with corporate IT/endpoint protection policy. If blocked, fall back to `90_System\.corp\` pattern. Owner: Rob (IT inquiry).

### Implementation (single coordinated deployment)

4. **Update `folder_names.py`** to declare exactly the 7 canonical folders + `.corp`. This is the single source of truth. Remove all references to deprecated folders.

5. **Update `routing_map.yaml`** to route to the new folder set. Key routing changes:
   - Default "evergreen" material → `30_Reference` (not MISC)
   - Missing client alias → `00_Inbox` (not MISC)
   - Pipeline config files → `.corp`
   - Security/compliance tagged files → `80_Compliance`

6. **Create the canonical folder structure on disk.** Create any folders that don't exist; rename where needed.

7. **Execute one-time migration:**
   - Move 8 stale projects (>90 days) from `10_Projects` to `90_Archive\{Client}\`
   - Move pipeline internals from `90_System` to `.corp`
   - Move user-facing reference files currently in `90_System` (e.g., `Project_Codes.xlsm` if user-facing) to `30_Reference` or `.corp` as appropriate
   - Delete empty `40_Media`
   - Establish symlinks from old folder names to new locations (14-day deprecation window)

8. **Create `30_Reference` subfolder structure:** `Products\`, `Architecture\`, `Competition\`, `Branding\`, `RFP_Library\Excel\`, `RFP_Library\Word\`, `RFP_Library\PowerPoint\`.

### Post-deployment (within 30 days)

9. **Measure MISC classification rate** at day 7, 14, and 30. Target: <20%. If still >20% at day 30, investigate classifier logic (separate workstream).

10. **Monitor `20_Workflows` file count.** If >75 files at any weekly check, trigger curation review.

11. **Remove deprecation symlinks** after 14 days.

12. **Write ADR-24** documenting all decisions above, including the access-frequency principle, folder-vs-tag rule, and signals to revisit.
