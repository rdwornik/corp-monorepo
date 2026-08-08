# models/

Classifier training/test datasets + evaluation artifacts consumed by `scripts/*classifier*.py`. NOT code models (see `src/corp/models.py`), NOT binaries.

## `hybrid_classifier.json` is duplicated deliberately — do not "de-dup" it

`models/hybrid_classifier.json` and `src/corp/extractor/data/hybrid_classifier.json` are byte-identical
by design (1,078,232 bytes, sha256 `aaa65201…65f05`). `scripts/train_classifier.py` writes **both** in a
single run — `train_classifier.py:154` and `:162` — because each copy is load-bearing through a different
channel:

- **This copy (`models/`)** is the *training artifact*. It belongs with the reproducibility cohort in this
  directory (`classifier_train.json`, `classifier_test.json`, `cv_report.txt`, `eval_results.json`) and is
  the copy `scripts/eval_classifier.py` scores against the locked held-out split (`eval_classifier.py:31`).
  `models/` sits outside `src/`, so it is excluded from the wheel and from `tach.toml`.
- **The `src/corp/extractor/data/` copy** is *shipped package data* (`pyproject.toml:65` —
  `"corp.extractor" = ["data/*.yaml", "data/*.json"]`) and is what the runtime loads by default
  (`hybrid_loader.py:25`, `_DEFAULT_MODEL_PATH`). `models/` does not exist inside an installed wheel, so the
  runtime cannot fall back to this copy.

Deleting either side breaks a real path: drop `models/` and the eval harness loses the artifact paired with
its locked split; drop the packaged copy and every installed deployment loses its model. The 1.08 MB is the
accepted cost of keeping the artifact lineage and the shipped asset separable.

Evidence and full reader table: `docs/audits/2026-08-08-hybrid-classifier-duplication-disposition.md`.
