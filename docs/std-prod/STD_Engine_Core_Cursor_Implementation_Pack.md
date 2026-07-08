# STD Engine Core Module — Cursor Implementation Pack

**Project:** KenTender e-Procurement System  
**Module:** Standard Tender Document Engine Core  
**Document type:** Cursor Implementation Pack  
**Document status:** Draft for build execution  
**Version:** 0.1  
**Prepared date:** 2026-07-07  
**Preceding artifacts:**

1. `STD_Engine_Core_Module_Pre_PRD.md`
2. `STD_Engine_Core_Module_PRD.md`
3. `STD_Engine_Core_Domain_Model.md`
4. `STD_Engine_Core_Governance_Roles_Permissions_State_Model.md`
5. `STD_Engine_Core_Seed_Data_and_Smoke_Contracts.md`
6. `STD_Engine_Core_API_UI_Service_Contract.md`

---

## 1. Purpose

This implementation pack converts the approved STD Engine Core module artifacts into concrete build instructions suitable for Cursor-assisted development.

The pack is intentionally implementation-oriented. It defines the build order, logical file structure, service boundaries, model groups, migration rules, seed loading, tests, API handlers, UI surfaces, and non-negotiable guardrails.

The STD Engine Core must remain generalized. It must support multiple Standard Tender Document families and versions, including but not limited to:

1. Procurement of Information Technology.
2. Works.
3. Goods.
4. Consulting services.
5. Non-consulting services.
6. Future PPRA or authority-issued STD families.

The IT STD is the first full production seed. The WORKS PoC and NSSF ERP tender are calibration fixtures, not hard-coded models.

---

## 2. How to Use This Pack in Cursor

Use this document as the governing implementation prompt for the STD Engine Core module.

Recommended Cursor workflow:

1. Load this file into the repository context.
2. Load the preceding artifacts listed above into the repository context.
3. Ask Cursor to implement one build stage at a time.
4. Do not ask Cursor to implement the whole module in one pass.
5. After each stage, run tests and review generated code against the guardrails in this file.
6. Do not proceed to the next stage if immutable-state, approval, traceability, or audit tests are failing.

### 2.1 Master Cursor Instruction

Use the following instruction at the beginning of each implementation session:

```text
You are implementing the KenTender STD Engine Core module.

Follow the implementation pack exactly.
Do not hard-code behavior for the IT STD, WORKS STD, or any single tender.
Represent STD-specific behavior as data: template families, versions, sections, clauses, parameters, rules, forms, schemas, render profiles, evaluation schemas, contract schemas, and package records.

Do not store an official STD as one monolithic production JSON document.
JSON packages may be used only for import, export, seeding, source control, migration, and regression testing.

Enforce lifecycle governance, source traceability, immutable active template versions, immutable published tender bundles, addendum handling, validation blockers, smoke contracts, hash verification, and audit events.

Do not implement shortcuts that allow direct editing of active STD content or published tender bundles.
If a requested change conflicts with these controls, implement the governed workflow instead.
```

---

## 3. Framework Assumptions

This pack is framework-neutral but assumes the platform can provide equivalent capabilities for:

1. Relational persistence or document persistence with indexed fields.
2. JSON schema validation.
3. File storage.
4. Role-based and object-level authorization.
5. Workflow/state transitions.
6. Audit logging.
7. Background jobs.
8. Server-side rendering of documents.
9. API endpoints or service methods.
10. Automated tests.

Where the implementation platform is Frappe/ERPNext, tables may be implemented as DocTypes, service methods as whitelisted methods, and migrations/seeds as fixtures or patch scripts.

Where the implementation platform is Django, Laravel, NestJS, FastAPI, Rails, or another stack, map the same logical responsibilities to native models, migrations, services, controllers, policies, and tests.

---

## 4. Non-Negotiable Controls

These controls must be implemented before the module is considered complete.

| Control | Required behavior |
|---|---|
| Generalized engine | No STD-family-specific logic in core services. |
| Normalized storage | Production behavior must not depend on a single monolithic STD JSON blob. |
| Source traceability | Every material STD object must trace to source authority, source document, source location, or declared traceability mode. |
| Active version immutability | Active STD versions cannot be edited in place. |
| Published bundle immutability | Published generated tender bundles cannot be regenerated or modified in place. |
| Tender binding | A tender binds to exactly one active STD template version. |
| Addendum governance | Post-publication changes must use addendum impact workflow. |
| Approval workflow | Draft, review, approval, activation, supersession, and archive states must be enforced by guards. |
| Validation blockers | Blocker/error findings prevent approval, activation, generation, or publication where applicable. |
| Smoke contracts | Required smoke tests must pass before activation and before release. |
| Hashing | Source, content, schema, rule, render, package, snapshot, and bundle hashes must be deterministic. |
| Auditability | All state changes, approvals, imports, renders, validations, publications, and overrides must produce audit events. |
| Segregation of duties | The same actor must not perform conflicting approval actions where policy forbids it. |

---

## 5. Implementation Boundary

### 5.1 In Scope

Implement the STD Engine Core foundation:

1. STD authority, jurisdiction, category, enum, role, and permission records.
2. Template family and version management.
3. Source document registration, hash verification, extraction, and trace links.
4. Section, content block, clause, placeholder, parameter, option, and dependency models.
5. Rule definition, rule input, rule target, rule test case, validation run, and validation finding models.
6. Form schema, form section, field, option, activation condition, and evidence requirement models.
7. Requirement schema, price schedule schema, evaluation schema, contract schema, and render profile models.
8. Workflow definitions, states, transitions, guards, approvals, approval steps, and transition logs.
9. Tender STD instance, configuration values, requirement items, price line templates, and generated bundles.
10. Addendum request, impact, and delta models.
11. Import/export packages.
12. Smoke contracts and smoke test runner.
13. Audit events and audit snapshots.
14. Core API/service methods.
15. Administrative and tender-configuration UI shells.
16. Unit, integration, permission, workflow, and smoke tests.

### 5.2 Out of Scope for This Pack

Do not implement these items in the STD Engine Core build unless a later package explicitly instructs it:

1. Full IT STD extraction package.
2. Full IT tender wizard with all IT-specific screens.
3. Supplier portal submission UI.
4. Bid opening module.
5. Evaluation committee scoring UI.
6. Award workflow.
7. Contract management module beyond STD-generated contract schema and artifact handoff.
8. Full PDF styling parity with PPRA source documents.
9. OCR engine development.
10. External PPRA verification integrations.

The core module may expose service contracts for these later modules, but must not implement their full domain behavior yet.

---

## 6. Recommended Repository Structure

Adapt paths to the actual framework, but preserve these logical boundaries.

```text
kentender/
  std_engine/
    README.md
    models/
      base.py
      reference_models.py
      template_models.py
      source_models.py
      content_models.py
      parameter_models.py
      rule_models.py
      form_models.py
      evidence_models.py
      requirement_models.py
      price_models.py
      evaluation_models.py
      contract_models.py
      render_models.py
      workflow_models.py
      tender_models.py
      generated_models.py
      addendum_models.py
      package_models.py
      smoke_models.py
      audit_models.py
      rbac_models.py
    migrations/
      0001_reference_tables.*
      0002_template_and_source_tables.*
      0003_content_parameter_rule_tables.*
      0004_form_evidence_schema_tables.*
      0005_price_requirement_evaluation_contract_tables.*
      0006_render_workflow_tables.*
      0007_tender_generated_addendum_tables.*
      0008_package_smoke_audit_rbac_tables.*
      0009_indexes_constraints.*
    services/
      canonical_json_service.py
      hash_service.py
      audit_service.py
      permission_service.py
      source_document_service.py
      source_trace_service.py
      package_import_service.py
      package_export_service.py
      template_version_service.py
      workflow_service.py
      approval_service.py
      validation_service.py
      rule_engine_service.py
      form_schema_service.py
      requirement_schema_service.py
      price_schema_service.py
      evaluation_schema_service.py
      contract_schema_service.py
      render_service.py
      tender_binding_service.py
      tender_configuration_service.py
      generated_bundle_service.py
      addendum_service.py
      smoke_test_service.py
      seed_service.py
    api/
      families_api.py
      versions_api.py
      source_documents_api.py
      packages_api.py
      sections_api.py
      clauses_api.py
      parameters_api.py
      rules_api.py
      forms_api.py
      requirements_api.py
      price_schedules_api.py
      evaluations_api.py
      contracts_api.py
      render_api.py
      workflows_api.py
      approvals_api.py
      tender_instances_api.py
      bundles_api.py
      addenda_api.py
      smoke_api.py
      audit_api.py
    schemas/
      common.py
      manifest_schema.json
      import_package_schema.json
      rule_expression_schema.json
      form_schema_schema.json
      requirement_schema_schema.json
      price_schedule_schema_schema.json
      evaluation_schema_schema.json
      contract_schema_schema.json
      render_profile_schema.json
    seeds/
      reference_seed.json
      enum_seed.json
      state_seed.json
      transition_seed.json
      role_seed.json
      permission_seed.json
      role_permission_seed.json
      approval_track_seed.json
      audit_event_type_seed.json
      minimum_fixture_package.json
    tests/
      unit/
      integration/
      permissions/
      workflows/
      smoke/
      fixtures/
    ui/
      admin/
      tender_configuration/
      shared/
```

If using Frappe, map the logical model files to DocTypes and keep services in a separate Python service layer. Avoid putting complex governance logic directly inside UI scripts.

---

## 7. Build Stages

Implement in this order. Do not skip stages.

| Stage | Name | Primary output |
|---:|---|---|
| 0 | Repository and conventions setup | Module skeleton, naming conventions, base model/mixin. |
| 1 | Reference and RBAC foundations | Authorities, jurisdictions, categories, enums, roles, permissions. |
| 2 | Template and source foundations | Families, versions, source documents, hashes, source trace. |
| 3 | STD content model | Sections, content blocks, clauses, placeholders, parameters. |
| 4 | Rule and validation engine | Rule definitions, test cases, validation runs/findings. |
| 5 | Schema models | Forms, evidence, requirements, price, evaluation, contract, render. |
| 6 | Workflow and approval engine | State machines, transitions, guards, approvals, SOD. |
| 7 | Tender binding and configuration | Tender STD instance, configuration values, requirement/price instance records. |
| 8 | Generation and immutability | Snapshotting, rendering, generated bundles, artifact hashes. |
| 9 | Addendum impact workflow | Post-publication change governance. |
| 10 | Import/export package system | Manifest validation, import, export, diff, rollback-safe apply. |
| 11 | Seed data and smoke contracts | Idempotent seed loading and core smoke tests. |
| 12 | API/service contracts | Endpoint/controller/service implementation. |
| 13 | UI shells | Admin and tender configuration screens. |
| 14 | Test hardening | Permission, state, immutable, trace, addendum, render tests. |
| 15 | Release readiness | Migration verification, security review, performance review, documentation. |

---

## 8. Stage 0 — Repository and Conventions Setup

### 8.1 Tasks

1. Create the module folder structure.
2. Create a `README.md` explaining STD Engine Core purpose and non-negotiable controls.
3. Create shared model mixins or base fields:
   - `id`.
   - `created_at`.
   - `created_by`.
   - `updated_at`.
   - `updated_by`.
   - `is_deleted`.
   - `deleted_at`.
   - `deleted_by`.
   - `record_version`.
   - `tenant_id` where applicable.
4. Create shared constants for:
   - Status values.
   - Severity values.
   - Mutability types.
   - Lifecycle stages.
   - Trace types.
   - Bundle types.
5. Create shared exception classes:
   - `ValidationError`.
   - `PermissionDeniedError`.
   - `WorkflowTransitionError`.
   - `ImmutableObjectError`.
   - `HashMismatchError`.
   - `SourceTraceMissingError`.
   - `PackageValidationError`.
6. Create shared response envelope helpers.
7. Create shared test fixture utilities.

### 8.2 Acceptance Criteria

1. Module imports cleanly.
2. Tests can be discovered.
3. Base fields are consistently available.
4. Soft delete does not bypass immutability or audit requirements.
5. Exceptions return structured error payloads through APIs.

---

## 9. Stage 1 — Reference and RBAC Foundations

### 9.1 Models to Implement

Implement the following model group first:

| Logical table | Purpose |
|---|---|
| `std_authority` | STD issuing authority. |
| `std_jurisdiction` | Jurisdiction/legal environment. |
| `std_procurement_category` | Procurement category taxonomy. |
| `std_enum_set` | Controlled enum families. |
| `std_enum_value` | Controlled enum values. |
| `std_role` | STD module roles. |
| `std_permission` | Permission actions. |
| `std_role_permission` | Role-permission mapping. |

### 9.2 Required Constraints

1. Authority code must be unique.
2. Jurisdiction code must be unique.
3. Procurement category code must be unique.
4. Enum set code must be unique.
5. Enum value code must be unique within an enum set.
6. Permission code must be unique.
7. Role code must be unique.
8. Role-permission mappings must be unique by `(role_id, permission_id)`.

### 9.3 Required Services

Implement:

1. `seed_service.load_reference_data()`.
2. `permission_service.has_permission(user, permission_code, object=None)`.
3. `permission_service.assert_permission(user, permission_code, object=None)`.
4. `permission_service.apply_object_scope(user, query, object_type)`.

### 9.4 Required Seed Records

Seed at minimum:

1. `PPRA_KE` authority.
2. `KE_NATIONAL` jurisdiction.
3. Procurement categories:
   - `WORKS`.
   - `GOODS`.
   - `IT`.
   - `CONSULTING_SERVICES`.
   - `NON_CONSULTING_SERVICES`.
   - `OTHER`.
4. Mutability types:
   - `LOCKED`.
   - `PARAMETERIZED`.
   - `CONTROLLED_CONFIGURABLE`.
   - `PE_AUTHORED_CONTROLLED`.
   - `BIDDER_COMPLETED`.
   - `SYSTEM_GENERATED`.
   - `REFERENCE_ONLY`.
5. Severity values:
   - `INFO`.
   - `WARNING`.
   - `ERROR`.
   - `BLOCKER`.
6. Roles from the governance artifact.
7. Permissions from the seed artifact.

### 9.5 Tests

1. Seed data is idempotent.
2. Duplicate codes are rejected.
3. Permission checks fail closed.
4. Object-level scope cannot be bypassed by direct service calls.

---

## 10. Stage 2 — Template and Source Foundations

### 10.1 Models to Implement

| Logical table | Purpose |
|---|---|
| `std_template_family` | STD family, e.g. Information Technology or Works. |
| `std_template_version` | Specific STD version. |
| `std_template_version_metadata` | Version metadata and attributes. |
| `std_src_document` | Registered source document. |
| `std_src_document_version` | Source file version and hash. |
| `std_src_location` | Page/section/paragraph/table location. |
| `std_src_extract` | Extracted source text or structured extract. |
| `std_source_trace_link` | Trace link from source to material object. |

### 10.2 Services

Implement:

1. `source_document_service.register_source_document()`.
2. `source_document_service.attach_source_file()`.
3. `source_document_service.compute_source_file_hash()`.
4. `source_document_service.verify_source_document_hash()`.
5. `source_trace_service.create_trace_link()`.
6. `source_trace_service.assert_traceability_required()`.
7. `template_version_service.create_family()`.
8. `template_version_service.create_version()`.
9. `template_version_service.compute_version_hash()`.
10. `template_version_service.assert_version_editable()`.

### 10.3 Hash Rules

1. Use SHA-256 unless platform policy requires a stronger compatible hash.
2. Hash raw source file bytes for `source_file_hash`.
3. Hash normalized extracted text for `source_text_hash`.
4. Hash canonical JSON for structured metadata and schema hashes.
5. Never use non-deterministic JSON serialization for any legally material hash.

### 10.4 Source Trace Rules

A material object must have one of these trace modes:

1. `DIRECT_SOURCE_LOCATION` — linked to page/section/paragraph/table in source document.
2. `DERIVED_FROM_SOURCE` — derived from one or more source locations.
3. `SYSTEM_GENERATED` — produced by the system according to a traceable rule/schema.
4. `ADMIN_DECLARED` — allowed only with reason and approval.
5. `NOT_APPLICABLE` — allowed only for technical/system metadata, never legal clauses.

### 10.5 Tests

1. Source document cannot become verified without a file hash.
2. Verified source document cannot have its hash changed in place.
3. Template version cannot activate without verified source.
4. Material objects cannot activate without trace links or approved trace exemption.

---

## 11. Stage 3 — STD Content Model

### 11.1 Models to Implement

| Logical table | Purpose |
|---|---|
| `std_tpl_section` | Hierarchical STD sections. |
| `std_tpl_content_block` | Ordered content blocks. |
| `std_tpl_clause` | Legal or procedural clauses. |
| `std_tpl_clause_placeholder` | Placeholder tokens inside clauses. |
| `std_tpl_parameter_group` | Groups of configurable fields. |
| `std_tpl_parameter` | Configurable tender/template parameter. |
| `std_tpl_parameter_option` | Controlled options. |
| `std_tpl_parameter_dependency` | Conditional relationships between parameters. |

### 11.2 Required Content Rules

1. Sections must form an acyclic tree.
2. Sibling sections must have deterministic order.
3. Locked sections cannot expose editable free text.
4. Parameterized locked sections may expose placeholders, not direct clause editing.
5. Clause placeholders must map to defined parameters or generated values.
6. Parameter dependencies must not create circular activation chains.
7. Deleted or inactive parameters cannot remain referenced by active placeholders.

### 11.3 Services

Implement:

1. `template_version_service.create_section()`.
2. `template_version_service.reorder_sections()`.
3. `template_version_service.create_content_block()`.
4. `template_version_service.create_clause()`.
5. `template_version_service.update_clause()` with immutability checks.
6. `template_version_service.create_placeholder()`.
7. `template_version_service.create_parameter_group()`.
8. `template_version_service.create_parameter()`.
9. `template_version_service.create_parameter_dependency()`.
10. `template_version_service.validate_section_tree()`.
11. `template_version_service.validate_placeholder_bindings()`.

### 11.4 Tests

1. Active template clauses cannot be edited.
2. Locked section cannot be changed by a tender configurator.
3. Placeholder without parameter fails validation.
4. Circular parameter dependency fails validation.
5. Section ordering is deterministic across export/import.

---

## 12. Stage 4 — Rule and Validation Engine

### 12.1 Models to Implement

| Logical table | Purpose |
|---|---|
| `std_rule_definition` | Declarative rule. |
| `std_rule_target` | Object/field target of rule. |
| `std_rule_input` | Rule input binding. |
| `std_rule_test_case` | Expected rule behavior. |
| `std_validation_run` | Execution of validation. |
| `std_validation_finding` | Finding from validation. |

### 12.2 Rule Types

Support at minimum:

1. `REQUIRED_FIELD`.
2. `DATE_ORDER`.
3. `NUMERIC_RANGE`.
4. `ENUM_ALLOWED`.
5. `CONDITIONAL_REQUIRED`.
6. `MUTUAL_EXCLUSION`.
7. `CALCULATION`.
8. `REFERENCE_INTEGRITY`.
9. `TRACEABILITY_REQUIRED`.
10. `IMMUTABILITY_GUARD`.
11. `STATE_TRANSITION_GUARD`.
12. `RENDER_COMPLETENESS`.
13. `CUSTOM_EXPRESSION`.

### 12.3 Expression Safety

If custom expressions are supported:

1. Use a constrained expression language.
2. Do not allow arbitrary code execution.
3. Whitelist functions.
4. Validate expression AST before saving.
5. Record expression language version.
6. Require test cases for production blocker rules.

### 12.4 Services

Implement:

1. `rule_engine_service.validate_rule_definition()`.
2. `rule_engine_service.execute_rule()`.
3. `rule_engine_service.execute_rule_test_case()`.
4. `validation_service.run_template_validation()`.
5. `validation_service.run_tender_instance_validation()`.
6. `validation_service.run_addendum_validation()`.
7. `validation_service.create_finding()`.
8. `validation_service.resolve_finding()`.
9. `validation_service.assert_no_blockers()`.

### 12.5 Tests

1. Required field rule produces blocker when missing.
2. Date-order rule detects invalid tender timelines.
3. Conditional rule activates only when dependency is true.
4. Rule with invalid expression is rejected.
5. Blocker finding prevents activation/publication.
6. Resolved finding retains audit history.

---

## 13. Stage 5 — Schema Models

### 13.1 Form and Evidence Models

Implement:

| Logical table | Purpose |
|---|---|
| `std_form_schema` | Form definition. |
| `std_form_section` | Form section grouping. |
| `std_form_field` | Field definition. |
| `std_form_field_option` | Field select option. |
| `std_form_activation_condition` | Conditional form activation. |
| `std_evidence_requirement` | Required supporting document. |
| `std_evidence_verification_schema` | Verification rules for evidence. |

Required behavior:

1. Form schemas are versioned through STD version.
2. Bidder-completed fields cannot be edited by PE after publication.
3. Evidence requirement criticality affects responsiveness/evaluation workflows.
4. Form activation conditions must be deterministic.
5. Forms must support respondent type: PE, bidder, successful bidder, evaluator, system.

### 13.2 Requirement Models

Implement:

| Logical table | Purpose |
|---|---|
| `std_req_schema` | Requirement schema family. |
| `std_req_group_schema` | Requirement grouping. |
| `std_req_field_definition` | Requirement item fields. |
| `std_req_item_template` | Predefined requirement row template. |

Required behavior:

1. Requirement schemas must support multiple STD families.
2. Requirement items must support criticality and conformance response type.
3. IT-specific categories such as functional, architectural, performance, service, technology, implementation, testing, and support must be data values, not core code branches.

### 13.3 Price Models

Implement:

| Logical table | Purpose |
|---|---|
| `std_price_schema` | Price schedule schema. |
| `std_price_table_schema` | Price table definition. |
| `std_price_column_schema` | Price table column definition. |
| `std_price_calculation_rule` | Calculation and rollup rules. |

Required behavior:

1. Support price schedule types such as BoQ, supply/install, recurrent cost, lump sum, rate card, and milestone payment schedule.
2. Do not hard-code Works BoQ or IT recurrent costs.
3. Use schema records and calculation rules.
4. Financial rollups must be deterministic and testable.

### 13.4 Evaluation Models

Implement:

| Logical table | Purpose |
|---|---|
| `std_eval_schema` | Evaluation schema. |
| `std_eval_stage` | Evaluation stages. |
| `std_eval_criterion` | Criteria/subcriteria. |
| `std_eval_score_scale` | Score scale and scoring rules. |

Required behavior:

1. Support pass/fail criteria.
2. Support weighted scoring criteria.
3. Support minimum pass marks.
4. Support financial evaluation rule references.
5. Support conformance-linked evaluation.
6. Support post-qualification criteria.

### 13.5 Contract Models

Implement:

| Logical table | Purpose |
|---|---|
| `std_contract_schema` | Contract output schema. |
| `std_contract_artifact_schema` | Contract artifact definition. |
| `std_contract_carry_forward_mapping` | Mapping from tender/award data to contract. |

Required behavior:

1. Contract forms are generated from approved tender and award data.
2. Carry-forward fields must be explicit.
3. Contract artifact generation must preserve source STD version.

### 13.6 Render Models

Implement:

| Logical table | Purpose |
|---|---|
| `std_render_profile` | Output profile. |
| `std_render_block` | Renderable block. |
| `std_render_placeholder` | Render placeholder. |

Required behavior:

1. Render profiles must specify output type.
2. Render blocks must be ordered deterministically.
3. Render placeholders must resolve from parameters, rules, tender configuration, generated values, or carry-forward data.
4. Missing required placeholder values cause blocker findings.

### 13.7 Tests

1. Form schema with missing required field metadata fails validation.
2. Evidence requirement without target form/field fails validation.
3. Price schema rollup returns expected total.
4. Evaluation stage order is deterministic.
5. Contract carry-forward mapping rejects missing source field.
6. Render profile rejects unresolved required placeholders.

---

## 14. Stage 6 — Workflow and Approval Engine

### 14.1 Models to Implement

| Logical table | Purpose |
|---|---|
| `std_workflow_definition` | Workflow definition. |
| `std_workflow_state` | States. |
| `std_workflow_transition` | Allowed transitions. |
| `std_transition_guard` | Guard condition. |
| `std_approval_request` | Approval request. |
| `std_approval_step` | Required approval step. |
| `std_approval_event` | Approval event. |
| `std_template_version_transition_log` | Version transition log. |
| `std_tender_instance_transition_log` | Tender STD transition log. |

### 14.2 Template Version States

Implement these states exactly as controlled values:

```text
Draft
Structuring
Internal Review
Legal Review
Procurement Standards Review
Technical Schema Review
Review Changes Required
Ready for Approval
Approved
Active
Suspended
Superseded
Archived
Rejected
```

### 14.3 Template Version Main Path

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

### 14.4 Tender STD Instance States

Implement these states exactly as controlled values:

```text
Not Started
Bound to STD Version
In Configuration
Validation Failed
Ready for Review
Procurement Review
Technical Review
Legal Review
Finance/Budget Review
Changes Required
Approved for Generation
Generated for Approval
Approved for Publication
Published
Addendum Required
Closed
Cancelled
```

### 14.5 Generated Bundle States

Implement these states exactly as controlled values:

```text
Preview Requested
Preview Generated
Preview Failed
Final Generation Requested
Final Generated
Final Generation Failed
Under Approval
Approved
Published
Superseded by Addendum
Voided Before Publication
```

### 14.6 Addendum Impact States

Implement these states exactly as controlled values:

```text
Addendum Requested
Impact Analysis Draft
Impact Analysis Complete
Validation Failed
Ready for Review
Under Review
Changes Required
Approved
Published
Withdrawn
Rejected
```

### 14.7 Services

Implement:

1. `workflow_service.get_available_transitions()`.
2. `workflow_service.assert_transition_allowed()`.
3. `workflow_service.execute_transition()`.
4. `workflow_service.evaluate_guards()`.
5. `approval_service.create_approval_request()`.
6. `approval_service.assign_steps()`.
7. `approval_service.record_approval()`.
8. `approval_service.record_rejection_or_changes_required()`.
9. `approval_service.assert_required_approvals_complete()`.
10. `approval_service.assert_segregation_of_duties()`.

### 14.8 Template Activation Guards

Implement all guards from the governance artifact. At minimum:

1. Version belongs to active STD family.
2. Source document verified.
3. Required section hierarchy complete.
4. Locked sections have locked mutability classification.
5. Configurable sections expose parameters instead of free editing where required.
6. Every material object has source traceability or approved traceability mode.
7. Required legal review approved.
8. Required procurement standards review approved.
9. Required technical schema review approved.
10. No unresolved blocker/error validation findings.
11. Smoke tests pass.
12. Version hash computed.
13. Segregation of duties checks pass.
14. Supersession policy declared when activating replacement.

### 14.9 Tests

1. User cannot jump from Draft to Active.
2. Active version cannot be edited.
3. Activation fails without verified source.
4. Activation fails without required reviews.
5. Activation fails if smoke tests fail.
6. Segregation-of-duties violation blocks approval.
7. Transition logs are written for every transition.

---

## 15. Stage 7 — Tender Binding and Configuration

### 15.1 Models to Implement

| Logical table | Purpose |
|---|---|
| `std_tender_instance` | Tender binding to STD version. |
| `std_tender_config_value` | Tender-specific parameter value. |
| `std_tender_requirement_item` | Tender-specific requirement item. |
| `std_tender_price_line_template` | Tender-specific price line template. |

### 15.2 Services

Implement:

1. `tender_binding_service.bind_tender_to_std_version()`.
2. `tender_binding_service.assert_version_is_active()`.
3. `tender_binding_service.assert_tender_not_already_bound()`.
4. `tender_configuration_service.set_config_value()`.
5. `tender_configuration_service.bulk_set_config_values()`.
6. `tender_configuration_service.create_requirement_item()`.
7. `tender_configuration_service.update_requirement_item()`.
8. `tender_configuration_service.create_price_line_template()`.
9. `tender_configuration_service.validate_configuration_completeness()`.
10. `tender_configuration_service.create_configuration_snapshot()`.

### 15.3 Binding Rules

1. A tender may bind only to an Active STD version.
2. A tender may not bind to Suspended, Superseded, Archived, Draft, or Approved-but-not-Active versions.
3. Binding records must preserve version ID, version code, version hash, family ID, and bind timestamp.
4. After tender publication, configuration values become immutable.
5. Changes after publication must create addendum impact records.

### 15.4 Tests

1. Binding to inactive version fails.
2. Binding stores version hash.
3. Required parameter missing causes validation blocker.
4. Config value cannot be edited after publication.
5. Requirement item update after publication routes to addendum workflow.

---

## 16. Stage 8 — Generation and Immutability

### 16.1 Models to Implement

| Logical table | Purpose |
|---|---|
| `std_gen_bundle` | Generated bundle record. |
| `std_gen_artifact` | File/artifact inside bundle. |
| `std_gen_section_snapshot` | Section snapshot at generation. |

### 16.2 Services

Implement:

1. `render_service.request_preview()`.
2. `render_service.render_preview()`.
3. `render_service.request_final_generation()`.
4. `render_service.render_final_bundle()`.
5. `render_service.resolve_placeholders()`.
6. `render_service.render_artifacts()`.
7. `render_service.compute_artifact_hash()`.
8. `generated_bundle_service.create_bundle()`.
9. `generated_bundle_service.create_section_snapshots()`.
10. `generated_bundle_service.approve_bundle()`.
11. `generated_bundle_service.publish_bundle()`.
12. `generated_bundle_service.assert_bundle_immutable()`.

### 16.3 Snapshot Requirements

A final generated bundle must include:

1. Tender STD instance ID.
2. STD family ID and code.
3. STD version ID and code.
4. STD version hash.
5. Render profile ID and hash.
6. Configuration snapshot hash.
7. Generated artifact hashes.
8. Section snapshots.
9. Generation timestamp.
10. Actor/service account.

### 16.4 Tests

1. Preview bundle cannot be published.
2. Final bundle cannot generate from unapproved configuration.
3. Published bundle cannot be changed.
4. Re-rendering the same snapshot produces same hash.
5. Missing render placeholder causes blocker.
6. Published artifact remains retrievable after addendum supersession.

---

## 17. Stage 9 — Addendum Impact Workflow

### 17.1 Models to Implement

| Logical table | Purpose |
|---|---|
| `std_addendum_record` | Addendum request/master record. |
| `std_addendum_impact` | Impact category and affected objects. |
| `std_addendum_delta` | Specific delta details. |

### 17.2 Services

Implement:

1. `addendum_service.request_addendum()`.
2. `addendum_service.start_impact_analysis()`.
3. `addendum_service.identify_impacted_objects()`.
4. `addendum_service.create_delta()`.
5. `addendum_service.run_addendum_validation()`.
6. `addendum_service.submit_for_review()`.
7. `addendum_service.approve_addendum()`.
8. `addendum_service.publish_addendum()`.
9. `addendum_service.mark_prior_bundle_superseded()`.

### 17.3 Impact Categories

Support at minimum:

1. `DEADLINE_IMPACT`.
2. `ELIGIBILITY_IMPACT`.
3. `TECHNICAL_REQUIREMENT_IMPACT`.
4. `PRICE_SCHEDULE_IMPACT`.
5. `EVALUATION_IMPACT`.
6. `CONTRACT_SCC_IMPACT`.
7. `FORM_IMPACT`.
8. `RENDER_ONLY_IMPACT`.
9. `OTHER_SUBSTANTIVE_IMPACT`.

### 17.4 Tests

1. Published tender change creates addendum request, not direct edit.
2. Impact analysis identifies affected sections/forms/rules/render blocks.
3. Evaluation impact requires review.
4. Published addendum marks prior bundle as superseded by addendum.
5. Addendum artifacts are hashed and audit logged.

---

## 18. Stage 10 — Import/Export Package System

### 18.1 Models to Implement

| Logical table | Purpose |
|---|---|
| `std_pkg_import` | Import job/package record. |
| `std_pkg_import_item` | Imported component item. |
| `std_pkg_export` | Export package record. |

### 18.2 Package Manifest

A package manifest must include at minimum:

```json
{
  "package_code": "KE-PPRA-IT-2022-04",
  "package_version": "0.1.0",
  "authority_code": "PPRA_KE",
  "jurisdiction_code": "KE_NATIONAL",
  "template_family_code": "KE-PPRA-IT",
  "template_version_code": "KE-PPRA-IT-2022-04",
  "source_documents": [],
  "modules": [],
  "package_hash": "sha256:...",
  "created_at": "2026-07-07T00:00:00+03:00"
}
```

### 18.3 Required Package Modules

Support these package modules:

1. `manifest.json`.
2. `source_trace.json`.
3. `sections.json`.
4. `clauses.json`.
5. `parameters.json`.
6. `rules.json`.
7. `forms.json`.
8. `form_fields.json`.
9. `evidence_requirements.json`.
10. `requirements_schema.json`.
11. `price_schedule_schema.json`.
12. `evaluation_schema.json`.
13. `contract_schema.json`.
14. `render_blocks.json`.
15. `smoke_tests.json`.

### 18.4 Services

Implement:

1. `package_import_service.upload_package()`.
2. `package_import_service.validate_manifest()`.
3. `package_import_service.validate_package_modules()`.
4. `package_import_service.validate_source_trace()`.
5. `package_import_service.diff_against_existing_version()`.
6. `package_import_service.apply_package_to_draft()`.
7. `package_import_service.rollback_failed_apply()`.
8. `package_export_service.export_template_version()`.
9. `package_export_service.compute_package_hash()`.

### 18.5 Tests

1. Package without manifest fails.
2. Package with hash mismatch fails.
3. Package with missing required module fails.
4. Package with invalid source trace fails.
5. Package import into active version fails.
6. Export/import round trip preserves canonical hashes.

---

## 19. Stage 11 — Seed Data and Smoke Contracts

### 19.1 Smoke Contract Models

| Logical table | Purpose |
|---|---|
| `std_smoke_contract` | Smoke contract definition. |
| `std_smoke_test_case` | Smoke test case. |
| `std_smoke_run` | Execution run. |
| `std_smoke_run_result` | Individual result. |

### 19.2 Required Smoke Contracts

Implement at minimum:

1. `SC-001 Seed Data Idempotency`.
2. `SC-002 Source Document Must Be Hashed Before Verification`.
3. `SC-003 Import Package Requires Valid Manifest`.
4. `SC-004 Template Version Cannot Activate Without Verified Source`.
5. `SC-005 Active Template Version Is Immutable`.
6. `SC-006 Material Object Requires Source Traceability`.
7. `SC-007 Tender Can Bind Only to Active Version`.
8. `SC-008 Published Tender Bundle Is Immutable`.
9. `SC-009 Post-Publication Change Requires Addendum`.
10. `SC-010 Blocker Findings Prevent Activation`.
11. `SC-011 Required Reviews Prevent Unauthorized Activation`.
12. `SC-012 Render Requires Required Placeholders`.
13. `SC-013 Package Export/Import Hash Round Trip`.
14. `SC-014 Rule Test Cases Execute Deterministically`.
15. `SC-015 Permission Checks Fail Closed`.

### 19.3 Services

Implement:

1. `seed_service.load_all()`.
2. `seed_service.load_enums()`.
3. `seed_service.load_roles_and_permissions()`.
4. `seed_service.load_workflows()`.
5. `seed_service.load_audit_event_types()`.
6. `smoke_test_service.register_smoke_contracts()`.
7. `smoke_test_service.run_smoke_contract()`.
8. `smoke_test_service.run_required_smoke_suite()`.
9. `smoke_test_service.assert_required_suite_passed()`.

### 19.4 Tests

1. Running seed loader twice creates no duplicates.
2. Required smoke suite fails when guard intentionally violated.
3. Required smoke suite passes with valid fixture package.
4. Smoke results are auditable.

---

## 20. Stage 12 — API and Service Contracts

Implement API endpoints or whitelisted service methods matching the API/UI/service contract document.

### 20.1 Core API Groups

| API group | Required endpoints/actions |
|---|---|
| STD Family | create, read, list, update draft metadata. |
| STD Version | create, read, list, update draft metadata, transition state. |
| Source Document | register, attach file, verify hash, link to version. |
| Import Package | upload, validate, apply, export. |
| Section | create, reorder, read tree. |
| Clause | create, update, compute hash, compare. |
| Parameter | create, list, update schema, preview usage. |
| Rule | create, execute, run tests, list findings. |
| Form | create schema, create field, validate schema. |
| Requirement Schema | create/update schema, validate. |
| Price Schedule | create/update schema, validate rollups. |
| Evaluation Schema | create/update schema, validate. |
| Contract Schema | create/update schema, validate carry-forward. |
| Render | preview, final generate, check job, read artifact. |
| Workflow | available transitions, execute transition. |
| Approval | submit, approve, request changes, reject. |
| Tender STD Instance | bind, configure, validate, submit for review. |
| Generated Bundle | preview, final generate, approve, publish. |
| Addendum | request, impact analysis, approve, publish. |
| Smoke | run suite, read results. |
| Audit | read events, verify snapshot/hash. |

### 20.2 API Error Requirements

Every API must return structured errors with:

1. Error code.
2. Human-readable message.
3. Severity.
4. Object type.
5. Object ID if available.
6. Field path if applicable.
7. Remediation hint if available.

### 20.3 Tests

1. Unauthorized API calls return permission error.
2. Invalid state transition returns workflow error.
3. Immutable edit returns immutable object error.
4. Missing source trace returns source trace error.
5. Validation API returns findings with severity and field path.

---

## 21. Stage 13 — UI Shells

Do not overbuild UI before core services pass tests. Build only the core shells needed to operate and test the module.

### 21.1 STD Administration UI

Screens:

1. STD Template Families list/detail.
2. STD Template Versions list/detail.
3. Source Document Registry.
4. Import Package Workspace.
5. Section Tree Editor.
6. Clause/Content Block Viewer.
7. Parameter Registry.
8. Rule Registry.
9. Form Schema Registry.
10. Requirement/Price/Evaluation/Contract Schema Registry.
11. Render Profile Registry.
12. Validation Findings Dashboard.
13. Approval Queue.
14. Version Transition History.
15. Audit Event Viewer.

### 21.2 Tender STD Configuration UI

Screens:

1. Select STD Version.
2. Configuration Workspace.
3. Parameter Completion Panel.
4. Requirements Composer Shell.
5. Price Schedule Setup Shell.
6. Form/Evidence Activation Preview.
7. Validation Findings Panel.
8. Preview Generated Bundle.
9. Submit for Review.
10. Bundle Approval and Publication.
11. Addendum Request and Impact Workspace.

### 21.3 UI Guardrails

1. UI must hide or disable actions the user lacks permission for.
2. Server-side services must still enforce every permission and workflow guard.
3. Active STD versions must render as read-only.
4. Published tender bundles must render as read-only.
5. Addendum-required changes must route to addendum workflow.
6. Validation blockers must be visible and actionable.
7. Audit and transition history must be visible to authorized users.

---

## 22. Stage 14 — Test Hardening

### 22.1 Required Test Categories

| Test category | Purpose |
|---|---|
| Unit tests | Pure services, hash, canonical JSON, expression validation. |
| Model tests | Constraints, relationships, unique keys, soft delete behavior. |
| Permission tests | RBAC and object-level authorization. |
| Workflow tests | State transitions and guard behavior. |
| Validation tests | Rule engine and findings behavior. |
| Import/export tests | Manifest, module, hash, trace, round trip. |
| Rendering tests | Placeholder resolution and artifact hashes. |
| Immutability tests | Active template and published bundle protection. |
| Addendum tests | Post-publication change routing and impact publication. |
| Smoke tests | Required cross-module minimum workflows. |

### 22.2 Minimum Release Gate

The module cannot be marked implementation-complete unless:

1. All required smoke contracts pass.
2. All activation guards are tested.
3. All publication immutability guards are tested.
4. All API permission-denial paths are tested.
5. All package hash tests pass.
6. All source trace required tests pass.
7. No test bypasses the service layer to mutate governed records without asserting failure.

---

## 23. Stage 15 — Release Readiness

### 23.1 Migration Review

Before release:

1. Confirm all tables/DocTypes have required common fields.
2. Confirm unique constraints exist.
3. Confirm foreign keys or document links are indexed.
4. Confirm state fields are controlled values.
5. Confirm audit event writes are transactional with governed actions.
6. Confirm generated artifacts are stored immutably.
7. Confirm source files are stored with hash metadata.
8. Confirm seed loader is idempotent.

### 23.2 Security Review

Check:

1. Permission checks fail closed.
2. Object-level permissions are enforced.
3. No API allows direct active-version mutation.
4. No API allows direct published-bundle mutation.
5. Source files and generated bundles respect access controls.
6. Audit records cannot be edited by normal users.
7. Service accounts have minimum required permissions.

### 23.3 Performance Review

Minimum indexes:

1. Template version by family/status.
2. Source trace by target object.
3. Tender instance by tender ID and STD version ID.
4. Validation findings by run/status/severity.
5. Generated bundle by tender instance/status/type.
6. Audit event by object type/object ID/timestamp.
7. Package import by package code/status.
8. Workflow transition by workflow/from/to.

### 23.4 Documentation Review

Update:

1. Module README.
2. Seed installation guide.
3. API reference.
4. Workflow/state reference.
5. Developer guide for adding a new STD family.
6. Operator guide for importing a new STD package.
7. Troubleshooting guide for validation and activation blockers.

---

## 24. Implementation Prompts for Cursor

Use these prompts sequentially.

### Prompt 1 — Scaffold Module

```text
Implement Stage 0 of the STD Engine Core module from the Cursor Implementation Pack.
Create the module skeleton, shared base model/mixin, constants, exception classes, response envelopes, and test directories.
Do not implement business logic yet.
Add basic tests proving the module imports and base conventions are available.
```

### Prompt 2 — Reference/RBAC Models

```text
Implement Stage 1.
Create reference and RBAC models/tables/DocTypes for authority, jurisdiction, procurement category, enum set, enum value, role, permission, and role_permission.
Add migrations, idempotent seed loading, uniqueness constraints, and permission service fail-closed behavior.
Add tests for idempotency, duplicate protection, and permission denial.
```

### Prompt 3 — Template and Source Foundations

```text
Implement Stage 2.
Create template family/version and source document/source trace models.
Implement source file hashing, source verification, template version creation, version hash computation, and trace link services.
Add tests that prevent activation without verified source and prevent source hash mutation after verification.
```

### Prompt 4 — Content and Parameter Model

```text
Implement Stage 3.
Create section, content block, clause, placeholder, parameter group, parameter, parameter option, and parameter dependency models.
Implement section tree validation, placeholder binding validation, immutability checks, and dependency cycle detection.
Add tests for active-template immutability, placeholder failures, and circular dependency failures.
```

### Prompt 5 — Rule and Validation Engine

```text
Implement Stage 4.
Create rule definition, rule target, rule input, rule test case, validation run, and validation finding models.
Implement the validation service and a safe expression evaluator or constrained rule dispatcher.
Add tests for required fields, date order, conditional requirements, invalid expressions, blocker findings, and finding resolution audit behavior.
```

### Prompt 6 — Schema Models

```text
Implement Stage 5.
Create form, evidence, requirement, price, evaluation, contract, and render schema models.
Implement schema validation services and deterministic schema hashing.
Add tests for invalid schemas, price rollups, evaluation ordering, contract carry-forward mappings, and render placeholder completeness.
```

### Prompt 7 — Workflow and Approval

```text
Implement Stage 6.
Create workflow, state, transition, guard, approval request, approval step, approval event, and transition log models.
Seed the STD Template Version, Tender STD Instance, Generated Bundle, and Addendum state machines.
Implement transition execution, guard evaluation, approval completion checks, and segregation-of-duties checks.
Add tests preventing invalid jumps, missing reviews, missing smoke tests, and SOD violations.
```

### Prompt 8 — Tender Binding and Configuration

```text
Implement Stage 7.
Create tender STD instance, configuration value, requirement item, and price line template models.
Implement binding to active STD version, configuration value services, completeness validation, and configuration snapshot hashing.
Add tests that binding fails for inactive versions and published configuration is immutable.
```

### Prompt 9 — Generation and Bundle Immutability

```text
Implement Stage 8.
Create generated bundle, generated artifact, and generated section snapshot models.
Implement preview generation, final generation, placeholder resolution, artifact hash computation, bundle approval, and publication guards.
Add tests proving preview bundles cannot publish, final bundles require approved configuration, and published bundles cannot be modified.
```

### Prompt 10 — Addendum Workflow

```text
Implement Stage 9.
Create addendum record, impact, and delta models.
Implement request, impact analysis, validation, approval, publication, and prior-bundle supersession behavior.
Add tests that post-publication content changes route to addendum and that addendum publication hashes artifacts and marks prior bundle superseded.
```

### Prompt 11 — Import/Export Packages

```text
Implement Stage 10.
Create import and export package models.
Implement manifest validation, module validation, source trace validation, package hash validation, diff, apply-to-draft, rollback-on-failure, and export round trip.
Add tests for missing manifest, hash mismatch, missing modules, invalid source trace, import into active version, and export/import hash preservation.
```

### Prompt 12 — Seeds and Smoke Contracts

```text
Implement Stage 11.
Create smoke contract, smoke test case, smoke run, and smoke run result models.
Load required seed data and smoke contracts idempotently.
Implement smoke test runner and required smoke suite gate.
Add tests for all required smoke contracts SC-001 through SC-015.
```

### Prompt 13 — APIs

```text
Implement Stage 12.
Expose API endpoints or whitelisted service methods for the API groups in the implementation pack.
Every endpoint must use the service layer and permission service.
Do not allow direct mutation of governed records.
Add API tests for authorization failures, invalid transitions, immutable edits, missing traceability, and validation finding payloads.
```

### Prompt 14 — UI Shells

```text
Implement Stage 13.
Build minimal UI shells for STD Administration and Tender STD Configuration.
The UI must call APIs/services, not duplicate business logic.
Disable or hide unauthorized actions, but keep server-side enforcement authoritative.
Add UI smoke tests where the platform supports them.
```

### Prompt 15 — Release Gate

```text
Implement Stages 14 and 15 hardening.
Run and repair all tests.
Confirm smoke contracts pass.
Add release-readiness checks for migrations, indexes, permissions, audit logging, immutable artifacts, and documentation.
Do not mark the module complete until all non-negotiable controls pass.
```

---

## 25. Do-Not-Implement List

Cursor must not implement these shortcuts:

1. Do not store the official STD as one runtime JSON blob.
2. Do not implement an IT-specific wizard inside core.
3. Do not hard-code PPRA IT section names as core assumptions.
4. Do not allow editing Active STD versions.
5. Do not allow editing Published generated bundles.
6. Do not allow bypassing approval workflows by admin-only hidden actions.
7. Do not allow untraced clauses, rules, forms, or render blocks in an activatable version.
8. Do not use arbitrary executable code for rule expressions.
9. Do not permit publication with unresolved blocker/error findings.
10. Do not permit addenda as mere uploaded PDFs detached from impacted structured objects.
11. Do not generate contract artifacts without explicit carry-forward mappings.
12. Do not let UI state determine legal state; server-side workflow state is authoritative.

---

## 26. Definition of Done

The STD Engine Core module is done only when all of the following are true:

1. All domain tables/DocTypes from the domain model are implemented or explicitly mapped to equivalent framework records.
2. Required seed data loads idempotently.
3. Required state machines and transitions are seeded.
4. Template version activation guards are enforced.
5. Tender STD instance publication guards are enforced.
6. Active STD versions are immutable.
7. Published tender bundles are immutable.
8. Source traceability is enforced for material objects.
9. Rule and validation engine produces deterministic findings.
10. Import/export package hash validation works.
11. Render profiles can generate deterministic preview and final bundles.
12. Addendum workflow routes post-publication changes.
13. Audit events are produced for all governed actions.
14. Permissions fail closed.
15. Required smoke contracts pass.
16. API/service methods are covered by tests.
17. Minimal UI shells are implemented for administration and tender configuration.
18. Developer documentation is updated.

---

## 27. Next Artifact After This Pack

After implementation of the STD Engine Core module begins, the next design artifact should be:

**STD for Procurement of Information Technology — Extraction Matrix**

That artifact will map the official IT STD into the generalized engine through:

1. Section records.
2. Clause records.
3. Parameter records.
4. Rule records.
5. Tendering form schemas.
6. Evidence requirement schemas.
7. Requirement composer schemas.
8. Price schedule schemas.
9. Evaluation schemas.
10. Contract output schemas.
11. Render blocks.
12. Smoke tests.
13. Seed package files.

Do not start the full IT-specific wizard before the IT extraction matrix and seed package are reviewed.
