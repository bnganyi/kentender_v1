# STD Engine Core Module - Governance, Roles, Permissions, and State Model

**Project:** KenTender e-Procurement System  
**Module:** Standard Tender Document Engine Core  
**Document type:** Governance, Roles, Permissions, and State Model  
**Document status:** Draft for implementation review  
**Version:** 0.1  
**Prepared date:** 2026-07-07  
**Preceding artifact:** `STD_Engine_Core_Domain_Model.md`  
**Next artifact:** STD Engine Core Seed Data and Smoke Contracts  

---

## 1. Purpose

This document defines the governance, approval, role, permission, and state-transition model for the Standard Tender Document Engine Core Module.

The purpose is to ensure that the STD Engine can safely manage official Standard Tender Documents as legal, auditable, versioned, immutable, and reusable procurement instruments. The model is generalized so that it can support multiple STD families, including Information Technology, WORKS, Goods, Consulting Services, Non-Consulting Services, Framework Agreements, and future PPRA or procuring-entity-approved STD families.

This document closes the approval/state-transition design gap before implementation proceeds into APIs, user interface design, import/export package construction, or STD-specific seed packages.

---

## 2. Scope

### 2.1 In Scope

This document covers governance for:

1. STD template families.
2. STD template versions.
3. STD source documents.
4. STD import packages.
5. STD sections and clauses.
6. STD parameters, rules, forms, fields, render blocks, and schemas.
7. STD version approval and activation.
8. Tender binding to an active STD version.
9. Tender-specific STD configuration review.
10. Generated tender artifact immutability.
11. Addendum impact governance.
12. Supersession and archival of STD versions.
13. Role-based access control.
14. Segregation of duties.
15. Audit events and evidentiary records.
16. State machine definitions.
17. Transition guards and blockers.
18. Implementation-ready permission checks.

### 2.2 Out of Scope

This document does not define:

1. Full UI screen layouts.
2. API endpoint contracts.
3. Full field dictionary, already covered in the domain model artifact.
4. IT STD extraction matrix.
5. Bidder portal implementation.
6. Evaluation committee scoring workflow outside the STD-generated evaluation structure.
7. Contract management workflow after contract execution, except where STD outputs are handed off.
8. Detailed document-renderer implementation.

---

## 3. Governance Principles

### 3.1 Official Source Control Principle

Each active STD template version must be traceable to an approved source document or approved source package. The system must preserve source identity, source hash, source file metadata, source page/section anchors where available, and the import package hash.

No active STD version may exist without a registered source authority.

### 3.2 No Direct Mutation of Active Versions

An active STD template version is immutable.

After activation, users must not be able to edit:

1. Locked clause text.
2. Section hierarchy.
3. Parameter definitions.
4. Rule definitions.
5. Form schemas.
6. Price schedule schemas.
7. Requirement schemas.
8. Evaluation schemas.
9. Contract output schemas.
10. Render block definitions.

Correction requires a new draft version, a governed correction process that results in a new immutable version, or a system-level emergency correction process with explicit legal authorization and full audit trail. The default behavior is new version creation.

### 3.3 Separation of Template Governance and Tender Configuration

The STD Engine has two governance layers:

| Layer | Purpose | Main users | Output |
|---|---|---|---|
| STD Administration | Controls official STD templates, versions, clauses, forms, rules, schemas, renderers, approvals, and activation | Central template administrators, legal reviewers, procurement standards reviewers, technical reviewers, auditors | Active STD template version |
| Tender STD Configuration | Controls tender-specific completion of TDS, SCC, requirements, schedules, forms, evaluation settings, and generated tender bundles | Procuring entity procurement officers, reviewers, approvers, auditors | Immutable tender bundle bound to one STD version |

No procuring entity user may modify a master STD template through the tender configuration interface.

### 3.4 Tender Binding Principle

A tender must bind to exactly one STD template version when the tender enters STD configuration or when the tender document bundle is first generated, depending on the implementation choice. The recommended binding point is when STD configuration is initiated.

Once a tender is published, the binding is immutable. If the official STD is later superseded, existing published tenders continue using the STD version they were bound to unless a formal cancellation/reissue or legally governed supersession process is executed.

### 3.5 Addendum Principle

After publication, no direct edit is allowed to the published tender bundle. Any change affecting published tender content must be processed as an addendum.

The addendum process must identify:

1. Affected sections.
2. Affected clauses.
3. Affected parameters.
4. Affected forms.
5. Affected bidder response fields.
6. Affected price schedules.
7. Affected technical requirements.
8. Affected evaluation rules.
9. Affected deadlines.
10. Whether bidder resubmission is required.
11. Whether already submitted bids must be invalidated, retained, supplemented, or reopened under applicable rules.

### 3.6 Auditability Principle

Every material governance action must create an immutable audit event.

Audit records must capture at minimum:

1. Actor.
2. Role or delegated authority used.
3. Action.
4. Object type.
5. Object identifier.
6. From-state.
7. To-state.
8. Timestamp.
9. Reason or comment where required.
10. Request metadata.
11. Previous hash where applicable.
12. New hash where applicable.
13. Validation status.
14. Approval decision.
15. Source package or document reference where applicable.

### 3.7 Least Privilege Principle

Users must have only the permissions required for their assigned responsibilities. Template administrators must not automatically receive procurement approval authority. Procuring entity users must not automatically receive template administration authority.

### 3.8 Segregation of Duties Principle

The system must prevent the same user from performing incompatible functions on the same governance object.

At minimum:

1. The user who authored or imported a template version must not be the sole approver of that same version.
2. The user who requested activation must not be the sole activator unless a documented emergency override is used.
3. A tender configurator must not be the sole final approver of their own tender STD configuration.
4. A reviewer who rejects an item must provide a reason.
5. A system administrator may recover or unlock system objects only through an auditable technical override, not by silently editing governed content.

### 3.9 Source Traceability Principle

Every object that can affect generated tender, bidder, evaluation, or contract output must be traceable to one or more sources. Where a source anchor is not available, the system must explicitly mark the traceability mode as `manual`, `derived`, `system_generated`, or `not_applicable`.

### 3.10 Validation Before Approval Principle

Governed objects must pass validation before they can be approved, activated, published, or rendered as final.

Validation findings have severity:

| Severity | Meaning | Approval impact |
|---|---|---|
| Blocker | Legal, structural, or data defect that prevents progression | Must be resolved before transition |
| Error | Invalid data or missing mandatory configuration | Must be resolved before transition |
| Warning | Risk or unusual condition requiring acknowledgement | May proceed only with acknowledgement and reason if policy permits |
| Information | Non-blocking note | No transition impact |

### 3.11 Immutable Publication Principle

A generated tender bundle that has been published must be immutable and reproducible.

The system must preserve:

1. The STD version used.
2. Configuration snapshot.
3. Render profile.
4. Rendered artifact hash.
5. Generated files.
6. Validation report at publication.
7. Publication timestamp.
8. Publishing user.
9. Approval event reference.

---

## 4. Governance Layers

## 4.1 Layer 1: STD Administration Governance

STD Administration governs official STD templates.

### 4.1.1 Main Responsibilities

1. Register STD families.
2. Register source documents.
3. Import structured STD packages.
4. Structure sections and clauses.
5. Define mutability classifications.
6. Define parameters.
7. Define rules.
8. Define forms and fields.
9. Define evidence requirements.
10. Define requirement schemas.
11. Define price schedule schemas.
12. Define evaluation schemas.
13. Define contract output schemas.
14. Define render blocks.
15. Run validation and smoke tests.
16. Submit for review.
17. Review legal/procurement/technical correctness.
18. Approve and activate STD versions.
19. Supersede and archive versions.
20. Provide audit access.

### 4.1.2 STD Administration Outputs

1. Active STD template version.
2. Template version hash.
3. Approved source traceability map.
4. Approved configuration surface.
5. Approved validation rules.
6. Approved render profile.
7. Approved import/export package.
8. Approved smoke test result.
9. Audit trail.

## 4.2 Layer 2: Tender STD Configuration Governance

Tender STD Configuration governs use of an active STD version in a specific tender.

### 4.2.1 Main Responsibilities

1. Select active STD template version.
2. Bind tender to STD version.
3. Complete TDS parameters.
4. Complete SCC parameters.
5. Configure procurement method and participation rules.
6. Configure tender security or tender-securing declaration settings.
7. Configure lots, alternatives, reservations, and margin of preference where allowed.
8. Prepare procuring entity requirements.
9. Prepare technical requirements.
10. Prepare implementation schedule.
11. Prepare system inventory tables.
12. Prepare price schedule setup.
13. Configure evaluation and qualification criteria within STD-permitted bounds.
14. Configure required forms and evidence.
15. Run tender STD validation.
16. Submit for review.
17. Approve generated tender bundle.
18. Publish generated tender bundle.
19. Process addenda where required.

### 4.2.2 Tender Configuration Outputs

1. Tender STD instance.
2. Tender-specific configuration value snapshot.
3. Generated tender document bundle.
4. Bidder response schema.
5. Evaluation schema.
6. Contract formation schema.
7. Validation report.
8. Publication record.
9. Addendum records if applicable.
10. Audit trail.

---

## 5. Role Model

## 5.1 Role Categories

| Category | Description |
|---|---|
| System Administration Roles | Technical platform administration roles. |
| STD Administration Roles | Roles responsible for master STD template governance. |
| Procuring Entity Roles | Roles responsible for tender-specific configuration and approval. |
| Review and Oversight Roles | Legal, procurement, technical, compliance, and audit review roles. |
| System Service Roles | Non-human roles used by importers, renderers, validators, and integration jobs. |

## 5.2 System Administration Roles

| Role | Purpose | Notes |
|---|---|---|
| Platform Super Administrator | Manages platform-level configuration, emergency recovery, tenant settings, and user access infrastructure | Must not be used for normal STD approval. |
| Security Administrator | Manages authentication, user groups, security policies, and access logs | Cannot approve STD versions by default. |
| Integration Administrator | Manages external integration credentials and service accounts | Cannot alter active STD content. |
| Audit Configuration Administrator | Configures audit retention, log export, and audit access policies | Cannot edit audit records. |

## 5.3 STD Administration Roles

| Role | Purpose | Typical holder |
|---|---|---|
| STD Registry Administrator | Creates STD families and registers official source documents | Central template administration team |
| STD Template Author | Structures draft versions, sections, clauses, parameters, forms, rules, schemas, and render blocks | Template digitization specialist |
| STD Import Operator | Imports package files and resolves import mapping issues | Template digitization or migration user |
| STD Legal Reviewer | Reviews legal text, locked sections, clause integrity, contract forms, and legal traceability | Legal officer |
| STD Procurement Standards Reviewer | Reviews procurement method, TDS, evaluation, forms, and compliance with procurement standards | Procurement standards officer |
| STD Technical Schema Reviewer | Reviews schema structure, field definitions, validation rules, render blocks, and smoke-test readiness | Product/technical reviewer |
| STD Approver | Approves a reviewed STD version for activation | Authorized governance officer |
| STD Activator | Activates approved STD versions and supersedes previous active versions where applicable | Controlled central role |
| STD Version Manager | Creates new draft versions from active or superseded versions | Central template administrator |
| STD Auditor | Reads all template records, approvals, source traces, hashes, and audit events | Internal/external audit |

## 5.4 Procuring Entity Roles

| Role | Purpose | Typical holder |
|---|---|---|
| PE Tender Initiator | Starts a tender and selects a procurement category or STD family | Procurement user |
| PE STD Configurator | Completes tender-specific STD parameters, requirements, forms, schedules, and configuration values | Procurement officer or assigned technical user |
| PE Technical Requirements Author | Drafts technical or functional requirements under controlled schemas | User department or technical department |
| PE Procurement Reviewer | Reviews tender configuration for procurement compliance | Procurement reviewer |
| PE Legal Reviewer | Reviews tender-specific contract/SCC configuration and legal risk | Legal officer |
| PE Technical Reviewer | Reviews technical requirements, implementation schedule, system inventory, and conformance matrices | Technical/domain expert |
| PE Budget/Finance Reviewer | Reviews financial thresholds, price schedules, budget alignment, and payment milestones | Finance or budget officer |
| PE Approver | Approves final tender STD configuration before publication | Authorized approving authority |
| PE Publisher | Publishes approved tender bundle | Procurement publishing role |
| PE Addendum Initiator | Requests changes after publication | Procurement officer |
| PE Addendum Approver | Approves addenda before publication | Authorized approving authority |
| PE Auditor | Reads tender STD configuration, generated artifacts, approvals, addenda, and audit records | Audit/oversight user |

## 5.5 Review and Oversight Roles

| Role | Purpose |
|---|---|
| Compliance Reviewer | Reviews compliance with internal policy, procurement plan, budget, and applicable controls. |
| Legal Oversight Viewer | Reads legal configuration and approval records without editing. |
| Procurement Oversight Viewer | Reads STD versions, tenders, addenda, and procurement records without editing. |
| External Auditor | Read-only access to selected records, hashes, artifacts, and audit events. |
| Investigation Officer | Read-only access with export rights under authorized investigation workflow. |

## 5.6 System Service Roles

| Role | Purpose | Permission boundary |
|---|---|---|
| STD Import Service | Executes import package parsing and staging | May create staging records only. |
| STD Validation Service | Runs validation rules and creates findings | May not approve, edit, or publish. |
| STD Render Service | Generates preview/final tender artifacts from approved source data | May not modify source data. |
| STD Hash Service | Computes hashes for packages, objects, snapshots, and generated artifacts | May not modify business fields. |
| STD Export Service | Exports approved or draft packages according to permission policy | Read/export only. |
| Notification Service | Sends workflow notifications | No content-edit permission. |
| Integration Service | Hands generated schemas to tender, supplier, evaluation, and contract modules | Read/output only. |

---

## 6. Authority Levels

## 6.1 Template Authority Levels

| Level | Authority | Description |
|---|---|---|
| Level T0 | Read-only | Can view template content and metadata. |
| Level T1 | Draft editing | Can create or edit draft template objects. |
| Level T2 | Review | Can review and recommend changes or approval. |
| Level T3 | Approval | Can approve template versions after review gates pass. |
| Level T4 | Activation | Can make approved versions active and supersede previous versions. |
| Level T5 | Emergency technical recovery | Can perform audited technical recovery, not normal content approval. |

## 6.2 Tender Authority Levels

| Level | Authority | Description |
|---|---|---|
| Level P0 | Read-only | Can view tender STD configuration and generated artifacts. |
| Level P1 | Draft configuration | Can complete or edit tender STD configuration before approval. |
| Level P2 | Review | Can review and request changes. |
| Level P3 | Approval | Can approve tender STD configuration for publication. |
| Level P4 | Publication | Can publish approved generated tender bundle. |
| Level P5 | Addendum publication | Can publish approved addenda. |

---

## 7. Segregation of Duties

## 7.1 Mandatory Segregation Rules

| Rule ID | Rule | Enforcement |
|---|---|---|
| SOD-001 | A user who imports or authors a draft STD version cannot be the only approving user for that same version | Hard blocker |
| SOD-002 | A user who requests activation cannot be the only user who activates the same version unless emergency override is approved | Hard blocker by default |
| SOD-003 | A user who configures a tender STD instance cannot be the sole final approver of that same instance | Hard blocker |
| SOD-004 | A user who rejects a review item must provide a rejection reason | Hard blocker |
| SOD-005 | A user cannot delete or alter audit events generated by their own actions | Hard blocker |
| SOD-006 | A platform administrator cannot silently alter active template content | Hard blocker |
| SOD-007 | A tender publisher cannot publish a tender bundle that lacks approval | Hard blocker |
| SOD-008 | A template activator cannot activate a version with unresolved blocker/error findings | Hard blocker |
| SOD-009 | A tender approver cannot approve configuration with unresolved blocker/error findings | Hard blocker |
| SOD-010 | A published tender bundle cannot be edited directly by any user | Hard blocker |

## 7.2 Recommended Segregation Rules

| Rule ID | Rule | Enforcement |
|---|---|---|
| SOD-011 | Legal reviewer and procurement standards reviewer should be different users for first activation of a template family | Configurable blocker or warning |
| SOD-012 | Technical schema reviewer should not be the same as template author for production activation | Configurable blocker or warning |
| SOD-013 | Final PE approver should not be the tender initiator | Configurable blocker or warning |
| SOD-014 | Addendum approver should not be the addendum initiator | Configurable blocker or warning |
| SOD-015 | Emergency override must require reason, approval reference, and post-event audit review | Hard blocker if missing |

---

## 8. State Model Overview

The STD Engine shall implement independent but linked state machines.

| State machine | Object | Purpose |
|---|---|---|
| SM-01 | STD Source Document | Tracks source registration, verification, and retirement. |
| SM-02 | STD Import Package | Tracks package upload, validation, import, and rejection. |
| SM-03 | STD Template Family | Tracks family availability and archival. |
| SM-04 | STD Template Version | Tracks draft, review, approval, activation, supersession, and archival. |
| SM-05 | STD Component | Tracks section/clause/parameter/rule/form/schema/render-block editing readiness within a version. |
| SM-06 | STD Approval Request | Tracks multi-review approval workflow. |
| SM-07 | Tender STD Instance | Tracks tender binding, configuration, review, approval, and publication. |
| SM-08 | Tender Generated Bundle | Tracks preview, final generation, approval, publication, and supersession by addendum. |
| SM-09 | Tender Addendum Impact | Tracks addendum request, impact analysis, approval, publication, and supersession. |
| SM-10 | Validation Finding | Tracks creation, resolution, acknowledgement, waiver, and closure. |
| SM-11 | Render Job | Tracks generation of preview and final artifacts. |
| SM-12 | Export Package | Tracks export request, generation, approval, and delivery. |

---

# 9. SM-01: STD Source Document State Model

## 9.1 Purpose

The STD Source Document state machine governs the registration and verification of official documents used to create or update STD template versions.

## 9.2 States

| State | Description |
|---|---|
| Uploaded | Source file has been uploaded but not verified. |
| Metadata Captured | Required metadata has been entered. |
| Hash Generated | Source hash has been computed. |
| Under Verification | Source authority and completeness are being reviewed. |
| Verified | Source is accepted for template version creation. |
| Rejected | Source is rejected as invalid, incomplete, duplicate, or unauthorized. |
| Retired | Source is no longer used for new versions but remains available for audit. |

## 9.3 Transitions

| From | To | Trigger | Actor | Guards | Audit event |
|---|---|---|---|---|---|
| Uploaded | Metadata Captured | Complete metadata | STD Registry Administrator | Required metadata present | `SOURCE_METADATA_CAPTURED` |
| Metadata Captured | Hash Generated | Generate hash | STD Hash Service | File accessible and readable | `SOURCE_HASH_GENERATED` |
| Hash Generated | Under Verification | Submit for verification | STD Registry Administrator | Hash exists | `SOURCE_SUBMITTED_FOR_VERIFICATION` |
| Under Verification | Verified | Verify source | STD Legal Reviewer or Procurement Standards Reviewer | Source authority confirmed; duplicate check complete | `SOURCE_VERIFIED` |
| Under Verification | Rejected | Reject source | Reviewer | Reason required | `SOURCE_REJECTED` |
| Verified | Retired | Retire source | STD Registry Administrator with approval | No active draft depends exclusively on it unless replacement identified | `SOURCE_RETIRED` |

## 9.4 Required Metadata

| Field | Required | Notes |
|---|---|---|
| Source document title | Yes | Official title. |
| Source issuing authority | Yes | Example: PPRA or approved authority. |
| Source document number | Yes where applicable | Example: Doc. 10. |
| Source revision date | Yes where available | Official revision date. |
| File name | Yes | Preserved original upload name. |
| File hash | Yes | System-generated. |
| Page count | Yes where detectable | Used for traceability. |
| Language | Yes | Default English where applicable. |
| Verification status | Yes | State-driven. |
| Verification notes | Conditional | Required on rejection. |

## 9.5 Invariants

1. A source document cannot be used for an active STD version unless it is Verified.
2. A verified source document cannot be physically deleted if any STD version references it.
3. Rejected source documents remain auditable but cannot be used for new template versions.
4. Retired source documents remain available for audit and historical tender reproduction.

---

# 10. SM-02: STD Import Package State Model

## 10.1 Purpose

The import package state machine governs structured package import, whether from JSON, YAML, Markdown bundle, or system-generated export package.

## 10.2 States

| State | Description |
|---|---|
| Uploaded | Package file received. |
| Parsed | Package syntax parsed successfully. |
| Parse Failed | Package syntax invalid. |
| Schema Validated | Package conforms to import schema. |
| Schema Failed | Package violates import schema. |
| Staged | Package objects staged but not committed. |
| Validation Failed | Package staged but validation produced blockers/errors. |
| Ready for Import | Package passed required validation gates. |
| Imported as Draft | Package committed into a draft STD version. |
| Rejected | Package rejected and cannot be imported without new upload. |
| Superseded by Reimport | A newer package superseded this staged package. |

## 10.3 Transitions

| From | To | Trigger | Actor | Guards | Audit event |
|---|---|---|---|---|---|
| Uploaded | Parsed | Parse package | STD Import Service | File readable | `IMPORT_PACKAGE_PARSED` |
| Uploaded | Parse Failed | Parse error | STD Import Service | Error captured | `IMPORT_PACKAGE_PARSE_FAILED` |
| Parsed | Schema Validated | Validate schema | STD Validation Service | Schema version supported | `IMPORT_SCHEMA_VALIDATED` |
| Parsed | Schema Failed | Schema failure | STD Validation Service | Findings created | `IMPORT_SCHEMA_FAILED` |
| Schema Validated | Staged | Stage package | STD Import Operator | Target family/version selected | `IMPORT_PACKAGE_STAGED` |
| Staged | Validation Failed | Run package validation | STD Validation Service | Findings include blockers/errors | `IMPORT_VALIDATION_FAILED` |
| Staged | Ready for Import | Run package validation | STD Validation Service | No unresolved blockers/errors | `IMPORT_READY` |
| Ready for Import | Imported as Draft | Commit import | STD Import Operator | Draft version exists or can be created; source verified | `IMPORT_COMMITTED` |
| Any pre-import state | Rejected | Reject package | STD Import Operator or reviewer | Reason required | `IMPORT_PACKAGE_REJECTED` |
| Staged | Superseded by Reimport | Reimport newer package | STD Import Operator | Replacement package reference exists | `IMPORT_PACKAGE_SUPERSEDED` |

## 10.4 Import Guards

| Guard ID | Guard | Severity |
|---|---|---|
| IMP-G001 | Package must declare package schema version | Blocker |
| IMP-G002 | Package must declare STD family code | Blocker |
| IMP-G003 | Package must declare target STD version code | Blocker |
| IMP-G004 | Package must reference a verified source document or declare source-trace mode | Blocker |
| IMP-G005 | Package must not overwrite active content in-place | Blocker |
| IMP-G006 | Package must contain unique stable keys for imported objects | Blocker |
| IMP-G007 | Package must preserve hierarchy order for sections and render blocks | Blocker |
| IMP-G008 | Package must include smoke tests for production activation | Error |
| IMP-G009 | Package may include calibration mappings but must mark them non-authoritative | Warning |

---

# 11. SM-03: STD Template Family State Model

## 11.1 Purpose

A template family groups versions of a standard document category, such as Information Technology, WORKS, Goods, or Consulting Services.

## 11.2 States

| State | Description |
|---|---|
| Draft | Family record is being prepared. |
| Active | Family may contain active versions and be selected for new template work. |
| Suspended | Family is temporarily blocked from new tender binding. |
| Archived | Family is historical only. |

## 11.3 Transitions

| From | To | Trigger | Actor | Guards | Audit event |
|---|---|---|---|---|---|
| Draft | Active | Activate family | STD Registry Administrator | Required family metadata complete | `STD_FAMILY_ACTIVATED` |
| Active | Suspended | Suspend family | STD Approver or Registry Administrator | Reason required | `STD_FAMILY_SUSPENDED` |
| Suspended | Active | Reinstate family | STD Approver | Reason required; no policy blocker | `STD_FAMILY_REINSTATED` |
| Active | Archived | Archive family | STD Approver | No active versions available for new tenders; historical tenders preserved | `STD_FAMILY_ARCHIVED` |
| Suspended | Archived | Archive family | STD Approver | Reason required | `STD_FAMILY_ARCHIVED` |

## 11.4 Invariants

1. A family code must be unique.
2. A family with historical tender usage cannot be physically deleted.
3. Suspending a family must not break existing tenders already bound to active versions.
4. Archiving a family must preserve all versions and usage records.

---

# 12. SM-04: STD Template Version State Model

## 12.1 Purpose

The STD Template Version state machine is the central governance process for creating, reviewing, approving, activating, superseding, and archiving official STD versions.

## 12.2 States

| State | Description |
|---|---|
| Draft | Version has been created but is still editable. |
| Structuring | Sections, clauses, parameters, rules, forms, schemas, and render blocks are being built. |
| Internal Review | Internal product/template review is underway. |
| Legal Review | Legal reviewer is reviewing locked text, clause integrity, contract content, and legal traceability. |
| Procurement Standards Review | Procurement reviewer is reviewing tendering, TDS, evaluation, forms, and procurement compliance. |
| Technical Schema Review | Technical reviewer is reviewing schema consistency, validation, rendering, and smoke tests. |
| Review Changes Required | One or more reviewers requested changes. |
| Ready for Approval | Required reviews passed and validation gates are clear. |
| Approved | Version approved but not yet active. |
| Active | Version may be used for new tender STD instances. |
| Suspended | Version is temporarily blocked from new tender binding. |
| Superseded | Version has been replaced by a newer active version. Existing tenders remain reproducible. |
| Archived | Version is historical and unavailable for new tender binding. |
| Rejected | Version cannot proceed without creating a new draft or major correction. |

## 12.3 Recommended Main Path

```text
Draft
 -> Structuring
 -> Internal Review
 -> Legal Review
 -> Procurement Standards Review
 -> Technical Schema Review
 -> Ready for Approval
 -> Approved
 -> Active
 -> Superseded
 -> Archived
```

The implementation may support parallel reviews, but the state model must still record each required review outcome.

## 12.4 Transition Table

| From | To | Trigger | Actor | Guards | Audit event |
|---|---|---|---|---|---|
| Draft | Structuring | Begin structuring | STD Template Author | Source verified or derivation source selected | `STD_VERSION_STRUCTURING_STARTED` |
| Structuring | Internal Review | Submit for internal review | STD Template Author | Required components present; validation run completed | `STD_VERSION_SUBMITTED_INTERNAL_REVIEW` |
| Internal Review | Review Changes Required | Request changes | STD Technical Schema Reviewer or assigned reviewer | Reason required | `STD_VERSION_CHANGES_REQUESTED` |
| Review Changes Required | Structuring | Resume structuring | STD Template Author | Change request acknowledged | `STD_VERSION_REWORK_STARTED` |
| Internal Review | Legal Review | Pass internal review | Assigned reviewer | No unresolved internal blockers | `STD_VERSION_INTERNAL_REVIEW_PASSED` |
| Legal Review | Review Changes Required | Request legal changes | STD Legal Reviewer | Reason required | `STD_VERSION_LEGAL_CHANGES_REQUESTED` |
| Legal Review | Procurement Standards Review | Pass legal review | STD Legal Reviewer | Legal checklist complete | `STD_VERSION_LEGAL_REVIEW_PASSED` |
| Procurement Standards Review | Review Changes Required | Request procurement changes | STD Procurement Standards Reviewer | Reason required | `STD_VERSION_PROCUREMENT_CHANGES_REQUESTED` |
| Procurement Standards Review | Technical Schema Review | Pass procurement review | STD Procurement Standards Reviewer | Procurement checklist complete | `STD_VERSION_PROCUREMENT_REVIEW_PASSED` |
| Technical Schema Review | Review Changes Required | Request technical/schema changes | STD Technical Schema Reviewer | Reason required | `STD_VERSION_TECHNICAL_CHANGES_REQUESTED` |
| Technical Schema Review | Ready for Approval | Pass technical review | STD Technical Schema Reviewer | Smoke tests pass; no blockers/errors | `STD_VERSION_TECHNICAL_REVIEW_PASSED` |
| Ready for Approval | Approved | Approve version | STD Approver | Required review approvals present; SOD checks pass | `STD_VERSION_APPROVED` |
| Approved | Active | Activate version | STD Activator | Version hash computed; no active conflict or supersession plan exists | `STD_VERSION_ACTIVATED` |
| Active | Suspended | Suspend version | STD Approver or Activator | Reason required | `STD_VERSION_SUSPENDED` |
| Suspended | Active | Reinstate version | STD Approver or Activator | Reason required; no replacement conflict | `STD_VERSION_REINSTATED` |
| Active | Superseded | Activate replacement | STD Activator | Replacement version approved and activated | `STD_VERSION_SUPERSEDED` |
| Superseded | Archived | Archive version | STD Version Manager | No open tender configuration using it except historical/published usage | `STD_VERSION_ARCHIVED` |
| Draft/Structuring/Internal Review/Review Changes Required | Rejected | Reject version | STD Approver | Reason required | `STD_VERSION_REJECTED` |

## 12.5 Activation Guards

| Guard ID | Guard | Severity |
|---|---|---|
| TV-G001 | Version must belong to an active STD family | Blocker |
| TV-G002 | Source document must be verified | Blocker |
| TV-G003 | Required section hierarchy must be complete | Blocker |
| TV-G004 | Locked sections must have locked mutability classification | Blocker |
| TV-G005 | Configurable sections must expose parameters instead of free editing where required | Blocker |
| TV-G006 | Every material object must have source traceability or declared traceability mode | Blocker |
| TV-G007 | Required legal review must be approved | Blocker |
| TV-G008 | Required procurement standards review must be approved | Blocker |
| TV-G009 | Required technical schema review must be approved | Blocker |
| TV-G010 | No unresolved blocker/error validation findings | Blocker |
| TV-G011 | Smoke tests must pass | Blocker for production activation |
| TV-G012 | Version hash must be computed | Blocker |
| TV-G013 | Segregation of duties checks must pass | Blocker |
| TV-G014 | If activating as replacement, supersession policy must be declared | Blocker |

## 12.6 Invariants

1. Only one version per family may be the default active version unless policy allows multiple active variants by procurement method, country, or legal regime.
2. An active version cannot be edited.
3. A version used by any tender cannot be deleted.
4. Superseding a version does not alter historical tenders bound to the previous version.
5. A suspended version cannot be selected for new tender binding unless an authorized override is recorded.
6. A rejected version cannot be activated.
7. A draft version cannot be selected for tender publication.

---

# 13. SM-05: STD Component State Model

## 13.1 Purpose

STD components include sections, clauses, parameters, rules, forms, form fields, evidence requirements, schemas, render blocks, and output schemas. They exist inside a template version and inherit key lifecycle constraints from that version.

## 13.2 Component States

| State | Description |
|---|---|
| Draft | Component is editable. |
| Incomplete | Component exists but required fields or traceability are missing. |
| Validated | Component passes validation. |
| Review Ready | Component is ready for reviewer inspection. |
| Review Changes Required | Component needs correction. |
| Approved Within Version | Component approved as part of version review. |
| Locked by Version | Component became immutable because parent version is active. |
| Deprecated Within Draft | Component is marked not to be used in the draft version. |
| Removed Before Activation | Component removed before version activation. |

## 13.3 Transition Table

| From | To | Trigger | Actor | Guards | Audit event |
|---|---|---|---|---|---|
| Draft | Incomplete | Save incomplete component | Author or Import Service | Required fields missing | `STD_COMPONENT_INCOMPLETE` |
| Draft/Incomplete | Validated | Validate component | Validation Service | No component errors | `STD_COMPONENT_VALIDATED` |
| Validated | Review Ready | Mark review ready | Author | Parent version in review-capable state | `STD_COMPONENT_REVIEW_READY` |
| Review Ready | Review Changes Required | Request component changes | Reviewer | Reason required | `STD_COMPONENT_CHANGES_REQUESTED` |
| Review Changes Required | Draft | Reopen component | Author | Parent version editable | `STD_COMPONENT_REOPENED` |
| Review Ready | Approved Within Version | Approve component | Reviewer | Review checklist complete | `STD_COMPONENT_APPROVED` |
| Approved Within Version | Locked by Version | Parent activated | System | Parent version Active | `STD_COMPONENT_LOCKED_BY_VERSION` |
| Draft/Incomplete/Validated | Deprecated Within Draft | Deprecate component | Author | Parent version editable | `STD_COMPONENT_DEPRECATED` |
| Draft/Incomplete/Validated/Deprecated Within Draft | Removed Before Activation | Remove component | Author | Parent version not active; dependency check passed | `STD_COMPONENT_REMOVED` |

## 13.4 Component-Level Edit Rules

| Parent version state | Component editing allowed? | Notes |
|---|---|---|
| Draft | Yes | Normal editing. |
| Structuring | Yes | Normal editing. |
| Internal Review | Restricted | Changes should reopen review or create change event. |
| Legal Review | Restricted | Legal-impacting changes return version to Review Changes Required. |
| Procurement Standards Review | Restricted | Procurement-impacting changes return version to Review Changes Required. |
| Technical Schema Review | Restricted | Schema-impacting changes return version to Review Changes Required. |
| Ready for Approval | No ordinary editing | Must reopen to Review Changes Required. |
| Approved | No ordinary editing | Must revoke approval or create new version. |
| Active | No | Immutable. |
| Suspended | No | Still immutable. |
| Superseded | No | Historical immutable. |
| Archived | No | Historical immutable. |
| Rejected | No ordinary editing | Clone to new draft if needed. |

---

# 14. SM-06: STD Approval Request State Model

## 14.1 Purpose

The approval request state machine tracks review and approval routing for STD template versions. It allows a version-level state to depend on multiple reviewer decisions.

## 14.2 States

| State | Description |
|---|---|
| Created | Approval request created. |
| Pending Assignment | Required reviewers have not all been assigned. |
| Pending Review | Reviewers assigned and review pending. |
| Partially Reviewed | At least one required review complete, others pending. |
| Changes Requested | At least one reviewer requested changes. |
| Review Complete | All required reviews passed. |
| Pending Final Approval | Awaiting final approver decision. |
| Approved | Final approval granted. |
| Rejected | Approval rejected. |
| Cancelled | Approval request cancelled before decision. |

## 14.3 Required Review Tracks

| Track | Required for first production activation? | Required for minor version? | Notes |
|---|---|---|---|
| Legal Review | Yes | Configurable by change impact | Required where clause, form, contract, or legal text changes occur. |
| Procurement Standards Review | Yes | Configurable by change impact | Required where TDS, evaluation, eligibility, forms, method, or rules change. |
| Technical Schema Review | Yes | Yes | Required where fields, rules, schemas, render blocks, import/export, or smoke tests change. |
| Source Traceability Review | Yes | Yes where source changed | May be performed by registry/legal/procurement reviewer. |
| Security Review | Conditional | Conditional | Required for service accounts, access model, or sensitive data schema changes. |

## 14.4 Transition Table

| From | To | Trigger | Actor | Guards | Audit event |
|---|---|---|---|---|---|
| Created | Pending Assignment | Create approval request | STD Template Author or Version Manager | Parent version in review-capable state | `APPROVAL_REQUEST_CREATED` |
| Pending Assignment | Pending Review | Assign reviewers | STD Approver or workflow router | All mandatory tracks assigned | `APPROVAL_REVIEWERS_ASSIGNED` |
| Pending Review | Partially Reviewed | Reviewer approves track | Assigned reviewer | Checklist complete | `APPROVAL_TRACK_APPROVED` |
| Pending Review/Partially Reviewed | Changes Requested | Reviewer requests changes | Assigned reviewer | Reason required | `APPROVAL_CHANGES_REQUESTED` |
| Changes Requested | Pending Review | Resubmit after changes | STD Template Author | Change responses recorded | `APPROVAL_RESUBMITTED` |
| Partially Reviewed | Review Complete | Final required track approved | Assigned reviewer/system | All required tracks approved | `APPROVAL_REVIEW_COMPLETE` |
| Review Complete | Pending Final Approval | Submit to final approver | Workflow router | SOD and validation pass | `APPROVAL_FINAL_SUBMITTED` |
| Pending Final Approval | Approved | Final approval | STD Approver | Final checklist complete; SOD checks pass | `APPROVAL_FINAL_APPROVED` |
| Pending Final Approval | Rejected | Final rejection | STD Approver | Reason required | `APPROVAL_FINAL_REJECTED` |
| Any non-final state | Cancelled | Cancel request | STD Version Manager or Approver | Reason required | `APPROVAL_REQUEST_CANCELLED` |

## 14.5 Approval Checklist

| Checklist item | Required |
|---|---|
| Source document verified | Yes |
| Package validation completed | Yes |
| Legal review complete | Yes for production activation |
| Procurement standards review complete | Yes for production activation |
| Technical schema review complete | Yes |
| Smoke tests pass | Yes for production activation |
| No blockers/errors open | Yes |
| Warnings acknowledged or resolved | Yes |
| Version hash computed | Yes |
| Segregation of duties passed | Yes |
| Supersession plan declared if replacing active version | Conditional |
| Activation notes provided | Yes |

---

# 15. SM-07: Tender STD Instance State Model

## 15.1 Purpose

A Tender STD Instance represents one tender's binding to one active STD template version and the tender-specific configuration values required to generate tender, bidder, evaluation, and contract artifacts.

## 15.2 States

| State | Description |
|---|---|
| Not Started | Tender exists but no STD instance has been created. |
| Bound to STD Version | Tender selected and bound to an active STD version. |
| In Configuration | PE users are completing parameters, requirements, forms, schedules, and settings. |
| Validation Failed | Configuration contains unresolved blockers/errors. |
| Ready for Review | Configuration is complete and validation passed. |
| Procurement Review | Procurement reviewer is reviewing tender configuration. |
| Technical Review | Technical reviewer is reviewing requirements and technical schedules where applicable. |
| Legal Review | Legal reviewer is reviewing SCC and contract-related configuration where applicable. |
| Finance/Budget Review | Finance reviewer is reviewing price schedules, payment terms, and budget-linked configuration where applicable. |
| Changes Required | One or more reviewers requested correction. |
| Approved for Generation | Configuration approved for final rendering. |
| Generated for Approval | Final bundle generated but not yet published. |
| Approved for Publication | Final generated bundle approved. |
| Published | Tender bundle published and immutable. |
| Addendum Required | Published tender requires a formal addendum for further change. |
| Closed | Tender STD instance is closed because tender ended, was cancelled, or moved downstream. |
| Cancelled | Tender STD instance cancelled before publication. |

## 15.3 Recommended Main Path

```text
Not Started
 -> Bound to STD Version
 -> In Configuration
 -> Ready for Review
 -> Procurement Review
 -> Technical Review / Legal Review / Finance Review as applicable
 -> Approved for Generation
 -> Generated for Approval
 -> Approved for Publication
 -> Published
```

Reviews may be parallel or sequential by implementation. The system must preserve each required review decision.

## 15.4 Transition Table

| From | To | Trigger | Actor | Guards | Audit event |
|---|---|---|---|---|---|
| Not Started | Bound to STD Version | Select STD version | PE Tender Initiator or PE STD Configurator | Selected version Active; family allowed for tender category | `TENDER_STD_BOUND` |
| Bound to STD Version | In Configuration | Start configuration | PE STD Configurator | User has tender edit permission | `TENDER_STD_CONFIGURATION_STARTED` |
| In Configuration | Validation Failed | Run validation | Validation Service | Blockers/errors found | `TENDER_STD_VALIDATION_FAILED` |
| Validation Failed | In Configuration | Correct configuration | PE STD Configurator | Parent tender not published | `TENDER_STD_CONFIGURATION_CORRECTED` |
| In Configuration | Ready for Review | Submit for review | PE STD Configurator | No unresolved blockers/errors; required values complete | `TENDER_STD_SUBMITTED_FOR_REVIEW` |
| Ready for Review | Procurement Review | Route procurement review | Workflow router | Procurement review required | `TENDER_STD_PROCUREMENT_REVIEW_STARTED` |
| Procurement Review | Changes Required | Request changes | PE Procurement Reviewer | Reason required | `TENDER_STD_PROCUREMENT_CHANGES_REQUESTED` |
| Procurement Review | Technical Review | Pass procurement review | PE Procurement Reviewer | Checklist complete | `TENDER_STD_PROCUREMENT_REVIEW_PASSED` |
| Technical Review | Changes Required | Request changes | PE Technical Reviewer | Reason required | `TENDER_STD_TECHNICAL_CHANGES_REQUESTED` |
| Technical Review | Legal Review | Pass technical review | PE Technical Reviewer | Required technical checklist complete | `TENDER_STD_TECHNICAL_REVIEW_PASSED` |
| Legal Review | Changes Required | Request changes | PE Legal Reviewer | Reason required | `TENDER_STD_LEGAL_CHANGES_REQUESTED` |
| Legal Review | Finance/Budget Review | Pass legal review | PE Legal Reviewer | Legal checklist complete | `TENDER_STD_LEGAL_REVIEW_PASSED` |
| Finance/Budget Review | Changes Required | Request changes | PE Budget/Finance Reviewer | Reason required | `TENDER_STD_FINANCE_CHANGES_REQUESTED` |
| Finance/Budget Review | Approved for Generation | Pass finance review | PE Budget/Finance Reviewer or PE Approver | Finance checklist complete; approval policy met | `TENDER_STD_APPROVED_FOR_GENERATION` |
| Changes Required | In Configuration | Reopen configuration | PE STD Configurator | Change request acknowledged | `TENDER_STD_REWORK_STARTED` |
| Approved for Generation | Generated for Approval | Generate final bundle | Render Service | Render job successful; hashes computed | `TENDER_STD_FINAL_BUNDLE_GENERATED` |
| Generated for Approval | Approved for Publication | Approve final bundle | PE Approver | SOD checks pass; final preview accepted | `TENDER_STD_APPROVED_FOR_PUBLICATION` |
| Approved for Publication | Published | Publish bundle | PE Publisher | Publication window valid; approval exists | `TENDER_STD_PUBLISHED` |
| Published | Addendum Required | Request post-publication change | PE Addendum Initiator | Change affects published content | `TENDER_STD_ADDENDUM_REQUIRED` |
| Any pre-publication state | Cancelled | Cancel instance | PE Tender Initiator or authorized approver | Reason required | `TENDER_STD_CANCELLED` |
| Published | Closed | Close after tender lifecycle | System or PE Publisher | Tender closed/cancelled/completed | `TENDER_STD_CLOSED` |

## 15.5 Tender Configuration Guards

| Guard ID | Guard | Severity |
|---|---|---|
| TI-G001 | Tender must be bound to an Active STD version | Blocker |
| TI-G002 | Bound STD version must not be suspended at binding time unless override approved | Blocker |
| TI-G003 | Required TDS parameters must be complete | Blocker |
| TI-G004 | Required SCC parameters must be complete where contract forms are generated | Blocker |
| TI-G005 | Locked sections must not contain tender-specific manual edits | Blocker |
| TI-G006 | Tender dates must follow valid sequence | Blocker |
| TI-G007 | Tender validity period must satisfy configured rule | Blocker/Error depending on STD rule |
| TI-G008 | Tender security or alternative security configuration must satisfy allowed STD options | Blocker |
| TI-G009 | Procurement method and participation settings must be allowed for the STD family/version | Blocker |
| TI-G010 | Evaluation criteria must stay within STD-permitted configurable bounds | Blocker |
| TI-G011 | Price schedule setup must match selected STD price schema | Blocker |
| TI-G012 | Technical requirements must use approved requirement schema | Blocker |
| TI-G013 | Addendum-only changes cannot be applied directly after publication | Blocker |
| TI-G014 | Final bundle must be generated from current approved configuration snapshot | Blocker |
| TI-G015 | Final publication requires bundle hash and validation report | Blocker |
| TI-G016 | SOD checks must pass before final approval | Blocker |

## 15.6 Invariants

1. One tender STD instance binds to one STD template version.
2. A published tender STD instance cannot change configuration values directly.
3. A tender cannot publish an STD-generated bundle without passing validation.
4. A tender cannot use a draft, rejected, archived, or non-active STD version for new publication.
5. Configuration values must preserve field source, actor, timestamp, and version snapshot.
6. Addenda create new output artifacts without mutating the original published bundle.

---

# 16. SM-08: Tender Generated Bundle State Model

## 16.1 Purpose

A generated bundle is the rendered tender artifact set generated from a tender STD instance. It may include tender PDF, HTML, forms, bidder response schemas, evaluation checklists, price schedules, technical compliance matrices, contract formation templates, and machine-readable output packages.

## 16.2 States

| State | Description |
|---|---|
| Preview Requested | User requested preview generation. |
| Preview Generated | Preview generated for review, not publishable. |
| Preview Failed | Preview generation failed. |
| Final Generation Requested | Final generation requested from approved configuration. |
| Final Generated | Final bundle generated and hashed. |
| Final Generation Failed | Final generation failed. |
| Under Approval | Final bundle is under approval. |
| Approved | Final bundle approved for publication. |
| Published | Final bundle published and immutable. |
| Superseded by Addendum | Bundle remains historical but later addendum modifies tender content. |
| Voided Before Publication | Final bundle voided before publication. |

## 16.3 Transition Table

| From | To | Trigger | Actor | Guards | Audit event |
|---|---|---|---|---|---|
| None | Preview Requested | Request preview | PE STD Configurator | Tender instance in editable/review state | `BUNDLE_PREVIEW_REQUESTED` |
| Preview Requested | Preview Generated | Render preview | Render Service | Render profile available | `BUNDLE_PREVIEW_GENERATED` |
| Preview Requested | Preview Failed | Render failure | Render Service | Error captured | `BUNDLE_PREVIEW_FAILED` |
| Approved for Generation | Final Generation Requested | Request final generation | PE STD Configurator or workflow | Tender instance approved for generation | `BUNDLE_FINAL_REQUESTED` |
| Final Generation Requested | Final Generated | Render final | Render Service | Configuration snapshot locked; hashes computed | `BUNDLE_FINAL_GENERATED` |
| Final Generation Requested | Final Generation Failed | Render failure | Render Service | Error captured | `BUNDLE_FINAL_FAILED` |
| Final Generated | Under Approval | Submit bundle approval | PE STD Configurator | Final generated; validation report attached | `BUNDLE_SUBMITTED_FOR_APPROVAL` |
| Under Approval | Approved | Approve bundle | PE Approver | SOD pass; final preview accepted | `BUNDLE_APPROVED` |
| Approved | Published | Publish bundle | PE Publisher | Tender publication approval exists | `BUNDLE_PUBLISHED` |
| Published | Superseded by Addendum | Publish addendum | PE Publisher/Addendum workflow | Addendum approved | `BUNDLE_SUPERSEDED_BY_ADDENDUM` |
| Final Generated/Under Approval/Approved | Voided Before Publication | Void bundle | PE Approver | Reason required | `BUNDLE_VOIDED` |

## 16.4 Bundle Invariants

1. Preview bundles are not publishable.
2. Final bundles must be generated from an approved configuration snapshot.
3. Published bundles cannot be regenerated in-place.
4. Published bundles must remain retrievable even after addenda.
5. Each final bundle must have a content hash.
6. Bundle metadata must identify STD version, render profile, configuration snapshot, and source objects.

---

# 17. SM-09: Tender Addendum Impact State Model

## 17.1 Purpose

The addendum impact model governs post-publication changes to a tender that affect published STD-generated content.

## 17.2 States

| State | Description |
|---|---|
| Addendum Requested | Change requested after publication. |
| Impact Analysis Draft | Affected objects are being identified. |
| Impact Analysis Complete | Impact analysis completed. |
| Validation Failed | Proposed addendum has blockers/errors. |
| Ready for Review | Addendum package ready for review. |
| Under Review | Addendum under procurement/legal/technical review as applicable. |
| Changes Required | Reviewers requested changes. |
| Approved | Addendum approved for publication. |
| Published | Addendum published and original bundle marked superseded by addendum. |
| Withdrawn | Addendum request withdrawn before publication. |
| Rejected | Addendum request rejected. |

## 17.3 Transition Table

| From | To | Trigger | Actor | Guards | Audit event |
|---|---|---|---|---|---|
| Published tender | Addendum Requested | Request addendum | PE Addendum Initiator | Tender published; reason required | `ADDENDUM_REQUESTED` |
| Addendum Requested | Impact Analysis Draft | Start impact analysis | PE STD Configurator or system | Addendum request accepted | `ADDENDUM_IMPACT_STARTED` |
| Impact Analysis Draft | Impact Analysis Complete | Complete impact analysis | PE STD Configurator/System | Affected objects identified | `ADDENDUM_IMPACT_COMPLETED` |
| Impact Analysis Complete | Validation Failed | Run validation | Validation Service | Blockers/errors found | `ADDENDUM_VALIDATION_FAILED` |
| Validation Failed | Impact Analysis Draft | Correct addendum | PE STD Configurator | Findings addressed | `ADDENDUM_REWORK_STARTED` |
| Impact Analysis Complete | Ready for Review | Submit addendum | PE Addendum Initiator | No unresolved blockers/errors | `ADDENDUM_SUBMITTED_FOR_REVIEW` |
| Ready for Review | Under Review | Route reviewers | Workflow router | Required reviewers assigned | `ADDENDUM_REVIEW_STARTED` |
| Under Review | Changes Required | Request changes | Reviewer | Reason required | `ADDENDUM_CHANGES_REQUESTED` |
| Changes Required | Impact Analysis Draft | Rework addendum | PE Addendum Initiator | Change request acknowledged | `ADDENDUM_REWORK_STARTED` |
| Under Review | Approved | Approve addendum | PE Addendum Approver | SOD pass; review tracks complete | `ADDENDUM_APPROVED` |
| Approved | Published | Publish addendum | PE Publisher | Publication controls pass; artifacts hashed | `ADDENDUM_PUBLISHED` |
| Any pre-publication state | Withdrawn | Withdraw addendum | PE Addendum Initiator or Approver | Reason required | `ADDENDUM_WITHDRAWN` |
| Under Review/Ready for Review | Rejected | Reject addendum | PE Addendum Approver | Reason required | `ADDENDUM_REJECTED` |

## 17.4 Addendum Impact Categories

| Impact category | Examples | Required handling |
|---|---|---|
| Deadline impact | Submission date, clarification deadline, opening date | Update dates; notify bidders; determine extension requirements. |
| Eligibility impact | Mandatory documents, eligibility rules, debarment rules | Revalidate bidder response schema. |
| Technical requirement impact | Requirement rows, compliance matrix, specifications | Identify affected forms and evaluation matrix. |
| Price schedule impact | Line items, currency, taxes, recurrent costs | Regenerate price schedule and financial evaluation schema. |
| Evaluation impact | Scoring criteria, pass mark, mandatory criteria | High-risk; require procurement/legal review. |
| Contract/SCC impact | Payment terms, warranty, performance security, IP, acceptance | Require legal and finance review where applicable. |
| Form impact | Bidder declaration, evidence requirements, templates | Regenerate bidder response schema. |
| Render-only impact | Formatting, numbering, typo without substantive effect | May use simplified review if policy allows. |

## 17.5 Addendum Guards

| Guard ID | Guard | Severity |
|---|---|---|
| AD-G001 | Addendum must reference a published tender bundle | Blocker |
| AD-G002 | Addendum must state reason and change summary | Blocker |
| AD-G003 | Affected sections/fields/forms/rules must be identified | Blocker |
| AD-G004 | Addendum must declare bidder response impact | Blocker |
| AD-G005 | Addendum must declare deadline impact | Blocker |
| AD-G006 | Evaluation-impacting addendum requires procurement review | Blocker |
| AD-G007 | Contract-impacting addendum requires legal review | Blocker |
| AD-G008 | Price/payment-impacting addendum requires finance review | Blocker |
| AD-G009 | Published addendum artifact must be hashed | Blocker |
| AD-G010 | Original bundle must remain immutable and retrievable | Blocker |

---

# 18. SM-10: Validation Finding State Model

## 18.1 Purpose

Validation findings document blockers, errors, warnings, and informational notes generated by the rules engine, validators, reviewers, import process, render process, and governance checks.

## 18.2 States

| State | Description |
|---|---|
| Open | Finding exists and is unresolved. |
| Assigned | Finding assigned to a user or role for action. |
| In Remediation | User is addressing finding. |
| Resolved | Finding has been corrected and awaits verification. |
| Verified Closed | Finding is verified closed. |
| Acknowledged | Warning has been acknowledged with reason. |
| Waiver Requested | User requested waiver for finding. |
| Waived | Authorized approver waived finding where policy permits. |
| Reopened | Finding reopened after verification failed or related data changed. |
| Superseded | Finding no longer applies because object changed or was replaced. |

## 18.3 Transition Table

| From | To | Trigger | Actor | Guards | Audit event |
|---|---|---|---|---|---|
| None | Open | Create finding | Validation Service/Reviewer | Finding details present | `VALIDATION_FINDING_OPENED` |
| Open | Assigned | Assign finding | Workflow router or reviewer | Assignee valid | `VALIDATION_FINDING_ASSIGNED` |
| Assigned | In Remediation | Start remediation | Assigned user | Parent object editable | `VALIDATION_REMEDIATION_STARTED` |
| In Remediation | Resolved | Mark resolved | Assigned user | Resolution note required | `VALIDATION_FINDING_RESOLVED` |
| Resolved | Verified Closed | Verify correction | Validation Service/Reviewer | Revalidation passes | `VALIDATION_FINDING_CLOSED` |
| Open/Assigned | Acknowledged | Acknowledge warning | Authorized user | Severity is Warning or Information; reason required for Warning | `VALIDATION_FINDING_ACKNOWLEDGED` |
| Open/Assigned | Waiver Requested | Request waiver | Authorized user | Finding policy allows waiver | `VALIDATION_WAIVER_REQUESTED` |
| Waiver Requested | Waived | Approve waiver | Authorized approver | Reason and authority recorded | `VALIDATION_FINDING_WAIVED` |
| Resolved/Acknowledged/Waived/Verified Closed | Reopened | Reopen finding | Validation Service/Reviewer | Related data changed or verification failed | `VALIDATION_FINDING_REOPENED` |
| Open/Assigned/In Remediation | Superseded | Object replaced | System | Replacement object reference exists | `VALIDATION_FINDING_SUPERSEDED` |

## 18.4 Waiver Policy

| Severity | Waiver allowed? | Notes |
|---|---|---|
| Blocker | No by default | Emergency override only with explicit authority and post-audit. |
| Error | No by default | Must be corrected unless policy explicitly permits. |
| Warning | Yes | Requires acknowledgement or waiver reason. |
| Information | Not applicable | Can be closed or left as informational. |

---

# 19. SM-11: Render Job State Model

## 19.1 Purpose

Render jobs generate preview and final artifacts from STD template versions and tender STD configuration snapshots.

## 19.2 States

| State | Description |
|---|---|
| Queued | Render job created. |
| Running | Render job executing. |
| Succeeded | Render job completed. |
| Failed | Render job failed. |
| Cancelled | Render job cancelled before completion. |
| Expired | Preview artifact expired under retention policy. |

## 19.3 Transition Table

| From | To | Trigger | Actor | Guards | Audit event |
|---|---|---|---|---|---|
| None | Queued | Request render | User/System | Render profile selected | `RENDER_JOB_QUEUED` |
| Queued | Running | Start render | Render Service | Required data available | `RENDER_JOB_STARTED` |
| Running | Succeeded | Complete render | Render Service | Artifact generated; hash computed where required | `RENDER_JOB_SUCCEEDED` |
| Running | Failed | Render failure | Render Service | Error captured | `RENDER_JOB_FAILED` |
| Queued | Cancelled | Cancel render | User/System | Job not running or cancellation safe | `RENDER_JOB_CANCELLED` |
| Succeeded | Expired | Expire preview | System | Artifact is preview and retention expired | `RENDER_PREVIEW_EXPIRED` |

## 19.4 Render Guards

| Guard ID | Guard | Severity |
|---|---|---|
| RJ-G001 | Render profile must be valid for STD version | Blocker |
| RJ-G002 | Final render requires approved configuration snapshot | Blocker |
| RJ-G003 | Published final render must compute content hash | Blocker |
| RJ-G004 | Preview render must be watermarked or marked non-final | Error |
| RJ-G005 | Render errors must create validation findings or render findings | Error |

---

# 20. SM-12: Export Package State Model

## 20.1 Purpose

Export packages support review, backup, source control, migration, and environment promotion. Exports may be generated for draft versions, approved versions, active versions, or historical versions depending on permission and policy.

## 20.2 States

| State | Description |
|---|---|
| Export Requested | User requested export. |
| Export Authorized | Request approved or permitted by policy. |
| Export Running | Export service is generating package. |
| Export Generated | Package generated and hashed. |
| Export Failed | Package generation failed. |
| Delivered | Package made available to requester. |
| Revoked | Export access revoked. |
| Expired | Export download expired. |

## 20.3 Transition Table

| From | To | Trigger | Actor | Guards | Audit event |
|---|---|---|---|---|---|
| None | Export Requested | Request export | Authorized user | Object exists; user has export request right | `EXPORT_REQUESTED` |
| Export Requested | Export Authorized | Authorize export | System or approver | Export policy allows | `EXPORT_AUTHORIZED` |
| Export Authorized | Export Running | Start export | Export Service | Data accessible | `EXPORT_STARTED` |
| Export Running | Export Generated | Complete export | Export Service | Package generated; hash computed | `EXPORT_GENERATED` |
| Export Running | Export Failed | Export error | Export Service | Error captured | `EXPORT_FAILED` |
| Export Generated | Delivered | Deliver package | Export Service | Requester still authorized | `EXPORT_DELIVERED` |
| Delivered | Revoked | Revoke export | Security Administrator or approver | Reason required | `EXPORT_REVOKED` |
| Delivered | Expired | Expire download | System | Retention elapsed | `EXPORT_EXPIRED` |

## 20.4 Export Restrictions

1. Exports of active official STD packages must include source traceability and hashes.
2. Exports of published tender bundles must include configuration snapshot and bundle hash.
3. Exported packages must not become production records unless imported and governed through the import process.
4. Sensitive data in tender-specific exports must respect role and tenant boundaries.

---

# 21. Permission Model

## 21.1 Permission Actions

The following normalized actions shall be used in permission definitions.

| Action | Meaning |
|---|---|
| `read` | View record and metadata. |
| `read_sensitive` | View sensitive fields or restricted metadata. |
| `create` | Create new record. |
| `edit_draft` | Edit record while draft/editable. |
| `submit_review` | Submit for review. |
| `review` | Perform review decision. |
| `request_changes` | Return item for correction. |
| `approve` | Approve item. |
| `activate` | Activate version or family. |
| `suspend` | Suspend version/family. |
| `supersede` | Supersede active version/bundle. |
| `archive` | Archive historical object. |
| `bind` | Bind tender to STD version. |
| `configure` | Complete tender-specific STD configuration. |
| `generate_preview` | Generate non-final preview. |
| `generate_final` | Generate final bundle. |
| `publish` | Publish final bundle or addendum. |
| `request_addendum` | Request addendum. |
| `approve_addendum` | Approve addendum. |
| `run_validation` | Run validation. |
| `resolve_finding` | Resolve validation findings. |
| `waive_finding` | Waive eligible finding. |
| `import_package` | Import structured package. |
| `export_package` | Export structured package. |
| `view_audit` | View audit events. |
| `emergency_override` | Execute controlled emergency action. |

## 21.2 Template Administration Permission Matrix

| Object / Action | Registry Admin | Template Author | Import Operator | Legal Reviewer | Procurement Reviewer | Technical Reviewer | STD Approver | STD Activator | STD Auditor | Platform Admin |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| STD Family - read | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| STD Family - create | Yes | No | No | No | No | No | No | No | No | No |
| STD Family - edit draft | Yes | No | No | No | No | No | No | No | No | Technical only |
| STD Family - activate | Yes | No | No | No | No | No | Conditional | Conditional | No | No |
| STD Family - suspend/archive | Conditional | No | No | No | No | No | Yes | Conditional | No | No |
| Source Document - upload/register | Yes | Conditional | Conditional | No | No | No | No | No | No | Technical only |
| Source Document - verify | No | No | No | Yes | Yes | Conditional | Conditional | No | No | No |
| Source Document - retire | Yes | No | No | No | No | No | Conditional | No | No | No |
| Import Package - upload/import | Conditional | Conditional | Yes | No | No | No | No | No | No | Technical only |
| Import Package - reject | Yes | No | Yes | Conditional | Conditional | Conditional | Conditional | No | No | No |
| Template Version - create draft | Yes | Yes | Conditional | No | No | No | No | No | No | No |
| Template Version - edit draft | Conditional | Yes | Conditional | No | No | Conditional | No | No | No | No |
| Template Version - submit review | Conditional | Yes | Conditional | No | No | No | No | No | No | No |
| Template Version - legal review | No | No | No | Yes | No | No | No | No | No | No |
| Template Version - procurement review | No | No | No | No | Yes | No | No | No | No | No |
| Template Version - technical review | No | No | No | No | No | Yes | No | No | No | No |
| Template Version - approve | No | No | No | No | No | No | Yes | No | No | No |
| Template Version - activate | No | No | No | No | No | No | Conditional | Yes | No | No |
| Template Version - suspend | No | No | No | No | No | No | Yes | Yes | No | No |
| Template Version - supersede | No | No | No | No | No | No | Conditional | Yes | No | No |
| Template Version - archive | Yes | No | No | No | No | No | Conditional | Conditional | No | No |
| Components - create/edit draft | Conditional | Yes | Conditional | No | No | Conditional | No | No | No | No |
| Components - review | No | No | No | Yes | Yes | Yes | Conditional | No | No | No |
| Validation - run | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Technical only |
| Validation - resolve findings | Conditional | Yes | Conditional | No | No | Conditional | No | No | No | No |
| Validation - waive warning | No | No | No | Conditional | Conditional | Conditional | Yes | No | No | No |
| Render preview | Yes | Yes | No | Yes | Yes | Yes | Yes | Yes | Yes | Technical only |
| Export package | Yes | Conditional | Conditional | No | No | Conditional | Yes | Conditional | Yes | Technical only |
| View audit | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Yes | Technical only |
| Emergency override | No | No | No | No | No | No | No | No | No | Conditional |

Legend:

| Value | Meaning |
|---|---|
| Yes | Permission normally granted. |
| No | Permission normally denied. |
| Conditional | Permission allowed only if assigned to object, tenant, workflow stage, or explicit delegated authority. |
| Technical only | Platform-level action that cannot alter business/legal content without governed workflow. |

## 21.3 Tender STD Configuration Permission Matrix

| Object / Action | Tender Initiator | STD Configurator | Technical Author | Procurement Reviewer | Legal Reviewer | Finance Reviewer | PE Approver | PE Publisher | Addendum Initiator | Addendum Approver | PE Auditor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Tender STD Instance - read | Yes | Yes | Conditional | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Bind tender to active STD | Yes | Yes | No | No | No | No | No | No | No | No | No |
| Configure TDS values | Conditional | Yes | No | No | No | No | No | No | No | No | No |
| Configure technical requirements | No | Conditional | Yes | No | No | No | No | No | No | No | No |
| Configure SCC values | No | Conditional | No | No | Conditional | Conditional | No | No | No | No | No |
| Configure evaluation criteria | No | Conditional | Conditional | Conditional | No | Conditional | No | No | No | No | No |
| Configure price schedule setup | No | Conditional | Conditional | No | No | Conditional | No | No | No | No | No |
| Run validation | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No | Yes | Yes | Yes |
| Submit for review | Conditional | Yes | Conditional | No | No | No | No | No | No | No | No |
| Procurement review | No | No | No | Yes | No | No | No | No | No | No | No |
| Technical review | No | No | Conditional | No | No | No | No | No | No | No | No |
| Legal review | No | No | No | No | Yes | No | No | No | No | No | No |
| Finance review | No | No | No | No | No | Yes | No | No | No | No | No |
| Approve tender STD configuration | No | No | No | No | No | No | Yes | No | No | No | No |
| Generate preview | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No | Yes | Yes | Yes |
| Generate final bundle | No | Yes | No | No | No | No | Conditional | No | No | No | No |
| Approve final bundle | No | No | No | No | No | No | Yes | No | No | No | No |
| Publish final bundle | No | No | No | No | No | No | No | Yes | No | No | No |
| Request addendum | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | No | Yes | No | No |
| Perform addendum impact analysis | No | Yes | Conditional | Conditional | Conditional | Conditional | No | No | Yes | No | No |
| Approve addendum | No | No | No | No | No | No | Conditional | No | No | Yes | No |
| Publish addendum | No | No | No | No | No | No | No | Yes | No | No | No |
| View audit | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Yes |

## 21.4 System Service Permission Matrix

| Object / Action | Import Service | Validation Service | Render Service | Hash Service | Export Service | Notification Service | Integration Service |
|---|---:|---:|---:|---:|---:|---:|---:|
| Read source files | Yes | Conditional | Conditional | Yes | Conditional | No | No |
| Create staging records | Yes | No | No | No | No | No | No |
| Commit production records | Conditional | No | No | No | No | No | No |
| Run validation | No | Yes | Conditional | No | No | No | No |
| Create validation findings | No | Yes | Conditional | No | No | No | No |
| Generate preview artifacts | No | No | Yes | Conditional | No | No | No |
| Generate final artifacts | No | No | Yes | Conditional | No | No | No |
| Compute hashes | No | Conditional | Conditional | Yes | Conditional | No | Conditional |
| Export packages | No | No | No | Conditional | Yes | No | No |
| Send notifications | No | No | No | No | No | Yes | No |
| Provide schemas to consuming modules | No | No | No | Conditional | No | No | Yes |
| Approve/reject/publish | No | No | No | No | No | No | No |

---

# 22. Data Access Boundaries

## 22.1 Tenant and Organization Boundaries

1. Central STD Administration users may manage official template families and versions across the platform according to assigned authority.
2. Procuring entity users may configure only tenders within their procuring entity, unless explicitly delegated.
3. A procuring entity may read active STD metadata needed to create tenders, but must not edit master STD content.
4. Auditors may receive cross-tenant access only through explicit audit authorization.

## 22.2 Object-Level Boundaries

| Object | Boundary rule |
|---|---|
| STD Family | Central governance object. |
| STD Template Version | Central governance object. |
| Source Document | Central governance object; source access may be restricted. |
| Tender STD Instance | Procuring entity object. |
| Tender Configuration Values | Procuring entity object, locked after publication. |
| Published Bundle | Procuring entity object, immutable after publication. |
| Addendum | Procuring entity object, linked to published bundle. |
| Audit Event | Read restricted by role and object scope; no user edit. |

## 22.3 Sensitive Fields

The following fields require `read_sensitive` permission where implemented:

1. Security-related configuration.
2. Internal reviewer comments marked confidential.
3. Investigation notes.
4. Emergency override reasons.
5. Unpublished tender configuration.
6. Draft addendum content before publication.
7. System integration credentials and service details.
8. Internal audit annotations.

---

# 23. Governance Workflow Details

# 23.1 Creating a New STD Family

## 23.1.1 Steps

1. Registry Administrator creates draft family.
2. Registry Administrator enters family metadata.
3. System validates code uniqueness.
4. Registry Administrator activates family.
5. Audit event records activation.

## 23.1.2 Required Metadata

1. Family code.
2. Family name.
3. Procurement category.
4. Issuing authority.
5. Applicability notes.
6. Default language.
7. Status.
8. Owner role.

## 23.1.3 Controls

1. Family code cannot be reused.
2. Active family cannot be deleted.
3. Archived family remains visible in historical records.

---

# 23.2 Registering a Source Document

## 23.2.1 Steps

1. Registry Administrator uploads source file.
2. System captures file metadata.
3. Hash Service computes source hash.
4. Registry Administrator enters official metadata.
5. Reviewer verifies source authority and completeness.
6. Source becomes Verified or Rejected.

## 23.2.2 Controls

1. Unverified sources cannot support active STD versions.
2. Duplicate source hashes should be flagged.
3. Source document retirement must not break historical reproducibility.

---

# 23.3 Creating a Draft STD Version

## 23.3.1 Creation Paths

| Path | Description |
|---|---|
| From source import | Create draft version from structured import package. |
| From existing active version | Clone current active version to create revised draft. |
| From superseded version | Clone historical version for controlled restoration or branch. |
| Manual structure | Create draft version manually through UI. |

## 23.3.2 Required Version Metadata

1. Family.
2. Version code.
3. Version label.
4. Effective date or intended effective date.
5. Source document reference.
6. Version basis.
7. Change summary.
8. Draft owner.
9. Traceability mode.
10. Activation policy.

## 23.3.3 Controls

1. Version code must be unique within family.
2. Draft may not override active version in-place.
3. Active version clone must preserve source and hash history.
4. Version cannot progress to review until core components exist.

---

# 23.4 Reviewing and Approving an STD Version

## 23.4.1 Review Tracks

| Review track | Main focus |
|---|---|
| Legal Review | Locked legal text, legal clauses, contract forms, SCC relationship, legal traceability. |
| Procurement Standards Review | Tendering procedure, TDS, evaluation, bidder forms, award rules, eligibility, procurement compliance. |
| Technical Schema Review | Data structure, rules, field types, dependencies, render blocks, smoke tests, integration outputs. |

## 23.4.2 Approval Rules

1. All mandatory review tracks must pass.
2. Review decisions must be recorded by assigned reviewers.
3. Rejection or change request requires reason.
4. Approval cannot proceed with unresolved blockers/errors.
5. Warning findings must be resolved, acknowledged, or waived according to policy.
6. Final approver must satisfy SOD checks.
7. Approval must compute or confirm version hash.

---

# 23.5 Activating an STD Version

## 23.5.1 Activation Steps

1. STD version is Approved.
2. Activator reviews activation summary.
3. System confirms all activation guards.
4. If replacing existing active version, system executes supersession plan.
5. New version becomes Active.
6. Previous version becomes Superseded where applicable.
7. Audit events are recorded.
8. New version becomes available for tender binding.

## 23.5.2 Supersession Modes

| Mode | Description |
|---|---|
| Replace default active version | New version becomes default for new tenders. |
| Add active variant | New version active only for specific procurement method/category/condition. |
| Emergency withdrawal and replacement | Previous version suspended and new approved version activated under special authorization. |
| No supersession | First active version for family. |

## 23.5.3 Controls

1. Activation cannot modify published tenders.
2. Activation cannot automatically migrate in-progress tender STD instances unless policy and user approval allow.
3. Existing bound tender instances must retain their version unless explicitly re-bound before publication under governed rules.
4. Published tenders cannot be re-bound.

---

# 23.6 Binding a Tender to an STD Version

## 23.6.1 Steps

1. Tender initiator selects procurement category.
2. System lists eligible active STD versions.
3. User selects STD family/version or system recommends default.
4. System creates Tender STD Instance.
5. Binding event records version, family, actor, timestamp, and applicable tender metadata.

## 23.6.2 Controls

1. Only Active versions are selectable by default.
2. Suspended versions are blocked unless explicit override policy permits.
3. Draft, rejected, archived, and superseded versions are not selectable for new tenders by default.
4. Bound version cannot change after publication.
5. If the bound version becomes superseded before publication, the system may warn the configurator but must not silently re-bind.

---

# 23.7 Configuring a Tender STD Instance

## 23.7.1 Configuration Surfaces

The user may configure only surfaces exposed by the active STD version.

Examples:

1. Tender identity.
2. Tender dates.
3. Clarification rules.
4. Participation settings.
5. Tender security settings.
6. Reservation/margin/alternative tender settings where allowed.
7. TDS values.
8. SCC values.
9. Requirements sections.
10. Technical requirements.
11. Implementation schedules.
12. System inventory or equivalent schedules.
13. Price schedule setup.
14. Evaluation criteria within permitted bounds.
15. Required forms and evidence settings.

## 23.7.2 Controls

1. Locked legal text is not editable.
2. Free text fields must be limited to approved configurable areas.
3. User-authored requirements must follow the applicable schema.
4. System-generated outputs must preserve configuration source and field history.
5. Validation must be available on demand and required before review.

---

# 23.8 Approving a Tender STD Instance

## 23.8.1 Required Review Tracks

| Review | Required when |
|---|---|
| Procurement Review | Always for publication. |
| Technical Review | Tender contains technical/functional requirements, schedules, conformance matrices, or system inventory. |
| Legal Review | SCC, contract terms, legal declarations, IP, dispute, liability, securities, or acceptance terms configured. |
| Finance Review | Price schedules, payment milestones, tender security, performance security, budget, or currency settings configured. |

## 23.8.2 Controls

1. Configuration cannot be approved with blockers/errors.
2. The final approver cannot be the sole configurator.
3. Approval must create an immutable configuration snapshot for final rendering.
4. Review comments must be preserved.

---

# 23.9 Publishing a Tender Bundle

## 23.9.1 Steps

1. Final bundle generated from approved configuration snapshot.
2. Bundle hash computed.
3. Final approval recorded.
4. Publisher publishes bundle.
5. Tender STD instance state becomes Published.
6. Published bundle becomes immutable.
7. Downstream bidder/evaluation/contract schemas are exposed to consuming modules.

## 23.9.2 Controls

1. Preview artifacts cannot be published.
2. Final artifact must be generated after approval or from approved snapshot.
3. Publication must record the exact STD version and configuration snapshot.
4. Publication must block direct post-publication edits.

---

# 23.10 Creating an Addendum

## 23.10.1 Steps

1. Addendum request created against a published tender.
2. User states reason and proposed changes.
3. System performs or assists impact analysis.
4. User confirms affected sections/fields/forms/rules/deadlines.
5. System validates addendum.
6. Required reviews occur.
7. Addendum approved.
8. Addendum artifact generated, hashed, and published.
9. Original published bundle remains immutable and linked to addendum.

## 23.10.2 Controls

1. Addendum cannot overwrite original published bundle.
2. Addendum must declare whether bidder action is required.
3. Addendum must declare whether deadlines are changed.
4. Evaluation-impacting addenda must be treated as high-risk.
5. Addenda must be visible in tender audit history.

---

# 24. Audit Event Model

## 24.1 Audit Event Categories

| Category | Examples |
|---|---|
| Source events | Upload, metadata capture, hash generation, verification, rejection, retirement. |
| Import events | Package upload, parse, schema validation, staging, import, rejection. |
| Template events | Version creation, structuring, review, approval, activation, suspension, supersession, archival. |
| Component events | Clause edit, parameter edit, rule edit, form schema edit, render block edit, validation status. |
| Tender binding events | STD version selection, binding, re-binding before publication where allowed. |
| Configuration events | Field value entry, change, deletion, validation, review submission. |
| Review events | Assignment, review pass, change request, rejection, approval. |
| Render events | Preview generation, final generation, render failure, hash generation. |
| Publication events | Tender bundle publication, addendum publication. |
| Addendum events | Request, impact analysis, approval, publication, withdrawal, rejection. |
| Validation events | Finding opened, resolved, acknowledged, waived, reopened, closed. |
| Access events | Read/export of sensitive objects, audit access, investigation export. |
| Override events | Emergency override, technical unlock, recovery action. |

## 24.2 Required Audit Fields

| Field | Required | Notes |
|---|---|---|
| Audit event ID | Yes | Unique. |
| Event type | Yes | Controlled taxonomy. |
| Object type | Yes | Domain object name. |
| Object ID | Yes | Record ID. |
| Parent object ID | Conditional | Required for child objects. |
| Actor user ID | Conditional | Required for human actions. |
| Actor service ID | Conditional | Required for service actions. |
| Role used | Yes | Role/permission context. |
| From state | Conditional | Required for state transitions. |
| To state | Conditional | Required for state transitions. |
| Timestamp | Yes | System time. |
| Reason/comment | Conditional | Required for rejection, waiver, override, cancellation, retirement. |
| Request/session metadata | Yes where available | IP/device/session or system job reference. |
| Previous hash | Conditional | Hash before change. |
| New hash | Conditional | Hash after change. |
| Validation result reference | Conditional | Required for validation transitions. |
| Approval request reference | Conditional | Required for approval transitions. |
| Source reference | Conditional | Required where source-derived. |

## 24.3 Audit Immutability

1. Audit events cannot be edited by business users.
2. Audit correction must be by append-only correction event.
3. Audit deletion is prohibited within retention period.
4. Audit export must itself be audited.
5. Audit retention must satisfy legal and organizational policy.

---

# 25. Hashing and Evidentiary Controls

## 25.1 Hash Targets

| Target | Required timing |
|---|---|
| Source document file | On upload/registration. |
| Import package | On upload and before import commit. |
| STD template version | Before approval and activation. |
| Locked clause text | On component validation and activation. |
| Render block set | Before activation. |
| Tender configuration snapshot | Before final generation. |
| Final generated bundle | Before publication. |
| Published addendum | Before publication. |
| Export package | On export generation. |

## 25.2 Hash Rules

1. Hash algorithm must be recorded.
2. Hash input canonicalization must be deterministic for structured records.
3. A changed hash after approval requires review of the changed object.
4. Published artifact hashes must never be overwritten.
5. Hash mismatch must produce a blocker finding.

---

# 26. Notifications and Task Routing

## 26.1 Notification Events

| Event | Recipients |
|---|---|
| Source submitted for verification | Assigned source reviewers. |
| Import validation failed | Import operator and template author. |
| STD version submitted for review | Assigned reviewers. |
| Review changes requested | Template author or tender configurator. |
| STD version ready for approval | STD approver. |
| STD version approved | Activator and registry admin. |
| STD version activated | Template administrators and subscribed procuring entities if configured. |
| Tender STD submitted for review | Assigned PE reviewers. |
| Tender STD approved for generation | Configurator/render service. |
| Final bundle generated | PE approver/publisher. |
| Tender bundle published | Tender stakeholders and downstream modules. |
| Addendum requested | PE reviewers/approvers. |
| Addendum published | Tender stakeholders and downstream modules. |
| Validation blocker created | Owner and responsible role. |
| Emergency override used | Security administrator, audit role, governance lead. |

## 26.2 Notification Controls

1. Notifications must not grant permissions.
2. Notification links must respect access control.
3. Sensitive content should not be exposed in email/SMS notification body unless policy permits.
4. Missed notifications must not invalidate state transitions, but task queues must remain accurate.

---

# 27. Emergency Override Model

## 27.1 Purpose

Emergency override exists for rare technical or governance recovery situations. It must not become a shortcut for normal approval.

## 27.2 Permitted Emergency Scenarios

| Scenario | Permitted? | Notes |
|---|---|---|
| Recover stuck workflow caused by technical failure | Yes | Must preserve content and audit. |
| Recompute missing hash after failed job | Yes | Must record reason and before/after state. |
| Restore mistakenly archived draft before activation | Conditional | Requires approval. |
| Edit active legal clause text | No by default | Requires new version. |
| Edit published tender bundle | No | Use addendum. |
| Delete audit events | No | Prohibited. |
| Bypass validation blockers for activation | No by default | Only explicit legal/system emergency policy could allow, with post-audit. |

## 27.3 Emergency Override Requirements

1. Actor must have emergency override permission.
2. Reason is mandatory.
3. Object reference is mandatory.
4. Approval reference is mandatory unless break-glass policy permits post-approval.
5. Before and after values must be captured where applicable.
6. Audit event must be high severity.
7. Notification must be sent to audit/security/governance roles.
8. Post-event review task must be created.

---

# 28. State-Transition Completeness Check

This section explicitly verifies that the approval/state-transition design is complete enough to proceed to seed data, smoke contracts, APIs, and UI design.

## 28.1 Template Version Governance Completeness

| Requirement | Covered? | Location |
|---|---:|---|
| Draft creation state | Yes | SM-04 |
| Structuring state | Yes | SM-04 |
| Review states | Yes | SM-04 and SM-06 |
| Legal review | Yes | SM-04, SM-06 |
| Procurement standards review | Yes | SM-04, SM-06 |
| Technical schema review | Yes | SM-04, SM-06 |
| Change request loop | Yes | SM-04, SM-06 |
| Approval state | Yes | SM-04, SM-06 |
| Activation state | Yes | SM-04 |
| Suspension state | Yes | SM-04 |
| Supersession state | Yes | SM-04 |
| Archival state | Yes | SM-04 |
| Rejection state | Yes | SM-04 |
| Activation guards | Yes | Section 12.5 |
| SOD rules | Yes | Section 7 |
| Audit events | Yes | Sections 12 and 24 |

## 28.2 Tender Configuration Governance Completeness

| Requirement | Covered? | Location |
|---|---:|---|
| Tender binding | Yes | SM-07 |
| Configuration state | Yes | SM-07 |
| Validation failed state | Yes | SM-07 |
| Review states | Yes | SM-07 |
| Approval for generation | Yes | SM-07 |
| Final bundle generation | Yes | SM-07, SM-08 |
| Approval for publication | Yes | SM-07, SM-08 |
| Publication state | Yes | SM-07, SM-08 |
| Published immutability | Yes | Sections 3, 15, 16 |
| Addendum requirement after publication | Yes | SM-07, SM-09 |
| Tender configuration guards | Yes | Section 15.5 |
| SOD rules | Yes | Section 7 |
| Audit events | Yes | Sections 15, 16, 24 |

## 28.3 Addendum Governance Completeness

| Requirement | Covered? | Location |
|---|---:|---|
| Addendum request | Yes | SM-09 |
| Impact analysis | Yes | SM-09 |
| Validation | Yes | SM-09, SM-10 |
| Review | Yes | SM-09 |
| Approval | Yes | SM-09 |
| Publication | Yes | SM-09 |
| Original bundle immutability | Yes | SM-08, SM-09 |
| Affected object identification | Yes | Section 17.4 |
| Addendum guards | Yes | Section 17.5 |

## 28.4 Permission Completeness

| Requirement | Covered? | Location |
|---|---:|---|
| Template roles | Yes | Section 5.3 |
| Procuring entity roles | Yes | Section 5.4 |
| Service roles | Yes | Section 5.6 |
| Template permission matrix | Yes | Section 21.2 |
| Tender permission matrix | Yes | Section 21.3 |
| Service permission matrix | Yes | Section 21.4 |
| Authority levels | Yes | Section 6 |
| Segregation of duties | Yes | Section 7 |
| Emergency override | Yes | Section 27 |

## 28.5 Finding

The approval/state-transition design is sufficiently complete to proceed to the next artifact: **STD Engine Core Seed Data and Smoke Contracts**.

No implementation should proceed without implementing the state guards, SOD checks, audit event generation, and published artifact immutability defined in this document.

---

# 29. Smoke Contracts for Governance

These smoke contracts shall be turned into automated tests or implementation checklist items.

## 29.1 Template Governance Smoke Contracts

| ID | Contract | Expected result |
|---|---|---|
| GOV-SM-001 | Attempt to activate a template version with unverified source document | Blocked |
| GOV-SM-002 | Attempt to activate a template version with unresolved blocker finding | Blocked |
| GOV-SM-003 | Attempt to activate a template version without legal review | Blocked |
| GOV-SM-004 | Attempt to activate a template version without procurement review | Blocked |
| GOV-SM-005 | Attempt to activate a template version without technical schema review | Blocked |
| GOV-SM-006 | Attempt to activate a template version without version hash | Blocked |
| GOV-SM-007 | Attempt to edit active clause text | Blocked |
| GOV-SM-008 | Attempt to delete a version used by a tender | Blocked |
| GOV-SM-009 | Activate replacement version | Previous active version becomes Superseded |
| GOV-SM-010 | View historical tender using superseded STD version | Historical version remains available |

## 29.2 Tender Governance Smoke Contracts

| ID | Contract | Expected result |
|---|---|---|
| GOV-SM-011 | Attempt to bind tender to draft STD version | Blocked |
| GOV-SM-012 | Attempt to bind tender to active STD version | Allowed |
| GOV-SM-013 | Attempt to publish tender with missing mandatory TDS value | Blocked |
| GOV-SM-014 | Attempt to edit locked ITT clause in tender configuration | Blocked |
| GOV-SM-015 | Attempt to approve own tender configuration as sole approver | Blocked |
| GOV-SM-016 | Generate preview from incomplete configuration | Allowed or warning according to policy, marked non-final |
| GOV-SM-017 | Generate final bundle from approved configuration | Allowed; hash created |
| GOV-SM-018 | Publish final bundle without approval | Blocked |
| GOV-SM-019 | Edit published bundle directly | Blocked |
| GOV-SM-020 | Request post-publication change | Addendum workflow required |

## 29.3 Addendum Governance Smoke Contracts

| ID | Contract | Expected result |
|---|---|---|
| GOV-SM-021 | Request addendum without reason | Blocked |
| GOV-SM-022 | Addendum affects technical requirement but no impact object declared | Blocked |
| GOV-SM-023 | Addendum affects evaluation criteria without procurement review | Blocked |
| GOV-SM-024 | Addendum affects SCC without legal review | Blocked |
| GOV-SM-025 | Publish approved addendum | New addendum artifact published; original bundle preserved |
| GOV-SM-026 | View original tender bundle after addendum | Original remains retrievable and immutable |

## 29.4 Audit Smoke Contracts

| ID | Contract | Expected result |
|---|---|---|
| GOV-SM-027 | Reject a review item without reason | Blocked |
| GOV-SM-028 | Approve template version | Approval event created |
| GOV-SM-029 | Activate template version | Activation event and version hash recorded |
| GOV-SM-030 | Publish tender bundle | Publication event and bundle hash recorded |
| GOV-SM-031 | Export active STD package | Export event and export hash recorded |
| GOV-SM-032 | Emergency override action | High-severity audit event and post-review task created |

---

# 30. Implementation Requirements

## 30.1 Backend Requirements

1. Implement state fields as controlled enums.
2. Implement transition services rather than allowing direct state writes.
3. Enforce guards in backend services, not only UI.
4. Generate audit events inside transaction boundaries.
5. Prevent active/published object mutation at database/service layer.
6. Implement SOD checks during approval and publication transitions.
7. Implement validation severity handling.
8. Implement deterministic hashing for structured records.
9. Implement append-only audit events.
10. Implement object-level and tenant-level permission checks.

## 30.2 Frontend Requirements

1. UI must show current state and allowed next actions.
2. UI must hide or disable actions not permitted by role/state.
3. UI must display blockers/errors before submission, approval, activation, or publication.
4. UI must require reasons for rejection, cancellation, waiver, suspension, archival, and override.
5. UI must clearly distinguish preview artifacts from final artifacts.
6. UI must clearly distinguish master STD administration from tender STD configuration.
7. UI must expose audit history to authorized users.
8. UI must prevent editing locked sections even before backend validation.

## 30.3 Database Requirements

1. Store state, state timestamps, and responsible actors.
2. Store version hash, source hash, package hash, configuration snapshot hash, and bundle hash where applicable.
3. Store review decisions as separate child records or audit-linked records.
4. Store validation findings with severity and state.
5. Store approval requests and review tracks.
6. Store immutable snapshots for active versions and published bundles.
7. Use database constraints where practical for uniqueness and referential integrity.
8. Use soft deletion or archival only for governed objects; physical deletion must be blocked after use.

## 30.4 API Requirements

1. Provide explicit transition endpoints/actions.
2. Reject direct state mutation requests.
3. Return allowed actions for object and user.
4. Return validation summary and findings.
5. Return approval status and pending review tasks.
6. Return audit event list for authorized users.
7. Return immutable snapshot references for published artifacts.
8. Return clear error messages for guard failures.

---

# 31. Acceptance Criteria

## 31.1 Template Governance Acceptance Criteria

The implementation is acceptable when:

1. A verified source document can be registered and hashed.
2. An import package can be staged, validated, and imported into a draft version.
3. A draft version can proceed through required reviews.
4. Reviewers can approve, reject, or request changes with recorded reasons.
5. A version cannot be activated without required approvals.
6. A version cannot be activated with unresolved blockers/errors.
7. An active version cannot be edited.
8. A replacement version can supersede a previous active version without altering historical usage.
9. Auditors can view source, approval, activation, and hash records.

## 31.2 Tender Governance Acceptance Criteria

The implementation is acceptable when:

1. A tender can bind only to an active STD version by default.
2. A tender configuration can expose only allowed parameters and configurable surfaces.
3. Locked sections cannot be edited through the tender UI or API.
4. Tender validation blocks approval where mandatory data is missing or inconsistent.
5. A tender configuration can proceed through required reviews.
6. A final bundle can be generated only from an approved configuration snapshot.
7. A final bundle cannot be published without approval.
8. A published bundle is immutable.
9. Any post-publication change is forced through addendum workflow.

## 31.3 Addendum Governance Acceptance Criteria

The implementation is acceptable when:

1. Addendum requests can be created only against published tenders.
2. Addendum reason and impact analysis are mandatory.
3. Review requirements depend on impact category.
4. Addendum publication creates a new immutable artifact.
5. Original tender bundle remains retrievable and unchanged.
6. Addendum audit history shows request, impact, review, approval, publication, and artifact hash.

## 31.4 Audit Acceptance Criteria

The implementation is acceptable when:

1. All material transitions create audit events.
2. Audit events are append-only.
3. Hashes are recorded for source, version, final bundle, addendum, and export artifacts.
4. Rejection, waiver, cancellation, archival, suspension, and override require reasons.
5. Emergency overrides create high-severity audit records and post-review tasks.

---

# 32. Open Design Decisions

The following decisions may be finalized during seed data and implementation design:

| Decision | Recommended default |
|---|---|
| Parallel vs sequential review tracks for template activation | Support parallel internally, but present clear required-track completion. |
| Whether one user may hold multiple reviewer roles | Allow globally, but enforce SOD per object/action. |
| Whether warnings require acknowledgement before approval | Yes for production activation/publication. |
| Whether suspended active versions may be selected with override | Default no; allow only policy-controlled override. |
| Whether in-progress unpublished tenders may migrate to newer STD version | Allow only before publication, with explicit re-bind workflow and audit. |
| Whether generated preview artifacts expire | Yes, according to retention policy. |
| Whether render-only typo correction after publication can bypass full addendum | Default no; if allowed, require controlled correction notice and audit. |

---

# 33. Risks and Controls

| Risk | Control |
|---|---|
| Users bypass STD governance by uploading custom tender documents | Require tender creation to bind to active STD version and generate official bundle. |
| Active STD text is changed silently | Enforce immutability and hash checks. |
| Evaluation criteria drift from published tender | Generate evaluation schema from published STD configuration snapshot. |
| Addenda do not update affected bidder/evaluation schemas | Require impact analysis and regenerated affected outputs. |
| Same user authors and approves critical content | Enforce SOD checks. |
| Old tenders break when STD is superseded | Preserve bound STD version and published bundle snapshots. |
| Audit records are incomplete | Generate audit events inside transition services. |
| Service accounts mutate business content | Restrict service roles to specific actions. |
| Emergency override becomes routine | Require reason, approval reference, high-severity audit, and post-review. |

---

# 34. Next Artifact

The next artifact should be:

**STD Engine Core Module - Seed Data and Smoke Contracts**

That artifact should define:

1. Base roles.
2. Permission sets.
3. State enum seed data.
4. Transition action seed data.
5. Audit event type seed data.
6. Validation severity seed data.
7. Mutability type seed data.
8. Source traceability mode seed data.
9. Review track seed data.
10. Initial smoke contract test cases.
11. Minimal development seed package for `KE-PPRA-IT`.

After seed data and smoke contracts, proceed to the Cursor implementation pack.

