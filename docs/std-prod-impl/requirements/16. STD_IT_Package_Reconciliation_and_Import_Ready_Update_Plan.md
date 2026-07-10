# STD for Procurement of Information Technology — Package Reconciliation and Import-Ready Update Plan

**Package:** `KE-PPRA-IT-2022-04`  
**Target next package:** `KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip`  
**Status of this document:** Planning artifact for package reconciliation  
**Activation status after v0.2:** Not legally activatable  
**Prepared:** 2026-07-07 20:53 UTC

---

## 1. Purpose

This document reconciles the current `KE-PPRA-IT-2022-04` seed package skeleton against the five completed extraction passes for the official PPRA **Standard Tender Document for Procurement of Information Technology**.

The purpose is not to activate the package. The purpose is to define the exact work required to move from a structurally valid skeleton to an import-ready `v0.2` seed package that can be loaded into the STD Engine in `DRAFT` or `STRUCTURING` state for review, validation, and further controlled completion.

The output of this artifact is a file-by-file update plan, import order, validation order, review gate model, activation blocker register, and checksum strategy.

---

## 2. Controlling principle

The official PPRA IT STD is the legal master. The NSSF ERP tender is a calibration fixture only.

This means:

1. The package must not encode the NSSF ERP tender as if it were the official standard.
2. NSSF-specific values, such as the procuring entity, ERP scope, Microsoft Dynamics 365 Business Central requirements, professional indemnity amount, phase-specific payment milestones, and pension-sector requirements, may be used only as fixture data.
3. The master package must remain generalized enough to support other IT tenders and, at the engine level, other STD families.
4. Locked legal text must remain locked.
5. TDS, SCC, evaluation, requirement, price schedule, form, and contract-formation areas must be configurable only through controlled schemas and governed workflows.
6. Published tender outputs must be immutable and must be superseded only through addendum governance.

---

## 3. Source basis

### 3.1 Package and planning artifacts

This plan assumes the following current artifacts exist:

| Artifact | Role |
|---|---|
| `KE-PPRA-IT-2022-04_Seed_Package_Skeleton.zip` | Current starter seed package skeleton. |
| `STD_IT_Seed_Package_Specification.md` | Package structure and import strategy. |
| `STD_IT_Full_Source_Extraction_Pass_1.md` | Sections, source anchors, ITT, GCC, locked clause register. |
| `STD_IT_Full_Source_Extraction_Pass_2.md` | TDS, SCC, parameter dictionary, rule dictionary. |
| `STD_IT_Full_Source_Extraction_Pass_3.md` | Evaluation, qualification, tendering forms, price schedule schemas. |
| `STD_IT_Full_Source_Extraction_Pass_4.md` | Procuring Entity requirements, technical requirements, implementation schedule, system inventory. |
| `STD_IT_Full_Source_Extraction_Pass_5.md` | Contract conditions, contract forms, acceptance certificates, change orders, contract carry-forward. |

### 3.2 Source documents

| Source | Role |
|---|---|
| Official PPRA IT STD, DOC. 10, April 2022 update | Master legal and structural source. |
| NSSF SPS ERP tender, Ref. `NSSFSPS/ICT/ERP/001/2025-2026` | Real-world calibration fixture only. |
| WORKS PoC JSON and official WORKS STD | Precedent for generalized STD Engine patterns, especially section mutability, tender configuration, locked sections, and structured schedules. |

---

## 4. Reconciliation conclusion

The current skeleton is structurally useful, but it remains too shallow for import-readiness.

The skeleton already contains the correct broad package modules:

- template
- source
- configuration
- rules
- forms
- requirements
- schedules
- pricing
- evaluation
- contract
- rendering
- workflow
- tests
- fixtures

However, the skeleton must be reconciled against Passes 1-5 before it can be treated as an import-ready draft package.

The most important missing areas are:

1. Full source anchors across all extracted areas.
2. Full TDS and SCC parameter dictionary coverage.
3. Full form-field extraction and evidence mapping.
4. Full rule bindings and test cases.
5. Full render block and render order mapping.
6. Technical requirement composer linkage to evaluation, pricing, supplier conformance, and contract carry-forward.
7. Price schedule calculations and recurrent-cost treatment.
8. Contract formation schemas, including appendices, acceptance certificates, securities, and change orders.
9. Addendum impact rules across all configurable surfaces.
10. Activation blockers that prevent accidental use as an approved master template.

---

## 5. Target state for v0.2

### 5.1 What v0.2 should be

`KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip` should be:

| Capability | Target state |
|---|---|
| JSON validity | All files valid JSON. |
| Package structure | Complete and stable. |
| Import behavior | Importable into STD Engine as `DRAFT` or `STRUCTURING`. |
| Source traceability | Major source anchors populated across all official STD zones. |
| Parameters | TDS and SCC parameters reconciled from Pass 2. |
| Rules | Core validation and governance rules present, with bindings. |
| Forms | Official form catalogue present, with starter field-level schema expanded beyond skeleton. |
| Evaluation | Evaluation stages, responsiveness, technical, financial, qualification, and post-qualification schemas present. |
| Requirements | Requirement composer schemas present and linked to conformance/evaluation/pricing. |
| Pricing | Official IT price schedule structure present. |
| Contract | Contract carry-forward, forms, appendices, certificates, securities, and change-order schemas present. |
| Rendering | Render block map present for all major output artifacts. |
| Tests | Smoke test files populated with executable or near-executable test contracts. |
| Fixture strategy | NSSF ERP fixture isolated and marked non-import-by-default. |
| Activation | Blocked. |

### 5.2 What v0.2 should not be

v0.2 must not be:

1. Activated.
2. Used to generate a live published tender.
3. Treated as legally approved.
4. Treated as complete full-text extraction.
5. Treated as a final renderer implementation.
6. Treated as a substitute for PPRA/legal/procurement review.

---

## 6. Current skeleton inventory

The current skeleton contains **64 JSON files**. The table below records each file, its current functional area, current starter record count, and the required reconciliation action for v0.2.

| File | Area | Current records | Required v0.2 action |
|---|---:|---:|---|
| `checksums.json` | Package root | 0 | Regenerate after all v0.2 file updates. Must include per-file SHA-256 and package-level digest. |
| `configuration/parameter_groups.json` | TDS/SCC configuration | 6 | Update groups from Pass 2; verify all TDS and SCC groups have governance ownership and render targets. |
| `configuration/parameter_options.json` | TDS/SCC configuration | 27 | Expand controlled values from Pass 2; separate universal options from IT-specific options. |
| `configuration/parameters.json` | TDS/SCC configuration | 44 | Replace starter parameter list with reconciled Pass 2 TDS/SCC parameter dictionary; add source anchors, dependencies, validation bindings, and render bindings. |
| `configuration/scc_schema.json` | TDS/SCC configuration | 1 | Update from Pass 2 and Pass 5 SCC contract carry-forward requirements. |
| `configuration/tds_schema.json` | TDS/SCC configuration | 1 | Update from Pass 2; ensure all TDS entries can render to Invitation, ITT references, TDS table, evaluation setup, and tender configuration validation. |
| `contract/acceptance_certificate_schema.json` | Contract formation and execution | 1 | Update from Pass 5; include installation certificate, operational acceptance certificate, phase/subsystem acceptance, prerequisite checks, and carry-forward values. |
| `contract/change_order_schema.json` | Contract formation and execution | 1 | Update from Pass 5; include request, estimate, estimate acceptance, proposal, change order, approvals, and budget/scope/time impact controls. |
| `contract/contract_appendices.json` | Contract formation and execution | 6 | Update from Pass 5; include supplier representative, adjudicator, approved subcontractors, software categories, custom materials, revised price schedules, and finalization minutes. |
| `contract/contract_forms.json` | Contract formation and execution | 16 | Update from Pass 5; align official IT STD contract forms and generated artifacts; add source anchors and rendering profile references. |
| `contract/contract_schema.json` | Contract formation and execution | 1 | Update from Pass 5; include tender-to-contract carry-forward categories and award/finalization lifecycle. |
| `evaluation/evaluation_schema.json` | Evaluation and qualification | 1 | Update from Pass 3; normalize stages and stage gates. |
| `evaluation/financial_evaluation_schema.json` | Evaluation and qualification | 1 | Update from Pass 3; include supply/install cost, recurrent cost, currency, discounts, arithmetical correction, and lowest evaluated price logic. |
| `evaluation/qualification_schema.json` | Evaluation and qualification | 1 | Update from Pass 3; include ELI/CON/EXP/FIN/personnel/IP/conformance schemas and post-qualification controls. |
| `evaluation/responsiveness_checklist.json` | Evaluation and qualification | 3 | Update from Pass 3; expand mandatory and conditional responsiveness requirements from official forms and rules. |
| `evaluation/technical_evaluation_schema.json` | Evaluation and qualification | 1 | Update from Pass 3 and Pass 4; link scoring and conformance checks to requirements composer. |
| `fixtures/nssf_erp/contract_fixture.json` | Calibration fixtures | 1 | Keep as non-importing calibration fixture; update after NSSF mapping pass. Fixture must never be promoted to official STD seed data. |
| `fixtures/nssf_erp/evaluation_fixture.json` | Calibration fixtures | 1 | Keep as non-importing calibration fixture; update after NSSF mapping pass. Fixture must never be promoted to official STD seed data. |
| `fixtures/nssf_erp/fixture_manifest.json` | Calibration fixtures | 0 | Keep as non-importing calibration fixture; update after NSSF mapping pass. Fixture must never be promoted to official STD seed data. |
| `fixtures/nssf_erp/price_schedule_fixture.json` | Calibration fixtures | 1 | Keep as non-importing calibration fixture; update after NSSF mapping pass. Fixture must never be promoted to official STD seed data. |
| `fixtures/nssf_erp/requirements_fixture.json` | Calibration fixtures | 4 | Keep as non-importing calibration fixture; update after NSSF mapping pass. Fixture must never be promoted to official STD seed data. |
| `fixtures/nssf_erp/tender_configuration_values.json` | Calibration fixtures | 1 | Keep as non-importing calibration fixture; update after NSSF mapping pass. Fixture must never be promoted to official STD seed data. |
| `forms/bidder_response_schema.json` | Tendering and response forms | 1 | Update from Pass 3 and Pass 4; create unified submission payload schema across declarations, qualifications, technical conformance, price schedules, and evidence. |
| `forms/evidence_requirements.json` | Tendering and response forms | 3 | Update from Pass 3; map evidence documents to forms, qualification criteria, requirement responses, and contract carry-forward where applicable. |
| `forms/form_catalog.json` | Tendering and response forms | 14 | Update from Pass 3; align official form catalogue and activation conditions. |
| `forms/form_fields.json` | Tendering and response forms | 3 | Replace starter fields with full field-level schema from Pass 3; add validation, respondent, evidence, downstream-use, and source anchors. |
| `forms/form_sections.json` | Tendering and response forms | 0 | Populate; currently empty and must be filled for render and UI grouping. |
| `manifest.json` | Package root | 0 | Update quality_status, extraction_passes_applied, activation_blockers, import_policy, package_version_label, and source evidence summary. |
| `pricing/price_schedule_calculations.json` | Price schedule | 3 | Update from Pass 3; encode grand totals, supply/install totals, recurrent totals, VAT/tax handling where configurable, and cross-checks. |
| `pricing/price_schedule_catalog.json` | Price schedule | 6 | Update from Pass 3; confirm six official price schedule forms and tenderer-facing status. |
| `pricing/price_schedule_fields.json` | Price schedule | 6 | Expand fields from Pass 3; currently only starter fields. |
| `rendering/output_profiles.json` | Rendering | 5 | Update output profiles for issued tender, tender preview, evaluation pack, contract pack, addendum pack, and audit extract. |
| `rendering/render_blocks.json` | Rendering | 15 | Update from Passes 1-5; add all section, table, form, requirement, evaluation, and contract render blocks. |
| `rendering/render_order.json` | Rendering | 2 | Update canonical render orders for tender issue, supplier submission pack, evaluation pack, contract pack, and addendum pack. |
| `rendering/render_templates.json` | Rendering | 15 | Replace placeholders with renderer template references; do not embed uncontrolled legal text in runtime templates. |
| `requirements/requirement_categories.json` | Requirements composer | 10 | Update from Pass 4; separate universal requirement types from IT-specific categories. |
| `requirements/requirement_compliance_schema.json` | Requirements composer | 1 | Update from Pass 4; define supplier response choices, references, deviations, evidence, evaluator notes, and carry-forward behavior. |
| `requirements/requirement_schema.json` | Requirements composer | 1 | Update from Pass 4; formalize requirement groups, items, mandatory flags, neutrality checks, and evaluation/pricing linkage. |
| `requirements/requirement_templates.json` | Requirements composer | 0 | Populate approved starter templates/patterns only if they are official or safely generic; otherwise keep empty with explicit governance rule. |
| `rules/rule_bindings.json` | Rules and validation | 0 | Populate; currently empty and must link rules to fields, forms, sections, render blocks, and lifecycle stages. |
| `rules/rule_catalog.json` | Rules and validation | 19 | Update from Passes 2-5; add validation, activation, calculation, governance, rendering, addendum, and contract carry-forward rules. |
| `rules/rule_test_cases.json` | Rules and validation | 0 | Populate; currently empty and required for import-readiness. |
| `schedules/holiday_table_schema.json` | Implementation schedule and inventory | 1 | Review from Pass 4; keep generalized. |
| `schedules/implementation_schedule_schema.json` | Implementation schedule and inventory | 1 | Update from Pass 4; add milestones, phase dependencies, sites, acceptance links, and payment milestone links. |
| `schedules/site_table_schema.json` | Implementation schedule and inventory | 1 | Update from Pass 4; include implementation locations, delivery locations, and site-specific inventory/acceptance mapping. |
| `schedules/system_inventory_schema.json` | Implementation schedule and inventory | 2 | Update from Pass 4; split supply/install inventory and recurrent cost inventory; link to price schedules and implementation schedule. |
| `source/source_anchors.json` | Source traceability | 14 | Expand anchors from Passes 1-5; every major section, clause, parameter, form, rule, table, and contract artifact must have source anchors. |
| `source/source_document.json` | Source traceability | 1 | Update file hash evidence, source identity, extraction status, and source anomaly notes. |
| `source/source_pages.json` | Source traceability | 181 | Retain page map; add extraction coverage status by page ranges where useful. |
| `template/clause_fragments.json` | Template structure and locked legal content | 0 | Populate locked or parameterized clause fragments where full extraction has been performed; currently empty. |
| `template/clauses.json` | Template structure and locked legal content | 11 | Replace starter clause placeholders with clause register from Passes 1 and 5; add full text hashes when full text extraction is done. |
| `template/family.json` | Template structure and locked legal content | 1 | Minor update only; verify generalized family metadata. |
| `template/mutability_map.json` | Template structure and locked legal content | 15 | Update from Passes 1-5; ensure section and child-object mutability rules match engine enums. |
| `template/section_order.json` | Template structure and locked legal content | 2 | Update from Pass 1 and source anomaly policy; normalize official section numbering without hiding source inconsistencies. |
| `template/sections.json` | Template structure and locked legal content | 15 | Update from Pass 1; confirm canonical sections and source section references. |
| `template/version.json` | Template structure and locked legal content | 1 | Update status to STRUCTURING or DRAFT_IMPORT_READY, not ACTIVE; add extraction coverage fields. |
| `tests/addendum_smoke_tests.json` | Smoke tests | 2 | Update from Passes 2, 4, and 5. |
| `tests/import_smoke_tests.json` | Smoke tests | 4 | Update to cover full v0.2 package import sequence and blockers. |
| `tests/rendering_smoke_tests.json` | Smoke tests | 2 | Update to cover tender, supplier submission, evaluation, contract, and addendum rendering. |
| `tests/tender_binding_smoke_tests.json` | Smoke tests | 2 | Update to confirm active-only binding is blocked until approval, and draft import never creates usable tender version. |
| `tests/validation_smoke_tests.json` | Smoke tests | 4 | Update from Passes 2-5; include field, form, price, requirement, evaluation, contract, and addendum cases. |
| `workflow/addendum_impact_rules.json` | Governance workflow | 6 | Update from Passes 2, 4, and 5; include which changes force addendum and which artifacts are superseded. |
| `workflow/approval_bindings.json` | Governance workflow | 7 | Update review tracks for legal, procurement, technical, finance, contract, rendering, and data governance review. |
| `workflow/lifecycle_bindings.json` | Governance workflow | 2 | Update import lifecycle and activation blockers; make v0.2 importable only into Draft/Structuring. |

---

## 7. Extraction-pass reconciliation map

### 7.1 Pass 1 — Sections, source anchors, and locked clauses

| Pass 1 output | Package files affected | v0.2 action |
|---|---|---|
| Section/source anchor map | `template/sections.json`, `template/section_order.json`, `source/source_anchors.json` | Update canonical section hierarchy and source anchors. |
| Locked ITT clause register | `template/clauses.json`, `template/clause_fragments.json`, `source/source_anchors.json` | Add ITT clause records and full-text extraction placeholders/hash fields. |
| Locked GCC clause register | `template/clauses.json`, `template/clause_fragments.json`, `contract/contract_schema.json` | Add GCC clause records and contract render references. |
| Mutability classification | `template/mutability_map.json` | Normalize section and child-object mutability. |
| Source anomalies | `source/source_document.json`, `template/section_order.json`, `manifest.json` | Add official-source anomaly notes, especially section numbering inconsistency flags. |

### 7.2 Pass 2 — TDS, SCC, parameters, and rules

| Pass 2 output | Package files affected | v0.2 action |
|---|---|---|
| TDS parameter dictionary | `configuration/parameters.json`, `configuration/tds_schema.json`, `configuration/parameter_groups.json` | Replace starter parameters with reconciled source-derived dictionary. |
| SCC parameter dictionary | `configuration/parameters.json`, `configuration/scc_schema.json` | Align SCC parameters to contract carry-forward and render targets. |
| Rule dictionary | `rules/rule_catalog.json`, `rules/rule_bindings.json`, `rules/rule_test_cases.json` | Add validation, activation, render, and contract rules with explicit bindings. |
| Parameter dependencies | `configuration/parameters.json`, `rules/rule_bindings.json` | Add dependency metadata and lifecycle-stage effects. |
| Render block map | `rendering/render_blocks.json`, `rendering/render_templates.json` | Add render references for TDS/SCC fields. |

### 7.3 Pass 3 — Evaluation, forms, and price schedules

| Pass 3 output | Package files affected | v0.2 action |
|---|---|---|
| Evaluation stage model | `evaluation/evaluation_schema.json` | Normalize stages and gates. |
| Responsiveness checklist | `evaluation/responsiveness_checklist.json`, `forms/evidence_requirements.json` | Expand mandatory and conditional requirements. |
| Technical evaluation model | `evaluation/technical_evaluation_schema.json`, `requirements/requirement_compliance_schema.json` | Link technical scoring to requirement conformance. |
| Financial evaluation model | `evaluation/financial_evaluation_schema.json`, `pricing/*` | Add price comparison and recurrent-cost rules. |
| Qualification model | `evaluation/qualification_schema.json`, `forms/form_catalog.json`, `forms/form_fields.json` | Populate ELI, CON, EXP, FIN, personnel, IP, conformance schema. |
| Tendering forms | `forms/form_catalog.json`, `forms/form_sections.json`, `forms/form_fields.json` | Replace starter form fields and add render/source metadata. |
| Price schedules | `pricing/price_schedule_catalog.json`, `pricing/price_schedule_fields.json`, `pricing/price_schedule_calculations.json` | Populate official IT price schedule structures and calculations. |

### 7.4 Pass 4 — Requirements, implementation schedule, and system inventory

| Pass 4 output | Package files affected | v0.2 action |
|---|---|---|
| Requirement composer design | `requirements/requirement_schema.json`, `requirements/requirement_categories.json`, `requirements/requirement_templates.json` | Formalize universal and IT-specific requirement types. |
| Supplier conformance matrix | `requirements/requirement_compliance_schema.json`, `forms/bidder_response_schema.json` | Define supplier responses, evidence, deviations, references, and evaluator review. |
| Implementation schedule schema | `schedules/implementation_schedule_schema.json`, `schedules/site_table_schema.json`, `schedules/holiday_table_schema.json` | Add milestones, sites, non-working days, and acceptance/payment links. |
| System inventory schema | `schedules/system_inventory_schema.json`, `pricing/*` | Link inventory lines to supply/install and recurrent price schedules. |
| Background materials | `requirements/requirement_schema.json`, `rendering/render_blocks.json` | Separate background materials from binding requirements. |
| Addendum handling | `workflow/addendum_impact_rules.json` | Add impact rules for requirement, schedule, and inventory changes. |

### 7.5 Pass 5 — Contract conditions, forms, acceptance, change orders, carry-forward

| Pass 5 output | Package files affected | v0.2 action |
|---|---|---|
| Contract schema | `contract/contract_schema.json` | Add generation inputs, carry-forward categories, and contract lifecycle. |
| Contract forms | `contract/contract_forms.json`, `rendering/render_blocks.json` | Align official forms, securities, certificates, and disclosures. |
| Contract appendices | `contract/contract_appendices.json` | Add supplier representative, adjudicator, subcontractors, software, custom materials, revised prices, finalization minutes. |
| Acceptance certificates | `contract/acceptance_certificate_schema.json`, `schedules/implementation_schedule_schema.json` | Link installation/operational acceptance to milestones and payment. |
| Change orders | `contract/change_order_schema.json`, `workflow/addendum_impact_rules.json` | Add change procedure states and approvals. |
| Carry-forward model | `contract/contract_schema.json`, `configuration/scc_schema.json`, `pricing/*`, `requirements/*` | Add tender-to-award-to-contract carry-forward records and statuses. |

---

## 8. Gap register

### 8.1 Critical gaps

| ID | Gap | Impact | Required action before v0.2 |
|---|---|---|---|
| G-001 | `rules/rule_bindings.json` is empty. | Rules cannot be reliably applied to fields, sections, forms, lifecycle stages, or render blocks. | Populate rule bindings from Passes 2-5. |
| G-002 | `rules/rule_test_cases.json` is empty. | Validation engine behavior cannot be tested. | Add test cases for TDS, SCC, forms, price, requirements, evaluation, contract, and addendum. |
| G-003 | `forms/form_sections.json` is empty. | Supplier response UI and rendering cannot group form fields correctly. | Populate with form section hierarchy and render ordering. |
| G-004 | `template/clause_fragments.json` is empty. | Locked and parameterized clause rendering cannot be deterministic. | Populate clause fragments or explicitly defer full text while preserving blockers. |
| G-005 | `requirements/requirement_templates.json` is empty. | Composer has no controlled starter patterns. | Either populate safe generic templates or explicitly preserve empty state with governance controls. |
| G-006 | `checksums.json` is empty. | Import integrity is not enforceable. | Regenerate checksums after v0.2 update. |
| G-007 | Render templates are placeholders. | Generated tender and contract outputs cannot be relied upon. | Populate render template references or retain activation blocker. |
| G-008 | Source anchors are starter-level only. | Audit traceability is incomplete. | Expand source anchors to cover all extracted areas. |
| G-009 | Clause full text and hashes are incomplete. | Legal-text immutability cannot be enforced. | Add full extraction or mark v0.2 as not activatable. |
| G-010 | NSSF fixture isolation must be explicit. | Risk of polluting the official STD template with tender-specific values. | Keep fixture under `fixtures/nssf_erp` with non-import policy. |

### 8.2 Non-critical but important gaps

| ID | Gap | Required action |
|---|---|---|
| G-011 | Need expanded source anomaly register. | Add section-numbering and section-label anomalies to manifest/source metadata. |
| G-012 | Need review-track metadata per object group. | Bind review tracks by module. |
| G-013 | Need addendum supersession impact matrix. | Expand addendum rules by affected artifact. |
| G-014 | Need importer dry-run report shape. | Define expected validation output for package import service. |
| G-015 | Need object-level import idempotency rules. | Define natural keys and conflict rules. |

---

## 9. v0.2 package manifest updates

`manifest.json` must be updated as follows:

```json
{
  "package_code": "KE-PPRA-IT-2022-04",
  "package_type": "STD_TEMPLATE_SEED",
  "package_version_label": "v0.2",
  "quality_status": "DRAFT_IMPORT_READY_NOT_ACTIVATABLE",
  "activation_allowed": false,
  "import_allowed_states": ["DRAFT", "STRUCTURING"],
  "contains_fixture_data": true,
  "fixture_data_import_policy": "DO_NOT_IMPORT_BY_DEFAULT",
  "extraction_passes_applied": [1, 2, 3, 4, 5],
  "requires_approval_before_activation": true,
  "immutable_after_activation": true,
  "contains_locked_legal_text": true,
  "activation_blockers": [
    "Full legal/procurement review has not been completed.",
    "Full locked clause text extraction and text hashing may remain incomplete.",
    "Render templates require formal rendering QA.",
    "Rule test cases require execution in the target engine.",
    "Source anchors require reviewer confirmation."
  ]
}
```

The importer must reject activation even if all JSON files validate.

---

## 10. Import order for v0.2

The package must be imported in a deterministic order.

| Order | Group | Files |
|---:|---|---|
| 1 | Package root | `manifest.json`, `checksums.json` |
| 2 | Source evidence | `source/source_document.json`, `source/source_pages.json`, `source/source_anchors.json` |
| 3 | Template identity | `template/family.json`, `template/version.json` |
| 4 | Template structure | `template/sections.json`, `template/section_order.json`, `template/mutability_map.json` |
| 5 | Locked/controlled content | `template/clauses.json`, `template/clause_fragments.json` |
| 6 | Configuration groups/options | `configuration/parameter_groups.json`, `configuration/parameter_options.json` |
| 7 | Configuration parameters | `configuration/parameters.json`, `configuration/tds_schema.json`, `configuration/scc_schema.json` |
| 8 | Requirements and schedules | `requirements/*`, `schedules/*` |
| 9 | Pricing | `pricing/*` |
| 10 | Forms and evidence | `forms/*` |
| 11 | Evaluation | `evaluation/*` |
| 12 | Contract | `contract/*` |
| 13 | Rules | `rules/rule_catalog.json`, `rules/rule_bindings.json`, `rules/rule_test_cases.json` |
| 14 | Rendering | `rendering/*` |
| 15 | Workflow | `workflow/*` |
| 16 | Tests | `tests/*` |
| 17 | Fixtures | `fixtures/nssf_erp/*`, only if explicitly requested in fixture mode |

The importer must fail if a later object references a missing earlier object.

---

## 11. Validation order

Validation must run in this sequence:

1. JSON syntax validation.
2. Package manifest validation.
3. Checksum validation.
4. Source document and source anchor validation.
5. Template family/version validation.
6. Section hierarchy validation.
7. Mutability validation.
8. Clause and fragment validation.
9. Parameter schema validation.
10. Parameter option validation.
11. Rule expression validation.
12. Rule binding validation.
13. Requirement schema validation.
14. Schedule and inventory schema validation.
15. Price schedule schema and calculation validation.
16. Form catalogue and form-field validation.
17. Evidence requirement validation.
18. Evaluation schema validation.
19. Contract schema validation.
20. Render block/template validation.
21. Workflow/lifecycle validation.
22. Smoke-test dry run.
23. Fixture isolation validation.
24. Activation blocker validation.

The final validation result for v0.2 should be:

```text
PACKAGE_IMPORT_VALID: true
PACKAGE_CAN_ENTER_STATE: DRAFT or STRUCTURING
PACKAGE_CAN_ACTIVATE: false
```

---

## 12. File-by-file update acceptance criteria

A file is v0.2-ready only if it satisfies all applicable criteria below.

| Criterion | Applies to |
|---|---|
| Valid JSON | All JSON files |
| Stable natural keys | All record-based files |
| Source anchors where source-derived | Template, configuration, rules, forms, evaluation, pricing, requirements, schedules, contract, rendering |
| No uncontrolled tender-specific values in master package | All files outside `fixtures/` |
| Explicit lifecycle/import status | Manifest, version, workflow, tests |
| Rule bindings are resolvable | Rules and all rule targets |
| Render bindings are resolvable | Render files and all render targets |
| Mutability matches engine enum | Template, configuration, forms, requirements, evaluation, contract |
| Smoke tests are specific and testable | Tests and rules |
| NSSF fixture is isolated | `fixtures/nssf_erp/*` |
| Activation remains blocked | Manifest, version, lifecycle bindings |

---

## 13. Numbering and source-normalization policy

The official IT STD contains section-numbering and label inconsistencies. The package must not hide them, but it also must not allow those inconsistencies to break the engine.

Use this policy:

1. `source_section_label` preserves the official document label exactly.
2. `canonical_section_code` stores the normalized engine section code.
3. `source_anomaly_flag` identifies mismatch, duplicate numbering, or unexpected sequence.
4. `source_anomaly_note` records the issue.
5. Renderers use canonical engine order, but audit views must show source labels.
6. Reviewers must approve normalization before activation.

Example:

```json
{
  "canonical_section_code": "GCC",
  "source_section_label": "Section VI - General Conditions of Contract",
  "expected_std_label": "Section X - General Conditions of Contract",
  "source_anomaly_flag": true,
  "source_anomaly_note": "Official IT STD table of contents and body use inconsistent section labels. Canonical code preserved for engine behavior."
}
```

---

## 14. Activation blocker register

v0.2 must preserve the following blockers:

| Blocker ID | Blocker | Severity | Removal condition |
|---|---|---|---|
| AB-001 | Package has not completed legal review. | Blocker | Legal reviewer approval recorded. |
| AB-002 | Package has not completed procurement policy review. | Blocker | Procurement reviewer approval recorded. |
| AB-003 | Locked clause full-text extraction and text hashing incomplete or unverified. | Blocker | Clause hashes verified against source. |
| AB-004 | Source anchors not fully reviewed. | Blocker | Source traceability review complete. |
| AB-005 | Render templates not QA-approved. | Blocker | Render QA approval complete. |
| AB-006 | Rule test cases not executed in engine. | Blocker | Smoke tests passed in target environment. |
| AB-007 | NSSF fixture is present in package. | Warning/Blocker depending importer mode | Fixture import disabled by default; activation ignores fixture data. |
| AB-008 | Addendum impact rules not end-to-end tested. | Blocker | Addendum tests pass. |
| AB-009 | Contract carry-forward not end-to-end tested. | Blocker | Award-to-contract smoke tests pass. |
| AB-010 | Official source anomaly normalization not approved. | Blocker | Source normalization approval recorded. |

---

## 15. Review gates

### 15.1 Required review tracks

| Review track | Responsible role | Applies to |
|---|---|---|
| Source extraction review | STD Source Reviewer | Source anchors, sections, clauses, forms, tables |
| Legal review | Legal Reviewer | Locked clauses, GCC, SCC, contract forms, addendum behavior |
| Procurement policy review | Procurement Policy Reviewer | TDS, evaluation, qualification, forms, tender process rules |
| Technical IT review | Technical Domain Reviewer | IT requirements, implementation schedule, system inventory, acceptance, technical conformance |
| Finance/commercial review | Finance/Commercial Reviewer | Price schedules, recurrent costs, payment milestones, securities |
| Contract management review | Contract Manager / Legal Reviewer | Carry-forward, contract appendices, acceptance certificates, change orders |
| Renderer QA | Document Generation Reviewer | Render blocks, templates, section order, issued bundle output |
| Data governance review | Data Governance / Audit Reviewer | Hashes, audit trail, source traceability, immutability |
| Security/access review | System Administrator / Security Reviewer | Roles, permissions, activation controls, fixture isolation |

### 15.2 Approval rule

No package version may move to `APPROVED` unless all mandatory review tracks are complete and no blocker findings remain open.

No package version may move to `ACTIVE` unless:

1. Approved state exists.
2. Activation blocker register is empty.
3. Full package hash has been generated.
4. No fixture data is imported into the master template records.
5. All smoke tests pass.
6. The version is locked as immutable.

---

## 16. Addendum and supersession reconciliation

The update plan must preserve addendum behavior for every configurable surface.

| Changed object after tender publication | Expected addendum impact |
|---|---|
| Tender identity or submission date | Addendum required; Invitation/TDS bundle superseded. |
| Clarification deadline or pre-tender meeting | Addendum required if already published. |
| Tender security/professional indemnity requirement | Addendum required; supplier checklist and evaluation responsiveness affected. |
| Eligibility or qualification criteria | Addendum required; evaluation matrix and supplier submission forms affected. |
| Technical requirement | Addendum required; requirements section, conformance matrix, evaluation, and possibly price schedules affected. |
| Implementation milestone | Addendum required; implementation schedule, acceptance, payment milestone, and contract carry-forward affected. |
| System inventory item | Addendum required; inventory, price schedule, technical conformance, and contract schedules affected. |
| Price schedule structure | Addendum required; supplier price forms and financial evaluation affected. |
| SCC parameter | Addendum required; contract terms and contract render affected. |
| Locked ITT/GCC clause | Not allowed in tender configuration; requires new STD version, not addendum. |
| Contract form after award | Contract amendment/change-order route, not tender addendum, unless award not yet finalized. |

---

## 17. NSSF ERP calibration fixture handling

The NSSF ERP tender should remain valuable but isolated.

### 17.1 Fixture use cases

| Use case | Allowed? | Notes |
|---|---|---|
| Validate that an ERP tender can be represented by the IT STD schema | Yes | Use fixture mode only. |
| Test TDS parameter population | Yes | Values remain fixture data. |
| Test real technical requirements volume | Yes | Do not import as official requirement templates. |
| Test evaluation scoring model | Yes | Compare with official STD evaluation flexibility. |
| Test price schedule variations | Yes | Useful because NSSF uses a flatter price schedule than the official STD model. |
| Use NSSF Microsoft-specific requirements as default STD values | No | Would make the master package vendor-specific. |
| Use NSSF pension-specific requirements as official IT requirement templates | No | Would wrongly specialize the master STD. |
| Use NSSF professional indemnity model as universal STD rule | No | Keep as tender-specific/calibration only unless official STD supports the pattern generically. |

### 17.2 Fixture package rule

Fixture records must include:

```json
{
  "fixture_only": true,
  "import_by_default": false,
  "source": "NSSF SPS ERP Tender",
  "not_part_of_official_std": true
}
```

The import service must ignore fixtures unless run in explicit calibration mode.

---

## 18. Checksum and integrity strategy

`checksums.json` must be regenerated after v0.2 updates.

Minimum structure:

```json
{
  "package_code": "KE-PPRA-IT-2022-04",
  "package_version_label": "v0.2",
  "hash_algorithm": "SHA-256",
  "generated_at": "<timestamp>",
  "files": [
    {
      "path": "manifest.json",
      "sha256": "<hash>",
      "bytes": 0
    }
  ],
  "package_digest": "<hash-of-normalized-file-hash-list>"
}
```

Rules:

1. Hash every file in the package except `checksums.json` first.
2. Generate `checksums.json` from those file hashes.
3. Compute package digest from the sorted list of file paths and hashes.
4. Importer must fail on hash mismatch unless explicitly running in unsafe development mode.
5. Published/approved packages must never be imported from unchecked sources.

---

## 19. v0.2 build procedure

Use the following controlled build process:

1. Unzip skeleton package into a clean working directory.
2. Create a new branch/folder named `KE-PPRA-IT-2022-04_seed_package_v0_2`.
3. Update `manifest.json`.
4. Update source files from Passes 1-5.
5. Update template files.
6. Update configuration files.
7. Update rule files.
8. Update forms and evidence files.
9. Update requirements and schedule files.
10. Update pricing files.
11. Update evaluation files.
12. Update contract files.
13. Update rendering files.
14. Update workflow files.
15. Update tests.
16. Confirm NSSF fixture files are isolated and non-importing by default.
17. Run JSON validation over all files.
18. Run referential integrity validation.
19. Regenerate `checksums.json`.
20. Create ZIP.
21. Produce package validation report.

---

## 20. Import dry-run report shape

The package importer should produce a dry-run report with this structure:

```json
{
  "package_code": "KE-PPRA-IT-2022-04",
  "package_version_label": "v0.2",
  "dry_run": true,
  "json_valid": true,
  "checksum_valid": true,
  "referential_integrity_valid": true,
  "fixture_imported": false,
  "import_target_state": "STRUCTURING",
  "activation_allowed": false,
  "object_counts": {
    "sections": 0,
    "clauses": 0,
    "parameters": 0,
    "rules": 0,
    "forms": 0,
    "requirements": 0,
    "price_schedules": 0,
    "evaluation_schemas": 0,
    "contract_artifacts": 0,
    "render_blocks": 0,
    "smoke_tests": 0
  },
  "blockers": [],
  "warnings": [],
  "source_anomalies": [],
  "next_required_reviews": []
}
```

---

## 21. Acceptance criteria for this reconciliation plan

This plan is complete if the next implementer can:

1. Identify every current skeleton file.
2. Understand why each file must change.
3. Trace each change back to an extraction pass.
4. Preserve the distinction between official STD data and NSSF fixture data.
5. Build a v0.2 ZIP without guessing import order.
6. Keep activation blocked.
7. Produce a validation report.
8. Prepare the package for formal review.

---

## 22. Immediate next artifact

The next artifact should be:

**`KE-PPRA-IT-2022-04 Seed Package v0.2 ZIP`**

That artifact should apply this update plan to the skeleton and create a new downloadable package.

The ZIP should be accompanied by a short validation note, but the full validation report should be a separate follow-on artifact.

---

## 23. Final implementation warning

Do not let the existence of a ZIP imply legal readiness.

The correct state after v0.2 is:

```text
Import-ready: yes, for Draft/Structuring
Legally reviewed: no
Procurement reviewed: no
Renderer-approved: no
Smoke-tested in engine: no
Activatable: no
Usable for live tenders: no
```

That discipline is what prevents the STD Engine from becoming an unsafe document-template repository.
