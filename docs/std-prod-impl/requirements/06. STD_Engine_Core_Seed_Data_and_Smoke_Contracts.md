# STD Engine Core Module - Seed Data and Smoke Contracts

**Project:** KenTender e-Procurement System  
**Module:** Standard Tender Document Engine Core  
**Document type:** Seed Data and Smoke Contracts  
**Document status:** Draft for implementation review  
**Version:** 0.1  
**Prepared date:** 2026-07-07  
**Preceding artifact:** `STD_Engine_Core_Governance_Roles_Permissions_State_Model.md`  
**Next artifact:** STD Engine Core API and UI Contract / Cursor Implementation Pack  

---

## 1. Purpose

This document defines the initial seed data and smoke contracts required to implement the Standard Tender Document Engine Core Module safely.

The purpose is to convert the approved conceptual, PRD, domain-model, and governance/state-model work into implementation-ready controlled values, initial records, transition definitions, permissions, validation fixtures, and acceptance tests.

This document is generalized for multiple Standard Tender Document families. It must not hard-code the engine for the Information Technology STD only. The IT STD should be implemented as the first production STD package on top of this generalized engine.

---

## 2. Scope

### 2.1 In Scope

This artifact covers seed data and smoke contracts for:

1. Source authorities.
2. STD family records.
3. STD version lifecycle states.
4. Source document states.
5. Import/export package states.
6. Component states.
7. Tender STD instance states.
8. Generated bundle states.
9. Addendum impact states.
10. Mutability types.
11. Section types.
12. Parameter types.
13. Form and field types.
14. Evidence requirement types.
15. Rule types.
16. Validation severity and blocking behavior.
17. Render block types.
18. Audit event types.
19. Role and permission seeds.
20. Approval tracks.
21. State-transition seeds.
22. Smoke contracts.
23. Minimum test fixtures.
24. Import/export package validation seeds.

### 2.2 Out of Scope

This artifact does not define:

1. The full IT STD extraction matrix.
2. The full IT STD package.
3. UI screen layouts.
4. API endpoint payloads.
5. Bidder portal screens.
6. Evaluation committee workflow beyond STD-generated structures.
7. Contract management after contract formation.
8. Procurement method configuration outside STD binding.

---

## 3. Implementation Principle

Seed data must be treated as controlled platform configuration. It must be versioned, reviewable, repeatable, idempotent, and safe to re-run in development, staging, and production.

Smoke contracts must be executable. Each smoke contract must prove one essential behavior that protects the legal, procedural, or audit integrity of the STD Engine.

The engine must fail closed. When a source document, STD version, rule, form, render block, approval, tender binding, or generated document is inconsistent, the system must block activation, publication, award, or contract generation as appropriate.

---

## 4. Seed Data Conventions

### 4.1 Seed Key Format

Each seed record must have a stable key.

Recommended format:

```text
<DOMAIN>.<CATEGORY>.<CODE>
```

Examples:

```text
STD.AUTHORITY.PPRA
STD.FAMILY.KE_PPRA_IT
STD.MUTABILITY.LOCKED
STD.PERMISSION.STD_VERSION_ACTIVATE
STD.AUDIT.STD_VERSION_ACTIVATED
```

### 4.2 Required Seed Columns

Each seed table should support these columns:

| Column | Required | Description |
|---|---:|---|
| `seed_key` | Yes | Stable unique seed identifier. |
| `code` | Yes | Machine-readable short code. |
| `display_name` | Yes | Human-readable label. |
| `description` | Yes | Meaning and intended use. |
| `is_active` | Yes | Whether the seed is currently available. |
| `is_system` | Yes | Whether ordinary users may edit it. |
| `sort_order` | Yes | Display and evaluation order where applicable. |
| `effective_from` | No | Optional start date. |
| `effective_to` | No | Optional end date. |
| `metadata_json` | No | Controlled extension metadata. |

### 4.3 Idempotency Rule

Seed scripts must upsert by `seed_key`, not by display name.

Changing a display name must not create a duplicate seed record.

### 4.4 Deactivation Rule

Seed records that have been used in STD versions, tender instances, generated bundles, audit events, or approvals must not be deleted. They may only be deactivated.

---

## 5. Source Authority Seed Data

### 5.1 Purpose

Source authorities identify the organization or authority responsible for issuing, approving, or providing the source material from which an STD family or version is derived.

### 5.2 Seed Records

| Seed key | Code | Display name | Authority type | Active | System | Notes |
|---|---|---|---|---:|---:|---|
| `STD.AUTHORITY.PPRA` | `PPRA` | Public Procurement Regulatory Authority | `REGULATOR` | Yes | Yes | Primary source authority for Kenya public procurement STD templates. |
| `STD.AUTHORITY.PE` | `PROCURING_ENTITY` | Procuring Entity | `AGENCY` | Yes | Yes | Used for procuring-entity-specific documents and calibration tenders. |
| `STD.AUTHORITY.SYSTEM` | `SYSTEM` | KenTender System | `OTHER` | Yes | Yes | Used for system-generated fixtures, test packages, and internal smoke artifacts. |

### 5.3 Constraints

1. Every STD source document must reference one source authority.
2. Every active STD template version must trace to at least one approved source document.
3. Calibration tenders may reference a procuring entity as source authority but must not be treated as official STD master templates.

---

## 6. Source Type Seed Data

| Seed key | Code | Display name | Description | Active |
|---|---|---|---|---:|
| `STD.SOURCE_TYPE.OFFICIAL_STD` | `OFFICIAL_STD` | Official STD | Official source STD issued by the competent authority. | Yes |
| `STD.SOURCE_TYPE.CALIBRATION_TENDER` | `CALIBRATION_TENDER` | Calibration Tender | Real tender used to validate practical usability, not the legal master template. | Yes |
| `STD.SOURCE_TYPE.REFERENCE_GUIDANCE` | `REFERENCE_GUIDANCE` | Reference Guidance | Manuals, circulars, notes, or guidance material. | Yes |
| `STD.SOURCE_TYPE.IMPORT_PACKAGE` | `IMPORT_PACKAGE` | Import Package | Structured package imported into the STD Engine. | Yes |
| `STD.SOURCE_TYPE.OTHER` | `OTHER` | Other Source | Exceptional source type requiring explanation. | Yes |

---

## 7. Extraction Method and Quality Seed Data

### 7.1 Extraction Method

| Seed key | Code | Display name | Description |
|---|---|---|---|
| `STD.EXTRACTION_METHOD.NATIVE_TEXT` | `NATIVE_TEXT` | Native Text | Text extracted directly from source document text layer. |
| `STD.EXTRACTION_METHOD.OCR` | `OCR` | OCR | Text extracted by optical character recognition. |
| `STD.EXTRACTION_METHOD.MANUAL` | `MANUAL` | Manual Entry | Text entered manually by an authorized user. |
| `STD.EXTRACTION_METHOD.HYBRID` | `HYBRID` | Hybrid Extraction | Combination of native text, OCR, and/or manual correction. |

### 7.2 Extraction Quality

| Seed key | Code | Display name | Blocks activation by default |
|---|---|---|---:|
| `STD.EXTRACTION_QUALITY.HIGH` | `HIGH` | High | No |
| `STD.EXTRACTION_QUALITY.MEDIUM` | `MEDIUM` | Medium | No, but requires review |
| `STD.EXTRACTION_QUALITY.LOW` | `LOW` | Low | Yes, unless corrected/reviewed |
| `STD.EXTRACTION_QUALITY.UNKNOWN` | `UNKNOWN` | Unknown | Yes |

---

## 8. STD Family Seed Data

### 8.1 Purpose

STD families represent reusable families of tender documents. The engine must support multiple STD families without code branching per STD type.

### 8.2 Initial Seed Records

| Seed key | Family code | Display name | Source authority | Active | Notes |
|---|---|---|---|---:|---|
| `STD.FAMILY.KE_PPRA_IT` | `KE-PPRA-IT` | STD for Procurement of Information Technology | `PPRA` | Yes | First production implementation target. |
| `STD.FAMILY.KE_PPRA_WORKS_BLDG` | `KE-PPRA-WORKS-BLDG` | STD for Works - Building and Associated Civil Engineering Works | `PPRA` | Yes | Proven through earlier PoC; future production package. |
| `STD.FAMILY.KE_PPRA_GOODS` | `KE-PPRA-GOODS` | STD for Procurement of Goods | `PPRA` | No | Placeholder; activate only when source extraction begins. |
| `STD.FAMILY.KE_PPRA_CONSULTING` | `KE-PPRA-CONSULTING` | STD for Consulting Services | `PPRA` | No | Placeholder; activate only when source extraction begins. |
| `STD.FAMILY.KE_PPRA_NON_CONSULTING` | `KE-PPRA-NON-CONSULTING` | STD for Non-Consulting Services | `PPRA` | No | Placeholder; activate only when source extraction begins. |
| `STD.FAMILY.KE_PPRA_FRAMEWORK` | `KE-PPRA-FRAMEWORK` | STD for Framework Agreements | `PPRA` | No | Placeholder; activate only when source extraction begins. |

### 8.3 Guardrails

1. Placeholder families must not be selectable for tender creation.
2. A family must have at least one active template version before it can be used in a tender.
3. A family with no active version may appear only in administration screens.

---

## 9. Mutability Type Seed Data

### 9.1 Purpose

Mutability controls who can change a section, clause, form, field, or parameter, and at which lifecycle stage.

### 9.2 Seed Records

| Seed key | Code | Display name | Meaning | Default enforcement |
|---|---|---|---|---|
| `STD.MUTABILITY.LOCKED` | `LOCKED` | Locked | Legal/source text must not be edited by procuring entity users. | Block direct edits outside template governance. |
| `STD.MUTABILITY.PARAMETERIZED` | `PARAMETERIZED` | Parameterized | Text contains controlled placeholders supplied by configuration values. | Allow only parameter value completion. |
| `STD.MUTABILITY.CONFIGURABLE` | `CONFIGURABLE` | Configurable | Field or section may be completed through controlled tender configuration. | Validate against schema and rules. |
| `STD.MUTABILITY.CONTROLLED_EDIT` | `CONTROLLED_EDIT` | Controlled Edit | Structured content can be authored within boundaries, such as requirements. | Require review and source/type classification. |
| `STD.MUTABILITY.OPTIONAL_OMITTABLE` | `OPTIONAL_OMITTABLE` | Optional/Omittable | Section or block may be included or omitted based on controlled conditions. | Require rule-based activation/omission. |
| `STD.MUTABILITY.SYSTEM_GENERATED` | `SYSTEM_GENERATED` | System Generated | Content is generated from system state, tender data, award data, or contract data. | Block manual edits unless override permission exists. |
| `STD.MUTABILITY.BIDDER_COMPLETED` | `BIDDER_COMPLETED` | Bidder Completed | Form or field completed by bidder/supplier during submission. | Enforce bidder submission schema. |
| `STD.MUTABILITY.EVALUATOR_COMPLETED` | `EVALUATOR_COMPLETED` | Evaluator Completed | Checklist, score, finding, or comparison completed during evaluation. | Enforce evaluation role and audit trail. |
| `STD.MUTABILITY.CONTRACT_COMPLETED` | `CONTRACT_COMPLETED` | Contract Completed | Completed during award or contract formation. | Enforce award/contract workflow. |

### 9.3 Minimum Mutability Smoke Rule

An active template version containing a `LOCKED` clause must reject direct clause text updates by a procuring entity user.

---

## 10. Section Type Seed Data

| Seed key | Code | Display name | Typical mutability |
|---|---|---|---|
| `STD.SECTION_TYPE.COVER` | `COVER` | Cover / Identity Page | `PARAMETERIZED` |
| `STD.SECTION_TYPE.PREFACE` | `PREFACE` | Preface / User Guidance | `LOCKED` or excluded from tender issue bundle |
| `STD.SECTION_TYPE.INVITATION` | `INVITATION` | Invitation to Tender | `PARAMETERIZED` |
| `STD.SECTION_TYPE.ITT` | `ITT` | Instructions to Tenderers | `LOCKED` |
| `STD.SECTION_TYPE.TDS` | `TDS` | Tender Data Sheet | `CONFIGURABLE` |
| `STD.SECTION_TYPE.EVALUATION` | `EVALUATION` | Evaluation and Qualification Criteria | `CONFIGURABLE` or `CONTROLLED_EDIT` |
| `STD.SECTION_TYPE.FORMS` | `FORMS` | Tendering Forms | `BIDDER_COMPLETED` with locked labels and schema |
| `STD.SECTION_TYPE.REQUIREMENTS` | `REQUIREMENTS` | Procuring Entity Requirements | `CONTROLLED_EDIT` |
| `STD.SECTION_TYPE.TECHNICAL_REQUIREMENTS` | `TECHNICAL_REQUIREMENTS` | Technical Requirements | `CONTROLLED_EDIT` |
| `STD.SECTION_TYPE.PRICE_SCHEDULE` | `PRICE_SCHEDULE` | Price Schedule | `BIDDER_COMPLETED` with configured schema |
| `STD.SECTION_TYPE.BOQ` | `BOQ` | Bills of Quantities | `CONFIGURABLE` / `BIDDER_COMPLETED` |
| `STD.SECTION_TYPE.IMPLEMENTATION_SCHEDULE` | `IMPLEMENTATION_SCHEDULE` | Implementation Schedule | `CONTROLLED_EDIT` |
| `STD.SECTION_TYPE.SYSTEM_INVENTORY` | `SYSTEM_INVENTORY` | System Inventory Tables | `CONFIGURABLE` |
| `STD.SECTION_TYPE.GCC` | `GCC` | General Conditions of Contract | `LOCKED` |
| `STD.SECTION_TYPE.SCC` | `SCC` | Special Conditions of Contract | `CONFIGURABLE` |
| `STD.SECTION_TYPE.CONTRACT_FORMS` | `CONTRACT_FORMS` | Contract Forms | `SYSTEM_GENERATED` / `CONTRACT_COMPLETED` |
| `STD.SECTION_TYPE.APPENDIX` | `APPENDIX` | Appendix | Context-specific |
| `STD.SECTION_TYPE.OTHER` | `OTHER` | Other Section | Requires classification reason |

---

## 11. Block Type Seed Data

| Seed key | Code | Display name | Description |
|---|---|---|---|
| `STD.BLOCK_TYPE.HEADING` | `HEADING` | Heading | Section or subsection heading. |
| `STD.BLOCK_TYPE.PARAGRAPH` | `PARAGRAPH` | Paragraph | Standard text paragraph. |
| `STD.BLOCK_TYPE.CLAUSE` | `CLAUSE` | Clause | Numbered legal/procedural clause. |
| `STD.BLOCK_TYPE.TABLE` | `TABLE` | Table | Structured table block. |
| `STD.BLOCK_TYPE.FORM_PLACEHOLDER` | `FORM_PLACEHOLDER` | Form Placeholder | Insertion point for generated form. |
| `STD.BLOCK_TYPE.PARAMETER_PLACEHOLDER` | `PARAMETER_PLACEHOLDER` | Parameter Placeholder | Insertion point for configured value. |
| `STD.BLOCK_TYPE.RENDER_INCLUDE` | `RENDER_INCLUDE` | Render Include | Include another render block or fragment. |
| `STD.BLOCK_TYPE.NOTE` | `NOTE` | Note | Instructional note, warning, or guidance. |
| `STD.BLOCK_TYPE.OTHER` | `OTHER` | Other Block | Requires explanation. |

---

## 12. Parameter Type Seed Data

| Seed key | Code | Display name | Typical use |
|---|---|---|---|
| `STD.PARAMETER_TYPE.TEXT` | `TEXT` | Text | Short free-text values. |
| `STD.PARAMETER_TYPE.LONG_TEXT` | `LONG_TEXT` | Long Text | Narrative configuration values. |
| `STD.PARAMETER_TYPE.INTEGER` | `INTEGER` | Integer | Counts, days, number of copies. |
| `STD.PARAMETER_TYPE.DECIMAL` | `DECIMAL` | Decimal | Decimal quantities. |
| `STD.PARAMETER_TYPE.MONEY` | `MONEY` | Money | Tender security, estimated values, thresholds. |
| `STD.PARAMETER_TYPE.DATE` | `DATE` | Date | Deadlines and milestones. |
| `STD.PARAMETER_TYPE.DATETIME` | `DATETIME` | Date and Time | Submission/opening date-times. |
| `STD.PARAMETER_TYPE.BOOLEAN` | `BOOLEAN` | Boolean | Yes/no choices. |
| `STD.PARAMETER_TYPE.SELECT` | `SELECT` | Select | Controlled single choice. |
| `STD.PARAMETER_TYPE.MULTI_SELECT` | `MULTI_SELECT` | Multi-Select | Controlled multiple choice. |
| `STD.PARAMETER_TYPE.FILE` | `FILE` | File | Attachment or source reference. |
| `STD.PARAMETER_TYPE.ENTITY_REF` | `ENTITY_REF` | Entity Reference | Reference to another system entity. |
| `STD.PARAMETER_TYPE.JSON` | `JSON` | JSON | Structured custom payload. |
| `STD.PARAMETER_TYPE.TABLE` | `TABLE` | Table | Repeating row configuration. |
| `STD.PARAMETER_TYPE.DURATION` | `DURATION` | Duration | Days, months, contract period. |
| `STD.PARAMETER_TYPE.PERCENTAGE` | `PERCENTAGE` | Percentage | Security percent, margin, evaluation weight. |

---

## 13. Lifecycle Stage Seed Data

| Seed key | Code | Display name | Description |
|---|---|---|---|
| `STD.LIFECYCLE.TEMPLATE_ADMIN` | `TEMPLATE_ADMIN` | Template Administration | Master template setup and governance. |
| `STD.LIFECYCLE.TENDER_CONFIGURATION` | `TENDER_CONFIGURATION` | Tender Configuration | Procuring entity completion of tender-specific values. |
| `STD.LIFECYCLE.BIDDER_SUBMISSION` | `BIDDER_SUBMISSION` | Bidder Submission | Supplier/tenderer response stage. |
| `STD.LIFECYCLE.EVALUATION` | `EVALUATION` | Evaluation | Tender evaluation and comparison. |
| `STD.LIFECYCLE.AWARD` | `AWARD` | Award | Intention to award, standstill, and award actions. |
| `STD.LIFECYCLE.CONTRACT_FORMATION` | `CONTRACT_FORMATION` | Contract Formation | Contract forms and appendices. |
| `STD.LIFECYCLE.ADDENDUM` | `ADDENDUM` | Addendum | Post-publication amendment handling. |

---

## 14. Rule Type Seed Data

| Seed key | Code | Display name | Description |
|---|---|---|---|
| `STD.RULE_TYPE.VALIDATION` | `VALIDATION` | Validation Rule | Checks data correctness or completeness. |
| `STD.RULE_TYPE.ACTIVATION` | `ACTIVATION` | Activation Rule | Determines whether a section, form, or field is active. |
| `STD.RULE_TYPE.CALCULATION` | `CALCULATION` | Calculation Rule | Computes a value. |
| `STD.RULE_TYPE.DERIVATION` | `DERIVATION` | Derivation Rule | Derives a value from another value or state. |
| `STD.RULE_TYPE.VISIBILITY` | `VISIBILITY` | Visibility Rule | Controls whether UI/render output is shown. |
| `STD.RULE_TYPE.ELIGIBILITY` | `ELIGIBILITY` | Eligibility Rule | Determines eligibility or qualification compliance. |
| `STD.RULE_TYPE.SCORING` | `SCORING` | Scoring Rule | Computes or validates evaluation score. |
| `STD.RULE_TYPE.RENDERING` | `RENDERING` | Rendering Rule | Controls document generation. |
| `STD.RULE_TYPE.GOVERNANCE` | `GOVERNANCE` | Governance Rule | Controls approval, state transition, or segregation of duties. |
| `STD.RULE_TYPE.SMOKE_TEST` | `SMOKE_TEST` | Smoke Test Rule | Test-only rule used for smoke fixtures. |

---

## 15. Rule Scope Seed Data

| Seed key | Code | Display name |
|---|---|---|
| `STD.RULE_SCOPE.TEMPLATE` | `TEMPLATE` | Template |
| `STD.RULE_SCOPE.SECTION` | `SECTION` | Section |
| `STD.RULE_SCOPE.CLAUSE` | `CLAUSE` | Clause |
| `STD.RULE_SCOPE.PARAMETER` | `PARAMETER` | Parameter |
| `STD.RULE_SCOPE.FORM` | `FORM` | Form |
| `STD.RULE_SCOPE.FORM_FIELD` | `FORM_FIELD` | Form Field |
| `STD.RULE_SCOPE.REQUIREMENT` | `REQUIREMENT` | Requirement |
| `STD.RULE_SCOPE.PRICE_SCHEDULE` | `PRICE_SCHEDULE` | Price Schedule |
| `STD.RULE_SCOPE.EVALUATION` | `EVALUATION` | Evaluation |
| `STD.RULE_SCOPE.CONTRACT` | `CONTRACT` | Contract |
| `STD.RULE_SCOPE.TENDER_INSTANCE` | `TENDER_INSTANCE` | Tender STD Instance |
| `STD.RULE_SCOPE.GENERATED_BUNDLE` | `GENERATED_BUNDLE` | Generated Bundle |
| `STD.RULE_SCOPE.ADDENDUM` | `ADDENDUM` | Addendum |

---

## 16. Severity and Blocking Behavior Seed Data

### 16.1 Severity

| Seed key | Code | Display name | Meaning |
|---|---|---|---|
| `STD.SEVERITY.INFO` | `INFO` | Information | Advisory finding; does not block. |
| `STD.SEVERITY.WARNING` | `WARNING` | Warning | Requires attention; may block at later stage depending on rule. |
| `STD.SEVERITY.BLOCKER` | `BLOCKER` | Blocker | Must be resolved or explicitly overridden where allowed. |

### 16.2 Blocking Behavior

| Seed key | Code | Display name | Meaning |
|---|---|---|---|
| `STD.BLOCKING.NON_BLOCKING` | `NON_BLOCKING` | Non-Blocking | Does not block state transition. |
| `STD.BLOCKING.BLOCKS_SAVE` | `BLOCKS_SAVE` | Blocks Save | Prevents saving invalid data. |
| `STD.BLOCKING.BLOCKS_REVIEW` | `BLOCKS_REVIEW` | Blocks Review | Prevents submission for review. |
| `STD.BLOCKING.BLOCKS_APPROVAL` | `BLOCKS_APPROVAL` | Blocks Approval | Prevents approval decision. |
| `STD.BLOCKING.BLOCKS_ACTIVATION` | `BLOCKS_ACTIVATION` | Blocks Activation | Prevents activating template version. |
| `STD.BLOCKING.BLOCKS_PUBLICATION` | `BLOCKS_PUBLICATION` | Blocks Publication | Prevents publishing tender bundle. |
| `STD.BLOCKING.BLOCKS_AWARD` | `BLOCKS_AWARD` | Blocks Award | Prevents award-stage actions. |
| `STD.BLOCKING.BLOCKS_CONTRACT` | `BLOCKS_CONTRACT` | Blocks Contract | Prevents contract generation or execution. |

---

## 17. Expression Language Seed Data

| Seed key | Code | Display name | Recommended use |
|---|---|---|---|
| `STD.EXPRESSION.JSON_LOGIC` | `JSON_LOGIC` | JSON Logic | Preferred portable rule expression format. |
| `STD.EXPRESSION.CEL` | `CEL` | Common Expression Language | Preferred for richer typed expressions if supported. |
| `STD.EXPRESSION.PY_EXPR_SAFE` | `PY_EXPR_SAFE` | Safe Python Expression | Only with strict sandbox and allowlist. |
| `STD.EXPRESSION.SQL_SAFE` | `SQL_SAFE` | Safe SQL Expression | Only for controlled server-side checks. |
| `STD.EXPRESSION.CUSTOM_ENGINE` | `CUSTOM_ENGINE` | Custom Engine | For specialized rules implemented in code. |
| `STD.EXPRESSION.MANUAL_CHECK` | `MANUAL_CHECK` | Manual Check | For review-only checks that cannot be automated. |

Implementation recommendation: use `JSON_LOGIC` as the first implementation target. Defer `CEL`, `PY_EXPR_SAFE`, and `SQL_SAFE` unless there is a demonstrated need.

---

## 18. Form Seed Data

### 18.1 Respondent Type

| Seed key | Code | Display name | Description |
|---|---|---|---|
| `STD.RESPONDENT.PROCURING_ENTITY` | `PROCURING_ENTITY` | Procuring Entity | Completed by procuring entity users. |
| `STD.RESPONDENT.TENDERER` | `TENDERER` | Tenderer | Completed by tenderer/bidder/supplier. |
| `STD.RESPONDENT.EVALUATOR` | `EVALUATOR` | Evaluator | Completed by evaluation users. |
| `STD.RESPONDENT.APPROVER` | `APPROVER` | Approver | Completed by approval users. |
| `STD.RESPONDENT.SYSTEM` | `SYSTEM` | System | Generated automatically. |
| `STD.RESPONDENT.SUCCESSFUL_TENDERER` | `SUCCESSFUL_TENDERER` | Successful Tenderer | Completed after award before or during contract formation. |

### 18.2 Form Type

| Seed key | Code | Display name | Typical respondent |
|---|---|---|---|
| `STD.FORM_TYPE.FORM_OF_TENDER` | `FORM_OF_TENDER` | Form of Tender | `TENDERER` |
| `STD.FORM_TYPE.ELIGIBILITY` | `ELIGIBILITY` | Eligibility Form | `TENDERER` |
| `STD.FORM_TYPE.CONFIDENTIAL_BUSINESS_QUESTIONNAIRE` | `CONFIDENTIAL_BUSINESS_QUESTIONNAIRE` | Confidential Business Questionnaire | `TENDERER` |
| `STD.FORM_TYPE.INDEPENDENT_TENDER_DETERMINATION` | `INDEPENDENT_TENDER_DETERMINATION` | Certificate of Independent Tender Determination | `TENDERER` |
| `STD.FORM_TYPE.SELF_DECLARATION` | `SELF_DECLARATION` | Self Declaration | `TENDERER` |
| `STD.FORM_TYPE.TENDER_SECURITY` | `TENDER_SECURITY` | Tender Security Form | `TENDERER` |
| `STD.FORM_TYPE.TENDER_SECURING_DECLARATION` | `TENDER_SECURING_DECLARATION` | Tender Securing Declaration | `TENDERER` |
| `STD.FORM_TYPE.QUALIFICATION` | `QUALIFICATION` | Qualification Form | `TENDERER` |
| `STD.FORM_TYPE.EXPERIENCE` | `EXPERIENCE` | Experience Form | `TENDERER` |
| `STD.FORM_TYPE.PERSONNEL` | `PERSONNEL` | Personnel Form | `TENDERER` |
| `STD.FORM_TYPE.EQUIPMENT` | `EQUIPMENT` | Equipment Form | `TENDERER` |
| `STD.FORM_TYPE.PRICE_SCHEDULE` | `PRICE_SCHEDULE` | Price Schedule | `TENDERER` |
| `STD.FORM_TYPE.TECHNICAL_CONFORMANCE` | `TECHNICAL_CONFORMANCE` | Technical Conformance Matrix | `TENDERER` |
| `STD.FORM_TYPE.IP_DISCLOSURE` | `IP_DISCLOSURE` | Intellectual Property Disclosure | `TENDERER` |
| `STD.FORM_TYPE.SUBCONTRACTOR_DISCLOSURE` | `SUBCONTRACTOR_DISCLOSURE` | Subcontractor Disclosure | `TENDERER` |
| `STD.FORM_TYPE.BENEFICIAL_OWNERSHIP` | `BENEFICIAL_OWNERSHIP` | Beneficial Ownership Disclosure | `SUCCESSFUL_TENDERER` |
| `STD.FORM_TYPE.NOTIFICATION_OF_INTENTION_TO_AWARD` | `NOTIFICATION_OF_INTENTION_TO_AWARD` | Notification of Intention to Award | `SYSTEM` |
| `STD.FORM_TYPE.LETTER_OF_AWARD` | `LETTER_OF_AWARD` | Letter of Award | `SYSTEM` |
| `STD.FORM_TYPE.CONTRACT_AGREEMENT` | `CONTRACT_AGREEMENT` | Contract Agreement | `SYSTEM` / `SUCCESSFUL_TENDERER` |
| `STD.FORM_TYPE.PERFORMANCE_SECURITY` | `PERFORMANCE_SECURITY` | Performance Security | `SUCCESSFUL_TENDERER` |
| `STD.FORM_TYPE.ADVANCE_PAYMENT_SECURITY` | `ADVANCE_PAYMENT_SECURITY` | Advance Payment Security | `SUCCESSFUL_TENDERER` |
| `STD.FORM_TYPE.ACCEPTANCE_CERTIFICATE` | `ACCEPTANCE_CERTIFICATE` | Installation / Operational Acceptance Certificate | `SYSTEM` / `APPROVER` |
| `STD.FORM_TYPE.CHANGE_ORDER` | `CHANGE_ORDER` | Change Order Form | `SYSTEM` / `APPROVER` |

### 18.3 Field Type

| Seed key | Code | Display name |
|---|---|---|
| `STD.FIELD_TYPE.TEXT` | `TEXT` | Text |
| `STD.FIELD_TYPE.LONG_TEXT` | `LONG_TEXT` | Long Text |
| `STD.FIELD_TYPE.INTEGER` | `INTEGER` | Integer |
| `STD.FIELD_TYPE.DECIMAL` | `DECIMAL` | Decimal |
| `STD.FIELD_TYPE.MONEY` | `MONEY` | Money |
| `STD.FIELD_TYPE.DATE` | `DATE` | Date |
| `STD.FIELD_TYPE.DATETIME` | `DATETIME` | Date and Time |
| `STD.FIELD_TYPE.BOOLEAN` | `BOOLEAN` | Boolean |
| `STD.FIELD_TYPE.SELECT` | `SELECT` | Select |
| `STD.FIELD_TYPE.MULTI_SELECT` | `MULTI_SELECT` | Multi-Select |
| `STD.FIELD_TYPE.FILE_UPLOAD` | `FILE_UPLOAD` | File Upload |
| `STD.FIELD_TYPE.ENTITY_REF` | `ENTITY_REF` | Entity Reference |
| `STD.FIELD_TYPE.TABLE` | `TABLE` | Table |
| `STD.FIELD_TYPE.CHECKBOX` | `CHECKBOX` | Checkbox |
| `STD.FIELD_TYPE.SIGNATURE` | `SIGNATURE` | Signature |
| `STD.FIELD_TYPE.CALCULATED` | `CALCULATED` | Calculated |

---

## 19. Evidence Requirement Seed Data

### 19.1 Evidence Type

| Seed key | Code | Display name | Description |
|---|---|---|---|
| `STD.EVIDENCE.CERTIFICATE` | `CERTIFICATE` | Certificate | Certificate issued by an authority or third party. |
| `STD.EVIDENCE.DECLARATION` | `DECLARATION` | Declaration | Signed self-declaration or undertaking. |
| `STD.EVIDENCE.AUTHORIZATION_LETTER` | `AUTHORIZATION_LETTER` | Authorization Letter | Manufacturer, partner, signatory, or representative authorization. |
| `STD.EVIDENCE.BANK_GUARANTEE` | `BANK_GUARANTEE` | Bank Guarantee | Financial guarantee issued by bank. |
| `STD.EVIDENCE.INSURANCE_BOND` | `INSURANCE_BOND` | Insurance Bond | Bond issued by insurer. |
| `STD.EVIDENCE.FINANCIAL_STATEMENT` | `FINANCIAL_STATEMENT` | Financial Statement | Audited financial statement or equivalent. |
| `STD.EVIDENCE.REFERENCE_LETTER` | `REFERENCE_LETTER` | Reference Letter | Client reference or completion letter. |
| `STD.EVIDENCE.CV` | `CV` | Curriculum Vitae | Personnel CV. |
| `STD.EVIDENCE.PROFESSIONAL_CERTIFICATION` | `PROFESSIONAL_CERTIFICATION` | Professional Certification | Professional or technical certificate. |
| `STD.EVIDENCE.LICENSE` | `LICENSE` | License | Business, software, professional, or regulatory license. |
| `STD.EVIDENCE.TECHNICAL_PROPOSAL` | `TECHNICAL_PROPOSAL` | Technical Proposal | Technical proposal document or structured response. |
| `STD.EVIDENCE.PRICE_SCHEDULE` | `PRICE_SCHEDULE` | Price Schedule | Completed financial/price schedule. |
| `STD.EVIDENCE.OTHER` | `OTHER` | Other Evidence | Requires description and approval. |

### 19.2 Evidence Criticality

| Seed key | Code | Display name | Default behavior |
|---|---|---|---|
| `STD.EVIDENCE_CRITICALITY.MANDATORY` | `MANDATORY` | Mandatory | Missing evidence blocks submission or evaluation progression. |
| `STD.EVIDENCE_CRITICALITY.CONDITIONAL` | `CONDITIONAL` | Conditional | Required when activation rule is true. |
| `STD.EVIDENCE_CRITICALITY.OPTIONAL` | `OPTIONAL` | Optional | May be supplied but does not block. |

---

## 20. Price Schedule Seed Data

### 20.1 Price Schedule Type

| Seed key | Code | Display name | Description |
|---|---|---|---|
| `STD.PRICE_TYPE.BOQ` | `BOQ` | Bills of Quantities | Unit-rate work quantities and bidder rates. |
| `STD.PRICE_TYPE.SUPPLY_INSTALLATION` | `SUPPLY_INSTALLATION` | Supply and Installation | IT or goods supply/install price schedule. |
| `STD.PRICE_TYPE.RECURRENT_COST` | `RECURRENT_COST` | Recurrent Cost | Maintenance, support, license, subscription, or operating costs. |
| `STD.PRICE_TYPE.GRAND_SUMMARY` | `GRAND_SUMMARY` | Grand Summary | Summary of one or more price schedule types. |
| `STD.PRICE_TYPE.DAYWORK` | `DAYWORK` | Daywork | Labor/material/equipment rates. |
| `STD.PRICE_TYPE.PROVISIONAL_SUM` | `PROVISIONAL_SUM` | Provisional Sum | PE-defined provisional amount. |
| `STD.PRICE_TYPE.OTHER` | `OTHER` | Other Price Schedule | Requires explicit schema. |

### 20.2 Price Line Basis

| Seed key | Code | Display name |
|---|---|---|
| `STD.PRICE_LINE.QUANTITY_RATE` | `QUANTITY_RATE` | Quantity and Rate |
| `STD.PRICE_LINE.LUMP_SUM` | `LUMP_SUM` | Lump Sum |
| `STD.PRICE_LINE.PERCENTAGE` | `PERCENTAGE` | Percentage |
| `STD.PRICE_LINE.RECURRENT_PERIOD` | `RECURRENT_PERIOD` | Recurrent Period |
| `STD.PRICE_LINE.SYSTEM_CALCULATED` | `SYSTEM_CALCULATED` | System Calculated |

---

## 21. Requirement Seed Data

### 21.1 Requirement Type

| Seed key | Code | Display name | Description |
|---|---|---|---|
| `STD.REQ_TYPE.FUNCTIONAL` | `FUNCTIONAL` | Functional Requirement | Business or functional capability requirement. |
| `STD.REQ_TYPE.ARCHITECTURAL` | `ARCHITECTURAL` | Architectural Requirement | Architecture, integration, hosting, security, or design requirement. |
| `STD.REQ_TYPE.PERFORMANCE` | `PERFORMANCE` | Performance Requirement | SLA, throughput, availability, response time, load, or capacity requirement. |
| `STD.REQ_TYPE.SERVICE` | `SERVICE` | Service Requirement | Implementation, migration, training, support, or managed service requirement. |
| `STD.REQ_TYPE.TECHNOLOGY` | `TECHNOLOGY` | Technology Requirement | Hardware, software, network, cloud, license, or platform requirement. |
| `STD.REQ_TYPE.COMPLIANCE` | `COMPLIANCE` | Compliance Requirement | Legal, regulatory, policy, data protection, security, or standards compliance. |
| `STD.REQ_TYPE.TESTING_ACCEPTANCE` | `TESTING_ACCEPTANCE` | Testing and Acceptance Requirement | UAT, commissioning, acceptance, guarantee, or certification requirement. |
| `STD.REQ_TYPE.IMPLEMENTATION` | `IMPLEMENTATION` | Implementation Requirement | Milestone, schedule, deliverable, sequencing, location, or project management requirement. |
| `STD.REQ_TYPE.OTHER` | `OTHER` | Other Requirement | Requires classification reason. |

### 21.2 Requirement Criticality

| Seed key | Code | Display name | Evaluation effect |
|---|---|---|---|
| `STD.REQ_CRITICALITY.MANDATORY` | `MANDATORY` | Mandatory | Non-conformance may cause rejection or fail status. |
| `STD.REQ_CRITICALITY.SCORED` | `SCORED` | Scored | Contributes to technical score. |
| `STD.REQ_CRITICALITY.DESIRABLE` | `DESIRABLE` | Desirable | May contribute to score or comparison. |
| `STD.REQ_CRITICALITY.INFORMATIONAL` | `INFORMATIONAL` | Informational | Does not directly affect score. |

### 21.3 Conformance Response Type

| Seed key | Code | Display name |
|---|---|---|
| `STD.CONFORMANCE.YES_NO` | `YES_NO` | Yes/No |
| `STD.CONFORMANCE.COMPLY_DEVIATE` | `COMPLY_DEVIATE` | Comply/Deviate |
| `STD.CONFORMANCE.COMPLY_PARTIAL_NOT` | `COMPLY_PARTIAL_NOT` | Comply/Partially Comply/Do Not Comply |
| `STD.CONFORMANCE.NARRATIVE` | `NARRATIVE` | Narrative Response |
| `STD.CONFORMANCE.EVIDENCE_LINKED` | `EVIDENCE_LINKED` | Evidence-Linked Response |

---

## 22. Evaluation Seed Data

### 22.1 Evaluation Stage

| Seed key | Code | Display name | Description |
|---|---|---|---|
| `STD.EVAL_STAGE.PRELIMINARY` | `PRELIMINARY` | Preliminary Examination | Mandatory responsiveness and completeness checks. |
| `STD.EVAL_STAGE.TECHNICAL_PASS_FAIL` | `TECHNICAL_PASS_FAIL` | Technical Pass/Fail | Mandatory technical checks. |
| `STD.EVAL_STAGE.TECHNICAL_SCORED` | `TECHNICAL_SCORED` | Technical Scored Evaluation | Weighted technical scoring. |
| `STD.EVAL_STAGE.FINANCIAL` | `FINANCIAL` | Financial Evaluation | Price comparison and corrections. |
| `STD.EVAL_STAGE.POST_QUALIFICATION` | `POST_QUALIFICATION` | Post-Qualification | Final qualification verification. |
| `STD.EVAL_STAGE.AWARD_RECOMMENDATION` | `AWARD_RECOMMENDATION` | Award Recommendation | Recommendation based on evaluation outcome. |

### 22.2 Evaluation Criterion Type

| Seed key | Code | Display name |
|---|---|---|
| `STD.EVAL_CRITERION.MANDATORY_PASS_FAIL` | `MANDATORY_PASS_FAIL` | Mandatory Pass/Fail |
| `STD.EVAL_CRITERION.SCORED` | `SCORED` | Scored Criterion |
| `STD.EVAL_CRITERION.PRICE_COMPARISON` | `PRICE_COMPARISON` | Price Comparison |
| `STD.EVAL_CRITERION.ARITHMETIC_CORRECTION` | `ARITHMETIC_CORRECTION` | Arithmetic Correction |
| `STD.EVAL_CRITERION.MARGIN_OF_PREFERENCE` | `MARGIN_OF_PREFERENCE` | Margin of Preference |
| `STD.EVAL_CRITERION.ABNORMALLY_LOW_HIGH` | `ABNORMALLY_LOW_HIGH` | Abnormally Low/High Review |
| `STD.EVAL_CRITERION.QUALIFICATION` | `QUALIFICATION` | Qualification Criterion |

---

## 23. Render Seed Data

### 23.1 Render Output Type

| Seed key | Code | Display name |
|---|---|---|
| `STD.RENDER_OUTPUT.HTML` | `HTML` | HTML |
| `STD.RENDER_OUTPUT.PDF` | `PDF` | PDF |
| `STD.RENDER_OUTPUT.DOCX` | `DOCX` | Word Document |
| `STD.RENDER_OUTPUT.JSON` | `JSON` | JSON Bundle |
| `STD.RENDER_OUTPUT.ZIP` | `ZIP` | ZIP Package |

### 23.2 Render Job Status

| Seed key | Code | Display name |
|---|---|---|
| `STD.RENDER_STATUS.QUEUED` | `QUEUED` | Queued |
| `STD.RENDER_STATUS.RUNNING` | `RUNNING` | Running |
| `STD.RENDER_STATUS.SUCCEEDED` | `SUCCEEDED` | Succeeded |
| `STD.RENDER_STATUS.FAILED` | `FAILED` | Failed |
| `STD.RENDER_STATUS.CANCELLED` | `CANCELLED` | Cancelled |

---

## 24. State Seed Data

This section seeds all state machines defined in the governance model.

### 24.1 Source Document States

| Seed key | Code | Display name | Terminal |
|---|---|---|---:|
| `STD.STATE.SOURCE.UPLOADED` | `UPLOADED` | Uploaded | No |
| `STD.STATE.SOURCE.PROFILED` | `PROFILED` | Profiled | No |
| `STD.STATE.SOURCE.HASHED` | `HASHED` | Hashed | No |
| `STD.STATE.SOURCE.VERIFIED` | `VERIFIED` | Verified | No |
| `STD.STATE.SOURCE.REJECTED` | `REJECTED` | Rejected | Yes |
| `STD.STATE.SOURCE.SUPERSEDED` | `SUPERSEDED` | Superseded | Yes |
| `STD.STATE.SOURCE.ARCHIVED` | `ARCHIVED` | Archived | Yes |

### 24.2 Import Package States

| Seed key | Code | Display name | Terminal |
|---|---|---|---:|
| `STD.STATE.IMPORT.RECEIVED` | `RECEIVED` | Received | No |
| `STD.STATE.IMPORT.SCHEMA_VALIDATED` | `SCHEMA_VALIDATED` | Schema Validated | No |
| `STD.STATE.IMPORT.CONTENT_VALIDATED` | `CONTENT_VALIDATED` | Content Validated | No |
| `STD.STATE.IMPORT.REVIEW_REQUIRED` | `REVIEW_REQUIRED` | Review Required | No |
| `STD.STATE.IMPORT.ACCEPTED` | `ACCEPTED` | Accepted | No |
| `STD.STATE.IMPORT.REJECTED` | `REJECTED` | Rejected | Yes |
| `STD.STATE.IMPORT.IMPORTED` | `IMPORTED` | Imported | Yes |

### 24.3 STD Template Family States

| Seed key | Code | Display name | Terminal |
|---|---|---|---:|
| `STD.STATE.FAMILY.DRAFT` | `DRAFT` | Draft | No |
| `STD.STATE.FAMILY.ACTIVE` | `ACTIVE` | Active | No |
| `STD.STATE.FAMILY.SUSPENDED` | `SUSPENDED` | Suspended | No |
| `STD.STATE.FAMILY.ARCHIVED` | `ARCHIVED` | Archived | Yes |

### 24.4 STD Template Version States

| Seed key | Code | Display name | Terminal |
|---|---|---|---:|
| `STD.STATE.VERSION.DRAFT` | `DRAFT` | Draft | No |
| `STD.STATE.VERSION.STRUCTURING` | `STRUCTURING` | Structuring | No |
| `STD.STATE.VERSION.INTERNAL_REVIEW` | `INTERNAL_REVIEW` | Internal Review | No |
| `STD.STATE.VERSION.LEGAL_REVIEW` | `LEGAL_REVIEW` | Legal Review | No |
| `STD.STATE.VERSION.PROCUREMENT_REVIEW` | `PROCUREMENT_REVIEW` | Procurement Review | No |
| `STD.STATE.VERSION.TECHNICAL_REVIEW` | `TECHNICAL_REVIEW` | Technical Review | No |
| `STD.STATE.VERSION.APPROVED` | `APPROVED` | Approved | No |
| `STD.STATE.VERSION.ACTIVE` | `ACTIVE` | Active | No |
| `STD.STATE.VERSION.SUSPENDED` | `SUSPENDED` | Suspended | No |
| `STD.STATE.VERSION.SUPERSEDED` | `SUPERSEDED` | Superseded | Yes |
| `STD.STATE.VERSION.ARCHIVED` | `ARCHIVED` | Archived | Yes |
| `STD.STATE.VERSION.REJECTED` | `REJECTED` | Rejected | Yes |

### 24.5 Component States

| Seed key | Code | Display name | Terminal |
|---|---|---|---:|
| `STD.STATE.COMPONENT.DRAFT` | `DRAFT` | Draft | No |
| `STD.STATE.COMPONENT.NEEDS_REVIEW` | `NEEDS_REVIEW` | Needs Review | No |
| `STD.STATE.COMPONENT.REVIEWED` | `REVIEWED` | Reviewed | No |
| `STD.STATE.COMPONENT.APPROVED` | `APPROVED` | Approved | No |
| `STD.STATE.COMPONENT.REJECTED` | `REJECTED` | Rejected | Yes |
| `STD.STATE.COMPONENT.LOCKED` | `LOCKED` | Locked | No |
| `STD.STATE.COMPONENT.SUPERSEDED` | `SUPERSEDED` | Superseded | Yes |

### 24.6 Approval Request States

| Seed key | Code | Display name | Terminal |
|---|---|---|---:|
| `STD.STATE.APPROVAL.DRAFT` | `DRAFT` | Draft | No |
| `STD.STATE.APPROVAL.SUBMITTED` | `SUBMITTED` | Submitted | No |
| `STD.STATE.APPROVAL.IN_REVIEW` | `IN_REVIEW` | In Review | No |
| `STD.STATE.APPROVAL.CHANGES_REQUESTED` | `CHANGES_REQUESTED` | Changes Requested | No |
| `STD.STATE.APPROVAL.APPROVED` | `APPROVED` | Approved | Yes |
| `STD.STATE.APPROVAL.REJECTED` | `REJECTED` | Rejected | Yes |
| `STD.STATE.APPROVAL.CANCELLED` | `CANCELLED` | Cancelled | Yes |

### 24.7 Tender STD Instance States

| Seed key | Code | Display name | Terminal |
|---|---|---|---:|
| `STD.STATE.TENDER_INSTANCE.NOT_STARTED` | `NOT_STARTED` | Not Started | No |
| `STD.STATE.TENDER_INSTANCE.IN_CONFIGURATION` | `IN_CONFIGURATION` | In Configuration | No |
| `STD.STATE.TENDER_INSTANCE.VALIDATION_FAILED` | `VALIDATION_FAILED` | Validation Failed | No |
| `STD.STATE.TENDER_INSTANCE.READY_FOR_REVIEW` | `READY_FOR_REVIEW` | Ready for Review | No |
| `STD.STATE.TENDER_INSTANCE.PROCUREMENT_REVIEW` | `PROCUREMENT_REVIEW` | Procurement Review | No |
| `STD.STATE.TENDER_INSTANCE.APPROVED_FOR_PUBLICATION` | `APPROVED_FOR_PUBLICATION` | Approved for Publication | No |
| `STD.STATE.TENDER_INSTANCE.BOUND_TO_TENDER` | `BOUND_TO_TENDER` | Bound to Tender | No |
| `STD.STATE.TENDER_INSTANCE.PUBLISHED` | `PUBLISHED` | Published | No |
| `STD.STATE.TENDER_INSTANCE.ADDENDUM_REQUIRED` | `ADDENDUM_REQUIRED` | Addendum Required | No |
| `STD.STATE.TENDER_INSTANCE.SUPERSEDED_BY_ADDENDUM` | `SUPERSEDED_BY_ADDENDUM` | Superseded by Addendum | No |
| `STD.STATE.TENDER_INSTANCE.CANCELLED` | `CANCELLED` | Cancelled | Yes |
| `STD.STATE.TENDER_INSTANCE.ARCHIVED` | `ARCHIVED` | Archived | Yes |

### 24.8 Generated Bundle States

| Seed key | Code | Display name | Terminal |
|---|---|---|---:|
| `STD.STATE.BUNDLE.DRAFT` | `DRAFT` | Draft | No |
| `STD.STATE.BUNDLE.GENERATING` | `GENERATING` | Generating | No |
| `STD.STATE.BUNDLE.GENERATED` | `GENERATED` | Generated | No |
| `STD.STATE.BUNDLE.VALIDATED` | `VALIDATED` | Validated | No |
| `STD.STATE.BUNDLE.APPROVED` | `APPROVED` | Approved | No |
| `STD.STATE.BUNDLE.PUBLISHED` | `PUBLISHED` | Published | No |
| `STD.STATE.BUNDLE.SUPERSEDED_BY_ADDENDUM` | `SUPERSEDED_BY_ADDENDUM` | Superseded by Addendum | No |
| `STD.STATE.BUNDLE.ARCHIVED` | `ARCHIVED` | Archived | Yes |
| `STD.STATE.BUNDLE.FAILED` | `FAILED` | Failed | Yes |

### 24.9 Addendum Impact States

| Seed key | Code | Display name | Terminal |
|---|---|---|---:|
| `STD.STATE.ADDENDUM.DRAFT` | `DRAFT` | Draft | No |
| `STD.STATE.ADDENDUM.IMPACT_ANALYZED` | `IMPACT_ANALYZED` | Impact Analyzed | No |
| `STD.STATE.ADDENDUM.REVIEW_REQUIRED` | `REVIEW_REQUIRED` | Review Required | No |
| `STD.STATE.ADDENDUM.APPROVED` | `APPROVED` | Approved | No |
| `STD.STATE.ADDENDUM.PUBLISHED` | `PUBLISHED` | Published | No |
| `STD.STATE.ADDENDUM.REJECTED` | `REJECTED` | Rejected | Yes |
| `STD.STATE.ADDENDUM.CANCELLED` | `CANCELLED` | Cancelled | Yes |

### 24.10 Validation Finding States

| Seed key | Code | Display name | Terminal |
|---|---|---|---:|
| `STD.STATE.FINDING.OPEN` | `OPEN` | Open | No |
| `STD.STATE.FINDING.ACKNOWLEDGED` | `ACKNOWLEDGED` | Acknowledged | No |
| `STD.STATE.FINDING.RESOLVED` | `RESOLVED` | resolved | Yes |
| `STD.STATE.FINDING.OVERRIDDEN` | `OVERRIDDEN` | Overridden | Yes |
| `STD.STATE.FINDING.WAIVED` | `WAIVED` | Waived | Yes |

---

## 25. Transition Seed Data

### 25.1 Transition Columns

Each transition seed should include:

| Column | Description |
|---|---|
| `transition_key` | Stable seed key. |
| `state_machine` | State machine code. |
| `from_state` | Source state. |
| `to_state` | Target state. |
| `permission_required` | Required permission code. |
| `requires_reason` | Whether a comment/reason is mandatory. |
| `requires_validation_clearance` | Whether unresolved blockers prevent transition. |
| `requires_approval` | Whether a separate approval request must exist. |
| `segregation_guard` | Whether same-actor restriction applies. |
| `audit_event_type` | Audit event to emit. |

### 25.2 Critical Template Version Transitions

| Transition key | From | To | Permission | Guard |
|---|---|---|---|---|
| `STD.TRANSITION.VERSION.DRAFT_TO_STRUCTURING` | `DRAFT` | `STRUCTURING` | `STD_VERSION_EDIT` | Source document must exist. |
| `STD.TRANSITION.VERSION.STRUCTURING_TO_INTERNAL_REVIEW` | `STRUCTURING` | `INTERNAL_REVIEW` | `STD_VERSION_SUBMIT_REVIEW` | No unresolved schema blockers. |
| `STD.TRANSITION.VERSION.INTERNAL_TO_LEGAL_REVIEW` | `INTERNAL_REVIEW` | `LEGAL_REVIEW` | `STD_VERSION_ROUTE_REVIEW` | Internal review completed. |
| `STD.TRANSITION.VERSION.LEGAL_TO_PROCUREMENT_REVIEW` | `LEGAL_REVIEW` | `PROCUREMENT_REVIEW` | `STD_VERSION_ROUTE_REVIEW` | Legal review approved. |
| `STD.TRANSITION.VERSION.PROCUREMENT_TO_TECHNICAL_REVIEW` | `PROCUREMENT_REVIEW` | `TECHNICAL_REVIEW` | `STD_VERSION_ROUTE_REVIEW` | Procurement review approved. |
| `STD.TRANSITION.VERSION.TECHNICAL_TO_APPROVED` | `TECHNICAL_REVIEW` | `APPROVED` | `STD_VERSION_APPROVE` | Technical review approved. |
| `STD.TRANSITION.VERSION.APPROVED_TO_ACTIVE` | `APPROVED` | `ACTIVE` | `STD_VERSION_ACTIVATE` | Approval complete; source verified; package hash stable; SoD satisfied. |
| `STD.TRANSITION.VERSION.ACTIVE_TO_SUSPENDED` | `ACTIVE` | `SUSPENDED` | `STD_VERSION_SUSPEND` | Reason required. |
| `STD.TRANSITION.VERSION.ACTIVE_TO_SUPERSEDED` | `ACTIVE` | `SUPERSEDED` | `STD_VERSION_SUPERSEDE` | Replacement version required unless emergency retirement. |
| `STD.TRANSITION.VERSION.SUPERSEDED_TO_ARCHIVED` | `SUPERSEDED` | `ARCHIVED` | `STD_VERSION_ARCHIVE` | No open tender dependency requiring active visibility. |
| `STD.TRANSITION.VERSION.ANY_TO_REJECTED` | `DRAFT/STRUCTURING/REVIEW` | `REJECTED` | `STD_VERSION_REJECT` | Reason required. |

### 25.3 Critical Tender Instance Transitions

| Transition key | From | To | Permission | Guard |
|---|---|---|---|---|
| `STD.TRANSITION.TENDER.NOT_STARTED_TO_IN_CONFIGURATION` | `NOT_STARTED` | `IN_CONFIGURATION` | `TENDER_STD_CONFIGURE` | Active STD version selected. |
| `STD.TRANSITION.TENDER.IN_CONFIGURATION_TO_VALIDATION_FAILED` | `IN_CONFIGURATION` | `VALIDATION_FAILED` | `SYSTEM_VALIDATE` | Blocker found. |
| `STD.TRANSITION.TENDER.IN_CONFIGURATION_TO_READY_FOR_REVIEW` | `IN_CONFIGURATION` | `READY_FOR_REVIEW` | `TENDER_STD_SUBMIT_REVIEW` | All mandatory fields complete; no publication blockers. |
| `STD.TRANSITION.TENDER.READY_TO_PROCUREMENT_REVIEW` | `READY_FOR_REVIEW` | `PROCUREMENT_REVIEW` | `TENDER_STD_REVIEW` | Reviewer assigned. |
| `STD.TRANSITION.TENDER.REVIEW_TO_APPROVED_FOR_PUBLICATION` | `PROCUREMENT_REVIEW` | `APPROVED_FOR_PUBLICATION` | `TENDER_STD_APPROVE_PUBLICATION` | SoD satisfied; validation clean. |
| `STD.TRANSITION.TENDER.APPROVED_TO_BOUND` | `APPROVED_FOR_PUBLICATION` | `BOUND_TO_TENDER` | `SYSTEM_BIND_STD` | Binding hash created. |
| `STD.TRANSITION.TENDER.BOUND_TO_PUBLISHED` | `BOUND_TO_TENDER` | `PUBLISHED` | `TENDER_PUBLISH` | Generated bundle approved and hashed. |
| `STD.TRANSITION.TENDER.PUBLISHED_TO_ADDENDUM_REQUIRED` | `PUBLISHED` | `ADDENDUM_REQUIRED` | `TENDER_ADDENDUM_INITIATE` | Reason required. |
| `STD.TRANSITION.TENDER.ADDENDUM_TO_SUPERSEDED` | `ADDENDUM_REQUIRED` | `SUPERSEDED_BY_ADDENDUM` | `TENDER_ADDENDUM_PUBLISH` | Approved addendum exists. |

### 25.4 Critical Bundle Transitions

| Transition key | From | To | Permission | Guard |
|---|---|---|---|---|
| `STD.TRANSITION.BUNDLE.DRAFT_TO_GENERATING` | `DRAFT` | `GENERATING` | `GENERATED_BUNDLE_RENDER` | Tender instance valid. |
| `STD.TRANSITION.BUNDLE.GENERATING_TO_GENERATED` | `GENERATING` | `GENERATED` | `SYSTEM_RENDER_COMPLETE` | Render job succeeded. |
| `STD.TRANSITION.BUNDLE.GENERATED_TO_VALIDATED` | `GENERATED` | `VALIDATED` | `GENERATED_BUNDLE_VALIDATE` | Render hash present; required sections present. |
| `STD.TRANSITION.BUNDLE.VALIDATED_TO_APPROVED` | `VALIDATED` | `APPROVED` | `GENERATED_BUNDLE_APPROVE` | Reviewer approval. |
| `STD.TRANSITION.BUNDLE.APPROVED_TO_PUBLISHED` | `APPROVED` | `PUBLISHED` | `GENERATED_BUNDLE_PUBLISH` | Tender publication allowed. |
| `STD.TRANSITION.BUNDLE.PUBLISHED_TO_SUPERSEDED` | `PUBLISHED` | `SUPERSEDED_BY_ADDENDUM` | `TENDER_ADDENDUM_PUBLISH` | Addendum bundle published. |

---

## 26. Role Seed Data

### 26.1 System Roles

| Seed key | Role code | Display name | Description |
|---|---|---|---|
| `STD.ROLE.SYSTEM_ADMIN` | `SYSTEM_ADMIN` | System Administrator | Platform administration; not automatically legal/procurement approver. |
| `STD.ROLE.STD_TEMPLATE_ADMIN` | `STD_TEMPLATE_ADMIN` | STD Template Administrator | Creates and structures STD families, versions, components, schemas, and packages. |
| `STD.ROLE.STD_IMPORTER` | `STD_IMPORTER` | STD Importer | Uploads and imports source/package content. |
| `STD.ROLE.STD_LEGAL_REVIEWER` | `STD_LEGAL_REVIEWER` | STD Legal Reviewer | Reviews locked legal text, legal basis, and immutable sections. |
| `STD.ROLE.STD_PROCUREMENT_REVIEWER` | `STD_PROCUREMENT_REVIEWER` | STD Procurement Reviewer | Reviews procurement procedure, evaluation, qualification, and compliance. |
| `STD.ROLE.STD_TECHNICAL_REVIEWER` | `STD_TECHNICAL_REVIEWER` | STD Technical Reviewer | Reviews requirement schemas, technical forms, price models, render logic, and package quality. |
| `STD.ROLE.STD_APPROVER` | `STD_APPROVER` | STD Approver | Approves template version for activation after required reviews. |
| `STD.ROLE.STD_ACTIVATOR` | `STD_ACTIVATOR` | STD Activator | Activates approved STD versions. |
| `STD.ROLE.PE_PROCUREMENT_OFFICER` | `PE_PROCUREMENT_OFFICER` | Procuring Entity Procurement Officer | Configures tender-specific STD values. |
| `STD.ROLE.PE_PROCUREMENT_REVIEWER` | `PE_PROCUREMENT_REVIEWER` | Procuring Entity Procurement Reviewer | Reviews tender STD configuration. |
| `STD.ROLE.PE_PROCUREMENT_APPROVER` | `PE_PROCUREMENT_APPROVER` | Procuring Entity Procurement Approver | Approves configured tender bundle for publication. |
| `STD.ROLE.PE_TECHNICAL_AUTHOR` | `PE_TECHNICAL_AUTHOR` | Procuring Entity Technical Author | Authors technical requirements within controlled composer. |
| `STD.ROLE.PE_TECHNICAL_REVIEWER` | `PE_TECHNICAL_REVIEWER` | Procuring Entity Technical Reviewer | Reviews PE-authored requirements. |
| `STD.ROLE.TENDER_PUBLISHER` | `TENDER_PUBLISHER` | Tender Publisher | Publishes approved generated tender bundles. |
| `STD.ROLE.ADDENDUM_MANAGER` | `ADDENDUM_MANAGER` | Addendum Manager | Initiates and manages post-publication addenda. |
| `STD.ROLE.EVALUATOR` | `EVALUATOR` | Evaluator | Uses STD-generated evaluation structures. |
| `STD.ROLE.CONTRACT_OFFICER` | `CONTRACT_OFFICER` | Contract Officer | Uses STD-generated contract forms and appendices. |
| `STD.ROLE.AUDITOR` | `AUDITOR` | Auditor | Read-only access to versions, bundles, approvals, hashes, and audit logs. |
| `STD.ROLE.READ_ONLY` | `READ_ONLY` | Read Only | Read-only operational access. |

### 26.2 Role Assignment Rules

1. `STD_APPROVER` and `STD_ACTIVATOR` should be separate users in production.
2. `STD_TEMPLATE_ADMIN` may prepare a version but must not solely approve it.
3. `PE_PROCUREMENT_OFFICER` may configure tender data but must not solely approve publication.
4. `SYSTEM_ADMIN` must not bypass legal/procurement approval workflows by default.
5. Emergency override roles, if later introduced, must require separate audit and reason controls.

---

## 27. Permission Seed Data

### 27.1 Source and Package Permissions

| Seed key | Permission code | Description |
|---|---|---|
| `STD.PERMISSION.SOURCE_UPLOAD` | `SOURCE_UPLOAD` | Upload STD source document. |
| `STD.PERMISSION.SOURCE_PROFILE` | `SOURCE_PROFILE` | Edit source metadata/profile. |
| `STD.PERMISSION.SOURCE_VERIFY` | `SOURCE_VERIFY` | Verify source document. |
| `STD.PERMISSION.SOURCE_REJECT` | `SOURCE_REJECT` | Reject source document. |
| `STD.PERMISSION.IMPORT_PACKAGE_UPLOAD` | `IMPORT_PACKAGE_UPLOAD` | Upload import package. |
| `STD.PERMISSION.IMPORT_PACKAGE_VALIDATE` | `IMPORT_PACKAGE_VALIDATE` | Validate import package. |
| `STD.PERMISSION.IMPORT_PACKAGE_ACCEPT` | `IMPORT_PACKAGE_ACCEPT` | Accept package for import. |
| `STD.PERMISSION.IMPORT_PACKAGE_REJECT` | `IMPORT_PACKAGE_REJECT` | Reject import package. |
| `STD.PERMISSION.EXPORT_PACKAGE_CREATE` | `EXPORT_PACKAGE_CREATE` | Export STD version package. |

### 27.2 Template Administration Permissions

| Seed key | Permission code | Description |
|---|---|---|
| `STD.PERMISSION.STD_FAMILY_CREATE` | `STD_FAMILY_CREATE` | Create STD family. |
| `STD.PERMISSION.STD_FAMILY_EDIT` | `STD_FAMILY_EDIT` | Edit STD family metadata. |
| `STD.PERMISSION.STD_VERSION_CREATE` | `STD_VERSION_CREATE` | Create STD template version. |
| `STD.PERMISSION.STD_VERSION_EDIT` | `STD_VERSION_EDIT` | Edit draft/structuring version. |
| `STD.PERMISSION.STD_VERSION_SUBMIT_REVIEW` | `STD_VERSION_SUBMIT_REVIEW` | Submit version for review. |
| `STD.PERMISSION.STD_VERSION_ROUTE_REVIEW` | `STD_VERSION_ROUTE_REVIEW` | Route version between review tracks. |
| `STD.PERMISSION.STD_VERSION_APPROVE` | `STD_VERSION_APPROVE` | Approve STD version. |
| `STD.PERMISSION.STD_VERSION_REJECT` | `STD_VERSION_REJECT` | Reject STD version. |
| `STD.PERMISSION.STD_VERSION_ACTIVATE` | `STD_VERSION_ACTIVATE` | Activate approved STD version. |
| `STD.PERMISSION.STD_VERSION_SUSPEND` | `STD_VERSION_SUSPEND` | Suspend active STD version. |
| `STD.PERMISSION.STD_VERSION_SUPERSEDE` | `STD_VERSION_SUPERSEDE` | Supersede active STD version. |
| `STD.PERMISSION.STD_VERSION_ARCHIVE` | `STD_VERSION_ARCHIVE` | Archive superseded or unused version. |
| `STD.PERMISSION.STD_COMPONENT_EDIT` | `STD_COMPONENT_EDIT` | Edit STD components in editable states. |
| `STD.PERMISSION.STD_RULE_EDIT` | `STD_RULE_EDIT` | Edit STD rules in editable states. |
| `STD.PERMISSION.STD_FORM_SCHEMA_EDIT` | `STD_FORM_SCHEMA_EDIT` | Edit form schemas in editable states. |
| `STD.PERMISSION.STD_RENDER_BLOCK_EDIT` | `STD_RENDER_BLOCK_EDIT` | Edit render blocks in editable states. |

### 27.3 Tender Configuration Permissions

| Seed key | Permission code | Description |
|---|---|---|
| `STD.PERMISSION.TENDER_STD_CONFIGURE` | `TENDER_STD_CONFIGURE` | Configure tender-specific STD values. |
| `STD.PERMISSION.TENDER_STD_SUBMIT_REVIEW` | `TENDER_STD_SUBMIT_REVIEW` | Submit configured STD instance for review. |
| `STD.PERMISSION.TENDER_STD_REVIEW` | `TENDER_STD_REVIEW` | Review configured tender STD instance. |
| `STD.PERMISSION.TENDER_STD_APPROVE_PUBLICATION` | `TENDER_STD_APPROVE_PUBLICATION` | Approve configured tender bundle for publication. |
| `STD.PERMISSION.TENDER_PUBLISH` | `TENDER_PUBLISH` | Publish approved tender bundle. |
| `STD.PERMISSION.TENDER_ADDENDUM_INITIATE` | `TENDER_ADDENDUM_INITIATE` | Initiate addendum process. |
| `STD.PERMISSION.TENDER_ADDENDUM_ANALYZE` | `TENDER_ADDENDUM_ANALYZE` | Analyze addendum impact. |
| `STD.PERMISSION.TENDER_ADDENDUM_APPROVE` | `TENDER_ADDENDUM_APPROVE` | Approve addendum. |
| `STD.PERMISSION.TENDER_ADDENDUM_PUBLISH` | `TENDER_ADDENDUM_PUBLISH` | Publish addendum. |

### 27.4 Generated Bundle and Validation Permissions

| Seed key | Permission code | Description |
|---|---|---|
| `STD.PERMISSION.GENERATED_BUNDLE_RENDER` | `GENERATED_BUNDLE_RENDER` | Generate tender or contract bundle. |
| `STD.PERMISSION.GENERATED_BUNDLE_VALIDATE` | `GENERATED_BUNDLE_VALIDATE` | Validate generated bundle. |
| `STD.PERMISSION.GENERATED_BUNDLE_APPROVE` | `GENERATED_BUNDLE_APPROVE` | Approve generated bundle. |
| `STD.PERMISSION.GENERATED_BUNDLE_PUBLISH` | `GENERATED_BUNDLE_PUBLISH` | Publish generated bundle. |
| `STD.PERMISSION.VALIDATION_FINDING_VIEW` | `VALIDATION_FINDING_VIEW` | View validation findings. |
| `STD.PERMISSION.VALIDATION_FINDING_RESOLVE` | `VALIDATION_FINDING_RESOLVE` | Resolve validation finding. |
| `STD.PERMISSION.VALIDATION_FINDING_OVERRIDE` | `VALIDATION_FINDING_OVERRIDE` | Override validation finding where allowed. |

### 27.5 Audit and Read Permissions

| Seed key | Permission code | Description |
|---|---|---|
| `STD.PERMISSION.STD_READ` | `STD_READ` | Read STD template records. |
| `STD.PERMISSION.TENDER_STD_READ` | `TENDER_STD_READ` | Read tender STD records. |
| `STD.PERMISSION.GENERATED_BUNDLE_READ` | `GENERATED_BUNDLE_READ` | Read generated bundle metadata and output. |
| `STD.PERMISSION.AUDIT_LOG_READ` | `AUDIT_LOG_READ` | Read audit logs. |
| `STD.PERMISSION.HASH_VERIFY` | `HASH_VERIFY` | Verify hashes and integrity records. |

---

## 28. Role Permission Matrix Seed

### 28.1 Summary Matrix

| Role | Key permissions |
|---|---|
| `SYSTEM_ADMIN` | System-level read, seed management, user-role assignment, technical recovery. No default legal approval authority. |
| `STD_TEMPLATE_ADMIN` | `STD_FAMILY_CREATE`, `STD_VERSION_CREATE`, `STD_VERSION_EDIT`, `STD_COMPONENT_EDIT`, `STD_RULE_EDIT`, `STD_FORM_SCHEMA_EDIT`, `STD_RENDER_BLOCK_EDIT`, `STD_VERSION_SUBMIT_REVIEW`, `STD_READ`. |
| `STD_IMPORTER` | `SOURCE_UPLOAD`, `SOURCE_PROFILE`, `IMPORT_PACKAGE_UPLOAD`, `IMPORT_PACKAGE_VALIDATE`, `STD_READ`. |
| `STD_LEGAL_REVIEWER` | `STD_READ`, `STD_VERSION_ROUTE_REVIEW`, legal approval task permissions, `AUDIT_LOG_READ`. |
| `STD_PROCUREMENT_REVIEWER` | `STD_READ`, procurement review task permissions, `AUDIT_LOG_READ`. |
| `STD_TECHNICAL_REVIEWER` | `STD_READ`, technical review task permissions, `AUDIT_LOG_READ`, package/schema validation permissions. |
| `STD_APPROVER` | `STD_READ`, `STD_VERSION_APPROVE`, `STD_VERSION_REJECT`, `AUDIT_LOG_READ`. |
| `STD_ACTIVATOR` | `STD_READ`, `STD_VERSION_ACTIVATE`, `STD_VERSION_SUSPEND`, `STD_VERSION_SUPERSEDE`, `STD_VERSION_ARCHIVE`, `HASH_VERIFY`. |
| `PE_PROCUREMENT_OFFICER` | `TENDER_STD_CONFIGURE`, `TENDER_STD_SUBMIT_REVIEW`, `GENERATED_BUNDLE_RENDER`, `VALIDATION_FINDING_VIEW`, `TENDER_STD_READ`. |
| `PE_PROCUREMENT_REVIEWER` | `TENDER_STD_REVIEW`, `VALIDATION_FINDING_VIEW`, `VALIDATION_FINDING_RESOLVE`, `TENDER_STD_READ`. |
| `PE_PROCUREMENT_APPROVER` | `TENDER_STD_APPROVE_PUBLICATION`, `GENERATED_BUNDLE_APPROVE`, `TENDER_STD_READ`, `AUDIT_LOG_READ`. |
| `PE_TECHNICAL_AUTHOR` | Requirement composer authoring permissions within tender configuration. |
| `PE_TECHNICAL_REVIEWER` | Requirement review and validation finding resolution permissions. |
| `TENDER_PUBLISHER` | `TENDER_PUBLISH`, `GENERATED_BUNDLE_PUBLISH`, `GENERATED_BUNDLE_READ`. |
| `ADDENDUM_MANAGER` | `TENDER_ADDENDUM_INITIATE`, `TENDER_ADDENDUM_ANALYZE`, `TENDER_ADDENDUM_APPROVE`, `TENDER_ADDENDUM_PUBLISH`. |
| `EVALUATOR` | Read published tender STD structures and complete evaluator-scoped structures. |
| `CONTRACT_OFFICER` | Generate/read contract formation outputs and appendices. |
| `AUDITOR` | `STD_READ`, `TENDER_STD_READ`, `GENERATED_BUNDLE_READ`, `AUDIT_LOG_READ`, `HASH_VERIFY`. |
| `READ_ONLY` | Read-only permissions only. |

### 28.2 Mandatory Deny Rules

| Deny rule | Applies to | Description |
|---|---|---|
| `DENY_ACTIVE_TEMPLATE_EDIT` | All roles | Active STD version components cannot be edited. |
| `DENY_PUBLISHED_BUNDLE_EDIT` | All roles | Published generated bundles cannot be edited. |
| `DENY_SELF_SOLE_APPROVAL` | Review/approval roles | Same actor cannot be sole preparer and final approver on same object. |
| `DENY_UNVERIFIED_SOURCE_ACTIVATION` | Activator | STD version cannot activate without verified source. |
| `DENY_PLACEHOLDER_FAMILY_TENDER_USE` | Tender users | Placeholder families cannot be used for tender configuration. |
| `DENY_UNHASHED_PUBLICATION` | Publisher | Generated bundle cannot publish without content hash. |

---

## 29. Approval Track Seed Data

### 29.1 STD Template Version Approval Tracks

| Seed key | Code | Display name | Required for activation | Minimum approver role |
|---|---|---|---:|---|
| `STD.APPROVAL_TRACK.INTERNAL` | `INTERNAL` | Internal Review | Yes | `STD_TEMPLATE_ADMIN` or separate internal reviewer |
| `STD.APPROVAL_TRACK.LEGAL` | `LEGAL` | Legal Review | Yes | `STD_LEGAL_REVIEWER` |
| `STD.APPROVAL_TRACK.PROCUREMENT` | `PROCUREMENT` | Procurement Standards Review | Yes | `STD_PROCUREMENT_REVIEWER` |
| `STD.APPROVAL_TRACK.TECHNICAL` | `TECHNICAL` | Technical/Schema Review | Yes | `STD_TECHNICAL_REVIEWER` |
| `STD.APPROVAL_TRACK.FINAL` | `FINAL` | Final Approval | Yes | `STD_APPROVER` |

### 29.2 Tender Configuration Approval Tracks

| Seed key | Code | Display name | Required for publication | Minimum approver role |
|---|---|---|---:|---|
| `STD.APPROVAL_TRACK.TENDER_PROCUREMENT` | `TENDER_PROCUREMENT` | Tender Procurement Review | Yes | `PE_PROCUREMENT_REVIEWER` |
| `STD.APPROVAL_TRACK.TENDER_TECHNICAL` | `TENDER_TECHNICAL` | Tender Technical Requirements Review | Conditional | `PE_TECHNICAL_REVIEWER` |
| `STD.APPROVAL_TRACK.TENDER_FINAL` | `TENDER_FINAL` | Tender Final Approval | Yes | `PE_PROCUREMENT_APPROVER` |
| `STD.APPROVAL_TRACK.ADDENDUM` | `ADDENDUM` | Addendum Approval | Conditional | `ADDENDUM_MANAGER` / approver role |

---

## 30. Audit Event Type Seed Data

### 30.1 Source and Package Events

| Seed key | Code | Description |
|---|---|---|
| `STD.AUDIT.SOURCE_UPLOADED` | `SOURCE_UPLOADED` | Source document uploaded. |
| `STD.AUDIT.SOURCE_HASHED` | `SOURCE_HASHED` | Source document hash generated. |
| `STD.AUDIT.SOURCE_VERIFIED` | `SOURCE_VERIFIED` | Source document verified. |
| `STD.AUDIT.SOURCE_REJECTED` | `SOURCE_REJECTED` | Source document rejected. |
| `STD.AUDIT.IMPORT_PACKAGE_UPLOADED` | `IMPORT_PACKAGE_UPLOADED` | Import package uploaded. |
| `STD.AUDIT.IMPORT_PACKAGE_VALIDATED` | `IMPORT_PACKAGE_VALIDATED` | Import package validated. |
| `STD.AUDIT.IMPORT_PACKAGE_ACCEPTED` | `IMPORT_PACKAGE_ACCEPTED` | Import package accepted. |
| `STD.AUDIT.IMPORT_PACKAGE_REJECTED` | `IMPORT_PACKAGE_REJECTED` | Import package rejected. |
| `STD.AUDIT.IMPORT_PACKAGE_IMPORTED` | `IMPORT_PACKAGE_IMPORTED` | Import package imported. |

### 30.2 Template Governance Events

| Seed key | Code | Description |
|---|---|---|
| `STD.AUDIT.STD_FAMILY_CREATED` | `STD_FAMILY_CREATED` | STD family created. |
| `STD.AUDIT.STD_VERSION_CREATED` | `STD_VERSION_CREATED` | STD version created. |
| `STD.AUDIT.STD_COMPONENT_CREATED` | `STD_COMPONENT_CREATED` | STD component created. |
| `STD.AUDIT.STD_COMPONENT_UPDATED` | `STD_COMPONENT_UPDATED` | STD component updated. |
| `STD.AUDIT.STD_RULE_UPDATED` | `STD_RULE_UPDATED` | STD rule updated. |
| `STD.AUDIT.STD_FORM_SCHEMA_UPDATED` | `STD_FORM_SCHEMA_UPDATED` | STD form schema updated. |
| `STD.AUDIT.STD_RENDER_BLOCK_UPDATED` | `STD_RENDER_BLOCK_UPDATED` | STD render block updated. |
| `STD.AUDIT.STD_VERSION_SUBMITTED_FOR_REVIEW` | `STD_VERSION_SUBMITTED_FOR_REVIEW` | STD version submitted for review. |
| `STD.AUDIT.STD_VERSION_REVIEWED` | `STD_VERSION_REVIEWED` | STD version reviewed. |
| `STD.AUDIT.STD_VERSION_APPROVED` | `STD_VERSION_APPROVED` | STD version approved. |
| `STD.AUDIT.STD_VERSION_REJECTED` | `STD_VERSION_REJECTED` | STD version rejected. |
| `STD.AUDIT.STD_VERSION_ACTIVATED` | `STD_VERSION_ACTIVATED` | STD version activated. |
| `STD.AUDIT.STD_VERSION_SUSPENDED` | `STD_VERSION_SUSPENDED` | STD version suspended. |
| `STD.AUDIT.STD_VERSION_SUPERSEDED` | `STD_VERSION_SUPERSEDED` | STD version superseded. |
| `STD.AUDIT.STD_VERSION_ARCHIVED` | `STD_VERSION_ARCHIVED` | STD version archived. |

### 30.3 Tender Configuration and Publication Events

| Seed key | Code | Description |
|---|---|---|
| `STD.AUDIT.TENDER_STD_INSTANCE_CREATED` | `TENDER_STD_INSTANCE_CREATED` | Tender STD instance created. |
| `STD.AUDIT.TENDER_STD_BOUND` | `TENDER_STD_BOUND` | Tender bound to STD version. |
| `STD.AUDIT.TENDER_CONFIG_VALUE_SET` | `TENDER_CONFIG_VALUE_SET` | Tender STD configuration value set. |
| `STD.AUDIT.TENDER_CONFIG_VALIDATED` | `TENDER_CONFIG_VALIDATED` | Tender STD configuration validated. |
| `STD.AUDIT.TENDER_CONFIG_SUBMITTED_REVIEW` | `TENDER_CONFIG_SUBMITTED_REVIEW` | Tender STD configuration submitted for review. |
| `STD.AUDIT.TENDER_CONFIG_APPROVED` | `TENDER_CONFIG_APPROVED` | Tender STD configuration approved. |
| `STD.AUDIT.GENERATED_BUNDLE_RENDERED` | `GENERATED_BUNDLE_RENDERED` | Generated bundle rendered. |
| `STD.AUDIT.GENERATED_BUNDLE_HASHED` | `GENERATED_BUNDLE_HASHED` | Generated bundle hash created. |
| `STD.AUDIT.GENERATED_BUNDLE_APPROVED` | `GENERATED_BUNDLE_APPROVED` | Generated bundle approved. |
| `STD.AUDIT.GENERATED_BUNDLE_PUBLISHED` | `GENERATED_BUNDLE_PUBLISHED` | Generated bundle published. |
| `STD.AUDIT.ADDENDUM_INITIATED` | `ADDENDUM_INITIATED` | Addendum initiated. |
| `STD.AUDIT.ADDENDUM_IMPACT_ANALYZED` | `ADDENDUM_IMPACT_ANALYZED` | Addendum impact analysis completed. |
| `STD.AUDIT.ADDENDUM_APPROVED` | `ADDENDUM_APPROVED` | Addendum approved. |
| `STD.AUDIT.ADDENDUM_PUBLISHED` | `ADDENDUM_PUBLISHED` | Addendum published. |

### 30.4 Integrity and Override Events

| Seed key | Code | Description |
|---|---|---|
| `STD.AUDIT.HASH_VERIFIED` | `HASH_VERIFIED` | Hash verification performed. |
| `STD.AUDIT.VALIDATION_FINDING_OPENED` | `VALIDATION_FINDING_OPENED` | Validation finding opened. |
| `STD.AUDIT.VALIDATION_FINDING_RESOLVED` | `VALIDATION_FINDING_RESOLVED` | Validation finding resolved. |
| `STD.AUDIT.VALIDATION_FINDING_OVERRIDDEN` | `VALIDATION_FINDING_OVERRIDDEN` | Validation finding overridden. |
| `STD.AUDIT.PERMISSION_DENIED` | `PERMISSION_DENIED` | Permission denied event. |
| `STD.AUDIT.EMERGENCY_OVERRIDE_USED` | `EMERGENCY_OVERRIDE_USED` | Emergency override used. |

---

## 31. Import Package Manifest Seed Contract

### 31.1 Required Manifest Keys

Every STD import package must contain a manifest with these keys:

```json
{
  "package_id": "string",
  "package_version": "string",
  "std_family_code": "string",
  "std_version_code": "string",
  "source_authority_code": "string",
  "source_document_hash": "string",
  "package_hash": "string",
  "schema_version": "string",
  "created_at": "datetime",
  "created_by": "string",
  "modules": [
    "sections",
    "clauses",
    "parameters",
    "rules",
    "forms",
    "render_blocks"
  ]
}
```

### 31.2 Required Package Modules

| Module | Required for production activation | Description |
|---|---:|---|
| `manifest` | Yes | Package identity and hashes. |
| `source_trace` | Yes | Source page/section/anchor/hash references. |
| `sections` | Yes | Section hierarchy. |
| `clauses` | Yes | Clause records and text fragments. |
| `parameters` | Yes | Configurable fields. |
| `rules` | Yes | Validation and activation rules. |
| `forms` | Yes | Form schemas. |
| `form_fields` | Yes | Field-level form schema. |
| `evidence_requirements` | Yes | Required evidence/documents. |
| `price_schedule_schema` | Conditional | Required where STD includes pricing schedules. |
| `requirements_schema` | Conditional | Required where STD includes PE requirements. |
| `evaluation_schema` | Yes | Evaluation and qualification model. |
| `contract_schema` | Conditional | Required where STD generates contract forms. |
| `render_blocks` | Yes | Deterministic rendering rules. |
| `smoke_tests` | Yes | Package-level tests. |

### 31.3 Package Activation Rule

No STD package may be activated unless:

1. Manifest is valid.
2. Package hash is stable.
3. Source document hash exists.
4. Source trace is complete for locked clauses.
5. Required modules exist.
6. All blocker-level package smoke tests pass.
7. Required approvals are completed.

---

## 32. Minimum Smoke Test Fixture Package

A minimal smoke fixture must be seeded for automated tests.

### 32.1 Fixture Family

| Field | Value |
|---|---|
| Family code | `SMOKE-STD` |
| Version code | `SMOKE-STD-001` |
| Source authority | `SYSTEM` |
| Source type | `IMPORT_PACKAGE` |
| Status | Draft until test activation |

### 32.2 Fixture Sections

| Section code | Section type | Mutability |
|---|---|---|
| `SMOKE.COVER` | `COVER` | `PARAMETERIZED` |
| `SMOKE.ITT` | `ITT` | `LOCKED` |
| `SMOKE.TDS` | `TDS` | `CONFIGURABLE` |
| `SMOKE.FORMS` | `FORMS` | `BIDDER_COMPLETED` |
| `SMOKE.GCC` | `GCC` | `LOCKED` |
| `SMOKE.SCC` | `SCC` | `CONFIGURABLE` |

### 32.3 Fixture Parameters

| Parameter code | Type | Required | Stage |
|---|---|---:|---|
| `PE_NAME` | `TEXT` | Yes | `TENDER_CONFIGURATION` |
| `TENDER_NAME` | `TEXT` | Yes | `TENDER_CONFIGURATION` |
| `SUBMISSION_DEADLINE` | `DATETIME` | Yes | `TENDER_CONFIGURATION` |
| `OPENING_DATETIME` | `DATETIME` | Yes | `TENDER_CONFIGURATION` |
| `TENDER_VALIDITY_DAYS` | `INTEGER` | Yes | `TENDER_CONFIGURATION` |
| `TENDER_SECURITY_REQUIRED` | `BOOLEAN` | Yes | `TENDER_CONFIGURATION` |
| `TENDER_SECURITY_AMOUNT` | `MONEY` | Conditional | `TENDER_CONFIGURATION` |

### 32.4 Fixture Rules

| Rule code | Type | Severity | Blocking behavior | Description |
|---|---|---|---|---|
| `SMOKE.RULE.REQUIRED_PE_NAME` | `VALIDATION` | `BLOCKER` | `BLOCKS_PUBLICATION` | PE name must be present. |
| `SMOKE.RULE.OPENING_AFTER_DEADLINE` | `VALIDATION` | `BLOCKER` | `BLOCKS_PUBLICATION` | Opening datetime must not be before submission deadline. |
| `SMOKE.RULE.SECURITY_AMOUNT_REQUIRED_IF_SECURITY_REQUIRED` | `ACTIVATION` / `VALIDATION` | `BLOCKER` | `BLOCKS_PUBLICATION` | Security amount required if security is required. |
| `SMOKE.RULE.ACTIVE_VERSION_IMMUTABLE` | `GOVERNANCE` | `BLOCKER` | `BLOCKS_SAVE` | Active STD version cannot be edited. |

---

# 33. Smoke Contracts

Each smoke contract below is written as an implementation acceptance test. The system should eventually automate these as backend tests, service tests, and end-to-end workflow tests.

---

## SC-001: Seed Data Idempotency

### Purpose

Verify that seed data can be safely re-run without creating duplicates.

### Setup

1. Run seed script once.
2. Capture counts for seed tables.
3. Run seed script again.

### Expected Result

1. No duplicate seed records are created.
2. Records are matched by `seed_key`.
3. Changed descriptions or labels update existing records only when allowed.
4. Previously used seed records are not deleted.

### Blocking Severity

`BLOCKER`

---

## SC-002: Source Document Must Be Hashed Before Verification

### Purpose

Verify source integrity controls.

### Setup

1. Upload a source document record.
2. Attempt to transition it directly from `UPLOADED` to `VERIFIED` without hash.

### Expected Result

1. Transition is rejected.
2. Validation finding is opened.
3. Audit event records the blocked attempt.
4. Source remains in `UPLOADED` or `PROFILED` state.

### Blocking Severity

`BLOCKER`

---

## SC-003: Import Package Requires Valid Manifest

### Purpose

Verify import package schema validation.

### Setup

1. Upload an import package without `source_document_hash` or `package_hash`.
2. Run package validation.

### Expected Result

1. Package does not reach `SCHEMA_VALIDATED`.
2. Missing manifest fields are returned as validation findings.
3. Package cannot be accepted or imported.

### Blocking Severity

`BLOCKER`

---

## SC-004: Template Version Cannot Activate Without Verified Source

### Purpose

Protect legal/source traceability.

### Setup

1. Create STD family.
2. Create STD version.
3. Attach unverified source document.
4. Complete version review artificially or through test approvals.
5. Attempt activation.

### Expected Result

1. Activation is blocked.
2. Finding states that source document must be verified.
3. STD version remains in `APPROVED` or pre-active state.
4. Audit event records denied activation attempt.

### Blocking Severity

`BLOCKER`

---

## SC-005: Template Version Requires Required Approval Tracks

### Purpose

Ensure governance review completeness.

### Setup

1. Create a template version.
2. Complete internal review only.
3. Attempt final approval or activation.

### Expected Result

1. Approval or activation is blocked.
2. Missing legal/procurement/technical/final tracks are reported.
3. No active version is created.

### Blocking Severity

`BLOCKER`

---

## SC-006: Segregation of Duties Blocks Self Sole Approval

### Purpose

Prevent author from being sole approver.

### Setup

1. User A creates or imports a template version.
2. User A attempts to be the only final approver.

### Expected Result

1. Approval is blocked unless an explicit emergency override path exists.
2. Audit event records the denied approval.
3. Approval request remains in review state.

### Blocking Severity

`BLOCKER`

---

## SC-007: Active STD Version Is Immutable

### Purpose

Ensure master template immutability.

### Setup

1. Activate `SMOKE-STD-001` or test STD version.
2. Attempt to edit a locked clause, parameter definition, form schema, rule, or render block.

### Expected Result

1. Edit is rejected.
2. Record remains unchanged.
3. Audit event records denied mutation.
4. User is instructed to create a new draft version.

### Blocking Severity

`BLOCKER`

---

## SC-008: Active Version Can Be Used for Tender Configuration

### Purpose

Verify tender binding to active STD version.

### Setup

1. Activate a fixture STD version.
2. Create tender STD instance selecting that version.

### Expected Result

1. Tender STD instance is created.
2. Bound STD version ID is stored.
3. Initial state is `IN_CONFIGURATION` or equivalent configured start state.
4. Binding audit event is emitted.

### Blocking Severity

`BLOCKER`

---

## SC-009: Inactive or Placeholder Family Cannot Be Used for Tender

### Purpose

Prevent use of incomplete STD families.

### Setup

1. Attempt to create a tender STD instance using inactive placeholder family.

### Expected Result

1. Creation is blocked.
2. User sees that no active STD version is available.
3. No tender instance is created.

### Blocking Severity

`BLOCKER`

---

## SC-010: Mandatory Tender Configuration Values Block Publication

### Purpose

Verify required parameter enforcement.

### Setup

1. Create tender STD instance.
2. Leave `PE_NAME` or `SUBMISSION_DEADLINE` blank.
3. Attempt to submit for review or publication.

### Expected Result

1. Transition is blocked.
2. Validation findings identify missing required parameters.
3. Tender instance remains editable.

### Blocking Severity

`BLOCKER`

---

## SC-011: Date Rule Blocks Invalid Opening Time

### Purpose

Verify cross-field validation.

### Setup

1. Set submission deadline to a later time.
2. Set opening datetime earlier than submission deadline.
3. Run validation.

### Expected Result

1. Validation finding is created.
2. Publication is blocked.
3. Finding identifies both affected fields.

### Blocking Severity

`BLOCKER`

---

## SC-012: Conditional Parameter Activation Works

### Purpose

Verify dependency and conditional field logic.

### Setup

1. Set `TENDER_SECURITY_REQUIRED = false`.
2. Leave `TENDER_SECURITY_AMOUNT` blank.
3. Validate.
4. Set `TENDER_SECURITY_REQUIRED = true`.
5. Validate again.

### Expected Result

1. First validation passes without tender security amount.
2. Second validation fails and requires tender security amount.
3. Conditional dependency is recorded in findings.

### Blocking Severity

`BLOCKER`

---

## SC-013: Generated Bundle Requires Stable Hash

### Purpose

Ensure generated tender artifacts are integrity-protected.

### Setup

1. Complete valid tender configuration.
2. Generate tender bundle.
3. Attempt publication before hash is stored.

### Expected Result

1. Publication is blocked.
2. System requires bundle hash.
3. After hash generation, publication may continue if approvals are complete.

### Blocking Severity

`BLOCKER`

---

## SC-014: Render Is Deterministic

### Purpose

Ensure repeated rendering of same inputs produces same output hash.

### Setup

1. Use identical STD version, tender configuration, and render settings.
2. Render twice.

### Expected Result

1. Rendered outputs are byte-equivalent or semantically equivalent depending on configured renderer mode.
2. Hashes match for deterministic output mode.
3. Any dynamic timestamps are either excluded from hash or deterministically fixed.

### Blocking Severity

`BLOCKER`

---

## SC-015: Published Bundle Is Immutable

### Purpose

Prevent post-publication direct edits.

### Setup

1. Publish generated bundle.
2. Attempt to update bundle content, rendered file, or configuration value that affects published content.

### Expected Result

1. Direct edit is blocked.
2. System requires addendum process.
3. Published bundle hash remains unchanged.

### Blocking Severity

`BLOCKER`

---

## SC-016: Addendum Impact Analysis Identifies Affected Objects

### Purpose

Ensure addendum is not a blind file replacement.

### Setup

1. Publish a tender bundle.
2. Initiate addendum changing a configured deadline or requirement.
3. Run impact analysis.

### Expected Result

1. Addendum impact record lists affected sections, parameters, render blocks, forms, and bidder response obligations where applicable.
2. System indicates whether resubmission or deadline extension may be required.
3. Addendum cannot publish without approval.

### Blocking Severity

`BLOCKER`

---

## SC-017: Superseded STD Version Remains Available to Existing Published Tender

### Purpose

Protect historical tender integrity.

### Setup

1. Publish tender using STD version V1.
2. Activate STD version V2 and supersede V1.
3. Open the published tender bundle and tender STD instance.

### Expected Result

1. Published tender still references V1.
2. V1 remains readable and renderable for audit purposes.
3. New tenders cannot select V1 if it is superseded and not active.

### Blocking Severity

`BLOCKER`

---

## SC-018: Audit Events Are Emitted for Material Actions

### Purpose

Verify audit completeness.

### Setup

1. Execute source upload, source verification, version creation, review submission, approval, activation, tender binding, bundle generation, and publication.

### Expected Result

1. Each material action emits an audit event.
2. Each audit event includes actor, timestamp, object type, object ID, action, from-state, to-state where applicable, and request metadata.
3. Hash fields appear on hash-related events.

### Blocking Severity

`BLOCKER`

---

## SC-019: Permission Denied Is Audited

### Purpose

Ensure failed access attempts are visible.

### Setup

1. User lacking `STD_VERSION_ACTIVATE` attempts to activate version.

### Expected Result

1. Action is denied.
2. Permission denied audit event is emitted.
3. No state transition occurs.

### Blocking Severity

`BLOCKER`

---

## SC-020: Export/Import Round Trip Preserves Semantics

### Purpose

Verify package portability.

### Setup

1. Export a draft or approved STD version to package.
2. Import into clean test environment.
3. Compare section hierarchy, clauses, parameters, rules, forms, render blocks, and source trace.

### Expected Result

1. Structural records match.
2. Source trace records match.
3. Package hash verification succeeds.
4. Generated output from imported version matches original for same tender fixture inputs.

### Blocking Severity

`BLOCKER`

---

## SC-021: Locked Clause Source Trace Required

### Purpose

Ensure legal text is source-grounded.

### Setup

1. Create locked clause without source trace.
2. Attempt to approve or activate STD version.

### Expected Result

1. Approval or activation is blocked.
2. Finding identifies clause missing source trace.
3. Clause must be linked to source document/page/anchor or justified as system-generated.

### Blocking Severity

`BLOCKER`

---

## SC-022: Form Schema Generates Bidder Submission Fields

### Purpose

Verify form schema consumption.

### Setup

1. Activate fixture STD containing Form of Tender schema.
2. Create tender instance.
3. Generate bidder submission schema.

### Expected Result

1. Bidder submission schema includes required fields from the form schema.
2. Field types, required flags, labels, and validation rules are preserved.
3. Locked form text cannot be altered by bidder.

### Blocking Severity

`BLOCKER`

---

## SC-023: Evidence Requirement Is Enforced

### Purpose

Verify mandatory document requirements.

### Setup

1. Seed a mandatory evidence requirement for a bidder form.
2. Submit bidder response without evidence.

### Expected Result

1. Submission validation fails.
2. Missing evidence is identified.
3. Evaluation cannot treat missing mandatory evidence as complete.

### Blocking Severity

`BLOCKER`

---

## SC-024: Price Schedule Arithmetic Can Be Validated

### Purpose

Ensure structured pricing can support later evaluation.

### Setup

1. Configure a simple price schedule with quantity, unit rate, and line total.
2. Bidder submits inconsistent line total.
3. Run validation.

### Expected Result

1. Arithmetic inconsistency is detected.
2. Rule records expected and submitted totals.
3. Depending on STD rule configuration, finding blocks submission/evaluation or routes to correction workflow.

### Blocking Severity

`BLOCKER`

---

## SC-025: Requirement Conformance Matrix Is Generated

### Purpose

Verify controlled requirements are not mere free text.

### Setup

1. Configure three technical requirements.
2. Generate bidder response schema.

### Expected Result

1. Each requirement appears as a structured conformance row.
2. Required response type is enforced.
3. Evidence/reference page field appears where configured.
4. Evaluator can later assess conformance against the same requirement ID.

### Blocking Severity

`BLOCKER`

---

## SC-026: Evaluation Schema Is Derived from STD Version

### Purpose

Prevent manual evaluation drift.

### Setup

1. Configure tender with evaluation criteria from active STD package.
2. Generate evaluation workspace.

### Expected Result

1. Evaluation workspace uses STD-derived criteria and weights.
2. Evaluators cannot add unapproved criteria after publication unless addendum/governed correction applies.
3. Sum of weights is validated where scoring applies.

### Blocking Severity

`BLOCKER`

---

## SC-027: Contract Forms Use Award Data and STD Schema

### Purpose

Verify downstream contract formation.

### Setup

1. Complete evaluation and select successful tenderer in test fixture.
2. Generate contract agreement or award form from STD schema.

### Expected Result

1. Contract form includes STD-defined locked text, configured contract parameters, successful tenderer data, price data, and applicable appendices.
2. Missing award data blocks final contract bundle generation.
3. Contract output is hashed when finalized.

### Blocking Severity

`BLOCKER`

---

## SC-028: Validation Finding Override Requires Permission and Reason

### Purpose

Control exceptional overrides.

### Setup

1. Create warning/blocker finding where override is permitted by rule.
2. User without override permission attempts override.
3. User with override permission attempts override without reason.
4. User with permission provides reason.

### Expected Result

1. First attempt is denied.
2. Second attempt is denied.
3. Third attempt succeeds only if rule allows override.
4. Audit event captures override reason and actor.

### Blocking Severity

`BLOCKER`

---

## SC-029: Emergency Override Is Disabled by Default

### Purpose

Avoid accidental bypass of legal governance.

### Setup

1. Attempt to use emergency override in default seed configuration.

### Expected Result

1. Override is unavailable unless explicitly enabled by environment/configuration.
2. If enabled later, it requires separate role, reason, approval, and audit.

### Blocking Severity

`BLOCKER`

---

## SC-030: Read-Only Auditor Can Verify Published Tender Integrity

### Purpose

Support defensible audit.

### Setup

1. Assign user `AUDITOR` role.
2. User accesses published tender bundle, STD version, source trace, approvals, and hashes.
3. User attempts to edit any record.

### Expected Result

1. Read access succeeds.
2. Hash verification can be run or viewed.
3. Edit attempt is denied and audited.

### Blocking Severity

`BLOCKER`

---

# 34. IT STD Implementation Readiness Smoke Contracts

These smoke contracts prepare for the first production STD package, without hard-coding the core engine to IT.

---

## IT-SC-001: IT STD Family Can Be Registered Without Custom Code

### Purpose

Verify that the generic family/version model can register the IT STD.

### Setup

1. Use `KE-PPRA-IT` family seed.
2. Create draft version for the attached IT STD.
3. Attach official source document.

### Expected Result

1. IT STD family/version uses generic STD family/version tables.
2. No IT-specific database table is required for family/version identity.
3. IT-specific behavior is represented through schemas, section types, rules, and composer modules.

---

## IT-SC-002: IT Requirements Section Uses Generic Requirement Schema

### Purpose

Ensure IT requirements are structured through the generalized requirement model.

### Setup

1. Create functional, architectural, performance, service, technology, implementation, and testing requirements.

### Expected Result

1. Requirements are stored as generic requirement records with type codes.
2. Bidder conformance matrix can be generated from those records.
3. Evaluator review later refers to the same requirement IDs.

---

## IT-SC-003: IT Price Schedules Use Generic Price Schedule Model

### Purpose

Avoid building a one-off IT price table engine.

### Setup

1. Create supply/installation price schedule.
2. Create recurrent cost schedule.
3. Create grand summary schedule.

### Expected Result

1. All schedules use generic price schedule tables with schedule type codes.
2. Summary totals derive from sub-schedules.
3. Financial evaluation can consume structured totals.

---

## IT-SC-004: IT Contract Appendices Use Generic Contract Form Schema

### Purpose

Ensure IT-specific appendices do not bypass the STD form engine.

### Setup

1. Configure contract appendices such as supplier representative, subcontractors, software categories, custom materials, revised price schedules, and contract finalization minutes.

### Expected Result

1. Appendices are stored as contract form schemas and generated contract outputs.
2. Missing required appendix data blocks contract finalization.
3. Final contract bundle is hashed.

---

# 35. Works STD Future Compatibility Smoke Contracts

These ensure that the core engine remains suitable for the WORKS STD and does not become IT-only.

---

## WORKS-SC-001: BOQ Schedule Uses Generic Price Schedule Framework

### Purpose

Ensure BOQ support fits within generic price/quantity model.

### Setup

1. Create a BOQ schedule type.
2. Add items with quantity, unit, rate, and amount.

### Expected Result

1. BOQ uses generic price schedule infrastructure with BOQ-specific rules.
2. Bidder rates are structured.
3. Arithmetic correction rules can apply.

---

## WORKS-SC-002: Drawings and Specifications Can Be Controlled Requirements

### Purpose

Ensure works specifications and drawings do not require a separate engine.

### Setup

1. Register specifications as controlled requirement/reference sections.
2. Register drawings as evidence/reference artifacts.

### Expected Result

1. Specifications and drawings are linked to the STD/tender instance.
2. Generated bundle can include or reference them.
3. Published artifacts are immutable and addendum-controlled.

---

# 36. Minimum Test Data Set

The implementation team should seed the following minimal test data into the test environment.

## 36.1 Users

| User | Roles |
|---|---|
| `std_importer@example.test` | `STD_IMPORTER` |
| `std_admin@example.test` | `STD_TEMPLATE_ADMIN` |
| `std_legal@example.test` | `STD_LEGAL_REVIEWER` |
| `std_procurement@example.test` | `STD_PROCUREMENT_REVIEWER` |
| `std_technical@example.test` | `STD_TECHNICAL_REVIEWER` |
| `std_approver@example.test` | `STD_APPROVER` |
| `std_activator@example.test` | `STD_ACTIVATOR` |
| `pe_officer@example.test` | `PE_PROCUREMENT_OFFICER` |
| `pe_reviewer@example.test` | `PE_PROCUREMENT_REVIEWER` |
| `pe_approver@example.test` | `PE_PROCUREMENT_APPROVER` |
| `publisher@example.test` | `TENDER_PUBLISHER` |
| `auditor@example.test` | `AUDITOR` |

## 36.2 Fixture Records

| Fixture | Required |
|---|---:|
| Source authority `SYSTEM` | Yes |
| Source authority `PPRA` | Yes |
| Family `SMOKE-STD` | Yes |
| Version `SMOKE-STD-001` | Yes |
| At least six fixture sections | Yes |
| At least two locked clauses | Yes |
| At least seven fixture parameters | Yes |
| At least four fixture rules | Yes |
| At least one bidder form schema | Yes |
| At least one render block per section | Yes |
| At least one tender instance | Yes |
| At least one generated bundle | Yes |
| At least one addendum impact record | Yes |

---

## 37. Implementation Order

Use this sequence when implementing seed data and smoke contracts.

1. Controlled enum tables.
2. Source authority seeds.
3. Role seeds.
4. Permission seeds.
5. Role-permission mapping seeds.
6. State seeds.
7. Transition seeds.
8. Audit event type seeds.
9. Approval track seeds.
10. Smoke STD fixture family and version.
11. Smoke source document fixture.
12. Smoke sections, clauses, parameters, rules, forms, render blocks.
13. Validation engine smoke tests.
14. Template governance smoke tests.
15. Tender binding smoke tests.
16. Bundle render/hash smoke tests.
17. Addendum smoke tests.
18. Export/import round-trip smoke test.
19. IT compatibility smoke tests.
20. Works compatibility smoke tests.

---

## 38. Acceptance Criteria

This artifact is implementation-ready when all of the following are true:

1. Seed scripts can be run repeatedly without duplication.
2. All controlled values required by the domain model exist.
3. Roles and permissions exist and support segregation of duties.
4. State machines have seeded states and critical transitions.
5. Active STD version immutability is enforced.
6. Published generated bundle immutability is enforced.
7. Source document hashing and verification are enforced.
8. Import packages require manifests and hashes.
9. Approval tracks block activation until complete.
10. Tender configuration cannot publish with blocker findings.
11. Addendum is required for post-publication content changes.
12. Audit events are emitted for material actions.
13. Generic requirement schema can support the IT STD.
14. Generic price schedule schema can support IT schedules and WORKS BOQs.
15. Smoke contracts SC-001 through SC-030 pass in automated tests.

---

## 39. Approval and State-Transition Completeness Check

Before moving to API/UI or Cursor implementation, verify the following:

| Check | Status required |
|---|---|
| STD source document states defined | Complete |
| Import package states defined | Complete |
| STD family/version states defined | Complete |
| Component states defined | Complete |
| Approval request states defined | Complete |
| Tender STD instance states defined | Complete |
| Generated bundle states defined | Complete |
| Addendum impact states defined | Complete |
| Validation finding states defined | Complete |
| Critical transitions seeded | Complete |
| Permissions mapped to transitions | Complete |
| SoD guardrails seeded | Complete |
| Audit event types seeded | Complete |
| Smoke contracts defined | Complete |

If any row above is incomplete, do not proceed to implementation packaging.

---

## 40. Next Artifact

The next artifact should be:

**STD Engine Core Module - API, UI, and Service Contract**

That artifact should define:

1. Backend services.
2. API endpoints.
3. Request and response payloads.
4. UI screens.
5. Admin workflows.
6. Tender configuration workflows.
7. Validation service contracts.
8. Render service contracts.
9. Import/export service contracts.
10. Addendum service contracts.
11. Audit and hash verification service contracts.
12. Cursor implementation tasks.

The implementation should not begin until this seed and smoke-contract artifact is reviewed and accepted.
