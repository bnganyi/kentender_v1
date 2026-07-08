# KenTender Cursor Rules — All-in-One Copy File

This file combines the Cursor rules from the `.cursor/rules` folder for easy review. For actual use, copy the individual `.mdc` files into `.cursor/rules/` at the repository root.


---

## 001-project-architecture.mdc

```mdc
---
description: KenTender STD Engine architecture guardrails
alwaysApply: true
---

# KenTender STD Engine Architecture Guardrails

This repository implements the KenTender Standard Tender Document Engine and related procurement workflows.

## Architectural hierarchy

The platform must preserve this hierarchy:

1. Official STD source document
2. STD Template Family
3. STD Template Version
4. STD sections, clauses, parameters, rules, forms, render blocks, and schemas
5. Tender-specific STD configuration instance
6. Generated tender document bundle
7. Supplier response
8. Evaluation record
9. Contract formation and carry-forward records

Tender Management must consume STD Engine outputs. Tender Management must not independently recreate locked clauses, legal rules, eligibility rules, evaluation logic, forms, or contract carry-forward fields that belong to the STD Engine.

## Generalization requirement

The STD Engine must support multiple STD families. Do not hard-code behavior for only the Information Technology STD, Works STD, Goods STD, Services STD, or any single tender.

Permitted pattern:

- Generic STD Engine model/service/rule/render behavior.
- STD-family-specific seed package, parameters, forms, requirements, and validation rules.
- Tender-specific configuration values bound to one active STD version.

Forbidden pattern:

- `if std_type == "IT"` logic inside core lifecycle, source trace, approval, audit, import, or rendering infrastructure unless implemented through an explicit plugin/extension registry.
- Treating the NSSF ERP tender or any actual tender as a master STD.
- Storing the complete production STD as one opaque JSON blob without normalized lifecycle, governance, audit, trace, and queryable records.

## Implementation sequence

Follow this order unless explicitly instructed otherwise:

1. STD Engine Core
2. STD package import/export
3. IT STD package import and validation
4. IT Tender Configuration Wizard
5. Supplier response integration
6. Evaluation integration
7. Contract formation integration

Do not implement wizard features before the corresponding core STD Engine services exist.

## Required module boundaries

Keep these concerns separate:

- Template/version lifecycle
- Source document traceability
- Section and clause registry
- Parameter schema and configuration values
- Rule validation engine
- Form schema engine
- Requirement composer
- Price schedule engine
- Render engine
- Approval/governance workflow
- Tender binding
- Addendum/supersession
- Audit/hash evidence

```

---

## 002-procurement-governance.mdc

```mdc
---
description: Procurement governance, approvals, immutability, and legal traceability rules
alwaysApply: true
---

# Procurement Governance Rules

The system is government-facing and must preserve legal defensibility, auditability, source traceability, and approval discipline.

## Non-negotiable governance rules

- Active STD versions are immutable.
- Published generated tender bundles are immutable.
- Used STD versions cannot be deleted.
- Only approved STD versions may become active.
- Only active STD versions may be bound to new tenders.
- Superseded STD versions must remain readable for tenders that already used them.
- Post-publication tender changes must be handled through addendum/supersession, not direct mutation.
- Locked ITT/GCC sections cannot be edited by tender users.
- TDS and SCC are controlled configuration surfaces, not free-form clause override areas.
- Any master-template change after activation must create a new version or follow an approved correction workflow.

## Required lifecycle behavior

STD Template Version lifecycle must be enforced by service-layer transition validators and persistence-layer constraints where possible.

Typical lifecycle:

- DRAFT
- STRUCTURING
- INTERNAL_REVIEW
- LEGAL_REVIEW
- PROCUREMENT_REVIEW
- APPROVED
- ACTIVE
- SUSPENDED
- SUPERSEDED
- ARCHIVED

Tender STD Configuration lifecycle must also be enforced:

- NOT_STARTED
- IN_CONFIGURATION
- VALIDATION_FAILED
- READY_FOR_REVIEW
- PROCUREMENT_REVIEW
- APPROVED_FOR_TENDER_CREATION
- BOUND_TO_TENDER
- PUBLISHED
- ADDENDUM_REQUIRED
- SUPERSEDED_BY_ADDENDUM

## Approval and state-transition design

Before implementing any feature that changes status, approval, publication, activation, supersession, archive, binding, or addendum behavior, verify:

1. Who is allowed to perform the transition.
2. What prior state is required.
3. What validations must pass.
4. What audit event is emitted.
5. Whether the action mutates immutable records.
6. Whether generated artifacts require a new hash.
7. Whether source traceability is affected.

Do not create bypass endpoints, admin shortcuts, fixtures, scripts, or migrations that can activate, publish, supersede, or archive records without the same governance checks unless the operation is explicitly marked as a controlled migration with audit evidence.

## Legal-source traceability

Every clause, parameter, rule, form, render block, and generated artifact should be traceable to:

- STD source document
- STD source version
- Section reference
- Page/anchor reference where available
- Extracted text hash where applicable
- Import package version
- Review/approval event

If source trace data is missing, mark the object as incomplete and not activatable.

```

---

## 003-domain-modeling-and-storage.mdc

```mdc
---
description: Domain modeling and data storage rules for STD Engine implementation
alwaysApply: true
---

# Domain Modeling and Data Storage Rules

The production system must use normalized, auditable, queryable records. JSON packages are import/export artifacts, not the primary source of runtime truth.

## Storage principles

Use a hybrid model:

- Relational/domain records for identity, lifecycle, relationships, governance, audit, permissions, and search.
- JSON schema fields for complex parameter constraints, form-field schemas, validation expressions, render metadata, and requirement structures.
- Immutable content blobs or content records for locked legal text, rendered artifacts, and source snapshots.
- Hashes for source files, clause text, package contents, rendered bundles, and published artifacts.
- Event logs for import, review, approval, activation, use, publication, addendum, supersession, and archive actions.

## Core entity groups

Keep these groups explicit:

- STD Template Family
- STD Template Version
- STD Source Document
- STD Source Anchor
- STD Section
- STD Clause
- STD Parameter
- STD Parameter Option
- STD Rule
- STD Form Schema
- STD Form Field
- STD Evidence Requirement
- STD Requirement Schema
- STD Price Schedule Schema
- STD Evaluation Schema
- STD Contract Schema
- STD Render Block
- STD Approval Event
- STD Audit Event
- STD Package Import Job
- Tender STD Instance
- Tender STD Configuration Value
- Tender STD Validation Finding
- Tender Generated Bundle
- Tender Addendum Impact

## Mutability classification

Every section, clause, parameter, form, requirement, price schedule, render block, and generated artifact must have a mutability classification where relevant.

Common classifications:

- LOCKED
- PARAMETERIZED
- CONTROLLED_CONFIG
- PE_AUTHORED_CONTROLLED
- BIDDER_RESPONSE
- SYSTEM_GENERATED
- CONTRACT_CARRY_FORWARD
- REFERENCE_ONLY

Do not use a generic editable text field for legally controlled content.

## Import/export package behavior

Import packages may contain JSON files, but after import they must resolve into domain records with:

- Stable IDs
- Version references
- Parent-child relationships
- Source anchors
- Validation status
- Hashes
- Audit events

Do not implement runtime behavior that depends on parsing a monolithic package JSON on every request.

## Database migration discipline

When changing persistence models:

- Add migrations.
- Preserve existing data.
- Add indexes for frequently queried lifecycle, version, family, section, source, and tender-binding fields.
- Add uniqueness constraints where required by the domain model.
- Enforce immutability through service checks and database constraints/triggers where feasible.
- Do not silently rename or drop fields that are part of audit, source trace, lifecycle, or hash evidence.

```

---

## 004-code-quality-and-scope-control.mdc

```mdc
---
description: Code quality, scope control, and implementation discipline
alwaysApply: true
---

# Code Quality and Scope Control

Work in small, reviewable vertical slices. Do not broaden scope during implementation.

## Task discipline

For each implementation task:

1. Read only the relevant context documents and source files.
2. Produce a plan when requested before editing files.
3. Modify only files required for the task.
4. Add or update tests.
5. Run relevant checks where available.
6. Update `docs/MODULE_STATUS.md` when module status changes.
7. Stop after completing the bounded task.

## Forbidden behavior

Do not:

- Implement multiple unrelated tickets in one pass.
- Make opportunistic refactors outside the task scope.
- Rewrite large modules without being asked.
- Replace domain-specific governance with generic CRUD behavior.
- Use mock success paths that bypass real validation.
- Leave TODOs in critical governance, immutability, audit, source trace, or security code without explicitly reporting them.
- Mark incomplete features as complete.
- Hide failing tests.
- Claim tests were run when they were not.

## Coding expectations

Prefer:

- Small services with explicit names.
- Deterministic validators.
- Clear error types and messages.
- Idempotent import operations where practical.
- Explicit state-transition functions.
- Version-aware reads and writes.
- Audit event emission inside authoritative service operations.
- Tests for both positive and negative paths.

## Error handling

Errors must distinguish:

- Validation failure
- Permission failure
- Invalid lifecycle transition
- Immutable record mutation attempt
- Source trace incompleteness
- Import package defect
- Referential integrity defect
- Render failure
- Hash/checksum mismatch
- Activation blocker

Do not collapse all failures into generic exceptions.

```

---

## 005-testing-and-smoke-contracts.mdc

```mdc
---
description: Testing and smoke-contract requirements for STD Engine tasks
alwaysApply: true
---

# Testing and Smoke Contracts

A task is incomplete unless it includes appropriate tests or explicitly explains why no test can be added.

## Required test categories

Use the strongest applicable category:

- Unit tests
- Integration tests
- Migration tests
- Permission tests
- State-transition tests
- Import dry-run tests
- Validation-rule tests
- Render snapshot tests
- Hash/checksum tests
- Addendum/supersession tests
- Smoke-contract tests

## Critical smoke contracts

Maintain and expand tests for these behaviors:

- Draft STD package can import into DRAFT/STRUCTURING state.
- Draft STD package cannot be activated.
- Only APPROVED STD versions can become ACTIVE.
- ACTIVE STD versions cannot be edited.
- ACTIVE STD versions cannot be deleted.
- Used STD versions cannot be deleted.
- Superseded STD versions remain readable.
- Tender cannot bind to DRAFT or STRUCTURING STD version.
- Tender can bind only to ACTIVE STD version.
- Published generated tender bundle cannot be mutated.
- Addendum must create a new superseding generated artifact or affected-section replacement.
- Locked ITT/GCC clauses cannot be edited from tender configuration.
- Missing source anchor blocks activation where source trace is mandatory.
- Missing clause hash blocks activation where clause hashing is mandatory.
- Calibration fixture cannot be imported as a master STD package.
- NSSF ERP tender data remains tender-instance/calibration data, not master template data.

## Test design

For every validator, include:

- Valid case
- Invalid case
- Boundary case
- Permission-denied case where applicable
- Immutable-state case where applicable

For every import job, include:

- Valid package structure
- Missing file
- Invalid JSON/schema
- Bad reference
- Duplicate stable ID
- Checksum mismatch
- Draft-only activation blocker

For every renderer, include:

- Deterministic render output
- Missing parameter failure
- Locked text preservation
- Hash generation
- Published artifact immutability

## Completion reporting

At the end of a task, report:

- Tests added
- Checks run
- Results
- Known failures
- Follow-up tasks

Never claim that tests pass unless they were actually executed or clearly state that execution was not available.

```

---

## 006-task-protocol.mdc

```mdc
---
description: Cursor task execution protocol for KenTender work
alwaysApply: true
---

# Cursor Task Execution Protocol

Use this protocol for implementation tasks.

## Planning phase

When asked to implement a task, first produce a plan if the prompt requests planning or if the task touches governance, lifecycle, storage, permissions, import/export, rendering, published artifacts, or contracts.

The plan must include:

1. Files expected to change.
2. Interfaces, classes, services, functions, endpoints, or schemas to add/change.
3. Tests to add/change.
4. Data migrations or seed updates required.
5. Risks, blockers, or ambiguities.
6. Governance and immutability impact.
7. Confirmation that scope is bounded.

Do not edit files until the user approves the plan when the prompt says to plan first.

## Implementation phase

During implementation:

- Stay inside the approved scope.
- Do not make unrelated refactors.
- Prefer small, explicit commits/changesets if the workflow supports them.
- Keep generated code and hand-written code clearly separated where applicable.
- Keep STD-family-specific logic out of generic engine code unless implemented through configured schemas/rules/plugins.

## Verification phase

After implementation, review your own work against acceptance criteria.

Report:

1. What changed.
2. Files modified.
3. Tests added or updated.
4. Commands run.
5. Results of checks.
6. Any assumptions.
7. Any unresolved issues.
8. Follow-up tasks created.

## Scope escalation

If a task requires changing broader architecture, state-transition rules, domain model boundaries, or security assumptions, stop and ask before proceeding.

```

---

## 007-import-export-rendering.mdc

```mdc
---
description: STD package import/export and rendering rules
alwaysApply: true
---

# STD Package Import, Export, and Rendering Rules

The package system must be deterministic, auditable, and activation-gated.

## Package principles

An STD package is an import/export representation of a template version. It is not the production runtime database.

Every package import must:

- Validate manifest.
- Validate package schema version.
- Validate file presence.
- Validate JSON syntax and schema.
- Validate checksums.
- Validate stable IDs.
- Validate references.
- Validate lifecycle status.
- Validate source trace completeness.
- Validate activation blockers.
- Emit import audit events.
- Produce a dry-run report before destructive or authoritative import where applicable.

## Draft-only packages

Packages marked as draft, skeleton, calibration, or not-activatable must never become ACTIVE through import.

The IT seed package v0.2 is draft/import-test material only unless a later approved package explicitly removes activation blockers after review.

## Source trace and hashes

Do not mark an STD package activatable unless required source trace and hash evidence exist:

- Source document hash
- Package checksum
- Clause text hash where clause text is authoritative
- Section/source anchors
- Rule source anchors where legal/procurement rules are extracted from the STD
- Render block identity and output hash for generated artifacts

## Rendering rules

Rendering must be deterministic.

Generated documents must preserve:

- Locked clause text
- Section order
- Legal numbering where applicable
- TDS/SCC parameter substitutions
- Requirement tables
- Form schemas
- Price schedules
- Evaluation criteria
- Contract carry-forward fields

Published render outputs must be immutable and hashed.

Do not render from ad hoc user text when the content is supposed to come from an approved STD template, controlled parameter, or structured requirement schema.

## Addendum rendering

Post-publication changes must generate addendum/supersession records identifying:

- Affected sections
- Affected clauses
- Affected forms
- Affected requirements
- Affected price schedules
- Affected evaluation criteria
- Affected contract carry-forward fields
- Previous artifact hash
- Superseding artifact hash

```

---

## 008-security-audit-evidence.mdc

```mdc
---
description: Security, audit, and evidentiary integrity requirements
alwaysApply: true
---

# Security, Audit, and Evidentiary Integrity

This system must support government-grade audit trails and defensible procurement records.

## Audit requirements

Every authoritative action must emit an audit event where applicable:

- Source document upload/registration
- Package import dry run
- Package import commit
- Validation execution
- Review submission
- Review approval/rejection
- Version activation
- Version suspension
- Version supersession
- Version archive
- Tender binding
- Configuration update
- Generated bundle creation
- Publication
- Addendum creation
- Supersession
- Contract carry-forward generation
- Permission-sensitive access

Audit events should include:

- Actor
- Role/context
- Timestamp
- Entity type
- Entity ID
- Previous state where relevant
- New state where relevant
- Reason/comment where required
- Request/correlation ID where available
- Hash/checksum where relevant

## Security principles

- Use least privilege.
- Protect approval, activation, publication, addendum, archive, and deletion actions.
- Do not expose internal IDs when stable public IDs or references should be used.
- Do not allow tender users to edit locked STD legal content.
- Do not allow calibration fixtures to be imported as official templates.
- Do not create hidden admin bypasses.
- Do not log secrets, credentials, tokens, private keys, or sensitive integration data.

## Evidence preservation

Preserve evidence for:

- Which STD version was used by a tender.
- Which source document supported the STD version.
- Which parameters were configured.
- Which validations passed or failed.
- Which generated document was published.
- Which addendum superseded which content.
- Which contract terms were carried forward from tender/award.

## Deletion rules

Prefer soft delete or archival for legally relevant records.

Never hard-delete:

- Active STD versions
- Used STD versions
- Published generated bundles
- Approval events
- Audit events
- Source documents used by activated templates
- Tender bindings
- Addendum/supersession records

```

---

## 009-ui-ux-government-workflows.mdc

```mdc
---
description: UI/UX rules for controlled government procurement workflows
alwaysApply: false
---

# UI/UX Rules for Government Procurement Workflows

Apply this rule when implementing user interfaces, screens, forms, wizards, review queues, preview pages, validation panels, or publication flows.

## UI principles

The UI must guide users through controlled configuration. It must not expose legal template editing as ordinary form editing.

Use wizard and review flows for:

- Tender identity
- Procurement method and participation
- Dates, clarifications, and meetings
- Tender security or equivalent instrument
- Lots, alternatives, reservations, and preference settings
- Requirements authoring
- Technical specification authoring
- Implementation schedule
- System inventory
- Price schedule setup
- Evaluation criteria
- Qualification requirements
- Contract/SCC parameters
- Forms and evidence
- Validation
- Preview
- Approval
- Publication

## Locked content behavior

For locked sections:

- Show read-only preview.
- Explain that the section is controlled by the active STD version.
- Do not show edit controls.
- Direct users to TDS/SCC or approved configuration surfaces for permitted changes.

## Validation UX

Validation findings must be clear and actionable:

- BLOCKER
- ERROR
- WARNING
- INFO

For each finding show:

- Affected section/field.
- Rule violated.
- Required correction.
- Whether publication is blocked.
- Link to the relevant wizard step.

## Review and approval UX

Approval screens must show:

- Current lifecycle state.
- Pending action.
- Required role.
- Validation summary.
- Source STD version.
- Generated preview hash where available.
- Prior approvals/rejections.
- Required comments for rejection or exceptional decisions.

Do not allow approval actions from list screens without enough context to make a legally defensible decision.

```

---

## 010-documentation-status-discipline.mdc

```mdc
---
description: Documentation and status-update discipline
alwaysApply: true
---

# Documentation and Status Discipline

Keep the documentation set synchronized with implementation.

## Required status file

Maintain:

- `docs/MODULE_STATUS.md`

Update it when a task changes:

- Models
- Migrations
- Services
- APIs
- UI screens
- Import/export behavior
- Validation behavior
- Rendering behavior
- Governance/state transitions
- Permissions
- Tests
- Known blockers

## Required decision log

For architectural decisions, update:

- `docs/DECISION_LOG.md`

Record:

- Decision
- Reason
- Alternatives considered
- Consequences
- Date
- Related task ID

## Documentation hierarchy

Do not scatter core project truth across random comments or temporary notes.

Use:

- `docs/PROJECT_INDEX.md` for navigation.
- `docs/IMPLEMENTATION_SEQUENCE.md` for build order.
- `docs/MODULE_STATUS.md` for current status.
- `docs/DECISION_LOG.md` for durable decisions.
- Module folders for PRDs, domain models, governance, API/service contracts, implementation packs, and smoke contracts.

## Completion reporting

At the end of each task, summarize:

- What changed.
- What was tested.
- What remains.
- Whether module status changed.
- Any follow-up tasks.

Do not leave the user guessing about task completeness.

```
