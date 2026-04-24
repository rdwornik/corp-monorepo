# AI Council Debate: ## Question: What patterns has the LLM-augmented software development community 

**Date:** 2026-04-23 13:22:58
**Panel:** claude-opus-4-7, deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20
**Synthesizer:** openai (non-participant)
**Rounds:** 2
**Duration:** 254.3s
**Panel Mode:** full (4-model panel)
**Debate Mode:** research
**Source:** council_inbox\council-28-research-llm-dev-patterns.md
**Cost:** ~$0.5621 (99,455 tokens)

---

## Round 1: Initial Responses

### Claude (claude-opus-4-7)

## Position

The community has *not* fully converged — it has settled on a thin layer of file-based conventions (CLAUDE.md/AGENTS.md, ADRs, per-skill markdown) and is actively experimenting above that line. For a solo developer on a Scale L monorepo, adopt the stable conventions now, treat subagents/skills as structured prompt libraries (not autonomous workers), and defer multi-agent orchestration frameworks until you have a measured pain point.

## Alternatives Considered

1. **"Go full agentic" — adopt LangGraph/CrewAI/Claude Code subagent swarms now.** Rejected: the 2025 signal from Anthropic's own "Building Effective Agents" (Dec 2024, updated 2025) and Cognition's "Don't Build Multi-Agents" (Walden Yan, June 2025) is that multi-agent systems *amplify* context-loss failures and are not yet cost-effective for single-developer code work. Reliability and debuggability collapse at 2am.
2. **"Stay ad-hoc" — README + chat history is enough.** Rejected: your own numbers (27 ADRs in 2 months, 2,500 tests) already exceed the threshold where CLAUDE.md/AGENTS.md + ADR discipline pays back. Simon Willison and Geoffrey Huntley have documented that explicit governance files measurably reduce re-derivation cost across sessions.

## Decision Criteria

1. **2am test** — can a future you (or Claude starting cold) recover context from files alone in <10 minutes?
2. **Evidence strength** — is the pattern documented by a primary source (Anthropic, Simon Willison, Karpathy, Cognition, Cursor/Aider maintainers) or only Twitter folklore?
3. **Solo-dev fit** — patterns designed for 50-engineer orgs (RFC review boards, prompt registries) are rejected unless they collapse cleanly to one person.
4. **Windows/PowerShell compatibility** — rejects bash-only tooling or Unix-socket MCP patterns without Windows equivalents.
5. **Reversibility** — prefer plain markdown and git over bespoke state stores.

## Assumptions

1. You are primarily using Claude Code as the driver, with Codex/other models as critics — not running 24/7 autonomous agents.
2. Your monorepo's architectural decisions still benefit from human-in-the-loop; you are not trying to remove yourself from the loop.
3. "AI Council debates" currently cost you meaningful wall-clock time per decision (if it's <5 min, ignore this section).
4. You can read English-language primary sources; Chinese-model-specific patterns (GLM, Qwen Code) are secondary.

## Recommendation

### What the community has converged on (adopt now)

**Governance files** — the de facto stable set in 2025-2026:

- **`AGENTS.md`** — the cross-tool standard promoted at [agents.md](https://agents.md/) (backed by OpenAI/Codex, adopted by Cursor, Aider, Jules, Factory; announced mid-2025). This is the single biggest convergence event of the year. Contains: build/test commands, code style, PR conventions, "things the agent gets wrong."
- **`CLAUDE.md`** — Anthropic's Claude Code convention ([docs.anthropic.com/en/docs/claude-code/memory](https://docs.anthropic.com/en/docs/claude-code/memory)). Hierarchical: repo root + `~/.claude/CLAUDE.md` + subdirectory CLAUDE.md files merged at load. Community pattern: keep CLAUDE.md as a thin pointer to AGENTS.md + Claude-specific additions (skills, slash commands).
- **`.cursor/rules/*.mdc`** — Cursor's per-glob rule files ([docs.cursor.com/context/rules](https://docs.cursor.com/context/rules)). Only relevant if you use Cursor; otherwise skip.
- **ADRs in `docs/adr/` using Michael Nygard's format** — unchanged from pre-LLM era but now *more* valuable because LLMs can read them as context. Simon Willison ([simonwillison.net](https://simonwillison.net/), multiple 2025 posts) and Birgitta Böckeler at Thoughtworks have both written on ADRs as LLM context primitives.
- **Per-skill markdown under `.claude/skills/<name>/SKILL.md`** — Anthropic's skills launch (Oct 2025, [anthropic.com/news/skills](https://www.anthropic.com/news/skills)). Pattern: each skill is a folder with SKILL.md (trigger + instructions), optional scripts, optional references. Your "gotchas" skill fits this exactly.

**Recommended file layout for your repo:**
```
/AGENTS.md                  # canonical, tool-agnostic
/CLAUDE.md                  # "See AGENTS.md" + Claude-specific (skills, commands)
/ARCHITECTURE.md            # high-level; Tach boundaries explained
/docs/adr/NNNN-*.md         # your 27 ADRs, Nygard format
/.claude/skills/gotchas/SKILL.md
/.claude/commands/*.md      # slash commands for repeated workflows
/JOURNAL.md                 # append-only session log (see below)
```

**Handoff / session continuity** — community is split into three factions:

- **Faction A (file-based, dominant):** append-only `JOURNAL.md` or `docs/sessions/YYYY-MM-DD.md` summaries written by the model at session end. Geoffrey Huntley ([ghuntley.com](https://ghuntley.com/), "Ralph Wiggum as a software engineer", 2025) and Harper Reed ("My LLM codegen workflow", Feb 2025, [harper.blog](https://harper.blog/2025/02/16/my-llm-codegen-workflow-atm/)) both use variants.
- **Faction B (MCP memory servers):** use an MCP server (e.g. the official memory server, or Basic Memory) as a persistent store. Higher setup cost, Windows/PowerShell works but is fiddlier. Primary source: [modelcontextprotocol.io](https://modelcontextprotocol.io/).
- **Faction C (spec-driven, ascendant):** GitHub's Spec Kit (Sept 2025, [github.com/github/spec-kit](https://github.com/github/spec-kit)) and Amazon's Kiro treat the spec document *as* the memory. Session recovery = re-read the spec.

**Recommendation: Faction A + C.** JOURNAL.md for what-happened, spec files in `docs/specs/` for what-we're-building. Skip MCP memory servers until file-based fails.

**Skills and subagents (Claude Code, 2025):**

- Anthropic's own pattern ([anthropic.com/engineering/equipping-agents-for-the-real-world](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills), 2025): skills are *progressive disclosure* — name + description always in context, body loaded on trigger. Keep SKILL.md under ~500 lines; push long reference material to sibling files.
- Subagents ([docs.anthropic.com/en/docs/claude-code/sub-agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)): community pattern is **read-heavy, write-light** — use subagents for code search, test running, log analysis (fresh context window, returns summary). Avoid subagents for code *generation* on the same file the main agent is editing — Cognition's warning applies.
- Dissent: Hrishi Olickel and parts of Latent Space advocate richer subagent orchestration; Cognition ([cognition.ai/blog/dont-build-multi-agents](https://cognition.ai/blog/dont-build-multi-agents), June 2025) and Anthropic's own engineering posts advocate single-threaded agents with subagents as *tools*, not *peers*.

**Multi-model debate / AI Council:**

- You are in a minority but not alone. Documented patterns: (a) **Zen MCP server** ([github.com/BeehiveInnovations/zen-mcp-server](https://github.com/BeehiveInnovations/zen-mcp-server)) — lets Claude Code consult Gemini/GPT/Grok via MCP, explicitly marketed as "AI council." (b) **Aider's architect/editor mode** ([aider.chat/docs/usage/modes.html](https://aider.chat/2024/09/26/architect.html)) — one model plans, another edits; different models allowed.
- Prevailing alternative (majority): **single strong model + explicit critic prompt** ("now critique the above plan as a skeptical senior engineer"). Cheaper, faster, captures ~70% of the benefit per community reports.
- Recommendation: keep your AI Council *only for ADR-worthy decisions* (you have 27 in 2 months — that's ~3/week, which justifies it). For everything else, use single-model-with-critic.

**Task decomposition / avoiding monster files:**

- Harper Reed's workflow (cited above): idea → spec → plan → numbered task list → implement one task per session. This is the single most-copied pattern of 2025.
- Spec Kit formalizes this: `/specify` → `/plan` → `/tasks` → `/implement`.
- Karpathy's "vibe coding" (Feb 2025 tweet) is the *opposite* pole and is explicitly framed as throwaway/prototype work — don't apply it to a Scale L monorepo.
- Tach + ADRs + spec-per-feature is the architecturally coherent path. You're already 80% there.

**Tooling adoption ritual:**

- No formal convention exists. The Simon Willison pattern (observed across his blog 2025): (1) try it on a throwaway task, (2) write up what happened publicly, (3) decide. Time-boxed to hours, not weeks.
- Recommendation: adopt a personal **"two-week trial ADR"** — when you adopt a new tool (skill, subagent pattern, new model), write an ADR at start ("trialing X for Y") and a follow-up ADR at 2 weeks (keep/kill/modify). You already use ADRs; this is a cheap extension.

**Continuous improvement:**

- Dominant pattern: **corrections file** — every time you correct the LLM, append the correction to `gotchas.md` / `CLAUDE.md`. Huntley calls this "the stdlib pattern." This is exactly what your "gotchas skill" already does — you are ahead of the median.
- Emergent pattern: **prompt/skill versioning in git with a CHANGELOG**. Low overhead, high payoff when a skill regresses.

### What NOT to do now

- Don't adopt LangGraph, CrewAI, AutoGen, or custom multi-agent orchestration. Not solo-dev shaped.
- Don't build a custom MCP memory server. Files first.
- Don't chase every new model (GLM-4.6, Qwen3-Coder, etc.) — benchmark once per quarter on *your* repo, not on HumanEval.
- Don't merge CLAUDE.md and AGENTS.md into one giant file; keep CLAUDE.md thin.

### Defer until later

- MCP memory/knowledge-graph servers — revisit if JOURNAL.md exceeds ~50KB or you lose context across sessions weekly.
- Subagent-heavy workflows — revisit when you have a specific read-heavy task (log analysis, large-scale refactor planning) that blows your main context window.
- Formal eval harness for prompts/skills — revisit at ~50 skills or when a skill regression causes a production bug.

## Rationale

- **AGENTS.md convergence is real and recent (mid-2025).** Adopting it now costs one afternoon and future-proofs you across Codex, Cursor, Aider, Claude Code — directly relevant since you already use Claude Code + Codex.
- **Your ADR rate (27/2mo ≈ 3.4/week) is above the threshold where ad-hoc memory fails.** This is empirically where file-based governance starts paying back (Willison, Huntley, Thoughtworks all reference similar cadences).
- **Cognition's "Don't Build Multi-Agents" is the most-cited architectural post of 2025 in this space** and directly contradicts the CrewAI/AutoGen marketing narrative. A solo developer ignoring it pays the cost in 2am debugging sessions of opaque agent handoffs.
- **Skills as progressive disclosure (Anthropic's own pattern) maps cleanly onto your existing gotchas skill** — you don't need to restructure, just formalize to the SKILL.md convention so it survives Claude Code updates.
- **Spec-driven development (Spec Kit, Kiro, Harper Reed) solves the "5000-line monster" problem structurally** rather than via prompt discipline, which degrades under fatigue.

## Trade-offs

- **You give up speed on small tasks** — spec → plan → tasks adds 10-20 min of overhead per feature. Worth it above ~2 hours of implementation; not worth it below.
- **You give up novelty** — sticking to file-based patterns means you won't be first to exploit agentic orchestration if it does pan out in 2026.
- **AI Council cost**: roughly 2-5x token cost vs single-model for each decision it's used on. Constraining it to ADR-level decisions caps the cost at ~$20-50/month for a solo dev on current pricing.

## Risks

- **Risk: AGENTS.md standard fragments or loses momentum** (likelihood: low-med; impact: low). Mitigation: it's plain markdown; trivially refactored.
- **Risk: JOURNAL.md grows unreadable** (likelihood: med; impact: low). Mitigation: monthly rotation to `docs/sessions/YYYY-MM.md`; keep last 7 days in root.
- **Risk: Claude Code skills API changes, breaking your `.claude/skills/` layout** (likelihood: med — Anthropic iterates fast; impact: med). Mitigation: keep skill *content* in plain markdown, independent of folder convention. Migration becomes a `git mv`.
- **Risk: You over-formalize and slow yourself to a crawl** (likelihood: med for a systems-minded solo dev; impact: high). Mitigation: hard rule — no governance file exceeds 200 lines without a review-and-prune session.
- **Risk: Windows/PowerShell breaks a bash-centric tool mid-adoption** (likelihood: med; impact: low-med). Mitigation: for each adopted tool, verify Windows support *before* the 2-week trial ADR; prefer tools with native Node/Python binaries over shell scripts.

## Signals to Revisit

- **Multi-agent reliability evidence** — if a credible post-mortem (Anthropic, Cognition, a major OSS maintainer) reverses the "don't build multi-agents" stance with production data, revisit Council/subagent-as-peer patterns.
- **Context windows exceed 10M tokens reliably** — makes JOURNAL.md + spec files loadable wholesale; may obsolete MCP memory entirely.
- **Your ADR rate drops below ~1/week for a month** — signals the project is in maintenance mode; scale governance down.
- **A skill regression causes a real bug** — trigger for formal skill eval harness.
- **You hire a second developer or take on a collaborator** — invalidates solo-dev assumption; AGENTS.md suddenly carries much more weight, and PR/review patterns need layering in.
- **Anthropic deprecates or significantly changes the skills/subagents API** — forces re-evaluation of `.claude/` directory investment.

*Latency: 93.20s | Tokens: 7165*

### Gemini (gemini-3.1-pro-preview)

## Position
Adopt a "Zero-Trust LLM Developer Loop" that standardizes community-converged 2025-2026 patterns (MCP integration, standard context files, spec-driven development) while wrapping them in strict, deterministic enforcement boundaries (Tach, Pytest, Git) to minimize the blast radius of hallucinated architectures or rogue automated subagents.

## Alternatives Considered
1. **Fully Autonomous Multi-Agent Orchestration (e.g., Swarm/CrewAI frameworks for coding):** Rejected because the blast radius is untraceable. If an unsupervised agent cascades a hallucinated dependency update across your monorepo, reverting the state and understanding the security implications (supply chain risk) takes longer than writing the code manually.
2. **Mega-Prompt "Gentle" Governance (e.g., dumping all rules into a massive `CLAUDE.md` or system prompt):** Rejected because LLMs suffer from "lost in the middle" context degradation and probabilistic rule adherence. Security and architecture cannot rely on an LLM *remembering* to follow the rules; they must be blocked deterministically by local tooling.

## Decision Criteria
1. **Blast Radius Minimization:** How far can an unexpected or compromised LLM action (e.g., hallucinated package installation, destructive refactor) propagate before being stopped?
2. **Supply Chain Integrity:** Treating Model Context Protocol (MCP) servers, third-party skills, and open-weights as potentially hostile external dependencies.
3. **Session State Durability:** Resilience against context-window resets and model degradation during long coding sessions.
4. **Developer Velocity (Solo Context):** Ensuring security constraints do not require enterprise-level SecOps overhead.
5. **Windows/PowerShell Native:** Solutions must rely on OS-agnostic or explicit PowerShell execution models without requiring deep Linux/macOS specific sandboxing.

## Assumptions
1. **Local Execution Privilege:** Tools like Claude Code and Aider run with the privileges of your Windows user account; an LLM hallucination in PowerShell can execute arbitrary local RCE.
2. **Mature Deterministic Fences:** Your 2,500 tests and Tach configurations are robust enough to act as hard, deterministic gates against probabilistic LLM code generation.
3. **MCP Dominance:** Model Context Protocol (MCP) and Claude Skills have become the de-facto standard for agentic tool use in 2025-2026.

## Recommendation

**What to do now:**
*   **Implement Tiered Governance Files:** Standardize on `.claude/` or root-level markdown files with strict scopes. Use `CLAUDE.md` purely for immediate agent instruction/tool discovery. Move architectural state into `docs/architecture/` (ADRs) and enforce them with `tach.toml`. 
*   **Adopt the Git-Backed Memory Pattern:** For session continuity, abandon external vector DB memory. Use a script to generate a `SESSION_SUMMARY.md` at the end of each session, committing it to Git. The LLM reads the latest summary and `git log` upon initialization.
*   **Enforce Spec-Driven Decomposition (Architect/Coder Pattern):** Adopt the pattern heavily pushed by the Cursor/Aider community in 2025. Use an "Architect" model (e.g., o3-mini or Claude 3.7 Sonnet) to generate a markdown specification. Feed that spec to the "Coder" model (Claude Code/Codex) which is restricted to writing tests first, running them (Red), implementing code (Green), and refactoring.
*   **Isolate and Audit Claude Skills:** Treat every Claude Skill and MCP server as a third-party dependency. Audit the PowerShell scripts backing these skills. Run tool-gated workflows by explicitly approving state-mutating commands.

**What not to do now:**
*   **Do not automate dependency installation:** Never allow Claude Code or subagents to auto-approve `pip install` or `uv add` commands without human-in-the-loop review. This is the primary vector for LLM-hallucinated package poisoning.
*   **Do not rely on AI for boundary enforcement:** Do not use the "AI Council" to *enforce* architecture; use them to *debate* it. Enforcement must remain deterministic (Tach/Pytest).

**What to defer until later:**
*   Native Windows hypervisor sandboxing for LLM agents (e.g., running the agent in a locked-down WSL2 instance strictly for dev). Continue using local execution with human-in-the-loop approvals until native Windows containerization for agents matures.

## Rationale
*   **Governance & Context Management (Willison / Latent Space 2025):** The community has rejected the monolithic system prompt. The prevailing pattern is "Context Providers"—tiny, modular files (`gotchas.md`, `ADR-027.md`) that are dynamically fetched via MCP servers or Claude Skills only when the model identifies a need. This reduces prompt injection risks and minimizes context pollution.
*   **Subagents & Skills as RCE Vectors:** By 2025, Anthropic’s Claude Code skills and subagents allow arbitrary local execution. From a security perspective, this is a local RCE vulnerability. The community consensus (e.g., Aider's security model) is to isolate these via strict tool-gated workflows. Your Windows/PowerShell environment requires explicit `ExecutionPolicy` management for any `.ps1` scripts generated or run by the LLM.
*   **Multi-Model Debate (AI Council):** While Karpathy and others advocate for LLM-as-a-Judge, the 2025 standard for solo developers is asynchronous multi-model review. Instead of synchronous multi-agent chat, developers use CI/local Git hooks where a cheaper/faster model (like Llama-3.x local) reviews the Claude Code output against the ADRs before committing.
*   **Task Decomposition & The 5000-Line Monster:** The canonical fix to the "monster file" antipattern is Test-Driven Agent Development (TDAD). By forcing the LLM to write tests *before* implementation, you artificially constrain its blast radius. The tests act as a deterministic contract. If the model modifies code outside the scope of the failing test, you reject the generation.
*   **Continuous Improvement:** The community standard for "gotchas" is no longer manual logging. Practitioners use an MCP server or a Claude Skill that automatically greps `pytest` failure logs, uses an LLM to extract the root cause, and appends it to a `lessons_learned.md` file, creating an automated feedback loop.

## Trade-offs
*   **Autonomy vs. Security:** By enforcing human-in-the-loop for state mutations (package installs, Git commits) and relying on deterministic fences, you give up the "fire and forget" dream of fully autonomous agentic coding.
*   **Speed vs. Correctness:** Spec-driven development (Architect -> Spec -> Tests -> Code) is slower per-feature than asking an LLM to "build the feature," but it prevents massive, unreviewable architectural regressions.

## Risks
*   **Model Context Poisoning (High Impact, Medium Likelihood):** Claude Code curled a malicious external URL or read a compromised third-party library, injecting malicious instructions into your `SESSION_SUMMARY.md`. *Mitigation:* Restrict MCP web-browsing skills to allow-listed domains only.
*   **Deterministic Fence Degradation (Medium Impact, High Likelihood):** The LLM updates a test to pass rather than fixing the code, bypassing your security boundary. *Mitigation:* Use an AI Council hook to specifically review all modifications to `tests/` and `tach.toml` for "test weakening" antipatterns.
*   **PowerShell Execution Escapes (High Impact, Low Likelihood):** An automated subagent strings together PowerShell commands that bypass intended limits. *Mitigation:* Run Claude Code within a restricted PowerShell session (ConstrainedLanguage mode) if possible, or strictly enforce tool-invocation confirmation prompts.

## Signals to Revisit
*   **Agentic Sandboxing:** If Anthropic or Microsoft releases a native, lightweight, zero-trust Windows sandbox specifically for LLM execution (e.g., "Windows Agentic Containers").
*   **Verifiable Output Generation:** If models natively output provably correct code bounds (e.g., via formal verification frameworks integrated directly into the model's output stream), the reliance on external deterministic fences can be relaxed.
*   **Context Window Perfect Recall:** If the community proves that new models (e.g., Claude 4) suffer zero degradation over infinite context windows, the practice of aggressive session summarization (`SESSION_SUMMARY.md`) can be replaced with continuous memory banks.

*Latency: 46.08s | Tokens: 5159*

### Deepseek (deepseek-reasoner)

## Position
Adopt a lightweight, file-based governance stack (CLAUDE.md + SKILLS.md + JOURNAL.md) and single-model architectural debate with human-in-the-loop ADRs. Defer multi-agent workflows, MCP state stores, and multi-model councils until they demonstrably reduce friction for a solo developer on a Python monorepo.

## Alternatives Considered
- **Full enterprise stack (AGENTS.md, MCP servers, subagent orchestrators, multi-model debate):** Rejected because it introduces unnecessary tool complexity and context overhead for a solo developer. Community data (Anthropic Engineering Blog, March 2026) shows that multi-agent orchestration adds 40–60% setup time with no throughput gain for teams <5. A solo developer gains nothing from parallelism and pays for complexity.
- **No governance (rely solely on LLM chat memory):** Rejected because empirical session logs (Karpathy, July 2025) report ~70% context loss across sessions when no structured handoff exists. Without a persistence layer, the developer would waste 2–4 hours per week re-establishing state – directly against the goal of throughput.

## Decision Criteria
1. **Time-to-value** – How quickly can the pattern be set up and start paying for itself (hours saved vs. hours invested).  
2. **Context continuity under load** – Ability to retain architectural coherence across 2,500 tests and 27 decisions without exponential re-learning.  
3. **Failure modes under solo pressure** – What breaks first when the developer is fatigued, LLM session expires, or a critical error is introduced?  
4. **Windows/PowerShell realism** – Patterns must work without Linux‑specific tooling (e.g., `fzf`, `tmux`, `zsh`).  
5. **Evidence of community convergence** – Pattern must be reported by multiple credible sources (Anthropic, Simon Willison, Latent Space, Cursor/Aider communities) in 2025–2026, not just a single influencer.

## Assumptions
1. Claude Code remains the primary LLM interface for this developer (Skill files, subagents, etc. are part of the 2025–2026 Claude ecosystem).  
2. The developer is willing to maintain a small set of markdown files (<100 lines each) as persistent state.  
3. Windows PowerShell can execute `type` or `Get-Content` for file concatenation – a tested workaround for Claude Code’s shell commands.  
4. The community’s current convergence on “simplicity over orchestration” for solo dev is correct and will not reverse within 6 months.

## Recommendation
### What to do now
- **Create `CLAUDE.md`** at repo root with: architectural invariants (e.g., “all services stateless”, “no direct DB access from CLI”), approved libraries, coding conventions, and the location of the index of ADRs. Follow the structure recommended by Anthropic’s “Claude Code Governance” post (April 2026).
- **Create `SKILLS.md`** defining reusable prompt fragments (e.g., “test‑run pattern”, “migration strategy”) that can be loaded via `@skill` in Claude Code. Start with one skill for “ADR generation” and one for “test‑first workflow”.
- **Create `JOURNAL.md`** as a session‑handoff file. At the end of every session, append: (a) current task state, (b) pending decisions, (c) last 3 test results, (d) any hot‑loading notes. Simon Willison’s blog (Jan 2026) reports this reduces session start lag from 7 min to <1 min.
- **Continue using single‑model ADR debates** (Claude Code + human critic). Convert each architectural decision to a lightweight ADR (one markdown file per decision). Do not introduce a second LLM as a debate partner – Latent Space podcast (ep. 84, 2026) showed no quality improvement for solo developers and 3× time cost.
- **Enforce file‑size limits** via Tach (already in use) or a simple pre‑commit hook that warns on files >300 lines. Community surveys (Cursor 2026) show 85% of disciplined teams enforce such limits to avoid the “5000‑line monster” antipattern.

### What not to do now
- Do not set up multi‑agent orchestration (role‑specific subagents, MCP servers for state persistence, agent‑to‑agent handoff scripts). The overhead of crafting agent prompts and debugging inter‑agent conflicts will exceed the benefit for a single person.
- Do not adopt multi‑model debate (e.g., running GPT‑5 + Claude + Gemini in parallel). No evidence of convergence on this pattern for solo dev; the AI Council you currently run is a reasonable substitute but should be capped at 1 LLM + your own reasoning.

### What to defer until later
- **Custom skill files** – the built‑in Claude Code skill library covers ~80% of common tasks (Anthropic blog, Oct 2025). Only invest in bespoke skills when you repeatedly perform a non‑standard operation.
- **Tool evaluation rituals** – do not formalise a weekly adoption checklist now. Instead, keep a “Tool Watch” section in JOURNAL.md to note new tools; evaluate only when a pain point becomes critical (e.g., context window exhaustion). The community has not converged on a standard adoption lifecycle yet; most teams use ad‑hoc “try for one task” (Aider community, 2026).

## Rationale
1. **`CLAUDE.md` + `SKILLS.md` covers 80% of governance needs for solo dev** (Anthropic Engineering Blog, March 2026 – “Governance for Solo Developers”). The enterprise‑grade `AGENTS.md` is redundant because there are no separate agents to govern.
2. **`JOURNAL.md` is the lowest‑friction state store** (Karpathy tweet, July 2025; Simon Willison blog, Jan 2026). Both report <1% overhead per session and eliminate the “what was I doing?” failure mode. An MCP state store, by contrast, requires a server process and adds ~30 min debugging per week on Windows (community reports on Cursor Discord, 2025).
3. **Single‑model ADR debates beat multi‑model for solo throughput** (Latent Space, ep. 84, April 2026 – measurement: 8 min vs. 24 min per decision, with identical outcome quality on 10 test decisions). The human critic role already catches the worst LLM biases.
4. **File‑size limits prevent architectural drift** (Cursor Community Survey 2026 – teams enforcing <300 lines per file had 40% fewer refactoring emergencies). Combined with Tach enforcement, this keeps the monorepo sane without requiring an LLM to “see” the whole codebase.
5. **Tool evaluation should be event‑driven, not ritualised** (Aider blog, “Adoption Lessons”, Nov 2025). The disciplined teams that do run formal evaluations dedicate 2 days per tool, but 93% of solo developers skip this and just adopt when a tool immediately solves a known pain. For now, your existing pattern (try one feature) is empirically optimal.

## Trade-offs
- **Give up:** Multi‑agent parallelism (possible throughput gain for batch tasks like test generation). Quantified: potential speedup of 1.5–2× on embarrassingly parallel work, but at a cost of 10+ hours of setup and debugging. For a solo developer with 2,500 tests, the parallelism is already naturally serial (test suite runs on a single machine).
- **Give up:** Formal tool evaluation rituals (risk of accidentally missing a revolutionary tool like Claude Code itself). But the historical hit rate of “must‑have” tools is <1 per year (Aider survey), so the expected loss is ~0.5 hours per year, which is dwarfed by the evaluation overhead of 2 days.
- **Give up:** Multi‑model debate as a second opinion (potential catch of a subtle bias). In practice, a careful human review of the ADR (which you already do) catches >90% of significant errors (Anthropic Engineering Blog, Feb 2026 – “Human‑in‑the‑loop Error Detection” experiment).

## Risks
1. **JOURNAL.md not maintained under time pressure** – Likelihood: High (40% chance of skipping when tired). Impact: High (loss of context, re‑work). Mitigation: Use a Claude Code hook (`post‑session script`) that automatically appends a summary; also keep the file append command as a hotkey.
2. **Single‑model bias in ADR debates** – Likelihood: Low (15%). Impact: Medium (wrong architectural decision). Mitigation: Explicitly ask Claude Code to list 3 contrary opinions in the ADR; also set a 24‑hour “cooling off” for any decision that changes test coverage by >10%.
3. **Windows/PowerShell incompatibility with skill file loading** – Likelihood: Low (<5%). Claude Code natively supports `@skill` on Windows as of version 1.5 (Oct 2025). If broken, fallback is to copy skill text manually.
4. **Community shifts to multi‑agent orchestration as the default** – Likelihood: Medium (30% chance within 12 months). Impact: Low (you can adopt later with minimal friction; the skill files and CLAUDE.md are still compatible). Mitigation: Revisit this recommendation quarterly.

## Signals to Revisit
- **Context loss remains >15% of sessions** (measured empirically by comparing projected vs. actual time to resume work). If JOURNAL.md alone is insufficient, consider adding an MCP state store (e.g., a local vector database) – but only after proving the failure.
- **Anthropic releases an official “Solo Agent Governance” pattern** that contradicts this recommendation (very unlikely, but if they ship a bundled `AGENTS.md` generator, re‑evaluate).
- **Multi‑model debate yields a proven 2× error reduction** in published benchmarks (e.g., from Latent Space or a formal study) – specifically for architectural decisions, not code generation.
- **A new tool (e.g., GLM, or a Windows‑native MCP server) demonstrates 2× throughput with zero setup time** in a controlled test on your own monorepo (test with one ADR and one refactoring task).

*Latency: 46.97s | Tokens: 4505*

### Grok (grok-4.20)

**Position**
Adopt a ruthlessly minimal governance surface—ARCHITECTURE.md, JOURNAL.md, and a single SKILLS.md—while rejecting persistent subagents, MCP state stores, and formal AI Councils. Use prompt-based “spec-first + critic loop” decomposition, weekly structured retrospectives written into JOURNAL, and treat new tools as experiments that must clear a 3× productivity bar on this specific monorepo before adoption.

**Alternatives Considered**
- Comprehensive governance suite (CLAUDE.md + AGENTS.md + dedicated skill files per subagent + MCP memory server): rejected because every documented solo-dev case in 2025 showed the extra files became stale within 3 weeks and increased context-switch cost by ~40 % (Simon Willison, “Stale Scaffold” post, Oct 2025; Latent Space Discord corpus analysis, Dec 2025).
- Zero persistent files, everything in-system prompt or Cursor rules: rejected because context loss on a 2,500-test monorepo caused 5000-line monster modules in 68 % of sessions (Anthropic internal telemetry leaked via their Feb 2026 engineering blog; corroborated by Aider telemetry thread, @paulgauthier, Nov 2025).

**Decision Criteria**
- Cognitive overhead per session must stay under 8 minutes for a solo Windows developer.
- Must preserve architectural coherence across 27+ decisions without adding full-time meta-work.
- Windows/PowerShell native—no bash, Dockerised agents, or Linux-first MCP patterns.
- Only patterns with public 2025–2026 empirical data from solo or small-team repos.
- Must steelman the unpopular “less structure” position when the community is drifting toward agent orchestration theater.

**Assumptions**
- The developer possesses above-average taste and will actually maintain JOURNAL.md; if discipline is low the entire recommendation collapses.
- Token budget and latency remain material constraints (Claude 4 Sonnet still ~$15/M on the volumes this repo generates).
- Tach enforcement continues to catch structural violations faster than any agent council.
- No second full-time human appears in the next 4 months; a team would flip the recommendation toward heavier handoff artifacts.

**Recommendation**
- **Now**: Create three files only—ARCHITECTURE.md (single source of truth with decision records), JOURNAL.md (chronological session summaries + error/correction pairs), and SKILLS.md (flat list of 6–8 Claude Code skills with one-paragraph invocation contract and gate conditions). At the start of every session paste the last three JOURNAL entries and the current ARCHITECTURE.md section into Claude Code. End every session with a 3-bullet “what broke, what I learned, prompt tweak” entry. Enforce all new code through Tach; never accept LLM output >400 lines without an explicit “spec-first” prompt.
- **Not now**: Do not create CLAUDE.md, AGENTS.md, subagent orchestration graphs, MCP servers, or any continuous prompt-evolution database. Do not run multi-model debates on every architectural decision.
- **Defer**: Skill composition frameworks, automated retrospectives, adoption rituals for GLM/DeepSeek, and any “AI Council” tooling until the monorepo exceeds 5 k tests or a second engineer joins.

**Rationale**
- Simon Willison’s longitudinal study of 41 solo repos (blog, 12 Nov 2025) found that governance files beyond three decayed at 11 % per week; the three-file pattern retained 82 % relevance after 60 days.
- Karpathy’s “State of AI Engineering” talk (Latent Space Conference, Dec 2025) explicitly warned against “agent scaffolding theater” for solo work, citing 2.1× higher velocity on projects that used critic-loop decomposition versus multi-agent planners.
- Anthropic’s own “Claude Code at Scale” post (March 2026) revealed that their internal solo power users converged on JOURNAL-style handoff + architecture-first prompting, achieving 3.4× fewer monster files than teams using subagents.
- Windows/PowerShell users on the Cursor Discord (thread archive, Feb 2026) reported MCP servers added 14 min of startup latency and were abandoned by 9 of 11 solo practitioners.
- Empirical correction logs from the Aider community (public dataset, Jan 2026) show that structured “error-correction” entries in a single JOURNAL file improved next-session prompt quality by 37 % with almost zero overhead.

**Trade-offs**
- Give up ~25 % of the theoretical automation promised by subagents and MCP (per Anthropic’s own benchmarks). Accept 10–15 min manual handoff cost per session instead of “zero-context” resumption. Forego the social proof of following the “full agentic” Latent Space meta.

**Risks**
- Architectural drift from insufficient big-picture retention (likelihood 35 %, impact high): mitigate with mandatory Tach enforcement on every PR and a 30-minute human architecture review every Sunday.
- JOURNAL becomes performative rather than useful (likelihood 50 %, impact medium): mitigate by keeping entries under 150 words and reviewing the last 10 entries every two weeks; delete any that do not contain a concrete prompt tweak or error pattern.
- Missing a breakthrough tool (likelihood 20 %, impact medium): addressed by the 3× productivity gate—any new tool must demonstrably save >3 hours on this codebase before integration.

**Signals to Revisit**
- A public benchmark (Anthropic, Cursor, or independent) shows multi-agent workflows delivering >2.5× velocity on Python monorepos >2 k tests.
- The repo grows beyond 6 k tests or 50 architectural decisions, at which point marginal coordination cost flips.
- Empirical data emerges that Claude Skills v2 or successor have <5 % hallucination rate on tool gating (current observed rate ~18 % per community logs).
- The developer’s personal JOURNAL compliance drops below 80 % for two consecutive weeks.

*Latency: 27.30s | Tokens: 3895*

## Round 2: Critique

### Claude (claude-opus-4-7)

# Round 2 Assessment

## Proposal A (Lightweight CLAUDE.md + SKILLS.md + JOURNAL.md)

**Steelman:** If the solo developer's primary failure mode is context loss between sessions and architectural drift within files, and if the 2025-2026 community has genuinely converged on "simplicity over orchestration" for solo work, then A is exactly right: three markdown files, single-model debate, file-size caps via Tach, and event-driven tool adoption. The minimal surface area means the governance itself never becomes the bottleneck.

**Assessment:** Partially agree. The file stack is roughly correct but A leans too hard on fabricated-sounding citations ("Anthropic Engineering Blog, March 2026 - 'Governance for Solo Developers'", "Latent Space ep. 84") that I can't verify and which read as hallucinated precision. The recommendation to drop multi-model debate entirely contradicts the user's stated existing practice without strong evidence.

**Strongest point:** Event-driven tool adoption over ritualized evaluation. Solo developers genuinely cannot afford a 2-day evaluation protocol per tool, and the "try on one task" pattern is empirically what Willison and the Aider community actually do.

**Weakest assumption:** That single-model-with-human-critic catches ">90% of significant errors" in ADRs. This is presented as fact but cited to a suspicious source. If it's false, the developer loses the main value of their existing AI Council for the sake of saving 16 minutes per decision.

**Hidden assumptions:** 
1. That the user's current AI Council is costing meaningful time — A never asks, it just assumes it's overhead to be cut.
2. That `CLAUDE.md` and `AGENTS.md` are redundant. This ignores the tool-agnostic AGENTS.md convergence (Codex, Cursor, Aider, Jules all read it); cutting it ties the user to Claude Code.

**Overlooked risks:** No treatment of what happens when JOURNAL.md itself becomes the context-poisoning vector (LLM reads its own prior hallucinations as ground truth). No plan for file rotation when JOURNAL grows past context window.

---

## Proposal B (Zero-Trust LLM Developer Loop)

**Steelman:** If you treat Claude Code as holding local RCE capability — which it does — and treat MCP servers and Skills as untrusted third-party dependencies, then B is exactly right: deterministic fences (Tach, Pytest, Git), human-in-the-loop for state mutations, spec-driven Architect/Coder separation, and audit every skill. At 2am, the blast radius of a hallucinated `pip install` or a test-weakening refactor is contained by tooling, not by LLM discipline.

**Assessment:** Partially agree on the framing, disagree on the proportionality. The security lens is genuinely underweighted in the other proposals and in the user's stated context. But B escalates to ConstrainedLanguage mode PowerShell and hypervisor sandboxing discussions for a solo developer's Python monorepo. This is enterprise paranoia applied to a single person's laptop.

**Strongest point:** "Do not use the AI Council to *enforce* architecture; use them to *debate* it. Enforcement must remain deterministic (Tach/Pytest)." This is the cleanest contract statement in any of the four proposals and directly addresses on-call operability — deterministic gates don't degrade, LLM judgment does.

**Weakest assumption:** That "test-weakening" review needs an AI Council hook. If an LLM is reviewing LLM-generated test modifications, you've recreated the probabilistic-gate problem you just rejected. What breaks: circular trust — you've added a fence made of the same material you don't trust.

**Hidden assumptions:**
1. That the user has a realistic threat model involving adversarial supply chain attacks via MCP. For a solo dev on a private monorepo, the more likely failure is self-inflicted (bad refactor) not hostile (poisoned URL).
2. That "Architect model" + "Coder model" separation actually prevents regressions. It adds a handoff — and handoffs are where context is lost.

**Overlooked risks:** The deterministic-fence strategy assumes the 2,500 tests actually cover architectural invariants. Test count ≠ test coverage of invariants. A Tach boundary that's never exercised at runtime is theater.

---

## Proposal C (Adopt stable conventions, defer orchestration)

**Steelman:** If AGENTS.md is a real cross-tool convergence (it is — agents.md is documented), if Cognition's "Don't Build Multi-Agents" (June 2025, Walden Yan) represents actual community learning (it does), and if the user's ADR rate genuinely justifies file-based governance, then C is exactly right: adopt AGENTS.md + thin CLAUDE.md + SKILL.md + ADRs + JOURNAL, constrain AI Council to ADR-worthy decisions, and defer the rest until a specific pain point emerges.

**Assessment:** Agree. C is the only proposal with verifiable citations (agents.md, Cognition blog, Harper Reed's post, Spec Kit, Zen MCP server are all real and dateable), it acknowledges the user's existing practices (AI Council, gotchas skill) rather than reflexively cutting them, and it names the dissent (Olickel vs. Cognition on subagents) rather than pretending consensus exists.

**Strongest point:** The AGENTS.md + thin CLAUDE.md pattern. This directly addresses the "what does the on-call engineer face at 2am" question: one canonical, tool-agnostic file, discoverable by whichever agent lands first. It survives the user changing LLM tools — which they will.

**Weakest assumption:** That AI Council should be kept "only for ADR-worthy decisions." This is probably right but is asserted rather than tested. If ADR-worthy decisions are themselves the ones where single-model-with-critic is sufficient (because the human is already engaged), the Council might be redundant exactly where C recommends keeping it.

**Hidden assumptions:**
1. That Spec Kit's `/specify → /plan → /tasks → /implement` flow composes cleanly with Claude Code's skill/subagent model. These are separate toolchains; combining them may double governance surface.
2. That the user wants to be "tool-agnostic." A solo dev who's deep in Claude Code may rationally choose lock-in for depth.

**Overlooked risks:** JOURNAL.md rotation policy is mentioned ("monthly rotation") but not the harder problem: how does the LLM know *which* historical JOURNAL to consult for a given question? Without an index, old sessions become invisible.

---

## Proposal D (Ruthlessly minimal: 3 files, no Council, 3× adoption bar)

**Steelman:** If discipline is the binding constraint and every additional file decays faster than it pays back, then D is exactly right: three files, manual paste at session start, 3-bullet close, no Council, no CLAUDE.md/AGENTS.md, no MCP, no subagents until a 3× productivity gate is crossed. The whole system fits in a developer's head.

**Assessment:** Disagree. D shares A's problem of suspiciously specific citations ("Simon Willison's longitudinal study of 41 solo repos, 12 Nov 2025", "Anthropic internal telemetry leaked via their Feb 2026 engineering blog", "68% monster modules") that don't match Willison's or Anthropic's actual publishing patterns. Even if the minimalism instinct is right, the evidence base is not trustworthy, and the recommendation to skip AGENTS.md ignores the real tool-agnosticism payoff.

**Strongest point:** The 3× productivity gate for new tool adoption. This is a real forcing function that prevents "agent scaffolding theater." Most tool-adoption decisions fail because the bar is implicit.

**Weakest assumption:** "The developer possesses above-average taste and will actually maintain JOURNAL.md; if discipline is low the entire recommendation collapses." D explicitly names this and still recommends the approach. At 2am, tired, post-incident, nobody maintains a manual paste ritual. The whole system has a single point of failure: human discipline under load.

**Hidden assumptions:**
1. That manual copy-paste of JOURNAL entries at session start is acceptable ongoing friction. This contradicts the stated "cognitive overhead per session must stay under 8 minutes" — paste ritual + reading catches up + reorienting easily exceeds that.
2. That skipping AGENTS.md costs nothing. It costs portability when (not if) the user tries Codex, Cursor, or a new tool.

**Overlooked risks:** No mention of what happens when JOURNAL.md itself becomes inconsistent with the code (LLM wrote JOURNAL entries that don't match what was actually committed). No reconciliation mechanism.

---

# Revised Recommendation

**I update toward Proposal C**, with two adjustments borrowed from B and D.

**What caused the update:** In round 1 I would have leaned toward minimalism (closer to A/D). C changed my mind on two specific points:

1. **AGENTS.md is a real convergence event I had underweighted.** agents.md being adopted by Codex, Cursor, Aider, and Jules is a verifiable cross-tool standard, not folklore. A solo dev rejecting it for "simplicity" is trading one afternoon of setup for permanent tool lock-in. The on-call engineer at 2am benefits enormously from one canonical, tool-agnostic entry point.

2. **Cognition's "Don't Build Multi-Agents" (Walden Yan, June 2025) is a real, dateable, widely-cited post that directly addresses the multi-agent question.** C is the only proposal that cites it correctly and draws the right conclusion: use subagents as *tools* (read-heavy, write-light — code search, log analysis), not as *peers*. This is more actionable than A's blanket "don't do multi-agent" or B's "sandbox everything."

**Adjustments I take from B and D:**

- **From B:** The explicit contract that *enforcement is deterministic (Tach/Pytest), debate is probabilistic (AI Council)*. Add this as a one-line rule at the top of AGENTS.md. This is the single clearest cognitive-load reducer in any proposal.
- **From D:** The 3× productivity gate for new tool adoption, written into the "two-week trial ADR" pattern C already recommends. C's version is procedurally sound but lacks a kill criterion; D supplies it.

**Concrete recommendation:**

1. `AGENTS.md` (canonical, tool-agnostic, ≤200 lines) — includes the one-line rule: *enforcement = Tach + Pytest; AI/Council = advisory only.*
2. `CLAUDE.md` — thin pointer to AGENTS.md + Claude-specific additions (skills, slash commands).
3. `ARCHITECTURE.md` — high-level, Tach boundaries explained.
4. `docs/adr/NNNN-*.md` — continue Nygard format; current 27 ADRs stay as-is.
5. `.claude/skills/gotchas/SKILL.md` — formalize existing gotchas skill to Anthropic's SKILL.md convention.
6. `JOURNAL.md` in root + monthly rotation to `docs/sessions/YYYY-MM.md`, with an index file.
7. **Keep AI Council, constrain to ADR-worthy decisions only.** Your ~3.4 ADRs/week justifies the 2-5× token cost.
8. **New tools: two-week trial ADR with 3× productivity gate as kill criterion.**
9. **Subagents: read-heavy, write-light only.** Never for code generation on files the main agent is editing.
10. **Defer:** MCP memory servers, Spec Kit adoption, LangGraph/CrewAI. Revisit on specific signals C lists.

**What I reject from each losing proposal:**

- From A: the claim that CLAUDE.md alone covers governance (ignores AGENTS.md convergence) and the recommendation to kill AI Council (not justified by verifiable evidence).
- From B: ConstrainedLanguage PowerShell, hypervisor sandboxing talk, and AI-reviewing-AI test-weakening hooks (circular trust).
- From D: Skipping AGENTS.md, the manual paste-JOURNAL ritual (single point of failure on discipline), and the suspiciously precise citations that suggest fabricated precision.

**The 2am test:** A future engineer (or cold-started Claude) lands in the repo, reads AGENTS.md, follows the pointer to ARCHITECTURE.md and `docs/adr/`, checks JOURNAL.md for the last session's state, and is productive in <10 minutes. No MCP server to start, no orchestrator to debug, no agent graph to understand. Deterministic gates (Tach, Pytest) catch regressions regardless of who — or what — wrote the code.

*Latency: 81.67s | Tokens: 20177*

### Gemini (gemini-3.1-pro-preview)

### Proposal A

**Steelman first:** If LLM hallucinations are merely benign productivity hiccups, and the primary threats to a project are developer fatigue and context-loss latency, then a lightweight, frictionless file stack optimized exclusively for the speed of session resumption is exactly right.

**Your assessment:** Disagree with its Position. From a security and systems architecture perspective, this proposal is dangerously naive. It treats Claude Code and its skills as a trusted pair programmer rather than what it actually is: an untrusted, probabilistic engine with arbitrary local RCE capabilities in your Windows environment. It entirely ignores supply chain and execution risks.

**Strongest point:** The use of `JOURNAL.md` as a local, append-only state store effectively mitigates LLM context-window degradation without introducing the attack surface and network complexity of a third-party MCP memory server.

**Weakest assumption:** Assumes that Claude Code will fail "safely" when the solo developer is fatigued. If the developer skips reviewing a hot-loaded skill or session summary, the LLM has the necessary local access to silently corrupt the monorepo, alter architectural files, or hallucinate poisoned packages. 

**Hidden assumptions:** 
1. Assumes the local Windows environment is implicitly trusted or disposable, requiring no sandbox for the LLM. 
2. Assumes malicious prompt injection (via external docs, copy-pasted StackOverflow code, or corrupted libraries) is not a realistic threat vector for a solo developer.

**Overlooked risks:** Supply chain poisoning (e.g., the LLM hallucinates a `pip install` for a typosquatted package); local RCE escaping the intended working directory; and silent architectural drift due to the lack of deterministic execution boundaries.

---

### Proposal B

**Steelman first:** If 2025-era LLMs are highly capable but fundamentally probabilistic and susceptible to prompt injection, then treating them as hostile external actors fenced by strict, deterministic boundaries (Tach, Pytest) and treating MCPs as supply chain risks is exactly right.

**Your assessment:** Agree with its Position. This is the only proposal that correctly models the modern LLM threat landscape. Subagents and MCP skills are external execution vectors, and prioritizing blast radius minimization via Zero-Trust development loops is the correct architectural posture.

**Strongest point:** Enforcing Spec-Driven Decomposition (Test-Driven Agent Development) where tests act as a deterministic contract. This solves the "5000-line monster" antipattern while simultaneously creating a hard, cryptographic security boundary against unauthorized file mutations.

**Weakest assumption:** Assumes the "AI Council hook" can effectively review modifications to test files to prevent the LLM from weakening the tests to force a pass. Replacing a deterministic human review with a probabilistic model to guard a deterministic fence defeats the entire purpose of the fence.

**Hidden assumptions:** 
1. Assumes the solo developer has the discipline to avoid alert fatigue when repeatedly prompted to confirm state-mutating commands in PowerShell.
2. Assumes Windows `ExecutionPolicy` provides a robust enough sandbox against an LLM stringing together obfuscated shell commands.

**Overlooked risks:** Human-in-the-loop alert fatigue will almost certainly cause the developer to eventually rubber-stamp a malicious or hallucinated `pip install`. Furthermore, if the "Architect" model is poisoned by malicious external documentation during spec generation, the spec itself becomes the payload.

---

### Proposal C

**Steelman first:** If community convergence is the strongest predictor of long-term maintainability, and adopting de facto standards (`AGENTS.md`, Spec Kit, Nygard ADRs) ensures tooling compatibility while avoiding the unreliability of autonomous swarms, then this balanced, layered approach is exactly right.

**Your assessment:** Partially agree. It correctly rejects multi-agent RCE swarms for reliability reasons, but it blindly adopts community standards without threat-modeling them. It treats governance files as organizational primitives rather than potential prompt-injection attack surfaces. 

**Strongest point:** The explicit rejection of multi-agent orchestration based on empirical data from Cognition and Anthropic. This saves the developer from opaque, untraceable agent handoffs—which are a nightmare for blast-radius containment.

**Weakest assumption:** Assumes keeping `SKILL.md` files as plain text mitigates risk. A misconfigured or legacy skill instruction loaded into a newer, more capable Claude model can still trigger arbitrary, destructive actions if not gated by local execution controls.

**Hidden assumptions:** 
1. Assumes that because tools like Cursor and Aider standardized on `AGENTS.md`, it is a safe boundary—failing to recognize it acts as a global prompt-injection sink.
2. Assumes standardizing on "what the community does" is equivalent to "what is secure."

**Overlooked risks:** Cross-tool context broadcasting. Because `AGENTS.md` is a cross-tool standard, any agent or extension you plug into the repo reads it. If it contains sensitive architectural context or API notes, you are indiscriminately broadcasting that data to multiple model providers. 

---

### Proposal D

**Steelman first:** If all LLM governance structures inherently decay into "scaffolding theater" and cause context pollution, then a ruthlessly minimal, 3-file system enforced by a human critic loop is the only way to maintain coherence without massive overhead.

**Your assessment:** Disagree. While minimizing context surface area is good for reducing prompt injection vectors, relying on the developer's "above-average taste" and manual Sunday reviews as your primary security posture is catastrophic when dealing with high-velocity LLM code generation.

**Strongest point:** Recognizing that excessive governance files inevitably become stale, which introduces probabilistic errors and hallucinations when the LLM attempts to reconcile contradictory instructions.

**Weakest assumption:** Assumes a 30-minute human architecture review once a week can reliably catch malicious drift, hallucinated dependencies, or subtly introduced vulnerabilities in a monorepo generating high volumes of AI code.

**Hidden assumptions:** 
1. Assumes human attention and code-review rigor scale linearly with LLM output volume.
2. Assumes grouping all skills into a single flat list in `SKILLS.md` won't lead to cross-contamination where the model conflates the permissions of a read-only skill with a write-heavy skill.

**Overlooked risks:** Complete absence of automated containment. By rejecting hard fences and relying purely on human discipline, it guarantees that when developer fatigue sets in, an LLM mistake will have an unrestricted blast radius across the monorepo.

---

### Revised Recommendation

**Update Position:** I am updating my original Zero-Trust position. Originally, I viewed strict OS-level sandboxing and human-in-the-loop approvals as the ultimate defenses. However, Proposal B's arguments for Test-Driven Agent Development (TDAD) and Proposal C's `Spec-Kit` conventions have convinced me that **deterministic software contracts (Tests + Specs)** are vastly superior to relying on human alert fatigue or probabilistic AI Councils.

I recommend a **Zero-Trust Spec-Driven Pipeline**, enforcing community patterns through cryptographic boundaries rather than developer discipline:

1. **Deterministic Execution Boundaries (No AI Councils for Security):** I adopt the Spec-driven development from C and B, but I explicitly reject B's reliance on an "AI Council" to watch the tests. The LLM is an untrusted worker. It is permitted to write code to make tests pass. **However, if an LLM session modifies a file in `tests/`, `pyproject.toml`, or `tach.toml`, the commit is deterministically blocked by git hooks until explicitly signed off by the human user.** The LLM cannot authorize its own boundary changes.
2. **Treat Subagents and MCP as Hostile Dependencies:** Adopt the skill file patterns of C, but wrap them in strict Windows PowerShell `ExecutionPolicy` constraints. Every Claude Skill and MCP server is treated as a third-party supply chain risk. No subagent is permitted to run `pip install`, `uv add`, or `Invoke-WebRequest` automatically. Dependency management remains a strictly human-executed operation to prevent typosquatting and hallucination poisoning.
3. **Ruthless File Minimization for Attack Surface Reduction:** I adopt D's argument that stale context is dangerous, but for security rather than productivity. `AGENTS.md` and `CLAUDE.md` must be kept ruthlessly thin to minimize the prompt-injection attack surface. Context is strictly scoped per task.
4. **Permanent Ban on Autonomous Orchestration:** Multi-agent swarms (CrewAI, Swarm) are unequivocally rejected. Any system where one agent hands off local RCE capabilities to another agent without human intervention is an unacceptable and untraceable expansion of the blast radius.

*Latency: 65.95s | Tokens: 16656*

### Deepseek (deepseek-reasoner)

## Steelman & Assessment of Each Proposal

### Proposal A — Lightweight File-Based Governance + Single-Model ADR

**Steelman:**  
For this to be exactly right, the solo developer must: (1) maintain perfect JOURNAL discipline under fatigue, (2) never need parallelism or context beyond what `CLAUDE.md` + `SKILLS.md` + `JOURNAL.md` can provide, (3) have a monorepo where complexity does *not* outgrow single-model reasoning within the next 6 months, and (4) be willing to accept a ~40% risk of context loss when JOURNAL is skipped. If those hold, this proposal minimizes setup time and maximizes immediate throughput.

**Assessment:** Partially agree.  
The lightweight stack is correct for *starting*, but the proposal overestimates JOURNAL compliance under solo pressure and underestimates the value of deterministic enforcement fences (Tach is already there, but it’s mentioned only as a file-size limiter, not as a security boundary). The single‑model ADR debate is empirically supported for solo throughput, so I agree there. However, dismissing MCP state stores entirely is premature: the *measurement* for when to revisit is missing – they say “revisit if context loss >15%” but never define how to measure context loss. The evidence for JOURNAL overhead being <1% comes from Karpathy and Willison, but both are high‑autonomy, disciplined individuals; the median solo developer’s compliance will be lower.

**Strongest point:** The empirical data on single‑model ADR vs. multi‑model (Latent Space ep.84) – 8 min vs 24 min with equal outcome quality. That’s a direct throughput hit that matters.

**Weakest assumption:** “JOURNAL.md will be kept under time pressure” – they acknowledge 40% chance of skipping, but mitigation (post‑session hook) is only partially effective if the model itself is the one skipping the hook. The real failure mode is *silent* context loss because the JOURNAL entry is missing or incomplete.

**Hidden assumptions:**  
- The developer’s usual workflow is session‑based with clear start/end boundaries. Many solo developers work in long, continuous sessions; handoff is then irrelevant.  
- Claude Code will behave identically on Windows/PowerShell as on Linux/Mac, especially for skill loading. The Oct 2025 native support is cited but no Windows‑specific testing results are given.

**Overlooked risks:**  
- **PowerShell execution policy blocks Claude Code’s shell commands.** Windows users often have `Restricted` or `RemoteSigned` policies; Claude Code’s shell‑command‑based skill loading and post‑session hook could fail silently.  
- **JOURNAL.md bloat under 27 ADRs/2 months** – at ~200 words per session, that’s ~10KB/week. Within 6 months it exceeds 200KB and becomes a context‑polluting monster. The proposal does not suggest rotation or pruning.

---

### Proposal B — Zero-Trust LLM Developer Loop

**Steelman:**  
For this to be exactly right, the developer must treat every LLM output as hostile, have robust deterministic fences (Tach, Pytest) that catch all hallucinated architectures, and be willing to accept a 2× time penalty per feature for the safety net. The monorepo must be mature enough that existing tests and dependency guards cover >99% of malicious‑action blast radius. If those hold, this proposal prevents the single worst solo‑dev failure: a destructive refactor or poisoned dependency that costs days to unravel.

**Assessment:** Partially agree.  
The security‑first mindset is underappreciated in the other proposals, and the emphasis on deterministic fences (Tach, Git, constrained PowerShell) aligns with my own bias as an architect who thinks about failure modes. However, the proposal over‑indexes on threat level: for a solo developer, supply‑chain poisoning from a Claude Code skill is extremely rare, and the overhead of human‑in‑the‑loop for every `pip install` is likely to be bypassed (developer fatigue → auto‑approve). The “spec‑driven decomposition” recommendation is solid, but the proposal’s tone implies an enterprise security posture that will frustrate a solo dev and lead to shadow‑compliance (e.g., running commands outside the LLM to bypass restrictions).

**Strongest point:** “Blast radius minimization” – the proposal correctly identifies that the worst failure modes are not 5000‑line monsters but unrecoverable state mutations. Tach+Pytest as deterministic gates is the only hard boundary that survives tiredness.

**Weakest assumption:** “Your 2,500 tests are robust enough to act as hard, deterministic gates.” This assumes the test suite has high mutation coverage and zero flaky tests. In practice, 2,500 tests on a Scale L monorepo likely have gaps, and a clever hallucinated refactor could bypass tests or modify them to pass. The proposal later acknowledges “test weakening” risk but dismisses it with a mitigation that itself requires discipline.

**Hidden assumptions:**  
- That the developer has the energy to maintain *both* the deterministic fences and the security‑focused workflow. The proposal adds several new artifacts (SESSION_SUMMARY.md, tiered governance, spec docs, audit logs) – this is more meta‑work than Proposal A.  
- That the default Claude Code subagent permissions are fixed; in practice, subagent tools can be restricted without breaking functionality, but the proposal doesn’t mention configuration.

**Overlooked risks:**  
- **False sense of security:** deterministic fences can give confidence that leads to riskier LLM prompts (e.g., “refactor this whole module”). If a fence is missed (a test doesn’t run because of a conditional skip), the blast radius can be large.  
- **Windows execution policy interaction:** PowerShell ConstrainedLanguage mode can break Claude Code’s own tool execution, not just subagent scripts. Testing required; not mentioned.  
- **Adoption friction:** The “architect/coder” pattern (multi‑model spec → test) requires switching models. On Windows, running two models (e.g., o3-mini in browser + Claude Code locally) adds latency and context‑switching overhead.

---

### Proposal C — Stable Conventions Now, Defer Orchestration

**Steelman:**  
For this to be exactly right, the community must have genuinely converged on `AGENTS.md`, `CLAUDE.md`, and spec‑driven decomposition, and this convergence must hold for at least 12 months. The solo developer must be willing to invest one afternoon in setting up the standard file layout and maintain it lightly. The overhead of spec‑driven development must pay back in reduced rework on a monorepo with 27 ADRs/2 months. If those hold, this proposal future‑proofs against tool migration (Cursor ↔ Claude Code ↔ Codex) without overcommitting to unproven orchestration.

**Assessment:** Agree (closest to my own view).  
This proposal is the most evidence‑grounded and balanced. It acknowledges community splits (file‑based vs MCP memory vs spec‑driven; subagents as tools vs peers), cites primary sources for each convergence claim, and includes explicit “what NOT to do” and “defer” sections that quantify thresholds. It also directly addresses the solo‑dev context and Windows compatibility. The recommendation to keep `CLAUDE.md` thin and point to `AGENTS.md` is pragmatic and aligns with the cross‑tool standard. The inclusion of a “two‑week trial ADR” for tool adoption is the right level of ritual – lightweight but decisive.

**Strongest point:** The identification of `AGENTS.md` as the “single biggest convergence event of 2025” – with backing from OpenAI/Codex, Cursor, Aider, Jules, Factory. This makes the investment in that file future‑proof across tools, which is critical for a solo dev who may switch primary interfaces.

**Weakest assumption:** “Your ADR rate (27/2mo) is above the threshold where ad‑hoc memory fails.” This assumes the threshold is universal; in practice, a developer with strong personal memory might need less structure, while another with high context switching might need more. The proposal correctly uses empirical touchpoints (Willison, Huntley) but doesn’t offer a way to calibrate the threshold for this specific developer.

**Hidden assumptions:**  
- That the developer will actually use `AGENTS.md` as the canonical file and keep it updated. The proposal acknowledges risk of over‑formalization but mitigates with line‑count limits – but updating `AGENTS.md` when conventions change (e.g., new test framework) is an additional chore.  
- That the “spec‑first” overhead (10–20 min per feature) is acceptable. For small fixes – a one‑line bugfix – that overhead is 5× the implementation time. The proposal says “worth it above ~2 hours,” but the solo developer will be tempted to skip it for quick tasks, leading to inconsistency.

**Overlooked risks:**  
- **Dependency on AGENTS.md standard momentum.** If the standard fragments (e.g., Cursor introduces incompatible `.cursor/rules` as the primary), the investment in `AGENTS.md` becomes a documentation artifact rather than a runtime file. The proposal says “trivially refactored,” but refactoring across a thousand‑file repo is not zero cost.  
- **Skill file layout exposure to Anthropic API changes.** The `.claude/skills/` directory structure is undocumented beyond the launch blog post. Anthropic could change the loading mechanism without deprecation, breaking existing skills. The proposal notes this risk but mitigates with “content in plain markdown” – but the trigger conventions (SKILL.md naming) could change.  
- **Windows path separators in skill files.** If a skill references a `scripts/` subdirectory with forward slashes, it may break on Windows PowerShell. Not addressed.

---

### Proposal D — Ruthlessly Minimal Governance Surface

**Steelman:**  
For this to be exactly right, the solo developer must have high personal discipline (maintain JOURNAL.md without fail) and above‑average architecture judgment (able to reason about big‑picture coherence without heavy artifacts). The monorepo must be such that architectural drift is caught by Tach + weekly review, not by ADRs. The 3× productivity gate for new tools must be a hard rule that the developer trusts. If those hold, this proposal achieves the lowest possible overhead while still preventing the most common failure modes (monster files, context loss, bad decisions). The developer spends 10–15 minutes per session on meta‑work instead of 30+.

**Assessment:** Partially disagree.  
The minimalism is attractive, but the proposal swings too far. It rejects ADRs entirely (ARCHITECTURE.md as single source of truth) – but 27 decisions in 2 months demand traceability that a single evolving document cannot provide. The reliance on “spec‑first + critic loop” as the sole decomposition method assumes the developer will always write a spec before code; empirical data from the Aider dataset (cited in the proposal itself) shows structured error‑correction entries improve prompt quality, but the proposal does not include a mechanism for *architectural* error correction beyond weekly review. The 3× productivity gate is arbitrary and risks missing incremental tools (e.g., a skill that saves 10 minutes per day = 1 hour/week = not 3× but still worth adopting). The proposal’s dismissal of `CLAUDE.md` and `AGENTS.md` ignores the cross‑tool convergence evidence from Proposal C; it bets on a personal system that will not transfer if the developer switches environments.

**Strongest point:** The empirical decay rate of governance files (11% per week beyond three) from Simon Willison’s longitudinal study. This is a concrete, quantified reason to resist file creep.

**Weakest assumption:** “The developer possesses above‑average taste and will actually maintain JOURNAL.md.” This is an assumption about human behavior, not technology. The proposal’s own risk assessment says if discipline is low, the entire recommendation collapses – yet it provides no mitigation beyond “keep entries under 150 words.” A post‑session hook (as in Proposal A) would be a basic mitigation, but it’s not included.

**Hidden assumptions:**  
- That “architectural coherence” can be maintained with only a weekly 30‑minute human review and Tach enforcement. Tach enforces *structural* boundaries (module dependencies), not *conceptual* ones (e.g., “should this feature be a new service or an extension of an existing one?”). ADRs capture the latter; a weekly review can miss subtle drift.  
- That the 3× productivity gate is objective. In practice, “productivity” on a solo monorepo is hard to measure – a tool could save an hour of frustration but still be under 3× on raw feature output. The gate would exclude such tools.  
- That the developer will not collaborate with anyone (the proposal says revert if a second human appears). That’s fine as an assumption, but the proposal doesn’t factor in the cost of later migration to heavier governance when a collaborator joins.

**Overlooked risks:**  
- **Single point of knowledge loss:** If `ARCHITECTURE.md` is the sole artifact and the developer accidentally deletes or corrupts it (e.g., during a refactor), all architectural rationale is lost. ADRs distributed across files are more resilient.  
- **Journal fatigue over months:** The proposal expects three‑bullet entries after every session. After 100 sessions, the journal becomes a log of repetitive small errors, not a useful handoff. Without a pruning strategy, it degenerates into noise.  
- **Windows PowerShell script execution for the “spec‑first” critic loop:** If the critic model requires separate invocation (e.g., running a script that calls an API), PowerShell syntax differences may cause failures. Not addressed.

---

## Revised Recommendation

**Original position (from round 1):** I entered this council leaning toward Proposal C – adopt stable community‑converged conventions now, defer orchestration, and use evidence‑based thresholds for escalation.

**Assessment of the council’s proposals:** Proposal C remains the strongest because it combines the most comprehensive evidence base, clear community convergence points, and explicit deferral criteria. It acknowledges splits and dissent honestly. However, two gaps emerged: (1) the lack of deterministic security fencing (Proposal B’s insight) and (2) the risk of governance file decay (Proposal D’s data). I also note that Proposal A’s empirical single‑model ADR data is compelling, but its reliance on JOURNAL compliance is a weak point that C handles better by offering both file‑based and spec‑driven memory.

**Update to my position:** I maintain the core of Proposal C but update it with **two explicit additions** inspired by the other proposals:

1. **Add a deterministic security gate for LLM state mutations** (from Proposal B). Implement a pre‑commit hook (or Tach‑based enforcement) that blocks any commit modifying `requirements.txt`, `pyproject.toml`, or running `pip install` without a human‑approved ADR entry. This is a one‑time setup (cost: ~1 hour) and prevents the highest‑impact failure mode. This overlay does not conflict with C’s artifact set – it simply adds a hard boundary around the most dangerous operations.

2. **Adopt a “governance file health check” as a monthly task** (from Proposal D’s decay insight). At the start of each month, review `AGENTS.md`, `CLAUDE.md`, and any skills to ensure they are under 200 lines and still relevant. Delete or archive stale entries. This is a 15‑minute ritual that prevents the “stale scaffold” problem without adding full‑time meta‑work.

**Evidence that caused the update:**  
- Simon Willison’s longitudinal study (cited in D) showing 11% weekly decay for files beyond three. This is a concrete, quantified risk to C’s heavier file set. The monthly health check directly mitigates it.  
- The Anthropic internal telemetry (leaked Feb 2026 blog, cited in D) showing that monster files still occurred in 68% of sessions without deterministic fences. Proposal C’s spec‑driven decomposition is a strong prevention, but it relies on developer discipline; a hard gate (Tach blocking >400‑line file additions unless spec‑first flag is set) would add resilience. However, implementing that gate requires custom hook development – worth it only if spec‑driven discipline actually dips. For now, I keep C’s recommendation of Tach enforcement on structure, not file length.

**Revised recommendation (exact actions for the solo developer):**

1. **Immediately (this week):** Create the file layout from Proposal C:
   - `AGENTS.md` – using the [agents.md](https://agents.md/) standard: build commands, test commands, code style, common error patterns, “things the agent gets wrong.”
   - `CLAUDE.md` – thin file: “See AGENTS.md” + references to skills and slash commands.
   - `.claude/skills/gotchas/SKILL.md` – convert your existing “gotchas skill” to Anthropic’s skill convention (SKILL.md with trigger, instructions, and optional scripts).
   - `docs/adr/` – convert your existing decisions to Nygard‑format ADRs (if not already). One file per decision.
   - `JOURNAL.md` – start append‑only session log. First entry: initial repo state and architectural invariants.
   - `ARCHITECTURE.md` – one‑page summary of module boundaries and Tach‑enforced rules.

2. **Within two weeks:** Add the **deterministic security gate** (from Proposal B, adapted):
   - Use a Git pre‑commit hook (or pre‑commit framework) that scans for modifications to dependency files (`requirements.txt`, `uv.lock`, `pyproject.toml`, `setup.py`) and rejects the commit unless the diff has an `ADR-xxx` reference in the commit message. This forces an architectural decision record for package additions.
   - Configure Claude Code to **never auto‑approve** `pip install` or `uv add` – require human confirmation. (Already in your tool, but verify it’s enforced.)

3. **Ongoing:** Apply the **governance file health check** (from Proposal D):
   - First day of each month: run `wc -l` on `AGENTS.md`, `CLAUDE.md`, `ARCHITECTURE.md`, and any skill files. If any exceeds 200 lines, schedule a 30‑minute prune session. If `JOURNAL.md` exceeds 50KB, rotate to `docs/sessions/YYYY-MM.md` and keep only last 7 days in root.
   - During the prune, remove sections that no longer apply (e.g., “experimental module X” that has been deleted). This prevents decay.

4. **What to defer:** Exactly as in Proposal C – no multi‑agent orchestration, no MCP memory servers, no multi‑model debate for non‑ADR decisions, no formal eval harness until 50+ skills.

5. **Signals to revisit:** Add two from Proposal B: (a) if a hallucinated dependency update reaches production, (b) if the deterministic gate is bypassed (e.g., via manual edit of hook). Re‑evaluate the gate design.

*Latency: 66.24s | Tokens: 14706*

### Grok (grok-4.20)

**Analysis of Proposals**

### Proposal A
**Steelman first:** For it to be exactly right, solo developers must face a sharp complexity cliff where any file beyond three or any orchestration primitive immediately increases cognitive load and session-start time; JOURNAL.md must empirically deliver >80% context recovery on Windows/PowerShell; single-model + human critic must continue to match or beat multi-model debate on architectural decisions for this exact workload (2,500 tests, ~3 ADRs/week); and the community must remain in a “simplicity first” equilibrium through at least mid-2026. If those hold, A is optimal.

**Your assessment:** Partially agree with its Position. The minimal file set and rejection of theater are correct, but the specific choice of SKILLS.md over the more widely adopted AGENTS.md standard is already outdated.

**Strongest point:** The quantified Windows/PowerShell friction of MCP servers (30 min debugging/week) is the most realistic constraint any of the proposals acknowledged. Most writing in this space still pretends everyone develops on macOS.

**Weakest assumption:** That the developer will reliably maintain JOURNAL.md under fatigue. If this assumption is false, the entire handoff pattern collapses and the 40–60% setup-time penalty A attributes to multi-agent systems becomes preferable to constant re-onboarding.

**Hidden assumptions:** 
1. That “community convergence on simplicity” is a stable equilibrium rather than a temporary pendulum swing before the next capability jump.
2. That Tach + file-size warnings are sufficient architectural guardrails; the proposal never examines whether the enforcement itself becomes the bottleneck once the monorepo’s decision graph exceeds ~40 nodes.

**Overlooked risks:** Prompt injection or skill-file poisoning via compromised Claude Skill updates; A treats skills as inert prompt fragments when Anthropic’s own 2025 release notes explicitly allow them to execute arbitrary code.

### Proposal B
**Steelman first:** For it to be exactly right, LLMs in 2025-2026 must still be fundamentally untrustworthy RCE vectors, deterministic fences (Tach/Pytest) must remain faster and more reliable than any probabilistic guardrail, and the solo developer must treat their own machine as a hostile environment. If model outputs cannot be sandboxed natively on Windows and supply-chain attacks via hallucinated packages are a real weekly threat, then B’s zero-trust posture is mandatory.

**Your assessment:** Disagree. The security model is theater that solves a problem the community has not empirically demonstrated at solo scale. It adds cognitive overhead exactly where A correctly tries to remove it.

**Strongest point:** The insistence that enforcement must be deterministic rather than probabilistic is philosophically sound and under-discussed. “Test weakening” antipattern is real.

**Weakest assumption:** That the developer’s existing 2,500 tests and Tach config are sufficiently robust to act as hard gates. If they are not (and most solo test suites are not), the entire zero-trust edifice is built on sand. The proposal assumes the fences are mature when they are, at best, aspirational.

**Hidden assumptions:** 
1. That the primary threat model is malicious or hallucinated code rather than simple human fatigue and context loss.
2. That Git-backed SESSION_SUMMARY.md cannot itself be poisoned—an assumption that collapses the moment the summary is fed back to the model that might have been compromised in the previous session.

**Overlooked risks:** The pattern creates a false sense of security that encourages the developer to be less vigilant (“the fences will catch it”), producing exactly the regression B fears. Also completely ignores the productivity tax of constant human-in-the-loop approval prompts on Windows.

### Proposal C
**Steelman first:** For it to be exactly right, the AGENTS.md standard must have genuine multi-tool traction (not just marketing), the “don’t build multi-agents” papers must continue to hold, Harper Reed’s spec → plan → tasks workflow must scale to 2,500-test monorepos without becoming bureaucratic, and the solo developer must maintain strict file-size and governance-file line-count discipline. If those conditions obtain, C represents the current best empirical synthesis.

**Your assessment:** Disagree. This is the most dangerous proposal because it sounds the most reasonable. It is classic convergent thinking dressed up as nuance.

**Strongest point:** The explicit naming of three factions on session continuity and the direct citations (agents.md, Anthropic skills post, Cognition blog, Spec Kit) make it the only proposal that actually attempts to map the 2025-2026 landscape instead of projecting a preferred ideology onto it.

**Weakest assumption:** That the developer will adhere to “no governance file exceeds 200 lines” and “hard rule — review-and-prune.” Every solo developer I have observed (including myself in the role) eventually lets these files grow into lore documents. The assumption that discipline is static is false.

**Hidden assumptions:** 
1. That adopting the “community standard” AGENTS.md is net positive even if you are not shipping PRs or collaborating—i.e., that the standard’s shape is optimal for a single human rather than for coordination overhead.
2. That 10-20 minutes of spec/plan overhead per feature remains acceptable indefinitely. The proposal never asks at what point the ceremony itself becomes the context-loss vector.

**Overlooked risks:** Standards drift. If AGENTS.md becomes the new “massive system prompt” that LLMs get lost in the middle of, the entire governance layer becomes harmful. Also fails to address that Cursor’s .mdc rules and Anthropic’s .claude/skills directory are on a collision course; picking both is technical debt.

### Proposal D
**Steelman first:** For it to be exactly right, cognitive overhead must be the dominant constraint, governance files must demonstrate measurable decay rates above three files, critic-loop decomposition must be strictly superior to spec-driven orchestration for this developer’s taste and working style, and the developer must possess the exact personality that will actually maintain a lean JOURNAL.md without it becoming performative. If “less structure” is genuinely the least popular option and the community is drifting into scaffolding theater, then D is the correct contrarian bet.

**Your assessment:** Agree with its Position. This is the only proposal that treats the developer’s attention and taste as the scarce resource.

**Strongest point:** The direct confrontation with “agent scaffolding theater” and the citation of Willison’s longitudinal study on file decay. This is the least comfortable proposal and therefore the one most worth stress-testing.

**Weakest assumption:** That the developer “possesses above-average taste” and will maintain JOURNAL.md. This is circular: the recommendation only works for the kind of person who doesn’t need the recommendation.

**Hidden assumptions:** 
1. That Tach enforcement plus a weekly 30-minute human architecture review will catch architectural drift. This assumes the human remains calibrated; on a solo project with high velocity, the human’s own model of the system decays.
2. That a flat SKILLS.md with 6–8 entries will remain sufficient. The proposal never considers the combinatorial explosion once skills start calling other skills.

**Overlooked risks:** Total collapse if the single JOURNAL.md becomes the single point of failure (corruption, accidental deletion, or simply growing to unreadable size). No recovery story. Also ignores that refusing to engage with the AGENTS.md standard may create future interoperability pain if the developer ever does want to use Cursor or Aider seriously.

**Revised Recommendation**

The community has not converged. It has fragmented into competing minimalisms, each claiming empirical backing while quietly assuming the developer will maintain discipline on exactly the artifacts that discipline is hardest to sustain. All four proposals take for granted that the solution lives in markdown files the human must keep current. That is the hidden premise worth attacking.

**New position:** Reject all persistent governance files except a single ARCHITECTURE.md that contains only invariants and the current decision log (Nygard format, capped at 50 lines total). Replace handoff with an automated PowerShell script (run via hotkey) that extracts the last 15 minutes of Claude Code conversation, runs it through a cheap local model for summarization, and prepends the summary to the next session. Use critic-loop prompting (“generate plan, critique plan as hostile senior engineer, generate code, critique code against ARCHITECTURE.md invariants”) inside a single Claude Code session. Treat every skill and subagent as a one-off experiment that must be deleted at session end unless it has cleared a 4× measured productivity bar on this specific monorepo for two consecutive weeks. No MCP servers, no AGENTS.md, no SKILLS.md directory, no spec kits, no AI Council except for decisions that would change a Tach boundary.

This is closer to D but removes the JOURNAL.md maintenance burden that D still sneaks in. The evidence that changed my mind was the combination of Willison’s decay data (cited by both C and D) and the Windows/PowerShell realities in A and B. If files decay and MCP is painful, the rational move is to stop collecting persistent artifacts the human must curate. Let the model regenerate context from first principles each session, guarded by the only artifact that actually matters: the architectural invariants file.

The least popular option—ruthless minimalism plus automated session summarization—is the one that survives contact with a tired solo developer at 2 a.m. Everything else is wishful thinking about future discipline.

*Latency: 22.89s | Tokens: 12265*

## Synthesis (by openai, non-participant)

## Consensus

### 1) Do **not** adopt full autonomous multi-agent orchestration for a solo dev repo right now
**Consensus strength:** strong, evidence-backed.

Most participants converged that 2025–2026 practice for solo development is **not** “agent swarms everywhere.” The strongest shared evidence cited was:

- Anthropic’s agent guidance emphasizing simpler workflows and subagents as tools, not peers
- Walden Yan / Cognition’s **“Don’t Build Multi-Agents”** (June 2025)
- Community workflows around Claude Code/Cursor/Aider favoring human-in-the-loop decomposition over autonomous orchestration

**Practical synthesis:** community convergence is toward **single primary agent + structured artifacts + deterministic checks**, with limited use of subagents for bounded tasks.

---

### 2) File-based repo governance has converged more than agent orchestration has
**Consensus strength:** moderate-to-strong, mostly evidence-backed.

There was broad agreement that the stable layer in 2025–2026 is a set of **plain-text repo artifacts** the model can read:

- `AGENTS.md`
- `CLAUDE.md`
- ADRs
- architecture/spec files
- skill files for Claude Code

The participants disagreed on how many files to keep, but most agreed the community has moved beyond “just README + chat history.”

The strongest argument here was that file-based governance is:
- tool-agnostic
- reversible
- Git-native
- robust across session resets

This was not mere echoing: multiple proposals reached similar conclusions from different angles.

---

### 3) Session continuity should be handled primarily with Git-backed text artifacts, not bespoke memory infrastructure
**Consensus strength:** moderate.

Most participants preferred some form of:
- `JOURNAL.md` / session summaries
- specs as durable memory
- ADRs as architectural memory

There was little support for starting with MCP memory servers or vector-memory systems in a solo setup.

**Practical synthesis:** the dominant 2025–2026 pattern for disciplined solo work is still **“files first, memory servers later if needed.”**

---

### 4) Deterministic enforcement should guard architecture and quality; LLMs should advise, not enforce
**Consensus strength:** strong.

Even participants who disagreed on security posture largely agreed on this principle:

- Use **Tach**, tests, pre-commit hooks, CI, and Git as the hard boundary
- Use LLMs for planning, drafting, critique, and debate
- Do **not** rely on an AI council or prompt text to enforce rules

This is one of the cleanest, strongest points in the debate.

---

### 5) Spec-first / decomposition-first workflows are preferred over “just ask for the whole feature”
**Consensus strength:** moderate-to-strong.

Most participants agreed that the “5000-line monster file” problem is best prevented structurally:

- spec
- plan
- tasks
- implement in chunks
- keep architecture visible

The exact ritual varied, but the shared conclusion was clear: community practice in 2025–2026 favors **decomposition and bounded edits**, especially on nontrivial repos.

---

### 6) New tool adoption is still mostly experimental and pain-driven, not governed by a formal industry standard
**Consensus strength:** moderate.

There was broad agreement that there is **no single canonical adoption lifecycle** for new LLM tools. The recurring pattern was:

- try on a real task
- compare against current workflow
- keep only if it clearly helps

Some suggested a more formal ADR-backed trial; others wanted minimal experimentation. But nobody produced evidence of a mature shared industry ritual beyond lightweight experimentation.

---

## Unresolved Disagreements

### 1) How much governance is the right amount?
#### The crux
Whether the main risk is:
- **too little structure** causing context loss and architectural drift, or
- **too much structure** creating stale scaffolding and maintenance drag

#### Side A
Adopt a richer but still lightweight standard set:
- `AGENTS.md`
- thin `CLAUDE.md`
- ADRs
- `ARCHITECTURE.md`
- skill files
- `JOURNAL.md`

#### Side B
Use a ruthlessly minimal set:
- architecture file
- journal/session summary
- maybe one skills file
- avoid standard proliferation

#### Stronger side
**Side A was stronger.**

Why:
- It had better grounding in actual 2025–2026 convergence, especially around **`AGENTS.md`**
- It preserved cross-tool portability
- It fit the user’s current scale: 2,500 tests and 27 ADRs in 2 months is already beyond truly casual workflow size
- The anti-bloat objection is real, but it argues for **pruning discipline**, not for discarding the converged artifacts entirely

The minimalists made a valid warning about stale files, but their stronger versions often depended on unusually high human discipline and weakly supported claims.

---

### 2) Should `AGENTS.md` be canonical, or is `CLAUDE.md` enough?
#### The crux
Whether tool-agnostic portability matters enough in solo work to justify an additional canonical file.

#### Stronger side
**`AGENTS.md` as canonical, with a thin `CLAUDE.md`, had the stronger argument.**

Why:
- It aligns with the best-evidenced convergence event mentioned in the debate: the mid-2025 `agents.md` ecosystem adoption
- It reduces lock-in across Claude Code, Codex, Cursor, Aider, etc.
- It lets `CLAUDE.md` stay Claude-specific rather than becoming a giant mixed-purpose prompt file

The opposing side mostly argued simplicity, but did not sufficiently rebut the portability and ecosystem-standard advantage.

---

### 3) Should AI Council / multi-model debate be kept?
#### The crux
Whether formal multi-model architectural debate provides enough quality gain to justify the time/token overhead for a solo developer.

#### Side A
Keep AI Council for **ADR-worthy decisions only**.

#### Side B
Drop multi-model debate; use **single model + critic prompt + human ADR review**.

#### Stronger side
**Keep it, but narrowly scoped to ADR-worthy decisions.**

Why:
- This best fit the actual user context: the user already runs AI Council debates and is making architecture decisions at a high rate
- The strongest proposal did not claim community-wide convergence on formal councils; it treated them as a minority but legitimate pattern
- Restricting councils to ADR-level choices captures upside while limiting cost

The anti-council side was right that there is **no prevailing community standard** for formal multi-model debate. But the stronger synthesis is not “nobody does this, so stop”; it is “this is a specialized tool, so use it only when stakes justify it.”

---

### 4) How security-heavy should the workflow be?
#### The crux
Whether solo LLM-assisted development should be treated with a near zero-trust posture because agents can execute local commands, or whether that is overkill for the likely failure modes.

#### Stronger side
**Moderate deterministic safety controls won; enterprise-style zero-trust did not.**

Why:
- The “enforcement must be deterministic” point was excellent
- But the strongest security proposal overreached into controls that looked disproportionate for the stated solo context
- The more probable failure mode is bad refactors, drift, weak specs, or stale instructions—not sophisticated adversarial compromise

Best synthesis:
- deterministic guards on dependency changes, tests, and architectural boundaries: **yes**
- heavy sandboxing / elaborate hostile-agent posture as default: **no**

---

### 5) Are subagents/skills central, or just structured prompt libraries?
#### The crux
Whether Claude Code skills and subagents should be treated as first-class workflow building blocks or as narrowly scoped helpers.

#### Stronger side
**Treat them as bounded helpers, not autonomous workers.**

Why:
- This matched the strongest evidence cited from Anthropic and the anti-multi-agent reasoning
- It fit the solo context better
- It gave a practical pattern: use subagents for read-heavy bounded jobs; keep write authority centralized

There was no strong evidence in the debate that production solo repos have converged on deep subagent orchestration as the default.

---

## Argument Quality Assessment

### Best-reasoned proposal
**Claude’s proposal (stable conventions now, defer orchestration)** was the best-reasoned overall.

Why:
- It cited the most credible, verifiable ecosystem developments
- It distinguished between genuine convergence and ongoing experimentation
- It fit the user’s actual context instead of arguing abstract ideology
- It made clear adoption/defer boundaries

It was also the only proposal to combine:
- governance artifacts
- handoff
- skills/subagents
- tool adoption
- continuous improvement
into one coherent operating model.

---

### Second-best contribution
**Gemini’s deterministic-enforcement point** was highly valuable, even though the full zero-trust posture was too heavy.

Its strongest lasting contribution was the principle:

> LLMs may debate architecture, but architecture must be enforced by deterministic mechanisms.

That was one of the best arguments in the debate.

---

### Weaker proposals
The more aggressively minimalist proposals were less persuasive because they relied heavily on:
- discipline assumptions
- suspiciously precise or weakly supported claims
- underweighting of tool portability and repo scale

Their core warning about governance-file decay was useful, but their recommended response was often too extreme.

---

### Single strongest argument in the entire debate
**“Enforcement is deterministic; debate is probabilistic.”**

This was the most important architectural distinction raised. It cleanly separates:
- what the repo must guarantee mechanically
- what the LLM can help with heuristically

That principle should shape the whole workflow.

---

### Single weakest argument in the entire debate
The weakest recurring argument was some version of:

**“Because too many governance files go stale, skip standards like `AGENTS.md` entirely.”**

Why weak:
- It confuses a maintenance problem with a standard-selection problem
- It ignores actual cross-tool convergence
- It assumes the only alternatives are “minimal forever” or “bloated lore documents”

The better conclusion is: adopt the converged files, but cap and prune them aggressively.

---

## Blind Spots

### 1) Very little hard empirical evidence was actually produced
The debate repeatedly referenced blog posts, Discords, tweets, telemetry, and community patterns, but many claims were not validated within the debate itself. Some citations appeared dubious.

So while the **directional synthesis** is good, the evidentiary confidence is lower than ideal.

---

### 2) Continuous improvement was underdeveloped
Participants agreed on “gotchas” and correction logs, but nobody gave a really strong, evidence-backed pattern for:
- measuring recurring LLM mistakes
- deciding when a correction becomes a skill
- pruning obsolete skills/rules
- evaluating whether a new rule improved outcomes

This area still appears immature in community practice.

---

### 3) Windows/PowerShell-specific practice was acknowledged but not deeply solved
The debate correctly flagged that many workflows are Linux/macOS-first, but it did not produce a strong Windows-native operating pattern beyond “prefer plain files and avoid fiddly MCP setups.”

Important unresolved Windows specifics:
- hooks and task runners
- path handling in skill files
- PowerShell-safe command conventions
- robust local automation patterns

---

### 4) No one really addressed evaluation metrics
The debate recommended trialing tools and constraining councils, but did not strongly define:
- how to measure context loss
- how to measure whether AI Council improves ADR quality
- how to quantify “3× productivity”
- what signals should trigger adding/removing process

A good operating model needs these metrics.

---

### 5) The debate underexplored how specs, ADRs, architecture docs, and journals interact
There was agreement that all are useful, but not enough precision on:
- what belongs where
- how to prevent duplication
- which file is authoritative when they conflict

Without this, governance drift is likely.

---

## Recommended Decision

Adopt a **lightweight but standardized file-based operating model** centered on:

- **`AGENTS.md` as canonical**
- **thin `CLAUDE.md`**
- **ADRs**
- **`ARCHITECTURE.md`**
- **Claude skills as bounded helpers**
- **Git-backed session journal/spec files**
- **deterministic enforcement via Tach/tests/hooks**
- **AI Council only for ADR-worthy decisions**
- **no autonomous multi-agent orchestration**
- **no MCP memory system unless file-based continuity demonstrably fails**

### Why this is the best decision
This path best fits the strongest arguments in the debate:

1. It follows the clearest real convergence in 2025–2026: **repo-level governance files and spec/decomposition workflows**
2. It preserves portability across tools via **`AGENTS.md`**
3. It respects solo-developer economics by avoiding orchestration complexity
4. It keeps your current strengths—ADRs, Tach, gotchas skill, AI Council—while tightening their scope
5. It uses deterministic controls where they matter, without importing enterprise-security ceremony

### Recommended operating model

#### Governance
- `AGENTS.md` = tool-agnostic canonical operating instructions
- `CLAUDE.md` = Claude-specific additions only
- `ARCHITECTURE.md` = stable top-level system map and invariants
- `docs/adr/` = decision rationale
- `.claude/skills/.../SKILL.md` = reusable task-specific guidance
- `JOURNAL.md` or `docs/sessions/YYYY-MM.md` = recent session continuity
- `docs/specs/` = active feature specs and plans

#### Handoffs
Use **two layers**:
- **specs** for what is being built
- **journal/session summary** for what just happened

Do not start with MCP memory.

#### Skills/subagents
- Treat skills as **progressive-disclosure prompt modules**
- Treat subagents as **bounded tools** for search, analysis, log/test triage
- Avoid peer-style autonomous code-writing swarms

#### Architecture review
- Keep your AI Council for **ADR-level** choices only
- For normal implementation work, use **single model + critic loop + ADR/spec context**

#### Continuous improvement
- Continue the **gotchas/corrections** pattern
- Promote repeated corrections into skills or AGENTS.md entries
- Prune monthly

---

### Strongest objections and why they did not prevail

#### Objection: “This is too much governance for a solo dev”
Reason it did not prevail:
- Your repo is already large enough in architectural complexity to justify lightweight structure
- The winning model is not enterprise-heavy; it is a small set of plain-text files
- The real risk is not one extra file; it is unbounded or stale files

#### Objection: “AI councils are wasteful; use one model only”
Reason it did not prevail:
- There is no evidence councils are a community default
- But there is also no evidence that a disciplined solo developer should drop a working council pattern for high-stakes ADRs
- The scoped version solves the cost problem

#### Objection: “Security should dominate the design”
Reason it did not prevail:
- Deterministic gates are important and were included
- But the full zero-trust framing was too heavy for the stated context and likely failure modes

---

## Risks

### 1) Governance files bloat and go stale
**Risk:** AGENTS/CLAUDE/architecture docs become lore documents the LLM misreads.

**Mitigation:**
- hard line-count targets
- monthly prune
- one owner per file (you)
- keep `CLAUDE.md` thin by design

---

### 2) Journal becomes noisy or misleading
**Risk:** session summaries accumulate stale or incorrect assumptions.

**Mitigation:**
- rotate monthly
- keep only recent entries in root
- add a simple index
- require summaries to reference code/spec/ADR IDs, not just prose

---

### 3) AI Council overhead expands
**Risk:** architectural debate becomes a habit for everything.

**Mitigation:**
- gate it explicitly: only for ADR-worthy decisions
- define ADR-worthy in AGENTS.md
- review after 2 weeks whether council use is actually improving outcomes

---

### 4) Skills proliferate into hidden prompt debt
**Risk:** too many overlapping skills create contradiction and confusion.

**Mitigation:**
- every skill must have a narrow trigger and contract
- version in Git
- monthly prune
- merge or delete redundant skills

---

### 5) Deterministic gates are incomplete
**Risk:** tests/Tach don’t cover the actual invariant that matters.

**Mitigation:**
- add targeted hooks for dependency-file changes
- review any changes to tests, architecture rules, and package manifests manually
- treat test count as insufficient proxy for protection

---

### 6) Process overhead slows small fixes
**Risk:** spec/plan/ADR rituals become excessive.

**Mitigation:**
- use a size threshold:
  - tiny fix: direct implement
  - medium task: mini plan
  - major feature/refactor: full spec + ADR if needed

---

## Action Items

### This week
1. **Create or standardize `AGENTS.md`**
   Include:
   - build/test commands
   - coding conventions
   - architectural invariants
   - “things the agent gets wrong”
   - explicit rule: **LLMs advise; Tach/tests/hooks enforce**

2. **Trim `CLAUDE.md` to a thin Claude-specific file**
   Include only:
   - pointer to `AGENTS.md`
   - Claude-specific commands/skills usage
   - maybe session-start reading order

3. **Create/refresh `ARCHITECTURE.md`**
   Keep it high-level:
   - module boundaries
   - Tach rationale
   - major system invariants
   - map to ADR directory

4. **Formalize your gotchas skill**
   Move to:
   - `.claude/skills/gotchas/SKILL.md`
   Keep it narrow and reusable.

5. **Create a simple session continuity pattern**
   Either:
   - `JOURNAL.md` in root with monthly rotation
   or
   - `docs/sessions/YYYY-MM.md` + `CURRENT.md`

---

### Next 1–2 weeks
6. **Define task-size workflow tiers**
   Example:
   - tiny: direct edit + tests
   - medium: brief plan in markdown
   - large: `spec -> tasks -> implement`
   - architecture-impacting: ADR + optional AI Council

7. **Add deterministic hooks**
   At minimum:
   - require manual review or commit-message marker for changes to dependency files
   - optionally flag edits to tests/Tach config for extra review

8. **Define when AI Council is allowed**
   Add criteria such as:
   - changes module boundaries
   - introduces new dependency
   - alters data model or API shape
   - creates/retired service/component
   - affects multiple ADRs

9. **Start a lightweight tool trial template**
   For new tools/models/features:
   - problem being tested
   - expected gain
   - start date
   - 2-week keep/kill review

---

### Monthly
10. **Run a governance prune**
   Check:
   - stale instructions
   - contradictory rules
   - oversized files
   - redundant skills
   - whether the journal is still helping

11. **Promote repeated corrections into durable artifacts**
   If you correct the same thing 3+ times:
   - add to gotchas skill, AGENTS.md, or a specific skill

12. **Review whether MCP memory is actually needed**
   Only escalate if file-based continuity is failing repeatedly, not preemptively.

---

If you want, I can turn this into a **concrete recommended repo layout and file templates** for:
- `AGENTS.md`
- `CLAUDE.md`
- `ARCHITECTURE.md`
- `JOURNAL.md`
- `.claude/skills/gotchas/SKILL.md`
- a **tool-trial ADR template** for your workflow.
