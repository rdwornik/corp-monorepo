# Disposition — `hybrid_classifier.json` duplication: ACCEPT-WITH-REASON

- **Date:** 2026-08-08
- **Trigger:** hub `[#283]` — de-dup-or-accept the two byte-identical `hybrid_classifier.json` copies (RULING-W: decided here in corp-monorepo per corp's own packaging reality, reported to the hub).
- **Evidence HEAD:** `c954876` (branch base — the sweep and every file:line below were derived fresh at this sha); change committed at `d19aad2` on `worktree-lane-a-283-dedup`.
- **Verdict:** **ACCEPT-WITH-REASON** — keep both copies; reason recorded in-repo.
- **Method:** one read-only reference sweep over every locator naming either path (imports, `open()`/`Path` readers, packaging config, CI, tests, docs, ignore files), then source-level verification of each load-bearing claim by the deciding session.

---

## 1. The duplication

Two byte-identical files, witnessed 2026-08-08:

- `models/hybrid_classifier.json`
- `src/corp/extractor/data/hybrid_classifier.json`

Both 1,078,232 bytes, sha256 `aaa65201d9a2a5313a9320fcb6a5d23d648be0f1cf9f0dd13c8be26bcd565f05`. Cost in git: ~1.08 MB duplicated.

They are identical because **one script writes both in a single run** — `scripts/train_classifier.py:154` (`models/`) and `:162-163` (package data), the latter already carrying the intent comment `# Also copy to CKE data dir for packaging`.

## 2. Verdict rationale — both copies are load-bearing, through different channels

The de-dup branch requires exactly one copy to be load-bearing. The sweep shows two, on disjoint channels:

**Copy A — `models/hybrid_classifier.json` — training artifact**

- Written by the trainer: `scripts/train_classifier.py:154`.
- Read by the eval harness: `scripts/eval_classifier.py:31` (`MODEL_PATH = MODELS_DIR / "hybrid_classifier.json"`), loaded at `:36` and scored against the **locked held-out split** `models/classifier_test.json` (`eval_classifier.py:30`).
- Cohabits with its reproducibility cohort in the same directory: `classifier_train.json`, `classifier_test.json`, `cv_report.txt`, `eval_results.json`.
- **Outside `src/`** — therefore excluded from the wheel/sdist, and explicitly excluded from import-boundary enforcement (`tach.toml:13`).

**Copy B — `src/corp/extractor/data/hybrid_classifier.json` — shipped package data**

- Written by the same trainer run: `scripts/train_classifier.py:162-163`.
- **Shipped**: `pyproject.toml:65` — `"corp.extractor" = ["data/*.yaml", "data/*.json"]` sweeps it into every wheel and sdist. Corroborated *out-of-tree* by a locally built manifest (`src/corp.egg-info/SOURCES.txt`, line 100, observed in the primary checkout) — that path is **gitignored build output** (`.gitignore:3`, `*.egg-info/`) and absent from a fresh checkout, so it is supporting observation only, not a repo locator.
- **Runtime default**: `src/corp/extractor/hybrid_loader.py:25` — `_DEFAULT_MODEL_PATH = Path(__file__).parent / "data" / "hybrid_classifier.json"`, consumed via `get_cached_model()` at `src/corp/extractor/doc_type_classifier.py:134`.
- Bound by the extractor test: `tests/extractor/test_hybrid_classifier.py:25`.

**Why neither deletion is available:**

- Delete A → `scripts/eval_classifier.py` breaks outright (`FileNotFoundError` at `hybrid_loader.py:40`), and the artifact is severed from the locked split it must be scored against. Repointing eval at B would make the eval harness read the *packaged* asset rather than the trainer's own output, collapsing a deliberate artifact/ship boundary that `models/` (outside `src/`, outside `tach.toml`) exists to hold.
- Delete B → **every installed deployment loses its model.** `models/` does not exist inside an installed wheel, so `_DEFAULT_MODEL_PATH` has nothing to fall back to. Packaging cannot reach `models/` either: `[tool.setuptools.packages.find] where = ["src"]`, so `models/` is unreachable by `package-data` without a `data-files`/force-include workaround. This is precisely the frozen contract's named failure mode — *deleting a copy that packaging silently ships*.

Symlinking is not an option (Windows repo, explicitly excluded by the contract).

**Accepted cost:** 1.08 MB of git duplication, in exchange for keeping the artifact lineage and the shipped asset independently replaceable. The model is retrained whenever the training corpus grows by >20% (corp ADR-18), so the duplication is regenerated, not hand-maintained — the trainer keeps the two copies in lockstep by construction.

## 3. Reference table (sweep evidence, file:line)

**Load-bearing — copy A (`models/`)**

| Locator | Role |
|---|---|
| `scripts/train_classifier.py:154` | WRITES A (trainer's canonical output) |
| `scripts/eval_classifier.py:31` | READS A (`MODEL_PATH`) |
| `scripts/eval_classifier.py:36` | loads A against locked split |
| `scripts/eval_classifier.py:30` | `classifier_test.json` — the paired split |
| `tach.toml:13` | `"models/"` excluded from import boundaries |

**Load-bearing — copy B (`src/corp/extractor/data/`)**

| Locator | Role |
|---|---|
| `scripts/train_classifier.py:162-163` | WRITES B ("for packaging") |
| `pyproject.toml:65` | SHIPS B — `"corp.extractor" = ["data/*.yaml", "data/*.json"]` |
| `src/corp/extractor/hybrid_loader.py:25` | `_DEFAULT_MODEL_PATH` — runtime default |
| `src/corp/extractor/hybrid_loader.py:38` | path resolution (`model_path or default`) |
| `src/corp/extractor/hybrid_loader.py:130` | same, cached-model path |
| `src/corp/extractor/doc_type_classifier.py:134` | `get_cached_model()` consumer |
| `src/corp/extractor/_paths.py:16` | `DATA_DIR` constant |
| `tests/extractor/test_hybrid_classifier.py:25` | test binds B's path |

Every locator above was re-read at source by the deciding session, not accepted from the sweep. One sweep finding was **rejected** on that check: `src/corp.egg-info/SOURCES.txt:100` is gitignored build output present only in the primary checkout, so it is cited in §2 as out-of-tree corroboration rather than as repo evidence.

**Non-load-bearing mentions** (prose/context only; no reader depends on them): `models/README.md`; `docs/decisions/ADR-18-algorithmic-hybrid.md`; `docs/archive/2026-03-28_CLEANUP_PLAN.md:126`; `docs/archive/2026-06-16-current-state-architecture-audit-inventory.json:3179-3180, 9195-9196, 19387-19388` (already recorded both files as duplicates); `docs/audits/2026-07-11-qa-lived-onboarding-and-root-hygiene.md:188`; `docs/audits/2026-07-05-functional-artifact-lifecycle.md:21,64`; `JOURNAL.md:681,825`; `.corp-monorepo.code-workspace:85`.

**Confirmed absent** (checked, none found): `MANIFEST.in`, `setup.py`, `setup.cfg` (do not exist); no Dockerfile; no CI workflow references either path (`.github/workflows/tach.yml`, `nightly-conformance-triage.yml`); no `.gitignore` / `.gitattributes` entry touching either file — both are tracked.

## 4. Change executed

Documentation and comments only — **no behaviour change, no file deleted, no reader repointed, no packaging config touched.**

```
models/README.md            | 22 ++++++++++++++++++++++
scripts/train_classifier.py |  6 +++++-
2 files changed, 27 insertions(+), 1 deletion(-)
```

- `models/README.md` — the reason at the artifact location: the duplication is deliberate, which copy serves which channel, and what breaks on either deletion.
- `scripts/train_classifier.py` — the intent comment at the duplicating write site expanded from "for packaging" to name the by-design duplication and point at `models/README.md`.

## 5. Verification

- Full suite at branch base: **2730 passed, 6 skipped** (180s).
- `tests/extractor/test_hybrid_classifier.py` run explicitly: **11 passed**. Checked deliberately, because that module is guarded by `@pytest.mark.skipif(not MODEL_PATH.exists())` (`:41`) — a missing copy B would have turned the whole module green-by-skipping rather than failing. It ran; it did not skip.
- Import binding verified to the lane worktree (not the primary checkout's editable install) before testing, so the run is honest to this tree.
- All pre-commit / commit-msg gates passed on `d19aad2`; no hook weakened or bypassed.
