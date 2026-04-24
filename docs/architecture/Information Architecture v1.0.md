Procurement App — Information Architecture (v1.0)

# Architecture

**1\. Design principles**

**1.1 One app, one working sidebar**

The Procurement app should have **one primary sidebar** only.

**1.2 Modules are workflow entry points**

Sidebar items should be:

-   real business modules
-   daily working surfaces

Not:

-   raw doctypes
-   technical configuration objects

**1.3 Work happens inside workbenches**

Clicking a module should open:

-   a workbench
-   a builder
-   a review surface

Not another navigation tree.

**1.4 Configuration is secondary**

Templates, profiles, rules, and reference structures belong under:

-   Settings
-   Configuration
-   Admin-only areas

**2\. App-level structure**

**Desktop**

Procurement

This remains the desktop/app icon.

**3\. Primary sidebar structure**

This is the main Procurement sidebar users should see.

Procurement

├── Procurement Home

├── Demand Intake & Approval

├── Procurement Planning

├── Supplier Management

├── Tendering & Solicitation

├── Submissions & Opening

├── Evaluation & Award

├── Contracts & Execution

├── Inspection & Acceptance

├── Complaints & Oversight

└── Settings

This is the long-term clean structure.

**4\. What should exist now vs later**

**4.1 Active now**

These should be in the sidebar now:

Procurement

├── Procurement Home

├── Demand Intake & Approval

├── Procurement Planning

└── Settings

**4.2 Reserve for later**

These should be planned in IA, but only exposed when implemented enough:

Supplier Management

Tendering & Solicitation

Submissions & Opening

Evaluation & Award

Contracts & Execution

Inspection & Acceptance

Complaints & Oversight

Do not expose dead links or premature shells unless you explicitly want placeholders.

**5\. Module-by-module IA**

**5.1 Procurement Home**

Purpose:

-   app landing page
-   cross-module summary
-   role-aware entry point

**Inside Procurement Home**

-   KPI strip
-   My pending actions
-   Recent activity
-   Quick links:
    -   New Demand
    -   Open DIA queue
    -   Open Procurement Planning
    -   Open Pending Approvals

This should be a dashboard/workbench, not a document list.

**5.2 Demand Intake & Approval**

Purpose:

-   capture, approve, and prepare demand for planning

**Entry point behavior**

Clicking it opens:

DIA Workbench

**Inside DIA**

-   workbench
-   queues
-   detail panel
-   builder/editor

**Do not expose in sidebar**

-   raw Demand DocType
-   raw exception records
-   raw workflow objects

**5.3 Procurement Planning**

Purpose:

-   transform approved demand into procurement packages

**Entry point behavior**

Clicking it opens:

Procurement Planning Workbench

**Inside Procurement Planning**

-   current plan context
-   package queues
-   package detail panel
-   package builder
-   template selector

**Do not expose in sidebar**

-   KPI Profile
-   Risk Profile
-   Procurement Template
-   Procurement Plan as raw doctype list
-   Vendor Management Profile
-   Decision Criteria Profile

Those belong in Settings.

**5.4 Supplier Management**

Purpose:

-   manage supplier lifecycle and procurement-facing supplier eligibility

**Entry point behavior**

Clicking it should open:

Supplier Management Workbench

**Inside Supplier Management**

-   supplier list / queue
-   onboarding status
-   qualification status
-   performance view
-   sanctions / restrictions view

**Do not expose in sidebar**

-   raw lookup/config tables as primary nav

**5.5 Tendering & Solicitation**

Purpose:

-   create and manage solicitation from approved procurement packages

**Entry point behavior**

Clicking it should open:

Tendering Workbench

**Inside**

-   tender list
-   draft solicitations
-   active solicitations
-   closing soon
-   tender detail / builder

**5.6 Submissions & Opening**

Purpose:

-   receive, secure, and open submissions

**Entry point behavior**

Submissions & Opening Workbench

**Inside**

-   active submission events
-   opening sessions
-   received submissions
-   opening records

**5.7 Evaluation & Award**

Purpose:

-   evaluate submissions and decide award

**Entry point behavior**

Evaluation & Award Workbench

**Inside**

-   evaluation queue
-   pending committee/authority actions
-   award decisions
-   award detail/review

**5.8 Contracts & Execution**

Purpose:

-   move award into contract and monitor execution posture

**Entry point behavior**

Contracts & Execution Workbench

**Inside**

-   contract list
-   active contracts
-   expiring contracts
-   performance tracking

**5.9 Inspection & Acceptance**

Purpose:

-   receive, inspect, and accept delivered outputs

**Entry point behavior**

Inspection & Acceptance Workbench

**Inside**

-   pending inspections
-   accepted deliveries
-   rejected deliveries
-   handoff to stores/assets where relevant

**5.10 Complaints & Oversight**

Purpose:

-   handle complaints, reviews, transparency-related oversight actions

**Entry point behavior**

Complaints & Oversight Workbench

**Inside**

-   complaint queue
-   investigation/review states
-   oversight notices
-   linked procurement cases

**6\. Settings structure**

This is where configuration belongs.

Settings

├── Planning Configuration

│ ├── Procurement Templates

│ ├── Risk Profiles

│ ├── KPI Profiles

│ ├── Decision Criteria Profiles

│ └── Vendor Management Profiles

├── Method & Threshold Rules

├── Approval & Governance Settings

├── Reference Data

└── Integration Settings

This is the correct home for profile/config objects.

**7\. What belongs inside each workbench vs sidebar**

**Sidebar = module entry only**

Examples:

-   Demand Intake & Approval
-   Procurement Planning

**Inside workbench = operational navigation**

Examples inside Procurement Planning:

-   My Work
-   All
-   Approved
-   Ready for Tender
-   queue selector
-   package list

Do not promote those internal queues to sidebar items.

**8\. Current recommended live IA**

Given where you are today, I would lock this as the immediate visible structure:

Procurement

├── Procurement Home

├── Demand Intake & Approval

├── Procurement Planning

└── Settings

And under **Settings**:

Settings

└── Planning Configuration

├── Procurement Templates

├── Risk Profiles

├── KPI Profiles

├── Decision Criteria Profiles

└── Vendor Management Profiles

That is the cleanest version right now.

**9\. Roles and navigation intent**

**Ordinary operational users**

Should spend almost all their time in:

-   Procurement Home
-   Demand Intake & Approval
-   Procurement Planning

**Admin/configuration users**

Should spend time in:

-   Settings
-   Planning Configuration

**Auditors/oversight users**

Should mostly use:

-   workbenches in read-only mode
-   later Complaints & Oversight

This separation is important.

**10\. Anti-patterns to avoid**

**10.1 Raw doctypes as sidebar peers**

Bad:

Procurement Planning

KPI Profile

Risk Profile

Procurement Plan

**10.2 Nested sidebars for one module**

Bad:

Procurement → Procurement Planning → another sidebar

**10.3 Config mixed with workflow**

Bad:

-   users see technical profiles before they see actual work

**10.4 One sidebar item per doctype**

This will kill usability later.

**11\. Naming guidance**

Use module names that reflect business work, not data structures.

**Good**

-   Procurement Planning
-   Tendering & Solicitation
-   Evaluation & Award

**Avoid as primary nav**

-   Procurement Package
-   KPI Profile
-   Vendor Management Profile
-   Decision Criteria Profile

Those are internal module objects, not top-level modules.

**12\. Recommended implementation sequence for navigation**

**Now**

Expose:

-   Procurement Home
-   Demand Intake & Approval
-   Procurement Planning
-   Settings

**Next**

When Supplier Management is ready enough, add:

-   Supplier Management

**Then**

Add each new module only when:

-   workbench exists
-   basic flow exists
-   module is not just a placeholder

**13\. Final concise structure**

**Long-term Procurement IA**

Procurement

├── Procurement Home

├── Demand Intake & Approval

├── Procurement Planning

├── Supplier Management

├── Tendering & Solicitation

├── Submissions & Opening

├── Evaluation & Award

├── Contracts & Execution

├── Inspection & Acceptance

├── Complaints & Oversight

└── Settings

**Current live Procurement IA**

Procurement

├── Procurement Home

├── Demand Intake & Approval

├── Procurement Planning

└── Settings

**Current Settings IA**

Settings

└── Planning Configuration

├── Procurement Templates

├── Risk Profiles

├── KPI Profiles

├── Decision Criteria Profiles

└── Vendor Management Profiles

# Cursor Prompts

Refactor the Procurement app information architecture to follow the locked Kentender Procurement IA.

This is an information architecture and navigation refactor.  
Do NOT redesign business logic.  
Do NOT create raw-doctype-driven navigation.  
Do NOT introduce double-sidebar patterns.

Use the locked Procurement app IA as the source of truth.

**1\. TARGET APP STRUCTURE**

Implement the Procurement app with a single primary sidebar.

**Current live structure required now:**

-   Procurement Home
-   Demand Intake & Approval
-   Procurement Planning
-   Settings

Do NOT expose technical/configuration doctypes as top-level peers to these modules.

**2\. PROCUREMENT HOME**

Create or refactor Procurement Home as the app landing/workbench.

Purpose:

-   role-aware entry point into the Procurement app
-   cross-module summary
-   quick access to primary work

Expected content:

-   KPI / summary strip
-   My pending actions
-   Recent activity or recent records if available
-   Quick links:
    -   New Demand
    -   Open Demand Intake & Approval
    -   Open Procurement Planning
    -   Open Pending Approvals

This should be a workbench/dashboard, not a raw list.

**3\. DEMAND INTAKE & APPROVAL**

Keep Demand Intake & Approval as a primary module in the Procurement sidebar.

Requirements:

-   clicking it opens the DIA workbench / primary module page
-   do not expose raw supporting doctypes as separate sidebar peers
-   keep workflow work inside the module page, not in nested navigation

**4\. PROCUREMENT PLANNING**

Keep Procurement Planning as a primary module in the Procurement sidebar.

Requirements:

-   clicking it opens the Procurement Planning workbench
-   it must NOT open a second sidebar with:
    -   KPI Profile
    -   Risk Profile
    -   Procurement Plan
    -   other config/support doctypes

Inside the Procurement Planning page/workbench, users should do the actual work:

-   current plan context
-   queues
-   package list
-   package detail
-   package builder access

Do NOT replace module pages with raw doctype menus.

**5\. SETTINGS / CONFIGURATION**

Move planning configuration objects out of primary workflow navigation.

Under Procurement → Settings, expose a planning configuration area containing:

-   Procurement Templates
-   Risk Profiles
-   KPI Profiles
-   Decision Criteria Profiles
-   Vendor Management Profiles

If needed, structure this as:

-   Settings
    -   Planning Configuration
        -   Procurement Templates
        -   Risk Profiles
        -   KPI Profiles
        -   Decision Criteria Profiles
        -   Vendor Management Profiles

These are configuration/support objects, not top-level daily workflow modules.

**6\. DO NOT EXPOSE AS PRIMARY SIDEBAR ITEMS**

Remove these from primary Procurement sidebar navigation:

-   KPI Profile
-   Risk Profile
-   Decision Criteria Profile
-   Vendor Management Profile
-   Procurement Template
-   raw Procurement Plan doctype list if separate from the workbench

These may remain reachable via Settings / Planning Configuration.

**7\. SINGLE-SIDEBAR RULE**

Enforce:

-   one Procurement sidebar only
-   modules in sidebar
-   work inside module workbenches
-   configuration inside Settings

Do NOT implement:

-   Procurement → Procurement Planning → second sidebar
-   nested normal-user sidebar structures for routine work

**8\. CURRENT VS FUTURE MODULES**

Implement visible current live modules now:

-   Procurement Home
-   Demand Intake & Approval
-   Procurement Planning
-   Settings

Reserve future module positions in architecture only, but do not expose dead/empty menu items unless explicitly instructed:

-   Supplier Management
-   Tendering & Solicitation
-   Submissions & Opening
-   Evaluation & Award
-   Contracts & Execution
-   Inspection & Acceptance
-   Complaints & Oversight

If placeholders already exist, either hide them or clearly mark them as intentionally unavailable only if required by framework constraints.

**9\. ROLE / UX INTENT**

Ordinary users should spend almost all their time in:

-   Procurement Home
-   Demand Intake & Approval
-   Procurement Planning

Admin/configuration users should access:

-   Settings
-   Planning Configuration

Auditors/oversight users should use module workbenches in read-only mode, not raw config menus.

This separation must be preserved.

**10\. ERPNext / FRAPPE-FRIENDLY IMPLEMENTATION**

Use workspace/navigation mechanisms that fit Frappe/ERPNext, but preserve the IA above.

Acceptable implementation moves include:

-   updating workspace definitions
-   changing sidebar/menu exposure
-   moving config links into Settings
-   using cards/shortcuts/links inside workbenches instead of top-level nav
-   preserving routes while changing where they are surfaced

Do NOT break working routes unnecessarily.

**11\. ACCEPTANCE CRITERIA**

Navigation is correct only if:

-   Procurement remains a desktop/app icon
-   Procurement has one primary working sidebar
-   Procurement Home exists as the main app landing page
-   Demand Intake & Approval remains a primary workflow module
-   Procurement Planning remains a primary workflow module
-   Procurement Planning opens a workbench, not a second sidebar of technical doctypes
-   KPI/Risk/Template/Profile objects are moved out of primary workflow nav
-   Planning configuration is reachable under Settings
-   ordinary users can reach their work without navigating technical config objects
-   no double-sidebar pattern remains for routine Procurement work

**12\. IMPLEMENTATION REPORT**

At the end report:

1.  workspace/sidebar changes made
2.  which items were removed from primary navigation
3.  which config objects were moved under Settings / Planning Configuration
4.  whether Procurement Planning still triggers any second-sidebar behavior
5.  any Frappe/ERPNext limitations that still affect the ideal IA

---

**Implementation report (repo, 2026-04-23)**

1. **Workspace / sidebar** — The legacy Desk workspace `Procurement` was renamed to **`Procurement Home`** (fixture JSON + post-migrate patch). The primary **`Procurement`** workspace sidebar rail now lists, in order: **Procurement Home**, **Demand Intake & Approval** (display label; route target remains workspace `Demand Intake and Approval`), **Procurement Planning**, and **Settings** (collapsible block) with planning configuration DocTypes as children. **`Planning module navigation`** and **`Demand Intake`** sidebars still link back to **Procurement Home** so the Procurement rail is not replaced by a minimal child sidebar. **`procurement_home_workspace.js`** / **`procurement_home_workspace.css`** inject a home workbench (KPI subset from DIA + PP landing APIs, quick links). **`get_procurement_home_landing_data`** composes read-only KPIs from existing whitelisted landing functions.

2. **Removed from primary workflow nav** — No additional raw DocTypes were added as top-level peers; configuration DocTypes remain only under **Settings**.

3. **Settings / Planning configuration** — Templates, risk/KPI/decision/vendor profiles, plans, and packages remain under the **Settings** collapsible section (sidebar label simplified from the older “Settings — planning configuration” wording).

4. **Procurement Planning second sidebar** — The dedicated sidebar document is still named **`Planning module navigation`** (not `Procurement Planning`) so Frappe does not call `sidebar.setup("Procurement Planning")` and swap the parent rail; routine work stays on one Procurement sidebar.

5. **Limitations** — The Demand Intake workspace **document name** stays `Demand Intake and Approval` (Frappe identity); only the **sidebar label** uses “&”. **Procurement Home** does not yet show a full “recent activity” feed or deep-linked queue selection from KPI cards (cards navigate to the target workspace).