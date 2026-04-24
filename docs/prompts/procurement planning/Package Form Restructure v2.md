Package Form Restructure v2

# Overview and Resolution

**What you got right ✅**

**1\. You avoided overloading the Package form**

That’s critical.

Demand Lines:

-   are **many**
-   are **editable in bulk**
-   require **context (budget, demand, grouping)**

Trying to manage them inside a static form would be a mess.

👉 Moving them to the **Planning workbench** is the correct architectural decision.

**2\. You enforced sequencing**

“Complete Definition and Template first”

This is **100% correct** because:

-   Template → defines structure
-   Method → defines procurement logic
-   Only then can you meaningfully assign demand

👉 This prevents garbage packages.

**What’s off ⚠️**

The issue is not the logic — it’s the **UX signaling**.

Right now:

-   The tab is clickable
-   But it contains no interaction
-   And shows a passive message

That creates **cognitive dissonance**:

“Why is this a tab if I can’t do anything here?”

**The real problem**

You’re mixing **form editing** and **workbench operations** in the same mental model.

👉 Demand Lines are **not form data**  
👉 They are **operational data**

That distinction needs to be clearer.

**Correct model (this is the key shift)**

**Package Form = Definition Layer**

-   What is this package?
-   How will it be procured?

**Planning Workbench = Execution Layer**

-   What demand goes into this package?
-   How is it structured?

**What to change (minimal, high-impact)**

**1\. Rename the tab**

Instead of:

Demand lines

Use:

Demand assignment

This subtly tells the truth:  
👉 “This is not where you edit them”

**2\. Replace passive guidance with an action**

Right now you say:

“After save, manage in workbench”

That’s weak.

**Replace with:**

Demand lines are managed in Procurement Planning.

\[ Save package to enable demand assignment \]

\[ Go to Planning Workbench \]

👉 Make it actionable, not informational.

**3\. Lock the tab until valid**

Don’t let users wander into a dead section.

**Behavior:**

-   If package not saved → tab disabled
-   If saved → tab shows:

Manage demand lines from Planning Workbench.

\[ Open Planning \]

**4\. (Optional but powerful) Show a summary**

Once demand is assigned (from workbench), show:

Demand lines: 5

Total value: 1,200,000

Source demands: 3

👉 This turns the tab into a **read-only summary**, not a dead page.

**What you should NOT do**

Do NOT:

-   Reintroduce demand line editing into the form
-   Add inline tables here
-   Try to “half-manage” demand in two places

That will break your architecture.

**Final verdict**

**Your approach is:**

✔ Architecturally correct  
✔ Scalable  
✔ Aligned with workbench model

**But currently:**

❌ Feels unfinished  
❌ Not clearly intentional to the user

**Clean version (recommended wording)**

Replace your current text with:

Demand Assignment

Demand lines are managed in Procurement Planning.

To assign demand to this package:

1\. Save the package

2\. Open Procurement Planning

3\. Select this package and assign demand lines

\[ Save package \] \[ Open Planning \]

# Package vs Workbench responsibility matrix

**Package Form vs Planning Workbench — Responsibility Matrix**

**Core rule**

**Package Form = define the package**  
**Planning Workbench = operate on packages and assign demand**

| **Area** | **Package Form** | **Planning Workbench** |
| --- | --- | --- |
| Package name | Edit | View |
| Package code | Auto-generated / view | View |
| Procurement plan | Select / view | Context selector |
| Template | Select | Apply / compare / review |
| Procurement method | Set / override with reason | Review / approve implications |
| Contract type | Set / derived | Review |
| Demand lines | Summary only | Add / remove / manage |
| Demand grouping | No | Yes |
| Estimated value | Derived / view | Review from lines |
| Schedule | Edit | Review / queue by readiness |
| Risk profile | Set / derived | Review / flag high-risk |
| KPI profile | Set / derived | Review |
| Decision criteria | Set / derived | Review |
| Vendor management profile | Set / derived | Review |
| Workflow status | View | Act on state |
| Submit / approve / ready actions | Limited | Primary action area |

**Specific rule for Demand Lines**

Demand Lines should **not** be edited inside the Package Form.

They should be:

-   assigned in the Planning Workbench
-   shown in the form as a read-only summary
-   linked back to source DIA records

**Package Form should show**

Demand Assignment

Demand lines are managed in Procurement Planning.

Assigned demands: 3

Total assigned value: KES 5,000,000

\[Open Planning Workbench\]

If unsaved:

Save this package before assigning demand lines.

\[Save Package\]

**Why this split is correct**

Package Form answers:

What is this package and how should it be procured?

Planning Workbench answers:

What approved demand belongs in this package, and what state is the package in?

Mixing those creates duplicate controls and later confusion.

# Cursor prompt

Refactor Procurement Package form responsibilities so the Package Form defines the package, while the Planning Workbench manages operational demand assignment.

Do not move demand-line editing into the form.

Rules:

1.  Package Form is responsible for:
    -   package name
    -   generated package code display
    -   procurement plan
    -   template
    -   method
    -   contract type
    -   schedule
    -   risk profile
    -   KPI profile
    -   decision criteria
    -   vendor management profile
    -   workflow status display
2.  Planning Workbench is responsible for:
    -   assigning approved DIA demand to packages
    -   removing demand lines
    -   reviewing package queues
    -   acting on package workflow states
3.  In the Package Form, rename “Demand lines” tab to “Demand assignment”.
4.  If package is not saved:
    -   show message: “Save this package before assigning demand.”
    -   show Save Package action if possible
5.  If package is saved:
    -   show read-only summary:
        -   assigned demand count
        -   total assigned value
        -   source demand count if different
    -   show action: “Open Planning Workbench”
6.  Do not show editable demand-line tables in the Package Form.
7.  Do not duplicate demand-line management in both places.

Acceptance criteria:

-   Package Form no longer feels like a dead tab
-   Demand assignment responsibility is clear
-   Planning Workbench remains the operational place for demand-line management
-   Package Form shows summary only
-   No domain or workflow logic changes