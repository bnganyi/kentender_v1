Builder Landing Page Refactor v2

# Analysis

**What’s actually wrong (root cause)**

**1\. Filters look like a primary section**

-   boxed
-   wide
-   full-width
-   sitting between KPI and data

👉 This visually says: “this is the main thing”

But in reality:  
👉 filters are **supporting controls**, not the core task

**2\. Too many “bands”**

You currently have:

Header

KPI strip

Filters block (heavy)

List + Detail

That’s **4 stacked layers**, each visually similar weight.

👉 Result: no clear focal point

**3\. The data area is not dominant**

Your master-detail area should feel like:

“this is where I work”

Instead it feels like:

“this is below the controls”

**The correct mental model**

You want this:

Header (light)

KPI (very light)

Controls (inline, minimal)

WORK AREA (dominant)

👉 The page is a **workbench**, not a report

**The fix (non-drastic but high impact)**

**1\. Kill the “filter box” completely**

Right now:

-   filters are in a container
-   visually heavy
-   separated from controls

**Replace with:**

👉 **inline control bar**

**New structure:**

\[ Tabs \] \[ Queue chips \] \[ Search \] \[ Filters (icon/button) \]

**Filters behavior:**

-   collapsed by default
-   appear as:
    -   button (icon + label)
    -   OR “Advanced filters”

👉 When clicked:

-   slide down panel
-   or modal

**2\. Make controls visually subordinate**

**Apply:**

-   no background box
-   no heavy borders
-   tighter spacing
-   lighter text

👉 Controls should feel like a toolbar, not a section

**3\. Reduce vertical stacking**

Right now:

Tabs

Queues

Helper text

Filters

Search

**Compress to:**

Tabs

Queues + Search (same row)

Filters (icon/button inline)

👉 That alone removes ~40–50% vertical waste

**4\. Kill or demote helper text**

This line:

“All shows every queue for your role…”

Is costing you vertical space and visual noise.

**Options:**

-   remove it entirely
-   or move it into tooltip / info icon

**5\. Pull the work area UP aggressively**

After refactor, the layout should feel like:

Header

KPI (tight)

Controls (thin strip)

\-------------------------

LIST | DETAIL ← starts high

👉 The split pane should start **almost immediately**

**6\. Fix spacing between sections**

Right now spacing is:

-   inconsistent
-   too generous between top sections
-   too tight inside sections

**Apply consistent rhythm:**

Use a rule like:

-   8px: within components
-   16px: between related groups
-   24px: between major sections

👉 Right now you’re closer to 24–32px everywhere

**7\. Make the data area visually dominant**

Small but powerful tweaks:

**List panel:**

-   slightly stronger contrast border or shadow
-   tighter card spacing

**Detail panel:**

-   stronger header
-   slightly elevated surface

👉 Subtle, but tells the brain:  
**this is the primary workspace**

**What this fixes immediately**

-   Filters stop competing with data
-   Page feels faster and more focused
-   User lands directly in “work mode”
-   Cognitive load drops significantly

**One optional (but strong) improvement**

If you want to go one step further without redesign:

**Make filters contextual**

Instead of global:

👉 Filters adapt based on:

-   selected tab
-   selected queue

This reduces:

-   visible controls
-   perceived complexity

**Your situation, honestly**

You’ve actually nailed:

-   structure
-   workflow
-   data modeling
-   interactions

What’s off is purely:  
👉 **visual hierarchy + density control**

This is a classic “good system, slightly wrong emphasis” problem.

**If you want next step**

I can give you:  
👉 a **Cursor prompt to convert filters → inline toolbar pattern cleanly**

or

👉 a **pixel-level layout spec (spacing, heights, alignment rules)** so your UI stays consistent across modules

Both will lock this in so you don’t keep fighting it later.