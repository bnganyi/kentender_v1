# Procurement Workbench Layout Spec (v1.0)

# Overview

This governs:

-   Demand Intake & Approval
-   Procurement Planning
-   All future workbench-style modules

**1\. Page Anatomy (Canonical Structure)**

Every workbench page must follow this structure:

\[ A \] Page Header

\[ B \] KPI Strip

\[ C \] Control Bar (Tabs + Queues + Search + Filters)

\-----------------------------------------------

\[ D \] Work Area (Master–Detail Split)

**Critical rule:**

👉 **\[D\] must start within first viewport (above the fold)**

**2\. Spacing System (MANDATORY)**

Use a strict spacing scale:

| **Token** | **Value** | **Usage** |
| --- | --- | --- |
| XS | 8px | inside components |
| SM | 12px | tight grouping |
| MD | 16px | default spacing |
| LG | 24px | section separation |
| XL | 32px | rare (avoid overuse) |

**Enforcement rules:**

-   No arbitrary spacing (no 20px, 28px, etc.)
-   Prefer **16px default**
-   Avoid stacking multiple LG/XL gaps

**3\. Section-by-Section Spec**

**A. Page Header**

**Structure:**

Title (left) Primary Action (right)

Subtitle (optional)

**Spacing:**

-   Top padding: **16px**
-   Title → subtitle: **8px**
-   Header → KPI strip: **16px**

**Rules:**

-   Keep header **visually light**
-   No large empty vertical padding
-   Actions (e.g. “New Demand”) aligned right

**B. KPI Strip**

**Layout:**

-   3–4 cards in a single row
-   Equal height
-   No wrapping if avoidable

**Card spec:**

-   Padding: **12px–16px**
-   Title → value: **8px**
-   No excessive internal whitespace

**Height target:**

👉 **~72–88px max**

**Number rules:**

-   No truncation ever
-   Currency NOT repeated inside each card
-   Use:
    -   10,225,000 (not KES 10,225,000 in every card)
-   Add a single note:
    -   “All monetary figures in KES”

**Spacing:**

-   KPI strip → control bar: **16px**

**C. Control Bar (CRITICAL FIX AREA)**

This replaces your current “filters block”.

**C1. Layout (single compact band)**

Tabs (left)

Queues (left, below or inline)

Search (right)

Filters button (right)

**Preferred compact layout:**

Row 1: Tabs

Row 2: Queues (left) Search + Filters (right)

**C2. Component rules**

**Tabs:**

-   Height: ~32px
-   Spacing between: **8px**

**Queue chips:**

-   Height: ~28px
-   Wrap allowed
-   Gap: **8px**

**Search:**

-   Height: **32–36px**
-   Width: 240–320px
-   Right-aligned

**Filters:**

-   NOT a full-width bar
-   Use:
    -   button: “Filters”
    -   or icon + label

**C3. Filters behavior**

Default:

-   collapsed

On click:

-   dropdown panel OR modal

Spacing when collapsed:  
👉 **NO extra vertical block**

**C4. Remove visual weight**

Controls must:

-   have **no container background**
-   no heavy borders
-   no large padding blocks

👉 This is a toolbar, not a section

**C5. Spacing**

-   Tabs → queues: **8–12px**
-   Queues → work area: **16px**

**D. Work Area (Master–Detail)**

This is the **primary visual focus**.

**D1. Layout**

| List panel (left) | Detail panel (right) |

**Split:**

-   Left: **30–40%**
-   Right: **60–70%**

**D2. Positioning**

👉 Must begin high on page  
👉 Should feel like “main content”, not secondary

**D3. Height**

-   Min visible height: **~400–500px**
-   Prefer:
    -   fixed container height
    -   internal scroll (not page scroll first)

**D4. List panel**

**Card spacing:**

-   Gap between cards: **12px**
-   Padding per card: **12–16px**

**Visual hierarchy:**

-   Title (strong)
-   Metadata (muted)
-   Status chips (compact)

**D5. Detail panel**

**Sections:**

-   Use section headers (A, B, C…)
-   Spacing between sections: **16–24px**

**Content:**

-   Avoid large empty text blocks
-   Use 2-column layout where possible

**4\. Global Density Rules**

**Rule 1: No stacked “full-width blocks”**

Avoid:

\[ KPI box \]

\[ Filters box \]

\[ Search box \]

Instead:

KPI strip

Control bar (inline)

Work area

**Rule 2: Controls < Data**

Visual priority must always be:

Data > Controls > Metadata

If controls dominate visually → it’s wrong

**Rule 3: First screen = usable**

User should:

-   see list items immediately
-   click something immediately

No scrolling required to begin work

**Rule 4: Collapse secondary elements**

Always collapsed by default:

-   Filters
-   Advanced controls
-   Helper text

**5\. Typography Scale (Quick Spec)**

| **Element** | **Size** | **Weight** |
| --- | --- | --- |
| Page title | 20–24px | Medium |
| KPI value | 18–20px | Medium |
| Section headers | 14–16px | Medium |
| Body text | 13–14px | Regular |
| Metadata | 12–13px | Muted |

**6\. Visual Hierarchy Rules**

**Primary focus:**

-   List + Detail

**Secondary:**

-   KPI strip

**Tertiary:**

-   Controls

**Lowest:**

-   helper text / metadata

**7\. Anti-patterns (Ban These)**

❌ Full-width filter containers  
❌ Repeating currency everywhere  
❌ Large vertical gaps between every section  
❌ Helper text pushing content down  
❌ Multiple stacked control rows  
❌ Data appearing below the fold

**8\. Target Outcome**

After applying this spec:

-   Page feels **immediate**
-   Data appears **early**
-   Controls feel **lightweight**
-   KPIs are **informative but not dominant**
-   No truncation or wasted space

**9\. One-line mental model**

👉 **“This is a workbench, not a report page.”**

# Cursor Prompts

Refactor DIA and Procurement Planning workbench layouts to follow the Procurement Workbench Layout Spec v1.0.

This is a layout and visual hierarchy refactor only.  
Do NOT change domain logic, workflow states, queue semantics, permissions, services, or seed data.

Goal:  
Make the actual master-detail work area visually dominant and higher on the page.  
Controls should support the work, not compete with it.

**1\. CANONICAL PAGE STRUCTURE**

Every workbench must follow:

1.  Page Header
2.  KPI Strip
3.  Compact Control Bar
4.  Master-detail Work Area

The master-detail work area must start within the first viewport wherever reasonably possible.

**2\. PAGE HEADER**

Compress the header.

Rules:

-   top padding around 16px
-   title to subtitle spacing around 8px
-   header to KPI strip around 16px
-   primary action remains top-right
-   no large vertical empty space

Do not remove the title, subtitle, or primary action.

**3\. KPI STRIP**

Keep KPI cards but make them compact.

Rules:

-   3–4 cards per row
-   target card height around 72–88px
-   padding around 12–16px
-   no excessive internal whitespace
-   no number truncation ever

Currency rule:

-   do not repeat currency in every card
-   assert currency once with text such as:  
    “All monetary figures in KES”
-   card values should show full readable numbers, e.g.:  
    10,225,000  
    not KES 10,225,0...

**4\. CONTROL BAR — REPLACE HEAVY FILTER AREA**

The current filter/control area is too visually heavy.

Replace the full-width filter/control block with a compact toolbar pattern.

Preferred structure:

Row 1:

-   top-level tabs on the left

Row 2:

-   queue chips on the left
-   search input and Filters button on the right

Rules:

-   no large container background
-   no heavy bordered filter box
-   no full-width collapsed filter bar
-   filters should be a small button: Filters
-   filters open as dropdown/panel/modal only when clicked
-   collapsed filters must consume no extra vertical block
-   helper text should be removed, reduced, or moved into tooltip/info icon

**5\. CONTROL DIMENSIONS**

Use compact controls:

-   tab height: about 32px
-   queue chip height: about 28px
-   chip gap: about 8px
-   search height: 32–36px
-   search width: 240–320px
-   spacing between tabs and queues: 8–12px
-   spacing from control bar to work area: about 16px

Do not create multiple stacked full-width control rows.

**6\. WORK AREA**

Make the master-detail area visually dominant.

Rules:

-   work area begins immediately after compact control bar
-   list/detail split should feel like main content
-   left panel around 30–40%
-   right panel around 60–70%
-   min visible height around 400–500px
-   prefer internal scroll inside list/detail panels instead of pushing whole page down

**7\. SPACING SCALE**

Apply a consistent spacing rhythm:

-   8px: inside compact controls
-   12px: tight grouping
-   16px: default spacing
-   24px: major section separation
-   avoid 32px+ except rare cases

Do not stack multiple large gaps.

**8\. VISUAL PRIORITY RULE**

The visual priority must be:

1.  Data / work area
2.  KPIs
3.  Controls
4.  Helper text / metadata

If the control area looks more important than the list/detail area, the implementation is wrong.

**9\. APPLY TO THESE PAGES**

Apply this pattern to:

1.  Demand Intake and Approval workbench
2.  Procurement Planning workbench

Preserve each page’s existing business semantics:

-   DIA queues stay DIA queues
-   Procurement Planning queues stay planning queues
-   actions remain role/state-aware

**10\. ACCEPTANCE CRITERIA**

The refactor is correct only if:

-   header is compact
-   KPI cards are compact and aligned
-   KPI numbers never truncate
-   repeated currency is removed/reduced
-   filters are no longer a heavy full-width section
-   queue chips and search are arranged as a compact toolbar
-   helper text no longer pushes content down
-   master-detail area begins higher on the page
-   data area feels visually dominant
-   no workflow/permission/domain behavior changes

At the end report:

1.  files/components changed
2.  header compression changes
3.  KPI/card formatting changes
4.  filter/control bar changes
5.  work-area height/position changes
6.  any remaining constraints preventing full compliance