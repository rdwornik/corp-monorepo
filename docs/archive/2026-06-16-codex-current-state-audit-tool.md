# Codex Review — current-state-audit-tool

**Date:** 2026-06-16
**Branch:** `audit/current-state-architecture`
**HEAD:** `79b9902`
**Diff range:** `main..audit/current-state-architecture`
**Codex version:** codex-cli 0.136.0
**Mode:** diff-review

---

## Focus

- Read-only / zero-mutation guarantee: is the single write sink (write_inventory) truly the only mutation path? Any way scanning could write/delete/hydrate?
- OneDrive safety: placeholder detection (st_file_attributes), no hydration of cloud-only files, marker-based prune, imported _guard_onedrive reuse.
- Correctness of metrics: naming classification, duplication clustering/wasted-bytes, source-of-truth scoping to local files, automation parsing.
- Bounded traversal: follow_symlinks=False, error handling, long-path handling, performance on large trees.

---

## Findings
## Critical

(none)

## High

## HIGH config/audit.yaml:8 — hardcoded local scan roots

**What:** The committed audit config hardcodes `C:/Users/1028120/...` paths, including the local username.  
**Why:** This makes the audit non-reproducible on any other workstation and can silently produce missing-root inventories.  
**Fix direction:** Resolve roots from environment variables or the repo’s centralized path config, with a local-only sample config if needed.

## HIGH scripts/_audit_core.py:766 — text scan can hydrate files and is not byte-bounded

**What:** `_read_text_safe()` uses `path.read_bytes()[:max_bytes]`, which opens the file without placeholder checks and reads the whole file before slicing.  
**Why:** Automation scanning can hydrate cloud-only files and can load large `.md`/config files fully into memory despite the `max_bytes` cap.  
**Fix direction:** Stat with `follow_symlinks=False`, skip `is_cloud_placeholder()`, and stream only up to `max_bytes`.

## HIGH scripts/_audit_core.py:828 — automation scan bypasses no-symlink traversal

**What:** `_build_repo_automation()` uses `Path.is_dir()` and `glob()` directly for workflow/routine/db discovery.  
**Why:** Those calls can follow symlinks or junctions, bypassing the `walk_tree(... follow_symlinks=False)` invariant and potentially reading outside the intended repo tree.  
**Fix direction:** Route automation discovery through the same no-follow traversal helper, or explicitly reject symlinks/reparse points before `is_dir()`/`glob()`.

## HIGH scripts/_audit_core.py:109 — hashed_count is always zero

**What:** `PathInventory.hashed_count` is serialized but never populated, while `collect_files()` does hash eligible files later.  
**Why:** The generated inventory reports incorrect metrics, contradicting the duplicate/source-of-truth sections that depend on hashes.  
**Fix direction:** Populate per-root hash counts from `collect_files()` or remove the field from the inventory schema.

## HIGH scripts/_audit_core.py:312 — skipped directory errors are not recorded in inventory

**What:** `walk_tree()` logs `os.scandir()` failures but does not propagate them into `PathInventory.errors`.  
**Why:** The JSON artifact can show zero errors even when whole subtrees were skipped, making audit totals look complete when they are partial.  
**Fix direction:** Return/yield traversal errors or pass an error collector so each root inventory records skipped directories.

## Medium

(none)

## Low

(none)
