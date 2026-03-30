# corp.retrieve -- Knowledge Retrieval

## What this module does

Unified retrieval engine for all query workflows. Builds FTS5 queries with
BM25 ranking, applies metadata filters, loads full note content from vault,
and returns ranked results with citations.

## Key files

| File | What it does |
|------|-------------|
| engine.py | FTS5 query building, BM25 ranking, coverage assessment |
| prep.py | Client context preparation for meetings/calls |
| rfp.py | RFP-specific retrieval with product focus |

## Dependencies

- **Depends on:** corp.schema, corp.ingest (for index path)
- **Used by:** corp.cli.retrieve, corp.rfp

## Data flow

Query string -> FTS5 BM25 search on index.db -> metadata filter -> vault note loading -> ranked results
