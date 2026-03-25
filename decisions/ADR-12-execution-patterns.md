# ADR-12: Claude Code Execution Patterns

**Date:** 2026-03-22 | **Status:** Accepted

## Context

Claude Code sessions were repeating the same mistakes across repos. No lightweight
mechanism existed to capture and re-surface repo-specific lessons.

## Decision

Do not install third-party Superpowers. Adopt a minimal custom layer: global
`gotchas.md` skill (triggered by context keywords), targeted verification scripts
per repo (PASS/FAIL output only), and a lightweight Understand step before planning
non-trivial tasks. Review friction/value after 30 days.

## Consequences

- `~/.claude/skills/gotchas/gotchas.md` is the single consolidation point for lessons
- Verification scripts run after pytest; they catch cross-repo and schema issues tests miss
- New process features added only if the 30-day review shows demonstrable value
