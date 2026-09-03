# TPR-CHG-001 — Minimal IT Tender Preparation

| Control | Value |
|---|---|
| Document ID | TPR-CHG-001 |
| Version | 0.4 |
| Date | 28 August 2026 |
| Status | Approved |
| Approval date | 29 August 2026 |
| Change type | Complete consolidated successor to proposed v0.3 |
| First product | `IT-EQUIPMENT-OPEN-V1` — straightforward IT equipment under the PPRA Goods STD |
| Starts from | One authorised REQ-CHG-001 v1.2 handoff |
| Ends at | One approved immutable publication handoff |
| Implementation authority | Gated by a successful KEBS walkthrough and completed template 1.1 release evidence |

**Controlling decision:** Tender Preparation consumes the authorised structured Requisition without re-entry. It applies one code-owned Goods Tender pattern, collects only genuine tender-specific decisions, generates the complete Tender and routes one immutable Version to the Head of Procurement Function. There is no STD Configuration module, schema editor, generic manifest or technical-specification upload as the primary requirement.

## 1. Governing decision

This approved complete document is the only Tender Preparation requirements document to consult for the first IT-equipment product. Proposed v0.3 is historical source material.

The useful parts of v0.3 remain: one released template, five Procurement Officer tasks, exact typed controls, one readiness check, one approver and one publication handoff.

The central correction is:

> Primary technical-specification PDF → inherited structured Requisition items and requirement rows.

### 1.1 Corrected earlier directions

| Earlier direction | Treatment in v0.4 |
|---|---|
| Quantity, delivery and technical document inherited from the Requisition | Replace technical document with the complete structured REQ-CHG-001 v1.2 package. |
| Procurement Officer recreates goods and delivery rows | Remove. Goods and services are inherited read-only. |
| Approved technical PDF published as Section V | Remove as the primary requirement. Generate Section V from structured items, technical rows, services and acceptance rows. |
| Supplier compliance against a PDF | Replace with one electronic response against every published technical requirement ID. |
| Supporting files listed without row-level control | Replace with governed files linked to specific structured rows and published with their authorised treatment. |
| Tender template version 1.0 assumes the PDF model | Do not mutate it silently. Release a corrected code-owned template version 1.1 before implementation. |
| Generic additional evidence linked to an item or document section | Link every evidence row to a visible structured requirement, item, service or acceptance ID. |
| Custom permission layers | Prohibited. Use native Frappe Roles, Workflow permissions and User Permissions. |

## 2. Purpose and scope

Tender Preparation shall:

- start from one unconsumed authorised Requisition handoff;
- prove that the Requisition fits the released IT-equipment product;
- bind one immutable code-owned template version;
- inherit Planning and Requisition facts read-only;
- collect a small set of tender-specific values through five fixed tasks;
- generate the Invitation, issued Tender, supplier-response controls and contract obligations;
- run one deterministic readiness check;
- let the Head of Procurement Function return or approve the complete Version; and
- create one immutable publication handoff.

### 2.1 Included

- straightforward off-the-shelf IT equipment;
- one PE, Financial Year, Requisition, award package and Tender;
- Open Tender method;
- one Tender currency, KES;
- fixed-price treatment;
- pass/fail technical compliance;
- arithmetic and financial evaluation; and
- the structured REQ-CHG-001 v1.2 handoff.

### 2.2 Excluded

- software development, systems implementation, integration, migration or hosting;
- Works, consulting or non-consulting-services products;
- lots, framework agreements, multiple currencies or multiple award packages;
- STD, template, clause, schema or mapping configuration through Desk;
- editing authorised Requisition facts;
- Procurement Officer entry of supplier prices or responses;
- criterion builders, weighted scoring or evaluator discretion not defined here;
- publication-channel implementation, supplier portal, evaluation, award or contract execution;
- a technical-review workflow or departmental clarification task;
- a second Tender approver; and
- automatic conversion of legacy PDFs into structured requirements.

## 3. Simple journey

1. Procurement Officer selects one eligible authorised Requisition handoff.
2. KenTender confirms that `IT-EQUIPMENT-OPEN-V1` version 1.1 is installed and compatible.
3. The system creates one Draft Tender and binds the exact handoff and template digests.
4. The officer completes five fixed tasks.
5. KenTender validates and renders the complete Invitation and issued Tender.
6. The officer submits the immutable Version.
7. The Head of Procurement Function reads the complete Version and returns or approves it.
8. Approval creates one immutable publication handoff.

No user configures a template or re-enters the department's requirements.

## 4. Responsibility boundary

| Information or action | Owner | Tender Preparation treatment |
|---|---|---|
| PE/FY, Plan, method, funding and value | Authorised Requisition/Planning | Inherit read-only; never render internal value publicly unless required. |
| Requirement title, need and expected result | Authorised Requisition | Inherit read-only; use title as Tender-title default. |
| Equipment items, quantities, unit, location and latest date | Authorised Requisition | Inherit read-only; generate goods, delivery and price schedules. |
| Technical requirements | Authorised Requisition | Inherit read-only; publish and generate supplier-response rows. |
| Warranty and support requirements | Authorised Requisition | Inherit read-only; render in Section V and contract schedules. |
| Related services and acceptance checks | Authorised Requisition | Inherit read-only; render as service and acceptance obligations. |
| Supporting materials | Authorised Requisition | Publish according to authorised treatment and exact row links. |
| Standard wording and forms | Installed template 1.1 | Locked code-owned release; operational users cannot edit. |
| Tender dates, security and meeting | Procurement Officer | Enter using the finite controls in section 8. |
| Supplier evidence requirements | Procurement Officer | Select only permitted evidence linked to visible requirements. |
| Contract parameters | Procurement Officer | Enter only finite values permitted by section 8.5. |
| Readiness and rendering | KenTender | Generate deterministically from the bound Versions. |
| Tender return or approval | Head of Procurement Function | Decide the complete immutable Version; cannot edit it. |
| Publication | Downstream process | Consume the immutable publication handoff. |

Technical clarification may occur between Procurement and the department outside a new KenTender workflow. If clarification changes an authorised requirement, quantity, value or date, the Tender stops and follows the upstream-correction route in section 10.4.

## 5. Roles and permissions

Use ordinary Frappe Roles, Workflow permissions and User Permissions.

| Role | Exact work |
|---|---|
| Procurement Officer | Start a Tender from an eligible handoff; edit the five Draft tasks; run readiness; submit; correct a returned Version. |
| Head of Procurement Function | Read the complete submitted Version and preview; return, approve or reopen before publication consumption. Cannot edit Tender values. |
| Departmental Author / Head of User Department | Read the inherited Requisition and neutral Tender status where already authorised; no Tender edit or decision. |
| Auditor | Scoped read of Versions, decisions, template binding and publication evidence; no business transition. |
| System Manager | Technical administration and exact-payload retry only; no Tender decision. |

The Procurement Officer who prepared a Version cannot approve it. No Tender reviewer, technical approver, committee or publication approver is introduced.

Every list, count, route, preview, file and command uses the same PE/FY scope and protected-task predicate. A selected context filters authorised records; it does not grant authority.

## 6. Installed Tender template

### 6.1 Exact product

| Property | Value |
|---|---|
| Template key | `IT-EQUIPMENT-OPEN-V1` |
| Display name | IT Equipment — Open Tender |
| KenTender template version | 1.1 |
| Official source | PPRA Standard Tender Document for Procurement of Goods |
| Product | Straightforward off-the-shelf IT equipment |
| Method | Open Tender |
| Evaluation | Eligibility, pass/fail technical compliance, arithmetic/financial evaluation, lowest evaluated responsive Tender |
| Award package | One |
| Tender currency | KES |

The Goods STD is used because the first product is equipment supply. The complex Information Technology STD is outside this release.

### 6.2 Version 1.1 release correction

Template version 1.1 shall reuse the independently reviewed locked text, official forms, coverage register and render structure from the curated version 1.0 work. It changes only the requirement boundary and mappings needed by the approved Requisition model.

The controlled release work must:

1. preserve the official source file, digest and reviewed locked text;
2. preserve the separate Invitation and issued-Tender outputs;
3. replace the primary technical-PDF insertion with generated structured Section V schedules;
4. add one supplier response for every `technical_requirement_id`;
5. render services and acceptance requirements with their stable IDs;
6. publish supporting materials only with their authorised treatment and links;
7. carry warranty/support values to the SCC and contract schedule;
8. update the coverage, insertion-point and forms registers;
9. produce a new KEBS expected fixture; and
10. record a new bundle digest and template version.

It must not rerun PDF parsing, infer requirements, rewrite locked clauses or create a configuration UI.

### 6.3 Installed bundle

The code-owned bundle contains:

- template metadata and official-source record;
- locked official text and forms;
- the five-task officer model;
- typed validation and readiness rules;
- Section V renderers for goods, technical requirements, services, acceptance and supporting materials;
- supplier-response, evaluation and contract mappings;
- Invitation and issued-Tender renderers;
- coverage, insertion and forms registers; and
- deterministic fixture and tests.

Installation validates the source and bundle digests, then creates one read-only Supported Tender Template registry row. The row is available for new Tenders only when the installed code and digests match. System Manager cannot edit the bundle through Desk.

### 6.4 Compatibility test

Version 1.1 is offered only when every answer is Yes:

| Test | Required result |
|---|---|
| Handoff version | `AuthorisedRequisitionHandoff v1.2` |
| Product pattern | `IT Equipment` |
| Method | Open Tender |
| Currency | KES |
| Award package | One |
| Equipment | Straightforward off-the-shelf goods |
| Technical response | Every mandatory requirement can use the typed pass/fail response in section 9.1 |
| Complex work | No custom development, integration or migration |
| Dates and value | Inside authorised Requisition boundaries |
| Supporting materials | Every operative file obligation has a structured row |

Any No blocks Tender creation with no free-text bypass.

## 7. Canonical domain model

### 7.1 Tender

| Field | Purpose and rule |
|---|---|
| `tender_id` | Stable server-generated identity. |
| `tender_reference` | Generated once and used in all outputs. |
| `requisition_handoff_id` | Exact authorised, unconsumed starting point; immutable. |
| `requisition_version_id` / `requisition_digest` | Fix the approved upstream content. |
| `pe_fy_context_id` / `plan_item_id` | Read-only lineage. |
| `template_key` / `template_version` | Fixed `IT-EQUIPMENT-OPEN-V1` / `1.1`. |
| `official_source_digest` / `bundle_digest` | Exact installed release binding. |
| `current_version_id` | Current Draft, submitted or approved Version. |
| `approved_version_id` | Exact approved Version. |
| `current_state` | Derived from section 10. |
| `publication_handoff_id` | Empty before approval. |
| `publication_consumed_at` | Neutral downstream projection. |
| `record_version` | Optimistic-concurrency token. |

One handoff can create at most one open or approved Tender.

### 7.2 TenderVersion

| Field | Purpose and rule |
|---|---|
| `tender_version_id` | Immutable decision identity after submit. |
| `tender_id` | Stable parent. |
| `version_number` | Generated sequence. |
| `based_on_version_id` | Returned or reopened Version copied for correction. |
| `version_status` | `Draft`, `Submitted`, `Returned`, `Approved`, `Reopened` or `Cancelled`. |
| Task 1 values | Exact fields in section 8.1. |
| Task 4 values | Exact evidence choices in section 8.4. |
| Task 5 values | Exact contract parameters in section 8.5. |
| `content_digest` | Canonical digest of binding, inherited data, officer values and generated rows. |
| `record_version` | Draft concurrency token. |

### 7.3 InheritedRequirementSnapshot

Created with the Draft from the immutable handoff. It stores no editable copy.

It contains:

- drawdown and source-line lineage;
- requirement title, need, result, location and date;
- equipment items;
- technical requirements;
- warranty/support values;
- related services;
- acceptance requirements; and
- supporting-material references and digests.

Every row retains its Requisition identifier. Tender commands cannot alter this snapshot.

### 7.4 TenderEvidenceRequirement

| Field | Purpose and rule |
|---|---|
| `evidence_requirement_id` | Stable Tender evidence identity. |
| `tender_version_id` | Owning Draft/Version. |
| `evidence_label` | Required plain text, 3–160 characters. |
| `evidence_type` | Select: `Declaration`, `Certificate`, `Datasheet or brochure`, `Schedule or form`, `Other document`. |
| `linked_requirement_type` | Select: `Equipment item`, `Technical requirement`, `Related service`, `Acceptance requirement`. |
| `linked_requirement_id` | Required exact visible inherited ID. |
| `mandatory` | Required Yes/No; default Yes. |
| `source` | `Fixed by template`, `Generated by officer choice` or `Additional officer evidence`. Read-only. |
| `row_order` | Stable generated order. |

An evidence row cannot create a hidden criterion. Its label and linked requirement appear in the issued Tender.

### 7.5 Generated Tender schedules

The following are deterministic projections, not editable tables:

- goods and delivery schedule from Requisition items;
- related-services schedule from service rows;
- technical compliance schedule from technical requirements;
- acceptance schedule from acceptance rows;
- supplier price schedule from goods and service rows;
- supplier evidence checklist from fixed and officer-selected evidence; and
- contract obligations from goods, service, warranty/support and acceptance rows.

### 7.6 TenderDecision and PublicationHandoff

`TenderDecision` records the exact submitted Version, actor, Head of Procurement Function capacity, return/approve/reopen decision, required reason where applicable, time and resulting state.

Approval creates one immutable `TenderPublicationHandoff v1.1` containing:

- Tender, Version, Requisition handoff and template binding;
- all inherited requirement snapshots and stable IDs;
- all officer values and generated schedules;
- Invitation and issued-Tender files and digests;
- structured supplier-response schema;
- evaluation contract;
- contract-obligation projection;
- readiness result and warning set;
- approval decision; and
- package digest.

## 8. Five Procurement Officer tasks

### 8.0 Rules for every control

| Value class | Presentation |
|---|---|
| From authorised Requisition | Read-only value with source label **From authorised Requisition**. |
| Fixed by template | Read-only value with source label **Fixed by IT Equipment template v1.1**. |
| Generated | Read-only value with source label **Generated by KenTender**. |
| Two choices | Yes/No switch or radio; never free text. |
| Finite choice | Select or radio containing only listed values. |
| Governed reference | Frappe Link restricted to Active records for the Tender PE. |
| Date/time | Date or datetime picker; datetime uses `Africa/Nairobi`. |
| Number/money/percentage | Numeric control with stated unit, range and precision. |
| Genuine Tender wording | Bounded plain text; no HTML or Markdown. |
| Supplier response | Read-only placeholder **Completed by Tenderer**. |

The client and server enforce the same type, source, visibility, options and validation. Read-only values are not styled as editable or disabled text boxes.

### 8.1 Task 1 — Tender details

Read-only context:

| Field | Source and use |
|---|---|
| Procuring Entity, Plan Item and Requisition | Exact handoff lineage. |
| Requirement title | Default Tender title. |
| Procurement method | Open Tender; compatibility and rendering. |
| Authorised value | Internal scope control; not published as supplier price. |
| Latest delivery date | Maximum permitted schedule date. |
| Requirement summary | Counts of items, technical rows, services, acceptance rows and materials. |
| Template | IT Equipment — Open Tender · Version 1.1. |
| Tender reference | Generated once. |
| Opening date/time | Generated equal to submission deadline for this release. |

Officer controls:

| Field | Control | Allowed/default | Validation |
|---|---|---|---|
| Tender title | Single-line text, maximum 160 | Default Requisition title | Required; no markup or generic title. |
| Issue date | Date | No text date | Required; before later deadlines. |
| Clarification deadline | Datetime | Africa/Nairobi | Required; after issue date, before submission. |
| Submission deadline | Datetime | Africa/Nairobi | Required; after clarification. |
| Tender validity | Integer days | 1–365; default 120 | Required. |
| Tender security treatment | Read-only | Tender Security | Fixed for version 1.1. |
| Tender security currency | Read-only | KES | Fixed. |
| Tender security amount | Currency, 2 decimals | Positive KES | Required. |
| Pre-tender meeting | Yes/No | Default No | Required. |
| Meeting date/time | Datetime | Conditional | Required when meeting is Yes; before submission. |
| Meeting mode | Radio | Physical, Online | Required when meeting is Yes. |
| Meeting venue | PE Location Link | Conditional | Required for Physical. |
| Online joining information | Text, maximum 240 | Conditional | Required for Online. |

### 8.2 Task 2 — Goods and requirements

This task is review-only. It displays the complete inherited Requisition package:

- goods and delivery schedule;
- technical requirements grouped by item and `technical_requirement_id`;
- warranty and support values;
- related-services schedule;
- acceptance schedule; and
- supporting-material cards with treatment and linked requirement IDs.

No quantity, description, unit, location, date, requirement, warranty, service, acceptance row or supporting file is editable.

The only action is **Request upstream correction**, which closes no record by itself. It opens the confirmation in section 10.4 and, when completed, moves the Tender to `Upstream correction required` through the protected command.

### 8.3 Task 3 — Price schedule

Task 3 contains no officer input.

| Column | Treatment |
|---|---|
| Item/service identity, description, quantity and unit | Generated from the inherited Requisition. |
| Unit price | Supplier response placeholder. |
| Line total | Calculated from supplier response. |
| Tax | Supplier response or released calculation. |
| Tender total | Calculated and reused throughout downstream records. |

Price currency is read-only KES. Prices are fixed for the contract period and taxes are shown separately. The authorised internal value is not copied into the supplier price schedule.

### 8.4 Task 4 — Submission and evaluation

The evaluation sequence is fixed:

1. submission and eligibility;
2. pass/fail technical compliance;
3. arithmetic and financial evaluation; and
4. award to the lowest evaluated responsive Tender.

Officer controls:

| Field | Control | Allowed/default | Validation/effect |
|---|---|---|---|
| Manufacturer authorisation required | Yes/No | Default Yes | Yes generates fixed evidence linked to each applicable item. |
| Product datasheets or brochures required | Yes/No | Default Yes | Yes generates evidence linked to technical rows. |
| Warranty confirmation required | Read-only | Yes — always required | Generated from authorised warranty obligation. |
| Past supply experience required | Yes/No | Default No | Required. |
| Minimum comparable contracts | Select | 1, 2, 3 | Required when experience is Yes. |
| Experience period | Select years | 3, 5 | Required when experience is Yes. |
| After-sales support evidence required | Yes/No | Default from authorised support need | Required. |
| After-sales evidence | Select | Kenya service-centre details and escalation contacts; Manufacturer or authorised service-partner commitment; Both | Required when after-sales evidence is Yes. |

Additional evidence row:

| Field | Control and rule |
|---|---|
| Evidence label | Plain text, 3–160 characters. |
| Evidence type | Select: Declaration, Certificate, Datasheet or brochure, Schedule or form, Other document. |
| Linked requirement type | Select from the four types in section 7.4. |
| Linked requirement | Required exact inherited Link. |
| Mandatory | Yes/No; default Yes. |

Additional evidence must be proportionate and prove the linked published requirement. It cannot add a qualification threshold or technical obligation hidden from Task 2.

### 8.5 Task 5 — Contract terms

Read-only summaries show delivery, warranty, support, services and acceptance from the Requisition.

Officer controls:

| Field | Control | Allowed/default | Validation |
|---|---|---|---|
| Inspection and acceptance location | PE Location Link | Active Tender-PE location | Required. |
| Payment timing | Select days | 30, 45, 60; default 30 | Required; used with fixed valid-invoice and acceptance wording. |
| Performance security required | Yes/No | Default Yes | Required. |
| Performance security percentage | Decimal percent | 1–10; default 10 | Required when security is Yes. |
| Delay damages per week | Decimal percent | 0.1–1.0; default 0.5 | Required. |
| Maximum delay damages | Integer percent | 5–10; default 10 | Required; not less than weekly rate. |
| Contract contact office | PE Office Link | Active office only | Required; no personal-user selection. |

General Conditions remain locked. No clause editor exists.

## 9. Supplier, evaluation and contract mappings

### 9.1 Technical supplier response

For every `technical_requirement_id`, the supplier receives:

| Response value | Control |
|---|---|
| Compliance | Required radio: `Comply`, `Do not comply`. |
| Offered value | Typed control matching the requirement where measurable; otherwise bounded text, maximum 300 characters. |
| Comment | Optional plain text, maximum 500 characters. |
| Evidence references | Required only where Task 4 links evidence to the requirement. |

The response displays the published requirement, comparison, value and unit. It does not ask the supplier to interpret an anonymous PDF paragraph.

### 9.2 Services and acceptance responses

- Each service row receives supplier confirmation, offered completion date and price-schedule link.
- Each acceptance row is carried as a contract obligation; the supplier confirms acceptance with the Tender submission.
- Supporting materials remain attached to their linked rows and authorised treatment.

### 9.3 Evaluation contract

Evaluation receives:

- one eligibility/evidence checklist;
- one pass/fail check for every mandatory technical requirement ID;
- offered values and evidence references;
- arithmetic and price totals from the supplier response;
- fixed stage order; and
- no hidden or evaluator-created criteria.

A technical failure identifies the exact published requirement ID and reason.

### 9.4 Contract-obligation projection

Contract formation receives awarded values linked to:

- each Requisition item and quantity;
- each mandatory technical requirement;
- each service and completion date;
- each warranty/support obligation;
- each acceptance requirement;
- agreed delivery and price rows; and
- the officer's finite contract parameters.

No obligation is reconstructed by copying free text from the rendered Tender.

## 10. Readiness and lifecycle

### 10.1 Readiness

Readiness is a deterministic check, not a workflow state. A Draft may be incomplete; submission may not.

A Tender is ready only when:

- the source `AuthorisedRequisitionHandoff v1.2` is valid, unrevoked and not consumed by another Tender;
- the stored Requisition Version and digest still match the handoff;
- template `IT-EQUIPMENT-OPEN-V1` version 1.1 is available and its source and bundle digests match;
- the Requisition passes every compatibility test in section 6.4;
- every required officer control is complete and valid;
- issue, clarification, meeting and submission dates are in the required order;
- the inherited snapshot contains every item, technical, service, acceptance and supporting-material row in the handoff, with unchanged IDs and values;
- the goods, delivery, related-services and price schedules reconcile exactly to the inherited rows;
- every published technical requirement has one supplier-response definition, one evaluation mapping and one contract-obligation mapping;
- every evidence requirement is visible and linked to an inherited structured row;
- supporting files are readable, digest-verified and published only with their authorised treatment;
- security and contract values are internally consistent;
- the Invitation and complete issued Tender render with no missing section, unresolved insertion, duplicate value or primary unstructured requirement; and
- the canonical package digest can be produced.

Findings are **Blocking** or **Warning**. Blocking findings prevent submission. Warnings remain visible to the approver; there is no dismissal control.

### 10.2 Lifecycle

| Current state | Action | Actor | Result |
|---|---|---|---|
| Eligible handoff | Prepare Tender | Procurement Officer | Creates or returns the one Draft and records handoff consumption idempotently. |
| Draft | Save | Procurement Officer | Saves valid incomplete or complete Draft data; creates no decision task. |
| Draft | Submit for approval | Procurement Officer | Requires zero Blocking findings; locks the Version and creates one Head of Procurement Function task. |
| Submitted | Return for correction | Head of Procurement Function | Preserves the submitted Version and creates a copied Draft successor with one required reason. |
| Submitted | Approve for publication | Head of Procurement Function | Creates the immutable approved Version, decision, rendered package and publication handoff atomically. |
| Approved | Reopen before publication | Head of Procurement Function | Allowed only while the handoff is unconsumed; records a reason, cancels that ready handoff and creates a copied Draft successor. |

No submitted, approved or handed-off Version is edited in place. Once publication consumes the handoff, correction belongs to the later publication/addendum process.

### 10.3 Segregation and approval

The Procurement Officer who prepared or submitted a Version cannot approve it. The Head of Procurement Function is the single Tender Preparation approver. This module adds no approval after that role and does not involve the Accounting Officer in this lifecycle.

### 10.4 Upstream correction

An inherited requirement is never edited in Tender Preparation.

If correction is needed:

1. the Procurement Officer selects **Request upstream correction** and gives a required reason;
2. the server closes the current Draft, Returned or Submitted Version as `Upstream correction required`, preserving it;
3. the existing Requisition-consumption link is released only through the controlled cross-module command and only before publication approval;
4. Requisitions creates and authorises a corrected successor under REQ-CHG-001 v1.2;
5. Tender Preparation consumes the new handoff and creates a new Tender Version linked to the prior stopped Version; and
6. all schedules, supplier-response definitions and renders are regenerated from the new immutable snapshot.

There is no direct edit, local override, pasted correction or retained stale row. If the correction changes product compatibility, the new handoff may be rejected as unsupported.

### 10.5 Core invariants

- One authorised handoff has at most one active Tender consumption.
- Every Tender Version binds one Requisition Version and one template release.
- Inherited identifiers and content do not change inside Tender Preparation.
- Each published technical requirement has exactly one response, evaluation and contract mapping.
- Approval commits the decision, package and handoff together or commits none.
- Repeated commands with the same idempotency key and payload return the same result.

## 11. Services, commands and errors

### 11.1 Reads

| Service | Required result |
|---|---|
| `GetTenderPreparationWorkspace` | Eligible handoffs, own Drafts, protected approval tasks and neutral publication status in exact scope. |
| `GetTenderCompatibility` | Typed version, product and boundary result; no mutation and no free-text bypass. |
| `GetTenderEditor` | One projection containing binding, immutable requirements, officer values, generated schedules, validation and permitted actions. |
| `GetTenderApprovalTask` | Exact submitted Version, complete renders, mappings, readiness and release evidence. |
| `GetApprovedTender` | Immutable approved package and neutral publication-consumption status. |
| `GetTenderHistory` | Versions, decisions, upstream-correction lineage and handoff evidence. |

Reads create no Tender, Version, task, decision, render or handoff.

### 11.2 Commands

| Command | Minimum effect |
|---|---|
| `PrepareTender` | Rechecks the v1.2 handoff and compatibility, creates or returns one Draft, binds digests and records consumption atomically. |
| `SaveTenderDraft` | Accepts only the Task 1, 4 and 5 fields defined here; rejects inherited, generated, hidden and unknown fields. |
| `AddTenderEvidenceRequirement` / `UpdateTenderEvidenceRequirement` / `RemoveTenderEvidenceRequirement` | Mutates one valid Draft evidence row linked to an inherited visible ID. |
| `RunTenderReadiness` | Rebuilds schedules and renders, validates the exact Draft and stores findings against its digest. |
| `SubmitTenderForApproval` | Re-runs readiness, locks the Version and creates one approval task. |
| `ReturnTenderForCorrection` | Requires one actionable reason; preserves the submitted Version and creates a copied Draft successor. |
| `ApproveTenderForPublication` | Rechecks role, segregation, readiness, render and digests; commits approval, package and handoff atomically. |
| `ReopenApprovedTender` | Requires an unconsumed publication handoff and reason; preserves the approved Version and creates a Draft successor. |
| `RequestTenderUpstreamCorrection` | Preserves the current Version and starts only the controlled section 10.4 route. |

Every write accepts an expected record version and idempotency key. The server derives actor, scope, state, totals, template binding, digests and permitted actions.

### 11.3 Errors

| Code | Meaning and user treatment |
|---|---|
| `TPR_NOT_FOUND` | Tender is absent or not visible. Show **Tender not found**. |
| `TPR_ROLE_REQUIRED` | Required native business role is absent. Name the role. |
| `TPR_SCOPE_DENIED` | PE/FY scope denied. Do not reveal record existence. |
| `TPR_HANDOFF_INVALID` | Handoff is missing, revoked, wrong version or changed. Return to workspace. |
| `TPR_HANDOFF_CONSUMED` | Handoff already belongs to another Tender. Offer **View Tender** only when authorised. |
| `TPR_PRODUCT_UNSUPPORTED` | Requisition does not fit this product. Stop with no free-text bypass. |
| `TPR_TEMPLATE_UNAVAILABLE` | Installed template or digest is unavailable. Create nothing. |
| `TPR_CONTROL_INVALID` | Value violates the exact control type, range or options. Show the field. |
| `TPR_INHERITED_EDIT` | Payload tried to change inherited or generated content. Reject it. |
| `TPR_MAPPING_INCOMPLETE` | A published structured row lacks a required downstream mapping. Block readiness. |
| `TPR_FILE_INVALID` | Linked file failed security, readability, digest or treatment checks. |
| `TPR_BLOCKING_FINDINGS` | Submission or approval has Blocking findings. Return exact links. |
| `TPR_STALE_VERSION` | Record changed. Reload the same record. |
| `TPR_SOD_BLOCKED` | Preparer attempted approval. Deny the transition. |
| `TPR_PUBLICATION_CONSUMED` | Reopen is no longer permitted. Use the later addendum process. |
| `TPR_IDEMPOTENCY_CONFLICT` | Same key was reused with a different payload. Stop safely. |

## 12. UI architecture and routes

Use Vue 3 single-file components inside Frappe Desk. Reuse the KenTender shell, context selector, components and tokens. Do not create an STD workspace or import design-tool runtime code.

| Surface | Route | Purpose |
|---|---|---|
| Tender Preparation workspace | `/app/tender-preparation` | Eligible handoffs, own Drafts, approval tasks and recent Tenders. |
| Start Tender | `/app/tender-preparation/new/{handoff_id}` | Confirm the one compatible product and prepare/reuse a Draft. |
| Tender editor | `/app/tender-preparation/{tender_id}` | Complete the five fixed tasks and readiness. |
| Approval task | `/app/tender-preparation/task/{task_id}` | HOPF reads, returns or approves the complete locked Version. |
| Approved Tender | `/app/tender-preparation/{tender_id}/approved` | Read approved package, digest and publication status. |

Opening a route creates nothing. Only **Prepare Tender** invokes creation.

## 13. Static Claude Design contract

### 13.1 Global rules

Create only the screens and dialogs listed below at 1440 × 1024. Use the exact control types, labels, editability and fixture values in this document. Do not add dashboards, charts, comments, attachment drop-zones, template selectors, configuration, criteria builders, reviewers, approvals or fields.

Read-only inherited values appear as plain values or tables with the caption **From authorised Requisition**. They must not appear as editable or disabled text inputs. Editable fields use their stated control. Supplier values show **Completed by Tenderer**.

### 13.2 Shared KEBS fixture

| Context | Exact value |
|---|---|
| Procuring Entity | Kenya Bureau of Standards |
| Financial Year | FY 2026/27 |
| Department | Coast Region — Administration and ICT |
| Plan Item | `PPI-KEBS-2026-ICT-001` — Supply and delivery of ICT equipment |
| Requisition | `REQ-KEBS-2026-ICT-0001` · Authorised · Version 1 |
| Handoff | `AuthorisedRequisitionHandoff v1.2` · unconsumed |
| Method | Open Tender |
| Authorised value | KES 4,875,000.00 — internal only |
| Latest delivery | 30 December 2026 |
| Package | 3 items · 19 technical requirements · 3 related services · 5 acceptance requirements · 1 informational material |
| Tender | `TND-KEBS-2026-0001` |
| Template | IT Equipment — Open Tender · Version 1.1 |
| Procurement Officer | Alice Wambui · `alice.wambui@kebs.example.test` |
| Head of Procurement Function | Samuel Otieno · `samuel.otieno@kebs.example.test` |

Equipment rows:

| Item | Quantity | Unit | Delivery location | Latest delivery | Warranty |
|---|---:|---|---|---|---:|
| Business laptops | 25 | Each | KEBS Coast Region Office, Mombasa | 30 Dec 2026 | 36 months |
| Desktop computers with monitors | 15 | Each | KEBS Coast Region Office, Mombasa | 30 Dec 2026 | 36 months |
| Business tablets | 10 | Each | KEBS Coast Region Office, Mombasa | 30 Dec 2026 | 24 months |

The fixture must use the exact stable row IDs and content from the approved REQ-CHG-001 v1.2 fixture. Do not create a second abbreviated technical dataset.

### 13.3 TPR-DES-01 — Tender Preparation workspace

Title **Tender Preparation**. Subtitle **Prepare Tenders from authorised Procurement Requisitions.**

Sections:

1. **Ready to prepare** — one row for `REQ-KEBS-2026-ICT-0001`, Open Tender, 3 items, required by 30 Dec 2026, action **Prepare Tender**.
2. **My Tenders** — Draft, Returned and Approved records the user may see.
3. **Approval tasks** — shown only to the Head of Procurement Function.

Do not show a value dashboard, STD Library link or create-without-Requisition action.

### 13.4 TPR-DES-02 — Start Tender

Dialog title **Prepare IT-equipment Tender**.

Show read-only Requisition, requirement, package counts, method, template version and PPRA Goods STD source. Notice: **This template release is fixed for this Tender. A later release will not change it.**

Buttons: **Cancel** and **Prepare Tender**. Show no alternative template, package, schema, manifest or configuration control.

### 13.5 TPR-DES-03 — Five-task workspace

Header:

- eyebrow **TENDER PREPARATION**;
- title **Supply and delivery of ICT equipment**;
- quiet line **TND-KEBS-2026-0001 · REQ-KEBS-2026-ICT-0001 · Version 1**; and
- status **Draft**.

Left navigation:

| Task | Exact fixture state |
|---|---|
| 1. Tender details | Complete |
| 2. Goods and requirements | Complete · 3 items · 19 technical rows |
| 3. Price schedule | Complete · Generated from 3 items and 3 services |
| 4. Submission and evaluation | Complete |
| 5. Contract terms | Complete |
| Review and readiness | Ready · 0 Blocking · 1 Warning |

The selected task uses the controls in section 8. Footer: **Save draft** and **Continue**; Task 5 uses **Review Tender**.

Task 1 fixture values:

| Field | Exact value |
|---|---|
| Tender title | Supply and delivery of business ICT equipment |
| Issue date | 8 Oct 2026 |
| Clarification deadline | 19 Oct 2026, 17:00 EAT |
| Submission deadline | 29 Oct 2026, 11:00 EAT |
| Tender validity | 120 days |
| Tender security | KES 300,000.00 |
| Pre-tender meeting | No |

Task 2 shows six read-only panels: **Goods and delivery**, **Technical requirements**, **Warranty and support**, **Related services**, **Acceptance requirements**, and **Supporting materials**. Each table shows its stable IDs. The informational room-layout material is linked but creates no obligation. The sole action is **Request upstream correction**.

Task 3 shows generated supplier price rows for all three items and applicable priced services. Quantity and units are inherited. Unit price and tax show **Completed by Tenderer**; line total and Tender total show **Calculated from Tenderer response**. No fixture or authorised value appears in these cells.

Task 4 fixture values:

- Manufacturer authorisation required: **Yes**;
- Product datasheets or brochures required: **Yes**;
- Warranty confirmation required: **Yes — always required**;
- Past supply experience required: **Yes**;
- Minimum comparable contracts: **2**;
- Experience period: **5 years**;
- After-sales support evidence required: **Yes**; and
- After-sales evidence: **Kenya service-centre details and escalation contacts**.

Task 5 fixture values:

- Inspection and acceptance location: **KEBS Coast Region Office, Mombasa**;
- Payment timing: **30 days**;
- Performance security required: **Yes**;
- Performance security: **10%**;
- Delay damages: **0.5% per week**, maximum **10%**; and
- Contract contact office: **KEBS Contracts Office**.

### 13.6 TPR-DES-04 — Review and readiness

Title **Review Tender**. Description **Resolve Blocking findings and review the complete Tender before submission.**

Summary:

| Check | Result |
|---|---|
| Source handoff | Complete · v1.2 · digest verified |
| Tender details | Complete |
| Inherited requirements | Complete · 3 items · 19 technical · 3 services · 5 acceptance |
| Supplier-response mappings | Complete · 19 of 19 |
| Evaluation and contract mappings | Complete |
| Price schedule | Complete · generated |
| Rendered Invitation and Tender | Complete |

Show **0 Blocking** and **1 Warning**. Warning: **Confirm that manufacturer authorisation is proportionate for every listed item.**

Actions: **Preview Invitation**, **Preview complete Tender**, and **Submit for approval**.

### 13.7 TPR-DES-05 — Tender approval

Status **Submitted for approval**. Show the immutable Requisition summary, all five task summaries, structured requirements, mappings, readiness, complete renders and quiet release panel. No value is editable.

Actions: **Return for correction** and **Approve for publication**.

### 13.8 TPR-DES-06 — Approved Tender

Status **Approved for publication**. Notice **This Tender is approved. The publication package is ready.**

Show approved Version, approver/time, Requisition and template digests, package digest, both renders, structured response/evaluation/contract mappings and publication-handoff status. There is no edit action. **Reopen before publication** appears only for the Head of Procurement Function while the handoff is unconsumed.

### 13.9 Dialogs and common states

**Return for correction** requires **Correction required**, fixture: **Confirm whether manufacturer authorisation is necessary for the tablet item and update the evidence requirement.**

**Request upstream correction** requires **Reason**, fixture: **The authorised technical requirement for tablet battery life must be corrected in the Requisition.** Notice: **Tender Preparation cannot edit an authorised requirement. This Tender Version will be preserved.**

**Reopen before publication** requires **Reason for reopening**, fixture: **The submission deadline must be corrected before publication.**

| State | Message | Action |
|---|---|---|
| No eligible handoffs | No authorised Requisitions are ready for Tender Preparation. | None |
| Unsupported requirement | This Requisition is not supported by the IT-equipment Tender pattern. | Return to workspace |
| Handoff consumed | This Requisition is already linked to a Tender. | View Tender, if authorised |
| Source changed/revoked | The source Requisition is no longer available for Tender Preparation. | Return to workspace |
| Template unavailable | This Tender template is not available for new Tenders. | Return to workspace |
| Stale write | Another user changed this Tender. Reload before continuing. | Reload |
| Load failure | Tender Preparation could not be loaded. | Try again |

## 14. Functional interaction contract

- Step navigation changes the displayed task without saving implicitly.
- **Save draft** validates only visible and applicable editable controls, then refreshes all generated projections.
- **Continue** saves the task and opens the next task only on success.
- Row IDs open a read-only detail drawer showing source, rule and downstream use.
- **Preview** always renders from the server's current canonical projection; browser HTML is never authoritative.
- **Submit**, **Return**, **Approve**, **Reopen** and **Request upstream correction** require a confirmation dialog and disable repeated clicks while pending.
- Browser back, refresh and retry do not duplicate records or decisions.
- Direct routes, lists, files and commands enforce the same native role and scope rules.
- Validation focuses the first invalid control and provides a link from every finding to its task or row.

## 15. Audit and evidence

Record actor, native role, PE/FY scope, command, record and Version IDs, expected/actual record versions, idempotency key, time, before/after digest and result for every write.

Retain immutable evidence for:

- Requisition handoff receipt and consumption;
- template source, version and bundle digest;
- inherited snapshot and stable IDs;
- every Tender Version and readiness result;
- every render and mapping digest;
- return, approval, reopen and upstream-correction decisions;
- publication handoff and consumption; and
- private supporting-file digest and authorised treatment.

Audit logging must not expose confidential internal values or private file contents to unauthorised users.

## 16. Deterministic KEBS walkthrough fixture

### 16.1 Source package

Seed and consume the exact authorised `REQ-KEBS-2026-ICT-0001` v1.2 handoff:

- 3 equipment items totalling 50 Each;
- 19 confirmed technical-requirement rows;
- package warranty plus item warranty/support facts;
- 3 related-service rows;
- 5 objective acceptance rows; and
- 1 informational room-layout material with its authorised row links and digest.

No technical specification PDF substitutes for this package. A generated PDF may be included only as a convenience rendering of the same structured content and digest.

### 16.2 Lifecycle

| Event | Actor | Exact time and result |
|---|---|---|
| Handoff consumed; Draft Version 1 created | Alice Wambui | 5 Oct 2026, 09:00 EAT |
| Five tasks completed | Alice Wambui | 5 Oct 2026, 11:30 EAT |
| Readiness run | Alice Wambui | 5 Oct 2026, 11:35 EAT · 0 Blocking · 1 Warning |
| Submitted | Alice Wambui | 5 Oct 2026, 11:40 EAT |
| Returned; Draft Version 2 created | Samuel Otieno | 5 Oct 2026, 14:00 EAT |
| Corrected and resubmitted | Alice Wambui | 6 Oct 2026, 09:15 EAT |
| Approved | Samuel Otieno | 6 Oct 2026, 10:00 EAT |
| Publication handoff ready | System | 6 Oct 2026, 10:00 EAT |

The fixture also contains one stopped Tender Version that requests an upstream correction and one corrected Requisition successor handoff. This proves that inherited technical content is corrected upstream rather than overwritten.

Seeds and retries must not duplicate a Tender, Version, task, decision, render, response definition, mapping or handoff.

## 17. Acceptance contract

| ID | Required result |
|---|---|
| TPR-AC-001 | Only an authorised, unconsumed v1.2 handoff that passes every compatibility test can create a Tender. |
| TPR-AC-002 | Preparing twice from the same handoff returns the same Tender and creates no duplicate. |
| TPR-AC-003 | One Tender consumes one Requisition handoff; no grouping or lotting control exists. |
| TPR-AC-004 | Every Version binds immutable Requisition, official-source and bundle digests. |
| TPR-AC-005 | No UI or API permits STD text, schema, mapping, workflow or validation configuration. |
| TPR-AC-006 | Procurement Officer input is limited to the exact Task 1, 4 and 5 controls. |
| TPR-AC-007 | Every inherited item, technical, service, acceptance and material row retains its stable Requisition ID and value. |
| TPR-AC-008 | Inherited and generated values are read-only in UI and rejected in write payloads. |
| TPR-AC-009 | Task 2 has no technical-document upload as the primary requirement and no editable requirement control. |
| TPR-AC-010 | Section V is generated from structured rows, not interpreted from an attachment. |
| TPR-AC-011 | Every operative supporting file links to a structured row and cannot create the only statement of an obligation. |
| TPR-AC-012 | Goods, delivery, services and price schedules reconcile to the Requisition without duplicate entry. |
| TPR-AC-013 | Task 3 contains no officer-entered or fixture supplier price. |
| TPR-AC-014 | Every published technical requirement has exactly one typed supplier-response definition. |
| TPR-AC-015 | Every published technical requirement has one pass/fail evaluation mapping and one contract mapping. |
| TPR-AC-016 | Every service, warranty/support and acceptance obligation is traceable into the Tender and contract projection. |
| TPR-AC-017 | An additional evidence row is rejected unless linked to a visible inherited requirement. |
| TPR-AC-018 | No evidence row creates a hidden criterion or unpublished threshold. |
| TPR-AC-019 | Boolean and finite-choice controls reject free text and unknown values. |
| TPR-AC-020 | Conditional hidden fields are not accepted in payloads while inapplicable. |
| TPR-AC-021 | Currency, location and office references accept only their stated fixed or governed sources. |
| TPR-AC-022 | Readiness requires zero Blocking findings and complete deterministic renders and mappings. |
| TPR-AC-023 | The preparing Procurement Officer cannot approve the same Version. |
| TPR-AC-024 | The Head of Procurement Function is the only approval level in this module. |
| TPR-AC-025 | Return preserves the submitted Version and creates a copied Draft successor. |
| TPR-AC-026 | Approval commits decision, approved Version, package and publication handoff atomically. |
| TPR-AC-027 | Reopen is permitted only before publication consumption and never edits the approved Version. |
| TPR-AC-028 | Upstream correction preserves the stopped Tender Version and accepts only a new authorised Requisition successor. |
| TPR-AC-029 | A later Requisition or template release does not alter an existing bound Version. |
| TPR-AC-030 | Cross-PE/FY access and direct routes fail without revealing the record. |
| TPR-AC-031 | The installed bundle identifies the exact official source, coverage register, version and digests. |
| TPR-AC-032 | A clean install creates exactly one read-only version 1.1 registry row; reinstall creates no duplicate. |
| TPR-AC-033 | Missing release evidence or a digest mismatch prevents new Tender binding. |
| TPR-AC-034 | No Desk or ordinary administrator action can edit the installed template release. |
| TPR-AC-035 | Invitation and issued Tender remain separate outputs with separate digests. |
| TPR-AC-036 | Complex IT and Works Requisitions are rejected, not forced through this product. |
| TPR-AC-037 | The KEBS fixture reproduces the same rows, findings, renders, mappings and digests on every clean run. |
| TPR-AC-038 | The approved publication handoff contains the structured supplier-response, evaluation and contract contracts. |
| TPR-AC-039 | A generated convenience document never becomes the authoritative technical source. |
| TPR-AC-040 | No custom capability profile or operational-scope assignment is required for this module. |

## 18. Test and smoke contract

Implement tests in this order:

1. pure tests for compatibility, control types/ranges, date order, evidence links and mapping completeness;
2. domain tests for immutable bindings, version copying, segregation, upstream correction and atomic approval;
3. permission tests for roles, scopes, direct routes and private files;
4. render tests for structured Section V, supplier-response schema and Invitation/issued-Tender separation;
5. contract tests against `AuthorisedRequisitionHandoff v1.2`; and
6. browser smoke using the exact KEBS fixture.

| Smoke | Proof |
|---|---|
| TPR-SMOKE-01 | Consume the authorised KEBS v1.2 handoff and create one bound Draft. |
| TPR-SMOKE-02 | Verify all 3 items, 19 technical rows, 3 services, 5 acceptance rows and 1 material appear read-only. |
| TPR-SMOKE-03 | Attempt to change an inherited quantity or technical value through the API; reject it. |
| TPR-SMOKE-04 | Verify Section V and all downstream mappings retain every stable ID. |
| TPR-SMOKE-05 | Verify Task 3 contains only blank supplier price controls and generated calculations. |
| TPR-SMOKE-06 | Send free text to a Boolean or finite choice; reject it. |
| TPR-SMOKE-07 | Add evidence without a visible row link; reject it. |
| TPR-SMOKE-08 | Submit with one technical response/evaluation/contract mapping removed; readiness blocks. |
| TPR-SMOKE-09 | Return the Version; verify the submitted Version remains unchanged and Draft Version 2 exists. |
| TPR-SMOKE-10 | Attempt self-approval as Alice; deny it. Approve as Samuel. |
| TPR-SMOKE-11 | Verify approval creates one immutable package and publication handoff; retry creates no duplicate. |
| TPR-SMOKE-12 | Reopen before consumption; permit. Mark consumed; retry reopen; deny. |
| TPR-SMOKE-13 | Request upstream correction; verify no inherited row changes and a new handoff is required. |
| TPR-SMOKE-14 | Alter the bundle after digest registration; make the template unavailable for new Tenders. |
| TPR-SMOKE-15 | Present a complex ERP Requisition and a Works Requisition; reject both without creating records. |
| TPR-SMOKE-16 | Compare every screen control and source label against sections 8 and 13. |

## 19. Required walkthrough before implementation

Use one practising Procurement Officer, one requesting-department representative and the Head of Procurement Function.

Run the KEBS fixture from authorised handoff through approval. Inspect the generated Invitation, complete Tender, supplier-response controls, evaluation mappings and contract obligations. Then request one upstream technical correction and prove that it cannot be made in Tender Preparation.

Record only:

- time taken;
- unclear questions;
- duplicate entry;
- missing or wrongly carried requirements;
- unnecessary fields;
- incorrect downstream mappings; and
- blockers with a named correction owner.

The result is **GO**, **SIMPLIFY FURTHER** or **REJECT**. This document is approved. A **GO** walkthrough authorises implementation, provided the template 1.1 release evidence also exists before code binds it.

## 20. Implementation constraints

If authorised:

- implement in `kentender_procurement` with ordinary Frappe records, Workflow permissions, User Permissions, private Files, transactions and audit;
- use one code-owned IT-equipment template, not a generic engine;
- implement the v1.2 handoff consumer before building the Tender screens;
- keep the reviewed bundle under version control with one idempotent loader and read-only registry;
- use one canonical serializer for preview, readiness, digest, mappings and handoff;
- keep authority, scope, state, validation, totals, mappings and approval in typed server-side code;
- reuse the existing Vue 3/Frappe Desk shell and KenTender components;
- do not use parser/OCR, inferred-schema logic, legacy generic runtime objects or compatibility layers; and
- remove any field or step with no present validation, Tender, response, evaluation, contract or publication use.

Do not add an STD Library administration screen, Configurator or reviewer role, runtime manifest activation, schema/clause editor, generic criterion designer, AI/PDF parsing in production, custom permission layer, technical-review workflow, or future fields hidden behind flags.

## 21. Cutover

- Proposed v0.3 Drafts and fixtures based on a primary technical PDF are not migrated into this model.
- Recreate the deterministic KEBS Tender from the approved v1.2 Requisition handoff and template 1.1.
- Do not support dual reads, fallback PDF requirements or mixed v1.0/v1.1 mappings.
- Preserve prior curated source evidence and v0.3 documents as history only.
- No production Tender is created until the installed version 1.1 bundle and contract tests pass.

## 22. Traceability and precedence

This document conforms to:

1. **E2E-REQ-001 v0.2 — Approved**, for the structured Departmental Needs → Planning → Requisition → Tender control contract;
2. **REQ-CHG-001 v1.2 — Approved**, for the complete immutable handoff and stable requirement IDs;
3. **STD-ST-001 v0.3 — Approved**, for productised code-owned Tender templates and no STD Configuration module; and
4. **STD-TPL-001 v0.3**, for the reviewed PPRA Goods source, locked text, forms and release evidence, subject to the version 1.1 correction in section 6.2.

Where earlier Tender Preparation or template material treats an attachment as the primary technical requirement, this v0.4 structured boundary controls. The official PPRA source controls locked standard wording. REQ-CHG-001 controls authorised business requirements. This document controls the Tender Preparation journey and downstream mappings.

## 23. Approval effect and next action

TPR-CHG-001 v0.4 is approved as the complete successor to proposed v0.3 and is the single Tender Preparation requirements document for the first IT-equipment slice. Version 0.3 remains historical and must not be consulted for implementation.

Approval does not permit an incomplete template or improvised handoff. The next action is to release `IT-EQUIPMENT-OPEN-V1` version 1.1 exactly as section 6.2 defines, run the deterministic KEBS walkthrough and record its result. Implementation may begin only after a **GO** result and complete release evidence.
