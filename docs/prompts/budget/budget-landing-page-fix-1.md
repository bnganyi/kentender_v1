Budget Landing Page Fix

**✅ What’s working (keep this)**

**1\. Structure is finally correct**

-   Left: **Budget list**
-   Right: **Detail panel**
-   Top: **KPIs**

👉 This matches how ERPNext does it. Good.

**2\. Data density is improving**

You’ve moved away from empty space:

-   KPIs → useful
-   Summary → useful
-   Allocation → useful

👉 This is the right direction.

**3\. Context linkage (important win)**

-   Strategic plan shown
-   Fiscal year shown
-   Currency shown

👉 This anchors the budget properly. Keep it.

**⚠️ What’s still off (this is where it becomes “serious”)**

**1\. ❌ KPIs are visually broken**

Right now:

-   Numbers are wrapping badly (17,000,00 0.00)
-   No hierarchy
-   No emphasis

**Fix (strict)**

Make KPIs into **proper cards**

\[ Active Budgets \]

0

\[ Draft Budgets \]

2

\[ Total Budget \]

KES 17,000,000

\[ Allocation \]

82.4%

👉 Big number, small label. Not inline text.

**2\. ❌ Right panel is too “text-blocky”**

Everything looks like:

label → value → label → value

No visual grouping.

**Fix: enforce sections as cards**

\[ Budget Summary \]

\- Fiscal Year

\- Strategic Plan

\- Status

\[ Allocation Overview \]

\- Total

\- Allocated

\- Remaining

\- %

\[ Structure \]

\- Programs

\- Allocated

\- Unallocated

\[ Actions \]

\[ Open Builder \] \[ Edit \]

👉 Each should be a **card**, not loose text.

**3\. ❌ Left panel (Budget list) is weak**

Problems:

-   No visual hierarchy
-   Status badge is okay but not strong
-   Years are not clearly secondary

**Fix**

Each item should look like:

FY2027 Budget

2027

\[DRAFT\]

But with:

-   **bold title**
-   muted year
-   right-aligned status pill

👉 Also add hover + selected state contrast

**4\. ❌ Missing critical CTA hierarchy**

Right now:

-   “Open Budget Builder” is buried
-   “Edit Budget” looks equal weight

This is wrong.

**Fix**

Primary action must be:

\[ Open Budget Builder \] ← primary (black)

\[ Edit Budget \] ← secondary

👉 Builder is the core workflow. Make it obvious.

**5\. ❌ Bottom section is weak / unnecessary**

Planning

Allocation

This is:

-   redundant
-   low-value
-   visually disconnected

**Decision:**

👉 Remove entirely OR convert into real navigation cards later

For now: **delete it**

**6\. ❌ No “New Budget” primary CTA**

ERP pages ALWAYS have a clear create action.

**Fix**

Add:

Top-right or below header:

\[ + New Budget \]

👉 Don’t bury creation in sub-sections

**7\. ❌ No empty/edge states**

What happens when:

-   no budgets?
-   no allocations?

Right now → unclear.

**Fix**

Add:

-   empty list state
-   empty allocation message

**8\. ⚠️ Visual polish gap (this is subtle but important)**

Compared to ERPNext:

-   spacing is inconsistent
-   typography hierarchy is flat
-   sections don’t “feel” separated

**Fix checklist:**

-   consistent vertical spacing (16–24px)
-   section titles slightly bolder
-   cards with light border or subtle shadow

**🧠 Big Picture Feedback (important)**

Right now your page is:

✔ Functionally correct  
❌ Visually still “developer UI”

To reach **ERP-grade quality**, you need:

👉 **Clear hierarchy**  
👉 **Card-based grouping**  
👉 **Primary vs secondary actions**  
👉 **Readable density**

**✅ If I had to give a score**

-   Architecture: **8.5/10**
-   Data clarity: **7/10**
-   UX polish: **6/10**

👉 You are one iteration away from “this looks like ERPNext”.

**🎯 Next step (do this before moving on)**

Implement these 5 fixes ONLY:

1.  KPI cards (big numbers)
2.  Card-based right panel sections
3.  Strong “Open Budget Builder” primary CTA
4.  Add “New Budget” button
5.  Clean/remove bottom section

If you want, I can now give you:

👉 **Exact Cursor prompt to refactor this UI cleanly (no guessing)**