# Development Journal

Append-only log. 3 lines per session. Never edit old entries.
Claude Code: read last 5 entries before starting work.

---

## 2026-03-25 night session
- **Did:** Monorepo complete (6 packages, 2,153 tests). Naming convention v2 (19 type codes, 15 client aliases). Code review fixes (2 critical, 4 high). Training data fixtures from 690 extractions. Routing feedback table. Trust_level protection. Vault ingest pipeline.
- **Failed:** Standalone repo folder rename blocked by Windows file locks. CKE had 6 pre-existing test failures (fixed).
- **Next:** Integration tests, pre-commit hooks, coverage gaps (CPE classifier, RFP anonymization), pilots.

## 2026-03-25 late night
- **Did:** Workflow improvements: JOURNAL.md, integration tests (6 new → 23 total), pre-commit hooks (ruff), dev-check.ps1, session-start.ps1, Session Protocol + Prompt Decision Rule in CLAUDE.md.
- **Failed:** sample_output.json is deep extraction format (qa_pairs/slide_breakdown), not frontmatter — test adapted accordingly.
- **Next:** Coverage gaps (CPE classifier, RFP anonymization), Hypothesis tests, ADR conversion.

## 2026-03-25 continuation
- **Did:** 79 CPE classifier tests (all 20 priority rules, priority ordering, edge cases). 25 RFP anonymization tests (core + middleware, all patched via mock). 5 Hypothesis property-based tests. 14 ADRs distilled from AI Council debates into decisions/.
- **Failed:** \bpayload\b doesn't match payload_inbound (underscore is \w — word boundary lesson). \bstrategy\b doesn't match supply_chain_strategy same reason. Fixed test inputs.
- **Next:** Run dev-check.ps1 full quality gate, consider adding hypothesis to monorepo pyproject.toml dev deps.
