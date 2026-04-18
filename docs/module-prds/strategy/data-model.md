**📘 Strategy Module — Data Model + API Contract (MVP)**

This is based on the Strategy structure already defined in your original PRD, but simplified and tightened for implementation control

**1\. Design Goals**

The model must guarantee:

- strict parent-child hierarchy
- no orphan records
- easy downstream lookup
- simple UI building
- safe approval / activation flow
- minimal schema for MVP

**2\. Canonical Hierarchy**

Strategic Plan

→ Program

→ Sub-program

→ Output Indicator

→ Performance Target

For MVP, that is enough.

We are **not** including the full national framework import model yet.

**3\. Core Data Model**

**3.1 Strategic Plan**

**Purpose**

Top-level entity-owned planning container.

**Fields**

| **Field** | **Type** | **Required** | **Notes** |
| --- | --- | --- | --- |
| name | String / ID | Yes | system-generated |
| plan_name | String | Yes | human-readable title |
| entity | Link | Yes | procuring entity |
| period_start_year | Int | Yes | e.g. 2026 |
| period_end_year | Int | Yes | e.g. 2030 |
| version_no | Int | Yes | default 1 |
| workflow_state | Enum | Yes | Draft / Submitted / Approved / Active / Archived |
| is_locked | Bool | Yes | derived/control field |
| remarks | Text | No  | optional |

**Rules**

- unique per entity + version + period
- only one Active plan per entity per overlapping period unless later config says otherwise

**3.2 Program**

**Purpose**

Primary strategy grouping under a plan.

**Fields**

| **Field** | **Type** | **Required** | **Notes** |
| --- | --- | --- | --- |
| name | String / ID | Yes | system-generated |
| strategic_plan | Link | Yes | parent plan |
| program_code | String | Yes | unique within plan |
| program_name | String | Yes | display title |
| national_objective_ref | String/Link | Yes | mock/static for MVP |
| description | Text | No  | optional |
| sort_order | Int | No  | UI ordering |

**Rules**

- unique program_code within a plan
- cannot exist without parent Strategic Plan

**3.3 Sub-program**

**Purpose**

Child of Program.

**Fields**

| **Field** | **Type** | **Required** | **Notes** |
| --- | --- | --- | --- |
| name | String / ID | Yes | system-generated |
| strategic_plan | Link | Yes | denormalized parent for query ease |
| program | Link | Yes | parent |
| sub_program_code | String | Yes | unique within plan |
| sub_program_name | String | Yes | display title |
| description | Text | No  | optional |
| sort_order | Int | No  | UI ordering |

**Rules**

- parent program must belong to same strategic_plan
- unique sub_program_code within a plan

**3.4 Output Indicator**

**Purpose**

Measurable output under a Sub-program.

**Fields**

| **Field** | **Type** | **Required** | **Notes** |
| --- | --- | --- | --- |
| name | String / ID | Yes | system-generated |
| strategic_plan | Link | Yes | denormalized parent |
| program | Link | Yes | denormalized parent |
| sub_program | Link | Yes | parent |
| indicator_code | String | Yes | unique within plan |
| indicator_name | String | Yes | display title |
| unit_of_measure | String | Yes | e.g. Number, %, Km |
| baseline_value | Float | No  | optional for MVP |
| description | Text | No  | optional |
| sort_order | Int | No  | UI ordering |

**Rules**

- sub_program must belong to given program and strategic_plan
- unique indicator_code within plan

**3.5 Performance Target**

**Purpose**

Time-bound target attached to an indicator.

**Fields**

| **Field** | **Type** | **Required** | **Notes** |
| --- | --- | --- | --- |
| name | String / ID | Yes | system-generated |
| strategic_plan | Link | Yes | denormalized parent |
| program | Link | Yes | denormalized parent |
| sub_program | Link | Yes | denormalized parent |
| output_indicator | Link | Yes | parent |
| target_period_year | Int | Yes | e.g. 2026 |
| target_value | Float | Yes | numeric for MVP |
| responsible_department | Link | Yes | department |
| notes | Text | No  | optional |
| sort_order | Int | No  | UI ordering |

**Rules**

- output_indicator must belong to stated hierarchy
- unique per output_indicator + target_period_year
- numeric only in MVP

**4\. Required Derived / Read-Only Fields**

These help the UI and downstream modules but should not be manually edited.

**On Strategic Plan**

- program_count
- sub_program_count
- indicator_count
- target_count

**On lower levels**

- display_label
- parent_display_label

**On all records**

- is_editable
- is_active_for_downstream_use

**5\. Naming Convention**

Keep names machine-friendly and separate from labels.

**Recommended IDs**

- Strategic Plan: SP-{ENTITY}-{STARTYEAR}-v{N}
- Program: PG-{PLAN}-{CODE}
- Sub-program: SPG-{PLAN}-{CODE}
- Indicator: IND-{PLAN}-{CODE}
- Target: TGT-{INDICATOR}-{YEAR}

The user should mostly see:

- program_name
- sub_program_name
- indicator_name

not raw IDs.

**6\. Workflow / State Logic**

Only **Strategic Plan** needs the formal workflow in MVP.

**Strategic Plan workflow**

Draft → Submitted → Approved → Active → Archived

**Lower-level records**

Do **not** give each child object its own full workflow in MVP.

They inherit control from the parent plan:

- if plan is Draft → children editable
- if plan is Submitted/Approved/Active → children locked unless revision flow exists later

This is important. Do not let Windsurf invent separate workflows for Program, Indicator, etc.

**7\. Locking Rules**

**Draft**

- everything editable

**Submitted**

- plan header locked
- children locked
- approver can review only

**Approved**

- still locked
- no downstream use yet unless explicitly activated

**Active**

- locked
- downstream modules can use data

**Archived**

- read-only, hidden from default operational selection

**8\. Validation Rules**

These are mandatory.

**Strategic Plan**

- period_start_year <= period_end_year
- plan_name required
- entity required

**Program**

- must have strategic_plan
- program_code unique within plan
- national_objective_ref required

**Sub-program**

- must have valid program
- parent plan consistency enforced

**Output Indicator**

- must have unit_of_measure
- must have valid sub_program
- hierarchy consistency enforced

**Performance Target**

- target_value required and numeric
- must have valid output_indicator
- hierarchy consistency enforced

**Submission validation**

Cannot submit plan unless:

- at least 1 Program
- at least 1 Sub-program
- at least 1 Indicator
- at least 1 Target
- no orphan child records
- no hierarchy mismatches

**9\. Downstream Consumption Contract**

This is where a lot of systems go wrong.

**Budget module must be able to fetch:**

- active sub_program
- active output_indicator

**Requisition module must be able to fetch:**

- active output_indicator
- active performance_target

**Planning module must be able to fetch:**

- active program
- active sub_program
- active output_indicator
- active performance_target

**Important rule**

Only records from:

- workflow_state = Active

should be selectable downstream.

**10\. API Contract**

Keep the API thin and explicit.

**10.1 Strategic Plan APIs**

**POST /api/strategy/plans**

Create a draft plan.

**Request**

{

"plan_name": "MOH Strategic Plan 2026-2030",

"entity": "MOH",

"period_start_year": 2026,

"period_end_year": 2030

}

**Response**

{

"name": "SP-MOH-2026-v1",

"workflow_state": "Draft"

}

**GET /api/strategy/plans**

List plans, filterable by:

- entity
- workflow_state
- year

**GET /api/strategy/plans/{plan_id}**

Return full plan header + summary counts.

**POST /api/strategy/plans/{plan_id}/submit**

Validate and move Draft → Submitted.

**POST /api/strategy/plans/{plan_id}/approve**

Move Submitted → Approved.

**POST /api/strategy/plans/{plan_id}/activate**

Move Approved → Active.

**POST /api/strategy/plans/{plan_id}/archive**

Move Active/Approved → Archived, subject to policy.

**10.2 Program APIs**

**POST /api/strategy/plans/{plan_id}/programs**

Create Program under a plan.

**Request**

{

"program_code": "P01",

"program_name": "Healthcare Services",

"national_objective_ref": "OBJ-HEALTH-001",

"description": "Improve public health access"

}

**GET /api/strategy/plans/{plan_id}/programs**

List programs for plan.

**PUT /api/strategy/programs/{program_id}**

Edit program, only if parent plan is Draft.

**DELETE /api/strategy/programs/{program_id}**

Delete program, only if no dependent children or use safe cascade policy.

**10.3 Sub-program APIs**

**POST /api/strategy/plans/{plan_id}/sub-programs**

{

"program": "PG-SP-MOH-2026-v1-P01",

"sub_program_code": "SP01",

"sub_program_name": "District Hospitals"

}

**GET /api/strategy/plans/{plan_id}/sub-programs**

**PUT /api/strategy/sub-programs/{id}**

**DELETE /api/strategy/sub-programs/{id}**

**10.4 Output Indicator APIs**

**POST /api/strategy/plans/{plan_id}/indicators**

{

"program": "PG-...",

"sub_program": "SPG-...",

"indicator_code": "IND01",

"indicator_name": "Diagnostic Equipment Coverage",

"unit_of_measure": "Number",

"baseline_value": 10

}

**GET /api/strategy/plans/{plan_id}/indicators**

**PUT /api/strategy/indicators/{id}**

**DELETE /api/strategy/indicators/{id}**

**10.5 Performance Target APIs**

**POST /api/strategy/plans/{plan_id}/targets**

{

"program": "PG-...",

"sub_program": "SPG-...",

"output_indicator": "IND-...",

"target_period_year": 2026,

"target_value": 25,

"responsible_department": "Clinical Services"

}

**GET /api/strategy/plans/{plan_id}/targets**

**PUT /api/strategy/targets/{id}**

**DELETE /api/strategy/targets/{id}**

**10.6 Downstream selector APIs**

These are very important for later modules.

**GET /api/strategy/active/programs?entity=MOH**

**GET /api/strategy/active/sub-programs?program=...**

**GET /api/strategy/active/indicators?sub_program=...**

**GET /api/strategy/active/targets?indicator=...**

These should return lightweight option payloads for dropdowns:

- id
- code
- name
- display_label

Do not return huge record blobs here.

**11\. Response Shape Standard**

Every API should use a consistent envelope.

**Success**

{

"ok": true,

"data": { ... },

"message": "Program created"

}

**Error**

{

"ok": false,

"error_code": "INVALID_HIERARCHY",

"message": "Selected sub-program does not belong to the specified program"

}

This matters because Windsurf will otherwise invent inconsistent responses.

**12\. UI-to-API Mapping**

This keeps implementation honest.

**Step 1 — Plan Info**

- POST /plans
- GET /plans/{id}

**Step 2 — Programs**

- GET /plans/{id}/programs
- POST /plans/{id}/programs
- PUT /programs/{id}

**Step 3 — Sub-programs**

- GET /plans/{id}/sub-programs
- POST /plans/{id}/sub-programs

**Step 4 — Indicators**

- GET /plans/{id}/indicators
- POST /plans/{id}/indicators

**Step 5 — Targets**

- GET /plans/{id}/targets
- POST /plans/{id}/targets

**Step 6 — Review**

- GET /plans/{id} summary
- POST /plans/{id}/submit

**13\. Minimal Server Services**

If you don’t want raw endpoint logic everywhere, define these services:

- create_strategic_plan
- create_program
- create_sub_program
- create_indicator
- create_target
- validate_plan_structure
- submit_plan
- approve_plan
- activate_plan

That is enough for MVP.

**14\. MVP Sanity Checks**

Before you move off Strategy, all of these must pass:

**Functional**

- create draft plan
- add all hierarchy levels
- submit
- approve
- activate

**Data integrity**

- cannot create orphan child
- cannot create mismatched hierarchy
- cannot activate incomplete plan

**UI**

- no long scrolling forms
- no dead links
- no hidden required steps

**Integration readiness**

- downstream dropdown APIs return active records only

**15\. Windsurf Implementation Brief**

Implement Strategy module using this strict data model and API contract.

Rules:

1\. Use exactly these entities:

\- Strategic Plan

\- Program

\- Sub-program

\- Output Indicator

\- Performance Target

2\. Use hierarchy:

Strategic Plan -> Program -> Sub-program -> Output Indicator -> Performance Target

3\. Only Strategic Plan has workflow:

Draft -> Submitted -> Approved -> Active -> Archived

4\. Child objects do not get independent workflow in MVP.

Their editability depends on parent plan state.

5\. Enforce parent-child consistency on every create/update.

6\. Provide explicit CRUD endpoints for each child level under a plan.

7\. Provide active-selector endpoints for downstream modules.

8\. Use consistent API envelopes:

{ ok, data, message } or { ok, error_code, message }

9\. Do not invent extra states, hidden fields, or alternate hierarchy levels.

10\. UI must consume this model through the step-based builder already defined.

**16\. My opinion before you build this**

This is the right level of strictness.

If you keep:

- data model minimal
- workflow only on plan
- hierarchy rigid
- API explicit

then Windsurf has much less room to cause sprawl.

If you loosen any of those too early, you will be back in reconstruction mode again.

The next best step is to define the **Strategy MVP sanity checklist + smoke test contract** before any implementation starts.