# Codex Review — adr71-doctools-pilot

**Date:** 2026-06-03
**Branch:** `feat/consume-doctools-hooks`
**HEAD:** `8b80a34`
**Diff range:** `main..feat/consume-doctools-hooks`
**Codex version:** codex-cli 0.136.0
**Mode:** diff-review

---

## Focus

- Cross-repo pre-commit wiring: repo:/rev: stanza consuming ../.dev-knowledge at pinned commit 69558c7. Is local-path consumption + the pin correct/stable?
- Confirm only TOC hooks consumed; codemap hooks intentionally excluded (corp codemap hand-authored, ADR-51).
- Any risk in toc-freshness files-scope or toc-generate manual-stage config?

---

## Findings
## CRITICAL

(none)

## HIGH

(none)

## MEDIUM

(none)

## LOW

(none)

Visible config only consumes `toc-freshness` and `toc-generate`; no codemap hook IDs are included. `toc-freshness` is scoped to root `ARCHITECTURE.md`, which matches the intended TOC target. `toc-generate` is present without a local `files:` override, consistent with a manual-only generation hook if that stage is defined in the pinned hook repo.

Note: the sandbox blocked reading `../.dev-knowledge`, so I could not independently inspect the pinned hook manifest at `69558c7`; this review is based on the scoped diff and local config guarantees.
