# Parameter & Rule Desk Drift Audit (screens 07–10)

**Date:** 2026-07-10  
**Scope:** Hydrated Desk iframe vs design `code.html` after Phase 3 API wiring regression.

## Root cause

| Layer | Status before remediation |
|---|---|
| Static HTML (`std_prod_impl/*.html`) | Match design (layout guards pass) |
| Desk hydration (`std_prod_engine.js`) | Replaced table rows with minimal templates |
| Navigation | Single Version Detail row routed only to Parameter Dictionary |
| QA gates | Static-only guards; no hydrated iframe contract tests |

## Gap matrix (pre-fix → post-fix)

| Screen | Check | Before | After |
|---|---|---|---|
| 03 Version Detail | Separate Parameter / Rule module rows | Missing (combined row) | Match |
| 07 Parameter Dictionary | 13-column table + action cluster | Partial (4 usable columns) | Match |
| 07 Parameter Dictionary | View Rules scoped filter | Missing (full catalogue) | Match |
| 08 Parameter Detail | Validation rules table chips | Partial (plain text) | Match |
| 09 Rule Dictionary | 11-column table + Open Rule actions | Partial (4 columns) | Match |
| 09 Rule Dictionary | Peer entry from Version Detail | Missing | Match |
| 10 Rule Detail | Breadcrumb back to Rule Dictionary | Missing | Match |

## Regression gates

- `test_be_07_read_api.py` — list field enrichment + `parameter_key` rule filter
- `std-schema-slice.spec.ts` — desk design column/action contracts + filtered View Rules
- `std-vertical-slice.spec.ts` — Version Detail peer navigation to both dictionaries
- Static layout guards unchanged (Phase 1 assets)
