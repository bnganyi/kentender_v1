# Procurement Planning — MVP 1 Requirements

**Document ID:** PLANNING-MVP1-REQ-1.4  
**Status:** Approved MVP 1 functional baseline  
**Date:** 9 August 2026  
**Change control:** Approval locks the MVP 1 functional baseline; later functional changes require a new version  
**Module:** Procurement Planning  
**Application:** KenTender  
**Primary fixture:** Ministry of Health  
**Secondary fixture:** County Government of Kisumu

**Revision 1.4:** Retains the 1.3 field model and applies it across the complete Planning journey: filters, selectors, confirmations, decision comments, reporting periods, revision reasons and derived evidence are now unambiguous in every screen.

**Approval note:** Version 1.4 is the authoritative Requirements baseline. Any earlier `REQ-1.0` or unversioned repository copy is obsolete and must be replaced before implementation.

## Source baseline

### Authoritative Kenyan sources

- [Constitution of Kenya, Article 227](https://new.kenyalaw.org/akn/ke/act/2010/constitution/eng%402010-09-03)
- [Public Procurement and Asset Disposal Act, 2015](https://new.kenyalaw.org/akn/ke/act/2015/33/eng%402022-12-31), particularly sections 53, 54 and 91
- [Public Procurement and Asset Disposal Regulations, 2020](https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng%402020-12-24), particularly Regulations 33, 34 and 40–43, Regulation 50 and the Third Schedule

### International reference standards

- [OECD Recommendation of the Council on Public Procurement](https://legalinstruments.oecd.org/en/instruments/OECD-LEGAL-0411)
- [World Bank Procurement Regulations for IPF Borrowers, Seventh Edition](https://thedocs.worldbank.org/en/doc/c84273d1b230aeb2b0b8134de5dc8cd7-0290012025/original/Procurement-Regulations-7th-Edition-Sep-2025.pdf)
- [World Bank Project Procurement Strategy for Development guidance](https://thedocs.worldbank.org/en/doc/ae0f8a5bf130bce9c3bf23f088a6c3a9-0290012024/original/PPSD-Procurement-Guidance-FINAL-Aug-24-WEB.pdf)
- [Open Contracting Data Standard](https://standard.open-contracting.org/latest/en/primer/how/)

### KenTender baselines

- `DEMAND-MVP1-REQ-1.4`
- `BUDGET-MVP1-REQ-1.1`
- `STRATEGY-MVP1-REQ-1.1`
- KenTender Procuring Entity and Organisation Scope Model
- KenTender MVP Canonical Demo Data Contract, version 2.4
- KenTender Statutory and Public-Value Obligations Matrix, version 1.1
- Previous Procurement Planning v2 PRD, used only as an indicative source inventory

Where sources conflict, applicable Kenyan law and binding financing agreements prevail. International references inform value for money, proportionality, competition, integration, risk, transparency and lifecycle data; they shall not create extra approval stages or screens.

Before production use, the configured approval routes, thresholds, allocation rules and publication obligations shall be verified against the law and official instruments then in force. This document defines the product control pattern; it is not a substitute for entity-specific legal advice.

---

## 1. Purpose

Procurement Planning converts approved, funded Demands into an approved and executable annual procurement plan.

It shall give ordinary users one clear journey:

> **Approved Demand → Plan Item → Consolidated Plan Approval → Tender take-up**

The module shall answer:

1. Which approved needs will the Procuring Entity procure during the planning period?
2. How are those needs grouped, scheduled, funded and assigned a procurement method?
3. Does the consolidated plan comply with statutory planning and policy-allocation requirements?
4. Which Organisation Unit proposed and owns each requirement?
5. Who reviewed and approved the plan?
6. Which approved Plan Items have entered Tender Management, and are they progressing to schedule?

Procurement Planning is not a generic package builder. It is the governed consolidation and execution bridge between Approved Demands and Tender Management.

---

## 2. Legal and standards baseline

### 2.1 Kenyan legal requirements

MVP 1 shall implement these requirements directly:

| Requirement | System treatment |
|---|---|
| Fair, equitable, transparent, competitive and cost-effective procurement | Explainable planning decisions, open competition by default, recorded alternatives and auditable approval |
| Annual, realistic procurement plan within the approved budget | One consolidated, versioned annual plan per Procuring Entity and financial year |
| Departmental plans submitted for consolidation | Organisation Unit-owned Plan Items plus a compact departmental submission sign-off |
| Goods, works and services required | Plan Item category and description derived from Approved Demands |
| Planned delivery, implementation or completion schedule | Planned milestones on every Plan Item; actual milestones derived downstream |
| Single-year or multi-year arrangement | Explicit arrangement and annual funding schedule |
| Aggregation and lotting | Simple aggregation, split and indicative-lot decisions with reasons |
| Estimated value, available budget and source of funds | Read-only Demand/Budget funding context plus Plan Item estimate |
| Procurement method | Method recommendation, confirmation and legal basis |
| Transfer responsibility and timing, where justified | Optional transfer treatment with responsible entity, authority and timing; no generic extra workflow |
| Applicable incidental procurement costs | Revalidate that the approved estimate includes applicable insurance, logistics, warehousing, advertising and related costs |
| Open tender as the preferred method | Open competition is the default; alternatives require the applicable legal grounds |
| Prevention of contract splitting | Automated potential-splitting checks and mandatory justification for divided scope |
| Preference and reservation allocations | Plan-level statutory allocation tracking and validation |
| Consolidated plan approval | Configured approval route reflecting the Procuring Entity type and applicable law |
| E-procurement preparation and publication | Approved-plan publication/export status and State Portal integration boundary |
| Quarterly implementation reporting | Derived execution reporting from Plan Items, Tenders and later lifecycle records |
| No procurement without sufficient approved funds | Funding and reservation revalidation before plan approval and Tender take-up |

### 2.2 International good-practice treatment

The module shall apply international standards through a few practical controls:

- **Value for money:** consider cost, quality, timeliness, delivery risk and whole-life implications where applicable.
- **Competition:** default toward open competition and explain any restricted method.
- **Integration:** retain stable links from Strategy, Budget and Demand through Tender and Contract.
- **Efficiency:** identify aggregation opportunities, avoid duplicate procurements and reuse governed defaults.
- **Proportionality:** apply more analysis only where value, complexity or risk justifies it.
- **Integrity and accountability:** preserve immutable decisions, reasons, versions and handoffs.
- **Transparency:** structure approved planning data for authorised publication and open-contracting export.
- **Evaluation:** compare planned and actual procurement milestones without manual duplication.

These controls shall remain explainable. MVP 1 shall not use opaque scoring or autonomous planning decisions.

---

## 3. Lifecycle boundary

### 3.1 Inputs

Planning consumes, but does not own:

- Approved Demand and approved Demand baseline;
- Demand Items and remaining Planning availability;
- Procuring Entity and Organisation Unit ownership;
- confirmed estimate and currency;
- Budget and Budget Line references;
- funding allocations and reservation identities;
- Strategy Target references and snapshots;
- Plan Value Commitments and upstream treatment decisions; and
- supporting evidence and approvals required for traceability.

### 3.2 Outputs

Planning owns:

- logical Procurement Plan, its current Approved version and any single open Draft revision;
- immutable Procurement Plan versions;
- stable Plan Items and versioned Plan Item snapshots;
- Demand-to-Plan allocation records;
- departmental submission evidence;
- planning method, schedule, aggregation, lotting and policy-allocation decisions;
- plan validation results;
- planning review and approval decisions;
- approved-plan publication status;
- immutable Planning Handoff Snapshot at Tender take-up; and
- planning implementation projections and audit events.

### 3.3 Boundary rule

Planning may read upstream records and create downstream handoff evidence. It shall not silently edit Strategy, Budget, reservation, Demand approval or Tender legal state.

An Active Plan Item in the current Approved Plan Version is permission to begin the next governed procurement stage; it is not a Tender, award, contract, commitment, expenditure or proof of realised public value.

---

## 4. MVP outcomes

MVP 1 shall enable a Procuring Entity to:

1. Register one consolidated annual Procurement Plan through a short form.
2. Surface eligible Approved Demands automatically.
3. Add eligible Demand Items to Plan Items without re-entering upstream information.
4. Preserve Organisation Unit ownership while consolidating at Procuring Entity level.
5. Confirm category, method, schedule, aggregation, indicative lotting and statutory treatments.
6. Validate the complete plan using business-readable issues.
7. Capture departmental submission, procurement review and required plan approval.
8. Lock the approved version and publish or export it through the applicable channel.
9. Start Tender preparation only from an Active Plan Item in the current Approved Plan Version.
10. Track actual take-up and schedule performance from downstream records.
11. Support controlled plan revisions without rewriting approved history.
12. Provide management reporting on execution, competition, funding, statutory allocations and public-value coverage.

---

## 5. Design principles

1. **The Plan Item is the working unit.** Users shall not navigate separate Inclusion, Package, Package Line and Release workbenches.
2. **One annual plan, many accountable contributors.** Organisation Units own their contributions; Procurement consolidates them under the Procuring Entity.
3. **Upstream data is reused, not retyped.** Demand, funding, Strategy and value context remain read-only Planning inputs.
4. **Planning adds planning decisions only.** Method, timing, aggregation, indicative lotting and policy treatment belong here.
5. **The plan is approved as a governed whole.** Item issues may be returned individually, but the approved baseline is one versioned consolidated plan.
6. **Validation is issue-led.** Passed checks stay quiet; users see blockers, warnings, owners and corrective actions.
7. **Approval, publication and execution are separate.** They shall not be compressed into one ambiguous status.
8. **Approved versions are immutable.** Corrections use a controlled revision.
9. **Tender take-up is direct.** Tender Management consumes an Approved Plan Item through a generated handoff snapshot; there is no manually managed release package.
10. **Codes are system managed.** Users work with names, fiscal years and meaningful context.
11. **Open competition is the default.** Alternative methods require applicable legal grounds and approval.
12. **Aggregation creates value; splitting requires scrutiny.** The system assists but an accountable planner confirms.
13. **Actual performance is derived.** Planning shall not ask users to re-enter dates already available downstream.
14. **Policy and public-value goals are carried forward.** The system shall distinguish planned treatment from realised results.
15. **No legacy dual-write.** Disposable MVP structures may be removed rather than preserved through compatibility layers.

---

## 6. Scope

### 6.1 Included

- Role- and scope-aware Procurement Planning workspace
- Direct annual-plan registration
- Organisation Unit contributions to one consolidated plan
- Approved Demand eligibility and selection
- Partial or full planning of eligible Demand Items
- Plan Item creation and editing
- Controlled aggregation of compatible Demand Items
- Controlled division of scope with anti-splitting checks
- Indicative lotting decision
- Goods, Works, Non-consulting Services and Consulting Services categories
- Procurement regime, method recommendation, confirmation and justification
- Single-year and multi-year treatment
- Procurement milestone planning
- Funding and reservation validation
- Statutory preference and reservation allocation tracking
- Strategy and Plan Value Commitment carry-forward
- Business-readable readiness validation
- Departmental contribution sign-off
- Consolidated review and approval
- Immutable approved versions and controlled revisions
- Approved-plan publication/export status
- Tender take-up through an immutable handoff snapshot
- Quarterly implementation and management reporting
- Notifications, audit, permissions and cross-entity isolation
- Repeatable Ministry and County fixtures
- Clean removal of obsolete Planning structures

### 6.2 Excluded

- Strategy, Budget or Demand creation and approval
- Editing Approved Demand scope or ownership
- Creating, increasing, moving or releasing Budget reservations
- Detailed market research or business-case authoring
- Detailed Tender lots and alternatives configuration
- STD selection beyond identifying the required family/category context
- Tender document configuration or generation
- Tender publication, bid submission, opening, evaluation or award
- Contract commitment, expenditure, inventory, asset or disposal management
- Detailed donor-project procurement strategy authoring
- Generic workflow, rule-profile, risk-profile or template builders
- AI-generated method approval or autonomous rejection
- Separate user workbenches for inclusions, packages, releases and consumption
- Full public transparency portal; MVP provides structured publication/export readiness
- Annual Asset Disposal Plan, which belongs to the future Disposal module

---

## 7. Actors and responsibilities

| Actor | Owns | Does not own |
|---|---|---|
| Organisation Unit Planning Contributor | Completeness of unit-owned planning inputs and proposed timing | Method approval, consolidated plan approval or funding mutation |
| Head of User Department | Submission of the unit's annual contribution and business accountability | Consolidation or final plan approval |
| Procurement Planner | Consolidation, Plan Items, method proposal, schedule, aggregation, lotting and validation resolution | Demand approval, Budget approval or Tender configuration |
| Head of Procurement Function / Planning Reviewer | Professional review, method and aggregation scrutiny, return or recommendation | Final approval where not legally assigned |
| Accounting Officer | Accountability for preparation, funding assurance and submission/approval action required by the configured legal route | Unrecorded delegation or silent bypass |
| Designated Plan Approver | Approval required for the entity type, such as the responsible Cabinet Secretary, County Executive Committee Member, board or equivalent authority | Day-to-day Plan Item preparation |
| Procurement Officer / Tender Initiator | Create a Tender from an Approved Plan Item and report a material planning issue | Edit the approved Planning baseline |
| Manager / Auditor | Oversight, quarterly reporting, lineage and evidence review | Operational mutation unless separately authorised |
| System Administrator | Configuration, role assignment and support | Planning, review or approval by virtue of administration alone |

The approval route shall be configured from the applicable entity type and legal regime. Role labels shall not hard-code a Ministry hierarchy into the data model.

---

## 8. User journey

### 8.1 Standard journey

1. **Open or create the annual plan.** Select the authorised Procuring Entity and financial year.
2. **Add Approved Demands.** Choose eligible needs from the planning queue.
3. **Complete Plan Items.** Confirm method, schedule, aggregation, lotting and statutory treatment.
4. **Submit departmental contributions.** Heads of User Departments sign off their scoped items.
5. **Validate and review.** Procurement resolves issues and submits the consolidated plan.
6. **Approve the plan.** Required authorities make recorded decisions and lock the approved version.
7. **Publish or export.** Record submission/publication to the required portal or channel.
8. **Start Tender preparation.** Tender Management consumes an Approved Plan Item through a handoff snapshot.
9. **Monitor execution.** Actual downstream dates and status update the approved plan's implementation view.

### 8.2 Additional need after approval

An Approved Demand arising after plan approval shall be added through a Draft successor version without taking the current Approved version out of operation:

1. The user selects **Add Plan Item** on the Approved Plan.
2. The system creates or opens the Plan's single Draft revision.
3. The new Plan Item is Proposed inside that Draft revision.
4. The current Approved version and its existing Plan Items remain operational.
5. Additional changes may be accumulated in the same Draft revision until it is submitted.
6. Only changed items and affected plan-level controls require active review; unchanged items are carried forward with traceable snapshots.
7. The revised consolidated Plan is validated and approved through the applicable route.
8. On approval, the Draft revision becomes the current Approved version, the former version becomes Superseded and the new Plan Item becomes Active and eligible for Tender take-up.
9. Existing Tender handoffs remain valid for unchanged carried-forward Plan Items.

The interface shall make the concurrent state explicit, for example: **Approved Version 1 · Draft Revision 2 in progress**. The user shall not have to create a revision before selecting **Add Plan Item**.

### 8.3 Material issue found by Tender Management

Tender Management shall raise a planning correction request. Planning shall either:

- correct non-material handoff metadata without changing the approved baseline; or
- create a Plan Revision for a material change.

Tender Management shall never edit the approved Plan Item directly.

---

## 9. State and projection model

### 9.1 Logical Procurement Plan lifecycle

Use only:

- Open
- Closed
- Cancelled

The logical Plan is the stable Procuring Entity and financial-year container. It does not become Draft merely because a revision is being prepared.

### 9.2 Procurement Plan Version status

Use only:

- Draft
- In review
- Returned
- Approved
- Superseded
- Cancelled

Only one current Approved version may exist for the logical Plan. A newly approved revision supersedes the prior current version without deleting it. Only one open Draft successor may exist at a time.

### 9.3 Plan Item baseline state

Use only:

- Proposed — first introduced in a Draft Plan Version
- Active — present in the current Approved Plan Version
- Removed — excluded by an Approved revision while retained for history

The Plan Item is the stable operational identity. Its approved planning values are carried by a Plan Item Version associated with the applicable Plan Version.

### 9.4 Separate projections

Do not turn every concern into a Plan status.

| Projection | Values |
|---|---|
| Validation | Not run, Ready, Needs attention, Blocked, Stale |
| Departmental contribution | Preparing, Submitted, Returned |
| Publication | Not submitted, Queued, Published, Failed, Not applicable |
| Tender take-up | Not taken up, Tender in preparation, Tender active, Contracted, Closed downstream |

### 9.5 Editing rules

- Draft and Returned versions are editable within the user's role and scope.
- In review is read-only except for recall or authorised return.
- Approved, Superseded and Cancelled versions are immutable.
- Closed and Cancelled logical Plans do not accept new revisions.
- Actual execution projections may update against an immutable Approved version because they are derived links, not baseline edits.
- A Draft revision does not suspend or invalidate the current Approved version.

---

## 10. Functional requirements

### 10.1 Planning workspace and plan registration

| ID | Requirement |
|---|---|
| PLN-FR-001 | The module shall be labelled **Procurement Planning**. |
| PLN-FR-002 | The landing page shall show the current authorised annual plan, Approved Demands awaiting planning, Returned work, Plan Items needing attention and approved items not yet taken up. |
| PLN-FR-003 | Counts, search, filters and exports shall use the same Procuring Entity and Organisation Unit scope as the underlying records. |
| PLN-FR-004 | Workspace context shall filter data only; it shall not silently select ownership for a new plan. |
| PLN-FR-005 | Plan registration shall use a short direct form containing only Procuring Entity, financial year, title, currency and coordinating procurement unit. |
| PLN-FR-006 | Procuring Entity selection shall follow the zero-, single- and multi-scope pattern in `DEMAND-MVP1-REQ-1.4`: zero eligible scopes block creation, one is visible and read-only, and multiple require explicit selection. |
| PLN-FR-007 | The system shall generate stable Plan and version references; users shall not enter codes. |
| PLN-FR-008 | The system shall maintain one logical Plan per Procuring Entity and financial year and prevent conflicting current Approved versions. |
| PLN-FR-009 | Organisation Units shall contribute scoped Plan Items to the consolidated entity plan rather than maintaining unrelated duplicate plan headers. |
| PLN-FR-010 | The plan shall show the configured contribution and approval deadlines before the financial year starts; a late action shall require a reason and remain visible for escalation and audit. |
| PLN-FR-011 | The workspace shall display the current Approved Plan Version and any open Draft revision as separate concurrent states. |
| PLN-FR-012 | A logical Plan shall have at most one open Draft successor revision; later changes shall join that revision until it is submitted, approved or cancelled. |
| PLN-FR-013 | Selecting the financial year shall derive the configured start and end dates. The planning period shall be displayed read-only and shall not be captured as free text. |
| PLN-FR-014 | Currency shall be a required controlled selection from the active ISO 4217 currencies permitted for the Procuring Entity. Where only one currency is permitted, it may be visibly preselected and read-only. |
| PLN-FR-014A | **Coordinating procurement unit** shall reference an active Organisation Unit configured to perform the procurement function for the selected Procuring Entity. It is not necessarily the lowest Organisation Unit; one eligible value shall be shown read-only and multiple eligible values shall require explicit selection. |
| PLN-FR-014B | Plan registration shall not capture a Budget context. Funding coverage shall be derived after creation from the approved Demands, Budget allocations and reservations included in the Plan. |

### 10.2 Eligible Demands and Plan Item creation

| ID | Requirement |
|---|---|
| PLN-FR-015 | The planning queue shall return only Approved, Planning Ready Demands within the selected Procuring Entity and authorised scope. |
| PLN-FR-016 | A Demand Item shall show its approved amount/quantity, amount already planned, remaining planning availability, owner unit, required-by date, funding and blockers. |
| PLN-FR-017 | Draft, Returned, Rejected, Cancelled or fully planned Demands shall not be selectable. |
| PLN-FR-018 | Selecting **Add to plan** shall create or update a stable Plan Item, its Draft Plan Item Version and a Draft Demand Allocation without changing the Approved Demand. |
| PLN-FR-019 | The Plan Item shall inherit human-readable Demand, Strategy, value and funding context as read-only source information. |
| PLN-FR-020 | Planning may allocate all or part of a Demand Item's remaining approved quantity or amount. |
| PLN-FR-021 | Effective Planning Consumption and Active Plan Item state shall be created only when the containing Plan Version is Approved; Draft allocations and Proposed items shall not make a Demand appear planned. |
| PLN-FR-022 | A Plan Item total shall equal its Demand Allocations and shall not exceed approved, unplanned and funded scope. |
| PLN-FR-023 | A planner shall not replace an upstream Budget Line, funding allocation, reservation, Strategy Target or Plan Value Commitment. |
| PLN-FR-024 | The Plan Item shall retain `procuring_entity`, `owner_org_unit` and optional `delivery_org_unit`; all source allocations shall belong to the same Procuring Entity. |

### 10.3 Plan Item planning decisions

| ID | Requirement |
|---|---|
| PLN-FR-030 | The planner shall confirm a concise requirement description that remains consistent with the Approved Demand baseline. |
| PLN-FR-031 | The planner shall confirm procurement category, method, planned schedule, arrangement duration, aggregation treatment, indicative lotting and statutory allocation treatment through controlled fields. The planner shall enter narrative only for the Plan Item description and reasons or treatment notes that require accountable explanation. |
| PLN-FR-032 | The system shall show funding source, approved estimate, reservation identity and source freshness as read-only context. |
| PLN-FR-033 | Material changes to scope, amount, ownership, beneficiaries or intended outcome shall be blocked and referred to the Demand process. |
| PLN-FR-034 | Single-year items shall fit the applicable plan period unless a justified cross-year completion date is allowed. |
| PLN-FR-035 | Multi-year items shall record justification, total estimate and annual funding schedule consistent with the medium-term budget context. |
| PLN-FR-036 | The system may recommend defaults but an accountable planner shall confirm the planning decisions. |
| PLN-FR-037 | Where transfer of procurement responsibility is justified, the Plan Item shall identify the receiving entity or agent, authority, scope and optimal transfer period; the formal transfer remains governed by the applicable process. |
| PLN-FR-038 | The system shall confirm that the approved estimate covers applicable incidental costs. If material insurance, logistics, clearing, warehousing, advertising or related costs are omitted, Planning shall return the item for upstream correction rather than silently increasing it. |
| PLN-FR-039 | Procurement category, method, arrangement, aggregation decision, lotting decision, statutory treatment and target groups shall use governed selections rather than free text. Planned milestone dates shall use date inputs. |

### 10.4 Aggregation, division and indicative lots

| ID | Requirement |
|---|---|
| PLN-FR-040 | The default shall be one Approved Demand converted into one Plan Item. |
| PLN-FR-041 | A planner may aggregate compatible Demand Items into one Plan Item within the same Procuring Entity where funding and reservation lineage can be preserved. |
| PLN-FR-042 | Aggregation shall record the reason and show the expected efficiency, competition or delivery benefit without claiming realised savings. |
| PLN-FR-043 | Potential duplicate or aggregation candidates shall be suggested from category, timing, owner, description and market context; suggestions shall not merge records automatically. |
| PLN-FR-044 | Dividing one Demand Item across Plan Items shall require a business reason and a server-side anti-splitting check. |
| PLN-FR-045 | The system shall block or escalate division intended to avoid an applicable procurement procedure, threshold or approval. |
| PLN-FR-046 | Planning shall record whether lots are expected, the indicative basis and optional expected lot count. Detailed lot structure remains a Tender Configuration decision. |

### 10.5 Procurement regime and method

| ID | Requirement |
|---|---|
| PLN-FR-050 | The governing procurement regime shall be derived read-only from the Procuring Entity, funding and applicable legal configuration. PPADA is the default unless a recorded binding financing agreement provides another procedure; the Plan Item editor shall not offer a free-text regime field. |
| PLN-FR-051 | Method options and conditions shall come from versioned legal/reference configuration, not hard-coded page logic. |
| PLN-FR-052 | The system shall recommend a method using category, value, conditions, competition, arrangement and governing regime. |
| PLN-FR-053 | Open tender shall be the preferred method under PPADA. Any alternative shall require the applicable grounds, evidence and approval. |
| PLN-FR-054 | The method decision shall retain recommendation, confirmed method, legal basis, actor, time and override reason where applicable. |
| PLN-FR-055 | A method shall not be changed on an Approved Plan Item except through an approved Plan Revision. |
| PLN-FR-056 | Planning shall identify the required broad STD family/category for handoff without configuring the tender document. |
| PLN-FR-057 | The method recommendation and legal basis shall be read-only outputs of the current rule configuration. The planner shall confirm a method from the permitted list; selecting a different permitted method shall require an override reason and applicable evidence. |

### 10.6 Procurement schedule

| ID | Requirement |
|---|---|
| PLN-FR-060 | Every Plan Item shall have planned milestones sufficient for the applicable annual plan format. |
| PLN-FR-061 | Milestones shall cover, where applicable, invitation/advertisement, opening, evaluation, award approval, notification, contract signature and delivery/completion. |
| PLN-FR-062 | The system shall propose milestone dates from the method, category, target completion and governed lead-time defaults. |
| PLN-FR-063 | A planner may adjust proposed dates using date inputs with a reason; the schedule shall remain chronologically valid and realistically fit the need and plan period. |
| PLN-FR-064 | Actual milestones shall be derived from Tender, Award, Contract and implementation records rather than re-entered in Planning. |
| PLN-FR-065 | Planned-versus-actual variance shall remain a reporting projection and shall not alter the Approved baseline. |

### 10.7 Preference, reservation and public-value treatment

| ID | Requirement |
|---|---|
| PLN-FR-070 | The plan shall track the applicable statutory preference and reservation allocation against the relevant plan-value basis. |
| PLN-FR-071 | Under PPADA, the system shall validate the applicable minimum allocation for enterprises owned by women, youth, persons with disabilities and other disadvantaged groups. |
| PLN-FR-072 | County plans shall additionally validate the applicable resident-tenderer allocation under the Regulations. |
| PLN-FR-073 | Allocation rules shall be versioned and effective-dated; users shall not maintain statutory percentages inside a Plan Item. |
| PLN-FR-074 | Every Plan Item shall record the applicable treatment through a controlled selection, target group where relevant, planned treatment value where applicable and rationale for Not applicable. |
| PLN-FR-075 | Strategy Targets and Plan Value Commitments shall flow from the Approved Demand as immutable references and readable snapshots. |
| PLN-FR-076 | Planning shall record how applicable commitments will be carried into method, schedule, packaging, specification or contract preparation, without claiming achievement. |
| PLN-FR-077 | Users shall not enter or maintain a statutory percentage on a Plan Item. The system shall calculate the current required plan-level value and coverage from the effective-dated rule and Plan totals, using Plan Item treatment values as contributions. |

### 10.8 Validation and readiness

| ID | Requirement |
|---|---|
| PLN-FR-080 | Validation shall run automatically on material save, submission, approval and Tender take-up. |
| PLN-FR-081 | Validation shall cover source Demand eligibility, allocation arithmetic, funding, ownership, category, method, schedule, aggregation/division, statutory allocations, departmental submissions, approvals and handoff integrity. |
| PLN-FR-082 | The user shall see only Ready, Needs attention or Blocking issues at summary level; passed technical checks shall remain collapsed. |
| PLN-FR-083 | Every issue shall state the affected Plan Item or plan, owner, reason and corrective action. |
| PLN-FR-084 | Blocking issues shall prevent submission, approval or Tender take-up as applicable. |
| PLN-FR-085 | Warnings may be acknowledged with a reason where the governing rule permits; acknowledgement shall not convert a legal blocker into a warning. |
| PLN-FR-086 | A material change shall make the prior validation Stale and require revalidation. |
| PLN-FR-087 | Users shall not manually set Ready status. |

### 10.9 Departmental submission, review and approval

| ID | Requirement |
|---|---|
| PLN-FR-090 | Each Organisation Unit's contribution shall be identifiable from its owned Plan Items. |
| PLN-FR-091 | The Head of User Department shall submit the unit contribution with a recorded actor, time and declaration that the requirements represent the unit's planned needs. |
| PLN-FR-092 | Procurement may return specific Plan Items or a unit contribution with actionable reasons. |
| PLN-FR-093 | Procurement shall consolidate submitted contributions, resolve cross-unit aggregation and run plan-level validation. |
| PLN-FR-094 | The Head of Procurement Function or configured reviewer shall record a professional recommendation, return or rejection. |
| PLN-FR-095 | The Accounting Officer shall perform the preparation, certification, submission or approval action required by the configured legal route. |
| PLN-FR-096 | Final approval shall be performed by the authority applicable to the Procuring Entity type and legal regime. |
| PLN-FR-097 | The UI shall show only the current required decision and prior decision trail; it shall not display a generic approval matrix to ordinary users. |
| PLN-FR-098 | Approval shall atomically lock the Plan Version and its Plan Item Versions, make Draft allocations effective, activate Proposed items, apply approved removals, supersede the prior current version where applicable and create an immutable approved snapshot. |

### 10.10 Revision, cancellation and closure

| ID | Requirement |
|---|---|
| PLN-FR-105 | An Approved Plan shall not be edited directly. |
| PLN-FR-106 | A revision shall create a Draft successor version with a controlled reason category, accountable narrative explanation, initiating actor and comparison to the current Approved version. |
| PLN-FR-107 | Only changed items and affected plan-level validations shall require active correction; unchanged items shall retain traceable snapshots. |
| PLN-FR-108 | Removing or reducing an untaken Plan Item shall reverse the applicable Planning Consumption only after the revision is approved. |
| PLN-FR-109 | A Plan Item already taken up by Tender Management shall not be materially changed without a linked downstream correction or cancellation process. |
| PLN-FR-110 | Cancelling a logical Plan or removing a Plan Item requires the applicable authority and reason, preserves history and shall not delete the Plan, version, item or downstream evidence. |
| PLN-FR-111 | Closing a plan shall preserve outstanding execution projections and audit access. |
| PLN-FR-112 | Selecting **Add Plan Item** on an Open Plan with a current Approved version shall automatically create or open the single Draft successor revision. |
| PLN-FR-113 | While a Draft revision is in progress, the current Approved version and all unchanged Active Plan Items, handoffs and Tenders shall remain operational. |
| PLN-FR-114 | Multiple additions and other changes may be batched into the same Draft revision; review shall focus on changed items and affected plan-level controls while retaining the complete consolidated snapshot for approval. |

### 10.11 Publication and Tender take-up

| ID | Requirement |
|---|---|
| PLN-FR-115 | The current Approved Plan Version shall expose structured publication/export data in the applicable annual-plan format and retain publication status and evidence. |
| PLN-FR-116 | Publication failure shall not rewrite approval status; it shall create a visible operational issue. |
| PLN-FR-117 | Tender Management shall create a Tender only from an Active, valid and not-fully-taken-up Plan Item present in the current Approved Plan Version. |
| PLN-FR-118 | **Create tender** shall revalidate plan version, funding/reservation, method, ownership and remaining take-up before proceeding. |
| PLN-FR-119 | Tender take-up shall atomically create an immutable Planning Handoff Snapshot and link the Tender to the Plan Item, Demand allocations and reservation identities. |
| PLN-FR-120 | The handoff shall include readable approved scope, category, method, amount, currency, schedule, funding, Strategy/value context, aggregation and indicative-lot decisions. |
| PLN-FR-121 | The handoff shall not require a user-managed Release Package or manual Consumed action. |
| PLN-FR-122 | One active procurement process shall exist per Plan Item unless an approved arrangement explicitly permits separate processes; retenders shall be related rather than duplicated silently. |
| PLN-FR-123 | Tender Management shall raise a governed correction request where the approved Planning baseline is materially unsuitable. |
| PLN-FR-124 | Superseding a Plan Version shall not invalidate an existing Planning Handoff Snapshot or downstream process for an unchanged carried-forward Plan Item. |

### 10.12 Monitoring, reporting, notifications and audit

| ID | Requirement |
|---|---|
| PLN-FR-130 | The approved-plan view shall derive Tender take-up, actual milestones and lifecycle status from downstream records. |
| PLN-FR-131 | The system shall support quarterly implementation reporting for the Approved Plan. |
| PLN-FR-132 | Reporting shall include planned value, approved funding, method mix, statutory allocation coverage, items not taken up, schedule variance, returns, revisions and execution status. |
| PLN-FR-133 | Management metrics shall show `As at`, scope, coverage, calculation basis and drill-down to the contributing Plan Items. |
| PLN-FR-134 | Aggregation benefits shall be reported as planned or evidenced; the system shall not infer realised savings from aggregation alone. |
| PLN-FR-135 | Responsible users shall receive in-app notifications for submissions, returns, approvals, validation blockers, publication failures, approaching milestones and overdue take-up. |
| PLN-FR-136 | All creation, allocation, method, aggregation, schedule, submission, decision, revision, publication and handoff actions shall be auditable. |
| PLN-FR-137 | Audit history shall preserve actor, role, time, source, before/after values, reason and related evidence where applicable. |

---

## 11. Role, visibility and permission contract

| Role | Visibility | Permitted actions | Prohibited actions |
|---|---|---|---|
| Organisation Unit Planning Contributor | Unit-owned eligible Demands and Plan Items | Add Demand, prepare unit-owned Plan Items, resolve returns | Approve plan, change funding or edit other units |
| Head of User Department | Unit contribution and its source records | Submit or recall unit contribution, respond to returns | Consolidate or approve the entity plan |
| Procurement Planner | Authorised plan and contributions | Create plan, consolidate, create/edit Plan Items, recommend method, validate, submit | Approve own plan where segregation is required; mutate upstream records |
| Planning Reviewer / Head of Procurement | Consolidated plan in scope | Review, return, recommend, reject where authorised | Change Demand or Budget baselines |
| Accounting Officer | Entity plan and evidence | Required certification, submission, approval or return | Bypass statutory approval or funding blockers |
| Designated Plan Approver | Submitted plans in assigned authority scope | Approve, return or reject | Edit Plan Items directly |
| Tender Initiator | Approved Plan Items in Tender scope | Create Tender, raise correction request | Edit Approved Plan baseline |
| Manager / Auditor | Authorised plans, evidence and reports | View, filter and export | Mutate workflow |
| System Administrator | Configuration according to data-access policy | Configure roles and reference data | Perform operational action without a separately assigned role and scope |

### 11.1 Scope rules

1. Every Plan and Plan Item shall carry `procuring_entity`; each Plan Item shall carry `owner_org_unit`.
2. User Scope Assignments shall govern visibility and action authority.
3. Role assignment without an applicable scope shall grant no operational access.
4. Cross-entity access shall require explicit assignment.
5. Consolidated entity reviewers may view assigned Organisation Units without transferring item ownership.
6. APIs, queues, totals, validation, reports, notifications and exports shall enforce the same scope.
7. System Administrator status shall not provide a default Procuring Entity or approval authority.

---

## 12. Readiness rules

### 12.1 Departmental submission readiness

A unit contribution may be submitted when each included Plan Item has:

- eligible Approved Demand allocation;
- owner Organisation Unit;
- requirement description and category;
- proposed method and basis;
- planned schedule;
- funding and reservation context;
- single- or multi-year treatment;
- aggregation/division decision;
- indicative-lot decision; and
- applicable statutory and Plan Value Commitment treatment.

### 12.2 Consolidated review readiness

The plan may enter review when:

- required unit contributions are submitted or explicitly recorded as having no requirements;
- no Demand is over-allocated;
- all Plan Item totals reconcile;
- required methods and schedules are complete;
- potential splitting issues are resolved;
- plan-level statutory allocations meet the applicable minimums or have a legally valid treatment;
- funding is valid and sufficiently current; and
- no blocking validation issue remains.

### 12.3 Approval readiness

Final approval requires:

- completed professional review;
- current validation result;
- applicable Accounting Officer action;
- required entity-level approval authority;
- reconciled plan totals and funding;
- complete statutory allocation treatment;
- no unresolved legal, funding or scope blocker; and
- an approval snapshot ready to lock.

### 12.4 Tender take-up readiness

A Plan Item may be taken up when:

- the logical Plan is Open and has a current Approved version;
- the Plan Item is Active, present in that current Approved version and not fully taken up;
- Demand allocations and reservations remain valid;
- method and broad STD family remain applicable;
- sufficient unconsumed amount/quantity remains;
- the user has Tender initiation authority; and
- no material correction is pending.

---

## 13. Clean domain model

### 13.1 Procurement Plan

- immutable internal identifier
- system-generated logical Plan reference
- Procuring Entity
- title and financial year
- read-only planning-period dates derived from the financial-year configuration
- controlled currency
- plan type: Annual
- coordinating procurement Organisation Unit
- governing regime and approval route
- lifecycle state: Open, Closed or Cancelled
- current Approved Plan Version
- optional single open Draft revision
- derived totals and coverage
- publication projection
- created, closed and cancelled metadata

### 13.2 Procurement Plan Version

- Plan identifier and version number
- version reason and source version
- workflow status: Draft, In review, Returned, Approved, Superseded or Cancelled
- immutable approved snapshot
- validation status
- approval decisions
- effective and superseded dates

### 13.3 Plan Item

- immutable internal identifier and system-generated reference
- logical Procurement Plan
- Procuring Entity and owner Organisation Unit
- optional delivery Organisation Unit
- baseline state: Proposed, Active or Removed
- current Approved Plan Item Version
- optional Draft Plan Item Version
- Tender take-up projection
- created, activated, removed and modified metadata

### 13.4 Plan Item Version

- Plan Item and containing Plan Version
- source Plan Item Version where carried forward
- changed or unchanged marker
- requirement title and readable description
- category, regime, method and method basis
- confirmed estimate and currency
- source-of-funds snapshot and reservation references
- single-/multi-year treatment and annual funding schedule
- planned milestones
- aggregation/division decision and reason
- indicative-lot decision
- statutory allocation treatment, target group and optional planned treatment value
- Strategy and Plan Value Commitment snapshots
- validation projection
- immutable approved snapshot metadata

### 13.5 Plan Demand Allocation

- Plan Item
- Demand and Demand Item immutable identifiers
- approved baseline version
- allocated quantity and/or amount
- reservation identity and amount
- proposed-in Plan Version
- effective-from Plan Version
- optional reversed-by Plan Version
- Draft, Effective or Reversed status
- effective/reversal reason and time

An unchanged Plan Item Version references the existing Effective allocations; it does not create new consumption. This record provides the Planning Consumption required by the Demand module. It is not a separate user-facing Inclusion record.

### 13.6 Departmental Submission

- Plan Version and Organisation Unit
- submitted item set/hash
- submitted by and time
- declaration
- status
- return reason and correction owner

### 13.7 Plan Decision

- Plan Version
- decision type and stage
- actor, role and authority scope
- timestamp
- decision/recommendation
- reason or comment
- validation and item snapshot references

### 13.8 Plan Validation Result

- Plan Version and optional Plan Item
- validation run and rule-set version
- result status
- issue code, business message, severity, owner and corrective action
- source record/version and timestamp
- acknowledgement where permitted

### 13.9 Planning Handoff Snapshot

- Plan and Approved version
- Plan Item
- Demand Allocations and reservation identities
- approved planning values and readable snapshots
- Tender identifier
- created by and time
- handoff version/hash

### 13.10 Publication Event

- Plan Approved version
- destination/channel
- submitted/published by and time
- status and external receipt/reference
- failure reason and retry history

Shared append-only audit and notification infrastructure shall be reused where it satisfies these requirements.

---

## 14. Service and integration contracts

### 14.1 Required Planning services

- `create_procurement_plan`
- `get_planning_workspace`
- `list_eligible_demands`
- `add_demand_to_plan`
- `update_plan_item`
- `aggregate_plan_allocations`
- `validate_plan`
- `submit_departmental_contribution`
- `submit_plan_for_review`
- `record_plan_decision`
- `approve_plan_version`
- `open_or_create_plan_revision`
- `cancel_plan_revision`
- `publish_approved_plan`
- `create_tender_from_plan_item`
- `get_plan_implementation`
- `get_plan_audit`

All state-changing services shall validate role, scope, current version and transition server-side and return a fresh projection.

### 14.2 Upstream integrations

| Owner | Planning use |
|---|---|
| Strategy | Read immutable Strategy/value snapshots inherited through Demand; no reassignment |
| Budget & Funding | Revalidate Budget Line, funding source, reservation and amount; no balance mutation |
| Demands | List eligible Demand Items, create effective Planning Consumption on approval and reverse through approved revision |
| Core scope | Resolve Procuring Entity, Organisation Unit, user scope and approval authority |

### 14.3 Downstream integrations

| Consumer | Planning output |
|---|---|
| Tender Management | Immutable Planning Handoff Snapshot and Approved Plan Item |
| Tender Configuration / STD | Category, method, broad STD family, scope, schedule, value and policy/value treatments |
| Publication / State Portal | Approved annual-plan structured data and publication evidence |
| Public Disclosure | Publishable planning data mapped to the later open-contracting lifecycle, subject to disclosure rules |
| Analytics | Approved plan, planned milestones, actual downstream status and lineage |

Planning shall not create duplicate Tender, reservation or public-disclosure records to simulate integration.

---

## 15. Non-functional requirements

| ID | Requirement |
|---|---|
| PLN-NFR-001 | Permissions and scope shall be enforced server-side on every read and mutation. |
| PLN-NFR-002 | Plan approval, version supersession and effective Demand Allocation creation shall be transactional and idempotent. |
| PLN-NFR-003 | Approved versions, decisions, handoffs and audit evidence shall remain immutable and retrievable. |
| PLN-NFR-004 | The UI shall meet WCAG 2.1 AA for keyboard operation, labels, focus, contrast and status communication. |
| PLN-NFR-005 | Ordinary workspace, builder and detail requests shall target two-second response at normal MVP volume, excluding file transfer and external portals. |
| PLN-NFR-006 | Validation errors shall identify the issue, owner and corrective action in business language. |
| PLN-NFR-007 | APIs shall use stable errors for permission, validation, conflict, stale version, funding and duplicate take-up failures. |
| PLN-NFR-008 | Dates shall use consistent storage and the user's configured display timezone; statutory/export dates shall be unambiguous. |
| PLN-NFR-009 | Seed and reset operations shall be deterministic, idempotent and isolated to fixture-owned records. |
| PLN-NFR-010 | Plan totals and reports shall derive from source records and shall not persist conflicting page-level aggregates. |
| PLN-NFR-011 | Rules for method, statutory allocations and validation shall be versioned and effective-dated. |
| PLN-NFR-012 | Publication/export shall protect classified, restricted and personal data according to applicable disclosure policy. |

---

## 16. Minimum screen families

MVP 1 requires five screen families:

1. **Procurement Planning workspace** — current plan context, eligible Approved Demands, Returned work and items requiring action.
2. **Plan builder** — short plan header, unit filters and one compact Plan Item table with Add approved demand.
3. **Plan Item editor** — focused planning decisions, schedule and inherited read-only source context.
4. **Plan review and approval** — consolidated totals, statutory allocation coverage, issues, changed items and the current decision.
5. **Approved plan and implementation** — immutable current baseline, visible Draft-revision indicator, Add Plan Item, publication evidence, Tender take-up and quarterly performance.

Departmental submission, Demand selection, aggregation and issue resolution shall use focused drawers, dialogs or inline states within these families. They shall not become standalone workbenches.

The UI shall not include:

- Planning Inclusion Detail;
- separate Procurement Package Workbench;
- ten-tab Package Detail;
- manually managed Release Package;
- raw readiness-rule tables by default;
- technical IDs or hashes;
- separate dashboards for every role; or
- decorative KPI cards without a decision or drill-down.

---

## 17. Canonical seed-data contract

The KenTender MVP Canonical Demo Data Contract version 2.4 shall provide the Planning baseline and the repeatable post-approval addition scenario below.

### 17.1 Principal Ministry story

The Planning fixture shall continue the existing Demand story:

- Procuring Entity: `PE-MOH`
- Financial year: FY 2027/28
- Approved Demand: `DMD-MOH-2027-014`
- Title: National digital health infrastructure upgrade
- Owner Organisation Unit: `MOH-DIR-DHP`
- Confirmed estimate and planned amount: KES 455,000,000
- Demand Items: both existing approved Need Items
- Budget Line: `MOH-BL-DHI-2027`
- Reservation: `RSV-MOH-0001`
- Logical Plan: `PLN-MOH-2027-001`, Open
- Current Plan Version: Version 1, Approved
- Plan Item: `PPI-MOH-2027-021`
- Plan Item baseline state: Active
- Category: ICT infrastructure and services
- Method: Open tender, confirmed from applicable rules
- Broad STD family: Information Technology
- Arrangement: Single-year procurement with delivery schedule
- Tender continuation: `TND-MOH-2027-008`

The two Demand Items may be represented by two Plan Demand Allocations under one Plan Item. Their total shall remain KES 455,000,000.

### 17.2 Post-approval addition scenario

The deterministic scenario `SCN-PLN-ADD-001` shall demonstrate the common addition of a Plan Item after approval:

1. `DMD-MOH-2027-019` starts Returned with a KES 15,000,000 shortfall.
2. The responsible Organisation Unit reduces the scope from KES 95,000,000 to KES 80,000,000, completes the existing Demand approval route and creates `RSV-MOH-0002` for KES 80,000,000.
3. On `PLN-MOH-2027-001` Version 1, the planner selects **Add Plan Item**.
4. The system creates Draft Version 2 and Proposed Plan Item `PPI-MOH-2027-022` for the Digital health technical staff certification programme.
5. Approved Version 1 and `PPI-MOH-2027-021` remain operational while Draft Version 2 is prepared.
6. The relevant Head of User Department signs off the added item; affected plan totals, funding and statutory allocations are revalidated.
7. Approval makes Version 2 current Approved, makes Version 1 Superseded and activates `PPI-MOH-2027-022`.
8. The unchanged `PPI-MOH-2027-021` retains its existing handoff and Tender linkage.

Draft Version 2 has a consolidated value of KES 535,000,000. Its applicable 30% plan-allocation basis is KES 160,500,000. The fixture shall record planned treatment only and shall not imply that the allocation has been awarded or realised.

### 17.3 Ineligible and secondary stories

- At the base seed boundary, `DMD-MOH-2027-019` remains Returned and shall not appear as eligible for Planning. It becomes eligible only inside `SCN-PLN-ADD-001` after its controlled correction and approval.
- `DMD-CGK-2027-006` remains Draft and shall not appear as eligible for Planning.
- A minimal County FY 2027/28 Draft Plan may exist with no Plan Items to prove entity isolation and the absence of silently imported Ministry data.

### 17.4 Planning actors

Version 2.3 shall add the smallest realistic users and explicit scopes needed for:

- Ministry Organisation Unit contribution;
- Procurement Planner;
- Head of User Department submission;
- Planning review/professional recommendation;
- Accounting Officer action;
- applicable Designated Plan Approval;
- Tender initiation;
- Ministry and County read-only oversight; and
- Administrator-without-operational-authority denial.

### 17.5 Repeatability and verification

The seed shall prove:

- only the Approved Ministry Demand is eligible;
- Draft allocations do not change Demand planning usage;
- Plan approval creates effective allocations once;
- the Plan Item and allocations total KES 455,000,000;
- the same reservation identity is preserved;
- the Approved version is immutable;
- selecting Add Plan Item on the Approved Plan creates or reuses one Draft successor without changing the current Approved version;
- the new item remains Proposed and unavailable for Tender take-up until Draft Version 2 is approved;
- approval of Version 2 supersedes Version 1, activates the added item and retains the unchanged item's handoff and Tender linkage;
- Tender take-up creates one handoff and links the existing Tender once;
- rerun creates no duplicate plan, version, item, allocation, decision, handoff or audit event;
- County users cannot access Ministry Planning records and vice versa; and
- reset removes only fixture-owned Planning records.

Stable fixture references are deterministic test identities, not user-maintained production codes.

---

## 18. Acceptance criteria

### 18.1 Core journey

| ID | Acceptance criterion |
|---|---|
| PLN-AC-001 | An authorised user can register the annual plan using a short direct form without entering technical codes. |
| PLN-AC-002 | Only Approved, Planning Ready and not-fully-planned Demand Items appear in the planning queue. |
| PLN-AC-003 | Adding a Demand creates a Plan Item and Draft allocation without mutating the Demand or reservation. |
| PLN-AC-004 | A planner can complete method, schedule, aggregation, indicative lotting and statutory treatment in one focused Plan Item editor. |
| PLN-AC-005 | A Head of User Department can submit the unit's contribution without creating a separate departmental plan workspace. |
| PLN-AC-006 | Procurement can consolidate unit contributions and resolve aggregation candidates. |
| PLN-AC-007 | The applicable review, Accounting Officer and Designated Approver decisions are recorded according to the configured entity route. |
| PLN-AC-008 | Approval atomically locks the version and makes Draft Demand Allocations effective once. |
| PLN-AC-009 | Tender Management can create a Tender from an Approved Plan Item through one immutable handoff snapshot. |
| PLN-AC-010 | Approved-plan implementation derives Tender and actual milestone status without editing the baseline. |

### 18.2 Legal and control requirements

| ID | Acceptance criterion |
|---|---|
| PLN-AC-011 | Plan Items cannot exceed approved, funded and unplanned Demand scope. |
| PLN-AC-012 | Open tender is recommended by default under PPADA; an alternative method requires valid configured grounds and evidence. |
| PLN-AC-013 | Potential contract splitting is blocked or escalated and cannot be bypassed through client payloads. |
| PLN-AC-014 | Aggregated Demand allocations retain exact Demand, Budget and reservation lineage. |
| PLN-AC-015 | The consolidated plan cannot be approved while applicable statutory allocation minimums are unmet or unresolved. |
| PLN-AC-016 | Multi-year treatment contains justification and annual funding schedule. |
| PLN-AC-017 | Actual schedule dates are derived from downstream records and do not overwrite planned dates. |
| PLN-AC-018 | A user cannot read or mutate Planning records outside assigned Procuring Entity/Organisation Unit scope through UI or API. |
| PLN-AC-019 | An Administrator without a Planning operational role and scope cannot prepare, review or approve a plan. |
| PLN-AC-020 | A material change to an Approved Plan requires a revision and new approval. |
| PLN-AC-021 | A taken-up Plan Item cannot be materially changed without a linked downstream correction process. |
| PLN-AC-022 | Publication failure remains visible without corrupting Approved status. |

### 18.3 Data, performance and repeatability

| ID | Acceptance criterion |
|---|---|
| PLN-AC-023 | Plan totals, statutory coverage and management metrics reconcile to the underlying Plan Items. |
| PLN-AC-024 | Quarterly implementation reporting shows As at, scope, planned/actual basis and drill-down. |
| PLN-AC-025 | Planned aggregation benefits and public-value treatments are not presented as realised results without evidence. |
| PLN-AC-026 | The canonical Ministry and County Planning fixtures can be rebuilt repeatedly without duplicates. |
| PLN-AC-027 | The principal Plan Item retains the existing Demand, Strategy, Budget, reservation and Tender identities. |
| PLN-AC-028 | One approved current Plan version exists per Procuring Entity/financial year, and all superseded versions remain readable. |
| PLN-AC-029 | Applicable transfer treatment and incidental-cost coverage are complete before plan approval, without Planning mutating the approved Demand or Budget baseline. |
| PLN-AC-030 | Selecting Add Plan Item on an Approved Plan creates or reuses one Draft successor while the current Approved version remains operational. |
| PLN-AC-031 | A newly added Plan Item remains Proposed and unavailable for Tender take-up until the revised consolidated Plan is approved. |
| PLN-AC-032 | Review of a Draft revision focuses on changed items and affected plan-level controls without requiring users to rework unchanged items. |
| PLN-AC-033 | Approving a revision atomically supersedes the former Approved version, activates added items and preserves handoffs and downstream processes for unchanged items. |
| PLN-AC-034 | Carrying an unchanged Plan Item into a successor version reuses its Effective Demand Allocations and does not double-count Planning Consumption. |

---

## 19. Explicit non-requirements and legacy removals

Implementation shall not preserve or recreate these concepts merely because they exist in the previous MVP:

- user-facing Planning Inclusion records;
- separate Procurement Package and Package Line workflows where Plan Item and Demand Allocations suffice;
- Planning Release Package as a user-managed object;
- manual Released or Consumed actions;
- nine-state package lifecycle;
- separate plan, package, inclusion and release workbenches;
- ten-tab Package Detail;
- mandatory template/rule-profile administration;
- risk, KPI and decision-profile builders inside Planning;
- manual entry of actual tender milestones;
- requester or planner mutation of funding reservations;
- re-selection of Strategy in Planning;
- automatic merging of Demand Items;
- detailed Tender lots or STD configuration;
- page-local canonical fixtures;
- Ministry-specific ownership fields;
- Administrator-as-operational-approver behaviour;
- user-maintained Plan, Item, Demand, Budget or Strategy codes;
- duplicate workflow, audit, notification or handoff services; or
- legacy dual reads, dual writes and fallback queries.

The previous District Hospital Renovation Works seed shall not override or compete with the current canonical Ministry digital-health story.

---

## 20. Delivery gates

Implementation shall follow this sequence. Status as of 9 August 2026:

| Step | Gate | Status |
|---|---|---|
| 1 | Approve and lock this requirements document (`PLANNING-MVP1-REQ-1.4`) | **Done** |
| 2 | Use the approved Canonical Demo Data Contract version 2.4 | **Done** |
| 3 | Produce and approve Stitch designs for the five screen families and focused states (`PLN-UI-01`–`PLN-UI-10`) | **Done** |
| 4 | Produce the Cursor implementation pack (`PLANNING-MVP1-CURSOR-1.2`) | **Done** |
| 5 | Perform a read-only legacy/dependency audit and approve the exact replacement boundary (Cursor Gate 00) | **Done** — see `GATE_00_REPLACEMENT_BOUNDARY.md` |
| 6 | Implement the clean domain and service contracts before UI state mutations (Gates 01–02) | **Next** |
| 7 | Implement workspace, builder, item editor, validation, approval, revision and integration UI (Gates 03–07) | Not started |
| 8 | Run legal-rule, role, scope, versioning, aggregation, funding, handoff, repeatability and browser acceptance tests | Not started |
| 9 | Audit implementation against every `PLN-FR`, `PLN-NFR` and `PLN-AC` requirement (Gate 08) | Not started |

Day-to-day delivery status is tracked in `04_Procurement_Planning_MVP1_Implementation_Tracker.md`.

---

## 21. Approval decision

Approval locks this MVP 1 pattern:

> Organisation Units contribute approved needs; Procurement converts them into stable Plan Items within one logical annual Plan; the Plan Item is the operational unit and the Plan Version is the approval unit; authorised officials approve immutable versions; additions use one Draft successor while the current Approved version remains operational; Tender Management takes up Active Plan Items through a generated handoff; and actual execution is derived for quarterly monitoring without multiplying workbenches or re-entering lifecycle data.
