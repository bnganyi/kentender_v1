🧩 BUDGET LANDING — FINAL SPEC

**1\. Page Purpose**

The Budget Landing page is a **control dashboard** to:

-   view all budgets
-   understand allocation status
-   select a budget
-   enter allocation workflow (builder)

**2\. Layout Structure (same system as Strategy)**

HEADER

OVERVIEW STRIP

MAIN WORKSPACE (master-detail)

ACTION CARDS

Consistency across modules is critical.

**3\. HEADER**

Budget Management

Define and manage budget allocations linked to strategic plans.

-   no buttons here
-   clean and informational only

**4\. OVERVIEW STRIP (metrics)**

**Metrics**

Active Budgets | Draft Budgets | Total Budget Amount | Allocated %

**Example**

Active: 1 Draft: 3 Total: 25,000,000 Allocated: 62%

**Behavior**

-   computed across all budgets
-   updates dynamically
-   Allocation % = (allocated / total)

**UI**

-   inline or card-style
-   NOT a grey slab

**5\. MAIN WORKSPACE**

**Two-column layout**

Left: Budgets list (35%)

Right: Budget Details (65%)

**5A. LEFT PANEL — Budgets**

**Title**

Budgets

**Each item shows**

Budget Name

Fiscal Year (or period)

Status (Draft / Active)

Optional (recommended later):

Allocation progress (e.g. 62%)

**Selection behavior**

-   click → highlight
-   loads details on right
-   first item auto-selected

**Empty state**

No budgets yet.

Create one to begin.

**5B. RIGHT PANEL — Budget Details**

**If selected**

**Section 1 — Budget Summary**

Budget Name

Status

Fiscal Year

Linked Strategic Plan

**Section 2 — Allocation Overview**

Total Budget

Allocated Amount

Remaining Amount

Allocation %

**Section 3 — Structure**

Programs: X

Allocated Programs: X

Unallocated Programs: X

**Section 4 — Actions**

\[ Open Budget Builder \]

\[ Edit Budget \]

**If no selection**

Select a budget to view details.

**6\. ACTION CARDS**

**Card 1 — Planning**

Planning

\+ New Budget

Link to Strategic Plan (implicit in creation)

**Card 2 — Allocation**

Allocation

Open Budget Builder

Review Allocation Status

**Rules**

-   grouped actions
-   not scattered buttons
-   visually consistent with Strategy

**7\. NAVIGATION RULES**

-   Page: /desk/budget-management
-   Builder: /desk/budget-builder/{budget}
-   No hidden navigation

**8\. STATE HANDLING**

**A. No budgets**

-   empty state left + right
-   action cards visible

**B. Budgets exist**

-   first auto-selected
-   details populated

**C. Partial allocation**

-   clearly visible in metrics

**D. Fully allocated**

-   allocation % = 100%
-   remaining = 0

**9\. DATA REQUIREMENTS**

Backend must provide:

-   Budget list
-   Status
-   Fiscal year
-   Linked strategic plan
-   Total amount
-   Allocated amount
-   Program count
-   Allocation distribution

**10\. VISUAL SYSTEM**

Same as Strategy:

✔ cards  
✔ spacing consistency  
✔ minimal color usage

**Avoid**

❌ accounting-heavy UI  
❌ ledger-style tables  
❌ ERP clutter

**11\. UX ACCEPTANCE CRITERIA**

User should:

**✔ See all budgets immediately**

**✔ Understand allocation status instantly**

**✔ Select and inspect a budget**

**✔ Enter builder in one click**

**✔ Create new budget easily**

**12\. CURSOR IMPLEMENTATION PROMPT**

Implement the Budget Management landing page as a dashboard.

Layout:

1.  Header:

-   Title: "Budget Management"
-   Subtitle: "Define and manage budget allocations linked to strategic plans."

1.  Overview strip:

-   Show:
    -   Active Budgets
    -   Draft Budgets
    -   Total Budget Amount
    -   Allocation %
-   compute dynamically

1.  Main workspace (2 columns):

Left (35%):

-   Title: "Budgets"
-   List all budgets
-   Each item shows:
    -   name
    -   fiscal year
    -   status
-   selectable list
-   highlight selected row

Right (65%):

If selected:

-   Show:
    -   name
    -   status
    -   fiscal year
    -   linked strategic plan
    -   Total Budget
    -   Allocated Amount
    -   Remaining Amount
    -   Allocation %
    -   Programs count
    -   Allocated programs
    -   Unallocated programs
-   Buttons:
    -   "Open Budget Builder"
    -   "Edit Budget"

If no selection:

-   Show empty message

1.  Action cards:

Planning:

-   New Budget

Allocation:

-   Open Budget Builder
-   Review Allocation Status (placeholder)

1.  Behavior:

-   auto-select first budget
-   clicking updates detail panel
-   builder navigation works

1.  Styling:

-   use cards, not full grey backgrounds
-   consistent spacing
-   no heavy tables

Add test ids for:

-   overview metrics
-   budget list
-   selected budget
-   detail panel
-   action buttons

Acceptance:

-   matches Strategy layout pattern
-   clear allocation visibility
-   minimal scrolling

## Sample Landing Pages

![](./budget-landing-page-refactor_images/image-001.png)

![](./budget-landing-page-refactor_images/image-002.png)

![](./budget-landing-page-refactor_images/image-003.png)