# PLN-CHG-001 — Clean Procurement Planning

| Control | Value |
|---|---|
| Document ID | PLN-CHG-001 |
| Version | 1.2 |
| Date | 30 August 2026 |
| Status | Proposed for approval |
| Change type | Complete consolidated successor to approved v1.1 |
| Module | Procurement Planning |
| Implementation posture | Correct the existing module in place; reuse the proven Planning UI and Claude Design → Vue 3 → Frappe Desk pattern |

**Controlling decision:** Procurement Planning turns departmental requirements into one funded, governed Annual Procurement Plan with the fewest necessary user actions. A Departmental Procurement Plan may contain accepted Departmental Needs, direct departmental requirements, or both. Departmental Needs supports consultation but is not a prerequisite for planning. When the first DPP is accepted, the system automatically creates the initial Draft Annual Procurement Plan and places the accepted entries in its unallocated-source queue. The Planner begins with the meaningful work of forming Plan Items; there is no separate **Begin consolidation** gate. Planning owns requirement classification, the Budget Line and indicative amount on each departmental-plan entry, formation of Plan Items, selection of one Strategic Objective per Plan Item, Finance confirmation, Accounting Officer adoption, one applicable statutory approval, system publication and the approved lineage exposed to Procurement Requisitions.

## 1. Governing decision

On approval, this complete document becomes the single implementation authority for Procurement Planning. It consolidates approved v1.1 with the lifecycle, reservation, segregation, context and navigation corrections defined here, and replaces the Planning documents listed in section 18 wherever they conflict with it.

The existing application is corrected in place. Proven page structure, components, visual tokens and working Planning interactions are reused where they conform. Removed concepts are deleted rather than renamed, aliased, dual-read or retained behind feature flags.

Completion requires one coherent result across schema, services, permissions, screens, fixtures and tests. A field, action, object, service, queue or screen not defined here is outside the module.

### 1.1 Conflict and disposition register

| Earlier item | Disposition in v1.2 |
|---|---|
| Every DPP entry and Plan Item must originate from an accepted Need | Correct. A DPP entry originates from either an `Accepted Departmental Need` or a `Direct departmental requirement`. |
| Accepted Need carries Strategy, requirement type, Budget Line, funding source, currency and amount into Planning | Remove. The Need supplies title, description, expected operational result, quantity, unit and required-by date only. Planning adds the Budget Line and indicative amount; the Procurement Planner classifies the entry; the Planner selects the Strategic Objective on the Plan Item. |
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
| 71 separately specified Stitch frames | Replace with the smaller Claude Design contract in section 11. State variants are functional requirements unless a visually distinct artboard is explicitly required. |
| Stitch/Tailwind markup imported into Frappe | Replace with Claude Design as visual evidence, then Vue 3 SFCs mounted in Frappe Desk. No design-runtime file is shipped. |
| Breadcrumb drawn inside the artboard | Remove. Breadcrumb is fixture data outside the artboard and is rendered by the existing Frappe header. |
| Plan approval page shows only a summary | Correct. Every review, certification and approval task shows the complete submitted Plan details before its decision controls. |
| Separate professional-review stage before the Accounting Officer | Remove. It creates no distinct statutory decision in this Planning chain. |
| Head of Procurement Function approves the Annual Plan | Remove. The Head of Procurement Function is not an Annual Plan approval stage. |
| Publication Operator as a business role | Remove. Publication is an idempotent system action after statutory approval. |
| Separate departmental preparer and validator roles | Replace with Departmental Author and Procurement Planner respectively. |
| Custom capability and Operational Scope Assignment permissions | Remove. Use native Frappe Role, Workflow permission and User Permission only. |
| Publication acknowledges a Tender opportunity | Remove. Annual Plan publication does not create or advertise a Tender. |
| Legacy compatibility and migrated Demand records | Prohibited. This remains a clean Planning domain. |
| Draft Plan Item formation is irreversible | Correct. A Planner may dissolve an item while its Plan Version is mutable; sources return to the unallocated list and any effective reservations are released first. Submitted evidence is never dissolved. |
| Reservation release left to implementation inference | Remove. Planning must call the Budget-owned release contract on the exact lifecycle triggers defined in sections 5 and 7. |
| Generic maker-checker error without an action matrix | Remove. Section 6.1 defines the incompatible actions on one DPP submission or Plan Version. |
| Returned Annual Plan resumes at an inferred stage | Remove. A correction is a copied Draft with a new submitted snapshot; every resubmission restarts at Accounting Officer adoption. Finance repeats only under the objective rules in section 5.2. |
| Accepted DPP successor silently rewrites an allocated source | Prohibited. The affected Draft item is marked **Source correction required** and must be dissolved and re-formed. Submitted and Active evidence is never rewritten. |
| Withdrawn initial DPP permanently closes the root | Correct. It may be reopened as the next Draft Version only while the initial submission window remains Open. |
| Accepted Needs disappear when their department misses DPP submission | Remove. Planning shows **Not included — DPP submission window closed** while Departmental Needs retains the accepted records; this is visibility, not a late-submission bypass. |
| Combined sources need not share currency | Correct. Sources must resolve to the same Budget and currency. Cross-currency Planning is outside MVP-1. |
| One Plan Item can be consumed by only one Requisition | Remove. Requisitions may make sequential partial drawdowns while balances remain, subject to its one-open-Requisition rule. |
| Browser-stored PE/FY choice is the operating authority | Prohibited. Server-side Role and User Permission define access. The Planning Financial Year is a visible, changeable module filter and never a permanent browser lock. |
| Separate sidebar links for Finance, validation or approval queues | Prohibited. Procurement Planning has one workspace entry. Actionable work arrives through that workspace, the shared **My Work** surface and notifications; task routes are deep links, not menu items. |

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
- Accounting Officer adoption and exactly one applicable statutory approval;
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
- a custom Frappe shell, header, breadcrumb or navigation system;
- an authoritative browser-stored PE/FY context or a Planning-only work-queue menu; or
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
| Direct requirement description | Tells the HoD, Procurement Planner and Planner what the department requires. |
| Expected operational result | Preserves what the department expects the requirement to achieve and passes it read-only into Requisition eligibility. |
| Quantity and unit | Establish the complete source quantity and the quantity available for one Plan Item allocation. |
| Required by | Constrains the Plan Item completion date. |
| Budget Line | Identifies the authoritative funding position checked by Finance. |
| Indicative amount | Establishes the entry value, Plan Item value and reservation request. |
| Requirement type classification | Determines compatible Plan Item formation and procurement reporting. |
| Plan Item title and description | Define the procurement package shown in the Annual Plan and downstream lineage. |
| Strategic Objective | Provides the approved strategic alignment for the Plan Item. |
| Procurement method | Provides the method recorded in the Annual Plan. MVP-1 assigns the sole admitted method; it does not ask the user to select a fixed value. |
| Aggregation reason | Explains why several departmental entries form one procurement package; required only for a combined item. |
| Seven planned dates | Produce the approved procurement schedule and enforce chronological readiness. |
| Return reason | Gives the correction owner one actionable reason while preserving the submitted snapshot. |

## 3. Fixed ownership and dependency boundary

- Configuration & Governance owns PE, organisation unit, Financial Year, timezone, unit catalogue, requirement-type catalogue, procurement-method catalogue, module windows, statutory approval route and native Role/User Permission assignments.
- Departmental Needs owns accepted Need identity, accepted versions and the six requirement facts supplied to Planning.
- Strategy Alignment owns Strategic Plans and Active Strategic Objectives. Planning stores the selected Objective lineage on a Plan Item and never edits Strategy.
- Budget & Funding owns Budget identity, Budget Lines, funding source, currency, live positions, reservations, commitments and ledger events.
- Procurement Planning owns DPPs, direct requirements, DPP funding specification, classification, Annual Plans, Plan Items, source allocations, Finance tasks, Planning decisions, publication evidence and Requisition-eligibility projection.
- Procurement Requisitions owns the Requisition and its drawdown. Tendering and Contract Management own later operational records and actual milestones.

| Information or decision | Owner | Planning relationship |
|---|---|---|
| PE/FY context, OU, timezone and assignments | Configuration & Governance | Resolve exact identifiers and fail closed when absent or ambiguous. |
| DPP submission window | Procurement Planning configuration | Gate the first submission of a DPP root, including a reopened root with no accepted predecessor. Returned corrections and accepted-plan successors follow section 5.1. Opening a page creates nothing. |
| Accepted Need facts | Departmental Needs | Project read-only title, description, quantity, unit and required-by date. |
| Direct departmental requirement | Procurement Planning | Create and edit only inside a Draft or Returned DPP Version. |
| Budget Line identity, funding source and currency | Budget & Funding | Select from eligible Active Budget Lines and read live funding through services. |
| DPP indicative amount | Procurement Planning | Capture on every DPP entry and pass to Plan Item formation. |
| Requirement type | Procurement Planning | Procurement Planner classifies the immutable submitted entry. |
| Strategic Objective | Strategy Alignment / Procurement Planning | Select exactly one Active Objective on the Plan Item and preserve its version lineage. |
| Finance confirmation and reservation | Planning task / Budget service | Planning owns task and decision UI; Budget performs the live check and reservation transaction. |
| Annual Plan adoption, statutory approval and publication | Procurement Planning | Present the exact Plan Version to the Accounting Officer and one applicable statutory authority, then activate only the acknowledged approved payload. |
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

The stable `source_line_id` is the Need ID for a Need-origin entry and the `dpp_entry_id` for a direct entry. No duplicate source identifier is stored.

| Field | Operational purpose and system effect |
|---|---|
| `dpp_entry_id` | Immutable entry reference used by classification and source lineage. |
| `dpp_version_id` | Fixes the containing Version. |
| `source_origin` | `Accepted Departmental Need` or `Direct departmental requirement`. Required and immutable after creation. |
| `need_id` / `need_version_id` | Fix the accepted Need source. Required only for Need-origin entries; empty for direct entries. |
| `title` | Requirement label. Read-only projection for Need-origin; editable for direct origin. |
| `description` | Requirement statement. Read-only projection for Need-origin; editable for direct origin. |
| `expected_operational_result` | Intended operational effect. Read-only projection for Need-origin; editable for direct origin. Required for every entry. |
| `quantity` | Full source quantity, greater than zero. Read-only for Need-origin. |
| `unit_id` | Governed quantity unit. Read-only for Need-origin. |
| `required_by_date` | Required and inside the target FY. Read-only for Need-origin. |
| `budget_line_id` | Planning-selected Active eligible Budget Line. Required before submission. |
| `indicative_amount_minor_units` | Planning-owned entry value. Required before submission and greater than zero. Currency is read from the Budget Line; there is no editable currency field. |

Direct entries contain no Need reference, bypass reason, attachment or source evidence. Need-origin entries retain the accepted Need's expected operational result as a read-only projection.

### 4.5 DPPSubmission

The immutable HoD-certified snapshot of one DPP Version.

| Field | Operational purpose and system effect |
|---|---|
| `dpp_submission_id` | Immutable submission and queue reference. |
| `dpp_version_id` | Fixes the submitted Version. |
| `submission_number` | Generated sequence for the DPP root. |
| `submitted_entry_snapshots` | Immutable ordered rows containing each entry and its source lineage, funding specification and source version. |
| `attestation_text` | Exact fixed certification rendered with department and FY. |
| `submitted_by_user_id` | Records the HoD or acting HoD who certified the plan. |
| `authority_snapshot` | Records the native role and User Permission used for the decision. |
| `submitted_at` | Server decision instant. |

The attestation is:

> I certify that this Departmental Procurement Plan contains the current procurement requirements of {department} for {financial_year}, including every current accepted Departmental Need and any direct departmental requirements shown. I confirm that the quantities, required-by dates, Budget Lines and indicative amounts are ready for Procurement validation and inclusion in the Annual Procurement Plan.

### 4.6 DPPValidationTask and DPPValidationDecision

`DPPValidationTask` identifies the exact submitted DPP Version, PE/FY/OU scope, Open/Completed status and decision token. It is visible only to a Procurement Planner with the exact native User Permission scope.

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
| `title` | System-generated as `{Procuring Entity} Annual Procurement Plan {FY period}`. `FY period` is the display period without an `FY` prefix, for example `2027/28`. |
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
| `correction_of_plan_version_id` | Identifies the immutable submitted Plan Version returned by a governance actor. Empty unless this Draft is a correction. |
| `version_status` | `Draft`, `Awaiting Accounting Officer`, `Awaiting statutory approval`, `Returned`, `Approved — publication pending`, `Publication failed`, `Active`, `Superseded` or `Cancelled`. |
| `change_reason` | Required only for a successor Version; identifies the approved-plan change being proposed. |

The mutable Draft content is locked when submitted. A return preserves that immutable Plan Version and creates the next numbered Draft Plan Version linked through `correction_of_plan_version_id`; it does not reopen the submitted record. The correction retains the returned Version's `based_on_version_id`, if any. Pending DPP additions cannot enter it. The Active predecessor remains operational until the correction or successor is approved, published and acknowledged.

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
| `item_state` | `Draft`, `Dissolved`, `Active`, `Removed in successor` or `Superseded`. A Dissolved item is historical, read-only and excluded from Plan totals. |
| `finance_state` | Derived as `Not requested`, `Awaiting Finance`, `Confirmed`, `Returned` or `Stale`. |
| `record_version` | Optimistic-concurrency token. |

Quantity, unit, planned value, funding source and Budget Line breakdown are derived from source allocations. **Source correction required** is derived when an allocation no longer points to the current accepted DPP entry/version for its stable departmental source. Contract period, lotting, Value Commitment, recommended method, generic basis and actual milestone fields do not exist.

### 4.10 PlanSourceAllocation

| Field | Operational purpose and system effect |
|---|---|
| `plan_source_allocation_id` | Immutable source-lineage reference passed to Requisition eligibility as `plan_item_line_id`. |
| `plan_item_id` | Identifies the Plan Item consuming the source. |
| `accepted_dpp_entry_id` | Fixes the exact accepted departmental entry. |
| `source_origin` | Preserves `Accepted Departmental Need` or `Direct departmental requirement`. |
| `need_id` / `need_version_id` | Preserves Need lineage only when the source has it. |
| `quantity` / `unit_id` | Full accepted source quantity. |
| `budget_line_id` / `indicative_amount_minor_units` | Full accepted source funding specification. |
| `allocation_state` | `Draft`, `Active`, `Released`, `Removed in successor` or `Superseded`. `Released` preserves a dissolved Draft item's lineage but makes the source available for new formation. |

One accepted DPP entry has at most one effective allocation and is allocated at full quantity in one open Plan Version. `Released` allocations are historical and do not block re-formation. No split allocation or partial amount is permitted in MVP-1.

### 4.11 FinanceTask, FinanceDecision and reservation reference

The Planning-owned Finance task fixes one Plan Item, its exact source allocations, required amounts, assigned funding scope, `Open`, `Completed` or `Cancelled` status and concurrency token.

The immutable Finance decision records `Confirm funding` or `Return to planner`, actor, effective assignment, time and required return reason where applicable. A successful confirmation stores one Budget-owned reservation reference per source allocation. Each reference is derived as `Active`, `Needs Attention`, `Partially Converted`, `Converted` or `Released` from Budget; Planning does not duplicate Budget position fields.

Finance evidence becomes `Stale` only when at least one reservation is absent, released, `Needs Attention`, based on a changed source set, Budget Line, amount or currency, or fails Budget revalidation at Plan resubmission. A title, description, Strategic Objective, aggregation reason, method or schedule correction does not by itself invalidate an otherwise current reservation.

### 4.12 PlanGovernanceTask and PlanDecision

One protected task is created for each of two controlled decisions:

- `Accounting Officer adoption` — the Accounting Officer adopts or returns the complete consolidated Plan; and
- `Statutory approval` — exactly one authority applicable to the PE approves or returns the Accounting-Officer-adopted Plan.

The statutory authority is the responsible Cabinet Secretary, County Executive Committee Member for finance or responsible for the entity, Board of Directors or similar governing body, as applicable. The route is resolved from governed PE data; users cannot add an approval stage.

Each task fixes the exact immutable submitted Plan Version, current stage, role or legal capacity, scope and concurrency token. Each decision stores the action, actor, capacity exercised, decision time, submitted Version and required return reason. A Board decision also stores its collective resolution reference. There is no optional note field.

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
| No DPP | Open departmental plan | DPP root and Draft Version 1 | Departmental Author or HoD |
| Draft | Save direct requirement / enrich Need / remove direct requirement | Draft updated | Departmental Author or HoD |
| Draft | Submit departmental plan | Immutable submission and Open validation task | HoD or acting HoD using the same role |
| Submitted | Return to department | Submitted snapshot preserved; copied correction Draft created | Procurement Planner |
| Submitted | Accept departmental plan | Submitted Version Accepted with classifications; accepted entries appear in the open Draft Annual Plan | Procurement Planner |
| Returned | Save / Resubmit | Corrected Draft saved or submitted as the next submission | Departmental Author; HoD submits |
| Accepted; change required | Create update | One Draft successor copied from Accepted Version | Departmental Author or HoD |
| Draft successor | Submit update | Same validation route; Active Plan unchanged | HoD or acting HoD using the same role |
| Draft / Returned with no downstream consumption | Withdraw DPP Version | Version Withdrawn; prior Accepted Version remains current when one exists | HoD or acting HoD using the same role |
| Withdrawn with no accepted predecessor; initial window Open | Reopen departmental plan | Same DPP root; next numbered Draft Version | Departmental Author or HoD |

The DPP may consist entirely of direct requirements. If current accepted Needs exist in the exact department/context, all must be represented exactly once before submission. Direct entries may be added in any number. A DPP with no entries cannot be submitted. The window gates the first submission and any reopened root that still has no accepted predecessor. A correction returned from validation and a successor required by an authoritative source change may be resubmitted after window close; neither route admits a new unreviewed initial DPP.

### 5.2 Annual Plan lifecycle

| Current state | Command | Result | Actor |
|---|---|---|---|
| First DPP accepted; no Annual Plan | Project accepted entries | Annual Plan and Draft Version 1 created automatically; entries shown as unallocated | System, in the DPP-acceptance transaction |
| Active; no successor | Begin plan update | Draft successor; Active Version unchanged | Procurement Planner |
| Draft | Form Plan Items / save item | Draft updated | Procurement Planner |
| Mutable Draft item | Dissolve Plan Item | Open Finance task cancelled; effective reservations released; allocations marked Released; sources return to unallocated | Procurement Planner |
| Draft item | Request Finance confirmation | Open Finance task | Procurement Planner |
| Awaiting Finance | Confirm funding | All source reservations created; item Confirmed | Budget Officer |
| Awaiting Finance | Return to planner | No reservation; item Returned | Budget Officer |
| Draft; every item Confirmed | Submit consolidated Plan | Immutable submitted snapshot and Accounting Officer task | Procurement Planner |
| Awaiting Accounting Officer | Adopt and submit | Adoption decision and one statutory-approval task | Accounting Officer |
| Awaiting Accounting Officer | Return for correction | Submitted Version marked Returned; next numbered Draft correction created | Accounting Officer |
| Awaiting statutory approval | Approve Annual Procurement Plan | Approved — publication pending | One statutory authority applicable to the PE |
| Awaiting statutory approval | Return for correction | Submitted Version marked Returned; next numbered Draft correction created | One statutory authority applicable to the PE |
| Returned correction; ready | Submit corrected Plan | New immutable snapshot; Budget reservations revalidated; Finance repeated only if stale; route restarts at Accounting Officer | Procurement Planner |
| Approved / Publication failed | Publish / Retry | Active only on exact acknowledgement; otherwise failed/indeterminate | System; technical retry by System Manager if required |
| Draft successor | Cancel update | Successor-only reservations released; successor Cancelled; Active Version and its reservations unchanged | Procurement Planner |

A governance return never edits or reopens the submitted Version. It creates the next numbered Draft Plan Version containing exactly the sources present in the returned Version. DPP entries accepted while the Plan is submitted, returned or being corrected remain **Pending addition** until the corrected Version becomes Active; they enter only the later successor.

On corrected-Plan submission, Budget revalidates every retained reservation. If the source set, Budget Line, amount or currency changed, or Budget reports a reservation absent, released or `Needs Attention`, the affected item returns to Finance before Plan submission can complete. When all reservations remain current, the correction proceeds without creating replacement reservations. Every corrected submission restarts at Accounting Officer adoption, including one returned at the statutory stage.

### 5.3 Invariants

1. Reads never create a DPP, Annual Plan, Version, task, allocation, reservation or publication attempt.
2. One DPP root exists per PE/FY/OU and one Annual Plan root per PE/FY. The initial Annual Plan is created only by the first successful DPP acceptance, never by a read.
3. A current accepted Need is represented once and at full quantity in its department's submitted DPP.
4. A direct requirement never creates or pretends to be a Need.
5. Every submitted DPP entry has one eligible Budget Line and one positive indicative amount.
6. Only the Procurement Planner classifies a submitted entry.
7. Every accepted DPP entry is allocated exactly once and at full quantity in the submitted Plan Version.
8. Sources may be combined only when PE/FY, Budget, currency, requirement type, unit and procurement treatment are compatible. Cross-currency combination is prohibited in MVP-1.
9. Every Plan Item has exactly one current Active Strategic Objective.
10. Plan Item value equals the sum of its source-allocation amounts.
11. Finance confirmation is all-source and atomic; no partial reservation is permitted.
12. Planned dates are chronological and delivery completion is no later than the earliest source required-by date.
13. Governance actors decide only an immutable submitted Version and cannot edit it.
14. The Accounting Officer adoption is followed by exactly one statutory approval route applicable to the PE; no professional-review, Head of Procurement Function, generic committee or publication approval is inserted.
15. Statutory approval does not itself publish or activate the Plan.
16. Only acknowledgement of the exact approved payload activates a Version.
17. At most one Plan Version is Active and at most one successor is open.
18. An Active item remains eligible until an acknowledged successor changes it, subject to funding and drawdown.
19. An Active item with a Requisition drawdown, Tender handoff, commitment or contract cannot be removed through Planning.
20. Submitted, decided, approved, Active and Superseded evidence is never edited or deleted.
21. Draft dissolution and successor cancellation release only the unconverted reservation remainder linked to the affected Draft or successor; they never release an Active predecessor's reservation.
22. An acknowledged successor releases the unconverted reservation remainder for each removed item in the same controlled activation process; downstream commitments remain untouched.
23. A corrected Plan always returns to Accounting Officer adoption and never resumes directly at statutory approval.
24. A database uniqueness constraint enforces one Annual Plan root per PE/FY and one open Version per Plan; concurrent first-DPP acceptance returns or reloads the winner rather than creating a duplicate.

## 6. Roles and permissions

| Native Frappe role or legal capacity | Exact scope and permitted work |
|---|---|
| Departmental Author | Assigned PE/OU scope; open the relevant FY DPP, enrich Need-origin entries, create/edit direct entries and correct a returned Draft. Several people may hold this role for one department, and one person may cover several assigned departments. Cannot submit unless also HoD. |
| Head of User Department | Assigned PE/OU scope; all Author work plus certify, submit, resubmit and withdraw the departmental Version. Only the effective HoD assignment may act at the command time. |
| Procurement Planner | Assigned PE and permitted OUs; accept or return submitted DPPs, classify entries, consolidate accepted sources, form/edit Plan Items, request Finance, submit the Annual Plan and prepare successors. |
| Budget Officer | Assigned PE and Budget scope; view protected Finance tasks, confirm funding or return. Cannot edit Planning content. |
| Accounting Officer | Assigned PE; adopt or return the complete consolidated Annual Procurement Plan. |
| Responsible Cabinet Secretary / County Executive Committee Member for finance or responsible for the entity / Board of Directors or similar governing body | Assigned PE and legal capacity; approve or return the Accounting-Officer-adopted Plan. Exactly one route applies to the PE. |
| Planning Auditor | Authorised neutral read of Plan and immutable evidence for assigned PE/OU scope only. |

Use Frappe Role, Workflow permissions and User Permission. User Permissions assign PE and, where relevant, OU or Budget scope; they are not recreated for each Financial Year. Eligible Financial Years derive from configured FY/context records and the requested operation's window or state. Do not use Capability Profiles, Operational Scope Assignments or a second permission store. A role label alone grants no cross-scope authority. Every list, count, detail, button and command uses the same PE/FY/OU and task-scope predicates.

Publication is an idempotent system service. A technical retry may be available to System Manager, but it retries the same approved payload and is not a procurement decision.

### 6.1 Maker-checker rules

Role combinations are permitted. The conflict is between actions on the same evidence chain, not between role labels held by a user.

| Earlier action by the same user | Later action prohibited on the same evidence chain |
|---|---|
| Submit one DPP submission as HoD | Accept or return that DPP submission as Procurement Planner |
| Create the Version, form/dissolve an item, save any Planner-owned field, request Finance or submit one Annual Plan Version as Procurement Planner | Confirm or return Finance for that Version; adopt or return it as Accounting Officer; approve or return it as statutory authority |
| Confirm or return Finance for any item in one Plan Version | Adopt or return that Version as Accounting Officer; approve or return it as statutory authority |
| Adopt or return one Plan Version as Accounting Officer | Approve or return that Version as statutory authority |

A Departmental Author may also be the effective HoD and submit the DPP: this is one departmental certification step, not an invented review level. For Annual Plans, the evidence chain includes the submitted Version and every correction derived through `correction_of_plan_version_id` until one Version activates or the open chain is cancelled. A correction does not reset segregation history. Administrator and System Manager receive no business-decision exception.

## 7. Cross-module integration contracts

### 7.1 Departmental Needs intake

`DepartmentalNeedAccepted.v2` supplies event identity, Need/version lineage, PE/OU/FY, title, description, expected operational result, quantity, unit and required-by date. Projection is idempotent.

- The current accepted Need appears as one read-only Need-origin DPP entry.
- Planning adds only Budget Line and indicative amount.
- A successor accepted event marks the earlier unsubmitted source stale and refreshes the Draft; if already submitted or consumed, it creates a correction requirement without rewriting evidence.
- A withdrawn event removes only an unsubmitted/unconsumed source. Departmental Needs cannot publish withdrawal while an Active Plan dependency exists.
- `NeedPlanningUsageChanged.v1` is published only when an Active Plan begins or ceases to represent the accepted Need version.
- When a DPP successor is accepted and its predecessor entry is allocated to a mutable Draft item, Planning marks the item **Source correction required**, leaves the historical allocation unchanged but ineligible, and lists the successor entry as unallocated. It never moves the allocation automatically. The Planner dissolves and re-forms the item; any linked reservation is released first.
- When the affected Plan Version is submitted or in governance, Planning blocks the decision and requires a governance return before correction. When the predecessor is Active, it remains authoritative and the successor entry waits for the next Plan successor.
- Accepted Needs belonging to a department with no submitted DPP after window close remain visible in the Planning workspace as **Not included — DPP submission window closed**. Departmental Needs retains the accepted records. This creates no DPP and does not permit a late first submission.

### 7.2 Strategy selection

`ListEligibleStrategicObjectives` returns only Active Strategic Objectives for the same PE whose effective period covers the Plan Version. The selector displays the Objective title and its hierarchy path. Saving stores Objective ID, Strategy Plan ID and Strategy Version ID. Planning does not store Outcome, Indicator, Target or Value Commitment.

If the selected Objective ceases to be eligible before Plan submission, the item is blocked and the Planner must select a current Objective. An already Active Plan preserves its approved lineage.

### 7.3 Budget and Finance

`ListEligibleBudgetLines` returns only Active Budget Lines valid for the same PE/FY and department/PE scope. The DPP entry stores the selected line ID and amount; funding source and currency display from Budget read services.

`CheckAndReserveFunding` is called only from the protected Finance confirmation command. It rechecks each source allocation under lock and either creates every reservation or none. Planning stores reservation references; Budget remains authoritative for balances and ledger effects.

`RevalidatePlanningReservations` checks the exact retained reservation set on corrected-Plan submission and before later downstream use. It creates no reservation. `ReleasePlanningReservations` calls Budget's authenticated `release_reservation` contract for the unconverted remainder of every affected reservation under one Planning correlation and idempotency key. Planning records the returned release references; it never edits Budget rows.

Release occurs only for these Planning events:

- dissolution of a mutable Draft item;
- replacement of a financed Draft source after an accepted DPP successor;
- cancellation of reservations created only for a Draft successor; and
- activation of a successor that removes an Active item, after downstream checks prove no drawdown, Tender handoff, commitment or contract.

A governance return does not release unchanged reservations. Cancelling a successor does not release any reservation belonging to the Active predecessor. A release failure rolls back the Planning transition and leaves the item blocked; Planning never marks a reservation released from a local assumption.

Need acceptance, DPP save, DPP submission, DPP validation and Plan Item formation create no reservation.

### 7.4 Requisition eligibility

`GetRequisitionEligiblePlanItem.v2` exposes an item only when its Plan Version is Active, Finance evidence remains current, remaining quantity and value are positive, and no blocking successor or withdrawal effect applies.

It returns the Plan, Version and Plan Item IDs; PE/FY; requirement type; procurement method; Strategic Objective and path; planned dates; funding-confirmation references; total and remaining quantity/value; and, for every `plan_source_allocation_id`:

- source origin and stable `source_line_id`;
- DPP entry ID and Need/version lineage where applicable;
- department, title, description and expected operational result;
- approved and remaining quantity, unit and required-by date; and
- Budget Line, allocated amount and remaining amount.

Each authorised Requisition draws a positive quantity and value from one eligible Plan Item and preserves every selected `plan_source_allocation_id`. Several sequential Requisitions may draw the same Plan Item while quantity/value remain. Procurement Requisitions enforces at most one open Requisition per `plan_item_id + requesting_org_unit_id`. Drawdown and reversal are atomic and cannot exceed either the source row or Plan Item balance. Planning never creates the Requisition or technical specification, and a later Plan successor never silently changes an authorised Requisition.

## 8. Service and command contracts

### 8.1 Read contracts

| Contract | Required result |
|---|---|
| `ResolvePlanningContexts` | Authorised PEs/OUs from native assignments plus configured Financial Years available to the module; no implicit first record and no per-user FY assignment. |
| `GetPlanningWorkspace` | Reconciled action queue, waiting work and current Plan state using one scope predicate. |
| `GetDepartmentalPlan` | Current DPP Version, accepted Need coverage, direct entries, blockers and authorised commands. |
| `GetDPPValidationTask` | Exact immutable submission, all entry details, funding specification, source origin and current decision controls. |
| `ListAcceptedDPPSources` | Current accepted, unallocated entries for the exact PE/FY. The read model joins each accepted DPP entry through the immutable `DPPValidationDecision` for that submission/version to obtain its classification; it does not invent a classification field on `DPPEntry` or `PlanSourceAllocation`. |
| `GetPlanVersion` | Complete Version, all Plan Items, source allocations, Finance state, governance history and current commands. |
| `GetPlanItem` | Exact item, all source rows, Objective, method, schedule and Finance state. |
| `GetFinanceTask` | Protected current Budget positions and required/after-confirmation amounts for every source. |
| `GetPlanGovernanceTask` | Complete immutable Plan details and exact stage decision controls. |
| `GetPublicationTask` | Exact approved Version, destination, attempt result and permitted publish/retry action. |
| `GetRequisitionEligibility` | Current eligible or blocked result with lineage, balances and evaluation time. |

### 8.2 Commands

| Command | Core effect |
|---|---|
| `OpenDepartmentalPlan` | Idempotently create/reuse the one DPP root and current Draft after exact authority checks; after withdrawal with no accepted predecessor, create the next Draft Version only while the initial window is Open. |
| `SaveNeedFunding` | Add or change only Budget Line and amount on a current Need-origin Draft entry. |
| `SaveDirectRequirement` | Create/update the eight permitted direct-entry values, including expected operational result. |
| `RemoveDirectRequirement` | Remove an unsubmitted direct entry from the current Draft. |
| `SubmitDepartmentalPlan` | Revalidate complete accepted-Need coverage, direct entries, funding, window and HoD authority; create immutable submission and validation task. |
| `ReturnDepartmentalPlan` | Preserve submission, record structured issues and create the correction Draft. |
| `AcceptDepartmentalPlan` | Record classifications, create/reuse the initial Draft Annual Plan when necessary and project accepted entries into its unallocated-source queue in the same transaction. |
| `FormPlanItems` | Create one item per selected source or one combined item for compatible selected sources; allocate each source atomically. |
| `DissolvePlanItem` | On a mutable Draft only, cancel an open Finance task, release every effective reservation, mark allocations Released and return the sources to the unallocated list atomically. |
| `SavePlanItem` | Save only the Plan Item allow-list and recalculate exact blockers. |
| `RequestFinanceConfirmation` | Validate the complete item and create/reuse one current Finance task. |
| `ConfirmFunding` | Atomically reserve every source amount and record the Finance decision. |
| `ReturnFromFinance` | Record the required reason, create no reservation and reopen planner-owned fields. |
| `SubmitConsolidatedPlan` | Require all accepted sources allocated, all items complete and Finance current; create the immutable submission and Accounting Officer task. |
| `AdoptAndSubmitPlan` | Record Accounting Officer adoption and create exactly one statutory-approval task resolved for the PE. |
| `ApproveAnnualPlan` | Record approval and move the exact Version to publication pending. |
| `ReturnPlanVersion` | Mark the submitted Plan Version Returned, record the actionable reason and create the next numbered Draft correction linked to it. |
| `SubmitCorrectedPlan` | Lock a new corrected snapshot, revalidate retained reservations, route stale items through Finance where required and then restart governance at Accounting Officer adoption. |
| `PublishAnnualPlan` | Transmit the exact approved payload and activate only on acknowledged response. |
| `BeginPlanUpdate` | Create the sole Draft successor from the Active Version. |
| `RemovePlanItemInSuccessor` | Propose whole-item removal only when downstream checks permit it. |
| `CancelPlanUpdate` | Release successor-only reservations, cancel the successor and leave the Active Version and its reservations unchanged. |

All mutating commands require an expected record version and idempotency key. Server-side Role, User Permission, state and live-data checks are repeated inside the transaction.

## 9. Error contract

| Code | Plain-language result |
|---|---|
| `PLN_NO_CONTEXT` | You do not have an assigned Procurement Planning scope, or no configured Financial Year is available. |
| `PLN_WINDOW_CLOSED` | The initial departmental-plan submission window is closed. |
| `PLN_NEED_COVERAGE_INCOMPLETE` | Add every current accepted Need to this departmental plan before submitting. |
| `PLN_ENTRY_INCOMPLETE` | Complete the highlighted requirement fields before submitting. |
| `PLN_BUDGET_LINE_INELIGIBLE` | Select an Active Budget Line available to this department and Financial Year. |
| `PLN_DPP_STALE` | This departmental plan changed. Reload and review the current Version. |
| `PLN_CLASSIFICATION_INCOMPLETE` | Classify every submitted requirement before accepting the plan. |
| `PLN_SOURCE_UNAVAILABLE` | One or more selected departmental entries are no longer available for Plan Item formation. |
| `PLN_SOURCE_INCOMPATIBLE` | The selected entries cannot form one Plan Item. Create separate items. |
| `PLN_SOURCE_CORRECTION_REQUIRED` | A departmental source changed. Dissolve and re-form the affected Draft item before continuing. |
| `PLN_DISSOLUTION_BLOCKED` | This Plan Item is no longer in a mutable Draft and cannot be dissolved. |
| `PLN_OBJECTIVE_INELIGIBLE` | Select an Active Strategic Objective valid for this Plan. |
| `PLN_SCHEDULE_INVALID` | Correct the highlighted dates so the schedule is chronological and meets the required-by date. |
| `PLN_FINANCE_SHORTFALL` | Funding is insufficient for one or more source allocations. No reservation was created. |
| `PLN_FINANCE_STALE` | Funding confirmation is no longer current. Request confirmation again. |
| `PLN_RESERVATION_RELEASE_FAILED` | Funding could not be released. The Planning change was not completed. Try again or quote the support reference. |
| `PLN_REVIEW_STALE` | This task has already changed. Reload to see the current decision. |
| `PLN_SEGREGATION_CONFLICT` | You cannot make this decision because you performed an incompatible earlier action. |
| `PLN_PUBLICATION_FAILED` | Publication was not acknowledged. The approved Plan remains unchanged and may be retried. |
| `PLN_REMOVAL_BLOCKED` | This Active Plan Item has downstream use and cannot be removed through Planning. |
| `PLN_STALE_WRITE` | Another user changed this record. Reload before continuing. |

Unauthorised detail and task reads return the same not-found response as a nonexistent record. Internal diagnostics are logged with a support correlation and are not shown as user fields.

## 10. UI architecture, menu and routes

Procurement Planning has one KenTender navigation entry named **Procurement Planning**. It does not add sidebar entries for DPP review, Finance, Accounting Officer, statutory approval, publication or any other work queue.

| Surface | Canonical Frappe Desk route | Primary user |
|---|---|---|
| Planning workspace | `/app/procurement-planning` | All authorised Planning users |
| Departmental Plan | `/app/departmental-procurement-plan/{dpp_reference}` | Departmental preparer, HoD, Procurement Planner read |
| DPP validation task | `/app/procurement-planning/dpp-review/{task_id}` | Procurement Planner |
| Annual Plan | `/app/annual-procurement-plan/{plan_reference}` | Planner and authorised readers |
| Plan Item | `/app/procurement-plan-item/{plan_item_id}` | Planner and authorised readers |
| Finance task | `/app/procurement-planning/finance/{task_id}` | Assigned Budget Officer |
| Governance task | `/app/procurement-planning/review/{task_id}` | Accounting Officer or the one statutory authority applicable to the PE |
| Publication result | `/app/procurement-planning/publication/{publication_id}` | Neutral read; technical retry only for System Manager when required |

The workspace shows only work the actor can perform or is waiting for. The same tasks may appear in the shared KenTender **My Work** surface and notifications. Task routes above are authorised deep links reached from a task row or notification; they are not menu definitions. The workspace does not duplicate Budget, Strategy, Needs or Configuration dashboards. Frappe supplies the Desk header, breadcrumb, global search, user menu and common navigation.

Access is resolved server-side from native Role and PE/OU/Budget User Permission. Financial Year is not assigned to a user. It is derived from configured FY/context records and filtered by the operation's window and record state. A selected PE or FY is only a visible filter within Procurement Planning and never grants access. The page loads the sole eligible value directly; when several are eligible it shows a changeable Procuring Entity selector and a changeable Financial Year selector in the Planning page header. The last valid Planning selection may be stored as a server-side user preference for convenience. A browser value may cache presentation only and must be ignored when unauthorised, invalid or absent. Direct record and task routes derive PE/FY from the record and reauthorise it; they never depend on a prior browser selection.

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
| Separate actor dashboards or sidebar work-queue entries | Remove. Use one role-aware Planning workspace, shared My Work/notifications and authorised task deep links. |
| Monitoring entry/history and custom support workspace | Retire. |
| Stitch runtime, Tailwind utilities and vendor design markup | Keep only as historical visual evidence; never import into production. |

## 11. Static Claude Design contract

This section is the complete visual input to Claude Design. It defines appearance and exact fixture content only. Behaviour, validation, permissions, service calls, routing and state transitions are defined in section 12 and shall not be added to a design prompt.

### 11.1 Closed-input rules

- Produce desktop artboards at **1440 × 1024 px**.
- Reuse the approved KenTender Strategy Portfolio and deployed Planning visual system: spacing, type scale, tokens, cards, badges, tables, fields, buttons, tabs, empty states and dialogs.
- The artboard starts below the Frappe Desk header. Do not draw Frappe navigation, Desk header, breadcrumb, user menu, notifications, Help or global search. When the named artboard is the Planning workspace, draw only the visible Planning context controls explicitly stated for that artboard.
- Breadcrumb text is fixture data outside the artboard. It is supplied only to confirm location.
- Use only the visible labels, values, badges, controls, sections and states stated for the artboard.
- Do not invent data. If a value, column, control, message or state is not stated, omit it.
- Do not encode behaviour, validation, permissions, APIs, routing, transitions, concurrency, component names or implementation instructions in the visual output.
- Do not add charts, percentages, trend arrows, illustrations, side panels, steppers, helper panels, generic notes, attachments, action menus, metadata or extra table columns.
- Do not show technical digests, record versions, idempotency keys, event IDs, audit field names or editable identifiers.
- Do not show Value Commitment, contract period, lotting, recommended method, generic method basis, unit price, tax, cost breakdown, actual milestones, Requisition creation or Tender controls.
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

**Planning context row**

- Label **Procuring Entity** above a select showing **PE-MOH — Ministry of Health**.
- Label **Financial Year** above a select showing **FY 2027/28**.
- Quiet value **Annual Plan · Draft Version 1** to the right.

Both selects use normal editable-select styling. Do not depict either value as permanently fixed or as a browser-wide context.

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
| Human Resources Management and Development | 1 | 2 | KES 88,000,000 | Not submitted — window closed | View |

Below the table: **2 departmental plans**. Under it show the neutral message **2 accepted Needs are not included because the departmental-plan submission window closed.** Do not show a late-submit action, summary cards, charts, waiting queues or system support links.

### 11.3 PLN-DES-02 — Draft Departmental Procurement Plan

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Author · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 24 Nov 2026, 15:00 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP-MOH-DHI-2027-001**

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

Do not show Strategy, requirement type, funding source column, currency selector, attachment, source reference or Plan Item controls.

### 11.4 PLN-DES-03 — Accepted Need funding details

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Author · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 24 Nov 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP-MOH-DHI-2027-001 > NDS-MOH-2027-0001**

**Page content header**

- Title: **Complete funding details**
- Description: **Add the Planning-owned funding details for this accepted departmental requirement.**
- Status badge: **Accepted Need**
- No header action button

**Accepted requirement card**

Use the six Need-owned facts as read-only fields, followed by the accepted-source reference:

| Field label | Displayed value |
|---|---|
| Title | National digital health infrastructure upgrade |
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Expected operational result | Priority health facilities can use secure and interoperable digital health services. |
| Quantity | 1 programme |
| Unit | Programme |
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

Do not edit any Need-owned fact. Do not show Strategy, requirement type, procurement method or reservation.

### 11.5 PLN-DES-04 — Direct departmental requirement

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Author · PE-MOH — Ministry of Health · OU-MOH-DHI — Digital Health · FY 2027/28 · 24 Nov 2026, 15:10 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP-MOH-DHI-2027-001 > Add direct requirement**

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
| Expected operational result | The Ministry receives a prioritised and actionable security remediation plan. |
| Quantity | 1 |
| Unit | Service |
| Required by | 31 Oct 2027 |

Title is a single-line input. Description and Expected operational result are multiline inputs. Quantity and Unit appear side by side; Required by appears below them.

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

Do not show Need, bypass reason, Strategy, requirement type, procurement method, attachment, source reference, funding source selector or reservation.

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

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · PE-MOH — Ministry of Health · FY 2027/28 · 27 Nov 2026, 13:45 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP review > DPP-MOH-DHI-2027-001**

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
- Right-aligned disabled primary button: **Submit consolidated Plan**

Do not show charts, creation of a blank Plan Item, Finance decision controls or approval controls.

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
- Left-aligned secondary button: **Dissolve Plan Item**
- Right-aligned secondary button: **Save draft**
- Right-aligned primary button: **Request Finance confirmation**

Do not show Value Commitment, contract period, lotting, recommended method, method basis, actual dates, attachment or source edit.

### 11.11 PLN-DES-09A — Combined Plan Item editor

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · PE-MOH — Ministry of Health · FY 2027/28 · 3 Dec 2026, 15:00 EAT · Frappe header breadcrumb: **Home > Procurement Planning > PLN-MOH-2027-001 > PPI-MOH-2027-033**

Use PLN-DES-09 page geometry with these exact replacements:

- Title: **Clinical training and deployment laptops for digital health rollout**
- Quiet reference: **PPI-MOH-2027-033 · Draft Version 1**

Replace the single source card with **Departmental sources**:

| Requirement | Department | Source origin | Quantity | Required by | Budget Line | Amount |
|---|---|---|---:|---|---|---:|
| Clinical training laptops for digital health rollout | Human Resources Management and Development | Accepted Departmental Need | 200 each | 31 Dec 2027 | MOH-BL-HWD-2027 | KES 48,000,000 |
| Clinical deployment laptops for digital health rollout | Digital Health | Accepted Departmental Need | 300 each | 31 Dec 2027 | MOH-BL-DHI-2027 | KES 72,000,000 |

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

### 11.13 PLN-DES-11 — Accounting Officer adoption

**Fixture context — outside the artboard:** Amina Hassan · `amina.hassan@moh.example.test` · Accounting Officer · PE-MOH — Ministry of Health · FY 2027/28 · 8 Dec 2026, 09:55 EAT · Frappe header breadcrumb: **Home > Procurement Planning > Accounting Officer adoption > PLN-MOH-2027-001-V1**

**Page content header**

- Eyebrow: **ACCOUNTING OFFICER ADOPTION · PLN-MOH-2027-001 · VERSION 1**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Status badge: **Awaiting Accounting Officer**

**Immutable Plan table**

| Plan Item | Department | Source origin | Quantity | Strategic Objective | Method | Value | Completion | Finance |
|---|---|---|---:|---|---|---:|---|---|
| PPI-MOH-2027-021 · National digital health infrastructure upgrade | Digital Health | Accepted Departmental Need | 1 programme | OBJ-MOH-2023-001 — Strengthen interoperable national digital health services | Open Tender | KES 80,000,000 | 31 Aug 2027 | Confirmed |

Below the table: **1 Plan Item · KES 80,000,000**. Do not collapse the Plan into summary cards.

**Decision statement:** **I adopt the complete consolidated Annual Procurement Plan Version 1 shown above and submit it for the statutory approval applicable to this Procuring Entity.**

**Sticky page footer**

- Left-aligned secondary button: **Return for correction**
- Right-aligned primary button: **Adopt and submit**

Do not show professional review, Head of Procurement Function approval, editable Plan content, optional comments or publication controls.

### 11.14 PLN-DES-12 — Statutory approval

**Fixture context — outside the artboard:** MOH statutory approver · `moh.plan.approver@example.test` · Responsible Cabinet Secretary · PE-MOH — Ministry of Health · FY 2027/28 · 9 Dec 2026, 10:55 EAT · Frappe header breadcrumb: **Home > Procurement Planning > Statutory approval > PLN-MOH-2027-001-V1**

**Page content header**

- Eyebrow: **STATUTORY APPROVAL · PLN-MOH-2027-001 · VERSION 1**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Status badge: **Awaiting statutory approval**

**Authority card**

- Capacity: **Responsible Cabinet Secretary**
- Accounting Officer adoption: **Amina Hassan · 8 Dec 2026, 10:00 EAT**

Show the exact immutable Plan table and total defined in PLN-DES-11. For a Board or similar body, replace the individual capacity row with **Governing body** and require **Resolution reference** before approval.

**Sticky page footer**

- Left-aligned secondary button: **Return for correction**
- Right-aligned primary button: **Approve Annual Procurement Plan**

This is the only approval after Accounting Officer adoption. Do not show another approver, committee, professional recommendation or publication approval.

### 11.15 PLN-DES-13 — Publication result

Show the exact approved Version, destination, last attempt, result and acknowledgement reference read-only. Publication starts as a system action after approval. No business-role Publish button exists. When a retry is technically required, only System Manager sees **Retry exact approved payload**; the control cannot edit the destination or payload and creates no new approval.

### 11.16 PLN-DES-14 — Active Annual Procurement Plan

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

**Adoption, approval and publication card**

| Label | Value |
|---|---|
| Accounting Officer adoption | Amina Hassan · 8 Dec 2026, 10:00 EAT |
| Statutory approval | Responsible Cabinet Secretary · 9 Dec 2026, 11:00 EAT |
| Publication | Acknowledged · 10 Dec 2026, 15:00 EAT |

Do not show actual milestones, monitoring entry, create Requisition, create Tender, editable Plan fields, chart or generic evidence table.

### 11.17 PLN-DES-15 — Return dialogs

Produce two separate dialog artboards over their corresponding dimmed task pages.

**Accounting Officer return**

- Title: **Return Plan Version for correction?**
- Intro: **The submitted Version 1 remains unchanged. State the correction required.**
- Required multiline label: **Correction required**
- Exact value: **Confirm the planned contract-signing date against the delivery completion date.**
- Footer buttons: **Cancel** and **Return for correction**

**Statutory-approval return**

- Title: **Return adopted Plan Version for correction?**
- Intro: **The Accounting-Officer-adopted Version 1 remains unchanged. State the correction required.**
- Required multiline label: **Correction required**
- Exact value: **Correct the procurement package description before the Plan is resubmitted.**
- Footer buttons: **Cancel** and **Return for correction**

Do not add a reason category, attachment, assignee, due date, optional note or editing controls.

### 11.18 PLN-DES-16 — Common page states

Use the approved KenTender empty, error and unavailable components with these exact variants:

| State | Heading | Text | Control |
|---|---|---|---|
| No authorised context | Procurement Planning is not available | You do not have an assigned Procuring Entity scope, or no configured Financial Year is available for Planning. | None |
| No departmental plan | No departmental plan yet | Open the departmental plan to review accepted Needs or add a direct requirement. | Open departmental plan |
| No validation tasks | No departmental plans awaiting validation | New submissions will appear here. | None |
| No accepted sources | No accepted departmental entries | Accepted departmental entries will appear here automatically. | None |
| Finance shortfall | Funding is insufficient | The required amount exceeds the current available amount on at least one Budget Line. No reservation has been created. | Return to planner |
| Publication failed | Publication was not acknowledged | The approved Plan is unchanged. Retry the same publication when the destination is available. | Retry publication |
| Load error | Procurement Planning could not be loaded | Try again. If the problem continues, quote the support reference shown below. | Try again |

Only the load-error component may display a generated support reference. Do not add diagnostic text, illustrations or alternative actions.

## 12. Functional interaction requirements — excluded from design prompts

### 12.1 PLN-UI-01 — Procurement Planning workspace

- Resolve authorised PE and OU/Budget scope from native roles and User Permissions. Derive Financial Year options from configured records and operation windows; do not assign FY to the user. No client value grants access.
- One eligible PE or FY loads directly. Several are shown in visible, changeable Planning selectors. A user may change Financial Year at any time; choosing a future year does not permanently bind later visits.
- Store the last valid Planning selection as a server-side user preference only. Treat local storage as an optional cache, never as authority. Invalid or inaccessible cached values are discarded and the user can select again.
- A direct task or record route resolves context from the record, reauthorises it and displays it. It never requires a prior selector choice.
- The action queue contains only tasks the actor may decide now. Waiting work is neutral read-only information and never exposes disabled protected controls.
- Workspace counts and rows use the same database scope and snapshot.
- Opening the workspace or switching context creates no Planning record.
- A departmental user sees their DPP work, a Procurement Planner sees submitted DPP tasks, a Planner sees accepted sources and Plan work, a Budget Officer sees Finance tasks, and each governance actor sees only their exact task.
- No role receives a separate sidebar work-queue menu. The sole **Procurement Planning** entry, shared **My Work** and notifications link to the same authorised tasks.
- Search and counts never disclose another PE, FY, OU, task or Plan.

### 12.2 PLN-UI-02 — Departmental Plan

- **Open departmental plan** calls the explicit guarded command; subsequent reads reuse the one root and Draft Version.
- Project every current accepted Need in the exact PE/FY/OU once. Its six facts remain read-only.
- **Complete** opens PLN-UI-03 for a Need-origin entry. **Add direct requirement** opens PLN-UI-04. **Edit** opens the current direct entry only.
- Draft save permits incomplete funding. Submission requires all entries complete, every current accepted Need covered once, every direct entry valid and at least one entry in total.
- Only direct entries can be removed from a Draft. A current accepted Need cannot be omitted or locally deleted.
- Source successor, withdrawal and Budget Line changes are rechecked on every save and submission.
- If the initial Version was withdrawn without an accepted predecessor, **Open departmental plan** creates the next numbered Draft only while the original submission window is Open. It never revives or edits the withdrawn Version.
- Initial HoD submission requires the exact certification checkbox, current role/User Permission and Open window. An acting HoD uses the same role with a time-bound User Permission. A returned correction or source-change successor requires the same certification and authority but may be resubmitted after the initial window closes. The certification text is server supplied, not client composed.
- A successful submission routes to immutable submitted detail. The submitter sees neutral status while the Procurement Planner acts.
- A returned submission loads the copied correction Draft and displays each structured issue next to its affected entry.

### 12.3 PLN-UI-03 — Accepted Need funding details

- Load the exact accepted Need version fixed by the DPP entry and display all six source facts read-only.
- Budget Line options come only from `ListEligibleBudgetLines` for the exact PE/FY/OU.
- Selecting a line refreshes its currency and approved line amount for context; it does not display or promise live availability.
- Save accepts only Budget Line and positive indicative amount. Direct URL or payload attempts to alter Need facts are rejected.
- Save creates no reservation, commitment or Budget mutation.
- If the Need version is no longer current, save is blocked and the DPP refresh path is shown.

### 12.4 PLN-UI-04 — Direct requirement editor

- A new direct entry exists only after a successful save command; opening or cancelling the blank editor creates nothing.
- Save accepts exactly title, description, expected operational result, quantity, unit, required-by, Budget Line and indicative amount.
- Unit options come from the active governed unit catalogue; Budget Lines come from the eligible Budget contract.
- Required-by must fall inside the selected FY. Amount and quantity must be positive.
- Save creates no Need, bypass reason, reservation or Strategy link.
- A submitted, accepted or another department's entry is never editable through a direct URL.

### 12.5 PLN-UI-05 — HoD submission

- Recalculate readiness from current authoritative sources when the page loads and again inside the submit transaction.
- Certification is available only to the HoD or acting HoD holding the same role and exact current OU/FY User Permission.
- Submission locks one immutable snapshot and creates one validation task atomically.
- A repeated command with the same idempotency key returns the original submission and task.
- A concurrent source, Budget Line or DPP change returns `PLN_DPP_STALE` and creates no partial submission.

### 12.6 PLN-UI-06 — DPP validation task

- Load the exact immutable DPP submission and all submitted entry details before any decision controls.
- Requirement-type options come from the governed active catalogue. Classification does not edit the submitted source row.
- **Accept departmental plan** requires one classification for every entry, current source versions, no unresolved issue and maker-checker compliance.
- **Return to department** opens a structured issue dialog. At least one issue with affected entry, concise problem and correction required is mandatory.
- Decision commands recheck task token, assignment, state, sources and segregation under one transaction.
- Acceptance completes the task and places every accepted entry in the open Draft Annual Plan as an unallocated source. If this is the first accepted DPP for the PE/FY, the same transaction inserts the uniquely constrained Annual Plan root and Draft Version 1. If a concurrent acceptance won that insert, the command reloads and reuses the winner inside the transaction. It does not form a Plan Item, reserve funds or approve expenditure.
- Return completes the task, preserves the submission and creates the correction Draft atomically.

### 12.7 PLN-UI-07 and PLN-UI-08 — Annual Plan workbench and formation

- There is no **Begin consolidation** command, page or permission gate. The initial Draft Annual Plan already exists after the first DPP acceptance.
- Each later DPP accepted before the initial Plan is submitted adds its entries automatically to the same Draft Version's unallocated-source queue.
- The Planner may form Plan Items incrementally and does not wait for the submission window to close, every department to submit or a department to declare a nil plan.
- A DPP accepted after the current Plan Version has been submitted cannot alter that immutable Version and does not interrupt its governance. Its entries appear as **Pending addition** in the workspace and become available in the next Draft successor after the current Version is activated.
- A DPP successor that replaces a source already allocated to a mutable Draft item marks that item **Source correction required**. It does not rewrite or move the allocation. The Planner must dissolve and re-form the item from the current source.
- Source selection lists only current accepted entries in the exact PE/FY that are not already allocated in the open Version.
- One selected source creates one Plan Item without asking for an unnecessary second choice.
- Several selected sources require **one each** or **one combined**. Combined formation requires the same PE/FY, Budget, currency, requirement type, unit and treatment plus a complete aggregation reason before the item is ready.
- Formation is atomic and idempotent. A unique active allocation prevents concurrent duplicate use.
- A single created item opens its editor. Several separately created items return to the workbench.
- The Planner never creates a blank source-less Plan Item.
- Draft summary counts, value and blockers are derived from source allocations and current item states.
- **Dissolve Plan Item** appears only for an item in a mutable Draft Version. Confirmation states that its sources will return to the unallocated list and any effective funding hold will be released. The server completes cancellation, release and allocation updates atomically or changes nothing.

### 12.8 PLN-UI-09 — Plan Item editor

- Load an existing formed item and every allocation read-only. Source selection, regrouping and partial allocation are absent; regrouping is done by dissolving the Draft item and forming again.
- For a single source, default title from the source. For combined sources, require a Planner-entered package title and aggregation reason.
- Strategic Objective options are only current eligible Active Objectives and show title plus hierarchy path.
- The server assigns Open Tender as the sole admitted MVP method. It is displayed read-only and the UI does not present a one-option selector.
- Save accepts only title, description, Strategic Objective, aggregation reason when combined and seven planned dates.
- Requirement type, quantity, unit, source details, Budget Lines and planned value are derived and read-only.
- Schedule validation binds each failure to the exact date control and explains the chronological or required-by conflict.
- **Save draft** creates no Finance task. **Request Finance confirmation** saves and fully validates in one transaction, then creates/reuses one current task.
- A change to the source set, Budget Line, amount or currency after Finance confirmation releases the affected Draft reservation remainder, marks Finance Stale and requires new confirmation. A title, description, Objective, aggregation reason, method or schedule edit retains the reservation but it is revalidated before Plan submission. No reservation is silently adjusted.

### 12.9 PLN-UI-10 — Finance task

- Authorise task assignment, PE/FY and Budget scope before returning any protected position.
- Reload every Budget Line position at the command time; the displayed As-at time must match the snapshot.
- **Confirm funding** is available only when every allocation has full availability. The command locks all lines and sources and creates all reservations or none.
- A shortfall omits Confirm, displays the exact deficient source and after-confirmation result, and creates no partial reservation.
- **Return to planner** requires one actionable correction reason and creates no reservation.
- The task contains no editable amount, Budget Line, Plan field or optional note.
- Navigation to Budget & Funding preserves the Planning task and creates no mutation in either module.

### 12.10 PLN-UI-11 and PLN-UI-12 — Annual Plan decisions

- Each task loads the exact immutable submitted Plan Version and displays every Plan Item, source summary, Strategic Objective, method, completion date, value and Finance result before decision controls.
- The Accounting Officer may adopt and submit the complete Plan or return it for correction.
- Adoption creates exactly one statutory-approval task resolved from governed PE type and jurisdiction.
- The statutory authority may approve the Accounting-Officer-adopted Plan or return it for correction.
- For a Board or similar body, approval records the collective decision and mandatory resolution reference; the data-entry user is not represented as the sole authority.
- Every return requires one actionable correction. No reason category or optional note exists.
- Every decision rechecks the exact role or legal capacity, native User Permission, task token, source currency, Objective eligibility and Finance freshness.
- No Head of Procurement Function, professional reviewer, generic committee or publication approval is inserted.
- A return preserves the submitted snapshot and creates a copied correction Draft containing only that snapshot's sources. Pending DPP additions remain outside it.
- Corrected submission revalidates every reservation. It repeats Finance only for an item whose source set, Budget Line, amount or currency changed, whose reservation is absent, released or `Needs Attention`, or whose Budget revalidation fails.
- Every corrected submission creates a new immutable snapshot and restarts at Accounting Officer adoption, including a correction returned from statutory approval.

### 12.11 PLN-UI-13 — Publication

- After statutory approval, the system serialises and transmits the exact approved Plan through the configured adapter.
- Acknowledgement activates the Version and supersedes the predecessor where applicable.
- Failed or indeterminate transmission preserves approval and permits an idempotent technical retry of the same payload by System Manager.
- There is no manual acknowledgement, payload edit, successful-result override or business publication decision.

### 12.12 PLN-UI-14 — Active Plan and successor

- Display the Active Version and its complete item baseline read-only.
- Requisition availability is a live neutral projection, not a Planning edit control.
- **Prepare plan update** creates/reuses the sole Draft successor after authority and state checks.
- The Active predecessor remains operational while the successor is Draft, returned or under governance.
- An item may be proposed for whole-item removal only after fresh downstream checks show no drawdown, Tender handoff, commitment or contract.
- Cancelling a Draft successor releases only successor-created reservations and leaves the Active predecessor unchanged.
- An acknowledged successor atomically becomes the sole Active Version; unchanged lineage is preserved, removed items cease future eligibility and their unconverted reservation remainder is released only after the downstream-use checks pass.
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
- Annual Plan and Version creation, each source allocation, dissolution, source-correction flag and every Planner field change;
- Finance task iterations, Budget snapshots used for decisions, reservation references, revalidation and release results;
- each Accounting Officer and statutory-approval task and immutable decision;
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
| `grace.wanjiku@moh.example.test` · Grace Wanjiku | Departmental Author for PE-MOH / OU-MOH-DHI and OU-MOH-HRMD |
| `peter.kimani@moh.example.test` · Dr Peter Kimani | Head of User Department for OU-MOH-HRMD and OU-MOH-DHI, except that his OU-MOH-DHI permission is ineffective from 26 to 30 Nov 2026 |
| `julia.njeri@moh.example.test` · Julia Njeri | Acting Head of User Department for OU-MOH-DHI from 26 to 30 Nov 2026, using the same role and a time-bound native User Permission; Peter's OU-MOH-DHI permission is ineffective during this period |
| `mercy.kilonzo@moh.example.test` · Mercy Kilonzo | Procurement Planner for PE-MOH; DPP classification and Annual Plan preparation |
| `moh.budget.officer@example.test` · MOH Budget Officer | Finance confirmation for PE-MOH and the named Budget Lines |
| `amina.hassan@moh.example.test` · Amina Hassan | Accounting Officer for PE-MOH |
| `moh.plan.approver@example.test` · MOH statutory approver | Responsible Cabinet Secretary for the PE-MOH fixture; exactly one statutory route |
| `peter.ouma@audit.example.test` · Peter Ouma | Planning Auditor read for PE-MOH |
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
| Expected operational result | Priority health facilities can use secure and interoperable digital health services. |
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
| Accounting Officer adoption | `AOD-MOH-2027-001-V1` · Amina Hassan · 8 Dec 2026, 10:00 EAT |
| Statutory approval | `APP-MOH-2027-001-V1` · Responsible Cabinet Secretary · 9 Dec 2026, 11:00 EAT |
| Publication attempt | `PUB-MOH-2027-001-A1` · System · 10 Dec 2026, 14:55 EAT |
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
| Expected operational result | The Ministry receives a prioritised and actionable security remediation plan. |
| Quantity | 1 service |
| Required by | 31 Oct 2027 |
| Budget Line | `MOH-BL-DHI-2027` |
| Indicative amount | KES 20,000,000 |
| Classification | Consulting services |
| Source origin | Direct departmental requirement |
| Need lineage | None |

Profiles shall prove a direct-only DPP, a Need-only DPP and a mixed DPP. No profile creates a synthetic Need or bypass reason.

### 14.8 Isolated combined-source fixture

| Source | Department | Quantity | Required by | Budget Line | Currency | Amount | Classification |
|---|---|---:|---|---|---|---:|---|
| Clinical training laptops for digital health rollout | Human Resources Management and Development | 200 each | 31 Dec 2027 | MOH-BL-HWD-2027 | KES | KES 48,000,000 | Goods |
| Clinical deployment laptops for digital health rollout | Digital Health | 300 each | 31 Dec 2027 | MOH-BL-DHI-2027 | KES | KES 72,000,000 | Goods |

Both sources resolve to the one PE-MOH/FY-2027-2028 procurement Budget. The combined item is `PPI-MOH-2027-033`, totals 500 each and KES 120,000,000, completes on 31 Dec 2027, and uses the exact title, description and aggregation reason in PLN-DES-09A. It is isolated because its funding requirements exceed the default live baseline.

### 14.9 KEBS first-slice profile

The KEBS profile uses these exact departmental source lines:

| Source line | Requirement | Quantity | Expected operational result |
|---|---|---:|---|
| `SRC-KEBS-ICT-001` | Business laptops | 25 Each | Mobile officers can run approved office and standards applications securely. |
| `SRC-KEBS-ICT-002` | Desktop computers with monitors | 15 Each | Fixed workstations replace unsupported equipment at the Coast Region office. |
| `SRC-KEBS-ICT-003` | Business tablets | 10 Each | Field officers can capture and review inspection information away from the office. |

The profile runs once from three Accepted Departmental Needs and once from three direct DPP entries. Both produce the same source facts and form `PPI-KEBS-2026-ICT-001`. The Plan Item preserves all three source allocations and contains no specification, attachment, supplier evidence or Tender security.

### 14.10 Seed execution rules

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
| PLN-AC-001 | Zero, one and multiple authorised PE plus configured-FY option cases fail closed and disclose no unauthorised data. |
| PLN-AC-002 | Workspace reads and direct routes create no record. |
| PLN-AC-003 | One DPP root is created idempotently per PE/FY/OU. |
| PLN-AC-004 | Every current accepted Need appears once with six read-only facts, including expected operational result, and no Budget, Strategy or classification from Needs. |
| PLN-AC-005 | A direct-only DPP can be created and submitted without any Need. |
| PLN-AC-006 | A mixed DPP retains distinct source origins and creates no synthetic Need. |
| PLN-AC-007 | Direct requirement input is limited to the eight defined values. |
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
| PLN-AC-024 | A changed source set, Budget Line, amount or currency, or a failed Budget revalidation, makes prior Finance evidence Stale; narrative, Objective and schedule changes alone do not. |
| PLN-AC-025 | Accounting Officer and statutory-approval tasks each show the complete immutable Plan before decisions. |
| PLN-AC-026 | The Accounting Officer adopts or returns the complete consolidated Plan. |
| PLN-AC-027 | Exactly one statutory authority approves or returns the same Accounting-Officer-adopted Version. |
| PLN-AC-028 | Every return requires one actionable correction and preserves the submitted snapshot. |
| PLN-AC-029 | Approval authorises only the exact system publication payload and does not itself activate the Plan. |
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
| PLN-AC-041 | No Head of Procurement Function, professional reviewer, generic approval committee or publication approver exists in the Annual Plan chain. |
| PLN-AC-042 | A Board or similar-body approval records the collective decision and resolution reference. |
| PLN-AC-043 | Publication is an idempotent system action; any technical retry reuses the exact approved payload. |
| PLN-AC-044 | Native Frappe Role, Workflow permission and User Permission enforce PE/FY/OU scope without another permission store. |
| PLN-AC-045 | Requisition eligibility exposes every source allocation, expected operational result and exact remaining quantity and value. |
| PLN-AC-046 | The KEBS Needs-origin and direct-entry profiles produce equivalent approved source lineage. |
| PLN-AC-047 | A mutable Draft Plan Item can be dissolved; open Finance work is cancelled, effective reservations are released and its sources become available for re-formation without deleting history. |
| PLN-AC-048 | Dissolution is blocked after Plan submission and fails atomically when reservation release fails. |
| PLN-AC-049 | Reservation revalidation and every Planning-triggered release use the Budget-owned service and preserve exact correlation evidence. |
| PLN-AC-050 | Governance correction preserves the returned snapshot, excludes pending additions and restarts at Accounting Officer adoption. |
| PLN-AC-051 | Finance repeats on correction only for the defined stale conditions; narrative, Objective and schedule changes alone do not create replacement reservations. |
| PLN-AC-052 | Acceptance of a DPP successor never rewrites an allocated source; mutable Draft items require dissolve and re-form, submitted Plans require return, and Active Plans wait for a successor. |
| PLN-AC-053 | A withdrawn initial DPP can reopen only as the next Version while the initial window is Open. |
| PLN-AC-054 | Accepted Needs stranded by a closed DPP window remain visible with the exact not-included status and gain no late-submission bypass. |
| PLN-AC-055 | Combined Plan Items reject different Budgets or currencies. |
| PLN-AC-056 | Sequential Requisitions may draw one Plan Item while balances remain, subject to the Requisition module's one-open rule. |
| PLN-AC-057 | The maker-checker matrix blocks every prohibited same-user action pair and no unlisted approval level is introduced. |
| PLN-AC-058 | Concurrent first-DPP acceptance creates exactly one Annual Plan root and one open Version. |
| PLN-AC-059 | Planning has one navigation entry and no role-specific work-queue menu. |
| PLN-AC-060 | Planning context is server-authorised, visible and changeable; local storage never grants access or permanently binds PE/FY. |
| PLN-AC-061 | Draft, Accounting Officer, statutory approval and Active surfaces render the same generated Annual Plan title and the governance surfaces use the exact immutable fixture row and total. |
| PLN-AC-062 | The combined-source fixture has deterministic required-by dates and its completion date satisfies both sources. |

### 15.1 Minimum automated coverage

1. Domain tests for DPP coverage, direct-entry fields, source immutability, classification, formation/dissolution compatibility, correction restart, schedule, Objective eligibility and lifecycle transitions.
2. Permission tests for every role, PE/FY/OU boundary, task assignment, acting-HoD period and maker-checker rule.
3. Contract tests for Needs events, Strategy Objective selection, Budget Line eligibility, all-source reservation, revalidation/release, publication adapter and Requisition eligibility.
4. Transaction tests for submission, concurrent first-DPP acceptance, formation, dissolution, Finance, governance correction, successor cancellation, publication acknowledgement and concurrent retries.
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
- Keep the Frappe header, breadcrumb and navigation outside the Vue artboard. Render the Planning-specific PE/FY selectors inside the Planning workspace page content exactly as defined in PLN-DES-01.
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
- screenshots for PLN-DES-01 through PLN-DES-16 at 1440 × 1024;
- scripted click-through of direct-only DPP, accepted-Need DPP and integrated Active Plan;
- zero page-specific console errors and failed network requests; and
- confirmation that no design-runtime or removed field remains in production code.

## 17. Prohibited shortcuts

Implementation shall not:

- make Departmental Needs a prerequisite for a DPP entry;
- create a synthetic Need or collect a bypass reason for a direct requirement;
- source Strategy, requirement type, Budget Line or amount from Departmental Needs;
- let Planning edit accepted Need facts;
- add a field because it appeared in an old document or visual;
- add Value Commitment, source reference, generic evidence, optional note, attachment, contract period, lotting or actual milestone fields;
- create an Annual Plan or task from a page read;
- create a source-less Plan Item or partially allocate a DPP entry;
- accept a client-computed value, permission, state, balance or approval route as authoritative;
- reserve only part of a combined item;
- release or mark a Budget reservation through a local Planning-table update;
- rewrite an allocated source automatically when a DPP successor is accepted;
- hide full Plan details from the Accounting Officer or statutory approver;
- insert professional review, Head of Procurement Function approval, a generic committee or publication approval into the Accounting Officer plus one-statutory-approval chain;
- activate on approval or on an unacknowledged publication attempt;
- expose create-Requisition or create-Tender actions from Planning;
- import Claude Design runtime, `.dc.html`, Tailwind utilities or copied vendor markup into production;
- create a role-specific sidebar work-queue entry;
- treat a browser-stored PE/FY value as permission or prevent the user from changing an authorised Planning Financial Year;
- draw or replace the Frappe breadcrumb or header inside the page;
- maintain old routes, aliases, duplicate fields or compatibility reads; or
- use a full-suite test run as the first diagnostic step for a focused defect.

## 18. Traceability and precedence

This document incorporates the approved boundary decisions from:

- CFG-CHG-002 v0.3 — PE/FY context and configuration ownership;
- STR-CHG-001 v1.3 — exactly one Active Strategic Objective on each Plan Item and no Value Commitment;
- BUD-CHG-001 v1.1 — Planning-owned Finance task, Budget-owned live position and reservations; and
- NDS-CHG-001 v1.1 — optional consultation, direct departmental planning path, six Need values and Planning-owned DPP funding specification; and
- REQ-CHG-001 v1.2 — partial Plan Item drawdown, one-open-Requisition control, reversal and remaining balances.

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

## 19. E2E-REQ-001 conformance

| End-to-end control | Procurement Planning implementation |
|---|---|
| Structured information is primary | DPP entries and Plan Items are governed records; attachments do not replace requirement data. |
| Enter once, carry forward | Accepted Need facts and direct-requirement facts flow into the Plan and Requisition-eligibility projection without re-entry. |
| Ownership remains clear | Planning may classify and fund a requirement, but it cannot rewrite accepted departmental facts. |
| Stable lineage | Every Plan Item preserves its exact DPP entry and Need-version source where applicable. |
| Minimal approval chain | The Accounting Officer adopts the complete Plan and exactly one statutory authority approves it. Publication is a system action. |
| No STD configuration dependency | Planning exposes governed requirement lineage; it does not create, select or configure a tender template. |

## 20. Approval effect

PLN-CHG-001 v1.1 remains approved until this successor is approved. On approval, PLN-CHG-001 v1.2 supersedes v1.1 in full and becomes the only Procurement Planning requirements document to consult.

Approval authorises implementation of the complete clean Procurement Planning module and conversion of section 11 into Claude Design artboards. It does not approve generated visual deviations, production publication configuration, a Procurement Requisition, a Tender or any field not defined here.
