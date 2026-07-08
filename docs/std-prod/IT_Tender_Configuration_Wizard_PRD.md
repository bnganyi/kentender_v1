# IT Tender Configuration Wizard PRD

## Document Control

| Field | Value |
|---|---|
| Document Title | IT Tender Configuration Wizard PRD |
| Project | KenTender e-Procurement System |
| Module Family | STD Engine / Tender Management Integration |
| Primary STD Target | Standard Tender Document for Procurement of Information Technology |
| Master STD Package | `KE-PPRA-IT-2022-04` |
| Calibration Fixture | NSSF SPS ERP System Tender, Ref. `NSSFSPS/ICT/ERP/001/2025-2026` |
| Status | Draft for design review |
| Activation Status | Not implementation-authorized until domain model, governance model, and smoke contracts are reviewed |
| Intended Audience | Product owner, procurement domain experts, legal reviewers, architects, backend engineers, frontend engineers, QA, audit/compliance team |

---

## 1. Executive Summary

The IT Tender Configuration Wizard is the controlled tender-preparation interface through which a Procuring Entity creates a tender-specific instance from an active Standard Tender Document package.

The wizard must not be a free-form document editor. It must be a policy-bound configuration surface generated from the STD Engine. It must allow authorized users to configure only the fields, sections, forms, criteria, schedules, requirements, and contract parameters that the applicable STD permits them to configure.

For the first implementation, the wizard will support the Standard Tender Document for Procurement of Information Technology. However, the architecture must remain STD-family agnostic so the same engine can later support Works, Goods, Non-Consulting Services, Consulting Services, Framework Agreements, Restricted Tendering, RFQ, RFP, and other standard documents.

The IT STD is a good first full implementation because it contains a broad but manageable set of structures: TDS, evaluation criteria, tendering forms, technical requirements, implementation schedule, system inventory tables, price schedules, SCC, contract forms, acceptance certificates, and change order forms.

The NSSF ERP tender is used only as a calibration fixture to confirm that a real ERP procurement can be represented by the generalized IT STD model. It must not be used as the legal master template.

---

## 2. Product Objective

The objective is to provide a guided, auditable, legally controlled wizard that allows a Procuring Entity to configure, validate, approve, generate, and publish an IT tender document from an active STD package.

The wizard must produce structured outputs for:

1. Tender advertisement and invitation data.
2. Tender Data Sheet values.
3. Eligibility, qualification, and evaluation criteria.
4. Tendering forms and bidder response requirements.
5. Price schedule schemas and line items.
6. Functional, architectural, performance, service, technology, implementation, and inventory requirements.
7. Special Conditions of Contract.
8. Contract carry-forward data.
9. Generated tender document previews.
10. Supplier portal submission schema.
11. Evaluation workspace schema.
12. Contract-formation handoff schema.
13. Addendum impact analysis.
14. Full audit, validation, source traceability, and hash evidence.

---

## 3. Core Design Position

The wizard is not the source of law or template authority.

The authoritative source hierarchy is:

1. Official PPRA STD source document.
2. Approved active STD package version in the STD Engine.
3. Tender-specific STD instance created from the active package.
4. Generated tender artifact bundle.
5. Published tender record.
6. Addendum records, if any.
7. Evaluation and contract records generated from the published artifact bundle.

The wizard must never allow a tender user to bypass or silently override the active STD package.

---

## 4. Generalized Engine Principle

Although this PRD targets the IT STD wizard, the implementation must use a generalized wizard framework.

The UI must be generated from these engine concepts:

| Engine Concept | Wizard Use |
|---|---|
| STD Template Version | Determines available sections, steps, forms, fields, rules, and renderers |
| Section Mutability | Determines whether a section is locked, configurable, generated, or PE-authored |
| Parameter Dictionary | Generates structured input fields |
| Rule Dictionary | Generates validations, warnings, calculations, dependencies, and activation logic |
| Form Schema | Generates bidder form requirements and supplier submission schemas |
| Requirement Schema | Generates structured requirements composer screens |
| Price Schedule Schema | Generates pricing setup and supplier pricing tables |
| Evaluation Schema | Generates evaluation setup and evaluator workspace structure |
| SCC Schema | Generates contract-specific configuration fields |
| Render Blocks | Generates previews and final tender document bundles |
| Workflow Bindings | Determines review, approval, and publication gates |

No IT-specific behavior should be hard-coded in the wizard shell. IT-specific behavior must come from the active IT STD package.

---

## 5. In Scope

The wizard module must support:

1. Creation of a tender STD instance from an active STD package.
2. Step-by-step configuration of tender-specific STD values.
3. Controlled editing of configurable sections only.
4. Structured requirements authoring for IT procurement.
5. Structured price schedule setup.
6. Structured evaluation criteria setup within STD-permitted boundaries.
7. Structured SCC configuration.
8. Evidence and form requirement configuration where allowed.
9. Validation of all mandatory fields, rules, dependencies, and policy constraints.
10. Draft preview generation.
11. Review submission and approval workflow.
12. Binding of approved configuration to a Tender Management record.
13. Generation of immutable tender artifact bundle at publication.
14. Supplier submission schema generation.
15. Evaluation schema generation.
16. Contract carry-forward schema generation.
17. Addendum impact detection after publication.
18. Full audit trail for all configuration changes.
19. Support for calibration using the NSSF ERP tender.

---

## 6. Out of Scope

The wizard module must not directly implement:

1. Master STD package editing.
2. PPRA-level STD approval workflow.
3. Supplier submission screens, except through generated schemas.
4. Evaluation committee scoring screens, except through generated schemas.
5. Contract execution management.
6. Direct editing of locked ITT or GCC text.
7. Upload-only tender document generation as a substitute for structured configuration.
8. Legal activation of an incomplete STD package.
9. AI-based automatic legal modification of clauses.
10. Vendor-specific hard-coding, including Microsoft Dynamics-specific logic, except when entered as tender-specific requirements.

---

## 7. Primary Users and Roles

| Role | Description | Primary Capabilities |
|---|---|---|
| Procurement Officer | Prepares tender configuration | Create draft, enter TDS values, configure requirements, run validations, generate preview |
| Procurement Manager | Supervises procurement preparation | Review, request changes, approve for legal/procurement review |
| Technical Owner | Provides subject-matter requirements | Draft functional, technical, performance, integration, implementation, and support requirements |
| ICT Reviewer | Reviews technical quality and vendor-neutrality | Review IT requirements, flag over-specific or non-neutral specifications |
| Legal Reviewer | Reviews contract and compliance implications | Review SCC, IP, liability, dispute, acceptance, warranty, and contract carry-forward fields |
| Finance/Budget Reviewer | Reviews estimate, payment, price schedule, and security values | Confirm budget availability, pricing structures, security amounts, payment milestones |
| Approving Authority | Authorizes tender configuration for publication | Approve final configuration and generated bundle |
| Tender Publisher | Publishes approved tender | Publish immutable tender artifact bundle |
| Auditor | Reviews evidence and history | Read audit trail, hashes, validation findings, approvals, and generated artifacts |
| System Administrator | Manages technical configuration | Configure system roles, not legal template content |
| STD Administrator | Maintains master STD packages | Not a normal wizard user; provides active package used by wizard |

---

## 8. Required Governance Check Before Implementation

Approval and state-transition design is mandatory and cannot be deferred.

Before implementation begins, the following must be confirmed:

1. Every wizard state is defined.
2. Every transition has an authorized role.
3. Every transition has guard conditions.
4. Every approval action creates an immutable audit event.
5. Every rejected review creates a required change reason.
6. A published generated bundle cannot be edited.
7. Post-publication changes require addendum workflow.
8. Addendum workflow identifies affected sections, forms, dates, supplier obligations, evaluation criteria, and contract carry-forward outputs.
9. Tender instances remain bound to the exact STD package version used at publication.
10. Superseding the master STD package does not alter already published tenders.

No domain modeling or UI implementation should proceed until this governance model is approved.

---

## 9. Wizard Lifecycle States

| State | Description | Editable | Primary Owner |
|---|---|---:|---|
| `NOT_STARTED` | Tender exists but no STD instance has been created | No | Procurement Officer |
| `INSTANCE_CREATED` | Active STD package has been selected and instance created | Yes | Procurement Officer |
| `IN_CONFIGURATION` | User is actively configuring tender fields | Yes | Procurement Officer / Technical Owner |
| `VALIDATION_FAILED` | One or more blocking validations failed | Yes | Procurement Officer |
| `READY_FOR_INTERNAL_REVIEW` | Required fields complete and blocking validations cleared | Limited | Procurement Officer |
| `PROCUREMENT_REVIEW` | Procurement manager review in progress | No, except returned changes | Procurement Manager |
| `TECHNICAL_REVIEW` | Technical requirements review in progress | No, except returned changes | ICT Reviewer / Technical Owner |
| `LEGAL_REVIEW` | SCC, contract, IP, acceptance, liability, and compliance review in progress | No, except returned changes | Legal Reviewer |
| `FINANCE_REVIEW` | Budget, price schedule, payment, security, and estimate review in progress | No, except returned changes | Finance Reviewer |
| `RETURNED_FOR_CORRECTION` | Reviewer returned configuration with comments | Yes, scoped to returned items | Procurement Officer |
| `APPROVED_FOR_TENDER_CREATION` | Configuration approved for binding to tender | No | Approving Authority |
| `BOUND_TO_TENDER` | Configuration is linked to Tender Management tender record | No, except controlled pre-publication amendment |
| `PRE_PUBLICATION_FINAL_CHECK` | Final validation and render verification before publication | No | Tender Publisher |
| `PUBLISHED` | Tender artifact bundle has been published and hashed | No | Tender Publisher |
| `ADDENDUM_REQUIRED` | Change requested after publication | No direct edit | Procurement Manager |
| `ADDENDUM_IN_CONFIGURATION` | Addendum is being configured | Yes, addendum scope only | Procurement Officer |
| `ADDENDUM_PUBLISHED` | Addendum bundle published and linked to original tender | No | Tender Publisher |
| `CANCELLED` | Tender STD instance cancelled before publication | No | Procurement Manager |
| `ARCHIVED` | Instance retained for record after closure | No | System |

---

## 10. State Transition Rules

| From State | To State | Actor | Guard Conditions | Audit Event |
|---|---|---|---|---|
| `NOT_STARTED` | `INSTANCE_CREATED` | Procurement Officer | Active STD package selected; tender method compatible | `STD_INSTANCE_CREATED` |
| `INSTANCE_CREATED` | `IN_CONFIGURATION` | Procurement Officer | User has edit permission | `WIZARD_CONFIGURATION_STARTED` |
| `IN_CONFIGURATION` | `VALIDATION_FAILED` | System | Blocking validation exists | `WIZARD_VALIDATION_FAILED` |
| `VALIDATION_FAILED` | `IN_CONFIGURATION` | Procurement Officer | User edits affected fields | `WIZARD_CORRECTION_STARTED` |
| `IN_CONFIGURATION` | `READY_FOR_INTERNAL_REVIEW` | Procurement Officer | Mandatory fields complete; no blocking findings | `WIZARD_SUBMITTED_FOR_REVIEW` |
| `READY_FOR_INTERNAL_REVIEW` | `PROCUREMENT_REVIEW` | Procurement Manager | Review queue accepted | `PROCUREMENT_REVIEW_STARTED` |
| `PROCUREMENT_REVIEW` | `RETURNED_FOR_CORRECTION` | Procurement Manager | Return reason entered | `PROCUREMENT_REVIEW_RETURNED` |
| `PROCUREMENT_REVIEW` | `TECHNICAL_REVIEW` | Procurement Manager | Procurement checks passed | `PROCUREMENT_REVIEW_PASSED` |
| `TECHNICAL_REVIEW` | `RETURNED_FOR_CORRECTION` | ICT Reviewer | Return reason entered | `TECHNICAL_REVIEW_RETURNED` |
| `TECHNICAL_REVIEW` | `LEGAL_REVIEW` | ICT Reviewer | Technical checks passed | `TECHNICAL_REVIEW_PASSED` |
| `LEGAL_REVIEW` | `RETURNED_FOR_CORRECTION` | Legal Reviewer | Return reason entered | `LEGAL_REVIEW_RETURNED` |
| `LEGAL_REVIEW` | `FINANCE_REVIEW` | Legal Reviewer | Legal checks passed | `LEGAL_REVIEW_PASSED` |
| `FINANCE_REVIEW` | `RETURNED_FOR_CORRECTION` | Finance Reviewer | Return reason entered | `FINANCE_REVIEW_RETURNED` |
| `FINANCE_REVIEW` | `APPROVED_FOR_TENDER_CREATION` | Approving Authority | All reviews passed; final approval reason entered | `WIZARD_APPROVED` |
| `APPROVED_FOR_TENDER_CREATION` | `BOUND_TO_TENDER` | Procurement Officer / System | Tender record exists; version binding confirmed | `STD_INSTANCE_BOUND_TO_TENDER` |
| `BOUND_TO_TENDER` | `PRE_PUBLICATION_FINAL_CHECK` | Tender Publisher | Preview generated; checksums available | `PRE_PUBLICATION_CHECK_STARTED` |
| `PRE_PUBLICATION_FINAL_CHECK` | `PUBLISHED` | Tender Publisher | Final validations pass; generated bundle hash created | `TENDER_STD_BUNDLE_PUBLISHED` |
| `PUBLISHED` | `ADDENDUM_REQUIRED` | Procurement Manager | Change request logged; impact analysis required | `ADDENDUM_REQUIRED_FLAGGED` |
| `ADDENDUM_REQUIRED` | `ADDENDUM_IN_CONFIGURATION` | Procurement Officer | Addendum scope approved | `ADDENDUM_CONFIGURATION_STARTED` |
| `ADDENDUM_IN_CONFIGURATION` | `ADDENDUM_PUBLISHED` | Tender Publisher | Addendum validations pass; addendum bundle hash created | `ADDENDUM_PUBLISHED` |
| Any pre-publication state | `CANCELLED` | Procurement Manager | Cancellation reason entered | `WIZARD_INSTANCE_CANCELLED` |
| Closed state | `ARCHIVED` | System | Retention rules satisfied | `WIZARD_INSTANCE_ARCHIVED` |

---

## 11. Wizard Architecture

The wizard must be implemented as a generic wizard runtime with STD-specific configuration.

### 11.1 Generic Runtime Components

| Component | Responsibility |
|---|---|
| Wizard Shell | Loads steps, routes, permissions, progress, and validation state |
| Step Registry | Defines which screens appear for the selected STD package |
| Field Renderer | Renders input fields from parameter and form schemas |
| Requirement Composer | Renders structured requirement authoring screens |
| Table Builder | Renders price schedules, system inventory, milestones, evaluation criteria, and compliance matrices |
| Validation Engine Client | Executes or requests validation against STD rules |
| Preview Generator Client | Requests generated document previews from render service |
| Review Workflow Client | Submits, returns, approves, and tracks review states |
| Audit Client | Records user actions and displays audit history |
| Addendum Client | Computes post-publication impact and controls addendum changes |

### 11.2 STD-Specific Plug-in Data

The IT STD package must supply:

1. Wizard step definitions.
2. Field groups.
3. Parameter bindings.
4. Section bindings.
5. Rule bindings.
6. Render block bindings.
7. Form activation rules.
8. Requirement category definitions.
9. Price schedule templates.
10. Evaluation criteria templates.
11. Contract carry-forward mappings.
12. Smoke contracts.

---

## 12. IT Wizard Steps

The first IT STD implementation must include the following wizard steps.

| Step No. | Step Name | Purpose | Required for Publication |
|---:|---|---|---:|
| 1 | STD Version Confirmation | Confirm active STD version and source identity | Yes |
| 2 | Tender Identity | Capture tender name, number, PE identity, description, lots | Yes |
| 3 | Procurement Method and Participation | Configure national/international, reservations, margin of preference, JV, alternatives | Yes |
| 4 | Dates, Clarifications, and Meetings | Configure submission deadline, opening, clarification deadline, pre-tender meeting | Yes |
| 5 | Tender Security / Professional Indemnity | Configure required security or indemnity requirements | Yes |
| 6 | Tender Submission Rules | Configure copies, serialization, electronic submission, addresses | Yes |
| 7 | IT Scope and Objectives | Capture background, objectives, expected outcomes, project tasks | Yes |
| 8 | IT Requirements Composer | Build functional, architectural, performance, service, technology, integration, data, training, support, and acceptance requirements | Yes |
| 9 | Implementation Schedule | Configure phases, milestones, acceptance events, dependencies, locations | Yes |
| 10 | System Inventory | Configure supply/install and recurrent inventory items | Yes if inventory required |
| 11 | Price Schedule Setup | Configure pricing structures and recurrent cost periods | Yes |
| 12 | Evaluation and Qualification | Configure criteria within STD-permitted limits | Yes |
| 13 | Tendering Forms and Evidence | Activate forms and evidence requirements | Yes |
| 14 | SCC and Contract Parameters | Configure contract-specific parameters, IP, payments, securities, acceptance, warranty, dispute | Yes |
| 15 | Generated Supplier Submission Schema | Preview what bidders must submit | Yes |
| 16 | Generated Evaluation Workspace Schema | Preview evaluation structure | Yes |
| 17 | Contract Carry-Forward Preview | Preview award and contract outputs | Yes |
| 18 | Validation Dashboard | Display blockers, warnings, informational findings | Yes |
| 19 | Tender Document Preview | Generate and review rendered draft | Yes |
| 20 | Review and Approval Submission | Submit package for workflow approval | Yes |
| 21 | Publication Readiness | Final pre-publication checks and bundle hashing | Yes |

---

## 13. Step-Level Requirements

### 13.1 STD Version Confirmation

The system must display:

1. STD family.
2. STD version.
3. Activation status.
4. Source document identity.
5. Source document hash.
6. Package hash.
7. Effective date.
8. Whether the STD version is still active.
9. Whether the version has been superseded.
10. Usage constraints.

The user must confirm that the selected STD is appropriate for the procurement before proceeding.

A tender instance must store the exact STD package version ID. The instance must not float to a newer STD version automatically.

### 13.2 Tender Identity

The wizard must capture:

1. Procuring Entity name.
2. Procuring Entity logo reference.
3. Procuring Entity address.
4. Procuring Entity email.
5. Tender name.
6. Tender number.
7. Contract name and description.
8. Procurement plan reference.
9. Budget reference.
10. Estimated cost, where permitted.
11. Lot structure.
12. Procurement category.
13. Responsible officer.
14. Review owners.
15. Tender document language.

The system must validate uniqueness of tender number within the Procuring Entity.

### 13.3 Procurement Method and Participation

The wizard must support:

1. Open national tendering.
2. Open international tendering.
3. Restricted tendering where legally enabled by the broader procurement module.
4. Prequalification flag.
5. Reservations flag.
6. Eligible reserved group, if applicable.
7. Margin of preference flag.
8. Alternative tenders allowed/not allowed.
9. Multiple lots allowed/not allowed.
10. Maximum JV members.
11. Foreign tenderer local sourcing rule.
12. Country eligibility restrictions.

The system must prevent invalid combinations, such as enabling margin of preference where the package rules or procurement method do not permit it.

### 13.4 Dates, Clarifications, and Meetings

The wizard must capture:

1. Tender issue date.
2. Clarification request deadline.
3. Clarification response deadline.
4. Pre-tender meeting flag.
5. Pre-tender meeting date/time.
6. Pre-tender meeting location or virtual link.
7. Site visit flag if applicable.
8. Tender submission deadline.
9. Tender opening date/time.
10. Tender opening venue.
11. Tender validity period.
12. Standstill period parameters where applicable.

The rule engine must validate date order and minimum notice periods according to package rules and system policy.

### 13.5 Tender Security / Professional Indemnity

The IT wizard must support both the official STD model and real tender calibration scenarios.

It must capture:

1. Whether tender security, tender-securing declaration, professional indemnity, or another permitted instrument is required.
2. Security amount.
3. Currency.
4. Validity period.
5. Permitted issuer types.
6. Required original/copy rules.
7. Forfeiture conditions.
8. Whether failure is mandatory non-responsiveness.

The system must flag non-standard substitutions where a real tender uses professional indemnity in place of tender security, unless the active STD package permits that pattern.

### 13.6 Tender Submission Rules

The wizard must capture:

1. Physical submission address.
2. Tender box location.
3. Opening venue.
4. Number of originals.
5. Number of copies.
6. Electronic tender permitted flag.
7. Serialization requirement.
8. Envelope marking rules.
9. Late tender handling.
10. Contact for clarifications.
11. Document download/registration process.

The system must generate these into the Invitation to Tender, TDS, and supplier submission instructions.

### 13.7 IT Scope and Objectives

The wizard must support PE-authored background and objective content with review controls.

It must capture:

1. Institutional background.
2. Current problem statement.
3. Procurement objective.
4. Expected outcomes.
5. Specific tasks for successful bidder.
6. Hosting/deployment preference.
7. Key integrations.
8. Data migration scope.
9. Training scope.
10. Support scope.
11. Compliance requirements.
12. Business process re-engineering scope.

The system must distinguish background information from binding supplier obligations.

### 13.8 IT Requirements Composer

The requirements composer must create structured supplier obligations, not loose prose.

It must support requirement categories including:

1. Functional requirements.
2. Architectural requirements.
3. Performance requirements.
4. Security requirements.
5. Integration requirements.
6. Data migration requirements.
7. Reporting and business intelligence requirements.
8. Service specifications.
9. Technology specifications.
10. Training requirements.
11. Documentation requirements.
12. Testing and acceptance requirements.
13. Warranty and support requirements.
14. Regulatory compliance requirements.
15. Accessibility and usability requirements.
16. Hosting and infrastructure requirements.
17. Business continuity and disaster recovery requirements.
18. Change management requirements.
19. Project management requirements.
20. Knowledge transfer requirements.

Each requirement must support:

| Field | Description |
|---|---|
| Requirement ID | Stable unique identifier |
| Category | Requirement category |
| Subcategory | Optional grouping |
| Requirement Text | Supplier obligation text |
| Priority | Mandatory, desirable, optional |
| Compliance Type | Yes/No, narrative, numeric, document evidence, demonstration, test |
| Evaluation Treatment | Pass/fail, scored, informational, contract-only |
| Evidence Required | Yes/No and evidence type |
| Response Required | Yes/No |
| Contract Carry-Forward | Whether requirement becomes contract obligation |
| Acceptance Test Required | Whether requirement requires acceptance test |
| Source/Author | PE author and source basis |
| Review Status | Draft, reviewed, returned, approved |
| Version | Requirement revision number |

The composer must support bulk import from CSV/XLSX in later phases, but initial implementation may use manual structured entry.

### 13.9 Vendor-Neutrality and Over-Specification Review

The wizard must flag potential over-specification where requirements mention:

1. A named vendor.
2. A named product.
3. A named cloud platform.
4. A named implementation partner.
5. Proprietary protocols where alternatives may be possible.
6. Mandatory certifications that may restrict competition.
7. Local references that are too narrow.
8. Sector references that may over-restrict competition.

The system should not automatically prohibit such requirements because some may be justified. It must require justification and review when such terms are used.

For calibration, an ERP tender specifying Microsoft Dynamics 365 Business Central and Azure must be representable, but the wizard must mark this as a vendor-specific configuration requiring justification and review.

### 13.10 Implementation Schedule

The wizard must support:

1. Single-phase implementation.
2. Multi-phase implementation.
3. Milestone names.
4. Milestone descriptions.
5. Deliverables.
6. Planned start.
7. Planned duration.
8. Dependencies.
9. Acceptance criteria.
10. Payment linkage.
11. Warranty start trigger.
12. Responsible party.
13. Location.
14. Contract carry-forward.

For IT procurements, implementation schedule must link to requirements, price schedule, acceptance certificates, and payment milestones.

### 13.11 System Inventory

The wizard must support the official IT STD inventory distinction:

1. Supply and installation cost items.
2. Recurrent cost items.

Each system inventory item must capture:

| Field | Description |
|---|---|
| Item ID | Stable identifier |
| Item Category | Hardware, software, license, service, training, support, hosting, integration, other |
| Description | Item description |
| Quantity | Quantity |
| Unit | Unit of measure |
| Source Requirement ID | Linked requirement if applicable |
| Cost Category | Supply/install or recurrent |
| Delivery Phase | Implementation phase |
| Acceptance Dependency | Acceptance milestone |
| Pricing Required | Whether supplier must price the item |
| Country of Origin Required | Whether country-of-origin data is required |
| Contract Carry-Forward | Whether item appears in contract appendices |

### 13.12 Price Schedule Setup

The wizard must configure pricing structures but suppliers must provide actual bid prices through the supplier portal.

The wizard must define:

1. Whether supply/install pricing is required.
2. Whether recurrent pricing is required.
3. Recurrent cost period count.
4. Currency.
5. Tax handling.
6. VAT display rules.
7. Discount handling.
8. Country-of-origin requirement.
9. Phase-based pricing.
10. Milestone-based payment relationship.
11. Price adjustment allowed/not allowed.
12. Financial evaluation formula.
13. Total evaluated price definition.

The wizard must not allow arbitrary financial evaluation formula changes outside STD-permitted controls.

### 13.13 Evaluation and Qualification

The wizard must generate evaluation criteria from the STD package and permit only controlled configuration.

It must support:

1. Preliminary responsiveness checks.
2. Mandatory eligibility requirements.
3. Technical qualification criteria.
4. Technical scoring criteria.
5. Minimum pass mark.
6. Requirement conformance checks.
7. Personnel requirements.
8. Experience requirements.
9. Financial capacity requirements.
10. Local presence requirements, where justified.
11. Vendor authorization requirements, where justified.
12. Financial evaluation rules.
13. Post-qualification rules.
14. Margin of preference rules, if enabled.
15. Abnormally low/high tender checks.

Each criterion must capture:

| Field | Description |
|---|---|
| Criterion ID | Stable identifier |
| Stage | Preliminary, technical, financial, post-qualification |
| Criterion Text | Evaluation requirement |
| Requirement Type | Mandatory, scored, formula, informational |
| Maximum Points | For scored criteria |
| Minimum Score | For scored or pass/fail blocks |
| Evidence Required | Required supplier evidence |
| Evaluation Owner | Committee role or evaluator type |
| Rule Binding | Validation/scoring rule |
| Source Binding | STD package or tender-specific justified addition |
| Justification Required | Whether deviation justification is needed |

### 13.14 Tendering Forms and Evidence

The wizard must display all forms activated by the package and any tender-specific evidence requirements.

For the IT STD, forms may include:

1. Form of Tender.
2. Confidential Business Questionnaire.
3. Certificate of Independent Tender Determination.
4. Self-Declaration Form.
5. Fraud and Corruption appendix.
6. Price schedule forms.
7. Foreign tenderers 40 percent rule form.
8. Tenderer information form.
9. JV member information form.
10. Historical non-performance and pending litigation form.
11. General experience form.
12. Specific experience form.
13. Current contract commitments form.
14. Financial situation form.
15. Average annual turnover form.
16. Financial resources form.
17. Personnel capability forms.
18. Intellectual property forms.
19. Conformance of information system materials.

The wizard must not treat form activation as a mere checklist. It must generate field-level supplier response schemas.

### 13.15 SCC and Contract Parameters

The wizard must capture contract-specific parameters including:

1. Contract governing law fields where configurable.
2. Contract documents hierarchy where configurable.
3. Payment milestones.
4. Performance security amount and validity.
5. Advance payment security, if applicable.
6. Warranty period.
7. Defect liability period.
8. Operational acceptance rules.
9. Acceptance certificate structure.
10. Intellectual property ownership.
11. Software license categories.
12. Escrow requirements, if applicable.
13. Confidentiality requirements.
14. Insurance requirements.
15. Limitation of liability values where configurable.
16. Dispute resolution/adjudicator fields.
17. Change order procedure configuration.
18. Subcontractor approval controls.
19. Support and SLA parameters.
20. Contract appendix generation rules.

SCC values must carry forward into contract formation after award.

### 13.16 Supplier Submission Schema Preview

The wizard must preview the supplier submission package that will be generated from the tender configuration.

The preview must include:

1. Required forms.
2. Required documents.
3. Technical proposal sections.
4. Compliance matrix.
5. Price schedule tables.
6. Personnel forms.
7. Experience forms.
8. Financial forms.
9. IP forms.
10. Evidence upload requirements.
11. Validation rules suppliers will face.

### 13.17 Evaluation Workspace Preview

The wizard must preview the evaluation workspace that will be generated from the published tender.

The preview must include:

1. Preliminary evaluation checklist.
2. Mandatory requirement pass/fail matrix.
3. Technical scoring matrix.
4. Requirement conformance review table.
5. Personnel scoring table.
6. Financial evaluation table.
7. Post-qualification checks.
8. Lowest evaluated responsive tender output.
9. Evaluation audit events.

### 13.18 Contract Carry-Forward Preview

The wizard must preview the contract fields that will carry forward after award:

1. Contract agreement values.
2. Approved supplier details.
3. Approved subcontractors.
4. Approved system inventory.
5. Approved price schedules.
6. Approved implementation schedule.
7. Software categories.
8. Custom materials.
9. Acceptance certificates.
10. Support and warranty terms.
11. Payment milestones.
12. Securities.
13. Beneficial ownership disclosure requirement.
14. Change order procedure references.

### 13.19 Validation Dashboard

The validation dashboard must group findings by:

1. Blockers.
2. Warnings.
3. Informational notices.
4. Legal review required.
5. Technical review required.
6. Finance review required.
7. Vendor-neutrality review required.
8. Addendum impact warnings.
9. Render preview issues.
10. Source traceability issues.

Each finding must display:

| Field | Description |
|---|---|
| Finding ID | Unique identifier |
| Severity | Blocker, warning, info |
| Step | Wizard step |
| Field/Section | Affected item |
| Message | Human-readable issue |
| Rule ID | Source rule |
| Resolution Guidance | Required correction |
| Overridable | Yes/No |
| Override Role | If overridable |
| Justification Required | Yes/No |

### 13.20 Tender Document Preview

The wizard must generate:

1. Section-level preview.
2. Full tender preview.
3. Supplier submission package preview.
4. Evaluation package preview.
5. Contract carry-forward preview.
6. Diff from previous preview.
7. Render validation report.
8. Preview hash.

The preview must clearly mark draft status until publication.

### 13.21 Review and Approval Submission

Before submission, the wizard must require:

1. No blocking validations.
2. All mandatory fields complete.
3. Review owners assigned.
4. All vendor-specific requirements justified.
5. All non-standard values justified.
6. All generated previews available.
7. All source traceability checks passed or explicitly flagged.
8. Change summary generated.

### 13.22 Publication Readiness

Before publication, the system must confirm:

1. Active STD package version still exists.
2. Tender instance remains bound to the same package version.
3. Final validation passes.
4. Final preview generated.
5. Final artifact bundle created.
6. Bundle hash generated.
7. Approval trail complete.
8. Publication actor authorized.
9. Tender Management record ready.
10. Supplier submission schema generated.
11. Evaluation schema generated.
12. Contract carry-forward schema generated.

---

## 14. Data Objects Required

This PRD depends on the STD Engine Core domain model and adds or uses the following wizard-specific objects.

| Object | Purpose |
|---|---|
| `TenderStdInstance` | Tender-specific binding to one active STD package version |
| `TenderStdWizardStep` | Step state and completion tracking |
| `TenderStdConfigurationValue` | Actual configured values entered by users |
| `TenderStdRequirement` | Tender-specific requirement rows authored through composer |
| `TenderStdImplementationMilestone` | Tender-specific schedule and milestone data |
| `TenderStdSystemInventoryItem` | Tender-specific inventory/cost items |
| `TenderStdEvaluationCriterion` | Tender-specific configured evaluation criterion within permitted schema |
| `TenderStdFormActivation` | Forms activated for the tender |
| `TenderStdEvidenceRequirement` | Evidence required from suppliers |
| `TenderStdValidationFinding` | Validation results for the tender configuration |
| `TenderStdReviewEvent` | Review and approval history |
| `TenderStdPreview` | Generated previews and hashes |
| `TenderStdGeneratedBundle` | Final generated tender artifact bundle |
| `TenderStdSupplierSubmissionSchema` | Generated supplier response schema |
| `TenderStdEvaluationSchema` | Generated evaluation workspace schema |
| `TenderStdContractCarryForward` | Generated contract-formation schema |
| `TenderStdAddendumImpact` | Impact analysis for post-publication changes |
| `TenderStdAuditEvent` | Immutable user/system action log |

---

## 15. Validation Requirements

### 15.1 Validation Categories

| Category | Examples |
|---|---|
| Completeness | Mandatory TDS/SCC fields missing |
| Date Logic | Opening date before submission deadline |
| Security Logic | Invalid amount, currency, instrument, or validity |
| Participation Logic | Reservation and international tender conflict |
| Evaluation Logic | Points do not sum to required total; pass mark missing |
| Requirement Logic | Mandatory requirement lacks supplier response type |
| Price Logic | Recurrent cost period missing; formula mismatch |
| Contract Logic | Payment milestone not linked to acceptance event |
| Vendor-Neutrality | Named vendor/product/cloud without justification |
| Render Logic | Required render block missing |
| Source Traceability | Parameter or clause lacks source anchor |
| Governance Logic | Approval missing; unauthorized transition attempted |
| Addendum Logic | Post-publication change affects supplier obligation but addendum not created |

### 15.2 Severity Levels

| Severity | Meaning | Effect |
|---|---|---|
| `BLOCKER` | Must be resolved before proceeding | Prevents review or publication |
| `WARNING` | Must be reviewed or justified | Does not always block, but requires reviewer attention |
| `INFO` | Informational finding | Does not block |
| `REVIEW_REQUIRED` | Requires role-specific review | Blocks approval until reviewed |

---

## 16. Permission Requirements

| Action | Procurement Officer | Technical Owner | Procurement Manager | ICT Reviewer | Legal Reviewer | Finance Reviewer | Approving Authority | Publisher | Auditor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Create STD instance | Yes | No | Yes | No | No | No | No | No | No |
| Edit TDS values | Yes | No | Limited | No | No | No | No | No | No |
| Edit technical requirements | Yes | Yes | Limited | Limited | No | No | No | No | No |
| Edit price schedule setup | Yes | No | Limited | No | No | Yes | No | No | No |
| Edit SCC values | Yes | No | Limited | No | Limited | Limited | No | No | No |
| Run validation | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Read |
| Generate draft preview | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Read |
| Submit for review | Yes | No | Yes | No | No | No | No | No | No |
| Return for correction | No | No | Yes | Yes | Yes | Yes | No | No | No |
| Approve final configuration | No | No | No | No | No | No | Yes | No | No |
| Publish tender bundle | No | No | No | No | No | No | No | Yes | No |
| View audit trail | Limited | Limited | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Override warning | No | No | Yes | Yes | Yes | Yes | Yes | No | No |
| Override blocker | No | No | No | No | No | No | No | No | No |

---

## 17. Audit and Hash Requirements

The wizard must record immutable audit events for:

1. Instance creation.
2. Package version selection.
3. Field creation/update/delete.
4. Requirement creation/update/delete.
5. Price schedule configuration changes.
6. Evaluation criteria changes.
7. SCC changes.
8. Validation runs.
9. Preview generation.
10. Review submission.
11. Review return.
12. Approval.
13. Binding to tender.
14. Publication.
15. Addendum request.
16. Addendum publication.
17. Cancellation.
18. Archive.

Each audit event must include:

1. Event ID.
2. Actor ID.
3. Role at time of action.
4. Timestamp.
5. Tender STD instance ID.
6. STD package version ID.
7. Affected object type.
8. Affected object ID.
9. Before value hash where applicable.
10. After value hash where applicable.
11. Reason or justification where applicable.
12. IP/session metadata where available.

The final generated bundle must have a bundle hash. Any published addendum must have its own hash and must reference the original published bundle hash.

---

## 18. Integration Requirements

### 18.1 STD Engine Integration

The wizard must consume:

1. Active package metadata.
2. Section definitions.
3. Parameter schemas.
4. Form schemas.
5. Requirement schemas.
6. Rule definitions.
7. Render block definitions.
8. Workflow bindings.
9. Smoke test definitions.

### 18.2 Tender Management Integration

The wizard must provide:

1. Approved tender STD configuration.
2. Generated tender artifact bundle.
3. Tender identity fields.
4. Publication readiness status.
5. Addendum impact results.

### 18.3 Supplier Portal Integration

The wizard must generate:

1. Supplier response schema.
2. Required forms.
3. Required evidence uploads.
4. Compliance matrix.
5. Price schedules.
6. Submission validation rules.

### 18.4 Evaluation Module Integration

The wizard must generate:

1. Preliminary examination checklist.
2. Mandatory requirement matrix.
3. Technical scoring matrix.
4. Requirement conformance table.
5. Financial evaluation formula.
6. Post-qualification checks.
7. Evaluation report structure.

### 18.5 Contract Module Integration

The wizard must generate:

1. Contract agreement carry-forward fields.
2. SCC values.
3. Payment milestones.
4. Performance security requirements.
5. Acceptance certificate definitions.
6. Approved system inventory references.
7. Approved price schedule references.
8. Software/IP appendix fields.
9. Change order procedure fields.

---

## 19. API Requirements

The detailed API contract will be produced in a later API/UI/service contract artifact. At PRD level, the module needs endpoints or service methods for:

1. List active STD packages available for tender creation.
2. Create tender STD instance.
3. Read wizard configuration.
4. Update configuration values.
5. Update requirements.
6. Update implementation schedule.
7. Update system inventory.
8. Update price schedule setup.
9. Update evaluation setup.
10. Update SCC values.
11. Run validation.
12. Generate preview.
13. Submit for review.
14. Return for correction.
15. Approve configuration.
16. Bind to tender.
17. Generate final bundle.
18. Publish bundle.
19. Create addendum impact analysis.
20. Configure addendum.
21. Publish addendum.
22. Read audit trail.

---

## 20. UI Requirements

### 20.1 Global Layout

The wizard UI must include:

1. Header with tender identity and STD package version.
2. Step navigation sidebar.
3. Completion progress.
4. Validation summary.
5. Current state badge.
6. Review comments panel.
7. Source/reference panel where applicable.
8. Preview button.
9. Save draft button.
10. Submit/approve/publish action buttons based on state and permission.

### 20.2 Field Behavior

Fields must support:

1. Required indicators.
2. Help text from package schema.
3. Source references where available.
4. Validation feedback.
5. Conditional visibility.
6. Conditional mandatory status.
7. Controlled values.
8. Justification prompts for non-standard values.
9. Change history.
10. Role-based editability.

### 20.3 Requirement Composer UI

The requirement composer must support:

1. Category tree.
2. Requirement table.
3. Requirement detail drawer.
4. Bulk reorder.
5. Duplicate requirement detection.
6. Vendor-specific flagging.
7. Evidence binding.
8. Evaluation binding.
9. Contract carry-forward toggle.
10. Acceptance test toggle.
11. Review status.
12. Commenting.

### 20.4 Validation Dashboard UI

The validation dashboard must support:

1. Filter by severity.
2. Filter by step.
3. Filter by reviewer role.
4. Jump-to-field action.
5. Export validation report.
6. Mark warning reviewed where authorized.
7. Add justification where authorized.

### 20.5 Preview UI

The preview UI must support:

1. Section navigation.
2. Full document preview.
3. Render warnings.
4. Draft watermark.
5. Diff since last preview.
6. Export draft preview.
7. Preview hash display.

---

## 21. NSSF ERP Calibration Expectations

The NSSF ERP tender must be used to test whether the wizard can represent a real IT tender without corrupting the master STD model.

The calibration must confirm support for:

1. ERP tender identity and invitation data.
2. National competitive tendering.
3. Professional indemnity requirement.
4. Fixed prices in Kenya Shillings.
5. 154-day tender validity.
6. No alternative tenders.
7. Three-member JV cap.
8. Two-phase implementation.
9. ERP module requirements.
10. Microsoft Dynamics-specific requirements with review flags.
11. Azure hosting requirements with review flags.
12. Technical scoring out of 100 points.
13. Minimum technical pass mark.
14. Mandatory requirements.
15. Supplier authorization requirements.
16. Pension-sector experience criteria.
17. Compliance matrix with yes/no/reference columns.
18. Warranty and support terms.
19. Payment milestones linked to phases and acceptance.
20. Performance security.
21. Contract carry-forward of IP, warranty, SLA, acceptance, and support obligations.

The calibration must also identify deviations from the official IT STD pattern, including simplified forms, simplified price schedule, shortened GCC/SCC text, or custom mandatory criteria.

---

## 22. Non-Functional Requirements

| Area | Requirement |
|---|---|
| Security | Role-based access control; no unauthorized edits to locked/generated/published content |
| Auditability | All material changes must be logged with actor, timestamp, before/after hash, and reason where applicable |
| Integrity | Published bundles must be immutable and hash-verifiable |
| Traceability | Fields, rules, render blocks, and forms must trace to STD package records |
| Maintainability | Wizard must be driven by package schemas, not hard-coded for IT only |
| Performance | Validation and preview generation must remain responsive for large requirement matrices |
| Usability | Procurement users must be able to configure a tender without editing JSON |
| Accessibility | UI should support keyboard navigation, readable tables, and exportable previews |
| Reliability | Draft changes must autosave or be recoverable |
| Extensibility | Additional STD families must be supported by adding package definitions, not rewriting wizard core |
| Legal Defensibility | Published tender artifacts must be reproducible from stored configuration, STD version, render templates, and hashes |

---

## 23. Acceptance Criteria

The wizard is acceptable when:

1. A user can create an IT tender STD instance from an active package.
2. The instance is bound to an exact STD package version.
3. Locked ITT and GCC sections cannot be edited.
4. TDS and SCC fields are configurable only through approved parameter schemas.
5. IT requirements are captured as structured obligations.
6. Requirements can be linked to supplier response, evaluation, price, implementation, acceptance, and contract carry-forward.
7. Price schedule setup generates supplier pricing tables.
8. Evaluation setup generates preliminary, technical, financial, and post-qualification structures.
9. Form activation generates field-level supplier submission schema.
10. Validation prevents publication with blockers.
11. Review and approval workflow enforces required gates.
12. Final tender preview can be generated.
13. Published tender bundle is immutable and hash-verifiable.
14. Supplier portal schema can be generated from the published configuration.
15. Evaluation schema can be generated from the published configuration.
16. Contract carry-forward schema can be generated from the published configuration.
17. Post-publication changes require addendum workflow.
18. NSSF ERP tender can be represented as a tender-specific instance with deviation flags.
19. The same wizard runtime can support another STD family through package configuration.

---

## 24. Smoke Contracts

| Smoke ID | Scenario | Expected Result |
|---|---|---|
| `IT-WIZ-SMOKE-001` | Create IT tender STD instance from active package | Instance created and package version locked |
| `IT-WIZ-SMOKE-002` | Attempt to edit locked ITT clause | Edit blocked and audit event recorded |
| `IT-WIZ-SMOKE-003` | Submit incomplete TDS | Blocking validation returned |
| `IT-WIZ-SMOKE-004` | Configure invalid date order | Blocking validation returned |
| `IT-WIZ-SMOKE-005` | Add vendor-specific requirement without justification | Review-required warning returned |
| `IT-WIZ-SMOKE-006` | Configure technical scoring total not equal to expected total | Blocking validation returned |
| `IT-WIZ-SMOKE-007` | Configure payment milestone without acceptance link | Warning or blocker according to rule severity |
| `IT-WIZ-SMOKE-008` | Generate draft preview | Preview generated with draft watermark and hash |
| `IT-WIZ-SMOKE-009` | Submit valid configuration for review | State changes to review workflow |
| `IT-WIZ-SMOKE-010` | Reviewer returns configuration | State changes to returned for correction and reason required |
| `IT-WIZ-SMOKE-011` | Approve and bind configuration to tender | State changes to bound and binding audit event created |
| `IT-WIZ-SMOKE-012` | Publish final bundle | Bundle hash created and content becomes immutable |
| `IT-WIZ-SMOKE-013` | Attempt edit after publication | Edit blocked; addendum required path offered |
| `IT-WIZ-SMOKE-014` | Create addendum for changed submission deadline | Addendum impact identifies invitation, TDS, and supplier instructions |
| `IT-WIZ-SMOKE-015` | Represent NSSF ERP calibration tender | Instance can be configured with deviation warnings and generated schemas |

---

## 25. Major Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Wizard becomes IT-specific and cannot support other STDs | High | Use schema-driven generic runtime |
| Users bypass structured requirements by uploading attachments | High | Allow attachments only as supporting material, not replacement for required structured fields |
| Evaluation criteria drift from tender document | High | Generate evaluation schema directly from published tender configuration |
| Contract terms drift from tender configuration | High | Generate contract carry-forward schema from published configuration |
| Vendor-specific requirements restrict competition without review | High | Flag and require justification/review |
| Published tender changes without addendum | Critical | Enforce immutability and addendum workflow |
| Incomplete STD package used for publication | Critical | Require active package status and validation gates |
| Overly complex UI discourages adoption | Medium | Use step-wise guidance, templates, progressive disclosure, and validation summaries |
| Real tenders use non-standard structures | Medium | Support deviation warnings and controlled custom fields where allowed |

---

## 26. Open Questions for Design Review

1. Should legal review always be mandatory for IT tenders, or only where SCC/IP/liability fields are modified?
2. Should finance review always be mandatory where payment milestones or securities are configured?
3. Should vendor-specific requirements require approval from a procurement compliance role?
4. Should the system allow user-defined evaluation subcriteria, or only choose from controlled libraries?
5. Should supplier response schemas be generated immediately at preview, or only after approval?
6. Should addendum impact analysis be available before publication for simulated changes?
7. Should the NSSF ERP tender be converted into a formal calibration JSON fixture in the next package version?
8. What is the minimum legally acceptable source traceability granularity for first production release: section, clause, paragraph, or field?

---

## 27. Implementation Phases

### Phase 1: Wizard Runtime Foundation

Deliver:

1. Generic wizard shell.
2. STD package loading.
3. Step registry.
4. Field renderer.
5. Basic configuration persistence.
6. Validation dashboard.
7. Draft preview request integration.

### Phase 2: IT STD Configuration Steps

Deliver:

1. Tender identity.
2. TDS configuration.
3. Participation rules.
4. Dates and submission rules.
5. Security/indemnity fields.
6. SCC fields.

### Phase 3: IT Requirements Composer

Deliver:

1. Requirement categories.
2. Requirement rows.
3. Compliance treatment.
4. Evidence binding.
5. Evaluation binding.
6. Contract carry-forward binding.
7. Vendor-specific flagging.

### Phase 4: Price, Inventory, Evaluation, and Forms

Deliver:

1. System inventory setup.
2. Price schedule setup.
3. Evaluation criteria setup.
4. Form activation.
5. Supplier submission schema preview.
6. Evaluation schema preview.

### Phase 5: Governance, Review, Approval, Publication

Deliver:

1. Full workflow transitions.
2. Review comments.
3. Approval gates.
4. Bundle generation.
5. Publication lock.
6. Hashing.
7. Audit.

### Phase 6: Addendum and Calibration

Deliver:

1. Addendum impact analysis.
2. Addendum configuration.
3. Addendum publication.
4. NSSF ERP calibration instance.
5. Calibration validation report.

---

## 28. Next Required Artifact

The next artifact after this PRD should be:

`IT_Tender_Configuration_Wizard_Domain_Model.md`

That document must define the exact entities, fields, enums, relationships, constraints, indexes, immutability rules, validation bindings, source-trace fields, and audit fields needed to implement this wizard.

After the domain model, produce:

1. `IT_Tender_Configuration_Wizard_Governance_State_Model.md`
2. `IT_Tender_Configuration_Wizard_API_UI_Service_Contract.md`
3. `IT_Tender_Configuration_Wizard_Seed_Data_and_Smoke_Contracts.md`
4. `IT_Tender_Configuration_Wizard_Cursor_Implementation_Pack.md`

