# Decision Closure and Residual Evidence Gaps

**Document ID:** KENTENDER-ROIDA-08-1.1  
**Version:** 1.1  
**Date:** 11 August 2026  
**Status:** Product decisions closed; residual implementation evidence retained  
**Authority:** Approved CMOM v1.0 and Correction Control and Backlog v1.0

This file supersedes ROIDA-08-1.0. The audit originally recorded ten open decisions because the operating model had not yet been approved. The product owner subsequently approved the operating model and correction backlog. Cursor shall not reopen the decisions below.

## OD-01 — Operating-model authority

**Closed:** CMOM v1.0 and Correction Control and Backlog v1.0 are approved. SWA v1.1 is an accepted correction audit subordinate to them.

## OD-02 — Finance sign-off timing

**Closed:** One Finance/Budget Officer confirmation occurs after the Procurement Planner completes the proposed Plan Item and before Head-of-Procurement review/approval.

The existing Demand-stage Budget Confirmation must be relocated or refactored, not duplicated. Demand may carry proposed funding context, but HoD approval makes it Planning Ready without completing Finance approval.

**Residual evidence needed before implementation:** determine the safest reuse/migration of `Demand Funding Allocation`, reservation logic and audit history. Requirements must decide the final persistence contract before Cursor changes schema or services.

## OD-03 — PLN-UI-08 statutory coverage

**Closed:** Keep only a concrete read-only **Preference and reservation coverage** projection derived from actual Plan Item decisions.

Remove generic statutory-treatment inputs, statutory rationale and planned-treatment value. User-facing copy shall not use the broad `statutory coverage` label.

## OD-04 — Unauthorised task routes

**Closed:** An unauthorised task route must be denied by its server-side loader/API. A neutral read-only record view, where authorised, uses a separate route and is not the approval form with disabled controls.

**Residual evidence needed:** role-by-role direct-route and API tests for Budget, Strategy and Planning surfaces.

## OD-05 — Reservation-to-commitment conversion

**Closed:** Keep the Commitment schema and lineage contract. Defer the live conversion action until the Tender/Contract lifecycle requires it. Do not create a manual placeholder UI.

This is not a blocker for Strategy-to-Planning correction. It becomes a mandatory gate before Contract commitment implementation.

## OD-06 — Returned Demand story

**Closed:** The original submitted/returned value is KES 95,000,000; the corrected and resubmitted value is KES 80,000,000.

**Residual evidence needed:** the next seed validation must prove KES 80,000,000 as the current value and retain intelligible audit/history evidence of the KES 95,000,000 return.

## OD-07 — Annual departmental-plan certification

**Closed:** Deferred from MVP 1. Do not reintroduce PLN-UI-07 or a contribution editor. Any future certification must pass the concept-admission gate as one annual batch-certification journey.

## OD-08 — PVO rules engine and Strategy Performance dashboard

**Closed:** Deferred from MVP 1. Quarantine existing surfaces from ordinary MVP navigation and prevent new dependencies pending later disposition.

Strategy Value Commitments remain in scope and must not be removed with the generic PVO applicability engine.

## OD-09 — Dual Strategy seeds

**Closed:** `kentender_mvp_v1_strategy` is the authoritative canonical demonstration seed. The works-master hierarchy is an explicit opt-in regression fixture and shall not run through the canonical demonstration orchestrator.

**Residual evidence needed:** confirm and correct the orchestrator call graph during the seed wave.

## OD-10 — Version-control and rollback baseline

**Closed as a product decision; execution pending:** no application correction may begin without a verified backup, reviewed tracked-file manifest, source snapshot, baseline commit and restore procedure.

Wave 0A discovers and proposes the boundary. Wave 0B requires separate product-owner approval before backup execution or Git-state changes.

## Residual implementation investigations

These are evidence tasks, not open product-policy choices:

| ID | Evidence task | Required wave |
|---|---|---|
| EG-01 | Verify Strategy list scoping for real zero/multi-PE users | Wave 1 |
| EG-02 | Verify task-route denial for every role and module | Wave 1 |
| EG-03 | Determine live versus fixture use of `strategy_alignment_shell.js` `FIXTURE_PLAN` | Wave 2 |
| EG-04 | Count and inspect non-empty Budget/Demand treatment records before migration/removal | Waves 3–4 |
| EG-05 | Determine safe persistence/migration for post-Plan Finance confirmation | Requirements, then Waves 3–5 |
| EG-06 | Count Departmental Submission rows and downstream references | Wave 5 |
| EG-07 | Verify the 95m-to-80m seed history in a controlled test site | Wave 6 |
| EG-08 | Verify works-master seed is removed from the canonical orchestrator | Wave 6 |
| EG-09 | Confirm Tender handoff snapshot remains bound to the Approved Plan Version during revision | Wave 5/7 |
| EG-10 | Establish repository and rollback baseline | Wave 0A/0B |

## Explicitly settled dispositions

The following shall not be reopened during implementation:

- Departmental Submission, PLN-UI-07 contribution workflow and its hard gate → **Remove**;
- routine planning-stage HoD sign-off → **Remove**;
- Budget Line Value Treatment and Demand Value Treatment → **Remove**;
- Budget PE-MOH, Administrator and sorted-first fallbacks → **Correct**;
- Plan Value Commitment terminology → **Correct to Strategy Value Commitment**;
- one Demand to one Plan Item formation → **Keep**;
- explicit aggregation only when another source is deliberately added → **Keep**;
- Approved-plan Draft successor → **Keep**;
- Finance confirmation after Plan Item completion → **Required**;
- unauthorised task forms → **Deny; use separate neutral detail**; and
- annual certification and generic PVO engine → **Defer**.
