Budget Line Change — System Direction

# Budget Line Removal

**1\. First principle**

Budget Lines should rarely be *deleted*.  
They should be **removed safely or deactivated**.

**2\. Two Modes (Must implement both)**

**2.1 Remove (Soft Delete / Deactivate) — DEFAULT**

This is what users will use 95% of the time.

**Behavior:**

-   Mark Budget Line as inactive
-   Remove it from:
    -   allocation totals
    -   left panel list (or show under “Inactive” filter)
-   Preserve:
    -   audit trail
    -   references

**UI:**

-   Action: Remove Budget Line
-   Confirmation required

**2.2 Hard Delete — STRICTLY CONTROLLED**

Only allowed when:

allocated\_amount = 0

AND reserved\_amount = 0

AND not referenced anywhere

**If conditions not met:**

→ block deletion

**3\. UI Placement (Consistent with your system pattern)**

**Where:**

In the **right panel header (top-right actions)**

Example:

\[Save Budget Line\] \[Remove\]

NOT:

-   buried at bottom
-   hidden in form

**Visual hierarchy:**

| **Action** | **Style** |
| --- | --- |
| Save | primary |
| Remove | subtle destructive (red outline or text) |

**4\. Confirmation Flow (Mandatory)**

On click:

**Dialog:**

Remove Budget Line?

This will deactivate the budget line.

It will no longer be used for allocations or reservations.

\[Cancel\] \[Remove\]

**If hard delete eligible:**

Delete Budget Line permanently?

This action cannot be undone.

\[Cancel\] \[Delete\]

**5\. Constraints (Critical)**

**5.1 Must BLOCK removal if:**

-   Budget is **Approved**
-   OR line has **active reservations**
-   OR line is referenced by:
    -   DIA demand
    -   procurement planning (future)

**Error:**

Cannot remove Budget Line.

It is in use by active allocations or downstream processes.

**5.2 Draft Budget behavior**

If Budget = Draft:

-   allow remove (soft)
-   allow delete (if zero-impact)

**5.3 Approved Budget behavior**

If Budget = Approved:

-   ❌ No removal
-   ❌ No delete

Instead:

-   allow only:
    -   “Deactivate for future use” (optional later)
-   BUT allocations must remain immutable

**6\. Data Model Changes (Minimal)**

Add:

is\_active: boolean (default true)

removed\_at: datetime (optional)

removed\_by: user (optional)

**7\. Left Panel Behavior**

**After removal:**

**Option A (recommended):**

-   hide inactive lines by default
-   add filter: Active | Inactive

**Option B:**

-   show inactive lines dimmed

**8\. Budget Totals Behavior**

When a line is removed:

Line Allocated = sum(active lines only)

Line Unallocated updates accordingly

This must be recalculated immediately.

**9\. Reservation Safety (Important for future)**

When DIA is active:

-   if reserved\_amount > 0  
    → removal must be blocked

Later you may allow:

-   forced removal → auto-release reservations (but NOT now)

**10\. Cursor Implementation Prompt**

Implement Budget Line removal with strict governance rules.

Requirements:

1.  Add action "Remove Budget Line" in right panel (top-right)
2.  Default behavior = soft delete (set is\_active = false)
3.  Hard delete ONLY if:
    -   allocated\_amount = 0
    -   reserved\_amount = 0
    -   no downstream references
4.  Block removal if:
    -   Budget is Approved
    -   OR reserved\_amount > 0
    -   OR line is referenced
5.  Add confirmation dialog before removal
6.  After removal:
    -   update budget totals (allocated/unallocated)
    -   remove from active list (or move to inactive filter)
7.  Add fields:
    -   is\_active
    -   removed\_at
    -   removed\_by
8.  UI:
    -   remove action is visible but not primary
    -   destructive styling

Do NOT:

-   silently delete records
-   allow removal in Approved budgets
-   break allocation totals

At the end report:

1.  removal rules implemented
2.  UI placement
3.  how totals are recalculated
4.  edge cases handled

**Final guidance**

This is one of those decisions that defines system maturity:

-   ❌ Simple delete → fragile system
-   ✅ Governed removal → audit-ready system

You’re building a **public procurement system**, so always bias toward:

reversibility, traceability, and control

# Budget Line Edits