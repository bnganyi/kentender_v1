**KenTender — Users, Roles & Permissions Specification v1**

**1\. Purpose**

This document defines the initial user, role, workspace visibility, and permission model required to support:

- Strategy module implementation
- workspace and builder UX testing
- role-based UI testing
- future Budget and Procurement expansion
- separation between normal business users and setup/admin users

This is a **build-grade v1 permission model**, not a final enterprise IAM design.

**2\. Design principles**

Use these rules:

1.  **Business roles first**  
    Permissions must be expressed in business terms, not only raw Frappe system roles.
2.  **Minimal viable access model**  
    Implement only the roles needed for the current Strategy-first phase, while defining the near-future Procurement roles now.
3.  **Entity-scoped by default**  
    Most users should only see records for their assigned Procuring Entity.
4.  **Least privilege**  
    A user should see only the workspaces and records needed for their job.
5.  **One workspace should not imply full module ownership**  
    Viewing, editing, approving, and administering are separate capabilities.
6.  **Administrator is not a business test user**  
    Administrator is only for setup, troubleshooting, and emergency inspection.

**3\. User model**

Each seeded business user must have these core attributes.

|     |     |     |
| --- | --- | --- |
| **Attribute** | **Required** | **Description** |
| email / username | ✓   | login identity |
| full_name | ✓   | display name |
| enabled | ✓   | active status |
| procuring_entity | ✓   | primary entity scope |
| primary_department | ✓   | business department |
| business_role | ✓   | primary business role |
| system_roles | ✓   | assigned Frappe roles needed to operate |
| can_login | ✓   | Desk access enabled |

**4\. Role architecture**

Use two layers:

**4.1 System / platform roles**

These are technical Frappe roles needed to make users operational.

Examples:

- Desk User
- System Manager
- All
- Guest (framework only, not business-assigned)

**4.2 Business roles**

These are the actual product-facing roles.

Required v1 business roles:

- Strategy Manager
- Planning Authority
- Requisitioner
- Procurement Planner
- Finance Reviewer

Optional later:

- Procurement Manager
- Evaluator
- Tender Committee Member
- Store Officer
- Asset Officer
- Internal Auditor

**5\. User catalogue v1**

**5.1 Required users**

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| **Username / Email** | **Full Name** | **Entity** | **Department** | **Business Role** | **Purpose** |
| administrator | Administrator | global | —   | System Administrator | setup only |
| [strategy.manager@moh.test](mailto:strategy.manager@moh.test) | Strategy Manager MOH | MOH | CLIN-SERV | Strategy Manager | manage strategy |
| [planning.authority@moh.test](mailto:planning.authority@moh.test) | Planning Authority MOH | MOH | FIN | Planning Authority | review / approve later |
| [requisitioner@moh.test](mailto:requisitioner@moh.test) | Requisitioner MOH | MOH | CLIN-SERV | Requisitioner | later PR creation |
| [planner@moh.test](mailto:planner@moh.test) | Procurement Planner MOH | MOH | PROC | Procurement Planner | later planning |
| [finance.reviewer@moh.test](mailto:finance.reviewer@moh.test) | Finance Reviewer MOH | MOH | FIN | Finance Reviewer | later budget review |

Optional future users:

- [strategy.manager@moe.test](mailto:strategy.manager@moe.test)
- [planner@moe.test](mailto:planner@moe.test)

**6\. Role definitions**

**6.1 System Administrator**

**Purpose**

Technical owner of the environment.

**Workspace visibility**

- all workspaces
- all setup/admin areas

**Record visibility**

- all records across all entities

**Allowed actions**

- create/update seed data
- inspect all records
- assign roles
- fix configuration
- access all workspaces

**Forbidden business assumption**

- should not be used as the main business validation user for Strategy workflows

**Required system roles**

- System Manager
- Desk User

**6.2 Strategy Manager**

**Purpose**

Owns Strategy planning work for an entity.

**Workspace visibility**

- Strategy

**Record visibility**

- Strategic Plans for own Procuring Entity only
- Programs for own entity’s plans
- Objectives for own entity’s plans
- Targets for own entity’s plans

**Allowed actions**

- create Strategic Plan
- edit Draft Strategic Plan
- open Strategy Builder
- create/edit/delete Programs
- create/edit/delete Objectives
- create/edit/delete Targets
- view plan counts and hierarchy
- later submit plan for review

**Forbidden actions**

- approve or activate plan
- view or edit other entities’ plans
- access Procurement or Budget workspaces unless separately assigned

**Required system roles**

- Desk User
- Strategy Manager

**6.3 Planning Authority**

**Purpose**

Oversight and review role for Strategy.

**Workspace visibility**

- Strategy

**Record visibility**

- Strategic Plans for own Procuring Entity
- full hierarchy for own entity

**Allowed actions (v1)**

- view plans
- open Strategy Builder in read-only or limited edit mode depending on implementation choice
- review plan content

**Allowed actions (later)**

- approve / activate plan
- archive superseded plan version

**Forbidden actions**

- create or freely edit strategy hierarchy unless explicitly delegated
- access other entities’ data

**Required system roles**

- Desk User
- Planning Authority

**6.4 Requisitioner**

**Purpose**

Future procurement demand originator.

**Workspace visibility (v1)**

- none for Strategy
- later Procurement only

**Record visibility (v1)**

- no Strategy records unless policy later allows read-only visibility

**Allowed actions (v1)**

- none in Strategy

**Forbidden actions**

- create/edit Strategic Plans
- open Strategy Builder
- view planning administration screens

**Required system roles**

- Desk User
- Requisitioner

**6.5 Procurement Planner**

**Purpose**

Future owner of procurement planning.

**Workspace visibility (v1)**

- none for Strategy editing
- later Procurement / Planner Workbench

**Record visibility (v1)**

- optionally read-only Strategy summary later if needed for downstream alignment
- no Strategy editing now

**Allowed actions (v1)**

- none in Strategy editing

**Forbidden actions**

- create/edit Strategy hierarchy
- approve Strategic Plans

**Required system roles**

- Desk User
- Procurement Planner

**6.6 Finance Reviewer**

**Purpose**

Future budget review and financial alignment role.

**Workspace visibility (v1)**

- no Strategy editing workspace
- optional read-only Strategy visibility later if policy requires

**Record visibility**

- none for Strategy editing in v1

**Allowed actions (v1)**

- none in Strategy

**Forbidden actions**

- create/edit Strategic Plans
- edit Strategy hierarchy

**Required system roles**

- Desk User
- Finance Reviewer

**7\. Workspace visibility matrix v1**

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| **Workspace** | **Administrator** | **Strategy Manager** | **Planning Authority** | **Requisitioner** | **Procurement Planner** | **Finance Reviewer** |
| Strategy | Yes | Yes | Yes | No  | No  | No  |
| Budget | Yes | No  | Later optional | No  | No  | Later Yes |
| Procurement | Yes | No  | No  | Later Yes | Later Yes | No  |

For current implementation, only the Strategy workspace needs to be operational.

**8\. Strategic Plan permissions matrix v1**

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| **Action** | **Administrator** | **Strategy Manager** | **Planning Authority** | **Requisitioner** | **Procurement Planner** | **Finance Reviewer** |
| Read own-entity Strategic Plan | Yes | Yes | Yes | No  | No  | No  |
| Read other-entity Strategic Plan | Yes | No  | No  | No  | No  | No  |
| Create Strategic Plan | Yes | Yes | No  | No  | No  | No  |
| Edit Draft Strategic Plan | Yes | Yes | No\* | No  | No  | No  |
| Delete Draft Strategic Plan | Yes | Yes | No  | No  | No  | No  |
| Open Strategy Builder | Yes | Yes | Yes (read-only or limited) | No  | No  | No  |
| Submit Strategic Plan | Yes | Later Yes | No  | No  | No  | No  |
| Approve Strategic Plan | Yes | No  | Later Yes | No  | No  | No  |
| Activate Strategic Plan | Yes | No  | Later Yes | No  | No  | No  |
| Archive Strategic Plan | Yes | No  | Later Yes | No  | No  | No  |

\* Planning Authority edit access should default to **No** in v1. If needed for implementation simplicity, allow only inspection, not mutation.

**9\. Strategy Program / Objective / Target permissions matrix v1**

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| **Action** | **Administrator** | **Strategy Manager** | **Planning Authority** | **Requisitioner** | **Procurement Planner** | **Finance Reviewer** |
| Read hierarchy for own entity | Yes | Yes | Yes | No  | No  | No  |
| Create Program | Yes | Yes | No  | No  | No  | No  |
| Edit Program | Yes | Yes | No  | No  | No  | No  |
| Delete Program | Yes | Yes | No  | No  | No  | No  |
| Create Objective | Yes | Yes | No  | No  | No  | No  |
| Edit Objective | Yes | Yes | No  | No  | No  | No  |
| Delete Objective | Yes | Yes | No  | No  | No  | No  |
| Create Target | Yes | Yes | No  | No  | No  | No  |
| Edit Target | Yes | Yes | No  | No  | No  | No  |
| Delete Target | Yes | Yes | No  | No  | No  | No  |

This preserves a simple ownership model for v1:

- Strategy Manager edits
- Planning Authority reviews
- everyone else stays out

**10\. Record visibility rules**

These are the key record-level rules.

**10.1 Entity scoping**

A business user may only see Strategy records where:

record.procuring_entity == user.procuring_entity

or equivalent derived scope through Strategic Plan parentage.

**10.2 Parent-derived visibility**

For Program, Objective, and Target:

- visibility is inherited from the parent Strategic Plan’s entity

**10.3 Administrator exception**

Administrator can see all records.

**10.4 No broad cross-role visibility yet**

Requisitioner, Procurement Planner, and Finance Reviewer should not see Strategy records in v1 unless a future read-only dependency is explicitly implemented.

**11\. UI behavior rules by role**

**11.1 Strategy workspace**

**Strategy Manager**

Must see:

- Strategy Desk icon
- Strategy Management workspace
- New Strategic Plan button
- Strategic Plans list
- Open Strategy Builder

**Planning Authority**

Must see:

- Strategy Desk icon
- Strategy Management workspace
- Strategic Plans list
- Open Strategy Builder
- no New Strategic Plan button in v1

**Requisitioner / Procurement Planner / Finance Reviewer**

Must not see:

- Strategy Desk icon
- Strategy Management workspace
- Strategy Builder route via normal navigation

**Administrator**

Sees all

**11.2 Strategy Builder page**

**Strategy Manager**

- full access to add/edit/delete hierarchy nodes

**Planning Authority**

Recommended v1:

- view access only
- no add/edit/delete buttons  
    If implementation simplicity demands temporary access, note it clearly and treat as transitional, not final.

**Other business roles**

- no access

**12\. Technical role mapping recommendation**

Use explicit Frappe roles with these names:

|     |     |
| --- | --- |
| **Business Role** | **Frappe Role Name** |
| Strategy Manager | Strategy Manager |
| Planning Authority | Planning Authority |
| Requisitioner | Requisitioner |
| Procurement Planner | Procurement Planner |
| Finance Reviewer | Finance Reviewer |

Assign Desk User to all business users who need Desk access.

Do **not** try to infer permissions only from Department names.

**13\. Permission implementation rules**

**13.1 Do not rely only on DocType-level broad permissions**

You need both:

- DocType permission
- record-level filtering by entity

**13.2 Use entity-based permission helpers**

For Strategy-related DocTypes:

- Strategic Plan
- Strategy Program
- Strategy Objective
- Strategy Target

permission queries must filter by entity scope.

**13.3 UI must respect backend permission**

Do not hide buttons in UI while leaving backend APIs open.

Buttons and APIs must align.

**14\. Minimal v1 implementation decisions**

To stay tractable, use these exact decisions:

1.  **Only Strategy Manager can mutate Strategy data in v1**
2.  **Planning Authority is read-only in v1**
3.  **Other business users have no Strategy visibility in v1**
4.  **Administrator remains unrestricted**
5.  **All non-admin visibility is entity-scoped**

These five rules are enough to implement now without getting trapped in policy detail.

**15\. Test matrix v1**

This is the minimum role-based test coverage you need.

|     |     |     |     |     |
| --- | --- | --- | --- | --- |
| **Test** | **Administrator** | **Strategy Manager** | **Planning Authority** | **Requisitioner** |
| Strategy icon visible | Yes | Yes | Yes | No  |
| Strategy workspace opens | Yes | Yes | Yes | No  |
| New Strategic Plan visible | Yes | Yes | No  | No  |
| Existing plans visible | Yes | Yes | Yes | No  |
| Open Strategy Builder visible | Yes | Yes | Yes | No  |
| Add Program in Builder | Yes | Yes | No  | No  |
| Add Objective in Builder | Yes | Yes | No  | No  |
| Add Target in Builder | Yes | Yes | No  | No  |
| Edit/Delete hierarchy nodes | Yes | Yes | No  | No  |

This is enough for first real role-aware UI testing.

**16\. Seed alignment rules**

Your seed users must align exactly with this spec.

Required mappings:

|     |     |
| --- | --- |
| **User** | **Business Role** |
| [strategy.manager@moh.test](mailto:strategy.manager@moh.test) | Strategy Manager |
| [planning.authority@moh.test](mailto:planning.authority@moh.test) | Planning Authority |
| [requisitioner@moh.test](mailto:requisitioner@moh.test) | Requisitioner |
| [planner@moh.test](mailto:planner@moh.test) | Procurement Planner |
| [finance.reviewer@moh.test](mailto:finance.reviewer@moh.test) | Finance Reviewer |

Each must also have:

- MOH entity assignment
- primary department assignment

**17\. Playwright user strategy**

Do not keep testing only as Administrator.

**Required UI test users for current Strategy phase**

- Strategy Manager
- Planning Authority
- Requisitioner

Why:

- Strategy Manager proves mutation
- Planning Authority proves read-only review
- Requisitioner proves hidden access

That is the minimal meaningful set.

**18\. What is intentionally deferred**

Do not define yet:

- committee-based permissions
- multi-entity delegated access
- field-level sensitivity masking
- approval delegation chains
- temporary acting roles
- separation-of-duty conflict engine
- public portal access

These belong in later governance and compliance layers.

**19\. Acceptance criteria for this specification**

This specification is complete only if it can support:

- Strategy workspace visible only to intended roles
- Strategy mutation restricted to Strategy Manager
- Planning Authority review access without edit access
- non-Strategy users excluded
- entity-scoped record visibility
- role-based Playwright testing

This document now does that.

**Cursor-ready implementation prompt**

Use this as the implementation prompt.

Implement Users, Roles & Permissions Specification v1 for the Strategy module exactly.

Create or configure business roles:

- Strategy Manager
- Planning Authority
- Requisitioner
- Procurement Planner
- Finance Reviewer

Assign seeded users to these roles exactly as specified.

Implement v1 Strategy access model:

1.  Strategy workspace visibility

- Visible to:
    - Administrator
    - Strategy Manager
    - Planning Authority
- Hidden from:
    - Requisitioner
    - Procurement Planner
    - Finance Reviewer

1.  Strategic Plan permissions

- Strategy Manager:
    - read/create/edit/delete Draft Strategic Plans for own entity
    - open Strategy Builder
- Planning Authority:
    - read-only access for own entity
    - open Strategy Builder in read-only mode
- Other business roles:
    - no Strategy access

1.  Strategy Program / Objective / Target permissions

- Strategy Manager:
    - full create/edit/delete for own entity
- Planning Authority:
    - read-only
- Others:
    - no access

1.  Entity scoping

- All Strategy records must be visible only within the user’s assigned procuring entity
- Administrator can see all

1.  UI alignment

- Hide or disable mutation actions for Planning Authority
- Do not show Strategy workspace or builder links to non-Strategy roles

Do not implement advanced delegation or committee rules yet.  
Do not broaden visibility beyond this specification.

At the end provide:

1.  roles created/configured
2.  user-role mappings
3.  permission rules implemented
4.  entity-filtering mechanism used
5.  known temporary limitations

**Recommended next step**

Now that you have:

- Seed Data Specification v1
- Users, Roles & Permissions Specification v1

the correct next move is:

1.  implement roles and seeded users
2.  switch Playwright Strategy tests to:
    - Strategy Manager
    - Planning Authority
    - Requisitioner
3.  validate:
    - visible
    - read-only
    - hidden

That is where your product starts behaving like a real system instead of a developer sandbox.