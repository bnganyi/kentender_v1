# STD-CHG-001 — Clean Manual STD Configuration and Runtime

| Control | Value |
|---|---|
| Document ID | STD-CHG-001 |
| Version | 1.3 |
| Date | 25 August 2026 |
| Status | Proposed for approval |
| Module | Standard Tender Document Configuration |
| First package | PPRA Standard Tender Document for Procurement of Information Technology |
| Implementation posture | Greenfield domain; reuse prior configured knowledge, not the retired parsing runtime |

**Controlling decision:** KenTender shall operate from complete, curated and versioned Standard Tender Document packages. Authorised people configure and review each package against the official STD. AI and previously configured data may help prepare a Draft, but neither is authoritative and neither may activate or silently change a package. The production system shall not depend on an automated PDF parsing, OCR, clause-inference or schema-inference pipeline.

## 1. What this module does

A Standard Tender Document is more than a downloadable document. It contains:

- wording that must remain fixed;
- places where a Procuring Entity supplies tender-specific information;
- structures for technical requirements, schedules and prices;
- rules for bidder eligibility, qualification and evaluation;
- forms and declarations bidders must complete;
- conditions that become part of the contract; and
- information that must move into bidder response, evaluation and contract work.

KenTender represents those parts as one governed package. The package is configured once for an STD version and reused by many procurements.

The package does not contain a Ministry's particular requirement, tender date, bidder answer or bid price. It defines what later screens may collect, how values are checked, where they appear and which downstream module receives them.

For the IT STD, the result is:

```text
Official PPRA IT STD
        │
        ├─ authorised manual configuration
        ├─ optional AI drafting assistance
        └─ optional reuse of reviewed prior configuration
        ▼
Complete Draft IT STD package
        │ validation + full coverage review + rendered preview
        ▼
Immutable Active IT STD Version
        ├─ Requisition Requirements Composer Manifest
        ├─ Tender Configuration Manifest
        ├─ Bidder Response Manifest
        ├─ Evaluation Manifest
        ├─ Contract Formation Manifest
        └─ Render Manifest
```

The rendered PDF is an output. It is not the database and is not the source from which the runtime repeatedly tries to rediscover its rules.

## 2. Governing decisions

This document is the single implementation authority for the clean Manual STD Configuration and Runtime module. It replaces proposed STD-CHG-001 v1.0.

### 2.1 What is new and clean

- New DocTypes, services, pages, manifests, fixtures and tests are created from this specification.
- The old parsing engine, extracted-clause model, inferred schemas, runtime objects and routes are not migrated or wrapped.
- Old configured content may be reviewed and deliberately transformed into the new Draft model.
- Successful earlier IT Wizard product decisions, coverage work, terminology and fixture content may be reused as requirements evidence.
- No earlier implementation object becomes an authority merely because it already exists.

### 2.2 What “manual configuration” means

Manual configuration means a person is accountable for the package content and can see every item before submission. It does not require every character to be typed from scratch.

Permitted Draft inputs are:

1. direct entry by an STD Configurator;
2. copying an Active package to start its next version;
3. importing an explicitly supported prior configuration dataset into a Draft;
4. AI-assisted suggestions prepared from the official source and/or prior configured data; and
5. controlled bulk entry for repetitive configuration rows where every imported row is visible and validated.

None of these inputs can activate a package. Imported or suggested content becomes ordinary Draft content and passes the same coverage, validation, preview and independent review as directly entered content.

### 2.3 What is prohibited

The production path shall not:

- automatically ingest a PPRA PDF and declare a usable package;
- infer legal mutability, mandatory fields, evaluation rules or downstream mappings without human confirmation;
- hide unreviewed extracted content behind a confidence score;
- activate or update a package because a source file changed;
- let AI rewrite locked standard wording in an Active Version;
- use a completed PDF, Word document or spreadsheet as a substitute for structured configuration;
- use one opaque JSON field to avoid the governed package model;
- preserve old runtime aliases, dual reads or compatibility adapters; or
- omit a section because it is static, lengthy or used only after award.

## 3. Scope and boundaries

The module shall provide:

- the STD Library;
- one stable package identity for each supported STD family;
- Draft creation and versioning;
- complete coverage of official document areas;
- locked standard text blocks;
- configurable parameters and permitted choices;
- requirement, schedule, inventory, price, evaluation, form and contract schemas;
- render and downstream mappings;
- optional Draft assistance from AI or prior configuration;
- deterministic validation and coverage reporting;
- independent package review;
- complete package preview;
- activation and supersession of immutable Versions; and
- runtime manifests for downstream modules.

The module shall not contain:

- Requisition transactions or departmental requirements;
- Tender-specific values or Tender workflow;
- bidder accounts, answers, documents or prices;
- evaluation results, recommendations or award decisions;
- contract execution, inspection, payment or change-order transactions;
- a supplier portal;
- a general-purpose legal-document editor;
- editable audit actors, timestamps, hashes or technical IDs;
- generic notes, source references, evidence or attachments without a named use;
- a custom Frappe header, breadcrumb or navigation shell; or
- PDF parsing and schema inference as an application dependency.

## 4. Four content treatments

Every item in an STD must be assigned exactly one treatment. This is the primary control that prevents gaps and hidden behavior.

| Treatment | Meaning | Example | User who supplies transaction value |
|---|---|---|---|
| Locked standard content | Official wording reproduced without ordinary transaction editing | Instructions to Tenderers; General Conditions of Contract | Nobody during a Tender |
| Configurable definition | Package defines a permitted field, choice, rule or table | Tender validity period; security choice; price-table columns | Tender Preparation or System |
| PE-authored structured content | Package defines the structure; a Procuring Entity supplies procurement-specific content | IT requirements; implementation milestones; inventory background | Requisition or Tender Preparation, as assigned |
| Generated content | Runtime derives content from approved upstream data or accepted downstream responses | Tender reference; PE identity; contract carry-forward | System |

An official section may contain several treatments. For example, the Tender Data Sheet contains fixed labels, system-derived PE facts and Tender-specific values.

No package author chooses an undefined “Other” treatment. A section cannot be marked complete until every required content area has one explicit treatment and destination.

## 5. Complete IT STD coverage register

The IT package is incomplete unless all sixteen areas below are present. “Present” means that locked content, configurable definitions, structured schemas, generated bindings and downstream ownership are all accounted for—not merely that a heading exists.

| No. | Official area | Required package treatment | Primary configuration area | Runtime destination |
|---:|---|---|---|---|
| 1 | Tender identity, cover and Invitation to Tender | Locked invitation structure plus generated PE, Tender and publication slots | Package Profile; Tender Parameters | Tender document; Tender Management publication |
| 2 | Section I — Instructions to Tenderers | Locked ordered text; only declared cross-references may receive configured values | Document Structure; Tender Parameters | Render Manifest |
| 3 | Section II — Tender Data Sheet | Exact parameter definitions, choices, conditions and render bindings | Tender Parameters | Tender Configuration; rendered TDS |
| 4 | Section III — Evaluation and Qualification Criteria | Permitted stages, criterion structures, pass/scoring rules and evidence bindings | Evaluation | Tender Configuration; Evaluation Manifest |
| 5 | Section IV — Non-price Tendering Forms | Locked form text plus field-level bidder response definitions | Forms and Evidence | Bidder Response Manifest |
| 6 | Section IV — Price Schedule Forms | Price tables, line structures, calculations, currencies and evaluation totals | Price Schedules | Bidder Response and Evaluation Manifests |
| 7 | Section V — Requirements of the Information System | Structured requirement categories and row schema; no hidden obligations in prose | IT Requirements | Requisition Composer; Tender document; bidder response; contract |
| 8 | Section VI — Technical Requirements | Structured technical obligations, response modes, evidence and acceptance links | IT Requirements | Requisition Composer; bidder response; evaluation; contract |
| 9 | Section VII — Implementation Schedule | Milestone, deliverable, dependency, duration and acceptance structures | Schedule and Inventory | Requisition/Tender schedule; contract |
| 10 | Section VIII — System Inventory Tables | Technical-disclosure inventory and requirement links; commercial values remain in Price Schedules | Schedule and Inventory | Tender document; bidder response; contract appendices |
| 11 | Section IX — Background and Informational Materials | Structured bidder-relevant context with no hidden supplier obligation | Schedule and Inventory | Tender document only unless explicitly mapped |
| 12 | General Conditions of Contract | Locked ordered text and declared links to SCC values | Document Structure; Contract and Outputs | Render Manifest; contract base |
| 13 | Special Conditions of Contract | Package-permitted Tender-specific contract values and validations | Contract and Outputs | Tender Configuration; Contract Formation Manifest |
| 14 | Contract Forms and appendices | Locked form wording, generated fields and carry-forward mappings | Forms and Evidence; Contract and Outputs | Tender document; Contract Formation |
| 15 | Securities, declarations and qualification evidence | Instrument choices, field-level forms and required evidence rules | Tender Parameters; Forms and Evidence; Contract and Outputs | Bidder response; evaluation; contract |
| 16 | Change-order and post-award administration forms | Preserved and mapped to Contract Management; not presented as Tender configuration steps | Contract and Outputs | Contract Management manifest |

The coverage report shall show these sixteen rows in this order for every Draft and Version. A row cannot be removed by configuration.

## 6. End-to-end operating model

### 6.1 First package

1. Deterministic seed creates package identity `KE-PPRA-IT` and Draft Version 1.
2. The Configurator records the exact official issue label and official source file.
3. The Configurator enters content directly or uses approved Draft assistance.
4. Every imported or suggested item is reviewed inside its owning configuration area.
5. The system validates local definitions while the Configurator works.
6. The Configurator runs the complete coverage and readiness check.
7. Zero Blocking findings are required to submit.
8. A separate STD Reviewer compares the complete Draft with the official source and views the full rendered preview.
9. The Reviewer returns one actionable correction or activates the package.
10. Activation creates one immutable Version and all runtime manifests atomically.

### 6.2 Later official revision

1. Existing Tenders remain bound to their original STD Version.
2. The Configurator creates the next Draft by copying the Active Version.
3. The new official source is attached to the Draft.
4. The system derives a Version comparison from configured content; the user does not type a generic change summary.
5. Changed and unchanged coverage areas remain reviewable.
6. Review and activation create a new Active Version for new downstream instances.
7. The prior Version becomes Superseded, not deleted.

### 6.3 Downstream use

- A new applicable Requisition binds the current Active Requirement Composer Manifest.
- The authorised Requisition carries the same `std_version_id` into Tender Preparation.
- Tender Preparation cannot silently switch to a newer Version.
- Bidder, Evaluation and Contract work use manifests materialised from that same Version and the approved Tender configuration.
- A later STD revision never changes a published Tender or existing contract.

## 7. Canonical domain model

Framework audit fields remain framework-managed. User-facing forms do not collect generated identifiers, actors, timestamps or digests.

### 7.1 STDPackage

| Field | Operational purpose and effect |
|---|---|
| `package_id` | Immutable family identity. |
| `package_code` | Governed route and binding code, initially `KE-PPRA-IT`. |
| `official_title` | Exact title shown in Library, review and downstream package identity. |
| `requirement_profile` | Determines the Requisition composer family, initially `Information Technology`. |
| `current_active_version_id` | One Active Version for new instances. |
| `current_draft_id` | One open Draft maximum. |
| `state` | Derived as `Not configured`, `Draft in progress`, `In review`, `Active` or `Retired`. |

Package identities are governed seed/configuration records. MVP-1 has no general create-family screen.

### 7.2 STDDraft

| Field | Operational purpose and effect |
|---|---|
| `draft_id` | Stable authoring and review route reference. |
| `package_id` | Fixes the family. |
| `based_on_version_id` | Active Version copied for revision; empty for Version 1. |
| `proposed_version_number` | Next generated integer. |
| `official_issue_label` | Exact edition/revision wording used during review. |
| `official_source_file_id` | Reviewer-only official source. Required before submission. |
| `state` | `Draft`, `In review` or `Returned`. |
| `record_version` | Optimistic-concurrency token. |

There is no generic description, source reference, note or manually entered change summary.

### 7.3 STDVersion

Immutable activation result containing package identity, version number, official issue, source file, status and generated manifest revision. Status is `Active`, `Superseded` or `Retired`.

### 7.4 STDSourceDocument

The official source used for human review.

| Field | Operational purpose and effect |
|---|---|
| `source_document_id` | Generated identity. |
| `draft_or_version_id` | Fixes the exact Draft/Version reviewed. |
| `official_title` | Displayed beside the source viewer. |
| `official_issue_label` | Confirms the edition being configured. |
| `file_id` | Opens the reviewer-only source file. |

The source is not parsed by the runtime. File integrity is protected by the normal file service and internal audit; users do not enter or view a hash as business data.

### 7.5 STDSection

One required document section with code, title, coverage-area number and positive display order. The IT seed supplies the cover/invitation, Sections I–IX, GCC, SCC and Contract Forms. Required Sections cannot be deleted or renamed by a package Configurator.

### 7.6 STDContentBlock

| Field | Operational purpose and effect |
|---|---|
| `content_block_id` | Generated child identity. |
| `section_id` | Fixes the official section. |
| `block_type` | `Locked text`, `Generated value`, `Parameter`, `Requirement table`, `Schedule table`, `Inventory table`, `Price table`, `Evaluation table`, `Bidder form` or `Contract value`. |
| `locked_text` | Exact fixed wording for Locked text only. |
| `binding_key` | Exact definition or manifest destination for every non-text block. |
| `display_order` | Unique positive order within the section. |

Every block is visible in Document Structure. No block has a generic note, source page, confidence or inferred mutability field.

### 7.7 STDParameterDefinition

Defines one package-permitted transaction value.

| Field | Operational purpose and effect |
|---|---|
| `parameter_key` | Stable runtime and render binding. |
| `label` | Exact user-facing label. |
| `value_type` | `Text`, `Long text`, `Integer`, `Decimal`, `Date`, `Datetime`, `Duration`, `Money`, `Choice`, `Boolean`, `Address` or `Contact`. |
| `runtime_owner` | `System derived`, `Tender Preparation`, `Tender Management` or `Contract Formation`. |
| `required` / `required_when` | Defines completeness without user-authored code. |
| `allowed_values` | Required for Choice and empty otherwise. |
| `minimum_value` / `maximum_value` | Present only where the package constrains numeric, duration or money values. |
| `render_binding` | Exact section placeholder. |
| `downstream_binding` | Exact manifest consumer when the value is reused. |
| `help_text` | Present only when the label and choices do not let the user answer correctly. |

Definitions without a render or downstream consumer are invalid.

### 7.8 STDRequirementSchema

The IT requirement schema generates the Requisition Requirements Composer. It owns:

- ordered requirement categories;
- exact row fields;
- response types;
- evidence modes;
- acceptance modes;
- vendor-neutrality review triggers;
- render binding;
- bidder-response binding;
- evaluation binding; and
- contract carry-forward binding.

The Requisition row contains only:

| Field | Purpose |
|---|---|
| Category | Groups and renders the obligation. |
| Supplier obligation | States what the supplier must provide, do or satisfy. |
| Bidder response | Defines the response structure expected later. |
| Evidence required | Defines the exact proof or demonstration where needed. |
| Acceptance condition | Defines how delivery can be accepted. |

The Configurator defines the schema; the department later supplies requirement rows. Score, price, actual result, source/author, generic priority and row-level review status do not belong in the Requisition row.

The IT package contains these fourteen governed categories:

1. Functional;
2. Architecture;
3. Performance;
4. Security;
5. Integration;
6. Data and migration;
7. Reporting and analytics;
8. Hosting and infrastructure;
9. Training and knowledge transfer;
10. Support and warranty;
11. Testing and acceptance;
12. Accessibility and usability;
13. Business continuity and disaster recovery; and
14. Regulatory compliance.

### 7.9 STDScheduleSchema

Defines milestone, required deliverable, completion rule, duration, dependency and acceptance checkpoint. It maps to the rendered schedule and Contract Formation. It does not contain actual project dates, payment certification, inspections or contract status.

### 7.10 STDInventorySchema

Defines bidder-relevant technical disclosure for Hardware, Software, Licence, Service, Training, Support, Hosting and Integration. Each inventory row may link to a Requirement and a Schedule milestone. Quantity, unit, tax and commercial totals belong to Price Schedules, not Inventory.

### 7.11 STDPriceSchema

Defines four IT price-table families:

1. Software and infrastructure;
2. Implementation services;
3. Training; and
4. Recurrent support.

Each schema defines line description, quantity/unit source, currency rule, tax treatment, bidder price fields, calculation and evaluated-total binding. It contains no actual bid price.

### 7.12 STDEvaluationSchema

Defines permitted stages:

1. Preliminary responsiveness;
2. Technical evaluation;
3. Financial evaluation; and
4. Post-qualification.

It defines allowed criterion types, evidence/requirement bindings, pass/scoring treatment, threshold rules and financial basis. It does not contain an evaluator, score or award result.

### 7.13 STDFormSchema

One standard form is stored as locked wording plus field-level supplier response definitions. The IT package accounts for:

1. Form of Tender;
2. Tenderer Information Form;
3. Joint Venture Member Information Form;
4. Confidential Business Questionnaire;
5. Certificate of Independent Tender Determination;
6. Self-Declaration forms;
7. Fraud and Corruption declaration;
8. Beneficial Ownership disclosure;
9. Historical Non-performance and Pending Litigation;
10. General Experience;
11. Specific Experience;
12. Current Contract Commitments;
13. Financial Situation;
14. Average Annual Turnover;
15. Financial Resources;
16. Personnel Capability;
17. Intellectual Property; and
18. Conformance of Information System Materials.

Price forms are owned by STDPriceSchema. A form required for evaluation must expose field-level data; it cannot be only a downloadable template.

### 7.14 STDContractSchema

Defines package-permitted Special Conditions and contract mappings for:

- performance security;
- advance-payment security where applicable;
- payment milestones;
- operational acceptance;
- warranty and support periods;
- intellectual-property treatment;
- software licence categories;
- confidentiality and insurance;
- liability values where configurable;
- dispute-resolution fields;
- subcontractor approval; and
- contract appendices and post-award form mappings.

It contains no post-award execution, change, inspection or payment data.

### 7.15 STDOutputMapping

One explicit edge from a package definition to `Render`, `Requisition`, `Tender`, `Bidder response`, `Evaluation`, `Contract Formation` or `Contract Management`. A required definition with no terminal output is Blocking.

### 7.16 STDAssistanceBatch

System audit object for one optional Draft-assistance operation. It records Draft ID, assistance type (`Prior configuration` or `AI-assisted draft`), input file/reference, generated proposal set, actor and time. It does not make proposals authoritative.

The Configurator must accept or reject proposed items. Accepted items are copied into ordinary Draft records and show in the normal configuration areas. The package review does not rely on an AI confidence score.

### 7.17 STDValidationFinding, STDReviewTask and STDDecision

Findings are derived as `Blocking` or `Warning`, with a stable code, owning configuration area and actionable message. Users cannot dismiss or annotate them.

The Review task binds one submitted snapshot to the effective STD Reviewer. Decisions are `Return for correction` or `Activate package`. Return requires one correction. Activation requires the complete source, coverage report, comparison when applicable and rendered preview.

### 7.18 STDTenderConfigurationManifest

The immutable contract through which Tender Preparation configures a Tender under one Active STD Version. It contains:

- manifest identity and the bound `std_version_id`;
- nine ordered configuration-step definitions;
- every configurable or generated item used by those steps;
- upstream bindings from the authorised Requisition and PE/FY configuration;
- structured composer definitions;
- governed conditions, defaults and validations;
- completion rules for every step;
- render and downstream mappings; and
- the complete-readiness rule.

Each manifest item has the following contract. These are system configuration properties, not fields shown indiscriminately to the Procurement Officer.

| Property | Purpose |
|---|---|
| `item_key` | Stable package-owned key used by values, conditions, tests and render bindings. |
| `step_id` | One owning step `CFG-01` through `CFG-09`. |
| `label` | Exact Procurement Officer label. |
| `help_text` | Exact guidance shown only where the value is not self-explanatory. |
| `value_type` | Governed type: Text, Long Text, Integer, Decimal, Money, Percentage, Date, Date and Time, Duration, Boolean, Choice, Multi-choice, Link, Structured Table or Generated Display. |
| `source_mode` | `Generated`, `Inherited locked`, `Inherited reviewable`, `Officer entry` or `Officer choice`. |
| `source_binding` | Exact upstream or system key when the source is generated or inherited. |
| `required_mode` | `Always`, `Conditional` or `Optional`. Optional is allowed only where the official STD permits omission and the omission has a defined effect. |
| `condition` | Governed expression over manifest keys. Empty unless required mode, choices or visibility depend on another value. |
| `allowed_values` | Exact package choices or governed link query. Empty for unrestricted typed values. |
| `default_rule` | Package constant or named system/upstream binding. No hidden UI default. |
| `validation` | Bounds, format, chronology, cross-field rule or table-row rule. |
| `render_binding` | Exact official document slot, table or clause cross-reference. |
| `downstream_mapping` | Named bidder, evaluation, contract or publication destination where applicable. |
| `completion_effect` | Whether a missing or invalid value blocks the owning step or produces a warning. |

The manifest does not contain transaction values. A Tender Configuration Instance stores values against these stable keys and remains bound to the same `std_version_id`.

## 8. Package configuration areas

The package-authoring workspace uses nine areas. These are not the downstream Tender Wizard steps.

| ID | Area | Owns | Must not own |
|---|---|---|---|
| PCFG-01 | Source and Profile | Official identity, issue, source file, requirement profile | Document content or Tender values |
| PCFG-02 | Coverage and Document Structure | Required sections, ordered blocks and content treatment | Parameter definitions or transaction values |
| PCFG-03 | Tender Parameters | Configurable/system-generated values and render bindings | Technical requirements, prices or evaluation results |
| PCFG-04 | IT Requirements | Composer categories, row fields, response/evidence/acceptance modes and mappings | Tender-specific requirement rows or scores |
| PCFG-05 | Schedule, Inventory and Background | Schedule and inventory schemas; background structure | Commercial totals or hidden supplier obligations |
| PCFG-06 | Price Schedules | Price table schemas, calculations and financial bindings | Actual bidder prices or technical wording |
| PCFG-07 | Evaluation and Qualification | Stages, criterion structures, thresholds and evidence bindings | Actual evaluation or award recommendation |
| PCFG-08 | Forms and Evidence | Field-level forms, declarations and evidence rules | Actual bidder submissions |
| PCFG-09 | Contract and Outputs | SCC definitions, contract forms, carry-forward and all terminal mappings | Post-award contract execution |

## 9. Generated Tender Configuration Manifest

### 9.1 Purpose and ownership boundary

The Tender Configuration Manifest is the primary operational output of an Active STD Version. It tells Tender Preparation exactly what a Procurement Officer must see, review, select or enter to configure a particular Tender correctly under that STD.

STD Configuration owns:

- the nine-step structure;
- labels and help text;
- item types, choices and defaults;
- upstream sources and editability;
- conditions and validation;
- structured composer definitions;
- step-completion rules;
- official-document render bindings; and
- bidder, evaluation, contract and publication mappings.

Tender Preparation owns:

- creation of the Tender transaction from an authorised Requisition;
- the Procurement Officer workspace and navigation;
- draft saving, concurrent-edit protection and assignments;
- collaboration on the Tender instance;
- display of completion and validation results produced under the manifest;
- internal Tender review and approval;
- complete Tender preview; and
- publication handoff.

Tender Preparation may choose the page composition needed to perform that work, but it shall not invent, rename, omit or reinterpret manifest items. STD-CHG-001 therefore defines the complete configuration contract, not the transaction-page design.

### 9.2 Manifest identity and binding

Every generated manifest shall contain:

| Property | Rule |
|---|---|
| `manifest_type` | Exact value `Tender Configuration`. |
| `manifest_version` | Package-generated contract version. |
| `package_code` | `KE-PPRA-IT` for the first package. |
| `std_version_id` | Immutable Active Version from which the manifest was generated. |
| `official_title` | Exact STD title. |
| `official_issue` | Exact approved issue label. |
| `requirement_profile` | `Information Technology`. |
| `steps` | Exactly CFG-01 through CFG-09 in the order below. |
| `complete_rule` | All nine steps Complete and zero Blocking findings. |

The authorised Requisition stores the applicable `std_version_id`. Tender Preparation must use that Version's manifest. It cannot silently use the package's newer Active Version.

### 9.3 Source modes and editability

| Source mode | Procurement Officer treatment | Correction route |
|---|---|---|
| Generated | Displayed read-only. | Correct the named system configuration or source transaction. |
| Inherited locked | Displayed read-only because it is already approved upstream. | Return to the owning upstream process; do not duplicate the value in Tender Preparation. |
| Inherited reviewable | Pre-filled and reviewable. It may be changed only where the STD package and Requisition contract explicitly permit Tender-stage refinement. | Save the permitted refinement with its owning Tender item. |
| Officer entry | Entered for this Tender. | Correct in the owning Tender step while editable. |
| Officer choice | Selected from exact package-permitted choices. | Change the selection while the Tender is editable. |

A manifest item cannot be editable merely because its upstream source is inconvenient. Budget, approved scope, requirement rows and procurement method are not re-entered in the Tender Wizard.

### 9.4 Nine-step manifest summary

| ID | User-facing step | Purpose | Primary sources | Completion basis |
|---|---|---|---|---|
| CFG-01 | Tender Profile | Confirm the identity and approved procurement basis of the Tender. | PE/FY configuration; authorised Requisition; system | All generated/inherited bindings resolve and the permitted officer entries are valid. |
| CFG-02 | Tender Data Sheet | Supply the Tender-specific values referenced by the Instructions to Tenderers. | STD parameter definitions; CFG-01 | Every applicable TDS item is valid and chronology passes. |
| CFG-03 | IT Requirements | Confirm the complete structured requirement package bidders must answer. | Authorised Requisition; Requirement Composer Manifest | Every requirement is valid, mapped and has a bidder-response treatment. |
| CFG-04 | Implementation Schedule | Define the required delivery and acceptance schedule within approved scope. | Requisition schedule; STD schedule schema | Every milestone and deliverable is complete and chronologically valid. |
| CFG-05 | System Inventory and Bidder Background | Provide the existing-environment and context information needed to prepare responsive bids. | Requisition; STD inventory/background schemas | Required inventory and background structures are complete and contain no hidden obligation. |
| CFG-06 | Price Schedule | Define how bidders must price the approved scope. | Approved requirements, schedule and STD price schemas | Every priced scope item maps once to an applicable schedule and calculations validate. |
| CFG-07 | Evaluation Setup | Configure the package-permitted qualification and evaluation treatment. | Procurement method; requirements; evidence and price schemas | All stages, criteria, sources, thresholds and totals are valid. |
| CFG-08 | Forms and Evidence | Resolve which conditional tendering forms, declarations, securities and evidence apply. | STD conditions; CFG-01, CFG-02 and CFG-07 | Every applicable form is enabled and all required parameters resolve. |
| CFG-09 | Contract Values | Supply Tender-specific SCC and contract values that are not determined elsewhere. | STD contract schema; earlier steps | Every applicable SCC value and contract mapping resolves. |

### 9.5 CFG-01 — Tender Profile

The IT manifest shall define at least the following items. A package may include another item only where it maps to the official IT STD and passes the field-purpose rule.

| Key and label | Type | Source mode and binding | Required/validation | Output |
|---|---|---|---|---|
| `tender_reference` — Tender reference | Generated Display | System Tender identity | Always; unique | Cover, Invitation, TDS and publication |
| `tender_title` — Tender title | Inherited reviewable Text from authorised Requisition | Always; clear procurement title | Cover, Invitation and publication |
| `procuring_entity` — Procuring Entity | Generated Display from active PE | Always | All named PE slots |
| `financial_year` — Financial Year | Inherited locked Link from Requisition | Always; configured FY | Tender record and audit binding |
| `procurement_method` — Procurement method | Inherited locked Choice from authorised Requisition | Always; supported by package | TDS, evaluation and publication |
| `procurement_category` — Procurement category | Inherited locked value `Goods — Information Technology` | Always | Package applicability |
| `requisition_reference` — Requisition reference | Generated Display | Authorised Requisition | Always | Lineage only; not rendered in the official Tender unless mapped |
| `tender_contact_name` — Contact person | Officer entry Text | Always | Invitation and TDS contact slot |
| `tender_contact_email` — Contact email | Officer entry Text | Always; valid email | Invitation and TDS contact slot |
| `tender_contact_phone` — Contact telephone | Officer entry Text | Always; valid telephone format | Invitation and TDS contact slot |

The manifest shall not ask the Procurement Officer to re-enter the approved budget, funding source, department, procurement method or Financial Year.

### 9.6 CFG-02 — Tender Data Sheet

The package emits the exact applicable TDS definitions. For the IT package, the configuration contract shall cover these groups:

| Group | Required manifest content |
|---|---|
| Communication | Clarification channel, clarification deadline and response/publication treatment. |
| Tender preparation | Language, alternative-tender permission, number of copies where applicable and signing treatment. |
| Submission | Submission method, submission address or portal binding, deadline and late-tender treatment. |
| Opening | Opening date/time, location or online-opening treatment and attendance information. |
| Validity | Tender-validity period and extension treatment. |
| Securities | Tender-security or tender-securing-declaration choice, amount/form where applicable and validity. |
| Currency | Permitted tender currencies, conversion currency, source and conversion date where applicable. |
| Preference and reservation | Exact applicable programme/treatment from the authorised procurement; no free-text preference invention. |
| Site and meetings | Pre-tender meeting and site-visit applicability, dates, locations and attendance rule where enabled. |
| Award | Notification channel and standstill-related configured values where required by the package. |

Every emitted TDS item shall have a corresponding `STDParameterDefinition`, official slot and completion effect. Chronology validation shall cover, at minimum:

```text
clarification deadline < submission deadline
pre-tender meeting date < submission deadline
site visit date < submission deadline
opening date/time >= submission deadline
tender validity end > submission deadline
tender security validity end >= tender validity end + package-defined buffer
```

Disabled conditional groups shall render the package-approved “not applicable” treatment; they shall not leave empty official slots.

### 9.7 CFG-03 — IT Requirements

The Tender inherits the authorised structured Requirement Package. It shall not accept a replacement specification, TOR, BOQ, spreadsheet or PDF as the requirements source.

The manifest emits the fourteen governed categories and the five-field requirement-row contract:

| Row field | Tender-stage treatment |
|---|---|
| Category | Inherited locked from the Requirement Package. |
| Supplier obligation | Inherited locked unless the Requisition contract explicitly permits non-substantive Tender refinement. |
| Bidder response | Package-defined response mode and fields. |
| Evidence required | Package-defined or Requisition-selected governed evidence requirement. |
| Acceptance condition | Inherited structured acceptance statement used by evaluation and contract. |

For every requirement, the manifest includes:

- stable requirement key and category;
- display order;
- obligation text;
- response type: `Compliance choice`, `Text`, `Numeric`, `Choice` or `Structured table`;
- allowed choices or numeric unit/bounds where applicable;
- evidence rule;
- evaluation treatment;
- price-schedule mapping;
- contract carry-forward mapping; and
- acceptance mapping.

Step completion requires every approved requirement to have one bidder-response treatment and all four downstream mappings required by its category. Adding scope belongs to the Requisition process, not Tender Preparation.

### 9.8 CFG-04 — Implementation Schedule

The manifest emits structured tables for:

1. implementation milestones;
2. deliverables;
3. dependencies supplied by the PE;
4. acceptance events; and
5. training, migration, testing, commissioning and support periods where applicable.

Each milestone row contains only:

| Field | Purpose |
|---|---|
| Milestone | Identifies the required stage. |
| Required deliverable | States the tangible output. |
| Due rule | Defines date, duration from commencement or dependency-based timing. |
| PE dependency | Identifies a necessary PE input, if any. |
| Acceptance condition | Defines how completion is confirmed. |

The Procurement Officer may organise timing within the authorised delivery period but cannot expand approved scope or introduce an unmapped supplier obligation. Every milestone must map to the Tender document and Contract Formation Manifest.

### 9.9 CFG-05 — System Inventory and Bidder Background

The manifest provides two separate structures:

- **System Inventory** — the existing hardware, software, interfaces, data, sites or facilities bidders must consider; and
- **Bidder Background** — PE context needed to understand the operating environment.

An inventory row contains `Category`, `Item`, `Current state`, `Relevant quantity or scale` and `Requirement link`. It contains no price, tax or evaluated total.

Background entries contain `Topic` and `Bidder-relevant information`. They cannot create a supplier obligation. If the text requires the supplier to act, deliver or comply, it must be represented in CFG-03 and linked from the background entry.

### 9.10 CFG-06 — Price Schedule

The manifest shall generate only the price schedules applicable to the approved scope. The IT package supports:

| Schedule | Purpose | Minimum columns |
|---|---|---|
| Goods supplied from outside Kenya | Imported hardware/software items | Item, requirement reference, country of origin, quantity, unit price, applicable duties/taxes, total |
| Goods supplied from within Kenya | Locally supplied hardware/software items | Item, requirement reference, quantity, unit price, applicable taxes, total |
| Services | Implementation, migration, training, support or other services | Service, requirement/milestone reference, unit, quantity/duration, rate, applicable taxes, total |
| Recurrent costs | Licences, subscriptions, maintenance or support over the evaluation period | Cost item, requirement reference, period, quantity, rate, applicable taxes, total |

The manifest defines applicable schedules, currency treatment, calculations, rounding and the evaluated-total composition. Every price row must link to approved scope. One approved scope item cannot be accidentally priced twice unless the package explicitly defines separate one-off and recurrent components.

### 9.11 CFG-07 — Evaluation Setup

The IT manifest emits four ordered stages:

1. preliminary responsiveness;
2. mandatory technical compliance;
3. scored technical evaluation where the package permits it; and
4. financial evaluation and comparison.

Each criterion definition contains:

| Property | Rule |
|---|---|
| Criterion | Exact officer-facing criterion label. |
| Source | Exact bidder response, evidence field, form field or price result. |
| Treatment | Pass/fail, scored or calculated financial result. |
| Rule | Governed pass condition, score scale or calculation. |
| Weight | Present only for scored criteria; totals must equal the package-required total. |
| Threshold | Present only where the package permits a threshold. |
| Failure effect | Exact stage effect. |

The Procurement Officer can select or configure only package-permitted treatments. The manifest shall not provide a generic criterion builder capable of creating evaluation rules unrelated to requirements, qualification forms, evidence or price schedules.

### 9.12 CFG-08 — Forms and Evidence

The manifest evaluates package conditions and emits the applicable subset of all eighteen IT forms defined in section 7.13. Each enabled form contains its exact field-level schema, signing treatment, evidence rule and render location.

The step distinguishes:

- always-required forms;
- forms made applicable by procurement method or bidder structure;
- security/declaration alternatives selected in CFG-02;
- qualification evidence referenced by CFG-07; and
- contract forms displayed for Tender purposes but completed only at the correct later stage.

No required bidder information may be represented only as an attachment request where a structured field or table is defined by the package.

### 9.13 CFG-09 — Contract Values

The manifest emits only Tender-specific Special Conditions and contract values not already generated or inherited. The IT package supports governed definitions for:

- commencement and implementation timing;
- performance security;
- advance-payment security where enabled;
- payment milestones;
- operational acceptance;
- warranty and support periods;
- software licensing treatment;
- intellectual-property treatment;
- confidentiality and insurance where applicable;
- liability values where configurable;
- dispute-resolution fields;
- subcontractor approval; and
- named contract appendices.

Every item must map to an SCC slot or contract form. A value already resolved in CFG-01 through CFG-08 is displayed as inherited and is not collected again.

### 9.14 Complete-readiness output

The manifest generates a deterministic readiness result with:

- each step's state: `Not started`, `In progress`, `Complete` or `Blocked`;
- every Blocking finding with exact step and item key;
- warnings that require review but do not replace a package rule;
- unresolved upstream bindings;
- render status for all official sections;
- bidder, evaluation and contract mapping status; and
- the final `Ready for Tender review` Boolean.

`Ready for Tender review` is true only when all nine steps are Complete, all required upstream bindings resolve, every official slot renders, every required downstream mapping terminates and Blocking findings equal zero.

### 9.15 Worked IT Tender instance

The golden manifest shall be instantiated with the following deterministic Tender data. This fixture proves the contract; it is not a substitute for completing the production IT package against the official STD.

#### A. Profile and source

| Value | Fixture |
|---|---|
| STD package | KE-PPRA-IT |
| STD Version | IT-STD-V1 |
| Tender reference | MOH/ICT/OT/003/2027-2028 |
| Tender title | Supply, Installation and Support of a Hospital Information Management System |
| Procuring Entity | Ministry of Health |
| Financial Year | FY-2027-2028 |
| Procurement method | Open Tender |
| Requisition reference | PR-MOH-ICT-2027-0042 |
| Contact person | Head, Supply Chain Management Services |
| Contact email | procurement@health.go.ke |
| Contact telephone | +254 20 2717077 |

#### B. Tender Data Sheet

| Item | Fixture value |
|---|---|
| Tender language | English |
| Alternative tenders | Not permitted |
| Clarification deadline | 10 September 2027, 17:00 EAT |
| Pre-tender meeting | 6 September 2027, 10:00 EAT — Afya House Boardroom |
| Site visit | Not applicable |
| Submission method | Electronic submission through KenTender |
| Submission deadline | 24 September 2027, 10:00 EAT |
| Tender opening | 24 September 2027, 10:30 EAT — KenTender online opening |
| Tender validity | 120 days from submission deadline |
| Tender security treatment | Tender Security |
| Tender security amount | KES 2,000,000 |
| Tender security validity | 28 days beyond Tender validity |
| Tender currency | Kenya Shillings |
| Preference or reservation | None |

#### C. IT Requirements sample

The complete golden fixture contains all fourteen categories. The selected visible rows are:

| Category | Supplier obligation | Bidder response | Evidence required | Acceptance condition |
|---|---|---|---|---|
| Functional Requirements | Provide patient registration, appointment, clinical documentation, billing and pharmacy workflows. | Compliance choice plus description | Product documentation and configured demonstration | All five workflows pass the approved user-acceptance scripts. |
| Architecture and Technology | Provide a browser-based, three-tier solution deployable in the Ministry private cloud. | Compliance choice plus architecture description | Architecture diagram | Architecture review confirms all declared layers and deployment controls. |
| Integration Requirements | Integrate with the national identity, laboratory and payment interfaces defined in the interface schedule. | Structured interface-response table | Interface specifications and prior integration references | Each interface passes contract integration testing. |
| Security Requirements | Enforce role-based access, multi-factor authentication for privileged users and encryption in transit and at rest. | Compliance choice plus control description | Security design and independent test evidence | Security verification records no unresolved critical finding. |
| Service-Level Requirements | Provide 99.9% monthly production availability excluding approved maintenance. | Numeric commitment and service description | Proposed SLA | Contract SLA states at least 99.9% and includes the package-defined measurement rule. |

#### D. Implementation schedule

| Milestone | Required deliverable | Due rule | PE dependency | Acceptance condition |
|---|---|---|---|---|
| Inception | Approved inception report and detailed work plan | 14 days from commencement | Project team availability | Inception report approved by the Project Manager. |
| Solution design | Approved solution and integration design | 35 days from commencement | Access to current-system documentation | Design review completed with no Blocking finding. |
| Configuration and integration | Configured solution and completed interfaces | 90 days from commencement | Test credentials and interface access | System and integration tests passed. |
| Training and migration | Trained users and accepted migrated data | 120 days from commencement | Cleansed source data and nominated trainees | Training records and migration reconciliation accepted. |
| Go-live and operational acceptance | Production service and operational acceptance certificate | 150 days from commencement | Production infrastructure and authorised users | Thirty-day stabilisation period completed and acceptance certificate issued. |

#### E. Inventory and background

| Type | Fixture |
|---|---|
| Inventory | 12 referral hospitals; approximately 3,500 named users; Ministry private-cloud environment; national identity, laboratory and payment interfaces. |
| Background | The Ministry is replacing separate facility applications with one centrally governed hospital information platform. |

#### F. Price and evaluation

| Item | Fixture |
|---|---|
| Applicable price schedules | Goods supplied from within Kenya; Services; Recurrent costs |
| Evaluation period for recurrent costs | 3 years |
| Preliminary evaluation | Pass/fail |
| Mandatory technical evaluation | Pass/fail against every mandatory requirement |
| Scored technical evaluation | 70 points; minimum technical score 49 |
| Financial evaluation | Evaluated price of technically qualified tenders |
| Final comparison | Package-permitted combined treatment configured in the golden evaluation schema |

#### G. Forms, securities and contract values

| Item | Fixture |
|---|---|
| Tender Form | Required |
| Tenderer's Eligibility and Qualification Information | Required |
| Manufacturer's Authorization | Conditional for proposed proprietary hardware or software not manufactured/published by the Tenderer |
| Tender Security | Required — KES 2,000,000 |
| Performance Security | 10% of Contract Price |
| Advance-payment security | Required only if the signed Contract includes an advance payment |
| Warranty | 12 months from Operational Acceptance |
| Support period | 36 months from Operational Acceptance |
| Payment milestones | 10% inception; 20% design; 30% configuration and integration; 20% training and migration; 20% Operational Acceptance |
| Intellectual property | Governed IT package choice selected in CFG-09 and rendered into SCC; no free-text clause drafting |

The fixture is Complete only when the remaining configured requirements, forms, criteria, parameters and mappings also pass. The tables above define the representative content that must be visible in contract tests and later Tender Preparation design fixtures.

### 9.16 Tender Preparation follow-on document

After the revised Procurement Requisition contract is approved, a separate Tender Preparation canonical document shall define:

1. Tender creation from an authorised Requisition;
2. immutable binding to its STD Version and Tender Configuration Manifest;
3. the Procurement Officer's nine-step workspace;
4. save, resume, assignments and concurrent-edit handling;
5. completion and error presentation;
6. complete rendered Tender preview;
7. internal review, return, approval and maker-checker rules;
8. publication readiness and handoff; and
9. exact Claude Design fixtures and interactions for every Tender Preparation surface.

That document shall use the worked instance in section 9.15. It may arrange the workflow for usability, but it cannot redefine the manifest contract.

Readiness, Tender review, complete preview and publication handoff are workflow gates, not additional configuration steps.

## 10. Runtime manifests

| Manifest | Required content | Consumer |
|---|---|---|
| Requirement Composer | Categories, row fields, allowed modes, validations, schedule schema and package Version | Procurement Requisitions |
| Tender Configuration | Complete section 9 contract: identity, nine ordered steps, every item definition, upstream bindings, structured composers, conditions, validations, completion rules, render bindings and downstream mappings | Tender Preparation |
| Bidder Response | Field-level forms, compliance responses, evidence controls and price tables | Bidder Response |
| Evaluation | Stages, criteria structures and exact links to bidder fields, evidence and prices | Evaluation |
| Contract Formation | Approved obligations, accepted responses, schedule, securities and contract values | Contract Formation |
| Contract Management | Post-award forms and declared administration mappings | Contract Management |
| Render | Ordered sections, locked blocks, slots, tables and formatting instructions | Preview and final document renderer |

Every manifest identifies the immutable `std_version_id`. It contains validated data, not user-authored executable code or design-tool HTML.

## 11. Coverage and validation

### 11.1 Coverage checks

Each of the sixteen official areas must answer:

1. Is the area present?
2. Which content treatment applies to each part?
3. Which package area owns it?
4. Which runtime output receives it?
5. Does the rendered preview contain it?
6. If no Tender screen collects a value, is it correctly locked, generated or downstream-owned?

### 11.2 Blocking validation

Blocking findings include:

- missing official source;
- missing required section or coverage row;
- unresolved content block;
- duplicate binding key;
- parameter without render or downstream use;
- unbounded or invalid Choice definition;
- requirement schema without bidder/evaluation/contract treatment;
- schedule field without render or contract use;
- inventory field hiding a commercial value;
- price table without calculation or evaluated-total treatment;
- criterion without response/evidence source;
- required form represented only as an opaque upload;
- contract value without SCC/render mapping;
- locked block containing an undeclared placeholder;
- output mapping cycle or missing terminal consumer;
- runtime manifest generation failure; or
- render failure.

Warnings identify review concerns that do not make the package structurally unusable, such as a vendor-neutrality trigger definition that is unusually broad. Warnings cannot be dismissed; the Reviewer sees them with their owning area.

### 11.3 Activation rule

Activation requires:

- zero Blocking findings;
- all sixteen coverage rows passed;
- successful generation of all seven manifests;
- successful full preview render;
- current Reviewer authority;
- maker-checker separation; and
- unchanged submitted snapshot.

Any failure creates no Version and no partial manifests.

## 12. Lifecycle and permissions

| Current state | Action | Next state | Actor |
|---|---|---|---|
| Draft | Save area | Draft | STD Configurator |
| Draft | Run complete check | Draft | STD Configurator |
| Draft | Submit for review | In review | STD Configurator |
| In review | Return for correction | Returned | STD Reviewer |
| Returned | Save correction | Returned | STD Configurator |
| Returned | Resubmit | In review | STD Configurator |
| In review | Activate package | Active Version created | STD Reviewer |
| Active | Create new version | New Draft | STD Configurator |

The submitter cannot activate the same Draft. System Manager alone grants no STD business decision. Configurator and Reviewer capabilities are assigned through Configuration and Governance and fail closed when missing or ambiguous.

## 13. Services and errors

### 13.1 Reads

- `ListSTDPackages`
- `GetSTDPackageHome`
- `GetSTDConfigurationArea`
- `GetSTDCoverageReport`
- `GetSTDReadinessReport`
- `GetSTDReviewWorkspace`
- `GetSTDPreview`
- `GetSTDVersionComparison`
- `GetActiveSTDVersion`
- `GetRuntimeManifest`
- `GetAssistanceProposal`

### 13.2 Commands

- `SaveSTDSourceAndProfile`
- `SaveSTDDocumentStructure`
- `SaveSTDParameters`
- `SaveSTDRequirementSchema`
- `SaveSTDScheduleInventoryBackground`
- `SaveSTDPriceSchemas`
- `SaveSTDEvaluationSchema`
- `SaveSTDFormSchemas`
- `SaveSTDContractAndOutputs`
- `PreparePriorConfigurationProposal`
- `PrepareAIAssistedDraftProposal`
- `AcceptAssistanceItems`
- `RejectAssistanceItems`
- `RunSTDCompleteCheck`
- `SubmitSTDForReview`
- `ReturnSTDForCorrection`
- `ActivateSTDVersion`
- `CreateNextSTDDraft`

Every command requires current capability, record version and idempotency key. Save commands validate the changed area and immediate mapping edges. Complete validation runs only on explicit check, submission, review load and activation.

### 13.3 Error contract

| Code | Meaning | User response |
|---|---|---|
| `STD_CONTEXT_REQUIRED` | No effective STD assignment | Show unavailable state. |
| `STD_DRAFT_CHANGED` | Draft record version is stale | Reload without overwriting newer content. |
| `STD_BINDING_DUPLICATE` | Stable key already exists | Focus the duplicate row. |
| `STD_BINDING_UNRESOLVED` | Block or mapping has no valid target | Open the owning area. |
| `STD_COVERAGE_INCOMPLETE` | One or more required areas are incomplete | Open Coverage Report. |
| `STD_VALIDATION_BLOCKED` | Blocking findings remain | Open Readiness Report. |
| `STD_ASSISTANCE_FAILED` | Draft assistance could not produce a proposal | Preserve Draft; offer retry without partial acceptance. |
| `STD_ASSISTANCE_STALE` | Proposal was generated against an older Draft | Regenerate or discard it. |
| `STD_MAKER_CHECKER` | Submitter attempted activation | Deny action. |
| `STD_REVIEW_CHANGED` | Submitted snapshot is no longer current | Reload review task. |
| `STD_MANIFEST_FAILED` | One or more manifests could not be generated | Create no Active Version. |
| `STD_VERSION_NOT_ACTIVE` | Runtime requested an unavailable Version | Return a controlled upstream configuration error. |

## 14. UI architecture and complete surface registry

Menu: **Configuration and Governance > Standard Tender Documents**.

Frappe owns the header, breadcrumb, Desk lifecycle and navigation. Vue 3 owns the package-authoring work surface. The global PE/FY selector is not shown because STD packages are global configuration.

| ID | Surface | Type | Required |
|---|---|---|---:|
| STD-UI-00 | Standard Tender Documents | Application page | Yes |
| STD-UI-M01 | Create new package version | Modal | Yes |
| STD-UI-01 | Package home | Application page | Yes |
| STD-UI-M02 | Draft assistance | Modal and proposal drawer | Yes |
| PCFG-01 | Source and Profile | Configuration page | Yes |
| PCFG-02 | Coverage and Document Structure | Configuration page | Yes |
| PCFG-03 | Tender Parameters | Configuration page | Yes |
| PCFG-04 | IT Requirements | Configuration page | Yes |
| PCFG-05 | Schedule, Inventory and Background | Configuration page | Yes |
| PCFG-06 | Price Schedules | Configuration page | Yes |
| PCFG-07 | Evaluation and Qualification | Configuration page | Yes |
| PCFG-08 | Forms and Evidence | Configuration page | Yes |
| PCFG-09 | Contract and Outputs | Configuration page | Yes |
| STD-WF-01 | Coverage and Readiness Report | Workflow report | Yes |
| STD-WF-02 | Package Review | Workflow task | Yes |
| STD-WF-03 | Complete Package Preview | Read-only preview | Yes |
| STD-WF-04 | Active Version | Read-only handoff | Yes |
| STD-WF-05 | Version Comparison | Read-only comparison | Required for Version 2+ |
| STD-STATE | Common page states | State variants | Yes |

No package-authoring surface outside this registry may be designed or implemented without revising this document.

## 15. Complete static Claude Design contract

### 15.1 Rules for every artboard

- These are static visual instructions only. Behavior is in section 16.
- Use only the exact fixture data below. Do not invent fields, cards, metrics, rows, actions, filters, notices or text.
- Frappe header and breadcrumb are fixture context outside the artboard.
- Do not draw a PE/FY selector.
- Use the approved KenTender page header, tabs, cards, tables, status badges, dialogs, drawers, notices, empty states and fixed footer.
- Do not show hashes, rule IDs, source anchors, extraction confidence, OCR, parsing status, internal object names or raw JSON.
- Do not place API, permission, validation algorithm, routing or persistence instructions in an artboard.

### 15.2 Shared fixture

Unless a screen states otherwise:

- Configurator: **Amina Hassan** · `amina.hassan@kentender.example.test` · STD Configurator
- Reviewer: **David Mwangi** · `david.mwangi@kentender.example.test` · STD Reviewer
- Date/time: **25 Aug 2026, 09:00 EAT**
- Package: **KE-PPRA-IT · Standard Tender Document for Procurement of Information Technology**
- Draft: **Proposed Version 1**
- Official issue: **April 2021 edition**
- Official source: **PPRA IT Standard Tender Document.pdf**

### 15.3 STD-UI-00 — Standard Tender Documents

**Outside artboard:** Amina Hassan · Frappe breadcrumb **Home > Configuration and Governance > Standard Tender Documents**

Header:

- Eyebrow **CONFIGURATION AND GOVERNANCE**
- Title **Standard Tender Documents**
- Text **Configure and activate the standard document packages used by KenTender.**
- No header action

Table:

| Standard Tender Document | Profile | Active version | Status | Action |
|---|---|---|---|---|
| KE-PPRA-IT · Standard Tender Document for Procurement of Information Technology | Information Technology | Not active | Draft in progress | Open package |

Footer: **1 Standard Tender Document**.

Do not show create-family, extraction, import-PDF, confidence, analytics or document-count controls.

### 15.4 STD-UI-M01 — Create new package version

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT**

Show over a dimmed Active Package page:

- Title **Create new package version**
- Text **Start Version 2 from the current Active Version 1. Existing Requisitions and Tenders will remain bound to Version 1.**
- Read-only row **Based on — Version 1 · April 2021 edition**
- Field **Official issue** with value **June 2028 revision**
- Field **Official source** with file **PPRA IT Standard Tender Document June 2028.pdf** and action **Replace**
- Buttons **Cancel** and **Create Draft Version 2**

Do not show version number input, change-summary field, extraction option or activation date.

### 15.5 STD-UI-01 — Package home

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT**

Header:

- Eyebrow **STANDARD TENDER DOCUMENT**
- Title **Procurement of Information Technology**
- Quiet reference **KE-PPRA-IT · Proposed Version 1**
- Badge **Draft**
- Secondary header action **Draft assistance**

Source card:

| Label | Value |
|---|---|
| Official title | Standard Tender Document for Procurement of Information Technology |
| Official issue | April 2021 edition |
| Official source | PPRA IT Standard Tender Document.pdf · View |

Configuration table:

| Area | Exact purpose | Status | Action |
|---|---|---|---|
| Source and Profile | Official package identity and source | Complete | Review |
| Coverage and Document Structure | Sixteen coverage areas, required sections and ordered content | Complete | Review |
| Tender Parameters | Configurable and system-derived tender values | Complete | Review |
| IT Requirements | Requirement composer and downstream response structure | Complete | Review |
| Schedule, Inventory and Background | Delivery structure and bidder-relevant context | Complete | Review |
| Price Schedules | Four bidder price-table structures | Complete | Review |
| Evaluation and Qualification | Four evaluation stages and permitted criteria | Complete | Review |
| Forms and Evidence | Eighteen field-level bidder forms | Complete | Review |
| Contract and Outputs | SCC values, forms and downstream mappings | Complete | Review |

Completion card:

| Item | Value | Action |
|---|---|---|
| Coverage | 16 of 16 areas complete | View report |
| Blocking findings | 0 | View readiness |
| Warnings | 1 | View readiness |
| Complete preview | Available | Open preview |

Fixed footer: secondary **Run complete check**, primary **Submit for review**.

Do not show percentages, extraction counts, clause confidence, hashes or hidden “other” areas.

### 15.6 STD-UI-M02 — Draft assistance

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT > Draft assistance**

Modal:

- Title **Prepare Draft assistance**
- Text **Use reviewed prior configuration or AI assistance to prepare proposals. Nothing changes until you review and accept individual items.**
- Choice cards:
  - **Prior configured data** — **Use an earlier reviewed IT STD configuration dataset.**
  - **AI-assisted draft** — **Prepare proposals from the official source and existing Draft.**
- Selected choice **Prior configured data**
- Field **Configuration file** with **IT_STD_Config_Control_Pack_v3.json · Replace**
- Buttons **Cancel** and **Prepare proposals**

Proposal drawer artboard:

- Heading **Draft assistance proposals**
- Subtext **Prior configured data · 42 proposed items**
- Tabs **Document content 12**, **Fields and schemas 21**, **Mappings 9**; select **Fields and schemas 21**
- Table:

| Proposed item | Owning area | Current Draft | Action |
|---|---|---|---|
| Tender validity period | Tender Parameters | Not configured | Review |
| Security response structure | Forms and Evidence | Not configured | Review |
| Recurrent support price table | Price Schedules | Not configured | Review |

- Footer **Reject remaining proposals** and **Close**

Do not show confidence scores, Accept all, automatic save, automatic activation or hidden proposal rows.

### 15.7 PCFG-01 — Source and Profile

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT > Source and Profile**

Header: **Source and Profile**, quiet reference **Draft Version 1**, badge **Complete**.

Form card:

| Field | Exact displayed value |
|---|---|
| Package code | KE-PPRA-IT |
| Official title | Standard Tender Document for Procurement of Information Technology |
| Official issue | April 2021 edition |
| Requirement profile | Information Technology |
| Official source | PPRA IT Standard Tender Document.pdf · View · Replace |

Package code and Requirement profile are read-only. Footer **Back to package**, **Save Source and Profile**.

Do not show description, source URL, source reference, hash, effective date, parsing state or AI status.

### 15.8 PCFG-02 — Coverage and Document Structure

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT > Coverage and Document Structure**

Header: **Coverage and Document Structure**, quiet reference **Draft Version 1**, badge **Complete**.

Tabs **Coverage 16**, **Sections 13**, **Selected section**; select **Coverage 16**.

Coverage table contains all sixteen rows from section 5 with these shortened exact labels and results:

| No. | STD area | Treatment summary | Result | Action |
|---:|---|---|---|---|
| 1 | Tender identity and invitation | Locked + generated + parameters | Complete | View |
| 2 | Instructions to Tenderers | Locked + declared parameters | Complete | View |
| 3 | Tender Data Sheet | Parameters + generated values | Complete | View |
| 4 | Evaluation and Qualification | Evaluation schema | Complete | View |
| 5 | Non-price Tendering Forms | Locked + field-level forms | Complete | View |
| 6 | Price Schedule Forms | Price schemas | Complete | View |
| 7 | Requirements of the Information System | Requirement schema | Complete | View |
| 8 | Technical Requirements | Requirement schema | Complete | View |
| 9 | Implementation Schedule | Schedule schema | Complete | View |
| 10 | System Inventory Tables | Inventory schema | Complete | View |
| 11 | Background and Informational Materials | Structured background | Complete | View |
| 12 | General Conditions of Contract | Locked + contract links | Complete | View |
| 13 | Special Conditions of Contract | Contract parameters | Complete | View |
| 14 | Contract Forms and appendices | Locked + generated forms | Complete | View |
| 15 | Securities, declarations and evidence | Parameters + forms + mappings | Complete | View |
| 16 | Post-award administration forms | Contract Management mappings | Complete | View |

**Sections 13 tab artboard:** show rows **Invitation to Tender**, **Section I** through **Section IX**, **General Conditions of Contract**, **Special Conditions of Contract**, **Contract Forms**. Columns: Section, Blocks, Unresolved, Action. Exact block counts: `3, 4, 5, 4, 6, 4, 3, 4, 3, 3, 5, 4, 4`; every Unresolved value is `0`; every action is **Open**.

**Selected section tab artboard:** select **Section II — Tender Data Sheet** and show:

| Order | Content | Treatment | Binding | Action |
|---:|---|---|---|---|
| 1 | Tender Data Sheet introduction | Locked standard content | — | Edit content |
| 2 | Procuring Entity | Generated value | pe.official_name | Edit binding |
| 3 | Tender reference | Generated value | tender.reference | Edit binding |
| 4 | Clarification deadline | Parameter | tender.clarification_deadline | Edit binding |
| 5 | Tender validity | Parameter | tender.validity_days | Edit binding |

Buttons **Add locked content** and **Add declared slot**. Footer **Back to package**, **Save Document Structure**.

Do not show PDF page extraction, OCR text, confidence, clause hashes or an omitted-section control.

### 15.9 PCFG-03 — Tender Parameters

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT > Tender Parameters**

Header: **Tender Parameters**, quiet reference **Draft Version 1**, badge **Complete**.

Group tabs **Identity 5**, **Dates and meetings 7**, **Participation 5**, **Security 5**, **Submission 4**; select **Dates and meetings 7**.

Table:

| Parameter | Type | Supplied by | Required treatment | Output | Action |
|---|---|---|---|---|---|
| Tender issue date | Date | Tender Management | Required | Invitation | Edit |
| Clarification deadline | Datetime | Tender Preparation | Required | TDS | Edit |
| Clarification response deadline | Datetime | Tender Preparation | Required | TDS | Edit |
| Pre-tender meeting required | Yes/No | Tender Preparation | Required | TDS | Edit |
| Pre-tender meeting time | Datetime | Tender Preparation | Conditional | TDS | Edit |
| Submission deadline | Datetime | Tender Preparation | Required | Invitation and TDS | Edit |
| Tender validity | Duration in days | Tender Preparation | Required | TDS and Contract Formation | Edit |

Right-side selected definition panel:

- Heading **Tender validity**
- Label **Field label** value **Tender validity**
- Label **Value type** value **Duration**
- Label **Supplied by** value **Tender Preparation**
- Checkbox **Required** checked
- Label **Minimum days** value **120**
- Label **Rendered in** value **Section II — Tender Data Sheet**
- Label **Used by** value **Contract Formation**

Buttons **Add parameter** and footer **Back to package**, **Save Tender Parameters**.

Do not show a Tender-specific value, source paragraph, rule expression, hash or generic note.

### 15.10 PCFG-04 — IT Requirements

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT > IT Requirements**

Header: **IT Requirements**, quiet reference **Draft Version 1**, badge **Complete**.

Tabs **Categories 14**, **Requirement row 5**, **Allowed responses 5**, **Mappings 4**; select **Categories 14**.

Categories table shows all fourteen categories in section 7.8 with Order, Category and Edit. Do not truncate the list.

**Requirement row 5 tab artboard:** table:

| Field shown to department | Type | Required | Current effect |
|---|---|---|---|
| Category | Governed choice | Yes | Groups and renders the obligation |
| Supplier obligation | Long text | Yes | Tender and contract obligation |
| Bidder response | Governed choice | Yes | Supplier response field |
| Evidence required | Conditional choice | Conditional | Bidder evidence and evaluation input |
| Acceptance condition | Long text plus mode | Yes | Evaluation or contract acceptance |

**Allowed responses 5 tab artboard:** `Comply / Does not comply plus explanation`, `Narrative response`, `Numeric response`, `Demonstration`, `Test result`.

**Mappings 4 tab artboard:** Tender document → **Sections V and VI**; Bidder response → **Technical compliance response**; Evaluation → **Requirement evaluation input**; Contract → **Accepted supplier obligation**.

Footer **Back to package**, **Save IT Requirements**.

Do not show requirement transaction rows, scores, prices, source/author, generic priority, review status or PDF uploads.

### 15.11 PCFG-05 — Schedule, Inventory and Background

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT > Schedule, Inventory and Background**

Header: **Schedule, Inventory and Background**, quiet reference **Draft Version 1**, badge **Complete**.

Tabs **Implementation Schedule 6**, **System Inventory 8**, **Bidder Background 5**; select **Implementation Schedule 6**.

Schedule table:

| Column | Type | Required | Used in |
|---|---|---|---|
| Milestone | Text | Yes | Tender and contract |
| Required deliverable | Long text | Yes | Tender and contract |
| Completion rule | Duration or date | Yes | Tender and contract |
| Dependency | Milestone link | No | Tender and contract |
| Acceptance checkpoint | Long text | Yes | Evaluation and contract |
| Requirement links | Multi-link | No | Tender and evaluation |

**System Inventory 8 tab artboard:** show Hardware, Software, Licence, Service, Training, Support, Hosting and Integration. Columns: Category, Requirement link, Schedule link, Price Schedule link policy. Exact policies: Hardware `Required`; Software `Required`; Licence `Required`; Service `Required`; Training `Required`; Support `Required`; Hosting `Optional`; Integration `Required`.

**Bidder Background 5 tab artboard:** rows `Existing systems`, `Deployment sites`, `Current integrations`, `Data environment`, `Operating constraints`; each has treatment **Informational only** and output **Section IX**.

Blue notice on Background tab: **Supplier obligations must be configured in IT Requirements, not hidden in background information.**

Footer **Back to package**, **Save Schedule, Inventory and Background**.

Do not show actual project status, inventory prices, quantity, tax, hidden obligations or payment certification.

### 15.12 PCFG-06 — Price Schedules

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT > Price Schedules**

Header: **Price Schedules**, quiet reference **Draft Version 1**, badge **Complete**.

Left list:

1. Software and infrastructure
2. Implementation services — selected
3. Training
4. Recurrent support

Selected schema card:

| Column | Supplied from | Required | Calculation use |
|---|---|---|---|
| Line description | Approved scope | Yes | Display |
| Quantity | Approved scope | Yes | Line total |
| Unit | Approved scope | Yes | Display |
| Currency | Tender configuration | Yes | Financial evaluation |
| Unit price | Bidder | Yes | Line total |
| Tax amount | Bidder | Yes | Evaluated total |
| Total price | System calculated | Yes | Evaluated total |

Calculation card:

| Label | Value |
|---|---|
| Line total | Quantity × Unit price + Tax amount |
| Evaluated total | Sum of all four price schedules |
| Discount treatment | Applied only through the package-defined Tender Form |

Buttons **Add price schedule** and footer **Back to package**, **Save Price Schedules**.

Do not show actual prices, bidder names, arbitrary formula code, technical requirement editing or evaluation scores.

### 15.13 PCFG-07 — Evaluation and Qualification

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT > Evaluation and Qualification**

Header: **Evaluation and Qualification**, quiet reference **Draft Version 1**, badge **Complete**.

Stage tabs **Preliminary**, **Technical**, **Financial**, **Post-qualification**; select **Technical**.

Permitted criterion structures:

| Criterion structure | Treatment | Response source | Evidence source | Action |
|---|---|---|---|---|
| Mandatory requirement compliance | Pass / Fail | Requirement response | Requirement evidence | Edit |
| Technical response quality | Scored | Narrative response | Configured evidence | Edit |
| Demonstration result | Pass / Fail or scored | Demonstration record | Demonstration evidence | Edit |
| Key personnel capability | Scored | Personnel Form | Personnel evidence | Edit |
| Relevant experience | Pass / Fail or scored | Specific Experience Form | Contract evidence | Edit |

Threshold card:

| Label | Value |
|---|---|
| Technical scoring permitted | Yes |
| Minimum technical score required | Tender Preparation supplies a package-permitted value |
| Financial evaluation basis | Lowest evaluated responsive Tender |

Footer **Back to package**, **Save Evaluation and Qualification**.

Do not show bidder responses, evaluator assignments, actual scores, ranking, award recommendation or arbitrary executable formulas.

### 15.14 PCFG-08 — Forms and Evidence

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT > Forms and Evidence**

Header: **Forms and Evidence**, quiet reference **Draft Version 1**, badge **Complete**.

Left table shows all eighteen forms in section 7.13 without truncation. Columns: Form, Activation, Response treatment, Action.

Exact activation values:

- Always: Form of Tender; Tenderer Information; Confidential Business Questionnaire; Certificate of Independent Tender Determination; Self-Declaration; Fraud and Corruption; Beneficial Ownership.
- Conditional: Joint Venture Member Information; Historical Non-performance and Pending Litigation; General Experience; Specific Experience; Current Contract Commitments; Financial Situation; Average Annual Turnover; Financial Resources; Personnel Capability; Intellectual Property; Conformance of Information System Materials.

Select **Specific Experience**. Right panel:

| Field | Type | Required |
|---|---|---|
| Client organisation | Text | Yes |
| Contract title | Text | Yes |
| Contract value | Money | Yes |
| Start date | Date | Yes |
| Completion date | Date | Yes |
| Evidence | File evidence | Yes |

Footer **Back to package**, **Save Forms and Evidence**.

Do not show actual bidder files, evidence verification, scores, a generic attachment bucket or a form represented only as a PDF download.

### 15.15 PCFG-09 — Contract and Outputs

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT > Contract and Outputs**

Header: **Contract and Outputs**, quiet reference **Draft Version 1**, badge **Complete**.

Tabs **Contract values 12**, **Contract forms 4**, **Output mappings 7**, **Post-award 3**; select **Contract values 12**.

Contract values table:

| Value | Supplied by | Required treatment | Output |
|---|---|---|---|
| Performance security | Tender Preparation | Required | SCC and Contract Formation |
| Advance-payment security | Tender Preparation | Conditional | SCC and Contract Formation |
| Payment milestones | Tender Preparation | Required | SCC and contract schedule |
| Operational acceptance | Requirement and schedule data | Required | SCC and acceptance certificate |
| Warranty period | Tender Preparation | Required | SCC and contract |
| Support period | Tender Preparation | Required | SCC and contract |
| Intellectual-property treatment | Tender Preparation | Required | SCC and contract |
| Software licence categories | IT Requirements | Conditional | Contract appendix |
| Confidentiality | Package default plus Tender value | Required | SCC and contract |
| Insurance | Tender Preparation | Conditional | SCC and contract |
| Liability limit | Tender Preparation | Required | SCC and contract |
| Dispute resolution | Tender Preparation | Required | SCC and contract |

**Contract forms 4 tab:** Contract Agreement, Performance Security, Advance Payment Security, Acceptance Certificate; each treatment **Locked + generated fields**.

**Output mappings 7 tab:** Render, Requisition, Tender Preparation, Bidder Response, Evaluation, Contract Formation, Contract Management; every status **Resolved** and action **View mappings**.

**Post-award 3 tab:** Change Order Form, Acceptance Certificate, Contract Amendment Form; destination **Contract Management**, Tender configuration **Not shown**.

Footer **Back to package**, **Save Contract and Outputs**.

Do not show actual contract, supplier, inspection, payment, change-order transaction or post-award status.

### 15.16 STD-WF-01 — Coverage and Readiness Report

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT > Coverage and Readiness**

Header: **Coverage and Readiness**, quiet reference **Draft Version 1**, badge **Ready for review**.

Green notice **All sixteen STD areas are covered and the package has no blocking findings.**

Summary strip: **Coverage 16 of 16**, **Blocking 0**, **Warnings 1**, **Manifests 7 of 7**, **Preview Available**.

Coverage table repeats all sixteen labels from PCFG-02 with result **Pass** and action **View area**.

Warnings card:

| Area | Warning | Action |
|---|---|---|
| IT Requirements | Vendor-neutrality trigger includes named cloud platforms and requires reviewer attention. | Open IT Requirements |

Fixed footer **Back to package**, **Submit for review**.

Do not show score, percentage, waiver, dismiss, optional submission note or reviewer selector.

### 15.17 STD-WF-02 — Package Review

**Outside artboard:** David Mwangi · breadcrumb **Home > Standard Tender Documents > Review > KE-PPRA-IT Version 1**

Header:

- Eyebrow **STD PACKAGE REVIEW**
- Title **Procurement of Information Technology**
- Quiet reference **KE-PPRA-IT · Submitted Version 1**
- Badge **In review**

Tabs **Overview**, **Coverage 16**, **Configuration 9**, **Complete preview**, **History**; select **Overview**.

Review context:

| Label | Value |
|---|---|
| Official issue | April 2021 edition |
| Official source | PPRA IT Standard Tender Document.pdf · View |
| Configured by | Amina Hassan |
| Submitted | 25 Aug 2026, 14:30 EAT |
| Coverage | 16 of 16 areas passed |
| Blocking findings | 0 |
| Warnings | 1 |
| Runtime manifests | 7 generated successfully |

Warning notice repeats the exact Vendor-neutrality warning from STD-WF-01.

Confirmation text: **I have reviewed the complete package against the official source, including all configuration areas, mappings and the rendered preview.**

Checkbox **I confirm this review**.

Fixed footer **Return for correction**, **Activate package**.

**Coverage tab:** exact sixteen-row table from PCFG-02, read-only.

**Configuration tab:** exact nine-row configuration table from STD-UI-01, read-only, action **View**.

**Complete preview tab:** use STD-WF-03 content embedded without edit actions.

**History tab:** rows `25 Aug 2026, 14:30 EAT · Submitted for review · Amina Hassan`; `25 Aug 2026, 14:05 EAT · Complete check passed · Amina Hassan`; `25 Aug 2026, 09:00 EAT · Draft Version 1 created · System`.

Do not show editing, approval note, source parsing data, hidden sections or a summary without access to complete content.

**Return dialog artboard:** title **Return package for correction?**; text **The submitted package will remain unchanged. State the exact correction required.**; required label **Correction required**; value **Correct the bidder response mapping for Security requirements so the required evidence is available to technical evaluators.**; buttons **Cancel**, **Return for correction**. No category, assignee, due date, attachment or optional note.

### 15.18 STD-WF-03 — Complete Package Preview

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT > Complete preview**

Header: **Complete Package Preview**, quiet reference **Draft Version 1**, badge **Generated**.

Left section navigation lists all thirteen sections from PCFG-02. Select **Section II — Tender Data Sheet**.

Main preview card:

- Heading **Section II — Tender Data Sheet**
- Read-only rendered rows:

| Tender Data Sheet item | Preview value |
|---|---|
| Procuring Entity | [Generated from Tender context] |
| Tender reference | [Generated from Tender context] |
| Clarification deadline | [Tender Preparation value] |
| Tender validity | [Tender Preparation value in days] |

Blue notice **Placeholders show the exact runtime owner because this is an STD package preview, not a configured Tender.**

Toolbar buttons **Previous section**, **Next section**. Secondary action **Open source document**. No footer decision action.

Do not show editable fields, real Tender fixture values, raw binding keys, HTML, hashes or omitted sections.

### 15.19 STD-WF-04 — Active Version

**Outside artboard:** Amina Hassan · breadcrumb **Home > Standard Tender Documents > KE-PPRA-IT**

Use Package Home geometry with quiet reference **KE-PPRA-IT · Version 1**, badge **Active**, and green notice **Version 1 is available to Procurement Requisitions and Tender Preparation.**

Configuration table remains nine complete read-only rows. Add Runtime Outputs card:

| Output | Status | Action |
|---|---|---|
| Requirement Composer | Available | Preview |
| Tender Configuration | Available | Preview |
| Bidder Response | Available | Preview |
| Evaluation | Available | Preview |
| Contract Formation | Available | Preview |
| Contract Management | Available | Preview |
| Render | Available | Preview |

Footer **Open complete preview**, **Create new version**.

Do not show Edit, regenerate from PDF, replace source, deactivate or amend Active Version.

### 15.20 STD-WF-05 — Version Comparison

**Outside artboard:** David Mwangi · breadcrumb **Home > Standard Tender Documents > Review > KE-PPRA-IT Version 2 > Comparison**

Header **Changes from Active Version 1**, quiet reference **Submitted Version 2 · June 2028 revision**, badge **In review**.

Summary: **Changed areas 3**, **Added definitions 2**, **Changed definitions 3**, **Removed definitions 0**.

Table:

| Area | Active Version 1 | Submitted Version 2 | Action |
|---|---|---|---|
| Tender Parameters | Tender validity minimum 120 days | Tender validity minimum 150 days | View change |
| Forms and Evidence | 18 forms | 19 forms; added Data Protection Compliance Form | View change |
| Contract and Outputs | Support period required | Support period and security-incident notification required | View change |

Text **Thirteen coverage areas have no configured change.**

Do not show a user-entered change summary, accept/reject individual changes, PDF text diff or hidden unchanged-area list.

### 15.21 STD-STATE — Common states

Create exact variants:

| State | Heading | Text | Control |
|---|---|---|---|
| No assignment | Standard Tender Documents is not available | You do not have an active STD configuration assignment. | None |
| Assistance preparing | Preparing Draft proposals | Your current Draft is unchanged while proposals are prepared. | Cancel assistance |
| Assistance failed | Draft assistance could not be prepared | Your Draft was not changed. Try again or continue configuring manually. | Try again |
| Stale Draft | This Draft changed | Reload the configuration area before saving your changes. | Reload |
| Coverage incomplete | Package coverage is incomplete | Complete every required STD area before submission. | Open Coverage Report |
| Manifest failure | Runtime outputs could not be generated | Correct the reported package configuration and run the complete check again. | Open Readiness Report |
| Load error | Standard Tender Documents could not be loaded | Try again. If the problem continues, quote the support reference shown below. | Try again |

Only Load error may show a generated support reference. Do not add illustrations, diagnostics or alternate controls.

## 16. Functional interactions — excluded from Claude Design

### 16.1 Library and Drafts

- Opening, filtering or previewing creates nothing.
- Package identity comes from governed seed/configuration; there is no blank family form in MVP-1.
- One package has one Active Version and one open Draft maximum.
- Creating Version 2 copies Version 1 server-side and binds the new official source; it does not alter Version 1.
- Draft content is editable only by the effective Configurator while Draft or Returned.

### 16.2 Draft assistance

- Prior-data assistance accepts only the supported clean import contract; it never reads retired database objects at runtime.
- AI assistance produces proposals from the official source, current Draft and approved configured reference data. It does not save package records directly.
- A proposal set is bound to one Draft record version. Any subsequent Draft change makes it stale.
- The Configurator reviews each proposed item in its owning area and accepts or rejects it deliberately.
- There is no **Accept all** command.
- Accepted items pass the same local validators as direct entry.
- Assistance failure or cancellation creates no package change.
- No confidence score replaces coverage or human review.

### 16.3 Configuration areas

- Required sections and sixteen coverage rows cannot be deleted.
- Locked text is entered deliberately and rendered without transaction editing.
- Configurators choose only governed block, value, response, evidence, criterion and mapping types.
- Conditions are assembled from governed keys/operators; user-authored executable code is prohibited.
- Removing a definition is blocked while a block or mapping refers to it.
- Background information cannot create an obligation. A supplier obligation must exist in IT Requirements.
- Inventory contains technical disclosure only. Commercial quantity, unit, tax and totals belong to Price Schedules.
- Forms required for bidder response or evaluation have field-level schemas.
- Post-award forms are mapped but not exposed as Tender configuration steps.

### 16.4 Validation, review and activation

- Area save validates the changed area and immediate edges only.
- **Run complete check** validates all definitions, coverage, manifests and rendering.
- **Submit for review** repeats the complete check and creates one immutable submitted snapshot/task atomically.
- Review tabs always read the submitted snapshot; they never fall back to the current Draft or Active Version.
- Reviewer **Return** preserves the submitted snapshot and opens a copied correction Draft with one exact correction.
- Reviewer **Activate** requires confirmation, maker-checker and unchanged snapshot.
- Activation generates Version and all seven manifests atomically. Any failure rolls back the entire activation.

### 16.5 Runtime

- New downstream instances use the currently Active applicable Version.
- Existing instances use their bound Version even after supersession.
- Manifests are server-authorised, immutable and cacheable by internal revision.
- Consumers receive validated structures, not configuration DocTypes for client-side interpretation.
- No manifest endpoint permits mutation.
- Render rejects an unresolved slot and escapes transaction values.
- Tender Preparation stores transaction values against stable manifest item keys; it does not copy package definitions into editable Tender records.
- Tender Preparation shall render every applicable manifest item exactly once in its owning step.
- A consumer may not weaken a manifest requirement, substitute an attachment for a structured composer or treat an unresolved binding as optional.
- Tender Configuration Instance validation is performed server-side against its bound manifest Version.
- A manifest-version change requires a new downstream instance or an explicit future migration specification; it is never automatic.

### 16.6 Accessibility and Frappe lifecycle

- Use semantic headings, tabs, labels, tables, dialogs, drawers and status text.
- Colour is never the only status carrier.
- Focus moves to the first invalid field or error summary and returns after modal/drawer close.
- Pending actions disable repeat submission and reuse one idempotency key.
- Direct routes enforce the same assignment scope as list reads.
- Vue unmounts on route change and stale requests are cancelled.
- Browser tests wait for DOM readiness and a stable page-ready selector, not Frappe `networkidle`.

## 17. Deterministic seed and configured-content reuse

### 17.1 Golden package fixture

Seed `STD-IT-V1-GOLDEN` creates:

- package `KE-PPRA-IT`;
- Draft Version 1;
- the exact official-source fixture identity in section 15.2;
- all sixteen coverage rows;
- all thirteen required sections;
- every exact row, count and label used in section 15;
- all fourteen requirement categories;
- schedule, eight inventory categories and five background structures;
- four price schemas;
- four evaluation stages;
- eighteen form schemas;
- twelve contract values, four contract forms and three post-award mappings;
- seven runtime-output definitions; and
- exact actors and task states required by the artboards.

The fixture must be internally complete and renderable. It is a deterministic product/test package, not a claim that the short fixture text reproduces the entire official legal document.

### 17.2 Production IT configuration

The production IT package shall be completed against the official STD by deliberately reusing the valuable earlier IT STD work. Reuse is expected; discarding that work and starting the content analysis again is not the default implementation path.

The earlier work is input evidence, not an Active package. Each reusable item must be transformed into the new v1.3 model, reviewed in its owning configuration area and validated like directly entered content.

### 17.3 Required reuse inputs

Before transformation begins, the implementation team shall assemble a read-only reuse bundle containing all available items in these classes:

| Input class | Expected examples | Purpose |
|---|---|---|
| Product and control documents | `01 IT_Tender_Configuration_Wizard_PRD`, `A1_IT_Tender_Wizard_Product_Control_Document_v3`, `A2_IT_Tender_Wizard_Complete_Screen_Registry_v3`, `A3_IT_Tender_Wizard_STD_Coverage_and_Control_Addendum_v3`, and the control-pack changelog | Recover reviewed coverage, ownership, labels, structures and product decisions. |
| Configured STD content | Section inventory, locked text, TDS definitions, requirements, schedules, inventories, price tables, criteria, forms, SCC values and output mappings | Populate new Draft definitions without repeating completed analysis. |
| Working wizard fixtures | Reviewed IT Tender examples, choices, help text, table columns and conditional examples | Supply candidate labels, fixtures and condition cases. |
| Existing implementation exports | Read-only JSON/CSV or deterministic exports of relevant old configuration records | Provide source values for one-time transformation where the content cannot be recovered reliably from control documents. |
| Official source | Exact PPRA IT STD issue being configured | Sole authority for completeness and wording verification. |

The reuse bundle shall not include production credentials, bidder data, live Tender transactions, evaluation results or contract transactions.

If an expected earlier dataset cannot be located, the team records it as `Unavailable` in the register below and configures that target area directly from the official source. It shall not guess the missing content.

### 17.4 Reuse disposition register

The team shall create one machine-readable and human-readable register before importing content. One row represents one source dataset, document section, schema group or other independently reviewable unit.

| Field | Required content |
|---|---|
| `reuse_item_id` | Stable one-time transformation reference. |
| `source_name` | Exact document, export file or old object family. |
| `source_location` | Read-only repository path or controlled file reference. |
| `source_scope` | Exact sections, rows or records covered. |
| `content_class` | Locked text, Parameter, Requirement, Schedule, Inventory, Background, Price, Evaluation, Form, Contract, Mapping, Label/Help or Fixture. |
| `target_area` | Exact PCFG-01 through PCFG-09 owner. |
| `target_entity` | Exact v1.3 entity from section 7. |
| `disposition` | `Reuse as proposal`, `Rewrite from official source`, `Reference only`, `Retire` or `Unavailable`. |
| `transformation` | Exact normalization or field mapping required. |
| `verification` | Official section, control rule and structural check used to accept it. |
| `result` | Proposed-row count, rejected-row count and unresolved count after the transformation run. System-derived. |

There is no generic comment or confidence field. A disposition must be supported by the named source, target and verification method.

### 17.5 Mandatory source-to-target disposition

The initial register shall cover at least the following. “Reuse” means transform to reviewable proposals, not copy directly into an Active package.

| Earlier work | Target in v1.3 | Required disposition and transformation |
|---|---|---|
| IT STD identity, edition and section inventory | `STDPackage`, `STDDraft`, `STDSourceDocument`, coverage rows | Reuse reviewed identity and inventory; verify exact issue against the official source. Generate new IDs. |
| Official section ordering and headings | `STDSection` | Reuse as proposals; normalize to the required thirteen-section order and sixteen-area coverage register. |
| Reviewed standard wording | `STDContentBlock` | Reuse only where the official issue matches exactly; split into ordered locked blocks and declared slots. Rewrite any uncertain or parser-damaged text from the official source. |
| TDS configuration and prior wizard fields | `STDParameterDefinition` and Tender Configuration items | Reuse labels, choices, conditions and mappings as proposals; convert them to the section 7.18 item contract and section 9 ownership. Remove duplicate transaction fields. |
| Requirements System and Technical Requirements configurations | `STDRequirementSchema` | Reuse categories, response types, evidence and acceptance structures; normalize every row to the five-field contract and four required downstream mappings. |
| Implementation Schedule configuration | `STDScheduleSchema` | Reuse milestone and deliverable structures; remove transaction results and normalize to section 9.8. |
| System Inventory tables | `STDInventorySchema` | Reuse technical disclosure fields; move commercial columns to Price schemas and supplier obligations to Requirements. |
| Background and informational structures | Background definitions in PCFG-05 | Reuse bidder-relevant context structures; rewrite any entry that hides a supplier obligation. |
| Price Schedule forms and calculations | `STDPriceSchema` | Reuse table structures, formulas and evaluation-total logic; normalize scope links and prevent duplicate pricing. Do not import bidder prices. |
| Evaluation and qualification configuration | `STDEvaluationSchema` | Reuse stage order, criteria structures, evidence sources, thresholds and calculations; remove any actual evaluation result or generic unmapped criterion. |
| Non-price Tendering Forms | `STDFormSchema` | Reuse exact field-level forms, declarations and evidence rules; replace attachment-only collection where structured fields already exist. |
| Contract forms, GCC/SCC definitions and appendices | `STDContractSchema` and `STDContentBlock` | Reuse verified locked content, permitted SCC values and carry-forward mappings; exclude post-award transaction data. |
| Securities and declarations | Parameter, Form and Contract definitions | Reuse governed alternatives, conditions and field schemas; ensure each has render, bidder/evaluation and contract treatment as applicable. |
| Change-order and administration form definitions | Contract Management output mappings | Reuse schemas and mappings as proposals; do not expose them as Tender configuration steps or import completed forms. |
| Earlier Wizard screen labels and help text | Section 9 manifest labels/help | Reference and reuse where the same definition survives; do not reuse old layouts, route code or obsolete fields. |
| Earlier sample IT Tender data | Golden fixture and later Tender Preparation fixture | Reuse reviewed realistic values after removing transaction identifiers that conflict with the deterministic section 9.15 fixture. |
| PDF/OCR/parser output with no verified configured counterpart | None by default | Retire. It may be consulted only to locate official text for human review; it cannot produce accepted records. |
| Parser, OCR, inferred-schema, legacy runtime and compatibility code | None | Retire. Do not import, wrap, call or preserve it. |

### 17.6 One-time transformation procedure

The transformation shall be a bounded implementation utility, not a production parsing service.

1. **Freeze inputs.** Copy the selected reuse bundle to a read-only controlled location and record exact filenames or export identities in the disposition register.
2. **Inventory.** Produce register rows for every reusable content group before writing Draft records.
3. **Map.** Define deterministic source-to-target field mappings for each `Reuse as proposal` row. Unmapped source fields fail the row; they are not silently dropped.
4. **Transform.** Convert source content into `STDAssistanceBatch` proposals using new stable proposal IDs. Do not retain old runtime primary keys as package identity.
5. **Report.** Produce counts for source items, proposed items, retired items, duplicates, unmapped fields and transformation failures by PCFG area.
6. **Review.** Present proposals in the owning PCFG area. The Configurator accepts or rejects individual items; there is no **Accept all**.
7. **Verify locally.** Accepted items pass their target entity validators and mapping checks before saving.
8. **Reconcile coverage.** Compare the resulting Draft against all sixteen coverage areas, thirteen official sections and the source-to-target register.
9. **Complete gaps.** Configure missing or rejected content directly from the official source or through separately reviewed AI proposals.
10. **Run full controls.** Generate all seven manifests and the complete rendered preview.
11. **Review independently.** The STD Reviewer compares the complete submitted snapshot with the official STD, not with the old implementation.
12. **Archive evidence.** Preserve the register, transformation report and proposal decisions as implementation evidence. Do not deploy the old input bundle as a runtime dependency.

The utility may be rerun against a fresh Draft during development. It shall refuse to write to an Active Version, a submitted snapshot or an ordinary production transaction.

### 17.7 Transformation rules

- Use exact stable target keys defined by the new package; never derive authority from old IDs.
- Preserve verified text faithfully. Do not paraphrase locked official wording.
- Normalize whitespace, ordering and known enumerations only through explicit mappings.
- Detect duplicate semantic keys before creating proposals.
- Preserve source order where it represents official document order.
- Split combined legacy objects when their parts belong to different target owners.
- Merge duplicates only where the mapping identifies the same official definition and reports the merge.
- Reject an unrecognized choice, condition operator, response type, calculation or output target.
- Do not convert an attachment into a structured schema by assumption. Configure the schema from the reviewed earlier work or official source.
- Do not infer missing obligations, criteria, forms or contract terms.
- AI may propose a missing mapping or configuration item, but its proposal follows the same item-level review path and is identified as `AI-assisted draft`.
- Accepted content loses its “legacy” or “AI” operational character: it becomes an ordinary Draft record governed by its target definition and review history.

### 17.8 Reuse reconciliation report

The final report shall show, for every PCFG area:

| Measure | Required result before submission |
|---|---|
| Registered source groups | Every located earlier content group is represented. |
| Reused proposals | Count and accepted/rejected result are visible. |
| Rewritten items | Count and official-source verification are visible. |
| Retired items | Count and retired class are visible. |
| Unavailable inputs | Identified with the target gap they created. |
| Unmapped source fields | Zero. |
| Transformation failures | Zero unresolved. |
| Duplicate target keys | Zero. |
| Missing target definitions | Zero Blocking. |

The report also provides the system-derived totals:

- sixteen of sixteen coverage areas accounted for;
- thirteen of thirteen official sections accounted for;
- nine of nine package configuration areas reconciled;
- seven of seven runtime manifests generated; and
- zero Blocking findings.

These totals prove controlled transformation and structural completeness. They do not replace the Reviewer's comparison with the official source.

### 17.9 Reuse acceptance gate

Earlier work has been safely reused only when:

1. every available input class has a register disposition;
2. no prohibited runtime or parser component is imported;
3. every accepted proposal exists as a valid new Draft entity;
4. all unmapped source fields and transformation failures are resolved;
5. all sixteen coverage areas and thirteen official sections pass;
6. the complete section 9 Tender Configuration Manifest is generated;
7. all seven runtime manifests pass their contracts;
8. the complete IT STD preview renders without an unresolved slot;
9. the Reviewer can trace accepted reused content to its source register row; and
10. independent review confirms the complete package against the official IT STD.

Successful import alone is not acceptance.

### 17.10 Seed rules

- Run only on an explicitly selected development/test site.
- Upsert by exact stable fixture identifiers.
- Second run produces no semantic change.
- Never alter an Active production package.
- Fail loudly on any missing coverage row, unresolved mapping or invalid fixture.
- Do not print per-row logs during normal execution.

## 18. Acceptance and testing

The module is accepted only when:

1. no retired parser, inference service or legacy runtime object is required;
2. all sixteen IT STD areas are represented and visible;
3. every package definition has a current render or downstream use;
4. prior configured data can produce reviewable Draft proposals without direct activation;
5. AI assistance can produce reviewable proposals without direct save or activation;
6. locked content, parameters and structured schemas render in deterministic order;
7. Requirement Composer produces the exact five-field Requisition row contract;
8. Tender Configuration produces the complete section 9 contract, including every item property, source, condition, validation, completion rule, render binding and downstream mapping;
9. field-level bidder forms and price tables are generated;
10. evaluation structures bind to exact bidder responses/evidence/prices;
11. contract and post-award mappings terminate at named consumers;
12. incomplete coverage or manifest failure blocks submission and activation;
13. Reviewer can inspect all sixteen areas, nine configuration areas and complete preview;
14. Active Version and manifests are immutable;
15. supersession does not change existing bound instances;
16. every screen in section 14 has the exact section 15 contract; and
17. no design surface invents or omits data;
18. the worked IT Tender instance completes all nine steps and produces a full readiness result;
19. every generated or inherited Tender item resolves to its named source;
20. every applicable manifest item appears exactly once in its owning Tender step; and
21. Tender Preparation can consume the manifest without reading STD configuration DocTypes or inventing configuration rules;
22. every located earlier IT STD content group has an explicit section 17 disposition;
23. the one-time transformation reports zero unresolved unmapped fields, failures or duplicate target keys;
24. accepted reused content is traceable to its register row and valid new Draft entity; and
25. no retired parser, inference or legacy runtime component is a production dependency.

### 18.1 Focused automated coverage

- package/Draft/Active uniqueness;
- source and immutable Version binding;
- required coverage rows and sections;
- content treatment and block ordering;
- parameter types, choices and conditional requirements;
- Requirement Composer schema and four downstream mappings;
- schedule, inventory and background ownership boundaries;
- price calculation definitions;
- evaluation response/evidence bindings;
- eighteen field-level forms;
- contract and post-award mappings;
- local vs complete validation behavior;
- assistance proposal isolation, staleness, selective acceptance and failure rollback;
- reuse-register completeness and governed dispositions;
- one-time source-to-target mapping, split, merge and rejection cases;
- refusal of unmapped source fields and prohibited source classes;
- transformation idempotence against a fresh Draft;
- transformation refusal against Active, submitted and transaction records;
- reconciliation counts across all nine PCFG areas;
- reviewer authority and maker-checker;
- atomic activation and manifest rollback;
- immutable bound-version reads;
- manifest identity and immutable Requisition-to-Tender Version binding;
- exact nine-step and item ordering;
- all five source-mode and editability treatments;
- TDS conditional groups and cross-field chronology;
- Tender-step completion and complete-readiness derivation;
- fixture values against render, bidder, evaluation, contract and publication mappings;
- no missing, duplicated or unowned manifest item;
- fixture-to-artboard contract tests; and
- one browser path: Library → Package Home → each PCFG area → Complete Check → Review tabs → Preview → Activate.

### 18.2 Efficient TDD loop

1. Write or select the smallest failing test.
2. Implement the smallest coherent change.
3. Run that test module.
4. Run the owning configuration-area tests.
5. Run mapping contract tests only when an edge changes.
6. Run the relevant component/browser test when its surface changes.
7. Run the full STD suite once at the release gate.

Do not rerun the full Bench or KenTender suite after a label, layout or isolated validator correction.

### 18.3 Release evidence

- clean-site install and migrate;
- static proof that retired parsing routes are unreachable;
- completed reuse disposition register;
- one-time transformation report with source, proposal, rejection, retirement, failure and reconciliation counts;
- proof that the application runtime does not import or call the transformation utility;
- complete golden-package validation;
- seven manifest contract results;
- focused domain, permission and activation results;
- one complete browser journey with screenshots for every registered surface;
- production build without global CSS regression; and
- successful second seed run with no semantic change.

## 19. Implementation constraints

- Build new package records and services in the owning app namespace.
- Do not import retired STD controllers, extracted-clause tables, parsers, OCR utilities or inferred-schema fixtures.
- Do not add production dependencies for OCR or general PDF parsing.
- AI assistance is an optional authoring adapter behind the proposal contract; the core runtime works without it.
- Prior configured data enters through the same proposal contract or deterministic package configuration—not legacy database reads.
- The one-time reuse utility is development/controlled-deployment tooling. It is not called by package, Tender, bidder, evaluation or contract runtime paths.
- The reuse utility and its input bundle may be removed from the deployed application after the production IT package is accepted; the disposition register and transformation report remain controlled evidence.
- Keep domain invariants server-side and Vue pages thin.
- Use existing KenTender components, tokens and the proven Vue 3/Frappe Desk mounting pattern.
- Keep Claude Design exports under documentation as visual evidence; ship no design runtime.
- Do not add Tailwind, CDN styles, global resets or a second application shell.
- Use stable test IDs only on primary controls, tabs, rows, statuses, errors, drawers and dialogs.

## 20. Approval effect and next work

On approval:

1. Proposed STD-CHG-001 v1.0, v1.1 and v1.2 are rejected and superseded by v1.3.
2. STD-ADR-001 is revised to record curated configuration, optional Draft assistance and retirement of authoritative parsing automation.
3. The clean IT package workspace and runtime are implemented from this document.
4. The useful earlier IT configuration content is transformed into reviewable new Draft configuration.
5. The complete IT vertical slice is proven.
6. REQ-CHG-001 v1.1 then replaces attachment-centred technical documents with the Active Requirement Composer Manifest and structured Requirement Package.
7. Tender Preparation is defined after the revised Requisition contract is approved.
