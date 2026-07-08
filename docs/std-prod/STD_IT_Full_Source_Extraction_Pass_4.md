# STD for Procurement of Information Technology — Full Source Extraction Pass 4

## Procuring Entity Requirements, Technical Requirements, Implementation Schedule, and System Inventory Schemas

**Document status:** Draft extraction artifact  
**Activation status:** Not activatable  
**Target STD package:** `KE-PPRA-IT-2022-04`  
**Engine scope:** Generalized STD Engine, with IT STD specialization  
**Prepared for:** KenTender e-Procurement System  
**Pass number:** 4 of the IT STD source extraction series  

---

## 1. Purpose of this extraction pass

This pass converts the official Information Technology STD’s **Procuring Entity Requirements** area into implementable STD Engine schemas.

The specific focus is:

1. Requirements of the Information System.
2. Technical Requirements.
3. Functional, architectural, and performance requirements.
4. Service specifications.
5. Technology specifications.
6. Implementation Schedule.
7. Site tables and non-working day tables.
8. System Inventory Tables.
9. Background and Informational Materials.
10. Supplier conformance response structure.
11. Cross-linking between requirements, inventory, price schedules, evaluation, and contract execution.

This pass must remain generalized enough to support other STDs, while giving the IT STD enough structure to be implemented without falling back to unstructured uploaded documents.

---

## 2. Source basis

### 2.1 Official master source

The legal master source remains:

**DOC 10. Standard Tender Document for Procurement of Information Technology**  
Issued by the Public Procurement Regulatory Authority, Kenya.

The official IT STD Part 2 contains the Procuring Entity’s Requirements and covers:

1. Requirements of the Information System.
2. Technical Requirements.
3. Functional, Architectural and Performance Requirements.
4. Service Specifications.
5. Technology Specifications.
6. Implementation Schedule.
7. System Inventory Tables.
8. Background and Informational Materials.

The STD states that the Technical Requirements, Implementation Schedule, and System Inventory Tables collectively state the Supplier’s obligations to design, supply, and install the Information System. These requirements are therefore not cosmetic tender text. They are part of the contractual and operational basis for procurement, supplier tendering, evaluation, implementation, acceptance, and contract management.

### 2.2 Calibration fixture

The NSSF SPS ERP tender is used as a real-world calibration fixture only:

**NSSF SPS RFP ERP 2026 — Supply, Installation, Configuration, Customization, Testing, Commissioning and Maintenance of an ERP System.**

It is useful because it shows a real IT tender that contains:

1. Background and objectives.
2. Scope of work.
3. Phased implementation.
4. ERP module requirements.
5. Technical specification and compliance matrices.
6. Project management requirements.
7. Data migration requirements.
8. Integration requirements.
9. Documentation, training, testing, warranty, support, and cloud infrastructure requirements.
10. Schedule and price requirements.

It is not the master template and must not override the official IT STD.

---

## 3. Design conclusion from this pass

The most important conclusion is:

**The Procuring Entity Requirements area must be treated as structured domain data, not as a document upload area.**

For IT procurement, the requirements area is the bridge between:

1. The legal STD template.
2. The PE’s business and technical needs.
3. The bidder’s technical proposal.
4. The bidder’s price schedule.
5. The evaluation team’s compliance assessment.
6. The final contract scope.
7. The project plan.
8. Testing, commissioning, operational acceptance, warranty, and recurrent support.

Therefore, the engine must provide a configurable **Requirements Composer** and not merely a file attachment box.

---

## 4. Generalized model for Procuring Entity Requirements

The engine should generalize the requirements area into a reusable framework that can support IT, Works, Goods, Non-Consulting Services, Consultancy, Framework Agreements, and other STD families.

### 4.1 Universal requirement concepts

| Concept | Generalized meaning |
|---|---|
| Requirement Domain | A broad area of obligations, such as Technical, Functional, Works Specification, Goods Specification, Service Level, ESHS, Training, Warranty, or Contract Deliverable. |
| Requirement Group | A logical grouping within a domain, such as Security, Performance, Pension Administration, Civil Works, Delivery, Testing, or Documentation. |
| Requirement Item | A discrete requirement capable of being rendered, responded to, evaluated, traced, and carried into contract execution. |
| Requirement Response Schema | The bidder response format for a requirement item. |
| Requirement Evidence | Documents, references, certificates, diagrams, methodology statements, or compliance artifacts required from the bidder. |
| Requirement Compliance Classification | Mandatory, scored, optional, informational, alternative, or contract-only. |
| Requirement Trace | A source and downstream link connecting source STD, tender configuration, bidder response, evaluation, contract, acceptance, and audit. |
| Requirement Render Block | The document-generation block that renders the requirement into the tender document. |
| Requirement Validation Rule | A rule that checks completeness, neutrality, cross-references, pricing linkage, evaluation linkage, or contract linkage. |

### 4.2 IT-specific requirement concepts

| IT concept | Required treatment |
|---|---|
| Functional Requirement | A business capability or process the system must support. |
| Architectural Requirement | A structural or integration architecture obligation. |
| Performance Requirement | A measurable threshold for responsiveness, throughput, capacity, availability, recovery, or scalability. |
| Service Specification | A supplier service obligation, such as installation, configuration, migration, training, support, warranty, maintenance, or technical assistance. |
| Technology Specification | A technology component or platform requirement, normally vendor-neutral unless a justified exception is approved. |
| Implementation Milestone | A time-bound activity or deliverable measured in weeks from contract effectiveness. |
| Site | A physical or logical location where the system is supplied, installed, configured, operated, supported, or accepted. |
| System Inventory Item | A component, service, license, material, hardware item, software item, or recurrent support input tied to a subsystem and price schedule. |
| Recurrent Cost Item | A warranty-period or post-warranty cost item, such as technical services, license renewals, support, maintenance, or managed services. |
| Background Material | Informational content that helps bidders understand the context but must not introduce binding requirements. |

---

## 5. Mutability model for Part 2 requirements

The IT STD Part 2 is not locked in the same way as ITT or GCC. It is a controlled configuration area.

| Component | Mutability | Governance treatment |
|---|---|---|
| STD authoring guidance notes | Locked master guidance | Visible to authorized template administrators and PE preparers; not necessarily rendered in the issued bidder document unless the official template requires it. |
| Requirement category structure | Controlled | Can be extended only according to the active STD package configuration. |
| PE-authored requirement items | Configurable | Entered through the Requirements Composer, not edited as raw document text. |
| Requirement compliance options | Controlled | Must use approved response formats and compliance classifications. |
| Implementation schedule structure | Controlled | PE configures dates, milestones, sites, and LD flags within the approved schema. |
| System inventory structure | Controlled | PE configures line items and quantities within approved schema. |
| Background materials | Configurable but non-binding | Must be explicitly marked informational and validated to prevent hidden requirements. |
| Rendered Part 2 tender content | Immutable after publication | Changes after publication require addendum/supersession. |

---

## 6. Requirements Composer design

### 6.1 Composer purpose

The Requirements Composer is the controlled authoring workspace used by a Procuring Entity to build the requirements portion of a tender from the active STD package.

It must support:

1. Structured authoring.
2. Source traceability.
3. Vendor-neutral drafting checks.
4. Requirement completeness validation.
5. Supplier response schema generation.
6. Evaluation linkage.
7. Price schedule linkage.
8. Implementation milestone linkage.
9. Contract carry-forward.
10. Addendum impact detection.

### 6.2 Composer sections for the IT STD

| Composer section | Purpose |
|---|---|
| Requirements Overview | Names the system and summarizes the procurement need. |
| Functional Requirements | Captures business capabilities the system must perform. |
| Architectural Requirements | Captures hosting, architecture, integration, interoperability, data, identity, and security architecture obligations. |
| Performance Requirements | Captures measurable thresholds and service levels. |
| Service Specifications | Captures implementation, configuration, migration, training, documentation, warranty, support, maintenance, and technical assistance obligations. |
| Technology Specifications | Captures hardware, software, cloud, network, license, platform, or infrastructure specifications. |
| Testing and Acceptance | Captures inspection, testing, commissioning, UAT, operational acceptance, and acceptance evidence. |
| Implementation Schedule | Captures subsystem milestones, sites, installation weeks, acceptance weeks, and liquidated damages markers. |
| Site Table | Captures physical or logical locations relevant to delivery, installation, testing, support, or operation. |
| Non-Working Days | Captures holidays and other non-working days relevant to scheduling. |
| System Inventory | Captures supply/install and recurrent cost inventory items by subsystem. |
| Background Materials | Captures contextual, non-binding information. |
| Validation | Shows blockers, warnings, and advisory findings. |
| Preview | Renders the generated Part 2 content as it will appear in the tender document. |

---

## 7. Core data objects for this pass

### 7.1 STD Requirement Domain

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `name` | string | Yes | Unique domain name. |
| `std_template_version` | link | Yes | Active or draft STD version. |
| `domain_code` | string | Yes | Example: `TECHNICAL`, `FUNCTIONAL`, `SERVICE`, `PERFORMANCE`, `BACKGROUND`. |
| `display_label` | string | Yes | Human-readable label. |
| `description` | text | No | Domain description. |
| `is_renderable` | boolean | Yes | Whether this domain appears in the tender output. |
| `is_binding` | boolean | Yes | Whether items in this domain create supplier obligations. |
| `default_response_schema` | json | No | Default bidder response format. |
| `sort_order` | integer | Yes | Render and UI order. |
| `source_anchor_id` | link | No | Source trace to official STD. |

### 7.2 STD Requirement Group

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `name` | string | Yes | Unique group name. |
| `requirement_domain` | link | Yes | Parent domain. |
| `group_code` | string | Yes | Example: `SECURITY`, `DATA_MIGRATION`, `TRAINING`. |
| `title` | string | Yes | Group title. |
| `description` | text | No | Group description. |
| `render_heading_level` | integer | Yes | Document heading level. |
| `is_repeatable` | boolean | Yes | Allows multiple modules/subsystems. |
| `requires_items` | boolean | Yes | Whether at least one item is mandatory. |
| `sort_order` | integer | Yes | Render and UI order. |
| `source_anchor_id` | link | No | Source trace. |

### 7.3 STD Requirement Item

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `name` | string | Yes | Unique requirement item ID. |
| `tender_std_instance` | link | Yes | Tender-specific STD instance. |
| `requirement_group` | link | Yes | Parent group. |
| `requirement_code` | string | Yes | Example: `A.1`, `B2`, `SEC-003`. |
| `title` | string | No | Optional short title. |
| `statement` | rich text | Yes | Requirement obligation. |
| `obligation_actor` | enum | Yes | `SUPPLIER`, `SYSTEM`, `PE`, `BIDDER`, `CONTRACTOR`, `JOINT`. |
| `binding_status` | enum | Yes | `BINDING`, `INFORMATIONAL`, `GUIDANCE`, `EVALUATION_ONLY`, `CONTRACT_ONLY`. |
| `compliance_classification` | enum | Yes | `MANDATORY`, `SCORED`, `OPTIONAL`, `DESIRABLE`, `ALTERNATIVE_ALLOWED`, `NOT_APPLICABLE`. |
| `response_mode` | enum | Yes | `YES_NO_REFERENCE`, `NARRATIVE`, `NUMERIC_THRESHOLD`, `TABLE`, `ATTACHMENT`, `NONE`. |
| `measurement_type` | enum | No | `BOOLEAN`, `TEXT`, `NUMBER`, `DATE`, `DURATION`, `PERCENTAGE`, `MONEY`, `FILE`, `MATRIX`. |
| `threshold_value` | string/number | No | Measurable threshold if applicable. |
| `threshold_unit` | string | No | Example: `users`, `seconds`, `%`, `days`, `KES`. |
| `evidence_policy` | enum | Yes | `NONE`, `OPTIONAL`, `REQUIRED`, `CONDITIONAL`. |
| `evaluation_link_required` | boolean | Yes | Whether the item must appear in evaluation. |
| `price_link_required` | boolean | Yes | Whether the item must be priced or linked to a priced inventory item. |
| `implementation_link_required` | boolean | Yes | Whether the item must link to an implementation milestone. |
| `inventory_link_required` | boolean | Yes | Whether the item must link to a system inventory item. |
| `acceptance_link_required` | boolean | Yes | Whether the item must link to testing/acceptance criteria. |
| `brand_reference_flag` | boolean | Yes | True if brand or proprietary reference detected. |
| `equivalence_allowed` | boolean | Yes | Must normally be true if brand reference exists. |
| `brand_exception_justification` | text | No | Required if brand/proprietary reference is used without equivalence. |
| `source_anchor_id` | link | No | Official STD or tender-specific source anchor. |
| `render_block_id` | link | No | Render mapping. |
| `sort_order` | integer | Yes | Display and render order. |
| `status` | enum | Yes | `DRAFT`, `VALIDATED`, `APPROVED`, `PUBLISHED`, `SUPERSEDED`. |

### 7.4 STD Requirement Evidence

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `requirement_item` | link | Yes | Parent requirement. |
| `evidence_code` | string | Yes | Evidence ID. |
| `evidence_type` | enum | Yes | `DOCUMENT`, `CERTIFICATE`, `REFERENCE_PAGE`, `DIAGRAM`, `METHODOLOGY`, `CV`, `LICENSE`, `SCREENSHOT`, `DEMO`, `OTHER`. |
| `description` | text | Yes | Required evidence description. |
| `bidder_upload_required` | boolean | Yes | Whether upload is mandatory. |
| `reference_page_required` | boolean | Yes | Whether bidder must cite proposal pages. |
| `review_stage` | enum | Yes | `PRELIMINARY`, `TECHNICAL`, `FINANCIAL`, `POST_QUALIFICATION`, `CONTRACT`. |
| `validation_rule_id` | link | No | Rule to enforce evidence. |

### 7.5 STD Requirement Response Schema

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `requirement_item` | link | Yes | Parent requirement. |
| `response_schema_code` | string | Yes | Unique schema code. |
| `requires_compliance_selection` | boolean | Yes | Usually yes for conformance matrix. |
| `allowed_compliance_values` | json | Yes | Example: `COMPLIANT`, `PARTIALLY_COMPLIANT`, `NOT_COMPLIANT`, `EXCEPTION`. |
| `requires_reference_pages` | boolean | Yes | For proposal traceability. |
| `requires_commentary` | boolean | Yes | Whether bidder must explain. |
| `requires_evidence_upload` | boolean | Yes | Whether bidder upload is mandatory. |
| `exception_handling` | enum | Yes | `NOT_ALLOWED`, `ALLOWED_WITH_JUSTIFICATION`, `ALLOWED_AS_ALTERNATIVE`. |

---

## 8. Implementation Schedule schema

### 8.1 Official STD intent

The Implementation Schedule summarizes when and where installation and operational acceptance should take place for subsystems, major components, the whole system, and other major contract milestones.

The official STD makes several important design points that must be enforced by the engine:

1. The schedule should be realistic and achievable.
2. Dates must be consistent with the GCC/SCC and other tender sections.
3. The work breakdown structure must be detailed enough for contract management but not so detailed that it unfairly constrains bidders.
4. Timings should be stated in weeks from contract effectiveness.
5. The schedule, system inventory tables, and price schedules must be closely linked.
6. Liquidated damages milestones should be limited to essential milestones.
7. Site tables must give enough detail for bidders to estimate delivery, insurance, installation, cabling, inter-building communication, and related costs.

### 8.2 STD Implementation Schedule

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `name` | string | Yes | Unique schedule ID. |
| `tender_std_instance` | link | Yes | Tender-specific STD instance. |
| `schedule_title` | string | Yes | Example: `Implementation Schedule`. |
| `time_basis` | enum | Yes | `WEEKS_FROM_CONTRACT_EFFECTIVENESS` should be default for IT STD. |
| `includes_delivery_date` | boolean | Yes | Should normally be false in the official IT STD schedule model. |
| `project_plan_line_required` | boolean | Yes | The official sample includes Project Plan as line 0. |
| `operational_acceptance_line_required` | boolean | Yes | Integrated whole acceptance should be represented. |
| `recurrent_cost_line_required` | boolean | Conditional | Required if recurrent costs are enabled. |
| `site_table_required` | boolean | Conditional | Required if there are physical/logical sites. |
| `non_working_day_table_required` | boolean | Conditional | Required if scheduling depends on non-working day calendars. |
| `status` | enum | Yes | `DRAFT`, `VALIDATED`, `APPROVED`, `PUBLISHED`, `SUPERSEDED`. |

### 8.3 STD Implementation Milestone

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `implementation_schedule` | link | Yes | Parent schedule. |
| `line_item_no` | string | Yes | Example: `0`, `1`, `1.1`, `x`, `y`. |
| `subsystem_or_item` | string | Yes | Subsystem, project plan, operational acceptance, recurrent cost item, etc. |
| `configuration_table_no` | string | No | Links to configuration/inventory table. |
| `site_code` | link/string | No | Links to site table. |
| `supplier_delivery_detail_required` | boolean | Yes | Whether tenderer specifies delivery in preliminary project plan. |
| `installation_weeks_from_effective_date` | integer | No | Planned installation period. |
| `acceptance_weeks_from_effective_date` | integer | No | Planned acceptance period. |
| `liquidated_damages_milestone` | boolean | Yes | Whether delay may trigger LD. |
| `ld_basis_reference` | string | Conditional | Required if LD milestone is true. |
| `related_inventory_table` | link | Conditional | Required for subsystem lines with priced items. |
| `related_price_schedule` | link | Conditional | Required for subsystem lines with priced items. |
| `related_requirement_group` | link | No | Link to relevant technical requirement group. |
| `sort_order` | integer | Yes | Schedule order. |

### 8.4 STD Site Table

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `name` | string | Yes | Unique site record. |
| `tender_std_instance` | link | Yes | Parent tender STD instance. |
| `site_code` | string | Yes | Example: `HQ`, `R1`, `R1.1`. |
| `site_name` | string | Yes | Site label. |
| `city_town_region` | string | No | Geographic area. |
| `primary_street_address` | text | No | Site address. |
| `drawing_reference_no` | string | No | Drawing or layout reference, if applicable. |
| `site_type` | enum | No | `HEADQUARTERS`, `BRANCH`, `DATA_CENTER`, `CLOUD_REGION`, `REMOTE_SITE`, `OTHER`. |
| `installation_relevant` | boolean | Yes | Whether installation effort applies. |
| `acceptance_relevant` | boolean | Yes | Whether acceptance occurs at this site. |
| `support_relevant` | boolean | Yes | Whether support/warranty obligations apply. |

### 8.5 STD Non-Working Day Calendar

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `name` | string | Yes | Unique calendar ID. |
| `tender_std_instance` | link | Yes | Parent tender STD instance. |
| `year` | integer | Yes | Calendar year. |
| `month` | integer | Yes | 1 to 12. |
| `non_working_days` | json | No | Dates or day numbers. |
| `reason` | text | No | Holiday or business reason. |
| `source` | enum | Yes | `PUBLIC_HOLIDAY`, `PE_SPECIFIED`, `SITE_SPECIFIC`, `OTHER`. |

---

## 9. System Inventory schema

### 9.1 Official STD intent

The System Inventory Tables detail:

1. The Information Technologies, Materials, Goods, and Services that comprise the system.
2. The quantities of each item.
3. The sites and specific site locations.
4. Cross-references to the relevant technical specifications.

The official IT STD includes two primary inventory formats:

1. **Supply and Installation Cost Items.**
2. **Recurrent Cost Items.**

The second format supports price information about items needed during the warranty period and/or post-warranty period.

### 9.2 STD System Inventory Table

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `name` | string | Yes | Unique table ID. |
| `tender_std_instance` | link | Yes | Parent tender STD instance. |
| `inventory_table_no` | string | Yes | Identifying number. |
| `inventory_type` | enum | Yes | `SUPPLY_INSTALL`, `RECURRENT_COST`, `WARRANTY`, `POST_WARRANTY`, `OTHER`. |
| `line_item_no` | string | Yes | Must link to implementation schedule line item. |
| `subsystem_or_item` | string | Yes | Corresponding subsystem or schedule item. |
| `related_implementation_milestone` | link | Yes | Required cross-link. |
| `related_price_schedule` | link | Conditional | Required for priced items. |
| `related_requirement_group` | link | No | Technical requirement group. |
| `status` | enum | Yes | `DRAFT`, `VALIDATED`, `APPROVED`, `PUBLISHED`, `SUPERSEDED`. |

### 9.3 STD System Inventory Line

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `system_inventory_table` | link | Yes | Parent table. |
| `component_no` | string | Yes | Component line number. |
| `component` | string | Yes | Component/service/license/material name. |
| `relevant_technical_specification_no` | string/link | Yes | Cross-reference to technical requirement item or group. |
| `additional_site_information` | text | No | Building, floor, department, room, cloud region, etc. |
| `site_code` | link/string | No | Site table link. |
| `quantity` | number | Conditional | Required for countable items. |
| `unit_of_measure` | string | No | Example: `each`, `days`, `licenses`, `users`, `months`. |
| `bidder_may_adjust_quantity` | boolean | Yes | Controlled by STD/tender configuration. |
| `pricing_required` | boolean | Yes | Whether line must appear in price schedule. |
| `acceptance_required` | boolean | Yes | Whether line must be accepted/tested. |
| `notes` | text | No | Optional clarifying notes. |

### 9.4 STD Recurrent Cost Inventory Line

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `system_inventory_table` | link | Yes | Parent recurrent cost table. |
| `component_no` | string | Yes | Component line number. |
| `component` | string | Yes | Example: warranty defect repair, software updates, technical services. |
| `relevant_technical_specification_no` | string/link | Yes | Cross-reference to requirement. |
| `cost_period_type` | enum | Yes | `WARRANTY_PERIOD`, `POST_WARRANTY`, `YEARLY`, `MONTHLY`, `AD_HOC`. |
| `year_1_quantity` | number/string | No | Year 1 input. |
| `year_2_quantity` | number/string | No | Year 2 input. |
| `year_3_quantity` | number/string | No | Year 3 input. |
| `additional_years` | json | No | Extend beyond 3 years if configured. |
| `unit_of_measure` | string | No | Example: `days`, `licenses`, `months`, `incidents`, `support hours`. |
| `included_in_supply_install_price` | boolean | Yes | Whether included in initial price. |
| `separate_contract_required` | boolean | Conditional | Based on TDS/SCC configuration. |
| `pricing_required` | boolean | Yes | Whether recurrent price schedule must include it. |

---

## 10. Background and Informational Materials schema

### 10.1 Official STD intent

Background and Informational Materials help tenderers prepare precise technical tenders and prices. They must not introduce binding requirements.

Examples include:

1. Existing systems.
2. Existing data sources.
3. Regulatory report formats.
4. Site layouts.
5. Business context.
6. Current process descriptions.
7. Constraints that help interpret binding requirements.

If a matter is intended to bind the Supplier, it must be stated in Technical Requirements, Implementation Schedule, System Inventory Tables, SCC, or another binding contract/tender area, not hidden in background materials.

### 10.2 STD Background Material

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `name` | string | Yes | Unique material ID. |
| `tender_std_instance` | link | Yes | Parent tender STD instance. |
| `material_code` | string | Yes | Example: `BG-001`. |
| `title` | string | Yes | Material title. |
| `material_type` | enum | Yes | `NARRATIVE`, `EXISTING_SYSTEM`, `DATASET`, `REGULATORY_CONTEXT`, `SITE_LAYOUT`, `PROCESS_DESCRIPTION`, `ATTACHMENT`, `OTHER`. |
| `content` | rich text | No | Narrative content. |
| `attachment_id` | link | No | Optional file attachment. |
| `binding_status` | enum | Yes | Must default to `INFORMATIONAL`. |
| `related_requirement_items` | multi-link | No | Link to binding requirements that use this as context. |
| `contains_obligation_language_flag` | boolean | Yes | Auto-detected during validation. |
| `review_required` | boolean | Conditional | Required if obligation-like language appears. |
| `render_in_tender` | boolean | Yes | Whether material is included in issued tender. |

---

## 11. Requirement drafting controls

The engine should enforce or warn on the following drafting controls.

| Control | Severity | Rule |
|---|---|---|
| Supplier voice required | Warning / blocker by configuration | Binding technical requirements should be stated as obligations of the Supplier/System. |
| Aspirational text warning | Warning | Phrases such as “improve efficiency”, “enable world-class service”, or “maximize value” must be converted into measurable obligations or moved to background/objectives. |
| Threshold value required | Warning/blocker | Performance requirements should include measurable thresholds where practical. |
| Vendor-neutrality check | Warning/blocker | Brand, catalog, proprietary product, or manufacturer-specific references require equivalence language or approved exception. |
| Background cannot bind | Blocker | Background materials must not introduce “must/shall/required” obligations unless converted into a requirement item. |
| Requirement must be evaluable | Warning/blocker | Mandatory/scored items must define response mode and evaluation method. |
| Requirement must be traceable | Blocker | Requirement item must have code, group, render block, and audit trace. |
| Requirement-pricing consistency | Blocker | Items that imply supply/install or recurrent costs must link to inventory and price schedule. |
| Requirement-acceptance consistency | Warning/blocker | Items that require delivery/testing must link to testing or acceptance criteria. |
| Implementation consistency | Blocker | Subsystem schedule lines must link to inventory tables and price schedule lines. |
| Liquidated damages consistency | Blocker | LD milestone must link to SCC/GCC LD basis. |

---

## 12. Supplier conformance matrix

### 12.1 Purpose

Every binding IT requirement should generate a supplier response row unless explicitly marked as non-response/internal.

The conformance matrix allows the bidder to state whether it complies, provide evidence, cite proposal pages, and declare deviations.

### 12.2 Recommended conformance response fields

| Field | Required | Notes |
|---|---:|---|
| Requirement code | Yes | Generated from requirement item. |
| Requirement statement | Yes | Rendered read-only to bidder. |
| Compliance status | Yes | `COMPLIANT`, `PARTIALLY_COMPLIANT`, `NOT_COMPLIANT`, `EXCEPTION`, `ALTERNATIVE`. |
| Bidder commentary | Conditional | Required for partial compliance, exception, alternative, or non-compliance. |
| Reference page(s) | Yes | Proposal reference pages or section. |
| Evidence upload | Conditional | Based on evidence policy. |
| Deviation flag | Conditional | Required if not fully compliant. |
| Alternative proposal flag | Conditional | Only if alternatives are permitted. |
| Evaluator finding | Internal | Used during evaluation. |
| Evaluator comments | Internal | Used during evaluation. |
| Contract carry-forward flag | Internal | Marks items to appear in final contract/project plan. |

---

## 13. Evaluation linkage

Part 2 requirements must not be disconnected from Section III evaluation.

Each requirement item should have one of the following evaluation treatments:

| Treatment | Meaning |
|---|---|
| Pass/fail mandatory | Failure causes non-responsiveness or technical disqualification. |
| Scored technical | Requirement contributes to technical score. |
| Evidence-only | Evidence is reviewed but not separately scored. |
| Contract clarification | Used for contract formation after award. |
| Informational only | Not evaluated directly. |

The system must prevent the following failure modes:

1. A mandatory requirement with no evaluation treatment.
2. A scored requirement with no scoring criterion.
3. A technical requirement that creates cost but has no inventory/price linkage.
4. A background statement that is used as an evaluation requirement.
5. A requirement that is priced but never appears in the implementation or system inventory model.

---

## 14. Price schedule linkage

The official IT STD creates a strong relationship between:

1. Technical Requirements.
2. Implementation Schedule.
3. System Inventory Tables.
4. Price Schedules.

The engine must implement this as a hard data relationship.

### 14.1 Required cross-links

| Source object | Must link to |
|---|---|
| Implementation milestone | System inventory table and price schedule, where priced deliverables exist. |
| Supply/install inventory line | Technical specification and supply/install price line. |
| Recurrent cost inventory line | Technical support/service requirement and recurrent price line. |
| Recurrent cost table | Warranty/post-warranty treatment and payment model. |
| Operational acceptance milestone | Testing/acceptance requirements and contract acceptance certificates. |

### 14.2 Pricing validation rules

| Rule code | Rule |
|---|---|
| `IT_REQ_PRICE_001` | A requirement classified as supply/install deliverable must have at least one linked system inventory line or be explicitly marked non-priced. |
| `IT_REQ_PRICE_002` | Every supply/install inventory line must have a linked technical specification number and price schedule line. |
| `IT_REQ_PRICE_003` | Every recurrent cost inventory line must have period coverage and pricing treatment. |
| `IT_REQ_PRICE_004` | If recurrent costs are enabled in TDS/SCC, recurrent cost tables and recurrent price schedules are mandatory. |
| `IT_REQ_PRICE_005` | Blank price cells must be handled according to the applicable tender price rules and evaluation adjustment logic. |

---

## 15. Contract carry-forward model

Part 2 requirements must carry forward into contract execution.

| Requirement artifact | Contract destination |
|---|---|
| Final requirements set | Contract scope / technical appendices. |
| Supplier conformance response | Supplier proposal annex and negotiated clarifications. |
| Implementation schedule | Agreed Project Plan and contract milestones. |
| System inventory tables | Contract deliverables and price/payment basis. |
| Testing and acceptance requirements | Installation and acceptance certificates. |
| Warranty/support requirements | SCC, service level schedules, maintenance obligations. |
| Technical team requirements | Supplier representative / technical support appendices. |
| Software/license/IP requirements | Software categories, custom materials, license and IP appendices. |
| Background materials | Informational annex only, unless referenced by binding requirements. |

The engine must preserve exactly which published requirement version was used for tendering, evaluation, award, and contract formation.

---

## 16. Render blocks required for Pass 4

The following render blocks must be added to the IT STD seed package.

| Render block code | Purpose |
|---|---|
| `IT_PART2_REQUIREMENTS_ROOT` | Renders Part 2 heading and requirements root. |
| `IT_REQ_TECHNICAL_GUIDANCE` | Renders permitted technical requirements guidance if included. |
| `IT_REQ_ACRONYMS` | Renders acronyms table. |
| `IT_REQ_FUNCTIONAL_ARCH_PERF` | Renders functional, architectural, and performance requirement groups. |
| `IT_REQ_SERVICE_SPECS` | Renders service specifications. |
| `IT_REQ_TECHNOLOGY_SPECS` | Renders technology specifications. |
| `IT_REQ_CONFORMANCE_MATRIX` | Renders bidder compliance matrix. |
| `IT_IMPLEMENTATION_SCHEDULE` | Renders implementation schedule table. |
| `IT_SITE_TABLE` | Renders site table. |
| `IT_NON_WORKING_DAYS` | Renders holidays and other non-working days table. |
| `IT_SYSTEM_INVENTORY_SUPPLY_INSTALL` | Renders supply/install system inventory tables. |
| `IT_SYSTEM_INVENTORY_RECURRENT` | Renders recurrent cost inventory tables. |
| `IT_BACKGROUND_MATERIALS` | Renders informational materials. |

---

## 17. Package file updates implied by this pass

The seed package should be extended with the following files or enriched if they already exist.

```text
requirements/domains.json
requirements/groups.json
requirements/items.schema.json
requirements/response_schemas.json
requirements/evidence_policies.json
requirements/drafting_rules.json
requirements/compliance_matrix.schema.json
implementation/implementation_schedule.schema.json
implementation/milestones.schema.json
implementation/sites.schema.json
implementation/non_working_days.schema.json
inventory/system_inventory_tables.schema.json
inventory/system_inventory_lines.schema.json
inventory/recurrent_cost_lines.schema.json
background/background_materials.schema.json
render/part2_requirements_render_blocks.json
validation/part2_requirements_validation_rules.json
smoke_tests/part2_requirements_smoke_tests.json
fixtures/nssf_erp_requirements_calibration.json
```

---

## 18. NSSF ERP calibration findings

The NSSF ERP tender demonstrates why the requirements composer must be structured.

### 18.1 Useful calibration patterns

| NSSF pattern | Engine implication |
|---|---|
| Background and objectives | Support informational business context separate from binding requirements. |
| Two-phase implementation | Implementation schedule must support phases and milestones. |
| ERP module list | Requirement groups must be repeatable by module/subsystem. |
| Compliance matrices with `M`, Yes, No, Reference Pages | Supplier conformance matrix must support mandatory compliance and reference pages. |
| Detailed system requirements | Requirement item schema must support long obligation text, measurable thresholds, security, reporting, integration, and audit controls. |
| Documentation, training, testing, warranty, support | Service specifications must be first-class, not hidden in narrative scope. |
| Cloud infrastructure requirements | Technology specifications must support hosting/platform/security obligations. |
| Warranty and SLA requirements | Recurrent cost, SLA, warranty, and support structures must link to contract terms. |
| IP/source code escrow language | IP/custom material/license requirements must carry into contract appendices. |

### 18.2 Cautionary calibration findings

| Finding | Required engine response |
|---|---|
| The NSSF tender specifies Microsoft Dynamics 365 Business Central and Microsoft Azure. | Brand/proprietary references must trigger vendor-neutrality review or exception approval. |
| The NSSF tender collapses official STD implementation and inventory concepts into custom sections. | The engine should let PE users enter real-world structures but normalize them into official schedule, inventory, price, and requirement objects. |
| Long requirements contain many separate obligations in one paragraph. | The composer should support decomposition into atomic requirements, or at least flag multi-obligation statements. |
| Compliance tables are extensive and page-heavy. | The supplier portal must generate structured response tables rather than asking bidders to manually fill a PDF/Word table. |
| Warranty, SLA, support, uptime, and escrow terms are contract-sensitive. | These should be linked to SCC/contract terms and reviewed before publication. |

---

## 19. Validation rule dictionary for Pass 4

| Rule code | Name | Severity | Description |
|---|---|---:|---|
| `IT_REQ_001` | Requirement code required | Blocker | Every binding requirement item must have a unique code. |
| `IT_REQ_002` | Requirement group required | Blocker | Every requirement item must belong to a group. |
| `IT_REQ_003` | Binding status required | Blocker | Every item must be classified as binding, informational, guidance, evaluation-only, or contract-only. |
| `IT_REQ_004` | Response schema required | Blocker | Mandatory or scored requirements must define bidder response mode. |
| `IT_REQ_005` | Evidence policy required | Warning | Mandatory or high-risk requirements should define evidence expectations. |
| `IT_REQ_006` | Background cannot bind | Blocker | Background materials must not introduce supplier obligations. |
| `IT_REQ_007` | Vendor-neutrality review | Warning/blocker | Brand/proprietary references require equivalence or approved exception. |
| `IT_REQ_008` | Aspirational wording review | Warning | Aspirational text should be rewritten as measurable obligations or moved to background. |
| `IT_REQ_009` | Multi-obligation statement review | Warning | Long statements containing multiple obligations should be decomposed. |
| `IT_REQ_010` | Evaluation linkage required | Blocker | Mandatory/scored requirements must link to an evaluation treatment. |
| `IT_REQ_011` | Price linkage required | Blocker | Priced deliverables must link to inventory and price schedule. |
| `IT_REQ_012` | Acceptance linkage required | Warning/blocker | Deliverables must link to acceptance/testing where applicable. |
| `IT_SCHED_001` | Schedule time basis required | Blocker | Implementation schedule must define time basis, preferably weeks from contract effectiveness for IT STD. |
| `IT_SCHED_002` | Operational acceptance required | Blocker | Schedule must include operational acceptance of integrated system unless explicitly waived. |
| `IT_SCHED_003` | LD milestone consistency | Blocker | LD milestones must link to SCC/GCC basis. |
| `IT_SCHED_004` | Site detail sufficiency | Warning | Site table should include enough detail to price delivery/installation. |
| `IT_INV_001` | Inventory line technical reference required | Blocker | Each inventory line must reference technical specifications. |
| `IT_INV_002` | Inventory line quantity required | Blocker | Countable inventory lines must have quantity and unit. |
| `IT_INV_003` | Recurrent period required | Blocker | Recurrent cost lines must define period and pricing treatment. |
| `IT_INV_004` | Inventory-price schedule consistency | Blocker | Inventory and price schedule lines must reconcile. |

---

## 20. Smoke contracts for Pass 4

### 20.1 Requirement authoring smoke contracts

| ID | Scenario | Expected result |
|---|---|---|
| `SMOKE-IT-P4-001` | Create a mandatory technical requirement without a response schema. | Block publication. |
| `SMOKE-IT-P4-002` | Create a background material using “Supplier must”. | Block or require conversion to requirement item. |
| `SMOKE-IT-P4-003` | Add a brand-specific product without equivalence or exception approval. | Raise blocker or high-severity warning based on package policy. |
| `SMOKE-IT-P4-004` | Add a performance requirement with no threshold. | Raise warning. |
| `SMOKE-IT-P4-005` | Add a scored requirement without scoring linkage. | Block publication. |
| `SMOKE-IT-P4-006` | Add a requirement that implies supply/install cost but no inventory line. | Block publication. |
| `SMOKE-IT-P4-007` | Add a requirement with evidence required but no evidence definition. | Block publication. |
| `SMOKE-IT-P4-008` | Add a long paragraph with multiple “shall/must” obligations. | Raise decomposition warning. |

### 20.2 Implementation schedule smoke contracts

| ID | Scenario | Expected result |
|---|---|---|
| `SMOKE-IT-P4-009` | Create implementation schedule without operational acceptance line. | Block publication unless waived by authorized reviewer. |
| `SMOKE-IT-P4-010` | Create subsystem milestone without inventory table. | Block publication. |
| `SMOKE-IT-P4-011` | Mark milestone as LD milestone without SCC/GCC reference. | Block publication. |
| `SMOKE-IT-P4-012` | Use calendar dates instead of weeks from contract effectiveness. | Warning or blocker depending on STD package policy. |
| `SMOKE-IT-P4-013` | Add site-based installation milestone without site table. | Block publication. |

### 20.3 System inventory smoke contracts

| ID | Scenario | Expected result |
|---|---|---|
| `SMOKE-IT-P4-014` | Add supply/install inventory item without quantity. | Block publication. |
| `SMOKE-IT-P4-015` | Add inventory item without technical specification reference. | Block publication. |
| `SMOKE-IT-P4-016` | Add recurrent cost table without pricing period. | Block publication. |
| `SMOKE-IT-P4-017` | Enable recurrent costs in TDS/SCC but omit recurrent inventory table. | Block publication. |
| `SMOKE-IT-P4-018` | Inventory table line does not reconcile with price schedule line. | Block publication. |

### 20.4 Supplier response smoke contracts

| ID | Scenario | Expected result |
|---|---|---|
| `SMOKE-IT-P4-019` | Supplier submits compliance matrix without reference pages where required. | Block submission or flag incomplete. |
| `SMOKE-IT-P4-020` | Supplier marks partial compliance without commentary. | Block submission. |
| `SMOKE-IT-P4-021` | Supplier uploads alternative response when alternatives are not permitted. | Block submission. |
| `SMOKE-IT-P4-022` | Evaluator tries to score requirement not published in tender. | Block evaluation entry. |

### 20.5 Addendum smoke contracts

| ID | Scenario | Expected result |
|---|---|---|
| `SMOKE-IT-P4-023` | PE changes published technical requirement. | Require addendum. |
| `SMOKE-IT-P4-024` | PE changes inventory quantity after publication. | Require addendum and regenerate affected price schedule/conformance matrix. |
| `SMOKE-IT-P4-025` | PE changes implementation milestone after publication. | Require addendum and impact analysis. |
| `SMOKE-IT-P4-026` | PE changes background material only. | Require addendum if rendered in published tender; otherwise internal version note. |

---

## 21. Activation blockers remaining after Pass 4

This pass is still not sufficient to activate the IT STD package.

The following work remains:

1. Full extraction of actual Part 2 boilerplate and all source anchors.
2. Formal render template implementation for Part 2.
3. Full form-to-requirement response integration.
4. Price schedule schema reconciliation with Pass 3.
5. Contract carry-forward mapping into Pass 5.
6. Legal/procurement review of mutability, guidance visibility, and render behavior.
7. Full smoke test implementation and passing result evidence.
8. Import package update and package checksum regeneration.

---

## 22. Recommended implementation order for Part 2 requirements

1. Build generalized requirement domain/group/item models.
2. Build compliance response schema generator.
3. Build background material model with non-binding validation.
4. Build implementation schedule model.
5. Build site and non-working day models.
6. Build system inventory table models.
7. Build inventory-price schedule cross-linker.
8. Build requirement-evaluation cross-linker.
9. Build requirement-acceptance cross-linker.
10. Build Part 2 renderer.
11. Build addendum impact detection for requirement, schedule, inventory, and background changes.
12. Load IT STD Part 2 seed schema.
13. Load NSSF ERP calibration fixture.
14. Run smoke contracts.
15. Submit package for procurement/legal review.

---

## 23. Next extraction pass

The next extraction artifact should be:

**IT STD Full Source Extraction Pass 5 — Contract Conditions, Contract Forms, Acceptance Certificates, Change Orders, and Contract Carry-Forward Schemas**

That pass should connect the work already completed in Passes 1 to 4 into contract execution, including:

1. GCC/SCC contract linkages.
2. Project Plan.
3. Design and engineering.
4. Procurement, delivery, installation, commissioning, and operational acceptance.
5. Defect liability.
6. Functional guarantees.
7. Intellectual property rights.
8. Software licenses.
9. Limitation of liability.
10. Change orders.
11. Contract appendices.
12. Acceptance certificates.
13. Performance and advance payment securities.
14. Beneficial ownership disclosure.

---

## 24. Final position

The IT STD implementation cannot be legally or operationally reliable unless Part 2 is fully structured.

The correct product decision is:

**Build the Part 2 Requirements Composer as a first-class engine component, not as an attachment feature.**

This allows KenTender to generate:

1. A compliant tender document.
2. A supplier technical response structure.
3. A technical evaluation matrix.
4. Price schedule cross-checks.
5. Implementation and acceptance milestones.
6. Contract deliverables.
7. Addendum impact reports.
8. A defensible audit trail.

That is the only approach that properly generalizes from the WORKS PoC to the IT STD and then onward to other STD families.
