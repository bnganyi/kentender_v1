# STD for Procurement of Information Technology - Full Source Extraction Pass 1

**Package:** `KE-PPRA-IT-2022-04`  
**Target engine:** Generalized STD Engine Core  
**Artifact status:** Draft extraction register - not activatable  
**Generated:** 2026-07-07 20:16 UTC

## 1. Purpose

This document is the first full source extraction pass for the official PPRA Standard Tender Document for Procurement of Information Technology. It does not attempt to rewrite or improve the legal text. Its purpose is to establish the controlled source anchors, section registry, mutability decisions, and locked clause register that will be used to populate the `KE-PPRA-IT-2022-04` seed package.

The key design decision remains: the STD Engine must be generalized. The IT STD is one template family/version inside the engine, not a special-purpose hard-coded module.

## 2. Source documents and extraction evidence

| Source | File | Role | Hash / identifier | Use in this pass |
| --- | --- | --- | --- | --- |
| Official IT STD | DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.doc | Legal master source | 1a69541b29c6acde23198cfdd021bef1ed45d4816ffe482e17d0cd1cfce72eed | Primary source for sections, anchors, mutability, ITT/GCC locked clause register. |
| Rendered extraction PDF | DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.pdf | Internal extraction derivative | 0ba4c142d1ccbb62b6c7d8ffaaf96c8fdd3b069198c9b377f7b8e7c325bda127 | Used only to obtain page-based anchors from the .doc source. Not a legal source by itself. |
| Layout text extraction | it_std_layout.txt | Internal extraction derivative | d704b39b278e20972c0a5243135050a90092650aad7307d7f1214f2e6c79dca1 | Used only to support anchor discovery and clause heading discovery. |
| NSSF SPS ERP tender | NSSF SPS RFP ERP 2026(1).pdf | Calibration fixture | Uploaded file | Used later to validate that the IT STD model can generate a real ERP-style tender. Not used as legal master source. |

## 3. Extraction conventions

| Convention | Decision |
| --- | --- |
| Internal IDs | Use stable engine IDs such as `IT-STD-ITT`, `ITT-001`, and `GCC-001`. These IDs do not depend on visible source numbering being perfect. |
| Source-visible labels | Preserve the source document's visible headings and numbering in rendered legal text unless an approved legal correction is issued. |
| Page anchors | Use page numbers from the rendered source document extraction. These anchors are for traceability and review; exact paragraph anchors and text hashes are a Pass 2 task. |
| Mutability | Classify each section as `LOCKED`, `CONTROLLED_CONFIG`, `CONTROLLED_AUTHORING`, `STRUCTURED_FORMS`, or `GENERATED`. |
| Locked text | ITT and GCC are locked. Tender-specific modification occurs through TDS and SCC only. |
| Legal review | This pass identifies extraction anomalies. It does not silently correct source text, numbering, or legal wording. |

## 4. Section/source anchor map

| Engine section ID | Source section | Functional role | Mutability | Source anchor | Extracted scope | Implementation handling |
| --- | --- | --- | --- | --- | --- | --- |
| IT-STD-COVER | Cover Page | Administrative cover | Excluded from tender issue / source identity | Page 1 | Official source metadata and cover image | Do not render into issued tender except where PE identity cover is generated. |
| IT-STD-TOC | Table of Contents | Administrative navigation | System-generated | Pages 2-6 | TOC lists full STD structure | Generated from render blocks; source TOC preserved only as source reference. |
| IT-STD-PREFACE | Preface | Guidance / legal context | Administrative guidance; excluded from issued tender | Pages 7-8 | Prepared by PPRA for IT procurement; mandatory use; ITT/GCC not to be changed | Retain in master package but exclude from bidder-issued tender bundle. |
| IT-STD-APP-PREFACE | Appendix to Preface / Guidelines | Preparation guidance | Administrative guidance; excluded from issued tender | Pages 9-10 | Instructions on preparing TDS, criteria, forms, requirements, SCC | Retain as user guidance and validation basis. |
| IT-STD-START-PAGE | Beginning Page for Issued Document | Issued-document identity page | Parameterized generated | Page 11 | PE name/logo/address, tender name, invitation number | Generated from Tender STD Configuration values. |
| IT-STD-INVITATION | Invitation to Tender | Tender notice | Parameterized generated | Pages 12-13 | PE, contract name, method, eligibility, addresses, security, submission deadline | Generated and published as part of tender bundle. |
| IT-STD-PART1 | Part 1 - Tendering Procedures | Part heading | Generated heading | Page 14 | Heading only | Render block wrapper. |
| IT-STD-ITT | Section I - Instructions to Tenderers | Tender procedure law/rules | LOCKED | Pages 15-34 | Clause-level ITT content | Locked legal text; supplemented only through TDS parameters. |
| IT-STD-TDS | Section II - Tender Data Sheet | Tender-specific supplements | CONTROLLED_CONFIG | Pages 35-40 | Specific data supplementing/amending ITT | User-editable only through controlled parameter schema. |
| IT-STD-EVAL | Section III - Evaluation and Qualification Criteria | Evaluation rules | CONTROLLED_CONFIG | Pages 41-48 | Responsiveness, technical, price, margin, qualification/personnel | Data-driven evaluation schema; additions constrained by STD. |
| IT-STD-FORMS | Section IV - Tendering Forms | Bidder response forms | STRUCTURED_FORMS | Pages 49-85 | Form of tender, declarations, price tables, qualification forms, IP forms, conformance forms | Generate supplier portal forms and rendered forms from schemas. |
| IT-STD-PART2 | Part 2 - Procuring Entity's Requirements | PE requirements part | CONTROLLED_AUTHORING | Pages 86-103 | Requirements of Information System, technical requirements, implementation schedule, inventory tables, background | Must be authored in structured composer; free-text allowed only in controlled fields. |
| IT-STD-REQ | Section V - Requirements of the Information System | IT requirements | CONTROLLED_AUTHORING | Pages 86-103 | Functional, architectural, performance, service, technology, implementation, inventory, background | Native IT Requirements Composer. |
| IT-STD-PART3 | Part 3 - Conditions of Contract and Contract Forms | Contract part | Mixed | Page 104 | Part heading | Render block wrapper. |
| IT-STD-GCC | Section VI - General Conditions of Contract | General contract conditions | LOCKED | Pages 105-139 | 43 GCC clauses | Locked legal text; supplemented only through SCC. |
| IT-STD-SCC | Section VII - Special Conditions of Contract | Contract-specific supplements | CONTROLLED_CONFIG | Pages 140-149 | GCC clause-specific special conditions | User-editable only through SCC parameter schema. |
| IT-STD-CONTRACT-FORMS | Section XIII - Contract Forms | Post-award contract artifacts | STRUCTURED_FORMS / GENERATED | Pages 150-181 | Notification, award, agreement, appendices, securities, acceptance, change order, beneficial ownership | Generated after award using tender, winning bid, and contract finalization data. |

## 5. Locked ITT clause register

The following register identifies the locked Instructions to Tenderers clauses. Full canonical clause text, paragraph anchors, and text hashes should be extracted in Pass 2. The current pass locks the clause boundary, page anchor, mutability, and configuration implications.

| Internal ID | Source visible no. | Clause title | Source page anchor | Treatment | Configuration / engine note |
| --- | --- | --- | --- | --- | --- |
| ITT-001 | 1 | Scope of Tender | 15 | Locked | TDS supplies PE, tender name, lots/contracts. |
| ITT-002 | 2 | Definitions | 15 | Locked | Definition text locked; e-procurement wording parameterized through TDS where allowed. |
| ITT-003 | 3 | Fraud and Corruption | 15 | Locked | Declaration/form linkage to Form of Tender and declarations. |
| ITT-004 | 4 | Eligible Tenderers | 15-17 | Locked | TDS may set JV maximum, registration requirements, consultant conflict declarations. |
| ITT-005 | 5 | Eligible Goods and Services | 17 | Locked | Eligibility scope for information system goods/services. |
| ITT-006 | 6 | Sections of Tendering Document | 18 | Locked | Engine must preserve/source-normalize section list. |
| ITT-007 | 7 | Clarification of Tendering Document, Site Visit, Pre-tender Meeting | 18-19 | Locked | TDS determines clarification address, site/pre-tender meeting occurrence and details. |
| ITT-008 | 8 | Amendment of Tendering Document | 19 | Locked | Addendum model must implement this; post-publication changes require addendum. |
| ITT-009 | 9 | Cost of Tendering | 19 | Locked | No configuration except inherited PE context. |
| ITT-010 | 10 | Language of Tender | 19 | Locked | TDS may specify language if allowed by source wording. |
| ITT-011 | 11 | Documents Comprising the Tender | 19-20 | Locked + form activation | TDS may require additional documents; forms and evidence checklist generated. |
| ITT-012 | 12 | Form of Tender and Price Schedules | 20 | Locked | Linked to Section IV form and price schedule schemas. |
| ITT-013 | 13 | Alternative Tenders | 20-21 | Locked + controlled option | TDS permits/prohibits alternatives and declares evaluation method where applicable. |
| ITT-014 | 14 | Documents Establishing the Eligibility of the Information System | 21 | Locked | Supplier evidence and technical conformance form linkage. |
| ITT-015 | 15 | Documents Establishing Eligibility and Qualifications of the Tenderer | 21-22 | Locked | Qualification forms/evidence rules generated. |
| ITT-016 | 16 | Documents Establishing Conformity of the Information System | 22 | Locked | Controls supplier technical response/conformance matrix. |
| ITT-017 | 17 | Tender Prices | 22-23 | Locked | Price schedule schema must cover supply/install and recurrent costs. |
| ITT-018 | 18 | Currencies of Tender and Payment | 23 | Locked + TDS option | TDS controls currency/currencies. |
| ITT-019 | 19 | Period of Validity of Tenders | 24 | Locked + parameter | TDS controls validity period. |
| ITT-020 | 20 | Tender Security | 24-25 | Locked + parameter | TDS controls security type, value, validity, acceptable instruments. |
| ITT-021 | 21 | Format and Signing of Tender | 25 | Locked + parameter | TDS controls copies/originals/e-proc submission particulars. |
| ITT-022 | 22 | Submission, Sealing and Marking of Tenders | 25-26 | Locked + parameter | TDS controls submission address, marking, e-proc details. |
| ITT-023 | 23 | Deadline for Submission of Tenders | 26 | Locked + parameter | TDS controls deadline datetime and timezone. |
| ITT-024 | 24 | Late Tenders | 26 | Locked | Hard rule: late tender handling. |
| ITT-025 | 25 | Withdrawal, Substitution, and Modification of Tenders | 26 | Locked | Tender submission workflow must support/forbid according to stage. |
| ITT-026 | 26 | Tender Opening | 26-27 | Locked + parameter | TDS controls opening venue/date/time and records read-out requirements. |
| ITT-027 | 27 | Confidentiality | 27 | Locked | Evaluation privacy/audit rule. |
| ITT-028 | 28 | Clarification of Tenders | 27 | Locked | Clarification workflow must preserve audit trail and no price/substance change. |
| ITT-029 | 29 | Deviations, Reservations, and Omissions | 27-28 | Locked | Evaluation flags and responsiveness findings. |
| ITT-030 | 30 | Determination of Responsiveness | 28 | Locked | Evaluation workflow block/pass rules. |
| ITT-031 | 31 | Non-material Non-conformities | 28 | Locked | Evaluation adjustment/waiver rules. |
| ITT-032 | 32 | Correction of Arithmetical Errors | 28-29 | Locked | Price schedule arithmetic correction rule. |
| ITT-033 | 33 | Conversion to Single Currency | 29 | Locked + TDS option | TDS controls exchange/currency basis if multiple currencies are allowed. |
| ITT-034 | 34 | Margin of Preference and Reservations | 29 | Locked + controlled option | TDS/evaluation schema controls whether applied. |
| ITT-035 | 35 | Evaluation of Tenders | 29-30 | Locked | Evaluation engine must follow generated criteria. |
| ITT-036 | 36 | Comparison of Tenders | 30 | Locked | Financial comparison and ranking. |
| ITT-037 | 37 | Abnormally Low Tenders and Abnormally High Tenders | 31 | Locked | Estimate-linked warning/review workflow. |
| ITT-038 | 38 | Unbalanced or Front-Loaded Tenders | 31 | Locked | Evaluation risk review workflow. |
| ITT-039 | 39 | Eligibility and Qualification of the Tenderer | 31-32 | Locked | Qualification/post-qualification schema. |
| ITT-040 | 40 | Procuring Entity's Right to Accept Any Tender, and to Reject Any or All Tenders | 32 | Locked | Award decision workflow guardrail. |
| ITT-041 | 41 | Standstill Period | 33 | Locked + parameter where allowed | Notice and award workflow must observe standstill. |
| ITT-042 | 42 | Notice of Intention to Award | 33 | Locked | Generated notification content and audit event. |
| ITT-043 | 43 | Award Criteria | 32 | Locked | Lowest/best evaluated tender method must match TDS/evaluation configuration. |
| ITT-044 | 44 | Procuring Entity's Right to Vary Quantities at Time of Award | 32 | Locked + parameter | If used, variation limits and affected price schedules must be explicit. |
| ITT-045 | 45 | Notification of Award / Letter of Award | 33 | Locked | Generated letter of award. |
| ITT-046 | 46 | Debriefing by the Procuring Entity | 33 | Locked | Debriefing request/response workflow. |
| ITT-047 | 47 | Signing of Contract | 33 | Locked | Post-standstill contract formation. |
| ITT-048 | 48 | Performance Security | 33-34 | Locked + parameter | TDS/SCC controls amount/form/deadline. |
| ITT-049 | 49 | Publication of Procurement Contract | 34 | Locked | Post-signature publication event. |
| ITT-050 | 50 | Adjudicator | 34 | Locked + TDS/SCC parameter | TDS/SCC controls nominated adjudicator and fees. |
| ITT-051 | 51 | Procurement Related Complaints and Administrative Review | 34 | Locked | Complaint instructions tied to TDS and review form. |

## 6. Locked GCC clause register

The following register identifies the locked General Conditions of Contract clauses. SCC values and contract appendices may supplement these clauses, but ordinary users must not edit the GCC text itself.

| Internal ID | Source visible no. | Clause title | Source page anchor | Treatment | Configuration / engine note |
| --- | --- | --- | --- | --- | --- |
| GCC-001 | 1 | Definitions | 105-108 | Locked | Foundational contract definitions, including System, Services, Software, Custom Materials, IPR. |
| GCC-002 | 2 | Contract Documents | 108 | Locked | Document precedence/order controlled by contract agreement. |
| GCC-003 | 3 | Interpretation | 108-109 | Locked | Governing language, singular/plural, headings, persons, incoterms, entire agreement, amendment. |
| GCC-004 | 4 | Notices | 109 | Locked + SCC parameter | SCC provides addresses and notice method details. |
| GCC-005 | 5 | Governing Law | 110 | Locked + SCC parameter | SCC specifies governing law if required. |
| GCC-006 | 6 | Fraud and Corruption | 110 | Locked | Contract-level anti-corruption obligations. |
| GCC-007 | 7 | Scope of the System | 110-111 | Locked | Contract scope from requirements, tender, and appendices. |
| GCC-008 | 8 | Time for Commencement and Operational Acceptance | 111 | Locked + SCC/implementation schedule | Dates/milestones derived from schedule and SCC. |
| GCC-009 | 9 | Supplier's Responsibilities | 111-112 | Locked | Supplier obligation baseline. |
| GCC-010 | 10 | Procuring Entity's Responsibilities | 112-113 | Locked | PE obligation baseline. |
| GCC-011 | 11 | Contract Price | 113 | Locked | Price basis from contract agreement and revised schedules. |
| GCC-012 | 12 | Terms of Payment | 113 | Locked + SCC/payment schedule | Payment milestones and conditions from SCC/contract. |
| GCC-013 | 13 | Securities | 113-114 | Locked + SCC/form parameter | Performance/advance securities. |
| GCC-014 | 14 | Taxes and Duties | 114 | Locked | Tax responsibility terms. |
| GCC-015 | 15 | Copyright | 114-115 | Locked | Copyright allocation baseline. |
| GCC-016 | 16 | Software License Agreements | 115 | Locked + appendix data | Software license categories and terms. |
| GCC-017 | 17 | Confidential Information | 116 | Locked | Confidentiality obligations. |
| GCC-018 | 18 | Representatives | 116 | Locked + appendix data | Project manager/supplier representative details. |
| GCC-019 | 19 | Project Plan | 117 | Locked + deliverable | Agreed Project Plan approval workflow. |
| GCC-020 | 20 | Subcontracting | 118 | Locked + appendix data | Approved subcontractors appendix. |
| GCC-021 | 21 | Design and Engineering | 119 | Locked | Design/specification obligations. |
| GCC-022 | 22 | Procurement, Delivery, and Transport | 120 | Locked | Delivery and transport obligations. |
| GCC-023 | 23 | Product Upgrades | 121 | Locked | Upgrade obligations. |
| GCC-024 | 24 | Implementation, Installation, and Other Services | 122 | Locked | Implementation services obligations. |
| GCC-025 | 25 | Inspections and Tests | 122 | Locked | Inspection/test obligations. |
| GCC-026 | 26 | Installation of the System | 122-123 | Locked | Installation readiness and procedure. |
| GCC-027 | 27 | Commissioning and Operational Acceptance | 123-124 | Locked | Commissioning, acceptance certificates. |
| GCC-028 | 28 | Operational Acceptance Time Guarantee | 124 | Locked + SCC parameter | Delay damages/time guarantee. |
| GCC-029 | 29 | Defect Liability | 125-126 | Locked + SCC parameter | Warranty/defect liability period and obligations. |
| GCC-030 | 30 | Functional Guarantees | 126-127 | Locked + technical requirements | Functional guarantee tests and remedies. |
| GCC-031 | 31 | Intellectual Property Rights Warranty | 127 | Locked | IP warranty. |
| GCC-032 | 32 | Intellectual Property Rights Indemnity | 127-128 | Locked | IP indemnity. |
| GCC-033 | 33 | Limitation of Liability | 128 | Locked + SCC parameter | Liability cap/exclusions if specified. |
| GCC-034 | 34 | Transfer of Ownership | 128-129 | Locked | Ownership transfer of goods/materials/custom materials. |
| GCC-035 | 35 | Care of the System | 129 | Locked | Risk/care obligations. |
| GCC-036 | 36 | Loss of or Damage to Property; Accident or Injury to Workers; Indemnification | 129-130 | Locked | Risk and indemnification. |
| GCC-037 | 37 | Insurances | 130-131 | Locked + SCC parameter | Insurance requirements. |
| GCC-038 | 38 | Force Majeure | 131-132 | Locked | Force majeure procedure and effect. |
| GCC-039 | 39 | Changes to the System | 132-134 | Locked | Change-order governance. |
| GCC-040 | 40 | Extension of Time for Achieving Operational Acceptance | 134-135 | Locked | EOT procedure. |
| GCC-041 | 41 | Termination | 135-138 | Locked | Termination by PE/Supplier; consequences. |
| GCC-042 | 42 | Assignment | 138 | Locked | Assignment limitations. |
| GCC-043 | 43 | Settlement of Disputes | 138-139 | Locked + SCC parameter | Adjudication/arbitration process and rules. |

## 7. Controlled configuration sections requiring Pass 2 extraction

| Section | Source pages | Pass 2 output | Primary data objects |
| --- | --- | --- | --- |
| Tender Data Sheet | 35-40 | Parameter dictionary, allowed values, dependencies, TDS render map | `std_parameter`, `std_parameter_option`, `std_rule`, `render_block`. |
| Evaluation and Qualification Criteria | 41-48 | Responsiveness criteria, scoring/qualification schema, post-qualification criteria, personnel schema | `evaluation_schema`, `criterion`, `criterion_option`, `score_band`, `evidence_requirement`. |
| Tendering Forms | 49-85 | Form catalog and field-level schemas | `form_schema`, `form_field`, `evidence_requirement`, `price_schedule_schema`, `ip_material_schema`. |
| Requirements of the Information System | 86-103 | IT requirements composer schema, implementation schedule schema, inventory table schema | `requirement_schema`, `requirement_item`, `implementation_milestone`, `system_inventory_item`. |
| Special Conditions of Contract | 140-149 | SCC parameter dictionary and GCC-reference mapping | `contract_parameter`, `scc_clause_mapping`, `std_rule`. |
| Contract Forms | 150-181 | Post-award generated form schemas and appendices | `contract_form_schema`, `contract_appendix_schema`, `security_form_schema`, `change_order_schema`. |

## 8. Source anomalies and review flags

| Flag ID | Issue | Observation | Required handling |
| --- | --- | --- | --- |
| E-001 | Section numbering discrepancy | TOC refers to Part 3 as Section X/XI/XII in one place but the body uses Section VI GCC, Section VII SCC, and Section XIII Contract Forms. | Preserve source labels; assign engine-normalized section IDs; require legal/procurement review before activation. |
| E-002 | ITT visible numbering irregularities | The extracted body around award/publication/adjudicator/complaints contains numbering irregularities/reuse after clause 48. | Do not renumber the rendered legal text without approval; assign stable internal IDs ITT-049 to ITT-051 while preserving source-visible labels in render text. |
| E-003 | Text extraction artifacts | The source uses ligatures and some text extraction artifacts, e.g. Deﬁnitions, Qualiﬁcation, and occasional spacing errors. | Canonical clause text extraction must normalize only for storage/search while preserving source-visible legal text hash separately. |
| E-004 | NSSF tender as calibration only | The NSSF ERP tender compresses and customizes the IT STD for a real ERP procurement. | Use it as a fixture for wizard and validation tests, not as the master STD source. |

## 9. Recommended source anchor schema

Use the following schema for the next extraction/import step. This should be represented in JSON and database records.

```json
{
  "source_anchor_id": "SRC-KE-PPRA-IT-2022-04-ITT-001",
  "template_family_code": "KE-PPRA-IT",
  "template_version_code": "KE-PPRA-IT-2022-04",
  "source_document_id": "DOC-10-IT-STD-2022-04",
  "source_section_id": "IT-STD-ITT",
  "source_visible_label": "1. Scope of Tender",
  "engine_object_type": "STD_CLAUSE",
  "engine_object_code": "ITT-001",
  "page_start": 15,
  "page_end": 15,
  "paragraph_start_hint": "1.1",
  "paragraph_end_hint": "before 2. Definitions",
  "extraction_status": "BOUNDARY_IDENTIFIED",
  "canonical_text_hash": null,
  "source_visible_text_hash": null,
  "review_required": true
}
```

## 10. Seed package updates implied by Pass 1

| Package module | Required update |
| --- | --- |
| `source_trace/source_documents.json` | Add official DOC source metadata, rendered derivative metadata, source hash, extraction timestamp, and review status. |
| `sections/sections.json` | Populate the section records listed in the section/source anchor map. |
| `sections/mutability.json` | Apply locked/configured/generated mutability classifications from this pass. |
| `clauses/itt_clauses.json` | Create 51 ITT clause boundary records using the ITT register. |
| `clauses/gcc_clauses.json` | Create 43 GCC clause boundary records using the GCC register. |
| `source_trace/source_anchors.json` | Create source anchor placeholders for every section and locked clause. |
| `review_flags/extraction_flags.json` | Create review flags for section-numbering and ITT-numbering anomalies. |
| `smoke_tests/source_trace_smoke_tests.json` | Add tests to ensure every locked clause has a source anchor and review status. |

## 11. Pass 1 acceptance checks

| Check | Expected result |
| --- | --- |
| Every major source section is represented | Pass when all official IT STD parts/sections appear in `sections.json`. |
| ITT clauses have stable internal IDs | Pass when all ITT locked clause records exist even where visible numbering requires review. |
| GCC clauses have stable internal IDs | Pass when GCC-001 through GCC-043 exist and are locked. |
| No active use allowed | Package remains `DRAFT` or `STRUCTURING`; activation blocked until Pass 2/3 review is complete. |
| Anomalies are not hidden | All detected numbering/section issues are stored as review flags. |
| TDS/SCC are not free-text overrides | Configuration must route through controlled parameter schemas. |

## 12. Next extraction pass

The next artifact should be:

**IT STD Full Source Extraction Pass 2 - TDS, SCC, Parameter Dictionary, and Rule Dictionary**

That pass should populate the first real machine-usable configuration objects: TDS parameters, SCC parameters, activation rules, validation rules, allowed options, dependencies, and render bindings. Clause full-text canonicalization should proceed in parallel or as Pass 2A if we want to keep the parameter pass smaller.

## 13. Non-negotiable implementation rule

Do not build the IT tender wizard until this extraction work has produced reviewed parameter, rule, form, requirement, and render dictionaries. Otherwise the UI will encode assumptions before the legal/configuration model is stable.