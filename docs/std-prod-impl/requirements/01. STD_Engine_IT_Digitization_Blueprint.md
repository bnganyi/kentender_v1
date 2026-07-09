# STD Engine Digitization Blueprint and Implementation Plan

**Project:** KenTender e-Procurement System  
**Subject:** Generalized Standard Tender Document Engine, with first full production implementation for the Standard Tender Document for Procurement of Information Technology  
**Reference implementation candidate:** NSSF SPS ERP System Tender, Tender No. NSSFSPS/ICT/ERP/001/2025-2026  
**Document status:** Working implementation blueprint  
**Prepared for:** KenTender product and implementation team  

---

## 1. Executive Direction

The Works proof of concept succeeded. It validated the core idea that Standard Tender Documents should be digitized as controlled, legally governed, reusable templates, not treated as uploaded Word or PDF attachments.

The next implementation should not copy the Works PoC file structure directly into production. The PoC JSON should be treated as an import/export package format, not as the runtime data store. The production STD Engine should store the official STD as normalized, auditable records, with JSON used only where it adds real value for schema, rules, rendering metadata, and structured requirement definitions.

The engine should be generalized from the beginning. The Information Technology STD should be the first full production digitization, but the same engine must later support Works, Goods, Non-Consulting Services, Consulting Services, Framework Agreements, and other PPRA STDs.

The working principle is:

> The STD Engine is the legal and procedural source of truth for tender document generation, bidder response structures, evaluation structures, contract formation outputs, and post-publication addendum governance. Tender Management consumes STD Engine outputs; it does not recreate or override them manually.

---

## 2. Source Inputs Reviewed

This blueprint is based on four inputs:

1. The earlier Works PoC package: `KE-PPRA-WORKS-BLDG-2022-04-POC.json5`.
2. The official PPRA Standard Tender Document for Procurement of Works - Building and Associated Civil Engineering Works, April 2022 revision.
3. The official PPRA Standard Tender Document for Procurement of Information Technology, Doc. 10.
4. The NSSF SPS ERP tender document, Tender No. NSSFSPS/ICT/ERP/001/2025-2026.

The Information Technology STD is suitable as the first full production implementation because it is simpler than Works in some respects: there is no Bills of Quantities module, no engineering drawings, no measurement-and-valuation contract machinery, and no site-based construction execution model. However, it is not a trivial STD. It introduces a different complexity: structured information-system requirements, conformance matrices, implementation schedules, recurrent costs, software licensing, intellectual property, operational acceptance, support obligations, and change-order governance.

---

## 3. Evaluation of the Works PoC

### 3.1 What worked

The Works PoC correctly proved the following design choices:

1. A Standard Tender Document can be represented as a structured template package.
2. Sections can be classified by mutability.
3. Tender-specific values can be captured through controlled fields.
4. Legal clauses can be protected from direct editing.
5. Bidder forms can be activated conditionally.
6. Validation rules can be expressed declaratively.
7. Domain-specific native modules, such as a Bills of Quantities module for Works, can be linked to the STD rather than embedded as uncontrolled prose.
8. The generated tender package can be assembled from a mix of locked text, configured values, structured requirements, bidder-response forms, and downstream contract artifacts.

These decisions should be retained.

### 3.2 What must change before production

The Works PoC should not become the production data model unchanged. The improvements below are mandatory before full implementation.

| PoC limitation | Production correction |
|---|---|
| Single large JSON carries too much runtime meaning | Use JSON as an import/export package only; store approved templates in normalized database tables. |
| Section mutability exists but is too coarse | Use a universal mutability model, with domain-specific extensions. |
| Fields are useful but not sufficiently anchored | Every field must carry section, clause, source page, source anchor, legal basis, rule scope, and render target. |
| Forms are mostly activation metadata | Forms must become complete structured schemas, including fields, validations, evidence policies, respondent type, workflow stage, and downstream usage. |
| Rules are valid but shallow | Rules must include lifecycle stage, severity, blocking behavior, affected objects, test cases, and source basis. |
| Render map is empty | Rendering must be a first-class model: render blocks, content bindings, ordering, conditional visibility, and output hash. |
| Governance is not complete | Template lifecycle, approval workflow, versioning, supersession, and addendum impact analysis must be core features. |
| Tender instance and template concepts are not fully separated | The STD master template must be immutable after activation; tender-specific configuration values must live separately. |
| No formal source traceability model | Every extracted section, clause, parameter, rule, form, and requirement must be traceable back to the official source document. |
| No automated regression/smoke suite | Each template package must include smoke contracts proving that locked sections, required fields, render outputs, and validation rules behave correctly. |

### 3.3 Production verdict on the PoC

The PoC validated the approach. It should be used as a learning artifact and seed design, not as the final architecture.

The production STD Engine must be database-backed, version-controlled, source-traceable, approval-governed, render-deterministic, and domain-extensible.

---

## 4. Generalized STD Engine Approach

### 4.1 Core concept

An STD is not a document in the ordinary sense. In the system, an STD should be represented as:

1. A template family.
2. A versioned official template.
3. A hierarchy of sections and clauses.
4. A mutability model.
5. A parameter model.
6. A rule model.
7. A form model.
8. A requirement model.
9. A price/schedule model.
10. An evaluation model.
11. A contract-output model.
12. A render model.
13. A governance and audit model.

The user sees a guided tender configuration experience. The system maintains the controlled legal structure underneath.

### 4.2 Universal STD lifecycle

Every STD template version should move through this lifecycle:

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

Rules:

1. Only an Approved template version can be activated.
2. Only one Active version should be used by default for new tenders in a given template family, unless policy allows multiple active variants.
3. Once Active, a template version is immutable.
4. Any change to locked text, form structure, evaluation logic, requirement schema, or render behavior requires a new template version.
5. A template version already used by a tender can never be physically deleted.
6. Superseded versions remain available for audit and for tenders that already used them.
7. Published tender outputs must preserve the exact STD version and configuration values used at publication time.

### 4.3 Universal tender STD instance lifecycle

When a Procuring Entity uses an STD for a tender, the tender-specific STD instance should move through this lifecycle:

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

Rules:

1. A tender may bind only to an Active STD template version.
2. Ordinary users may configure only allowed parameters, requirements, schedules, forms, and SCC/TDS fields.
3. Locked sections cannot be directly edited.
4. All mandatory configuration fields must be completed before publication.
5. The generated tender bundle must be hashed and preserved.
6. After publication, changes must be processed through addendum governance.
7. Addendum impact analysis must identify affected sections, forms, schedules, evaluation criteria, supplier response requirements, and contract outputs.

---

## 5. Generalized Storage Architecture

### 5.1 Storage principle

Use hybrid relational plus JSON storage.

Relational tables should hold identity, lifecycle, references, ordering, governance, permissions, approvals, usage, audit, and joins. JSON columns should hold complex schemas, validation expressions, render bindings, requirement models, and extensible domain-specific metadata.

Do not store an approved STD only as one JSON blob.

### 5.2 Storage layers

| Layer | Purpose |
|---|---|
| Relational records | Template families, versions, sections, clauses, fields, rules, forms, approvals, usage, audit. |
| JSON schema columns | Field constraints, requirement structures, conditional expressions, render metadata, domain-specific extensions. |
| Immutable content blobs | Locked clause text, official source extracts, rendered HTML/PDF/DOCX, publication bundles. |
| Hashes | Source document hash, normalized text hash, template version hash, rendered output hash, addendum hash. |
| Event log | Import, extraction, normalization, review, approval, activation, binding to tender, publication, addendum, supersession. |

### 5.3 Core tables or DocTypes

The following objects should be created as generalized STD Engine records. They can be implemented as database tables, Frappe DocTypes, or equivalent persistent models.

| Object | Purpose |
|---|---|
| `STDTemplateFamily` | Identifies the STD family, such as Works, IT, Goods, or Services. |
| `STDTemplateVersion` | Stores one version of an STD family, including status, source, effective date, and hash. |
| `STDSourceDocument` | Stores official source file metadata, page count, hash, source authority, and extraction status. |
| `STDSection` | Stores hierarchy, numbering, title, part, order, mutability, and render behavior. |
| `STDClause` | Stores locked or parameterized clause text with source trace and hash. |
| `STDParameter` | Stores configurable tender-specific fields, allowed values, constraints, and render targets. |
| `STDParameterOption` | Stores controlled options for select fields. |
| `STDRule` | Stores validation, activation, calculation, warning, blocking, and consistency rules. |
| `STDFormSchema` | Stores the definition of a bidder, PE, evaluator, or contract form. |
| `STDFormField` | Stores field-level schemas, validation rules, respondent type, and evidence rules. |
| `STDEvidenceRequirement` | Stores required attachments, document types, validity rules, issuer requirements, and workflow stage. |
| `STDRequirementSchema` | Stores the structure used for PE-authored requirements. |
| `STDRequirementItem` | Stores one functional, technical, performance, service, legal, implementation, or support requirement. |
| `STDPriceScheduleSchema` | Stores the structure of price tables and cost categories. |
| `STDEvaluationSchema` | Stores preliminary, technical, financial, qualification, and award criteria. |
| `STDContractOutputSchema` | Stores downstream contract forms, appendices, acceptance certificates, and securities. |
| `STDRenderBlock` | Stores deterministic document rendering blocks and conditional inclusion logic. |
| `STDApprovalEvent` | Stores reviewer, approver, decision, timestamp, comments, and state transition. |
| `STDUsage` | Records which tenders used which STD version. |
| `TenderSTDInstance` | Stores the tender's binding to an active STD version. |
| `TenderSTDConfigurationValue` | Stores PE-entered values for a tender-specific STD instance. |
| `TenderSTDValidationFinding` | Stores blockers, warnings, and informational validation findings. |
| `TenderGeneratedBundle` | Stores final rendered tender documents and hashes. |
| `TenderAddendumImpact` | Stores affected sections, forms, rules, requirements, schedules, and output artifacts. |

### 5.4 Source traceability fields

Every extractable object should include these fields where applicable:

| Field | Purpose |
|---|---|
| `source_document_id` | Links object to the official source document. |
| `source_page_start` | First source page. |
| `source_page_end` | Last source page. |
| `source_section_ref` | Official section reference, such as `Section II - TDS`. |
| `source_clause_ref` | Clause reference, if applicable. |
| `source_anchor` | Internal anchor, paragraph marker, table marker, or normalized heading path. |
| `source_text_hash` | Hash of extracted source text. |
| `normalized_text_hash` | Hash of normalized text after cleaning. |
| `extraction_confidence` | Manual, OCR, parsed text, or verified extraction confidence. |
| `review_status` | Pending, reviewed, accepted, rejected, superseded. |
| `reviewed_by` | Responsible reviewer. |
| `reviewed_at` | Timestamp. |

This is non-negotiable. Without source traceability, the engine cannot defend the legal integrity of generated documents.

---

## 6. Universal Mutability Model

The mutability model should be generalized beyond Works and IT.

| Mutability type | Meaning | Example |
|---|---|---|
| `LOCKED_LEGAL_TEXT` | Text must be used without modification. | ITT, GCC. |
| `PARAMETERIZED_LEGAL_TEXT` | Text is fixed except for controlled placeholders. | Invitation to Tender, cover page, notification forms. |
| `CONTROLLED_PARAMETER_TABLE` | PE fills only allowed data points. | TDS, SCC. |
| `CONTROLLED_EVALUATION_SCHEMA` | Criteria may be selected or completed only within STD-permitted boundaries. | Evaluation and Qualification Criteria. |
| `STRUCTURED_BIDDER_RESPONSE_SCHEMA` | Bidder must respond using generated fields/forms. | Tenderer information, price schedules, conformance forms. |
| `PE_AUTHORED_REQUIREMENT_SCHEMA` | PE authors content inside a controlled structure. | Technical specifications, service requirements, schedules. |
| `NATIVE_TRANSACTION_MODULE` | Domain-specific module drives output. | BoQ for Works; System Inventory for IT. |
| `CONTROLLED_REFERENCE_MATERIAL` | Background content supports interpretation but does not create requirements. | Existing systems, reports, legal background. |
| `DOWNSTREAM_GENERATED_CONTRACT_ARTIFACT` | Generated after award or contract finalization. | Contract Agreement, appendices, acceptance certificate. |
| `EXTERNAL_ATTACHMENT_REFERENCE` | File attachment is referenced, controlled, and versioned. | Drawings, network diagrams, process maps. |
| `SYSTEM_GENERATED_AUDIT_ARTIFACT` | Produced by the platform. | Publication hash summary, addendum impact report. |

The engine should treat mutability as enforceable behavior, not a label.

---

## 7. Generalized Package Format

### 7.1 Package role

The STD package is an interchange format. It is used for import, export, review, diffing, and migration. It is not the runtime source of truth.

### 7.2 Recommended package structure

```text
/std-package
  manifest.json
  source_documents.json
  source_trace.json
  sections.json
  clauses.json
  parameters.json
  parameter_options.json
  rules.json
  forms.json
  form_fields.json
  evidence_requirements.json
  requirements_schema.json
  requirements_seed.json
  price_schedule_schema.json
  evaluation_schema.json
  contract_output_schema.json
  render_blocks.json
  governance.json
  smoke_tests.json
  sample_tender_instances.json
```

### 7.3 Package import behavior

The import process should:

1. Validate manifest completeness.
2. Validate source document hashes.
3. Validate section hierarchy.
4. Validate mutability constraints.
5. Validate parameter IDs and render references.
6. Validate rule references.
7. Validate form and field schemas.
8. Validate evaluation and price schedule schema consistency.
9. Validate render block coverage.
10. Run smoke tests.
11. Store imported records in Draft status.
12. Require review and approval before activation.

---

## 8. IT STD Digitization Profile

### 8.1 Why IT should be the first full implementation

The IT STD is a good first production target because it requires the engine to handle real structured procurement complexity without the additional measurement, drawing, and construction supervision complexity of Works.

The IT STD requires the engine to support:

1. Tender identity and invitation generation.
2. Locked ITT text.
3. TDS parameterization.
4. Evaluation and qualification schemas.
5. Tendering forms.
6. Price schedule forms.
7. Information-system requirements.
8. Functional, architectural, performance, service, and technology specifications.
9. Implementation schedules.
10. System inventory tables.
11. Background and informational materials.
12. Locked GCC text.
13. SCC parameterization.
14. Contract forms and appendices.
15. Software licensing, intellectual property, confidentiality, acceptance, warranties, support, and change orders.

### 8.2 IT STD section classification

| IT STD area | Engine treatment |
|---|---|
| Cover and tender identity page | Parameterized generated section. |
| Invitation to Tender | Parameterized generated section. |
| Section I - Instructions to Tenderers | Locked legal text. |
| Section II - Tender Data Sheet | Controlled parameter table. |
| Section III - Evaluation and Qualification Criteria | Controlled evaluation schema. |
| Section IV - Tendering Forms | Structured bidder response schemas. |
| Price Schedule Forms | Native price schedule schema. |
| Section V - Requirements of the Information System | PE-authored requirement schema. |
| Technical Requirements | PE-authored structured requirements. |
| Implementation Schedule | Native milestone and deliverable schedule. |
| System Inventory Tables | Native inventory and recurrent-cost tables. |
| Background and Informational Materials | Controlled reference material; cannot introduce requirements. |
| General Conditions of Contract | Locked legal text. |
| Special Conditions of Contract | Controlled parameter table. |
| Contract Forms and Appendices | Downstream generated contract artifacts. |
| Change Order Forms | Downstream contract administration artifacts. |
| Beneficial Ownership Disclosure | Structured form and evidence requirement. |

### 8.3 IT-specific native objects

The following IT domain objects should be added on top of the universal STD Engine objects.

| IT object | Purpose |
|---|---|
| `ITRequirementGroup` | Groups requirements by module, subsystem, domain, phase, or functional area. |
| `ITRequirementItem` | One requirement statement, normally expressed as a mandatory or optional obligation. |
| `ITRequirementConformanceField` | Captures bidder compliance, explanation, reference page, and deviation. |
| `ITFunctionalRequirement` | Business process or business function requirement. |
| `ITArchitecturalRequirement` | Architecture, hosting, security, integration, scalability, or technology architecture requirement. |
| `ITPerformanceRequirement` | Availability, throughput, response time, concurrency, recovery, or SLA requirement. |
| `ITServiceSpecification` | Services required from the supplier, such as installation, customization, migration, training, and support. |
| `ITTechnologySpecification` | Hardware, software, cloud, network, database, platform, or integration specification. |
| `ITImplementationMilestone` | Milestone, phase, deliverable, target date, acceptance point, and dependency. |
| `ITSystemInventoryItem` | Component, site, quantity, technical reference, cost category, and recurrent-cost status. |
| `ITPriceScheduleLine` | Pricing line linked to module, inventory item, milestone, or service category. |
| `ITSoftwareCategory` | Standard software, third-party software, custom software, configuration, or bespoke development. |
| `ITLicenseRequirement` | Named user, concurrent user, subscription, perpetual, maintenance, and license ownership rules. |
| `ITAcceptanceTest` | Unit, integration, performance, regression, UAT, operational acceptance, or commissioning test. |
| `ITSupportSLA` | Response time, resolution time, severity class, uptime, support window, and escalation. |
| `ITContractAppendixItem` | Supplier representative, subcontractors, software categories, custom materials, revised prices, finalization minutes. |

---

## 9. IT Requirements Composer

### 9.1 Purpose

The IT Requirements Composer is the most important product surface for the IT STD. It prevents the Procuring Entity from turning the technical requirements into an uncontrolled Word attachment.

The composer should allow authorized users to define requirements in structured rows, grouped into logical sections, with clear links to bidder response, evaluation, price schedules, implementation milestones, and contract obligations.

### 9.2 Requirement item structure

Each requirement should carry at least the following fields:

| Field | Purpose |
|---|---|
| `requirement_id` | Stable internal ID, such as `IT-GEN-001`. |
| `requirement_group` | Module, subsystem, domain, or section. |
| `requirement_type` | Functional, architectural, performance, service, technology, security, integration, data migration, training, support, legal, regulatory, documentation, acceptance. |
| `requirement_text` | Requirement stated as an obligation. |
| `priority` | Mandatory, desirable, optional, informational. |
| `compliance_response_required` | Whether the bidder must provide Yes/No and explanation. |
| `evidence_required` | Whether the bidder must attach proof or reference pages. |
| `evaluation_treatment` | Pass/fail, scored, reference only, financial comparison, contract deliverable. |
| `phase` | Implementation phase, if applicable. |
| `module` | Functional module or subsystem. |
| `linked_price_line` | Price schedule reference, if applicable. |
| `linked_inventory_item` | System inventory reference, if applicable. |
| `linked_milestone` | Implementation milestone reference, if applicable. |
| `acceptance_test_required` | Whether acceptance testing must cover this requirement. |
| `contract_carry_forward` | Whether the requirement becomes a contract obligation. |
| `source_basis` | STD source section, PE-authored requirement, addendum, or clarification. |
| `version_status` | Draft, approved, published, superseded. |

### 9.3 Requirement language governance

The engine should encourage requirements to be written as obligations, for example:

```text
The System must ...
The Supplier must ...
The Supplier shall provide ...
The System shall support ...
```

The system should warn against weak language such as:

```text
The Procuring Entity would like ...
The solution should preferably ...
The vendor may consider ...
World-class system ...
Modern and robust platform ...
```

This is not cosmetic. Vague requirements damage evaluation and contract enforcement.

### 9.4 Brand or platform-specific requirements

The engine should support brand-specific or platform-specific requirements, but they must be governed.

When a user enters a specific product, platform, vendor, or proprietary technology, the engine should require:

1. Justification.
2. Approval by the authorized procurement/legal/technical authority.
3. Confirmation that the requirement is permitted under applicable procurement rules.
4. Classification as one of:
   - justified interoperability requirement;
   - standardization requirement;
   - compatibility with existing estate;
   - regulatory or security requirement;
   - prohibited or unjustified proprietary restriction.

This is important because the NSSF ERP tender requires Microsoft Dynamics 365 Business Central and a Microsoft partner authorization. That may be legitimate if justified by the Procuring Entity's approved strategy, installed base, or interoperability needs, but the engine should not allow such requirements to be inserted without a justification and approval trail.

---

## 10. Price Schedule and System Inventory Model

### 10.1 Core design

The IT price model must not be implemented as a Works BoQ. It needs a separate IT price schedule model.

The IT STD links implementation schedule, system inventory tables, and price schedules. The system should enforce this relationship.

```text
Requirement
 -> Deliverable or subsystem
 -> Implementation milestone
 -> System inventory item
 -> Price schedule line
 -> Supplier response
 -> Evaluation comparison
 -> Contract obligation
 -> Acceptance test
```

### 10.2 Required price schedule categories

The IT implementation should support at least the following categories:

| Category | Example |
|---|---|
| Supply and installation cost | Software, licenses, hardware, configuration, implementation. |
| Professional services | Analysis, design, customization, integration, project management. |
| Data migration | Extraction, transformation, loading, validation, reconciliation. |
| Training | End users, super users, technical administrators, executives, trustees. |
| Documentation | User manuals, admin guides, installation guides, configuration guides. |
| Recurrent costs | Support, maintenance, subscriptions, cloud hosting, annual licenses. |
| Warranty-period costs | Included or separately itemized where applicable. |
| Optional or conditional costs | Optional modules, additional users, additional support years. |
| Third-party costs | Third-party software, APIs, SMS gateway, payment integrations. |
| Cloud and hosting | Compute, storage, backup, disaster recovery, network/security services. |

### 10.3 Price schedule validation

Validation rules should check:

1. Every mandatory module has a corresponding price line.
2. Every recurrent-cost requirement has recurrent-cost pricing.
3. Every implementation phase has pricing and milestones.
4. Currency is consistent with the TDS/SCC.
5. VAT treatment is explicit.
6. Totals reconcile from sub-tables to summaries.
7. Price schedule rows align with system inventory rows.
8. Optional items are clearly separated from evaluated price, if not included in evaluation.
9. Maintenance and support periods match SCC requirements.
10. Cloud infrastructure assumptions are explicit and comparable.

---

## 11. Evaluation Model

### 11.1 Generalized evaluation layers

The engine should support evaluation as a generated structure from the active STD and tender configuration.

| Layer | Purpose |
|---|---|
| Preliminary responsiveness | Mandatory documents, forms, securities, serialization, signatures, eligibility. |
| Technical qualification | Minimum capability, experience, personnel, financial capacity, local presence, certifications. |
| Technical scoring | Weighted assessment of solution, methodology, personnel, support, migration, training. |
| Requirement conformance | Requirement-by-requirement compliance matrix. |
| Financial evaluation | Price schedule comparison and corrections. |
| Preference/reservation evaluation | Applied only if enabled and legally applicable. |
| Abnormally low/high review | Estimate-linked workflow and justification review. |
| Award determination | Lowest evaluated responsive tender, or other method if the specific STD permits it. |

### 11.2 Evaluation schema object

Each criterion should include:

| Field | Purpose |
|---|---|
| `criterion_id` | Stable criterion ID. |
| `stage` | Preliminary, technical, financial, qualification, award. |
| `criterion_text` | Description. |
| `criterion_type` | Pass/fail, score, formula, document check, calculated, evaluator judgment. |
| `maximum_score` | For scored criteria. |
| `minimum_required_score` | For threshold criteria. |
| `supporting_document_required` | Evidence required from bidder. |
| `evidence_rule_id` | Link to evidence requirement. |
| `source_basis` | STD source or tender-specific configuration basis. |
| `evaluator_role` | Procurement, technical, finance, legal, committee. |
| `scoring_guidance` | Controlled guidance. |
| `appears_in_published_tender` | Whether criterion is visible to bidders. |
| `carry_forward_to_evaluation_module` | Whether system generates evaluation workflow from it. |

### 11.3 NSSF calibration insight

The NSSF ERP tender uses a three-stage evaluation: preliminary examination, technical evaluation, and financial evaluation. It also specifies a technical scoring structure totaling 100 points with a minimum pass mark of 75 points. This confirms that the engine must support both pass/fail and scored evaluation criteria in the IT domain.

The NSSF tender also contains a detailed compliance matrix with columns for requirement description, compliance, Yes/No response, and reference pages. This confirms that the supplier response module must generate a requirement-by-requirement conformance form, not only accept a free-form technical proposal.

---

## 12. Contract Formation and Post-Award Model

The STD Engine must not stop at tender publication.

For IT, many obligations become meaningful only after award: source code transfer or escrow, software licenses, confidentiality, implementation plan, acceptance testing, warranty, support SLA, subcontractor approval, change orders, and contract appendices.

### 12.1 Contract output objects

| Contract object | Source |
|---|---|
| Notification of Intention to Award | Tender result and statutory workflow. |
| Letter of Award | Award decision and accepted tender values. |
| Contract Agreement | Awarded tender, SCC, GCC, accepted price, addenda. |
| Supplier Representative Appendix | Supplier submission and contract finalization. |
| Adjudicator Appendix | SCC / dispute configuration. |
| Approved Subcontractors Appendix | Supplier proposal and PE approval. |
| Software Categories Appendix | Supplier IP/software disclosure. |
| Custom Materials Appendix | Supplier technical/IP forms. |
| Revised Price Schedules | Negotiation/finalization outcomes, where permitted. |
| Contract Finalization Minutes | Finalization workflow. |
| Performance Security | Award value and SCC. |
| Advance Payment Security | If applicable. |
| Installation and Acceptance Certificates | Implementation milestones and acceptance tests. |
| Change Order Forms | Contract administration. |
| Beneficial Ownership Disclosure | Supplier disclosure and statutory forms. |

### 12.2 Carry-forward rules

The engine should explicitly mark which tender fields carry forward into contract formation.

Examples:

| Tender item | Contract carry-forward |
|---|---|
| Accepted price | Contract Agreement and payment schedule. |
| Implementation schedule | SCC, project plan baseline, acceptance milestones. |
| Supplier technical proposal | Contract technical obligations, subject to accepted deviations. |
| Software categories | Software appendix and IP clauses. |
| Subcontractors | Approved subcontractors appendix. |
| Warranty period | SCC and support SLA. |
| Security requirements | Confidentiality, data protection, access control, support obligations. |
| Acceptance tests | Installation and acceptance certificates. |

---

## 13. NSSF ERP Tender as Calibration Sample

The NSSF SPS ERP tender should be used as a calibration sample for the IT STD Engine. It should not be treated as the legal master template. The official PPRA IT STD remains the master source.

### 13.1 What the NSSF tender confirms

The NSSF tender confirms the need for the following engine capabilities:

1. Tender identity generation.
2. TDS-style parameter capture.
3. Professional indemnity or tender security configuration.
4. JV member limit configuration.
5. Alternative tender control.
6. Tender validity period configuration.
7. Physical submission and tender opening configuration.
8. Mandatory requirements checklist.
9. Technical qualification criteria.
10. Technical scoring model.
11. Structured requirements and compliance matrix.
12. Phased implementation model.
13. Module-based technical requirements.
14. Integration requirements.
15. Documentation, training, testing, acceptance, support, warranty, and SLA requirements.
16. Schedule of requirements.
17. Price schedule of requirements.
18. SCC payment milestone configuration.
19. IP and software escrow treatment.
20. Contract forms.

### 13.2 Example NSSF configuration seed

The NSSF tender can be converted into a seed tender instance for testing.

| Field | Seed value |
|---|---|
| Template family | IT STD. |
| Tender subject | ERP system. |
| Procuring entity | National Social Security Fund Staff Pension Scheme. |
| Tender number | NSSFSPS/ICT/ERP/001/2025-2026. |
| Procurement method | Open National Competitive Tendering. |
| Currency | Kenya Shillings. |
| Tender validity | 154 days. |
| Submission mode | Physical submission; electronic tenders not permitted. |
| Bid security / security substitute | Professional Indemnity cover of KES 500,000. |
| Maximum JV members | 3. |
| Alternative tenders | Not permitted. |
| Implementation structure | Two financial-year phases. |
| Technical evaluation | 100 points; 75-point pass mark. |
| Main modules | Pension Administration, Financial Management, HR and Payroll, Procurement, CRM, E-Board, EDMS, Member Self-Service, BI, Liveness Certification. |
| Contract security | Performance Security at 10 percent of Contract Price. |
| Warranty | 12 months per phase from acceptance. |
| SCC emphasis | Payment milestones, IP/source code transfer or escrow, SLA, subcontracting approval. |

### 13.3 Caution from NSSF sample

The NSSF tender contains product-specific requirements around Microsoft Dynamics 365 Business Central and Microsoft partner authorization. The engine should allow this only through a governed proprietary/platform-specific requirement pathway.

The tender also uses a Professional Indemnity cover where the standard IT STD generally expects security and guarantee concepts to be configured carefully. The engine should therefore model this area generically as `Tender Security / Tender-Securing Declaration / Professional Indemnity / Other Security Instrument`, with controlled applicability rules and approval.

---

## 14. Governance and Approval Design

### 14.1 STD administration roles

| Role | Authority |
|---|---|
| STD System Administrator | Technical administration only; cannot approve legal template content alone. |
| STD Template Author | Creates draft template structures and mappings. |
| Procurement Policy Reviewer | Reviews compliance with procurement process and PPRA STD structure. |
| Legal Reviewer | Reviews locked legal text, modification rules, SCC/TDS boundaries, contract forms. |
| Technical Domain Reviewer | Reviews domain-specific schemas, such as IT requirements and price schedules. |
| Approver | Approves template version for activation. |
| Auditor | Read-only access to source, versions, approvals, usage, generated outputs, and addenda. |

### 14.2 Tender configuration roles

| Role | Authority |
|---|---|
| Procurement Officer | Configures allowed tender parameters and requirements. |
| Technical Officer | Drafts technical requirements, implementation schedule, system inventory, and acceptance tests. |
| Procurement Reviewer | Reviews TDS, evaluation, forms, schedule, and tender readiness. |
| Legal Reviewer | Reviews SCC, contract carry-forward, and exceptions. |
| Accounting / Finance Reviewer | Reviews price schedule, budget, payment milestones, securities, taxes. |
| Approving Authority | Approves final generated tender package for publication. |
| Auditor | Read-only access to tender configuration, validation findings, publication hash, and addenda. |

### 14.3 Approval gates

| Gate | Required checks |
|---|---|
| Template structuring complete | Sections, clauses, parameters, forms, rules, render blocks, and source trace exist. |
| Template review complete | Locked text verified, configurable areas verified, domain schemas verified. |
| Template approval | Smoke tests pass, approval trail complete, version hash generated. |
| Tender configuration complete | Mandatory values complete; requirements valid; price schedule linked; evaluation schema complete. |
| Tender review | Procurement, technical, legal, and finance review findings cleared. |
| Publication | Rendered bundle generated, output hash stored, publication version locked. |
| Addendum | Affected outputs identified, revised bundle generated, addendum hash stored. |

---

## 15. Rendering Model

### 15.1 Rendering principle

Rendering must be deterministic. The same STD version and same configuration values must always produce the same tender output.

### 15.2 Render block structure

Each render block should include:

| Field | Purpose |
|---|---|
| `render_block_id` | Stable ID. |
| `section_id` | Section rendered by block. |
| `block_type` | Locked text, parameterized text, table, form, requirement matrix, price schedule, attachment reference, generated summary. |
| `source_object_type` | Clause, parameter, form, requirement, price line, schedule, contract output. |
| `source_object_id` | Linked object. |
| `render_order` | Order within section. |
| `visibility_rule_id` | Conditional rendering rule. |
| `required_for_publication` | Whether missing block is a hard blocker. |
| `output_formats` | HTML, PDF, DOCX, supplier portal form, evaluation form. |
| `hash_inclusion` | Whether included in generated output hash. |

### 15.3 Render outputs

The engine should generate:

1. Human-readable tender document.
2. Supplier response forms.
3. Supplier portal schema.
4. Evaluation workbook/schema.
5. Contract formation documents.
6. Publication hash summary.
7. Addendum impact summary.

---

## 16. Addendum and Supersession Model

Post-publication changes cannot overwrite the published tender bundle.

### 16.1 Addendum object

| Field | Purpose |
|---|---|
| `addendum_id` | Stable ID. |
| `tender_id` | Tender affected. |
| `published_bundle_id` | Original bundle. |
| `change_reason` | Explanation. |
| `requested_by` | User. |
| `approved_by` | Approver. |
| `affected_sections` | Sections changed. |
| `affected_requirements` | Requirement rows changed. |
| `affected_forms` | Supplier response forms changed. |
| `affected_price_schedules` | Price lines changed. |
| `affected_evaluation_criteria` | Evaluation impact. |
| `deadline_extension_required` | Yes/no. |
| `supplier_notification_required` | Yes/no. |
| `new_bundle_hash` | Hash of revised output. |
| `supersedes_bundle_id` | Previous bundle. |

### 16.2 Addendum validation

The system should block publication of an addendum if:

1. Required approvals are missing.
2. The change affects supplier response requirements but no supplier notification is prepared.
3. The change affects evaluation criteria after submissions have opened, unless handled by an authorized cancellation/reissue path.
4. The change affects price schedules but the supplier price form is not regenerated.
5. The change affects implementation schedule or acceptance requirements but contract carry-forward is not updated.

---

## 17. Implementation Roadmap

### Phase 0 - Confirm production design

Deliverables:

1. Approved STD Engine meta-model.
2. Approved mutability taxonomy.
3. Approved source traceability standard.
4. Approved lifecycle and approval workflow.
5. Approved import/export package format.
6. Approved domain-extension mechanism.

Exit condition:

> The team agrees that the engine is generalized and will not be hard-coded for IT only.

### Phase 1 - Build STD Engine foundation

Deliverables:

1. Template family/version records.
2. Source document record and hash storage.
3. Section and clause model.
4. Parameter and option model.
5. Rule model.
6. Form schema model.
7. Render block model.
8. Template lifecycle workflow.
9. Approval event log.
10. Usage tracking.
11. Smoke test runner.

Exit condition:

> The system can import a template package into Draft, review it, approve it, activate it, and prevent edits after activation.

### Phase 2 - Implement IT domain profile

Deliverables:

1. IT requirement schema.
2. IT system inventory model.
3. IT implementation schedule model.
4. IT price schedule model.
5. IT conformance matrix model.
6. IT software/IP model.
7. IT acceptance test model.
8. IT support/SLA model.
9. IT contract appendix model.

Exit condition:

> The system can represent the official IT STD structure without relying on a Word document as the source of runtime behavior.

### Phase 3 - Digitize official IT STD

Deliverables:

1. Full section map.
2. Locked ITT and GCC clauses.
3. TDS parameter schema.
4. SCC parameter schema.
5. Evaluation and qualification schema.
6. Tendering form schemas.
7. Price schedule schemas.
8. Requirements composer schema.
9. Implementation schedule schema.
10. System inventory schema.
11. Contract forms and appendices.
12. Render blocks.
13. Smoke tests.
14. Review and approval package.

Exit condition:

> `KE-PPRA-IT-2022-04` is approved and active as the first full STD Engine template.

### Phase 4 - Build IT tender configuration wizard

Wizard tabs:

1. Tender identity.
2. Procurement method and participation.
3. Submission, clarification, and opening details.
4. Securities and guarantees.
5. Lots, alternatives, preferences, and reservations.
6. TDS values.
7. Requirements of the Information System.
8. Technical requirements.
9. Implementation schedule.
10. System inventory.
11. Price schedule setup.
12. Evaluation and qualification criteria.
13. SCC and contract parameters.
14. Forms and evidence.
15. Validation findings.
16. Preview.
17. Approval and publication.

Exit condition:

> A procurement officer can configure an IT tender without touching the underlying template, JSON, Word, or PDF.

### Phase 5 - Supplier response and evaluation integration

Deliverables:

1. Supplier portal form generation.
2. Supplier eligibility forms.
3. Technical conformance matrix.
4. Price schedule response forms.
5. Evidence upload requirements.
6. Preliminary evaluation checklist.
7. Technical scoring workflow.
8. Financial comparison workflow.
9. Evaluation report data model.
10. Award recommendation support.

Exit condition:

> Evaluation cannot drift from the published tender document.

### Phase 6 - Contract formation integration

Deliverables:

1. Notification of Intention to Award.
2. Letter of Award.
3. Contract Agreement.
4. SCC carry-forward.
5. Software/IP appendices.
6. Approved subcontractors appendix.
7. Revised price schedules.
8. Acceptance certificates.
9. Change order forms.
10. Beneficial ownership forms.

Exit condition:

> Awarded tender data flows into contract formation without manual re-keying or legal drift.

### Phase 7 - NSSF sample round-trip test

Deliverables:

1. NSSF ERP seed tender configuration.
2. Requirements imported as structured requirement groups.
3. Compliance matrix generated.
4. Price schedule generated.
5. Evaluation schema generated.
6. SCC payment milestones and IP clauses configured.
7. Rendered tender preview generated.
8. Validation findings documented.

Exit condition:

> The system can reproduce a tender materially equivalent to the NSSF ERP tender using the IT STD Engine, while flagging governed exceptions.

---

## 18. Smoke Contracts

The IT STD implementation should not be accepted until the following smoke contracts pass.

| Smoke contract | Expected result |
|---|---|
| Active template immutability | Active template cannot be edited directly. |
| Locked ITT/GCC protection | Ordinary user cannot modify locked ITT or GCC text. |
| TDS completion | Missing mandatory TDS fields block publication. |
| SCC completion | Missing mandatory SCC values block publication. |
| Requirement conformance generation | Each mandatory requirement generates supplier compliance fields. |
| Requirement-price linkage | Mandatory priced deliverables require price schedule lines. |
| Schedule-inventory-price linkage | Implementation milestones link to inventory and price rows where required. |
| Evaluation generation | Published evaluation criteria generate evaluation workflow. |
| Technical pass threshold | Technical pass mark is enforced before financial evaluation. |
| Professional indemnity/security rule | Selected security instrument drives required bidder evidence. |
| Platform-specific requirement governance | Proprietary/platform-specific requirement requires justification and approval. |
| Publication hash | Published output hash is generated and immutable. |
| Addendum impact | Change to a requirement identifies affected supplier forms, evaluation, and render outputs. |
| Contract carry-forward | Accepted price, schedule, warranty, support, IP, and software data carry into contract outputs. |
| Superseded template usage | Existing tenders retain old STD version after a new version is activated. |

---

## 19. Immediate Next Work Products

The recommended next artifacts are:

1. STD Engine Meta-Model PRD.
2. STD Engine Domain Model Tables.
3. STD Governance and Approval Workflow Specification.
4. IT STD Section-by-Section Digitization Map.
5. IT STD Field Dictionary.
6. IT STD Rule Dictionary.
7. IT STD Form Schema Inventory.
8. IT Requirements Composer Specification.
9. IT Price Schedule and System Inventory Specification.
10. IT Evaluation Schema Specification.
11. IT Contract Formation Schema Specification.
12. NSSF ERP Sample Tender Mapping and Gap Analysis.
13. Cursor Implementation Pack for Phase 1.

The correct sequence is:

```text
Meta-model
 -> Governance
 -> IT STD digitization map
 -> IT package schema
 -> IT package build
 -> Wizard
 -> Supplier response
 -> Evaluation
 -> Contract formation
 -> Addendum governance
```

Do not start by building the wizard. If the underlying STD package, rule model, requirement schema, and render model are not correct, the UI will hard-code bad assumptions.

---

## 20. Design Decisions to Lock Now

The team should decide the following before implementation begins:

1. Whether the official source document is stored only as evidence or also as a downloadable source reference.
2. Whether template import is manual-only at first or supports semi-automated extraction.
3. Whether render output must be DOCX, PDF, HTML, or all three in Phase 1.
4. Whether the first supplier response implementation is portal-native only or also supports downloadable forms.
5. Whether NSSF ERP is used as a formal test fixture.
6. Whether the system will allow platform-specific IT requirements, and what approval is required.
7. Whether professional indemnity is modeled as a security instrument under the same family as tender security, or as a separate evidence requirement.
8. Whether technical scoring criteria are always visible to bidders, and how scoring guidance is handled.
9. Whether addendum governance is implemented in Phase 1 or Phase 2. Recommendation: implement at least the data model and blockers in Phase 1.
10. Whether contract formation is implemented immediately after tender publication or after evaluation integration. Recommendation: design the data model now, implement workflow after evaluation.

---

## 21. Final Recommendation

Proceed with the Information Technology STD as the first full production STD, but build it through a generalized STD Engine.

The production approach should be:

1. Normalize the STD into database-backed template records.
2. Preserve JSON as an import/export package format.
3. Add strict source traceability.
4. Enforce mutability in the application layer and database layer.
5. Add governance and approvals before activation.
6. Treat IT requirements, implementation schedule, system inventory, price schedule, evaluation, and contract outputs as native structured data.
7. Use the NSSF ERP tender as a real-world calibration and smoke-test fixture.
8. Flag and govern platform-specific requirements rather than silently allowing them.
9. Generate supplier response, evaluation, and contract outputs from the same published STD configuration.
10. Treat addenda and supersession as core features, not later enhancements.

The engine will then be able to support multiple STDs without rebuilding the architecture for each document type.

