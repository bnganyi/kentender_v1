# NDS-CHG-001 — Clean Departmental Needs

| Control | Value |
|---|---|
| Document ID | NDS-CHG-001 |
| Version | 1.0 |
| Date | 23 August 2026 |
| Status | Approved |
| Approval | Product owner · 23 August 2026 |
| Module | Departmental Needs |
| Implementation posture | Clean correction in place; no compatibility layer |

**Controlling decision:** Departmental Needs is an optional consultation channel through which users propose one plain-language anticipated requirement at a time. Acceptance makes a Need available to Procurement Planning; it is not a prerequisite for the HoD to plan a direct departmental requirement. Departmental Needs does not classify procurement, approve expenditure, reserve funds, create a Plan Item, create a Procurement Requisition or initiate a Tender.

## 1. Governing decision

This document is the single implementation authority for Departmental Needs. It replaces NDS-CHG-001 v0.2, NDS-CHG-002 v0.1 and NDS-CHG-003 v0.1 wherever they conflict with it.

The existing application is corrected in place. Usable code and the proven Claude Design → Vue 3 → Frappe Desk page pattern may be reused. Removed concepts are deleted rather than renamed, aliased, dual-read or retained behind feature flags.

Completion requires one coherent result across schema, services, permissions, screens, fixtures and tests. A field, action, object, service, queue or screen not defined here is outside this module.

### 1.1 Conflict and disposition register

| Earlier item | Disposition in v1.0 |
|---|---|
| One Need containing several item lines | Replace with one Need for one requirement. Quantity and unit belong directly to the Need. |
| Planner combine, split or partially allocate Need lines | Remove from Departmental Needs. When Planning uses an accepted Need, it uses the current accepted version and full accepted quantity. |
| `Partially included` Planning usage | Remove. The projection is only `Not included` or `Fully included`. |
| Delivery or use location | Remove. No approved current rule, decision or downstream contract consumes it. |
| Supporting attachments | Remove. No approved current departmental-review decision requires a document. |
| Indicative estimate, Budget Line, funding source and currency on a Need | Remove. Funding specification belongs to the DPP entry in Procurement Planning, not consultation intake. |
| Free-text `Other` unit | Remove. Units come only from the governed unit catalogue. |
| Requirement type or procurement category on a Need | Remove. Procurement Planning owns classification. |
| Strategy reference on a Need | Remove. A Plan Item selects its Strategic Objective in Procurement Planning. |
| Generic source, authority, evidence, notes or contact fields | Remove. None has a named current consumer and effect. |
| Budget Officer and Accounting Officer Departmental Needs workspaces | Remove. They have no Departmental Needs decision or task. |
| Procurement Planner Departmental Needs landing page | Remove. Planners work in Procurement Planning and may open an accepted Need read-only. |
| Four summary cards, separate action/waiting sections and advanced register filters | Replace with one role-appropriate table and minimal search/status filters. |
| Shared-task claim, release and support-lookup workflows | Remove. Review work is a scoped departmental queue; an authorised decision atomically completes the task. |
| `/departmental-needs`, `/desk/departmental-needs` and legacy `/demands` routes | Replace with the canonical Frappe Desk routes in section 10. No redirect or alias. |
| Accepted Need treated as permanently unchangeable | Correct. The accepted version is immutable, but a separately reviewed successor may replace it. |
| Direct withdrawal of an accepted Need | Retain only through a reviewed withdrawal request. An Active Plan dependency must be cleared first. |
| Separate Needs intake and departmental-plan windows treated as interchangeable | Correct. Departmental Needs owns its minimal intake window; Procurement Planning owns its separate submission window. |
| Planning source payload includes Strategy, requirement type or generic source evidence | Correct the payload. Those values are not owned by Departmental Needs. No Planning screen redesign is required. |
| Accepted Need as the exclusive source of a DPP entry or Plan Item | Remove. Planning also permits a HoD or authorised departmental plan preparer to capture a direct departmental requirement. It does not create a synthetic Need. |
| Legacy Demand migration and compatibility | Prohibited. Departmental Needs remains a clean domain. |

## 2. Purpose and outcomes

Departmental Needs shall provide:

- wider consultation on requirements that departments may consider for procurement planning;
- a simple way for a departmental requester to state one anticipated requirement;
- clear PE, department and Financial Year ownership;
- departmental maker-checker review;
- immutable accepted versions that Procurement Planning can consume safely;
- controlled correction of an accepted Need through a successor version;
- clear read-only Planning usage without changing the Need lifecycle; and
- a reviewed withdrawal path that protects an Active Plan dependency.

Departmental Needs is not the gatekeeper for departmental procurement planning. A department may prepare a DPP entirely from direct departmental requirements, entirely from accepted Needs, or from both.

### 2.1 Scope exclusions

The module shall not contain:

- procurement category, requirement type, method, lot, schedule, specification, bill of quantities or Terms of Reference;
- a Strategic Objective, Outcome, Indicator, Target or Value Commitment;
- unit price, tax calculation, market estimate or cost breakdown;
- funding availability, reservation, commitment, Finance confirmation or payment data;
- a Plan Item editor, Procurement Requisition, Tender or contract action;
- delivery location, source reference, authority reference, evidence field, attachment, generic note or contact;
- several item rows inside one Need;
- a scoring model, completion percentage, dashboard chart or performance card;
- editable technical identifiers, hashes, audit actors or timestamps;
- a duplicate Planner, Budget Officer, Accounting Officer or System Administrator landing page;
- a custom Frappe shell, header, breadcrumb, global selector or navigation system; or
- legacy Demand fields, routes, adapters, aliases, fallback records or migrated fixtures.

### 2.2 Data-purpose gate

No stored field is permitted unless all three conditions are documented before implementation:

1. a current operational decision or output uses the field;
2. the screen, rule or service consuming it is named; and
3. its validation and system effect are defined.

“Useful later”, “normally captured”, “helpful context” and “the design showed it” are not sufficient reasons. An undocumented field is omitted, not added as optional data.

The six requester-entered values in section 4.3 pass this gate:

| Value | Current consumer and effect |
|---|---|
| Title | Identifies the Need in queues, selectors, details and Planning lineage. |
| Description | Tells the departmental reviewer and Planner what is required. |
| Business justification | Tells the departmental reviewer why the Need should be accepted. It is not copied into the Planning source payload. |
| Indicative quantity | Supplies the full accepted quantity projected into the departmental plan. |
| Unit | Gives meaning to the quantity and is projected into the departmental plan. |
| Required by | Supports departmental review and the Planning schedule guard. |

## 3. Fixed ownership and dependency boundary

- Configuration & Governance owns PE, organisation unit, Financial Year, timezone, unit catalogue and capability assignments. Departmental Needs reads them and never infers a first or current record.
- Departmental Needs owns its intake window, Need identity, versions, review decisions and withdrawal requests.
- Strategy Alignment owns Strategic Objectives. A Need stores no Strategy reference.
- Budget & Funding owns Budgets, Budget Lines, funding source, currency, positions, reservations and commitments. Departmental Needs stores none of those values.
- Procurement Planning owns requirement classification, DPP entries, direct departmental requirements, Plan Items, source allocations, Finance tasks and Plan inclusion. It cannot edit a Need.
- Procurement Requisitions and Tendering consume approved Planning lineage later. A Need creates neither record.

| Information or decision | Owner | Departmental Needs relationship |
|---|---|---|
| PE, OU, FY, timezone, unit and capability assignment | Configuration & Governance | Resolve exact identifiers and fail closed when absent or ambiguous. |
| Needs intake open and close instants | Departmental Needs configuration | Gate initial Need creation and initial submission. |
| Need and accepted Need version | Departmental Needs | Create, review, version and publish. |
| Strategic Objective | Strategy Alignment / Procurement Planning | No Need field or write. |
| Requirement classification, direct requirement and Plan treatment | Procurement Planning | Consume an accepted Need when used, or capture a direct departmental requirement without creating a Need. |
| Planning usage | Procurement Planning | Publish `Not included` or `Fully included` back as a read-only projection. |
| Budget Line identity, funding source, currency and position | Budget & Funding | Selected through the Budget contract by Procurement Planning; no Need field or write. |
| DPP indicative amount | Procurement Planning | Captured on the DPP entry; no Need field or write. |
| Funding reservation | Budget & Funding through Procurement Planning | Created only at the Planning Finance control; no effect at Need save, submission or acceptance. |

The permitted dependency paths are:

**Configuration & Governance → Departmental Needs consultation → Procurement Planning DPP entry**

**Configuration & Governance / Budget & Funding → Procurement Planning direct requirement or accepted-Need enrichment → Procurement Requisitions**

Departmental Needs shall not import a downstream DocType controller or query a downstream table directly.

## 4. Canonical domain model

All identifiers are generated by the server. Framework audit fields remain framework-managed and are not repeated as user data.

### 4.1 NeedsIntakeWindow

The only Departmental Needs configuration record for initial intake.

| Field | Operational purpose and system effect |
|---|---|
| `needs_intake_window_id` | Immutable generated reference used by commands and audit. |
| `procuring_entity_id` | Fixes the PE scope. Required. |
| `financial_year_id` | Fixes the target FY. Required. |
| `opens_at` | UTC instant from which a new Need may be created or initially submitted. Required. |
| `closes_at` | Inclusive UTC instant after which a new Need cannot be created or initially submitted. Required and later than `opens_at`. |

There is at most one NeedsIntakeWindow for one PE/FY. `Scheduled`, `Open` and `Closed` are derived from the configured clock and are not stored statuses. There is no window title, description, reason, source reference, approval, attachment or manual status.

### 4.2 DepartmentalNeed

The stable identity and scope of one requirement.

| Field | Operational purpose and system effect |
|---|---|
| `need_id` | Immutable internal identity used by services and lineage. |
| `need_reference` | Generated on first save as `NDS-{PE code}-{FY start}-{4 digits}`; used by routes and users. |
| `procuring_entity_id` | Defines the PE and permission boundary. Required and immutable. |
| `org_unit_id` | Defines the owning department and review scope. Required and immutable. |
| `financial_year_id` | Defines the planning year and date boundary. Required and immutable. |
| `owner` (Frappe framework field) | Defines whose Need appears in **My needs** and who may correct it. Fixed on first save; do not create a duplicate originator field. |
| `current_state` | System-maintained root state: `Draft`, `Submitted`, `Returned`, `Accepted for planning`, `Not taken forward` or `Withdrawn`. |
| `current_version_id` | Points to the newest Draft or decided version for display and editing. |
| `current_accepted_version_id` | Points to the accepted version available to Planning. Empty until first acceptance. |
| `record_version` | Monotonic optimistic-concurrency token checked by every write. |

If an accepted Need has an open successor, `current_state` remains `Accepted for planning`; the successor's separate status is shown as `Draft update`, `Update submitted` or `Update returned`. This prevents an unaccepted edit from replacing the source available to Planning.

### 4.3 DepartmentalNeedVersion

One version of the requirement. Draft content is mutable only until submission. Submitted content is immutable.

| Field | Operational purpose and system effect |
|---|---|
| `need_version_id` | Immutable reference used in review, events and Planning lineage. |
| `need_id` | Links the version to its stable Need. |
| `version_number` | Generated sequence within the Need. |
| `based_on_version_id` | Identifies the version copied to create this correction or accepted successor. Empty only for the first Draft. |
| `version_status` | `Draft`, `Submitted`, `Returned`, `Accepted`, `Not taken forward`, `Withdrawn` or `Superseded`. |
| `title` | Short queue and detail label. Required for first save; 5–160 characters. |
| `description` | Plain-language statement of what is required. Required for submission; 10–1,000 characters. |
| `business_justification` | Plain-language reason used by the departmental reviewer. Required for submission; 20–1,000 characters. |
| `indicative_quantity` | Full quantity projected to Planning. Required for submission; greater than zero with at most three decimals. |
| `unit_id` | Governed unit giving meaning to the quantity. Required for submission. |
| `required_by_date` | Date the department needs the requirement. Required and inside the target FY. |
| `content_hash` | Generated when the version is submitted and used for idempotency, staleness and downstream lineage. |

### 4.4 DepartmentalNeedReviewTask

One open departmental decision task for one submitted version.

| Field | Operational purpose and system effect |
|---|---|
| `review_task_id` | Immutable task reference used by the review route and command. |
| `need_id` | Links the task to the stable Need. |
| `need_version_id` | Fixes the exact immutable content under review. |
| `task_type` | `Initial acceptance`, `Successor acceptance` or `Withdrawal`. |
| `procuring_entity_id` / `org_unit_id` / `financial_year_id` | Fixes the departmental queue and permission scope. |
| `status` | `Open`, `Completed` or `Cancelled`. |
| `decision_token` | Server-generated optimistic token preventing two decisions on the same task. |

The task is addressed to the effective departmental-review capability in the exact scope. It is not described as assigned to a named person until a decision actor completes it. There is no claim, release, priority, score, due-date or free-text task note.

### 4.5 DepartmentalNeedDecision

An immutable record created only by a successful command. It contains decision ID, Need ID, version or withdrawal-request ID, action, actor, effective assignment, timestamp, required reason when applicable, prior state, resulting state, content hash and command correlation ID.

Reasons exist only for:

- `Return for correction`;
- `Do not take forward`;
- `Request withdrawal`; and
- `Decline withdrawal`.

There is no generic reason, comment or evidence field on the Need.

### 4.6 NeedWithdrawalRequest

The minimal request to stop using an accepted Need.

| Field | Operational purpose and system effect |
|---|---|
| `withdrawal_request_id` | Immutable generated reference used by queue, route and audit. |
| `need_id` | Identifies the accepted Need. |
| `accepted_version_id` | Fixes the version the requester asks to withdraw. |
| `requested_by_user_id` | Enforces requester authority and maker-checker. |
| `reason` | Explains the business change to the departmental reviewer; 20–1,000 characters. |
| `status` | `Awaiting review`, `Awaiting planning clearance`, `Approved` or `Declined`. |
| `planning_dependency_version` | Identifies the Planning dependency result used by the current decision check. System-generated. |

There is at most one open withdrawal request for an accepted Need. The Need remains `Accepted for planning` until approval succeeds.

### 4.7 NeedPlanningUsageProjection

A read-only projection supplied by Procurement Planning.

| Field | Operational purpose and system effect |
|---|---|
| `need_id` / `accepted_version_id` | Fixes the source version represented by the projection. |
| `usage` | `Not included` or `Fully included`. |
| `active_plan_id` / `active_plan_item_id` | Supports **View Plan Item** and blocks an accepted withdrawal while inclusion is Active. Empty when not included. |
| `source_event_id` | Makes projection updates idempotent and ordered. |

This projection is not Need lifecycle state and users cannot edit it.

## 5. Lifecycle and business rules

### 5.1 Initial Need lifecycle

| Current state | Command | Result | Authorised actor |
|---|---|---|---|
| No record | Save Draft | Draft Version 1 and generated Need reference | Requester |
| Draft | Save Draft | Updated Draft | Originator |
| Draft | Submit | Submitted | Originator |
| Draft | Withdraw | Withdrawn | Originator |
| Submitted | Return for correction | Submitted version becomes Returned; copied successor Draft is created; root displays Returned | Departmental Reviewer |
| Submitted | Accept for planning | Submitted version becomes Accepted; root becomes Accepted for planning | Departmental Reviewer |
| Submitted | Do not take forward | Submitted version and root become Not taken forward | Departmental Reviewer |
| Returned | Save correction | Returned successor Draft updated; root remains Returned | Originator |
| Returned | Resubmit | Successor Draft becomes Submitted | Originator |
| Returned | Withdraw | Successor and root become Withdrawn | Originator |

### 5.2 Accepted successor lifecycle

| Current accepted state | Command | Result |
|---|---|---|
| Accepted for planning; no open successor | Create update | Copy accepted version into one Draft successor. Accepted version remains effective. |
| Draft update | Save / Submit update | Save the successor or lock and route it for departmental review. |
| Draft update | Cancel update | Successor becomes Withdrawn; earlier accepted version remains effective. |
| Update submitted | Return | Submitted successor becomes Returned and a copied correction Draft is created. Earlier accepted version remains effective. |
| Update submitted | Accept | Successor becomes Accepted; earlier accepted version becomes Superseded; new accepted event is published atomically. |
| Update submitted | Do not take forward | Successor becomes Not taken forward; earlier accepted version remains effective. |

There may be only one open successor per Need. No command edits, deletes or rewrites an Accepted, Superseded, Submitted, Returned, Not-taken-forward or Withdrawn version.

### 5.3 Accepted withdrawal lifecycle

| Current request state | Live Planning dependency | Decision | Result |
|---|---|---|---|
| Awaiting review | No Active Plan inclusion | Approve | Need and accepted version become Withdrawn; withdrawal event is published. |
| Awaiting review | Active Plan inclusion | Evaluate | Request becomes Awaiting planning clearance; Need remains Accepted. |
| Awaiting planning clearance | Still included | Re-evaluate | No state change. |
| Awaiting planning clearance | Inclusion cleared | Approve | Need and accepted version become Withdrawn. |
| Awaiting review or clearance | Any | Decline | Request becomes Declined; Need remains Accepted. |

Planning clearance is not performed in Departmental Needs. The user follows the existing Planning amendment route. A Draft or Submitted DPP is not an Active Plan dependency; withdrawal may proceed and Planning will receive a stale/ineligible-source event.

### 5.4 Invariants

| ID | Rule and enforcement |
|---|---|
| NDS-BR-001 | Every Need resolves to one explicit authorised PE, OU and FY. Missing, ambiguous or expired scope fails closed. |
| NDS-BR-002 | Initial creation and initial submission require one Open Needs intake window for the same PE/FY. Existing authorised records remain readable after close. |
| NDS-BR-003 | A correction of a version submitted before close may be resubmitted after close. An accepted successor may be proposed while the PE/FY context remains active. |
| NDS-BR-004 | One Need represents one requirement and has exactly one quantity, one unit and one required-by date. It has no funding specification. |
| NDS-BR-005 | The originator alone edits the initial Draft or returned correction. A separately assigned departmental reviewer decides it. |
| NDS-BR-006 | The actor who submitted the version cannot decide that version. Maker-checker is rechecked on the server. |
| NDS-BR-007 | Submission requires all six fields in section 4.3 and a current governed unit. |
| NDS-BR-008 | Need creation, submission and acceptance do not select or validate a Budget Line, capture an amount, check funding or create a reservation. |
| NDS-BR-009 | Required-by is inside the target FY and quantity is positive. |
| NDS-BR-010 | Submit creates one immutable content hash, one open review task and one durable notification event in the same transaction. |
| NDS-BR-011 | Return and decline require a 20–1,000 character reason. Accept has no invented reason field. |
| NDS-BR-012 | Accept means suitable for departmental procurement planning only. It creates no Plan Item, reservation, Requisition or Tender. |
| NDS-BR-013 | When Procurement Planning consumes a Need, it consumes only the current Accepted version and cannot edit, split, partially include or inflate its quantity. This rule does not prohibit a Planning-owned direct departmental requirement. |
| NDS-BR-014 | Planning usage is separate from lifecycle and changes only from an idempotent Planning projection event tied to an Active Plan. |
| NDS-BR-015 | Accepting a successor atomically supersedes the earlier accepted version and publishes exact old/new lineage. It does not rewrite a DPP or Active Plan. |
| NDS-BR-016 | An accepted withdrawal remains pending while the exact Need version is represented in an Active Plan. |
| NDS-BR-017 | Generated references, version numbers, statuses, hashes and audit data are never client-editable. |
| NDS-BR-018 | Every write checks record version, decision token and idempotency key under one transaction. |
| NDS-BR-019 | Counts, rows, direct routes, services and exports use the same server-side scope predicate before data is materialised. |
| NDS-BR-020 | No legacy Demand schema, state, route, service, permission, test or fixture is used. |
| NDS-BR-021 | A direct departmental requirement is created and governed in Procurement Planning. It does not create, impersonate or backfill a Departmental Need. |

## 6. Roles and permissions

| Role or capability | Permitted capability |
|---|---|
| Departmental Need Requester | View own Needs; create and edit own Draft/Returned Need; submit, resubmit and withdraw before acceptance; propose an update or withdrawal of own accepted Need. |
| Head of User Department | View Needs in assigned departmental scope; decide submitted Needs, successor updates and withdrawal requests, except own submitted version. |
| Departmental Review Delegate | Perform the same exact review command only within an explicit effective delegation. No broader department access is inferred from the role name. |
| Needs Configuration Manager | Set the intake open/close instants for an assigned PE/FY. No Need-review authority is implied. |
| Procurement Planner | Read current accepted Need versions through the typed source contract and exact read-only deep link. No Departmental Needs workspace or mutation. |
| Auditor | Read scoped Needs, versions, decisions and lineage; no business mutation. |
| System Administrator | Inspect technical metadata and neutral records read-only unless separately assigned a business capability. |

Assignments are scoped by PE, FY, optional OU, capability and effective dates. A selected context filters an already-authorised scope; it never grants authority. Combined roles are evaluated per command, not collapsed into the broadest label.

## 7. Procurement Planning integration

### 7.1 Accepted source payload

`DepartmentalNeedAccepted.v1` contains only:

- event ID and accepted time;
- Need ID and reference;
- accepted version ID, number and content hash;
- PE, OU and FY IDs;
- title and description;
- indicative quantity and governed unit ID/display value;
- required-by date.

It does not contain business justification, Budget Line, indicative amount, funding source, currency, Strategy, requirement type, procurement method, location, attachment, source reference, generic evidence or notes.

`DepartmentalNeedSuperseded.v1` identifies the Need, earlier accepted version/hash, successor accepted version/hash and the successor accepted payload. `DepartmentalNeedWithdrawn.v1` identifies the withdrawn accepted version and withdrawal decision. Delivery is transactional-outbox, idempotent and ordered per Need.

### 7.2 Planning treatment

- A DPP entry has exactly one source origin: `Accepted Departmental Need` or `Direct departmental requirement`.
- Planning creates or updates one DPP entry for every current accepted Need in the exact PE/FY/OU context. The Need-owned title, description, quantity, unit and required-by date remain read-only. Planning adds the Budget Line and indicative amount before DPP submission.
- When Planning uses an accepted Need, it takes the full accepted quantity; there is no partial Need allocation or Planning quantity override in MVP-1.
- A HoD or authorised departmental plan preparer may create a direct departmental requirement inside the department's Draft DPP without first creating a Need.
- A direct departmental requirement captures only title, description, quantity, governed unit, required-by date, eligible Budget Line and indicative amount. It does not collect a bypass reason, business justification, attachment, source reference or synthetic Need reference.
- Direct requirements are Planning-owned and editable only while the applicable DPP version is Draft or Returned. The HoD's certification of the complete DPP is the departmental governance control.
- A DPP may contain accepted-Need entries, direct entries or both. A DPP may consist entirely of direct entries.
- A Plan Item may be formed from one or more accepted DPP entries of either source origin. Every source retains its exact DPP-entry lineage; only accepted-Need entries additionally retain Need/version/hash lineage.
- Planning owns requirement classification and the selected Strategic Objective. Those fields do not return to the Need.
- A successor event makes the older Planning source stale. Existing Planning return, amendment and source-refresh controls handle the change; no Departmental Needs screen rewrites Planning data.
- An accepted withdrawal event makes any non-Active Planning source ineligible. An Active Plan dependency must have been cleared before the event can exist.
- Planning publishes `NeedPlanningUsageChanged.v1` only when an Active Plan starts or stops representing the accepted Need version.

### 7.3 Correction to the existing Planning source model

Earlier Planning text or fixtures that require every Plan Item to originate from an accepted Need are corrected by this document. The controlling source rule is:

- every current accepted Need must still be accounted for exactly once and at its full accepted quantity in the DPP, unless it is withdrawn or superseded and is no longer the current Accepted version;
- the DPP may also contain any number of direct departmental requirements authorised within its department and context;
- Plan Item source lineage terminates at the DPP entry for a direct requirement and at the accepted Need version for a Need-origin entry; and
- no direct entry creates a Need or requires a reason for not using the Needs consultation path.

Earlier Planning text or seed payloads that source `strategy`, `requirement_type` or generic `source evidence` from Departmental Needs are also corrected:

- Strategic Objective is selected on the Plan Item using the Strategy Alignment contract.
- Requirement type is classified by the DPP Validator in Procurement Planning.
- No generic source-evidence field exists.

Budget & Funding v1.1 text stating that Departmental Needs owns the selected Budget Line is superseded at this boundary. Procurement Planning owns the Budget Line and indicative amount on each DPP entry; Budget & Funding remains authoritative for Budget Line identity, eligibility and funding control.

The previously constructed Planning shell, DPP workspace and Plan Item UI remain reusable. The Planning design contract must add one exact direct-requirement editor, identify the source origin on DPP entries, and provide Budget Line and indicative amount controls for accepted-Need entries. The direct-requirement editor uses the seven values above. The accepted-Need enrichment surface displays the five read-only Need facts plus the two Planning-owned funding controls. Neither surface copies the Departmental Needs review workflow or asks Claude Design to invent data. This Departmental Needs design contract creates no extra Needs screen or duplicate dashboard.

## 8. Service and command contracts

All contracts are typed, versioned and server-authorised. Mutating commands require an idempotency key and expected record or decision token.

### 8.1 Read contracts

| Contract | Required input | Output and effect |
|---|---|---|
| `resolve_needs_contexts` | Actor and optional requested context | Exact eligible PE/OU/FY contexts and intake state. No fallback authority. |
| `get_needs_workspace` | Context, projection, search, status and paging | Authorised role-specific rows and counts from one predicate. |
| `get_departmental_need` | Need reference and optional accepted version | Authorised detail, current accepted source, open successor and Planning usage. No mutation. |
| `get_departmental_review_task` | Review task ID and decision token | Exact immutable version, requester, scope and permitted decision labels. |
| `get_needs_intake_window` | PE/FY | Open/close instants and derived Scheduled/Open/Closed state. |
| `get_current_accepted_need` | Need ID/reference, expected context and optional expected hash | Current accepted payload or typed stale/not-accepted error for Planning. |
| `check_accepted_need_withdrawal_dependency` | Need ID and accepted version | Current Active Plan dependency result and version token. No mutation. |

### 8.2 Commands

| Command | Purpose and required controls |
|---|---|
| `save_need_draft` | Create or update the originator's Draft after scope, intake and optimistic-lock checks. First save generates the Need reference. |
| `submit_need_version` | Validate all six values, governed unit, maker-checker route and intake/correction eligibility; lock the version and create one review task. |
| `return_need_version` | Recheck reviewer scope and maker-checker; require a reason; mark the submitted version Returned and create one copied correction Draft. |
| `accept_need_version` | Recheck exact reviewer task, current unit, content hash and concurrency; accept initial or successor version and publish lineage. |
| `decline_need_version` | Recheck exact reviewer task; require a reason; close the initial Need or successor without changing an earlier accepted version. |
| `withdraw_unaccepted_need` | Withdraw the originator's Draft or returned correction. |
| `create_accepted_need_successor` | Copy the originator's current accepted version into the only permitted Draft successor. |
| `cancel_accepted_need_successor` | Withdraw the originator's Draft successor and leave the earlier accepted version current. |
| `request_accepted_need_withdrawal` | Create the only open withdrawal request with a required reason and one review task. |
| `decide_accepted_need_withdrawal` | Recheck reviewer, maker-checker and live Planning dependency; approve, block for clearance or decline atomically. |
| `save_needs_intake_window` | Create or update one PE/FY window after configuration capability, UTC and concurrency checks. |
| `project_need_planning_usage` | Accept an authenticated, ordered Planning event and update the read-only projection idempotently. |

Notifications are durable post-commit effects for submit, return, accept, decline and withdrawal decisions. They are not separate business records or user-entered messages.

## 9. Error contract

| Code | Required result |
|---|---|
| `NDS_CONTEXT_REQUIRED` | No single authorised PE/OU/FY context can be resolved. Create no record. |
| `NDS_SCOPE_DENIED` | Actor lacks the exact current capability and scope. Disclose no protected record data. |
| `NDS_INTAKE_NOT_OPEN` | Initial creation or initial submission is outside the Needs intake window. |
| `NDS_FIELD_REQUIRED` | Return exact missing field identifiers; create no task or state change. |
| `NDS_REQUIRED_BY_OUTSIDE_FY` | Required-by is outside the target FY. |
| `NDS_UNIT_INELIGIBLE` | Unit is absent or inactive. |
| `NDS_MAKER_CHECKER` | Version maker attempted its decision. |
| `NDS_STATE_CONFLICT` | Command is invalid for the current Need/version state. |
| `NDS_OPEN_SUCCESSOR_EXISTS` | Another accepted successor is already open. |
| `NDS_STALE_WRITE` | Record version or decision token is stale. Overwrite nothing. |
| `NDS_WITHDRAWAL_ALREADY_OPEN` | One open withdrawal request already exists. |
| `NDS_ACTIVE_PLAN_DEPENDENCY` | Accepted withdrawal is blocked by the returned Active Plan and Plan Item. |
| `NDS_IDEMPOTENCY_CONFLICT` | The same key was reused with a different payload. |
| `NDS_SOURCE_STALE` | Requested accepted version/hash is no longer current. |
| `NDS_NOT_ACCEPTED` | No current accepted version exists. |

Errors are stable service results, not inferred from button visibility or free-text exception messages.

## 10. UI architecture, menu and routes

**Departmental Needs** is a top-level KenTender module placed after **Budget & Funding** and before **Procurement Planning** in the business-flow menu.

Its module menu contains only:

- **Departmental Needs**;
- **Review tasks**, visible only to an effective Head of User Department or Departmental Review Delegate; and
- **Intake window**, visible only to an effective Needs Configuration Manager.

Procurement Planners use the existing Procurement Planning workspace. A Planning deep link may open NDS-UI-06 read-only for the exact accepted Need; it does not create a Planner landing page.

| Screen | Canonical route | Purpose |
|---|---|---|
| NDS-UI-01 Requester workspace | `/app/departmental-needs` | Create and track the current user's Needs. |
| NDS-UI-02 Department review | `/app/departmental-needs/review` | Review queue and departmental register. |
| NDS-UI-03 Need editor | `/app/departmental-needs/new` or `/app/departmental-needs/{need_reference}/edit` | Create, correct or propose an accepted successor using the same six fields. |
| NDS-UI-04 Need detail | `/app/departmental-needs/{need_reference}` | Read current and accepted Need state, Planning usage and permitted next action. |
| NDS-UI-05 Review task | `/app/departmental-needs/review/{review_task_id}` | Inspect the complete submitted version and make one departmental decision. |
| NDS-UI-06 Accepted source detail | `/app/departmental-needs/{need_reference}/accepted/{version_number}` | Read-only exact accepted version for Planning lineage. |
| NDS-UI-07 Withdrawal review | `/app/departmental-needs/review/{review_task_id}/withdrawal` | Inspect the full accepted Need, request reason and live Planning dependency. |
| NDS-UI-08 Intake window | `/app/departmental-needs/intake-window` | Maintain only the PE/FY open and close instants. |

The proven Vue-in-Frappe page pattern and approved KenTender design tokens shall be reused. This document does not authorise a second application shell, custom header, breadcrumb, global context selector or general Procurement Home dashboard.

## 11. Static Claude Design contract

This section is the complete input to Claude Design. It defines static visual compositions only. Runtime behaviour belongs to section 12 and shall not be pasted into a design prompt.

### 11.1 Closed-input rules

- Produce desktop artboards at **1440 × 1024 px**.
- Reuse the approved KenTender Strategy Portfolio visual system, spacing, type scale, tokens, cards, badges, tables, fields, buttons, tabs, empty states and dialogs.
- The artboard starts below the Frappe Desk header. Do not draw Frappe navigation, the Desk header, breadcrumb, user menu, notifications, Help, global search or the PE/FY workspace selector.
- Breadcrumb text is fixture data outside the artboard. It is supplied to confirm location only.
- Use only the visible labels, values, badges, controls, sections and states stated for that artboard.
- Do not invent data. If a value or state is not stated, omit it.
- Do not encode behaviour, validation, permissions, APIs, routing, transitions, concurrency or implementation instructions in the visual output.
- Do not add summary cards, charts, percentages, trend arrows, illustrations, side panels, steppers, timelines, helper panels, action menus, metadata or table columns unless explicitly stated.
- Do not show Budget Line, indicative amount, funding source, currency, Strategy, requirement type, procurement category, method, location, unit price, cost breakdown, availability, reservation, Requisition, Tender, contact, note, source reference or attachment.
- Generated identifiers may be displayed on saved records but never as editable fields.

The approved desktop shell inside every artboard is:

- full-width warm-white page background;
- a 1200 px maximum-width content column centred in the available page area;
- 32 px top and bottom page padding;
- page header followed by 24 px vertical spacing;
- 16 px gaps between cards or table sections; and
- no custom sidebar.

### 11.2 NDS-DES-01 — Requester workspace

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Need Requester · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 24 Nov 2026, 15:00 EAT · Frappe header breadcrumb: **Home > Departmental Needs**

**Page content header**

- Eyebrow: **DEPARTMENTAL NEEDS**
- Title: **My needs**
- Description: **Capture and track the requirements your department expects to include in procurement planning.**
- Right-aligned primary button: **Create need**

**Context strip**

| Label | Value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Department | OU-MOH-DHI — Digital Health |
| Financial Year | FY 2027/28 |
| Intake window | Open until 25 Nov 2026, 23:59 EAT |

**Filter row**

- Search input with placeholder: **Search title or reference**
- Status select showing: **All statuses**
- Secondary button: **Clear filters**

**My needs table**

| Need | Quantity | Required by | Status | Planning usage | Action |
|---|---:|---|---|---|---|
| NDS-MOH-2027-0001 · National digital health infrastructure upgrade | 1 programme | 31 Aug 2027 | Accepted for planning | Not included | View |
| NDS-MOH-2027-0004 · Clinical deployment laptops for digital health rollout | 300 each | 31 Dec 2027 | Draft | Not included | Continue |

Below the table: **2 needs** on the left. No pagination control.

### 11.3 NDS-DES-02 — Department review

**Fixture context — outside the artboard:** Dr Peter Kimani · `peter.kimani@moh.example.test` · Head of User Department · PE-MOH — Ministry of Health · OU-MOH-HRMD — Human Resources Management and Development · FY 2027/28 · 24 Nov 2026, 15:00 EAT · Frappe header breadcrumb: **Home > Departmental Needs > Review tasks**

**Page content header**

- Eyebrow: **DEPARTMENTAL NEEDS**
- Title: **Department review**
- Description: **Review submitted needs and view the department's current needs.**
- No header action button

**Context strip**

| Label | Value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Department | OU-MOH-HRMD — Human Resources Management and Development |
| Financial Year | FY 2027/28 |

**Tabs**

- **Review queue** — selected
- **Department needs**

**Review queue table**

| Need | Submitted by | Quantity | Required by | Status | Action |
|---|---|---:|---|---|---|
| NDS-MOH-2027-0002 · Digital health workforce certification programme | Grace Wanjiku | 1 programme | 31 Dec 2027 | Submitted | Review |

Below the table: **1 need awaiting review**. Do not show an assignee column, summary card or action menu.

**Department needs tab variant**

Use the same page header and context strip. Select **Department needs** and show:

- Search input with placeholder: **Search title or reference**
- Status select showing: **All statuses**
- Secondary button: **Clear filters**

| Need | Requester | Quantity | Required by | Status | Planning usage | Action |
|---|---|---:|---|---|---|---|
| NDS-MOH-2027-0002 · Digital health workforce certification programme | Grace Wanjiku | 1 programme | 31 Dec 2027 | Submitted | Not included | Review |
| NDS-MOH-2027-0003 · Clinical training laptops for digital health rollout | Grace Wanjiku | 200 each | 31 Dec 2027 | Returned | Not included | View |

Below the table: **2 department needs**. No pagination control.

### 11.4 NDS-DES-03 — Create need

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Need Requester · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 24 Nov 2026, 10:05 EAT · Frappe header breadcrumb: **Home > Departmental Needs > Create need**

**Page content header**

- Title: **Create need**
- Description: **Describe one requirement your department expects to include in procurement planning.**
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
| Title | National digital health infrastructure upgrade |
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Business justification | Improve availability and reliability of interoperable digital health services used by priority health facilities. |

Title uses one single-line input. Description and Business justification use separate multiline text areas.

**Quantity and timing card**

| Field label | Displayed value |
|---|---|
| Indicative quantity | 1 |
| Unit | Programme |
| Required by | 31 Aug 2027 |

Quantity and Unit appear side by side; Required by appears below them.

**Sticky page footer**

- Left-aligned secondary text button: **Cancel**
- Right-aligned secondary button: **Save draft**
- Right-aligned primary button: **Submit for review**

Do not show a Need reference, item table, add-item control, attachment, location or history.

### 11.5 NDS-DES-04 — Returned correction

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Need Requester · PE-MOH — Ministry of Health · OU-MOH-HRMD — Human Resources Management and Development · FY 2027/28 · 24 Nov 2026, 14:15 EAT · Frappe header breadcrumb: **Home > Departmental Needs > NDS-MOH-2027-0003 > Correct**

**Page content header**

- Eyebrow: **NDS-MOH-2027-0003 · VERSION 2**
- Title: **Clinical training laptops for digital health rollout**
- Status badge: **Returned**
- No header action button

**Return notice**

- Heading: **Returned for correction**
- Text: **Confirm the number of trainees to be supported and revise the laptop quantity if the approved training cohort has changed.**
- Detail: **Returned by Dr Peter Kimani · 24 Nov 2026, 13:35 EAT**

**Context card**

| Field label | Displayed value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Department | OU-MOH-HRMD — Human Resources Management and Development |
| Financial Year | FY 2027/28 |

**Requirement card**

| Field label | Displayed value |
|---|---|
| Title | Clinical training laptops for digital health rollout |
| Description | Laptop computers for clinical training during the national digital health rollout. |
| Business justification | Provide the equipment required for staff training on the deployed digital health services. |

**Quantity and timing card**

| Field label | Displayed value |
|---|---|
| Indicative quantity | 200 |
| Unit | Each |
| Required by | 31 Dec 2027 |

Use the same field components and arrangement as NDS-DES-03.

**Sticky page footer**

- Left-aligned destructive text button: **Withdraw need**
- Right-aligned secondary button: **Save changes**
- Right-aligned primary button: **Resubmit for review**

### 11.6 NDS-DES-05 — Submitted Need detail

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Need Requester · PE-MOH — Ministry of Health · OU-MOH-HRMD — Human Resources Management and Development · FY 2027/28 · 24 Nov 2026, 12:30 EAT · Frappe header breadcrumb: **Home > Departmental Needs > NDS-MOH-2027-0002**

**Page content header**

- Eyebrow: **NDS-MOH-2027-0002 · VERSION 1**
- Title: **Digital health workforce certification programme**
- Status badge: **Submitted**
- No header action button

**Waiting notice**

- Heading: **Awaiting departmental review**
- Text: **This version is read-only while it is in the department review queue.**
- Detail: **Submitted by Grace Wanjiku · 24 Nov 2026, 12:20 EAT**

**Context card**

| Label | Value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Department | OU-MOH-HRMD — Human Resources Management and Development |
| Financial Year | FY 2027/28 |

**Requirement card**

| Label | Value |
|---|---|
| Description | Professional certification programme for staff supporting national digital health services. |
| Business justification | Build internal capacity to operate and support national digital health platforms. |
| Indicative quantity | 1 programme |
| Required by | 31 Dec 2027 |

All values use read-only display rows. Do not show a footer action, reviewer name, Budget data, progress stepper or history panel.

### 11.7 NDS-DES-06 — Departmental review task

**Fixture context — outside the artboard:** Dr Peter Kimani · `peter.kimani@moh.example.test` · Head of User Department · PE-MOH — Ministry of Health · OU-MOH-HRMD — Human Resources Management and Development · FY 2027/28 · 24 Nov 2026, 12:35 EAT · Frappe header breadcrumb: **Home > Departmental Needs > Review tasks > NDS-MOH-2027-0002**

**Page content header**

- Eyebrow: **DEPARTMENTAL REVIEW · NDS-MOH-2027-0002 · VERSION 1**
- Title: **Digital health workforce certification programme**
- Status badge: **Submitted**
- No header action button

**Submission strip**

| Label | Value |
|---|---|
| Submitted by | Grace Wanjiku |
| Submitted | 24 Nov 2026, 12:20 EAT |
| Department | Human Resources Management and Development |
| Financial Year | FY 2027/28 |

**Requirement card**

| Label | Value |
|---|---|
| Description | Professional certification programme for staff supporting national digital health services. |
| Business justification | Build internal capacity to operate and support national digital health platforms. |
| Indicative quantity | 1 programme |
| Required by | 31 Dec 2027 |

**Decision card**

- Heading: **Departmental decision**
- Prompt: **Should this requirement be made available to Procurement Planning?**

**Sticky page footer**

- Left-aligned secondary button: **Return for correction**
- Right-aligned destructive secondary button: **Do not take forward**
- Right-aligned primary button: **Accept for planning**

The entire submitted Need is visible on this artboard. Do not show editable fields, a reason input, score, recommendation, Budget data, Strategy or Planning classification.

### 11.8 NDS-DES-07 — Accepted Need detail

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Need Requester · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 5 Jan 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Departmental Needs > NDS-MOH-2027-0001**

**Page content header**

- Eyebrow: **NDS-MOH-2027-0001 · ACCEPTED VERSION 1**
- Title: **National digital health infrastructure upgrade**
- Status badge: **Accepted for planning**
- Right-aligned secondary button: **Create update**
- Right-aligned secondary button: **Request withdrawal**

**Acceptance strip**

| Label | Value |
|---|---|
| Accepted by | Dr Peter Kimani |
| Accepted | 24 Nov 2026, 14:00 EAT |
| Department | Digital Health |
| Financial Year | FY 2027/28 |

**Requirement card**

| Label | Value |
|---|---|
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Business justification | Improve availability and reliability of interoperable digital health services used by priority health facilities. |
| Indicative quantity | 1 programme |
| Required by | 31 Aug 2027 |

**Planning usage card**

- Heading: **Procurement Planning**
- Badge: **Fully included**
- Text: **This accepted version is included in the Active Annual Procurement Plan.**
- Reference: **PPI-MOH-2027-021 · National digital health infrastructure upgrade**
- Right-aligned secondary button: **View Plan Item**

All fields are read-only. Do not show a version-history table, source hash, Plan classification, Strategic Objective or Finance position.

### 11.9 NDS-DES-08 — Accepted Need update draft

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Need Requester · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 15 Dec 2026, 09:10 EAT · Frappe header breadcrumb: **Home > Departmental Needs > NDS-MOH-2027-0001 > Create update**

**Page content header**

- Eyebrow: **NDS-MOH-2027-0001 · VERSION 2**
- Title: **Update accepted need**
- Status badge: **Draft update**
- No header action button

**Current-version notice**

- Heading: **Accepted Version 1 remains in use**
- Text: **The proposed Version 2 is shown below.**

**Context card**

| Field label | Displayed value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Department | OU-MOH-DHI — Digital Health |
| Financial Year | FY 2027/28 |

**Requirement card**

| Field label | Displayed value |
|---|---|
| Title | National digital health infrastructure upgrade |
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Business justification | Improve availability and reliability of interoperable digital health services used by priority health facilities. |

**Quantity and timing card**

| Field label | Displayed value |
|---|---|
| Indicative quantity | 1 |
| Unit | Programme |
| Required by | 15 Sep 2027 |

Use the same components and arrangement as NDS-DES-03.

**Sticky page footer**

- Left-aligned secondary text button: **Cancel update**
- Right-aligned secondary button: **Save draft**
- Right-aligned primary button: **Submit update for review**

### 11.10 NDS-DES-09 — Accepted Need update review

**Fixture context — outside the artboard:** Dr Peter Kimani · `peter.kimani@moh.example.test` · Head of User Department · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 15 Dec 2026, 10:05 EAT · Frappe header breadcrumb: **Home > Departmental Needs > Review tasks > NDS-MOH-2027-0001 > Version 2**

**Page content header**

- Eyebrow: **DEPARTMENTAL REVIEW · NDS-MOH-2027-0001 · VERSION 2**
- Title: **National digital health infrastructure upgrade**
- Status badge: **Update submitted**
- No header action button

**Submission strip**

| Label | Value |
|---|---|
| Submitted by | Grace Wanjiku |
| Submitted | 15 Dec 2026, 09:45 EAT |
| Current accepted version | Version 1 |
| Proposed version | Version 2 |

**Changes card**

| Field | Accepted Version 1 | Proposed Version 2 |
|---|---|---|
| Required by | 31 Aug 2027 | 15 Sep 2027 |

**Proposed requirement card**

| Label | Value |
|---|---|
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Business justification | Improve availability and reliability of interoperable digital health services used by priority health facilities. |
| Indicative quantity | 1 programme |
| Required by | 15 Sep 2027 |

**Decision card**

- Heading: **Departmental decision**
- Prompt: **Should Version 2 replace Accepted Version 1 for Procurement Planning?**

**Sticky page footer**

- Left-aligned secondary button: **Return for correction**
- Right-aligned destructive secondary button: **Do not take forward**
- Right-aligned primary button: **Accept updated version**

Do not collapse the full proposed details into the Changes table. Do not show editable fields or a reason input.

### 11.11 NDS-DES-10 — Intake window

**Fixture context — outside the artboard:** Amina Hassan · `amina.hassan@moh.example.test` · Needs Configuration Manager · PE-MOH — Ministry of Health · FY 2027/28 · 24 Nov 2026, 15:00 EAT · Frappe header breadcrumb: **Home > Departmental Needs > Intake window**

**Page content header**

- Eyebrow: **DEPARTMENTAL NEEDS CONFIGURATION**
- Title: **Intake window**
- Description: **Set when departments may create and initially submit needs for this Financial Year.**
- Status badge: **Open**
- No header action button

**Context card**

| Field label | Displayed value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Financial Year | FY 2027/28 |

Both rows use read-only field components.

**Window card**

| Field label | Displayed value |
|---|---|
| Opens at | 1 Sep 2026, 00:00 EAT |
| Closes at | 25 Nov 2026, 23:59 EAT |

Both rows use the approved date-time component.

**Page footer**

- Right-aligned primary button: **Save window**

Do not show a title, description, manual status, reason, source reference, approval field, attachment, audit panel or module-readiness card.

### 11.12 NDS-DES-11 — Withdrawal request dialog

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · NDS-MOH-2027-0001 · Accepted Version 1 · 5 Jan 2027, 10:20 EAT · Frappe header breadcrumb: **Home > Departmental Needs > NDS-MOH-2027-0001**

Show NDS-DES-07 dimmed behind a centred modal.

**Modal**

- Title: **Request withdrawal**
- Introductory text: **Explain why this accepted need should no longer be used for procurement planning.**
- Field label: **Reason**
- Text-area value: **The programme will not proceed in FY 2027/28 because implementation responsibility has moved outside the department.**
- Left footer button: **Cancel**
- Right primary footer button: **Submit request**

Do not show an attachment, source reference, Planning selector, approval checkbox or second field.

### 11.13 NDS-DES-12 — Withdrawal review

#### Blocked variant

**Fixture context — outside the artboard:** Dr Peter Kimani · `peter.kimani@moh.example.test` · Head of User Department · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 5 Jan 2027, 10:30 EAT · Frappe header breadcrumb: **Home > Departmental Needs > Review tasks > Withdraw NDS-MOH-2027-0001**

**Page content header**

- Eyebrow: **WITHDRAWAL REVIEW · NDS-WDR-MOH-2027-0001**
- Title: **National digital health infrastructure upgrade**
- Status badge: **Awaiting planning clearance**
- No header action button

**Request card**

| Label | Value |
|---|---|
| Requested by | Grace Wanjiku |
| Requested | 5 Jan 2027, 10:20 EAT |
| Reason | The programme will not proceed in FY 2027/28 because implementation responsibility has moved outside the department. |

**Accepted Need card**

| Label | Value |
|---|---|
| Accepted version | Version 1 |
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Business justification | Improve availability and reliability of interoperable digital health services used by priority health facilities. |
| Indicative quantity | 1 programme |
| Required by | 31 Aug 2027 |

**Planning dependency card**

- Heading: **Active Plan inclusion must be cleared**
- Badge: **Fully included**
- Text: **The accepted Need is represented by the following Active Plan Item.**
- Reference: **PPI-MOH-2027-021 · National digital health infrastructure upgrade**
- Secondary button: **View Plan Item**

**Page footer**

- Right-aligned secondary button: **Close**

Do not show **Approve withdrawal** or **Decline withdrawal** on the blocked variant.

#### Cleared variant

Use the same context, header, Request card and Accepted Need card with these exact changes:

- Status badge: **Awaiting review**
- Planning dependency card heading: **No Active Plan inclusion**
- Planning dependency badge: **Not included**
- Planning dependency text: **This accepted Need is not represented in an Active Plan.**
- Omit the Plan Item reference and **View Plan Item** button.
- Footer buttons: left-aligned secondary **Decline withdrawal**; right-aligned primary **Approve withdrawal**.

### 11.14 NDS-DES-13 — Decision dialogs

Produce two separate 520 px wide modal artboards over a dimmed NDS-DES-06 background.

**Return for correction dialog**

- Title: **Return for correction**
- Text: **Explain what the requester must correct before resubmission.**
- Field label: **Reason**
- Exact value: **Confirm the number of staff covered by the programme and update the description if the approved training cohort has changed.**
- Footer buttons: **Cancel** and primary **Return need**

**Do not take forward dialog**

- Title: **Do not take forward**
- Text: **Explain why this requirement should not proceed to procurement planning.**
- Field label: **Reason**
- Exact value: **The requirement is already covered by an existing enterprise service for FY 2027/28.**
- Footer buttons: **Cancel** and destructive **Do not take forward**

Do not add a reason field to the Accept action.

### 11.15 NDS-DES-14 — Common workspace states

Produce four separate variants using the NDS-DES-01 shell, page header and context position.

| Variant | Exact visible content |
|---|---|
| Loading | Table card with the text **Loading departmental needs…** and approved skeleton rows. |
| Empty | Heading **No departmental needs yet**; text **Create the first need for this department and Financial Year.**; primary button **Create need**. |
| Intake closed | Context strip value **Intake window · Closed 25 Nov 2026, 23:59 EAT**; omit **Create need**; retain the exact existing rows. |
| No authorised context | Heading **Departmental Needs is not available**; text **You do not have an active Departmental Needs assignment for a configured Procuring Entity, department and Financial Year.**; no table or action. |
| Error | Heading **Departmental Needs could not be loaded**; text **Try again. If the problem continues, contact support.**; secondary button **Try again**. |

### 11.16 Existing Frappe and KenTender controls

Frappe supplies the Desk header, breadcrumb, session controls, route lifecycle, dialogs, toasts and accessibility primitives. KenTender supplies the established tokens and shared Vue components. Claude Design supplies only the page content defined in sections 11.2–11.15.

## 12. Functional interaction requirements — excluded from design prompts

### 12.1 NDS-UI-01 — Requester workspace

- Resolve eligible contexts from effective requester assignments and configured PE/FY Contexts. Restore a saved selection only if it remains authorised.
- One eligible context loads directly. Several require explicit selection in the existing Frappe/KenTender context control before rows are requested. None renders the no-authorised-context state.
- Load only the actor's Needs in the selected PE/OU/FY. Search matches title or reference. Status is the only list filter.
- **Create need** is available only while the Needs intake window is Open. It routes to NDS-UI-03 with the resolved immutable context.
- **Continue** and **Correct** route to the actor's editable current version. **View** routes to NDS-UI-04.
- Submitted, accepted, terminal and another actor's versions are never editable through a direct URL.
- Intake close removes new creation and initial submission; it does not hide existing authorised records.

### 12.2 NDS-UI-02 — Department review

- The review queue returns only Open tasks in the actor's exact effective departmental-review scope after maker-checker exclusion.
- The department register returns authorised Needs in that same PE/OU/FY. It does not grant actions outside an Open task.
- A delegate sees only tasks covered by the exact current delegation. A role label alone returns no queue.
- **Review** carries the stable task ID and current decision token to NDS-UI-05 or NDS-UI-07.
- A successful decision removes the task from the queue. A concurrent decision returns `NDS_STALE_WRITE` and reloads the current neutral result.
- Counts, queue rows and register rows use the same database scope predicate.

### 12.3 NDS-UI-03 — Need editor

- First save requires resolved context and a valid title. It creates the root and Draft Version 1, then replaces the route with the generated Need reference.
- A partial Draft may be saved after the title is valid. Submission requires all six values.
- Unit options come from the governed active unit catalogue.
- Submit revalidates assignment, state, unit, FY date, maker-checker route and intake/correction rule on the server. It performs no Budget service call.
- The UI disables the initiating button while the command is pending and uses one idempotency key for retries.
- Field errors bind to exact controls. A business-rule error appears in the approved error summary and moves focus there.
- A successful initial submit or resubmit routes to NDS-UI-04. A successful accepted-update submit routes to NDS-UI-04 while the earlier accepted version remains displayed as current.
- Return creates a copied successor Draft server-side. The returned editor loads that copy and the immutable return reason; it never unlocks the submitted snapshot.
- **Cancel** on a new unsaved form creates no mutation. **Cancel update** confirms and withdraws the open Draft successor, leaving the accepted version current. Withdrawal before acceptance requires confirmation and routes to the read-only terminal detail after success.

### 12.4 NDS-UI-04 and NDS-UI-06 — Need detail

- Detail resolves the stable Need, current root state, current accepted version, open successor state and Planning usage independently.
- A Submitted version shows the exact immutable submitted content and no requester mutation.
- Accepted detail shows the exact accepted version even when a Draft/Submitted successor exists. The successor is represented by a clear status notice and a link available only to its maker.
- **Create update** appears only to the originator when the Need is Accepted and no open successor exists.
- **Request withdrawal** appears only to the originator when the Need is Accepted and no withdrawal request is open.
- **View Plan Item** uses the exact route returned by the Planning usage projection. It is absent for `Not included`.
- The Planning deep link to NDS-UI-06 fixes the accepted version in the route. If it is superseded, the page remains historically readable and clearly labels the current accepted version without redirecting or rewriting the requested version.
- Direct links enforce the same scope as service reads and return Not found when existence disclosure is unauthorised.

### 12.5 NDS-UI-05 — Review task

- Load the exact immutable submitted version identified by the task, not mutable root fields.
- Render all six requester-entered fields before the decision area.
- Return opens the exact Return dialog; decline opens the exact Do-not-take-forward dialog. Accept opens a standard confirmation dialog containing Need reference, version and the fixed statement **Acceptance makes this version available to Procurement Planning. It does not approve expenditure or create procurement authority.**
- No Accept reason, recommendation, checklist or score is collected.
- Decision commands revalidate task token, assignment, maker-checker, Need state and unit under one transaction.
- Accept initial version routes to accepted detail. Accept successor routes to the new accepted detail and publishes supersession lineage.
- Returning an initial or successor version creates the next Draft copy atomically and notifies the maker.
- Declining an initial version closes the Need. Declining a successor leaves the earlier accepted version current.

### 12.6 NDS-UI-07 — Withdrawal review

- Load the exact request, complete accepted Need version and a fresh Planning dependency result.
- The page never relies on a cached button state to authorise approval.
- If an Active Plan dependency exists, the command records/retains `Awaiting planning clearance`, returns the exact Plan/Plan Item reference and exposes no Departmental Needs action that edits Planning.
- **View Plan Item** navigates only. The existing Planning amendment process clears the dependency.
- Approve rechecks that no Active Plan dependency exists, then withdraws the Need and publishes the event in one transaction.
- Decline requires the exact decision dialog reason, leaves the accepted version current and completes the review task.
- The requester cannot decide their own withdrawal request.

### 12.7 NDS-UI-08 — Intake window

- Resolve PE/FY options only from the actor's effective Needs-configuration assignments and active PE/FY Contexts.
- Save validates `closes_at > opens_at`, converts displayed EAT values to UTC and uses optimistic concurrency.
- Moving or closing a window does not rewrite, delete or hide an existing Need.
- Initial create and submit commands evaluate the window at their server clock instant. The end instant is inclusive.
- The page exposes no manual status command or approval lifecycle.

### 12.8 Common page behaviour and accessibility

- Use semantic headings, labels, tables, status text and keyboard-operable controls. Colour is never the only carrier of state.
- Dialog focus is trapped and restored. Validation focus moves to the first invalid control or error summary.
- Loading, empty, intake-closed, no-authorised-context and error states use the exact copy in NDS-DES-14.
- All dates display in `Africa/Nairobi`; service and audit instants remain UTC.
- Do not wait for `networkidle` on a Frappe Desk page. Tests wait for DOM content plus the exact page-ready selector.
- Route changes unmount the Vue app and cancel stale requests. Returning to a cached Desk page re-resolves context and authorization.

## 13. Audit and historical integrity

- Framework audit fields identify record creation and technical updates. DepartmentalNeedDecision records business transitions.
- Draft autosaves or routine saves do not create user-authored notes. Material command audit includes actor, effective assignment, command, correlation ID, record token, prior/result state and submitted content hash.
- Submitted content is immutable. Return creates a copied Draft successor; it never makes the submitted row editable.
- Accepted content is immutable. A replacement becomes effective only through successor acceptance.
- Decision reasons remain attached to their exact decision and version. They are not copied into the next Draft as an editable field.
- Planning events preserve Need/version/hash lineage. Projection events never alter Need content or decision history.
- Timestamps and actors are system-generated. A client cannot supply or amend them.
- Submitted, accepted, superseded, terminal and withdrawal records are not physically deleted.
- Auditor and System Administrator reads do not imply a business action. Standard technical access logging applies; no invented support-reason form is required.

## 14. Deterministic seed contract

### 14.1 Configuration prerequisites

| Fixture | Exact value |
|---|---|
| Procuring Entity | `PE-MOH` — Ministry of Health |
| Financial Year | `FY-2027-2028` — FY 2027/28 · 1 Jul 2027 to 30 Jun 2028 |
| OU 1 | `OU-MOH-DHI` — Digital Health |
| OU 2 | `OU-MOH-HRMD` — Human Resources Management and Development |
| Unit 1 | `UNIT-PROGRAMME` — Programme |
| Unit 2 | `UNIT-EACH` — Each |
| Needs intake window | 1 Sep 2026, 00:00:00 EAT to 25 Nov 2026, 23:59:59 EAT inclusive |
| Design clock | `2026-11-24T12:00:00Z` · 24 Nov 2026, 15:00 EAT unless an artboard states another exact time |

The PE, FY, OUs, units and assignments come from Configuration & Governance. Seeds fail if any authoritative prerequisite differs; they do not invent fallback records.

### 14.2 Actors and assignments

| Actor | Exact assignment |
|---|---|
| `grace.wanjiku@moh.example.test` · Grace Wanjiku | Departmental Need Requester for PE-MOH / OU-MOH-DHI and OU-MOH-HRMD / FY 2027/28 |
| `peter.kimani@moh.example.test` · Dr Peter Kimani | Head of User Department for both named OUs / FY 2027/28 |
| `julia.njeri@moh.example.test` · Julia Njeri | Departmental Review Delegate for OU-MOH-DHI from 1 Oct to 30 Nov 2026 |
| `amina.hassan@moh.example.test` · Amina Hassan | Needs Configuration Manager for PE-MOH / FY 2027/28 |
| `mercy.kilonzo@moh.example.test` · Mercy Kilonzo | Procurement Planner for PE-MOH / FY 2027/28; accepted-source contract and exact detail link only |
| `auditor.moh@example.test` · MOH Auditor | Read-only audit scope for PE-MOH / FY 2027/28 |
| `requester.cgk@example.test` · CGK Requester | Separate PE-CGK scope used only for isolation tests |

No actor receives authority merely because they are Administrator or because a context selector contains a value.

### 14.3 Default Needs

| Reference | Department | Title | Quantity | Required by | State | Planning usage |
|---|---|---|---:|---|---|---|
| `NDS-MOH-2027-0001` | Digital Health | National digital health infrastructure upgrade | 1 programme | 31 Aug 2027 | Accepted for planning | Not included at design clock |
| `NDS-MOH-2027-0002` | HR Management and Development | Digital health workforce certification programme | 1 programme | 31 Dec 2027 | Submitted | Not included |
| `NDS-MOH-2027-0003` | HR Management and Development | Clinical training laptops for digital health rollout | 200 each | 31 Dec 2027 | Returned; editable Version 2 | Not included |
| `NDS-MOH-2027-0004` | Digital Health | Clinical deployment laptops for digital health rollout | 300 each | 31 Dec 2027 | Draft Version 1 | Not included |

Exact descriptions and justifications:

| Reference | Description | Business justification |
|---|---|---|
| NDS-MOH-2027-0001 | Procure and implement national digital health infrastructure across priority health facilities. | Improve availability and reliability of interoperable digital health services used by priority health facilities. |
| NDS-MOH-2027-0002 | Professional certification programme for staff supporting national digital health services. | Build internal capacity to operate and support national digital health platforms. |
| NDS-MOH-2027-0003 | Laptop computers for clinical training during the national digital health rollout. | Provide the equipment required for staff training on the deployed digital health services. |
| NDS-MOH-2027-0004 | Laptop computers for deployment at priority facilities during the national digital health rollout. | Provide endpoint equipment required to use the deployed digital health services. |

NDS-MOH-2027-0001 Version 1 is accepted by Dr Peter Kimani on 24 Nov 2026 at 14:00 EAT. NDS-MOH-2027-0002 is submitted by Grace Wanjiku on 24 Nov 2026 at 12:20 EAT. NDS-MOH-2027-0003 Version 1 is returned by Dr Peter Kimani on 24 Nov 2026 at 13:35 EAT with the exact NDS-DES-04 reason; Version 2 is the server-created editable copy.

### 14.4 Integrated Planning usage fixture

An integration profile projects NDS-MOH-2027-0001 Version 1 to:

- usage: `Fully included`;
- Active Plan: `PLN-MOH-2027-001`, Active Version 1; and
- Plan Item: `PPI-MOH-2027-021` — National digital health infrastructure upgrade.

That profile is used by NDS-DES-07 and NDS-DES-12. It is not loaded into tests that expect the design-clock default `Not included` value.

### 14.5 Isolated successor and withdrawal fixtures

The successor profile copies NDS-MOH-2027-0001 Version 1 into Version 2 and changes only:

| Field | Version 1 | Version 2 |
|---|---|---|
| Required by | 31 Aug 2027 | 15 Sep 2027 |

Acceptance emits the exact supersession event without altering Version 1.

The withdrawal profile creates `NDS-WDR-MOH-2027-0001` with the exact NDS-DES-11 reason. Its blocked variant uses the Active Plan dependency in section 14.4; its cleared variant supplies `Not included` and no Plan references.

Terminal-state, stale-write, concurrent-decision, expired-delegation, window-boundary and PE-CGK isolation records exist only in named isolated test profiles. They are not added to the default four-row workspace fixture.

Direct departmental requirement fixtures belong to Procurement Planning and create no Departmental Needs seed record. The Planning integration profile must prove a DPP containing only direct requirements and another containing both source origins without changing the four Needs above.

### 14.6 Seed execution rules

- Seed keys and timestamps are deterministic and idempotent.
- Seed scripts call domain builders or public commands that enforce the same invariants as production setup.
- Default, Planning usage, successor, withdrawal and negative profiles are independently selectable and resettable.
- No seed creates a legacy Demand, partial Need allocation, reservation, Requisition or Tender.
- No test changes the process clock, current accepted version or Planning usage without restoring its isolated transaction or fixture namespace.

## 15. Acceptance contract

| ID | Acceptance criterion |
|---|---|
| NDS-AC-001 | One Need contains exactly the six requester-entered values in section 2.2 and no item child table or funding field. |
| NDS-AC-002 | Context is explicit and server-authorised; first-record, current-FY and Administrator fallbacks do not exist. |
| NDS-AC-003 | Initial create and submit succeed only inside the configured Needs intake window, including its exact inclusive boundaries. |
| NDS-AC-004 | A valid partial Draft saves after title; submission rejects every missing required value without side effects. |
| NDS-AC-005 | Required-by must be inside the target FY and quantity must be positive. |
| NDS-AC-006 | Unit is selected only from the active governed catalogue; no free-text `Other` value is stored. |
| NDS-AC-007 | Need creation, submission, review, acceptance, payload and screens contain no Budget Line, indicative amount, funding source or currency. |
| NDS-AC-008 | Need save, submit and acceptance create no funding reservation or availability check. |
| NDS-AC-009 | Submit creates one immutable version/hash, one scoped review task and one notification effect atomically and idempotently. |
| NDS-AC-010 | A version maker cannot decide that version; expired or cross-scope review assignments fail closed. |
| NDS-AC-011 | Return requires a reason, preserves the submitted version and creates one copied correction Draft. |
| NDS-AC-012 | Decline requires a reason. Accept collects no reason, score, recommendation or checklist. |
| NDS-AC-013 | Accept for planning creates no Plan Item, Strategic Objective selection, classification, Requisition or Tender. |
| NDS-AC-014 | When Planning consumes a Need, it uses only the current accepted version at the full accepted quantity. Partial Need usage does not exist. |
| NDS-AC-015 | Planning usage is independent of lifecycle and is only `Not included` or `Fully included`. |
| NDS-AC-016 | An accepted version is immutable; an open successor does not replace it before acceptance. |
| NDS-AC-017 | Successor acceptance atomically supersedes the earlier version and publishes exact old/new lineage. |
| NDS-AC-018 | Successor decline leaves the earlier accepted version current. |
| NDS-AC-019 | Accepted withdrawal is maker-checked and cannot complete while an exact Active Plan dependency exists. |
| NDS-AC-020 | Planning clearance occurs only in Procurement Planning; Departmental Needs exposes no foreign-module mutation. |
| NDS-AC-021 | Search, counts, rows, detail, export and service access use the same server-side scope predicate. |
| NDS-AC-022 | Requester, reviewer, delegate, configuration, Planner deep-link, auditor and System Administrator permissions match section 6 exactly. |
| NDS-AC-023 | Budget Officer and Accounting Officer receive no Departmental Needs workspace, task or special action. |
| NDS-AC-024 | The Planning source payload contains no Budget Line, amount, funding source, currency, Strategy, requirement type, business justification, generic evidence, location or attachment. |
| NDS-AC-025 | NDS-DES-01 through NDS-DES-14 render only their exact fixtures and exclusions. |
| NDS-AC-026 | Breadcrumb and Frappe header remain outside every Claude Design artboard and use the existing framework components. |
| NDS-AC-027 | Runtime behaviour is implemented from section 12, not inferred from static design output. |
| NDS-AC-028 | Stale, duplicate and concurrent commands create no overwritten version, duplicate task, duplicate event or duplicate decision. |
| NDS-AC-029 | No delivery location, attachment, source reference, notes, contact, Strategy, classification or line-item field exists. |
| NDS-AC-030 | No `/demands`, `/departmental-needs` or `/desk/departmental-needs` compatibility route exists. |
| NDS-AC-031 | The existing Planning shell and Plan Item UI are reused; the Planning contract adds the direct-requirement editor and Budget Line/indicative-amount enrichment for accepted-Need entries. |
| NDS-AC-032 | A fresh environment creates the exact clean schema and selectable seed profiles without a legacy prerequisite. |
| NDS-AC-033 | Cancelling a Draft accepted successor withdraws only that successor and leaves the earlier accepted version current. |
| NDS-AC-034 | A HoD or authorised departmental plan preparer can create a Planning-owned direct departmental requirement without a Departmental Need. |
| NDS-AC-035 | A DPP and its Plan Items may be formed entirely from direct departmental requirements, entirely from accepted Needs, or from both source origins. |
| NDS-AC-036 | A direct departmental requirement creates no synthetic Need, Need review task, bypass reason or Need audit event. |
| NDS-AC-037 | Accepted-Need entries retain Need/version/hash lineage; direct entries retain DPP-entry lineage and are never presented as accepted Needs. |

### 15.1 Minimum automated coverage

| Test layer | Minimum coverage |
|---|---|
| Domain unit | Field validation, date, quantity, lifecycle, root/accepted/successor pointers, withdrawal dependency and usage projection. |
| Permission unit | Own vs department vs delegated vs Planner contract vs auditor, cross-OU/PE/FY denial and maker-checker. |
| Command integration | Draft, submit, return-copy, resubmit, accept, decline, successor, withdrawal, intake save, idempotency and concurrency. |
| Contract integration | Accepted/superseded/withdrawn events, Planning usage event, stale hash, accepted-Need Planning enrichment, direct-only DPP and mixed-origin DPP. |
| UI component | Exact fields, read-only derived values, role tables, dialogs, button states and no forbidden controls. |
| Browser smoke | Frappe login → route → create/submit; reviewer opens full detail and returns/accepts; successor comparison; withdrawal blocked/cleared; no console or own-request errors. |
| Visual regression | 1440 × 1024 references for every design artboard, modal and workspace state. |

## 16. Implementation and test constraints

### 16.1 Frappe and UI implementation

- Implement domain records as explicit Frappe DocTypes with server-side controllers/services; do not store business state in client-only objects.
- Mount Vue 3 pages through the existing `frappe.ui.make_app_page()` → built bundle → `createApp().mount()` pattern already proven by the Strategy pilot.
- Port Claude Design markup and design tokens into scoped Vue single-file components. Design export runtime files remain design evidence under `docs/` and are not imported into production.
- Reuse the existing KenTender page header, context strip, fields, buttons, badges, tables, dialogs, states and token chain before creating a module-local component.
- Keep component styles scoped beneath one Departmental Needs root. Do not add Tailwind Preflight, a CDN, global element resets or rules that restyle Frappe Desk.
- Use Frappe RPC/resource APIs for authorised services. Do not expose writable DocType endpoints that bypass commands.
- Register only the canonical routes in section 10. Page controllers unmount Vue and detach listeners before remount.
- Add stable accessible test selectors to page-ready state, field controls, tables, dialogs and primary commands. Do not select by visual CSS classes.

### 16.2 TDD and efficient verification

For each behavior change:

1. write or identify the smallest failing test that proves the rule;
2. run that test file or exact test node;
3. implement the minimum coherent fix;
4. rerun the same focused test;
5. run the directly affected domain or component group;
6. run the one relevant browser smoke and screenshot when UI changed; and
7. run the Departmental Needs module suite once after the focused group is green.

Do not rerun the whole repository suite, all browser tests or every screenshot after each small fix. The broader integrated suite runs at the release gate or when a shared contract/component changed.

Required test commands shall be documented in the repository test map as:

- exact domain test node;
- Departmental Needs domain group;
- exact Vue component test;
- exact Playwright scenario;
- Departmental Needs module suite; and
- integrated release suite.

When a failure occurs, preserve the first useful traceback, server response, browser console error and screenshot. Classify it as product, fixture, selector, environment or unrelated failure before changing code. Do not “fix” a product screen to satisfy an ambiguous selector.

### 16.3 Required release evidence

- targeted red/green test record for every acceptance criterion changed during implementation;
- clean Departmental Needs module suite;
- clean accepted-source and Planning contract tests;
- successful production-mode asset build;
- scripted browser smoke with zero Departmental Needs page console errors and zero failed own requests;
- visual comparison for all approved artboards at 1440 × 1024; and
- schema scan proving every prohibited field, object and legacy route is absent.

## 17. Prohibited shortcuts

- Do not preserve the item child table as a hidden or single-row implementation.
- Do not store Budget Line, indicative amount, funding source, currency, delivery location, attachments, `other_unit`, Strategy, classification, generic notes, source reference or evidence “for later”.
- Do not calculate or display Budget availability inside Departmental Needs.
- Do not create a reservation, Plan Item, Requisition or Tender from a Need command.
- Do not require a synthetic Need, Need acceptance or bypass reason before Planning may capture a direct departmental requirement.
- Do not implement the direct-requirement editor inside Departmental Needs; it belongs to the DPP workspace in Procurement Planning.
- Do not edit an accepted or submitted snapshot in place.
- Do not let Planning query Departmental Needs tables or mutate a Need.
- Do not infer role authority from a UI tab, route, role label, ownership alone or Administrator status.
- Do not implement a Planner, Budget Officer, Accounting Officer or support dashboard in this module.
- Do not introduce `Partially included`, quantity override or a Plan allocation child table.
- Do not copy runtime rules into Claude Design prompts or infer runtime behavior from generated HTML.
- Do not import Claude Design canvas runtime files into production.
- Do not create a second Frappe header, breadcrumb, shell or global context selector.
- Do not add compatibility redirects, legacy Demand fields, migration branches, dual reads or fallback fixtures.
- Do not run hundreds of unrelated tests after each small correction.

## 18. Traceability and precedence

This document is the single Departmental Needs authority. Its requirement, design, interaction, seed and implementation sections are mutually controlling parts of one specification.

Where another approved module document owns a value or decision, its domain authority prevails for that value:

1. Configuration & Governance for PE/FY/OU/unit/capability identity;
2. Budget & Funding v1.1 for Budget Line identity, funding source and currency as consumed by Procurement Planning, subject to the ownership correction in section 7.3;
3. this document for Need capture, review, versions and withdrawal;
4. Strategy Alignment v1.3 for Strategic Objectives; and
5. Procurement Planning canonical/functional contracts for DPP, classification, Plan Items, Finance and Active Plan usage, as corrected by the accepted-source boundary in section 7.

If an implementation ambiguity would add a field, action, screen, object or role, the default answer is **omit it** until a current operational purpose, named consumer, validation and effect are approved.
