# STD Engine Core Module - Pre-PRD

**Project:** KenTender e-Procurement System  
**Module:** Standard Tender Document Engine Core  
**Document type:** Pre-Product Requirements Document  
**Document status:** Draft for review  
**Primary implementation target:** Generalized STD Engine supporting multiple Standard Tender Documents  
**First full STD to be digitized:** Standard Tender Document for Procurement of Information Technology  
**Calibration fixture:** NSSF SPS ERP System Tender, Tender No. NSSFSPS/ICT/ERP/001/2025-2026  

---

## 1. Executive Summary

The Standard Tender Document Engine, referred to in this document as the STD Engine, shall be the controlled legal, procedural, and structural source of truth for generating tender documents, bidder submission structures, evaluation matrices, contract formation outputs, and addendum-controlled changes in the KenTender e-Procurement system.

The earlier WORKS proof of concept successfully demonstrated that a Standard Tender Document can be digitized as a structured, configurable, auditable template instead of being treated as an uploaded Word or PDF attachment. The next phase must convert that proof of concept into a generalized production module capable of supporting multiple PPRA Standard Tender Documents, including Works, Information Technology, Goods, Non-Consulting Services, Consulting Services, Framework Agreements, and future categories.

The STD Engine must not be designed around one document type only. The Standard Tender Document for Procurement of Information Technology should be used as the first full implementation because it is sufficiently complex to validate the generalized engine while being simpler than the Works STD in certain areas. It does not require a Bills of Quantities module, engineering drawings, or measurement-and-valuation workflows, but it does require structured functional and technical requirements, implementation schedules, system inventory tables, recurrent costs, price schedules, software licensing, intellectual property, operational acceptance, support obligations, and change-order governance.

The core principle is:

> The STD Engine owns the official STD structure, legal text, allowed configuration surfaces, validation rules, rendered tender outputs, bidder response schemas, evaluation structures, and contract formation schemas. Tender Management consumes STD Engine outputs; it does not recreate, override, or manually edit them.

This Pre-PRD defines the business problem, product direction, users, generalized scope, high-level requirements, governance model, storage approach, workflows, integrations, risks, and next artifacts required before implementation.

---

## 2. Background and Rationale

Public procurement tender documents are legal instruments, not ordinary documents. The current legacy pattern of preparing tenders by copying, editing, uploading, and circulating Word/PDF documents creates operational and legal risks:

1. Locked legal provisions may be changed unintentionally.
2. Tender Data Sheet and Special Conditions of Contract fields may be incomplete or inconsistent.
3. Evaluation criteria may drift from the published tender document.
4. Bidder forms may not match submission requirements.
5. Addenda may not be linked cleanly to affected sections, rules, forms, and evaluation criteria.
6. Published tender documents may not be reproducible from structured source data.
7. Contract formation outputs may not carry forward the tender and award data reliably.
8. Audit teams may not be able to prove which official STD version was used.

The WORKS PoC confirmed that digitization can solve these problems if the STD is modeled as structured data with controlled mutability, source traceability, validation rules, renderable sections, native domain modules, and governance.

The next step is not to create an IT tender wizard directly. The next step is to create the STD Engine Core Module so that any STD family can be represented, approved, versioned, rendered, validated, and consumed consistently.

---

## 3. Source Inputs and Evidence Basis

This Pre-PRD is based on the following inputs:

1. The earlier WORKS STD proof-of-concept JSON package: `KE-PPRA-WORKS-BLDG-2022-04-POC.json5`.
2. The official PPRA Standard Tender Document for Procurement of Works, Building and Associated Civil Engineering Works, April 2022 revision.
3. The official PPRA Standard Tender Document for Procurement of Information Technology, Doc. 10.
4. The NSSF SPS ERP System Tender, Tender No. `NSSFSPS/ICT/ERP/001/2025-2026`.

The Information Technology STD confirms that an IT tender document is organized into tendering procedures, Tender Data Sheet, evaluation and qualification criteria, tendering forms, procuring entity requirements, technical requirements, implementation schedule, system inventory tables, background materials, General Conditions of Contract, Special Conditions of Contract, and contract forms.

The NSSF ERP tender confirms that a real IT tender may contain tender identity values, Tender Data Sheet values, mandatory compliance requirements, technical scoring criteria, detailed module requirements, technical compliance matrices, project management requirements, testing and acceptance requirements, implementation schedule constraints, warranty and support requirements, intellectual property provisions, and contract forms.

The NSSF tender is useful as a calibration fixture. It must not be treated as the legal master template. The official STD remains the master source.

---

## 4. Problem Statement

KenTender needs a reusable STD Engine that allows authorized users to digitize, govern, configure, validate, render, publish, and audit Standard Tender Documents across multiple procurement categories.

Without this engine, the platform will either:

1. Continue relying on uncontrolled document uploads; or
2. Hard-code tender forms and rules into module-specific screens; or
3. Build isolated STD-specific implementations that cannot scale across procurement categories.

All three outcomes would be unacceptable for a government-facing e-Procurement system.

The product problem is therefore:

> How can KenTender represent each official Standard Tender Document as a controlled, versioned, legally traceable, configurable template that can generate tender documents, bidder submission schemas, evaluation schemas, contract outputs, and addendum impacts without allowing unauthorized alteration of protected legal content?

---

## 5. Product Vision

The STD Engine shall provide a controlled authoring and execution layer for official Standard Tender Documents.

It shall allow central administrators to import and structure official STDs, define allowed configuration surfaces, map forms and rules, approve template versions, activate official versions, and preserve immutable source-traced records.

It shall allow procurement users to configure a tender using an approved active STD version through guided screens, without directly editing locked legal sections.

It shall allow bidders to submit responses through structured forms derived from the published STD configuration.

It shall allow evaluation teams to evaluate tenders using structured checklists, conformance matrices, technical scoring models, financial comparison models, and qualification requirements generated from the same STD version used to publish the tender.

It shall allow contract formation to consume structured tender, award, bidder, price, schedule, and contract parameter data to generate contract forms and appendices.

It shall allow all post-publication changes to pass through addendum governance with impact analysis.

---

## 6. Product Goals

### 6.1 Business goals

1. Ensure official PPRA STDs are used consistently across procuring entities.
2. Prevent unauthorized modification of locked STD provisions.
3. Reduce preparation errors in tender documents.
4. Ensure published tender documents, bidder response structures, evaluation matrices, and contract outputs remain aligned.
5. Improve auditability, legal defensibility, and version traceability.
6. Support digitization of multiple STD families through one generalized engine.
7. Reduce manual document handling while preserving the legal structure of official STDs.
8. Enable future automation of tender preparation, validation, publication, evaluation, award, contract formation, and addendum management.

### 6.2 Product goals

1. Provide a reusable STD meta-model.
2. Provide a governed STD template lifecycle.
3. Provide controlled tender-specific configuration.
4. Provide deterministic rendering of tender documents.
5. Provide schema-driven bidder response forms.
6. Provide STD-generated evaluation structures.
7. Provide contract output schemas.
8. Provide source traceability for every material element.
9. Provide import/export package support.
10. Provide smoke contracts and regression checks for each STD package.

### 6.3 Technical goals

1. Use normalized persistent storage for official template data.
2. Use JSON schemas only where flexible schema, rules, or render metadata are needed.
3. Preserve immutable hashes of official sources, clauses, rendered outputs, and published bundles.
4. Support version-safe evolution of templates.
5. Support domain-specific extensions without breaking the core model.
6. Provide APIs for Tender Management, Supplier Portal, Evaluation, Contract Management, Audit, and Addendum workflows.

---

## 7. Non-Goals

The first release of the STD Engine Core Module shall not attempt to do the following:

1. Replace Tender Management entirely.
2. Replace Supplier Registration.
3. Replace the Evaluation Committee module.
4. Replace Contract Management.
5. Provide full natural-language authoring of official legal clauses.
6. Automatically infer legal rules from uploaded documents without human review.
7. Allow procuring entities to modify locked ITT or GCC text.
8. Build a full IT tender configuration wizard before the core STD meta-model is approved.
9. Treat each tender document as an isolated uploaded document.
10. Treat the NSSF ERP tender as the official master source.

---

## 8. User Classes

### 8.1 Central STD Administrator

Responsible for managing STD families, source documents, extracted sections, clauses, template versions, import/export packages, render blocks, and activation status.

### 8.2 Legal or Procurement Template Reviewer

Responsible for reviewing structured extraction, mutability classification, rule mapping, clause protection, and consistency with the official STD.

### 8.3 PPRA or Authorized Template Approver

Responsible for approving template versions for activation.

### 8.4 Procuring Entity Procurement Officer

Responsible for configuring a tender using an active STD version through controlled fields, requirements, schedules, forms, and contract parameters.

### 8.5 Procuring Entity Reviewer or Approver

Responsible for reviewing configured tender documents before publication.

### 8.6 Bidder or Supplier

Responsible for submitting structured responses, forms, evidence, technical conformance responses, price schedules, and declarations generated from the published STD configuration.

### 8.7 Evaluation Committee Member

Responsible for evaluating tenders using evaluation structures derived from the published STD configuration.

### 8.8 Contract Officer

Responsible for generating contract forms, appendices, securities, acceptance certificates, and change-order records after award.

### 8.9 Auditor or Oversight Officer

Responsible for reviewing source traceability, template versions, publication bundles, addenda, evaluation alignment, approval history, and audit logs.

### 8.10 System Administrator

Responsible for technical configuration, permissions, background jobs, indexing, rendering services, and platform integration health.

---

## 9. Core Concepts

### 9.1 STD Template Family

A template family represents a class of Standard Tender Document. Examples include:

1. Works - Building and Associated Civil Engineering Works.
2. Procurement of Information Technology.
3. Goods.
4. Non-Consulting Services.
5. Consulting Services.
6. Framework Agreements.
7. Small Works.
8. Design and Build.

Each family may have multiple versions.

### 9.2 STD Template Version

A template version represents one approved edition of a Standard Tender Document. It has a source document, version metadata, lifecycle state, structured sections, clauses, parameters, rules, forms, schemas, render blocks, and hashes.

Once active, a version is immutable.

### 9.3 Source Document

A source document is the official uploaded source used for extraction. It must be stored with metadata and a file hash. All extracted sections, clauses, fields, rules, and render blocks must trace back to the source.

### 9.4 Section

A section is a structural unit of the STD, such as ITT, TDS, Evaluation Criteria, Tendering Forms, Technical Requirements, GCC, SCC, or Contract Forms.

### 9.5 Clause

A clause is a legal or procedural textual provision. It may be locked, parameterized, conditionally included, or generated.

### 9.6 Parameter

A parameter is a controlled field that may be supplied at tender configuration time. Examples include tender name, tender number, deadline, validity period, tender security amount, JV limit, currency, pre-tender meeting status, performance security percentage, payment milestones, warranty period, and dispute resolution values.

### 9.7 Rule

A rule is a validation, activation, calculation, consistency, eligibility, scoring, rendering, or workflow rule. Rules must be declarative, testable, scoped, and auditable.

### 9.8 Form Schema

A form schema defines a structured form used by the Procuring Entity, bidder, evaluator, or contract officer. It includes fields, field types, validation rules, evidence requirements, respondent roles, lifecycle stage, and downstream usage.

### 9.9 Requirement Schema

A requirement schema defines how procuring entity requirements are structured. Different STDs will require different requirement schemas.

Examples:

1. Works: specifications, drawings, BoQ, site data.
2. IT: functional requirements, architectural requirements, performance requirements, service specifications, technology specifications, implementation schedule, system inventory tables.
3. Goods: schedule of requirements, delivery schedule, technical specifications.
4. Services: scope of services, service levels, deliverables.

### 9.10 Render Block

A render block defines how a section, clause, table, form, requirement, or contract output is assembled into a human-readable document.

### 9.11 Tender STD Instance

A Tender STD Instance is the tender-specific binding between one tender and one active STD template version. It stores configuration values and generated outputs separately from the master template.

### 9.12 Addendum Impact

An Addendum Impact record identifies which published fields, clauses, forms, requirements, schedules, evaluation criteria, price schedules, or contract outputs are affected by a post-publication change.

---

## 10. Universal Mutability Model

Every STD section, clause, field, form, and render block must be assigned a mutability classification.

| Mutability Type | Meaning | Example |
|---|---|---|
| `LOCKED_TEXT` | Text cannot be edited by procuring entity users. | ITT, GCC core clauses. |
| `PARAMETERIZED_TEXT` | Text contains controlled placeholders populated from parameters. | Invitation to Tender, TDS-linked clauses. |
| `CONTROLLED_CONFIG` | Users select or enter values only through allowed fields. | TDS, SCC, tender security, currency, JV limit. |
| `CONTROLLED_REQUIREMENTS` | Users author requirements through a structured schema. | IT functional and technical requirements. |
| `STRUCTURED_TABLE` | Users populate controlled tabular structures. | Price schedules, implementation schedule, inventory tables. |
| `BIDDER_RESPONSE_SCHEMA` | Defines fields and evidence to be completed by bidders. | Forms, declarations, conformance matrix. |
| `EVALUATION_SCHEMA` | Defines evaluation checklist, scoring, qualification, and financial comparison structures. | Preliminary and technical evaluation criteria. |
| `CONTRACT_OUTPUT_SCHEMA` | Defines post-award contract forms and appendices. | Contract Agreement, software categories, accepted subcontractors. |
| `GENERATED_OUTPUT` | System-generated content that users do not edit directly. | Published tender bundle, audit summary, addendum summary. |
| `REFERENCE_ONLY` | Informational material, not a bidder obligation unless explicitly linked. | Background information. |

Rules:

1. `LOCKED_TEXT` must never be edited in a tender instance.
2. `PARAMETERIZED_TEXT` must render only from approved parameters.
3. `CONTROLLED_CONFIG` must be validated before publication.
4. `CONTROLLED_REQUIREMENTS` must maintain requirement IDs, compliance status, bidder response fields, and evaluation linkage.
5. `STRUCTURED_TABLE` must support import/export but must preserve schema validation.
6. `BIDDER_RESPONSE_SCHEMA` must be generated from the published tender configuration.
7. `EVALUATION_SCHEMA` must not drift from the published tender configuration.
8. `CONTRACT_OUTPUT_SCHEMA` must consume award and tender data; it must not ask users to re-enter data already captured.
9. `GENERATED_OUTPUT` must be immutable after publication.
10. `REFERENCE_ONLY` must be clearly separated from binding requirements.

---

## 11. Generalized STD Template Lifecycle

### 11.1 States

```text
Draft
 -> Structuring
 -> Internal Review
 -> Legal/Procurement Review
 -> Approved
 -> Active
 -> Superseded
 -> Archived
```

### 11.2 State definitions

| State | Meaning |
|---|---|
| `Draft` | Template version has been created but is not yet fully structured. |
| `Structuring` | Sections, clauses, parameters, rules, forms, and render blocks are being mapped. |
| `Internal Review` | Product and implementation team reviews structural correctness. |
| `Legal/Procurement Review` | Authorized legal/procurement reviewers validate fidelity to the official STD. |
| `Approved` | Template is approved but not yet available for new tenders. |
| `Active` | Template can be selected for new tenders. |
| `Superseded` | Template is replaced by a newer active version but remains available for existing tenders and audit. |
| `Archived` | Template is no longer selectable and is retained only for audit/history. |

### 11.3 Transition rules

| From | To | Required checks |
|---|---|---|
| Draft | Structuring | Source document attached; source hash captured. |
| Structuring | Internal Review | Section map complete; no missing mandatory sections. |
| Internal Review | Legal/Procurement Review | Internal review complete; extraction warnings resolved or justified. |
| Legal/Procurement Review | Approved | Legal/procurement approval recorded; locked text and mutability reviewed. |
| Approved | Active | Smoke tests passed; render checks passed; approval chain complete. |
| Active | Superseded | Replacement version activated or administrative supersession approved. |
| Superseded | Archived | No active tender preparation depends on the version. |

### 11.4 Hard blockers

1. A template without a source document hash cannot be approved.
2. A template with unmapped mandatory sections cannot be activated.
3. A template with editable locked text cannot be activated.
4. A template without render blocks for mandatory output sections cannot be activated.
5. A template without smoke tests cannot be activated.
6. A template used by a tender cannot be deleted.
7. An active template cannot be modified in place.
8. A change to official clause text requires a new version.
9. A change to form schema, rule behavior, evaluation schema, or render behavior requires a new version.
10. Supersession must preserve audit access to the superseded version.

---

## 12. Tender STD Instance Lifecycle

### 12.1 States

```text
Not Started
 -> In Configuration
 -> Validation Failed
 -> Ready for Review
 -> Procurement Review
 -> Approved for Tender Creation
 -> Bound to Tender
 -> Published
 -> Addendum Required
 -> Superseded by Addendum
```

### 12.2 State definitions

| State | Meaning |
|---|---|
| `Not Started` | Tender has selected or will select an STD template version. |
| `In Configuration` | Procuring Entity is completing allowed configuration fields and requirements. |
| `Validation Failed` | Required fields, dates, rules, forms, or schedules fail validation. |
| `Ready for Review` | Configuration passes validation and is ready for review. |
| `Procurement Review` | Internal PE review of configured tender package. |
| `Approved for Tender Creation` | Tender package is approved for generation. |
| `Bound to Tender` | STD configuration is formally bound to the tender record. |
| `Published` | Tender document bundle has been rendered, hashed, and published. |
| `Addendum Required` | A post-publication change has been requested or approved. |
| `Superseded by Addendum` | The published bundle has been superseded by a later addendum-controlled bundle. |

### 12.3 Hard blockers

1. A tender cannot bind to a non-active STD version.
2. A tender cannot publish with missing mandatory parameters.
3. A tender cannot publish with failed blocking validation rules.
4. A tender cannot publish if the generated bundle hash is missing.
5. A published tender bundle cannot be edited in place.
6. Post-publication changes must use addendum governance.
7. Evaluation schemas must be locked to the published tender version.
8. Bidder response schemas must be locked to the published tender version.
9. Contract output schemas must reference the tender version and addenda history.
10. A tender cannot be evaluated using criteria not present in the published tender or approved addendum.

---

## 13. Functional Scope

### 13.1 Included in STD Engine Core

The core module shall include:

1. STD family registry.
2. STD source document registry.
3. STD template version lifecycle.
4. Section hierarchy model.
5. Clause model.
6. Universal mutability model.
7. Parameter model.
8. Rule model.
9. Form schema model.
10. Evidence requirement model.
11. Requirement schema model.
12. Price schedule schema model.
13. Evaluation schema model.
14. Contract output schema model.
15. Render block model.
16. Source traceability model.
17. Approval workflow model.
18. Template activation and supersession.
19. Tender STD instance binding.
20. Tender configuration values.
21. Validation findings.
22. Generated bundle registry.
23. Addendum impact model.
24. Import/export package support.
25. Smoke contract framework.
26. Audit event logging.

### 13.2 Excluded from STD Engine Core but dependent on it

The following modules will consume STD Engine outputs but are not part of the core module:

1. Tender Management full workflow.
2. Supplier Portal tender submission UI.
3. Evaluation Committee scoring workspace.
4. Contract Management execution workspace.
5. Procurement Planning.
6. Supplier Registration and compliance management.
7. Payment and contract administration modules.
8. External PPRA publication portal integration.

### 13.3 Domain-specific extensions

The core engine must allow domain extensions, including:

| STD family | Domain extension examples |
|---|---|
| Works | Bills of Quantities, drawings, site visit, NCA category, measurement and valuation. |
| IT | Functional requirements, technology requirements, system inventory, implementation schedule, recurrent costs, software categories, operational acceptance. |
| Goods | Delivery schedule, item specifications, warranty, country of origin, inspection. |
| Services | Scope of services, service levels, personnel, deliverables, performance standards. |
| Consulting | Terms of Reference, technical/financial proposals, consultant evaluation, key experts. |

The core engine must not hard-code any one STD family.

---

## 14. High-Level Functional Requirements

### 14.1 STD family management

The system shall allow authorized users to create and manage STD families.

Minimum fields:

| Field | Description |
|---|---|
| `family_code` | Stable code, such as `KE-PPRA-IT`. |
| `family_name` | Human-readable name. |
| `procurement_category` | Works, IT, Goods, Services, Consulting, etc. |
| `authority` | Source authority, such as PPRA. |
| `default_version_id` | Active default version. |
| `status` | Active, inactive, archived. |

### 14.2 Source document registry

The system shall store the official source document and metadata.

Minimum fields:

| Field | Description |
|---|---|
| `source_document_id` | Unique identifier. |
| `file_name` | Uploaded source file name. |
| `file_type` | PDF, DOC, DOCX, JSON, etc. |
| `source_authority` | Issuing authority. |
| `issue_date` | Official issue date where known. |
| `revision_date` | Revision date where known. |
| `file_hash` | Hash of uploaded file. |
| `page_count` | Page count where applicable. |
| `extraction_status` | Not started, in progress, completed, reviewed. |

### 14.3 Template version management

The system shall support versioned STD templates.

Minimum fields:

| Field | Description |
|---|---|
| `template_version_id` | Unique version identifier. |
| `family_id` | Parent family. |
| `version_code` | Stable version code. |
| `version_label` | Human-readable label. |
| `source_document_id` | Linked official source. |
| `status` | Lifecycle status. |
| `effective_date` | Effective date. |
| `supersedes_version_id` | Previous version, if any. |
| `template_hash` | Hash of normalized structured package. |
| `activation_date` | Date activated. |
| `activated_by` | User who activated. |

### 14.4 Section and clause management

The system shall allow structured storage of sections and clauses.

Minimum section fields:

| Field | Description |
|---|---|
| `section_id` | Unique section identifier. |
| `template_version_id` | Parent template version. |
| `parent_section_id` | Parent section, if nested. |
| `section_ref` | Official reference. |
| `section_title` | Section title. |
| `part_ref` | Part reference. |
| `sort_order` | Render order. |
| `mutability_type` | Universal mutability classification. |
| `render_required` | Whether this section must render. |

Minimum clause fields:

| Field | Description |
|---|---|
| `clause_id` | Unique clause identifier. |
| `section_id` | Parent section. |
| `clause_ref` | Official clause reference. |
| `clause_text` | Normalized clause text or clause template. |
| `mutability_type` | Mutability classification. |
| `parameter_bindings` | Controlled placeholders, if any. |
| `source_text_hash` | Source hash. |
| `normalized_text_hash` | Normalized clause hash. |

### 14.5 Parameter management

The system shall define all allowed tender-specific configuration fields.

Minimum fields:

| Field | Description |
|---|---|
| `parameter_id` | Unique parameter identifier. |
| `template_version_id` | Parent template version. |
| `parameter_code` | Stable code. |
| `label` | User-facing label. |
| `data_type` | String, number, date, datetime, amount, percentage, select, boolean, table, object. |
| `required` | Whether mandatory. |
| `default_value` | Default, if any. |
| `allowed_values` | Options, if select. |
| `validation_schema` | JSON schema or expression. |
| `render_targets` | Sections/clauses/forms where value appears. |
| `lifecycle_stage` | Configuration, publication, evaluation, award, contract. |
| `legal_basis` | Source section or clause. |

### 14.6 Rule management

The system shall define declarative rules.

Rule types:

1. Required field validation.
2. Date-order validation.
3. Numeric threshold validation.
4. Conditional activation.
5. Form activation.
6. Evidence requirement activation.
7. Price calculation.
8. Evaluation score validation.
9. Bidder eligibility validation.
10. Contract output activation.
11. Addendum impact rule.
12. Render visibility rule.

Minimum fields:

| Field | Description |
|---|---|
| `rule_id` | Unique rule identifier. |
| `template_version_id` | Parent template version. |
| `rule_code` | Stable rule code. |
| `rule_type` | Type from list above. |
| `scope` | Template, tender instance, bidder response, evaluation, contract, addendum. |
| `severity` | Info, warning, blocker. |
| `expression` | Declarative condition or validation expression. |
| `message` | User-facing validation message. |
| `affected_objects` | Fields/forms/sections impacted. |
| `source_basis` | Source reference. |
| `test_cases` | Positive and negative smoke tests. |

### 14.7 Form schema management

The system shall support complete form schemas.

Form respondent types:

1. Procuring Entity.
2. Bidder.
3. Evaluation Committee.
4. Successful Tenderer.
5. Contract Officer.
6. System-generated.

Minimum form fields:

| Field | Description |
|---|---|
| `form_schema_id` | Unique form schema identifier. |
| `template_version_id` | Parent template version. |
| `form_code` | Stable code. |
| `form_title` | Form title. |
| `respondent_type` | PE, bidder, evaluator, successful bidder, contract officer, system. |
| `lifecycle_stage` | Tender configuration, submission, evaluation, award, contract. |
| `activation_rule_id` | Conditional activation rule, if any. |
| `fields_schema` | Field schema. |
| `evidence_requirements` | Required attachments. |
| `render_block_id` | Render definition. |

### 14.8 Requirement schema management

The system shall support structured procuring entity requirements.

Requirement item minimum fields:

| Field | Description |
|---|---|
| `requirement_id` | Unique requirement identifier. |
| `template_version_id` | Parent template version. |
| `tender_instance_id` | Tender-specific owner when instantiated. |
| `requirement_code` | Stable row code. |
| `requirement_category` | Functional, technical, service, performance, schedule, inventory, legal, support. |
| `description` | Requirement description. |
| `mandatory_flag` | Mandatory, desirable, optional. |
| `bidder_response_required` | Whether bidder must respond. |
| `compliance_response_type` | Yes/no, narrative, evidence, numeric, select, table. |
| `evaluation_linkage` | Evaluation criteria linked to this requirement. |
| `contract_linkage` | Contract output linkage, if awarded. |

### 14.9 Price schedule schema management

The system shall support structured price schedules across STD families.

Generic price schedule concepts:

1. Cost category.
2. Cost item.
3. Quantity.
4. Unit of measure.
5. Unit price.
6. Tax treatment.
7. Currency.
8. Recurrent versus one-time cost.
9. Warranty-period cost.
10. Post-warranty cost.
11. Summary totals.
12. Financial evaluation treatment.

The IT STD extension must support supply and installation cost tables, recurrent cost tables, system inventory linkages, and implementation schedule linkages.

### 14.10 Evaluation schema management

The system shall define evaluation structures generated from the STD.

Evaluation schema components:

1. Preliminary responsiveness checklist.
2. Mandatory requirements.
3. Eligibility checks.
4. Technical qualification checks.
5. Technical scoring criteria.
6. Requirement-by-requirement conformance review.
7. Personnel criteria.
8. Experience criteria.
9. Financial evaluation method.
10. Price comparison and adjustments.
11. Margin of preference, where enabled.
12. Abnormally low or high tender checks.
13. Award recommendation basis.

### 14.11 Contract output schema management

The system shall define contract formation outputs.

Contract output examples:

1. Notification of Intention to Award.
2. Letter of Award.
3. Contract Agreement.
4. Performance Security.
5. Advance Payment Security.
6. Beneficial Ownership Disclosure.
7. Supplier Representative appendix.
8. Approved Subcontractors appendix.
9. Software Categories appendix.
10. Custom Materials appendix.
11. Revised Price Schedules.
12. Contract Finalization Minutes.
13. Installation and Acceptance Certificates.
14. Change Order Procedures and Forms.

### 14.12 Render block management

The system shall render official outputs deterministically.

Render block requirements:

1. Stable block ID.
2. Section binding.
3. Clause binding.
4. Parameter binding.
5. Conditional visibility.
6. Table rendering rules.
7. Page/heading hierarchy.
8. Output format compatibility.
9. Hash generation.
10. Preview support.
11. Publication output support.

---

## 15. Generalized Data Storage Approach

### 15.1 Storage principle

The production system shall not store an approved STD template only as a monolithic JSON document.

The system shall use a hybrid storage approach:

1. Relational records for identity, lifecycle, section structure, references, approvals, usage, audit, and joins.
2. JSON schema fields for complex validation, form schemas, render metadata, requirement schemas, and domain-specific extensions.
3. Immutable content blobs for locked clause text, source extracts, rendered documents, and publication bundles.
4. Hashes for source documents, clause text, normalized templates, rendered outputs, and addenda.
5. Event logs for import, extraction, review, approval, activation, publication, and supersession.

### 15.2 Core persistent objects

| Object | Purpose |
|---|---|
| `STDTemplateFamily` | Identifies a family of STDs. |
| `STDTemplateVersion` | Stores a version of a family. |
| `STDSourceDocument` | Stores official source metadata and hashes. |
| `STDSection` | Stores section hierarchy and mutability. |
| `STDClause` | Stores protected or parameterized legal/procedural text. |
| `STDParameter` | Stores configurable fields. |
| `STDParameterOption` | Stores controlled options. |
| `STDRule` | Stores validation, activation, calculation, scoring, and rendering rules. |
| `STDFormSchema` | Stores form definitions. |
| `STDFormField` | Stores field-level definitions. |
| `STDEvidenceRequirement` | Stores required supporting documents. |
| `STDRequirementSchema` | Stores requirement model definition. |
| `STDRequirementItem` | Stores instantiated or reusable requirement items. |
| `STDPriceScheduleSchema` | Stores price schedule definition. |
| `STDPriceScheduleItem` | Stores item-level price schedule structure. |
| `STDEvaluationSchema` | Stores evaluation structures. |
| `STDContractOutputSchema` | Stores contract output structures. |
| `STDRenderBlock` | Stores deterministic rendering rules. |
| `STDApprovalEvent` | Stores review and approval history. |
| `STDUsage` | Records tender usage of STD versions. |
| `TenderSTDInstance` | Stores tender binding to STD version. |
| `TenderSTDConfigurationValue` | Stores PE-entered tender-specific values. |
| `TenderSTDValidationFinding` | Stores validation warnings/blockers. |
| `TenderGeneratedBundle` | Stores rendered tender bundle metadata and hashes. |
| `TenderAddendumImpact` | Stores addendum impact analysis. |

### 15.3 Source traceability fields

Every object derived from the official source should include source traceability fields where applicable.

| Field | Purpose |
|---|---|
| `source_document_id` | Link to official source document. |
| `source_page_start` | First source page. |
| `source_page_end` | Last source page. |
| `source_section_ref` | Official section reference. |
| `source_clause_ref` | Official clause reference. |
| `source_anchor` | Heading path, paragraph marker, table marker, or extracted anchor. |
| `source_text_hash` | Hash of extracted source text. |
| `normalized_text_hash` | Hash of cleaned normalized text. |
| `extraction_confidence` | Manual or automated extraction confidence. |
| `review_status` | Pending, reviewed, approved, exception accepted. |

---

## 16. Governance and Approval Requirements

Governance is not optional. It must be part of the core module.

### 16.1 Template governance

The system shall require formal review and approval before activation of any STD template version.

Required approval roles:

1. Structuring reviewer.
2. Procurement/legal reviewer.
3. Template approver.
4. Activation authority.

### 16.2 Tender configuration governance

The system shall require tender configuration review before publication.

Required checks:

1. Active STD version selected.
2. Mandatory fields completed.
3. Locked sections unchanged.
4. Requirements completed where required.
5. Price schedules configured where required.
6. Evaluation schema generated.
7. Contract outputs mapped.
8. Render preview generated.
9. Blocking validations resolved.
10. Publication bundle hash generated.

### 16.3 Addendum governance

After publication, changes shall not edit the original bundle. They shall generate an addendum-controlled updated bundle or addendum notice.

Addendum impact analysis shall identify:

1. Affected sections.
2. Affected clauses.
3. Affected parameters.
4. Affected requirements.
5. Affected forms.
6. Affected bidder response fields.
7. Affected evaluation criteria.
8. Affected price schedules.
9. Affected contract outputs.
10. Whether tender deadline extension should be considered.

### 16.4 Audit governance

The system shall preserve:

1. Source document hash.
2. Template package hash.
3. Clause hashes.
4. Rendered output hash.
5. Tender publication hash.
6. Addendum hash.
7. Approval trail.
8. User action logs.
9. Rule execution results.
10. Validation findings.

---

## 17. Permissions Matrix - High Level

| Capability | Central STD Admin | Template Reviewer | Template Approver | PE Procurement Officer | PE Reviewer | Bidder | Evaluator | Contract Officer | Auditor |
|---|---|---|---|---|---|---|---|---|---|
| Create STD family | Yes | No | No | No | No | No | No | No | View |
| Upload source document | Yes | No | No | No | No | No | No | No | View |
| Structure sections/clauses | Yes | Comment | No | No | No | No | No | No | View |
| Define parameters/rules/forms | Yes | Comment | No | No | No | No | No | No | View |
| Review template | View | Yes | View | No | No | No | No | No | View |
| Approve template | No | No | Yes | No | No | No | No | No | View |
| Activate template | Yes, if authorized | No | Approval required | No | No | No | No | No | View |
| Configure tender STD instance | No | No | No | Yes | Comment/approve | No | No | No | View |
| Edit locked text | No | No | No | No | No | No | No | No | No |
| Publish tender bundle | No | No | No | Submit | Approve | No | No | No | View |
| Submit bidder forms | No | No | No | No | No | Yes | No | No | View after opening as allowed |
| Evaluate tender | No | No | No | No | No | No | Yes | No | View |
| Generate contract outputs | No | No | No | No | No | No | No | Yes | View |
| Review audit trail | View | View | View | View own PE | View own PE | Limited own submissions | View assigned | View assigned | Yes |

---

## 18. Generalized Workflows

### 18.1 STD template creation workflow

1. Central STD Admin creates template family or selects an existing family.
2. Central STD Admin uploads official source document.
3. System records file metadata and source hash.
4. Central STD Admin creates new template version.
5. Sections are extracted and mapped.
6. Clauses are extracted and classified by mutability.
7. Parameters are defined.
8. Rules are defined.
9. Form schemas are defined.
10. Requirement and price schedule schemas are defined.
11. Evaluation and contract output schemas are defined.
12. Render blocks are defined.
13. Smoke tests are attached.
14. Template moves to review.
15. Reviewers approve or return with findings.
16. Approver approves template.
17. System runs smoke tests and render checks.
18. Template is activated.

### 18.2 Tender configuration workflow

1. Procurement Officer creates tender and selects procurement category.
2. System recommends active STD family/version.
3. Procurement Officer confirms active STD version.
4. System creates Tender STD Instance.
5. User completes TDS-like configuration parameters.
6. User completes requirements, schedules, inventories, price table setup, and SCC-like parameters.
7. System validates configuration.
8. User resolves validation findings.
9. System renders preview bundle.
10. PE Reviewer reviews.
11. Approver approves for publication.
12. System renders final bundle and computes hash.
13. Tender is published with bound STD version.

### 18.3 Bidder submission workflow

1. Bidder opens tender opportunity.
2. Supplier Portal receives bidder response schema generated from published STD instance.
3. Bidder completes required forms.
4. Bidder uploads required evidence.
5. Bidder completes technical conformance responses.
6. Bidder completes price schedules.
7. System validates bidder submission against published schema.
8. Bidder submits tender.
9. Submission is sealed until opening according to tender rules.

### 18.4 Evaluation workflow

1. Evaluation module loads evaluation schema from published STD instance.
2. System generates preliminary checklist.
3. Evaluators complete responsiveness checks.
4. System applies mandatory disqualification rules where applicable.
5. Technical evaluation proceeds according to published criteria.
6. Financial evaluation proceeds according to price schedule rules.
7. Qualification/post-qualification checks are recorded.
8. Award recommendation is generated according to published award basis.
9. Audit log links evaluation result to published STD schema.

### 18.5 Contract formation workflow

1. Awarded bidder is selected.
2. Contract module loads contract output schema from published STD instance and addenda history.
3. System carries forward tender identity, awarded bidder details, accepted price, schedules, requirements, subcontractors, software categories, warranties, securities, and payment terms.
4. Contract officer completes only fields that legitimately arise after award.
5. Contract forms and appendices are rendered.
6. Contract documents are approved, signed, stored, and hashed.

### 18.6 Addendum workflow

1. User requests change after publication.
2. System identifies whether change affects published bundle.
3. System performs addendum impact analysis.
4. System identifies affected sections, forms, bidder response fields, evaluation criteria, price schedules, and contract outputs.
5. Authorized reviewer approves or rejects the addendum.
6. If approved, system renders addendum notice and/or superseding bundle.
7. System notifies bidders and updates audit trail.
8. Evaluation and contract schemas are updated only through the approved addendum path.

---

## 19. Integration Requirements

### 19.1 Tender Management

Tender Management shall consume:

1. Active STD families and versions.
2. Tender configuration schemas.
3. Rendered preview bundles.
4. Published tender bundles.
5. Validation findings.
6. Addendum impact data.

Tender Management shall not directly edit locked template content.

### 19.2 Supplier Portal

Supplier Portal shall consume:

1. Published bidder response schema.
2. Required forms.
3. Required evidence rules.
4. Technical conformance matrix.
5. Price schedule schema.
6. Submission validation rules.
7. Addendum updates.

### 19.3 Evaluation Module

Evaluation Module shall consume:

1. Published evaluation schema.
2. Mandatory responsiveness checklist.
3. Technical scoring criteria.
4. Requirement conformance matrix.
5. Financial evaluation rules.
6. Qualification criteria.
7. Addendum-adjusted evaluation changes.

### 19.4 Contract Management

Contract Management shall consume:

1. Contract output schema.
2. Tender identity values.
3. Awarded bidder data.
4. Accepted price schedules.
5. Accepted requirements and conformance commitments.
6. SCC-like contract parameters.
7. Appendices and securities.
8. Addendum history.

### 19.5 Audit and Reporting

Audit shall consume:

1. Template version history.
2. Source traceability.
3. Approval history.
4. Published bundle hashes.
5. Addendum history.
6. Rule execution logs.
7. Evaluation alignment logs.
8. Contract formation traceability.

---

## 20. IT STD First Implementation Considerations

The IT STD should be used as the first full production implementation after the core engine is accepted.

The IT implementation should validate these core capabilities:

1. Locked ITT and GCC sections.
2. Controlled TDS and SCC parameters.
3. Evaluation and qualification criteria schemas.
4. Tendering form schemas.
5. Functional, architectural, performance, service, and technology requirement schemas.
6. Implementation schedule model.
7. System inventory table model.
8. Supply and installation price schedules.
9. Recurrent cost schedules.
10. Software license and intellectual property contract outputs.
11. Operational acceptance and testing outputs.
12. Warranty and post-implementation support obligations.
13. Change-order governance.

The NSSF ERP tender should be used to test the IT STD model because it contains realistic tender-specific values, mandatory requirements, scored technical criteria, module-by-module requirements, compliance tables, project management rules, testing and acceptance provisions, implementation schedule requirements, warranty/support terms, IP/escrow treatment, and contract forms.

---

## 21. Acceptance Criteria for STD Engine Core Pre-Implementation

The core module shall be considered ready for full PRD and implementation design only when the following are accepted:

1. The generalized STD meta-model is approved.
2. The universal mutability model is approved.
3. The template lifecycle and state transitions are approved.
4. The Tender STD Instance lifecycle is approved.
5. The source traceability model is approved.
6. The governance and approval workflow is approved.
7. The high-level persistent object list is approved.
8. The rule model is approved.
9. The render block model is approved.
10. The import/export package strategy is approved.
11. The addendum impact model is approved.
12. The first IT STD extraction plan is approved.
13. The NSSF ERP tender calibration approach is approved.

---

## 22. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Engine becomes IT-specific | Future STDs require rework | Generalize core meta-model before IT wizard. |
| Monolithic JSON becomes production store | Poor governance, weak querying, brittle evolution | Use normalized storage with JSON only for schemas and metadata. |
| Locked legal text is editable | Legal non-compliance | Enforce mutability at database, API, and UI levels. |
| Evaluation criteria drift from tender document | Procurement challenge risk | Generate evaluation schema from published STD instance only. |
| Addenda are handled manually | Inconsistent bidder/evaluation/contract records | Build addendum impact model into core. |
| Source traceability is incomplete | Audit weakness | Require source anchors and hashes before activation. |
| Rendering is inconsistent | Published artifacts cannot be reproduced | Use deterministic render blocks and output hashes. |
| Too much flexibility in requirements composer | Poor comparability of tenders | Use structured requirement schemas and compliance response types. |
| Too little flexibility in domain extensions | Cannot support multiple STDs | Allow domain-specific extension schemas. |
| Workflow approvals are added late | Governance gaps | Include approval/state-transition design in core from the beginning. |

---

## 23. Open Questions

These questions should be resolved before the full PRD:

1. Who is the final approval authority for activating an STD template version?
2. Can multiple active versions exist within the same STD family, or only one default active version?
3. Should PPRA-level administration and Procuring Entity-level administration be separated physically or by roles only?
4. Which output formats are mandatory for publication: PDF, DOCX, HTML, JSON, or all?
5. Should official rendered tender bundles include a machine-readable manifest?
6. How should source document extraction exceptions be recorded?
7. What level of external integration with PPRA publication or validation services is required?
8. Should addendum impact analysis be purely rule-driven or allow reviewer override with justification?
9. Should bidders be able to export structured forms to offline files and re-import them?
10. What is the retention policy for archived template versions and rendered bundles?

---

## 24. Implementation Roadmap

### Phase 1 - STD Engine Core PRD and Domain Model

Deliverables:

1. Full PRD.
2. Strict domain model tables.
3. State-transition model.
4. Roles and permissions matrix.
5. API boundary specification.
6. Storage model.
7. Import/export package contract.
8. Smoke contract framework.

### Phase 2 - Core Module Foundation

Deliverables:

1. STD family/version registry.
2. Source document registry.
3. Section and clause models.
4. Mutability enforcement.
5. Parameter and rule registry.
6. Form schema registry.
7. Requirement and price schema registry.
8. Render block registry.
9. Approval workflow.
10. Audit logging.

### Phase 3 - IT STD Extraction Matrix

Deliverables:

1. Full IT STD section map.
2. Clause map.
3. Parameter map.
4. Rule dictionary.
5. Form inventory.
6. Requirement schema.
7. Price schedule schema.
8. Evaluation schema.
9. Contract output schema.
10. Render block map.
11. Smoke tests.

### Phase 4 - IT STD Seed Package

Deliverables:

1. `KE-PPRA-IT-2022-04` template package.
2. Importable structured package.
3. Source trace manifest.
4. Render map.
5. Validation suite.
6. Activation test.

### Phase 5 - IT Tender Configuration Wizard

Deliverables:

1. Tender identity screen.
2. TDS configuration screen.
3. Participation and eligibility screen.
4. Dates and meetings screen.
5. Tender security screen.
6. Requirements composer.
7. Implementation schedule screen.
8. System inventory screen.
9. Price schedule setup.
10. Evaluation criteria screen.
11. SCC and contract parameter screen.
12. Validation and preview screen.
13. Approval and publication screen.

### Phase 6 - Supplier, Evaluation, and Contract Integration

Deliverables:

1. Supplier response schema generation.
2. Submission validation.
3. Evaluation schema generation.
4. Financial comparison support.
5. Contract form generation.
6. Addendum propagation.
7. Audit reports.

---

## 25. Smoke Contracts - Initial Set

The following smoke contracts should be created for the STD Engine Core.

### 25.1 Template activation smoke contract

Given a template version in `Approved` state, when activation is requested, the system shall activate it only if:

1. Source document hash exists.
2. Mandatory sections exist.
3. Locked sections are not editable.
4. Required parameters are mapped.
5. Required forms are mapped.
6. Required render blocks exist.
7. Smoke tests pass.

### 25.2 Locked clause smoke contract

Given a tender instance bound to an active template, when a user attempts to edit a locked clause, the system shall reject the edit and log the attempt.

### 25.3 Required parameter smoke contract

Given a tender instance with missing mandatory configuration values, when publication is requested, the system shall block publication and list missing values.

### 25.4 Render determinism smoke contract

Given the same template version and the same configuration values, when the tender bundle is rendered twice, the normalized output hash shall be identical.

### 25.5 Published immutability smoke contract

Given a published tender bundle, when a user requests a change to published content, the system shall require addendum workflow and prevent direct modification.

### 25.6 Evaluation alignment smoke contract

Given a published tender, when evaluation starts, the evaluation schema shall be loaded from the published STD instance and shall not allow criteria outside the published tender or approved addendum.

### 25.7 Contract carry-forward smoke contract

Given an awarded tender, when contract formation starts, the contract output schema shall carry forward tender identity, awarded bidder, accepted price, requirements, schedules, securities, and SCC parameters from the published tender and award record.

### 25.8 Addendum impact smoke contract

Given a post-publication change to a configured field, requirement, form, price schedule, or evaluation criterion, the system shall identify affected rendered sections and downstream bidder, evaluation, and contract outputs before approval.

---

## 26. Preliminary API Boundaries

### 26.1 STD Administration APIs

1. Create STD family.
2. Upload source document.
3. Create template version.
4. Import template package.
5. Export template package.
6. Add/update sections.
7. Add/update clauses.
8. Add/update parameters.
9. Add/update rules.
10. Add/update forms.
11. Add/update render blocks.
12. Submit template for review.
13. Approve template.
14. Activate template.
15. Supersede template.

### 26.2 Tender Configuration APIs

1. Create Tender STD Instance.
2. Load configuration schema.
3. Save configuration value.
4. Validate tender STD instance.
5. Render preview.
6. Submit for review.
7. Approve for publication.
8. Generate publication bundle.
9. Record publication hash.

### 26.3 Supplier Schema APIs

1. Load bidder response schema.
2. Load evidence requirements.
3. Validate bidder response.
4. Validate price schedule.
5. Validate technical conformance matrix.

### 26.4 Evaluation Schema APIs

1. Load evaluation schema.
2. Load preliminary checklist.
3. Load technical scoring criteria.
4. Load financial evaluation rules.
5. Record rule execution results.

### 26.5 Contract Output APIs

1. Load contract output schema.
2. Generate contract forms.
3. Generate appendices.
4. Generate securities.
5. Generate acceptance certificates.
6. Record contract output hash.

### 26.6 Addendum APIs

1. Request addendum.
2. Analyze impact.
3. Approve addendum.
4. Render addendum.
5. Supersede bundle.
6. Notify dependent modules.

---

## 27. Import/Export Package Strategy

The engine should support import/export packages for template migration, review, source control, and regression testing.

A production package should be modular, not one large file.

Recommended package structure:

```text
manifest.json
source_trace.json
sections.json
clauses.json
parameters.json
rules.json
forms.json
form_fields.json
evidence_requirements.json
requirement_schema.json
price_schedule_schema.json
evaluation_schema.json
contract_output_schema.json
render_blocks.json
smoke_tests.json
```

The package is an interchange format. It is not the runtime source of truth after import and approval.

---

## 28. Minimum Viable Core Release

The minimum viable core release should include:

1. STD family and version registry.
2. Source document metadata and hash storage.
3. Section and clause model.
4. Mutability enforcement.
5. Parameter registry.
6. Basic rule engine.
7. Form schema registry.
8. Render block registry.
9. Template lifecycle workflow.
10. Tender STD instance binding.
11. Configuration value storage.
12. Validation findings.
13. Preview rendering.
14. Publication bundle hash.
15. Audit log.

The minimum viable core release does not need every domain-specific extension, but it must be designed so that IT STD extraction can be implemented without refactoring core tables.

---

## 29. Recommended Next Artifacts

The immediate next artifacts should be produced in this order:

1. STD Engine Core Module - Full PRD.
2. STD Engine Core Module - Strict Domain Model Tables.
3. STD Engine Core Module - Governance and State Transition Specification.
4. STD Engine Core Module - Roles and Permissions Matrix.
5. STD Engine Core Module - API and Integration Boundary Specification.
6. STD Engine Core Module - Import/Export Package Contract.
7. STD for Procurement of Information Technology - Extraction Matrix.
8. STD for Procurement of Information Technology - Seed Package Specification.
9. STD Engine Core and IT STD - Smoke Contracts.
10. Cursor Implementation Pack.

---

## 30. Pre-PRD Recommendation

Proceed to the full PRD for the STD Engine Core Module before implementing the IT STD wizard.

The correct sequence is:

```text
Pre-PRD
 -> Full PRD
 -> Domain Model
 -> Governance/State Model
 -> Roles/Permissions Matrix
 -> API/Integration Boundary
 -> Import/Export Package Contract
 -> IT STD Extraction Matrix
 -> IT STD Seed Package
 -> Smoke Contracts
 -> Implementation Pack
```

This sequence protects the project from hard-coding the first STD implementation and ensures the platform can support multiple official Standard Tender Documents under one governed engine.

