# Training Data Extraction Report

**Date:** 2026-03-25
**Source:** 690 extraction notes from _outputs/

## Generated Fixtures

| Fixture | Count | Location |
|---------|-------|----------|
| Classifier training | 310 pairs | CKE/tests/fixtures/classifier_training.json |
| Tag golden set | 200 tags | CKE/tests/fixtures/tag_golden_set.json |
| Product normalization | 64 products | CKE/tests/fixtures/product_normalization.json |
| People filter | 444 entries | CKE/tests/fixtures/people_filter.json |
| Quality prediction | 690 entries | CKE/tests/fixtures/quality_prediction.json |
| Routing patterns | 383 entries | corp-by-os/tests/fixtures/routing_patterns.json |

## Batch Distribution

| Batch | Notes |
|-------|-------|
| _outputs | 687 |
| jlr_pilot | 3 |

## Doc Type Distribution

| doc_type | Count |
|----------|-------|
| general | 198 |
| training | 159 |
| unknown | 125 |
| product_doc | 72 |
| meeting | 40 |
| security | 31 |
| rfp_response | 31 |
| architecture | 26 |
| commercial | 8 |

## Quality by Extension

| Extension | Count | Avg Score | Min | Max |
|-----------|-------|-----------|-----|-----|
| .xlsx | 2 | 57 | 29 | 85 |
| .txt | 2 | 3 | 1 | 5 |
| .docx | 1 | 28 | 28 | 28 |

## Quality by Doc Type (top 10)

| doc_type | Count | Avg Score |
|----------|-------|-----------|
| meeting | 1 | 85 |
| general | 4 | 16 |

## People Classification Summary

| Type | Count |
|------|-------|
| real_person | 405 |
| organization | 17 |
| role | 13 |
| ambiguous | 9 |

## Top 20 Products

| Product | Count |
|---------|-------|
| Blue Yonder Platform | 288 |
| Blue Yonder Demand Planning | 207 |
| Azure | 189 |
| Blue Yonder Supply Planning | 119 |
| Blue Yonder WMS | 96 |
| Blue Yonder TMS | 77 |
| Blue Yonder Control Tower | 43 |
| Snowflake | 39 |
| Demand Planning | 24 |
| Platform Data Cloud | 23 |
| Blue Yonder Workforce Management | 17 |
| Blue Yonder OMS | 12 |
| Supply Planning | 12 |
| Platform | 12 |
| ML Studio | 12 |
| Blue Yonder Network Design | 10 |
| Control Tower | 9 |
| WMS | 8 |
| SAP | 8 |
| Supply Chain Planning Platform | 6 |

## Top 20 Topics

| Topic | Count |
|-------|-------|
| Supply Chain Planning | 332 |
| Demand Planning | 324 |
| API Integration | 320 |
| SaaS Architecture | 276 |
| Implementation | 261 |
| Machine Learning | 243 |
| Data Migration | 218 |
| Change Management | 213 |
| Workflow Orchestration | 210 |
| Performance Optimization | 192 |
| Security | 149 |
| Cloud Infrastructure | 147 |
| Replenishment | 105 |
| Pricing | 88 |
| Disaster Recovery | 83 |
| Customer Success | 74 |
| Incident Management | 68 |
| Competitive Analysis | 62 |
| WMS | 61 |
| SLA | 57 |
