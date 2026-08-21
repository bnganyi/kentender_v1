**CHANGE UNIT**

**NDS-CHG-001**

**Departmental Needs boundary, ownership and lifecycle**

**Module:** Departmental Needs

**Status:** Proposed for approval

**Version:** 0.2

**Documentation standard:** Integrated revision-ledger change unit

**Authority:** PPADA 2015 and Public Procurement and Asset Disposal Regulations, 2020

**Controlling decision:** The existing user-facing Demands module is replaced by Departmental Needs. A Departmental Need is a simple internal planning input; it is not a Procurement Requisition and does not initiate procurement.

# 1\. Decision

Replace the current user-facing Demands module with Departmental Needs.

A Departmental Need allows ordinary departmental users to state what their department expects to require without confronting procurement classifications, procurement methods, formal specifications, bills of quantities or approval procedures.

**Departmental Need → Departmental Procurement Planning → Approved Plan Item → Procurement Requisition → Tender preparation**

The formal Procurement Requisition remains a separate, later module.

# 2\. Legal and procedural grounding

Section 53 of the Public Procurement and Asset Disposal Act requires annual procurement planning to be realistic, integrated with the applicable budget process and prepared before the financial year begins.

Regulation 34 assigns the User Department responsibility for initiating requirements, preparing and submitting technical specifications, and preparing departmental procurement and asset-disposal plans. Regulation 40 assigns the Head of User Department responsibility for submitting the annual departmental procurement plan.

Departmental Needs is therefore a KenTender internal control supporting these responsibilities. It is not a statutory procurement approval or prescribed procurement form. The later statutory and operational controls remain attached to procurement planning, requisition and procurement processing.

**Interpretive boundary:** The legislation assigns responsibilities to the User Department but does not require every ordinary staff member to complete procurement classifications or formal technical schedules at the first expression-of-need stage.

# 3\. Functional boundary

## 3.1 Departmental Needs shall support

- Plain-language capture of an anticipated departmental requirement.
- One or more simple need lines containing Description, Indicative quantity and Unit.
- Business justification or the problem to be addressed.
- Required-by date and delivery or use location.
- Target financial year, including a future financial year whose needs-intake window is open.
- Optional indicative cost where the submitting department knows it.
- Supporting attachments.
- Departmental review before the Need becomes eligible for procurement planning.
- Traceable full or partial use of an accepted Need in Procurement Planning.

## 3.2 Departmental Needs shall not

- Initiate a procurement proceeding.
- Create a Procurement Requisition, Tender or tender document.
- Reserve, commit or certify funds.
- Determine the procurement method.
- Require the ordinary requester to select a procurement category or requirement type.
- Require formal specifications, bills of quantities, schedules of requirements or Terms of Reference.
- Confer Procurement Function, Head of Procurement Function or Accounting Officer approval.
- Allow a Procurement Planner to alter the source Need.

Formal specifications and structured requirements remain the User Department's responsibility, but they are completed during formal requisition preparation rather than imposed on the ordinary user submitting an initial Need.

# 4\. Ownership and scope

Every Departmental Need shall be owned by one Procuring Entity, one organisational unit or User Department, one target financial year and one submitting user.

- One effective assignment: fix the PE and organisational-unit context automatically.
- Multiple effective assignments: require explicit context selection.
- No effective assignment: block creation and explain that an organisational assignment is required.
- PE and financial-year filters alter the view only; they never grant access, ownership or operational authority.
- Future financial years may be selected when their configured departmental-needs intake window is open. An annual Plan does not need to exist yet.

# 5\. Lifecycle and state model

| **Current state** | **Permitted action**  | **Result**            |
| ----------------- | --------------------- | --------------------- |
| Draft             | Submit                | Submitted             |
| Draft             | Withdraw              | Withdrawn             |
| Submitted         | Return for correction | Returned              |
| Submitted         | Accept for planning   | Accepted for planning |
| Submitted         | Do not take forward   | Not taken forward     |
| Returned          | Resubmit              | Submitted             |
| Returned          | Withdraw              | Withdrawn             |

Canonical lifecycle states are Draft, Submitted, Returned, Accepted for planning, Not taken forward and Withdrawn.

Accepted for planning means only that the department considers the Need suitable for consideration in its procurement plan. It is not procurement approval, budget confirmation or authority to procure.

## 5.1 Planning usage is a separate projection

- Not included
- Partially included
- Fully included

The Need's lifecycle state must not be overwritten when Procurement Planning consumes it.

# 6\. Downstream planning rules

- Only effective Accepted for planning Needs may be selected in Procurement Planning.
- The Procurement Planner may combine, split or partially allocate accepted Need lines into Draft Plan Items.
- Every allocation must retain the originating Need and Need-line references.
- A Draft Plan allocation does not constitute final consumption.
- Planning usage changes to Partially included or Fully included only when the allocation becomes part of an Approved Plan Version.
- Removing an allocation through an approved Plan amendment recalculates Planning usage.
- An accepted Need may remain outside the Plan; acceptance does not compel inclusion.
- A Need represented in an Approved Plan cannot be withdrawn directly. The Approved Plan must first be amended.
- No Departmental Need may directly generate a Procurement Requisition.

# 7\. Roles and capabilities

| **Role or assignment**       | **Departmental Needs authority**                                                                           |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Departmental Need Requester  | Create and edit own Draft or Returned Needs; submit; withdraw before acceptance.                           |
| Head of User Department      | Review submitted Needs within the assigned department; return, accept for planning or decline.             |
| Departmental Review Delegate | Perform explicitly delegated departmental review within the assigned scope.                                |
| Procurement Planner          | Read accepted Needs for assigned PEs and allocate them in Planning; cannot edit or review the source Need. |
| Budget Officer               | Relevant read-only visibility; no confirmation or approval action in Departmental Needs.                   |
| Accounting Officer           | Read-only oversight; no routine Need-level approval.                                                       |
| System Administrator         | Audited read-only support access; no operational action unless separately assigned an operational role.    |

Role membership alone is insufficient. Every operational command requires an effective PE, organisational-unit and time-bound assignment.

# 8\. NDS-UI-01 — Static workspace design specification

**Design-tool constraint:** This section defines one exact static screen. Runtime permissions, transitions, validation, loading and saving behavior belong only to the implementation controls.

## 8.1 Signed-in context

| **Field**        | **Exact fixture**                        |
| ---------------- | ---------------------------------------- |
| Signed-in user   | Dr Peter Kimani                          |
| Role             | Head of User Department                  |
| Procuring Entity | Ministry of Health                       |
| Department       | Directorate of Digital Health and Policy |
| Planning year    | 2027/28                                  |

## 8.2 Page content

- Breadcrumb: Home > Departmental Needs
- Title: Departmental Needs
- Description: Capture and review departmental requirements for procurement planning.
- Context line: Procuring Entity: Ministry of Health | Department: Directorate of Digital Health and Policy | Planning year: 2027/28 | Change
- Primary action: Create need

## 8.3 Summary

| **Total needs** | **Awaiting departmental review** | **Accepted for planning** | **Included in approved plan** |
| --------------- | -------------------------------- | ------------------------- | ----------------------------- |
| 3               | 1                                | 1                         | 1                             |

## 8.4 Work requiring action

| **Reference**    | **Need**                                               | **Submitted by** | **Required by** | **Status** | **Action** |
| ---------------- | ------------------------------------------------------ | ---------------- | --------------- | ---------- | ---------- |
| NDS-MOH-2027-002 | Digital health technical staff certification programme | Grace Wanjiku    | 31 October 2027 | Submitted  | Review     |

## 8.5 Departmental needs table

| **Need**                                                                    | **Indicative requirement** | **Required by** | **Status**            | **Planning usage** | **Action** |
| --------------------------------------------------------------------------- | -------------------------- | --------------- | --------------------- | ------------------ | ---------- |
| National digital health infrastructure upgrade <br>NDS-MOH-2027-001         | 1 programme                | 31 August 2027  | Accepted for planning | Fully included     | View       |
| Digital health technical staff certification programme <br>NDS-MOH-2027-002 | 120 staff                  | 31 October 2027 | Submitted             | Not included       | Review     |
| Regional health-facility connectivity equipment <br>NDS-MOH-2027-003        | 120 sets                   | 15 January 2028 | Returned              | Not included       | View       |

## 8.6 Exclusions from the screen

- Procurement method or requirement type
- Funding confirmation or budget balances
- Procurement or Accounting Officer approval
- Requisition or Tender status
- BOQ, specification or Terms-of-Reference completion
- Charts, dashboards or a progress stepper

# 9\. Implementation controls

## 9.1 Canonical records

- DepartmentalNeed
- DepartmentalNeedItem
- DepartmentalNeedReview
- PlanNeedAllocation

## 9.2 Mandatory controls

- Make /departmental-needs the only Departmental Needs route. Do not create a /demands compatibility route or redirect.
- Enforce PE, organisational-unit, financial-year and assignment scope on the server for every query and command.
- Record every submission, return, acceptance, decline and withdrawal in an immutable audit trail.
- Require a reason when returning or declining a Need.
- Make accepted Need content immutable to Procurement Planning users.
- Keep Plan allocation and Need lifecycle state as separate projections.
- Prevent direct Procurement Requisition or Tender creation from a Need.
- Create no financial reservation, commitment or confirmation from a Need command.
- Make commands idempotent and concurrency-safe.
- Expose administrative support access through an audited read-only projection, not operational permission escalation.

# 10\. Clean-build implementation strategy

**Implementation mandate:** Departmental Needs shall be implemented from scratch against a fresh schema and fresh seed data. There will be no legacy data migration, compatibility layer or reuse of the old Demands implementation.

- Create the Departmental Needs domain, routes, services, permissions, workflows, tests and seed fixtures as new implementation units.
- Do not reuse, extend or rename legacy Demand DocTypes, models, services, endpoints, workflow definitions, status values, permissions, tests or fixtures.
- Do not migrate Demand records, item rows, decisions, funding allocations, strategy references, state histories, attachments or planning-consumption records.
- Do not create compatibility adapters, mapping tables, legacy-reference fields, redirects, shadow writes, dual reads, feature flags or fallback queries for the old Demands module.
- Remove the old Demands navigation entry, route registration and operational entry points from the new build.
- Use /departmental-needs as the only canonical route and the NDS identifiers defined by this ledger as the only new record references.
- Initialize the module only in a fresh development, test or deployment database. Resetting an existing environment is a deployment prerequisite where legacy records are present.
- Generate all development and acceptance-test records exclusively from the seed contract in this revision ledger.
- Treat legacy Demands documents and code only as non-authoritative historical material. They must not supply requirements, defaults or implementation patterns.
- Connect Departmental Needs to Procurement Planning only through the new PlanNeedAllocation contract defined by the approved revision-ledger units.

# 11\. Seed and role-test data

| **Principal**                    | **Assignment and expected authority**                                                        |
| -------------------------------- | -------------------------------------------------------------------------------------------- |
| <grace.wanjiku@moh.example.test> | Departmental Need Requester for the Directorate of Digital Health and Policy.                |
| <peter.kimani@moh.example.test>  | Head of User Department for the Directorate of Digital Health and Policy.                    |
| <mercy.kilonzo@moh.example.test> | Procurement Planner for the Ministry of Health; read and planning-allocation authority only. |
| MOH Budget Officer               | Read-only Departmental Needs visibility.                                                     |
| System Administrator             | Audited read-only support visibility; no Departmental Needs operational authority.           |

Seed the three exact Needs defined in NDS-UI-01.

For NDS-MOH-2027-001, seed an approved allocation to Plan PLN-MOH-2027-001, Approved Plan Version 1 and Plan Item PPI-MOH-2027-021.

Do not seed a Procurement Requisition from any of these Needs.

# 12\. Acceptance criteria

| **ID**     | **Acceptance criterion**                                                                                                                    |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| NDS-AC-001 | The user-facing module and only canonical route are Departmental Needs and /departmental-needs.                                             |
| NDS-AC-002 | Users can create Needs only within an effective PE and department assignment.                                                               |
| NDS-AC-003 | A future open planning year is selectable even when no annual Plan exists.                                                                  |
| NDS-AC-004 | Ordinary requesters are not required to select procurement classifications or methods.                                                      |
| NDS-AC-005 | Only the Head of User Department or an effective delegate can conduct departmental review.                                                  |
| NDS-AC-006 | The affirmative departmental decision is labelled Accepted for planning, never Approved.                                                    |
| NDS-AC-007 | Acceptance creates no funding reservation, procurement authority or Procurement Requisition.                                                |
| NDS-AC-008 | Budget Officers have no confirmation action in Departmental Needs.                                                                          |
| NDS-AC-009 | Procurement Planners cannot edit the source Need.                                                                                           |
| NDS-AC-010 | System Administrators can inspect records read-only with audit logging.                                                                     |
| NDS-AC-011 | Need lifecycle state and Planning usage remain separate.                                                                                    |
| NDS-AC-012 | Only accepted Needs are eligible for Plan allocation.                                                                                       |
| NDS-AC-013 | A Draft Plan allocation does not mark a Need as included in an Approved Plan.                                                               |
| NDS-AC-014 | Every Plan allocation preserves Need-line lineage.                                                                                          |
| NDS-AC-015 | No Need can directly create a Procurement Requisition or Tender.                                                                            |
| NDS-AC-016 | No legacy Demand schema, record, route, workflow, service, permission, test or fixture is present in the Departmental Needs implementation. |
| NDS-AC-017 | No migration, compatibility adapter, redirect, dual-read or fallback behavior exists for the old Demands module.                            |
| NDS-AC-018 | A fresh environment can create the entire Departmental Needs schema and exact seed dataset without legacy prerequisites.                    |
| NDS-AC-019 | Cross-PE and cross-department access tests fail closed.                                                                                     |

# 13\. Change impact and supersession

- Establishes Departmental Needs as a greenfield module; the old Demands implementation is retired rather than migrated or refactored.
- Removes Budget confirmation, Procurement Function final approval and funding reservation from the Departmental Needs boundary.
- Preserves the useful plain-language need-capture capability and PE/organisational-unit ownership controls.
- Requires a separate Procurement Requisitions workstream after the Departmental Needs and Procurement Planning boundaries are reconciled.
- Updates the approved Procurement Planning module only through a new upstream PlanNeedAllocation contract; no legacy Demand conversion is required.
- Reduces implementation risk and agent workload by eliminating legacy-state reconciliation, compatibility code and migrated test data.

# 14\. Next change unit

**Next:** NDS-CHG-002 — Departmental Need capture, items and submission, including exact creation, edit, submission, return and review screens; implementation validation; seed variants; and smoke contracts.

# Sources

1\. Public Procurement and Asset Disposal Act, 2015, section 53 — [Kenya Law consolidated text](https://new.kenyalaw.org/akn/ke/act/2015/33/eng@2022-12-31)

2\. Public Procurement and Asset Disposal Regulations, 2020, regulations 34, 40, 42, 52 and 54 — [Kenya Law consolidated text](https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng@2022-12-31)