# PLN-CHG-001 — Clean Procurement Planning

| Control | Value |
|---|---|
| Document ID | PLN-CHG-001 |
| Version | 1.0 |
| Date | 24 August 2026 |
| Status | Approved |
| Approval | Product owner · 24 August 2026 |
| Module | Procurement Planning |
| Implementation posture | Correct the existing module in place; reuse the proven Planning UI and Claude Design → Vue 3 → Frappe Desk pattern |

**Controlling decision:** Procurement Planning turns departmental requirements into one funded, governed Annual Procurement Plan with the fewest necessary user actions. A Departmental Procurement Plan may contain accepted Departmental Needs, direct departmental requirements, or both. Departmental Needs supports consultation but is not a prerequisite for planning. When the first DPP is accepted, the system automatically creates the initial Draft Annual Procurement Plan and places the accepted entries in its unallocated-source queue. The Planner begins with the meaningful work of forming Plan Items; there is no separate **Begin consolidation** gate. Planning owns requirement classification, the Budget Line and indicative amount on each departmental-plan entry, formation of Plan Items, selection of one Strategic Objective per Plan Item, Finance confirmation, plan review, approval, publication and the approved lineage exposed to Procurement Requisitions.

## 1. Governing decision

This document is the single implementation authority for Procurement Planning. On approval, it replaces the Planning canonical, functional, design and seed documents listed in section 19 wherever they conflict with this document.

The existing application is corrected in place. Proven page structure, components, visual tokens and working Planning interactions are reused where they conform. Removed concepts are deleted rather than renamed, aliased, dual-read or retained behind feature flags.

Completion requires one coherent result across schema, services, permissions, screens, fixtures and tests. A field, action, object, service, queue or screen not defined here is outside the module.

### 1.1 Conflict and disposition register

| Earlier item | Disposition in v1.0 |
|---|---|
| Every DPP entry and Plan Item must originate from an accepted Need | Correct. A DPP entry originates from either an `Accepted Departmental Need` or a `Direct departmental requirement`. |
| Accepted Need carries Strategy, requirement type, Budget Line, funding source, currency and amount into Planning | Remove. The Need supplies title, description, quantity, unit and required-by date only. Planning adds the Budget Line and indicative amount; the DPP Validator classifies the entry; the Planner selects the Strategic Objective on the Plan Item. |
| HoD must create a Need before planning a known requirement | Remove. The authorised departmental plan preparer may create a direct requirement inside the Draft DPP. No synthetic Need or bypass reason is created. |
| Need-origin quantity can be partially included or changed in Planning | Remove. A current accepted Need is represented exactly once and at its full accepted quantity in the DPP. |
| Direct and Need-origin entries use different approval routes | Remove. Both are certified in the same DPP and receive the same Procurement validation. |
| Budget specification belongs at Need creation | Remove. Budget Line and indicative amount are required on the DPP entry before HoD submission. |
| Strategic Objective belongs on the Need or DPP entry | Remove. Exactly one Active Strategic Objective is selected on each Plan Item. |
| `Value Commitment` on a Plan Item | Remove. Strategic Objectives and Outcomes already express the intended strategic contribution. |
| Separate recommended method and planned method | Replace with one governed `Procurement method` on the Plan Item. |
| Editable `Single year` and `No lots expected` fields when those are the only admitted values | Remove. Fixed MVP scope is not collected as user data. |
| Generic source reference, authority reference, evidence, note, contact or attachment fields | Remove unless a named decision in this document explicitly consumes the value. |
| AO recipient captured on a DPP submission | Remove. A DPP submission routes to the scoped DPP validation queue. The Accounting Officer acts later on the consolidated Annual Plan. |
| Separate **Begin consolidation** action and `Not started` Annual Plan state after a DPP is accepted | Remove. Acceptance of the first DPP creates/reuses Draft Version 1 automatically and projects its entries into the unallocated-source queue. |
| Mandatory wait for every department or a nil-plan declaration before Plan Item work | Remove. Accepted DPP entries may be formed incrementally. Later accepted entries flow into the same open Draft or, after activation, become pending inputs for a successor. |
| DPP readiness score or percentage | Remove. Readiness is an exact blocker list. |
| Custom System Administrator Planning workspace | Remove. Support and audit use authorised framework records and logs; they receive no Planning business action. |
| Planning-owned actual milestone entry and Monitoring Officer role | Remove from MVP-1. Tendering, Requisitions and Contract Management own actual operational events. Planning may display their read-only projections later. |
| 71 separately specified Stitch frames | Replace with the smaller Claude Design contract in section 12. State variants are functional requirements unless a visually distinct artboard is explicitly required. |
| Stitch/Tailwind markup imported into Frappe | Replace with Claude Design as visual evidence, then Vue 3 SFCs mounted in Frappe Desk. No design-runtime file is shipped. |
| Breadcrumb drawn inside the artboard | Remove. Breadcrumb is fixture data outside the artboard and is rendered by the existing Frappe header. |
| Plan approval page shows only a summary | Correct. Every review, certification and approval task shows the complete submitted Plan details before its decision controls. |
| Publication acknowledges a Tender opportunity | Remove. Annual Plan publication does not create or advertise a Tender. |
| Legacy compatibility and migrated Demand records | Prohibited. This remains a clean Planning domain. |

## 2. Purpose and outcomes

Procurement Planning shall provide:

- one Departmental Procurement Plan for each department and PE/FY context;
- automatic intake of every current accepted Need in that department and context;
- direct capture of a known departmental requirement without a Need;
- HoD certification of the complete departmental plan;
- Procurement classification and acceptance of each departmental entry;
- automatic intake of accepted departmental entries into the Draft Annual Plan;
- controlled formation of those entries into Plan Items;
- exact source lineage for every Plan Item;
- one Strategic Objective on every Plan Item;
- Budget Line selection and indicative amounts before departmental submission;
- live Finance confirmation and reservation before plan governance;
- professional review, Accounting Officer certification and configured approval;
- publication of the exact approved Plan Version before activation;
- an Active Plan baseline that Procurement Requisitions can validate; and
- controlled successor versions that never rewrite the Active baseline.

### 2.1 Scope exclusions

The module shall not contain:

- Need consultation, Need justification or Need review;
- Strategy plan authoring, Strategy approval, outcomes, indicators, targets or Value Commitment;
- Budget authorisation, Budget Line maintenance, funding-source maintenance, currency maintenance, commitments, expenditure or payments;
- a purchase request, Procurement Requisition, Tender, evaluation, contract, invoice or payment action;
- specifications, bills of quantities, Terms of Reference or attachments;
- a synthetic Need for a direct departmental requirement;
- a reason for not using Departmental Needs;
- partial use of an accepted Need;
- unit price, tax, cost breakdown or market-estimate components;
- editable contract-period or lotting fields in MVP-1;
- a generic note, comment, source reference, authority reference, evidence field, priority, score or completion percentage;
- actual procurement milestone entry or a Planning Monitoring Officer;
- editable technical identifiers, digests, audit actors or timestamps;
- a custom Frappe shell, header, breadcrumb, global PE/FY selector or navigation system; or
- legacy routes, aliases, compatibility adapters, fallback records or migrated fixtures.

### 2.2 Data-purpose gate

No stored field is permitted unless all three conditions are documented before implementation:

1. a current operational decision or output uses the field;
2. the screen, rule or service consuming it is named; and
3. its validation and system effect are defined.

“Useful later”, “normally captured”, “helpful context” and “the design showed it” are not valid reasons. An undocumented field is omitted, not added as optional data.

The Planning values below pass this gate:

| Value | Current consumer and effect |
|---|---|
| Direct requirement title | Identifies the departmental entry, validation task, source selector and Plan lineage. |
| Direct requirement description | Tells the HoD, DPP Validator and Planner what the department requires. |
| Quantity and unit | Establish the complete source quantity and the quantity available for one Plan Item allocation. |
| Required by | Constrains the Plan Item completion date. |
| Budget Line | Identifies the authoritative funding position checked by Finance. |
| Indicative amount | Establishes the entry value, Plan Item value and reservation request. |
| Requirement type classification | Determines compatible Plan Item formation and procurement reporting. |
| Plan Item title and description | Define the procurement package shown in the Annual Plan and downstream lineage. |
| Strategic Objective | Provides the approved strategic alignment for the Plan Item. |
| Procurement method | Provides the method recorded in the Annual Plan and reviewed by the Head of Procurement Function. MVP-1 assigns the sole admitted method; it does not ask the user to select a fixed value. |
| Aggregation reason | Explains why several departmental entries form one procurement package; required only for a combined item. |
| Seven planned dates | Produce the approved procurement schedule and enforce chronological readiness. |
| Return reason | Gives the correction owner one actionable reason while preserving the submitted snapshot. |

## 3. Fixed ownership and dependency boundary

- Configuration & Governance owns PE, organisation unit, Financial Year, timezone, unit catalogue, requirement-type catalogue, procurement-method catalogue, module windows, approval route and capability assignments.
- Departmental Needs owns accepted Need identity, accepted versions and the five requirement facts supplied to Planning.
- Strategy Alignment owns Strategic Plans and Active Strategic Objectives. Planning stores the selected Objective lineage on a Plan Item and never edits Strategy.
- Budget & Funding owns Budget identity, Budget Lines, funding source, currency, live positions, reservations, commitments and ledger events.
- Procurement Planning owns DPPs, direct requirements, DPP funding specification, classification, Annual Plans, Plan Items, source allocations, Finance tasks, Planning decisions, publication evidence and Requisition-eligibility projection.
- Procurement Requisitions owns the Requisition and its drawdown. Tendering and Contract Management own later operational records and actual milestones.

| Information or decision | Owner | Planning relationship |
|---|---|---|
| PE/FY context, OU, timezone and assignments | Configuration & Governance | Resolve exact identifiers and fail closed when absent or ambiguous. |
| DPP submission window | Procurement Planning configuration | Gate initial DPP submission and resubmission; opening a page creates nothing. |
| Accepted Need facts | Departmental Needs | Project read-only title, description, quantity, unit and required-by date. |
| Direct departmental requirement | Procurement Planning | Create and edit only inside a Draft or Returned DPP Version. |
| Budget Line identity, funding source and currency | Budget & Funding | Select from eligible Active Budget Lines and read live funding through services. |
| DPP indicative amount | Procurement Planning | Capture on every DPP entry and pass to Plan Item formation. |
| Requirement type | Procurement Planning | DPP Validator classifies the immutable submitted entry. |
| Strategic Objective | Strategy Alignment / Procurement Planning | Select exactly one Active Objective on the Plan Item and preserve its version lineage. |
| Finance confirmation and reservation | Planning task / Budget service | Planning owns task and decision UI; Budget performs the live check and reservation transaction. |
| Annual Plan approval and publication | Procurement Planning | Govern the exact Plan Version and activate only the acknowledged approved payload. |
| Requisition drawdown | Procurement Requisitions | Planning exposes eligibility and consumes authoritative drawdown references; it does not create a Requisition. |

Permitted dependency paths are:

**Configuration & Governance → Departmental Needs → Procurement Planning**

**Configuration & Governance / Strategy Alignment / Budget & Funding → Procurement Planning → Procurement Requisitions**

Planning shall consume other modules through explicit service or event contracts. It shall not import another module's controller or write directly to another module's tables.

## 4. Canonical domain model

All identifiers are generated by the server. Frappe audit fields remain framework-managed and are not duplicated as user data.

### 4.1 DPPSubmissionWindow

| Field | Operational purpose and system effect |
|---|---|
| `window_id` | Immutable command and audit reference. |
| `pe_fy_context_id` | Fixes the PE/FY scope. Required and unique. |
| `opens_at` | UTC instant from which an initial DPP may be submitted. Required. |
| `closes_at` | Inclusive UTC instant after which an initial DPP submission is unavailable. Required and later than `opens_at`. |

`Scheduled`, `Open` and `Closed` are derived from the configured clock. There is no title, description, manual status, reason or approval field.

### 4.2 DepartmentalProcurementPlan

Stable identity for one department in one PE/FY context.

| Field | Operational purpose and system effect |
|---|---|
| `dpp_id` | Immutable internal identity. |
| `dpp_reference` | Generated as `DPP-{PE code}-{OU code}-{FY start}-{3 digits}` and used in routes and queues. |
| `pe_fy_context_id` | Fixes the PE/FY permission and planning boundary. Required and immutable. |
| `org_unit_id` | Fixes the department and HoD scope. Required and immutable. |
| `current_state` | Derived root display state: `Draft`, `Submitted`, `Returned`, `Accepted` or `Withdrawn`. |
| `current_version_id` | Points to the current Draft, Returned or Submitted Version. |
| `current_accepted_version_id` | Points to the latest accepted Version. Empty until acceptance. |
| `record_version` | Monotonic optimistic-concurrency token. |

There is exactly one DPP root per `pe_fy_context_id + org_unit_id`.

### 4.3 DPPVersion

| Field | Operational purpose and system effect |
|---|---|
| `dpp_version_id` | Immutable version reference used by submission and Annual Plan lineage. |
| `dpp_id` | Links the Version to its stable root. |
| `version_number` | Generated sequence within the DPP. |
| `based_on_version_id` | Identifies the accepted Version copied for an update. Empty on Version 1. |
| `version_status` | `Draft`, `Submitted`, `Returned`, `Accepted`, `Superseded` or `Withdrawn`. |
| `submission_id` | Points to the immutable submitted snapshot. Empty before submission. |

A Draft Version is mutable. Submission locks its snapshot. A return creates a copied Draft correction and preserves the submitted Version. One accepted Version may coexist with at most one open successor.

### 4.4 DPPEntry

One departmental requirement in one DPP Version.

| Field | Operational purpose and system effect |
|---|---|
| `dpp_entry_id` | Immutable entry reference used by classification and source lineage. |
| `dpp_version_id` | Fixes the containing Version. |
| `source_origin` | `Accepted Departmental Need` or `Direct departmental requirement`. Required and immutable after creation. |
| `need_id` / `need_version_id` | Fix the accepted Need source. Required only for Need-origin entries; empty for direct entries. |
| `title` | Requirement label. Read-only projection for Need-origin; editable for direct origin. |
| `description` | Requirement statement. Read-only projection for Need-origin; editable for direct origin. |
| `quantity` | Full source quantity, greater than zero. Read-only for Need-origin. |
| `unit_id` | Governed quantity unit. Read-only for Need-origin. |
| `required_by_date` | Required and inside the target FY. Read-only for Need-origin. |
| `budget_line_id` | Planning-selected Active eligible Budget Line. Required before submission. |
| `indicative_amount_minor_units` | Planning-owned entry value. Required before submission and greater than zero. Currency is read from the Budget Line; there is no editable currency field. |

Direct entries contain no Need reference, business justification, bypass reason, attachment or source evidence. Need-origin entries contain no Planning copy of business justification.

### 4.5 DPPSubmission

The immutable HoD-certified snapshot of one DPP Version.

| Field | Operational purpose and system effect |
|---|---|
| `dpp_submission_id` | Immutable submission and queue reference. |
| `dpp_version_id` | Fixes the submitted Version. |
| `submission_number` | Generated sequence for the DPP root. |
| `submitted_entry_snapshots` | Immutable ordered rows containing each entry and its source lineage, funding specification and source version. |
| `attestation_text` | Exact fixed certification rendered with department and FY. |
| `submitted_by_user_id` | Records the HoD or effective delegate who certified the plan. |
| `effective_assignment_id` | Proves the exact departmental authority used. |
| `submitted_at` | Server decision instant. |

The attestation is:

> I certify that this Departmental Procurement Plan contains the current procurement requirements of {department} for {financial_year}, including every current accepted Departmental Need and any direct departmental requirements shown. I confirm that the quantities, required-by dates, Budget Lines and indicative amounts are ready for Procurement validation and inclusion in the Annual Procurement Plan.

### 4.6 DPPValidationTask and DPPValidationDecision

`DPPValidationTask` identifies the exact submitted DPP Version, PE/FY/OU scope, Open/Completed status and decision token. It is visible only to the effective DPP validation capability.

`DPPValidationDecision` is immutable and records:

- `Accept departmental plan` with one governed requirement type for every submitted entry; or
- `Return to department` with at least one structured issue containing the affected entry, concise problem and exact correction required.

There is no claim, priority, score, generic note or AO recipient.

### 4.7 AnnualProcurementPlan

| Field | Operational purpose and system effect |
|---|---|
| `plan_id` | Stable Annual Plan identity. |
| `plan_reference` | Generated as `PLN-{PE code}-{FY start}-{3 digits}`. |
| `pe_fy_context_id` | Fixes the PE/FY scope. Required and immutable. |
| `title` | System-generated as `{Procuring Entity} Annual Procurement Plan {FY label}`. |
| `active_version_id` | Points to the sole Active Version. Empty before activation. |
| `open_successor_version_id` | Points to the sole Draft or in-governance successor. Empty when none. |
| `record_version` | Optimistic-concurrency token. |

There is at most one AnnualProcurementPlan per PE/FY context and at most one open successor.

### 4.8 PlanVersion

| Field | Operational purpose and system effect |
|---|---|
| `plan_version_id` | Immutable version reference. |
| `plan_id` | Links to the stable Annual Plan. |
| `version_number` | Generated sequence within the Annual Plan. |
| `based_on_version_id` | Identifies the Active predecessor. Empty for Version 1. |
| `version_status` | `Draft`, `In professional review`, `Awaiting AO certification`, `Awaiting approval`, `Approved — publication pending`, `Publication failed`, `Active`, `Superseded` or `Cancelled`. |
| `change_reason` | Required only for a successor Version; identifies the approved-plan change being proposed. |

The mutable Draft content is locked when submitted. A return preserves the immutable submitted snapshot and creates the governed Draft correction state. The Active predecessor remains operational until the successor is approved, published and acknowledged.

### 4.9 PlanItem

| Field | Operational purpose and system effect |
|---|---|
| `plan_item_id` | Stable item reference used in plan output and downstream lineage. |
| `plan_version_id` | Fixes the containing Version. |
| `title` | Procurement package title; required, 5–160 characters. |
| `description` | Procurement-facing description; required, 10–1,000 characters. |
| `strategic_objective_id` | Exactly one Active Strategic Objective valid for the PE and Plan period. Required before Finance request. |
| `requirement_type_id` | Derived from the accepted DPP classification. All combined sources must have the same type. |
| `procurement_method_id` | System-assigned Active MVP method from the governed catalogue. Required before Finance request and read-only while Open Tender is the sole admitted method. |
| `aggregation_reason` | Required only when more than one DPP entry forms the item; 20–500 characters. Empty for a single-source item. |
| `invitation_date` | First planned procurement milestone. |
| `bid_opening_date` | Planned bid opening. |
| `evaluation_completion_date` | Planned evaluation completion. |
| `award_approval_date` | Planned award approval. |
| `award_notification_date` | Planned notification. |
| `contract_signing_date` | Planned contract signing. |
| `delivery_completion_date` | Planned delivery or implementation completion; not later than the earliest source required-by date. |
| `finance_state` | Derived as `Not requested`, `Awaiting Finance`, `Confirmed`, `Returned` or `Stale`. |
| `record_version` | Optimistic-concurrency token. |

Quantity, unit, planned value, funding source and Budget Line breakdown are derived from source allocations. Contract period, lotting, Value Commitment, recommended method, generic basis and actual milestone fields do not exist.

### 4.10 PlanSourceAllocation

| Field | Operational purpose and system effect |
|---|---|
| `allocation_id` | Immutable source-lineage reference. |
| `plan_item_id` | Identifies the Plan Item consuming the source. |
| `accepted_dpp_entry_id` | Fixes the exact accepted departmental entry. |
| `source_origin` | Preserves `Accepted Departmental Need` or `Direct departmental requirement`. |
| `need_id` / `need_version_id` | Preserves Need lineage only when the source has it. |
| `quantity` / `unit_id` | Full accepted source quantity. |
| `budget_line_id` / `indicative_amount_minor_units` | Full accepted source funding specification. |
| `allocation_state` | `Draft`, `Active`, `Removed in successor` or `Superseded`. |

One accepted DPP entry is allocated exactly once and at full quantity in one open Plan Version. No split allocation or partial amount is permitted in MVP-1.

### 4.11 FinanceTask, FinanceDecision and reservation reference

The Planning-owned Finance task fixes one Plan Item, its exact source allocations, required amounts, assigned funding scope, Open/Completed status and concurrency token.

The immutable Finance decision records `Confirm funding` or `Return to planner`, actor, effective assignment, time and required return reason where applicable. A successful confirmation stores one Budget-owned reservation reference per source allocation. It does not duplicate Budget position fields.

### 4.12 PlanGovernanceTask and PlanDecision

One protected task is created for each required stage:

- `Professional review` — Head of Procurement Function;
- `Accounting Officer certification` — Accounting Officer; and
- `Plan approval` — configured Plan Approval Authority.

Each task fixes the exact immutable submitted Plan Version, current stage, effective scope and concurrency token. Each decision stores the exact action, actor, assignment, decision time, submitted Version and required return reason. There is no optional note field.

### 4.13 PlanPublication

| Field | Operational purpose and system effect |
|---|---|
| `publication_id` | Immutable attempt reference. |
| `plan_version_id` | Fixes the approved Version. |
| `destination_configuration_id` | Fixes the configured Annual Plan publication destination. |
| `attempt_number` | Supports idempotent retry of the same approved payload. |
| `result` | `Pending`, `Acknowledged`, `Failed` or `Indeterminate`. |
| `external_reference` | Authoritative acknowledgement or failure reference returned by the adapter. |
| `attempted_at` / `acknowledged_at` | Server instants used by task and audit views. |

The approved Plan payload is generated from the immutable Version. Users cannot edit the payload, destination or acknowledgement.

### 4.14 RequisitionEligibilityProjection

Read-only contract containing Plan, Version, Plan Item and allocation lineage; approved quantity/value; authoritative drawdown quantity/value; remaining quantity/value; current funding state; Active status; and evaluation time. It creates no Requisition and stores no duplicate operational status on the Plan Item.

## 5. Lifecycle and business rules

### 5.1 DPP lifecycle

| Current state | Command | Result | Actor |
|---|---|---|---|
| No DPP | Open departmental plan | DPP root and Draft Version 1 | Departmental Plan Preparer or HoD |
| Draft | Save direct requirement / enrich Need / remove direct requirement | Draft updated | Departmental Plan Preparer or HoD |
| Draft | Submit departmental plan | Immutable submission and Open validation task | HoD or effective delegate |
| Submitted | Return to department | Submitted snapshot preserved; copied correction Draft created | DPP Validator |
| Submitted | Accept departmental plan | Submitted Version Accepted with classifications; accepted entries appear in the open Draft Annual Plan | DPP Validator |
| Returned | Save / Resubmit | Corrected Draft saved or submitted as the next submission | Departmental Plan Preparer; HoD submits |
| Accepted; change required | Create update | One Draft successor copied from Accepted Version | Departmental Plan Preparer or HoD |
| Draft successor | Submit update | Same validation route; Active Plan unchanged | HoD or effective delegate |
| Draft / Returned with no downstream consumption | Withdraw DPP Version | Version Withdrawn; prior Accepted Version remains current when one exists | HoD or effective delegate |

The DPP may consist entirely of direct requirements. If current accepted Needs exist in the exact department/context, all must be represented exactly once before submission. Direct entries may be added in any number. A DPP with no entries cannot be submitted. The window gates the first submission. A correction returned from validation and a successor required by an authoritative source change may be resubmitted after window close; neither route admits a new unreviewed initial DPP.

### 5.2 Annual Plan lifecycle

| Current state | Command | Result | Actor |
|---|---|---|---|
| First DPP accepted; no Annual Plan | Project accepted entries | Annual Plan and Draft Version 1 created automatically; entries shown as unallocated | System, in the DPP-acceptance transaction |
| Active; no successor | Begin plan update | Draft successor; Active Version unchanged | Procurement Planner |
| Draft | Form Plan Items / save item | Draft updated | Procurement Planner |
| Draft item | Request Finance confirmation | Open Finance task | Procurement Planner |
| Awaiting Finance | Confirm funding | All source reservations created; item Confirmed | Budget Officer |
| Awaiting Finance | Return to planner | No reservation; item Returned | Budget Officer |
| Draft; every item Confirmed | Submit for professional review | Immutable submitted snapshot; professional task | Procurement Planner |
| In professional review | Validate and submit to AO | Professional decision; AO task | Head of Procurement Function |
| In professional review | Return to planner | Return decision; governed Draft correction | Head of Procurement Function |
| Awaiting AO certification | Certify and submit | Certification decision; approval task | Accounting Officer |
| Awaiting AO certification | Return for correction | Return decision; governed Draft correction | Accounting Officer |
| Awaiting approval | Approve Annual Procurement Plan | Approved — publication pending | Plan Approval Authority |
| Awaiting approval | Return for correction | Return decision; governed Draft correction | Plan Approval Authority |
| Approved / Publication failed | Publish / Retry | Active only on exact acknowledgement; otherwise failed/indeterminate | Publication Operator |
| Draft successor | Cancel update | Successor Cancelled; Active Version unchanged | Procurement Planner |

### 5.3 Invariants

1. Reads never create a DPP, Annual Plan, Version, task, allocation, reservation or publication attempt.
2. One DPP root exists per PE/FY/OU and one Annual Plan root per PE/FY. The initial Annual Plan is created only by the first successful DPP acceptance, never by a read.
3. A current accepted Need is represented once and at full quantity in its department's submitted DPP.
4. A direct requirement never creates or pretends to be a Need.
5. Every submitted DPP entry has one eligible Budget Line and one positive indicative amount.
6. Only the DPP Validator classifies a submitted entry.
7. Every accepted DPP entry is allocated exactly once and at full quantity in the submitted Plan Version.
8. Sources may be combined only when PE/FY, requirement type, unit and procurement treatment are compatible.
9. Every Plan Item has exactly one current Active Strategic Objective.
10. Plan Item value equals the sum of its source-allocation amounts.
11. Finance confirmation is all-source and atomic; no partial reservation is permitted.
12. Planned dates are chronological and delivery completion is no later than the earliest source required-by date.
13. Governance actors decide only an immutable submitted Version and cannot edit it.
14. The Planner cannot professionally validate the Version they prepared; the professional reviewer, AO and approver are distinct effective capabilities.
15. Approval does not publish or activate the Plan.
16. Only acknowledgement of the exact approved payload activates a Version.
17. At most one Plan Version is Active and at most one successor is open.
18. An Active item remains eligible until an acknowledged successor changes it, subject to funding and drawdown.
19. An Active item with a Requisition drawdown, Tender handoff, commitment or contract cannot be removed through Planning.
20. Submitted, decided, approved, Active and Superseded evidence is never edited or deleted.

## 6. Roles and permissions

| Capability | Exact scope and permitted work |
|---|---|
| Departmental Plan Preparer | One PE/FY/OU; open DPP, enrich Need-origin entries, create/edit direct entries and correct a returned Draft. Cannot submit unless also HoD. |
| Head of User Department | One PE/FY/OU; all preparer work plus certify, submit, resubmit and withdraw the departmental Version. |
| DPP Validator | Assigned PE/FY/OU validation scope; view submitted DPP, classify entries, accept or return. Cannot decide a DPP they submitted. |
| Procurement Planner | Assigned PE/FY; consolidate accepted DPP entries, form/edit Plan Items, request Finance, submit the Plan and prepare successors. |
| Budget Officer | Assigned PE/FY and Budget scope; view protected Finance tasks, confirm funding or return. Cannot edit Planning content. |
| Head of Procurement Function | Assigned PE/FY; professionally review the complete submitted Plan or return it. |
| Accounting Officer | Assigned PE/FY; certify the complete professionally reviewed Plan or return it. |
| Plan Approval Authority | Configured PE/FY route; approve the complete AO-certified Plan or return it. |
| Publication Operator | Assigned PE/FY; publish or retry the exact approved payload. Cannot edit, approve or manually activate it. |
| Planning Viewer / Auditor | Authorised neutral read of Plan and immutable evidence only. |

System Manager, Administrator or a role label alone grants no business capability. Every list, count, detail, button and command uses the same effective PE/FY/OU and task-scope predicates.

## 7. Cross-module integration contracts

### 7.1 Departmental Needs intake

`DepartmentalNeedAccepted.v1` supplies event identity, Need/version lineage, PE/OU/FY, title, description, quantity, unit and required-by date. Projection is idempotent.

- The current accepted Need appears as one read-only Need-origin DPP entry.
- Planning adds only Budget Line and indicative amount.
- A successor accepted event marks the earlier unsubmitted source stale and refreshes the Draft; if already submitted or consumed, it creates a correction requirement without rewriting evidence.
- A withdrawn event removes only an unsubmitted/unconsumed source. Departmental Needs cannot publish withdrawal while an Active Plan dependency exists.
- `NeedPlanningUsageChanged.v1` is published only when an Active Plan begins or ceases to represent the accepted Need version.

### 7.2 Strategy selection

`ListEligibleStrategicObjectives` returns only Active Strategic Objectives for the same PE whose effective period covers the Plan Version. The selector displays the Objective title and its hierarchy path. Saving stores Objective ID, Strategy Plan ID and Strategy Version ID. Planning does not store Outcome, Indicator, Target or Value Commitment.

If the selected Objective ceases to be eligible before Plan submission, the item is blocked and the Planner must select a current Objective. An already Active Plan preserves its approved lineage.

### 7.3 Budget and Finance

`ListEligibleBudgetLines` returns only Active Budget Lines valid for the same PE/FY and department/PE scope. The DPP entry stores the selected line ID and amount; funding source and currency display from Budget read services.

`CheckAndReserveFunding` is called only from the protected Finance confirmation command. It rechecks each source allocation under lock and either creates every reservation or none. Planning stores reservation references; Budget remains authoritative for balances and ledger effects.

Need acceptance, DPP save, DPP submission, DPP validation and Plan Item formation create no reservation.

### 7.4 Requisition eligibility

Planning exposes an item only when its Plan Version is Active, Finance evidence remains current, remaining quantity and value are positive, and no blocking successor or withdrawal effect applies. The result includes exact lineage and an evaluation instant. Procurement Requisitions publishes authoritative drawdown references; Planning prevents overdraw but never creates the Requisition.

## 8. Service and command contracts

### 8.1 Read contracts

| Contract | Required result |
|---|---|
| `ResolvePlanningContexts` | Zero, one or several authorised PE/FY contexts; no implicit first record. |
| `GetPlanningWorkspace` | Reconciled action queue, waiting work and current Plan state using one scope predicate. |
| `GetDepartmentalPlan` | Current DPP Version, accepted Need coverage, direct entries, blockers and authorised commands. |
| `GetDPPValidationTask` | Exact immutable submission, all entry details, funding specification, source origin and current decision controls. |
| `ListAcceptedDPPSources` | Current accepted, unallocated entries for the exact PE/FY. |
| `GetPlanVersion` | Complete Version, all Plan Items, source allocations, Finance state, governance history and current commands. |
| `GetPlanItem` | Exact item, all source rows, Objective, method, schedule and Finance state. |
| `GetFinanceTask` | Protected current Budget positions and required/after-confirmation amounts for every source. |
| `GetPlanGovernanceTask` | Complete immutable Plan details and exact stage decision controls. |
| `GetPublicationTask` | Exact approved Version, destination, attempt result and permitted publish/retry action. |
| `GetRequisitionEligibility` | Current eligible or blocked result with lineage, balances and evaluation time. |

### 8.2 Commands

| Command | Core effect |
|---|---|
| `OpenDepartmentalPlan` | Idempotently create/reuse the one DPP root and Draft Version after exact authority checks. |
| `SaveNeedFunding` | Add or change only Budget Line and amount on a current Need-origin Draft entry. |
| `SaveDirectRequirement` | Create/update the seven permitted direct-entry values. |
| `RemoveDirectRequirement` | Remove an unsubmitted direct entry from the current Draft. |
| `SubmitDepartmentalPlan` | Revalidate complete accepted-Need coverage, direct entries, funding, window and HoD authority; create immutable submission and validation task. |
| `ReturnDepartmentalPlan` | Preserve submission, record structured issues and create the correction Draft. |
| `AcceptDepartmentalPlan` | Record classifications, create/reuse the initial Draft Annual Plan when necessary and project accepted entries into its unallocated-source queue in the same transaction. |
| `FormPlanItems` | Create one item per selected source or one combined item for compatible selected sources; allocate each source atomically. |
| `SavePlanItem` | Save only the Plan Item allow-list and recalculate exact blockers. |
| `RequestFinanceConfirmation` | Validate the complete item and create/reuse one current Finance task. |
| `ConfirmFunding` | Atomically reserve every source amount and record the Finance decision. |
| `ReturnFromFinance` | Record the required reason, create no reservation and reopen planner-owned fields. |
| `SubmitForProfessionalReview` | Require all accepted sources allocated, all items complete and Finance current; create immutable submission and task. |
| `ProfessionallyValidate` | Record professional decision and create the AO task. |
| `CertifyAndSubmit` | Record AO certification and create the configured approval task. |
| `ApproveAnnualPlan` | Record approval and move the exact Version to publication pending. |
| `ReturnPlanVersion` | Preserve the submitted snapshot, record actionable reason and open the governed correction state. |
| `PublishAnnualPlan` | Transmit the exact approved payload and activate only on acknowledged response. |
| `BeginPlanUpdate` | Create the sole Draft successor from the Active Version. |
| `RemovePlanItemInSuccessor` | Propose whole-item removal only when downstream checks permit it. |
| `CancelPlanUpdate` | Cancel successor and leave Active Version unchanged. |

All mutating commands require an expected record version and idempotency key. Server-side capability, scope, state and live-data checks are repeated inside the transaction.

## 9. Error contract

| Code | Plain-language result |
|---|---|
| `PLN_NO_CONTEXT` | You do not have access to a Procurement Planning context. |
| `PLN_WINDOW_CLOSED` | The initial departmental-plan submission window is closed. |
| `PLN_NEED_COVERAGE_INCOMPLETE` | Add every current accepted Need to this departmental plan before submitting. |
| `PLN_ENTRY_INCOMPLETE` | Complete the highlighted requirement fields before submitting. |
| `PLN_BUDGET_LINE_INELIGIBLE` | Select an Active Budget Line available to this department and Financial Year. |
| `PLN_DPP_STALE` | This departmental plan changed. Reload and review the current Version. |
| `PLN_CLASSIFICATION_INCOMPLETE` | Classify every submitted requirement before accepting the plan. |
| `PLN_SOURCE_UNAVAILABLE` | One or more selected departmental entries are no longer available for Plan Item formation. |
| `PLN_SOURCE_INCOMPATIBLE` | The selected entries cannot form one Plan Item. Create separate items. |
| `PLN_OBJECTIVE_INELIGIBLE` | Select an Active Strategic Objective valid for this Plan. |
| `PLN_SCHEDULE_INVALID` | Correct the highlighted dates so the schedule is chronological and meets the required-by date. |
| `PLN_FINANCE_SHORTFALL` | Funding is insufficient for one or more source allocations. No reservation was created. |
| `PLN_FINANCE_STALE` | Funding confirmation is no longer current. Request confirmation again. |
| `PLN_REVIEW_STALE` | This task has already changed. Reload to see the current decision. |
| `PLN_SEGREGATION_CONFLICT` | You cannot make this decision because you performed an incompatible earlier action. |
| `PLN_PUBLICATION_FAILED` | Publication was not acknowledged. The approved Plan remains unchanged and may be retried. |
| `PLN_REMOVAL_BLOCKED` | This Active Plan Item has downstream use and cannot be removed through Planning. |
| `PLN_STALE_WRITE` | Another user changed this record. Reload before continuing. |

Unauthorised detail and task reads return the same not-found response as a nonexistent record. Internal diagnostics are logged with a support correlation and are not shown as user fields.

## 10. UI architecture, menu and routes

Procurement Planning is a top-level KenTender workspace named **Procurement Planning**.

| Surface | Canonical Frappe Desk route | Primary capability |
|---|---|---|
| Planning workspace | `/app/procurement-planning` | All authorised Planning users |
| Departmental Plan | `/app/departmental-procurement-plan/{dpp_reference}` | Departmental preparer, HoD, DPP Validator read |
| DPP validation task | `/app/procurement-planning/dpp-review/{task_id}` | DPP Validator |
| Annual Plan | `/app/annual-procurement-plan/{plan_reference}` | Planner and authorised readers |
| Plan Item | `/app/procurement-plan-item/{plan_item_id}` | Planner and authorised readers |
| Finance task | `/app/procurement-planning/finance/{task_id}` | Assigned Budget Officer |
| Governance task | `/app/procurement-planning/review/{task_id}` | Exact professional, AO or approval capability |
| Publication task | `/app/procurement-planning/publication/{publication_task_id}` | Publication Operator |

The workspace shows only work the actor can perform or is waiting for. It does not duplicate Budget, Strategy, Needs or Configuration dashboards. Frappe supplies the Desk header, breadcrumb, global search, user menu and common navigation. The existing global PE/FY selector is reused and is never drawn inside a Claude Design artboard.

### 10.1 Existing UI reuse and correction

| Existing Planning asset | Disposition |
|---|---|
| Page shell, context strip, headers, cards, tables, status badges, dialogs and sticky action footer | Reuse. |
| Planning workspace, DPP workspace, Plan workbench, Plan Item editor, Finance drawer/task and wide governance review layout | Reuse and correct against this document. |
| Need-origin DPP row | Retain; remove Need-owned funding/Strategy/classification assumptions and add Planning funding completion. |
| Direct requirement editor | Add using PLN-DES-04. |
| Accepted-Need funding editor | Add or correct using PLN-DES-03. |
| Plan Item Strategy control | Add exactly one Strategic Objective selector. |
| Governance task detail | Retain layout; show the complete Plan Item table and Plan output before decisions. |
| Separate actor dashboards that differ only by disabled buttons | Collapse into capability-scoped queues and neutral read-only detail. |
| Monitoring entry/history and custom support workspace | Retire. |
| Stitch runtime, Tailwind utilities and vendor design markup | Keep only as historical visual evidence; never import into production. |

## 11. Static Claude Design contract

This section is the complete visual input to Claude Design. It defines appearance and exact fixture content only. Behaviour, validation, permissions, service calls, routing and state transitions are defined in section 12 and shall not be added to a design prompt.

### 11.1 Closed-input rules

- Produce desktop artboards at **1440 × 1024 px**.
- Reuse the approved KenTender Strategy Portfolio and deployed Planning visual system: spacing, type scale, tokens, cards, badges, tables, fields, buttons, tabs, empty states and dialogs.
- The artboard starts below the Frappe Desk header. Do not draw Frappe navigation, Desk header, breadcrumb, user menu, notifications, Help, global search or the global PE/FY selector.
- Breadcrumb text is fixture data outside the artboard. It is supplied only to confirm location.
- Use only the visible labels, values, badges, controls, sections and states stated for the artboard.
- Do not invent data. If a value, column, control, message or state is not stated, omit it.
- Do not encode behaviour, validation, permissions, APIs, routing, transitions, concurrency, component names or implementation instructions in the visual output.
- Do not add charts, percentages, trend arrows, illustrations, side panels, steppers, helper panels, generic notes, attachments, action menus, metadata or extra table columns.
- Do not show technical digests, record versions, idempotency keys, event IDs, audit field names or editable identifiers.
- Do not show Need business justification, Value Commitment, contract period, lotting, recommended method, generic method basis, unit price, tax, cost breakdown, actual milestones, Requisition creation or Tender controls.
- Generated references may appear as quiet read-only text but never as editable controls.

The approved page shell inside every artboard is:

- full-width warm-white page background;
- a 1200 px maximum-width content column centred in the available page area;
- 32 px top and bottom page padding;
- page header followed by 24 px vertical spacing;
- 16 px gaps between cards or table sections; and
- no custom sidebar.

### 11.2 PLN-DES-01 — Procurement Planning workspace

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · PE-MOH — Ministry of Health · FY 2027/28 · 1 Dec 2026, 09:00 EAT · Frappe header breadcrumb: **Home > Procurement Planning**

**Page content header**

- Eyebrow: **PROCUREMENT PLANNING**
- Title: **Annual procurement planning**
- Description: **Turn accepted departmental plans into a funded and approved Annual Procurement Plan.**
- No header action button

**Context strip**

| Label | Value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Financial Year | FY 2027/28 |
| Annual Plan | Draft Version 1 |

**Your work card**

Heading: **Your work**

| Work item | Scope | Status | Action |
|---|---|---|---|
| Form Plan Items | 1 accepted departmental entry · KES 80,000,000 | Ready | Open Annual Plan |

**Departmental plans card**

Heading: **Departmental plans**

| Department | Version | Requirements | Value | Status | Action |
|---|---:|---:|---:|---|---|
| Digital Health | 1 | 1 | KES 80,000,000 | Accepted | View |
| Human Resources Management and Development | 1 | 2 | KES 88,000,000 | Draft | View |

Below the table: **2 departmental plans**. Do not show summary cards, charts, waiting queues or system support links.

### 11.3 PLN-DES-02 — Draft Departmental Procurement Plan

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Plan Preparer · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 24 Nov 2026, 15:00 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP-MOH-DHI-2027-001**

**Page content header**

- Eyebrow: **DEPARTMENTAL PROCUREMENT PLAN**
- Title: **Digital Health departmental plan**
- Quiet reference: **DPP-MOH-DHI-2027-001 · Version 1**
- Status badge: **Draft**
- Right-aligned secondary button: **View accepted needs**
- Right-aligned primary button: **Add direct requirement**

**Context strip**

| Label | Value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Department | OU-MOH-DHI — Digital Health |
| Financial Year | FY 2027/28 |
| Submission window | Open until 30 Nov 2026, 23:59 EAT |

**Readiness notice**

Amber notice title: **1 requirement needs funding details**

Text: **Select a Budget Line and enter the indicative amount for every requirement before the plan can be submitted.**

**Requirements table**

| Requirement | Source | Quantity | Required by | Budget Line | Indicative amount | Status | Action |
|---|---|---:|---|---|---:|---|---|
| National digital health infrastructure upgrade | Accepted Need · NDS-MOH-2027-0001 | 1 programme | 31 Aug 2027 | Not selected | — | Funding incomplete | Complete |
| Digital health platform security assessment | Direct requirement | 1 service | 31 Oct 2027 | MOH-BL-DHI-2027 | KES 20,000,000 | Ready | Edit |

Below the table: **2 requirements · KES 20,000,000 specified**.

**Sticky page footer**

- Left-aligned secondary text button: **Back to workspace**
- Right-aligned secondary button: **Save draft**
- Right-aligned disabled primary button: **Submit departmental plan**

Do not show Strategy, requirement type, funding source column, currency selector, business justification, attachment, source reference or Plan Item controls.

### 11.4 PLN-DES-03 — Accepted Need funding details

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Plan Preparer · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 24 Nov 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP-MOH-DHI-2027-001 > NDS-MOH-2027-0001**

**Page content header**

- Title: **Complete funding details**
- Description: **Add the Planning-owned funding details for this accepted departmental requirement.**
- Status badge: **Accepted Need**
- No header action button

**Accepted requirement card**

Use five read-only fields:

| Field label | Displayed value |
|---|---|
| Title | National digital health infrastructure upgrade |
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Quantity | 1 programme |
| Required by | 31 Aug 2027 |
| Accepted Need | NDS-MOH-2027-0001 · Version 1 |

**Planning funding card**

| Field label | Displayed value |
|---|---|
| Budget Line | MOH-BL-DHI-2027 — Digital health infrastructure programme |
| Indicative amount | 80,000,000 |
| Currency | KES |

Budget Line is a select field. Indicative amount is a money input. Currency uses the approved read-only field component.

**Sticky page footer**

- Left-aligned secondary button: **Cancel**
- Right-aligned primary button: **Save funding details**

Do not show or edit Need description, quantity, unit, required-by, business justification, Strategy, requirement type, procurement method or reservation.

### 11.5 PLN-DES-04 — Direct departmental requirement

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Plan Preparer · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 24 Nov 2026, 15:10 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP-MOH-DHI-2027-001 > Add direct requirement**

**Page content header**

- Title: **Add direct requirement**
- Description: **Add a requirement the department already knows it needs to procure.**
- Status badge: **New**
- No header action button

**Context card**

| Field label | Displayed value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Department | OU-MOH-DHI — Digital Health |
| Financial Year | FY 2027/28 |

All three rows use the approved read-only field component.

**Requirement card**

| Field label | Displayed value |
|---|---|
| Title | Digital health platform security assessment |
| Description | Assess the security of the national digital health platform and provide a prioritised remediation report. |
| Quantity | 1 |
| Unit | Service |
| Required by | 31 Oct 2027 |

Title is a single-line input. Description is a multiline input. Quantity and Unit appear side by side; Required by appears below them.

**Funding card**

| Field label | Displayed value |
|---|---|
| Budget Line | MOH-BL-DHI-2027 — Digital health infrastructure programme |
| Indicative amount | 20,000,000 |
| Currency | KES |

Budget Line is a select field. Indicative amount is a money input. Currency is read-only.

**Sticky page footer**

- Left-aligned secondary button: **Cancel**
- Right-aligned primary button: **Add requirement**

Do not show Need, bypass reason, business justification, Strategy, requirement type, procurement method, attachment, source reference, funding source selector or reservation.

### 11.6 PLN-DES-05 — HoD departmental-plan submission

**Fixture context — outside the artboard:** Dr Peter Kimani · `peter.kimani@moh.example.test` · Head of User Department · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 25 Nov 2026, 09:55 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP-MOH-DHI-2027-001**

Use PLN-DES-02 page geometry with these exact differences:

- Status badge: **Ready to submit**
- No readiness notice
- Both table rows show status **Ready**
- First row Budget Line: **MOH-BL-DHI-2027**
- First row Indicative amount: **KES 80,000,000**
- Below the table: **2 requirements · KES 100,000,000**
- Right-aligned primary button: **Submit departmental plan**

Below the table, show a bordered certification card:

Heading: **Departmental certification**

Text: **I certify that this Departmental Procurement Plan contains the current procurement requirements of Digital Health for FY 2027/28, including every current accepted Departmental Need and any direct departmental requirements shown. I confirm that the quantities, required-by dates, Budget Lines and indicative amounts are ready for Procurement validation and inclusion in the Annual Procurement Plan.**

Checkbox label: **I confirm this certification**

Do not show an Accounting Officer recipient, classification, Strategy, approval route or generic comments field.

### 11.7 PLN-DES-06 — DPP validation task

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · DPP Validator · PE-MOH — Ministry of Health · FY 2027/28 · 27 Nov 2026, 13:45 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP review > DPP-MOH-DHI-2027-001**

**Page content header**

- Eyebrow: **DEPARTMENTAL PLAN REVIEW**
- Title: **Validate Digital Health departmental plan**
- Quiet reference: **DPP-MOH-DHI-2027-001 · Submitted Version 1**
- Status badge: **Awaiting validation**
- No header action button

**Submission context card**

| Label | Value |
|---|---|
| Procuring Entity | Ministry of Health |
| Department | Digital Health |
| Financial Year | FY 2027/28 |
| Submitted by | Dr Peter Kimani |
| Submitted | 25 Nov 2026, 10:00 EAT |
| Requirements | 2 |
| Total indicative value | KES 100,000,000 |

**Submitted requirements table**

| Requirement | Source | Quantity | Required by | Budget Line | Amount | Requirement type | Action |
|---|---|---:|---|---|---:|---|---|
| National digital health infrastructure upgrade | Accepted Need · NDS-MOH-2027-0001 | 1 programme | 31 Aug 2027 | MOH-BL-DHI-2027 | KES 80,000,000 | Non-consulting services | View |
| Digital health platform security assessment | Direct requirement | 1 service | 31 Oct 2027 | MOH-BL-DHI-2027 | KES 20,000,000 | Consulting services | View |

Requirement type uses an inline select in each row. All other cells are read-only.

**Departmental certification card**

Show the exact certification text from PLN-DES-05, followed by **Certified by Dr Peter Kimani · 25 Nov 2026, 10:00 EAT**.

**Decision footer**

- Left-aligned secondary button: **Return to department**
- Right-aligned primary button: **Accept departmental plan**

Do not show editable requirement facts, editable Budget data, Strategy, Finance confirmation, AO decision, score, checklist or generic note.

### 11.8 PLN-DES-07 — Draft Annual Procurement Plan

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · PE-MOH — Ministry of Health · FY 2027/28 · 1 Dec 2026, 09:10 EAT · Frappe header breadcrumb: **Home > Procurement Planning > PLN-MOH-2027-001**

**Page content header**

- Eyebrow: **ANNUAL PROCUREMENT PLAN**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **PLN-MOH-2027-001 · Version 1**
- Status badge: **Draft**
- Right-aligned primary button: **Form Plan Items**

**Plan summary strip**

| Label | Value |
|---|---|
| Accepted departmental entries | 1 |
| Allocated | 0 |
| Plan Items | 0 |
| Plan value | KES 0 |

**Unallocated sources card**

Heading: **Accepted departmental entries**

| Requirement | Department | Source origin | Classification | Quantity | Budget Line | Amount | Status |
|---|---|---|---|---:|---|---:|---|
| National digital health infrastructure upgrade | Digital Health | Accepted Departmental Need | Non-consulting services | 1 programme | MOH-BL-DHI-2027 | KES 80,000,000 | Unallocated |

Below the table: **1 entry available**.

**Plan Items card**

Heading: **Plan Items**

Empty-state title: **No Plan Items yet**

Empty-state text: **Form Plan Items from the accepted departmental entries above.**

**Sticky page footer**

- Left-aligned secondary button: **Back to workspace**
- Right-aligned disabled primary button: **Submit for professional review**

Do not show charts, creation of a blank Plan Item, Need business justification, Finance decision controls or approval controls.

### 11.9 PLN-DES-08 — Form Plan Items dialog

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · PE-MOH — Ministry of Health · FY 2027/28 · 1 Dec 2026, 09:12 EAT · Frappe header breadcrumb: **Home > Procurement Planning > PLN-MOH-2027-001**

Use PLN-DES-07 as a dimmed background.

**Dialog**

- Title: **Form Plan Items**
- Intro: **Select accepted departmental entries and choose how they should form procurement packages.**

**Source table**

| Select | Requirement | Department | Classification | Quantity | Amount |
|---|---|---|---|---:|---:|
| Checked | National digital health infrastructure upgrade | Digital Health | Non-consulting services | 1 programme | KES 80,000,000 |

**Formation choice**

Selected radio: **Create one Plan Item for each selected requirement**

Unselected radio: **Create one combined Plan Item from all selected requirements**

**Result preview**

| Label | Value |
|---|---|
| Selected entries | 1 |
| Plan Items to create | 1 |
| Total value | KES 80,000,000 |

**Dialog footer**

- Secondary button: **Cancel**
- Primary button: **Create 1 Plan Item**

Do not show a source search, partial quantity, amount override, lot split, Strategy, method, Finance or generic note.

### 11.10 PLN-DES-09 — Plan Item editor

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · PE-MOH — Ministry of Health · FY 2027/28 · 3 Dec 2026, 14:00 EAT · Frappe header breadcrumb: **Home > Procurement Planning > PLN-MOH-2027-001 > PPI-MOH-2027-021**

**Page content header**

- Eyebrow: **PLAN ITEM**
- Title: **National digital health infrastructure upgrade**
- Quiet reference: **PPI-MOH-2027-021 · Draft Version 1**
- Status badges: **Proposed** and **Finance not requested**
- No header action button

**Source card**

Heading: **Departmental source**

| Label | Value |
|---|---|
| Department | Digital Health |
| Source origin | Accepted Departmental Need |
| Departmental plan | DPP-MOH-DHI-2027-001 · Version 1 |
| Accepted Need | NDS-MOH-2027-0001 · Version 1 |
| Quantity | 1 programme |
| Required by | 31 Aug 2027 |
| Budget Line | MOH-BL-DHI-2027 — Digital health infrastructure programme |
| Planned value | KES 80,000,000 |

All source rows are read-only.

**Procurement package card**

| Field label | Displayed value |
|---|---|
| Plan Item title | National digital health infrastructure upgrade |
| Procurement description | Procure and implement the national digital health infrastructure upgrade as one integrated FY 2027/28 programme. |
| Requirement type | Non-consulting services |
| Strategic Objective | OBJ-MOH-2023-001 — Strengthen interoperable national digital health services |
| Objective path | Digital health systems › Health policy, standards and regulation › Digital health governance |
| Procurement method | Open Tender |

Title and Procurement description are editable. Strategic Objective is a select field. Requirement type, Objective path and Procurement method are read-only.

**Planned schedule card**

Use a two-column field grid with these exact dates:

| Field label | Displayed value |
|---|---|
| Invitation or advertisement | 1 May 2027 |
| Bid opening | 23 May 2027 |
| Evaluation completion | 23 Jun 2027 |
| Tender award approval | 10 Jul 2027 |
| Notification of award | 14 Jul 2027 |
| Contract signing | 1 Aug 2027 |
| Delivery or implementation completion | 31 Aug 2027 |

**Sticky page footer**

- Left-aligned secondary text button: **Back to Annual Plan**
- Right-aligned secondary button: **Save draft**
- Right-aligned primary button: **Request Finance confirmation**

Do not show Value Commitment, contract period, lotting, recommended method, method basis, actual dates, attachment or source edit.

### 11.11 PLN-DES-09A — Combined Plan Item editor

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · PE-MOH — Ministry of Health · FY 2027/28 · 3 Dec 2026, 15:00 EAT · Frappe header breadcrumb: **Home > Procurement Planning > PLN-MOH-2027-001 > PPI-MOH-2027-033**

Use PLN-DES-09 page geometry with these exact replacements:

- Title: **Clinical training and deployment laptops for digital health rollout**
- Quiet reference: **PPI-MOH-2027-033 · Draft Version 1**

Replace the single source card with **Departmental sources**:

| Requirement | Department | Source origin | Quantity | Budget Line | Amount |
|---|---|---|---:|---|---:|
| Clinical training laptops for digital health rollout | Human Resources Management and Development | Accepted Departmental Need | 200 each | MOH-BL-HWD-2027 | KES 48,000,000 |
| Clinical deployment laptops for digital health rollout | Digital Health | Accepted Departmental Need | 300 each | MOH-BL-DHI-2027 | KES 72,000,000 |

Below the table: **2 sources · 500 each · KES 120,000,000**.

**Procurement package card**

| Field label | Displayed value |
|---|---|
| Plan Item title | Clinical training and deployment laptops for digital health rollout |
| Procurement description | Procure one standard laptop specification and deployment service for the national digital-health rollout across both source departments. |
| Requirement type | Goods |
| Strategic Objective | OBJ-MOH-2023-001 — Strengthen interoperable national digital health services |
| Objective path | Digital health systems › Health policy, standards and regulation › Digital health governance |
| Procurement method | Open Tender |
| Aggregation reason | Procure one standard laptop specification and deployment service for the same national digital-health rollout. |

Use the same schedule card and footer layout as PLN-DES-09, with delivery completion **31 Dec 2027**. Do not show source detachment, partial allocation, different treatment per source or a generic reason field.

### 11.12 PLN-DES-10 — Finance confirmation task

**Fixture context — outside the artboard:** MOH Budget Officer · `moh.budget.officer@example.test` · Budget Officer · PE-MOH — Ministry of Health · FY 2027/28 · 4 Dec 2026, 09:58 EAT · Frappe header breadcrumb: **Home > Procurement Planning > Finance > FNT-MOH-2027-021-001**

**Page content header**

- Eyebrow: **FINANCE CONFIRMATION**
- Title: **Confirm funding for Plan Item**
- Quiet reference: **FNT-MOH-2027-021-001 · PPI-MOH-2027-021**
- Status badge: **Awaiting Finance**
- No header action button

**Plan Item card**

| Label | Value |
|---|---|
| Plan Item | National digital health infrastructure upgrade |
| Department | Digital Health |
| Requirement type | Non-consulting services |
| Planned value | KES 80,000,000 |
| Procurement method | Open Tender |
| Delivery completion | 31 Aug 2027 |

**Funding position table**

As-at line: **Position as at 4 Dec 2026, 09:58 EAT**

| Budget Line | Funding source | Approved | Reserved | Committed | Available | Required | Available after confirmation |
|---|---|---:|---:|---:|---:|---:|---:|
| MOH-BL-DHI-2027 — Digital health infrastructure programme | Government of Kenya | KES 100,000,000 | KES 0 | KES 0 | KES 100,000,000 | KES 80,000,000 | KES 20,000,000 |

Green notice: **Full funding is available for every source allocation.**

**Decision footer**

- Left-aligned secondary button: **Return to planner**
- Right-aligned primary button: **Confirm funding**

Do not show editable amounts, Budget Line changes, optional note, partial confirmation, Plan approval or Budget-maintenance controls.

### 11.13 PLN-DES-11 — Professional review task

**Fixture context — outside the artboard:** Samuel Otieno · `samuel.otieno@moh.example.test` · Head of Procurement Function · PE-MOH — Ministry of Health · FY 2027/28 · 7 Dec 2026, 09:55 EAT · Frappe header breadcrumb: **Home > Procurement Planning > Professional review > PLN-MOH-2027-001-V1**

**Page content header**

- Eyebrow: **PROFESSIONAL REVIEW**
- Title: **Review Annual Procurement Plan**
- Quiet reference: **PLN-MOH-2027-001 · Submitted Version 1**
- Status badge: **In professional review**
- No header action button

**Submission context card**

| Label | Value |
|---|---|
| Procuring Entity | Ministry of Health |
| Financial Year | FY 2027/28 |
| Submitted by | Mercy Kilonzo |
| Submitted | 7 Dec 2026, 09:30 EAT |
| Plan Items | 1 |
| Total value | KES 80,000,000 |

**Plan Items table**

| Plan Item | Source | Strategic Objective | Type | Method | Completion | Value | Finance | Action |
|---|---|---|---|---|---|---:|---|---|
| PPI-MOH-2027-021 · National digital health infrastructure upgrade | Digital Health · Accepted Need | Strengthen interoperable national digital health services | Non-consulting services | Open Tender | 31 Aug 2027 | KES 80,000,000 | Confirmed | View details |

**Plan output card**

| Label | Value |
|---|---|
| Plan reference | PLN-MOH-2027-001 |
| Version | 1 |
| Departments | Digital Health |
| Budget Lines | MOH-BL-DHI-2027 |
| Finance reservations | 1 confirmed · KES 80,000,000 |

**Decision history**

| Event | Actor | Time |
|---|---|---|
| Draft Version 1 created from the first accepted departmental plan | System | 27 Nov 2026, 14:00 EAT |
| Plan Item formed | Mercy Kilonzo | 1 Dec 2026, 09:00 EAT |
| Funding confirmed | MOH Budget Officer | 4 Dec 2026, 10:00 EAT |
| Submitted for professional review | Mercy Kilonzo | 7 Dec 2026, 09:30 EAT |

**Decision footer**

- Left-aligned secondary button: **Return to planner**
- Right-aligned primary button: **Validate and submit to Accounting Officer**

Do not show editable Plan fields, optional professional note, final approval, publication or generic checklist.

### 11.14 PLN-DES-12 — Accounting Officer certification task

**Fixture context — outside the artboard:** Amina Hassan · `amina.hassan@moh.example.test` · Accounting Officer · PE-MOH — Ministry of Health · FY 2027/28 · 8 Dec 2026, 09:55 EAT · Frappe header breadcrumb: **Home > Procurement Planning > Accounting Officer certification > PLN-MOH-2027-001-V1**

Use PLN-DES-11 geometry and show the same complete Plan Items table and Plan output card.

Exact replacements:

- Eyebrow: **ACCOUNTING OFFICER CERTIFICATION**
- Title: **Certify Annual Procurement Plan**
- Status badge: **Awaiting certification**
- Submission card adds **Professionally validated by — Samuel Otieno** and **Professionally validated — 7 Dec 2026, 10:00 EAT**
- Decision history adds **Professionally validated and submitted — Samuel Otieno — 7 Dec 2026, 10:00 EAT**
- Left button: **Return for correction**
- Primary button: **Certify and submit**

Above the footer show a bordered certification statement:

**I certify that the complete Annual Procurement Plan Version 1 shown above is ready for submission to the configured Plan Approval Authority.**

Do not show an optional certification note, editable Plan content, approval button, publication or a summary without the Plan Item table.

### 11.15 PLN-DES-13 — Plan approval task

**Fixture context — outside the artboard:** National-government Plan Approver · `moh.plan.approver@example.test` · Plan Approval Authority · PE-MOH — Ministry of Health · FY 2027/28 · 9 Dec 2026, 10:55 EAT · Frappe header breadcrumb: **Home > Procurement Planning > Plan approval > PLN-MOH-2027-001-V1**

Use PLN-DES-11 geometry and show the same complete Plan Items table and Plan output card.

Exact replacements:

- Eyebrow: **PLAN APPROVAL**
- Title: **Approve Annual Procurement Plan**
- Status badge: **Awaiting approval**
- Top authority card: **Plan Approval Authority — National-government Plan Approval Authority**; **Approval route — National government PE plan route**
- Submission context shows **Certified by — Amina Hassan** and **Certified — 8 Dec 2026, 10:00 EAT**
- Decision history includes professional validation and AO certification
- Left button: **Return for correction**
- Primary button: **Approve Annual Procurement Plan**

Quiet notice above the footer: **Approval does not publish or activate the Plan.**

Do not show an optional approval note, editable Plan content, publication button, generic review title or a summary without the complete Plan Item table.

### 11.16 PLN-DES-14 — Publication task

**Fixture context — outside the artboard:** MOH Plan Publisher · `moh.plan.publisher@example.test` · Publication Operator · PE-MOH — Ministry of Health · FY 2027/28 · 10 Dec 2026, 14:50 EAT · Frappe header breadcrumb: **Home > Procurement Planning > Publication > PLN-MOH-2027-001-V1**

**Page content header**

- Eyebrow: **ANNUAL PLAN PUBLICATION**
- Title: **Publish approved Annual Procurement Plan**
- Quiet reference: **PLN-MOH-2027-001 · Version 1**
- Status badge: **Approved — publication pending**
- No header action button

**Approved Plan card**

| Label | Value |
|---|---|
| Procuring Entity | Ministry of Health |
| Financial Year | FY 2027/28 |
| Plan Items | 1 |
| Approved value | KES 80,000,000 |
| Approved by | National-government Plan Approval Authority |
| Approved | 9 Dec 2026, 11:00 EAT |

**Plan Items table**

| Plan Item | Department | Strategic Objective | Method | Completion | Value |
|---|---|---|---|---|---:|
| PPI-MOH-2027-021 · National digital health infrastructure upgrade | Digital Health | Strengthen interoperable national digital health services | Open Tender | 31 Aug 2027 | KES 80,000,000 |

**Publication destination card**

| Label | Value |
|---|---|
| Destination | KenTender Annual Plan Publication Sandbox |
| Configuration | MOH-APP-SANDBOX-v1 |
| Latest attempt | None |
| Acknowledgement | Not received |

**Page footer**

- Right-aligned primary button: **Publish Annual Procurement Plan**

Do not show a payload editor, digest, destination selector, manual acknowledgement, optional note, approval action or Tender publication control.

### 11.17 PLN-DES-15 — Active Annual Procurement Plan

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · PE-MOH — Ministry of Health · FY 2027/28 · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Procurement Planning > PLN-MOH-2027-001**

**Page content header**

- Eyebrow: **ANNUAL PROCUREMENT PLAN**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **PLN-MOH-2027-001 · Version 1**
- Status badge: **Active**
- Right-aligned primary button: **Prepare plan update**

**Plan summary strip**

| Label | Value |
|---|---|
| Plan Items | 1 |
| Approved value | KES 80,000,000 |
| Departments | 1 |
| Activated | 10 Dec 2026, 15:00 EAT |

**Plan Items table**

| Plan Item | Department | Source origin | Strategic Objective | Method | Completion | Value | Requisition availability | Action |
|---|---|---|---|---|---|---:|---|---|
| PPI-MOH-2027-021 · National digital health infrastructure upgrade | Digital Health | Accepted Departmental Need | Strengthen interoperable national digital health services | Open Tender | 31 Aug 2027 | KES 80,000,000 | 1 programme · KES 80,000,000 | View |

**Approval and publication card**

| Label | Value |
|---|---|
| Professional validation | Samuel Otieno · 7 Dec 2026, 10:00 EAT |
| Accounting Officer certification | Amina Hassan · 8 Dec 2026, 10:00 EAT |
| Plan approval | National-government Plan Approval Authority · 9 Dec 2026, 11:00 EAT |
| Publication | Acknowledged · 10 Dec 2026, 15:00 EAT |

Do not show actual milestones, monitoring entry, create Requisition, create Tender, editable Plan fields, chart or generic evidence table.

### 11.18 PLN-DES-16 — Return dialogs

Produce three separate dialog artboards over their corresponding dimmed task pages.

**Professional return**

- Title: **Return Plan Version to planner?**
- Intro: **The submitted Version 1 remains unchanged. State the correction required before it is resubmitted.**
- Required multiline label: **Correction required**
- Exact value: **Clarify the delivery sequencing for the digital health infrastructure programme.**
- Footer buttons: **Cancel** and **Return to planner**

**Accounting Officer return**

- Title: **Return Plan Version for correction?**
- Intro: **The professionally reviewed Version 1 remains unchanged. State the correction required.**
- Required multiline label: **Correction required**
- Exact value: **Confirm the planned contract-signing date against the delivery completion date.**
- Footer buttons: **Cancel** and **Return for correction**

**Approval return**

- Title: **Return certified Plan Version for correction?**
- Intro: **The certified Version 1 remains unchanged. State the correction required.**
- Required multiline label: **Correction required**
- Exact value: **Correct the procurement package description before the Plan is resubmitted.**
- Footer buttons: **Cancel** and **Return for correction**

Do not add a reason category, attachment, assignee, due date, optional note or editing controls.

### 11.19 PLN-DES-17 — Common page states

Use the approved KenTender empty, error and unavailable components with these exact variants:

| State | Heading | Text | Control |
|---|---|---|---|
| No authorised context | Procurement Planning is not available | You do not have an active Procurement Planning assignment for a Procuring Entity and Financial Year. | None |
| No departmental plan | No departmental plan yet | Open the departmental plan to review accepted Needs or add a direct requirement. | Open departmental plan |
| No validation tasks | No departmental plans awaiting validation | New submissions will appear here. | None |
| No accepted sources | No accepted departmental entries | Accepted departmental entries will appear here automatically. | None |
| Finance shortfall | Funding is insufficient | The required amount exceeds the current available amount on at least one Budget Line. No reservation has been created. | Return to planner |
| Publication failed | Publication was not acknowledged | The approved Plan is unchanged. Retry the same publication when the destination is available. | Retry publication |
| Load error | Procurement Planning could not be loaded | Try again. If the problem continues, quote the support reference shown below. | Try again |

Only the load-error component may display a generated support reference. Do not add diagnostic text, illustrations or alternative actions.

## 12. Functional interaction requirements — excluded from design prompts

### 12.1 PLN-UI-01 — Procurement Planning workspace

- Resolve contexts only from effective Planning assignments and configured PE/FY Contexts. One eligible context loads directly; several require deliberate selection in the existing global selector; none renders PLN-DES-17.
- The action queue contains only tasks the actor may decide now. Waiting work is neutral read-only information and never exposes disabled protected controls.
- Workspace counts and rows use the same database scope and snapshot.
- Opening the workspace or switching context creates no Planning record.
- A departmental user sees their DPP work, a Validator sees submitted DPP tasks, a Planner sees accepted sources and Plan work, a Budget Officer sees Finance tasks, and each governance actor sees only their exact task.
- Search and counts never disclose another PE, FY, OU, task or Plan.

### 12.2 PLN-UI-02 — Departmental Plan

- **Open departmental plan** calls the explicit guarded command; subsequent reads reuse the one root and Draft Version.
- Project every current accepted Need in the exact PE/FY/OU once. Its five facts remain read-only.
- **Complete** opens PLN-UI-03 for a Need-origin entry. **Add direct requirement** opens PLN-UI-04. **Edit** opens the current direct entry only.
- Draft save permits incomplete funding. Submission requires all entries complete, every current accepted Need covered once, every direct entry valid and at least one entry in total.
- Only direct entries can be removed from a Draft. A current accepted Need cannot be omitted or locally deleted.
- Source successor, withdrawal and Budget Line changes are rechecked on every save and submission.
- Initial HoD submission requires the exact certification checkbox, current assignment/delegation and Open window. A returned correction or source-change successor requires the same certification and authority but may be resubmitted after the initial window closes. The certification text is server supplied, not client composed.
- A successful submission routes to immutable submitted detail. The submitter sees neutral status while the Validator acts.
- A returned submission loads the copied correction Draft and displays each structured issue next to its affected entry.

### 12.3 PLN-UI-03 — Accepted Need funding details

- Load the exact accepted Need version fixed by the DPP entry and display all five source facts read-only.
- Budget Line options come only from `ListEligibleBudgetLines` for the exact PE/FY/OU.
- Selecting a line refreshes its currency and approved line amount for context; it does not display or promise live availability.
- Save accepts only Budget Line and positive indicative amount. Direct URL or payload attempts to alter Need facts are rejected.
- Save creates no reservation, commitment or Budget mutation.
- If the Need version is no longer current, save is blocked and the DPP refresh path is shown.

### 12.4 PLN-UI-04 — Direct requirement editor

- A new direct entry exists only after a successful save command; opening or cancelling the blank editor creates nothing.
- Save accepts exactly title, description, quantity, unit, required-by, Budget Line and indicative amount.
- Unit options come from the active governed unit catalogue; Budget Lines come from the eligible Budget contract.
- Required-by must fall inside the selected FY. Amount and quantity must be positive.
- Save creates no Need, bypass reason, reservation or Strategy link.
- A submitted, accepted or another department's entry is never editable through a direct URL.

### 12.5 PLN-UI-05 — HoD submission

- Recalculate readiness from current authoritative sources when the page loads and again inside the submit transaction.
- Certification is available only to the HoD or a currently effective delegate for the exact OU/FY.
- Submission locks one immutable snapshot and creates one validation task atomically.
- A repeated command with the same idempotency key returns the original submission and task.
- A concurrent source, Budget Line or DPP change returns `PLN_DPP_STALE` and creates no partial submission.

### 12.6 PLN-UI-06 — DPP validation task

- Load the exact immutable DPP submission and all submitted entry details before any decision controls.
- Requirement-type options come from the governed active catalogue. Classification does not edit the submitted source row.
- **Accept departmental plan** requires one classification for every entry, current source versions, no unresolved issue and maker-checker compliance.
- **Return to department** opens a structured issue dialog. At least one issue with affected entry, concise problem and correction required is mandatory.
- Decision commands recheck task token, assignment, state, sources and segregation under one transaction.
- Acceptance completes the task and places every accepted entry in the open Draft Annual Plan as an unallocated source. If this is the first accepted DPP for the PE/FY, the same transaction creates the Annual Plan root and Draft Version 1. It does not form a Plan Item, reserve funds or approve expenditure.
- Return completes the task, preserves the submission and creates the correction Draft atomically.

### 12.7 PLN-UI-07 and PLN-UI-08 — Annual Plan workbench and formation

- There is no **Begin consolidation** command, page or permission gate. The initial Draft Annual Plan already exists after the first DPP acceptance.
- Each later DPP accepted before the initial Plan is submitted adds its entries automatically to the same Draft Version's unallocated-source queue.
- The Planner may form Plan Items incrementally and does not wait for the submission window to close, every department to submit or a department to declare a nil plan.
- A DPP accepted after the current Plan Version has been submitted cannot alter that immutable Version and does not interrupt its governance. Its entries appear as **Pending addition** in the workspace and become available in the next Draft successor after the current Version is activated.
- Source selection lists only current accepted entries in the exact PE/FY that are not already allocated in the open Version.
- One selected source creates one Plan Item without asking for an unnecessary second choice.
- Several selected sources require **one each** or **one combined**. Combined formation requires compatible requirement type, unit and treatment and a complete aggregation reason before the item is ready.
- Formation is atomic and idempotent. A unique active allocation prevents concurrent duplicate use.
- A single created item opens its editor. Several separately created items return to the workbench.
- The Planner never creates a blank source-less Plan Item.
- Draft summary counts, value and blockers are derived from source allocations and current item states.

### 12.8 PLN-UI-09 — Plan Item editor

- Load an existing formed item and every allocation read-only. Source selection, regrouping and partial allocation are absent.
- For a single source, default title from the source. For combined sources, require a Planner-entered package title and aggregation reason.
- Strategic Objective options are only current eligible Active Objectives and show title plus hierarchy path.
- The server assigns Open Tender as the sole admitted MVP method. It is displayed read-only and the UI does not present a one-option selector.
- Save accepts only title, description, Strategic Objective, aggregation reason when combined and seven planned dates.
- Requirement type, quantity, unit, source details, Budget Lines and planned value are derived and read-only.
- Schedule validation binds each failure to the exact date control and explains the chronological or required-by conflict.
- **Save draft** creates no Finance task. **Request Finance confirmation** saves and fully validates in one transaction, then creates/reuses one current task.
- A material change after Finance confirmation marks the evidence Stale and requires a new confirmation. No reservation is silently adjusted.

### 12.9 PLN-UI-10 — Finance task

- Authorise task assignment, PE/FY and Budget scope before returning any protected position.
- Reload every Budget Line position at the command time; the displayed As-at time must match the snapshot.
- **Confirm funding** is available only when every allocation has full availability. The command locks all lines and sources and creates all reservations or none.
- A shortfall omits Confirm, displays the exact deficient source and after-confirmation result, and creates no partial reservation.
- **Return to planner** requires one actionable correction reason and creates no reservation.
- The task contains no editable amount, Budget Line, Plan field or optional note.
- Navigation to Budget & Funding preserves the Planning task and creates no mutation in either module.

### 12.10 PLN-UI-11 to PLN-UI-13 — Plan governance tasks

- Each task loads the exact immutable submitted Plan Version and displays every Plan Item, source summary, Strategic Objective, method, completion date, value and Finance result before decision controls.
- `Professional review` may validate and submit to AO or return to Planner.
- `Accounting Officer certification` may certify and submit to the configured Plan Approval Authority or return for correction.
- `Plan approval` may approve the Annual Procurement Plan or return for correction.
- Every return requires the single actionable correction field in PLN-DES-16; no reason category or optional note exists.
- Every decision rechecks exact assignment, task token, maker-checker chain, source currency, Objective eligibility and Finance freshness.
- A decision completes only its own stage. Professional review is not approval; certification is not approval; approval is not publication or activation.
- A returned Version preserves the submitted snapshot. Only Planner-owned fields reopen in the governed correction state; a new submission repeats Finance when relevant and all later stages.

### 12.11 PLN-UI-14 — Publication

- Load the exact approved Version and configured publication destination. Users cannot change either.
- Publish serialises the approved Plan deterministically and transmits it through the configured adapter.
- Acknowledged response activates the Version in the same transaction and supersedes the predecessor where applicable.
- Failed or indeterminate response preserves approval and permits idempotent retry of the same payload.
- There is no manual acknowledgement, successful-result override or Tender-publication action.

### 12.12 PLN-UI-15 — Active Plan and successor

- Display the Active Version and its complete item baseline read-only.
- Requisition availability is a live neutral projection, not a Planning edit control.
- **Prepare plan update** creates/reuses the sole Draft successor after authority and state checks.
- The Active predecessor remains operational while the successor is Draft, returned or under governance.
- An item may be proposed for whole-item removal only after fresh downstream checks show no drawdown, Tender handoff, commitment or contract.
- An acknowledged successor atomically becomes the sole Active Version; unchanged lineage is preserved and removed items cease future eligibility.
- Planning displays later downstream status only from authoritative projections. It does not collect actual milestone dates.

### 12.13 Common page behaviour and accessibility

- Use semantic headings, labels, tables, status text and keyboard-operable controls. Colour is never the only state carrier.
- Dialog focus is trapped and restored. Validation focus moves to the first invalid control or error summary.
- Buttons are disabled while their command is pending and reuse one idempotency key on retry.
- All dates display in `Africa/Nairobi`; service and audit instants remain UTC.
- Do not wait for `networkidle` on Frappe Desk pages. Browser tests wait for DOM content plus an exact page-ready selector.
- Route changes unmount the Vue app and cancel stale requests. Returning to a cached Desk page re-resolves context and authority.
- Direct links enforce the same scope as list reads and return Not found when existence disclosure is unauthorised.

## 13. Audit and historical integrity

The audit record shall preserve:

- DPP Draft creation, direct-entry changes and accepted-Need projection changes;
- each DPP submission, certification actor/assignment, submitted rows, validation classification and return/accept decision;
- Annual Plan and Version creation, each source allocation and every Planner field change;
- Finance task iterations, Budget snapshots used for decisions and reservation references;
- each professional, AO and approval task and immutable decision;
- publication attempts, adapter results, acknowledgement and activation;
- successor creation, whole-item removal proposal, cancellation and supersession; and
- Requisition drawdown references received from the owning module.

Audit uses framework timestamps and actor fields plus immutable decision records. It does not add editable `created by`, `approved by`, `evidence`, `history note` or `source reference` fields to business forms.

No submitted DPP, accepted classification, submitted Plan snapshot, Finance decision, reservation reference, governance decision, publication attempt, Active Version or Superseded Version may be edited or deleted through product commands.

## 14. Deterministic seed contract

### 14.1 Configuration prerequisites

| Fixture | Exact value |
|---|---|
| Procuring Entity | `PE-MOH` — Ministry of Health |
| Financial Year | `FY-2027-2028` — FY 2027/28 · 1 Jul 2027 to 30 Jun 2028 |
| Context | `CTX-MOH-2027-2028` |
| OU 1 | `OU-MOH-DHI` — Digital Health |
| OU 2 | `OU-MOH-HRMD` — Human Resources Management and Development |
| Unit 1 | `UNIT-PROGRAMME` — Programme |
| Unit 2 | `UNIT-EACH` — Each |
| Unit 3 | `UNIT-SERVICE` — Service |
| Requirement types | Non-consulting services; Consulting services; Goods |
| Procurement method | Open Tender |
| DPP submission window | 1 Oct 2026, 00:00 EAT to 30 Nov 2026, 23:59:59 EAT inclusive |
| Publication destination | KenTender Annual Plan Publication Sandbox · `MOH-APP-SANDBOX-v1` |
| Design clock | Exact time stated on each artboard |

Seeds fail when an authoritative prerequisite is absent or differs. They do not invent a first PE, FY, OU, unit, Budget Line, Objective or assignment.

### 14.2 Actors and assignments

| Actor | Exact assignment |
|---|---|
| `grace.wanjiku@moh.example.test` · Grace Wanjiku | Departmental Plan Preparer for PE-MOH / OU-MOH-DHI and OU-MOH-HRMD / FY 2027/28 |
| `peter.kimani@moh.example.test` · Dr Peter Kimani | Head of User Department for the two named OUs / FY 2027/28 |
| `julia.njeri@moh.example.test` · Julia Njeri | HoD delegate for OU-MOH-DHI from 20 to 30 Nov 2026 |
| `mercy.kilonzo@moh.example.test` · Mercy Kilonzo | DPP Validator and Procurement Planner for PE-MOH / FY 2027/28; distinct capability assignments |
| `moh.budget.officer@example.test` · MOH Budget Officer | Finance confirmation for PE-MOH / FY 2027/28 |
| `samuel.otieno@moh.example.test` · Samuel Otieno | Head of Procurement Function for PE-MOH / FY 2027/28 |
| `amina.hassan@moh.example.test` · Amina Hassan | Accounting Officer for PE-MOH / FY 2027/28 |
| `moh.plan.approver@example.test` · National-government Plan Approver | Configured Plan Approval Authority for PE-MOH / FY 2027/28 |
| `moh.plan.publisher@example.test` · MOH Plan Publisher | Publication Operator for PE-MOH / FY 2027/28 |
| `peter.ouma@audit.example.test` · Peter Ouma | Planning Auditor read for PE-MOH / FY 2027/28 |
| `no.context@example.test` · No-context User | Authenticated with no Planning assignment |

No seed business decision uses Administrator.

### 14.3 Authoritative Strategy and Budget fixtures

| Fixture | Exact value |
|---|---|
| Active Strategic Plan | `STR-MOH-2023-001-V1` — Ministry of Health Strategic Plan (Demo) |
| Active Strategic Objective | `OBJ-MOH-2023-001` — Strengthen interoperable national digital health services |
| Objective path | Digital health systems › Health policy, standards and regulation › Digital health governance |
| Budget Line 1 | `MOH-BL-DHI-2027` — Digital health infrastructure programme · Government of Kenya · KES 100,000,000 |
| Budget Line 2 | `MOH-BL-HWD-2027` — Health workforce development · Government of Kenya · KES 60,000,000 |

Planning seed data references these exact owned records. It does not create a substitute Objective, Budget, Budget Line, funding source or currency.

### 14.4 Integrated accepted Need and DPP baseline

The default integrated lifecycle uses one accepted Need and no direct requirement.

| Field | Exact value |
|---|---|
| Need | `NDS-MOH-2027-0001` · Version `NDS-MOH-2027-0001-V1` |
| Title | National digital health infrastructure upgrade |
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Quantity | 1 programme |
| Required by | 31 Aug 2027 |
| DPP | `DPP-MOH-DHI-2027-001` · Digital Health · Version 1 |
| DPP entry | `DPPE-MOH-DHI-2027-001` · Accepted Departmental Need |
| Planning Budget Line | `MOH-BL-DHI-2027` |
| Planning indicative amount | KES 80,000,000 |
| DPP classification | Non-consulting services |
| DPP submission | `DPPS-MOH-DHI-2027-001-V1` · Dr Peter Kimani · 25 Nov 2026, 10:00 EAT |
| DPP validation | `DPPV-MOH-DHI-2027-001-V1` · Mercy Kilonzo · Accepted · 27 Nov 2026, 14:00 EAT |

The Need fixture contains no Budget Line, amount, funding source, currency, Strategy or classification. Those values first exist in their owning Planning records.

### 14.5 Integrated Annual Plan baseline

| Field | Exact value |
|---|---|
| Annual Plan | `PLN-MOH-2027-001` — Ministry of Health Annual Procurement Plan 2027/28 |
| Plan Version | `PLN-MOH-2027-001-V1` · Version 1 · created automatically from the first accepted DPP at 27 Nov 2026, 14:00 EAT · Active after publication acknowledgement |
| Plan Item | `PPI-MOH-2027-021` — National digital health infrastructure upgrade |
| Description | Procure and implement the national digital health infrastructure upgrade as one integrated FY 2027/28 programme. |
| Source allocation | `PSA-MOH-2027-021-001` · full DPPE-MOH-DHI-2027-001 allocation |
| Requirement type | Non-consulting services |
| Strategic Objective | `OBJ-MOH-2023-001` |
| Procurement method | Open Tender |
| Quantity and value | 1 programme · KES 80,000,000 |

Exact planned dates are:

| Milestone | Date |
|---|---|
| Invitation or advertisement | 1 May 2027 |
| Bid opening | 23 May 2027 |
| Evaluation completion | 23 Jun 2027 |
| Tender award approval | 10 Jul 2027 |
| Notification of award | 14 Jul 2027 |
| Contract signing | 1 Aug 2027 |
| Delivery or implementation completion | 31 Aug 2027 |

### 14.6 Integrated Finance, governance and publication baseline

| Evidence | Exact value |
|---|---|
| Finance task | `FNT-MOH-2027-021-001` |
| Finance decision | `FND-MOH-2027-021-001` · Confirm funding · MOH Budget Officer · 4 Dec 2026, 10:00 EAT |
| Reservation | `RSV-MOH-2027-021-001` · MOH-BL-DHI-2027 · KES 80,000,000 |
| Professional decision | `PVD-MOH-2027-001-V1` · Samuel Otieno · 7 Dec 2026, 10:00 EAT |
| AO certification | `AOC-MOH-2027-001-V1` · Amina Hassan · 8 Dec 2026, 10:00 EAT |
| Plan approval | `APP-MOH-2027-001-V1` · National-government Plan Approver · 9 Dec 2026, 11:00 EAT |
| Publication attempt | `PUB-MOH-2027-001-A1` · MOH Plan Publisher · 10 Dec 2026, 14:55 EAT |
| Acknowledgement | `ACK-MOH-2027-001-A1` · 10 Dec 2026, 15:00 EAT |
| Activation | `PLN-MOH-2027-001-V1` Active at the acknowledgement time |
| Available after reservation | MOH-BL-DHI-2027 · KES 20,000,000 |

At the observation time of 10 Dec 2026, 15:05 EAT, PPI-MOH-2027-021 has remaining eligibility of 1 programme and KES 80,000,000 and no Requisition drawdown.

### 14.7 Isolated direct-requirement fixture

This profile exists for DPP and direct-source tests only. It is not loaded into the default integrated Active Plan.

| Field | Exact value |
|---|---|
| Direct entry | `DPPE-MOH-DHI-2027-DIR-001` |
| Title | Digital health platform security assessment |
| Description | Assess the security of the national digital health platform and provide a prioritised remediation report. |
| Quantity | 1 service |
| Required by | 31 Oct 2027 |
| Budget Line | `MOH-BL-DHI-2027` |
| Indicative amount | KES 20,000,000 |
| Classification | Consulting services |
| Source origin | Direct departmental requirement |
| Need lineage | None |

Profiles shall prove a direct-only DPP, a Need-only DPP and a mixed DPP. No profile creates a synthetic Need or bypass reason.

### 14.8 Isolated combined-source fixture

| Source | Department | Quantity | Budget Line | Amount | Classification |
|---|---|---:|---|---:|---|
| Clinical training laptops for digital health rollout | Human Resources Management and Development | 200 each | MOH-BL-HWD-2027 | KES 48,000,000 | Goods |
| Clinical deployment laptops for digital health rollout | Digital Health | 300 each | MOH-BL-DHI-2027 | KES 72,000,000 | Goods |

The combined item is `PPI-MOH-2027-033`, totals 500 each and KES 120,000,000, and uses the exact title, description and aggregation reason in PLN-DES-09A. It is isolated because its funding requirements exceed the default live baseline.

### 14.9 Seed execution rules

- Upsert by exact stable seed identifiers and produce no duplicate root, Version, entry, allocation, task, decision, reservation or publication attempt.
- Run configuration, Strategy, Budget and Departmental Needs prerequisites before Planning.
- Validate fixtures through the same domain services used by commands.
- Use the named role actor for each lifecycle event, never Administrator.
- Freeze the service clock per profile.
- Keep isolated direct, combined, return, shortfall, stale, successor and publication-failure profiles out of the default integrated baseline.
- Fail loudly on missing prerequisite, ineligible Objective/Budget Line, invalid amount/date, duplicate allocation, authority conflict or inconsistent expected state.
- Seed no removed field, UI-only display value, optional note, source reference, monitoring event or legacy alias.

## 15. Acceptance contract

The module is accepted only when all statements below are demonstrably true.

| ID | Required result |
|---|---|
| PLN-AC-001 | Zero, one and multiple authorised PE/FY context cases fail closed and disclose no unauthorised data. |
| PLN-AC-002 | Workspace reads and direct routes create no record. |
| PLN-AC-003 | One DPP root is created idempotently per PE/FY/OU. |
| PLN-AC-004 | Every current accepted Need appears once with five read-only facts and no Budget, Strategy or classification from Needs. |
| PLN-AC-005 | A direct-only DPP can be created and submitted without any Need. |
| PLN-AC-006 | A mixed DPP retains distinct source origins and creates no synthetic Need. |
| PLN-AC-007 | Direct requirement input is limited to the seven defined values. |
| PLN-AC-008 | Need-origin input is limited to Budget Line and indicative amount. |
| PLN-AC-009 | DPP submission blocks missing accepted Needs, partial quantities, incomplete funding, invalid dates and zero entries. |
| PLN-AC-010 | HoD submission records the exact certification and routes to DPP validation, not the AO. |
| PLN-AC-011 | A DPP return preserves the submitted Version and provides actionable entry-level correction. |
| PLN-AC-012 | DPP acceptance requires one governed classification per entry, creates/reuses the initial Draft Annual Plan and projects every accepted entry without creating a Plan Item. |
| PLN-AC-013 | The Draft Annual Plan has no separate start gate, window-close wait, all-department gate or nil-plan declaration; it lists only current accepted unallocated sources. |
| PLN-AC-014 | Single and separate formation allocate every source once and at full quantity. |
| PLN-AC-015 | Combined formation rejects incompatible sources and requires the defined aggregation reason. |
| PLN-AC-016 | No blank or source-less Plan Item can be created. |
| PLN-AC-017 | Each Plan Item has exactly one eligible Active Strategic Objective and no Value Commitment. |
| PLN-AC-018 | Plan Item input contains no contract period, lotting, recommended method, generic basis or actual milestone field. |
| PLN-AC-019 | Seven planned dates are required, chronological and bounded by source required-by date. |
| PLN-AC-020 | Plan Item value and funding breakdown equal the exact source allocations. |
| PLN-AC-021 | Finance task data is protected before serialization and displays a current As-at position. |
| PLN-AC-022 | Funding confirmation creates all source reservations and one decision atomically, or none on shortfall. |
| PLN-AC-023 | Need acceptance, DPP actions and Plan formation create no reservation. |
| PLN-AC-024 | A material item/source/funding change makes prior Finance evidence Stale. |
| PLN-AC-025 | Professional, AO and approval tasks each show the complete immutable Plan before decisions. |
| PLN-AC-026 | The Planner cannot professionally validate their own submitted Version. |
| PLN-AC-027 | Each governance stage performs only its named decision and cannot skip the next stage. |
| PLN-AC-028 | Every return requires one actionable correction and preserves the submitted snapshot. |
| PLN-AC-029 | Approval creates no publication attempt and does not activate the Plan. |
| PLN-AC-030 | Publication transmits the exact approved payload and activates only on acknowledgement. |
| PLN-AC-031 | Failed/indeterminate publication can retry the same payload without a new approval. |
| PLN-AC-032 | Exactly one Plan Version is Active and one successor may be open. |
| PLN-AC-033 | Active predecessor eligibility remains unchanged until successor acknowledgement. |
| PLN-AC-034 | Requisition eligibility exposes exact remaining quantity/value and creates no Requisition. |
| PLN-AC-035 | Active item removal is blocked by drawdown, Tender handoff, commitment or contract. |
| PLN-AC-036 | Planning has no actual-milestone entry, Monitoring Officer action or custom support workspace. |
| PLN-AC-037 | All counts, queues, details and actions use the same PE/FY/OU and task predicates. |
| PLN-AC-038 | Same idempotency key returns the original result; concurrent different commands yield one winner and one stale result. |
| PLN-AC-039 | Cross-PE, cross-FY and out-of-scope direct URLs disclose no record existence. |
| PLN-AC-040 | Seed reset and rerun produce the exact baseline without duplicates or semantic drift. |

### 15.1 Minimum automated coverage

1. Domain tests for DPP coverage, direct-entry fields, source immutability, classification, formation compatibility, schedule, Objective eligibility and lifecycle transitions.
2. Permission tests for every role, PE/FY/OU boundary, task assignment, delegation window and maker-checker rule.
3. Contract tests for Needs events, Strategy Objective selection, Budget Line eligibility, all-source reservation, publication adapter and Requisition eligibility.
4. Transaction tests for submission, formation, Finance, governance, publication acknowledgement and concurrent retries.
5. Vue component tests for exact fields, absent fields, task detail, errors, dialog copy and action visibility.
6. Focused Playwright journeys for direct-only DPP, accepted-Need DPP, mixed DPP, integrated Active Plan, Finance shortfall, governance return and publication retry.

## 16. Implementation and test constraints

### 16.1 Frappe and Vue implementation

- Retain one Frappe app/module boundary for Procurement Planning and conventional DocType ownership.
- Use standard naming, permissions, link fields, child tables, background jobs, transactions and framework audit fields.
- Enforce every important rule in Python domain services; Vue state and client controls are never the authority.
- Mount Vue 3 SFCs into real `frappe.ui.make_app_page()` Desk pages through the bench build pipeline already proven by the Strategy pilot.
- Port Claude Design tokens into the existing KenTender token chain. Do not ship `.dc.html`, design runtime, vendor state logic, CDN assets or utility-class output.
- Use scoped component styles and existing shared KenTender components before adding a new component.
- Unmount Vue and detach listeners on Desk route change.
- Self-host any approved fonts through the application asset pipeline; no CDN dependency.
- Keep the Frappe header, breadcrumb, global selector and navigation outside the Vue artboard.
- Prefer server-computed projections tailored to each screen over client joins across DocTypes.

### 16.2 TDD and efficient verification

Work in the smallest proving loop:

1. write or identify the focused failing test for the rule being changed;
2. run that exact test or smallest file;
3. implement the minimum coherent change;
4. rerun the focused test;
5. run the immediately related module slice;
6. run broader Planning and cross-module regression only at a checkpoint; and
7. run the full suite once before handoff, not after every small fix.

Required test tiers are:

| Tier | When | Expected scope |
|---|---|---|
| 1 — focused | Every code change | One named domain/component test or one scenario |
| 2 — feature slice | Focused test passes | Direct DPP, DPP review, Plan Item, Finance or governance slice |
| 3 — module regression | A coherent slice is complete | Procurement Planning server and UI tests |
| 4 — integration checkpoint | Cross-module contract changes | Planning plus the affected Needs, Strategy or Budget contract tests |
| 5 — release | Before handoff | Full suite, build and selected browser acceptance journeys |

Do not rerun hundreds of unrelated tests while one focused failure is being diagnosed. Record the first failing assertion, inspect its owning layer and fix the cause before broad reruns. Browser tests use deterministic fixtures, stable `data-testid` selectors and explicit page-ready elements; they do not use arbitrary sleeps or `networkidle`.

### 16.3 Required release evidence

- schema and removed-field audit;
- focused and module test report;
- cross-module contract test report;
- successful application build;
- seed reset/idempotency report;
- screenshots for PLN-DES-01 through PLN-DES-17 at 1440 × 1024;
- scripted click-through of direct-only DPP, accepted-Need DPP and integrated Active Plan;
- zero page-specific console errors and failed network requests; and
- confirmation that no design-runtime or removed field remains in production code.

## 17. Prohibited shortcuts

Implementation shall not:

- make Departmental Needs a prerequisite for a DPP entry;
- create a synthetic Need or collect a bypass reason for a direct requirement;
- copy Need business justification into Planning;
- source Strategy, requirement type, Budget Line or amount from Departmental Needs;
- let Planning edit accepted Need facts;
- add a field because it appeared in an old document or visual;
- add Value Commitment, source reference, generic evidence, optional note, attachment, contract period, lotting or actual milestone fields;
- create an Annual Plan or task from a page read;
- create a source-less Plan Item or partially allocate a DPP entry;
- accept a client-computed value, permission, state, balance or approval route as authoritative;
- reserve only part of a combined item;
- hide full Plan details from a reviewer, AO or approver;
- merge professional review, AO certification and Plan approval into one generic approval;
- activate on approval or on an unacknowledged publication attempt;
- expose create-Requisition or create-Tender actions from Planning;
- import Claude Design runtime, `.dc.html`, Tailwind utilities or copied vendor markup into production;
- draw or replace the Frappe breadcrumb/header/global selector inside the page;
- maintain old routes, aliases, duplicate fields or compatibility reads; or
- use a full-suite test run as the first diagnostic step for a focused defect.

## 18. Traceability and precedence

This document incorporates the approved boundary decisions from:

- CFG-CHG-002 v0.3 — PE/FY context and configuration ownership;
- STR-CHG-001 v1.3 — exactly one Active Strategic Objective on each Plan Item and no Value Commitment;
- BUD-CHG-001 v1.1 — Planning-owned Finance task, Budget-owned live position and reservations; and
- NDS-CHG-001 v1.0 — optional consultation, direct departmental planning path, six Need values and Planning-owned DPP funding specification.

On approval, this document supersedes conflicting Planning requirements in:

- PLN-CAN-001 v0.1;
- PLN-CDR-001 v0.1;
- PLN-FR-001 v0.1;
- PLN-STC-001 v0.1;
- PLN-SDC-001 v0.1;
- PLN-GF-001 v0.1/v0.2;
- PLN-GF-002 v0.2;
- PLN-GF-003 v0.1/v0.2; and
- the Procurement Planning Revision Ledger.

Earlier UI assets remain evidence for reuse only. Where their fields, states, labels, source ownership or actions differ from this document, this document controls.

## 19. Approval effect

Approval of PLN-CHG-001 v1.0 authorises implementation of the clean Procurement Planning module and conversion of section 11 into Claude Design artboards. It does not approve generated visual deviations, production publication configuration, a Procurement Requisition, a Tender or any field not defined here.

After approval, implementation starts with the data-purpose and removed-field audit, then the two missing DPP editors, the Plan Item Strategic Objective correction, complete governance-task detail, and retirement of monitoring/support surfaces. Existing conforming Planning UI is reused throughout.
