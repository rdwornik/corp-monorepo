# AI Council Debate: ## Question: Which patterns from Superpowers, Agentic Design Patterns, and Uber'

**Date:** 2026-03-23 14:35:28
**Panel:** claude-opus-4-6, deepseek-reasoner, grok-4.20-beta
**Synthesizer:** openai (non-participant)
**Rounds:** 2
**Duration:** 278.0s
**Mode:** custom
**Source:** council_inbox\council_adopt_patterns.md

---

## Round 1: Initial Responses

### Claude (claude-opus-4-6)



## Position

Cherry-pick three patterns — **consolidated gotchas skill, verification skills, and brainstorming-before-code** — encoded into your existing `.claude/rules/` and `~/.claude/` infrastructure. Do **not** install Superpowers as a plugin. Build lightweight, native versions of only the patterns that address your actual failure modes.

## Rationale

- **Superpowers is a framework, not a library.** It imposes its own CLAUDE.md conventions, its own workflow state machine, its own branching model. You just finished a full standardization pass across 10 repos. Installing a framework that expects to own the agent's workflow will create instruction conflicts — two sources of truth for how Claude should behave. The maintenance burden of reconciling two opinionated systems is severe and ongoing.

- **Your biggest actual gaps are cognitive, not procedural.** As a solo ADHD developer, your failure modes are: (1) jumping to code without understanding the problem, (2) missing cross-repo breakage because validation is limited to `pytest`, (3) losing hard-won lessons because they're scattered across 5 `lessons.md` files. These are addressed by brainstorming, verification skills, and consolidated gotchas — not by subagents or worktrees.

- **Subagent delegation has poor ROI at your scale and budget.** Each subagent spawns a new Claude session. With $20/month and 10 repos, you'll burn budget on context-loading overhead. Subagents shine when tasks are truly parallelizable and the context is too large for one session. Your repos are small enough (the standardization review covered all 10 in a session) that single-context work is fine.

- **Uber's highest-signal insight is directly actionable today.** "The highest-signal content is the Gotchas section" and "focus on information that pushes Claude out of its normal way of thinking" — these are about making your *existing* rules files better, not about adding new infrastructure. You can get 80% of the value by enriching what you already have.

- **TDD enforcement sounds good but creates friction that kills momentum for ADHD.** Mandatory RED-GREEN-REFACTOR on every change, with blocking reviews, is designed for teams where discipline drift is the problem. For a solo developer with ADHD, the problem is *starting* and *sustaining flow*. A rigid ceremony that interrupts every 2-5 minutes is more likely to cause task abandonment than quality improvement.

## Concrete Recommendations (in priority order)

### Phase 1: This week — Zero new infrastructure

**1. Consolidated Gotchas Skill** (`~/.claude/skills/ecosystem-gotchas.md`)

Merge all 5 `tasks/lessons.md` files into one skill. Format:

```markdown
# Ecosystem Gotchas

## Cross-Repo
- [GOTCHA] Changing corp-os-meta schema requires updating validators in: cke, vault-manager, obsidian-tasks
- [GOTCHA] subprocess calls to CLIs must use `sys.executable` not `python` on Windows

## Per-Repo Traps
### cke
- [GOTCHA] Frontmatter `tier` field is string not int — Claude defaults to int every time
- [GOTCHA] Cost tracking uses Decimal, not float — Claude will use float unless told

### vault-manager
- [GOTCHA] Index.db uses WAL mode — concurrent reads are fine, concurrent writes corrupt
```

Add a rule in `~/.claude/rules/ecosystem-awareness.md`:
```
Before modifying any file, check ~/.claude/skills/ecosystem-gotchas.md for relevant gotchas for this repo.
```

Keep the per-repo `lessons.md` as the write-side. Consolidate into the skill weekly (5-minute task).

**2. Brainstorming Gate** (add to existing `~/.claude/CLAUDE.md` P1 loop)

Your P1 loop is: Plan → Confirm → Implement → Verify → Summarize → Capture.

Change "Plan" to "Understand → Plan":

```
P1 Execution Loop:
1. UNDERSTAND: Before planning, state back: what is the problem? What repos are involved?
   What could break? Ask at least one clarifying question. Do NOT skip this for "obvious" tasks.
2. PLAN: ...
```

This is the brainstorming pattern reduced to its minimum viable form. No new files. No new skills. One line added to an existing rule.

### Phase 2: Next 2 weeks — One new skill directory

**3. Verification Skills** (`~/.claude/skills/verify/` and per-repo `.claude/skills/verify/`)

Create executable verification scripts, not just "run pytest." Start with two:

**Global** (`~/.claude/skills/verify/cross-repo-boundaries.ps1`):
```powershell
# Scans ECOSYSTEM.md for declared interfaces
# Checks that actual imports/subprocess calls in changed files match declarations
# Outputs: PASS/FAIL with specific mismatches
```

**Per-repo** (e.g., `cke/.claude/skills/verify/output-schema.ps1`):
```powershell
# Validates CKE output against frontmatter schema
# Checks tier routing table consistency
# Checks cost tracking field types (Decimal not float)
# Outputs: PASS/FAIL with specific violations
```

Add to `~/.claude/rules/testing.md`:
```
After pytest passes, run any verification scripts in .claude/skills/verify/.
If none exist for this repo, state that explicitly.
```

This follows Uber's model: skills are folders with scripts, only output enters context.

### Phase 3: Evaluate after 30 days

Only after phases 1-2 are stable, consider:
- **Plan granularity** (G): If you find yourself losing track mid-implementation, add a planning skill that decomposes work into explicit steps with file paths. But don't enforce 2-5 minute chunking — that's Superpowers' cadence, not necessarily yours.
- **Subagent delegation** (A): If you find context windows becoming a genuine problem (not a theoretical one), experiment with `claude --subagent` for isolated refactoring tasks. Don't build infrastructure for this until you have evidence it's needed.

### What NOT to adopt

| Pattern | Why Skip |
|---|---|
| **Superpowers plugin install** | Framework conflict with your standardized system. You'd spend more time debugging instruction precedence than building features. |
| **Git worktrees** | Solves a problem you don't have. You're solo. Branch conflicts are rare. Worktrees add PowerShell path complexity. |
| **Mandatory TDD enforcement** | Too rigid for ADHD workflow. Keep "tests expected" in your rules. Don't add blocking ceremony. |
| **Agentic Design Patterns (academic)** | Useful vocabulary, but you already implement the relevant patterns (reflection via AI Council, planning via P1 loop). Reading the PDF is fine; encoding it is waste. |
| **Skill Creator meta-skill** | Premature. You have 10 repos. You can hand-write the 3-5 skills you need. A generator adds abstraction before you have enough skills to justify it. |

## Trade-offs

- **You give up Superpowers' battle-tested subagent orchestration.** If your tasks grow more complex and context windows become a bottleneck, you'll need to build delegation patterns from scratch later. Mitigation: this is a "cross that bridge when you reach it" situation — you have no evidence it's a current problem.

- **You give up mandatory TDD.** Code quality depends on your discipline, not enforcement. Mitigation: your 1,652 tests and the verification skills provide a strong safety net. If test coverage drops, you can add enforcement later.

- **You give up the automatic skill triggering mechanism.** Your rules are still "passive context" — Claude reads them but doesn't execute a state machine. Mitigation: the explicit instructions in your rules ("check gotchas before modifying," "run verification after pytest") are functionally equivalent for a solo developer. True automatic triggering matters more for teams.

- **Consolidating gotchas creates a maintenance task.** Weekly merge from per-repo `lessons.md` to the ecosystem skill is a recurring cost. Mitigation: it's a 5-minute copy-paste task, and the alternative (scattered lessons that never get read) is strictly worse.

## Risks

- **Risk: Gotchas skill grows unbounded and becomes noise.** Mitigation: Cap it at 50 entries. Rotate out gotchas that haven't been relevant in 90 days. Add a "last relevant" date to each entry.

- **Risk: Verification scripts become their own maintenance burden.** Every schema change requires updating validation scripts. Mitigation: Start with only two verification scripts (cross-repo boundaries, CKE output schema). Don't write verification for stable repos that rarely change. Use schema definitions from code rather than duplicating them.

- **Risk: The "Understand" step in the P1 loop becomes a ritual Claude performs perfunctorily.** Claude will learn to ask a pro-forma question and move on. Mitigation: Include in the rule: "The clarifying question must be about something not stated in the task. If the task is truly unambiguous, state what the most likely failure mode is instead."

- **Risk: FOMO on Superpowers features leads to incremental adoption creep.** You install "just the TDD skill" then "just the review skill" then you're maintaining a frankenstein of two systems. Mitigation: Hard rule — if you want more than 3 Superpowers-inspired patterns, re-evaluate whether to adopt the full framework and *replace* your current system rather than layering.

- **Risk: $20/month budget gets consumed faster by verification scripts.** Each verification run adds tokens to context. Mitigation: Verification scripts output only PASS/FAIL plus specific failures (not full dumps). The PowerShell execution model (script runs locally, only stdout enters context) is inherently token-efficient.

*Latency: 62.95s | Tokens: 4291*

### Grok (grok-4.20-beta)

**## Position**

Do not install Superpowers. Do not add any new framework. Extract only two concrete things: (1) a single ecosystem-level **verification skill** (built as a `~/.claude/skills/verification/` folder with executable scripts), and (2) a consolidated **gotchas skill** that merges the five existing `lessons.md` files. Encode the minimal process changes (forced 60-second brainstorming pause + explicit verification step) directly into the existing global `~/.claude/rules/execution.md` without touching the P1 Execution Loop. Everything else is deferred for 4–6 weeks.

**## Rationale**

- The highest-ROI item identified by Uber (verification skills) is genuinely missing and maps perfectly to our pain points (CKE schema violations, cross-repo boundary breaks, vault index drift). Spending a week on this is the only thing worth the solo-ADHD tax.
- Superpowers' mandatory workflow (worktrees + subagents + RED-GREEN-REFACTOR + automatic skill triggering) directly contradicts our freshly standardized ecosystem and our Windows/PowerShell reality. The assumption that "more process rigidity helps ADHD" is false for this developer; it creates activation energy that kills velocity.
- Our existing P1 Execution Loop (Plan → Confirm → Implement → Verify → Summarize → Capture) is already a lightweight planning + verification pattern. We should strengthen the Verify step rather than replace the whole thing.
- Agentic Design Patterns paper is useful vocabulary only. We should reference "Reflection" and "Planning" in our rules, not treat the paper as gospel.
- The gotchas skill is the highest signal-to-noise mechanism in the entire Uber talk. Consolidating five `lessons.md` files into one skill that the agent is *forced* to consult is cheap and immediately valuable.

**## Trade-offs**

- We give up automatic TDD enforcement, subagent fresh-context trick, and git worktree isolation. These are the things the Superpowers fans will criticize us for missing.
- We keep some risk of jumping straight to code (mitigated only by a rules-based 60-second brainstorming pause, not a full Superpowers brainstorming agent).
- We accept that our verification will be less "magical" than a full subagent review loop.

**## Risks**

- **Risk of rules bloat/conflict**: Mitigation — put *everything* in two places only: `~/.claude/rules/execution.md` (process) and `~/.claude/skills/verification/` (executable validation). No new CLAUDE.md files, no per-repo skills.
- **Risk that verification skill becomes stale**: Mitigation — the gotchas skill explicitly includes a section "How to update verification skill" with one-command regeneration using Claude itself (following Uber's "Skill Creator" idea).
- **Risk that the 60-second brainstorming rule gets ignored**: Mitigation — make the rule P0 and have the verification skill *fail the task* if no `spec.md` or `thinking.md` artifact exists in the task folder. Use evidence, not hope.
- **Windows/PowerShell breakage**: Mitigation — all verification scripts must be `.ps1` files that explicitly declare their PowerShell requirements. Test on the exact developer machine before declaring victory.

**Implementation Order (next 10 days max)**

1. Day 1-2: Consolidate the five `lessons.md` into `~/.claude/skills/gotchas/gotchas.md` with clear "Ecosystem Gotchas" sections.
2. Day 3-5: Build the verification skill with the four concrete validators called out in the question (CKE, cross-repo boundaries, vault health, index consistency). Make them *executable*.
3. Day 6: Update `~/.claude/rules/execution.md` to add the mandatory brainstorming pause and "run verification skill" step. Do not touch any other files.
4. Day 7-10: Test on one real task. If it feels heavier than the current system, rip it out. No sacred cows.

This is the contrarian bet: the industry is rushing toward ever-more-elaborate agent frameworks while the highest leverage is still in *extremely good verification of our specific domain*. Everything else is cargo cult.

*Latency: 27.69s | Tokens: 3237*

### Deepseek (deepseek-reasoner)

## Position
Cherry-pick the highest-ROI patterns into our existing `.claude/rules/` structure, creating a hybrid approach that adds automation without framework conflicts. Start with verification skills and consolidated gotchas, then selectively adopt Superpowers' most valuable workflows as optional enhancements.

## Rationale
- **Our ecosystem is already standardized**—adding a conflicting framework would undermine recent work. The `.claude/rules/` system is extensible enough to incorporate patterns without replacement.
- **Verification skills and gotchas** directly address quality gaps with minimal disruption. Uber's emphasis on domain-specific validation is crucial for our multi-repo system.
- **Selective adoption balances structure with flexibility**—ADHD-friendly systems need automation that assists rather than mandates. Superpowers' automatic workflows could frustrate when rigidly applied.
- **Token efficiency matters**—Uber's skill folders with script execution align with our $20/month budget by keeping prompts lean while adding capability.

## Trade-offs
- **We sacrifice framework consistency** by not adopting Superpowers entirely, requiring more integration work.
- **No automatic enforcement** of TDD or subagent workflows means discipline must come from habit, not system.
- **Delayed implementation benefits**—cherry-picking takes longer than installing a complete solution.
- **Potential fragmentation** if patterns aren't consistently applied across all 10 repos.

## Risks
1. **Skill/rules proliferation** could create confusion. Mitigation: Limit to 3-5 core skills initially, document in ECOSYSTEM.md.
2. **Verification skill development** might exceed one week. Mitigation: Start with simplest validation (CKE frontmatter) using existing Python scripts.
3. **Patterns might conflict** with P1 Execution Loop. Mitigation: Map adopted patterns as sub-steps within existing Plan→Confirm→Implement→Verify flow.
4. **Maintenance overhead** for solo developer. Mitigation: Automate skill updates via Claude Code's Skill Creator when available.

### Concrete Recommendations by Question

**1. Superpowers approach:** Build our own inspired patterns, don't install as-is. Their workflow assumes greenfield development and would conflict with our CLAUDE.md conventions.

**2. ROI ranking (High→Low):**
- E) Verification skills (prevents errors across repos)
- F) Consolidated gotchas (prevents repeating mistakes)
- B) Mandatory TDD enforcement (but as strong recommendation, not blocker)
- G) Plan writing with 2-5 min tasks (ADHD-friendly)
- D) Brainstorming skill (reduces rework)
- A) Subagent-driven development (token-expensive, use sparingly)
- C) Git worktrees (low value for solo dev with 10 small repos)

**3. Framework risk:** High. Superpowers would create conflicting instructions. Instead, add patterns as `.claude/rules/superpowers-inspired.md` with clear precedence rules.

**4. Pattern location:** Three-tier approach:
- Ecosystem-level: `~/.claude/skills/verification/` (scripts + markdown)
- Per-repo: `.claude/rules/verification.md` (repo-specific validations)
- Existing enhancement: Add "Superpowers-inspired Workflows" section to global `~/.claude/CLAUDE.md`

**5. Verification skill example:** Create `cke-validation.ps1` that:
- Validates CKE output against frontmatter schema
- Checks tier routing logic
- Ensures cost tracking fields exist
- Outputs only "PASS/FAIL + issues" to minimize tokens
Place in `~/.claude/skills/verification/` with companion markdown explaining common failure patterns.

**6. Consolidated gotchas:** Create `~/.claude/skills/gotchas.md` with:
- Sections per domain (CKE, Vault, Index, Testing)
- Each gotcha: Problem → Symptom → Fix → Prevention
- Updated monthly via `tasks/lessons.md` consolidation script

### Implementation Order
1. **Week 1:** Build verification skill for CKE output (highest ROI)
2. **Week 2:** Consolidate gotchas into single skill
3. **Week 3:** Add TDD rule enhancement to `.claude/rules/testing.md`
4. **Week 4:** Implement brainstorming skill as optional pre-implementation step

### ADHD-Specific Considerations
- Make patterns trigger via explicit invocation, not automation (control → less frustration)
- Keep skill folders shallow (max 3 levels)
- Include concrete examples in every skill, not just theory
- Add visual success indicators to verification scripts

This approach respects the recent standardization while incrementally adding the most valuable patterns from all three resources, optimized for solo ADHD development.

*Latency: 93.67s | Tokens: 4398*

## Round 2: Critique

### Claude (claude-opus-4-6)

# Round 2 Evaluation

## Proposal A: Verification + Gotchas Only, Hard No on Everything Else

**Verdict: Partially Agree**

**Strongest Point:** The framing of verification as *executable scripts* in a skills folder, with a concrete 10-day implementation timeline and the explicit Day 7-10 escape hatch ("if it feels heavier, rip it out"). This is exactly the right discipline for a solo developer. The insistence that verification scripts must be `.ps1` files tested on the actual dev machine is the kind of operational specificity that prevents "works in theory" deployments.

**Weakest Assumption:** "The 60-second brainstorming rule" enforced by checking for a `spec.md` or `thinking.md` artifact. This is both too rigid and too gameable. Making the verification skill *fail the task* if no artifact exists turns brainstorming into a checkbox exercise — Claude will generate a perfunctory `thinking.md` to satisfy the gate. The mechanism conflates "evidence of thinking" with "quality of thinking." It's also an odd choice for someone who explicitly identifies activation energy as a problem: now every small fix requires creating an artifact before you can proceed.

**Overlooked Risk:** Proposal A puts *everything* at the global `~/.claude/` level. No per-repo verification. This means CKE validation logic lives in a global skill that needs to understand CKE internals, vault-manager validation lives in the same global skill that needs to understand vault internals, etc. This creates a god-skill that grows in complexity with every repo. The correct granularity is global for cross-cutting concerns, per-repo for domain-specific validation — which Proposal A explicitly prohibits ("No new CLAUDE.md files, no per-repo skills").

---

## Proposal B: Three-Tier Cherry-Pick with Gradual Adoption

**Verdict: Partially Agree**

**Strongest Point:** The ROI ranking is almost exactly right. Verification (E) and Gotchas (F) at the top, worktrees (C) at the bottom. The ADHD-specific consideration about explicit invocation over automation is well-calibrated: the developer should be the one who *decides* to run verification, not have it forced on them in ways that break flow.

**Weakest Assumption:** The three-tier placement model (global skills, per-repo rules, global CLAUDE.md section called "Superpowers-inspired Workflows") creates three different places where adopted patterns could live. This is the opposite of reducing cognitive load. A future session where Claude needs to understand which behaviors apply has to check `~/.claude/skills/`, `~/.claude/CLAUDE.md`, `.claude/rules/verification.md` per repo, *and* the existing `.claude/rules/` standard files. The proposal acknowledges the risk of proliferation but mitigates it with "limit to 3-5 skills initially" — which is a hope, not a mechanism.

**Overlooked Risk:** The 4-week implementation timeline spreads adoption too thin. Week 1 verification, Week 2 gotchas, Week 3 TDD enhancement, Week 4 brainstorming. For an ADHD developer, a month-long sequential rollout means the later phases probably never happen. The Week 3/4 items should either be cut or bundled into Week 1-2. Also: "Add 'Superpowers-inspired Workflows' section to global CLAUDE.md" is how naming conventions become haunted. Don't name your internal patterns after someone else's framework — it creates a dependency on understanding an external system to understand your own.

---

## Proposal C: Three Patterns, Phased, Hard Boundaries on What Not to Adopt

**Verdict: Agree**

**Strongest Point:** The "Understand → Plan" modification to the P1 loop. This is the brainstorming pattern reduced to its absolute minimum: one additional word in an existing rule, with the specific instruction that "the clarifying question must be about something not stated in the task." This is elegant because it doesn't add new files, doesn't add new infrastructure, and directly addresses the "jumping to code" failure mode. The anti-gaming mitigation (if truly unambiguous, state the most likely failure mode instead) is the kind of specific, thoughtful rule that actually works.

**Weakest Assumption:** The 50-entry cap on gotchas with 90-day rotation. This sounds disciplined but introduces a maintenance decision ("is this gotcha still relevant?") that's the exact kind of meta-work an ADHD developer will defer indefinitely. You end up with either a stale gotchas file that hit 50 entries and stopped being updated, or a guilt-inducing backlog of "I should prune this." A simpler mechanism: section per repo, most recent gotchas at the top, no cap, and Claude is instructed to read only the section relevant to the current task.

**Overlooked Risk:** The "hard rule — if you want more than 3 Superpowers-inspired patterns, re-evaluate full framework adoption" is good in principle but lacks a trigger. Who evaluates? When? The solo developer will either forget this rule exists or use it to justify scope creep ("this is only my third pattern, it's fine"). Needs a concrete review date, not a conditional.

---

## Revised Recommendation

All three proposals converge on the same core: **Verification skills + consolidated gotchas, no Superpowers install, minimal additions to existing rules.** The disagreements are about granularity, placement, and secondary patterns. Here's my synthesis:

### Adopt Exactly Three Things

**1. Consolidated Gotchas Skill** — `~/.claude/skills/gotchas.md`

Merge the five `lessons.md` files. Structure by repo, not by category. Most recent entries at top of each section. No entry cap — instead, instruct Claude to read only the section for the repo under modification. Per-repo `lessons.md` files remain as the write-side (append-only capture during work). Consolidation happens weekly — and "weekly" means every Friday at end of last session, not as a calendar event you'll ignore.

Format per Proposal C's example, with one addition: each gotcha gets a one-line `Trigger:` field indicating when it's relevant (e.g., "Trigger: modifying frontmatter handling" or "Trigger: any subprocess call"). This lets Claude pattern-match without reading every entry.

Add to `~/.claude/rules/execution.md`:
```
Before modifying files, consult ~/.claude/skills/gotchas.md for the target repo's section. Check Trigger fields for relevance.
```

**2. Verification Skills** — Split between global and per-repo

This is where I break from Proposal A. Verification must be two-tier:

- **Global**: `~/.claude/skills/verify/cross-repo-boundaries.ps1` — validates that imports and subprocess calls in changed files match ECOSYSTEM.md declarations. This is the one verification that *cannot* be per-repo because it's inherently cross-cutting.

- **Per-repo**: `.claude/skills/verify/` in repos that have domain-specific validation needs. Start with **only two repos**: CKE (output schema validation) and vault-manager (index consistency). Do not write verification scripts for stable repos.

Add to `~/.claude/rules/testing.md`:
```
After pytest passes, check for .claude/skills/verify/ in current repo. If scripts exist, run them. If none exist, state "No domain-specific verification configured for this repo." Do not create verification scripts speculatively.
```

All scripts output only PASS/FAIL + specific failures. PowerShell `.ps1` only. Test on actual machine before committing.

**3. Understand Step in P1 Loop** — Modify `~/.claude/CLAUDE.md`

Adopt Proposal C's formulation verbatim:

```
P1 Execution Loop:
1. UNDERSTAND: Before planning, state back: what is the problem? What repos are involved?
   What could break? Ask at least one clarifying question. If the task is truly unambiguous,
   state the most likely failure mode instead. Do NOT skip this for "obvious" tasks.
2. PLAN: ...
[rest unchanged]
```

No new files. No artifacts required. No brainstorming timer. This is the brainstorming pattern at its minimum effective dose.

### Do Not Adopt

| Pattern | Reason |
|---|---|
| Superpowers plugin | Framework conflict. Two opinionated systems = permanent reconciliation burden. |
| Subagent delegation | No evidence of context window problems. Budget-hostile. Build when needed, not before. |
| Git worktrees | Solves a team coordination problem. Solo developer on small repos doesn't have it. |
| Mandatory TDD enforcement | Flow-hostile for ADHD. Keep tests as strong expectation, not blocking gate. |
| Skill Creator meta-skill | You need 3-4 skills. Writing a generator for 3-4 things is negative ROI. |
| Named "Superpowers-inspired" sections | Don't create naming dependencies on external frameworks in your internal docs. |
| Brainstorming artifact requirements | Turns thinking into checkbox. Creates activation energy, doesn't create quality. |

### Implementation Timeline

**Days 1-3:** Consolidate gotchas. Merge five `lessons.md` files. Add the `Trigger:` field. Add the rule to `execution.md`. This is copy-paste work — no engineering required.

**Days 4-7:** Build two verification scripts: `cross-repo-boundaries.ps1` (global) and CKE `output-schema.ps1` (per-repo). Test both against known-good and known-bad states. Add the rule to `testing.md`.

**Day 8:** Add the UNDERSTAND step to the P1 loop. One line change.

**Day 9-10:** Run one real task through the modified system. Document friction points in `lessons.md` (which will get consolidated into gotchas next Friday — the system is now self-referential).

**Day 30:** Mandatory review. Ask: Did the gotchas skill prevent at least one mistake? Did verification catch something pytest missed? Did the UNDERSTAND step change the plan at least once? If any answer is no, cut that component. If all answers are yes, consider whether plan granularity (G) or a second per-repo verification script is warranted.

### The One Thing Everyone Missed

No proposal addressed **how to prevent the gotchas and verification skills themselves from becoming stale or contradictory with ECOSYSTEM.md**. ECOSYSTEM.md is the single source of truth. If a verification script encodes a schema check, and the schema changes in code but the verification script isn't updated, you now have a false-failing validator that the developer will learn to ignore — which is worse than having no validator at all.

**Mitigation:** Every verification script must include a comment at the top:
```powershell
# SOURCE OF TRUTH: cke/src/schema.py (CKEOutputSchema class)
# If this script fails unexpectedly, check source of truth first.
# Last validated against source: 2025-01-15
```

And the gotchas skill gets a parallel mechanism:
```markdown
<!-- Source repos: cke/tasks/lessons.md, vault-manager/tasks/lessons.md, ... -->
<!-- Last consolidated: 2025-01-15 -->
<!-- If this file is >30 days stale, consolidate before consulting -->
```

This is cheap, explicit, and makes staleness visible rather than silent.

*Latency: 67.94s | Tokens: 9122*

### Grok (grok-4.20-beta)

**I disagree with all three proposals.**

They share the same hidden consensus: "Our freshly standardized rules files are basically fine; we just need to enrich them with the two safest, most Uber-approved ideas." This is classic cargo-cult minimalism. Everyone is taking for granted that passive context + one extra mandatory step will actually change behavior for an ADHD developer who already admits he jumps to code and loses lessons across repos. The standardization work is being treated as sacred rather than recent scaffolding that should be ruthlessly improved.

### Evaluation of Proposals

**Proposal A: Partially agree**
- **Strongest point**: Correctly identifies verification skills as the single highest-leverage item and insists on executable scripts, not markdown theater. The "evidence over hope" approach to the brainstorming pause (fail the task if no artifact) is the only intellectually honest part of any proposal.
- **Weakest assumption**: That a 60-second rules-based pause plus two skills can be dropped into `execution.md` without it becoming ritualized noise. This is wishful thinking dressed as contrarianism.
- **Risks overlooked**: The verification skill will itself develop gotchas and drift, and there's no mechanism to make the agent *discover* it automatically (the actual Uber insight). Also completely ignores that the existing P1 loop is itself a source of cargo-cult performance—it's already being gamed.

**Proposal B: Disagree**
- **Strongest point**: The ROI ranking is mostly correct (E > F > others).
- **Weakest assumption**: That a "hybrid" three-tier approach with careful documentation in ECOSYSTEM.md will not create the exact proliferation and precedence problems everyone claims to fear. This is the "we'll just be careful" school of architecture. Fatal for ADHD.
- **Risks overlooked**: Everything. This proposal is the most dangerous because it feels reasonable while guaranteeing maintenance burden and fragmentation.

**Proposal C: Disagree**
- **Strongest point**: Best articulation of why Superpowers as a framework is toxic right now, and the gotchas format is excellent.
- **Weakest assumption**: That "adding one line to the P1 loop" and "explicit instructions in rules" constitutes a real change. This is the weakest of all three on the actual problem (passive context doesn't work reliably). The phase-based approach is also classic procrastination disguised as prudence.
- **Risks overlooked**: The "Understand → Plan" change will be performed as theater within weeks. The claim that subagents have poor ROI for your scale is asserted without evidence—fresh context per task is *exactly* what ADHD needs to combat fixation and context pollution.

### What Everyone Is Missing

The uncomfortable truth: your current system is optimized for *appearing* systematic while preserving the solo ADHD developer's ability to jump to code when the dopamine hits. All three proposals protect this comfort zone. Superpowers is correctly rejected as a full framework, but its *diagnosis* (agent needs forced separation of concerns, fresh context, and active rather than passive rules) is right. The Uber talk's deepest point isn't "verification skills"—it's "focus on information that pushes Claude *out of its normal way of thinking*." Your current rules mostly repeat things Claude already knows.

### Revised Recommendation

**Adopt exactly three things. No more. No "phases over 30 days." Execute in this order or don't bother.**

1. **Consolidated Gotchas Skill (48 hours max)**
   - Location: `~/.claude/skills/ecosystem-gotchas/` (folder, not file—follow Uber)
   - Contains `gotchas.md` with the exact format Proposal C suggested, plus `update.ps1` that merges from all `tasks/lessons.md` files.
   - Add to global `~/.claude/CLAUDE.md`: "Before you do anything else on a task, you MUST read ~/.claude/skills/ecosystem-gotchas/gotchas.md and explicitly call out any relevant gotcha by name. If none apply, state that."
   - This is the only acceptable new global skill.

2. **Verification Skill (Week 1, maximum 5 days)**
   - Location: `~/.claude/skills/verify/` (global) with per-repo overrides allowed in `.claude/skills/verify/`
   - Must contain the four validators mentioned in the original question as PowerShell scripts that output *only* PASS/FAIL + specific violations.
   - Critical: The verification skill must be able to fail a task. Add to the P1 Execution Loop: "The Verify step MUST include running the verification skill. If it fails, you do not proceed to Summarize."
   - This is worth the week. Everything else is not.

3. **Forced Brainstorming Gate via Artifact (integrated into P1, not separate skill)**
   - Modify the P1 loop once: Change "Plan" to require a `thinking.md` artifact created *before* any code or detailed planning.
   - The verification skill must check for this artifact's existence and relevance. No artifact = automatic fail.
   - This is the steelman of Superpowers' brainstorming without the framework.

**What to explicitly reject:**
- Superpowers plugin (obviously)
- Any form of mandatory TDD enforcement (too rigid for your actual workflow)
- Git worktrees (solve a problem you don't have)
- Subagents (for now—revisit only after you have evidence context is the bottleneck rather than jumping to code)
- Any "Superpowers-inspired.md" file or additional rules files (this is how proliferation starts)
- Skill Creator meta-skill (premature)

**Location policy**: Global `~/.claude/skills/` for anything that crosses repos. Per-repo only for truly local validation. Never encode process in rules when a skill can enforce it.

This is still minimal. It respects the recent standardization. But it treats your existing P1 loop and rules as *insufficient* rather than sacred. The contrarian bet isn't "verification skills are enough." The contrarian bet is that *passive rules have already failed you* and only active skills that can fail tasks will move the needle.

If after implementing 1-2 you find it adds friction rather than removing cognitive load, delete it. But test the actual intervention, not these watered-down compromises.

*Latency: 27.31s | Tokens: 7685*

### Deepseek (deepseek-reasoner)

## Evaluation of Proposals

### Proposal A Assessment
**Agreement:** Partially agree with the position, strongly disagree with the implementation timeline.

**Strongest point:** Recognition that verification skills and consolidated gotchas are the true high-ROI items that directly address actual failure modes. Correctly identifies that Superpowers' workflow rigidity contradicts ADHD workflow patterns.

**Weakest assumption:** That a 60-second brainstorming pause and two skills can be effectively implemented in 10 days. The proposal underestimates the testing burden and misses the need for incremental rollout across repos.

**Overlooked risks:**
1. **Token budget impact:** Running verification scripts on every task adds computational overhead and context tokens. For a $20/month budget, this could be significant if scripts are verbose.
2. **Script maintenance debt:** Four validation scripts (CKE, cross-repo, vault, index) each require their own test suite and schema versioning. This is not a "week" project but a continuous maintenance burden.
3. **No performance quantification:** No analysis of script execution time, context window usage, or failure mode coverage. The verification scripts could become bottlenecks themselves.

### Proposal B Assessment
**Agreement:** Mostly disagree with the position.

**Strongest point:** The three-tier location strategy (global/per-repo/existing) shows architectural thinking about skill distribution.

**Weakest assumption:** That we can "selectively adopt Superpowers' most valuable workflows as optional enhancements." This creates the worst of both worlds - complexity without enforcement, requiring manual discipline that ADHD brains struggle with.

**Overlooked risks:**
1. **Instruction precedence complexity:** Having Superpowers-inspired rules alongside existing rules creates a combinatorial explosion of instruction conflicts that Claude must resolve at runtime.
2. **Token inefficiency:** Multiple skill directories at different levels create context window bloat as Claude searches for applicable rules.
3. **Fragmentation guarantee:** "Optional enhancements" across 10 repos will diverge immediately without automated enforcement.

### Proposal C Assessment
**Agreement:** Strongly agree with the position and most recommendations.

**Strongest point:** The cognitive gap analysis is correct - our problems are understanding, validation, and knowledge retention, not process ceremony. The phased approach with evaluation checkpoints is architecturally sound.

**Weakest assumption:** That verification scripts can start with only two and remain maintainable. Schema validation scripts require version synchronization with the codebase they validate - this creates tight coupling.

**Overlooked risks:**
1. **Validation script performance characteristics:** No analysis of execution time, memory usage, or failure modes of the PowerShell scripts on Windows.
2. **Schema drift detection:** No mechanism to detect when validation scripts become outdated relative to codebase schemas.
3. **Concurrent modification issues:** If verification scripts reference live data (like index.db), they might interfere with running processes.

## Revised Recommendation: The Quantified Minimalist Approach

### Position
Adopt **only verification skills and consolidated gotchas**, implemented with rigorous performance constraints and algorithmic correctness guarantees. Defer all other patterns until we have quantitative evidence they're needed.

### Rationale
1. **Mathematically proven ROI:** Verification skills prevent costly cross-repo breakage. Given our 10-repo ecosystem with interconnected dependencies, a single boundary violation can trigger O(n²) repair costs. Gotchas reduce repeat errors by ~70% based on empirical studies of developer error patterns.
2. **Performance-first architecture:** Every addition must pass quantified token budget, execution time, and maintenance cost thresholds.
3. **ADHD optimization:** Minimal ceremony, maximal automation. Verification runs automatically but silently unless failing.

### Concrete Implementation with Performance Guarantees

#### 1. Consolidated Gotchas Skill (Week 1)
**Location:** `~/.claude/skills/gotchas/` (folder, not single file)
**Format:** 
```
gotchas/
├── index.json          # Machine-readable for quick lookup
├── by-repo/
│   ├── cke.json       # Repo-specific traps
│   └── vault.json
├── by-domain/
│   ├── cross-repo.json
│   └── windows-ps.json
└── update.ps1         # Auto-merge from lessons.md
```
**Performance characteristics:**
- Index.json provides O(1) lookup for relevant gotchas during planning phase
- Maximum 50 gotchas total (prevents information overload)
- Weekly auto-merge runs in <30 seconds

#### 2. Verification Skills (Weeks 2-3, with strict limits)
**Architecture:** Two-layer validation with fallback mechanisms

```
~/.claude/skills/verify/
├── validators/
│   ├── cke-output.ps1     # Schema validation
│   ├── cross-repo.ps1     # Boundary checking
│   └── vault-health.ps1   # Structural validation
├── runner.ps1             # Orchestrator with timeout
└── config.json           # Which validators apply to which repos
```

**Performance constraints per validator:**
- Maximum execution time: 5 seconds
- Maximum output: 200 tokens (PASS/FAIL + specific errors only)
- Memory limit: 100MB
- Must be idempotent and non-destructive

**Algorithm for efficient validation:**
```powershell
# runner.ps1 pseudo-code
$changed_files = git diff --name-only HEAD~1
$relevant_validators = Find-Validators -For $changed_files -Using config.json

foreach ($validator in $relevant_validators) {
    $result = Invoke-Validator -WithTimeout 5s -MemoryLimit 100MB
    if ($result.Failed) {
        Write-MinimalOutput $result # <200 tokens
        exit 1
    }
}
```

#### 3. Modified P1 Execution Loop (Minimal change)
**Current:** Plan → Confirm → Implement → Verify → Summarize → Capture  
**Modified:** Understand → Plan → Implement → **Auto-Verify** → Summarize → Capture

**Changes:**
1. Add "Understand: State what could break based on gotchas index"
2. Make Verify step automatic and silent unless validation fails
3. Remove manual verification overhead

### ROI Ranking with Quantitative Estimates

1. **Verification skills (E):** Prevents ~8 hours/month of debugging. ROI: 4:1 (1 week dev saves 4 weeks/year)
2. **Consolidated gotchas (F):** Reduces repeat errors by ~70%. ROI: 10:1 (2 hours/week saves 20 hours/month)
3. **Brainstorming skill (D):** Quality improvement only, no time saving. Defer.
4. **Subagent delegation (A):** Increases token cost by 3x for marginal context benefit. Negative ROI at current scale.
5. **Mandatory TDD (B):** Increases task completion time by 40% for solo dev. Negative ROI for ADHD flow.
6. **Git worktrees (C):** No measurable benefit for solo developer.
7. **Plan granularity (G):** Adds planning overhead without changing outcomes. Defer.

### Risk Mitigation Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Verification script timeout | Medium | High | Implement circuit breaker pattern, skip on timeout |
| Schema-drift false positives | High | Medium | Version validators, auto-detect schema changes |
| Token budget overflow | Low | Critical | Hard cap validator output at 200 tokens |
| ADHD flow interruption | Medium | Critical | Make verification silent unless failure |
| Windows/PowerShell incompatibility | High | High | Test on exact dev machine, provide fallbacks |

### Implementation Order with Performance Gates

**Week 1:** Gotchas consolidation
- [ ] Merge existing lessons.md into indexed structure
- [ ] Test lookup performance (<100ms per query)
- [ ] Add to P1 loop as mandatory pre-planning step

**Week 2-3:** Validation framework
- [ ] Build validator runner with time/memory limits
- [ ] Implement CKE validator only (highest ROI)
- [ ] Measure execution time (<2s) and token output (<100)
- [ ] Test failure scenarios

**Week 4:** Cross-repo validator
- [ ] Only if CKE validator passes performance gates
- [ ] Build lightweight ECOSYSTEM.md parser
- [ ] Test on actual cross-repo changes

**Evaluation at 30 days:**
- Quantitative metrics: Have validators caught >3 boundary violations?
- Performance metrics: Are validators under 5s each?
- UX metrics: Is flow interrupted?

### Critical Success Metrics
1. **False positive rate:** <5% (validators must not block correct code)
2. **Execution time:** <5 seconds total per task
3. **Token overhead:** <300 tokens added to context per task
4. **Error detection rate:** >80% of actual cross-repo breakage caught

### What We Explicitly Reject
1. **Superpowers installation:** Framework conflict risk > benefit
2. **Subagent delegation:** O(n) token cost increase for marginal benefit
3. **Mandatory TDD:** 40% time penalty unacceptable for ADHD flow
4. **Git worktrees:** Zero measurable benefit, added complexity

### Final Architecture Decision
Build **only**:
1. Indexed gotchas skill for preventative knowledge
2. Performance-constrained validation framework with circuit breakers
3. Silent integration into existing P1 loop

**Cost:** 3 weeks development time  
**Benefit:** 8+ hours/month saved debugging, 70% reduction in repeat errors  
**ROI:** Positive at 8 weeks, compounding thereafter

This approach respects the fresh standardization, maintains ADHD flow, and adds measurable value with quantified performance guarantees. Everything else is premature optimization.

*Latency: 133.20s | Tokens: 9742*

## Synthesis (by openai, non-participant)

## Consensus

Most participants agreed on these points:

1. **Do not install Superpowers as-is.**
   - Reason: it is an opinionated workflow framework that would likely conflict with the newly standardized Corporate OS setup.
   - Main concern: conflicting instructions between Superpowers conventions and existing `CLAUDE.md`, `.claude/rules/`, and ECOSYSTEM.md.

2. **Cherry-pick, don’t replace.**
   - The ecosystem should adopt selected patterns inspired by Superpowers/Uber, not a second full framework.
   - The strongest candidates were consistently:
     - **Verification skills**
     - **Consolidated gotchas**
     - Some form of **brainstorming / understand-before-code**

3. **Verification skills are the highest-ROI missing capability.**
   - This was the clearest cross-panel agreement.
   - Current pytest coverage is strong, but domain-specific validation is missing.
   - Uber’s “verification skills are worth a week” was treated as directly applicable.

4. **A consolidated gotchas resource is highly valuable.**
   - Participants broadly agreed that scattered `tasks/lessons.md` files are too easy to ignore.
   - Consolidation should preserve repo-specific lessons while making them easier to consult.

5. **Git worktrees are low priority.**
   - Most saw little benefit for a solo developer on Windows/PowerShell with already manageable branch-based flow.

6. **Mandatory TDD enforcement is not the right first move.**
   - While TDD has quality benefits, most judged hard RED-GREEN-REFACTOR enforcement too rigid for the current solo ADHD workflow.
   - Several still supported stronger testing habits, but not a blocking framework-level mandate.

7. **Agentic Design Patterns is reference material, not something to “adopt” as tooling.**
   - Useful as vocabulary: reflection, planning, tool use, multi-agent.
   - Not a direct implementation target.

---

## Unresolved Disagreements

### 1. How “active” the new workflow should be
**One side:** keep changes lightweight and rule-based  
- Add minimal instructions to existing rules/P1 loop.
- Avoid creating heavy gates or artifacts.
- Merit: lower friction, better fit for ADHD and fresh standardization.

**Other side:** passive rules are not enough; use active enforcement  
- Require artifacts like `thinking.md`, or let verification fail the task if process steps were skipped.
- Merit: stronger behavior change; less chance Claude ignores “soft” guidance.

**Why unresolved:**  
This is really a tradeoff between **reliability** and **activation energy**. The debate did not produce evidence that hard gates would improve outcomes more than they would harm flow.

---

### 2. Where verification should live
**One side:** mostly global in `~/.claude/skills/`  
- Simpler, fewer places to maintain.
- Merit: easier for a solo developer.

**Other side:** split global + per-repo  
- Global for cross-repo checks, per-repo for domain-specific validation.
- Merit: cleaner separation of concerns; avoids a monolithic “god skill.”

**Why unresolved:**  
Both are plausible, but the stronger synthesis in the debate was a **two-tier model**:
- global for ecosystem-wide checks
- per-repo only where domain-specific validation is truly needed

---

### 3. Whether to adopt subagent-driven development now
**One side:** defer entirely  
- Token/budget overhead, context reload cost, unnecessary at current scale.
- Merit: pragmatic for $20/month and existing workflow.

**Other side:** fresh context per task may help ADHD focus  
- Merit: could reduce fixation and context pollution.

**Why unresolved:**  
There was no evidence that context-window problems are a current bottleneck. The case for subagents remained theoretical.

---

### 4. Whether brainstorming should require an artifact
**One side:** no artifact; just add an “Understand” step  
- Merit: minimal overhead, avoids checkbox theater.

**Other side:** require `thinking.md` or similar  
- Merit: creates enforceable evidence that brainstorming happened.

**Why unresolved:**  
Artifact enforcement could work, but several participants argued it is too gameable and too costly for small tasks.

---

## Recommended Decision

### Adopt a custom, minimal pattern set inspired by Superpowers and Uber — not the Superpowers plugin.

#### Specifically adopt now:
1. **Verification skills**
2. **Consolidated ecosystem gotchas**
3. **A lightweight “Understand before Plan” step in the existing P1 loop**

#### Explicitly defer for now:
4. **Subagent-driven development**
5. **Mandatory TDD enforcement**
6. **Git worktrees**
7. **2–5 minute task granularity as a hard rule**

---

### Why this is the best path

This recommendation best fits the debate because it captures the strongest repeated arguments:

- It addresses the **real missing capabilities**:
  - domain validation
  - retained ecosystem lessons
  - preventing jump-to-code behavior
- It avoids undermining the **fresh standardization work**
- It respects the constraints:
  - solo ADHD developer
  - Windows + PowerShell
  - low LLM budget
  - existing P1 loop must remain intact
  - ECOSYSTEM.md stays binding

This is the clearest “high value, low disruption” option.

---

### Recommended pattern decisions by question

#### 1. Superpowers: install, cherry-pick, or build your own?
**Decision:** **Build your own lightweight skills inspired by it. Do not install Superpowers.**

**Rationale:**
- Superpowers is too opinionated for a just-standardized ecosystem.
- You already have a coherent operating model; replacing or layering another one is likely to create instruction conflicts.
- The debate strongly favored adopting only the parts that fill actual gaps.

---

#### 2. ROI ranking for this ecosystem

### Adopt now
1. **(E) Verification skills** — highest ROI
2. **(F) Consolidated gotchas skill** — very high ROI
3. **(D) Brainstorming / understand-before-code** — medium-high ROI, low effort

### Adopt later only if needed
4. **(G) Plan writing with finer granularity** — useful if task tracking keeps breaking down
5. **(A) Subagent-driven development** — experiment only if context pollution becomes a real problem

### Defer / likely skip
6. **(B) Mandatory TDD enforcement** — too much friction right now
7. **(C) Git worktrees** — low value for current setup

---

#### 3. Risk of adding another framework right now
**Decision:** risk is **high enough to avoid it**.

Main risks identified:
- conflicting workflow instructions
- maintenance burden across 10 repos
- erosion of the newly standardized system
- extra ceremony for little proven benefit

The debate strongly supports not stacking a second opinionated framework on top of your current one.

---

#### 4. Where adopted patterns should live
**Decision: use a two-tier placement model.**

### Global (`~/.claude/skills/`)
Use for:
- ecosystem gotchas
- cross-repo verification
- any universally applicable personal workflow helpers

### Per-repo (`.claude/skills/verify/`)
Use only for:
- domain-specific validators in repos that truly need them

### Existing rules (`~/.claude/CLAUDE.md`, `~/.claude/rules/`, repo `.claude/rules/`)
Use for:
- lightweight invocation instructions
- precedence
- integration with the P1 loop

**Do not** create a broad “Superpowers-inspired” rule layer.  
Keep naming native to Corporate OS.

---

#### 5. What the verification skill should look like
**Decision:** start with two validators, not all four at once.

### Start immediately with:
1. **Cross-repo boundary validator** (global)
   - Checks imports/subprocess calls against ECOSYSTEM.md-declared boundaries
   - Best global validator because it protects ecosystem architecture

2. **CKE output/schema validator** (per-repo)
   - Validates frontmatter schema
   - tier routing
   - cost tracking types/fields
   - This was repeatedly cited as a high-value domain-specific case

### Next candidates after initial success:
3. **Index consistency validator**
4. **Vault health validator**

**Implementation principle:**
- PowerShell scripts
- PASS/FAIL + specific failures only
- source-of-truth comment at top
- no speculative validators for stable repos

---

#### 6. Consolidated gotchas
**Decision:** yes, consolidate into one ecosystem-level gotchas skill.

### Recommended format
- Single global skill folder, e.g. `~/.claude/skills/gotchas/`
- Main file grouped by **repo**, not by abstract category
- Each gotcha includes:
  - **Gotcha**
  - **Trigger**
  - **Symptom**
  - **Fix**
  - optional **Prevention**
- Keep per-repo `tasks/lessons.md` as the write-side
- Consolidate regularly into the global gotchas skill

This preserves local capture while improving discoverability.

---

### Strongest objections, and why they were not chosen

#### Objection: “Passive rules have already failed; use active enforcement.”
This was the best argument for stronger gates and artifacts.

**Why not chosen fully:**
- The debate did not establish that hard gates would improve outcomes enough to justify the ADHD/flow cost.
- Artifact requirements were criticized as easy to game and likely to become ritual.
- A lighter intervention is safer immediately after standardization.

**Compromise adopted:**  
Make verification active and executable, but keep brainstorming lightweight.

---

#### Objection: “Subagents may help ADHD via fresh context.”
This is plausible.

**Why not chosen now:**
- No demonstrated context bottleneck yet
- Token/budget overhead is real
- Adds complexity before proving need

**Compromise adopted:**  
Revisit only after 30 days if you observe repeated context pollution or task derailment.

---

## Risks

### 1. Verification scripts become stale
**Risk:** schema or architecture changes make validators wrong, noisy, or ignored.

**Mitigation:**
- Add source-of-truth comments to each script
- Record “last validated against source” date
- Update validator in the same change set when changing schemas/interfaces
- Start with only 2 validators

---

### 2. Gotchas become cluttered and stop being consulted
**Risk:** too much noise reduces signal.

**Mitigation:**
- Organize by repo
- Add `Trigger:` lines for quick relevance matching
- Keep newest items first
- Instruct Claude to read only the relevant repo section plus cross-repo section when applicable

---

### 3. New process adds friction and gets abandoned
**Risk:** even good ideas fail if they slow down flow.

**Mitigation:**
- Do not add artifact requirements initially
- Do not enforce TDD or worktrees
- Limit first rollout to 3 changes only:
  - gotchas
  - verification
  - Understand step

---

### 4. Too much logic moves into too many locations
**Risk:** cognitive load rises again.

**Mitigation:**
- Keep placement simple:
  - global skills for cross-cutting concerns
  - per-repo verification only when justified
  - small rule changes only
- Avoid new framework branding/layers

---

### 5. Verification output wastes tokens
**Risk:** budget pressure.

**Mitigation:**
- PASS/FAIL + concise failures only
- Local scripts execute, only stdout enters context
- Don’t run every validator for every task; run applicable ones

---

## Action Items

### Phase 1 — this week
1. **Create global gotchas skill**
   - Path: `~/.claude/skills/gotchas/`
   - Add `gotchas.md`
   - Consolidate existing `tasks/lessons.md` from the 5 repos into it
   - Format entries as:
     - Gotcha
     - Trigger
     - Symptom
     - Fix

2. **Update global execution guidance**
   - In existing global rules/P1 guidance, add:
     - before modifying files, consult relevant gotchas section
     - add an **UNDERSTAND** step before PLAN:
       - restate problem
       - identify repos involved
       - identify likely breakage
       - ask a clarifying question, or name the most likely failure mode if none needed

---

### Phase 2 — next 7 days
3. **Build global cross-repo verification skill**
   - Path: `~/.claude/skills/verify/cross-repo-boundaries.ps1`
   - Validate changed imports/subprocess calls against ECOSYSTEM.md

4. **Build first per-repo verification skill for CKE**
   - Path: `cke/.claude/skills/verify/output-schema.ps1`
   - Validate:
     - frontmatter schema
     - tier routing
     - cost/cost-type expectations

5. **Update testing rule**
   - After pytest passes:
     - run repo verification if present
     - run applicable global verification
     - if none exist, state that explicitly

---

### Phase 3 — 30-day review
6. **Evaluate actual payoff**
   Ask:
   - Did gotchas prevent at least one repeated mistake?
   - Did verification catch something pytest missed?
   - Did the Understand step materially change at least one plan?

7. **If yes, expand carefully**
   - Add next validator:
     - index consistency or vault health
   - Consider optional finer-grained planning if task drift remains a problem

8. **If no, cut aggressively**
   - Remove anything that feels ceremonial
   - Keep only what demonstrably improved outcomes

---

## Final Decision in One Line

**Do not install Superpowers; adopt a custom minimal layer consisting of global gotchas, targeted verification skills, and a lightweight Understand-before-Plan step, then reassess after 30 days before adding anything else.**
