# REQ-CHG-001 — Clean Procurement Requisitions

| Control | Value |
|---|---|
| Document ID | REQ-CHG-001 |
| Version | 1.0 |
| Date | 24 August 2026 |
| Status | Approved |
| Approval | Product owner · 24 August 2026 |
| Module | Procurement Requisitions |
| Implementation posture | New clean module; reuse the proven Claude Design → Vue 3 → Frappe Desk pattern and existing KenTender components |

**Controlling decision:** A Procurement Requisition is the formal departmental initiation of procurement against one eligible Active Plan Item. It inherits Planning, Strategy and funding context; it does not recreate them. The department supplies only the exact quantity and value now requested, the expected delivery date and the applicable technical documents. The Head of User Department submits the Requisition to the Head of Procurement Function, who either authorises it for Tender Preparation or returns it for a specific correction. Authorisation atomically consumes the approved Plan Item availability and publishes an immutable Tender Preparation handoff. It does not create, configure or advertise a Tender.

## 1. Governing decision

This document is the single implementation authority for Procurement Requisitions MVP-1. There is no earlier Requisition module specification to preserve or migrate.

The module is implemented as a clean domain. It may reuse approved KenTender visual components, page structure, context controls and the proven Frappe/Vue mounting pattern. It shall not copy Planning forms, invent a generic approval workflow or import a design-tool runtime.

Completion requires one coherent result across schema, services, permissions, screens, fixtures and tests. A field, action, object, service, queue or screen not defined here is outside the module.

### 1.1 Conflict and disposition register

| Candidate or inherited idea | Disposition in v1.0 |
|---|---|
| Blank Requisition unrelated to an approved Plan Item | Remove. Every Requisition starts from one eligible Active Plan Item. |
| Re-enter title, description, requirement type, Strategic Objective, procurement method, Budget Line or funding source | Remove. These are inherited read-only from the exact Active Plan Item and its source allocations. |
| Requisition may contain several unrelated Plan Items | Remove. One Requisition references one Plan Item. Tender Preparation may later group authorised Requisitions only through its own governed rules. |
| Accepted Departmental Need as the Requisition source | Remove. The source is the Active Plan Item. Need and DPP lineage remains readable through Planning. |
| Lead User Department for a cross-department combined Plan Item | Remove. Each contributing department raises its own Requisition against its own Plan source allocation or allocations. |
| One HoD signs for other departments | Prohibit. Each HoD initiates only the Requisition for their department's allocation. |
| Multiple HoD signatures on one Requisition | Remove. Use separate departmental Requisitions linked to the same combined Plan Item. |
| New Budget Officer or Finance approval | Remove. Planning already confirmed and reserved funding. Requisition authorisation rechecks current Planning eligibility and consumes the approved availability; it does not repeat Finance confirmation. |
| Accounting Officer Requisition approval | Remove. No distinct MVP-1 Requisition decision is assigned to the Accounting Officer. |
| Planner approval of a Requisition | Remove. The Planner owns the Plan, not departmental initiation. |
| Free-text procurement description or business justification | Remove. The Plan Item description and approved lineage are authoritative. |
| Priority, urgency, requested-by person, contact, delivery location, source reference, authority reference, generic evidence or generic note | Remove. No approved current Requisition decision or downstream contract consumes them. |
| Market-estimate narrative or unit-price breakdown | Remove. The requested value is required; no separate narrative or cost decomposition has a defined MVP-1 system effect. |
| One generic attachment bucket | Replace with typed technical documents that have a named Procurement review and Tender Preparation consumer. |
| Optional documents displayed as mandatory blank controls | Remove. Show required document types and uploaded applicable documents only. |
| Requisition save immediately reduces Plan availability | Remove. Drafting and HoD preparation create no drawdown. The drawdown is committed atomically only when the Head of Procurement Function authorises the Requisition. |
| Authorisation automatically advertises or opens a Tender | Remove. It publishes a Tender Preparation handoff only. |
| User clicks a second **Create Tender** action after authorisation | Remove from Requisitions. Tender Preparation consumes the authorised handoff through its own module. |
| Requisition-owned Tender status, evaluation, award or contract fields | Remove. Requisition displays only a neutral downstream handoff projection. |
| Legacy Purchase Request, Material Request or Demand compatibility | Prohibited. No aliases, dual writes, migrated fixtures or fallback routes. |

## 2. Purpose and outcomes

Procurement Requisitions shall provide:

- a role-scoped list of Active Plan Item allocations a department may initiate;
- explicit creation from one eligible Plan Item and one requesting department;
- exact inherited Planning, Strategy and funding context without re-entry;
- full or partial drawdown of the department's remaining Plan allocation;
- one reasonable expected delivery date;
- a small, typed technical-document package appropriate to the requirement type;
- preparation by an authorised departmental user where needed;
- formal initiation by the effective Head of User Department;
- one complete Procurement Function review of the submitted Requisition;
- atomic Plan quantity/value drawdown on authorisation;
- an immutable Tender Preparation handoff; and
- correction, withdrawal and pre-handoff revocation paths that preserve evidence and release availability correctly.

### 2.1 Scope exclusions

The module shall not contain:

- Need creation, Need review, DPP preparation or Plan Item formation;
- Strategy, Budget or Budget Line maintenance;
- procurement-method selection, aggregation, lotting or schedule planning;
- a second Finance confirmation or Budget reservation;
- Tender shell creation, STD selection, wizard configuration, invitation, bid submission, evaluation, award or contract work;
- a supplier, bidder, committee, evaluator or contract manager;
- business justification, priority, urgency, project narrative, market-survey narrative, unit price, tax or cost breakdown;
- contact, requested-by person, delivery location, source reference, authority reference, generic evidence, generic note or optional comments;
- a manual reference, editable technical identifier, hash, audit actor or timestamp;
- a lead-department field for combined Plan Items;
- a dashboard chart, score, completion percentage or performance card;
- a custom Frappe shell, header, breadcrumb, PE/FY selector or navigation system; or
- legacy Material Request, Purchase Request, Demand or ERP workflow compatibility.

### 2.2 Data-purpose gate

No stored field is permitted unless all three conditions are documented before implementation:

1. a current operational decision or output uses it;
2. the consuming screen, rule or service is named; and
3. its validation and system effect are defined.

“Useful later”, “normally captured”, “for reporting”, “for audit” and “the design showed it” are not sufficient reasons.

The user-supplied Requisition values pass this gate:

| Value | Current consumer and effect |
|---|---|
| Requested quantity per Plan source allocation | Defines the quantity being initiated and reduces the exact remaining Plan allocation on authorisation. |
| Requested value per Plan source allocation | Defines the value being initiated and reduces the exact remaining Plan allocation on authorisation. |
| Expected delivery date | Gives Procurement and Tender Preparation the departmental delivery requirement and must fit the approved Plan schedule. |
| Technical document type and file | Gives the HoD, Procurement reviewer and Tender Preparation the technical requirement package. |
| Return correction | Tells the departmental preparer exactly what must change before resubmission. |
| Withdrawal reason | Explains why an already initiated Requisition is stopped and supports release of its pending route. It exists only after HoD submission. |
| Revocation reason | Explains why Procurement withdraws an authorisation before Tender Preparation consumes it. It exists only on that command. |

No other user-entered value is admitted.

## 3. Fixed external constraints

The minimum initiation controls are narrow:

- procurement is initiated through a Requisition against the approved procurement plan by the Head of User Department and submitted to the Head of Procurement Function; and
- the Requisition is accompanied, as applicable, by technical documents and a reasonable expected delivery date.

These controls are implemented without a second Planning or Finance workflow. Source: [Public Procurement and Asset Disposal Regulations, regulation 71](https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng%402022-12-31).

The approved product boundary remains: an authorised Requisition permits Tender Preparation to begin; it is not a Tender, invitation or procurement award.

## 4. Ownership and dependency boundary

- Configuration & Governance owns PE, organisation units, FY, timezone, unit and requirement-type catalogues, capability assignments and delegations.
- Procurement Planning owns the Active Plan, Plan Versions, Plan Items, source allocations, funding-confirmation lineage, remaining quantity/value and Requisition drawdown ledger.
- Strategy Alignment and Budget & Funding remain authoritative through the Planning lineage. Requisitions do not query or copy their editable records.
- Procurement Requisitions owns Requisition identity, versions, technical documents, HoD and Procurement tasks, decisions and the authorised handoff.
- Tender Preparation owns Tender identity, Tender shell, STD binding, wizard configuration and every later Tender action.

| Information or decision | Owner | Requisition treatment |
|---|---|---|
| PE/FY/OU and effective authority | Configuration & Governance | Resolve exact scope and fail closed. |
| Plan Item title, description, type, method, schedule and Objective | Procurement Planning | Display exact Active-version values read-only. |
| Plan source department, quantity, value, Budget Line and remaining balance | Procurement Planning | Select only allocations belonging to the requesting OU; draw down atomically on authorisation. |
| Funding reservation and live funding state | Budget & Funding through Planning | Display confirmation state; create no new reservation or Finance task. |
| Requested drawdown and expected delivery | Procurement Requisitions | Capture, validate and submit. |
| Technical requirements | User department / Procurement Requisitions | Attach typed immutable files for review and Tender Preparation. |
| Formal initiation | Head of User Department | Submit the exact immutable Requisition Version. |
| Authorisation for Tender Preparation | Head of Procurement Function | Authorise or return the exact submitted Version. |
| Tender Preparation readiness and handoff | Procurement Requisitions | Publish immutable authorised snapshot; create no Tender. |
| Tender shell and procurement procedure | Tender Preparation | Consume one or more authorised Requisitions under its own rules. |

Permitted dependency paths are:

**Configuration & Governance → Procurement Planning → Procurement Requisitions → Tender Preparation**

**Strategy Alignment / Budget & Funding → Procurement Planning lineage → Procurement Requisitions read-only context**

Requisitions shall use explicit Planning service contracts. It shall not edit Planning tables directly or import another module's controller.

## 5. Canonical domain model

All references are server-generated. Frappe framework audit fields remain framework-managed and are not duplicated as user data.

### 5.1 ProcurementRequisition

Stable identity for one department's initiation against one Active Plan Item.

| Field | Operational purpose and system effect |
|---|---|
| `requisition_id` | Immutable internal identity. |
| `requisition_reference` | Generated as `REQ-{PE code}-{FY start}-{OU code}-{4 digits}` and used in routes, tasks and handoff. |
| `pe_fy_context_id` | Fixes PE/FY authority and lineage. Required and immutable. |
| `requesting_org_unit_id` | Derived from the selected Plan source allocations and fixes the HoD scope. Required and immutable. |
| `plan_id` / `plan_version_id` / `plan_item_id` | Fix the Active Planning baseline from which the Requisition is drawn. Required and immutable. |
| `current_state` | Derived root display state: `Draft`, `Awaiting HoD`, `Submitted to Procurement`, `Returned`, `Authorised for Tender Preparation`, `Withdrawn` or `Authorisation revoked`. |
| `current_version_id` | Points to the current Draft, task or authorised Version. |
| `authorised_version_id` | Points to the immutable authorised Version. Empty until authorisation. |
| `planning_drawdown_reference` | Planning-owned drawdown created on authorisation. Empty beforehand. |
| `record_version` | Monotonic optimistic-concurrency token checked by every write. |

Only one open Requisition may exist for the same `plan_item_id + requesting_org_unit_id`. After it is authorised or withdrawn, another Requisition may be prepared only against positive remaining Planning availability.

### 5.2 RequisitionVersion

One immutable decision snapshot or its mutable Draft predecessor.

| Field | Operational purpose and system effect |
|---|---|
| `requisition_version_id` | Immutable version reference used by tasks, decisions and handoff. |
| `requisition_id` | Links the Version to its stable root. |
| `version_number` | Generated sequence within the Requisition. |
| `based_on_version_id` | Identifies the returned Version copied for correction. Empty for Version 1. |
| `version_status` | `Draft`, `Awaiting HoD`, `Submitted`, `Returned`, `Authorised`, `Withdrawn`, `Revoked` or `Superseded`. |
| `expected_delivery_date` | Departmental delivery requirement inherited initially from the Plan completion date; required for HoD submission. |

Draft content is mutable only through the allow-list in this document. **Send to HoD** locks the Version. A return preserves the viewed snapshot and creates a copied Draft successor.

### 5.3 RequisitionDrawdownLine

One requested drawdown from one eligible Plan source allocation owned by the requesting department.

| Field | Operational purpose and system effect |
|---|---|
| `drawdown_line_id` | Immutable child-row identity. |
| `requisition_version_id` | Fixes the containing Version. |
| `plan_source_allocation_id` | Fixes the exact Planning allocation. Required and immutable. |
| `requested_quantity` | Quantity initiated from that allocation; greater than zero and not above its live remaining quantity. |
| `unit_id` | Inherited from Planning and read-only. |
| `requested_value_minor_units` | Value initiated from that allocation; greater than zero and not above its live remaining value. |
| `currency` | Inherited from the Planning/Budget lineage and read-only. |

The Requisition total quantity and value are derived from its lines. A single-source Plan Item has one line. A combined Plan Item may expose several lines only when they belong to the same requesting department; another department prepares a separate Requisition.

### 5.4 RequisitionTechnicalDocument

| Field | Operational purpose and system effect |
|---|---|
| `technical_document_id` | Immutable document-row identity. |
| `requisition_version_id` | Fixes the Version whose submission includes the file. |
| `document_type` | One governed type from section 5.5. Required. |
| `file_id` | Links the immutable Frappe File stored for review and handoff. Required. |
| `file_name` | Framework-derived display value. Read-only. |

There is no document title, description, note, reference, issuer, date or contact field. Replacement in a Draft creates a new File reference; a submitted file is never overwritten.

### 5.5 Technical-document rules

| Requirement type | Minimum document before HoD submission | Additional admitted document types when applicable |
|---|---|---|
| Goods | Technical Specifications | Technical Drawing; Feasibility or Survey Report; Environmental and Social Impact Assessment |
| Works | Technical Specifications and Bill of Quantities | Technical Drawing; Feasibility or Survey Report; Environmental and Social Impact Assessment |
| Consulting services | Terms of Reference | Feasibility or Survey Report |
| Non-consulting services | Statement of Requirements | Technical Drawing; Feasibility or Survey Report; Environmental and Social Impact Assessment |

Only the seven named document types are admitted. The module does not ask an applicability questionnaire or display empty optional upload controls. The user adds an admitted additional document only when it exists.

### 5.6 RequisitionTask

One protected decision task for one immutable Requisition Version.

| Field | Operational purpose and system effect |
|---|---|
| `requisition_task_id` | Immutable route and decision reference. |
| `requisition_version_id` | Fixes the exact Version under decision. |
| `task_type` | `HoD initiation` or `Procurement authorisation`. |
| `pe_fy_context_id` / `org_unit_id` | Fix the exact assignment scope. |
| `status` | `Open`, `Completed` or `Cancelled`. |
| `decision_token` | Prevents concurrent decisions on the same task. |

The HoD task is addressed to the effective HoD capability for the requesting OU. The Procurement task is addressed to the effective Head of Procurement Function capability for the PE/FY. There is no claim, release, priority, due date, score or generic task note.

### 5.7 RequisitionDecision

Immutable record created only by a successful command. It contains decision ID, Requisition and Version IDs, action, actor, effective assignment, timestamp, prior/resulting state and command correlation.

Permitted actions are:

- `Send to HoD`;
- `Submit to Procurement Function`;
- `Return to preparer`;
- `Authorise for Tender Preparation`;
- `Return to department`;
- `Withdraw initiated Requisition`; and
- `Revoke authorisation before Tender handoff`.

A reason exists only for return, post-submission withdrawal and revocation. There is no optional decision note.

### 5.8 AuthorisedRequisitionHandoff

Immutable snapshot published after successful Procurement authorisation and Planning drawdown.

It contains only:

- event identity and authorised time;
- Requisition, Version, PE/FY and requesting OU identities;
- Active Plan, Plan Version and Plan Item lineage;
- exact source-allocation drawdown lines;
- inherited Plan Item title, description, requirement type, procurement method, Strategic Objective and planned schedule;
- expected delivery date;
- Planning drawdown and Budget reservation lineage;
- immutable technical-document references; and
- authorising Head of Procurement Function decision.

It contains no Tender number, STD, procurement wizard answers, supplier, committee, evaluation, award or contract data.

### 5.9 TenderPreparationProjection

Read-only projection supplied by Tender Preparation:

| Field | Purpose |
|---|---|
| `requisition_id` / `authorised_version_id` | Fix the Requisition consumed by the projection. |
| `handoff_status` | `Ready for Tender Preparation` or `Tender Preparation started`. |
| `tender_reference` | Supports **View Tender Preparation** after a Tender shell exists. Empty beforehand. |
| `consumed_at` | Shows when Tender Preparation accepted the handoff. Empty beforehand. |

This projection is not Requisition lifecycle state and cannot be edited in Requisitions.

## 6. Lifecycle and business rules

### 6.1 Initial lifecycle

| Current state | Command | Result | Actor |
|---|---|---|---|
| Eligible Active Plan allocation | Prepare Requisition | Requisition root and Draft Version 1 | Requisition Preparer or HoD |
| Draft | Save Draft | Allowed values and documents saved | Draft preparer or HoD |
| Draft / Returned with no prior HoD submission | Cancel draft | Requisition Withdrawn; no reason and no Planning effect | Draft preparer or HoD |
| Draft prepared by non-HoD | Send to HoD | Immutable Version; Open HoD task | Requisition Preparer |
| Draft prepared by HoD | Submit to Procurement Function | Immutable Version; Open Procurement task | HoD |
| Awaiting HoD | Submit to Procurement Function | Same immutable Version submitted; Procurement task replaces HoD task | HoD or effective delegate |
| Awaiting HoD | Return to preparer | Viewed Version Returned; copied Draft successor | HoD or effective delegate |
| Submitted to Procurement | Authorise for Tender Preparation | Planning drawdown and decision committed atomically; handoff published | Head of Procurement Function |
| Submitted to Procurement | Return to department | Viewed Version Returned; copied Draft successor | Head of Procurement Function |
| Returned | Save / Send to HoD | Corrected Draft saved or routed through HoD again | Preparer or HoD |
| Submitted to Procurement / correction after Procurement return | Withdraw initiated Requisition | Requisition Withdrawn; open tasks cancelled; no drawdown | HoD or effective delegate |
| Authorised; handoff not consumed | Revoke authorisation | Root becomes Authorisation revoked; exact Planning drawdown reversed; authorised content remains historical under a Revoked status | Head of Procurement Function |

Opening a workspace, Plan Item or editor creates nothing. The explicit **Prepare Requisition** command creates/reuses the one open Requisition for the Plan Item and OU.

### 6.2 Cross-department combined Plan Item

- Planning source allocations retain the owning organisation unit.
- A department sees and may requisition only its own allocations.
- One Requisition may cover all source allocations in the same Plan Item belonging to that department.
- Another contributing department prepares a separate Requisition with the same Plan Item reference.
- Requisitions do not select a lead department, request another HoD's signature or combine departmental initiation decisions.
- Tender Preparation may later group authorised Requisitions sharing the Plan Item. That grouping is not a Requisition action or state.

### 6.3 Invariants

1. Every Requisition references one Active Plan Item and one requesting OU.
2. Reads never create a Requisition, Version, task, decision, drawdown or handoff.
3. Only source allocations owned by the requesting OU may appear in its Requisition.
4. One open Requisition exists per Plan Item and requesting OU.
5. Requested quantity and value are positive and do not exceed live remaining Planning availability.
6. Expected delivery is after the planned contract-signing date and no later than the approved Plan completion date.
7. The minimum technical-document set is complete before HoD submission.
8. Planning, Strategy, Budget and DPP facts are immutable in Requisitions.
9. A non-HoD preparer cannot formally initiate procurement.
10. The HoD cannot authorise the Procurement Function decision.
11. The Head of Procurement Function views the complete immutable Requisition before deciding.
12. Draft, HoD submission and return create no Planning drawdown or new Budget reservation.
13. Authorisation locks and rechecks Planning availability and creates the complete drawdown or no decision.
14. No partial line drawdown is committed when any line fails.
15. An authorised Version and technical files are immutable.
16. Revocation is permitted only before Tender Preparation consumes the handoff and reverses the exact drawdown atomically.
17. Requisition authorisation does not create or advertise a Tender.
18. Cross-department combined Plan Items use separate OU Requisitions; no actor signs for another OU.
19. Unauthorised lists, counts, details and routes disclose no record existence.

## 7. Roles and permissions

| Capability | Exact scope and permitted work |
|---|---|
| Requisition Preparer | One PE/FY/OU; view eligible Plan allocations, prepare/save Drafts, attach technical documents and send a complete Draft to the HoD. Cannot submit to Procurement or authorise. |
| Head of User Department | One PE/FY/OU; prepare directly, review a prepared Version, submit it to Procurement, return it to the preparer or withdraw an initiated Requisition. |
| HoD Delegate | Exact effective delegated PE/FY/OU initiation scope; same decision only within the delegation period. |
| Head of Procurement Function | One PE/FY; review the complete submitted Requisition, authorise it for Tender Preparation, return it or revoke before handoff consumption. Cannot alter departmental content. |
| Procurement Planner | Authorised neutral read of Planning lineage and Requisition drawdown only. No Requisition decision. |
| Planning/Budget Viewer | Authorised neutral read of their owned projections only. No Requisition decision. |
| Requisition Auditor | Scoped immutable Requisition and decision read only. |

Administrator, System Manager or a role label alone grants no business capability. Every capability is evaluated against the exact PE/FY/OU, record state, assignment or task.

## 8. Cross-module integration contracts

### 8.1 Planning eligibility and drawdown

`GetRequisitionEligibility` supplies the exact Active Plan/Version/Item, requesting OU source allocations, approved and remaining quantity/value, unit, Budget Line/reservation lineage, funding state, Plan schedule and evaluation time.

`AuthoriseRequisitionDrawdown` is invoked only inside the Head of Procurement Function authorisation transaction. It locks and reloads the Plan Item, all requested source allocations and current drawdowns; accepts every line or none; records the authoritative Requisition drawdown; and returns the immutable Planning reference.

Drafting, HoD review, submission and Procurement return do not consume availability. A second Requisition cannot be opened for the same Plan Item/OU while one is open. After authorisation, another may be prepared only from positive remaining availability.

`ReverseRequisitionDrawdown` is permitted only for an authorised Requisition whose Tender handoff has not been consumed. It restores the exact source quantities and values and preserves both the original drawdown and reversal evidence.

### 8.2 Budget and Strategy lineage

Requisitions display Budget Line, funding source, currency, reservation status, Strategic Objective and Objective path only from the Active Plan Item projection. They store their immutable authorised snapshot for handoff but do not offer selectors or direct writes to Strategy or Budget.

No Budget Officer task, Finance confirmation, new reservation or Strategy decision is created.

### 8.3 Tender Preparation handoff

Successful authorisation publishes `ProcurementRequisitionAuthorised.v1` through a transactional outbox. Delivery is idempotent and ordered per Requisition.

Tender Preparation may consume one or more authorised Requisitions. If it groups several Requisitions, they must share a compatible Plan Item/package context under the Tender module's rules. Requisitions does not pre-create or name the Tender.

`ProcurementRequisitionAuthorisationRevoked.v1` may be published only before Tender Preparation records consumption. A consumed handoff cannot be revoked from Requisitions.

## 9. Service and command contracts

### 9.1 Read contracts

| Contract | Required result |
|---|---|
| `ResolveRequisitionContexts` | Zero, one or several authorised PE/FY/OU contexts; no inferred first record. |
| `GetRequisitionWorkspace` | Reconciled eligible Plan allocations, actor-owned Drafts, exact tasks and neutral waiting records. |
| `ListEligiblePlanAllocations` | Only current Active Plan Item allocations owned by the selected OU with positive remaining availability. |
| `GetRequisition` | Current Version, immutable lineage, drawdown lines, documents, decisions, handoff projection and permitted commands. |
| `GetHoDInitiationTask` | Exact immutable Version and all information needed for departmental initiation. |
| `GetProcurementAuthorisationTask` | Exact immutable Version, live Planning eligibility and all information needed for authorisation. |

### 9.2 Commands

| Command | Core effect |
|---|---|
| `PrepareRequisition` | Create/reuse one Draft for the selected Active Plan Item and requesting OU; prefill remaining allocation lines and planned delivery completion. |
| `SaveRequisitionDraft` | Save only requested line quantities/values, expected delivery date and typed documents. |
| `RemoveTechnicalDocument` | Remove an uploaded file only from the current Draft. |
| `CancelRequisitionDraft` | Withdraw an unsubmitted Draft that has no earlier HoD submission; create no reason, task or Planning effect. |
| `SendRequisitionToHoD` | Validate completeness, lock the Version and create one HoD task. |
| `SubmitRequisitionToProcurement` | Validate HoD authority and current completeness; lock or reuse the exact Version and create one Procurement task. |
| `ReturnRequisition` | Record one required correction, preserve the decided Version and create a copied Draft successor. |
| `AuthoriseRequisition` | Revalidate task/authority/content, atomically commit all Planning drawdown lines, record authorisation and publish the handoff. |
| `WithdrawInitiatedRequisition` | Require a specific reason, cancel open tasks and withdraw without a drawdown. |
| `RevokeRequisitionAuthorisation` | Require Procurement authority/reason and unconsumed handoff; reverse the exact Planning drawdown and publish revocation. |

All mutations require an expected record version and idempotency key. Authority, scope, source eligibility, state and live availability are repeated inside the transaction.

## 10. Error contract

| Code | Plain-language result |
|---|---|
| `REQ_NO_CONTEXT` | You do not have access to a Procurement Requisitions context. |
| `REQ_PLAN_ITEM_INELIGIBLE` | This Plan Item is not currently available for a Requisition. |
| `REQ_NO_REMAINING_AVAILABILITY` | This department has no remaining quantity or value available on the Plan Item. |
| `REQ_OPEN_EXISTS` | This department already has an open Requisition for the Plan Item. |
| `REQ_LINE_INVALID` | Correct the highlighted requested quantity or value. |
| `REQ_DELIVERY_DATE_INVALID` | Select a delivery date within the approved Plan Item schedule. |
| `REQ_DOCUMENT_MISSING` | Add the required technical document before sending the Requisition. |
| `REQ_DOCUMENT_TYPE_INVALID` | Select an admitted document type for this requirement. |
| `REQ_HOD_REQUIRED` | Only the effective Head of User Department or delegate may submit this Requisition. |
| `REQ_AVAILABILITY_CHANGED` | Plan Item availability changed. Reload and review the current remaining quantity and value. |
| `REQ_SEGREGATION_CONFLICT` | You cannot make this decision because you performed an incompatible earlier action. |
| `REQ_TASK_STALE` | This task has already changed. Reload to see the current result. |
| `REQ_HANDOFF_CONSUMED` | Tender Preparation has already consumed this Requisition; authorisation cannot be revoked here. |
| `REQ_STALE_WRITE` | Another user changed this Requisition. Reload before continuing. |

Unauthorised detail or task reads return the same not-found result as a nonexistent record. Diagnostics are logged with a support correlation and are not exposed as business fields.

## 11. UI architecture, menu and routes

Procurement Requisitions is a top-level KenTender workspace named **Procurement Requisitions**, placed after **Procurement Planning** and before **Tender Preparation**.

| Surface | Canonical Frappe Desk route | Primary capability |
|---|---|---|
| Requisitions workspace | `/app/procurement-requisitions` | All authorised Requisition users |
| Requisition detail/editor | `/app/procurement-requisition/{requisition_reference}` | Requesting department and authorised neutral readers |
| HoD initiation task | `/app/procurement-requisitions/hod/{task_id}` | Exact HoD/delegate scope |
| Procurement authorisation task | `/app/procurement-requisitions/review/{task_id}` | Head of Procurement Function |

The workspace is role-sensitive. A preparer sees eligible Plan allocations and their Drafts; a HoD sees initiation tasks and departmental Requisitions; the Head of Procurement Function sees authorisation tasks; neutral readers see no decision controls.

Frappe supplies the Desk header, breadcrumb, global search, user menu and common navigation. The existing PE/FY selector is reused and is never drawn inside a Claude Design artboard.

### 11.1 UI reuse and construction

| Asset | Disposition |
|---|---|
| Strategy/Planning page shell, context strip, cards, tables, badges, fields, file rows, dialogs and sticky footer | Reuse. |
| Planning Active Plan Item detail and eligibility projection | Reuse as read-only source context; add **Prepare Requisition** only when eligible. |
| Wide governance task layout | Reuse for HoD initiation and Procurement authorisation with the complete Requisition visible. |
| Planning, Budget or Needs workspaces | Do not duplicate. Deep links open their authorised neutral detail. |
| New Requisition workspace, editor and task pages | Build as Vue 3 SFCs mounted in Frappe Desk. |
| Design runtime, `.dc.html`, Tailwind utilities and copied vendor markup | Never ship. Claude Design remains visual evidence only. |

## 12. Static Claude Design contract

This section is the complete visual input to Claude Design. It contains static visual composition and exact fixture data only. Behaviour, validation, permissions, commands and transitions belong to section 13 and shall not be placed in a design prompt.

### 12.1 Closed-input rules

- Produce desktop artboards at **1440 × 1024 px**.
- Reuse the approved KenTender Strategy Portfolio, Procurement Planning and shared Desk-page visual system: tokens, spacing, typography, cards, badges, tables, fields, file rows, buttons, tabs, notices, empty states and dialogs.
- The artboard begins below the Frappe Desk header. Do not draw Frappe navigation, Desk header, breadcrumb, user menu, notifications, Help, global search or the PE/FY selector.
- Breadcrumb text is fixture data outside the artboard. It is supplied only to confirm location.
- Use only the visible labels, values, sections, badges, controls and states stated for the artboard.
- Do not invent data. If a value, column, control, message or state is not stated, omit it.
- Do not encode behaviour, validation, permissions, APIs, routing, transitions, concurrency, component names or implementation instructions in the visual output.
- Do not add charts, percentages, trends, illustrations, custom sidebars, steppers, helper panels, action menus, metadata or extra table columns.
- Do not show editable Plan title, description, Strategic Objective, method, Budget Line, funding source, unit or Planning dates.
- Do not show business justification, priority, urgency, requested-by person, contact, delivery location, source reference, authority reference, estimate basis, unit price, tax, cost breakdown, generic note or optional comments.
- Do not show Tender number, STD, procurement wizard, supplier, committee, evaluation, award or contract controls.
- Generated references appear only as quiet read-only text and never as inputs.

The approved page shell inside every artboard is:

- full-width warm-white page background;
- a 1200 px maximum-width content column centred in the page area;
- 32 px top and bottom page padding;
- page header followed by 24 px vertical spacing;
- 16 px gaps between cards or table sections; and
- no custom sidebar.

### 12.2 REQ-DES-01 — Requisition workspace

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Requisition Preparer · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 15 Jan 2027, 09:00 EAT · Frappe header breadcrumb: **Home > Procurement Requisitions**

**Page content header**

- Eyebrow: **PROCUREMENT REQUISITIONS**
- Title: **Departmental requisitions**
- Description: **Initiate procurement from your department's available Active Plan Items.**
- No header action button

**Context strip**

| Label | Value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Department | OU-MOH-DHI — Digital Health |
| Financial Year | FY 2027/28 |

**Tabs**

- **Eligible Plan Items** — selected
- **My requisitions**

**Eligible Plan Items table**

| Plan Item | Requirement type | Method | Planned completion | Remaining quantity | Remaining value | Action |
|---|---|---|---|---:|---:|---|
| PPI-MOH-2027-021 · National digital health infrastructure upgrade | Non-consulting services | Open Tender | 31 Aug 2027 | 1 programme | KES 80,000,000 | Prepare Requisition |

Below the table: **1 Plan Item available**. Do not show summary cards, search, advanced filters, Budget balances or another department's allocations.

**My requisitions tab variant**

Use the same header and context strip. Select **My requisitions** and show:

| Requisition | Plan Item | Requested value | Expected delivery | Status | Action |
|---|---|---:|---|---|---|
| REQ-MOH-2027-DHI-0001 · National digital health infrastructure upgrade | PPI-MOH-2027-021 | KES 80,000,000 | 31 Aug 2027 | Draft | Continue |

Below the table: **1 Requisition**. Do not show a second creation button or pagination.

### 12.3 REQ-DES-02 — Requisition editor

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Requisition Preparer · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 15 Jan 2027, 09:15 EAT · Frappe header breadcrumb: **Home > Procurement Requisitions > REQ-MOH-2027-DHI-0001**

**Page content header**

- Eyebrow: **PROCUREMENT REQUISITION**
- Title: **National digital health infrastructure upgrade**
- Quiet reference: **REQ-MOH-2027-DHI-0001 · PPI-MOH-2027-021**
- Status badge: **Draft**
- No header action button

**Approved Plan Item card**

| Label | Value |
|---|---|
| Annual Procurement Plan | PLN-MOH-2027-001 · Active Version 1 |
| Department | Digital Health |
| Requirement type | Non-consulting services |
| Procurement method | Open Tender |
| Strategic Objective | Strengthen interoperable national digital health services |
| Plan completion date | 31 Aug 2027 |
| Funding | MOH-BL-DHI-2027 · Government of Kenya |
| Finance | Confirmed |

All rows use the approved read-only field component.

**Requested drawdown card**

| Plan source | Available quantity | Requested quantity | Available value | Requested value |
|---|---:|---:|---:|---:|
| Digital Health infrastructure programme | 1 programme | 1 | KES 80,000,000 | 80,000,000 |

Requested quantity and Requested value are inputs. The unit and currency remain visible beside their controls. All other cells are read-only.

Below the row:

| Field label | Displayed value |
|---|---|
| Total requested value | KES 80,000,000 |
| Expected delivery date | 31 Aug 2027 |

Total is read-only. Expected delivery date is a date input.

**Technical documents card**

Heading: **Technical documents**

Required document row:

| Document type | File | Size | Status | Action |
|---|---|---:|---|---|
| Statement of Requirements | Digital Health Infrastructure Statement of Requirements v1.0.pdf | 2.4 MB | Ready | Replace |

Below the row, restrained secondary button: **Add applicable document**.

**Sticky page footer**

- Left-aligned secondary text button: **Cancel draft**
- Right-aligned secondary button: **Save draft**
- Right-aligned primary button: **Send to Head of Department**

Do not show title/description inputs, justification, priority, delivery location, market basis, unit price, Finance approval, HoD declaration or Tender controls.

### 12.4 REQ-DES-03 — Head of Department initiation task

**Fixture context — outside the artboard:** Dr Peter Kimani · `peter.kimani@moh.example.test` · Head of User Department · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 16 Jan 2027, 08:55 EAT · Frappe header breadcrumb: **Home > Procurement Requisitions > HoD initiation > REQ-MOH-2027-DHI-0001**

**Page content header**

- Eyebrow: **DEPARTMENTAL INITIATION**
- Title: **Initiate procurement requisition**
- Quiet reference: **REQ-MOH-2027-DHI-0001 · Version 1**
- Status badge: **Awaiting HoD**
- No header action button

**Plan and departmental context card**

| Label | Value |
|---|---|
| Procuring Entity | Ministry of Health |
| Department | Digital Health |
| Financial Year | FY 2027/28 |
| Plan Item | PPI-MOH-2027-021 · National digital health infrastructure upgrade |
| Annual Plan | PLN-MOH-2027-001 · Active Version 1 |
| Prepared by | Grace Wanjiku |
| Sent to HoD | 15 Jan 2027, 10:00 EAT |

**Requested procurement card**

| Label | Value |
|---|---|
| Requested quantity | 1 programme |
| Requested value | KES 80,000,000 |
| Expected delivery date | 31 Aug 2027 |
| Requirement type | Non-consulting services |
| Procurement method | Open Tender |
| Budget Line | MOH-BL-DHI-2027 — Digital health infrastructure programme |
| Funding | Confirmed |

**Technical documents table**

| Document type | File | Size | Action |
|---|---|---:|---|
| Statement of Requirements | Digital Health Infrastructure Statement of Requirements v1.0.pdf | 2.4 MB | View |

**Initiation statement card**

Text: **I initiate this procurement requisition against the approved Active Plan Item and submit the complete requirement shown above to the Head of Procurement Function for processing.**

Checkbox label: **I confirm this initiation**

**Decision footer**

- Left-aligned secondary button: **Return to preparer**
- Right-aligned primary button: **Submit to Procurement Function**

Do not show editable content, optional note, Accounting Officer approval, Finance task, Tender setup or a summary without the complete request and documents.

### 12.5 REQ-DES-04 — Submitted Requisition detail

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Requisition Preparer · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 16 Jan 2027, 09:05 EAT · Frappe header breadcrumb: **Home > Procurement Requisitions > REQ-MOH-2027-DHI-0001**

Use REQ-DES-03 main-content geometry without decision controls.

Exact differences:

- Eyebrow: **PROCUREMENT REQUISITION**
- Title: **National digital health infrastructure upgrade**
- Status badge: **Submitted to Procurement**
- Context row: **Submitted by — Dr Peter Kimani**
- Context row: **Submitted — 16 Jan 2027, 09:00 EAT**
- Blue neutral notice: **This Requisition is awaiting review by the Head of Procurement Function.**
- Footer has only **Back to requisitions**

Show the complete requested procurement and technical-document table. Do not show disabled Procurement decision controls, edit actions, drawdown, Tender actions or withdrawal in the page header.

### 12.6 REQ-DES-05 — Procurement authorisation task

**Fixture context — outside the artboard:** Samuel Otieno · `samuel.otieno@moh.example.test` · Head of Procurement Function · PE-MOH — Ministry of Health · FY 2027/28 · 17 Jan 2027, 09:55 EAT · Frappe header breadcrumb: **Home > Procurement Requisitions > Procurement review > REQ-MOH-2027-DHI-0001**

**Page content header**

- Eyebrow: **PROCUREMENT AUTHORISATION**
- Title: **Review procurement requisition**
- Quiet reference: **REQ-MOH-2027-DHI-0001 · Submitted Version 1**
- Status badge: **Submitted to Procurement**
- No header action button

**Initiation context card**

| Label | Value |
|---|---|
| Procuring Entity | Ministry of Health |
| Department | Digital Health |
| Plan Item | PPI-MOH-2027-021 · National digital health infrastructure upgrade |
| Annual Plan | PLN-MOH-2027-001 · Active Version 1 |
| Initiated by | Dr Peter Kimani |
| Initiated | 16 Jan 2027, 09:00 EAT |

**Requested procurement card**

| Label | Value |
|---|---|
| Requirement type | Non-consulting services |
| Procurement method | Open Tender |
| Strategic Objective | Strengthen interoperable national digital health services |
| Requested quantity | 1 programme |
| Requested value | KES 80,000,000 |
| Expected delivery date | 31 Aug 2027 |

**Planning availability table**

As-at line: **Availability as at 17 Jan 2027, 09:55 EAT**

| Plan source | Budget Line | Remaining quantity | Remaining value | Requested | Remaining after authorisation |
|---|---|---:|---:|---:|---:|
| Digital Health infrastructure programme | MOH-BL-DHI-2027 | 1 programme | KES 80,000,000 | 1 programme · KES 80,000,000 | 0 programme · KES 0 |

Green notice: **The complete requested quantity and value are available on the Active Plan Item.**

**Technical documents table**

| Document type | File | Size | Action |
|---|---|---:|---|
| Statement of Requirements | Digital Health Infrastructure Statement of Requirements v1.0.pdf | 2.4 MB | View |

**Departmental initiation card**

Show the exact initiation statement from REQ-DES-03 followed by **Confirmed by Dr Peter Kimani · 16 Jan 2027, 09:00 EAT**.

**Decision footer**

- Left-aligned secondary button: **Return to department**
- Right-aligned primary button: **Authorise for Tender Preparation**

Do not show editable request fields, optional professional note, method change, Finance confirmation, Accounting Officer approval, Tender number or STD selection.

### 12.7 REQ-DES-06 — Authorised Requisition

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Requisition Preparer · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 17 Jan 2027, 10:05 EAT · Frappe header breadcrumb: **Home > Procurement Requisitions > REQ-MOH-2027-DHI-0001**

**Page content header**

- Eyebrow: **PROCUREMENT REQUISITION**
- Title: **National digital health infrastructure upgrade**
- Quiet reference: **REQ-MOH-2027-DHI-0001 · Version 1**
- Status badge: **Authorised for Tender Preparation**
- No header action button

Green success notice: **This Requisition is authorised and ready for Tender Preparation.**

**Authorised request card**

| Label | Value |
|---|---|
| Plan Item | PPI-MOH-2027-021 |
| Department | Digital Health |
| Authorised quantity | 1 programme |
| Authorised value | KES 80,000,000 |
| Expected delivery date | 31 Aug 2027 |
| Authorised by | Samuel Otieno |
| Authorised | 17 Jan 2027, 10:00 EAT |
| Planning availability remaining | 0 programme · KES 0 |

**Technical documents table**

Show the same one document row as REQ-DES-05.

**Tender Preparation card**

| Label | Value |
|---|---|
| Handoff status | Ready for Tender Preparation |
| Tender reference | Not created |

Page footer: secondary **View Plan Item**. Do not show **Create Tender**, Tender fields, edit, reauthorise, optional note or manual handoff action.

### 12.8 REQ-DES-07 — Cross-department combined Plan Item Requisition

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Requisition Preparer · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 20 Jan 2027, 09:00 EAT · Frappe header breadcrumb: **Home > Procurement Requisitions > REQ-MOH-2027-DHI-0002**

**Page content header**

- Eyebrow: **PROCUREMENT REQUISITION**
- Title: **Clinical training and deployment laptops for digital health rollout**
- Quiet reference: **REQ-MOH-2027-DHI-0002 · PPI-MOH-2027-033**
- Status badge: **Draft**

**Combined Plan Item card**

| Label | Value |
|---|---|
| Annual Plan | PLN-MOH-2027-001 · Active Version 1 |
| Plan Item total | 500 each · KES 120,000,000 |
| Contributing departments | 2 |
| Requirement type | Goods |
| Procurement method | Open Tender |
| Planned completion | 31 Dec 2027 |

**Department allocations table**

| Department | Planned allocation | Requisition status |
|---|---:|---|
| Digital Health | 300 each · KES 72,000,000 | This Draft Requisition |
| Human Resources Management and Development | 200 each · KES 48,000,000 | Separate departmental Requisition |

**Your department drawdown card**

| Plan source | Available quantity | Requested quantity | Available value | Requested value |
|---|---:|---:|---:|---:|
| Clinical deployment laptops for digital health rollout | 300 each | 300 | KES 72,000,000 | 72,000,000 |

Expected delivery date: **31 Dec 2027**.

**Technical documents card**

| Document type | File | Size | Status | Action |
|---|---|---:|---|---|
| Technical Specifications | Clinical Laptop Technical Specifications v1.0.pdf | 1.8 MB | Ready | Replace |

Use the same footer as REQ-DES-02. Do not show a lead department selector, another department's editable allocation, another HoD signature, combined-Requisition control or Tender grouping action.

### 12.9 REQ-DES-08 — Returned correction

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Requisition Preparer · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 17 Jan 2027, 11:00 EAT · Frappe header breadcrumb: **Home > Procurement Requisitions > REQ-MOH-2027-DHI-0001 > Correct**

Use REQ-DES-02 geometry with these exact changes:

- Quiet reference: **REQ-MOH-2027-DHI-0001 · Draft Version 2**
- Status badge: **Returned**
- Red-bordered notice heading: **Correction required by Procurement**
- Notice text: **Replace the Statement of Requirements with the approved version that includes the service acceptance criteria.**
- Notice footer: **Returned by Samuel Otieno · 17 Jan 2027, 10:20 EAT**
- Technical document file: **Digital Health Infrastructure Statement of Requirements v1.1.pdf**
- File size: **2.6 MB**
- Left footer button: **Withdraw Requisition**
- Secondary footer button: **Save draft**
- Primary footer button: **Send to Head of Department**

Do not unlock or alter inherited Plan facts, display the earlier file as editable, or add a response/comment field.

### 12.10 REQ-DES-09 — Decision dialogs

Produce four separate dialog artboards over their corresponding dimmed pages.

**Return to preparer**

- Title: **Return Requisition to preparer?**
- Intro: **The Version reviewed above will remain unchanged. State the correction required.**
- Required multiline label: **Correction required**
- Exact value: **Confirm the expected delivery date against the department's implementation schedule.**
- Footer buttons: **Cancel** and **Return to preparer**

**Return to department**

- Title: **Return Requisition to department?**
- Intro: **The submitted Version will remain unchanged. State the correction required before resubmission.**
- Required multiline label: **Correction required**
- Exact value: **Replace the Statement of Requirements with the approved version that includes the service acceptance criteria.**
- Footer buttons: **Cancel** and **Return to department**

**Withdraw initiated Requisition**

- Title: **Withdraw this Requisition?**
- Intro: **The Requisition will no longer proceed to Procurement authorisation.**
- Required multiline label: **Reason for withdrawal**
- Exact value: **The department no longer requires initiation in this delivery period.**
- Footer buttons: **Cancel** and **Withdraw Requisition**

**Revoke authorisation**

- Title: **Revoke Requisition authorisation?**
- Intro: **This is available only before Tender Preparation consumes the handoff. The Planning drawdown will be reversed.**
- Required multiline label: **Reason for revocation**
- Exact value: **The authorised technical package contains a material error and must be replaced before a new Requisition is submitted.**
- Footer buttons: **Cancel** and **Revoke authorisation**

Do not add a reason category, attachment, assignee, due date, optional note or alternative action.

### 12.11 REQ-DES-10 — Common page states

Use the approved KenTender empty, error and unavailable components with these exact variants:

| State | Heading | Text | Control |
|---|---|---|---|
| No authorised context | Procurement Requisitions is not available | You do not have an active Requisition assignment for a Procuring Entity, Financial Year and department. | None |
| No eligible Plan Items | No Plan Items are currently available | Eligible Active Plan Item allocations will appear here. | None |
| No HoD tasks | No Requisitions awaiting initiation | Complete departmental Requisitions will appear here. | None |
| No Procurement tasks | No Requisitions awaiting Procurement review | HoD-submitted Requisitions will appear here. | None |
| Availability changed | Plan Item availability changed | Reload the Requisition and review the current remaining quantity and value. | Reload |
| Missing document | Technical document required | Add the required document before sending this Requisition. | Return to Requisition |
| Load error | Procurement Requisitions could not be loaded | Try again. If the problem continues, quote the support reference shown below. | Try again |

Only the load-error component may display a generated support reference. Do not add diagnostic details, illustrations or alternative controls.

## 13. Functional interaction requirements — excluded from design prompts

### 13.1 REQ-UI-01 — Requisition workspace

- Resolve eligible contexts only from effective Requisition assignments and configured PE/FY/OU contexts. One loads directly; several require deliberate selection in the existing global context control; none renders REQ-DES-10.
- `Eligible Plan Items` and `My requisitions` use the exact same PE/FY/OU scope as their counts and commands.
- Eligible rows come only from current Planning eligibility with positive remaining quantity and value and no open Requisition for that Plan Item/OU.
- An Active Plan Item with several departments yields a separate eligible row in each authorised department using only that OU's source allocations.
- Opening or filtering the workspace creates nothing.
- **Prepare Requisition** passes the exact Plan Item and OU to the guarded command. It never opens a blank form.
- A HoD or Procurement reviewer sees their task queue through the same workspace shell and only for their exact current capability.

### 13.2 REQ-UI-02 — Requisition editor

- `PrepareRequisition` locks and reloads Planning eligibility before creating/reusing one Draft and prepopulates the exact remaining source lines and Plan completion date.
- A Draft may be saved with incomplete line amounts or documents after the root exists. A zero or negative requested line is not saved as a placeholder row; the allocation is omitted from the current request.
- At least one drawdown line is required before sending or submitting.
- The user may reduce requested quantities and values but cannot exceed the current remaining values displayed on any source allocation.
- The unit and currency are inherited and never accepted from the client as authority.
- Expected delivery must be later than the Plan contract-signing date and no later than the Plan completion date.
- The required document types are derived from the inherited requirement type. **Add applicable document** offers only the admitted additional types.
- File upload validates admitted type, non-empty file, configured size limit, allowed safe MIME type and malware-scan result before the row becomes Ready.
- **Save draft** creates no task, Planning drawdown, Budget transaction or Tender handoff.
- **Cancel draft** withdraws an unsubmitted Draft without a reason, records the action and returns to the workspace. It changes no Planning availability.
- A returned correction loads the copied Draft successor and immutable correction text. The decided Version and its files remain read-only history.

### 13.3 REQ-UI-03 — HoD initiation

- A non-HoD preparer uses **Send to Head of Department**. The command completes validation, locks the exact Version and creates one protected HoD task.
- A HoD preparing their own complete Draft sees **Submit to Procurement Function** and does not perform a redundant send-to-self step.
- The task shows the complete inherited Plan context, requested drawdown, expected delivery and every technical document before the initiation declaration.
- **Submit to Procurement Function** requires the fixed confirmation, current HoD/delegation authority, exact task token and current Requisition completeness.
- A successful submission completes the HoD task and creates one protected Procurement authorisation task atomically. It creates no Planning drawdown.
- **Return to preparer** requires the exact correction dialog, preserves the immutable Version and creates one copied Draft successor.
- The HoD cannot edit the Version in the task or silently correct a preparer's values.

### 13.4 REQ-UI-04 — Submitted neutral detail

- Departmental users see the exact immutable submitted Version and a neutral waiting state.
- The page does not return Procurement-only availability detail or disabled decision controls.
- An effective HoD may invoke **Withdraw initiated Requisition** from the authorised contextual action before Procurement authorisation. The required reason is collected only in REQ-DES-09.
- Withdrawal completes open tasks and preserves submitted evidence. Because no authorisation exists, there is no Planning drawdown to reverse.

### 13.5 REQ-UI-05 — Procurement authorisation

- Authorise exact Head of Procurement Function task assignment and PE/FY scope before serialising submitted Requisition or live Planning availability.
- Load the immutable submitted Version, every technical file and a fresh Planning eligibility snapshot.
- **Authorise for Tender Preparation** is present only when every requested line is fully available, funding remains current, documents are complete, the Plan Version remains Active and maker-checker controls pass.
- Authorisation locks every affected Planning allocation and the Requisition task; reloads all values; creates all drawdown lines, the immutable decision and transactional-outbox handoff; and completes the task in one transaction.
- If any line fails, create no drawdown, decision or handoff and return `REQ_AVAILABILITY_CHANGED` with the current neutral values.
- **Return to department** requires one actionable correction, creates no drawdown and opens a copied Draft successor that must pass through HoD initiation again.
- The reviewer cannot edit requested values, expected date, files or inherited Plan data.
- There is no optional professional note, Finance reapproval, AO task or manual Tender creation.

### 13.6 REQ-UI-06 — Authorised Requisition and handoff

- Authorised detail displays the immutable Version, Planning drawdown reference and neutral Tender Preparation projection.
- The page shows **View Tender Preparation** only when the projection supplies a tender reference. Before that, it shows `Ready for Tender Preparation` and no manual create action.
- Handoff delivery retries idempotently and never repeats the Planning drawdown or authorisation.
- The Head of Procurement Function may open **Revoke authorisation** only while the handoff projection is unconsumed.
- Revocation rechecks consumption, reverses the exact Planning drawdown, records the reason/decision and publishes revocation atomically.
- Once Tender Preparation has consumed the handoff, Requisitions contains no revocation or edit path. Correction belongs to the downstream Tender lifecycle and its governed upstream-return contract.

### 13.7 REQ-UI-07 — Combined Plan Item departmental treatment

- A requesting department sees the complete Plan Item context but may enter drawdowns only for source allocations owned by that department.
- Other contributing departments appear as read-only context with their own Requisition status; their quantities, values and actions are not editable.
- One department's submission, return or authorisation does not create, decide or alter another department's Requisition.
- Requisitions publishes each authorised departmental handoff independently with the same Plan Item identity.
- Tender grouping, completeness of the combined package and anti-splitting treatment are decided in Tender Preparation, not through a Requisition lead-department or grouping control.

### 13.8 Technical-document handling

- A Draft technical file is visible only to the requesting department, the exact HoD task, the exact Procurement task and authorised neutral auditors.
- A submitted or authorised file is immutable and included by exact File reference in the handoff.
- Download uses an authorised service that rechecks Requisition scope before returning a short-lived file response.
- Removing or replacing a Draft file does not delete an immutable file used by an earlier Version.
- File names are display data from the File record; users do not type a second title or description.
- Tender Preparation receives the authorised technical files but cannot overwrite the Requisition copy.

### 13.9 Common page behaviour and accessibility

- Use semantic headings, labels, tables, file controls, status text and keyboard-operable actions. Colour is never the only state carrier.
- Dialog focus is trapped and restored. Validation focus moves to the first invalid input or the error summary.
- Initiating buttons are disabled while pending and reuse one idempotency key on retry.
- Dates display in `Africa/Nairobi`; service and audit instants remain UTC.
- Do not wait for `networkidle` on Frappe Desk pages. Browser tests wait for DOM content and a stable page-ready selector.
- Route changes unmount Vue and cancel stale reads/uploads. Returning to a cached page re-resolves context, task and current authority.
- Direct routes and file downloads enforce the same scope as list reads and return Not found when existence disclosure is unauthorised.

## 14. Audit and historical integrity

The audit record shall preserve:

- explicit Requisition creation from the exact Planning eligibility result;
- every Draft save and technical-file addition/removal;
- each locked Version sent to the HoD or submitted directly by an HoD;
- HoD initiation or return, including effective delegation where used;
- Procurement authorisation or return and the live Planning eligibility used;
- every Planning drawdown line and reference;
- the exact authorised handoff and outbox-delivery result;
- withdrawal, pre-consumption revocation and drawdown reversal; and
- downstream Tender Preparation consumption projection.

Audit uses framework actors/timestamps and immutable decisions. It does not add editable `created by`, `submitted by`, `approved by`, evidence, history note or source-reference fields to business forms.

Submitted, Returned, Authorised, Withdrawn and Superseded Versions; their files; decisions; drawdowns; reversals and handoffs are never edited or deleted through product commands.

## 15. Deterministic seed contract

### 15.1 Configuration prerequisites

| Fixture | Exact value |
|---|---|
| Procuring Entity | `PE-MOH` — Ministry of Health |
| Financial Year | `FY-2027-2028` — FY 2027/28 · 1 Jul 2027 to 30 Jun 2028 |
| Context | `CTX-MOH-2027-2028` |
| OU 1 | `OU-MOH-DHI` — Digital Health |
| OU 2 | `OU-MOH-HRMD` — Human Resources Management and Development |
| Unit 1 | `UNIT-PROGRAMME` — Programme |
| Unit 2 | `UNIT-EACH` — Each |
| Timezone | `Africa/Nairobi` |
| Maximum technical-file size | 20 MB |
| Allowed fixture MIME type | `application/pdf` |

Planning, Strategy, Budget and organisation fixtures load before Requisitions. Seeds fail on any missing or inconsistent authoritative prerequisite and create no fallback record.

### 15.2 Actors and assignments

| Actor | Exact assignment |
|---|---|
| `grace.wanjiku@moh.example.test` · Grace Wanjiku | Requisition Preparer for PE-MOH / OU-MOH-DHI and OU-MOH-HRMD / FY 2027/28 |
| `peter.kimani@moh.example.test` · Dr Peter Kimani | Head of User Department for the two named OUs / FY 2027/28 |
| `julia.njeri@moh.example.test` · Julia Njeri | HoD Delegate for OU-MOH-DHI from 1 to 31 Jan 2027 |
| `samuel.otieno@moh.example.test` · Samuel Otieno | Head of Procurement Function for PE-MOH / FY 2027/28 |
| `mercy.kilonzo@moh.example.test` · Mercy Kilonzo | Procurement Planner neutral read for the same Plan lineage |
| `peter.ouma@audit.example.test` · Peter Ouma | Requisition Auditor read for PE-MOH / FY 2027/28 |
| `no.context@example.test` · No-context User | Authenticated with no Requisition assignment |

No seed business decision uses Administrator.

### 15.3 Authoritative Active Plan baseline

| Field | Exact value |
|---|---|
| Annual Plan | `PLN-MOH-2027-001` — Ministry of Health Annual Procurement Plan 2027/28 |
| Active Version | `PLN-MOH-2027-001-V1` |
| Plan Item | `PPI-MOH-2027-021` — National digital health infrastructure upgrade |
| Department | `OU-MOH-DHI` — Digital Health |
| Requirement type | Non-consulting services |
| Procurement method | Open Tender |
| Strategic Objective | `OBJ-MOH-2023-001` — Strengthen interoperable national digital health services |
| Source allocation | `PSA-MOH-2027-021-001` |
| Approved/remaining quantity before Requisition | 1 programme / 1 programme |
| Approved/remaining value before Requisition | KES 80,000,000 / KES 80,000,000 |
| Budget Line | `MOH-BL-DHI-2027` — Digital health infrastructure programme |
| Funding source | Government of Kenya |
| Reservation | `RSV-MOH-2027-021-001` · KES 80,000,000 · Active |
| Contract signing | 1 Aug 2027 |
| Plan completion | 31 Aug 2027 |

### 15.4 Integrated authorised Requisition

| Field | Exact value |
|---|---|
| Requisition | `REQ-MOH-2027-DHI-0001` |
| Root scope | PE-MOH / FY-2027-2028 / OU-MOH-DHI / PPI-MOH-2027-021 |
| Authorised Version | `REQ-MOH-2027-DHI-0001-V1` |
| Drawdown line | `REQDL-MOH-2027-DHI-0001-001` → `PSA-MOH-2027-021-001` |
| Requested quantity | 1 programme |
| Requested value | KES 80,000,000 |
| Expected delivery | 31 Aug 2027 |
| Technical document | `REQDOC-MOH-2027-DHI-0001-001` · Statement of Requirements |
| File | `FILE-REQ-MOH-2027-DHI-0001-SOR-V1` · Digital Health Infrastructure Statement of Requirements v1.0.pdf · 2.4 MB |
| Planning drawdown | `PLN-DW-MOH-2027-021-REQ-0001` |
| Handoff | `REQ-HO-MOH-2027-DHI-0001-V1` · Ready for Tender Preparation |
| Tender reference | None |

The deterministic PDF fixture contains the fixed heading **Digital Health Infrastructure Statement of Requirements**, version **1.0**, Plan Item reference **PPI-MOH-2027-021**, scope paragraph and service-acceptance headings. It is generated from fixed seed bytes and not from user workstation content.

### 15.5 Integrated lifecycle authority

| Event | Actor | Exact time and outcome |
|---|---|---|
| Draft created | Grace Wanjiku | 15 Jan 2027, 09:05 EAT · Draft Version 1 |
| Draft saved complete | Grace Wanjiku | 15 Jan 2027, 09:30 EAT |
| Sent to HoD | Grace Wanjiku | 15 Jan 2027, 10:00 EAT · Awaiting HoD |
| Initiated and submitted | Dr Peter Kimani | 16 Jan 2027, 09:00 EAT · Submitted to Procurement |
| Authorised | Samuel Otieno | 17 Jan 2027, 10:00 EAT · Authorised for Tender Preparation |
| Planning drawdown committed | System in authorisation transaction | 17 Jan 2027, 10:00 EAT · 1 programme / KES 80,000,000 |
| Handoff published | System outbox | 17 Jan 2027, 10:00 EAT · Ready for Tender Preparation |

After authorisation, PPI-MOH-2027-021 has remaining quantity 0 programme and remaining value KES 0. The existing Budget reservation remains KES 80,000,000; Requisitions creates no second reservation.

### 15.6 Isolated returned-correction profile

| Field | Exact value |
|---|---|
| Decided Version | `REQ-MOH-2027-DHI-0001-V1` · Returned by Procurement |
| Decision | `REQDEC-MOH-2027-DHI-0001-RETURN-001` |
| Correction | Replace the Statement of Requirements with the approved version that includes the service acceptance criteria. |
| Returned by | Samuel Otieno · 17 Jan 2027, 10:20 EAT |
| Correction Draft | `REQ-MOH-2027-DHI-0001-V2` |
| Replacement file | Digital Health Infrastructure Statement of Requirements v1.1.pdf · 2.6 MB |
| Planning drawdown | None |

### 15.7 Isolated combined Plan Item profile

| Field | Exact value |
|---|---|
| Plan Item | `PPI-MOH-2027-033` — Clinical training and deployment laptops for digital health rollout |
| Plan Item total | 500 each · KES 120,000,000 |
| Digital Health allocation | `PSA-MOH-2027-033-002` · 300 each · KES 72,000,000 |
| HRMD allocation | `PSA-MOH-2027-033-001` · 200 each · KES 48,000,000 |
| DHI Requisition | `REQ-MOH-2027-DHI-0002` · 300 each · KES 72,000,000 |
| HRMD Requisition | `REQ-MOH-2027-HRMD-0001` · 200 each · KES 48,000,000 |
| DHI technical file | Clinical Laptop Technical Specifications v1.0.pdf · 1.8 MB |
| HRMD technical file | Clinical Laptop Technical Specifications v1.0.pdf · 1.8 MB |

Both Requisitions reference PPI-MOH-2027-033 but contain only their own OU allocations and HoD decision. The profile is isolated from the default Budget baseline and exists for boundary, UI and Tender-handoff tests.

### 15.8 Isolated partial and negative profiles

| Profile | Exact condition and result |
|---|---|
| `REQ-SC-PARTIAL-DHI` | DHI requests 100 of 300 each and KES 24,000,000 from PSA-MOH-2027-033-002; authorisation leaves 200 each and KES 48,000,000. |
| `REQ-SC-OVER-QUANTITY` | Request 301 each from a remaining 300; `REQ_LINE_INVALID`. |
| `REQ-SC-OVER-VALUE` | Request KES 72,000,001 from remaining KES 72,000,000; `REQ_LINE_INVALID`. |
| `REQ-SC-AVAILABILITY-RACE` | Two different authorisation commands compete for the final remaining availability; exactly one drawdown commits. |
| `REQ-SC-MISSING-DOCUMENT` | Non-consulting services Requisition has no Statement of Requirements; HoD send/submit is blocked. |
| `REQ-SC-INVALID-DATE` | Expected delivery is after Plan completion; submit is blocked. |
| `REQ-SC-CROSS-OU` | DHI actor requests HRMD allocation; return Not found and disclose no allocation. |
| `REQ-SC-REVOKE-READY` | Authorised handoff unconsumed; revocation reverses exact drawdown once. |
| `REQ-SC-REVOKE-CONSUMED` | Tender Preparation projection contains a Tender reference; revocation returns `REQ_HANDOFF_CONSUMED`. |

### 15.9 Seed execution rules

- Upsert by exact stable identifiers and create no duplicate root, Version, task, decision, document, drawdown or handoff.
- Use the named role actor for every business event and System only for transaction/outbox effects.
- Validate all records through the same domain services used by product commands.
- Freeze the service clock per profile.
- Scan and store deterministic fixture files through the same file controls used in product flows.
- Keep return, partial, race, revocation and combined profiles isolated from the default authorised baseline.
- Fail loudly on missing prerequisite, invalid authority, wrong Plan state, bad arithmetic, duplicate open Requisition, invalid document or inconsistent expected state.
- Seed no removed field, legacy alias, UI-only display value, optional note or Tender record.

## 16. Acceptance contract

The module is accepted only when all statements below are demonstrably true.

| ID | Required result |
|---|---|
| REQ-AC-001 | Zero, one and multiple authorised context cases fail closed without unauthorised disclosure. |
| REQ-AC-002 | Workspace, detail and file reads create no business record. |
| REQ-AC-003 | A Requisition can be created only from one eligible Active Plan Item and requesting OU. |
| REQ-AC-004 | One open Requisition per Plan Item/OU is enforced idempotently and concurrently. |
| REQ-AC-005 | Title, description, type, method, Strategy, Budget and schedule display from Planning and cannot be posted as edits. |
| REQ-AC-006 | Draft input is limited to drawdown quantities/values, expected delivery date and typed technical files. |
| REQ-AC-007 | Requested line quantity/value cannot exceed the live remaining source allocation. |
| REQ-AC-008 | Expected delivery is after contract signing and not after Plan completion. |
| REQ-AC-009 | Each requirement type enforces only its defined minimum technical document set. |
| REQ-AC-010 | Draft save and HoD routing create no Planning drawdown or Budget transaction. |
| REQ-AC-011 | A non-HoD preparer can send but cannot formally submit the Requisition. |
| REQ-AC-012 | A HoD preparing directly can submit without a redundant send-to-self task. |
| REQ-AC-013 | HoD task shows the complete immutable request and technical documents before initiation. |
| REQ-AC-014 | HoD return preserves the viewed Version and creates a copied Draft successor. |
| REQ-AC-015 | HoD submission creates one Procurement task and no Finance or AO task. |
| REQ-AC-016 | Departmental neutral detail exposes no Procurement-only decision controls. |
| REQ-AC-017 | Procurement task authorisation and PE/FY scope are checked before protected data serialisation. |
| REQ-AC-018 | Procurement review shows complete request, live Planning availability and every technical file. |
| REQ-AC-019 | Authorisation commits every requested Planning drawdown line, one decision and one handoff atomically. |
| REQ-AC-020 | Any failed line causes zero drawdowns, no authorisation and no handoff. |
| REQ-AC-021 | Authorisation creates no new Budget reservation and no Tender. |
| REQ-AC-022 | Procurement return preserves the submitted Version and repeats HoD initiation after correction. |
| REQ-AC-023 | An authorised Requisition exposes only neutral Tender Preparation status and no Create Tender control. |
| REQ-AC-024 | Handoff retries are idempotent and never duplicate drawdown or authorisation. |
| REQ-AC-025 | Pre-consumption revocation reverses the exact drawdown once and preserves evidence. |
| REQ-AC-026 | Consumed handoff cannot be revoked from Requisitions. |
| REQ-AC-027 | A department sees and draws only its own allocations in a combined Plan Item. |
| REQ-AC-028 | Separate departmental Requisitions retain the same combined Plan Item reference without a lead department. |
| REQ-AC-029 | One HoD cannot initiate another department's Requisition. |
| REQ-AC-030 | Technical file access is scope-protected and submitted files are immutable. |
| REQ-AC-031 | Draft cancellation needs no reason and changes no Planning availability. |
| REQ-AC-032 | Post-submission withdrawal requires the exact reason and creates no drawdown. |
| REQ-AC-033 | Same idempotency key returns the original result; a competing command returns the current result or stale error. |
| REQ-AC-034 | Cross-PE, cross-FY, cross-OU and out-of-task direct URLs return Not found. |
| REQ-AC-035 | No removed field, Finance task, AO task, Planner approval, Tender field or legacy adapter exists. |
| REQ-AC-036 | Seed reset and rerun produce the exact baseline without duplicates or semantic drift. |

### 16.1 Minimum automated coverage

1. Domain tests for eligibility, one-open uniqueness, line arithmetic, delivery date, document rules, state transitions and immutability.
2. Permission tests for preparer, HoD, delegate, Head of Procurement Function, neutral viewers, auditors and cross-scope denial.
3. Contract tests for Planning eligibility/drawdown/reversal, Budget/Strategy snapshots and Tender handoff/revocation.
4. Transaction tests for HoD submission, Procurement authorisation, drawdown races, idempotent handoff and revocation.
5. File tests for admitted types, size, malware result, replacement, immutable versions and protected download.
6. Vue component tests for exact fields, absent fields, complete task details, errors, file rows and decision dialogs.
7. Focused Playwright journeys for direct HoD preparation, preparer-to-HoD, Procurement return, authorisation, combined Plan Item OU isolation and pre-consumption revocation.

## 17. Implementation and test constraints

### 17.1 Frappe and Vue implementation

- Keep Procurement Requisitions in its own Frappe module boundary with conventional DocTypes, permissions, child tables, transactions, File links and audit fields.
- Enforce every material rule in Python domain services; client controls are not authority.
- Use one server-computed screen projection per surface rather than client joins across Planning, Budget and Strategy DocTypes.
- Integrate Planning drawdown and Requisition authorisation inside one database transaction where the apps share the bench/database; use locked domain services, not direct table writes.
- Publish Tender handoff through a transactional outbox after the same commit.
- Mount Vue 3 SFCs into real `frappe.ui.make_app_page()` Desk pages through the proven bench build pipeline.
- Reuse shared KenTender tokens/components and scoped styles. Do not ship Claude Design runtime, `.dc.html`, CDN dependencies or utility-class markup.
- Use the Frappe File model with private files, safe MIME/size checks, malware status and authorised download handlers.
- Unmount Vue, abort stale requests and release event listeners on Desk route change.
- Keep Frappe header, breadcrumb, global selector and navigation outside the Vue artboard.

### 17.2 TDD and efficient verification

Use the smallest proving loop:

1. write or identify the focused failing test for the changed rule;
2. run that exact test or smallest test file;
3. implement the minimum coherent change;
4. rerun the focused test;
5. run the immediately related Requisition slice;
6. run Planning/Tender contract regression only at integration checkpoints; and
7. run the full suite once before handoff, not after every small fix.

| Tier | When | Expected scope |
|---|---|---|
| 1 — focused | Every code change | One named domain, file, permission or component test |
| 2 — feature slice | Focused test passes | Editor, HoD, Procurement review, drawdown or handoff slice |
| 3 — module regression | A coherent slice is complete | Procurement Requisitions server and UI tests |
| 4 — integration checkpoint | Planning or Tender contract changes | Requisitions plus affected Planning/Tender contract tests |
| 5 — release | Before handoff | Full suite, build and selected browser acceptance journeys |

Do not rerun hundreds of unrelated tests while diagnosing one focused failure. Capture the first failing assertion, inspect its owning layer and correct the cause before broad reruns. Browser tests use deterministic profiles, stable `data-testid` selectors and explicit page-ready elements; they do not use arbitrary sleeps or `networkidle`.

### 17.3 Required release evidence

- schema and field-purpose audit;
- removed-field and legacy-route search;
- focused and module test reports;
- Planning drawdown and Tender handoff contract test report;
- successful application build;
- seed reset/idempotency report;
- screenshots for REQ-DES-01 through REQ-DES-10 at 1440 × 1024;
- scripted direct-HoD, preparer-to-HoD, return, authorisation and combined-OU journeys;
- protected-file negative checks;
- zero page-specific console errors and failed network requests; and
- confirmation that no design runtime, duplicate Finance workflow or Tender implementation entered the module.

## 18. Prohibited shortcuts

Implementation shall not:

- create a Requisition without an eligible Active Plan Item;
- accept another department's source allocation;
- re-enter or edit Planning, Strategy, Budget or DPP facts;
- add title, description, justification, priority, urgency, contact, delivery location, estimate basis, source reference, authority reference, generic evidence or optional note fields;
- add a Lead User Department or multi-HoD Requisition;
- let a preparer submit as HoD because they created the Draft;
- let HoD or Procurement task pages edit the submitted Version;
- add a Budget Officer, Finance, Accounting Officer or Planner approval task;
- consume Plan availability on Draft save, send-to-HoD or Procurement return;
- commit only some drawdown lines when another line fails;
- create a second Budget reservation;
- create, name, configure, publish or advertise a Tender;
- let users manually mark a Tender handoff consumed or successful;
- revoke a handoff after Tender Preparation consumption;
- expose submitted technical files through public or scope-free URLs;
- overwrite a file referenced by a submitted Version;
- import Claude Design runtime, Tailwind utilities or vendor markup into production;
- draw or replace the Frappe header, breadcrumb or global selector; or
- use full-suite reruns as the first diagnostic step for a focused defect.

## 19. Traceability and precedence

This document consumes:

- CFG-CHG-002 v0.3 for PE/FY/OU context, assignments and delegation;
- STR-CHG-001 v1.3 through the immutable Strategic Objective lineage on the Active Plan Item;
- BUD-CHG-001 v1.1 through the Planning reservation and funding projection;
- NDS-CHG-001 v1.0 only through inherited Planning lineage; and
- PLN-CHG-001 v1.0 for Active Plan Item eligibility, exact source allocations, remaining quantity/value and Requisition drawdown.

The fixed initiation boundary is supported by [Public Procurement and Asset Disposal Regulations, regulation 71](https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng%402022-12-31).

Where an earlier informal note, audit or mockup treats a Need, DPP or approved Plan as procurement initiation, this document and the approved Planning boundary control: initiation occurs only when the HoD submits the Requisition. Where a mockup adds a second Finance/approval layer or creates a Tender from the Requisition page, that mockup is not implementation authority.

## 20. Approval effect and next module

Approval of REQ-CHG-001 v1.0 authorises implementation of the clean Procurement Requisitions module and conversion of section 12 into Claude Design artboards. It does not approve generated visual deviations, a Tender shell, STD binding, procurement wizard, invitation, evaluation, award or contract workflow.

The next module is **Tender Preparation**. Its first canonical document must consume the immutable `AuthorisedRequisitionHandoff`, define whether and how compatible authorised Requisitions are grouped into one Tender shell, bind the correct Standard Tender Document and keep Tender configuration separate from Requisition initiation.
