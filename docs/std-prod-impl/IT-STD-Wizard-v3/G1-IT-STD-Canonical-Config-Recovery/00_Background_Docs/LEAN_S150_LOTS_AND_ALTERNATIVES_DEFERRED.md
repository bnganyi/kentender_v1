# Lean S150 — Lots & Alternatives (DEFERRED)

| Item | Value |
|---|---|
| Status | **Deferred** (not implemented) |
| Binding pack | `05_Cursor_Section_by_Section_Electronic_IT_STD_Implementation_Pack_v1.md` — Prompt S150 |
| Blueprint | `02. Canonical_PPRA_IT_STD_Bidder_Submission_Section_Blueprint_v1.md` §12 |
| Date | 2026-07-24 |

## Goal

Record that **Lots & Alternatives** (`lot_and_alternative_selection`) is intentionally not implemented in this programme slice.

## Deferral reasons

1. No current calibration tender (including NSSF) requires bidder lot selection or permitted alternatives.
2. No approved Stitch design exists for this section under `docs/bidder-workspace/`.

## Required behaviour while deferred

- Section remains **conditional** via template applicability `lots_or_alternatives_configured`.
- NSSF and other single-lot / alternatives-prohibited tenders **must omit** this section from checklist and progress calculation.
- Do **not** add `/tenders/<ref>/lots`, a generic lots placeholder page, domain services, S150 prove-list tests, or `LEAN_S150_LOTS_AND_ALTERNATIVES_REPORT.md`.

## Resume when

1. An actual tender configuration requires lot selection and/or alternatives; and
2. An approved Stitch (or equivalent approved shared) design for the section is available.

## Explicit non-scope of this note

No domain logic, routes, UI, tests, or implementation report for S150.

**Proceed to S300** (Confidential Business Questionnaire) as the next applicable always-on section.
