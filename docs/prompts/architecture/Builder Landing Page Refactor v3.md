Builder Landing Page Refactor v3.docx

# The real issue now

**1\. Too many equal-weight controls**

You have:

-   Tabs (My Work / All / Approved / Rejected)
-   Queue chips (My Drafts, Planning Ready, etc.)
-   Search
-   Filters

All sitting together with **equal visual weight**

👉 The brain doesn’t know:

-   what to use first
-   what actually matters

**2\. No strong “entry point”**

Look at your empty state:

“My Drafts — No drafts in this queue”

That’s fine.

But visually:

-   nothing pulls the eye to the list area
-   nothing says “start here”

**3\. Control bar still feels like a “control surface”, not a “selector”**

It’s still too wide and too busy for what should be:  
👉 a simple queue selector

**The fix (this is the important part)**

You don’t need more compression.

👉 You need **hierarchy simplification**

**1\. Collapse the mental model: Tabs OR Queues — not both equally**

Right now you have two axes:

-   Tabs (My Work / All)
-   Queues (My Drafts / All Demands / Planning Ready...)

These compete.

**Fix:**

**Make Tabs = scope**

**Make Queues = primary selector**

Visually:

Tabs (small, secondary)

Queues (dominant)

**Implementation:**

**Tabs:**

-   reduce emphasis (lighter style)
-   smaller spacing
-   not bold/filled

**Queue chips:**

-   slightly larger
-   primary interaction
-   clearly “this is what you choose”

👉 This immediately reduces cognitive load

**2\. Turn queues into a single “active line”**

Right now queues wrap into multiple lines → messy

**Fix:**

-   show **1 row of primary queues**
-   overflow → dropdown (“More”)

Example:

My Drafts | All Demands | Planning Ready | Approved | More ▾

👉 This removes visual chaos

**3\. Move Search OUT of the queue flow**

Right now search is competing with queues.

**Fix:**

Place search:

-   top right of header OR
-   far right of tabs row (but visually separated)

👉 It should feel like a tool, not part of selection

**4\. Filters must become invisible until needed**

Right now:

-   “Filters” still draws attention

**Fix:**

-   icon only (funnel icon)
-   or subtle text button

NO inline presence unless active

When active:

-   show filter summary like:

Filters: Department = Health (x)

**5\. Pull the list UP even more**

This is the part you’re still feeling.

Right now:

Controls

↓

(empty feeling)

↓

List

**Fix:**

Reduce spacing so it becomes:

Controls

List immediately starts

Target:  
👉 **List starts within ~120–140px of top**

**6\. Strengthen the list as the primary element**

Right now your list feels passive.

**Make it feel active:**

-   slightly stronger border or elevation
-   slightly tighter card spacing
-   highlight first item when empty state resolves

**7\. Fix empty state positioning**

Right now:

“No drafts in this queue”

Feels like a dead end.

**Improve:**

-   center vertically within list panel
-   add CTA:
    -   “Create new demand”
    -   or “Switch queue”

**8\. Sidebar problem (important)**

Your sidebar still shows:

Procurement Templates

Risk Profiles

KPI Profiles

...

This is bleeding into the experience.

👉 Even though it’s “correct IA”, visually it’s noisy.

**Fix (small but powerful):**

Collapse “Settings” by default.

👉 Only show:

Procurement Home

Demand Intake & Approval

Procurement Planning

Settings ▾ (collapsed)

**What your page should feel like after this**

Instead of:

dashboard → filters → controls → maybe work

It should feel like:

queue → list → action

**The key mental shift**

👉 This is NOT a dashboard  
👉 This is NOT a report

👉 This is a **queue-based operational tool**

Everything should reinforce:

“Pick a queue → pick an item → act”

**If I had to give you just 5 changes**

Do these and you’ll feel the difference immediately:

1.  Make queues dominant, tabs secondary
2.  Reduce queues to one line + overflow
3.  Move search away from queues
4.  Hide filters until used
5.  Pull list up tighter + strengthen it visually

# Cursor Prompts

Refactor DIA and Procurement Planning workbench pages to a **queue-first interaction model**.

This is a visual hierarchy and interaction refinement.  
Do NOT change domain logic, queues, workflow states, permissions, or data structures.

Goal:  
Make the page feel like a **queue-driven operational tool**:  
→ Select a queue  
→ Select a record  
→ Take action

Reduce cognitive load by simplifying and prioritizing controls.

**1\. CORE PRINCIPLE**

The page must clearly communicate:

-   Queues = primary interaction
-   Tabs = secondary scope
-   Filters/Search = supporting tools
-   List/Detail = main work area

If controls compete visually with queues or data, the implementation is incorrect.

**2\. TABS VS QUEUES (HIERARCHY FIX)**

Current problem:  
Tabs and queues are visually equal.

Refactor:

**Tabs (secondary scope)**

-   My Work / All / Approved / Rejected
-   lighter visual style
-   reduced prominence (less contrast, less padding)

**Queues (primary selector)**

-   My Drafts
-   All Demands / All Packages
-   Planning Ready / Structured Packages etc.

Rules:

-   queues must be visually stronger than tabs
-   queues should feel like the main selection control

**3\. QUEUE BAR RESTRUCTURE**

Replace multi-line chip sprawl with a controlled single-line layout.

**Required:**

-   show ONE row of primary queues
-   overflow into dropdown: “More ▾”

Example:  
My Drafts | All Demands | Planning Ready | Approved | More ▾

Rules:

-   chip height: ~28px
-   gap: 8px
-   no wrapping into multiple rows unless absolutely necessary
-   avoid vertical expansion

**4\. SEARCH REPOSITIONING**

Search should NOT compete with queues.

Move search to:

-   far right of tabs row OR
-   top-right of control area (aligned with header action zone)

Rules:

-   visually separate from queues
-   treat as utility, not primary selector
-   width: ~240–320px

**5\. FILTERS REFACTOR (CRITICAL)**

Filters must become **invisible by default**.

**Replace:**

-   visible “Filters” section/block

**With:**

-   compact button or icon:  
    “Filters” or funnel icon

**Behavior:**

-   opens dropdown panel or modal
-   no vertical space consumed when collapsed

**When active:**

-   show summary inline:  
    Example:  
    “Filters: Department = Health ×”

Do NOT:

-   show full-width filter bar
-   reserve vertical space when not in use

**6\. REMOVE / DEMOTE HELPER TEXT**

Current:  
“All shows every queue for your role…”

Refactor:

-   remove OR
-   move to tooltip/info icon

Rules:

-   helper text must never push content downward
-   must not occupy a full row

**7\. CONTROL BAR COMPRESSION**

Final control bar should look like:

Row 1:

-   Tabs (left)
-   Search (right)

Row 2:

-   Queue chips (left)
-   Filters button (right)

Spacing:

-   Tabs → queues: 8–12px
-   Queues → list: ~16px

No extra rows allowed.

**8\. WORK AREA PRIORITY**

The list/detail area must feel like the main focus.

**Required:**

-   begins high on the page
-   immediately visible without scrolling
-   visually stronger than control bar

**Visual adjustments:**

-   slightly stronger border or elevation for list panel
-   tighter spacing between list items (12px)
-   clearer hover/selection states

**9\. EMPTY STATE IMPROVEMENT**

Current empty state feels passive.

Refactor:

-   vertically center content in list panel
-   add clear next step:
    -   “Create new demand”
    -   or “Switch queue”

Rules:

-   empty state should guide action, not just inform

**10\. SIDEBAR CLEANUP (SUPPORTING FIX)**

Settings items are visually noisy.

Required:

-   collapse “Settings” group by default
-   do not show all config items expanded

Visible sidebar should prioritize:

-   Procurement Home
-   Demand Intake & Approval
-   Procurement Planning

**11\. VISUAL PRIORITY ORDER (ENFORCE)**

1.  Queue selection (primary)
2.  List + detail (work area)
3.  KPI strip
4.  Tabs
5.  Search / filters
6.  Helper/meta text

If anything above is violated, adjust styling/spacing.

**12\. APPLY TO**

-   Demand Intake & Approval workbench
-   Procurement Planning workbench

Preserve:

-   queue definitions
-   workflow actions
-   role behavior

**13\. ACCEPTANCE CRITERIA**

Refactor is correct only if:

-   queues are visually dominant over tabs
-   queues fit in a single row (with overflow if needed)
-   search is repositioned and no longer competes with queues
-   filters are hidden by default (no full-width filter bar)
-   helper text no longer consumes vertical space
-   control bar is reduced to max 2 rows
-   list/detail area starts higher and feels primary
-   empty states guide action
-   page feels like a queue-driven tool, not a control-heavy dashboard

**14\. IMPLEMENTATION REPORT**

At the end report:

1.  queue layout changes
2.  tab styling changes
3.  search repositioning
4.  filter behavior changes
5.  rows removed from control area
6.  empty state improvements
7.  any remaining constraints preventing full queue-first model