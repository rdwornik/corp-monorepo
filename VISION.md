---
version: 1.0
tier: standard
scale: L
owner: rob
status: active
last_reviewed: 2026-05-18
---

# VISION — corp-monorepo

## Vision

`corp-monorepo` is the consolidated codebase of a personal **Corporate
OS** — an AI-powered platform that automates the repetitive parts of
Rob's pre-sales / solution-advisory work at Blue Yonder and turns the
scattered knowledge of that work into a structured, queryable system.

It absorbs corporate source material — presentations, RFPs, recorded
sessions, product and platform specs — extracts the facts into a
structured knowledge base, and drives the downstream work products that
pre-sales work demands: RFP responses, presentation drafts, opportunity
preparation.

**The long-term horizon:** as much of the repetitive pre-sales workflow
as possible — knowledge management, RFP answering, deck drafting,
opportunity tracking — runs through one coherent, automated pipeline
instead of ad-hoc manual effort. Two outcomes define "realised": the
work is automated, and the corporate knowledge Rob accumulates is
organised rather than lost.

`corp-monorepo` is the largest repository in the ecosystem (Scale L) and
its product layer — the place where the ecosystem's methodology and
tooling are turned into actual day-job leverage.

## Scope

**In scope:**
- AI-driven extraction of facts from corporate documents into a
  structured knowledge base (the Obsidian vault + cross-project index).
- The knowledge-base orchestration layer — vault writing, routing,
  cross-project search.
- Pre-sales work products generated from that knowledge: RFP-answering
  support, presentation / deck drafting, opportunity preparation.
- The unified `src/corp/` namespace, the Click-based CLIs, and the
  shared schema / taxonomy the packages depend on.
- The pipelines connecting source documents → extracted facts →
  knowledge base → work products.

**Out of scope (non-goals):**
- Methodology, governance, and cross-repo conventions — those live in
  `.dev-knowledge`.
- The AI Council decision tool — standalone `ai-council` repo.
- Time / calendar automation — standalone `corp-sca-time-automation`.
- Operations / infrastructure tooling — standalone `corp-ops`.
- Blue Yonder's own product or platform code — `corp-monorepo` is Rob's
  personal tooling, never a fork or copy of employer product code.
- Storage of credentials or corporate secrets in-repo (secrets live in
  the external `.secrets` location).

## Values

Universal engineering values (clean architecture, single-responsibility
modules, config-in-YAML, dataclasses over dicts, Click + Rich + pytest,
logging over print) are defined once in `.dev-knowledge` ESSENTIALS and
in `corp-monorepo`'s own `CLAUDE.md` — VISION does not duplicate them.

`corp-monorepo`-specific operating principles:

- **Single writer for the knowledge base.** The orchestration layer is
  the sole writer of the vault; extraction is a pure, side-effect-free
  engine.
- **Source / extract separation.** Source material is immutable;
  extracted artifacts are regenerable. The two never mix.
- **One routing authority.** Routing configuration has a single source
  of truth, not per-module copies.
- **Incremental, never big-bang.** Structural change lands as small,
  independently revertable commits.
- **Deterministic and low-friction.** The system favours predictable,
  scannable, deterministic behaviour over cleverness.

## Relationships

`corp-monorepo` is a **consumer** of `.dev-knowledge` — it adopts the
ecosystem's methodology, conventions, and governance patterns, and feeds
lessons back. It depends on no other repository for code.

It is a **sibling** to the other repositories under `Dev/`:
`ai-council`, `corp-ops`, `corp-sca-time-automation`. There is **no
hierarchy** — only functional roles. `ai-council` may be used as a tool
to produce architectural decisions for `corp-monorepo`; its debate
transcripts return per the Council output convention.

`corp-monorepo` writes its knowledge base to an **Obsidian vault** that
lives outside the repository — the vault is the durable knowledge store;
the repo is the engine that fills and queries it.

## Lifecycle

VISION is a **living, verifiable document** — not a one-shot statement.

**Review triggers** (not deadlines):
- A new package or major capability joining `corp-monorepo`.
- A significant scope reinterpretation surfacing in a fresh AI chat
  (drift signal).
- A major architectural shift in the ecosystem.
- When the Vision section reads as realised — propose the next horizon.

**Verification mechanism:** VISION is checked against the repo's other
artifacts to detect drift — `BACKLOG.md` reflects what VISION declares
in-scope; `JOURNAL` entries trace back to VISION goals; ADRs implement
VISION decisions. Any contradiction is a drift signal that triggers
review.

**Tier classification:** Standard tier, Scale L. `corp-monorepo` is the
ecosystem's largest repository — multiple packages, deep history,
extraction + orchestration + product surface — and carries the full
Scale-L mandatory file set per ADR-38.

**Ownership:** Rob (sole authority).

**Edit process:** AI Council debate for material Vision or Scope
changes; conversational edit for clarifications and the References
section.

## References

- `README.md` — current capability and module index
- `ARCHITECTURE.md` — system architecture (repo root)
- `CLAUDE.md` — agent session guidance and dev standards
- `CONTRIBUTING.md` — branch / commit / review conventions
- `JOURNAL.md` — session-by-session activity history
- `BACKLOG.md` — cross-session pending items
- `docs/decisions/` — architectural decision records
- `.dev-knowledge/` — ecosystem methodology this repo consumes
