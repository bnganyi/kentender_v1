# KenTender Demand Intake and Approval UI Refactor Recommendations

This document captures recommendations for improving the Demand Intake and Approval (DIA) module UI. The current DIA implementation is better than several earlier modules because the main workbench is moving toward a cleaner master-detail pattern. However, there are still important issues around queues, filters, KPI cards, search placement, and form navigation context.

The goal is to make DIA feel like a focused demand case-management workbench:

```text
Demand list → selected demand → next action → approval / planning readiness
```

It should not feel like a collection of competing queue strips, KPI cards, filters, and detached forms.

---

# 1. Current Assessment

DIA is moving in the right direction, but the screenshots show two main UX problems:

1. **The queue, card, filter, and search area is confusing and contradictory.**
   - KPI cards show one set of statuses.
   - Scope filters show another set.
   - Queue chips show another set.
   - Search sits separately and competes for attention.
   - Empty-state messaging appears inside a large panel, but it is not obvious whether the user is looking at “My Drafts”, “All Demands”, “Approved”, or “Planning Ready”.

2. **The create/edit/approval form changes the left navigation context.**
   - When opening a demand form, the left menu changes to a narrow DIA-only context.
   - The user loses the broader Procurement Planner navigation.
   - The form page feels detached from the DIA workbench.
   - This is especially problematic because the form and workflow are necessarily separate in some cases, but the user should still feel anchored in the same module.

DIA should be refactored similarly to the Tender Management workbench pattern.

---

# 2. What DIA Should Be

Demand Intake and Approval should answer four operational questions:

```text
What demand has been requested?
Is it complete and justified?
Has it been approved?
Is it ready for procurement planning?
```

The primary user workflow should be:

```text
Capture demand → review demand → approve/reject → mark planning ready / hand off to planning
```

The UI should support this with a clear lifecycle workbench.

---

# 3. Main Problem: Too Many Competing Controls

The first screenshot shows:

```text
Approved KPI
Planning Ready KPI
Emergency Approved KPI
Total Value Ready for Planning KPI

My Work / All / Approved / Rejected segmented row

My Drafts / All Demands / Planning Ready / Approved Not Yet Planned / More queue chips

Search field
Filter icon
Info icon

Large empty queue panel
Separate detail panel
```

This is too much control surface for a module that should be simple.

The user has to mentally resolve:

- Is `Approved` a KPI, a tab, a queue, or a status?
- What is the difference between `Planning Ready` and `Approved Not Yet Planned`?
- Why is `My Drafts` active while the KPI says there is one approved demand?
- Does `My Work` mean ownership, assigned approvals, drafts, or actionable items?
- Is the search scoped to all demands, the current queue, or the current tab?

This is the same problem Tender Management had before the queue refactor.

---

# 4. Recommended Direction: DIA Workbench Pattern

Use a compact workbench structure:

```text
Demand Intake and Approval                           [New Demand]
Capture, review, approve, and prepare procurement demand for planning.

[All 1] [My Work]
Draft [0] · Submitted [0] · Under Review [0] · Approved [1] · Planning Ready [0] · Rejected [0] · Emergency [0]

┌──────────────────────────────┬─────────────────────────────────────────────┐
│ Demand list                  │ Selected demand detail                      │
│ [Search demand...]           │                                             │
│ filters                      │ Demand header                               │
│ demand cards                 │ Status badges                               │
│                              │ Next step                                   │
│                              │ Actions                                     │
│                              │ Tabs / sections                             │
└──────────────────────────────┴─────────────────────────────────────────────┘
```

This matches the Tender Management direction and gives the user one coherent mental model.

---

# 5. Replace KPI Cards with a Compact Lifecycle Queue Bar

## Current Problem

The KPI cards at the top show:

```text
Approved
Planning Ready
Emergency Approved
Total Value Ready for Planning
```

These cards consume space and partially duplicate the queue filters below them.

They also mix different concepts:

- lifecycle status: Approved
- lifecycle/hand-off status: Planning Ready
- demand type/priority: Emergency Approved
- monetary aggregate: Total Value Ready for Planning

These should not all sit in the same KPI row.

## Recommendation

Remove the large KPI card row from the default workbench.

Use a compact lifecycle queue bar instead:

```text
[All 1] [My Work]
Draft 0 · Submitted 0 · Under Review 0 · Approved 1 · Planning Ready 0 · Rejected 0 · Emergency 0
```

Or grouped:

```text
[All 1] [My Work]
Intake [Draft 0] [Submitted 0] · Review [Under Review 0] [Approved 1] [Rejected 0] · Planning [Planning Ready 0] [Not Yet Planned 1] · Exception [Emergency 0]
```

The second option is better if the lifecycle has many states.

## Recommended DIA Queue Bar

```text
[All 1] [My Work]
Intake [Draft 0] [Submitted 0] · Review [Under Review 0] [Approved 1] [Rejected 0] · Planning [Approved not planned 1] [Planning ready 0] · Exception [Emergency 0]
```

Target height: **maximum 72–96px**.

Do not use large cards for queue navigation.

---

# 6. Clarify Status Terms

The current queue names may confuse users.

Problematic terms:

```text
Planning Ready
Approved Not Yet Planned
Emergency Approved
```

These need clearer lifecycle meaning.

## Suggested Status Vocabulary

Use a clean state model:

```text
Draft
Submitted
Under Review
Approved
Rejected
Planning Ready
Planned
Cancelled
```

Use emergency as a flag, not a lifecycle state:

```text
Emergency: Yes/No
Priority: Normal/High/Emergency
```

Do not make `Emergency Approved` a main lifecycle queue unless it is a legally distinct approval path.

## Recommended Distinction

Use:

```text
Status: Approved
Planning state: Not yet planned
Priority: Emergency
```

instead of:

```text
Emergency Approved
Approved Not Yet Planned
```

This prevents one demand from appearing to have multiple contradictory statuses.

---

# 7. Better Search Placement

The search bar should belong to the demand list, not float as a top-level page control.

## Recommended Placement

Inside the left list panel:

```text
Demand list
[Search ID, title, requester, department...]

Status: Approved
Priority: Any
Department: Any
Planning state: Not yet planned
```

This makes it obvious that search filters the demand list.

The top of the page should stay focused on lifecycle queues and primary action.

---

# 8. Better Left Demand List

The left demand list should act like an inbox.

Each card should show only the most important information:

```text
DIA-PE-MOH-2026-0001
Test
Draft · Goods · Normal
KES 200,000 · Required by 22 May 2026
```

For an approved demand:

```text
DIA-MOH-2026-0007
District Hospital Renovation Works
Approved · Works
KES 98,000,000 · Not yet planned
```

Avoid showing too many labels or repeating the same concept.

## Recommended List Card Fields

Always visible:

- Demand ID
- Title
- Current status
- Category/type
- Estimated value
- Required-by date
- Planning state or blocker status

Optional badges:

- Emergency
- Blocked
- Returned
- Planning Ready

---

# 9. Detail Panel Should Lead with Demand Identity and Next Action

When a demand is selected, the right panel should immediately answer:

```text
What is this demand?
What state is it in?
What is the value?
What is the next action?
What can I do now?
```

## Recommended Selected Demand Header

```text
DIA-PE-MOH-2026-0001 · Test
Clinical Services · Goods · Normal priority
Requested by Administrator · Required by 22 May 2026

[Draft] [KES 200,000] [Not submitted] [No blockers]

Next step
Complete the demand and submit for approval.

[Edit Demand] [Submit for Approval] [Cancel Demand] [More]
```

For an approved demand:

```text
DIA-MOH-2026-0007 · District Hospital Renovation Works
Ministry of Health · Works · Normal priority
Requested by Clinical Services · Required by 05 Jun 2026

[Approved] [KES 98,000,000] [Not yet planned] [No blockers]

Next step
Prepare this approved demand for procurement planning.

[Mark Planning Ready] [View Demand] [More]
```

---

# 10. Replace Empty State Confusion with Actionable Empty States

Current empty state:

```text
No drafts in this queue.
Create new demand
Switch queue
```

This is acceptable, but it needs clearer context.

## Better Empty State

```text
No draft demands
You do not currently have draft demands assigned to you.

[Create Demand] [View All Demands]
```

For approved queue:

```text
No approved demands in this queue
Approved demands will appear here after review.

[View All Demands]
```

Do not show a large empty panel and a separate detail panel that says “Select a demand” at the same time. If the list is empty, the detail panel should either be hidden or show guidance related to the empty state.

---

# 11. Detail Tabs for DIA

Use a small, stable set of tabs in the selected demand detail:

```text
Overview | Items & Value | Review | Planning | Audit
```

## Overview

- Demand identity
- Requester / department
- Category / priority
- Required-by date
- Business justification summary
- Current next step

## Items & Value

- Requested items table
- Quantity
- Unit cost
- Line total
- Total requested

## Review

- Completeness checks
- Approval decision
- Reviewer comments
- Return/reject reasons

## Planning

- Strategy linkage
- Budget linkage
- Planning readiness
- Planning handoff state

## Audit

- State transition history
- Submit/approve/reject events
- Evidence
- Attachments

This is clearer than mixing everything in a large form or unstructured detail area.

---

# 12. New/Edit Demand Forms Necessarily Separate, But Must Preserve Context

The user noted that new/edit demand and approval workflow are necessarily on a separate form. That is acceptable. However, the current behavior causes context loss because the left navigation changes.

This should be fixed.

## Current Problem

When the user opens a demand form:

- the broader Procurement Planner menu disappears or changes
- the left menu becomes DIA-only
- the user no longer feels anchored in the same workbench
- the page looks like a generic Frappe form rather than a DIA workflow screen

## Recommendation

Keep the global left menu stable.

The user should still see:

```text
Procurement Home
Procurement Journeys
My Work
Strategy Alignment
Budget & Funding
Demand Intake & Approval
Procurement Planning
Tender Management
...
```

The form can open as a separate route, but it should retain the same application shell and left navigation.

---

# 13. Add a Context Header to Separate Form Pages

If the form must be a separate page, add a strong context header:

```text
Demand Intake and Approval / DIA-PE-MOH-2026-0001
Draft

[Back to Demand Workbench]        [Submit for Approval] [Cancel Demand] [Save]
```

Below that, show a compact status ribbon:

```text
Demand: Test · Goods · KES 200,000 · Required by 22 May 2026
Status: Draft · Planning: Not ready · Blockers: None
```

This keeps the user oriented.

---

# 14. Use a Form Stepper Instead of One Long Form

The current new/edit form is already long:

1. Demand identity
2. What is being requested
3. Amount summary
4. Why / business justification
5. likely more sections below

This is better than a completely unstructured form, but it can still become scroll-heavy.

## Recommendation

Use a compact stepper or anchored section navigation:

```text
Identity | Items | Justification | Strategy/Budget | Review
```

The form can remain on one page, but the top should show where the user is and what remains incomplete.

## Better Form Layout

```text
DIA-PE-MOH-2026-0001 · Draft
[Identity complete] [Items complete] [Justification missing] [Strategy link missing]

Identity | Items & Value | Justification | Linkages | Review
```

Each section should be collapsible after completion.

---

# 15. Approval Workflow Actions Should Be State-Aware

Do not show every possible workflow action at all times.

## Draft

```text
[Save] [Submit for Approval] [Cancel Demand]
```

## Submitted / Under Review

```text
[Approve] [Return for Correction] [Reject]
```

## Approved

```text
[Mark Planning Ready] [Return to Review] [Cancel]
```

## Planning Ready

```text
[Create Procurement Plan Item] [View Planning Handoff]
```

Dangerous actions such as cancel/reject should be secondary or behind confirmation.

---

# 16. Separate Demand Status from Planning Status

One source of confusion is that approval and planning readiness are mixed together.

Use two fields visually:

```text
Demand status: Draft / Submitted / Approved / Rejected
Planning status: Not ready / Ready for planning / Planned
```

Example:

```text
[Approved] [Planning: Not yet planned]
```

This is clearer than:

```text
Approved Not Yet Planned
```

which reads like a queue name rather than a state model.

---

# 17. Recommended DIA Workbench Layout

```text
Demand Intake and Approval                                      [New Demand]
Capture, review, approve, and prepare procurement demand for planning.

[All 1] [My Work]
Intake [Draft 0] [Submitted 0] · Review [Under Review 0] [Approved 1] [Rejected 0] · Planning [Not yet planned 1] [Planning ready 0] · Exception [Emergency 0]

┌──────────────────────────────┬─────────────────────────────────────────────┐
│ Demand list                  │ DIA-MOH-2026-0007 · District Hospital Works │
│ [Search ID, title, dept...]  │ Clinical Services · Works · Normal          │
│                              │ Required by 05 Jun 2026 · KES 98,000,000   │
│ Status: Approved             │                                             │
│ Planning: Not yet planned    │ [Approved] [Planning: Not yet planned]      │
│ Priority: Any                │ [No blockers]                               │
│                              │                                             │
│ DIA-MOH-2026-0007            │ Next step                                   │
│ District Hospital Works      │ Prepare this demand for procurement planning│
│ Approved · Not yet planned   │                                             │
│ KES 98.0M · 05 Jun 2026      │ [Mark Planning Ready] [View Demand] [More]  │
│                              │                                             │
│                              │ Overview | Items & Value | Review | Planning | Audit
│                              │                                             │
│                              │ Overview                                    │
│                              │ Business justification summary              │
│                              │ Requester and department                    │
│                              │ Value summary                               │
└──────────────────────────────┴─────────────────────────────────────────────┘
```

---

# 18. Recommended Separate Form Layout

If the demand form must remain separate, use this pattern:

```text
Demand Intake and Approval / DIA-PE-MOH-2026-0001               [Save] [Submit for Approval]
Draft · Goods · KES 200,000 · Required by 22 May 2026

[Back to Demand Workbench]

Identity | Items & Value | Justification | Linkages | Review

Identity
Title
Department
Demand category
Priority
Requested by
Required by

Items & Value
Item table
Total requested

Justification
Business justification
Beneficiaries

Linkages
Strategic target
Budget line

Review
Completeness checks
Submit readiness
```

Keep the global left navigation unchanged.

---

# 19. What to Change Immediately

In priority order:

1. **Remove the large KPI card row from the default DIA workbench.**
   - Replace it with a compact lifecycle queue bar.

2. **Merge contradictory queue/filter rows.**
   - Do not show KPI cards, scope tabs, queue chips, search, and filters as separate competing layers.

3. **Move search into the left demand list panel.**
   - Search should clearly filter visible demands.

4. **Separate demand status from planning status.**
   - Example: `Approved` + `Planning: Not yet planned`.

5. **Use Tender-style compact queue bar.**
   - Intake / Review / Planning / Exception groups.

6. **Make the selected demand header stronger.**
   - Identity, value, status, planning state, next action.

7. **Use state-aware actions.**
   - Show only relevant actions for the current state.

8. **Keep the global left menu stable on form pages.**
   - Do not change the user’s navigation context when they open new/edit/approval pages.

9. **Add a clear form context header.**
   - Breadcrumb, demand ID, state, primary actions, back to workbench.

10. **Use section tabs or stepper on the long demand form.**
   - Identity / Items / Justification / Linkages / Review.

---

# 20. Final Recommendation

DIA should follow the same pattern established for Tender Management:

```text
Compact lifecycle queue bar
Left searchable list
Right selected-record workbench
Strong selected-record header
Current next step
State-aware actions
Grouped tabs
Audit/details on demand
```

The module is already close, but the current top area is doing too much. The refactor should remove competing controls and make the screen read as one coherent workflow.

For separate form pages, the solution is not to force everything into the workbench. The solution is to preserve context:

```text
same global navigation
clear DIA breadcrumb
back to workbench
sticky action header
section-based form
```

That will keep DIA simple while still supporting the necessary create/edit/approval workflow forms.

