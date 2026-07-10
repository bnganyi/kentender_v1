# STD for Procurement of Information Technology — Full Source Extraction Pass 5

## Contract Conditions, Contract Forms, Acceptance Certificates, Change Orders, and Contract Carry-Forward Schemas

**Document status:** Draft extraction artifact  
**Activation status:** Not activatable  
**Target STD package:** `KE-PPRA-IT-2022-04`  
**Engine scope:** Generalized STD Engine, with IT STD specialization  
**Prepared for:** KenTender e-Procurement System  
**Pass number:** 5 of the IT STD source extraction series  
**Generated:** 2026-07-07T20:44:16Z

---

## 1. Purpose of this extraction pass

This pass converts the official Information Technology STD’s **contract area** into implementable STD Engine schemas.

The specific focus is:

1. Contract Conditions.
2. General Conditions of Contract.
3. Special Conditions of Contract.
4. Contract Agreement.
5. Contract appendices.
6. Performance Security and Advance Payment Security forms.
7. Installation Certificate and Operational Acceptance Certificate.
8. Change Order procedures and forms.
9. Beneficial Ownership Disclosure.
10. Contract carry-forward from tender configuration, supplier response, evaluation, award, and accepted tender data.
11. Contract execution linkages for project plan, implementation schedule, acceptance, warranty, support, intellectual property, and change control.

The purpose is not merely to catalogue forms. The purpose is to define how the STD Engine must preserve the legal chain from **published tender** to **accepted tender** to **generated contract** to **contract execution events**.

---

## 2. Source basis

### 2.1 Official master source

The legal master source remains:

**DOC 10. Standard Tender Document for Procurement of Information Technology**  
Issued by the Public Procurement Regulatory Authority, Kenya.

The official IT STD contract area contains:

1. General Conditions of Contract.
2. Special Conditions of Contract.
3. Contract Forms.
4. Notification of Intention to Award.
5. Letter of Award.
6. Contract Agreement.
7. Contract appendices.
8. Performance and Advance Payment Security forms.
9. Installation and Acceptance Certificates.
10. Change Order Procedures and Forms.
11. Beneficial Ownership Disclosure Form.

### 2.2 Calibration fixture

The NSSF SPS ERP tender remains a calibration fixture only:

**NSSF SPS RFP ERP 2026 — Supply, Installation, Configuration, Customization, Testing, Commissioning and Maintenance of an ERP System.**

It is useful because it shows a real IT procurement instance with:

1. A simplified GCC section.
2. SCC values for scope, commencement, payment milestones, intellectual property, escrow, subcontracting, service levels, warranty, and performance security.
3. A phased implementation model.
4. Testing and acceptance requirements.
5. Contract forms.

It must not override the official STD. It should be used to validate whether the STD Engine can produce real-world contract artifacts without allowing uncontrolled legal editing.

---

## 3. Critical design conclusion from this pass

The most important conclusion is:

**Contract generation must be a structured carry-forward process, not a free-form upload of a signed contract draft.**

For IT procurement, the final contract is not a separate legal island. It must be generated from:

1. The active STD version.
2. The tender-specific TDS and SCC values.
3. The Procuring Entity’s requirements.
4. The accepted supplier technical proposal.
5. The accepted price schedules.
6. The accepted implementation schedule.
7. The accepted system inventory.
8. The evaluation and award decision.
9. Any approved contract finalization adjustments.
10. Any approved revised price schedules.
11. Any approved subcontractors.
12. The applicable securities.
13. The selected intellectual-property treatment.
14. The applicable warranty, defect liability, SLA, and operational acceptance provisions.

The engine therefore needs a **Contract Carry-Forward Layer** that records where each contract datum came from and prevents silent divergence between the tender, the accepted tender, and the signed contract.

---

## 4. Section-numbering and source-normalization flag

The IT STD source shows section numbering inconsistencies in the contract area. In different parts of the document, the contract area appears as:

1. Part 3 — Contract.
2. Section X — General Conditions of Contract.
3. Section XII — Special Conditions of Contract.
4. Section XIII — Contract Forms.
5. In the extracted body, the same area is also shown as Section VI, Section VII, and Section VIII in places.

This should be handled as a **source-normalization issue**, not as a model-design issue.

The engine must therefore store both:

| Field | Purpose |
|---|---|
| `canonical_component_type` | Stable internal meaning, such as `GENERAL_CONDITIONS_OF_CONTRACT`, `SPECIAL_CONDITIONS_OF_CONTRACT`, `CONTRACT_FORMS`. |
| `source_section_label` | The exact section label as printed or extracted from the official STD. |
| `source_page_range` | Page or anchor evidence. |
| `source_normalization_note` | Any numbering anomaly or extraction issue. |
| `legal_review_required` | Whether the anomaly must be checked before activation. |

The recommended canonical mapping for the IT STD package is:

| Canonical component | Official functional meaning | Mutability |
|---|---|---|
| `GCC` | General Conditions of Contract | Locked |
| `SCC` | Special Conditions of Contract | Controlled configuration |
| `CONTRACT_FORMS` | Award, agreement, securities, appendices, acceptance, change order, beneficial ownership forms | Controlled generated artifacts |

---

## 5. Generalized contract model for all STD families

The STD Engine should not hard-code the IT contract model. The following contract abstractions should be reusable across STDs.

| Concept | Generalized meaning |
|---|---|
| Contract Condition Set | A body of contract clauses governing the post-award relationship. |
| General Conditions | Locked legal clauses common to the STD family. |
| Special Conditions | Controlled parameters that supplement or amend the General Conditions. |
| Contract Form | A generated legal form used at award or contract formation. |
| Contract Appendix | Structured data attached to the Contract Agreement. |
| Security Instrument | Performance security, advance payment security, retention security, or other guarantee/bond required by the STD. |
| Acceptance Instrument | A certificate or formal sign-off evidencing delivery, installation, completion, taking-over, operational acceptance, or similar milestone. |
| Change Instrument | A structured change request, variation, change estimate, change proposal, change order, or change approval. |
| Contract Carry-Forward Mapping | A rule specifying how tender, evaluation, award, and accepted supplier data become contract data. |
| Contract Execution Event | A lifecycle event after award, such as effective date, commencement, installation, commissioning, acceptance, warranty start, defect notification, support event, or change order. |
| Contract Artifact Bundle | Immutable generated output containing contract forms, schedules, appendices, certificates, and audit metadata. |

### 5.1 Why this must be generalized

Different STD families have different contract objects:

| STD family | Contract object examples |
|---|---|
| Works | GCC, SCC, Contract Agreement, Performance Security, Advance Payment Security, Retention Security, taking-over, defects liability, variation orders. |
| Goods | GCC, SCC, delivery schedules, acceptance, warranty, performance security, advance payment security. |
| IT | GCC, SCC, Contract Agreement, software categories, custom materials, installation, operational acceptance, functional guarantees, IPR warranty, change orders. |
| Consulting | Contract data, key experts, deliverables, time-based/lump-sum payments, replacement of personnel, reports. |
| Non-consulting services | Service levels, deliverables, contract management reports, performance/security clauses. |

The engine must therefore support a configurable `Contract Artifact Type` catalogue rather than a fixed set of hard-coded forms.

---

## 6. Mutability model for the IT contract area

| Component | Treatment | Governance requirement |
|---|---|---|
| GCC clause text | Locked | No PE edit; any change requires new STD version and central approval. |
| SCC headings and references | Controlled | PE fills approved parameters only. |
| SCC values | Configurable | Must be validated against rule dictionary and legal/procurement review gates. |
| Contract Agreement structure | Controlled generated | Generated from award and accepted tender data; legal structure cannot be freely rewritten. |
| Contract appendices | Structured generated | Values carried from accepted tender, finalization discussion, and approved contract inputs. |
| Performance Security form | Controlled generated | Generated according to STD template and SCC amount/currency. |
| Advance Payment Security form | Conditional generated | Generated only when advance payment applies. |
| Acceptance certificates | Controlled execution forms | Generated from implementation milestones/subsystems; signed/issued during contract execution. |
| Change order forms | Controlled execution forms | Generated and routed through contract governance workflow. |
| Beneficial Ownership Disclosure | Controlled post-award form | Required from successful tenderer and JV members where applicable. |
| Rendered contract bundle | Immutable after signing | Any change after signing requires contract amendment/change order process. |

---

## 7. General Conditions of Contract extraction model

The IT STD GCC is a locked legal text area. It must be imported as clause records with source anchors and hashes.

### 7.1 GCC clause register

| GCC no. | Clause title | Engine treatment | Downstream linkage |
|---:|---|---|---|
| 1 | Contract and Interpretation / Definitions | Locked clause set | Contract schema, appendix definitions, software/material classifications. |
| 2 | Contract Documents | Locked clause | Contract Agreement document precedence. |
| 3 | Interpretation | Locked clause | Renderer and legal interpretation reference. |
| 4 | Notices | Locked clause with SCC values | Notice addresses and EDI/email protocol settings. |
| 5 | Governing Law | Locked clause with SCC value | Jurisdiction, dispute resolution, contract metadata. |
| 6 | Fraud and Corruption | Locked clause | Contract enforcement, termination triggers, audit. |
| 7 | Scope of the System | Locked clause with SCC and requirements linkage | Requirements, system inventory, recurrent cost items. |
| 8 | Time for Commencement and Operational Acceptance | Locked clause with SCC values | Effective date, commencement, operational acceptance deadline. |
| 9 | Supplier's Responsibilities | Locked clause | Execution obligations, compliance checks. |
| 10 | Procuring Entity's Responsibilities | Locked clause | PE obligations and project dependencies. |
| 11 | Contract Price | Locked clause with price schedule linkage | Accepted price schedules, revised price schedules. |
| 12 | Terms of Payment | Locked clause with SCC payment configuration | Milestones, advance payment, recurrent costs, payment certification. |
| 13 | Securities | Locked clause with SCC values | Performance Security and Advance Payment Security. |
| 14 | Taxes and Duties | Locked clause | Price schedule tax handling. |
| 15 | Copyright | Locked clause with SCC choices | IPR treatment, software categories, custom materials. |
| 16 | Software License Agreements | Locked clause with software appendix linkage | License records, standard/custom software categories. |
| 17 | Confidential Information | Locked clause | Confidentiality obligations and access controls. |
| 18 | Representatives | Locked clause with appendices | Supplier Representative, Project Manager. |
| 19 | Project Plan | Locked clause with deliverable workflow | Preliminary Project Plan, Agreed Project Plan, updates. |
| 20 | Subcontracting | Locked clause with appendix linkage | Approved Subcontractors Appendix, approval workflow. |
| 21 | Design and Engineering | Locked clause | Technical requirements, design deliverables, review events. |
| 22 | Procurement, Delivery, and Transport | Locked clause | System inventory, delivery events, incoterms if applicable. |
| 23 | Product Upgrades | Locked clause | Updates, versioning, product support. |
| 24 | Implementation, Installation, and Other Services | Locked clause | Implementation schedule, installation events, service obligations. |
| 25 | Inspections and Tests | Locked clause | Test scripts, test results, inspection events. |
| 26 | Installation of the System | Locked clause | Installation certificate, subsystem installation. |
| 27 | Commissioning and Operational Acceptance | Locked clause | Operational acceptance tests and certificate. |
| 28 | Operational Acceptance Time Guarantee | Locked clause | Delay/liquidated damages/acceptance deadline logic. |
| 29 | Defect Liability | Locked clause with SCC values | Warranty, defect liability, recurrent support. |
| 30 | Functional Guarantees | Locked clause | Performance guarantees, acceptance criteria. |
| 31 | Intellectual Property Rights Warranty | Locked clause | Supplier warranty and infringement checks. |
| 32 | Intellectual Property Rights Indemnity | Locked clause | Claims, indemnity, mitigation workflows. |
| 33 | Limitation of Liability | Locked clause with SCC parameters where applicable | Contract risk limits. |
| 34 | Transfer of Ownership | Locked clause | Ownership transfer of goods/system/materials. |
| 35 | Care of the System | Locked clause | Risk and care during implementation. |
| 36 | Loss or Damage / Accident / Injury / Indemnification | Locked clause | Incident and indemnity management. |
| 37 | Insurances | Locked clause with SCC values | Insurance evidence requirements. |
| 38 | Force Majeure | Locked clause | Force majeure notification and relief workflow. |
| 39 | Changes to the System | Locked clause | Change order workflow and forms. |
| 40 | Extension of Time for Achieving Operational Acceptance | Locked clause | Extension requests and schedule adjustment. |
| 41 | Termination | Locked clause | Termination workflow and grounds. |
| 42 | Assignment | Locked clause | Assignment restrictions and approvals. |
| 43 | Settlement of Disputes | Locked clause with SCC values | Adjudicator, arbitration, dispute workflow. |

### 7.2 GCC extraction fields

Each GCC clause should be stored as:

| Field | Required | Notes |
|---|---:|---|
| `clause_key` | Yes | Example: `KE-PPRA-IT-2022-04.gcc.27`. |
| `std_family_code` | Yes | `KE-PPRA-IT`. |
| `std_version_code` | Yes | `KE-PPRA-IT-2022-04`. |
| `canonical_component_type` | Yes | `GENERAL_CONDITIONS_OF_CONTRACT`. |
| `source_section_label` | Yes | Exact source label. |
| `clause_number` | Yes | Numeric or compound clause number. |
| `clause_title` | Yes | Official title. |
| `clause_text` | Yes | Exact normalized text. |
| `text_hash` | Yes | Hash of normalized legal text. |
| `mutability` | Yes | `LOCKED`. |
| `source_anchor_key` | Yes | Page/paragraph/line anchor. |
| `renderer_block_key` | Yes | Render target. |
| `linked_scc_parameter_keys` | Conditional | If SCC supplements this GCC clause. |
| `linked_execution_object_types` | Conditional | Example: `ACCEPTANCE_CERTIFICATE`, `CHANGE_ORDER`. |
| `review_status` | Yes | `EXTRACTED_PENDING_LEGAL_REVIEW` until verified. |

---

## 8. Special Conditions of Contract extraction model

The SCC supplements or amends the GCC. It is not free legal drafting space. It must be modeled as controlled parameters linked to specific GCC clauses.

### 8.1 SCC group register

| SCC group | Source basis | Engine treatment |
|---|---|---|
| A. Contract and Interpretation | Definitions, Procuring Entity, Project Manager, Post-Warranty Services Period | Controlled parameters. |
| Notices | Project Manager address, Procuring Entity fallback address, EDI standards/protocols if used | Controlled parameters. |
| B. Subject Matter of Contract | Scope of the System, recurrent cost items, spare parts where applicable | Controlled parameters linked to requirements/inventory/pricing. |
| C. Payment | Contract price adjustment, terms of payment, delayed payment interest, currency conversion | Controlled payment schema. |
| D. Intellectual Property | Copyright, Custom Software, Custom Materials, escrow | Controlled legal-choice model requiring elevated review. |
| E. Supply, Installation, Testing, Commissioning, and Acceptance | Sites, implementation schedule, acceptance tests, inspection, operational acceptance | Controlled execution schema. |
| F. Guarantees and Liabilities | Defect liability, functional guarantees, limitation of liability | Controlled risk and warranty parameters. |
| G. Risk Distribution | Insurances, risk allocation, care of system | Controlled risk parameters. |
| H. Change in Contract Elements | Change procedures, thresholds, forms, approvals | Controlled change workflow parameters. |
| I. Settlement of Disputes | Adjudicator, arbitration rules, appointing authority | Controlled dispute parameters. |

### 8.2 SCC parameter dictionary — minimum required records

| Parameter key | GCC link | Type | Required | Validation |
|---|---:|---|---:|---|
| `scc.procuring_entity_legal_name` | 1 | Text | Yes | Must match tender PE identity. |
| `scc.project_manager_name_or_title` | 1 / 18 | Text | Yes | Must be an authorized role or official. |
| `scc.contract_period_end_rule` | 1 | Enum | No | Default: obligations complete. Hard date requires justification. |
| `scc.post_warranty_services_period_months` | 1 | Integer | Conditional | Required if post-warranty services are included. |
| `scc.project_manager_notice_address` | 4 | Address object | Yes | Required before contract signing. |
| `scc.pe_fallback_notice_address` | 4 | Address object | Yes | Required before contract signing. |
| `scc.edi_enabled` | 4 | Boolean | No | If true, protocol details required. |
| `scc.edi_standards_protocols` | 4 | Structured text | Conditional | Required if EDI enabled. |
| `scc.recurrent_cost_items_included` | 7 | Reference list | Conditional | Must reference recurrent cost table lines. |
| `scc.spare_parts_obligation_enabled` | 7 | Boolean | No | If true, spare parts table and period required. |
| `scc.spare_parts_period_years` | 7 | Integer | Conditional | Required if spare parts obligation enabled. |
| `scc.commencement_period_days` | 8 | Integer | Yes | Must be positive; must align with tender timeline. |
| `scc.price_adjustment_enabled` | 11 | Boolean | Yes | Defaults to false unless justified. |
| `scc.price_adjustment_formula` | 11 | Formula object | Conditional | Required if price adjustment enabled. |
| `scc.payment_categories` | 12 | Structured list | Yes | Must total 100% for applicable categories. |
| `scc.advance_payment_enabled` | 12 / 13 | Boolean | Conditional | If true, advance payment security required. |
| `scc.advance_payment_percent` | 12 | Decimal | Conditional | Must align with security and payment schema. |
| `scc.delayed_payment_interest_rate` | 12 | Decimal | Conditional | Required if interest applies. |
| `scc.payment_currency` | 12 | Currency | Yes | Must align with price schedules. |
| `scc.exchange_rate_source` | 12 | Text | Conditional | Required if payment currency differs from KES/local currency. |
| `scc.performance_security_percent` | 13 | Decimal | Yes | Must comply with allowed range. |
| `scc.performance_security_currency` | 13 | Currency | Yes | Must align with contract currency or accepted convertible currency. |
| `scc.performance_security_warranty_reduction_percent` | 13 | Decimal | Conditional | Required if security reduces during warranty. |
| `scc.ipr_custom_software_strategy` | 15 | Enum | Conditional | Legal review required. |
| `scc.custom_software_source_code_access` | 15 | Enum | Conditional | Required when custom software exists. |
| `scc.software_escrow_required` | 15 | Boolean | Conditional | Required decision for application/custom software. |
| `scc.software_escrow_agent` | 15 | Text | Conditional | Required if escrow is required. |
| `scc.software_escrow_release_triggers` | 15 | Structured list | Conditional | Required if escrow is required. |
| `scc.custom_materials_ipr_strategy` | 15 | Enum | Conditional | Legal review required. |
| `scc.license_transfer_rights` | 16 | Structured text | Conditional | Required where software license terms affect PE use. |
| `scc.confidentiality_special_terms` | 17 | Structured text | No | Legal review required if supplied. |
| `scc.subcontractor_preapproval_required` | 20 | Boolean | Yes | Default true. |
| `scc.design_review_period_days` | 21 | Integer | Conditional | Required if design submissions exist. |
| `scc.installation_sites` | 24 / 26 | Reference list | Yes | Must reference implementation site table. |
| `scc.operational_acceptance_test_framework` | 27 | Reference | Yes | Must reference acceptance/test schema. |
| `scc.operational_acceptance_deadline` | 8 / 27 / 28 | Date or duration | Yes | Must align with implementation schedule. |
| `scc.defect_liability_period_months` | 29 | Integer | Yes | Must align with warranty/support requirements. |
| `scc.functional_guarantee_items` | 30 | Reference list | Conditional | Required if functional guarantees are specified. |
| `scc.limitation_of_liability_cap` | 33 | Money/percent | Conditional | Legal/procurement review required. |
| `scc.insurance_requirements` | 37 | Structured list | Conditional | Must define evidence and validity. |
| `scc.change_order_authority_thresholds` | 39 | Structured list | Yes | Required for change governance. |
| `scc.extension_of_time_rules` | 40 | Structured rule set | Yes | Must link to schedule-change workflow. |
| `scc.termination_special_terms` | 41 | Structured text | No | Legal review required. |
| `scc.adjudicator_required` | 43 | Boolean | Yes | If true, Appendix 2 required. |
| `scc.appointing_authority` | 43 | Text | Conditional | Required if adjudicator can be appointed externally. |
| `scc.arbitration_rules` | 43 | Text | Yes | Required before contract signing. |

---

## 9. Contract Agreement schema

The Contract Agreement should be generated only after award approval and standstill handling are complete.

### 9.1 Contract Agreement generation inputs

| Input | Source object |
|---|---|
| Procuring Entity legal name | Tender configuration / SCC. |
| Supplier legal name | Successful tenderer record. |
| Supplier registration country/address | Tenderer eligibility form and award data. |
| Contract title | Tender identity. |
| Contract number | Tender/award/contract module. |
| System description | PE requirements and accepted supplier offer. |
| Contract price | Accepted and corrected price schedule. |
| Payment terms | SCC payment configuration. |
| Contract documents list | STD contract schema. |
| Order of precedence | Contract Agreement template. |
| Effective date conditions | Contract Agreement and GCC/SCC. |
| Performance Security | Security instrument record. |
| Advance Payment Security | Conditional security instrument record. |
| Appendices | Contract appendix records. |
| Finalization minutes | Contract finalization record. |

### 9.2 Contract documents order of precedence

The Contract Agreement should render a controlled order of precedence. The official structure lists:

1. Contract Agreement and appendices.
2. Special Conditions of Contract.
3. General Conditions of Contract.
4. Technical Requirements, including Implementation Schedule.
5. Supplier’s tender and original Price Schedules.
6. Additional documents, if approved.

The engine must store the order as structured records, not as an editable paragraph.

### 9.3 Contract Agreement schema fields

| Field | Type | Required | Source |
|---|---|---:|---|
| `contract_agreement_key` | ID | Yes | Generated. |
| `tender_key` | Reference | Yes | Tender record. |
| `award_key` | Reference | Yes | Award decision. |
| `std_version_code` | Reference | Yes | Active STD used for tender. |
| `procuring_entity_legal_name` | Text | Yes | SCC / PE profile. |
| `procuring_entity_address` | Address | Yes | SCC / PE profile. |
| `supplier_legal_name` | Text | Yes | Successful tenderer. |
| `supplier_address` | Address | Yes | Tenderer form. |
| `supplier_country` | Text | Yes | Tenderer form. |
| `system_description` | Long text | Yes | Requirements and award. |
| `contract_price_by_currency` | Money array | Yes | Accepted price schedule. |
| `grand_summary_price_schedule_reference` | Reference | Yes | Accepted price schedule. |
| `tax_treatment_summary` | Structured object | Conditional | Price schedule. |
| `effective_date_conditions` | Structured list | Yes | Contract template. |
| `appendix_keys` | Reference list | Yes | Contract appendices. |
| `document_precedence_order` | Structured list | Yes | STD contract schema. |
| `signatory_pe_name_title` | Text | Yes | Contract execution. |
| `signatory_supplier_name_title` | Text | Yes | Contract execution. |
| `signed_date` | Date | Conditional | Execution. |
| `contract_hash` | Hash | Yes after generation | Generated artifact. |

---

## 10. Contract appendices schema

The IT STD includes seven core appendices. These must be modeled as structured contract artifacts.

| Appendix | Title | Source | Generation source | Required |
|---:|---|---|---|---:|
| 1 | Supplier’s Representative | Contract Agreement / GCC Representatives | Successful tenderer and contract finalization | Yes |
| 2 | Adjudicator | GCC dispute settlement / SCC | SCC and finalization | Conditional |
| 3 | List of Approved Subcontractors | GCC Subcontracting | Accepted tender and PE approval | Conditional |
| 4 | Categories of Software | GCC definitions / IPR / licensing | Accepted supplier offer and IP forms | Yes for software procurements |
| 5 | Custom Materials | GCC definitions / IPR | Accepted supplier offer and PE requirements | Conditional |
| 6 | Revised Price Schedules | Contract finalization / price corrections | Evaluation and finalization | Conditional |
| 7 | Minutes of Contract Finalization Discussions and Agreed-to Contract Amendments | Contract finalization | Finalization workflow | Conditional but should always be explicitly recorded as `not applicable` if absent |

### 10.1 Appendix 1 — Supplier Representative

| Field | Type | Required | Source |
|---|---|---:|---|
| `supplier_representative_name` | Text | Yes | Supplier nomination / finalization. |
| `supplier_representative_title` | Text | Yes | Supplier nomination. |
| `supplier_representative_address` | Address | Yes | Supplier nomination. |
| `supplier_notice_address` | Address | Yes | Supplier nomination. |
| `fallback_supplier_address` | Address | Yes | Supplier profile. |
| `nomination_due_days_after_effective_date` | Integer | Conditional | Required if representative not named at signing. |

### 10.2 Appendix 2 — Adjudicator

| Field | Type | Required | Source |
|---|---|---:|---|
| `adjudicator_applicable` | Boolean | Yes | SCC. |
| `adjudicator_name` | Text | Conditional | Required if applicable. |
| `adjudicator_title` | Text | Conditional | Required if applicable. |
| `adjudicator_address` | Address | Conditional | Required if applicable. |
| `adjudicator_phone` | Text | Conditional | Required if applicable. |
| `hourly_fee` | Money | Conditional | Required if applicable. |
| `reimbursable_expenses` | List | Conditional | Required if applicable. |
| `appointing_authority` | Text | Conditional | Required if no adjudicator is agreed at signing. |

### 10.3 Appendix 3 — Approved Subcontractors

| Field | Type | Required | Source |
|---|---|---:|---|
| `subcontractor_item` | Text | Yes | Supplier tender / finalization. |
| `subcontractor_name` | Text | Yes | Supplier tender. |
| `place_of_registration` | Text | Yes | Supplier tender. |
| `approved_scope` | Long text | Yes | PE approval. |
| `approval_date` | Date | Yes | Contract finalization. |
| `approval_reference` | Text | Yes | Workflow/audit record. |

### 10.4 Appendix 4 — Categories of Software

The engine must classify each software item along two dimensions:

1. Functional category: System Software, General-Purpose Software, or Application Software.
2. IPR/commercial category: Standard Software or Custom Software.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `software_item_name` | Text | Yes | Each named software item. |
| `software_item_description` | Long text | Yes | Description. |
| `functional_category` | Enum | Yes | `SYSTEM_SOFTWARE`, `GENERAL_PURPOSE_SOFTWARE`, `APPLICATION_SOFTWARE`. |
| `customization_category` | Enum | Yes | `STANDARD_SOFTWARE`, `CUSTOM_SOFTWARE`. |
| `license_type` | Enum | Conditional | Subscription, perpetual, open-source, SaaS, OEM, custom, other. |
| `license_owner` | Text | Conditional | Required if third-party licensed. |
| `license_term` | Text | Conditional | Required if license-based. |
| `source_code_access_required` | Boolean | Conditional | Required for custom software. |
| `escrow_required` | Boolean | Conditional | Required for application/custom software decision. |
| `ipr_treatment_key` | Reference | Conditional | Link to SCC IPR strategy. |

### 10.5 Appendix 5 — Custom Materials

| Field | Type | Required | Source |
|---|---|---:|---|
| `custom_material_name` | Text | Yes | Supplier tender / PE requirements. |
| `custom_material_description` | Long text | Yes | Supplier tender / PE requirements. |
| `format_or_medium` | Text | Conditional | Documentation, training material, designs, data models, manuals, etc. |
| `ipr_owner` | Enum | Yes | PE, supplier, joint, licensed. |
| `usage_rights` | Long text | Yes | SCC/legal review. |
| `delivery_milestone` | Reference | Conditional | Implementation schedule. |

### 10.6 Appendix 6 — Revised Price Schedules

| Field | Type | Required | Source |
|---|---|---:|---|
| `revised_price_schedule_required` | Boolean | Yes | Finalization. |
| `original_price_schedule_reference` | Reference | Conditional | Accepted tender. |
| `revision_reason` | Enum | Conditional | Arithmetic correction, validity extension, negotiated clarification, approved finalization adjustment, other. |
| `revised_schedule_reference` | Reference | Conditional | Finalized price schedule. |
| `difference_summary` | Money object | Conditional | Change from accepted tender. |
| `approval_reference` | Text | Conditional | Procurement/legal approval. |

### 10.7 Appendix 7 — Finalization Minutes and Agreed Amendments

| Field | Type | Required | Source |
|---|---|---:|---|
| `finalization_meeting_required` | Boolean | Yes | Contract workflow. |
| `meeting_date` | Date | Conditional | Finalization. |
| `attendees` | List | Conditional | Finalization. |
| `agreed_amendments` | Structured list | Conditional | Finalization. |
| `affected_contract_documents` | Reference list | Conditional | Contract schema. |
| `amendment_precedence_flag` | Boolean | Yes | True if Appendix 7 overrides affected terms. |
| `legal_review_reference` | Text | Conditional | Required where contract terms are affected. |

---

## 11. Security instrument schemas

### 11.1 Performance Security

The Performance Security is required after award according to the GCC/SCC framework. It should be represented as a contract security object and a generated form.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `security_key` | ID | Yes | Generated. |
| `security_type` | Enum | Yes | `PERFORMANCE_SECURITY`. |
| `supplier_key` | Reference | Yes | Successful tenderer. |
| `beneficiary_name` | Text | Yes | Procuring Entity. |
| `guarantor_name` | Text | Yes | Bank/insurance/guarantor. |
| `guarantor_address` | Address | Yes | Issuing branch/office. |
| `guarantee_number` | Text | Yes | Instrument number. |
| `contract_number` | Text | Yes | Contract record. |
| `contract_title` | Text | Yes | Tender/contract title. |
| `security_amount` | Money | Yes | From SCC. |
| `security_percent` | Decimal | Yes | From SCC. |
| `currency` | Currency | Yes | From SCC. |
| `valid_from` | Date | Yes | Contract execution. |
| `valid_until` | Date | Yes | Must meet SCC validity rule. |
| `reduction_after_operational_acceptance` | Boolean | Conditional | From SCC. |
| `reduced_amount_or_percent` | Money/percent | Conditional | From SCC. |
| `form_template_key` | Reference | Yes | Performance Security form. |
| `instrument_hash` | Hash | Yes after upload/render | Evidence integrity. |
| `verification_status` | Enum | Yes | Pending, verified, rejected, expired. |

### 11.2 Advance Payment Security

The Advance Payment Security is conditional. It is generated and required only if the SCC/payment terms provide for an advance payment.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `security_type` | Enum | Yes | `ADVANCE_PAYMENT_SECURITY`. |
| `advance_payment_enabled` | Boolean | Yes | From SCC. |
| `advance_payment_amount` | Money | Conditional | Required if advance payment enabled. |
| `advance_payment_percent` | Decimal | Conditional | Required if advance payment enabled. |
| `guarantee_amount` | Money | Conditional | Should secure the full advance amount. |
| `valid_until_rule` | Rule | Conditional | Must cover advance recovery. |
| `linked_payment_milestone_key` | Reference | Conditional | Advance milestone. |
| `verification_status` | Enum | Conditional | Required if issued. |

### 11.3 Security rules

| Rule key | Rule |
|---|---|
| `CONTRACT.SECURITY.PERFORMANCE_REQUIRED_BEFORE_EFFECTIVE_DATE` | Contract cannot become effective unless required Performance Security is recorded and verified, unless the STD/SCC explicitly allows a different effective-date rule. |
| `CONTRACT.SECURITY.ADVANCE_REQUIRES_SECURITY` | Advance payment cannot be released unless Advance Payment Security is recorded and verified. |
| `CONTRACT.SECURITY.VALIDITY_MUST_COVER_REQUIRED_PERIOD` | Security validity must satisfy SCC requirements. |
| `CONTRACT.SECURITY.AMOUNT_MUST_MATCH_SCC` | Security amount must equal the amount/percentage configured in SCC. |
| `CONTRACT.SECURITY.EXPIRY_ALERTS_REQUIRED` | System must generate expiry alerts before security expiry. |

---

## 12. Acceptance certificate schemas

The IT STD includes recommended Installation and Operational Acceptance Certificates.

The engine must distinguish:

1. Installation readiness/completion.
2. Commissioning/testing.
3. Operational Acceptance.
4. Defect/warranty start.
5. Phase/subsystem acceptance where the tender allows phased implementation.

### 12.1 Installation Certificate schema

| Field | Type | Required | Source |
|---|---|---:|---|
| `installation_certificate_key` | ID | Yes | Generated. |
| `contract_key` | Reference | Yes | Contract. |
| `system_or_subsystem_key` | Reference | Yes | Requirements / implementation schedule. |
| `major_component_key` | Reference | Conditional | Inventory / subsystem. |
| `description_of_system_or_component` | Long text | Yes | Implementation schedule / inventory. |
| `installation_date` | Date | Yes | Contract execution. |
| `site_key` | Reference | Conditional | Site table. |
| `supplier_representative` | Reference | Yes | Appendix 1. |
| `project_manager` | Reference | Yes | SCC. |
| `installation_exceptions` | Long text | Conditional | Punch list / defects. |
| `attachments` | Evidence list | Conditional | Test logs, installation reports, photos, handover notes. |
| `issued_by` | User/official | Yes | Contract manager/project manager. |
| `issued_date` | Date | Yes | Execution event. |
| `certificate_hash` | Hash | Yes | Generated artifact. |

### 12.2 Operational Acceptance Certificate schema

| Field | Type | Required | Source |
|---|---|---:|---|
| `operational_acceptance_certificate_key` | ID | Yes | Generated. |
| `contract_key` | Reference | Yes | Contract. |
| `system_or_subsystem_key` | Reference | Yes | Requirements / schedule. |
| `acceptance_date` | Date | Yes | Execution event. |
| `operational_acceptance_test_reference` | Reference | Yes | Testing/acceptance plan. |
| `test_result_summary` | Structured object | Yes | Test records. |
| `unresolved_defects` | List | Conditional | Must be classified. |
| `accepted_with_exceptions` | Boolean | Yes | True only with authorized exception record. |
| `exception_resolution_deadline` | Date | Conditional | Required if accepted with exceptions. |
| `warranty_start_date` | Date | Yes | Normally acceptance date. |
| `defect_liability_start_date` | Date | Yes | Normally acceptance date. |
| `functional_guarantee_status` | Enum | Conditional | Pass, conditional, fail. |
| `issued_by` | User/official | Yes | Authorized PE official. |
| `supplier_acknowledgement` | Boolean | Conditional | If workflow requires. |
| `certificate_hash` | Hash | Yes | Generated artifact. |

### 12.3 Phase/subsystem acceptance

The engine must support partial operational acceptance when the tender/contract allows:

| Acceptance mode | Description | Example |
|---|---|---|
| Full system acceptance | One acceptance certificate covers the complete system. | Single integrated ERP go-live. |
| Subsystem acceptance | Each subsystem/module is accepted separately. | Payroll, finance, procurement modules. |
| Phase acceptance | Each implementation phase is accepted separately. | NSSF Phase 1 and Phase 2. |
| Conditional acceptance | Acceptance with approved exceptions/punch-list items. | Non-critical defects with deadline. |

### 12.4 Acceptance rules

| Rule key | Rule |
|---|---|
| `CONTRACT.ACCEPTANCE.INSTALLATION_BEFORE_OPERATIONAL_ACCEPTANCE` | Operational Acceptance cannot be issued before installation is recorded for the applicable system/subsystem, unless an authorized exception exists. |
| `CONTRACT.ACCEPTANCE.TEST_RESULTS_REQUIRED` | Operational Acceptance requires completed test results and approval. |
| `CONTRACT.ACCEPTANCE.WARRANTY_STARTS_FROM_ACCEPTANCE` | Warranty/defect liability start date must be set from Operational Acceptance unless SCC provides another rule. |
| `CONTRACT.ACCEPTANCE.PHASE_LINK_REQUIRED` | Phase acceptance certificates must link to implementation phase/milestone records. |
| `CONTRACT.ACCEPTANCE.EXCEPTIONS_REQUIRE_DEADLINE` | Acceptance with exceptions requires exception list, severity, owner, and resolution deadline. |

---

## 13. Change Order procedures and forms

The IT STD includes a structured change process with related forms. This is a major implementation requirement.

The engine must provide a contract change workflow separate from tender addenda.

| Process | When used |
|---|---|
| Tender Addendum | Before contract signing, to amend published tender documents. |
| Contract Change Order | After contract signing, to amend the system, schedule, price, functional guarantees, or contract obligations according to GCC/SCC change provisions. |

### 13.1 Change Order form catalogue

| Form | Originator | Purpose |
|---|---|---|
| Request for Change Proposal | Procuring Entity | Requests Supplier to prepare a change proposal. |
| Change Estimate Proposal | Supplier | States approximate cost/time to prepare a detailed change proposal. |
| Estimate Acceptance Form | Procuring Entity | Authorizes Supplier to prepare the formal change proposal. |
| Change Proposal Form | Supplier | Provides detailed change proposal, price impact, schedule impact, technical impact, and guarantee impact. |
| Change Order Form | Procuring Entity / authorized authority | Orders the approved change and updates contract obligations. |
| Application for Change Proposal | Supplier | Allows Supplier to initiate a proposed change for PE consideration. |

### 13.2 Change Order workflow

```text
NO_CHANGE
  → CHANGE_INITIATED
  → CHANGE_ESTIMATE_REQUESTED
  → CHANGE_ESTIMATE_SUBMITTED
  → ESTIMATE_ACCEPTED
  → CHANGE_PROPOSAL_SUBMITTED
  → CHANGE_PROPOSAL_UNDER_REVIEW
  → CHANGE_APPROVED
  → CHANGE_ORDER_ISSUED
  → CHANGE_IMPLEMENTATION_IN_PROGRESS
  → CHANGE_IMPLEMENTED
  → CHANGE_ACCEPTED
```

Negative/terminal states:

```text
CHANGE_REJECTED
CHANGE_WITHDRAWN
CHANGE_CANCELLED
CHANGE_SUPERSEDED
```

### 13.3 Request for Change Proposal schema

| Field | Type | Required |
|---|---|---:|
| `request_for_change_key` | ID | Yes |
| `contract_key` | Reference | Yes |
| `request_number` | Text | Yes |
| `revision_number` | Integer | Yes |
| `title_of_change` | Text | Yes |
| `originator_type` | Enum | Yes |
| `originator_name` | Text | Yes |
| `brief_description` | Long text | Yes |
| `affected_system_or_subsystem` | Reference | Conditional |
| `affected_requirements` | Reference list | Conditional |
| `affected_inventory_items` | Reference list | Conditional |
| `technical_documents_or_drawings` | Evidence list | Conditional |
| `special_conditions` | Long text | Conditional |
| `response_due_days` | Integer | Yes |
| `approval_to_request_reference` | Text | Yes |
| `status` | Enum | Yes |

### 13.4 Change Estimate Proposal schema

| Field | Type | Required |
|---|---|---:|
| `change_estimate_key` | ID | Yes |
| `request_for_change_key` | Reference | Yes |
| `change_estimate_number` | Text | Yes |
| `brief_implementation_approach` | Long text | Yes |
| `initial_schedule_impact` | Duration / Long text | Yes |
| `initial_cost_estimate` | Money object | Yes |
| `proposal_preparation_cost` | Money object | Yes |
| `price_breakdown` | Structured list | Conditional |
| `supplier_representative_signature` | Signature | Yes |
| `submission_date` | Date | Yes |

### 13.5 Estimate Acceptance schema

| Field | Type | Required |
|---|---|---:|
| `estimate_acceptance_key` | ID | Yes |
| `change_estimate_key` | Reference | Yes |
| `estimate_acceptance_number` | Text | Yes |
| `accepted_preparation_cost` | Money object | Yes |
| `authorization_to_prepare_proposal` | Boolean | Yes |
| `other_terms_and_conditions` | Long text | Conditional |
| `approved_by` | User/official | Yes |
| `approval_date` | Date | Yes |
| `approval_reference` | Text | Yes |

### 13.6 Change Proposal schema

| Field | Type | Required |
|---|---|---:|
| `change_proposal_key` | ID | Yes |
| `request_for_change_key` | Reference | Yes |
| `change_proposal_number` | Text | Yes |
| `title_of_change` | Text | Yes |
| `originator_type` | Enum | Yes |
| `brief_description` | Long text | Yes |
| `reason_for_change` | Long text | Yes |
| `affected_system_or_subsystem` | Reference | Conditional |
| `affected_requirements` | Reference list | Conditional |
| `affected_inventory_items` | Reference list | Conditional |
| `technical_documents` | Evidence list | Conditional |
| `contract_price_increase_or_decrease` | Money object | Yes |
| `cost_to_prepare_proposal` | Money object | Conditional |
| `additional_time_required` | Duration | Conditional |
| `effect_on_functional_guarantees` | Long text | Conditional |
| `effect_on_contract_terms` | Long text | Conditional |
| `proposal_validity_days` | Integer | Yes |
| `supplier_signature` | Signature | Yes |
| `submission_date` | Date | Yes |

### 13.7 Change Order schema

| Field | Type | Required |
|---|---|---:|
| `change_order_key` | ID | Yes |
| `change_proposal_key` | Reference | Yes |
| `change_order_number` | Text | Yes |
| `approved_change_description` | Long text | Yes |
| `approved_contract_price_adjustment` | Money object | Yes |
| `approved_schedule_adjustment` | Duration | Conditional |
| `approved_requirement_changes` | Reference list | Conditional |
| `approved_inventory_changes` | Reference list | Conditional |
| `approved_functional_guarantee_changes` | Reference list | Conditional |
| `affected_contract_documents` | Reference list | Yes |
| `budget_confirmation_reference` | Text | Conditional |
| `legal_review_reference` | Text | Conditional |
| `procurement_approval_reference` | Text | Yes |
| `authorized_signatory` | User/official | Yes |
| `issue_date` | Date | Yes |
| `implementation_status` | Enum | Yes |
| `change_order_hash` | Hash | Yes |

### 13.8 Change governance rules

| Rule key | Rule |
|---|---|
| `CONTRACT.CHANGE.NO_WORK_BEFORE_APPROVAL` | Supplier may not proceed with change work until price and schedule impact are accepted in writing, unless emergency rules are configured and authorized. |
| `CONTRACT.CHANGE.PRICE_IMPACT_REQUIRES_BUDGET_CHECK` | Any positive contract price adjustment requires budget confirmation. |
| `CONTRACT.CHANGE.SCHEDULE_IMPACT_REQUIRES_EOT_REVIEW` | Any schedule extension must trigger extension-of-time review. |
| `CONTRACT.CHANGE.FUNCTIONAL_GUARANTEE_IMPACT_REQUIRES_TECHNICAL_REVIEW` | Any change affecting functional guarantees requires technical and legal review. |
| `CONTRACT.CHANGE.CONTRACT_TERM_IMPACT_REQUIRES_LEGAL_REVIEW` | Any change affecting GCC, SCC, or Contract Agreement terms requires legal review. |
| `CONTRACT.CHANGE.AUDIT_CHAIN_REQUIRED` | Change Order must trace to request, estimate, acceptance, proposal, approvals, and issued order. |
| `CONTRACT.CHANGE.ADDENDUM_NOT_ALLOWED_AFTER_CONTRACT` | Post-contract changes must use contract change workflow, not tender addendum workflow. |

---

## 14. Beneficial Ownership Disclosure schema

The IT STD includes a Beneficial Ownership Disclosure Form for the successful tenderer. The engine must treat this as a post-award/compliance form and not as a generic attachment.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `beneficial_ownership_form_key` | ID | Yes | Generated. |
| `contract_key` | Reference | Yes | Contract. |
| `supplier_key` | Reference | Yes | Successful tenderer. |
| `jv_member_key` | Reference | Conditional | Required for each JV member. |
| `beneficial_owner_name` | Text | Yes | Natural person. |
| `nationality` | Text | Yes | As disclosed. |
| `identity_document_type` | Enum | Yes | National ID, passport, etc. |
| `identity_document_number` | Text | Yes | Sensitive; apply access control. |
| `ownership_or_control_nature` | Enum/list | Yes | Ownership, voting rights, control, nominee, other. |
| `ownership_percentage` | Decimal | Conditional | Required where applicable. |
| `effective_control_description` | Long text | Conditional | Required where control is not purely shareholding. |
| `submission_date` | Date | Yes | Current as of submission. |
| `declaration_signature` | Signature | Yes | Authorized person. |
| `verification_status` | Enum | Yes | Pending, verified, rejected. |

### 14.1 Beneficial ownership rules

| Rule key | Rule |
|---|---|
| `CONTRACT.BO.SUCCESSFUL_TENDERER_REQUIRED` | Beneficial Ownership Disclosure is required from the successful tenderer before contract finalization where applicable. |
| `CONTRACT.BO.JV_MEMBER_REQUIRED` | If the successful tenderer is a JV, each JV member must submit a separate disclosure. |
| `CONTRACT.BO.CURRENT_AS_OF_SUBMISSION` | Disclosure must include an effective/current date. |
| `CONTRACT.BO.RESTRICTED_ACCESS` | Beneficial ownership data must be access-controlled and audited. |

---

## 15. Contract carry-forward model

The Contract Carry-Forward Layer maps upstream procurement data into downstream contract records.

### 15.1 Carry-forward categories

| Carry-forward category | Upstream source | Contract destination |
|---|---|---|
| Tender identity | Tender configuration | Contract title, number, project, PE identity. |
| STD version | Published tender bundle | Contract metadata and legal source. |
| SCC values | Tender configuration | SCC rendered contract values. |
| Supplier identity | Successful tenderer | Contract Agreement party details. |
| Supplier representative | Tender/finalization | Appendix 1. |
| Adjudicator | SCC/finalization | Appendix 2. |
| Subcontractors | Supplier tender and PE approval | Appendix 3. |
| Software categories | Supplier technical proposal/IP forms | Appendix 4. |
| Custom materials | Supplier proposal/requirements | Appendix 5. |
| Price schedules | Accepted tender / corrections | Contract price and Appendix 6. |
| Contract finalization minutes | Finalization workflow | Appendix 7. |
| Requirements | Published requirements + accepted proposal | Technical Requirements contract document. |
| Implementation schedule | Accepted supplier schedule | Contract schedule and milestones. |
| System inventory | Accepted system inventory | Scope and price schedule. |
| Functional guarantees | Requirements / accepted proposal / SCC | GCC 30-linked guarantee records. |
| Acceptance tests | Technical requirements and project plan | Operational acceptance workflow. |
| Payment terms | SCC / accepted price schedule | Contract payment milestones. |
| Securities | SCC / award | Security instruments. |
| Warranty and support | SCC / requirements / accepted proposal | Defect liability and support obligations. |
| Beneficial ownership | Successful tenderer / JV members | Post-award disclosure record. |

### 15.2 Carry-forward record schema

| Field | Type | Required |
|---|---|---:|
| `carry_forward_key` | ID | Yes |
| `std_version_code` | Reference | Yes |
| `tender_key` | Reference | Yes |
| `award_key` | Reference | Conditional |
| `source_object_type` | Enum | Yes |
| `source_object_key` | Reference | Yes |
| `source_field_path` | Text | Yes |
| `target_object_type` | Enum | Yes |
| `target_object_key` | Reference | Conditional |
| `target_field_path` | Text | Yes |
| `transformation_rule_key` | Reference | Conditional |
| `carry_forward_status` | Enum | Yes |
| `requires_review` | Boolean | Yes |
| `review_role` | Role | Conditional |
| `carried_value_hash` | Hash | Yes |
| `created_at` | Timestamp | Yes |
| `approved_at` | Timestamp | Conditional |

### 15.3 Carry-forward statuses

```text
PENDING
CARRIED_FORWARD_AUTOMATICALLY
CARRIED_FORWARD_REQUIRES_CONFIRMATION
CONFIRMED
REJECTED
SUPERSEDED
LOCKED_IN_CONTRACT_BUNDLE
```

---

## 16. Contract generation lifecycle

### 16.1 Lifecycle states

```text
NOT_STARTED
  → AWARD_DECISION_APPROVED
  → STANDSTILL_PENDING
  → READY_FOR_CONTRACT_FINALIZATION
  → CONTRACT_FINALIZATION_IN_PROGRESS
  → CONTRACT_DRAFT_GENERATED
  → CONTRACT_DRAFT_UNDER_REVIEW
  → CONTRACT_APPROVED_FOR_SIGNATURE
  → CONTRACT_SIGNED
  → CONTRACT_EFFECTIVE_PENDING_CONDITIONS
  → CONTRACT_EFFECTIVE
  → IMPLEMENTATION_IN_PROGRESS
  → INSTALLATION_CERTIFIED
  → COMMISSIONING_IN_PROGRESS
  → OPERATIONAL_ACCEPTANCE_CERTIFIED
  → WARRANTY_IN_PROGRESS
  → WARRANTY_COMPLETED
  → CONTRACT_COMPLETED
```

Exception states:

```text
CONTRACT_FINALIZATION_FAILED
CONTRACT_REVIEW_REJECTED
SIGNATURE_CANCELLED
CONTRACT_TERMINATED
CONTRACT_SUSPENDED
DISPUTE_ACTIVE
CHANGE_ORDER_ACTIVE
```

### 16.2 Transition controls

| Transition | Required controls |
|---|---|
| Award approved → Standstill pending | Award decision approved; notification artifacts generated. |
| Standstill pending → Ready for finalization | Standstill period handled; complaints/debriefings resolved or recorded. |
| Ready → Finalization | Successful tenderer selected; accepted tender data locked. |
| Finalization → Draft generated | Carry-forward mapping complete; required SCC values complete. |
| Draft generated → Under review | Contract bundle hash generated; review task created. |
| Under review → Approved for signature | Procurement, legal, and technical approvals completed as required. |
| Approved → Signed | Authorized signatures captured. |
| Signed → Effective pending conditions | Effective-date conditions evaluated. |
| Effective pending → Effective | Required securities and advance conditions satisfied. |
| Effective → Implementation | Commencement instruction/event recorded. |
| Implementation → Installation certified | Installation evidence and certificate issued. |
| Installation → Operational acceptance | Test results, commissioning, UAT, and acceptance evidence complete. |
| Operational acceptance → Warranty | Acceptance certificate issued; warranty start date recorded. |
| Warranty → Completed | Warranty period complete; unresolved defects closed or handled. |

---

## 17. IT-specific execution objects

The IT STD contract area requires the contract module to understand IT-specific execution concepts.

| Object | Purpose |
|---|---|
| Agreed Project Plan | Supplier’s post-award project plan approved by the Procuring Entity. |
| Design Submission | Supplier design/engineering output for review. |
| Software Classification Register | Contract Appendix 4 operationalized. |
| Custom Materials Register | Contract Appendix 5 operationalized. |
| License Register | Tracks software license agreements, terms, renewal, restrictions, and evidence. |
| Source Code / Escrow Register | Tracks source code access and escrow compliance where required. |
| Installation Event | Records installation of system/subsystem/component. |
| Commissioning Event | Records readiness for operational testing. |
| Test Event | Unit, integration, performance, user acceptance, regression, or other testing event. |
| Operational Acceptance Event | Contractual acceptance of system/subsystem. |
| Defect Record | Defect liability and warranty issue tracking. |
| Functional Guarantee Record | Measurable guarantee and compliance status. |
| Support/SLA Record | Warranty and post-warranty support events. |
| Change Order Record | Contract changes after signing. |

---

## 18. NSSF ERP calibration findings

The NSSF ERP tender validates the need for the above model.

### 18.1 Useful calibration points

| NSSF item | Engine implication |
|---|---|
| Two-phase implementation | Acceptance certificates must support phase-specific acceptance. |
| Payment milestones tied to Phase 1 and Phase 2 | Payment schema must link to milestones and acceptance certificates. |
| 12-month warranty per phase | Warranty start/end must be phase-specific, not always global contract-level. |
| UAT and formal acceptance certificate required for each phase | Testing and acceptance must be structured execution objects. |
| Microsoft Dynamics 365 Business Central / Azure | Software category, license, IPR, escrow, and proprietary-source-code carveout must be modeled. |
| Customization source code/configuration transfer or escrow | SCC IPR strategy must support source-code/customization treatment. |
| SLA with P1/P2/P3 response and resolution times | Support obligations must become contract execution objects. |
| Subcontracting requires prior approval | Approved Subcontractors Appendix must be linked to approval workflow. |
| Performance Security 10% valid through warranty + 60 days | Security validity rule must support post-acceptance validity. |

### 18.2 NSSF caution flags

| Caution | Reason |
|---|---|
| The NSSF tender uses a simplified GCC/SCC structure compared to the official IT STD. | The engine must generate from official STD structure, not from simplified tender drafting. |
| It includes strong product/vendor-specific requirements. | Vendor-specific requirements may be justified in a tender instance, but should not become the generic STD model. |
| It uses phased payment and acceptance. | This is a good fixture for testing, but the engine must also support single-stage acceptance. |
| It includes IP escrow customization. | IPR model must support legal-review-dependent alternatives. |

---

## 19. Contract render-block model

The contract render layer should use deterministic render blocks.

| Render block key | Output |
|---|---|
| `render.contract.gcc` | Locked GCC clauses. |
| `render.contract.scc` | SCC table with configured values. |
| `render.contract.notification_intention_to_award` | Notification of Intention to Award. |
| `render.contract.letter_of_award` | Letter of Award. |
| `render.contract.contract_agreement` | Contract Agreement. |
| `render.contract.appendix_1_supplier_representative` | Appendix 1. |
| `render.contract.appendix_2_adjudicator` | Appendix 2. |
| `render.contract.appendix_3_approved_subcontractors` | Appendix 3. |
| `render.contract.appendix_4_software_categories` | Appendix 4. |
| `render.contract.appendix_5_custom_materials` | Appendix 5. |
| `render.contract.appendix_6_revised_price_schedules` | Appendix 6. |
| `render.contract.appendix_7_finalization_minutes` | Appendix 7. |
| `render.contract.performance_security` | Performance Security form. |
| `render.contract.advance_payment_security` | Advance Payment Security form. |
| `render.contract.installation_certificate` | Installation Certificate. |
| `render.contract.operational_acceptance_certificate` | Operational Acceptance Certificate. |
| `render.contract.change_order_forms` | Change Order procedures and forms. |
| `render.contract.beneficial_ownership_disclosure` | Beneficial Ownership Disclosure Form. |

### 19.1 Render rules

| Rule | Requirement |
|---|---|
| GCC must render from locked clause text | No tender-instance edits. |
| SCC must render from approved parameters | No raw legal text insertion unless parameter permits. |
| Contract Agreement must render from carry-forward records | No manual retyping of accepted values. |
| Appendices must render from structured data | Empty appendices must render as `Not Applicable` where appropriate. |
| Securities must render only when required | Advance Payment Security is conditional. |
| Acceptance certificates and change forms must be available during contract execution | They are not only tender publication artifacts. |
| Rendered signed contract bundle must be hashed and immutable | Later modifications require amendment/change workflow. |

---

## 20. Seed package updates required by Pass 5

The current seed package skeleton already includes starter contract files. Pass 5 requires strengthening them.

### 20.1 Contract files to update

| File | Required update |
|---|---|
| `contract/contract_schema.json` | Add Contract Agreement generation inputs, document precedence, effective-date conditions, carry-forward mappings. |
| `contract/contract_forms.json` | Add complete contract form catalogue, including Request for Review and Beneficial Ownership Disclosure if retained in this package area. |
| `contract/contract_appendices.json` | Add full appendix field schemas and required/conditional logic. |
| `contract/acceptance_certificate_schema.json` | Split into Installation Certificate and Operational Acceptance Certificate schemas. |
| `contract/change_order_schema.json` | Expand into full change workflow forms and states. |
| `configuration/scc_schema.json` | Add SCC contract parameters linked to GCC clauses. |
| `rules/rule_catalog.json` | Add contract, security, acceptance, change, IP, escrow, and carry-forward rules. |
| `rendering/render_blocks.json` | Add contract render blocks. |
| `workflow/lifecycle_bindings.json` | Add contract generation and contract execution states. |
| `workflow/approval_bindings.json` | Add legal/procurement/technical approvals for contract finalization and change orders. |
| `tests/validation_smoke_tests.json` | Add contract validation smoke tests. |
| `tests/rendering_smoke_tests.json` | Add contract render smoke tests. |

### 20.2 New files recommended

| File | Purpose |
|---|---|
| `contract/gcc_clause_register.json` | Locked GCC clause records with source hashes. |
| `contract/scc_parameter_bindings.json` | SCC parameter-to-GCC bindings. |
| `contract/contract_carry_forward_map.json` | Source-to-target contract generation mappings. |
| `contract/security_instrument_schema.json` | Performance and Advance Payment Security schemas. |
| `contract/software_classification_schema.json` | Appendix 4 software classification schema. |
| `contract/custom_materials_schema.json` | Appendix 5 schema. |
| `contract/beneficial_ownership_schema.json` | BO disclosure schema. |
| `contract/contract_execution_events.json` | Installation, commissioning, acceptance, warranty, support, change events. |
| `contract/contract_state_model.json` | Contract lifecycle states and transitions. |

---

## 21. Smoke contracts for Pass 5

### 21.1 Contract generation smoke tests

| Test key | Scenario | Expected result |
|---|---|---|
| `SMOKE.CONTRACT.001` | Generate contract bundle from successful tender with all required data. | Contract Agreement, SCC, appendices, securities, and contract forms render. |
| `SMOKE.CONTRACT.002` | Attempt contract generation with missing SCC commencement period. | Blocking validation error. |
| `SMOKE.CONTRACT.003` | Attempt contract generation without accepted price schedule. | Blocking validation error. |
| `SMOKE.CONTRACT.004` | Generate contract with no adjudicator. | Appendix 2 renders `Not Applicable` if SCC allows. |
| `SMOKE.CONTRACT.005` | Generate contract with approved subcontractors. | Appendix 3 renders subcontractor table and approval references. |

### 21.2 Security smoke tests

| Test key | Scenario | Expected result |
|---|---|---|
| `SMOKE.SECURITY.001` | Performance Security required and present. | Contract can proceed to effective-date check. |
| `SMOKE.SECURITY.002` | Performance Security missing. | Contract effective transition blocked. |
| `SMOKE.SECURITY.003` | Advance payment enabled but Advance Payment Security missing. | Advance payment release blocked. |
| `SMOKE.SECURITY.004` | Performance Security validity shorter than SCC requirement. | Blocking validation error. |

### 21.3 Acceptance smoke tests

| Test key | Scenario | Expected result |
|---|---|---|
| `SMOKE.ACCEPTANCE.001` | Issue Installation Certificate for Phase 1. | Certificate generated, linked to phase and installation event. |
| `SMOKE.ACCEPTANCE.002` | Attempt Operational Acceptance without test results. | Blocking validation error. |
| `SMOKE.ACCEPTANCE.003` | Issue Operational Acceptance with unresolved critical defect. | Blocked unless authorized exception policy permits; otherwise fails. |
| `SMOKE.ACCEPTANCE.004` | Issue Phase 2 acceptance in phased contract. | Warranty starts for Phase 2 only. |

### 21.4 Change order smoke tests

| Test key | Scenario | Expected result |
|---|---|---|
| `SMOKE.CHANGE.001` | PE requests change proposal. | RFC generated and awaiting supplier estimate. |
| `SMOKE.CHANGE.002` | Supplier submits estimate; PE accepts estimate. | Change proposal preparation authorized. |
| `SMOKE.CHANGE.003` | Supplier submits change proposal with price and schedule impact. | Budget, technical, and legal review tasks generated as applicable. |
| `SMOKE.CHANGE.004` | Attempt to implement change before approval. | Blocked. |
| `SMOKE.CHANGE.005` | Approved change order modifies price schedule and implementation deadline. | Contract price, schedule, and audit chain update through change order only. |

### 21.5 Carry-forward smoke tests

| Test key | Scenario | Expected result |
|---|---|---|
| `SMOKE.CARRYFORWARD.001` | Accepted supplier price schedule carried into Contract Agreement. | Contract price equals accepted/corrected price schedule. |
| `SMOKE.CARRYFORWARD.002` | Accepted implementation schedule carried into contract. | Milestones and acceptance points match accepted tender. |
| `SMOKE.CARRYFORWARD.003` | Software categories missing for software procurement. | Contract finalization blocked. |
| `SMOKE.CARRYFORWARD.004` | Custom software exists but IPR strategy absent. | Contract finalization blocked pending legal review. |
| `SMOKE.CARRYFORWARD.005` | Finalization amendment attempts to modify locked GCC text. | Blocked; requires new STD version, not finalization edit. |

---

## 22. Approval and permission gates

### 22.1 Contract finalization permissions

| Action | Required role(s) |
|---|---|
| Generate draft contract bundle | Procurement Officer / Contract Preparation Officer. |
| Confirm carry-forward values | Procurement Officer and Contract Manager. |
| Review SCC legal-sensitive fields | Legal Reviewer. |
| Review technical carry-forward | Technical/ICT Reviewer. |
| Approve contract for signature | Authorized Procurement Approver / Accounting Officer or delegated authority. |
| Sign contract | Authorized signatories only. |
| Mark contract effective | Contract Manager after effective-date conditions are satisfied. |

### 22.2 Contract execution permissions

| Action | Required role(s) |
|---|---|
| Record installation event | Project Manager / Contract Manager. |
| Issue Installation Certificate | Authorized Project Manager / PE official. |
| Record test results | Technical/ICT Reviewer / Project Team. |
| Issue Operational Acceptance Certificate | Authorized PE official after review. |
| Raise change request | Contract Manager / Project Manager / authorized PE official. |
| Submit supplier change estimate/proposal | Supplier Representative. |
| Approve change estimate | Contract Manager / authorized PE official. |
| Approve change order | Procurement, finance/budget, technical, legal, and approving authority according to threshold. |
| Record warranty/support incident | Contract Manager / Supplier Representative / support desk. |

---

## 23. Audit and evidence requirements

The contract area must be audit-grade.

| Object | Required evidence |
|---|---|
| Contract bundle | Rendered artifact, hash, STD version, source mappings, approval history. |
| SCC value | Input source, user, timestamp, validation result, review state. |
| Carry-forward value | Source object, source hash, transformation rule, target field, confirmation. |
| Security instrument | Uploaded/issued form, verification record, validity dates, expiry alerts. |
| Acceptance certificate | Test evidence, sign-off, exception list, issued artifact hash. |
| Change order | Request, estimate, estimate acceptance, proposal, review decisions, approved order, revised price/schedule links. |
| Beneficial ownership disclosure | Submitted form, restricted access audit, verification result. |

---

## 24. Activation blockers remaining after Pass 5

This pass is still not sufficient to activate the IT STD package.

The following work remains:

1. Full extraction of exact GCC clause text and paragraph-level source anchors.
2. Full extraction of exact SCC table entries and guidance notes.
3. Full extraction of contract form templates.
4. Full extraction of installation and operational acceptance certificate wording.
5. Full extraction of complete change order procedure wording and form text.
6. Beneficial Ownership Disclosure schema verification against the exact official form.
7. Render-template implementation for all contract artifacts.
8. Import package update with Pass 5 schema records.
9. Legal review of SCC IPR options, escrow, liability, securities, dispute resolution, and change control.
10. Technical review of software classification, acceptance, warranty, SLA, and support execution objects.
11. Smoke test implementation and passing evidence.
12. Package checksum regeneration.
13. End-to-end dry run using the NSSF ERP tender as a calibration fixture.

---

## 25. Recommended implementation order for the contract area

1. Build locked GCC clause register with source anchors and hashes.
2. Build SCC parameter bindings by GCC clause.
3. Build contract carry-forward map.
4. Build Contract Agreement generator.
5. Build appendices generator.
6. Build security instrument schemas and verification workflow.
7. Build installation and operational acceptance certificate schemas.
8. Build change order workflow and forms.
9. Build beneficial ownership disclosure schema.
10. Build contract lifecycle and approval workflow.
11. Build audit/hashing for contract artifacts.
12. Add contract rendering blocks.
13. Add smoke tests.
14. Run NSSF ERP fixture through the contract generation pipeline.
15. Submit for legal/procurement review.

---

## 26. Next extraction / implementation artifact

The next artifact should be:

**IT STD Package Reconciliation and Import-Ready Update Plan**

That artifact should reconcile Passes 1 through 5 and produce a precise update plan for the seed package:

1. Which existing skeleton JSON files must be replaced.
2. Which new JSON files must be added.
3. Which records are still placeholders.
4. Which source anchors are missing.
5. Which render templates are missing.
6. Which smoke contracts are mandatory before activation.
7. Which NSSF ERP fixture records should be loaded for testing.
8. Which legal/procurement review gates remain.

After that, the implementation work should move from extraction documents into the actual seed package update.

---

## 27. Final position

The IT STD contract area confirms the engine architecture chosen earlier.

The STD Engine must not stop at tender-document generation. For IT procurement, the same structured STD data must drive:

1. Tender publication.
2. Supplier response.
3. Evaluation.
4. Award notification.
5. Contract Agreement generation.
6. Contract appendices.
7. Securities.
8. Implementation schedule management.
9. Installation and operational acceptance.
10. Warranty and support.
11. Change control.
12. Contract amendments.
13. Audit and dispute evidence.

The correct design is therefore:

**STD Engine → Tender Configuration → Supplier Response → Evaluation → Award → Contract Carry-Forward → Contract Execution.**

Anything less would recreate the legacy failure mode where the tender document and the signed contract slowly diverge from the structured procurement record.
