# Codex Review — adr27-safety-n1-r4

**Date:** 2026-07-17
**Branch:** `fix/adr27-safety-centralization`
**HEAD:** `af6821d`
**Diff range:** `main..fix/adr27-safety-centralization`
**Codex version:** codex-cli 0.144.5
**Mode:** diff-review

---

## Focus

Convergence confirmation (final round). Round-3's only finding was that os.replace slipped past the scanner's .replace heuristic; that is now fixed: _is_dangerous_primitive matches os.* (incl. os.replace) BEFORE the .replace str/Path arg-count check, 'replace' added to tracked os primitives, self-tests cover unguarded-flagged / guarded-passes / str.replace-unflagged. Confirm the scanner now covers os.replace and the shipped project/cli.py atomic write is enforced.
Assess ONLY for genuinely new, realistic defects in shipped code. Do NOT re-raise: (a) full every-path CFG dominance / guard-argument association (intentionally beyond ADR-27's presence-based Rule 1, an ADR-acknowledged limitation); (b) directory-level TOCTOU on this local single-user CLI (out of threat model). Both are accepted, documented design boundaries.

---

## Findings
## Critical

(none)

## High

(none)

## Medium

(none)

## Low

(none)

Convergence confirmed: the scanner detects `os.replace` before the generic `.replace` heuristic, flags the unguarded fixture, accepts the guarded fixture, ignores `str.replace`, and recognizes the shipped `project/cli.py:346` atomic write with no violation.
