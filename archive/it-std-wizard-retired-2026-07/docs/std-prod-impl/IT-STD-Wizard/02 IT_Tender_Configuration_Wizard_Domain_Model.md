# IT Tender Configuration Wizard — Strict Domain Model

## Document Control

| Field | Value |
|---|---|
| Document Title | IT Tender Configuration Wizard — Strict Domain Model |
| Project | KenTender e-Procurement System |
| Module Family | STD Engine / Tender Management Integration |
| Primary STD Target | Standard Tender Document for Procurement of Information Technology |
| Master STD Package | `KE-PPRA-IT-2022-04` |
| Calibration Fixture | NSSF SPS ERP System Tender, Ref. `NSSFSPS/ICT/ERP/001/2025-2026` |
| Upstream Document | `IT_Tender_Configuration_Wizard_PRD.md` |
| Status | Draft for design review |
| Activation Status | Not implementation-authorized until governance, permissions, seed data, smoke contracts, and Cursor implementation pack are approved |
| Intended Audience | Product owner, procurement domain experts, legal reviewers, architects, backend engineers, frontend engineers, QA, audit/compliance team |

---

## 1. Purpose

This document converts the IT Tender Configuration Wizard PRD into strict implementation entities, fields, enums, relationships, constraints, indexes, audit requirements, validation bindings, lifecycle bindings, and immutability rules.

The wizard must remain STD-family agnostic. The first full implementation is for the Standard Tender Document for Procurement of Information Technology, but the same runtime must later support other STDs through package-provided schemas, rules, render blocks, and workflow bindings.

The domain model in this document covers the tender-specific configuration layer. It does not replace the STD Engine Core domain model. It depends on the STD Engine Core for master template families, template versions, source documents, sections, clauses, parameters, rules, forms, render blocks, package validation, source anchors, and master-template lifecycle governance.

---

## 2. Domain Boundary

### 2.1 In Scope

This domain model covers:

1. Creation of a tender-specific STD instance from an active STD package.
2. Wizard step generation and progress tracking.
3. Tender identity and procurement method configuration.
4. TDS values and SCC values.
5. PE-authored IT scope, background, and objectives.
6. IT requirements composer.
7. Implementation schedule, milestones, locations, dependencies, and acceptance events.
8. System inventory tables.
9. Price schedule setup.
10. Evaluation and qualification configuration.
11. Tendering forms and evidence requirements.
12. Supplier submission schema preview.
13. Evaluation workspace schema preview.
14. Contract carry-forward preview.
15. Validation runs and findings.
16. Review workflow state and decision trail.
17. Rendered preview and published bundle tracking.
18. Post-publication addendum impact analysis.
19. NSSF ERP calibration fixture mapping as non-production evidence.

### 2.2 Out of Scope

This model does not define:

1. Master STD package authoring tables. These are owned by the STD Engine Core.
2. Legal activation of STD packages.
3. Supplier portal submission storage beyond generated schema handoff.
4. Evaluation committee scoring records beyond generated evaluation workspace handoff.
5. Contract execution management beyond contract carry-forward handoff.
6. General Tender Management lifecycle outside STD configuration binding.
7. Direct editing of locked ITT or GCC legal text.
8. Vendor-specific hard-coded ERP behavior.

---

## 3. Core Architectural Principle

The wizard is a controlled configuration surface, not a document editor.

All wizard screens, fields, validations, forms, requirement categories, price structures, evaluation matrices, contract carry-forward fields, and render blocks must be derived from:

1. The active STD package version.
2. The STD Engine Core parameter, rule, form, section, and render definitions.
3. Tender-specific configuration values entered through the wizard.

A tender user must not be able to alter master STD content, locked legal clauses, STD package rules, or legal render order.

---

## 4. Dependency on STD Engine Core Entities

The following entities are external dependencies owned by the STD Engine Core module. This wizard stores references to them but does not own their master data.

| External Entity | Reference Field Pattern | Wizard Use |
|---|---|---|
| `STDTemplateFamily` | `std_family_id` | Identifies the STD family, e.g. IT, Works, Goods |
| `STDTemplateVersion` | `std_version_id` | Locks the wizard instance to an exact active STD version |
| `STDSourceDocument` | `source_document_id` | Displays source evidence and hash |
| `STDSection` | `std_section_id` | Maps wizard steps to legal/render sections |
| `STDClause` | `std_clause_id` | Supports locked clause references and source anchors |
| `STDParameter` | `std_parameter_id` | Defines configurable fields |
| `STDRule` | `std_rule_id` | Defines validation/calculation/activation rules |
| `STDFormSchema` | `std_form_schema_id` | Defines tendering and contract forms |
| `STDFormField` | `std_form_field_id` | Defines bidder form fields |
| `STDEvidenceRequirement` | `std_evidence_requirement_id` | Defines required supplier evidence |
| `STDRenderBlock` | `std_render_block_id` | Defines document generation blocks |
| `STDSmokeContract` | `std_smoke_contract_id` | Defines package-level and wizard-level tests |
| `STDWorkflowBinding` | `std_workflow_binding_id` | Defines review tracks and gates |

Hard rule: a wizard instance must remain permanently bound to the exact `std_version_id` selected at creation. It must not float to a later STD version.

---

## 5. High-Level Entity Map

| Entity Group | Main Entities |
|---|---|
| Instance and lifecycle | `TenderSTDInstance`, `WizardStepInstance`, `WizardProgressSnapshot`, `WizardStateTransitionEvent` |
| Tender identity and participation | `TenderIdentityProfile`, `ProcurementParticipationProfile`, `TenderDateProfile`, `TenderSubmissionProfile`, `SecurityInstrumentProfile` |
| Parameter values | `TenderSTDParameterValue`, `TenderSTDParameterValueHistory`, `TenderSTDSectionValueStatus` |
| Requirements | `ITRequirementSet`, `ITRequirementGroup`, `ITRequirementItem`, `ITRequirementEvidenceBinding`, `ITRequirementReviewFinding` |
| Implementation schedule | `ITImplementationPlan`, `ITImplementationPhase`, `ITImplementationMilestone`, `ITAcceptanceEvent`, `ITMilestonePaymentBinding` |
| System inventory | `ITSystemInventoryTable`, `ITSystemInventoryItem`, `ITInventoryCostBinding` |
| Price schedules | `ITPriceScheduleProfile`, `ITPriceScheduleTable`, `ITPriceScheduleLineTemplate`, `ITRecurrentCostPeriod` |
| Evaluation | `ITEvaluationProfile`, `ITEvaluationStage`, `ITEvaluationCriterion`, `ITEvaluationSubcriterion`, `ITQualificationRequirement`, `ITEvaluationFormulaBinding` |
| Forms and evidence | `TenderFormActivation`, `TenderEvidenceRequirement`, `TenderSupplierSubmissionSchemaSnapshot` |
| SCC and contract carry-forward | `TenderSCCProfile`, `ContractCarryForwardProfile`, `ContractCarryForwardItem`, `ContractAppendixBinding` |
| Validation and preview | `WizardValidationRun`, `WizardValidationFinding`, `WizardPreviewBundle`, `WizardGeneratedArtifact`, `WizardHashEvidence` |
| Review and approval | `WizardReviewTrack`, `WizardReviewAssignment`, `WizardReviewDecision`, `WizardApprovalGateStatus` |
| Addendum | `WizardAddendumRequest`, `WizardAddendumImpactAnalysis`, `WizardAddendumAffectedObject`, `WizardAddendumBundle` |
| Calibration | `TenderCalibrationFixture`, `TenderCalibrationMapping`, `TenderCalibrationDeviation` |

---

## 6. Shared Field Conventions

### 6.1 Identifier Fields

| Field | Type | Required | Rule |
|---|---|---:|---|
| `id` | UUID / String | Yes | Primary key |
| `tenant_id` | UUID / String | Yes | Owning organization or platform tenant |
| `procuring_entity_id` | UUID / String | Conditional | Required for tender-owned records |
| `tender_id` | UUID / String | Conditional | Required once the wizard is bound to a Tender Management tender |
| `tender_std_instance_id` | UUID / String | Conditional | Required for all child wizard records |
| `external_ref` | String | No | Human-readable external reference, if any |

### 6.2 Audit Fields

Every mutable entity must include:

| Field | Type | Required |
|---|---|---:|
| `created_at` | Timestamp | Yes |
| `created_by` | User ID | Yes |
| `updated_at` | Timestamp | Yes |
| `updated_by` | User ID | Yes |
| `version_no` | Integer | Yes |
| `row_hash` | String | Yes for locked/approved states |
| `is_deleted` | Boolean | Yes, default false |
| `deleted_at` | Timestamp | Conditional |
| `deleted_by` | User ID | Conditional |
| `deletion_reason` | Text | Conditional |

Deletion must be logical only. Published, approved, or audit-relevant records must never be physically deleted through business workflows.

### 6.3 Source Trace Fields

Where a record is generated from an STD package object, include:

| Field | Type | Required | Description |
|---|---|---:|---|
| `std_family_id` | FK | Yes | STD family |
| `std_version_id` | FK | Yes | Bound STD version |
| `std_section_id` | FK | Conditional | Related STD section |
| `std_parameter_id` | FK | Conditional | Related STD parameter |
| `std_rule_id` | FK | Conditional | Related STD rule |
| `std_form_schema_id` | FK | Conditional | Related STD form |
| `std_render_block_id` | FK | Conditional | Related render block |
| `source_anchor_id` | FK/String | Conditional | Source anchor from STD Core |
| `source_hash` | String | Conditional | Source object hash where applicable |

### 6.4 Lifecycle Lock Fields

Entities that can become immutable must include:

| Field | Type | Required | Description |
|---|---|---:|---|
| `lock_status` | Enum | Yes | `UNLOCKED`, `REVIEW_LOCKED`, `APPROVED_LOCKED`, `PUBLISHED_LOCKED`, `ARCHIVED_LOCKED` |
| `locked_at` | Timestamp | Conditional | Set when record becomes locked |
| `locked_by` | User ID/System | Conditional | Lock actor |
| `lock_reason` | Text | Conditional | Reason for lock |
| `published_bundle_id` | FK | Conditional | Bundle that made the record immutable |

---

## 7. Enumerations

### 7.1 Wizard State Enum

| Value | Meaning | Editable |
|---|---|---:|
| `NOT_STARTED` | Tender exists but no STD instance has been created | No |
| `INSTANCE_CREATED` | Active STD package selected and instance created | Yes |
| `IN_CONFIGURATION` | User is configuring values | Yes |
| `VALIDATION_FAILED` | Blocking validations exist | Yes |
| `READY_FOR_INTERNAL_REVIEW` | Complete enough for review | Limited |
| `PROCUREMENT_REVIEW` | Procurement review in progress | No |
| `TECHNICAL_REVIEW` | Technical review in progress | No |
| `LEGAL_REVIEW` | Legal review in progress | No |
| `FINANCE_REVIEW` | Finance review in progress | No |
| `RETURNED_FOR_CORRECTION` | Returned with required corrections | Scoped Yes |
| `APPROVED_FOR_TENDER_CREATION` | Approved for tender binding | No |
| `BOUND_TO_TENDER` | Bound to Tender Management record | No except controlled pre-publication amendment |
| `PRE_PUBLICATION_FINAL_CHECK` | Final validation/render checks | No |
| `PUBLISHED` | Tender artifact bundle published | No |
| `ADDENDUM_REQUIRED` | Post-publication change requested | No direct edit |
| `ADDENDUM_IN_CONFIGURATION` | Addendum is being configured | Addendum scope only |
| `ADDENDUM_PUBLISHED` | Addendum published | No |
| `CANCELLED` | Instance cancelled before publication | No |
| `ARCHIVED` | Retained for record | No |

### 7.2 Step Status Enum

| Value | Meaning |
|---|---|
| `NOT_AVAILABLE` | Step disabled by package/rule |
| `NOT_STARTED` | Step available but no work started |
| `IN_PROGRESS` | Step has draft content |
| `COMPLETE` | Required fields completed |
| `HAS_WARNINGS` | Step has non-blocking findings |
| `HAS_BLOCKERS` | Step has blocking findings |
| `RETURNED` | Step returned by reviewer |
| `APPROVED` | Step approved in review |
| `LOCKED` | Step locked due to review/publication |

### 7.3 Mutability Enum

| Value | Meaning |
|---|---|
| `LOCKED` | No tender-level editing permitted |
| `PARAMETERIZED` | Tender values entered through defined fields |
| `CONTROLLED_CONFIGURABLE` | User may select/compose within controlled schemas |
| `PE_AUTHORED_REVIEWED` | PE may author content subject to review |
| `GENERATED` | System-generated from approved data |
| `REFERENCE_ONLY` | Informational, not supplier obligation unless explicitly mapped |

### 7.4 Requirement Category Enum

| Value |
|---|
| `FUNCTIONAL` |
| `ARCHITECTURAL` |
| `PERFORMANCE` |
| `SECURITY` |
| `INTEGRATION` |
| `DATA_MIGRATION` |
| `REPORTING_BI` |
| `SERVICE_SPECIFICATION` |
| `TECHNOLOGY_SPECIFICATION` |
| `TRAINING` |
| `DOCUMENTATION` |
| `TESTING_ACCEPTANCE` |
| `WARRANTY_SUPPORT` |
| `REGULATORY_COMPLIANCE` |
| `ACCESSIBILITY_USABILITY` |
| `HOSTING_INFRASTRUCTURE` |
| `BUSINESS_CONTINUITY_DR` |
| `CHANGE_MANAGEMENT` |
| `PROJECT_MANAGEMENT` |
| `KNOWLEDGE_TRANSFER` |
| `OTHER` |

### 7.5 Requirement Priority Enum

| Value | Meaning |
|---|---|
| `MANDATORY` | Failure may make tender non-responsive or reduce technical score according to evaluation setup |
| `DESIRABLE` | Preferred feature, may be scored |
| `OPTIONAL` | Optional information or future capability |
| `INFORMATIONAL` | Not a supplier obligation unless carried forward elsewhere |

### 7.6 Compliance Response Type Enum

| Value | Meaning |
|---|---|
| `YES_NO` | Supplier marks compliance yes/no |
| `YES_NO_NARRATIVE` | Supplier marks compliance and explains |
| `NARRATIVE` | Supplier provides text explanation |
| `NUMERIC` | Supplier provides numeric value |
| `DOCUMENT_EVIDENCE` | Supplier uploads evidence |
| `DEMONSTRATION` | Supplier must demonstrate capability |
| `TEST_CASE` | Requirement linked to acceptance test |
| `REFERENCE_PAGE` | Supplier references technical proposal page |
| `NOT_REQUIRED` | No direct supplier response required |

### 7.7 Evaluation Treatment Enum

| Value | Meaning |
|---|---|
| `PASS_FAIL` | Mandatory compliance check |
| `SCORED` | Weighted technical scoring criterion |
| `PRICE_EVALUATED` | Included in financial evaluation |
| `CONTRACT_ONLY` | Carries forward to contract but not separately evaluated |
| `INFORMATIONAL` | Included for context only |
| `NOT_EVALUATED` | No evaluation treatment |

### 7.8 Security Instrument Type Enum

| Value |
|---|
| `TENDER_SECURITY` |
| `TENDER_SECURING_DECLARATION` |
| `PROFESSIONAL_INDEMNITY` |
| `BID_BOND` |
| `NOT_REQUIRED` |
| `OTHER_PERMITTED_BY_STD` |

### 7.9 Price Schedule Type Enum

| Value | Meaning |
|---|---|
| `GRAND_SUMMARY` | Overall tender price summary |
| `SUPPLY_INSTALLATION_SUMMARY` | Supply and installation cost summary |
| `SUPPLY_INSTALLATION_SUBTABLE` | Detailed supply/install line items |
| `RECURRENT_COST_SUMMARY` | Recurrent cost summary |
| `RECURRENT_COST_SUBTABLE` | Detailed recurrent cost line items |
| `COUNTRY_OF_ORIGIN` | Country of origin code table |
| `CUSTOM_ALLOWED_EXTENSION` | Controlled extension requiring review |

### 7.10 Review Track Enum

| Value |
|---|
| `PROCUREMENT` |
| `TECHNICAL` |
| `LEGAL` |
| `FINANCE` |
| `APPROVING_AUTHORITY` |
| `PUBLICATION` |
| `AUDIT` |

### 7.11 Review Decision Enum

| Value | Meaning |
|---|---|
| `APPROVE` | Review passed |
| `RETURN_FOR_CORRECTION` | Changes required |
| `REJECT` | Configuration cannot proceed in current form |
| `ESCALATE` | Send to higher authority |
| `COMMENT_ONLY` | Comment without state change |

### 7.12 Validation Severity Enum

| Value | Meaning |
|---|---|
| `BLOCKER` | Must be resolved before progression/publication |
| `WARNING` | May proceed with justification or review approval |
| `INFO` | Informational only |
| `SYSTEM_ERROR` | Validation could not execute properly |

### 7.13 Addendum Impact Type Enum

| Value |
|---|
| `DATES_ONLY` |
| `TDS_CHANGE` |
| `SCC_CHANGE` |
| `REQUIREMENT_CHANGE` |
| `PRICE_SCHEDULE_CHANGE` |
| `EVALUATION_CRITERIA_CHANGE` |
| `FORM_OR_EVIDENCE_CHANGE` |
| `CONTRACT_CARRY_FORWARD_CHANGE` |
| `RENDER_ONLY_CHANGE` |
| `CANCELLATION_OR_REISSUE_REQUIRED` |

---

## 8. Entity Definitions

## 8.1 `TenderSTDInstance`

### Purpose

Represents one tender-specific configuration instance created from one active STD package version.

### Fields

| Field | Type | Required | Constraints / Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tenant_id` | UUID | Yes | Indexed |
| `procuring_entity_id` | UUID | Yes | Indexed |
| `tender_id` | UUID | No | Required from `BOUND_TO_TENDER` onward |
| `std_family_id` | FK | Yes | References STD Core |
| `std_version_id` | FK | Yes | Immutable after creation |
| `std_package_code` | String | Yes | Example: `KE-PPRA-IT-2022-04` |
| `source_document_id` | FK | Yes | Source document used by package |
| `package_hash` | String | Yes | Copied from active STD package at instance creation |
| `source_document_hash` | String | Yes | Copied for evidence |
| `instance_code` | String | Yes | Unique per procuring entity |
| `instance_title` | String | Yes | Usually tender name |
| `procurement_category` | String/Enum | Yes | Example: `INFORMATION_TECHNOLOGY` |
| `wizard_state` | Enum | Yes | `Wizard State Enum` |
| `created_from_active_version` | Boolean | Yes | Must be true |
| `std_version_active_at_creation` | Boolean | Yes | Must be true |
| `std_version_superseded_after_creation` | Boolean | Yes | Default false; informational only |
| `current_validation_status` | Enum | Yes | `NOT_RUN`, `PASSED`, `PASSED_WITH_WARNINGS`, `FAILED`, `ERROR` |
| `current_render_status` | Enum | Yes | `NOT_RUN`, `DRAFT_RENDERED`, `FINAL_RENDERED`, `PUBLISHED`, `ERROR` |
| `published_bundle_id` | FK | No | Required when `PUBLISHED` |
| `published_at` | Timestamp | No | Required when `PUBLISHED` |
| `published_by` | User ID | No | Required when `PUBLISHED` |
| `cancelled_at` | Timestamp | No | Required when `CANCELLED` |
| `cancelled_by` | User ID | No | Required when `CANCELLED` |
| `cancellation_reason` | Text | No | Required when cancelled |
| `lock_status` | Enum | Yes | See lifecycle lock fields |
| audit fields | Shared | Yes | See shared audit fields |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `UQ_tender_std_instance_code` | Unique | `(tenant_id, procuring_entity_id, instance_code)` |
| `CHK_active_version_on_create` | Business | Instance can be created only from active STD version |
| `IMMUTABLE_std_version_id` | Business | `std_version_id` cannot change after creation |
| `CHK_published_bundle_required` | Business | `published_bundle_id` required when `wizard_state = PUBLISHED` |
| `CHK_no_edit_after_published` | Business | Child editable records cannot be modified after publication except via addendum records |

### Indexes

| Index | Fields |
|---|---|
| `IDX_instance_tender` | `tenant_id`, `tender_id` |
| `IDX_instance_state` | `tenant_id`, `wizard_state` |
| `IDX_instance_std_version` | `std_version_id` |
| `IDX_instance_pe` | `tenant_id`, `procuring_entity_id`, `created_at` |

---

## 8.2 `WizardStepInstance`

### Purpose

Represents the generated instance of a wizard step for a specific tender STD instance.

### Fields

| Field | Type | Required | Constraints / Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `step_code` | String | Yes | Stable code, e.g. `TENDER_IDENTITY` |
| `step_order` | Integer | Yes | Display order |
| `step_title` | String | Yes | Display title |
| `step_description` | Text | No | UI helper text |
| `std_section_id` | FK | No | Related section where applicable |
| `std_render_block_id` | FK | No | Related render block where applicable |
| `mutability_type` | Enum | Yes | From package |
| `is_required_for_publication` | Boolean | Yes | Default from package |
| `is_available` | Boolean | Yes | Controlled by activation rules |
| `availability_reason` | Text | No | If disabled |
| `status` | Enum | Yes | Step Status Enum |
| `completion_percent` | Decimal | Yes | 0–100 |
| `last_validation_run_id` | FK | No | Latest validation affecting step |
| `last_review_status` | Enum | No | `NOT_REVIEWED`, `RETURNED`, `APPROVED` |
| `assigned_owner_user_id` | User ID | No | Optional owner |
| `assigned_owner_role` | String | No | Optional role owner |
| `lock_status` | Enum | Yes | Lock state |
| audit fields | Shared | Yes |  |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `UQ_step_per_instance` | Unique | `(tender_std_instance_id, step_code)` |
| `CHK_step_order_positive` | Check | `step_order > 0` |
| `CHK_required_step_available` | Business | Required publication step cannot be marked `NOT_AVAILABLE` unless package rule says not applicable |

---

## 8.3 `WizardProgressSnapshot`

### Purpose

Stores summarized wizard progress for dashboard and audit-friendly status reporting.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `snapshot_at` | Timestamp | Yes | Capture time |
| `wizard_state` | Enum | Yes | State at snapshot |
| `total_steps` | Integer | Yes |  |
| `available_steps` | Integer | Yes |  |
| `completed_steps` | Integer | Yes |  |
| `steps_with_blockers` | Integer | Yes |  |
| `steps_with_warnings` | Integer | Yes |  |
| `required_fields_total` | Integer | Yes |  |
| `required_fields_completed` | Integer | Yes |  |
| `blocking_findings_count` | Integer | Yes |  |
| `warning_findings_count` | Integer | Yes |  |
| `latest_validation_run_id` | FK | No |  |
| `latest_preview_bundle_id` | FK | No |  |
| `snapshot_payload_json` | JSON | Yes | Full progress summary |
| audit fields | Shared | Yes |  |

### Constraints

Progress snapshots are append-only after creation.

---

## 8.4 `WizardStateTransitionEvent`

### Purpose

Append-only record of every state change for a tender STD instance.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `from_state` | Enum | Yes | Wizard State Enum |
| `to_state` | Enum | Yes | Wizard State Enum |
| `transition_code` | String | Yes | Example: `SUBMIT_FOR_REVIEW` |
| `actor_user_id` | User ID | Yes | User or system account |
| `actor_role` | String | Yes | Role at time of transition |
| `transition_reason` | Text | Conditional | Required for return, reject, cancel, addendum |
| `guard_result_json` | JSON | Yes | Guards evaluated |
| `validation_run_id` | FK | No | Relevant validation run |
| `review_decision_id` | FK | No | If review action triggered transition |
| `hash_before` | String | No | Optional instance hash before transition |
| `hash_after` | String | No | Optional instance hash after transition |
| `event_at` | Timestamp | Yes |  |
| audit fields | Shared | Yes | Append-only |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `APPEND_ONLY_transition` | Business | Records must not be updated or deleted |
| `CHK_valid_transition` | Business | Transition must exist in approved state-transition matrix |
| `CHK_reason_required` | Business | Reason required for `RETURNED_FOR_CORRECTION`, `REJECT`, `CANCELLED`, `ADDENDUM_REQUIRED` |

---

## 8.5 `TenderIdentityProfile`

### Purpose

Stores tender identity data used in the cover page, invitation, TDS, rendered tender document, and Tender Management binding.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | One-to-one |
| `procuring_entity_name` | String | Yes | Rendered value |
| `procuring_entity_logo_file_id` | File ID | No | Controlled upload/reference |
| `procuring_entity_address` | Text | Yes |  |
| `procuring_entity_email` | String | Yes | Valid email |
| `procuring_entity_website` | String | No |  |
| `tender_name` | String | Yes |  |
| `tender_number` | String | Yes | Unique per PE |
| `contract_name` | String | Yes |  |
| `contract_description` | Text | Yes |  |
| `procurement_plan_reference` | String | Conditional | Required where plan integration is enabled |
| `budget_reference` | String | Conditional | Required where budget integration is enabled |
| `estimated_cost_amount` | Decimal | Conditional | Visibility controlled by role/policy |
| `estimated_cost_currency` | String | Conditional | ISO currency |
| `number_of_lots` | Integer | Yes | Default 1 |
| `lotting_strategy` | Enum | Yes | `SINGLE_LOT`, `MULTIPLE_LOTS`, `NOT_APPLICABLE` |
| `language_code` | String | Yes | Default `en` |
| `responsible_officer_user_id` | User ID | Yes |  |
| `review_owner_user_id` | User ID | No |  |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `UQ_tender_number_per_pe` | Unique | `(tenant_id, procuring_entity_id, tender_number)` |
| `CHK_number_of_lots` | Check | `number_of_lots >= 1` |
| `CHK_estimate_positive` | Check | `estimated_cost_amount > 0` when provided |

---

## 8.6 `ProcurementParticipationProfile`

### Purpose

Stores procurement method, eligibility, reservation, margin of preference, alternative tender, JV, and foreign-tenderer configuration.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | One-to-one |
| `procurement_method` | Enum | Yes | `OPEN_NATIONAL`, `OPEN_INTERNATIONAL`, `RESTRICTED`, `OTHER_PERMITTED` |
| `prequalification_used` | Boolean | Yes |  |
| `prequalification_reference` | String | Conditional | Required if prequalification used |
| `reservation_applies` | Boolean | Yes |  |
| `reserved_group_code` | String | Conditional | Required if reservation applies |
| `margin_of_preference_applies` | Boolean | Yes |  |
| `margin_of_preference_profile_id` | FK/String | Conditional | Required if applies |
| `alternative_tenders_allowed` | Boolean | Yes |  |
| `multiple_lots_allowed` | Boolean | Yes |  |
| `max_jv_members` | Integer | Conditional | Required where JV allowed |
| `foreign_tenderer_allowed` | Boolean | Yes |  |
| `foreign_local_sourcing_rule_applies` | Boolean | Yes | Typically 40% local sourcing for foreign tenderers if package rule enabled |
| `country_restriction_policy_json` | JSON | No | Eligible/ineligible country rules |
| `requires_vendor_neutrality_review` | Boolean | Yes | Set by rule engine if vendor-specific terms present |
| `review_justification` | Text | Conditional | Required if warnings accepted |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `CHK_jv_members` | Check | `max_jv_members` must be within package-defined max/min |
| `CHK_reservation_group_required` | Business | Reserved group required if reservation applies |
| `CHK_margin_allowed` | Business | Margin of preference can be true only if package/procurement method permits it |

---

## 8.7 `TenderDateProfile`

### Purpose

Stores date and event configuration for clarifications, meetings, submission, opening, validity, standstill, and related deadlines.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | One-to-one |
| `issue_date` | Date | Yes |  |
| `clarification_request_deadline` | Timestamp | Yes |  |
| `clarification_response_deadline` | Timestamp | Conditional |  |
| `pre_tender_meeting_required` | Boolean | Yes |  |
| `pre_tender_meeting_at` | Timestamp | Conditional | Required if meeting required |
| `pre_tender_meeting_location` | Text | Conditional | Required if in-person meeting |
| `pre_tender_meeting_virtual_link` | String | Conditional | Required if virtual meeting |
| `site_visit_required` | Boolean | Yes | Generic STD support |
| `site_visit_at` | Timestamp | Conditional | Required if site visit required |
| `site_visit_location` | Text | Conditional | Required if site visit required |
| `submission_deadline` | Timestamp | Yes |  |
| `opening_at` | Timestamp | Yes | Must be same or after submission deadline according to package rules |
| `tender_validity_days` | Integer | Yes |  |
| `standstill_period_days` | Integer | Conditional | Where applicable |
| `timezone` | String | Yes | IANA timezone |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `CHK_deadline_order` | Business | Clarification deadline < submission deadline; opening >= submission deadline |
| `CHK_validity_positive` | Check | `tender_validity_days > 0` |
| `CHK_meeting_fields` | Business | Meeting date/location/link required when enabled |

---

## 8.8 `TenderSubmissionProfile`

### Purpose

Stores physical/electronic submission rules, addresses, copies, serialization, marking, and opening location.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | One-to-one |
| `physical_submission_allowed` | Boolean | Yes |  |
| `electronic_submission_allowed` | Boolean | Yes |  |
| `submission_address` | Text | Conditional | Required if physical allowed |
| `tender_box_location` | Text | Conditional | Required if physical allowed |
| `opening_venue` | Text | Yes |  |
| `number_of_originals` | Integer | Yes | Usually 1 |
| `number_of_copies` | Integer | Yes |  |
| `serialization_required` | Boolean | Yes |  |
| `envelope_marking_instructions` | Text | Conditional | Generated default plus custom permitted values |
| `late_tender_handling` | Enum | Yes | `REJECT_RETURN_UNOPENED`, `REJECT_KEEP_RECORD`, `EPROCUREMENT_AUTO_REJECT` |
| `clarification_contact_name` | String | Yes |  |
| `clarification_contact_title` | String | No |  |
| `clarification_contact_email` | String | Yes | Valid email |
| `document_download_registration_required` | Boolean | Yes |  |
| `download_registration_instruction` | Text | Conditional | Required if registration required |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

At least one of `physical_submission_allowed` or `electronic_submission_allowed` must be true unless the tender is cancelled.

---

## 8.9 `SecurityInstrumentProfile`

### Purpose

Stores tender security, tender-securing declaration, professional indemnity, or other permitted instrument configuration.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | One-to-one |
| `instrument_type` | Enum | Yes | Security Instrument Type Enum |
| `required` | Boolean | Yes |  |
| `amount` | Decimal | Conditional | Required when monetary instrument required |
| `currency` | String | Conditional | ISO currency |
| `amount_basis` | Enum | No | `ABSOLUTE`, `PERCENT_ESTIMATE`, `OTHER` |
| `validity_period_days` | Integer | Conditional |  |
| `valid_beyond_tender_validity_days` | Integer | No |  |
| `permitted_issuer_types_json` | JSON | Conditional | Bank, insurance, etc. |
| `original_required` | Boolean | Yes |  |
| `failure_is_nonresponsive` | Boolean | Yes |  |
| `forfeiture_conditions_text` | Text | Conditional | Required if applicable |
| `std_permitted` | Boolean | Yes | Derived by rules |
| `non_standard_instrument_warning` | Boolean | Yes | Set if calibration-like substitution occurs |
| `justification` | Text | Conditional | Required if non-standard warning accepted |
| `reviewed_by_legal` | Boolean | Yes |  |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

If `instrument_type = PROFESSIONAL_INDEMNITY` and the active STD package does not explicitly permit it as tender security substitute, a warning or blocker must be raised according to configured governance policy.

---

## 8.10 `TenderSTDParameterValue`

### Purpose

Stores tender-specific values for STD Core parameters.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `std_parameter_id` | FK | Yes | STD Core parameter |
| `std_section_id` | FK | Conditional | Section context |
| `parameter_code` | String | Yes | Copied from package for stable reporting |
| `parameter_label` | String | Yes | Copied display label |
| `value_type` | Enum | Yes | `STRING`, `TEXT`, `NUMBER`, `BOOLEAN`, `DATE`, `DATETIME`, `CURRENCY`, `SELECT`, `MULTI_SELECT`, `JSON`, `FILE_REF` |
| `value_string` | String | No | One of value fields used |
| `value_text` | Text | No |  |
| `value_number` | Decimal | No |  |
| `value_boolean` | Boolean | No |  |
| `value_date` | Date | No |  |
| `value_datetime` | Timestamp | No |  |
| `value_currency_amount` | Decimal | No |  |
| `value_currency_code` | String | No |  |
| `value_json` | JSON | No |  |
| `file_ref_id` | File ID | No |  |
| `is_required` | Boolean | Yes | Copied from package/effective rule |
| `is_completed` | Boolean | Yes | Derived |
| `validation_status` | Enum | Yes | `NOT_VALIDATED`, `VALID`, `WARNING`, `BLOCKED`, `ERROR` |
| `last_validation_run_id` | FK | No |  |
| `source_anchor_id` | FK/String | No | Parameter source anchor |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `UQ_parameter_value` | Unique | `(tender_std_instance_id, std_parameter_id)` unless parameter explicitly repeatable |
| `CHK_single_value_field` | Business | Only the value field matching `value_type` should be populated |
| `CHK_required_complete` | Business | Required parameters must be completed before review submission |

---

## 8.11 `TenderSTDParameterValueHistory`

### Purpose

Append-only history of parameter changes.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `parameter_value_id` | FK | Yes | Parent |
| `tender_std_instance_id` | FK | Yes | Denormalized for query |
| `changed_at` | Timestamp | Yes |  |
| `changed_by` | User ID | Yes |  |
| `old_value_json` | JSON | No |  |
| `new_value_json` | JSON | No |  |
| `change_reason` | Text | Conditional | Required during review correction/addendum |
| `change_source` | Enum | Yes | `USER_EDIT`, `SYSTEM_CALCULATION`, `IMPORT`, `REVIEW_CORRECTION`, `ADDENDUM` |
| `state_at_change` | Enum | Yes | Wizard state |
| `hash_before` | String | No |  |
| `hash_after` | String | No |  |

### Constraints

History records are append-only.

---

## 8.12 `TenderSTDSectionValueStatus`

### Purpose

Summarizes completion, validation, review, and render status by STD section.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `std_section_id` | FK | Yes | STD section |
| `section_code` | String | Yes | Copied code |
| `section_title` | String | Yes | Copied title |
| `mutability_type` | Enum | Yes |  |
| `completion_status` | Enum | Yes | `NOT_STARTED`, `PARTIAL`, `COMPLETE`, `NOT_APPLICABLE` |
| `validation_status` | Enum | Yes | `NOT_RUN`, `PASSED`, `WARNINGS`, `FAILED`, `ERROR` |
| `review_status` | Enum | Yes | `NOT_REQUIRED`, `NOT_STARTED`, `RETURNED`, `APPROVED` |
| `render_status` | Enum | Yes | `NOT_RENDERED`, `DRAFT_RENDERED`, `FINAL_RENDERED`, `PUBLISHED` |
| `blocking_count` | Integer | Yes |  |
| `warning_count` | Integer | Yes |  |
| `last_validation_run_id` | FK | No |  |
| `last_preview_bundle_id` | FK | No |  |
| audit fields | Shared | Yes |  |

---

## 8.13 `ITRequirementSet`

### Purpose

Container for IT requirements attached to a tender STD instance.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | One-to-one |
| `std_section_id` | FK | Yes | Requirements section |
| `requirement_set_code` | String | Yes | Example: `IT_REQUIREMENTS` |
| `title` | String | Yes |  |
| `description` | Text | No |  |
| `business_background_text` | Text | No | Background only unless mapped |
| `objectives_text` | Text | No |  |
| `expected_outcomes_text` | Text | No |  |
| `specific_tasks_text` | Text | No |  |
| `hosting_preference` | String | No |  |
| `deployment_model` | Enum | No | `CLOUD`, `ON_PREMISE`, `HYBRID`, `UNSPECIFIED` |
| `vendor_specific_terms_detected` | Boolean | Yes | Derived |
| `vendor_specific_review_required` | Boolean | Yes | Derived |
| `technical_review_status` | Enum | Yes | `NOT_STARTED`, `RETURNED`, `APPROVED` |
| `legal_review_status` | Enum | Yes | Where applicable |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

Background and informational material must not be treated as supplier obligation unless linked to one or more `ITRequirementItem` records with `contract_carry_forward = true` or `evaluation_treatment != INFORMATIONAL`.

---

## 8.14 `ITRequirementGroup`

### Purpose

Groups requirement items into categories/modules/subsections.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `requirement_set_id` | FK | Yes | Parent |
| `parent_group_id` | FK | No | Supports hierarchy |
| `group_code` | String | Yes | Stable code, e.g. `PENSION_ADMIN` |
| `group_title` | String | Yes |  |
| `group_description` | Text | No |  |
| `category` | Enum | Yes | Requirement Category Enum |
| `display_order` | Integer | Yes |  |
| `is_required` | Boolean | Yes |  |
| `review_status` | Enum | Yes | `DRAFT`, `RETURNED`, `APPROVED` |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `UQ_requirement_group_code` | Unique | `(requirement_set_id, group_code)` |
| `CHK_group_order_positive` | Check | `display_order > 0` |

---

## 8.15 `ITRequirementItem`

### Purpose

Represents one structured supplier obligation or requirement row.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `requirement_set_id` | FK | Yes | Parent set |
| `requirement_group_id` | FK | Yes | Parent group |
| `requirement_code` | String | Yes | Stable code, e.g. `GEN-001`, `SEC-004` |
| `requirement_title` | String | No | Optional short title |
| `requirement_text` | Text | Yes | Supplier obligation text |
| `category` | Enum | Yes | Requirement Category Enum |
| `subcategory` | String | No |  |
| `priority` | Enum | Yes | Requirement Priority Enum |
| `compliance_response_type` | Enum | Yes | Compliance Response Type Enum |
| `evaluation_treatment` | Enum | Yes | Evaluation Treatment Enum |
| `evaluation_stage_code` | String | No | Links to evaluation stage |
| `evaluation_criterion_id` | FK | No | Links if scored or pass/fail |
| `evidence_required` | Boolean | Yes |  |
| `response_required` | Boolean | Yes |  |
| `contract_carry_forward` | Boolean | Yes | Becomes contract obligation |
| `acceptance_test_required` | Boolean | Yes |  |
| `acceptance_event_id` | FK | No | If linked |
| `supplier_page_reference_required` | Boolean | Yes | For compliance matrix |
| `vendor_specific_flag` | Boolean | Yes | Derived/manual |
| `vendor_specific_term` | String | No | Detected term |
| `vendor_specific_justification` | Text | Conditional | Required when flag accepted |
| `regulatory_basis` | Text | No | If requirement is statutory/regulatory |
| `source_type` | Enum | Yes | `PE_AUTHORED`, `STD_DEFAULT`, `IMPORT`, `CALIBRATION_FIXTURE`, `OTHER` |
| `source_reference` | String/Text | No | Upload/row/source note |
| `review_status` | Enum | Yes | `DRAFT`, `RETURNED`, `APPROVED` |
| `revision_no` | Integer | Yes | Starts at 1 |
| `superseded_by_requirement_id` | FK | No | For addendum/versioning |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `UQ_requirement_code` | Unique | `(requirement_set_id, requirement_code)` |
| `CHK_requirement_text_not_empty` | Check | Requirement text must not be blank |
| `CHK_vendor_justification` | Business | Vendor-specific flag requires justification and technical/procurement review |
| `CHK_acceptance_link` | Business | If `acceptance_test_required = true`, link to acceptance event or acceptance test definition required before publication |
| `CHK_contract_carry_forward` | Business | Requirements with `CONTRACT_ONLY` treatment must have `contract_carry_forward = true` |

### Indexes

| Index | Fields |
|---|---|
| `IDX_req_group` | `requirement_group_id`, `display_order` if implemented |
| `IDX_req_category` | `requirement_set_id`, `category` |
| `IDX_req_vendor_flag` | `requirement_set_id`, `vendor_specific_flag` |
| `IDX_req_review` | `requirement_set_id`, `review_status` |

---

## 8.16 `ITRequirementEvidenceBinding`

### Purpose

Links requirement items to supplier evidence obligations.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `requirement_item_id` | FK | Yes | Requirement |
| `std_evidence_requirement_id` | FK | No | STD Core evidence definition |
| `evidence_code` | String | Yes | Stable code |
| `evidence_title` | String | Yes |  |
| `evidence_description` | Text | No |  |
| `mandatory_for_supplier` | Boolean | Yes |  |
| `allowed_file_types_json` | JSON | No |  |
| `max_file_size_mb` | Integer | No |  |
| `requires_original` | Boolean | Yes | For physical evidence |
| `requires_certification` | Boolean | Yes |  |
| `evaluation_stage_code` | String | No | Stage where checked |
| audit fields | Shared | Yes |  |

### Constraints

One requirement may have multiple evidence bindings. Evidence records must be generated into the supplier submission schema.

---

## 8.17 `ITRequirementReviewFinding`

### Purpose

Captures technical/procurement/legal review findings against requirement items.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `requirement_item_id` | FK | Yes | Parent |
| `review_track` | Enum | Yes | Review Track Enum |
| `finding_type` | Enum | Yes | `VENDOR_SPECIFIC`, `AMBIGUOUS`, `UNTESTABLE`, `NON_MEASURABLE`, `CONTRACT_RISK`, `EVALUATION_RISK`, `DUPLICATE`, `OTHER` |
| `severity` | Enum | Yes | Validation Severity Enum |
| `finding_text` | Text | Yes |  |
| `recommended_action` | Text | No |  |
| `resolution_status` | Enum | Yes | `OPEN`, `ACCEPTED_WITH_JUSTIFICATION`, `CORRECTED`, `DISMISSED`, `ESCALATED` |
| `resolution_text` | Text | Conditional | Required when resolved |
| `resolved_by` | User ID | No |  |
| `resolved_at` | Timestamp | No |  |
| audit fields | Shared | Yes |  |

---

## 8.18 `ITImplementationPlan`

### Purpose

Stores overall implementation approach for the information system.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | One-to-one |
| `plan_code` | String | Yes |  |
| `plan_title` | String | Yes |  |
| `implementation_model` | Enum | Yes | `SINGLE_PHASE`, `MULTI_PHASE`, `ROLLING_WAVE`, `OTHER` |
| `total_expected_duration_days` | Integer | No |  |
| `implementation_location` | Text | Conditional |  |
| `requires_project_plan_from_supplier` | Boolean | Yes |  |
| `requires_phase_integration_architecture` | Boolean | Yes | Especially for phased ERP-like tenders |
| `requires_uat` | Boolean | Yes |  |
| `requires_operational_acceptance` | Boolean | Yes |  |
| `warranty_trigger_basis` | Enum | Yes | `FINAL_ACCEPTANCE`, `PHASE_ACCEPTANCE`, `GO_LIVE`, `OTHER` |
| `review_status` | Enum | Yes | `DRAFT`, `RETURNED`, `APPROVED` |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

---

## 8.19 `ITImplementationPhase`

### Purpose

Represents a phase of implementation, such as Phase 1 and Phase 2 in an ERP tender.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `implementation_plan_id` | FK | Yes | Parent |
| `phase_code` | String | Yes | Example: `PHASE_1` |
| `phase_title` | String | Yes |  |
| `phase_description` | Text | No |  |
| `display_order` | Integer | Yes |  |
| `planned_start_offset_days` | Integer | No | Relative to commencement |
| `planned_duration_days` | Integer | No |  |
| `financial_year` | String | No | Optional |
| `modules_or_scope_json` | JSON | No | List of modules/scope items |
| `requires_acceptance_certificate` | Boolean | Yes |  |
| `warranty_months` | Integer | No |  |
| `payment_linked` | Boolean | Yes |  |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `UQ_phase_code` | Unique | `(implementation_plan_id, phase_code)` |
| `CHK_phase_order` | Check | `display_order > 0` |
| `CHK_warranty_positive` | Check | `warranty_months >= 0` when provided |

---

## 8.20 `ITImplementationMilestone`

### Purpose

Represents a milestone, deliverable, or stage-gate within an implementation phase.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `implementation_phase_id` | FK | Yes | Parent |
| `milestone_code` | String | Yes | Stable code |
| `milestone_title` | String | Yes |  |
| `milestone_description` | Text | No |  |
| `display_order` | Integer | Yes |  |
| `deliverables_json` | JSON | No |  |
| `planned_duration_days` | Integer | No |  |
| `dependency_milestone_ids_json` | JSON | No | References prior milestones |
| `acceptance_criteria_text` | Text | Conditional | Required if acceptance/payment linked |
| `requires_uat_signoff` | Boolean | Yes |  |
| `requires_operational_acceptance` | Boolean | Yes |  |
| `payment_linked` | Boolean | Yes |  |
| `payment_binding_id` | FK | No |  |
| `contract_carry_forward` | Boolean | Yes |  |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

---

## 8.21 `ITAcceptanceEvent`

### Purpose

Defines acceptance events used by requirements, milestones, certificates, warranty triggers, and payment milestones.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `implementation_plan_id` | FK | Yes | Parent |
| `implementation_phase_id` | FK | No | Optional phase |
| `acceptance_code` | String | Yes | Stable code |
| `acceptance_title` | String | Yes |  |
| `acceptance_type` | Enum | Yes | `UAT`, `GO_LIVE`, `OPERATIONAL_ACCEPTANCE`, `POST_IMPLEMENTATION_SIGNOFF`, `WARRANTY_EXPIRY`, `OTHER` |
| `acceptance_description` | Text | No |  |
| `acceptance_criteria_json` | JSON | Yes | Structured criteria |
| `certificate_required` | Boolean | Yes |  |
| `certificate_form_schema_id` | FK | No | Acceptance certificate form |
| `triggers_payment` | Boolean | Yes |  |
| `triggers_warranty_start` | Boolean | Yes |  |
| `contract_carry_forward` | Boolean | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

Acceptance events used as warranty or payment triggers must carry forward to contract schema.

---

## 8.22 `ITMilestonePaymentBinding`

### Purpose

Links implementation milestones or acceptance events to SCC payment terms.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `implementation_milestone_id` | FK | No | One of milestone or acceptance event required |
| `acceptance_event_id` | FK | No |  |
| `scc_parameter_id` | FK | No | Related SCC payment parameter |
| `payment_sequence` | Integer | Yes |  |
| `payment_description` | Text | Yes |  |
| `payment_percentage` | Decimal | Conditional | If percentage based |
| `payment_amount` | Decimal | Conditional | If fixed amount |
| `currency` | String | Conditional |  |
| `payment_condition_text` | Text | Yes |  |
| `retention_applies` | Boolean | Yes |  |
| `retention_percentage` | Decimal | No |  |
| `contract_carry_forward` | Boolean | Yes | Must be true |
| audit fields | Shared | Yes |  |

### Constraints

Payment percentages must sum to 100% where the payment model is percentage-based and retention is represented as part of the contract price.

---

## 8.23 `ITSystemInventoryTable`

> **Ownership Matrix override (`99` / ITW-OWN-DOC-02):** Commercial quantity/unit/evaluated-price fields on inventory items are owned by the Price Schedule binding model (ITW-08). ITW-07 persists technical-disclosure items only; `quantity` / `unit_of_measure` on this entity are not edited on the System Inventory screen. Requirement score marks remain on Evaluation criteria, not `ITRequirementItem` UI.

### Purpose

Stores system inventory table metadata for supply/install and recurrent cost items.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `table_code` | String | Yes | Example: `SUPPLY_INSTALL_ITEMS`, `RECURRENT_ITEMS` |
| `table_type` | Enum | Yes | `SUPPLY_INSTALLATION`, `RECURRENT`, `OTHER_PERMITTED` |
| `table_title` | String | Yes |  |
| `description` | Text | No |  |
| `is_required` | Boolean | Yes |  |
| `linked_price_schedule_table_id` | FK | Conditional | Required if price schedule linked |
| `review_status` | Enum | Yes | `DRAFT`, `RETURNED`, `APPROVED` |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

A required inventory table must have at least one item before publication unless explicitly marked not applicable by a package rule.

---

## 8.24 `ITSystemInventoryItem`

### Purpose

Represents a supply/install or recurrent item that bidders must price/respond to.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `inventory_table_id` | FK | Yes | Parent |
| `item_code` | String | Yes | Stable item code |
| `item_description` | Text | Yes |  |
| `item_category` | String | No | Hardware, software, license, service, support, training, etc. |
| `unit_of_measure` | String | Conditional |  |
| `quantity` | Decimal | Conditional | Required for quantified items |
| `recurrent_period_code` | String | Conditional | Required for recurrent items |
| `supplier_to_complete_quantity` | Boolean | Yes | Usually false if PE-defined |
| `supplier_to_complete_description` | Boolean | Yes | Controlled by package/rule |
| `country_of_origin_required` | Boolean | Yes |  |
| `linked_requirement_item_id` | FK | No | Requirement source |
| `linked_milestone_id` | FK | No | Implementation linkage |
| `linked_price_schedule_line_template_id` | FK | No | Pricing linkage |
| `contract_carry_forward` | Boolean | Yes |  |
| `display_order` | Integer | Yes |  |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `UQ_inventory_item_code` | Unique | `(inventory_table_id, item_code)` |
| `CHK_quantity_positive` | Check | `quantity > 0` when provided |
| `CHK_supplier_editable_flags` | Business | Supplier-editable fields must be permitted by price/inventory schema |

---

## 8.25 `ITInventoryCostBinding`

### Purpose

Links inventory items to price schedule tables and cost categories.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `inventory_item_id` | FK | Yes | Parent item |
| `price_schedule_table_id` | FK | Yes | Price table |
| `price_schedule_line_template_id` | FK | No | Specific line template |
| `cost_category` | Enum | Yes | `SUPPLY`, `INSTALLATION`, `LICENSE`, `SUBSCRIPTION`, `MAINTENANCE`, `SUPPORT`, `TRAINING`, `OTHER` |
| `is_recurrent` | Boolean | Yes |  |
| `recurrent_cost_period_id` | FK | No | Required if recurrent |
| `evaluation_included` | Boolean | Yes |  |
| `contract_carry_forward` | Boolean | Yes |  |
| audit fields | Shared | Yes |  |

---

## 8.26 `ITPriceScheduleProfile`

### Purpose

Controls price schedule structure for the tender.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | One-to-one |
| `currency` | String | Yes | ISO currency |
| `vat_treatment` | Enum | Yes | `INCLUSIVE`, `EXCLUSIVE`, `SEPARATE_LINE`, `NOT_APPLICABLE` |
| `price_adjustment_allowed` | Boolean | Yes | Usually false for calibration tender; package-controlled |
| `requires_country_of_origin` | Boolean | Yes |  |
| `has_recurrent_costs` | Boolean | Yes |  |
| `recurrent_cost_evaluation_method` | Enum | Conditional | `TOTAL_N_YEARS`, `PRESENT_VALUE`, `YEAR_1_ONLY`, `NOT_EVALUATED`, `OTHER` |
| `recurrent_cost_years` | Integer | Conditional | Required if recurrent costs evaluated by years |
| `supplier_may_add_lines` | Boolean | Yes | Controlled by schema |
| `review_status` | Enum | Yes | `DRAFT`, `RETURNED`, `APPROVED` |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

Recurrent costs must have an explicit evaluation method if they are required or may affect evaluated price.

---

## 8.27 `ITPriceScheduleTable`

### Purpose

Represents a price schedule table generated for supplier completion.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `price_schedule_profile_id` | FK | Yes | Parent |
| `table_code` | String | Yes | Stable code |
| `table_type` | Enum | Yes | Price Schedule Type Enum |
| `table_title` | String | Yes |  |
| `display_order` | Integer | Yes |  |
| `is_required` | Boolean | Yes |  |
| `supplier_editable` | Boolean | Yes | Whether supplier fills values |
| `included_in_evaluated_price` | Boolean | Yes |  |
| `calculation_formula_json` | JSON | No | For totals/subtotals |
| `linked_inventory_table_id` | FK | No |  |
| `render_block_id` | FK | No |  |
| audit fields | Shared | Yes |  |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `UQ_price_table_code` | Unique | `(price_schedule_profile_id, table_code)` |
| `CHK_table_order` | Check | `display_order > 0` |

---

## 8.28 `ITPriceScheduleLineTemplate`

### Purpose

Defines a supplier pricing line generated from inventory, requirements, or PE-defined cost structures.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `price_schedule_table_id` | FK | Yes | Parent |
| `line_code` | String | Yes | Stable code |
| `line_description` | Text | Yes |  |
| `display_order` | Integer | Yes |  |
| `unit_of_measure` | String | No |  |
| `quantity` | Decimal | No |  |
| `quantity_editable_by_supplier` | Boolean | Yes |  |
| `unit_price_required` | Boolean | Yes |  |
| `total_price_formula_json` | JSON | No | Usually quantity × unit price |
| `country_of_origin_required` | Boolean | Yes |  |
| `linked_inventory_item_id` | FK | No |  |
| `linked_requirement_item_id` | FK | No |  |
| `included_in_grand_total` | Boolean | Yes |  |
| `included_in_evaluation` | Boolean | Yes |  |
| audit fields | Shared | Yes |  |

---

## 8.29 `ITRecurrentCostPeriod`

### Purpose

Defines recurrent cost periods used in price schedules and evaluation.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `price_schedule_profile_id` | FK | Yes | Parent |
| `period_code` | String | Yes | Example: `YEAR_1`, `YEAR_2`, `WARRANTY`, `POST_WARRANTY_YEAR_1` |
| `period_title` | String | Yes |  |
| `period_order` | Integer | Yes |  |
| `duration_months` | Integer | Yes |  |
| `starts_after_event_id` | FK | No | Acceptance/warranty event |
| `included_in_evaluation` | Boolean | Yes |  |
| `discount_factor` | Decimal | No | If present value method used |
| audit fields | Shared | Yes |  |

---

## 8.30 `ITEvaluationProfile`

### Purpose

Configures the tender-specific evaluation model within STD-permitted limits.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | One-to-one |
| `evaluation_model` | Enum | Yes | `LOWEST_EVALUATED_RESPONSIVE`, `TECHNICAL_PASS_FINANCIAL_LOWEST`, `QUALITY_COST_ALLOWED_BY_STD`, `OTHER_PERMITTED` |
| `has_preliminary_stage` | Boolean | Yes |  |
| `has_technical_pass_fail_stage` | Boolean | Yes |  |
| `has_technical_scored_stage` | Boolean | Yes |  |
| `technical_total_points` | Decimal | Conditional | Required if scored |
| `technical_pass_mark` | Decimal | Conditional | Required if scored |
| `has_financial_stage` | Boolean | Yes |  |
| `has_postqualification_stage` | Boolean | Yes |  |
| `margin_of_preference_applies` | Boolean | Yes | Must align participation profile |
| `abnormally_low_high_check_required` | Boolean | Yes |  |
| `review_status` | Enum | Yes | `DRAFT`, `RETURNED`, `APPROVED` |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

If `has_technical_scored_stage = true`, the sum of active scored criteria must equal `technical_total_points`, and `technical_pass_mark` must be less than or equal to total points.

---

## 8.31 `ITEvaluationStage`

### Purpose

Represents one stage in the tender evaluation workflow.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `evaluation_profile_id` | FK | Yes | Parent |
| `stage_code` | String | Yes | `PRELIMINARY`, `TECHNICAL_PASS_FAIL`, `TECHNICAL_SCORED`, `FINANCIAL`, `POSTQUALIFICATION` |
| `stage_title` | String | Yes |  |
| `stage_order` | Integer | Yes |  |
| `stage_type` | Enum | Yes | `PASS_FAIL`, `SCORED`, `FINANCIAL`, `QUALIFICATION`, `SYSTEM_CHECK` |
| `is_required` | Boolean | Yes |  |
| `minimum_pass_required` | Boolean | Yes |  |
| `minimum_score` | Decimal | No |  |
| `supplier_visibility` | Enum | Yes | `PUBLISHED`, `INTERNAL_ONLY`, `SUMMARY_ONLY` |
| `render_block_id` | FK | No |  |
| audit fields | Shared | Yes |  |

---

## 8.32 `ITEvaluationCriterion`

### Purpose

Represents a mandatory, scored, financial, or post-qualification criterion.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `evaluation_stage_id` | FK | Yes | Parent |
| `criterion_code` | String | Yes | Stable code |
| `criterion_title` | String | Yes |  |
| `criterion_description` | Text | No |  |
| `criterion_type` | Enum | Yes | `MANDATORY`, `SCORED`, `FINANCIAL`, `QUALIFICATION`, `PRICE_FORMULA`, `PREFERENCE` |
| `display_order` | Integer | Yes |  |
| `maximum_points` | Decimal | No | Required for scored |
| `minimum_points` | Decimal | No | Optional |
| `pass_fail_requirement` | Boolean | Yes |  |
| `supporting_documentation_text` | Text | No |  |
| `linked_requirement_group_id` | FK | No |  |
| `linked_requirement_item_id` | FK | No |  |
| `linked_form_schema_id` | FK | No |  |
| `linked_evidence_requirement_id` | FK | No |  |
| `supplier_visible` | Boolean | Yes | Usually true for published criteria |
| `std_permitted` | Boolean | Yes | Derived from package |
| `customization_justification` | Text | Conditional | Required for PE-added/modified criteria where allowed |
| `review_status` | Enum | Yes | `DRAFT`, `RETURNED`, `APPROVED` |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `UQ_eval_criterion_code` | Unique | `(evaluation_stage_id, criterion_code)` |
| `CHK_points_for_scored` | Business | Scored criteria require `maximum_points > 0` |
| `CHK_no_unpermitted_criteria` | Business | Criteria outside STD-permitted scope require blocker unless package allows controlled addition |

---

## 8.33 `ITEvaluationSubcriterion`

### Purpose

Defines subcriteria for scored technical evaluation.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `evaluation_criterion_id` | FK | Yes | Parent |
| `subcriterion_code` | String | Yes |  |
| `subcriterion_title` | String | Yes |  |
| `subcriterion_description` | Text | No |  |
| `display_order` | Integer | Yes |  |
| `maximum_points` | Decimal | Yes |  |
| `scoring_guidance` | Text | No |  |
| `linked_requirement_item_id` | FK | No |  |
| `supplier_visible` | Boolean | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

Subcriterion points must sum to parent criterion points where subcriteria are used.

---

## 8.34 `ITQualificationRequirement`

### Purpose

Stores qualification criteria such as experience, turnover, personnel, local presence, certifications, or project references.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `evaluation_profile_id` | FK | Yes | Parent |
| `evaluation_stage_id` | FK | Yes | Usually preliminary/postqualification/technical |
| `qualification_code` | String | Yes | Stable code |
| `qualification_title` | String | Yes |  |
| `qualification_description` | Text | Yes |  |
| `requirement_type` | Enum | Yes | `EXPERIENCE`, `TURNOVER`, `PERSONNEL`, `CERTIFICATION`, `LOCAL_PRESENCE`, `LEGAL_STATUS`, `TAX_COMPLIANCE`, `PROJECT_REFERENCE`, `OTHER` |
| `mandatory` | Boolean | Yes |  |
| `minimum_value_number` | Decimal | No | For turnover/years/projects |
| `minimum_value_unit` | String | No | `YEARS`, `PROJECTS`, `KES`, etc. |
| `lookback_period_years` | Integer | No |  |
| `supporting_documentation_text` | Text | Yes |  |
| `vendor_specific_flag` | Boolean | Yes | e.g., named product partner certification |
| `vendor_specific_justification` | Text | Conditional | Required if flagged |
| `linked_form_schema_id` | FK | No |  |
| `linked_evidence_requirement_id` | FK | No |  |
| `review_status` | Enum | Yes | `DRAFT`, `RETURNED`, `APPROVED` |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

Vendor-specific qualifications require review justification and may require approval by procurement and technical reviewers.

---

## 8.35 `ITEvaluationFormulaBinding`

### Purpose

Stores formulas and bindings for evaluated price, recurrent cost inclusion, preference, and threshold calculations.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `evaluation_profile_id` | FK | Yes | Parent |
| `formula_code` | String | Yes | Stable code |
| `formula_title` | String | Yes |  |
| `formula_type` | Enum | Yes | `EVALUATED_PRICE`, `TECHNICAL_TOTAL`, `PASS_MARK`, `PREFERENCE`, `ABNORMALLY_LOW_HIGH`, `OTHER` |
| `formula_json` | JSON | Yes | Machine-readable formula |
| `human_readable_formula` | Text | Yes | Published/internal explanation |
| `published_to_suppliers` | Boolean | Yes |  |
| `std_rule_id` | FK | No | Related STD rule |
| `requires_review` | Boolean | Yes |  |
| audit fields | Shared | Yes |  |

---

## 8.36 `TenderFormActivation`

### Purpose

Stores which STD forms are activated for the tender and whether suppliers must complete them.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `std_form_schema_id` | FK | Yes | STD Core form |
| `form_code` | String | Yes | Copied from package |
| `form_title` | String | Yes |  |
| `form_stage` | Enum | Yes | `TENDER_SUBMISSION`, `EVALUATION`, `AWARD`, `CONTRACT`, `ADDENDUM` |
| `active` | Boolean | Yes | Controlled by rules |
| `mandatory_for_supplier` | Boolean | Yes |  |
| `mandatory_for_pe` | Boolean | Yes |  |
| `activation_reason` | Text | No |  |
| `deactivation_reason` | Text | Conditional | Required if package-default form disabled where allowed |
| `supplier_visible` | Boolean | Yes |  |
| `render_block_id` | FK | No |  |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

| Constraint | Type | Rule |
|---|---|---|
| `UQ_form_activation` | Unique | `(tender_std_instance_id, std_form_schema_id)` |
| `CHK_mandatory_active` | Business | Mandatory package forms cannot be deactivated unless package rule allows omission |

---

## 8.37 `TenderEvidenceRequirement`

### Purpose

Stores tender-specific evidence requirements generated from STD evidence definitions, forms, qualifications, and requirement items.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `std_evidence_requirement_id` | FK | No | STD Core evidence definition |
| `evidence_code` | String | Yes | Stable code |
| `evidence_title` | String | Yes |  |
| `evidence_description` | Text | No |  |
| `required_from_supplier` | Boolean | Yes |  |
| `required_stage` | Enum | Yes | `PRELIMINARY`, `TECHNICAL`, `FINANCIAL`, `POSTQUALIFICATION`, `CONTRACT` |
| `linked_form_activation_id` | FK | No |  |
| `linked_requirement_item_id` | FK | No |  |
| `linked_qualification_requirement_id` | FK | No |  |
| `allowed_file_types_json` | JSON | No |  |
| `original_required` | Boolean | Yes |  |
| `certified_copy_required` | Boolean | Yes |  |
| `expiry_date_required` | Boolean | Yes | e.g., certificates |
| `supplier_visible` | Boolean | Yes |  |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

---

## 8.38 `TenderSupplierSubmissionSchemaSnapshot`

### Purpose

Stores generated supplier submission schema snapshot for the configured tender.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `snapshot_code` | String | Yes |  |
| `snapshot_version_no` | Integer | Yes |  |
| `generated_at` | Timestamp | Yes |  |
| `generated_by` | User ID/System | Yes |  |
| `generation_basis_hash` | String | Yes | Hash of configuration inputs |
| `schema_json` | JSON | Yes | Full supplier submission schema |
| `forms_included_json` | JSON | Yes |  |
| `requirements_included_json` | JSON | Yes |  |
| `price_tables_included_json` | JSON | Yes |  |
| `evidence_included_json` | JSON | Yes |  |
| `is_final_for_publication` | Boolean | Yes |  |
| `published_bundle_id` | FK | No | Required if final/published |
| audit fields | Shared | Yes | Append-only once final |

### Constraints

Final supplier submission schema snapshots are immutable.

---

## 8.39 `TenderSCCProfile`

### Purpose

Stores SCC configuration profile and contract-specific parameters.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | One-to-one |
| `contract_governing_law` | String | No | Usually inherited/default |
| `contract_language` | String | No |  |
| `performance_security_required` | Boolean | Yes |  |
| `performance_security_percentage` | Decimal | Conditional |  |
| `advance_payment_allowed` | Boolean | Yes |  |
| `advance_payment_security_required` | Boolean | Conditional |  |
| `warranty_period_months` | Integer | Conditional |  |
| `defect_liability_period_months` | Integer | No | If applicable |
| `support_and_maintenance_required` | Boolean | Yes |  |
| `sla_required` | Boolean | Yes |  |
| `ip_transfer_required` | Boolean | Yes |  |
| `software_license_model` | Enum | No | `PERPETUAL`, `SUBSCRIPTION`, `MIXED`, `OTHER` |
| `source_code_escrow_required` | Boolean | No | Calibration support; review required |
| `confidentiality_terms_required` | Boolean | Yes |  |
| `data_protection_terms_required` | Boolean | Yes |  |
| `dispute_resolution_profile` | String/JSON | No |  |
| `payment_terms_summary` | Text | No | Derived from payment bindings |
| `review_status` | Enum | Yes | `DRAFT`, `RETURNED`, `APPROVED` |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

### Constraints

SCC fields that affect payments, IP, liability, warranty, acceptance, dispute resolution, or security must pass legal and finance review before approval.

---

## 8.40 `ContractCarryForwardProfile`

### Purpose

Stores the tender-to-contract handoff model.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | One-to-one |
| `profile_code` | String | Yes |  |
| `generated_at` | Timestamp | No |  |
| `generated_by` | User ID/System | No |  |
| `generation_status` | Enum | Yes | `NOT_GENERATED`, `DRAFT`, `VALID`, `FAILED` |
| `carry_forward_hash` | String | No | Required when generated |
| `contract_schema_json` | JSON | No | Full contract handoff schema |
| `review_status` | Enum | Yes | `NOT_STARTED`, `RETURNED`, `APPROVED` |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

---

## 8.41 `ContractCarryForwardItem`

### Purpose

Represents one tender value, requirement, price table, milestone, SCC value, or form output that must carry forward to award/contract.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `contract_carry_forward_profile_id` | FK | Yes | Parent |
| `source_object_type` | Enum | Yes | `PARAMETER`, `REQUIREMENT`, `PRICE_LINE`, `INVENTORY_ITEM`, `MILESTONE`, `ACCEPTANCE_EVENT`, `SCC_PARAMETER`, `FORM`, `EVIDENCE`, `EVALUATION_RESULT`, `OTHER` |
| `source_object_id` | UUID/String | Yes | Source object |
| `carry_forward_code` | String | Yes | Stable code |
| `carry_forward_title` | String | Yes |  |
| `carry_forward_value_json` | JSON | Yes | Value to pass forward |
| `target_contract_section` | String | Yes | Contract section/appendix |
| `target_contract_form_schema_id` | FK | No | Contract form if applicable |
| `target_appendix_code` | String | No |  |
| `mandatory_for_contract` | Boolean | Yes |  |
| `supplier_confirmed_at_award` | Boolean | Yes | Whether winning supplier must confirm/finalize |
| `review_status` | Enum | Yes | `DRAFT`, `RETURNED`, `APPROVED` |
| audit fields | Shared | Yes |  |

---

## 8.42 `ContractAppendixBinding`

### Purpose

Defines generated contract appendices and their data sources.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `contract_carry_forward_profile_id` | FK | Yes | Parent |
| `appendix_code` | String | Yes | Examples: `SUPPLIER_REPRESENTATIVE`, `APPROVED_SUBCONTRACTORS`, `SOFTWARE_CATEGORIES`, `CUSTOM_MATERIALS`, `REVISED_PRICE_SCHEDULES`, `FINALIZATION_MINUTES` |
| `appendix_title` | String | Yes |  |
| `std_form_schema_id` | FK | No | Related contract form |
| `source_objects_json` | JSON | Yes | Source object references |
| `required_for_contract` | Boolean | Yes |  |
| `generated_by_system` | Boolean | Yes |  |
| `requires_award_stage_completion` | Boolean | Yes |  |
| `render_block_id` | FK | No |  |
| audit fields | Shared | Yes |  |

---

## 8.43 `WizardValidationRun`

### Purpose

Stores execution of validation rules against the wizard instance or subset of records.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `run_code` | String | Yes |  |
| `run_scope` | Enum | Yes | `FULL_INSTANCE`, `STEP`, `SECTION`, `PARAMETER`, `REQUIREMENTS`, `PRICE`, `EVALUATION`, `CONTRACT`, `PRE_PUBLICATION`, `ADDENDUM` |
| `scope_object_type` | String | No |  |
| `scope_object_id` | UUID/String | No |  |
| `trigger_type` | Enum | Yes | `MANUAL`, `AUTO_ON_SAVE`, `SUBMIT_FOR_REVIEW`, `PRE_PUBLICATION`, `ADDENDUM`, `IMPORT` |
| `started_at` | Timestamp | Yes |  |
| `finished_at` | Timestamp | No |  |
| `status` | Enum | Yes | `RUNNING`, `PASSED`, `PASSED_WITH_WARNINGS`, `FAILED`, `ERROR` |
| `rules_executed_count` | Integer | Yes |  |
| `blocker_count` | Integer | Yes |  |
| `warning_count` | Integer | Yes |  |
| `info_count` | Integer | Yes |  |
| `error_count` | Integer | Yes |  |
| `input_hash` | String | Yes | Hash of data validated |
| `result_hash` | String | No | Hash of findings/result |
| `executed_by` | User ID/System | Yes |  |
| audit fields | Shared | Yes |  |

---

## 8.44 `WizardValidationFinding`

### Purpose

Stores one validation finding from a validation run.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `validation_run_id` | FK | Yes | Parent |
| `tender_std_instance_id` | FK | Yes | Denormalized |
| `std_rule_id` | FK | No | Related STD rule |
| `rule_code` | String | Yes |  |
| `severity` | Enum | Yes | Validation Severity Enum |
| `finding_code` | String | Yes | Stable code |
| `finding_title` | String | Yes |  |
| `finding_message` | Text | Yes |  |
| `affected_object_type` | String | Yes |  |
| `affected_object_id` | UUID/String | Yes |  |
| `affected_step_code` | String | No |  |
| `affected_section_id` | FK | No |  |
| `recommended_action` | Text | No |  |
| `can_be_overridden` | Boolean | Yes |  |
| `override_requires_role` | String | No |  |
| `override_reason` | Text | Conditional | Required if overridden |
| `overridden_by` | User ID | No |  |
| `overridden_at` | Timestamp | No |  |
| `resolution_status` | Enum | Yes | `OPEN`, `RESOLVED`, `OVERRIDDEN`, `DISMISSED`, `SUPERSEDED` |
| audit fields | Shared | Yes |  |

### Constraints

Blockers cannot be overridden unless the governing STD rule explicitly permits override and defines the approving role.

---

## 8.45 `WizardPreviewBundle`

### Purpose

Stores a generated tender document preview or final generated bundle before/at publication.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `bundle_code` | String | Yes |  |
| `bundle_type` | Enum | Yes | `DRAFT_PREVIEW`, `REVIEW_PREVIEW`, `FINAL_PRE_PUBLICATION`, `PUBLISHED`, `ADDENDUM` |
| `generated_at` | Timestamp | Yes |  |
| `generated_by` | User ID/System | Yes |  |
| `input_configuration_hash` | String | Yes | Hash of all source config |
| `render_profile_hash` | String | Yes | Hash of render block definitions |
| `bundle_hash` | String | Yes | Hash of generated bundle manifest/files |
| `render_status` | Enum | Yes | `SUCCESS`, `PARTIAL`, `FAILED` |
| `validation_run_id` | FK | No | Related validation |
| `is_publishable` | Boolean | Yes | True only if final checks pass |
| `published_at` | Timestamp | No | Required if bundle type `PUBLISHED` |
| `published_by` | User ID | No |  |
| `artifact_manifest_json` | JSON | Yes | List of generated artifacts |
| `lock_status` | Enum | Yes | Published bundles locked |
| audit fields | Shared | Yes |  |

---

## 8.46 `WizardGeneratedArtifact`

### Purpose

Represents each file or generated artifact in a preview/published bundle.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `preview_bundle_id` | FK | Yes | Parent |
| `artifact_type` | Enum | Yes | `HTML`, `PDF`, `DOCX`, `JSON_SCHEMA`, `SUPPLIER_SCHEMA`, `EVALUATION_SCHEMA`, `CONTRACT_HANDOFF`, `ADDENDUM_NOTICE`, `OTHER` |
| `artifact_title` | String | Yes |  |
| `file_id` | File ID | Conditional | Required for stored artifact |
| `artifact_json` | JSON | Conditional | For schema outputs |
| `artifact_hash` | String | Yes |  |
| `render_block_ids_json` | JSON | Yes | Blocks used |
| `page_count` | Integer | No | If PDF/DOCX render known |
| `is_public` | Boolean | Yes | Whether artifact is supplier-facing |
| `is_immutable` | Boolean | Yes | True after publication |
| audit fields | Shared | Yes |  |

---

## 8.47 `WizardHashEvidence`

### Purpose

Stores hash evidence for instance configuration, generated bundles, rendered artifacts, and source references.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `object_type` | String | Yes |  |
| `object_id` | UUID/String | Yes |  |
| `hash_type` | Enum | Yes | `SOURCE`, `CONFIGURATION`, `ROW`, `BUNDLE`, `ARTIFACT`, `SCHEMA`, `AUDIT_CHAIN` |
| `hash_algorithm` | String | Yes | Example: `SHA-256` |
| `hash_value` | String | Yes |  |
| `hash_payload_canonical_json` | JSON | Conditional | Store canonical payload or reference as policy permits |
| `created_at` | Timestamp | Yes |  |
| `created_by` | User ID/System | Yes |  |

### Constraints

Hash evidence records are append-only.

---

## 8.48 `WizardReviewTrack`

### Purpose

Defines active review tracks for the tender STD instance.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `review_track` | Enum | Yes | Review Track Enum |
| `track_order` | Integer | Yes |  |
| `required` | Boolean | Yes |  |
| `parallel_allowed` | Boolean | Yes | Whether track may run parallel with others |
| `status` | Enum | Yes | `NOT_STARTED`, `IN_PROGRESS`, `RETURNED`, `APPROVED`, `SKIPPED`, `CANCELLED` |
| `started_at` | Timestamp | No |  |
| `completed_at` | Timestamp | No |  |
| `current_assignment_id` | FK | No |  |
| audit fields | Shared | Yes |  |

---

## 8.49 `WizardReviewAssignment`

### Purpose

Assigns users or roles to review tracks.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `review_track_id` | FK | Yes | Parent |
| `assigned_user_id` | User ID | No | One of user or role required |
| `assigned_role` | String | No |  |
| `assigned_by` | User ID/System | Yes |  |
| `assigned_at` | Timestamp | Yes |  |
| `due_at` | Timestamp | No |  |
| `status` | Enum | Yes | `PENDING`, `IN_PROGRESS`, `COMPLETED`, `REASSIGNED`, `CANCELLED` |
| `reassignment_reason` | Text | No |  |
| audit fields | Shared | Yes |  |

---

## 8.50 `WizardReviewDecision`

### Purpose

Stores reviewer decisions, comments, returns, approvals, and escalations.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `review_track_id` | FK | Yes | Parent |
| `review_assignment_id` | FK | No |  |
| `tender_std_instance_id` | FK | Yes | Denormalized |
| `decision` | Enum | Yes | Review Decision Enum |
| `decision_text` | Text | Conditional | Required for return, reject, escalate |
| `affected_step_code` | String | No |  |
| `affected_object_type` | String | No |  |
| `affected_object_id` | UUID/String | No |  |
| `requires_correction` | Boolean | Yes |  |
| `correction_due_at` | Timestamp | No |  |
| `decided_by` | User ID | Yes |  |
| `decided_at` | Timestamp | Yes |  |
| `state_transition_event_id` | FK | No | If decision moved state |
| `decision_hash` | String | Yes |  |
| audit fields | Shared | Yes | Append-only |

### Constraints

Return/reject decisions must include a clear reason and affected scope.

---

## 8.51 `WizardApprovalGateStatus`

### Purpose

Stores each approval gate required before publication.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Parent |
| `gate_code` | String | Yes | `PROCUREMENT_APPROVAL`, `TECHNICAL_APPROVAL`, `LEGAL_APPROVAL`, `FINANCE_APPROVAL`, `FINAL_APPROVAL`, `PUBLICATION_CHECK` |
| `gate_title` | String | Yes |  |
| `required` | Boolean | Yes |  |
| `status` | Enum | Yes | `NOT_STARTED`, `BLOCKED`, `READY`, `APPROVED`, `WAIVED`, `FAILED` |
| `approved_by` | User ID | No |  |
| `approved_at` | Timestamp | No |  |
| `waived_by` | User ID | No | If waiver allowed |
| `waiver_reason` | Text | Conditional | Required if waived |
| `blocking_reason` | Text | No |  |
| `related_review_decision_id` | FK | No |  |
| audit fields | Shared | Yes |  |

---

## 8.52 `WizardAddendumRequest`

### Purpose

Starts an addendum workflow for a published tender STD instance.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `tender_std_instance_id` | FK | Yes | Published parent |
| `addendum_number` | Integer | Yes | Sequence per tender |
| `request_title` | String | Yes |  |
| `request_description` | Text | Yes |  |
| `requested_by` | User ID | Yes |  |
| `requested_at` | Timestamp | Yes |  |
| `request_reason` | Text | Yes |  |
| `initial_impact_type` | Enum | No | Addendum Impact Type Enum |
| `status` | Enum | Yes | `REQUESTED`, `IMPACT_ANALYSIS_PENDING`, `IMPACT_ANALYSIS_COMPLETE`, `APPROVED_FOR_CONFIGURATION`, `IN_CONFIGURATION`, `READY_FOR_PUBLICATION`, `PUBLISHED`, `REJECTED`, `CANCELLED` |
| `approved_scope_text` | Text | Conditional | Required before configuration |
| `published_addendum_bundle_id` | FK | No | Required when published |
| audit fields | Shared | Yes |  |

### Constraints

Addendum requests are allowed only after parent instance is `PUBLISHED`.

---

## 8.53 `WizardAddendumImpactAnalysis`

### Purpose

Stores system and reviewer analysis of addendum impacts.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `addendum_request_id` | FK | Yes | Parent |
| `analysis_status` | Enum | Yes | `PENDING`, `COMPLETE`, `FAILED` |
| `primary_impact_type` | Enum | Yes | Addendum Impact Type Enum |
| `requires_deadline_extension` | Boolean | Yes |  |
| `requires_supplier_notification` | Boolean | Yes |  |
| `requires_reissue` | Boolean | Yes |  |
| `affects_evaluation` | Boolean | Yes |  |
| `affects_price_schedule` | Boolean | Yes |  |
| `affects_contract_carry_forward` | Boolean | Yes |  |
| `affects_published_supplier_schema` | Boolean | Yes |  |
| `analysis_summary` | Text | Yes |  |
| `analysis_json` | JSON | Yes | Machine-readable impact result |
| `analysed_by` | User ID/System | Yes |  |
| `analysed_at` | Timestamp | Yes |  |
| audit fields | Shared | Yes |  |

---

## 8.54 `WizardAddendumAffectedObject`

### Purpose

Lists each object affected by an addendum.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `addendum_impact_analysis_id` | FK | Yes | Parent |
| `object_type` | String | Yes | Parameter, requirement, price line, form, date, render block, etc. |
| `object_id` | UUID/String | Yes |  |
| `object_title` | String | Yes |  |
| `impact_type` | Enum | Yes | Addendum Impact Type Enum |
| `old_value_json` | JSON | No |  |
| `proposed_new_value_json` | JSON | No |  |
| `requires_review_track` | Enum | No | Review Track Enum |
| `requires_supplier_response_change` | Boolean | Yes |  |
| `requires_evaluation_reset` | Boolean | Yes | If already in evaluation stage, later integration |
| audit fields | Shared | Yes |  |

---

## 8.55 `WizardAddendumBundle`

### Purpose

Represents the published addendum artifact bundle.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `addendum_request_id` | FK | Yes | Parent |
| `parent_published_bundle_id` | FK | Yes | Original tender bundle |
| `addendum_bundle_code` | String | Yes |  |
| `addendum_number` | Integer | Yes |  |
| `generated_at` | Timestamp | Yes |  |
| `published_at` | Timestamp | No |  |
| `published_by` | User ID | No |  |
| `bundle_hash` | String | Yes |  |
| `artifact_manifest_json` | JSON | Yes |  |
| `supplier_notification_text` | Text | Yes |  |
| `lock_status` | Enum | Yes |  |
| audit fields | Shared | Yes |  |

---

## 8.56 `TenderCalibrationFixture`

### Purpose

Stores non-production calibration fixture metadata, such as the NSSF ERP tender, to test whether real tenders can be represented by the STD package.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `fixture_code` | String | Yes | Example: `NSSF_SPS_ERP_2025_2026` |
| `fixture_title` | String | Yes |  |
| `fixture_source_file_id` | File ID | Yes | Uploaded tender fixture |
| `fixture_hash` | String | Yes |  |
| `related_std_version_id` | FK | Yes | STD package tested against |
| `importable_to_production` | Boolean | Yes | Must be false by default |
| `fixture_status` | Enum | Yes | `DRAFT`, `MAPPED`, `VALIDATED`, `ARCHIVED` |
| `notes` | Text | No |  |
| audit fields | Shared | Yes |  |

### Constraints

Calibration fixtures must never create master STD package content automatically. They may create mapping evidence, test data, or draft tender instance examples only.

---

## 8.57 `TenderCalibrationMapping`

### Purpose

Maps calibration fixture content to wizard/STD objects.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `calibration_fixture_id` | FK | Yes | Parent |
| `fixture_section_reference` | String | Yes | Fixture page/section/table reference |
| `target_object_type` | String | Yes | Wizard object type |
| `target_object_id` | UUID/String | No | May be null until mapped |
| `target_std_object_id` | UUID/String | No | Related master STD object if applicable |
| `mapping_status` | Enum | Yes | `UNMAPPED`, `MAPPED`, `PARTIAL`, `DEVIATION`, `NOT_APPLICABLE` |
| `mapping_notes` | Text | No |  |
| `confidence` | Enum | Yes | `HIGH`, `MEDIUM`, `LOW` |
| audit fields | Shared | Yes |  |

---

## 8.58 `TenderCalibrationDeviation`

### Purpose

Records real-world tender deviations from the STD model.

### Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Primary key |
| `calibration_fixture_id` | FK | Yes | Parent |
| `deviation_code` | String | Yes | Stable code |
| `deviation_title` | String | Yes |  |
| `deviation_description` | Text | Yes |  |
| `affected_std_area` | String | Yes | TDS, SCC, Price, Evaluation, etc. |
| `severity` | Enum | Yes | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `recommended_engine_response` | Enum | Yes | `REPRESENT_AS_PARAMETER`, `REPRESENT_WITH_WARNING`, `REQUIRE_REVIEW`, `BLOCK_UNLESS_ALLOWED`, `DO_NOT_SUPPORT`, `OTHER` |
| `requires_std_package_change` | Boolean | Yes |  |
| `requires_policy_decision` | Boolean | Yes |  |
| `resolution_status` | Enum | Yes | `OPEN`, `ACCEPTED`, `REJECTED`, `DEFERRED`, `RESOLVED` |
| audit fields | Shared | Yes |  |

---

## 9. Relationship Summary

| Parent | Child | Cardinality | Delete Rule |
|---|---|---:|---|
| `TenderSTDInstance` | `WizardStepInstance` | 1:N | Restrict; logical delete only before publication |
| `TenderSTDInstance` | `TenderIdentityProfile` | 1:1 | Restrict |
| `TenderSTDInstance` | `ProcurementParticipationProfile` | 1:1 | Restrict |
| `TenderSTDInstance` | `TenderDateProfile` | 1:1 | Restrict |
| `TenderSTDInstance` | `TenderSubmissionProfile` | 1:1 | Restrict |
| `TenderSTDInstance` | `SecurityInstrumentProfile` | 1:1 | Restrict |
| `TenderSTDInstance` | `TenderSTDParameterValue` | 1:N | Restrict |
| `TenderSTDInstance` | `ITRequirementSet` | 1:1 | Restrict |
| `ITRequirementSet` | `ITRequirementGroup` | 1:N | Restrict |
| `ITRequirementGroup` | `ITRequirementItem` | 1:N | Restrict |
| `ITRequirementItem` | `ITRequirementEvidenceBinding` | 1:N | Restrict |
| `ITImplementationPlan` | `ITImplementationPhase` | 1:N | Restrict |
| `ITImplementationPhase` | `ITImplementationMilestone` | 1:N | Restrict |
| `ITImplementationPlan` | `ITAcceptanceEvent` | 1:N | Restrict |
| `ITSystemInventoryTable` | `ITSystemInventoryItem` | 1:N | Restrict |
| `ITPriceScheduleProfile` | `ITPriceScheduleTable` | 1:N | Restrict |
| `ITPriceScheduleTable` | `ITPriceScheduleLineTemplate` | 1:N | Restrict |
| `ITEvaluationProfile` | `ITEvaluationStage` | 1:N | Restrict |
| `ITEvaluationStage` | `ITEvaluationCriterion` | 1:N | Restrict |
| `ITEvaluationCriterion` | `ITEvaluationSubcriterion` | 1:N | Restrict |
| `TenderSTDInstance` | `WizardValidationRun` | 1:N | Append-only |
| `WizardValidationRun` | `WizardValidationFinding` | 1:N | Append-only |
| `TenderSTDInstance` | `WizardPreviewBundle` | 1:N | Restrict |
| `WizardPreviewBundle` | `WizardGeneratedArtifact` | 1:N | Restrict |
| `TenderSTDInstance` | `WizardReviewTrack` | 1:N | Restrict |
| `WizardReviewTrack` | `WizardReviewAssignment` | 1:N | Restrict |
| `WizardReviewTrack` | `WizardReviewDecision` | 1:N | Append-only |
| `TenderSTDInstance` | `WizardAddendumRequest` | 1:N | Restrict |
| `WizardAddendumRequest` | `WizardAddendumImpactAnalysis` | 1:1/N | Append-only versions |
| `WizardAddendumImpactAnalysis` | `WizardAddendumAffectedObject` | 1:N | Append-only |

---

## 10. Immutability Rules

| Rule ID | Rule |
|---|---|
| `IMM-WIZ-001` | `TenderSTDInstance.std_version_id` is immutable after creation. |
| `IMM-WIZ-002` | Published tender STD instances cannot be edited directly. |
| `IMM-WIZ-003` | Published generated bundles and artifacts are immutable. |
| `IMM-WIZ-004` | Parameter value history is append-only. |
| `IMM-WIZ-005` | Validation runs and findings are append-only, except findings may receive resolution metadata where permitted. |
| `IMM-WIZ-006` | Review decisions are append-only. |
| `IMM-WIZ-007` | State transition events are append-only. |
| `IMM-WIZ-008` | Addendum records must not overwrite original published values. They must create addendum-specific values and affected-object records. |
| `IMM-WIZ-009` | Hash evidence records are append-only. |
| `IMM-WIZ-010` | Superseding a master STD version does not alter existing tender STD instances. |

---

## 11. Validation Rules Required by the Domain Model

| Rule Code | Scope | Severity | Description |
|---|---|---|---|
| `VAL-WIZ-001` | Instance | BLOCKER | Instance must be created from active STD package. |
| `VAL-WIZ-002` | Instance | BLOCKER | Bound STD version cannot be changed. |
| `VAL-WIZ-003` | Tender Identity | BLOCKER | Tender number must be unique for the Procuring Entity. |
| `VAL-WIZ-004` | Dates | BLOCKER | Clarification deadline must be before submission deadline. |
| `VAL-WIZ-005` | Dates | BLOCKER | Tender opening must not occur before submission deadline. |
| `VAL-WIZ-006` | Submission | BLOCKER | At least one permitted submission channel must be configured. |
| `VAL-WIZ-007` | Security | WARNING/BLOCKER | Professional indemnity used as tender security substitute requires STD permission or review. |
| `VAL-WIZ-008` | Participation | BLOCKER | Margin of preference may be enabled only if package and procurement method permit it. |
| `VAL-WIZ-009` | Participation | BLOCKER | Reservation group required when reservation applies. |
| `VAL-WIZ-010` | Requirements | WARNING | Vendor/product/cloud-specific terms require justification and review. |
| `VAL-WIZ-011` | Requirements | BLOCKER | Mandatory requirements must define supplier response type and evaluation treatment. |
| `VAL-WIZ-012` | Requirements | BLOCKER | Acceptance-test-required requirements must link to an acceptance event or test definition. |
| `VAL-WIZ-013` | Implementation | BLOCKER | Required implementation plan must contain at least one phase and milestone. |
| `VAL-WIZ-014` | Implementation | BLOCKER | Payment-linked milestones must define acceptance conditions. |
| `VAL-WIZ-015` | Inventory | BLOCKER | Required system inventory table must contain at least one item. |
| `VAL-WIZ-016` | Price | BLOCKER | Required price schedule tables must be generated and linked to inventory where applicable. |
| `VAL-WIZ-017` | Price | BLOCKER | Recurrent cost evaluation method required when recurrent costs are included in evaluation. |
| `VAL-WIZ-018` | Evaluation | BLOCKER | Technical scored criteria must sum to configured total points. |
| `VAL-WIZ-019` | Evaluation | BLOCKER | Technical pass mark must be less than or equal to total technical points. |
| `VAL-WIZ-020` | Evaluation | WARNING/BLOCKER | Vendor-specific qualification criteria require justification and review. |
| `VAL-WIZ-021` | Forms | BLOCKER | Mandatory package forms cannot be deactivated unless package rule permits omission. |
| `VAL-WIZ-022` | Evidence | BLOCKER | Mandatory evidence requirements must appear in supplier submission schema. |
| `VAL-WIZ-023` | SCC | BLOCKER | Payment, security, warranty, IP, acceptance, and dispute parameters require legal/finance review. |
| `VAL-WIZ-024` | Contract Carry-Forward | BLOCKER | Requirements marked contract carry-forward must appear in contract handoff schema. |
| `VAL-WIZ-025` | Preview | BLOCKER | Final preview bundle cannot be publishable if blocking findings remain. |
| `VAL-WIZ-026` | Publication | BLOCKER | Publication requires final validation, final render, approval gates, and bundle hash. |
| `VAL-WIZ-027` | Addendum | BLOCKER | Post-publication changes must go through addendum workflow. |
| `VAL-WIZ-028` | Calibration | BLOCKER | Calibration fixture content cannot be imported as master STD content. |

---

## 12. State Transition Guard Matrix

| From | To | Required Guards |
|---|---|---|
| `NOT_STARTED` | `INSTANCE_CREATED` | Active STD selected; user has create permission; package valid for draft instance creation |
| `INSTANCE_CREATED` | `IN_CONFIGURATION` | User has edit permission; steps generated |
| `IN_CONFIGURATION` | `VALIDATION_FAILED` | Validation run completed with blockers |
| `VALIDATION_FAILED` | `IN_CONFIGURATION` | User edits affected records |
| `IN_CONFIGURATION` | `READY_FOR_INTERNAL_REVIEW` | Mandatory fields complete; no blockers; required step statuses complete or warning-accepted |
| `READY_FOR_INTERNAL_REVIEW` | `PROCUREMENT_REVIEW` | Procurement review track exists and assignment active |
| `PROCUREMENT_REVIEW` | `RETURNED_FOR_CORRECTION` | Return decision with reason and affected scope |
| `PROCUREMENT_REVIEW` | `TECHNICAL_REVIEW` | Procurement approval recorded |
| `TECHNICAL_REVIEW` | `RETURNED_FOR_CORRECTION` | Return decision with reason and affected scope |
| `TECHNICAL_REVIEW` | `LEGAL_REVIEW` | Technical approval recorded; vendor-specific warnings resolved/accepted |
| `LEGAL_REVIEW` | `RETURNED_FOR_CORRECTION` | Return decision with reason and affected scope |
| `LEGAL_REVIEW` | `FINANCE_REVIEW` | Legal approval recorded |
| `FINANCE_REVIEW` | `RETURNED_FOR_CORRECTION` | Return decision with reason and affected scope |
| `FINANCE_REVIEW` | `APPROVED_FOR_TENDER_CREATION` | Finance approval; final approval decision; no blockers |
| `APPROVED_FOR_TENDER_CREATION` | `BOUND_TO_TENDER` | Tender Management record exists; user has bind permission; instance hash captured |
| `BOUND_TO_TENDER` | `PRE_PUBLICATION_FINAL_CHECK` | Final preview generated; supplier/evaluation/contract schemas generated |
| `PRE_PUBLICATION_FINAL_CHECK` | `PUBLISHED` | Final validation passed; approval gates approved; bundle hash created; publisher permission |
| `PUBLISHED` | `ADDENDUM_REQUIRED` | Change request logged; impact analysis required |
| `ADDENDUM_REQUIRED` | `ADDENDUM_IN_CONFIGURATION` | Addendum scope approved |
| `ADDENDUM_IN_CONFIGURATION` | `ADDENDUM_PUBLISHED` | Addendum validation passed; addendum bundle hash created; publisher permission |
| Any pre-publication state | `CANCELLED` | Cancellation reason; Procurement Manager permission |
| Closed states | `ARCHIVED` | Retention/archive policy executed by system |

---

## 13. Permission Model

### 13.1 Permission Codes

| Permission Code | Description |
|---|---|
| `wizard.instance.create` | Create tender STD instance from active STD version |
| `wizard.instance.read` | View wizard instance |
| `wizard.instance.edit` | Edit draft configuration |
| `wizard.instance.cancel` | Cancel pre-publication instance |
| `wizard.step.edit` | Edit assigned wizard step |
| `wizard.requirements.edit` | Edit IT requirements |
| `wizard.requirements.review` | Review IT requirements |
| `wizard.evaluation.edit` | Edit evaluation setup |
| `wizard.scc.edit` | Edit SCC configuration |
| `wizard.finance.review` | Review price/security/payment fields |
| `wizard.legal.review` | Review SCC/legal/contract fields |
| `wizard.procurement.review` | Procurement review |
| `wizard.approve.final` | Final approval for tender creation/publication |
| `wizard.preview.generate` | Generate preview bundle |
| `wizard.validation.run` | Run validation |
| `wizard.publish` | Publish approved tender bundle |
| `wizard.addendum.request` | Request addendum |
| `wizard.addendum.configure` | Configure addendum scope |
| `wizard.addendum.publish` | Publish addendum bundle |
| `wizard.audit.read` | View audit trail and hash evidence |
| `wizard.calibration.manage` | Manage non-production calibration fixture mappings |

### 13.2 Role Permission Matrix

| Role | Key Permissions |
|---|---|
| Procurement Officer | create, read, edit, step edit, requirements edit, evaluation edit, SCC draft edit, validation run, preview generate, submit for review |
| Procurement Manager | read, procurement review, return, approve procurement stage, cancel, request addendum |
| Technical Owner | read, requirements edit, technical clarifications, respond to review returns |
| ICT Reviewer | read, requirements review, vendor-neutrality review, technical approval/return |
| Legal Reviewer | read, legal review, SCC/contract approval/return |
| Finance/Budget Reviewer | read, finance review, price/security/payment approval/return |
| Approving Authority | read, final approval, escalation decision |
| Tender Publisher | read, final validation, final render, publish, addendum publish |
| Auditor | read, audit read, hash evidence read |
| System Administrator | technical role assignment; no legal content editing by default |
| STD Administrator | master STD package management in STD Core; read wizard as needed |

---

## 14. Indexing and Query Strategy

### 14.1 Required Operational Indexes

| Entity | Index Fields | Purpose |
|---|---|---|
| `TenderSTDInstance` | `tenant_id`, `procuring_entity_id`, `wizard_state` | Dashboard state filtering |
| `TenderSTDInstance` | `std_version_id` | Usage tracking by STD version |
| `TenderSTDInstance` | `tender_id` | Tender binding lookup |
| `WizardStepInstance` | `tender_std_instance_id`, `step_order` | Wizard navigation |
| `TenderSTDParameterValue` | `tender_std_instance_id`, `std_parameter_id` | Parameter lookup |
| `ITRequirementItem` | `requirement_set_id`, `category` | Requirement filtering |
| `ITRequirementItem` | `requirement_set_id`, `vendor_specific_flag` | Review filtering |
| `WizardValidationFinding` | `tender_std_instance_id`, `severity`, `resolution_status` | Validation dashboard |
| `WizardReviewDecision` | `tender_std_instance_id`, `decided_at` | Review trail |
| `WizardPreviewBundle` | `tender_std_instance_id`, `bundle_type`, `generated_at` | Render history |
| `WizardAddendumRequest` | `tender_std_instance_id`, `addendum_number` | Addendum history |

### 14.2 Audit Query Requirements

The system must support efficient retrieval of:

1. Who changed a field, when, from what, to what, and why.
2. Which STD package/version was used for a tender.
3. Which validation blockers existed at each review stage.
4. Which reviewer approved or returned each review stage.
5. Which exact generated artifact was published.
6. Which addendum changed which published object.
7. Which supplier submission schema was active at publication.
8. Which evaluation schema was generated from the published tender.

---

## 15. JSON Payload Standards

### 15.1 General Rule

JSON fields are allowed only for structured payloads that are variable by STD package or too complex for stable columns. They must not be used to hide core searchable state.

### 15.2 Required JSON Payload Patterns

| JSON Field | Required Structure |
|---|---|
| `country_restriction_policy_json` | List of country eligibility rules and legal basis |
| `modules_or_scope_json` | List of implementation modules/scope items with codes and descriptions |
| `acceptance_criteria_json` | List of acceptance criteria, test methods, evidence, signoff role |
| `calculation_formula_json` | Machine-readable arithmetic/formula structure |
| `schema_json` | JSON schema for supplier/evaluation/contract handoff |
| `artifact_manifest_json` | Artifact list with titles, file IDs, hashes, visibility, render blocks |
| `guard_result_json` | Transition guards evaluated with pass/fail and messages |
| `analysis_json` | Addendum impact analysis result |

### 15.3 Canonical Hashing

All JSON payloads used for hashing must be canonicalized with:

1. Stable key ordering.
2. UTF-8 encoding.
3. No insignificant whitespace.
4. Normalized date/time format.
5. Stable decimal serialization.

---

## 16. Generated Schema Outputs

The wizard must generate and store snapshots for three downstream schemas.

### 16.1 Supplier Submission Schema

Generated from:

1. Active forms.
2. Required evidence.
3. Requirement items requiring supplier response.
4. Price schedule tables.
5. Qualification requirements.
6. Tender security/professional indemnity requirements.

### 16.2 Evaluation Workspace Schema

Generated from:

1. Preliminary mandatory requirements.
2. Technical pass/fail criteria.
3. Technical scored criteria and subcriteria.
4. Requirement conformance matrix.
5. Financial evaluation formulas.
6. Recurrent cost method.
7. Postqualification requirements.

### 16.3 Contract Carry-Forward Schema

Generated from:

1. Tender identity.
2. Contract name/description.
3. Winning supplier data at award stage.
4. Approved requirements marked carry-forward.
5. Price schedules and revised prices.
6. Implementation phases and milestones.
7. Acceptance events and certificates.
8. SCC parameters.
9. IP/software/license/custom materials fields.
10. Securities, warranty, SLA, support, and change order data.

---

## 17. Data Retention and Audit Rules

| Record Type | Retention Rule |
|---|---|
| Tender STD instances | Retain for statutory procurement record period; never physically delete if published |
| Parameter histories | Retain with parent instance permanently for audit period |
| Review decisions | Append-only, retain permanently with tender record |
| Validation runs | Retain all runs from review submission onward; draft auto-save runs may be compacted only before publication if policy allows |
| Published bundles | Retain immutable artifact and hash evidence permanently for audit period |
| Addendum bundles | Retain with original tender bundle |
| Calibration fixtures | May be archived, not deleted, if used for design evidence |

---

## 18. Non-Functional Domain Requirements

| Requirement | Description |
|---|---|
| Auditability | Every change to legally relevant data must be attributable, timestamped, and reconstructable. |
| Immutability | Published records and bundles must be technically immutable. |
| Traceability | Tender values must trace to STD version, parameter/rule/form, and source anchors where applicable. |
| Determinism | Given the same STD package and same configuration, render and schema outputs must be deterministic. |
| Extensibility | Domain must support future STD families without schema rewrite wherever possible. |
| Searchability | Core review, validation, requirement, price, and state fields must be queryable without parsing large JSON blobs. |
| Performance | Wizard dashboard queries must be served from summarized status records rather than recalculating all validations. |
| Security | Role-based access must prevent unauthorized edits, reviews, publication, and addendum creation. |
| Legal defensibility | Published output must be hash-verifiable against configuration and STD package evidence. |

---

## 19. Activation Blockers Before Implementation

The wizard domain model is not implementation-authorized until the following are completed:

1. Governance/state-transition model approved.
2. Role and permission matrix approved.
3. Seed data for wizard states, step statuses, review tracks, permissions, and validation severities prepared.
4. Smoke contracts defined for instance creation, validation, review, publication, and addendum.
5. Cursor implementation pack prepared.
6. IT STD package v0.2 or later imported successfully in draft mode.
7. Legal/procurement reviewers confirm locked text cannot be edited through the wizard.
8. Technical reviewers confirm vendor-neutrality review and requirement composer behaviors.
9. Finance reviewers confirm price schedule and payment milestone model.
10. Audit reviewers confirm hash and evidence requirements.

---

## 20. Smoke Contracts Required from This Domain Model

| Smoke Contract | Purpose |
|---|---|
| `SMOKE-WIZ-001-create-instance-from-active-std` | Ensure instance can only be created from active STD version. |
| `SMOKE-WIZ-002-generate-steps-from-package` | Ensure wizard steps are generated from package definitions. |
| `SMOKE-WIZ-003-complete-required-tds-values` | Ensure required TDS values are captured and validated. |
| `SMOKE-WIZ-004-detect-invalid-date-order` | Ensure date validation blockers fire. |
| `SMOKE-WIZ-005-detect-vendor-specific-requirements` | Ensure vendor/product-specific terms trigger review findings. |
| `SMOKE-WIZ-006-generate-requirements-compliance-matrix` | Ensure requirement items become supplier response schema. |
| `SMOKE-WIZ-007-generate-price-schedule-schema` | Ensure price tables and recurrent costs generate correctly. |
| `SMOKE-WIZ-008-validate-technical-scoring-total` | Ensure technical scores sum to configured total. |
| `SMOKE-WIZ-009-generate-contract-carry-forward` | Ensure contract obligations are handed forward. |
| `SMOKE-WIZ-010-block-publication-with-blockers` | Ensure blocking findings prevent publication. |
| `SMOKE-WIZ-011-publish-immutable-bundle` | Ensure published bundle is hashed and immutable. |
| `SMOKE-WIZ-012-require-addendum-after-publication` | Ensure post-publication changes cannot edit original bundle. |
| `SMOKE-WIZ-013-map-nssf-erp-fixture` | Ensure NSSF ERP calibration data can be represented as tender instance data, not master STD data. |

---

## 21. Next Artifact

The next artifact should be:

`IT_Tender_Configuration_Wizard_Governance_Roles_Permissions_State_Model.md`

That document should lock:

1. Transition-level role authority.
2. Step editability by state.
3. Review assignment behavior.
4. Approval-gate requirements.
5. Addendum authority.
6. Publication authority.
7. Permission seed records.
8. Audit-event requirements for every state transition.

