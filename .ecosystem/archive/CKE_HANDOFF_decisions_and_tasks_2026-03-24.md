# CKE Handoff — Context Update + Implementation Tasks

## What happened since your last session

CKE v0.4.0 shipped successfully (500 tests). Batch extraction ran on ~500 files from local MyWork. 492 notes extracted. Pipeline works end-to-end.

BUT: Two AI Council decisions from today (2026-03-22) require CKE changes before the next batch extraction.

## Council Decision #7: Vault Navigation (binding, 2026-03-22)

**What was decided:** Obsidian vault will use hierarchical tags for multi-dimensional navigation. Every extracted note must have a `tags:` field in frontmatter. Tags are auto-generated from existing frontmatter fields.

**What CKE must do:**

Every note CKE produces must have a `tags:` array in YAML frontmatter. Tags are generated from `products`, `topics`, `domains`, and `client` fields that CKE already extracts.

**Tag format:** hierarchical, lowercase, hyphens instead of spaces.

**Mapping rules:**
```yaml
# From products: ["WMS", "Demand Planning"]
# Generate: product/wms, product/demand-planning

# From topics: ["SaaS Architecture", "API Integration"]  
# Generate: topic/saas-architecture, topic/api-integration

# From domains: ["Platform & Architecture", "Security"]
# Generate: domain/platform-architecture, domain/security

# From client: "SGDBF"
# Generate: client/sgdbf

# From doc_type: "training"
# Generate: type/training

# From source_type: "rfp"
# Generate: source/rfp
```

**Example complete frontmatter with tags:**
```yaml
---
title: "Blue Yonder WMS Architecture Overview"
type: "presentation"
products: ["WMS"]
topics: ["SaaS Architecture", "API Integration", "Disaster Recovery"]
domains: ["Platform & Architecture", "Security"]
client: "SGDBF"
doc_type: "product_doc"
source_type: "documentation"
tags:
  - product/wms
  - topic/saas-architecture
  - topic/api-integration
  - topic/disaster-recovery
  - domain/platform-architecture
  - domain/security
  - client/sgdbf
  - type/product-doc
  - source/documentation
schema_version: 2
source_tool: "knowledge-extractor"
# ... rest of frontmatter
---
```

**Normalization rules:**
- Lowercase everything
- Replace spaces with hyphens
- Replace `&` with empty (e.g., "Platform & Architecture" -> "platform-architecture")
- Replace underscores with hyphens
- Strip special characters except hyphens and slashes
- Deduplicate tags

**Where to implement:** In `post_process.py` or `synthesize.py` — wherever frontmatter is assembled before writing the .md file. The tags should be generated AFTER normalization by corp-os-meta (so product names are canonical).

**Tests needed:**
- Tags generated from products, topics, domains, client
- Tags are lowercase with hyphens
- Empty fields produce no tags for that prefix
- No duplicate tags
- Multi-value fields produce multiple tags

---

## Council Decision #8: Model Tiering + Gemini Capabilities (binding, 2026-03-22)

Two parts to this decision:

### Part A: Updated Model Tiering

Budget is NOT a constraint. Quality is the only metric.

**New tiering (replaces old Decision #3):**

| When | Model | Why |
|------|-------|-----|
| PPTX, image-heavy PDF, video | Gemini 3.1 Pro | Best multimodal quality |
| Text-heavy DOCX, XLSX, CSV | Gemini 3 Flash | Good enough, faster |
| Validation failure / escalation | Claude Sonnet 4.6 | Strongest reasoning |
| Files <5KB | Free (metadata only) | No LLM needed |

**Policy-based auto-routing:** CKE should auto-select model based on file type, not require `--model` flag. The `--model` flag (already implemented) stays as manual override.

**Implementation:**
```python
def select_model(file_path, file_size, has_images=False):
    ext = file_path.suffix.lower()
    
    if file_size < 5000:
        return "free"  # Tier 1, metadata only
    
    if ext in [".pptx", ".mp4", ".mkv", ".avi", ".mov", ".wav"]:
        return "gemini-3.1-pro-preview"  # Always Pro for multimodal
    
    if ext == ".pdf" and has_images:
        return "gemini-3.1-pro-preview"  # Pro for visual PDFs
    
    if ext == ".pdf":
        return "gemini-3-flash-preview"  # Flash for text PDFs
    
    # DOCX, XLSX, CSV, etc
    return "gemini-3-flash-preview"  # Flash default
```

The `--model` flag overrides this when specified.

**Add provenance metadata to frontmatter:**
```yaml
model_name: "gemini-3.1-pro-preview"
model_version: "2026-03"
routing_reason: "pptx_multimodal"
prompt_version: "deep_v2"
```

### Part B: Gemini API Capabilities (future sprints, not now)

These are PLANNED but NOT for this sprint:
- **Structured Outputs** (Sprint 2): JSON mode instead of markdown parsing
- **Document Understanding** (Sprint 2): Binary PDF upload instead of text extraction
- **Thinking mode** (Sprint 2): For complex docs only
- **Function Calling** (Sprint 2+): taxonomy lookup during extraction

**DO NOT implement Part B now.** Only implement Part A (auto-routing + provenance).

---

## File naming convention (Council Decision #7)

CKE should normalize output filenames:

**Current:** Whatever the source filename is (e.g., `SGDBF-Architecural requirements.md`)
**New:** `{date}_{source_filename_normalized}_{hash4}.md`

**Example:** `2026-03-22_sgdbf_architectural_requirements_a7b2.md`

**Rules:**
- Date from `extracted_at` (YYYY-MM-DD)
- Source filename: lowercase, underscores for spaces, strip special chars
- 4-char hash from source_hash (first 4 chars) for collision safety
- Truncate filename to 64 chars before hash

**Where to implement:** In `synthesize.py` where the output .md filename is determined.

---

## Summary: What to implement NOW

### Task 1: Tags generation (Decision #7)
- Add `tags:` field to frontmatter
- Auto-generate from products, topics, domains, client, doc_type, source_type
- Hierarchical format: `prefix/value`
- Tests

### Task 2: Policy-based auto-routing (Decision #8a)
- Auto-select model by file type (.pptx -> Pro, .docx -> Flash)
- `--model` flag still overrides
- Tests

### Task 3: Provenance metadata (Decision #8a)
- Add model_name, model_version, routing_reason, prompt_version to frontmatter
- Tests

### Task 4: File naming convention (Decision #7)
- Normalize output filenames: `{date}_{name}_{hash4}.md`
- Tests

### Order: 1 -> 2 -> 3 -> 4, or all on one feature branch.

Run all tests after. Tag as v0.5.0 when done.
