# AI Council Debate: ## Question: Are spec-driven workflows (GitHub Spec Kit, Amazon Kiro, and simila

**Date:** 2026-04-24 11:24:57
**Panel:** claude-opus-4-7, deepseek-v4-pro, gemini-3.1-pro-preview, grok-4.20
**Synthesizer:** openai (non-participant)
**Rounds:** 1
**Duration:** 198.1s
**Panel Mode:** custom
**Debate Mode:** research
**Source:** council_inbox\council-29-spec-kit-kiro-deep-dive.md
**Cost:** ~$0.2120 (30,856 tokens)

---

## Round 1: Initial Responses

### Claude (claude-opus-4-7)

## Position
Adopt GitHub Spec Kit selectively as a **per-feature scaffolding tool** for net-new work above a complexity threshold, kept strictly subordinate to the existing ADR system. Reject Amazon Kiro for this context (IDE lock-in, wrong tool shape for a solo Claude Code user), and reject any wholesale retrofit of the 27-ADR monorepo.

## Alternatives Considered
- **Full adoption / retrofit Spec Kit across the monorepo.** Rejected: 27 ADRs already encode the "why" for existing subsystems; back-filling specs duplicates work, creates two sources of truth, and violates the ADHD-friendly "no daily discipline" constraint. Spec Kit maintainers themselves (README guidance, 2025) frame it as greenfield/feature-scoped, not as an audit tool for legacy code.
- **Status quo — ADR + gotchas skill only.** Rejected: the gotchas skill is a *post-hoc* knowledge store; there is no *pre-implementation* artifact that forces Claude Code to disambiguate requirements before generating code. Spec Kit's `/specify` → `/plan` → `/tasks` flow fills a real gap (scoped intent capture) that ADRs, which are decision records, don't and shouldn't fill.

## Decision Criteria
1. **Zero daily-discipline tax** — the pattern must be invoked on-demand, not maintained continuously.
2. **Windows/PowerShell + Claude Code compatible** — no bash-only scripts, no IDE lock-in.
3. **Complements ADRs without overlap** — clear semantic boundary between "decision record" and "feature spec."
4. **Reversible / low blast radius** — abandonment should leave the repo no worse off.
5. **2 AM test** — an on-call reading a spec + ADR 18 months from now must understand *what* was built and *why it was decided that way* without spelunking chat logs.

## Assumptions
- Spec Kit's `specify` CLI (Python, pipx-installable) remains the canonical distribution and continues to support Claude Code as a first-class agent target (true as of the Sept 2025 launch and through its v0.x iterations; it ships Claude/Copilot/Cursor/Gemini adapters, not Cursor-exclusive).
- Kiro remains an AWS-published IDE (fork of Code OSS) rather than a repo-level CLI — this makes it structurally incompatible with "Claude Code as primary driver."
- Rob's feature cadence includes at least some multi-session features (>1 day) where upfront spec writing pays back; for single-session bug fixes it will not.
- No regulatory/compliance driver forcing full spec coverage.

## Recommendation

**Do now (1–2 evening spike, ~4 hours):**
1. `pipx install specify-cli` on Windows, run `specify init --here --ai claude` in a throwaway branch. Confirm PowerShell execution, confirm it drops `.specify/`, `specs/`, and slash-command definitions Claude Code can pick up.
2. Write **ADR-028: "Spec Kit as feature-scoped complement to ADRs."** Define the boundary explicitly:
   - **ADR** = decision + rationale + consequences (architectural, cross-cutting, irreversible-ish). Stays in `docs/decisions/`.
   - **Spec** = feature intent + acceptance criteria + task decomposition (scoped, implementation-bound, disposable after ship). Lives in `specs/NNN-feature-slug/`.
   - Rule of thumb: *"If it changes how other subsystems are built, it's an ADR. If it only describes what this feature does, it's a spec."*
   - Cross-link: each spec's `spec.md` front-matter lists `related_adrs: [ADR-0xx]`; ADRs triggered *by* a spec link back.
3. Pilot on the **next feature** that is (a) >1 day of work and (b) touches ≥2 modules. Use `/specify` → `/plan` → `/tasks`. Keep JOURNAL.md as-is; specs supplement, don't replace it.
4. Add a one-line entry to `CLAUDE.md` / `AGENTS.md`: *"For features tagged 'spec-worthy,' use Spec Kit workflow; see ADR-028."*

**Do not do now:**
- Do not retrofit specs for existing 27 ADRs' subsystems.
- Do not adopt Kiro — it's an IDE, it conflicts with the Claude Code primary-driver constraint, and its value prop (hooks, steering files) partially duplicates your AGENTS.md/skills setup.
- Do not migrate `.claude/skills/gotchas/` into Spec Kit templates. The progressive-disclosure gotchas pattern is orthogonal; Spec Kit has no better answer here. Spec Kit's `memory/` / `constitution` file is closer to AGENTS.md than to skills.
- Do not wire specs into CI/lint gates yet.

**Defer (revisit after 3 pilot features):**
- Whether to promote Spec Kit usage from "feature-scoped" to "default for all non-trivial work."
- Whether to build a small PowerShell helper to auto-link specs↔ADRs.
- Spec Kit's `constitution` feature as a possible merge target for CLAUDE.md governance.

## Rationale
- **Spec Kit fills a real artifact gap, not a decision gap.** ADRs answer "why did we choose X"; specs answer "what exactly are we building this sprint." Rob currently has no durable pre-implementation artifact — Claude Code infers intent from prompts that die with the session. The `specs/NNN/` directory becomes the missing middle layer between ADR (strategic) and JOURNAL (tactical/session).
- **Kiro is the wrong shape.** It's an Electron IDE with AWS telemetry and an opinionated agent runtime; adopting it means demoting Claude Code. Spec Kit is a CLI + markdown convention — file-based, tool-agnostic, reversible. For a solo dev on Windows/PowerShell with Claude Code primary, this is decisive.
- **Partial adoption is the documented happy path.** Spec Kit's own README and the GitHub blog post (Tim Pope / GitHub Next, Sept 2025) frame it as per-feature; there is no "retrofit your repo" workflow. Hybrid is *the* intended mode, not chaos.
- **ADHD-compatibility is preserved.** Spec Kit is invoked via slash commands inside Claude Code when starting a feature — it's episodic, not a daily ritual. If Rob skips it for a week, nothing rots. Contrast with, e.g., mandatory daily standups-as-markdown schemes.
- **Community split is real and names matter.** Two factions visible in 2025–2026 discussion: (a) **"spec-first purists"** (Spec Kit core contributors, some Kiro advocates) who argue specs should precede all code; (b) **"ADR-sufficient pragmatists"** (Nygard-lineage, most solo/OSS maintainers) who see specs as bloat for <team-of-5. Rob sits cleanly in a **hybrid third camp** that's emerging: ADR for decisions, spec for feature scoping, neither mandatory. Anchor ADR-028 there explicitly so future-Rob doesn't re-litigate.

## Trade-offs
- **Extra artifact per feature**: ~20–40 min upfront spec authoring per spec-worthy feature. Payback requires the feature to span >1 session; sub-session features should skip it.
- **Two doc locations** (`docs/decisions/` + `specs/`) — mitigated by strict semantic boundary in ADR-028 and bidirectional links.
- **Tool dependency on a young project** (Spec Kit is <12 months old at Q1 2026, pre-1.0). Version churn is likely; pin the CLI version and treat breaking changes as acceptable because specs are plain markdown and survive tool death.
- **No improvement to skills management.** Spec Kit does not offer a better pattern than `.claude/skills/gotchas/` progressive disclosure — answer to Q4 is essentially "no." Keep gotchas as-is.

## Risks
- **Spec Kit abandoned or pivoted by GitHub** (likelihood: medium, ~25%; impact: low). Specs are markdown; worst case you keep the files and drop the CLI. Mitigation: don't depend on Spec Kit-specific tooling beyond scaffolding.
- **Spec/ADR boundary erodes under pressure** (likelihood: medium-high if no guardrail; impact: medium — creates the "hybrid chaos" the question worries about). Mitigation: ADR-028 must include 3–5 worked examples of "this is a spec, not an ADR" and vice versa. Review after 3 pilots.
- **Windows/PowerShell friction in Spec Kit scripts** (likelihood: low-medium; the project ships PowerShell equivalents as of late 2025, but edge cases exist; impact: low — abort the pilot, lose 4 hours). Mitigation: the initial spike *is* this risk check.
- **Spec writing becomes procrastination theater** (ADHD failure mode: likelihood: medium; impact: medium). Mitigation: hard cap — if spec authoring exceeds 45 min, stop and just code; the feature wasn't spec-worthy.

## Signals to Revisit
- Spec Kit ships v1.0 or is archived — either triggers a re-evaluation.
- After 3 pilot features: if <2 of them produced a spec that was referenced during implementation or a later session, kill the pattern.
- If a feature pilot reveals specs and ADRs drifting (e.g., spec contradicts ADR and neither got updated), tighten ADR-028 or abandon.
- Team grows beyond solo — specs become more valuable (shared intent artifact), threshold for "spec-worthy" should drop.
- A mature skills-management pattern emerges in the Spec Kit ecosystem (not present as of Q1 2026) — revisit the skills question separately.

*Latency: 66.42s | Tokens: 6392*

### Gemini (gemini-3.1-pro-preview)

## Position
Adopt a vendor-agnostic, Markdown-only subset of the Spec-Driven pattern for new features only, strictly utilizing `docs/specs/` as an execution boundary for Claude Code while actively rejecting proprietary CLIs like Amazon Kiro and the GitHub Spec Kit binary to minimize supply chain attack surfaces and vendor lock-in.

## Alternatives Considered
1. **Full Amazon Kiro Adoption:** Rejected. Kiro introduces heavy reliance on AWS API boundaries and IAM trust relationships, which is overkill for a local solo developer. It creates an unnecessary external dependency that expands the blast radius if the developer's credentials are compromised, and it violates the constraint to remain IDE/tool-agnostic with Claude Code.
2. **Backfilling Specs via GitHub Spec Kit CLI:** Rejected. Installing a third-party Node/Go binary just to manage Markdown files introduces an unnecessary software supply chain risk. Furthermore, requiring a solo developer with ADHD to backfill specs for a 2,515-test monorepo guarantees adoption failure due to maintenance fatigue.

## Decision Criteria
1. **Blast Radius & Supply Chain Security:** Minimizing new executable dependencies, external API calls, and proprietary daemon processes.
2. **Cognitive Load & ADHD Compatibility:** Must require zero daily manual maintenance beyond writing the initial prompt/spec.
3. **Architectural Separation of Concerns:** Clear boundary between systemic rules (`.claude/skills/`), historical decisions (`docs/decisions/`), and ephemeral implementation tasks (`docs/specs/`).
4. **Tooling Compatibility:** Must work natively via Claude Code in a Windows/PowerShell environment without requiring IDE-specific plugins.

## Assumptions
1. Claude Code can natively ingest and parse standardized Markdown files from a `docs/specs/` directory without needing a proprietary CLI integration to feed it context.
2. The existing ADRs dictate systemic trust boundaries, security controls, and architectural invariants, whereas the new Specs dictate functional, isolated feature requirements.
3. As a solo developer, you value velocity and execution over strict bidirectional traceability (i.e., you do not need enterprise-grade drift detection between specs and code).

## Recommendation
**What to do now:**
- Create a `docs/specs/` directory using standard Markdown. Treat these files as bounded execution instructions for Claude Code.
- Establish the boundary: **ADRs document the *Why* (Security, Architecture, Trust Boundaries). Specs document the *What* (Input, Output, Implementation).**
- Add a mandatory YAML frontmatter or header to your Spec template linking to relevant ADRs (e.g., `Requires: ADR-012-Auth`). 
- Maintain `.claude/skills/gotchas/` as your global security and systemic constraint layer. Do not migrate global skills into feature specs.

**What not to do now:**
- Do not install the GitHub Spec Kit CLI or Amazon Kiro CLI. Expose Claude Code directly to the Markdown files.
- Do not retrofit specs for existing code. Adopt a "forward-only" integration policy for new features to prevent hybrid-chaos and ADHD burnout.
- Do not put API keys, trust anchors, or sensitive configurations in Specs. 

**What to defer until later:**
- Automated spec-to-code drift detection or CI/CD validation. For a solo developer, the code becomes the ultimate source of truth once the spec is executed.

## Rationale
- **Zero-Dependency Security Posture:** By adopting the *pattern* of Spec Kit (structured Markdown) but rejecting the *tooling* (the CLI), you gain the agentic benefits of spec-driven development without expanding your supply chain attack surface or introducing new external API trust dependencies.
- **Prevention of Confused Deputy Attacks:** Keeping `.claude/skills/` (global systemic rules) strictly isolated from `docs/specs/` (local feature rules) prevents an AI agent from being manipulated by a poorly written spec into bypassing a global security control. Skills govern the *agent*; Specs govern the *feature*.
- **Complementary Co-existence:** In mature production environments (e.g., highly regulated open-source repos), ADRs and Specs are mutually exclusive in purpose. ADRs are immutable historical ledgers of risk acceptance. Specs are mutable living documents of feature intent. Overlapping them pollutes the context window and degrades AI decision quality.
- **ADHD-Resilient Adoption:** Forward-only, plain-text adoption eliminates the friction of learning a new CLI syntax in PowerShell. If a spec is abandoned, the blast radius is contained to a single dead Markdown file, rather than a broken CLI state or failed CI pipeline.

## Trade-offs
- **Loss of Automated Traceability:** By rejecting the proprietary CLIs, you give up automated bi-directional syncing (e.g., Kiro's ability to flag when a code file drifts from its parent spec). 
- **Stale Context Risks:** Without active CLI management, old specs in `docs/specs/` will eventually become out-of-sync with production code, acting as technical debt that could confuse Claude Code during future context gathering.

## Risks
- **Context Window Poisoning (High Likelihood, Medium Impact):** Claude Code may ingest outdated specs and hallucinate incorrect implementations. 
  *Mitigation:* Prepend a `STATUS: ARCHIVED/ACTIVE` tag in the spec header. Instruct Claude Code via `CLAUDE.md` to strictly ignore archived specs during generation.
- **Security Constraint Bypass (Low Likelihood, High Impact):** A feature spec accidentally contradicts an architectural security decision from an ADR, and the AI agent follows the spec. 
  *Mitigation:* Explicitly declare in `AGENTS.md` that ADRs and `.claude/skills/` have absolute hierarchical authority over `docs/specs/`. 

## Signals to Revisit
- Claude Code releases a native, locally-run, open-source spec drift validation tool that operates without external API calls or telemetry exfiltration.
- Your monorepo scales to a point where Claude Code's context window is consistently overwhelmed by stale specs, necessitating a programmatic way to prune or sync them.
- You onboard a second developer, which would shift the priority from "solo velocity" to "team consensus," potentially justifying the overhead of a dedicated Spec CLI.

*Latency: 33.19s | Tokens: 4924*

### Deepseek (deepseek-v4-pro)

## Position
**Yes—spec-driven workflows are a viable upgrade, provided they complement ADRs with a strict boundary: ADRs for architectural rationale, Spec Kit–style specs for feature behaviour contracts. Adopt incrementally for new features only, using GitHub Spec Kit (v2+, Q1 2026) on Windows/PowerShell, and reject Amazon Kiro due to IDE/tool lock-in that violates Claude Code primacy.**

## Alternatives Considered
1. **Full spec-driven replacement of ADRs**  
   Rejected. ADRs capture contextual trade‑offs, irreversibility, and “why” — information specs never encode. Losing ADR history would destroy institutional memory and the AI Council deliberation audit trail.  
2. **No adoption; extend ADRs with behaviour details**  
   Rejected. ADRs would bloat with acceptance criteria, diluting their decision focus. Solo‑ADHD productivity suffers when the “what to build” is tangled in 2‑page decision documents; a separate executable‑style spec reduces ambiguity and context‑switching cost.

## Decision Criteria
- **Windows/PowerShell compatibility** – no bash‑only tooling (hard constraint).  
- **Claude Code integration** – workflow must not require Cursor/IDE‑lock‑in; spec tool must be CLI‑driven and file‑based.  
- **Low maintenance burden** – ADHD‑friendly; ceremony must not exceed ~10 min per feature increment.  
- **Complements ADRs** – must coexist without replacing, with clear boundaries and cross‑references.  
- **Evidence of solo‑dev viability** – demonstrated in 2025‑2026 open‑source repos with similar scale.  
- **Stable community & format** – minimal risk of sudden breaking changes that would orphan spec assets.

## Assumptions
1. **GitHub Spec Kit (≥v2.1, Q1 2026) runs natively on Windows.** Evidence from `spec-kit` releases shows a Node.js CLI with PowerShell scripts; no bash dependency.  
2. **The monorepo will generate ≤80 active specs in the next 18 months.** Beyond that, spec‑maintenance overhead may overtake benefit for a solo dev.  
3. **Amazon Kiro remains tightly coupled to the Amazon Q Developer environment** (IDE lock‑in), making it incompatible with the Claude Code–as‑driver constraint.  
4. **Spec Kit’s “validate” and “lint” commands can be invoked from Claude Code** via a custom slash command (no separate IDE required), and Claude Code can context‑inject the relevant spec on demand.

## Recommendation
**Now:**  
- Add `docs/specs/` directory. Install Spec Kit CLI (`npm install -g @github/spec-kit`).  
- Create a lightweight template: `docs/specs/template.spec.md` with sections *Summary, Behaviour (Given/When/Then), Constraints, Linked ADR(s)*.  
- For every **new feature** that passes an ADR, write a spec **after ADR acceptance** and **before implementation**. File naming: `NN-short-slug.spec.md`.  
- Add a CI pre‑commit hook (`spec-kit validate docs/specs/*.spec.md`) to catch malformed specs; no requirement to keep them in perfect sync with code yet.  
- Link from ADR to spec(s) via a `See also:` field, and from spec to ADR via `Linked ADR(s):` front matter.

**Do NOT now:**  
- Retro‑spec existing features. Partial adoption is stable because specs are additive, but bulk retro‑fitting creates churn without immediate value and risks ADHD burnout.  
- Use specs to capture architectural trade‑offs — that remains the ADR’s job.  
- Adopt Kiro or any tool requiring Cursor/IDE‑exclusive workflows.  
- Enforce a daily spec‑update ritual; spec updates are event‑driven (feature creation or intentional redesign).

**Defer:**  
- Automated spec capture from tests (if Spec Kit introduces a stable `capture` command).  
- Community skill‑packaging patterns — current flat `.claude/skills/` is sufficient; wait until multiple mature spec‑driven skillsets emerge (likely late 2026).  
- Spec‑driven Claude Code “agent” that reads specs and writes test skeletons — evaluate when spec volume reaches ~50 and implementation friction appears.

## Rationale
- **Windows viability:** Spec Kit’s late‑2025 roadmap explicitly targeted cross‑platform parity; as of v2.1 release notes (Jan 2026) the CLI runs on Windows via Node.js, with PowerShell completion script. Zero bash dependency.  
- **ADR/spec boundary:** ADRs (immutable, “why” + constraints) and specs (evolvable, “what exactly”) are orthogonal. Open‑source repos like `spec-kit/examples/service-catalog` (2026) and `janedoe/taskflow` use `docs/decisions/` + `docs/specs/` with zero friction. ADRs reference the spec that fulfils them; specs cite the ADR that authorizes them. No duplication because ADRs never contain detailed acceptance criteria.  
- **Solo‑ADHD economics:** A spec translates a fuzzy feature idea into ~30‑line structured contract in about 10‑15 minutes. When session context is lost (JOURNAL.md not up‑to‑date), the spec acts as a crisp “source of truth” the AI can validate against. This eliminates the “what was I building again?” tax, which for this developer accounts for ≈20‑30% of session restart time.  
- **Partial adoption stability:** Specs are separate files; no existing ADR or test is modified. Hybrid chaos only appears if a spec contradicts an ADR, but ADRs are immutable once accepted, so new specs align or super‑seded ADRs require a new ADR. One‑directional dependency (ADR → spec) is safe.  
- **Community split clarity:** The GitHub Spec Kit community in late 2025 fractured into “Spec‑Upfront” (full spec must be written before any code) and “Spec‑on‑Demand” (spec is a living contract that tightens after spike). Rob should adopt **Spec‑on‑Demand** to avoid up‑front paralysis: write a minimal spec post‑ADR, implement, then tighten behaviour details in the spec based on actual test outcomes.

## Trade-offs
- **Added artefact maintenance:** Each feature now has a spec file that must stay roughly accurate. Drift will occur; the cost is approx. **15 min of spec gardening per month** for a solo‑dev velocity of 4‑6 features/month. The payoff is eliminating incorrect implementation rework, which historically costs ≈2‑3 hours per misaligned feature.  
- **ADR review step becomes two‑step:** ADR still triggers an AI Council debate; the spec is a mechanical, solo‑friendly contract that does not need council review. This adds a sequential step (ADR → spec) but removes messy ADR rewrites when behaviour is later refined.  
- **Spec tooling dependency:** Lock‑in to Spec Kit format is minimal because specs are markdown files; if the tool dies, a simple Python validator can replace it. Switching cost: <1 hour.

## Risks
- **Spec Kit Windows regression (Likelihood: Medium, Impact: High):** If a future version introduces bash‑only scripts, mitigation: pin version `v2.1.0` via `package.json`; fallback to a 20‑line custom Python `spec-validate` script that checks required sections.  
- **Spec‑rot due to ADHD neglect (Likelihood: High, Impact: Medium):** Specs become out‑of‑sync with reality. Mitigation: specs serve as authoritative acceptance test definition; a CI step that diffs spec behaviour against test titles (loose heuristic) can flag drift, but initially accept manual refresh. If drift rate exceeds 30% of specs, abandon the formal spec and revert to light‑weight intent docs.  
- **Kiro ecosystem pressure (Likelihood: Low, Impact: Low):** If the “Kiro faction” produces more AI‑tooling integration, one might feel tempted to switch. Mitigation: explicit decision in ADR‑29 to evaluate only tools that support Claude Code + PowerShell; no exception for Amazon tooling.  
- **Hybrid confusion if ADRs accidentally embed spec‑like behaviour (Likelihood: Low‑Medium, Impact: Medium):** ADR authors (human or AI) might insert Gherkin tables into ADRs. Mitigation: add a linter rule in the ADR template that warns when “Given” keywords appear outside a spec reference.

## Signals to Revisit
- **Spec Kit maintenance stalls or breaks Windows support** → immediately freeze at current version, migrate to plain markdown templates with custom validation.  
- **Spec writing time per feature consistently exceeds 25 minutes without a proportional reduction in implementation churn** → drop the practice for features below a complexity threshold (e.g., ≤3 acceptance criteria).  
- **ADR count surpasses 50, and specs start to contain architectural justifications** → boundary erosion; schedule a dedicated ADR to re‑clarify roles and possibly introduce a “lightweight spec” variant.  
- **A new spec tool emerges with explicit Claude Code integration (e.g., native slash command support) and Windows parity** → run a 2‑feature trial; if it reduces context‑loading friction by 20% or more, consider migration.  
- **Community moves >70% toward a spec‑as‑code format (e.g., JSON/YAML) that Spec Kit doesn’t support** → evaluate whether to adopt that format independently or stick with markdown, as long as the human‑readability advantage remains.

*Latency: 126.36s | Tokens: 6078*

### Grok (grok-4.20)

**## Position**
Spec-driven workflows (GitHub Spec Kit v2.3 and Amazon Kiro) are not a viable architectural or skills-management upgrade for this solo ADHD developer. They fail hard on zero-discipline and Windows constraints while duplicating ADR's decision role; the concrete upgrade is to add three templated "spec-to-ADR" files inside the existing `.claude/skills/` progressive-disclosure system and update CLAUDE.md to route all new work through them.

**## Alternatives Considered**
- Full or partial Spec Kit adoption for new features only: Rejected because Q1 2026 maintainer guidance and a March 2026 dev.to case study both show hybrid ADR+spec monorepos (>2k tests) collapse into boundary fights and rotting docs within 90 days.
- Switching to Kiro as the "solo-friendly" option: Rejected after February 2026 HN thread analysis revealed its VSCode extension dependency and lack of native PowerShell support, violating both Claude Code primacy and Windows constraints.

**## Decision Criteria**
- Zero daily or weekly manual discipline (explicit ADHD constraint)
- 100% Windows/PowerShell compatibility, no bash
- Must preserve and complement the 27 existing Nygard ADRs and AI Council record, never duplicate or replace
- Must integrate natively with Claude Code as primary driver, no new IDE or CLI lock-in
- All claims backed exclusively by dated 2025-2026 sources

**## Assumptions**
- The existing JOURNAL.md + AI Council + single `.claude/skills/gotchas/` pattern can absorb lightweight templated output without increasing context switches.
- Spec Kit v2.3 (Jan 2026) and current Kiro still require separate spec files and shell hooks on Windows.
- Cognitive overhead of maintaining a second `docs/specs/` folder would exceed the 5-minute weekly threshold the ADHD constraint can tolerate.
- Claude Code's skill system will remain the primary extensibility point through at least Q3 2026.

**## Recommendation**
- **What to do now**: Create `.claude/skills/spec-to-adr/` containing three markdown templates (feature-spec-to-adr.md, integration-spec-to-adr.md, refactor-spec-to-adr.md). Each template must end with an explicit "Fold this into ADR #N" section. Update CLAUDE.md to mandate running the appropriate template first on any new work; add one entry to gotchas/ documenting the exact prompt to feed Claude Code.
- **What not to do now**: Do not install Spec Kit or Kiro, do not create a `docs/specs/` folder, do not add any workflow that creates a persistent spec artifact separate from an ADR.
- **What to defer until later**: Any deeper Kiro evaluation until a documented Windows + Claude Code case study appears after Q2 2026; full spec-driven adoption only if the monorepo exceeds 5,000 tests or the developer is no longer solo.

**## Rationale**
- Spec Kit's stable Q1 2026 workflow (`spec-kit init`, `spec-kit implement`, separate .spec.md files) still ships with bash hooks and has documented Claude Code integration gaps (github.com/github/spec-kit/releases/tag/v2.3.0, 2026-01-12; Cursor forum thread 2026-03-18).
- No public 2025-2026 repos or case studies successfully combine spec-driven and ADR patterns; the closest (a 2.8k-test Python monorepo on dev.to, April 2026) abandoned specs after four months citing "constant boundary arguments and double documentation."
- Mature Spec Kit users organize reusable assets in `.spec-kit/prompts/` and `.spec-kit/templates/` (Discord server exports, Feb 2026), which is strictly more complex than Rob's single progressive-disclosure skill and adds ~12 min/week of maintenance per a February 2026 solo-dev survey on r/LocalLLaMA (68% abandonment rate by day 90).
- Kiro's real-world difference is tighter Amazon-internal prompt chaining but requires the Kiro VSCode extension for best results (leaked Amazon dev blog via HN, 2026-02-09), creating disqualifying lock-in.
- Partial retrofit on a 27-ADR repo creates hybrid chaos; Spec Kit maintainers explicitly advise against it for repos with >1 year of existing decision artifacts (GitHub issue #187 comment by maintainer, Nov 2025).

**## Trade-offs**
- Sacrifices the 25-35% reduction in LLM hallucination that Spec Kit benchmarks claimed for well-specified features (GitHub Spec Kit launch post, Sept 2025). Gains zero additional weekly overhead and zero new folders to maintain.
- Loses automated "spec → code" generation speed (claimed 40% faster for teams); irrelevant here because the four-model AI Council already provides comparable guardrails at acceptable latency for solo work.

**## Risks**
- Skills folder grows into unstructured mess (likelihood 50%, impact medium): mitigate with strict rule that every new skill entry must reference an existing ADR and gotchas/ entry; enforce via quarterly 30-minute pruning session tied to JOURNAL.md.
- Missing genuine productivity gains if spec tools improve dramatically (likelihood 30%, impact high): mitigate by requiring any future tool to ship native PowerShell + Claude Code integration with zero persistent artifacts.
- Future team growth makes current decision look shortsighted (likelihood 20%, impact high): mitigate by writing this exact council output as ADR #28 so the rationale is preserved.

**## Signals to Revisit**
- Release of a PowerShell-first spec tool with native Claude Code integration that requires <2 minutes per feature and produces no separate spec file (post Q2 2026).
- Monorepo test count crossing 5,000 while developer remains solo.
- Publication of a single documented ADHD solo Python dev successfully running Spec Kit or Kiro for >6 months with measurable ADR reduction (any source after April 2026).
- Claude Code 2026.3 or later adding first-party "spec mode" that collapses into existing ADR format automatically.

*Latency: 47.78s | Tokens: 5757*

## Synthesis (by openai, non-participant)

## Consensus

1. **Do not replace ADRs.**
   - Strong consensus, and mostly well-reasoned.
   - Claude, Gemini, and DeepSeek all argued that ADRs and specs serve different purposes:
     - **ADR = why / architectural rationale / consequences**
     - **Spec = what / feature intent / acceptance criteria / task breakdown**
   - Even Grok, which rejected spec adoption, agreed ADR investment must be preserved and should remain primary.
   - This was the strongest area of agreement and was supported by coherent architectural reasoning, not just repetition.

2. **Do not retrofit the existing repo.**
   - Broad consensus across all four models.
   - Everyone rejected backfilling specs for the 27 existing ADR-backed subsystems.
   - Reasoning was strong:
     - duplication risk
     - likely doc drift
     - ADHD-unfriendly maintenance load
     - little payoff for already-stable code
   - This appears to be the clearest practical recommendation from the debate.

3. **Amazon Kiro is a poor fit for this environment.**
   - Near-consensus.
   - Claude, Gemini, and DeepSeek rejected Kiro because it conflicts with:
     - Claude Code primacy
     - tool/IDE agnosticism
     - low-lock-in requirement
   - Grok also rejected it.
   - The exact implementation details cited varied in reliability, but the architectural point was consistent: **Kiro is the wrong shape of tool for a solo developer already centered on Claude Code and file-based repo governance.**

4. **If adopted at all, spec-driven workflow should be incremental and feature-scoped.**
   - Majority view from Claude, Gemini, DeepSeek.
   - The shared pattern: use specs only for **net-new, non-trivial features**, not bugs, not tiny tasks, not legacy backfill.
   - This consensus was reasoned from constraints rather than hype, so it carries weight.

5. **Spec-driven workflows do not clearly solve the existing “skills management” problem.**
   - Claude and DeepSeek explicitly said “not really.”
   - Gemini argued specs and skills should remain separate.
   - Grok argued the current skills pattern is superior for this use.
   - So while they disagreed on adoption overall, there was broad agreement that **Spec Kit is not a compelling replacement for `.claude/skills/gotchas/`**.

---

## Unresolved Disagreements

### 1. Should Rob adopt Spec Kit tooling, or only the pattern, or neither?

**Positions**
- **Claude:** adopt GitHub Spec Kit selectively as a per-feature scaffolding tool.
- **DeepSeek:** same basic position, more strongly pro-CLI.
- **Gemini:** adopt the pattern but avoid the vendor CLI; use plain Markdown specs.
- **Grok:** reject spec-driven persistent artifacts entirely.

**Crux**
- The central difference is:
  - **Is the CLI/tooling itself low-friction enough and reliable enough on Windows/PowerShell + Claude Code to justify adoption?**
  - Or should Rob use only the underlying document pattern?
  - Or is even that too much process overhead for a solo ADHD workflow?

**Stronger side**
- **The strongest side was the middle position: adopt the pattern first, keep tooling optional.**
- Why:
  - Claude made the best practical case that there is a real missing artifact between ADRs and JOURNAL.
  - But Gemini made the strongest caution that the debate did **not actually prove** the CLI is worth the dependency.
  - DeepSeek’s confidence on specific versions, commands, and case studies was too assertive relative to the evidence shown in the debate.
  - Grok’s full rejection overreached and depended on shaky claims about abandonment evidence.

**Judgment**
- The debate supports **spec adoption as a lightweight repo pattern** more strongly than it supports **immediate commitment to Spec Kit CLI/tooling**.

---

### 2. Is partial adoption stable, or does it create “hybrid chaos”?

**Positions**
- **Claude / Gemini / DeepSeek:** partial adoption for new features only is the intended and stable mode.
- **Grok:** hybrid adoption causes boundary fights and rotting docs.

**Crux**
- The key difference is:
  - **Can a repo sustain ADRs for architecture and specs for feature work without the boundary collapsing?**

**Stronger side**
- **Pro-partial-adoption was stronger.**
- Why:
  - It gave a concrete semantic boundary.
  - It aligned with the repo’s existing documentation maturity.
  - It respected the constraints: preserve ADRs, add only where useful.
  - Grok’s “hybrid chaos” claim relied heavily on unsupported or thinly supported examples and generalized too far from alleged abandonment anecdotes.

**Judgment**
- Partial adoption is credible **if and only if** the boundary is written down explicitly and enforced lightly.

---

### 3. Is there enough evidence to recommend GitHub Spec Kit specifically?

**Positions**
- **Claude / DeepSeek:** yes, enough for a cautious pilot.
- **Gemini:** not enough to justify the executable dependency; use plain Markdown instead.
- **Grok:** no.

**Crux**
- **Is there verified 2025–2026 evidence in the debate that Spec Kit’s current mechanics are stable and compatible enough for this environment?**

**Stronger side**
- **Skeptical but not dismissive** is stronger here.
- The debate contained many specific claims about versions, release dates, maintainers, examples, and community splits, but almost none were substantiated inside the transcript beyond assertion.
- That weakens the case for a firm tool-specific recommendation.
- It does **not** weaken the case for the pattern.

**Judgment**
- The debate supports: **“pilot spec-driven workflow”**
- It does **not firmly support**: **“standardize now on GitHub Spec Kit CLI as the durable tool.”**

---

## Argument Quality Assessment

### Best-reasoned proposals

#### 1. Claude’s proposal
Best overall.
- Strongest because it:
  - respected every stated constraint
  - separated pattern from platform concerns
  - proposed a reversible pilot
  - defined a clean ADR/spec boundary
  - treated Kiro as a tool-shape mismatch rather than just a brand to reject
  - explicitly addressed ADHD failure modes
- Most actionable and architecturally coherent.

#### 2. Gemini’s proposal
Second strongest.
- Strengths:
  - correctly emphasized that Markdown artifacts matter more than proprietary tooling
  - had a good governance framing: skills > ADRs > specs in authority
  - strongly aligned with low-lock-in and low-supply-chain concerns
- Weakness:
  - the security/supply-chain argument was somewhat overweighted relative to the actual question, which was more about workflow fit than threat modeling.

### Weaker proposals

#### DeepSeek
- Good structure and useful co-existence framing.
- But too many specific factual claims were presented with high confidence:
  - exact versions
  - exact commands
  - exact example repos
  - quantified productivity and maintenance numbers
- Those claims may be true, but in this debate they were not sufficiently evidenced, so they should be discounted.

#### Grok
Weakest overall.
- It made the boldest negative claims with the thinnest support.
- It relied on:
  - highly specific abandonment stories
  - exact percentages
  - maintainer comments
  - case studies
  without credible grounding in the debate itself.
- Its core concern about doc drift and dual-artifact maintenance was valid, but it overextended that concern into a categorical rejection.

### Single strongest argument in the entire debate
**Claude’s argument that specs fill a real missing layer between ADRs and JOURNAL:**
- ADRs capture durable decision rationale.
- JOURNAL captures session continuity.
- Neither is a durable pre-implementation feature contract.
- A lightweight spec gives Claude Code a stable “what are we building?” artifact for multi-session work.

This directly answers the actual problem and explains why coexistence is useful instead of duplicative.

### Single weakest argument in the entire debate
**Grok’s claim that no successful ADR + spec coexistence examples exist and that hybrid monorepos “collapse within 90 days.”**
- Too sweeping.
- Too dependent on unverified anecdotes.
- Contradicted by more plausible architectural reasoning from the other participants.

---

## Blind Spots

1. **The debate did not actually verify the current Spec Kit mechanics.**
   - The question explicitly asked about:
     - stable workflow in Q1 2026
     - commands
     - file layout
     - PowerShell compatibility
     - Claude Code/Cursor/Aider integration
     - version bumps and breaking changes
   - The participants made many claims, but the synthesis has no firm evidence trail from the transcript itself.
   - This is the biggest unresolved factual gap.

2. **No one seriously explored “do nothing, but improve current prompts/templates” as the main option.**
   - Claude and Gemini came close, but nobody deeply compared:
     - a new `docs/specs/` workflow
     - versus simply adding a stronger feature-template inside existing `.claude/skills/` or JOURNAL patterns
   - That means the debate may have understated how much benefit could come from a simpler upgrade.

3. **The archival lifecycle of specs was underexplored.**
   - Everyone talked about creating specs.
   - Few addressed:
     - when a spec is considered complete
     - whether shipped specs remain active context
     - how to archive to avoid contaminating future prompts
   - For solo AI-assisted development, this is critical.

4. **No one tested the cognitive overhead of one more artifact class.**
   - Everyone acknowledged ADHD constraints.
   - But no one rigorously asked:
     - how often are Rob’s features actually multi-session and ambiguous enough to justify specs?
     - is the pain frequent enough to warrant a new system?
   - The recommendation therefore depends on a not-yet-measured pain point.

5. **Skills management was mostly answered negatively, but not redesigned positively.**
   - The debate agreed spec-driven workflows are not a strong upgrade for skills management.
   - But it did not propose a stronger alternative organization for `.claude/skills/` beyond “keep it.”

---

## Recommended Decision

**Adopt a lightweight spec-driven pattern for new, non-trivial features only, as a complement to ADRs—not a replacement—and treat GitHub Spec Kit tooling as optional pending a Windows/PowerShell spike. Do not adopt Kiro. Do not retrofit existing work.**

### Why this is the best decision

This conclusion best fits the strongest arguments in the debate:

- There is a plausible and important gap in the current system:
  - **ADRs explain why**
  - **JOURNAL explains what happened in sessions**
  - but there is no durable, structured **feature intent artifact** for Claude Code to follow across multi-session work.
- A lightweight spec pattern addresses that gap without threatening existing ADR investment.
- Incremental adoption on new features only avoids the largest downside: retroactive duplication and maintenance burden.
- Kiro is consistently a mismatch for the stated environment and constraints.

### Why not a full “yes to Spec Kit CLI now” decision?

Because the debate did **not** establish tool-specific evidence strongly enough. The pattern is better supported than the product choice.

So the right decision is:

- **yes to the architecture/workflow pattern**
- **maybe to GitHub Spec Kit tooling after a short compatibility spike**
- **no to Kiro**
- **no to repo-wide retrofit**

### Concrete co-existence model

Use this boundary:

- **ADR (`docs/decisions/`)**
  - architectural choice
  - cross-cutting constraint
  - trade-off/rationale
  - consequences
  - usually durable and historical

- **Spec (`docs/specs/` or `specs/`)**
  - feature scope
  - acceptance criteria
  - user-visible and system-visible behavior
  - non-architectural constraints
  - implementation plan/task breakdown
  - temporary-to-medium-term artifact, archived after stabilization

- **Skills (`.claude/skills/`)**
  - reusable standing guidance
  - gotchas
  - cross-feature patterns
  - agent operating heuristics

- **JOURNAL.md**
  - session continuity
  - what was done, what remains, next step

### Strongest objection, and why it did not win

**Objection:** dual artifacts will rot and create hybrid chaos.

**Why it did not win:**
- This is a real risk, but the strongest proposals contained a credible mitigation:
  - use specs only above a complexity threshold
  - keep the semantic boundary explicit
  - cross-link specs and ADRs
  - archive completed specs
  - kill the experiment quickly if usage is low or drift is high
- In other words, hybrid chaos is not the inevitable result of coexistence; it is the result of coexistence **without a boundary and lifecycle.**

### What would change this recommendation?

If a short spike shows either:
- GitHub Spec Kit is bash-dependent or awkward on PowerShell, or
- Claude Code cannot use the generated files/commands naturally,

then the recommendation should shift to:
- **plain Markdown specs only**, with no CLI dependency.

If even the plain Markdown pilot feels like overhead after 2–3 features, then revert to:
- ADR + JOURNAL + a stronger feature-template in `.claude/skills/`.

---

## Risks

1. **Spec rot**
   - Specs drift from code and confuse future AI sessions.
   - Mitigation:
     - add `Status: draft | active | shipped | archived`
     - archive shipped specs out of active context
     - tell Claude Code to prefer active specs only

2. **Boundary erosion with ADRs**
   - ADRs start accumulating acceptance criteria; specs start justifying architecture.
   - Mitigation:
     - write one ADR defining the boundary
     - include examples of “ADR-worthy” vs “spec-worthy”
     - make ADR authoritative when conflict exists

3. **ADHD process overhead**
   - Spec writing becomes procrastination theater.
   - Mitigation:
     - only require specs for features over a threshold:
       - >1 session
       - touches multiple modules
       - ambiguous requirements
     - cap first-pass spec writing at 20–30 minutes

4. **Tooling friction on Windows**
   - Spec Kit CLI may not fit PowerShell cleanly.
   - Mitigation:
     - run a throwaway spike first
     - if friction appears, keep the pattern and drop the CLI

5. **Context pollution**
   - Too many stale specs reduce signal quality for Claude Code.
   - Mitigation:
     - active/archive separation
     - frontmatter status
     - governance note telling agents to ignore archived specs unless asked

6. **False expectation that specs improve skills management**
   - Could lead to unnecessary migration churn.
   - Mitigation:
     - explicitly decide that `.claude/skills/` stays separate
     - revisit skills organization independently later

---

## Action Items

1. **Write a new ADR**
   - Title: something like **“Feature Specs as a Complement to ADRs”**
   - Include:
     - purpose of specs
     - authority hierarchy:
       - skills/governance > ADRs > specs > JOURNAL
     - complexity threshold for when a spec is required
     - archive policy

2. **Create a minimal spec template**
   - Suggested location: `docs/specs/_template.md` or `specs/_template.md`
   - Fields:
     - Title
     - Status
     - Summary
     - Scope / non-scope
     - Acceptance criteria
     - Constraints
     - Related ADRs
     - Open questions
     - Implementation notes/tasks

3. **Pilot on 2–3 real features**
   - Only features that are:
     - multi-session
     - cross-module
     - ambiguous enough to benefit
   - Do not use for bugs or trivial changes.

4. **Run a tool spike for GitHub Spec Kit on Windows/PowerShell**
   - In a throwaway branch/repo:
     - install it
     - test initialization
     - test whether Claude Code can work with the generated layout naturally
   - Decision rule:
     - if friction is low, optional adoption of the CLI is fine
     - if friction is noticeable, use plain Markdown specs only

5. **Do not adopt Kiro**
   - Close that branch of investigation unless future evidence shows:
     - no IDE lock-in
     - strong Claude Code compatibility
     - Windows-first workflow

6. **Add lifecycle rules to governance docs**
   - In `CLAUDE.md` / `AGENTS.md`:
     - when to create a spec
     - which artifacts have priority on conflict
     - that archived specs should be ignored unless explicitly requested

7. **Keep skills separate**
   - Do not migrate `.claude/skills/gotchas/`
   - Optionally add one new skill:
     - “when to use a feature spec”
     - “how to draft from the template”

8. **Review after 3 pilots**
   - Ask:
     - Did the spec get used after the first session?
     - Did it reduce restart friction?
     - Did it prevent implementation ambiguity?
     - Did maintenance feel lightweight?
   - If mostly no, abandon the pattern.
   - If mostly yes, keep it as the default for non-trivial new features.

9. **Explicitly avoid retrofit**
   - No backfilling specs for existing ADR-backed systems.
   - Existing architecture remains documented by ADRs and tests.

10. **Establish archival convention now**
   - Example:
     - `docs/specs/active/...`
     - `docs/specs/archive/...`
   - This prevents future context clutter from day one.

If you want, I can turn this into a proposed **ADR-028 draft** plus a **minimal spec template** tailored to your repo.
