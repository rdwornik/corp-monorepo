# Codex Review — adr27-safety-n1

**Date:** 2026-07-17
**Branch:** `fix/adr27-safety-centralization`
**HEAD:** `a58fc7e`
**Diff range:** `main..fix/adr27-safety-centralization`
**Codex version:** codex-cli 0.144.5
**Mode:** diff-review

---

## Focus

- Centralized synced-path guard correctness (corp/safety/onedrive.py): guard_path and is_onedrive_path fail-closed on resolve error; resolve-then-substring detection; guard_within_root containment via is_relative_to.
- project/cli.py copy-to-vault guard: does the synced-path raise plus vault-root containment close the D6 arbitrary-write hole? Any bypass via symlink, traversal, or a missing guard?
- renderer.py exception-type migration to the centralized error: any behavior regression for corp.project.cli.render callers, or narrowed-detection risk?
- cleanup/errors.py re-export shim: do all existing importers keep class identity?
- AST scanner test_no_unguarded_writes.py: scoping plus Rule1 and Rule2 logic sound; any false-negative letting an unguarded write through?

---

## Findings
## Critical

### [CRITICAL] src/corp/project/cli.py:314 — Existing destination symlink bypasses both guards

**What:** `guard_path` and `guard_within_root` validate only `vault_dir`; an existing `vault_dir/index.md` symlink can point outside the vault or into OneDrive, and `shutil.copy2` follows it.

**Why:** `--copy-to-vault` can still overwrite an arbitrary or synced file, so the D6 arbitrary-write hole remains open.

**Fix direction:** Validate the final destination file after creating the directory, reject symlinks/reparse points, and use a no-follow or atomic write strategy; add an existing-file-symlink regression test.

### [CRITICAL] src/corp/safety/onedrive.py:107 — Centralization narrows renderer’s synced-path protection

**What:** The centralized guard matches only the exact `"OneDrive - Blue Yonder"` substring, while the replaced renderer guard rejected any case-insensitive `"onedrive"` path.

**Why:** `render_project` now permits writes under paths such as the personal `~/OneDrive`, regressing the previous synced-directory protection.

**Fix direction:** Preserve the renderer’s broader behavior centrally—preferably by detecting configured OneDrive roots/path segments case-insensitively—and add personal-OneDrive coverage.

## High

### [HIGH] tests/safety/test_no_unguarded_writes.py:45 — Enforcement scans only one production file

**What:** `ROOTS` contains only `src/corp/project/cli.py`, excluding every other production module, including the migrated renderer, cleanup, and action write sites.

**Why:** New unguarded mutations elsewhere in `src/corp` pass CI, preserving the omission failure mode the scanner is intended to eliminate.

**Fix direction:** Recursively scan all Python files under `src/corp`, with explicit reviewed exemptions where necessary.

### [HIGH] tests/safety/test_no_unguarded_writes.py:229 — Rule 1 accepts guards that cannot protect the write

**What:** Rule 1 checks only whether any `guard_path` call exists anywhere under the function AST; a guard after the write or inside an unrelated nested function satisfies it.

**Why:** An actually unguarded write can pass the safety gate. Both forms reproduce with zero reported violations.

**Fix direction:** Exclude nested function bodies and require a relevant guard to dominate each dangerous primitive on every reachable path.

### [HIGH] tests/safety/test_no_unguarded_writes.py:175 — Rule 2 treats conditional termination as unconditional

**What:** `_handler_prevents_continuation` returns true if it finds any `raise` or exit call anywhere in a handler, including inside a conditional or nested definition.

**Why:** A handler such as `if debug: raise` can otherwise swallow `OneDriveSafetyError`, fall through to the write, and still pass the scanner.

**Fix direction:** Verify that every handler control-flow path terminates or re-raises; add conditional-raise and conditional-exit negative fixtures.

## Medium

(none)

## Low

(none)
