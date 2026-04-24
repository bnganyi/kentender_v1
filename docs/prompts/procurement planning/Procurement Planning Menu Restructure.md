Procurement Planning Menu Restructure

# Review

Right now you have:

Desktop → Procurement (app)

→ Sidebar: Procurement Planning (menu)

→ Sidebar again: KPI Profile / Risk Profile / Procurement Plan

This creates a **double-navigation pattern**, which is not ideal.

**What’s wrong with current structure**

**❌ 1. “Procurement Planning” behaves like both:**

-   a **module**
-   and a **workspace**

That’s ambiguous.

**❌ 2. Profiles (KPI, Risk) are exposed as primary navigation**

These are:

-   configuration objects
-   not daily user workflows

👉 They should NOT sit at the same level as “Procurement Plan”.

**❌ 3. You are nesting sidebars unnecessarily**

User flow becomes:

Procurement → Procurement Planning → (new sidebar)

That’s one layer too deep.

**Correct structure (clean, scalable)**

**✅ Level 1 — Desktop**

Procurement (App)

**✅ Level 2 — Procurement workspace sidebar**

This is the **main navigation users live in**.

Procurement

├── Dashboard (optional later)

├── Demand Intake & Approval

├── Procurement Planning

├── Suppliers (next module)

├── Tendering (future)

👉 **Stop here. No second sidebar layer.**

**✅ Level 3 — Inside “Procurement Planning” (workbench, not menu)**

When user clicks:

Procurement Planning

They should land on:

👉 **Procurement Planning Workbench (single page)**

NOT another sidebar.

**What goes inside Procurement Planning**

Inside the workbench (NOT sidebar menus):

**Primary working surface**

\- Procurement Plans

\- Procurement Packages (within plans)

\- Queues (Draft / Pending Approval / Approved / Ready)

**Configuration (hidden / secondary)**

Move these OUT of main nav:

KPI Profile

Risk Profile

Decision Criteria Profile

Vendor Management Profile

Templates

Place them under:

Settings / Configuration

Example:

Procurement

→ Settings

→ Planning Configuration

\- Templates

\- KPI Profiles

\- Risk Profiles

\- Decision Criteria

\- Vendor Management Profiles

**Final clean structure**

**Desktop**

Procurement

**Sidebar (single level)**

Procurement

├── Demand Intake & Approval

├── Procurement Planning

├── Suppliers (future)

├── Tendering (future)

├── Settings

**Procurement Planning (no sidebar nesting)**

→ Workbench

Inside page:

\- Plan selector

\- Package queues

\- KPI strip

\- Master-detail view

**Key rule going forward**

👉 **Modules = sidebar items**  
👉 **Work = inside workbench**  
👉 **Configuration ≠ primary navigation**

**Bottom line**

**Your current structure:**

✔ Correct direction  
❌ Too many layers  
❌ Exposes config too early

**Correct structure:**

✔ Single sidebar level  
✔ Workbench-driven modules  
✔ Config moved to settings

# Cursor Prompts

Refactor the Procurement app navigation so it follows a clean single-sidebar, workbench-first structure.

This is a navigation / information architecture refactor only.  
Do NOT redesign Procurement Planning domain logic.  
Do NOT add new business workflows.  
Do NOT create nested sidebar layers for everyday work.

Current problem:

-   Procurement Planning appears as a sidebar menu under Procurement
-   then opens another set of sidebar menus (KPI Profile, Risk Profile, Procurement Plan, etc.)
-   configuration objects are exposed as primary navigation
-   users are forced into double navigation

Use the Kentender UI System Pattern as the source of truth.

**1\. TARGET NAVIGATION STRUCTURE**

**Desktop / App level**

Keep:

-   Procurement

**Procurement sidebar (single working sidebar)**

Show only primary user-facing modules:

-   Procurement
-   Demand Intake & Approval
-   Procurement Planning
-   Settings

Do NOT create a second sidebar layer when entering Procurement Planning.

**2\. PROCUREMENT PLANNING BEHAVIOR**

When user clicks:

-   Procurement Planning

They must land on:

-   one Procurement Planning workbench page

That page should contain:

-   current plan context
-   KPI strip
-   queue selector
-   package master-detail work surface

It must NOT replace the sidebar with:

-   KPI Profile
-   Risk Profile
-   Procurement Plan
-   other config doctypes as primary nav

**3\. MOVE CONFIGURATION OUT OF PRIMARY NAVIGATION**

The following are configuration/support objects, not primary working modules:

-   KPI Profile
-   Risk Profile
-   Decision Criteria Profile
-   Vendor Management Profile
-   Procurement Template
-   Procurement Plan configuration screens if separate from the workbench

These should be reachable from:

-   Procurement → Settings  
    or
-   Procurement → Planning Settings / Planning Configuration

Recommended structure:

Procurement

-   Demand Intake & Approval
-   Procurement Planning
-   Settings

Inside Settings, expose:

-   Planning Configuration
    -   Procurement Templates
    -   Risk Profiles
    -   KPI Profiles
    -   Decision Criteria Profiles
    -   Vendor Management Profiles

Keep this ERPNext/Frappe-friendly, but do not expose these config doctypes as equal peers to primary workflow modules.

**4\. PROCUREMENT APP HOME / SIDEBAR RULES**

Enforce these rules:

1.  Modules = sidebar items
2.  Work happens inside module workbenches
3.  Configuration lives under Settings, not primary daily navigation
4.  No double-sidebar pattern for normal users

This means:

-   Procurement Planning is a module/workbench
-   not a parent menu that opens another sidebar of subordinate doctypes

**5\. UI/IA BEHAVIOR REQUIREMENTS**

**Procurement sidebar should feel like:**

-   a small set of real workflow entry points

**Procurement Planning page should feel like:**

-   the full planning workspace

**Settings should feel like:**

-   admin/configuration space

Do NOT:

-   create a giant sidebar list of technical doctypes
-   surface profile/config objects as if they are daily user tasks
-   require user to navigate sidebar → sidebar → work

**6\. ROLE / UX INTENT**

For ordinary users:

-   they should start from Procurement Planning workbench
-   not from raw profile lists

For admin/configuration users:

-   they can access settings/configuration separately

This separation is important and must be preserved.

**7\. KEEP / PRESERVE**

Preserve:

-   Procurement desktop icon/app
-   Demand Intake & Approval as a primary module
-   Procurement Planning as a primary module

Refactor:

-   the extra sidebar/menu layer under Procurement Planning
-   placement of KPI/Risk/Profile doctypes
-   placement of template/profile/configuration screens

**8\. ACCEPTANCE CRITERIA**

Navigation is correct only if:

-   Procurement remains a desktop/app icon
-   Procurement sidebar has a single working navigation layer
-   Procurement Planning opens a workbench page, not a new sidebar of doctypes
-   KPI Profile and Risk Profile are removed from primary navigation
-   Templates/profiles/config objects are moved under Settings / Planning Configuration
-   ordinary users can reach planning work without navigating technical config menus
-   no double-sidebar pattern remains for Procurement Planning

**9\. IMPLEMENTATION NOTES**

Use Frappe/ERPNext-friendly navigation mechanisms, but preserve the IA above.

If needed:

-   create/update workspace definitions
-   create/update shortcuts/cards/links
-   move raw doctypes out of top-level user navigation
-   keep configuration accessible but secondary

Do not break existing routes if avoidable; prefer rerouting or reorganizing menu exposure rather than deleting working pages unnecessarily.

At the end report:

1.  sidebar/workspace changes made
2.  which config objects were moved under Settings
3.  whether any second-sidebar behavior still remains
4.  any ERPNext/Frappe limitations that still affect the ideal navigation structure