# KenTender — Seed Data Specification v1

Here is a **complete but still tractable Seed Data Specification v1** for KenTender, starting with the Strategy module and laying the groundwork for later Budget and Procurement work.

This is designed to be:

- realistic enough to feel like a real implementation
- small enough to understand and reset
- stable enough for UI and functional testing
- deterministic enough for Playwright and regression testing

**1\. Purpose**

This document defines the initial seed data required to support:

- workspace testing
- Strategy module UX testing
- Strategy builder functional testing
- early role-based access testing
- future downstream Budget and Procurement scenarios

This is **test-grade seed data**, not demo filler.

**2\. Seed design principles**

The seed dataset must satisfy these rules:

1.  **Minimal but realistic**  
    Enough data to exercise the product, but not so much that the UI becomes noisy.
2.  **Deterministic**  
    Same seed run produces the same records every time.
3.  **Layered**  
    Core data loads first, then Strategy, then later Budget and Procurement.
4.  **Readable**  
    Users, entities, plans, and records must have obvious names and business meaning.
5.  **Resettable**  
    Seed scripts must support clean refresh for repeated testing.
6.  **Scenario-driven**  
    The seed should support specific business stories, not random records.

**3\. Seed packs**

Use seed packs, not one giant dataset.

**3.1 Required seed packs**

**seed_core_minimal**

Loads:

- entities
- departments
- users
- roles
- basic workspace visibility prerequisites

**seed_strategy_empty**

Loads:

- core data only
- no Strategic Plans

Purpose:

- test empty-state UX

**seed_strategy_basic**

Loads:

- core data
- one realistic Strategic Plan with hierarchy

Purpose:

- test normal Strategy flow

**seed_strategy_extended**

Loads:

- core data
- two Strategic Plans
- fuller hierarchy

Purpose:

- test selection, list rendering, and hierarchy scale

Later, additional packs can be added:

- seed_budget_basic
- seed_procurement_requisition_basic
- seed_planning_basic

**4\. Reference organization model**

Use one primary entity first, with one secondary entity for future multi-entity testing.

**4.1 Procuring Entities**

| **Code** | **Name** | **Purpose** |
| --- | --- | --- |
| MOH | Ministry of Health | Primary test entity |
| MOE | Ministry of Education | Secondary future entity |

For v1 implementation, MOH is required. MOE is optional but recommended.

**4.2 Departments for MOH**

| **Code** | **Name** | **Purpose** |
| --- | --- | --- |
| CLIN-SERV | Clinical Services | Strategy / requisition testing |
| HR  | Human Resources | Workforce objectives |
| FIN | Finance | Budget and review flows |
| PROC | Procurement | Planning and tendering later |
| ICT | ICT Services | Optional future scenarios |

Minimum required now:

- CLIN-SERV
- FIN
- PROC
- HR

**4.3 Departments for MOE**

Optional for v1, but useful later:

| **Code** | **Name** |
| --- | --- |
| BASIC-EDU | Basic Education |
| FIN | Finance |
| PROC | Procurement |

**5\. User seed data**

This section only defines user accounts. Role mapping will be formalized in the next permissions document, but we need seeded users now.

**5.1 Required users**

|     |     |     |     |     |
| --- | --- | --- | --- | --- |
| **Username / Email** | **Display Name** | **Entity** | **Primary Department** | **Purpose** |
| administrator | Administrator | global | —   | system setup |
| [strategy.manager@moh.test](mailto:strategy.manager@moh.test) | Strategy Manager MOH | MOH | CLIN-SERV | create/edit plans |
| [planning.authority@moh.test](mailto:planning.authority@moh.test) | Planning Authority MOH | MOH | FIN | review/approval later |
| [requisitioner@moh.test](mailto:requisitioner@moh.test) | Requisitioner MOH | MOH | CLIN-SERV | later procurement flow |
| [planner@moh.test](mailto:planner@moh.test) | Procurement Planner MOH | MOH | PROC | later planning flow |
| [finance.reviewer@moh.test](mailto:finance.reviewer@moh.test) | Finance Reviewer MOH | MOH | FIN | later budget review |

Optional future:

- [strategy.manager@moe.test](mailto:strategy.manager@moe.test)
- [planner@moe.test](mailto:planner@moe.test)

**5.2 Password convention for local test only**

Use a single controlled local password for all non-admin test users:

Test@123

Do not use production-like secrets in seed scripts.

**6\. Core master data seed**

**6.1 Currency**

| **Code** | **Name** |
| --- | --- |
| KES | Kenya Shilling |

**6.2 Fiscal years / planning years**

For now, you do not need a full financial model, but you do need planning years that Strategy Targets can reference.

Required planning years:

- 2026
- 2027
- 2028
- 2029
- 2030

Optional:

- 2025 for baseline context

**7\. Strategy seed data — empty scenario**

**7.1 seed_strategy_empty**

This seed pack must create:

- MOH entity
- MOH departments
- required users
- Strategy workspace visibility for Strategy Manager and Planning Authority

It must **not** create any Strategic Plan.

Purpose:

- verify workspace empty state
- verify “New Strategic Plan” CTA
- verify no false records

Expected workspace state:

- “No strategic plans yet. Create one to begin.”

**8\. Strategy seed data — basic scenario**

**8.1 Overview**

This is the primary v1 scenario.

It should create one Strategic Plan for MOH with:

- 2 Programs
- 3 Objectives
- 4 Targets

This is enough to test:

- workspace populated state
- master-detail selection
- builder rendering
- node editing
- readiness counts
- measurement-type handling

**8.2 Strategic Plan**

|     |     |
| --- | --- |
| **Field** | **Value** |
| strategic_plan_name | MOH Strategic Plan 2026–2030 |
| procuring_entity | MOH |
| start_year | 2026 |
| end_year | 2030 |
| status | Draft |
| version_no | 1   |
| is_current_version | 1   |
| supersedes_plan | null |

Recommended stable document key behavior:

- let system autoname, but always query by strategic_plan_name in UI tests unless exact name is deterministic

**8.3 Programs**

**Program 1**

|     |     |
| --- | --- |
| **Field** | **Value** |
| program_title | Healthcare Access |
| program_code | P001 |
| strategic_plan | MOH Strategic Plan 2026–2030 |
| description | Expand equitable access to essential healthcare services across underserved areas. |
| order_index | 1   |

**Program 2**

|     |     |
| --- | --- |
| **Field** | **Value** |
| program_title | Workforce Development |
| program_code | P002 |
| strategic_plan | MOH Strategic Plan 2026–2030 |
| description | Strengthen health workforce capacity, deployment, and specialist availability. |
| order_index | 2   |

**8.4 Objectives**

**Objective 1**

|     |     |
| --- | --- |
| **Field** | **Value** |
| objective_title | Increase rural healthcare coverage |
| objective_code | O001 |
| program | Healthcare Access |
| strategic_plan | MOH Strategic Plan 2026–2030 |
| description | Improve population access to healthcare services in rural and underserved counties. |
| order_index | 1   |

**Objective 2**

|     |     |
| --- | --- |
| **Field** | **Value** |
| objective_title | Improve maternal health service access |
| objective_code | O002 |
| program | Healthcare Access |
| strategic_plan | MOH Strategic Plan 2026–2030 |
| description | Expand access to maternal care infrastructure and referral capability. |
| order_index | 2   |

**Objective 3**

|     |     |
| --- | --- |
| **Field** | **Value** |
| objective_title | Expand nursing and clinical workforce capacity |
| objective_code | O003 |
| program | Workforce Development |
| strategic_plan | MOH Strategic Plan 2026–2030 |
| description | Increase trained personnel and improve workforce deployment. |
| order_index | 1   |

**8.5 Targets**

This seed set must exercise different target semantics.

**Target 1 — Percentage**

|     |     |
| --- | --- |
| **Field** | **Value** |
| target_title | Rural healthcare coverage reaches 65 percent |
| objective | Increase rural healthcare coverage |
| program | Healthcare Access |
| strategic_plan | MOH Strategic Plan 2026–2030 |
| measurement_type | Percentage |
| target_period_type | Annual |
| target_period_value | 2027 |
| target_value_numeric | 65  |
| target_value_text | null |
| target_unit | Percent |
| baseline_value_numeric | 52  |
| baseline_value_text | null |
| baseline_year | 2025 |
| description | Increase national rural healthcare service coverage by 2027. |
| order_index | 1   |

**Target 2 — Percentage**

|     |     |
| --- | --- |
| **Field** | **Value** |
| target_title | Rural healthcare coverage reaches 85 percent |
| objective | Increase rural healthcare coverage |
| program | Healthcare Access |
| strategic_plan | MOH Strategic Plan 2026–2030 |
| measurement_type | Percentage |
| target_period_type | End of Plan |
| target_period_value | 2030 |
| target_value_numeric | 85  |
| target_value_text | null |
| target_unit | Percent |
| baseline_value_numeric | 52  |
| baseline_value_text | null |
| baseline_year | 2025 |
| description | Achieve broad rural healthcare access by end of plan period. |
| order_index | 2   |

**Target 3 — Numeric**

|     |     |
| --- | --- |
| **Field** | **Value** |
| target_title | Additional maternal health facilities operational |
| objective | Improve maternal health service access |
| program | Healthcare Access |
| strategic_plan | MOH Strategic Plan 2026–2030 |
| measurement_type | Numeric |
| target_period_type | Annual |
| target_period_value | 2028 |
| target_value_numeric | 40  |
| target_value_text | null |
| target_unit | Facilities |
| baseline_value_numeric | 18  |
| baseline_value_text | null |
| baseline_year | 2025 |
| description | Expand operational maternal health facilities across priority counties. |
| order_index | 1   |

**Target 4 — Numeric**

|     |     |
| --- | --- |
| **Field** | **Value** |
| target_title | Nurses trained and deployed |
| objective | Expand nursing and clinical workforce capacity |
| program | Workforce Development |
| strategic_plan | MOH Strategic Plan 2026–2030 |
| measurement_type | Numeric |
| target_period_type | Annual |
| target_period_value | 2026 |
| target_value_numeric | 500 |
| target_value_text | null |
| target_unit | Staff |
| baseline_value_numeric | 0   |
| baseline_value_text | null |
| baseline_year | 2025 |
| description | Train and deploy additional nurses to underserved facilities. |
| order_index | 1   |

**9\. Strategy seed data — extended scenario**

**9.1 Purpose**

This pack is for:

- testing multiple plan selection in workspace
- testing list sorting
- testing counts and plan switching
- testing different statuses later

**9.2 Additional Strategic Plan**

Add a second plan:

|     |     |
| --- | --- |
| **Field** | **Value** |
| strategic_plan_name | MOH Service Delivery Improvement Plan 2027–2031 |
| procuring_entity | MOH |
| start_year | 2027 |
| end_year | 2031 |
| status | Draft |
| version_no | 1   |
| is_current_version | 0   |
| supersedes_plan | null |

This second plan can initially have:

- 1 Program
- 1 Objective
- 1 Target

Enough to verify multi-record behavior.

**10\. Workspace behavior expected from seed packs**

**10.1 With seed_strategy_empty**

Workspace should show:

- New Strategic Plan
- empty-state message
- no list items
- no selected detail panel

**10.2 With seed_strategy_basic**

Workspace should show:

- at least 1 plan in Strategic Plans list
- first plan selected by default
- selected plan detail panel
- counts:
    - Programs: 2
    - Objectives: 3
    - Targets: 4
- Open Strategy Builder
- Edit Plan

**10.3 With seed_strategy_extended**

Workspace should show:

- 2 plans in list
- switching selection updates detail panel
- counts change correctly by selected plan

**11\. Builder behavior expected from seed packs**

**11.1 With seed_strategy_basic**

Builder should show:

**Left tree**

- Healthcare Access
    - Increase rural healthcare coverage
        - Rural healthcare coverage reaches 65 percent
        - Rural healthcare coverage reaches 85 percent
    - Improve maternal health service access
        - Additional maternal health facilities operational
- Workforce Development
    - Expand nursing and clinical workforce capacity
        - Nurses trained and deployed

**Right panel**

- when no node selected: guidance message
- when Program selected: Program fields
- when Objective selected: Objective fields
- when Target selected: Target fields appropriate to measurement type

**12\. Seed naming conventions**

Keep all names readable and reusable in testing.

**Plans**

Use format:

&lt;ENTITY&gt; Strategic Plan &lt;START&gt;–&lt;END&gt;

**Programs**

Use short business labels, not coded-only names.

**Objectives**

Use result-oriented language.

**Targets**

Use plain English commitments.

This matters because UI tests and manual reviews are easier when records are understandable.

**13\. Seed implementation rules**

**13.1 Idempotency**

Each seed pack must be safe to run repeatedly.

Preferred approach:

- create by stable natural key if absent
- update if present
- do not duplicate

**13.2 Layer dependency**

Packs must load in order:

seed_core_minimal

→ seed_strategy_empty OR seed_strategy_basic OR seed_strategy_extended

**13.3 Deterministic ordering**

Programs, Objectives, Targets must have stable order_index values.

**13.4 No random test junk**

Do not create records like:

- Plan 1
- Test Program
- Objective abc
- Target xyz

The only acceptable exception is ephemeral UI-created records during manual testing.

**14\. Functional stories supported by this seed**

This v1 seed must support these stories:

**Story 1 — Empty strategy workspace**

“As a Strategy Manager, when no plans exist, I see a clear empty state and can create a new plan.”

**Story 2 — Populated strategy workspace**

“As a Strategy Manager, I see existing plans in the workspace and can open one.”

**Story 3 — Builder navigation**

“As a Strategy Manager, I can open the builder and see the hierarchy.”

**Story 4 — Typed target behavior**

“As a Strategy Manager, I can distinguish percentage and numeric targets.”

**Story 5 — Multi-plan selection**

“As a Strategy Manager, I can switch between plans in the workspace.”

**15\. Playwright-friendly seeded assertions**

These are the kinds of values your tests should look for.

**Workspace assertions**

- MOH Strategic Plan 2026–2030
- Healthcare Access
- Workforce Development
- Programs: 2
- Objectives: 3
- Targets: 4

**Builder assertions**

- Increase rural healthcare coverage
- Rural healthcare coverage reaches 65 percent
- Nurses trained and deployed

Prefer these business labels over document IDs.

**16\. Seed script packaging recommendation**

Implement seed scripts in a controlled structure like:

kentender_core/seeds/

seed_core_minimal.py

seed_strategy_empty.py

seed_strategy_basic.py

seed_strategy_extended.py

And expose safe commands or bench tasks to run them.

Recommended command style:

bench execute kentender_core.seeds.seed_core_minimal.run

bench execute kentender_core.seeds.seed_strategy_basic.run

Or a wrapper:

bench execute kentender_core.seeds.run_pack --kwargs "{'pack': 'strategy_basic'}"

**17\. What is intentionally excluded from v1 seed**

Do not include yet:

- budgets
- requisitions
- procurement plans
- tenders
- actual progress tracking
- approval history
- archived strategy versions
- indicator libraries
- public portal data

This is Strategy-first seed data.

**18\. Acceptance criteria for this specification**

This seed specification is complete only if it can support:

- empty-state testing
- one-plan workspace testing
- multi-plan workspace testing
- builder tree testing
- basic target-type testing
- role-based visibility testing later

This specification now does that.

**Cursor-ready implementation prompt**

Use this to make Cursor implement the seeds exactly.

Implement KenTender Seed Data Specification v1 exactly.

Create seed packs:

1.  seed_core_minimal
2.  seed_strategy_empty
3.  seed_strategy_basic
4.  seed_strategy_extended

Use stable, idempotent seed logic.

Core data must include:

- Procuring Entity: MOH (required), MOE (optional)
- Departments for MOH:
    - CLIN-SERV / Clinical Services
    - HR / Human Resources
    - FIN / Finance
    - PROC / Procurement
- Currency: KES
- Users:
    - administrator
    - [strategy.manager@moh.test](mailto:strategy.manager@moh.test)
    - [planning.authority@moh.test](mailto:planning.authority@moh.test)
    - [requisitioner@moh.test](mailto:requisitioner@moh.test)
    - [planner@moh.test](mailto:planner@moh.test)
    - [finance.reviewer@moh.test](mailto:finance.reviewer@moh.test)

seed_strategy_basic must create:

- Strategic Plan: MOH Strategic Plan 2026–2030
- Programs:
    - Healthcare Access
    - Workforce Development
- Objectives:
    - Increase rural healthcare coverage
    - Improve maternal health service access
    - Expand nursing and clinical workforce capacity
- Targets:
    - Rural healthcare coverage reaches 65 percent
    - Rural healthcare coverage reaches 85 percent
    - Additional maternal health facilities operational
    - Nurses trained and deployed

Use exact field values from the specification.  
Do not create random or placeholder seed names.  
Do not add downstream procurement seed data yet.

At the end provide:

1.  files created
2.  seed pack entry points
3.  idempotency approach
4.  commands to run each pack