# Procurement Planning Workspace State Specifications

**Document ID:** `PLANNING-MVP1-UI01-REV-2.0`
**Change:** `PLN-CHG-015`
**Status:** Approved  
**Date:** 15 August 2026

## 1. Common contract

PLN-UI-01 is the Procurement Planner's PE/FY-scoped operational landing page. The server derives one state from authoritative Planning, Demand, Finance-task and professional-review evidence. A workspace load never creates or mutates a Plan, Version, item, task, reservation or decision, and no variant, queue or counter is persisted.

One eligible Procuring Entity is read-only. Multiple entities require deliberate selection and have no aggregate/default option. The selected financial year remains visible. Shared Desk chrome owns breadcrumbs and navigation.

Actionable rows have exactly one server-authorised action. Waiting rows are informational and expose no Finance or professional decision route. Search and the exact filters **All work**, **Approved Demands**, **Plan Items**, and **Returned work** affect returned work rows only; they never affect state selection.

## 2. State resolution

| Workspace state | UI | Governing condition | Primary action |
|---|---|---|---|
| `NO_PLAN` | PLN-UI-01A | No logical Plan for selected PE/FY | **Create annual plan** |
| `INITIAL_DRAFT_EMPTY` | PLN-UI-01B | Initial Draft Version 1, zero effective items | **Continue planning** |
| `APPROVED_WITH_ACTIONABLE_WORK` | PLN-UI-01 | Approved Plan, no Draft, eligible Approved Demand | **View approved plan** |
| `DRAFT_WITH_PLANNER_ACTION` | PLN-UI-01C | Editable Draft with any planner work | **Continue plan update** |
| `DRAFT_AWAITING_FINANCE` | PLN-UI-01D | Draft has no planner work and one or more open Finance tasks | **View plan update** |
| `VERSION_AWAITING_PROFESSIONAL_REVIEW` | PLN-UI-01E | In-review successor with an open professional task | **View approved plan** |
| `APPROVED_NO_WORK` | PLN-UI-01F | Approved Plan, no Draft, actionable work or waiting work | **View approved plan** |

Precedence is the order above except that submitted review is evaluated before Draft planner/Finance work. Returned Finance, returned professional review, incomplete items, planner-remediable validation and a Draft with no effective change all resolve to `DRAFT_WITH_PLANNER_ACTION`. Mixed planner and Finance work uses PLN-UI-01C and retains Finance as neutral waiting context.

## 3. Exact deterministic frames

All states use Mercy Kilonzo, Procurement Planner, and Ministry of Health. Common description: **Turn approved needs into funded, approved Plan Items ready for tendering.** Common helper: **These controls define the workspace view; they do not change record ownership.**

### PLN-UI-01 — Approved Plan with eligible Demand

- FY2027/28, `PLN-MOH-2027-001`, Approved Version 1, no Draft.
- One active item; KES 455,000,000; Finance 1 of 1; validation Ready.
- One actionable row for `DMD-MOH-2027-019`, **Digital health technical staff certification programme**, KES 80,000,000, **Ready for planning**, **Add to plan**.
- Waiting text: **Nothing is currently waiting on another reviewer.**

### PLN-UI-01A — No annual Plan

- FY2028/29, no logical Plan, with two Approved Demands eligible after registration.
- Heading: **No annual Procurement Plan**.
- Copy: **No Procurement Plan has been registered for Ministry of Health for FY 2028/29.**
- Supporting copy: **Create the annual Plan before adding the 2 Approved Demands ready for Planning.**
- Work text: **Create the annual Plan to begin Planning approved requirements.**
- No Demand rows or Plan/version/Finance/validation values.

### PLN-UI-01B — Initial Draft

- `PLN-MOH-2028-001`, Draft Version 1, zero items, KES 0, two eligible Demands, validation Not run.
- Supporting copy: **The annual Plan is ready for its first Approved Demands.**
- Exact Demand rows: `DMD-MOH-2028-001` at KES 48,000,000 and `DMD-MOH-2028-002` at KES 72,000,000, each with **Add to plan**.
- No Approved Version, Finance progress or submission action.

### PLN-UI-01C — Draft requiring planner action

- Approved Version 1 remains operational; Draft Version 2 totals KES 535,000,000, net KES 80,000,000 added.
- Planning 1 of 2; Finance 1 of 2; validation Needs attention.
- One `PPI-MOH-2027-022` row: **Planning incomplete**, **Complete item**, reason **Complete the procurement method and schedule before requesting Finance confirmation.**
- No-effective-change and returned states use this same workspace state with their highest-priority authorised row.

### PLN-UI-01D — Awaiting Finance

- Draft Version 2: two items, KES 535,000,000, net KES 80,000,000 added, Planning 2 of 2, Finance 1 of 2, validation Needs attention.
- Work text: **No planning work currently needs your action.**
- One four-column waiting row for `PPI-MOH-2027-022`: **Finance confirmation**, **Awaiting confirmation**, **Budget Officer**.
- No row action or Finance-task route.

### PLN-UI-01E — Awaiting professional review

- Version 2 In review, KES 535,000,000, net KES 80,000,000 added, Finance 2 of 2, validation Ready.
- Work text: **No planning work currently needs your action.**
- One four-column waiting row: **Professional review**, **Awaiting review**, **Head of Procurement**.
- No row action, task route, Approve or Return control.

### PLN-UI-01F — Approved Plan with no work

- Current Approved Version 2; two active items; KES 535,000,000; Finance 2 of 2; validation Ready; no Draft or eligible Demand.
- Work text: **No planning work currently needs your action.**
- Waiting text: **Nothing is currently waiting on another reviewer.**
- No Add Plan Item or Add to plan path.

## 4. Fixture and evidence boundary

PLN-UI-01A/B use resettable FY2028/29 records `DMD-MOH-2028-001/002`. Base and C–F reuse named `SCN-PLN-ADD-001` boundaries. Preparation is idempotent, removes only fixture-owned evidence, and never stores a screen-state flag. Finance/professional returns remain isolated fixtures.

The approved HTML files control visual composition after applying the exact ledger content and the no-breadcrumb correction. PLN-CHG-015 is complete only when all seven projections reconcile with their owning builder, Finance, review and Approved-plan services and focused service/browser evidence passes.

## 5. Final route, FY and audit contract

| State | Server action | Destination / effect | Audit evidence |
|---|---|---|---|
| PLN-UI-03/05 Draft or Returned | Continue update | `/app/procurement-plan-builder?plan=<plan>` | Version concurrency and mutation history |
| PLN-UI-05B empty successor | Cancel update | terminal Cancelled Version, then `/app/procurement-plan-approved?plan=<plan>` | Plan Decision with actor, time, fixed reason and idempotency key |
| PLN-UI-09 Approved Plan | Back | `/app/procurement-planning` | no mutation |
| PLN-UI-09 Approved Plan | Add Plan Item | approved workspace demand dialog, only when authorized | successor Version and allocation audit |
| PLN-UI-09 Approved row | View | `/app/procurement-plan-approved?plan=<plan>&plan_item=<item>` | no mutation; approved workspace remains authoritative |
| PLN-UI-09 eligible row | Propose removal | governed removal dialog/command | Plan Decision and successor mutation evidence |

Actions not present in the server action map do not render or execute. Approved export is absent from the MVP-1 route contract. Financial-year context resolves in the order selected, saved default, then deterministic legacy/default; Demand dates report `inferred_from_demand_date` and explicit missing, outside-period or mismatch issue codes without cross-FY merging.
