# STD for Procurement of Information Technology - Full Source Extraction Pass 2

**Package:** `KE-PPRA-IT-2022-04`  
**Target engine:** Generalized STD Engine Core  
**Artifact status:** Draft extraction register - not activatable  
**Generated:** 2026-07-07 20:22 UTC  
**Pass focus:** Tender Data Sheet, Special Conditions of Contract, parameter dictionary, and rule dictionary

---

## 1. Purpose

This document is Pass 2 of the full source extraction for the official PPRA Standard Tender Document for Procurement of Information Technology. Pass 1 established the source evidence, section anchors, mutability classifications, and locked ITT/GCC clause registers. This pass converts the two main controlled-configuration surfaces into implementation-ready extraction registers:

1. **Tender Data Sheet (TDS)** - the tender-specific supplement to the locked Instructions to Tenderers.
2. **Special Conditions of Contract (SCC)** - the contract-specific supplement to the locked General Conditions of Contract.

The goal is not to rewrite the STD. The goal is to define the controlled parameters, allowed values, dependencies, validation rules, render locations, and governance controls that allow the STD Engine to generate compliant tender documents without allowing ordinary users to alter locked legal text.

The approach is generalized. The same model must support WORKS, GOODS, SERVICES, CONSULTANCY, IT, and future PPRA STD families. IT-specific parameters are modeled as a package profile under the generalized `std_parameter`, `std_rule`, `render_block`, and `source_anchor` abstractions.

---

## 2. Source basis

| Source | Role in this pass | Handling |
| --- | --- | --- |
| Official PPRA IT STD, DOC 10 | Legal master source | Used for the TDS and SCC parameter surfaces. |
| Rendered PDF derivative | Page-anchor support | Used only for page-based extraction anchors. |
| Layout text derivative | Extraction support | Used only for clause/parameter boundary identification. |
| NSSF SPS ERP tender | Calibration fixture | Used to validate whether the extracted TDS/SCC model can represent a real ERP tender. It is not the master STD. |

### 2.1 Source anchor scope

| Source section | Rendered source page anchor | Engine section ID | Mutability | Extraction result |
| --- | ---: | --- | --- | --- |
| Section II - Tender Data Sheet | 35-40 | `IT-STD-TDS` | `CONTROLLED_CONFIG` | TDS parameter dictionary and tender-stage rules. |
| Section VII - Special Conditions of Contract | 140-149 | `IT-STD-SCC` | `CONTROLLED_CONFIG` | SCC parameter dictionary and contract-stage rules. |

### 2.2 Important source-note

The TDS table label uses **"Reference to ITC Clause"** in places while the underlying document and engine model refer to **ITT**. The engine must preserve the visible source label where rendered, but internally normalize the reference field as `itt_reference`. This must remain a review flag until legal/procurement reviewers approve how the rendered output should display the label.

---

## 3. Configuration principle

The IT STD states that ITT and GCC text are not to be changed directly. The configuration surfaces are therefore:

| Locked source | Allowed configuration surface | Engine behavior |
| --- | --- | --- |
| Section I - Instructions to Tenderers | Section II - Tender Data Sheet | Users complete controlled TDS fields. Locked ITT clauses render unchanged. |
| Section VI - General Conditions of Contract | Section VII - Special Conditions of Contract | Users complete controlled SCC fields. Locked GCC clauses render unchanged. |
| Section III - Evaluation and Qualification Criteria | Controlled evaluation schema | Users may select or complete allowed criteria only where the STD permits. |
| Section IV - Tendering Forms | Structured form schemas | Users may activate/configure forms only through schema-bound fields. |
| Part 2 - Procuring Entity's Requirements | Controlled authoring composer | Users author requirements using structured requirement, schedule, inventory, and background models. |

The engine must reject any attempt to add arbitrary TDS/SCC rows, arbitrary evaluation criteria, or direct edits to locked clauses unless the active STD version is superseded through template governance.

---

## 4. TDS parameter dictionary

### 4.1 TDS parameter object standard

Each TDS parameter should be stored using the following generalized structure:

```json
{
  "parameter_code": "IT-TDS-001",
  "template_family_code": "KE-PPRA-IT",
  "template_version_code": "KE-PPRA-IT-2022-04",
  "section_id": "IT-STD-TDS",
  "source_reference": "ITT 1.1",
  "source_visible_label": "ITT 1.1",
  "normalized_reference": "ITT-001",
  "display_label": "Reference number of the Request for Tenders",
  "data_type": "text",
  "required_stage": "TENDER_CONFIGURATION",
  "required": true,
  "allowed_values": null,
  "default_value": null,
  "render_block_code": "R-TDS-A-GENERAL",
  "source_anchor_id": "SRC-KE-PPRA-IT-2022-04-TDS-ITT-1-1",
  "legal_review_required": false
}
```

The same table structure can be reused by all STD families. The `template_family_code`, `section_id`, source reference, and renderer decide the specific document behavior.

### 4.2 TDS parameter register

| Code | Source ref. | Parameter | Type | Required | Allowed / validation | Engine handling |
| --- | --- | --- | --- | --- | --- | --- |
| IT-TDS-001 | ITT 1.1 | Request for Tenders reference number | Text | Yes | Non-empty; unique within PE/tender year where applicable | Render into TDS and issued document identity. |
| IT-TDS-002 | ITT 1.1 | Procuring Entity legal name | Entity reference / text | Yes | Must match registered PE profile unless override approved | Used across invitation, TDS, SCC, forms, and contract. |
| IT-TDS-003 | ITT 1.1 | Name of ITT / tender name | Text | Yes | Non-empty; should match procurement plan/tender creation record | Used in cover, invitation, TDS, forms, contract. |
| IT-TDS-004 | ITT 1.1 | Number and identification of lots/contracts | Structured list | Conditional | Required if lots/subsystems/slices enabled | Drives lot pricing, evaluation, award and contract generation. |
| IT-TDS-005 | ITT 2.3(a) | E-procurement system enabled | Boolean | Yes | `true` or `false` | Activates e-procurement fields and electronic submission/opening rules. |
| IT-TDS-006 | ITT 2.3(a) | E-procurement system name | Text | Conditional | Required if e-procurement enabled | Rendered in TDS. |
| IT-TDS-007 | ITT 2.3(a) | E-procurement URL/link | URL | Conditional | Required if e-procurement enabled | Rendered in TDS and bidder instructions. |
| IT-TDS-008 | ITT 2.3(a) | E-procurement process aspects | Multi-select | Conditional | Examples: issue tender, submission, opening, clarification, addenda | Must align with submission/opening electronic procedure fields. |
| IT-TDS-009 | ITT 3.3 | Firms that provided consulting services | Structured list | Conditional | Required if any firm provided design/specification/project preparation services | Feeds conflict-of-interest checks and unfair advantage disclosures. |
| IT-TDS-010 | ITT 4.1 | Maximum number of JV members | Integer | Yes | Recommended practical range: 1-5; warn above 5 | Used in eligibility validation. |
| IT-TDS-011 | ITT 4.9 | Additional registration requirement | Text / controlled register | Optional | Must specify registration authority and evidence | Generates eligibility evidence requirement if completed. |
| IT-TDS-012 | ITT 8.1 | Clarification contact attention | Text | Yes | Person or role | Renders in TDS and clarification instructions. |
| IT-TDS-013 | ITT 8.1 | Clarification street address | Address | Yes | Address fields | Renders in TDS. |
| IT-TDS-014 | ITT 8.1 | Clarification floor/room | Text | Optional | Free text | Renders in TDS. |
| IT-TDS-015 | ITT 8.1 | Clarification city | Text | Yes | Non-empty | Renders in TDS. |
| IT-TDS-016 | ITT 8.1 | Clarification ZIP/postal code | Text | Optional | Free text | Renders in TDS. |
| IT-TDS-017 | ITT 8.1 | Clarification country | Country | Yes | ISO/country list | Renders in TDS. |
| IT-TDS-018 | ITT 8.1 | Clarification telephone | Phone | Optional | Phone format | Renders if provided. |
| IT-TDS-019 | ITT 8.1 | Clarification fax | Phone | Optional | Phone format | Renders if provided. |
| IT-TDS-020 | ITT 8.1 | Clarification email | Email | Yes | Valid email | Renders in TDS; used for notices. |
| IT-TDS-021 | ITT 8.1 | Clarification request deadline offset | Duration / date | Yes | Either absolute date or days before submission | Must precede submission deadline. |
| IT-TDS-022 | ITT 8.2 | Procurement publication web page | URL | Conditional | Required where tender information is published electronically | Used for clarification/addenda publishing. |
| IT-TDS-023 | ITT 8.4 | Pre-tender meeting will take place | Boolean | Yes | `shall` / `shall not` normalized to boolean | If true, date/time/place required. |
| IT-TDS-024 | ITT 8.4 | Pre-tender meeting date | Date | Conditional | Required if pre-tender meeting enabled | Must be before clarification deadline/submission deadline. |
| IT-TDS-025 | ITT 8.4 | Pre-tender meeting time | Time | Conditional | Required if pre-tender meeting enabled | Renders in TDS. |
| IT-TDS-026 | ITT 8.4 | Pre-tender meeting place | Location | Conditional | Required if pre-tender meeting enabled | Renders in TDS. |
| IT-TDS-027 | ITT 8.4 | Procuring Entity-organized site visit | Boolean | Yes | `shall be` / `shall not be` normalized to boolean | If true, site visit details must be captured. |
| IT-TDS-028 | ITT 8.4 | Site visit details | Structured location/date/time | Conditional | Required if site visit enabled | Rendered in TDS and bidder instructions. |
| IT-TDS-029 | ITT 9.1 | Website where clarification response is published | URL | Conditional | Required if responses published online | Must be consistent with publication web page/e-procurement settings. |
| IT-TDS-030 | ITT 13.1(k) | Additional documents required with tender | Structured list | Optional | Each item must have title, respondent, evidence type, mandatory flag | Generates supplier submission checklist and evidence requirements. |
| IT-TDS-031 | ITT 15.1 | Alternative tenders status | Enum | Yes | `INVITED`, `PERMITTED`, `NOT_PERMITTED` | Controls alternative tender submission and evaluation paths. |
| IT-TDS-032 | ITT 15.2 | Alternatives to time schedule permitted | Boolean | Conditional | Should not be true unless alternative tenders are invited/permitted | Requires evaluation method in Section III. |
| IT-TDS-033 | ITT 15.4 | Alternative technical solutions permitted | Boolean | Conditional | Should not be true unless alternative tenders are invited/permitted | Requires specified parts and evaluation method. |
| IT-TDS-034 | ITT 15.4 | Parts permitting alternative technical solutions | Structured list | Conditional | Required if technical alternatives are permitted | Must reference Technical Requirements items/subsystems. |
| IT-TDS-035 | ITT 17.2 | Prequalification undertaken | Boolean | Yes | `has` / `has not` normalized to boolean | Activates prequalification consistency checks. |
| IT-TDS-036 | ITT 18.2(a) | Preliminary Project Plan topics | Multi-select / structured list | Yes | Default topics plus approved additions | Drives supplier technical proposal checklist. |
| IT-TDS-037 | ITT 18.3 | Mandatory brand/model limited items | Structured list | Optional | Use only where justifiable; item + technical reference required | Legal/procurement review recommended; anti-restrictive risk flag. |
| IT-TDS-038 | ITT 19.2 | Tenderer must tender recurrent cost items | Boolean | Yes | `must` / `must not` | Activates recurrent cost tables and post-warranty service configuration. |
| IT-TDS-039 | ITT 19.2(a) | Tenderer must tender separate recurrent cost contracts not in main contract | Boolean | Conditional | Required if recurrent cost items exist | Drives recurrent-cost tendering model. |
| IT-TDS-040 | ITT 19.5 | Incoterms edition | Text / controlled list | Conditional | Required for goods/import components | Use current approved edition list if platform maintains one. |
| IT-TDS-041 | ITT 19.5(a) | Named place of destination | Location | Conditional | Required if goods supplied from outside Kenya or Incoterms used | Must align with project sites. |
| IT-TDS-042 | ITT 19.6 | Named final destination / project site | Location | Yes | Must match PE requirements/project site | Used in logistics, risk, installation, contract. |
| IT-TDS-043 | ITT 19.8 | Modification to ITT 17.8 service pricing | Text / controlled clause | Optional | If blank, render no modification statement | Legal/procurement review required if modified. |
| IT-TDS-044 | ITT 19.9 | Tender prices subject to adjustment | Boolean | Yes | `shall` / `shall not` normalized to boolean | If true, adjustment factors required. |
| IT-TDS-045 | ITT 19.9 | Local currency price adjustment factor | Formula / text | Conditional | Required if price adjustment enabled and local currency component exists | Must pass formula review. |
| IT-TDS-046 | ITT 19.9 | Foreign currency price adjustment factor | Formula / text | Conditional | Required if price adjustment enabled and foreign currency component exists | Must pass formula review. |
| IT-TDS-047 | ITT 20.1 | Tenderer required to quote Kenya-currency portion | Boolean | Yes | `is` / `is not` | Tied to currency/payment setup. |
| IT-TDS-048 | ITT 21.1 | Tender validity period in days | Integer | Yes | Positive integer | Must align with invitation and forms. |
| IT-TDS-049 | ITT 22.1 | Tender Security required | Boolean | Yes | Mutually exclusive with Tender-Securing Declaration unless legal basis says otherwise | Activates security form/evidence. |
| IT-TDS-050 | ITT 22.1 | Tender-Securing Declaration required | Boolean | Yes | Mutually exclusive with Tender Security | Activates declaration form. |
| IT-TDS-051 | ITT 22.1 | Tender Security amount and currency | Money | Conditional | Required if Tender Security required | Amount should not exceed permitted statutory/STD threshold. |
| IT-TDS-052 | ITT 22.3(v) | Other acceptable securities | Structured list | Optional | Must be allowed under procurement rules | Controls evidence validation. |
| IT-TDS-053 | ITT 23.1 | Number of tender copies | Integer | Yes | Integer >= 0 | Renders in TDS and submission instructions. |
| IT-TDS-054 | ITT 23.3 | Documentation proving signatory authority | Text / evidence list | Yes | Examples: board resolution, power of attorney, authorization letter | Generates supplier checklist. |
| IT-TDS-055 | ITT 25.1 | Tender submission attention/contact | Text | Yes | Person/role | Renders in submission address. |
| IT-TDS-056 | ITT 25.1 | Tender submission street address | Address | Yes | Non-empty | Renders in TDS. |
| IT-TDS-057 | ITT 25.1 | Tender submission floor/room | Text | Optional | Free text | Renders if provided. |
| IT-TDS-058 | ITT 25.1 | Tender submission city | Text | Yes | Non-empty | Renders in TDS. |
| IT-TDS-059 | ITT 25.1 | Tender submission country | Country | Yes | Country list | Renders in TDS. |
| IT-TDS-060 | ITT 25.1 | Tender submission deadline date | Date | Yes | Must be after publication date and clarification deadline | Drives publication countdown and late tender validation. |
| IT-TDS-061 | ITT 25.1 | Tender submission deadline time | Time | Yes | Valid local time | Used with deadline date. |
| IT-TDS-062 | ITT 25.1 | Electronic tender submission allowed | Boolean | Yes | `shall` / `shall not` | Requires e-submission procedures if true. |
| IT-TDS-063 | ITT 25.1 | Electronic tender submission procedures | Long text | Conditional | Required if electronic submission allowed | Rendered in TDS. |
| IT-TDS-064 | ITT 28.1 | Tender opening street address | Address | Yes | Non-empty | May equal submission address. |
| IT-TDS-065 | ITT 28.1 | Tender opening floor/room | Text | Optional | Free text | Renders if provided. |
| IT-TDS-066 | ITT 28.1 | Tender opening city | Text | Yes | Non-empty | Renders in TDS. |
| IT-TDS-067 | ITT 28.1 | Tender opening country | Country | Yes | Country list | Renders in TDS. |
| IT-TDS-068 | ITT 28.1 | Tender opening date | Date | Yes | Must be same as or after submission deadline date | Usually immediately after deadline. |
| IT-TDS-069 | ITT 28.1 | Tender opening time | Time | Yes | Must be same as or after submission deadline time if same date | Renders in TDS. |
| IT-TDS-070 | ITT 28.1 | Electronic tender opening procedures | Long text | Conditional | Required if electronic tendering/opening enabled | Renders in TDS. |
| IT-TDS-071 | ITT 28.6 | Number of PE representatives initialing Form of Tender and Price Schedules | Integer | Yes | Integer >= 1 | Renders in tender opening instructions. |
| IT-TDS-072 | ITT 33.3 | Missing item adjustment basis | Enum | Yes | `AVERAGE_PRICE`, `HIGHEST_PRICE`, `BEST_ESTIMATE` fallback | Drives financial evaluation adjustment logic. |
| IT-TDS-073 | ITT 35.1 | Single evaluation currency | Currency | Conditional | Required if multiple tender currencies allowed | Used in price conversion. |
| IT-TDS-074 | ITT 35.1 | Currency used for comparison | Currency | Conditional | Required if currency conversion applies | Usually KES for local evaluation. |
| IT-TDS-075 | ITT 35.1 | Source of exchange rate | Text / controlled source | Conditional | Required if currency conversion applies | Example source may be Central Bank of Kenya. |
| IT-TDS-076 | ITT 35.1 | Exchange rate date/time | DateTime | Conditional | Required if currency conversion applies | Must be specified before tender opening/evaluation. |
| IT-TDS-077 | ITT 36.2 | Margin of preference applies | Boolean | Yes | Applies / does not apply | Must be consistent with tender method and legal threshold. |
| IT-TDS-078 | ITT 36.4 | Reservation group | Enum / structured | Conditional | SME, women, youth, persons with disability, or other allowed group | No more than one reservation group unless law/STD permits. |
| IT-TDS-079 | ITT 40.2(b) | Tenderers may quote separate prices for lots/subsystems/slices | Boolean | Conditional | Required if lots/subsystems/slices exist | Drives lot evaluation and award logic. |
| IT-TDS-080 | ITT 40.2(b) | Conditional multi-lot discounts considered | Boolean | Conditional | Required if lot pricing enabled | For rated criteria, default warning: do not consider to avoid complexity. |
| IT-TDS-081 | ITT 44.3 | Additional post-qualification tests/performance benchmarks | Structured list | Optional | Each test requires method, success criteria, responsible party, stage | Drives demonstration/reference site/performance testing. |
| IT-TDS-082 | ITT 46.1 | Award basis uses rated criteria | Enum | Yes | `RATED`, `NOT_RATED` | Must align with Section III evaluation schema. |
| IT-TDS-083 | ITT 47.1 | Maximum quantity increase percentage | Percentage | Optional | Recommended warning above 20% for hardware/software components | Controls award variation rule. |
| IT-TDS-084 | ITT 47.1 | Maximum quantity decrease percentage | Percentage | Optional | Recommended warning above 20% for hardware/software components | Controls award variation rule. |
| IT-TDS-085 | ITT 47.1 | Items subject to quantity increase/decrease | Structured list | Conditional | Required if variation percentages set | Must reference system inventory/price schedule items. |
| IT-TDS-086 | ITT 50.1 | Proposed adjudicator | Person / text | Optional | Name and identifying information or explicit no-adjudicator statement | If no adjudicator, legal review recommended for complex IT procurements. |
| IT-TDS-087 | ITT 50.1 | Proposed adjudicator hourly fee | Money | Conditional | Required if adjudicator proposed | Used in contract agreement appendix. |
| IT-TDS-088 | ITT 51.1 | Procurement complaint recipient attention | Text | Yes | Person/role | Renders in complaint procedure. |
| IT-TDS-089 | ITT 51.1 | Complaint recipient title/position | Text | Yes | Non-empty | Renders in complaint procedure. |
| IT-TDS-090 | ITT 51.1 | Complaint recipient procuring entity | Entity/text | Yes | Usually same PE | Renders in complaint procedure. |
| IT-TDS-091 | ITT 51.1 | Complaint recipient email address | Email | Yes | Valid email | Renders in complaint procedure. |

---

## 5. SCC parameter dictionary

### 5.1 SCC parameter object standard

Each SCC parameter should use the same generalized parameter structure, with an SCC-specific reference to the affected GCC clause:

```json
{
  "parameter_code": "IT-SCC-001",
  "template_family_code": "KE-PPRA-IT",
  "template_version_code": "KE-PPRA-IT-2022-04",
  "section_id": "IT-STD-SCC",
  "source_reference": "GCC 1.1(b)(i)",
  "normalized_reference": "GCC-001",
  "display_label": "Procuring Entity legal name",
  "data_type": "entity_reference",
  "required_stage": "CONTRACT_CONFIGURATION",
  "required": true,
  "render_block_code": "R-SCC-A-CONTRACT-INTERPRETATION",
  "source_anchor_id": "SRC-KE-PPRA-IT-2022-04-SCC-GCC-1-1-B-I",
  "legal_review_required": false
}
```

### 5.2 SCC parameter register

| Code | GCC ref. | Parameter | Type | Required | Allowed / validation | Engine handling |
| --- | --- | --- | --- | --- | --- | --- |
| IT-SCC-001 | GCC 1.1(b)(i) | Procuring Entity legal name | Entity reference / text | Yes | Must match tender PE unless legal override approved | Render into SCC and contract agreement. |
| IT-SCC-002 | GCC 1.1(b)(ii) | Project Manager name/title | Person / text | Yes | Must identify role or named officer | Used for notices, approvals, project governance. |
| IT-SCC-003 | GCC 1.1(e)(ix)/(x) | Fixed contract period end date | Date / text | Optional | Use only if hard calendar end is required | Review flag because source numbering appears inconsistent. |
| IT-SCC-004 | GCC 1.1(e)(xii) | Post-Warranty Services Period | Duration months | Conditional | Required if recurrent/post-warranty services are included | Drives recurrent cost tables and contract duration. |
| IT-SCC-005 | GCC 4.3 | Project Manager notice address | Address/contact | Yes | Postal, physical, email, EDI where used | Used in contract notices. |
| IT-SCC-006 | GCC 4.3 | Procuring Entity fallback notice address | Address/contact | Yes | Postal, physical, email, EDI where used | Used if Project Manager notice route fails or is not applicable. |
| IT-SCC-007 | GCC 4.3 | EDI standards/protocols/addresses/procedures | Structured technical text | Conditional | Required if EDI notices are used | Must align with e-procurement/e-notice capability. |
| IT-SCC-008 | GCC 7.3 | Recurrent cost items included in contract | Structured list | Conditional | Required if recurrent costs included | Must cross-reference recurrent cost table and technical requirements. |
| IT-SCC-009 | GCC 7.3 | Spare parts supply obligation period | Duration years | Optional | Required only if spare parts obligation is imposed | Usually low priority for modern IT but valid for hardware-heavy systems. |
| IT-SCC-010 | GCC 7.3 | Spare parts list / reference | Structured list | Conditional | Required if spare parts obligation period set | May reference spare parts price schedule. |
| IT-SCC-011 | GCC 8.1 | Commencement period after effective date | Integer days | Yes | Positive integer | Drives contract implementation schedule. |
| IT-SCC-012 | GCC 11.2 | Contract price adjustment applicability | Enum | Yes | `NOT_APPLICABLE` or `APPLICABLE` | If applicable, formula/index fields required. |
| IT-SCC-013 | GCC 11.2 | Contract price adjustment formula/index | Formula / structured text | Conditional | Required if price adjustment applies | Legal/procurement/finance review required. |
| IT-SCC-014 | GCC 12.1 | Payment schedule category model | Structured schedule | Yes | Must allocate payment by allowed payment categories/milestones | Feeds contract, invoice, acceptance, and payment module. |
| IT-SCC-015 | GCC 12.1(a) | Advance payment percentage | Percentage | Optional | Default source example: 20% excluding recurrent costs | If > 0, advance payment security required. |
| IT-SCC-016 | GCC 12.1(b) | Goods/materials delivery payment percentage | Percentage | Conditional | Source example: 60% against delivery | Applies to Information Technologies, Materials, and other Goods except custom software/materials. |
| IT-SCC-017 | GCC 12.1(b) | Goods/materials installation payment percentage | Percentage | Conditional | Source example: 10% against installation | Requires installation milestone. |
| IT-SCC-018 | GCC 12.1(b) | Goods/materials operational acceptance payment percentage | Percentage | Conditional | Source example: 10% against operational acceptance | Requires acceptance certificate. |
| IT-SCC-019 | GCC 12.1(c) | Custom software/materials installation payment percentage | Percentage | Conditional | Source example: 60% against installation | For custom software and custom materials. |
| IT-SCC-020 | GCC 12.1(c) | Custom software/materials operational acceptance payment percentage | Percentage | Conditional | Source example: 20% against operational acceptance | Requires acceptance certificate. |
| IT-SCC-021 | GCC 12.1(d) | Services other than training payment percentage | Percentage | Conditional | Source example: 80% monthly in arrears | Can be milestone-based for data conversion/migration/digitization. |
| IT-SCC-022 | GCC 12.1(e) | Training start payment percentage | Percentage | Conditional | Source example: 30% at start of full training program | Requires training plan. |
| IT-SCC-023 | GCC 12.1(e) | Training performed payment percentage | Percentage | Conditional | Source example: 50% monthly in arrears | Requires accepted invoices/training evidence. |
| IT-SCC-024 | GCC 12.1(f) | Complete system integration final payment percentage | Percentage | Conditional | Source example: 10% against operational acceptance of integrated system | Required where integrated whole-system acceptance applies. |
| IT-SCC-025 | GCC 12.1(g) | Recurrent cost payment timing | Enum / schedule | Conditional | Source example: 100% quarterly in arrears | Required if recurrent costs included. |
| IT-SCC-026 | GCC 12.3 | Interest rate for delayed payments | Percentage | Optional | Must be specified if delayed-payment interest applies | Finance/legal review. |
| IT-SCC-027 | GCC 12.4 | Exchange rate source for local payment conversion | Text / controlled source | Conditional | Required if contract/price schedule currency differs from KES for local payments | Align with TDS currency conversion source where applicable. |
| IT-SCC-028 | GCC 13.3.1 | Performance security currency | Currency | Yes | Contract currency or acceptable convertible currency | Used in performance security form. |
| IT-SCC-029 | GCC 13.3.1 | Performance security percentage | Percentage | Yes | Should be no more than 10% of contract price including warranty recurrent costs unless legally approved | Hard/warning rule depending policy. |
| IT-SCC-030 | GCC 13.3.4 | Reduced performance security percentage during warranty | Percentage | Optional | Source note indicates 1%-2.5% may be appropriate for a three-year warranty | Required if reduction is used. |
| IT-SCC-031 | GCC 15.3 | Copyright rights conveyed to successors/group entities | Text / structured rights | Optional | Usually no special condition unless needed | Legal review required if completed. |
| IT-SCC-032 | GCC 15.4 | Custom software/materials IPR allocation model | Enum / legal text | Conditional | Options should include PE ownership, supplier ownership/license, shared/commercial exploitation, hybrid | Legal drafting required; cannot be casual free text. |
| IT-SCC-033 | GCC 15.4 | Custom software exploitation restrictions | Structured legal terms | Conditional | Territory, duration, customer category, royalty, audit/reporting | Required if supplier or PE commercial exploitation rights are defined. |
| IT-SCC-034 | GCC 15.5 | Software escrow required | Boolean | Conditional | Recommended where custom/application software support continuity risk exists | If true, escrow terms required. |
| IT-SCC-035 | GCC 15.5 | Escrow agent / jurisdiction / release events | Structured legal terms | Conditional | Required if escrow required | Release events, update obligation, fees, verification, confidentiality. |
| IT-SCC-036 | GCC 16.1(a)(iv) | Software usage limitations | Structured limits | Optional | Records, transactions, users, concurrent users, workstations, other limits | Must not contradict requirements; additional fees preferred over absolute blocking where growth likely. |
| IT-SCC-037 | GCC 16.1(b)(vi) | Permitted user/sublicensee entity restrictions | Structured list | Optional | May restrict direct competitors or specify permitted entities | Legal review. |
| IT-SCC-038 | GCC 16.1(b)(vii) | Business group entities bound to license terms | Structured list | Optional | Requires written adherence by listed parties | Contract appendix may be required. |
| IT-SCC-039 | GCC 16.2 | Software audit conditions | Structured terms | Optional | Duration, number/year, hours, categories, access procedure, auditors, notice, indemnity | Legal review. |
| IT-SCC-040 | GCC 17.1 | Confidentiality exemptions | Structured list | Optional | Persons/topics/conditions for which confidentiality does not apply | Legal review. |
| IT-SCC-041 | GCC 18.1 | PE Project Manager additional powers/limitations | Text / structured authority | Optional | If blank, GCC default applies | Contract administration settings. |
| IT-SCC-042 | GCC 18.2.2 | Supplier Representative additional powers/limitations | Text / structured authority | Optional | May be finalized after award | Contract appendix integration. |
| IT-SCC-043 | GCC 19.1 | Required Project Plan chapters | Multi-select / structured list | Yes | Default: project organization/management, implementation, training, testing/QA, warranty defect repair/support | Must cross-reference technical requirements. |
| IT-SCC-044 | GCC 19.6 | Required periodic reports | Multi-select / structured list | Yes | Default: monthly QA reports, training participant test results, service calls/problem resolutions | Drives contract deliverable schedule. |
| IT-SCC-045 | GCC 21.3.1 | Controlling technical documents requiring approval | Structured list | Optional | Examples: site surveys, final subsystem configurations | Blocks downstream work until approval where configured. |
| IT-SCC-046 | GCC 23.4 | Product upgrade special terms | Text / structured | Optional | If blank, no SCC modification | Defines new versions/releases/updates obligations. |
| IT-SCC-047 | GCC 25 | Inspection and test special arrangements | Structured terms | Optional | Inspectors, timing, pre-shipment inspection, responsibilities | Technical/legal review. |
| IT-SCC-048 | GCC 27.2.1 | Operational acceptance test specification reference | Structured reference | Yes | Must reference technical requirements/acceptance tests | Critical blocker before publication. |
| IT-SCC-049 | GCC 28.2 | Liquidated damages rate for delay | Percentage / period | Optional | Source note: typical 0.5% per week | Required if operational acceptance time guarantee enforced. |
| IT-SCC-050 | GCC 28.2 | Liquidated damages cap | Percentage | Conditional | Source note: typical cap 10% | Required if LD rate specified. |
| IT-SCC-051 | GCC 28.3 | Intermediate milestone LDs | Structured list | Optional | Milestone, rate, cap, affected subsystem | Use only where implementation schedule precisely defines milestones. |
| IT-SCC-052 | GCC 29.1 | Defect liability exceptions/limitations | Structured legal terms | Optional | Use only with expert/legal review | Must not undermine critical system reliability. |
| IT-SCC-053 | GCC 29.4 | Warranty period and excluded/included support services | Duration / structured list | Yes | Must distinguish commercial warranty from paid recurrent services | Drives warranty and recurrent cost model. |
| IT-SCC-054 | GCC 29.10 | Defect response times by severity/category | Structured SLA | Yes | P1/P2/P3 or equivalent severity model | Drives warranty support obligations. |
| IT-SCC-055 | GCC 30 | Functional guarantee special requirements | Structured test/requirement | Optional | Calendar system or other system guarantee variation | Must reference technical requirements. |
| IT-SCC-056 | GCC 37.1(c) | Third-party liability insurance amount | Money | Yes / Conditional by policy | Monetary value required if third-party liability insurance imposed | Used in contract compliance checklist. |
| IT-SCC-057 | GCC 37.1(c) | Third-party liability deductible limit | Money | Conditional | Required if third-party liability insurance imposed | Contract compliance. |
| IT-SCC-058 | GCC 37.1(c) | Insured parties | Structured list | Conditional | Required if third-party liability insurance imposed | Contract compliance. |
| IT-SCC-059 | GCC 37.1(c) | Insurance coverage period | Date/duration | Conditional | Required if third-party liability insurance imposed | Contract compliance. |
| IT-SCC-060 | GCC 37.1(e) | Worker compensation / employer liability insurance requirements | Structured legal terms | Optional / jurisdictional | Must comply with Kenya statutory requirements where applicable | Legal review. |
| IT-SCC-061 | GCC 39.4.3 | Supplier share of accepted value engineering savings | Percentage | Optional | Source note: normally up to 50% | Applies only when value engineering produces contract price reduction. |
| IT-SCC-062 | GCC 43.1.4 | Adjudicator appointing authority | Organization / text | Conditional | Required if adjudicator used and appointing authority needed | Contract dispute setup. |
| IT-SCC-063 | GCC 43.2.3 | Arbitration rules for foreign supplier | Enum | Conditional | UNCITRAL, ICC, Stockholm Chamber, LCIA, or approved option | Required where foreign supplier scenario applies. |
| IT-SCC-064 | GCC 43.2.3 | Arbitration basis for Kenyan supplier | Text / controlled legal reference | Yes | Disputes referred to arbitration under Kenyan law | Render in SCC. |

---

## 6. Render block map

| Render block code | Source section | Inputs | Output location | Notes |
| --- | --- | --- | --- | --- |
| R-TDS-A-GENERAL | TDS A. General | IT-TDS-001 through IT-TDS-011 | Section II TDS | Includes tender identity, PE, lots, e-procurement, consultants, JV, registration. |
| R-TDS-B-DOCUMENT | TDS B. Tendering Document | IT-TDS-012 through IT-TDS-029 | Section II TDS | Clarification, website, pre-tender meeting, site visit, clarification publication. |
| R-TDS-C-PREPARATION | TDS C. Preparation of Tenders | IT-TDS-030 through IT-TDS-054 | Section II TDS | Additional documents, alternatives, prequalification, project plan, brand/model, pricing, currencies, validity, tender security, copies, signing authority. |
| R-TDS-D-SUBMISSION | TDS D. Submission and Opening | IT-TDS-055 through IT-TDS-071 | Section II TDS | Submission and opening address/procedure/deadlines, electronic submission/opening, initialing representatives. |
| R-TDS-E-EVALUATION | TDS E. Evaluation and Comparison | IT-TDS-072 through IT-TDS-085 | Section II TDS | Missing items, currency conversion, margin, reservations, lots, post-qualification tests, award basis, quantity variation. |
| R-TDS-F-COMPLAINTS | TDS F / late TDS entries | IT-TDS-086 through IT-TDS-091 | Section II TDS | Adjudicator, complaint recipient and complaint procedure. |
| R-SCC-A-CONTRACT-INTERPRETATION | SCC A | IT-SCC-001 through IT-SCC-007 | Section VII SCC | Contract parties, project manager, notices, EDI. |
| R-SCC-B-SUBJECT-MATTER | SCC B | IT-SCC-008 through IT-SCC-011 | Section VII SCC | Recurrent costs, spare parts, commencement. |
| R-SCC-C-PAYMENT | SCC C | IT-SCC-012 through IT-SCC-030 | Section VII SCC | Price adjustment, payments, delayed interest, conversion, securities. |
| R-SCC-D-IP | SCC D | IT-SCC-031 through IT-SCC-040 | Section VII SCC | Copyright, custom software, escrow, license limits, audit, confidentiality. |
| R-SCC-E-IMPLEMENTATION | SCC E | IT-SCC-041 through IT-SCC-048 | Section VII SCC | Representatives, project plan, reports, design documents, upgrades, inspections, acceptance tests. |
| R-SCC-F-GUARANTEES | SCC F | IT-SCC-049 through IT-SCC-055 | Section VII SCC | LDs, warranty, defect response, functional guarantees. |
| R-SCC-G-RISK | SCC G | IT-SCC-056 through IT-SCC-060 | Section VII SCC | Insurance requirements. |
| R-SCC-H-CHANGE | SCC H | IT-SCC-061 | Section VII SCC | Value engineering share. |
| R-SCC-I-DISPUTES | SCC I | IT-SCC-062 through IT-SCC-064 | Section VII SCC | Adjudicator appointing authority and arbitration rules. |

---

## 7. Rule dictionary

The following rules are package-level rules for `KE-PPRA-IT-2022-04`, implemented using the generalized STD Engine rule model. Rules should be stored with severity, stage, affected fields, legal/source basis, and a test case.

### 7.1 Rule severity convention

| Severity | Meaning |
| --- | --- |
| BLOCKER | User cannot proceed to the next governed state. |
| WARNING | User may proceed only with acknowledgement, justification, or reviewer attention. |
| INFO | Advisory or traceability notice. |

### 7.2 TDS rule register

| Rule code | Stage | Severity | Rule | Affected parameters | Engine action |
| --- | --- | --- | --- | --- | --- |
| IT-R-TDS-001 | Tender configuration | BLOCKER | TDS may contain only parameters defined by the active STD version. | All TDS | Reject arbitrary TDS rows. |
| IT-R-TDS-002 | Tender configuration | BLOCKER | Tender reference number, PE, tender name, and project site must be populated. | IT-TDS-001, 002, 003, 042 | Prevent validation success until complete. |
| IT-R-TDS-003 | Tender configuration | BLOCKER | If e-procurement is enabled, e-system name, URL, process aspects, and electronic procedures must be completed. | IT-TDS-005 to 008, 062, 063, 070 | Activate required fields. |
| IT-R-TDS-004 | Tender configuration | BLOCKER | Clarification deadline must be before tender submission deadline. | IT-TDS-021, 060, 061 | Date validation. |
| IT-R-TDS-005 | Tender configuration | BLOCKER | Pre-tender meeting date/time/place are required if pre-tender meeting is enabled. | IT-TDS-023 to 026 | Conditional required fields. |
| IT-R-TDS-006 | Tender configuration | BLOCKER | Site visit details are required if PE-organized site visit is enabled. | IT-TDS-027, 028 | Conditional required fields. |
| IT-R-TDS-007 | Tender configuration | WARNING | JV member maximum above 5 requires justification/review. | IT-TDS-010 | Flag reviewer. |
| IT-R-TDS-008 | Tender configuration | BLOCKER | Alternative time schedules or technical solutions cannot be enabled when alternative tenders are not permitted. | IT-TDS-031, 032, 033 | Conditional consistency check. |
| IT-R-TDS-009 | Tender configuration | BLOCKER | If alternative technical solutions are permitted, the affected parts and evaluation method must be specified. | IT-TDS-033, 034; Section III evaluation schema | Block until configured. |
| IT-R-TDS-010 | Tender configuration | BLOCKER | If price adjustment is enabled, applicable formulas/factors must be completed and review-routed. | IT-TDS-044 to 046 | Block publication until reviewed. |
| IT-R-TDS-011 | Tender configuration | WARNING | Price adjustment should normally be disabled for standard IT procurements unless justified by long duration, inflation exposure, or recurrent services. | IT-TDS-044 | Require justification if enabled. |
| IT-R-TDS-012 | Tender configuration | BLOCKER | Tender Security and Tender-Securing Declaration must not both be required unless a legal override is approved. | IT-TDS-049, 050 | Mutually exclusive validation. |
| IT-R-TDS-013 | Tender configuration | BLOCKER | Tender Security amount and currency are required when Tender Security is required. | IT-TDS-049, 051 | Conditional required fields. |
| IT-R-TDS-014 | Tender configuration | BLOCKER | Tender validity period must be a positive integer and must align with the Form of Tender validity statement. | IT-TDS-048; Form of Tender | Cross-render validation. |
| IT-R-TDS-015 | Tender configuration | BLOCKER | Tender opening date/time must be the same as or after the tender submission deadline. | IT-TDS-060, 061, 068, 069 | Date/time validation. |
| IT-R-TDS-016 | Tender configuration | WARNING | Opening should normally occur immediately after the deadline unless a justified difference is recorded. | IT-TDS-060, 061, 068, 069 | Reviewer notice. |
| IT-R-TDS-017 | Evaluation setup | BLOCKER | Missing item adjustment basis must be selected before price evaluation can be configured. | IT-TDS-072 | Evaluation configuration blocker. |
| IT-R-TDS-018 | Evaluation setup | BLOCKER | Currency conversion source/date/currency fields are required if more than one tender currency is allowed. | IT-TDS-073 to 076 | Evaluation configuration blocker. |
| IT-R-TDS-019 | Evaluation setup | BLOCKER | Margin of preference cannot apply unless the tender method/legal threshold allows it and the tender is not reserved to a protected group. | IT-TDS-077, 078; procurement method | Cross-field legal rule. |
| IT-R-TDS-020 | Tender configuration | BLOCKER | No tender may be reserved to more than one group unless the active legal configuration explicitly permits it. | IT-TDS-078 | Reservation validation. |
| IT-R-TDS-021 | Evaluation setup | BLOCKER | If lots/subsystems/slices are enabled, the evaluation method and price-quotation approach must be defined. | IT-TDS-004, 079, 080; Section III | Lot evaluation blocker. |
| IT-R-TDS-022 | Evaluation setup | WARNING | Conditional multi-lot discounts should not be considered when rated criteria are used unless reviewed. | IT-TDS-080, 082 | Reviewer notice. |
| IT-R-TDS-023 | Post-qualification setup | BLOCKER | Additional post-qualification tests require success criteria and responsible party. | IT-TDS-081 | Prevent vague benchmark tests. |
| IT-R-TDS-024 | Award setup | WARNING | Quantity variation above 20% requires justification and review. | IT-TDS-083, 084 | Review flag. |
| IT-R-TDS-025 | Dispute setup | WARNING | No-adjudicator option should be exceptional for complex IT procurements and requires justification. | IT-TDS-086 | Review flag. |
| IT-R-TDS-026 | Complaint setup | BLOCKER | Complaint recipient name/role, title, PE, and email must be complete. | IT-TDS-088 to 091 | Complaint procedure blocker. |
| IT-R-TDS-027 | Tender configuration | WARNING | Mandatory brand/model requirements require justification and procurement/legal review. | IT-TDS-037 | Anti-restrictive review flag. |
| IT-R-TDS-028 | Tender configuration | BLOCKER | If additional documents are required, each must specify respondent, mandatory/optional status, and evidence type. | IT-TDS-030 | Evidence schema validation. |

### 7.3 SCC rule register

| Rule code | Stage | Severity | Rule | Affected parameters | Engine action |
| --- | --- | --- | --- | --- | --- |
| IT-R-SCC-001 | Contract configuration | BLOCKER | SCC may contain only parameters defined by the active STD version. | All SCC | Reject arbitrary SCC rows. |
| IT-R-SCC-002 | Contract configuration | BLOCKER | Procuring Entity and Project Manager must be specified before SCC can be rendered. | IT-SCC-001, 002 | Required fields. |
| IT-R-SCC-003 | Contract configuration | BLOCKER | Notice addresses must include at least one reliable delivery method for Project Manager and PE fallback. | IT-SCC-005, 006 | Notice validation. |
| IT-R-SCC-004 | Contract configuration | BLOCKER | EDI standards/procedures are required if EDI is used for notices. | IT-SCC-007 | Conditional requirement. |
| IT-R-SCC-005 | Contract configuration | BLOCKER | Recurrent cost items in SCC must match recurrent cost tables and technical requirements. | IT-SCC-004, 008, IT-TDS-038, price schema | Cross-document validation. |
| IT-R-SCC-006 | Contract configuration | BLOCKER | Commencement period after effective date must be a positive integer. | IT-SCC-011 | Required validation. |
| IT-R-SCC-007 | Contract configuration | WARNING | Contract price adjustment should be disabled unless duration/exposure justifies it. | IT-SCC-012, 013 | Review flag. |
| IT-R-SCC-008 | Contract configuration | BLOCKER | If price adjustment is applicable, formula/index must be provided and finance/legal review must approve. | IT-SCC-012, 013 | Approval blocker. |
| IT-R-SCC-009 | Contract configuration | BLOCKER | Advance payment greater than zero requires advance payment security form activation. | IT-SCC-015 | Activates security form. |
| IT-R-SCC-010 | Contract configuration | BLOCKER | Payment milestones must be tied to deliverables, delivery, installation, training, operational acceptance, or recurrent service periods. | IT-SCC-014 to 025 | Payment schedule validation. |
| IT-R-SCC-011 | Contract configuration | BLOCKER | Payments that depend on operational acceptance require acceptance certificate workflow. | IT-SCC-018, 020, 024 | Activates acceptance certificate. |
| IT-R-SCC-012 | Contract configuration | BLOCKER | Recurrent cost payment schedule is required if recurrent costs are included. | IT-SCC-008, 025 | Conditional required field. |
| IT-R-SCC-013 | Contract configuration | BLOCKER | Performance security percentage must be specified and should not exceed 10% unless legal policy allows override. | IT-SCC-028, 029 | Security validation. |
| IT-R-SCC-014 | Contract configuration | WARNING | Reduced warranty-period performance security outside 1%-2.5% requires justification. | IT-SCC-030 | Review flag. |
| IT-R-SCC-015 | IP configuration | BLOCKER | Custom software/materials IPR allocation requires explicit model and legal review. | IT-SCC-032, 033 | Legal review blocker. |
| IT-R-SCC-016 | IP configuration | BLOCKER | If software escrow is required, release events, deposit/update obligations, verification, fees, and confidentiality must be configured. | IT-SCC-034, 035 | Escrow completeness validation. |
| IT-R-SCC-017 | IP configuration | WARNING | If substantial custom software is procured and escrow is disabled, justification is required. | IT-SCC-032, 034 | Review flag. |
| IT-R-SCC-018 | License configuration | WARNING | Software usage limits that may constrain future growth should prefer priced expansion over absolute prohibition. | IT-SCC-036 | Review flag. |
| IT-R-SCC-019 | License configuration | BLOCKER | Software audit rights must specify scope and procedure if audit is enabled. | IT-SCC-039 | Audit terms validation. |
| IT-R-SCC-020 | Confidentiality | WARNING | Confidentiality exemptions require legal review. | IT-SCC-040 | Review flag. |
| IT-R-SCC-021 | Implementation setup | BLOCKER | Project Plan chapters must include at minimum organization/management, implementation, training, testing/QA, and warranty/support unless legally reviewed. | IT-SCC-043 | Completeness validation. |
| IT-R-SCC-022 | Implementation setup | BLOCKER | Controlling technical documents requiring approval must block dependent downstream work until approved. | IT-SCC-045 | Workflow binding. |
| IT-R-SCC-023 | Implementation setup | BLOCKER | Operational acceptance test specification/reference is required before publication. | IT-SCC-048 | Publication blocker. |
| IT-R-SCC-024 | Guarantees/liabilities | BLOCKER | Liquidated damages rate requires cap; cap requires rate. | IT-SCC-049, 050 | Pair validation. |
| IT-R-SCC-025 | Guarantees/liabilities | WARNING | Intermediate milestone liquidated damages increase contract complexity and require precise implementation-schedule milestones. | IT-SCC-051 | Review flag. |
| IT-R-SCC-026 | Warranty/SLA | BLOCKER | Warranty period and defect response times must be specified for IT system procurements. | IT-SCC-053, 054 | Contract readiness blocker. |
| IT-R-SCC-027 | Risk/insurance | BLOCKER | If third-party liability insurance is imposed, amount, deductible, insured parties, and period must be specified. | IT-SCC-056 to 059 | Insurance validation. |
| IT-R-SCC-028 | Change management | WARNING | Value engineering supplier share above 50% requires special approval. | IT-SCC-061 | Review flag. |
| IT-R-SCC-029 | Disputes | BLOCKER | Adjudicator appointing authority is required if adjudicator is used and not named/agreed. | IT-SCC-062 | Dispute setup validation. |
| IT-R-SCC-030 | Disputes | BLOCKER | Arbitration rules must be selected for foreign supplier scenarios; Kenyan supplier disputes must refer to arbitration under Kenyan law. | IT-SCC-063, 064 | Contract rendering validation. |

---

## 8. Parameter dependencies

### 8.1 TDS dependency map

| Driver | Dependent fields | Dependency behavior |
| --- | --- | --- |
| E-procurement enabled | E-system name, URL, aspects, electronic submission procedure, electronic opening procedure | Required only when electronic procurement is enabled. |
| Pre-tender meeting enabled | Meeting date, time, place | Required only when meeting is enabled. |
| Site visit enabled | Site visit details | Required only when visit is enabled. |
| Alternative tenders status | Alternative time schedule, alternative technical solutions | Cannot enable alternatives when alternatives are not permitted. |
| Alternative technical solutions enabled | Affected parts, Section III evaluation method | Required. |
| Recurrent cost items required | Recurrent cost table, recurrent contract choice, SCC recurrent services | Activates recurrent cost schema. |
| Price adjustment enabled | Local and/or foreign adjustment factor/formula | Required and review-routed. |
| Tender Security required | Security amount/currency, accepted security forms | Required; Tender-Securing Declaration disabled unless override. |
| Multiple currencies allowed | Evaluation currency, comparison currency, exchange rate source, exchange rate date | Required. |
| Margin of preference enabled | Tender method/legal threshold checks | Must pass legal validation. |
| Reservation group selected | Invitation wording, eligibility evidence | Activates reservation-specific rendering and evidence. |
| Lots/subsystems/slices enabled | Lot list, separate pricing, conditional discount handling, evaluation methodology | Required. |
| Additional post-qualification tests configured | Test method, success criteria, responsible party | Required. |

### 8.2 SCC dependency map

| Driver | Dependent fields | Dependency behavior |
| --- | --- | --- |
| Recurrent services included | Recurrent cost items, post-warranty period, recurrent payment schedule | Required. |
| Advance payment > 0 | Advance payment security | Required. |
| Price adjustment applicable | Formula/index and finance/legal approval | Required. |
| Custom software/materials included | IPR allocation, custom materials appendix, possible escrow | Required/review-routed. |
| Escrow required | Escrow agent, release events, fees, update obligations, verification, confidentiality | Required. |
| Software audit rights enabled | Audit conditions | Required. |
| Operational acceptance payment/milestone exists | Acceptance test specification and certificate workflow | Required. |
| Liquidated damages enabled | Rate and cap | Required as pair. |
| Third-party liability insurance imposed | Amount, deductible, insured parties, period | Required. |
| Value engineering share set | Percentage review | Warning above 50%. |
| Foreign supplier scenario | Arbitration rules | Required. |

---

## 9. Suggested database insert groups

This pass should translate into the following package modules.

| Package module | Records to add/update |
| --- | --- |
| `parameters/tds_parameters.json` | Add IT-TDS-001 through IT-TDS-091. |
| `parameters/scc_parameters.json` | Add IT-SCC-001 through IT-SCC-064. |
| `rules/tds_rules.json` | Add IT-R-TDS-001 through IT-R-TDS-028. |
| `rules/scc_rules.json` | Add IT-R-SCC-001 through IT-R-SCC-030. |
| `rendering/tds_render_blocks.json` | Add R-TDS-A through R-TDS-F render block mappings. |
| `rendering/scc_render_blocks.json` | Add R-SCC-A through R-SCC-I render block mappings. |
| `source_trace/source_anchors.json` | Add source anchors for each TDS/SCC parameter. |
| `review_flags/extraction_flags.json` | Add TDS ITC/ITT label flag and SCC GCC 1.1(e) numbering flag. |
| `smoke_tests/tds_scc_smoke_tests.json` | Add all smoke tests listed below. |

---

## 10. NSSF ERP calibration notes

The NSSF SPS ERP tender validates the need for the TDS/SCC model to handle real ERP procurement values, including:

| NSSF calibration item | Engine implication |
| --- | --- |
| Tender reference and title are fully instantiated. | IT-TDS-001 through IT-TDS-003 must render across invitation, TDS, forms, and contract. |
| Maximum JV members set to three. | IT-TDS-010 supports ordinary integer configuration. |
| Pre-tender meeting marked N/A. | IT-TDS-023 can be false/disabled and should suppress meeting detail requirements. |
| Alternative tenders not permitted. | IT-TDS-031 should disable alternative technical/time-schedule paths. |
| Price adjustment not permitted; prices fixed. | IT-TDS-044 and IT-SCC-012 support fixed-price configurations. |
| Tender validity set to 154 days. | IT-TDS-048 must propagate into Form of Tender. |
| Professional indemnity used as a tender requirement. | This should be modeled through additional evidence/security configuration, not by changing locked ITT text casually. |
| SCC uses phase-based payment milestones. | IT-SCC-014 must support a milestone schedule, not only the STD's default category percentages. |
| SCC includes source-code/configuration transfer and escrow conditions. | IT-SCC-032 through IT-SCC-035 are necessary for ERP/customization-heavy tenders. |
| SCC includes SLA response/resolution times and uptime. | IT-SCC-054 must support structured severity-based SLA terms. |
| Performance security set to 10% and warranty-plus-60-days validity. | IT-SCC-028 through IT-SCC-030 must support percentage, validity, form, and duration rules. |

The calibration also shows why the engine must be strict: a real tender may compress, relabel, or simplify STD sections. The platform should allow controlled completion and project-specific configuration, but not undocumented mutation of the official STD structure.

---

## 11. Smoke contracts

| Smoke ID | Test | Expected result |
| --- | --- | --- |
| SMK-IT-TDS-001 | Create IT tender with missing PE name. | Validation fails. |
| SMK-IT-TDS-002 | Enable e-procurement without URL/procedures. | Validation fails. |
| SMK-IT-TDS-003 | Set clarification deadline after submission deadline. | Validation fails. |
| SMK-IT-TDS-004 | Mark pre-tender meeting as required but omit date/time/place. | Validation fails. |
| SMK-IT-TDS-005 | Set alternative tenders as not permitted but enable alternative technical solutions. | Validation fails. |
| SMK-IT-TDS-006 | Enable price adjustment but omit formula/factors. | Validation fails. |
| SMK-IT-TDS-007 | Require both Tender Security and Tender-Securing Declaration. | Validation fails unless legal override exists. |
| SMK-IT-TDS-008 | Allow multiple currencies but omit exchange-rate source/date. | Validation fails. |
| SMK-IT-TDS-009 | Apply margin of preference to a reserved tender. | Validation fails. |
| SMK-IT-TDS-010 | Select two reservation groups. | Validation fails. |
| SMK-IT-TDS-011 | Configure lots without lot evaluation method. | Validation fails. |
| SMK-IT-TDS-012 | Configure no adjudicator for complex ERP tender. | Validation passes only with warning and justification. |
| SMK-IT-SCC-001 | Create SCC without Project Manager. | Validation fails. |
| SMK-IT-SCC-002 | Include recurrent services but omit recurrent payment schedule. | Validation fails. |
| SMK-IT-SCC-003 | Configure advance payment but omit advance payment security activation. | Validation fails. |
| SMK-IT-SCC-004 | Configure custom software but omit IPR allocation. | Validation fails. |
| SMK-IT-SCC-005 | Require escrow but omit release events. | Validation fails. |
| SMK-IT-SCC-006 | Add operational acceptance payment without acceptance test specification. | Validation fails. |
| SMK-IT-SCC-007 | Configure liquidated damages rate but omit cap. | Validation fails. |
| SMK-IT-SCC-008 | Omit warranty period and defect response times. | Validation fails. |
| SMK-IT-SCC-009 | Set value engineering supplier share to 75%. | Validation passes only with warning and approval requirement. |
| SMK-IT-SCC-010 | Select foreign supplier arbitration without arbitration rules. | Validation fails. |

---

## 12. Review flags created by Pass 2

| Flag ID | Area | Issue | Required handling |
| --- | --- | --- | --- |
| E-005 | TDS source label | TDS table uses `ITC Clause` in some places, while the document and engine model use `ITT`. | Preserve source-visible label but normalize internally to ITT; legal review before rendered correction. |
| E-006 | SCC source reference | SCC GCC 1.1(e) numbering appears inconsistent around contract period/post-warranty service definitions. | Preserve source reference; normalize internal mapping; legal/procurement review before activation. |
| E-007 | Payment model | STD default SCC payment categories may not fit phased ERP procurements without milestone-based customization. | Allow controlled milestone schedule but require deliverable/acceptance linkage. |
| E-008 | Professional indemnity calibration | NSSF tender uses Professional Indemnity as a mandatory tender requirement rather than the standard security wording. | Model as a configurable evidence/security requirement; do not alter locked ITT unless approved. |
| E-009 | IPR/escrow complexity | SCC notes show multiple possible IPR strategies for custom software and escrow. | Force legal review for custom software/material IPR and escrow choices. |

---

## 13. Activation gate for Pass 2 content

This pass remains **not activatable**. The `KE-PPRA-IT-2022-04` package can only progress from `STRUCTURING` to `INTERNAL_REVIEW` after the following are true:

1. All TDS parameters have source anchors and render blocks.
2. All SCC parameters have source anchors and render blocks.
3. TDS and SCC rules have at least one smoke test each for blocker behavior.
4. The ITC/ITT TDS label anomaly is recorded as an extraction review flag.
5. SCC numbering anomaly around GCC 1.1(e) is recorded as an extraction review flag.
6. Payment schedule logic supports both default category-based and milestone-based payment models.
7. IPR/custom software/escrow parameters are review-routed to legal reviewers.
8. NSSF ERP tender fixture can be represented without direct locked-text edits.

---

## 14. Next artifact

The next artifact should be:

**IT STD Full Source Extraction Pass 3 - Evaluation, Qualification, Tendering Forms, and Price Schedule Schemas**

That pass should extract:

1. Section III evaluation and qualification criteria.
2. Preliminary responsiveness criteria.
3. Technical evaluation criteria.
4. Price evaluation rules.
5. Qualification forms and evidence requirements.
6. Tendering forms field schemas.
7. Price schedule tables.
8. Intellectual property forms.
9. Conformance forms.
10. Related smoke contracts.
