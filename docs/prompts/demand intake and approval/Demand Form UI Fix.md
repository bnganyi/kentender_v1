Demand Form UI Fix

# Current Status Review

**1\. What’s good (don’t lose this)**

You’ve already done a few important things right:

**✅ Clear sectioning**

-   Basic request
-   Items
-   Justification
-   Strategy linkage
-   Budget linkage
-   Delivery
-   Flags

That’s aligned with DIA intent.

**✅ Proper upstream linkage**

-   Budget Line
-   Reservation Status

Good — this keeps financial discipline intact.

**✅ Items table exists**

Critical. This prevents “lump sum demand” problems.

**2\. The real problems (these will hurt you later)**

**❌ 1. The form is too vertical and cognitively heavy**

Right now:

-   everything is stacked
-   long scroll
-   no prioritization

This causes:

-   slow data entry
-   skipped fields
-   poor-quality justifications

👉 Users won’t think — they’ll just fill minimally.

**❌ 2. “Basic request” is not actually basic**

You’ve mixed:

-   identity
-   metadata
-   classification

Example:

Title

Procuring Entity

Department

Priority

Demand Type

Demand Category

Dates

That’s **too much for first contact**.

**❌ 3. Items section is too weak**

Right now:

-   no strong structure
-   no guidance
-   no derived behavior

Missing:

-   automatic total calculation (visible)
-   validation against budget early
-   category-driven behavior

**❌ 4. Strategy linkage is fragile**

Budget Line (picker)

This is risky because:

-   users don’t understand budget structure deeply
-   wrong selection = downstream corruption

👉 This should be **guided, not free selection**

**❌ 5. Budget linkage is passive**

Reservation Status: None

This is just informational.

Missing:

-   clear “this demand will reserve funds” moment
-   visibility of available balance
-   early validation feedback

**❌ 6. Flags & exceptions are buried**

This is dangerous.

Emergency logic should NOT be:

checkbox at bottom

That guarantees:

-   misuse
-   or complete neglect

**❌ 7. Workflow section is noise for users**

Workflow State

Planning Status

Users should not care at creation time.

This is system-level, not user-level.

**❌ 8. No “decision confidence” signals**

There’s nothing telling the user:

-   “this is a good demand”
-   “this will be rejected”
-   “budget is insufficient”

**3\. Structural fix (this is the important part)**

You need to reorganize this into **4 blocks max**.

**✅ Recommended structure (production-grade)**

**1\. Demand Identity (TOP — compact, 2-column)**

Title Request Date

Department Required By

Priority Demand Type

Demand Category

👉 Keep this tight. No scrolling here.

**2\. What is being requested (CORE)**

**Items table (primary focus)**

Enhance it:

Columns:

Item | Category | UoM | Qty | Unit Cost | Line Total

Add:

-   auto total
-   inline validation
-   running total display

**Show:**

Total Requested Amount: KES X

NOT a separate input field.

👉 Kill the “Requested Amount” manual field.

**3\. Why (justification)**

Split into two:

Business Justification (why needed)

Impact if Not Procured (risk)

👉 Remove duplication between sections.

**4\. Funding & Delivery (SMART grouping)**

**Left:**

Budget Line (guided selector)

Available Budget (read-only)

Reservation Impact (preview)

**Right:**

Delivery Location

Required Delivery Period

**5\. Exception Handling (NOT buried)**

Move this UP and make it conditional:

**If Demand Type = Emergency OR Exception flag checked:**

Show:

Emergency Justification (REQUIRED)

Approval escalation note

👉 Make this loud and intentional.

**6\. REMOVE from main form**

Remove from user-facing form:

-   Workflow State
-   Planning Status

👉 Move to header/status bar.

**4\. Critical behavior fixes**

**1\. Budget Line selector must be guided**

Instead of raw dropdown:

Show:

Program → Sub-program → Budget Line

Or:

Search: "Healthcare equipment"

→ Healthcare Access > Primary Care > Medical Equipment Capex

→ Available: KES 5,000,000

**2\. Live budget validation**

As user fills items:

Requested: 3,200,000

Available: 3,000,000

⚠ Over budget by 200,000

👉 This prevents bad submissions early.

**3\. Auto-reservation preview**

Before submit:

This demand will reserve: KES 3,200,000

Remaining after reservation: KES X

**4\. Items must drive everything**

Right now:

-   items feel secondary

They should be:

-   the core of the form

**5\. UI/UX improvements (high impact, low effort)**

**Fix 1 — Two-column layout everywhere possible**

Your current form wastes horizontal space.

**Fix 2 — Collapse advanced sections**

Default collapsed:

-   Flags & exceptions
-   Delivery (if simple)

**Fix 3 — Sticky summary bar (top right)**

Show:

Total: KES X

Budget Available: KES Y

Status: OK / Over Budget

**Fix 4 — Replace grey disabled fields**

Your UI has too many:

-   greyed inputs

Replace with:

-   clean display rows

**6\. Data integrity risks (fix these early)**

If you don’t fix these, you will rewrite later:

**❗ Risk 1**

Manual “Requested Amount” ≠ sum(items)

👉 Remove manual field.

**❗ Risk 2**

Wrong Budget Line selection

👉 Use guided selector.

**❗ Risk 3**

Emergency misuse

👉 Move + enforce justification.

**❗ Risk 4**

Weak justification quality

👉 Split fields and guide input.

**7\. Bottom line**

Right now the form is:

**Structurally correct but not operationally safe or efficient**

After fixes, it becomes:

**A guided demand capture tool that enforces financial and strategic discipline early**

# Cursor Prompts

Refactor the current Demand Intake and Approval (DIA) creation form into a guided, compact demand-capture surface.

This is a UI/UX + form behavior refactor.  
Do NOT change the locked DIA workflow/state model.  
Do NOT change approvals or downstream Procurement Planning logic.  
Do NOT expose raw internal IDs.

The current problem:

-   the form is too vertical
-   too many fields are stacked
-   items do not clearly drive the demand
-   Budget Line selection is too weak/generic
-   exceptions are buried
-   workflow/system fields are shown too early
-   Requested Amount appears manual instead of item-derived

Use the Kentender UI System Pattern and Dropdown/Reference Display Standard as the source of truth.

**1\. OVERALL FORM STRUCTURE**

Reorganize the form into these major blocks in this order:

1.  Demand Identity
2.  What is Being Requested
3.  Why / Business Justification
4.  Funding & Delivery
5.  Exception Handling (conditional)
6.  System / Workflow metadata (moved out of primary entry flow)

Do NOT keep the current long stacked section sequence.

**2\. DEMAND IDENTITY BLOCK**

Use a compact two-column layout.

**Required fields:**

-   Title
-   Request Date
-   Department
-   Required By Date
-   Priority
-   Demand Type
-   Demand Category / Requisition Type

**Layout:**

Row 1:

-   Title (full width if needed)

Row 2:

-   Department | Request Date

Row 3:

-   Required By Date | Priority

Row 4:

-   Demand Type | Demand Category / Requisition Type

Rules:

-   Procuring Entity should be auto-derived or defaulted where possible; do not force noisy manual entry unless truly required
-   keep this section compact and above the fold

**3\. WHAT IS BEING REQUESTED BLOCK**

This must become the core of the form.

**3.1 Items table**

Make the items table the primary demand-definition surface.

Columns:

-   Item / Service Description
-   Category
-   Unit of Measure
-   Quantity
-   Estimated Unit Cost
-   Line Total

Rules:

-   Line Total must be derived automatically
-   no manual line total entry
-   table must support add/remove rows cleanly
-   keep headers readable and not overly truncated

**3.2 Requested Amount**

Remove the current manual Requested Amount field as a primary editable field.

Replace it with a derived summary:

-   Total Requested Amount = sum of item line totals

Display it clearly below or beside the items table as a read-only financial summary.

Rules:

-   users must not manually type the total
-   total must always reconcile with item rows

**4\. WHY / BUSINESS JUSTIFICATION BLOCK**

Split justification into guided fields instead of one weak narrative flow.

Use full-width text areas, but keep them compact.

**Required fields:**

-   Business Justification / Why needed
-   What is being requested
-   Who benefits & why
-   Impact if Not Procured (required for exception/unplanned/emergency paths, visible when relevant)

Rules:

-   do not create giant textareas by default
-   reduce default textarea height
-   expand on focus
-   use clear labels that improve answer quality
-   remove duplication where fields overlap semantically

If current field names are fixed in backend, improve only labels/help text/layout rather than breaking model unnecessarily.

**5\. FUNDING & DELIVERY BLOCK**

Use a two-column layout.

**Left column — Funding**

-   Budget Line (guided selector)
-   Available Budget (read-only, if service support already exists)
-   Reservation Preview / Budget Impact (read-only if available)

**Right column — Delivery**

-   Delivery Location
-   Requested Delivery Period (days)

Rules:

-   Budget Line selection should feel deliberate and guided
-   do not show raw internal IDs
-   when a Budget Line is selected, show meaningful context:
    -   Budget Line Name
    -   Code
    -   Program / strategic context if relevant
    -   Available Budget
-   if live budget validation is available, surface:
    -   requested amount
    -   available budget
    -   over-budget warning if applicable

**6\. BUDGET LINE SELECTOR BEHAVIOR**

Improve Budget Line selection substantially.

Requirements:

-   selector must display:
    -   Budget Line Name
    -   Budget Line Code
    -   strategic/program context as secondary info where useful
-   selector search must work on:
    -   name
    -   code
-   no raw DB IDs
-   only active/eligible Budget Lines should appear

If feasible without major backend rewrite, support guided narrowing such as:

-   Program / Sub-program → Budget Line  
    OR
-   richer Budget Line picker with contextual display

At minimum:

-   make the Budget Line selector understandable and traceable

**7\. EXCEPTION HANDLING BLOCK**

Do NOT bury exception logic at the bottom as passive fields.

Make this a conditional section that appears more intentionally.

**Trigger conditions:**

-   Demand Type = Unplanned
-   Demand Type = Emergency
-   Exception Flag checked

**Fields:**

-   Exception Flag
-   Impact if Not Procured
-   Emergency Justification (required when Demand Type = Emergency)

Rules:

-   show this section only when relevant
-   make emergency justification visually prominent when required
-   do not show empty placeholders for normal planned demand
-   validation must remain server-side, but UI must make the requirement obvious

**8\. WORKFLOW / SYSTEM METADATA**

Move low-level workflow/system fields out of the main user-entry path.

Examples:

-   Workflow State
-   Planning Status
-   Reservation Status (unless directly helpful as read-only context)

Recommended:

-   show these in a compact header/meta strip or a secondary read-only section
-   do not place them in the middle of the entry flow
-   do not make users think they need to manage system workflow values manually

**9\. HEADER / ACTIONS**

Improve page-level usability.

Requirements:

-   clear back navigation to DIA landing/workbench
-   compact identity header:
    -   New Demand / Demand Title
    -   status badge (Draft / Not Saved)
-   primary Save action remains top-right
-   once saved, workflow actions can appear in header as already intended

Do NOT force users to scroll to the bottom for primary actions.

**10\. LIVE DECISION SUPPORT (IF AVAILABLE WITH CURRENT SERVICES)**

Where existing service support already exists, surface compact guidance:

**Examples:**

-   Total Requested Amount: KES X
-   Available Budget: KES Y
-   Over Budget by: KES Z
-   This demand will reserve funds on finance approval

Do NOT fabricate values if backend support is not yet implemented.  
If not available yet, leave clean placeholders or omit rather than showing misleading UI.

**11\. READ-ONLY VS EDITABLE RENDERING**

Enforce Kentender display rules:

-   Editable fields → real inputs
-   Derived/read-only values → display rows or compact summaries
-   Do NOT render read-only data as large disabled grey inputs where avoidable

This is especially important for:

-   Requested Amount / totals
-   Available Budget
-   Reservation / workflow information
-   strategy/budget context

**12\. LAYOUT / DENSITY RULES**

Apply these throughout:

-   two-column layout for structured fields
-   full width only for:
    -   long text
    -   items table
-   reduce unnecessary vertical spacing
-   reduce oversized textarea dominance
-   keep the most important fields above the fold

The form should feel:

-   guided
-   compact
-   decision-aware

Not:

-   long
-   passive
-   bureaucratic

**13\. VALIDATION / BEHAVIOR EXPECTATIONS**

Without changing backend rules, ensure the UI strongly supports:

-   item totals derive automatically
-   requested amount derives automatically
-   budget context becomes clearer after Budget Line selection
-   emergency/unplanned fields appear when needed
-   users cannot miss critical fields easily

If there are frontend validations already, keep them aligned with backend truth.

**14\. DO NOT CHANGE**

Do NOT change:

-   DIA workflow/state machine
-   approval routing
-   Budget reservation logic
-   Procurement Planning integration semantics
-   server-side validation contract unless separately instructed

This ticket is a guided form refactor, not a domain redesign.

**15\. ACCEPTANCE CRITERIA**

The refactor is correct only if:

-   the form is visibly more compact
-   Demand Identity is compact and above the fold
-   items table is the clear center of the request
-   Requested Amount is derived, not manually typed
-   Budget Line selection is more understandable
-   funding + delivery are grouped logically
-   exception logic is conditional and more prominent
-   workflow/system fields are demoted from the main entry path
-   no raw IDs are shown
-   the form feels like a guided capture surface, not a long generic form

At the end report:

1.  components/templates changed
2.  fields moved or regrouped
3.  whether Requested Amount is now derived-only
4.  Budget Line selector improvements made
5.  exception-handling visibility changes
6.  any remaining blockers that would require backend support