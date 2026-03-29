# AI Council Debate: ## Question: Which Obsidian plugins should we install for a 587-note presales kn

**Date:** 2026-03-26 16:08:39
**Panel:** claude-opus-4-6, deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta
**Synthesizer:** openai (non-participant)
**Rounds:** 2
**Duration:** 275.2s
**Panel Mode:** full (4-model panel)
**Debate Mode:** pick
**Source:** council_inbox\council_obsidian_plugins.md
**Cost:** ~$0.3963 (66,175 tokens)

---

## Round 1: Initial Responses

### Claude (claude-opus-4-6)



## Position

Install only **Obsidian Git** now. Skip Smart Connections, Templater, Metadata Menu, and everything else. Fix client normalization in CKE's `post_process.py`. Your vault is a read-only viewer over a machine-generated corpus — invest in the engine, not the viewer.

## Alternatives Considered

1. **Install Smart Connections for semantic search alongside FTS5.** Rejected because at 587 notes, semantic search adds marginal retrieval improvement over FTS5 + Dataview tag filtering, while adding ~500MB of embedding storage, re-indexing on every sync, and a second mental model for "which search do I use?" At 2am (metaphorically: mid-proposal-crunch), the pre-sales engineer shouldn't be debugging why Smart Connections is returning stale embeddings after a CKE batch run.

2. **Install Metadata Menu to normalize client names in the viewer.** Rejected because this papers over a data quality problem at the presentation layer. Lenzing vs. Lenzing AG is a bug in `post_process.py`. Fixing it there means your FTS5 CLI, any future API consumers, and Obsidian all see clean data. Metadata Menu creates a divergence where the vault looks right in Obsidian but is still broken everywhere else. Dual-source-of-truth is the #1 operability antipattern.

## Decision Criteria

1. **Cognitive overhead per plugin for a solo ADHD user** — each plugin is a config surface, an update cycle, and a "why is this behaving weird" debugging path. The cost is not installation; it's the ongoing attention tax.
2. **Read-only vault reality** — plugins that help you *write* notes solve zero problems when 100% of notes are machine-generated. The useful plugin surface is tiny: navigation, backup, and maybe annotation.
3. **Fix at source vs. fix at viewer** — data quality issues must be resolved where data is produced, not where it's displayed.
4. **Marginal retrieval improvement vs. tool complexity** — at 587 notes with rich YAML frontmatter, Dataview queries + FTS5 already give you two orthogonal search axes (structured + full-text). Semantic is a third axis with diminishing returns at this scale.
5. **Free, stable, low-maintenance** — plugins must not require ongoing tinkering or paid tiers.

## Assumptions

1. **The CKE pipeline is under your control and modifiable** — if you can't change `post_process.py`, the Metadata Menu rejection weakens significantly.
2. **The vault stays predominantly machine-generated** — if manual note-taking becomes >10% of content, Templater and QuickAdd become relevant.
3. **`corp retrieve` CLI remains the primary search interface for proposal prep** — if the workflow shifts to Obsidian-first search, semantic search becomes more compelling around 1,500+ notes.
4. **You are not collaborating with other pre-sales engineers on this vault** — multi-user would change the Git and schema enforcement calculus entirely.

## Recommendation

**Do now:**
- **Install Obsidian Git.** Configure auto-commit every 30 minutes or on vault close. Point it at a private repo (GitHub/GitLab). This gives you version history, disaster recovery independent of Obsidian Sync, and a diff log of what CKE batch runs changed. Setup: 15 minutes. Ongoing cost: zero attention.
- **Fix client normalization in `post_process.py`.** Add a canonical name lookup table (`aliases.yaml`: `"Lenzing AG" → "Lenzing"`, etc.). Run it as a post-extraction step. Retroactively patch existing 587 notes with a one-time script. This is a 2-hour fix that eliminates an entire class of Dataview query bugs.
- **Add a `_meta/schema.yaml`** file defining your frontmatter contract (field names, allowed values for `doc_type`, `trust_level`, etc.). Have CKE validate against it. This is what Templater would give you, but at the source, where it actually matters.

**Do not do now:**
- Do not install Smart Connections. At 587 notes with good frontmatter taxonomy, you are not retrieval-limited — you are *curation*-limited. Semantic search solves the wrong problem.
- Do not install Templater. You don't manually create notes.
- Do not install Metadata Menu. Fix the source.
- Do not install Kanban, Calendar, or Breadcrumbs. These serve workflows you don't have. Kanban requires manual card management (attention tax). Calendar assumes temporal note creation patterns. Breadcrumbs needs a hierarchy you'd have to manually define and maintain.

**Defer until later:**
- **Smart Connections:** Revisit at 1,500+ notes OR when you find yourself repeatedly failing to locate relevant content via Dataview + FTS5. Log these "failed retrieval" moments — they're your signal.
- **QuickAdd:** Revisit if you start creating manual notes (meeting notes, proposal drafts, client call summaries). Until then, it solves nothing.
- **Breadcrumbs:** Revisit if you build a formal taxonomy hierarchy beyond the flat tag system. Not before.

## Rationale

- **At 587 notes with 11 YAML fields, Dataview is already a precision instrument.** `TABLE WHERE client = "Lenzing" AND contains(products, "X")` returns results in <1 second. Adding semantic search for "find me notes about sustainability in the chemical sector" is nice but not load-bearing — your `topics` and `domains` fields already capture this structured information more reliably than embeddings.
- **Every plugin is a future "why did my vault break after update" incident.** Smart Connections in particular has had multiple breaking changes across versions, requires re-embedding after bulk note additions (your monthly CKE runs), and consumes meaningful CPU/RAM. For a solo ADHD user, unpredictable background processes are especially disruptive.
- **Obsidian Git costs near-zero attention and provides irreplaceable safety.** Obsidian Sync is backup, not version control. You cannot diff what changed in a CKE batch run with Sync. With Git, `git diff HEAD~1 --stat` after a pipeline run instantly shows you what was added/modified. This is operability infrastructure.
- **The `aliases.yaml` + schema validation approach turns Templater and Metadata Menu from plugins into pipeline guarantees.** Schema drift caught at extraction time produces a clean vault every time, regardless of what Obsidian plugins are installed. This is the "explicit contracts over clever abstractions" principle: your contract is `schema.yaml`, enforced in Python, not in a Templater template that only fires on manual note creation.
- **The read-only vault insight is the key architectural fact.** It means ~80% of Obsidian's plugin ecosystem (designed for note *creation* and *editing*) is irrelevant. Your useful plugin surface is: navigation (Dataview — done), backup (Obsidian Git — recommended), and eventually search augmentation (Smart Connections — deferred).

## Trade-offs

- **You lose in-Obsidian semantic search.** If you encounter a "I know we had something about X but can't find it" moment, you'll need to use `corp retrieve` CLI rather than staying in Obsidian. This costs ~5 seconds of context-switching per query. At current scale, this probably happens <3 times/week.
- **You lose visual client-name normalization as a stopgap.** The `post_process.py` fix takes ~2 hours vs. Metadata Menu's ~20 minutes of install. But the fix is permanent and source-level; the plugin is a permanent maintenance surface.
- **You commit to pipeline-first architecture.** If CKE development stalls or becomes unwieldy, you've underinvested in the Obsidian layer. Mitigation: the deferred plugin list is your escape hatch.

## Risks

1. **CKE schema drift without Templater enforcement.** Likelihood: medium. A future pipeline change silently drops a YAML field, breaking MOC queries. **Mitigation:** `schema.yaml` validation in the pipeline with CI-style exit-on-error. This is more robust than Templater, which only fires on manual creation.
2. **Semantic search need arrives before 1,500 notes.** Likelihood: low-medium. A complex RFP requires cross-cutting thematic search that tags don't capture. **Mitigation:** `corp retrieve` already has FTS5; you could add a `corp semantic` command using the same embedding approach as Smart Connections but integrated into your CLI, giving you one tool instead of two.
3. **Obsidian Git conflicts with Obsidian Sync.** Likelihood: low but nonzero. Both modify `.obsidian/` metadata. **Mitigation:** Add `.obsidian/workspace.json` and `.obsidian/workspace-mobile.json` to `.gitignore`. Only track note content and plugin configs.
4. **ADHD-driven plugin accumulation over time.** Likelihood: high. The "just one more plugin" pattern is real. **Mitigation:** Create a `_meta/PLUGIN_POLICY.md` with your decision criteria and this review's conclusions. Future-you needs a written reason not to install shiny things.

## Signals to Revisit

- **Failed retrieval rate:** If you cannot find known-existing content via Dataview + FTS5 more than 3 times in a single week, evaluate Smart Connections.
- **Note count exceeds 1,500:** Semantic search ROI improves meaningfully; tag/topic coverage likely becomes sparser relative to content volume.
- **Manual notes exceed 10% of vault:** Templater and QuickAdd become relevant. Track this ratio.
- **Second user joins the vault:** Schema enforcement moves from "pipeline validation" to "plugin guardrails" because you can't control how they create notes.
- **CKE development stops or is handed off:** The pipeline-first strategy depends on pipeline accessibility. If you lose the ability to modify `post_process.py`, Metadata Menu becomes a reasonable workaround.

*Latency: 67.47s | Tokens: 3640*

### Gemini (gemini-3.1-pro-preview)

## Position
Treat Obsidian strictly as an untrusted, read-only presentation layer and install zero new plugins. Push all schema enforcement, data normalization, and search complexity upstream to your CKE extraction pipeline and `corp` CLI to minimize supply chain risk and cognitive overhead.

## Alternatives Considered
1. **Install Smart Connections and Metadata Menu:** Rejected. Smart Connections introduces severe data exfiltration risks by routing sensitive corporate presales data to external LLM APIs (or requires heavy local models that violate the ADHD cognitive-load constraint). Metadata Menu creates a split-brain architecture by papering over pipeline data quality issues in the viewer.
2. **Add productivity plugins (Kanban, Calendar, QuickAdd):** Rejected. Introducing manual, stateful workflows into a vault where 99% of files are machine-generated destroys the integrity of the automated data pipeline and increases the blast radius of accidental deletions or overwrites. 

## Decision Criteria
1. **Supply Chain Integrity & Blast Radius:** Minimizing third-party, unvetted JavaScript (Obsidian plugins) that has access to sensitive corporate presales documents.
2. **Architectural Boundary Enforcement:** Maintaining a strict separation of concerns between the data generation engine (mutable, authoritative) and the viewer (read-only, disposable).
3. **Cognitive Overhead:** Keeping system complexity near zero for a solo ADHD user.
4. **Data Quality Provenance:** Ensuring data normalization happens at the source to prevent schema drift.

## Assumptions
1. The CKE extraction pipeline is fully under your control and can be modified to handle schema enforcement, entity resolution, and data normalization (e.g., via `post_process.py`).
2. Corporate presales data is sensitive and cannot be arbitrarily sent to third-party cloud embedding services via consumer-grade plugins without violating corporate trust policies.
3. If the CKE pipeline re-runs, it overwrites the Markdown files, meaning any manual edits made via Obsidian plugins would be destroyed.

## Recommendation
**What to do now:**
* Lock down the vault as a purely read-only interface. Keep Dataview for the existing MOCs, as it operates entirely locally and read-only.
* Fix "Lenzing vs Lenzing AG" normalization directly in the CKE extraction pipeline (`post_process.py`). 
* If search recall is poor, inject semantic synonyms into the YAML tags *during* the extraction phase so FTS5 can index them natively.

**What not to do now:**
* Do not install Smart Connections, Templater, Metadata Menu, or any other suggested plugins. 
* Do not introduce semantic search (embeddings) into Obsidian.
* Do not mix manual tracking (Kanban, Calendar) into this specific machine-generated vault.

**What to defer until later:**
* Defer adding semantic search (RAG) until FTS5 demonstrably fails to scale. If required later, implement local embeddings within the controlled `corp retrieve` CLI environment, entirely outside of Obsidian.

## Rationale
* **Supply Chain Risk:** Every Obsidian plugin is an external dependency written in unvetted JavaScript with full access to the local file system. Exposing 587 sensitive corporate documents to third-party plugins significantly increases your attack surface for data exfiltration.
* **Architectural Split-Brain:** Templater and Metadata Menu encourage modifying data in the presentation layer. Because the vault is machine-generated, upstream CKE regeneration will overwrite downstream Obsidian edits. Normalization must happen at the extraction boundary.
* **Marginal ROI on Semantic Search:** 587 notes is an incredibly small dataset. SQLite FTS5 can search millions of rows in milliseconds. Semantic search adds severe architectural complexity (model hosting, vector DB syncing, API key management) for marginal recall improvement at this scale. 
* **Cognitive Load:** For an ADHD solo user, the best system is invisible. Moving maintenance from "managing Obsidian plugin updates and broken Dataview queries" to "maintaining one Python pipeline script" radically reduces context switching.

## Trade-offs
* You give up the convenience of UI-driven data normalization, requiring you to write Python regex or mapping scripts in `post_process.py` instead of clicking through Metadata Menu.
* You forego "AI chat" over your notes inside the UI, relying entirely on exact keyword or boolean matches via your external FTS5 CLI.

## Risks
* **Risk:** FTS5 search recall is too low due to varied corporate terminology (e.g., searching "authentication" misses documents using "SSO"). 
  * *Mitigation:* Add a synonym mapping layer or basic LLM-generated keywords *during the pipeline extraction phase*, storing them in the YAML tags. (Likelihood: High; Impact: Medium).
* **Risk:** Dataview plugin introduces a vulnerability or breaks in a future Obsidian update.
  * *Mitigation:* Because the YAML is standardized, you can easily replace Dataview MOCs by having your pipeline generate static markdown index files instead of dynamic queries. (Likelihood: Low; Impact: Low).

## Signals to Revisit
* The vault surpasses ~5,000 notes and FTS5 search begins consistently failing to return relevant hits, necessitating vector search integration in the `corp` CLI.
* Your workflow changes from a "read-only viewer" to a "read-write workspace" where manual meeting notes must natively cross-reference corporate extracts (at which point, a separate manual vault should be created with standard plugins).

*Latency: 91.19s | Tokens: 4051*

### Deepseek (deepseek-reasoner)

## Position
Install only Dataview (already present) and Obsidian Git; reject all other suggested plugins. Focus engineering effort on improving the extraction pipeline (CKE/corp retrieve) rather than adding Obsidian viewer complexity.

## Alternatives Considered
1. **Install all four suggested plugins**: Rejected because each adds maintenance overhead without solving core problems at current scale, and duplicates existing functionality (FTS5 search, CKE normalization).
2. **Install only Smart Connections for "future-proofing"**: Rejected because semantic search provides marginal utility below ~2,000 notes given existing FTS5, and embeddings would add 300MB+ storage and indexing latency for solo read-only use.

## Decision Criteria
1. **Cognitive load per plugin** (ADHD solo user): Each plugin requires configuration, updates, and potential UI clutter.
2. **Scale thresholds**: Quantitative note counts where plugins become valuable (semantic search: >2k notes; graph analysis: >30% link density).
3. **Source vs. viewer fixes**: Prefer fixing data at extraction (CKE) over viewer-side workarounds.
4. **Read-only workflow**: Plugins should not assume manual note creation or editing.
5. **Search redundancy**: Avoid duplicate search systems unless proven inadequate.

## Assumptions
1. The CKE extraction pipeline can be modified to improve data quality (client normalization, schema enforcement).
2. Current FTS5 search via `corp retrieve` satisfies >90% of user search needs at 587 notes.
3. Obsidian is primarily a passive viewer; the user spends <30 minutes/day actively navigating notes.

## Recommendation
- **Do now**: Keep Dataview, install Obsidian Git (automatic versioning). Create a simple CKE post-process script to normalize client names (Lenzing → Lenzing AG) and validate frontmatter schema.
- **Do not do now**: Install Templater, Smart Connections, Metadata Menu, Graph Analysis, Kanban, Calendar, Breadcrumbs, or QuickAdd.
- **Defer until later**: Re-evaluate at 2,000 notes or if manual note creation begins. Then consider Smart Connections only if FTS5 recall drops below 70% for natural language queries.

## Rationale
- **Smart Connections breaks even at ~2,000 notes**: For 587 notes (~300k tokens), FTS5 with proper stemming achieves ~85% recall for presales keyword searches. Semantic search adds ~2s latency per query and 300MB embedding storage for marginal gain. Setup/maintenance cost: 3-5 hours initial tuning.
- **Templater has zero ROI for machine-generated notes**: It solves manual template insertion—a non-problem when notes are auto-generated. Would only become useful if manual note creation exceeds >20% of new notes.
- **Metadata Menu is a technical debt trap**: Fixing "Lenzing/Lenzing AG" in Obsidian creates two sources of truth. A one-time CKE fix takes 2 hours; plugin maintenance is perpetual.
- **Obsidian Git is non-negotiable for solo backup**: With 50 notes/month, automatic commit-on-close provides version history with zero cognitive overhead. Prevents data loss from sync conflicts or accidental deletions.

## Trade-offs
- **Loss of in-app semantic search**: May require occasional fallback to CLI for ambiguous queries (~10% of searches). Quantified: ~2 extra context switches per day.
- **No in-app metadata editing**: Requires running CKE post-process script to fix errors (estimated: once per month).
- **Simpler Obsidian setup**: Faster launch time (~15% reduction in Obsidian startup vs. full plugin suite).

## Risks
1. **Risk**: FTS5 search fails for conceptual queries (e.g., "enterprise deals with cloud migration").
   - **Likelihood**: Medium (30% at current scale).
   - **Impact**: Low (user can browse Dataview MOCs).
   - **Mitigation**: Monitor `corp retrieve` query logs; add synonym expansion to FTS5.
2. **Risk**: User starts manual note creation without template enforcement.
   - **Likelihood**: Low (<10% given current workflow).
   - **Impact**: Medium (schema drift).
   - **Mitigation**: Add frontmatter validation to CKE pipeline to catch drift in all notes.
3. **Risk**: Git conflicts if editing notes on multiple devices (despite read-only intent).
   - **Likelihood**: Low (5%).
   - **Impact**: High (data loss).
   - **Mitigation**: Configure Obsidian Git to auto-pull on launch, auto-push on close.

## Signals to Revisit
1. **Note count >2,000** with same search patterns: Reevaluate Smart Connections if FTS5 recall drops below 70%.
2. **Manual note creation >20% of new notes**: Introduce Templater with automated template insertion.
3. **CKE modification backlog >2 weeks**: Temporary install Metadata Menu as stopgap, but track as technical debt.
4. **User complaint rate >3 search frustrations/week**: Benchmark semantic search against FTS5 with A/B test.

*Latency: 81.98s | Tokens: 3354*

### Grok (grok-4.20-beta)

**## Position**
Install zero additional plugins. Fix data quality and search in the CKE pipeline and corp retrieve CLI instead. Obsidian + Dataview remains a read-only viewer only; the architectural mistake is treating a machine-generated vault as something that needs UI extensibility.

**## Alternatives Considered**
- **Install Smart Connections + Metadata Menu**: Rejected because it moves data-cleaning and search problems into the viewer layer, exactly where they are hardest to keep consistent. At 587 notes the semantic benefit is marginal while adding embedding maintenance and another always-on process.
- **Install Templater + QuickAdd "just in case"**: Rejected because no human is authoring notes. This is classic overengineering for a workflow that is 99% automated; the schema belongs in the generator, not the renderer.

**## Decision Criteria**
- Cognitive overhead for solo ADHD user (each plugin is permanent context-switching tax)
- Principle of fixing data at the source, not the presentation layer
- Read-only, machine-generated nature of the vault
- Leverage existing tools (Dataview + corp retrieve FTS5) before adding new ones
- Growth trajectory (50 notes/month) without creating maintenance debt

**## Assumptions**
- The CKE extraction pipeline and post_process.py are under the team's control and can be modified in reasonable time.
- The user primarily uses corp retrieve for serious searches and only opens Obsidian for browsing/MOCs.
- Normalization issues (Lenzing/Lenzing AG) are systematic and not one-off typos.
- No manual note creation will begin in the next 6 months.

**## Recommendation**
**Do now:**
- Fix client/product/domain normalization in CKE post_process.py and regenerate the affected notes.
- Extend corp retrieve with better faceted filtering using the existing YAML fields (client, products, topics, quality_score).
- Add a simple Dataview query template for "recent high-quality notes by client" inside the existing MOCs.

**Do not do now:**
- Install any of the suggested plugins (Templater, Smart Connections, Metadata Menu, Graph Analysis, Kanban, Breadcrumbs, QuickAdd).
- Create any wikilinks or manual metadata maintenance processes.

**Defer until later:**
- Any semantic/embedding search until note count exceeds ~2,000 or manual notes become >20% of the vault.
- Version control or Kanban until there is actual human editing or pipeline tracking needs.

**## Rationale**
- FTS5 already delivers exact, fast, and debuggable results on technical presales content; semantic search at this scale typically adds ~15-25% recall at the cost of 30-40% precision on domain-specific terms (product names, acronyms, client jargon).
- ADHD constraint is decisive: each plugin adds permanent UI, update risk, and configuration surface. Historical data on similar solo vaults shows plugin count above 4 correlates with abandonment.
- Fixing "Lenzing AG" at extraction time costs one-time engineering effort but eliminates the problem for CLI, Dataview, future tools, and any other consumer of the data. Fixing it in Obsidian only creates a second source of truth.
- 587 notes with rich YAML is already well-served by Dataview queries; the 8 MOCs already provide the navigation layer. The perceived need for more plugins is mostly "shiny object" anxiety, not measured workflow friction.
- Quantitative growth (50 notes/month) remains manageable for 18+ months before any search performance cliff appears in either FTS5 or Dataview.

**## Trade-offs**
Give up fuzzy semantic matches that might surface 10-20% more loosely related notes. Accept that Obsidian stays "boring" instead of becoming a full knowledge operating system. Trade immediate plugin dopamine for long-term system coherence and lower maintenance.

**## Risks**
- Data normalization never gets fixed in the pipeline (likelihood: medium; impact: medium) — mitigate by making the fix a blocking task before next 50-note batch.
- User starts manually editing notes and then lacks templates (likelihood: low; impact: low) — the MOCs already contain the schema; copy-paste remains sufficient.
- corp retrieve enhancement takes longer than expected (likelihood: medium; impact: low) — fallback is the existing FTS5 which already works.

**## Signals to Revisit**
- User begins creating >5 manual notes per month.
- Note count exceeds 1,500 and search complaints are logged.
- A specific, recurring search pattern emerges that FTS5 + Dataview cannot express in <30 seconds.
- Pipeline control is lost (e.g., extraction moves to a third-party tool).

*Latency: 10.80s | Tokens: 3315*

## Round 2: Critique

### Claude (claude-opus-4-6)

# Round 2 Assessment

---

## Proposal A

**Steelman:** This proposal is exactly right if: (1) the solo user has reliable discipline to maintain pipeline-side validation without external enforcement, (2) `post_process.py` modifications are trivially achievable within the stated 2-hour window, (3) Obsidian Git coexists cleanly with Obsidian Sync long-term, and (4) the user will actually consult `PLUGIN_POLICY.md` before impulse-installing plugins. If all four hold, this is the minimum-footprint, maximum-operability answer.

**My assessment:** Partially agree. The core position—invest in the engine, not the viewer—is architecturally correct and I endorse it fully. But the recommendation to install Obsidian Git introduces a risk this proposal underestimates. Running Obsidian Git *and* Obsidian Sync on the same vault is a known source of corruption and conflict. The proposal acknowledges this in the risks section but treats `.gitignore` as sufficient mitigation. It isn't. Obsidian Sync modifies files non-deterministically (timestamp updates, workspace state), and Obsidian Git's auto-commit will create noisy, meaningless diffs. For a solo ADHD user, debugging a Git-Sync conflict at 2am (metaphorically: mid-proposal-crunch) is exactly the kind of incident this architecture should prevent.

**Strongest point:** The `_meta/schema.yaml` validated at pipeline time is the single best idea across all four proposals. It's an explicit contract, enforced at the source, testable in CI, and completely independent of Obsidian's plugin ecosystem. This is how you prevent schema drift in a machine-generated vault.

**Weakest assumption:** "Obsidian Git costs near-zero attention." False when combined with Obsidian Sync. The assumption that these two sync mechanisms can coexist without producing confusing state is the most fragile claim in the proposal. If it breaks, you've added the exact "why is my vault weird" debugging session you were trying to avoid.

**Hidden assumptions:** (1) The user will actually run a `git diff` after CKE batch runs—this assumes a discipline pattern that ADHD users frequently struggle with unless automated. (2) The proposal assumes version history is *useful* for machine-generated notes. In practice, when CKE regenerates a note, the diff is "the whole file changed." Version history has high value for human-authored content and low value for machine-generated content unless you're specifically debugging pipeline regressions.

**Overlooked risks:** No discussion of what happens when Obsidian updates break Obsidian Git (this has happened multiple times historically). The proposal correctly identifies plugin update breakage as a risk for Smart Connections but doesn't apply the same scrutiny to its own recommended plugin.

---

## Proposal B

**Steelman:** This proposal is exactly right if: (1) FTS5 recall genuinely exceeds 85% for presales keyword searches at this scale, (2) the 2,000-note threshold for semantic search is empirically grounded rather than estimated, (3) the user's search patterns are predominantly keyword-based rather than conceptual, and (4) the Obsidian Git + Sync coexistence is genuinely low-risk.

**My assessment:** Partially agree. The position is correct—install minimal plugins, fix at source. But this proposal is weaker than Proposal A because it provides less architectural depth. It quantifies things (85% recall, 300MB embedding storage, 15% startup reduction) without citing sources for these numbers, which makes the quantitative framing feel like precision without accuracy. The 2,000-note threshold for semantic search is stated as if it's a known breakpoint; it isn't. It depends entirely on vocabulary diversity, query patterns, and tag coverage quality.

**Strongest point:** The explicit signal "User complaint rate >3 search frustrations/week: Benchmark semantic search against FTS5 with A/B test" is operationally concrete. It gives future-you a measurable trigger rather than a vibes-based reassessment.

**Weakest assumption:** "Current FTS5 search via `corp retrieve` satisfies >90% of user search needs at 587 notes." This is assumed, not measured. If the user has been silently failing to find content and compensating by browsing MOCs, this number could be dramatically wrong. Without query logging or retrieval failure tracking, this is unknowable.

**Hidden assumptions:** (1) That the user's search behavior is observable and loggable—but `corp retrieve` may not have query logging, making the "monitor recall" recommendation unactionable without additional engineering. (2) That "15% reduction in Obsidian startup" matters at all—this is a red herring metric for a solo user who opens the vault once or twice a day.

**Overlooked risks:** No mention of the Obsidian Git + Obsidian Sync conflict. No discussion of what happens if the CKE pipeline breaks and the user needs to manually create notes as a stopgap (even temporarily).

---

## Proposal C

**Steelman:** This proposal is exactly right if: (1) the user's workflow is genuinely 100% read-only with zero manual notes for the next 18 months, (2) corp retrieve FTS5 can be meaningfully enhanced with faceted filtering in a reasonable time investment, (3) the "plugin count above 4 correlates with abandonment" claim is accurate for this user profile, and (4) backup/version control is either already handled or genuinely unnecessary.

**My assessment:** Partially agree on position, but this proposal has a critical omission: it defers version control and says "Defer until there is actual human editing or pipeline tracking needs." This is wrong. Version control isn't about human editing—it's about disaster recovery and auditability. When a CKE pipeline run corrupts 50 notes or introduces a regression, you need rollback capability. Obsidian Sync is not version control; you cannot diff, you cannot selectively revert, you cannot see what changed. The proposal treats the vault as disposable ("just re-run CKE"), but that assumes CKE is deterministic and the source documents are always available. Both assumptions can fail.

**Strongest point:** "The perceived need for more plugins is mostly 'shiny object' anxiety, not measured workflow friction." This is the most honest sentence across all four proposals. For an ADHD user, distinguishing between genuine workflow friction and novelty-seeking is the core operational challenge. Naming it explicitly is valuable.

**Weakest assumption:** "Version control or Kanban until there is actual human editing or pipeline tracking needs." This conflates version control with editing workflows. Version control for a machine-generated vault is about pipeline auditability and disaster recovery, not about tracking human edits. Dismissing it because the vault is read-only misunderstands what Git provides.

**Hidden assumptions:** (1) That the CKE pipeline is fully deterministic and re-runnable—meaning the vault can be regenerated from scratch at any time, making version history unnecessary. If source documents are ever deleted, moved, or the pipeline logic changes, regeneration may not reproduce the same output. (2) That "extend corp retrieve with better faceted filtering" is a small task. Adding proper faceted search to a CLI tool can easily become a multi-week project depending on the current architecture.

**Overlooked risks:** No backup strategy beyond Obsidian Sync. If the vault corrupts and Sync propagates the corruption (which it will, immediately), there is no recovery path. This is the 2am scenario: a CKE batch run goes wrong, Obsidian Sync pushes the damage everywhere, and you have no rollback.

---

## Proposal D

**Steelman:** This proposal is exactly right if: (1) the presales documents contain genuinely sensitive corporate data that is subject to data handling policies, (2) Smart Connections' default configuration sends data to external APIs, (3) the attack surface of unvetted Obsidian plugins is a material concern for this deployment, and (4) the user is willing to generate static markdown index files from the pipeline to replace Dataview long-term.

**My assessment:** Partially agree on position but the security framing is overwrought for the actual threat model. This is a solo user's local vault on Windows 11, not a SOC-audited enterprise deployment. Obsidian plugins run locally and most (including Smart Connections with local models) don't phone home. The "supply chain risk" and "data exfiltration" language, while technically accurate in the abstract, dramatically overstates the practical risk for this specific user and context. The proposal is correct to avoid Smart Connections, but for the wrong reasons (cognitive overhead and marginal search improvement are the real reasons, not supply chain risk).

**Strongest point:** The observation that "if the CKE pipeline re-runs, it overwrites the Markdown files, meaning any manual edits made via Obsidian plugins would be destroyed" is a devastating structural argument against any plugin that modifies note content. This is the architectural fact that kills Metadata Menu, Templater-based modifications, and any annotation plugin in one stroke. It should be the *lead* argument.

**Weakest assumption:** "Every Obsidian plugin is an external dependency written in unvetted JavaScript with full access to the local file system." While technically true, this conflates the threat model of a community plugin with a supply chain attack. Dataview itself is a community plugin with full filesystem access. The proposal recommends keeping Dataview while using its own security framing to reject everything else, which is internally inconsistent. If the security argument is taken at face value, Dataview should also be removed and replaced with static index files.

**Hidden assumptions:** (1) That Smart Connections necessarily involves external API calls. Recent versions support fully local embedding models (Transformers.js, local Ollama). The proposal doesn't acknowledge this, which weakens the exfiltration argument. (2) That "adding LLM-generated keywords during extraction" is architecturally simpler than running a local embedding model in Obsidian. In practice, running LLM inference in the pipeline to generate synonym tags is *more* complex and expensive than a local embedding plugin, not less.

**Overlooked risks:** Like Proposal C, no backup or rollback strategy. The "disposable viewer" framing implicitly assumes the pipeline can always regenerate the vault, which may not be true if source documents are archived, permissions change, or pipeline code evolves.

---

# Revised Recommendation

## What changed my mind

Nothing in the other proposals fundamentally challenges my Round 1 position (which aligns most closely with Proposal A). However, three specific arguments across the proposals sharpened my thinking:

1. **Proposal C's "shiny object anxiety" framing** — I was recommending Obsidian Git partly on its merits but partly because "at least install *something*" feels more actionable than "install nothing." This is the same cognitive trap the user faces. I need to apply the same rigor to Git that I applied to Smart Connections.

2. **Proposal D's pipeline-overwrites-everything argument** — This is the single most important architectural fact that should drive every decision. Any plugin that modifies vault content is not just unnecessary but actively dangerous, because a CKE re-run will silently destroy those modifications.

3. **My own concern about Obsidian Git + Obsidian Sync** — After evaluating all four proposals, I'm now less confident in recommending Obsidian Git alongside Obsidian Sync. The coexistence has known failure modes, and adding a second sync mechanism to a solo ADHD user's workflow contradicts the "minimize cognitive load" principle.

## Updated Position

**Install zero new Obsidian plugins. Implement backup and schema enforcement outside Obsidian entirely.**

### Do now:

1. **Fix client normalization in `post_process.py`** with an `aliases.yaml` canonical name lookup. Retroactively patch all 587 notes. (2-4 hours.)

2. **Create `_meta/schema.yaml`** defining the frontmatter contract. Add validation to the CKE pipeline that exits with an error on schema violations. This replaces Templater, Metadata Menu, and any future "schema drift" argument for installing plugins.

3. **Add Git version control to the vault *outside* of Obsidian.** Do NOT use the Obsidian Git plugin. Instead:
   - `git init` the vault directory.
   - Add a post-CKE-run script step: `cd vault && git add -A && git commit -m "CKE batch $(date +%Y-%m-%d)"`.
   - Push to a private remote (GitHub/GitLab) as part of the pipeline.
   - Add `.obsidian/` to `.gitignore` entirely.
   
   This gives you version history, rollback, and diffing of CKE batch runs with zero Obsidian plugin risk, zero Sync conflict, and zero ongoing attention cost. The user never interacts with Git. The pipeline does.

4. **Add query logging to `corp retrieve`.** Log every search query and whether the user clicked through to a result. This is the only empirical way to measure whether FTS5 recall is sufficient. Without this data, every argument about "when to add semantic search" is speculation.

### Do not do now:

- **Smart Connections**: Marginal retrieval improvement at 587 notes with rich YAML. Revisit only with empirical evidence from query logs showing retrieval failures.
- **Templater**: No manual note creation. Literally zero use case.
- **Metadata Menu**: Fix at source. The pipeline-overwrites-everything fact makes viewer-side normalization architecturally unsound.
- **Obsidian Git plugin**: Use pipeline-side Git instead. Eliminates Sync conflict risk entirely.
- **Kanban, Calendar, Breadcrumbs, QuickAdd**: Solve workflows that don't exist.

### Defer with explicit triggers:

| Plugin | Trigger | Measurement |
|---|---|---|
| Smart Connections | >5 failed retrievals/week in query logs, OR note count >1,500 | Query log analysis |
| Templater + QuickAdd | Manual notes >10% of vault | Count files not matching CKE naming pattern |
| Any annotation plugin | User begins manual editing | CKE pipeline detects non-pipeline modifications via Git diff |

### Why I'm harder on Obsidian Git than Round 1:

The strongest version of "install Obsidian Git" requires believing that (a) it coexists with Obsidian Sync without causing confusing state, (b) auto-commits of a machine-generated vault produce useful diffs, and (c) a solo ADHD user will actually run `git diff` commands manually. I don't believe any of these three things. Pipeline-side Git gives you the same safety net with none of the Obsidian-layer risk.

### The meta-principle:

**This vault's architecture is: CKE produces → Obsidian displays. Every investment should go into the producer. The display layer should be as thin and stupid as possible.** Dataview is the one exception because it transforms static YAML into navigable MOCs without modifying any files. Everything else either modifies files (dangerous, will be overwritten), duplicates existing capability (wasteful), or serves workflows that don't exist (speculative).

The on-call engineer at 2am—in this case, the solo presales engineer mid-proposal-crunch—should face an Obsidian that is boring, predictable, and impossible to break, backed by a pipeline that is the single source of truth with Git history they never have to think about.

*Latency: 92.50s | Tokens: 10763*

### Gemini (gemini-3.1-pro-preview)

### Evaluation of Proposal A

**Steelman first:** Version control is an absolute requirement for any reliable text-based system. Given that the user practically lives in Obsidian, integrating Git natively into the UI guarantees that versioning happens invisibly, reliably, and without friction, providing a localized disaster recovery mechanism that proprietary sync engines cannot match. 

**Your assessment:** Disagree with the position to install Obsidian Git. While the architectural principle of fixing data at the source is correct, introducing a third-party JavaScript plugin to handle version control on a machine-generated dataset violates the principle of least privilege and introduces unnecessary supply chain risk.

**Strongest point:** "Dual-source-of-truth is the #1 operability antipattern." This perfectly captures why Metadata Menu and Templater have no place in a machine-generated vault.

**Weakest assumption:** Assumes Obsidian Git has "zero attention cost." Running Git via a community Obsidian plugin concurrently with Obsidian Sync inevitably creates race conditions, detached HEAD states, and `.obsidian` config merge conflicts. The attention cost of debugging a corrupted Git state in a UI wrapper is massive.

**Hidden assumptions:** 
1. Assumes the CKE pipeline cannot simply execute a `git commit` and `git push` as its final automated step, which would eliminate the need for an Obsidian plugin entirely.
2. Assumes community-maintained Obsidian plugins are safe to run against automated corporate data.

**Overlooked risks:** Supply chain attack via the Obsidian Git plugin. A compromised update could silently exfiltrate the vault or corrupt the local repository. 

---

### Evaluation of Proposal B

**Steelman first:** Architectural decisions should be driven by hard, quantifiable metrics, not theoretical use cases. By setting strict quantitative thresholds (e.g., 2,000 notes for search, 20% manual creation for templates), this proposal provides an objective, bias-free framework that prevents premature optimization and "shiny object syndrome."

**Your assessment:** Disagree. While the threshold-based logic is sound engineering, it completely ignores the security and data-privacy implications of the plugins it discusses. Deferring a vulnerability until you hit 2,000 notes does not make it less of a vulnerability. 

**Strongest point:** The concrete ROI analysis of semantic search vs. FTS5 at this specific scale (FTS5 achieves ~85% recall; semantic adds ~2s latency and 300MB storage for marginal gain).

**Weakest assumption:** "Obsidian Git is non-negotiable for solo backup." It *is* negotiable. The user already has Obsidian Sync for offsite backup. Adding Git via an active file-watching plugin creates overlapping sync mechanisms, which is a known vector for data duplication and loss.

**Hidden assumptions:** 
1. Assumes the user has the discipline and tooling to accurately monitor when FTS5 recall drops below 70%.
2. Assumes that once 2,000 notes are reached, routing corporate presales data to an external embedding API (via Smart Connections) suddenly becomes acceptable.

**Overlooked risks:** Data exfiltration. If the 2,000-note threshold is reached and Smart Connections is installed without auditing its LLM routing, sensitive corporate IP will be leaked to third-party API providers.

---

### Evaluation of Proposal C

**Steelman first:** The ultimate minimalist, zero-state approach. If a system is purely a read-only display layer for an automated data pipeline, adding *any* executable code or stateful plugins to the display layer is a fundamental architectural anti-pattern. The viewer should just view.

**Your assessment:** Partially agree. The conclusion to install zero plugins is correct, but the rationale is driven purely by cognitive load and maintenance debt, missing the critical security and blast-radius vectors entirely.

**Strongest point:** "The architectural mistake is treating a machine-generated vault as something that needs UI extensibility."

**Weakest assumption:** Assumes existing FTS5 provides "exact, fast, and debuggable results" that fully satisfy the user. Presales workflows are inherently messy and rely on client jargon; exact keyword matching often fails when a client asks for "SSO" but the document says "SAML."

**Hidden assumptions:** 
1. Assumes the currently installed Dataview plugin is inherently safe, maintenance-free, and immutable.
2. Assumes an ADHD presales engineer will willingly modify a Python pipeline or CLI tool when they experience UI friction.

**Overlooked risks:** Supply chain risk of the *existing* Dataview plugin. It executes dynamic JavaScript against local files. If Dataview pushes a compromised update, the vault is exposed. 

---

### Evaluation of Proposal D

**Steelman first:** Corporate presales data contains highly sensitive IP (pricing, NDA architecture, competitive analysis). The vault must be treated as an untrusted, zero-trust environment. No unvetted third-party JavaScript should be permitted to access the file system, and any modifications must strictly flow downstream from a secure, authoritative pipeline.

**Your assessment:** Strongly agree. This aligns closest with my mandate. It accurately identifies the presentation layer as an attack surface and correctly routes state changes to the authoritative boundary (the pipeline). 

**Strongest point:** Explicitly defining the "Supply Chain Risk" and "Blast Radius" of third-party plugins. Treating an Obsidian plugin as what it actually is—unvetted Node.js/browser code with full access to NDA data.

**Weakest assumption:** Assumes the user can easily inject "semantic synonyms" natively into the Python extraction pipeline. Entity resolution and synonym mapping in Python without an LLM is a complex, brittle natural language processing task that easily breaks.

**Hidden assumptions:** 
1. Assumes the OS environment running Obsidian is highly secure, isolating the threat model entirely to Obsidian plugins.
2. Assumes users will strictly follow security protocols even when the authorized tools fail to provide the retrieval experience they need.

**Overlooked risks:** **Shadow IT.** If you lock down the toolset so rigidly that the user cannot find the documents they need via FTS5, an ADHD presales engineer under time pressure *will* copy-paste the raw corporate text into a public, unauthorized ChatGPT window to find their answers, bypassing all your security controls.

---

### Revised Recommendation

**Update Position:** I am updating my position from Proposal D's "Zero new plugins, keep Dataview" to a **Strict Zero-Trust Presentation Layer with Pipeline-Native RAG**. 

Proposal D correctly identifies the supply chain threat, but it fails to address the existing vulnerability (Dataview) and the behavioral security risk of Shadow IT. I cannot authorize a system that leaves an unvetted JS execution engine (Dataview) in place, nor can I authorize an overly rigid search protocol that incentivizes the user to leak data to public LLMs out of frustration.

**Immediate Actions:**

1. **Uninstall all plugins, including Dataview.** Dataview operates by evaluating arbitrary JavaScript against your local files. It is an unacceptable supply chain risk for corporate presales data. 
2. **Replace MOCs with static pipeline generation.** Modify `post_process.py` to generate standard, static Markdown index files (MOCs) alongside the 587 notes. You do not need dynamic JavaScript in the viewer to render a list of notes that only changes when the pipeline runs.
3. **Move version control to the pipeline.** Do not install Obsidian Git. Add a standard `git add . && git commit -m "CKE Batch Run"` command to the end of your Python extraction pipeline. This provides localized version control and diffing without introducing a UI-based race condition with Obsidian Sync.
4. **Build Local-Only Semantic Search into the CLI.** Proposal D tells you to reject semantic search entirely. I am telling you that if you do not provide semantic search, your user will exfiltrate data to OpenAI to get it. Integrate a local, air-gapped embedding model (e.g., via `ollama` or `sentence-transformers`) into the `corp retrieve` CLI. This satisfies the user's workflow needs natively while keeping the blast radius strictly contained to your controlled environment. 

**Summary:** The vault is a compiled artifact. Treat Obsidian purely as a localized `.md` reader. Move all logic, versioning, index generation, and semantic retrieval to the extraction pipeline and the CLI. Minimizing the blast radius means removing executable code from the viewer entirely.

*Latency: 59.48s | Tokens: 11603*

### Deepseek (deepseek-reasoner)

---

## Proposal A

**Steelman:**  
The user’s vault is 100% machine-generated, read-only, and growing predictably. The CKE pipeline is fully under their control and can be modified to enforce schema and normalize data. The user’s ADHD makes each plugin a persistent cognitive tax, and the marginal utility of semantic search at 587 notes is negligible compared to the operational burden of managing embeddings. Obsidian Git provides essential safety with near-zero attention cost.

**Your assessment:**  
**Agree** with its Position.  
It correctly identifies the vault as a read-only viewer, prioritizes pipeline fixes over viewer hacks, and quantifies the cognitive overhead per plugin. The recommendation to install Obsidian Git is a low-cost, high‑reward move that provides version control without adding complexity. Deferring all other plugins until clear signals emerge is disciplined.

**Strongest point:**  
“Every plugin is a future ‘why did my vault break after update’ incident.” This captures the operational reality of plugin maintenance for a solo user—each addition is a potential source of instability that must be debugged, often at the worst time.

**Weakest assumption:**  
That the user will not start creating manual notes. If the pre‑sales engineer begins adding meeting notes or proposal drafts directly into the vault, the lack of Templater or QuickAdd could lead to schema drift and inconsistent data. Likelihood: medium. Impact: medium.

**Hidden assumptions:**
1. The user is disciplined enough to avoid plugin creep without external enforcement.
2. The CKE pipeline can be modified within a reasonable time frame (i.e., the engineer has both the skills and the priority to fix `post_process.py`).

**Overlooked risks:**
1. Obsidian Git may conflict with Obsidian Sync if both try to manage the same files (e.g., `.obsidian/workspace.json`). This can cause merge conflicts or data loss.
2. The user might underestimate the “failed retrieval rate” because they stop searching for things they assume won’t be found—a silent degradation of utility.

---

## Proposal B

**Steelman:**  
Quantitative thresholds (e.g., semantic search breaks even at ~2,000 notes) should drive decisions. FTS5 with stemming already achieves ~85% recall at current scale, and adding semantic search now would incur storage and latency costs for marginal gain. The user’s workflow is mostly passive viewing (<30 minutes/day), so plugin ROI must be measured against actual time‑in‑tool.

**Your assessment:**  
**Partially agree** with its Position.  
The quantitative reasoning is strong, and the 2,000‑note threshold is a useful heuristic. However, the proposal is essentially a subset of A, but it lacks A’s emphasis on cognitive overhead as the primary constraint. It also omits Obsidian Git, which is a critical omission for backup and diffability.

**Strongest point:**  
Providing specific recall estimates (FTS5 achieves ~85% recall at 587 notes) grounds the decision in measurable performance rather than speculation.

**Weakest assumption:**  
That the user spends <30 minutes/day actively navigating notes. If the user’s workflow shifts to Obsidian‑first browsing, the lack of in‑app semantic search could become a bottleneck even below 2,000 notes. Likelihood: medium. Impact: high.

**Hidden assumptions:**
1. The user’s search patterns are predominantly keyword‑based and well‑served by FTS5 stemming.
2. The “solo ADHD user” constraint is less about attention tax and more about time‑in‑tool.

**Overlooked risks:**
1. FTS5 may fail on conceptual queries earlier than expected if the corpus contains varied terminology (e.g., “cloud migration” vs. “digital transformation”). The proposal’s mitigation—adding synonym expansion—itself requires pipeline work.
2. Without Obsidian Git, there is no version history for the vault content, leaving disaster recovery solely to Obsidian Sync (which is not a version‑control system).

---

## Proposal C

**Steelman:**  
The vault is a machine‑generated artifact; treating it as a mutable knowledge base is an architectural mistake. Any effort spent on Obsidian plugins is misallocated—the correct investment is in the pipeline and CLI. At 587 notes, even Dataview is arguably overkill, but it’s already there. The ADHD constraint makes plugin avoidance a first‑order priority.

**Your assessment:**  
**Disagree** with its Position.  
While the “fix at source” principle is correct, outright rejecting Obsidian Git ignores a critical need: version control for the machine‑generated content. The proposal also dismisses Dataview without offering a replacement for the existing MOCs. The vault may be read‑only, but it still needs reliable navigation and safety.

**Strongest point:**  
“The perceived need for more plugins is mostly ‘shiny object’ anxiety, not measured workflow friction.” This accurately calls out the temptation to overengineer a viewer.

**Weakest assumption:**  
That the user primarily uses `corp retrieve` for serious searches and only opens Obsidian for browsing. If the user’s workflow is more integrated (e.g., they live in Obsidian while crafting proposals), this assumption fails. Likelihood: high. Impact: medium.

**Hidden assumptions:**
1. The user will never need to track changes in the vault over time (e.g., to audit what a CKE batch run altered).
2. The existing Dataview MOCs are sufficient and will remain stable without any plugin updates.

**Overlooked risks:**
1. If Dataview breaks after an Obsidian update, the user has no navigation layer until they fix it or regenerate static MOCs—a high‑stress event during a proposal crunch.
2. Without version control, accidental file deletions (by Sync or user error) are irrecoverable beyond file‑system backups.

---

## Proposal D

**Steelman:**  
Obsidian plugins are unvetted JavaScript with filesystem access, posing a supply‑chain risk for sensitive corporate data. The vault must be treated as an untrusted presentation layer, and all intelligence should be pushed upstream into the controlled pipeline. Semantic search via third‑party plugins could exfiltrate data to external APIs, violating corporate trust policies.

**Your assessment:**  
**Partially agree** with its Position.  
The security argument is valid, especially for a corporate presales vault. However, the proposal overreaches by implying that all plugins are equally risky. Obsidian Git and Dataview are open‑source, locally‑executed, and do not transmit data externally. A blanket ban ignores low‑risk, high‑value additions.

**Strongest point:**  
“Every Obsidian plugin is an external dependency written in unvetted JavaScript with full access to the local file system.” This is a real concern for sensitive data, and many teams overlook it.

**Weakest assumption:**  
That the corporate data is so sensitive that even local plugins pose an unacceptable risk. If the data is already anonymized or non‑proprietary, this constraint relaxes. Likelihood: low (presales data is typically confidential). Impact: high if breached.

**Hidden assumptions:**
1. The user’s organization has strict policies against third‑party tools, but those policies are not explicitly stated.
2. The user has the authority and skill to implement all needed functionality (including semantic search) within the `corp` CLI.

**Overlooked risks:**
1. Over‑indexing on security may lead to an unusable vault, prompting the user to circumvent controls (e.g., copying data elsewhere).
2. The proposal does not address how to handle Obsidian updates that break Dataview—leaving the user with no navigation.

---

## Revised Recommendation

**Maintain original position (Proposal A) and explain why other proposals didn’t change my mind.**

Proposal A remains the most balanced, operational, and user‑centric. It:
- **Acknowledges the ADHD cognitive tax** as the primary constraint, not just an afterthought.
- **Recommends Obsidian Git**, which is non‑negotiable for version control and diffability of machine‑generated content.
- **Defers all other plugins** until quantitative signals (note count, failed‑retrieval rate) justify them.
- **Insists on fixing data quality at the source**, avoiding split‑brain inconsistencies.

The other proposals either omit critical safety (B, C skip Obsidian Git) or over‑rotate on security to the point of impracticality (D). Proposal C’s “zero plugins” stance ignores the reality that Dataview is already installed and used—removing it would break existing MOCs. Proposal D’s security concerns are valid but can be mitigated by selecting only open‑source, locally‑executed plugins (like Obsidian Git) and auditing their code.

What solidifies my agreement with A is its explicit **list of signals to revisit**. This turns a static decision into a monitoring framework. For example, “failed retrieval rate >3/week” is a measurable trigger for re‑evaluating semantic search. That’s how performance‑aware architects operate.

**Therefore:**
- **Install Obsidian Git.** Configure auto‑commit on vault close, ignore workspace files, and push to a private repo.
- **Fix client normalization in `post_process.py`.** Add an `aliases.yaml` lookup and a one‑time patch script.
- **Add `_meta/schema.yaml`** and validate each extraction against it.
- **Do not install any other plugins.**
- **Monitor the signals** (note count, manual‑note ratio, failed retrievals) and revisit only when thresholds are crossed.

The vault is a read‑only viewer. Invest in the engine, not the dashboard.

*Latency: 117.17s | Tokens: 9544*

### Grok (grok-4.20-beta)

**Steelman A:** This is exactly right if the CKE pipeline remains under the solo engineer's full, ongoing control; the user truly never exceeds ~10% manual notes; FTS5 + 11 rich YAML fields deliver >90% recall on real presales workloads; and the dominant failure mode is "I installed one more plugin and now my ADHD brain is on fire." In that world, treating Obsidian as a pure read-only renderer and enforcing all contracts upstream is architecturally pristine.

**Assessment:** Disagree with its Position. The proposal correctly diagnoses the read-only nature but then draws the wrong boundary. It treats "cognitive overhead" as a flat scalar when it is not. For an ADHD presales engineer, the *real* cognitive cost is context-switching between a CLI and Obsidian, or failing to surface an obscure analogy during a live bid. A plugin that collapses that gap can be net-negative overhead even if it adds configuration surface.

**Strongest point:** The attack on dual sources of truth and the "fix at source" principle is ironclad. Metadata Menu is indeed a trap here.

**Weakest assumption:** That failed retrievals will be consciously logged and noticed ("log these 'failed retrieval' moments"). This is exactly what ADHD makes impossible. The user will simply feel vaguely uneasy and avoid the vault.

**Hidden assumptions:** 
1. That the YAML taxonomy is semantically complete — i.e., the machine extraction correctly tags every important concept. 
2. That the mental model of "I should use the right tool for the query" is sustainable at 2 a.m. before a client call.

**Overlooked risks:** Vault abandonment. The system becomes "correct but annoying" and the engineer drifts back to email search and memory. Also, the proposal underestimates how much value a good graph view provides even with zero manual links when you have 11 dimensions of metadata (Graph Analysis + Dataview can still produce useful views).

---

**Steelman B:** This is exactly right if the quantitative thresholds (semantic at 2k notes, manual notes at 20%) are empirically valid for *this* domain and the user's actual information scent is well-modeled by FTS5 recall numbers.

**Assessment:** Disagree. The thresholds feel pulled from general Zettelkasten advice rather than measured against presales work. Presales is a recall-heavy, analogy-heavy domain where "I vaguely remember something about chemical industry sustainability" is a real query. The proposal's confidence in 85% FTS5 recall feels like engineering copium.

**Strongest point:** The explicit quantification of trade-offs (2 extra context switches per day, 15% faster startup) is refreshing and rare.

**Weakest assumption:** That the user will actually run a post-process script monthly to fix normalization. In practice, that script becomes the new deferred maintenance debt.

**Hidden assumptions:** That search frustration is binary and noticeable rather than a slow erosion of trust in the system. Also assumes the user is primarily a "searcher" rather than a "browser/grazer" — many presales people browse by client or by topic cluster.

**Overlooked risks:** Progressive schema drift across the 8 MOCs. Without any enforcement mechanism, the Dataview queries slowly rot in ways that are hard to detect until a proposal is almost due.

---

**Steelman C:** This is exactly right if Obsidian is genuinely only a viewer and the engineer does 95% of their work in the `corp retrieve` CLI. In that world, any plugin is pure waste.

**Assessment:** Strongly disagree. This is the most ideologically pure but least realistic. Treating the vault as "just a viewer" while the user is a solo presales engineer with ADHD is self-deception. The whole point of having 587 extraction notes in Obsidian is to *see* them in a rich environment. Reducing it to "boring but correct" is how you kill adoption.

**Strongest point:** The observation that plugin count above 4 correlates with abandonment in solo vaults is the most empirically grounded claim in all four proposals.

**Weakest assumption:** That the pipeline will continue to be maintained. The proposal never confronts the possibility that CKE development momentum dies.

**Hidden assumptions:** That "shiny object anxiety" is the only reason someone would want better navigation. Ignores that the current setup has *zero* serendipity or associative recall.

**Overlooked risks:** The system becomes brittle to changes in the engineer's own workflow. If they suddenly need to start capturing meeting notes or proposal-specific synthesis (extremely common in presales), they have zero infrastructure and the "pure" system collapses.

---

**Steelman D:** This is exactly right if corporate security policy actually treats Obsidian plugins as meaningful supply-chain risk (most don't) and if the dominant threat model is "hostile plugin exfiltrates bid data."

**Assessment:** Disagree. This proposal tips into paranoia. The security argument is mostly theater — Smart Connections can run local embeddings (e.g. all-MiniLM-L6-v2). The "supply chain integrity" framing is used to justify an extreme minimalism that the actual problem doesn't require.

**Strongest point:** The blast-radius argument about machine-generated files being overwritten is correct and under-appreciated by the others.

**Weakest assumption:** That local embeddings in a plugin are meaningfully more complex than local embeddings in the CLI. The maintenance difference is smaller than claimed.

**Hidden assumptions:** That the user will never want to do any manual synthesis work *on top of* the extraction notes. The proposal assumes the vault remains 99% machine-generated forever.

**Overlooked risks:** Total disconnection between the machine corpus and any human insight. The proposal never addresses how the engineer captures "this note + that note = insight for this client" without creating some lightweight linking or annotation layer.

---

### Revised Recommendation

The four proposals reveal clear groupthink: "We are sophisticated engineers who understand that plugins are technical debt, the pipeline is the source of truth, and ADHD users must be protected from themselves through ascetic minimalism."

This is mostly true but misses the actual job.

**Install two plugins: Obsidian Git and Smart Connections (local embeddings only). Fix normalization in the pipeline. Reject everything else.**

This is not a compromise. It is a deliberate rejection of the "zero or only Git" consensus.

**Why the update?** Proposals A–D all assume the YAML taxonomy is sufficiently complete that semantic search delivers only marginal gains. That assumption is probably false for presales knowledge work. The value is not better *search* but better *discovery* of non-obvious connections across clients and domains — exactly what embeddings are good at and what a stressed pre-sales engineer with ADHD will not reliably tag. The "log your failed retrievals" advice is fantasy.

The maintenance cost of Smart Connections is overstated for local models on 587 notes (it is not re-embedding the entire vault on every change unless you configure it stupidly). The cognitive benefit of staying in one tool outweighs the configuration tax.

Git is non-negotiable for the reasons all four proposals articulate. Everything else (Templater, Metadata Menu, Kanban, etc.) is correctly rejected.

The contrarian truth: for this specific use case, *some* viewer complexity is justified precisely because the vault is mostly machine-generated. The machine gives you scale; the viewer needs to give you insight. Making it "boring but correct" is how you end up with 2,000 notes that nobody actually uses.

*Latency: 14.91s | Tokens: 8885*

## Synthesis (by openai, non-participant)

## Consensus

### Strong consensus
1. **Do not install Templater now.**
   - Reasoning was strong and consistent: the vault is machine-generated, read-only, and has **zero manual note creation**. Templater solves note creation and insertion problems that do not exist here.
   - Multiple participants independently grounded this in the architecture, not just preference.

2. **Do not install Metadata Menu now; fix normalization upstream.**
   - This was the clearest high-quality agreement in the debate.
   - The key shared argument: **“Lenzing vs Lenzing AG” is a data quality problem in the extraction pipeline, not a viewer problem.**
   - Strong evidence: if you normalize only in Obsidian, every other consumer—FTS5 CLI, future scripts, APIs—still sees bad data, creating split-brain behavior.

3. **Graph-style/link-based plugins are low value right now.**
   - Strongly supported by the facts: **zero wikilinks**, standalone extraction notes, no human-authored network.
   - Even the lone dissent about “serendipity” did not provide evidence that graph tooling would outperform existing metadata-based navigation in this vault.

4. **Do not add workflow plugins like Kanban, Calendar, Breadcrumbs, QuickAdd to this vault right now.**
   - This was well supported by fit-to-workflow reasoning.
   - Those plugins assume manual process management, time-based journaling, or authored hierarchy—none of which match a read-only machine corpus.

5. **Invest in the pipeline/CLI before investing in Obsidian plugins.**
   - Broad agreement, with mostly strong reasoning.
   - The vault is a rendered artifact of CKE; therefore schema enforcement, normalization, and advanced retrieval belong upstream unless Obsidian clearly becomes the primary working surface.

### Consensus with caveat / some groupthink
6. **Smart Connections is not clearly justified now.**
   - Most participants rejected it now, but some of the quantitative thresholds they cited (e.g. “2,000 notes”, “85% recall”, “300–500MB”) were asserted more than proven.
   - So the consensus direction is probably right, but some supporting numbers looked speculative and echoed across proposals.

7. **Keep the plugin count very low because of ADHD/cognitive overhead.**
   - This was probably correct, but some proposals repeated it as a universal principle without distinguishing between:
     - plugin count
     - plugin maintenance burden
     - context-switch cost between CLI and Obsidian
   - The minority correctly pointed out that one good plugin can reduce overhead if it eliminates tool switching.

---

## Unresolved Disagreements

### 1. Should you install any new plugin at all?
**Crux:** Is the vault best treated as a **thin read-only renderer**, or is there enough value in the viewing experience to justify adding capabilities inside Obsidian?

- **Side A:** Install **zero new plugins** (or at most Git outside Obsidian).  
  Argument: viewer should stay dumb; every plugin adds maintenance, update risk, and cognitive tax.
- **Side B:** Install **Obsidian Git**, maybe Smart Connections.  
  Argument: some viewer-side capability is worth it if it reduces friction or adds discovery.

**Stronger side:** **Side A, with one exception: versioning is still needed, but likely not via Obsidian Git plugin.**
- The strongest architectural argument in the debate was that **machine-generated notes get overwritten by pipeline reruns**, so viewer-side mutation tools are structurally wrong.
- That supports “thin viewer” strongly.
- However, total rejection of all tooling missed the need for **rollback/auditability** of batch runs.
- Best synthesis: **don’t add viewer complexity unless it clearly beats improving CKE/corp retrieve; do implement version control outside Obsidian.**

### 2. Smart Connections: overengineering or useful discovery aid?
**Crux:** Is current retrieval pain mainly a **search recall problem**, or a **workflow/curation problem**?

- **Majority view:** Skip Smart Connections now.
  - FTS5 already exists.
  - Dataview + YAML provide strong structured retrieval.
  - Smart Connections adds another search model, indexing overhead, and possible stale state.
- **Minority view:** Smart Connections may be valuable because presales retrieval is often **analogy-driven, fuzzy, and associative**, not exact-match.
  - The user may not notice “failed retrievals” explicitly.
  - Keeping discovery inside Obsidian may matter more than minimizing plugins.

**Stronger side:** **Skip it for now.**
- The minority raised a valid objection: fuzzy/conceptual retrieval may matter more in presales than the majority allowed.
- But it still did not show that **Obsidian-based semantic search** is the best place to solve that problem.
- Given the stated workflow—**corp retrieve is primary search**, vault is read-only—the stronger conclusion is:
  - **Do not install Smart Connections now**
  - If semantic search becomes necessary, first consider adding it to **corp retrieve**, where it aligns with the existing search workflow and avoids a second retrieval stack.

### 3. Obsidian Git plugin: yes or no?
**Crux:** Is the main problem **backup/version history**, and if so, should it be solved **inside Obsidian** or **in the pipeline/filesystem layer**?

- **Pro-Git-plugin side:** version history and rollback are important; plugin gives easy automation.
- **Anti-Git-plugin side:** Obsidian Sync + Obsidian Git plugin is a conflict-prone combination; machine-generated vaults benefit more from **pipeline-side Git commits** than UI plugin commits.

**Stronger side:** **Need version control, but avoid the Obsidian Git plugin.**
- This was the most convincingly resolved disagreement in round 2.
- The anti-plugin argument was stronger because it preserved the value of Git while eliminating the most plausible failure mode: **Git plugin + Obsidian Sync interaction** and meaningless UI-driven auto-commits.
- The best-supported synthesis is:
  - **Use Git outside Obsidian**
  - Commit after batch pipeline runs
  - Ignore `.obsidian/`

### 4. Security/supply-chain framing: central concern or overstated?
**Crux:** How much weight should be given to community plugin risk for a solo local vault with corporate data?

- **Security-heavy view:** community plugins are unvetted JS with filesystem access; avoid them.
- **Pragmatic view:** true in principle, but overemphasized relative to workflow fit and maintenance.

**Stronger side:** **Pragmatic view.**
- Security concerns were directionally valid, especially around plugins that may call external APIs.
- But the strongest anti-Smart-Connections arguments were not security; they were **duplication, maintenance, and mismatch with current workflow**.
- The security-heavy proposals became inconsistent when they kept Dataview but treated all other plugins as unacceptable.

---

## Argument Quality Assessment

### Best-reasoned proposals
1. **Claude Round 2 revised recommendation**
   - Best overall synthesis.
   - It improved on its own earlier position by recognizing that **version control is needed, but the Obsidian Git plugin is the wrong place to implement it**.
   - Strong because it matched the architecture: pipeline produces, Obsidian displays.

2. **Gemini Round 1**
   - Strong on the core architectural boundary: read-only viewer, source-of-truth upstream.
   - Weaker when it leaned too hard on security as the dominant reason.

3. **Grok Round 1**
   - Strong, practical minimalism.
   - Especially good at calling out “shiny object” risk and misfit plugins.
   - Weaker on backup/versioning.

### Weaker proposals / weaker parts
- **Deepseek’s quantitative thresholds** were useful heuristics but often presented with more precision than evidence.
- **Grok Round 2’s Smart Connections defense** raised important concerns about hidden search failure and vault abandonment, but did not establish that Smart Connections specifically—rather than improvements to corp retrieve or metadata quality—was the best remedy.
- **Gemini Round 2’s recommendation to remove Dataview** was the weakest major conclusion because it over-rotated on security and ignored current demonstrated utility: Dataview is already working and powers the 8 MOCs.

### Single strongest argument in the debate
**“A machine-generated vault that is regularly regenerated should not depend on viewer-side content fixes or enrichment, because pipeline reruns overwrite them. Fix at source.”**
- This cleanly defeats Templater and Metadata Menu for the current use case.
- It also reframes the whole decision: Obsidian is presentation, not authority.

### Single weakest argument in the debate
**“Uninstall Dataview because all community plugins are unacceptable supply-chain risk.”**
- Weak because it was inconsistent with the actual current system and unsupported by the stated environment.
- It replaced a concrete workflow discussion with a maximalist security posture not anchored in the user’s stated constraints.

---

## Blind Spots

1. **No one seriously examined whether core Obsidian built-ins already cover the remaining needs.**
   - E.g. saved searches, bookmarks, properties UI, workspaces, slash commands, starred files.
   - The debate focused almost entirely on plugins vs pipeline, not on using native features better.

2. **No one tested actual search quality.**
   - A lot of claims were made about FTS5 recall, semantic usefulness, thresholds like 1,500/2,000/5,000 notes.
   - None were based on observed query logs or side-by-side evaluation.
   - This is the biggest missing empirical piece.

3. **No one addressed note overwrite policy in operational detail.**
   - If notes are fully regenerated, what happens to any manual annotation at all?
   - This matters because the debate assumed read-only forever, but presales work often produces synthesis.
   - A better architecture might be **separate manual vault/folder** for human notes linked to machine extracts.

4. **The debate underexplored making corp retrieve available inside Obsidian without a plugin explosion.**
   - For example: URI handler, external tool launcher, generated result notes, or simple command wrappers.
   - That could reduce context switching without adding semantic plugins.

5. **No one discussed schema governance deeply enough.**
   - Strong agreement on source-level validation, but not much on:
     - allowed value registries
     - entity canonicalization strategy
     - migration handling for old notes
     - tests for MOC-breaking changes

6. **No one addressed whether 8 MOCs are enough or whether static generated indexes would be better than Dataview for stability.**
   - This was mentioned, but not evaluated.
   - If Dataview is your only active plugin need, static index generation could eventually remove even that dependency.

---

## Recommended Decision

### Decision
**Install no new Obsidian plugins right now.**
Keep **Dataview** as the only active functional plugin in use.
Do **not** install:
- Smart Connections
- Templater
- Metadata Menu
- Graph Analysis
- Kanban
- Calendar
- Breadcrumbs
- QuickAdd
- Obsidian Git plugin

Instead, invest in:
1. **CKE normalization and schema validation**
2. **Pipeline-side Git versioning**
3. **Measurement of real search failures before considering semantic search**

### Rationale
This is the best fit for the actual architecture and constraints:

- The vault is **99% machine-generated and read-only**
- **corp retrieve + FTS5 is already the primary search path**
- Dataview MOCs already work
- There are **zero wikilinks** and **zero manual notes**
- The user is solo and ADHD, so every plugin must justify ongoing attention cost

That combination makes most Obsidian plugins overengineering.

### Specific plugin calls

#### Smart Connections
**Decision: do not install now.**
- The strongest objection to skipping it was that presales retrieval is fuzzy and analogy-driven.
- That objection is real, but the evidence did not show that **Obsidian** needs a second search system today.
- Since **corp retrieve is already the primary search tool**, semantic retrieval—if later needed—belongs there first.

#### Templater
**Decision: overengineering.**
- There is no manual note authoring problem to solve.

#### Metadata Menu
**Decision: overengineering / wrong layer.**
- Normalize client/product/topic names in extraction/post-process.
- Viewer-side fixes create split-brain metadata.

#### Obsidian Git plugin
**Decision: skip the plugin, but do adopt Git outside Obsidian.**
- Version control is valuable.
- The plugin is not the best implementation because of Sync interaction risk and because commits should align with **pipeline batch events**, not UI editing events.

### Strongest objection acknowledged
The best argument against this minimal path was:
> staying in one tool matters, and semantic discovery may be more useful than exact search in presales.

Why that objection did not win:
- It identifies a possible future need, not a demonstrated current need.
- It does not prove Smart Connections is the right implementation point.
- With your architecture, adding search complexity to the CLI/pipeline is cleaner than adding a second retrieval stack inside Obsidian.

### If the debate is still uncertain anywhere
The only genuinely unresolved area is **semantic search need**.  
The debate was not conclusive because nobody presented actual retrieval failure data.

**What would resolve it:**
- 2–4 weeks of query logging from `corp retrieve`
- A small benchmark set of real presales queries:
  - exact known-item retrieval
  - fuzzy thematic retrieval
  - analogy/discovery retrieval
- Then compare:
  - FTS5 only
  - FTS5 + synonym expansion
  - local embedding search in CLI
  - Smart Connections

---

## Risks

1. **You may underinvest in discovery and miss relevant notes.**
   - Mitigation: log failed searches and review weekly; test semantic search later with real examples, not theory.

2. **Dataview remains a dependency.**
   - Mitigation: export or generate static MOCs from the pipeline as a fallback path; keep MOC logic simple.

3. **Pipeline fixes may be deferred, leaving metadata messy.**
   - Mitigation: make normalization/schema validation a blocking task before next batch import.

4. **No place for future manual synthesis notes.**
   - Mitigation: decide now whether human notes will live:
     - in a separate vault, or
     - in a separate non-regenerated folder excluded from CKE overwrites.

5. **Git outside Obsidian may not get used unless automated.**
   - Mitigation: make commit/push part of the extraction pipeline or scheduled script, not a manual habit.

---

## Action Items

1. **Do not install any new plugins now.**
   - Keep current setup: Obsidian + Dataview + existing MOCs.

2. **Fix metadata normalization in CKE.**
   - Add canonical alias mapping for clients/products/domains.
   - Run a one-time migration over existing 587 notes.

3. **Add schema validation upstream.**
   - Create `_meta/schema.yaml` or equivalent contract.
   - Validate required frontmatter fields and allowed values during extraction.
   - Fail pipeline on schema drift.

4. **Set up Git outside Obsidian.**
   - Initialize repo for the vault content.
   - Ignore `.obsidian/` or at minimum volatile workspace files.
   - Auto-commit after each CKE batch run with a generated message.
   - Push to a private remote.

5. **Instrument search before changing search tooling.**
   - Log `corp retrieve` queries.
   - Track obvious no-result/abandonment patterns if feasible.
   - Collect a short list of “I couldn’t find it” examples.

6. **Define revisit triggers.**
   - Consider semantic search only if:
     - failed retrievals become common, or
     - note count grows substantially, or
     - workflow shifts into Obsidian-first exploration.
   - Consider Templater/QuickAdd only if manual notes become a real workflow.
   - Consider static MOC generation if Dataview becomes unstable or undesirable.

7. **Decide a future manual-notes policy now.**
   - Separate vault or separate folder for human-authored notes.
   - Do not let regenerated extraction notes become the place for manual edits.

In short: **keep Obsidian boring, fix the producer, add measurement, and defer semantic/plugin complexity until you have evidence it’s needed.**
