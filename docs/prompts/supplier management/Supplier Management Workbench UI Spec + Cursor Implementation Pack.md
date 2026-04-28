Supplier Management Workbench UI Spec + Cursor Implementation Pack

**1\. PURPOSE (NON-NEGOTIABLE)**

Supplier Management is a WORKBENCH, not a dashboard.

**Primary objective:**

Review, approve, and manage supplier lifecycle, compliance, and eligibility.

**2\. PAGE STRUCTURE (CANONICAL LAYOUT)**

**2.1 Layout Model**

\------------------------------------------------------------

Header (Title + Actions)

\------------------------------------------------------------

KPI Row (clickable)

\------------------------------------------------------------

Queue Filters (primary control)

\------------------------------------------------------------

Search + Secondary Filters (collapsed)

\------------------------------------------------------------

\------------------------------------------------------------

| Supplier List (left) | Supplier Detail (right) |

\------------------------------------------------------------

👉 This MUST match:

-   Demand Intake
-   Procurement Planning

**3\. HEADER**

**3.1 Title**

Supplier Management

**3.2 Actions (top-right)**

| **Action** | **Visibility** | **Notes** |
| --- | --- | --- |
| New Supplier | Always | Primary |
| Import Suppliers | Optional | Later phase |

**4\. KPI ROW (CLICKABLE, NOT DECORATIVE)**

**4.1 KPI Cards**

| **KPI** | **Meaning** | **Filter Action** |
| --- | --- | --- |
| Registered | Total suppliers | All |
| Pending Review | Submitted + Under Review | Filter |
| Active | Approved + Active | Filter |
| Blocked | Suspended + Blacklisted | Filter |

**4.2 Rules**

-   No currency
-   No truncation
-   Clicking KPI → applies filter

**5\. QUEUE FILTER BAR (PRIMARY CONTROL)**

**5.1 Row 1 (ownership)**

My Work | All | Approved | Blocked

**5.2 Row 2 (state-driven)**

Draft | Submitted | Under Review | Returned | Active | Suspended | Blacklisted | Expired

**5.3 Behavior**

-   Multi-filter capable
-   Active filter highlighted
-   Drives left list

**6\. SEARCH + FILTERS**

**6.1 Search**

Search suppliers...

Searches:

-   supplier\_code
-   supplier\_name
-   contact email

**6.2 Filters (collapsed panel)**

| **Filter** | **Type** |
| --- | --- |
| Category | Multi-select |
| Compliance Status | Enum |
| Risk Level | Enum |
| Entity | Select |

**7\. MAIN WORK AREA**

**7.1 LEFT PANEL — SUPPLIER LIST**

**7.1.1 Structure**

Scrollable card list

**7.1.2 Card Design**

AfyaMed Supplies Ltd

SUP-KE-2026-0001

\[Submitted\] \[Incomplete\] \[High Risk\]

Category: Medical Equipment

Last Updated: 2026-04-20

**7.1.3 Required Fields**

| **Field** | **Required** |
| --- | --- |
| Supplier Name | Yes |
| Supplier Code | Yes |
| Approval Status | Yes |
| Compliance Status | Yes |
| Risk Level | Optional |
| Category | Optional |
| Last Updated | Yes |

**7.1.4 Visual Rules**

-   Selected card highlighted
-   High Risk → colored badge
-   Incomplete → warning indicator

**7.2 RIGHT PANEL — SUPPLIER DETAIL**

**7.2.1 Header**

AfyaMed Supplies Ltd

SUP-KE-2026-0001

\[Submitted\] \[Incomplete\] \[High Risk\]

**7.2.2 ACTION BAR (CRITICAL)**

Dynamic based on state.

**STATE → ACTION MATRIX**

| **Approval State** | **Actions** |
| --- | --- |
| Draft | Submit |
| Submitted | Approve, Return, Reject |
| Under Review | Approve, Return |
| Returned | Edit |
| Approved | Suspend, Blacklist |
| Suspended | Reactivate |
| Blacklisted | (No normal recovery) |

**Example:**

**Submitted:**

\[Approve\] \[Return\] \[Reject\]

**Active:**

\[Suspend\] \[Blacklist\]

**7.2.3 DETAIL SECTIONS**

**1\. Supplier Profile**

| **Field** |
| --- |
| Name |
| Code |
| ERPNext Supplier (link) |
| Contact Info |
| Registration Date |

**2\. Documents**

| **Field** |
| --- |
| Document Type |
| Status |
| Expiry |
| Verified By |

Actions:

-   Upload
-   Verify
-   Reject

**3\. Category Qualification**

| **Field** |
| --- |
| Category |
| Qualification Status |
| Valid Until |

**4\. Compliance Status**

| **Field** |
| --- |
| Overall Status |
| Missing Documents |
| Expired Documents |

**5\. Risk Profile**

| **Field** |
| --- |
| Risk Level |
| Risk Factors |

**6\. Activity Log**

| **Field** |
| --- |
| Action |
| User |
| Timestamp |

**8\. UX RULES (MANDATORY)**

**8.1 REMOVE**

-   ❌ Static “reference chips”
-   ❌ Documentation text on main page

**8.2 REQUIRE**

-   Every element must be:
    -   actionable
    -   or navigational

**8.3 CONSISTENCY**

Must match:

Demand Intake = Suppliers Intake equivalent

Planning = Suppliers lifecycle equivalent

**9\. GOVERNANCE IN UI**

**9.1 Approval visibility**

Always visible:

Approval Status: Submitted

Operational Status: Pending

Compliance Status: Incomplete

**9.2 Blocking logic**

Buttons disabled if:

-   Compliance incomplete
-   Required docs missing

**10\. CURSOR IMPLEMENTATION PACK**

**10.1 Page Definition**

Create Supplier Management Workbench page.

This is NOT a dashboard.

Must include:

\- KPI row (clickable)

\- Queue filter bar (2 rows)

\- Search input

\- Left panel supplier list

\- Right panel detail view

\- Contextual action bar

**10.2 Data Binding**

**Fetch suppliers**

get\_suppliers(filters)

**Fetch supplier detail**

get\_supplier\_detail(supplier\_code)

**Perform actions**

approve\_supplier()

return\_supplier()

reject\_supplier()

suspend\_supplier()

blacklist\_supplier()

reactivate\_supplier()

**10.3 UI Behavior**

\- Clicking KPI applies filters

\- Clicking queue filter updates list

\- Clicking supplier loads detail panel

\- Actions update state and refresh UI

**10.4 State-driven UI**

Render buttons dynamically based on approval\_status

**10.5 DO NOT IMPLEMENT**

\- Static status explanation sections

\- Non-clickable chips

\- Standalone summary pages

**11\. SMOKE TEST CONTRACT**

**Scenario 1: Review supplier**

Given supplier in Submitted

When reviewer selects supplier

Then Approve / Return buttons are visible

**Scenario 2: Approve supplier**

Given supplier is compliant

When Approve clicked

Then approval\_status = Approved

And operational\_status = Active

**Scenario 3: Block supplier**

Given supplier is active

When Suspend clicked

Then operational\_status = Suspended

**Scenario 4: Filter by KPI**

When user clicks Pending Review KPI

Then list shows only Submitted + Under Review

**12\. FINAL DESIGN PRINCIPLE**

This page is a decision engine, not a report.

**If you want next**

We can now:

👉 Align this with **Supplier API exposure model**  
👉 Or connect it directly to **Tender eligibility enforcement UI**

But do NOT implement this UI without enforcing this spec —  
otherwise you will regress into passive dashboards again.