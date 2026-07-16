# Codex Review — adr27-safety-n1-r3

**Date:** 2026-07-17
**Branch:** `fix/adr27-safety-centralization`
**HEAD:** `ebce0b6`
**Diff range:** `main..fix/adr27-safety-centralization`
**Codex version:** codex-cli 0.144.5
**Mode:** diff-review

---

## Focus

Final convergence re-review. Confirm resolution of round-2 findings:
- project/cli.py copy-to-vault now writes atomically: mkstemp inside the validated vault_dir, copy into it, os.replace() over dest_file (repoints the directory entry, does not truncate a hard-linked target). Is the hard-link truncation vector now closed? Directory-level TOCTOU is explicitly accepted as out of this local single-user CLI's threat model — do not re-raise it as blocking.
- scanner _stmt_terminates now matches only sys.exit / os._exit / builtin exit()/quit() plus raise/return; an unrelated logger.exit() no longer counts. Confirmed?
- Note: full every-path CFG dominance + guard-argument association are intentionally beyond ADR-27's presence-based Rule 1 (already met and strengthened with own-scope lexical dominance) and are the ADR's acknowledged conditional-guard limitation deferred to Codex review — assess correctness of the implemented rules, not this accepted design boundary.
Report only genuinely NEW realistic defects in shipped code.

---

## Findings
```markdown
## CRITICAL

(none)

## HIGH

### tests/safety/test_no_unguarded_writes.py:115 — `os.replace()` bypasses the safety scanner

**What:** `_is_dangerous_primitive()` classifies every two-argument `.replace()` call as non-dangerous, so an unguarded `os.replace(src, dst)` produces zero violations.

**Why:** The newly shipped atomic mutation at `project/cli.py:346` is invisible to ADR-27’s enforcement, allowing future unguarded replacements to pass CI.

**Fix direction:** Recognize `os.replace` before applying the `str.replace` argument-count heuristic and add an unguarded `os.replace` self-test.

## MEDIUM

(none)

## LOW

(none)

Round-2 confirmations: the hard-link truncation vector is closed by the temporary-file plus `os.replace()` approach, and unrelated calls such as `logger.exit()` no longer count as handler termination.
```
