# Requirements Compliance — Implementation Report

## Goal

Deliver a bidder-facing **Requirements Compliance** section that digitizes ITT 18.2(c) item-by-item responses: published requirements drive a grouped workspace + response drawer + review screen; statuses/progress are derived; evidence is linked; addenda and lots behave per pack; incomplete required responses block checklist/submission readiness — without an evaluation or DMS subsystem.

## Scope delivered

| Area | Status |
|---|---|
| Lean fixtures (standard / conditional / amended) + template materialization | Done |
| Modes, applicability, progress denominator, plain-language summaries | Done |
| Website workspace + drawer (Stitch 01/02) on dedicated routes | Done |
| Review screen + Complete Section (no seal) (Stitch 03) | Done |
| Checklist roll-up + Resolve deep-link for Needs Attention | Done |
| Layout guard + Makefile gates + Playwright smoke | Done |

## Architecture

- Domain: `kentender_procurement/tender_configurations/services/requirement_matrix.py` (evolved A4; persistence key `responses.requirements_compliance`)
- Seed: `tender_configurations/seed/lean_requirements_compliance.py`
- Materialize: `materialize_requirements_compliance()` in `electronic_std_template.py` (default fixture `standard` when PE rows absent)
- Website: CBQ/FoT shell + `requirement_matrix_web.css/js` + `requirements_compliance_review.js`
- Routes (before catch-all section):
  - `/tenders/<ref>/sections/requirements_compliance`
  - `/tenders/<ref>/sections/requirements_compliance/review`

## Fixtures

| Fixture | Behaviour |
|---|---|
| standard | Required + optional + informational across groups; combined/yes-no/ack/number renderers |
| conditional | Lot-scoped + named condition rows; technical-alternative permitted flag |
| amended | Addendum-changed row → Needs Attention until resave; withdrawn excluded from progress |

## Evidence commands

```bash
bench --site kentender.midas.com clear-cache
cd apps/kentender_v1 && make bw-requirements-compliance-domain-gate
cd apps/kentender_v1 && make ui-bidder-requirements-compliance-gate
```

**Gate evidence (this delivery):** `bw-requirements-compliance-domain-gate` OK (9 domain + 4 layout-guard tests); `ui-bidder-requirements-compliance-gate` OK (1 Playwright smoke).

Manual spot-check: `http://127.0.0.1:8000/tenders/<ref>/sections/requirements_compliance` and `/review` (seed via `publish_lean_requirements_compliance_for_tests`).

## Reused components

- A4 matrix get/save/drawer APIs and Website drawer chrome
- Evidence register link/replace/remove (no file copy)
- Bidder portal nav + workspace sidebar
- Lean NSSF publish path for Playwright (`publish_e1_nssf_lean_for_tests`)

## Explicitly deferred

- Full PE-side requirement authoring UI (consume published config only)
- Evaluator scoring / responsiveness decisions
- New DMS / file-copy reuse
- General-purpose expression engine (named conditions only)
- NSSF as canonical fixture (calibration-only; lean fixtures are PE-neutral)

## Gaps / follow-ups

- Richer drawer controls for `%` / date / period / repeating_table beyond fixture-critical paths
- Lot-selection live wiring in UI when selected lots change mid-bid (domain supports scope; full lot UI is shared)
- Published snapshots created before materialize land with empty requirements until republish
