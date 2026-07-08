# STD for Procurement of Information Technology — Seed Package Specification

**Project:** KenTender e-Procurement System  
**Module family:** Standard Tender Document Engine  
**Artifact:** Seed Package Specification  
**Target seed package:** `KE-PPRA-IT-2022-04`  
**Source STD:** PPRA Standard Tender Document for Procurement of Information Technology, DOC. 10  
**Calibration fixture:** NSSF SPS ERP Tender, Ref. `NSSFSPS/ICT/ERP/001/2025-2026`  
**Status:** Implementation planning artifact  

---

## 1. Purpose

This document converts the IT STD extraction matrix into a concrete seed package specification for importing the official PPRA Standard Tender Document for Procurement of Information Technology into the generalized STD Engine.

The goal is not to hard-code one tender type. The goal is to define a reusable seed package pattern that can be applied to multiple Standard Tender Documents while using the IT STD as the first production-grade implementation.

The seed package must allow the platform to:

1. Register an STD family and version.
2. Preserve source document traceability.
3. Import the official section structure.
4. Store locked legal text separately from configurable tender parameters.
5. Define tender-specific configuration fields.
6. Define structured bidder response forms.
7. Define technical requirements, system inventory, implementation schedule, price schedules, evaluation criteria, SCC fields, and contract forms.
8. Enforce mutability, validation, rendering, approval, versioning, and audit rules.
9. Generate tender documents, bidder submission schemas, evaluation instruments, and contract artifacts from the same active STD version.

---

## 2. Core design position

The seed package must not become an alternative tender document editor.

The STD Engine must treat the official STD as a governed, versioned, traceable legal template. Procurement users may configure permitted fields only. They must not directly edit locked sections such as Instructions to Tenderers or General Conditions of Contract.

The seed package is therefore divided into four conceptual layers:

| Layer | Purpose | Edited by ordinary procurement users? |
|---|---|---:|
| Legal template layer | STD family, version, section structure, locked clauses | No |
| Configuration layer | TDS, SCC, permitted options, tender identity, method, security, dates | Yes, through controlled UI only |
| Business requirement layer | IT requirements, implementation schedule, system inventory, price schedule structure | Yes, through controlled composer only |
| Generated artifact layer | Rendered tender document, bidder response forms, evaluation matrix, contract package | No direct edit after generation/publishing |

---

## 3. Relationship to previous artifacts

This specification depends on the following previously prepared artifacts:

1. `STD_Engine_Core_Module_Pre_PRD.md`
2. `STD_Engine_Core_Module_PRD.md`
3. `STD_Engine_Core_Domain_Model.md`
4. `STD_Engine_Core_Governance_Roles_Permissions_State_Model.md`
5. `STD_Engine_Core_Seed_Data_and_Smoke_Contracts.md`
6. `STD_Engine_Core_API_UI_Service_Contract.md`
7. `STD_Engine_Core_Cursor_Implementation_Pack.md`
8. `STD_IT_Extraction_Matrix.md`

The present document is the bridge between the extraction matrix and the actual importable seed package.

---

## 4. Package identity

### 4.1 STD family seed

| Field | Value |
|---|---|
| `family_code` | `KE-PPRA-IT` |
| `family_name` | `PPRA Standard Tender Document for Procurement of Information Technology` |
| `country_code` | `KE` |
| `authority_code` | `PPRA` |
| `procurement_category` | `INFORMATION_TECHNOLOGY` |
| `default_procurement_method_family` | `COMPETITIVE_TENDERING` |
| `supports_national_tendering` | `true` |
| `supports_international_tendering` | `true` |
| `supports_prequalification` | `true` |
| `supports_lots` | `true` |
| `supports_alternative_tenders` | `true`, controlled by TDS |
| `supports_margin_of_preference` | `true`, controlled by TDS/evaluation schema |
| `supports_reservations` | `true`, controlled by TDS |
| `active_version_policy` | One active version per family unless authority-specific exception is approved |

### 4.2 STD version seed

| Field | Value |
|---|---|
| `version_code` | `KE-PPRA-IT-2022-04` |
| `family_code` | `KE-PPRA-IT` |
| `version_label` | `April 2022 updated edition` |
| `source_document_title` | `Standard Tender Document for Procurement of Information Technology` |
| `source_document_number` | `DOC. 10` |
| `source_authority` | `Public Procurement Regulatory Authority` |
| `jurisdiction` | `Kenya` |
| `source_issue_date` | `2021-04-22` |
| `source_update_date` | `2022-04-21` |
| `initial_lifecycle_state` | `DRAFT` |
| `activation_requires_approval` | `true` |
| `immutable_after_activation` | `true` |
| `default_language` | `en` |

---

## 5. Seed package folder structure

The seed package should be stored as a folder, not as one monolithic JSON file.

Recommended package root:

```text
seed-packages/
  KE-PPRA-IT-2022-04/
    manifest.json
    README.md
    checksums.json
    source/
      source_document.json
      source_pages.json
      source_anchors.json
    template/
      family.json
      version.json
      sections.json
      section_order.json
      clauses.json
      clause_fragments.json
      mutability_map.json
    configuration/
      parameters.json
      parameter_options.json
      parameter_groups.json
      tds_schema.json
      scc_schema.json
    rules/
      rule_catalog.json
      rule_bindings.json
      rule_test_cases.json
    forms/
      form_catalog.json
      form_fields.json
      form_sections.json
      evidence_requirements.json
      bidder_response_schema.json
    requirements/
      requirement_categories.json
      requirement_schema.json
      requirement_compliance_schema.json
      requirement_templates.json
    schedules/
      implementation_schedule_schema.json
      site_table_schema.json
      holiday_table_schema.json
      system_inventory_schema.json
    pricing/
      price_schedule_catalog.json
      price_schedule_fields.json
      price_schedule_calculations.json
    evaluation/
      evaluation_schema.json
      responsiveness_checklist.json
      technical_evaluation_schema.json
      financial_evaluation_schema.json
      qualification_schema.json
    contract/
      contract_schema.json
      contract_forms.json
      contract_appendices.json
      acceptance_certificate_schema.json
      change_order_schema.json
    rendering/
      render_blocks.json
      render_templates.json
      render_order.json
      output_profiles.json
    workflow/
      lifecycle_bindings.json
      approval_bindings.json
      addendum_impact_rules.json
    fixtures/
      nssf_erp/
        fixture_manifest.json
        tender_configuration_values.json
        requirements_fixture.json
        evaluation_fixture.json
        price_schedule_fixture.json
        contract_fixture.json
    tests/
      import_smoke_tests.json
      validation_smoke_tests.json
      rendering_smoke_tests.json
      tender_binding_smoke_tests.json
      addendum_smoke_tests.json
```

This structure makes review, diffing, validation, and future STD onboarding much safer than maintaining a single giant JSON file.

---

## 6. Import order

The import process must be deterministic. The importer must reject packages that attempt to import dependent records before their parents exist.

### 6.1 Required import sequence

| Step | Module | Depends on |
|---:|---|---|
| 1 | `manifest.json` | None |
| 2 | `source/source_document.json` | Manifest |
| 3 | `template/family.json` | Manifest |
| 4 | `template/version.json` | Family, source document |
| 5 | `template/sections.json` | Version |
| 6 | `template/section_order.json` | Sections |
| 7 | `template/mutability_map.json` | Sections |
| 8 | `template/clauses.json` | Sections, source anchors |
| 9 | `template/clause_fragments.json` | Clauses |
| 10 | `configuration/parameter_groups.json` | Version, sections |
| 11 | `configuration/parameters.json` | Parameter groups, sections |
| 12 | `configuration/parameter_options.json` | Parameters |
| 13 | `configuration/tds_schema.json` | Parameters |
| 14 | `configuration/scc_schema.json` | Parameters |
| 15 | `rules/rule_catalog.json` | Parameters, sections, clauses |
| 16 | `rules/rule_bindings.json` | Rules, parameters/forms/sections |
| 17 | `forms/form_catalog.json` | Version, sections |
| 18 | `forms/form_sections.json` | Forms |
| 19 | `forms/form_fields.json` | Forms, parameters, evidence requirements |
| 20 | `forms/evidence_requirements.json` | Forms, fields |
| 21 | `requirements/*` | Version, sections, forms |
| 22 | `schedules/*` | Version, sections, requirements |
| 23 | `pricing/*` | Schedules, inventory, forms |
| 24 | `evaluation/*` | Requirements, forms, rules, pricing |
| 25 | `contract/*` | SCC, pricing, award data, forms |
| 26 | `rendering/*` | Sections, clauses, parameters, forms, schedules, pricing, contract |
| 27 | `workflow/*` | Version, rules, governance seed data |
| 28 | `fixtures/*` | Active package structures; fixtures must not be imported as master STD records unless explicitly requested |
| 29 | `tests/*` | All package modules |

### 6.2 Importer behavior

The importer must:

1. Validate all JSON files against the seed package schema before writing database records.
2. Confirm that the package identifier in every file matches `KE-PPRA-IT-2022-04`.
3. Validate source hash references before importing clauses and source anchors.
4. Reject duplicate stable keys inside a package.
5. Reject references to missing sections, forms, parameters, rules, or render blocks.
6. Import into `DRAFT` state only.
7. Prevent activation until package review and approval are completed.
8. Generate an import report listing created, updated, skipped, and rejected records.
9. Never overwrite an active STD version.
10. Never silently change a locked clause or legal section.

---

## 7. Naming conventions and stable keys

### 7.1 General key pattern

Use stable, human-readable keys.

```text
<package_code>.<domain>.<section_or_group>.<name>
```

Examples:

```text
KE-PPRA-IT-2022-04.section.ITT
KE-PPRA-IT-2022-04.parameter.tds.tender_validity_days
KE-PPRA-IT-2022-04.rule.tds.tender_security_required_when_selected
KE-PPRA-IT-2022-04.form.form_of_tender
KE-PPRA-IT-2022-04.requirement.functional
KE-PPRA-IT-2022-04.price.grand_summary
KE-PPRA-IT-2022-04.render.section_v_requirements
```

### 7.2 Rules for stable keys

1. Stable keys must never depend on database IDs.
2. Stable keys must not change when display labels change.
3. Stable keys must include the package version code.
4. Stable keys must be unique inside the package.
5. Future corrected versions must use a new version code, not mutate existing active keys.

---

## 8. Manifest specification

File: `manifest.json`

### 8.1 Required fields

```json
{
  "package_code": "KE-PPRA-IT-2022-04",
  "package_type": "STD_TEMPLATE_SEED",
  "schema_version": "1.0.0",
  "family_code": "KE-PPRA-IT",
  "version_code": "KE-PPRA-IT-2022-04",
  "jurisdiction": "KE",
  "authority": "PPRA",
  "procurement_category": "INFORMATION_TECHNOLOGY",
  "source_document_number": "DOC. 10",
  "source_update_date": "2022-04-21",
  "language": "en",
  "created_by": "seed-author",
  "created_at": "<ISO-8601 timestamp>",
  "requires_approval_before_activation": true,
  "immutable_after_activation": true,
  "contains_locked_legal_text": true,
  "contains_fixture_data": true,
  "fixture_data_import_policy": "DO_NOT_IMPORT_BY_DEFAULT"
}
```

### 8.2 Manifest validation rules

| Rule | Severity |
|---|---|
| `package_code` must match folder name | Blocker |
| `family_code` must exist or be created by this package | Blocker |
| `version_code` must be unique | Blocker |
| `schema_version` must be supported by importer | Blocker |
| `contains_fixture_data=true` requires fixture policy | Blocker |
| Missing source document metadata | Blocker |

---

## 9. Source traceability module

The source traceability module is mandatory. Every imported section, locked clause, configurable parameter, form, and render block should be traceable back to the official STD source.

### 9.1 `source_document.json`

Required fields:

```json
{
  "source_document_key": "KE-PPRA-IT-DOC-10-2022-04",
  "title": "Standard Tender Document for Procurement of Information Technology",
  "document_number": "DOC. 10",
  "authority": "Public Procurement Regulatory Authority",
  "jurisdiction": "Kenya",
  "issue_date": "2021-04-22",
  "update_date": "2022-04-21",
  "file_name": "DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.doc",
  "file_hash_sha256": "<computed at import>",
  "page_count": 181,
  "source_type": "OFFICIAL_STD",
  "copyright_notice_present": true
}
```

### 9.2 `source_anchors.json`

Each source anchor should point to a precise source location.

```json
{
  "anchor_key": "KE-PPRA-IT-2022-04.anchor.section_i_itt",
  "source_document_key": "KE-PPRA-IT-DOC-10-2022-04",
  "part_label": "PART 1 - Tendering Procedures",
  "section_label": "Section I - Instructions to Tenderers",
  "clause_label": null,
  "page_start": 15,
  "page_end": 35,
  "paragraph_start": null,
  "paragraph_end": null,
  "source_hash_sha256": "<normalized excerpt hash>"
}
```

### 9.3 Source traceability rules

| Requirement | Rationale |
|---|---|
| Every locked clause must have a source anchor | Legal defensibility |
| Every configurable parameter must identify the STD provision it supplements | Avoid unauthorized additions |
| Every render block must identify its source section | Reproducible tender generation |
| Source hashes must be generated from normalized text | Stable comparison |
| Import must fail if a source anchor references a missing source document | Prevent orphaned legal content |

---

## 10. Section seed specification

File: `template/sections.json`

### 10.1 Required section fields

```json
{
  "section_key": "KE-PPRA-IT-2022-04.section.tds",
  "version_code": "KE-PPRA-IT-2022-04",
  "section_code": "TDS",
  "part_code": "PART_1",
  "display_title": "Section II - Tender Data Sheet",
  "canonical_order": 20,
  "parent_section_key": null,
  "mutability_type": "CONFIGURABLE_CONTROLLED",
  "render_required": true,
  "included_in_issued_tender": true,
  "source_anchor_key": "KE-PPRA-IT-2022-04.anchor.section_ii_tds"
}
```

### 10.2 Core IT STD section seeds

| Section code | Display title | Mutability | Issued to bidders? | Notes |
|---|---|---|---:|---|
| `COVER` | Cover / title identity page | Generated parameterized | Yes | Starts issued tender after excluded preface materials |
| `INVITATION` | Invitation to Tender | Generated parameterized | Usually yes, depending tender publication policy | May also exist as notice outside tender document |
| `ITT` | Instructions to Tenderers | Locked | Yes | No ordinary user edits |
| `TDS` | Tender Data Sheet | Configurable controlled | Yes | Supplements ITT |
| `EVAL_QUAL` | Evaluation and Qualification Criteria | Controlled configurable | Yes | Criteria must remain within STD-permitted model |
| `TENDERING_FORMS` | Tendering Forms | Structured forms | Yes | Bidder response schema generated from here |
| `REQ_INFO_SYSTEM` | Requirements of the Information System | Controlled authored requirements | Yes | PE-authored using composer |
| `TECH_REQ` | Technical Requirements | Controlled authored requirements | Yes | Functional, architectural, performance, service, technology specs |
| `IMPL_SCHEDULE` | Implementation Schedule | Structured schedule | Yes | Linked to inventory and price schedules |
| `SYSTEM_INVENTORY` | System Inventory Tables | Structured inventory | Yes | Supply/install and recurrent cost items |
| `BACKGROUND` | Background and Informational Materials | Informational only | Yes, if provided | Must not introduce requirements |
| `GCC` | General Conditions of Contract | Locked | Yes | No ordinary user edits |
| `SCC` | Special Conditions of Contract | Configurable controlled | Yes | Supplements GCC |
| `CONTRACT_FORMS` | Contract Forms | Generated / post-award structured | Yes / post-award | Contract agreement, securities, acceptance certificates, change orders |

### 10.3 Mutability enum values

| Enum | Meaning |
|---|---|
| `LOCKED_LEGAL_TEXT` | Text must not be edited in tender configuration |
| `CONFIGURABLE_CONTROLLED` | User may select/enter values only through controlled schema |
| `CONTROLLED_AUTHORED_REQUIREMENTS` | User may author procurement-specific requirements through structured composer |
| `STRUCTURED_FORM_SCHEMA` | Defines bidder or contract forms and fields |
| `STRUCTURED_PRICE_SCHEMA` | Defines price schedule tables, calculations, and submission fields |
| `STRUCTURED_SCHEDULE_SCHEMA` | Defines implementation and site schedules |
| `GENERATED_PARAMETERIZED` | Rendered from parameters and locked template text |
| `INFORMATIONAL_REFERENCE` | Context only; cannot impose obligations unless obligation is also in requirements |
| `SYSTEM_GENERATED_AUDIT` | Audit/legal metadata generated by system |

---

## 11. Clause seed specification

File: `template/clauses.json`

### 11.1 Clause fields

```json
{
  "clause_key": "KE-PPRA-IT-2022-04.clause.itt.1_scope_of_tender",
  "section_key": "KE-PPRA-IT-2022-04.section.itt",
  "clause_number": "1",
  "clause_title": "Scope of Tender",
  "clause_text_source": "SOURCE_EXTRACT",
  "text_hash_sha256": "<computed from normalized source text>",
  "mutability_type": "LOCKED_LEGAL_TEXT",
  "parameterized": true,
  "parameter_bindings": [
    "KE-PPRA-IT-2022-04.parameter.tds.tender_name",
    "KE-PPRA-IT-2022-04.parameter.tds.tender_identification_number"
  ],
  "source_anchor_key": "KE-PPRA-IT-2022-04.anchor.itt.1"
}
```

### 11.2 Clause import rules

1. Locked clauses must be imported from the official source extraction, not typed manually in application code.
2. Clause text must be normalized before hashing.
3. Parameter placeholders may be stored separately from source text where the source text contains blanks or bracketed instructions.
4. Active clause records must be immutable.
5. Any correction to clause text after activation requires a new STD version or a formally governed erratum process.

---

## 12. Parameter seed specification

Files:

- `configuration/parameter_groups.json`
- `configuration/parameters.json`
- `configuration/parameter_options.json`
- `configuration/tds_schema.json`
- `configuration/scc_schema.json`

### 12.1 Parameter fields

```json
{
  "parameter_key": "KE-PPRA-IT-2022-04.parameter.tds.tender_validity_days",
  "version_code": "KE-PPRA-IT-2022-04",
  "group_key": "KE-PPRA-IT-2022-04.parameter_group.tds.dates",
  "display_label": "Period of Validity of Tenders",
  "field_type": "INTEGER",
  "required": true,
  "default_value": null,
  "min_value": 1,
  "max_value": null,
  "unit": "days",
  "applies_to_section_key": "KE-PPRA-IT-2022-04.section.tds",
  "source_anchor_key": "KE-PPRA-IT-2022-04.anchor.tds.validity",
  "render_binding_keys": [
    "KE-PPRA-IT-2022-04.render.invitation",
    "KE-PPRA-IT-2022-04.render.tds"
  ],
  "validation_rule_keys": [
    "KE-PPRA-IT-2022-04.rule.tds.validity_positive_integer"
  ]
}
```

### 12.2 Initial TDS parameter inventory

This is the initial seed inventory. It may be expanded during full extraction.

| Parameter key suffix | Field type | Required | Controlled? | Notes |
|---|---|---:|---:|---|
| `tds.procuring_entity_name` | Text | Yes | No | Used across cover, invitation, TDS, forms |
| `tds.procuring_entity_address` | Multiline text | Yes | No | Physical/postal/contact data may be structured separately |
| `tds.tender_name` | Text | Yes | No | Also rendered in Form of Tender |
| `tds.tender_number` | Text | Yes | No | Must be unique per PE/tender |
| `tds.procurement_method` | Select | Yes | Yes | National/International/open/restricted as permitted |
| `tds.lots_enabled` | Boolean | Yes | Yes | Activates lot configuration |
| `tds.number_of_lots` | Integer | Conditional | No | Required if lots enabled |
| `tds.max_jv_members` | Integer | Yes | No | Must be reasonable and controlled by governance policy |
| `tds.prequalification_used` | Boolean | Yes | Yes | Impacts forms/evaluation |
| `tds.alternative_tenders_permitted` | Boolean | Yes | Yes | Controls alternative tender rules |
| `tds.margin_of_preference_applies` | Boolean | Yes | Yes | Activates preference calculation rules |
| `tds.reservation_applies` | Boolean | Yes | Yes | Activates reservation group fields |
| `tds.reservation_group` | Select/multiselect | Conditional | Yes | Required if reservation applies |
| `tds.clarification_address` | Structured address | Yes | No | Rendered in TDS/invitation |
| `tds.clarification_deadline_days_before_submission` | Integer | Yes | No | Validation against submission date |
| `tds.pre_tender_meeting_required` | Boolean | Yes | Yes | Activates meeting date/location |
| `tds.pre_tender_meeting_datetime` | Datetime | Conditional | No | Required if meeting required |
| `tds.site_visit_required` | Boolean | Optional | Yes | Useful for IT site/context inspections |
| `tds.site_visit_datetime` | Datetime | Conditional | No | Required if site visit required |
| `tds.tender_submission_deadline` | Datetime | Yes | No | Must be after publication and clarification deadline |
| `tds.tender_opening_datetime` | Datetime | Yes | No | Usually same as/after submission deadline |
| `tds.tender_opening_address` | Structured address | Yes | No | Rendered in invitation/TDS |
| `tds.electronic_tenders_permitted` | Boolean | Yes | Yes | Affects submission instructions |
| `tds.number_of_originals` | Integer | Yes | No | Physical submission setup |
| `tds.number_of_copies` | Integer | Yes | No | Physical submission setup |
| `tds.currency_of_tender` | Currency code | Yes | Yes | KES default; foreign currency possible if international |
| `tds.currency_of_payment` | Currency code | Yes | Yes | May differ by permitted rules |
| `tds.price_adjustment_permitted` | Boolean | Yes | Yes | Activates price adjustment clauses if allowed |
| `tds.tender_validity_days` | Integer | Yes | No | Rendered in invitation/form |
| `tds.tender_security_type` | Select | Yes | Yes | Tender security, declaration, professional indemnity, none if permitted |
| `tds.tender_security_amount` | Money | Conditional | No | Required if monetary security selected |
| `tds.professional_indemnity_required` | Boolean | Optional | Yes | Seen in NSSF calibration fixture; should be controlled as evidence/security variant |
| `tds.professional_indemnity_amount` | Money | Conditional | No | Required if PI required |
| `tds.foreign_tenderer_40_percent_rule_applies` | Boolean | Yes | Yes | Activates evidence requirement |
| `tds.subcontracting_allowed` | Boolean | Yes | Yes | Activates subcontractor schedule |
| `tds.max_subcontracting_percent` | Decimal | Conditional | No | Required if subcontracting is allowed and limit applies |

### 12.3 Initial SCC parameter inventory

| Parameter key suffix | Field type | Required | Notes |
|---|---|---:|---|
| `scc.contract_effectiveness_condition` | Multiline text/select | Yes | Determines when project timelines start |
| `scc.performance_security_percent` | Decimal | Yes | May be rendered as percentage of contract price |
| `scc.performance_security_validity_days_after_completion` | Integer | Yes | Controls security validity |
| `scc.advance_payment_allowed` | Boolean | Yes | Activates advance payment security |
| `scc.payment_milestone_model` | Structured table | Yes | Must link to implementation schedule |
| `scc.warranty_period_months` | Integer | Yes | May be per phase/subsystem |
| `scc.post_warranty_support_required` | Boolean | Yes | Links to recurrent cost schedule |
| `scc.operational_acceptance_time_limit` | Duration | Optional | Used for acceptance/liquidated damages logic |
| `scc.liquidated_damages_apply` | Boolean | Yes | Activates LD fields |
| `scc.liquidated_damages_rate` | Decimal/money | Conditional | Required if LD applies |
| `scc.ipr_ownership_model` | Select | Yes | Custom software/materials/license ownership |
| `scc.software_license_model` | Select/multiselect | Yes | Standard, custom, third-party, subscription, SaaS |
| `scc.confidentiality_period` | Duration | Optional | Contractual confidentiality behavior |
| `scc.dispute_resolution_forum` | Select | Yes | Domestic/international options if allowed |
| `scc.adjudicator_required` | Boolean | Yes | Activates adjudicator appendix |
| `scc.change_order_procedure_enabled` | Boolean | Yes | Should be true for IT system implementation |

---

## 13. Rule seed specification

Files:

- `rules/rule_catalog.json`
- `rules/rule_bindings.json`
- `rules/rule_test_cases.json`

### 13.1 Rule fields

```json
{
  "rule_key": "KE-PPRA-IT-2022-04.rule.tds.submission_before_opening",
  "version_code": "KE-PPRA-IT-2022-04",
  "rule_type": "VALIDATION",
  "severity": "BLOCKER",
  "lifecycle_stage": "TENDER_CONFIGURATION",
  "expression_language": "JSON_LOGIC",
  "expression": {
    "<=": [
      { "var": "tds.tender_submission_deadline" },
      { "var": "tds.tender_opening_datetime" }
    ]
  },
  "message": "Tender opening date/time must not be earlier than the tender submission deadline.",
  "affected_parameter_keys": [
    "KE-PPRA-IT-2022-04.parameter.tds.tender_submission_deadline",
    "KE-PPRA-IT-2022-04.parameter.tds.tender_opening_datetime"
  ],
  "legal_basis_anchor_key": "KE-PPRA-IT-2022-04.anchor.itt.opening"
}
```

### 13.2 Initial rule catalog

| Rule key suffix | Type | Severity | Stage | Purpose |
|---|---|---|---|---|
| `tds.required_identity_fields` | Validation | Blocker | Tender configuration | PE name, tender name, tender number required |
| `tds.submission_before_opening` | Validation | Blocker | Tender configuration | Opening cannot precede submission deadline |
| `tds.clarification_before_submission` | Validation | Blocker | Tender configuration | Clarification deadline must precede submission deadline |
| `tds.pre_tender_meeting_before_submission` | Validation | Blocker | Tender configuration | Meeting must precede submission if required |
| `tds.lots_count_required_if_enabled` | Activation/validation | Blocker | Tender configuration | Lots fields required when lots enabled |
| `tds.reservation_group_required_if_reservation_applies` | Activation/validation | Blocker | Tender configuration | Reservation group required if reservation applies |
| `tds.tender_security_amount_required` | Activation/validation | Blocker | Tender configuration | Security amount required when monetary security selected |
| `tds.professional_indemnity_amount_required` | Activation/validation | Blocker | Tender configuration | PI amount required when PI required |
| `tds.alternative_tender_sections_hidden_if_not_permitted` | Activation | Blocker | Rendering/evaluation | Alternative tender fields disabled if not permitted |
| `tds.foreign_tenderer_40_percent_rule_evidence` | Activation | Blocker | Bid submission | Requires foreign tenderer local input evidence if activated |
| `requirements.background_cannot_create_obligations` | Validation | Blocker | Tender configuration | Background materials cannot define mandatory requirements |
| `requirements.must_have_unique_requirement_ids` | Validation | Blocker | Tender configuration | Requirement IDs must be stable and unique |
| `requirements.mandatory_requirement_requires_compliance_response` | Validation | Blocker | Bid submission | Mandatory technical requirements need supplier response |
| `schedule.inventory_price_link_required` | Validation | Blocker | Tender configuration | Inventory items must map to price schedule lines |
| `schedule.implementation_price_link_required` | Validation | Blocker | Tender configuration | Milestones must link to deliverables/pricing where applicable |
| `pricing.grand_total_must_equal_subtotals` | Calculation/validation | Blocker | Bid submission | Grand total must match supply/install plus recurrent totals |
| `pricing.blank_price_treatment_warning` | Validation | Warning | Bid submission/evaluation | Blank items require controlled treatment |
| `evaluation.minimum_pass_mark_required_if_scored` | Validation | Blocker | Tender configuration | Scored technical evaluation must define pass mark |
| `evaluation.weights_sum_to_100` | Validation | Blocker | Tender configuration | Scoring weights must total 100 or configured total |
| `contract.payment_milestones_match_schedule` | Validation | Blocker | Contract formation | SCC payment milestones must match accepted implementation milestones |
| `contract.acceptance_certificate_required_per_phase` | Activation | Blocker | Contract execution | Acceptance certificates required for configured phases |
| `governance.active_template_immutable` | Governance | Blocker | Template administration | Active version cannot be edited |
| `governance.used_template_not_deletable` | Governance | Blocker | Template administration | Used version cannot be deleted |
| `governance.published_tender_bundle_immutable` | Governance | Blocker | Tender publication | Published output cannot be edited directly |
| `governance.post_publication_change_requires_addendum` | Governance | Blocker | Addendum | Changes after publication require addendum |

---

## 14. Form seed specification

Files:

- `forms/form_catalog.json`
- `forms/form_sections.json`
- `forms/form_fields.json`
- `forms/evidence_requirements.json`
- `forms/bidder_response_schema.json`

### 14.1 Form catalog fields

```json
{
  "form_key": "KE-PPRA-IT-2022-04.form.form_of_tender",
  "version_code": "KE-PPRA-IT-2022-04",
  "form_code": "FORM_OF_TENDER",
  "display_title": "Form of Tender",
  "section_key": "KE-PPRA-IT-2022-04.section.tendering_forms",
  "respondent_type": "TENDERER",
  "submission_stage": "TENDER_SUBMISSION",
  "required": true,
  "repeatable": false,
  "source_anchor_key": "KE-PPRA-IT-2022-04.anchor.form.form_of_tender"
}
```

### 14.2 Initial IT form catalog

| Form code | Respondent | Required | Repeatable | Notes |
|---|---|---:|---:|---|
| `FORM_OF_TENDER` | Tenderer | Yes | No | Price summary and commitment |
| `CONFIDENTIAL_BUSINESS_QUESTIONNAIRE` | Tenderer | Yes | No | Eligibility/business details |
| `CERTIFICATE_INDEPENDENT_TENDER_DETERMINATION` | Tenderer | Yes | No | Anti-collusion declaration |
| `SELF_DECLARATION_FRAUD_CORRUPTION` | Tenderer | Yes | No | Corruption/debarment declaration |
| `FOREIGN_TENDERER_40_PERCENT_RULE` | Tenderer | Conditional | No | Required when applicable |
| `ELI_1_TENDERER_INFORMATION` | Tenderer | Yes | No | Tenderer details |
| `ELI_1_JV_MEMBER_INFORMATION` | Tenderer/JV member | Conditional | Repeatable | Required for JVs |
| `CON_1_CONTRACT_NON_PERFORMANCE` | Tenderer | Yes | Repeatable if needed | Non-performance/litigation |
| `EXP_1_GENERAL_EXPERIENCE` | Tenderer | Conditional | Repeatable | Qualification |
| `EXP_2_SPECIFIC_EXPERIENCE` | Tenderer | Conditional | Repeatable | Similar IT experience |
| `CCC_1_CURRENT_COMMITMENTS` | Tenderer | Conditional | Repeatable | Work in progress |
| `FIN_1_FINANCIAL_SITUATION` | Tenderer | Conditional | Repeatable | Financial statements |
| `FIN_2_AVERAGE_ANNUAL_TURNOVER` | Tenderer | Conditional | Repeatable | Turnover qualification |
| `FIN_3_FINANCIAL_RESOURCES` | Tenderer | Conditional | Repeatable | Liquid assets/credit |
| `PERSONNEL_CAPABILITIES` | Tenderer | Conditional | Repeatable | Key personnel |
| `IPR_SOFTWARE_CATEGORY_LIST` | Tenderer | Yes | Repeatable | Standard/custom/third-party materials |
| `CONFORMANCE_INFORMATION_SYSTEM_MATERIALS` | Tenderer | Yes | Repeatable | Technical conformance |
| `PRICE_GRAND_SUMMARY` | Tenderer | Yes | No | Pricing |
| `SUPPLY_INSTALL_COST_SUMMARY` | Tenderer | Yes | No | Pricing |
| `RECURRENT_COST_SUMMARY` | Tenderer | Conditional | No | Pricing |
| `SUPPLY_INSTALL_COST_SUB_TABLE` | Tenderer | Yes | Repeatable | Pricing/inventory linked |
| `RECURRENT_COST_SUB_TABLE` | Tenderer | Conditional | Repeatable | Pricing/inventory linked |
| `COUNTRY_OF_ORIGIN_CODE_TABLE` | Tenderer | Conditional | Repeatable | Goods/services origin |

### 14.3 Evidence requirement pattern

```json
{
  "evidence_key": "KE-PPRA-IT-2022-04.evidence.tax_compliance_certificate",
  "display_label": "Valid Tax Compliance Certificate",
  "evidence_type": "DOCUMENT_UPLOAD",
  "required_stage": "TENDER_SUBMISSION",
  "applies_to_form_key": "KE-PPRA-IT-2022-04.form.eli_1_tenderer_information",
  "validity_required": true,
  "expiry_date_field_required": true,
  "verification_required": true,
  "verification_mode": "MANUAL_OR_INTEGRATION",
  "activation_rule_key": null
}
```

---

## 15. IT requirements seed specification

Files:

- `requirements/requirement_categories.json`
- `requirements/requirement_schema.json`
- `requirements/requirement_compliance_schema.json`
- `requirements/requirement_templates.json`

### 15.1 Requirement category seeds

| Category code | Display label | Purpose |
|---|---|---|
| `FUNCTIONAL` | Functional Requirements | Business functions the system must perform |
| `ARCHITECTURAL` | Architectural Requirements | Deployment, architecture, scalability, integrations |
| `PERFORMANCE` | Performance Requirements | Availability, throughput, response time, volume |
| `SECURITY` | Security Requirements | Authentication, authorization, audit, encryption, compliance |
| `SERVICE` | Service Specifications | Implementation, support, training, warranty, maintenance |
| `TECHNOLOGY` | Technology Specifications | Hardware, software, cloud, platform, standards |
| `DATA_MIGRATION` | Data Migration Requirements | Extraction, cleansing, transformation, migration, validation |
| `INTEGRATION` | Integration Requirements | APIs, external systems, middleware, protocols |
| `TESTING_ACCEPTANCE` | Testing and Acceptance | UAT, performance testing, acceptance certificates |
| `DOCUMENTATION` | Documentation Requirements | Manuals, admin guides, architecture, configuration docs |
| `TRAINING` | Training and Knowledge Transfer | User, technical, administrator, executive training |
| `SUPPORT_MAINTENANCE` | Warranty and Support | SLAs, escalation, local support, AMC |
| `COMPLIANCE_REGULATORY` | Regulatory Compliance | Sector-specific compliance such as reporting obligations |
| `BACKGROUND_INFORMATIONAL` | Background and Informational Materials | Context only, not obligations |

### 15.2 Requirement schema fields

```json
{
  "requirement_key": "<generated per tender instance unless master template requirement>",
  "category_code": "FUNCTIONAL",
  "requirement_number": "FR-001",
  "module_or_subsystem": "Pension Administration",
  "requirement_title": "Member registration and bio-data management",
  "requirement_description": "<PE-authored requirement text>",
  "mandatory_type": "MANDATORY",
  "supplier_response_required": true,
  "evidence_required": false,
  "compliance_response_type": "YES_NO_REFERENCE_COMMENTARY",
  "evaluation_binding": "TECHNICAL_CONFORMANCE",
  "inventory_binding_required": false,
  "price_binding_required": false,
  "source_type": "TENDER_CONFIGURATION",
  "source_anchor_key": null
}
```

### 15.3 Supplier compliance response schema

The seed package must define a reusable response pattern for IT technical requirements:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `requirement_key` | Reference | Yes | Requirement being answered |
| `compliance_status` | Select | Yes | `COMPLY`, `PARTIALLY_COMPLY`, `DO_NOT_COMPLY`, `NOT_APPLICABLE_IF_ALLOWED` |
| `supplier_commentary` | Long text | Yes | Must explain how requirement is met |
| `reference_pages` | Text/list | Conditional | Required where tender asks for reference pages |
| `evidence_attachment_ids` | Attachment list | Conditional | Required when evidence rule applies |
| `exception_or_deviation` | Long text | Conditional | Required if partial/non-compliance allowed |
| `evaluator_finding` | Select | Evaluation only | `ACCEPTED`, `CLARIFICATION_REQUIRED`, `REJECTED` |
| `evaluator_notes` | Long text | Evaluation only | Audit trail |

### 15.4 Background material rule

Background and informational materials must be stored separately from requirements. They may help bidders understand context but must not introduce obligations unless the obligation is also stated in the Technical Requirements or Requirements of the Information System.

---

## 16. Implementation schedule seed specification

Files:

- `schedules/implementation_schedule_schema.json`
- `schedules/site_table_schema.json`
- `schedules/holiday_table_schema.json`

### 16.1 Implementation schedule fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `schedule_line_key` | Stable key | Yes | Unique line item |
| `line_number` | Text | Yes | Human-readable line reference |
| `deliverable_or_subsystem` | Text | Yes | Must map to inventory/price where applicable |
| `site_key` | Reference | Conditional | Required if site-specific |
| `supplier_obligation` | Text | Yes | What supplier must deliver |
| `pe_dependency` | Text | Optional | PE obligations/dependencies |
| `duration_weeks_from_effectiveness` | Integer | Conditional | Recommended base timing |
| `target_completion_date` | Date | Optional | May be calculated from effectiveness |
| `acceptance_required` | Boolean | Yes | Links to acceptance certificate |
| `liquidated_damages_milestone` | Boolean | Optional | Controlled by SCC |
| `price_schedule_binding_required` | Boolean | Yes | Links schedule to price |
| `inventory_binding_required` | Boolean | Yes | Links schedule to inventory |

### 16.2 Site table fields

| Field | Type | Required |
|---|---|---:|
| `site_key` | Stable key | Yes |
| `site_name` | Text | Yes |
| `physical_address` | Structured address | Yes |
| `department_or_unit` | Text | Optional |
| `floor_room_building` | Text | Optional |
| `delivery_installation_constraints` | Long text | Optional |
| `network_power_cabling_notes` | Long text | Optional |

### 16.3 Holiday/non-working day table

The package should provide a schema, not hard-coded dates. Actual dates are tender-specific configuration values.

---

## 17. System inventory seed specification

File: `schedules/system_inventory_schema.json`

### 17.1 Inventory types

| Inventory type | Description |
|---|---|
| `SUPPLY_INSTALL` | Components supplied, installed, configured, customized, tested, or commissioned |
| `RECURRENT_COST` | Warranty, support, maintenance, licenses, subscriptions, post-warranty services |

### 17.2 Supply/install inventory fields

| Field | Type | Required |
|---|---|---:|
| `inventory_item_key` | Stable key | Yes |
| `line_item_number` | Text | Yes |
| `component_number` | Text | Yes |
| `component_name` | Text | Yes |
| `subsystem_or_module` | Text/reference | Yes |
| `relevant_technical_specification_refs` | Requirement references | Yes |
| `site_key` | Reference | Conditional |
| `quantity` | Decimal | Yes |
| `unit_of_measure` | Text/select | Yes |
| `price_schedule_binding_key` | Reference | Yes |

### 17.3 Recurrent cost inventory fields

| Field | Type | Required |
|---|---|---:|
| `recurrent_item_key` | Stable key | Yes |
| `line_item_number` | Text | Yes |
| `component_name` | Text | Yes |
| `recurrent_cost_category` | Select | Yes |
| `technical_specification_refs` | Requirement references | Conditional |
| `year_1_quantity_or_days` | Decimal | Conditional |
| `year_2_quantity_or_days` | Decimal | Conditional |
| `year_3_quantity_or_days` | Decimal | Conditional |
| `warranty_period_included` | Boolean | Yes |
| `post_warranty_required` | Boolean | Yes |
| `price_schedule_binding_key` | Reference | Yes |

---

## 18. Price schedule seed specification

Files:

- `pricing/price_schedule_catalog.json`
- `pricing/price_schedule_fields.json`
- `pricing/price_schedule_calculations.json`

### 18.1 Price schedule catalog

| Schedule code | Required | Repeatable | Purpose |
|---|---:|---:|---|
| `GRAND_SUMMARY_COST_TABLE` | Yes | No | Total tender price summary |
| `SUPPLY_INSTALL_COST_SUMMARY` | Yes | No | Summary of supply/install costs |
| `RECURRENT_COST_SUMMARY` | Conditional | No | Summary of recurrent costs |
| `SUPPLY_INSTALL_COST_SUB_TABLE` | Yes | Repeatable | Detailed line pricing by inventory/schedule |
| `RECURRENT_COST_SUB_TABLE` | Conditional | Repeatable | Recurrent cost line pricing |
| `COUNTRY_OF_ORIGIN_CODE_TABLE` | Conditional | Repeatable | Origin coding for goods/services |

### 18.2 Standard monetary fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `currency` | Currency code | Yes | Controlled by TDS |
| `unit_price_excluding_taxes` | Money | Conditional | Required for itemized prices |
| `quantity` | Decimal | Yes | Pulled from inventory where locked |
| `line_total_excluding_taxes` | Money calculated | Yes | Quantity × unit price |
| `tax_amount` | Money | Conditional | VAT or other taxes |
| `line_total_including_taxes` | Money calculated | Yes | Excluding taxes + tax amount |
| `recurrent_year` | Integer | Conditional | Required for recurrent costs |
| `warranty_included_flag` | Boolean | Conditional | Useful for warranty period pricing |

### 18.3 Price calculation rules

| Calculation | Rule |
|---|---|
| Supply/install subtotal | Sum all supply/install sub-table line totals |
| Recurrent subtotal | Sum all recurrent sub-table line totals for selected years/periods |
| Grand total excluding taxes | Supply/install subtotal + recurrent subtotal + any other permitted cost group |
| VAT/tax summary | Sum tax amounts by configured tax type |
| Grand total including taxes | Grand total excluding taxes + tax totals |
| Blank line treatment | Must be controlled by STD rule and evaluation policy |

---

## 19. Evaluation seed specification

Files:

- `evaluation/evaluation_schema.json`
- `evaluation/responsiveness_checklist.json`
- `evaluation/technical_evaluation_schema.json`
- `evaluation/financial_evaluation_schema.json`
- `evaluation/qualification_schema.json`

### 19.1 Evaluation stages

| Stage code | Stage name | Output |
|---|---|---|
| `PRELIMINARY_RESPONSIVENESS` | Preliminary responsiveness examination | Responsive / non-responsive |
| `TECHNICAL_QUALIFICATION` | Minimum qualification assessment | Qualified / not qualified |
| `TECHNICAL_EVALUATION` | Technical scoring or conformance assessment | Score / pass-fail |
| `FINANCIAL_EVALUATION` | Price evaluation | Evaluated price |
| `POST_QUALIFICATION` | Final qualification confirmation | Qualified / rejected |
| `AWARD_RECOMMENDATION` | Lowest evaluated responsive tender | Recommended awardee |

### 19.2 Evaluation item fields

| Field | Type | Required |
|---|---|---:|
| `evaluation_item_key` | Stable key | Yes |
| `stage_code` | Select | Yes |
| `criterion_title` | Text | Yes |
| `criterion_description` | Long text | Yes |
| `criterion_type` | Select | Yes |
| `mandatory` | Boolean | Yes |
| `max_points` | Decimal | Conditional |
| `minimum_points` | Decimal | Conditional |
| `weight` | Decimal | Conditional |
| `supporting_documentation_required` | Boolean | Yes |
| `evidence_requirement_keys` | Reference list | Conditional |
| `requirement_bindings` | Requirement references | Optional |
| `form_bindings` | Form references | Optional |
| `rule_bindings` | Rule references | Optional |

### 19.3 Evaluation constraints

1. If the evaluation model is scored, total weights must sum to the configured total, usually 100.
2. Minimum technical pass mark must be explicitly configured if technical scoring is used.
3. Mandatory criteria must not be overridden by evaluator discretion.
4. Financial evaluation must consume the structured price schedule, not manually entered totals.
5. Evaluation records must cite the published tender document version and generated artifact hash.

---

## 20. Contract seed specification

Files:

- `contract/contract_schema.json`
- `contract/contract_forms.json`
- `contract/contract_appendices.json`
- `contract/acceptance_certificate_schema.json`
- `contract/change_order_schema.json`

### 20.1 Contract forms and appendices

| Contract artifact code | Generated from |
|---|---|
| `NOTIFICATION_OF_INTENTION_TO_AWARD` | Evaluation/award decision |
| `LETTER_OF_AWARD` | Award decision, tender identity, successful tenderer |
| `CONTRACT_AGREEMENT` | Tender, award, SCC, accepted price, accepted schedule |
| `SUPPLIER_REPRESENTATIVE_APPENDIX` | Supplier contract data |
| `ADJUDICATOR_APPENDIX` | SCC/adjudicator configuration |
| `APPROVED_SUBCONTRACTORS_APPENDIX` | Tenderer subcontractor submissions and approval |
| `SOFTWARE_CATEGORIES_APPENDIX` | IPR/software category forms |
| `CUSTOM_MATERIALS_APPENDIX` | Custom materials/IPR submissions |
| `REVISED_PRICE_SCHEDULES_APPENDIX` | Final accepted prices if revised during finalization |
| `CONTRACT_FINALIZATION_MINUTES` | Finalization discussions |
| `PERFORMANCE_SECURITY` | SCC/security configuration |
| `ADVANCE_PAYMENT_SECURITY` | SCC/advance payment configuration |
| `INSTALLATION_CERTIFICATE` | Contract execution milestone |
| `OPERATIONAL_ACCEPTANCE_CERTIFICATE` | Acceptance milestone |
| `CHANGE_ORDER_FORM` | Contract change process |
| `BENEFICIAL_OWNERSHIP_DISCLOSURE` | Ownership disclosure requirement |

### 20.2 Contract formation rules

1. Contract forms must be generated from the published tender package, accepted tender, award decision, and SCC values.
2. Contract appendices must carry forward supplier submissions where legally relevant.
3. Any negotiated/finalized amendment must be recorded in a contract finalization record and must not contradict immutable tender obligations unless legally permitted.
4. Acceptance certificates must link to implementation schedule milestones.
5. Change orders must not be used to retroactively alter the original tender evaluation outcome.

---

## 21. Rendering seed specification

Files:

- `rendering/render_blocks.json`
- `rendering/render_templates.json`
- `rendering/render_order.json`
- `rendering/output_profiles.json`

### 21.1 Render block fields

```json
{
  "render_block_key": "KE-PPRA-IT-2022-04.render.tds",
  "version_code": "KE-PPRA-IT-2022-04",
  "section_key": "KE-PPRA-IT-2022-04.section.tds",
  "render_engine": "STD_MARKDOWN_HTML_PDF",
  "template_ref": "render_templates/tds.md.hbs",
  "required_inputs": [
    "tds.procuring_entity_name",
    "tds.tender_name",
    "tds.tender_number",
    "tds.tender_submission_deadline"
  ],
  "output_format_support": ["HTML", "PDF", "DOCX", "JSON"],
  "hash_output": true,
  "source_anchor_key": "KE-PPRA-IT-2022-04.anchor.section_ii_tds"
}
```

### 21.2 Render order

| Order | Render block |
|---:|---|
| 1 | Cover / tender identity page |
| 2 | Invitation to Tender |
| 3 | Instructions to Tenderers |
| 4 | Tender Data Sheet |
| 5 | Evaluation and Qualification Criteria |
| 6 | Tendering Forms |
| 7 | Requirements of the Information System |
| 8 | Technical Requirements |
| 9 | Implementation Schedule |
| 10 | System Inventory Tables |
| 11 | Background and Informational Materials |
| 12 | General Conditions of Contract |
| 13 | Special Conditions of Contract |
| 14 | Contract Forms |
| 15 | System-generated audit and hash appendix, if enabled |

### 21.3 Output profiles

| Output profile | Purpose |
|---|---|
| `ISSUED_TENDER_DOCUMENT` | Tender document issued to bidders |
| `BIDDER_RESPONSE_SCHEMA` | Digital submission schema for supplier portal |
| `EVALUATION_WORKBOOK_SCHEMA` | Structured evaluation checklist/scoring matrix |
| `CONTRACT_FORMATION_PACKAGE` | Post-award contract documents |
| `AUDIT_PACKAGE` | Internal trace, hashes, approvals, source anchors |

---

## 22. Workflow seed specification

Files:

- `workflow/lifecycle_bindings.json`
- `workflow/approval_bindings.json`
- `workflow/addendum_impact_rules.json`

### 22.1 Template lifecycle binding

```text
DRAFT
  → STRUCTURING
  → INTERNAL_REVIEW
  → LEGAL_PROCUREMENT_REVIEW
  → APPROVED
  → ACTIVE
  → SUPERSEDED
  → ARCHIVED
```

### 22.2 Tender STD instance lifecycle binding

```text
NOT_STARTED
  → IN_CONFIGURATION
  → VALIDATION_FAILED
  → READY_FOR_REVIEW
  → PROCUREMENT_REVIEW
  → APPROVED_FOR_TENDER_CREATION
  → BOUND_TO_TENDER
  → GENERATED
  → PUBLISHED
  → ADDENDUM_REQUIRED
  → SUPERSEDED_BY_ADDENDUM
```

### 22.3 Approval gates

| Gate | Required approvals |
|---|---|
| Import accepted | STD Administrator |
| Structuring complete | STD Administrator |
| Legal template review | Legal/Procurement Reviewer |
| Activation | Authorized Template Approver |
| Tender configuration approval | Procurement reviewer / tender approval authority |
| Publication | Tender publication authority |
| Addendum issue | Addendum approval authority |

### 22.4 Addendum impact rules

| Changed item | Addendum impact |
|---|---|
| TDS deadline/date/address | Regenerate invitation/TDS; publish addendum |
| Technical requirement | Regenerate requirement section, bidder schema, evaluation matrix if affected |
| Price schedule structure | Regenerate price forms and financial evaluation schema |
| Evaluation criteria | High-risk change; must be blocked after publication unless legally approved by addendum governance |
| SCC payment/warranty/security | Regenerate SCC and contract forms |
| Locked ITT/GCC text | Not permitted in tender instance; requires new STD version or formal authority correction |

---

## 23. NSSF ERP calibration fixture

The NSSF ERP tender is not the master STD. It is a fixture used to test whether the IT STD package can support a realistic ERP procurement.

### 23.1 Fixture folder

```text
fixtures/
  nssf_erp/
    fixture_manifest.json
    tender_configuration_values.json
    requirements_fixture.json
    evaluation_fixture.json
    price_schedule_fixture.json
    contract_fixture.json
```

### 23.2 Fixture usage policy

| Rule | Required behavior |
|---|---|
| Fixture must never be imported as an active STD | Prevents contamination of legal template |
| Fixture may be imported into a sandbox tender instance | Enables testing |
| Fixture values must be tagged `CALIBRATION_FIXTURE` | Clear separation |
| Fixture-specific deviations must be reported | Useful for compliance analysis |
| Fixture must not create new master parameters silently | Prevents overfitting |

### 23.3 Calibration checks

The fixture should be used to test whether the package supports:

1. ERP system scope.
2. National tendering.
3. Tender validity.
4. Physical submission.
5. Professional indemnity/security variant.
6. JV member limit.
7. No alternative tenders.
8. Fixed prices.
9. Mandatory preliminary requirements.
10. Technical qualification requirements.
11. Technical scoring with pass mark.
12. Detailed module requirements.
13. Compliance matrix with Yes/No/reference pages.
14. Phased implementation.
15. Data migration, training, documentation, testing, acceptance.
16. Cloud infrastructure and support requirements.
17. Payment milestones.
18. Warranty period.
19. Performance security.
20. Contract forms.

---

## 24. Database import mapping

The importer should map package modules into the STD Engine domain model as follows.

| Package file | Target domain tables / DocTypes |
|---|---|
| `family.json` | `STD Template Family` |
| `version.json` | `STD Template Version` |
| `source_document.json` | `STD Source Document` |
| `source_anchors.json` | `STD Source Anchor` |
| `sections.json` | `STD Section` |
| `clauses.json` | `STD Clause` |
| `clause_fragments.json` | `STD Clause Fragment` |
| `parameters.json` | `STD Parameter` |
| `parameter_options.json` | `STD Parameter Option` |
| `rule_catalog.json` | `STD Rule` |
| `rule_bindings.json` | `STD Rule Binding` |
| `form_catalog.json` | `STD Form Schema` |
| `form_fields.json` | `STD Form Field` |
| `evidence_requirements.json` | `STD Evidence Requirement` |
| `requirement_schema.json` | `STD Requirement Schema` / `IT Requirement Type` |
| `implementation_schedule_schema.json` | `STD Schedule Schema` |
| `system_inventory_schema.json` | `STD Inventory Schema` |
| `price_schedule_catalog.json` | `STD Price Schedule Schema` |
| `evaluation_schema.json` | `STD Evaluation Schema` |
| `contract_schema.json` | `STD Contract Schema` |
| `render_blocks.json` | `STD Render Block` |
| `lifecycle_bindings.json` | `STD Lifecycle Binding` |
| `approval_bindings.json` | `STD Approval Binding` |
| `addendum_impact_rules.json` | `STD Addendum Impact Rule` |
| `tests/*.json` | `STD Smoke Contract` |

---

## 25. Smoke tests

The seed package must include test definitions that run immediately after import.

### 25.1 Import smoke tests

| Test ID | Expected result |
|---|---|
| `IT_IMPORT_001` | Package imports into DRAFT state |
| `IT_IMPORT_002` | All sections have valid parent/version references |
| `IT_IMPORT_003` | All locked clauses have source anchors |
| `IT_IMPORT_004` | All parameters have valid group and section bindings |
| `IT_IMPORT_005` | All rules reference existing parameters/forms/sections |
| `IT_IMPORT_006` | All render blocks reference existing sections |
| `IT_IMPORT_007` | Fixture data is not imported by default |

### 25.2 Validation smoke tests

| Test ID | Expected result |
|---|---|
| `IT_VAL_001` | Missing tender name blocks readiness |
| `IT_VAL_002` | Opening before submission is blocked |
| `IT_VAL_003` | Clarification deadline after submission is blocked |
| `IT_VAL_004` | Alternative tender fields are inactive when alternatives are not permitted |
| `IT_VAL_005` | Reservation group is required if reservation applies |
| `IT_VAL_006` | Professional indemnity amount is required if PI is required |
| `IT_VAL_007` | Technical evaluation weights must sum to 100 if scored |
| `IT_VAL_008` | Background material cannot be marked as mandatory requirement |
| `IT_VAL_009` | Inventory items must map to price schedules |
| `IT_VAL_010` | Payment milestones must map to implementation milestones |

### 25.3 Rendering smoke tests

| Test ID | Expected result |
|---|---|
| `IT_RENDER_001` | Draft tender preview renders all required sections |
| `IT_RENDER_002` | Locked ITT/GCC text renders from source-controlled clauses |
| `IT_RENDER_003` | TDS parameter values render in TDS and related clauses |
| `IT_RENDER_004` | Price schedules render from structured schema |
| `IT_RENDER_005` | Technical requirements render as compliance matrix where configured |
| `IT_RENDER_006` | Output bundle hash is generated |

### 25.4 Tender binding smoke tests

| Test ID | Expected result |
|---|---|
| `IT_BIND_001` | Tender instance can bind only to ACTIVE STD version |
| `IT_BIND_002` | Tender instance stores version hash at binding time |
| `IT_BIND_003` | Published bundle is immutable |
| `IT_BIND_004` | Used STD version cannot be deleted |

### 25.5 Addendum smoke tests

| Test ID | Expected result |
|---|---|
| `IT_ADD_001` | Post-publication change request creates addendum workflow |
| `IT_ADD_002` | Technical requirement change identifies affected bidder schema and evaluation schema |
| `IT_ADD_003` | Deadline change regenerates invitation and TDS |
| `IT_ADD_004` | Locked clause change is blocked at tender instance level |
| `IT_ADD_005` | Addendum output is hashed and linked to original published bundle |

---

## 26. Package build tasks

### 26.1 Manual/legal extraction tasks

1. Extract official section hierarchy from DOC. 10.
2. Assign source anchors to all sections.
3. Extract locked ITT clauses.
4. Extract locked GCC clauses.
5. Extract TDS configurable items.
6. Extract SCC configurable items.
7. Extract tendering form inventory.
8. Extract price schedule forms.
9. Extract implementation schedule templates.
10. Extract system inventory table templates.
11. Extract contract form and appendix inventory.
12. Review all extracted items for source traceability.

### 26.2 Schema authoring tasks

1. Author parameter groups and parameters.
2. Author TDS schema.
3. Author SCC schema.
4. Author rule catalog and bindings.
5. Author form catalog and fields.
6. Author evidence requirement catalog.
7. Author IT requirement schema.
8. Author system inventory schema.
9. Author implementation schedule schema.
10. Author price schedule schema.
11. Author evaluation schema.
12. Author contract schema.
13. Author render blocks.
14. Author workflow bindings.
15. Author smoke tests.

### 26.3 Fixture tasks

1. Map NSSF ERP tender identity and TDS values into fixture configuration.
2. Map NSSF ERP mandatory requirements into evaluation fixture.
3. Map NSSF ERP scored criteria into technical evaluation fixture.
4. Map NSSF ERP technical requirements into requirements fixture.
5. Map NSSF ERP implementation phases into schedule fixture.
6. Map NSSF ERP pricing into price fixture.
7. Map NSSF ERP SCC/payment/warranty/security into contract fixture.
8. Run fixture against package and report unsupported fields.

---

## 27. Acceptance criteria for this seed package

The package is implementation-ready when all of the following are true:

1. Package imports successfully into DRAFT state.
2. Every section, clause, parameter, form, rule, render block, and schema has a stable key.
3. Every locked legal section has source traceability.
4. ITT and GCC are locked and cannot be modified through tender configuration.
5. TDS and SCC are configurable only through controlled schemas.
6. Requirements of the Information System can be authored through a structured composer.
7. Background materials cannot create requirements.
8. System inventory tables support supply/install and recurrent cost items.
9. Price schedules link to inventory and implementation schedule.
10. Evaluation schema supports responsiveness, qualification, technical evaluation, financial evaluation, and award recommendation.
11. Contract forms and appendices can be generated from tender, award, SCC, accepted price, and accepted schedule data.
12. Activation requires approval.
13. Active package is immutable.
14. Used package cannot be deleted.
15. Published tender bundle is immutable.
16. Post-publication changes trigger addendum governance.
17. Smoke tests pass.
18. NSSF ERP fixture can be loaded as a sandbox tender instance without modifying the master STD package.

---

## 28. Known exclusions from initial seed package

The initial seed package should not attempt to solve everything.

Out of scope for the first package import:

1. Full optical/textual perfection of every source clause if extraction quality is poor.
2. Automated legal interpretation of ambiguous provisions.
3. Automatic correction of non-compliant real-world tenders.
4. External integrations for KRA, PPRA debarment, Microsoft partner validation, RBA, banks, or identity systems.
5. Full contract execution management beyond generated contract artifacts, acceptance certificates, and change order schemas.
6. AI-generated technical requirements without human approval.
7. Automatic migration of legacy uploaded tender documents into fully compliant structured tenders.

These may be addressed in later modules.

---

## 29. Immediate next implementation artifact

After this specification, the next artifact should be:

# `KE-PPRA-IT-2022-04 Seed Package Skeleton`

That artifact should create the actual folder/module files with placeholder but valid JSON structures, ready for progressive filling from the official IT STD extraction.

Recommended first skeleton files:

```text
manifest.json
source/source_document.json
template/family.json
template/version.json
template/sections.json
template/mutability_map.json
configuration/parameter_groups.json
configuration/parameters.json
rules/rule_catalog.json
forms/form_catalog.json
requirements/requirement_categories.json
schedules/system_inventory_schema.json
pricing/price_schedule_catalog.json
evaluation/evaluation_schema.json
contract/contract_forms.json
rendering/render_order.json
workflow/lifecycle_bindings.json
tests/import_smoke_tests.json
```

Once the skeleton exists, the work should proceed in this order:

1. Section map and mutability map.
2. Source anchors.
3. Parameters and rules.
4. Forms and evidence.
5. Requirements, inventory, schedules, and pricing.
6. Evaluation.
7. Contract generation.
8. Rendering.
9. Smoke tests.
10. NSSF ERP fixture calibration.

---

## 30. Final implementation warning

The biggest risk is allowing the tender configuration UI to become a general document editor. That would defeat the purpose of digitizing STDs.

The correct implementation posture is strict:

- Locked legal text is managed centrally.
- Tender-specific values are entered through governed schemas.
- Requirements are authored through structured composers.
- Forms, evaluation, pricing, and contracts are generated from the active STD version.
- Published outputs are immutable.
- Changes after publication are handled through addenda.

That is the line between a document upload system and a legally defensible e-Procurement STD Engine.
