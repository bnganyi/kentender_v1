# IT Tender Configuration Wizard — Cursor Implementation Pack

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Document type:** Cursor Implementation Pack  
**Version:** 0.1  
**Status:** Draft for build execution  
**Prepared date:** 2026-07-08  
**Primary dependency:** STD Engine Core Module  
**Reference STD family:** `KE-PPRA-IT`  
**Reference package:** `KE-PPRA-IT-2022-04`  
**Calibration fixture:** NSSF SPS ERP System Tender, Ref. `NSSFSPS/ICT/ERP/001/2025-2026`  

**Preceding artifacts:**

1. `IT_Tender_Configuration_Wizard_PRD.md`
2. `IT_Tender_Configuration_Wizard_Domain_Model.md`
3. `IT_Tender_Configuration_Wizard_Governance_Roles_Permissions_State_Model.md`
4. `IT_Tender_Configuration_Wizard_Seed_Data_and_Smoke_Contracts.md`
5. `IT_Tender_Configuration_Wizard_API_UI_Service_Contract.md`
6. `STD_Engine_Core_Module_PRD.md`
7. `STD_Engine_Core_Domain_Model.md`
8. `STD_Engine_Core_Governance_Roles_Permissions_State_Model.md`
9. `STD_Engine_Core_API_UI_Service_Contract.md`
10. `STD_Engine_Core_Cursor_Implementation_Pack.md`
11. `STD_IT_Extraction_Matrix.md`
12. `STD_IT_Seed_Package_Specification.md`
13. `STD_IT_Package_Validation_Report_v0_2.md`
14. `NSSF_ERP_Calibration_Mapping.md`

---

## 1. Purpose

This implementation pack converts the IT Tender Configuration Wizard design artifacts into concrete build instructions suitable for Cursor-assisted development.

The wizard is the controlled Procuring Entity configuration layer for tenders that use the Standard Tender Document for Procurement of Information Technology. It must let authorized users configure an IT tender through structured fields, guided requirement composition, validation, review, preview, approval, publication-bundle generation, and addendum impact analysis.

The wizard must not become a document editor. It must not allow users to alter locked ITT, GCC, master STD clauses, master rules, master render order, or active package content. It must consume the active STD package through the STD Engine Core and persist only tender-specific configuration values, generated snapshots, review decisions, validation evidence, and publication artifacts.

---

## 2. How to Use This Pack in Cursor

Use this document as the governing implementation prompt for the IT Tender Configuration Wizard module.

Recommended workflow:

1. Load this file into Cursor context.
2. Load the preceding artifacts listed above into context.
3. Confirm the STD Engine Core service contracts are available or mocked.
4. Implement one build stage at a time.
5. Run tests after each build stage.
6. Do not proceed to UI implementation until lifecycle, permissions, validation, and persistence tests pass.
7. Do not generate publication-bundle functionality until preview-bundle and hash-evidence tests pass.
8. Do not expose addendum actions until publication immutability tests pass.

### 2.1 Master Cursor Instruction

Use this instruction at the start of each Cursor implementation session:

```text
You are implementing the KenTender IT Tender Configuration Wizard.

Follow the implementation pack exactly.
The wizard must be a controlled configuration surface, not a legal document editor.
It must consume active STD package definitions from the STD Engine Core and must not duplicate or mutate master STD content.

Before any screen UI or Desk wiring work, load and obey:
- 99 IT_Tender_Wizard_Screen_Ownership_Matrix.md (field ownership / editability / source presentation)
- 98 IT_Tender_Wizard_Screen_Ownership_Correction_Plan.md
- Screen_Ownership_Implementation_Tracker.md

The Ownership Matrix is the correction layer over PRD, Domain, API, Governance, Pack, Sprint backlog, and design HTML when they conflict on which screen owns a field.
Do not show magical, hardcoded, or unexplained template values.
If a value has no configured source, show "Not configured".
If another screen owns a field, show it read-only with source label, owning screen, and Edit in [owning screen].
Do not start ITW-08+ Desk wiring until make it-wizard-ownership-gate is green and the matching ITW-OWN-* precondition is Ready/Done.

Implement tender-specific configuration records, wizard steps, requirements, implementation schedule, system inventory, price setup, evaluation configuration, SCC values, validation runs, review/approval workflow, preview generation, publication bundle handoff, and addendum impact analysis.

Do not hard-code NSSF ERP tender behavior.
Do not hard-code Microsoft Dynamics-specific behavior.
Use package-provided schema and tender-specific configuration values.
The NSSF ERP tender is only a calibration fixture and test case.

Enforce lifecycle transitions, role permissions, validation blockers, immutable published bundles, source-trace display, audit events, hash evidence, and addendum governance.
If a shortcut would allow direct editing of locked STD text or published tender artifacts, reject the shortcut and implement the governed workflow instead.
```

---

## 3. Framework Assumptions

This pack is framework-neutral. The implementation stack may be Frappe/ERPNext, Django, FastAPI, NestJS, Laravel, Rails, or another application framework.

The platform must support equivalent capabilities for:

1. Relational or document persistence with indexed fields.
2. JSON schema validation.
3. Server-side services.
4. Role-based access control.
5. Object-level authorization.
6. Workflow/state transitions.
7. Audit logging.
8. File/artifact storage.
9. Deterministic hashing.
10. Background jobs for validation and rendering.
11. API endpoints.
12. UI screens and components.
13. Automated unit, integration, permission, workflow, and smoke tests.

Where the platform is Frappe/ERPNext, implement models as DocTypes, services as Python modules and whitelisted methods, lifecycle actions as DocType methods/workflows, seeds as fixtures or patch scripts, and tests as integration tests.

Where the platform uses a conventional MVC or service architecture, map these responsibilities to models, migrations, services, controllers, policies, jobs, serializers, and tests.

---

## 4. Non-Negotiable Controls

| Control | Required behavior |
|---|---|
| Exact STD version binding | A wizard instance must bind to exactly one active `std_version_id` at creation. |
| No floating package reference | A wizard instance must not automatically upgrade when a later STD package version becomes active. |
| No master content editing | The wizard must not edit STD Template Version, Section, Clause, Rule, Form, Render Block, or master source-trace records. |
| Locked clause protection | ITT and GCC legal text must display as reference/preview only. |
| Structured configuration | TDS, SCC, requirements, schedules, price setup, evaluation, forms, and evidence must be captured as structured data. |
| Validation gates | Blocker findings must prevent submission for review, approval, binding, publication, and addendum publication. |
| Approval workflow | Review tracks and approval gates must be enforced before publication. |
| Segregation of duties | The same actor must not perform conflicting workflow actions where configured policy forbids it. |
| Published bundle immutability | A generated publication bundle must be immutable after publication. |
| Addendum governance | Post-publication configuration changes must go through addendum impact workflow. |
| Hash evidence | Preview, publication, generated artifact, supplier schema, evaluation schema, and contract carry-forward hashes must be deterministic. |
| Source trace visibility | Users must be able to see source anchors for master STD-derived fields and render blocks where available. |
| Auditability | Every material action must generate an audit event. |
| Calibration isolation | NSSF ERP calibration records must not be imported into production tender data unless explicitly loaded as test fixtures. |

---

## 5. Implementation Boundary

### 5.1 In Scope

Implement the IT Tender Configuration Wizard:

1. Tender STD instance creation from an active IT STD package.
2. Wizard step generation from package-provided bindings.
3. Tender identity profile.
4. Procurement participation profile.
5. Date, clarification, opening, and submission profile.
6. Tender security or professional indemnity/security-instrument profile.
7. TDS values.
8. SCC values.
9. IT background, objectives, scope, and task fields.
10. IT requirements composer.
11. Implementation phases, milestones, locations, dependencies, and acceptance events.
12. System inventory tables.
13. Price schedule configuration.
14. Evaluation and qualification configuration.
15. Tendering form activation and evidence requirements.
16. Supplier response schema snapshot generation.
17. Evaluation workspace schema snapshot generation.
18. Contract carry-forward package preview.
19. Validation runs and findings.
20. Review and approval workflow.
21. Preview bundle generation.
22. Tender binding and publication bundle generation.
23. Addendum impact analysis.
24. Audit and hash evidence.
25. UI screens for all wizard steps.
26. API endpoints and service methods.
27. Seed data and smoke-contract execution.
28. Tests.

### 5.2 Out of Scope

Do not implement these in this wizard pack unless a later artifact explicitly authorizes it:

1. Master STD package authoring.
2. Full PPRA legal review console.
3. Supplier portal tender-submission UI.
4. Bid opening ceremonies.
5. Evaluation committee scoring workspace.
6. Award recommendation and award approval workflow.
7. Contract execution management.
8. Payment processing.
9. External PPRA API integration.
10. OCR/extraction tooling.
11. Full PDF styling parity with the official source documents.
12. Custom NSSF ERP-specific tender hard-coding.

---

## 6. Dependency Contract with STD Engine Core

The wizard must call or reference the STD Engine Core for the following responsibilities.

| Need | Core dependency |
|---|---|
| Active STD version lookup | `STDTemplateVersionService` |
| Package metadata | `PackageRegistryService` |
| Section and step bindings | `STDSectionService`, `STDWorkflowBindingService` |
| Parameter schemas | `STDParameterService` |
| Rules | `RuleEngineService` |
| Forms and evidence | `FormSchemaService`, `EvidenceRequirementService` |
| Requirement schemas | `RequirementSchemaService` |
| Price schemas | `PriceSchemaService` |
| Evaluation schemas | `EvaluationSchemaService` |
| Contract schemas | `ContractSchemaService` |
| Render blocks | `RenderService` |
| Source trace display | `SourceTraceService` |
| Validation | `ValidationService`, `RuleEngineService` |
| Canonical JSON and hashing | `CanonicalJsonService`, `HashService` |
| Audit logging | `AuditService` |
| Package smoke contracts | `SmokeContractService` |

Hard rule: if a Core service is not yet implemented, create an adapter interface and a mock implementation for tests. Do not bypass the dependency by copying master STD data into wizard code.

---

## 7. Recommended Repository Structure

Adapt paths to the actual platform, but preserve the logical boundaries.

```text
kentender/
  it_tender_wizard/
    README.md
    models/
      __init__.py
      instance_models.py
      step_models.py
      profile_models.py
      parameter_value_models.py
      requirement_models.py
      implementation_schedule_models.py
      inventory_models.py
      price_schedule_models.py
      evaluation_models.py
      form_evidence_models.py
      contract_carry_forward_models.py
      validation_models.py
      review_models.py
      preview_models.py
      publication_models.py
      addendum_models.py
      calibration_models.py
      audit_hash_models.py
    migrations/
      0001_instance_and_steps.*
      0002_profiles_and_parameter_values.*
      0003_requirements.*
      0004_implementation_schedule.*
      0005_inventory_and_price.*
      0006_evaluation_forms_evidence.*
      0007_validation_review_preview.*
      0008_publication_addendum.*
      0009_calibration_audit_hash.*
      0010_indexes_constraints.*
    enums/
      wizard_states.py
      wizard_step_statuses.py
      validation_severities.py
      requirement_types.py
      price_table_types.py
      evaluation_stage_types.py
      review_decisions.py
      addendum_statuses.py
    services/
      std_core_adapter.py
      wizard_instance_service.py
      wizard_step_service.py
      tender_identity_service.py
      participation_service.py
      tender_date_service.py
      security_instrument_service.py
      tds_service.py
      scc_service.py
      requirement_composer_service.py
      implementation_schedule_service.py
      system_inventory_service.py
      price_schedule_service.py
      evaluation_config_service.py
      form_evidence_service.py
      supplier_schema_snapshot_service.py
      evaluation_schema_snapshot_service.py
      contract_carry_forward_service.py
      wizard_validation_service.py
      wizard_workflow_service.py
      wizard_review_service.py
      wizard_preview_service.py
      wizard_publication_service.py
      wizard_addendum_service.py
      wizard_audit_service.py
      wizard_hash_service.py
      calibration_fixture_service.py
    api/
      routes.py
      serializers.py
      validators.py
      instance_endpoints.py
      tds_endpoints.py
      scc_endpoints.py
      requirement_endpoints.py
      implementation_schedule_endpoints.py
      inventory_endpoints.py
      price_endpoints.py
      evaluation_endpoints.py
      form_evidence_endpoints.py
      validation_endpoints.py
      preview_endpoints.py
      review_endpoints.py
      publication_endpoints.py
      addendum_endpoints.py
      audit_endpoints.py
    ui/
      pages/
        ITTenderWizardShell.*
        TenderIdentityPage.*
        ProcurementParticipationPage.*
        DatesClarificationsOpeningPage.*
        SecurityInstrumentPage.*
        ITRequirementsComposerPage.*
        ImplementationSchedulePage.*
        SystemInventoryPage.*
        PriceScheduleSetupPage.*
        EvaluationQualificationPage.*
        FormsEvidencePage.*
        SCCContractParametersPage.*
        ValidationPage.*
        PreviewPage.*
        ReviewApprovalPage.*
        AddendumImpactPage.*
      components/
        WizardHeader.*
        WizardStepRail.*
        SectionStatusBadge.*
        ValidationPanel.*
        SourceTracePanel.*
        RequirementTable.*
        RequirementDetailDrawer.*
        MilestoneTable.*
        InventoryTable.*
        PriceScheduleTable.*
        EvaluationCriteriaEditor.*
        EvidenceRequirementEditor.*
        PreviewViewer.*
        ApprovalDecisionPanel.*
        HashEvidencePanel.*
    seeds/
      roles.json
      permissions.json
      wizard_steps_it.json
      state_transitions.json
      validation_rule_bindings.json
      smoke_contracts.json
      calibration_fixtures/
        nssf_erp_mapping.json
    tests/
      unit/
      integration/
      permissions/
      workflow/
      validation/
      rendering/
      publication/
      addendum/
      smoke/
```

---

## 8. Required Model Groups

Implement model groups in this order. Do not start UI screens until these models and minimal services exist.

### 8.1 Instance and Step Models

Required entities:

1. `TenderSTDInstance`
2. `WizardStepInstance`
3. `WizardProgressSnapshot`
4. `WizardStateTransitionEvent`

Implementation requirements:

| Requirement | Rule |
|---|---|
| `TenderSTDInstance.std_version_id` | Required, immutable after creation. |
| `TenderSTDInstance.state` | Must use governed enum. |
| `TenderSTDInstance.tender_id` | Nullable until binding; immutable after binding except through governed correction. |
| `WizardStepInstance.step_key` | Derived from STD package/wizard seed. |
| `WizardStepInstance.status` | Not started, in progress, complete, failed, not applicable, locked. |
| `WizardProgressSnapshot` | Generated after material saves and validation runs. |
| `WizardStateTransitionEvent` | Created on every state transition attempt, including rejected attempts. |

### 8.2 Tender Profile Models

Required entities:

1. `TenderIdentityProfile`
2. `ProcurementParticipationProfile`
3. `TenderDateProfile`
4. `TenderSubmissionProfile`
5. `SecurityInstrumentProfile`

Implementation requirements:

1. Profile records must be one-to-one with `TenderSTDInstance` unless explicitly versioned.
2. Values must be validated against package-provided TDS parameter schemas.
3. Date fields must be timezone-aware.
4. Submission and opening information must be renderable into Invitation to Tender and TDS render blocks.
5. Security instrument configuration must support tender security, tender-securing declaration, professional indemnity, or package-defined instruments without hard-coding one tender’s approach.

### 8.3 Parameter Value Models

Required entities:

1. `TenderSTDParameterValue`
2. `TenderSTDParameterValueHistory`
3. `TenderSTDSectionValueStatus`

Implementation requirements:

1. Store parameter values separately from master parameter definitions.
2. Store field paths and schema version references.
3. Preserve old values in value history.
4. Hash value payloads after canonicalization.
5. Apply parameter-level editability based on lifecycle state.

### 8.4 IT Requirement Models

Required entities:

1. `ITRequirementSet`
2. `ITRequirementGroup`
3. `ITRequirementItem`
4. `ITRequirementEvidenceBinding`
5. `ITRequirementReviewFinding`

Implementation requirements:

| Field / behavior | Rule |
|---|---|
| Requirement group | Must support background, functional, architectural, performance, service, technology, integration, data migration, training, testing, support, security, reporting, and custom package-defined categories. |
| Requirement item code | Must be unique within a tender instance. |
| Requirement obligation text | Must be structured as a supplier/system obligation where applicable. |
| Compliance response type | Must support Yes/No, narrative, document reference, numeric value, table, and package-defined response types. |
| Mandatory flag | Must drive supplier response schema and evaluation conformance. |
| Evaluation binding | Must optionally map requirement to evaluation criterion/subcriterion. |
| Evidence binding | Must optionally map requirement to required bidder attachment/evidence. |
| Versioning | Changes after publication require addendum impact analysis. |

### 8.5 Implementation Schedule Models

Required entities:

1. `ITImplementationPlan`
2. `ITImplementationPhase`
3. `ITImplementationMilestone`
4. `ITAcceptanceEvent`
5. `ITMilestonePaymentBinding`

Implementation requirements:

1. Support one or more phases.
2. Support dependency relationships between milestones.
3. Support acceptance event binding.
4. Support location binding.
5. Support payment milestone binding where SCC or payment terms require it.
6. Prevent publication where required milestones are missing.
7. Generate contract carry-forward fields.

### 8.6 System Inventory and Price Schedule Models

Required entities:

1. `ITSystemInventoryTable`
2. `ITSystemInventoryItem`
3. `ITInventoryCostBinding`
4. `ITPriceScheduleProfile`
5. `ITPriceScheduleTable`
6. `ITPriceScheduleLineTemplate`
7. `ITRecurrentCostPeriod`

Implementation requirements:

1. Supply/install inventory and recurrent cost inventory must be distinguishable.
2. Inventory items must optionally map to price schedule line templates.
3. Quantities may be fixed by the Procuring Entity or supplier-proposed depending on package schema.
4. Recurrent cost periods must support warranty, support, maintenance, subscription, license, cloud hosting, and other package-defined categories.
5. Price configuration must support VAT handling, inclusive/exclusive treatment, currency, and fixed-price rules.

### 8.7 Evaluation Models

Required entities:

1. `ITEvaluationProfile`
2. `ITEvaluationStage`
3. `ITEvaluationCriterion`
4. `ITEvaluationSubcriterion`
5. `ITQualificationRequirement`
6. `ITEvaluationFormulaBinding`

Implementation requirements:

1. Support preliminary responsiveness stage.
2. Support pass/fail technical qualification stage.
3. Support scored technical stage.
4. Support financial evaluation stage.
5. Support post-qualification stage.
6. Support minimum pass mark validation.
7. Enforce scoring total rules, for example total scored points must equal configured total where package requires it.
8. Support requirement-to-evaluation binding.
9. Support generated evaluation workspace snapshot.

### 8.8 Forms, Evidence, and Schema Snapshot Models

Required entities:

1. `TenderFormActivation`
2. `TenderEvidenceRequirement`
3. `TenderSupplierSubmissionSchemaSnapshot`
4. `TenderEvaluationWorkspaceSchemaSnapshot`

Implementation requirements:

1. Form activation must be derived from master form schemas and tender-specific activation conditions.
2. Evidence requirements must be structured and stage-aware.
3. Supplier schema snapshot must be generated before publication.
4. Evaluation workspace snapshot must be generated before publication.
5. Snapshots must be immutable after publication.

### 8.9 SCC and Contract Carry-Forward Models

Required entities:

1. `TenderSCCProfile`
2. `ContractCarryForwardProfile`
3. `ContractCarryForwardItem`
4. `ContractAppendixBinding`

Implementation requirements:

1. SCC values must be controlled fields, not direct GCC edits.
2. Carry-forward items must map tender configuration into contract formation.
3. Contract appendices must bind to source configuration and successful supplier values where required.
4. Carry-forward package must have deterministic hash evidence.

### 8.10 Validation, Review, Preview, Publication, and Addendum Models

Required entities:

1. `WizardValidationRun`
2. `WizardValidationFinding`
3. `WizardReviewTrack`
4. `WizardReviewAssignment`
5. `WizardReviewDecision`
6. `WizardApprovalGateStatus`
7. `WizardPreviewBundle`
8. `WizardGeneratedArtifact`
9. `WizardHashEvidence`
10. `WizardPublicationBundle`
11. `WizardAddendumRequest`
12. `WizardAddendumImpactAnalysis`
13. `WizardAddendumAffectedObject`
14. `WizardAddendumBundle`

Implementation requirements:

1. Findings must include severity, category, field path, source rule, and blocking behavior.
2. Review decisions must be immutable after submission.
3. Preview bundles may be regenerated before publication.
4. Publication bundles are immutable.
5. Addendum impact analysis must identify affected sections, forms, supplier schema, evaluation schema, contract carry-forward, and render blocks.

---

## 9. Enumerations

Seed these enums before workflows and tests.

### 9.1 Wizard State Enum

```text
DRAFT
IN_CONFIGURATION
VALIDATION_FAILED
READY_FOR_REVIEW
UNDER_PROCUREMENT_REVIEW
UNDER_TECHNICAL_REVIEW
UNDER_LEGAL_REVIEW
RETURNED_FOR_CORRECTION
APPROVED_FOR_TENDER_BINDING
BOUND_TO_TENDER
READY_FOR_PUBLICATION
PUBLISHED
ADDENDUM_DRAFT
ADDENDUM_UNDER_REVIEW
ADDENDUM_APPROVED
ADDENDUM_PUBLISHED
SUPERSEDED_BY_ADDENDUM
CANCELLED
ARCHIVED
```

### 9.2 Step Status Enum

```text
NOT_STARTED
IN_PROGRESS
COMPLETE
FAILED_VALIDATION
NOT_APPLICABLE
LOCKED
READ_ONLY
```

### 9.3 Validation Severity Enum

```text
INFO
WARNING
ERROR
BLOCKER
```

### 9.4 Requirement Type Enum

```text
BACKGROUND
OBJECTIVE
SCOPE_TASK
FUNCTIONAL
ARCHITECTURAL
PERFORMANCE
SERVICE
TECHNOLOGY
SECURITY
INTEGRATION
DATA_MIGRATION
TRAINING
TESTING_ACCEPTANCE
SUPPORT_MAINTENANCE
REPORTING_ANALYTICS
SYSTEM_INVENTORY
CUSTOM
```

### 9.5 Price Table Type Enum

```text
GRAND_SUMMARY
SUPPLY_INSTALLATION_SUMMARY
SUPPLY_INSTALLATION_SUB_TABLE
RECURRENT_COST_SUMMARY
RECURRENT_COST_SUB_TABLE
COUNTRY_OF_ORIGIN
CUSTOM
```

### 9.6 Review Decision Enum

```text
APPROVE
RETURN_FOR_CORRECTION
REJECT
REQUEST_CLARIFICATION
WAIVE_WARNING
```

### 9.7 Audit Event Type Enum

```text
IT_WIZARD_INSTANCE_CREATED
IT_WIZARD_STEP_UPDATED
IT_WIZARD_PARAMETER_UPDATED
IT_WIZARD_REQUIREMENT_CREATED
IT_WIZARD_REQUIREMENT_UPDATED
IT_WIZARD_REQUIREMENT_DELETED
IT_WIZARD_IMPLEMENTATION_SCHEDULE_UPDATED
IT_WIZARD_INVENTORY_UPDATED
IT_WIZARD_PRICE_CONFIG_UPDATED
IT_WIZARD_EVALUATION_CONFIG_UPDATED
IT_WIZARD_FORM_ACTIVATION_UPDATED
IT_WIZARD_EVIDENCE_REQUIREMENT_UPDATED
IT_WIZARD_VALIDATION_RUN
IT_WIZARD_VALIDATION_FINDING_CREATED
IT_WIZARD_REVIEW_SUBMITTED
IT_WIZARD_REVIEW_DECISION_RECORDED
IT_WIZARD_STATE_TRANSITION_ATTEMPTED
IT_WIZARD_STATE_TRANSITION_COMPLETED
IT_WIZARD_PREVIEW_GENERATED
IT_WIZARD_PUBLICATION_BUNDLE_GENERATED
IT_WIZARD_PUBLICATION_COMPLETED
IT_WIZARD_ADDENDUM_IMPACT_CREATED
IT_WIZARD_ADDENDUM_PUBLISHED
IT_WIZARD_IMMUTABILITY_VIOLATION_BLOCKED
```

---

## 10. Permissions and Role Implementation

### 10.1 Permission Keys

Implement permission checks with these logical keys. Map them to the platform’s native RBAC system.

```text
it_wizard.instance.create
it_wizard.instance.read
it_wizard.instance.delete_draft
it_wizard.tds.update
it_wizard.scc.update
it_wizard.requirements.create
it_wizard.requirements.update
it_wizard.requirements.delete
it_wizard.schedule.update
it_wizard.inventory.update
it_wizard.price.update
it_wizard.evaluation.update
it_wizard.forms.update
it_wizard.evidence.update
it_wizard.validation.run
it_wizard.preview.generate
it_wizard.review.submit
it_wizard.review.procurement_decide
it_wizard.review.technical_decide
it_wizard.review.legal_decide
it_wizard.approval.finalize
it_wizard.tender.bind
it_wizard.publication.generate
it_wizard.addendum.create
it_wizard.addendum.review
it_wizard.addendum.publish
it_wizard.audit.read
```

### 10.2 Role Mapping

| Role | Minimum permissions |
|---|---|
| Procurement Officer | Create/read/update configuration, run validation, generate preview, submit for review. |
| Procurement Reviewer | Read, return for correction, approve procurement review, read audit. |
| Technical SME | Read, update technical requirements where assigned, technical review decision. |
| Legal Reviewer | Read, legal review decision, SCC legal review. |
| Approving Authority | Final approval, bind authorization where policy permits. |
| Tender Publisher | Generate publication bundle, publish after approval. |
| Audit Officer | Read-only access to configuration, validation, publication bundle, and audit. |
| System Administrator | Seed/admin support only; must not bypass workflow. |

### 10.3 Object-Level Permission Rules

1. Users may only access tender instances for their procuring entity unless they hold central oversight authority.
2. Users may not approve their own submitted review track where segregation policy forbids it.
3. Users may not edit fields in states that make the relevant section read-only.
4. Users may not edit published configuration values directly.
5. Users may not publish a bundle unless all required approval gates are passed.
6. System administrators may repair metadata through audited maintenance actions but must not modify legal configuration values outside governed workflows.

---

## 11. Workflow and State Transition Implementation

Implement state transitions through a single workflow service. Do not allow direct state-field updates from controllers or UI handlers.

### 11.1 Core Transition Table

| From | Action | To | Required checks |
|---|---|---|---|
| `DRAFT` | start configuration | `IN_CONFIGURATION` | Active STD version exists; steps generated. |
| `IN_CONFIGURATION` | run validation with blockers | `VALIDATION_FAILED` | Validation run completed. |
| `IN_CONFIGURATION` | run validation clean | `READY_FOR_REVIEW` | No blocker/error findings; required steps complete. |
| `VALIDATION_FAILED` | correct findings | `IN_CONFIGURATION` | Editable sections only. |
| `READY_FOR_REVIEW` | submit for review | `UNDER_PROCUREMENT_REVIEW` | Submitter permission; snapshot created. |
| `UNDER_PROCUREMENT_REVIEW` | approve procurement | `UNDER_TECHNICAL_REVIEW` or next configured track | Procurement approval recorded. |
| `UNDER_TECHNICAL_REVIEW` | approve technical | `UNDER_LEGAL_REVIEW` or next configured track | Technical approval recorded. |
| `UNDER_LEGAL_REVIEW` | approve legal | `APPROVED_FOR_TENDER_BINDING` | Legal approval recorded. |
| Any review state | return for correction | `RETURNED_FOR_CORRECTION` | Reason required. |
| `RETURNED_FOR_CORRECTION` | resume correction | `IN_CONFIGURATION` | Correction scope unlocked. |
| `APPROVED_FOR_TENDER_BINDING` | bind to tender | `BOUND_TO_TENDER` | Tender exists; no incompatible tender state. |
| `BOUND_TO_TENDER` | mark ready for publication | `READY_FOR_PUBLICATION` | Final validation clean. |
| `READY_FOR_PUBLICATION` | publish | `PUBLISHED` | Publication bundle hash generated; audit logged. |
| `PUBLISHED` | create addendum | `ADDENDUM_DRAFT` | Addendum request created. |
| `ADDENDUM_DRAFT` | submit addendum review | `ADDENDUM_UNDER_REVIEW` | Impact analysis complete. |
| `ADDENDUM_UNDER_REVIEW` | approve addendum | `ADDENDUM_APPROVED` | Addendum review gates passed. |
| `ADDENDUM_APPROVED` | publish addendum | `ADDENDUM_PUBLISHED` | Addendum bundle generated and hashed. |
| `PUBLISHED` or `ADDENDUM_PUBLISHED` | archive | `ARCHIVED` | Tender lifecycle allows archive. |

### 11.2 Workflow Service Guardrails

The workflow service must:

1. Load current state with row/object lock where supported.
2. Check actor permission.
3. Check object-level authorization.
4. Check required validation status.
5. Check required review decisions.
6. Check immutable-state restrictions.
7. Generate audit event for attempted transition.
8. Reject invalid transition with a typed error.
9. Generate audit event for completed transition.
10. Create a state transition event record.

---

## 12. Service Implementation Order

Implement services in this order.

### Stage 1 — Core Adapters and Utilities

1. `STDCoreAdapter`
2. `WizardAuditService`
3. `WizardHashService`
4. `WizardPermissionService`
5. `WizardStateGuardService`

Acceptance checks:

1. Adapter can retrieve active IT STD package metadata.
2. Hash service produces deterministic hashes for identical canonical payloads.
3. Permission service rejects unauthorized role/action combinations.
4. Audit service records events for create/update/transition actions.

### Stage 2 — Instance and Step Services

1. `WizardInstanceService`
2. `WizardStepService`
3. `WizardProgressService`
4. `WizardWorkflowService`

Acceptance checks:

1. A wizard instance can be created from an active IT STD package.
2. Step instances are generated from seed/package bindings.
3. `std_version_id` is immutable after creation.
4. State changes only occur through workflow service.

### Stage 3 — Profile and Parameter Services

1. `TenderIdentityService`
2. `ParticipationService`
3. `TenderDateService`
4. `SecurityInstrumentService`
5. `TDSService`
6. `SCCService`
7. `ParameterValueService`

Acceptance checks:

1. TDS and SCC values are stored as tender-specific parameter values.
2. Required fields are enforced.
3. Date-order validation works.
4. History records are created on updates.

### Stage 4 — Requirement Composer Services

1. `RequirementComposerService`
2. `RequirementImportService`
3. `RequirementEvidenceBindingService`
4. `RequirementEvaluationBindingService`

Acceptance checks:

1. Requirement groups can be created from package categories.
2. Requirement items can be created, updated, and soft-deleted before publication.
3. Requirement codes are unique per tender.
4. Requirement-to-evidence and requirement-to-evaluation bindings validate correctly.

### Stage 5 — Schedule, Inventory, and Price Services

1. `ImplementationScheduleService`
2. `AcceptanceEventService`
3. `MilestonePaymentBindingService`
4. `SystemInventoryService`
5. `PriceScheduleService`

Acceptance checks:

1. Phases and milestones can be configured.
2. Milestone dependencies cannot form cycles.
3. Inventory items can bind to price schedule line templates.
4. Recurrent cost periods validate.
5. Payment milestone totals comply with configured rules where applicable.

### Stage 6 — Evaluation, Forms, and Evidence Services

1. `EvaluationConfigService`
2. `QualificationRequirementService`
3. `FormActivationService`
4. `EvidenceRequirementService`
5. `SupplierSchemaSnapshotService`
6. `EvaluationWorkspaceSnapshotService`

Acceptance checks:

1. Evaluation stage sequence is generated.
2. Technical scoring totals validate.
3. Pass mark validates.
4. Mandatory evidence feeds supplier schema snapshot.
5. Evaluation workspace snapshot is deterministic.

### Stage 7 — Validation Service

1. `WizardValidationService`
2. `ValidationFindingService`
3. `ManualFindingResolutionService`

Acceptance checks:

1. Full validation runs across all configured areas.
2. Findings include severity, category, field path, rule source, and blocking behavior.
3. Blockers prevent submission for review.
4. Manual resolution requires permission and reason.

### Stage 8 — Preview, Publication, and Contract Carry-Forward Services

1. `WizardPreviewService`
2. `WizardRenderService`
3. `PublicationBundleService`
4. `ContractCarryForwardService`
5. `GeneratedArtifactService`

Acceptance checks:

1. Preview bundle can be generated before publication.
2. Publication bundle requires clean validation and required approvals.
3. Publication bundle is immutable after publication.
4. Supplier response schema, evaluation schema, and contract carry-forward package are generated and hashed.

### Stage 9 — Addendum Services

1. `AddendumRequestService`
2. `AddendumImpactAnalysisService`
3. `AddendumBundleService`
4. `AddendumPublicationService`

Acceptance checks:

1. Addendum impact analysis identifies affected sections, forms, requirements, price schedules, evaluation schemas, supplier schemas, and contract carry-forward items.
2. Addendum cannot be published without review approval.
3. Original publication bundle remains immutable.
4. Addendum bundle has separate hash evidence.

### Stage 10 — Calibration Fixture Service

1. `CalibrationFixtureService`
2. `CalibrationMappingService`
3. `CalibrationDeviationService`

Acceptance checks:

1. NSSF ERP fixture can be loaded in test/dev only.
2. Fixture data is clearly marked non-production.
3. Fixture validates the ability to represent a real ERP tender without altering master STD models.

---

## 13. API Implementation Checklist

Implement APIs from the API/UI/Service Contract. Use service-layer validation for every write.

### 13.1 Configuration Instance APIs

| Endpoint | Method | Service |
|---|---|---|
| `/configurations` | `POST` | `WizardInstanceService.create` |
| `/configurations/{id}` | `GET` | `WizardInstanceService.get_summary` |
| `/configurations` | `GET` | `WizardInstanceService.list` |
| `/configurations/{id}` | `DELETE` | `WizardInstanceService.delete_draft` |

Rules:

1. Delete allowed only in draft/unbound states.
2. Create requires active `KE-PPRA-IT` package version.
3. Summary must include state, step completion, validation status, approval gates, and bound tender ID where available.

### 13.2 TDS and SCC APIs

| Endpoint | Method | Service |
|---|---|---|
| `/configurations/{id}/tds` | `GET` | `TDSService.get_schema_and_values` |
| `/configurations/{id}/tds` | `PUT/PATCH` | `TDSService.update_values` |
| `/configurations/{id}/scc` | `GET` | `SCCService.get_schema_and_values` |
| `/configurations/{id}/scc` | `PUT/PATCH` | `SCCService.update_values` |

Rules:

1. Schema comes from STD Engine Core.
2. Values are tender-specific.
3. Updates must create history and audit events.
4. Updates in locked states must be rejected unless addendum workflow permits them.

### 13.3 Requirement Composer APIs

| Endpoint | Method | Service |
|---|---|---|
| `/configurations/{id}/requirements` | `GET` | `RequirementComposerService.get_set` |
| `/configurations/{id}/requirements/groups` | `POST` | `RequirementComposerService.create_group` |
| `/configurations/{id}/requirements/items` | `POST` | `RequirementComposerService.create_item` |
| `/configurations/{id}/requirements/items/import` | `POST` | `RequirementImportService.bulk_import` |
| `/configurations/{id}/requirements/items/{item_id}` | `PATCH` | `RequirementComposerService.update_item` |
| `/configurations/{id}/requirements/items/{item_id}` | `DELETE` | `RequirementComposerService.soft_delete_item` |

Rules:

1. Bulk import must validate before committing.
2. Requirement items must have stable codes.
3. Published requirements cannot be edited outside addendum workflow.

### 13.4 Implementation Schedule APIs

| Endpoint | Method | Service |
|---|---|---|
| `/configurations/{id}/implementation-schedule` | `GET` | `ImplementationScheduleService.get` |
| `/configurations/{id}/implementation-schedule/phases` | `POST` | `ImplementationScheduleService.add_phase` |
| `/configurations/{id}/implementation-schedule/milestones` | `POST` | `ImplementationScheduleService.add_milestone` |
| `/configurations/{id}/implementation-schedule/milestones/{milestone_id}` | `PATCH` | `ImplementationScheduleService.update_milestone` |
| `/configurations/{id}/implementation-schedule/acceptance-events` | `POST` | `AcceptanceEventService.create` |

Rules:

1. Milestone dates must respect phase dates.
2. Dependencies must not form cycles.
3. Required acceptance events must exist before publication.

### 13.5 Inventory and Price APIs

| Endpoint | Method | Service |
|---|---|---|
| `/configurations/{id}/system-inventory` | `GET` | `SystemInventoryService.get` |
| `/configurations/{id}/system-inventory/items` | `POST` | `SystemInventoryService.add_item` |
| `/configurations/{id}/system-inventory/items/{item_id}` | `PATCH` | `SystemInventoryService.update_item` |
| `/configurations/{id}/price-schedule` | `GET` | `PriceScheduleService.get_config` |
| `/configurations/{id}/price-schedule` | `PUT/PATCH` | `PriceScheduleService.update_config` |
| `/configurations/{id}/price-schedule/line-templates` | `POST` | `PriceScheduleService.add_line_template` |

Rules:

1. Inventory-price binding must validate.
2. Recurrent cost structures must be separately identifiable.
3. VAT/currency behavior must follow TDS/SCC/package configuration.

### 13.6 Evaluation, Forms, and Evidence APIs

| Endpoint | Method | Service |
|---|---|---|
| `/configurations/{id}/evaluation` | `GET` | `EvaluationConfigService.get` |
| `/configurations/{id}/evaluation` | `PUT/PATCH` | `EvaluationConfigService.update` |
| `/configurations/{id}/forms` | `GET` | `FormActivationService.get` |
| `/configurations/{id}/forms` | `PUT/PATCH` | `FormActivationService.update` |
| `/configurations/{id}/evidence-requirements` | `GET` | `EvidenceRequirementService.get` |
| `/configurations/{id}/evidence-requirements` | `PUT/PATCH` | `EvidenceRequirementService.update` |

Rules:

1. Evaluation scoring totals must be validated.
2. Mandatory forms and evidence cannot be disabled unless package rules permit it.
3. Form activation must feed supplier submission schema snapshot.

### 13.7 Validation, Preview, Review, Publication, Addendum, and Audit APIs

| Endpoint | Method | Service |
|---|---|---|
| `/configurations/{id}/validation-runs` | `POST` | `WizardValidationService.run_full_validation` |
| `/configurations/{id}/validation-findings` | `GET` | `ValidationFindingService.list` |
| `/configurations/{id}/validation-findings/{finding_id}/resolve` | `POST` | `ManualFindingResolutionService.resolve` |
| `/configurations/{id}/preview` | `POST` | `WizardPreviewService.generate` |
| `/configurations/{id}/preview/sections/{section_id}` | `POST` | `WizardPreviewService.generate_section` |
| `/configurations/{id}/review/submit` | `POST` | `WizardReviewService.submit` |
| `/configurations/{id}/review/return` | `POST` | `WizardReviewService.return_for_correction` |
| `/configurations/{id}/review/approve` | `POST` | `WizardReviewService.approve` |
| `/configurations/{id}/bind` | `POST` | `PublicationBundleService.bind_to_tender` |
| `/configurations/{id}/publication-bundle` | `POST` | `PublicationBundleService.generate` |
| `/configurations/{id}/addendum-impact` | `POST` | `AddendumImpactAnalysisService.create` |
| `/configurations/{id}/audit-events` | `GET` | `WizardAuditService.list_events` |

Rules:

1. Preview generation is allowed before approval but must be clearly marked preview.
2. Publication bundle generation requires approval and clean validation.
3. Addendum impact is required for post-publication changes.
4. Audit events must never expose internal secrets, credentials, or private file paths.

---

## 14. UI Implementation Plan

Build UI only after services and APIs pass basic integration tests.

### 14.1 Wizard Shell

Required components:

1. Header summary.
2. STD version badge.
3. Tender identity summary.
4. State badge.
5. Validation status badge.
6. Approval gate status badge.
7. Step rail.
8. Main content panel.
9. Validation panel.
10. Source trace panel.
11. Audit/action history panel.

### 14.2 Screen Build Order

Build screens in this order:

1. Wizard list and create configuration.
2. Wizard shell and step rail.
3. Tender Identity.
4. Procurement Method and Participation.
5. Dates, Clarifications, Opening, and Submission.
6. Security Instrument.
7. TDS generated field screen.
8. IT Requirements Composer.
9. Implementation Schedule.
10. System Inventory.
11. Price Schedule Setup.
12. Evaluation and Qualification.
13. Forms and Evidence.
14. SCC and Contract Parameters.
15. Validation screen.
16. Preview screen.
17. Review and Approval screen.
18. Publication Bundle screen.
19. Addendum Impact screen.
20. Audit and Hash Evidence screen.

### 14.3 Global UI Guardrails

1. Show source trace for STD-derived fields and sections.
2. Show whether a field is editable, locked, inherited, generated, or addendum-controlled.
3. Never display locked legal text in editable text fields.
4. Use explicit save/validate actions; do not silently publish or submit.
5. Require confirmation for state transitions.
6. Show blocker findings before submission, approval, and publication.
7. Show generated previews as watermarked preview until publication.
8. Show published bundle hash and generated timestamp.
9. For addenda, show original value, proposed value, affected sections, affected supplier schema, affected evaluation schema, and affected contract carry-forward.

### 14.4 UI Component Requirements

#### Requirement Table

Columns:

1. Code.
2. Category.
3. Requirement description.
4. Mandatory flag.
5. Compliance response type.
6. Evidence required.
7. Evaluation binding.
8. Status.
9. Last modified.
10. Actions.

#### Milestone Table

Columns:

1. Phase.
2. Milestone code.
3. Milestone name.
4. Deliverable.
5. Planned date/duration.
6. Dependency.
7. Acceptance event.
8. Payment binding.
9. Status.

#### Inventory Table

Columns:

1. Table type.
2. Item code.
3. Item description.
4. Quantity.
5. Unit.
6. Supplier response required.
7. Price schedule binding.
8. Recurrent cost flag.
9. Status.

#### Evaluation Criteria Editor

Required behavior:

1. Display stages.
2. Support pass/fail criteria.
3. Support scored criteria and subcriteria.
4. Calculate total points.
5. Validate minimum pass mark.
6. Bind requirements to criteria.
7. Preview generated evaluation workspace.

---

## 15. Validation Implementation

### 15.1 Validation Categories

Implement these categories:

```text
IDENTITY
PROCUREMENT_METHOD
DATES
SECURITY_INSTRUMENT
TDS
SCC
REQUIREMENTS
IMPLEMENTATION_SCHEDULE
SYSTEM_INVENTORY
PRICE_SCHEDULE
EVALUATION
FORMS
EVIDENCE
RENDERING
REVIEW_APPROVAL
TENDER_BINDING
PUBLICATION
ADDENDUM
CONTRACT_CARRY_FORWARD
```

### 15.2 Required Validation Rules

Minimum rules:

1. Tender name is required.
2. Tender number/reference is required.
3. Procuring Entity is required.
4. `std_version_id` is required and active at instance creation.
5. Alternative tender configuration must match package rules.
6. Clarification deadline must precede submission deadline.
7. Opening date/time must be at or after submission deadline according to configured policy.
8. Tender validity period must be positive and meet package minimum where applicable.
9. Currency must be allowed by package/TDS configuration.
10. Security instrument type and amount must satisfy package rules.
11. Mandatory TDS values must be complete.
12. Mandatory SCC values must be complete before contract carry-forward preview.
13. At least one requirement group must exist where package requires PE requirements.
14. Mandatory requirement items must have compliance response configuration.
15. Requirement codes must be unique.
16. Requirement evidence bindings must reference existing evidence records.
17. Requirement evaluation bindings must reference existing evaluation criteria.
18. Implementation schedule must include required phases/milestones.
19. Milestone dependencies must not be cyclic.
20. Acceptance events required by package must be present.
21. System inventory tables required by package must exist.
22. Inventory items bound to price schedules must reference valid line templates.
23. Price schedule tables required by package must exist.
24. VAT/currency handling must be configured.
25. Evaluation stages required by package must exist.
26. Technical scoring total must equal configured total.
27. Pass mark must not exceed total score.
28. Mandatory forms must be active.
29. Mandatory evidence requirements must be active.
30. Supplier submission schema snapshot must be generatable.
31. Evaluation workspace schema snapshot must be generatable.
32. Contract carry-forward package must be generatable before publication.
33. Preview render must complete without missing render blocks.
34. Required review gates must be approved before publication.
35. Publication bundle must have deterministic hash.
36. Post-publication change must produce addendum impact analysis.

### 15.3 Validation Output Requirements

Each finding must include:

| Field | Required |
|---|---:|
| `finding_id` | Yes |
| `tender_std_instance_id` | Yes |
| `validation_run_id` | Yes |
| `severity` | Yes |
| `category` | Yes |
| `code` | Yes |
| `message` | Yes |
| `field_path` | Conditional |
| `object_type` | Conditional |
| `object_id` | Conditional |
| `std_rule_id` | Conditional |
| `blocks_state_transition` | Yes |
| `blocks_publication` | Yes |
| `resolution_status` | Yes |
| `created_at` | Yes |

---

## 16. Rendering and Generated Output Implementation

### 16.1 Preview Bundle

Preview bundle generation must:

1. Load tender-specific configuration values.
2. Load render blocks from STD Engine Core.
3. Render sections using locked master content and tender-specific values.
4. Mark output as preview.
5. Create generated artifact records.
6. Create hash evidence.
7. Record audit event.

Preview bundles may be regenerated before publication.

### 16.2 Publication Bundle

Publication bundle generation must:

1. Require state `READY_FOR_PUBLICATION` or equivalent approved state.
2. Run final validation.
3. Reject if blockers/errors exist.
4. Generate all required tender documents.
5. Generate supplier submission schema snapshot.
6. Generate evaluation workspace schema snapshot.
7. Generate contract carry-forward package.
8. Hash every generated artifact.
9. Hash the full bundle manifest.
10. Mark bundle as immutable.
11. Record audit events.
12. Advance state to `PUBLISHED` only through workflow service.

### 16.3 Generated Output Types

Required generated outputs:

1. Tender document preview.
2. Tender document publication bundle.
3. Supplier response schema snapshot.
4. Evaluation workspace schema snapshot.
5. Contract carry-forward package.
6. Addendum impact report.
7. Addendum publication bundle.
8. Hash manifest.
9. Audit summary.

---

## 17. Addendum Implementation

### 17.1 Addendum Triggers

A post-publication change to any of the following must require addendum impact analysis:

1. TDS values.
2. SCC values.
3. IT requirements.
4. Implementation schedule.
5. System inventory.
6. Price schedule configuration.
7. Evaluation criteria.
8. Forms or evidence requirements.
9. Submission deadlines.
10. Clarification/opening data.
11. Contract carry-forward values.
12. Rendered tender document content.

### 17.2 Impact Analysis Must Identify

1. Changed object.
2. Old value hash.
3. New value hash.
4. Affected tender document sections.
5. Affected supplier response schema fields.
6. Affected evaluation workspace fields.
7. Affected price schedule lines.
8. Affected contract carry-forward items.
9. Required reviewer tracks.
10. Whether bidders must resubmit any portion.
11. Whether deadlines must be extended.
12. Generated addendum render blocks.

### 17.3 Addendum Publication Rules

1. Original publication bundle must remain immutable.
2. Addendum bundle must have its own hash evidence.
3. Addendum must reference the original publication bundle.
4. Addendum must not overwrite original generated artifacts.
5. Addendum must be visible to Supplier Portal and Evaluation Module handoff consumers.

---

## 18. Seed Data Implementation

Seed data must be idempotent. Re-running seed scripts must not duplicate records.

### 18.1 Seed Files

Create or load:

1. `roles.json`
2. `permissions.json`
3. `role_permission_matrix.json`
4. `wizard_steps_it.json`
5. `state_transitions.json`
6. `validation_categories.json`
7. `validation_rule_bindings.json`
8. `audit_event_types.json`
9. `smoke_contracts.json`
10. `calibration_fixtures/nssf_erp_mapping.json`

### 18.2 Wizard Step Seed

Minimum IT wizard steps:

```text
TENDER_IDENTITY
PROCUREMENT_METHOD_AND_PARTICIPATION
DATES_CLARIFICATIONS_AND_OPENING
SECURITY_INSTRUMENT
TDS_CONFIGURATION
BACKGROUND_OBJECTIVES_AND_SCOPE
IT_REQUIREMENTS_COMPOSER
IMPLEMENTATION_SCHEDULE
SYSTEM_INVENTORY
PRICE_SCHEDULE_SETUP
EVALUATION_AND_QUALIFICATION
FORMS_AND_EVIDENCE
SCC_AND_CONTRACT_PARAMETERS
VALIDATION
PREVIEW
REVIEW_AND_APPROVAL
TENDER_BINDING_AND_PUBLICATION
ADDENDUM_IMPACT
```

### 18.3 Smoke Contract Seed

Minimum smoke contracts:

1. Create IT wizard configuration from active IT STD version.
2. Locked STD text cannot be edited.
3. TDS date validation fails when clarification deadline is after submission deadline.
4. Technical scoring total must equal configured maximum.
5. Requirement-to-evaluation binding must reference an existing criterion.
6. Implementation milestone payment binding must reference an existing milestone and payment term.
7. Publication bundle immutability prevents direct edits after publication.
8. Addendum impact identifies affected sections and downstream schemas.
9. Supplier schema snapshot is deterministic.
10. Contract carry-forward package is deterministic.

---

## 19. Test Implementation Plan

### 19.1 Unit Tests

Required unit tests:

1. Hash canonicalization.
2. State transition guards.
3. Permission checks.
4. TDS value validation.
5. SCC value validation.
6. Requirement code uniqueness.
7. Requirement import prevalidation.
8. Milestone dependency cycle detection.
9. Inventory-price binding validation.
10. Evaluation scoring total validation.
11. Form activation validation.
12. Evidence requirement validation.
13. Addendum impact object diffing.

### 19.2 Integration Tests

Required integration tests:

1. Create wizard instance from active STD version.
2. Generate wizard steps.
3. Complete TDS profile.
4. Create requirement groups and items.
5. Configure implementation schedule.
6. Configure system inventory.
7. Configure price setup.
8. Configure evaluation criteria.
9. Generate supplier schema snapshot.
10. Generate evaluation workspace snapshot.
11. Run full validation.
12. Submit for review.
13. Approve review gates.
14. Bind to tender.
15. Generate publication bundle.
16. Create addendum impact analysis.

### 19.3 Permission Tests

Required permission tests:

1. Unauthorized user cannot create wizard instance.
2. Procurement Officer cannot approve own submission where segregation applies.
3. Technical SME cannot update SCC unless permission granted.
4. Legal Reviewer cannot edit requirements unless permission granted.
5. Audit Officer has read-only access.
6. System Administrator cannot bypass publication immutability.
7. Tender Publisher cannot publish without approvals.

### 19.4 Workflow Tests

Required workflow tests:

1. Invalid state transition is rejected.
2. Direct state update is rejected or impossible.
3. Validation blockers prevent review submission.
4. Review return unlocks correction scope only.
5. Approval gates advance state correctly.
6. Publication changes state to published only after immutable bundle creation.
7. Post-publication changes require addendum workflow.

### 19.5 Rendering and Publication Tests

Required tests:

1. Preview render uses locked master content and tender-specific values.
2. Preview can be regenerated before publication.
3. Publication bundle cannot be regenerated in place.
4. Generated artifact hashes are deterministic.
5. Bundle manifest hash changes when content changes before publication.
6. Published bundle hash remains stable after publication.

### 19.6 Calibration Tests

Required tests:

1. NSSF ERP tender fixture maps to tender identity/TDS fields.
2. NSSF ERP requirements map to requirement groups/items.
3. NSSF ERP phased implementation maps to implementation phases and milestones.
4. NSSF ERP technical scoring maps to evaluation criteria.
5. NSSF ERP price schedule deviation is detected as simplified pricing relative to full IT STD price schedule.
6. Fixture does not alter master STD package records.

---

## 20. Build Stages and Completion Criteria

### Stage A — Foundation

Deliver:

1. Models for instance, steps, profile shells, audit, and hash evidence.
2. Basic migrations.
3. Core adapter interface.
4. Seed roles/permissions/states.
5. Unit tests for permissions and state guards.

Completion criteria:

1. Tests pass.
2. Wizard instance can be created in `DRAFT`.
3. Steps are generated.
4. Direct state mutation is blocked.

### Stage B — Configuration Data

Deliver:

1. TDS/SCC services.
2. Parameter value persistence.
3. Tender profile services.
4. History and audit.
5. Validation for required profile fields.

Completion criteria:

1. TDS and SCC schemas can be read from Core adapter.
2. Values can be saved with history.
3. Invalid values produce findings.

### Stage C — Requirements, Schedule, Inventory, Price

Deliver:

1. Requirement composer.
2. Implementation schedule.
3. System inventory.
4. Price schedule setup.
5. Related APIs.
6. Related UI screens in basic form.

Completion criteria:

1. Requirement item and milestone smoke tests pass.
2. Inventory-price binding validates.
3. Price schedule setup is deterministic.

### Stage D — Evaluation, Forms, Evidence

Deliver:

1. Evaluation configuration.
2. Form activation.
3. Evidence requirements.
4. Supplier schema snapshot.
5. Evaluation workspace snapshot.

Completion criteria:

1. Technical scoring validation passes/fails correctly.
2. Mandatory evidence appears in supplier schema snapshot.
3. Snapshot hashes are deterministic.

### Stage E — Validation and Review

Deliver:

1. Full validation runner.
2. Validation findings UI.
3. Review submit/approve/return services.
4. Approval gate tracking.

Completion criteria:

1. Blockers prevent review submission.
2. Review decisions are audited.
3. Segregation-of-duties tests pass.

### Stage F — Preview, Binding, Publication

Deliver:

1. Preview generation.
2. Publication bundle generation.
3. Tender binding.
4. Hash manifest.
5. Immutable artifact behavior.

Completion criteria:

1. Publication bundle cannot be edited after publication.
2. Supplier/evaluation/contract handoff packages are generated.
3. Hash evidence is stored.

### Stage G — Addendum

Deliver:

1. Addendum request.
2. Impact analysis.
3. Addendum review.
4. Addendum publication bundle.

Completion criteria:

1. Post-publication edits are blocked outside addendum.
2. Addendum impact identifies affected downstream artifacts.
3. Addendum bundle is immutable and separately hashed.

### Stage H — Calibration and Hardening

Deliver:

1. NSSF ERP fixture loader for dev/test only.
2. Calibration mapping tests.
3. Performance checks.
4. Error handling review.
5. Security review.

Completion criteria:

1. Calibration fixture maps cleanly without master STD mutation.
2. All smoke contracts pass.
3. No activation/publish bypass remains.

---

## 21. Cursor Task Prompts

Use the following task prompts one at a time.

### Prompt 1 — Models and Migrations

```text
Implement Stage A for the IT Tender Configuration Wizard.
Create the instance, wizard step, progress snapshot, state transition event, audit, and hash evidence models.
Add migrations, enums, indexes, uniqueness constraints, and immutable std_version_id behavior.
Do not implement UI yet.
Add tests for creation, step generation, direct state mutation rejection, and deterministic hash evidence.
```

### Prompt 2 — Permissions and Workflow

```text
Implement the IT Tender Configuration Wizard permission and workflow services.
Use the roles, permission keys, and transition guards from the implementation pack.
All state transitions must go through the workflow service.
Add tests for unauthorized access, invalid transitions, segregation of duties, and audit events.
```

### Prompt 3 — TDS/SCC and Parameter Values

```text
Implement TDS, SCC, and tender profile configuration services for the IT Tender Configuration Wizard.
Read schemas from the STD Engine Core adapter.
Persist tender-specific values separately from master STD parameters.
Create value history and audit events for updates.
Add validation tests for required fields and date-order rules.
```

### Prompt 4 — Requirement Composer

```text
Implement the IT Requirements Composer.
Create requirement sets, groups, items, evidence bindings, evaluation bindings, and import prevalidation.
Do not hard-code ERP or Microsoft Dynamics behavior.
Use package-provided categories and response types.
Add tests for unique codes, mandatory flags, evidence binding, evaluation binding, and post-publication edit blocking.
```

### Prompt 5 — Schedule, Inventory, and Price

```text
Implement implementation schedule, acceptance events, system inventory, and price schedule setup.
Support phases, milestones, dependencies, payment bindings, inventory-price bindings, and recurrent cost periods.
Add tests for dependency cycle detection, required acceptance events, inventory binding, and recurrent cost validation.
```

### Prompt 6 — Evaluation, Forms, Evidence, and Snapshots

```text
Implement evaluation configuration, qualification requirements, form activation, evidence requirements, supplier schema snapshots, and evaluation workspace snapshots.
Ensure scoring totals and pass marks are validated.
Ensure mandatory forms and evidence feed the generated supplier schema.
Add deterministic snapshot hash tests.
```

### Prompt 7 — Full Validation Runner

```text
Implement the full wizard validation runner.
It must aggregate profile, TDS, SCC, requirements, schedule, inventory, price, evaluation, forms, evidence, renderability, review, publication, addendum, and contract carry-forward findings.
Findings must include severity, category, code, message, field path, object reference, source rule where available, and blocking flags.
Add tests showing blockers prevent review and publication.
```

### Prompt 8 — UI Screens

```text
Implement the IT Tender Configuration Wizard UI shell and step screens.
Use the WizardHeader, WizardStepRail, ValidationPanel, SourceTracePanel, RequirementTable, MilestoneTable, InventoryTable, PriceScheduleTable, EvaluationCriteriaEditor, PreviewViewer, ApprovalDecisionPanel, and HashEvidencePanel components.
Do not render locked STD legal text inside editable inputs.
Show source trace and field editability status.
```

### Prompt 9 — Preview and Publication

```text
Implement preview generation, tender binding, publication bundle generation, generated artifacts, supplier schema handoff, evaluation schema handoff, contract carry-forward package, and hash manifest.
Publication requires clean validation and approval gates.
Published bundles must be immutable.
Add tests for preview regeneration, publication immutability, and deterministic bundle hashes.
```

### Prompt 10 — Addendum

```text
Implement addendum request, addendum impact analysis, addendum review, addendum bundle generation, and addendum publication.
Post-publication changes must be blocked unless routed through addendum workflow.
Impact analysis must identify affected sections, supplier schema, evaluation schema, price schedule, and contract carry-forward items.
Add tests for addendum impact and immutable original bundle behavior.
```

### Prompt 11 — NSSF ERP Calibration Fixture

```text
Implement the NSSF ERP calibration fixture loader for development and test environments only.
Map the fixture into tender identity, TDS, requirements, phased implementation, evaluation criteria, price setup, SCC, and contract carry-forward records.
Mark all fixture records as non-production.
Add tests proving the fixture does not mutate master STD package records.
```

---

## 22. Data Integrity and Indexing Requirements

Minimum indexes and constraints:

| Entity | Constraint / index |
|---|---|
| `TenderSTDInstance` | Unique active instance per `tender_id` and `std_version_id` where business rules require it. |
| `TenderSTDInstance` | Index on `tenant_id`, `procuring_entity_id`, `state`, `std_version_id`. |
| `WizardStepInstance` | Unique `tender_std_instance_id + step_key`. |
| `TenderSTDParameterValue` | Unique current value by `tender_std_instance_id + parameter_key`. |
| `ITRequirementItem` | Unique active `tender_std_instance_id + requirement_code`. |
| `ITImplementationMilestone` | Unique active `tender_std_instance_id + milestone_code`. |
| `ITSystemInventoryItem` | Unique active `tender_std_instance_id + item_code`. |
| `ITEvaluationCriterion` | Unique active `tender_std_instance_id + criterion_code`. |
| `WizardValidationFinding` | Index on `tender_std_instance_id`, `validation_run_id`, `severity`, `category`, `resolution_status`. |
| `WizardGeneratedArtifact` | Index on `publication_bundle_id`, `artifact_type`, `hash_value`. |
| `WizardAuditEvent` | Index on `tenant_id`, `tender_std_instance_id`, `event_type`, `created_at`, `actor_id`. |

Soft delete policy:

1. Prefer status flags and tombstones for records that may be audited.
2. Do not physically delete records after review submission except through audited administrative maintenance.
3. Never physically delete records after publication.

---

## 23. Security and Audit Requirements

### 23.1 Security

1. Enforce server-side permissions for every API.
2. Never rely only on UI disabling.
3. Validate tenant/procuring-entity ownership on every request.
4. Protect generated artifacts using object-level access control.
5. Sanitize rich text or narrative fields used in render output.
6. Validate file references and evidence definitions.
7. Do not expose file system paths in API responses.
8. Do not expose internal exception traces to users.
9. Rate-limit bulk import and render endpoints where applicable.
10. Use idempotency keys for state transition and publication actions where platform supports it.

### 23.2 Audit

Every audit event must capture:

1. Event type.
2. Actor.
3. Role context.
4. Tenant/procuring entity.
5. Tender STD instance.
6. Object type and object ID.
7. Old value hash where applicable.
8. New value hash where applicable.
9. Timestamp.
10. Request ID.
11. IP/session/device metadata where available.
12. Success/failure status.
13. Failure reason where applicable.

---

## 24. Error Handling

Use typed errors. Minimum error codes:

```text
IT_WIZARD_STD_VERSION_NOT_ACTIVE
IT_WIZARD_INVALID_STATE_TRANSITION
IT_WIZARD_PERMISSION_DENIED
IT_WIZARD_OBJECT_NOT_FOUND
IT_WIZARD_VALIDATION_FAILED
IT_WIZARD_REQUIRED_FIELD_MISSING
IT_WIZARD_LOCKED_FIELD_EDIT_ATTEMPT
IT_WIZARD_IMMUTABLE_PUBLICATION_EDIT_ATTEMPT
IT_WIZARD_REVIEW_GATE_NOT_APPROVED
IT_WIZARD_PUBLICATION_BLOCKED
IT_WIZARD_ADDENDUM_REQUIRED
IT_WIZARD_ADDENDUM_IMPACT_INCOMPLETE
IT_WIZARD_SCHEMA_NOT_FOUND
IT_WIZARD_RENDER_FAILED
IT_WIZARD_HASH_MISMATCH
IT_WIZARD_CALIBRATION_FIXTURE_NOT_ALLOWED
```

Rules:

1. Errors returned to users must be actionable.
2. Internal logs may contain technical details but must not expose secrets.
3. Validation errors must identify field path and blocking behavior.
4. Workflow errors must identify current state and allowed actions where safe.

---

## 25. Performance Requirements

Minimum performance targets for normal tender sizes:

| Operation | Target |
|---|---:|
| Load wizard summary | Under 2 seconds |
| Load requirement composer with 500 requirements | Under 3 seconds with pagination/virtualization |
| Save one requirement item | Under 1 second excluding network latency |
| Run full validation for ordinary IT tender | Under 10 seconds or background job with progress |
| Generate preview bundle | Background job if over 10 seconds |
| Generate publication bundle | Background job with status and audit trail |
| Addendum impact analysis | Under 15 seconds or background job with progress |

Implementation notes:

1. Use pagination for requirement, inventory, and audit tables.
2. Use async/background jobs for rendering and large validations.
3. Cache read-only package schemas carefully; invalidate cache on package version changes.
4. Do not cache tender-specific editable values without cache invalidation.

---

## 26. Acceptance Criteria

The module is implementation-complete only when all of the following are true:

1. A wizard instance can be created from an active IT STD package version.
2. The wizard remains permanently bound to the selected `std_version_id`.
3. Wizard steps are generated from package/seed definitions.
4. TDS and SCC values are saved as tender-specific parameter values.
5. IT requirements can be structured, validated, bound to evidence, and bound to evaluation criteria.
6. Implementation schedule, acceptance events, inventory, and price setup can be configured.
7. Evaluation criteria can be configured and scoring totals validate.
8. Mandatory forms and evidence requirements generate supplier response schema snapshots.
9. Evaluation configuration generates evaluation workspace schema snapshots.
10. Full validation produces blocker/warning/info findings with field paths.
11. Blocker findings prevent review submission and publication.
12. Review and approval workflow enforces role permissions and segregation of duties.
13. Preview bundle generation works before publication.
14. Publication bundle generation requires clean validation and approval.
15. Published bundles are immutable.
16. Contract carry-forward package is generated and hashed.
17. Post-publication changes require addendum workflow.
18. Addendum impact identifies affected sections and downstream schemas.
19. All major actions generate audit events.
20. Hash evidence is deterministic.
21. NSSF ERP calibration fixture loads only in dev/test and does not mutate master STD records.
22. All smoke contracts pass.

---

## 27. Open Decisions Before Build Freeze

These decisions should be confirmed before final production build freeze. They do not block early implementation if sensible defaults are used and marked configurable.

| Decision | Default until confirmed |
|---|---|
| Exact backend framework conventions | Follow existing KenTender platform patterns. |
| Whether render jobs are synchronous or async | Use async for full bundle generation. |
| Whether review tracks are sequential or parallel | Support sequential by default; model should allow configured tracks. |
| Whether Technical SME may edit requirements or only review them | Allow assigned edit before review; read-only during review unless returned. |
| Whether tender binding happens before or after approval | Default: after approval, before publication. |
| Whether publication is a separate role from approval | Default: separate role. |
| Whether addendum review repeats all gates or only affected gates | Default: affected gates based on impact analysis. |
| Whether NSSF fixture is stored in repo or external test data | Default: repo test fixture, never production seed. |

---

## 28. Recommended Next Artifact

After this implementation pack, the next artifact should be:

**IT Tender Configuration Wizard — Sprint Backlog and Task Breakdown**

That backlog should split this pack into development tickets with:

1. Ticket ID.
2. User story.
3. Acceptance criteria.
4. Dependencies.
5. Test requirements.
6. Target files/services.
7. Risk notes.

