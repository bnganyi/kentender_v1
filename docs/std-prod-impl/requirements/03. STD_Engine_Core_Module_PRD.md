# STD Engine Core Module - Product Requirements Document (PRD)

**Project:** KenTender e-Procurement System  
**Module:** Standard Tender Document Engine Core  
**Document type:** Product Requirements Document  
**Document status:** Draft for review  
**Version:** 0.1  
**Prepared for:** KenTender product and engineering design sequence  
**Primary implementation target:** Generalized Standard Tender Document Engine supporting multiple official STDs  
**First full STD implementation:** Standard Tender Document for Procurement of Information Technology  
**Calibration fixture:** NSSF SPS ERP System Tender, Tender No. `NSSFSPS/ICT/ERP/001/2025-2026`  

---

## 1. Document Purpose

This Product Requirements Document defines the full product requirements for the Standard Tender Document Engine Core Module, referred to in this document as the **STD Engine**.

The STD Engine shall provide the governed, reusable, legally traceable foundation for digitizing official Standard Tender Documents in the KenTender e-Procurement system. It shall support multiple STD families and shall not be hard-coded for the first Information Technology STD implementation.

This PRD expands the approved Pre-PRD direction into implementation-ready product requirements. It defines the business problem, product scope, user classes, core concepts, lifecycle states, governance requirements, functional requirements, non-functional requirements, validation behavior, integration boundaries, acceptance criteria, risks, and implementation phasing.

This document intentionally stops before strict domain modeling. The next artifact shall convert this PRD into formal domain model tables, field dictionaries, relationships, constraints, workflows, and API contracts.

---

## 2. Executive Summary

KenTender requires a controlled STD Engine because a Standard Tender Document is not merely a Word or PDF document. It is a legal and procedural template that controls tender preparation, bidder submission, tender evaluation, award, contract formation, addenda, and audit.

The earlier WORKS proof of concept demonstrated that an STD can be represented as structured, configurable, auditable data. The successful proof of concept validated the core principle:

> The STD Engine owns the official STD structure, legal text, allowed configuration surfaces, validation rules, renderable tender outputs, bidder response schemas, evaluation schemas, contract formation schemas, source traceability, governance state, and publication immutability. Other procurement modules consume these outputs; they do not recreate or override them.

The proof of concept also exposed the main correction needed for production: a monolithic JSON package is acceptable as an import/export artifact, but it must not become the production data store. Production storage must be normalized, governed, source-traced, versioned, hashable, and auditable.

The first full implementation shall use the **Standard Tender Document for Procurement of Information Technology** because it exercises the generalized engine without requiring the WORKS-specific Bills of Quantities, drawings, and measurement/valuation complexity. The IT STD still has enough complexity to validate the engine because it contains locked tendering procedures, Tender Data Sheet parameters, evaluation and qualification criteria, tendering forms, technical requirements, implementation schedules, system inventory tables, price schedules, General Conditions of Contract, Special Conditions of Contract, contract forms, software licensing, intellectual property, operational acceptance, support obligations, and change-order structures.

The NSSF SPS ERP tender shall be used as a real-world calibration fixture to test whether the IT STD model can support actual tender-specific data such as ERP module requirements, compliance matrices, technical scoring criteria, payment milestones, professional indemnity, warranty periods, implementation phases, and cloud/software/IP requirements. It shall not be treated as the official master source.

---

## 3. Source Inputs and Evidence Basis

This PRD is based on the following project inputs:

| Source | Role in this PRD |
|---|---|
| `KE-PPRA-WORKS-BLDG-2022-04-POC.json5` | Proof-of-concept package showing structured STD digitization for WORKS. |
| `STD for Works - Building and Associated Civil Engineering Works` | Prior official STD used to validate locked sections, BoQ handling, mutability, and tender/contract structure. |
| `STD for Procurement of Information Technology` | First official STD to be fully digitized using the generalized engine. |
| `NSSF SPS ERP System Tender` | Real-world calibration tender used to test practical tender configuration, evaluation, technical compliance, price schedule, and contract carry-forward. |
| `STD Engine IT Digitization Blueprint` | Prior blueprint that established the generalized STD Engine direction and IT-specific digitization approach. |
| `STD Engine Core Module Pre-PRD` | Immediate predecessor document defining scope, principles, lifecycle, storage approach, and roadmap. |

Source hierarchy:

1. Official PPRA STD source documents are authoritative for template structure and legal content.
2. Approved KenTender module artifacts define product and implementation design.
3. Real procuring entity tenders are calibration fixtures only.
4. Imported JSON/Markdown packages are interchange artifacts only until imported, reviewed, approved, and activated.

---

## 4. Business Problem

Public procurement tender documents are legal instruments. In a manual or semi-manual environment, tender documents are often created through copied Word templates, locally edited clauses, uploaded PDFs, ad-hoc spreadsheets, manually assembled evaluation criteria, and separately prepared contract forms.

This creates serious procurement risks:

1. Locked legal text may be changed without authorization.
2. Tender Data Sheet values may be incomplete, inconsistent, or contradictory.
3. Special Conditions of Contract may not align with the tender instructions.
4. Evaluation criteria may drift from what was published to bidders.
5. Bidder forms may not match the stated submission requirements.
6. Price schedules may not be machine-validated.
7. Addenda may not update all affected downstream artifacts.
8. Published documents may not be reproducible from source data.
9. Contract documents may require re-entry of information already captured during tendering.
10. Auditors may be unable to prove which STD version, clause text, rules, and forms were used.

The product problem is therefore:

> KenTender needs a generalized, governed, auditable STD Engine that can represent official Standard Tender Documents as structured template versions, control what may be configured, generate aligned tender/submission/evaluation/contract artifacts, prevent unauthorized mutation of protected legal content, and preserve source traceability from official STD source to published tender and contract outputs.

---

## 5. Product Goals

### 5.1 Business Goals

1. Ensure official Standard Tender Documents are used consistently across procuring entities.
2. Prevent unauthorized changes to locked legal sections such as ITT and GCC.
3. Reduce tender preparation errors and omissions.
4. Ensure alignment between tender document, bidder response schema, evaluation schema, and contract output.
5. Enable legally defensible audit of STD source, template version, tender configuration, publication, addenda, evaluation, award, and contract formation.
6. Support multiple STD families through one generalized engine.
7. Avoid hard-coded STD-specific logic in Tender Management, Supplier Portal, Evaluation, or Contract Management modules.
8. Enable deterministic rendering and reproducibility of published tender documents.
9. Enable future structured analytics across tender requirements, evaluation criteria, prices, and contract commitments.

### 5.2 Product Goals

1. Provide STD family and template version management.
2. Provide source document registration and traceability.
3. Provide section, clause, parameter, rule, form, requirement, price schedule, evaluation, contract, and renderer models.
4. Provide a universal mutability model.
5. Provide governed lifecycle workflows for templates and tender instances.
6. Provide declarative validation rules and smoke contracts.
7. Provide tender configuration schemas generated from active STD versions.
8. Provide bidder response schemas generated from published tender instances.
9. Provide evaluation schemas generated from published tender instances.
10. Provide contract output schemas generated from published tender and award records.
11. Provide addendum impact analysis.
12. Provide audit logs, hashes, and immutable generated bundles.
13. Provide import/export packages for controlled migration, review, source control, and regression testing.

### 5.3 Technical Goals

1. Use normalized database records for core identity, lifecycle, relationships, permissions, usage, approvals, and audit.
2. Use JSON schema fields only where flexibility is required for forms, validation expressions, render metadata, and domain-specific extensions.
3. Store locked source text and rendered outputs as immutable content blobs with hashes.
4. Preserve stable identifiers for all template elements.
5. Support version-safe evolution without modifying active versions in place.
6. Support deterministic rendering and hash comparison.
7. Expose clear APIs/events to Tender Management, Supplier Portal, Evaluation, Contract Management, and Audit modules.
8. Allow domain-specific extensions without breaking the core STD meta-model.

---

## 6. Non-Goals

The STD Engine Core Module shall not attempt to do the following in its initial release:

1. Replace the full Tender Management workflow.
2. Replace Supplier Registration.
3. Replace Supplier Portal submission UI.
4. Replace the Evaluation Committee workspace.
5. Replace Contract Management execution workflows.
6. Replace Procurement Planning.
7. Automatically infer legal meaning from uploaded documents without human review and approval.
8. Allow procuring entities to edit locked ITT or GCC text.
9. Treat a tender-specific PDF as an official STD template.
10. Treat a monolithic JSON file as the runtime source of truth.
11. Hard-code the Information Technology STD into core tables or workflows.
12. Build the IT tender wizard before the generalized core model, state transitions, and governance model are accepted.
13. Provide natural-language drafting of legal clauses as a substitute for official source-traced template management.

---

## 7. Scope

### 7.1 In Scope for STD Engine Core

The core module shall include the following capabilities:

1. STD family registry.
2. STD source document registry.
3. STD template version lifecycle.
4. Section hierarchy management.
5. Clause management.
6. Universal mutability classification.
7. Parameter management.
8. Rule management.
9. Form schema management.
10. Evidence requirement management.
11. Requirement schema management.
12. Price schedule schema management.
13. Evaluation schema management.
14. Contract output schema management.
15. Render block management.
16. Source traceability model.
17. Approval and activation workflow.
18. Template supersession and archive workflow.
19. Tender STD instance creation and binding.
20. Tender configuration value storage.
21. Validation finding storage.
22. Preview rendering.
23. Publication bundle generation and hashing.
24. Addendum impact analysis model.
25. Import/export package support.
26. Smoke contract framework.
27. Audit event logging.
28. Integration APIs/events for dependent modules.

### 7.2 Out of Scope but Dependent on STD Engine

The following modules are outside this core module but shall consume STD Engine outputs:

| Dependent Module | Dependency on STD Engine |
|---|---|
| Tender Management | Uses active STD versions, configuration schemas, preview/publication bundles, addendum impacts. |
| Supplier Portal | Uses bidder response schemas, required forms, evidence rules, conformance matrices, price schedules. |
| Evaluation Module | Uses published evaluation schemas, checklists, scoring, financial evaluation rules. |
| Contract Management | Uses contract output schemas, award data, tender commitments, SCC parameters, appendices. |
| Audit and Reporting | Uses source traceability, approval history, publication hashes, addenda, rule logs, evaluation alignment. |
| Procurement Planning | May later feed estimated cost, procurement category, method, and planning data into STD selection. |

### 7.3 Domain-Specific Extensions Supported by Core

The core module shall support domain-specific STD extensions without core redesign:

| STD Family | Example Extension Needs |
|---|---|
| Works | BoQ, drawings, site visit, NCA category, engineer role, measurement and valuation, provisional sums. |
| Information Technology | Functional requirements, architectural requirements, implementation schedule, system inventory tables, recurrent costs, software categories, operational acceptance, IP warranties. |
| Goods | Delivery schedules, item specifications, inspection, warranty, country of origin, quantities. |
| Non-Consulting Services | Service levels, deliverables, performance standards, staffing, recurrent service pricing. |
| Consulting Services | TOR, key experts, technical/financial proposal separation, quality-cost scoring, negotiations. |
| Framework Agreements | Call-off rules, lots, mini-competition rules, catalogue/pricing structures. |

---

## 8. Product Principles

The STD Engine shall be designed according to the following principles:

1. **Official source first.** All master template content must trace to an official source document or an approved administrative source.
2. **Immutable active versions.** Active template versions shall not be edited in place.
3. **Controlled configuration only.** Tender-specific variation shall occur only through approved parameters, requirement schemas, table schemas, and form schemas.
4. **No legal text drift.** Locked sections shall remain locked across import, review, activation, tender configuration, rendering, publication, and addendum workflows.
5. **One published truth.** The published tender bundle, bidder response schema, evaluation schema, and contract output schema must derive from the same STD instance.
6. **Addendum, not overwrite.** Post-publication changes must use addendum governance and impact analysis.
7. **Traceability by default.** Every material section, clause, parameter, rule, form, field, requirement, price item, evaluation criterion, and render block must be traceable.
8. **Deterministic rendering.** Same STD version plus same configuration values must generate the same normalized output hash.
9. **Generalized core, specific extensions.** The core model must remain stable while allowing domain-specific extension schemas.
10. **Audit-grade evidence.** The system must preserve enough data to defend template selection, tender configuration, publication, addenda, evaluation, award, and contract formation.

---

## 9. User Classes and Primary Needs

| User Class | Primary Needs |
|---|---|
| Central STD Administrator | Create STD families, upload sources, structure templates, manage sections/clauses/parameters/rules/forms/renderers, prepare versions for review. |
| Structuring Reviewer | Verify extraction completeness, section hierarchy, source anchors, mutability, parameters, forms, and render mappings. |
| Legal/Procurement Reviewer | Verify fidelity to official STD, locked legal text, permitted configuration surfaces, and procurement legality. |
| Template Approver | Approve a template version for activation after review and smoke tests. |
| Activation Authority | Activate approved versions and supersede older versions. |
| PE Procurement Officer | Configure a tender using an active STD version through controlled fields and structured requirements. |
| PE Reviewer/Approver | Review tender configuration, validation findings, preview bundle, and publication readiness. |
| Bidder/Supplier | Complete structured response forms, evidence uploads, technical conformance, and price schedules derived from the published tender. |
| Evaluation Committee Member | Evaluate tenders using criteria, checklists, and scoring structures from the published tender. |
| Evaluation Secretary | Coordinate evaluation records, rule execution, clarifications, and audit trail. |
| Contract Officer | Generate contract forms and appendices from award and tender data. |
| Auditor/Oversight Officer | Review template source, approvals, usage, publication hashes, addendum history, evaluation alignment, and contract carry-forward. |
| System Administrator | Manage permissions, background jobs, rendering services, storage, system health, and integration reliability. |

---

## 10. Glossary and Core Concepts

| Term | Definition |
|---|---|
| STD | Standard Tender Document issued by an authorized body, such as PPRA. |
| STD Template Family | A procurement document family, such as `KE-PPRA-IT` or `KE-PPRA-WORKS-BLDG`. |
| STD Template Version | A specific edition/revision of an STD family. |
| Source Document | Official uploaded STD source file used for extraction and traceability. |
| Section | Structural unit of the STD, such as ITT, TDS, Evaluation Criteria, Tendering Forms, GCC, SCC. |
| Clause | Legal or procedural text provision within a section. |
| Parameter | Controlled value populated for a specific tender. |
| Rule | Declarative validation, activation, calculation, scoring, rendering, or workflow rule. |
| Form Schema | Structured form definition for PE, bidder, evaluator, successful bidder, contract officer, or system. |
| Evidence Requirement | Attachment/document requirement linked to a form, criterion, or requirement. |
| Requirement Schema | Structure used to capture procuring entity requirements. |
| Price Schedule Schema | Structure used to capture pricing items, totals, and evaluation treatment. |
| Evaluation Schema | Published evaluation structure generated from the STD instance. |
| Contract Output Schema | Post-award contract form and appendix generation structure. |
| Render Block | Deterministic rendering definition for clauses, forms, tables, sections, or bundles. |
| Tender STD Instance | Tender-specific binding to one active STD template version. |
| Published Bundle | Immutable generated tender document bundle with hash and manifest. |
| Addendum Impact | Record of how a post-publication change affects published and downstream artifacts. |
| Mutability | Classification of whether and how content can be edited, parameterized, generated, or referenced. |

---

## 11. Universal Mutability Model

Every STD section, clause, field, table, form, rule, and render block shall have a mutability classification.

| Mutability Type | Meaning | Examples |
|---|---|---|
| `LOCKED_TEXT` | Text cannot be edited by procuring entity users. | ITT clauses, GCC clauses. |
| `PARAMETERIZED_TEXT` | Text is fixed except for approved placeholders. | Invitation to Tender, TDS-referenced clauses. |
| `CONTROLLED_CONFIG` | User supplies controlled values through approved fields. | TDS, SCC, tender security, currency, validity period. |
| `CONTROLLED_REQUIREMENTS` | User authors requirements through structured schema. | IT functional/technical requirements, Goods specifications. |
| `STRUCTURED_TABLE` | User completes controlled tabular data. | Price schedules, implementation schedule, system inventory. |
| `BIDDER_RESPONSE_SCHEMA` | Defines bidder response form/field/evidence requirements. | Form of Tender, declarations, conformance matrix. |
| `EVALUATION_SCHEMA` | Defines evaluation checklist, scoring, qualification, financial comparison. | Preliminary checklist, technical scoring criteria. |
| `CONTRACT_OUTPUT_SCHEMA` | Defines post-award contract forms and appendices. | Contract agreement, performance security, software appendix. |
| `GENERATED_OUTPUT` | System-generated content not directly edited by users. | Published tender bundle, addendum notice, audit summary. |
| `REFERENCE_ONLY` | Informational material not binding unless linked to a requirement. | Background notes, reference documents. |

### 11.1 Mutability Enforcement Requirements

| ID | Requirement |
|---|---|
| MUT-001 | The system shall reject any attempt to edit `LOCKED_TEXT` in a tender instance. |
| MUT-002 | The system shall allow `PARAMETERIZED_TEXT` to vary only through approved parameter values. |
| MUT-003 | The system shall validate `CONTROLLED_CONFIG` fields before publication. |
| MUT-004 | The system shall require `CONTROLLED_REQUIREMENTS` to maintain stable requirement identifiers. |
| MUT-005 | The system shall validate `STRUCTURED_TABLE` rows against schema rules before publication/submission. |
| MUT-006 | The system shall generate bidder response schemas from the published tender instance only. |
| MUT-007 | The system shall generate evaluation schemas from the published tender instance only. |
| MUT-008 | The system shall prevent contract outputs from re-entering values already captured in tender/award records unless explicitly marked post-award. |
| MUT-009 | The system shall preserve generated output hashes. |
| MUT-010 | The system shall distinguish reference-only materials from binding bidder requirements. |

---

## 12. Lifecycle and Governance Model

Governance is core scope. It shall not be implemented as a late approval wrapper.

### 12.1 STD Template Version Lifecycle

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

### 12.2 STD Template Version State Definitions

| State | Definition | Editable? | Selectable for New Tenders? |
|---|---|---:|---:|
| `Draft` | Version shell created; source may be attached; structure incomplete. | Yes | No |
| `Structuring` | Sections, clauses, parameters, rules, forms, schemas, render blocks being mapped. | Yes | No |
| `Internal Review` | Internal team reviews structure, completeness, and technical correctness. | No, except through returned changes | No |
| `Legal/Procurement Review` | Legal/procurement reviewers validate fidelity to official STD and mutability. | No, except through returned changes | No |
| `Approved` | Approved for activation but not yet available for tenders. | No | No |
| `Active` | Available for new tender configuration. | No | Yes |
| `Superseded` | Replaced by a later version; preserved for existing tenders and audit. | No | No for new tenders; yes for existing references |
| `Archived` | Retained for history only. | No | No |

### 12.3 STD Template Transition Requirements

| ID | From | To | Required Checks |
|---|---|---|---|
| STT-001 | Draft | Structuring | Source document attached or explicit exception recorded; source hash captured. |
| STT-002 | Structuring | Internal Review | Section map complete; mandatory section checklist passed; basic extraction warnings resolved or logged. |
| STT-003 | Internal Review | Structuring | Reviewer returns findings requiring correction. |
| STT-004 | Internal Review | Legal/Procurement Review | Internal review completed; smoke pre-checks passed; mutability map available. |
| STT-005 | Legal/Procurement Review | Structuring | Legal/procurement reviewer returns template for correction. |
| STT-006 | Legal/Procurement Review | Approved | Legal/procurement approval recorded; locked text verified; allowed configuration surfaces confirmed. |
| STT-007 | Approved | Active | Activation authority approves; smoke tests pass; render checks pass; template hash generated. |
| STT-008 | Active | Superseded | New version activated or supersession approved; no new tenders may select old version. |
| STT-009 | Superseded | Archived | No active tender preparation depends on the version; audit retention confirmed. |

### 12.4 STD Template Hard Blockers

The system shall block template approval or activation when any of the following is true:

1. Source document hash is missing.
2. Mandatory source metadata is missing.
3. Mandatory sections are unmapped.
4. Any `LOCKED_TEXT` section is configured as editable by procuring entity users.
5. Mandatory parameters are undefined.
6. Mandatory form schemas are missing.
7. Required render blocks are missing.
8. Smoke tests are missing.
9. Smoke tests fail.
10. Template package hash cannot be generated.
11. Legal/procurement approval is missing.
12. Source traceability is incomplete for material locked clauses.
13. The version duplicates an active version code.
14. The version attempts to overwrite an active version in place.

### 12.5 Tender STD Instance Lifecycle

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

### 12.6 Tender STD Instance State Definitions

| State | Definition |
|---|---|
| `Not Started` | Tender has not yet selected an STD or configuration has not begun. |
| `In Configuration` | PE user is completing allowed tender-specific values and requirements. |
| `Validation Failed` | Blocking validation issues exist. |
| `Ready for Review` | Configuration passes validation and is ready for review. |
| `Procurement Review` | PE reviewer/approver is reviewing the configured tender package. |
| `Approved for Tender Creation` | Approved for final render/binding. |
| `Bound to Tender` | STD configuration is formally linked to the tender record. |
| `Published` | Tender bundle rendered, hashed, and published. |
| `Addendum Required` | A post-publication change request exists. |
| `Superseded by Addendum` | Published bundle replaced or supplemented through approved addendum. |

### 12.7 Tender STD Transition Requirements

| ID | From | To | Required Checks |
|---|---|---|---|
| TST-001 | Not Started | In Configuration | Active STD version selected. |
| TST-002 | In Configuration | Validation Failed | Blocking rule fails. |
| TST-003 | Validation Failed | In Configuration | User resumes correction. |
| TST-004 | In Configuration | Ready for Review | Mandatory parameters complete; blocking validation clear; preview render available. |
| TST-005 | Ready for Review | Procurement Review | Submitted by authorized PE user. |
| TST-006 | Procurement Review | In Configuration | Reviewer returns for correction. |
| TST-007 | Procurement Review | Approved for Tender Creation | Reviewer approval recorded. |
| TST-008 | Approved for Tender Creation | Bound to Tender | Tender record confirms binding; STD instance locked against structural change. |
| TST-009 | Bound to Tender | Published | Final bundle rendered; bundle hash and manifest generated. |
| TST-010 | Published | Addendum Required | Authorized post-publication change request submitted. |
| TST-011 | Addendum Required | Superseded by Addendum | Addendum approved; affected outputs rendered and hashed. |

### 12.8 Tender STD Hard Blockers

The system shall block tender publication when any of the following is true:

1. STD version is not active at time of tender instance creation.
2. Tender instance has no template version binding.
3. Mandatory parameters are missing.
4. Blocking validation findings are unresolved.
5. Required requirements/tables/forms are incomplete.
6. Evaluation schema cannot be generated.
7. Bidder response schema cannot be generated.
8. Contract output schema cannot be generated where required.
9. Preview render fails.
10. Final bundle hash cannot be generated.
11. PE approval is missing.
12. Any locked clause differs from active template source.
13. Tender evaluation criteria include a criterion not present in the tender configuration or approved addendum.

---

## 13. Roles and Permissions - Product Requirements

The detailed roles/permissions matrix will be delivered as a separate artifact. The core PRD establishes the following minimum requirements.

| ID | Requirement |
|---|---|
| PER-001 | Only authorized central users shall create STD families. |
| PER-002 | Only authorized central users shall upload official source documents. |
| PER-003 | Only authorized central users shall create and structure template versions. |
| PER-004 | Template reviewers shall review and comment but shall not activate templates. |
| PER-005 | Legal/procurement reviewers shall approve fidelity to official STD and mutability. |
| PER-006 | Activation authority shall activate only approved versions that pass smoke tests. |
| PER-007 | PE procurement officers shall configure tender instances but shall not edit locked template content. |
| PER-008 | PE reviewers shall approve tender configuration before publication. |
| PER-009 | Bidders shall access only published bidder response schemas and their own submissions. |
| PER-010 | Evaluators shall access only evaluation schemas for assigned tenders after opening/authorization. |
| PER-011 | Contract officers shall generate contract outputs only after award authorization. |
| PER-012 | Auditors shall have read-only access to traceability, approvals, hashes, logs, and generated artifacts according to their oversight scope. |
| PER-013 | No user role shall have permission to mutate active template versions in place. |
| PER-014 | System administrators may manage technical settings but shall not bypass legal template approvals. |

---

## 14. Functional Requirements

### 14.1 STD Family Management

| ID | Requirement | Priority |
|---|---|---|
| FR-FAM-001 | The system shall allow authorized users to create STD template families. | Must |
| FR-FAM-002 | The system shall store stable family codes, names, procurement category, issuing authority, status, and default version. | Must |
| FR-FAM-003 | The system shall prevent duplicate active family codes. | Must |
| FR-FAM-004 | The system shall support multiple versions under one STD family. | Must |
| FR-FAM-005 | The system shall allow families to be active, inactive, or archived. | Should |
| FR-FAM-006 | The system shall expose active families to Tender Management for STD selection. | Must |

### 14.2 Source Document Registry

| ID | Requirement | Priority |
|---|---|---|
| FR-SRC-001 | The system shall allow authorized users to upload official source documents. | Must |
| FR-SRC-002 | The system shall compute and store a cryptographic hash for every uploaded source document. | Must |
| FR-SRC-003 | The system shall store source metadata including file name, file type, authority, issue date, revision date, upload user, upload timestamp, and page count where available. | Must |
| FR-SRC-004 | The system shall prevent source document deletion after it is linked to a template version. | Must |
| FR-SRC-005 | The system shall support extraction status tracking: Not Started, In Progress, Extracted, Reviewed, Approved, Exception Accepted. | Must |
| FR-SRC-006 | The system shall allow source trace exceptions with reviewer justification. | Should |
| FR-SRC-007 | The system shall preserve the original uploaded file separately from normalized extracted text. | Must |

### 14.3 Template Version Management

| ID | Requirement | Priority |
|---|---|---|
| FR-VER-001 | The system shall allow authorized users to create template versions under an STD family. | Must |
| FR-VER-002 | Each template version shall link to one or more source documents. | Must |
| FR-VER-003 | Each template version shall have a stable version code and lifecycle state. | Must |
| FR-VER-004 | The system shall compute a normalized template package hash before activation. | Must |
| FR-VER-005 | The system shall prevent editing of active versions. | Must |
| FR-VER-006 | The system shall allow a new version to supersede an older active version. | Must |
| FR-VER-007 | The system shall preserve historical access to superseded versions used by tenders. | Must |
| FR-VER-008 | The system shall prevent deletion of any template version referenced by a tender instance. | Must |
| FR-VER-009 | The system shall allow only approved versions to become active. | Must |
| FR-VER-010 | The system shall support activation date, effective date, supersession date, and archive date metadata. | Should |

### 14.4 Section Management

| ID | Requirement | Priority |
|---|---|---|
| FR-SEC-001 | The system shall support hierarchical STD sections and subsections. | Must |
| FR-SEC-002 | Each section shall have stable identifiers, official references, titles, sort order, parent section, and mutability type. | Must |
| FR-SEC-003 | The system shall support section-level render requirements. | Must |
| FR-SEC-004 | The system shall support source traceability at section level. | Must |
| FR-SEC-005 | The system shall support section inclusion/visibility rules. | Should |
| FR-SEC-006 | The system shall identify mandatory sections required for template activation. | Must |
| FR-SEC-007 | The system shall validate that mandatory sections exist before activation. | Must |

### 14.5 Clause Management

| ID | Requirement | Priority |
|---|---|---|
| FR-CLA-001 | The system shall store clauses under sections with official clause references where available. | Must |
| FR-CLA-002 | Each clause shall have mutability type, source trace, source text hash, normalized text hash, and render order. | Must |
| FR-CLA-003 | The system shall support locked clauses. | Must |
| FR-CLA-004 | The system shall support parameterized clauses with approved placeholders. | Must |
| FR-CLA-005 | The system shall validate that locked clauses cannot be edited in tender instances. | Must |
| FR-CLA-006 | The system shall detect and flag any mismatch between active locked clause text and rendered output. | Must |
| FR-CLA-007 | The system shall support conditional clause rendering based on approved rules. | Should |
| FR-CLA-008 | The system shall preserve prior clause hashes when versions are superseded. | Must |

### 14.6 Parameter Management

| ID | Requirement | Priority |
|---|---|---|
| FR-PAR-001 | The system shall define tender-specific configuration parameters for each template version. | Must |
| FR-PAR-002 | Each parameter shall have code, label, data type, required flag, default value, validation schema, lifecycle stage, render targets, and source basis. | Must |
| FR-PAR-003 | Supported data types shall include string, long text, number, integer, date, datetime, boolean, amount, percentage, select, multi-select, file reference, table, and object. | Must |
| FR-PAR-004 | The system shall support controlled option lists for select parameters. | Must |
| FR-PAR-005 | The system shall validate required parameters before publication. | Must |
| FR-PAR-006 | The system shall support parameter reuse across sections, forms, render blocks, rules, and contract outputs. | Must |
| FR-PAR-007 | The system shall track whether a parameter is PE-entered, system-generated, bidder-entered, evaluator-entered, award-entered, or contract-entered. | Must |
| FR-PAR-008 | The system shall support parameter deprecation only through a new template version. | Should |

### 14.7 Rule Management

| ID | Requirement | Priority |
|---|---|---|
| FR-RUL-001 | The system shall support declarative rules attached to template versions. | Must |
| FR-RUL-002 | Rule types shall include validation, activation, calculation, scoring, render visibility, evidence activation, eligibility, workflow, addendum impact, and contract output activation. | Must |
| FR-RUL-003 | Each rule shall have code, type, scope, severity, expression, affected objects, message, source basis, and test cases. | Must |
| FR-RUL-004 | Rule severity shall include info, warning, and blocker. | Must |
| FR-RUL-005 | The system shall execute rules during template activation, tender configuration, publication, bidder submission, evaluation, contract generation, and addendum impact analysis as applicable. | Must |
| FR-RUL-006 | The system shall record rule execution results for audit where material. | Must |
| FR-RUL-007 | The system shall prevent publication where unresolved blocker rules exist. | Must |
| FR-RUL-008 | The system shall support rule versioning through template versioning, not in-place active edits. | Must |
| FR-RUL-009 | The system shall allow reviewer override of warning-level findings with justification where configured. | Should |
| FR-RUL-010 | The system shall not allow reviewer override of blocker-level findings unless an explicit exception rule permits it and records approval. | Should |

### 14.8 Form Schema Management

| ID | Requirement | Priority |
|---|---|---|
| FR-FRM-001 | The system shall define structured form schemas for each template version. | Must |
| FR-FRM-002 | Form respondent types shall include Procuring Entity, Bidder, Evaluator, Successful Tenderer, Contract Officer, and System. | Must |
| FR-FRM-003 | Each form shall have code, title, lifecycle stage, respondent type, activation rule, field schema, evidence requirements, render block, and source basis. | Must |
| FR-FRM-004 | The system shall support field-level validation. | Must |
| FR-FRM-005 | The system shall support conditional fields. | Must |
| FR-FRM-006 | The system shall support repeatable sections/tables inside forms. | Must |
| FR-FRM-007 | The system shall generate bidder-facing forms from published tender instances. | Must |
| FR-FRM-008 | The system shall preserve submitted form schemas as at publication, even if the master STD later changes. | Must |
| FR-FRM-009 | The system shall support rendering completed forms into tender or contract documents where required. | Should |

### 14.9 Evidence Requirement Management

| ID | Requirement | Priority |
|---|---|---|
| FR-EVD-001 | The system shall define evidence requirements linked to forms, fields, requirements, criteria, or rules. | Must |
| FR-EVD-002 | Evidence requirements shall support respondent type, mandatory flag, file type constraints, validity date requirements, issuing authority, and verification status. | Must |
| FR-EVD-003 | The system shall activate evidence requirements conditionally based on rules. | Must |
| FR-EVD-004 | The system shall validate mandatory evidence during bidder submission where applicable. | Must |
| FR-EVD-005 | The system shall support evidence review results during evaluation. | Should |
| FR-EVD-006 | The system shall preserve evidence requirement definitions as published. | Must |

### 14.10 Requirement Schema Management

| ID | Requirement | Priority |
|---|---|---|
| FR-REQ-001 | The system shall support structured procuring entity requirement schemas. | Must |
| FR-REQ-002 | Requirement categories shall be configurable by STD family. | Must |
| FR-REQ-003 | Requirement items shall have stable codes, description, mandatory flag, response type, evidence requirement, evaluation linkage, and contract linkage. | Must |
| FR-REQ-004 | The system shall support mandatory, desirable, and optional requirement classifications. | Must |
| FR-REQ-005 | The system shall support bidder response types including yes/no, compliant/non-compliant, narrative, numeric, select, table, file evidence, and reference page. | Must |
| FR-REQ-006 | The system shall support requirement import/export through controlled templates. | Should |
| FR-REQ-007 | The system shall support requirement grouping by module, category, lot, phase, or deliverable. | Must |
| FR-REQ-008 | The system shall link requirements to evaluation criteria where applicable. | Must |
| FR-REQ-009 | The system shall link accepted requirements to contract obligations where applicable. | Must |
| FR-REQ-010 | The system shall preserve requirement text and identifiers after publication. | Must |

### 14.11 Price Schedule Schema Management

| ID | Requirement | Priority |
|---|---|---|
| FR-PRI-001 | The system shall define price schedule schemas by STD family/version. | Must |
| FR-PRI-002 | Price schedules shall support one-time cost, recurrent cost, provisional cost, optional cost, taxes, currency, quantity, unit, unit price, total, and summary totals. | Must |
| FR-PRI-003 | The system shall support computed totals and validation rules. | Must |
| FR-PRI-004 | The system shall support tax-inclusive and tax-exclusive configurations. | Must |
| FR-PRI-005 | The system shall support financial evaluation treatment flags for each cost category. | Must |
| FR-PRI-006 | The system shall support linkage between price schedule items and requirement/inventory items where applicable. | Should |
| FR-PRI-007 | The system shall preserve published price schedule structure for bidder submission and evaluation. | Must |
| FR-PRI-008 | The system shall prevent financial evaluation using price fields outside the published price schedule unless added by approved addendum. | Must |

### 14.12 Evaluation Schema Management

| ID | Requirement | Priority |
|---|---|---|
| FR-EVL-001 | The system shall define evaluation schemas for each template version. | Must |
| FR-EVL-002 | Evaluation schemas shall include preliminary responsiveness, eligibility, mandatory criteria, technical scoring, qualification, financial evaluation, and award basis where applicable. | Must |
| FR-EVL-003 | The system shall support pass/fail criteria. | Must |
| FR-EVL-004 | The system shall support scored criteria with weights and pass marks. | Must |
| FR-EVL-005 | The system shall support requirement-by-requirement conformance evaluation. | Must |
| FR-EVL-006 | The system shall support financial comparison based on published price schedules. | Must |
| FR-EVL-007 | The system shall support margin of preference, reservations, and other preference rules where enabled by the STD. | Should |
| FR-EVL-008 | The system shall preserve the published evaluation schema at tender publication. | Must |
| FR-EVL-009 | The system shall prevent evaluators from adding unpublished criteria during evaluation. | Must |
| FR-EVL-010 | The system shall update evaluation schemas after publication only through approved addendum governance. | Must |

### 14.13 Contract Output Schema Management

| ID | Requirement | Priority |
|---|---|---|
| FR-CON-001 | The system shall define contract output schemas for each template version. | Must |
| FR-CON-002 | Contract outputs shall support letters, agreements, securities, appendices, acceptance certificates, change-order forms, disclosure forms, and other contract artifacts. | Must |
| FR-CON-003 | Contract outputs shall carry forward tender identity, successful bidder, accepted price, scope, schedules, requirements, SCC parameters, securities, warranties, and addenda where applicable. | Must |
| FR-CON-004 | The system shall identify which contract fields are carried forward and which are post-award inputs. | Must |
| FR-CON-005 | The system shall prevent contract forms from contradicting the published tender or approved addenda. | Must |
| FR-CON-006 | The system shall generate contract output hashes. | Must |
| FR-CON-007 | The system shall preserve contract output source traceability to the originating STD template version and tender instance. | Must |

### 14.14 Render Block Management

| ID | Requirement | Priority |
|---|---|---|
| FR-RND-001 | The system shall define deterministic render blocks for sections, clauses, forms, tables, requirements, schedules, evaluation summaries, and contract outputs. | Must |
| FR-RND-002 | Render blocks shall bind to sections, clauses, parameters, rules, and schemas. | Must |
| FR-RND-003 | Render blocks shall support conditional visibility. | Must |
| FR-RND-004 | Render blocks shall support table rendering. | Must |
| FR-RND-005 | Render blocks shall support preview and final publication modes. | Must |
| FR-RND-006 | The system shall compute normalized output hashes for rendered bundles. | Must |
| FR-RND-007 | The same version and same values shall produce the same normalized hash. | Must |
| FR-RND-008 | Render failures shall produce actionable validation findings. | Must |
| FR-RND-009 | The system shall support PDF and HTML outputs at minimum; DOCX output should be supported where required by business policy. | Should |
| FR-RND-010 | Rendered bundles shall include a machine-readable manifest. | Should |

### 14.15 Source Traceability

| ID | Requirement | Priority |
|---|---|---|
| FR-TRC-001 | The system shall support source trace fields for sections, clauses, parameters, rules, forms, fields, requirements, price schedules, evaluation criteria, contract outputs, and render blocks. | Must |
| FR-TRC-002 | Source trace shall include source document, page range where available, section reference, clause reference, anchor, source text hash, normalized text hash, extraction confidence, and review status where applicable. | Must |
| FR-TRC-003 | The system shall require source trace for locked legal content before activation. | Must |
| FR-TRC-004 | The system shall allow reviewed exceptions where source trace is not applicable, with justification. | Should |
| FR-TRC-005 | Audit users shall be able to view source trace from published output back to template source. | Must |

### 14.16 Tender STD Instance Management

| ID | Requirement | Priority |
|---|---|---|
| FR-TIN-001 | The system shall create a Tender STD Instance when a tender binds to an active STD version. | Must |
| FR-TIN-002 | Each tender instance shall store template version ID, tender ID, lifecycle state, configuration values, validation findings, render outputs, and addendum history. | Must |
| FR-TIN-003 | The system shall prevent tender instances from binding to non-active STD versions for new tenders. | Must |
| FR-TIN-004 | The system shall preserve the STD version used by each tender even after supersession. | Must |
| FR-TIN-005 | The system shall support cloning/copying configuration only where allowed and always against a current active version unless explicitly authorized. | Could |

### 14.17 Tender Configuration Value Management

| ID | Requirement | Priority |
|---|---|---|
| FR-CFG-001 | The system shall store tender-specific values separately from master template data. | Must |
| FR-CFG-002 | The system shall validate each value against parameter schema and rules. | Must |
| FR-CFG-003 | The system shall record user, timestamp, previous value, new value, and reason where configured. | Must |
| FR-CFG-004 | The system shall lock configuration values after publication except through addendum workflow. | Must |
| FR-CFG-005 | The system shall support draft saves during configuration. | Must |
| FR-CFG-006 | The system shall expose configuration completeness status. | Must |

### 14.18 Generated Bundle Management

| ID | Requirement | Priority |
|---|---|---|
| FR-BUN-001 | The system shall generate preview bundles before publication. | Must |
| FR-BUN-002 | The system shall generate final publication bundles after approval. | Must |
| FR-BUN-003 | Each final bundle shall store output format, render timestamp, rendered by, normalized hash, binary hash, template version, tender instance, and manifest. | Must |
| FR-BUN-004 | Published bundles shall be immutable. | Must |
| FR-BUN-005 | Superseded bundles shall remain accessible for audit. | Must |
| FR-BUN-006 | The system shall preserve addendum bundles separately from original published bundles. | Must |

### 14.19 Addendum Impact Management

| ID | Requirement | Priority |
|---|---|---|
| FR-ADD-001 | The system shall require addendum workflow for post-publication changes. | Must |
| FR-ADD-002 | The system shall identify affected sections, clauses, parameters, forms, bidder fields, requirements, price schedules, evaluation criteria, contract outputs, and render blocks. | Must |
| FR-ADD-003 | The system shall show addendum impact before approval. | Must |
| FR-ADD-004 | The system shall record reviewer approval or rejection of addendum impact. | Must |
| FR-ADD-005 | The system shall generate addendum notice and/or superseding bundle. | Must |
| FR-ADD-006 | The system shall notify dependent modules of approved addendum changes. | Should |
| FR-ADD-007 | The system shall prevent evaluation from starting on outdated schemas where an approved addendum changes evaluation criteria or bidder response requirements. | Must |
| FR-ADD-008 | The system shall preserve addendum hash and link to affected original bundle. | Must |

### 14.20 Import/Export Package Management

| ID | Requirement | Priority |
|---|---|---|
| FR-PKG-001 | The system shall support importing template packages. | Must |
| FR-PKG-002 | The system shall support exporting template packages. | Must |
| FR-PKG-003 | Packages shall be modular rather than one monolithic runtime file. | Should |
| FR-PKG-004 | Import shall validate manifest, source trace, sections, clauses, parameters, rules, forms, schemas, render blocks, and smoke tests. | Must |
| FR-PKG-005 | Imported packages shall enter Draft or Structuring state, not Active state. | Must |
| FR-PKG-006 | Exported packages shall include manifest, source trace, sections, clauses, parameters, rules, forms, evidence requirements, requirement schema, price schedule schema, evaluation schema, contract output schema, render blocks, and smoke tests where applicable. | Must |
| FR-PKG-007 | The package format shall be an interchange format, not the production source of truth after import. | Must |

### 14.21 Audit Event Management

| ID | Requirement | Priority |
|---|---|---|
| FR-AUD-001 | The system shall log material events in the STD lifecycle. | Must |
| FR-AUD-002 | Audit events shall include actor, timestamp, object type, object ID, action, previous state/value, new state/value, reason, IP/session metadata where available, and related workflow ID. | Must |
| FR-AUD-003 | The system shall log approval events separately from ordinary edits. | Must |
| FR-AUD-004 | The system shall log denied attempts to edit locked content. | Must |
| FR-AUD-005 | The system shall log template activation, supersession, publication, addendum, and contract output generation. | Must |
| FR-AUD-006 | Audit logs shall be append-only for ordinary users and administrators. | Must |
| FR-AUD-007 | Audit views shall allow tracing from published tender output back to STD version and source document. | Must |

---

## 15. IT STD First Implementation Requirements

The core engine shall be validated against the Information Technology STD as the first full implementation.

### 15.1 IT STD Capability Coverage

The engine must support the following IT STD features without core refactoring:

| IT STD Feature | Required Engine Capability |
|---|---|
| Locked ITT | Locked section and clause model. |
| TDS | Controlled configuration parameters. |
| Evaluation and Qualification Criteria | Evaluation schema, rules, scoring, pass/fail criteria. |
| Tendering Forms | Bidder form schemas and evidence requirements. |
| Requirements of Information System | Controlled requirement schemas. |
| Technical Requirements | Requirement categories and conformance matrix. |
| Implementation Schedule | Structured schedule table. |
| System Inventory Tables | Structured inventory/cost item tables. |
| Price Schedules | Supply/install and recurrent cost schemas. |
| GCC | Locked contract conditions. |
| SCC | Controlled contract parameters. |
| Contract Forms | Contract output schemas. |
| Software Licenses/IP | Contract appendices and warranty/indemnity fields. |
| Operational Acceptance | Acceptance milestones, certificates, functional guarantees. |
| Support/Maintenance | Recurrent cost and SLA requirement structures. |
| Change Orders | Contract output and post-award change forms. |

### 15.2 NSSF ERP Calibration Use

The NSSF ERP tender shall be used to test whether the IT STD model can capture, validate, render, and evaluate:

1. Tender identity.
2. Tender Data Sheet values.
3. JV member limit.
4. Currency.
5. Alternative tender status.
6. Tender validity period.
7. Professional indemnity requirement.
8. Tender submission deadline.
9. Performance security percentage.
10. Payment milestones.
11. Warranty period.
12. Mandatory preliminary requirements.
13. Technical qualification requirements.
14. Technical scoring criteria and pass mark.
15. ERP module requirements.
16. Compliance matrix rows.
17. Implementation phases.
18. Data migration, integration, training, testing, acceptance, cloud hosting, warranty, support, and IP requirements.
19. Price schedule requirements.
20. Contract forms.

Calibration rule:

> The NSSF tender may expose missing fields or usability requirements, but it shall not override the official IT STD structure unless an authorized template reviewer approves a generalized or IT-specific extension.

---

## 16. User Experience Requirements

### 16.1 STD Administration Workspace

The STD Administration workspace shall provide screens for:

1. STD families.
2. Source documents.
3. Template versions.
4. Section tree.
5. Clause editor/reviewer.
6. Mutability map.
7. Parameters.
8. Rules.
9. Forms and fields.
10. Evidence requirements.
11. Requirement schemas.
12. Price schedule schemas.
13. Evaluation schemas.
14. Contract output schemas.
15. Render blocks.
16. Smoke tests.
17. Review findings.
18. Approval history.
19. Activation and supersession.
20. Usage history.

UX requirements:

| ID | Requirement |
|---|---|
| UX-ADM-001 | The section tree shall show mutability and source trace status. |
| UX-ADM-002 | Locked clauses shall be visually distinct from configurable areas. |
| UX-ADM-003 | Reviewers shall be able to view source trace beside extracted content. |
| UX-ADM-004 | Activation readiness shall show unresolved blockers clearly. |
| UX-ADM-005 | Template versions shall show status, active/default indicators, supersession chain, and tender usage count. |

### 16.2 Tender Configuration Workspace

The Tender Configuration workspace shall provide guided configuration derived from the active STD version.

UX requirements:

| ID | Requirement |
|---|---|
| UX-TEN-001 | Users shall see only configurable fields, not editable locked legal text. |
| UX-TEN-002 | The system shall group fields by tender preparation flow, not merely by database object. |
| UX-TEN-003 | Users shall see completeness indicators for each configuration area. |
| UX-TEN-004 | Users shall see validation findings with severity and affected fields. |
| UX-TEN-005 | Users shall be able to generate preview bundles before submitting for review. |
| UX-TEN-006 | Published bundles shall display version, hash, publication timestamp, and addendum status. |

### 16.3 Review and Approval UX

| ID | Requirement |
|---|---|
| UX-REV-001 | Reviewers shall see a structured checklist for template review and tender configuration review. |
| UX-REV-002 | Reviewers shall be able to approve, reject, or return with findings. |
| UX-REV-003 | All returns shall require a finding/reason. |
| UX-REV-004 | Approval screens shall show blockers, warnings, source trace status, smoke test status, and render status. |

### 16.4 Audit UX

| ID | Requirement |
|---|---|
| UX-AUD-001 | Auditors shall be able to trace a published tender section back to template version and source document. |
| UX-AUD-002 | Auditors shall be able to view template approvals, tender approvals, publication hash, and addendum history. |
| UX-AUD-003 | Auditors shall be able to compare original and addendum-superseded bundles. |
| UX-AUD-004 | Auditors shall be able to export an audit manifest. |

---

## 17. Integration Requirements

### 17.1 Tender Management Integration

The STD Engine shall provide Tender Management with:

1. List of active STD families and versions.
2. Recommended STD based on procurement category.
3. Tender configuration schema.
4. Validation results.
5. Preview bundle.
6. Final publication bundle.
7. Published manifest.
8. Addendum impact results.
9. Published bidder/evaluation/contract schemas.

Tender Management shall not directly edit active template structure or locked content.

### 17.2 Supplier Portal Integration

The STD Engine shall provide Supplier Portal with:

1. Published bidder response schema.
2. Required tendering forms.
3. Required evidence rules.
4. Technical conformance matrix.
5. Price schedule schema.
6. Submission validation rules.
7. Addendum-adjusted schemas.

Supplier Portal shall validate submissions against the schema that was published for that tender.

### 17.3 Evaluation Module Integration

The STD Engine shall provide Evaluation Module with:

1. Published preliminary checklist.
2. Published mandatory requirements.
3. Published technical evaluation criteria.
4. Published requirement conformance matrix.
5. Published financial evaluation rules.
6. Published price comparison schema.
7. Published qualification criteria.
8. Addendum history affecting evaluation.

Evaluation Module shall not allow unpublished evaluation criteria.

### 17.4 Contract Management Integration

The STD Engine shall provide Contract Management with:

1. Contract output schema.
2. Tender identity values.
3. Awarded bidder details.
4. Accepted price schedules.
5. Accepted requirements and commitments.
6. SCC/contract parameters.
7. Required contract forms.
8. Required appendices.
9. Securities and acceptance certificate templates.
10. Addendum history.

Contract Management shall distinguish carried-forward tender/award values from true post-award inputs.

### 17.5 Audit and Reporting Integration

The STD Engine shall expose:

1. Source document metadata and hashes.
2. Template package hashes.
3. Section and clause traceability.
4. Template approval events.
5. Tender configuration approval events.
6. Publication bundle hashes.
7. Addendum hashes.
8. Rule execution logs.
9. Evaluation schema alignment.
10. Contract output traceability.

---

## 18. API Boundary Requirements

Detailed API specifications will be delivered later. This PRD defines required API groups.

### 18.1 STD Administration APIs

1. Create/list/update STD family.
2. Upload/list/read source document metadata.
3. Create/list/read template version.
4. Import/export template package.
5. Manage sections.
6. Manage clauses.
7. Manage parameters.
8. Manage rules.
9. Manage forms/fields.
10. Manage evidence requirements.
11. Manage requirement schemas.
12. Manage price schedule schemas.
13. Manage evaluation schemas.
14. Manage contract output schemas.
15. Manage render blocks.
16. Manage smoke tests.
17. Submit for review.
18. Return with findings.
19. Approve.
20. Activate.
21. Supersede.
22. Archive.

### 18.2 Tender Configuration APIs

1. Create Tender STD Instance.
2. Load configuration schema.
3. Save configuration value.
4. Save structured requirements.
5. Save structured schedules/tables.
6. Validate instance.
7. Render preview.
8. Submit for review.
9. Approve for publication.
10. Generate final bundle.
11. Record publication hash.
12. Load published manifest.

### 18.3 Bidder Schema APIs

1. Load bidder response schema.
2. Load required evidence.
3. Load technical conformance matrix.
4. Load price schedule schema.
5. Validate bidder response payload.
6. Validate bidder evidence completeness.
7. Validate price schedule arithmetic.

### 18.4 Evaluation Schema APIs

1. Load evaluation schema.
2. Load preliminary checklist.
3. Load technical scoring criteria.
4. Load conformance matrix.
5. Load financial evaluation rules.
6. Record rule execution outputs.
7. Validate evaluation criteria alignment.

### 18.5 Contract Output APIs

1. Load contract output schema.
2. Generate contract form.
3. Generate contract bundle.
4. Generate appendices.
5. Generate securities.
6. Generate acceptance certificates.
7. Record contract output hash.

### 18.6 Addendum APIs

1. Request addendum.
2. Analyze addendum impact.
3. Return addendum for correction.
4. Approve addendum.
5. Render addendum notice.
6. Render superseding bundle.
7. Record addendum hash.
8. Notify dependent modules.

---

## 19. Event Requirements

The system shall emit events for downstream modules and audit.

| Event | Trigger | Consumers |
|---|---|---|
| `std.template_version.created` | New version created. | Audit, Admin UI. |
| `std.template_version.submitted_for_review` | Review submission. | Review workflow. |
| `std.template_version.approved` | Template approval. | Audit, Admin UI. |
| `std.template_version.activated` | Version activated. | Tender Management, Audit. |
| `std.template_version.superseded` | Version superseded. | Tender Management, Audit. |
| `std.tender_instance.created` | Tender binds STD. | Tender Management. |
| `std.tender_instance.validation_failed` | Blocking validation. | Tender Management. |
| `std.tender_instance.ready_for_review` | Configuration complete. | PE Review workflow. |
| `std.tender_bundle.published` | Tender bundle published. | Supplier Portal, Evaluation, Audit. |
| `std.addendum.requested` | Post-publication change requested. | Tender Management, Review workflow. |
| `std.addendum.approved` | Addendum approved. | Supplier Portal, Evaluation, Contract Management, Audit. |
| `std.evaluation_schema.locked` | Evaluation starts or publication locks schema. | Evaluation Module. |
| `std.contract_schema.generated` | Contract formation begins. | Contract Management. |

---

## 20. Data Storage Requirements

### 20.1 Storage Architecture

The STD Engine shall use hybrid storage:

1. **Relational tables** for identity, relationships, lifecycle states, permissions, approvals, references, usage, and audit.
2. **JSON schema fields** for flexible form schemas, validation expressions, requirement structures, price schedule definitions, render metadata, and domain-specific extensions.
3. **Immutable content storage** for source files, locked text snapshots, rendered outputs, publication bundles, addendum bundles, and contract output bundles.
4. **Hashes** for source documents, clauses, normalized package, rendered output, publication bundle, addendum bundle, and contract output.
5. **Append-only event log** for material actions and state transitions.

### 20.2 Runtime Source of Truth

The production database and immutable content storage shall be the runtime source of truth after package import and approval.

A JSON/Markdown/file package shall be treated as:

1. An import artifact before approval.
2. An export artifact for review, migration, source control, or regression testing.
3. Not the authoritative runtime data store after import.

### 20.3 Hash Requirements

| Object | Hash Required? |
|---|---:|
| Source document | Yes |
| Locked clause source text | Yes |
| Normalized clause text | Yes |
| Template package | Yes before activation |
| Rendered preview | Should |
| Published bundle | Yes |
| Addendum bundle | Yes |
| Contract output bundle | Yes |
| Export package | Yes |

---

## 21. Security Requirements

| ID | Requirement |
|---|---|
| SEC-001 | The system shall enforce role-based access control for all STD Engine actions. |
| SEC-002 | The system shall prevent unauthorized mutation of active template versions at API and database layers. |
| SEC-003 | The system shall prevent unauthorized access to draft templates, review comments, bidder schemas before publication, and unpublished tender configurations. |
| SEC-004 | The system shall log denied attempts to access or mutate restricted content. |
| SEC-005 | The system shall protect immutable content blobs from overwrite. |
| SEC-006 | The system shall preserve separation between template administration permissions and tender configuration permissions. |
| SEC-007 | System administrators shall not bypass procurement/legal approval workflows through ordinary UI actions. |
| SEC-008 | Published bidder/evaluation schemas shall be available only according to procurement stage and permissions. |
| SEC-009 | Audit users shall have read-only access according to scope and legal authority. |

---

## 22. Non-Functional Requirements

### 22.1 Reliability

| ID | Requirement |
|---|---|
| NFR-REL-001 | Template activation shall be atomic: either all activation checks pass and state changes, or no activation state changes. |
| NFR-REL-002 | Publication shall be atomic: either the final bundle, manifest, hash, and state update complete, or publication fails without partial publication. |
| NFR-REL-003 | Addendum approval shall be atomic across impacted STD Engine records. |
| NFR-REL-004 | Render failures shall not corrupt template or tender configuration data. |

### 22.2 Performance

| ID | Requirement |
|---|---|
| NFR-PER-001 | Loading an active STD configuration schema should complete within acceptable interactive UI response time for typical templates. |
| NFR-PER-002 | Validation should return actionable findings without excessive delay for typical tender configurations. |
| NFR-PER-003 | Rendering may run asynchronously for large bundles but must expose status, errors, and retry behavior. |
| NFR-PER-004 | Audit queries by tender ID, template version, source document, and bundle hash should be indexed. |

### 22.3 Maintainability

| ID | Requirement |
|---|---|
| NFR-MNT-001 | The core engine shall not contain hard-coded IT STD section codes except in seed/configuration data. |
| NFR-MNT-002 | Domain-specific STD behavior shall be implemented through extension schemas and rules where possible. |
| NFR-MNT-003 | Rule expressions and render blocks shall be testable through smoke contracts. |
| NFR-MNT-004 | Import/export packages shall support source-control-friendly diffs. |
| NFR-MNT-005 | Template version changes shall be reviewed through version diff views. |

### 22.4 Auditability

| ID | Requirement |
|---|---|
| NFR-AUD-001 | The system shall support traceability from source document to published tender bundle. |
| NFR-AUD-002 | The system shall support traceability from published tender bundle to bidder response schema. |
| NFR-AUD-003 | The system shall support traceability from published tender bundle to evaluation schema. |
| NFR-AUD-004 | The system shall support traceability from published tender bundle and award record to contract output. |
| NFR-AUD-005 | The system shall preserve historical data for superseded template versions used by tenders. |

### 22.5 Usability

| ID | Requirement |
|---|---|
| NFR-USE-001 | Procurement users shall not need to understand internal JSON packages to configure a tender. |
| NFR-USE-002 | Reviewers shall see clear state, blockers, warnings, and source trace status. |
| NFR-USE-003 | Validation messages shall identify affected fields and required corrective action. |
| NFR-USE-004 | Locked content shall be visibly protected. |

---

## 23. Validation and Rule Execution

### 23.1 Validation Scopes

The system shall support validation in the following scopes:

1. Template package import.
2. Template structuring completeness.
3. Template activation readiness.
4. Tender configuration completeness.
5. Tender publication readiness.
6. Bidder response completeness.
7. Price schedule arithmetic.
8. Evaluation schema alignment.
9. Contract output readiness.
10. Addendum impact analysis.

### 23.2 Validation Finding Model

Each validation finding shall include:

1. Finding ID.
2. Related rule ID.
3. Severity: info, warning, blocker.
4. Scope.
5. Affected object type.
6. Affected object ID.
7. Message.
8. Suggested correction.
9. Created timestamp.
10. Resolved timestamp.
11. Resolved by.
12. Override status, if allowed.
13. Override justification, if allowed.

### 23.3 Rule Execution Logging

The system shall log material rule executions where they affect:

1. Template activation.
2. Tender publication.
3. Bidder disqualification/submission blocking.
4. Evaluation criteria/scoring.
5. Financial evaluation.
6. Contract output generation.
7. Addendum impact.

---

## 24. Smoke Contracts

The system shall support smoke contracts as testable acceptance checks.

### 24.1 Template Activation Smoke Contract

Given a template version in `Approved` state, when activation is requested, the system shall activate it only if:

1. Source document hash exists.
2. Mandatory sections exist.
3. Locked sections are not editable.
4. Required parameters are mapped.
5. Required forms are mapped.
6. Required render blocks exist.
7. Template package hash is generated.
8. Smoke tests pass.

### 24.2 Locked Clause Smoke Contract

Given a tender instance bound to an active template, when a user attempts to edit a locked clause, the system shall reject the edit and log the attempt.

### 24.3 Required Parameter Smoke Contract

Given a tender instance with missing mandatory configuration values, when publication is requested, the system shall block publication and list missing values.

### 24.4 Render Determinism Smoke Contract

Given the same template version and the same configuration values, when the tender bundle is rendered twice, the normalized output hash shall be identical.

### 24.5 Published Immutability Smoke Contract

Given a published tender bundle, when a user requests a change to published content, the system shall require addendum workflow and prevent direct modification.

### 24.6 Evaluation Alignment Smoke Contract

Given a published tender, when evaluation starts, the evaluation schema shall be loaded from the published STD instance and shall not allow criteria outside the published tender or approved addendum.

### 24.7 Contract Carry-Forward Smoke Contract

Given an awarded tender, when contract formation starts, the contract output schema shall carry forward tender identity, awarded bidder, accepted price, requirements, schedules, securities, and contract parameters from the published tender and award record.

### 24.8 Addendum Impact Smoke Contract

Given a post-publication change to a configured field, requirement, form, price schedule, or evaluation criterion, the system shall identify affected rendered sections and downstream bidder, evaluation, and contract outputs before approval.

### 24.9 Active Version Immutability Smoke Contract

Given an active STD template version, when any user attempts to alter a section, clause, parameter, rule, form, schema, or render block, the system shall reject the change and require creation of a new version.

### 24.10 Source Trace Activation Smoke Contract

Given a template version with locked clauses lacking source trace, when activation is requested, the system shall block activation unless an approved source trace exception exists.

---

## 25. Acceptance Criteria

The STD Engine Core Module shall be accepted for implementation completion only when all must-have requirements are implemented and the following end-to-end scenarios pass.

### 25.1 Template Administration Acceptance

1. Authorized user creates an STD family.
2. Authorized user uploads a source document.
3. System captures metadata and source hash.
4. Authorized user creates a template version.
5. Authorized user structures sections and clauses.
6. Authorized user assigns mutability classifications.
7. Authorized user defines parameters, rules, forms, schemas, and render blocks.
8. Reviewer reviews and returns findings or approves.
9. Legal/procurement reviewer approves.
10. Activation authority activates after smoke tests pass.
11. Active version becomes selectable for new tenders.
12. Active version cannot be edited in place.

### 25.2 Tender Configuration Acceptance

1. PE user creates a tender STD instance from an active version.
2. System loads the configuration schema.
3. PE user completes controlled fields and requirements.
4. System validates fields, rules, schedules, forms, and render readiness.
5. System blocks publication with unresolved blockers.
6. System renders preview after blockers are resolved.
7. PE reviewer approves.
8. System generates final bundle, manifest, and hash.
9. Tender is published.
10. Published bundle cannot be edited in place.

### 25.3 Bidder Schema Acceptance

1. Supplier Portal loads bidder response schema from the published tender instance.
2. Bidder completes required forms.
3. Bidder provides required evidence.
4. Bidder completes price schedule and requirement conformance.
5. System validates response against published schema.
6. Schema remains stable even if master STD is later superseded.

### 25.4 Evaluation Acceptance

1. Evaluation module loads published evaluation schema.
2. Evaluators complete preliminary responsiveness checklist.
3. System enforces mandatory criteria.
4. Evaluators complete technical scoring where applicable.
5. Financial evaluation uses published price schedule fields only.
6. Evaluation cannot include unpublished criteria.
7. Evaluation audit trail links to published tender bundle and STD version.

### 25.5 Contract Formation Acceptance

1. Contract module loads contract output schema after award.
2. System carries forward tender, bidder, award, price, requirement, schedule, security, and SCC/contract parameter values.
3. Contract officer completes only post-award fields.
4. System renders contract forms and appendices.
5. Contract output hash is generated and recorded.

### 25.6 Addendum Acceptance

1. User requests post-publication change.
2. System identifies affected published and downstream artifacts.
3. Reviewer approves or rejects the addendum.
4. Approved addendum generates addendum notice and/or superseding bundle.
5. Supplier Portal, Evaluation, and Contract modules consume updated schemas where affected.
6. Original published bundle and addendum bundle remain auditable.

---

## 26. Release Plan

### 26.1 Release 1 - Core Foundation

Deliverables:

1. STD family registry.
2. Source document registry.
3. Template version lifecycle.
4. Section and clause models.
5. Mutability enforcement.
6. Parameter registry.
7. Basic rule registry and execution.
8. Form schema registry.
9. Render block registry.
10. Approval workflow.
11. Audit log.
12. Template activation smoke contracts.

### 26.2 Release 2 - Tender Binding and Publication

Deliverables:

1. Tender STD instance.
2. Configuration value storage.
3. Validation findings.
4. Preview rendering.
5. Final bundle rendering.
6. Publication hash and manifest.
7. Published immutability.
8. Addendum request shell.

### 26.3 Release 3 - Schema Consumers

Deliverables:

1. Bidder response schema API.
2. Evidence requirement API.
3. Price schedule validation API.
4. Evaluation schema API.
5. Contract output schema API.
6. Evaluation alignment checks.

### 26.4 Release 4 - Addendum and Contract Carry-Forward

Deliverables:

1. Addendum impact rules.
2. Addendum approval workflow.
3. Addendum render/bundle/hash.
4. Contract carry-forward mapping.
5. Contract output generation.
6. Audit manifest exports.

### 26.5 Release 5 - IT STD Seed and Calibration

Deliverables:

1. IT STD extraction matrix.
2. IT STD seed package.
3. IT requirement schema.
4. IT price schedule schema.
5. IT evaluation schema.
6. IT contract output schema.
7. NSSF ERP calibration test.

---

## 27. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Engine becomes IT-specific | Cannot support other STDs without redesign. | Keep IT behavior in seed package and extension schemas, not core code. |
| Monolithic JSON becomes runtime store | Weak governance, poor querying, brittle changes. | Use normalized persistent storage; packages remain import/export artifacts. |
| Locked text can be edited | Legal and audit failure. | Enforce mutability at UI, API, and database/service layers. |
| Evaluation drifts from published tender | Procurement challenge risk. | Generate and lock evaluation schema from published tender instance. |
| Addenda are handled manually | Inconsistent downstream records. | Build addendum impact model into core release. |
| Source traceability is incomplete | Audit weakness. | Require source trace for locked content and material schema elements. |
| Rendering is non-deterministic | Published artifacts cannot be reproduced. | Implement deterministic render blocks and normalized output hashing. |
| Requirements composer is too flexible | Poor comparability and uncontrolled tender content. | Use structured requirement schemas, response types, and evaluation linkages. |
| Requirements composer is too rigid | Cannot support real tenders. | Allow domain-specific extension schemas and controlled import/export. |
| Approvals are vague | Governance gaps. | Implement explicit states, transitions, roles, blockers, and approval events. |
| Contract module re-enters tender data | Contract drift and audit issues. | Define contract carry-forward mappings. |
| Supersession breaks existing tenders | Legal/audit inconsistency. | Preserve historical template versions and tender instance bindings. |

---

## 28. Open Questions

The following questions should be resolved before or during the domain model artifact:

1. Who is the final activation authority for STD template versions?
2. Can more than one active version exist for one STD family, or should one version be marked default while others remain active for special circumstances?
3. Should template administration be centralized only, or should procuring entities have controlled local extensions for non-legal requirements?
4. Which rendered output formats are mandatory at launch: PDF, HTML, DOCX, JSON manifest?
5. Should the publication bundle always include both human-readable and machine-readable artifacts?
6. What cryptographic hash standard shall be used for source, template, bundle, and addendum hashes?
7. Should addendum impact analysis allow reviewer override, and if so under what conditions?
8. Should bidders be allowed offline exports/imports of response schemas?
9. What retention policy applies to archived template versions and rendered bundles?
10. Should template packages be stored in a version-control repository in addition to database storage?
11. What external PPRA publication or validation integrations are required?
12. How should official amendments to a source STD be introduced when a new document is unavailable but circulars or corrigenda exist?

---

## 29. Dependency Map

| Dependency | Required For | Timing |
|---|---|---|
| Role/permission model | All workflows | Before implementation. |
| Domain model tables | Database/API implementation | Next artifact. |
| Governance/state transition spec | Workflow implementation | Next or immediately after domain model. |
| Render service decision | Preview/publication bundles | Before Release 2. |
| Hashing standard | Source and publication integrity | Before Release 1 implementation. |
| Storage service decision | Source files and bundles | Before Release 1 implementation. |
| IT STD extraction matrix | First full STD seed | After core domain model. |
| NSSF ERP calibration mapping | IT STD validation | After IT extraction matrix. |
| Tender Management API boundary | Tender instance creation/publication | Before Release 2. |
| Supplier Portal API boundary | Bidder schemas | Before Release 3. |
| Evaluation API boundary | Evaluation alignment | Before Release 3. |
| Contract API boundary | Contract carry-forward | Before Release 4. |

---

## 30. Implementation Readiness Checklist

The module is ready to move from PRD to strict domain modeling when the following are accepted:

1. Scope and non-goals accepted.
2. Universal mutability model accepted.
3. Template version lifecycle accepted.
4. Tender STD instance lifecycle accepted.
5. Approval/state-transition requirements accepted.
6. Functional requirements accepted.
7. Source traceability requirements accepted.
8. Addendum governance accepted.
9. Published immutability requirements accepted.
10. Integration boundaries accepted.
11. IT STD first implementation approach accepted.
12. NSSF ERP calibration role accepted.
13. Open questions either resolved or assigned to the domain model/governance artifact.

Explicit approval/state-transition check:

> This PRD includes approval and state-transition design as core scope. The next artifact may proceed to strict domain modeling only if the template lifecycle, tender instance lifecycle, transition blockers, approval roles, and immutable active/published states are accepted.

---

## 31. Next Artifact

The next artifact shall be:

**STD Engine Core Module - Strict Domain Model Tables**

It shall define:

1. Domain entities.
2. Field names.
3. Field types.
4. Required/optional status.
5. Enumerations.
6. Relationships.
7. Unique constraints.
8. Immutability constraints.
9. Lifecycle state fields.
10. Audit fields.
11. Source trace fields.
12. Hash fields.
13. Indexing recommendations.
14. Domain-specific extension strategy.
15. Seed data requirements.

After the domain model, the next artifacts shall be:

1. Governance and State Transition Specification.
2. Roles and Permissions Matrix.
3. API and Integration Boundary Specification.
4. Import/Export Package Contract.
5. IT STD Extraction Matrix.
6. IT STD Seed Package Specification.
7. Smoke Contracts.
8. Cursor Implementation Pack.

---

## 32. PRD Recommendation

Proceed to strict domain modeling only after review of this PRD.

The correct sequence remains:

```text
Pre-PRD
 -> Full PRD
 -> Strict Domain Model Tables
 -> Governance/State Model
 -> Roles/Permissions Matrix
 -> API/Integration Boundary
 -> Import/Export Package Contract
 -> IT STD Extraction Matrix
 -> IT STD Seed Package
 -> Smoke Contracts
 -> Implementation Pack
```

This sequence protects the project from hard-coding the IT STD implementation and ensures that KenTender can support multiple official Standard Tender Documents under one governed STD Engine.
