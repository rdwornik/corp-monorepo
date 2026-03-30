# corp.schema -- Taxonomy, Models & Validation

## What this module does

Foundation layer (Layer 0) for the entire system. Defines the taxonomy
(products, topics, domains), Pydantic models for note frontmatter, path
resolution, and the frozen PipelineConfig used by all CLIs.

## Key files

| File | What it does |
|------|-------------|
| models.py | NoteFrontmatter (Pydantic), overlay models (Architecture, Security, etc.) |
| config.py | Centralized path resolution: ENV > paths.toml > defaults |
| pipeline_config.py | Frozen PipelineConfig with .production() / .sandbox() constructors |
| normalize.py | Taxonomy term normalization (products, topics, domains) |
| validate.py | Frontmatter validation against taxonomy.yaml |
| folder_names.py | MyWork folder name constants (PROJECTS, ARCHIVE, etc.) |
| products.py | Product name aliases and mappings |
| cli.py | `corp-meta` CLI: validate, normalize, report |

## Dependencies

- **Depends on:** pydantic, PyYAML (no corp.* imports)
- **Used by:** nearly every module in the system

## Data flow

taxonomy.yaml + schema.yaml -> NoteFrontmatter validation -> normalize -> validated note
