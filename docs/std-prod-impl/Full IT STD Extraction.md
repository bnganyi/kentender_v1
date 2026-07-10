The next Cursor task should be **Full IT STD Extraction + Final Hydration Package**, not more UI fixes.

Use this plan.

CURSOR TASK: Full IT STD Extraction and Hydration Package

Objective:

Replace the partial v0.2 seed with a complete, source-traced, validation-ready IT STD package that can support real tender-instance creation.

Reference documents:

\- STD_Engine_IT_Digitization_Blueprint.md

\- STD_Engine_Core_Module_PRD.md

\- STD_Engine_Core_Domain_Model.md

\- STD_Engine_Core_Governance_Roles_Permissions_State_Model.md

\- STD_Engine_Core_API_UI_Service_Contract.md

\- STD_IT_Extraction_Matrix.md

\- STD_IT_Seed_Package_Specification.md

\- STD_IT_Full_Source_Extraction_Pass_1.md through Pass_5.md

\- STD_IT_Package_Reconciliation_and_Import_Ready_Update_Plan.md

\- STD_IT_Package_Validation_Report_v0_2.md

\- NSSF_ERP_Calibration_Mapping.md

**1\. Freeze the target package**

Create a new final package version:

KE-PPRA-IT-2022-04_Seed_Package_v1_0.zip

Do not continue modifying v0_2 except as a historical reference.

Package status:

family_code: KE-PPRA-IT

version_code: KE-PPRA-IT-2022-04

package_id: KE-PPRA-IT-2022-04

initial_lifecycle_state: DRAFT

activation_allowed: false until validation passes

package_quality: FULL_EXTRACTION_CANDIDATE

**2\. Complete source extraction first**

Extract the official IT STD into complete structured data.

Required extraction coverage:

source_documents

source_trace

sections

clauses

parameters

parameter_options

rules

forms

form_fields

evidence_requirements

requirements_schema

price_schedule_schema

evaluation_schema

contract_output_schema

render_blocks

governance

smoke_tests

sample_tender_instances

Every legal/procedural clause must have:

clause_id

section_id

clause_number

clause_title

full_clause_text

mutability_type

source_document_id

source_section_ref

source_clause_ref

source_page_start

source_page_end

source_anchor

source_text_hash

normalized_text_hash

extraction_status

verification_status

No placeholder clause text is acceptable.

**3\. Reconcile against the extraction matrix**

Use STD_IT_Extraction_Matrix.md as the checklist.

For every STD section, mark:

extracted

source_traced

hash_generated

schema_mapped

render_mapped

validated

Any missing item must become a validation finding, not a silent TODO.

Required blocker examples:

CLAUSE_TEXT_MISSING

SOURCE_ANCHOR_MISSING

TEXT_HASH_MISSING

MANDATORY_SECTION_UNMAPPED

FORM_SCHEMA_MISSING

EVALUATION_CRITERION_UNMAPPED

RENDER_BLOCK_MISSING

PARAMETER_UNBOUND

RULE_TARGET_MISSING

**4\. Build the final package from normalized files**

Expected package structure:

/std-package

manifest.json

checksums.json

source_documents.json

source_trace.json

sections.json

clauses.json

parameters.json

parameter_options.json

rules.json

forms.json

form_fields.json

evidence_requirements.json

requirements_schema.json

requirements_seed.json

price_schedule_schema.json

evaluation_schema.json

contract_output_schema.json

render_blocks.json

governance.json

smoke_tests.json

sample_tender_instances.json

validation_expectations.json

The package must be importable without relying on UI mock data.

**5\. Hydrate backend from the final package**

Importer must load v1_0 into the existing STD Engine read model.

Commit behavior:

import as DRAFT

register official PDF

persist all extracted objects

persist source anchors

persist text hashes

persist validation findings

persist audit events

seed sample tender instance data

do not activate

do not enable editing

**6\. Prove tender-instance readiness**

The final extraction must support creating a tender STD instance later.

Therefore the package must include enough structured data for:

Tender identity

Tender Data Sheet

Special Conditions of Contract

Requirements of the Information System

Technical requirements

Implementation schedule

System inventory

Price schedules

Evaluation criteria

Tendering forms

Contract forms

Render blocks

Validation rules

The package is not complete if it only visualizes STD administration screens.

**7\. UI hydration validation**

After import, verify these screens use real extracted data:

01 STD Library

02 STD Family Detail

03 STD Version Detail

04 Source Traceability

05 Section / Clause Map

06 Clause Detail

07 Parameter Dictionary

08 Parameter Detail

09 Rule Dictionary

10 Rule Detail

11 Form Schema Manager

12 Form Detail

13 Requirement Schema Manager

14 Price Schedule Schema

15 Evaluation Schema

16 Render Blocks

17 Validation Report

22 Audit Log

Screens 18–21 remain read-only/stubbed until workflow, usage, import review, and diff are finalized.

**8\. Smoke contract gates**

Create smoke tests that fail if any placeholder extraction remains.

Minimum smoke checks:

STD-SMOKE-001: Package imports as DRAFT

STD-SMOKE-002: Official PDF registered with SHA-256

STD-SMOKE-003: All mandatory sections exist

STD-SMOKE-004: All locked clauses have full text

STD-SMOKE-005: All locked clauses have source anchors

STD-SMOKE-006: All locked clauses have normalized text hashes

STD-SMOKE-007: TDS parameters exist and are render-bound

STD-SMOKE-008: SCC parameters exist and are render-bound

STD-SMOKE-009: Tendering forms have fields

STD-SMOKE-010: Evaluation schema has criteria

STD-SMOKE-011: Price schedules have schemas

STD-SMOKE-012: IT requirements schema can create a tender requirement set

STD-SMOKE-013: Render blocks cover mandatory output sections

STD-SMOKE-014: Validation report contains no extraction placeholders

STD-SMOKE-015: Sample tender instance can be created from the STD package

**9\. Stop condition**

Do not move to editing, approval workflow, supersession, addenda, or tender wizard development until this is true:

The official IT STD is fully extracted, source-traced, hashable, imported, hydrated, validated, and capable of producing a structured tender STD instance.

**Cursor execution instruction**

Start with a new workstream: FULL_IT_STD_EXTRACTION_V1.

Do not patch v0.2 placeholders. Use v0.2 only as a reference. Build KE-PPRA-IT-2022-04_Seed_Package_v1_0.zip from the official IT STD and the existing extraction documents.

The first deliverable is not UI work. The first deliverable is a complete extraction reconciliation report showing every official STD section, clause, form, parameter, rule, evaluation criterion, price schedule, requirement schema, contract output, source anchor, and render block.

Then generate the v1_0 package, import it as DRAFT, hydrate the read APIs, and run smoke tests proving that no mandatory legal clause or tender-instance-critical schema is still a placeholder.

That is the right reset. The POC proved the model. The draft backend proved hydration. Now the asset that matters is the **complete legal STD data package**.