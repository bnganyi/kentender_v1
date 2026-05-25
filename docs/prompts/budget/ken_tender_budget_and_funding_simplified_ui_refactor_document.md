# KenTender Budget and Funding Simplified UI Refactor Document

This document defines a simplified UI refactor for the Budget and Funding module. The goal is to make Budget and Funding consistent with the improved Strategy Management pattern while keeping the module appropriately small, clear, and workflow-driven.

Budget and Funding should not feel like a financial dashboard, procurement reservation engine, or accounting console. It should be a simple workbench for creating annual budgets, allocating money to strategy-linked programs/sub-programs, reviewing allocation completeness, and approving or locking the budget when ready.

---

# 1. Current Assessment

The latest Budget and Funding screens are improved compared to the earlier version, but the module is still overly complicated for its purpose.

The current implementation has four main issues:

1. **The workflow is not immediately clear.**
   - The user sees status filters, budget list, budget summary, allocation table, manage allocation button, approved/locked message, and allocation details across multiple pages.
   - It is not obvious whether the next step is to edit the budget, manage allocations, approve, submit, or review downstream usage.

2. **The workbench is partially aligned with Strategy, but not fully.**
   - Strategy now uses a strong master-detail pattern with a stable list, selected record summary, tabs, and modal editing.
   - Budget should follow the same pattern rather than using separate heavy pages for allocation management.

3. **The allocation screen is too heavy and introduces scope creep.**
   - It shows large financial cards, available for reservation, reserved amount, budget line details, strategic context, financial context, and procurement use.
   - This makes Budget look like a procurement consumption and reservation module, not a simple allocation module.

4. **New budget and manage allocations pages still feel detached.**
   - The Frappe left menu is now more stable than before, which is good.
   - But the route/page context is still not clean enough.
   - Breadcrumbs such as `Budget ManagementNew Budget / Create Budget` feel broken and reinforce the sense of a stitched-together flow.

---

# 2. Target Mental Model

Budget and Funding should answer only five questions:

```text
Which budget are we working on?
What fiscal year and strategic plan does it belong to?
How much money is available?
How much has been allocated?
Is the budget ready for approval or already approved?
```

The module should follow this simple flow:

```text
Create Budget → Add Allocations → Review Totals → Submit / Approve → Lock
```

The UI should guide the user through that flow without forcing unnecessary navigation.

---

# 3. Recommended Pattern: Match Strategy Management

The Budget module should mirror the successful Strategy Management pattern.

Use this structure:

```text
Budget Management
├── status filter row
├── left budget list
└── selected budget workspace
    ├── budget header
    ├── status/readiness badges
    ├── metric summary
    ├── tabs
    └── focused content
```

Recommended tabs:

```text
Summary | Allocations | Review | Audit
```

This is enough. Do not create too many tabs.

---

# 4. Recommended Workbench Layout

Use this layout as the target:

```text
Budget Management                                      [New Budget]
Create, review, approve, and manage strategy-linked budget allocations.

[All 1] [My Work 0] [Draft 0] [Submitted 0] [Approved 1] [Rejected 0]

┌──────────────────────────────┬─────────────────────────────────────────────┐
│ Budgets                      │ BUDGET-MOH-2026                             │
│ [Search budgets...]          │ FY 2026 · Ministry of Health Strategic Plan  │
│                              │ KES · [Approved] [Locked]                   │
│ BUDGET-MOH-2026              │                                             │
│ FY 2026 · Approved           │ This budget is approved and locked.         │
│ KES 120.0M                   │                                             │
│                              │ Total        KES 120,000,000                │
│                              │ Allocated    KES 120,000,000                │
│                              │ Remaining    KES 0                          │
│                              │ Programs     1                              │
│                              │                                             │
│                              │ [Summary] [Allocations] [Review] [Audit]    │
│                              │                                             │
│                              │ Program allocations                         │
│                              │ Program                       Allocated      │
│                              │ Healthcare Infrastructure     KES 120.0M     │
└──────────────────────────────┴─────────────────────────────────────────────┘
```

This keeps the full module on one coherent page.

---

# 5. Simplify the Top Status Filters

The current status chips are acceptable:

```text
All 1 | My Work 0 | Draft 0 | Submitted 0 | Approved 1 | Rejected 0
```

Keep them, but make them compact and consistent with Strategy.

Recommended rules:

- Keep the filter row to one line.
- Do not add separate KPI cards above it.
- Use counts only where useful.
- Selected filter should be visually dominant.
- Zero-count filters should be muted.

Do not introduce separate cards such as:

```text
Active
Drafts
Pending Approval
Available to Reserve
```

Those create duplication and confusion.

---

# 6. Improve the Budget List

The left list should behave like the Strategy list.

Current budget cards are acceptable but can be clearer.

Recommended budget card:

```text
BUDGET-MOH-2026
FY 2026 · Approved
KES 120.0M · 1 program
```

Optional second line:

```text
MOH Strategic Plan 2026–2030
```

Avoid overly large cards. The list is for selection, not for full financial review.

Recommended list panel:

```text
Budgets
[Search budgets...]

BUDGET-MOH-2026
FY 2026 · Approved
KES 120.0M · 1 program
```

The list should scroll independently when there are many budgets.

---

# 7. Strengthen the Selected Budget Header

The selected budget header should carry the core context.

Recommended header:

```text
BUDGET-MOH-2026
FY 2026 · Ministry of Health Strategic Plan 2026–2030 · KES
[Approved] [Locked]

This budget is approved and locked.
```

For a draft budget:

```text
BUDGET-MOH-2027
FY 2027 · Ministry of Health Strategic Plan 2026–2030 · KES
[Draft] [Editable]

Next step: add allocations and submit for approval.
```

The header should make the next state obvious.

---

# 8. Simplify the Metric Summary

Budget should show only the primary allocation metrics by default:

```text
Total
Allocated
Remaining
Programs Funded
```

Example:

```text
Total               KES 120,000,000
Allocated           KES 120,000,000
Remaining           KES 0
Programs Funded     1
```

Do not show `Available for Reservation` or `Reserved` as primary metrics in the Budget Management workbench.

Those are downstream procurement consumption metrics. They should be moved to a secondary area.

---

# 9. Move Reservation and Procurement Usage Out of the Primary View

The current allocation screen shows:

```text
Available for Reservation
Reserved
Procurement Use
Linked procurement journeys
Linked demands
Linked procurement packages
```

This is too much for the main Budget and Funding workflow.

Recommended placement:

```text
Audit / Usage tab
```

or collapsed section:

```text
Downstream usage
Reserved: KES 98,000,000
Available for reservation: KES 22,000,000
Linked demands: 1
Linked packages: 1
```

Default view should stay focused on allocation.

Budget should not visually become a procurement execution screen.

---

# 10. Replace “Manage Allocations” Page with an Allocations Tab

The current `Manage Allocations` page is too heavy and creates another workspace inside the workspace.

The preferred design is to manage allocations inside the selected budget workspace, using an `Allocations` tab.

Recommended tab:

```text
Allocations                                      [Add Allocation]

Program / Sub-program                     Allocated        Notes
Healthcare Infrastructure Rehabilitation   KES 120.0M       Funding for rehabilitation...
```

When a row is selected or edited, open a drawer/modal:

```text
Edit Allocation

Program / Sub-program *
[Healthcare Infrastructure Rehabilitation]

Allocated Amount *
[KES 120,000,000]

Funding Source
[Government of Kenya Development Budget]

Notes
[Funding for rehabilitation...]

[Cancel] [Save Allocation]
```

This matches the Strategy pattern where editing happens in a modal while the user remains in the main workbench.

---

# 11. Recommended Allocation Editing Pattern

Do not show a large allocation detail form inline by default.

Use table + modal.

## Allocation Table

```text
Allocations                                      [Add Allocation]

Program / Sub-program                    Amount             Funding Source       Status
Healthcare Infrastructure Rehab           KES 120,000,000    GoK Development      Active
```

## Allocation Drawer / Modal

```text
Edit Allocation

Hierarchy link
Program / Sub-program *

Allocation
Amount *
Funding Source
Notes

[Cancel] [Save]
```

This is similar to the Strategy target edit modal shown in the latest Strategy screen. It keeps the page compact and understandable.

---

# 12. Simplify New Budget Creation

The `New Budget` page is better than before because it keeps the global menu, but it still feels like a separate form and has breadcrumb issues.

Current issue:

```text
Budget ManagementNew Budget / Create Budget
```

This looks broken and undermines confidence.

Recommended approach:

Use a modal/drawer for new budget creation, not a full page, because budget metadata is small.

## New Budget Drawer

```text
New Budget

Budget name *
Strategic plan *
Procuring entity *
Fiscal year *
Currency *
Total budget amount *
Notes

[Cancel] [Create Budget]
```

After saving:

```text
- stay on Budget Management
- select the new budget automatically
- open the Allocations tab
- show next step: Add allocations
```

This is simpler and more consistent with Strategy.

---

# 13. If New Budget Must Remain a Separate Route

If Frappe implementation constraints require a separate route, preserve context cleanly.

Required header:

```text
Budget Management / New Budget
Create Budget

[Back to Budget Workbench]                         [Save]
```

Required left menu behavior:

```text
Budget & Funding remains active
Global KenTender navigation remains unchanged
```

Required save behavior:

```text
Save → return to Budget Management with the new budget selected
```

Do not leave the user on a generic form page after creation unless there is a strong reason.

---

# 14. Clarify Budget Workflow

The module should expose a simple state model:

```text
Draft → Submitted → Approved / Rejected
```

Optional later:

```text
Approved → Locked
Approved → Revised
```

But do not make the workflow ambiguous.

## Draft Budget

Show:

```text
[Edit Budget Info] [Add Allocation] [Submit for Approval]
```

## Submitted Budget

Show:

```text
[Approve] [Reject] [Return for Correction]
```

## Approved Budget

Show:

```text
[View Allocations] [Audit] [More]
```

If approved budgets are locked, say so clearly:

```text
This budget is approved and locked. Allocations cannot be edited unless a revision is opened.
```

---

# 15. State-Aware Actions

Avoid showing irrelevant actions.

Recommended actions by state:

## Draft

```text
[Edit Budget Info] [Add Allocation] [Submit for Approval]
```

## Submitted

```text
[Review] [Approve] [Return for Correction] [Reject]
```

## Approved

```text
[View Allocations] [View Audit] [More]
```

## Rejected

```text
[Revise] [View Comments]
```

Do not show allocation editing actions when the budget is locked unless there is a formal revision flow.

---

# 16. Recommended Tabs

Use only four tabs:

```text
Summary | Allocations | Review | Audit
```

## Summary

Purpose: understand the selected budget at a glance.

Show:

- budget identity
- status
- strategic plan
- fiscal year
- total budget
- allocated
- remaining
- programs funded
- next step

## Allocations

Purpose: manage or review allocation rows.

Show:

- allocation table
- add/edit allocation action if allowed
- total allocation footer

## Review

Purpose: readiness and approval workflow.

Show:

- validation checks
- approval comments
- submit/approve/reject actions

## Audit

Purpose: evidence and downstream usage.

Show:

- approval history
- lock/revision history
- downstream usage
- reservation summary if applicable
- linked demands/packages if applicable

---

# 17. Recommended Summary Tab

```text
Summary

Budget identity
BUDGET-MOH-2026
FY 2026 · MOH Strategic Plan 2026–2030 · KES
Approved · Locked

Financial summary
Total               KES 120,000,000
Allocated           KES 120,000,000
Remaining           KES 0
Programs Funded     1

Next step
This budget is approved and locked. Use Audit to view downstream usage.
```

This is enough. Do not show strategic context, financial context, and procurement use all on Summary.

---

# 18. Recommended Allocations Tab

```text
Allocations                                      [Add Allocation]

Program / Sub-program                    Allocated          Funding Source        Notes
Healthcare Infrastructure Rehab           KES 120.0M         GoK Development       Funding for rehabilitation...

Total allocated: KES 120,000,000
Remaining: KES 0
```

On approved/locked budget:

```text
Allocations
This budget is approved and locked. Allocations are read-only.

Program / Sub-program                    Allocated          Funding Source        Notes
Healthcare Infrastructure Rehab           KES 120.0M         GoK Development       Funding for rehabilitation...
```

---

# 19. Recommended Review Tab

For draft budget:

```text
Review

Readiness checks
✓ Budget name provided
✓ Strategic plan selected
✓ Fiscal year provided
✓ Total budget amount provided
✓ At least one allocation exists
✓ Allocated amount does not exceed total budget

Current state: Draft
Next action: Submit for approval

[Submit for Approval]
```

For submitted budget:

```text
Review

Current state: Submitted
Awaiting approval by Planning Authority / Budget Approver.

[Approve] [Return for Correction] [Reject]
```

For approved budget:

```text
Review

Current state: Approved
This budget is approved and locked.

Approved by: [user]
Approved on: [date]
```

---

# 20. Recommended Audit Tab

```text
Audit

Workflow history
Draft created
Submitted for approval
Approved
Locked

Downstream usage
Reserved amount: KES 98,000,000
Available for reservation: KES 22,000,000
Linked demands: 1
Linked procurement packages: 1
Linked procurement journeys: 1
```

This preserves the useful downstream information without cluttering the normal allocation workflow.

---

# 21. Notes Field Should Be Controlled

The current notes field contains long seed/internal text:

```text
WORKS master seed §9.2. Description: Funding for rehabilitation and renovation...
Approved by: USER-BUD-001 on 2026-02-10T11:00:00+03:00.
```

This is too technical for the main UI.

Recommended split:

```text
Description / Notes
Funding for rehabilitation and renovation of priority district hospital facilities.

Technical seed reference
WORKS master seed §9.2

Approval reference
Approved by USER-BUD-001 on 2026-02-10 11:00
```

Place technical seed references in Audit or Technical Details, not in the primary notes field.

---

# 22. Strategic Context Should Be Compact

The current allocation detail shows large strategic context blocks:

```text
Program
Sub-program
Output Indicator
Performance Target
```

This is useful, but too large in the primary allocation page.

Recommended compact display:

```text
Strategic alignment
Program: Healthcare Infrastructure Rehabilitation
Sub-program: District health facility rehabilitation
Indicator: Improve district hospital infrastructure readiness
Target: Renovate priority district hospital facilities in FY 2026/2027
```

Place this in allocation detail drawer or Audit/Usage tab, not always expanded in the main screen.

---

# 23. Consistency with Strategy Pattern

The improved Strategy screen shows the right direction:

- stable left menu
- module workbench
- list on the left
- selected record detail on the right
- compact status filters
- tabs inside selected record
- modals for editing child records

Budget should use the same pattern:

```text
Strategy Pattern                     Budget Equivalent
Strategic Plans list                 Budgets list
Selected plan header                 Selected budget header
Plan status filters                  Budget status filters
Structure tab                        Allocations tab
Review tab                           Review tab
Audit tab                            Audit tab
Edit target modal                    Edit allocation modal
New Strategic Plan drawer/modal      New Budget drawer/modal
```

This will make KenTender feel coherent across modules.

---

# 24. What to Remove from the Default Budget Workbench

Remove or hide by default:

- large reservation cards
- large allocation detail forms
- procurement use blocks
- linked journeys/demands/packages
- technical seed references
- duplicated financial context
- generic Frappe-style full-page creation where a drawer would do

Keep visible:

- selected budget identity
- status
- fiscal year
- strategic plan
- total budget
- allocated
- remaining
- allocations table
- next action

---

# 25. Immediate Implementation Changes

In priority order:

1. **Convert New Budget to a drawer/modal if possible.**
   - Keep the user in Budget Management.

2. **Move Manage Allocations into the main workbench as an Allocations tab.**
   - Do not open a separate allocation workspace unless absolutely required.

3. **Use allocation table + edit modal.**
   - Match the Strategy edit modal pattern.

4. **Remove reservation metrics from the primary summary.**
   - Move to Audit/Usage.

5. **Move Procurement Use to Audit/Usage.**
   - Keep Budget focused on allocations.

6. **Fix breadcrumbs and route labels.**
   - Use `Budget Management / New Budget`, not concatenated labels.

7. **Make workflow actions state-aware.**
   - Draft: edit/add/submit.
   - Submitted: approve/return/reject.
   - Approved: view/audit.

8. **Simplify notes and strategic context.**
   - Keep technical references out of default UI.

9. **Match Strategy visual structure.**
   - Same list/detail proportions, tabs, modals, and compact filters.

10. **Restore context after save.**
   - New budget save should return to workbench with the new budget selected.

---

# 26. Final Target Experience

The desired experience should be:

```text
Budget Management
→ select budget
→ see totals and status
→ open Allocations tab
→ add/edit allocation in modal
→ review readiness
→ submit/approve
→ audit downstream usage only when needed
```

Not:

```text
Budget Management
→ New Budget page
→ Manage Allocations page
→ large financial cards
→ budget line detail form
→ strategic context
→ financial context
→ procurement usage
→ scroll-heavy page
```

Budget and Funding is a small module. Keep it small.

---

# 27. Final Recommendation

Refactor Budget and Funding into the same workbench pattern now used for Strategy:

```text
Left list + selected record workspace + compact filters + tabs + modals
```

The module should feel like a simple financial allocation workbench, not a procurement finance console.

The core rule is:

```text
Budget defines allocation.
Audit shows usage.
Procurement consumes allocation.
```

Keep those concerns separate in the UI.

