# IT Tender Configuration Wizard — API, UI, and Service Contract

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Artifact Type:** API, UI, and Service Contract  
**Version:** v1.0 Draft  
**Status:** Implementation-Ready Draft, Subject to Technical Review  
**Primary Dependency:** STD Engine Core Module  
**Reference STD Family:** `KE-PPRA-IT`  
**Reference Package:** `KE-PPRA-IT-2022-04`  

---

## 1. Purpose

This document defines the API, UI, and service-level contract for the IT Tender Configuration Wizard within the KenTender e-Procurement system.

The wizard allows authorized Procuring Entity users to configure a tender based on an active Standard Tender Document version for Procurement of Information Technology. The wizard must not permit free-form legal document editing. It must bind a tender to an approved, active STD version and collect only the tender-specific values, requirements, schedules, pricing configuration, evaluation options, and contract parameters that the STD permits.

The module must be generalized enough to support future STD-specific wizards by relying on the STD Engine Core Module for template versioning, mutability, rules, render blocks, validation, source traceability, and generated artifact governance.

---

## 2. Design Principle

The IT Tender Configuration Wizard is not the source of legal truth.

The source of truth is:

1. The active STD Template Version.
2. The STD Engine Core configuration schema.
3. The rule dictionary attached to that STD version.
4. The render blocks attached to that STD version.
5. The tender-specific configuration values entered through controlled UI surfaces.

The wizard must therefore behave as a controlled configuration interface, not a document authoring tool.

---

## 3. Scope

### 3.1 In Scope

The module must support:

1. Creating an IT tender configuration instance from an active IT STD version.
2. Capturing Tender Data Sheet values.
3. Capturing Special Conditions of Contract values.
4. Capturing Procuring Entity requirements.
5. Capturing functional, architectural, performance, service, technology, testing, training, implementation, and support requirements.
6. Capturing implementation phases, milestones, deliverables, acceptance points, and locations.
7. Capturing system inventory items.
8. Configuring price schedule structures.
9. Configuring evaluation and qualification criteria within STD-permitted boundaries.
10. Configuring forms and evidence requirements.
11. Running validation against the active STD rule set.
12. Producing preview renders.
13. Submitting the configuration for review and approval.
14. Binding the approved configuration to a tender.
15. Generating immutable tender document artifacts at publication.
16. Supporting addendum impact detection after publication.
17. Supporting audit logging and traceability for all material changes.

### 3.2 Out of Scope

This module must not:

1. Edit master STD clauses.
2. Edit locked ITT or GCC text.
3. Activate or approve STD template versions.
4. Replace the Tender Management module.
5. Replace Supplier Submission module.
6. Replace Evaluation module.
7. Replace Contract Management module.
8. Serve as a generic file upload repository for tender documents.
9. Allow users to bypass STD validation by uploading a standalone tender document.

---

## 4. External Dependencies

| Dependency | Purpose |
|---|---|
| STD Engine Core Module | STD family/version, schema, rules, rendering, validation, lifecycle, traceability |
| Tender Management Module | Tender shell, publication workflow, addenda, tender notices |
| Procurement Plan Module | Approved procurement plan item, budget, method, estimate, timeline |
| User/RBAC Module | Roles, permissions, approval gates |
| Document Rendering Service | HTML/PDF/DOCX preview and publication artifacts |
| Audit/Event Service | Evidentiary audit trail |
| Attachment/Evidence Service | Requirement files, reference materials, background attachments |
| Notification Service | Review, approval, return, rejection, and addendum alerts |
| Evaluation Module | Generated evaluation schema consumption |
| Supplier Portal | Generated bidder response forms and conformance matrices |
| Contract Management Module | Contract carry-forward after award |

---

## 5. High-Level Architecture

```text
Tender Management
      |
      | creates / references tender shell
      v
IT Tender Configuration Wizard
      |
      | reads schemas, rules, render blocks
      v
STD Engine Core
      |
      | validates / renders / hashes
      v
Generated Tender Document Bundle
      |
      | feeds
      +--> Supplier Portal
      +--> Tender Publication
      +--> Evaluation Module
      +--> Contract Formation
```

The wizard stores tender-specific configuration data. It must reference the STD Template Version and must not duplicate master STD content except as immutable generated snapshots at publication.

---

## 6. Core API Conventions

### 6.1 API Style

All APIs should use REST-style resources with explicit service-layer validation. Internal service methods may be implemented as application services, but public module contracts should remain resource-oriented.

### 6.2 Base Path

```text
/api/procurement/std-it-wizard
```

### 6.3 Common Request Headers

| Header | Required | Description |
|---|---:|---|
| `Authorization` | Yes | Bearer token or platform session token |
| `X-Request-Id` | Yes | Idempotency and traceability |
| `X-Org-Id` | Yes | Procuring Entity context |
| `X-User-Id` | Yes | Authenticated user context |
| `X-Role-Context` | Conditional | Active role where user has multiple roles |

### 6.4 Common Response Envelope

```json
{
  "success": true,
  "data": {},
  "warnings": [],
  "errors": [],
  "audit_event_id": "AUD-000000"
}
```

### 6.5 Error Envelope

```json
{
  "success": false,
  "data": null,
  "warnings": [],
  "errors": [
    {
      "code": "STD_IT_VALIDATION_FAILED",
      "message": "The tender submission deadline must be after the clarification deadline.",
      "field_path": "tds.submission.deadline_at",
      "severity": "BLOCKER"
    }
  ],
  "audit_event_id": "AUD-000001"
}
```

### 6.6 Common Status Codes

| Status | Meaning |
|---:|---|
| 200 | Success |
| 201 | Created |
| 202 | Accepted for asynchronous processing |
| 400 | Invalid input |
| 401 | Not authenticated |
| 403 | Permission denied |
| 404 | Resource not found |
| 409 | State conflict or immutable resource |
| 422 | Business validation failed |
| 423 | Locked resource |
| 500 | Unexpected server error |

---

## 7. Primary Resource Model

### 7.1 Main Resources

| Resource | Purpose |
|---|---|
| `ITTenderConfiguration` | Tender-specific STD configuration instance |
| `ITTenderConfigurationSectionStatus` | Tracks completion/validation status by wizard section |
| `ITTDSConfiguration` | Tender Data Sheet values |
| `ITSCCConfiguration` | Special Conditions of Contract values |
| `ITRequirementSet` | Functional/technical/service requirements |
| `ITRequirementItem` | Individual structured requirement |
| `ITImplementationSchedule` | Phases, milestones, deliverables, acceptance points |
| `ITSystemInventory` | System inventory and supply/recurrent items |
| `ITPriceScheduleConfiguration` | Price schedule structure |
| `ITEvaluationConfiguration` | Evaluation and qualification settings |
| `ITFormActivationConfiguration` | Tendering form activation settings |
| `ITEvidenceRequirementConfiguration` | Evidence/document requirements |
| `ITWizardValidationRun` | Validation execution and findings |
| `ITWizardRenderPreview` | Rendered previews |
| `ITWizardApprovalRequest` | Review and approval workflow request |
| `ITGeneratedTenderBundle` | Immutable generated output bundle |
| `ITAddendumImpactAssessment` | Impact of post-publication changes |

---

## 8. Wizard State Model

### 8.1 States

| State | Description |
|---|---|
| `DRAFT` | Created but incomplete |
| `IN_CONFIGURATION` | Being actively configured |
| `VALIDATION_FAILED` | Contains blocking findings |
| `READY_FOR_REVIEW` | Complete and submitted for review |
| `RETURNED_FOR_CORRECTION` | Reviewer returned it to preparer |
| `PROCUREMENT_REVIEW` | Under procurement review |
| `TECHNICAL_REVIEW` | Under technical review, where required |
| `LEGAL_REVIEW` | Under legal review, where required |
| `APPROVED_FOR_TENDER_CREATION` | Approved but not yet bound to tender shell |
| `BOUND_TO_TENDER` | Bound to a tender record |
| `PUBLISHED` | Generated bundle published and immutable |
| `ADDENDUM_REQUIRED` | Material change requires addendum |
| `SUPERSEDED_BY_ADDENDUM` | Replaced by an addendum configuration |
| `CANCELLED` | Cancelled before publication |

### 8.2 Transition Summary

| From | To | Actor | Required Checks |
|---|---|---|---|
| `DRAFT` | `IN_CONFIGURATION` | Preparer | Active STD version selected |
| `IN_CONFIGURATION` | `VALIDATION_FAILED` | System | Blocking validation findings exist |
| `IN_CONFIGURATION` | `READY_FOR_REVIEW` | Preparer | No blockers, required sections complete |
| `VALIDATION_FAILED` | `IN_CONFIGURATION` | Preparer | User resumes editing |
| `READY_FOR_REVIEW` | `PROCUREMENT_REVIEW` | Procurement Reviewer | Assignment accepted |
| `PROCUREMENT_REVIEW` | `TECHNICAL_REVIEW` | Procurement Reviewer | Technical review required |
| `PROCUREMENT_REVIEW` | `LEGAL_REVIEW` | Procurement Reviewer | Legal review required |
| `TECHNICAL_REVIEW` | `PROCUREMENT_REVIEW` | Technical Reviewer | Technical review complete |
| `LEGAL_REVIEW` | `PROCUREMENT_REVIEW` | Legal Reviewer | Legal review complete |
| `PROCUREMENT_REVIEW` | `RETURNED_FOR_CORRECTION` | Reviewer | Correction reason required |
| `RETURNED_FOR_CORRECTION` | `IN_CONFIGURATION` | Preparer | Correction acknowledged |
| `PROCUREMENT_REVIEW` | `APPROVED_FOR_TENDER_CREATION` | Approver | All review gates passed |
| `APPROVED_FOR_TENDER_CREATION` | `BOUND_TO_TENDER` | Tender Officer | Tender shell exists |
| `BOUND_TO_TENDER` | `PUBLISHED` | Tender Publisher | Generated bundle hash created |
| `PUBLISHED` | `ADDENDUM_REQUIRED` | System/Authorized User | Material change requested |
| `ADDENDUM_REQUIRED` | `SUPERSEDED_BY_ADDENDUM` | Approver | Addendum approved and published |
| Any pre-publication state | `CANCELLED` | Authorized User | Cancellation reason required |

---

## 9. Permissions Contract

### 9.1 Permission Keys

| Permission | Description |
|---|---|
| `std_it_wizard.create` | Create IT tender configuration |
| `std_it_wizard.view` | View IT tender configuration |
| `std_it_wizard.edit` | Edit draft/in-configuration values |
| `std_it_wizard.delete_draft` | Delete unbound draft configuration |
| `std_it_wizard.validate` | Run validation |
| `std_it_wizard.preview` | Generate preview |
| `std_it_wizard.submit_review` | Submit for review |
| `std_it_wizard.review_procurement` | Conduct procurement review |
| `std_it_wizard.review_technical` | Conduct technical review |
| `std_it_wizard.review_legal` | Conduct legal review |
| `std_it_wizard.approve` | Approve configuration for tender creation |
| `std_it_wizard.return` | Return configuration for correction |
| `std_it_wizard.bind_tender` | Bind approved configuration to tender |
| `std_it_wizard.publish_bundle` | Publish generated tender bundle |
| `std_it_wizard.create_addendum_assessment` | Assess addendum impact |
| `std_it_wizard.approve_addendum` | Approve addendum configuration |
| `std_it_wizard.audit_view` | View audit events |

### 9.2 Role Mapping

| Role | Key Permissions |
|---|---|
| Procurement Preparer | create, view, edit, validate, preview, submit_review |
| Procurement Reviewer | view, validate, preview, review_procurement, return |
| Technical Reviewer | view, review_technical, return |
| Legal Reviewer | view, review_legal, return |
| Procurement Approver | view, approve, return |
| Tender Publisher | view, bind_tender, publish_bundle |
| Auditor | view, audit_view |
| System Administrator | configuration support only; no override of legal immutability |

---

## 10. API Contract

## 10.1 Configuration Instance APIs

### 10.1.1 Create IT Tender Configuration

```http
POST /api/procurement/std-it-wizard/configurations
```

#### Request

```json
{
  "std_template_version_id": "STDVER-KE-PPRA-IT-2022-04",
  "procurement_plan_item_id": "PPLAN-000001",
  "title": "Supply, Installation, Configuration, Customization, Testing, Commissioning and Maintenance of an ERP System",
  "procurement_entity_id": "PE-000001",
  "created_from_calibration_fixture_id": null
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "configuration_id": "ITCFG-000001",
    "state": "DRAFT",
    "std_template_version_id": "STDVER-KE-PPRA-IT-2022-04",
    "section_statuses": [
      { "section_key": "tender_identity", "status": "INCOMPLETE" },
      { "section_key": "tds", "status": "INCOMPLETE" },
      { "section_key": "requirements", "status": "INCOMPLETE" }
    ]
  },
  "warnings": [],
  "errors": [],
  "audit_event_id": "AUD-000001"
}
```

#### Rules

1. The STD Template Version must be `ACTIVE`.
2. The STD Template Version must belong to an IT-compatible STD family.
3. The procurement plan item must exist and be usable by the Procuring Entity.
4. A configuration may not be created from a superseded STD version unless expressly permitted for continuation of an already-started tender.

---

### 10.1.2 Get Configuration Summary

```http
GET /api/procurement/std-it-wizard/configurations/{configuration_id}
```

#### Response

```json
{
  "success": true,
  "data": {
    "configuration_id": "ITCFG-000001",
    "title": "Supply and Installation of ERP System",
    "state": "IN_CONFIGURATION",
    "std_template_version_id": "STDVER-KE-PPRA-IT-2022-04",
    "std_template_version_label": "KE-PPRA-IT-2022-04",
    "procurement_entity_id": "PE-000001",
    "procurement_plan_item_id": "PPLAN-000001",
    "completion_percent": 62,
    "validation_status": "HAS_WARNINGS",
    "last_validation_run_id": "VALRUN-000006",
    "bound_tender_id": null,
    "published_bundle_id": null,
    "created_at": "2026-07-08T10:00:00Z",
    "updated_at": "2026-07-08T12:00:00Z"
  },
  "warnings": [],
  "errors": [],
  "audit_event_id": null
}
```

---

### 10.1.3 List Configurations

```http
GET /api/procurement/std-it-wizard/configurations?state=IN_CONFIGURATION&procurement_entity_id=PE-000001
```

#### Supported Filters

| Filter | Type | Description |
|---|---|---|
| `state` | enum | Configuration state |
| `procurement_entity_id` | string | Procuring Entity |
| `std_template_version_id` | string | STD version |
| `created_by` | string | Creator |
| `bound_tender_id` | string | Bound tender |
| `q` | string | Search title/reference |
| `page` | integer | Page number |
| `page_size` | integer | Page size |

---

### 10.1.4 Delete Draft Configuration

```http
DELETE /api/procurement/std-it-wizard/configurations/{configuration_id}
```

#### Rules

1. Only `DRAFT` configurations may be deleted.
2. Configurations that have been submitted for review, bound to tender, or published must never be deleted.
3. Deletion must create an audit event.

---

## 10.2 TDS APIs

### 10.2.1 Get TDS Schema and Current Values

```http
GET /api/procurement/std-it-wizard/configurations/{configuration_id}/tds
```

#### Response

```json
{
  "success": true,
  "data": {
    "schema_version": "tds-schema-it-2022-04-v0.2",
    "values": {
      "tender_name": "",
      "tender_number": "",
      "procurement_method": "OPEN_NATIONAL",
      "alternative_tenders_allowed": false,
      "currency": "KES",
      "tender_validity_days": null,
      "submission_deadline_at": null,
      "opening_at": null,
      "electronic_tenders_allowed": null,
      "jv_max_members": null,
      "tender_security_type": null,
      "tender_security_amount": null,
      "pre_tender_meeting_required": null
    },
    "field_metadata": [
      {
        "field_key": "tender_validity_days",
        "label": "Tender validity period in days",
        "type": "integer",
        "required": true,
        "source_anchor": "IT_STD:Section_II:TDS"
      }
    ]
  },
  "warnings": [],
  "errors": [],
  "audit_event_id": null
}
```

---

### 10.2.2 Update TDS Values

```http
PATCH /api/procurement/std-it-wizard/configurations/{configuration_id}/tds
```

#### Request

```json
{
  "values": {
    "tender_name": "Supply, Installation, Configuration, Customization, Testing, Commissioning and Maintenance of an ERP System",
    "tender_number": "NSSFSPS/ICT/ERP/001/2025-2026",
    "procurement_method": "OPEN_NATIONAL",
    "currency": "KES",
    "alternative_tenders_allowed": false,
    "jv_max_members": 3,
    "tender_validity_days": 154,
    "submission_deadline_at": "2026-06-30T11:00:00+03:00",
    "opening_at": "2026-06-30T11:00:00+03:00",
    "electronic_tenders_allowed": false,
    "tender_security_type": "PROFESSIONAL_INDEMNITY",
    "tender_security_amount": 500000
  },
  "change_reason": "Initial TDS configuration"
}
```

#### Rules

1. The configuration must be editable.
2. The submitted fields must exist in the STD TDS schema.
3. Locked STD fields must not be updated through this endpoint.
4. Date and sequencing validations may run immediately, but final validation occurs through the validation API.
5. Every material change must produce a value-change audit event.

---

## 10.3 SCC APIs

### 10.3.1 Get SCC Schema and Values

```http
GET /api/procurement/std-it-wizard/configurations/{configuration_id}/scc
```

### 10.3.2 Update SCC Values

```http
PATCH /api/procurement/std-it-wizard/configurations/{configuration_id}/scc
```

#### Request

```json
{
  "values": {
    "performance_security_percent": 10,
    "performance_security_validity_days_after_contract_end": 60,
    "warranty_period_months": 12,
    "governing_law": "Kenya",
    "dispute_resolution_method": "ADJUDICATION_THEN_ARBITRATION",
    "payment_milestones": [
      {
        "milestone_key": "contract_signing",
        "description": "Upon contract signing and commencement",
        "percentage": 20
      },
      {
        "milestone_key": "phase_1_uat",
        "description": "Upon completion of Phase 1 implementation and UAT sign-off",
        "percentage": 30
      }
    ]
  },
  "change_reason": "Initial SCC configuration"
}
```

#### Rules

1. Payment milestone totals must equal 100% unless retention or framework-based pricing is explicitly configured.
2. Performance security value must comply with the active STD rule catalog.
3. Warranty and acceptance terms must align with implementation phases.
4. SCC values must be carried forward into contract generation after award.

---

## 10.4 Requirement Composer APIs

### 10.4.1 Get Requirement Set

```http
GET /api/procurement/std-it-wizard/configurations/{configuration_id}/requirements
```

### 10.4.2 Create Requirement Category

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/requirements/categories
```

#### Request

```json
{
  "category_key": "pension_administration",
  "title": "Pension Administration Module",
  "requirement_type": "FUNCTIONAL",
  "display_order": 10,
  "mandatory_by_default": true
}
```

---

### 10.4.3 Create Requirement Item

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/requirements/items
```

#### Request

```json
{
  "category_key": "pension_administration",
  "requirement_code": "PA-001",
  "requirement_type": "FUNCTIONAL",
  "title": "Member bio-data management",
  "description": "The System must register and maintain full member records with maker-checker controls and full audit trail.",
  "priority": "MANDATORY",
  "supplier_response_required": true,
  "evidence_required": true,
  "evidence_types": ["TECHNICAL_PROPOSAL_REFERENCE", "SCREENSHOT_OR_BROCHURE", "IMPLEMENTATION_REFERENCE"],
  "evaluation_binding": {
    "technical_scoring_category_key": "technical_solution_proposal",
    "conformance_mode": "YES_NO_REFERENCE"
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "requirement_item_id": "REQ-000001",
    "requirement_code": "PA-001",
    "status": "ACTIVE_IN_CONFIGURATION"
  },
  "warnings": [],
  "errors": [],
  "audit_event_id": "AUD-REQ-000001"
}
```

---

### 10.4.4 Bulk Import Requirement Items

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/requirements/items/import
```

#### Request

```json
{
  "import_mode": "VALIDATE_ONLY",
  "source_format": "CSV",
  "file_id": "FILE-000001",
  "mapping": {
    "requirement_code": "No.",
    "description": "Requirement Description",
    "priority": "Compliance"
  }
}
```

#### Rules

1. Bulk import must validate before commit.
2. Duplicate requirement codes must be blocked unless update mode is explicitly selected.
3. Every imported requirement must have a category, type, priority, and supplier response mode.
4. Requirements must be rendered as obligations using controlled language where possible.

---

### 10.4.5 Update Requirement Item

```http
PATCH /api/procurement/std-it-wizard/configurations/{configuration_id}/requirements/items/{requirement_item_id}
```

#### Rules

1. Requirement changes before publication are allowed subject to state and permission.
2. Requirement changes after publication must trigger addendum impact assessment.
3. Requirement deletion after review submission should be soft delete with audit trace.

---

## 10.5 Implementation Schedule APIs

### 10.5.1 Get Implementation Schedule

```http
GET /api/procurement/std-it-wizard/configurations/{configuration_id}/implementation-schedule
```

### 10.5.2 Add Phase

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/implementation-schedule/phases
```

#### Request

```json
{
  "phase_code": "PHASE_1",
  "title": "Phase 1 — Financial Year 2026/2027",
  "description": "Implementation of core modules",
  "planned_start_date": "2026-07-01",
  "planned_end_date": "2027-06-30",
  "location": "Nairobi, Kenya",
  "display_order": 1
}
```

### 10.5.3 Add Milestone

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/implementation-schedule/milestones
```

#### Request

```json
{
  "phase_code": "PHASE_1",
  "milestone_code": "PH1-UAT",
  "title": "Phase 1 UAT Sign-Off",
  "deliverables": [
    "Configured Phase 1 modules",
    "User acceptance test report",
    "Signed acceptance certificate"
  ],
  "acceptance_required": true,
  "payment_binding_key": "phase_1_uat",
  "display_order": 20
}
```

#### Rules

1. Milestones may bind to SCC payment milestones.
2. Acceptance milestones must generate contract carry-forward data.
3. Phase dates must not contradict tender or contract dates.
4. Each phase must contain at least one milestone before publication.

---

## 10.6 System Inventory APIs

### 10.6.1 Get System Inventory

```http
GET /api/procurement/std-it-wizard/configurations/{configuration_id}/system-inventory
```

### 10.6.2 Add Inventory Item

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/system-inventory/items
```

#### Request

```json
{
  "inventory_type": "SUPPLY_AND_INSTALLATION",
  "item_code": "SW-001",
  "description": "ERP core platform licenses and configuration services",
  "quantity": 1,
  "unit": "Lot",
  "phase_code": "PHASE_1",
  "requirement_refs": ["REQ-000001", "REQ-000002"],
  "price_schedule_binding_key": "supply_installation_sub_table"
}
```

### 10.6.3 Add Recurrent Cost Item

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/system-inventory/items
```

#### Request

```json
{
  "inventory_type": "RECURRENT",
  "item_code": "REC-001",
  "description": "Annual maintenance and support",
  "quantity": 1,
  "unit": "Year",
  "recurrence_period": "ANNUAL",
  "support_year_start": 1,
  "support_year_end": 3,
  "price_schedule_binding_key": "recurrent_cost_sub_table"
}
```

#### Rules

1. Supply/installation and recurrent inventory items must be separated.
2. Inventory items may link to requirements, milestones, and price schedule lines.
3. Items used in price schedule schemas must be present in inventory unless marked as lump-sum service.
4. Deleting an inventory item referenced by a requirement, price schedule, or milestone must be blocked or require explicit unlinking.

---

## 10.7 Price Schedule APIs

### 10.7.1 Get Price Schedule Configuration

```http
GET /api/procurement/std-it-wizard/configurations/{configuration_id}/price-schedule
```

### 10.7.2 Update Price Schedule Configuration

```http
PATCH /api/procurement/std-it-wizard/configurations/{configuration_id}/price-schedule
```

#### Request

```json
{
  "pricing_mode": "STRUCTURED_IT_PRICE_SCHEDULE",
  "currency": "KES",
  "vat_treatment": "VAT_STATED_SEPARATELY",
  "allow_price_adjustment": false,
  "include_supply_installation_summary": true,
  "include_recurrent_cost_summary": true,
  "include_country_of_origin_table": true,
  "recurrent_cost_evaluation_years": 3,
  "financial_evaluation_basis": "LOWEST_EVALUATED_TOTAL_COST"
}
```

#### Rules

1. Price adjustment may only be enabled if allowed by STD rules.
2. Recurrent cost evaluation period must be defined where recurrent costs are part of evaluation.
3. Currency must match TDS unless multi-currency mode is permitted.
4. VAT treatment must be consistent across Form of Tender, price schedules, and financial evaluation.

---

## 10.8 Evaluation Configuration APIs

### 10.8.1 Get Evaluation Configuration

```http
GET /api/procurement/std-it-wizard/configurations/{configuration_id}/evaluation
```

### 10.8.2 Update Evaluation Configuration

```http
PATCH /api/procurement/std-it-wizard/configurations/{configuration_id}/evaluation
```

#### Request

```json
{
  "evaluation_method": "THREE_STAGE_PRELIM_TECH_FINANCIAL",
  "technical_scoring_enabled": true,
  "technical_pass_mark": 75,
  "financial_evaluation_basis": "LOWEST_EVALUATED_RESPONSIVE_TENDER",
  "margin_of_preference_enabled": false,
  "abnormally_low_high_check_enabled": true,
  "mandatory_requirements": [
    {
      "criterion_code": "MAND-001",
      "description": "Valid Certificate of Incorporation or Registration",
      "supporting_document": "Certificate of Incorporation/Registration",
      "failure_effect": "DISQUALIFICATION"
    }
  ],
  "technical_scoring_criteria": [
    {
      "criterion_code": "TECH-001",
      "title": "Company Profile, Experience and Past Performance",
      "maximum_points": 20
    },
    {
      "criterion_code": "TECH-002",
      "title": "Technical Solution Proposal",
      "maximum_points": 25
    }
  ]
}
```

#### Rules

1. Technical scoring total must equal 100 where scoring is enabled unless the STD version explicitly permits a different total.
2. Technical pass mark must fall within STD-permitted bounds.
3. Mandatory requirements must be pass/fail and must define supporting documentation.
4. Evaluation criteria must not introduce criteria prohibited by the STD.
5. Financial evaluation must be tied to the price schedule configuration.

---

## 10.9 Form and Evidence APIs

### 10.9.1 Get Form Activation Configuration

```http
GET /api/procurement/std-it-wizard/configurations/{configuration_id}/forms
```

### 10.9.2 Update Form Activation Configuration

```http
PATCH /api/procurement/std-it-wizard/configurations/{configuration_id}/forms
```

#### Request

```json
{
  "forms": [
    {
      "form_key": "form_of_tender",
      "active": true,
      "required_for_submission": true
    },
    {
      "form_key": "confidential_business_questionnaire",
      "active": true,
      "required_for_submission": true
    },
    {
      "form_key": "tender_security_demand_bank_guarantee",
      "active": false,
      "required_for_submission": false,
      "deactivation_reason": "Professional indemnity selected instead"
    }
  ]
}
```

#### Rules

1. Mandatory STD forms cannot be deactivated unless the STD rule catalog permits conditional deactivation.
2. Active forms required for submission must be exposed to the Supplier Portal.
3. Form activation must align with TDS settings, tender security type, JV settings, and procurement method.

---

### 10.9.3 Configure Evidence Requirements

```http
PATCH /api/procurement/std-it-wizard/configurations/{configuration_id}/evidence-requirements
```

#### Request

```json
{
  "evidence_requirements": [
    {
      "evidence_key": "tax_compliance_certificate",
      "title": "Valid Tax Compliance Certificate",
      "required": true,
      "applies_to": "ALL_TENDERERS",
      "linked_criterion_code": "MAND-002",
      "allowed_file_types": ["pdf", "jpg", "png"],
      "expiry_date_required": true
    }
  ]
}
```

---

## 10.10 Validation APIs

### 10.10.1 Run Validation

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/validation-runs
```

#### Request

```json
{
  "validation_scope": "FULL",
  "include_render_validation": true,
  "include_cross_module_validation": true
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "validation_run_id": "VALRUN-000001",
    "status": "COMPLETED",
    "result": "HAS_BLOCKERS",
    "summary": {
      "blockers": 2,
      "warnings": 5,
      "info": 3
    },
    "findings": [
      {
        "finding_id": "FIND-000001",
        "severity": "BLOCKER",
        "rule_key": "DATES.SUBMISSION_AFTER_CLARIFICATION",
        "message": "Submission deadline must be after the clarification deadline.",
        "field_path": "tds.submission_deadline_at",
        "resolution_hint": "Set submission deadline later than the clarification deadline."
      }
    ]
  },
  "warnings": [],
  "errors": [],
  "audit_event_id": "AUD-VAL-000001"
}
```

### 10.10.2 Get Validation Findings

```http
GET /api/procurement/std-it-wizard/configurations/{configuration_id}/validation-runs/{validation_run_id}/findings
```

### 10.10.3 Resolve Manual Finding

```http
PATCH /api/procurement/std-it-wizard/configurations/{configuration_id}/validation-findings/{finding_id}
```

#### Request

```json
{
  "status": "ACKNOWLEDGED",
  "resolution_note": "Reviewed by procurement reviewer; warning accepted because no pre-tender meeting is required.",
  "supporting_attachment_id": null
}
```

#### Rules

1. Blockers cannot be manually waived unless the rule explicitly supports authorized override.
2. Overrides must require reason, approver identity, and audit event.
3. Legal immutability blockers must never be overridden.

---

## 10.11 Preview and Render APIs

### 10.11.1 Generate Preview

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/previews
```

#### Request

```json
{
  "preview_scope": "FULL_TENDER_DOCUMENT",
  "format": "HTML",
  "include_watermark": true,
  "watermark_text": "DRAFT PREVIEW - NOT FOR PUBLICATION"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "preview_id": "PREVIEW-000001",
    "status": "READY",
    "format": "HTML",
    "artifact_url": "/documents/previews/PREVIEW-000001",
    "render_hash": "sha256:...",
    "generated_at": "2026-07-08T12:30:00Z"
  },
  "warnings": [],
  "errors": [],
  "audit_event_id": "AUD-REN-000001"
}
```

### 10.11.2 Generate Section Preview

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/previews/sections/{section_key}
```

#### Rules

1. Draft previews must be watermarked.
2. Preview render hash must not be treated as publication hash.
3. Preview generation must not change configuration state.
4. Render failures must create validation findings where applicable.

---

## 10.12 Review and Approval APIs

### 10.12.1 Submit for Review

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/submit-review
```

#### Request

```json
{
  "submission_note": "Configuration completed and ready for procurement review.",
  "requested_review_tracks": ["PROCUREMENT", "TECHNICAL", "LEGAL"]
}
```

#### Rules

1. Full validation must have run successfully.
2. No blocking findings may remain unresolved.
3. Required sections must be complete.
4. Review tracks may be derived from STD rules and tender complexity.

---

### 10.12.2 Return for Correction

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/return-for-correction
```

#### Request

```json
{
  "return_reason": "The implementation schedule does not identify acceptance milestones for Phase 2.",
  "return_items": [
    {
      "section_key": "implementation_schedule",
      "field_path": "phases.PHASE_2.milestones",
      "comment": "Add Phase 2 acceptance certificate milestone."
    }
  ]
}
```

---

### 10.12.3 Approve Configuration

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/approve
```

#### Request

```json
{
  "approval_note": "Approved for tender creation.",
  "approval_basis": "Procurement, technical, and legal review completed."
}
```

#### Rules

1. User must have approval permission.
2. All required review tracks must be complete.
3. No unresolved blockers may exist.
4. The configuration must be locked against ordinary editing after approval.

---

## 10.13 Tender Binding and Publication APIs

### 10.13.1 Bind to Tender

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/bind-tender
```

#### Request

```json
{
  "tender_id": "TDR-000001",
  "binding_note": "Binding approved IT STD configuration to tender shell."
}
```

#### Rules

1. Configuration must be `APPROVED_FOR_TENDER_CREATION`.
2. Tender shell must belong to the same Procuring Entity.
3. Tender shell procurement category must be compatible with the STD family.
4. One published tender must not bind to multiple active STD configurations unless addendum/supersession logic applies.

---

### 10.13.2 Generate Publication Bundle

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/publication-bundles
```

#### Request

```json
{
  "formats": ["PDF", "HTML", "DOCX"],
  "publication_note": "Generate final tender document bundle for publication.",
  "include_machine_readable_package": true
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "bundle_id": "BUNDLE-000001",
    "status": "GENERATED",
    "bundle_hash": "sha256:...",
    "artifacts": [
      {
        "artifact_type": "FULL_TENDER_DOCUMENT",
        "format": "PDF",
        "url": "/documents/tenders/BUNDLE-000001/full.pdf",
        "hash": "sha256:..."
      },
      {
        "artifact_type": "SUPPLIER_RESPONSE_SCHEMA",
        "format": "JSON",
        "url": "/documents/tenders/BUNDLE-000001/supplier-response-schema.json",
        "hash": "sha256:..."
      }
    ]
  },
  "warnings": [],
  "errors": [],
  "audit_event_id": "AUD-PUB-000001"
}
```

#### Rules

1. Configuration must be `BOUND_TO_TENDER`.
2. Full validation must pass immediately before bundle generation.
3. Bundle contents must be immutable after publication.
4. All generated artifacts must be hashed.
5. Published bundle must record STD version, configuration version, render profile, generation timestamp, and actor.

---

## 10.14 Addendum Impact APIs

### 10.14.1 Create Addendum Impact Assessment

```http
POST /api/procurement/std-it-wizard/configurations/{configuration_id}/addendum-impact-assessments
```

#### Request

```json
{
  "proposed_changes": [
    {
      "change_type": "UPDATE_REQUIREMENT",
      "target_id": "REQ-000001",
      "field_path": "description",
      "new_value": "Updated requirement text",
      "reason": "Clarification issued following bidder query"
    }
  ]
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "assessment_id": "ADDIMP-000001",
    "materiality": "MATERIAL",
    "requires_addendum": true,
    "affected_outputs": [
      "FULL_TENDER_DOCUMENT",
      "SUPPLIER_RESPONSE_SCHEMA",
      "EVALUATION_SCHEMA"
    ],
    "affected_sections": [
      "technical_requirements",
      "evaluation_criteria"
    ],
    "recommendation": "Create addendum configuration and regenerate affected publication bundle."
  },
  "warnings": [],
  "errors": [],
  "audit_event_id": "AUD-ADD-000001"
}
```

#### Rules

1. Published tender changes must not mutate the original bundle.
2. Material changes must create addenda.
3. Addendum outputs must reference the original bundle and the changed sections.
4. Supplier Portal and Evaluation Module must be notified of schema-impacting addenda.

---

## 10.15 Audit APIs

### 10.15.1 List Audit Events

```http
GET /api/procurement/std-it-wizard/configurations/{configuration_id}/audit-events
```

### 10.15.2 Get Audit Event Detail

```http
GET /api/procurement/std-it-wizard/audit-events/{audit_event_id}
```

#### Required Audit Event Fields

| Field | Description |
|---|---|
| `audit_event_id` | Unique audit ID |
| `configuration_id` | Related configuration |
| `actor_user_id` | Acting user |
| `actor_role` | Active role |
| `event_type` | Event key |
| `before_value_hash` | Hash before change, where applicable |
| `after_value_hash` | Hash after change, where applicable |
| `field_path` | Changed field path |
| `change_reason` | User or system reason |
| `created_at` | Timestamp |
| `ip_address` | Request IP, where available |
| `request_id` | Request correlation ID |

---

## 11. Service Contract

## 11.1 Application Services

| Service | Responsibility |
|---|---|
| `ITWizardConfigurationService` | Create, retrieve, update configuration shell |
| `ITTDSConfigurationService` | Manage TDS values |
| `ITSCCConfigurationService` | Manage SCC values |
| `ITRequirementComposerService` | Manage requirement categories and items |
| `ITImplementationScheduleService` | Manage phases, milestones, deliverables, acceptance points |
| `ITSystemInventoryService` | Manage supply/install and recurrent inventory items |
| `ITPriceScheduleService` | Configure price schedule structures |
| `ITEvaluationConfigurationService` | Manage evaluation and qualification settings |
| `ITFormEvidenceService` | Manage form activation and evidence requirements |
| `ITWizardValidationService` | Run STD-backed validations |
| `ITWizardRenderService` | Generate previews and publication bundles |
| `ITWizardGovernanceService` | Manage state transitions and review workflow |
| `ITWizardTenderBindingService` | Bind approved configuration to tender shell |
| `ITWizardAddendumService` | Assess post-publication changes and create addendum flows |
| `ITWizardAuditService` | Create and retrieve audit events |
| `ITWizardExportService` | Export configuration package for diagnostics and migration |

---

## 11.2 Service Method Examples

### 11.2.1 `ITWizardValidationService.run_full_validation`

#### Input

```json
{
  "configuration_id": "ITCFG-000001",
  "requested_by": "USER-000001",
  "validation_scope": "FULL"
}
```

#### Output

```json
{
  "validation_run_id": "VALRUN-000001",
  "result": "PASS",
  "blockers": 0,
  "warnings": 2,
  "info": 5
}
```

#### Required Internal Steps

1. Load configuration.
2. Load active STD version schema snapshot.
3. Load rule catalog.
4. Validate TDS.
5. Validate SCC.
6. Validate requirements.
7. Validate implementation schedule.
8. Validate system inventory.
9. Validate price schedule.
10. Validate evaluation criteria.
11. Validate forms and evidence requirements.
12. Validate render block dependencies.
13. Persist findings.
14. Update section statuses.
15. Create audit event.

---

### 11.2.2 `ITWizardRenderService.generate_publication_bundle`

#### Input

```json
{
  "configuration_id": "ITCFG-000001",
  "formats": ["PDF", "HTML", "DOCX"],
  "include_machine_readable_package": true
}
```

#### Output

```json
{
  "bundle_id": "BUNDLE-000001",
  "bundle_hash": "sha256:...",
  "artifact_count": 4
}
```

#### Required Internal Steps

1. Check configuration state.
2. Run full validation.
3. Load render blocks from STD Engine Core.
4. Merge tender-specific values with locked STD content.
5. Generate full tender document.
6. Generate supplier response schema.
7. Generate evaluation schema.
8. Generate contract carry-forward package.
9. Hash all artifacts.
10. Persist immutable bundle.
11. Update configuration state to `PUBLISHED`.
12. Notify Tender Management.
13. Create audit event.

---

## 12. UI Contract

## 12.1 UI Navigation

The IT Tender Configuration Wizard should be presented as a guided multi-step workflow with persistent validation status.

### 12.1.1 Primary Wizard Steps

| Step | Screen | Purpose |
|---:|---|---|
| 1 | Tender Identity | Select STD version, tender title, tender number, procurement plan item |
| 2 | Procurement Method and Participation | Method, national/international, reservation, lots, JV, alternatives |
| 3 | Dates, Clarifications, and Opening | Clarification, pre-tender meeting, submission, opening, validity |
| 4 | Tender Security / Professional Indemnity | Security type, amount, validity, form activation |
| 5 | Procuring Entity Details | Entity, contacts, submission/opening addresses |
| 6 | IT Requirements Overview | Business objectives, scope, expected outcomes |
| 7 | Technical Requirements Composer | Functional, architectural, performance, technology, service requirements |
| 8 | Implementation Schedule | Phases, milestones, deliverables, acceptance points, locations |
| 9 | System Inventory | Supply/install and recurrent inventory items |
| 10 | Price Schedule Setup | Price tables, currency, VAT, recurrent cost evaluation |
| 11 | Evaluation and Qualification | Mandatory requirements, scoring criteria, pass mark, financial evaluation |
| 12 | Forms and Evidence | Tendering forms, supplier documents, evidence requirements |
| 13 | SCC and Contract Parameters | Securities, payment milestones, warranty, dispute resolution, IP |
| 14 | Validation | Findings, blockers, warnings, resolution paths |
| 15 | Preview | Draft tender document and generated schemas |
| 16 | Review and Approval | Submit, review, approve, return, bind to tender |

---

## 12.2 Global UI Components

### 12.2.1 Header Summary

Every screen must show:

1. Tender title.
2. Tender number, if assigned.
3. STD version.
4. Configuration state.
5. Completion percentage.
6. Validation status.
7. Last saved timestamp.
8. Last validation timestamp.

### 12.2.2 Section Status Rail

Each wizard step must show status:

| Status | Meaning |
|---|---|
| `NOT_STARTED` | No data entered |
| `IN_PROGRESS` | Partial data entered |
| `COMPLETE` | Required fields complete |
| `HAS_WARNINGS` | Complete but contains warnings |
| `HAS_BLOCKERS` | Contains blockers |
| `LOCKED` | Not editable in current state |

### 12.2.3 Validation Panel

Validation panel must show:

1. Findings grouped by severity.
2. Findings grouped by wizard step.
3. Rule key.
4. Field path.
5. Resolution hint.
6. Link to affected field.
7. Override action only if permitted.

### 12.2.4 Source Trace Panel

For fields derived from the STD schema, the UI should expose source trace metadata:

1. STD section.
2. Clause or form reference.
3. Mutability classification.
4. Source anchor.
5. Rule dependencies.

This is important for reviewer confidence and audit defensibility.

---

## 13. Screen-Level UI Requirements

## 13.1 Tender Identity Screen

### Required Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| STD Template Version | Select | Yes | Only active compatible versions |
| Procurement Plan Item | Select | Yes | Must belong to PE |
| Tender Name | Text | Yes | Appears in cover, ITT, TDS |
| Tender Number | Text | Yes | Unique within PE/year |
| Procurement Entity | Read-only/Select | Yes | Based on org context |
| Tender Description | Long text | Yes | Used in invitation and scope |

### Actions

1. Save draft.
2. Validate step.
3. Continue.

### Blockers

1. Inactive STD version.
2. Missing procurement plan item.
3. Duplicate tender number.

---

## 13.2 Procurement Method and Participation Screen

### Required Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| Procurement Method | Enum | Yes | Open National, Open International, Restricted, etc. |
| Reservation Applies | Boolean | Yes | Enables reservation fields |
| Reservation Group | Select | Conditional | Required if reservation applies |
| Lots Allowed | Boolean | Yes | Enables lot configuration |
| Alternative Tenders Allowed | Boolean | Yes | Controls alternative tender forms/rules |
| JV Allowed | Boolean | Yes | Controls JV form requirements |
| Max JV Members | Integer | Conditional | Required if JV allowed |
| Foreign Tenderer 40% Rule Applies | Boolean | Conditional | Based on method and participation |

---

## 13.3 Dates, Clarifications, and Opening Screen

### Required Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| Clarification Address | Structured address | Yes | Used in TDS/ITT |
| Clarification Deadline | DateTime | Yes | Must precede submission deadline |
| Pre-Tender Meeting Required | Boolean | Yes | Enables meeting details |
| Pre-Tender Meeting Date | DateTime | Conditional | Required if meeting required |
| Submission Deadline | DateTime | Yes | Must precede or equal opening time per rules |
| Opening DateTime | DateTime | Yes | Typically immediately after deadline |
| Tender Validity Days | Integer | Yes | Used in Form of Tender and TDS |

---

## 13.4 IT Requirements Composer Screen

### Layout

The screen should support:

1. Requirement categories in left navigation.
2. Requirement table in main pane.
3. Requirement detail drawer.
4. Bulk import action.
5. Conformance matrix preview.
6. Evaluation binding panel.

### Requirement Table Columns

| Column | Description |
|---|---|
| Requirement Code | Unique code |
| Category | Functional/technical/service category |
| Requirement Type | Functional, architectural, performance, etc. |
| Description | Obligation text |
| Priority | Mandatory/Desirable/Informational |
| Supplier Response Required | Yes/No |
| Evidence Required | Yes/No |
| Evaluation Binding | Linked scoring/checklist criterion |
| Status | Active/Draft/Deprecated |

### Requirement Detail Fields

| Field | Type | Required |
|---|---|---:|
| Requirement Code | Text | Yes |
| Title | Text | Yes |
| Description | Long text | Yes |
| Requirement Type | Enum | Yes |
| Priority | Enum | Yes |
| Compliance Mode | Enum | Yes |
| Supplier Response Required | Boolean | Yes |
| Evidence Required | Boolean | Yes |
| Evidence Type | Multi-select | Conditional |
| Evaluation Binding | Select | Conditional |
| Related Inventory Items | Multi-select | Optional |
| Related Milestones | Multi-select | Optional |

---

## 13.5 Implementation Schedule Screen

### Required UI Features

1. Phase table.
2. Milestone table by phase.
3. Deliverable list per milestone.
4. Acceptance certificate flag.
5. Payment milestone binding.
6. Gantt-style visual preview where available.

### Validation

1. Each phase must have at least one milestone.
2. Acceptance-required milestones must identify acceptance evidence.
3. Payment-linked milestones must match SCC payment milestones.
4. Phase sequence must be chronological.

---

## 13.6 System Inventory Screen

### Required UI Features

1. Separate tabs for Supply & Installation items and Recurrent Cost items.
2. Bulk import and export.
3. Link to requirements.
4. Link to price schedule lines.
5. Link to implementation phase.
6. Warnings for unpriced inventory items.

---

## 13.7 Price Schedule Setup Screen

### Required UI Features

1. Price schedule mode selector.
2. Supply and installation summary configuration.
3. Recurrent cost summary configuration.
4. VAT treatment configuration.
5. Currency configuration.
6. Evaluation basis configuration.
7. Preview of supplier price forms.

### Validation

1. Currency must match TDS.
2. Recurrent cost years must be defined where recurrent costs are evaluated.
3. VAT rules must be consistent with Form of Tender.
4. Price adjustment must be blocked if not allowed.

---

## 13.8 Evaluation and Qualification Screen

### Required UI Features

1. Mandatory requirement checklist builder.
2. Technical scoring matrix builder.
3. Pass mark setting.
4. Personnel requirements builder.
5. Specific experience criteria builder.
6. Financial evaluation basis selector.
7. Margin of preference toggle if allowed.
8. Generated evaluation schema preview.

### Validation

1. Technical scoring total must equal required total.
2. Pass mark must be within allowed range.
3. Mandatory criteria must identify supporting document.
4. Criteria must not conflict with STD rules.
5. Financial evaluation must align with price schedule.

---

## 13.9 SCC and Contract Parameters Screen

### Required UI Features

1. Performance security configuration.
2. Payment milestones.
3. Warranty/defect liability settings.
4. Intellectual property and software license settings.
5. Support and maintenance settings.
6. Dispute resolution settings.
7. Contract appendix generation preview.

### Validation

1. Performance security must comply with rule catalog.
2. Payment milestone total must be complete.
3. Warranty period must align with implementation schedule.
4. IP/software categories must be captured where custom materials exist.

---

## 13.10 Review and Approval Screen

### Required UI Features

1. Validation summary.
2. Section completion summary.
3. Review track checklist.
4. Reviewer comments.
5. Approval/return actions.
6. Audit timeline.
7. Preview links.

### Actions by State

| State | Available Actions |
|---|---|
| `IN_CONFIGURATION` | Validate, Preview, Submit for Review |
| `READY_FOR_REVIEW` | Accept Review, Return |
| `PROCUREMENT_REVIEW` | Return, Request Technical Review, Request Legal Review, Approve |
| `TECHNICAL_REVIEW` | Complete Technical Review, Return |
| `LEGAL_REVIEW` | Complete Legal Review, Return |
| `APPROVED_FOR_TENDER_CREATION` | Bind to Tender |
| `BOUND_TO_TENDER` | Generate Publication Bundle |
| `PUBLISHED` | View Bundle, Create Addendum Impact Assessment |

---

## 14. Validation Contract

## 14.1 Validation Severity

| Severity | Meaning | Publication Effect |
|---|---|---|
| `BLOCKER` | Must be fixed | Blocks review/publish |
| `WARNING` | Requires attention | Does not block unless rule says so |
| `INFO` | Informational | Does not block |

## 14.2 Validation Categories

| Category | Examples |
|---|---|
| Schema validation | Required fields, types, enums |
| Date sequencing | Clarification deadline, submission, opening |
| STD compliance | Locked text, permitted values, form activation |
| Cross-section consistency | TDS currency vs price schedule currency |
| Requirement consistency | Requirement linked to evaluation/inventory |
| Schedule consistency | Milestones linked to payment and acceptance |
| Price consistency | Recurrent years, VAT treatment, total formulas |
| Evaluation consistency | Score totals, pass mark, criteria support documents |
| Contract carry-forward | SCC terms, acceptance, securities, IP appendices |
| Render readiness | Missing render block values |
| Publication readiness | Bundle hash, source trace, approval status |

---

## 15. Generated Outputs

The wizard must be able to generate the following outputs through the STD Engine render service:

| Output | Consumer |
|---|---|
| Draft tender preview | Internal users/reviewers |
| Final tender document bundle | Tender publication |
| Supplier response schema | Supplier Portal |
| Supplier evidence checklist | Supplier Portal |
| Technical conformance matrix | Supplier Portal and Evaluation Module |
| Price schedule forms | Supplier Portal and Evaluation Module |
| Evaluation schema | Evaluation Module |
| Contract carry-forward package | Contract Management Module |
| Audit summary | Audit and compliance users |
| Addendum impact report | Tender Management and publication users |

---

## 16. Immutability Rules

1. Active STD master content must not be mutated by the wizard.
2. Approved configurations are locked except through authorized return or addendum workflows.
3. Bound configurations must not be edited except through controlled pre-publication reopening, if permitted.
4. Published bundles are immutable.
5. Post-publication changes must create addendum impact assessment.
6. Addendum outputs must not overwrite original publication artifacts.
7. Audit events must not be deleted or altered.
8. Hashes must be recalculated whenever generated outputs are created.

---

## 17. Data Exchange with Other Modules

## 17.1 Tender Management

### Outbound Payload: Tender Binding

```json
{
  "tender_id": "TDR-000001",
  "configuration_id": "ITCFG-000001",
  "std_template_version_id": "STDVER-KE-PPRA-IT-2022-04",
  "configuration_state": "BOUND_TO_TENDER",
  "validation_status": "PASS"
}
```

### Outbound Payload: Publication Bundle

```json
{
  "tender_id": "TDR-000001",
  "bundle_id": "BUNDLE-000001",
  "bundle_hash": "sha256:...",
  "published_artifacts": [
    {
      "artifact_type": "FULL_TENDER_DOCUMENT",
      "format": "PDF",
      "url": "/documents/tenders/BUNDLE-000001/full.pdf"
    }
  ]
}
```

---

## 17.2 Supplier Portal

### Outbound Payload: Supplier Response Schema

```json
{
  "tender_id": "TDR-000001",
  "schema_id": "SUPRESP-000001",
  "forms": ["form_of_tender", "confidential_business_questionnaire"],
  "requirements": ["REQ-000001", "REQ-000002"],
  "price_schedules": ["supply_installation_summary", "recurrent_cost_summary"],
  "evidence_requirements": ["tax_compliance_certificate", "technical_proposal"]
}
```

---

## 17.3 Evaluation Module

### Outbound Payload: Evaluation Schema

```json
{
  "tender_id": "TDR-000001",
  "evaluation_schema_id": "EVALSCH-000001",
  "stages": [
    "PRELIMINARY_RESPONSIVENESS",
    "TECHNICAL_EVALUATION",
    "FINANCIAL_EVALUATION"
  ],
  "technical_pass_mark": 75,
  "technical_total_points": 100,
  "financial_evaluation_basis": "LOWEST_EVALUATED_RESPONSIVE_TENDER"
}
```

---

## 17.4 Contract Management

### Outbound Payload: Contract Carry-Forward Package

```json
{
  "tender_id": "TDR-000001",
  "configuration_id": "ITCFG-000001",
  "contract_parameters": {
    "performance_security_percent": 10,
    "warranty_period_months": 12,
    "payment_milestones": [],
    "acceptance_milestones": [],
    "software_categories": [],
    "custom_materials": []
  }
}
```

---

## 18. Non-Functional Requirements

| Area | Requirement |
|---|---|
| Security | Role-based access control for every action |
| Auditability | All material changes, state transitions, renders, approvals, and publications audited |
| Traceability | Every field must trace to STD schema, user input, or generated artifact |
| Immutability | Published artifacts immutable and hashed |
| Performance | Wizard screens should load within acceptable operational thresholds for large requirement sets |
| Bulk handling | Requirement and inventory import must support validation-only mode |
| Reliability | Publication bundle generation must be transactional or resumable |
| Accessibility | UI should support keyboard navigation and readable validation feedback |
| Localization | Date/time/currency handling must support Kenya context and future localization |
| Extensibility | Wizard framework must support other STD families through schema-driven screens |

---

## 19. Logging and Audit Event Types

| Event Type | Trigger |
|---|---|
| `IT_WIZARD_CONFIGURATION_CREATED` | New configuration created |
| `IT_WIZARD_TDS_UPDATED` | TDS values changed |
| `IT_WIZARD_SCC_UPDATED` | SCC values changed |
| `IT_WIZARD_REQUIREMENT_CREATED` | Requirement added |
| `IT_WIZARD_REQUIREMENT_UPDATED` | Requirement changed |
| `IT_WIZARD_REQUIREMENT_DELETED` | Requirement soft-deleted |
| `IT_WIZARD_SCHEDULE_UPDATED` | Implementation schedule changed |
| `IT_WIZARD_INVENTORY_UPDATED` | System inventory changed |
| `IT_WIZARD_PRICE_SCHEDULE_UPDATED` | Price schedule configuration changed |
| `IT_WIZARD_EVALUATION_UPDATED` | Evaluation criteria changed |
| `IT_WIZARD_FORMS_UPDATED` | Form activation changed |
| `IT_WIZARD_VALIDATION_RUN` | Validation executed |
| `IT_WIZARD_PREVIEW_RENDERED` | Preview generated |
| `IT_WIZARD_SUBMITTED_FOR_REVIEW` | Submitted for review |
| `IT_WIZARD_RETURNED_FOR_CORRECTION` | Returned by reviewer |
| `IT_WIZARD_APPROVED` | Approved for tender creation |
| `IT_WIZARD_BOUND_TO_TENDER` | Bound to tender shell |
| `IT_WIZARD_PUBLICATION_BUNDLE_GENERATED` | Final bundle generated |
| `IT_WIZARD_ADDENDUM_IMPACT_ASSESSED` | Addendum impact assessed |
| `IT_WIZARD_ADDENDUM_GENERATED` | Addendum output generated |

---

## 20. Acceptance Criteria

The module is acceptable when:

1. A user can create an IT tender configuration only from an active compatible STD version.
2. The wizard exposes TDS, SCC, requirements, schedule, inventory, pricing, evaluation, forms, and evidence screens.
3. Locked STD content cannot be edited from the wizard.
4. TDS and SCC values can be saved and audited.
5. Functional and technical requirements can be entered, imported, categorized, validated, and rendered.
6. Implementation schedule phases and milestones can be linked to acceptance and payment events.
7. System inventory items can be linked to requirements and price schedules.
8. Price schedule configuration can generate supplier price forms.
9. Evaluation criteria can be configured within STD-permitted rules.
10. Validation detects blockers, warnings, and informational findings.
11. Draft previews can be generated with watermarks.
12. Configurations can be submitted, reviewed, returned, and approved through controlled workflow.
13. Approved configurations can be bound to tender shells.
14. Published bundles are generated, hashed, and locked.
15. Post-publication changes trigger addendum impact assessment.
16. Supplier Portal, Evaluation Module, and Contract Management receive structured generated outputs.
17. All material actions create audit events.

---

## 21. Smoke Contracts

## 21.1 Smoke Contract: Create Configuration

**Given** an active IT STD version exists  
**When** a Procurement Preparer creates a configuration from that version  
**Then** the system creates an `ITTenderConfiguration` in `DRAFT` state  
**And** initializes section statuses  
**And** records an audit event.

---

## 21.2 Smoke Contract: Locked STD Text Cannot Be Edited

**Given** a configuration exists  
**When** a user attempts to update locked ITT or GCC text through the wizard  
**Then** the system rejects the update with `403` or `409`  
**And** records a denied-action audit event.

---

## 21.3 Smoke Contract: TDS Validation

**Given** a configuration has TDS values  
**When** the clarification deadline is after the submission deadline  
**Then** validation returns a `BLOCKER`  
**And** review submission is blocked.

---

## 21.4 Smoke Contract: Technical Scoring Total

**Given** technical scoring is enabled  
**When** configured scoring criteria total less than or greater than 100 points  
**Then** validation returns a `BLOCKER`  
**And** publication is blocked.

---

## 21.5 Smoke Contract: Requirement-to-Evaluation Binding

**Given** mandatory technical requirements exist  
**When** no supplier response or conformance mode is configured  
**Then** validation returns a `BLOCKER` or `WARNING` according to STD rule severity.

---

## 21.6 Smoke Contract: Implementation Milestone Payment Binding

**Given** SCC payment milestones reference Phase 1 UAT  
**When** no implementation milestone exists for Phase 1 UAT  
**Then** validation returns a `BLOCKER`.

---

## 21.7 Smoke Contract: Publication Bundle Immutability

**Given** a configuration is bound to a tender  
**When** the publication bundle is generated  
**Then** artifacts are hashed and locked  
**And** subsequent edits are blocked unless routed through addendum assessment.

---

## 21.8 Smoke Contract: Addendum Impact

**Given** a tender has been published  
**When** a user proposes a change to a technical requirement  
**Then** the system creates an addendum impact assessment  
**And** identifies affected tender document, supplier response schema, and evaluation schema.

---

## 22. Implementation Notes

1. Keep the wizard schema-driven wherever possible.
2. Avoid hard-coding IT STD field definitions into UI components where the STD Engine Core can supply field metadata.
3. Hard-code only IT-domain UI affordances that are genuinely domain-specific, such as requirement composer, implementation schedule, system inventory, and price schedule interactions.
4. Treat NSSF ERP as a calibration fixture only, never as a master STD source.
5. Use strict audit and hash behavior from the start. Retrofitting audit defensibility later will be costly and risky.
6. Do not implement publication before validation and state-transition enforcement are complete.
7. Do not allow raw document upload to replace configured STD outputs.

---

## 23. Open Decisions

| Decision | Options | Recommended |
|---|---|---|
| Wizard framework | IT-only screens vs schema-driven generic wizard | Hybrid schema-driven with IT-specific components |
| Requirement import | CSV only vs CSV/XLSX | CSV first, XLSX later |
| Preview formats | HTML only vs HTML/PDF/DOCX | HTML first, PDF/DOCX at publication |
| Technical review | Always required vs conditionally required | Conditionally required by complexity/rules |
| Legal review | Always required vs conditionally required | Conditionally required, mandatory for post-publication addenda |
| Addendum publication | Full regenerated bundle vs affected-section bundle | Both, with affected-section map |
| Supplier response schema | Generated at publication vs at review | Preview at review, immutable version at publication |

---

## 24. Next Artifact

The next artifact should be:

**IT Tender Configuration Wizard — Cursor Implementation Pack**

That artifact should convert this API, UI, and service contract into concrete implementation instructions covering:

1. Model files.
2. Service files.
3. Endpoint handlers.
4. UI routes and components.
5. Permission checks.
6. State transition guards.
7. Validation execution.
8. Rendering integration.
9. Test files.
10. Seed loading.
11. Build order.

