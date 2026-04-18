**📘 KenTender — Strategy Module PRD v2 (MVP)**

**1\. 🎯 Core Goal**

Define a structured strategic hierarchy that all downstream modules (Budget, Requisition, Planning) must link to.

**2\. 📌 Scope**

**✅ INCLUDED (MVP)**

- Entity Strategic Plan creation
- Program definition
- Sub-program definition
- Output Indicator definition
- Performance Target definition
- Hierarchical linkage enforcement
- Approval and activation workflow

**❌ EXCLUDED (MVP)**

- National plan API integration (use static/mock data)
- Advanced reporting dashboards
- Strategy performance tracking
- Cross-version comparison tools
- Complex multi-version branching

**3\. 👤 Primary Users**

- **Strategy Manager**
    - Creates and structures plans
- **Planning Authority**
    - Reviews and approves plans
- **All other roles**
    - Read-only (consume structure downstream)

**4\. 🔁 Core Workflow (NON-NEGOTIABLE)**

Create Plan → Define Programs → Define Sub-programs → Define Indicators → Define Targets → Submit → Approve → Activate

No alternate flows in MVP.

**5\. 🧩 UX DESIGN (CRITICAL)**

**5.1 Entry Point**

Workspace: **“Strategy Management”**

**5.2 Screens**

**A. Strategic Plan List**

Columns:

- Plan Name
- Entity
- Period
- Status
- Version

Actions:

- Create New Plan
- Open Plan

**B. Strategic Plan Workspace (PRIMARY UI)**

⚠️ This is NOT a long form.

**Layout**

**🔹 Header (fixed)**

- Plan Name
- Entity
- Period
- Status
- Version

**🔹 Progress Indicator (top bar)**

\[ Plan Info ✓ \] → \[ Programs \] → \[ Sub-programs \] → \[ Indicators \] → \[ Targets \] → \[ Review \]

**🔹 Main Work Area (Tabbed / Step-based)**

**TAB 1 — Plan Info**

Fields:

- Plan Name (required)
- Entity (required)
- Period Start Year (required)
- Period End Year (required)

**TAB 2 — Programs**

Table:

| Program Code | Name | Linked National Objective | Description |

Actions:

- Add Program
- Edit
- Delete

Validation:

- Must link to National Objective (use dropdown/mock data)

**TAB 3 — Sub-programs**

Table:

| Sub-program Code | Name | Parent Program | Description |

Validation:

- Cannot exist without Program

**TAB 4 — Indicators**

Table:

| Indicator Code | Name | Sub-program | Unit | Baseline | Target |

Validation:

- Must have:
    - Unit
    - Numeric baseline or default

**TAB 5 — Targets**

Table:

| Indicator | Period | Target Value | Responsible Dept |

Validation:

- Must link to Indicator
- Must be numeric

**TAB 6 — Review & Submit**

Shows:

- Summary counts:
    - Programs
    - Sub-programs
    - Indicators
    - Targets

Validation panel:

- Missing linkages
- Empty required tables

Actions:

- Submit Plan

**6\. 🧱 DATA MODEL (MINIMAL)**

**6.1 Strategic Plan**

Fields:

- plan_id
- entity
- period_start
- period_end
- status
- version

**6.2 Program**

Fields:

- program_code
- name
- national_objective
- plan_id

**6.3 Sub-program**

Fields:

- sub_program_code
- name
- program_id

**6.4 Output Indicator**

Fields:

- indicator_code
- name
- sub_program_id
- unit
- baseline_value

**6.5 Performance Target**

Fields:

- target_id
- indicator_id
- period
- target_value
- department

**7\. 🔒 VALIDATION RULES (STRICT)**

**Structural Rules**

- Program MUST link to National Objective
- Sub-program MUST link to Program
- Indicator MUST link to Sub-program
- Target MUST link to Indicator

**Blocking Rules**

System must BLOCK:

\- Submit if no Programs exist

\- Submit if no Sub-programs exist

\- Submit if no Indicators exist

\- Submit if no Targets exist

**Data Rules**

- Target Value must be numeric
- Indicator must have unit
- Codes must be unique per plan

**8\. 🔄 WORKFLOW STATES**

| **State** | **Meaning** |
| --- | --- |
| Draft | Editable |
| Submitted | Locked, awaiting approval |
| Approved | Approved but not active |
| Active | In use by system |
| Archived | Historical |

**Transitions**

Draft → Submitted → Approved → Active → Archived

**9\. 🔐 PERMISSIONS**

| **Action** | **Role** |
| --- | --- |
| Create/Edit Plan | Strategy Manager |
| Submit Plan | Strategy Manager |
| Approve Plan | Planning Authority |
| Activate Plan | Planning Authority |
| View | All roles |

**10\. 🔗 INTEGRATION CONTRACTS (CRITICAL)**

**Budget Module MUST use:**

- Sub-program
- Indicator

**Requisition Module MUST use:**

- Indicator
- Target

**Planning Module MUST use:**

- Full chain (Program → Target)

👉 These fields must be selectable from Strategy module only (no free text)

**11\. ⚠️ SYSTEM RULE (CRITICAL)**

No Budget, Requisition, or Plan Item can be created without valid Strategy linkage

**12\. 🧪 MVP ACCEPTANCE CRITERIA**

The module is ONLY complete if:

**1\. Usability**

- User can create full strategy in <10 minutes
- No scrolling-heavy forms
- No confusion about next step

**2\. Navigation**

- Strategy workspace accessible from menu
- No hidden forms (no CTRL+K dependency)

**3\. Data Integrity**

- No orphan entities possible
- All relationships enforced

**4\. Persistence**

- Save → reload → data intact

**5\. Integration Readiness**

- Other modules can fetch:
    - Programs
    - Sub-programs
    - Indicators
    - Targets

**13\. 🧪 SMOKE TEST (MANDATORY)**

**Test: Strategy Creation Flow**

Steps:

1.  Login as Strategy Manager
2.  Create new Strategic Plan
3.  Add Program
4.  Add Sub-program
5.  Add Indicator
6.  Add Target
7.  Submit Plan
8.  Approve Plan
9.  Activate Plan

**Expected Result:**

- No errors
- No missing fields
- Plan becomes Active
- All entities visible in dropdowns elsewhere

**14\. 🚫 WHAT MUST NOT HAPPEN**

- ❌ Long scrolling forms
- ❌ Hidden required fields
- ❌ Disconnected screens
- ❌ Free-text strategy fields
- ❌ Partial linkage allowed

**15\. 🔧 CURSOR / WINDSURF IMPLEMENTATION BRIEF**

Implement Strategy Module as a guided workspace, not a form.

1\. Create “Strategy Management” workspace

2\. Plan must open in step-based/tabs UI:

\- Plan Info

\- Programs

\- Sub-programs

\- Indicators

\- Targets

\- Review

3\. Each step uses tables (not long forms)

4\. Enforce strict parent-child linkage

5\. Block submission if any layer is missing

6\. Use dropdowns for all linkages (no free text)

7\. Keep UI minimal and progressive (no overload)

8\. Workflow states must be enforced

9\. No editing after submission except via proper state control

10\. Ensure other modules can query strategy data cleanly

**💥 Final Note (Important)**

This module is your **foundation layer**.

If this is:

- clean
- simple
- enforced

👉 everything downstream becomes easier

If this is:

- complex
- messy
- form-heavy

👉 you will rebuild again

**🚀 Next Step**

Before building:

👉 I strongly recommend we do:

**Strategy UX Wireframe (visual + layout rules for Cursor)**

Because this is where things broke last time.

Say:

**“Design Strategy UX wireframe”**

and we lock the UI before any code is written.