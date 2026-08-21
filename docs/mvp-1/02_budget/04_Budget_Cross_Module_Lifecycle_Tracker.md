# Budget & Funding — Cross-Module Lifecycle Tracker

**Document ID:** BUDGET-MVP1-XMOD-TRACKER-1.0  
**Status:** Active tracking (not an implementation Done claim)  
**Date:** 6 August 2026  
**Authority:** `03_Budget_and_Funding_Cursor_Implementation_Pack.md` §2 → `BUDGET-MVP1-REQ-1.1` → Stitch  
**Companion audit canvas:** workspace canvases `budget-mvp1-requirements-audit.canvas.tsx`

## Goal

Track Budget lifecycle capabilities that span modules so provider work, consumer wiring, and end-to-end proof are never collapsed into a single “Implemented” flag. Use this file to complete remaining cross-module work without forgetting ownership.

## Canonical fixture (settled)

Use the **implementation / seed / Stitch** identity set as the working fixture:

| Role | Canonical code |
|---|---|
| Active Budget | `MOH-BUD-0001` |
| Lines | `MOH-BL-0001`, `MOH-BL-0002` |
| Seed bundle | `MOH_MVP_V1` (`kentender_budget/.../seeds/moh_mvp_v1_portfolio.py`) |

REQ §15 narrative codes (`MOH-BUD-2027-2028`, `MOH-BL-DHI-01`) are **aliases to reconcile in a future REQ doc revision** — do not invent a second seed pack.

## Completion levels (report only these)

| Level | Meaning |
|---|---|
| **Budget Core Complete** | Budget-owned screens, rules, and services work with provider tests |
| **Integration Ready** | Stable, tested contracts exist for downstream callers |
| **End-to-End Complete** | Demand / Planning / Tender / Award / Contract triggers are wired and proven |

**Current overall:** substantially complete at UI/core (approaching Level 1). **Not** Integration Ready or End-to-End Complete.

## Delivery statuses (mandatory vocabulary)

Do **not** use a single “Implemented” flag.

- Not started
- Provider in progress
- Provider complete — consumer pending
- Consumer wired — end-to-end proof pending
- End-to-end complete
- Future external integration
- Blocked
- Out of scope
- Closed (hygiene) — terminal status for BUD-SUP documentation/registry rows only

## Condition classes (track separately)

Every gap must be classified as exactly one of:

1. **Budget-owned capability missing** — provider service/rules absent in Budget
2. **Provider present — consumer not invoked** — Budget contract exists; trigger module has not wired/proven it
3. **Future external integration** — intentionally unavailable in MVP 1 (e.g. live IFMIS connector); internal contracts may still be required

Also never confuse:

- **Seeded display state** (e.g. “Partially converted” on a screen) with a working conversion workflow
- **Screen live** with business lifecycle complete
- **Internal ingestion contract** (`sync_expenditure` + snapshots + stale/unavailable handling) with **live finance-system connector** (future)

## Cross-module ownership model

A requirement must have both a **trigger owner** and a **Budget (provider) responsibility**.

| Business event | Trigger owner | Budget responsibility |
|---|---|---|
| Check funding while preparing a Demand | Demand | Validate funding without mutation |
| Approve a Demand | Demand | Atomically create the reservation |
| Move into Planning | Planning | Revalidate and inherit the same reservation |
| Create/configure a Tender | Tender | Carry and revalidate the same reservation |
| Financially clear an Award | Award | Revalidate funding against the proposed award |
| Activate a Contract | Contract Management | Convert reservation into commitment |
| Approve a contract variation | Contract Management | Adjust commitment after funding validation |
| Cancel or reduce downstream work | Owning downstream module | Release the authorised amount |
| Receive expenditure information | Finance integration | Store a read-only snapshot and detect exceptions |

## Required fields per cross-module requirement

| Field | Purpose |
|---|---|
| Requirement ID | Canonical traceability |
| Business event | What causes the operation |
| Trigger module | Module responsible for initiating it |
| Provider module | Module enforcing the business rules |
| Service contract | API or domain service invoked |
| Preconditions | Required state and authority |
| Idempotency key | Prevent duplicate processing |
| Expected mutation | Reservation, commitment, release, etc. |
| Failure result | Block, shortfall or exception behaviour |
| Audit event | Evidence recorded at runtime |
| Provider test | Budget service works independently |
| Consumer test | Calling module invokes it correctly |
| End-to-end test | Complete business transition works |
| Delivery status | Current completion classification |

## Runtime tracking target

Maintain a single **Funding Lifecycle shared read model** over authoritative DocTypes — **not** a new journal store / DocType. Authority remains:

- `Funding Reservation`
- `Procurement Commitment`
- `Expenditure Snapshot`
- `Budget Audit Event`

Canonical API: `list_funding_lifecycle(budget, filters=None)` (normalize → order → dedup → scope). Each normalized event should include when applicable:

- Correlation and idempotency key
- Budget and Budget Line
- Demand, Plan, Tender, Award, or Contract reference
- Event type
- Amount and currency
- Previous and resulting state
- Triggering module / source doctype
- Actor or system identity
- Timestamp
- Success, rejection, or exception
- Reason and supporting approval reference / `audit_ref`

Funding Activity, Downstream Usage, and Audit History screens are **purpose-specific projections** of this read model, not independently authored aggregators. **No BUD-SUP-005B** — convert/release/adjust/`sync_expenditure` land on their XMOD/service tickets and must emit `Budget Audit Event` so the same adapters pick them up.

---

## Tracker rows

Update **Delivery status** and evidence columns as work lands. Add rows if new cross-module events are discovered; do not delete historical rows — mark Out of scope / Blocked instead.

### XMOD-BUD-001 — Check funding (Demand prep)

| Field | Value |
|---|---|
| Requirement ID | XMOD-BUD-001 / BUD-FR-060–061 / BUD-AC-008 |
| Business event | Check funding while preparing a Demand |
| Trigger module | Demand |
| Provider module | Budget |
| Service contract | `check_funding` / `check_available_budget` |
| Preconditions | Active Budget + Active line; entity authority; amount & currency valid |
| Idempotency key | N/A (non-mutating) |
| Expected mutation | None |
| Failure result | Block with shortfall / next action |
| Audit event | Optional check audit (no balance change) |
| Provider test | `test_budget_check_reserve.py` |
| Consumer test | Demand readiness / workbench calls present — strengthen evidence |
| End-to-end test | Pending formal E2E ID |
| Delivery status | **Consumer wired — end-to-end proof pending** |
| Condition class | Provider present — consumer verification/evidence |

### XMOD-BUD-002 — Reserve on Demand approval

| Field | Value |
|---|---|
| Requirement ID | XMOD-BUD-002 / BUD-FR-062–065 / BUD-AC-009 |
| Business event | Approve a Demand |
| Trigger module | Demand |
| Provider module | Budget |
| Service contract | `reserve_funding` / `create_reservation` |
| Preconditions | Successful funding check; approved Demand; concurrency-safe |
| Idempotency key | Required unique operation key |
| Expected mutation | Create/retain Active reservation identity |
| Failure result | Insufficient funding blocks; no duplicate hold |
| Audit event | Reservation created |
| Provider test | `test_budget_check_reserve.py` (idempotency) |
| Consumer test | `demand_intake/api/lifecycle.py` invokes `create_reservation` |
| End-to-end test | Pending formal Demand→reservation E2E |
| Delivery status | **Consumer wired — end-to-end proof pending** |
| Condition class | Provider present — consumer proof incomplete |

### XMOD-BUD-003 — Release on cancel/reduce

| Field | Value |
|---|---|
| Requirement ID | XMOD-BUD-003 / BUD-FR-068–069 |
| Business event | Cancel or reduce downstream work |
| Trigger module | Owning downstream module (Demand today; others later) |
| Provider module | Budget |
| Service contract | Stable Budget `release_reservation` (today: DIA adapter) |
| Preconditions | Active / partially converted reservation; authorised reason |
| Idempotency key | Required for release operations |
| Expected mutation | Release authorised amount; update remaining reserved |
| Failure result | Reject release of non-releasable state |
| Audit event | Reservation released |
| Provider test | Partial — adapter path; promote to `budget_api` + contracts |
| Consumer test | Demand lifecycle cancel paths call `release_reservation` |
| End-to-end test | Pending |
| Delivery status | **Provider in progress** |
| Condition class | Budget-owned capability incomplete (stable public Budget API) + consumer coverage incomplete for non-Demand owners |

### XMOD-BUD-004 — Revalidate / inherit reservation (Planning)

| Field | Value |
|---|---|
| Requirement ID | XMOD-BUD-004 / BUD-FR-066 |
| Business event | Move into Planning |
| Trigger module | Planning |
| Provider module | Budget |
| Service contract | `revalidate_reservation` |
| Preconditions | Existing reservation for Demand; Active line still valid |
| Idempotency key | Revalidation operation key |
| Expected mutation | None (or metadata update); **no new reservation** |
| Failure result | Block planning progression if invalid |
| Audit event | Reservation revalidated |
| Provider test | Missing |
| Consumer test | Missing |
| End-to-end test | Missing |
| Delivery status | **Not started** |
| Condition class | Budget-owned capability missing |

### XMOD-BUD-005 — Revalidate / carry reservation (Tender)

| Field | Value |
|---|---|
| Requirement ID | XMOD-BUD-005 / BUD-FR-066 |
| Business event | Create/configure a Tender |
| Trigger module | Tender |
| Provider module | Budget |
| Service contract | `revalidate_reservation` |
| Preconditions | Inherited reservation identity |
| Idempotency key | Revalidation operation key |
| Expected mutation | None; no duplicate hold |
| Failure result | Block tender financial gate if invalid |
| Audit event | Reservation revalidated |
| Provider test | Missing |
| Consumer test | Missing |
| End-to-end test | Missing |
| Delivery status | **Not started** |
| Condition class | Budget-owned capability missing |

### XMOD-BUD-006 — Award financial clearance revalidation

| Field | Value |
|---|---|
| Requirement ID | XMOD-BUD-006 / BUD-FR-075 |
| Business event | Financially clear an Award |
| Trigger module | Award |
| Provider module | Budget |
| Service contract | `revalidate_reservation` (+ funding sufficiency vs proposed award) |
| Preconditions | Proposed award amounts; linked reservation(s) |
| Idempotency key | Award clearance key |
| Expected mutation | None until contract conversion |
| Failure result | Block award clearance on shortfall/invalid reservation |
| Audit event | Award funding revalidated |
| Provider test | Missing |
| Consumer test | Missing |
| End-to-end test | Missing |
| Delivery status | **Not started** |
| Condition class | Budget-owned capability missing |

### XMOD-BUD-007 — Convert reservation on Contract activation

| Field | Value |
|---|---|
| Requirement ID | XMOD-BUD-007 / BUD-FR-076–078 / BUD-AC-011 |
| Business event | Activate a Contract |
| Trigger module | Contract Management |
| Provider module | Budget |
| Service contract | `convert_reservation` |
| Preconditions | Authorised contract activation; reservation remaining ≥ convert amount |
| Idempotency key | Conversion operation key |
| Expected mutation | Create commitment(s); partial/full conversion; retain or release remainder explicitly |
| Failure result | Block activation; no silent oversubscription |
| Audit event | Reservation converted / Partially converted |
| Provider test | Missing (**seeded “Partially converted” is not proof**) |
| Consumer test | Missing |
| End-to-end test | Missing |
| Delivery status | **Not started** |
| Condition class | Budget-owned capability missing |

### XMOD-BUD-008 — Adjust commitment on contract variation

| Field | Value |
|---|---|
| Requirement ID | XMOD-BUD-008 / BUD-FR-079–080 / BUD-AC-014 |
| Business event | Approve a contract variation |
| Trigger module | Contract Management |
| Provider module | Budget |
| Service contract | `adjust_commitment` |
| Preconditions | Authorised variation; available funding for increases |
| Idempotency key | Variation adjustment key |
| Expected mutation | Increase/reduce commitment; release unused only when authorised |
| Failure result | Block unauthorised/manual edits and insufficient funding |
| Audit event | Commitment adjusted |
| Provider test | Missing |
| Consumer test | Missing |
| End-to-end test | Missing |
| Delivery status | **Not started** |
| Condition class | Budget-owned capability missing |

### XMOD-BUD-009 — Expenditure snapshot ingestion (internal)

| Field | Value |
|---|---|
| Requirement ID | XMOD-BUD-009 / BUD-FR-081–083 / BUD-AC-020 |
| Business event | Receive expenditure information |
| Trigger module | Finance integration (internal contract now; live connector later) |
| Provider module | Budget |
| Service contract | `sync_expenditure` (internal ingestion) |
| Preconditions | Snapshot payload with source timestamp; Budget Line identity |
| Idempotency key | Source event / snapshot id |
| Expected mutation | Store immutable snapshot; Matched / Stale / Exception / Unavailable — **never show unavailable as zero** |
| Failure result | Reconciliation exception; do not silently change Available |
| Audit event | Expenditure synced / exception |
| Provider test | Missing for ingestion contract (seeded snapshots ≠ sync capability) |
| Consumer test | N/A until connector; fixture-driven provider tests required in MVP 1 |
| End-to-end test | Fixture-driven only in MVP 1 |
| Delivery status | **Not started** (internal contract) |
| Condition class | Budget-owned capability missing for **internal** contract; live IFMIS connector = **Future external integration** |

### XMOD-BUD-010 — Close Budget

| Field | Value |
|---|---|
| Requirement ID | XMOD-BUD-010 / Impl pack `close_budget` |
| Business event | Close a Budget for an entity/period |
| Trigger module | Budget |
| Provider module | Budget |
| Service contract | `close_budget` |
| Preconditions | Governance rules for close (no open blockers as defined) |
| Idempotency key | Close operation key |
| Expected mutation | Status → Closed; lock further mutations |
| Failure result | Block close when disallowed |
| Audit event | Budget closed |
| Provider test | Missing (Closed seed row ≠ close workflow) |
| Consumer test | N/A (Budget-owned) |
| End-to-end test | Missing |
| Delivery status | **Not started** |
| Condition class | Budget-owned capability missing |

---

## Budget-owned support gaps (not always cross-module)

| ID | Item | Delivery status | Notes |
|---|---|---|---|
| BUD-SUP-001A | Budget + revision workflow Notification Log | Provider complete | In-app Alert via `emit_notification_log` + `budget_notification_service`; events: submitted/returned/reviewed/activated + revision submitted/returned/rejected/applied; evidence `kentender_budget.tests.test_budget_notifications` + `kentender_core.tests.test_notification_service` |
| BUD-SUP-001B | Insufficient-funding Notification Log on `reserve_funding` | Provider complete | Notify then throw; Demand owns call site; evidence `test_reserve_insufficient_emits_notification_idempotent` |
| BUD-SUP-001C | Reservation expiry notify | Provider complete — consumer pending | Notification adapter ready; Funding Reservation expiry date + scheduled domain event still missing (Budget-owned) |
| BUD-SUP-001D | Commitment increase notify | Provider complete — consumer pending | Adapter ready; Contract Management must invoke commitment adjust + notify hook |
| BUD-SUP-001E | Expenditure exception / stale source notify | Provider complete — consumer pending | Adapter ready; finance snapshot / internal `sync_expenditure` path pending (Budget + Finance integration) |
| BUD-SUP-001F | Untreated Required PVO notify | Provider complete — consumer pending | Adapter ready; wire when readiness/activation exposes a stable untreated-PVO event (Budget) |
| BUD-SUP-002 | Role-based browser evidence | Provider complete | Seeded PE-MOH/PE-MOE Budget roles; API matrix `test_budget_role_matrix` + Playwright `budget-funding-role-matrix.spec.ts`; `make ui-budget-role-gate`; Admin chrome smokes unchanged |
| BUD-SUP-003 | Parallel oversubscription protection evidence | Provider complete — consumer pending* | Idempotency tested; parallel stress matrix incomplete |
| BUD-SUP-004 | `kt_module_registry` routePrefixes + doc hygiene | Closed (hygiene) | Full `page_js` slugs in `module_registry.py` + `kt_module_registry.js`; MVP-1 taskLabels; guarded by `kentender_core.tests.test_module_registry` |
| BUD-SUP-005 | Funding Lifecycle shared read model as single truth | Provider complete | `list_funding_lifecycle` + Activity/Downstream/Audit projections; `reserve_funding` → `EVENT_RESERVED`; evidence `test_budget_funding_lifecycle` + activity/downstream/audit/check_reserve; **no 005B** — convert/release/adjust/sync continue on XMOD tickets |
| BUD-SUP-006 | Cursor ticket-doc-read-gate → MVP-1 pack | Closed (hygiene) | `.cursor/rules/kentender-ticket-doc-read-gate.mdc` Budget row → `docs/mvp-1/02_budget/` + `04_Budget_Cross_Module_Lifecycle_Tracker.md`; prompts/budget reference-only; guarded by `test_budget_ticket_doc_read_gate_targets_mvp1_pack` |
| BUD-SUP-007 | Teardown inventory §6 status refresh | Closed (hygiene) | `05_Budget_Teardown_Dependency_Inventory.md` §6 + header Current status; points at this tracker; guarded by `test_teardown_inventory_section_6_reflects_rebuild` |

BUD-SUP-001 (REQ §14) is split into **001A–001F**. Only 001A/001B are complete with automated evidence.

\*Reclassify BUD-SUP-003 when locking/concurrency stress tests land.

## Recommended next priorities

1. Lifecycle service spine (provider): `revalidate_reservation`, stable `release_reservation`, `convert_reservation`, `adjust_commitment`, internal `sync_expenditure`, `close_budget`
2. Wire each owning downstream module (consumer)
3. Add provider + consumer + end-to-end evidence per row above
4. Keep live finance connector tagged **Future external integration** while finishing internal snapshot contract

## Change log

| Date | Change |
|---|---|
| 2026-08-06 | Initial tracker from audit revision (provider/consumer/external separation) |
| 2026-08-06 | BUD-SUP-004 Closed (hygiene) — Budget routePrefixes synced + module registry guard |
| 2026-08-06 | BUD-SUP-006 Closed (hygiene) — ticket-doc-read-gate Budget pack retargeted to MVP-1 + guard |
| 2026-08-06 | BUD-SUP-007 Closed (hygiene) — teardown inventory §6 refreshed to post-rebuild status + guard |
| 2026-08-06 | BUD-SUP-001 split into 001A–F; 001A/001B Provider complete (`emit_notification_log` + budget facade + tests); 001C–F provider/consumer pending with owning modules |
| 2026-08-06 | BUD-SUP-002 Provider complete — role matrix UI+API evidence (`make ui-budget-role-gate`) |
| 2026-08-06 | BUD-SUP-005 Provider complete — shared `list_funding_lifecycle` read model; three screen projections; reserve→audit; no new journal DocType / no 005B |
