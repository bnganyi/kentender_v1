# KenTender STD Engine Backend Import & Wiring Cursor Pack

## Purpose

This pack gives Cursor a tractable implementation path for wiring the backend of the KenTender STD Engine after the UI designs have been implemented.

The recommended approach is:

```text
Read-first.
Import-first.
Immutable-first.
Visualize the official IT STD before building editing, approval workflow, supersession, or live tender generation.
```

The immediate goal is **not** to build the full workflow engine. The immediate goal is to load the Information Technology Standard Tender Document package into the database, expose read-only APIs, and prove that every STD Engine screen can display real data.

---

## Non-negotiable architectural rules

1. The official STD is the legal master.
2. NSSF ERP and other real tenders are calibration fixtures only. They must not define or corrupt the master STD model.
3. Active STD versions are immutable.
4. Published tender bundles are immutable.
5. Post-publication changes must go through addendum/supersession governance.
6. Tender Management consumes STD Engine outputs; it must not recreate legal STD logic manually.
7. The first backend milestone must be read-only.
8. Every imported object must be traceable to a source document, source anchor, or explicit validation finding.
9. The importer must not silently invent missing legal data.
10. All imports, validations, and package checks must create audit events.

---

## Recommended first milestone

### Milestone 1: IT STD read model

Build only this first:

```text
Import IT STD package
Persist canonical STD records
Verify package/file/source hashes where available
Expose read-only APIs
Wire the implemented UI screens to real backend data
Persist validation findings
Persist audit events
Display the STD package across the designed UI
```

Do not build yet:

```text
Editing
Draft change requests
Approval workflow
Supersession execution
Addendum generation
Role-based approval decisioning
Live tender generation
Tender publication
```

Milestone 1 is complete only when:

```text
The official IT STD package is loaded.
STD Library shows the imported package.
STD Version Detail opens real version data.
Source Traceability shows source documents/anchors.
Section and Clause Map shows real sections and clauses.
Clause Detail shows real clause text and hash/source metadata.
Parameter, Rule, Form, Requirement, Price, Evaluation, and Render Block screens show real data.
Validation Report shows persisted findings.
Audit Log shows persisted import/validation events.
The UI is wired read-only.
No editing/workflow is required to understand the STD.
```

---

## Package/version convention

The current seed package artifacts are based on the official Information Technology STD revision from April 2022.

Use this as the canonical first backend seed unless the project intentionally creates a later package version:

```text
Family Code: KE-PPRA-IT
Version Code: 2022-04
Package ID: KE-PPRA-IT-2022-04
Lifecycle State for first visualization: ACTIVE
Mutability: READ_ONLY
```

Some UI mockups used `KE-PPRA-IT-2024-04` as placeholder data. Treat that as mock UI text unless a real 2024 package is intentionally created.

---

## Existing artifacts to use

Place these files in a repository folder such as:

```text
/seed-packages/std-it/
/docs/std-it/
/docs/calibration/
/docs/cursor/
```

### Preferred import candidate

```text
KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip
```

Role:

```text
Canonical candidate for the first backend import.
Use for dry-run, commit import, validation, and UI wiring.
```

### Earlier skeleton package

```text
KE-PPRA-IT-2022-04_Seed_Package_Skeleton.zip
```

Role:

```text
Fallback structure reference only.
Do not prefer it over v0_2 for real import unless v0_2 is unavailable.
```

### Expanded v0.2 package directory

```text
KE-PPRA-IT-2022-04_seed_package_v0_2/
  README.md
  VERSION_NOTES_v0_2.md
  IMPORT_DRY_RUN_REPORT_TEMPLATE.md
```

Role:

```text
Human-readable package notes and dry-run reporting template.
Use to define importer diagnostics and report output.
```

### Official source documents

```text
DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.doc
it_std_extract/DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.pdf
```

Role:

```text
Legal/source basis for the IT STD package.
Use for source document registration, source hash tracking, and source anchor validation.
```

### Extraction and reconciliation references

```text
STD_IT_Extraction_Matrix.md
STD_IT_Seed_Package_Specification.md
STD_IT_Full_Source_Extraction_Pass_1.md
STD_IT_Full_Source_Extraction_Pass_2.md
STD_IT_Full_Source_Extraction_Pass_3.md
STD_IT_Full_Source_Extraction_Pass_4.md
STD_IT_Full_Source_Extraction_Pass_5.md
STD_IT_Package_Reconciliation_and_Import_Ready_Update_Plan.md
STD_IT_Package_Validation_Report_v0_2.md
```

Role:

```text
Use as reference material to confirm what should be present in the import package.
Do not treat Markdown extraction notes as the database source of truth if the packaged JSON/seed files are available.
```

### Calibration-only reference

```text
NSSF_ERP_Calibration_Mapping.md
NSSF SPS RFP ERP 2026(1).pdf
```

Role:

```text
Calibration only.
Do not import as an STD family/version.
Use only later to test whether the STD Engine can support realistic IT tender configuration.
```

### Cursor/repository rules

```text
KenTender_Cursor_Rules_Pack.zip
```

Role:

```text
Repository discipline and Cursor rules.
Not an STD import package.
Do not feed this into the STD data importer.
```

---

## Repository layout to create

Use this target structure. Adapt names if the project already has a framework convention, but keep the separation clear.

```text
/docs/
  PROJECT_INDEX.md
  IMPLEMENTATION_SEQUENCE.md
  DECISION_LOG.md
  SMOKE_CONTRACTS.md
  MODULE_STATUS.md

/docs/std-engine-core/
  BACKEND_IMPORT_AND_WIRING_PACK.md
  PRD.md
  DOMAIN_MODEL.md
  GOVERNANCE.md
  API_UI_SERVICE_CONTRACT.md
  CURSOR_IMPLEMENTATION_PACK.md

/docs/std-it/
  EXTRACTION_MATRIX.md
  SEED_PACKAGE_SPEC.md
  VALIDATION_REPORT_v0_2.md
  PACKAGE_RECONCILIATION_PLAN.md
  NSSF_CALIBRATION_MAPPING.md

/seed-packages/std-it/
  KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip
  KE-PPRA-IT-2022-04_Seed_Package_Skeleton.zip
  KE-PPRA-IT-2022-04_seed_package_v0_2/

/src/modules/std-engine/
  domain/
  import/
  validation/
  audit/
  read-models/
  api/
  services/
  repositories/

/src/modules/std-engine/import/
  package-reader.ts
  manifest-validator.ts
  checksum-verifier.ts
  import-planner.ts
  dry-run-importer.ts
  commit-importer.ts
  import-report-writer.ts
  std-it-import.command.ts

/src/modules/std-engine/validation/
  std-validation.service.ts
  validators/
    source-traceability.validator.ts
    clause-coverage.validator.ts
    parameter-binding.validator.ts
    rule-binding.validator.ts
    form-schema.validator.ts
    requirement-schema.validator.ts
    price-schedule.validator.ts
    evaluation-schema.validator.ts
    render-block.validator.ts

/src/modules/std-engine/audit/
  audit-event.service.ts
  audit-hash.service.ts

/src/modules/std-engine/api/
  std-family.controller.ts
  std-version.controller.ts
  source-traceability.controller.ts
  section-clause.controller.ts
  parameter.controller.ts
  rule.controller.ts
  form-schema.controller.ts
  requirement-schema.controller.ts
  price-schedule.controller.ts
  evaluation-schema.controller.ts
  render-block.controller.ts
  validation-report.controller.ts
  usage-binding.controller.ts
  import-package.controller.ts
  version-diff.controller.ts
  audit-log.controller.ts

/test/std-engine/
  import-it-std.spec.ts
  validation.spec.ts
  read-api.spec.ts
  smoke-contracts.spec.ts
```

If the project uses Next.js route handlers, replace `controller.ts` files with route handlers. If it uses NestJS or Express, keep the controller/service/repository split.

---

## Minimum canonical database entities

Create migrations for these core tables before writing the importer.

```text
std_family
std_version
std_source_document
std_source_anchor
std_section
std_clause
std_parameter
std_rule
std_form_schema
std_form_field
std_requirement_schema
std_price_schedule_schema
std_evaluation_schema
std_render_block
std_validation_run
std_validation_finding
std_audit_event
std_usage_binding
```

Most core STD objects should have:

```text
id
package_id
family_code
version_code
object_key
title
description
lifecycle_state
validation_status
source_anchor_id
content_hash
metadata_json
created_at
updated_at
```

Use JSON columns only for complex schema/config structures. Keep legal identity, object keys, lifecycle state, validation status, and source traceability normalized.

---

## Lifecycle states

Use the final lifecycle vocabulary consistently:

```text
DRAFT
STRUCTURING
INTERNAL_REVIEW
LEGAL_REVIEW
PROCUREMENT_REVIEW
APPROVED
ACTIVE
SUSPENDED
SUPERSEDED
ARCHIVED
```

For the first read-only seed import, set the official IT STD package to:

```text
lifecycle_state = ACTIVE
is_immutable = true
activation_method = SEEDED_OFFICIAL_SOURCE
```

This allows the UI to behave as read-only without building the full approval workflow yet.

---

## Expected import package contents

The importer should expect the preferred package zip to contain, or be mappable to, these logical files.

```text
manifest.json
source_documents.json
source_anchors.json
sections.json
clauses.json
parameters.json
rules.json
form_schemas.json
form_fields.json
requirement_schemas.json
price_schedule_schemas.json
evaluation_schema.json
render_blocks.json
validation_expectations.json
smoke_contracts.json
audit_seed.json
/source/
  official_it_std.pdf or official_it_std.doc
```

If v0.2 does not yet contain every file above, do not fabricate missing legal content. Instead:

```text
1. Import what is present.
2. Create validation findings for missing required objects.
3. Mark derived/placeholder objects clearly as GENERATED_PLACEHOLDER if absolutely needed for UI continuity.
4. Do not allow placeholders to pass activation validation.
```

---

## Import strategy options

### Strategy A — Strict package import

Recommended for the first backend milestone.

```text
Read zip
Verify manifest
Verify checksums
Load normalized JSON records
Persist records in a transaction
Run validation
Write audit events
Generate dry-run/commit report
```

Benefits:

```text
Deterministic
Repeatable
Easy to test
Compatible with immutable STD versioning
Best for Cursor implementation
```

### Strategy B — Hybrid package + source reconciliation

Use after Strategy A works.

```text
Import structured package
Register official PDF/DOC source document
Validate source anchors against extracted source references
Compare package anchors with extraction matrix
Persist missing-anchor findings
```

### Strategy C — Incremental object-family import

Use only for debugging.

```text
Import family/version/source documents
Import sections/clauses
Stop and verify UI
Import parameters/rules
Stop and verify UI
Import forms/requirements/pricing/evaluation/render blocks
Stop and verify UI
```

### Strategy D — Live source extraction import

Do not use first.

```text
Parse DOC/PDF directly
Extract sections/clauses/anchors
Infer structured objects
Persist generated records
```

Reason to defer:

```text
Too much variability
Hard to audit
High risk of malformed legal model
Should only be used as a future assisted import workflow
```

---

## First implementation sequence for Cursor

### Step 0 — Repository audit

Cursor task:

```text
Inspect the repository structure. Identify framework, API routing style, database ORM/migration tool, test runner, package manager, and existing module conventions. Do not create implementation files until you report the discovered conventions and propose exact file locations.
```

Expected output:

```text
Repo stack summary
Package manager
Database/migration tool
API style
Test runner
Proposed file locations
Risks/blockers
```

---

### Step 1 — Add STD Engine database migrations

Cursor task:

```text
Create database migrations for the STD Engine read model. Include std_family, std_version, source documents, source anchors, sections, clauses, parameters, rules, forms, form fields, requirement schemas, price schedule schemas, evaluation schemas, render blocks, validation runs, validation findings, audit events, and usage bindings. Use normalized keys for identity and JSON columns only for complex schemas/configuration. Do not implement editing workflow.
```

Acceptance criteria:

```text
Migrations run cleanly.
Tables have stable unique keys.
Package identity is enforced.
Active versions can be marked immutable.
Validation findings can reference any STD object.
Audit events can reference any STD object.
```

---

### Step 2 — Add import package reader

Cursor task:

```text
Implement a package reader for /seed-packages/std-it/KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip. It should list files, read manifest data, verify expected package structure, expose parsed JSON payloads, and report missing optional/required files without crashing the process.
```

Required files:

```text
src/modules/std-engine/import/package-reader.ts
src/modules/std-engine/import/manifest-validator.ts
src/modules/std-engine/import/checksum-verifier.ts
```

Acceptance criteria:

```text
Can list zip contents.
Can read manifest.
Can classify required vs optional files.
Can report missing files.
Can verify SHA-256 when expected hashes are present.
Does not write to DB.
```

---

### Step 3 — Add dry-run importer

Cursor task:

```text
Implement dry-run import for KE-PPRA-IT-2022-04. The dry run must parse the package, normalize records, calculate insert/update/skip counts, validate package identity, verify checksums, detect missing anchors, and write a dry-run report to /reports/std-import/.
```

Required files:

```text
src/modules/std-engine/import/import-planner.ts
src/modules/std-engine/import/dry-run-importer.ts
src/modules/std-engine/import/import-report-writer.ts
```

Command:

```bash
pnpm std:import:dry-run -- --zip ./seed-packages/std-it/KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip --package-id KE-PPRA-IT-2022-04
```

Report fields:

```text
package_id
family_code
version_code
source_authority
package_checksum
manifest_hash
files_total
files_verified
records_planned_insert
records_planned_skip
records_planned_fail
missing_required_files
missing_optional_files
validation_blockers
validation_warnings
dry_run_id
dry_run_timestamp
```

---

### Step 4 — Add commit importer

Cursor task:

```text
Implement commit import for the IT STD package. The importer must run inside a transaction, insert canonical read-model records, persist validation findings, persist audit events, mark the imported official package as immutable/read-only, and emit a commit report. Do not implement editing, approval workflow, or supersession.
```

Required files:

```text
src/modules/std-engine/import/commit-importer.ts
src/modules/std-engine/import/std-it-import.command.ts
src/modules/std-engine/audit/audit-event.service.ts
src/modules/std-engine/audit/audit-hash.service.ts
```

Command:

```bash
pnpm std:import:commit -- --zip ./seed-packages/std-it/KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip --package-id KE-PPRA-IT-2022-04 --target-state ACTIVE --immutable true
```

Commit behavior:

```text
If package already exists with identical package hash: skip idempotently.
If package exists with different hash and lifecycle ACTIVE: fail.
If blockers exist: fail unless --allow-blockers is explicitly supplied for local dev only.
If commit succeeds: create audit events.
```

---

### Step 5 — Add validation engine

Cursor task:

```text
Implement persistent validation for the imported IT STD package. Validators must create std_validation_run and std_validation_finding records. Findings must include severity, code, object type, object ID, description, suggested fix, lifecycle gate, and status.
```

Required validators:

```text
source-traceability.validator.ts
clause-coverage.validator.ts
parameter-binding.validator.ts
rule-binding.validator.ts
form-schema.validator.ts
requirement-schema.validator.ts
price-schedule.validator.ts
evaluation-schema.validator.ts
render-block.validator.ts
```

Severity values:

```text
BLOCKER
WARNING
INFO
```

Finding status values:

```text
OPEN
ASSIGNED
REMEDIATED_IN_DRAFT
WAIVED_WITH_APPROVAL
RESOLVED
```

Command:

```bash
pnpm std:validate -- --package-id KE-PPRA-IT-2022-04
```

---

### Step 6 — Add read-only APIs

Cursor task:

```text
Implement read-only STD Engine APIs for all implemented UI screens. Do not create POST/PATCH/DELETE endpoints except import/dry-run commands if the backend framework requires HTTP access.
```

Minimum endpoints:

```text
GET /api/std/families
GET /api/std/families/:familyCode
GET /api/std/versions/:packageId
GET /api/std/versions/:packageId/source-traceability
GET /api/std/versions/:packageId/sections
GET /api/std/sections/:sectionId
GET /api/std/clauses/:clauseId
GET /api/std/versions/:packageId/parameters
GET /api/std/parameters/:parameterId
GET /api/std/versions/:packageId/rules
GET /api/std/rules/:ruleId
GET /api/std/versions/:packageId/forms
GET /api/std/forms/:formId
GET /api/std/versions/:packageId/requirements
GET /api/std/versions/:packageId/price-schedules
GET /api/std/versions/:packageId/evaluation-schema
GET /api/std/versions/:packageId/render-blocks
GET /api/std/versions/:packageId/validation-report
GET /api/std/versions/:packageId/usage-bindings
GET /api/std/versions/:packageId/audit-log
GET /api/std/import/dry-run-reports/:dryRunId
GET /api/std/versions/:packageId/diff?compareTo=:packageId
```

Screen mapping:

```text
01 STD Library -> GET /api/std/families
02 STD Family Detail -> GET /api/std/families/:familyCode
03 STD Version Detail -> GET /api/std/versions/:packageId
04 Source Traceability -> GET /api/std/versions/:packageId/source-traceability
05 Section / Clause Map -> GET /api/std/versions/:packageId/sections
06 Clause Detail -> GET /api/std/clauses/:clauseId
07 Parameter Dictionary -> GET /api/std/versions/:packageId/parameters
08 Parameter Detail -> GET /api/std/parameters/:parameterId
09 Rule Dictionary -> GET /api/std/versions/:packageId/rules
10 Rule Detail -> GET /api/std/rules/:ruleId
11 Form Schema Manager -> GET /api/std/versions/:packageId/forms
12 Form Detail -> GET /api/std/forms/:formId
13 Requirement Schema Manager -> GET /api/std/versions/:packageId/requirements
14 Price Schedule Schema -> GET /api/std/versions/:packageId/price-schedules
15 Evaluation Schema -> GET /api/std/versions/:packageId/evaluation-schema
16 Render Blocks -> GET /api/std/versions/:packageId/render-blocks
17 Validation Report -> GET /api/std/versions/:packageId/validation-report
18 Review & Approval -> read-only placeholder using version/validation/audit data
19 Usage / Tender Bindings -> GET /api/std/versions/:packageId/usage-bindings
20 Import Package Review -> dry-run report data
21 Version Diff / Supersession -> compare-only endpoint
22 Audit Log -> GET /api/std/versions/:packageId/audit-log
```

---

### Step 7 — Wire UI to backend read APIs

Cursor task:

```text
Replace static UI data with calls to the STD Engine read-only APIs. Use KE-PPRA-IT-2022-04 as the default package ID for the first backend wiring. Preserve read-only behavior. Do not enable editing, approval, supersession execution, or addendum actions.
```

UI wiring order:

```text
1. STD Library
2. STD Family Detail
3. STD Version Detail
4. Source Document & Traceability
5. Section / Clause Map
6. Clause Detail
7. Parameter Dictionary
8. Parameter Detail
9. Rule Dictionary
10. Rule Detail
11. Form Schema Manager
12. Form Detail
13. Requirement Schema Manager
14. Price Schedule Schema
15. Evaluation Schema
16. Render Blocks
17. Validation Report
22. Audit Log
20. Import Package Review
21. Version Diff / Supersession compare-only
18. Review & Approval read-only placeholder
19. Usage / Tender Bindings seeded/read-only
```

Acceptance criteria:

```text
No screen relies on hard-coded fake data for the imported package.
All screens show package context.
All active-version screens are read-only.
Missing data is displayed as validation finding, not hidden.
```

---

### Step 8 — Add smoke contracts

Cursor task:

```text
Create smoke tests proving the imported IT STD package is queryable and displayable across the main screens. Tests should assert package existence, clause availability, source traceability, validation findings, audit events, and API response contracts.
```

Minimum smoke checks:

```text
Package KE-PPRA-IT-2022-04 exists.
Family KE-PPRA-IT exists.
Version lifecycle is ACTIVE and immutable.
At least one source document is registered.
At least one section is imported.
At least one clause is imported.
Clauses have source anchors or validation findings.
Parameters endpoint returns records or explicit empty state.
Rules endpoint returns records or explicit empty state.
Forms endpoint returns records or explicit empty state.
Requirements endpoint returns records or explicit empty state.
Evaluation endpoint returns records or explicit empty state.
Render blocks endpoint returns records or explicit empty state.
Validation report endpoint returns latest validation run.
Audit log endpoint returns import/validation events.
No write endpoint mutates ACTIVE version.
```

---

## Import report contract

The Import Package Review screen should be driven by this report structure.

```json
{
  "dryRunId": "DRY-KE-PPRA-IT-2022-04-0001",
  "packageId": "KE-PPRA-IT-2022-04",
  "familyCode": "KE-PPRA-IT",
  "versionCode": "2022-04",
  "importMode": "NEW_VERSION",
  "targetState": "ACTIVE",
  "immutable": true,
  "sourceAuthority": "PPRA",
  "packageSha256": "...",
  "manifestHash": "...",
  "sourceDocumentHash": "...",
  "fileCount": 12,
  "checksumStatus": "PASSED",
  "validationStatus": "WARNING",
  "importReadiness": "READY_WITH_WARNINGS",
  "recordCounts": {
    "families": 1,
    "versions": 1,
    "sourceDocuments": 1,
    "anchors": 0,
    "sections": 0,
    "clauses": 0,
    "parameters": 0,
    "rules": 0,
    "forms": 0,
    "requirements": 0,
    "priceSchedules": 0,
    "evaluationCriteria": 0,
    "renderBlocks": 0
  },
  "findings": [
    {
      "severity": "WARNING",
      "code": "IMPORT-WRN-001",
      "objectType": "PACKAGE",
      "objectId": "KE-PPRA-IT-2022-04",
      "description": "Optional render block file missing.",
      "suggestedFix": "Add render_blocks.json in the next package revision.",
      "lifecycleGate": "ACTIVATION"
    }
  ]
}
```

Adjust record counts based on real package contents. Do not hard-code the example values.

---

## API response envelope standard

All read APIs should use a consistent envelope:

```json
{
  "packageContext": {
    "familyCode": "KE-PPRA-IT",
    "versionCode": "2022-04",
    "packageId": "KE-PPRA-IT-2022-04",
    "lifecycleState": "ACTIVE",
    "immutable": true
  },
  "data": {},
  "pagination": null,
  "validationSummary": {
    "blockers": 0,
    "warnings": 0,
    "info": 0
  },
  "audit": {
    "snapshotHash": "...",
    "generatedAt": "2026-07-09T00:00:00Z"
  }
}
```

---

## Deferred backend work

Do not implement these until Milestone 1 is complete:

```text
Draft version creation
Editing in draft state
Role/permission decisioning
Internal review workflow
Legal review workflow
Procurement review workflow
Approval
Activation
Supersession execution
Tender usage binding enforcement
Addendum generation
Supplier-facing tender rendering
Contract carry-forward execution
```

Next proper sequence after Milestone 1:

```text
1. Draft version creation
2. Controlled editing in DRAFT only
3. Validation rerun
4. Internal review
5. Legal review
6. Procurement review
7. Approval
8. Activation
9. Supersession
10. Tender binding enforcement
11. Addendum impact handling
```

---

## Cursor prompts to run

### Prompt 1 — Repo discovery

```text
Inspect the repository and identify the framework, routing style, database/migration tool, package manager, and test runner. Then propose exact file locations for the STD Engine import/read-model implementation. Do not write code yet.
```

### Prompt 2 — Migrations

```text
Create the STD Engine read-model migrations for family, version, source document, source anchor, section, clause, parameter, rule, form schema, form field, requirement schema, price schedule schema, evaluation schema, render block, validation run, validation finding, audit event, and usage binding. Keep the model read-only for ACTIVE versions. Do not create editing/workflow tables yet.
```

### Prompt 3 — Package reader

```text
Implement a zip package reader for KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip. It must list contents, read manifest data, verify file hashes when expected hashes are present, classify missing required/optional files, and return a structured package inspection result. No database writes.
```

### Prompt 4 — Dry-run importer

```text
Implement a dry-run importer for KE-PPRA-IT-2022-04. It should parse package contents, normalize records, calculate planned inserts/skips/failures, detect missing anchors/files, run validation checks that do not require committed IDs, and write a deterministic dry-run report.
```

### Prompt 5 — Commit importer

```text
Implement commit import for the IT STD seed package. It must run in a transaction, be idempotent, refuse to overwrite immutable ACTIVE packages with different hashes, persist validation findings, and write audit events.
```

### Prompt 6 — Validation engine

```text
Implement persistent validators for source traceability, clause coverage, parameter binding, rule binding, form schemas, requirement schemas, price schedules, evaluation schema, and render blocks. Persist validation runs and findings.
```

### Prompt 7 — Read APIs

```text
Implement read-only API endpoints for STD Library, Family Detail, Version Detail, Source Traceability, Section/Clause Map, Clause Detail, Parameter Dictionary/Detail, Rule Dictionary/Detail, Form Schema Manager/Detail, Requirement Schema, Price Schedule, Evaluation Schema, Render Blocks, Validation Report, Usage Bindings, Import Dry Run Report, Version Diff compare-only, and Audit Log.
```

### Prompt 8 — UI wiring

```text
Replace static screen data with calls to the read-only APIs using KE-PPRA-IT-2022-04 as the default package. Preserve active-version read-only behavior. Do not enable editing, approval, activation, or supersession execution.
```

### Prompt 9 — Smoke contracts

```text
Add smoke tests proving that KE-PPRA-IT-2022-04 imports, validates, creates audit events, and serves data to all read-only STD Engine screens. Include tests that ACTIVE versions cannot be mutated.
```

---

## Definition of done

The backend import/read-model work is done when all are true:

```text
The IT STD package import can run locally from a clean database.
Dry-run import produces a deterministic report.
Commit import is idempotent.
Imported package is immutable/read-only.
Read APIs return real data for all implemented screens.
Validation findings are persisted and visible.
Audit events are persisted and visible.
UI screens display backend data, not static mock rows.
No editing or workflow mutation is required.
Smoke tests pass.
```
