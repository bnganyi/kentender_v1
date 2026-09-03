# REQ-CHG-001 — Structured Procurement Requisitions

| Control | Value |
|---|---|
| Document ID | REQ-CHG-001 |
| Version | 1.2 |
| Date | 28 August 2026 |
| Status | Approved |
| Change type | Complete replacement for proposed v1.1 and successor to approved v1.0 |
| Module | Procurement Requisitions |
| First released product | Straightforward IT equipment |
| Implementation posture | Correct the module in place; no STD Configuration dependency and no attachment-first specification model |

**Controlling decision:** A Procurement Requisition turns one approved Planning allocation into one precise departmental request. For the first release, the department completes a fixed, code-owned IT Equipment Requirement Package. Structured items, technical requirements, services and acceptance checks are the authoritative requirements. Files may support those rows but cannot replace them.

## 1. Governing decision

This complete document is the only requirements document to consult for Procurement Requisitions. It supersedes approved REQ-CHG-001 v1.0 for new implementation work and withdraws the unapproved v1.1 draft.

The module shall not contain an STD selector, Requirements Composer Manifest, schema editor, mapping editor or generic requirements engine. Tender Preparation selects the released Tender template after Requisition authorisation.

Implementation must produce one coherent result across schema, services, permissions, screens, fixtures and tests. A field, action, state, role, screen or service not defined here is outside this release.

### 1.1 Corrected earlier directions

| Earlier direction | Treatment in v1.2 |
|---|---|
| Requisition binds to a Requirement Composer Manifest from STD Configuration | Remove. The first release uses the code-owned IT Equipment Requirement Package in section 6. |
| Department chooses a requirements profile | Remove. Starting an eligible IT-equipment Requisition opens the fixed form directly. |
| Generic requirement sections, schemas and mappings | Remove. Use the fixed records and controls in this document. |
| Information Technology Systems profile | Remove from this release. It covered complex systems, software and integration rather than straightforward equipment. |
| Technical specification PDF as the primary requirement | Remove. Structured rows are authoritative. A file may only support identified rows. |
| Procurement Officer recreates goods and technical requirements in Tender Preparation | Remove. Tender Preparation inherits them read-only. |
| HoD Delegate role | Remove. An acting HoD receives the same Head of User Department role and scoped native User Permission for the approved period. |
| Requisition Preparer and Requisition Auditor roles | Use the established Departmental Author and Auditor roles. Do not create module-specific aliases. |
| Custom Capability Profiles or Operational Scope Assignments | Remove. Use native Frappe Roles, Workflow permissions and User Permissions. |
| Separate requirements approval or technical-review workflow | Remove. Contributors may help the Author, but the only Requisition decisions are departmental submission and Procurement authorisation. |
| Attachment migration or automated extraction | Do not build. Existing files may inform manual Draft entry but do not become authoritative data. |

## 2. Purpose

Procurement Requisitions shall:

- start from one eligible Active Plan Item and its exact source allocations;
- show all approved Planning facts read-only;
- let the requesting department state the exact quantity and value being requested;
- capture a complete structured IT Equipment Requirement Package;
- preserve every Planning, item and requirement identifier;
- let the Head of User Department submit the departmental request;
- let the Head of Procurement Function authorise or return it;
- commit the Planning drawdown only on authorisation;
- create one immutable handoff for Tender Preparation; and
- provide clear correction routes without rewriting approved history.

### 2.1 First-release boundary

The first release supports:

- one PE, Financial Year and requesting department;
- one Active Plan Item per Requisition;
- one or more source allocations belonging to that department;
- straightforward off-the-shelf IT equipment;
- goods supplied in Kenya Shillings;
- one Requisition and one later award package;
- whole-number equipment quantities in `Each`;
- structured pass/fail technical requirements; and
- the released `IT-EQUIPMENT-OPEN-V1` Tender pattern.

It does not support:

- custom software, systems implementation, integration, migration or hosting;
- Works, consulting services or non-consulting services;
- multiple currencies, lots or award packages;
- cross-department Requisitions;
- a generic specification editor or rich-text Terms of Reference;
- supplier qualification, Tender security, evaluation criteria or contract clauses;
- bidder responses, prices, evidence or evaluation results;
- a second budget check or reservation; or
- Requisition approval levels beyond those in section 8.

### 2.2 Field-purpose rule

A stored field is permitted only when this document names:

1. the current decision or output using it;
2. its control, source and validation; and
3. its effect on validation, handoff, Tender output or contract obligation.

“Useful later”, “normally captured”, “helpful context” and “present in an old form” are not valid reasons. An undefined field is omitted.

## 3. Ownership and module boundary

| Information or action | Owner | Requisition treatment |
|---|---|---|
| Active Plan, Plan Item and source allocations | Procurement Planning | Read exact eligibility and remaining balances; never edit. |
| Need, description and expected operational result | Requesting department through Needs or Planning | Inherit read-only; return upstream if materially wrong. |
| Requested drawdown | Requesting department | State within remaining Planning quantity and value. |
| Equipment items and intended use | Requesting department | Create as structured rows linked to Planning sources. |
| Minimum technical characteristics | Requesting department | Create as structured rows using released controls. |
| Warranty, support, related services and acceptance | Requesting department | State the required operational result in fixed controls. |
| Budget Line, funding, planned method and schedule | Planning and Budget | Inherit read-only. Authorisation rechecks Planning availability. |
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

Descriptions are not identifiers. The system shall not reconstruct lineage by comparing text.

## 5. Canonical domain model

All identifiers, references, version numbers, digests, actors and timestamps are server-managed.

### 5.1 ProcurementRequisition

Stable root for one departmental request against one Active Plan Item.

| Field | Purpose and rule |
|---|---|
| `requisition_id` | Immutable internal identity. |
| `requisition_reference` | Generated `REQ-{PE}-{FY}-{OU}-{4 digits}`. |
| `pe_fy_context_id` | Exact authorised PE/FY context; immutable. |
| `requesting_org_unit_id` | Exact department owning every selected Planning source; immutable. |
| `plan_id` / `plan_version_id` / `plan_item_id` | Exact Active Planning baseline; immutable. |
| `current_version_id` | Current Draft, submitted or authorised Version. |
| `authorised_version_id` | Exact authorised Version; empty before authorisation. |
| `current_state` | Derived root state from section 7. |
| `planning_drawdown_reference` | Planning reference created only on authorisation. |
| `handoff_id` | Immutable downstream handoff; empty before authorisation. |
| `handoff_consumed_at` | Neutral downstream-consumption projection. |
| `record_version` | Optimistic-concurrency token. |

Only one open Requisition may exist for the same `plan_item_id + requesting_org_unit_id`.

### 5.2 RequisitionVersion

One complete decision snapshot.

| Field | Purpose and rule |
|---|---|
| `requisition_version_id` | Immutable Version identity. |
| `requisition_id` | Stable parent. |
| `version_number` | Generated sequence. |
| `based_on_version_id` | Returned or revoked Version copied for correction. |
| `version_status` | `Draft`, `Awaiting Department Approval`, `Submitted to Procurement`, `Returned`, `Authorised`, `Withdrawn`, `Revoked` or `Superseded`. |
| `requirement_title` | Required; 5–160 characters. Initially inherited from Planning and editable only while Draft. |
| `delivery_location_id` | Required Link to an Active PE Location. |
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
| `approved_quantity` / `approved_value` | Read-only Planning values. |
| `remaining_quantity` / `remaining_value` | Read-only evaluation-time values. |
| `requested_quantity` | Positive whole number, not above remaining quantity. |
| `requested_value` | Positive KES amount, not above remaining value. |
| `unit` | Read-only Planning unit; `Each` for the first product. |

At submission, requested lines are locked. At authorisation, Planning rechecks every line and commits all or none.

### 5.4 ITEquipmentRequirementPackage

Stable package root created with the Requisition. It has no profile, manifest or user-selected schema.

| Field | Purpose and rule |
|---|---|
| `package_id` | Stable identity. |
| `requisition_id` | One-to-one owning Requisition. |
| `product_pattern` | Fixed `IT Equipment`. Read-only. |
| `current_version_id` | Current package Version. |
| `authorised_version_id` | Authorised package Version. |

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
| `delivery_location_id` | Defaults from Version; may select another Active location for the same PE. |
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

“Satisfactory”, “acceptable” or similar wording without an observable condition is invalid.

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

`RequisitionTask` records one protected decision queue item for the Head of User Department or Head of Procurement Function. It stores the exact Version, role, PE/FY/OU scope, status, due display data and decision token. It grants no authority by itself.

`RequisitionDecision` stores the exact task, Version, actor, legal capacity, decision, required return reason where applicable, timestamp and resulting state. Decisions are immutable.

### 5.12 AuthorisedRequisitionHandoff v1.2

One immutable handoff is created atomically with authorisation. It contains:

- Requisition, Version and content digest;
- PE, FY, department, Plan, Plan Version and Plan Item;
- every drawdown line, `source_line_id` and `plan_item_line_id`;
- inherited business need, description and expected operational result;
- planned method, schedule, Budget Line, funding and reservation references;
- requirement title, location and latest delivery date;
- every equipment item and `requisition_item_id`;
- warranty and support values;
- every technical, service and acceptance row with stable IDs;
- supporting-material metadata, links and digests;
- Head of User Department and Head of Procurement Function decisions;
- `product_pattern = IT Equipment` and first-release suitability facts; and
- handoff version, generated time and handoff digest.

It contains no editable STD binding, supplier field, price, evaluation score or contract result.

### 5.13 TenderConsumptionProjection

Tender Preparation records handoff consumption idempotently using handoff ID, Tender ID, Tender Version, template key/version and consumed time. Requisitions uses this projection only to control revocation and show neutral status.

## 6. Fixed IT Equipment Requirement Package

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
| Draft | Send for department approval | Departmental Author | Version and package locked; state `Awaiting Department Approval`; HoD task created |
| Draft | Submit to Procurement | Head of User Department preparing directly | Version and package locked; state `Submitted to Procurement`; Procurement task created |
| Awaiting Department Approval | Return for correction | Head of User Department | Reviewed Version preserved; copied Draft successor created |
| Awaiting Department Approval | Submit to Procurement | Head of User Department | Same locked Version becomes `Submitted to Procurement`; Procurement task created |
| Submitted to Procurement | Return to department | Head of Procurement Function | Submitted Version preserved; copied Draft successor created |
| Submitted to Procurement | Authorise for Tender Preparation | Head of Procurement Function | Planning drawdown, decision and immutable handoff committed atomically; state `Authorised` |
| Awaiting Department Approval or Submitted to Procurement | Withdraw | Head of User Department | Locked Version retained; state `Withdrawn`; no drawdown |
| Authorised; handoff unconsumed | Revoke authorisation | Head of Procurement Function | Authorised evidence retained; exact drawdown reversed; state `Revoked` |

There is no separate technical review, requirements approval, Finance approval, Accounting Officer approval or committee stage in the Requisition lifecycle.

### 7.2 Submission and authorisation gates

Before departmental routing or submission, the server rechecks:

- native role and exact PE/FY/OU scope;
- current Planning eligibility and open balance;
- every field and row control in this document;
- step completion and zero Blocking findings;
- supporting-file security and digest;
- product suitability; and
- canonical content digest.

Before Procurement authorisation, the server repeats every check against the immutable submitted Version and current Planning balances. Authorisation succeeds only if the drawdown, decision, outbox event and handoff all commit.

### 7.3 Maker-checker rules

- A Departmental Author cannot complete the Head of User Department decision on the same Version unless the actor is independently assigned the Head of User Department role and prepared the Requisition directly in that capacity.
- A Head of User Department may prepare and submit a Requisition directly; this removes an unnecessary internal task but not the Procurement authorisation.
- The Head of Procurement Function cannot edit departmental content.
- The actor performing Procurement authorisation cannot also be recorded as the departmental submitting authority for the same Version.
- System Manager, ownership or technical access grants no business decision.

### 7.4 Corrections

A return requires one reason of 20–1,000 characters. The reviewed Version stays immutable and a copied Draft successor is created.

If a Planning fact is wrong, the Requisition is not edited around it. The user follows the approved Planning successor or correction route.

After authorisation:

- before handoff consumption, the Head of Procurement Function may revoke, reverse the exact Planning drawdown and allow a corrected successor;
- after handoff consumption, Requisitions cannot revoke or edit the authorised package; Tender Preparation uses its upstream-correction route; and
- after publication, clarification, addendum, cancellation or a new proceeding is governed downstream.

### 7.5 Core invariants

1. One Requisition uses one Plan Item and one requesting department.
2. Every selected Planning allocation belongs to that department.
3. One open Requisition exists per Plan Item/department.
4. Requested quantity and value never exceed current remaining Planning balances.
5. Every item links to one drawdown line; reconciled quantities are exact.
6. Planning, Strategy and Budget facts are read-only.
7. One fixed IT Equipment Requirement Package exists per Requisition; there is no user-selected schema.
8. Structured rows are authoritative; no file is an obligation by itself.
9. A locked Requisition Version references the matching locked package Version.
10. Drafting, routing and return create no Planning drawdown or Budget transaction.
11. Authorisation creates the complete drawdown, decision and handoff or none.
12. Submitted and authorised Versions, rows, files and digests are immutable.
13. Revocation is allowed only before handoff consumption and reverses the drawdown once.
14. Authorisation creates no Tender and binds no STD or Tender template.
15. Unauthorised requests reveal no record, row, file or count existence.

## 8. Roles and permissions

Use native Frappe Roles, Workflow permissions and User Permissions.

| Role | Exact work |
|---|---|
| Departmental Author | View eligible Planning allocations for the assigned department; prepare and correct a Draft; send a complete Version to the Head of User Department. |
| Head of User Department | View the complete departmental Requisition; prepare and submit directly, or return/submit an Author's locked Version; withdraw before authorisation. |
| Head of Procurement Function | View the complete submitted Requisition and fresh Planning availability; return, authorise or revoke before consumption. Cannot edit requirements. |
| Procurement Planner | Neutral read of Planning lineage and drawdown projection; no Requisition decision. |
| Procurement Officer | No Draft right in Requisitions by virtue of this role; consumes the authorised handoff in Tender Preparation. |
| Auditor | Scoped read of immutable Versions, decisions, drawdowns, handoffs and consumption evidence; no business transition. |
| System Manager | Technical administration only; no Requisition decision. |

An acting Head of User Department receives the same role and a time-bound scoped User Permission. Do not create a delegate role.

Every list, count, direct route, file download and command applies the same PE/FY/OU and task predicates before data is returned. A selected application context filters authorised data; it does not grant permission.

## 9. Cross-module contracts

### 9.1 Procurement Planning

`GetRequisitionEligiblePlanItem.v2` is the only starting projection. It returns the exact approved facts defined by PLN-CHG-001 v1.1.

`AuthoriseRequisitionDrawdown.v2` locks and rechecks every selected allocation and accepts all lines or none. It is called only inside Requisition authorisation.

`ReverseRequisitionDrawdown.v2` restores the exact quantities and values once when an unconsumed authorisation is revoked. Original drawdown and reversal evidence remain immutable.

Draft creation, save, departmental submission and Procurement return perform no Planning write.

### 9.2 Tender Preparation

Authorisation publishes `ProcurementRequisitionAuthorised.v1.2` through the transactional outbox. Tender Preparation consumes the exact handoff idempotently.

Tender Preparation shall:

- preserve all Requisition and requirement identifiers;
- show inherited requirements read-only;
- generate goods, delivery and price schedules from `RequisitionItem` rows;
- publish technical, service and acceptance rows as controlled Tender requirements;
- generate one supplier response against every published technical requirement;
- prevent the Procurement Officer from omitting or rewriting an authorised obligation;
- select or confirm the compatible released Tender template downstream; and
- carry awarded values and obligations into contract formation without re-entry.

TPR-CHG-001 v0.3 sections that treat a technical-specification PDF as the primary requirement conflict with E2E-REQ-001 v0.2 and this document. They must be corrected in the next Tender Preparation successor before implementation joins the modules.

### 9.3 No STD Configuration contract

Requisitions calls no STD Configuration, manifest, schema or mapping service. It stores no STD package, manifest, compatibility signature or schema digest. Product suitability is a typed rule for the fixed IT Equipment product, not a generic engine.

## 10. Service and command contracts

### 10.1 Reads

| Service | Required result |
|---|---|
| `GetRequisitionWorkspace` | Eligible Plan Items, own Drafts, protected tasks and neutral authorised status in exact scope. |
| `GetEligiblePlanItemDetail` | Complete Planning projection and current remaining balances; no mutation. |
| `GetRequisitionEditor` | One server projection containing Planning context, Draft values, package rows, validation, step status and permitted actions. |
| `GetDepartmentApprovalTask` | Complete immutable Version and package for the exact Head of User Department task. |
| `GetProcurementAuthorisationTask` | Complete submitted Version, package, files, validation snapshot and fresh Planning availability. |
| `GetAuthorisedRequisitionHandoff` | Exact immutable v1.2 handoff for an authorised consumer. |
| `GetRequisitionHistory` | Versions, decisions, drawdown, reversal and handoff-consumption evidence; no mutation. |

Reads never create a root, Version, package, row, task, decision, drawdown or handoff.

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
| `SendForDepartmentApproval` | Lock exact content and create one HoD task. |
| `ReturnToDepartmentAuthor` | Preserve reviewed Version and create copied Draft successor with reason. |
| `SubmitRequisitionToProcurement` | Record departmental submission and create one Procurement task. |
| `ReturnRequisitionToDepartment` | Preserve submitted Version and create copied Draft successor with reason. |
| `AuthoriseRequisition` | Atomically recheck, draw down Planning, decide, create handoff and publish outbox event. |
| `WithdrawRequisition` | Close pre-authorisation Version with no drawdown. |
| `RevokeUnconsumedAuthorisation` | Reverse exact drawdown, preserve evidence and publish revocation. |
| `RecordHandoffConsumption` | Idempotently store neutral Tender consumption evidence. |

Every command accepts an idempotency key and expected record version. The server derives actor, scope, state, totals, digests and permitted actions.

## 11. Error contract

| Code | Meaning and user treatment |
|---|---|
| `REQ_NOT_FOUND` | Record is absent or not visible. Show **Requisition not found**. |
| `REQ_ROLE_REQUIRED` | The user lacks the required native role. Show the required business role. |
| `REQ_SCOPE_DENIED` | PE/FY/OU scope is not authorised. Do not reveal record existence. |
| `REQ_PLAN_INELIGIBLE` | The Plan Item is not currently eligible. Refresh Planning status. |
| `REQ_BALANCE_CHANGED` | Remaining quantity or value changed. Refresh the drawdown step. |
| `REQ_OPEN_EXISTS` | Another open Requisition exists for this Plan Item and department. Open it. |
| `REQ_CONTROL_INVALID` | A value does not match its released type, range or options. Show the field error. |
| `REQ_QUANTITY_MISMATCH` | Item and drawdown quantities do not reconcile. Show the affected line. |
| `REQ_PRODUCT_UNSUPPORTED` | Requirement is outside straightforward IT equipment. Stop; do not offer free-text bypass. |
| `REQ_REQUIREMENT_RESTRICTIVE` | A brand or restrictive term lacks permitted equivalent treatment. Show the row. |
| `REQ_FILE_INVALID` | File type, size, malware, readability, digest or row-link rule failed. |
| `REQ_BLOCKING_FINDINGS` | Submission or authorisation has Blocking findings. Return exact links. |
| `REQ_STALE_VERSION` | Record changed. Reload the same record. |
| `REQ_SOD_BLOCKED` | Actor may not complete the decision on this Version. |
| `REQ_HANDOFF_CONSUMED` | Authorisation cannot be revoked because Tender Preparation consumed it. |
| `REQ_IDEMPOTENCY_CONFLICT` | The same key was reused with a different payload. Stop safely. |

## 12. UI architecture and routes

Use Vue 3 single-file components mounted in Frappe Desk. Reuse the existing KenTender shell, header, breadcrumb, context selector, tokens, table and dialog components. Do not import design-tool runtime code or recreate the Frappe shell.

| Surface | Route | Purpose |
|---|---|---|
| Requisitions workspace | `/app/procurement-requisitions` | Eligible Plan Items, own Drafts, tasks and authorised records. |
| Start Requisition | `/app/procurement-requisitions/new/{plan_item_id}` | Confirm the exact Planning source and create/reuse the Draft. |
| Requisition editor | `/app/procurement-requisitions/{requisition_id}` | Complete the five fixed steps. |
| Department approval | `/app/procurement-requisitions/department-task/{task_id}` | HoD reads the complete locked Version and returns or submits. |
| Procurement authorisation | `/app/procurement-requisitions/procurement-task/{task_id}` | Head of Procurement Function reads the complete submission and returns or authorises. |
| Authorised Requisition | `/app/procurement-requisitions/{requisition_id}/authorised` | Read immutable handoff, drawdown and Tender-consumption status. |

The editor loads one server projection. Opening a route creates nothing except when the user completes the explicit **Prepare Requisition** command.

## 13. Static Claude Design contract

### 13.1 Global rules

Create only the artboards listed below at 1440 × 1024. Use the exact labels, fixture values, control types and read-only treatment. Do not add dashboards, charts, scores, comments, generic attachment panels, extra reviewers, extra approvals or fields.

The Frappe breadcrumb, global PE/FY context and user menu remain outside the artboard. Static artboards show design evidence only; behaviour is controlled by section 14.

Every editor artboard uses:

- eyebrow **PROCUREMENT REQUISITIONS**;
- title **Supply and delivery of ICT equipment**;
- quiet line **REQ-KEBS-2026-ICT-0001 · PPI-KEBS-2026-ICT-001 · Version 1**;
- status badge **Draft** unless the artboard states another status;
- left step navigation with exact completion text; and
- footer actions **Save draft** and the exact next action.

### 13.2 Shared KEBS fixture

| Context | Exact value |
|---|---|
| Procuring Entity | Kenya Bureau of Standards |
| Financial Year | FY 2026/27 |
| Department | Coast Region — Administration and ICT |
| Plan Item | `PPI-KEBS-2026-ICT-001` — Supply and delivery of ICT equipment |
| Procurement method | Open Tender |
| Planned value | KES 4,875,000.00 |
| Planned completion | 30 December 2026 |
| Business need | Replace unsupported end-user devices used by Coast Region officers. |
| Expected operational result | Officers can use secure, supported equipment for office and field work. |
| Delivery location | KEBS Coast Region Office, Mombasa |
| Latest delivery date | 30 December 2026 |

Planning allocations:

| Plan item line | Source line | Requirement | Remaining quantity | Remaining value |
|---|---|---|---:|---:|
| `PIL-KEBS-ICT-001` | `SRC-KEBS-ICT-001` | Business laptops | 25 Each | KES 3,000,000.00 |
| `PIL-KEBS-ICT-002` | `SRC-KEBS-ICT-002` | Desktop computers with monitors | 15 Each | KES 1,425,000.00 |
| `PIL-KEBS-ICT-003` | `SRC-KEBS-ICT-003` | Business tablets | 10 Each | KES 450,000.00 |

### 13.3 REQ-DES-01 — Requisitions workspace

Header:

- title **Procurement Requisitions**;
- subtitle **Prepare precise departmental requests from approved Plan Items.**

Sections:

1. **Ready to prepare** — one row:

| Plan Item | Department | Method | Remaining value | Required by | Action |
|---|---|---|---:|---|---|
| Supply and delivery of ICT equipment | Coast Region — Administration and ICT | Open Tender | KES 4,875,000.00 | 30 Dec 2026 | **Prepare Requisition** |

2. **My Drafts** — one row `REQ-KEBS-2026-ICT-0001`, status Draft, updated **28 Aug 2026, 14:20**, action **Continue**.
3. **Tasks** — empty copy **No Requisition decisions are waiting for you.**
4. **Recent Requisitions** — one neutral placeholder row may show no data; no create-without-Plan action.

### 13.4 REQ-DES-02 — Start IT-equipment Requisition

Title **Prepare Requisition from approved Plan Item**.

Read-only source panel:

- Plan Item, department, procurement method, planned completion and planned value from section 13.2;
- business need and expected operational result;
- the three Planning allocation rows with remaining quantity/value.

Product panel:

- **Requirement product** — read-only **IT Equipment**;
- help: **This release supports straightforward off-the-shelf IT equipment. Complex software, integration or migration is not supported.**

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
| Requirement title | Single-line text, 160 characters | Supply and delivery of ICT equipment |
| Delivery location | PE Location Link | KEBS Coast Region Office, Mombasa |
| Latest delivery date | Date picker | 30 Dec 2026 |
| Related services required | Yes/No switch | Yes |

Drawdown table:

| Source requirement | Remaining | Requested quantity | Remaining value | Requested value |
|---|---:|---:|---:|---:|
| Business laptops | 25 Each | Integer `25` | KES 3,000,000.00 | Currency `3,000,000.00` |
| Desktop computers with monitors | 15 Each | Integer `15` | KES 1,425,000.00 | Currency `1,425,000.00` |
| Business tablets | 10 Each | Integer `10` | KES 450,000.00 | Currency `450,000.00` |

Footer: **Save draft** and **Continue to equipment items**.

### 13.6 REQ-DES-04 — Step 2: Equipment items

Step status: Request complete; Equipment in progress; Review has 6 blockers.

Item table:

| Item | Planning source | Category | Quantity | Intended use | Delivery |
|---|---|---|---:|---|---|
| Business laptops | `SRC-KEBS-ICT-001` | Laptop | 25 Each | Secure mobile office work and standards applications | Mombasa · 30 Dec 2026 |
| Desktop computers with monitors | `SRC-KEBS-ICT-002` | Desktop computer | 15 Each | Replace unsupported fixed workstations | Mombasa · 30 Dec 2026 |
| Business tablets | `SRC-KEBS-ICT-003` | Tablet | 10 Each | Field inspection capture and review | Mombasa · 30 Dec 2026 |

Button **Add equipment item** opens an exact dialog with:

- Planning source — required Link restricted to selected drawdown lines;
- Equipment category — required Select with section 5.6 choices;
- Item name — required single-line text;
- Quantity — required positive integer;
- Unit — read-only Each;
- Intended use — required textarea, maximum 500 characters;
- Delivery location — required PE Location Link; and
- Latest delivery date — required date.

Dialog actions: **Cancel** and **Add item**. Row menu: **Edit** and **Remove** only while Draft.

Footer: **Save draft** and **Continue to technical and support**.

### 13.7 REQ-DES-05 — Step 3: Technical and support

Use item tabs **Business laptops**, **Desktop computers with monitors**, **Business tablets**, and **All items**.

For Business laptops show:

| Characteristic | Comparison | Required value | Unit | Status |
|---|---|---|---|---|
| Memory | Minimum | Integer `16` | GB | Confirmed |
| Storage capacity | Minimum | Integer `512` | GB | Confirmed |
| Storage type | One of | Select `NVMe SSD` | — | Confirmed |
| Display size | Minimum | Decimal `14.0` | inches | Confirmed |
| Processor requirement | Minimum | `64-bit business-class processor, minimum 10 cores or equivalent benchmark` | — | Confirmed |
| Network connectivity | One of | `Wi-Fi 6`, `Bluetooth 5 or later` | — | Confirmed |

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
| Minimum warranty | Integer with months suffix | 24 |
| On-site support required | Yes/No | Yes |
| Maximum support response | Integer with hours suffix | 8 |
| Manufacturer support required | Yes/No | Yes |
| Service location constraint | Select | Within Kenya |
| Support description | Textarea, maximum 500 | Supplier to provide escalation and warranty-contact details. |

Footer: **Save draft** and **Continue to services and acceptance**.

### 13.8 REQ-DES-06 — Step 4: Services and acceptance

Related services table:

| Type | Applies to | Required result | Coverage | Completion | Evidence |
|---|---|---|---|---|---|
| Delivery | All items | Deliver all equipment in new, undamaged condition | 50 devices | 30 Dec 2026 | Delivery note |
| Configuration | All items | Apply KEBS standard device configuration and asset identification | 50 devices | 30 Dec 2026 | Completion certificate |
| User orientation | All items | Orient nominated users on basic operation and care | Up to 20 users | 30 Dec 2026 | Attendance record |

Button **Add related service** uses the exact controls in section 5.8.

Acceptance table:

| Check | Applies to | Pass condition | Evidence |
|---|---|---|---|
| Quantity | All items | Delivered quantities equal the authorised schedule | Inspection record |
| Physical condition | All items | No visible damage and all listed accessories are present | Inspection record |
| Required specification | All items | Every delivered model complies with all mandatory technical rows | Inspection record |
| Functional test | All items | Each device powers on and completes the agreed basic functional test | Test result |
| Documents received | All items | Warranty and delivery documents are received and verified | Certificate |

Supporting materials panel shows one optional card:

- **Coast Region device deployment room layout**;
- type **Room layout**;
- version **1.0**;
- treatment **Informational**;
- file **kebs_coast_room_layout.pdf**;
- purpose **Shows the intended workstation areas; creates no technical obligation.**

Button **Add supporting material** opens the exact controls in section 5.10.

Footer: **Save draft** and **Continue to review**.

### 13.9 REQ-DES-07 — Step 5: Review and submit

Top result: green **Ready for departmental submission**; **0 Blocking · 1 Warning**.

Summary cards:

- Planning drawdown — 3 source lines · 50 Each · KES 4,875,000.00;
- Equipment — 3 items;
- Technical requirements — 19 confirmed rows;
- Related services — 3 rows;
- Acceptance — 5 rows;
- Supporting materials — 1 informational file.

Warning row: **Delivery date is the same as the latest approved Plan completion date.**

Show the complete printable Requisition preview beneath the summary. It includes every inherited fact and structured row, not only totals.

For a Departmental Author, footer actions are **Back**, **Save draft** and **Send for department approval**.

For a Head of User Department preparing directly, replace the last action with **Submit to Procurement**.

### 13.10 REQ-DES-08 — Department approval task

Status **Awaiting Department Approval**. Header identifies Author **James Mwangi**, Departmental Author.

Show the complete immutable Version from REQ-DES-07, including Planning allocations, items, all technical rows, services, acceptance rows, material card, validation and digest.

Decision statement:

> I confirm that this Requisition states the department's operational need and minimum requirements and may be submitted to Procurement.

Footer: **Return for correction** and **Submit to Procurement**. No edit control.

### 13.11 REQ-DES-09 — Procurement authorisation task

Status **Submitted to Procurement**. Show:

- the same complete immutable Version;
- fresh Planning availability: **Eligible · KES 4,875,000.00 and 50 Each remain available**;
- suitability: **Straightforward IT equipment · Compatible with first released product**;
- validation: **0 Blocking · 1 Warning**; and
- Head of User Department submission: **Approved by Grace Achieng · 28 Aug 2026, 15:10 EAT**.

Decision statement:

> I authorise this complete Requisition for Tender Preparation and commit its stated Planning drawdown.

Footer: **Return to department** and **Authorise for Tender Preparation**. No edit, evidence-builder or template selector.

### 13.12 REQ-DES-10 — Authorised Requisition

Status **Authorised for Tender Preparation**.

Show:

- Requisition and handoff references;
- authorised Version and digest;
- Planning drawdown reference and exact source lines;
- complete structured package read-only;
- decision evidence;
- Tender status **Not yet consumed**; and
- one available action for authorised downstream users: **Open Tender Preparation**.

The action deep-links to Tender Preparation; it does not create a Tender from a read. The actual Tender is created only by Tender Preparation's explicit command.

When consumed, replace status with **Consumed by TND-KEBS-2026-0001 · IT Equipment — Open Tender v1.0**. Hide revocation action after consumption.

### 13.13 Decision dialogs and common states

Return dialog:

- title **Return Requisition for correction?**;
- textarea label **Correction required**;
- 20–1,000 characters;
- buttons **Cancel** and **Return**.

Authorisation dialog:

- title **Authorise Requisition?**;
- exact totals **50 Each · KES 4,875,000.00**;
- statement **This commits the Planning drawdown and creates the immutable Tender Preparation handoff.**;
- buttons **Cancel** and **Authorise**.

Revocation dialog:

- title **Revoke unconsumed authorisation?**;
- required reason 20–1,000 characters;
- statement **The Planning drawdown will be reversed. The authorised Version remains in history.**;
- buttons **Cancel** and **Revoke authorisation**.

Common states:

- loading uses the shared KenTender skeleton;
- empty states state what is absent and never offer unauthorised creation;
- forbidden and nonexistent records both show **Requisition not found**;
- stale Version shows **This Requisition changed. Reload to continue.**;
- unsupported product shows **This requirement is not supported by the IT Equipment product. Return to Planning or use a later approved product.**;
- no page displays technical identifiers as editable controls.

## 14. Functional interaction requirements

### 14.1 Workspace and preparation

- Workspace reads are side-effect free.
- **Prepare Requisition** rechecks eligibility and creates or reuses the one open Draft.
- Browser Back, refresh and repeated commands do not create duplicates.
- Opening a protected task requires the exact open task and current scope.

### 14.2 Editor

- Save validates only the current edit plus cross-row invariants affected by it.
- Continue saves the current step and moves only when its blockers are zero.
- Row dialogs derive control type, comparison, unit and options from typed server metadata for the code-owned catalogue.
- Changing an equipment category revalidates its characteristics and blocks removal of incompatible rows until the user resolves them.
- Removing an item is blocked while linked technical, service, acceptance or file rows remain.
- Turning related services to No requires explicit confirmation and removes no rows silently.
- Autosave is not required. Explicit Save draft is authoritative.

### 14.3 Submission and decisions

- Submission locks the exact Version and package before creating a task.
- Task screens show the complete immutable content; summary-only approval is prohibited.
- A return creates a copied Draft successor only after the decision commits.
- Authorisation reruns validation and Planning availability under lock.
- Double-clicks and retries return the first successful result.
- Notifications are outbox effects, not part of authority.

### 14.4 Accessibility and page lifecycle

- Every control has a visible label and error text associated programmatically.
- Keyboard users can complete tables, dialogs and steps.
- Focus moves to the first invalid field after validation.
- Status is not conveyed by colour alone.
- Unsaved changes prompt before leaving the editor.
- Pages clean up listeners and abort stale requests on unmount.

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
- outbox publication and retry evidence; and
- Tender handoff consumption.

Audit records contain actor, native role/legal capacity, PE/FY/OU scope, server time, request ID and idempotency key. Audit payloads do not store authentication secrets or duplicate uploaded file bytes.

Submitted, returned, authorised, withdrawn, revoked and superseded Versions cannot be edited or deleted through product commands.

## 16. Deterministic KEBS seed

### 16.1 Prerequisites and actors

| Fixture | Exact value |
|---|---|
| PE/FY context | `PE-KEBS` · FY 2026/27 · Active |
| Department | `OU-KEBS-COAST-ICT` — Coast Region — Administration and ICT |
| Departmental Author | `james.mwangi@kebs.example.test` |
| Head of User Department | `grace.achieng@kebs.example.test` |
| Head of Procurement Function | `david.kimani@kebs.example.test` |
| Procurement Officer | `faith.njeri@kebs.example.test` |
| Auditor | `audit@kebs.example.test` |

Each user receives only native roles and User Permissions required by section 8.

### 16.2 Planning projection

Seed the exact Plan Item, three allocations and values in section 13.2 as an Active, funded and Requisition-eligible projection. No Requisition seed writes Planning or Budget tables directly.

### 16.3 Complete package

Seed the three equipment items, technical examples, warranty/support values, related services, acceptance checks and informational room-layout material in sections 13.6–13.8.

The complete technical fixture has these 19 confirmed rows:

| ID | Applies to | Characteristic | Required value |
|---|---|---|---|
| `TECH-001` | All items | Electrical compatibility | Yes — suitable for Kenyan mains supply |
| `TECH-002` | All items | New and unused equipment | Yes |
| `TECH-003` | Business laptops | Memory | Minimum 16 GB |
| `TECH-004` | Business laptops | Storage capacity | Minimum 512 GB |
| `TECH-005` | Business laptops | Storage type | NVMe SSD |
| `TECH-006` | Business laptops | Display size | Minimum 14.0 inches |
| `TECH-007` | Business laptops | Processor requirement | 64-bit business-class processor, minimum 10 cores or equivalent benchmark |
| `TECH-008` | Business laptops | Network connectivity | Wi-Fi 6 and Bluetooth 5 or later |
| `TECH-009` | Desktop computers with monitors | Memory | Minimum 16 GB |
| `TECH-010` | Desktop computers with monitors | Storage capacity | Minimum 512 GB |
| `TECH-011` | Desktop computers with monitors | Storage type | SSD |
| `TECH-012` | Desktop computers with monitors | Processor requirement | 64-bit business-class processor, minimum 10 cores or equivalent benchmark |
| `TECH-013` | Desktop computers with monitors | Network connectivity | Ethernet |
| `TECH-014` | Desktop computers with monitors | Display resolution | Minimum Full HD |
| `TECH-015` | Business tablets | Memory | Minimum 8 GB |
| `TECH-016` | Business tablets | Storage capacity | Minimum 256 GB |
| `TECH-017` | Business tablets | Display size | Minimum 10.5 inches |
| `TECH-018` | Business tablets | Battery runtime | Minimum 10 hours |
| `TECH-019` | Business tablets | Network connectivity | Wi-Fi 6 |

Package-level warranty remains 24 months and is carried once into the handoff and Tender. It is not duplicated as an editable technical row.

### 16.4 Lifecycle fixtures

Seed separately and idempotently:

1. one complete Draft owned by James Mwangi;
2. one Version awaiting Grace Achieng's department decision;
3. one Version submitted to David Kimani for Procurement authorisation;
4. one authorised Version with drawdown and unconsumed handoff;
5. one returned Version with copied Draft successor; and
6. one authorised handoff consumed by `TND-KEBS-2026-0001`.

Fixtures use distinct Requisition references so lifecycle states do not overwrite each other.

### 16.5 Seed rules

- Upsert by stable IDs; rerun creates no duplicates.
- Validate PE/FY/OU and Planning prerequisites before seeding.
- Never grant Administrator a business decision by implication.
- Never use production emails or attachments.
- Never create an STD manifest, profile or template-selection record.
- Print a concise created/reused/failed report.

## 17. Acceptance contract

| ID | Required result |
|---|---|
| REQ-AC-001 | Starting from the eligible KEBS Plan Item creates or reuses one Draft Requisition. |
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
| REQ-AC-015 | “Satisfactory” alone is rejected as a pass condition. |
| REQ-AC-016 | A supporting file cannot create an unstructured obligation. |
| REQ-AC-017 | An operative file links to at least one structured requirement and retains a digest. |
| REQ-AC-018 | Brand/restrictive wording without permitted equivalence treatment blocks submission. |
| REQ-AC-019 | A Departmental Author routes one complete locked Version to the HoD. |
| REQ-AC-020 | A Head of User Department sees the complete Version and may return or submit it. |
| REQ-AC-021 | A HoD preparing directly may submit without an invented departmental-review task. |
| REQ-AC-022 | The Head of Procurement Function sees the complete Version and fresh Planning availability. |
| REQ-AC-023 | No technical reviewer, Finance approver, Accounting Officer or committee stage exists in the Requisition chain. |
| REQ-AC-024 | Procurement return creates a copied Draft successor and preserves the submitted Version. |
| REQ-AC-025 | Authorisation commits decision, all Planning drawdowns, handoff and outbox event atomically. |
| REQ-AC-026 | Failed authorisation creates none of those effects. |
| REQ-AC-027 | The handoff contains all inherited facts and every structured row with stable IDs. |
| REQ-AC-028 | Authorisation creates no Tender and binds no Tender template. |
| REQ-AC-029 | Tender Preparation can consume the handoff once and retain every identifier. |
| REQ-AC-030 | Revocation before consumption reverses the exact drawdown once and preserves evidence. |
| REQ-AC-031 | Revocation after consumption is blocked. |
| REQ-AC-032 | Native Frappe role and User Permission checks protect rows, counts, routes, files and commands consistently. |
| REQ-AC-033 | An acting HoD uses the same role; no delegate role or second permission system exists. |
| REQ-AC-034 | The complete KEBS package renders with zero missing values or anonymous requirement text. |
| REQ-AC-035 | Repeated seed and command execution remains idempotent. |
| REQ-AC-036 | No STD Configuration, manifest, composer profile or generic schema object exists. |
| REQ-AC-037 | No attachment-only specification can reach authorisation. |
| REQ-AC-038 | TPR compatibility receives structured items, technical rows, services and acceptance rows rather than one primary specification PDF. |

## 18. Test and smoke contract

### 18.1 Focused automated layers

1. Pure tests for ranges, options, category applicability, quantity reconciliation, date rules and objective acceptance wording.
2. Domain tests for Version locking, correction copies, maker-checker, drawdown and handoff invariants.
3. Permission tests for every role, scope, list, count, direct route and File.
4. Database tests for uniqueness, optimistic concurrency, atomic authorisation, reversal and idempotency.
5. Contract tests against `GetRequisitionEligiblePlanItem.v2` and the v1.2 Tender handoff.
6. Vue component tests for control types, conditional fields, read-only presentation, row dependencies and decision dialogs.
7. Browser smoke using the KEBS fixtures.

### 18.2 Named smoke journeys

**REQ-SMK-01 — Happy path**

Departmental Author prepares the KEBS Draft, completes five steps, HoD submits, Head of Procurement Function authorises, Planning drawdown is visible and Tender Preparation reads the handoff.

**REQ-SMK-02 — Direct HoD preparation**

Head of User Department prepares a complete Draft and submits it directly to Procurement without a self-review task.

**REQ-SMK-03 — Controlled return**

Procurement returns one immutable Version; the department corrects the copied Draft; earlier content and reason remain visible.

**REQ-SMK-04 — Planning balance changed**

Planning availability changes after departmental submission; authorisation stops with `REQ_BALANCE_CHANGED` and creates no partial drawdown.

**REQ-SMK-05 — Attachment misuse**

An operative uploaded document has no structured-row link; submission is blocked even though the file is readable.

**REQ-SMK-06 — Unsupported complexity**

The Author adds custom software development or systems integration as the principal service; the product stops without a free-text bypass.

**REQ-SMK-07 — Permission isolation**

Users outside the exact PE/FY/OU or task scope receive the same not-found treatment for list, detail, file and command access.

**REQ-SMK-08 — Revocation boundary**

Unconsumed authorisation revokes and reverses once; consumed authorisation cannot revoke.

### 18.3 Required release evidence

- migration/build output;
- focused unit, domain, permission, database and contract-test results;
- screenshots for REQ-DES-01 through REQ-DES-10 at 1440 × 1024;
- scripted KEBS happy-path and return-path walkthroughs;
- exact generated handoff fixture and digest;
- proof of all-or-none Planning drawdown;
- zero page-specific console errors or failed network requests; and
- search evidence showing no manifest, composer-profile, capability-profile or attachment-primary compatibility path.

## 19. Implementation constraints

- Use ordinary typed Frappe DocTypes and child tables; do not store the package as opaque user-authored JSON.
- Keep authoritative validation and transitions in server services, not Vue components or Jinja.
- Use database uniqueness and row locks for one-open-Draft, drawdown and idempotency rules.
- Use the transactional outbox for handoff and revocation events.
- Keep uploaded Files private; permission-check every download.
- Use one canonical serializer for validation, preview, digest and handoff.
- Do not duplicate Planning or Budget tables inside Requisitions.
- Do not make implementation depend on legacy parser, OCR, inferred schemas or abandoned STD runtime code.
- Do not run the full suite as the first diagnostic step for a focused failure.

## 20. Existing data and cutover

REQ-CHG-001 v1.2 is a clean product correction.

- Do not migrate unfinished manifest-based Drafts into the fixed package automatically.
- Do not create aliases, dual reads or hidden legacy routes.
- Existing authorised historical records remain read-only evidence under their original implementation where retention is required.
- No historical record becomes eligible for Tender Preparation merely because v1.2 is installed.
- Test or incomplete PoC data may be removed only through an explicit, separately approved cleanup.
- New Requisitions use only the v1.2 model after cutover.

## 21. E2E-REQ-001 conformance

| Approved control | Requisition implementation |
|---|---|
| Structured system data is authoritative | Items, technical requirements, services and acceptance checks are typed rows. |
| Fixed product form | One code-owned IT Equipment package; no user-defined schema. |
| Released product, not STD Configuration | Requisitions selects no STD or manifest. |
| Enter once, carry forward | Planning lineage and departmental facts are inherited; all requirement IDs pass to Tender. |
| Clear ownership | Department owns the requirement; Procurement authorises but cannot edit it. |
| Electronic downstream use | Bidder, evaluation and contract consumers receive stable structured rows. |
| Native permissions and minimum roles | Departmental Author, HoD, Head of Procurement Function and read-only supporting roles only. |
| No premature abstraction | The model is specific to straightforward IT equipment. |

## 22. Traceability and precedence

This document implements and is subordinate to:

- E2E-REQ-001 v0.2 — approved structured requirement lineage and simplicity controls;
- NDS-CHG-001 v1.1 — accepted Need facts and optional Needs route;
- PLN-CHG-001 v1.1 — Active Plan Item, source allocations, eligibility and drawdown;
- STD-ST-001 v0.3 — no STD Configuration module and code-owned released product pattern; and
- STD-TPL-001 v0.3 — released `IT-EQUIPMENT-OPEN-V1` source and curation evidence, except where its attachment-primary assumption conflicts with E2E-REQ-001 v0.2.

REQ-CHG-001 v1.2 supersedes approved REQ-CHG-001 v1.0 for new implementation work and withdraws proposed v1.1. The next required document is a complete Tender Preparation successor that replaces technical-PDF inheritance with the v1.2 structured handoff while retaining the released Goods template and five-task officer journey.

## 23. Approval effect

REQ-CHG-001 v1.2 was approved by the Project Owner on 28 August 2026. It supersedes v1.0 for new implementation work and is the complete Procurement Requisitions authority. Proposed v1.1 remains unapproved source material and must not be implemented.

This approval authorises:

- implementation of the fixed IT Equipment Requisition product;
- conversion of section 13 into Claude Design artboards;
- the Planning drawdown and Tender handoff contracts defined here; and
- retirement of the manifest-based and attachment-primary Requisition path.

It will not approve Tender Preparation implementation until that document is revised to consume this structured handoff.
