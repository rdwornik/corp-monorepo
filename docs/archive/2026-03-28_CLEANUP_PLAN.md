# Monorepo Cleanup Plan — 2026-03-28

**Total repo size: 25 GB** (git repo itself: 96 MB)
**Biggest offenders:** CKE `_outputs/` (20 GB), `.sandbox/` (2.4 GB), `rebuild_staging/` (2.0 GB)

---

## 1. SAFE TO DELETE (24.4 GB recoverable)

### 1a. Cache/Build Artifacts (auto-regenerated)

| What | Count | Size | Why safe |
|------|-------|------|----------|
| `__pycache__/` dirs | 46 | ~5 MB | Python bytecode, auto-regenerated |
| `*.egg-info/` dirs | 6 | ~100 KB | Editable install metadata, recreated by `pip install -e .` |
| `.pytest_cache/` dirs | 7 | ~255 KB | Pytest cache, recreated on next run |
| `.ruff_cache/` dirs | 6+ | ~50 KB | Linter cache, recreated on next run |
| `.hypothesis/` | 1 | ~254 KB | Hypothesis test DB, recreated on next run |

**All gitignored already.** Safe to nuke:
```bash
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null
find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null
rm -rf .hypothesis/
```

### ~~1b. .sandbox/ (2.4 GB)~~ — DO NOT DELETE

Contains `cleanup_pilot/` with 123 files — pipeline test results **not yet reviewed by Rob**.
Keep until review is complete.

### 1c. Root `output/` dir (30 KB) — gitignored, safe to delete

Contains `test/` subdir. Test output artifact. Tiny, but unnecessary.
```bash
rm -rf output/
```

### 1d. CKE `output/` dir (54 KB) — gitignored, safe to delete

Same: test output from `eval_extraction.py`. Regenerable.
```bash
rm -rf packages/corp-knowledge-extractor/output/
```

---

## 2. NEEDS ROB'S DECISION (22 GB)

### 2a. CKE `_outputs/` (20 GB, 4,552 files) — DO NOT DELETE YET

**This is 80% of the entire repo's disk footprint.**

Structure:
```
packages/corp-knowledge-extractor/_outputs/
├── README.md          ← tracked in git (tiny, informational)
├── inventory.md       ← tracked in git (tiny, informational)
├── jlr_pilot/         18 files — JLR pilot extraction run
├── jlr_staged/        18 files — JLR staged extraction run
└── _outputs/          ← NESTED duplicate (this is the bulk)
    ├── golden_set/    103 MB — evaluation reference extractions
    ├── test/          12 MB — test extraction output
    ├── misc/          2.7 GB — miscellaneous extraction runs
    ├── v2/            11 GB — full v2 extraction output
    └── v3/            6.5 GB — full v3 extraction output
```

**BLOCKED: Needs v2-vs-v3 dedup/best-version audit first.**

For each source document that has both a v2 and v3 extraction, we need to determine
which version produced the better result (higher quality score, more complete frontmatter,
richer facts). Only after that audit can we safely delete the losing version per source
and consolidate to a single best extraction per document.

The nested `_outputs/_outputs/` path suggests a script wrote to wrong relative dir at some point.

**Next steps (in order):**
1. Inventory: list all source documents present in both v2/ and v3/
2. For each pair: compare quality_score, fact count, frontmatter completeness
3. Produce a best-version manifest (source_hash → winner version)
4. Delete losing versions, flatten the nested `_outputs/_outputs/` path
5. Then decide: keep golden_set locally, archive or delete the rest

### 2b. `.ecosystem/rebuild_staging/` (2.0 GB, 2,037 files, 279 extract dirs) — gitignored

This is the vault rebuild output from Council Decision #20 (2026-03-27). Contains:
- 279 `extract/` subdirectories — CKE extraction output per source document
- Source files + extraction JSON pairs
- Already ingested into the vault

**Questions for Rob:**
- Has the rebuild been fully verified and ingested?
- If yes, safe to delete (regenerable from source files via CKE batch)
- If partially done, identify which extractions haven't been ingested yet

---

## 3. SHOULD GITIGNORE (currently tracked but shouldn't be)

### 3a. Nothing critical found

Git tracking is clean. The only tracked files inside gitignored directories are:
- `packages/corp-knowledge-extractor/_outputs/README.md` — informational, 1 file
- `packages/corp-knowledge-extractor/_outputs/inventory.md` — informational, 1 file

These are intentionally tracked docs inside an otherwise-ignored dir. **Low priority.** Could move to `docs/` if desired, but harmless.

### 3b. `.claude/` dirs in packages — tracked (intentional)

6 packages each have `.claude/rules/` with code-standards, python-env, testing rules. These are **intentionally tracked** Claude Code configuration. CKE also has `.claude/skills/verify/`. **Keep.**

---

## 4. SHOULD KEEP (intentional, correctly placed)

### Root directories (all correct):
| Dir | Purpose | Status |
|-----|---------|--------|
| `config/` | `paths.toml` | Correct |
| `decisions/` | 21 ADRs | Correct |
| `docs/` | 3 phase reports | Correct |
| `eval/` | `eval_history.jsonl` + `ontology_benchmark.md` | Correct |
| `models/` | `hybrid_classifier.json` + train/test splits + eval results (1.4 MB) | Correct |
| `packages/` | 6 packages | Correct |
| `scripts/` | 22 utility scripts | Correct |
| `tests/` | `integration/` tests | Correct |
| `.ecosystem/` | Handoff, archive, council transcripts | Correct |

### Root files (all correct):
| File | Status |
|------|--------|
| `CLAUDE.md` | Repo instructions |
| `JOURNAL.md` | Session log |
| `README.md` | Repo readme |
| `pyproject.toml` | Root project config |
| `ruff.toml` | Linter config |
| `.gitignore` | Comprehensive, well-maintained |
| `.gitattributes` | Git config |
| `.env.example` | Template |
| `.pre-commit-config.yaml` | Pre-commit hooks |

### Package-level files flagged but acceptable:
| File | Package | Verdict |
|------|---------|---------|
| `check_db.py` | corp-by-os | Debug utility (reads overnight_state.db). Could move to `scripts/` but harmless |
| `eval_extraction.py` | CKE | Extraction evaluator. Could move to `scripts/` but used from package root |
| `logs/.gitkeep` | corp-by-os | Empty log dir placeholder. Intentional |
| `tasks/*.md` | all 6 packages | Per-package task/lesson tracking. Intentional, tracked |

### .ecosystem/archive/ (intentional):
18 files — historical reports, manifests, logs. Read-only reference. **Keep.**

---

## 5. COULD MOVE (misplaced but not urgent)

| File | Current Location | Suggested | Priority |
|------|-----------------|-----------|----------|
| `check_db.py` | `packages/corp-by-os/` root | `packages/corp-by-os/scripts/` | Low |
| `eval_extraction.py` | `packages/corp-knowledge-extractor/` root | `packages/corp-knowledge-extractor/scripts/` | Low |

These are loose `.py` files at package root level. They work fine where they are. Moving them is cosmetic.

---

## 6. .GITIGNORE AUDIT

Current `.gitignore` is **comprehensive and correct**. Covers:
- `__pycache__/`, `*.egg-info/`, `dist/`, `build/`, `.ruff_cache/`, `.pytest_cache/`, `.mypy_cache/`
- `.venv/`, `venv/`, `env/`
- `.vscode/`, `.idea/`
- `desktop.ini`, `Thumbs.db`
- `.env`, `.claude/`
- `*.db`, `_outputs/`, `output/`
- `.hypothesis/`, `.sandbox/`, `.ecosystem/rebuild_staging/`

**No gaps found.** All generated/cached directories are properly ignored.

One note: `.claude/` is gitignored at root level, but package-level `.claude/` dirs are **explicitly tracked** (they contain rules/skills). This works because git tracks files that were `git add`ed even if the pattern is in `.gitignore` — but if someone clones fresh they'll get these files. This is correct behavior (the rules should be in the repo).

---

## Summary

| Action | Items | Disk Freed | Risk |
|--------|-------|------------|------|
| **Delete (safe)** | caches, output dirs | ~0.3 GB | Zero — all gitignored, auto-regenerated |
| **Keep (pending review)** | .sandbox/ | 2.4 GB | Pipeline test results not yet reviewed |
| **Keep (pending audit)** | CKE _outputs/ | 20 GB | Needs v2-vs-v3 best-version dedup audit first |
| **Rob's call** | rebuild_staging/ | 2.0 GB | Already ingested into vault? |
| **Keep** | everything else | — | All intentional |
| **Move (cosmetic)** | 2 loose .py files | 0 | Extremely low priority |

**Safe to delete now: ~0.3 GB.** Full cleanup (after audit + review): up to 24.4 GB recoverable.
