# IT Tender Configuration Wizard — Sprint Backlog and Task Breakdown

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Document type:** Sprint Backlog and Task Breakdown  
**Version:** 0.1  
**Status:** Draft for implementation planning  
**Prepared date:** 2026-07-08  
**Primary dependencies:** STD Engine Core Module; `KE-PPRA-IT-2022-04` seed package v0.2  
**Reference STD family:** `KE-PPRA-IT`  
**Calibration fixture:** NSSF SPS ERP System Tender, Ref. `NSSFSPS/ICT/ERP/001/2025-2026`  

---

## 1. Purpose

This document converts the IT Tender Configuration Wizard implementation pack into a sprint-level delivery backlog.

It is intended for product owners, technical leads, backend engineers, frontend engineers, QA engineers, security reviewers, and Cursor-assisted development sessions.

The backlog is deliberately sequenced so that governance, state transitions, source traceability, validation, and immutability are implemented before user-facing convenience features. The wizard must not become a legal-document editor. It must remain a controlled tender-configuration layer that consumes active Standard Tender Document definitions from the STD Engine Core.

---

## 2. Non-Negotiable Delivery Controls

| Control | Delivery implication |
|---|---|
| Active STD binding | A wizard instance must bind to exactly one active STD version at creation. |
| No floating template reference | A wizard instance must not automatically upgrade when a newer STD version becomes active. |
| No master content mutation | The wizard must not edit STD family, STD version, sections, clauses, rules, forms, render blocks, or source-trace records. |
| Locked clause protection | ITT and GCC legal text must be read-only reference/preview content. |
| Structured configuration only | TDS, SCC, requirements, schedules, system inventory, price setup, evaluation, forms, and evidence must be structured records. |
| Governance before publication | Review and approval gates must be completed before publication bundle generation. |
| Validation blockers | Blocking findings must prevent review submission, approval, binding, publication, and addendum publication. |
| Published artifact immutability | Published bundles and published addendum bundles must be immutable and hash-verifiable. |
| Addendum-only post-publication changes | Changes after publication must pass through addendum request, impact analysis, review, and publication. |
| NSSF as fixture only | The NSSF ERP tender must be used for calibration/testing only, not as the master STD model. |

---

## 3. Delivery Assumptions

1. The STD Engine Core APIs or equivalent service adapter mocks are available before Sprint 1 begins.
2. The IT STD seed package v0.2 is importable into a draft/test environment.
3. Full legal activation of the IT STD package is not required for wizard build; a draft/test package may be used with a feature flag or test-mode binding.
4. Production publication must remain disabled until the target environment has an approved active STD package.
5. The implementation stack may be Frappe/ERPNext, Django/FastAPI, NestJS, Laravel, Rails, or an equivalent platform. This backlog is framework-neutral.
6. Each sprint must produce automated tests, not only UI screens.
7. Cursor-generated code must be reviewed against the governance and immutability rules before merge.

---

## 4. Recommended Sprint Cadence

| Item | Recommendation |
|---|---|
| Sprint length | 2 weeks |
| Sprint demo | End of each sprint |
| QA regression | Continuous, with formal regression at sprint close |
| Security review | Sprint 2, Sprint 7, Sprint 8, Sprint 9, Sprint 10 |
| Product/legal review | Sprint 3, Sprint 7, Sprint 8, Sprint 9 |
| Release candidate | After Sprint 10 |
| Production enablement | Only after STD package activation and end-to-end smoke tests pass |

---

## 5. Release Milestones

| Milestone | Target sprint | Outcome |
|---|---:|---|
| M0 — Engineering readiness | Sprint 0 | Environments, package imports, CI, test scaffolding, fixtures ready. |
| M1 — Governed wizard foundation | Sprint 2 | Wizard instance creation, state guards, permission checks, audit, and STD version binding work. |
| M2 — Structured configuration baseline | Sprint 3 | TDS, SCC, profile, dates, participation, and security instrument values are persisted and validated. |
| M3 — IT requirements and commercial model | Sprint 5 | Requirements, schedule, system inventory, and price setup are configurable and validated. |
| M4 — Evaluation and supplier schemas | Sprint 6 | Evaluation, forms, evidence, supplier schema, and evaluation workspace snapshots are generated. |
| M5 — Review-ready configuration | Sprint 7 | Full validation runner, review workflow, blockers, and approval gates work. |
| M6 — Publishable bundle generation | Sprint 8 | Preview, publication bundle, supplier/evaluation/contract handoff, and hash evidence work. |
| M7 — Addendum governance | Sprint 9 | Post-publication changes are addendum-only and impact-analyzed. |
| M8 — Calibration and release hardening | Sprint 10 | NSSF ERP fixture maps cleanly, all smoke contracts pass, and security/performance gaps are resolved. |

---

## 6. Backlog Structure

The backlog is organized as:

1. **Initiatives** — major implementation areas.
2. **Epics** — deliverable groups within each initiative.
3. **Stories / tasks** — development units suitable for sprint planning.
4. **Acceptance checks** — objective completion criteria.
5. **Dependencies** — predecessor work or environment requirements.

Priority values:

| Priority | Meaning |
|---|---|
| P0 | Required for safe module operation. Cannot defer. |
| P1 | Required for MVP completion. |
| P2 | Required before production release but may follow MVP demo. |
| P3 | Enhancement or later hardening item. |

Estimate values are intentionally relative. Teams may convert them to story points, ideal engineering days, or issue sizes.

---

## 7. Sprint Plan Overview

| Sprint | Theme | Primary outcome |
|---|---|---|
| Sprint 0 | Readiness and environment setup | Development can begin safely. |
| Sprint 1 | Core adapters, audit, hash, permissions | Technical foundation and guardrails. |
| Sprint 2 | Wizard instance, steps, lifecycle | Controlled wizard object with governed transitions. |
| Sprint 3 | TDS, SCC, tender profile | Structured tender-specific parameters. |
| Sprint 4 | Requirement composer | Functional, technical, service, and performance requirements. |
| Sprint 5 | Schedule, inventory, price setup | Implementation schedule, system inventory, and price schema. |
| Sprint 6 | Evaluation, forms, evidence | Supplier and evaluator downstream schemas. |
| Sprint 7 | Validation and review | Full validation runner and approval gates. |
| Sprint 8 | Preview, publication, carry-forward | Immutable generated bundles and handoff packages. |
| Sprint 9 | Addendum | Post-publication change governance. |
| Sprint 10 | Calibration and hardening | NSSF fixture, security, performance, release readiness. |

---

## 8. Sprint 0 — Readiness and Environment Setup

### 8.1 Sprint Goal

Prepare development, test, fixture, and governance foundations before implementation starts.

### 8.2 Required Inputs

1. STD Engine Core Module implementation pack.
2. IT Tender Configuration Wizard implementation pack.
3. IT STD seed package v0.2.
4. NSSF ERP calibration mapping.
5. Access to target repository and development environment.
6. Selected application framework conventions.

### 8.3 Sprint Backlog

| ID | Task | Priority | Estimate | Dependencies | Acceptance criteria |
|---|---|---:|---:|---|---|
| S0-001 | Confirm repository structure for modules, services, migrations, tests, and fixtures. | P0 | 2 | None | Folder/module layout approved by tech lead. |
| S0-002 | Configure CI pipeline for linting, formatting, unit tests, integration tests, and security checks. | P0 | 3 | S0-001 | CI runs on pull requests and blocks failing tests. |
| S0-003 | Import or mock STD Engine Core API/service contract. | P0 | 3 | Core contract available | Wizard code can call adapter interface in tests. |
| S0-004 | Load IT STD seed package v0.2 into dev/test or create deterministic package fixture. | P0 | 3 | S0-003 | Test package metadata is retrievable by `std_family_code` and `version_code`. |
| S0-005 | Create NSSF ERP fixture namespace marked development/test only. | P1 | 2 | NSSF mapping artifact | Fixture cannot be enabled in production mode. |
| S0-006 | Define branch, PR, review, and migration policy. | P0 | 1 | None | PR checklist includes governance, permissions, tests, and immutability checks. |
| S0-007 | Create test user roles and baseline accounts. | P0 | 2 | Permission seed plan | Tests can authenticate as procurement drafter, reviewer, approver, admin, auditor. |
| S0-008 | Confirm feature flags for draft package usage, publication disablement, and fixture loading. | P0 | 2 | Environment config | Production-unsafe actions are disabled unless explicitly allowed in non-production. |

### 8.4 Exit Criteria

1. CI is operational.
2. STD Core adapter is callable or mockable.
3. IT STD package fixture is available.
4. NSSF fixture is isolated from production.
5. Test users and roles exist.
6. Development may proceed without inventing missing architecture during coding.

---

## 9. Sprint 1 — Core Adapters, Audit, Hash, and Permissions

### 9.1 Sprint Goal

Build the service foundation that every later feature must use.

### 9.2 Sprint Backlog

| ID | Task | Priority | Estimate | Dependencies | Acceptance criteria |
|---|---|---:|---:|---|---|
| S1-001 | Implement `STDCoreAdapter` interface. | P0 | 5 | S0-003 | Adapter retrieves active/test IT STD metadata, sections, parameters, rules, forms, render blocks. |
| S1-002 | Implement canonical JSON serialization utility. | P0 | 3 | S1-001 | Identical semantic payloads produce identical canonical strings. |
| S1-003 | Implement `WizardHashService`. | P0 | 3 | S1-002 | Hashes are deterministic and include algorithm/version metadata. |
| S1-004 | Implement `WizardAuditService`. | P0 | 5 | S0-001 | Create/update/transition/validation/publication events are persisted with actor, timestamp, object, before/after metadata. |
| S1-005 | Implement `WizardPermissionService`. | P0 | 5 | S0-007 | Role/action checks pass for allowed roles and fail for unauthorized roles. |
| S1-006 | Implement `WizardStateGuardService`. | P0 | 5 | S1-005 | Invalid transitions and direct state mutation attempts are rejected. |
| S1-007 | Create typed error model for permission, state, validation, immutability, source, and package errors. | P0 | 3 | S1-005, S1-006 | API/service errors are consistent and testable. |
| S1-008 | Add unit tests for adapter, hash, audit, permission, and state guard services. | P0 | 5 | S1-001 through S1-007 | Tests pass in CI. |

### 9.3 Exit Criteria

1. Adapter can retrieve STD package metadata and schema records.
2. Hashing is deterministic.
3. Unauthorized actions are rejected.
4. Audit events are generated.
5. Invalid state transitions fail with typed errors.

---

## 10. Sprint 2 — Wizard Instance, Step Generation, and Lifecycle

### 10.1 Sprint Goal

Create a governed wizard instance that binds to a single STD version and generates controlled wizard steps.

### 10.2 Sprint Backlog

| ID | Task | Priority | Estimate | Dependencies | Acceptance criteria |
|---|---|---:|---:|---|---|
| S2-001 | Create database/models for wizard instance, step instance, progress, audit event, and hash evidence. | P0 | 8 | S1 complete | Migrations run cleanly; records include tenant/organization fields where applicable. |
| S2-002 | Implement `WizardInstanceService.create`. | P0 | 5 | S2-001, S1-001 | Instance binds to exactly one active/test STD version at creation. |
| S2-003 | Enforce immutable `std_version_id` after creation. | P0 | 3 | S2-002 | Update attempts are blocked and audited. |
| S2-004 | Implement `WizardStepService.generate_steps_from_package`. | P0 | 5 | S2-002 | Step instances are created from package/wizard-step binding order. |
| S2-005 | Implement `WizardProgressService`. | P1 | 3 | S2-004 | Progress calculates step status and overall completion. |
| S2-006 | Implement `WizardWorkflowService` for early states: `DRAFT`, `IN_CONFIGURATION`, `VALIDATION_FAILED`. | P0 | 5 | S1-006, S2-001 | Transitions are service-only and permission-checked. |
| S2-007 | API endpoints for create/list/get/delete draft configuration. | P1 | 5 | S2-002, S2-006 | APIs return summary, steps, state, validation status, and package binding. |
| S2-008 | Basic wizard shell UI: header, step rail, package badge, state badge, source/version reference panel. | P1 | 8 | S2-007 | User can create/open a wizard instance and see generated steps. |
| S2-009 | Tests for instance creation, version immutability, step generation, and lifecycle guards. | P0 | 5 | S2-001 through S2-008 | Tests pass in CI. |

### 10.3 Exit Criteria

1. Wizard instance can be created.
2. Steps are generated from STD/package metadata.
3. STD version binding is immutable.
4. Direct state mutation is blocked.
5. Basic shell UI displays governed instance data.

---

## 11. Sprint 3 — Tender Profile, TDS, SCC, Dates, Participation, and Security Instruments

### 11.1 Sprint Goal

Implement the first full structured configuration area: tender identity, participation, date controls, tender security/professional indemnity, TDS values, and SCC values.

### 11.2 Sprint Backlog

| ID | Task | Priority | Estimate | Dependencies | Acceptance criteria |
|---|---|---:|---:|---|---|
| S3-001 | Create tender profile models: identity, participation, dates, security instrument, TDS value, SCC value, value history. | P0 | 8 | S2 complete | Migrations include unique constraints and audit/history fields. |
| S3-002 | Implement `TenderIdentityService`. | P0 | 3 | S3-001 | Tender name, tender number, PE identity, and description validate. |
| S3-003 | Implement `ParticipationService`. | P0 | 4 | S3-001 | National/international, reservations, alternatives, lots, JV limit, and prequalification values are stored. |
| S3-004 | Implement `TenderDateService`. | P0 | 4 | S3-001 | Submission, opening, clarification, meeting, validity, and related date rules validate. |
| S3-005 | Implement `SecurityInstrumentService`. | P0 | 4 | S3-001 | Tender security, tender-securing declaration, professional indemnity, validity, and amount rules validate. |
| S3-006 | Implement `TDSService.get_schema_and_values` and `TDSService.update_values`. | P0 | 5 | S1-001, S3-001 | TDS schema is read from STD Core; values are tender-specific only. |
| S3-007 | Implement `SCCService.get_schema_and_values` and `SCCService.update_values`. | P0 | 5 | S1-001, S3-001 | SCC schema is read from STD Core; values are tender-specific only. |
| S3-008 | Implement parameter value history and audit on each update. | P0 | 4 | S3-006, S3-007 | Before/after values are recorded with actor and reason where required. |
| S3-009 | API endpoints for profile, participation, dates, security, TDS, and SCC. | P1 | 8 | S3-002 through S3-007 | APIs reject invalid values and return typed findings. |
| S3-010 | UI screens for tender identity, participation, dates, security, TDS, and SCC. | P1 | 12 | S3-009 | Users can enter and save structured values; read-only source trace is visible. |
| S3-011 | Tests for required fields, date ordering, amount rules, TDS/SCC schema binding, and history. | P0 | 7 | S3-001 through S3-010 | Tests pass in CI. |

### 11.3 Exit Criteria

1. Tender-specific TDS/SCC values can be captured without editing the master STD.
2. Required profile fields validate.
3. Date-order validation works.
4. Security/professional indemnity rules validate.
5. Update history and audit records are created.

---

## 12. Sprint 4 — IT Requirement Composer

### 12.1 Sprint Goal

Build the structured requirement composer for Information Technology tenders.

### 12.2 Sprint Backlog

| ID | Task | Priority | Estimate | Dependencies | Acceptance criteria |
|---|---|---:|---:|---|---|
| S4-001 | Create models for requirement group, requirement item, requirement response type, requirement evidence binding, and requirement evaluation binding. | P0 | 8 | S3 complete | Models include requirement code, category, priority, mandatory flag, source/reference fields, and lifecycle fields. |
| S4-002 | Implement `RequirementComposerService.create_group_from_package_category`. | P0 | 4 | S4-001 | Functional, architectural, performance, service, technology, testing, integration, documentation, training categories are supported through package schema. |
| S4-003 | Implement requirement item CRUD before publication. | P0 | 6 | S4-001 | Requirement codes are unique per tender and soft-delete is audited. |
| S4-004 | Implement requirement bulk import from structured table/CSV/JSON. | P1 | 5 | S4-003 | Import validates columns and produces row-level findings. |
| S4-005 | Implement `RequirementEvidenceBindingService`. | P0 | 4 | S4-003 | Mandatory requirements can require supplier evidence or reference pages. |
| S4-006 | Implement `RequirementEvaluationBindingService`. | P0 | 4 | S4-003 | Requirements can bind to evaluation criteria or conformance matrix rules. |
| S4-007 | Add requirement source-trace and legal/status display. | P1 | 3 | S4-003 | Users can see whether an item is package-originated, PE-authored, or imported. |
| S4-008 | API endpoints for requirement groups, items, import, evidence binding, and evaluation binding. | P1 | 8 | S4-002 through S4-006 | APIs return row-level validation findings. |
| S4-009 | UI requirement composer: group tabs, requirement table, add/edit drawer, import preview, conformance/evidence binding panels. | P1 | 15 | S4-008 | Users can manage requirements without free-form document editing. |
| S4-010 | Tests for code uniqueness, mandatory flags, evidence binding, evaluation binding, import validation, and soft delete. | P0 | 7 | S4-001 through S4-009 | Tests pass in CI. |

### 12.3 Exit Criteria

1. Requirement groups and items are structured.
2. Requirement codes are unique.
3. Requirement evidence and evaluation bindings work.
4. Bulk import is validated before save.
5. No locked STD text is edited.

---

## 13. Sprint 5 — Implementation Schedule, System Inventory, and Price Setup

### 13.1 Sprint Goal

Implement the linked delivery/commercial model: phases, milestones, acceptance events, inventory items, price tables, recurrent costs, and milestone-payment bindings.

### 13.2 Sprint Backlog

| ID | Task | Priority | Estimate | Dependencies | Acceptance criteria |
|---|---|---:|---:|---|---|
| S5-001 | Create models for implementation phase, milestone, deliverable, acceptance event, milestone dependency, and milestone payment binding. | P0 | 8 | S4 complete | Models include dates, dependencies, acceptance criteria, percentage/payment metadata, and audit fields. |
| S5-002 | Implement `ImplementationScheduleService`. | P0 | 6 | S5-001 | Phases and milestones can be created, updated, ordered, and validated. |
| S5-003 | Implement milestone dependency cycle detection. | P0 | 4 | S5-002 | Cycles are blocked with clear finding paths. |
| S5-004 | Implement `AcceptanceEventService`. | P0 | 4 | S5-001 | Acceptance events bind to milestones and contract carry-forward records. |
| S5-005 | Implement `MilestonePaymentBindingService`. | P1 | 4 | S5-002 | Payment milestone totals validate against configured rules. |
| S5-006 | Create models for system inventory groups and items. | P0 | 6 | S4 complete | Inventory items support supply/install and recurrent cost categories. |
| S5-007 | Implement `SystemInventoryService`. | P0 | 5 | S5-006 | Inventory items validate quantity, unit, category, and price-template bindings. |
| S5-008 | Create models for price schedule setup, price lines, recurrent cost periods, tax treatment, and summary lines. | P0 | 8 | S5-006 | Price line templates can bind to inventory and requirements where configured. |
| S5-009 | Implement `PriceScheduleService`. | P0 | 6 | S5-008 | Supply/install and recurrent costs are captured and summarized deterministically. |
| S5-010 | API endpoints for schedule, acceptance, inventory, and price setup. | P1 | 10 | S5-002 through S5-009 | APIs return validation findings and summary totals. |
| S5-011 | UI screens for phases/milestones, inventory tables, price setup, recurrent costs, and payment milestone bindings. | P1 | 15 | S5-010 | Users can configure schedule, inventory, price structure, and recurrent-cost periods. |
| S5-012 | Tests for milestone date rules, dependency cycles, inventory-price bindings, recurrent cost periods, and payment totals. | P0 | 8 | S5-001 through S5-011 | Tests pass in CI. |

### 13.3 Exit Criteria

1. Implementation schedule is structured and dependency-safe.
2. System inventory is structured.
3. Inventory-price bindings validate.
4. Recurrent cost periods validate.
5. Payment milestone totals comply with configured rules.

---

## 14. Sprint 6 — Evaluation, Forms, Evidence, Supplier Schema, and Evaluation Workspace

### 14.1 Sprint Goal

Generate downstream supplier and evaluator structures from the configured tender.

### 14.2 Sprint Backlog

| ID | Task | Priority | Estimate | Dependencies | Acceptance criteria |
|---|---|---:|---:|---|---|
| S6-001 | Create models for evaluation stage, criterion, subcriterion, score band, pass mark, and evaluation rule binding. | P0 | 8 | S5 complete | Models support preliminary, technical, financial, qualification, and award stages. |
| S6-002 | Implement `EvaluationConfigService`. | P0 | 6 | S6-001 | Evaluation stage sequence is generated from package/configuration. |
| S6-003 | Implement technical scoring total and pass-mark validation. | P0 | 4 | S6-002 | Totals and pass marks validate with blocker findings where invalid. |
| S6-004 | Create models for qualification requirement, mandatory requirement, and supporting documentation. | P0 | 5 | S6-001 | Mandatory and scored requirements can be distinguished. |
| S6-005 | Implement `QualificationRequirementService`. | P0 | 5 | S6-004 | Qualification criteria persist with required evidence. |
| S6-006 | Create models for form activation and form field override where allowed by package. | P0 | 5 | S6-001 | Forms activate only according to rules and configuration. |
| S6-007 | Implement `FormActivationService`. | P0 | 4 | S6-006 | Activated forms match tender settings, e.g. JV, foreign tenderer, tender security, professional indemnity, alternatives. |
| S6-008 | Create and implement `EvidenceRequirementService`. | P0 | 5 | S4, S6-004 | Evidence requirements bind to forms, requirements, qualification criteria, and supplier schema. |
| S6-009 | Implement `SupplierSchemaSnapshotService`. | P0 | 6 | S6-007, S6-008 | Supplier response schema snapshot is deterministic and hashable. |
| S6-010 | Implement `EvaluationWorkspaceSnapshotService`. | P0 | 6 | S6-002, S6-005 | Evaluation workspace snapshot is deterministic and hashable. |
| S6-011 | API endpoints for evaluation, qualification, form activation, evidence, supplier snapshot, and evaluator snapshot. | P1 | 10 | S6-002 through S6-010 | APIs return activated forms and schema snapshots. |
| S6-012 | UI screens for evaluation criteria editor, qualification requirements, forms/evidence activation, and snapshot preview. | P1 | 15 | S6-011 | Users can review supplier/evaluator schemas before validation. |
| S6-013 | Tests for scoring totals, pass mark, form activation rules, evidence propagation, and snapshot hash determinism. | P0 | 8 | S6-001 through S6-012 | Tests pass in CI. |

### 14.3 Exit Criteria

1. Evaluation sequence is structured.
2. Technical scoring and pass mark validate.
3. Forms activate based on rules.
4. Mandatory evidence appears in supplier schema.
5. Supplier and evaluator snapshots are deterministic and hashable.

---

## 15. Sprint 7 — Validation Runner, Findings, Review, and Approval Gates

### 15.1 Sprint Goal

Make the wizard review-ready by enforcing full validation, findings, review workflow, approval gates, and segregation of duties.

### 15.2 Sprint Backlog

| ID | Task | Priority | Estimate | Dependencies | Acceptance criteria |
|---|---|---:|---:|---|---|
| S7-001 | Create models for validation run, validation finding, finding category, finding resolution, review request, review decision, and approval gate. | P0 | 8 | S6 complete | Models include severity, field path, rule source, blocking behavior, actor, and timestamps. |
| S7-002 | Implement `WizardValidationService.run_full_validation`. | P0 | 8 | S7-001 | Runner validates profile, TDS, SCC, requirements, schedule, inventory, price, evaluation, forms, evidence, snapshots. |
| S7-003 | Implement `ValidationFindingService`. | P0 | 5 | S7-002 | Findings include severity, category, rule id, field path, display message, and blocking flag. |
| S7-004 | Implement `ManualFindingResolutionService`. | P0 | 4 | S7-003 | Manual resolution requires permission, reason, and audit. |
| S7-005 | Implement review submission workflow. | P0 | 5 | S7-002 | Blockers prevent submission; clean configurations can move to review. |
| S7-006 | Implement review decision workflow: approve, return, reject, request changes. | P0 | 6 | S7-005 | Decisions are permission-checked and audited. |
| S7-007 | Implement approval gate tracker. | P0 | 5 | S7-006 | Required review tracks must complete before approval for publication. |
| S7-008 | Implement segregation-of-duties checks. | P0 | 5 | S7-006 | Same actor cannot perform conflicting actions where policy forbids it. |
| S7-009 | API endpoints for validation, findings, finding resolution, submit review, review decisions, and approval gates. | P1 | 10 | S7-002 through S7-008 | APIs reject invalid workflow actions with typed errors. |
| S7-010 | UI validation panel, findings table, review request screen, approval decision panel, and audit timeline. | P1 | 15 | S7-009 | Users can see blockers, warnings, review status, and decisions. |
| S7-011 | Tests for full validation, blockers, manual resolution, review decisions, approval gates, segregation of duties, and audit. | P0 | 10 | S7-001 through S7-010 | Tests pass in CI. |
| S7-012 | Security review of permissions and workflow bypass risks. | P0 | 3 | S7-011 | Findings are logged and P0/P1 issues resolved before Sprint 8. |

### 15.3 Exit Criteria

1. Full validation runs across all configured areas.
2. Blockers prevent review submission.
3. Review and approval decisions are audited.
4. Segregation-of-duties rules pass tests.
5. No direct workflow bypass remains known.

---

## 16. Sprint 8 — Preview, Publication Bundle, Tender Binding, and Contract Carry-Forward

### 16.1 Sprint Goal

Generate preview and publication bundles, bind approved configuration to a tender, and produce downstream supplier/evaluation/contract handoff packages.

### 16.2 Sprint Backlog

| ID | Task | Priority | Estimate | Dependencies | Acceptance criteria |
|---|---|---:|---:|---|---|
| S8-001 | Create models for preview bundle, publication bundle, generated artifact, render event, artifact hash, supplier handoff, evaluation handoff, and contract carry-forward package. | P0 | 10 | S7 complete | Models include immutable-state fields, hash evidence, and source package reference. |
| S8-002 | Implement `WizardPreviewService`. | P0 | 6 | S8-001 | Preview can be generated before publication and marked non-authoritative. |
| S8-003 | Implement `WizardRenderService`. | P0 | 8 | S8-002, STD Core render blocks | Rendered sections are deterministic from package definitions and configuration values. |
| S8-004 | Implement `PublicationBundleService`. | P0 | 8 | S7 approvals, S8-003 | Publication requires clean validation and required approvals. |
| S8-005 | Implement immutable publication bundle enforcement. | P0 | 5 | S8-004 | Published artifacts cannot be updated or deleted through normal update paths. |
| S8-006 | Implement `ContractCarryForwardService`. | P0 | 6 | S8-004 | Contract carry-forward package contains award/contract fields, SCC values, acceptance events, securities, IP/software categories, price schedules. |
| S8-007 | Implement supplier response handoff generation. | P0 | 5 | S6 snapshots, S8-004 | Supplier schema is generated and hash-linked to publication bundle. |
| S8-008 | Implement evaluation workspace handoff generation. | P0 | 5 | S6 snapshots, S8-004 | Evaluation workspace is generated and hash-linked to publication bundle. |
| S8-009 | Implement tender binding service. | P0 | 5 | S8-004 | Approved configuration binds to one tender record; binding is audited. |
| S8-010 | API endpoints for preview, render, publication, artifacts, hash manifest, binding, and downstream handoffs. | P1 | 12 | S8-002 through S8-009 | APIs require approval and validation gates before publication. |
| S8-011 | UI preview viewer, render status, hash evidence panel, publication confirmation, artifact list, and handoff summary. | P1 | 15 | S8-010 | Users can preview, publish, and inspect hash evidence. |
| S8-012 | Tests for preview generation, publication gating, immutability, hash manifest, supplier/evaluation/contract handoff, and tender binding. | P0 | 12 | S8-001 through S8-011 | Tests pass in CI. |
| S8-013 | Product/legal review of generated artifacts using sample IT tender configuration. | P0 | 5 | S8-011 | Review findings are logged; blockers resolved before release candidate. |

### 16.3 Exit Criteria

1. Preview bundle can be generated.
2. Publication bundle requires clean validation and approvals.
3. Published artifacts are immutable.
4. Supplier, evaluation, and contract carry-forward handoffs are generated and hashed.
5. Tender binding is audited.

---

## 17. Sprint 9 — Addendum Governance and Impact Analysis

### 17.1 Sprint Goal

Implement post-publication change governance so all changes are handled through addenda.

### 17.2 Sprint Backlog

| ID | Task | Priority | Estimate | Dependencies | Acceptance criteria |
|---|---|---:|---:|---|---|
| S9-001 | Create models for addendum request, addendum scope item, impact analysis, impacted artifact, addendum review decision, addendum bundle, and addendum hash evidence. | P0 | 10 | S8 complete | Models preserve original publication bundle immutability. |
| S9-002 | Implement `AddendumRequestService`. | P0 | 5 | S9-001 | Addendum request can be opened only for published configurations. |
| S9-003 | Enforce post-publication edit block outside addendum. | P0 | 5 | S9-002 | Direct edits to published configuration values are rejected. |
| S9-004 | Implement `AddendumImpactAnalysisService`. | P0 | 8 | S9-002 | Affected sections, forms, requirements, price schedules, evaluation schemas, supplier schemas, and contract carry-forward items are identified. |
| S9-005 | Implement addendum validation rules. | P0 | 5 | S9-004 | Addendum cannot introduce invalid downstream state. |
| S9-006 | Implement addendum review and approval workflow. | P0 | 5 | S9-005 | Approval gates and segregation-of-duties rules apply. |
| S9-007 | Implement `AddendumBundleService`. | P0 | 6 | S9-006 | Addendum bundle renders changed/affected content and hash evidence. |
| S9-008 | Implement `AddendumPublicationService`. | P0 | 5 | S9-007 | Addendum publication creates immutable bundle and audit trail. |
| S9-009 | API endpoints for addendum request, impacted fields, impact analysis, review, publication, and hash evidence. | P1 | 10 | S9-002 through S9-008 | APIs enforce addendum-only post-publication changes. |
| S9-010 | UI for addendum request, field changes, impact analysis report, review decisions, and addendum publication. | P1 | 15 | S9-009 | Users can see exactly what the addendum affects before approval. |
| S9-011 | Tests for blocked direct edits, impact analysis, addendum validation, review, immutable addendum publication, and original bundle immutability. | P0 | 12 | S9-001 through S9-010 | Tests pass in CI. |
| S9-012 | Security review of publication/addendum immutability. | P0 | 3 | S9-011 | P0/P1 bypass risks are resolved. |

### 17.3 Exit Criteria

1. Published configurations cannot be edited directly.
2. Addendum request and impact analysis work.
3. Addendum review and publication are governed.
4. Original publication bundle remains immutable.
5. Addendum bundle is separately hashed and immutable.

---

## 18. Sprint 10 — NSSF Calibration, Hardening, UAT Readiness, and Release Candidate

### 18.1 Sprint Goal

Prove the wizard can represent a real ERP tender without corrupting the master IT STD model, then harden for release.

### 18.2 Sprint Backlog

| ID | Task | Priority | Estimate | Dependencies | Acceptance criteria |
|---|---|---:|---:|---|---|
| S10-001 | Implement `CalibrationFixtureService` for NSSF ERP tender in dev/test only. | P0 | 5 | S9 complete | Fixture cannot run in production mode. |
| S10-002 | Implement `CalibrationMappingService`. | P0 | 6 | S10-001 | NSSF profile, TDS, SCC, requirements, evaluation, price, schedule, and contract values map into wizard records. |
| S10-003 | Implement `CalibrationDeviationService`. | P0 | 5 | S10-002 | Deviations from official IT STD model are flagged, not silently normalized. |
| S10-004 | Run NSSF calibration through full validation, preview, publication simulation, and addendum simulation. | P0 | 8 | S10-001 through S10-003 | Fixture maps cleanly or produces documented findings; no master STD mutation occurs. |
| S10-005 | Performance test validation, preview generation, publication bundle generation, and addendum impact analysis. | P1 | 5 | S8, S9 | Performance thresholds are documented and met or risk-accepted. |
| S10-006 | Accessibility and usability pass for wizard UI. | P1 | 4 | UI complete | Critical usability issues are fixed. |
| S10-007 | Security review: RBAC, object authorization, workflow transitions, immutable states, audit, hash evidence, fixture isolation. | P0 | 6 | S10-004 | P0/P1 security findings resolved. |
| S10-008 | Data migration and rollback rehearsal. | P1 | 4 | All migrations complete | Migrations and rollback steps are documented and tested in staging. |
| S10-009 | Production feature-flag plan. | P0 | 3 | S10-007 | Publication and fixture flags are explicitly controlled by environment. |
| S10-010 | UAT script preparation. | P1 | 5 | S10-004 | UAT scripts cover full tender configuration, review, preview, publication, and addendum flow. |
| S10-011 | Release candidate build and release notes. | P1 | 4 | S10-005 through S10-010 | RC build is tagged; release notes include known limitations and activation dependencies. |
| S10-012 | Final smoke contract run. | P0 | 5 | S10-011 | All P0 smoke contracts pass. |

### 18.3 Exit Criteria

1. NSSF ERP calibration proves the model can handle real ERP tender content.
2. No master STD content is mutated by fixture import.
3. Security and immutability checks pass.
4. UAT scripts are ready.
5. Release candidate is tagged.

---

## 19. Initiative and Epic Backlog

### 19.1 Initiative A — Governed Wizard Foundation

| Epic ID | Epic | Sprints | Outcome |
|---|---|---|---|
| A1 | Environment and CI readiness | 0 | Safe development environment. |
| A2 | STD Core adapter and utility services | 1 | Package metadata and schemas retrievable. |
| A3 | Audit, hash, permissions, state guards | 1 | Governance controls implemented. |
| A4 | Wizard instance and lifecycle | 2 | Governed wizard object with fixed STD version binding. |
| A5 | Wizard shell UI | 2 | Users can create/open and navigate a wizard instance. |

### 19.2 Initiative B — Tender Configuration Data

| Epic ID | Epic | Sprints | Outcome |
|---|---|---|---|
| B1 | Tender identity and PE profile | 3 | Tender identity data captured. |
| B2 | Participation, lots, alternatives, reservations | 3 | Participation model captured. |
| B3 | Dates and deadlines | 3 | Date dependencies validated. |
| B4 | Security/professional indemnity | 3 | Security instrument data validated. |
| B5 | TDS and SCC parameter values | 3 | Tender-specific parameter values captured. |

### 19.3 Initiative C — IT Requirement and Commercial Configuration

| Epic ID | Epic | Sprints | Outcome |
|---|---|---|---|
| C1 | Requirement composer | 4 | Structured IT requirements captured. |
| C2 | Requirement import | 4 | Large requirement tables can be imported safely. |
| C3 | Requirement evidence/evaluation binding | 4 | Requirements feed supplier and evaluator schemas. |
| C4 | Implementation schedule | 5 | Phases, milestones, dependencies, acceptance events. |
| C5 | System inventory | 5 | Supply/install and recurrent inventory structured. |
| C6 | Price schedule setup | 5 | Price tables and recurrent costs configured. |

### 19.4 Initiative D — Supplier and Evaluation Outputs

| Epic ID | Epic | Sprints | Outcome |
|---|---|---|---|
| D1 | Evaluation configuration | 6 | Evaluation stages and criteria configured. |
| D2 | Qualification requirements | 6 | Mandatory and scored qualification requirements. |
| D3 | Form activation | 6 | Supplier forms activated by rules. |
| D4 | Evidence requirements | 6 | Evidence obligations generated. |
| D5 | Supplier and evaluation snapshots | 6 | Hashable downstream schemas generated. |

### 19.5 Initiative E — Validation, Review, Publication, and Addendum

| Epic ID | Epic | Sprints | Outcome |
|---|---|---|---|
| E1 | Full validation runner | 7 | Blockers/warnings/info findings generated. |
| E2 | Review and approval workflow | 7 | Review gates enforced. |
| E3 | Preview rendering | 8 | Non-authoritative preview generated. |
| E4 | Publication bundle | 8 | Immutable tender publication bundle. |
| E5 | Downstream handoff | 8 | Supplier, evaluation, and contract packages. |
| E6 | Addendum governance | 9 | Post-publication changes governed. |

### 19.6 Initiative F — Calibration and Release Hardening

| Epic ID | Epic | Sprints | Outcome |
|---|---|---|---|
| F1 | NSSF fixture loading | 10 | Real tender mapped in dev/test. |
| F2 | Deviation analysis | 10 | STD deviations are flagged. |
| F3 | Performance and security hardening | 10 | Release-blocking issues resolved. |
| F4 | UAT and release candidate | 10 | Module ready for formal UAT. |

---

## 20. Consolidated Task Backlog

This table is suitable for conversion into Jira, Linear, GitHub Issues, Azure DevOps, or another backlog tool.

| Task ID | Epic | Title | Priority | Sprint | Dependencies |
|---|---|---|---:|---:|---|
| S0-001 | A1 | Confirm repository/module structure | P0 | 0 | None |
| S0-002 | A1 | Configure CI pipeline | P0 | 0 | S0-001 |
| S0-003 | A2 | Import or mock STD Core adapter contract | P0 | 0 | S0-001 |
| S0-004 | A2 | Load IT STD seed package v0.2 fixture | P0 | 0 | S0-003 |
| S0-005 | F1 | Create NSSF dev/test fixture namespace | P1 | 0 | NSSF mapping |
| S0-006 | A1 | Define branch, PR, and migration policy | P0 | 0 | None |
| S0-007 | A3 | Create test users and roles | P0 | 0 | Permission seeds |
| S0-008 | A1 | Configure safety feature flags | P0 | 0 | Environment config |
| S1-001 | A2 | Implement `STDCoreAdapter` | P0 | 1 | S0-003 |
| S1-002 | A3 | Implement canonical JSON serializer | P0 | 1 | S1-001 |
| S1-003 | A3 | Implement `WizardHashService` | P0 | 1 | S1-002 |
| S1-004 | A3 | Implement `WizardAuditService` | P0 | 1 | S0-001 |
| S1-005 | A3 | Implement `WizardPermissionService` | P0 | 1 | S0-007 |
| S1-006 | A3 | Implement `WizardStateGuardService` | P0 | 1 | S1-005 |
| S1-007 | A3 | Implement typed error model | P0 | 1 | S1-005, S1-006 |
| S1-008 | A3 | Add foundation unit tests | P0 | 1 | S1-001-S1-007 |
| S2-001 | A4 | Create wizard instance/step/audit/hash models | P0 | 2 | S1 complete |
| S2-002 | A4 | Implement wizard instance creation | P0 | 2 | S2-001, S1-001 |
| S2-003 | A4 | Enforce immutable STD version binding | P0 | 2 | S2-002 |
| S2-004 | A4 | Generate wizard steps from package | P0 | 2 | S2-002 |
| S2-005 | A4 | Implement wizard progress service | P1 | 2 | S2-004 |
| S2-006 | A4 | Implement early workflow transitions | P0 | 2 | S1-006, S2-001 |
| S2-007 | A4 | Implement configuration instance APIs | P1 | 2 | S2-002, S2-006 |
| S2-008 | A5 | Build basic wizard shell UI | P1 | 2 | S2-007 |
| S2-009 | A4 | Add instance/lifecycle tests | P0 | 2 | S2-001-S2-008 |
| S3-001 | B1 | Create profile/TDS/SCC models | P0 | 3 | S2 complete |
| S3-002 | B1 | Implement tender identity service | P0 | 3 | S3-001 |
| S3-003 | B2 | Implement participation service | P0 | 3 | S3-001 |
| S3-004 | B3 | Implement tender date service | P0 | 3 | S3-001 |
| S3-005 | B4 | Implement security instrument service | P0 | 3 | S3-001 |
| S3-006 | B5 | Implement TDS service | P0 | 3 | S1-001, S3-001 |
| S3-007 | B5 | Implement SCC service | P0 | 3 | S1-001, S3-001 |
| S3-008 | B5 | Implement parameter history and audit | P0 | 3 | S3-006, S3-007 |
| S3-009 | B1-B5 | Implement profile/TDS/SCC APIs | P1 | 3 | S3-002-S3-007 |
| S3-010 | B1-B5 | Build profile/TDS/SCC UI | P1 | 3 | S3-009 |
| S3-011 | B1-B5 | Add profile/TDS/SCC tests | P0 | 3 | S3-001-S3-010 |
| S4-001 | C1 | Create requirement composer models | P0 | 4 | S3 complete |
| S4-002 | C1 | Create requirement groups from package | P0 | 4 | S4-001 |
| S4-003 | C1 | Implement requirement item CRUD | P0 | 4 | S4-001 |
| S4-004 | C2 | Implement requirement import | P1 | 4 | S4-003 |
| S4-005 | C3 | Implement requirement-evidence binding | P0 | 4 | S4-003 |
| S4-006 | C3 | Implement requirement-evaluation binding | P0 | 4 | S4-003 |
| S4-007 | C1 | Add requirement source/status display | P1 | 4 | S4-003 |
| S4-008 | C1-C3 | Implement requirement APIs | P1 | 4 | S4-002-S4-006 |
| S4-009 | C1-C3 | Build requirement composer UI | P1 | 4 | S4-008 |
| S4-010 | C1-C3 | Add requirement tests | P0 | 4 | S4-001-S4-009 |
| S5-001 | C4 | Create schedule/acceptance/payment models | P0 | 5 | S4 complete |
| S5-002 | C4 | Implement implementation schedule service | P0 | 5 | S5-001 |
| S5-003 | C4 | Implement milestone dependency cycle detection | P0 | 5 | S5-002 |
| S5-004 | C4 | Implement acceptance event service | P0 | 5 | S5-001 |
| S5-005 | C4 | Implement milestone payment binding service | P1 | 5 | S5-002 |
| S5-006 | C5 | Create system inventory models | P0 | 5 | S4 complete |
| S5-007 | C5 | Implement system inventory service | P0 | 5 | S5-006 |
| S5-008 | C6 | Create price schedule setup models | P0 | 5 | S5-006 |
| S5-009 | C6 | Implement price schedule service | P0 | 5 | S5-008 |
| S5-010 | C4-C6 | Implement schedule/inventory/price APIs | P1 | 5 | S5-002-S5-009 |
| S5-011 | C4-C6 | Build schedule/inventory/price UI | P1 | 5 | S5-010 |
| S5-012 | C4-C6 | Add schedule/inventory/price tests | P0 | 5 | S5-001-S5-011 |
| S6-001 | D1 | Create evaluation models | P0 | 6 | S5 complete |
| S6-002 | D1 | Implement evaluation configuration service | P0 | 6 | S6-001 |
| S6-003 | D1 | Implement scoring/pass-mark validation | P0 | 6 | S6-002 |
| S6-004 | D2 | Create qualification models | P0 | 6 | S6-001 |
| S6-005 | D2 | Implement qualification requirement service | P0 | 6 | S6-004 |
| S6-006 | D3 | Create form activation models | P0 | 6 | S6-001 |
| S6-007 | D3 | Implement form activation service | P0 | 6 | S6-006 |
| S6-008 | D4 | Implement evidence requirement service | P0 | 6 | S4, S6-004 |
| S6-009 | D5 | Implement supplier schema snapshot service | P0 | 6 | S6-007, S6-008 |
| S6-010 | D5 | Implement evaluation workspace snapshot service | P0 | 6 | S6-002, S6-005 |
| S6-011 | D1-D5 | Implement evaluation/forms/evidence APIs | P1 | 6 | S6-002-S6-010 |
| S6-012 | D1-D5 | Build evaluation/forms/evidence UI | P1 | 6 | S6-011 |
| S6-013 | D1-D5 | Add evaluation/forms/evidence tests | P0 | 6 | S6-001-S6-012 |
| S7-001 | E1-E2 | Create validation/review models | P0 | 7 | S6 complete |
| S7-002 | E1 | Implement full validation runner | P0 | 7 | S7-001 |
| S7-003 | E1 | Implement validation finding service | P0 | 7 | S7-002 |
| S7-004 | E1 | Implement manual finding resolution service | P0 | 7 | S7-003 |
| S7-005 | E2 | Implement review submission workflow | P0 | 7 | S7-002 |
| S7-006 | E2 | Implement review decision workflow | P0 | 7 | S7-005 |
| S7-007 | E2 | Implement approval gate tracker | P0 | 7 | S7-006 |
| S7-008 | E2 | Implement segregation-of-duties checks | P0 | 7 | S7-006 |
| S7-009 | E1-E2 | Implement validation/review APIs | P1 | 7 | S7-002-S7-008 |
| S7-010 | E1-E2 | Build validation/review UI | P1 | 7 | S7-009 |
| S7-011 | E1-E2 | Add validation/review tests | P0 | 7 | S7-001-S7-010 |
| S7-012 | E2 | Perform workflow security review | P0 | 7 | S7-011 |
| S8-001 | E3-E5 | Create preview/publication/handoff models | P0 | 8 | S7 complete |
| S8-002 | E3 | Implement preview service | P0 | 8 | S8-001 |
| S8-003 | E3 | Implement render service | P0 | 8 | S8-002 |
| S8-004 | E4 | Implement publication bundle service | P0 | 8 | S7 approvals, S8-003 |
| S8-005 | E4 | Enforce immutable publication bundles | P0 | 8 | S8-004 |
| S8-006 | E5 | Implement contract carry-forward service | P0 | 8 | S8-004 |
| S8-007 | E5 | Implement supplier response handoff | P0 | 8 | S6 snapshots, S8-004 |
| S8-008 | E5 | Implement evaluation workspace handoff | P0 | 8 | S6 snapshots, S8-004 |
| S8-009 | E4 | Implement tender binding service | P0 | 8 | S8-004 |
| S8-010 | E3-E5 | Implement preview/publication APIs | P1 | 8 | S8-002-S8-009 |
| S8-011 | E3-E5 | Build preview/publication UI | P1 | 8 | S8-010 |
| S8-012 | E3-E5 | Add preview/publication tests | P0 | 8 | S8-001-S8-011 |
| S8-013 | E4 | Product/legal review generated artifacts | P0 | 8 | S8-011 |
| S9-001 | E6 | Create addendum models | P0 | 9 | S8 complete |
| S9-002 | E6 | Implement addendum request service | P0 | 9 | S9-001 |
| S9-003 | E6 | Block post-publication edits outside addendum | P0 | 9 | S9-002 |
| S9-004 | E6 | Implement addendum impact analysis service | P0 | 9 | S9-002 |
| S9-005 | E6 | Implement addendum validation rules | P0 | 9 | S9-004 |
| S9-006 | E6 | Implement addendum review workflow | P0 | 9 | S9-005 |
| S9-007 | E6 | Implement addendum bundle service | P0 | 9 | S9-006 |
| S9-008 | E6 | Implement addendum publication service | P0 | 9 | S9-007 |
| S9-009 | E6 | Implement addendum APIs | P1 | 9 | S9-002-S9-008 |
| S9-010 | E6 | Build addendum UI | P1 | 9 | S9-009 |
| S9-011 | E6 | Add addendum tests | P0 | 9 | S9-001-S9-010 |
| S9-012 | E6 | Perform immutability security review | P0 | 9 | S9-011 |
| S10-001 | F1 | Implement NSSF calibration fixture service | P0 | 10 | S9 complete |
| S10-002 | F1 | Implement NSSF calibration mapping service | P0 | 10 | S10-001 |
| S10-003 | F2 | Implement calibration deviation service | P0 | 10 | S10-002 |
| S10-004 | F1-F2 | Run full NSSF calibration scenario | P0 | 10 | S10-001-S10-003 |
| S10-005 | F3 | Performance test critical services | P1 | 10 | S8, S9 |
| S10-006 | F3 | Accessibility and usability pass | P1 | 10 | UI complete |
| S10-007 | F3 | Perform final security review | P0 | 10 | S10-004 |
| S10-008 | F3 | Rehearse migration and rollback | P1 | 10 | All migrations complete |
| S10-009 | F3 | Finalize production feature-flag plan | P0 | 10 | S10-007 |
| S10-010 | F4 | Prepare UAT scripts | P1 | 10 | S10-004 |
| S10-011 | F4 | Create release candidate and release notes | P1 | 10 | S10-005-S10-010 |
| S10-012 | F4 | Run final smoke contracts | P0 | 10 | S10-011 |

---

## 21. Definition of Ready

A story is ready for sprint commitment only when:

1. The parent artifact is available and referenced.
2. The required model/service/API/UI behavior is clear.
3. Dependencies are completed or explicitly mocked.
4. Permission and state implications are known.
5. Acceptance criteria are testable.
6. Required seed data or fixtures are available.
7. The story does not require changing locked STD master content.
8. The story identifies whether it affects publication or addendum governance.

---

## 22. Definition of Done

A story is done only when:

1. Code is implemented in the agreed module location.
2. Database migration/model definition is included where required.
3. Server-side validation is implemented.
4. Permission checks are implemented.
5. State-transition checks are implemented where relevant.
6. Audit events are generated for material actions.
7. Hash evidence is generated where required.
8. Unit tests pass.
9. Integration tests pass for affected services/APIs.
10. UI behavior is tested where applicable.
11. Documentation or inline developer notes are updated.
12. No direct edit path exists for locked STD content or published artifacts.
13. PR has been reviewed against the non-negotiable controls.

---

## 23. Test Strategy by Sprint

| Sprint | Required tests |
|---|---|
| 0 | CI smoke, fixture loading, role setup. |
| 1 | Adapter, hash determinism, audit event, permission, state guard unit tests. |
| 2 | Instance creation, version immutability, step generation, lifecycle transition tests. |
| 3 | Parameter validation, TDS/SCC binding, date-order, security amount/validity, history tests. |
| 4 | Requirement code uniqueness, import validation, evidence/evaluation binding, soft delete tests. |
| 5 | Milestone dependency cycles, acceptance events, inventory-price binding, recurrent cost validation. |
| 6 | Evaluation totals, pass mark, form activation, evidence propagation, snapshot hash tests. |
| 7 | Full validation, blockers, review decisions, approval gates, segregation-of-duties tests. |
| 8 | Preview generation, publication gating, artifact immutability, hash manifest, handoff tests. |
| 9 | Post-publication edit block, addendum impact, addendum review, immutable addendum tests. |
| 10 | NSSF calibration scenario, performance checks, security checks, final smoke contracts. |

---

## 24. Critical Smoke Contracts

These smoke contracts must be automated before release candidate approval.

| ID | Smoke contract | Expected result |
|---|---|---|
| SC-WIZ-001 | Create wizard instance from active/test IT STD package. | Instance is created with immutable `std_version_id`. |
| SC-WIZ-002 | Attempt to change bound STD version after creation. | Request is rejected and audited. |
| SC-WIZ-003 | Enter incomplete mandatory TDS values and run validation. | Blocking findings are produced. |
| SC-WIZ-004 | Attempt review submission with blockers. | Submission is blocked. |
| SC-WIZ-005 | Complete required configuration and run validation. | No blocker findings remain. |
| SC-WIZ-006 | Submit for review and approve through configured gates. | State changes are audited. |
| SC-WIZ-007 | Attempt conflicting approval by same actor where segregation rule applies. | Request is rejected. |
| SC-WIZ-008 | Generate preview bundle. | Bundle is marked non-authoritative and hashable. |
| SC-WIZ-009 | Publish approved configuration. | Immutable publication bundle and hash manifest are created. |
| SC-WIZ-010 | Attempt to edit published artifact directly. | Request is rejected. |
| SC-WIZ-011 | Generate supplier response schema. | Schema contains activated forms, evidence requirements, requirements matrix, and price schedule. |
| SC-WIZ-012 | Generate evaluation workspace. | Workspace contains responsiveness, technical, financial, and qualification structures. |
| SC-WIZ-013 | Generate contract carry-forward package. | Package contains SCC, price, acceptance, securities, IP/software, and appendices data. |
| SC-WIZ-014 | Open addendum request after publication. | Addendum request is created and original bundle remains immutable. |
| SC-WIZ-015 | Run addendum impact analysis. | Affected sections/forms/schemas/artifacts are identified. |
| SC-WIZ-016 | Publish approved addendum. | Immutable addendum bundle and separate hash evidence are created. |
| SC-WIZ-017 | Load NSSF ERP fixture in test mode. | Fixture maps without mutating master STD records. |
| SC-WIZ-018 | Attempt to load NSSF fixture in production mode. | Request is rejected. |

---

## 25. Cursor Task Prompt Sequence

Use these task prompts in order. Do not skip governance tasks to build UI first.

### Prompt 1 — Sprint 1 Foundation

```text
Implement Sprint 1 for the IT Tender Configuration Wizard.
Focus only on STDCoreAdapter, canonical serialization, WizardHashService, WizardAuditService, WizardPermissionService, WizardStateGuardService, typed errors, and tests.
Do not implement user-facing wizard screens yet.
Ensure hash determinism, audit event persistence, role/action permission checks, and invalid transition rejection.
```

### Prompt 2 — Sprint 2 Wizard Instance and Lifecycle

```text
Implement Sprint 2 for the IT Tender Configuration Wizard.
Create the wizard instance, wizard step, progress, audit, and hash evidence models.
Implement instance creation from an active or test-mode IT STD package.
Generate wizard steps from package metadata.
Make std_version_id immutable after creation.
Implement early lifecycle transitions through WizardWorkflowService only.
Add tests for creation, step generation, version immutability, and direct state mutation rejection.
```

### Prompt 3 — Sprint 3 Structured Tender Profile

```text
Implement Sprint 3 for the IT Tender Configuration Wizard.
Build tender identity, participation, dates, security instrument, TDS values, SCC values, value history, APIs, and UI screens.
All TDS and SCC schemas must be read from STD Core through the adapter.
Persist only tender-specific values.
Add tests for required fields, date ordering, amount/validity rules, value history, and audit.
```

### Prompt 4 — Sprint 4 Requirement Composer

```text
Implement Sprint 4 for the IT Tender Configuration Wizard.
Build the requirement composer models, services, APIs, and UI.
Support requirement groups, requirement items, requirement import validation, source/status display, evidence binding, and evaluation binding.
Do not allow free-form legal document editing.
Add tests for requirement code uniqueness, import row validation, evidence binding, evaluation binding, and soft delete audit.
```

### Prompt 5 — Sprint 5 Schedule, Inventory, and Price

```text
Implement Sprint 5 for the IT Tender Configuration Wizard.
Build implementation phase, milestone, deliverable, acceptance event, dependency, payment binding, system inventory, price schedule, recurrent cost models, services, APIs, and UI.
Implement dependency cycle detection and deterministic price summaries.
Add tests for milestone date rules, dependency cycles, inventory-price bindings, recurrent cost periods, and payment total rules.
```

### Prompt 6 — Sprint 6 Evaluation, Forms, Evidence, and Snapshots

```text
Implement Sprint 6 for the IT Tender Configuration Wizard.
Build evaluation configuration, qualification requirements, form activation, evidence requirements, supplier schema snapshot, and evaluation workspace snapshot.
Activated forms must follow package rules and tender configuration.
Snapshots must be deterministic and hashable.
Add tests for scoring totals, pass mark, form activation, evidence propagation, and snapshot hash determinism.
```

### Prompt 7 — Sprint 7 Validation and Review

```text
Implement Sprint 7 for the IT Tender Configuration Wizard.
Build full validation runner, validation findings, manual finding resolution, review submission, review decisions, approval gates, and segregation-of-duties checks.
Blockers must prevent review submission.
Review decisions must be audited.
Add tests for blockers, warnings, manual resolution permissions, review decisions, approval gates, and segregation-of-duties enforcement.
```

### Prompt 8 — Sprint 8 Preview, Publication, and Carry-Forward

```text
Implement Sprint 8 for the IT Tender Configuration Wizard.
Build preview generation, deterministic rendering, publication bundle generation, immutable artifact enforcement, supplier response handoff, evaluation workspace handoff, contract carry-forward package, tender binding, APIs, and UI.
Publication must require clean validation and completed approvals.
Published bundles must be immutable and hash-verifiable.
Add tests for preview, publication gates, immutable artifacts, hash manifest, downstream handoffs, and tender binding.
```

### Prompt 9 — Sprint 9 Addendum

```text
Implement Sprint 9 for the IT Tender Configuration Wizard.
Build addendum request, post-publication edit blocking, impact analysis, addendum validation, addendum review, addendum bundle generation, addendum publication, APIs, and UI.
Original publication bundles must remain immutable.
Addendum bundles must be separately hashed and immutable.
Add tests for direct edit blocking, impact analysis, addendum review, addendum publication, and immutability.
```

### Prompt 10 — Sprint 10 Calibration and Hardening

```text
Implement Sprint 10 for the IT Tender Configuration Wizard.
Build the NSSF ERP calibration fixture loader, mapping service, deviation service, full calibration scenario, performance checks, final security checks, migration rollback rehearsal, UAT scripts, and release candidate preparation.
The NSSF fixture must be dev/test only and must not mutate master STD records.
Run all smoke contracts and document any remaining release risks.
```

---

## 26. Risk Register

| Risk | Severity | Mitigation |
|---|---|---|
| UI is built before governance and validation are stable. | High | Enforce sprint sequence; no publication UI before validation/review services pass. |
| Developers hard-code NSSF ERP-specific logic. | High | Treat NSSF as fixture only; add tests that require generic package-driven behavior. |
| Wizard mutates master STD records. | Critical | Adapter must expose read-only master objects; write services only persist tender-specific values. |
| Published artifacts remain editable through generic update endpoints. | Critical | Add immutability guard at model/service/API levels and test bypass paths. |
| Addendum impact analysis misses downstream artifacts. | High | Include supplier schema, evaluation workspace, contract carry-forward, price schedules, forms, and requirements in impact tests. |
| Hash evidence is non-deterministic. | High | Use canonical serialization and deterministic ordering in tests. |
| Permissions are enforced only in UI. | Critical | Enforce permissions server-side on every write and transition. |
| Draft/test STD package accidentally enabled for production publication. | High | Use environment feature flags and package activation checks. |
| Requirement import creates inconsistent data. | Medium | Require import preview and row-level validation before commit. |
| Price/recurrent-cost model is oversimplified. | Medium | Validate against official IT STD price schedule model and NSSF ERP calibration fixture. |

---

## 27. Open Decisions Before Sprint 1

| Decision | Owner | Required by | Notes |
|---|---|---|---|
| Final application framework mapping for models/services/APIs. | Technical Lead | Sprint 1 | Determines migrations and service structure. |
| STD Core adapter implementation vs mock boundary. | Technical Lead | Sprint 1 | Mock is acceptable for early development if contract is stable. |
| Test package activation strategy. | Product + Technical Lead | Sprint 1 | Need safe test-mode binding without production activation. |
| Role names in target identity system. | Security/Product | Sprint 1 | Must map to seed roles and permission matrix. |
| Artifact storage backend. | Technical Lead | Sprint 8 | Required for preview/publication bundle storage. |
| Hash algorithm and canonical payload standard. | Technical Lead/Security | Sprint 1 | Recommended: SHA-256 over canonical JSON/bytes plus algorithm metadata. |
| UAT environment and users. | Product Owner | Sprint 10 | Needed for release candidate. |

---

## 28. Recommended First Implementation Cut

The first implementation cut should include Sprints 0–2 only.

Reason: the platform must first prove that it can create a wizard instance, bind to an STD version, generate steps, enforce roles, enforce state transitions, audit actions, and prevent direct template mutation.

Do not start with requirements UI or price tables. Those are important, but they depend on the foundation being right.

Minimum demonstrable outcome after Sprint 2:

1. A user with the correct role can create an IT tender configuration wizard instance.
2. The instance binds to exactly one STD version.
3. The generated wizard steps match package metadata.
4. The user can view read-only source/package identity.
5. Unauthorized users cannot create or transition the instance.
6. The bound STD version cannot be changed.
7. All actions are audited.
8. Direct state mutation is blocked.

---

## 29. Final Delivery Gate

The IT Tender Configuration Wizard is not production-ready until all of the following are true:

1. All P0 tasks are complete.
2. All P0 smoke contracts pass.
3. Full validation blocks incomplete or invalid configurations.
4. Review and approval gates work with segregation-of-duties enforcement.
5. Publication bundle generation is hash-verifiable and immutable.
6. Addendum flow is the only route for post-publication changes.
7. NSSF ERP calibration maps cleanly without mutating the master STD model.
8. Security review has no unresolved P0/P1 findings.
9. Production feature flags prevent draft/test package misuse.
10. UAT scripts are executed and accepted.

---

## 30. Next Artifact After This Document

The next practical artifact should be:

**IT Tender Configuration Wizard — Jira/Linear Import Backlog CSV**

That artifact should convert the consolidated task backlog into a machine-importable CSV with columns such as:

1. Issue key
2. Issue type
3. Epic
4. Summary
5. Description
6. Priority
7. Sprint
8. Dependencies
9. Acceptance criteria
10. Labels
11. Component
12. Estimate

