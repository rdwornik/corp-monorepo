# Codex Review — w3-corp-legs-ruff-home

**Date:** 2026-07-13
**Branch:** `chore/w3-corp-legs`
**HEAD:** `517b64c`
**Diff range:** `main..chore/w3-corp-legs`
**Codex version:** codex-cli 0.144.1
**Mode:** diff-review

---

## Focus

- Confirm E/F/I select + ignore E501 + tests/** per-file-ignore moved 1:1 from .ruff.toml to pyproject [tool.ruff.lint]
- Confirm no dangling config-source ambiguity after .ruff.toml deletion (single ruff config source)
- Confirm .methodology.yaml ruff-gate reason edit is truthful and does not alter the divergence semantics

---

## Findings
```text
## CRITICAL
(none)

## HIGH
(none)

## MEDIUM
(none)

## LOW
(none)
```

Ruff configuration moved 1:1, resolves solely from `pyproject.toml`, and the `.methodology.yaml` edit remains truthful without changing divergence semantics.
