Kentender UI System Pattern v1.0

**Kentender UI System Pattern v1.0**

**1\. Design Philosophy (Non-negotiable)**

Every screen must feel like:

A structured workbench, not a long form

That means:

-   minimal vertical scroll
-   clear hierarchy
-   role-aware surfaces
-   read-heavy, not input-heavy
-   actions close to context

**2\. Page Types (Standardized)**

Every module must use one of these patterns:

**2.1 Landing / Workbench Page**

Used by:

-   Strategy
-   Budget
-   DIA

Structure:

Header

KPI Strip

Primary Work Area (master-detail OR cards)

Secondary Actions (minimal)

**2.2 Builder / Editor Page**

Used by:

-   Budget Builder
-   DIA Builder

Structure:

Header (with actions)

Summary strip (optional)

Master-detail (left selector + right editor)

**2.3 Review / Approval Page (can be inline in workbench)**

Used by:

-   DIA approvals
-   future Procurement approvals

Structure:

Identity header

Sectioned detail view

Top-right actions

Audit + workflow section

**3\. Layout System**

**3.1 Core Rule: Two-Column Default**

If a section has structured fields:  
→ use 2-column layout

Only use full-width for:

-   long text
-   tables
-   complex controls

**3.2 Section Pattern**

Every section must follow:

\[Section Title\]

\[Two-column grid OR full-width content\]

No mixed clutter.

**3.3 Identity Header (Required Everywhere)**

Top of every detail/editor panel:

Primary Title (bold)

Secondary line (muted metadata)

Badges (status, priority)

Actions (right-aligned)

Example:

FY2027 Budget

MOH-SP-2026-0011 · KES · Draft

\[Approve\] \[Edit\]

**4\. Field Rendering Rules**

**4.1 Strict rule**

| **Field Type** | **Render As** |
| --- | --- |
| Editable | Input |
| Read-only | Display row |
| Derived | Display row |
| System fields | Hidden or audit section |

**4.2 Display Row Pattern**

Instead of:  
\[ grey disabled input \]

Use:

Label

Value

This alone will dramatically improve perceived quality.

**4.3 Text Fields**

| **Type** | **Behavior** |
| --- | --- |
| Notes | small by default, expand on focus |
| Justification | full-width but compact |
| Long text | avoid giant textareas |

**5\. Lists (Left Panel / Tables)**

**5.1 Row Hierarchy**

Each row must have:

Primary: Title

Secondary: ID · Context

Tertiary: Key metrics

Optional: 1–2 meaningful badges

**5.2 Badge Rules**

Only show badges when meaningful:

Allowed:

-   Status (Draft, Submitted, Approved)
-   Exception (Emergency, Unplanned)
-   Critical priority

Avoid:

-   Default-state badges like “Allocated”

**5.3 Anti-pattern**

❌ Badge overload  
❌ Repeating same info as text + badge  
❌ Equal visual weight for all metadata

**6\. Actions**

**6.1 Placement**

Primary actions must be:

-   top-right of page OR
-   top-right of detail panel

Never:

-   only at bottom of long form

**6.2 Action Hierarchy**

| **Type** | **Style** |
| --- | --- |
| Primary | solid |
| Secondary | outline |
| Destructive | subtle red |

**6.3 Contextual Actions**

Only show valid actions for:

-   role
-   state

No disabled clutter.

**7\. KPI / Summary Cards**

**7.1 Rules**

-   3–5 cards max per row
-   consistent sizing
-   clear labels (no ambiguity)
-   aligned formatting

**7.2 Label Clarity Rule**

Avoid:

-   “Remaining”
-   “Available”

Prefer:

-   Line Unallocated
-   Available for Reservation

**8\. Section Prioritization**

Every page must follow this order:

1.  Identity
2.  Core data
3.  Strategic context
4.  Financial context
5.  Items / structure
6.  Workflow / audit
7.  Exceptions (conditional)

**9\. Conditional Visibility**

Fields must appear ONLY when relevant.

Examples:

| **Scenario** | **Show** |
| --- | --- |
| Emergency demand | Emergency justification |
| Unplanned demand | Exception justification |
| Budget reserved | Reservation info |

Avoid empty placeholders.

**10\. Density Rules**

**Target:**

-   No excessive vertical stacking
-   Sections fit within viewport where possible

**Techniques:**

-   two-column layout
-   collapse low-priority sections
-   reduce textarea size
-   remove redundant fields

**11\. Navigation Consistency**

Every builder/editor must have:

-   clear “Back to X” button (top-right or top-left)
-   breadcrumb path

Example:

Budget Management / Budget Builder

**12\. Visual Language**

**Required consistency across modules:**

-   spacing scale
-   typography hierarchy
-   card style
-   button style
-   badge style
-   grid system

**13\. Anti-Patterns (Must Avoid)**

❌ Long vertical forms  
❌ Disabled grey inputs everywhere  
❌ Badge overload  
❌ Duplicate information  
❌ Bottom-only actions  
❌ Unclear financial terminology  
❌ Showing all fields all the time

**14\. Acceptance Checklist (Global)**

Every new page/module must pass:

-   Uses standard page type (Workbench / Builder / Review)
-   Has identity header
-   Uses two-column layout where applicable
-   Read-only fields are display rows (not disabled inputs)
-   Actions are accessible at top
-   Lists are clean and scannable
-   Badges are minimal and meaningful
-   Terminology is unambiguous
-   Sections are logically ordered
-   Page feels compact, not stretched

**15\. Cursor Enforcement Prompt**

Use this whenever building/refactoring UI:

Ensure the UI strictly follows the Kentender UI System Pattern v1.0.

Key requirements:

-   Use the correct page type (Workbench, Builder, or Review)
-   Include an identity header at top
-   Use two-column layout for structured sections
-   Render read-only fields as display rows (not disabled inputs)
-   Keep actions at top-right, not only at bottom
-   Minimize vertical stacking
-   Avoid unnecessary badges (only show meaningful ones)
-   Ensure lists are clean and scannable
-   Use clear, unambiguous terminology for financial fields
-   Show conditional fields only when relevant

Do NOT:

-   create long single-column forms
-   render read-only data as grey input boxes
-   overload UI with badges or redundant metadata

At the end, report:

1.  which pattern type the page uses
2.  where two-column layouts were applied
3.  which fields were converted to display rows
4.  how action placement was improved
5.  any deviations from the pattern and why

**Final perspective**

You now have:

-   **Domain rigor** (PRDs, workflows, governance)
-   **Data rigor** (Budget Lines, Reservations)
-   **Service rigor** (control layer)
-   **UI rigor** (this pattern)

That combination is what produces a **world-class system**, not just a functional one.

**Next move (important)**

Before touching Procurement:

👉 Apply this UI pattern to:

-   Budget Builder (you’re already doing it)
-   DIA (next)

Once those two are consistent:  
→ every future module becomes faster and cleaner to build