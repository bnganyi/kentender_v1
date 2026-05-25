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

# 12. New/Edit Demand Should Follow the Same Workbench Pattern as Strategy and Budget

The earlier guidance allowed New/Edit Demand forms to sit on separate routes as long as context was preserved. That should be corrected.

For consistency with Strategy and Budget, DIA should not treat New/Edit Demand as a detached full-page form by default. The demand form is larger than Strategy or Budget metadata forms, but the interaction pattern should remain the same:

```text
Workbench remains the anchor.
New/Edit opens as a guided drawer, modal, or in-workbench form panel.
The user does not feel they entered a different app.
```

## Recommended Pattern

Use an in-workbench guided form surface:

```text
Demand Intake and Approval
├── Left: demand list
└── Right: selected demand / form workspace
    ├── Header
    ├── Stepper
    ├── Current form step
    └── Review / submit section
```

For `New Demand`, the right panel can temporarily become the guided form while the left demand list and module shell remain visible.

For `Edit Demand`, the selected demand detail should switch into edit mode or open a large right-side drawer over the detail area.

## Acceptable Implementations

Preferred:

```text
New Demand → right-side guided drawer or panel inside DIA workbench
Edit Demand → edit mode / drawer inside selected demand workspace
```

Acceptable if the form is too large for a drawer:

```text
New/Edit Demand → module-owned full-screen workbench mode
```

But even then, it must preserve:

- global left navigation
- active `Demand Intake & Approval` menu item
- module breadcrumb
- back to workbench action
- same visual shell
- same route family

## Route Guidance

Avoid generic detached routes:

```text
/desk/demand/670ohgj3jt
/app/demand/DIA-PE-MOH-2026-0001
```

Prefer module-owned routes if a full-screen mode is unavoidable:

```text
/desk/demand-intake-and-approval/new
/desk/demand-intake-and-approval/DIA-PE-MOH-2026-0001/edit
/desk/demand-intake-and-approval/DIA-PE-MOH-2026-0001/review
```

## Design Rule

DIA should follow the Strategy and Budget pattern:

```text
Small forms → drawer/modal
Large forms → guided in-workbench panel or module-owned full-screen mode
Generic detached Frappe form → avoid for primary user workflow
```

---

# 13. If Full-Screen Editing Is Unavoidable, Use a Workbench-Mode Header

The preferred solution is to keep New/Edit Demand inside the DIA workbench. However, if the demand form is too large and must use a full-screen mode, it must still look and behave like DIA, not like a generic Frappe document form.

Required header:

```text
Demand Intake and Approval / New Demand
Draft · Not saved

[Back to Demand Workbench]                         [Save Draft]
```

For an existing demand:

```text
Demand Intake and Approval / DIA-PE-MOH-2026-0001
Draft · Goods · KES 200,000 · Required by 22 May 2026

[Back to Demand Workbench]                         [Save]
```

Below that, show guided progress:

```text
Identity ✓ | Items & Value ! | Justification ! | Linkages optional | Review blocked
```

Do not use broken or concatenated breadcrumbs such as:

```text
Demand Intake and ApprovalNew Demand / Create Demand
```

## Design Rule

Full-screen editing is a workbench mode, not a separate app.

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

# 18. Recommended In-Workbench New/Edit Demand Layout

The New/Edit Demand experience should follow the Strategy and Budget pattern: remain anchored in the module and use a guided editing surface.

Preferred layout:

```text
Demand Intake and Approval                                      [New Demand]
Capture, review, approve, and prepare procurement demand for planning.

[All 1] [My Work]
Intake [Draft 0] [Submitted 0] · Review [Approved 1] [Rejected 0] · Planning [Not yet planned 1] [Planning ready 0]

┌──────────────────────────────┬─────────────────────────────────────────────┐
│ Demand list                  │ New Demand                                  │
│ [Search ID, title, dept...]  │ Draft · Not saved                           │
│                              │                                             │
│ DIA-MOH-2026-0007            │ Identity | Items & Value | Justification    │
│ District Hospital Works      │ Linkages | Review                           │
│ Approved · Not yet planned   │                                             │
│ KES 98.0M · 05 Jun 2026      │ Step 1: Identity                            │
│                              │ Title *                                     │
│                              │ Department *                                │
│                              │ Demand category *                           │
│                              │ Priority *                                  │
│                              │ Required by date *                          │
│                              │                                             │
│                              │ [Save Draft] [Next: Items & Value]          │
└──────────────────────────────┴─────────────────────────────────────────────┘
```

For editing an existing demand:

```text
DIA-PE-MOH-2026-0001 · Edit Demand
Draft · Goods · KES 200,000 · Required by 22 May 2026

Identity | Items & Value | Justification | Linkages | Review
```

The left demand list may remain visible or collapse to a narrow context rail if screen width is limited, but the global KenTender navigation and DIA context must remain stable.

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

8. **Do not use detached generic form pages for New/Edit Demand by default.**

   - Follow Strategy and Budget: keep New/Edit inside the DIA workbench as a drawer, modal, right-panel form, or guided workbench mode.
   - Use a separate route only if unavoidable, and only as a module-owned workbench route.

9. **Add a clear form context header when using guided edit mode.**

   - Breadcrumb, demand ID, state, primary actions, back to workbench.

10. **Use section tabs or stepper on the long demand form.**

- Identity / Items / Justification / Linkages / Review.

---

# 20. Strengthened Recommendations Based on Latest Screenshots

The earlier DIA refactor is still directionally correct and should remain the implementation baseline:

```text
Compact lifecycle queue bar
Left searchable list
Right selected-record workbench
Strong selected-record header
Current next step
State-aware actions placed in the relevant tab
Grouped tabs
Audit/details on demand
New/Edit forms handled inside the workbench pattern where possible
```

However, the latest screenshots show that the form and workbench need additional tightening. The biggest remaining issue is not the overall workbench idea. The issue is **role-based data entry** and **progressive completion**.

A requester should not be forced to provide planner-owned fields before they can submit a valid demand. DIA should distinguish between:

```text
Requester input
Reviewer input
Planner enrichment
Finance / budget validation
Audit output
```

Right now, some fields from later stages are appearing too early in the form.

---

# 21. Guided Data Entry: Keep the Form, But Make It Step-Based

The new/edit demand form has strong section demarcation, which is good. But it is still long and scroll-heavy.

Use a guided stepper or sticky section navigation:

```text
1 Identity → 2 Requested Items → 3 Justification → 4 Linkages → 5 Review & Submit
```

Each step should show completion state:

```text
Identity ✓   Items missing   Justification missing   Linkages optional   Review blocked
```

The user should always know:

```text
Where am I?
What is missing?
Can I submit?
What is optional at this stage?
```

## Recommended Form Header

```text
Demand Intake and Approval / New Demand
Draft · Not saved

[Back to Demand Workbench]                         [Save Draft]

Complete the required requester sections, then submit for approval.

Identity ✓ | Items & Value ! | Justification ! | Linkages optional | Review blocked
```

After save:

```text
Demand Intake and Approval / DIA-PE-MOH-2026-0001
Draft · Goods · KES 200,000 · Required by 22 May 2026

[Back to Demand Workbench]                         [Save] [Submit for Approval] [Cancel Demand]
```

---

# 22. Reorder the Form Around the Requester’s Mental Model

The current order is close, but still needs correction. The user noted that important fields can appear after less important ones.

The requester’s natural order is:

```text
Who needs it?
What is needed?
How much / how many?
Why is it needed?
When is it needed?
Which strategy/budget/planning context applies?
```

Recommended order:

## Step 1 — Demand Identity

Keep this first, but only include requester-known fields:

```text
Title
Department
Requested by
Demand category
Priority
Demand type
Required by date
Procuring entity
```

Move `Request Date` lower or make it system-generated/read-only. Requesters should not need to think about it.

## Step 2 — Requested Items & Value

Move this before the business justification section.

```text
Items table
Quantity
Unit of measure
Estimated unit cost
Line total
Total requested
```

This should come before justification because the user must first define what they are asking for.

## Step 3 — Justification

Then ask why:

```text
Business justification / who benefits
What is being requested / scope narrative
```

But avoid duplicating the items table. If `What is being requested` is just a prose version of line items, rename it to:

```text
Scope / requested outcome
```

or make it optional when line items are sufficiently clear.

## Step 4 — Linkages and Planning Context

This is where fields like budget line, strategy target, delivery location, and requested delivery period belong.

But these must not all be requester-required.

```text
Strategy linkage
Budget line
Delivery location
Requested delivery period
Reservation status
```

## Step 5 — Review & Submit

Show:

```text
Required fields complete
Items total calculated
Justification provided
Optional planning fields incomplete
Submit readiness
```

---

# 23. Mandatory Field Matrix by Workflow Stage

This section is implementation-critical. Cursor should not infer required fields from the current Frappe form, database required flags, or visual asterisks alone.

DIA must use **stage-based validation**. A field can be optional for draft save, required for submission, and required later for planning readiness.

The requester must be able to save a draft without planner-owned data such as budget line, strategy linkage, reservation status, funding source, delivery period, or planning handoff information.

## 23.1 Stages

Use these validation stages:

```text
Stage 0 — Save Draft
Stage 1 — Submit for Approval
Stage 2 — Review / Approve
Stage 3 — Prepare Planning Handoff
Stage 4 — Mark Planning Ready
```

## 23.2 Mandatory Fields by Stage

| Field / Section                       | Owner                        | Save Draft               | Submit for Approval             | Review / Approve                                  | Prepare Planning Handoff                 | Mark Planning Ready                      |
| ------------------------------------- | ---------------------------- | ------------------------ | ------------------------------- | ------------------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| Demand title                          | Requester                    | Required                 | Required                        | Required                                          | Required                                 | Required                                 |
| Requester / requested by              | System / requester           | Auto or Required         | Required                        | Required                                          | Required                                 | Required                                 |
| Department                            | Requester                    | Optional                 | Required                        | Required                                          | Required                                 | Required                                 |
| Procuring entity                      | System / requester           | Optional                 | Required                        | Required                                          | Required                                 | Required                                 |
| Demand category                       | Requester                    | Optional                 | Required                        | Required                                          | Required                                 | Required                                 |
| Demand type                           | Requester                    | Optional                 | Required                        | Required                                          | Required                                 | Required                                 |
| Priority                              | Requester                    | Optional; default Normal | Required                        | Required                                          | Required                                 | Required                                 |
| Request date                          | System                       | Auto                     | Auto                            | Auto                                              | Auto                                     | Auto                                     |
| Required by date                      | Requester                    | Optional                 | Required                        | Required                                          | Required                                 | Required                                 |
| At least one item row                 | Requester                    | Optional                 | Required                        | Required                                          | Required                                 | Required                                 |
| Item / service description            | Requester                    | Optional                 | Required for each submitted row | Required                                          | Required                                 | Required                                 |
| Item category                         | Requester                    | Optional                 | Required for each submitted row | Required                                          | Required                                 | Required                                 |
| Unit of measure                       | Requester                    | Optional                 | Required for each submitted row | Required                                          | Required                                 | Required                                 |
| Quantity                              | Requester                    | Optional                 | Required and > 0                | Required                                          | Required                                 | Required                                 |
| Estimated unit cost                   | Requester                    | Optional                 | Required and >= 0               | Required                                          | Required                                 | Required                                 |
| Line total                            | System                       | Auto                     | Auto                            | Auto                                              | Auto                                     | Auto                                     |
| Total requested                       | System                       | Auto, may be 0           | Required and > 0                | Required                                          | Required                                 | Required                                 |
| Business justification / who benefits | Requester                    | Optional                 | Required                        | Required                                          | Required                                 | Required                                 |
| Scope / requested outcome             | Requester                    | Optional                 | Required                        | Required                                          | Required                                 | Required                                 |
| Attachments                           | Requester / reviewer         | Optional                 | Optional unless policy requires | Optional / reviewer may request                   | Optional                                 | Optional                                 |
| Strategy linkage                      | Planner / requester if known | Optional                 | Optional                        | Optional                                          | Required                                 | Required                                 |
| Strategic plan                        | System from linkage          | Optional                 | Optional                        | Optional                                          | Required                                 | Required                                 |
| Program                               | System from linkage          | Optional                 | Optional                        | Optional                                          | Required                                 | Required                                 |
| Sub-program                           | System from linkage          | Optional                 | Optional                        | Optional                                          | Required                                 | Required                                 |
| Output indicator                      | System from linkage          | Optional                 | Optional                        | Optional                                          | Required                                 | Required                                 |
| Performance target                    | System from linkage          | Optional                 | Optional                        | Optional                                          | Required                                 | Required                                 |
| Budget line                           | Planner / budget owner       | Optional                 | Optional                        | Optional                                          | Required                                 | Required                                 |
| Budget                                | System from budget line      | Optional                 | Optional                        | Optional                                          | Required                                 | Required                                 |
| Funding source                        | System from budget line      | Optional                 | Optional                        | Optional                                          | Required                                 | Required                                 |
| Budget availability check             | System / budget control      | Not required             | Not required                    | Not required                                      | Required                                 | Required                                 |
| Reservation status                    | System / budget control      | Not required             | Not required                    | Not required                                      | Required if reservation model is enabled | Required if reservation model is enabled |
| Reservation reference                 | System                       | Not required             | Not required                    | Not required                                      | Required only if reserved                | Required only if reserved                |
| Delivery location                     | Requester / planner          | Optional                 | Optional                        | Optional                                          | Required                                 | Required                                 |
| Requested delivery period             | Requester / planner          | Optional                 | Optional                        | Optional                                          | Optional                                 | Optional unless policy requires          |
| Reviewer decision                     | Reviewer                     | Not applicable           | Not applicable                  | Required to approve/reject/return                 | Required if already approved             | Required if already approved             |
| Reviewer comments                     | Reviewer                     | Not applicable           | Optional                        | Required for return/reject; optional for approval | Optional                                 | Optional                                 |
| Planning inclusion artefact           | System / planner             | Not applicable           | Not applicable                  | Not applicable                                    | Required                                 | Required                                 |
| Planning handoff status               | System / planner             | Not applicable           | Not applicable                  | Not applicable                                    | Required                                 | Required                                 |

## 23.3 Hard Rules for Cursor / Implementation

1. **Save Draft must be permissive.**

   - Required for draft save: `Demand title` only.
   - If the implementation needs a requester or request date, set them automatically from the logged-in user and server date.
   - Do not require department, budget line, strategy linkage, items, justification, delivery location, or planning fields to save a draft.

2. **Submit for Approval requires requester-owned completeness only.**

   - Require identity, items/value, and justification.
   - Do not require budget line, funding source, strategy linkage, reservation status, or planning handoff fields.

3. **Approval should not require planner-owned enrichment.**

   - A reviewer may approve the demand as a justified need even if budget/strategy linkage is incomplete, unless the business policy explicitly requires pre-approval coding.
   - If budget/strategy linkage is missing, the approved demand moves to `Approved / Not yet planned`, not `Planning Ready`.

4. **Planning readiness requires planner-owned enrichment.**

   - Strategy linkage, budget line, budget availability check, and planning handoff artefacts become mandatory before `Mark Planning Ready`.

5. **Database required flags should be minimal.**

   - Avoid marking planner-owned fields as required at the DocType level if that blocks draft save.
   - Enforce stage-specific requirements in workflow validation methods instead.

6. **Visual asterisks must reflect the current step/stage.**

   - Do not show `Budget Line *` on the requester draft step if it is not required until planning readiness.
   - Use helper text: `Can be completed by planner before planning handoff.`

## 23.4 Field Grouping by Owner

### Requester-Owned Fields

These belong in the requester-guided form:

```text
Title
Department
Demand category
Demand type
Priority
Required by date
Items and estimated values
Business justification
Scope / requested outcome
Optional attachments
```

### Planner-Owned Fields

These should be optional or hidden during requester entry and completed later in the Planning tab:

```text
Strategy linkage
Budget line
Funding source
Budget availability check
Reservation status
Delivery planning details
Planning handoff artefacts
```

### System-Owned Fields

These should be computed or populated automatically:

```text
Demand ID
Request date
Requested by
Line totals
Total requested
Budget derived from budget line
Funding source derived from budget line
Reservation reference
Workflow timestamps
Audit users
```

---

# 24. Split Validation by Workflow Stage

Use separate validation contracts for each workflow action. Do not use one universal required-field list.

## 24.1 Save Draft Validation

Used when the requester clicks `Save Draft`.

Required:

```text
Demand title
```

Automatically set if missing:

```text
Demand ID
Request date
Requested by
Current stage = Draft
Planning status = Not planned
```

Optional at draft save:

```text
Department
Procuring entity
Demand category
Demand type
Priority
Required by date
Line items
Total requested
Business justification
Scope / requested outcome
Strategy linkage
Budget line
Delivery location
Requested delivery period
Reservation status
```

Draft save must not fail because any planner-owned field is empty.

## 24.2 Submit for Approval Validation

Used when the requester clicks `Submit for Approval`.

Required:

```text
Demand title
Department
Procuring entity
Demand category
Demand type
Priority
Required by date
At least one item row
Item / service description for each row
Item category for each row
Unit of measure for each row
Quantity > 0 for each row
Estimated unit cost >= 0 for each row
Total requested > 0
Business justification / who benefits
Scope / requested outcome
```

Optional before submission:

```text
Strategy linkage
Budget line
Funding source
Budget availability check
Reservation status
Reservation reference
Delivery location
Requested delivery period
Planning handoff artefacts
```

On successful submission:

```text
Current stage = Submitted or Under Review
Planning status = Not planned
```

## 24.3 Review / Approval Validation

Used when reviewer approves, rejects, or returns the demand.

Required to approve:

```text
Demand is submitted / under review
Submission readiness passed
Reviewer has approval permission
```

Required to return or reject:

```text
Reviewer decision
Reviewer comments / reason
```

Optional at approval:

```text
Strategy linkage
Budget line
Reservation status
Planning handoff artefacts
```

On approval without planning enrichment:

```text
Current stage = Approved
Planning status = Not yet planned
```

Do not automatically mark the demand as planning ready merely because it is approved.

## 24.4 Prepare Planning Handoff Validation

Used by planner/procurement planning role after approval.

Required:

```text
Current stage = Approved
Valid strategy linkage
Valid budget line
Budget availability check performed
Delivery location
```

Required only if reservation model is enabled:

```text
Reservation status resolved
Reservation reference if reserved
```

Output:

```text
Planning inclusion artefact generated or updated
Planning handoff status = Prepared
```

## 24.5 Mark Planning Ready Validation

Used when the demand is ready to be consumed by Procurement Planning.

Required:

```text
Current stage = Approved
Planning handoff prepared
Valid strategy linkage
Valid budget line
Budget availability check passed
Required planning artefacts generated
No unresolved planning blockers
```

On success:

```text
Planning status = Planning Ready
```

This prevents the form from becoming hostile to requesters while still protecting downstream governance.

---

# 25. Recommended New Demand Form Structure

The New Demand form should show required fields according to the current step and target action. It should not mark planner-owned fields as required during draft creation.

```text
Demand Intake and Approval / New Demand                     [Save Draft]
Draft · Not saved
[Back to Demand Workbench]

Step 1 of 5: Identity
Title *                                      Required to save draft and submit
Department                                  Required before submit
Requested by                                Auto from logged-in user
Request date                                Auto from server date
Demand category                             Required before submit
Priority                                    Default Normal; required before submit
Demand type                                 Required before submit
Required by date                            Required before submit
Procuring entity                            Required before submit

[Save Draft] [Next: Items & Value]
```

```text
Step 2 of 5: Items & Value
Required before submit, optional for draft save.

Items table
- Item / service description
- Category
- Unit of measure
- Quantity
- Estimated unit cost
- Line total auto-calculated

Total requested auto-calculated

[Back] [Save Draft] [Next: Justification]
```

```text
Step 3 of 5: Justification
Required before submit, optional for draft save.

Business justification / who benefits
Scope / requested outcome
Optional attachments

[Back] [Save Draft] [Next: Linkages]
```

```text
Step 4 of 5: Linkages
Not required for draft save or submit for approval.
These fields may be completed by a planner before planning handoff.

Strategy linkage                    Optional before approval; required before Planning Ready
Budget line                         Optional before approval; required before Planning Ready
Delivery location                   Optional before approval; required before Planning Ready
Requested delivery period           Optional
Reservation status                  System-managed; required before Planning Ready only if reservation model is enabled
Funding source                      Derived from budget line
Budget availability                 Checked by planner/system

[Back] [Save Draft] [Review]
```

```text
Step 5 of 5: Review & Submit
Submission readiness
✓ Title entered
✓ Department selected
✓ Demand category selected
✓ Priority selected
✓ Demand type selected
✓ Required by date entered
✓ At least one item entered
✓ Total requested > 0
✓ Business justification provided
✓ Scope / requested outcome provided
! Strategy/budget linkages pending — can be completed by planner before planning handoff

[Back] [Save Draft] [Submit for Approval]
```

This keeps the long form manageable without removing required governance.

---

# 26. Do Not Use a Floating Action Bar if It Breaks the Cross-Module Pattern

The floating action bar is useful in isolation, but it should be removed from the DIA recommendation if it breaks consistency with Strategy and Budget.

Strategy and Budget now place workflow actions inside the relevant `Review` tab or context-specific section. DIA should follow the same pattern for consistency.

## Recommendation

Do not use a persistent floating action bar in the DIA detail panel.

Instead, place actions in predictable locations:

1. **Overview tab**

   - Show the next step as guidance only.
   - Do not overload it with all workflow buttons.

2. **Review tab**

   - Place approval workflow actions here.
   - Examples: `Submit for Approval`, `Approve`, `Return for Correction`, `Reject`.

3. **Planning tab**

   - Place planning handoff actions here.
   - Examples: `Prepare Planning Handoff`, `Mark Planning Ready`, `Create Procurement Plan Item`.

4. **Form header**

   - On separate new/edit forms, keep only form-level actions.
   - Examples: `Save Draft`, `Save`, `Back to Demand Workbench`.

## State-Aware Review Tab Actions

### Draft

```text
Review
Submission readiness
✓ Identity complete
✓ Items entered
✓ Justification provided
! Budget and strategy linkages can be completed later by planner

[Submit for Approval]
```

### Submitted / Under Review

```text
Review
Current state: Submitted
Awaiting review.

[Approve] [Return for Correction] [Reject]
```

### Approved

```text
Review
Current state: Approved
Demand is approved and ready for planning preparation.

[Move to Planning]
```

## State-Aware Planning Tab Actions

### Approved, Not Yet Planned

```text
Planning
Planning readiness
! Strategy linkage missing
! Budget line missing
! Budget availability not checked

[Prepare Planning Handoff]
```

### Planning Ready

```text
Planning
This demand is ready for procurement planning.

[Create Procurement Plan Item] [View Planning Handoff]
```

## Design Rule

DIA should not introduce a different action model from Strategy and Budget.

Use this cross-module rule:

```text
Overview explains the current state.
Review handles approval workflow.
Planning handles planning handoff.
Audit holds evidence and history.
```

---

# 27. Workbench Detail: Reduce Audit Noise in Default View

The workbench detail is improving, but sections `E. Workflow and Audit` and `F. Procurement Planning Handoff` are too verbose in the default detail stream.

Current audit fields include many empty values:

```text
Submitted by —
Submitted at —
HoD approved by —
HoD approved at —
Finance approved by —
Finance approved at —
Rejected by —
Rejected at —
Returned by —
Returned at —
Cancelled by —
Cancelled at —
```

This is too much empty audit data in the main view.

## Recommendation

Default view should show a compact workflow summary:

```text
Workflow
Current stage: Draft
Planning status: Not planned
Next action: Submit for approval
```

Move detailed audit fields into the `Audit` tab or an expandable section:

```text
[View full workflow history]
```

Do the same for procurement planning handoff. In draft stage, show only:

```text
Planning handoff
Available after approval.
```

Do not show long explanatory text until the demand is approved.

---

# 28. Workbench Detail: Use Tabs Instead of A–F Continuous Sections

The A–F sections are clear but long. They force vertical scanning.

Use tabs in the detail panel:

```text
Overview | Items & Value | Review | Planning | Audit
```

Recommended mapping:

```text
A. Demand Summary          → Overview
B. Budget and Strategy     → Planning
C. Financial Summary       → Items & Value or Planning
D. Items Summary           → Items & Value
E. Workflow and Audit      → Review / Audit
F. Procurement Handoff     → Planning
```

Default tab should be `Overview`.

Overview should show only:

```text
Demand identity
Status chips
Requester / department
Required by date
Total requested
Next step
```

This will make the detail panel calmer.

---

# 29. Budget and Strategy Section Should Be Role-Aware

In the workbench detail, Budget and Strategy currently shows many fields:

```text
Budget line
Budget
Funding source
Reservation status
Strategic plan
Program
Sub-program
Output indicator
Performance target
```

This is useful, but should be interpreted differently depending on stage.

## Draft Demand

Show:

```text
Planning context
Not yet completed.
A planner can add budget and strategy linkage during review or planning preparation.
```

## Approved Demand

Show:

```text
Planning context
Strategy linkage: complete / incomplete
Budget linkage: complete / incomplete
Reservation: not reserved / reserved
```

## Planning Ready Demand

Show full linkage details.

This avoids overwhelming the requester and prevents planner-owned fields from looking like requester mistakes.

---

# 30. Recommended Updates to the Previous DIA Refactor

The previous DIA refactor is still valid, but strengthen it with these additional implementation rules:

1. **Use staged validation, not one universal required-field model.**

   - Draft save, submit for approval, approval, and planning readiness each have different required fields.

2. **Requester forms should not require planner-owned fields.**

   - Budget line, reservation status, and detailed strategy linkage should be optional before approval unless the organization explicitly requires requester-side coding.

3. **Move ************Items & Value************ before business justification.**

   - Users should state what they need before explaining why.

4. **Use a guided stepper or anchored navigation for the demand form.**

   - The section demarcation is good, but the form is long.

5. **Do not use a floating action bar if it breaks consistency with Strategy and Budget.**

   - Put workflow actions in the `Review` tab.
   - Put planning handoff actions in the `Planning` tab.
   - Keep only form-level actions in the separate form header.

6. **Replace A–F continuous detail sections with tabs or collapsible sections.**

   - Keep `Overview` calm and move audit/planning depth to tabs.

7. **Hide empty audit fields by default.**

   - Show workflow summary first; full history belongs in Audit.

8. **Make Planning Handoff conditional by state.**

   - Draft: unavailable after approval.
   - Approved: prepare handoff.
   - Planning Ready: show artefacts and links.

9. **Use role-aware labels.**

   - Example: `Can be completed by planner` instead of showing missing budget fields as hard errors.

10. **Preserve the existing compact workbench direction.**

- Left list, selected detail, lifecycle queue bar, and tab-based workflow actions are still appropriate.

---

# 31. Final Strengthened Recommendation

Implement DIA as a two-layer experience, but keep both layers inside the same module pattern:

```text
Workbench = manage demand cases and take workflow actions
Guided form = capture or edit demand data with staged validation
```

The guided form should not feel like a detached Frappe form or separate app. It should open inside the DIA workbench where possible, or as a module-owned workbench mode if full-screen editing is unavoidable.

Do not force all data to be present at the requester stage.

A good DIA flow should feel like this:

```text
Requester: what do you need, by when, and why?
Reviewer: is this justified and approvable?
Planner: how does it link to strategy, budget, and procurement planning?
System: what is the status, audit trail, and handoff readiness?
```

That separation will make the module easier to use and much more defensible while keeping the UI consistent with Strategy and Budget.

