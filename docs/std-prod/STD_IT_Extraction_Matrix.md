# STD for Procurement of Information Technology — Extraction Matrix

**Project:** KenTender e-Procurement System  
**Module:** Standard Tender Document Engine  
**Artifact:** IT STD Extraction Matrix  
**Document status:** Draft for production seed-package preparation  
**Version:** 0.1  
**Prepared date:** 2026-07-07  
**Primary source STD:** `DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.doc`  
**Calibration fixture:** `NSSF SPS RFP ERP 2026(1).pdf`  
**Preceding artifacts:**

1. `STD_Engine_IT_Digitization_Blueprint.md`
2. `STD_Engine_Core_Module_Pre_PRD.md`
3. `STD_Engine_Core_Module_PRD.md`
4. `STD_Engine_Core_Domain_Model.md`
5. `STD_Engine_Core_Governance_Roles_Permissions_State_Model.md`
6. `STD_Engine_Core_Seed_Data_and_Smoke_Contracts.md`
7. `STD_Engine_Core_API_UI_Service_Contract.md`
8. `STD_Engine_Core_Cursor_Implementation_Pack.md`

---

## 1. Purpose

This document converts the official **Standard Tender Document for Procurement of Information Technology** into an implementation extraction matrix for the generalized KenTender STD Engine.

The matrix is not a final seed package. It is the controlled bridge between the official source document and the production-ready package objects that will later be imported into the STD Engine.

The extraction matrix defines:

1. The canonical section hierarchy.
2. The mutability classification for each source area.
3. The production object type to be created for each source area.
4. The tender-specific parameters to expose to Procuring Entities.
5. The bidder-response forms and field groups to generate.
6. The requirement schemas for IT system procurement.
7. The price schedule schemas.
8. The evaluation and qualification schemas.
9. The contract-generation schemas.
10. The render blocks needed to produce issued tender documents and downstream contract artifacts.
11. The rule inventory and validation behavior.
12. The smoke contracts required before the IT STD package can be activated.

The goal is to produce the first full production STD package:

```text
KE-PPRA-IT-2022-04
```

This package must be usable for IT tenders without hard-coding ERP-specific or NSSF-specific assumptions.

---

## 2. Source Basis

### 2.1 Official IT STD

The official IT STD is the legal master source for this extraction. It is a PPRA standard tender document for procurement of information technology under competitive tendering methods. It supports national and international tendering, with or without prequalification, and is designed for complex business, functional, technical, implementation, support, and information-system requirements.

The official IT STD includes:

1. Preface and preparation guidance.
2. Invitation to Tender.
3. Part 1 — Tendering Procedures.
4. Section I — Instructions to Tenderers.
5. Section II — Tender Data Sheet.
6. Section III — Evaluation and Qualification Criteria.
7. Section IV — Tendering Forms.
8. Part 2 — Procuring Entity's Requirements.
9. Section V — Requirements of the Information System.
10. Section VI — Technical Requirements.
11. Section VII — Implementation Schedule.
12. Section VIII — System Inventory Tables.
13. Section IX — Background and Informational Materials.
14. Part 3 — Contract.
15. Section X — General Conditions of Contract.
16. Section XI/XII — Special Conditions of Contract, depending on source numbering.
17. Section XII/XIII — Contract Forms, depending on source numbering.

The source numbering has internal inconsistencies in places, especially around the contract sections. The engine must preserve the source label as printed but must also assign stable internal canonical identifiers.

### 2.2 WORKS PoC as architectural precedent

The earlier WORKS PoC validated the approach of treating an STD as a structured legal configuration source, not as an uploaded attachment. That approach remains valid.

The corrected production approach is:

1. Do not store a whole STD as a single production JSON blob.
2. Use import/export JSON packages only as seed, migration, review, source-control, and regression artifacts.
3. Store runtime objects in normalized domain records.
4. Preserve source traceability for sections, clauses, parameters, fields, rules, forms, render blocks, and generated bundles.

### 2.3 NSSF ERP tender as calibration fixture

The NSSF ERP tender is a useful real-world tender prepared for supply, installation, configuration, customization, testing, commissioning, and maintenance of an ERP system.

It is not the legal master STD.

Use it only to validate that the IT STD model can represent a real IT tender with:

1. Tender identity and TDS values.
2. Mandatory requirements.
3. Technical qualification criteria.
4. Scored technical evaluation.
5. ERP module requirements.
6. Technical compliance matrices.
7. Implementation phasing.
8. Testing and acceptance obligations.
9. Training and knowledge transfer.
10. Warranty and maintenance support.
11. Price schedule structures.
12. SCC and contract-form content.

Any NSSF-specific choices must remain tender-instance data, not STD master data.

---

## 3. Extraction Principles

### 3.1 Generalized engine first

The IT STD is the first full production seed, but the engine must remain STD-family-neutral.

The package must use the same core concepts required for future STDs:

1. Template family.
2. Template version.
3. Source document.
4. Section hierarchy.
5. Clause inventory.
6. Parameters.
7. Rules.
8. Forms.
9. Form fields.
10. Evidence requirements.
11. Requirement schemas.
12. Price schedule schemas.
13. Evaluation schemas.
14. Contract schemas.
15. Render blocks.
16. Lifecycle state.
17. Audit events.
18. Hashes.
19. Smoke contracts.

### 3.2 No direct editing of locked legal sections

The official IT STD states that Instructions to Tenderers and General Conditions of Contract are not to be changed directly. They are customized through TDS and SCC respectively.

The extraction must therefore classify:

| Source area | Treatment |
|---|---|
| ITT | Locked legal text |
| GCC | Locked legal text |
| TDS | Controlled parameter surface |
| SCC | Controlled parameter surface |
| Evaluation criteria | Controlled configurable schema |
| Tendering forms | Structured schema, with controlled editable blanks |
| Requirements | Controlled PE-authored structured content |
| Technical requirements | Controlled requirement library / matrix |
| Implementation schedule | Structured milestone and deliverable schema |
| System inventory tables | Structured inventory and cost schema |
| Contract forms | Generated downstream artifacts |

### 3.3 Rendered tender documents are immutable once published

The engine must generate tender documents from the active STD version and the tender-specific configuration.

After publication:

1. The generated bundle is immutable.
2. The generated bundle is hashed.
3. The tender is bound to the STD version used.
4. Changes require an addendum workflow.
5. Addenda must identify affected sections, parameters, forms, rules, requirements, render blocks, and bidder submission obligations.

### 3.4 Requirements must be structured, not uploaded as prose

The IT STD is designed around business, functional, architectural, performance, service, technology, implementation, testing, and support requirements.

The Requirements of the Information System must therefore be implemented as a controlled requirements composer, not as a single attachment field.

### 3.5 Real tender variation is permitted only through controlled data

The NSSF ERP tender demonstrates legitimate real-world tailoring, including:

1. Specific ERP scope.
2. Microsoft Dynamics 365 Business Central requirement.
3. Pension scheme-specific module requirements.
4. Professional indemnity requirement.
5. Two-phase implementation schedule.
6. Specific minimum experience requirements.
7. Technical scoring with a 75-point pass mark.

These must be represented as tender-instance configuration, evaluation criteria, requirement rows, evidence requirements, price schedule values, and SCC values. They must not become hard-coded IT STD behavior.

---

## 4. Canonical Package Identity

| Field | Value |
|---|---|
| Template family code | `KE-PPRA-IT` |
| Template family name | Standard Tender Document for Procurement of Information Technology |
| Version code | `KE-PPRA-IT-2022-04` |
| Source authority | Public Procurement Regulatory Authority, Kenya |
| Source document title | Standard Tender Document for Procurement of Information Technology |
| Source document label | DOC. 10 |
| Issue date basis | Issued 22 April 2021; updated 21 April 2022 with amended Form of Tender and Beneficial Ownership Information Disclosure Form |
| Procurement domain | Information Technology / Information System procurement |
| Tendering process | One-envelope tendering process, with or without prequalification |
| Intended procurement use | Complex IT systems, business applications, software development, large-scale IT, design, supply, installation, training, support, and related services |
| Initial production status | Draft seed package |
| Target activation state | Approved and Active after extraction QA, legal/procurement review, package import, validation, render verification, and smoke tests |

---

## 5. Canonical Section Hierarchy

The official source has printed numbering inconsistencies. The following canonical section hierarchy must be used internally while preserving printed source references.

| Canonical ID | Printed source reference | Section title | Parent | Render order | Default treatment |
|---|---|---|---|---:|---|
| `IT.COVER` | Cover page | STD cover | Root | 1 | Source/admin only; not issued as tender cover unless configured |
| `IT.PREFACE` | Preface | Preface | Root | 2 | Source/admin only; not issued to bidders |
| `IT.PREFACE.APPENDIX` | Appendix to Preface | Guidelines for Preparing Tender Documents | Root | 3 | Source/admin only; not issued to bidders |
| `IT.ISSUE_PAGE` | Beginning page | Name, logo, address, tender identity | Root | 4 | Generated tender cover/start page |
| `IT.INVITATION` | Invitation to Tender | Invitation to Tender | Root | 5 | Parameterized generated section |
| `IT.PART1` | Part 1 | Tendering Procedures | Root | 6 | Container |
| `IT.ITT` | Section I | Instructions to Tenderers | `IT.PART1` | 7 | Locked legal text |
| `IT.TDS` | Section II | Tender Data Sheet | `IT.PART1` | 8 | Configurable parameter table |
| `IT.EVAL` | Section III | Evaluation and Qualification Criteria | `IT.PART1` | 9 | Controlled configurable evaluation schema |
| `IT.FORMS` | Section IV | Tendering Forms | `IT.PART1` | 10 | Structured bidder form schemas |
| `IT.PART2` | Part 2 | Procuring Entity's Requirements | Root | 11 | Container |
| `IT.REQ` | Section V | Requirements of the Information System | `IT.PART2` | 12 | Controlled PE-authored structured requirements |
| `IT.TECH` | Section VI | Technical Requirements | `IT.PART2` | 13 | Structured technical requirement schema |
| `IT.IMPL` | Section VII | Implementation Schedule | `IT.PART2` | 14 | Structured milestone/deliverable schema |
| `IT.INVENTORY` | Section VIII | System Inventory Tables | `IT.PART2` | 15 | Structured inventory and cost item schema |
| `IT.BACKGROUND` | Section IX | Background and Informational Materials | `IT.PART2` | 16 | Controlled informational content |
| `IT.PART3` | Part 3 | Contract | Root | 17 | Container |
| `IT.GCC` | Section X / VI in source body | General Conditions of Contract | `IT.PART3` | 18 | Locked legal text |
| `IT.SCC` | Section XI / VII in source body | Special Conditions of Contract | `IT.PART3` | 19 | Configurable contract parameter table |
| `IT.CONTRACT_FORMS` | Section XII / XIII in source body | Contract Forms | `IT.PART3` | 20 | Generated downstream contract artifacts |
| `IT.AUDIT` | System-generated | STD generation and audit summary | Root | 21 | System-generated internal/output appendix where authorized |

---

## 6. Mutability Model

| Mutability code | Meaning | Editable by PE? | Editable by STD admin? | Version impact | Examples |
|---|---|---:|---:|---|---|
| `SOURCE_ONLY` | Source guidance/admin content not issued to bidders | No | Yes, before approval | New template version if changed | Preface, preparation guidance |
| `LOCKED_LEGAL` | Legal standard text used without modification | No | Yes, only by new version | New template version | ITT, GCC |
| `PARAMETERIZED_LOCKED` | Locked text with controlled blanks/variables | Only blanks/parameters | Yes, only by new version | Parameter change for tender; template change for text | Invitation, Form of Tender |
| `CONFIG_TABLE` | Structured data table completed by PE | Yes, through schema | Yes, schema only by new version | Tender instance values | TDS, SCC |
| `CONTROLLED_REQUIREMENTS` | PE-authored structured requirements governed by schema | Yes, through composer | Yes, schema only by new version | Tender instance values | Technical requirements |
| `CONTROLLED_EVALUATION` | Evaluation criteria selected/configured within template guardrails | Yes, within allowed schema | Yes, schema only by new version | Tender instance values | Qualification and scoring |
| `BIDDER_RESPONSE_SCHEMA` | Forms completed by bidders | No for PE after publication; bidders complete during submission | Yes, schema only by new version | Template version | Tendering forms |
| `PRICE_SCHEMA` | Pricing tables completed by bidders or PE setup | PE configures structure; bidders enter prices | Yes, schema only by new version | Template version / tender instance | Price schedules |
| `GENERATED_CONTRACT` | Contract artifact generated after award | No direct edit except governed finalization | Yes, schema only by new version | Award/contract instance | Contract agreement, appendices |
| `SYSTEM_GENERATED` | Derived system artifact | No | No direct edit | Regenerated only before publication or through addendum | Validation summary, audit bundle |

---

## 7. Section-Level Extraction Matrix

### 7.1 Source guidance and preface

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.COVER` | Official cover page | Source document metadata and visual reference | `SOURCE_ONLY` | No | Preserve source document hash and title metadata. |
| `IT.PREFACE` | Preface | Source guidance clauses | `SOURCE_ONLY` | No | Important for governance and policy but not part of issued tender document. |
| `IT.PREFACE.APPENDIX` | Guidelines for Preparing Tender Documents | Source guidance clauses and validation notes | `SOURCE_ONLY` | No | Convert key preparation instructions into validation and help text where appropriate. |

Key extracted controls from guidance:

| Control | Engine treatment |
|---|---|
| ITT and GCC not directly modified | Enforce `LOCKED_LEGAL` mutability. |
| TDS and SCC supplement ITT/GCC | Map TDS/SCC fields to controlled parameter tables. |
| Tender security should be absolute amount and not more than 2% of estimate | Validation rule against tender estimate where tender security is used. |
| Average annual turnover guidance approximately 2.5x estimate | Advisory rule / recommended value helper. |
| Specific experience value often around 80% of estimate | Advisory rule / recommended value helper. |
| PE must confirm procurement plan and budget | Pre-generation readiness rule. |
| Experts should prepare estimates | Workflow/evidence prompt, not hard blocker unless policy requires. |

### 7.2 Tender issue page

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.ISSUE_PAGE` | Beginning page: PE name, logo, address, tender identity | Render block with required parameters | `PARAMETERIZED_LOCKED` | Yes | This is the actual starting page of the issued tender document. |

Parameters:

| Parameter code | Label | Type | Required | Source surface | Validation |
|---|---|---|---:|---|---|
| `pe.name` | Name of Procuring Entity | Text | Yes | Issue page / Invitation / TDS | Must match tender owner entity. |
| `pe.logo_file_id` | Procuring Entity logo | File reference | Optional/conditional | Issue page | If required by platform branding policy. |
| `pe.physical_address` | Physical address | Multiline text | Yes | Issue page / Invitation | Required for submission/opening unless e-tender only. |
| `pe.postal_address` | Postal address | Text | Optional/conditional | Issue page / Invitation | Required where physical submission is used. |
| `pe.email` | Contact email | Email | Yes | Issue page / Invitation / TDS | Must be valid email. |
| `tender.name` | Tender name | Text | Yes | Issue page / Invitation / TDS | Must match tender record. |
| `tender.identification_no` | Invitation/Tender number | Text | Yes | Issue page / Invitation / TDS | Unique per PE and financial year according to system policy. |
| `tender.description` | Brief tender description | Multiline text | Yes | Invitation | Should be concise and not conflict with requirements scope. |

### 7.3 Invitation to Tender

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.INVITATION` | Invitation to Tender | Render block with parameterized paragraphs | `PARAMETERIZED_LOCKED` | Yes | Generated from tender identity, method, participation, dates, security, and address parameters. |

Parameters:

| Parameter code | Label | Type | Required | Validation / rule |
|---|---|---|---:|---|
| `procurement.method` | Procurement method | Enum | Yes | Allowed values controlled by procurement method module. |
| `competition.scope` | National / International | Enum | Yes | Drives currency, dispute, margin, and foreign-input rules. |
| `reservation.enabled` | Reservation applies? | Boolean | Yes | If true, reservation group required. |
| `reservation.group` | Eligible reserved group | Enum/text | Conditional | Required when reservation enabled. |
| `lots.enabled` | Multiple lots/contracts? | Boolean | Yes | If true, lot structure required. |
| `lots.bid_policy` | Whether tenderers may bid for one or more lots | Enum | Conditional | Required when lots enabled. |
| `document.purchase_fee` | Tender document fee | Money | Optional | Must not conflict with electronic-free-download policy where applicable. |
| `document.download_url` | Tender download website | URL | Optional | Required when electronic download is allowed. |
| `tender.security.type` | Tender security or tender-securing declaration | Enum | Yes | Drives form activation. |
| `tender.security.amount` | Tender security amount | Money | Conditional | Required when security type is money guarantee; must pass max-percentage rule. |
| `tender.validity_days` | Tender validity period | Integer | Yes | Must be positive and consistent with opening date. |
| `tender.submission_deadline` | Submission deadline | Datetime | Yes | Must be after publication date and clarification cutoff. |
| `tender.electronic_submission_permitted` | Electronic tenders permitted? | Boolean | Yes | Drives submission instructions and portal obligations. |
| `tender.opening_datetime` | Tender opening date/time | Datetime | Yes | Must be same as or after submission deadline according to policy. |
| `address.obtain_information` | Address for obtaining further information | Address group | Yes | Rendered in invitation. |
| `address.submission` | Address for submission | Address group | Conditional | Required where physical submission is permitted/required. |
| `address.opening` | Address for opening | Address group | Yes | Required for public opening details. |
| `authorized_official.name` | Authorized official name | Text | Yes before final issue | Required for signed issue artifact. |
| `authorized_official.designation` | Authorized official designation | Text | Yes before final issue | Required for signed issue artifact. |
| `authorized_official.signature_mode` | Signature mode | Enum | Yes | Manual / digital / e-signature. |
| `authorized_official.signature_date` | Signature date | Date | Yes before final issue | Must not be before approval date unless permitted. |

### 7.4 Part 1 container

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.PART1` | Part 1 — Tendering Procedures | Section container | `SYSTEM_GENERATED` | Yes | Header only. |

### 7.5 Section I — Instructions to Tenderers

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.ITT` | Section I — Instructions to Tenderers | Locked clause tree | `LOCKED_LEGAL` | Yes | Source text must be preserved. Tender-specific detail is supplied through TDS. |

Clause group extraction:

| Clause group | Topic | Extraction object | Parameter dependency |
|---|---|---|---|
| `ITT.A` | General | Locked clause group | TDS identity, site, definitions. |
| `ITT.1` | Scope of Tender | Locked clause | `tender.name`, `tender.identification_no`, `lots.*` |
| `ITT.2` | Definitions | Locked clause | None except cross-reference metadata. |
| `ITT.3` | Fraud and Corruption | Locked clause | Form activation for declarations. |
| `ITT.4` | Eligible Tenderers | Locked clause | JV max, state-owned enterprise, debarment, foreign-input rules. |
| `ITT.5` | Eligible Goods and Services | Locked clause | Origin and harmful goods/services rules. |
| `ITT.6` | Sections of Tendering Document | Locked clause | Rendered section list. |
| `ITT.7` | Site Visit / clarification | Locked clause | TDS site visit and clarification fields. |
| `ITT.8` | Pre-Tender Meeting | Locked clause | TDS meeting fields. |
| `ITT.9/10` | Amendment/Addenda | Locked clause | Addendum service integration. |
| `ITT.11` | Documents Comprising Tender | Locked clause | Form/evidence activation. |
| `ITT.12` | Form of Tender and Price Schedules | Locked clause | Price schedule schemas. |
| `ITT.13` | Alternative Tenders | Locked clause | `alternative_tenders.permitted`. |
| `ITT.14` | Eligibility of Information System | Locked clause | Country of origin, eligibility evidence. |
| `ITT.15` | Tenderer qualifications | Locked clause | Qualification forms and criteria. |
| `ITT.16` | Conformity of Information System | Locked clause | Requirement conformance matrix. |
| `ITT.17` | Tender Prices | Locked clause | Price schema, currency, fixed/adjustable price. |
| `ITT.18` | Currency | Locked clause | `currency.*`. |
| `ITT.19` | Tender validity | Locked clause | `tender.validity_days`. |
| `ITT.20` | Tender Security | Locked clause | `tender.security.*`. |
| `ITT.21` | Format and Signing | Locked clause | submission copies, signing authority. |
| `ITT.22-26` | Submission and Opening | Locked clauses | physical/electronic submission, deadline, opening. |
| `ITT.27-40` | Evaluation and Comparison | Locked clauses | Evaluation schema, conversion, margin, abnormally low/high, postqualification. |
| `ITT.41-50` | Award and complaint | Locked clauses | award, standstill, notification, debriefing, performance security, adjudicator, complaint. |

### 7.6 Section II — Tender Data Sheet

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.TDS` | Tender Data Sheet | Parameter table schema | `CONFIG_TABLE` | Yes | PE completes values through controlled UI. |

TDS parameter extraction:

| Parameter code | TDS topic | Type | Required | Rule / dependency |
|---|---|---|---:|---|
| `tds.itt_1_1.pe_name` | Procuring Entity name | Text | Yes | Must match tender owner. |
| `tds.itt_1_1.system_scope` | Supply and installation scope | Multiline text | Yes | Must align with Part 2 requirements. |
| `tds.itt_1_1.tender_name` | Tender name | Text | Yes | Must match tender record. |
| `tds.itt_1_1.tender_number` | Tender identification number | Text | Yes | Unique. |
| `tds.lots.number` | Number of lots/contracts | Integer | Conditional | Required when lots enabled; minimum 1. |
| `tds.jv.maximum_members` | Maximum JV members | Integer | Yes | Recommended two or three; above five requires warning/blocker depending policy. |
| `tds.unfair_competitive_advantage.firms` | Firms that provided consulting services | Repeatable party list | Optional | If present, conflict checks must run. |
| `tds.clarification.address` | Address for clarification | Address/contact group | Yes | Must include contact route. |
| `tds.clarification.deadline_days_before_submission` | Clarification cutoff | Integer | Yes | Must be before submission deadline. |
| `tds.site_visit.enabled` | Site visit / pre-arranged visit applies | Boolean | Yes | If true, site visit details required. |
| `tds.site_visit.datetime` | Site visit date/time | Datetime | Conditional | Must be before clarification cutoff or submission deadline. |
| `tds.site_visit.location` | Site visit location | Address/text | Conditional | Required if enabled. |
| `tds.pre_tender_meeting.enabled` | Pre-tender meeting applies | Boolean | Yes | If true, meeting details required. |
| `tds.pre_tender_meeting.datetime` | Pre-tender meeting date/time | Datetime | Conditional | Must be before submission deadline. |
| `tds.pre_tender_meeting.location` | Meeting location or link | Text/URL | Conditional | Physical or virtual. |
| `tds.addenda.publication_url` | Web page for addenda/minutes | URL | Optional | Required where publication policy applies. |
| `tds.language` | Tender language | Enum | Yes | Default English. |
| `tds.alternative_tenders.permitted` | Alternative tenders permitted | Boolean | Yes | Drives form/evaluation behavior. |
| `tds.price_adjustment.permitted` | Price adjustment allowed | Boolean | Yes | If false, reject adjustable-price tenders. |
| `tds.currency.local` | Local currency | Currency | Yes | Default KES. |
| `tds.currency.foreign_allowed` | Foreign currency allowed | Boolean | Conditional | Typically driven by national/international scope. |
| `tds.currency.conversion_method` | Currency conversion source/method | Text/enum | Conditional | Required if foreign currencies allowed. |
| `tds.tender_validity_days` | Tender validity period | Integer | Yes | Must match invitation and Form of Tender. |
| `tds.tender_security.type` | Security type | Enum | Yes | Tender security / tender-securing declaration / other approved security. |
| `tds.tender_security.amount` | Security amount | Money | Conditional | Required for monetary security. |
| `tds.tender_security.validity_days_after_tender_validity` | Security validity buffer | Integer | Conditional | Required for monetary security if source specifies. |
| `tds.submission.copies_original` | Number of originals | Integer | Conditional | Required for physical submission. |
| `tds.submission.copies_duplicate` | Number of copies | Integer | Conditional | Required for physical submission. |
| `tds.submission.electronic_permitted` | Electronic submission permitted | Boolean | Yes | Drives submission channel. |
| `tds.submission.deadline` | Tender submission deadline | Datetime | Yes | Must be after issue/publication. |
| `tds.opening.datetime` | Tender opening date/time | Datetime | Yes | Must be on or after deadline. |
| `tds.opening.location` | Tender opening location | Address/text | Yes | Required unless electronic opening regime handles it. |
| `tds.margin_of_preference.applies` | Margin of preference applies | Boolean | Yes | If true, margin method required. |
| `tds.reservation.applies` | Reservation applies | Boolean | Yes | If true, eligible group required. |
| `tds.prequalification.applies` | Prequalification applies | Boolean | Yes | If true, prequalification reference required. |
| `tds.foreign_input_40_percent_rule.applies` | Foreign tenderer 40% citizen-input rule applies | Boolean | Yes | Typically true where foreign tenderers allowed. |
| `tds.award.quantity_variation_allowed` | Quantity variation at award | Boolean | Optional | If allowed, cap/rule required. |
| `tds.standstill_period_days` | Standstill period | Integer | Yes | Must comply with applicable procurement rules. |
| `tds.performance_security.amount_or_percent` | Performance security amount/percentage | Money/percent | Yes | Render into SCC/contract forms. |
| `tds.adjudicator.required` | Adjudicator required | Boolean | Yes | If true, adjudicator data required. |
| `tds.complaint_review_reference` | Procurement complaint/review instructions | Text/reference | Yes | Must render with award section. |

### 7.7 Section III — Evaluation and Qualification Criteria

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.EVAL` | Evaluation and Qualification Criteria | Evaluation schema with controlled configurable values | `CONTROLLED_EVALUATION` | Yes | Evaluation must be generated from the published tender, not created ad hoc later. |

Evaluation-stage schema:

| Stage code | Stage name | Evaluation mode | Configurable by PE? | Output object |
|---|---|---|---:|---|
| `EVAL.PRELIM` | Preliminary responsiveness | Pass/fail | Yes, within allowed criteria library | Responsiveness checklist |
| `EVAL.TECH_ADEQUACY` | Adequacy of tenderer's proposal against IT requirements | Pass/fail and/or scored | Yes, within guardrails | Technical compliance matrix |
| `EVAL.PRICE` | Price evaluation | Computed | Limited | Financial evaluation sheet |
| `EVAL.ALTERNATIVES` | Alternative tenders | Conditional | Yes, through TDS | Alternative tender review matrix |
| `EVAL.MARGIN` | Margin of preference | Conditional computed | Yes, if enabled | Preference adjustment schedule |
| `EVAL.POSTQUAL` | Post-qualification and contract award | Pass/fail | Yes, within allowed criteria | Postqualification report |
| `EVAL.QUALIFICATION` | Qualification | Pass/fail / threshold | Yes | Qualification checklist |
| `EVAL.PERSONNEL` | Personnel | Pass/fail / scored | Yes | Personnel evaluation matrix |

Evaluation criteria extraction:

| Criteria code | Criteria family | Data object | Expected configuration |
|---|---|---|---|
| `qual.general_experience` | General experience | `STD Evaluation Criterion` | Years, evidence, minimum threshold. |
| `qual.specific_experience` | Specific IT system implementation experience | `STD Evaluation Criterion` | Number/value/type of similar contracts. |
| `qual.financial_situation` | Financial situation | `STD Evaluation Criterion` | Audited statements, ratios, solvency. |
| `qual.average_annual_turnover` | Average annual turnover | `STD Evaluation Criterion` | Years and monetary threshold. |
| `qual.financial_resources` | Financial resources | `STD Evaluation Criterion` | Available cash/credit threshold. |
| `qual.current_commitments` | Current contract commitments | `STD Evaluation Criterion` | Work in progress summary. |
| `qual.litigation_history` | Contract non-performance / pending litigation | `STD Evaluation Criterion` | Disclosure form and pass/fail logic. |
| `qual.personnel_project_manager` | Project manager | `STD Personnel Criterion` | Role, minimum years, qualifications, evidence. |
| `qual.personnel_technical_lead` | Technical lead / system architect | `STD Personnel Criterion` | Role, years, certifications, evidence. |
| `qual.personnel_functional_experts` | Functional consultants | `STD Personnel Criterion` | Domain-specific configurable roles. |
| `tech.functional_conformity` | Functional requirements | `STD Technical Criterion` | Conformance response per requirement. |
| `tech.architecture_conformity` | Architecture requirements | `STD Technical Criterion` | Conformance response per requirement. |
| `tech.performance_conformity` | Performance requirements | `STD Technical Criterion` | Conformance response per requirement. |
| `tech.service_conformity` | Service specifications | `STD Technical Criterion` | Conformance response per service item. |
| `tech.technology_conformity` | Technology specifications | `STD Technical Criterion` | Conformance response per technology item. |
| `tech.implementation_schedule` | Implementation schedule | `STD Technical Criterion` | Milestone conformance. |
| `tech.training` | Training / knowledge transfer | `STD Technical Criterion` | Required plan and evidence. |
| `price.supply_installation` | Supply and installation price | `STD Price Evaluation Component` | Calculated from price schedules. |
| `price.recurrent` | Recurrent cost | `STD Price Evaluation Component` | Calculated from recurrent cost tables. |
| `price.grand_total` | Grand summary | `STD Price Evaluation Component` | Computed from supply/install and recurrent components. |

Guardrails:

| Guardrail | Behavior |
|---|---|
| Published criteria immutability | Evaluation criteria cannot be changed after publication except by addendum. |
| Evaluation-source binding | Evaluators see criteria generated from tender's STD instance only. |
| No hidden criteria | Evaluation service must reject criteria not included in the published tender or addendum. |
| Pass/fail before price | Price evaluation must not proceed for non-responsive tenders where tender rules block it. |
| Requirement conformance traceability | Each technical finding must trace to a published requirement row. |

### 7.8 Section IV — Tendering Forms

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.FORMS` | Tendering Forms | Form schema library | `BIDDER_RESPONSE_SCHEMA` | Yes | Each form becomes a structured bidder-response schema with fields, validations, evidence, and signature rules. |

Form inventory:

| Form code | Source title | Respondent | Object type | Activation |
|---|---|---|---|---|
| `FORM.TENDER` | Form of Tender | Tenderer | Bidder form schema | Always |
| `FORM.CBQ` | Tenderer's Eligibility / Confidential Business Questionnaire | Tenderer | Bidder form schema | Always |
| `FORM.CITD` | Certificate of Independent Tender Determination | Tenderer | Declaration form | Always |
| `FORM.SELF_DECLARATION` | Self-Declaration Form | Tenderer | Declaration form | Always |
| `FORM.FRAUD_CORRUPTION_APPENDIX` | Appendix 1 — Fraud and Corruption | Tenderer | Acknowledgement/declaration form | Always or where required by policy |
| `FORM.PRICE.GRAND_SUMMARY` | Grand Summary Cost Table | Tenderer | Price schedule | Always |
| `FORM.PRICE.SUPPLY_INSTALL_SUMMARY` | Supply and Installation Cost Summary Table | Tenderer | Price schedule | Always |
| `FORM.PRICE.RECURRENT_SUMMARY` | Recurrent Cost Summary Table | Tenderer | Price schedule | Conditional / usually always for IT |
| `FORM.PRICE.SUPPLY_INSTALL_SUBTABLE` | Supply and Installation Cost Sub-Table | Tenderer | Price line-item table | Always |
| `FORM.PRICE.RECURRENT_SUBTABLE` | Recurrent Cost Sub-Table | Tenderer | Price line-item table | Conditional / usually always for IT |
| `FORM.PRICE.ORIGIN_CODE` | Country of Origin Code Table | Tenderer | Reference/code table | When origin data required |
| `FORM.FOREIGN_40_RULE` | Foreign Tenderers 40% Rule | Tenderer | Compliance declaration/table | When foreign tenderers allowed/rule applies |
| `FORM.ELI_1` | Tenderer Information Form | Tenderer | Qualification form | Always |
| `FORM.ELI_1_JV` | Tenderer's JV Members Information Form | Tenderer/JV members | Qualification form | If JV permitted/submitted |
| `FORM.CON_1` | Historical Contract Non-Performance and Pending Litigation | Tenderer | Qualification form | Always |
| `FORM.EXP_1` | Experience — General Experience | Tenderer | Qualification form | If general experience criterion enabled |
| `FORM.EXP_2` | Specific Experience | Tenderer | Qualification form | If specific experience criterion enabled |
| `FORM.CCC_1` | Current Contract Commitments / Work in Progress | Tenderer | Qualification form | If current commitments criterion enabled |
| `FORM.FIN_1` | Financial Situation | Tenderer | Qualification form | If financial situation criterion enabled |
| `FORM.FIN_2` | Average Annual Turnover | Tenderer | Qualification form | If turnover criterion enabled |
| `FORM.FIN_3` | Financial Resources | Tenderer | Qualification form | If financial resources criterion enabled |
| `FORM.PERSONNEL` | Personnel Capabilities | Tenderer | Qualification/personnel form | If personnel criterion enabled |
| `FORM.IP` | Intellectual Property Forms | Tenderer | IP/license disclosure form | Always for IT system tenders unless excluded by template config |
| `FORM.CONFORMANCE` | Conformance of Information System Materials | Tenderer | Requirement conformance response | Always |

Form-level fields to standardize:

| Field group | Applies to | Required behavior |
|---|---|---|
| Tenderer identity | All bidder forms | Pull from supplier profile where authenticated; lock after submission. |
| Authorized signatory | Signature/declaration forms | Require authorization evidence where applicable. |
| JV member details | JV forms | Repeatable members; each member traceable. |
| Evidence attachments | Qualification forms | Evidence requirement rows created from evaluation criteria. |
| Certification text | Declaration forms | Locked; tenderer can only acknowledge/sign. |
| Price amounts | Price schedules | Numeric, currency-aware, calculation-controlled. |
| Tax treatment | Price schedules | VAT/taxes captured separately according to template/tender config. |
| Origin codes | Origin forms/price schedules | Validate against configured country list/codes. |
| Requirement response | Conformance form | Yes/No/partial/complies/not complies/comment/reference page/evidence. |
| IP category | IP forms | Standard software, custom software, third-party software, licenses, custom materials. |

### 7.9 Part 2 container

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.PART2` | Part 2 — Procuring Entity's Requirements | Section container | `SYSTEM_GENERATED` | Yes | Header only. |

### 7.10 Section V — Requirements of the Information System

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.REQ` | Requirements of the Information System | Requirements composer schema | `CONTROLLED_REQUIREMENTS` | Yes | Core IT-specific configuration surface. |

Requirement object model:

| Requirement object | Purpose | Required fields |
|---|---|---|
| `IT Requirement Set` | Groups requirements for a tender | title, scope, requirement category, source, status, owner |
| `IT Requirement Row` | Atomic requirement obligation | code, title, statement, category, mandatory flag, response mode, evaluation link |
| `IT Requirement Attribute` | Structured metadata | performance metric, module, priority, standard, interface, security level |
| `IT Requirement Evidence` | Required proof from bidder | evidence type, mandatory flag, accepted file types, validation notes |
| `IT Requirement Conformance Field` | Bidder response specification | yes/no, partial, remarks, reference page, attachment, deviation |
| `IT Requirement Evaluation Link` | Maps requirement to evaluation | criterion, score group, pass/fail group, weight |

Requirement categories:

| Category code | Category title | Examples |
|---|---|---|
| `REQ.FUNCTIONAL` | Functional requirement | Business functions, transaction workflows, reports, approvals. |
| `REQ.ARCHITECTURAL` | Architectural requirement | Hosting, integration, identity, scalability, APIs, environment design. |
| `REQ.PERFORMANCE` | Performance requirement | Response time, throughput, availability, concurrent users, recovery. |
| `REQ.SECURITY` | Security requirement | Access control, audit trails, encryption, logs, compliance. |
| `REQ.SERVICE` | Service specification | Installation, configuration, customization, support, maintenance. |
| `REQ.TECHNOLOGY` | Technology specification | Hardware, software, platform, database, cloud, network. |
| `REQ.DATA_MIGRATION` | Data migration | Extract, transform, load, validation, reconciliation. |
| `REQ.INTEGRATION` | Integration | Internal/external systems, APIs, protocols, interface ownership. |
| `REQ.TESTING_ACCEPTANCE` | Testing and acceptance | Unit, integration, UAT, performance, operational acceptance. |
| `REQ.TRAINING` | Training and knowledge transfer | User training, administrator training, training materials. |
| `REQ.DOCUMENTATION` | Documentation | Manuals, architecture docs, configuration guides, support docs. |
| `REQ.WARRANTY_SUPPORT` | Warranty, maintenance, support | Warranty period, SLA, local support, escalation, preventive maintenance. |
| `REQ.BACKGROUND` | Background/informational material | Current environment, sites, training facilities, existing systems. |

### 7.11 Section VI — Technical Requirements

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.TECH` | Technical Requirements | Requirement subtype schemas and controlled tables | `CONTROLLED_REQUIREMENTS` | Yes | This is the main technical compliance matrix source. |

Technical requirement subtype extraction:

| Subtype | Data object | Field pattern | Bidder response pattern |
|---|---|---|---|
| Acronyms | Reference table | acronym, meaning | No bidder response unless requested. |
| Functional requirements | Requirement rows | module/process/function/requirement/mandatory | Complies? comment, reference, evidence. |
| Architectural requirements | Requirement rows | architecture area/design requirement/mandatory | Complies? architecture narrative, reference. |
| Performance requirements | Requirement rows | metric/target/unit/test method | Complies? proposed value, evidence. |
| Service specifications | Service item rows | service type/deliverable/timeline/acceptance | Approach, evidence, compliance. |
| Technology specifications | Technology item rows | component/spec/minimum/standard | Make/model/version, compliance, evidence. |
| Testing requirements | Test obligation rows | test type/responsibility/acceptance evidence | Methodology and artifacts. |
| Documentation requirements | Deliverable rows | document name/minimum content/format | Delivery commitment. |
| Training requirements | Training row | audience/duration/materials/signoff | Training approach. |

Standard requirement row fields:

| Field code | Type | Required | Notes |
|---|---|---:|---|
| `requirement_code` | Text | Yes | Stable within tender, e.g. `GEN-001`, `SEC-004`. |
| `requirement_title` | Text | Yes | Short name. |
| `requirement_statement` | Rich text | Yes | Must be written as an obligation: system/supplier shall/must. |
| `category` | Enum | Yes | From requirement categories. |
| `sub_category` | Text/enum | Optional | e.g. identity, integration, reporting. |
| `module` | Text/reference | Optional | For ERP or domain modules. |
| `mandatory_flag` | Enum | Yes | Mandatory / desirable / optional / scored. |
| `response_required` | Boolean | Yes | Most technical rows require response. |
| `response_type` | Enum | Yes | yes_no, narrative, numeric, attachment, matrix. |
| `evidence_required` | Boolean | Optional | Triggers evidence upload. |
| `evaluation_mode` | Enum | Yes | pass_fail, scored, informational. |
| `weight` | Decimal | Conditional | Required for scored requirements. |
| `acceptance_test_reference` | Text/reference | Optional | Maps to testing/acceptance rows. |
| `contract_carry_forward` | Boolean | Yes | If true, requirement flows to contract/implementation obligations. |
| `source_trace_id` | Reference | Yes | Official source or tender-instance authoring trace. |

### 7.12 Section VII — Implementation Schedule

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.IMPL` | Implementation Schedule | Milestone and schedule schema | `CONTROLLED_REQUIREMENTS` | Yes | Must support PE-defined milestones and bidder-proposed schedule responses. |

Implementation schedule schema:

| Object | Fields | Notes |
|---|---|---|
| `Implementation Phase` | phase code, title, financial year/period, description, order | Supports phased IT implementations such as NSSF Phase 1 / Phase 2. |
| `Implementation Milestone` | milestone code, title, phase, expected date/relative duration, deliverables, acceptance criteria | Used for tender requirements and contract acceptance. |
| `Implementation Activity` | activity code, milestone, title, responsible party, dependencies, estimated duration | Used for bidder project plan requirements. |
| `Acceptance Gate` | gate code, milestone, sign-off authority, required evidence, certificate template | Generates acceptance certificate obligations. |
| `Payment Milestone Link` | payment milestone, implementation milestone, percentage/amount, conditions | Connects SCC payment schedule to delivery. |
| `Warranty Start Rule` | phase/milestone, trigger event, warranty duration | Supports phase-specific warranty periods. |

Implementation schedule rules:

| Rule code | Rule |
|---|---|
| `IT_IMPL_001` | Every implementation phase must have at least one milestone. |
| `IT_IMPL_002` | Every acceptance milestone must define an acceptance authority and evidence. |
| `IT_IMPL_003` | Payment milestones linked to implementation must sum correctly where percentages are used. |
| `IT_IMPL_004` | Bidder schedule response must cover all PE-defined phases and milestones. |
| `IT_IMPL_005` | Contract carry-forward milestones must be included in the contract implementation appendix. |

### 7.13 Section VIII — System Inventory Tables

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.INVENTORY` | System Inventory Tables | Inventory and price-line schema | `PRICE_SCHEMA` / `CONTROLLED_REQUIREMENTS` | Yes | Inventory items feed technical scope and price schedules. |

System inventory tables:

| Table code | Source title | Completed by | Purpose |
|---|---|---|---|
| `INV.SUPPLY_INSTALL` | System Inventory Table — Supply and Installation Cost Items | PE defines items; bidder prices/responds | One-time supply, installation, software, hardware, services, customization, commissioning. |
| `INV.RECURRENT` | System Inventory Table — Recurrent Cost Items | PE defines items; bidder prices/responds | Licenses, subscriptions, maintenance, support, hosting, recurring services. |

Inventory item fields:

| Field code | Type | Required | Notes |
|---|---|---:|---|
| `item_code` | Text | Yes | Stable item code. |
| `item_category` | Enum | Yes | hardware, software, license, service, training, support, customization, integration, cloud, other. |
| `item_description` | Rich text | Yes | Clear description. |
| `quantity` | Decimal | Conditional | Required when quantity-based. |
| `unit_of_measure` | Text/enum | Conditional | Required when quantity is used. |
| `delivery_phase` | Reference | Optional | Phase/milestone link. |
| `mandatory_flag` | Enum | Yes | Mandatory/desirable/optional. |
| `origin_required` | Boolean | Yes | Drives country-of-origin response. |
| `technical_requirement_link` | Reference | Optional | Links item to requirement row. |
| `price_schedule_link` | Reference | Yes | Determines which price table captures cost. |
| `recurrent_period` | Text/enum | Conditional | Required for recurrent items. |
| `contract_carry_forward` | Boolean | Yes | True for items that must become contract deliverables. |

### 7.14 Section IX — Background and Informational Materials

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.BACKGROUND` | Background and Informational Materials | Controlled informational content | `CONTROLLED_REQUIREMENTS` | Yes, where configured | Should not create bidder obligations unless explicitly marked as requirement. |

Background object types:

| Object | Purpose |
|---|---|
| `IT Background Narrative` | Describes PE context, objectives, business environment. |
| `Existing System Inventory` | Current systems, users, data, integrations, constraints. |
| `Site Information` | Locations where system is implemented or supported. |
| `Training Facility Information` | Available facilities for implementation and training. |
| `Reference Document` | Informational attachments or links. |

Control:

```text
Background content must be classified as informational unless a PE intentionally creates a requirement row.
The renderer must distinguish informational statements from binding requirements.
```

### 7.15 Part 3 container

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.PART3` | Part 3 — Contract | Section container | `SYSTEM_GENERATED` | Yes | Header only. |

### 7.16 Section X — General Conditions of Contract

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.GCC` | General Conditions of Contract | Locked clause tree | `LOCKED_LEGAL` | Yes | Contract-specific values are supplied through SCC and Contract Agreement. |

GCC clause group extraction:

| GCC group | Topic | Extraction object | Parameter dependency |
|---|---|---|---|
| `GCC.1` | Contract and Interpretation / Definitions | Locked clause group | Contract parties, project manager, supplier representative, subcontractors. |
| `GCC.2` | Contract Documents | Locked clause | Contract document order and appendices. |
| `GCC.3` | Interpretation | Locked clause | None. |
| `GCC.4` | Notices | Locked clause | SCC notice addresses. |
| `GCC.5` | Governing Law | Locked clause | SCC governing law if configurable. |
| `GCC.6` | Fraud and Corruption | Locked clause | Declaration forms and audit. |
| `GCC.7` | Scope of the System | Locked clause | Contract requirements and inventory carry-forward. |
| `GCC.8` | Commencement and Operational Acceptance | Locked clause | Implementation schedule and acceptance gates. |
| `GCC.9` | Supplier Responsibilities | Locked clause | Project plan, deliverables, conformance. |
| `GCC.10` | Procuring Entity Responsibilities | Locked clause | SCC/requirements obligations. |
| `GCC.11-14` | Price, payment, securities, taxes | Locked clause group | SCC payment/security/tax parameters. |
| `GCC.15-17` | Copyright, software licenses, confidential information | Locked clause group | IP forms, SCC IP parameters. |
| `GCC.18-20` | Representatives, project plan, subcontracting | Locked clause group | Contract appendices. |
| `GCC.21-27` | Design, delivery, installation, testing, acceptance | Locked clause group | Requirements, inventory, implementation schedule. |
| `GCC.28-30` | Operational acceptance, defects, guarantees | Locked clause group | Acceptance gates and warranty/support parameters. |
| `GCC.31-33` | IPR warranty, IPR indemnity, limitation of liability | Locked clause group | SCC IP and liability parameters. |
| `GCC.34-37` | Ownership, care of system, indemnification, insurance | Locked clause group | SCC insurance/risk parameters. |
| `GCC.38-43` | Force majeure, changes, extension, termination, assignment, disputes | Locked clause group | SCC dispute/change/adjudicator parameters. |

### 7.17 Section XI/XII — Special Conditions of Contract

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.SCC` | Special Conditions of Contract | Contract parameter table schema | `CONFIG_TABLE` | Yes | SCC values supplement GCC and become contract data. |

SCC parameter groups:

| Group code | Group title | Representative parameters |
|---|---|---|
| `SCC.CONTRACT_INTERPRETATION` | Contract and interpretation | PE legal identity, governing law, language, notices, project manager. |
| `SCC.SUBJECT_MATTER` | Subject matter of contract | system description, scope, site, operational acceptance deadline. |
| `SCC.PAYMENT` | Payment | payment milestones, currency, retention, taxes, invoice requirements. |
| `SCC.IP` | Intellectual property | software categories, custom materials, license terms, ownership transfer. |
| `SCC.SUPPLY_INSTALL_ACCEPTANCE` | Supply, installation, testing, commissioning, acceptance | schedule, acceptance gates, test obligations. |
| `SCC.GUARANTEES_LIABILITIES` | Guarantees and liabilities | warranty period, defect liability, functional guarantees, limitation of liability. |
| `SCC.RISK` | Risk distribution | insurance, care of system, indemnities. |
| `SCC.CHANGE` | Change in contract elements | change order authority, process, forms. |
| `SCC.DISPUTES` | Settlement of disputes | adjudicator, arbitration/courts, dispute timelines. |

SCC parameter extraction:

| Parameter code | Label | Type | Required | Contract carry-forward |
|---|---|---|---:|---:|
| `scc.procuring_entity.legal_name` | Procuring Entity legal name | Text | Yes | Yes |
| `scc.project_manager.name` | Project Manager | Text/person | Yes | Yes |
| `scc.notice.pe_address` | PE notice address | Address | Yes | Yes |
| `scc.notice.supplier_address` | Supplier notice address | Address | Award stage | Yes |
| `scc.system.brief_description` | System description | Multiline text | Yes | Yes |
| `scc.operational_acceptance_deadline` | Operational acceptance deadline | Date/duration | Yes | Yes |
| `scc.payment.milestones` | Payment milestones | Repeatable table | Yes | Yes |
| `scc.performance_security.amount_or_percent` | Performance security | Money/percent | Yes | Yes |
| `scc.advance_payment_security.required` | Advance payment security required | Boolean | Conditional | Yes |
| `scc.retention.required` | Retention applies | Boolean | Conditional | Yes |
| `scc.warranty.period` | Warranty period | Duration | Yes | Yes |
| `scc.defect_liability.period` | Defect liability period | Duration | Optional/conditional | Yes |
| `scc.functional_guarantee.items` | Functional guarantee items | Repeatable table | Optional | Yes |
| `scc.ip.software_license_terms` | Software license terms | Rich text/reference | Yes | Yes |
| `scc.ip.custom_materials_ownership` | Custom materials ownership | Enum/rich text | Yes | Yes |
| `scc.confidentiality.period` | Confidentiality period | Duration/text | Optional | Yes |
| `scc.insurance.requirements` | Insurance requirements | Repeatable table | Conditional | Yes |
| `scc.change_order_authority` | Change order approval authority | Role/person | Yes | Yes |
| `scc.dispute.adjudicator` | Adjudicator | Person/org | Conditional | Yes |
| `scc.dispute.forum` | Dispute forum | Enum/text | Yes | Yes |

### 7.18 Section XII/XIII — Contract Forms

| Canonical ID | Source area | Extract as | Mutability | Rendered to bidders? | Notes |
|---|---|---|---|---:|---|
| `IT.CONTRACT_FORMS` | Contract Forms | Contract artifact schemas and render blocks | `GENERATED_CONTRACT` | Yes / award-stage | Generated after award using tender, supplier, award, and SCC data. |

Contract form inventory:

| Contract form code | Source title | Generation stage | Data sources |
|---|---|---|---|
| `CONTRACT.NOTICE_INTENTION_AWARD` | Notification of Intention to Award | Award recommendation / intention | Evaluation result, standstill, successful/unsuccessful tenderers. |
| `CONTRACT.LETTER_AWARD` | Letter of Award | After award approval | Award data, contract price, performance security. |
| `CONTRACT.AGREEMENT` | Contract Agreement | Contract finalization | PE data, supplier data, system description, price schedules, SCC/GCC. |
| `CONTRACT.APPENDIX_SUPPLIER_REP` | Appendix 1 — Supplier's Representative | Contract finalization | Supplier representative form. |
| `CONTRACT.APPENDIX_ADJUDICATOR` | Appendix 2 — Adjudicator | Contract finalization | SCC/adjudicator data. |
| `CONTRACT.APPENDIX_SUBCONTRACTORS` | Appendix 3 — Approved Subcontractors | Contract finalization | Approved subcontractor disclosures. |
| `CONTRACT.APPENDIX_SOFTWARE_CATEGORIES` | Appendix 4 — Categories of Software | Contract finalization | IP forms and evaluated tender. |
| `CONTRACT.APPENDIX_CUSTOM_MATERIALS` | Appendix 5 — Custom Materials | Contract finalization | IP forms and negotiated clarifications. |
| `CONTRACT.APPENDIX_REVISED_PRICES` | Appendix 6 — Revised Price Schedules | Contract finalization | Original or revised price schedules if permitted. |
| `CONTRACT.APPENDIX_FINALIZATION_MINUTES` | Appendix 7 — Minutes of Contract Finalization Discussions and Agreed Amendments | Contract finalization | Contract finalization workflow. |
| `CONTRACT.PERFORMANCE_SECURITY` | Performance Security Forms | Post-award | Award data and security requirement. |
| `CONTRACT.ADVANCE_PAYMENT_SECURITY` | Advance Payment Security Forms | Post-award if applicable | Advance payment terms. |
| `CONTRACT.INSTALLATION_ACCEPTANCE_CERT` | Installation and Acceptance Certificates | Implementation | Milestone/acceptance data. |
| `CONTRACT.CHANGE_ORDER_FORMS` | Change Order Procedures and Forms | Contract administration | Change order workflow. |
| `CONTRACT.BENEFICIAL_OWNERSHIP` | Beneficial Ownership Disclosure Form | Award/contract | Supplier beneficial ownership data. |

---

## 8. Price Schedule Extraction Matrix

The IT STD price model is not a WORKS BoQ. It must be implemented as an IT price schedule model with supply/installation and recurrent components.

### 8.1 Price schedule objects

| Object | Purpose |
|---|---|
| `IT Price Schedule Schema` | Defines price tables activated for a tender. |
| `IT Price Schedule Table` | A specific price table, e.g. Grand Summary or Recurrent Sub-Table. |
| `IT Price Schedule Line` | A line to be priced by bidder. |
| `IT Price Component` | Computed component of evaluated price. |
| `IT Recurrent Cost Period` | Year, warranty period, support period, subscription period, etc. |
| `IT Price Evaluation Rule` | Calculates grand total, recurrent total, evaluated price, discounts, taxes. |

### 8.2 Tables

| Table code | Title | Line type | Completed by | Calculation role |
|---|---|---|---|---|
| `PRICE.GRAND_SUMMARY` | Grand Summary Cost Table | Summary | Bidder / computed | Final tender price summary. |
| `PRICE.SUPPLY_INSTALL_SUMMARY` | Supply and Installation Cost Summary Table | Summary | Bidder / computed | One-time cost summary. |
| `PRICE.RECURRENT_SUMMARY` | Recurrent Cost Summary Table | Summary | Bidder / computed | Recurrent cost summary. |
| `PRICE.SUPPLY_INSTALL_SUBTABLE` | Supply and Installation Cost Sub-Table | Detailed line | Bidder | Detail for supply/install items. |
| `PRICE.RECURRENT_SUBTABLE` | Recurrent Cost Sub-Table | Detailed line | Bidder | Detail for recurrent items. |
| `PRICE.COUNTRY_ORIGIN_CODE` | Country of Origin Code Table | Reference/response | Bidder | Origin reporting and eligibility. |

### 8.3 Price line fields

| Field code | Type | Required | Notes |
|---|---|---:|---|
| `line_no` | Integer/text | Yes | Stable display order. |
| `item_code` | Text/reference | Yes | Links inventory/requirement item. |
| `description` | Text/rich text | Yes | From PE inventory or bidder detail where allowed. |
| `origin_country` | Country | Conditional | Required if origin reporting applies. |
| `quantity` | Decimal | Conditional | Required for quantity-based items. |
| `unit` | Text/enum | Conditional | Required if quantity is used. |
| `unit_price` | Money | Conditional | Required for unit-priced lines. |
| `line_total` | Money | Yes | Computed or bidder-entered depending table mode. |
| `currency` | Currency | Yes | Controlled by TDS. |
| `tax_exclusive_amount` | Money | Conditional | Required where VAT/tax separated. |
| `tax_amount` | Money | Conditional | Required where tax separated. |
| `tax_inclusive_amount` | Money | Conditional | Computed. |
| `discount` | Money/percent | Optional | Only where discounts allowed. |
| `recurrent_period` | Text/enum | Conditional | Required for recurrent line. |
| `warranty_included` | Boolean | Optional | Useful for support/maintenance distinction. |
| `notes` | Text | Optional | Bidder explanation. |

### 8.4 Price validation rules

| Rule code | Rule | Severity |
|---|---|---|
| `IT_PRICE_001` | Grand summary must equal sum of activated summary tables. | Blocker |
| `IT_PRICE_002` | Supply/install summary must equal its sub-table total. | Blocker |
| `IT_PRICE_003` | Recurrent summary must equal its sub-table total. | Blocker |
| `IT_PRICE_004` | Currency must match TDS unless foreign currencies are allowed. | Blocker |
| `IT_PRICE_005` | Price-adjustable bid must be rejected where price adjustment is not permitted. | Blocker |
| `IT_PRICE_006` | Required inventory items must appear in the relevant price schedule. | Blocker |
| `IT_PRICE_007` | VAT/tax fields must be completed according to tender tax policy. | Error |
| `IT_PRICE_008` | Country of origin must be provided where origin reporting is required. | Error |
| `IT_PRICE_009` | Negative price lines are not permitted unless explicitly allowed by discount rules. | Error |
| `IT_PRICE_010` | Evaluated price must be reproducible from published price schedule rules. | Blocker |

---

## 9. Requirement Composer Extraction Matrix

### 9.1 Composer screens

| Composer screen | Purpose | Output objects |
|---|---|---|
| System Overview | Define system title, purpose, scope, users, sites, existing environment | Requirement set, background narrative |
| Business/Functional Requirements | Define business processes and required functions | Functional requirement rows |
| Architectural Requirements | Define hosting, security, identity, integrations, environments | Architectural/security/integration rows |
| Performance Requirements | Define measurable performance targets | Performance rows and test references |
| Service Specifications | Define implementation, configuration, customization, support services | Service rows, deliverables |
| Technology Specifications | Define technology, software, hardware, platform, cloud, network needs | Technology rows and inventory links |
| Data Migration | Define source systems, data sets, cleansing, migration, validation | Data migration rows |
| Testing and Acceptance | Define testing stages, UAT, acceptance certificates | Test and acceptance rows |
| Training and Knowledge Transfer | Define audiences, training scope, materials, signoff | Training rows |
| Documentation | Define required project and technical documents | Documentation rows |
| Warranty and Support | Define warranty, SLA, support, escalation, maintenance | Warranty/support rows |
| Implementation Schedule | Define phases, milestones, acceptance gates | Implementation phase/milestone rows |
| System Inventory | Define supply/install and recurrent inventory items | Inventory rows |
| Conformance Matrix Preview | Shows bidder response form generated from requirements | Bidder response schema |

### 9.2 Requirement-to-output mapping

| Input object | Published tender output | Bidder output | Evaluation output | Contract output |
|---|---|---|---|---|
| Functional requirement | Technical requirements section | Conformance response | Technical compliance finding | Contract scope/system requirement |
| Architectural requirement | Technical requirements section | Architecture proposal | Architecture compliance finding | Design/engineering obligation |
| Performance requirement | Technical requirements section | Proposed performance / proof | Performance compliance finding | Functional guarantee / acceptance test |
| Service specification | Service specification section | Methodology and work plan | Technical service score/finding | Supplier service obligation |
| Technology specification | Technology specification section | Make/model/version/approach | Technical compliance finding | Inventory/technical appendix |
| Implementation milestone | Implementation schedule | Bidder implementation plan | Schedule adequacy finding | Contract implementation schedule |
| Inventory item | System inventory and price schedule | Price and item response | Price/compliance finding | Contract inventory/deliverable |
| Training requirement | Training requirements | Training plan | Training score/finding | Training deliverable |
| Documentation requirement | Documentation standards | Documentation commitment | Documentation compliance | Deliverable list |
| Warranty/support requirement | Support requirements | Support plan/SLA | Support score/finding | Warranty/SLA obligation |

---

## 10. Rule Extraction Matrix

### 10.1 Rule object structure

Each rule must be stored as a production `STD Rule` with:

| Field | Required |
|---|---:|
| Rule code | Yes |
| Rule title | Yes |
| Rule type | Yes |
| Rule scope | Yes |
| Trigger stage | Yes |
| Severity | Yes |
| Expression or service hook | Yes |
| Affected fields/objects | Yes |
| Legal/source basis | Yes |
| Error/warning message | Yes |
| Smoke test reference | Yes for blocker/error rules |

### 10.2 Initial IT STD rule inventory

| Rule code | Title | Scope | Trigger | Severity |
|---|---|---|---|---|
| `IT_CORE_001` | ITT is locked | Template/tender | Edit attempt | Blocker |
| `IT_CORE_002` | GCC is locked | Template/tender | Edit attempt | Blocker |
| `IT_CORE_003` | TDS required fields complete | Tender STD instance | Ready for review / generation | Blocker |
| `IT_CORE_004` | SCC required fields complete | Tender STD instance | Ready for publication / contract generation | Blocker |
| `IT_CORE_005` | Issued tender excludes preface and preparation guidance | Render | Tender generation | Blocker |
| `IT_CORE_006` | Active STD version immutable | Template version | Edit attempt | Blocker |
| `IT_CORE_007` | Published generated bundle immutable | Tender bundle | Edit/regenerate attempt | Blocker |
| `IT_CORE_008` | Addendum required after publication | Tender bundle | Change request | Blocker |
| `IT_CORE_009` | Tender bound to active STD version | Tender creation | Bind STD | Blocker |
| `IT_TDS_001` | JV maximum members provided | TDS | Validation | Error |
| `IT_TDS_002` | JV maximum above five flagged | TDS | Validation | Warning/Error depending policy |
| `IT_TDS_003` | Clarification deadline before submission deadline | TDS | Validation | Blocker |
| `IT_TDS_004` | Opening date/time not before submission deadline | TDS | Validation | Blocker |
| `IT_TDS_005` | Alternative tender behavior matches TDS | Tender/bid | Submission/evaluation | Blocker |
| `IT_TDS_006` | Currency behavior matches national/international setup | TDS/price | Validation | Error |
| `IT_TDS_007` | Tender security amount within configured statutory cap | TDS | Validation | Blocker |
| `IT_TDS_008` | Reservation group required if reservation enabled | TDS | Validation | Blocker |
| `IT_TDS_009` | Margin method required if margin enabled | TDS/evaluation | Validation | Blocker |
| `IT_REQ_001` | Mandatory requirement must have response mode | Requirements | Validation | Error |
| `IT_REQ_002` | Scored requirement must have weight | Requirements/evaluation | Validation | Error |
| `IT_REQ_003` | Requirement code unique within tender | Requirements | Save/import | Blocker |
| `IT_REQ_004` | Contract carry-forward requirements included in contract scope | Contract generation | Generation | Blocker |
| `IT_REQ_005` | Informational background cannot be evaluated unless converted to requirement | Evaluation | Criteria generation | Blocker |
| `IT_EVAL_001` | Evaluation criteria published before submission | Evaluation | Publication | Blocker |
| `IT_EVAL_002` | No hidden evaluation criteria | Evaluation | Evaluation setup | Blocker |
| `IT_EVAL_003` | Technical evaluation before financial evaluation where required | Evaluation | Stage transition | Blocker |
| `IT_EVAL_004` | Pass mark required if scored technical evaluation enabled | Evaluation | Validation | Blocker |
| `IT_EVAL_005` | Total scoring weights sum to configured total | Evaluation | Validation | Blocker |
| `IT_EVAL_006` | Mandatory preliminary failures disqualify where configured | Evaluation | Stage transition | Blocker |
| `IT_PRICE_001` | Grand summary total reconciles | Price | Submission/evaluation | Blocker |
| `IT_PRICE_002` | Recurrent totals reconcile | Price | Submission/evaluation | Blocker |
| `IT_PRICE_003` | Price schedule covers mandatory inventory | Price/inventory | Submission/evaluation | Blocker |
| `IT_CONTRACT_001` | Contract agreement uses awarded supplier and evaluated price | Contract | Contract generation | Blocker |
| `IT_CONTRACT_002` | Contract document order preserved | Contract | Generation | Blocker |
| `IT_CONTRACT_003` | Software categories appendix generated where IP forms used | Contract | Generation | Error |
| `IT_CONTRACT_004` | Custom materials appendix generated where custom materials declared | Contract | Generation | Error |
| `IT_CONTRACT_005` | Acceptance certificates derive from acceptance gates | Contract administration | Certificate generation | Error |

---

## 11. Render Block Extraction Matrix

### 11.1 Render block types

| Render block type | Purpose |
|---|---|
| `STATIC_LOCKED_TEXT` | Renders locked clauses from source. |
| `PARAMETERIZED_TEXT` | Renders locked text with controlled variables. |
| `CONFIG_TABLE` | Renders TDS/SCC tables. |
| `FORM_SCHEMA` | Renders bidder forms. |
| `PRICE_TABLE` | Renders price schedules. |
| `REQUIREMENT_MATRIX` | Renders technical requirements and conformance matrix. |
| `IMPLEMENTATION_TABLE` | Renders implementation schedule. |
| `INVENTORY_TABLE` | Renders system inventory tables. |
| `EVALUATION_MATRIX` | Renders evaluation criteria. |
| `CONTRACT_FORM` | Renders award/contract forms. |
| `AUDIT_SUMMARY` | Renders internal audit and source trace summaries where authorized. |

### 11.2 Render map

| Render block code | Output section | Input objects | Output stage |
|---|---|---|---|
| `RB.IT.ISSUE_PAGE` | Issue page | Tender identity, PE profile | Tender generation |
| `RB.IT.INVITATION` | Invitation to Tender | Invitation parameters, TDS | Tender generation |
| `RB.IT.PART1_HEADER` | Part 1 header | Section metadata | Tender generation |
| `RB.IT.ITT` | ITT | Locked clause tree | Tender generation |
| `RB.IT.TDS` | TDS | TDS parameter values | Tender generation |
| `RB.IT.EVAL` | Evaluation and Qualification Criteria | Evaluation schema | Tender generation |
| `RB.IT.FORMS` | Tendering Forms | Form schemas | Tender generation / bidder portal |
| `RB.IT.PRICE_FORMS` | Price Schedule Forms | Price schemas, inventory | Tender generation / bidder portal |
| `RB.IT.REQ` | Requirements of Information System | Requirement sets/background | Tender generation |
| `RB.IT.TECH` | Technical Requirements | Requirement rows | Tender generation / bidder conformance |
| `RB.IT.IMPL` | Implementation Schedule | Milestones and phases | Tender generation |
| `RB.IT.INVENTORY` | System Inventory Tables | Inventory items | Tender generation / price forms |
| `RB.IT.BACKGROUND` | Background and Informational Materials | Background objects | Tender generation |
| `RB.IT.GCC` | GCC | Locked clause tree | Tender generation / contract |
| `RB.IT.SCC` | SCC | SCC parameter values | Tender generation / contract |
| `RB.IT.CONTRACT_FORMS` | Contract Forms | Contract schemas | Tender generation preview / award generation |
| `RB.IT.NOTICE_INTENTION_AWARD` | Notification of Intention to Award | Evaluation/award data | Award |
| `RB.IT.LETTER_AWARD` | Letter of Award | Award data | Award |
| `RB.IT.CONTRACT_AGREEMENT` | Contract Agreement | Award, SCC, supplier, price, requirements | Contract formation |
| `RB.IT.ACCEPTANCE_CERT` | Installation and Acceptance Certificates | Acceptance gates | Contract administration |
| `RB.IT.CHANGE_ORDER` | Change Order Forms | Change workflow | Contract administration |

---

## 12. NSSF ERP Calibration Matrix

The NSSF ERP tender should be used to test whether the IT STD package can support real tenders.

### 12.1 Mapping

| NSSF source area | Official IT STD surface | Engine object |
|---|---|---|
| Cover page with tender number, closing date, PE contact | Issue page / Invitation / TDS | Tender identity parameters |
| Invitation to Tender | Invitation to Tender | Rendered invitation parameters |
| Part 1 Tendering Procedures | ITT/TDS/Evaluation/Forms | Tender-specific configuration using IT STD locked structure |
| TDS table | TDS | `Tender STD Configuration Value` rows |
| Mandatory requirements | Evaluation and Qualification Criteria | Preliminary responsiveness criteria |
| Technical qualification criteria | Evaluation and Qualification Criteria | Qualification criteria and evidence requirements |
| Technical scoring criteria | Evaluation and Qualification Criteria | Scored technical evaluation schema |
| Tendering forms | Tendering Forms | Form schemas / form responses |
| ERP background and objectives | Background and Requirements | Background narrative and requirement set |
| Scope of work / implementation phases | Requirements / Implementation Schedule | Implementation phases and milestones |
| Technical requirements by ERP module | Technical Requirements | Requirement rows grouped by module |
| Compliance matrix | Technical Requirements / Conformance Form | Bidder conformance response schema |
| Testing and acceptance | Testing and Acceptance requirements | Acceptance gates and test requirements |
| Training and knowledge transfer | Training requirements | Training requirement rows |
| Implementation schedule/location | Implementation Schedule | Milestone schema and phase schedule |
| Hardware/cloud infrastructure requirements | Technology specifications | Technology requirement rows |
| Warranty/support/maintenance | Warranty and Support | Support requirement and SCC warranty parameters |
| Schedule of requirements | System Inventory Tables | Inventory items |
| Price schedule of requirements | Price Schedule Forms | Price tables |
| GCC/SCC/Contract forms | GCC/SCC/Contract Forms | Locked GCC, SCC parameters, contract schemas |

### 12.2 Calibration observations

| Observation | Engine implication |
|---|---|
| NSSF uses Professional Indemnity cover of KES 500,000. | The engine must allow tender security/security-like obligations to be configured through controlled security/evidence types, subject to procurement/legal review. |
| NSSF specifies Microsoft Dynamics 365 Business Central and Microsoft partner authorization. | Product/vendor-specific requirements must be allowed only as tender-instance technical/evidence criteria, with governance review because they may affect competition. |
| NSSF uses mandatory preliminary requirements. | The evaluation schema must support pass/fail mandatory requirements with disqualification behavior. |
| NSSF uses technical qualification criteria and a scored technical evaluation out of 100 with a pass mark. | The evaluation model must support qualification thresholds and weighted scoring. |
| NSSF has many module-specific requirements. | Requirements composer must support grouped technical matrices with codes, mandatory flag, compliance response, and bidder reference pages. |
| NSSF uses two financial-year implementation phases. | Implementation schedule must support phases, milestones, dependencies, and payment links. |
| NSSF includes testing, UAT, acceptance certificates, and sign-offs. | Acceptance gates must be first-class objects and carry into contract administration. |
| NSSF includes training, documentation, support, warranty, and maintenance. | These must be standard IT requirement categories, not ad hoc notes. |
| NSSF tender appears shorter than the full official IT STD. | The engine must support complete official STD generation, while allowing authorized omission/configuration where the STD permits. |

### 12.3 NSSF caution list

These items require governance review when using the NSSF tender as a test case:

| Item | Risk | Treatment |
|---|---|---|
| Product-specific Microsoft Dynamics requirement | May restrict competition if not justified | Require PE justification and approval note. |
| Professional indemnity replacing tender security wording | May require legal/procurement validation | Model as security/evidence type; do not hard-code as universal IT STD rule. |
| Simplified GCC compared to official source | May omit official legal protections | Use official IT STD as master; NSSF simplified text is fixture only. |
| Vendor authorization requirement | Potentially valid but competition-sensitive | Store as mandatory evidence criterion with approval trace. |
| Specific pension/RBA module requirements | Domain-specific | Store as tender requirements, not STD master requirements. |
| Two-phase payment milestones | Legitimate tender-specific SCC/payment data | Model through implementation/payment links. |

---

## 13. Source Traceability Requirements

Every extracted object must include source traceability.

### 13.1 Trace fields

| Field | Applies to | Required |
|---|---|---:|
| `source_document_id` | All source-derived objects | Yes |
| `source_document_hash` | All source-derived objects | Yes |
| `source_page_start` | Clauses/sections/forms/rules where known | Yes where available |
| `source_page_end` | Clauses/sections/forms/rules where known | Yes where available |
| `source_section_label` | Sections/clauses/forms | Yes |
| `source_heading` | Sections/clauses/forms | Yes |
| `source_text_hash` | Clauses/static text | Yes |
| `source_extraction_confidence` | Extracted objects | Yes |
| `traceability_mode` | All objects | Yes: `source_exact`, `source_derived`, `system_generated`, `tender_authored` |
| `traceability_note` | Derived/tender-authored objects | Conditional |

### 13.2 Traceability modes

| Mode | Meaning | Example |
|---|---|---|
| `source_exact` | Object directly extracted from source text | ITT clause text, GCC clause text. |
| `source_derived` | Object derived from source guidance or structure | Tender security max rule from preparation guidance. |
| `system_generated` | Created by engine to support operation | Audit summary, hash manifest. |
| `tender_authored` | Created by PE within controlled template surface | ERP module requirement rows. |
| `calibration_fixture` | Derived from real tender for testing only | NSSF ERP sample values. |

---

## 14. Import Package Module Plan

The final IT STD package should be split into import modules.

```text
KE-PPRA-IT-2022-04/
  manifest.json
  source_documents.json
  source_trace.json
  section_hierarchy.json
  clauses_itt.json
  clauses_gcc.json
  parameters_tds.json
  parameters_scc.json
  rules.json
  forms_tendering.json
  form_fields.json
  evidence_requirements.json
  price_schedule_schema.json
  requirement_schema.json
  implementation_schedule_schema.json
  system_inventory_schema.json
  evaluation_schema.json
  contract_schema.json
  render_blocks.json
  smoke_contracts.json
  nssf_calibration_fixture.json
```

### 14.1 Package module responsibilities

| Module | Responsibility |
|---|---|
| `manifest.json` | Package identity, version, authority, hashes, dependencies. |
| `source_documents.json` | Registered source document metadata. |
| `source_trace.json` | Page/section/source trace anchors. |
| `section_hierarchy.json` | Canonical section tree and render order. |
| `clauses_itt.json` | Locked ITT clause tree. |
| `clauses_gcc.json` | Locked GCC clause tree. |
| `parameters_tds.json` | TDS parameter definitions and validations. |
| `parameters_scc.json` | SCC parameter definitions and validations. |
| `rules.json` | Validation, activation, calculation, workflow, and render rules. |
| `forms_tendering.json` | Form inventory and activation. |
| `form_fields.json` | Field-level schemas for bidder forms. |
| `evidence_requirements.json` | Evidence types linked to forms/evaluation criteria. |
| `price_schedule_schema.json` | IT price table definitions and calculation rules. |
| `requirement_schema.json` | Requirement composer categories and fields. |
| `implementation_schedule_schema.json` | Phases, milestones, acceptance gates. |
| `system_inventory_schema.json` | Supply/install and recurrent inventory schemas. |
| `evaluation_schema.json` | Evaluation stages, criteria families, scoring/pass-fail structures. |
| `contract_schema.json` | Contract forms, appendices, carry-forward rules. |
| `render_blocks.json` | Render block inventory and section mapping. |
| `smoke_contracts.json` | Package activation and regression tests. |
| `nssf_calibration_fixture.json` | Real tender sample values for test import only. |

---

## 15. Smoke Contracts for IT STD Package

### 15.1 Package import smoke tests

| Smoke code | Test | Expected result |
|---|---|---|
| `IT_SMOKE_IMPORT_001` | Import package manifest | Package imports with correct identity. |
| `IT_SMOKE_IMPORT_002` | Import section hierarchy | All canonical sections created in correct order. |
| `IT_SMOKE_IMPORT_003` | Import locked ITT and GCC | Locked sections created with hashes and immutability. |
| `IT_SMOKE_IMPORT_004` | Import TDS/SCC parameters | Parameter schemas created with required flags and validations. |
| `IT_SMOKE_IMPORT_005` | Import form schemas | Tendering forms and fields created. |
| `IT_SMOKE_IMPORT_006` | Import requirements schema | Requirement composer categories available. |
| `IT_SMOKE_IMPORT_007` | Import price schema | Price schedules and calculation rules created. |
| `IT_SMOKE_IMPORT_008` | Import evaluation schema | Evaluation stages and criteria families created. |
| `IT_SMOKE_IMPORT_009` | Import contract schema | Contract forms and appendices created. |
| `IT_SMOKE_IMPORT_010` | Import render blocks | Render blocks available and mapped to sections. |

### 15.2 Activation smoke tests

| Smoke code | Test | Expected result |
|---|---|---|
| `IT_SMOKE_ACTIVATE_001` | Activate package with missing source hash | Blocked. |
| `IT_SMOKE_ACTIVATE_002` | Activate package with editable ITT | Blocked. |
| `IT_SMOKE_ACTIVATE_003` | Activate package with editable GCC | Blocked. |
| `IT_SMOKE_ACTIVATE_004` | Activate package with missing TDS required parameters | Blocked. |
| `IT_SMOKE_ACTIVATE_005` | Activate package with missing render blocks | Blocked. |
| `IT_SMOKE_ACTIVATE_006` | Activate package after all blockers resolved | Approved/Active allowed. |

### 15.3 Tender generation smoke tests

| Smoke code | Test | Expected result |
|---|---|---|
| `IT_SMOKE_TENDER_001` | Create tender from active IT STD | Tender binds to active version. |
| `IT_SMOKE_TENDER_002` | Generate tender with incomplete TDS | Blocked with findings. |
| `IT_SMOKE_TENDER_003` | Generate tender with complete TDS/SCC and requirements | Bundle generated and hashed. |
| `IT_SMOKE_TENDER_004` | Attempt to edit locked ITT in tender | Blocked. |
| `IT_SMOKE_TENDER_005` | Attempt to edit GCC in tender | Blocked. |
| `IT_SMOKE_TENDER_006` | Publish generated bundle | Bundle immutable after publication. |
| `IT_SMOKE_TENDER_007` | Modify published tender requirement | Addendum required. |

### 15.4 Bidder response smoke tests

| Smoke code | Test | Expected result |
|---|---|---|
| `IT_SMOKE_BID_001` | Bidder opens generated conformance matrix | All published requirement rows visible. |
| `IT_SMOKE_BID_002` | Bidder submits incomplete mandatory form | Submission blocked or flagged per tender rules. |
| `IT_SMOKE_BID_003` | Price summary mismatch | Submission blocked. |
| `IT_SMOKE_BID_004` | Missing mandatory evidence | Submission blocked or evaluation failure depending configuration. |
| `IT_SMOKE_BID_005` | Alternative tender submitted when not permitted | Submission blocked. |

### 15.5 Evaluation smoke tests

| Smoke code | Test | Expected result |
|---|---|---|
| `IT_SMOKE_EVAL_001` | Preliminary mandatory failure | Tender disqualified where configured. |
| `IT_SMOKE_EVAL_002` | Technical score below pass mark | Tender does not proceed to financial stage where configured. |
| `IT_SMOKE_EVAL_003` | Hidden criterion added after publication | Blocked. |
| `IT_SMOKE_EVAL_004` | Financial evaluation computes from price schedules | Evaluated price reproducible. |
| `IT_SMOKE_EVAL_005` | Award recommendation uses lowest evaluated responsive tender | Correct award candidate selected. |

### 15.6 Contract generation smoke tests

| Smoke code | Test | Expected result |
|---|---|---|
| `IT_SMOKE_CONTRACT_001` | Generate Letter of Award | Uses award data and performance security requirement. |
| `IT_SMOKE_CONTRACT_002` | Generate Contract Agreement | Uses PE, supplier, system description, price, SCC, appendices. |
| `IT_SMOKE_CONTRACT_003` | Generate software categories appendix | Uses IP form responses. |
| `IT_SMOKE_CONTRACT_004` | Generate acceptance certificate | Uses acceptance gate and milestone. |
| `IT_SMOKE_CONTRACT_005` | Generate change order form | Uses change order workflow. |

---

## 16. Data Objects to Seed for IT STD

The following records must be created during seed-package import.

| Domain object | Minimum seed records |
|---|---:|
| `STD Template Family` | 1 |
| `STD Template Version` | 1 |
| `STD Source Document` | 1 |
| `STD Section` | 21+ |
| `STD Clause` | Complete ITT and GCC clause trees |
| `STD Parameter` | All TDS and SCC fields |
| `STD Rule` | Initial rule inventory plus source-derived rules |
| `STD Form Schema` | All tendering and contract forms |
| `STD Form Field` | All field-level form schemas |
| `STD Evidence Requirement` | Qualification/evaluation/form-linked evidence definitions |
| `STD Requirement Schema` | Requirement categories and row schemas |
| `STD Price Schedule Schema` | IT price schedules and calculations |
| `STD Evaluation Schema` | Evaluation stages and criteria families |
| `STD Contract Schema` | Contract forms and appendices |
| `STD Render Block` | All render map entries |
| `STD Smoke Contract` | All package/tender/bid/eval/contract smoke tests |

---

## 17. Implementation Readiness Checklist

Before building the IT seed package, confirm:

| Checklist item | Required status |
|---|---|
| STD Engine Core domain model complete | Yes |
| Governance/state model complete | Yes |
| Roles/permissions complete | Yes |
| Import/export package schema complete | Yes |
| Render block engine defined | Yes |
| Validation engine defined | Yes |
| Source trace model defined | Yes |
| Hashing model defined | Yes |
| Addendum model defined | Yes |
| Tender binding model defined | Yes |
| Official IT STD source hash recorded | Pending during package build |
| Official IT STD section/page anchors extracted | Pending during package build |
| Locked ITT/GCC text extraction completed | Pending during package build |
| TDS/SCC parameter extraction completed | Pending during package build |
| Form field extraction completed | Pending during package build |
| Price schedule schema completed | Pending during package build |
| Requirements schema completed | Drafted here; to be encoded in seed package |
| NSSF calibration fixture encoded | Pending during package build |
| Smoke contracts encoded | Drafted here; to be encoded in seed package |

---

## 18. Next Artifact

The next artifact should be:

```text
STD for Procurement of Information Technology — Seed Package Specification
```

That document should convert this extraction matrix into actual import-package structures, including:

1. Canonical IDs.
2. JSON module shapes.
3. Required seed records.
4. Import order.
5. Validation order.
6. Hashing requirements.
7. Render block definitions.
8. Test fixtures.
9. NSSF calibration fixture mapping.
10. Cursor implementation prompts for creating the actual seed package.

After the seed package specification is approved, the following artifact should be produced:

```text
KE-PPRA-IT-2022-04 Seed Package
```

That package will be the first importable production STD package for the generalized STD Engine.

---

## 19. Non-Negotiable Constraints

1. Do not hard-code NSSF ERP requirements into the IT STD master package.
2. Do not hard-code Microsoft Dynamics, pension scheme requirements, or Professional Indemnity as universal IT STD behavior.
3. Do not permit direct editing of ITT or GCC text in tender configuration.
4. Do not allow evaluation criteria to be added after publication except through addendum governance.
5. Do not allow generated tender bundles to be modified after publication.
6. Do not generate a contract from a tender unless the tender is bound to a known STD version and award result.
7. Do not treat background information as an evaluated requirement unless it is explicitly converted into a requirement row.
8. Do not treat the price schedule as a WORKS BoQ.
9. Do not omit source traceability for extracted objects.
10. Do not activate the IT STD package until all blocker smoke contracts pass.

---

## 20. Summary

The IT STD can be implemented cleanly in the generalized STD Engine if it is represented as a structured package of sections, clauses, parameters, rules, forms, requirement schemas, price schedules, evaluation schemas, contract schemas, and render blocks.

The key design decision is to separate:

1. **Official STD master structure** — PPRA source-controlled and versioned.
2. **Tender-specific configuration** — completed by a PE through controlled UI.
3. **Bidder response schemas** — generated from the active STD version and tender configuration.
4. **Evaluation matrices** — generated from published criteria and requirements.
5. **Contract artifacts** — generated from award, evaluated tender, SCC, requirements, price schedules, and contract appendices.

This extraction matrix is now ready to be converted into the IT Seed Package Specification.
