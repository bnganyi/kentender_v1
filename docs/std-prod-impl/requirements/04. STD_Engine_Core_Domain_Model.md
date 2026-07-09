# STD Engine Core Module - Strict Domain Model Tables

**Project:** KenTender e-Procurement System  
**Module:** Standard Tender Document Engine Core  
**Document type:** Strict Domain Model Tables  
**Document status:** Draft for implementation review  
**Version:** 0.1  
**Prepared date:** 2026-07-07  
**Preceding artifact:** `STD_Engine_Core_Module_PRD.md`  
**Next artifact:** STD Engine Core Governance, Roles, Permissions, and State Model  

---

## 1. Purpose

This document converts the STD Engine Core Module PRD into implementation-ready domain model tables.

The domain model is intentionally generalized. It must support multiple Standard Tender Document families, not only the Information Technology STD. The Information Technology STD is the first full production seed, while the earlier WORKS proof of concept and the NSSF ERP tender are used as validation and calibration inputs.

The domain model is written as a strict logical model that can be implemented in a relational database, Frappe/ERPNext DocTypes, Django models, Laravel models, or another enterprise application framework. Where the word **table** is used, it may also be read as **DocType** in a Frappe implementation.

---

## 2. Core Design Rules

### 2.1 Production Storage Rule

The STD Engine shall not store an official STD as one monolithic JSON document in production.

JSON packages may be used for:

1. Import.
2. Export.
3. Source control.
4. Migration.
5. Regression testing.
6. Offline review.
7. Seeding environments.

After import and approval, production behavior shall be driven by normalized database records, immutable content snapshots, hashes, lifecycle states, validation rules, and audit events.

### 2.2 Generalization Rule

The engine must not contain hard-coded logic for:

1. WORKS.
2. Information Technology.
3. Goods.
4. Consulting Services.
5. Non-consulting Services.
6. Any single PPRA document number.
7. Any single Procuring Entity tender.

STD-specific behavior shall be represented through data records: sections, clauses, parameters, rules, forms, requirement schemas, price schemas, evaluation schemas, render profiles, and contract output schemas.

### 2.3 Legal Integrity Rule

Official locked content shall be immutable once the template version becomes Active. Any change to locked content after activation requires a new template version or a formally governed correction process that creates a new immutable snapshot.

### 2.4 Tender Binding Rule

A tender must bind to one active STD template version at the point of tender configuration/publication. Once the tender is published, the generated tender bundle and its source configuration snapshot are immutable. Later changes must proceed through addendum or supersession.

### 2.5 Source Traceability Rule

Every material STD object that affects tender, bidder, evaluation, or contract output must be traceable to source authority.

At minimum, source traceability applies to:

1. Sections.
2. Clauses.
3. Parameters.
4. Rules.
5. Forms.
6. Form fields.
7. Evidence requirements.
8. Requirement schemas.
9. Price schedule schemas.
10. Evaluation schemas.
11. Contract output schemas.
12. Render blocks.

### 2.6 Approval and State-Transition Completeness Check

This domain model explicitly includes the following governance/state-transition tables before moving to implementation:

1. `std_workflow_definition`.
2. `std_workflow_state`.
3. `std_workflow_transition`.
4. `std_transition_guard`.
5. `std_approval_request`.
6. `std_approval_step`.
7. `std_approval_event`.
8. `std_template_version_transition_log`.
9. `std_tender_instance_transition_log`.

This satisfies the required check that approval and state-transition design is present before building implementation tables.

---

## 3. Naming and Type Conventions

### 3.1 Table Naming

| Prefix | Meaning |
|---|---|
| `std_` | STD Engine core table. |
| `std_src_` | Source document and source trace table. |
| `std_tpl_` | Template/version/content table. |
| `std_rule_` | Rule and validation table. |
| `std_form_` | Form schema and field table. |
| `std_req_` | Requirement schema table. |
| `std_price_` | Price schedule schema table. |
| `std_eval_` | Evaluation schema table. |
| `std_contract_` | Contract output schema table. |
| `std_render_` | Rendering table. |
| `std_tender_` | Tender-specific STD instance table. |
| `std_gen_` | Generated bundle/artifact table. |
| `std_addendum_` | Addendum impact table. |
| `std_pkg_` | Import/export package table. |
| `std_audit_` | Audit and event table. |

### 3.2 Primitive Types

| Type | Meaning |
|---|---|
| `ULID` | Globally unique sortable identifier. UUID may be used if platform lacks ULID support. |
| `Text` | Variable-length text. |
| `LongText` | Long legal text, rendered body, markdown, HTML, or extracted source text. |
| `JSON` | Structured object validated against a registered schema. |
| `Boolean` | True/false value. |
| `Integer` | Whole number. |
| `Decimal(p,s)` | Decimal number with precision and scale. |
| `Date` | Calendar date. |
| `Datetime` | Timestamp with timezone handling. |
| `Enum` | Controlled value from registered enum set. |
| `Hash` | SHA-256 hash unless otherwise stated. |
| `FileRef` | Reference to file storage object. |
| `ExternalRef` | Identifier from another KenTender module. |

### 3.3 Common Columns

Every core table must include these columns unless explicitly stated otherwise:

| Column | Type | Required | Rule |
|---|---:|---:|---|
| `id` | ULID | Yes | Primary key. |
| `created_at` | Datetime | Yes | System set. |
| `created_by` | ULID/ExternalRef | Yes | User or service account. |
| `updated_at` | Datetime | Yes | System set. |
| `updated_by` | ULID/ExternalRef | Yes | User or service account. |
| `is_deleted` | Boolean | Yes | Soft delete flag. Default false. |
| `deleted_at` | Datetime | No | Required only if soft-deleted. |
| `deleted_by` | ULID/ExternalRef | No | Required only if soft-deleted. |
| `record_version` | Integer | Yes | Optimistic concurrency counter. |
| `tenant_id` | ULID/ExternalRef | Conditional | Required if deployed multi-tenant. |

### 3.4 Hash Columns

Hash fields must be computed by canonical serialization. Whitespace normalization must be deterministic.

| Hash | Applies to | Purpose |
|---|---|---|
| `source_file_hash` | Source files | Prove source file identity. |
| `source_text_hash` | Extracted source text | Prove source text did not change. |
| `content_hash` | Clauses/content blocks | Prove legal text did not change. |
| `schema_hash` | Forms, requirements, price, evaluation, contract schemas | Prove schema did not change. |
| `rule_hash` | Rule definitions | Prove validation logic did not change. |
| `render_hash` | Render blocks/profiles | Prove rendering logic did not change. |
| `package_hash` | Import/export package | Prove package integrity. |
| `bundle_hash` | Published generated bundle | Prove generated tender/contract artifact identity. |
| `snapshot_hash` | Configuration snapshot | Prove tender-specific configuration identity. |

---

## 4. Master Reference Tables

### 4.1 `std_authority`

Represents the public authority or legal source issuing the STD.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `authority_code` | Text | Yes | Unique. Example: `PPRA_KE`. |
| `authority_name` | Text | Yes | Example: `Public Procurement Regulatory Authority`. |
| `abbreviation` | Text | No | Example: `PPRA`. |
| `country_code` | Text | Yes | ISO country code, e.g. `KE`. |
| `authority_type` | Enum | Yes | `REGULATOR`, `MINISTRY`, `AGENCY`, `OTHER`. |
| `website_url` | Text | No | Informational only. |
| `is_active` | Boolean | Yes | Default true. |

Relationships:

| Relationship | Cardinality |
|---|---|
| `std_authority` to `std_template_family` | One authority may issue many families. |
| `std_authority` to `std_src_document` | One authority may issue many source documents. |

Unique constraints:

1. `authority_code` unique.
2. `(country_code, abbreviation)` unique where abbreviation is not null.

---

### 4.2 `std_jurisdiction`

Represents the jurisdiction/legal environment where an STD applies.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `jurisdiction_code` | Text | Yes | Unique. Example: `KE_NATIONAL`. |
| `country_code` | Text | Yes | ISO code. |
| `country_name` | Text | Yes | Example: `Kenya`. |
| `legal_framework` | JSON | Yes | Array of legal references. |
| `effective_from` | Date | No | Optional. |
| `effective_to` | Date | No | Optional. |
| `is_active` | Boolean | Yes | Default true. |

Relationships:

| Relationship | Cardinality |
|---|---|
| `std_jurisdiction` to `std_template_family` | One jurisdiction may contain many template families. |

---

### 4.3 `std_procurement_category`

Controlled classification for broad STD category.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `category_code` | Text | Yes | Unique. Examples: `WORKS`, `GOODS`, `IT`, `CONSULTING_SERVICES`, `NON_CONSULTING_SERVICES`. |
| `category_name` | Text | Yes | Human-readable name. |
| `description` | Text | No | Optional. |
| `is_active` | Boolean | Yes | Default true. |

---

### 4.4 `std_enum_set`

Registers extensible enum sets used by STD packages.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `enum_set_code` | Text | Yes | Unique. Example: `MUTABILITY_TYPE`. |
| `enum_set_name` | Text | Yes | Human-readable. |
| `description` | Text | No | Optional. |
| `is_system` | Boolean | Yes | System enum sets cannot be removed. |
| `is_active` | Boolean | Yes | Default true. |

---

### 4.5 `std_enum_value`

Values within an enum set.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `enum_set_id` | ULID | Yes | FK to `std_enum_set`. |
| `value_code` | Text | Yes | Machine code. |
| `value_label` | Text | Yes | Display label. |
| `description` | Text | No | Optional. |
| `sort_order` | Integer | Yes | Deterministic display order. |
| `is_default` | Boolean | Yes | At most one default per set. |
| `is_active` | Boolean | Yes | Default true. |

Unique constraints:

1. `(enum_set_id, value_code)` unique.
2. `(enum_set_id, sort_order)` unique.

Core enum sets are defined in section 21.

---

## 5. STD Template Family and Version Tables

### 5.1 `std_template_family`

Represents a reusable STD family, such as PPRA Works Building or PPRA Procurement of Information Technology.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `family_code` | Text | Yes | Unique. Example: `KE_PPRA_IT`. |
| `family_name` | Text | Yes | Official or normalized name. |
| `short_name` | Text | No | Display name. |
| `authority_id` | ULID | Yes | FK to `std_authority`. |
| `jurisdiction_id` | ULID | Yes | FK to `std_jurisdiction`. |
| `procurement_category_id` | ULID | Yes | FK to `std_procurement_category`. |
| `description` | LongText | No | Family scope. |
| `default_language` | Text | Yes | Example: `en`. |
| `classification_json` | JSON | No | Procurement subtype, contract nature, complexity. |
| `is_active` | Boolean | Yes | Default true. |

Relationships:

| Relationship | Cardinality |
|---|---|
| `std_template_family` to `std_template_version` | One family has many versions. |
| `std_template_family` to `std_src_document` | One family may have many official source documents. |

Unique constraints:

1. `family_code` unique.

---

### 5.2 `std_template_version`

Represents a governed, versioned STD template package.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `family_id` | ULID | Yes | FK to `std_template_family`. |
| `version_code` | Text | Yes | Unique within family. Example: `2022_04`. |
| `template_code` | Text | Yes | Globally unique. Example: `KE_PPRA_IT_2022_04`. |
| `template_name` | Text | Yes | Official template title. |
| `revision_label` | Text | No | Example: `Rev April 2022`. |
| `status` | Enum | Yes | `DRAFT`, `STRUCTURING`, `INTERNAL_REVIEW`, `LEGAL_REVIEW`, `APPROVED`, `ACTIVE`, `SUSPENDED`, `SUPERSEDED`, `ARCHIVED`, `REJECTED`. |
| `source_document_id` | ULID | Yes | Primary official source document. FK to `std_src_document`. |
| `effective_from` | Date | No | Required before Active. |
| `effective_to` | Date | No | Optional until superseded. |
| `supersedes_version_id` | ULID | No | FK to prior `std_template_version`. |
| `superseded_by_version_id` | ULID | No | FK to next version. |
| `package_hash` | Hash | No | Required when imported from package or activated. |
| `content_hash` | Hash | No | Template-wide content hash. Required before Active. |
| `schema_hash` | Hash | No | Template-wide schema hash. Required before Active. |
| `rule_hash` | Hash | No | Template-wide rule hash. Required before Active. |
| `render_hash` | Hash | No | Template-wide render hash. Required before Active. |
| `activation_snapshot_hash` | Hash | No | Combined activation evidence hash. Required before Active. |
| `activation_notes` | LongText | No | Review summary. |
| `locked_at` | Datetime | No | Set when status becomes Active. |
| `locked_by` | ULID/ExternalRef | No | User who activated. |
| `is_imported` | Boolean | Yes | True if initially created from package. |
| `import_package_id` | ULID | No | FK to `std_pkg_import`. |

Unique constraints:

1. `(family_id, version_code)` unique.
2. `template_code` unique.
3. Only one `ACTIVE` version per `(family_id)` unless business policy permits parallel active variants by procurement method or jurisdiction.

Immutability constraints:

1. If `status IN ('ACTIVE','SUPERSEDED','ARCHIVED')`, hash-affecting child records are immutable.
2. If any `std_tender_instance` exists for this version outside `CANCELLED`, deletion is prohibited.
3. Transition to `ACTIVE` requires zero blocking validation findings and passed activation smoke contracts.

---

### 5.3 `std_template_version_metadata`

Stores extensible template-level metadata without polluting the primary version table.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to `std_template_version`. |
| `metadata_key` | Text | Yes | Example: `contract_pricing_type`. |
| `metadata_value` | JSON | Yes | Typed value. |
| `value_type` | Enum | Yes | `TEXT`, `NUMBER`, `BOOLEAN`, `DATE`, `JSON`, `ENUM`. |
| `is_hash_affecting` | Boolean | Yes | Default true. |
| `description` | Text | No | Optional. |

Unique constraints:

1. `(template_version_id, metadata_key)` unique.

---

## 6. Source Document and Traceability Tables

### 6.1 `std_src_document`

Registers official or calibration source documents.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `source_code` | Text | Yes | Unique. Example: `DOC_10_IT_STD_2022_04`. |
| `source_title` | Text | Yes | Official source title. |
| `source_subtitle` | Text | No | Optional. |
| `authority_id` | ULID | No | FK to `std_authority`. Required for official source. |
| `source_type` | Enum | Yes | `OFFICIAL_STD`, `CALIBRATION_TENDER`, `REFERENCE_GUIDANCE`, `IMPORT_PACKAGE`, `OTHER`. |
| `file_ref` | FileRef | Yes | Stored source file. |
| `file_name` | Text | Yes | Original file name. |
| `mime_type` | Text | Yes | Example: `application/pdf`. |
| `page_count` | Integer | No | Required where applicable. |
| `source_file_hash` | Hash | Yes | SHA-256. |
| `revision_label` | Text | No | Example: `Rev April 2022`. |
| `issued_date` | Date | No | If known. |
| `uploaded_at` | Datetime | Yes | System set. |
| `uploaded_by` | ULID/ExternalRef | Yes | User. |
| `is_authoritative` | Boolean | Yes | True for official STD source. |
| `is_active` | Boolean | Yes | Default true. |

Unique constraints:

1. `source_code` unique.
2. `source_file_hash` unique unless explicitly overridden by admin for duplicate upload detection.

---

### 6.2 `std_src_document_version`

Tracks re-uploads, OCR improvements, or extracted text versions without changing the original source record.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `source_document_id` | ULID | Yes | FK to `std_src_document`. |
| `version_no` | Integer | Yes | Starts at 1. |
| `file_ref` | FileRef | Yes | Stored file. |
| `source_file_hash` | Hash | Yes | SHA-256. |
| `extraction_method` | Enum | Yes | `NATIVE_TEXT`, `OCR`, `MANUAL`, `HYBRID`. |
| `extraction_quality` | Enum | No | `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`. |
| `notes` | LongText | No | Optional. |
| `is_current` | Boolean | Yes | One current version per document. |

Unique constraints:

1. `(source_document_id, version_no)` unique.
2. `(source_document_id, is_current=true)` unique partial index.

---

### 6.3 `std_src_location`

Represents a specific location inside a source document.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `source_document_id` | ULID | Yes | FK to `std_src_document`. |
| `source_document_version_id` | ULID | No | FK to `std_src_document_version`. |
| `page_start` | Integer | No | Page number if applicable. |
| `page_end` | Integer | No | Must be >= `page_start`. |
| `section_ref` | Text | No | Example: `Section II`, `ITT 4.1`. |
| `heading_text` | Text | No | Heading at source location. |
| `anchor_label` | Text | No | Deterministic internal anchor. |
| `line_start` | Integer | No | If line extraction exists. |
| `line_end` | Integer | No | If line extraction exists. |
| `bbox_json` | JSON | No | Optional page coordinate region. |
| `location_confidence` | Decimal(5,2) | No | 0-100. |

Validation constraints:

1. `page_end >= page_start` when both are present.
2. At least one of `page_start`, `section_ref`, `anchor_label`, or `heading_text` must be present.

---

### 6.4 `std_src_extract`

Stores extracted text or structured data from a source location.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `source_location_id` | ULID | Yes | FK to `std_src_location`. |
| `extract_type` | Enum | Yes | `TEXT`, `TABLE`, `IMAGE_TEXT`, `FORM`, `CLAUSE`, `HEADING`, `OTHER`. |
| `extracted_text` | LongText | No | Required for text-based extract. |
| `extracted_json` | JSON | No | Required for table/form extraction. |
| `source_text_hash` | Hash | Yes | Hash of normalized extraction content. |
| `extraction_confidence` | Decimal(5,2) | No | 0-100. |
| `extracted_by` | ULID/ExternalRef | No | User or service. |
| `extracted_at` | Datetime | Yes | System set. |
| `review_status` | Enum | Yes | `UNREVIEWED`, `REVIEWED`, `REJECTED`, `CORRECTED`. |
| `reviewed_by` | ULID/ExternalRef | No | Required if reviewed/rejected/corrected. |
| `reviewed_at` | Datetime | No | Required if reviewed/rejected/corrected. |

Validation constraints:

1. At least one of `extracted_text` or `extracted_json` is required.
2. `source_text_hash` must be recalculated when extraction content changes.

---

### 6.5 `std_source_trace_link`

Generic traceability link from a domain object to source material.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `target_table` | Text | Yes | Table name of traced object. |
| `target_id` | ULID | Yes | ID of traced object. |
| `source_document_id` | ULID | Yes | FK to `std_src_document`. |
| `source_location_id` | ULID | No | FK to `std_src_location`. |
| `source_extract_id` | ULID | No | FK to `std_src_extract`. |
| `trace_type` | Enum | Yes | `DIRECT_TEXT`, `PARAMETER_BASIS`, `RULE_BASIS`, `FORM_BASIS`, `SCHEMA_BASIS`, `RENDER_BASIS`, `CALIBRATION_ONLY`. |
| `trace_confidence` | Decimal(5,2) | No | 0-100. |
| `source_text_hash` | Hash | No | Copy of source extract hash at link time. |
| `notes` | LongText | No | Optional. |
| `is_required_for_activation` | Boolean | Yes | Default true for official template content. |

Unique constraints:

1. `(target_table, target_id, source_extract_id, trace_type)` unique where `source_extract_id` is not null.

Activation constraint:

1. Objects marked as source-trace-required must have at least one `std_source_trace_link` with `trace_type != CALIBRATION_ONLY` before template activation.

---

## 7. Template Content Tables

### 7.1 `std_tpl_section`

Represents the hierarchical structure of a template version.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to `std_template_version`. |
| `parent_section_id` | ULID | No | Self FK. Null for root sections. |
| `section_code` | Text | Yes | Example: `PART_1`, `SECTION_II_TDS`. |
| `source_section_ref` | Text | No | Official reference. |
| `title` | Text | Yes | Section title. |
| `description` | LongText | No | Optional. |
| `section_type` | Enum | Yes | `COVER`, `PREFACE`, `INVITATION`, `ITT`, `TDS`, `EVALUATION`, `FORMS`, `REQUIREMENTS`, `TECHNICAL_REQUIREMENTS`, `PRICE_SCHEDULE`, `GCC`, `SCC`, `CONTRACT_FORMS`, `APPENDIX`, `OTHER`. |
| `mutability_type` | Enum | Yes | See mutability enum. |
| `include_in_issued_tender` | Boolean | Yes | Whether rendered for bidders. |
| `include_in_contract` | Boolean | Yes | Whether carried to contract bundle. |
| `sort_order` | Integer | Yes | Order among siblings. |
| `depth` | Integer | Yes | Cached hierarchy depth. |
| `path_code` | Text | Yes | Deterministic hierarchy path. |
| `is_required` | Boolean | Yes | Whether section is mandatory. |
| `activation_condition_json` | JSON | No | Optional conditional inclusion. |
| `content_hash` | Hash | No | Section-level hash. |

Unique constraints:

1. `(template_version_id, section_code)` unique.
2. `(parent_section_id, sort_order)` unique.
3. `(template_version_id, path_code)` unique.

Immutability constraints:

1. `mutability_type = LOCKED` or parent template `ACTIVE` prevents structure edits.
2. Section deletion is prohibited once referenced by rendered bundle, form, rule, or tender instance.

---

### 7.2 `std_tpl_content_block`

Generic content block within a section. This avoids forcing all text into clause records.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to `std_template_version`. |
| `section_id` | ULID | Yes | FK to `std_tpl_section`. |
| `block_code` | Text | Yes | Unique within template. |
| `block_type` | Enum | Yes | `HEADING`, `PARAGRAPH`, `CLAUSE`, `TABLE`, `FORM_PLACEHOLDER`, `PARAMETER_PLACEHOLDER`, `RENDER_INCLUDE`, `NOTE`, `OTHER`. |
| `title` | Text | No | Optional. |
| `body_text` | LongText | No | For text block. |
| `body_json` | JSON | No | For table/structured block. |
| `mutability_type` | Enum | Yes | See mutability enum. |
| `sort_order` | Integer | Yes | Order within section. |
| `is_legal_content` | Boolean | Yes | True if legally material. |
| `is_rendered` | Boolean | Yes | Default true. |
| `content_hash` | Hash | Yes | Hash of normalized content. |

Unique constraints:

1. `(template_version_id, block_code)` unique.
2. `(section_id, sort_order)` unique.

Validation constraints:

1. At least one of `body_text` or `body_json` is required unless `block_type` is placeholder/include.
2. Legal content blocks require source trace.

---

### 7.3 `std_tpl_clause`

Represents a legal/procedural clause or subclause.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to `std_template_version`. |
| `section_id` | ULID | Yes | FK to `std_tpl_section`. |
| `parent_clause_id` | ULID | No | Self FK. |
| `clause_code` | Text | Yes | Example: `ITT_4_1`, `GCC_31`. |
| `source_clause_ref` | Text | No | Official reference. |
| `clause_title` | Text | No | Optional heading. |
| `clause_text` | LongText | Yes | Canonical legal/procedural text. |
| `mutability_type` | Enum | Yes | Usually `LOCKED`, `PARAMETERIZED`, or `CONTROLLED_EDIT`. |
| `sort_order` | Integer | Yes | Order within parent/section. |
| `is_required` | Boolean | Yes | Default true. |
| `is_bidder_visible` | Boolean | Yes | Default true. |
| `is_contractual` | Boolean | Yes | True if becomes contract content. |
| `activation_condition_json` | JSON | No | Conditional inclusion. |
| `content_hash` | Hash | Yes | Hash of canonical clause text and placeholders. |
| `legal_basis_note` | Text | No | Optional internal note. |

Unique constraints:

1. `(template_version_id, clause_code)` unique.
2. `(section_id, parent_clause_id, sort_order)` unique.

Validation constraints:

1. All `LOCKED` clauses require official source trace.
2. `clause_text` cannot be edited after activation.
3. If `mutability_type = PARAMETERIZED`, placeholders must be registered in `std_tpl_clause_placeholder`.

---

### 7.4 `std_tpl_clause_placeholder`

Maps parameter placeholders embedded in clauses or content blocks.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to `std_template_version`. |
| `clause_id` | ULID | No | FK to `std_tpl_clause`. Required unless content block used. |
| `content_block_id` | ULID | No | FK to `std_tpl_content_block`. Required unless clause used. |
| `placeholder_code` | Text | Yes | Example: `{{TENDER_VALIDITY_DAYS}}`. |
| `parameter_id` | ULID | Yes | FK to `std_tpl_parameter`. |
| `is_required` | Boolean | Yes | Default true. |
| `render_format` | Text | No | Optional display format. |
| `fallback_text` | Text | No | Optional. Should be avoided for mandatory legal data. |

Unique constraints:

1. `(template_version_id, placeholder_code, clause_id, content_block_id)` unique.

Validation constraints:

1. Exactly one of `clause_id` or `content_block_id` must be set.
2. Required placeholders must resolve before tender publication.

---

## 8. Parameter Model Tables

### 8.1 `std_tpl_parameter_group`

Groups parameters for UI, validation, and review.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to `std_template_version`. |
| `group_code` | Text | Yes | Example: `TDS_GENERAL`. |
| `group_name` | Text | Yes | Display name. |
| `description` | LongText | No | Optional. |
| `section_id` | ULID | No | FK to owning section. |
| `sort_order` | Integer | Yes | UI order. |
| `is_required` | Boolean | Yes | Default false. |
| `activation_condition_json` | JSON | No | Optional conditional group. |

Unique constraints:

1. `(template_version_id, group_code)` unique.
2. `(template_version_id, sort_order)` unique within UI workspace if globally ordered.

---

### 8.2 `std_tpl_parameter`

Defines a configurable value allowed by the STD.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to `std_template_version`. |
| `parameter_group_id` | ULID | No | FK to `std_tpl_parameter_group`. |
| `section_id` | ULID | No | FK to section where value appears. |
| `parameter_code` | Text | Yes | Unique within template. Example: `TENDER_VALIDITY_DAYS`. |
| `label` | Text | Yes | UI label. |
| `description` | LongText | No | Help text. |
| `parameter_type` | Enum | Yes | `TEXT`, `LONG_TEXT`, `INTEGER`, `DECIMAL`, `MONEY`, `DATE`, `DATETIME`, `BOOLEAN`, `SELECT`, `MULTI_SELECT`, `FILE`, `ENTITY_REF`, `JSON`, `TABLE`, `DURATION`, `PERCENTAGE`. |
| `data_type_detail` | JSON | No | Currency, precision, reference entity, date rule, etc. |
| `is_required` | Boolean | Yes | Whether required when active. |
| `default_value_json` | JSON | No | Default if allowed. |
| `allowed_values_json` | JSON | No | Lightweight values if no option table. |
| `validation_schema_json` | JSON | No | JSON Schema or equivalent. |
| `min_value` | Decimal(18,4) | No | Numeric minimum. |
| `max_value` | Decimal(18,4) | No | Numeric maximum. |
| `regex_pattern` | Text | No | Text validation. |
| `mutability_type` | Enum | Yes | Usually `CONFIGURABLE`. |
| `lifecycle_stage` | Enum | Yes | `TEMPLATE_ADMIN`, `TENDER_CONFIGURATION`, `BIDDER_SUBMISSION`, `EVALUATION`, `AWARD`, `CONTRACT_FORMATION`, `ADDENDUM`. |
| `render_format` | Text | No | Formatting hint. |
| `sort_order` | Integer | Yes | Order in group. |
| `source_required` | Boolean | Yes | Default true for legal/STD parameters. |
| `is_hash_affecting` | Boolean | Yes | Default true. |
| `schema_hash` | Hash | Yes | Hash of parameter definition. |

Unique constraints:

1. `(template_version_id, parameter_code)` unique.
2. `(parameter_group_id, sort_order)` unique where group exists.

Validation constraints:

1. Required legal parameters require source trace.
2. Required parameters must be resolved in tender instance before publication unless explicitly waived by rule.
3. Parameter definitions are immutable after template activation.

---

### 8.3 `std_tpl_parameter_option`

Controlled options for select/multi-select parameters.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `parameter_id` | ULID | Yes | FK to `std_tpl_parameter`. |
| `option_code` | Text | Yes | Machine value. |
| `option_label` | Text | Yes | Display label. |
| `description` | Text | No | Optional. |
| `sort_order` | Integer | Yes | Option order. |
| `is_default` | Boolean | Yes | At most one default for single select. |
| `is_active` | Boolean | Yes | Default true. |
| `activation_condition_json` | JSON | No | Optional. |

Unique constraints:

1. `(parameter_id, option_code)` unique.
2. `(parameter_id, sort_order)` unique.

---

### 8.4 `std_tpl_parameter_dependency`

Defines declarative dependencies among parameters.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to `std_template_version`. |
| `source_parameter_id` | ULID | Yes | FK to controlling parameter. |
| `target_parameter_id` | ULID | Yes | FK to affected parameter. |
| `dependency_type` | Enum | Yes | `REQUIRES`, `SHOWS`, `HIDES`, `ENABLES`, `DISABLES`, `SETS_DEFAULT`, `LIMITS_OPTIONS`, `VALIDATES`. |
| `condition_json` | JSON | Yes | Declarative condition. |
| `effect_json` | JSON | Yes | Declarative effect. |
| `severity` | Enum | Yes | `INFO`, `WARNING`, `BLOCKER`. |
| `sort_order` | Integer | Yes | Deterministic execution order. |

Unique constraints:

1. `(template_version_id, source_parameter_id, target_parameter_id, dependency_type, sort_order)` unique.

---

## 9. Rule and Validation Tables

### 9.1 `std_rule_definition`

Defines a validation, activation, calculation, or governance rule.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to `std_template_version`. |
| `rule_code` | Text | Yes | Unique within template. |
| `rule_name` | Text | Yes | Human-readable. |
| `description` | LongText | No | Explanation. |
| `rule_type` | Enum | Yes | `VALIDATION`, `ACTIVATION`, `CALCULATION`, `DERIVATION`, `VISIBILITY`, `ELIGIBILITY`, `SCORING`, `RENDERING`, `GOVERNANCE`, `SMOKE_TEST`. |
| `rule_scope` | Enum | Yes | `TEMPLATE`, `SECTION`, `CLAUSE`, `PARAMETER`, `FORM`, `FORM_FIELD`, `REQUIREMENT`, `PRICE_SCHEDULE`, `EVALUATION`, `CONTRACT`, `TENDER_INSTANCE`, `GENERATED_BUNDLE`, `ADDENDUM`. |
| `lifecycle_stage` | Enum | Yes | Stage where rule executes. |
| `severity` | Enum | Yes | `INFO`, `WARNING`, `BLOCKER`. |
| `blocking_behavior` | Enum | Yes | `NON_BLOCKING`, `BLOCKS_SAVE`, `BLOCKS_REVIEW`, `BLOCKS_APPROVAL`, `BLOCKS_ACTIVATION`, `BLOCKS_PUBLICATION`, `BLOCKS_AWARD`, `BLOCKS_CONTRACT`. |
| `expression_language` | Enum | Yes | `JSON_LOGIC`, `CEL`, `PY_EXPR_SAFE`, `SQL_SAFE`, `CUSTOM_ENGINE`, `MANUAL_CHECK`. Prefer JSON Logic or CEL for portability. |
| `expression_json` | JSON | No | Required unless `MANUAL_CHECK`. |
| `manual_check_instructions` | LongText | No | Required if `MANUAL_CHECK`. |
| `error_message_template` | Text | Yes | Message shown to user. |
| `legal_basis_note` | LongText | No | Internal explanation. |
| `is_active` | Boolean | Yes | Default true. |
| `is_hash_affecting` | Boolean | Yes | Default true. |
| `rule_hash` | Hash | Yes | Hash of rule definition. |

Unique constraints:

1. `(template_version_id, rule_code)` unique.

Validation constraints:

1. Rules that affect legal validity require source trace.
2. Active template cannot have active rules without successful parse/compile status.

---

### 9.2 `std_rule_target`

Maps rules to target objects.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `rule_id` | ULID | Yes | FK to `std_rule_definition`. |
| `target_table` | Text | Yes | Target table name. |
| `target_id` | ULID | No | Specific target. Null means all objects in table/scope. |
| `target_code` | Text | No | Optional human-readable target code. |
| `is_primary_target` | Boolean | Yes | Default false. |

Unique constraints:

1. `(rule_id, target_table, target_id)` unique where target_id exists.
2. `(rule_id, target_table, target_code)` unique where target_code exists.

---

### 9.3 `std_rule_input`

Declares expected input values for a rule.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `rule_id` | ULID | Yes | FK to `std_rule_definition`. |
| `input_code` | Text | Yes | Example: `tender_security_amount`. |
| `input_source_type` | Enum | Yes | `PARAMETER`, `CONFIG_VALUE`, `SYSTEM_VALUE`, `RELATED_RECORD`, `CONSTANT`, `QUERY`. |
| `input_source_ref` | Text | No | Parameter code, field path, query code, etc. |
| `input_data_type` | Enum | Yes | `TEXT`, `NUMBER`, `BOOLEAN`, `DATE`, `DATETIME`, `JSON`, `LIST`. |
| `is_required` | Boolean | Yes | Default true. |
| `default_value_json` | JSON | No | Optional. |

Unique constraints:

1. `(rule_id, input_code)` unique.

---

### 9.4 `std_rule_test_case`

Test case proving rule behavior.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `rule_id` | ULID | Yes | FK to `std_rule_definition`. |
| `test_case_code` | Text | Yes | Unique within rule. |
| `description` | LongText | No | Optional. |
| `input_json` | JSON | Yes | Test input. |
| `expected_result_json` | JSON | Yes | Expected pass/fail/output/finding. |
| `expected_severity` | Enum | No | Optional. |
| `is_required_for_activation` | Boolean | Yes | Default true. |
| `last_run_status` | Enum | No | `PASSED`, `FAILED`, `ERROR`, `NOT_RUN`. |
| `last_run_at` | Datetime | No | Optional. |

Unique constraints:

1. `(rule_id, test_case_code)` unique.

Activation constraint:

1. Required rule tests must pass before template activation.

---

### 9.5 `std_validation_run`

Records one validation execution over a template, tender instance, generated bundle, or addendum.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `run_code` | Text | Yes | Unique. |
| `target_table` | Text | Yes | Validated object table. |
| `target_id` | ULID | Yes | Validated object ID. |
| `validation_scope` | Enum | Yes | `TEMPLATE_IMPORT`, `TEMPLATE_ACTIVATION`, `TENDER_CONFIGURATION`, `TENDER_PUBLICATION`, `BIDDER_SCHEMA`, `EVALUATION_SCHEMA`, `CONTRACT_SCHEMA`, `ADDENDUM`, `SMOKE_TEST`. |
| `started_at` | Datetime | Yes | System set. |
| `completed_at` | Datetime | No | Set after completion. |
| `status` | Enum | Yes | `RUNNING`, `PASSED`, `PASSED_WITH_WARNINGS`, `FAILED`, `ERROR`. |
| `blocking_finding_count` | Integer | Yes | Default 0. |
| `warning_finding_count` | Integer | Yes | Default 0. |
| `info_finding_count` | Integer | Yes | Default 0. |
| `engine_version` | Text | Yes | Validation engine version. |
| `input_snapshot_hash` | Hash | No | Hash of validation input. |
| `result_hash` | Hash | No | Hash of result set. |

Unique constraints:

1. `run_code` unique.

---

### 9.6 `std_validation_finding`

Stores validation findings.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `validation_run_id` | ULID | Yes | FK to `std_validation_run`. |
| `rule_id` | ULID | No | FK to `std_rule_definition`. Null if system finding. |
| `rule_code` | Text | No | Denormalized for audit. |
| `rule_hash` | Hash | No | Rule hash at execution time. |
| `target_table` | Text | Yes | Affected table. |
| `target_id` | ULID | No | Affected record if applicable. |
| `field_path` | Text | No | JSON/field path. |
| `severity` | Enum | Yes | `INFO`, `WARNING`, `BLOCKER`. |
| `message` | LongText | Yes | User-readable finding. |
| `technical_detail_json` | JSON | No | Debug detail. |
| `resolution_status` | Enum | Yes | `OPEN`, `RESOLVED`, `WAIVED`, `ACCEPTED_RISK`, `NOT_APPLICABLE`. |
| `resolved_by` | ULID/ExternalRef | No | Required if resolved/waived. |
| `resolved_at` | Datetime | No | Required if resolved/waived. |
| `resolution_note` | LongText | No | Required for waiver/accepted risk. |

Constraints:

1. `BLOCKER` findings cannot be waived unless rule allows waiver and governance approval exists.
2. Activation/publication is blocked if open blocker findings exist.

---

## 10. Form Schema Tables

### 10.1 `std_form_schema`

Defines a form generated from or required by an STD.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to `std_template_version`. |
| `form_code` | Text | Yes | Unique within template. |
| `form_name` | Text | Yes | Display name. |
| `form_type` | Enum | Yes | `TENDERER_FORM`, `DECLARATION`, `ELIGIBILITY`, `QUALIFICATION`, `TECHNICAL_PROPOSAL`, `PRICE_SCHEDULE`, `EVIDENCE_UPLOAD`, `CONTRACT_FORM`, `ADDENDUM_FORM`, `OTHER`. |
| `respondent_actor` | Enum | Yes | `PROCURING_ENTITY`, `TENDERER`, `EVALUATOR`, `APPROVER`, `SUCCESSFUL_TENDERER`, `SYSTEM`. |
| `lifecycle_stage` | Enum | Yes | Where form is completed/used. |
| `section_id` | ULID | No | Section where form appears. |
| `description` | LongText | No | Optional. |
| `is_required` | Boolean | Yes | Default false. |
| `is_repeatable` | Boolean | Yes | Allows multiple instances. |
| `activation_condition_json` | JSON | No | Conditional inclusion. |
| `submission_rule_json` | JSON | No | Form submission constraints. |
| `schema_version` | Integer | Yes | Starts at 1. |
| `schema_hash` | Hash | Yes | Hash of form schema. |

Unique constraints:

1. `(template_version_id, form_code)` unique.

Activation constraints:

1. Required forms must have at least one section or explicit render mapping.
2. Forms that create bidder obligations require source trace.

---

### 10.2 `std_form_section`

Logical section within a form.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `form_schema_id` | ULID | Yes | FK to `std_form_schema`. |
| `parent_form_section_id` | ULID | No | Self FK. |
| `section_code` | Text | Yes | Unique within form. |
| `section_title` | Text | Yes | Display title. |
| `description` | LongText | No | Optional. |
| `sort_order` | Integer | Yes | Form order. |
| `is_repeatable` | Boolean | Yes | Default false. |
| `activation_condition_json` | JSON | No | Optional. |

Unique constraints:

1. `(form_schema_id, section_code)` unique.
2. `(form_schema_id, parent_form_section_id, sort_order)` unique.

---

### 10.3 `std_form_field`

Field inside a form schema.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `form_schema_id` | ULID | Yes | FK to `std_form_schema`. |
| `form_section_id` | ULID | No | FK to `std_form_section`. |
| `field_code` | Text | Yes | Unique within form. |
| `field_label` | Text | Yes | Display label. |
| `field_help` | LongText | No | Help text. |
| `field_type` | Enum | Yes | `TEXT`, `LONG_TEXT`, `INTEGER`, `DECIMAL`, `MONEY`, `DATE`, `DATETIME`, `BOOLEAN`, `SELECT`, `MULTI_SELECT`, `FILE`, `TABLE`, `SIGNATURE`, `DECLARATION_CHECKBOX`, `ENTITY_REF`, `JSON`. |
| `data_type_detail` | JSON | No | Currency, precision, accepted file types, etc. |
| `is_required` | Boolean | Yes | Required when form active. |
| `is_read_only` | Boolean | Yes | Default false. |
| `is_system_populated` | Boolean | Yes | Default false. |
| `default_value_json` | JSON | No | Optional. |
| `validation_schema_json` | JSON | No | JSON Schema or equivalent. |
| `min_value` | Decimal(18,4) | No | Numeric min. |
| `max_value` | Decimal(18,4) | No | Numeric max. |
| `regex_pattern` | Text | No | Text validation. |
| `sort_order` | Integer | Yes | Display order. |
| `maps_to_parameter_id` | ULID | No | FK to `std_tpl_parameter` where applicable. |
| `maps_to_external_field` | Text | No | Downstream field path. |
| `is_evaluation_visible` | Boolean | Yes | Whether evaluators can view. |
| `is_contract_carry_forward` | Boolean | Yes | Whether response carries to contract. |
| `source_required` | Boolean | Yes | Default true for STD forms. |
| `schema_hash` | Hash | Yes | Field definition hash. |

Unique constraints:

1. `(form_schema_id, field_code)` unique.
2. `(form_section_id, sort_order)` unique where form section exists.

---

### 10.4 `std_form_field_option`

Controlled option for select/multi-select form fields.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `form_field_id` | ULID | Yes | FK to `std_form_field`. |
| `option_code` | Text | Yes | Machine code. |
| `option_label` | Text | Yes | Display value. |
| `description` | Text | No | Optional. |
| `sort_order` | Integer | Yes | Option order. |
| `is_default` | Boolean | Yes | Default false. |
| `is_active` | Boolean | Yes | Default true. |

Unique constraints:

1. `(form_field_id, option_code)` unique.
2. `(form_field_id, sort_order)` unique.

---

### 10.5 `std_form_activation_condition`

Declarative condition for including a form or field.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to template. |
| `target_type` | Enum | Yes | `FORM`, `FORM_SECTION`, `FORM_FIELD`. |
| `target_id` | ULID | Yes | ID of form/section/field. |
| `condition_json` | JSON | Yes | Declarative expression. |
| `condition_description` | LongText | No | Human-readable explanation. |
| `severity_if_unresolved` | Enum | Yes | `INFO`, `WARNING`, `BLOCKER`. |
| `sort_order` | Integer | Yes | Deterministic evaluation order. |

Unique constraints:

1. `(target_type, target_id, sort_order)` unique.

---

## 11. Evidence Requirement Tables

### 11.1 `std_evidence_requirement`

Defines a document/evidence requirement arising from an STD.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to `std_template_version`. |
| `evidence_code` | Text | Yes | Unique within template. |
| `evidence_name` | Text | Yes | Display name. |
| `description` | LongText | No | Explanation. |
| `required_from_actor` | Enum | Yes | `PROCURING_ENTITY`, `TENDERER`, `SUCCESSFUL_TENDERER`, `EVALUATOR`, `SYSTEM`. |
| `lifecycle_stage` | Enum | Yes | Stage required. |
| `section_id` | ULID | No | Owning STD section. |
| `form_schema_id` | ULID | No | Related form. |
| `form_field_id` | ULID | No | Related form field. |
| `is_mandatory` | Boolean | Yes | Whether absence is blocker. |
| `accepted_file_types_json` | JSON | No | Example: PDF, PNG, DOCX. |
| `max_file_size_mb` | Integer | No | Optional. |
| `requires_original` | Boolean | Yes | True if original physical submission required. |
| `requires_validity_period` | Boolean | Yes | Example: tax certificates. |
| `validity_rule_json` | JSON | No | Expiry/date rules. |
| `verification_rule_json` | JSON | No | Manual/automated verification rules. |
| `activation_condition_json` | JSON | No | Conditional requirement. |
| `schema_hash` | Hash | Yes | Hash of evidence definition. |

Unique constraints:

1. `(template_version_id, evidence_code)` unique.

---

### 11.2 `std_evidence_verification_schema`

Defines how evidence should be reviewed or verified.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `evidence_requirement_id` | ULID | Yes | FK to `std_evidence_requirement`. |
| `verification_code` | Text | Yes | Unique within evidence requirement. |
| `verification_type` | Enum | Yes | `MANUAL_CHECK`, `DATE_VALIDITY`, `REGISTRY_CHECK`, `CHECKSUM`, `SIGNATURE_CHECK`, `API_CHECK`, `OTHER`. |
| `verification_instruction` | LongText | Yes | Instructions to reviewer/system. |
| `is_required` | Boolean | Yes | Default true. |
| `failure_severity` | Enum | Yes | `INFO`, `WARNING`, `BLOCKER`. |
| `sort_order` | Integer | Yes | Review order. |

Unique constraints:

1. `(evidence_requirement_id, verification_code)` unique.

---

## 12. Requirement Schema Tables

These tables allow each STD family to define structured procuring entity requirements, such as IT technical requirements, WORKS specifications, GOODS schedule of requirements, or consulting terms of reference.

### 12.1 `std_req_schema`

Top-level requirement schema for a template version.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to template. |
| `schema_code` | Text | Yes | Example: `IT_TECHNICAL_REQUIREMENTS`. |
| `schema_name` | Text | Yes | Display name. |
| `requirement_domain` | Enum | Yes | `IT`, `WORKS`, `GOODS`, `SERVICES`, `CONSULTING`, `GENERAL`. |
| `description` | LongText | No | Optional. |
| `owning_section_id` | ULID | No | Section where requirements appear. |
| `is_required` | Boolean | Yes | Default false. |
| `allows_custom_groups` | Boolean | Yes | Whether PE can add groups. |
| `allows_custom_items` | Boolean | Yes | Whether PE can add requirement rows. |
| `response_mode` | Enum | Yes | `NONE`, `COMPLIANCE_YES_NO`, `COMPLIANCE_WITH_REFERENCE`, `NARRATIVE`, `SCORABLE`, `MIXED`. |
| `schema_json` | JSON | No | Optional formal schema. |
| `schema_hash` | Hash | Yes | Hash of schema definition. |

Unique constraints:

1. `(template_version_id, schema_code)` unique.

---

### 12.2 `std_req_group_schema`

Defines requirement groups/categories.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `requirement_schema_id` | ULID | Yes | FK to `std_req_schema`. |
| `parent_group_id` | ULID | No | Self FK. |
| `group_code` | Text | Yes | Unique within requirement schema. |
| `group_name` | Text | Yes | Display name. |
| `description` | LongText | No | Optional. |
| `is_required` | Boolean | Yes | Default false. |
| `sort_order` | Integer | Yes | Display order. |
| `allows_items` | Boolean | Yes | Whether group may contain requirement items. |
| `activation_condition_json` | JSON | No | Optional. |

Unique constraints:

1. `(requirement_schema_id, group_code)` unique.
2. `(requirement_schema_id, parent_group_id, sort_order)` unique.

---

### 12.3 `std_req_field_definition`

Defines columns/fields in a requirement item table.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `requirement_schema_id` | ULID | Yes | FK to `std_req_schema`. |
| `field_code` | Text | Yes | Example: `requirement_description`, `compliance_type`. |
| `field_label` | Text | Yes | Display label. |
| `field_type` | Enum | Yes | Same base field types as form fields. |
| `is_required` | Boolean | Yes | Whether required for each item. |
| `is_user_editable` | Boolean | Yes | Whether PE may edit. |
| `is_bidder_visible` | Boolean | Yes | Whether appears in tender. |
| `is_bidder_response_field` | Boolean | Yes | Whether bidder fills this column. |
| `is_evaluation_field` | Boolean | Yes | Whether evaluators use it. |
| `default_value_json` | JSON | No | Optional. |
| `validation_schema_json` | JSON | No | Optional. |
| `sort_order` | Integer | Yes | Column order. |

Unique constraints:

1. `(requirement_schema_id, field_code)` unique.
2. `(requirement_schema_id, sort_order)` unique.

---

### 12.4 `std_req_item_template`

Optional predefined requirement item. For many STDs, the template defines the structure and the PE supplies actual rows.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `requirement_schema_id` | ULID | Yes | FK to `std_req_schema`. |
| `requirement_group_id` | ULID | No | FK to `std_req_group_schema`. |
| `item_code` | Text | Yes | Unique within schema. |
| `item_title` | Text | No | Optional. |
| `item_text` | LongText | Yes | Requirement text. |
| `item_values_json` | JSON | No | Values for defined fields. |
| `is_mandatory` | Boolean | Yes | Default false. |
| `sort_order` | Integer | Yes | Order within group. |
| `activation_condition_json` | JSON | No | Optional. |
| `source_required` | Boolean | Yes | Default true if official template item. |
| `content_hash` | Hash | Yes | Hash of item definition. |

Unique constraints:

1. `(requirement_schema_id, item_code)` unique.
2. `(requirement_group_id, sort_order)` unique where group exists.

---

## 13. Price Schedule Schema Tables

### 13.1 `std_price_schema`

Defines a structured price schedule model for an STD.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to template. |
| `price_schema_code` | Text | Yes | Example: `IT_SUPPLY_INSTALL_RECURRENT`. |
| `price_schema_name` | Text | Yes | Display name. |
| `description` | LongText | No | Optional. |
| `pricing_type` | Enum | Yes | `LUMP_SUM`, `UNIT_RATE`, `SCHEDULE_OF_RATES`, `BOQ`, `SUPPLY_INSTALL`, `RECURRENT_COST`, `HYBRID`. |
| `currency_policy` | Enum | Yes | `SINGLE_CURRENCY`, `MULTI_CURRENCY_ALLOWED`, `CONVERT_TO_SINGLE_CURRENCY`. |
| `default_currency_parameter_id` | ULID | No | FK to parameter. |
| `tax_policy_json` | JSON | No | VAT/tax treatment. |
| `allows_alternatives` | Boolean | Yes | Whether alternatives affect price. |
| `is_required` | Boolean | Yes | Default true. |
| `schema_hash` | Hash | Yes | Hash of price schema. |

Unique constraints:

1. `(template_version_id, price_schema_code)` unique.

---

### 13.2 `std_price_table_schema`

Defines a table within a price schedule.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `price_schema_id` | ULID | Yes | FK to `std_price_schema`. |
| `table_code` | Text | Yes | Example: `GRAND_SUMMARY`, `SUPPLY_INSTALL_SUBTABLE`. |
| `table_name` | Text | Yes | Display name. |
| `table_type` | Enum | Yes | `SUMMARY`, `DETAIL`, `SUBTOTAL`, `RECURRENT`, `TAX`, `COUNTRY_OF_ORIGIN`, `OTHER`. |
| `is_required` | Boolean | Yes | Default true. |
| `is_repeatable` | Boolean | Yes | Default false. |
| `sort_order` | Integer | Yes | Display order. |
| `activation_condition_json` | JSON | No | Optional. |
| `calculation_rule_json` | JSON | No | Table-level calculation. |

Unique constraints:

1. `(price_schema_id, table_code)` unique.
2. `(price_schema_id, sort_order)` unique.

---

### 13.3 `std_price_column_schema`

Defines columns in a price table.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `price_table_schema_id` | ULID | Yes | FK to `std_price_table_schema`. |
| `column_code` | Text | Yes | Example: `item_description`, `quantity`, `unit_price`, `line_total`. |
| `column_label` | Text | Yes | Display label. |
| `column_type` | Enum | Yes | `TEXT`, `INTEGER`, `DECIMAL`, `MONEY`, `PERCENTAGE`, `SELECT`, `CALCULATED`, `COUNTRY_CODE`, `CURRENCY`. |
| `is_required` | Boolean | Yes | Default true. |
| `is_bidder_editable` | Boolean | Yes | Whether bidder fills. |
| `is_pe_editable` | Boolean | Yes | Whether PE configures. |
| `calculation_expression_json` | JSON | No | Required if `CALCULATED`. |
| `validation_schema_json` | JSON | No | Optional. |
| `sort_order` | Integer | Yes | Column order. |

Unique constraints:

1. `(price_table_schema_id, column_code)` unique.
2. `(price_table_schema_id, sort_order)` unique.

---

### 13.4 `std_price_calculation_rule`

Defines price calculations, totals, tax treatment, and evaluation-price derivation.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `price_schema_id` | ULID | Yes | FK to `std_price_schema`. |
| `rule_code` | Text | Yes | Unique within price schema. |
| `rule_name` | Text | Yes | Display name. |
| `calculation_scope` | Enum | Yes | `LINE`, `TABLE`, `SUMMARY`, `TAX`, `EVALUATED_PRICE`, `CURRENCY_CONVERSION`. |
| `expression_json` | JSON | Yes | Declarative calculation. |
| `rounding_policy_json` | JSON | No | Optional. |
| `failure_severity` | Enum | Yes | Usually `BLOCKER`. |
| `sort_order` | Integer | Yes | Execution order. |
| `rule_hash` | Hash | Yes | Hash of calculation. |

Unique constraints:

1. `(price_schema_id, rule_code)` unique.

---

## 14. Evaluation Schema Tables

### 14.1 `std_eval_schema`

Defines evaluation process generated by the STD.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to template. |
| `evaluation_schema_code` | Text | Yes | Unique within template. |
| `evaluation_schema_name` | Text | Yes | Display name. |
| `description` | LongText | No | Optional. |
| `evaluation_method` | Enum | Yes | `LOWEST_EVALUATED_RESPONSIVE`, `QUALITY_COST`, `PASS_FAIL_THEN_PRICE`, `TECHNICAL_SCORE_THEN_PRICE`, `OTHER`. |
| `minimum_technical_score` | Decimal(6,2) | No | Required where scoring applies. |
| `allows_margin_of_preference` | Boolean | Yes | Controlled by parameter/rule. |
| `allows_reservations` | Boolean | Yes | Controlled by parameter/rule. |
| `is_required` | Boolean | Yes | Default true. |
| `schema_hash` | Hash | Yes | Hash of evaluation schema. |

Unique constraints:

1. `(template_version_id, evaluation_schema_code)` unique.

---

### 14.2 `std_eval_stage`

Evaluation stage such as preliminary, technical, financial, qualification.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `evaluation_schema_id` | ULID | Yes | FK to `std_eval_schema`. |
| `stage_code` | Text | Yes | Example: `PRELIMINARY`, `TECHNICAL`, `FINANCIAL`. |
| `stage_name` | Text | Yes | Display name. |
| `stage_type` | Enum | Yes | `RESPONSIVENESS`, `TECHNICAL_PASS_FAIL`, `TECHNICAL_SCORED`, `FINANCIAL`, `POST_QUALIFICATION`, `AWARD_RECOMMENDATION`. |
| `sort_order` | Integer | Yes | Stage order. |
| `is_gate` | Boolean | Yes | If true, failure blocks later stages. |
| `pass_rule_json` | JSON | No | Stage pass/fail rule. |
| `minimum_score` | Decimal(6,2) | No | Required for scored gate. |
| `maximum_score` | Decimal(6,2) | No | Optional. |

Unique constraints:

1. `(evaluation_schema_id, stage_code)` unique.
2. `(evaluation_schema_id, sort_order)` unique.

---

### 14.3 `std_eval_criterion`

Evaluation criterion or mandatory checklist item.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `evaluation_stage_id` | ULID | Yes | FK to `std_eval_stage`. |
| `parent_criterion_id` | ULID | No | Self FK. |
| `criterion_code` | Text | Yes | Unique within evaluation schema. |
| `criterion_name` | Text | Yes | Display name. |
| `criterion_description` | LongText | No | Full criterion text. |
| `criterion_type` | Enum | Yes | `MANDATORY_PASS_FAIL`, `SCORED`, `FORMULA`, `PRICE_COMPARISON`, `QUALIFICATION`, `DOCUMENT_CHECK`, `REQUIREMENT_CONFORMANCE`. |
| `maximum_points` | Decimal(8,2) | No | Required for scored criterion. |
| `minimum_points` | Decimal(8,2) | No | Optional. |
| `weight_percent` | Decimal(6,2) | No | Optional. |
| `is_mandatory` | Boolean | Yes | Mandatory failure may disqualify. |
| `evidence_requirement_id` | ULID | No | FK to evidence if applicable. |
| `form_field_id` | ULID | No | FK to field if criterion uses form response. |
| `requirement_schema_id` | ULID | No | FK if criterion evaluates requirements. |
| `scoring_rule_json` | JSON | No | Rule for scoring. |
| `sort_order` | Integer | Yes | Display/evaluation order. |
| `source_required` | Boolean | Yes | Default true. |
| `content_hash` | Hash | Yes | Criterion definition hash. |

Unique constraints:

1. `(evaluation_stage_id, criterion_code)` unique.
2. `(evaluation_stage_id, parent_criterion_id, sort_order)` unique.

Validation constraints:

1. Sum of maximum points for a scored stage must match stage maximum where stage maximum is set.
2. Mandatory criteria require explicit pass/fail behavior.

---

### 14.4 `std_eval_score_scale`

Optional score scale/rubric for a criterion.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `criterion_id` | ULID | Yes | FK to `std_eval_criterion`. |
| `scale_code` | Text | Yes | Example: `FULL`, `PARTIAL`, `ZERO`. |
| `scale_label` | Text | Yes | Display label. |
| `min_score` | Decimal(8,2) | Yes | Minimum score. |
| `max_score` | Decimal(8,2) | Yes | Maximum score. |
| `description` | LongText | No | Scoring guidance. |
| `sort_order` | Integer | Yes | Display order. |

Unique constraints:

1. `(criterion_id, scale_code)` unique.
2. `(criterion_id, sort_order)` unique.

---

## 15. Contract Output Schema Tables

### 15.1 `std_contract_schema`

Defines contract artifacts and downstream contract formation outputs generated from an STD.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to template. |
| `contract_schema_code` | Text | Yes | Unique within template. |
| `contract_schema_name` | Text | Yes | Display name. |
| `description` | LongText | No | Optional. |
| `is_required` | Boolean | Yes | Default true. |
| `schema_hash` | Hash | Yes | Hash of contract schema. |

Unique constraints:

1. `(template_version_id, contract_schema_code)` unique.

---

### 15.2 `std_contract_artifact_schema`

Defines a contract artifact such as letter of award, contract agreement, performance security form, appendix, change order form.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `contract_schema_id` | ULID | Yes | FK to `std_contract_schema`. |
| `artifact_code` | Text | Yes | Unique within contract schema. |
| `artifact_name` | Text | Yes | Display name. |
| `artifact_type` | Enum | Yes | `NOTICE`, `LETTER_OF_AWARD`, `CONTRACT_AGREEMENT`, `SECURITY_FORM`, `APPENDIX`, `ACCEPTANCE_CERTIFICATE`, `CHANGE_ORDER`, `DISCLOSURE_FORM`, `OTHER`. |
| `owning_section_id` | ULID | No | Section reference. |
| `is_required` | Boolean | Yes | Default false. |
| `is_generated_after_award` | Boolean | Yes | Default true. |
| `requires_successful_tenderer_input` | Boolean | Yes | Whether supplier fills post-award. |
| `requires_pe_input` | Boolean | Yes | Whether PE fills. |
| `sort_order` | Integer | Yes | Output order. |
| `activation_condition_json` | JSON | No | Optional. |
| `schema_hash` | Hash | Yes | Hash of artifact schema. |

Unique constraints:

1. `(contract_schema_id, artifact_code)` unique.
2. `(contract_schema_id, sort_order)` unique.

---

### 15.3 `std_contract_carry_forward_mapping`

Maps tender, bidder, evaluation, award, or configuration data into contract artifacts.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `contract_artifact_schema_id` | ULID | Yes | FK to artifact schema. |
| `mapping_code` | Text | Yes | Unique within artifact. |
| `source_type` | Enum | Yes | `TENDER_PARAMETER`, `TENDER_CONFIG`, `BIDDER_RESPONSE`, `EVALUATION_RESULT`, `AWARD_RECORD`, `SYSTEM_VALUE`, `MANUAL_CONTRACT_INPUT`. |
| `source_ref` | Text | Yes | Parameter code, field path, external path. |
| `target_placeholder` | Text | Yes | Render placeholder or output field. |
| `is_required` | Boolean | Yes | Required to generate artifact. |
| `transform_rule_json` | JSON | No | Optional transformation. |
| `fallback_behavior` | Enum | Yes | `BLOCK`, `WARN`, `BLANK`, `DEFAULT`, `MANUAL_INPUT`. |
| `sort_order` | Integer | Yes | Deterministic order. |

Unique constraints:

1. `(contract_artifact_schema_id, mapping_code)` unique.
2. `(contract_artifact_schema_id, target_placeholder)` unique.

---

## 16. Rendering Tables

### 16.1 `std_render_profile`

Defines a rendering profile for a template version.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to template. |
| `render_profile_code` | Text | Yes | Unique within template. |
| `render_profile_name` | Text | Yes | Display name. |
| `output_type` | Enum | Yes | `TENDER_DOCUMENT`, `BIDDER_FORMS`, `EVALUATION_PACK`, `CONTRACT_PACK`, `ADDENDUM`, `PREVIEW`, `AUDIT_REPORT`. |
| `format` | Enum | Yes | `HTML`, `PDF`, `DOCX`, `ODT`, `JSON`, `ZIP`. |
| `is_default` | Boolean | Yes | One default per output type if required. |
| `style_profile_json` | JSON | No | Fonts, headings, page numbering, etc. |
| `renderer_engine` | Text | Yes | Example: `jinja_pdf_v1`. |
| `render_hash` | Hash | Yes | Hash of profile. |

Unique constraints:

1. `(template_version_id, render_profile_code)` unique.
2. `(template_version_id, output_type, is_default=true)` unique partial index.

---

### 16.2 `std_render_block`

Defines an ordered block used to render outputs.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `render_profile_id` | ULID | Yes | FK to `std_render_profile`. |
| `block_code` | Text | Yes | Unique within profile. |
| `block_name` | Text | No | Optional. |
| `block_type` | Enum | Yes | `SECTION`, `CLAUSE`, `FORM`, `REQUIREMENT_TABLE`, `PRICE_TABLE`, `EVALUATION_TABLE`, `CONTRACT_ARTIFACT`, `STATIC_TEXT`, `CUSTOM_TEMPLATE`, `INCLUDE`. |
| `source_table` | Text | No | Source object table. |
| `source_id` | ULID | No | Source object. |
| `template_text` | LongText | No | Rendering template. |
| `template_json` | JSON | No | Structured render definition. |
| `sort_order` | Integer | Yes | Render order. |
| `activation_condition_json` | JSON | No | Optional. |
| `is_required` | Boolean | Yes | Default true. |
| `render_hash` | Hash | Yes | Hash of render block. |

Unique constraints:

1. `(render_profile_id, block_code)` unique.
2. `(render_profile_id, sort_order)` unique.

Validation constraints:

1. Required render blocks must resolve before activation.
2. Render profile must pass deterministic rendering smoke contract.

---

### 16.3 `std_render_placeholder`

Defines placeholders used by render blocks.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `render_block_id` | ULID | Yes | FK to `std_render_block`. |
| `placeholder_code` | Text | Yes | Example: `{{procuring_entity_name}}`. |
| `source_type` | Enum | Yes | `PARAMETER`, `CONFIG_VALUE`, `FORM_VALUE`, `SYSTEM_VALUE`, `QUERY`, `CONTRACT_MAPPING`. |
| `source_ref` | Text | Yes | Parameter code/path/query. |
| `is_required` | Boolean | Yes | Default true. |
| `format_rule_json` | JSON | No | Optional. |
| `fallback_behavior` | Enum | Yes | `BLOCK`, `WARN`, `BLANK`, `DEFAULT`. |

Unique constraints:

1. `(render_block_id, placeholder_code)` unique.

---

## 17. Governance and Workflow Tables

### 17.1 `std_workflow_definition`

Defines workflow for an object type.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `workflow_code` | Text | Yes | Unique. Example: `STD_TEMPLATE_VERSION_WORKFLOW`. |
| `workflow_name` | Text | Yes | Display name. |
| `target_table` | Text | Yes | Example: `std_template_version`. |
| `description` | LongText | No | Optional. |
| `is_active` | Boolean | Yes | Default true. |
| `version_no` | Integer | Yes | Workflow version. |

Unique constraints:

1. `(workflow_code, version_no)` unique.
2. One active workflow per `target_table` unless explicitly allowed.

---

### 17.2 `std_workflow_state`

State in a workflow.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `workflow_definition_id` | ULID | Yes | FK to `std_workflow_definition`. |
| `state_code` | Text | Yes | Example: `DRAFT`, `ACTIVE`. |
| `state_label` | Text | Yes | Display label. |
| `state_type` | Enum | Yes | `INITIAL`, `INTERMEDIATE`, `APPROVED`, `ACTIVE`, `TERMINAL`, `REJECTED`, `ARCHIVED`. |
| `is_editable` | Boolean | Yes | Whether normal edits allowed. |
| `is_hash_locked` | Boolean | Yes | Whether hash-affecting records locked. |
| `is_terminal` | Boolean | Yes | Whether no outgoing transitions. |
| `sort_order` | Integer | Yes | Display/order. |

Unique constraints:

1. `(workflow_definition_id, state_code)` unique.
2. `(workflow_definition_id, sort_order)` unique.

---

### 17.3 `std_workflow_transition`

Allowed transition between states.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `workflow_definition_id` | ULID | Yes | FK to workflow. |
| `transition_code` | Text | Yes | Unique within workflow. |
| `transition_label` | Text | Yes | Button/action label. |
| `from_state_code` | Text | Yes | Source state. |
| `to_state_code` | Text | Yes | Target state. |
| `requires_approval` | Boolean | Yes | Default false. |
| `required_role_code` | Text | No | Role required to initiate. |
| `requires_validation` | Boolean | Yes | Default true for governed transitions. |
| `validation_scope` | Enum | No | Scope to execute. |
| `creates_immutable_snapshot` | Boolean | Yes | Whether transition snapshots object. |
| `is_active` | Boolean | Yes | Default true. |
| `sort_order` | Integer | Yes | Display order. |

Unique constraints:

1. `(workflow_definition_id, transition_code)` unique.
2. `(workflow_definition_id, from_state_code, to_state_code)` unique unless multiple actions intentionally exist.

---

### 17.4 `std_transition_guard`

Guard condition for a transition.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `workflow_transition_id` | ULID | Yes | FK to `std_workflow_transition`. |
| `guard_code` | Text | Yes | Unique within transition. |
| `guard_name` | Text | Yes | Display name. |
| `guard_type` | Enum | Yes | `VALIDATION_RESULT`, `ROLE`, `APPROVAL`, `HASH_PRESENT`, `SOURCE_TRACE`, `NO_USAGE`, `NO_OPEN_FINDINGS`, `CUSTOM_RULE`. |
| `condition_json` | JSON | No | Declarative condition. |
| `failure_message` | Text | Yes | Message if guard fails. |
| `severity` | Enum | Yes | Usually `BLOCKER`. |
| `sort_order` | Integer | Yes | Evaluation order. |

Unique constraints:

1. `(workflow_transition_id, guard_code)` unique.

---

### 17.5 `std_approval_request`

Approval request for template, tender instance, addendum, or other governed object.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `request_code` | Text | Yes | Unique. |
| `target_table` | Text | Yes | Object requiring approval. |
| `target_id` | ULID | Yes | Object ID. |
| `workflow_transition_id` | ULID | No | Transition being approved. |
| `requested_transition_code` | Text | No | Denormalized transition. |
| `requested_by` | ULID/ExternalRef | Yes | User. |
| `requested_at` | Datetime | Yes | System set. |
| `status` | Enum | Yes | `PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`, `EXPIRED`. |
| `request_note` | LongText | No | Optional. |
| `snapshot_hash` | Hash | No | Hash of object at request time. |
| `completed_at` | Datetime | No | Set when terminal. |

Unique constraints:

1. `request_code` unique.
2. Only one pending approval request per `(target_table, target_id, requested_transition_code)`.

---

### 17.6 `std_approval_step`

Defines required approval step within a request.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `approval_request_id` | ULID | Yes | FK to `std_approval_request`. |
| `step_no` | Integer | Yes | Sequence. |
| `step_name` | Text | Yes | Display name. |
| `required_role_code` | Text | Yes | Role required. |
| `assigned_to` | ULID/ExternalRef | No | Specific approver if assigned. |
| `status` | Enum | Yes | `PENDING`, `APPROVED`, `REJECTED`, `SKIPPED`, `CANCELLED`. |
| `is_required` | Boolean | Yes | Default true. |
| `approved_by` | ULID/ExternalRef | No | Set when approved/rejected. |
| `approved_at` | Datetime | No | Set when approved/rejected. |
| `decision_note` | LongText | No | Required for rejection. |

Unique constraints:

1. `(approval_request_id, step_no)` unique.

---

### 17.7 `std_approval_event`

Immutable event log for approval actions.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `approval_request_id` | ULID | Yes | FK to approval request. |
| `approval_step_id` | ULID | No | FK to approval step. |
| `event_type` | Enum | Yes | `REQUESTED`, `ASSIGNED`, `APPROVED`, `REJECTED`, `COMMENTED`, `CANCELLED`, `EXPIRED`, `TRANSITION_APPLIED`. |
| `actor_id` | ULID/ExternalRef | Yes | User/service. |
| `event_at` | Datetime | Yes | System set. |
| `event_note` | LongText | No | Optional. |
| `event_payload_json` | JSON | No | Snapshot/detail. |
| `event_hash` | Hash | Yes | Hash of immutable event. |

Insert-only table:

1. Records must not be updated or deleted except by database-level repair under super-admin break-glass procedure.

---

## 18. Tender Binding and Configuration Tables

### 18.1 `std_tender_instance`

Binds a tender to a specific STD template version.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `tender_id` | ExternalRef | Yes | FK/reference to Tender Management module. |
| `template_version_id` | ULID | Yes | FK to active template version. |
| `instance_code` | Text | Yes | Unique. |
| `status` | Enum | Yes | `NOT_STARTED`, `IN_CONFIGURATION`, `VALIDATION_FAILED`, `READY_FOR_REVIEW`, `PROCUREMENT_REVIEW`, `APPROVED_FOR_TENDER_CREATION`, `BOUND_TO_TENDER`, `PUBLISHED`, `ADDENDUM_REQUIRED`, `SUPERSEDED_BY_ADDENDUM`, `CANCELLED`, `ARCHIVED`. |
| `configured_by` | ULID/ExternalRef | No | Primary configuring officer. |
| `configuration_started_at` | Datetime | No | Set when started. |
| `approved_at` | Datetime | No | Set when approved for tender creation. |
| `approved_by` | ULID/ExternalRef | No | User. |
| `published_at` | Datetime | No | Set when tender bundle published. |
| `published_by` | ULID/ExternalRef | No | User. |
| `config_snapshot_hash` | Hash | No | Required before publication. |
| `active_generated_bundle_id` | ULID | No | FK to `std_gen_bundle`. |
| `source_template_hash` | Hash | Yes | Template activation hash at binding time. |

Unique constraints:

1. `instance_code` unique.
2. `(tender_id, template_version_id)` unique unless tender intentionally has multiple lots/packages with separate STD instances.

Constraints:

1. `template_version_id` must reference an `ACTIVE` template when instance is created.
2. Published instance cannot change configuration values directly.
3. Cancellation after publication requires governed cancellation/addendum process.

---

### 18.2 `std_tender_config_value`

Stores tender-specific configured values for STD parameters.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `tender_instance_id` | ULID | Yes | FK to `std_tender_instance`. |
| `parameter_id` | ULID | Yes | FK to `std_tpl_parameter`. |
| `parameter_code` | Text | Yes | Denormalized for audit. |
| `value_json` | JSON | Yes | Typed value. |
| `display_value` | LongText | No | Human-readable normalized display. |
| `value_hash` | Hash | Yes | Hash of canonical value. |
| `source_type` | Enum | Yes | `USER_INPUT`, `SYSTEM_DEFAULT`, `DERIVED`, `IMPORT`, `ADDENDUM`, `EXTERNAL_MODULE`. |
| `set_by` | ULID/ExternalRef | Yes | User/service. |
| `set_at` | Datetime | Yes | System set. |
| `is_current` | Boolean | Yes | Allows history of changes. |
| `superseded_by_value_id` | ULID | No | Self FK for history. |
| `validation_status` | Enum | Yes | `UNVALIDATED`, `VALID`, `WARNING`, `INVALID`. |

Unique constraints:

1. `(tender_instance_id, parameter_id, is_current=true)` unique partial index.

Constraints:

1. Cannot create/update current config value when instance status is `PUBLISHED` unless through addendum workflow.
2. Value must conform to parameter type and schema.

---

### 18.3 `std_tender_requirement_item`

Tender-specific requirement row created under a requirement schema.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `tender_instance_id` | ULID | Yes | FK to tender instance. |
| `requirement_schema_id` | ULID | Yes | FK to requirement schema. |
| `requirement_group_id` | ULID | No | FK to requirement group. |
| `item_code` | Text | Yes | Unique within tender requirement schema. |
| `item_title` | Text | No | Optional. |
| `item_text` | LongText | Yes | Requirement text. |
| `item_values_json` | JSON | No | Values according to schema fields. |
| `is_mandatory` | Boolean | Yes | Whether bidder must comply. |
| `sort_order` | Integer | Yes | Display order. |
| `source_type` | Enum | Yes | `TEMPLATE_SEEDED`, `PE_AUTHORED`, `IMPORT`, `ADDENDUM`. |
| `item_hash` | Hash | Yes | Hash of item. |
| `is_current` | Boolean | Yes | Current record flag. |

Unique constraints:

1. `(tender_instance_id, requirement_schema_id, item_code, is_current=true)` unique partial index.
2. `(tender_instance_id, requirement_group_id, sort_order, is_current=true)` unique partial index.

---

### 18.4 `std_tender_price_line_template`

Tender-specific price lines preconfigured by the procuring entity for bidder pricing.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `tender_instance_id` | ULID | Yes | FK to tender instance. |
| `price_table_schema_id` | ULID | Yes | FK to price table schema. |
| `line_code` | Text | Yes | Unique within tender price table. |
| `line_description` | LongText | Yes | Item/service/cost description. |
| `quantity` | Decimal(18,4) | No | Required where quantity-controlled. |
| `unit_of_measure` | Text | No | Optional. |
| `line_values_json` | JSON | No | Additional table-specific values. |
| `is_bidder_editable` | Boolean | Yes | Whether bidder can edit description/qty or only price. |
| `sort_order` | Integer | Yes | Display order. |
| `line_hash` | Hash | Yes | Hash of line template. |
| `is_current` | Boolean | Yes | Current record flag. |

Unique constraints:

1. `(tender_instance_id, price_table_schema_id, line_code, is_current=true)` unique partial index.
2. `(tender_instance_id, price_table_schema_id, sort_order, is_current=true)` unique partial index.

---

### 18.5 `std_tender_instance_transition_log`

Transition log for tender STD instances.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `tender_instance_id` | ULID | Yes | FK to `std_tender_instance`. |
| `from_status` | Enum | No | Null on creation. |
| `to_status` | Enum | Yes | New status. |
| `transition_code` | Text | Yes | Workflow transition. |
| `transitioned_by` | ULID/ExternalRef | Yes | User/service. |
| `transitioned_at` | Datetime | Yes | System set. |
| `approval_request_id` | ULID | No | FK if approval required. |
| `validation_run_id` | ULID | No | FK if validation executed. |
| `snapshot_hash` | Hash | No | Object snapshot at transition. |
| `transition_note` | LongText | No | Optional. |

Insert-only table.

---

### 18.6 `std_template_version_transition_log`

Transition log for template versions.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `template_version_id` | ULID | Yes | FK to template version. |
| `from_status` | Enum | No | Null on creation. |
| `to_status` | Enum | Yes | New status. |
| `transition_code` | Text | Yes | Workflow transition. |
| `transitioned_by` | ULID/ExternalRef | Yes | User/service. |
| `transitioned_at` | Datetime | Yes | System set. |
| `approval_request_id` | ULID | No | FK if approval required. |
| `validation_run_id` | ULID | No | FK if validation executed. |
| `snapshot_hash` | Hash | No | Object snapshot at transition. |
| `transition_note` | LongText | No | Optional. |

Insert-only table.

---

## 19. Generated Bundle and Publication Tables

### 19.1 `std_gen_bundle`

Represents an immutable generated package, such as published tender document bundle, bidder form pack, evaluation pack, contract pack, or addendum.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `bundle_code` | Text | Yes | Unique. |
| `tender_instance_id` | ULID | No | FK to tender instance. Required for tender-related bundles. |
| `template_version_id` | ULID | Yes | FK to template. |
| `bundle_type` | Enum | Yes | `TENDER_DOCUMENT`, `BIDDER_FORM_PACK`, `EVALUATION_PACK`, `CONTRACT_PACK`, `ADDENDUM_PACK`, `PREVIEW`, `AUDIT_EXPORT`. |
| `bundle_status` | Enum | Yes | `DRAFT`, `GENERATED`, `PUBLISHED`, `SUPERSEDED`, `CANCELLED`, `ARCHIVED`. |
| `render_profile_id` | ULID | No | FK to render profile. |
| `config_snapshot_hash` | Hash | No | Required for tender-specific bundles. |
| `template_activation_snapshot_hash` | Hash | Yes | Hash of template at generation. |
| `generated_at` | Datetime | Yes | System set. |
| `generated_by` | ULID/ExternalRef | Yes | User/service. |
| `published_at` | Datetime | No | Required if published. |
| `published_by` | ULID/ExternalRef | No | Required if published. |
| `bundle_hash` | Hash | Yes | Combined artifact hash. |
| `file_ref` | FileRef | No | ZIP/PDF/document package. |
| `is_immutable` | Boolean | Yes | True once published. |

Unique constraints:

1. `bundle_code` unique.
2. Only one active published `TENDER_DOCUMENT` bundle per tender instance unless superseded by addendum.

---

### 19.2 `std_gen_artifact`

Individual artifact within a generated bundle.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `bundle_id` | ULID | Yes | FK to `std_gen_bundle`. |
| `artifact_code` | Text | Yes | Unique within bundle. |
| `artifact_name` | Text | Yes | Display name. |
| `artifact_type` | Enum | Yes | `PDF`, `DOCX`, `HTML`, `JSON_SCHEMA`, `FORM_SCHEMA`, `EVALUATION_SCHEMA`, `PRICE_SCHEMA`, `CONTRACT_FORM`, `ZIP_ENTRY`, `OTHER`. |
| `file_ref` | FileRef | No | File if physical artifact. |
| `content_text` | LongText | No | Text/HTML/JSON if stored inline. |
| `content_json` | JSON | No | Structured artifact. |
| `mime_type` | Text | No | Required for file or inline content. |
| `sort_order` | Integer | Yes | Bundle order. |
| `artifact_hash` | Hash | Yes | Hash of artifact content. |

Unique constraints:

1. `(bundle_id, artifact_code)` unique.
2. `(bundle_id, sort_order)` unique.

---

### 19.3 `std_gen_section_snapshot`

Snapshot of rendered/issued section content used for audit and diffing.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `bundle_id` | ULID | Yes | FK to bundle. |
| `section_id` | ULID | Yes | FK to `std_tpl_section`. |
| `section_code` | Text | Yes | Denormalized. |
| `rendered_content` | LongText | Yes | Canonical rendered content. |
| `source_hashes_json` | JSON | No | Source/clause/parameter hashes used. |
| `rendered_hash` | Hash | Yes | Hash of rendered section. |
| `sort_order` | Integer | Yes | Bundle order. |

Unique constraints:

1. `(bundle_id, section_id)` unique.
2. `(bundle_id, sort_order)` unique.

---

## 20. Addendum and Supersession Tables

### 20.1 `std_addendum_record`

Represents an addendum process affecting an already published tender STD instance.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `addendum_code` | Text | Yes | Unique. |
| `tender_instance_id` | ULID | Yes | FK to tender instance. |
| `previous_bundle_id` | ULID | Yes | FK to prior published bundle. |
| `new_bundle_id` | ULID | No | FK to addendum/superseding bundle after generation. |
| `status` | Enum | Yes | `DRAFT`, `IMPACT_ANALYSIS`, `UNDER_REVIEW`, `APPROVED`, `PUBLISHED`, `REJECTED`, `CANCELLED`. |
| `reason` | LongText | Yes | Required. |
| `requested_by` | ULID/ExternalRef | Yes | User. |
| `requested_at` | Datetime | Yes | System set. |
| `approved_by` | ULID/ExternalRef | No | Required if approved. |
| `approved_at` | Datetime | No | Required if approved. |
| `published_by` | ULID/ExternalRef | No | Required if published. |
| `published_at` | Datetime | No | Required if published. |
| `impact_summary` | LongText | No | Summary of affected objects. |
| `impact_hash` | Hash | No | Hash of impact records. |

Unique constraints:

1. `addendum_code` unique.
2. Only one non-terminal addendum per tender instance unless explicitly allowed.

---

### 20.2 `std_addendum_impact`

Records affected objects from an addendum.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `addendum_id` | ULID | Yes | FK to `std_addendum_record`. |
| `impact_code` | Text | Yes | Unique within addendum. |
| `affected_table` | Text | Yes | Table affected. |
| `affected_id` | ULID | No | Specific record if known. |
| `affected_code` | Text | No | Denormalized code. |
| `impact_type` | Enum | Yes | `PARAMETER_CHANGE`, `REQUIREMENT_CHANGE`, `PRICE_CHANGE`, `FORM_CHANGE`, `DATE_CHANGE`, `EVALUATION_CHANGE`, `CONTRACT_CHANGE`, `RENDER_ONLY`, `OTHER`. |
| `change_summary` | LongText | Yes | Human-readable change. |
| `before_json` | JSON | No | Before snapshot. |
| `after_json` | JSON | No | After snapshot. |
| `requires_bidder_notification` | Boolean | Yes | Default true. |
| `requires_deadline_extension_check` | Boolean | Yes | Default false. |
| `severity` | Enum | Yes | `INFO`, `WARNING`, `MATERIAL`, `CRITICAL`. |
| `sort_order` | Integer | Yes | Report order. |
| `impact_hash` | Hash | Yes | Hash of impact item. |

Unique constraints:

1. `(addendum_id, impact_code)` unique.

---

### 20.3 `std_addendum_delta`

Stores machine-readable diff between previous and new bundles/configuration.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `addendum_id` | ULID | Yes | FK to addendum. |
| `delta_scope` | Enum | Yes | `CONFIG`, `RENDERED_DOCUMENT`, `BIDDER_SCHEMA`, `EVALUATION_SCHEMA`, `CONTRACT_SCHEMA`, `PRICE_SCHEMA`, `REQUIREMENTS`. |
| `before_hash` | Hash | Yes | Hash before change. |
| `after_hash` | Hash | Yes | Hash after change. |
| `delta_json` | JSON | Yes | Machine diff. |
| `delta_summary` | LongText | No | Human-readable summary. |

Unique constraints:

1. `(addendum_id, delta_scope)` unique.

---

## 21. Import, Export, and Package Tables

### 21.1 `std_pkg_import`

Represents an import package execution.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `import_code` | Text | Yes | Unique. |
| `package_file_ref` | FileRef | Yes | Uploaded package. |
| `package_file_name` | Text | Yes | Original name. |
| `package_hash` | Hash | Yes | SHA-256. |
| `package_format` | Enum | Yes | `JSON`, `JSON5`, `ZIP`, `YAML`, `OTHER`. |
| `import_status` | Enum | Yes | `UPLOADED`, `PARSING`, `VALIDATING`, `STAGED`, `IMPORTED`, `FAILED`, `CANCELLED`. |
| `target_template_version_id` | ULID | No | Created/updated version. |
| `imported_by` | ULID/ExternalRef | Yes | User. |
| `imported_at` | Datetime | Yes | System set. |
| `validation_run_id` | ULID | No | FK to validation run. |
| `notes` | LongText | No | Optional. |

Unique constraints:

1. `import_code` unique.
2. `package_hash` unique unless duplicate import explicitly allowed.

---

### 21.2 `std_pkg_import_item`

Staged object inside an import package.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `import_id` | ULID | Yes | FK to `std_pkg_import`. |
| `item_path` | Text | Yes | Package path/key. |
| `target_table` | Text | Yes | Table to create/update. |
| `target_code` | Text | No | Business code. |
| `operation` | Enum | Yes | `CREATE`, `UPDATE`, `DELETE`, `UPSERT`, `SKIP`. |
| `item_status` | Enum | Yes | `STAGED`, `VALID`, `WARNING`, `INVALID`, `IMPORTED`, `SKIPPED`, `FAILED`. |
| `source_json` | JSON | Yes | Raw package item. |
| `normalized_json` | JSON | No | Normalized form. |
| `result_id` | ULID | No | ID created/updated. |
| `item_hash` | Hash | Yes | Hash of normalized item. |

Unique constraints:

1. `(import_id, item_path)` unique.

---

### 21.3 `std_pkg_export`

Export operation for a template, tender instance, generated bundle, or audit package.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `export_code` | Text | Yes | Unique. |
| `export_type` | Enum | Yes | `TEMPLATE_PACKAGE`, `TENDER_INSTANCE_PACKAGE`, `GENERATED_BUNDLE`, `AUDIT_PACKAGE`, `SMOKE_TEST_PACKAGE`. |
| `target_table` | Text | Yes | Export target. |
| `target_id` | ULID | Yes | Export target ID. |
| `export_format` | Enum | Yes | `JSON`, `ZIP`, `YAML`, `PDF`, `DOCX`. |
| `file_ref` | FileRef | No | Exported file. |
| `export_hash` | Hash | Yes | Hash of export. |
| `exported_by` | ULID/ExternalRef | Yes | User/service. |
| `exported_at` | Datetime | Yes | System set. |
| `notes` | LongText | No | Optional. |

Unique constraints:

1. `export_code` unique.

---

## 22. Smoke Contract Tables

### 22.1 `std_smoke_contract`

Defines a repeatable smoke contract for templates or tender instances.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `contract_code` | Text | Yes | Unique. |
| `contract_name` | Text | Yes | Display name. |
| `description` | LongText | No | Optional. |
| `target_scope` | Enum | Yes | `TEMPLATE_VERSION`, `TENDER_INSTANCE`, `GENERATED_BUNDLE`, `ADDENDUM`, `IMPORT_PACKAGE`. |
| `is_required_for_activation` | Boolean | Yes | Default false. |
| `is_required_for_publication` | Boolean | Yes | Default false. |
| `is_active` | Boolean | Yes | Default true. |
| `sort_order` | Integer | Yes | Execution order. |

Unique constraints:

1. `contract_code` unique.

---

### 22.2 `std_smoke_test_case`

Specific test case under a smoke contract.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `smoke_contract_id` | ULID | Yes | FK to `std_smoke_contract`. |
| `test_case_code` | Text | Yes | Unique within contract. |
| `test_case_name` | Text | Yes | Display name. |
| `test_type` | Enum | Yes | `VALIDATION`, `RENDER`, `HASH`, `IMMUTABILITY`, `SOURCE_TRACE`, `SCHEMA_ALIGNMENT`, `RULE_EXECUTION`, `ADDENDUM_DIFF`. |
| `input_json` | JSON | No | Test input. |
| `expected_json` | JSON | No | Expected output. |
| `execution_rule_json` | JSON | Yes | Declarative execution instruction. |
| `is_required` | Boolean | Yes | Default true. |
| `sort_order` | Integer | Yes | Execution order. |

Unique constraints:

1. `(smoke_contract_id, test_case_code)` unique.
2. `(smoke_contract_id, sort_order)` unique.

---

### 22.3 `std_smoke_run`

Execution of smoke contracts.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `run_code` | Text | Yes | Unique. |
| `target_table` | Text | Yes | Tested object table. |
| `target_id` | ULID | Yes | Tested object. |
| `started_at` | Datetime | Yes | System set. |
| `completed_at` | Datetime | No | Set at completion. |
| `status` | Enum | Yes | `RUNNING`, `PASSED`, `FAILED`, `ERROR`. |
| `required_passed` | Boolean | Yes | True only when required tests pass. |
| `run_hash` | Hash | No | Result hash. |
| `executed_by` | ULID/ExternalRef | Yes | User/service. |

Unique constraints:

1. `run_code` unique.

---

### 22.4 `std_smoke_run_result`

Individual result in a smoke run.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `smoke_run_id` | ULID | Yes | FK to `std_smoke_run`. |
| `smoke_test_case_id` | ULID | Yes | FK to test case. |
| `status` | Enum | Yes | `PASSED`, `FAILED`, `ERROR`, `SKIPPED`. |
| `message` | LongText | No | Result message. |
| `actual_json` | JSON | No | Actual output. |
| `expected_json` | JSON | No | Expected output copy. |
| `result_hash` | Hash | Yes | Hash of result. |

Unique constraints:

1. `(smoke_run_id, smoke_test_case_id)` unique.

---

## 23. Audit and Event Tables

### 23.1 `std_audit_event`

Unified immutable audit event log for STD Engine activity.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `event_code` | Text | Yes | Unique. |
| `event_type` | Enum | Yes | Examples: `SOURCE_UPLOADED`, `TEMPLATE_IMPORTED`, `TEMPLATE_ACTIVATED`, `TENDER_BOUND`, `CONFIG_VALUE_CHANGED`, `BUNDLE_PUBLISHED`, `ADDENDUM_PUBLISHED`. |
| `target_table` | Text | Yes | Main affected table. |
| `target_id` | ULID | Yes | Main affected record. |
| `actor_id` | ULID/ExternalRef | Yes | User/service. |
| `actor_role_code` | Text | No | Role at event time. |
| `event_at` | Datetime | Yes | System set. |
| `event_summary` | Text | Yes | Human-readable summary. |
| `event_payload_json` | JSON | No | Structured details. |
| `before_hash` | Hash | No | Hash before change. |
| `after_hash` | Hash | No | Hash after change. |
| `ip_address` | Text | No | If available. |
| `user_agent` | Text | No | If available. |
| `event_hash` | Hash | Yes | Hash of event record. |
| `previous_event_hash` | Hash | No | Optional hash chain. |

Insert-only constraints:

1. No updates or deletes through normal application paths.
2. Every governed transition must produce an audit event.
3. Every publication must produce an audit event.
4. Every change to hash-affecting data must produce an audit event.

---

### 23.2 `std_audit_snapshot`

Snapshot of key object state for audit/evidence.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `snapshot_code` | Text | Yes | Unique. |
| `target_table` | Text | Yes | Snapshotted table. |
| `target_id` | ULID | Yes | Snapshotted record. |
| `snapshot_type` | Enum | Yes | `IMPORT`, `REVIEW`, `APPROVAL`, `ACTIVATION`, `BINDING`, `PUBLICATION`, `ADDENDUM`, `CONTRACT_FORMATION`, `EXPORT`. |
| `snapshot_json` | JSON | Yes | Canonical object graph snapshot. |
| `snapshot_hash` | Hash | Yes | Hash of snapshot JSON. |
| `created_at` | Datetime | Yes | System set. |
| `created_by` | ULID/ExternalRef | Yes | User/service. |

Unique constraints:

1. `snapshot_code` unique.
2. `(target_table, target_id, snapshot_type, snapshot_hash)` unique.

---

## 24. Role and Permission Domain Tables

These tables provide the domain model foundation. The detailed permission matrix should be completed in the next artifact.

### 24.1 `std_role`

STD Engine role.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `role_code` | Text | Yes | Unique. |
| `role_name` | Text | Yes | Display name. |
| `description` | LongText | No | Optional. |
| `role_scope` | Enum | Yes | `GLOBAL`, `AUTHORITY`, `PROCURING_ENTITY`, `TENDER`, `SYSTEM`. |
| `is_system_role` | Boolean | Yes | System role cannot be deleted. |
| `is_active` | Boolean | Yes | Default true. |

Core roles:

1. `STD_SYSTEM_ADMIN`.
2. `STD_TEMPLATE_AUTHOR`.
3. `STD_TEMPLATE_REVIEWER`.
4. `STD_LEGAL_REVIEWER`.
5. `STD_APPROVER`.
6. `STD_PUBLISHER`.
7. `PROCUREMENT_OFFICER`.
8. `PROCUREMENT_REVIEWER`.
9. `EVALUATION_SECRETARY`.
10. `AUDITOR`.
11. `READ_ONLY_VIEWER`.

---

### 24.2 `std_permission`

Atomic permission.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `permission_code` | Text | Yes | Unique. |
| `permission_name` | Text | Yes | Display name. |
| `target_table` | Text | No | Optional table scope. |
| `action_code` | Text | Yes | `CREATE`, `READ`, `UPDATE`, `DELETE`, `SUBMIT`, `APPROVE`, `REJECT`, `ACTIVATE`, `PUBLISH`, `EXPORT`, etc. |
| `description` | LongText | No | Optional. |
| `is_system_permission` | Boolean | Yes | Default true for core. |
| `is_active` | Boolean | Yes | Default true. |

Unique constraints:

1. `permission_code` unique.

---

### 24.3 `std_role_permission`

Mapping between roles and permissions.

| Column | Type | Required | Constraints / Notes |
|---|---:|---:|---|
| `role_id` | ULID | Yes | FK to `std_role`. |
| `permission_id` | ULID | Yes | FK to `std_permission`. |
| `condition_json` | JSON | No | Optional context constraint. |
| `is_active` | Boolean | Yes | Default true. |

Unique constraints:

1. `(role_id, permission_id)` unique.

---

## 25. Core Enum Sets

### 25.1 `TEMPLATE_VERSION_STATUS`

| Code | Meaning |
|---|---|
| `DRAFT` | Initial editable state. |
| `STRUCTURING` | Template content/schema being structured. |
| `INTERNAL_REVIEW` | Internal product/procurement review. |
| `LEGAL_REVIEW` | Legal or regulatory review. |
| `APPROVED` | Approved but not active. |
| `ACTIVE` | Available for new tenders; immutable. |
| `SUSPENDED` | Temporarily unavailable for new tenders. |
| `SUPERSEDED` | Replaced by newer version; existing tenders may continue. |
| `ARCHIVED` | Retained for audit only. |
| `REJECTED` | Review rejected. |

### 25.2 `TENDER_INSTANCE_STATUS`

| Code | Meaning |
|---|---|
| `NOT_STARTED` | Instance created but not configured. |
| `IN_CONFIGURATION` | PE is configuring values. |
| `VALIDATION_FAILED` | Blocking findings exist. |
| `READY_FOR_REVIEW` | Configuration complete enough for review. |
| `PROCUREMENT_REVIEW` | Under review. |
| `APPROVED_FOR_TENDER_CREATION` | Approved to generate tender. |
| `BOUND_TO_TENDER` | Bound to tender record. |
| `PUBLISHED` | Issued bundle published; immutable. |
| `ADDENDUM_REQUIRED` | Change required after publication. |
| `SUPERSEDED_BY_ADDENDUM` | Original bundle superseded. |
| `CANCELLED` | Instance cancelled. |
| `ARCHIVED` | Retained for audit. |

### 25.3 `MUTABILITY_TYPE`

| Code | Meaning |
|---|---|
| `LOCKED` | Cannot be changed by PE users; official legal text. |
| `PARAMETERIZED` | Text fixed but placeholders supplied through parameters. |
| `CONFIGURABLE` | PE selects or enters controlled values. |
| `CONTROLLED_EDIT` | Editable only under role, rule, and approval constraints. |
| `PE_AUTHORED` | PE may author content inside structured schema. |
| `SYSTEM_GENERATED` | Generated by system from other records. |
| `BIDDER_COMPLETED` | Completed by bidder/supplier. |
| `EVALUATOR_COMPLETED` | Completed by evaluators. |
| `CONTRACT_CARRY_FORWARD` | Populated from tender/award/contract data. |
| `REFERENCE_ONLY` | Informational, not legally operative. |

### 25.4 `LIFECYCLE_STAGE`

| Code |
|---|
| `TEMPLATE_ADMIN` |
| `TENDER_CONFIGURATION` |
| `TENDER_REVIEW` |
| `TENDER_PUBLICATION` |
| `BIDDER_SUBMISSION` |
| `TENDER_OPENING` |
| `EVALUATION` |
| `AWARD` |
| `CONTRACT_FORMATION` |
| `CONTRACT_MANAGEMENT` |
| `ADDENDUM` |
| `AUDIT` |

### 25.5 `SEVERITY`

| Code | Meaning |
|---|---|
| `INFO` | Informational only. |
| `WARNING` | Needs attention but may proceed. |
| `BLOCKER` | Must be resolved before target action. |

### 25.6 `TRACE_TYPE`

| Code |
|---|
| `DIRECT_TEXT` |
| `PARAMETER_BASIS` |
| `RULE_BASIS` |
| `FORM_BASIS` |
| `SCHEMA_BASIS` |
| `RENDER_BASIS` |
| `CALIBRATION_ONLY` |

### 25.7 `BUNDLE_TYPE`

| Code |
|---|
| `TENDER_DOCUMENT` |
| `BIDDER_FORM_PACK` |
| `EVALUATION_PACK` |
| `CONTRACT_PACK` |
| `ADDENDUM_PACK` |
| `PREVIEW` |
| `AUDIT_EXPORT` |

---

## 26. Required Database Constraints and Guards

### 26.1 Template Activation Guards

A template version may transition to `ACTIVE` only if all conditions are true:

1. Template status is `APPROVED`.
2. Source document exists and has `source_file_hash`.
3. All required sections exist.
4. All source-trace-required objects have source trace links.
5. All locked clauses have `content_hash`.
6. All required parameters have valid schema.
7. All required forms have valid fields.
8. All required rules parse/compile.
9. All required rule test cases pass.
10. Render profile exists for tender document output.
11. Deterministic render smoke contract passes.
12. Zero open blocker validation findings exist.
13. Approval request for activation is approved.
14. Activation snapshot hash is generated.

### 26.2 Active Template Immutability Guards

When `std_template_version.status IN ('ACTIVE','SUPERSEDED','ARCHIVED')`, the following are prohibited through normal application paths:

1. Updating hash-affecting fields on template child records.
2. Deleting sections, clauses, parameters, rules, forms, schemas, render blocks, or source trace links.
3. Replacing source document links.
4. Changing workflow history.
5. Changing approval history.

Corrective change requires either:

1. A new template version; or
2. A governed administrative correction that creates a new immutable snapshot and audit event, if permitted by policy.

### 26.3 Published Tender Immutability Guards

When `std_tender_instance.status = 'PUBLISHED'`, the following are prohibited outside addendum workflow:

1. Updating current configuration values.
2. Updating tender requirement rows.
3. Updating price line templates.
4. Re-rendering and replacing published bundle in place.
5. Changing evaluation schema published to evaluators.
6. Changing bidder submission schema issued to bidders.

### 26.4 Source Trace Guards

1. `LOCKED` legal content requires source trace.
2. `RULE_BASIS` trace is required for rules that block tender publication, evaluation, award, or contract formation.
3. `FORM_BASIS` trace is required for mandatory bidder forms.
4. `SCHEMA_BASIS` trace is required for required price/evaluation/contract schemas.
5. `CALIBRATION_ONLY` traces never satisfy activation requirements.

---

## 27. Recommended Indexes

### 27.1 Template Lookup Indexes

| Table | Index |
|---|---|
| `std_template_family` | `(authority_id, jurisdiction_id, procurement_category_id, is_active)` |
| `std_template_version` | `(family_id, status, effective_from, effective_to)` |
| `std_template_version` | `(template_code)` unique |
| `std_tpl_section` | `(template_version_id, section_type, sort_order)` |
| `std_tpl_clause` | `(template_version_id, section_id, sort_order)` |
| `std_tpl_parameter` | `(template_version_id, parameter_code)` unique |

### 27.2 Runtime Tender Indexes

| Table | Index |
|---|---|
| `std_tender_instance` | `(tender_id)` |
| `std_tender_instance` | `(template_version_id, status)` |
| `std_tender_config_value` | `(tender_instance_id, parameter_id, is_current)` |
| `std_tender_requirement_item` | `(tender_instance_id, requirement_schema_id, is_current)` |
| `std_gen_bundle` | `(tender_instance_id, bundle_type, bundle_status)` |
| `std_addendum_record` | `(tender_instance_id, status)` |

### 27.3 Audit and Trace Indexes

| Table | Index |
|---|---|
| `std_source_trace_link` | `(target_table, target_id)` |
| `std_source_trace_link` | `(source_document_id, source_location_id)` |
| `std_audit_event` | `(target_table, target_id, event_at)` |
| `std_audit_event` | `(actor_id, event_at)` |
| `std_validation_finding` | `(target_table, target_id, severity, resolution_status)` |

---

## 28. External Module Boundaries

The STD Engine owns the following:

1. STD template families and versions.
2. STD source traceability.
3. Section, clause, parameter, rule, form, schema, and render definitions.
4. Tender STD instances and STD configuration values.
5. Generated STD-derived tender, bidder, evaluation, and contract schemas.
6. Published STD-derived bundles and hashes.
7. STD addendum impact analysis.
8. STD audit evidence.

The STD Engine does not own the following, but exposes or consumes references:

| External module | STD Engine interaction |
|---|---|
| Tender Management | Receives active template list, binds tender to template version, receives generated tender bundle. |
| Supplier Portal | Receives bidder response schemas and evidence requirements. |
| Opening Module | Receives published opening fields and form metadata if applicable. |
| Evaluation Module | Receives published evaluation schema and bidder response mappings. |
| Contract Management | Receives contract formation schemas and carry-forward mappings. |
| Document Management | Stores source files and generated artifacts. |
| Identity/RBAC | Supplies users, roles, permissions, and organizational scope. |
| Audit/Reporting | Consumes audit events, snapshots, hashes, and generated bundles. |

---

## 29. Migration Mapping from WORKS PoC JSON

| PoC JSON concept | Production table(s) |
|---|---|
| `manifest` | `std_template_family`, `std_template_version`, `std_template_version_metadata` |
| `authority` | `std_authority` |
| `jurisdiction` | `std_jurisdiction` |
| `classification` | `std_procurement_category`, `std_template_version_metadata` |
| `source_document` | `std_src_document`, `std_src_document_version`, `std_source_trace_link` |
| `sections` | `std_tpl_section`, `std_tpl_content_block`, `std_tpl_clause` |
| `configurable_fields` | `std_tpl_parameter`, `std_tpl_parameter_group`, `std_tpl_parameter_option` |
| `rules` | `std_rule_definition`, `std_rule_target`, `std_rule_input`, `std_rule_test_case` |
| `forms` | `std_form_schema`, `std_form_section`, `std_form_field`, `std_evidence_requirement` |
| `boq_hooks` | Domain-specific extension through price/requirements schema or future WORKS extension tables. |
| `render_map` | `std_render_profile`, `std_render_block`, `std_render_placeholder` |
| `validation` | `std_validation_run`, `std_validation_finding`, `std_smoke_contract` |

---

## 30. Minimum Implementation Cut for Release 1

Release 1 should implement only the minimum tables needed to safely import, govern, activate, and render the first IT STD seed.

Minimum required tables:

1. `std_authority`.
2. `std_jurisdiction`.
3. `std_procurement_category`.
4. `std_template_family`.
5. `std_template_version`.
6. `std_src_document`.
7. `std_src_location`.
8. `std_src_extract`.
9. `std_source_trace_link`.
10. `std_tpl_section`.
11. `std_tpl_content_block`.
12. `std_tpl_clause`.
13. `std_tpl_parameter_group`.
14. `std_tpl_parameter`.
15. `std_tpl_parameter_option`.
16. `std_rule_definition`.
17. `std_rule_target`.
18. `std_rule_input`.
19. `std_rule_test_case`.
20. `std_form_schema`.
21. `std_form_section`.
22. `std_form_field`.
23. `std_evidence_requirement`.
24. `std_req_schema`.
25. `std_price_schema`.
26. `std_eval_schema`.
27. `std_contract_schema`.
28. `std_render_profile`.
29. `std_render_block`.
30. `std_workflow_definition`.
31. `std_workflow_state`.
32. `std_workflow_transition`.
33. `std_transition_guard`.
34. `std_approval_request`.
35. `std_approval_step`.
36. `std_approval_event`.
37. `std_validation_run`.
38. `std_validation_finding`.
39. `std_pkg_import`.
40. `std_pkg_import_item`.
41. `std_smoke_contract`.
42. `std_smoke_test_case`.
43. `std_smoke_run`.
44. `std_smoke_run_result`.
45. `std_audit_event`.
46. `std_audit_snapshot`.

Release 2 should add tender instance, generated bundle, addendum, bidder schema, and contract carry-forward runtime tables.

---

## 31. Domain Model Acceptance Criteria

The domain model is acceptable for implementation when all of the following are true:

1. It can represent multiple STD families and versions.
2. It can distinguish official source documents from calibration tenders.
3. It can represent locked, parameterized, configurable, PE-authored, bidder-completed, evaluator-completed, and contract carry-forward content.
4. It can source-trace all material STD objects.
5. It can prevent activation without source trace, validation, approval, and smoke test success.
6. It can bind a tender to an active template version.
7. It can store tender-specific configuration values without mutating the master template.
8. It can generate immutable tender bundles.
9. It can support addendum impact analysis.
10. It can support bidder response schemas, evaluation schemas, and contract carry-forward schemas.
11. It can produce audit evidence through hashes, snapshots, and immutable events.
12. It can import/export packages without making JSON the production source of truth.
13. It can support the IT STD as the first full seed.
14. It can support future WORKS/Goods/Services STDs through extension schemas rather than hard-coded logic.

---

## 32. Next Artifact

The next artifact should be:

**STD Engine Core Module - Governance, Roles, Permissions, and State Model**

That artifact should define:

1. Full role matrix.
2. Permission matrix by table and lifecycle state.
3. Template version workflow transitions.
4. Tender STD instance workflow transitions.
5. Approval step rules.
6. Transition guards.
7. Immutability enforcement matrix.
8. Break-glass administrative correction policy.
9. Audit event requirements by action.
10. Seed workflow definitions.

Only after that should we produce implementation-level API contracts and UI specifications.
