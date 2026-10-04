# REQ-CHG-001 — Structured Procurement Requisitions

| Control | Value |
|---|---|
| Document ID | REQ-CHG-001 |
| Version | 1.9 |
| Date | 16 September 2026 |
| Status | **Approved** |
| Approved on | **16 September 2026** |
| Supersedes | v1.8 and all earlier Requisition versions in full. |
| Module | Procurement Requisitions |
| First released product | Straightforward IT equipment |
| Standards | Governed by KT-STD-001 v1.6 and STD-STD-001 v1.1. Sections not restated here are inherited from them. |
| Implementation posture | Correct the module in place; no STD Configuration dependency and no attachment-first specification model |
| Change type | Complete successor incorporating approved REQ-UX-001 v0.3 into the current PLN v1.20/BUD v1.9/NDS v1.13/CFG v0.11/STR v1.8 owner baseline. It replaces the five-screen preparation experience with three plain-language tasks, adds atomic shared-item and standard-package operations, and preserves the existing lifecycle, source, funding, structured-requirement and audit controls. Full changes: §22.2. |

**Controlling decision:** A Procurement Requisition draws one or more exact eligible source allocations from one stable Active Plan Item into one precise departmental request. For the first release, the department completes a fixed, code-owned IT Equipment Requirement Package. Structured items, technical requirements, services and acceptance checks are the authoritative requirements. Files may support those rows but cannot replace them.

## 1. Governing decision

This approved complete successor is the sole Procurement Requisitions implementation authority. It retains the complete structured equipment catalogue, five internal validation groups, immutable governance, roles and owner controls, but presents preparation as three user tasks: **Request details**, **Requirements**, and **Review and submit**. It incorporates all 84 v1.8 acceptance results plus 34 approved usability results. REQ-UX-001 v0.3 is approval evidence, not a parallel implementation specification.

The module shall not contain an STD selector, Requirements Composer Manifest, schema editor, mapping editor or generic requirements engine. Tender Preparation selects the released Tender template after Requisition authorisation.

Implementation must produce one coherent result across schema, services, permissions, screens, fixtures and tests. A field, action, state, role, screen or service not defined here is outside this release.

### 1.1 Corrected earlier directions

| Earlier direction | Current treatment |
|---|---|
| Requisition binds to a Requirement Composer Manifest from STD Configuration | Removed. The first release uses the code-owned IT Equipment Requirement Package in §6. |
| Technical specification PDF as the primary requirement | Removed. Structured rows are authoritative; TPR-CHG-001 consumes them downstream. |
| Custom Capability Profiles, Operational Scope Assignments, native Frappe Roles, Workflow permissions and User Permissions | Removed. AUTH-ADR-001 v1.7’s role-bound `User Responsibility Assignment`, resolved through registered `permission_query_conditions` and `has_permission` hooks, is the sole authorisation mechanism. |
| `pe_fy_context_id` on the Requisition record | Removed. One site is one Procuring Entity, configured once by CFG-CHG-002 and never selected or scoped per record. Fiscal Year is inherited display data from the Plan Item, never a scope dimension. |
| "A second budget check or reservation" named as explicitly unsupported | Corrected. §9.1A makes Requisition authorisation invoke Budget’s complete-array reservation contract. |
| One Requisition uses one Plan Item and one requesting department | Narrowly relaxed under §§2.1 and 7.5: a Planning-approved cross-department combined item retains exactly its contributing departments; Requisition cannot add another department. |
| Golden fixture keyed to Kenya Bureau of Standards | Removed. Renamed to Ministry of Health throughout, per SEED-001 v1.3. |
| Upstream correction as one sentence of intent | Replaced by the complete request, hold, outcome and fresh-start contracts in §§7.4A–7.4B and 9.1B. |

## 2. Purpose

Procurement Requisitions shall:

- start from one eligible Active Plan Item and its exact source allocations;
- show all approved Planning facts read-only;
- let the requesting department, or departments where the Plan Item was itself formed as a cross-department combine, state the exact quantity and value being requested;
- capture a complete structured IT Equipment Requirement Package;
- preserve every Planning, item and requirement identifier;
- let the Head of User Department submit the departmental request;
- let the Head of Procurement Function authorise or return it;
- commit the Planning drawdown and the Budget reservation only on authorisation, atomically;
- create one immutable handoff for Tender Preparation; and
- provide clear correction routes without rewriting approved history.

### 2.1 First-release boundary

The first release supports:

- the implicit site Procuring Entity and one Financial Year, inherited from the Plan Item;
- one Active Plan Item per Requisition;
- one requesting department, **or**, only where the Plan Item was formed at Planning as a cross-department combine, exactly the departments that contributed to it — never a department that did not;
- one or more source allocations belonging to an eligible requesting department;
- straightforward off-the-shelf IT equipment;
- goods supplied in Kenya Shillings;
- one Requisition per proceeding and one later award package; sequential Requisitions may draw remaining original allowance under §5.1;
- whole-number equipment quantities in `Each`;
- structured pass/fail technical requirements;
- the inherited reservation category and lotting indicator, carried through unedited; and
- the released `IT-EQUIPMENT-OPEN-V1` Tender pattern.

It does not support:

- custom software, systems implementation, integration, migration or hosting;
- Works, consulting services or non-consulting services;
- multiple currencies, lots or award packages;
- multi-year procurement or future-year funding commitments;
- a Requisition drawing from a department the source Plan Item never included;
- a generic specification editor or rich-text Terms of Reference;
- supplier qualification, Tender security, evaluation criteria or contract clauses;
- bidder responses, prices, evidence or evaluation results; or
- Requisition approval levels beyond those in section 8.

**On the cross-department relaxation.** This is deliberately narrow. It does not open Requisitions generally to spanning departments; it recognises that Planning already made a governed decision to combine sources from more than one department into one Plan Item, with its own combine rule, its own aggregation reason, and its own record of which departments contributed. The Requisition reflects that decision; it does not re-litigate it, and it cannot combine departments Planning did not already combine.

### 2.2 Field-purpose rule

A stored field is permitted only when this document names:

1. the current decision or output using it;
2. its control, source and validation; and
3. its effect on validation, handoff, Tender output or contract obligation.

"Useful later", "normally captured", "helpful context" and "present in an old form" are not valid reasons. An undefined field is omitted.

## 3. Ownership and module boundary

| Information or action | Owner | Requisition treatment |
|---|---|---|
| Active Plan, Plan Item and source allocations | Procurement Planning | Read exact eligibility and remaining balances; never edit. |
| Need, description and expected operational result | Requesting department through Needs or Planning | Inherit read-only; return upstream if materially wrong, per §7.4A. |
| Requested drawdown | Requesting department(s) | State within remaining Planning quantity and value, per department where more than one contributed. |
| Equipment items and intended use | Requesting department | Create as structured rows linked to Planning sources. |
| Minimum technical characteristics | Requesting department | Create as structured rows using released controls. |
| Warranty, support, related services and acceptance | Requesting department | State the required operational result in fixed controls. |
| Budget Line, funding, planned method, schedule, reservation category and lotting indicator | Planning and Budget | Inherit read-only. Authorisation rechecks Planning availability **and creates the Budget reservation**, per §9.1A — REQ owns the authorisation decision and invocation; **Budget owns reservation records, balances, locking and ledger effects**. No direct Budget mutation by REQ. |
| Supplier evidence, qualification and Tender choices | Procurement | Add later in Tender Preparation; never require the department to define them. |
| Standard Tender text and released forms | Code-owned Tender template | Requisition neither selects nor edits them. |
| Requisition authorisation | Head of Procurement Function | Decide the complete immutable submission; cannot edit it. |
| Tender creation and approval | Tender Preparation | Consume the immutable handoff and apply its own approved lifecycle. |

Procurement staff may help the department express a requirement. A competent technical officer may contribute. This does not create another task, reviewer or approval stage. The Departmental Author remains responsible for the Draft and the Head of User Department confirms the departmental request.

## 4. Stable lineage

Every material row keeps a stable identifier.

| Identifier | Created by | Carried to |
|---|---|---|
| `source_line_id` | Planning projection of stable Need ID or direct-source ID, tagged by source origin | Plan, REQ, Tender and contract lineage; exact revision is separately retained. |
| `plan_item_line_id` | Planning’s exact `PlanSourceAllocation` ID exposed under this wire key | Requisition drawdown and Tender; never a display row number or a guessed PIL alias. |
| `requisition_item_id` | Requisition | Goods schedule, price schedule and contract schedule |
| `technical_requirement_id` | Requisition | Technical schedule, bidder response and evaluation |
| `service_requirement_id` | Requisition | Service schedule, bidder response and contract obligation |
| `acceptance_requirement_id` | Requisition | Acceptance schedule and contract obligation |
| `supporting_material_id` | Requisition | Tender package index and the structured rows it supports |
| `reservation_id` | Created by Budget’s owner service inside REQ authorisation | Handoff, and Budget's own Active reservations table |

Descriptions are not identifiers. The system shall not reconstruct lineage by comparing text.

## 5. Canonical domain model

All identifiers, references, version numbers, digests, actors and timestamps are server-managed.

### 5.1 ProcurementRequisition

Stable root for one departmental request against one Active Plan Item.

| Field | Purpose and rule |
|---|---|
| `requisition_id` | Immutable internal identity. |
| `requisition_reference` | Generated `REQ-{PE code}-{FY start}-{Plan Item number}-{3 digits}`. There is no `pe_fy_context_id`; the site is implicit and the Fiscal Year is read from the Plan Item. |
| `plan_id` / `plan_version_id` / `plan_item_id` / `plan_item_version_id` | Stable roots and exact approved content supplying this Requisition, pinned at preparation and immutable. A changed baseline requires an explicit new Requisition/follow-up against current eligible lineage; no root silently switches its approved content. |
| `strategic_objective_id` / `strategic_objective_path` | Inherited read-only from PLN v1.20’s exact Active item and Strategy snapshot fixed at final statutory Plan approval. Carried explicitly here, and into the handoff in §5.12, rather than left reachable only by a second query back into Planning — an auditor reading the Requisition alone can see which policy objective justified it. |
| `procurement_category` | **New.** Inherited read-only; `Goods` for this release, checked at compatibility per §5A. |
| `plan_horizon` | Inherited fixed `Single year`; Multi-year is outside this MVP and fails preparation/authorisation. No editable horizon or operative multi-year justification. Historical received fields are retained as history, not accepted as spendable future-year allowance. |
| `contributing_org_unit_ids` | One or more Organisation Units — one, in the ordinary case; more than one only where the Plan Item was itself formed at Planning as a cross-department combine, matching exactly the departments Planning's own combine recorded. Immutable. |
| `lead_org_unit_id` | Current routing department; initial default is the largest drawn value aggregated by contributing OU, with a deterministic stable-OU-ID tie break. Freeze the certified lead in each submitted Version. HOPF’s Change lead department at authorisation review requires reason and returns a copied Draft for the new lead’s certification; it never relabels the old submission. §7.3A. |
| `current_version_id` | Current Draft, submitted or authorised Version. |
| `authorised_version_id` | Exact authorised Version; empty before authorisation. |
| `current_state` | Derived root state from section 7. |
| `planning_drawdown_reference` | Planning reference created only on authorisation. |
| `reservation_ids` | Budget reservation references, one per drawdown line, created only on authorisation. Empty before it. |
| `handoff_id` | Immutable downstream handoff; empty before authorisation. |
| `handoff_consumed_at` | Neutral downstream-consumption projection. |
| `prior_requisition_id`, `prior_requisition_version_id`, `planning_correction_request_id`, `planning_correction_outcome_event_id` | Optional system-generated follow-up lineage for an explicit fresh Requisition after an upstream outcome; no edited old Version or inferred text matching. |
| `record_version` | Optimistic-concurrency token. |

Only one open Requisition may exist for the same **stable `plan_item_id` across every department, Plan Version and user**, enforced by an authoritative storage guard and command serialization.

Open means a current Draft, Awaiting Department Approval, Submitted to Procurement, or Authorised with **unconsumed** handoff. A Return creates a new current Draft and keeps the root open; Returned is the older Version’s status. A stopped `Upstream correction required`, Withdrawn or Revoked root is terminal unless its explicitly permitted corrected-Draft command opens a new current Version. An Authorised root with confirmed handoff consumption remains authorised history but no longer occupies the open slot. It never releases its drawdown merely because the slot is free.

A later eligible Requisition can use only remaining original allowance. It gets its own root, drawdown and reservations; it cannot add sources or increase the locked item’s original scope. Existing open work is returned only as an authorized route; another department does not obtain edit rights or a duplicate by attempting Prepare. A fresh correction root and a revoked-root successor compete for this same stable-item guard.

### 5.2 RequisitionVersion

One complete decision snapshot.

| Field | Purpose and rule |
|---|---|
| `requisition_version_id` | Immutable Version identity. |
| `requisition_id` | Stable parent. |
| `version_number` | Generated sequence. |
| `based_on_version_id` | Returned or revoked Version copied for correction. |
| Preparation authority evidence | System-recorded actor, exercised role/capacity and exact assignment at preparation/routing; distinguishes direct HoD preparation from an Author requesting departmental approval. No editable actor/authority control. |
| `version_status` | `Draft`, `Awaiting Department Approval`, `Submitted to Procurement`, `Returned`, `Authorised`, `Withdrawn`, `Revoked`, `Upstream correction required` or `Superseded`. |
| `requirement_title` | Required; 5–160 characters. Initially inherited from Planning and editable only while Draft. |
| `delivery_location_id` | Required Link to an Active Location. |
| `delivery_address_snapshot` | Generated from the selected location at submission. |
| `latest_delivery_date` | Required operational delivery date; no later than the approved **source-derived Plan completion boundary** or any selected source required-by. Do not substitute the separately calculated estimated completion date. |
| `certified_lead_org_unit_id`, departmental submission authority | Frozen lead and exact submitting actor/assignment/capacity at departmental submission; an HOPF routing change cannot rewrite them. |
| `related_services_required` | Required Yes/No. |
| `package_version_id` | Exact IT Equipment Requirement Package Version. |
| `content_digest` | Canonical digest created on lock. |
| `record_version` | Draft concurrency token. |

Business need, description and expected operational result are inherited Planning facts. They are not copied into editable fields.

### 5.3 RequisitionDrawdownLine

| Field | Purpose and rule |
|---|---|
| `drawdown_line_id` | Stable line identity. |
| `requisition_version_id` | Owning Draft or locked Version. |
| `plan_item_line_id` | Exact eligible `PlanSourceAllocation` ID from Planning; stable item and exact item/Plan/accepted DPP/source revision lineage are retained in the submitted snapshot. |
| `source_line_id` | Original Need or direct-DPP lineage. |
| `contributing_org_unit_id` | Which of `contributing_org_unit_ids` this specific line belongs to. Always one value, even when the Requisition itself spans more than one department. |
| `approved_quantity` / `approved_value` | Read-only Planning values. |
| `remaining_quantity` / `remaining_value` | Read-only evaluation-time values. |
| `requested_quantity` | Exact positive whole-number Quantity string, not above remaining quantity; §5.14. |
| `requested_value` | Exact positive KES Money string in currency units, not above remaining value; §5.14. |
| `unit` | Read-only Planning unit; `Each` for the first product. |
| `reservation_id` | Empty until authorisation; one reservation per drawdown line, per §9.1A. |

At submission, requested lines are locked. At authorisation, Planning rechecks every line and commits all or none, and Budget reserves every line's value or none.

### 5.4 ITEquipmentRequirementPackage

Stable package root created with the Requisition. It has no configurable profile, manifest or user-selected schema. The server-managed code release key in §5.5 identifies only the standard Laptop proposal that was shown; it is not a selectable domain object or configuration surface.

| Field | Purpose and rule |
|---|---|
| `package_id` | Stable identity. |
| `requisition_id` | One-to-one owning Requisition. |
| `product_pattern` | Fixed `IT Equipment`. Read-only. |
| `current_version_id` | Current package Version. |
| `authorised_version_id` | Authorised package Version. |
| `reservation_category` | Read-only, inherited from the Plan Item. Never edited here. |
| `lotting_indicator` | Read-only, inherited from the Plan Item. Confirmed as `Single lot` at product-suitability check; any other value is incompatible with this release. |

### 5.5 ITEquipmentRequirementPackageVersion

| Field | Purpose and rule |
|---|---|
| `package_version_id` | Immutable Version identity after lock. |
| `package_id` | Stable parent. |
| `version_number` | Generated sequence aligned with the Requisition Version. |
| `based_on_version_id` | Source Version copied after return or revocation. |
| `version_status` | Same decision state as the owning Requisition Version. |
| `minimum_warranty_months` | Required integer 1–120. |
| `onsite_support_required` | Required Yes/No. |
| `maximum_support_response_hours` | Integer 1–168; required only when on-site support is Yes. |
| `manufacturer_support_required` | Required Yes/No. |
| `service_location_constraint` | Required Select: `None`, `Within Kenya`, `At delivery location`. |
| `support_description` | Optional plain text, maximum 500 characters; cannot contradict controlled values. |
| `standard_profile_key` / `standard_profile_version` | Server-managed evidence of the code-owned starting proposal used for this Draft. For the routine fixture: `LAPTOP-REQUIREMENTS-V1`. It is required for new v1.9 proposal-generated content and may be null only on preserved historical content that predates it. It is not selectable, editable in Desk or a configuration object. |
| `standard_package_review_state` | Derived `Not generated`, `Review required` or `Reviewed`. `Review required` blocks routing. `Reviewed` is recorded only when the complete visible selected payload succeeds atomically. |
| `content_digest` | Canonical digest of every package row and file reference. |

### 5.6 RequisitionItem

At least one item is required.

| Field | Control and rule |
|---|---|
| `requisition_item_id` | Generated, read-only. |
| `package_version_id` | Owning package Version. |
| `drawdown_line_id` | Required exact link to one selected REQ drawdown line. Item quantity reconciles against this line. |
| `plan_item_line_id` | Read-only projected exact Planning allocation from that drawdown line; never used as if it were the REQ drawdown primary key. |
| `equipment_category` | Required Select: `Laptop`, `Desktop computer`, `Monitor`, `Tablet`, `Printer`, `Scanner`, `Network equipment`, `Power-protection equipment`, `Other IT equipment`. |
| `item_name` | Required single-line text, 3–120 characters. |
| `quantity` | Required positive whole-number Quantity string; exact arithmetic, §5.14. |
| `unit` | Read-only `Each`. |
| `intended_use` | Required plain text, 10–500 characters. |
| `delivery_location_id` | Defaults from Version; may select another Active location for the same site. |
| `latest_delivery_date` | Defaults from Version; may be earlier, never later. |
| `row_order` | Generated stable display order. |

The total item quantity linked to a drawdown line must equal that line's requested quantity before submission. `Other IT equipment` requires a specific supplier-neutral item name; it does not create a new template category.

Where selected approved requirements use the same category and specification, the UI may capture shared `equipment_category`, `item_name`, `delivery_location_id` and `latest_delivery_date` once. The server still creates one `RequisitionItem` per selected drawdown line, each with its own source, quantity and intended use. Creation and shared-detail updates are atomic; a failure creates or changes none of the selected rows. Editing or removing one source-linked item never silently changes another item’s source-specific values.

### 5.7 TechnicalRequirement

Each enforceable technical characteristic is a separate row.

| Field | Control and rule |
|---|---|
| `technical_requirement_id` | Generated, read-only. |
| `applies_to` | Required Link to one Requisition Item or `All items`. |
| `row_state` | `Proposed` only for server-generated Draft suggestions; `Confirmed` after grouped application or deliberate manual addition. Proposed rows can be edited/cleared but never enter a locked Version or handoff. |
| `characteristic_key` | Required Select from the released catalogue in section 6.3. |
| `comparison` | Fixed by the characteristic: `Minimum`, `Maximum`, `Exact`, `Required` or `One of`. Read-only. |
| `required_value` | Typed control fixed by the characteristic. |
| `other_value` | Required bounded text only when the selected characteristic or controlled option explicitly permits `Other`; never a substitute for a listed value. |
| `unit` | Fixed by the characteristic where applicable. Read-only. |
| `mandatory` | Read-only `Yes` in this release. |
| `reason` | Required only for `Other essential characteristic`; 20–300 characters. |
| `row_order` | Generated stable display order. |

The system rejects duplicate characteristic keys for the same target unless the catalogue explicitly permits repetition.

For the code-owned Laptop proposal, technical rows remain proposed input until the grouped package command succeeds. The proposal version, selected rows and visible edited values are validated together; there is no client-side loop that confirms rows one by one.

### 5.8 RelatedService

Rows exist only when `related_services_required = Yes`.

| Field | Control and rule |
|---|---|
| `service_requirement_id` | Generated, read-only. |
| `service_type` | Required Select: `Delivery`, `Installation`, `Configuration`, `Data transfer`, `User orientation`, `Training`, `Testing`, `Other`. |
| `applies_to` | Required Link to one item or `All items`. |
| `required_result` | Required plain text, 10–500 characters. |
| `quantity_or_coverage` | Required single-line text, 1–120 characters. |
| `completion_date` | Required; not later than the package delivery date. |
| `acceptance_evidence` | Required Select: `Delivery note`, `Installation certificate`, `Test result`, `Attendance record`, `Completion certificate`, `Other stated record`. |
| `other_evidence_name` | Required single-line text, 3–120 characters, only when evidence is `Other stated record`. |
| `row_order` | Generated stable display order. |

If services become the main purpose or require substantial development, integration or migration, the Requisition is incompatible with this product.

### 5.9 AcceptanceRequirement

At least one row is required.

| Field | Control and rule |
|---|---|
| `acceptance_requirement_id` | Generated, read-only. |
| `applies_to` | Required Link to one item, one service or `All items`. |
| `row_state` | `Proposed` only for server-generated Draft suggestions; `Confirmed` after grouped application or deliberate manual addition. Proposed rows block routing and never enter a locked Version or handoff. |
| `check_type` | Required Select: `Quantity`, `Physical condition`, `Required specification`, `Functional test`, `Installation complete`, `Documents received`, `Other objective check`. |
| `pass_condition` | Required plain text, 10–500 characters; must state an observable result. |
| `evidence_type` | Required Select: `Inspection record`, `Test result`, `Delivery note`, `Certificate`, `Other stated record`. |
| `other_evidence_name` | Required single-line text, 3–120 characters, only when evidence is `Other stated record`. |
| `row_order` | Generated stable display order. |

"Satisfactory", "acceptable" or similar wording without an observable condition is invalid.

The code-owned Laptop proposal includes the five objective checks in §13.1. They remain editable and individually selectable before grouped confirmation. At least one valid check is still required.

### 5.10 SupportingMaterial

| Field | Control and rule |
|---|---|
| `supporting_material_id` | Generated, read-only. |
| `title` | Required single-line text, 3–160 characters. |
| `document_type` | Required Select: `Drawing`, `Photograph`, `Room layout`, `Network diagram`, `Standards extract`, `Site report`, `Environment information`, `Other supporting material`. |
| `other_document_type` | Required single-line text, 3–80 characters, only when type is `Other supporting material`. |
| `purpose` | Required plain text, 10–300 characters. |
| `file_id` | Required private Frappe File; PDF, PNG, JPG or JPEG; maximum 20 MB. |
| `file_digest` | Generated after malware and readability checks. |
| `treatment` | Required Select: `Informational`, `Forms part of requirement`. |
| `linked_requirement_ids` | Required multi-link when treatment is `Forms part of requirement`; at least one structured technical, service or acceptance row. |
| `document_version` | Required single-line text, maximum 40 characters. |

A supporting file cannot be the only statement of an obligation. Bidder compliance is collected against the linked structured row.

### 5.11 RequisitionTask and RequisitionDecision

`RequisitionTask` records one protected decision queue item for the Head of User Department or Head of Procurement Function. It stores the exact Version, required business role, task OU where applicable, status, due display data and decision token. An open role queue is not bound to a fictional exercised assignment. The successful decision records the actor’s actual live `User Responsibility Assignment` ID and snapshot. It grants no authority by itself. There is no PE/FY scope on this record — only the Organisation Unit scope a departmental task genuinely needs.

`RequisitionDecision` stores the exact task, Version, actor, legal capacity, decision, required return reason where applicable, optional governed affected section, timestamp and resulting state. A return’s affected section uses: `Request details`, `Equipment`, `Technical requirements`, `Warranty and support`, `Services`, `Acceptance`, `Supporting materials` or `Whole requisition`. Decisions are immutable. A copied Draft opens at the affected section; this routing aid does not alter the reviewed Version.

### 5.12 AuthorisedRequisitionHandoff v1.3

One immutable handoff is created atomically with authorisation. It contains:

- Requisition, Version and content digest;
- the site, Financial Year, contributing department(s), Plan, Plan Version and Plan Item;
- the Strategic Objective and its full ancestor path;
- procurement category and fixed Single year horizon; no operative multi-year funding justification;
- every drawdown line, `source_line_id`, `plan_item_line_id` and its own `reservation_id`;
- inherited business need, description and expected operational result;
- planned method, schedule, Budget Line and funding source;
- the exact Budget-owned reservations produced by this handoff’s authorisation transaction, with full drawdown-to-reservation mapping;
- reservation category and lotting indicator;
- requirement title, location and latest delivery date;
- every equipment item and `requisition_item_id`;
- warranty and support values;
- every technical, service and acceptance row with stable IDs;
- supporting-material metadata, links and digests;
- the single certified lead-department Head of User Department decision covering all contributors, and the distinct Head of Procurement Function authorisation;
- `product_pattern = IT Equipment` and first-release suitability facts; and
- handoff version, generated time and handoff digest.

It contains no editable STD binding, supplier field, price, evaluation score or contract result.

### 5.13 Tender consumption and correction projections

`TenderConsumptionProjection` displays exact handoff, Tender/Tender Version, template key/version and consumed time. A delayed projection is **not** the authoritative unconsumed test. `RecordHandoffConsumption` validates and records consumption against REQ’s locked handoff in the same transaction as TPR’s Draft Tender creation; revocation uses the same guard. Until this owner transaction mapping is implemented/tested, do not claim that a local absence of consumption makes revocation safe. This does not record invitation publication or any milestone actual.

`PlanItemCorrectionOutcomeProjection` retains request ID, requesting REQ/exact stopped Version, stable item, original Plan/item Version, outcome, exact owner event/sequence, decision actor/time, reason and replacement eligible lineage where resolved. It is read-only producer evidence, not a Requisition lifecycle decision. Historical outcomes and the stopped content digest remain intact. §9.1B defines the new wire schema and follow-up.

### 5.14 Shared precision, identity and evidence contract

| Type / boundary | Required behavior |
|---|---|
| Money | Plain JSON decimal string in currency units, KES scale 2 from BUD v1.9 CurrencyBasis; e.g. `"20000000.00"`. At least 18 integral digits plus supported fractional digits in storage/calculation. Reject excess precision, JSON floats, exponent/NaN/Infinity, malformed values and overflow without rounding or epsilon. |
| Quantity | Exact decimal string under owner UOM precision. This product additionally requires Each and positive whole numbers for items/drawdown; no fractional equipment. Addition/reconciliation is exact. Zero is allowed only in read-only remaining balances. |
| Other numeric controls | Integer characteristics retain integer/range controls. Decimal characteristics use exact decimal arithmetic and code-owned declared scale/range; catalogue implementation must publish scale metadata and tests. No generic user-configurable schema or inferred precision. |
| Basis snapshot | Submitted Version/handoff retains BUD currency/precision evidence, native UOM basis, exact Plan/item/allocation/source/DPP IDs and eligibility observation time. Current eligibility is rechecked independently; historical numeric values/digests are not rewritten by new configuration. |
| Stable versus exact source | `source_line_id` is the Planning-projected stable Need/direct-source ID paired with source origin. Need Revision and accepted DPP entry/Submission IDs fix exact content separately. `plan_item_line_id` is the exact Planning allocation; REQ `drawdown_line_id` is a different identity. |
| Display references | Legacy fixture labels `PIL-MOH-033-001/002` and `SRC-MOH-033-001/002` may remain human references in the fixture; they do not replace canonical allocation/source IDs in owner commands. §16.2 supplies the explicit mapping. No guessed aliases or text-based identity matching. |
| Dates | Plan/source required-by boundary, estimated completion and REQ operational latest delivery are separate fields. Laptop values are 31 Dec 2027, 24 Sep 2027 and 30 Sep 2027 respectively. None is an invitation actual or delivery result. |
| Handoff and wire change | Preserve the complete v1.3 structured payload, row/file identities and digests. Bind any added metadata/required fields and changed numeric wire types in a coordinated REQ/TPR schema mapping before release. Inspect actual v1.3 serialization; an incompatible wire change requires an explicit agreed version/cutover, never two undocumented shapes under one name. |

Exact values flow through NDS/PLN/REQ/BUD owner boundaries. No REQ Budget table import, `flt()`/epsilon path, minor-unit/shilling relabelling, double reservation, automatic proportional repricing or quantity inflation is allowed. Requested quantity/value are explicit bounded estimates, not bidder prices; no unstated proportionality formula is introduced.

## 5A. Compatibility test

**New.** This document has asserted "product suitability" throughout — in invariant 16, in `REQ_PRODUCT_UNSUPPORTED`, in REQ-AC-013 and REQ-AC-043 — without ever stating, in one place, exactly what that check verifies. That gap has a real cost: without it, a Requisition can be fully authorised, with a genuine Budget reservation committed, against a Plan Item that Tender Preparation will then reject outright — wasting the department's, Procurement's and the Budget Line's time on something that could have stopped before any money moved. This section is that check, run at `PrepareITEquipmentRequisition` and rechecked at `AuthoriseRequisition`.

| Test | Required result |
|---|---|
| `procurement_category` | `Goods`. A Works or Services Plan Item is not eligible for this Requisition pattern at all — this is checked before the Draft is even created, not discovered later. |
| Requirement type | Straightforward off-the-shelf IT equipment, not a services-dominant or specialist-goods classification this package cannot express. |
| Reservation category | `None`, `Youth`, `Women`, `Persons with disabilities` or `Other disadvantaged group` — the categories STD-TPL-001 v0.6 §6.1 supports rendering. Any other value is incompatible in this release, checked against the same list Tender Preparation uses, not a second, independently-maintained one. |
| Lotting indicator | `Single lot`. A `Packaged into lots` Plan Item is incompatible in this release. |
| Currency | KES. |
| Award package | One. |
| Planned method | Open Tender, supported by the installed fixed product and applicable owner-validated method/rule context. REQ cannot substitute another method or infer a threshold waiver. |
| Plan horizon | Single year; completion/funding within the supported FY. Multi-year is explicitly deferred, even if an old payload contains a justification. |

The eight checks are product compatibility, not a fresh legal entitlement determination. Renderable reservation categories do not establish eligible candidate status or override CFG/LAW verification. PLN’s single-year MVP boundary controls this successor; the old permissive Multi-year sentence is withdrawn.

Any No blocks Requisition creation with no free-text bypass, returning `REQ_PRODUCT_UNSUPPORTED` and naming the failing test.

## 6. Fixed IT Equipment Requirement Package

This section defines the complete code-owned product. The catalogue and validations remain structured and enforceable; the ordinary user does not have to navigate the validation model as system mechanics.

### 6.1 Three visible tasks and five retained validation groups

| Visible task | User purpose | Retained validation groups |
|---|---|---|
| **Request details** | Confirm the approved purchase amounts and list the equipment. | Request and drawdown; Equipment items |
| **Requirements** | State minimum technical requirements, warranty/support, related services, acceptance and supporting materials. | Technical and support; Services and acceptance |
| **Review and submit** | Check the complete request and take the action allowed for the current responsibility. | Review and submit |

The progress row shows only these three task labels with **Not started**, **Needs attention** or **Complete**. It is navigation and progress, not a lifecycle. The five validation groups remain separately traceable in validation results, tests and audit; users are not made to complete five separate pages.

### 6.2 Source and editability rules

| Value class | Presentation and rule |
|---|---|
| Planning fact | Read-only value with source label **From approved Procurement Plan**. |
| Departmental fact inherited through Planning | Read-only value with source label **From departmental requirement**. |
| Requisition Draft value | Typed editable control defined in sections 5 and 6. |
| Generated value | Read-only value with source label **Generated by KenTender**. |
| Supporting file | Governed file card; never an unnamed upload field. |

Read-only data is displayed as text, a link or a value card. It is not shown as an enabled or disabled text box. Unknown Select values and user-created options are rejected by the server.

### 6.3 Released characteristic catalogue

The catalogue is code-owned and versioned with this product. It is not edited in Desk. Each category also allows `Other essential characteristic` using a bounded text value and required reason.

| Applies to | Characteristic | Control | Comparison | Unit / options |
|---|---|---|---|---|
| All equipment | Electrical compatibility | Yes/No | Required | `Yes` |
| All equipment | New and unused equipment | Yes/No | Required | `Yes` |
| Laptop, Desktop computer, Tablet | Memory | Integer 1–512 | Minimum | GB |
| Laptop, Desktop computer, Tablet | Storage capacity | Integer 16–8192 | Minimum | GB |
| Laptop, Desktop computer, Tablet | Storage type | Select | One of | `NVMe SSD`, `SSD`, `eMMC` |
| Laptop, Desktop computer, Monitor, Tablet | Display size | Decimal 5–60 | Minimum | inches |
| Laptop, Tablet | Battery runtime | Decimal 1–30 | Minimum | hours |
| Laptop, Desktop computer, Tablet | Processor requirement | Single-line text, 3–200 characters | Minimum | Supplier-neutral capability or benchmark wording |
| Laptop, Desktop computer, Tablet | Operating-system compatibility | Single-line text, 3–160 characters | Required | Approved organisational environment |
| Laptop, Desktop computer, Tablet | Network connectivity | Multi-select | Required | `Ethernet`, `Wi-Fi 5`, `Wi-Fi 6`, `Wi-Fi 6E`, `4G`, `5G`, `Bluetooth 5 or later` |
| Laptop, Desktop computer, Tablet | Required ports | Structured list of port type and positive minimum count | Required | `USB-A`, `USB-C`, `HDMI`, `DisplayPort`, `Ethernet`, `Audio`, `Other stated port` |
| Monitor | Display resolution | Select | Minimum | `Full HD`, `QHD`, `4K UHD` |
| Monitor | Panel size | Decimal 15–60 | Minimum | inches |
| Printer | Print technology | Select | Exact | `Laser`, `Ink tank`, `Thermal` |
| Printer | Colour capability | Select | Exact | `Monochrome`, `Colour` |
| Printer | Print speed | Integer 1–100 | Minimum | pages per minute |
| Printer, Scanner | Automatic duplex | Yes/No | Required | `Yes` / `No` |
| Scanner | Scan resolution | Integer 75–2400 | Minimum | dpi |
| Scanner | Automatic document feeder capacity | Integer 1–500 | Minimum | sheets |
| Network equipment | Equipment function | Select | Exact | `Switch`, `Router`, `Wireless access point`, `Firewall appliance`, `Other stated function` |
| Network equipment | Port count | Integer 1–128 | Minimum | ports |
| Network equipment | Throughput | Decimal 0.1–1000 | Minimum | Gbps |
| Power-protection equipment | Equipment function | Select | Exact | `UPS`, `Surge protector`, `Power distribution unit` |
| Power-protection equipment | Rated capacity | Decimal 0.1–1000 | Minimum | kVA |
| Power-protection equipment | Backup runtime | Integer 1–480 | Minimum | minutes |

Rules:

- Only characteristics applicable to the selected category are offered.
- The same minimum warranty value is maintained once at package level and projected to relevant item rows; it is not entered twice.
- A brand, model, proprietary certification or named technology triggers a Blocking finding unless the text includes an approved `or equivalent` treatment and a recorded functional reason.
- The system does not rewrite a restrictive requirement automatically.
- A new characteristic requires a new code release and document revision; operational users cannot extend the catalogue.

### 6.4 Versioned requirement proposals

After one or more Laptop items are created, the server returns one complete editable proposal using code-owned profile `LAPTOP-REQUIREMENTS-V1`. It contains exactly the eleven technical rows, six warranty/support values and five acceptance checks stated in §13.1. This is a convenience starting point, not a configurable schema, legal rule or supplier response.

Every proposed value is visible before confirmation. Technical and acceptance rows start selected; the user may edit values or clear any suggested technical row that does not apply. Once selected and confirmed, each technical row is mandatory for suppliers. At least one valid acceptance check remains required. **Use selected requirements** submits one payload containing the proposal version, every selected technical row, all visible warranty/support values and every selected acceptance check. The server validates and records all of it or none of it. No unseen value, client-side sequence or row-by-row confirmation is permitted.

**Save draft** persists the remaining visible technical and acceptance suggestions with `row_state = Proposed` plus the visible package-level warranty/support values; it does not mark a row or package Reviewed. Clearing a suggestion removes only that Proposed row. Until **Use selected requirements** succeeds, the package is **Review required** and blocks routing. A copied package or category change generates a fresh Review-required proposal without overwriting confirmed history. **Reset standard values** restores the visible code-owned proposal but does not confirm it. A future profile change requires a reviewed document and code release; operational users receive no configuration surface.

For another supported IT Equipment category, retain the catalogue-driven starting proposal: Electrical compatibility, New and unused equipment, package warranty, and applicable memory, storage, connectivity or functional rows where the code-owned catalogue supplies a starting value. Present the entire available proposal together and use the same `ApplySelectedRequirementPackage` command; do not revert to one confirmation command per row. The complete eleven-technical/five-acceptance preset and its exact values are claimed only for Laptop. Users add or edit any other required structured rows under the same catalogue and validation rules.

### 6.5 Completion and validation

Task completion is derived from the retained validation groups:

| Internal validation group | Visible task | Complete when |
|---|---|---|
| Request and drawdown | Request details | At least one current eligible drawdown line is selected; every requested quantity/value is valid; title, location and date are complete. |
| Equipment items | Request details | At least one item exists; each item is complete; item quantities reconcile to drawdown lines. |
| Technical and support | Requirements | The complete standard proposal has been deliberately reviewed where applicable; warranty/support controls are complete; no duplicate or invalid rows exist. |
| Services and acceptance | Requirements | Conditional service rows are complete; at least one objective acceptance row exists; every operative file is linked to a structured row. |
| Review and submit | Review and submit | All preceding groups are complete; no Blocking finding exists; the complete preview and digest render successfully. |

Blocking findings include:

- Planning eligibility, quantity or value changed;
- a date exceeds an approved Planning boundary;
- item quantities do not reconcile to drawdown lines;
- a required item is missing or a selected structured characteristic is incomplete;
- an unsupported category or control value is posted;
- the standard package remains Review required or contains an invalid selected row;
- a requirement is internally contradictory;
- a service shows complex development, integration or migration;
- an acceptance condition is subjective or empty;
- an operative file has no linked structured obligation;
- a brand or restrictive term lacks permitted equivalent treatment;
- the package is incompatible with the first product; or
- the canonical preview or digest cannot be produced.

Warnings do not block submission. They remain visible to the Head of User Department and Head of Procurement Function. Examples are unusually high minimum values, optional supporting material or a delivery date close to the Plan boundary.

Current numeric precision and fixed horizon follow §5.14/§5A. The characteristic catalogue above remains complete; network connectivity is a Required multi-select (all selected capabilities), not One of. Draft and authorised displays must use that catalogue comparison consistently.

## 7. Lifecycle and governance

### 7.1 State model

| Current state | Action | Actor | Result |
|---|---|---|---|
| No record | Start requisition | Departmental Author or Head of User Department | Draft root, Version 1 and fixed package created from current Planning eligibility |
| Draft | Save Draft | Departmental Author for permitted Draft content, or Head of User Department in scope | Same Draft updated and validation refreshed; a contributing Author cannot route or decide it |
| Draft | Send for department approval | Departmental Author | Version and package locked; state `Awaiting Department Approval`; task created for the lead department's Head of User Department |
| Draft | Submit to Procurement | Head of User Department preparing directly | Version and package locked; state `Submitted to Procurement`; Procurement task created |
| Awaiting Department Approval | Return for correction | Head of User Department | Reviewed Version preserved; copied Draft successor created |
| Awaiting Department Approval | Submit to Procurement | Head of User Department | Same locked Version becomes `Submitted to Procurement`; Procurement task created |
| Submitted to Procurement | Return to department | Head of Procurement Function | Submitted Version preserved; copied Draft successor created |
| Submitted to Procurement | Authorise requisition | Head of Procurement Function | Planning drawdown, **Budget reservation**, decision and immutable handoff committed atomically; state `Authorised` and Tender Preparation may begin |
| Draft, Awaiting Department Approval or Submitted to Procurement | Withdraw | Head of User Department | Locked Version retained; state `Withdrawn`; no drawdown, no reservation |
| Authorised; handoff unconsumed | Revoke authorisation | Head of Procurement Function | Authorised evidence retained; exact drawdown and reservation reversed; state `Revoked` |
| Draft, Awaiting Department Approval or Submitted to Procurement | Request Planning correction | HoD in the lead department or HOPF with permitted record access | Snapshot current content, cancel only this Version’s open tasks and atomically record Planning request/item hold; state Upstream correction required. |
| Submitted to Procurement | Change lead department and return | HOPF | Reasoned return preserves old submitted Version/certifier; copied Draft routes to new lead for fresh certification. |
| Upstream correction required | Receive Planning outcome | Authenticated Planning service | Append neutral outcome; stopped Version remains stopped. |
| Upstream correction required, terminal outcome available | Prepare a new Requisition | Departmental Author or HoD with current owner authority | Explicit fresh root linked to the stopped Version/request/outcome, subject to current eligibility/open-slot and §7.4B. |
| Revoked, exact baseline still eligible | Create corrected Draft | Departmental Author or HoD with current authority | Explicit copied successor with new Version/package; fresh certification/authorisation, no automatic hold or restored decision. |

There is no separate technical review, requirements approval, Finance approval, Accounting Officer approval or committee stage in the Requisition lifecycle.

### 7.2 Submission and authorisation gates

Before departmental routing or submission, the server rechecks:

- the required business role, resolved through the registered permission hooks;
- current Planning eligibility and open balance;
- every field and row control in this document;
- completion of all five internal validation groups through the three visible tasks, and zero Blocking findings;
- supporting-file security and digest;
- product suitability, including reservation category and lotting; and
- canonical content digest.

Before Procurement authorisation, repeat all checks on the immutable submitted Version, including pinned/current eligible Plan/item/source revisions, current funding evidence, item-specific correction hold, original-scope allowance, live authorising responsibility/segregation, all eight compatibility checks and dates. Budget checks the **complete drawdown array** and aggregates requests per Budget Line under §9.1A; do not call independent per-row checks/tokens.

The scope lock is not a blanket prohibition on further Requisitions: an otherwise eligible draw within remaining **original** allowance can proceed. A temporary correction hold blocks **new authorisation**, not historical reads or existing authorised proceedings. Display and investigation remain available; existing valid Draft work may continue under its own permissions. Draft preparation under a hold never guarantees later authorisation. Recheck the hold and allowances at commit under Planning’s stable-item guard, not from an earlier UI eligibility result.

Authorisation decision, Planning drawdown/permanent first-authorisation scope marker, every Budget reservation, immutable handoff and outbox commit together or all roll back. No signed positive decision, partial reservation or handoff survives a failed owner guard.

### 7.3 Maker-checker rules

- A Departmental Author cannot complete the Head of User Department decision on the same Version unless the actor is independently assigned the Head of User Department role and prepared the Requisition directly in that capacity.
- A Head of User Department may prepare and submit a Requisition directly; this removes an unnecessary internal task but not the Procurement authorisation.
- The Head of Procurement Function cannot edit departmental content.
- The actor performing Procurement authorisation cannot also be recorded as the departmental submitting authority for the same Version.
- Where more than one department contributed, the lead department's Head of User Department certifies the whole submission on behalf of every contributing department; this is a single certification, not one per department, and it is a deliberate simplification named here rather than hidden.
- Administrator or System Manager access grants no business decision.

### 7.3A Lead department and immutable certification

Default the lead from the currently drawn departmental totals when preparing the Draft. A tie uses sorted stable OU identity. Refresh the derived default after a Draft drawdown change, unless an explicit HOPF return directive fixes the new lead; display the effective lead before departmental routing.

The lead HoD certifies the entire combined requirement once. A Departmental Author may edit only source/item rows in their own contributing-OU assignment; shared package characteristics require authorized Draft access and are reviewed by that one lead certification. Whole-package context is available to permitted contributors for this existing cross-department product, not to unrelated departments. A parent/other role assignment is not combined with Author rights to invent extra edit scope.

**Change lead department** remains an HOPF action only at Submitted to Procurement, before authorisation. It requires a different contributing OU and20–500 character reason. The command records a return/routing decision, preserves the prior submitted Version/lead/certifying actor and creates a copied Draft with the new routing directive. It closes the Procurement task. The new lead’s HoD must submit the corrected Version before a new Procurement authorisation task can exist. This is the existing return-and-certify chain, not an additional approval tier. HOPF never changes the certified lead in place or attributes an old certification to another department.

### 7.4 Corrections

A return requires one reason of 20–1,000 characters. The reviewed Version stays immutable and a copied Draft successor is created.

After authorisation:

- before handoff consumption, the Head of Procurement Function may revoke, reverse the exact Planning drawdown and Budget reservation, and allow a corrected successor;
- after handoff consumption, Requisitions cannot revoke or edit the authorised package; Tender Preparation uses its own upstream-correction route, per TPR-CHG-001 §10.4; and
- after publication, changes belong to the relevant approved downstream procedure. No APP update or REQ return rewrites an issued Tender; unsupported scope-expansion facilities remain deferred. This amendment does not claim that every downstream module is absent.

### 7.4A Upstream correction to Planning and authorisation hold

For a defect in approved Planning-owned facts, the lead HoD or HOPF selects **Request Planning correction** and supplies 20–1,000 characters identifying the wrong fact. A warranty/technical row is REQ-owned and follows ordinary Draft/Return correction instead; it is not sent to Planning. Need facts begin in NDS, DPP funding/direct facts in a DPP update, and Planning facts in a governed Plan successor. **An Active Plan is never open to direct editing.**

1. Validate exact current pre-authorisation Version, actor/capacity, current stable item/exact approved baseline, reason and idempotency. Preserve the full existing Version/package/rows/files; if it is Draft, freeze its current content as the stopped snapshot. Cancel only its open decision tasks.
2. Through the Planning owner contract, record `PlanItemCorrectionRequest` with request ID, requesting REQ/exact Version, stable item/exact approved Plan/item Version, reason, actor/authority, received instant and idempotency identity. Recording the request and making the item’s hold effective are atomic with stopping the REQ Version. Do not report a recorded request based only on an undelivered outbound event.
3. Planning owns request states **Open**, **In progress**, **Resolved**, **Closed without change** and the Procurement Planner task. REQ exposes their read-only status and owner link, not disposition buttons or a manual clear-hold action.
4. The effective hold exists while **any** relevant request is Open or In progress. Resolve requires an actual Active correction and replacement eligible lineage. Close without change requires a reason. A Draft correction or closure of one of two requests cannot release the other’s hold.
5. Planning disposes of the request under the same stable-item guard used for authorisation, recomputes current eligibility, and emits `PlanItemCorrectionOutcome.v1`. Existing authorised REQs, reservations and published Tenders remain unchanged.
6. REQ records the outcome idempotently and informs the requester on the stopped record. It does not reopen the Version, restore approvals, recreate a handoff or authorise anything. The explicit follow-up is §7.4B.

If owner recording fails, the whole request/stopping operation rolls back; show a retryable typed failure and preserve the current pre-command state. Concurrent request recording and authorisation produce one serialized outcome. If authorisation commits first, this pre-authorisation stop command fails; correction of existing authorised proceedings follows the separate governed route. No background retry may then downgrade the authorised Version to stopped.

### 7.4B Requester follow-up after Planning outcome

| Outcome | What the requester sees | Permitted next work |
|---|---|---|
| Open / In progress | **Awaiting Planning correction**; exact request/reason and item-specific authorisation hold. | Read/investigate via **View Planning request**. No Resume, Resolve or Clear hold. |
| Resolved | **Planning correction is Active**; exact correcting Plan Version, replacement eligible item/allocation lineage and owner decision. | Explicit **Prepare a new Requisition**, rechecking current eligibility and one-open slot. New root links to the stopped root/Version/request/outcome. |
| Closed without change | **Planning request closed without change**; exact reason, deciding Planner and time. **The approved Planning facts have not changed. This stopped Requisition will not restart.** | Requester may leave it stopped, or explicitly **Prepare a new Requisition** against unchanged currently eligible facts and complete normal departmental certification/Procurement authorisation again. The outcome is not permission to edit around the rejected correction. |
| Terminal outcome but another request still open | Show that outcome plus **Authorisation remains on hold** and remaining unresolved count. | Investigation and permitted Draft work remain possible; new authorisation is blocked until all requests reach valid terminal outcomes. |
| Terminal outcome but source/funding/product eligibility now fails | Show exact current blocking reasons. | Do not create a purportedly eligible fresh root. Use the owning correction/recovery route; the old outcome does not override current guards. |
| Another open REQ exists | **This Plan Item already has an open Requisition.** | Open the authorized existing record; create no duplicate or extra edit right. |

A fresh follow-up is an explicit command, never an event-handler side effect. It binds current exact eligible lineage, uses new root/Version/package/row identities and records the old-to-new provenance. Valid REQ-owned content may be offered as a Draft copy for review, but must be remapped to current exact sources; baseline characteristics are Proposed until deliberately confirmed. Do not copy accepted decisions, reservations, digests or invalidated source values into spendable state. If Planning resolved to a different stable item for new scope, use precisely that eligible item; do not attach it to the locked original.

For a revoked unconsumed authorisation, the existing root may instead use explicit **Create corrected Draft** only if its pinned approved baseline remains eligible and no other open REQ occupies the item. A changed Plan baseline uses a fresh root against that baseline. Revocation restores the exact Planning drawdown/funding hold once; it never clears the permanent first-authorisation scope lock.

### 7.5 Core invariants

1. One Requisition uses one Plan Item and either one requesting department, or, only where Planning itself formed the Plan Item as a cross-department combine, exactly the departments Planning's own combine recorded — never a department Planning did not include.
2. Every selected Planning allocation belongs to one of the Requisition's contributing departments.
3. One open Requisition exists per Plan Item.
4. Requested quantity and value never exceed current remaining Planning balances.
5. Every item links to one drawdown line; reconciled quantities are exact.
6. Planning and Strategy facts are read-only. Budget facts remain read-only to REQ; REQ authorisation invokes the Budget owner service for the reservation effect.
7. One fixed IT Equipment Requirement Package exists per Requisition; there is no user-selected schema.
8. Structured rows are authoritative; no file is an obligation by itself.
9. A locked Requisition Version references the matching locked package Version.
10. Drafting, routing and return create no Planning drawdown and no Budget reservation.
11. Authorisation creates the complete drawdown, reservation, decision and handoff, or none of them.
12. Submitted and authorised Versions, rows, files and digests are immutable.
13. Revocation is allowed only before handoff consumption and reverses the drawdown and reservation once, together.
14. Authorisation creates no Tender and binds no STD or Tender template.
15. Unauthorised requests reveal no record, row, file or count existence.
16. Reservation category and lotting indicator are read-only throughout; only `Single lot` and the reservation categories STD-TPL-001 v0.6 §6.1 renders are compatible with this release.

## 8. Roles and permissions

Role-bound `User Responsibility Assignment`, resolved through AUTH-ADR-001 v1.7's registered `permission_query_conditions` and `has_permission` hooks. No Frappe User Permission participates in any authorization decision in this module.

| Business role | Scope type | Exact work |
|---|---|---|
| Departmental Author | Organisation Unit | View eligible Planning allocations for the assigned department; prepare and correct a Draft; send a complete Version to the Head of User Department when acting for the lead Draft. A contributing-department Author may edit only their permitted source/item content, sees the combined context read-only, and cannot route or decide the package. |
| Head of User Department | Organisation Unit | View the complete departmental Requisition; prepare and submit directly, or return/submit an Author's locked Version; withdraw before authorisation; certify on behalf of every contributing department when more than one exists. |
| Head of Procurement Function | Site-wide | View the complete submitted Requisition and fresh Planning and Budget availability; return, authorise or revoke before consumption. May request upstream correction, or change lead via reasoned return for recertification; cannot edit requirements. Same registry entry as DSP-CHG-001 and TPR-CHG-001 use for this office. |
| Procurement Planner | Site-wide | Neutral read of Planning lineage and drawdown projection; receives the `PlanItemCorrectionRequest` task in §7.4A; no Requisition decision. |
| Procurement Officer | Site-wide | No Draft right in Requisitions by virtue of this role; consumes the authorised handoff in Tender Preparation. |
| Auditor | Site-wide or approved OU oversight scope | Neutral read of immutable Versions, decisions, drawdowns, reservations, handoffs and consumption evidence; no business transition. |
| Administrator / System Manager | Technical read-all under AUTH v1.7 §8 | Read Draft/submitted/authorised/stopped content and evidence; no business write or decision without the applicable live responsibility. |

An acting Head of User Department receives a time-bound `User Responsibility Assignment` for the approved period, with an authority reference — not a scoped Frappe User Permission, and not a delegate role.

Every list, count, direct route, file download and command applies the same registered predicate before data is returned — Organisation Unit scope where the role genuinely has one, site-wide otherwise, and no PE or Fiscal Year scope anywhere, because neither is a dimension this module's authorization checks.

## 9. Cross-module contracts

### 9.1 Procurement Planning: exact provider contracts

`GetRequisitionEligiblePlanItem` supplies the exact Active Plan/item/source snapshot and separately current eligibility evidence: stable/exact identities, source origin/stable key/Need revision where applicable, accepted DPP entry/Submission, full original and remaining quantities/values, contributing OUs, Budget Line/funding/currency basis, read-only category/method/Strategy snapshot, fixed Single year horizon, Plan/source completion boundaries, estimated dates and reservation/lotting. It also exposes scope-lock identity, item-specific authorisation hold/unresolved request evidence and exact expected owner revisions. No first/last-row fallback or cached browser context.

`AuthoriseRequisitionDrawdown` is the **one canonical Planning command**; retire `RecordRequisitionDrawdown` rather than keeping an alias. It takes trusted REQ authorisation transaction context, REQ/root/exact Version, exact eligible Plan/item/allocation IDs, positive per-source Quantity/Money, expected revisions and correlation. Planning serializes the stable item, source/allowance revisions, correction hold and successor activation; validates remaining original capacity; and records drawdown/first-authorisation scope protection inside the same owner-coordinated transaction as Budget and REQ. A copied APP item Version creates no new allowance and never resets prior consumption.

`ReverseRequisitionDrawdown` reverses the **exact originating drawdown** once on permitted unconsumed revocation, preserving original Version/source/event lineage; it does not recalculate from current Plan totals, unlock scope or independently release Budget funds.

| Error / condition | REQ treatment |
|---|---|
| `PLN_ITEM_AUTHORISATION_HELD` | **New Requisition authorisations for this item are on hold while correction requests remain unresolved.** Block the positive decision atomically; show authorized request links and retain the submitted package. |
| `PLN_ITEM_SCOPE_LOCKED` | **This Plan Item already has an authorised Requisition. Create a separate Plan Item for the additional requirement.** Preserve owner error/lineage; REQ offers the Planning route, not an edit, reset or new-source bypass. |
| Remaining original allowance still eligible | Permanent lock alone does not reject the next draw. One-open rule and every independent current guard still apply. |
| Stale funding evidence / inactive source / replaced baseline | Fail with typed owner reason and refresh/correction route. No automatic rebinding of the immutable submitted Version. |

Draft creation/save/routing and ordinary Return perform owner reads only. The explicit upstream-correction command is the distinct authorized Planning request/hold write in §7.4A; it is not a financial drawdown.

### 9.1A Budget: complete-array check and reservation

Follow approved BUD v1.9 §§4.5, 5, 8.3–8.4 and 9. REQ supplies its exact Version, proposed authorisation event, exact Plan/item/allocation IDs, each REQ drawdown-line ID, source OU, drawn Quantity/value, funding source/currency/precision, source-set digest and one authorisation correlation/key.

1. Call `check_funding` **once for the complete array**. Budget aggregates by Budget Line and returns per-row/per-line results plus **one** expiring token bound to the full immutable payload, caller/actor and owner revisions. No per-row token array, Finance task or write.
2. In the trusted REQ transaction, call `reserve_funding` with the same complete payload/token and expected revisions. Budget owns root/line locks and rechecks aggregate current availability. Two individually affordable rows do not pass if their combined value exceeds one shared line.
3. Budget creates one reservation per REQ drawdown line, even when rows share a Budget Line. Store the complete returned mapping on those exact rows and in the immutable handoff; never collapse HRMD 20m and DHI 30m into one 50m reservation.
4. REQ authorisation, Planning drawdown/scope guard, all Budget reservations, decision, handoff and outbox commit together or all roll back. Service owners share a proven compatible lock order; no raw cross-module table access, early remote commit or compensating later release presented as atomicity.
5. Same key/same payload returns the original committed mapping and effects, even after a later release; same key/different payload fails. A new key cannot duplicate an already authorised drawdown-line reservation. Token expiry/staleness refreshes without silently reducing/substituting the request.

On revocation, verify authoritative **unconsumed** handoff under §9.2’s transaction guard, reverse the exact Planning drawdown and release every exact Budget reservation in the same transaction. Preserve decision/history and permanent item scope protection. Unavailable owner evidence fails closed; no handoff/projection retry recreates released funds.

Fixture after full authorisation: HWD approved 60m, reserved 50m, committed 0, available 10m; DHI remains 100m available. Before REQ authorisation all Planning actions leave Budget balances unchanged. Planning affordability is within-approved, but this REQ authorisation requires actual availability.

### 9.1B PlanItemCorrectionOutcome.v1

Planning produces the following **new coordinated outcome schema** from its terminal disposition transaction/outbox; REQ consumes it through `RecordPlanItemCorrectionOutcome`.

| Field | Required meaning |
|---|---|
| `event_id`, `schema_version` | Unique payload-bound identity; schema integer 1. Unsupported version or changed duplicate payload fails. |
| `producer_sequence` | Monotonic positive order within the correction-request stream; not a UUID or wall-clock sort. |
| `correction_request_id` | Exact Planning-owned request. |
| `requesting_requisition_id`, `requesting_requisition_version_id` | Exact stopped REQ and immutable Version; validate against retained request lineage. |
| `plan_item_id`, `requested_plan_version_id`, `requested_plan_item_version_id` | Stable affected item and exact approved content originally questioned. |
| `outcome` | `Resolved` or `Closed without change`. Open/In progress come from owner status reads, not invented terminal outcomes. |
| `reason` | Required 20–1,000 character owner decision explanation for Closed without change; for Resolved an owner summary may be null but exact correction evidence is mandatory. No editable REQ response reason. |
| `correcting_plan_version_id`, `replacement_lineage` | Required for Resolved: actual Active correcting Plan plus exact eligible stable item/item Version/allocation IDs and source-replacement mapping. Null for Closed without change. REQ rechecks current eligibility before fresh work. |
| `actor`, `decision_at` | Planning’s terminal decision actor and UTC instant, verifiable against owner authority/evidence; consumer receipt time is stored separately. |
| `item_hold_state`, `unresolved_request_count`, `eligibility_revision` | Owner snapshot of item-wide hold/current revision at disposition time; not permission to ignore later requests. Re-read and validate at any new authorisation. |

Both producers/consumers must adopt this exact schema or an explicitly reviewed equivalent mapping; PLN v1.20 establishes behavior, while this owner amendment supplies its missing response details. New required fields are not silently added to an unrelated existing event.

Authenticate producer, validate request/REQ/Version/item ownership, deduplicate identical events and reject conflicting payload/sequence. Gap/out-of-order delivery triggers owner replay or an authoritative versioned snapshot; preserve last-confirmed status with a pending indication. Never invent replacement IDs, apply one request’s outcome to another, or use a stale zero unresolved count to clear today’s hold. Receipt updates the neutral outcome/history and durable requester notification only; stopped Version/status/digest/decisions remain unchanged. Read/retry cannot create a Draft.

### 9.2 Tender Preparation

Authorisation publishes `ProcurementRequisitionAuthorised.v1.3` through the transactional outbox. Tender Preparation consumes the exact handoff idempotently through REQ’s `RecordHandoffConsumption` owner command within the same transaction as Draft Tender creation. This command serializes against revocation on the handoff identity, rechecks current Authorised/unconsumed state and binds one Tender identity plus exact template/digests. Same consumer/key replays once; a different Tender conflicts. If TPR creation fails, consumption rolls back too. A neutral after-the-fact notification or cached projection is insufficient.

Tender Preparation shall:

- preserve all Requisition and requirement identifiers;
- show inherited requirements read-only;
- generate goods, delivery and price schedules from `RequisitionItem` rows;
- publish technical, service and acceptance rows as controlled Tender requirements;
- render the inherited reservation category, per TPR-CHG-001 §7.7;
- generate one supplier response against every published technical requirement;
- prevent the Procurement Officer from omitting or rewriting an authorised obligation;
- select or confirm the compatible released Tender template downstream; and
- carry awarded values and obligations into contract formation without re-entry.

TPR v0.7 supplies the structured consumer specification and retains two inherited source items even if the issued same-specification schedule groups them. Matching TPR v0.8 must adopt this amendment’s precision, single-year, current compatibility, consumption/revocation and correction boundaries before integration can be declared complete. This review does not certify uninspected implementation.

### 9.3 No STD Configuration contract

Requisitions calls no STD Configuration, manifest, schema or mapping service. It stores no STD package, manifest, compatibility signature or schema digest. Product suitability is a typed rule for the fixed IT Equipment product, not a generic engine.

## 10. Service and command contracts

### 10.1 Reads

| Service | Required result |
|---|---|
| `GetRequisitionWorkspace` | Eligible Plan Items, own Drafts, protected tasks and neutral authorised status, using the registered predicate. |
| `GetEligiblePlanItemDetail` | Complete Planning projection, current remaining balances, reservation category and lotting indicator; no mutation. |
| `GetRequisitionEditor` | One server projection containing Planning context, Draft values, package rows, all five validation-group results, the derived three-task progress and permitted actions. It also returns the exact code-owned Laptop proposal when review is required. |
| `GetDepartmentApprovalTask` | Complete immutable Version and package for the exact Head of User Department task. |
| `GetProcurementAuthorisationTask` | Complete immutable submitted package, current Planning allowance/hold/scope/source basis, whole-array Budget availability and all compatibility checks; display check is not authorisation. |
| `GetStoppedRequisition` | Exact stopped Version/package, original request/reason and each current owner outcome/hold/eligible follow-up action; no resurrection. |
| `GetAuthorisedRequisitionHandoff` | Exact immutable v1.3 handoff for an authorised consumer. |
| `GetRequisitionHistory` | Versions, decisions, drawdown, reservation, reversal, upstream-correction and handoff-consumption evidence; no mutation. |

Reads never create a root, Version, package, row, task, decision, drawdown, reservation or handoff.

### 10.2 Commands

| Command | Core effect |
|---|---|
| `PrepareITEquipmentRequisition` | Serialize current preparation eligibility and the stable-item open slot; create a fresh Draft or return an authorized existing open-record route. Never convert submitted/authorised work back into Draft. |
| `SaveRequisitionSummary` | Save valid drawdown, title, location, date and related-services choice. |
| `AddRequisitionItem` / `UpdateRequisitionItem` / `RemoveRequisitionItem` | Mutate one Draft item and recheck quantity reconciliation. |
| `AddSameSpecificationItems` | Validate one shared equipment definition plus one selected row per approved requirement; atomically create exactly one source-linked item for every selected positive row or none. |
| `UpdateSharedItemDetails` | Atomically update category, name, location and delivery date across an explicitly named same-specification Draft item set; never changes source, quantity or intended use. |
| `AddTechnicalRequirement` / `UpdateTechnicalRequirement` / `RemoveTechnicalRequirement` | Mutate one typed Draft characteristic using the released catalogue. A deliberate manual Add creates a Confirmed Draft row; it does not confirm other Proposed rows. |
| `SaveRequirementProposalDraft` | Persist the complete visible proposal as unconfirmed Draft staging only; retain Review required and create no confirmed requirement or acceptance row. |
| `SaveWarrantyAndSupport` | Save only the controlled package fields. |
| `AddRelatedService` / `UpdateRelatedService` / `RemoveRelatedService` | Mutate one conditional Draft service row. |
| `AddAcceptanceRequirement` / `UpdateAcceptanceRequirement` / `RemoveAcceptanceRequirement` | Mutate one objective Draft acceptance row. A deliberate manual Add creates a Confirmed Draft row; it does not confirm other Proposed rows. |
| `AddSupportingMaterial` / `UpdateSupportingMaterial` / `RemoveSupportingMaterial` | Attach one governed private file and row links after checks. |
| `ApplySelectedRequirementPackage` | Validate the expected code-owned proposal version and atomically record exactly the visible selected technical rows, visible warranty/support values and selected acceptance checks; mark the package Reviewed or change nothing. Laptop uses the complete `LAPTOP-REQUIREMENTS-V1` payload. |
| `ValidateRequisition` | Recompute deterministic findings and preview digest; does not change lifecycle. |
| `SendForDepartmentApproval` | Lock exact content and create one HoD task for the lead department. |
| `ReturnToDepartmentAuthor` | Preserve reviewed Version and create a copied Draft successor with reason and optional governed affected section; open the successor at that section. |
| `SubmitRequisitionToProcurement` | Record departmental submission and create one Procurement task. |
| `ReturnRequisitionToDepartment` | Preserve submitted Version and create a copied Draft successor with reason and optional governed affected section; open the successor at that section. |
| `AuthoriseRequisition` | Atomically recheck, draw down Planning, reserve funding per §9.1A, decide, create handoff and publish outbox event. |
| `WithdrawRequisition` | Close pre-authorisation Version with no drawdown and no reservation. |
| `RevokeUnconsumedAuthorisation` | Reverse exact drawdown and reservation, preserve evidence and publish revocation. |
| `RecordHandoffConsumption` | Owner-authorized TPR command records consumption atomically with Tender creation and serializes against revocation; exposes neutral projection afterward. |
| `RecordPlanItemCorrectionOutcome` | Authenticate, order and project §9.1B’s exact outcome; notify requester without changing stopped Version. |
| `PrepareRequisitionAfterPlanCorrection` | Explicit fresh root/Draft from a terminal outcome and current eligible lineage; bind old request/Version; enforce one-open slot. |
| `CreateRequisitionCorrectionDraft` | Explicit successor of a Revoked root only when its pinned baseline remains eligible and no other open root exists; fresh governance. |
| `ChangeRequisitionLeadDepartment` | At Procurement review, reasoned return/copy for new lead certification; no mutation of old submitted facts. |
| `RequestUpstreamPlanCorrection` | Atomically freeze the current pre-authorisation Version, close its tasks, record Planning request and make the item hold effective under §7.4A. |

Every command accepts an idempotency key and expected record version. The server derives actor, the exercised responsibility assignment, state, totals, digests and permitted actions.

## 11. Error contract

| Code | Meaning and user treatment |
|---|---|
| `REQ_NOT_FOUND` | Record is absent or not visible. Show **Requisition not found**. |
| `REQ_RESPONSIBILITY_REQUIRED` | The actor lacks the required business responsibility. Name it. |
| `REQ_PLAN_INELIGIBLE` | The Plan Item is not currently eligible. Refresh Planning status. |
| `REQ_BALANCE_CHANGED` | Remaining quantity or value changed. Refresh the drawdown step. |
| `REQ_OPEN_EXISTS` | Another open Requisition exists for this Plan Item. Open it. |
| `REQ_CONTROL_INVALID` | A value does not match its released type, range or options. Show the field error. |
| `REQ_QUANTITY_MISMATCH` | Item and drawdown quantities do not reconcile. Show the affected line. |
| `REQ_BATCH_ITEM_INVALID` | One or more selected approved-requirement rows cannot be created or updated as the requested same-specification set. Retain the dialog values, identify each affected row and create/change none. |
| `REQ_STANDARD_PROPOSAL_STALE` | The code-owned proposal or Draft changed after it was shown. Retain permitted input, reload the current visible proposal and require deliberate grouped confirmation again. |
| `REQ_PRODUCT_UNSUPPORTED` | Requirement is outside straightforward IT equipment, or carries an unsupported reservation category or a lotting indicator other than Single lot. Stop; do not offer free-text bypass. |
| `REQ_REQUIREMENT_RESTRICTIVE` | A brand or restrictive term lacks permitted equivalent treatment. Show the row. |
| `REQ_FILE_INVALID` | File type, size, malware, readability, digest or row-link rule failed. |
| `REQ_BLOCKING_FINDINGS` | Submission or authorisation has Blocking findings. Return exact links. |
| `REQ_STALE_VERSION` | Record changed. Reload the same record. |
| `REQ_SOD_BLOCKED` | Actor may not complete the decision on this Version. |
| `REQ_HANDOFF_CONSUMED` | Authorisation cannot be revoked because Tender Preparation consumed it. |
| `REQ_FUNDING_UNAVAILABLE` | **New.** Budget's `check_funding` failed for one or more drawdown lines at authorisation. Name the exact line and shortfall; commit nothing. |
| `REQ_DEPARTMENT_NOT_CONTRIBUTING` | **New.** A drawdown line's Organisation Unit is not among the Plan Item's recorded contributing departments. Reject; this is never a configuration choice. |
| `REQ_IDEMPOTENCY_CONFLICT` | The same key was reused with a different payload. Stop safely. |
| `PLN_ITEM_AUTHORISATION_HELD` | Preserve Planning’s exact §9.1 message; no positive decision or balance effect. |
| `PLN_ITEM_SCOPE_LOCKED` | Preserve Planning’s exact §9.1 message; additional scope follows the separate-item route. |
| `REQ_CORRECTION_OUTCOME_PENDING` | No current terminal outcome can be verified, or event reconciliation is pending; stopped Version stays unchanged. |
| `REQ_CORRECTION_EVENT_INVALID` | Producer/schema/request/Version/payload lineage is invalid; reject/quarantine without lifecycle changes. |
| `REQ_MONEY_PRECISION_INVALID` | Exact amount/currency precision is missing, malformed, over scale/range or unsupported; no rounding. |
| `REQ_QUANTITY_PRECISION_INVALID` | Equipment/drawdown quantity is fractional, malformed or out of supported range; no rounding. |
| `REQ_LEAD_RECERTIFICATION_REQUIRED` | Changed lead requires the returned Draft to be certified and submitted by the new lead before authorisation. |
| `REQ_OWNER_VALIDATION_UNAVAILABLE` | Planning/Budget/TPR owner transaction/evidence cannot be established. Commit no positive decision or revocation. |
| `REQ_HANDOFF_CONFLICT` | The handoff is already consumed by another Tender or has been revoked. No duplicate Tender/consumption. |

`REQ_ROLE_REQUIRED` and `REQ_SCOPE_DENIED` are removed, for the same reason TPR-CHG-001 removed its equivalents: the first named a bare Frappe role rather than a resolved responsibility, and the second named a PE/FY/OU scope that, for PE and FY, no longer exists. A record outside the actor's authorised responsibility returns `REQ_NOT_FOUND`.

## 12. UI architecture and routes

Use Vue 3 single-file components mounted in Frappe Desk. Reuse the existing KenTender shell, header, breadcrumb, tokens, table and dialog components. Do not import design-tool runtime code, recreate the Frappe shell, or add a Procuring Entity selector.

| Surface | Route | Purpose |
|---|---|---|
| Requisitions workspace | `/app/procurement-requisitions` | Eligible Plan Items, own Drafts, tasks and authorised records. |
| Start Requisition | `/app/procurement-requisitions/new/{plan_item_id}` | Confirm the approved purchase in the concise start dialog and create/reuse the Draft. |
| Requisition editor | `/app/procurement-requisitions/{requisition_id}` | Complete the three visible tasks while retaining all five internal validation groups. |
| Department approval | `/app/procurement-requisitions/department-task/{task_id}` | HoD reads the complete locked Version and returns or submits. |
| Procurement authorisation | `/app/procurement-requisitions/procurement-task/{task_id}` | Head of Procurement Function reads the complete submission and returns or authorises. |
| Authorised Requisition | `/app/procurement-requisitions/{requisition_id}/authorised` | Read immutable handoff, drawdown, reservation and Tender-consumption status; authorized revocation/corrected-Draft actions come from server state. |

The existing record route also renders the immutable stopped/returned/revoked detail and correction follow-up; no new top-level menu or correction queue is introduced. Technical readers may discover/read Draft, submitted, authorised and stopped records through these same surfaces; their available business-action set is empty unless separately assigned the required responsibility. The editor loads one server projection. Opening a route creates nothing; only the explicit **Start requisition** confirmation invokes `PrepareITEquipmentRequisition`. Per KT-STD-001 v1.6 §3A, the authorisation verdict resolves before any content renders, and a page-load denial is an inline Forbidden state, never a modal.

### 12.1 User-facing language

| Internal or earlier term | Ordinary user-facing label | Rule |
|---|---|---|
| Plan Item | Approved purchase | Title first; Plan Item reference is supporting detail. |
| Request and drawdown | Amounts requested from the approved plan | Do not require users to understand “drawdown”. |
| Planning allocation / source line | Approved requirement | Department and requirement lead; exact references remain in Source details. |
| Remaining original allowance | Still available from the approved purchase | Show quantity and value separately. |
| Proposed baseline characteristic | Suggested minimum requirement | Explain that the user must keep, edit or clear each suggestion before grouped confirmation. |
| Generated technical/support/acceptance rows | Standard laptop requirements to review | Never imply confirmation before the grouped action succeeds. |
| Authorise for Tender Preparation | Authorise requisition | Consequence text states that Tender Preparation may then begin. |
| Change lead department | Change submitting department | Explain preserved history and fresh certification. |
| Request upstream correction | Request Planning correction | Use only for a Planning-owned fact; the current requisition stops and does not reopen automatically. |
| Prepare a new Requisition | Start a new requisition / Start new Draft | Earlier decisions and funding are not copied. |
| Handoff consumed | Tender Preparation started | Show the Tender reference when available; technical handoff evidence remains in History. |
| Upstream correction required | Planning correction requested | State that the current requisition is preserved and cannot resume. |
| Scope lock | Existing procurement scope | Explain the actual restriction in ordinary language; the technical term remains supporting evidence. |
| Version | Version | Secondary record evidence, never the main task label. |

Machine enums, command names, identities and stored historical text remain unchanged unless this document explicitly versions their contract.

## 13. Static design contract

Supply **KT-STD-001 v1.6 §2 plus this section only** to the design tool. Fixture metadata remains outside the artboard. The business fixtures are isolated scenario inputs, not production-law verification. Do not add screens, fields, actions, reviewers, cards or dashboard content not defined here.

### 13.1 Shared fixture pack

| Fact | Exact value |
|---|---|
| Financial year | FY 2027/28 |
| Requisition | REQ-MOH-2027-033-001 |
| Planning drawdown display reference | PDR-MOH-2027-033-001 — isolated visual-fixture reference, not a guessed command identity |
| Handoff display reference | REQ-MOH-2027-033-001 — the Requisition reference used for display; internal owner identity remains separate |
| Consumed Tender reference | TND-MOH-2027-033 |
| Approved purchase | Clinical training and deployment laptops for digital health rollout |
| Plan Item reference | PPI-MOH-2027-033 |
| Departments | Human Resources Management and Development; Digital Health |
| Lead department | Digital Health |
| Planned method | Open Tender |
| Requirement product | IT Equipment |
| Procurement category | Goods |
| Reservation category | Youth |
| Lotting | Single lot |
| Currency | KES |
| Award package | One |
| Plan horizon | Single year |
| Planned value | KES 50,000,000.00 |
| Still available | 250 Each; KES 50,000,000.00 |
| Plan completion boundary | 31 Dec 2027 |
| Estimated completion | 24 Sep 2027 |
| Delivery location | Ministry of Health Headquarters, Afya House, Nairobi |
| Latest delivery date | 30 Sep 2027 |
| Business need | Equip clinical training and field deployment staff with a common laptop specification for the national digital health rollout. |
| Expected operational result | Staff can use secure, supported equipment for training and field digital-health work. |
| Strategic objective | Strengthen interoperable national digital health services |
| Strategic objective reference | OBJ-MOH-2023-001 |
| Departmental Author | Grace Wanjiku |
| Isolated contributing Author | Asha Odhiambo; non-production permission fixture; Departmental Author assigned only to Human Resources Management and Development for REQ-DES-03-CONTRIBUTOR; this adds no business role or approval stage |
| Lead Head of User Department | Dr Peter Kimani |
| Head of Procurement Function | Charles Mutiso |
| Departmental certification | I confirm that this requisition states the departments’ operational need and minimum requirements and may be submitted to Procurement. |
| Planning-correction request | UI-CORR-001 |
| Planning-correction requester | Dr Peter Kimani; 10 Mar 2027, 09:00 EAT |
| Incorrect Budget Line in correction reset | MOH-BL-DHI-2027 — Digital Health only; cannot fund the HRMD source row |
| Planning-correction reason | The approved source allocation refers to the wrong Budget Line. Please review the departmental funding specification through the governed Planning correction process. |
| In-progress owner | Mercy Kilonzo; 10 Mar 2027, 11:00 EAT |
| Resolved outcome | PLN-MOH-2027-001, Version 2 is Active; replacement PPI-MOH-2027-033 item Version 2 is eligible for 250 Each and KES 50,000,000.00; Budget Line corrected from MOH-BL-DHI-2027 to entity-wide MOH-BL-HWD-2027; resolved by Mercy Kilonzo on 12 Mar 2027, 10:00 EAT |
| Closed-without-change outcome | The approved source allocation and Budget Line are correct. No Planning change is required. Decided by Mercy Kilonzo on 12 Mar 2027, 10:00 EAT |
| Second unresolved request | UI-CORR-002; Open |
| Department-return comment | Replace the processor wording with a measurable, supplier-neutral minimum. |

Approved-requirement rows:

| Department | Requirement | Reference | Available quantity | Available value |
|---|---|---|---:|---:|
| Human Resources Management and Development | Business laptops | SRC-MOH-033-001 | 100 Each | KES 20,000,000.00 |
| Digital Health | Business laptops | SRC-MOH-033-002 | 150 Each | KES 30,000,000.00 |

Equipment rows:

| Item | Approved requirement | Category | Quantity | Intended use | Delivery |
|---|---|---|---:|---|---|
| Business laptops | HR Management and Development — SRC-MOH-033-001 | Laptop | 100 Each | Clinical training for Human Resources Management and Development staff | Nairobi; 30 Sep 2027 |
| Business laptops | Digital Health — SRC-MOH-033-002 | Laptop | 150 Each | Field digital-health deployment for Digital Health staff | Nairobi; 30 Sep 2027 |

Technical-requirement rows for the complete fixture:

| Requirement | Comparison | Exact value | Unit | Control |
|---|---|---|---|---|
| Electrical compatibility | Required | Yes — suitable for Kenyan mains supply | — | Yes/No |
| New and unused equipment | Required | Yes | — | Yes/No |
| Memory | Minimum | 16 | GB | Integer |
| Storage capacity | Minimum | 512 | GB | Integer |
| Storage type | One of | NVMe SSD | — | Select |
| Display size | Minimum | 14.0 | inches | Decimal |
| Battery runtime | Minimum | 8 | hours | Decimal |
| Processor requirement | Minimum | 64-bit business-class processor, minimum 10 cores or equivalent benchmark | — | Single-line text |
| Operating-system compatibility | Required | Approved organisational Windows environment | — | Single-line text |
| Network connectivity | Required | Wi-Fi 6 and Bluetooth 5 or later | — | Multi-select; every selected capability is required |
| Required ports | Required | USB-C ×2; USB-A ×2; HDMI ×1 | — | Structured port and quantity rows |

Warranty-and-support values for the complete fixture:

| Label | Exact value | Control |
|---|---|---|
| Minimum warranty | 36 months | Integer with months suffix |
| On-site support required | Yes | Yes/No |
| Maximum support response | 8 hours | Integer with hours suffix |
| Manufacturer support required | Yes | Yes/No |
| Service location constraint | Within Kenya | Select |
| Support description | Supplier to provide escalation and warranty-contact details. | Textarea, maximum 500 characters |

Acceptance-check rows for the complete fixture:

| Check | Applies to | Pass condition | Evidence |
|---|---|---|---|
| Quantity | All items | Delivered quantities equal the authorised schedule | Inspection record |
| Physical condition | All items | No visible damage and all listed accessories are present | Inspection record |
| Required specification | All items | Every delivered unit complies with all mandatory technical rows | Inspection record |
| Functional test | All items | Each device powers on and completes the agreed basic functional test | Test result |
| Documents received | All items | Warranty and delivery documents are received and verified | Certificate |

Funding fixture at Procurement authorisation:

| Fact | Exact value |
|---|---|
| Budget Line | MOH-BL-HWD-2027 |
| Approved | KES 60,000,000.00 |
| Available now | KES 60,000,000.00 |
| This requisition | KES 50,000,000.00 |
| Available after authorisation | KES 10,000,000.00 |
| HR Management and Development source request | KES 20,000,000.00 |
| Digital Health source request | KES 30,000,000.00 |

Procurement-compatibility results:

| Check | Exact result |
|---|---|
| Procurement category | Goods |
| Requirement type | Straightforward off-the-shelf IT equipment |
| Reservation category | Youth |
| Lotting indicator | Single lot |
| Currency | KES |
| Award package | One |
| Planned method | Open Tender |
| Plan horizon | Single year |

The complete fixture has no related services and no supporting materials. REQ-DES-05-REVIEW-REQUIRED and REQ-DES-05-COMPLETE contain the same eleven technical rows, six warranty/support values and five acceptance checks; their exact difference is proposal state versus confirmed Draft content and disabled versus enabled continuation.

### 13.2 REQ-DES-01 — Requisitions workspace

**Purpose.** Find the next Requisition task or continue existing work.

**Fixture outside the artboard.** Grace Wanjiku; Departmental Author for both fixture departments; 1 Mar 2027, 09:00 EAT; READY scenario with no existing root.

**Header.** Title **Procurement Requisitions**. Description **Prepare and follow requests for purchases already approved in the annual plan.** No header primary action.

**Composition, top to bottom.**

1. Compact work summary row with **Drafts 0**, **Returned to me 0**, **My approvals 0**. Each is a local filter; omit counts for responsibilities Grace does not hold.
2. Filter row: Search by requisition or purchase; Status **All statuses**; Department **All my departments**; Clear filters.
3. Section **Ready to start**. One row using columns Approved purchase; Departments; Still available; Needed by; Action.
4. Section **My requisitions**. In this base variant show empty text **You have no requisitions yet.**

Ready row values: purchase title with `PPI-MOH-2027-033` beneath it; departments **Digital Health; HR Management and Development**; **250 Each** with **KES 50,000,000.00** beneath it; **31 Dec 2027**; primary row action **Start requisition**.

**Actions.** Start requisition is enabled. Filters are secondary. No generic Create action.

**Variants.**

- **REQ-DES-01-DRAFT:** Ready row is absent. My requisitions contains REQ-MOH-2027-033-001; purchase title; Status **Draft — Request details need attention**; Updated **1 Mar 2027, 09:45 EAT**; action **Continue**.
- **REQ-DES-01-ACTION:** My requisitions contains the exact assigned record; Status **Awaiting your approval**; action **Review**. Do not create a separate Tasks panel.
- **REQ-DES-01-NONE:** Ready to start says **No approved purchases are ready for a requisition.** My requisitions remains available.
- **REQ-DES-01-TECHNICAL:** Administrator/System Manager sees Search, Status, Department and Financial year filters plus all authorised rows site-wide; work-summary counts and all business actions are absent.

**Visual check.** The next legitimate action is visible without a dashboard, duplicate record sections or knowledge of Plan Item states.

### 13.3 REQ-DES-02 — Start requisition dialog

**Purpose.** Confirm the exact approved purchase before creating the Draft.

**Fixture outside the artboard.** Same as REQ-DES-01; no Requisition exists.

**Dialog.** A 520 px dialog over the workspace. Heading **Start this requisition?** Text **A Draft will be created from the approved purchase below.**

Place these labelled rows vertically: Approved purchase; Departments; Still available; Plan completion boundary; Requirement product. Values are the fixture title, both departments, **250 Each and KES 50,000,000.00** as separate adjacent values, **31 Dec 2027**, and **IT Equipment**.

Below, show the visible notice: **This release supports straightforward off-the-shelf IT equipment. It does not support software development, integration or migration.** Then show **Digital Health will submit this combined departmental request.**

Footer left **Cancel**; right primary **Start requisition**. Both enabled. No STD, template, profile or approval selector.

**Unsupported variant.** Isolated reset: Requirement product **Software integration**, while the approved purchase title remains visible. Replace the primary action with disabled **Start requisition** and show **This approved purchase requires software integration, which this release does not support.** Keep Cancel.

**Visual check.** The user can identify the purchase, available amount and product limitation without reading Planning lineage or a separate full page.

### 13.4 REQ-DES-03 — Draft: Request details

**Purpose.** State how much is requested and list the equipment.

**Fixture outside the artboard.** Grace Wanjiku; Draft Version 1; after creation and before adding items.

**Header.** Title **Clinical training and deployment laptops for digital health rollout**. Description **Complete the request using the approved purchase shown below.** Place badge **Draft** beside the title. Place `REQ-MOH-2027-033-001` beneath the title in muted text. No header action.

**Progress row.** Request details **Needs attention**; Requirements **Not started**; Review and submit **Not started**. Request details is selected.

**Composition, top to bottom.**

1. Returned-work panel, absent in the base variant.
2. Section **Approved purchase** with title, Plan Item reference, Method, Plan completion boundary, Estimated completion, Strategic objective and Business need as separately labelled values. Start open and compact; technical lineage disclosure **Source details** starts closed.
3. Section **Request information** with two-column form: Requirement title; Delivery location; Latest delivery date; Related services required. Values use the fixture; Related services **No**.
4. Section **Amounts requested from the approved plan**. Visible explanation **The full available amount is selected. Enter a smaller amount only when this requisition covers part of the approved purchase.**
5. Approved-requirements table with columns Department; Requirement; Available quantity; Requested quantity; Available value; Requested value. Show both fixture rows. Requested values default to the full available values. Each row has secondary **Use full available amount** only after a value has been changed.
6. Section **Equipment**. Empty state **No equipment added. Add the equipment covered by the requested quantities above.** Primary section action **Add laptop request**.

**Footer.** Left **Back to Requisitions**. Right secondary **Save draft** and primary **Continue to requirements**, disabled. Immediately above the disabled action show **Add the laptop request matching the requested quantities.** A Departmental Author has no cancel/withdraw command.

**Complete variant.** Above the table show **One shared laptop specification · 2 approved requirements** and secondary **Edit shared details**. The equipment table uses the two fixture rows with columns Item; Approved requirement; Quantity; Intended use; Delivery; Action. Each row has **Edit quantity and use** and **Remove**. Category, name and delivery are not repeated as separate editable work. Continue to requirements is enabled.

**Returned variant.** At the top show **Correction requested** and **Replace the processor wording with a measurable, supplier-neutral minimum.** Include link **Go to affected section**, targeting Technical requirements. Status badge **Draft correction**. Preserve approved-purchase and earlier-decision evidence under History; do not make the user choose a Version.

**REQ-DES-03-CONTRIBUTOR — isolated contributing-author variant.** Fixture: Asha Odhiambo; Departmental Author assigned only to Human Resources Management and Development; the combined Draft already contains both approved-requirement rows and both equipment rows. Keep the same page and full combined context. The HR Management and Development approved-requirement and equipment rows are editable. The Digital Health rows, Approved purchase section, shared Request information and every shared Requirements value are read-only. The only footer actions are **Back to Requisitions** and **Save my changes**. Do not show Cancel draft, Continue, Send, Submit, Return, Withdraw, Request Planning correction or any decision action. After save, show **Your changes are saved in the combined requisition.**

**Visual check.** The user sees business need, requested amount and equipment in one task. The isolated contributor can change only their own source/item content and can still understand the combined request. “Drawdown”, canonical IDs and routing algorithms do not appear in the ordinary composition.

### 13.5 REQ-DES-04 — Add laptop request

**Purpose.** Capture one shared laptop definition while creating the two required source-linked equipment records.

**Fixture outside the artboard.** Grace; both approved-requirement rows selected; no item saved.

**Dialog.** 640 px, scrollable within the viewport. Heading **Add laptop request**. Text **Enter the shared laptop details once, then confirm the quantity and intended use for each department.**

**Shared details**, in order: Equipment category Select **Laptop**; Item name **Business laptops**; Delivery location **Ministry of Health Headquarters, Afya House, Nairobi**; Latest delivery date **30 Sep 2027**.

Below, section **Department quantities and use** with columns Use; Department and approved requirement; Quantity; Unit; Intended use. Show two checked rows. HR Management and Development has 100 / Each / **Clinical training for Human Resources Management and Development staff**. Digital Health has 150 / Each / **Field digital-health deployment for Digital Health staff**. Quantity and intended use are editable; department, approved requirement and unit are read-only. Requested item quantities must reconcile to the selected approved-requirement quantities.

Below the rows show **The standard laptop requirements will be ready for review in the next task.** Do not show technical or acceptance rows in this dialog.

Footer left **Cancel**; right primary **Add 2 equipment rows**. The action is enabled when shared details and both selected rows are valid. One successful action creates both source-linked item records or none.

**One-source variant.** When only one approved requirement has a positive requested amount, show only that row and label the primary action **Add equipment row**. Do not create a zero-quantity or unrelated item.

**Visual check.** The user enters shared category, name and delivery once. The implementation still retains one item per approved requirement and never merges source identities.

### 13.6 REQ-DES-05 — Draft: Requirements

**Purpose.** Define the minimum supplier-facing requirements and how delivery will be accepted.

**Fixture outside the artboard.** Grace; both fixture items exist; complete standard laptop package generated but not reviewed; Related services No. The base artboard is REQ-DES-05-REVIEW-REQUIRED. REQ-DES-05-COMPLETE is a separate reset variant.

**Header and progress.** Reuse REQ-DES-03 header. Request details **Complete**; Requirements **Needs attention**; Review and submit **Not started**. Requirements selected.

**REQ-DES-05-REVIEW-REQUIRED composition, top to bottom.**

1. Visible issue summary: **Review the standard laptop requirements before continuing.** Link it to the package below.
2. Panel **Standard laptop requirements to review**. Explanation **These suggested requirements are not confirmed until you use the action below. Review every value, change what is necessary and clear any suggestion that does not apply.** Badge **Review required**.
3. Subsection **Technical requirements** with target **All equipment**. Show every §13.1 technical row selected under three headings:
   - **Basic equipment:** Electrical compatibility; New and unused equipment.
   - **Performance and storage:** Memory; Storage capacity; Storage type; Display size; Battery runtime; Processor requirement; Operating-system compatibility.
   - **Connectivity:** Network connectivity; Required ports.
4. Within each group use columns Use; Requirement; Minimum or required value; Unit; Action. Show comparison beneath the name. Actions Edit and Clear. Clearing a row removes it from the selected package but does not bypass any independent submission rule.
5. Subsection **Warranty and support** using all six editable §13.1 values.
6. Subsection **Acceptance checks** showing all five §13.1 rows selected. Columns Use; Check; Applies to; Pass condition; Evidence; Action. Actions Edit and Clear. Clearing all checks is invalid.
7. Panel footer: secondary **Reset standard values** and primary **Use selected requirements**. The primary action is enabled when every selected row and every warranty/support value is valid and at least one acceptance check remains selected.
8. Section **Related services**. Base value **No related services requested.** Secondary **Change answer**. When Yes, show service table and **Add service**.
9. Section **Supporting materials**. Base empty text **No supporting materials added.** Explanation **Files may support a structured requirement but cannot replace it.** Secondary **Add supporting material**.

**Review-required footer.** Left **Back to request details**. Right secondary **Save draft** and disabled primary **Continue to review**. Immediately above it show **Review and use the selected standard requirements.**

**REQ-DES-05-COMPLETE variant.** Use a clean reset after **Use selected requirements** succeeds. Remove the issue summary and Review required badge. Requirements is **Complete**. Show status **Reviewed** with all eleven §13.1 technical rows, all six §13.1 warranty/support values and all five §13.1 acceptance-check rows. Row actions become Edit/Remove. Related services remains No and Supporting materials remains empty. **Continue to review** is enabled. A later edit is deliberate and saved normally; a category change or copied package generates a new Review required proposal without overwriting confirmed history.

**Validation variant.** Keep every valid row and entered value. Place exact issues above the affected section and bind field errors locally. Do not reset the page or show one undifferentiated blocker count.

**Visual check.** The complete routine package is visible before confirmation, but the user does not create sixteen standard rows one at a time. Review required and Reviewed are never shown together. Strong headings and compact tables keep the package readable.

### 13.7 REQ-DES-06 — Draft: Review and submit

**Purpose.** Verify the complete request and send it to the next responsible person.

**Fixture outside the artboard.** Grace; complete Draft Version 1; no blocking issue; one delivery-date warning.

**Header and progress.** Request details Complete; Requirements Complete; Review and submit selected. Badge Draft.

**Top result.** Green result panel **Ready to send for department approval**. Under it show warning **The requested delivery date is 6 days after the plan’s estimated completion date.** Separately label Estimated completion **24 Sep 2027**, Latest delivery date **30 Sep 2027** and Plan completion boundary **31 Dec 2027**.

**Composition, top to bottom.**

1. **Purpose and approved purchase** starts open because it contains the date warning. Its summary is **Clinical training and deployment laptops · Digital Health and HR Management and Development · Open Tender**. Detail contains requirement title, business need, expected result, strategic objective, method and all three dates.
2. **Amounts requested** starts closed with summary **2 departments · 250 Each · KES 50,000,000.00** and **Show details**. Detail contains both source rows and totals.
3. **Equipment** starts closed with summary **2 laptop rows · one shared specification**. Detail contains both fixture item rows.
4. **Requirements and support** starts closed with summary **11 technical requirements · 36-month warranty · support within Kenya**. Detail contains all eleven grouped §13.1 technical rows and all six warranty/support values.
5. **Related services** is a compact read-only row **None requested**; no empty table.
6. **Acceptance** starts closed with summary **5 delivery checks**. Detail contains all five §13.1 acceptance rows.
7. **Supporting materials** is a compact read-only row **None added**.

Each closed section retains its complete content and changes **Show details** to **Hide details** when expanded. Long descriptions wrap in full. History and technical identities remain under closed **Record details**. A section with any blocking issue, warning or requested correction starts open and places the exact issue above its affected content.

**Footer.** Left **Back to requirements**; secondary **Save draft**; right primary **Send for department approval**.

**Direct-HoD variant.** Fixture: Dr Peter Kimani preparing the Draft directly in a current lead-HoD assignment. The result reads **Ready to submit to Procurement** and the primary action is **Submit to Procurement**. Place quiet actions **Request Planning correction** and **Withdraw requisition** in an **Other actions** menu beside the footer; neither is primary. Do not show a self-approval action. Request Planning correction opens the exact dialog in REQ-DES-08. Withdraw opens confirmation **Withdraw this requisition?** with required Reason, 20–1,000 characters, notice **The requisition will close without using approved-plan amounts or reserving funding**, and Cancel / **Withdraw requisition**.

**Visual check.** The result, warning, purchase, departments, quantity, value and next decision fit in the initial reading area. Full requirements remain one expansion away; no count or summary substitutes for them.

### 13.8 REQ-DES-07 — Head of User Department review

**Purpose.** Confirm the complete departmental request or return it with one actionable correction.

**Fixture outside the artboard.** Dr Peter Kimani; lead Head of User Department; immutable Version 1; 8 Mar 2027, 09:00 EAT.

**Header.** Title **Review departmental requisition**. Description **Confirm that the request accurately states the departments’ need and minimum requirements.** Badge **Awaiting your approval**. Requisition reference beneath title. No header action.

**Top result.** **Ready for departmental submission**. Visible context: Prepared by Grace Wanjiku; Contributing departments both listed; Submitting department **Digital Health**.

Use the result-first ordered review and disclosure states from REQ-DES-06. Above the footer show this exact certification statement in a distinct bordered panel: **I confirm that this requisition states the departments’ operational need and minimum requirements and may be submitted to Procurement.**

**Footer.** Far left **Request Planning correction**; secondary **Return for correction**; right primary **Submit to Procurement**. Place quiet **Withdraw requisition** in an **Other actions** menu. No edit action. Request Planning correction and Withdraw use the exact dialogs defined in REQ-DES-08 and the REQ-DES-06 direct-HoD variant respectively.

**Return dialog.** Heading **Return this requisition for correction?** Required **Correction required**, 20–1,000 characters. Helper **State what must change and identify the affected section.** Optional governed affected-section Select: Request details; Equipment; Technical requirements; Warranty and support; Services; Acceptance; Supporting materials; Whole requisition. Footer Cancel / Return for correction.

**Submitted HoD variant.** After submission and before authorisation, Dr Peter Kimani sees the same complete Version read-only with badge **Submitted to Procurement**. No edit, return, submit or Procurement-decision action appears. Quiet actions are **Request Planning correction** and **Withdraw requisition**, using the same dialogs. A successful withdrawal shows terminal status **Withdrawn** and no fresh Draft.

**Visual check.** Peter sees one complete request and one certification decision, not a second preparation workflow or contributor-by-contributor approval chain.

### 13.9 REQ-DES-08 — Procurement authorisation

**Purpose.** Decide whether the complete requisition can proceed to Tender Preparation.

**Fixture outside the artboard.** Charles Mutiso; HOPF; immutable submitted Version 1; 15 Mar 2027, 10:00 EAT; current checks pass.

**Header.** Title **Authorise requisition**. Description **Review the request, current funding and procurement checks before authorising it.** Badge **Submitted to Procurement**.

**Top result.** Green **Ready to authorise**. Directly below show **Authorising will reserve KES 50,000,000.00 and allow Tender Preparation to begin.**

**Composition, top to bottom.**

1. **Current funding** starts open. Render every Funding fixture fact from §13.1 and retain the two separately labelled source rows.
2. **Planning availability** starts open: Status Eligible; Quantity available 250 Each; Value available KES 50,000,000.00; no unresolved correction hold.
3. **Departmental certification** starts open: Submitted by Dr Peter Kimani; Lead department Digital Health; Submitted at 8 Mar 2027, 09:00 EAT.
4. Reuse the complete review summaries and expandable detail from REQ-DES-06. Purpose and approved purchase starts open because the delivery-date warning remains part of the submitted Version. Other non-exception detail starts closed; Current funding remains the first HOPF decision evidence.
5. **Procurement checks** starts closed with summary **8 checks passed** and **Show details**. Detail contains every §13.1 compatibility row in the same order. If any check fails, this section starts open, names the failed check and the result is not Ready to authorise.
6. Decision statement: **I authorise this requisition. The approved-plan amounts will be used, funding will be reserved and Tender Preparation may begin.**

**Footer.** Far left **Request Planning correction**; secondary **Return to department**; right primary **Authorise requisition**. Text action **Change submitting department** appears beside Departmental certification, not in the footer.

**Return-to-department dialog.** Heading **Return this requisition to the department?** Required **Correction required**, 20–1,000 characters. Optional affected-section Select uses the same values as REQ-DES-07. Notice **The submitted Version will remain in history and a copied Draft will open for correction.** Footer Cancel / **Return to department**.

**Change-submitting-department dialog.** Heading **Change submitting department and return?** Select is limited to **Human Resources Management and Development** and **Digital Health**, with Human Resources Management and Development selected in this variant. Required **Reason**, 20–500 characters. Notice **The current submission will remain in history. A copied Draft must be certified by the new submitting department before authorisation.** Footer Cancel / **Confirm change and return**. Success closes the Procurement task and opens its read-only returned result with the new Draft link; it never relabels the current certification.

**REQ-DES-08-CORRECTION reset variant and dialog.** This is isolated from the Ready-to-authorise base fixture. It replaces the displayed Budget Line with **MOH-BL-DHI-2027 — Digital Health only**, visibly conflicts with the HRMD source row, and uses the §13.1 Planning-correction reason. It does not simultaneously claim that current checks pass. The dialog is shared by the permitted lead-HoD and HOPF variants. Heading **Request a Planning correction?** Required textarea **What is wrong in the approved plan?**, 20–1,000 characters, prefilled with the exact reason. Notice **This requisition will be preserved and stopped. It will not reopen automatically after Planning responds.** Footer Cancel / primary **Send correction request**. A successful command creates display request **UI-CORR-001** and opens REQ-DES-11 in its Open state; it does not remain on an authorisable page.

**Blocking-funding variant.** Top result red **Cannot authorise — insufficient funding**. Current funding starts open and shows requested KES 50,000,000.00; available KES 40,000,000.00; shortfall KES 10,000,000.00. Authorise absent. Return and Refresh checks enabled.

**Hold variant.** Top result amber **Authorisation is on hold while Planning reviews a correction request.** Show **UI-CORR-001 · Open**. Authorise absent; View Planning request, Refresh checks and Return remain.

**Technical-reader variant.** Same complete content and result evidence; every business action and decision statement absent.

**Visual check.** Charles sees the result and financial consequence first, the complete request second and technical compatibility evidence last. No decision requires decoding transaction terminology.

### 13.10 REQ-DES-09 — Authorisation confirmation

**Purpose.** Confirm the material effects of authorisation.

**Dialog.** Heading **Authorise this requisition?** Labelled values: Quantity **250 Each**; Requisition value **KES 50,000,000.00**; Budget line **MOH-BL-HWD-2027**; Available after authorisation **KES 10,000,000.00**. Text **The approved-plan amounts will be used, two funding reservations will be created and Tender Preparation may begin.** Footer Cancel / primary **Authorise requisition**.

Do not display command names, transaction boundaries or “handoff” terminology.

### 13.11 REQ-DES-10 — Authorised requisition

**Purpose.** Read the authorised requirements and continue to the next procurement stage.

**Fixture outside the artboard.** Authorised Version 1; actor Procurement Officer in the base variant; handoff not consumed.

**Header.** Title fixture requisition title. Description **This requisition is authorised and ready for Tender Preparation.** Badge **Authorised**. Reference beneath title. Upper-right primary **Continue to Tender Preparation**.

**Top facts.** Authorised by Charles Mutiso; Authorised at 15 Mar 2027, 10:00 EAT; Requisition value KES 50,000,000.00; Tender Preparation **Not started**.

Use the complete review sections from REQ-DES-06. Add section **Funding reservations** after Amounts requested, with two rows: RSV-MOH-2027-033-001 / HRMD / KES 20,000,000.00 and RSV-MOH-2027-033-002 / Digital Health / KES 30,000,000.00. Under closed **Record details**, show Planning drawdown display reference **PDR-MOH-2027-033-001**, both `SRC-MOH-033-00x` source references, both reservation references and handoff display reference **REQ-MOH-2027-033-001**. Label each as supporting evidence; none is an editable command key.

**Actor variants.**

- HOPF before consumption: header has no primary; footer secondary **Revoke authorisation**.
- Procurement Officer: Continue to Tender Preparation enabled; reading the page creates nothing.
- Consumed: replace top status with **Tender Preparation started** and Tender reference **TND-MOH-2027-033**; primary **Open Tender**; revoke absent.
- Revoked: badge **Authorisation revoked**; retain the complete authorised content, reason, Planning reversal and both funding-release references. Show **Start corrected Draft** only to a currently eligible departmental actor when the pinned baseline and one-open guards pass; do not create a Draft automatically.
- Auditor/technical reader: navigation/export controls only; all business actions absent.

**Revocation dialog.** Heading **Revoke this authorisation?** Required Reason, 20–1,000 characters. Text **The approved-plan amounts and both funding reservations will be reversed. The authorised requisition will remain in history.** Footer Cancel / primary **Revoke authorisation**. If Tender Preparation has already consumed the handoff, do not show this dialog; show the Consumed variant instead.

**Visual check.** Authorised content is fully readable and the next valid stage is obvious. Counts never replace the actual requirements.

### 13.12 REQ-DES-11 — Returned and stopped work

**Returned Draft.** Reuse REQ-DES-03 or REQ-DES-05 according to the governed affected section. At the top show **Correction requested**, **Replace the processor wording with a measurable, supplier-neutral minimum**, Returned by **Dr Peter Kimani**, Returned at **8 Mar 2027, 09:10 EAT** and **Go to affected section**, targeting Technical requirements. The copied Draft is already open for correction; no Resume or Version-selection action.

**Returned reviewed Version.** History opens the exact earlier Version as a complete read-only review with badge **Returned**, the decision actor/time, correction reason, affected section and authorised link to the current copied Draft. It has no edit, route or decision action.

**Planning correction requested.** Read-only page. Header description **Planning is reviewing an approved-plan issue. This requisition is preserved and cannot be edited or resumed.** Card **Planning correction request** shows **UI-CORR-001**, the exact §13.1 reason, Dr Peter Kimani, 10 Mar 2027 at 09:00 EAT, `PPI-MOH-2027-033` and the variant’s owner status. Complete request follows in read-only form.

**Procurement Planner variant.** Fixture: Mercy Kilonzo opening the stopped requisition from her Planning correction task. Show the same complete read-only requisition and correction card. The only task action is **Open Planning correction task**, which navigates to Planning; no REQ edit, return, submit, authorise, withdraw, outcome or clear-hold control appears. Planning records and disposes of the correction through its own governed screen.

Variants:

- Open: status **Awaiting Planning correction**; show **UI-CORR-001 · Open**; actions View Planning request / Back to Requisitions.
- In progress: status **Planning correction in progress**; show **Mercy Kilonzo began review on 10 Mar 2027 at 11:00 EAT**; same actions.
- Resolved: status **Planning correction completed**; show the complete §13.1 Resolved outcome; primary **Start a new requisition**, only in the eligible actor fixture.
- Closed without change: status **Planning request closed without change**; show the complete §13.1 Closed-without-change outcome and **The approved Planning facts have not changed. This requisition will not restart.** Primary **Start a new requisition**, only if current eligibility permits.
- Outcome unavailable: show last confirmed **UI-CORR-001 · In progress · Mercy Kilonzo · 10 Mar 2027, 11:00 EAT**, then **Planning response is temporarily unavailable. The stopped requisition has not changed.** Action Try again.
- Another request unresolved: show the Resolved outcome for UI-CORR-001 plus **UI-CORR-002 · Open** and **Authorisation remains on hold: 1 Planning request is still unresolved.** No authorise or clear-hold control.

**Fresh-start confirmation.** For the Resolved variant, heading **Start a new requisition?** and text **Use the Active corrected Planning facts shown. Earlier decisions and funding reservations will not be copied.** For Closed without change, use the same heading and text **Use the unchanged approved Planning facts. Complete departmental submission and Procurement authorisation again.** Both show stopped requisition **REQ-MOH-2027-033-001**, current Plan **PLN-MOH-2027-001**, current Plan Version and current eligibility as separately labelled values. Footer Cancel / primary **Start new Draft**. Use isolated eligible and ineligible resets; the ineligible reset removes the primary action and shows **A new requisition cannot be prepared: current Plan funding confirmation is required.**

**Visual check.** A stopped record never resembles an editable Draft. The page states whether the next work is waiting, investigation or an explicit new requisition.

### 13.13 REQ-DES-12 — Common and access states

| Variant | Visible composition | Actions |
|---|---|---|
| Loading | Skeleton only; no stale header/content | None |
| Workspace forbidden | **You do not have access to Procurement Requisitions. This area needs Departmental Author, Head of User Department, Head of Procurement Function, Procurement Planner, Procurement Officer, Auditor, Administrator or System Manager access. Ask your KenTender administrator to assign the appropriate responsibility in System setup.** | None |
| Record not found / masked | **Requisition not found** | Back to Requisitions |
| Load failure | **Procurement Requisitions could not be loaded.** | Try again |
| Stale Draft | Existing page retained with **This requisition changed after you opened it. Review the latest version before saving.** | Review latest version |
| Unsupported product | Approved purchase fixture title; Requirement product **Software integration**; **This approved purchase requires software integration, which this release does not support.** | Back to Requisitions |
| Existing open requisition | **REQ-MOH-2027-033-001 · Draft · Request details need attention** | Open existing requisition |
| Existing procurement scope | **This approved purchase already has an authorised requisition. Additional requirements must use a separate approved purchase.** Preserve the existing authorised/published proceeding and identify the affected approved requirement only when authorised. | View approved purchase; no local add-source, bypass or unlock |
| Remaining original amount | **This request uses only the remaining amount from the original approved purchase.** Show original, previously used and still-available quantity/value separately; an isolated example is 250 Each / KES 50m original, 100 Each / KES 20m used, 150 Each / KES 30m still available. | Normal Start/Authorise remains available only when every other current guard passes |
| Multi-year unsupported | **This release supports purchases completed within one financial year.** Name Plan horizon as the failed procurement check. | Back to Requisitions or owner correction; no justification bypass |
| New submitting department | **This requisition was returned for certification by the new submitting department.** Show the earlier certified department and new submitting department separately. | Open copied Draft when authorised; the earlier Version cannot be authorised |
| Withdrawn | Badge **Withdrawn**; show the complete preserved Version, withdrawing HoD, time and reason, plus **No approved-plan amount or funding was used.** | Back to Requisitions; no Resume or automatic Draft |
| Revocation/consumption race | **Tender Preparation has already started. This authorisation can no longer be revoked.** Show Tender reference when authorised. | Open Tender; no funding release or retry of revocation |
| Save validation | Retain all still-authorised input; issue **Requested equipment quantity for Digital Health is 140 Each but the approved requirement requests 150 Each** above Equipment and beside the row | Save again after correction |
| Uncertain decision result | Base **Checking whether your action completed…**; committed reset **Requisition submitted to Procurement**; retry-safe reset **The result could not be confirmed. Check the current requisition before trying again.** | No second decision while unresolved |
| Technical read | Complete record in its actual state | Read/navigation/export only |

All narrow artboards preserve table meaning through horizontal scrolling or labelled row cards. They do not drop Department, Requirement, Quantity, Value, Pass condition, Result or Action columns.

## 14. Functional interaction requirements

### 14.1 Complete control map — excluded from design prompts

| Screen / control | Destination or result | Governing effect |
|---|---|---|
| Workspace filters and counts | Refresh the authorised local result set | Read only; no authority or global context change |
| Start requisition | Open REQ-DES-02; confirmation invokes PrepareITEquipmentRequisition | One explicit creation; open-slot and product checks re-run |
| Continue / Review / Open existing requisition | Open exact current root, Version or task | No lifecycle change |
| Open copied Draft | Open the exact current successor Draft after a committed return or lead change | Read/navigation only; the earlier Version remains immutable |
| Progress task labels | Navigate within the same Draft | Save prompt applies; no auto-completion |
| Save draft / Save my changes | Persist only the current actor’s permitted edits | Existing expected-version/idempotency rules; contributor cannot route the package |
| Use full available amount | Restore current displayed source remainder in the Draft | Revalidated at save/submit; never authority evidence |
| Add laptop request | Open REQ-DES-04 with both positive requested approved-requirement rows | Dialog open creates nothing |
| Add 2 equipment rows / Add equipment row | Create exactly one item per selected approved requirement using the visible shared and row-specific payload | Atomic batch-capable Draft command; source identities remain distinct |
| Edit shared details | Update category/name/delivery on the selected same-specification Draft items together | Atomic; source, quantity and intended-use identities remain distinct |
| Edit quantity and use / Remove | Update or remove only the selected source-linked Draft item | Draft-only; quantity/source reconciliation revalidates |
| Use selected requirements | Record exactly the visible selected technical and acceptance rows plus visible warranty/support values | Atomic package command; no unseen confirmation or partial package |
| Reset standard values | Restore the visible code-owned laptop proposal without confirming it | Draft-only; status remains Review required |
| Clear suggested row | Clear only the displayed suggestion from the proposed package | The row is not confirmed; independent submission rules such as at least one acceptance check still apply |
| Add/Edit/Remove requirement, service, acceptance check or supporting material | Open exact governed dialog and mutate one Draft row | Existing catalogue, objective-check, links and file rules |
| Change answer | Change Related services required and reveal or remove the governed service controls | Removing existing service rows requires explicit confirmation |
| Continue to requirements/review | Save affected task and navigate if its mapped validation groups pass | No lifecycle transition |
| Send for department approval | Lock exact content and create lead-HoD task | Existing command |
| Submit to Procurement | Record lead-HoD certification and create HOPF task | Existing command |
| Return for correction / Return to department | Capture one comment and affected section; commit return/copy | Earlier Version remains immutable; copied Draft opens directly |
| Go to affected section | Move focus to the governed section named by the return decision | Read/navigation only |
| Withdraw requisition | Open confirmation then close the pre-authorisation Version | HoD only; no drawdown or reservation; no automatic Draft |
| Change submitting department | Existing reasoned lead-change return/copy | New lead certification required; no in-place relabelling |
| Authorise requisition | Open REQ-DES-09 then invoke AuthoriseRequisition | Existing atomic Planning/Budget/REQ effects |
| Request Planning correction | Record exact owner request and stop current Version | Existing §7.4A contract; no direct Plan edit |
| View Planning request / Open Planning correction task | Navigate to the exact authorised Planning owner record or task | Read/navigation from REQ; disposition remains in Planning |
| View approved purchase | Navigate to the exact authorised Planning item | Read only; cannot expand or unlock an existing authorised procurement scope |
| Start a new requisition after outcome / Start new Draft | Open the fresh-start confirmation then invoke the guarded command | No resurrection or copied decision/funding |
| Start corrected Draft | Invoke CreateRequisitionCorrectionDraft for a Revoked root after current baseline/open-slot guards pass | New Draft governance; no restored approval, reservation or handoff |
| Continue to Tender Preparation | Navigate to TPR with exact authorised handoff | Reading/navigating creates no Tender |
| Open Tender | Navigate to the exact Tender created after handoff consumption | Read/navigation only |
| Revoke authorisation | Confirm reason and invoke guarded revocation | Only authoritative unconsumed handoff; exact reversals |
| Show details / Hide details | Expand or collapse the complete content already authorised for the page | Read only; state and validation do not change |
| Record details / History / Source details | Expand exact stored evidence | Read only; focus returns to trigger |
| Export | Produce the authorised read-only export for the exact displayed Version | No lifecycle change or expanded access |
| Cancel / Back | Return to exact parent without committing pending dialog work | No mutation |
| Try again / Review latest / Refresh checks | Repeat the named read and render current result | No inferred success or repeated decision |

Every new visible control must be added to this map before implementation. Labels do not rename machine commands or event schemas.

Common page behaviour and accessibility follow KT-STD-001 v1.6 §3 and §3A. The exact control map above is authoritative; an artboard may not imply a second destination or effect.

### 14.2 Workspace and preparation

- Workspace reads are side-effect free.
- **Start requisition** rechecks eligibility and creates or routes to the one open Draft only after explicit confirmation.
- Browser Back, refresh and repeated commands do not create duplicates.
- Opening a protected task requires the exact open task and current scope.
- The workspace resolves eligible Plan Items and own Drafts using the registered predicate for the actor's exact Organisation Unit assignment(s).
- Where a Plan Item is a cross-department combine, it appears once for each contributing department's Departmental Author, not duplicated as unrelated rows.

### 14.3 Editor

- Save validates only the current edit plus cross-row invariants affected by it.
- Continue saves the current visible task and moves only when its mapped validation groups have no blocker.
- Row dialogs derive control type, comparison, unit and options from typed server metadata for the code-owned catalogue.
- Changing an equipment category revalidates its characteristics and blocks removal of incompatible rows until the user resolves them.
- Removing an item is blocked while linked technical, service, acceptance or file rows remain.
- Turning related services to No requires explicit confirmation and removes no rows silently.
- Autosave is not required. Explicit Save draft is authoritative.
- Two drawdown rows render distinctly by contributing department; a user without an assignment for one contributing department can view but not edit that row.
- A contributing-department Author sees the whole combined Draft but may save only their permitted source/item rows; no routing or decision action is rendered.
- Item, technical, service and acceptance rows validate against the released catalogue server-side, matching client validation exactly.
- The same-specification Laptop dialog sends one explicit batch payload. The server creates every selected source-linked item or none; it never leaves a partial two-department result.
- Creating the first Laptop item set produces the complete code-owned proposal in **Review required** state. The proposal becomes Reviewed only through `ApplySelectedRequirementPackage`; row-by-row client confirmation is not the routine path.
- A drawdown line's requested quantity and value default to its remaining balance; **Use full available amount** restores a manually edited value to that displayed remainder.

### 14.4 Submission and decisions

- Submission locks the exact Version and package before creating a task.
- Task screens lead with the result and exceptions, but every complete immutable row remains available through in-page disclosure; summary-only approval is prohibited.
- Sections with a blocker, warning or requested correction start open and focus the exact affected content. Complete non-exception sections may start closed with a plain-language summary and **Show details**.
- Disclosure state is presentational only: it never removes content from the record, export, digest, validation or decision payload.
- A return creates a copied Draft successor only after the decision commits and opens it at the governed affected section when one was supplied.
- Authorisation rechecks exact current owner facts, stable-item hold/original allowance and full-array Budget availability in one owner-coordinated transaction. Earlier display checks are observations only.
- Double-clicks and retries return the first successful result.
- Notifications are outbox effects, not part of authority.
- **Change lead department** is HOPF-only at Submitted to Procurement and requires reasoned return/copy for new-lead certification; the old submitted Version cannot remain authorisable after that routing change.
- **Send for department approval** and **Submit to Procurement** are visible only to their exact authorised actor, per §7 and §8.
- Authorisation is a single atomic transaction: Planning drawdown, Budget reservation per line, decision, handoff and outbox event commit together or none commit, and the UI shows one pending state throughout, not a sequence of partial confirmations.
- **Request Planning correction** opens the dialog in §13.9 and, on confirmation, transitions the Version to `Upstream correction required` per §7.4A.

### 14.5 Accessibility and page lifecycle

- Every control has a visible label and error text associated programmatically.
- Keyboard users can complete tables, dialogs and all three visible tasks.
- Focus moves to the first invalid field after validation.
- Status is not conveyed by colour alone.
- Unsaved changes prompt before leaving the editor.
- Pages clean up listeners and abort stale requests on unmount.
- The authorisation verdict for every page resolves before any content renders; a denied actor sees the inline Forbidden state, never a modal.
- Direct routes, lists, files and commands enforce the same registered predicate as the UI.

### 14.6 Correction follow-up, record identity and decision races

The record route chooses editable or immutable rendering from server state, never from an optimistic client toggle. Stopped details show the full preserved package and independent owner request/outcome. Receipt of an event never mounts an editor or creates a new root. Fresh follow-up requires the explicit §13.12 command; identical command retries return the same new root or authorised existing open record.

Outcome/hold reads have separate loading and unavailable indicators. A terminal outcome’s old zero-unresolved snapshot never authorizes a later request; authorisation rechecks the current item-wide hold. Two open requests render two distinct rows. Late or unrelated outcome events cannot alter the wrong stopped Version.

Scope protection is a permanent item fact, authorisation hold is a temporary derived control, and remaining allowance is a per-source quantity/value balance. Present them as separate labelled facts. A valid remaining-allowance draw can proceed; new sources or added scope cannot. The source correction route retains all owner governance and never assumes an approved APP changes a previously issued Tender.

Lead-change Return, revocation, fresh-start and handoff consumption each use one pending UI state and one idempotency key. Recheck live role/task authority and owner guards at commit. A consumed handoff projection lag cannot enable a successful revocation. Focus moves to the failed guard or current result; retry never silently reduces quantities/values or changes exact source IDs.

## 15. Audit and history

Audit shall record:

- explicit Draft creation and every successful write;
- Planning projection identity and evaluation time used;
- old and new values for each Draft change;
- item, requirement, service, acceptance and material row identities;
- each atomic same-specification item set, its shared values and the distinct source-specific rows created or changed;
- the standard-profile key/version, complete visible selected payload and grouped confirmation result;
- file scan, digest and linked-row result;
- each validation snapshot and finding set used for a lifecycle action;
- content and handoff digests;
- submission, return, governed affected section, authorisation, withdrawal and revocation decisions;
- Planning drawdown and reversal references;
- **Budget reservation creation and reversal, per line**;
- upstream-correction request/hold recording and ordered outcomes, including Closed without change and every explicit old-to-new follow-up link;
- certified lead versus new routing directive and fresh certification;
- rejected scope expansion, current hold evidence and same-line aggregate funding failures;
- outbox publication and retry evidence; and
- Tender handoff consumption.

Audit records contain actor, business role, the exercised responsibility assignment ID, server time, request ID and idempotency key. There is no Procuring Entity or Fiscal Year scope on any record, because neither participates in authorization here. Audit payloads do not store authentication secrets or duplicate uploaded file bytes, and do not expose confidential internal values or private file contents to unauthorised users.

Submitted, returned, authorised, withdrawn, revoked, superseded and stopped Version **content** cannot be edited or deleted. Only the defined audited lifecycle transitions alter status; copy creates a new Version/root as specified. A changed wire precision implementation never recalculates historical digests silently.

## 16. Deterministic Ministry of Health seed

Use SEED v1.3’s shared Ministry of Health identities/chronology with approved BUD v1.9 and NDS v1.13 source boundaries. The complete structured package remains below. Positive REQ fixtures are conditional; they never force the default BASE Plan Active.

### 16.1 Prerequisites and actors

| Fixture | Exact value |
|---|---|
| Site / FY | Ministry of Health single-site fixture; native FY 2027-2028. Active refers to the eligible **Plan** only in the conditional positive profile, not to an inferred entity/FY permission. |
| Lead department | `OU-MOH-DHI` — Digital Health |
| Contributing department | `OU-MOH-HRMD` — HR Management and Development |
| Departmental Author | Grace Wanjiku · `grace.wanjiku@moh.example.test` |
| Isolated contributing-department Author | Asha Odhiambo · non-production permission fixture assigned only to `OU-MOH-HRMD` |
| Head of User Department | Dr Peter Kimani · `peter.kimani@moh.example.test` |
| Head of Procurement Function | Charles Mutiso · `charles.mutiso@moh.example.test` |
| Auditor | Naomi Chebet · `naomi.chebet@moh.example.test` |

Each user receives only the role-bound `User Responsibility Assignment`s required by section 8 — no Frappe User Permission, no bespoke capability grant. No new actor beyond KT-STD-001 v1.6 §8.3's existing register is required.

Configuration prerequisites: native FY `2027-2028` (1 Jul 2027–30 Jun 2028), exact HRMD/DHI OUs, native Each selectable/whole-number through CFG’s inspected adapter, KES scale 2 CurrencyBasis, HWD approved 60m and fully available in the pre-REQ fixture. HWD is **Entity-wide** in the fresh BUD v1.9 seed so both source OUs are eligible. No live immutable line-owner patch is authorized by a seed reset.

Grace has separate Author assignments in both OUs. Peter has HRMD authority and DHI authority effective from 1 Dec 2026, so his March certification is valid. Charles is **Charles Mutiso** (`charles.mutiso@moh.example.test`), the shared SEED/PLN/REQ HOPF actor. BUD v1.9’s isolated references to Charles Kariuki are an editorial defect to reconcile, not a new actor or authority; §22.3 records it.

Positive configuration/method/reservation eligibility uses the declared fixture-verified provenance, not production-law Verified. CFG-XD-001’s shared May 2027 versus July-start FY/applicability conflict remains a coordinated prerequisite. Do not shift Tender dates to 2028, change FY metadata or waive date checks to make a positive claim.

### 16.2 Exact Planning projection and fixture mapping

BASE has a blocked Draft Plan with None/None designation and cannot start a REQ. The conditional positive READY scenario uses planned Youth on the 50m laptop item, complete mandatory owner readiness and an actually Active Plan. It does not assert candidate entitlement or current legal verification.

| Fact | Exact positive value |
|---|---|
| Stable Plan Item | PPI-MOH-2027-033 |
| Plan / exact item Version | PLN-MOH-2027-001, Active Version 1 and exact item-version ID returned by Planning |
| Source-derived Plan boundary | 31 Dec 2027 |
| Estimated completion | 24 Sep 2027 |
| REQ operational latest delivery | 30 Sep 2027 |
| Original allowance | 250 Each / KES 50,000,000.00; not a new allowance on APP copy |
| Reservation designation / structure | Youth / Single lot / Single year; Open Tender |

| Human Plan-line reference | Canonical `plan_item_line_id` (allocation) | Human source reference | Canonical `source_line_id` | Exact accepted Need revision | OU | Quantity / value |
|---|---|---|---|---|---|---|
| PIL-MOH-033-001 | PSA-MOH-2027-033-001 | SRC-MOH-033-001 | NDS-MOH-2027-0003 | NDS-MOH-2027-0003-V002 | OU-MOH-HRMD | 100 Each / KES 20m |
| PIL-MOH-033-002 | PSA-MOH-2027-033-002 | SRC-MOH-033-002 | NDS-MOH-2027-0004 | NDS-MOH-2027-0004-V001 | OU-MOH-DHI | 150 Each / KES 30m |

This distinguishes SEED’s legacy displayed row/source references from PLN v1.20’s canonical exact-allocation/stable-source contract. REQ drawdown IDs and item IDs are separately generated/retained; an item links to its REQ drawdown, which links to this exact allocation. Freeze actual accepted DPP entry/Submission IDs and current item-version ID from the owner builder, not from guessed strings. If existing published handoffs use a different wire identity interpretation, preserve their historical data and coordinate a documented REQ/TPR cutover; do not rewrite old IDs in place.

No REQ seed writes Planning/Budget tables directly or sets the Plan Active. Provider-test stubs may supply an isolated eligible response but must be labelled contract fixtures; they are not end-to-end approval evidence.

### 16.3 Complete package

Seed both equipment items, technical rows, warranty/support values and acceptance checks exactly as §13.1. Include separate reset states for the unreviewed code-owned proposal and the atomically Reviewed package; do not combine both states in one fixture.

The complete technical fixture has these 11 confirmed rows:

| ID | Applies to | Characteristic | Required value |
|---|---|---|---|
| `TECH-001` | All items | Electrical compatibility | Yes — suitable for Kenyan mains supply |
| `TECH-002` | All items | New and unused equipment | Yes |
| `TECH-003` | All items | Memory | Minimum 16 GB |
| `TECH-004` | All items | Storage capacity | Minimum 512 GB |
| `TECH-005` | All items | Storage type | NVMe SSD |
| `TECH-006` | All items | Display size | Minimum 14.0 inches |
| `TECH-007` | All items | Battery runtime | Minimum 8 hours |
| `TECH-008` | All items | Processor requirement | 64-bit business-class processor, minimum 10 cores or equivalent benchmark |
| `TECH-009` | All items | Operating-system compatibility | Approved organisational Windows environment |
| `TECH-010` | All items | Network connectivity | Wi-Fi 6 and Bluetooth 5 or later |
| `TECH-011` | All items | Required ports | USB-C ×2, USB-A ×2, HDMI ×1 |

Package-level warranty remains 36 months and is carried once into the handoff and Tender. It is not duplicated as an editable technical row.

Fewer rows than the retired Kenya Bureau of Standards fixture's 19, because that fixture spanned three item types (laptops, desktops, tablets) and this one spans one, per SEED-001's harmonization. The full 25-row catalogue in §6.3 is unchanged and available to any future fixture that needs desktop or tablet rows.

### 16.4 Lifecycle fixtures

Seed separately and idempotently, matching the original's six distinct lifecycle states rather than one linear narrative — each is its own fixture a test can load independently:

1. one complete Draft owned by Grace Wanjiku;
2. one Version awaiting Dr Peter Kimani's department decision;
3. one Version submitted to Charles Mutiso for Procurement authorisation;
4. one authorised Version with drawdown, both Budget reservations, and unconsumed handoff;
5. one returned Version with copied Draft successor; and
6. one authorised handoff consumed by `TND-MOH-2027-033`.

Exact timeline for fixture 4, the authorised case:

| Event | Actor | Exact time and result |
|---|---|---|
| Draft opened | Grace Wanjiku | 1 Mar 2027, 09:00 EAT |
| Three visible tasks completed; all five validation groups pass | Grace Wanjiku | 1 Mar 2027, 11:00 EAT |
| Sent for department approval | Grace Wanjiku | 1 Mar 2027, 11:05 EAT |
| Submitted to Procurement | Dr Peter Kimani | 8 Mar 2027, 09:00 EAT |
| Authorised | Charles Mutiso | 15 Mar 2027, 10:00 EAT — creates `RSV-MOH-2027-033-001` (KES 20,000,000, HRMD line) and `RSV-MOH-2027-033-002` (KES 30,000,000, DHI line) against `MOH-BL-HWD-2027`, and the handoff `REQ-MOH-2027-033-001` |
| Handoff consumed (fixture 6 only) | TPR-CHG-001's `PrepareTender` | 20 Mar 2027, 09:00 EAT |

These are **mutually exclusive reset profiles**, not six coexisting open Requisitions against the same stable item. Use an isolated test namespace and restore it after each profile; distinct references alone cannot bypass one-open or consumed-allowance guards. The positive lifecycle uses the shared root reference with a profile-specific reset. Handoff reference may display the REQ reference; its internal handoff ID remains separately returned by the owner command, never inferred from the visible label.

The correction profiles below require actual owner request/hold recording and terminal outcome handling to claim end-to-end success. An isolated mock demonstrates only the REQ provider/consumer contract. PLN v1.20 now specifies the inbound workflow; its code implementation has not been inspected in this review.

### 16.4A Additional isolated profiles

| Profile | Required result |
|---|---|
| REQ-SC-HOLD | Record UI-CORR-001 against the item; new authorisation fails PLN_ITEM_AUTHORISATION_HELD, existing authorised proceedings unchanged, other item unaffected. |
| REQ-SC-MULTIPLE-REQUESTS | Two requests Open/In progress; close one without change and hold remains. Resolve other only against actual Active correction; re-evaluate all eligibility. |
| REQ-SC-CORRECTION-RESOLVED | Stopped Version preserved; owner outcome identifies real Active corrected lineage; explicit fresh-start creates a new linked Draft only after eligibility/open-slot checks. |
| REQ-SC-CLOSED-NO-CHANGE | Exact §13.12 no-change reason/actor/time; stopped Version never restarts. User may leave it stopped or explicitly prepare fresh against unchanged eligible facts with new governance. |
| REQ-SC-OUTCOME-ORDERING | Duplicate same payload no-op; changed-payload duplicate/unknown producer fails; out-of-order/gap/missing owner identity reconciles without changing stopped content. |
| REQ-SC-SHARED-LINE-SHORT | HWD available 40m, source requests 20m+30m; aggregate shortfall 10m, no drawdown/reservation/decision/handoff. |
| REQ-SC-SCOPE-LOCK | An existing authorised/published original proceeding plus later Need cannot enlarge/rebind the locked item. Separate eligible item follows its own normal REQ route. |
| REQ-SC-SEQUENTIAL | Isolated first draw 100 Each/20m, handoff consumed; remaining original 150 Each/30m can support a second eligible REQ. Existing scope lock remains; no extra source or fresh copied allowance. |
| REQ-SC-LEAD-CHANGE | HOPF chooses another contributor at review; reasoned Return retains old certification, new Draft requires new lead’s submission before authorisation. |
| REQ-SC-REVOKE-CONSUME-RACE | TPR creation/consumption and REQ revocation serialize; exactly one succeeds, with no consumed-revoked handoff or released Tender funds. |
| REQ-SC-PRECISION | Exact KES strings and whole-number Each across services/storage; high-precision boundary/overflow/fractional values rejected without epsilon/rounding. |
| REQ-SC-COMPATIBILITY | Each of eight §5A checks fails independently before Draft creation; authorisation rechecks; no Multi-year or non-Open-Tender bypass. |
| REQ-SC-OPEN-SLOT | Two departments concurrently Prepare for one stable item; one root exists. Terminal outcome/fresh-start and revoked-successor attempts compete for same slot. |

A current clock/source/owner fixture is required for every positive result. Shared May invitation/FY applicability conflicts remain governed by SEED/CFG, not re-dated locally. The stopped UI examples use an isolated 10-Mar request and 12-Mar outcome, not extra events added to the full 15-Mar authorisation narrative.

### 16.5 Seed rules

- Upsert by stable IDs; rerun creates no duplicates.
- Validate site, Fiscal Year, Organisation Unit and Planning prerequisites before seeding.
- Never grant Administrator a business decision by implication.
- Never use production emails or attachments.
- Never create an STD manifest, profile or template-selection record.
- Seeds call the same commands as the UI, including the Budget calls in §9.1A, and never write DocTypes directly.
- Print a concise created/reused/failed report.

## 17. Acceptance contract

All 84 v1.8 acceptance results are retained or explicitly reconciled in this single operative set. Criteria 085–118 incorporate the approved usability amendment. These are required results, not claims of tests executed during document review. Historical REQ-AC and REQ-UX-AC identifiers remain traceability only.

| ID | Prior criterion / source | Required result |
|---|---|---|
| REQ19-AC-001 | REQ-AC-001 | Starting from a currently preparation-eligible item serializes one stable-item open slot; create a Draft or return an authorized existing open-record route, never duplicate by department/Plan Version. |
| REQ19-AC-002 | REQ-AC-002 | A page read creates no record or task. |
| REQ19-AC-003 | REQ-AC-003 | Planning and inherited departmental facts are read-only. |
| REQ19-AC-004 | REQ-AC-004 | The Draft contains one fixed IT Equipment package without profile or schema selection. |
| REQ19-AC-005 | REQ-AC-005 | Each drawdown retains canonical exact Planning allocation and tagged stable source plus exact source/DPP/item revisions; each item links explicitly to a distinct REQ drawdown ID. |
| REQ19-AC-006 | REQ-AC-006 | Requested Money/Quantity are exact positive strings within current remaining original Planning allowance; copied APP Versions cannot reset prior consumption. |
| REQ19-AC-007 | REQ-AC-007 | Every item links to one REQ drawdown line, which links to one exact eligible Planning allocation; display PIL/SRC labels are not command identity keys. |
| REQ19-AC-008 | REQ-AC-008 | Item quantities reconcile exactly to requested source quantities. |
| REQ19-AC-009 | REQ-AC-009 | Only category-applicable characteristics and their released controls are accepted. |
| REQ19-AC-010 | REQ-AC-010 | Unknown Select values and free-text substitutes are rejected server-side. |
| REQ19-AC-011 | REQ-AC-011 | Every standard suggestion is visible and editable before one deliberate grouped confirmation; no generated value is silently confirmed. |
| REQ19-AC-012 | REQ-AC-012 | Warranty and conditional support fields enforce their ranges and visibility. |
| REQ19-AC-013 | REQ-AC-013 | Complex software, integration or migration produces a Blocking unsupported-product finding. |
| REQ19-AC-014 | REQ-AC-014 | At least one observable acceptance row is required. |
| REQ19-AC-015 | REQ-AC-015 | "Satisfactory" alone is rejected as a pass condition. |
| REQ19-AC-016 | REQ-AC-016 | A supporting file cannot create an unstructured obligation. |
| REQ19-AC-017 | REQ-AC-017 | An operative file links to at least one structured requirement and retains a digest. |
| REQ19-AC-018 | REQ-AC-018 | Brand/restrictive wording without permitted equivalence treatment blocks submission. |
| REQ19-AC-019 | REQ-AC-019 | A Departmental Author routes one complete locked Version to the HoD. |
| REQ19-AC-020 | REQ-AC-020 | A Head of User Department sees the complete Version and may return or submit it. |
| REQ19-AC-021 | REQ-AC-021 | A HoD preparing directly may submit without an invented departmental-review task. |
| REQ19-AC-022 | REQ-AC-022 | HOPF sees the complete immutable Version, independent current original allowance/scope/hold evidence and full-array Budget availability, all eight compatibility checks and frozen departmental certification. |
| REQ19-AC-023 | REQ-AC-023 | No technical reviewer, Finance approver, Accounting Officer or committee stage exists in the Requisition chain. |
| REQ19-AC-024 | REQ-AC-024 | Procurement return creates a copied Draft successor and preserves the submitted Version. |
| REQ19-AC-025 | REQ-AC-025 | REQ authorisation, Planning drawdown/permanent first-authorisation scope marker, every Budget reservation, decision, handoff and outbox commit together or all roll back. |
| REQ19-AC-026 | REQ-AC-026 | Failed authorisation creates none of those effects. |
| REQ19-AC-027 | REQ-AC-027 | The handoff contains all inherited facts and every structured row with stable IDs. |
| REQ19-AC-028 | REQ-AC-028 | Authorisation creates no Tender and binds no Tender template. |
| REQ19-AC-029 | REQ-AC-029 | TPR consumes exact handoff once through REQ owner validation in the same transaction as Tender creation; retains every source/item/requirement ID and groups display only where its template permits. |
| REQ19-AC-030 | REQ-AC-030 | Unconsumed revocation serializes against consumption, reverses exact drawdown and every Budget reservation once, preserves historical approvals and never clears permanent scope lock. |
| REQ19-AC-031 | REQ-AC-031 | Revocation after consumption is blocked. |
| REQ19-AC-032 | REQ-AC-032 | Role-bound `User Responsibility Assignment`, resolved through the registered permission hooks, protects rows, counts, routes, files and commands consistently — not native Frappe roles or User Permission. |
| REQ19-AC-033 | REQ-AC-033 | An acting HoD uses a time-bound assignment; no delegate role or second permission system exists. |
| REQ19-AC-034 | REQ-AC-034 | The complete Ministry of Health package renders with zero missing values or anonymous requirement text. |
| REQ19-AC-035 | REQ-AC-035 | Repeated seed and command execution remains idempotent. |
| REQ19-AC-036 | REQ-AC-036 | No STD Configuration, manifest, composer profile or generic schema object exists. |
| REQ19-AC-037 | REQ-AC-037 | No attachment-only specification can reach authorisation. |
| REQ19-AC-038 | REQ-AC-038 | TPR receives all structured items, technical/service/acceptance rows; v0.8 matching precision/single-year/consumption contracts require actual integration evidence, not merely a document assertion. |
| REQ19-AC-039 | REQ-AC-039 | A drawdown line's Organisation Unit must be among the Plan Item's contributing departments; any other value is rejected with `REQ_DEPARTMENT_NOT_CONTRIBUTING`. |
| REQ19-AC-040 | REQ-AC-040 | Budget’s complete-array funding check/locked reservation rejects any per-line aggregate shortfall; exact shared-line requirement/availability/shortfall are returned and the full authorisation rolls back. |
| REQ19-AC-041 | REQ-AC-041 | Every authorised Requisition's Budget position change is visible in BUD-CHG-001's own reservation records, matching this module's reservation IDs exactly. |
| REQ19-AC-042 | REQ-AC-042 | No pe_fy_context_id, PE/FY user-permission scope argument or authority bypass exists. Record FY and source OU remain required eligibility facts, not forbidden financial inputs. |
| REQ19-AC-043 | REQ-AC-043 | Reservation category and lotting indicator are read-only throughout, and an unsupported value is rejected at product-suitability check with `REQ_PRODUCT_UNSUPPORTED`. |
| REQ19-AC-044 | REQ-AC-044 | RequestUpstreamPlanCorrection atomically preserves/stops the exact pre-authorisation Version, cancels its tasks, records the owner request and makes item hold effective; owner failure rolls back all. |
| REQ19-AC-045 | REQ-AC-045 | HOPF cannot authorise a Version they submitted departmentally; HOPF alone cannot prepare a departmental Draft. Dual-role actors exercise exact current capacity with no self-authorisation. |
| REQ19-AC-046 | REQ-AC-046 | Every field in this document passes the field-purpose rule in §2.2; no field exists without a stated decision, control and downstream effect. |
| REQ19-AC-047 | REQ-AC-047 | The lead department's Head of User Department certifies on behalf of every contributing department in one submission, never one certification per department. |
| REQ19-AC-048 | REQ-AC-048 | An item links to exactly one drawdown line; a Requisition with two contributing departments and one shared specification produces two item rows, never one row spanning two lines. |
| REQ19-AC-049 | REQ-AC-049 | A standard package renders as **Review required**, distinct from **Reviewed**, and blocks Requirements and Review-and-submit completion until the selected visible payload is applied atomically. |
| REQ19-AC-050 | REQ-AC-050 | HOPF can request lead change only at Submitted to Procurement with reason; command returns/copies for new lead certification, preserves original Version/certifier and prohibits in-place reassignment. |
| REQ19-AC-051 | REQ-AC-051 | Each drawdown line's requested quantity and value default to its full remaining balance; a user may still enter a smaller amount. |
| REQ19-AC-052 | REQ-AC-052 | A Plan Item whose `procurement_category` is not `Goods` is rejected at `PrepareITEquipmentRequisition`, before any Draft is created, with `REQ_PRODUCT_UNSUPPORTED`. |
| REQ19-AC-053 | REQ-AC-053 | Every row in §5A's compatibility test is independently checked and independently named on failure; no test is folded into a single generic suitability flag. |
| REQ19-AC-054 | REQ-AC-054, reconciled by REQ-UX-001 | The Strategic Objective and its full path are visible in Request details, both decision tasks and the authorised handoff, traceable without a second query into Planning. The concise start dialog does not repeat it. |
| REQ19-AC-055 | REQ-AC-055 | Only fixed Single year is operative. Multi-year and non-Open-Tender method fail product compatibility before preparation and again at authorisation; no justification bypass. |
| REQ19-AC-056 | REQ-AC-056 | PLN/REQ provider schemas explicitly map every consumed stable/exact source, financial, date, scope/hold and eligibility fact; actual wire and precision differences require coordinated version/cutover evidence. |
| REQ19-AC-057 | FU-25; naming | AuthoriseRequisitionDrawdown is the sole canonical Planning drawdown command; no RecordRequisitionDrawdown alias remains in active provider/caller code or tests. |
| REQ19-AC-058 | FU-25; hold race | Request recording/hold and new authorisation use the same stable-item guard; both race orderings preserve one valid outcome and no acknowledged hold can be bypassed by stale eligibility. |
| REQ19-AC-059 | FU-25; multiple holds | Hold is derived while any relevant request is Open/In progress; one request’s closure, Draft correction or stale terminal snapshot cannot clear another unresolved request. |
| REQ19-AC-060 | FU-25; prior proceedings | Correction request/hold leaves existing authorised REQs, Budget reservations and published Tenders unchanged; no automatic revoke/release/cancel or APP-wide hold. |
| REQ19-AC-061 | FU-25; scope boundary | First authorised REQ permanently fixes stable-item procurement scope through APP copies, new source revisions, revocation and cancellation; new Needs use a separate eligible item. |
| REQ19-AC-062 | FU-25; remaining allowance | A consumed original proceeding can be followed by a REQ drawing remaining original scope; permanent scope lock alone is not a blanket authorisation rejection and no remaining balance is recreated by a copy. |
| REQ19-AC-063 | FU-25; source ownership | Planning-owned defect uses governed Plan successor; Need/DPP source defects begin with their owners; warranty/technical REQ facts use ordinary REQ correction, not a fictitious Planning warranty field. |
| REQ19-AC-064 | FU-25; response | PlanItemCorrectionOutcome.v1 validates exact request/stopped REQ/item/baseline lineage, terminal outcome, actor/time, required no-change reason and mandatory Active replacement evidence for Resolved. |
| REQ19-AC-065 | FU-25; no-change follow-up | Closed without change displays the reason and unchanged-facts warning; old Version remains stopped. An explicit fresh-start can create a new linked Draft only with current eligible facts and normal new governance. |
| REQ19-AC-066 | FU-25; resolved follow-up | Resolved does not resurrect the stopped Version or carry approvals/funds. Explicit fresh start binds current corrected exact lineage, fresh root/row IDs and explicit predecessor mapping. |
| REQ19-AC-067 | FU-25; outcome idempotency | Same event/payload no-op; conflicting duplicate/schema/producer rejected; gaps/out-of-order/missing identities reconciled with pending state. Event receipt never creates a Draft or authorisation. |
| REQ19-AC-068 | FU-25; fresh-start race | Fresh-start and normal Prepare against one stable item yield one open root across departments; exact retries return the same result, and unauthorized existing records are not disclosed. |
| REQ19-AC-069 | BUD v1.9; one check token | REQ sends one complete array and receives one bound expiring Budget token; independent per-row tokens/subsets, Finance task arguments and changed-payload retries are rejected. |
| REQ19-AC-070 | BUD v1.9; shared line | Two 20m/30m rows against 40m available produce 10m aggregate shortfall and no effects; a successful 50m draw produces two distinct reservations, not a merged one. |
| REQ19-AC-071 | FU-30; exact precision | Money/Quantity round-trip exactly through BUD/PLN/NDS/REQ/TPR contracts and persistence; at least 18 integral digits plus supported decimals; reject floats, excess scale, fractional Each and overflow without rounding/epsilon. |
| REQ19-AC-072 | Wire / identity | PSA allocation IDs, stable Need/direct source IDs, Need -V revision IDs, REQ drawdown/item IDs and human PIL/SRC labels retain distinct meanings. Legacy published handoffs are not silently rekeyed or rehashed. |
| REQ19-AC-073 | Lead governance | HOPF lead change cannot relabel previous certification; copied Draft and new lead submission precede authorisation. Deterministic default/tie and current Draft drawdown changes expose the effective lead. |
| REQ19-AC-074 | Consumption race | RecordHandoffConsumption/TPR creation and REQ revocation share the owner guard; no delayed projection admits revoked consumption or released funds behind a created Tender; failed creation rolls back consumption. |
| REQ19-AC-075 | Revoked recovery | Create corrected Draft is explicit and uses current eligibility/open-slot guard; no event automatically recreates a hold, decision or Draft. Changed approved baseline requires a fresh pinned root. |
| REQ19-AC-076 | UI correction | Stopped detail renders the full structured package, original reason, each outcome, older/new lineage, remaining hold and exact fresh-start actions; no summary-only package or Resume/Clear hold control. |
| REQ19-AC-077 | UI gate separation | Authorisation displays temporary hold, permanent scope lock and per-source remaining allowance separately; held and shared-line-shortfall states block positive decision without hiding the immutable content. |
| REQ19-AC-078 | UI technical access | Administrator/System Manager have full technical read without business decisions; queues/routes/files share AUTH checks and ordinary Forbidden paints no protected content. |
| REQ19-AC-079 | Compatibility / catalogue | All eight product gates are named independently. Network connectivity uses Required multi-select consistently; all 11 fixture technical rows apply to both exact items through All items, not an ambiguous title. |
| REQ19-AC-080 | Dates | Plan/source boundary 31 Dec 2027, estimated completion 24 Sep 2027 and REQ operational date 30 Sep 2027 remain distinct; REQ does not overwrite Plan dates or publish invitation/delivery actuals. |
| REQ19-AC-081 | Fixture integrity | BASE remains blocked Draft; positive REQ uses conditional READY/Youth plus owner prerequisites. Lifecycle fixtures reset separately, not six concurrent roots that evade one-open/allowance rules. |
| REQ19-AC-082 | Actor/ownership consistency | Shared HOPF is Charles Mutiso with exact login; Peter’s March DHI authority is valid from 1 Dec; Budget owns reservations and CFG catalogue; no new Charles Kariuki actor is seeded. |
| REQ19-AC-083 | Release boundaries | Only current owner evidence can close contract/precision/transaction/seed claims; LAW/CFG applicability and unprovided STD/E2E documents remain explicit, with no invented conformance or production verification. |
| REQ19-AC-084 | Full carry-forward | All 84 v1.8 results and the complete 25-row characteristic catalogue are retained or explicitly reconciled; five validation groups map to three visible tasks, the detailed 11-row/five-check package remains available, and the full change table guides reimplementation. |
| REQ19-AC-085 | REQ-UX-AC-01 | The Draft presents exactly three user tasks while retaining and reporting all five internal validation groups. |
| REQ19-AC-086 | REQ-UX-AC-02 | Request details contains approved-plan amounts and equipment without requiring a separate saved page transition between them. |
| REQ19-AC-087 | REQ-UX-AC-03 | Requirements contains all technical, warranty/support, service, acceptance and supporting-material fields with no deleted catalogue option. |
| REQ19-AC-088 | REQ-UX-AC-04 | The start dialog creates nothing until Start requisition succeeds; reload, Cancel and opening the dialog create no root. |
| REQ19-AC-089 | REQ-UX-AC-05 | All eleven suggested technical rows, five suggested acceptance checks and six warranty/support defaults are visible before grouped confirmation; one successful command records exactly the selected package or none. |
| REQ19-AC-090 | REQ-UX-AC-06 | Copied or changed-category packages remain Review required until the user uses Use selected requirements; confirmed history is not overwritten. |
| REQ19-AC-091 | REQ-UX-AC-07 | Ordinary preparation uses the approved business labels; exact identities and machine terminology remain available in supporting evidence and unchanged contracts. |
| REQ19-AC-092 | REQ-UX-AC-08 | Every returned Draft opens the governed affected section with the exact correction comment visible; the reviewed Version remains immutable in History. |
| REQ19-AC-093 | REQ-UX-AC-09 | HoD and HOPF see the complete request in the same stable order, with role-specific result, statement and actions only. |
| REQ19-AC-094 | REQ-UX-AC-10 | HOPF sees current funding, available-after amount, Planning availability and every material blocking exception before Authorise requisition. |
| REQ19-AC-095 | REQ-UX-AC-11 | All eight compatibility checks remain independently visible and enforced; their lower placement does not reduce the gate. |
| REQ19-AC-096 | REQ-UX-AC-12 | Authorisation confirmation states quantity, value, Budget Line, available-after amount and the plain-language consequence. |
| REQ19-AC-097 | REQ-UX-AC-13 | Authorised view contains every item, requirement, support value, acceptance check and reservation; counts never replace content. |
| REQ19-AC-098 | REQ-UX-AC-14 | Continue to Tender Preparation performs navigation only; Tender creation remains an explicit TPR command. |
| REQ19-AC-099 | REQ-UX-AC-15 | Planning-correction pages clearly distinguish waiting, in progress, resolved, closed without change, unavailable and another-request-open states. |
| REQ19-AC-100 | REQ-UX-AC-16 | No stopped Version displays Resume, Clear hold, edit, approve or authorise controls. |
| REQ19-AC-101 | REQ-UX-AC-17 | Author, direct HoD, reviewing HoD, HOPF, Procurement Officer, Planner, Auditor and technical-reader journeys have exact action sets without role switching. |
| REQ19-AC-102 | REQ-UX-AC-18 | Technical readers can open every record state site-wide and see no business command; ordinary masked records remain Requisition not found. |
| REQ19-AC-103 | REQ-UX-AC-19 | Save/validation failure retains still-authorised input and points to the affected section/control; no unsupported autosave is claimed. |
| REQ19-AC-104 | REQ-UX-AC-20 | Uncertain command outcomes resolve the original idempotency identity before another decision is offered. |
| REQ19-AC-105 | REQ-UX-AC-21 | Desktop and narrow layouts retain every decision-critical quantity, value, requirement, result and action. |
| REQ19-AC-106 | REQ-UX-AC-22 | Keyboard, focus, contrast, long-text wrapping and dialog return comply with KT-STD-001 v1.6. |
| REQ19-AC-107 | REQ-UX-AC-23 | Representative Departmental Author, HoD and HOPF users complete ordinary and correction tasks without button coaching and correctly explain scope, certification, funding and authorisation consequences. |
| REQ19-AC-108 | REQ-UX-AC-24 | Misunderstanding that an APP update expands an authorised package, authorisation creates a Tender, or a supporting file replaces structured requirements blocks acceptance and requires revision/retest. |
| REQ19-AC-109 | REQ-UX-AC-25 | KT-STD-001 v1.6 §2 plus §13 alone supplies every exact value, control, actor/state premise and action required to render every artboard; no operative phrase depends on another unavailable section. |
| REQ19-AC-110 | REQ-UX-AC-26 | Every artboard and reset variant represents one internally possible state; incomplete and complete values, progress labels, issue summaries and enabled actions are never combined. |
| REQ19-AC-111 | REQ-UX-AC-27 | Every actor in §8 maps to at least one explicit §13 artboard or named actor variant, including the isolated contributing-department Author. |
| REQ19-AC-112 | REQ-UX-AC-28 | Every §13 business control appears in §14.1, belongs to an actor/state permitted by the lifecycle and has its exact destination or committed result stated. A Departmental Author receives no withdrawal-equivalent control. |
| REQ19-AC-113 | REQ-UX-AC-29 | In the two-department same-specification fixture, the user enters category, item name, delivery location and date once; one atomic command creates exactly two items with distinct source, quantity and intended-use values. |
| REQ19-AC-114 | REQ-UX-AC-30 | Removing or editing one source-linked item never silently changes the other item’s source-specific quantity or intended use; editing shared details names both affected items before commit. |
| REQ19-AC-115 | REQ-UX-AC-31 | The routine Laptop package requires no row-by-row creation of the eleven technical requirements or five acceptance checks. Every selected row remains individually editable before grouped confirmation. |
| REQ19-AC-116 | REQ-UX-AC-32 | Author, HoD, HOPF, Procurement Officer and authorised readers receive the same ordered section summaries and can reveal every exact row without leaving the record. |
| REQ19-AC-117 | REQ-UX-AC-33 | Sections with a blocker, warning or requested correction start open and focus the exact affected content; complete non-exception sections may start closed. |
| REQ19-AC-118 | REQ-UX-AC-34 | A collapsed summary never replaces, truncates or changes the complete record, export, digest, decision payload or accessible detail. |

## 18. Test and smoke contract

The test contract covers the complete domain, cross-module and usability result. Passing document checks or design-tool rendering alone is insufficient.

### 18.1 Focused automated layers

1. Pure tests for ranges, options, category applicability, quantity reconciliation, date rules, objective acceptance wording, and reservation/lotting compatibility.
2. Domain tests for Version locking, correction copies, maker-checker, drawdown, cross-department contribution validation, and handoff invariants.
3. Responsibility tests for every role, scope, list, count, direct route and File, tested against Administrator and System Manager explicitly.
4. Database tests for uniqueness, optimistic concurrency, atomic authorisation, reversal and idempotency.
5. Budget-contract tests for `check_funding` success, failure and rollback, and for reservation reversal on revocation.
6. Contract tests against `GetRequisitionEligiblePlanItem` and the current Tender handoff shape TPR-CHG-001 v0.7 consumes.
7. Vue component tests for the three-task progress mapping, control types, conditional fields, read-only presentation, disclosure state, row dependencies and decision dialogs.
8. Command tests for atomic same-specification item creation/shared edits and atomic selected-package application, including partial-failure, stale-proposal and exact-retry cases.
9. Browser smoke using the Ministry of Health fixtures, including representative actor and narrow-layout journeys.

### 18.2 Named smoke journeys

**REQ-SMK-01 — Happy path**

Departmental Author prepares the Ministry of Health Draft across two contributing departments, enters shared Laptop details once, completes the three visible tasks, HoD submits, Head of Procurement Function authorises, Planning drawdown and both Budget reservations are visible, and Tender Preparation reads the handoff.

**REQ-SMK-02 — Direct HoD preparation**

Head of User Department prepares a complete Draft and submits it directly to Procurement without a self-review task.

**REQ-SMK-03 — Controlled return**

Procurement returns one immutable Version; the department corrects the copied Draft; earlier content and reason remain visible.

**REQ-SMK-04 — Planning balance changed**

Planning availability changes after departmental submission; authorisation stops with `REQ_BALANCE_CHANGED` and creates no partial drawdown or reservation.

**REQ-SMK-05 — Attachment misuse**

An operative uploaded document has no structured-row link; submission is blocked even though the file is readable.

**REQ-SMK-06 — Unsupported complexity**

The Author adds custom software development or systems integration as the principal service; the product stops without a free-text bypass.

**REQ-SMK-07 — Responsibility isolation**

Users outside the exact assignment or task scope receive the same not-found treatment for list, detail, file and command access.

**REQ-SMK-08 — Revocation boundary**

Unconsumed authorisation revokes and reverses the drawdown and both reservations once; consumed authorisation cannot revoke.

**REQ-SMK-09 — Budget shortfall**

Authorisation with insufficient Budget headroom on one drawdown line rolls back the entire command and names the exact line and shortfall.

**REQ-SMK-10 — Cross-department rejection**

A drawdown line against an Organisation Unit not among the Plan Item's contributing departments is rejected with `REQ_DEPARTMENT_NOT_CONTRIBUTING`.

**REQ-SMK-11 — Upstream correction**

Requesting upstream correction atomically preserves/stops the Version and records the Planning request/item hold. Exercise Open/In progress, two unresolved requests, Resolved and Closed without change; terminal outcomes never restart the Version. Explicit fresh Draft follow-up rechecks current source/open-slot and requires new governance.

**REQ-SMK-12 — Scope lock and sequential remainder**

First authorisation fixes scope permanently. After consumption a second eligible draw may use only remaining original allowance; a later Need/new source cannot be absorbed into the published original item. Use separate governed new item as the successful additional-requirement path.

**REQ-SMK-13 — Same-line funding and precision**

Two source rows 20m/30m on one line aggregate before reservation; 40m available fails with a 10m shortfall and total rollback. Exact decimal/whole-number boundaries round-trip; invalid precision/fractions fail without mutation.

**REQ-SMK-14 — Lead certification and handoff race**

HOPF lead change returns a copy for new lead certification. Independently race consumption against revocation; one valid result, no Tender tied to a revoked/released handoff. Technical reader sees all content without mutation authority.

### 18.3 Required release evidence

- migration/build output;
- focused unit, domain, responsibility, database, Budget-contract and contract-test results;
- screenshots for REQ-DES-01–12 and every named reset/actor variant at 1440 × 1024 and usable narrow-width layouts;
- scripted Ministry of Health happy-path and return-path walkthroughs;
- exact generated handoff fixture and digest;
- proof of all-or-none Planning drawdown and Budget reservation, together;
- proof of all-or-none two-item creation and grouped standard-package application;
- representative-user evidence under §18.4;
- zero page-specific console errors or failed network requests; and
- search evidence showing no manifest, composer-profile, capability-profile, attachment-primary compatibility path, or Frappe User Permission read.

### 18.4 Representative-user verification

Give tasks without naming controls.

| Participant | Task | Required understanding |
|---|---|---|
| Departmental Author | Prepare the supplied Laptop requisition and send it for approval. | Enters shared equipment once, checks both department rows, reviews one complete standard package and sends the request without creating routine rows individually. |
| Departmental Author — correction | Correct the returned processor requirement. | Opens the affected section directly; earlier reviewed content remains history. |
| Head of User Department | Check whether the request accurately represents both departments and submit it. | Understands one lead certification and both contributor rows. |
| Head of User Department — direct | Prepare and submit the request personally. | Does not look for an invented self-review task. |
| Head of Procurement Function | Decide whether the request may proceed with KES 60m available. | Understands KES 50m reservation, KES 10m remaining and that no Tender exists yet. |
| Head of Procurement Function — shortfall | Decide with only KES 40m available. | Does not attempt partial authorisation; returns or refreshes. |
| Head of Procurement Function — Planning defect | Report the wrong approved Budget Line. | Uses Planning correction, not local edit or the ordinary requirements return route. |
| Procurement Officer | Begin Tender Preparation from an authorised requisition. | Understands navigation versus Tender creation. |
| Auditor | Find the departmental certification, authorisation, source amounts and reservations. | Finds exact historical evidence and does not read current warnings as rewritten history. |

Record completion, wrong turns, assistance, repeated entry, unnecessary expansion, misunderstood consequence and exact participant wording. Any routine need to re-enter shared Laptop details, create standard technical/acceptance rows individually, or open every detail section merely to understand the decision blocks usability acceptance. Misunderstanding of approval, included scope, funding reservation, structured requirements or Tender creation also blocks acceptance. Document approval and a successful prototype walkthrough do not count as participant evidence.

## 19. Implementation constraints

- Implement in `kentender_procurement` with ordinary Frappe records, the registered AUTH-ADR-001 v1.7 permission hooks, private Files, transactions and audit.
- Use AUTH’s registered role/scope definitions: Author/HoD are OU; HOPF/Planner/Procurement Officer are site-wide; Auditor uses the actual approved oversight scope. Never broaden an OU-limited Auditor by this implementation sentence. Technical read grants no business decision.
- Call BUD v1.9’s complete-array check/token/reserve contracts in §§8.3–9.1; owners implement locking. Publish actual shared serialization order and prove authorisation/hold/activation/consumption races; no raw cross-module table locks.
- Keep the reviewed IT Equipment package under version control matching the owning Requisition Version.
- Implement `AddSameSpecificationItems`, `UpdateSharedItemDetails` and `ApplySelectedRequirementPackage` as server-side atomic, idempotent commands; never simulate them with client-side row loops.
- Keep `LAPTOP-REQUIREMENTS-V1` code-owned and release-versioned. Do not create a Desk configuration surface, generic profile DocType or user-selectable schema.
- Treat collapsed/expanded review sections as presentation state only; complete structured content and validation remain server authoritative.
- Do not use parser/OCR, inferred-schema logic, or a compatibility layer for the retired PE/FY scope model.

## 20. Existing data and cutover

- v1.0–v1.2 Drafts and fixtures keyed to Kenya Bureau of Standards or `pe_fy_context_id` are not migrated into this model.
- Existing v1.8 locked/submitted/authorised Versions remain immutable and are rendered through the new result-first disclosure without changing their rows or digests.
- Existing v1.8 Drafts map their five validation results to the three visible tasks. Valid user-entered rows remain user content; no Draft is silently labelled as having reviewed `LAPTOP-REQUIREMENTS-V1`. An incomplete routine Laptop package opens as Review required and requires explicit grouped confirmation.
- Recreate only authorized disposable fixtures against an eligible owner baseline. Inspect existing live records, open roots, source identities, reservation links, hashes and consumption evidence before a controlled migration; do not overwrite approved history or use fixture reset as data repair.
- Before production authorisation, require AUTH registration plus precision, Planning/Budget transaction, hold/scope, handoff-race and applicable CFG/LAW release evidence. Document approval alone closes none of those implementation gates.

## 21. E2E-REQ-001 conformance

v1.2 asserted conformance with **E2E-REQ-001 v0.2 — Approved**, for the structured Departmental Needs → Planning → Requisition → Tender control contract. That document has not been supplied in this review and its current content has not been re-verified against the corrections in this version. This section is carried forward as an open item, not a confirmed conformance claim: before this document is treated as fully aligned, E2E-REQ-001 should be obtained and checked against the cross-department relaxation in §2.1 and the Budget reservation addition in §9.1A, either of which it may also govern.

## 22. Traceability, full changes and remaining dependencies

### 22.1 Governing inputs

| Input | Use / limitation |
|---|---|
| REQ-CHG-001 v1.8 | Complete predecessor domain model, lifecycle, owner transactions, catalogue, seed, 84 acceptance results and 32-row re-implementation register retained or explicitly reconciled here. |
| REQ-UX-001 v0.3 — Approved | Governs the three-task workflow, business language, complete self-contained design contract, atomic shared-item/standard-package path, disclosure rules, actor coverage and representative-user acceptance. Incorporated into the body; not a parallel specification. |
| PLN-CHG-001 v1.20 | Stable/exact source identity, canonical drawdown command, one-open stable item, permanent scope versus temporary correction hold, current financial basis, fixed Single year and separate date boundaries. |
| Approved BUD v1.9 | Complete-array check/token/reserve and aggregate line availability, per-drawdown reservation identity, exact Money/currency contract, no Planning reservation. |
| Approved NDS v1.13 / CFG v0.11 | Immutable source revisions, exact Quantity/native UOM adapter, source ownership and effective configuration. Initial Needs/DPP intake flags do not independently gate an otherwise eligible Active-plan REQ. |
| Approved SEED v1.3 | Two sources/items, 100/150 quantities, 20m/30m reservations, BASE versus conditional READY, authoritative Charles Mutiso and March lifecycle, distinct Plan/REQ/estimated dates. |
| Approved LAW v1.1 | Current legal-verification prerequisites and boundary of design versus statutory interpretation. This review establishes no new legal entitlement or verified production rule. |
| Approved STR v1.8 / AUTH v1.7 / KT-STD-001 v1.6 | Strategy snapshot, registered live responsibility hooks, immutable authority evidence, technical read, common shell and verification requirements. |
| Supplied TPR v0.7 | Structured v1.3 handoff consumer baseline, fixed downstream template and full inherited-row ownership. Matching v0.8 is next; current code/schema not verified here. |
| Referenced STD-STD-001 / STD-TPL-001 / E2E-REQ-001 | Source REQ references are retained, but these full documents were not supplied in the inspected set. Obtain applicable versions and verify current compatibility/rendering/conformance before release; no assertion of reviewed content. |
| PLN-CHG-001_FOLLOW_UPS.md FU-25/FU-30 | Required REQ/TPR sibling contracts, correction follow-up and cross-module exact precision. |

Body rules are the sole proposed REQ implementation contract. Owner APIs govern each external decision/value; no cross-module direct table access, editable source facts or documentation-only “implemented” claim. Exact historical wire identities/digests stay preserved through a coordinated adoption.

### 22.2 Full change register for re-implementation

| ID | Prior issue / gap | Complete required change | Locations | Verification |
|---|---|---|---|---|
| REQ19-CHG-001 | Drawdown naming differs across owner documents | Use AuthoriseRequisitionDrawdown only, exact owner signatures and trusted transaction; no RecordRequisitionDrawdown alias. | §§9.1, 10 | REQ19-AC-005–006, 025, 057 |
| REQ19-CHG-002 | One-open rule lacks stable key/state definition | One open root per stable item across all departments/Plan Versions; explicit occupancy states, consumed-slot release without allowance reset, fresh-start race guard. | §§5.1, 7.4B, 10, 14.1 | REQ19-AC-001, 062, 068 |
| REQ19-CHG-003 | Local remaining balance could reset on APP copy | Pin stable/exact original allowance/source lineage and retain cumulative draws/reversals across successors; sequential draws use only remaining original scope. | §§5.1, 9.1, 13.15, 16.4A | REQ19-AC-006, 061–062 |
| REQ19-CHG-004 | New Need could appear covered by an old proceeding | Preserve permanent first-authorisation item scope; reject extra sources/quantity/value scope on locked item; use separately governed eligible item for new requirement. | §§7.2, 9.1, 13.15 | REQ19-AC-061–062 |
| REQ19-CHG-005 | Temporary hold unspecified on REQ side | Check item-specific unresolved correction hold inside authorisation; preserve exact PLN_ITEM_AUTHORISATION_HELD error and owner links. | §§7.2, 7.4A, 9.1, 11 | REQ19-AC-058–060 |
| REQ19-CHG-006 | Correction request/outbox could be acknowledged before hold exists | Stop exact pre-authorisation Version/tasks and record Planning request/hold atomically; failure rolls back, competing authorisation cannot be downgraded later. | §7.4A | REQ19-AC-044, 058 |
| REQ19-CHG-007 | One closed request could clear other unresolved work | Derive hold across all Open/In progress requests, resolve only Active correction or reasoned no-change; recheck all eligibility after release. | §§7.4A–7.4B, 9.1B | REQ19-AC-059–060 |
| REQ19-CHG-008 | Active Plan described as open to correction | Remove direct-edit route; correct source in NDS/DPP or Planning successor according to ownership; old Active content stays immutable. | §7.4A | REQ19-AC-063 |
| REQ19-CHG-009 | Warranty example sent REQ-owned fact upstream | Use wrong approved Budget Line as Planning correction example; warranty/technical defects remain REQ Draft/Return work. | §§7.4A, 13.13–13.14 | REQ19-AC-063 |
| REQ19-CHG-010 | No explicit terminal correction response | Add PlanItemCorrectionOutcome.v1 with exact request/stopped Version/item/baseline, terminal result, actor/time, reason/Active replacement lineage and ordered metadata. | §§5.13, 9.1B, 10 | REQ19-AC-064, 067 |
| REQ19-CHG-011 | Closed without change left requester stranded or silently restarted | Show reason and unchanged facts; retain stopped evidence; allow explicit fresh linked root with current eligibility and entirely new certification/authorisation, or leave stopped. | §§7.4B, 13.14, 14.5 | REQ19-AC-065 |
| REQ19-CHG-012 | Resolved outcome could resurrect old Version/approvals | Explicit fresh root against current corrected exact lineage; fresh IDs and predecessor mapping, Draft-only content carry, no copied approval/reservation/handoff. | §§7.4B, 9.1B, 10 | REQ19-AC-066, 068 |
| REQ19-CHG-013 | Outcome order/idempotency and stale hold snapshot unspecified | Authenticate/deduplicate by exact payload, reconcile gaps and unknown identities, retain last-confirmed information; event receipt never creates Draft or clears current hold. | §§9.1B, 13.14, 14.5 | REQ19-AC-067 |
| REQ19-CHG-014 | Per-row Budget checks/tokens conflict with BUD v1.9 | Send one complete drawdown array; receive one bound token; Budget aggregates shared-line demand, owns locks and emits one reservation per drawdown. | §9.1A | REQ19-AC-040, 069–070 |
| REQ19-CHG-015 | Partial orchestration could survive failed authorisation | Commit REQ decision, Planning drawdown/scope marker, complete reservation mapping, handoff and outbox together; no early remote commit disguised by compensation. | §§7.2, 9.1–9.1A | REQ19-AC-025–026, 058, 070 |
| REQ19-CHG-016 | REQ called itself reservation owner | Budget owns records/balances/locking; REQ owns authorisation and invocation. Funding catalogue remains CFG-owned and source selection PLN-owned. | §§3–4, 7.5, 9.1A | REQ19-AC-041, 082 |
| REQ19-CHG-017 | Money/Quantity floats or ambiguous units | Exact currency-unit decimal strings and governed precision; whole-number Each product gate, 18-integral-digit capacity, no rounding/epsilon or implicit repricing. | §§5.3, 5.6, 5.14 | REQ19-AC-071 |
| REQ19-CHG-018 | Plan allocation/source/display/drawdown identifiers conflated | Canonical PSA/Need-or-direct source IDs with exact revisions; separate REQ drawdown/item links; human PIL/SRC reference mapping, explicit historical wire cutover. | §§4–5.6, 5.14, 16.2 | REQ19-AC-005, 007, 072 |
| REQ19-CHG-019 | Multi-year allowed although PLN MVP rejects it | Fixed Single year compatibility gate; no operative multi-year justification or future-funding promise. Preserve historical fields only as evidence. | §§2.1, 5.1, 5.12, 5A, 13.4 | REQ19-AC-055, 079 |
| REQ19-CHG-020 | Fixed Open-Tender template had no method compatibility test | Require Open Tender and owner-validated applicability; expand compatibility to eight independent checks, not an inferred legal waiver. | §5A, 13.11, 16.4A | REQ19-AC-052–053, 055, 079 |
| REQ19-CHG-021 | Late lead reassignment could relabel old certification | HOPF-only reasoned Return/copy at review; frozen certified lead/actor, new routing lead and fresh lead-HoD submission; deterministic default/tie. | §§5.1–5.2, 7.3A, 10, 13.11 | REQ19-AC-047, 050, 073 |
| REQ19-CHG-022 | Handoff referred to multiple HoD decisions contrary to one-certifier rule | Carry one lead-HoD certification covering contributors, distinct HOPF authorisation; task stores required role while actual assignment is decision evidence. | §§5.11–5.12, 7.3 | REQ19-AC-020, 045, 047 |
| REQ19-CHG-023 | Delayed consumption projection used to authorize revocation | Authoritative REQ handoff guard shared by consumption/TPR creation and revocation; one transaction, exact consumer identity/idempotency, no released consumed handoff. | §§5.13, 9.2, 10, 13.12 | REQ19-AC-029–031, 074 |
| REQ19-CHG-024 | Revoked correction promised no explicit entry point | Add CreateRequisitionCorrectionDraft and visible guarded action; changed baseline requires fresh root, no automatic reservation/approval restoration. | §§7.1, 7.4B, 10, 13.12 | REQ19-AC-075 |
| REQ19-CHG-025 | Stopped response/hold/scope UI incomplete | Add complete stopped record/outcome and gate compositions on existing routes; fresh-start dialog, all structured content, unavailable/retry and multiple-request cases. | §§13.12–13.13, 14.6 | REQ19-AC-076–077 |
| REQ19-CHG-026 | Workspace offered Prepare alongside existing Draft | Separate pre-creation/open-root variants, Continue existing Requisition for occupied item; no duplicate by page load or double click. | §§10, 13.3, 14.1 | REQ19-AC-001–002, 068 |
| REQ19-CHG-027 | Technical read and role scope could be narrowed/broadened by prose | Explicit Administrator/System Manager read-all with no business action; Auditor uses actual oversight scope; preserve source-OU eligibility vs user authority distinction. | §§8, 19 | REQ19-AC-032–033, 042, 078 |
| REQ19-CHG-028 | Technical target and connectivity comparator drift | All 11 fixture rows target both items through exact All items; unique per-source item labels; connectivity Required multi-select matches complete retained catalogue. | §§6.3, 13.7, 13.12, 16.3 | REQ19-AC-009–011, 079, 084 |
| REQ19-CHG-029 | Plan boundary overwritten by REQ operational date | Keep 31-Dec Plan/source boundary,24-Sep estimate and 30-Sep REQ latest delivery separate in model, gates, UI and seed. | §§5.2, 5.14, 13.2–13.5, 16.2 | REQ19-AC-080 |
| REQ19-CHG-030 | Positive seed contradicted blocked BASE / one-open invariant | Use conditional READY Youth/Active prerequisites; reset lifecycle profiles independently; preserve two reservations and current authority/fiscal-date gates. | §16 | REQ19-AC-035, 081–083 |
| REQ19-CHG-031 | Cross-document actor/contract/conformance claims stale | Charles Mutiso is canonical; log BUD Kariuki/Need-selection editorial correction; require matching TPR v0.8, wire/provider mapping and actual STD/E2E/legal evidence. | §§16.1, 21, 22.1–22.3 | REQ19-AC-038, 056, 082–083 |
| REQ19-CHG-032 | No full successor change map | Retain all 84 v1.8 results and the full 25-row catalogue; this complete register links implementation locations and tests. | §§17–18, 22.2, 23 | REQ19-AC-084 |
| REQ19-CHG-033 | Five internal validation groups were exposed as five compulsory user steps. | Present exactly three visible tasks while retaining all five validation groups, gates and audit results. | §§1, 6.1, 10.1, 12–14 | REQ19-AC-085–087 |
| REQ19-CHG-034 | Ordinary screens were dominated by drawdown, allocation, scope-lock and handoff terminology. | Apply the §12.1 business-language map; retain exact technical identities in labelled supporting detail and audit. | §§12.1, 13 | REQ19-AC-091, 108 |
| REQ19-CHG-035 | Starting work required a dense pre-creation Planning review. | Use one concise start dialog with approved purchase, departments, availability, boundary and supported product; create nothing until explicit confirmation. | §§12–14.1 | REQ19-AC-088 |
| REQ19-CHG-036 | Requested amounts and equipment were split into separate pages. | Place both under Request details while retaining distinct source rows and reconciliation. | §§6.1, 13.4, 14.3 | REQ19-AC-086 |
| REQ19-CHG-037 | Two same-specification source items required repeated category, name, location and date entry. | Add atomic same-specification item creation and shared-detail update; retain one item per source with independent quantity and intended use. | §§5.6, 10.2, 13.5, 14.1–14.3 | REQ19-AC-113–114 |
| REQ19-CHG-038 | Only a few baseline rows were suggested, forcing routine technical and acceptance rows to be created individually. | Provide complete versioned code-owned `LAPTOP-REQUIREMENTS-V1`: 11 technical rows, 6 support values and 5 acceptance checks. Other supported categories retain their catalogue-driven proposal under the same grouped action. | §§5.5, 6.4, 13.1, 13.6 | REQ19-AC-089–090, 115 |
| REQ19-CHG-039 | Per-row confirmation could leave partial or unseen package state. | Add one atomic `ApplySelectedRequirementPackage` command bound to the visible selected payload and expected proposal/Draft versions. | §§6.4, 10.2, 11, 14.1 | REQ19-AC-089–090, 103–104 |
| REQ19-CHG-040 | Technical, support, service, acceptance and supporting-material work lacked one readable hierarchy. | Consolidate them under Requirements using strong group headings and compact tables without deleting fields or catalogue options. | §§6.1, 13.6 | REQ19-AC-087, 105 |
| REQ19-CHG-041 | One Requirements composition combined Review-required and complete states. | Separate deterministic REQ-DES-05-REVIEW-REQUIRED and REQ-DES-05-COMPLETE reset variants with exact deltas and action states. | §13.6 | REQ19-AC-090, 110 |
| REQ19-CHG-042 | Complete review evidence was overwhelming when every section started open. | Lead with outcome/exceptions; collapse complete non-exception sections behind in-page disclosure while retaining all content. | §§13.7–13.11, 14.4 | REQ19-AC-093–097, 116–118 |
| REQ19-CHG-043 | Procurement review led with compatibility mechanics instead of the decision and financial consequence. | Show readiness, reservation effect, current funding and Planning availability first; retain all eight checks below as enforced supporting evidence. | §§13.9–13.10 | REQ19-AC-094–096 |
| REQ19-CHG-044 | Return reasons did not reliably take the Author to the affected content. | Store an optional governed affected section on the immutable decision and open the copied Draft directly there with the exact comment. | §§5.11, 10.2, 13.4, 13.8–13.9 | REQ19-AC-092 |
| REQ19-CHG-045 | Contributor, direct-HoD, Procurement Officer, Planner and technical-read action sets were incomplete or could inherit incorrect controls. | Define every actor/reset variant and the union-of-live-responsibilities rule; never render disabled unauthorised business actions. | §§8, 13.2–13.13 | REQ19-AC-101–102, 111–112 |
| REQ19-CHG-046 | Departmental Author was given a destructive Cancel-draft implication not authorised by lifecycle. | Use Back to Requisitions; withdrawal remains a governed HoD action with explicit consequence. | §§7.1, 13.4, 13.7–13.8, 14.1 | REQ19-AC-101, 112 |
| REQ19-CHG-047 | Planning-correction pages required users to interpret Versions, roots and owner events. | Present plain waiting, in-progress, completed, no-change, unavailable and another-request-open states; never imply Resume or automatic restart. | §§12.1, 13.12, 14.6 | REQ19-AC-099–100 |
| REQ19-CHG-048 | The design contract depended on values outside the section supplied to the design tool. | Make §13 self-contained with exact technical, support, acceptance, funding, compatibility, actor/state and action fixtures. | §13 | REQ19-AC-109–112 |
| REQ19-CHG-049 | Document completeness could be mistaken for proven usability. | Require representative-user task evidence and make misunderstanding/repeated routine work blocking release findings. | §§17, 18.3–18.4 | REQ19-AC-107–108 |
| REQ19-CHG-050 | UI changes risked becoming a parallel amendment and leaving contradictory v1.8 artboards active. | Incorporate REQ-UX-001 v0.3 into the operative body, replace §§12–14 and make this approved v1.9 the sole successor. | §§1, 12–14, 22.1, 23 | REQ19-AC-084–118 |

### 22.3 Owner dependencies and release evidence

| ID | Outstanding owner work | Required evidence / status |
|---|---|---|
| REQ19-XD-001 | PLN/REQ drawdown, request/hold and correction outcome | Map exact named APIs and schemas, stable/exact identity, owner transaction and outbox boundaries; implement full request/outcome/fresh-start cases. PLN v1.20 specifies the inbound workflow; this MD does not claim current code implements it. |
| REQ19-XD-002 | BUD/REQ complete-array reservation | Replace legacy per-line token calls; prove same-line aggregation, owner lock order, idempotency and full authorisation rollback with actual Budget records. |
| REQ19-XD-003 | FU-30 precision/wire adoption — BUD/NDS/PLN/REQ/TPR | Inspect physical numeric columns, float paths, v1.3 handoff serialization and content-hash mapping; publish coordinated producer/consumer cutover if incompatible. Preserve old values/IDs/digests rather than reinterpreting them. |
| REQ19-XD-004 | TPR v0.8 sibling amendment | Adopt single-year/eight-gate compatibility, exact structured source and reservation lineage, authoritative consumption/revocation coordination and approved invitation-event ownership/envelope. Tender grouping retains both item/source IDs. |
| REQ19-XD-005 | REQ/TPR handoff transaction | Prove Draft Tender creation and authoritative consumption are atomic, compatible with revocation. Late passive projection cannot certify unconsumed state. Keep consumer creation gated until proven. |
| REQ19-XD-006 | Requisition governance/UI | Implement the three-task workflow, atomic shared-item and grouped-package commands, lead-return/recertification, stopped/fresh-start outcomes, full immutable disclosure and exact errors. Prove keyboard, narrow-screen, action-set and representative-user journeys; document completeness is not tested UX. |
| REQ19-XD-007 | Shared seed and live-data reconciliation | Freeze owner-generated exact item/DPP/drawdown/handoff IDs and source-reference mapping; use independent reset worlds, not multiple simultaneous roots. Inspect real reservations/consumption before any migration; no fixture-based overwriting of live histories. |
| REQ19-XD-008 | BUD editorial follow-through | Correct its Charles Kariuki references to shared Charles Mutiso and clarify “Need and selected Budget Line” as the Need-origin **DPP entry’s** selection. BUD’s approved file is not silently rewritten in this REQ review; no new actor/Need field is created. |
| REQ19-XD-009 | CFG/LAW/SEED date and verification prerequisites | Resolve CFG-XD-001’s May 2027 versus FY/profile July-start issue and applicable LAW verification items before positive production/end-to-end claims; do not move dates/FY or mark fixture-verified rules production Verified. |
| REQ19-XD-010 | Referenced standards / legal product conditions | Obtain applicable STD-STD, STD-TPL and E2E source files, verify exact package/schema/rendering and category/equivalence restrictions. Product renderability alone is not legal candidate eligibility. |
| REQ19-XD-011 | Current repository/locking implementation | Inspect actual supported database/transaction APIs, unique guards, shared stable-item/handoff lock order, native location/UOM metadata and AUTH hooks; no assumed column or unproven remote atomicity. |
| REQ19-XD-012 | Historical follow-up tracker | Record documentation approval separately from implementation, contract tests, seed proof and deployment. This successor advances FU-25/FU-30 specification work but cannot mark the cross-module code cycle complete. |

Multi-year funding, scope expansion through Tender amendment, unsupported products/methods, candidate preference entitlement and fulfilment/milestone facilities remain owned by separately approved future changes. REQ does not provide a manual bypass for them.

## 23. Approval effect

**REQ-CHG-001 v1.9 was approved by the Project Owner on 16 September 2026.** It supersedes v1.8 and all earlier Requisition versions in full. REQ-UX-001 v0.3 remains approval evidence rather than a parallel implementation contract. This successor contains the complete structured product, current owner/governance/precision contracts, the three-task usability model, 12 complete artboards with governed variants, 118 acceptance criteria and the 50-row re-implementation register.

Approval is a requirements/design decision. It does not certify code deployment, current primary-law verification, referenced-but-unseen standard conformance, completed artboards, safe migration of unseen live records or passing transactional/precision/browser tests. Implementers must attach concrete evidence to the acceptance criteria and §22.3 dependencies. Historical stopped/submitted/authorised content, exact source identities, decisions and digests remain immutable; fresh work always follows the named guarded command and appropriate new governance.
