# corp_os_meta

Shared metadata schema and taxonomy for the corp-by-os agent ecosystem. This package defines the frontmatter contract that all extraction tools (knowledge-extractor, project-extractor, etc.) must follow when producing Obsidian vault notes. It provides Pydantic models for validation, a canonical taxonomy with alias resolution, product key resolution, structured extraction overlays, and a CLI for vault health management.

## Features

- **Schema contract** — `NoteFrontmatter` Pydantic model with 30+ fields across knowledge dimensions, temporal validity, content routing, and deep extraction
- **Taxonomy normalization** — alias resolution with fuzzy-tolerant preprocessing (casefold, strip plurals, normalize `&`→`and`)
- **Validation + quarantine routing** — notes that fail schema validation are routed to `_quarantine/`
- **Product resolution** — canonical product key lookup with fuzzy matching (>0.85 similarity) and source reliability scoring
- **Structured overlays** — type-specific extraction schemas for architecture, security, commercial, RFP, and meeting documents
- **LLM JSON parsing** — robust 4-strategy parser for malformed LLM output (fence stripping, trailing commas, regex extraction, json-repair)
- **CLI** — validate, normalize, and report on vault health

## Installation

```bash
pip install -e C:\Users\1028120\Documents\Scripts\corp-os-meta
```

Dependencies: pydantic, pyyaml, click, rich, json-repair

## Usage

### Python API

```python
from corp_os_meta import NoteFrontmatter, normalize_frontmatter, validate_frontmatter

# Build frontmatter dict from extraction
data = {"title": "DR Overview", "date": "2026-01-15", "type": "presentation",
        "source_tool": "cke", "source_file": "dr_overview.pptx", "topics": ["DR"]}

# Normalize taxonomy terms (DR → Disaster Recovery)
data, changes, unknown = normalize_frontmatter(data)

# Validate against schema — routes to vault or _quarantine/
result, note, issues = validate_frontmatter(data)
```

### CLI

```bash
# Validate a single note or entire vault
corp-meta validate path/to/note.md
corp-meta validate path/to/vault/ --recursive --strict

# Normalize taxonomy terms in-place
corp-meta normalize path/to/note.md --in-place

# Report on vault health
corp-meta report path/to/vault/
```

## Architecture

```
corp-os-meta (this package)
    ↑ imported by
corp-knowledge-extractor    — video/presentation extraction
corp-project-extractor      — file system scanning
corp-meeting-extractor      — meeting notes (future)
```

Key modules:
- `models.py` — Pydantic models defining the frontmatter contract (schema v2)
- `normalize.py` — taxonomy loading, alias maps, term normalization
- `validate.py` — schema validation and quarantine routing
- `products.py` — product key resolution and source tier classification
- `overlays.py` — structured extraction overlay schemas
- `utils.py` — LLM JSON parsing utilities
- `cli.py` — Click CLI for vault management

## Testing

```bash
pytest tests/ -v
```

87 tests covering models, normalization, validation, preprocessing, products, utilities, deep extraction fields, and dimension fields.

## Related repos

- **corp-by-os** — orchestrator
- **corp-os-meta** — shared schemas (this repo)
- **corp-knowledge-extractor** — extraction engine
- **corp-rfp-agent** — RFP automation
- **ai-council** — multi-model debate

## License

Internal use only — Blue Yonder Pre-Sales Engineering
