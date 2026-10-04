# STD-TPL-001 — IT Equipment Open Tender Template Release Contract

| Control | Value |
|---|---|
| Document ID | STD-TPL-001 |
| Version | 0.11 |
| Date | 26 September 2026 |
| Status | **Proposed — v0.10 was Project Owner review; re-approval required** (v0.10 was never approved; v0.10 read: **Proposed for approval**) |
| Template key | `IT-EQUIPMENT-OPEN-V1` |
| Template release | 1.1 (v0.10 read: 1.1 candidate; owner decision OD5 retired the Candidate lifecycle state, §14.1) |
| Product profile | `GOODS-IT-SIMPLE-V1` |
| Renderer profile | `BDS-GOODS-IT-V1` |
| Official STD family | PPRA Standard Tender Document for Procurement of Goods |
| Supported use | Straightforward off-the-shelf IT equipment, delivery and minor related services |
| Current consumers | REQ-CHG-001 v1.12 approved upstream handoff; TPR-CHG-001 v0.11 and BDS-CHG-001 v0.7 coordinated proposed consumers; CFG-CHG-002 v0.16 proposed retains only site configuration, effective-rule and public-portal-information ownership |
| Design standard | KT-STD-001 v1.8 |
| Implementation authority | STD-TPL-IMP-001 v1.0 after approval. Under owner decision OD5 (26 September 2026), an intact release 1.1 installs Available and switched On; the §13 reviews, the §14.2 gates and any owner decision are recorded evidence and never block use (§14.1). (v0.10 read: Release 1.1 still requires completion of §13, all §14 gates and owner approval of the exact manifest before it may become Available.) |
| Reservation correction | MVP 1 supports `None`, Youth, Women and Persons with disabilities, plus the independently applicable County-residents restriction. Treatment is inherited, rule-backed and pass/fail; Planning designation never proves bidder entitlement. |
| Change type | Successor to v0.10 (Project Owner review, never approved). One owner-directed concern: reflects owner decision OD5 of 26 September 2026. A template release is an On/Off switch on a site. An intact release installs Available and switched On. Gates, reviews (including Gates D and E) and any owner decision are recorded evidence that never block use. **STD Templates** shows a release as Available only when its lifecycle is Available, its site switch is On, its integrity is verified and its renderer is registered. Also corrects the §12.1 statement that the runtime assets, validator and manifest already existed (follow-up FU-02). No other requirement changes. Full changes: §18.3. |
| Previous change type (v0.10, retained) | Successor to v0.9. Retains curated code-owned releases and prohibits runtime template authoring, while closing implementation authority, administrative visibility, structured gates, release comparison, concern capture, renderer abstraction and in-flight Tender lifecycle gaps. Full changes: §18.2. |

## 1. Purpose

This document defines the complete first KenTender Tender template, the exact procedure for constructing its controlled bundle and the evidence required to release it.

The release has two equally authoritative projections:

1. the human-readable Invitation and issued Tender documents; and
2. the machine-readable supplier-response definition used to generate the electronic Bid Workspace and preserve evaluation and contract lineage.

Both projections come from one released template and one approved Tender Version. The PDF is not parsed to create the Bid Workspace, and the structured definition does not replace the published legal document.

The template is prepared and reviewed by the KenTender product team and shipped as a code-owned software release. A Procurement Officer uses it but cannot edit its fixed clauses, response structure, evaluation treatment or contract mappings.

In this document, **template configuration** means the exact installed release, its compatibility, evidence and availability. It does not mean site-authored clauses, fields, forms, evaluation criteria or mappings. Visibility is mandatory; operational template editing is prohibited.

## 2. Product boundary

### 2.1 Supported release

| Decision | Release 1.1 treatment |
|---|---|
| Procurement category | Goods — IT equipment |
| Procurement method | Open Tender |
| Typical products | Laptops, desktops, tablets, monitors, printers, scanners, network equipment, power-protection equipment and peripherals |
| Related services | Delivery, installation, configuration, testing, training or orientation only when ancillary to the Goods |
| Lots | One lot |
| Currency | KES only |
| Price | Fixed price |
| Reservation | `None`, `Youth`, `Women` or `Persons with disabilities`; an independently applicable `County residents` restriction may also be present when the site is a county procuring entity and the verified rule permits it |
| Technical evaluation | Mandatory pass/fail checks feeding one Technical compliance gate |
| Financial evaluation | Arithmetic and financial evaluation under the approved lowest-evaluated-responsive treatment |
| Supplier submission | Structured electronic responses, evidence and price schedule |
| Template maintenance | Code-owned release; no operational editor |

### 2.2 Rejected uses

The release rejects:

- Works;
- consulting or non-consulting services;
- software development, integration, implementation or data migration as the main purpose;
- multiple lots or award packages;
- a reservation category outside `None`, `Youth`, `Women` or `Persons with disabilities`;
- a County-residents restriction without an applicable verified rule, approved overlap treatment or released rendering/evidence rule;
- weighted technical scoring;
- multiple currencies or alternative price schedules;
- an unsupported procurement method;
- a Requisition without authorised structured technical requirements and objective acceptance checks; or
- any response, validation, composition or mapping not supported by `BDS-GOODS-IT-V1`.

Rejection is a compatibility outcome, not an invitation to configure the template at runtime.

## 3. Ownership and authority

| Layer | Owns | Must not do |
|---|---|---|
| Requisition | Authorised goods, quantities, destinations, dates, technical requirements, warranty/support, ancillary services, acceptance checks, operative supporting materials, reservation category, County-residents restriction and exact rule snapshots | Delegate an enforceable requirement to an unstructured attachment or assert bidder entitlement |
| This template release | Official-document treatment; product composition; response rules; declarations; price treatment; evaluation groups; contract projection; supported renderer | Ask Procurement Officers to design forms or criteria |
| Tender Preparation | Bind the exact released template to the authorised Requisition and approved Tender-specific decisions; generate and freeze one Tender Version | Re-enter inherited requirements or invent response/evaluation fields |
| Bid Workspace | Render the exact published definition and save typed responses by stable identity | Infer fields from a PDF or execute arbitrary metadata |
| Evaluation and Contract modules | Consume the published identities and mappings | Re-key or reinterpret the Bid after submission |
| **STD Templates** administrative surface | Show the installed release, scope, documents, response definition, mappings, evidence and blockers from the exact installed-release projection | Edit, activate, upload, repair or override a release; switch it On or Off — the site switch is a deployment command outside this surface (§14.1, owner decision OD5) |

### 3.1 Closed integration contracts

The release is integrated through the following contracts. Each contract has one owner; consumers must use the exact identity, version and digest fields and must not infer missing facts.

| Contract | Producer → consumer | Required purpose | Mutability and failure rule |
|---|---|---|---|
| `AuthorisedRequisitionHandoff v1.3` | Requisitions → Tenders/template builder | Exact authorised items, structured requirements, services, acceptance checks, reservation treatment, rule snapshots and lineage | Immutable. Missing or incompatible content blocks Tender creation; the template does not repair or enrich it. |
| `InstalledSTDRelease v1` | Release registry → Tenders and **STD Templates** | Exact release identity, product/renderer support, constituent digests, manifest, approval, verification and blockers; from v0.11, the site switch state, with any recorded approval or owner decision as evidence only (OD5) | Immutable per installed release. Only `Available` may be bound to a new Tender (v0.11, OD5: only a release that is `Available` and switched On, §14.1); read-only inspection never changes status. The site switch changes only through the deployment command in §14.1 and never changes release content. |
| `TenderVersion v1` | Tenders → document/definition builder | Exact authorised handoff plus the finite officer decisions; effective addenda are separate immutable builder inputs and never fields written back into the Version | Submitted/approved Versions are immutable. Unsupported content blocks review or publication authorisation. |
| `PublishedBidDefinition v1` | Tenders + exact STD release → Bid Submission | Exact bidder tasks, response rows, declarations, price rows, reservation treatment and downstream mappings bound to one publication | Materialised and frozen atomically with publication authorisation. Any unknown control, missing mapping or digest mismatch blocks authorisation; BDS never repairs it. |
| `SubmittedBidProjection v1` | Bid Submission → Opening/Evaluation/Contract | Exact submitted response identities, evidence, calculations, signature/custody lineage and published mappings | Immutable per submitted Version. Downstream modules do not re-key or reinterpret responses. |
| `InstalledSTDReleaseProjection v1` | Release registry → **STD Templates** | Plain-language list/detail, previews, review pack, verification and exact blockers | Read-only. Missing owner facts display as missing and fail inspection acceptance; UI does not parse assets or raw JSON to reconstruct them. |

### 3.2 Canonical release and instance identity

Use these names consistently:

| Name | Meaning |
|---|---|
| `template_key` | Stable product release family key, here `IT-EQUIPMENT-OPEN-V1`. |
| `release_id` | Opaque installed release record identity. |
| `template_release` | Human-readable semantic release, here `1.1`. |
| `product_profile_id` | Exact product composition identity, here `GOODS-IT-SIMPLE-V1`. |
| `renderer_profile_id` | Exact renderer contract identity, here `BDS-GOODS-IT-V1`. |
| `supported_renderer_version` | Exact deployed renderer version accepted by the release. |
| `tender_version_id` | Immutable Tender Version that supplies the published facts. |
| `publication_id` | Immutable publication-authorisation record that freezes the original definition and owns subsequent subject-scoped channel evidence. |
| `bid_definition_id`, `definition_version` | Immutable Published Bid Definition identity and sequential Version. |

Aliases such as `template_family`, when retained at an external boundary, must equal `template_key` and are never separate identities. A field ending `_id` carries an opaque identity, not a display release number.

## 4. Controlled release pack

The release pack has this structure:

```text
it_equipment_open_v1/
├── 01_source/
│   ├── ppra_goods_std_official.pdf
│   ├── ppra_goods_std_official.txt
│   ├── source_record.md
│   └── pages/
├── 02_master/
│   ├── invitation_to_tender.html
│   ├── complete_tender.html
│   └── print.css
├── 03_registers/
│   ├── coverage_register.csv
│   ├── insertion_points.csv
│   └── forms_register.csv
├── 04_fixture/
│   ├── moh_input.json
│   ├── render_fixture.py
│   ├── build_definition_fixture.py
│   ├── moh_invitation_expected.html
│   ├── moh_invitation_expected.pdf
│   ├── moh_expected.html
│   ├── moh_expected.pdf
│   ├── package_index.md
│   └── reservation_variants/
│       ├── none_input.json
│       ├── none_expected.json
│       ├── women_input.json
│       ├── women_expected.json
│       ├── persons_with_disabilities_input.json
│       ├── persons_with_disabilities_expected.json
│       ├── county_residents_input.json
│       ├── county_residents_expected.json
│       ├── unsupported_overlap_input.json
│       └── unsupported_overlap_expected.json
├── 05_review/
│   ├── open_issues.md
│   ├── release_gates.json
│   ├── release_change_report.json
│   ├── validation_report.json
│   └── review_record.md
└── 06_runtime/
    ├── product_profile.json
    ├── response_rules.json
    ├── downstream_rules.json
    ├── addendum_identity_rules.json
    ├── moh_published_bid_definition_expected.json
    ├── release_manifest.json
    └── validate_release.py
```

### 4.1 File responsibilities

| Asset | Responsibility |
|---|---|
| Official source and page images | Exact legal/source comparison evidence |
| HTML masters and print CSS | Human-readable Invitation and issued Tender projections |
| Coverage, insertion and forms registers | Complete source treatment and render traceability |
| MoH input and expected outputs | Deterministic document fixture |
| Fixture render/build scripts | Curation-only deterministic generators for the human outputs and Published Bid Definition; never installed as runtime code |
| Product profile | Permitted tasks, groups, controls, compositions and renderer compatibility |
| Response rules | How each authorised source type becomes a bidder-visible response |
| Downstream rules | How responses feed evaluation groups and contract obligations |
| Addendum identity rules | Permitted identity-preserving response migration |
| Expected Published Bid Definition | Deterministic structured-output fixture |
| Release gates | Machine-readable result for every mandatory release gate, with evidence references and no implicit pass |
| Release change report | Generated, structured comparison with the preceding release; identifies added, changed, removed and compatibility-significant content |
| Release manifest | Canonical inventory, schema versions, constituent digests, validator result and exact candidate bundle identity presented for owner approval (v0.10). From v0.11 (OD5) the manifest is the installation integrity reference; an owner decision, when recorded, is evidence only (§13.10) |
| Release validator | Reconciliation, identity, mapping and completeness checks |
| Review record | Named decision, immutable digests and any release blocker (v0.11, OD5: the decision is evidence only, and a recorded blocker is an open review item that does not block installation or use) |

The runtime JSON files are declarative, code-owned release assets. They are not an operational schema editor, executable rules language or supplier-visible manifest.

## 5. Official source and document curation

### 5.1 Source record

The source record shall state the exact official title, STD family, printed revision or issue date, download filename, official URL, retrieval date, SHA-256, reviewer and review date. An absent source fact is recorded as `Not stated in source`.

The selected PPRA Goods STD is the legal/source master. Entity-specific examples are fixtures only and cannot supply missing law, policy or wording.

### 5.2 Source coverage

Every official heading, instruction, table and form has exactly one coverage-register row and one approved treatment:

- locked and rendered;
- rendered from an approved insertion;
- conditionally rendered through an approved named condition;
- completed by the supplier, award or contract stage; or
- excluded with a stated release reason.

No operative content may disappear merely because it is difficult to digitise.

### 5.3 Human-readable outputs

The release generates:

1. a separate Invitation to Tender; and
2. one complete issued Tender containing its cover, contents and Sections I–VIII.

Both use the same Tender Version and package identity. The Invitation is not embedded in the issued Tender. Neither output may contain unresolved brackets, drafting instructions, missing operative text or an independently maintained duplicate value.

### 5.4 Fixed authoring rules

- Fixed official wording remains read-only.
- Named Jinja values and approved conditions are recorded in `insertion_points.csv`.
- Repeated document rows are limited to reviewed schedules and forms.
- Jinja contains no database calls, permissions, calculations or business decisions.
- JavaScript is prohibited in the masters.
- The document renderer and electronic-response builder consume the same canonical Tender facts.
- The PDF is an output, never the electronic-response source.

## 6. Tender data ownership

### 6.1 Inherited from the authorised Requisition

| Fact | Treatment |
|---|---|
| PE, Plan Item, Requisition and source-line identities | Read-only lineage |
| Requirement title and procurement method | Read-only; compatibility checked |
| Goods descriptions, categories, quantities and units | Read-only |
| Delivery locations and latest delivery dates | Read-only |
| Technical requirement rows | Read-only structured rows with characteristic metadata |
| Warranty and support values | Read-only |
| Related-service rows | Read-only structured rows |
| Acceptance requirements | Read-only structured rows |
| Supporting materials and their linked requirement identities | Read-only governed artifacts |
| Reservation and lotting | Read-only. Reservation category is `None`, `Youth`, `Women` or `Persons with disabilities`; County-residents is a separate applicable true/false restriction; lotting remains `Single lot`. Exact effective rule/version identities and approved overlap treatment are preserved. |

Where compatible items share one specification, the supplier-facing schedule may group them. Every contributing `requisition_item_id`, source allocation and quantity remains retrievable; grouping never destroys lineage.

### 6.2 Entered by the Procurement Officer

Only the following finite decisions are editable:

| Area | Officer decision |
|---|---|
| Tender details | Clear title; issue, clarification and submission dates; validity; optional pre-tender meeting |
| Tender security | Approved treatment, amount and currency within the released choices |
| Supplier evidence | Manufacturer authorisation, datasheet/brochure, justified comparable-experience requirement, after-sales evidence and zero or more separately justified requirement-linked additional evidence rows. Every additional row has a stable identity, evidence type, linked inherited requirement and mandatory/optional treatment; it cannot create a hidden qualification or technical obligation. |
| Contract terms | Payment timing, performance-security treatment and percentage, delay-damages rate/cap, **Inspection and acceptance location** and **Contract contact office** within released choices |

The officer cannot edit goods, quantities, technical requirements, services, acceptance checks, evaluation mappings, response types, price-line identities or contract mappings.

### 6.3 Generated values

Tender reference, opening date/time, security validity dates, schedules, response identities, calculations, forms, documents, mappings and digests are generated. A generated value is never independently editable.

## 7. Document schedules and forms

### 7.1 Goods and delivery

Each supplier-facing goods line contains the stable schedule identity, description, quantity, unit, destination, latest delivery date, minimum warranty and source-item lineage. The supplier gives the offered make/model, offered delivery commitment, linked evidence and permitted prices.

### 7.2 Related services

When present, each line inherits `service_requirement_id`, service type, required result, coverage, completion boundary and acceptance evidence. The supplier confirms the service, gives the permitted offered completion date and price, and links required evidence. The Procurement Officer does not recreate the line.

### 7.3 Technical requirements and acceptance

Section V renders the authorised structured requirements directly. No technical-specification PDF is required. An optional supporting document may supplement linked rows but cannot be the only statement of an obligation.

Each technical row keeps `technical_requirement_id`; each acceptance row keeps `acceptance_requirement_id`. These identities appear in the human-readable schedule where useful and always remain in the structured definition.

### 7.4 Forms

Official fixed declaration text remains locked. Known PE, Tender and supplier facts are captured once and reused. Supplier, award and contract fields are completed only at their proper stage. A form excluded by this product boundary is neither displayed nor silently replaced.

## 8. Electronic Bid Workspace definition

### 8.1 Five supplier tasks

The current product profile generates these tasks:

| Task | Purpose |
|---|---|
| Tender documents and addenda | View and acknowledge the current published package |
| Company, declarations and tender security | Complete supplier facts, official declarations, applicable reservation declaration/evidence and security response |
| Requirements and supporting evidence | Respond to goods, technical, warranty/support, experience, service, acceptance and evidence requirements |
| Price | Complete the published Goods and related-service price schedules |
| Review and submit | Resolve blockers, review, sign and submit the exact package |

These are supplier tasks, not Procurement Officer tasks and not a universal layout for Works or Services.

### 8.2 Allowed controls and compositions

The renderer accepts only released controls: confirmation, yes/no, controlled single choice, controlled multi-select, short text, long text, integer, decimal, money, date, evidence reference and structured ports list. Published facts and calculations are read-only. Controlled multi-select preserves option codes and order rules; the structured ports list preserves one row identity, port type, quantity and required/optional treatment. Neither is an arbitrary nested-form facility.

Released compositions are: document/addendum acknowledgement, supplier-details form, locked declaration, reservation-eligibility response, tender-security response, Goods offer, technical-compliance group, warranty/support group, experience group, related-services confirmation, acceptance confirmation, evidence list, Goods price schedule and review/signature summary.

Unknown controls, compositions, validations or renderer versions block publication and Bid start. There is no generic fallback.

### 8.3 Response generation

| Published source | Generated supplier response |
|---|---|
| Goods line | Offered make/model, delivery commitment, evidence references and price inputs |
| Technical requirement | `Comply` or `Do not comply`, offered value using the released characteristic control, optional comment and required evidence |
| Warranty/support fact | Confirmation and the applicable offered value, contact or service detail |
| Comparable experience | Required contract entries and evidence only when the approved Tender requires them |
| Related service | Confirmation, offered completion date, evidence and price input |
| Acceptance requirement | Explicit confirmation of the resulting obligation |
| Evidence requirement | One or more permitted evidence references linked to the exact response or declaration |
| Reservation treatment | Category-specific declaration, certificate/reference/validity facts and evidence references required by the exact published rule; County-residents evidence is separate where applicable and is never inferred from an address alone |
| Declaration | Confirmation/signature against the exact locked text version |
| Price row | Permitted monetary inputs; system-calculated totals are read-only |

Every response has a stable published identity, source lineage, type, requiredness, applicability, validation and downstream treatment. The definition introduces no obligation absent from the issued Tender.

### 8.4 Validation

Validations reference only named code-owned rules with bounded parameters. Executable expressions, client-authored rules, arbitrary nesting and hidden conditions are prohibited. The server revalidates every save and submission against the exact published definition.

## 9. Evaluation and contract mappings

### 9.1 Evaluation model

The release has four governed evaluation groups/stages:

1. submission and eligibility;
2. Technical compliance;
3. arithmetic and financial evaluation; and
4. award under the approved rule.

The exact group identities are `EVG-ELIGIBILITY`, `EVG-TECHNICAL-COMPLIANCE`, `EVG-FINANCIAL` and `EVG-AWARD`. Award is not a weighted criterion screen; it consumes the prior governed results and the published award rule.

Mandatory technical, warranty, service and acceptance responses retain individual checks for evidence and reasons, but they feed one `EVG-TECHNICAL-COMPLIANCE` group outcome. They are not eleven independently designed criteria and have no weights.

| Response family | Evaluation destination |
|---|---|
| Official declarations, eligibility and Tender security | `EVG-ELIGIBILITY` |
| Reservation declaration and evidence | `EVG-ELIGIBILITY`; pass/fail against the published category and evidence rule, never against the Planning label alone |
| Mandatory technical, warranty/support and related-service compliance | `EVG-TECHNICAL-COMPLIANCE` |
| Experience and requirement-linked evidence | The published eligibility or technical group named in the rule |
| Price rows and calculations | `EVG-FINANCIAL` |
| Document acknowledgement and administrative contact facts | Explicitly `Not evaluated` |

The group result, each failed mandatory check and its reason are retained. Evaluators cannot add, remove, weight or rewrite a published check.

### 9.2 Contract projection

| Accepted response | Contract destination |
|---|---|
| Goods offer and delivery commitment | Goods/delivery schedule |
| Accepted technical offer | Technical obligation schedule |
| Warranty/support commitment | SCC and warranty/support schedule |
| Related-service commitment | Related-services schedule |
| Acceptance confirmation | Inspection and acceptance schedule |
| Awarded price | Contract price schedules |
| Eligibility-only evidence or administrative acknowledgement | Explicitly `Not carried forward` into contract obligations; reservation category, County-residents applicability and the evaluated eligibility result remain available to the governed award/reporting handoff |

Every response declares a destination or an explicit `Not applicable`. No free text is copied into a contract merely because it was supplied.

## 10. Addenda and identity preservation

An addendum creates a new immutable definition version. Every prior identity is classified using exactly one of these machine values:

- `unchanged`;
- `converted`;
- `fresh_response_required`;
- `removed`; or
- `new`.

Only exact unchanged identities copy automatically. Labels, row positions and text similarity are never used as identity. Removed responses remain in prior history; new required responses begin incomplete. The bidder is shown the affected tasks in ordinary language.

At addendum issue, Tenders applies these released identity rules to the current effective definition plus the one proposed immutable addendum and freezes a complete successor `PublishedBidDefinition`. The successor is not bidder-effective while any original required publication channel remains unconfirmed. Final channel confirmation atomically makes the addendum, revised deadline and exact successor definition effective; the template runtime never exposes a partial or awaiting-confirmation definition as current.

### 10.1 Clarification and candidate-notice boundary

The bundle owns published Tender wording, the structured bidder definition and addendum identity/migration rules. It does not own candidate registration, a supplier-question store, answer workflow, notice audiences, notice destinations, delivery attempts or public support/legal links. TPR v0.10 owns clarifications and mandatory candidate notices; BDS v0.7 owns Tender-bound candidate registration and the verified notice contact; CFG v0.16 owns the allowlisted public support/legal-link projection.

When an answer changes the published Tender, TPR must first issue an addendum and apply this bundle's identity rules. A non-changing answer and its delivery evidence do not change a controlled template byte, bundle digest or Published Bid Definition. Candidate-notice copy may identify an issued addendum or changed deadline, but it is an operational record derived from the governing TPR event, not a reusable clause or bundle asset.

## 11. **STD Templates** read-only administrative surface and static design contract

Installed template inspection is a first-class module named **STD Templates**. It is not part of System setup because template releases are code-owned product assets, not site configuration. The menu item is visible to Administrator, System Manager, Procurement Officer and Head of Procurement Function; all access is read-only except the bounded **Report concern** action.

Canonical routes are:

- list: `/app/std-templates`;
- detail: `/app/std-templates/{release_id}`; and
- immutable preview/download locators returned by the owner projection.

This section is the complete design input for the common list/detail surface. Supply KT-STD-001 v1.8 §2 and this §11 in full to the design tool. Do not also supply CFG, TPR, BDS or the bundle ZIP to invent missing layout. Product-specific values come from the closed fixture in §11.5; runtime values come from `InstalledSTDReleaseProjection v1`.

### 11.1 Shared shell and composition

Use the established KenTender Desk shell. Breadcrumb: **Home / STD Templates** on the list and **STD Templates / {display name}** on detail. Page eyebrow **TENDER DOCUMENT STANDARDS**. List title **STD Templates**. Description **Review the Tender formats installed on this site, what they support and whether they are ready to use.** No page-header primary action.

The list composition, in order, is:

1. page header;
2. compact filter row;
3. results table or labelled cards at 390 px; and
4. truthful filtered-empty or installed-empty state.

The detail composition, in order, is:

1. **Back to STD Templates** text link;
2. release header and one plain status consequence;
3. five section navigation links — **Overview**, **Tender content**, **Bid response and downstream use**, **Coverage and changes**, **Verification**;
4. the five complete sections in that order;
5. collapsed **Technical details**; and
6. a quiet footer with the last verification time and no action.

No raw JSON, database field name, digest or renderer key appears in the default reading path. Technical identities and digests remain available only inside **Technical details** for authorised diagnosis.

### 11.2 STD-DES-01 — installed template list

Filters are **Search Tender format** and **Status** (`All statuses`, `Available`, `Unavailable`, `Superseded`, `Withdrawn`). **Clear filters** appears only when a filter is active. Filters never change installation or availability.

Use one compact table with these columns and no additional columns:

| Column | Visible treatment |
|---|---|
| Tender format | Display name primary; `template_key` secondary. |
| Release | Human-readable `template_release`. |
| Supported use | One plain line naming category, method, lot treatment and reservation support; truncate visually only with an accessible full label. |
| Status | One badge: `Available`, `Unavailable`, `Superseded` or `Withdrawn`. |
| Official source | Plain official source title. |
| Last verified | EAT date/time or **Not yet verified**. |
| Action | **View** text action. |

Status consequence below an Unavailable row, when space permits: **This release cannot be used to publish a Tender. Open it to see why.** (v0.11, OD5; v0.10 read: **This release cannot be used to publish a Tender. Open it to see what remains.**) Do not show Add, Edit, Activate, Approve, Switch on, Switch off, Upload, Replace, Override, Repair or a kebab menu.

Filtered empty: **No STD Templates match these filters.** with **Clear filters** as the only action. Installed empty: **No STD Templates are installed. Ask whoever manages this site to install a release.** (v0.11, OD5; v0.10 read: **No STD Templates are installed. Ask the controlled template-release owner to install an approved release.**) with no action.

### 11.3 STD-DES-02 — release detail

Header title is the display name. Supporting line is **Release {template_release} · {status}**. For Unavailable show the plain consequence for its cause (v0.11, OD5). When the release is switched Off: **New Tenders cannot start on this release while it is switched off on this site. Tenders already started on it may continue.** When its integrity or renderer check fails: **This release cannot be used to publish a Tender.** (v0.10 read: **This release cannot be used to publish a Tender. Complete the release work listed under Verification.**) For Available show **This release may be used only for the supported procurements below.** Superseded and Withdrawn say respectively that existing published Tenders remain readable but new use is prohibited, and that new use is prohibited because the release was withdrawn.

Use these five sections:

1. **Overview**
   - **Supported use:** category, method, product scope, lot, currency, price treatment, related-service boundary and supported reservation treatments.
   - **Not supported:** a short structured list from §2.2, not one dense paragraph.
   - **Release:** template release, product profile, renderer profile and status.
   - **Official source:** title, source owner and retrieval date; source digest belongs only under Technical details.
2. **Tender content**
   - two output cards: **Invitation to Tender** and **Complete issued Tender**, each with section/form coverage summary and **Preview**;
   - one **Source coverage** summary with reviewed/total rows and forms accounted for;
   - three labelled summaries: **Inherited from the authorised Requisition**, **Entered during Tender preparation**, and **Generated by KenTender**;
   - **Download review pack** as the only download action.
3. **Bid response and downstream use**
   - five supplier tasks in their visible order, each with one-sentence purpose;
   - supported controls and compositions as labelled chips/summaries, not raw schema;
   - response-family counts and declaration/evidence/price treatment;
   - four evaluation groups, including the single shared Technical compliance group and Award group;
   - contract destinations and explicit **Not carried forward** treatment;
   - reservation declaration/evidence shown as eligibility pass/fail and Award/reporting context, never as Planning compliance or a contract obligation.
4. **Coverage and changes**
   - plain totals for source rows and forms by treatment: **Rendered**, **Structured input**, **Conditional**, **Excluded with reason**, and **Not applicable**;
   - **View coverage details** opens an in-page searchable, filterable table with source locator, title, treatment, output anchor and reason. It is a read-only inspection aid, not an editor;
   - every exclusion and conditional treatment remains visible and names its reason; counts alone never conceal an omitted source item;
   - **Changes from release {previous release}** summarises added, changed and removed documents, response rows, locked declarations, evaluation mappings, contract mappings, supported uses and renderer compatibility;
   - **View change details** opens the generated comparison grouped by change type and consequence. It must distinguish a compatible successor from a breaking product-family change and must not show a raw JSON diff.
5. **Verification**
   - one row each for **Official source**, **Tender documents**, **Supplier responses**, **Evaluation and contract mappings**, **Reservation variants**, **Addendum identity rules**, **MoH fixture** and a live **Site switch** row showing On or Off, who switched it and when (v0.11, OD5; v0.10 read: … **MoH fixture** and **Owner approval**; the Owner approval row is removed and any recorded owner decision appears under **Technical details**);
   - caption (v0.11, OD5): **These checks were recorded when this release was built. They are for information only; whether this site can use the release depends on its switch, its integrity and its renderer.**;
   - result values `Passed`, `Incomplete`, `Failed` or `Pending` plus one plain explanation (the **Site switch** row shows `On` or `Off`);
   - a blocker panel listing every current blocker and its owner. An empty blocker list is permitted only for Available. From v0.11 (OD5) blockers are derived live and are only: switched off on this site (owner: Site administrator); a missing registered renderer (owner: Site administrator); and a failed integrity check (owner: controlled template-release owner). Recorded gate results and open review items are shown in the rows above and are never blockers;
   - source verification shows **Last checked**, **Checked by** and **Outcome**;
   - **Report concern** is the only write action. It captures category, source locator or section, concise summary, description and optional evidence attachment against the installed release; it never edits, blocks, approves or withdraws the release automatically;
   - no repair control. The authorised next step names the controlled release owner, not a vague support contact. From v0.11 (OD5), a switched-off release or a missing renderer names the Site administrator instead (for a switched-off release: **Whoever manages this site can switch it on.**); an integrity failure still names the controlled release owner.

**Technical details**, collapsed by default, contains `release_id`, exact manifest identity, product/renderer identities, `supported_renderer_version`, constituent digests, repository commit and schema versions, and (v0.11, OD5) any recorded owner decision as evidence. Copy controls may be provided for identifiers and digests only inside this section.

### 11.4 Detail variants and interaction rules

- **Available:** v0.11 (OD5): lifecycle Available, switched On, integrity verified and renderer registered; blockers empty; the **Site switch** row shows On; the recorded verification rows show their recorded results, which may be Incomplete or Pending, as information; any recorded owner decision appears under **Technical details**. (v0.10 read: all verification rows Passed, blockers empty, exact manifest approval shown.) Preview and review-pack actions remain.
- **Unavailable:** v0.11 (OD5): switched Off, a failed integrity check or a missing renderer, each shown as a blocker with its owner; recorded results shown truthfully; no activation action. The site switch is a deployment command (§14.1), not a UI action, and **STD Templates** has no switch control. (v0.10 read: **Unavailable / Candidate:** truthful mixed results and complete blockers; no activation action.)
- **Failed verification:** (v0.11, OD5: a failed live integrity or renderer check; a Failed recorded review row alone is information, not a blocker) Failed row is first in the blocker panel; retain the last successful result separately and do not label the release merely Unavailable without the cause.
- **Superseded:** show successor release when supplied; state that new Tenders cannot bind it and that already-bound unpublished Tenders may continue only while integrity and renderer checks pass; existing published-Tender readability is stated.
- **Withdrawn:** show withdrawal reason, recorded time, actor and successor when supplied; state that new binding and publication of any already-bound unpublished Tender are blocked. Historical published outputs remain immutable and readable.
- **Filtered empty / installed empty / read failure:** preserve filters and route. A read failure states **STD Template details could not be loaded. Try again.** with **Try again** and **Back to STD Templates**; it never substitutes stale or guessed content.

**View**, section links, Back, Preview, Download review pack, View coverage details, View change details, Report concern, filter and Clear filters are the only common actions. Refresh/Back preserves filter and selected section. Keyboard order follows visible order; badges have text; at 200% zoom or 390 px the table becomes labelled cards without horizontal scrolling or omitted facts.

### 11.5 Closed release 1.1 design fixture

The design tool shall use this complete fixture and shall not derive facts from screenshots or the ZIP:

| Fact | Fixture value |
|---|---|
| Display name / key | IT Equipment Open Tender / `IT-EQUIPMENT-OPEN-V1` |
| Release / status | 1.1 / Unavailable — switched Off on the fixture site (v0.11, OD5) |
| Supported use | Goods · Open Tender · single lot · KES · fixed price · straightforward IT equipment |
| Reservation support | `None`, Youth, Women, Persons with disabilities; County residents is separate and conditional |
| Product / renderer | `GOODS-IT-SIMPLE-V1` / `BDS-GOODS-IT-V1` |
| Official source | PPRA Standard Tender Document for Procurement of Goods |
| Source coverage | 296 of 296 rows reviewed; 28 forms accounted for |
| Coverage treatments | Rendered 214; Structured input 39; Conditional 24; Excluded with reason 13; Not applicable 6; totals reconcile to 296 |
| Previous-release comparison | Compared with release 1.0; 18 response rows added, 4 declaration texts versioned, evaluation groups changed from 3 to 4, contract mappings added, renderer compatibility changed; classified **Breaking — not interchangeable with the preceding release** (v0.11, OD5; v0.10 read: **Breaking — new release approval required**) |
| Tender outputs | Invitation to Tender; Complete issued Tender |
| Supplier tasks | Tender documents and addenda; Company, declarations and tender security; Requirements and supporting evidence; Price; Review and submit |
| MoH structured content | 1 grouped Goods line from 2 Requisition items; 11 technical requirements; 6 warranty/support facts; 5 acceptance checks; 0 related services; 1 Goods price schedule |
| Evaluation groups | Eligibility; Technical compliance; Financial; Award |
| Contract treatment | Accepted Goods, delivery, technical, warranty/support, acceptance and awarded price carry forward; eligibility-only evidence and administrative acknowledgements do not |
| Verification | Official source Passed; Tender documents Passed; existing unreserved path Passed; Youth, Women, Persons-with-disabilities and County-residents variants Incomplete; coordinated supplier-response/mapping upgrade Incomplete; addendum identity Passed for the earlier candidate (v0.11, OD5: these recorded results are information only; v0.10 also listed: owner approval Pending, removed by OD5) |
| Site switch (v0.11, OD5) | Off |
| Switched by (v0.11, OD5) | Awaiting fixture |
| Switched at (v0.11, OD5) | Awaiting fixture |
| Blockers | v0.11 (OD5): **This release is switched off on this site.** Owner: Site administrator. (v0.10 read: Complete the four reserved/County variants and coordinated structured-definition upgrade; rerun the complete validator and manifest; obtain owner approval of the exact manifest. Under OD5 the first two are open review items shown in Verification, not blockers, and no owner approval is sought.) |
| Concern example | Category **Source treatment**; source locator **STD row 184**; summary **Confirm exclusion reason**; status **Open**; it does not change availability |
| Last verified | 21 September 2026, 17:30 EAT |

The fixture is intentionally Unavailable. It must not be altered to make a visually cleaner all-green screen. From v0.11 (OD5) it is Unavailable because the release is switched Off on the fixture site; its Incomplete recorded rows are information and are not the reason.

### 11.6 Ownership and security

`ListInstalledSTDReleases` and `GetInstalledSTDRelease` are template-owner reads. They return `InstalledSTDReleaseProjection v1`; CFG supplies no proxy and TPR/BDS supply no extra display facts. Administrator and System Manager have read-only access. Procurement Officer and Head of Procurement Function have the same inspection and concern-reporting access because they must understand the exact Tender format they use and govern; this does not grant template editing, activation, switching or broader technical access. The responsibility boundary is recorded in AUTH-ADR-001 v1.10. List/detail reads create no release, approval or audit business event beyond ordinary access logging.

The page may download immutable previews and the exact review pack returned by the owner. `CreateSTDTemplateConcern` creates only the lightweight concern record defined by STD-TPL-IMP-001 v1.0; authorised release owners resolve or link it to a successor release outside the inspection surface. The page has no edit, activate, switch, override, clause-builder, schema-builder, raw-schema-first, direct JSON-upload or repair action; the site switch is a deployment command, not a UI action (§14.1). From v0.11 (owner decision OD5), an intact release installs Available and switched On, and its availability then follows §14.1; no approval or commissioning step exists. (v0.10 read: A release becomes Available only through a reviewed software release whose exact manifest passes §14 and receives the §13.10 owner decision.) There is no second site-adoption approval.

## 12. Ministry of Health fixture

The release fixture is `TND-MOH-2027-033`, **Supply and delivery of business laptops**, sourced from the authorised MoH Requisition. Its reservation category is **Youth**; County-residents is **Not applicable** because the fixture Procuring Entity is not a county government.

It proves:

- two contributing Requisition items group into one 250 Each Goods line without losing lineage;
- eleven technical requirements;
- six warranty/support facts;
- five acceptance requirements;
- no related services;
- one currency and one Goods price schedule;
- manufacturer authorisation, datasheet, two comparable contracts over five years and after-sales evidence;
- one Youth reservation declaration and AGPO evidence response mapped to `EVG-ELIGIBILITY` and explicit non-contract treatment;
- separate Invitation and issued Tender outputs; and
- one deterministic Published Bid Definition whose response and downstream mappings reconcile with those outputs.

The fixture proves the Youth path. It does not prove Women, Persons with disabilities, County-residents, multiple lots, another currency, Works or complex IT; those reservation variants require isolated deterministic fixtures as recorded release evidence (§14.2 Reservation). From v0.11 (OD5) a missing or unreviewed variant fixture does not stop the release being Available; an unsupported treatment is still rejected as a compatibility outcome (§§2.2, 8.2). (v0.10 read: … require isolated deterministic fixtures before the release becomes Available.)

### 12.1 Current as-built candidate reconciliation

The existing `/07_tender_templates/it_equipment_open_v1` artefacts are a substantial candidate implementation, not unstarted work. They already contain the official source PDF/text and 103 page images; 296/296 coverage rows; 28 accounted forms; 80 insertion points; Invitation and complete-Tender masters and MoH fixtures; runtime product/response/downstream/addendum assets; a validator; review record; and a 127-file SHA-256 manifest. The packaged ZIP and current validator complete successfully for that earlier candidate definition.

**Correction (v0.11, follow-up FU-02).** The preceding paragraph is the v0.10 statement. It is wrong in part and is retained as history. When v0.10 was written, the pack held only `01_source` to `05_review`. The `06_runtime` assets (`product_profile.json`, `response_rules.json`, `downstream_rules.json`, `addendum_identity_rules.json`, `moh_published_bid_definition_expected.json` and `release_manifest.json`), the validator `validate_release.py`, `04_fixture/build_definition_fixture.py`, `04_fixture/reservation_variants/` and the review files `05_review/release_gates.json`, `05_review/release_change_report.json` and `05_review/validation_report.json` did not exist on the build machine or anywhere in the repository's git history. The packaged ZIP held 128 entries, none of them a manifest, a validator or a `06_runtime` asset, so no validator run for that candidate could have completed. These files were first built on 26 September 2026 during the STD-TPL-IMP-001 v1.0 build. They now exist under `docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1/`. `06_runtime/` holds seven files. `response_rules.json` holds 24 rules. `validate_release.py` implements 21 checks. The `01_source` to `05_review` folders did exist. Of the figures in the preceding paragraph, only the register counts were re-confirmed, on 25 September 2026: 296 coverage rows, 28 forms and 80 insertion points. The validator success referred to in the next paragraph therefore did not occur. Under OD5, whether release 1.1 can be used now follows §14.1.

That success does not make release 1.1 Available because the candidate predates the final coordinated contracts in this v0.9. Reconcile it as follows:

| Area | Existing candidate | Required before exact-manifest approval (v0.11, OD5: reconciliation work, no longer a condition of use) |
|---|---|---|
| Human Tender documents | Substantially complete and source-covered | Re-render and compare after any reservation/declaration or officer-field change. |
| Structured bidder layer | Present with product, response, downstream and addendum JSON | Upgrade to the exact `PublishedBidDefinition v1`, control vocabulary and four-group mapping contract in §§8–13. |
| Reservation | Existing review record supports the earlier `None` scope | Add and pass `None`, Youth, Women, Persons-with-disabilities, County-residents and unsupported-overlap fixtures required by this release; preserve Planning/eligibility separation. |
| Controls | Earlier finite Goods controls present | Add controlled multi-select and reviewed structured-ports composition where required by the authorised Requisition model. |
| Evaluation | Existing assets include the Award group | Make the four-group declaration and every mapping consistent; retain one shared Technical compliance group. |
| Manifest/inspection | 127-file manifest and review record present | Add the §13.9 release/projection fields, named constituent digests, summaries, blockers and exact owner-decision binding used by **STD Templates** (v0.11, OD5: a recorded owner decision is evidence only). |
| Approval | Review record remains Candidate/Unavailable | Run the complete revised validator, create a new exact manifest and (v0.10 only) obtain `APPROVE EXACT MANIFEST`. From v0.11 (OD5) that decision is not required; an intact release installs Available and switched On (§14.1). |

Do not discard or rebuild the candidate from scratch. Reuse verified source, coverage, forms, masters and fixture evidence; modify only the controlled assets affected by this contract, then rerun the complete deterministic release process.

## 13. Bundle construction procedure

This section is the authoritative procedure for creating release 1.1. It covers both projections of the product: the human-readable Tender documents and the machine-readable Published Bid Definition. A bundle is not constructed by copying the folder tree and filling files informally. Each phase produces named assets, runs deterministic checks and stops at a review gate.

Construction is curation and release engineering, not an operational KenTender workflow. The people who perform source, procurement/legal, supplier-experience and technical reviews are review responsibilities, not new system roles. This section authorises no DocType, route, migration, permission or production deployment.

**Review gates under owner decision OD5 (v0.11).** Gates A to E in this section and the §14.2 gates record review and check results as evidence. A Pending, Incomplete or Failed review result, an open review item and a missing owner decision never block installation or use of a release. Whether an installed release can be used depends only on its lifecycle, its site switch, its integrity and its renderer (§14.1).

### 13.1 Preconditions and working rules

Before editing an asset, record in `05_review/review_record.md`:

- the exact approved versions of REQ, CFG, KT-STD and the applicable statutory register;
- the exact proposed TPR and BDS consumer versions being reconciled;
- the selected PPRA source filename and retrieval URL;
- the repository commit used to construct the candidate; and
- the builder and review participants.

Work only in `docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1/`. Preserve the directory and filenames in §4. A proposed additional file, response type, evaluation group, contract destination, control or composition is first recorded in `open_issues.md`; it is not silently introduced.

Required tools are a SHA-256 utility, Poppler (`pdfinfo`, `pdftotext`, `pdftoppm`), Python 3, Jinja2 with `StrictUndefined`, the repository's approved HTML-to-PDF renderer and JSON Schema validation support. Tool versions are written to `validation_report.json`. Generated output must be reproducible from the controlled inputs; a local manual correction to generated HTML, PDF or JSON is prohibited.

### 13.2 Phase 1 — establish the official source

1. Obtain the exact PPRA Goods STD from the official source selected by the owner.
2. Save it byte-for-byte as `01_source/ppra_goods_std_official.pdf`.
3. Record title, family, printed revision/date or `Not stated in source`, original filename, official URL, retrieval time and SHA-256 in `source_record.md`.
4. Generate the layout-preserving text and page images from that same PDF:

   ```bash
   pdfinfo 01_source/ppra_goods_std_official.pdf
   sha256sum 01_source/ppra_goods_std_official.pdf
   pdftotext -layout 01_source/ppra_goods_std_official.pdf 01_source/ppra_goods_std_official.txt
   pdftoppm -png -r 150 01_source/ppra_goods_std_official.pdf 01_source/pages/page
   ```

5. Compare the PDF, extracted text and page images. Record every unreadable, missing, blank or damaged page as a blocker in `open_issues.md`; do not reconstruct legal wording from memory or another procuring entity's Tender.

**Gate A — source confirmation.** Stop until the owner confirms the official file and digest and the procurement/legal reviewer confirms it is the applicable source family.

### 13.3 Phase 2 — account for the complete source

Create `coverage_register.csv` with exactly these columns:

```text
coverage_id,source_page_start,source_page_end,section_number,heading,item_type,treatment,owner_key,human_render_location,structured_rule_id,readiness_check,status,review_note
```

Add one row for every cover or notice block, numbered heading, subheading, table, form, selectable alternative, blank and instruction to insert, select, delete or amend content. `treatment` is exactly one of:

- `Locked`;
- `Inherited`;
- `Officer value`;
- `Generated`;
- `Supplier response`;
- `Award-derived`;
- `Contract-derived`; or
- `Not used by this released pattern`.

`Not used` requires the source basis and reviewer decision. Every Supplier-response row has a `structured_rule_id`; every rendered row has a human render location. No row may remain unclassified, point to both outputs ambiguously or rely on a future implementer to decide its treatment.

Create `insertion_points.csv` with exactly these columns:

```text
key,kind,source_treatment,source_section,owner,task,label,data_type,required,condition,validation,example,human_render_location,structured_use,downstream_use
```

`kind` is `value`, `condition`, `goods_rows`, `service_rows` or another repeated structure explicitly approved in this document. One fact appearing several times has one key. A blank in the official document does not automatically become an Officer field.

Create `forms_register.csv` with exactly these columns:

```text
form_id,official_form_name,source_pages,included,variant_selected,fixed_text_complete,prefilled_keys,supplier_fields,award_fields,contract_fields,response_rule_ids,review_status,review_note
```

**Gate B — complete treatment.** Stop until every coverage, insertion and form row is reviewed, every proposed exclusion is justified and the finite Officer decisions still match §6.2.

### 13.4 Phase 3 — build the human-readable masters

Build `invitation_to_tender.html` only from coverage rows assigned to the public notice. Build `complete_tender.html` from the cover, contents and Sections I–VIII assigned to the issued Tender. The Invitation must not be embedded in or listed by the issued Tender.

Rules:

- preserve official section order, numbering, headings, tables, forms and locked wording;
- use semantic UTF-8 HTML and `print.css` for shared print layout;
- use only insertion keys and named conditions recorded in the registers;
- use Jinja with auto-escaping and `StrictUndefined`;
- permit no database calls, permissions, calculations, custom executable filters or JavaScript in the masters;
- render structured schedules from the authorised Requisition and approved Tender decisions;
- remove document-preparer instructions only after their required treatment is accounted for; and
- retain supplier-facing instructions, declarations and forms at the correct stage.

The response-definition assets may repeat locked declaration text only where the electronic supplier must affirm it. Such a rule records the official source locator and a normalized source-text digest. The validator must prove that the electronic text and the corresponding human-readable anchored text are identical; they are not maintained as independent wording.

`render_fixture.py` is curation-only tooling. It reads `moh_input.json`, loads both masters with Jinja auto-escaping and `StrictUndefined`, writes only `moh_invitation_expected.html` and `moh_expected.html`, and fails on an unknown or missing value. It is run as:

```bash
python 04_fixture/render_fixture.py --input 04_fixture/moh_input.json --output-dir 04_fixture
```

Render the fixture PDFs through the registered adapter for `renderer_profile_id` and `supported_renderer_version`:

```bash
python 04_fixture/render_fixture.py --input 04_fixture/moh_input.json \
  --output-dir 04_fixture --renderer-profile BDS-GOODS-IT-V1 --write-pdf
```

The adapter pins the concrete engine and version in the release evidence. The release contract does not hard-code one vendor executable. Replacing an engine requires a new adapter version, exact visual/text regression evidence and a new manifest; an unreviewed local renderer is Blocking.

Search resolved HTML for unresolved Jinja, insertion prompts, selection instructions and drafting placeholders. An unexplained match is Blocking. `render_fixture.py` is never imported or installed by KenTender.

**Gate C — document projection.** Stop until the procurement/legal reviewer confirms source coverage, the two-output boundary, complete operative content and the MoH document fixture.

### 13.5 Phase 4 — create the runtime asset envelope

Every JSON asset in `06_runtime` is UTF-8, contains no comments, uses sorted object keys in canonical output and starts with:

| Key | Required value |
|---|---|
| `schema_version` | Positive integer fixed by this release; initial value `1` |
| `release_id` | Opaque candidate/installed release identity used consistently by every asset and later manifest |
| `template_key` | `IT-EQUIPMENT-OPEN-V1` |
| `template_release` | `1.1` |
| `product_profile_id` | `GOODS-IT-SIMPLE-V1` |
| `renderer_profile_id` | `BDS-GOODS-IT-V1` |
| `supported_renderer_version` | Exact released runtime renderer version accepted by this bundle |

Unknown top-level keys, duplicate identifiers, executable expressions, arbitrary nesting and references to an unregistered control, composition, validation, evaluation group or contract destination are Blocking. JSON order never supplies business meaning.

#### 13.5.1 `product_profile.json`

The profile defines the finite product vocabulary, not Tender-specific answers. It contains:

| Collection | Required row content |
|---|---|
| `supported_use` / `rejected_use` | Deterministic category, method, product, lot, currency, price, related-service and reservation boundaries from §2 |
| `tasks` | Stable `task_id`, order, label and purpose for the five §8.1 supplier tasks |
| `controls` | Stable control ID, value type, supported parameters and accessible rendering contract, including controlled multi-select and the reviewed structured-ports composition required by the authorised IT requirement model |
| `compositions` | Stable composition ID, permitted child controls, task placement and repetition rule |
| `validations` | Stable named validation ID and bounded parameter schema; no executable expression |
| `evaluation_groups` | Exactly `EVG-ELIGIBILITY`, `EVG-TECHNICAL-COMPLIANCE`, `EVG-FINANCIAL` and `EVG-AWARD`, with their fixed purpose |
| `contract_destinations` | Finite destinations in §9.2 plus explicit `Not carried forward` |

The profile does not contain a general-purpose form builder, field layout coordinates or another product family's controls merely because the renderer could display them.

#### 13.5.2 `response_rules.json`

This file describes how an authorised source fact creates supplier-visible responses. Each rule contains:

```text
rule_id,source_family,source_selector,identity_suffix,task_id,composition_id,field_definitions,applicability,document_anchor,evaluation_mapping_id,contract_mapping_id
```

`source_family` is one of `document`, `supplier`, `declaration`, `tender_security`, `goods`, `technical_requirement`, `warranty_support`, `experience`, `related_service`, `acceptance_requirement`, `evidence_requirement`, `reservation`, `county_residents` or `price_row`.

Each `field_definition` contains:

```text
field_key,label,control_id,required_rule,visibility_rule,validation_id,validation_parameters,evidence_rule,help_text
```

Required and visibility rules reference only named, bounded rules in the product profile. A locked declaration also records `locked_text`, `source_locator`, `source_text_digest` and `text_version`. Evidence rules state permitted evidence type, cardinality, linkage target and whether evidence is mandatory. A rule cannot introduce an obligation absent from the coverage and forms registers.

#### 13.5.3 `downstream_rules.json`

Every response rule points to exactly one mapping row containing:

```text
mapping_id,response_rule_id,evaluation_treatment,evaluation_group_id,evaluation_result_rule,contract_treatment,contract_destination,award_reporting_treatment,reason
```

`evaluation_treatment` is `Evaluated` or `Not evaluated`. `contract_treatment` is `Carried forward` or `Not carried forward`. A null group or destination is valid only with the corresponding explicit negative treatment and reason. No response becomes a hidden evaluation criterion, and no supplied free text becomes a contract term merely because it exists.

Mandatory technical, warranty, support and related-service checks map individually to `EVG-TECHNICAL-COMPLIANCE`; the group produces one pass/fail outcome while retaining each failed check and reason. No weight, criterion-builder metadata or score is permitted.

#### 13.5.4 `addendum_identity_rules.json`

This file defines the allowed classifications `unchanged`, `converted`, `fresh_response_required`, `removed` and `new`. Each rule states the exact identity type, the comparison basis, whether a prior answer can copy, the permitted conversion identifier where applicable, the affected task and the bidder notice. Text similarity, row order, display label and client-provided identity are prohibited comparison bases.

### 13.6 Stable identity contract

Bundle-authored identifiers such as task, composition, response-rule, mapping, evaluation-group and contract-destination IDs are explicit stable strings and cannot be renumbered for presentation. Tender-instance response identity is derived from:

```text
published_tender_version_id + source_family + immutable_source_id + rule_id + field_key
```

The Published Bid Definition stores all five components. An implementation may additionally encode or hash that canonical tuple, but it must preserve the tuple, prove uniqueness and reproduce the same identity for the same immutable Tender Version. Labels, translations, row positions and display grouping never form identity.

One source may legitimately generate several fields, but every field has a distinct `field_key`. A grouped goods schedule retains every contributing Requisition item and source allocation beneath the published goods identity. The validator rejects duplicate tuples, orphan source IDs and one identity mapped to incompatible response types.

Goods may group only when category, approved specification-set identity, unit, delivery location, latest delivery date, warranty/support treatment, reservation/County treatment, lot and currency are identical. Sort contributing `requisition_item_id` values bytewise. The canonical group identity is:

```text
goods_group_id = "GDS-" + first_24_hex(
  SHA-256(template_key + "\u0000" + tender_version_id + "\u0000" +
  canonical_grouping_key + "\u0000" + joined_sorted_requisition_item_ids)
)
```

`canonical_grouping_key` is canonical JSON containing the exact grouping fields above with sorted keys and no insignificant whitespace. Quantity is summed using exact decimal strings and is not part of identity; changing a contributing item or any grouping field creates a new identity and requires an explicit addendum migration classification. The complete ordered contributing-item and source-allocation lists remain in `source_lineage`.

### 13.7 Phase 5 — build the deterministic fixtures

`moh_input.json` contains the complete authorised Requisition projection, Tender decisions, exact rule snapshots, document identities and expected renderer profile. It is the only input used to generate the MoH human outputs and structured output. Fixture-only facts are prohibited.

`CompilePublishedBidDefinition` is one deterministic, side-effect-free compiler owned by the template runtime. It reads an authorised input projection plus `product_profile.json`, `response_rules.json`, `downstream_rules.json` and `addendum_identity_rules.json`. The curation command `build_definition_fixture.py` is a thin adapter over that same compiler contract and writes the complete expected Published Bid Definition. Run:

```bash
python 04_fixture/build_definition_fixture.py \
  --input 04_fixture/moh_input.json \
  --runtime-dir 06_runtime \
  --output 06_runtime/moh_published_bid_definition_expected.json
```

The compiler contains no Frappe queries, user data lookup, hidden default or duplicated policy decision. It fails on an unmatched source, unknown rule, orphan mapping or unsupported control. The CLI adapter is never called in production; the compiler implementation and canonical test vectors are shared. A second fixture-only algorithm is prohibited.

Generate `moh_published_bid_definition_expected.json` as the fixture for the exact `PublishedBidDefinition v1` contract. Its top-level fields are:

```text
bid_definition_id,definition_version,tender_id,tender_version_id,publication_id,
effective_addendum_ids,submission_deadline,template_family,template_release_id,
product_profile_id,renderer_profile_id,supported_renderer_version,package_digest,
official_source_digest,bundle_digest,response_rules_digest,downstream_rules_digest,
addendum_identity_rules_digest,sections,response_rows,price_rows,declaration_texts,
reservation_treatment,evaluation_mappings,contract_mappings,definition_digest
```

`template_family` equals `template_key`; it is retained only because it is the published cross-module field name. `template_release_id` is the opaque installed `release_id`, not the display value `1.1`. `sections` contains the finite ordered tasks/groups. Every `response_rows` entry includes its stable five-part identity tuple, task, group/composition, fields, applicability, requiredness, validation, evidence treatment, source lineage and mapping references. `price_rows` contains stable published rows and calculation definitions. `declaration_texts` contains exact locked text identities and versions. Published facts are read-only. `definition_digest` binds the canonical completed object excluding that digest field itself. Calculated totals are definitions, not Procurement Officer-entered values.

The production `BuildPublishedBidDefinition` service calls `CompilePublishedBidDefinition` at the Tenders/template-runtime boundary. For original publication authorisation it applies the exact released assets to the approved `TenderVersion`, `publication_id` and effective addenda and freezes the complete definition in the `TenderPublication` transaction without mutating the approved Version. For addendum issue it applies them to the current effective definition plus the proposed immutable addendum, freezing a successor that becomes bidder-effective only on final required-channel confirmation. CI must prove byte-equivalent canonical JSON from the CLI adapter and production service for identical inputs.

Generate the five isolated reservation fixtures in `04_fixture/reservation_variants/`:

- `None` — no category declaration or category evidence;
- `Women` — exact category clause, declaration, evidence and eligibility mapping;
- `Persons with disabilities` — exact category clause, declaration, evidence and eligibility mapping;
- `County residents` — separate county restriction, rule evidence and explicit overlap treatment; and
- unsupported overlap — deterministic Blocking result and no publishable definition.

Each `*_expected.json` states expected document anchors, response rules, evidence requirements, eligibility mappings, award/reporting treatment and expected pass/fail construction result. These fixtures do not assert supplier eligibility.

Create at least these addendum fixtures within the validator:

1. label-only change with unchanged identity — response retained;
2. material requirement change — fresh response required;
3. removed requirement — prior response remains historical and is absent from the current definition; and
4. new mandatory requirement — current task becomes incomplete.

**Gate D — structured projection.** Stop until the supplier-experience reviewer can complete the five tasks from the generated definition, and the procurement/legal reviewer confirms that every electronic obligation and declaration exists in the issued Tender.

### 13.8 Phase 6 — implement and run `validate_release.py`

The validator is curation tooling and is not imported by the KenTender runtime. It accepts only:

```bash
python 06_runtime/validate_release.py --root . --write-report 05_review/validation_report.json
```

It exits `0` only when every required check passes, exits non-zero for any Blocking failure and writes a deterministic report with check ID, result, affected asset and message. It also writes `05_review/release_gates.json`: one row per §14.2 gate with `gate_id`, `result`, `evidence_refs`, `checked_by`, `checked_at` and `message`. Result is exactly `Passed`, `Failed` or `Pending`; a missing row is `Pending`. It must validate at least:

1. required path inventory and absence of unapproved assets;
2. source, schema and release identities;
3. complete coverage/form/insertion classifications;
4. Jinja key use, strict fixture rendering and unresolved authoring text;
5. Invitation/issued-Tender separation and shared-value equality;
6. unique stable IDs and response identity tuples;
7. supported controls, compositions, validations and renderer profile;
8. one mapping for every response rule and no orphan mapping;
9. valid evaluation group and explicit evaluated/not-evaluated treatment;
10. valid contract destination and explicit carried/not-carried treatment;
11. response/document obligation and locked-text reconciliation;
12. goods, service, evidence and price-schedule lineage/reconciliation;
13. reservation and County variants, including unsupported overlap failure;
14. addendum identity and migration fixtures;
15. exact reproduction of all MoH expected HTML and JSON outputs;
16. PDF existence, readable text, required sections and document anchors;
17. review blockers and mandatory reviewer decisions (v0.11, OD5: checks that they are recorded consistently; a Pending review, an open review item or a missing owner decision is not a Blocking failure); and
18. constituent SHA-256 values and the candidate bundle digest;
19. complete structured gate rows, evidence references and source-check facts;
20. exact compiler parity between fixture and production test vectors; and
21. generation and internal consistency of the preceding-release change report.

A warning cannot substitute for a failed mandatory check. The report contains no production supplier or secret data.

### 13.9 Phase 7 — create the release manifest

After a clean validator run, create `release_manifest.json` with:

```text
schema_version,release_id,template_key,template_release,display_name,product_profile_id,
renderer_profile_id,supported_renderer_version,status,supported_use,rejected_use,
official_source_title,official_source_digest,source_retrieved_at,repository_commit,
tool_versions,assets,document_summary,response_summary,evaluation_summary,
contract_summary,reservation_support,verification_results,blockers,
source_checked_by,source_checked_at,source_check_outcome,release_gates_digest,
release_change_report_digest,validation_report_digest,bundle_digest,built_by,built_at
```

The manifest also exposes the constituent `response_rules_digest`, `downstream_rules_digest` and `addendum_identity_rules_digest` as named values calculated from their asset rows. `status` is `Candidate` in the constructed manifest; installation binds the later owner decision and derives `Available`, `Superseded` or `Withdrawn` without rewriting the approved asset bytes (v0.10; superseded by owner decision OD5, see the next paragraph). Summaries are structured, versioned projections used by **STD Templates**; they do not replace the controlled assets or become editable UI metadata.

**Manifest `status` under OD5 (v0.11).** The constructed manifest still writes `status` as `Candidate`, for format stability only. The value is evidence, not a lifecycle state, and installation does not read it to decide availability. An intact release (§14.1) installs with lifecycle `Available` and its site switch On, or Off when the deployment asks for Off. It later becomes `Superseded` or `Withdrawn` only through the lifecycle operations, still without rewriting asset bytes. An owner decision is optional. When one is present it must name the exact template release, bundle digest and manifest-file digest; a decision naming other bytes fails installation as an integrity error. A decision that matches is recorded as evidence only. Dropping or renaming the `status` field is left to a later manifest format change.

`assets` lists every controlled relative path and SHA-256 in bytewise path order. It excludes `release_manifest.json` itself and transient cache/log files. `bundle_digest` is SHA-256 over the UTF-8 sequence of each sorted relative path, a null byte, its lowercase asset digest and a newline. The review record stores both the resulting bundle digest and the separately calculated SHA-256 of the completed manifest file, avoiding a self-referential digest.

Any controlled byte change after manifest creation invalidates the candidate. Rebuild the affected outputs, rerun the complete validator, issue a new manifest and obtain a new owner decision (v0.10; from v0.11, OD5, no owner decision is required, and a recorded decision never carries over to different bytes). Do not patch a manifest or reuse its approval for different bytes.

Generate `05_review/release_change_report.json` by comparing this candidate with the exact preceding approved release (v0.11, OD5: the exact preceding release, whether or not an approval was recorded for it). It lists each added, changed or removed asset, source treatment, document anchor, response rule, declaration, evaluation mapping, contract mapping, supported-use boundary and renderer compatibility statement. Each change carries `change_kind`, stable identity, plain summary and `compatibility_effect`. The overall result is exactly `Compatible successor`, `Breaking — not interchangeable with the preceding release`, or `First release` (v0.11, OD5; v0.10 read: `Compatible successor`, `Breaking — new release approval required`, or `First release`). A human-readable projection is shown in **Coverage and changes**; neither the builder nor an administrator writes the report manually.

### 13.10 Phase 8 — review and owner decision

Complete `review_record.md` with named results for:

- official source and legal wording;
- full source coverage and forms;
- product applicability and reservation variants;
- human document projection;
- supplier tasks and field usability;
- evaluation and contract mappings;
- addendum identity behaviour;
- MoH and isolated fixture reproduction;
- validator report, source digest, bundle digest and manifest-file digest; and
- unresolved blockers.

The reviewer also confirms every structured gate row and the generated change report. A gate cannot pass solely because prose in `review_record.md` sounds favourable.

(v0.10; superseded by owner decision OD5 as stated below.) The permitted decision is `APPROVE EXACT MANIFEST`, `CORRECT AND RE-REVIEW` or `REJECT PRODUCT RELEASE`. Approval names the exact template release, bundle digest and manifest-file digest. Document approval without that exact decision leaves release 1.1 `Candidate` and `Unavailable`.

**Gate E — exact release approval.** (v0.10; superseded by owner decision OD5 as stated below.) Stop. No installation or production use is authorised until the owner approves the exact manifest.

**Review and owner decision under OD5 (v0.11).** The Project Owner decided on 26 September 2026 (OD5): "I don't want this complicated admin overhead regarding approvals and commissioning of templates. It is unnecessary, adds no value and is vexing. Allow development work to contine without this friction. Template release is purely an on and off switch on an affected site. Update this decision as a follow up to reflect in affected documents if necessary". Accordingly, the review record, the structured gate rows, the Gate D and Gate E reviews and any owner decision are recorded evidence. None of them blocks installation or use, and Gate E no longer stops installation or production use. A reviewer or the owner may still record one of the decision values above. A recorded decision must name the exact template release, bundle digest and manifest-file digest (§13.9) and is shown under **Technical details**. To stop use of a release, it is switched Off or withdrawn (§14.1).

### 13.11 Handoff to implementation

STD-TPL-IMP-001 v1.0 is the implementation authority for the installed-release registry, immutable asset storage, shared compiler, renderer adapters, inspection projections, concern capture and release lifecycle operations. It may package only exact owner-approved assets (v0.10; from v0.11, OD5, the exact assets named by the verified manifest, with no owner approval required) and must verify their manifest transactionally during installation. It cannot regenerate official wording, add response fields, change mappings or relax a gate. The obsolete v0.2 is historical only.

## 14. Release lifecycle and gates

### 14.1 Status

| Status | Meaning |
|---|---|
| Candidate | Pack may be reviewed but cannot be selected for publication. Retired by owner decision OD5 in v0.11: no installed release is Candidate, and the constructed manifest `status` value is evidence only (§13.9). |
| Available | v0.11 (OD5): installed intact with the exact bundle digest; usable for new Tenders while its site switch is On. (v0.10 read: Owner approved; all gates pass; exact bundle digest installed.) |
| Superseded | A non-safety successor exists. New Tenders cannot bind it; already-bound unpublished Tenders may continue only while release integrity and renderer compatibility still pass. Published Tenders retain it. |
| Withdrawn | A safety or legal defect prohibits new binding and blocks publication of every already-bound unpublished Tender. Published Tenders remain immutable and readable for the record. |

Document approval alone does not make a candidate bundle Available. The review record must approve the exact bundle digest. (v0.10; the second sentence is superseded by OD5, see **Site switch** below. Document approval still does not install or switch on a release.)

**Availability projection (v0.10; superseded by OD5, see the v0.11 projection below).** `Unavailable` is the plain-language administrative UI result for a `Candidate` release or any release that cannot be selected because a mandatory gate, verification result, installation fact or exact owner decision is missing/failed. It is not a fifth lifecycle value and is never written into the controlled manifest `status`. `Available`, `Superseded` and `Withdrawn` project directly from their lifecycle values.

**Site switch (v0.11, owner decision OD5).** A template release is an On/Off switch on a site. An intact release installs with lifecycle `Available` and its site switch On; the deployment may install it switched Off instead. A release is intact when its manifest, every asset and every digest verify (§13.9) and its validation report records no Failed check (§13.8). Any integrity failure installs nothing. The switch is changed only by a deployment command (as built: `make std-release-switch SITE=<site> STATE=On|Off`); it is not a Desk or **STD Templates** action. Each change records the actor, the time and the new state in the release's audit history as **Switched On** or **Switched Off**. The switch can be changed only while the lifecycle is `Available`; a `Superseded` or `Withdrawn` release keeps its lifecycle rules above. The switch governs new binding only: a new Tender may bind a release only while it is `Available` and switched On. The switch does not change the lifecycle, so a Tender already bound continues under the lifecycle rules above whatever the switch state; switching Off never rebinds or strands it. Recorded gate results, review items and any owner decision are evidence and never block installation or use.

**Availability projection (v0.11, OD5).** **STD Templates** shows `Available` only when the lifecycle is `Available`, the site switch is On, integrity is verified and the registered renderer for `renderer_profile_id` and `supported_renderer_version` is present. Otherwise a lifecycle-`Available` release shows `Unavailable`, with each cause as a blocker: switched off on this site, a failed integrity check or a missing renderer. `Superseded` and `Withdrawn` show as themselves. `Unavailable` is still not a lifecycle value and is never written into the manifest.

No lifecycle change automatically rebinds a Tender. Withdrawal records reason, time, actor, optional successor and the affected-Tender projection. Each affected unpublished Tender must follow the Tender-governed outcome: cancel and start a new Tender, or use an explicitly authorised correction route if TPR permits it. KenTender does not silently substitute the successor release. A published Tender continues to show its exact historical release and withdrawal notice without rewriting its published documents or Bid definition.

### 14.2 Mandatory gates

| Gate | Required proof |
|---|---|
| Source | Exact official source, record, pages and digest |
| Applicability | Supported and rejected uses are deterministic |
| Reservation | Every supported reservation category and County-residents overlay has exact document wording, bidder responses, evidence rules, eligibility mapping, award/reporting disposition and isolated fixture coverage; no designation is treated as entitlement |
| Coverage | Every source row and form has an approved treatment |
| Documents | Invitation and issued Tender render completely and reconcile |
| Data ownership | Inherited facts cannot be re-entered; officer decisions are finite |
| Responses | Every bidder-editable field has identity, purpose, type and validation |
| Evaluation | Every evaluated response maps to one published group; no hidden criterion |
| Contract | Every applicable accepted response maps to an obligation or explicit N/A |
| Addenda | Identity migration is deterministic and safe |
| Renderer | Every control/composition/rule is supported by the exact renderer profile |
| Fixture | Document and structured MoH outputs reproduce and reconcile |
| Usability | Officer and supplier journeys pass representative-user review |
| Inspection | Administrator, System Manager, Procurement Officer and Head of Procurement Function can see installed content, coverage, changes, mappings, evidence and blockers through **STD Templates** |
| Compiler parity | Fixture and production paths invoke one deterministic compiler and reproduce the canonical vectors exactly |
| Change control | Generated preceding-release comparison is complete and its compatibility result is reviewed |
| Integrity | Source, assets, outputs and bundle have immutable digests |

(v0.10; superseded by OD5.) Any failed gate prevents `Available` and projects the release as `Unavailable` in **STD Templates**; there is no warning-only or staff override path. From v0.11 (OD5) a gate row's recorded result, whether Passed, Pending or Failed, is evidence shown in **Verification**; it never prevents `Available` or use. Only the live conditions in §14.1 make a release `Unavailable`, and there is no staff override of a failed integrity or renderer check.

## 15. Acceptance contract

| ID | Acceptance criterion |
|---|---|
| TPL07-AC-001 | Release 1.1 accepts only the product boundary in §2. |
| TPL07-AC-002 | `None`, Youth, Women and Persons with disabilities are supported; any other category is rejected before Tender creation unless a later approved release explicitly adds it. |
| TPL07-AC-003 | All goods, service, technical, warranty and acceptance facts are inherited from the authorised Requisition. |
| TPL07-AC-004 | The Procurement Officer cannot edit an inherited or generated fact. |
| TPL07-AC-005 | Separate Invitation and issued Tender outputs use one Tender Version and reconcile. |
| TPL07-AC-006 | The electronic workspace is generated from the released structured definition, never by parsing a PDF. |
| TPL07-AC-007 | Every bidder field has a stable identity, visible purpose, validation and downstream disposition. |
| TPL07-AC-008 | All mandatory technical checks feed one Technical compliance gate without weighted scoring or a criterion builder. |
| TPL07-AC-009 | Every applicable accepted response maps to a contract obligation or explicit N/A. |
| TPL07-AC-010 | Unknown response types, compositions, rules or renderer versions block publication and Bid start. |
| TPL07-AC-011 | Addenda preserve or deliberately replace stable identities; labels and positions never migrate responses. |
| TPL07-AC-012 | The MoH document and Published Bid Definition fixtures reproduce deterministically. |
| TPL07-AC-013 | The installed bundle digest and all constituent digests match the approved review record. Amended in v0.11 by TPL11-AC-006 (OD5): the review record need not record an approval. |
| TPL07-AC-014 | Administrator, System Manager, Procurement Officer and Head of Procurement Function can inspect the exact installed release through **STD Templates** without being able to edit or override it. |
| TPL07-AC-015 | A candidate or failed release is visible as Unavailable and cannot be used to publish a Tender. Superseded in v0.11 by TPL11-AC-003 (OD5). |
| TPL07-AC-016 | County-residents is evaluated as a separate inherited restriction, available only for an applicable county Procuring Entity with a verified effective rule and explicit overlap treatment. |
| TPL07-AC-017 | Every supported reserved Tender publishes the exact declaration and evidence requirements, maps them to pass/fail eligibility and preserves category/result for governed award and statutory reporting without making the supplier Account appear prequalified. |
| TPL08-AC-001 | The complete bundle can be constructed from §13 without consulting v0.6, the retired implementation pack or an undocumented convention. |
| TPL08-AC-002 | Coverage, insertion and forms registers use the exact schemas and controlled treatment values in §13.3; every official source item has one reviewed treatment. |
| TPL08-AC-003 | Every runtime JSON asset carries the exact release envelope, rejects unknown vocabulary and contains no executable expression or arbitrary schema. |
| TPL08-AC-004 | `product_profile.json` defines only the supported product boundary, five tasks and finite renderer vocabulary; it is not a general form builder. |
| TPL08-AC-005 | Every `response_rules.json` row identifies its source, stable rule, task, composition, fields, validations, evidence, document anchor and downstream mappings. |
| TPL08-AC-006 | Every response rule has exactly one explicit evaluation treatment and one explicit contract treatment; negative treatment requires a reason and no orphan mapping exists. |
| TPL08-AC-007 | Instance response identity preserves Tender Version, source family, immutable source identity, rule and field key; labels and positions cannot change identity. |
| TPL08-AC-008 | The same `moh_input.json` generates both human outputs and the expected Published Bid Definition; fixture-only obligations or manual output correction fail validation. |
| TPL08-AC-009 | Isolated deterministic fixtures prove `None`, Women, Persons with disabilities, County-residents and an unsupported overlap, in addition to the MoH Youth path. |
| TPL08-AC-010 | `validate_release.py` implements every mandatory check in §13.8, writes a deterministic report and exits non-zero for any Blocking result. |
| TPL08-AC-011 | The release manifest inventories every controlled asset and calculates constituent, validation-report and bundle digests by the exact §13.9 algorithm without self-reference. |
| TPL08-AC-012 | Any controlled byte change after manifest creation invalidates the candidate and requires complete regeneration, validation and owner re-approval. Amended in v0.11 by TPL11-AC-006 (OD5): owner re-approval is no longer required. |
| TPL08-AC-013 | The owner decision binds the exact template release, bundle digest and manifest-file digest; document approval alone cannot make the release Available. Superseded in v0.11 by TPL11-AC-001 and TPL11-AC-006 (OD5). |
| TPL08-AC-014 | A later Frappe implementation consumes and verifies the exact approved assets (v0.11, OD5: the exact assets named by the verified manifest); it cannot regenerate wording, add fields, change mappings or relax a release gate. |
| TPL08-AC-015 | Active references use REQ v1.12, identify TPR v0.11 and BDS v0.7 as coordinated proposed consumers, use CFG v0.16 only for site configuration, effective-rule and public-portal-information ownership, and use STD-TPL-IMP-001 v1.0 as implementation authority. |
| TPL08-AC-016 | `PublishedBidDefinition v1` uses the exact top-level field names in §13.7 and is materialised atomically with publication authorisation; the fixture builder and production builder produce semantically identical output from the same controlled inputs. |
| TPL08-AC-017 | Controlled multi-select and structured ports requirements from the authorised Requisition render without loss, unsupported fallback or free-text flattening. |
| TPL08-AC-018 | Exactly four evaluation groups exist: Eligibility, Technical compliance, Financial and Award; every response mapping names one group or an explicit not-evaluated disposition. |
| TPL08-AC-019 | `InstalledSTDReleaseProjection v1` supplies every §11 list/detail fact, state and blocker; the browser does not parse the bundle, PDF, filename or raw manifest to fill a gap. |
| TPL08-AC-020 | The **STD Templates** list/detail artboards can be produced from KT-STD-001 v1.8 §2 plus §11 alone and pass desktop, keyboard, 200% zoom and 390 px checks. |
| TPL08-AC-021 | One closed round-trip fixture proves authorised Requisition → Tender Version → Invitation/issued Tender/Published Bid Definition → five-task Bid Workspace → submitted response identities → evaluation and contract mappings without re-keying or hidden obligations. |
| TPL08-AC-022 | `Unavailable` is only the administrative availability projection of a Candidate/blocked release; the controlled lifecycle and manifest continue to use exactly `Candidate`, `Available`, `Superseded` and `Withdrawn`. Superseded in v0.11 by TPL11-AC-003 (OD5): the lifecycle is `Available`, `Superseded` and `Withdrawn`, and the manifest `status` field still carries the constructed value `Candidate` as evidence only. |
| TPL08-AC-023 | Original publication records definition identity/digests on `TenderPublication` without mutating the approved Tender Version; addendum issue freezes a complete successor definition that becomes effective only with final required-channel confirmation. |
| TPL09-AC-001 | The bundle contains no candidate-registration, supplier-question, notice-audience, notice-delivery or public-portal-support configuration schema; each is obtained from its named owner. |
| TPL09-AC-002 | A non-changing clarification answer and its notice evidence do not change a bundle digest or Published Bid Definition; a published-content change requires an issued addendum and the released identity rules. |
| TPL09-AC-003 | Active dependency and owner-boundary checks use TPR v0.11, BDS v0.7 and CFG v0.16 without importing their operational records into the controlled bundle. |
| TPL10-AC-001 | **Coverage and changes** exposes reconciled treatment totals, every conditional/excluded source row and the generated preceding-release comparison without raw JSON. |
| TPL10-AC-002 | **Report concern** creates a bounded concern against the exact installed release and cannot edit, approve, block, supersede or withdraw it. |
| TPL10-AC-003 | `release_gates.json` contains every mandatory gate and evidence reference; a missing, Failed or Pending row prevents Available. Amended in v0.11 by TPL11-AC-004 (OD5): a Failed or Pending row is recorded evidence and does not prevent Available. |
| TPL10-AC-004 | Fixture and production construction use one `CompilePublishedBidDefinition` implementation and reproduce identical canonical output for identical inputs. |
| TPL10-AC-005 | PDF generation uses a registered, versioned renderer adapter; changing the concrete engine invalidates the manifest and requires full regression evidence. |
| TPL10-AC-006 | A Superseded release cannot bind a new Tender but an already-bound unpublished Tender may continue only after integrity and renderer checks pass. |
| TPL10-AC-007 | A Withdrawn release cannot bind a new Tender and blocks publication of every already-bound unpublished Tender; no Tender is automatically rebound. |
| TPL10-AC-008 | Published Tenders retain their exact release, documents and Bid definition after supersession or withdrawal and remain readable with the lifecycle notice. |
| TPL10-AC-009 | Release installation has one exact-manifest owner approval and no duplicate site-adoption approval. Superseded in v0.11 by TPL11-AC-001 (OD5): installation needs no owner approval of any kind. |
| TPL10-AC-010 | STD-TPL-IMP-001 v1.0 supplies the records, services, permissions, deployment and test authority needed to implement this contract without runtime template authoring. |
| TPL11-AC-001 | An intact release installs with lifecycle `Available` and its site switch On, or Off when the deployment asks for Off; any integrity failure installs nothing; no Candidate lifecycle state, approval or commissioning step exists before use. |
| TPL11-AC-002 | The site switch changes only through a deployment command and only while the lifecycle is `Available`; each change records the actor, time and new state; **STD Templates** shows the switch state and offers no switch, activate or approve action. |
| TPL11-AC-003 | **STD Templates** shows `Available` only for a release whose lifecycle is `Available`, whose site switch is On, whose integrity is verified and whose registered renderer is present. Any other lifecycle-`Available` release shows `Unavailable` with its cause as a blocker and cannot bind a new Tender. `Superseded` and `Withdrawn` show as themselves. `Unavailable` is never a lifecycle or manifest value. |
| TPL11-AC-004 | Recorded gate results, open review items, the Gate D and Gate E reviews and any owner decision appear only as evidence in **Verification** or **Technical details**; none is a blocker, and none prevents installation, `Available` or use. |
| TPL11-AC-005 | Switching a release Off stops new Tenders binding it and never rebinds, strands or blocks a Tender already bound; that Tender continues under the §14.1 lifecycle rules. |
| TPL11-AC-006 | The constructed manifest `status` value `Candidate` is evidence only and is not read to decide availability. A recorded owner decision must name the exact template release, bundle digest and manifest-file digest, or installation fails. A controlled byte change requires complete regeneration and validation but no owner re-approval. |
| TPL11-AC-007 | The release change report's overall result is exactly `Compatible successor`, `Breaking — not interchangeable with the preceding release` or `First release`. |
| TPL11-AC-008 | The installed-empty and Unavailable list copy, the detail consequence and next-step copy, the **Site switch** verification row and caption, and the absence of an **Owner approval** row match §§11.2–11.4 as amended in v0.11. |

## 16. Prohibited shortcuts

The implementation shall not:

1. parse the issued PDF to construct the Bid Workspace;
2. expose a generic form, clause, evaluation or contract-mapping builder;
3. let a Procurement Officer re-enter inherited requirements;
4. treat an attachment as the only statement of an obligation;
5. generate one weighted criterion per response row;
6. force every response into evaluation or contract treatment when N/A is correct;
7. copy addendum responses by label, row order or text similarity;
8. mark a bundle Available (the §14.1 availability projection) while its integrity check fails, its renderer is missing or its site switch is Off (v0.11, OD5; v0.10 read: while a gate, digest or owner decision is missing);
9. hide installed-template content from authorised Administrator/System Manager users or place the inspection surface back inside System setup;
10. infer reservation eligibility from a Planning designation, supplier address, Account status or uploaded file without the published rule and governed evaluation; or
11. claim support for another product family because its fields fit the primitive control allowlist;
12. maintain a second fixture-only Bid-definition compiler;
13. hard-code a document-engine executable outside the registered renderer adapter;
14. automatically rebind a Tender when a release is superseded or withdrawn;
15. add a site-level template authoring, upload, activation or adoption-approval workflow, or any release approval or commissioning step before use (v0.11, OD5; the site switch is a deployment command, not a workflow); or
16. hide exclusions, conditional treatments or between-release changes behind totals alone.

## 17. Normative references and precedence

This release follows:

- KT-STD-001 v1.8 for document and artboard quality;
- STD-ST-001 v0.5 for simplified curated-template policy;
- STD-STD-001 v1.1 for content separation and curation principles;
- LAW-REG-001 v1.2 for the verified statutory interpretation and reservation boundary;
- CFG-CHG-002 v0.16 proposed for site configuration, effective-rule and public-portal-information ownership only; installed template inspection is owned here under **STD Templates**;
- REQ-CHG-001 v1.12 approved for the authoritative structured requirement handoff;
- TPR-CHG-001 v0.11 proposed for Tender preparation, publication, clarifications and mandatory candidate notices;
- STD-TPL-IMP-001 v1.0 proposed for installation, projection, compiler, renderer-adapter and lifecycle implementation; and
- BDS-CHG-001 v0.7 proposed for candidate registration, supplier runtime, submission, custody and receipt.

For template content, response construction and downstream mappings, this document and its exact approved bundle govern (v0.11, OD5: the exact installed release bundle; no bundle approval is required). For a particular Tender, the immutable approved Tender Version and Published Bid Definition govern. A lower layer cannot silently broaden the product boundary.

`STD-TPL-IMP-001 v0.2` is historical source analysis only. It targets the superseded release 1.0/KEBS/PDF-primary assumptions and cannot authorise release 1.1 construction or implementation.

## 18. Full v0.8 change register

| ID | v0.7 gap | Complete v0.8 correction | Verification |
|---|---|---|---|
| TPL08-CHG-001 | The release contract named assets and gates but did not explain how to construct the bundle. | Add the authoritative eight-phase construction procedure with stop gates and exact outputs. | TPL08-AC-001 |
| TPL08-CHG-002 | Source coverage registers had no current schemas after the document was shortened. | Restore exact coverage, insertion and forms columns and controlled treatment values. | TPL08-AC-002 |
| TPL08-CHG-003 | Runtime JSON files were named but their common envelope and allowed content were undefined. | Define the release envelope, product profile, response rules, downstream rules and addendum rule contracts. | TPL08-AC-003–006 |
| TPL08-CHG-004 | Stable bidder-response identity was required but not constructible. | Define the canonical Tender-Version/source/rule/field identity tuple and grouping lineage. | TPL08-AC-007 |
| TPL08-CHG-005 | The MoH Published Bid Definition had no prescribed shape or single-input rule. | Define its top-level structure and require the same MoH input to generate both projections. | TPL08-AC-008 |
| TPL08-CHG-006 | Only the Youth fixture was concrete although all supported reservation paths gate release. | Add isolated `None`, Women, Persons-with-disabilities, County and unsupported-overlap fixtures. | TPL08-AC-009 |
| TPL08-CHG-007 | `validate_release.py` had no interface or exhaustive result contract. | Define its command, deterministic report, exit behaviour and eighteen mandatory check families. | TPL08-AC-010 |
| TPL08-CHG-008 | Approval referred to a manifest that was absent from the pack and had no digest algorithm. | Add `release_manifest.json`, exact asset inventory and non-self-referential bundle/manifest digest treatment. | TPL08-AC-011–013 |
| TPL08-CHG-009 | Review roles and owner approval object were ambiguous. | Make review responsibilities non-system roles and bind approval to exact release and digests. | TPL08-AC-013 |
| TPL08-CHG-010 | The old implementation pack could be mistaken for current bundle instructions. | Declare STD-TPL-IMP-001 v0.2 historical and require a release-1.1 successor to consume the approved bundle without re-authoring it. | TPL08-AC-014–015 |
| TPL08-CHG-011 | Current upstream and consumer document versions were stale. | Adopt approved REQ v1.11; identify TPR v0.9 and BDS v0.6 as coordinated proposed consumers and CFG v0.15 as the narrowed configuration successor. | TPL08-AC-015 |
| TPL08-CHG-012 | A byte change after review could retain an earlier approval. | Require full rebuild, validation, manifest and owner decision for every controlled-byte change. | TPL08-AC-012–013 |
| TPL08-CHG-013 | Administrative inspection was embedded in System setup and too terse to generate complete screens. | Move it to the first-class **STD Templates** module and add the self-contained list/detail static design contract, complete fixture, variants, interactions and security boundary. | §§3.1, 11; TPL08-AC-019–020 |
| TPL08-CHG-014 | The structured fixture shape did not match BDS's canonical Published Bid Definition and left the production materialisation point implicit. | Adopt the exact `PublishedBidDefinition v1` fields and require atomic production materialisation with publication. | §§3.1–3.2, 13.7; TPL08-AC-016, 021 |
| TPL08-CHG-015 | The control allowlist could not preserve multi-select network connectivity or structured port rows from Requisitions. | Add controlled multi-select and the reviewed structured-ports composition with bounded semantics. | §§8.2, 13.5.1; TPL08-AC-017 |
| TPL08-CHG-016 | The release described four stages but declared only three evaluation groups. | Define the four exact groups, including `EVG-AWARD`, consistently across profile, UI and mappings. | §§9.1, 13.5.1; TPL08-AC-018 |
| TPL08-CHG-017 | Manifest/inspection data was insufficient for Tenders and the administrative UI. | Add release identity, renderer compatibility, named constituent digests, summaries, verification results, blockers and owner-decision projection. | §§11, 13.9; TPL08-AC-019 |
| TPL08-CHG-018 | Evidence-row cardinality and officer terminology drifted from Tenders. | Permit finite separately justified additional evidence rows and align the two contract labels exactly. | §6.2; coordinated document check |
| TPL08-CHG-019 | Addendum classification names drifted across the template, Tenders and BDS. | Standardise `unchanged`, `converted`, `fresh_response_required`, `removed`, `new`. | §§10, 13.5.4; coordinated document check |
| TPL08-CHG-020 | The UI word `Unavailable` could be read as an undocumented fifth release lifecycle status. | Define it as a derived administrative projection for Candidate/blocked releases while retaining the four-value controlled lifecycle. | §14.1; TPL08-AC-022 |
| TPL08-CHG-021 | Publication wording allowed a reader to attach definition fields to an already-approved Tender Version, and addendum effectiveness lacked an explicit activation boundary. | Place original-definition evidence on `TenderPublication`; freeze the successor at addendum issue and activate it only with the final required-channel confirmation. | §§10, 13.7; TPL08-AC-023 |

### 18.1 v0.9 Gate 1 interface reconciliation

| ID | v0.8 issue | v0.9 correction | Verification |
|---|---|---|---|
| TPL09-CHG-001 | Active consumer references predated the reconciled public/vendor contracts. | Adopt TPR v0.10, BDS v0.7 and CFG v0.16 while retaining REQ v1.11. | TPL09-AC-003 and obsolete-reference scan. |
| TPL09-CHG-002 | A later implementer could place clarifications, candidate audiences or delivery data inside the reusable template bundle. | State the exact TPR/BDS/CFG ownership boundary and prohibit those operational records in the controlled assets. | TPL09-AC-001. |
| TPL09-CHG-003 | The effect of a clarification on release identity was implicit. | Distinguish a non-changing answer from a published-content change; require the latter to use an issued addendum and the released identity rules. | TPL09-AC-002. |

### 18.2 v0.10 implementation and visibility closure

| ID | v0.9 gap | v0.10 correction | Verification |
|---|---|---|---|
| TPL10-CHG-001 | The administrative surface proved release presence but concealed row-level coverage, exclusions and change impact. | Add **Coverage and changes**, reconciled treatments, row inspection and generated preceding-release comparison. | TPL10-AC-001 |
| TPL10-CHG-002 | Users could discover a problem but had no bounded way to record it. | Add release-bound **Report concern** without template mutation or automatic lifecycle effect. | TPL10-AC-002 |
| TPL10-CHG-003 | Gate results existed principally as prose. | Add `release_gates.json` with mandatory evidence-linked rows and fail-closed treatment. | TPL10-AC-003 |
| TPL10-CHG-004 | Fixture and production builders could drift into separate algorithms. | Require one deterministic compiler with CLI and production adapters plus parity tests. | TPL10-AC-004 |
| TPL10-CHG-005 | The construction steps named a specific archived rendering executable as if it were the permanent contract. | Bind releases to a versioned renderer adapter and require complete regression evidence for engine changes. | TPL10-AC-005 |
| TPL10-CHG-006 | Superseded and Withdrawn did not define the effect on already-bound unpublished Tenders. | Permit integrity-checked continuation only for Superseded; block publication for Withdrawn; prohibit automatic rebinding. | TPL10-AC-006–008 |
| TPL10-CHG-007 | Procurement governance users lacked direct inspection access. | Extend read/concern access to Procurement Officer and HOPF without template-edit or broader technical permissions. | TPL07-AC-014; AUTH-ADR-001 v1.10 |
| TPL10-CHG-008 | The current release had no usable implementation authority. | Introduce STD-TPL-IMP-001 v1.0 for records, services, security, compiler, adapters, deployment and tests. | TPL10-AC-010 |
| TPL10-CHG-009 | Installation could be misread as requiring a second local approval. | State that exact-manifest owner approval is sufficient; installation verifies rather than re-approves. | TPL10-AC-009 |

### 18.3 v0.11 owner decision OD5 and §12.1 correction

Decision basis, quoted:

| Date | Project Owner instruction |
|---|---|
| 26 September 2026 | OD5, given when asked how Requisitions should treat an unapproved Candidate release: "I don't want this complicated admin overhead regarding approvals and commissioning of templates. It is unnecessary, adds no value and is vexing. Allow development work to contine without this friction. Template release is purely an on and off switch on an affected site. Update this decision as a follow up to reflect in affected documents if necessary" |
| 26 September 2026 | "Close the open issues" — the instruction to make these document updates |

| ID | v0.10 issue | v0.11 correction | Verification |
|---|---|---|---|
| TPL11-CHG-001 | Release use depended on owner approval of the exact manifest, a Candidate lifecycle state and Gate E. | Reflect OD5: an intact release installs Available and switched On; Candidate is retired as a lifecycle state; gates, reviews and any owner decision are recorded evidence. | §§3.1, 4.1, 13, 13.9, 13.10, 13.11, 14.1; TPL11-AC-001, 004, 006 |
| TPL11-CHG-002 | A release could only become usable through an approval route, and no site-level control stopped or resumed its use. | Add the site switch: changed only by a deployment command, audited, allowed only while the lifecycle is Available, and governing new binding only. | §§3, 3.1, 14.1; TPL11-AC-002, 005 |
| TPL11-CHG-003 | The availability projection treated missing gates, verification results or owner decisions as reasons for Unavailable. | Show Available only when the lifecycle is Available, the switch is On, integrity is verified and the renderer is registered; derive blockers live from those conditions only. | §§11.3, 11.4, 12, 14.1, 14.2; TPL11-AC-003, 004 |
| TPL11-CHG-004 | **STD Templates** copy and the design fixture asked for approval through the Owner approval row, the installed-empty and Unavailable wording and the fixture blockers. | Replace the Owner approval row with a live Site switch row and caption; amend the empty, Unavailable, consequence and next-step copy; make the fixture Unavailable because it is switched Off. | §§11.2–11.6; TPL11-AC-008 |
| TPL11-CHG-005 | The manifest `status` value and the change-report result wording implied a pending approval. | State that `status` `Candidate` is evidence only; rename the breaking result to `Breaking — not interchangeable with the preceding release`. | §13.9; TPL11-AC-006, 007 |
| TPL11-CHG-006 | Acceptance criteria and prohibitions required owner approval before use. | Mark TPL07-AC-013, TPL07-AC-015, TPL08-AC-012, TPL08-AC-013, TPL08-AC-014, TPL08-AC-022, TPL10-AC-003 and TPL10-AC-009 superseded or amended; amend prohibitions 8 and 15 and the §17 precedence wording. | §§15, 16, 17 |
| TPL11-CHG-007 | §12.1 stated that the runtime assets, a validator and a manifest already existed; none existed until 26 September 2026 (follow-up FU-02). | Add a correction beside the retained v0.10 statement. | §12.1 correction paragraph |

## 19. Approval effect

### 19.1 v0.11 (proposed)

v0.11 is proposed for Project Owner approval. On approval it supersedes v0.10, which was in Project Owner review and was never approved, and carries forward everything v0.10 proposed except as amended here. It records owner decision OD5 of 26 September 2026 (§18.3). A template release is an On/Off switch on a site. An intact release installs Available and switched On. The §13 reviews (including Gates D and E), the §14.2 gates and any owner decision are recorded evidence that never block use. **STD Templates** shows a release as Available only when its lifecycle is Available, its site switch is On, its integrity is verified and its renderer is registered. The site switch is a deployment command, so the **STD Templates** surface still has no activation action. v0.11 also corrects §12.1 (follow-up FU-02). Approval of v0.11 does not itself install, switch, supersede or withdraw a release, and it does not create a candidate registration, answer a clarification, send a notice or configure public portal information.

### 19.2 v0.10 (retained; its release-availability sentences are superseded by OD5)

Approval of this document supersedes v0.9 and approves the requirements, construction procedure, visibility contract and release-lifecycle boundary for release 1.1; it does not itself approve the bundle. Release 1.1 becomes Available only when the owner approves the exact manifest after §13 is completed and every §14 gate passes. Installation verifies that decision and does not add a second approval. Approval does not create a candidate registration, answer a clarification, send a notice or configure public portal information.
