# E2E-REQ-001 — Departmental Requirement to Tender Preparation Control Contract

| Item | Value |
|---|---|
| Version | 0.2 |
| Date | 28 August 2026 |
| Status | Approved |
| Change type | Complete consolidated successor to approved v0.1 |
| First product | Straightforward IT equipment |
| Authority | Controls all subsequent first-slice specifications and implementation packs |

## 1. Decision

KenTender will carry requirements from the requesting department to the issued Tender as structured system data.

An attachment may explain or support a requirement. It must not be the only place where a supplier obligation, bidder response, evaluation rule or contract deliverable is stated.

The first implementation will not use a generic Requirements Composer, an STD Configuration module or user-defined schemas. It will use one small, code-owned **IT Equipment Requirement Package**.

## 2. Purpose

This document closes the requirement-lineage gap between:

1. Departmental Needs;
2. Departmental Procurement Planning;
3. consolidated Procurement Planning;
4. Procurement Requisitions; and
5. Tender Preparation.

It defines what information moves forward, who may change it and how corrections work. It is a control contract for revising the affected module documents. It is not, by itself, an implementation pack.

## 3. First-slice boundary

The first slice supports:

- one Procuring Entity, Financial Year and requesting department;
- one Active Plan Item;
- one authorised Requisition;
- one straightforward IT-equipment Tender;
- one award package;
- goods supplied in Kenya Shillings;
- pass/fail technical compliance; and
- the released `IT-EQUIPMENT-OPEN-V1` Tender template.

It excludes custom software, major integration, data migration, complex implementation projects, multiple award packages, multiple currencies and cross-department Requisition grouping.

## 4. The complete flow

| Stage | Main action | Controlled output |
|---|---|---|
| Departmental Need | Department describes the need and expected operational result | Accepted Need, or a recorded decision that no separate Need was required |
| Departmental Plan | Department identifies what it expects to procure | Departmental plan lines with stable source IDs |
| Procurement Planning | Procurement consolidates, schedules, costs and selects the proposed method | One approved Active Plan Item with preserved source-line lineage |
| Requisition | Department requests a precise drawdown and completes the fixed IT requirement form | One immutable authorised Requisition handoff |
| Tender Preparation | Procurement confirms template fit and adds tender-facing parameters | One approved publication package |

A direct Departmental Plan entry remains allowed when a separate Departmental Need would add no value. The Plan entry must still contain the same minimum need, result, quantity and timing information.

The information becomes more detailed as the transaction advances. Departmental Needs and Planning do **not** require a completed technical specification. The complete IT Equipment Requirement Package is required only when the Requisition is submitted. This prevents early planning work from becoming a second Requisition process.

## 5. Ownership of information

| Information | Owner | Rule |
|---|---|---|
| Business need and expected result | Requesting department | Procurement may return it for clarification but must not rewrite it silently. |
| Items, quantities and units | Requesting department | Inherited by Requisition and Tender; no manual re-entry downstream. |
| Minimum technical characteristics | Requesting department | Entered as structured requirement rows. |
| Delivery place and latest acceptable date | Requesting department | May be narrowed by Procurement only through a visible, justified change that does not exceed the authorised boundary. |
| Warranty and support need | Requesting department | States the operational need; Procurement determines the tender evidence and contract treatment. |
| Related services and acceptance needs | Requesting department | Entered as structured rows where applicable. |
| Budget, package, schedule and procurement method | Procurement Planning and Budget | Inherited downstream as read-only approved facts. |
| Supplier qualification and evidence | Procurement | Added during Tender Preparation and linked to a visible published requirement. |
| Evaluation sequence, Tender security and contract conditions | Released product plus Procurement | Fixed by the released template or selected from its closed choices. |
| Standard Tender text and bidder-response structure | Released product | Code-owned, versioned and not editable through Desk. |

The department is not expected to define supplier qualification, evidence forms, Tender security, evaluation logic or contract clauses.

Procurement may help the department express a requirement using the fixed controls, and a technical officer may contribute where needed. The department remains responsible for confirming its operational need and minimum characteristics. This collaboration does not create another reviewer role or allow Procurement to substitute its own requirement silently.

## 6. Stable requirement lineage

Every material row receives a stable identifier when it first enters the system. Later stages retain that identifier rather than copying anonymous text.

| Identifier | Created at | Carried to |
|---|---|---|
| `source_line_id` | Need or direct Departmental Plan entry | Plan Item, Requisition and Tender |
| `plan_item_line_id` | Approved Plan Item | Requisition and Tender |
| `requisition_item_id` | Requisition | Tender goods row, price schedule and contract schedule |
| `technical_requirement_id` | Requisition | Published technical schedule, bidder response and evaluation |
| `service_requirement_id` | Requisition | Published service schedule, bidder response and contract obligation |
| `acceptance_requirement_id` | Requisition | Published acceptance schedule and contract obligation |

The system must be able to show the source of every published requirement without relying on matching descriptions.

## 7. IT Equipment Requirement Package

### 7.1 Package summary

The Requisition contains one package with:

| Field | Control |
|---|---|
| Requirement title | Required single-line text, maximum 160 characters |
| Business need | Required plain text, maximum 1,000 characters |
| Expected operational result | Required plain text, maximum 1,000 characters |
| Delivery location | Required Link to an authorised PE location, with a controlled address snapshot |
| Latest acceptable delivery date | Required date within the approved Plan schedule |
| Related services required | Required Yes/No |
| Supporting materials | Optional governed files; rules in section 8 |

### 7.2 Equipment items

At least one item is required.

| Field | Control |
|---|---|
| Item ID | System-generated, read-only |
| Equipment category | Required Select from the released list: `Laptop`, `Desktop computer`, `Monitor`, `Tablet`, `Printer`, `Scanner`, `Network equipment`, `Power-protection equipment`, `Other IT equipment` |
| Item name | Required single-line text, maximum 120 characters |
| Quantity | Required positive whole number for the first release |
| Unit | Read-only `Each` for the first release |
| Intended use | Required plain text, maximum 500 characters |
| Delivery location | Inherited from package; an authorised PE location may be selected per row when different |
| Latest delivery date | Inherited from package; may be earlier, never later |

Selecting `Other IT equipment` requires a specific item name. It does not allow the user to create a new equipment category or template.

### 7.3 Technical requirement rows

Each enforceable technical characteristic is a separate row linked to one equipment item or to all items.

| Field | Control |
|---|---|
| Requirement ID | System-generated, read-only |
| Applies to | Required Link to one item or `All items` |
| Characteristic | Required Select from the released catalogue for that category, with `Other essential characteristic` as a controlled escape |
| Requirement | Required value using the control assigned to the characteristic: text, integer, decimal, Yes/No or closed Select |
| Unit | Fixed by the characteristic where applicable; read-only |
| Comparison | Fixed by the characteristic: `Minimum`, `Maximum`, `Exact`, `Required` or `One of` |
| Mandatory | Read-only `Yes` for the first release |
| Reason | Required only for `Other essential characteristic`; maximum 300 characters |

Examples are `Minimum memory = 16 GB`, `Minimum storage = 512 GB`, `Storage type = SSD` and `Minimum warranty = 36 months`.

Free text is allowed only where a closed value cannot truthfully express the requirement. It does not permit a hidden evaluation criterion.

The released product should offer sensible characteristic rows for the selected equipment category. The author selects the rows that apply and enters their values; the author does not design the form. Copying a prior package may create a Draft starting point, but every copied row must be visibly reconfirmed before submission.

### 7.4 Warranty and support

| Field | Control |
|---|---|
| Minimum warranty period | Required positive integer in months |
| On-site support required | Required Yes/No |
| Maximum response time | Duration control; required only when on-site support is Yes |
| Manufacturer support required | Required Yes/No |
| Service location constraint | Select: `None`, `Within Kenya`, `At delivery location`; required |
| Support description | Optional plain text, maximum 500 characters; may clarify but not contradict the controlled fields |

The department states the service outcome it needs. Tender Preparation decides what proportionate supplier evidence proves it.

### 7.5 Related services

Shown only when related services are required.

| Field | Control |
|---|---|
| Service ID | System-generated, read-only |
| Service type | Required Select: `Delivery`, `Installation`, `Configuration`, `Data transfer`, `User orientation`, `Training`, `Testing`, `Other` |
| Applies to | Required Link to one item or `All items` |
| Required result | Required plain text, maximum 500 characters |
| Quantity or coverage | Required single-line text, maximum 120 characters |
| Completion date | Required date not later than the package date |
| Acceptance evidence | Required Select: `Delivery note`, `Installation certificate`, `Test result`, `Attendance record`, `Completion certificate`, `Other stated record` |

Complex implementation or integration discovered here makes the Requisition incompatible with the first template.

### 7.6 Acceptance requirements

At least one acceptance row is required.

| Field | Control |
|---|---|
| Acceptance ID | System-generated, read-only |
| Applies to | Required Link to one item, one related service or `All items` |
| Check | Required Select: `Quantity`, `Physical condition`, `Required specification`, `Functional test`, `Installation complete`, `Documents received`, `Other objective check` |
| Pass condition | Required plain text, maximum 500 characters |
| Evidence | Required Select: `Inspection record`, `Test result`, `Delivery note`, `Certificate`, `Other stated record` |

Acceptance rows must describe an observable pass condition. “Satisfactory” on its own is invalid.

## 8. Supporting materials

Supporting materials may include drawings, photographs, room layouts, network diagrams, existing architecture, standards extracts, site reports and product-environment information.

They are governed as follows:

1. A file must have a title, document type, purpose and version.
2. The file must be private and immutable after Requisition authorisation.
3. Every file must link to the package or to specific structured rows.
4. A file may clarify context or provide detail.
5. A file may not be the only statement of an enforceable obligation.
6. If a drawing, standard or schedule creates an obligation, the obligation must also be represented by a structured row that cites the file.
7. The Tender must tell bidders whether each file is informational or forms part of the requirement.
8. Bidder compliance is recorded electronically against the structured row, not by uploading a blanket compliance letter.

For future Works products, drawings and specifications may remain governed documents, but the principal deliverables, BOQ lines, completion milestones, material requirements, tests and acceptance obligations must be structured. A BOQ must normally be imported into governed rows rather than retained only as a spreadsheet or PDF.

## 9. Requisition authorisation and handoff

The authorised handoff contains an immutable snapshot of:

- Procuring Entity, Financial Year and requesting department;
- Plan Item and every contributing source line;
- approved method, schedule, internal estimated value and funding references;
- package summary;
- all equipment, technical, service and acceptance rows;
- supporting-material references and digests;
- department and Procurement decisions; and
- package version and content digest.

Tender Preparation reads this handoff. It does not query mutable Draft rows or ask the Procurement Officer to re-enter the department's requirements.

## 10. Tender Preparation treatment

Tender Preparation must:

1. test the handoff against the released template's suitability rules;
2. display inherited department and Planning data as read-only;
3. generate goods, delivery and price-schedule rows from the authorised item rows;
4. publish every technical, service and acceptance requirement;
5. generate an electronic bidder response for every published requirement;
6. let Procurement add only permitted evidence and tender-specific choices;
7. link each evaluation check to a visible published requirement; and
8. carry awarded values and obligations into the contract record without re-entry.

For a technical requirement, the first released bidder response is:

- `Comply` or `Do not comply`;
- offered value where the characteristic has a measurable value;
- bidder comment, maximum 500 characters; and
- evidence reference where Tender Preparation requires evidence.

The system evaluates a controlled numeric or closed-choice rule where possible. It does not infer compliance from an attachment.

## 11. Template suitability test

`IT-EQUIPMENT-OPEN-V1` is available only when every answer below is Yes:

| Test | Required answer |
|---|---|
| Is the requirement principally supply and delivery of off-the-shelf IT equipment? | Yes |
| Is the approved method supported by this release? | Yes |
| Is there one Requisition and one award package? | Yes |
| Is the IT Equipment Requirement Package complete? | Yes |
| Can technical compliance be decided through the published structured rows? | Yes |
| Are complex development, integration and migration absent? | Yes |
| Are all dates within the approved Plan and Requisition boundaries? | Yes |
| Is every operative attachment obligation represented by a structured row? | Yes |

If any answer is No, the system stops. It does not force the requirement into the template or invite the officer to bypass the test with free text.

## 12. Correction routes

| Point reached | Correction route |
|---|---|
| Need or Plan is still a Draft | Edit the owning Draft. |
| Plan Item is Active but no Requisition is authorised | Use the approved Planning amendment or create the correct Requisition within remaining availability. |
| Requisition submitted but not authorised | Return it to the department with one clear reason. |
| Requisition authorised; handoff not consumed | Revoke authorisation, preserve history, reverse the exact Planning drawdown and create a corrected successor. |
| Tender Draft exists but is not approved for publication | Return to Requisition. Close the Tender Draft as `Upstream correction required`, release the handoff, correct and reauthorise the Requisition, then create a Tender successor from the new handoff. Do not silently mutate inherited facts. |
| Tender approved but publication handoff unconsumed | Reopen under the Tender lifecycle, or return upstream where the source requirement changed. Preserve the approved Version. |
| Tender published | Use the governed clarification, addendum, cancellation or new-proceeding process. This is outside the first slice. |

## 13. Minimal roles

Use native Frappe Roles, Workflow permissions and User Permissions. Do not create a parallel capability or scope-assignment system.

| Role or legal capacity | Responsibility |
|---|---|
| Departmental Author | Prepare a Need, Departmental Plan entry and Requisition for the user's permitted department. |
| Head of User Department | Approve or return the department-owned Need, Departmental Plan and Requisition submission. |
| Procurement Planner | Accept and classify Departmental Plans; consolidate, fund and schedule the Annual Procurement Plan. This includes Planning validation and creates no separate validator role. |
| Budget Officer | Confirm budget availability or reservation where required. |
| Accounting Officer | Prepare/adopt or return the complete consolidated Annual Procurement Plan. |
| Responsible Cabinet Secretary, County Executive Committee Member for finance or responsible for the entity, Board of Directors or similar governing body | Approve or return the Accounting-Officer-adopted Annual Procurement Plan. Exactly one of these routes applies to a PE. |
| Head of Procurement Function | Authorise or return a Requisition and perform the Tender decision assigned by the approved downstream contract. No Annual Plan approval is implied. |
| Procurement Officer | Prepare a Tender from an authorised handoff. |
| Auditor | Read authorised records and audit history; no business transition. |

The consolidated Annual Procurement Plan is adopted by the Accounting Officer and then receives exactly one statutory approval applicable to the PE. KenTender must not insert a Head of Procurement Function approval, professional reviewer, generic approval committee or publication approval into that chain.

The same individual may hold more than one assigned application role where law permits, but each decision records the legal capacity exercised. A combined assignment does not create or remove a required decision. For a Board or similar governing body, KenTender records the collective decision and resolution reference; it does not present the person entering the resolution as the sole approving authority.

Publication is an idempotent system action after statutory approval. It is not another approval level.

## 14. Worked KEBS example

### 14.1 Source and Planning

| Source line | Need | Quantity | Expected result |
|---|---|---:|---|
| `SRC-KEBS-ICT-001` | Business laptops | 25 Each | Mobile officers can run approved office and standards applications securely. |
| `SRC-KEBS-ICT-002` | Desktop computers with monitors | 15 Each | Fixed workstations replace unsupported equipment at the Coast Region office. |
| `SRC-KEBS-ICT-003` | Business tablets | 10 Each | Field officers can capture and review inspection information away from the office. |

Procurement consolidates these lines into `PPI-KEBS-2026-ICT-001`, with the approved method, schedule, internal estimate and funding. The source IDs remain visible.

### 14.2 Requisition package

| Item ID | Item | Quantity | Delivery |
|---|---|---:|---|
| `REQITEM-001` | Business laptops | 25 Each | KEBS Coast Region Office by 30 Dec 2026 |
| `REQITEM-002` | Desktop computers with monitors | 15 Each | KEBS Coast Region Office by 30 Dec 2026 |
| `REQITEM-003` | Business tablets | 10 Each | KEBS Coast Region Office by 30 Dec 2026 |

Example structured rows:

| Requirement ID | Applies to | Characteristic | Rule |
|---|---|---|---|
| `TECH-001` | `REQITEM-001` | Memory | Minimum 16 GB |
| `TECH-002` | `REQITEM-001` | Storage capacity | Minimum 512 GB |
| `TECH-003` | `REQITEM-001` | Storage type | Exact SSD |
| `TECH-004` | `REQITEM-002` | Memory | Minimum 16 GB |
| `TECH-005` | `REQITEM-003` | Warranty | Minimum 24 months |
| `TECH-006` | All items | Electrical compatibility | Required for Kenyan mains supply |

Related services state delivery, setup, asset-tag support and user orientation as separate rows. Acceptance covers quantity, physical condition, specification compliance, functional test and required documents. A room layout or existing network diagram may be attached for context, but it cannot replace any of these rows.

### 14.3 Tender result

Tender Preparation inherits all three items and requirement IDs. The Procurement Officer does not type them again. The released product generates:

- the goods and delivery schedule;
- the supplier price schedule with blank supplier-price fields;
- a compliance response against every `TECH-*` row;
- required evidence selected by Procurement;
- the fixed evaluation sequence; and
- contract schedules linked to the same item and requirement IDs.

## 15. Acceptance conditions

The first slice is acceptable only when:

1. a requirement can be traced from source line to Tender and contract schedule;
2. no operative supplier obligation exists only in an attachment;
3. the department enters its facts once;
4. Procurement cannot silently change department-owned facts;
5. Procurement can add proportionate supplier evidence without inventing an unpublished criterion;
6. every bidder response is electronic and linked to a published requirement;
7. the template suitability decision is deterministic;
8. a source correction preserves history and creates a new authorised handoff;
9. the rendered Tender contains the same controlled values as the electronic record; and
10. the KEBS example completes without a generic schema, manifest editor or STD Configuration screen;
11. the Accounting Officer sees and adopts or returns the complete immutable consolidated Plan;
12. exactly one statutory approving authority applies to each PE;
13. that authority approves or returns the same Accounting-Officer-adopted Plan;
14. the Head of Procurement Function is not an Annual Plan approval stage;
15. no professional review, generic approval committee or publication approval is inserted;
16. a Board approval records the collective decision and resolution reference; and
17. publication starts only after statutory approval and creates no approval decision.

## 16. Effect on current documents

| Document | Required treatment after approval of this contract |
|---|---|
| `NDS-CHG-001 v1.1` | Retain the simple Need flow; ensure the expected result and source-line handoff are explicit. |
| `PLN-CHG-001 v1.1` | Apply the exact Accounting Officer adoption and single statutory-approval chain, departmental intake, stable line output and simplified role model. |
| `REQ-CHG-001 v1.0` | Replace attachment-centred technical requirements with the code-owned IT Equipment Requirement Package. |
| `REQ-CHG-001 v1.1` | Do not implement the generic composer. Reuse only product knowledge that fits this contract. |
| `STD-ADR-002 v1.0` | Clarify that the minimal Requisition boundary is structured product-specific data, not a PDF specification. |
| `STD-ST-001 v0.3` | Retain the approved productised-template direction. Add this structured upstream input to the tested flow. |
| `STD-TPL-001 v0.3` | Replace technical-document input with the authorised structured package plus optional supporting materials. |
| `TPR-CHG-001 v0.3` | Make inherited requirement rows read-only, remove their manual recreation and add the upstream-correction route. |
| `STD-TPL-IMP-001 v0.2` | Keep implementation paused until the upstream modules and revised handoff exist. |

## 17. Delivery order

1. Revise the Departmental Needs and Planning contracts narrowly against this approved contract.
2. Implement and test Need/direct-entry to Active Plan Item.
3. Revise and implement Requisitions with the IT Equipment Requirement Package.
4. Revise the IT template and Tender Preparation contracts to consume the handoff.
5. Run the KEBS journey end to end with actual users.
6. Correct practical problems and lock the first released product.

Do not generalise during these steps. Add another product-specific requirement form only when a second released procurement pattern proves that it is needed.

## 18. Non-drift controls

The following are fixed unless the Project Owner approves a later change to this document:

1. Structured system data is the authoritative requirement record; attachments remain supporting material.
2. Business users complete a fixed product form; they do not configure schemas, mappings, manifests or Tender templates.
3. The first product uses the code-owned IT Equipment Requirement Package and `IT-EQUIPMENT-OPEN-V1`; no generic configuration engine is introduced.
4. Department-owned data is entered once and inherited downstream through stable identifiers.
5. Procurement adds only Procurement-owned rules and cannot silently rewrite departmental requirements.
6. Bidder responses, evaluation checks and contract obligations link to visible structured requirements.
7. Native Frappe permissions and the minimum roles in section 13 are used. The consolidated-plan chain contains Accounting Officer adoption followed by exactly one statutory approval applicable to the PE. Extra permission layers, reviewers or approval levels require an identified legal source and Project Owner approval.
8. New abstractions are introduced only after at least two released product patterns prove the same requirement.

Every later module revision and implementation pack must include a short conformance table against these eight controls. A conflicting proposal must identify the exact control, explain the practical need and obtain approval before code is changed. Passing tests cannot waive this requirement.

## 19. Approval record

E2E-REQ-001 v0.2 was approved by the Project Owner on 28 August 2026. It incorporates the corrected Annual Plan approval chain, supersedes v0.1 in full and is the single end-to-end control document to consult. Production implementation remains subject to the approved module contracts and their implementation packs.
