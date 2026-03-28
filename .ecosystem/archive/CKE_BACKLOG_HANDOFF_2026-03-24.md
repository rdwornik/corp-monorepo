# CKE Backlog — Handoff Document (2026-03-23)

## Current State
- **Version:** v0.5.0 on main (v0.6.0 pending PDF multimodal merge)
- **Tests:** 584 (+ PDF multimodal tests pending)
- **Eval baseline:** 95/100 on Cognitive Friday, 79/100 golden set average
- **Repo:** clean, no stashes, .gitignore fixed, gemini-2.5 refs cleaned

---

## IN PROGRESS (Claude Code working on it)

### PDF Multimodal (Council decision 2026-03-23)
- All PDFs → Gemini Pro multimodal (direct upload)
- pdfplumber text extraction in parallel (grounding)
- Haiku enrichment on pdfplumber text
- Large PDF guard (>50 pages → truncate upload, full text via pdfplumber)
- Cover page PNG (PyMuPDF page 0)
- Prompt adapted for PDF layouts (diagrams, tables, flows)
- Tag as v0.6.0 when done
- **Status:** Claude Code prompt delivered, awaiting results

---

## IMMEDIATE (blocks batch extraction)

### Already shipped this session:
- ✅ quality_score (0-100) in frontmatter
- ✅ extraction_cost_usd in frontmatter
- ✅ force flag propagation for direct import path
- ✅ user_context from manifest/CLI → LLM prompt
- ✅ Section headers for DOCX/PDF (not "Slide")

### Still needed before batch:
| # | Feature | Effort | Blocks |
|---|---------|--------|--------|
| 1 | PDF multimodal (in progress) | 3h | Quality on 80+ PDFs |
| 2 | Tag validation against taxonomy.yaml | 1h | Tag drift in vault |
| 3 | batch.py slide_image_paths | 2h | Batch PPTX without slides |

---

## PHASE 2 — Validation (Week 2-3)

| # | Feature | Priority | Notes |
|---|---------|----------|-------|
| 4 | Golden set human-verified facts (10 files) | HIGH | Ground truth for accuracy measurement |
| 5 | FFmpeg scene threshold tuning (0.25-0.4) | MEDIUM | Test on 5+ diverse videos |
| 6 | Transcript quality evaluation (5 criteria ≥3.5) | MEDIUM | 5-10 video samples |
| 7 | Token usage monitoring (actual vs budget) | MEDIUM | Logging to cost_log.jsonl |
| 8 | Cost monitoring per-file dashboard | LOW | Aggregate from extraction_cost_usd |
| 9 | Prompt A/B testing vs baseline 94/100 | LOW | After golden set established |

---

## PHASE 3 — Hardening (Week 4-5)

| # | Feature | Priority | Notes |
|---|---------|----------|-------|
| 10 | D→A upgrade evaluation (full parallel extraction) | MEDIUM | Only if Haiku enrichment insufficient |
| 11 | Type-specific eval rubrics (transcript, session) | MEDIUM | Separate scoring for each output type |
| 12 | ADR documentation | LOW | Architecture decision records |
| 13 | COM vs LibreOffice stability assessment | LOW | 2 weeks production data needed |
| 14 | PPTX direct upload experiment (feature flag) | LOW | Council: gated experiment |

---

## SPRINT 2 — Gemini Capabilities (Month 2)

| # | Feature | Council Decision | Notes |
|---|---------|-----------------|-------|
| 15 | Structured Outputs (JSON mode) | #8b | Replace markdown parsing |
| 16 | Document Understanding benchmark | #8b | Binary PDF vs text comparison |
| 17 | Thinking mode for complex docs | #8b | Selective, complex docs only |
| 18 | Function calling (taxonomy lookup) | #8b+ | During extraction |
| 19 | DOCX multimodal (COM→PDF→Gemini) | Council PDF decision | Separate from PDF, own sprint |
| 20 | Image extraction from DOCX/PDF | Previous Council | Embedded images pipeline |

---

## SPRINT 3+ — Vision Features

| # | Feature | Description |
|---|---------|-------------|
| 21 | `corp learn <topic>` | Aggregate notes by topic → NotebookLM-ready bundle |
| 22 | NotebookLM API integration | Auto-create notebooks from extracted knowledge |
| 23 | Knowledge gap detection | "Which products have <N notes?" |
| 24 | Competitive battlecard extraction | Specialized prompt for competitive docs |
| 25 | Slide-level fact injection | Map PPTX facts to MP4 slide sections by title |
| 26 | Embeddings / vector search | Gated on 5+ FTS5 failures (Council #1) |
| 27 | Local LLM / Ollama integration | Offline extraction capability |
| 28 | Voice → Whisper pipeline | Meeting audio direct extraction |

---

## CORP-BY-OS DEPENDENCIES (blocks CKE indirectly)

| # | Feature | Status | Impact on CKE |
|---|---------|--------|---------------|
| 29 | corp ingest-extractions | In design | CKE output → vault |
| 30 | trust_level verified protection | NOT IMPLEMENTED | Must exist before batch re-extraction |
| 31 | MOC auto-generation (corp generate-mocs) | Not started | Uses CKE tags |
| 32 | Homepage dashboard | Not started | Dataview on CKE frontmatter |
| 33 | Controlled vocabulary file (taxonomy.yml) | Not started | CKE tag validation depends on this |
| 34 | FTS5 transcript indexing | Not started | Chunked segments |
| 35 | corp triage auto-classification | Not started | Uses CKE extraction |
| 36 | Forward slash audit in index.db | Not verified | May affect CKE paths |

---

## RFP AGENT DEPENDENCIES

| # | Feature | Status | Impact on CKE |
|---|---------|--------|---------------|
| 37 | vault_adapter.py parse verification_status | Not started | 3h after corp-by-os delivers |
| 38 | llm_router.py polarity filtering | Not started | Uses CKE dominant_polarity |
| 39 | RFP Agent trust boundary prompts | Not started | "Only verified facts for customer-facing" |
| 40 | RFP enrichment structured locator | Partial | Slide refs in strings, not dicts |

---

## ECOSYSTEM-WIDE

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 41 | ECOSYSTEM.md update with CKE v0.5+ | Pending | CKE section outdated (says 324 tests) |
| 42 | Hardcoded CKE path in CPE cke_invoker.py | Not fixed | Not portable |
| 43 | Version number cleanup (pyproject.toml vs git tags) | Not done | CKE says 1.0.0, tag says v0.5.0 |
| 44 | Git push (8+ commits ahead of origin) | Not done | Need push to GitHub |
| 45 | Stale feature branches cleanup | Partially done | Stashes dropped, branches remain |

---

## METRICS

| Metric | Session start | Now | Target |
|--------|-------------|-----|--------|
| Eval score (Cognitive Friday) | 24/100 | 95/100 | ≥90 ✅ |
| Eval score (golden set avg) | n/a | 79/100 | ≥80 |
| Tests | 363 | 584 | 600+ |
| Key facts per extraction | 0 | 15-34 | ≥10 ✅ |
| Slide PNGs per PPTX | 0 | 55 | ✅ |
| Fact verification rate | 0% | ~95% verified | ✅ |
| Council debates (session) | 0 | 7 completed | ✅ |
| Monthly LLM cost | unknown | ~$4/batch | <$20 ✅ |

---

## CRITICAL PATH FOR NEXT CHAT

```
1. Merge PDF multimodal (v0.6.0)
2. Tag validation against taxonomy
3. batch.py slide_image_paths fix
4. ───── CKE ready for batch ─────
5. Corp-by-os: trust_level protection
6. Corp-by-os: corp ingest-extractions
7. ───── Pipeline ready ─────
8. Batch extraction 30_Reference/ (25 clean files, quick test)
9. Batch extraction full MyWork (overnight)
10. Corp-by-os: vault ingest
11. RFP Agent: integration test
12. ───── System operational ─────
```

---

## SESSION ARTIFACTS (files produced this session)

| File | Purpose |
|------|---------|
| CKE_STATUS_FOR_CORP_BY_OS.md | Output format, frontmatter schema, gotchas |
| CKE_CROSS_ECOSYSTEM_COORDINATION.md | Dependency map, execution sequence |
| CORP_BYOS_RFP_AGENT_NEEDS.md | What RFP Agent needs from corp retrieve |
| CKE_TECHNICAL_BRIEF_FOR_CORP_BYOS.md | Full technical brief (5 questions answered) |
| CKE_ROADMAP_FULL.md | 86-feature tracker with status |
| COUNCIL_Q_EXTRACTION_BOTTLENECKS.md | PPTX rendering + frame sampling |
| COUNCIL_Q_TOKEN_TRANSCRIPT.md | Token budgets + transcript architecture |
| COUNCIL_Q_QUALITY_FRAMEWORK.md | Dual-signal, fact validation, eval |
| COUNCIL_Q_FILE_MANAGEMENT.md | CKE → vault pipeline |
| COUNCIL_Q_PDF_MULTIMODAL.md | PDF direct upload to Gemini Pro |
| eval_extraction.py | Updated eval script (doc-type aware) |

---

## HANDOFF NOTES FOR NEXT CHAT

### What works perfectly:
- PPTX: COM→PDF→Gemini Pro multimodal→slide PNGs (95/100)
- MP4: FFmpeg scene detect→Gemini Pro→transcript→session merge (94/100)
- Fact validation with verification_status
- Haiku enrichment (dual-signal)
- Tags, polarity, source_date, quality_score, extraction_cost
- Resume support (hash-based skip + --force)
- user_context from corp-by-os manifest

### Known gotchas (read CKE_TECHNICAL_BRIEF for full list):
- Gemini returns dicts instead of strings for people/products → normalize_string_list()
- COM PowerPoint: use WithWindow=False, not Visible=0
- PDF text-only pipeline being replaced by PDF multimodal (v0.6.0)
- batch.py lacks slide_image_paths support
- Corp-by-os imports CKE directly (not subprocess) — Python API matters

### Architecture rules (non-negotiable):
- CKE = pure extraction engine — no vault writes, no routing
- Corp-by-os = sole vault writer
- Forward slashes everywhere in databases/paths
- Never delete code without asking
- Feature branches → merge to main
- Tests after every change
- AI Council for architectural decisions
