Procurement Workbench Refactor

**What’s actually wrong**

**1\. The Plan is not acting like a “container”**

Right now:

-   Plan
-   KPIs
-   Packages

All sit visually at the same level.

👉 So the brain reads:

“These are all just sections”

Instead of:

“This plan governs everything below”

**2\. The Plan block is visually weak**

The red-box area:

-   looks like a card
-   same style as everything else
-   no dominance
-   no structure

👉 It doesn’t feel like:

-   a **header**
-   or a **context**
-   or a **control layer**

**3\. You’re mixing 3 responsibilities**

On one screen you currently have:

1.  **Plan context (what plan am I in?)**
2.  **Plan actions (submit plan)**
3.  **Package work (list + detail)**

All stacked, but not separated.

👉 That’s why it feels like “too much”

**The fix (don’t remove — separate and elevate)**

You don’t need fewer features.

👉 You need **clear layers**

**The correct mental model**

LEVEL 1: PLAN (context + control)

LEVEL 2: PLAN METRICS (KPIs)

LEVEL 3: PACKAGE WORK (queues + list + detail)

Right now you have:

everything = same level

**Fix it cleanly (non-drastic)**

**1\. Turn the Plan into a “Context Bar” (not a card)**

Your current plan block should NOT look like a content card.

👉 It should behave like a **sticky context header**

**Replace this:**

\[ big card with plan name + submit \]

**With this:**

PP-MOH-2026 · FY2026 Procurement Plan · Ministry of Health \[Draft\] \[Submit Plan\]

**Styling:**

-   full-width
-   very light background OR subtle divider
-   horizontal layout
-   compact height (~48–56px)

👉 This makes it feel like:

“You are inside this plan”

**2\. Separate Plan actions from Package work**

Right now:

-   “Submit plan” sits in the same visual group as everything else

👉 That’s wrong.

**Fix:**

Keep actions in the **context bar**, not inside a block.

So:

\[ Plan name \] \[ Submit Plan \]

Not:

\[ card \]

Submit button inside

**3\. Add visual separation BEFORE KPIs**

Right now:  
Plan → KPIs feel blended.

**Add:**

-   a subtle divider
-   OR 16–24px spacing + lighter background change

👉 So it becomes:

Context Bar

\--------------------

KPI Strip

**4\. Make KPIs clearly “Plan-level”**

Right now KPIs look generic.

**Improve clarity:**

Add label:

Plan Summary

Or subtle grouping.

👉 This tells user:

“These metrics belong to the plan, not packages”

**5\. Then clearly separate PACKAGE WORK**

After KPIs:

\--------------------

Package Work

You don’t even need a heavy label — just spacing + structure.

**6\. You are NOT doing too much — but you were mixing layers**

Let’s be precise:

**✔ Correct to have:**

-   Plan context
-   Plan KPIs
-   Package work

**❌ Incorrect to:**

-   render them all as equal “cards”

**7\. One small but powerful improvement**

**Add subtle “Plan scope awareness”**

In package cards:

You already show:

-   package name
-   value
-   tags

👉 Add (lightly):

-   plan code or FY context (small, muted)

This reinforces:

“These belong to this plan”

**8\. If you want a cleaner mental split (optional)**

You could introduce:

**Tab inside Procurement Planning:**

Packages | Plan Details

But honestly:  
👉 You don’t need this yet

You can fix 90% with visual hierarchy alone.

**Final simplified structure**

After fix:

\[ PLAN CONTEXT BAR \] ← strong identity, not a card

\[ KPI STRIP \] ← clearly plan-level

\[ QUEUE + CONTROLS \] ← package filtering

\[ LIST | DETAIL \] ← actual work

**The key principle**

👉 **Context ≠ Content**

-   Plan = context (light, always visible)
-   Packages = content (heavy, interactive)

**Bottom line**

You’re not overloading the page.

You’re just:  
👉 **not telling the user what is context vs what is work**

Fix that, and the whole thing will “click”.

# Cursor prompt

Refactor the Procurement Planning top area so the Procurement Plan behaves as a clear context layer, not as another content card.

This is a layout/hierarchy refactor only.  
Do NOT change Procurement Planning domain logic, package logic, workflow states, permissions, or services.

Current problem:

-   the Plan area visually blends into KPI cards and package work
-   Plan, KPIs, and Packages appear as equal sections
-   users cannot immediately tell what is plan context versus package work

Goal:  
Create a clear hierarchy:

1.  Plan Context Bar
2.  Plan Summary KPIs
3.  Package Work controls
4.  Package List + Detail

**1\. CONVERT PLAN CARD TO PLAN CONTEXT BAR**

Replace the current large plan card/block with a compact horizontal context bar.

**Content:**

Left side:

-   Plan code
-   Plan name
-   fiscal year
-   procuring entity

Right side:

-   status badge
-   valid plan-level action, e.g. Submit Plan

Example:

PP-MOH-2026 · FY2026 Procurement Plan · 2026 · Ministry of Health \[Draft\] \[Submit Plan\]

**Styling:**

-   compact height, approximately 48–56px
-   full width of content area
-   subtle background or subtle bottom border
-   do NOT style it like a normal content card
-   do NOT give it the same visual weight as package/list/detail cards

Intent:  
The bar should communicate:  
“You are working inside this plan.”

**2\. PLAN ACTION PLACEMENT**

Move plan-level actions into the context bar.

Examples:

-   Submit Plan
-   Approve Plan
-   Return Plan
-   Reject Plan

Rules:

-   only show valid actions for current role/state
-   keep actions right-aligned
-   do not place plan actions inside package work area
-   do not mix plan actions with package actions

**3\. KPI STRIP AS PLAN SUMMARY**

Make the KPI strip explicitly read as plan-level summary.

**Add subtle label if helpful:**

-   Plan Summary

Do not over-style it.

**KPI cards remain:**

-   Total Packages
-   Total Planned Value
-   Pending Approval
-   High-Risk Packages

Rules:

-   KPI cards should sit below the context bar
-   spacing between context bar and KPI strip should be clear but compact
-   KPI cards should not visually merge with the context bar

**4\. PACKAGE WORK SEPARATION**

After the KPI strip, visually transition into package work.

Required:

-   package tabs/queues/search belong to package work, not plan context
-   package list/detail should remain the dominant working area
-   no plan-level buttons should appear inside package work controls

If helpful, add a subtle section label:

-   Package Work  
    or omit the label if spacing and layout make hierarchy clear.

**5\. SPACING / HIERARCHY**

Use clear but compact hierarchy:

-   Page header → Plan context bar: 12–16px
-   Plan context bar → KPI strip: 12–16px
-   KPI strip → package controls: 12–16px
-   Package controls → package list/detail: 12–16px

Avoid large vertical gaps.  
Avoid stacked card-like sections with equal weight.

**6\. VISUAL RULE**

The hierarchy must read as:

Context: Plan bar  
Summary: KPI strip  
Work: Package queues + list/detail

If the plan bar looks like just another package/content card, the refactor has failed.

**7\. DO NOT CHANGE**

Do NOT change:

-   Procurement Plan fields
-   Procurement Package fields
-   package queues
-   package states
-   plan workflow logic
-   package workflow logic
-   permissions
-   services
-   seed data

This is visual hierarchy only.

**8\. ACCEPTANCE CRITERIA**

The refactor is correct only if:

-   Plan is shown as a compact context bar, not a large card
-   Plan-level actions are right-aligned inside the plan context bar
-   KPI cards clearly read as plan summary
-   Package controls clearly belong to package work
-   Plan actions and package actions are not mixed
-   The page hierarchy reads: Plan → Summary → Package Work
-   The package list/detail remains the dominant working area
-   No business logic or workflow behavior changed

At the end report:

1.  files/components changed
2.  how the plan card was converted to a context bar
3.  where plan-level actions now live
4.  how plan/package hierarchy is visually separated
5.  any remaining hierarchy issues