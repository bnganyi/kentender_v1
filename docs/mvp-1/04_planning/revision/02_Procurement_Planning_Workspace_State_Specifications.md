# Procurement Planning Workspace State Specifications

**Document ID:** `PLANNING-MVP1-UI01-REV-1.0`  
**Change:** `PLN-CHG-001`  
**Status:** Approved  
**Date:** 14 August 2026

## 1. Common contract

PLN-UI-01 is the Procurement Planner's PE/FY-scoped operational landing page. It contains one current-Plan panel, one server-derived primary action, **Work requiring action**, and **Waiting on others**. It does not expose Finance or professional-review decision controls and does not persist workspace tasks or counters.

One eligible Procuring Entity is visible read-only. Multiple eligible entities require deliberate selection and provide no aggregate or default option. The financial year remains visibly selected. Every action is omitted unless its target service will authorise the same actor, PE, OU and record state.

The work filter options are exactly **All work**, **Approved Demands**, **Plan Items**, and **Returned work**. The search placeholder is **Search work**. Both work sections use the columns **Work item**, **Type**, **Organisation Unit**, **Amount**, **Why it appears**, **Status**, and **Action**.

Priority is deterministic: returned work; blocking or stale work; incomplete or outstanding work; eligible Approved Demands. If one record meets more than one condition, only its highest-priority reason appears; secondary issues remain on record detail.

## 2. Action vocabulary

| Condition | Status | Action | Destination |
|---|---|---|---|
| Approved, Planning Ready Demand | Ready for planning | **Add to plan** | Owning Plan surface with PLN-UI-04 open and the Demand freshly revalidated and selected |
| Incomplete Proposed Plan Item | Incomplete | **Complete item** | PLN-UI-06 Plan Item editor |
| Finance return | Returned by Finance | **Correct item** | PLN-UI-06 Plan Item editor |
| Blocking or stale validation | Blocked / Stale | **Resolve issues** | PLN-UI-06 Plan Item editor |
| Returned Plan Version | Returned by Head of Procurement | **Address return** | PLN-UI-05 Draft update |
| Draft update needing planner action | Needs attention | **Continue update** | PLN-UI-05 Draft update |
| Draft successor with no effective changes | No changes | **Cancel update** | PLN-UI-05, where cancellation is confirmed and authorised |
| Awaiting Finance | Awaiting Finance confirmation | **View item** | Neutral Plan Item detail; never PLN-UI-07 |
| Awaiting professional review | Awaiting Head-of-Procurement review | **View update** | Neutral submitted-update detail; never another actor's decision controls |

## 3. Deterministic states

All states use Mercy Kilonzo, Procurement Planner, Ministry of Health, unless expressly stated otherwise. Common header description: **Turn approved needs into funded, approved Plan Items ready for tendering.** Common helper: **These controls define the workspace view; they do not change record ownership.**

### PLN-UI-01 — Approved Plan with one Approved Demand

- FY 2027/28; `PLN-MOH-2027-001`, Open; Approved `PLN-MOH-2027-001-V1`; no Draft successor.
- One active item; approved value KES 455,000,000; Finance confirmed 1 of 1; validation Ready.
- Primary action: **View approved plan**.
- Work contains `DMD-MOH-2027-019`, **Digital health technical staff certification programme**, Approved Demand, Human Resources Management and Development, KES 80,000,000, reason **HoD-approved Demand is ready to add to the FY 2027/28 Plan.**, status **Ready for planning**, action **Add to plan**.
- Waiting empty text: **Nothing is currently waiting on another reviewer.**

### PLN-UI-01A — No annual Plan

- FY 2028/29; no logical Plan and no eligible Approved Demand.
- Primary action: **Create annual plan**.
- Current Plan empty text: **No annual Plan exists for Ministry of Health FY 2028/29.** Supporting text: **Create the annual Plan before adding approved Demands.**
- Work empty text: **No approved Demands are ready for planning in FY 2028/29.**
- Waiting empty text: **Nothing is currently waiting on another reviewer.**

### PLN-UI-01B — Initial Draft Plan

- FY 2029/30; `PLN-MOH-UI-DRAFT-001`, **Ministry of Health Annual Procurement Plan 2029/30**, Open; Draft Version 1; no Approved Version.
- Zero items; Draft value KES 0; Finance confirmed 0 of 0; validation Not run.
- Supporting text: **This initial Plan is in preparation and has not been approved.**
- Primary action: **Continue planning**.
- Work empty text: **No work currently requires your action.** Waiting uses the common empty text.

### PLN-UI-01C — Approved Plan with incomplete Draft addition

- FY 2027/28; Approved Version 1 remains current; Draft Version 2 is open.
- Approved: one item, KES 455,000,000. Draft: two items, KES 535,000,000. Finance confirmed 1 of 2. Validation Needs attention.
- Supporting text: **Draft Version 2 is being prepared; Approved Version 1 remains current.**
- Primary action: **Continue plan update**.
- Work contains `PPI-MOH-2027-022`, **Digital health technical staff certification programme**, Plan Item, Human Resources Management and Development, KES 80,000,000, reason **Required planning details are incomplete.**, status **Incomplete**, action **Complete item**.
- Waiting uses the common empty text.

### PLN-UI-01C-NC — No effective Draft changes

- `SCN-PLN-REMOVE-001` after the only Draft addition is removed. Approved Version 1 and Draft Version 2 each project KES 455,000,000; no effective Draft change remains.
- Current Plan supporting text: **No changes remain in Draft Version 2.** Primary action: **Continue plan update**.
- Work contains one Plan update row with reason **No effective changes remain in Draft Version 2.**, status **No changes**, action **Cancel update**. Submission is absent.
- Waiting uses the common empty text.

### PLN-UI-01D — Awaiting Finance confirmation

- Approved Version 1 remains current; Draft Version 2 has two items and KES 535,000,000. Finance confirmed 1 of 2; validation Ready.
- Primary action: **Continue plan update**. Work empty text: **No work currently requires your action.**
- Waiting contains `PPI-MOH-2027-022`, Plan Item, KES 80,000,000, reason **Finance confirmation has been requested and is awaiting the Budget Officer.**, status **Awaiting Finance confirmation**, action **View item**.

### PLN-UI-01E — Awaiting Head-of-Procurement review

- Approved Version 1 remains current; Draft Version 2 is In review. Draft value KES 535,000,000; Finance confirmed 2 of 2; validation Ready.
- Supporting text: **Draft Version 2 has been submitted for professional review; Approved Version 1 remains current.**
- Primary action: **View approved plan**. Work uses the common no-action text.
- Waiting contains the Plan update, KES 535,000,000, reason **Submitted plan update is awaiting Head-of-Procurement review.**, status **Awaiting Head-of-Procurement review**, action **View update**.

### PLN-UI-01F — Approved Plan with no current work

- Canonical base FY 2027/28: Approved Version 1, no Draft successor, one active item, KES 455,000,000, Finance confirmed 1 of 1, validation Ready.
- Primary action: **View approved plan**.
- Work empty text: **No work currently requires your action.** Waiting uses the common empty text.

## 4. Fixture boundary

PLN-UI-01/F use the canonical base; PLN-UI-01 uses `SCN-PLN-ADD-001` after HoD reapproval; C/D/E use named stop points in that scenario; C-NC uses `SCN-PLN-REMOVE-001`; B uses the existing Playwright-owned empty Draft; A uses an unoccupied FY after canonical reset. Finance and professional returns use isolated transactional/UI fixtures. No permanent Demand, Plan Item, reservation, decision or workspace-task record is added for these states.

## 5. Approval evidence boundary

The deterministic state contracts above are approved implementation inputs. Generated Stitch canvases or screenshots remain manual visual evidence and must be attached before `PLN-CHG-001` is marked fully implemented; their absence does not authorise alternative content or labels.
