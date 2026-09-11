# REQ-CHG-001 — Structured Procurement Requisitions

| Control | Value |
|---|---|
| Document ID | REQ-CHG-001 |
| Version | 1.7 |
| Date | 10 September 2026 |
| Status | **Approved** |
| Approved on | 11 September 2026 |
| Supersedes | v1.6, approved 4 September 2026 — superseded in full by this domain correction; re-approval required |
| Module | Procurement Requisitions |
| First released product | Straightforward IT equipment |
| Standards | Governed by KT-STD-001 v1.4 and STD-STD-001 v1.1. Sections not restated here are inherited from them. |
| Implementation posture | Correct the module in place; no STD Configuration dependency and no attachment-first specification model |
| Change type | Removes this document's own copy of the anti-cramming rule, now centralised in KT-STD-001 §2.2 per that standard's own controlling decision; the concrete history stays, the restated rule doesn't. Corrects §13.12's Authorised Requisition screen, found by direct comparison with a rendered production screenshot: the entire structured package was specified as "complete structured package read-only" — three words, no field, no table, no further definition anywhere in this document — and the implementation built from that specification rendered "Equipment: 2 items," "Technical Requirements: 11 rows," "Acceptance: 5 rows," with no way for the Head of Procurement Function to see what any of them actually were. Replaced with the full labelled breakdown, reusing the exact equipment, technical-characteristic, warranty and acceptance rows §13.6–§13.8 already define — no new data invented, only the display of existing data corrected. The same audit found §13.11's suitability line collapsed all six rows of §5A's compatibility test onto one dot-separated line while its own sentence claimed the opposite ("every row... not a single collapsed pass/fail") — now genuinely six rows. §13.9's summary cards and §13.3's workspace card had smaller instances of the same pattern — a value, a department list and a title joined with `·` under one line — split into labelled parts. One rule added to §13.1 naming this exact defect as the reason it exists, with an explicit carve-out for the two uses of `·` that were never the problem (identifier lineage, status-count badges), so the rule doesn't overcorrect into banning a legitimate pattern along with the illegitimate one. Earlier: A cross-document accuracy pass against CFG, STR, BUD, NDS and PLN in their current state found: PLN-CHG-001's own `RequisitionEligibilityProjection` never actually listed several fields this document claimed to receive from it — corrected in both documents together; no compatibility test existed anywhere in this document despite being asserted repeatedly, risking a real Budget reservation against a Plan Item Tender Preparation would reject outright; `procurement_category` was never checked, so a Works or Services Plan Item had no gate stopping it from reaching an IT-goods package; and the Strategic Objective and plan horizon were inherited nowhere, leaving the policy justification for a public procurement invisible except by a second query into Planning. Earlier still: Corrects a genuine domain-model contradiction v1.4's restoration introduced — an item row spanning two drawdown lines, which §5.6 does not permit — and closes five completeness/UX gaps the artboards had: a dangling section reference, a duplicated common-states table, a designed-but-unbuilt lead-department reassignment control, a required confirm-or-remove moment for proposed baseline characteristics with no artboard, and a workspace still showing PLN-DES-01's original disconnected-sections pattern. Adds a quick-fill default for the common full-balance drawdown case. Earlier still: **v1.3 was defective and is withdrawn.** While correcting the authorization model and adding the Budget reservation mechanism, v1.3 replaced roughly 450 lines of the approved v1.2's requirements content — the full characteristic catalogue in §6, the field-by-field detail of all ten artboards in §13, half the acceptance criteria, half the test/smoke contract, and most of the seed detail — with brief summaries and a pointer back to "the original." That is not how a document that supersedes another in full may be written. v1.4 restores every line of v1.2's original content, verified section by section against the source, and keeps every genuine correction v1.3 made — the authorization model, the Budget reservation call, the cross-department relaxation, the upstream-correction design, reservation/lotting carriage, and the Ministry of Health rename — as additions woven into the full original, not replacements for it. |

**Controlling decision:** A Procurement Requisition turns one approved Planning allocation into one precise departmental request. For the first release, the department completes a fixed, code-owned IT Equipment Requirement Package. Structured items, technical requirements, services and acceptance checks are the authoritative requirements. Files may support those rows but cannot replace them.

## 1. Governing decision

This document is the requirements document to consult for Procurement Requisitions. v1.2 is superseded in full.

The module shall not contain an STD selector, Requirements Composer Manifest, schema editor, mapping editor or generic requirements engine. Tender Preparation selects the released Tender template after Requisition authorisation.

Implementation must produce one coherent result across schema, services, permissions, screens, fixtures and tests. A field, action, state, role, screen or service not defined here is outside this release.

### 1.1 Corrected earlier directions

| Earlier direction | Treatment in v1.3 |
|---|---|
| Requisition binds to a Requirement Composer Manifest from STD Configuration | Unchanged from v1.2: removed. The first release uses the code-owned IT Equipment Requirement Package in section 6. |
| Technical specification PDF as the primary requirement | Unchanged from v1.2: removed. Structured rows are authoritative. TPR-CHG-001 v0.7 is now the corrected consumer this required — that correction is delivered, not still pending. |
| Custom Capability Profiles, Operational Scope Assignments, native Frappe Roles, Workflow permissions and User Permissions | **This is now the defect.** AUTH-ADR-001 v1.7 established role-bound `User Responsibility Assignment`, resolved through registered `permission_query_conditions` and `has_permission` hooks, as the sole authorization mechanism. This is not a new custom layer; it is the one mechanism every other approved KenTender module already uses. |
| `pe_fy_context_id` on the Requisition record | Removed. One site is one Procuring Entity, configured once by CFG-CHG-002 and never selected or scoped per record. Fiscal Year is inherited display data from the Plan Item, never a scope dimension. |
| "A second budget check or reservation" named as explicitly unsupported | **This is now the defect, and the most consequential one in this revision.** BUD-CHG-001 v1.4 moved fund reservation out of Procurement Planning specifically because Procurement Requisitions was assumed to be its new home — "reservation begins at Procurement Requisition, where money is actually drawn." This document never implemented that call. The result was a real gap running through the whole approved chain: nothing, anywhere, ever reserved money. §9.1A closes it. |
| One Requisition uses one Plan Item and one requesting department | **Relaxed, narrowly.** SEED-001 v1.2's harmonized scenario combines two departments' Needs into one Plan Item at Planning, per PLN-CHG-001's own combine rule. A Requisition against that Plan Item cannot honestly claim one requesting department. See §2.1 and §7.5 invariant 1 for the exact, narrow scope of this change — it is not a general opening of cross-department Requisitions. |
| Golden fixture keyed to Kenya Bureau of Standards | Removed. Renamed to Ministry of Health throughout, per SEED-001 v1.2. |
| Upstream correction as one sentence of intent | Designed for real in §7.4A, matching the level of design TPR-CHG-001 §10.4 already has for its own upstream hop. |

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
- one Requisition and one later award package;
- whole-number equipment quantities in `Each`;
- structured pass/fail technical requirements;
- the inherited reservation category and lotting indicator, carried through unedited; and
- the released `IT-EQUIPMENT-OPEN-V1` Tender pattern.

It does not support:

- custom software, systems implementation, integration, migration or hosting;
- Works, consulting services or non-consulting services;
- multiple currencies, lots or award packages;
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
| Budget Line, funding, planned method, schedule, reservation category and lotting indicator | Planning and Budget | Inherit read-only. Authorisation rechecks Planning availability **and creates the Budget reservation**, per §9.1A — this module is the reservation's actual owner, not merely its checker. |
| Supplier evidence, qualification and Tender choices | Procurement | Add later in Tender Preparation; never require the department to define them. |
| Standard Tender text and released forms | Code-owned Tender template | Requisition neither selects nor edits them. |
| Requisition authorisation | Head of Procurement Function | Decide the complete immutable submission; cannot edit it. |
| Tender creation and approval | Tender Preparation | Consume the immutable handoff and apply its own approved lifecycle. |

Procurement staff may help the department express a requirement. A competent technical officer may contribute. This does not create another task, reviewer or approval stage. The Departmental Author remains responsible for the Draft and the Head of User Department confirms the departmental request.

## 4. Stable lineage

Every material row keeps a stable identifier.

| Identifier | Created by | Carried to |
|---|---|---|
| `source_line_id` | Departmental Need or direct DPP entry | Plan, Requisition, Tender and contract schedule |
| `plan_item_line_id` | Approved Plan Item allocation | Requisition drawdown and Tender |
| `requisition_item_id` | Requisition | Goods schedule, price schedule and contract schedule |
| `technical_requirement_id` | Requisition | Technical schedule, bidder response and evaluation |
| `service_requirement_id` | Requisition | Service schedule, bidder response and contract obligation |
| `acceptance_requirement_id` | Requisition | Acceptance schedule and contract obligation |
| `supporting_material_id` | Requisition | Tender package index and the structured rows it supports |
| `reservation_id` | **New.** Created by this module's Budget reservation call at authorisation | Handoff, and Budget's own Active reservations table |

Descriptions are not identifiers. The system shall not reconstruct lineage by comparing text.

## 5. Canonical domain model

All identifiers, references, version numbers, digests, actors and timestamps are server-managed.

### 5.1 ProcurementRequisition

Stable root for one departmental request against one Active Plan Item.

| Field | Purpose and rule |
|---|---|
| `requisition_id` | Immutable internal identity. |
| `requisition_reference` | Generated `REQ-{PE code}-{FY start}-{Plan Item number}-{3 digits}`. There is no `pe_fy_context_id`; the site is implicit and the Fiscal Year is read from the Plan Item. |
| `plan_id` / `plan_version_id` / `plan_item_id` | Exact Active Planning baseline; immutable. |
| `strategic_objective_id` / `strategic_objective_path` | **New.** Inherited read-only from PLN-CHG-001 §4.14's projection, itself sourced from the immutable snapshot Planning creates at Plan Item approval. Carried explicitly here, and into the handoff in §5.12, rather than left reachable only by a second query back into Planning — an auditor reading the Requisition alone can see which policy objective justified it. |
| `procurement_category` | **New.** Inherited read-only; `Goods` for this release, checked at compatibility per §5A. |
| `plan_horizon` / `multi_year_justification` | **New.** Inherited read-only. `Single year` or `Multi-year`; the justification only where Multi-year. Displayed so a preparer understands whether the value shown is one year's allocation or a multi-year total — see §13.4's notice. Never a compatibility gate; see §5A. |
| `contributing_org_unit_ids` | One or more Organisation Units — one, in the ordinary case; more than one only where the Plan Item was itself formed at Planning as a cross-department combine, matching exactly the departments Planning's own combine recorded. Immutable. |
| `lead_org_unit_id` | The Organisation Unit whose Head of User Department certifies the departmental submission when more than one department contributed. Defaults to the department with the largest drawn value. Confirmed implicitly at departmental submission; may be changed only by the Head of Procurement Function, only at authorisation review per REQ-DES-09, with a required reason — this is the one place it can change, since the Head of Procurement Function is the first actor to see the complete submitted package and judge whether the default made sense. |
| `current_version_id` | Current Draft, submitted or authorised Version. |
| `authorised_version_id` | Exact authorised Version; empty before authorisation. |
| `current_state` | Derived root state from section 7. |
| `planning_drawdown_reference` | Planning reference created only on authorisation. |
| `reservation_ids` | Budget reservation references, one per drawdown line, created only on authorisation. Empty before it. |
| `handoff_id` | Immutable downstream handoff; empty before authorisation. |
| `handoff_consumed_at` | Neutral downstream-consumption projection. |
| `record_version` | Optimistic-concurrency token. |

Only one open Requisition may exist for the same `plan_item_id`.

### 5.2 RequisitionVersion

One complete decision snapshot.

| Field | Purpose and rule |
|---|---|
| `requisition_version_id` | Immutable Version identity. |
| `requisition_id` | Stable parent. |
| `version_number` | Generated sequence. |
| `based_on_version_id` | Returned or revoked Version copied for correction. |
| `version_status` | `Draft`, `Awaiting Department Approval`, `Submitted to Procurement`, `Returned`, `Authorised`, `Withdrawn`, `Revoked`, `Upstream correction required` or `Superseded`. |
| `requirement_title` | Required; 5–160 characters. Initially inherited from Planning and editable only while Draft. |
| `delivery_location_id` | Required Link to an Active Location. |
| `delivery_address_snapshot` | Generated from the selected location at submission. |
| `latest_delivery_date` | Required; not later than the approved Plan completion date or any selected source boundary. |
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
| `plan_item_line_id` | Exact eligible Planning allocation. |
| `source_line_id` | Original Need or direct-DPP lineage. |
| `contributing_org_unit_id` | Which of `contributing_org_unit_ids` this specific line belongs to. Always one value, even when the Requisition itself spans more than one department. |
| `approved_quantity` / `approved_value` | Read-only Planning values. |
| `remaining_quantity` / `remaining_value` | Read-only evaluation-time values. |
| `requested_quantity` | Positive whole number, not above remaining quantity. |
| `requested_value` | Positive KES amount, not above remaining value. |
| `unit` | Read-only Planning unit; `Each` for the first product. |
| `reservation_id` | Empty until authorisation; one reservation per drawdown line, per §9.1A. |

At submission, requested lines are locked. At authorisation, Planning rechecks every line and commits all or none, and Budget reserves every line's value or none.

### 5.4 ITEquipmentRequirementPackage

Stable package root created with the Requisition. It has no profile, manifest or user-selected schema.

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
| `content_digest` | Canonical digest of every package row and file reference. |

### 5.6 RequisitionItem

At least one item is required.

| Field | Control and rule |
|---|---|
| `requisition_item_id` | Generated, read-only. |
| `package_version_id` | Owning package Version. |
| `plan_item_line_id` | Required Link to one selected drawdown line. |
| `equipment_category` | Required Select: `Laptop`, `Desktop computer`, `Monitor`, `Tablet`, `Printer`, `Scanner`, `Network equipment`, `Power-protection equipment`, `Other IT equipment`. |
| `item_name` | Required single-line text, 3–120 characters. |
| `quantity` | Required positive whole number. |
| `unit` | Read-only `Each`. |
| `intended_use` | Required plain text, 10–500 characters. |
| `delivery_location_id` | Defaults from Version; may select another Active location for the same site. |
| `latest_delivery_date` | Defaults from Version; may be earlier, never later. |
| `row_order` | Generated stable display order. |

The total item quantity linked to a drawdown line must equal that line's requested quantity before submission. `Other IT equipment` requires a specific supplier-neutral item name; it does not create a new template category.

### 5.7 TechnicalRequirement

Each enforceable technical characteristic is a separate row.

| Field | Control and rule |
|---|---|
| `technical_requirement_id` | Generated, read-only. |
| `applies_to` | Required Link to one Requisition Item or `All items`. |
| `characteristic_key` | Required Select from the released catalogue in section 6.3. |
| `comparison` | Fixed by the characteristic: `Minimum`, `Maximum`, `Exact`, `Required` or `One of`. Read-only. |
| `required_value` | Typed control fixed by the characteristic. |
| `other_value` | Required bounded text only when the selected characteristic or controlled option explicitly permits `Other`; never a substitute for a listed value. |
| `unit` | Fixed by the characteristic where applicable. Read-only. |
| `mandatory` | Read-only `Yes` in this release. |
| `reason` | Required only for `Other essential characteristic`; 20–300 characters. |
| `row_order` | Generated stable display order. |

The system rejects duplicate characteristic keys for the same target unless the catalogue explicitly permits repetition.

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
| `check_type` | Required Select: `Quantity`, `Physical condition`, `Required specification`, `Functional test`, `Installation complete`, `Documents received`, `Other objective check`. |
| `pass_condition` | Required plain text, 10–500 characters; must state an observable result. |
| `evidence_type` | Required Select: `Inspection record`, `Test result`, `Delivery note`, `Certificate`, `Other stated record`. |
| `other_evidence_name` | Required single-line text, 3–120 characters, only when evidence is `Other stated record`. |
| `row_order` | Generated stable display order. |

"Satisfactory", "acceptable" or similar wording without an observable condition is invalid.

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

`RequisitionTask` records one protected decision queue item for the Head of User Department or Head of Procurement Function. It stores the exact Version, business role, the exercised `User Responsibility Assignment` ID, status, due display data and decision token. It grants no authority by itself. There is no PE/FY scope on this record — only the Organisation Unit scope a departmental task genuinely needs.

`RequisitionDecision` stores the exact task, Version, actor, legal capacity, decision, required return reason where applicable, timestamp and resulting state. Decisions are immutable.

### 5.12 AuthorisedRequisitionHandoff v1.3

One immutable handoff is created atomically with authorisation. It contains:

- Requisition, Version and content digest;
- the site, Financial Year, contributing department(s), Plan, Plan Version and Plan Item;
- the Strategic Objective and its full ancestor path;
- procurement category, plan horizon and, where Multi-year, its justification;
- every drawdown line, `source_line_id`, `plan_item_line_id` and its own `reservation_id`;
- inherited business need, description and expected operational result;
- planned method, schedule, Budget Line and funding source;
- the reservation this handoff's own authorisation created — not an inherited reference, a fact this module produced;
- reservation category and lotting indicator;
- requirement title, location and latest delivery date;
- every equipment item and `requisition_item_id`;
- warranty and support values;
- every technical, service and acceptance row with stable IDs;
- supporting-material metadata, links and digests;
- Head of User Department (or Heads, where more than one department contributed) and Head of Procurement Function decisions;
- `product_pattern = IT Equipment` and first-release suitability facts; and
- handoff version, generated time and handoff digest.

It contains no editable STD binding, supplier field, price, evaluation score or contract result.

### 5.13 TenderConsumptionProjection

Tender Preparation records handoff consumption idempotently using handoff ID, Tender ID, Tender Version, template key/version and consumed time. Requisitions uses this projection only to control revocation and show neutral status, and to trigger nothing else — the milestone-actual write-back in TPR-CHG-001 §9.5 is a Tender Preparation concern, not a Requisition one.

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

`plan_horizon` is deliberately **absent** from this table: a Multi-year Plan Item is not incompatible with an IT Equipment Requisition. It changes what the drawn value *means* — see §5.1's new field — but it blocks nothing here.

Any No blocks Requisition creation with no free-text bypass, returning `REQ_PRODUCT_UNSUPPORTED` and naming the failing test.

## 6. Fixed IT Equipment Requirement Package

**Restored in full in v1.4.** v1.3 replaced this entire section with a five-line summary and a pointer back to "the original" — an editing error, corrected here. Nothing in this section depends on the authorization model, the Budget gap, or the entity identity; it is reproduced exactly as v1.2 defined it.

### 6.1 Five preparation steps

The department completes five fixed steps:

1. **Request and drawdown** — confirm Planning lineage, requested quantities and requested value.
2. **Equipment items** — state the equipment, intended use, quantity, location and date.
3. **Technical and support** — select minimum characteristics and state warranty/support needs.
4. **Services and acceptance** — state related services, objective acceptance checks and supporting materials.
5. **Review and submit** — resolve blockers, preview the complete package and route it.

The user cannot add, remove, rename or reorder steps.

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

### 6.4 Automatic baseline rows

Creating an item proposes, but does not silently confirm, these baseline rows:

- Electrical compatibility = Required;
- New and unused equipment = Required;
- minimum warranty from the package value; and
- category-relevant memory, storage, connectivity or functional rows where applicable.

Proposed rows are visibly marked **Confirm or remove**. Every proposed row must be confirmed by the Departmental Author before submission. Copying a prior authorised package follows the same rule.

### 6.5 Completion and validation

Step completion is derived:

| Step | Complete when |
|---|---|
| Request and drawdown | At least one current eligible drawdown line is selected; every requested quantity/value is valid; title, location and date are complete. |
| Equipment items | At least one item exists; each item is complete; item quantities reconcile to drawdown lines. |
| Technical and support | Every item has confirmed baseline characteristics; warranty/support controls are complete; no duplicate or invalid rows exist. |
| Services and acceptance | Conditional service rows are complete; at least one objective acceptance row exists; every operative file is linked to a structured row. |
| Review and submit | All preceding steps are complete; no Blocking finding exists; the complete preview and digest render successfully. |

Blocking findings include:

- Planning eligibility, quantity or value changed;
- a date exceeds an approved Planning boundary;
- item quantities do not reconcile to drawdown lines;
- a required item or characteristic is missing;
- an unsupported category or control value is posted;
- a proposed baseline row remains unconfirmed;
- a requirement is internally contradictory;
- a service shows complex development, integration or migration;
- an acceptance condition is subjective or empty;
- an operative file has no linked structured obligation;
- a brand or restrictive term lacks permitted equivalent treatment;
- the package is incompatible with the first product; or
- the canonical preview or digest cannot be produced.

Warnings do not block submission. They remain visible to the Head of User Department and Head of Procurement Function. Examples are unusually high minimum values, optional supporting material or a delivery date close to the Plan boundary.

## 7. Lifecycle and governance

### 7.1 State model

| Current state | Action | Actor | Result |
|---|---|---|---|
| No record | Prepare Requisition | Departmental Author or Head of User Department | Draft root, Version 1 and fixed package created from current Planning eligibility |
| Draft | Save Draft | Draft owner or Head of User Department in scope | Same Draft updated and validation refreshed |
| Draft | Send for department approval | Departmental Author | Version and package locked; state `Awaiting Department Approval`; task created for the lead department's Head of User Department |
| Draft | Submit to Procurement | Head of User Department preparing directly | Version and package locked; state `Submitted to Procurement`; Procurement task created |
| Awaiting Department Approval | Return for correction | Head of User Department | Reviewed Version preserved; copied Draft successor created |
| Awaiting Department Approval | Submit to Procurement | Head of User Department | Same locked Version becomes `Submitted to Procurement`; Procurement task created |
| Submitted to Procurement | Return to department | Head of Procurement Function | Submitted Version preserved; copied Draft successor created |
| Submitted to Procurement | Authorise for Tender Preparation | Head of Procurement Function | Planning drawdown, **Budget reservation**, decision and immutable handoff committed atomically; state `Authorised` |
| Awaiting Department Approval or Submitted to Procurement | Withdraw | Head of User Department | Locked Version retained; state `Withdrawn`; no drawdown, no reservation |
| Authorised; handoff unconsumed | Revoke authorisation | Head of Procurement Function | Authorised evidence retained; exact drawdown and reservation reversed; state `Revoked` |
| Draft, Returned or Submitted | Request upstream correction | Head of User Department or Head of Procurement Function | Version preserved as `Upstream correction required`; starts §7.4A |

There is no separate technical review, requirements approval, Finance approval, Accounting Officer approval or committee stage in the Requisition lifecycle.

### 7.2 Submission and authorisation gates

Before departmental routing or submission, the server rechecks:

- the required business role, resolved through the registered permission hooks;
- current Planning eligibility and open balance;
- every field and row control in this document;
- step completion and zero Blocking findings;
- supporting-file security and digest;
- product suitability, including reservation category and lotting; and
- canonical content digest.

Before Procurement authorisation, the server repeats every check against the immutable submitted Version and current Planning balances, **and additionally calls Budget's `check_funding` for every drawdown line before committing.** Authorisation succeeds only if the drawdown, the reservation, the decision, the outbox event and the handoff all commit together.

### 7.3 Maker-checker rules

- A Departmental Author cannot complete the Head of User Department decision on the same Version unless the actor is independently assigned the Head of User Department role and prepared the Requisition directly in that capacity.
- A Head of User Department may prepare and submit a Requisition directly; this removes an unnecessary internal task but not the Procurement authorisation.
- The Head of Procurement Function cannot edit departmental content.
- The actor performing Procurement authorisation cannot also be recorded as the departmental submitting authority for the same Version.
- Where more than one department contributed, the lead department's Head of User Department certifies the whole submission on behalf of every contributing department; this is a single certification, not one per department, and it is a deliberate simplification named here rather than hidden.
- Administrator or System Manager access grants no business decision.

### 7.4 Corrections

A return requires one reason of 20–1,000 characters. The reviewed Version stays immutable and a copied Draft successor is created.

After authorisation:

- before handoff consumption, the Head of Procurement Function may revoke, reverse the exact Planning drawdown and Budget reservation, and allow a corrected successor;
- after handoff consumption, Requisitions cannot revoke or edit the authorised package; Tender Preparation uses its own upstream-correction route, per TPR-CHG-001 §10.4; and
- after publication, clarification, addendum, cancellation or a new proceeding is governed downstream, in modules that do not yet exist.

### 7.4A Upstream correction to Planning — designed for real

**New in v1.3.** v1.2 said only: "If a Planning fact is wrong, the Requisition is not edited around it. The user follows the approved Planning successor or correction route." That was a principle with no mechanism behind it. This is the mechanism, matching the standard TPR-CHG-001 §10.4 already set for its own upstream hop.

1. The Head of User Department or the Head of Procurement Function selects **Request upstream correction** and gives a required reason identifying the wrong Planning fact — the Plan Item's description, its Strategic Objective, its Budget Line, or a source allocation's quantity or value ceiling.
2. The server closes the current Version as `Upstream correction required`, preserving it exactly, and creates one `PlanItemCorrectionRequest` naming the Plan Item, the reason, the requesting Requisition, and the actor.
3. This request is visible in Procurement Planning's own workspace as a task for the Procurement Planner — **this is a required correction to PLN-CHG-001**, named in §17, since no such inbound contract exists there today.
4. Planning resolves the request through its own governed mechanism: where the Active Plan Version is still open to correction, the Planner forms a corrected allocation; otherwise, correcting the baseline itself requires a Plan successor, following PLN-CHG-001's own Version lifecycle. Requisitions does not shortcut this by accepting an unreviewed local edit.
5. Once Planning's correction is Active, a neutral projection notifies the stopped Requisition. A fresh Draft is prepared against the corrected allocation; the stopped Version is never resurrected or silently edited.
6. Every step of this preserves the original stopped Version's content and reason as permanent evidence.

This route exists specifically for defects in what Planning approved. A defect in what the *department* asked for is a departmental correction under the ordinary return route in §7.4, not an upstream correction.

### 7.5 Core invariants

1. One Requisition uses one Plan Item and either one requesting department, or, only where Planning itself formed the Plan Item as a cross-department combine, exactly the departments Planning's own combine recorded — never a department Planning did not include.
2. Every selected Planning allocation belongs to one of the Requisition's contributing departments.
3. One open Requisition exists per Plan Item.
4. Requested quantity and value never exceed current remaining Planning balances.
5. Every item links to one drawdown line; reconciled quantities are exact.
6. Planning and Strategy facts are read-only. Budget facts are read-only **except the reservation this module itself creates at authorisation.**
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
| Departmental Author | Organisation Unit | View eligible Planning allocations for the assigned department; prepare and correct a Draft; send a complete Version to the Head of User Department. |
| Head of User Department | Organisation Unit | View the complete departmental Requisition; prepare and submit directly, or return/submit an Author's locked Version; withdraw before authorisation; certify on behalf of every contributing department when more than one exists. |
| Head of Procurement Function | Site-wide | View the complete submitted Requisition and fresh Planning and Budget availability; return, authorise or revoke before consumption. Cannot edit requirements. Same registry entry as DSP-CHG-001 and TPR-CHG-001 use for this office. |
| Procurement Planner | Site-wide | Neutral read of Planning lineage and drawdown projection; receives the `PlanItemCorrectionRequest` task in §7.4A; no Requisition decision. |
| Procurement Officer | Site-wide | No Draft right in Requisitions by virtue of this role; consumes the authorised handoff in Tender Preparation. |
| Auditor | Site-wide or approved OU oversight scope | Neutral read of immutable Versions, decisions, drawdowns, reservations, handoffs and consumption evidence; no business transition. |
| Administrator / System Manager | — | Technical administration only, per AUTH-ADR-001 v1.7 §8; no Requisition decision. |

An acting Head of User Department receives a time-bound `User Responsibility Assignment` for the approved period, with an authority reference — not a scoped Frappe User Permission, and not a delegate role.

Every list, count, direct route, file download and command applies the same registered predicate before data is returned — Organisation Unit scope where the role genuinely has one, site-wide otherwise, and no PE or Fiscal Year scope anywhere, because neither is a dimension this module's authorization checks.

## 9. Cross-module contracts

### 9.1 Procurement Planning

`GetRequisitionEligiblePlanItem` is the only starting projection. It returns the exact approved facts PLN-CHG-001 v1.15 defines, including reservation category, lotting indicator and, where the Plan Item is a cross-department combine, every contributing Organisation Unit.

`AuthoriseRequisitionDrawdown` locks and rechecks every selected allocation and accepts all lines or none. It is called only inside Requisition authorisation, in the same transaction as §9.1A's Budget call.

`ReverseRequisitionDrawdown` restores the exact quantities and values once when an unconsumed authorisation is revoked, in the same transaction as the Budget reservation's reversal.

`PlanItemCorrectionRequest` (**new**) is the outbound half of §7.4A's upstream-correction route — the inbound receiving task is a required correction to PLN-CHG-001, named in §17.

Draft creation, save, departmental submission and Procurement return perform no Planning write and no Budget write.

### 9.1A Budget — the reservation this module was always meant to create

**New in v1.3.** This is the single most consequential addition in this revision. BUD-CHG-001 v1.4 stated plainly, months ago, that "reservation begins at Procurement Requisition, where money is actually drawn." Nothing in v1.2 of this document ever called the contract that makes that true. The result was a real gap: from the moment BUD-CHG-001 moved reservation out of Planning until this version, no module anywhere in the approved chain ever reserved a shilling.

At `AuthoriseRequisition`, in the same atomic transaction as the Planning drawdown:

1. For every `RequisitionDrawdownLine`, call Budget's `check_funding` with the line's Procurement Budget Line, requested value and a correlation ID. This is non-mutating and returns a short-lived token and current position for each line.
2. If every line's check passes, call `reserve_funding` with the returned tokens, one idempotency key for the whole authorisation, and the exact drawdown lines.
3. Budget locks the affected lines in stable ID order, reloads positions and creates one reservation per drawdown line — matching BUD-CHG-001 §8.2A exactly.
4. If any line fails either call, the entire `AuthoriseRequisition` command rolls back: no drawdown, no reservation, no decision, no handoff. The failing line and its exact shortfall are returned to the Head of Procurement Function.
5. The created `reservation_id`s are stored on their owning drawdown lines and included in the handoff, per §5.12.

Revocation before handoff consumption reverses this in the same transaction as the Planning drawdown reversal, calling Budget's own release contract once per reservation.

### 9.2 Tender Preparation

Authorisation publishes `ProcurementRequisitionAuthorised.v1.3` through the transactional outbox. Tender Preparation consumes the exact handoff idempotently.

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

**This correction is complete.** TPR-CHG-001 v0.7 is the corrected consumer this section previously said had to exist before implementation could join the modules. It no longer treats any attachment as the primary technical requirement.

### 9.3 No STD Configuration contract

Requisitions calls no STD Configuration, manifest, schema or mapping service. It stores no STD package, manifest, compatibility signature or schema digest. Product suitability is a typed rule for the fixed IT Equipment product, not a generic engine.

## 10. Service and command contracts

### 10.1 Reads

| Service | Required result |
|---|---|
| `GetRequisitionWorkspace` | Eligible Plan Items, own Drafts, protected tasks and neutral authorised status, using the registered predicate. |
| `GetEligiblePlanItemDetail` | Complete Planning projection, current remaining balances, reservation category and lotting indicator; no mutation. |
| `GetRequisitionEditor` | One server projection containing Planning context, Draft values, package rows, validation, step status and permitted actions. |
| `GetDepartmentApprovalTask` | Complete immutable Version and package for the exact Head of User Department task. |
| `GetProcurementAuthorisationTask` | Complete submitted Version, package, files, validation snapshot, fresh Planning availability and fresh Budget affordability. |
| `GetAuthorisedRequisitionHandoff` | Exact immutable v1.3 handoff for an authorised consumer. |
| `GetRequisitionHistory` | Versions, decisions, drawdown, reservation, reversal, upstream-correction and handoff-consumption evidence; no mutation. |

Reads never create a root, Version, package, row, task, decision, drawdown, reservation or handoff.

### 10.2 Commands

| Command | Core effect |
|---|---|
| `PrepareITEquipmentRequisition` | Lock eligibility; create or return the one existing Draft root, Version and fixed package. |
| `SaveRequisitionSummary` | Save valid drawdown, title, location, date and related-services choice. |
| `AddRequisitionItem` / `UpdateRequisitionItem` / `RemoveRequisitionItem` | Mutate one Draft item and recheck quantity reconciliation. |
| `AddTechnicalRequirement` / `UpdateTechnicalRequirement` / `RemoveTechnicalRequirement` | Mutate one typed Draft characteristic using the released catalogue. |
| `SaveWarrantyAndSupport` | Save only the controlled package fields. |
| `AddRelatedService` / `UpdateRelatedService` / `RemoveRelatedService` | Mutate one conditional Draft service row. |
| `AddAcceptanceRequirement` / `UpdateAcceptanceRequirement` / `RemoveAcceptanceRequirement` | Mutate one objective Draft acceptance row. |
| `AddSupportingMaterial` / `UpdateSupportingMaterial` / `RemoveSupportingMaterial` | Attach one governed private file and row links after checks. |
| `ConfirmProposedRequirement` | Mark one system-proposed baseline row deliberately confirmed. |
| `ValidateRequisition` | Recompute deterministic findings and preview digest; does not change lifecycle. |
| `SendForDepartmentApproval` | Lock exact content and create one HoD task for the lead department. |
| `ReturnToDepartmentAuthor` | Preserve reviewed Version and create copied Draft successor with reason. |
| `SubmitRequisitionToProcurement` | Record departmental submission and create one Procurement task. |
| `ReturnRequisitionToDepartment` | Preserve submitted Version and create copied Draft successor with reason. |
| `AuthoriseRequisition` | Atomically recheck, draw down Planning, reserve funding per §9.1A, decide, create handoff and publish outbox event. |
| `WithdrawRequisition` | Close pre-authorisation Version with no drawdown and no reservation. |
| `RevokeUnconsumedAuthorisation` | Reverse exact drawdown and reservation, preserve evidence and publish revocation. |
| `RecordHandoffConsumption` | Idempotently store neutral Tender consumption evidence. |
| `RequestUpstreamPlanCorrection` | Preserve the current Version as `Upstream correction required` and create the `PlanItemCorrectionRequest` in §7.4A. |

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

`REQ_ROLE_REQUIRED` and `REQ_SCOPE_DENIED` are removed, for the same reason TPR-CHG-001 removed its equivalents: the first named a bare Frappe role rather than a resolved responsibility, and the second named a PE/FY/OU scope that, for PE and FY, no longer exists. A record outside the actor's authorised responsibility returns `REQ_NOT_FOUND`.

## 12. UI architecture and routes

Use Vue 3 single-file components mounted in Frappe Desk. Reuse the existing KenTender shell, header, breadcrumb, tokens, table and dialog components. Do not import design-tool runtime code, recreate the Frappe shell, or add a Procuring Entity selector.

| Surface | Route | Purpose |
|---|---|---|
| Requisitions workspace | `/app/procurement-requisitions` | Eligible Plan Items, own Drafts, tasks and authorised records. |
| Start Requisition | `/app/procurement-requisitions/new/{plan_item_id}` | Confirm the exact Planning source and create/reuse the Draft. |
| Requisition editor | `/app/procurement-requisitions/{requisition_id}` | Complete the five fixed steps. |
| Department approval | `/app/procurement-requisitions/department-task/{task_id}` | HoD reads the complete locked Version and returns or submits. |
| Procurement authorisation | `/app/procurement-requisitions/procurement-task/{task_id}` | Head of Procurement Function reads the complete submission and returns or authorises. |
| Authorised Requisition | `/app/procurement-requisitions/{requisition_id}/authorised` | Read immutable handoff, drawdown, reservation and Tender-consumption status. |

The editor loads one server projection. Opening a route creates nothing except when the user completes the explicit **Prepare Requisition** command. Per KT-STD-001 §3A: the authorisation verdict resolves before any content renders, and a page-load denial is an inline Forbidden state, never a modal.

## 13. Static Claude Design contract

Supply **KT-STD-001 §2 plus this section** to Claude Design. Fixture actors, Organisation Units and Fiscal Years come from KT-STD-001 §8, extended by §13.2.

### 13.1 Global rules

Create only the artboards listed below at 1440 × 1024. Use the exact labels, fixture values, control types and read-only treatment. Do not add dashboards, charts, scores, comments, generic attachment panels, extra reviewers, extra approvals, a Procuring Entity row or column, or any field not defined here.

Every editor artboard uses:

- eyebrow **PROCUREMENT REQUISITIONS**;
- title **Clinical training and deployment laptops for digital health rollout**;
- quiet line **REQ-MOH-2027-033-001 · PPI-MOH-2027-033 · Version 1**;
- status badge **Draft** unless the artboard states another status;
- left step navigation with exact completion text; and
- footer actions **Save draft** and the exact next action.

§13.12 carried exactly this defect until correction — "complete structured package read-only," three words with no further definition, which is how an implementation ended up inventing bare counts, "2 items," "11 rows," with no way to see what any of them were. The general rule against that is now centralised in KT-STD-001 §2.2, per that standard's own controlling decision that a rule repeated verbatim across change units is deleted from them once centralised — it is inherited here, not restated. Identifier lineage (`REQ-MOH-2027-033-001 · PPI-MOH-2027-033 · Version 1`, above) and status-count badges (`0 Blocking · 1 Warning`) are not instances of it.

### 13.2 Shared Ministry of Health fixture

**Renamed from Kenya Bureau of Standards, per SEED-001 v1.2.**

| Context | Exact value |
|---|---|
| Procuring Entity | Ministry of Health |
| Financial Year | FY 2027/28 |
| Contributing departments | Human Resources Management and Development (100 each) and Digital Health (150 each) |
| Lead department | Digital Health — larger contributed value |
| Plan Item | `PPI-MOH-2027-033` — Clinical training and deployment laptops for digital health rollout |
| Procurement method | Open Tender |
| Reservation category | None |
| Lotting | Single lot |
| Planned value | KES 50,000,000.00 |
| Planned completion | 30 September 2027 |
| Strategic Objective | `OBJ-MOH-2023-001` — Strengthen interoperable national digital health services |
| Objective path | Digital health systems › Health policy, standards and regulation › Digital health governance |
| Plan horizon | Single year |
| Business need | Equip clinical training and field deployment staff with a common laptop specification for the national digital health rollout. |
| Expected operational result | Staff can use secure, supported equipment for training and field digital-health work. |
| Delivery location | Ministry of Health Headquarters, Afya House, Nairobi |
| Latest delivery date | 30 September 2027 |

Planning allocations:

| Plan item line | Source line | Contributing department | Requirement | Remaining quantity | Remaining value |
|---|---|---|---|---:|---:|
| `PIL-MOH-033-001` | `SRC-MOH-033-001` | Human Resources Management and Development | Business laptops | 100 Each | KES 20,000,000.00 |
| `PIL-MOH-033-002` | `SRC-MOH-033-002` | Digital Health | Business laptops | 150 Each | KES 30,000,000.00 |

### 13.3 REQ-DES-01 — Requisitions workspace

Title **Procurement Requisitions**. Subtitle **Prepare precise departmental requests from approved Plan Items.**

**Ready to prepare** — one prominent headline-plus-button card, in the same style as PLN-DES-01 and PLN-DES-14's summary cards, not a generic table with column headers:

- Headline: **1 Plan Item ready to prepare**
- Requirement: **Clinical training and deployment laptops for digital health rollout**
- Departments: **Digital Health, HR Management and Development**
- Value: **KES 50,000,000.00**
- Right-aligned primary button: **Prepare Requisition**

This card is absent — not shown empty — when nothing is currently eligible. Where more than one Plan Item is eligible, each is its own row in the same card, never a table.

**Your Requisitions** — one connected list beneath the card, retitled from the earlier "My Drafts" / "Tasks" / "Recent Requisitions" split, since those were three disconnected sections describing one thing: the Requisitions this user has a stake in, at whatever stage:

| Requisition | Plan Item | Status | Action |
|---|---|---|---|
| `REQ-MOH-2027-033-001` | Clinical training and deployment laptops for digital health rollout | Draft | Continue |

Below the list: **1 Requisition**. When a Requisition is awaiting this user's decision specifically, its row's status is the decision itself — **Awaiting your approval** — not a separate "Tasks" section pointing back at the same record.

Do not show a value dashboard, STD Library link, Procuring Entity selector, or create-without-Plan-Item action.

### 13.4 REQ-DES-02 — Start IT-equipment Requisition

Title **Prepare Requisition from approved Plan Item**.

Read-only source panel:

- Plan Item, contributing departments, procurement method, planned completion and planned value from section 13.2;
- Strategic Objective and its full path — this is the policy justification a department is drawing against, shown here so it is visible before any drawdown decision is made, not only discoverable later by an auditor;
- plan horizon, shown as a quiet line: **Single year** — or, for a Multi-year Plan Item, **Multi-year · {justification}**, with an explanatory note: **The value above is this Plan Item's full multi-year allocation, not one year's worth.**;
- business need and expected operational result;
- the two Planning allocation rows with remaining quantity/value, one per contributing department.

Product panel:

- **Requirement product** — read-only **IT Equipment**;
- help: **This release supports straightforward off-the-shelf IT equipment. Complex software, integration or migration is not supported.**

Notice, shown only because this Plan Item has more than one contributing department: **This Requisition draws from two departments because Planning combined their Needs into one Plan Item. Digital Health, as the larger contributor, certifies the departmental submission.**

Actions: **Cancel** and **Prepare Requisition**. No template, STD or profile selector.

### 13.5 REQ-DES-03 — Step 1: Request and drawdown

Left navigation:

1. **Request and drawdown** — In progress
2. **Equipment items** — Not started
3. **Technical and support** — Not started
4. **Services and acceptance** — Not started
5. **Review and submit** — 8 blockers

Read-only context cards show Business need, Expected operational result, Method and Planned completion.

Editable controls:

| Label | Control | Fixture value |
|---|---|---|
| Requirement title | Single-line text, 160 characters | Clinical training and deployment laptops for digital health rollout |
| Delivery location | Location Link | Ministry of Health Headquarters, Afya House, Nairobi |
| Latest delivery date | Date picker | 30 Sep 2027 |
| Related services required | Yes/No switch | No |

Drawdown table — two rows, one per contributing department, since this Plan Item is a cross-department combine per §2.1. Each row's quantity and value fields default to the full remaining balance shown beside them — the ordinary case is drawing everything available — with a quiet **Request full remaining balance** link restoring that default if the user has typed a partial amount:

| Contributing department | Source requirement | Remaining | Requested quantity | Remaining value | Requested value |
|---|---|---:|---:|---:|---:|
| Human Resources Management and Development | Business laptops | 100 Each | Integer `100` — defaulted | KES 20,000,000.00 | Currency `20,000,000.00` — defaulted |
| Digital Health | Business laptops | 150 Each | Integer `150` — defaulted | KES 30,000,000.00 | Currency `30,000,000.00` — defaulted |

A partial draw remains fully supported; the default only removes the need to retype the common case.

Footer: **Save draft** and **Continue to equipment items**.

### 13.6 REQ-DES-04 — Step 2: Equipment items

Step status: Request complete; Equipment in progress; Review has 6 blockers.

Item table — two rows, one per drawdown line, per §5.6: an item links to exactly one drawdown line, never several, so two departments requesting the same specification means two item rows, not one spanning both:

| Item | Planning source | Category | Quantity | Intended use | Delivery |
|---|---|---:|---|---|---|
| Business laptops | `SRC-MOH-033-001` | Laptop | 100 Each | Clinical training for Human Resources Management and Development staff | Nairobi · 30 Sep 2027 |
| Business laptops | `SRC-MOH-033-002` | Laptop | 150 Each | Field digital-health deployment for Digital Health staff | Nairobi · 30 Sep 2027 |

Both rows are the same equipment category and specification; only their Planning source, quantity and intended use differ. The eleven technical characteristics in §13.7 apply to both — each characteristic's `applies_to` is **All items**, so nothing is entered twice.

Button **Add equipment item** opens an exact dialog with:

- Planning source — required Link restricted to selected drawdown lines;
- Equipment category — required Select with section 5.6 choices;
- Item name — required single-line text;
- Quantity — required positive integer;
- Unit — read-only Each;
- Intended use — required textarea, maximum 500 characters;
- Delivery location — required Location Link; and
- Latest delivery date — required date.

Dialog actions: **Cancel** and **Add item**. Row menu: **Edit** and **Remove** only while Draft.

Footer: **Save draft** and **Continue to technical and support**.

### 13.6A Proposed baseline rows, immediately after adding an item

The moment either item row in §13.6 is added, before Step 3 is ever opened, the system proposes its category's baseline characteristics — per §6.4, this must be a visible confirm-or-remove moment, not something that silently arrives already confirmed. Show a notice banner on the item row: **3 baseline characteristics proposed for Business laptops.** Opening it shows:

| Characteristic | Comparison | Proposed value | Unit | Status |
|---|---|---|---|---|
| Electrical compatibility | Required | Yes | — | **Confirm** · Remove |
| New and unused equipment | Required | Yes | — | **Confirm** · Remove |
| Storage type | One of | NVMe SSD | — | **Confirm** · Remove |

Each row's **Confirm** button is primary; **Remove** is a quiet text action. A row not yet acted on shows the amber **Proposed** badge, not the green **Confirmed** badge used everywhere else in this document once a row is settled. Step 3 and Step 5 both block on any row still **Proposed** — this is where REQ-AC-011's requirement is actually visible to a user, not merely asserted in the domain model.

### 13.7 REQ-DES-05 — Step 3: Technical and support

Use tabs **All items** and **Business laptops** — both items in this fixture share one specification, so **All items** is the tab a user actually works in; the per-item tab exists for the case, not exercised here, where two items of the same category need different characteristics. This fixture has one equipment category across its two items — a deliberate simplification from the retired Kenya Bureau of Standards fixture's three categories (laptops, desktops, tablets), made when SEED-001 harmonized this scenario across every module. The full released catalogue in §6.3 still supports desktop and tablet rows; this fixture simply does not exercise them. A future isolated multi-item-type profile remains a legitimate addition to §16, not yet built.

For Business laptops show every characteristic the catalogue makes available to this category:

| Characteristic | Comparison | Required value | Unit | Status |
|---|---|---|---|---|
| Electrical compatibility | Required | Yes — suitable for Kenyan mains supply | — | Confirmed |
| New and unused equipment | Required | Yes | — | Confirmed |
| Memory | Minimum | Integer `16` | GB | Confirmed |
| Storage capacity | Minimum | Integer `512` | GB | Confirmed |
| Storage type | One of | Select `NVMe SSD` | — | Confirmed |
| Display size | Minimum | Decimal `14.0` | inches | Confirmed |
| Battery runtime | Minimum | Decimal `8` | hours | Confirmed |
| Processor requirement | Minimum | `64-bit business-class processor, minimum 10 cores or equivalent benchmark` | — | Confirmed |
| Operating-system compatibility | Required | `Approved organisational Windows environment` | — | Confirmed |
| Network connectivity | One of | `Wi-Fi 6`, `Bluetooth 5 or later` | — | Confirmed |
| Required ports | Required | `USB-C` ×2, `USB-A` ×2, `HDMI` ×1 | — | Confirmed |

Button **Add characteristic** opens:

- Applies to — required Item/All items Link;
- Characteristic — required applicable Select;
- Comparison — derived read-only;
- Required value — derived typed control;
- Unit — derived read-only;
- Reason — conditional for Other essential characteristic.

Warranty and support panel:

| Label | Control | Fixture value |
|---|---|---|
| Minimum warranty | Integer with months suffix | 36 |
| On-site support required | Yes/No | Yes |
| Maximum support response | Integer with hours suffix | 8 |
| Manufacturer support required | Yes/No | Yes |
| Service location constraint | Select | Within Kenya |
| Support description | Textarea, maximum 500 | Supplier to provide escalation and warranty-contact details. |

Footer: **Save draft** and **Continue to services and acceptance**.

### 13.8 REQ-DES-06 — Step 4: Services and acceptance

Related services required is No for this fixture; the related-services table is absent. A future isolated profile with related services remains available for whichever product pattern needs to exercise that path — TPR-CHG-001's own fixture already carries zero related-service rows for consistency with this one.

Acceptance table:

| Check | Applies to | Pass condition | Evidence |
|---|---|---|---|
| Quantity | All items | Delivered quantities equal the authorised schedule | Inspection record |
| Physical condition | All items | No visible damage and all listed accessories are present | Inspection record |
| Required specification | All items | Every delivered unit complies with all mandatory technical rows | Inspection record |
| Functional test | All items | Each device powers on and completes the agreed basic functional test | Test result |
| Documents received | All items | Warranty and delivery documents are received and verified | Certificate |

Supporting materials panel shows no rows for this fixture — the retired Kenya Bureau of Standards fixture's one informational room-layout material is not carried forward, since Ministry of Health Headquarters delivery has no equivalent room-layout document in this scenario. Button **Add supporting material** still opens the exact controls in section 5.10 when a future Requisition needs one.

Footer: **Save draft** and **Continue to review**.

### 13.9 REQ-DES-07 — Step 5: Review and submit

Top result: green **Ready for departmental submission**; **0 Blocking · 1 Warning**.

Summary cards — compact by design, since the complete printable preview immediately below carries the full detail; each card still names what it counts, not a bare number:

- Planning drawdown — 2 source lines, 250 Each total, KES 50,000,000.00 total;
- Equipment — 2 items: Business laptops;
- Technical requirements — 11 confirmed characteristics for Business laptops;
- Related services — none requested;
- Acceptance — 5 checks defined;
- Supporting materials — none.

Warning row: **Delivery date is the same as the latest approved Plan completion date.**

Show the complete printable Requisition preview beneath the summary. It includes every inherited fact and structured row, not only totals.

For a Departmental Author, footer actions are **Back**, **Save draft** and **Send for department approval**.

For a Head of User Department preparing directly, replace the last action with **Submit to Procurement**.

### 13.10 REQ-DES-08 — Department approval task

Status **Awaiting Department Approval**. Header identifies Author **Grace Wanjiku**, Departmental Author.

Show the complete immutable Version from REQ-DES-07, including Planning allocations from both contributing departments, both items, all 11 technical rows, acceptance rows, validation and digest.

Decision statement:

> I confirm that this Requisition states the departments' operational need and minimum requirements and may be submitted to Procurement.

Footer: **Return for correction** and **Submit to Procurement**. No edit control. Fixture context: Dr Peter Kimani, Head of User Department for Digital Health — the lead department, certifying on behalf of both contributing departments per §7.3.

### 13.11 REQ-DES-09 — Procurement authorisation task

Status **Submitted to Procurement**. Show:

- the same complete immutable Version;
- fresh Planning availability: **Eligible · KES 50,000,000.00 and 250 Each remain available**;
- fresh Budget affordability: **`MOH-BL-HWD-2027` — KES 50,000,000.00 requested against KES 60,000,000.00 approved and fully available**;
- suitability — every row of §5A's compatibility test, shown as its own row, not collapsed into one line:

  | Test | Result |
  |---|---|
  | Procurement category | Goods |
  | Requirement type | Straightforward off-the-shelf IT equipment |
  | Reservation category | None |
  | Lotting indicator | Single lot |
  | Currency | KES |
  | Award package | One |
- policy justification: **OBJ-MOH-2023-001 — Strengthen interoperable national digital health services**;
- validation: **0 Blocking · 1 Warning**; and
- Head of User Department submission: **Submitted by Dr Peter Kimani · 8 Mar 2027, 09:00 EAT**.

Where more than one department contributed, a quiet line above the decision statement reads: **Lead department: Digital Health.** with a text action **Change lead department** — visible only to the Head of Procurement Function, only before submission to Procurement is possible from this screen's own state. Selecting it opens a dialog: title **Change lead department?**, a Select restricted to the Plan Item's contributing departments, a required reason (20–500 characters), and buttons **Cancel** and **Confirm change**. This is the only place `lead_org_unit_id` can change, per §5.1, and it is never available after submission.

Decision statement:

> I authorise this complete Requisition for Tender Preparation and commit its stated Planning drawdown and Budget reservation.

Footer: **Return to department** and **Authorise for Tender Preparation**. No edit, evidence-builder or template selector. Fixture context: Charles Mutiso, Head of Procurement Function.

### 13.12 REQ-DES-10 — Authorised Requisition

Status **Authorised for Tender Preparation**.

Show:

- Requisition and handoff references;
- authorised Version and digest;
- Planning drawdown reference and exact source lines;
- both Budget reservations — `RSV-MOH-2027-033-001` (KES 20,000,000.00, Human Resources Management and Development's line) and `RSV-MOH-2027-033-002` (KES 30,000,000.00, Digital Health's line), both against `MOH-BL-HWD-2027`;
- the complete structured package, read-only, laid out exactly as below — not a count card. "2 items" and "11 rows" are not a screen; they were never specified as one, and the absence of a specification is what let an implementation invent them:

**Equipment items** — the same two rows as §13.6, unchanged:

| Item | Planning source | Category | Quantity | Intended use | Delivery |
|---|---|---:|---|---|---|
| Business laptops | `SRC-MOH-033-001` | Laptop | 100 Each | Clinical training for Human Resources Management and Development staff | Nairobi · 30 Sep 2027 |
| Business laptops | `SRC-MOH-033-002` | Laptop | 150 Each | Field digital-health deployment for Digital Health staff | Nairobi · 30 Sep 2027 |

**Technical requirements** — the same eleven confirmed rows as §13.7, unchanged, applying to both items:

| Characteristic | Comparison | Required value | Unit | Status |
|---|---|---|---|---|
| Electrical compatibility | Required | Yes — suitable for Kenyan mains supply | — | Confirmed |
| New and unused equipment | Required | Yes | — | Confirmed |
| Memory | Minimum | 16 | GB | Confirmed |
| Storage capacity | Minimum | 512 | GB | Confirmed |
| Storage type | One of | NVMe SSD | — | Confirmed |
| Display size | Minimum | 14.0 | inches | Confirmed |
| Battery runtime | Minimum | 8 | hours | Confirmed |
| Processor requirement | Minimum | 64-bit business-class processor, minimum 10 cores or equivalent benchmark | — | Confirmed |
| Operating-system compatibility | Required | Approved organisational Windows environment | — | Confirmed |
| Network connectivity | One of | Wi-Fi 6, Bluetooth 5 or later | — | Confirmed |
| Required ports | Required | USB-C ×2, USB-A ×2, HDMI ×1 | — | Confirmed |

**Warranty and support** — from §13.7, unchanged:

| Field | Value |
|---|---|
| Minimum warranty | 36 months |
| On-site support required | Yes |
| Maximum support response | 8 hours |
| Manufacturer support required | Yes |
| Service location constraint | Within Kenya |
| Support description | Supplier to provide escalation and warranty-contact details. |

**Related services** — No related services requested.

**Acceptance requirements** — the same five rows as §13.8, unchanged:

| Check | Applies to | Pass condition | Evidence |
|---|---|---|---|
| Quantity | All items | Delivered quantities equal the authorised schedule | Inspection record |
| Physical condition | All items | No visible damage and all listed accessories are present | Inspection record |
| Required specification | All items | Every delivered unit complies with all mandatory technical rows | Inspection record |
| Functional test | All items | Each device powers on and completes the agreed basic functional test | Test result |
| Documents received | All items | Warranty and delivery documents are received and verified | Certificate |

**Supporting materials** — No supporting materials.

Also show:

- decision evidence;
- Tender status **Not yet consumed**; and
- one available action for authorised downstream users: **Open Tender Preparation**.

The action deep-links to Tender Preparation; it does not create a Tender from a read. The actual Tender is created only by Tender Preparation's explicit command.

When consumed, replace status with **Consumed by TND-MOH-2027-033 · IT Equipment — Open Tender v1.1**. Hide revocation action after consumption.

### 13.13 Decision dialogs and common states

Return dialog:

- title **Return Requisition for correction?**;
- textarea label **Correction required**;
- 20–1,000 characters;
- buttons **Cancel** and **Return**.

Authorisation dialog:

- title **Authorise Requisition?**;
- exact totals **250 Each · KES 50,000,000.00**;
- statement **This commits the Planning drawdown, reserves the requested value against MOH-BL-HWD-2027, and creates the immutable Tender Preparation handoff.**;
- buttons **Cancel** and **Authorise**.

Revocation dialog:

- title **Revoke unconsumed authorisation?**;
- required reason 20–1,000 characters;
- statement **The Planning drawdown and both Budget reservations will be reversed. The authorised Version remains in history.**;
- buttons **Cancel** and **Revoke authorisation**.

**Request upstream correction** requires **Reason**, fixture: **The Plan Item's authorised warranty period does not match what the department actually needs; this must be corrected in Planning.** Notice: **Requisitions cannot edit an approved Planning fact. This Requisition Version will be preserved.**

Common states:

- loading uses the shared KenTender skeleton;
- empty states state what is absent and never offer unauthorised creation;
- a record outside the actor's authority and a genuinely nonexistent record both show **Requisition not found**, per AUTH-ADR-001 v1.7's non-disclosure rule; and
- no page displays technical identifiers as editable controls.

The exact wording for Forbidden, stale writes, load failure, unsupported product and the other named states is the table below — do not restate it differently in implementation.

| State | Message | Action |
|---|---|---|
| No eligible Plan Items | No Active Plan Items are ready for Requisition. | None |
| Product unsupported | This Plan Item is not supported by the IT-equipment Requisition pattern. | Return to workspace |
| Open Requisition exists | This Plan Item already has an open Requisition. | Open it, if authorised |
| Forbidden | You do not have access to Procurement Requisitions. This area needs one of these responsibilities: Departmental Author, Head of User Department, Head of Procurement Function or Auditor. Ask your KenTender administrator to assign one in System setup. | None |
| Stale write | Another user changed this Requisition. Reload before continuing. | Reload |
| Load failure | Procurement Requisitions could not be loaded. | Try again |

## 14. Functional interaction requirements

**Restored in full in v1.4**, alongside the cross-department and Budget-transaction additions v1.3 introduced. Common page behaviour and accessibility follow KT-STD-001 §3 and §3A.

### 14.1 Workspace and preparation

- Workspace reads are side-effect free.
- **Prepare Requisition** rechecks eligibility and creates or reuses the one open Draft.
- Browser Back, refresh and repeated commands do not create duplicates.
- Opening a protected task requires the exact open task and current scope.
- The workspace resolves eligible Plan Items and own Drafts using the registered predicate for the actor's exact Organisation Unit assignment(s).
- Where a Plan Item is a cross-department combine, it appears once for each contributing department's Departmental Author, not duplicated as unrelated rows.

### 14.2 Editor

- Save validates only the current edit plus cross-row invariants affected by it.
- Continue saves the current step and moves only when its blockers are zero.
- Row dialogs derive control type, comparison, unit and options from typed server metadata for the code-owned catalogue.
- Changing an equipment category revalidates its characteristics and blocks removal of incompatible rows until the user resolves them.
- Removing an item is blocked while linked technical, service, acceptance or file rows remain.
- Turning related services to No requires explicit confirmation and removes no rows silently.
- Autosave is not required. Explicit Save draft is authoritative.
- Two drawdown rows render distinctly by contributing department; a user without an assignment for one contributing department can view but not edit that row.
- Item, technical, service and acceptance rows validate against the released catalogue server-side, matching client validation exactly.
- Adding an item proposes its category's baseline characteristics immediately, each rendered **Proposed** until the Departmental Author confirms or removes it; a **Proposed** row blocks Step 3 and Step 5 completion.
- A drawdown line's requested quantity and value default to its remaining balance; the **Request full remaining balance** link resets a manually-edited value back to that default.

### 14.3 Submission and decisions

- Submission locks the exact Version and package before creating a task.
- Task screens show the complete immutable content; summary-only approval is prohibited.
- A return creates a copied Draft successor only after the decision commits.
- Authorisation reruns validation and Planning availability under lock.
- Double-clicks and retries return the first successful result.
- Notifications are outbox effects, not part of authority.
- **Change lead department** is visible only to the Head of Procurement Function, only on the authorisation task, only before the authorisation decision itself, and requires a reason.
- **Send for department approval** and **Submit to Procurement** are visible only to their exact authorised actor, per §7 and §8.
- Authorisation is a single atomic transaction: Planning drawdown, Budget reservation per line, decision, handoff and outbox event commit together or none commit, and the UI shows one pending state throughout, not a sequence of partial confirmations.
- **Request upstream correction** opens the dialog in §13.13 and, on confirmation, transitions the Version to `Upstream correction required` per §7.4A.

### 14.4 Accessibility and page lifecycle

- Every control has a visible label and error text associated programmatically.
- Keyboard users can complete tables, dialogs and steps.
- Focus moves to the first invalid field after validation.
- Status is not conveyed by colour alone.
- Unsaved changes prompt before leaving the editor.
- Pages clean up listeners and abort stale requests on unmount.
- The authorisation verdict for every page resolves before any content renders; a denied actor sees the inline Forbidden state, never a modal.
- Direct routes, lists, files and commands enforce the same registered predicate as the UI.

## 15. Audit and history

Audit shall record:

- explicit Draft creation and every successful write;
- Planning projection identity and evaluation time used;
- old and new values for each Draft change;
- item, requirement, service, acceptance and material row identities;
- file scan, digest and linked-row result;
- each validation snapshot and finding set used for a lifecycle action;
- content and handoff digests;
- submission, return, authorisation, withdrawal and revocation decisions;
- Planning drawdown and reversal references;
- **Budget reservation creation and reversal, per line**;
- upstream-correction requests and their resolution;
- outbox publication and retry evidence; and
- Tender handoff consumption.

Audit records contain actor, business role, the exercised responsibility assignment ID, server time, request ID and idempotency key. There is no Procuring Entity or Fiscal Year scope on any record, because neither participates in authorization here. Audit payloads do not store authentication secrets or duplicate uploaded file bytes, and do not expose confidential internal values or private file contents to unauthorised users.

Submitted, returned, authorised, withdrawn, revoked and superseded Versions cannot be edited or deleted through product commands.

## 16. Deterministic Ministry of Health seed

**Restored to full original depth in v1.4**, renamed from Kenya Bureau of Standards and adapted to the harmonized two-department, one-item-type scenario.

### 16.1 Prerequisites and actors

| Fixture | Exact value |
|---|---|
| Site | `PE-MOH` · FY 2027/28 · Active |
| Lead department | `OU-MOH-DHI` — Digital Health |
| Contributing department | `OU-MOH-HRMD` — HR Management and Development |
| Departmental Author | Grace Wanjiku · `grace.wanjiku@moh.example.test` |
| Head of User Department | Dr Peter Kimani · `peter.kimani@moh.example.test` |
| Head of Procurement Function | Charles Mutiso · `charles.mutiso@moh.example.test` |
| Auditor | Naomi Chebet · `naomi.chebet@moh.example.test` |

Each user receives only the role-bound `User Responsibility Assignment`s required by section 8 — no Frappe User Permission, no bespoke capability grant. No new actor beyond KT-STD-001 §8.3's existing register is required.

Configuration prerequisites: ERPNext Fiscal Year `2027-2028`; `OU-MOH-HRMD` and `OU-MOH-DHI`; ERPNext `UOM` **Each**, enabled; `MOH-BL-HWD-2027`, approved KES 60,000,000, fully available before this seed runs.

### 16.2 Planning projection

Seed the exact Plan Item, two allocations and values in section 13.2 as an Active, funded and Requisition-eligible projection. No Requisition seed writes Planning or Budget tables directly — every position change happens through the commands in §9.1 and §9.1A.

### 16.3 Complete package

Seed both equipment items, technical rows, warranty/support values and acceptance checks in sections 13.6–13.8.

The complete technical fixture has these 11 confirmed rows:

| ID | Applies to | Characteristic | Required value |
|---|---|---|---|
| `TECH-001` | All items | Electrical compatibility | Yes — suitable for Kenyan mains supply |
| `TECH-002` | All items | New and unused equipment | Yes |
| `TECH-003` | Business laptops | Memory | Minimum 16 GB |
| `TECH-004` | Business laptops | Storage capacity | Minimum 512 GB |
| `TECH-005` | Business laptops | Storage type | NVMe SSD |
| `TECH-006` | Business laptops | Display size | Minimum 14.0 inches |
| `TECH-007` | Business laptops | Battery runtime | Minimum 8 hours |
| `TECH-008` | Business laptops | Processor requirement | 64-bit business-class processor, minimum 10 cores or equivalent benchmark |
| `TECH-009` | Business laptops | Operating-system compatibility | Approved organisational Windows environment |
| `TECH-010` | Business laptops | Network connectivity | Wi-Fi 6 and Bluetooth 5 or later |
| `TECH-011` | Business laptops | Required ports | USB-C ×2, USB-A ×2, HDMI ×1 |

Package-level warranty remains 36 months and is carried once into the handoff and Tender. It is not duplicated as an editable technical row.

Fewer rows than the retired Kenya Bureau of Standards fixture's 19, because that fixture spanned three item types (laptops, desktops, tablets) and this one spans one, per SEED-001's harmonization. The full 24-row catalogue in §6.3 is unchanged and available to any future fixture that needs desktop or tablet rows.

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
| Five steps completed | Grace Wanjiku | 1 Mar 2027, 11:00 EAT |
| Sent for department approval | Grace Wanjiku | 1 Mar 2027, 11:05 EAT |
| Submitted to Procurement | Dr Peter Kimani | 8 Mar 2027, 09:00 EAT |
| Authorised | Charles Mutiso | 15 Mar 2027, 10:00 EAT — creates `RSV-MOH-2027-033-001` (KES 20,000,000, HRMD line) and `RSV-MOH-2027-033-002` (KES 30,000,000, DHI line) against `MOH-BL-HWD-2027`, and the handoff `REQ-MOH-2027-033-001` |
| Handoff consumed (fixture 6 only) | TPR-CHG-001's `PrepareTender` | 20 Mar 2027, 09:00 EAT |

Fixtures use distinct Requisition references so lifecycle states do not overwrite each other.

The seed also contains one stopped Requisition Version that requested an upstream correction and one Planning-side `PlanItemCorrectionRequest`, proving §7.4A's route without depending on PLN-CHG-001's own inbound handling, which is not yet built.

### 16.5 Seed rules

- Upsert by stable IDs; rerun creates no duplicates.
- Validate site, Fiscal Year, Organisation Unit and Planning prerequisites before seeding.
- Never grant Administrator a business decision by implication.
- Never use production emails or attachments.
- Never create an STD manifest, profile or template-selection record.
- Seeds call the same commands as the UI, including the Budget calls in §9.1A, and never write DocTypes directly.
- Print a concise created/reused/failed report.

## 17. Acceptance contract

**Restored to the original's full 38 criteria in v1.4**, renumbered continuously, with 15 new criteria appended for the genuinely new mechanisms this revision adds. v1.3 had replaced most of the original 38 with 18 that mostly covered only the new material — an error, corrected here.

| ID | Required result |
|---|---|
| REQ-AC-001 | Starting from the eligible Ministry of Health Plan Item creates or reuses one Draft Requisition. |
| REQ-AC-002 | A page read creates no record or task. |
| REQ-AC-003 | Planning and inherited departmental facts are read-only. |
| REQ-AC-004 | The Draft contains one fixed IT Equipment package without profile or schema selection. |
| REQ-AC-005 | Every drawdown line preserves `source_line_id` and `plan_item_line_id`. |
| REQ-AC-006 | Requested quantity/value cannot exceed current Planning availability. |
| REQ-AC-007 | Every item links to one selected Planning allocation. |
| REQ-AC-008 | Item quantities reconcile exactly to requested source quantities. |
| REQ-AC-009 | Only category-applicable characteristics and their released controls are accepted. |
| REQ-AC-010 | Unknown Select values and free-text substitutes are rejected server-side. |
| REQ-AC-011 | Proposed baseline rows require visible confirmation. |
| REQ-AC-012 | Warranty and conditional support fields enforce their ranges and visibility. |
| REQ-AC-013 | Complex software, integration or migration produces a Blocking unsupported-product finding. |
| REQ-AC-014 | At least one observable acceptance row is required. |
| REQ-AC-015 | "Satisfactory" alone is rejected as a pass condition. |
| REQ-AC-016 | A supporting file cannot create an unstructured obligation. |
| REQ-AC-017 | An operative file links to at least one structured requirement and retains a digest. |
| REQ-AC-018 | Brand/restrictive wording without permitted equivalence treatment blocks submission. |
| REQ-AC-019 | A Departmental Author routes one complete locked Version to the HoD. |
| REQ-AC-020 | A Head of User Department sees the complete Version and may return or submit it. |
| REQ-AC-021 | A HoD preparing directly may submit without an invented departmental-review task. |
| REQ-AC-022 | The Head of Procurement Function sees the complete Version, fresh Planning availability and fresh Budget affordability. |
| REQ-AC-023 | No technical reviewer, Finance approver, Accounting Officer or committee stage exists in the Requisition chain. |
| REQ-AC-024 | Procurement return creates a copied Draft successor and preserves the submitted Version. |
| REQ-AC-025 | Authorisation commits decision, all Planning drawdowns, **every Budget reservation**, handoff and outbox event atomically. |
| REQ-AC-026 | Failed authorisation creates none of those effects. |
| REQ-AC-027 | The handoff contains all inherited facts and every structured row with stable IDs. |
| REQ-AC-028 | Authorisation creates no Tender and binds no Tender template. |
| REQ-AC-029 | Tender Preparation can consume the handoff once and retain every identifier. |
| REQ-AC-030 | Revocation before consumption reverses the exact drawdown **and every Budget reservation** once and preserves evidence. |
| REQ-AC-031 | Revocation after consumption is blocked. |
| REQ-AC-032 | Role-bound `User Responsibility Assignment`, resolved through the registered permission hooks, protects rows, counts, routes, files and commands consistently — not native Frappe roles or User Permission. |
| REQ-AC-033 | An acting HoD uses a time-bound assignment; no delegate role or second permission system exists. |
| REQ-AC-034 | The complete Ministry of Health package renders with zero missing values or anonymous requirement text. |
| REQ-AC-035 | Repeated seed and command execution remains idempotent. |
| REQ-AC-036 | No STD Configuration, manifest, composer profile or generic schema object exists. |
| REQ-AC-037 | No attachment-only specification can reach authorisation. |
| REQ-AC-038 | TPR compatibility receives structured items, technical rows, services and acceptance rows rather than one primary specification PDF — confirmed against TPR-CHG-001 v0.7, not merely asserted as a future requirement. |
| REQ-AC-039 | A drawdown line's Organisation Unit must be among the Plan Item's contributing departments; any other value is rejected with `REQ_DEPARTMENT_NOT_CONTRIBUTING`. |
| REQ-AC-040 | A `check_funding` failure for any line blocks the entire authorisation, naming the exact line and shortfall, with `REQ_FUNDING_UNAVAILABLE`. |
| REQ-AC-041 | Every authorised Requisition's Budget position change is visible in BUD-CHG-001's own reservation records, matching this module's reservation IDs exactly. |
| REQ-AC-042 | No command, role or API path accepts a `pe_fy_context_id` or any Procuring Entity/Fiscal Year scope argument, tested against every role including Administrator and System Manager. |
| REQ-AC-043 | Reservation category and lotting indicator are read-only throughout, and an unsupported value is rejected at product-suitability check with `REQ_PRODUCT_UNSUPPORTED`. |
| REQ-AC-044 | Requesting upstream correction preserves the current Version exactly, transitions it to `Upstream correction required`, and creates one `PlanItemCorrectionRequest`. |
| REQ-AC-045 | The Head of Procurement Function preparing a Requisition directly cannot also authorise it, checked against a user holding both responsibilities. |
| REQ-AC-046 | Every field in this document passes the field-purpose rule in §2.2; no field exists without a stated decision, control and downstream effect. |
| REQ-AC-047 | The lead department's Head of User Department certifies on behalf of every contributing department in one submission, never one certification per department. |
| REQ-AC-048 | An item links to exactly one drawdown line; a Requisition with two contributing departments and one shared specification produces two item rows, never one row spanning two lines. |
| REQ-AC-049 | A proposed baseline characteristic renders as **Proposed**, distinct from **Confirmed**, and blocks Step 3 and Step 5 completion until confirmed or removed. |
| REQ-AC-050 | Only the Head of Procurement Function can change `lead_org_unit_id`, only at authorisation review, only with a reason, and never after authorisation. |
| REQ-AC-051 | Each drawdown line's requested quantity and value default to its full remaining balance; a user may still enter a smaller amount. |
| REQ-AC-052 | A Plan Item whose `procurement_category` is not `Goods` is rejected at `PrepareITEquipmentRequisition`, before any Draft is created, with `REQ_PRODUCT_UNSUPPORTED`. |
| REQ-AC-053 | Every row in §5A's compatibility test is independently checked and independently named on failure; no test is folded into a single generic suitability flag. |
| REQ-AC-054 | The Strategic Objective and its full path are visible on the start dialog, both decision tasks, and the authorised handoff, traceable without a second query into Planning. |
| REQ-AC-055 | Plan horizon and, where Multi-year, its justification are inherited and displayed; no compatibility test blocks on this field. |
| REQ-AC-056 | PLN-CHG-001's `RequisitionEligibilityProjection` contract explicitly lists every field this document depends on; a field this Requisition document uses that PLN-CHG-001 does not enumerate is a defect in one of the two documents, not an assumption either may carry silently. |

## 18. Test and smoke contract

**Restored to full original depth in v1.4**, with the Budget-contract and cross-department layers v1.3 added kept alongside every original layer and journey.

### 18.1 Focused automated layers

1. Pure tests for ranges, options, category applicability, quantity reconciliation, date rules, objective acceptance wording, and reservation/lotting compatibility.
2. Domain tests for Version locking, correction copies, maker-checker, drawdown, cross-department contribution validation, and handoff invariants.
3. Responsibility tests for every role, scope, list, count, direct route and File, tested against Administrator and System Manager explicitly.
4. Database tests for uniqueness, optimistic concurrency, atomic authorisation, reversal and idempotency.
5. Budget-contract tests for `check_funding` success, failure and rollback, and for reservation reversal on revocation.
6. Contract tests against `GetRequisitionEligiblePlanItem` and the current Tender handoff shape TPR-CHG-001 v0.7 consumes.
7. Vue component tests for control types, conditional fields, read-only presentation, row dependencies and decision dialogs.
8. Browser smoke using the Ministry of Health fixtures.

### 18.2 Named smoke journeys

**REQ-SMK-01 — Happy path**

Departmental Author prepares the Ministry of Health Draft across two contributing departments, completes five steps, HoD submits, Head of Procurement Function authorises, Planning drawdown and both Budget reservations are visible, and Tender Preparation reads the handoff.

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

Requesting upstream correction preserves the Version as `Upstream correction required` and creates one `PlanItemCorrectionRequest`.

### 18.3 Required release evidence

- migration/build output;
- focused unit, domain, responsibility, database, Budget-contract and contract-test results;
- screenshots for REQ-DES-01 through REQ-DES-10 at 1440 × 1024;
- scripted Ministry of Health happy-path and return-path walkthroughs;
- exact generated handoff fixture and digest;
- proof of all-or-none Planning drawdown and Budget reservation, together;
- zero page-specific console errors or failed network requests; and
- search evidence showing no manifest, composer-profile, capability-profile, attachment-primary compatibility path, or Frappe User Permission read.

## 19. Implementation constraints

- Implement in `kentender_procurement` with ordinary Frappe records, the registered AUTH-ADR-001 v1.7 permission hooks, private Files, transactions and audit.
- Register Departmental Author and Head of User Department with `scope_type = Organisation Unit`; register Head of Procurement Function, Procurement Planner, Procurement Officer and Auditor with `scope_type = Site-wide`, per AUTH-ADR-001 v1.7 §4.4.
- Call Budget's `check_funding` and `reserve_funding` exactly as BUD-CHG-001 §8.2A specifies; do not reimplement reservation locking locally.
- Keep the reviewed IT Equipment package under version control matching the owning Requisition Version.
- Do not use parser/OCR, inferred-schema logic, or a compatibility layer for the retired PE/FY scope model.

## 20. Existing data and cutover

- v1.0–v1.2 Drafts and fixtures keyed to Kenya Bureau of Standards or `pe_fy_context_id` are not migrated into this model.
- Recreate the deterministic Ministry of Health Requisition from Plan Item `PPI-MOH-2027-033`.
- No production Requisition is authorised until the AUTH-ADR-001 v1.7 registration and the Budget-contract suite both pass.

## 21. E2E-REQ-001 conformance

v1.2 asserted conformance with **E2E-REQ-001 v0.2 — Approved**, for the structured Departmental Needs → Planning → Requisition → Tender control contract. That document has not been supplied in this review and its current content has not been re-verified against the corrections in this version. This section is carried forward as an open item, not a confirmed conformance claim: before this document is treated as fully aligned, E2E-REQ-001 should be obtained and checked against the cross-department relaxation in §2.1 and the Budget reservation addition in §9.1A, either of which it may also govern.

## 22. Traceability and precedence

This document conforms to:

1. **KT-STD-001 v1.4** for document structure, shared fixtures, page-state rules and universal prohibitions;
2. **STD-STD-001 v1.1** for the three-layer separation and the parameter rule this package's field-purpose rule already embodied independently;
3. **AUTH-ADR-001 v1.7** for role-bound responsibility assignment and the registered permission hooks that replace this module's former native-Frappe-Role/User-Permission model;
4. **CFG-CHG-002 v0.9** for the implicit site Procuring Entity and the ERPNext Fiscal Year this module reads but never scopes by;
5. **PLN-CHG-001 v1.15** for the eligible Plan Item, its combine rule, and the `PlanItemCorrectionRequest` this document's §7.4A now depends on as a required correction there;
6. **BUD-CHG-001 v1.7** for the `check_funding`/`reserve_funding` contracts this module now actually calls;
7. **TPR-CHG-001 v0.7** for the corrected handoff consumer; and
8. **SEED-001 v1.2** for the exact harmonized identifiers this document's fixture uses.

**Required correction in another document.** PLN-CHG-001 needs an inbound handler for `PlanItemCorrectionRequest`, visible as a Procurement Planner task, per §7.4A and §9.1. Until it exists, the upstream-correction route in this document ends at a request Planning has no designed way to receive.

**Not yet resolved.** E2E-REQ-001's actual current content, per §21.

## 23. Approval effect

REQ-CHG-001 v1.7 is approved. It supersedes v1.6, v1.5, v1.4, v1.3 (withdrawn) and v1.2 (approved 28 August 2026) and all earlier versions in full and is the Procurement Requisitions requirements document. v1.6 was itself approved on 4 September 2026; this domain correction superseded that approval.

Approval authorises the §13.12, §13.11, §13.9 and §13.3 display corrections in this version — no domain model, lifecycle, role, command or error contract changes; every corrected screen renders data this document already defined elsewhere, laid out for the first time rather than left to be invented.

This approval also authorises everything v1.6 introduced — removal of `pe_fy_context_id` and the native-Frappe-Role/User-Permission model; the Budget reservation call in §9.1A, closing the gap that has existed since BUD-CHG-001 v1.4; the narrow cross-department relaxation in §2.1, scoped exactly to a Plan Item Planning itself combined; the upstream-correction mechanism in §7.4A; reservation-category and lotting carriage through the handoff; the Ministry of Health fixture; the compatibility test in §5A; the `procurement_category`, Strategic Objective and `plan_horizon` fields added to §5.1 and carried into the handoff, artboards and decision tasks; and the matching correction to PLN-CHG-001's `RequisitionEligibilityProjection`.

This approval does not resolve the required correction to PLN-CHG-001 named in §22 — the `PlanItemCorrectionRequest` inbound handler — and does not confirm conformance with E2E-REQ-001, which remains unverified per §21. Both remain open.
