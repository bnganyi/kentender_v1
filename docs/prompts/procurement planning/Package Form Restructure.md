Package Form Restructure

# Review

**Why tabs were used here (the actual rationale)**

This isn’t a normal form.

👉 This is a **composite, multi-domain object**:

A Procurement Package includes:

1.  Definition
2.  Template & method
3.  Demand lines
4.  Financials
5.  Risk
6.  KPIs
7.  Decision criteria
8.  Vendor management
9.  Workflow

That’s not one form — that’s **9 logical modules**.

**So the real intent was:**

Tabs = **module boundaries**, not just UI grouping

**When tabs are correct (this case)**

Tabs are appropriate when:

**1\. The entity is large and structured**

✔ Package = complex object  
✔ Multiple independent concerns

**2\. Sections are not used simultaneously**

You don’t:

-   define KPIs *while* editing demand lines
-   configure risk *while* editing financials

👉 Each step is **mentally isolated**

**3\. There is a natural sequence**

Definition → Template → Demand → Financial → Risk → KPI → Decision → Vendor → Workflow

👉 Tabs act like a **horizontal workflow**

**Why I warned against tabs (and why that still applies)**

Tabs are bad when:

-   used for **filtering** (your earlier issue)
-   used for **too many shallow fields**
-   used when user must constantly jump back and forth
-   used without clear progression or validation

👉 That’s where they become confusing.

**The real problem in your current implementation**

Not that tabs exist — but **how they feel**

Looking at your screen:

**1\. No sense of progression**

-   Tabs look flat
-   No indication of:
    -   where you are
    -   what’s done
    -   what’s next

👉 Feels like random sections, not a flow

**2\. No completion feedback**

-   You don’t know:
    -   which sections are complete
    -   which are missing required data

👉 This is critical for large forms

**3\. Weak coupling to templates**

You already established:

Templates drive structure

But tabs don’t reflect:

-   required vs optional sections
-   template-driven changes

**4\. No guardrails**

User can:

-   jump to Vendor Management
-   before defining Demand Lines

👉 That breaks logic (even if technically allowed)

**So: Was using tabs wrong?**

👉 **No — but incomplete**

Tabs are the right structural choice here.

But they must behave like a:

**guided multi-step builder**

Not a:

**flat navigation bar**

**What this should evolve into (without drastic change)**

**1\. Add “step awareness”**

Each tab should show state:

1\. Definition ✓

2\. Template ✓

3\. Demand Lines ⚠

4\. Financial ○

Where:

-   ✓ = complete
-   ⚠ = incomplete / errors
-   ○ = not started

**2\. Enforce soft progression**

Don’t block hard, but guide:

-   allow forward navigation
-   but show warnings if prerequisites missing

Example:

“Demand lines required before financial estimation”

**3\. Auto-focus next step**

After saving:

-   suggest next tab

👉 Reduces cognitive load

**4\. Make Template drive visibility**

If template defines:

-   no KPI → hide KPI tab
-   no vendor mgmt → hide tab

👉 This is **huge for simplicity**

**5\. Add “summary awareness”**

At top (lightweight):

Package completeness: 60%

Missing: Demand lines, Financials

**When NOT to use tabs (important distinction)**

You were right earlier for:

-   DIA workbench → ❌ no tabs
-   Procurement Planning → ❌ no tabs
-   Budget builder → ❌ minimal tabs

👉 Because those are **interactive workspaces**

**Final framing**

| **Context** | **Tabs?** |
| --- | --- |
| Workbench (queues, lists) | ❌ No |
| Small forms | ❌ No |
| Large structured entity (like Package) | ✅ Yes |
| Multi-domain configuration | ✅ Yes |

**Bottom line**

You didn’t violate the principle.

👉 You applied the **correct exception case**

But to make it *feel right*, you now need:

Tabs → **guided structure**, not just navigation

# Cursor Prompts

Upgrade the Procurement Package tabbed form into a **guided builder with completion states**.

This is a UX/interaction enhancement.  
Do NOT change domain logic, data model, workflow states, permissions, or API contracts.

Goal:  
Transform tabs from passive navigation into a **structured, guided progression** with visibility into completeness and required inputs.

**1\. CORE TRANSFORMATION**

Current:  
Tabs = flat navigation

Target:  
Tabs = **guided steps with status**

Each tab must communicate:

-   Is it complete?
-   Is it incomplete?
-   Is it not started?

**2\. TAB STATE MODEL**

Each tab must have one of the following states:

-   NOT\_STARTED
-   IN\_PROGRESS
-   COMPLETE
-   ERROR (missing required fields)

**3\. TAB VISUAL INDICATORS**

Enhance each tab label with a status indicator:

Examples:

1.  Definition ✓
2.  Template ✓
3.  Demand Lines ⚠
4.  Financial ○

Rules:

-   ✓ = complete (all required fields valid)
-   ⚠ = incomplete or validation errors
-   ○ = not started
-   active tab retains highlight as today

Do NOT:

-   use heavy colors
-   over-style (keep minimal, subtle, consistent)

**4\. COMPLETION RULES (LOGIC ONLY, NO MODEL CHANGE)**

Define per-tab completion logic:

**1\. Package Definition**

-   name exists
-   code exists
-   procurement plan selected
-   template selected

**2\. Template & Method**

-   procurement method set
-   contract type set (if required)

**3\. Demand Lines**

-   at least one demand line linked

**4\. Financial & Schedule**

-   estimated value exists
-   schedule fields (if required by template)

**5\. Risk & Mitigation**

-   risk profile selected OR mitigation defined (if required)

**6\. KPI Profile**

-   KPI profile assigned (if required)

**7\. Decision Criteria**

-   decision criteria profile assigned

**8\. Vendor Management**

-   vendor strategy defined (if required)

**9\. Workflow**

-   no validation needed (system-managed)

Note:  
Use existing fields only. No schema changes.

**5\. HEADER COMPLETENESS SUMMARY**

Add a lightweight summary above tabs:

Example:

Package completeness: 60%  
Missing: Demand Lines, Financial & Schedule

Rules:

-   compute from tab states
-   show only missing or incomplete tabs
-   keep visually subtle (not a large card)

**6\. SOFT PROGRESSION (GUIDANCE, NOT BLOCKING)**

Allow free navigation across tabs.

But:

**When prerequisites missing:**

Show inline warning:

Example:  
“Define Demand Lines before completing Financial & Schedule.”

Do NOT:

-   hard-block navigation
-   create modal blockers

**7\. AUTO-ADVANCE SUGGESTION**

After saving a tab:

-   detect next incomplete tab
-   show suggestion:

“Next: Complete Demand Lines →”

Option:

-   clickable CTA to move to next tab

**8\. TEMPLATE-DRIVEN TAB VISIBILITY**

Tabs must adapt based on selected Procurement Template.

Rules:

-   Hide tabs not relevant to template
-   Do not show empty/unnecessary sections

Examples:

-   No KPI requirement → hide KPI tab
-   No vendor strategy → hide Vendor Management tab

Implementation:

-   use template configuration already available
-   do NOT introduce new backend structures

**9\. ERROR SURFACING**

When a tab has validation issues:

-   mark tab as ⚠
-   optionally show count of errors inside tab content
-   do NOT overload tab label with text

**10\. PRESERVE EXISTING FORM STRUCTURE**

Do NOT:

-   redesign tab content layout
-   merge tabs
-   convert to accordion
-   change field positions

Only enhance:

-   tab header behavior
-   state awareness
-   guidance

**11\. ACCEPTANCE CRITERIA**

The upgrade is correct only if:

-   every tab has a visible state (✓ ⚠ ○)
-   completion rules reflect actual required inputs
-   a completeness summary is visible above tabs
-   users can navigate freely without hard blocking
-   warnings guide correct sequencing
-   templates dynamically hide irrelevant tabs
-   next-step suggestion appears after save
-   no domain logic or data model changed

**12\. IMPLEMENTATION REPORT**

At completion report:

1.  how tab states are computed
2.  completion rules per tab
3.  how template affects tab visibility
4.  how completeness % is calculated
5.  how next-step suggestion is triggered
6.  any limitations in validation or state tracking