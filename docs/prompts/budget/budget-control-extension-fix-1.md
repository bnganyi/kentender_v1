Budget Builder v2.1 refinement

# Overview

**What is working**

-   The control unit shift to **Budget Lines** is now visible.
-   The left-right master/detail structure is right.
-   The top summary cards are useful.
-   The strategic context is visible, which is important for DIA.

**Main problems now**

**1\. The right panel is too long**

You are stacking too many single-column fields vertically. That creates unnecessary scroll and makes the page feel heavier than it is.

**2\. Field hierarchy is weak**

Everything looks like the same level of importance:

-   line name
-   code
-   allocated amount
-   program
-   target
-   funding source
-   reserved
-   available
-   notes

That is not how the user thinks.

**3\. The list badges are noisy**

\[Allocated\] is not pulling its weight. It adds visual chatter without telling the user much.

For a budget line, if the amount is non-zero, the number already tells the story. You do not need a tag screaming the obvious.

**4\. The summary cards may be mathematically inconsistent**

You show:

-   Total Budget = 8,000,000
-   Allocated = 8,000,000
-   Remaining = 0
-   Reserved = 0
-   Available = 8,000,000

That is only valid if **Available means available for reservation**, not unallocated budget remaining. If so, the labels need to be crystal clear.

Right now a user could read:

-   Remaining = 0
-   Available = 8,000,000

and reasonably think the page contradicts itself.

**Recommended field arrangement**

Use **four compact sections**, with **two columns inside sections** where appropriate.

**Right panel layout**

**Section 1 — Budget Line Definition**

This should be the shortest and most important section.

**Two-column layout**

Left:

-   Budget Line Name
-   Budget Line Code

Right:

-   Allocated Amount
-   Funding Source

**Full-width below**

-   Notes

This alone removes a lot of unnecessary height.

**Section 2 — Strategic Context**

Do **not** stack all strategy fields one per row unless necessary.

Use a **two-column grid**:

Left:

-   Program
-   Sub-program

Right:

-   Output Indicator
-   Performance Target

If Strategic Plan is always inherited from the parent Budget or already obvious at page level, do not give it prime screen space here. Show it as muted metadata or omit it from the line editor if redundant.

**Section 3 — Financial Context**

Again, two columns.

Left:

-   Reserved Amount
-   Available Amount

Right:

-   Parent Budget
-   Currency

If Parent Budget is already obvious from the page header (FY2026 Budget), remove it from this section entirely.

That leaves:

-   Reserved Amount
-   Available Amount
-   Funding Source

which is enough.

**Section 4 — Administrative / Secondary**

This is low priority. Keep it collapsed or visually subdued.

Fields:

-   Active / inactive
-   created / updated metadata if needed later

For now, you may not need to show this at all.

**What to remove or demote**

**Remove from the main right panel if redundant**

-   repeating the selected line title again as a section title and then again as a field label can be trimmed
-   Parent Budget, if already obvious in the page header
-   Strategic Plan, if the whole builder is already within one budget and one strategic context

**Demote visually**

-   Budget Line Code should be important, but not as visually loud as the line name
-   Notes should be lower prominence unless being edited

**Suggested visual hierarchy**

**Top of right panel**

Show a compact identity header like:

**Medical Equipment Capex**  
BL-MOH-2026-001 · Healthcare Access

Then below that, show sections.

That is much cleaner than repeating the same information through many full-width inputs.

**Left panel improvements**

**Current issue**

Rows are a little busy:

-   name
-   code + program on one line
-   amount
-   \[Allocated\]

The status tag is the main offender.

**Better row model**

Use:

**Medical Equipment Capex**  
BL-MOH-2026-001 · Healthcare Access  
**KES 5,000,000**

That may be enough.

**When to show a badge**

Only show a badge when it adds real meaning:

-   Unallocated
-   Inactive
-   Reserved
-   maybe Locked

But not Allocated for every row with a non-zero amount. That is the default case.

**Better rule**

-   If amount = 0 → show Unallocated
-   If line inactive → show Inactive
-   If parent budget approved → maybe no row badge; use page-level lock banner instead

**Specific list-status guidance**

**Replace \[Allocated\]**

Do not use it.

**Alternatives**

For non-zero lines:

-   no badge at all

For zero lines:

-   subtle badge: Unallocated

For inactive lines:

-   subtle badge: Inactive

This will immediately reduce noise and make exceptions stand out properly.

**Top summary card guidance**

You need clearer terminology.

**Recommended labels**

If the current semantics are:

-   Total Budget = budget total
-   Allocated = sum of budget line allocations
-   Remaining = unallocated budget not yet assigned to lines
-   Reserved = amount held by DIA reservations
-   Available = amount available for reservation across active lines

Then rename to:

-   **Total Budget**
-   **Line Allocated**
-   **Line Unallocated**
-   **Reserved**
-   **Available for Reservation**

That removes ambiguity.

Right now Remaining and Available fight each other.

**Arrangement recommendation for summary cards**

Use one row of four if possible:

-   Total Budget
-   Line Allocated
-   Line Unallocated
-   Available for Reservation

Then, if reservation is already active in the system, either:

-   make Reserved a fifth card
-   or put Reserved as smaller supporting text under Available for Reservation

If reservations are still mostly zero in early stages, you can keep it subdued.

**Other observations**

**1\. Save button placement**

The Save Budget Line button at the bottom makes the user travel too far.

**Better**

Place primary action:

-   sticky at top-right of the right panel  
    or
-   at both top and bottom if the panel remains long

For this form, top-right is better.

**2\. Inputs look too much like disabled grey slabs**

Even though the data model is better, the presentation still feels like raw form controls.

**Better**

For read-only / derived fields:

-   render many of them as **display rows** instead of input boxes

Example:  
Instead of a grey input for Program, show:

**Program**  
Healthcare Access

This will make the detail panel feel more like a professional inspector/editor and less like a disabled form.

**Rule of thumb**

-   editable fields → inputs
-   derived/read-only fields → display text rows/cards

That single change will improve the page a lot.

**3\. Notes box is too visually heavy**

The notes textarea is dominating the lower part of the screen.

**Better**

-   reduce default height
-   allow expansion on focus
-   or move Notes into a secondary/collapsible section

**4\. + Add Budget Line is too weak**

It currently looks like a small text link and gets lost.

**Better**

Make it a proper secondary button.

Not oversized, but clearly actionable.

**Best compact arrangement**

If I were locking this for implementation, I would structure the right panel like this:

**Identity header**

-   Line name
-   code
-   program as muted context

**Section A: Definition**

Two columns:

-   Line Name | Allocated Amount
-   Line Code | Funding Source

Then:

-   Notes

**Section B: Strategic Context**

Two columns:

-   Program | Sub-program
-   Output Indicator | Performance Target

**Section C: Financial Context**

Two columns:

-   Reserved Amount | Available for Reservation
-   Currency | Active/Inactive

And most of Section B/C should render as read-only display text, not full input controls.

**Final verdict**

The refactor is **architecturally much better**, but visually it still feels like:

“a long form made from the right fields”

You want it to feel like:

“a compact budget-line workbench”

Cursor prompt

Good — this is the exact kind of refinement Cursor needs to stop “form-stacking” and move into proper ERP-grade UI.

Below is a **tight, implementation-ready prompt** that focuses only on UI restructuring (no data model changes).

Refine the existing Budget Builder UI to improve layout density, clarity, and hierarchy without changing the underlying data model.

This is a UI/UX refactor only. Do NOT modify business logic, models, or service behavior.

**1\. RIGHT PANEL — STRUCTURE REFACTOR**

Replace the current long single-column form with structured sections and two-column layouts.

**1.1 Add Identity Header (top of right panel)**

Instead of repeating fields as inputs, render a compact header:

-   Line Name (bold, primary)
-   Below it: Budget Line Code + Program (muted text, inline)

Example:  
Medical Equipment Capex  
BL-MOH-2026-001 · Healthcare Access

**1.2 Section A — Budget Line Definition**

Convert to TWO-COLUMN layout:

LEFT COLUMN:

-   Budget Line Name (editable input)
-   Budget Line Code (editable input)

RIGHT COLUMN:

-   Allocated Amount (editable input)
-   Funding Source (editable input)

FULL WIDTH BELOW:

-   Notes (textarea)

Reduce default height of Notes. Expand on focus.

**1.3 Section B — Strategic Context**

Convert to TWO-COLUMN layout and render as READ-ONLY display (not inputs):

LEFT:

-   Program
-   Sub-program

RIGHT:

-   Output Indicator
-   Performance Target

Render as text rows, not grey input fields.

Example:  
Program  
Healthcare Access

Do NOT use disabled input boxes for these.

**1.4 Section C — Financial Context**

Convert to TWO-COLUMN layout:

LEFT:

-   Reserved Amount (read-only)
-   Available Amount (read-only)

RIGHT:

-   Currency (read-only)
-   Active / Inactive (toggle if editable, else display)

If Parent Budget is already visible in page header, REMOVE it from this section.

**1.5 Remove Visual Noise**

-   Do NOT render read-only fields as grey input boxes
-   Use clean label + value rows
-   Only editable fields should look like inputs

**2\. LEFT PANEL — LIST CLEANUP**

**2.1 Remove \[Allocated\] badge**

This is redundant and creates noise.

**2.2 New row structure**

Each row should display:

-   Line Name (primary)
-   Secondary line: Code + Program
-   Amount aligned right

Example:

Medical Equipment Capex  
BL-MOH-2026-001 · Healthcare Access  
KES 5,000,000

**2.3 Conditional badges ONLY**

Show badges only when meaningful:

-   If amount == 0 → show Unallocated
-   If inactive → show Inactive

Do NOT show a badge for normal allocated lines.

**2.4 Improve Add Button**

Replace:

-   \+ Add Budget Line (text link)

With:

-   proper secondary button: Add Budget Line

**3\. SUMMARY CARDS — TERMINOLOGY FIX**

Clarify meaning of budget values.

Rename:

-   Allocated → Line Allocated
-   Remaining → Line Unallocated
-   Available → Available for Reservation

Ensure consistency:

-   Line Allocated = sum of Budget Line amounts
-   Line Unallocated = Total Budget − Line Allocated
-   Available for Reservation = sum of (allocated − reserved − consumed)

Do NOT allow ambiguity between Remaining and Available.

**4\. SAVE ACTION IMPROVEMENT**

**Current problem:**

Save button is at bottom → too far to reach

**Required change:**

-   Move primary action Save Budget Line to TOP RIGHT of right panel
-   Optional: keep secondary Save at bottom if needed

**5\. NOTES FIELD REFINEMENT**

-   Reduce default height
-   Expand on focus
-   Move visually to lower priority section (bottom of Section A)

**6\. VISUAL HIERARCHY RULES**

Enforce:

-   Editable fields → input controls
-   Derived/read-only fields → text display rows
-   Section titles clearly separated
-   Avoid full-width stacked inputs unless necessary

**7\. DO NOT CHANGE**

-   Data model
-   API/service logic
-   Budget Line structure
-   Reservation behavior

This is strictly presentation and layout improvement.

**8\. ACCEPTANCE CRITERIA**

UI is correct only if:

-   Right panel is split into clear sections
-   Sections use two-column layout where appropriate
-   Read-only fields are NOT rendered as grey input boxes
-   Left panel has no \[Allocated\] noise
-   Only meaningful badges are shown (Unallocated / Inactive)
-   Summary cards use unambiguous terminology
-   Save button is accessible at top
-   Page feels compact, not vertically stretched

At the end, report:

1.  components/templates modified
2.  fields converted from input → display
3.  layout changes made (grid/columns)
4.  any UI edge cases or inconsistencies still present

**Final note (important)**

You’re now at the stage where:

-   **architecture is correct**
-   **UI is catching up**

This kind of refinement is what separates:

“it works”  
from  
“this feels like a real system”

Once this lands, your Budget module will feel very close to ERPNext-level polish.

If you want next, we can:  
👉 align DIA UI to this same pattern (so the system feels consistent end-to-end)