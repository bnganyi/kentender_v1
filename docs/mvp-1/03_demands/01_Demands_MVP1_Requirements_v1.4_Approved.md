# Demands — MVP 1 Requirements

**Document ID:** DEMAND-MVP1-REQ-1.4  
**Status:** Approved MVP 1 functional baseline  
**Date:** 9 August 2026  
**Change control:** Approval locks the MVP 1 functional baseline; subsequent functional changes require a new version  
**Module:** Demands  
**Application:** KenTender  
**Primary fixture:** Ministry of Health  
**Secondary fixture:** County Government of Kisumu

**Revision 1.4:** Retains the 1.3 Planning-allocation semantics and adopts Canonical Demo Data Contract 2.4, including the reconciled principal-Demand required-by date.

**Approval note:** This newly issued version 1.4 file is authoritative. It replaces every `DEMAND-MVP1-REQ-1.0`, unversioned or earlier cached Demands requirements file.

## Source baseline

- Previous Demand Intake and Approval PRD (`2. prd(1).md`)
- Strategy Alignment requirements `STRATEGY-MVP1-REQ-1.1`
- Budget & Funding requirements `BUDGET-MVP1-REQ-1.1`
- KenTender Procuring Entity and Organisation Scope Model
- KenTender MVP Canonical Demo Data Contract, version 2.4
- KenTender Statutory and Public-Value Obligations Matrix, version 1.1
- [Public Procurement and Asset Disposal Act, 2015](https://new.kenyalaw.org/akn/ke/act/2015/33/eng%402022-12-31)
- [Public Procurement and Asset Disposal Regulations, 2020](https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng%402022-12-31)
- [OECD Recommendation of the Council on Public Procurement](https://legalinstruments.oecd.org/en/instruments/OECD-LEGAL-0411)
- [Oracle: How Funds Are Reserved for Requisitions](https://docs.oracle.com/en/cloud/saas/procurement/25c/oaprc/how-funds-are-reserved-for-requisitions.html)

## 1. Purpose

The Demands module captures a business need, progressively enriches it with procurement, Strategy and funding information, obtains the required internal approvals, reserves funding and makes the approved need available to Procurement Planning.

The module shall replace informal emails, spreadsheets and prematurely detailed requisitions with a guided, traceable process in which each role supplies only the information it reasonably owns.

The module shall answer:

1. What public or operational need exists, for whom, where and by when?
2. Is the need legitimate, necessary and supported by the responsible organisational unit?
3. How does it support the entity's Strategy and public-value commitments?
4. What is the credible approved estimate and where will the funding come from?
5. Is the need sufficiently defined, approved and funded for Procurement Planning?
6. What happened to the approved demand downstream?

## 2. Legal and lifecycle boundary

### 2.1 Pre-planning demand

For MVP 1, a **Demand** is an internal, pre-planning proposal for a need. It supports needs assessment, prioritisation, funding confirmation and preparation of the procurement plan.

A Demand does **not**:

- start a tender or procurement proceeding;
- select the final procurement method;
- replace the approved annual procurement plan;
- replace the later purchase requisition initiated against an approved procurement plan where required by law or entity procedure;
- authorise solicitation, award, contracting or expenditure; or
- prove that a Strategy outcome or public-value result has been achieved.

The statutory or operational purchase requisition that initiates procurement against an approved plan is a separate downstream record and shall reference the approved Demand and Plan Item.

### 2.2 Public-entity neutrality

The module shall work for ministries, State departments, counties, constitutional commissions, the Judiciary, public universities, State corporations and other public entities without hard-coded government hierarchies.

Ownership shall use:

- `procuring_entity` — the legally accountable public entity;
- `owner_org_unit` — the organisational unit that owns the need; and
- optional `delivery_org_unit` — a different unit responsible for delivery or technical support.

Terms such as Ministry, State Department, Directorate, County Department and Agency are fixture labels or configurable organisation-unit types, not schema fields.

## 3. MVP outcomes

MVP 1 shall enable a procuring entity to:

1. Capture a business need without requiring the requester to know Strategy codes, Budget Lines, procurement methods or planning data.
2. Route the need to an accountable Business Approver.
3. Allow Procurement to enrich, classify and challenge the demand before approval.
4. Derive and confirm Strategy alignment and applicable Plan Value Commitments.
5. Match the Demand to one or more active Budget Lines and obtain Budget Officer confirmation of the assignment and funding position.
6. Perform a final funds check and reserve funding atomically when the Demand is approved.
7. Lock an immutable approved baseline and make it automatically ready for Planning.
8. Track partial or full consumption of the Demand by Procurement Planning.
9. Expose cycle time, funding exceptions, duplicates, aggregation opportunities and value coverage to managers.
10. Preserve entity scope, role separation, decisions, reasons and complete audit history.

## 4. Design principles

1. **The requester describes the need.** The requester is not expected to be a procurement, Strategy, planning or budget specialist.
2. **Progressive enrichment replaces a large requisition form.** Business, procurement and funding information is added by the role that owns it.
3. **Automation recommends; an accountable officer confirms.** The system may propose a Budget Line automatically, but a Budget Officer shall review and sign off every Demand's funding assignment.
4. **One final procurement authority approves the Demand.** Business support and Budget Officer confirmation are mandatory controls; they do not replace the final procurement approval.
5. **Approval and reservation are atomic.** An approved Demand cannot exist without confirmed funding and successful reservation.
6. **Reservation is not commitment.** Contractual commitment occurs downstream at contract or purchase-order control, not at Demand approval.
7. **Approved means Planning Ready.** No manual “Mark ready for planning” action shall exist.
8. **Demand state and planning usage are separate.** Approval status shall not be overwritten when Planning consumes the Demand.
9. **Emergency does not bypass control.** It accelerates routing and requires justification; the downstream legal procurement method remains a Planning/Tender decision.
10. **Strategy alignment and public-value treatment are distinct.** Alignment states what outcome the Demand supports; value treatment states what obligations or goals must be carried forward.
11. **Codes are system managed.** Users work with meaningful names and context; references are generated and stored internally.
12. **No legacy dual-write.** Obsolete MVP structures may be removed because current data is disposable.
13. **Evidence is not inference.** The system shall not claim savings, benefits or outcomes without an identified basis and source.
14. **Every hand-off is traceable.** Demand, funding, Planning and later requisition records shall retain stable references.
15. **Ownership is chosen explicitly when it is ambiguous.** A current workspace filter, the first scope assignment or the Administrator role shall never silently determine the Procuring Entity or owning Organisation Unit of a new Demand.

## 5. Scope

### 5.1 Included

- Role-scoped Demands workspace and work queues
- Guided creation and editing of a business need
- Demand header and one or more need items
- Optional early cost estimate and evidence
- Business review
- Procurement enrichment and final approval
- Standard, Additional and Emergency demand routes
- Strategy target suggestion, confirmation and versioned reference
- Plan Value Commitment applicability and proposed downstream treatment
- Automated Budget Line matching and funds checking
- Mandatory Budget Officer funding confirmation, including resolution of split, ambiguous or insufficient funding
- Atomic reservation at final approval
- Potential duplicate and aggregation-candidate flags
- Returns, rework, rejection and cancellation
- Immutable approved baseline
- Automatic Planning Ready hand-off
- Partial and full Planning consumption tracking
- Notifications, audit, role permissions and entity scope
- Operational and management reporting
- Repeatable Ministry of Health and County Government of Kisumu fixtures
- Clean replacement of obsolete Demand structures

### 5.2 Excluded

- Full procurement-plan preparation and approval
- Final procurement-method selection
- Tender configuration, publication, evaluation, award or contract management
- The later statutory/operational purchase requisition against an approved Plan Item
- Budget formulation, approval, revision or accounting
- Creation of contract commitments or expenditure
- Inventory issue requests, stores replenishment or asset-disposal requests
- Complex project appraisal, feasibility studies or business-case authoring
- AI-generated approvals, opaque demand scoring or autonomous rejection
- Supplier selection, quotations or market engagement
- Arbitrary workflow builders or entity-specific hard coding
- Full approved-Demand amendment workflow; MVP 1 uses controlled cancellation/replacement

## 6. Actors and operating model

| Actor | Owns | Does not own |
|---|---|---|
| Requester | Need, problem, expected outcome, beneficiaries, location, timing, basic items and available evidence | Budget Line, Strategy code, procurement method, final category, approved estimate |
| Business Approver | Business legitimacy, priority, necessity, unit accountability and support | Funding reservation, procurement method or final Demand approval |
| Procurement Approval Authority | Procurement enrichment, demand classification, category, estimate challenge, duplicate/aggregation review, Strategy/value confirmation and final approval | Budget administration, financial-system approval or tender method selection |
| Budget Officer | Confirming every funding assignment and resolving split, ambiguous or insufficient funding | Approving the business need or final Demand |
| Planning Officer | Consuming approved Demand items into the procurement plan | Editing the approved Demand baseline |
| Manager / Auditor | Oversight, reporting and evidence review | Editing or transitioning operational records unless separately assigned another role |
| System Administrator | Configuration, role assignment and technical support | Business, procurement or funding approval by virtue of administration alone |

### 6.1 Standard operating pattern

The MVP pattern is **guided intake → business support → procurement enrichment → Budget Officer confirmation → final approval and reservation → Planning**.

Budget matching may be automated, but Budget Officer confirmation is mandatory for every Demand. Straightforward matches receive a quick confirmation; ambiguous, split or insufficient funding requires exception resolution within the same stage.

## 7. Lifecycle

### 7.1 Status and stage model

Workflow status and current stage shall be separate fields.

| Workflow status | Meaning |
|---|---|
| Draft | Requester is preparing the Demand |
| In Review | One of the controlled review stages owns the next action |
| Returned | The named owner must correct specified issues |
| Approved | Final approval and funding reservation succeeded; baseline is locked |
| Rejected | Final or stage decision ended the Demand |
| Cancelled | Demand was withdrawn or formally cancelled |

| Current stage | Meaning |
|---|---|
| Request Preparation | Requester owns the Draft or Returned work |
| Business Review | Business Approver validates and supports the need |
| Procurement Enrichment | Procurement Approval Authority enriches and challenges it |
| Budget Confirmation | Budget Officer is confirming the proposed allocation or resolving a funding exception |
| Final Approval | Funding is valid and Procurement Approval Authority owns the final decision |
| Complete | Approved, Rejected or Cancelled |

### 7.2 Planning usage

Planning usage is derived independently of workflow status:

- Not taken up
- Partially planned
- Fully planned

An Approved Demand remains Approved after partial or full Planning consumption.

Only **Effective** allocations in the current Approved Procurement Plan Version count toward Planning usage. A Proposed Plan Item or Draft Plan Item Version may show intended allocation inside Planning, but it shall not change the Demand's Not taken up, Partially planned or Fully planned projection.

### 7.3 Standard transitions

| From | Action | To | Result |
|---|---|---|---|
| Draft | Submit | In Review / Business Review | Completeness validated and Business Approver assigned |
| Business Review | Support | In Review / Procurement Enrichment | Business decision and reason recorded |
| Business Review | Return | Returned / Request Preparation | Specific correction requests recorded |
| Business Review | Reject | Rejected / Complete | Terminal reason recorded |
| Procurement Enrichment | Send for budget confirmation | In Review / Budget Confirmation | Enrichment baseline validated and proposed allocations generated where possible |
| Procurement Enrichment | Return | Returned / named prior owner | Specific correction requests recorded |
| Budget Confirmation | Confirm funding | In Review / Final Approval | Budget Officer sign-off and valid allocation set recorded; no reservation yet |
| Budget Confirmation | Return | Returned / Procurement Enrichment | Funding issue and required action recorded |
| Final Approval | Approve | Approved / Complete | Funds rechecked and reserved atomically; baseline locked; Planning Ready derived |
| Final Approval | Return | Returned / named prior owner | Reason and invalidated approvals recorded |
| Final Approval | Reject | Rejected / Complete | Terminal reason recorded; no reservation |
| Draft or Returned | Cancel | Cancelled / Complete | Open work ended |

### 7.4 Return and rework rules

1. Every return shall identify the target owner, reason and fields or evidence requiring correction.
2. Correction shall return to the stage that requested it, not restart the whole workflow by default.
3. A material change to business need, owner, amount, route or required date shall invalidate affected later-stage decisions.
4. The UI shall disclose which decisions will be invalidated before resubmission.
5. Rejection is terminal; a new Demand is required for a materially new request.

## 8. Functional requirements

### 8.1 Workspace and intake

| ID | Requirement |
|---|---|
| DIA-FR-001 | The module shall be labelled **Demands** in navigation, page titles and user-facing references. “Demand Intake and Approval” may describe the process but shall not be the module name. |
| DIA-FR-002 | The workspace shall default its list, counts and queues to the user's permitted viewing scope. Workspace context is a filter only and shall not silently become the ownership of a new Demand. |
| DIA-FR-003 | The workspace shall provide My Drafts, Returned to Me, My Approvals, Budget Confirmations and All Permitted Demands views as applicable to the user's roles. Budget Confirmations shall distinguish routine confirmations from exceptions. |
| DIA-FR-004 | Users shall not see inaccessible entity or organisation-unit records in counts, filters, search results or exports. |
| DIA-FR-005 | A Demand shall receive a system-generated, stable, human-readable reference on first save. Users shall not enter or maintain it. |
| DIA-FR-006 | The system shall derive eligible Demand-creation scopes from the authenticated user's active User Scope Assignments that explicitly grant the **Demand Requester** capability. Generic visibility, another operational role or System Administrator status shall not create this authority. |
| DIA-FR-007 | If exactly one eligible `procuring_entity` and `owner_org_unit` pair exists, the form shall visibly preselect it and show it as read-only ownership context. |
| DIA-FR-007A | If more than one eligible pair exists, the user shall explicitly select the Procuring Entity and owning Organisation Unit before first save. No pair shall be selected from list order, a previous workspace filter or an Administrator fallback. |
| DIA-FR-007B | Procuring Entity selection shall constrain the owning-unit choices to authorised pairs for that entity. Changing the Procuring Entity shall clear any selected owning unit. |
| DIA-FR-007C | If no eligible Demand-creation scope exists, Create demand shall be unavailable or lead to a clear blocked state explaining that a Demand Requester scope assignment is required. |
| DIA-FR-007D | The server shall validate the exact submitted `procuring_entity` and `owner_org_unit` pair on creation and first save. Hidden fields, client filtering and trusted request payloads are insufficient. |
| DIA-FR-007E | The creator/requester identity shall be recorded separately from the Demand's owning Procuring Entity and Organisation Unit. Explicit cross-entity creation is permitted only where the user has the corresponding Demand Requester scope assignment. |
| DIA-FR-007F | Demand ownership shall become read-only after first save in MVP 1. Correcting ownership requires cancellation of the Draft and creation of a new Demand in the correct authorised scope. |
| DIA-FR-008 | The initial form shall ask for business information only and shall not require Strategy, Budget, Planning or procurement-method codes. |
| DIA-FR-009 | A Requester may save an incomplete Draft. Submission shall apply the minimum completeness rules in section 10. |
| DIA-FR-010 | Drafts shall autosave or clearly disclose unsaved changes without creating duplicate records. |

### 8.2 Business need and Demand items

| ID | Requirement |
|---|---|
| DIA-FR-015 | A Demand shall record a concise title, need statement, expected outcome, beneficiaries, required-by date, delivery location and urgency. |
| DIA-FR-016 | A Demand shall contain at least one Need Item before submission. |
| DIA-FR-017 | A Need Item shall require a plain-language description; quantity, unit of measure and Requester estimate may be unknown at submission. |
| DIA-FR-018 | The Requester may provide an overall estimate or line estimates, their source and confidence level; these values are advisory until Procurement confirms them. |
| DIA-FR-019 | Attachments shall be optional unless a configured category or route requires named evidence. |
| DIA-FR-020 | The system shall not force the Requester to upload a manual form where the same information is captured structurally. |
| DIA-FR-021 | One Demand may contain related items that serve one coherent business need. Unrelated needs shall use separate Demands. |
| DIA-FR-022 | The Requester may identify a technical contact or `delivery_org_unit` where specialist input is needed. |

### 8.3 Demand route and urgency

| ID | Requirement |
|---|---|
| DIA-FR-025 | Demand route shall be Standard, Additional or Emergency. |
| DIA-FR-026 | Standard shall represent an anticipated need following the ordinary cycle. |
| DIA-FR-027 | Additional shall represent a valid new or changed need requiring downstream plan inclusion or amendment; a reason and impact shall be required. |
| DIA-FR-028 | Emergency shall require the event, urgency, public or operational impact and latest acceptable delivery date. |
| DIA-FR-029 | Emergency shall accelerate notifications and queue priority but shall not bypass business, funding, approval, audit or downstream legal controls. |
| DIA-FR-030 | Demand route shall not determine the final procurement method. |
| DIA-FR-031 | Procurement Approval Authority may change the route with a recorded reason before final approval. |

### 8.4 Business review

| ID | Requirement |
|---|---|
| DIA-FR-035 | Submission shall route the Demand to the configured Business Approver for the owning organisational unit. |
| DIA-FR-036 | The Business Approver shall review necessity, priority, scope, timing, expected outcome and organisational ownership. |
| DIA-FR-037 | The Business Approver may Support, Return or Reject the Demand. |
| DIA-FR-038 | Support shall record actor, time and an optional comment; Return and Reject shall require a reason. |
| DIA-FR-039 | Business support shall not represent final procurement approval or funding confirmation. |
| DIA-FR-040 | A Requester shall not act as Business Approver on the same Demand unless a documented small-entity exception policy authorises it. |

### 8.5 Procurement enrichment

| ID | Requirement |
|---|---|
| DIA-FR-045 | Procurement Approval Authority shall confirm or assign the procurement category using a controlled classification. |
| DIA-FR-046 | Procurement shall refine Need Items, quantities, units, estimate and estimate basis where necessary without changing the underlying business need silently. |
| DIA-FR-047 | A positive confirmed approved estimate and currency shall be required before Budget Confirmation. |
| DIA-FR-048 | Material differences from the Requester estimate shall show the before value, after value and reason. |
| DIA-FR-049 | Procurement shall assess likely duplication and aggregation opportunity before sending the Demand for funding. |
| DIA-FR-050 | Procurement may mark a Demand as a potential duplicate, link related Demands, retain it with a reason, return it or reject it. |
| DIA-FR-051 | Procurement may place related Demands in an aggregation-candidate group; actual packaging and aggregation decisions remain in Planning. |
| DIA-FR-052 | Procurement shall not select the final procurement method, tender type or solicitation timetable in this module. |
| DIA-FR-053 | Procurement enrichment shall preserve which values came from the Requester and which were confirmed or changed by Procurement. |

### 8.6 Strategy alignment and public value

| ID | Requirement |
|---|---|
| DIA-FR-060 | The Requester shall not be required to select a Strategic Plan, Outcome, Target or code. |
| DIA-FR-061 | Strategy shall suggest effective eligible targets using procuring entity, organisational scope, demand category and available Budget Line alignment. |
| DIA-FR-062 | Only Strategy references applicable through the entity's Strategy Scope Assignments may be selected. |
| DIA-FR-063 | Procurement Approval Authority shall confirm one primary Performance Target or record a controlled reason why no direct alignment applies. |
| DIA-FR-064 | Supporting targets may be recorded only with a reason. |
| DIA-FR-065 | A Strategy reference shall retain internal identifiers, plan/version, complete path and immutable human-readable snapshot. |
| DIA-FR-066 | Strategy shall return applicable Plan Value Commitments for the confirmed target, category and context. |
| DIA-FR-067 | Procurement shall confirm applicability and proposed downstream treatment for every Required commitment before final approval. |
| DIA-FR-068 | A commitment treatment shall be Embedded in specification, Evaluation requirement, Contract obligation, Delivery or disposal obligation, Reporting only, Not applicable, or To be determined in Planning. |
| DIA-FR-069 | Not applicable and To be determined in Planning shall require a reason; Required commitments may use To be determined only where the governance rule permits deferral. |
| DIA-FR-070 | Demand approval shall carry confirmed Strategy and value context to Planning but shall not generate tender criteria or contract clauses. |

### 8.7 Budget confirmation

| ID | Requirement |
|---|---|
| DIA-FR-075 | A Demand may be submitted and business-supported without a Budget Line. |
| DIA-FR-076 | Budget matching shall use entity, fiscal period, owner organisational unit, confirmed category, currency, approved estimate and Strategy context. |
| DIA-FR-077 | The system may propose one or more valid Budget Line allocations, but an automated proposal shall remain unconfirmed until a Budget Officer signs it off. |
| DIA-FR-078 | Every Procurement-enriched Demand shall be assigned to a Budget Officer for confirmation. No match, multiple plausible matches, insufficient funding or a need for split funding shall additionally be marked as a Funding Exception. |
| DIA-FR-079 | The Budget Officer shall review the proposed allocation, current availability, amount, currency, fiscal period, Strategy context and source freshness, then Confirm, Adjust or Return it. |
| DIA-FR-080 | One Demand may use multiple Budget Lines; each allocation shall identify its amount and currency. |
| DIA-FR-081 | Budget Officer-confirmed allocations shall total the confirmed approved estimate before final approval. |
| DIA-FR-082 | A zero-value, placeholder, inactive, expired, cross-entity or unauthorised Budget Line shall not satisfy funding confirmation. |
| DIA-FR-083 | Budget Confirmation shall record the automated recommendation where used, availability checked, confirmed allocation, result, source freshness, Budget Officer, time and any adjustment reason. |
| DIA-FR-084 | Budget Officer confirmation shall not reserve funds and shall not approve the business need or the final Demand. |
| DIA-FR-085 | Insufficient funding shall not be silently overridden in MVP 1. The exception shall remain open until funding is valid or the Demand is returned, rejected or cancelled. |
| DIA-FR-086 | Budget Officer sign-off shall be mandatory even where the system recommends a single sufficient Budget Line without an exception. |
| DIA-FR-087 | A material change to amount, currency, category, owning unit, Strategy reference or proposed allocation after sign-off shall invalidate Budget Confirmation and return the Demand to that stage. |

### 8.8 Final approval and reservation

| ID | Requirement |
|---|---|
| DIA-FR-090 | Procurement Approval Authority shall be the final human approval role. |
| DIA-FR-091 | Final approval shall require a valid Budget Officer sign-off and shall revalidate workflow authority, entity scope, approved estimate, Strategy/value completeness, Active Budget Lines and current availability. |
| DIA-FR-092 | Final approval and creation of all required funding reservations shall occur in one transaction. |
| DIA-FR-093 | If any reservation or funding revalidation fails, the Demand shall remain unapproved, no partial reservation shall remain, the Budget Officer sign-off shall be invalidated and the Demand shall return to Budget Confirmation. |
| DIA-FR-094 | Repeated approval requests shall be idempotent and shall not create duplicate reservations. |
| DIA-FR-095 | A successful approval shall lock the approved baseline, set workflow status to Approved and derive Planning Ready automatically. |
| DIA-FR-096 | The approved snapshot shall include business need, items, estimates, route, Strategy/value context, funding allocations, approvals and reservation references. |
| DIA-FR-097 | An Approved Demand shall not be directly edited. |
| DIA-FR-098 | Approval shall not create a contract commitment, expenditure or procurement method. |
| DIA-FR-099 | The final approver shall not approve a Demand they created unless an authorised small-entity exception is configured and disclosed in the audit record. |

### 8.9 Cancellation and replacement

| ID | Requirement |
|---|---|
| DIA-FR-105 | A Draft or Returned Demand may be cancelled by its owner with a reason. |
| DIA-FR-106 | Approved Demand cancellation shall require an authorised Procurement Approval Authority and a reason. |
| DIA-FR-107 | Approved cancellation shall atomically release the unconsumed reservation balance through Budget & Funding. |
| DIA-FR-108 | A Demand with Planning consumption shall not be cancelled beyond its unconsumed scope. |
| DIA-FR-109 | Material change to an Approved Demand shall use cancellation and a linked replacement Demand in MVP 1. |
| DIA-FR-110 | The replacement shall preserve traceability to the original but shall undergo current validation and approval. |

### 8.10 Planning hand-off and consumption

| ID | Requirement |
|---|---|
| DIA-FR-115 | Approved Demands shall appear automatically in the permitted Planning intake queue. |
| DIA-FR-116 | Planning shall receive the approved Demand snapshot, remaining item quantities or amounts, Strategy/value context and reservation references. |
| DIA-FR-117 | One Demand may be allocated to one or more stable Plan Items. Downstream tender packaging shall not create additional Demand consumption. |
| DIA-FR-118 | Planning Consumption shall identify the Demand, Demand Item, stable Plan Item, quantity where applicable, amount, reservation, proposed Plan Version, effective Plan Version and actor/time. |
| DIA-FR-119 | Planning shall not consume more than the approved and unconsumed quantity or amount. |
| DIA-FR-120 | Planning usage shall be derived as Not taken up, Partially planned or Fully planned from Effective allocations only. |
| DIA-FR-121 | Planning changes shall not rewrite Demand workflow status or its approved baseline. |
| DIA-FR-122 | The downstream purchase requisition shall reference the Demand and approved Plan Item where applicable. |
| DIA-FR-123 | An approved Plan revision that removes or reduces a Plan Item shall reverse only the affected Effective allocation and return the released scope to the Demand without creating or duplicating a funding reservation. |
| DIA-FR-124 | Draft Plan allocations and Proposed Plan Items shall not change Demand Planning usage or make the allocation effective. |
| DIA-FR-125 | Approval of the containing Plan Version shall atomically make its new or changed allocations Effective; an unchanged carried-forward Plan Item shall reuse its existing Effective allocation rather than create duplicate consumption. |

### 8.11 Notifications and audit

| ID | Requirement |
|---|---|
| DIA-FR-130 | The current owner shall receive an in-app notification when work is assigned or returned. |
| DIA-FR-131 | The Requester shall be notified of support, return, rejection, approval and cancellation. |
| DIA-FR-132 | Budget Officers shall be notified of every Budget Confirmation assigned to them; exception cases shall be clearly prioritised. |
| DIA-FR-133 | Planning users shall be notified or queued when a Demand becomes Approved and Planning Ready. |
| DIA-FR-134 | Notifications shall link to the record and state the required action, due context and reason where relevant. |
| DIA-FR-135 | All field changes, stage decisions, returns, funding checks, reservations, releases, scope overrides and downstream consumption shall be auditable. |
| DIA-FR-136 | Audit events shall record actor or service, timestamp, action, before/after values, reason and source record. |
| DIA-FR-137 | Audit history shall be append-only and visible to authorised audit users. |

### 8.12 Management and value reporting

| ID | Requirement |
|---|---|
| DIA-FR-140 | Operational views shall show volume and ageing by stage, owner unit, route and current assignee. |
| DIA-FR-141 | Management views shall show submission-to-approval cycle time and time spent at each stage. |
| DIA-FR-142 | The module shall report first-time-right rate, return rate and principal return reasons. |
| DIA-FR-143 | It shall report automatic budget-match rate, Budget Officer confirmation time, recommendation-adjustment rate, Funding Exceptions, insufficient-funding value and time to resolution. |
| DIA-FR-144 | It shall report potential duplicates, retained duplicates and aggregation candidates with drill-down evidence. |
| DIA-FR-145 | It shall report approved demand value by Strategy Outcome/Target and Plan Value Commitment treatment. |
| DIA-FR-146 | It shall report Standard, Additional and Emergency demand volume and value separately. |
| DIA-FR-147 | It shall report Approved Demands not taken up by Planning and Demand-to-Plan lead time. |
| DIA-FR-148 | Every metric shall expose reporting period, `As at`, entity and organisational coverage, calculation basis and drill-down records. |
| DIA-FR-149 | Estimates, approved demand value and Strategy alignment shall not be labelled as realised savings, benefits or outcomes. |

## 9. Role, visibility and permission contract

| Role | Workspace visibility | Record visibility | Permitted actions | State transitions | UI permissions |
|---|---|---|---|---|---|
| Requester | Personal intake and status views | Own Demands plus explicitly shared records in permitted scope | Create, edit Draft/Returned requester fields, submit, cancel pre-approval | Draft → In Review; Draft/Returned → Cancelled | Business fields and attachments; funding and specialist fields read-only or hidden |
| Business Approver | Business Review queue | Assigned Demands in permitted organisational scope | Support, Return, Reject, comment | In Review → Procurement Enrichment / Returned / Rejected | Business review and decision controls; funding details read-only |
| Procurement Approval Authority | Procurement and Final Approval queues | Entity/organisation scope granted by assignment | Enrich, confirm estimate/route/Strategy/value, link duplicates, group candidates, send for budget confirmation, Return, Reject, Approve, authorised cancel | Procurement Enrichment → Budget Confirmation; Final Approval → Approved/Returned/Rejected | Procurement fields and final actions; Budget master data read-only |
| Budget Officer | Budget Confirmations queue | Assigned Demands and linked funding context within permitted scope | Review recommendation, confirm or adjust allocations, resolve exceptions, Return | Budget Confirmation → Final Approval/Returned | Funding allocations, sign-off and exception fields; business and procurement decisions read-only |
| Planning Officer | Approved Demand intake | Approved Demands in planning scope | Consume, release consumption, link Plan Items/packages | No Demand workflow transition | Approved baseline read-only; Planning consumption controls only |
| Manager / Auditor | Oversight and reporting | Records within assigned entity/organisation scope | View, filter, export where authorised | None | Read-only with lineage and audit access |
| System Administrator | Configuration and support | Technical scope subject to data-access policy | Configure roles and reference data | None by administration alone | No business approval controls unless separately assigned the business role |

### 9.1 Scope enforcement

1. Every Demand shall carry `procuring_entity` and `owner_org_unit`.
2. User Scope Assignments shall govern record visibility and action authority.
3. Role assignment without entity/organisation scope shall grant no record access.
4. Cross-entity access shall require an explicit cross-entity assignment.
5. APIs, list counts, searches, exports and notifications shall enforce the same scope rules as the UI.
6. The secondary County fixture shall prove that users from one entity cannot access the other entity's records.
7. Demand creation authority shall be evaluated independently from general record visibility and administration privileges.
8. Where a user has multiple eligible creation pairs, every create request shall carry an explicit pair and the server shall reject an omitted, mismatched or unauthorised pair.
9. No environment, including local development, shall fall back to a hard-coded Procuring Entity or Organisation Unit.

## 10. Validation and readiness

### 10.1 Submission readiness

A Draft may be submitted only when it has:

- title;
- need statement;
- expected outcome;
- beneficiary description;
- required-by date;
- delivery location;
- Demand route and applicable route justification;
- an explicitly resolved and authorised Procuring Entity / owner Organisation Unit pair;
- owner organisational unit and Business Approver; and
- at least one Need Item description.

Budget Line, Strategy Target, procurement category, final estimate, quantity and unit of measure are not requester submission blockers.

### 10.2 Budget-confirmation readiness

The Procurement-enriched Demand may enter Budget Confirmation only when it has:

- supported business need;
- confirmed Demand route;
- procurement category;
- confirmed positive estimate and currency;
- sufficiently defined items;
- duplicate/aggregation review outcome;
- primary Strategy treatment; and
- all applicable Required Plan Value Commitments addressed or validly deferred.

### 10.3 Final approval readiness

Final approval requires:

- all Funding Exceptions resolved;
- one or more Budget Officer-confirmed funding allocations totalling the approved estimate;
- a current, valid Budget Officer sign-off;
- current successful funds check;
- no open blocking validation;
- authorised final approver; and
- segregation-of-duties compliance or an authorised, disclosed small-entity exception.

Warnings may require acknowledgement but shall not be treated as blockers unless the governing rule defines them as blocking.

## 11. Clean domain model

### 11.1 Demand

Core fields:

- internal immutable identifier
- system-generated Demand reference
- procuring entity
- owner organisational unit
- optional delivery organisational unit
- requester and technical contact
- title, need statement, expected outcome and beneficiaries
- delivery location and required-by date
- Demand route, urgency and route justification
- requester estimate, source and confidence
- confirmed estimate, currency and estimate basis
- procurement category
- workflow status, current stage and current owner
- approved baseline version and snapshot
- Planning Ready flag derived from Approved status
- planning usage derived from consumption
- original/replacement Demand link
- created, modified, submitted, approved, rejected and cancelled metadata

### 11.2 Demand Item

- immutable item identifier
- Demand identifier
- description
- optional quantity and unit of measure
- optional requester estimate
- confirmed quantity/unit and estimate where applicable
- required-by date or location override where necessary
- planning-consumed and remaining quantity/amount, derived

### 11.3 Demand Strategy Reference

- Demand identifier
- reference type: Primary or Supporting
- Strategy internal identifiers
- plan and immutable version identifier
- full Outcome/Target path
- human-readable snapshot
- applicability/selection source
- confirmation actor, time and reason

### 11.4 Demand Value Treatment

- Demand identifier
- Plan Value Commitment identifier/version/snapshot
- applicability
- proposed downstream treatment
- rationale
- confirmation actor and time

### 11.5 Demand Funding Allocation

- Demand identifier
- Budget and Budget Line identifiers
- allocation amount and currency
- matching source: Automatic or Budget Officer
- funds-check result and time
- Budget Officer confirmation status, actor and time
- recommendation-adjustment reason where applicable
- reservation identifier and status after approval
- availability snapshot before and after reservation

### 11.6 Funding Exception

- Demand identifier
- exception type
- candidate Budget Lines and diagnostic context
- current owner
- status
- resolution and reason
- created/resolved metadata

### 11.7 Demand Decision

- Demand identifier
- stage
- decision
- actor and role
- timestamp
- comment or mandatory reason
- decision-input snapshot

### 11.8 Planning Consumption

- Demand and Demand Item identifiers
- stable Plan Item identifier
- quantity and/or amount consumed
- reservation reference carried forward
- proposed-in Plan Version
- effective-from Plan Version
- optional reversed-by Plan Version
- status: Draft, Effective or Reversed
- actor, timestamp and reversal metadata

## 12. Service and application boundaries

### 12.1 Ownership

| Application | Owns |
|---|---|
| `kentender_procurement` | Demand, Demand Item, workflow, decisions, duplicate/aggregation links, approved baseline and Planning consumption |
| `kentender_budget` | Budget matching, funding availability, Funding Exceptions, reservations and releases |
| `kentender_strategy` | Strategy Scope Assignment, effective target search, version validation and Plan Value Commitment applicability |
| `kentender_core` | Procuring Entity, Organisation Unit, User Scope Assignment, shared audit and notifications |

### 12.2 Required service contracts

- `get_demand_creation_scopes`
- `create_or_update_demand`
- `submit_demand`
- `record_business_decision`
- `enrich_demand`
- `suggest_strategy_context`
- `validate_strategy_reference`
- `suggest_funding_allocations`
- `confirm_demand_funding`
- `resolve_funding_exception`
- `approve_and_reserve_demand`
- `cancel_and_release_demand`
- `consume_demand_in_planning`
- `get_demand_audit`

All state-changing services shall validate permissions and scope server-side. UI code shall not directly mutate lifecycle state or cross-application records.

### 12.3 Events

The lifecycle shall emit durable, traceable events or equivalent append-only audit entries for:

- DemandSubmitted
- BusinessSupported
- DemandReturned
- ProcurementEnriched
- FundingExceptionCreated
- BudgetConfirmed
- DemandApproved
- DemandRejected
- DemandCancelled
- DemandPlanningConsumed
- DemandPlanningConsumptionReversed

## 13. Non-functional requirements

| ID | Requirement |
|---|---|
| DIA-NFR-001 | Approval/reservation and cancellation/release shall be transactional, concurrency-safe and idempotent. |
| DIA-NFR-002 | Permissions and organisational scope shall be enforced server-side on every read and mutation. |
| DIA-NFR-003 | The module shall meet WCAG 2.1 AA for keyboard use, labels, focus, contrast and status communication. |
| DIA-NFR-004 | Desktop and tablet layouts shall remain usable without horizontal page scrolling; tables may use controlled responsive patterns. |
| DIA-NFR-005 | Ordinary queue and detail requests shall target a two-second response at normal MVP data volume, excluding file transfer. |
| DIA-NFR-006 | Dates and times shall be stored consistently and displayed in the user's configured timezone with explicit timezone where material. |
| DIA-NFR-007 | Files shall be access-controlled, malware-scanned where infrastructure permits and linked to immutable metadata. |
| DIA-NFR-008 | Validation messages shall identify the issue, owner and corrective action in business language. |
| DIA-NFR-009 | APIs shall return stable error codes for permission, validation, conflict, insufficient funding and stale-version failures. |
| DIA-NFR-010 | The approved snapshot, decisions and audit trail shall remain retrievable after Strategy or Budget supersession. |

## 14. Minimum screens

MVP 1 requires only:

1. **Demands workspace** — role-scoped queues, concise filters and visible next actions.
2. **Create/Edit Demand** — compact guided intake for the business need and Need Items, with visible zero-, single- or multi-scope ownership treatment before first save.
3. **Demand Review** — one record with stage-specific sections and actions for Business, Procurement, Funding and Final Approval.
4. **Demand Detail** — approved or terminal record, funding/Strategy context, Planning usage and audit history.
5. **Demand Performance** — manager view of demand flow, exceptions, value coverage and Planning uptake.

Separate forms for every workflow stage, an 11-step wizard, a generic workflow builder and duplicate specialist dashboards are not required.

## 15. Canonical seed-data contract

Implementation shall use KenTender MVP Canonical Demo Data Contract version 2.4, including its reconciled Demand baseline, deterministic zero-, single- and multi-scope creation fixtures and compatible downstream Planning extension.

### 15.1 Principal Ministry of Health story

The fixture shall include one Approved Demand owned by the Ministry of Health's eligible organisation unit for the existing health-supply-chain story:

- stable Demand reference;
- meaningful health-sector need and beneficiaries;
- Standard route;
- confirmed estimate of KES 455,000,000;
- versioned Strategy Target and Plan Value Commitment references already established in the Strategy fixture;
- one or more active Budget Line allocations already established in the Budget fixture;
- Budget Officer confirmation of the proposed allocation;
- final approval and reservation references;
- Planning usage Not taken up at the Demands-only seed boundary, then Fully planned in the complete canonical bundle through the Effective allocation for `PPI-MOH-2027-021` in Approved Plan Version 1.

### 15.2 Secondary and exception stories

The fixture shall also include:

1. one Ministry of Health Demand Returned to the Requester to demonstrate role ownership and correction; and
2. one minimal County Government of Kisumu Draft or In Review Demand with no Budget Line selected by the Requester, proving entity isolation and progressive enrichment.

All records shall use generic Procuring Entity and Organisation Unit references. No schema or script shall depend on Ministry-specific fields.

### 15.3 Repeatability

The seed script shall:

- be deterministic and idempotent;
- create the same references and relationships on every clean run;
- update canonical fixtures deliberately rather than creating duplicates;
- create users for Requester, Business Approver, Procurement Approval Authority, Budget Officer, Planning Officer and Viewer/Auditor;
- prove cross-entity denial between Ministry of Health and County Government of Kisumu;
- include one deterministic multi-scope Requester fixture with explicit creation assignments to the Ministry and County pairs, without treating Administrator as operational authority;
- produce a validation summary of created, updated, skipped and failed records; and
- fail if Strategy or Budget fixture references are missing or inconsistent.

## 16. Acceptance criteria

### 16.1 Core journey

| ID | Acceptance criterion |
|---|---|
| DIA-AC-001 | A Requester can submit a complete business need without selecting Strategy, Budget, Planning or procurement-method codes. |
| DIA-AC-002 | The correct Business Approver receives the Demand based on entity and owning organisation unit. |
| DIA-AC-003 | Business support routes the Demand to Procurement Enrichment without implying final approval. |
| DIA-AC-004 | Procurement can confirm category, estimate, route, Strategy and value context and can record duplicate/aggregation treatment. |
| DIA-AC-005 | A single valid Budget match is proposed automatically but proceeds to Final Approval only after Budget Officer confirmation; ambiguous or insufficient funding is additionally identified as an exception. |
| DIA-AC-006 | Final approval rechecks and reserves all funding atomically, locks the baseline and makes the Demand Planning Ready. |
| DIA-AC-007 | Repeating the approval request does not create a duplicate reservation. |
| DIA-AC-008 | Planning can partially and then fully consume the Approved Demand through Effective allocations in Approved Plan Versions without changing its approval status; Draft revisions do not change the projection. |

### 16.2 Controls

| ID | Acceptance criterion |
|---|---|
| DIA-AC-010 | A user cannot view or act on records outside assigned entity/organisation scope through UI or API. |
| DIA-AC-011 | A Requester cannot edit Procurement, Strategy confirmation or funding fields. |
| DIA-AC-012 | A Budget Officer must confirm every funding assignment and can resolve exceptions, but cannot approve the business need or final Demand. |
| DIA-AC-019 | A material funding-relevant change after Budget Officer sign-off invalidates that sign-off and returns the Demand to Budget Confirmation. |
| DIA-AC-013 | An administrator without an operational role cannot approve a Demand. |
| DIA-AC-014 | A failed reservation leaves the Demand unapproved and leaves no partial reservation. |
| DIA-AC-015 | An Approved Demand cannot be edited directly. |
| DIA-AC-016 | Approved cancellation releases only the unconsumed reservation balance and preserves audit history. |
| DIA-AC-017 | Emergency routing retains every required control and does not assign a procurement method. |
| DIA-AC-018 | Return identifies the correction owner and does not silently erase prior decisions. |
| DIA-AC-025 | A user with exactly one eligible Demand Requester scope sees that pair visibly preselected; a user with multiple eligible pairs must explicitly select a valid Procuring Entity and owning Organisation Unit before first save. |
| DIA-AC-026 | A user with no Demand Requester scope, including an Administrator without an explicit operational assignment, cannot create a Demand and receives no hard-coded or first-assignment fallback. |
| DIA-AC-027 | The server rejects a Demand create request whose submitted Procuring Entity / Organisation Unit pair is omitted, mismatched or outside the user's explicit Demand Requester assignments. |
| DIA-AC-028 | Changing the selected Procuring Entity clears the owning Organisation Unit and limits the replacement choices to authorised pairs for the selected entity. |

### 16.3 Data and reporting

| ID | Acceptance criterion |
|---|---|
| DIA-AC-020 | Strategy references remain readable after the source plan/version is superseded. |
| DIA-AC-021 | Demand funding allocations equal the approved estimate before approval. |
| DIA-AC-022 | Workspace counts, exports and management metrics use the same scope and source data as the underlying records. |
| DIA-AC-023 | Management metrics provide `As at`, coverage, calculation basis and drill-down. |
| DIA-AC-024 | Ministry of Health and County Government of Kisumu fixtures can be rebuilt repeatedly without duplicate records. |

## 17. Explicit non-requirements and legacy removals

Cursor shall not preserve or recreate the following merely because they exist in the previous MVP:

- mandatory requester selection of Budget Line or Strategy hierarchy;
- hard-coded `requesting_department`, `owner_state_department` or `owner_directorate` structures;
- Pending HoD Approval / Pending Finance Approval as the only workflow model;
- the legacy Pending Finance Approval state or a multi-level Finance workflow in place of the defined mandatory Budget Officer confirmation;
- a manual Planning Ready transition;
- `Planned / Unplanned / Emergency` as Demand routes;
- final procurement-method selection in Demand;
- budget commitment at Demand approval;
- a large multi-step requisition wizard;
- user-maintained Demand, Strategy, Budget or item codes;
- duplicate records or reservations at downstream hand-offs;
- Administrator-as-universal-business-approver behavior; or
- first-assignment, current-filter or hard-coded Administrator fallbacks for Demand ownership;
- dual-write compatibility with disposable legacy MVP fields.

## 18. Delivery gates

Implementation shall proceed only after the following sequence:

1. Approve and lock this requirements document.
2. Revise and version the canonical demo-data contract.
3. Produce and approve simple Stitch designs for the five minimum screens.
4. Produce the Cursor implementation prompt with explicit clean-rebuild and legacy-removal instructions.
5. Implement domain model and service contracts before UI state mutations.
6. Run role, entity-scope, workflow, funding-concurrency, seed-repeatability and end-to-end acceptance tests.
7. Audit the implementation requirement-by-requirement before marking MVP 1 complete.

## 19. Approval decision

Approval of this document locks the following MVP 1 pattern:

> Requesters explicitly establish an authorised Demand owner where more than one creation scope exists, then describe needs; Business Approvers validate legitimacy; Procurement enriches the Demand; a Budget Officer confirms every funding assignment and resolves any exception; Procurement gives the final approval; final approval reserves funding atomically; Approved Demands flow automatically to Planning; and every role, value commitment and downstream use remains traceable.
