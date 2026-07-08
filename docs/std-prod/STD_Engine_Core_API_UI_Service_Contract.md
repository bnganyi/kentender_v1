# STD Engine Core Module - API, UI, and Service Contract

**Project:** KenTender e-Procurement System  
**Module:** Standard Tender Document Engine Core  
**Document type:** API, UI, and Service Contract  
**Document status:** Draft for implementation review  
**Version:** 0.1  
**Prepared date:** 2026-07-07  
**Preceding artifact:** `STD_Engine_Core_Seed_Data_and_Smoke_Contracts.md`  
**Next artifact:** STD Engine Core Cursor Implementation Pack  

---

## 1. Purpose

This document defines the implementation-facing API, UI, and service contracts for the Standard Tender Document Engine Core Module.

It translates the approved Pre-PRD, PRD, domain model, governance model, seed data, and smoke contracts into a practical contract for backend services, frontend screens, state transitions, import/export operations, validation, rendering, audit, hashing, tender binding, and addendum handling.

The contract is intentionally generalized. It must support multiple Standard Tender Document families and versions. It must not be hard-coded for the Information Technology STD, the WORKS STD, or any individual Procuring Entity tender. STD-specific behavior shall be represented through data records, schemas, rules, render profiles, and seed packages.

---

## 2. Design Position

The STD Engine Core is the authoritative template governance and generation layer for Standard Tender Documents.

It is not a file repository.

It is not a free-text tender authoring tool.

It is not a replacement for Tender Management, Supplier Submission, Evaluation, or Contract Management.

It provides the governed, versioned, traceable, renderable, and reusable legal/procedural template layer consumed by those modules.

---

## 3. Implementation Boundary

### 3.1 In Scope

This contract covers:

1. STD family management.
2. STD version lifecycle management.
3. Source document registration and hashing.
4. Package import and export.
5. Section and clause management.
6. Parameter management.
7. Rule management.
8. Form schema management.
9. Evidence requirement management.
10. Render block and render profile management.
11. Approval workflow services.
12. State-transition services.
13. Validation services.
14. Tender binding services.
15. Tender STD configuration services.
16. Generated bundle services.
17. Addendum impact services.
18. Audit-event services.
19. Hash verification services.
20. Administrative UI screens.
21. Tender configuration UI screens.
22. Review and approval UI screens.
23. API payload contracts.
24. Service-layer responsibilities.
25. Implementation task breakdown.

### 3.2 Out of Scope

This contract does not implement:

1. The full IT STD extraction matrix.
2. The full IT STD seed package.
3. The Supplier Portal submission UI.
4. Bid encryption or bid opening ceremonies.
5. Evaluation committee scoring workflow beyond STD-generated evaluation structures.
6. Contract management after contract formation.
7. Payments, invoices, contract performance, or asset management.
8. External PPRA publishing APIs unless later required.
9. OCR extraction from official STD documents.
10. AI-assisted clause extraction as a production dependency.

---

## 4. Non-Negotiable Controls

The following controls must be implemented before the module is considered production-ready.

| Control | Required behavior |
|---|---|
| Active STD immutability | Active STD versions cannot be edited directly. |
| Used STD immutability | Any STD version used by at least one tender cannot be deleted. |
| Locked clause protection | Locked clauses cannot be modified in tender configuration. |
| Source traceability | Every section, clause, parameter, rule, form, and render block must trace to a source document or approved system-origin record. |
| Approval enforcement | Draft or unapproved versions cannot be activated. |
| Activation validation | STD version cannot become Active unless required components pass validation. |
| Tender binding | Tender instances must bind to one active STD version. |
| Generated bundle immutability | Published tender bundles cannot be edited; changes require addendum. |
| Addendum impact tracking | Addenda must identify affected sections, forms, parameters, rules, and rendered outputs. |
| Hash verification | Source documents, packages, clauses, and generated bundles must be hashable and verifiable. |
| Audit logging | Material actions must create tamper-evident audit events. |
| Fail-closed validation | Ambiguous or inconsistent STD data must block activation, publication, or generation as appropriate. |

---

## 5. Approval and State-Transition Completeness Check

This artifact confirms that approval and state-transition design has been addressed before API/UI implementation.

The APIs and UI must enforce the following state models:

1. STD Version lifecycle.
2. Source Document lifecycle.
3. Import Package lifecycle.
4. Component lifecycle.
5. Tender STD Instance lifecycle.
6. Generated Bundle lifecycle.
7. Addendum Impact lifecycle.

No screen, endpoint, or background service may bypass these state models.

Where a caller attempts to modify a record outside the permitted state, the system must return a controlled validation error and create an audit event for blocked material operations.

---

## 6. Architecture Overview

### 6.1 Logical Components

```text
STD Engine Core
├── Administration UI
├── Tender Configuration UI
├── Review and Approval UI
├── Import/Export Service
├── Template Registry Service
├── Source Trace Service
├── Component Service
├── Validation Service
├── Rule Evaluation Service
├── Render Service
├── Tender Binding Service
├── Generated Bundle Service
├── Addendum Impact Service
├── Approval Workflow Service
├── Audit Service
├── Hash Service
└── Notification Service
```

### 6.2 Runtime Flow

```text
Official STD Source Document
        ↓
Source Document Registration and Hashing
        ↓
STD Package Import
        ↓
Component Validation
        ↓
Internal Review
        ↓
Legal / Procurement Approval
        ↓
Activation
        ↓
Tender Binding
        ↓
Tender Configuration
        ↓
Configuration Validation
        ↓
Tender Bundle Rendering
        ↓
Publication
        ↓
Addendum or Supersession if changes are required
```

---

## 7. API Design Principles

### 7.1 API Style

The contract is expressed as REST-style APIs. The same contracts may be implemented as Frappe methods, Django REST endpoints, Laravel controllers, NestJS services, or another equivalent architecture.

Where the platform uses document-style APIs, these endpoints may be mapped to DocType methods and whitelisted service methods.

### 7.2 API Conventions

| Convention | Standard |
|---|---|
| Base path | `/api/std-engine/v1` |
| Payload format | JSON |
| Date-time format | ISO 8601 UTC timestamp |
| IDs | Stable server-generated UUID or framework-equivalent immutable ID |
| Idempotency | Required for imports, activation, render, publication, and addendum generation |
| Pagination | Cursor or page-based pagination required for lists |
| Sorting | Explicit `sort` query parameter |
| Filtering | Explicit `filter` query parameter or named query fields |
| Soft delete | Only allowed where records are unused and not legally material |
| Audit | All mutating endpoints must call Audit Service |
| Authorization | Role and permission checked before business logic execution |
| State validation | State transition checked before mutation |

### 7.3 Standard Response Envelope

```json
{
  "success": true,
  "data": {},
  "warnings": [],
  "errors": [],
  "meta": {
    "request_id": "req_...",
    "timestamp": "2026-07-07T00:00:00Z"
  }
}
```

### 7.4 Standard Error Envelope

```json
{
  "success": false,
  "data": null,
  "warnings": [],
  "errors": [
    {
      "code": "STD_VERSION_NOT_EDITABLE",
      "message": "Active STD versions cannot be edited.",
      "field": null,
      "severity": "BLOCKER",
      "details": {
        "std_version_id": "...",
        "current_state": "ACTIVE"
      }
    }
  ],
  "meta": {
    "request_id": "req_...",
    "timestamp": "2026-07-07T00:00:00Z"
  }
}
```

### 7.5 Error Severity

| Severity | Meaning |
|---|---|
| `INFO` | Non-blocking informational message. |
| `WARNING` | Non-blocking issue requiring user awareness. |
| `BLOCKER` | Operation cannot proceed. |
| `LEGAL_BLOCKER` | Operation cannot proceed because legal/procedural integrity would be violated. |
| `SYSTEM_BLOCKER` | Operation cannot proceed because system integrity would be violated. |

---

## 8. Authentication and Authorization Contract

### 8.1 Authentication

All endpoints require authenticated users except public hash verification endpoints, if exposed later.

### 8.2 Authorization Layers

Authorization must be evaluated through three layers:

1. Role-based permission.
2. Record-state permission.
3. Ownership or organizational-scope permission.

### 8.3 Authorization Example

A Procurement Officer may configure a tender STD instance but may not activate a master STD version.

A Template Administrator may import and structure a Draft STD version but may not approve their own activation if segregation of duties is enabled.

A Legal Reviewer may approve locked legal text but may not configure PE-specific tender values unless separately granted.

### 8.4 Permission Failure Response

```json
{
  "success": false,
  "errors": [
    {
      "code": "PERMISSION_DENIED",
      "message": "You do not have permission to activate STD versions.",
      "severity": "BLOCKER"
    }
  ]
}
```

---

## 9. Core API Resources

### 9.1 Resource Summary

| Resource | Purpose |
|---|---|
| `/std-families` | Manage STD families. |
| `/std-versions` | Manage versioned STD templates. |
| `/source-documents` | Register official source documents. |
| `/import-packages` | Import structured STD packages. |
| `/sections` | Manage STD section hierarchy. |
| `/clauses` | Manage clause records and locked text. |
| `/parameters` | Manage configurable fields. |
| `/rules` | Manage validation, activation, calculation, and rendering rules. |
| `/forms` | Manage form schemas. |
| `/form-fields` | Manage form field schemas. |
| `/evidence-requirements` | Manage document/evidence obligations. |
| `/render-blocks` | Manage deterministic document render blocks. |
| `/render-profiles` | Manage render profiles and output formats. |
| `/approvals` | Manage reviews and approval actions. |
| `/validations` | Execute validation checks. |
| `/tender-instances` | Bind active STD versions to tenders. |
| `/configuration-values` | Store tender-specific STD values. |
| `/generated-bundles` | Render and publish generated tender documents. |
| `/addendum-impacts` | Track post-publication changes. |
| `/audit-events` | Read audit events. |
| `/hashes` | Verify hashes. |

---

## 10. STD Family APIs

### 10.1 Create STD Family

`POST /api/std-engine/v1/std-families`

Creates a new STD family, such as Information Technology, WORKS, Goods, Consulting Services, or Non-Consulting Services.

#### Request

```json
{
  "code": "KE-PPRA-IT",
  "name": "STD for Procurement of Information Technology",
  "source_authority_code": "KE-PPRA",
  "procurement_category": "INFORMATION_TECHNOLOGY",
  "description": "Standard Tender Document family for procurement of Information Technology design, supply, installation, and related services.",
  "is_active": true
}
```

#### Required Validation

| Rule | Behavior |
|---|---|
| Code unique | Block duplicate family codes. |
| Source authority exists | Block unknown authority. |
| Procurement category valid | Block invalid category. |

### 10.2 List STD Families

`GET /api/std-engine/v1/std-families`

Supports filters:

```text
?source_authority_code=KE-PPRA&procurement_category=INFORMATION_TECHNOLOGY&is_active=true
```

### 10.3 Read STD Family

`GET /api/std-engine/v1/std-families/{std_family_id}`

### 10.4 Update STD Family

`PATCH /api/std-engine/v1/std-families/{std_family_id}`

Allowed only if the family has no active locked dependency requiring change control, or the update is administrative metadata only.

---

## 11. STD Version APIs

### 11.1 Create STD Version

`POST /api/std-engine/v1/std-versions`

#### Request

```json
{
  "std_family_id": "uuid",
  "version_code": "KE-PPRA-IT-2022-04",
  "version_label": "April 2022",
  "effective_from": "2022-04-01",
  "effective_to": null,
  "source_document_ids": ["uuid"],
  "initial_state": "DRAFT",
  "description": "Initial structured version of the IT STD."
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "std_version_id": "uuid",
    "state": "DRAFT",
    "version_code": "KE-PPRA-IT-2022-04"
  }
}
```

### 11.2 Read STD Version

`GET /api/std-engine/v1/std-versions/{std_version_id}`

Returned object must include:

1. Family metadata.
2. Lifecycle state.
3. Activation status.
4. Source document links.
5. Component counts.
6. Validation status.
7. Approval status.
8. Usage count.
9. Current hash summary.

### 11.3 List STD Versions

`GET /api/std-engine/v1/std-versions`

Common filters:

```text
?std_family_id=...&state=ACTIVE
?version_code=KE-PPRA-IT-2022-04
?procurement_category=INFORMATION_TECHNOLOGY
?used_by_tender=true
```

### 11.4 Update Draft STD Version Metadata

`PATCH /api/std-engine/v1/std-versions/{std_version_id}`

Allowed only in states:

1. `DRAFT`
2. `STRUCTURING`
3. `RETURNED_FOR_CORRECTION`

Blocked in:

1. `APPROVED`
2. `ACTIVE`
3. `SUPERSEDED`
4. `ARCHIVED`

### 11.5 Transition STD Version State

`POST /api/std-engine/v1/std-versions/{std_version_id}/transition`

#### Request

```json
{
  "action": "SUBMIT_FOR_INTERNAL_REVIEW",
  "comment": "Initial structuring complete. Ready for review.",
  "idempotency_key": "optional-client-key"
}
```

#### Supported Actions

| Action | From state | To state |
|---|---|---|
| `START_STRUCTURING` | `DRAFT` | `STRUCTURING` |
| `SUBMIT_FOR_INTERNAL_REVIEW` | `STRUCTURING` | `INTERNAL_REVIEW` |
| `RETURN_FOR_CORRECTION` | `INTERNAL_REVIEW`, `LEGAL_REVIEW`, `PROCUREMENT_REVIEW` | `RETURNED_FOR_CORRECTION` |
| `RESUBMIT_FOR_REVIEW` | `RETURNED_FOR_CORRECTION` | Previous review state or `INTERNAL_REVIEW` |
| `APPROVE_INTERNAL_REVIEW` | `INTERNAL_REVIEW` | `LEGAL_REVIEW` or `PROCUREMENT_REVIEW` |
| `APPROVE_LEGAL_REVIEW` | `LEGAL_REVIEW` | `PROCUREMENT_REVIEW` or `APPROVED` |
| `APPROVE_PROCUREMENT_REVIEW` | `PROCUREMENT_REVIEW` | `APPROVED` |
| `ACTIVATE` | `APPROVED` | `ACTIVE` |
| `SUPERSEDE` | `ACTIVE` | `SUPERSEDED` |
| `ARCHIVE` | `SUPERSEDED` | `ARCHIVED` |

#### Transition Guardrails

| Guardrail | Required behavior |
|---|---|
| Required components complete | Block activation if incomplete. |
| Validation passes | Block activation on blockers. |
| Required approvals present | Block activation without approvals. |
| Hash generated | Block activation if hash cannot be computed. |
| Segregation of duties | Block self-approval where enabled. |
| Used active version | Cannot be archived directly. |

---

## 12. Source Document APIs

### 12.1 Register Source Document

`POST /api/std-engine/v1/source-documents`

Registers an official source document file and computes hash metadata.

#### Request

```json
{
  "source_authority_code": "KE-PPRA",
  "title": "STD for Procurement of Information Technology",
  "document_type": "OFFICIAL_STD",
  "file_reference": "file-storage-key-or-attachment-id",
  "document_date": "2022-04-01",
  "language": "en",
  "notes": "Official IT STD source document."
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "source_document_id": "uuid",
    "state": "REGISTERED",
    "sha256_hash": "...",
    "page_count": 181,
    "file_size_bytes": 4800000
  }
}
```

### 12.2 Verify Source Document Hash

`POST /api/std-engine/v1/source-documents/{source_document_id}/verify-hash`

Returns whether the current stored file hash matches the registered hash.

### 12.3 Link Source Document to STD Version

`POST /api/std-engine/v1/std-versions/{std_version_id}/source-documents`

#### Request

```json
{
  "source_document_id": "uuid",
  "relationship_type": "PRIMARY_SOURCE"
}
```

---

## 13. Import Package APIs

### 13.1 Upload Import Package

`POST /api/std-engine/v1/import-packages`

Imports a structured package generated from a source STD.

#### Request

```json
{
  "std_version_id": "uuid",
  "package_reference": "file-storage-key",
  "package_format": "SPLIT_JSON_PACKAGE",
  "package_version": "1.0",
  "idempotency_key": "KE-PPRA-IT-2022-04-import-001"
}
```

### 13.2 Validate Import Package

`POST /api/std-engine/v1/import-packages/{import_package_id}/validate`

Validation must check:

1. Manifest exists.
2. Family code matches target STD version.
3. Version code matches target STD version.
4. Required modules exist.
5. Section references resolve.
6. Clause references resolve.
7. Parameter references resolve.
8. Rule references resolve.
9. Form references resolve.
10. Render references resolve.
11. Source trace references resolve.
12. Duplicate codes are blocked.
13. Hashes match package manifest.

### 13.3 Apply Import Package

`POST /api/std-engine/v1/import-packages/{import_package_id}/apply`

Allowed only after package validation passes.

#### Request

```json
{
  "mode": "CREATE_OR_REPLACE_DRAFT_COMPONENTS",
  "comment": "Apply validated IT STD package to draft version."
}
```

#### Modes

| Mode | Meaning |
|---|---|
| `CREATE_ONLY` | Create new components; fail on duplicates. |
| `CREATE_OR_REPLACE_DRAFT_COMPONENTS` | Replace components only while STD version is editable. |
| `DRY_RUN` | Validate and preview changes without writing. |

### 13.4 Export STD Package

`POST /api/std-engine/v1/std-versions/{std_version_id}/export-package`

Exports a normalized STD version to a structured package.

#### Request

```json
{
  "format": "SPLIT_JSON_PACKAGE",
  "include_source_trace": true,
  "include_hashes": true,
  "include_inactive_components": false
}
```

---

## 14. Section APIs

### 14.1 Create Section

`POST /api/std-engine/v1/sections`

#### Request

```json
{
  "std_version_id": "uuid",
  "parent_section_id": null,
  "section_code": "PART_1_SECTION_I",
  "title": "Instructions to Tenderers",
  "section_type": "ITT",
  "mutability_type": "LOCKED",
  "display_order": 10,
  "render_order": 10,
  "source_trace": {
    "source_document_id": "uuid",
    "page_start": 15,
    "page_end": 27,
    "source_anchor": "Section I - Instructions to Tenderers"
  }
}
```

### 14.2 Reorder Sections

`POST /api/std-engine/v1/std-versions/{std_version_id}/sections/reorder`

#### Request

```json
{
  "section_order": [
    {"section_id": "uuid", "display_order": 10, "render_order": 10},
    {"section_id": "uuid", "display_order": 20, "render_order": 20}
  ]
}
```

Blocked if STD version is not editable.

### 14.3 Read Section Tree

`GET /api/std-engine/v1/std-versions/{std_version_id}/section-tree`

Returns hierarchical section tree with counts for clauses, parameters, forms, rules, and render blocks.

---

## 15. Clause APIs

### 15.1 Create Clause

`POST /api/std-engine/v1/clauses`

#### Request

```json
{
  "std_version_id": "uuid",
  "section_id": "uuid",
  "clause_code": "ITT_3_1",
  "title": "Fraud and Corruption",
  "clause_number": "3.1",
  "mutability_type": "LOCKED",
  "content_format": "MARKDOWN",
  "content": "The Procuring Entity requires compliance with applicable anti-corruption provisions...",
  "parameter_refs": [],
  "source_trace": {
    "source_document_id": "uuid",
    "page_start": 15,
    "page_end": 15,
    "source_anchor": "3. Fraud and Corruption"
  }
}
```

### 15.2 Update Clause

`PATCH /api/std-engine/v1/clauses/{clause_id}`

Allowed only when:

1. Parent STD version is editable.
2. Clause is not part of an Active version.
3. User has required permission.
4. Change reason is supplied for legal text changes.

### 15.3 Compute Clause Hash

`POST /api/std-engine/v1/clauses/{clause_id}/compute-hash`

Computes normalized hash for clause content and source trace.

### 15.4 Compare Clauses

`GET /api/std-engine/v1/clauses/{clause_id}/diff?compare_to_clause_id={id}`

Returns text and metadata diff.

---

## 16. Parameter APIs

### 16.1 Create Parameter

`POST /api/std-engine/v1/parameters`

#### Request

```json
{
  "std_version_id": "uuid",
  "section_id": "uuid",
  "parameter_code": "TDS_TENDER_VALIDITY_DAYS",
  "label": "Tender validity period in days",
  "description": "Number of days tenders remain valid from tender opening or submission deadline as specified by the STD.",
  "parameter_type": "INTEGER",
  "required": true,
  "default_value": null,
  "allowed_values": null,
  "validation_schema": {
    "minimum": 1,
    "maximum": 365
  },
  "configuration_stage": "TENDER_PREPARATION",
  "mutability_type": "CONFIGURABLE",
  "source_trace": {
    "source_document_id": "uuid",
    "page_start": 21,
    "page_end": 27,
    "source_anchor": "Tender Data Sheet"
  }
}
```

### 16.2 List Parameters for STD Version

`GET /api/std-engine/v1/std-versions/{std_version_id}/parameters`

Filters:

```text
?section_id=...&configuration_stage=TENDER_PREPARATION&required=true
```

### 16.3 Update Parameter Schema

`PATCH /api/std-engine/v1/parameters/{parameter_id}`

Allowed only when STD version is editable.

### 16.4 Preview Parameter Usage

`GET /api/std-engine/v1/parameters/{parameter_id}/usage`

Returns clauses, rules, forms, render blocks, and tender configuration values referencing the parameter.

---

## 17. Rule APIs

### 17.1 Create Rule

`POST /api/std-engine/v1/rules`

#### Request

```json
{
  "std_version_id": "uuid",
  "rule_code": "RULE_TENDER_SECURITY_MAX_2_PERCENT",
  "name": "Tender security shall not exceed allowed percentage of estimate",
  "rule_type": "VALIDATION",
  "scope_type": "TENDER_CONFIGURATION",
  "severity": "LEGAL_BLOCKER",
  "blocking_behavior": "BLOCK_PUBLICATION",
  "expression_language": "JSON_LOGIC",
  "expression": {
    "<=": [
      {"var": "tender_security.amount"},
      {"*": [{"var": "procurement.estimated_value"}, 0.02]}
    ]
  },
  "message": "Tender security exceeds the maximum permitted threshold.",
  "affected_parameter_codes": ["TDS_TENDER_SECURITY_AMOUNT", "PROCUREMENT_ESTIMATED_VALUE"],
  "source_trace": {
    "source_document_id": "uuid",
    "page_start": 8,
    "page_end": 8,
    "source_anchor": "Guidelines for preparing tender documents"
  }
}
```

### 17.2 Execute Rule

`POST /api/std-engine/v1/rules/{rule_id}/execute`

#### Request

```json
{
  "context_type": "TENDER_STD_INSTANCE",
  "context_id": "uuid",
  "input": {
    "tender_security": {"amount": 500000},
    "procurement": {"estimated_value": 100000000}
  }
}
```

### 17.3 Validate Rule Syntax

`POST /api/std-engine/v1/rules/validate-syntax`

#### Request

```json
{
  "expression_language": "JSON_LOGIC",
  "expression": {
    "==": [{"var": "alternative_tenders"}, false]
  }
}
```

### 17.4 Rule Execution Result

```json
{
  "success": true,
  "data": {
    "passed": true,
    "severity": "LEGAL_BLOCKER",
    "message": null,
    "affected_fields": []
  }
}
```

---

## 18. Form Schema APIs

### 18.1 Create Form Schema

`POST /api/std-engine/v1/forms`

#### Request

```json
{
  "std_version_id": "uuid",
  "section_id": "uuid",
  "form_code": "FORM_OF_TENDER",
  "title": "Form of Tender",
  "form_type": "TENDERER_SUBMISSION",
  "respondent_type": "TENDERER",
  "activation_rule_id": null,
  "required": true,
  "display_order": 10,
  "source_trace": {
    "source_document_id": "uuid",
    "page_start": 37,
    "page_end": 39,
    "source_anchor": "Form of Tender"
  }
}
```

### 18.2 Create Form Field

`POST /api/std-engine/v1/form-fields`

#### Request

```json
{
  "form_id": "uuid",
  "field_code": "TOTAL_TENDER_PRICE_EXCL_VAT",
  "label": "Total Tender Price excluding VAT",
  "field_type": "MONEY",
  "required": true,
  "display_order": 10,
  "validation_schema": {
    "currency": "KES",
    "minimum": 0
  },
  "maps_to_parameter_code": null,
  "maps_to_price_schedule_field": "grand_total_excluding_vat"
}
```

### 18.3 Read Full Form Schema

`GET /api/std-engine/v1/forms/{form_id}/schema`

Returns form metadata, fields, conditional logic, validation, evidence requirements, and render hints.

### 18.4 Preview Form

`POST /api/std-engine/v1/forms/{form_id}/preview`

Renders the form as it would appear in the generated tender document or supplier submission UI.

---

## 19. Evidence Requirement APIs

### 19.1 Create Evidence Requirement

`POST /api/std-engine/v1/evidence-requirements`

#### Request

```json
{
  "std_version_id": "uuid",
  "form_id": "uuid",
  "evidence_code": "VALID_TAX_COMPLIANCE_CERTIFICATE",
  "title": "Valid Tax Compliance Certificate",
  "evidence_type": "DOCUMENT_UPLOAD",
  "required": true,
  "respondent_type": "TENDERER",
  "validation_policy": {
    "expiry_date_required": true,
    "file_required": true,
    "allowed_file_types": ["pdf", "jpg", "png"],
    "manual_verification_required": true
  }
}
```

### 19.2 List Evidence Requirements for Tender Submission

`GET /api/std-engine/v1/tender-instances/{tender_std_instance_id}/evidence-requirements`

Returns the activated evidence obligations applicable to the tender.

---

## 20. Render Block APIs

### 20.1 Create Render Block

`POST /api/std-engine/v1/render-blocks`

#### Request

```json
{
  "std_version_id": "uuid",
  "section_id": "uuid",
  "render_block_code": "RENDER_INVITATION_TO_TENDER",
  "title": "Invitation to Tender Render Block",
  "render_block_type": "DOCUMENT_SECTION",
  "template_engine": "HANDLEBARS",
  "template": "PROCURING ENTITY: {{procuring_entity.name}}\nCONTRACT NAME: {{tender.name}}",
  "input_parameter_codes": [
    "PROCURING_ENTITY_NAME",
    "TENDER_NAME",
    "TENDER_NUMBER"
  ],
  "display_order": 10,
  "output_format": "MARKDOWN"
}
```

### 20.2 Validate Render Block

`POST /api/std-engine/v1/render-blocks/{render_block_id}/validate`

Checks:

1. Template syntax.
2. Input parameter references.
3. Missing required values.
4. Illegal editable regions.
5. Output format validity.

### 20.3 Preview Render Block

`POST /api/std-engine/v1/render-blocks/{render_block_id}/preview`

#### Request

```json
{
  "context_type": "TENDER_STD_INSTANCE",
  "context_id": "uuid",
  "sample_values": {
    "PROCURING_ENTITY_NAME": "Example Procuring Entity",
    "TENDER_NAME": "Example ERP System Tender",
    "TENDER_NUMBER": "EXAMPLE/ICT/ERP/001"
  }
}
```

---

## 21. Render Profile APIs

### 21.1 Create Render Profile

`POST /api/std-engine/v1/render-profiles`

#### Request

```json
{
  "std_version_id": "uuid",
  "profile_code": "DEFAULT_TENDER_DOCUMENT",
  "title": "Default Tender Document Profile",
  "output_formats": ["HTML", "PDF", "DOCX"],
  "render_block_codes": [
    "RENDER_COVER_PAGE",
    "RENDER_INVITATION_TO_TENDER",
    "RENDER_PART_1",
    "RENDER_PART_2",
    "RENDER_PART_3"
  ],
  "default": true
}
```

### 21.2 Render Preview

`POST /api/std-engine/v1/render-profiles/{render_profile_id}/preview`

Generates a non-published preview. Preview outputs must be watermarked or marked as draft.

### 21.3 Render Final Bundle

`POST /api/std-engine/v1/render-profiles/{render_profile_id}/render-final`

Allowed only for validated tender STD instances approved for publication.

---

## 22. Validation APIs

### 22.1 Validate STD Version

`POST /api/std-engine/v1/std-versions/{std_version_id}/validate`

#### Request

```json
{
  "validation_scope": "ACTIVATION_READINESS",
  "include_warnings": true
}
```

#### Validation Scopes

| Scope | Purpose |
|---|---|
| `STRUCTURAL_INTEGRITY` | Section, clause, parameter, rule, form, and render relationships. |
| `SOURCE_TRACEABILITY` | Source trace completeness. |
| `LEGAL_INTEGRITY` | Locked content, approval, and mutability checks. |
| `RENDER_READINESS` | Render block completeness. |
| `ACTIVATION_READINESS` | All checks required before activation. |
| `EXPORT_READINESS` | Package export consistency. |

### 22.2 Validate Tender STD Instance

`POST /api/std-engine/v1/tender-instances/{tender_std_instance_id}/validate`

#### Request

```json
{
  "validation_scope": "PUBLICATION_READINESS",
  "include_rule_trace": true
}
```

#### Tender Validation Scopes

| Scope | Purpose |
|---|---|
| `CONFIGURATION_COMPLETENESS` | Required tender-specific fields complete. |
| `RULE_COMPLIANCE` | Business/legal rules pass. |
| `FORM_ACTIVATION` | Applicable forms correctly activated. |
| `RENDER_READINESS` | Generated document can be rendered. |
| `PUBLICATION_READINESS` | All publication blockers resolved. |
| `ADDENDUM_READINESS` | Proposed changes can be issued through addendum. |

### 22.3 Validation Finding Object

```json
{
  "finding_id": "uuid",
  "code": "MISSING_REQUIRED_PARAMETER",
  "severity": "BLOCKER",
  "message": "Tender submission deadline is required.",
  "context_type": "TENDER_STD_INSTANCE",
  "context_id": "uuid",
  "affected_component_type": "PARAMETER",
  "affected_component_code": "TDS_TENDER_SUBMISSION_DEADLINE",
  "blocking_behavior": "BLOCK_PUBLICATION",
  "resolved": false
}
```

---

## 23. Tender Binding APIs

### 23.1 Bind Active STD Version to Tender

`POST /api/std-engine/v1/tender-instances`

#### Request

```json
{
  "tender_id": "uuid-or-external-tender-id",
  "std_version_id": "uuid",
  "binding_reason": "Create tender document from active IT STD.",
  "idempotency_key": "tender-uuid-std-binding"
}
```

#### Guardrails

| Guardrail | Required behavior |
|---|---|
| STD version must be Active | Block non-active versions. |
| Tender must not already have conflicting active STD instance | Block duplicate active binding. |
| User must have tender preparation permission | Block unauthorized binding. |
| Binding must snapshot STD version hash | Required. |

### 23.2 Read Tender STD Instance

`GET /api/std-engine/v1/tender-instances/{tender_std_instance_id}`

Returns:

1. Tender ID.
2. Bound STD version.
3. Snapshot hash.
4. Configuration state.
5. Validation state.
6. Render state.
7. Publication state.
8. Addendum state.
9. Generated bundle links.

### 23.3 Transition Tender STD Instance

`POST /api/std-engine/v1/tender-instances/{tender_std_instance_id}/transition`

#### Actions

| Action | From state | To state |
|---|---|---|
| `START_CONFIGURATION` | `NOT_STARTED` | `IN_CONFIGURATION` |
| `RUN_VALIDATION` | `IN_CONFIGURATION` | `VALIDATION_FAILED` or `READY_FOR_REVIEW` |
| `SUBMIT_FOR_PROCUREMENT_REVIEW` | `READY_FOR_REVIEW` | `PROCUREMENT_REVIEW` |
| `RETURN_FOR_CORRECTION` | `PROCUREMENT_REVIEW`, `LEGAL_REVIEW` | `IN_CONFIGURATION` |
| `APPROVE_FOR_TENDER_CREATION` | `PROCUREMENT_REVIEW` or `LEGAL_REVIEW` | `APPROVED_FOR_TENDER_CREATION` |
| `GENERATE_BUNDLE` | `APPROVED_FOR_TENDER_CREATION` | `BUNDLE_GENERATED` |
| `PUBLISH` | `BUNDLE_GENERATED` | `PUBLISHED` |
| `MARK_ADDENDUM_REQUIRED` | `PUBLISHED` | `ADDENDUM_REQUIRED` |
| `SUPERSEDE_BY_ADDENDUM` | `ADDENDUM_REQUIRED` | `SUPERSEDED_BY_ADDENDUM` |

---

## 24. Tender Configuration Value APIs

### 24.1 Upsert Configuration Values

`PUT /api/std-engine/v1/tender-instances/{tender_std_instance_id}/configuration-values`

#### Request

```json
{
  "values": [
    {
      "parameter_code": "PROCURING_ENTITY_NAME",
      "value": "National Social Security Fund Staff Pension Scheme"
    },
    {
      "parameter_code": "TENDER_SUBMISSION_DEADLINE",
      "value": "2026-06-30T08:00:00Z"
    }
  ],
  "comment": "Initial tender identity and deadline values."
}
```

### 24.2 Configuration Value Guardrails

| Guardrail | Required behavior |
|---|---|
| Parameter must exist in bound STD version | Block unknown parameter. |
| Parameter must be configurable | Block locked/derived-only parameter. |
| Value must match parameter type | Block invalid value. |
| Value must pass parameter schema | Block invalid value. |
| Tender instance must be editable | Block after publication unless addendum workflow is active. |
| Changes must be audited | Required. |

### 24.3 Get Configuration Wizard Data

`GET /api/std-engine/v1/tender-instances/{tender_std_instance_id}/configuration-wizard`

Returns grouped configuration sections, fields, defaults, current values, rules, warnings, and completion progress.

---

## 25. Generated Bundle APIs

### 25.1 Generate Draft Bundle

`POST /api/std-engine/v1/tender-instances/{tender_std_instance_id}/generated-bundles/draft`

Creates a preview bundle for review.

### 25.2 Generate Final Bundle

`POST /api/std-engine/v1/tender-instances/{tender_std_instance_id}/generated-bundles/final`

Allowed only when tender instance is approved for tender creation.

#### Request

```json
{
  "render_profile_code": "DEFAULT_TENDER_DOCUMENT",
  "output_formats": ["PDF", "DOCX", "HTML"],
  "comment": "Generate final tender bundle for publication."
}
```

### 25.3 Publish Generated Bundle

`POST /api/std-engine/v1/generated-bundles/{generated_bundle_id}/publish`

Publishes an immutable generated bundle.

#### Guardrails

| Guardrail | Required behavior |
|---|---|
| Bundle hash exists | Required. |
| Tender instance approved | Required. |
| No publication blockers | Required. |
| Source STD hash matches binding snapshot | Required unless formally superseded. |
| Bundle not already published | Required. |

### 25.4 Download Generated Bundle

`GET /api/std-engine/v1/generated-bundles/{generated_bundle_id}/download?format=PDF`

### 25.5 Verify Generated Bundle Hash

`POST /api/std-engine/v1/generated-bundles/{generated_bundle_id}/verify-hash`

---

## 26. Addendum Impact APIs

### 26.1 Create Addendum Impact Assessment

`POST /api/std-engine/v1/tender-instances/{tender_std_instance_id}/addendum-impacts`

#### Request

```json
{
  "change_reason": "Correction to tender submission deadline and clarification response period.",
  "proposed_changes": [
    {
      "component_type": "CONFIGURATION_VALUE",
      "parameter_code": "TENDER_SUBMISSION_DEADLINE",
      "old_value": "2026-06-30T08:00:00Z",
      "new_value": "2026-07-07T08:00:00Z"
    }
  ]
}
```

### 26.2 Validate Addendum Impact

`POST /api/std-engine/v1/addendum-impacts/{addendum_impact_id}/validate`

Checks:

1. Tender is already published.
2. Proposed changes are allowed through addendum.
3. Locked source STD text is not changed.
4. Affected rendered sections are identified.
5. Affected forms and submission obligations are identified.
6. Rule impacts are identified.
7. Re-rendering can be performed.
8. Audit trail can link old and new bundle hashes.

### 26.3 Approve Addendum Impact

`POST /api/std-engine/v1/addendum-impacts/{addendum_impact_id}/approve`

Requires procurement/legal approval depending on affected components.

### 26.4 Generate Addendum Bundle

`POST /api/std-engine/v1/addendum-impacts/{addendum_impact_id}/generate-bundle`

Generates:

1. Addendum notice.
2. Revised affected sections.
3. Change summary.
4. Old/new value table.
5. Updated bundle hash.
6. Relationship to original published bundle.

---

## 27. Approval APIs

### 27.1 Create Review Task

`POST /api/std-engine/v1/approvals/review-tasks`

#### Request

```json
{
  "target_type": "STD_VERSION",
  "target_id": "uuid",
  "review_track": "LEGAL_REVIEW",
  "assigned_to_user_id": "uuid",
  "due_date": "2026-07-15",
  "instructions": "Review locked clauses and source traceability before activation."
}
```

### 27.2 Submit Review Decision

`POST /api/std-engine/v1/approvals/review-tasks/{review_task_id}/decision`

#### Request

```json
{
  "decision": "APPROVED",
  "comment": "Legal text and mutability classifications reviewed and accepted.",
  "conditions": []
}
```

#### Decision Values

| Decision | Meaning |
|---|---|
| `APPROVED` | Review track passed. |
| `APPROVED_WITH_CONDITIONS` | Passed subject to logged conditions. |
| `RETURNED_FOR_CORRECTION` | Must be corrected and resubmitted. |
| `REJECTED` | Cannot proceed without major rework. |

### 27.3 Approval Guardrails

| Guardrail | Required behavior |
|---|---|
| Reviewer must be authorized for track | Block otherwise. |
| Reviewer cannot approve own authored work where SoD applies | Block otherwise. |
| Review target must be in reviewable state | Block otherwise. |
| Decision must include comment for rejection/return | Required. |
| Approval must create audit event | Required. |

---

## 28. Audit APIs

### 28.1 Search Audit Events

`GET /api/std-engine/v1/audit-events`

Filters:

```text
?target_type=STD_VERSION&target_id=...&event_type=STD_VERSION_ACTIVATED
?actor_user_id=...&from=2026-07-01&to=2026-07-07
```

### 28.2 Read Audit Event

`GET /api/std-engine/v1/audit-events/{audit_event_id}`

### 28.3 Audit Event Object

```json
{
  "audit_event_id": "uuid",
  "event_type": "STD_VERSION_ACTIVATED",
  "target_type": "STD_VERSION",
  "target_id": "uuid",
  "actor_user_id": "uuid",
  "timestamp": "2026-07-07T00:00:00Z",
  "before_state": "APPROVED",
  "after_state": "ACTIVE",
  "reason": "Approved template version activated for use.",
  "hash_before": "...",
  "hash_after": "...",
  "ip_address": "...",
  "user_agent": "..."
}
```

---

## 29. Hash APIs

### 29.1 Compute Hash

`POST /api/std-engine/v1/hashes/compute`

#### Request

```json
{
  "target_type": "STD_VERSION",
  "target_id": "uuid",
  "hash_scope": "FULL_NORMALIZED_RECORD_SET"
}
```

### 29.2 Verify Hash

`POST /api/std-engine/v1/hashes/verify`

#### Request

```json
{
  "target_type": "GENERATED_BUNDLE",
  "target_id": "uuid",
  "expected_hash": "sha256:..."
}
```

### 29.3 Hash Scope Values

| Scope | Meaning |
|---|---|
| `SOURCE_FILE` | Raw source document file hash. |
| `CLAUSE_CONTENT` | Normalized clause text hash. |
| `COMPONENT_RECORD` | Individual normalized component record hash. |
| `FULL_NORMALIZED_RECORD_SET` | Full STD version normalized record-set hash. |
| `GENERATED_OUTPUT` | Rendered file hash. |
| `PUBLISHED_BUNDLE` | Full published bundle hash. |

---

## 30. UI Design Principles

### 30.1 General UI Rules

1. The UI must not expose JSON editing to ordinary users.
2. The UI must present locked and configurable content differently.
3. Locked content must be visibly read-only.
4. All configuration screens must show validation status.
5. Publication blockers must be clear and actionable.
6. Review screens must show source traceability.
7. Activation screens must show approval and validation gates.
8. Generated bundle screens must show hash and version identity.
9. Addendum screens must show before/after differences.
10. Tender users must not see central STD administration controls unless authorized.

### 30.2 UI Personas

| Persona | Main UI need |
|---|---|
| System Administrator | Configure platform-level settings and seed data. |
| STD Template Administrator | Import, structure, and maintain draft STD packages. |
| Procurement Policy Reviewer | Review STD configuration and procurement correctness. |
| Legal Reviewer | Review locked text, SCC/TDS boundaries, legal traceability. |
| Approver | Approve STD versions and tender STD configurations. |
| Procurement Officer | Configure tender-specific values using active STD templates. |
| Evaluation Administrator | Consume generated evaluation forms and criteria. |
| Auditor | Review trace, approvals, hashes, generated outputs, and audit events. |

---

## 31. Administration UI Screens

### 31.1 STD Family List

**Route:** `/std-engine/admin/families`

#### Purpose

Display and manage STD families.

#### Columns

| Column | Description |
|---|---|
| Family code | Stable family code. |
| Name | STD family name. |
| Authority | Source authority. |
| Category | Procurement category. |
| Active versions | Count of active versions. |
| Latest version | Latest version code. |
| Status | Active/inactive family status. |

#### Actions

1. Create family.
2. View family.
3. View versions.
4. Deactivate family, if unused and allowed.

### 31.2 STD Family Detail

**Route:** `/std-engine/admin/families/{id}`

#### Sections

1. Family metadata.
2. Version list.
3. Source authority.
4. Procurement category.
5. Usage summary.
6. Audit history.

### 31.3 STD Version Workspace

**Route:** `/std-engine/admin/versions/{id}`

#### Purpose

Central workspace for one STD version.

#### Panels

| Panel | Purpose |
|---|---|
| Header | Version code, family, state, hash, usage count. |
| Lifecycle | Current state and allowed transitions. |
| Source documents | Linked official documents. |
| Validation | Latest validation findings. |
| Sections | Section tree. |
| Clauses | Clause inventory. |
| Parameters | Configurable fields. |
| Rules | Rule inventory. |
| Forms | Form schemas. |
| Evidence | Evidence requirements. |
| Render | Render blocks and profiles. |
| Approvals | Review tasks and decisions. |
| Audit | Audit events. |

#### Critical UI Behavior

If state is Active, the workspace becomes read-only except for permitted supersession operations.

### 31.4 Source Document Registry

**Route:** `/std-engine/admin/source-documents`

#### Features

1. Upload/register official source document.
2. Compute hash.
3. Display page count and file metadata.
4. Link to STD versions.
5. Verify hash.
6. View source trace coverage.

### 31.5 Import Package Wizard

**Route:** `/std-engine/admin/versions/{id}/import`

#### Steps

1. Select package file.
2. Confirm target STD version.
3. Validate package manifest.
4. Show dry-run changes.
5. Show validation findings.
6. Apply package.
7. Review imported component counts.
8. Create audit event.

#### Required Dry-Run Output

| Output | Required |
|---|---|
| Components to create | Yes |
| Components to update | Yes |
| Components to delete/deactivate | Yes, if allowed |
| Duplicate codes | Yes |
| Broken references | Yes |
| Source trace gaps | Yes |
| Hash mismatches | Yes |

### 31.6 Section Tree Editor

**Route:** `/std-engine/admin/versions/{id}/sections`

#### Features

1. View hierarchy.
2. Create section.
3. Edit draft section metadata.
4. Reorder sections.
5. Assign mutability type.
6. Link source trace.
7. View component counts.

Locked behavior: section editing disabled after activation.

### 31.7 Clause Editor

**Route:** `/std-engine/admin/versions/{id}/clauses/{clause_id}`

#### Features

1. View clause text.
2. Edit draft clause text.
3. Assign mutability.
4. Link parameters.
5. View source trace.
6. Compute hash.
7. Compare with previous version.
8. View usage.

#### UI Warning

When editing clause content, display:

> Clause text changes are legally material. Activation will require review and approval.

### 31.8 Parameter Dictionary

**Route:** `/std-engine/admin/versions/{id}/parameters`

#### Features

1. List parameters.
2. Filter by section, stage, required, mutability.
3. Create parameter.
4. Edit parameter schema.
5. Manage allowed values.
6. View usage in clauses, forms, rules, render blocks.

### 31.9 Rule Studio

**Route:** `/std-engine/admin/versions/{id}/rules`

#### Features

1. List rules.
2. Create/edit draft rules.
3. Validate rule expression syntax.
4. Execute rule against sample context.
5. View affected parameters/components.
6. Assign severity and blocking behavior.
7. Link source trace.

### 31.10 Form Schema Builder

**Route:** `/std-engine/admin/versions/{id}/forms`

#### Features

1. Create form schema.
2. Add fields.
3. Add field validation.
4. Add conditional display logic.
5. Link evidence requirements.
6. Preview form.
7. View supplier submission mapping.

### 31.11 Render Profile Builder

**Route:** `/std-engine/admin/versions/{id}/render`

#### Features

1. Manage render blocks.
2. Manage render profiles.
3. Validate templates.
4. Preview output.
5. Verify required input parameters.
6. Show missing render coverage.

### 31.12 STD Activation Review Screen

**Route:** `/std-engine/admin/versions/{id}/activation`

#### Required Panels

1. Current lifecycle state.
2. Component completeness summary.
3. Validation summary.
4. Source trace summary.
5. Approval summary.
6. Hash summary.
7. Usage warning.
8. Activation checklist.
9. Final activation action.

#### Activation Button Behavior

The Activate button remains disabled until all blockers are resolved.

---

## 32. Review and Approval UI Screens

### 32.1 Review Task Inbox

**Route:** `/std-engine/reviews`

#### Columns

| Column | Description |
|---|---|
| Review target | STD version, tender instance, addendum impact. |
| Review track | Legal, procurement, technical, template structure. |
| Assigned date | Date task assigned. |
| Due date | Due date. |
| Status | Pending, approved, returned, rejected. |
| Priority | Normal/high/urgent. |

### 32.2 Review Task Detail

**Route:** `/std-engine/reviews/{review_task_id}`

#### Panels

1. Review instructions.
2. Target summary.
3. Validation findings.
4. Source trace.
5. Diff view, if applicable.
6. Component checklist.
7. Comment history.
8. Decision controls.

### 32.3 Approval Decision Controls

Available decisions:

1. Approve.
2. Approve with conditions.
3. Return for correction.
4. Reject.

Rejection and return require comments.

Approval with conditions requires condition list.

---

## 33. Tender Configuration UI Screens

### 33.1 Select STD Template for Tender

**Route:** `/tenders/{tender_id}/std/select`

#### Purpose

Bind an active STD version to a tender.

#### Features

1. Show available active STD families and versions.
2. Filter by procurement category.
3. Show version effective date.
4. Show source authority.
5. Show warning if superseded.
6. Bind selected active version.

### 33.2 Tender STD Configuration Dashboard

**Route:** `/tenders/{tender_id}/std/{tender_std_instance_id}`

#### Panels

| Panel | Purpose |
|---|---|
| STD identity | Bound STD family/version/hash. |
| Configuration progress | Completion percentage by section. |
| Validation status | Blockers, warnings, info. |
| Wizard navigation | Configuration groups. |
| Preview | Draft generated document preview. |
| Review | Submit for review. |
| Bundle | Generated bundle status. |
| Addendum | Post-publication change controls. |

### 33.3 Tender Configuration Wizard

**Route:** `/tenders/{tender_id}/std/{instance_id}/wizard`

#### Generic Wizard Groups

The wizard must be generated from STD parameter metadata, not hard-coded screens.

Minimum generic groups:

1. Tender identity.
2. Procuring Entity details.
3. Procurement method and participation.
4. Lots and alternatives.
5. Dates and deadlines.
6. Clarifications and meetings.
7. Securities and declarations.
8. Eligibility and qualification.
9. Requirements and schedules.
10. Price schedule setup.
11. Evaluation setup.
12. Contract and SCC parameters.
13. Forms and evidence.
14. Review and validation.
15. Preview and approval.

The IT STD implementation can add specialized groups through package data, such as Technical Requirements, Implementation Schedule, System Inventory, Software Categories, and Acceptance Testing.

### 33.4 Field Display Contract

Each field rendered in the wizard must be driven by parameter metadata.

```json
{
  "parameter_code": "TENDER_SUBMISSION_DEADLINE",
  "label": "Tender submission deadline",
  "type": "DATETIME",
  "required": true,
  "current_value": "2026-06-30T08:00:00Z",
  "help_text": "Deadline for submission of tenders.",
  "source_trace_summary": "TDS reference",
  "validation_messages": [],
  "editable": true
}
```

### 33.5 Locked Content Preview

The tender configuration UI must allow users to preview locked clauses but not edit them.

Visual rules:

1. Locked clauses display a lock indicator.
2. Configurable fields display input controls.
3. System-generated values display derived-value indicators.
4. Source trace can be expanded.
5. Changes to configurable values show affected output sections.

### 33.6 Validation Screen

**Route:** `/tenders/{tender_id}/std/{instance_id}/validation`

#### Features

1. Run validation.
2. Display blockers first.
3. Group findings by section.
4. Link each finding to affected field.
5. Show legal/procedural basis where available.
6. Allow re-validation.
7. Disable review submission until blockers clear.

### 33.7 Preview Screen

**Route:** `/tenders/{tender_id}/std/{instance_id}/preview`

#### Features

1. Generate draft preview.
2. Render section navigation.
3. Show unresolved placeholders.
4. Show validation overlay.
5. Export draft preview if permitted.
6. Watermark as draft.

### 33.8 Publication Bundle Screen

**Route:** `/tenders/{tender_id}/std/{instance_id}/bundle`

#### Features

1. Generate final bundle.
2. Display output formats.
3. Display generated hash.
4. Display source STD hash.
5. Publish bundle.
6. Download bundle.
7. Lock published bundle.

### 33.9 Addendum Screen

**Route:** `/tenders/{tender_id}/std/{instance_id}/addendum`

#### Features

1. Initiate post-publication change.
2. Select affected configuration values or generated sections.
3. Enter change reason.
4. Run impact assessment.
5. Show affected forms/rules/render blocks.
6. Submit addendum for approval.
7. Generate addendum bundle.
8. Link addendum to original published bundle.

---

## 34. Service Contracts

### 34.1 Template Registry Service

#### Responsibilities

1. Manage STD family and version records.
2. Enforce version uniqueness.
3. Resolve active version by family/category/effective date.
4. Prevent deletion of used versions.
5. Provide version usage counts.

#### Core Methods

```text
create_family(input) -> std_family
create_version(input) -> std_version
get_active_version(std_family_code, date) -> std_version
transition_version(std_version_id, action, actor, comment) -> transition_result
assert_version_editable(std_version_id) -> void/error
assert_version_activatable(std_version_id) -> void/error
```

### 34.2 Source Trace Service

#### Responsibilities

1. Register source documents.
2. Compute source document hashes.
3. Link components to source pages/anchors.
4. Report source trace coverage.
5. Verify source hash integrity.

#### Core Methods

```text
register_source_document(input) -> source_document
compute_source_hash(source_document_id) -> hash
link_source_trace(component_type, component_id, trace) -> source_trace
validate_trace_coverage(std_version_id) -> findings[]
verify_source_hash(source_document_id) -> verification_result
```

### 34.3 Component Service

#### Responsibilities

1. Manage sections, clauses, parameters, rules, forms, fields, evidence requirements, render blocks, and render profiles.
2. Enforce editability based on STD version state.
3. Enforce code uniqueness within STD version.
4. Compute component hashes.
5. Resolve component dependencies.

#### Core Methods

```text
create_component(component_type, input) -> component
update_component(component_type, id, input) -> component
deactivate_component(component_type, id, reason) -> component
get_component_usage(component_type, id) -> usage_summary
compute_component_hash(component_type, id) -> hash
```

### 34.4 Import/Export Service

#### Responsibilities

1. Validate import package manifest.
2. Validate component relationships.
3. Validate package hashes.
4. Dry-run package application.
5. Apply package to editable STD version.
6. Export normalized STD package.

#### Core Methods

```text
validate_package(import_package_id) -> validation_result
dry_run_import(import_package_id) -> import_preview
apply_import(import_package_id, mode) -> import_result
export_package(std_version_id, options) -> package_reference
```

### 34.5 Validation Service

#### Responsibilities

1. Validate STD activation readiness.
2. Validate tender configuration completeness.
3. Validate publication readiness.
4. Validate addendum readiness.
5. Persist validation findings.
6. Resolve validation findings when corrected.

#### Core Methods

```text
validate_std_version(std_version_id, scope) -> findings[]
validate_tender_instance(tender_std_instance_id, scope) -> findings[]
validate_addendum_impact(addendum_impact_id) -> findings[]
has_blockers(context_type, context_id, blocking_behavior) -> boolean
```

### 34.6 Rule Evaluation Service

#### Responsibilities

1. Validate rule expressions.
2. Execute rules against context.
3. Resolve parameter values.
4. Return structured findings.
5. Support deterministic execution.

#### Core Methods

```text
validate_rule_expression(language, expression) -> syntax_result
execute_rule(rule_id, context) -> rule_result
execute_rules(std_version_id, scope, context) -> rule_results[]
```

### 34.7 Render Service

#### Responsibilities

1. Validate render templates.
2. Resolve input values.
3. Render blocks.
4. Render full profiles.
5. Generate draft previews.
6. Generate final immutable outputs.
7. Compute output hashes.

#### Core Methods

```text
validate_render_block(render_block_id) -> findings[]
render_block(render_block_id, context) -> render_output
render_profile(render_profile_id, context, mode) -> rendered_bundle
compute_render_hash(rendered_output_id) -> hash
```

### 34.8 Tender Binding Service

#### Responsibilities

1. Bind active STD versions to tenders.
2. Snapshot STD hash at binding.
3. Manage tender STD instance lifecycle.
4. Store configuration values.
5. Enforce editability rules.
6. Resolve wizard configuration data.

#### Core Methods

```text
bind_std_to_tender(tender_id, std_version_id, actor) -> tender_std_instance
get_configuration_wizard(instance_id) -> wizard_model
upsert_configuration_values(instance_id, values, actor) -> save_result
transition_tender_instance(instance_id, action, actor, comment) -> transition_result
```

### 34.9 Generated Bundle Service

#### Responsibilities

1. Generate draft bundles.
2. Generate final bundles.
3. Publish bundles.
4. Lock published bundles.
5. Verify bundle hashes.
6. Link bundles to tender and STD instance.

#### Core Methods

```text
generate_draft_bundle(instance_id, profile_code) -> generated_bundle
generate_final_bundle(instance_id, profile_code) -> generated_bundle
publish_bundle(bundle_id, actor) -> published_bundle
verify_bundle_hash(bundle_id) -> verification_result
```

### 34.10 Addendum Impact Service

#### Responsibilities

1. Capture proposed post-publication changes.
2. Compare proposed values to published bundle values.
3. Determine affected components.
4. Validate whether change can be issued by addendum.
5. Generate addendum bundle.
6. Link original and superseding bundle hashes.

#### Core Methods

```text
create_addendum_impact(instance_id, proposed_changes, reason) -> addendum_impact
assess_impact(addendum_impact_id) -> impact_result
approve_impact(addendum_impact_id, actor, comment) -> approval_result
generate_addendum_bundle(addendum_impact_id) -> generated_bundle
```

### 34.11 Approval Workflow Service

#### Responsibilities

1. Create review tasks.
2. Assign reviewers.
3. Enforce review tracks.
4. Capture decisions.
5. Enforce segregation of duties.
6. Feed transition guardrails.

#### Core Methods

```text
create_review_task(target_type, target_id, track, assignee) -> review_task
submit_decision(review_task_id, decision, actor, comment) -> review_decision
get_approval_summary(target_type, target_id) -> approval_summary
assert_required_approvals_present(target_type, target_id, transition_action) -> void/error
```

### 34.12 Audit Service

#### Responsibilities

1. Record material events.
2. Persist before/after states where applicable.
3. Link audit events to hashes.
4. Provide audit search.
5. Support evidentiary export.

#### Core Methods

```text
record_event(event_input) -> audit_event
search_events(filters) -> audit_event[]
get_event(audit_event_id) -> audit_event
export_audit_trail(target_type, target_id) -> file_reference
```

### 34.13 Hash Service

#### Responsibilities

1. Normalize records for hashing.
2. Compute SHA-256 hashes.
3. Verify stored hashes.
4. Detect drift.
5. Link hashes to audit events.

#### Core Methods

```text
compute_hash(target_type, target_id, scope) -> hash_result
verify_hash(target_type, target_id, expected_hash) -> verification_result
normalize_for_hash(target_type, target_id, scope) -> canonical_payload
```

### 34.14 Notification Service

#### Responsibilities

1. Notify reviewers of assigned tasks.
2. Notify template administrators of returned corrections.
3. Notify procurement officers of validation blockers.
4. Notify approvers of activation/publication requests.
5. Notify auditors of material events where configured.

#### Core Methods

```text
notify_review_assigned(review_task_id) -> void
notify_transition(target_type, target_id, transition) -> void
notify_validation_blockers(context_type, context_id, findings) -> void
```

---

## 35. Background Jobs

### 35.1 Required Jobs

| Job | Frequency / Trigger | Purpose |
|---|---|---|
| Source hash verification | Scheduled and on demand | Detect source file drift. |
| STD version integrity check | Scheduled | Detect invalid active version state. |
| Validation recalculation | On component/configuration change | Refresh findings. |
| Render preview cleanup | Scheduled | Remove expired draft previews. |
| Audit export generation | On demand | Generate auditor-readable trails. |
| Addendum impact recalculation | On proposed change | Update affected component list. |
| Superseded version usage report | Scheduled | Track continued use of old versions. |

### 35.2 Job Failure Behavior

Job failures must be logged and visible to administrators.

Jobs that protect integrity, such as hash verification and active-version integrity checks, must create warning or blocker records if they detect inconsistencies.

---

## 36. Integration Contracts

### 36.1 Tender Management Integration

Tender Management consumes:

1. Active STD family/version list.
2. Tender STD binding endpoint.
3. Configuration wizard model.
4. Validation status.
5. Generated tender bundles.
6. Addendum impact outputs.

Tender Management provides:

1. Tender identity.
2. Procuring Entity identity.
3. Procurement category.
4. Procurement method.
5. Estimated value, where rules require it.
6. Publication state.
7. Addendum state.

### 36.2 Supplier Submission Integration

Supplier Submission consumes:

1. Active form schemas.
2. Evidence requirements.
3. Price schedule schema.
4. Requirement conformance schema.
5. Submission validation rules.

Supplier Submission provides:

1. Submitted form values.
2. Evidence documents.
3. Price schedule responses.
4. Requirement conformance responses.
5. Submission validation results.

### 36.3 Evaluation Integration

Evaluation consumes:

1. Evaluation criteria schema.
2. Responsiveness checklist.
3. Technical scoring model.
4. Financial comparison model.
5. Rule-generated evaluation constraints.
6. Requirement conformance matrix.

Evaluation provides:

1. Evaluation results.
2. Disqualification decisions.
3. Clarification requests.
4. Evaluation reports.
5. Recommended award outcome.

### 36.4 Contract Formation Integration

Contract Formation consumes:

1. Awarded supplier data.
2. Final accepted tender values.
3. Contract forms schema.
4. SCC values.
5. Price schedules.
6. Technical requirements.
7. Accepted deviations and finalization minutes.
8. Generated contract appendices.

Contract Formation provides:

1. Contract agreement record.
2. Executed contract bundle.
3. Securities.
4. Contract start and acceptance milestones.

---

## 37. Data Payload Standards

### 37.1 Source Trace Object

```json
{
  "source_document_id": "uuid",
  "page_start": 1,
  "page_end": 3,
  "section_heading": "Section II - Tender Data Sheet",
  "source_anchor": "TDS",
  "text_hash": "sha256:...",
  "notes": "Optional trace note."
}
```

### 37.2 Mutability Object

```json
{
  "mutability_type": "CONFIGURABLE",
  "editable_in_master_draft": true,
  "editable_in_tender_configuration": true,
  "editable_after_publication": false,
  "requires_addendum_after_publication": true
}
```

### 37.3 Rule Reference Object

```json
{
  "rule_code": "RULE_ALTERNATIVE_TENDERS_NOT_PERMITTED",
  "severity": "LEGAL_BLOCKER",
  "blocking_behavior": "BLOCK_PUBLICATION",
  "affected_component_codes": ["TDS_ALTERNATIVE_TENDERS"]
}
```

### 37.4 Render Output Object

```json
{
  "generated_bundle_id": "uuid",
  "output_format": "PDF",
  "file_reference": "file-storage-key",
  "sha256_hash": "sha256:...",
  "rendered_at": "2026-07-07T00:00:00Z",
  "render_profile_code": "DEFAULT_TENDER_DOCUMENT",
  "source_std_version_hash": "sha256:..."
}
```

---

## 38. Frontend State Management Contract

### 38.1 Required Client State

The frontend should treat the server as authoritative for:

1. User permissions.
2. Record editability.
3. Allowed transitions.
4. Validation findings.
5. Render readiness.
6. Published/locked state.

The frontend may cache display data, but it must refresh server state before transitions, publication, activation, or approval.

### 38.2 Optimistic Updates

Optimistic UI updates may be used for minor draft edits, but not for:

1. State transitions.
2. Approvals.
3. Activation.
4. Publication.
5. Addendum approval.
6. Final bundle generation.
7. Hash verification.

### 38.3 Unsaved Change Handling

Configuration wizard screens must warn users before navigation away when unsaved values exist.

### 38.4 Conflict Handling

If the server detects that a record changed since the UI loaded it, the UI must show a conflict resolution message and reload the latest state.

---

## 39. Security Requirements

### 39.1 Access Control

1. All mutating actions require explicit permission.
2. Read access to draft STD versions may be restricted to template administrators and reviewers.
3. Tender configuration values must be scoped to the relevant Procuring Entity and tender.
4. Audit events must be read-only.
5. Published bundle downloads must respect tender publication visibility rules.

### 39.2 Input Security

1. All template input must be sanitized.
2. Render templates must not execute arbitrary code.
3. Rule expressions must be sandboxed.
4. File uploads must be scanned and type-validated.
5. Large payloads must be size-limited.

### 39.3 Integrity Security

1. Active version records must be protected from direct database mutation through application-level services.
2. Hash verification must detect drift.
3. Audit events must be append-only.
4. Published generated bundles must be immutable.

---

## 40. Performance Requirements

| Operation | Target |
|---|---|
| Load STD version workspace | Under 3 seconds for normal component counts. |
| Run activation validation | Under 10 seconds for ordinary STD package. |
| Load tender configuration wizard | Under 3 seconds per section. |
| Save configuration values | Under 2 seconds for normal batch. |
| Generate draft preview | Under 30 seconds for full tender document. |
| Generate final bundle | Under 60 seconds for full tender document. |
| Search audit events | Under 5 seconds for indexed filters. |

Longer operations must run asynchronously with visible job status.

---

## 41. Observability Requirements

The module must log:

1. API request failures.
2. Validation failures.
3. Render failures.
4. Import failures.
5. Hash verification failures.
6. State-transition failures.
7. Permission denials for material actions.
8. Background job failures.

The module should expose administrative dashboards for:

1. Active STD versions.
2. Failed validations.
3. Pending approvals.
4. Source hash drift.
5. Generated bundle counts.
6. Addendum activity.
7. Superseded version usage.

---

## 42. Acceptance Criteria

### 42.1 API Acceptance Criteria

| ID | Criterion |
|---|---|
| API-001 | STD family can be created and listed. |
| API-002 | STD version can be created in Draft state. |
| API-003 | Source document can be registered and hashed. |
| API-004 | Import package can be validated before application. |
| API-005 | Invalid package references produce blocker findings. |
| API-006 | Sections, clauses, parameters, rules, forms, and render blocks can be created in editable states. |
| API-007 | Active STD version cannot be modified through public APIs. |
| API-008 | Activation is blocked without required validation and approvals. |
| API-009 | Active STD version can be bound to a tender. |
| API-010 | Non-active STD version cannot be bound to a tender. |
| API-011 | Tender configuration values can be saved only for configurable parameters. |
| API-012 | Tender publication is blocked when validation blockers exist. |
| API-013 | Final generated bundle is hashable. |
| API-014 | Published generated bundle is immutable. |
| API-015 | Addendum impact identifies affected components. |
| API-016 | Audit events are created for material actions. |

### 42.2 UI Acceptance Criteria

| ID | Criterion |
|---|---|
| UI-001 | Administrator can view STD family and version lists. |
| UI-002 | Administrator can open STD version workspace. |
| UI-003 | Locked content is visibly read-only. |
| UI-004 | Editable draft components can be edited only in editable states. |
| UI-005 | Import wizard shows dry-run changes before application. |
| UI-006 | Activation screen disables activation until blockers clear. |
| UI-007 | Review task screen supports approve, conditional approve, return, and reject. |
| UI-008 | Procurement user can bind active STD version to tender. |
| UI-009 | Configuration wizard renders from parameter metadata. |
| UI-010 | Validation screen links findings to fields. |
| UI-011 | Preview screen generates draft output. |
| UI-012 | Publication bundle screen shows output hash. |
| UI-013 | Addendum screen shows before/after changes and impact summary. |

### 42.3 Service Acceptance Criteria

| ID | Criterion |
|---|---|
| SVC-001 | Validation Service detects missing required components. |
| SVC-002 | Rule Evaluation Service executes deterministic rule expressions. |
| SVC-003 | Render Service blocks output where required values are missing. |
| SVC-004 | Hash Service computes stable hashes for unchanged normalized content. |
| SVC-005 | Audit Service records before/after states for transitions. |
| SVC-006 | Approval Service enforces review-track permissions. |
| SVC-007 | Tender Binding Service snapshots active STD hash. |
| SVC-008 | Addendum Impact Service links original and revised bundles. |

---

## 43. Implementation Task Breakdown

### 43.1 Backend Foundation

1. Create module namespace.
2. Implement base response envelope.
3. Implement permission guards.
4. Implement state-transition guard service.
5. Implement audit event service.
6. Implement hash normalization utilities.
7. Implement common validation finding model.
8. Implement idempotency support for material operations.

### 43.2 Registry and Source Document Services

1. Implement STD family APIs.
2. Implement STD version APIs.
3. Implement source document APIs.
4. Implement source hash computation.
5. Implement version usage counts.
6. Implement version state transitions.

### 43.3 Component Services

1. Implement section APIs.
2. Implement clause APIs.
3. Implement parameter APIs.
4. Implement rule APIs.
5. Implement form APIs.
6. Implement evidence APIs.
7. Implement render block APIs.
8. Implement render profile APIs.
9. Implement component usage service.

### 43.4 Import/Export Services

1. Implement package upload record.
2. Implement package manifest parser.
3. Implement package validation.
4. Implement dry-run import.
5. Implement apply import.
6. Implement package export.
7. Implement import audit events.

### 43.5 Validation and Rule Engine

1. Implement structural validation.
2. Implement source trace validation.
3. Implement legal integrity validation.
4. Implement render readiness validation.
5. Implement activation readiness validation.
6. Implement tender configuration validation.
7. Implement rule syntax validation.
8. Implement rule execution.

### 43.6 Rendering and Bundle Services

1. Implement render template validation.
2. Implement block rendering.
3. Implement profile rendering.
4. Implement draft preview generation.
5. Implement final bundle generation.
6. Implement published bundle locking.
7. Implement bundle hash verification.

### 43.7 Tender Binding and Configuration

1. Implement active STD selection API.
2. Implement tender binding API.
3. Implement configuration wizard API.
4. Implement configuration value save API.
5. Implement tender instance validation.
6. Implement tender review transition.
7. Implement publication controls.

### 43.8 Addendum Services

1. Implement addendum impact creation.
2. Implement impact assessment.
3. Implement addendum validation.
4. Implement approval flow for addenda.
5. Implement addendum bundle generation.
6. Implement original/revised hash linking.

### 43.9 UI Implementation

1. STD family list and detail.
2. STD version workspace.
3. Source document registry.
4. Import package wizard.
5. Section tree editor.
6. Clause editor.
7. Parameter dictionary.
8. Rule studio.
9. Form schema builder.
10. Render profile builder.
11. Activation review screen.
12. Review task inbox and detail.
13. Tender STD selection screen.
14. Tender configuration dashboard.
15. Configuration wizard.
16. Validation screen.
17. Preview screen.
18. Bundle publication screen.
19. Addendum screen.
20. Audit event viewer.

### 43.10 Tests

1. Unit tests for state transitions.
2. Unit tests for permissions.
3. Unit tests for hash normalization.
4. Unit tests for rule execution.
5. Unit tests for validation scopes.
6. Unit tests for render template resolution.
7. Integration tests for import package workflow.
8. Integration tests for activation workflow.
9. Integration tests for tender binding workflow.
10. Integration tests for generated bundle workflow.
11. Integration tests for addendum workflow.
12. Regression smoke contracts from prior artifact.

---

## 44. First Build Slice

The first implementation slice should be deliberately narrow but legally meaningful.

### 44.1 Slice Objective

Prove that the platform can register an STD family, create a version, register a source document, import structured components, validate the STD version, approve it, activate it, bind it to a tender, configure required values, render a draft bundle, and block publication until validation passes.

### 44.2 Included Capabilities

1. STD family and version registry.
2. Source document registry and hash.
3. Minimal section, parameter, and render block components.
4. Import package dry-run.
5. Activation validation.
6. Approval task stub.
7. Activation transition.
8. Tender binding.
9. Configuration wizard model.
10. Configuration value save.
11. Tender validation.
12. Draft render preview.
13. Audit events.

### 44.3 Excluded from First Build Slice

1. Full form builder.
2. Full rule expression studio.
3. Full addendum generation.
4. Full PDF/DOCX fidelity.
5. Supplier portal integration.
6. Evaluation integration.
7. Full IT STD seed package.

---

## 45. Risks and Controls

| Risk | Control |
|---|---|
| UI hard-codes IT STD assumptions | Generate screens from parameter/form metadata. |
| Active STD records are edited directly | Centralize editability guard and database constraints where possible. |
| Source trace is incomplete | Activation validation blocks missing required trace. |
| Rendering produces legally incomplete output | Render readiness validation and required render coverage. |
| Package import overwrites approved content | Imports allowed only in editable states. |
| Addendum changes bypass approval | Addendum workflow has separate impact and approval states. |
| Audit trail is incomplete | Mutating services call Audit Service through common wrapper. |
| Hashes are unstable | Use canonical normalization and deterministic ordering. |
| Rule engine becomes unsafe | Use sandboxed expression language, not arbitrary code execution. |
| Too many STD-specific branches | Move STD-specific behavior into package data and schemas. |

---

## 46. Open Implementation Decisions

The following decisions should be resolved during the Cursor Implementation Pack stage:

1. Exact framework naming conventions for tables, DocTypes, or models.
2. Whether file storage is local, object storage, or document-management-backed.
3. Exact render engine for HTML/PDF/DOCX generation.
4. Exact rule expression language.
5. Whether approval workflow uses existing platform workflow engine or a module-specific workflow table.
6. Whether hashes are computed synchronously or asynchronously for large bundles.
7. Whether generated DOCX output is required in first release or PDF/HTML is sufficient.
8. Whether package import supports split JSON only or also YAML.
9. Whether source trace page anchors are manually captured or semi-automatically extracted.
10. Whether published bundles are stored inside STD Engine or handed off to Tender Management storage after publication.

---

## 47. Definition of Done for This Module Contract

This API, UI, and Service Contract is complete when:

1. All core resources have endpoint contracts.
2. All lifecycle transitions have service enforcement points.
3. All critical UI screens are identified.
4. All material operations create audit events.
5. Hashing and immutability are represented in API and service contracts.
6. Tender binding and publication behavior are represented.
7. Addendum impact behavior is represented.
8. Generalization across multiple STDs is preserved.
9. The first build slice is clear enough to implement.
10. The next artifact can safely become a Cursor Implementation Pack.

---

## 48. Recommended Next Artifact

The next artifact should be:

**STD Engine Core Module - Cursor Implementation Pack**

That pack should convert this contract into:

1. File/module structure.
2. Model/DocType definitions.
3. Migration plan.
4. API controller/service files.
5. Validation service implementation instructions.
6. Render service implementation instructions.
7. Permission fixtures.
8. Seed data fixtures.
9. Test files.
10. Step-by-step implementation sequence.

Only after the Core Module implementation pack is ready should the project proceed to the IT STD extraction matrix and IT STD seed package.
