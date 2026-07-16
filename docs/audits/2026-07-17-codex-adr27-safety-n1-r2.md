# Codex Review — adr27-safety-n1-r2

**Date:** 2026-07-17
**Branch:** `fix/adr27-safety-centralization`
**HEAD:** `4c0aa91`
**Diff range:** `main..fix/adr27-safety-centralization`
**Codex version:** codex-cli 0.144.5
**Mode:** diff-review

---

## Focus

Re-review after fixes. Confirm resolution of the prior round's findings:
- project/cli.py copy-to-vault: now rejects a pre-existing dest symlink (no-follow) and guards the final destination file plus vault-root containment. Is the D6 arbitrary/synced-write hole now closed, or is there a residual bypass?
- guard_path/is_onedrive_path gained a strict= param; renderer.py uses strict=False to preserve its broad pre-centralization detection. Any remaining narrowing?
- scanner test_no_unguarded_writes.py Rule 1 now scopes to the function own body and requires lexical dominance (guard before write); Rule 2 counts only top-level handler termination. Any remaining false-negative in the logic?
- The scanner ROOTS deliberately covers only project/cli.py for this batch (full-repo Decision-1 is ADR-27 PR-3); assess only the correctness of what is in scope, not scope breadth.

---

## Findings
## CRITICAL

## CRITICAL src/corp/project/cli.py:329 — destination can still redirect writes through hard links or a pathname race

**What:** The checks reject existing symlinks, but `shutil.copy2()` subsequently reopens `dest_file` by pathname; an existing hard link to a OneDrive file passes every check, and the path can also be replaced after validation.  
**Why:** `copy2()` truncates the linked/replaced target, so this can still modify a synced file despite the guard—violating the merge-blocking OneDrive invariant.  
**Fix direction:** Create a new temporary file exclusively without following links, copy into it, then atomically replace the destination; ensure the destination directory cannot be swapped between containment validation and creation.

## HIGH

## HIGH tests/safety/test_no_unguarded_writes.py:282 — line ordering is not guard dominance

**What:** Rule 1 accepts any earlier guard call, including `if enabled: guard_path(dst)` followed by an unconditional write, or a guard applied to an unrelated path.  
**Why:** The scanner can pass a function whose write is reachable without its destination ever being guarded, silently weakening the intended CI safety enforcement.  
**Fix direction:** Require control-flow dominance on every path to the write and associate the guard argument with the write destination, or enforce writes through a small recognized guarded helper.

## HIGH tests/safety/test_no_unguarded_writes.py:210 — arbitrary `.exit()` methods count as unconditional termination

**What:** `_stmt_terminates()` treats any attribute named `exit`, `quit`, or `_exit` as terminating, so `logger.exit()` or `session.quit()` makes a swallowed guard appear safe.  
**Why:** Such methods may return normally, allowing execution to reach the dangerous write while Rule 2 reports no violation.  
**Fix direction:** Match only exact recognized callees such as `sys.exit` and `os._exit`, plus explicit `raise`/`return`, and add a negative fixture using an unrelated `.exit()` method.

## MEDIUM

(none)

## LOW

(none)

`renderer.py`’s `strict=False` use preserves the previous case-insensitive broad `"onedrive"` detection; I found no remaining narrowing there. Tests were not executed because the repository reviewer contract permits read-only commands only.
