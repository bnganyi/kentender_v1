# LAW-REG-001 — Statutory Correction Register

| Control | Value |
|---|---|
| Document ID | LAW-REG-001 |
| Version | 1.2 |
| Date | 23 September 2026 |
| Status | **Proposed for approval — 30% reservation interpretation correction** |
| Approved on | Not yet approved |
| Approval record | Prepared following the Project Owner's instruction to correct the 30% reservation rule. |
| Predecessor | v1.1, approved 12 September 2026; retained unchanged as historical evidence |
| Approval effect | On approval, supersedes v1.1's interpretations and implementation instructions where corrected below. Approval of this document does not verify an unverified legal proposition or amend another controlled document automatically. |
| Purpose | Separate source evidence, legal interpretation and KenTender design decisions; correct the Planning-related statutory register and assign unresolved legal/configuration work to its proper owner. |
| Governing project decisions | Approved LAW v1.1 retained except for this correction; proposed PLN-CHG-001 v1.25 and CFG-CHG-002 v0.13; attached 30% reservation-rule review |
| Verification scope | Targeted primary-source checks and a visual inspection of the historical Third Schedule. No claim of exhaustive legislation, amendment, case-law or circular review through the document date. |
| Change table | §11 provides the complete successor change register and acceptance mapping. |

## 1. Evidence and verification rules

### 1.1 Three distinct kinds of statement

| Kind | Meaning | Permitted implementation use |
|---|---|---|
| Source evidence | What an identified instrument, edition, provision or official communication actually says. | Evidence for a rule; not automatically proof of its current applicability to every entity or transaction. |
| Interpretation | How provisions, definitions, amendments and institutional circumstances fit together. | Must identify its reasoning and unresolved questions; no silent conversion of ambiguity into a permissive constant. |
| KenTender decision | A chosen system control that implements or conservatively limits a workflow. | State it as a product decision. Do not attribute its exact database model, transaction point or extra restriction to legislation unless the source actually prescribes it. |

This is a reorganized analytical register, not a verbatim transcription. Short source labels are retained where necessary for mapping. The predecessor's assertions that every source had been read in full and that nothing remained unread are not adopted as this review's findings.

### 1.2 Sources and retrieval record

| Evidence ID | Source and edition | Inspected evidence / location | Verification limit |
|---|---|---|---|
| SRC-01 | Supplied LAW-REG-001 v1.0 | Entire attached register, dated 3 September 2026 | Its citations and figures are inherited evidence claims, not automatically independently verified law. |
| SRC-02 | National Treasury-hosted Public Procurement and Asset Disposal Regulations, Legal Notice 69 of 2020, Gazette Supplement No. 53 dated 22 April 2020 | Downloaded PDF, 121 PDF pages. Targeted provision inspection and Third Schedule printed pp. 849–851; table visually inspected on printed p. 850, PDF page 102. [Official PDF](https://www.treasury.go.ke/sites/default/files/PPDA/Public-Procurement-and-Asset-Disposal-Regulations-2020.pdf) | This is the historical gazetted source, not a verified consolidated statement through September 2026. Later amendments and applicable directions require reconciliation. |
| SRC-03 | PPRA official Regulations index | Lists the 2020 Regulations and a separate amendments download. [PPRA index](https://ppra.go.ke/regulations/) | Index inspected; amendment text was not successfully obtained through the exposed download link. No inference that the amendment is irrelevant. |
| SRC-04 | PPRA official Act, Revised Edition 2022, download entry | Official entry identifies that edition. [PPRA Act entry](https://ppra.go.ke/download/the-public-procurement-and-asset-disposal-act-revised-edition-2022/) | The entry is not the Act's text. Kenya Law edition-specific Act retrieval returned access errors; the Act's provisions below remain inherited pending direct edition verification. |
| SRC-05 | PPRA Circular 02/2025 on PPIP/E-GPS integration | Official published circular text, including its references to the Treasury circular of 26 March 2025 and Office of the President circular of 5 June 2025. [Official circular](https://ppra.go.ke/ppra-circular-02-2025/) | Circular text inspected. Referenced circulars, subsequent changes, judicial orders and entity-specific application were not comprehensively verified. |
| SRC-06 | Supplied controlled project documents | PLN v1.18, CFG v0.9, BUD v1.7, NDS v1.10, STR v1.7, REQ v1.7, TPR v0.7, TPUB internal v0.3 and approved SEED v1.3 | Evidence of project requirements/decisions; not primary legal sources. DSP was not supplied. |
| SRC-07 | Attached `thirty_percent_reservation_rule.pdf` | Four-page analytical note supplied for this correction; distinguishes Budget ceiling, current complete APP planning value and downstream actual procurement value | Project interpretation evidence, not a primary legal instrument. Its conclusions require the source checks and controlled adoption recorded here. |
| SRC-08 | Kenya Law, Public Procurement and Asset Disposal Act, revised edition dated 31 December 2022 | Targeted inspection of sections 45(3), 53(6), 157(5) and 157(10). [Official Act](https://new.kenyalaw.org/akn/ke/act/2015/33/eng@2022-12-31) | Official consolidated text for the named edition; later changes and applicability through the production date remain subject to LAW-V-001. |
| SRC-09 | National Treasury-hosted Public Procurement and Asset Disposal Regulations, Legal Notice 69 of 2020 | Targeted reinspection of regulations 40(5) and 149 in the official PDF already identified as SRC-02 | Historical gazetted source; later amendments and current applicability remain subject to LAW-V-001. |

SRC-02 retrieved on 12 September 2026; SHA-256: `29c65f140544b10c161515086800b65a89507fdafa355207a986ac603fa8d3d7`. Page numbers below distinguish printed page from PDF page where necessary. The publication date printed on the source is not asserted to be its legal commencement date.

### 1.3 Targeted primary-source findings

The following findings are limited to the inspected sources:

| Finding | Evidence |
|---|---|
| VF-01 | SRC-02's Third Schedule has 16 numbered table columns; guidance note 17 separately names Status. Its signature block distinguishes HOPF preparation, AO countersignature and CS/CECM/Board/Council approval. |
| VF-02 | SRC-02 regulation 40(3) directs departmental plans to the AO; 40(4) assigns consolidated preparation to the AO. These responsibilities must be reconciled with procurement-function routing and the signature block. |
| VF-03 | SRC-02 regulations 49(2) and 50(1) address State Portal integration and plan upload when using e-procurement. |
| VF-04 | SRC-02 regulation 180(3)–(5) addresses disposal submission timing and differentiates departmental routes from corporation submissions. AO-only approval cannot be inferred universally from the form. |
| VF-05 | SRC-05 directs reporting through E-GPS from 1 July 2025 and registration by 30 June 2025; it also addresses transfer of procuring responsibility and continued public disclosure through PPIP. |
| VF-06 | SRC-08 section 45(3) requires procurement processes to stay within approved budget and section 53(6) requires all procurement and asset-disposal planning to be within approved budgets. “Within” establishes a ceiling; it does not require the APP to exhaust every approved shilling. |
| VF-07 | SRC-08 section 157(5) uses procurement-budget language, while section 157(10) uses procurement-value language. SRC-09 regulation 149 uses annual-procurement-budget language. The provisions do not themselves supply KenTender's full data-boundary algorithm, so source wording, controlled interpretation and actual implementation measure must remain distinguishable. |
| VF-08 | SRC-09 regulation 40(5) separately addresses the county-resident allocation. Its denominator, eligibility and interaction with AGPO must not be inferred from the 30% Planning interpretation. |

VF-01–04 identify historical source content, not closure of current-law applicability. VF-05 identifies the circular's direction, not a finding that every subsequent implementation or enforcement question is resolved. VF-06–08 support the corrected system interpretation but do not eliminate the current-edition, category, county or overlap verification gates. [SRC-02](https://www.treasury.go.ke/sites/default/files/PPDA/Public-Procurement-and-Asset-Disposal-Regulations-2020.pdf), [SRC-05](https://ppra.go.ke/ppra-circular-02-2025/), [SRC-08](https://new.kenyalaw.org/akn/ke/act/2015/33/eng@2022-12-31).

### 1.4 Verification dispositions

| Disposition | Meaning |
|---|---|
| Source checked — identified edition | Specified content was inspected in the named source; current applicability may remain open. |
| Inherited — primary verification pending | Preserved from v1.0 to maintain traceability; not verified afresh in this review. |
| Interpretation unresolved | Evidence exists, but the controlling meaning, applicability or implementation mapping remains unsettled. |
| KenTender decision agreed | Approved product behavior; not itself a claim of statutory wording. |
| Superseded instruction | Do not implement the predecessor's instruction; use its replacement here. |

These are document-review dispositions, not new CFG enum values. CFG owns its stored verification vocabulary. A production rule may be marked Verified only after its exact source, applicability, effective period and interpretation are resolved. Approval of this register, a passing seed, or a screenshot must not change that status by implication.

## 2. Third Schedule — format and field mapping

### 2.1 Corrected description

VF-01 resolves the predecessor's numerical inconsistency for the inspected historical edition. Do not change “sixteen” mechanically to “seventeen.” Retain the distinction between the printed grid and the guidance note; the current prescribed export treatment of Status remains a format-validation task.

The mapping below reorganizes the fields already recorded in v1.0. It is a KenTender mapping, not a facsimile, and does not certify the production export layout.

| Source position | Concept retained from v1.0 | KenTender treatment |
|---|---|---|
| Header | Ministry/Parastatal; entity name; optional project; financial year | Owner-supplied entity/FY identity; optional project name. No invented PE selector or compulsory project. |
| 1 | Number | Public row numbering is distinct from stable item and exact version IDs. |
| 2 | Item description | Approved package description; do not substitute detailed tender specifications. |
| 3–4 | Unit and quantity | Governed UOM and exact approved quantity; preserve source lineage. |
| 5 | Procurement method | Display the selected admissible method and retain its rule/profile version. Catalogue membership alone does not establish executable support. |
| 6 | Funding source | Use the governed funding-source name, separate from internal Budget Line identifiers. |
| 7 | Estimated cost, source heading in thousands of KES | Internal Money remains exact currency-unit decimal. Export conversion, displayed precision and rounding policy must be explicit; never reinterpret an internal shilling amount as minor units. |
| 8 | Time-process information | Keep planned baseline, actual evidence and duration variance distinct. The source's repeated timing rows are not one generic completion-status field. |
| 9–14 | Invitation, opening, evaluation, award, notification and signing | Preserve the seven-milestone Planning model, including the separate completion boundary below. Actuals belong to exact proceedings. |
| 15 | Interval associated with notification and signing | Do not infer total procurement lead time from its heading. Verify the exact endpoint/counting mapping before export. |
| 16 | Contract-completion date/time concept | Preserve source required-by boundary, estimated period/completion and actual completion separately; resolve the heading/guidance date-versus-duration presentation explicitly. |
| Guidance note 17 | Status | Retain status as required mapped information; do not call it a seventeenth printed column or guess its lawful layout/semantics. |
| Signature block | Preparation, countersignature and statutory approval | Apply §3; retain each exact actor, capacity, signed version and instant. |

### 2.2 Timing semantics and missing operational data

The predecessor correctly identified a need to represent actuals, but its P1 instruction “per Plan Item” is too coarse for multiple proceedings. Apply the agreed PLN v1.18 model:

| Measure | Definition / owner |
|---|---|
| Baseline date | Immutable approved planning date. |
| Forecast | Separately versioned operational expectation with its own reason and revision identity. |
| Actual | Authenticated owner event for the exact proceeding and milestone; linked corrections preserve earlier evidence. |
| Baseline lateness | Actual date minus baseline date; positive means late. |
| Forecast error | Actual date minus the identified forecast revision; do not compare to a subsequently revised forecast silently. |
| Duration variance | Planned elapsed days minus actual elapsed days for the same defined activity; not the same sign convention or measure as date lateness. |

The supported invitation integration does not create the other six actuals. Blank/unavailable actuals must remain explicit; no inferred award, contract completion or fulfilment from Plan or Tender publication. Aggregate item-level actuals need a future owner contract. This preserves the agreed implementation boundary without claiming that an incomplete dataset fulfils every statutory return.

### 2.3 Export verification still required

Complete the current-edition form check, Status placement, grouped timing rows, date/day endpoint rules, unit conversion, signature mapping and accessible web/PDF/JSON parity before claiming prescribed-format compliance. Retain the historical source alongside the approved mapping. A KenTender JSON schema is not an OCDS compliance claim and does not itself replace a prescribed public form.

## 3. Procurement planning governance

### 3.1 Correct the HOPF/Planner conflation

The predecessor's statement that HOPF preparation “matches” a Procurement Planner submission was incorrect. Under the approved KenTender decision, the Planner consolidates and maintains draft content; the HOPF performs **Sign and submit Annual Plan** on the complete exact version. The AO then adopts/countersigns and the configured statutory authority approves. No additional HOPF approval state is introduced.

| Actor | KenTender responsibility | Legal/evidence qualification |
|---|---|---|
| Departmental Author | Prepares permitted departmental content | Internal role under AUTH; not a substitute for HoD certification. |
| Head of User Department | Certifies the departmental submission | Reconcile the departmental submission recipient and procurement-function route in VF-02 and the inherited regulation 34(i) citation. |
| Procurement Planner | Validates submissions, consolidates and edits the candidate Plan | Operational role; cannot impersonate the HOPF signature or statutory authority. |
| Finance Confirmation Officer | Confirms the whole Plan's financial basis by Budget Line | KenTender affordability control, not a separately named statutory Plan approver. |
| Head of Procurement Function | Signs and submits the complete Plan | Implements the distinct preparation signature identified in VF-01; AO accountability in VF-02 remains. |
| Accounting Officer | Adopts/countersigns and submits onward; accountable for the entity's Plan | Do not present the HOPF signature as removing the AO's preparation/accountability duties. |
| Configured statutory authority | Approves under the applicable CS, CECM, Board or Council route | Exact entity-specific applicability is required; a generic route choice does not itself establish jurisdiction. |

The DPP-to-procurement-function workflow must provide AO-level receipt/visibility and accountable consolidation consistent with its confirmed legal routing. Whether additional receipt evidence is required is an owner mapping question; this finding does not create a new departmental AO approval stage.

CFG v0.9 already contains all four route values. Replace the predecessor's “add Council” instruction with completion of the mandatory configuration command, first-run surface, AUTH mapping and evidence. Collective-body approval requires the agreed resolution evidence and authorized recorder, not an invented personal office. No “None” route or hidden local approver registry is permitted by the current design.

### 3.2 Funding and authorization boundaries

The inherited Act sections 53(2) and 53(8), and regulation 71(1), support budget alignment and procurement-initiation checks as recorded in v1.0. They do not prescribe KenTender's exact database reservation event or require exactly one lifetime Finance decision.

**Agreed KenTender control:** Planning performs a whole-Plan affordability review by line, creates no financial reservation, permits repeated review on changed financial bases and serializes the positive decision against BUD's authoritative basis. REQ authorization coordinates drawdown and BUD reservation. Budget approval, affordability confirmation, cash availability and financial reservation are distinct facts.

### 3.3 Later Needs, published tenders and permanent scope protection

The permanent source-scope lock at first authorized Requisition is an agreed conservative MVP control. It is not presented as statutory wording that every post-authorization correction is unlawful. A later Need cannot be absorbed into an already locked item through an APP revision or copied successor; use a separate item and governed procurement route. APP inclusion alone proves neither proceeding coverage nor fulfilment.

Any future scope expansion through tender amendment, cancellation/replacement or contract variation requires separately verified downstream conditions, authority, source/quantity treatment and evidence. The Planning change cannot stand in for those procedures. Temporary correction holds and terminal outcomes remain distinct from the permanent scope lock; no automatic resurrection of stopped Requisitions.

## 4. Methods, thresholds and procedure profiles

### 4.1 Catalogue, admissibility and implementation support

The predecessor attributes eleven method labels to Third Schedule guidance note 5: open tender, direct, restricted, request for quotation, low value, community participation, design competition, electronic reverse auction, force account, competitive negotiations and request for proposals. Retain that historical form mapping; do not infer that every method authorized elsewhere in the Act is unlawful because it is absent from those labels.

Its section 92 comparison, two-stage/framework treatment and specially permitted procurement mapping require reconciliation with the exact applicable Act and Regulations. Open tender remains the agreed default subject to legal admissibility. A method condition, threshold, exception, reporting label and implemented procedure are distinct configuration facts.

### 4.2 Carried-forward numeric claims — not a production threshold dataset

The following preserves the predecessor's selected numeric entries for verification and traceability. It is not a complete matrix; it omits methods and conditions. No row may be loaded as currently Verified solely because it appears here.

| Rule candidate | Goods | Works | Services | Verification needed |
|---|---:|---:|---:|---|
| Restricted, Act 102(1)(b) | KES 30m | KES 30m | KES 20m | Exact condition, comparator, applicability and revised matrix. |
| RFQ, Act 105 | KES 3m/request | KES 5m/request | KES 3m/request | Current ceiling, aggregation basis and required competition procedure. |
| Low value, Act 107 | KES 50,000/item/FY | KES 100,000/item/FY | KES 50,000/item/FY | Exact definition of item, annual cumulative basis, adjustments and anti-avoidance rules. |
| National/international open tender | No minimum; budget-qualified maximum, as reported in v1.0 | Same reported treatment | Same reported treatment | Method admission is distinct from national/international advertising thresholds. |
| Restricted, Act 102(1)(a)/(c) | No minimum; budget-qualified maximum, as reported in v1.0 | Same reported treatment | Same reported treatment | Condition-specific eligibility, not unrestricted permission based on amount. |
| RFP, Act 116 | No minimum; budget-qualified maximum, as reported in v1.0 | Same reported treatment | Same reported treatment | Appropriate procurement category and selection procedure must be resolved. |
| Direct, Act 103 | No fixed min/max reported | Same reported treatment | Same reported treatment | Applicable statutory grounds remain mandatory. |

All figures above are inherited from SRC-01. Retain them as pending candidates, with exact source provisions, rather than deleting traceability or presenting them as live configuration. Complete the omitted method rows and their segregation requirements before describing the result as the full Second Schedule matrix.

Goods/Works/Services is the threshold category and must be distinct from, or explicitly mapped by, finer requirement types. A Works catalogue entry does not authorize an unimplemented Works tender procedure.

The low-value annual test must not stop at a single Plan line or one APP version. Define the legally correct cumulative identity and data scope across relevant proceedings/adjustments; prevent duplicate counting across successor versions and evasion through splitting. The precise owner aggregation contract remains open until the legal basis is resolved.

### 4.3 Schedule profiles

Resolve method-specific preparation minima, evaluation maxima, standstill rules, exceptions and counting conventions. Planning buffers are labelled assumptions. The seed's 21/30/5/2/14-day example and seven-day reminder threshold are not independently verified legal constants. No guessed fallback is permitted when a mandatory applicable profile is missing.

## 5. Preferences and reservations

### 5.1 Preserve the separate legal bases

The following provisions and descriptions are carried from v1.0; their complete current application remains subject to §10 verification. They must not be merged into one interchangeable percentage rule.

| Inherited provision | Distinct basis identified in v1.0 | Required owner treatment |
|---|---|---|
| Regulation 149 | At least 30% of annual procurement budget for youth-, women- and disability-owned enterprises | Preserve the source wording. For KenTender's Planning control, apply the eligible value of the current complete APP under the controlled interpretation below; verify exact eligibility and scope. |
| Act 53(6) | Procurement/asset-disposal planning and budgetary allocations; includes other disadvantaged groups in its wording | Reconcile applicable groups and disposal treatment; do not import disposal lines into the APP. |
| Act 157(5) | Prescribed procurement-budget reservation for disadvantaged groups, not less than 30% | Resolve definitions and relationship with the other provisions. |
| Act 157(10) | Annual procurement-value allocation | Do not equate actual procurement results with planned budget allocations. |
| Act 158(1) | Integration of preferences/reservations into plans | Preserve planned designation and applicable restrictions. |
| Regulation 40(5), with Act citation 33(2)(g) reported in v1.0 | County-resident allocation, reported minimum 20% | Verify both citations, denominator, eligibility and overlap independently. |

**Controlled KenTender interpretation for Planning:** the applicable mandatory allocation target is a readiness condition, not an advisory warning. For the 30% AGPO planning measure:

- the denominator is the eligible value of the exact current complete APP Version: the sum of estimated values of current Plan Items included by the exact verified rule;
- the approved Budget is a funding ceiling checked separately and unused Budget headroom is not planned procurement;
- each included or excluded Plan Item retains its rule-based reason so expected procurement cannot be suppressed merely to reduce the denominator;
- an approved APP amendment recalculates the successor Version's denominator, target, qualifying allocation and remaining allocation without rewriting the predecessor snapshot; and
- actual achievement is a separate downstream measure: qualifying actual procurement value divided by applicable actual procurement value from authoritative proceedings, never from APP estimates.

A missing mandatory rule, missing calculation basis or shortfall blocks the affected positive submission/action; drafting remains available. This is a controlled product/legal interpretation informed by SRC-07–09, not a claim that the statutory phrases are textually identical. Production use still requires LAW-V-001 current-edition confirmation and exact category/applicability verification. Optional market-price-index availability is a separate matter.

The same amount must not be counted twice within one target. Whether a qualifying amount may count toward different concurrent obligations is a legal interpretation to resolve, not an assumed prohibition or permission. The county-resident measure remains separate. Missing rules cannot display “requirement met.”

### 5.2 Planned designation is not candidate entitlement

The predecessor's inference from Act 156 and regulation 153 to automatic Planning selection of the “highest advantage” scheme is withdrawn. Those cited provisions concern entitlement and scheme treatment for the person/candidate in the proceeding. Planning has no candidate evidence at that stage.

Retain planned designation and verified mandatory restrictions in Planning. Candidate eligibility, evidence, highest-advantage treatment and tender evaluation belong to the responsible downstream modules. Do not add a Planning override reason or automatic entitlement calculation. Categories mentioned across Act 157(4), regulations 151–152 and the annual-budget rules are not automatically interchangeable qualifying categories for every target.

### 5.3 Exclusive preference and evaluation margins

The predecessor reports regulation 163 figures of KES 1bn for the specified Works/material categories and KES 500m for Goods/Services. Preserve them as pending rule candidates. Resolve funding conditions, local origin, exact comparison boundaries, citizen-contractor definition and source edition before production selection.

The reported regulation 164 margins, 20%, 15%, 10%, 8% and 6%, are not a Planning ranking table. Their exact origin/shareholding conditions, equality boundaries, valuation basis and applicable procedure require downstream verification; do not invent values for gaps between the printed conditions.

The inherited regulation 154 unbundling citation supports investigating lawful participation-oriented packaging. It does not establish that all lotting has that sole purpose or repeal anti-splitting controls generally. Retain the approved lotting indicator and meaningful aggregation rationale; tender-lot formation and eligibility remain separately governed.

## 6. Reporting, publication and electronic-procurement obligations

### 6.1 Obligation register

The predecessor's eight rows are retained below with stable identifiers. Its “six distinct obligations” heading is removed. Descriptions and timing in LAW-OB-001–008 are inherited from v1.0 pending exact current-edition/application verification; the additional electronic-procurement obligation is grounded in VF-03/VF-05. Owner assignments are KenTender design responsibility, not verbatim legislation.

| ID | Cited basis | Accountable actor / output | Recipient | Trigger / timing to verify | KenTender owner and retained evidence |
|---|---|---|---|---|---|
| LAW-OB-001 | Act 44(2)(c), exemption reported under 44(3) | Entity/AO: submit procurement plan consistent with the applicable fiscal framework | National Treasury | Preparation/submission duty; verify exact trigger and exemption applicability | PLN: exact approved document, dispatch channel/reference, instant and supporting evidence; no Treasury approval stage. |
| LAW-OB-002 | Act 53(12) | Entity/AO: publish approved Plan as invitation to treat | Public, entity website | Submission to Treasury, as reported | PLN publication owner: immutable package, actual destination, acknowledgement, reconciliation and publication history. |
| LAW-OB-003 | Act 53(13) | National Treasury: portal publication duty | Public, State Portal | Receipt, as reported | External obligation; PLN records distinct evidence if supplied. Entity website success does not prove this external action. |
| LAW-OB-004 | Act 158(2), 44(2)(i) | Entity/AO: preference/reservation part of Plan | PPRA | Within 60 days after FY commencement, as reported | Reporting owner with PLN/BUD: exact qualifying allocations, denominator, rule versions and submission evidence. |
| LAW-OB-005 | Act 157(12)–(13), regulation 161(2) | Entity/AO: disaggregated compliance certification | PPRA; copy to Treasury under the reported regulation | Six-month reporting periods; 14 days after period end, subject to verification | Reporting with procurement/award owners: actual data and certification; not derived from planned designation alone. |
| LAW-OB-006 | Act 158(3), regulation 161(2) | Entity/AO: awards applying preference/reservation | PPRA; copy to Treasury under the reported regulation | Quarterly; 14 days after period end, subject to verification | Award/reporting owners: award, category evidence, value, period and exact return. |
| LAW-OB-007 | Regulation 40(6) | Entity/AO: APP implementation report | Applicable CS, CECM or governing body | Quarterly, as reported | Reporting with PLN and operational owners: planning baseline and actual implementation evidence; unavailable facts remain explicit. |
| LAW-OB-008 | Regulation 150(4), read with 150(1) | Entity/AO: payment-performance statistics | Treasury and PPRA | Quarterly; payment-period basis and conditions verified separately | Payment/contract/reporting owners: invoice, certification, payment dates and actual statistics. |
| LAW-OB-009 | Regulations 49–50; PPRA Circular 02/2025 | Entity/AO and responsible system owners: applicable e-procurement integration, upload/reporting and registration | Government e-procurement system / State Portal / PPRA as applicable | Electronic use and operative circular requirements; verify current route and applicability | Product/architecture with CFG/PLN/REQ/TPUB/reporting: permitted integration role, registration, exact transmissions, receipts and exception evidence. |

Do not apply the fourteen-day rule to every row without a provision that does so. Period close, dispatch deadline, recipient, required format and proof of submission must be distinct fields. “Future facility” does not waive an institution's legal reporting duty: record any permitted external operating procedure and responsible actor before production use depends on it.

### 6.2 Publication facts and recovery

The approved PLN control commits durable publication intent with statutory approval. AO records exact approved-Version Treasury dispatch evidence; valid evidence gates transmission. The adapter records the actual external result, including unknown outcomes; activation occurs once only if the candidate remains eligible. This is the system design implementing the supplied statutory interpretation, not a claim that each internal state name appears in the Act.

Treasury submission, entity website publication, State Portal publication and the relevant E-GPS transaction are distinct evidence. No one fact is automatically proof of the others. A real website destination is a production prerequisite. An isolated test acknowledgement or static Treasury example cannot establish external compliance.

### 6.3 Material follow-up from the primary-source check

VF-03 and VF-05 mean that KenTender's intended government operating model must be explicitly reconciled with the prescribed electronic channel. Determine whether KenTender is an authorized integrated system, a preparatory internal tool handing off to E-GPS, or another permitted arrangement; obtain the applicable technical and institutional evidence. This review does not select or authorize an integration model, infer permission for a parallel replacement platform, or declare KenTender prohibited.

This is a production operating-model dependency affecting more than Planning. Add it to the architecture/CFG/LAW follow-ups and reconcile the current status of the referenced circulars and any later directions/orders. The existing deferral of automated Treasury transmission or full OCDS functionality cannot be used to defer a legally required electronic channel without an established permitted arrangement.

## 7. Asset disposal — retain ownership and correct unsupported inferences

### 7.1 Separate plan and source mappings

The predecessor identifies Act 53(4), regulation 176 and the Thirteenth Schedule as the disposal-plan basis. Preserve the separate DSP module boundary. Do not add disposal items or their budget calculations into the Procurement APP.

Its recorded content includes item description, quantity/unit, purchase date/price, estimated current value, disposal justification, lifespan, asset-register reference, method, activity schedule, managing entity/agency/expert and disposal-management cost. The reported form also contains disposal-stage dates and an employee-disposal notice. These are inherited analytical mappings, not a verbatim certified layout; the DSP owner must verify the applicable form and every content-versus-column gap.

### 7.2 Approval and revision corrections

**Superseded instruction:** “The disposal plan is approved by the Accounting Officer” as an unconditional rule. VF-04 supplies a material route distinction omitted from v1.0. Reconcile Act 53(5), regulations 176 and 180, institutional type and the Thirteenth Schedule before specifying DSP's approval-state model. Separate consolidated-plan approval from approval of a disposal committee's particular recommendation. The signature block alone does not resolve the whole hierarchy.

**Superseded interpretation:** regulation 176(4)'s flexibility means an immutable-version model is unlawful. Flexibility concerns accommodation of emerging issues; it does not, by itself, require overwriting approved history. A governed successor/revision mechanism can preserve prior decisions while allowing change. The DSP owner must specify amendment authority and effects; this register does not import PLN's workflow unchanged.

### 7.3 Remaining disposal matters retained for DSP verification

| Inherited matter | Correct handling in the successor |
|---|---|
| Act 165 methods: transfer, public tender, auction, trade-in, waste management and prescribed methods | Verify exact permitted method and implementing procedure. “Destruction” must not be asserted universally non-statutory merely because it is not the top-level label; resolve the waste-management procedure and evidence. |
| Act 163/regulation 176 classifications: unserviceable, surplus, obsolete/obsolescent | Map domain conditions and approved disposal grounds; an operational expiry fact does not itself replace a legally required determination. |
| Act 165(2) licensing for radioactive/electronic waste | Verify applicable licensing and environmental-law requirements in the disposal procedure. |
| Act 4(2)(b) versus 165(1)(a), transfers without consideration/financial adjustment | Preserve the unresolved scope distinction; do not claim all such transfers fall inside or outside the same workflow. |
| Regulations 177–179 committee composition, quorum and functions; Act 45(4) segregation | Verify exact membership, conflicted-actor restrictions and decision scope in DSP, not Planning. |
| Act 164(3), 166: valuation, reserve price and employee/member restrictions | Withdraw any inference that a reserve price must always be below market value. Check the exact source and distinguish valuation, minimum accepted price and lawful exceptions. |

DSP was not supplied or amended here. This successor prevents propagation of the predecessor's broad instructions; it does not claim to complete the disposal PRD.

## 8. Legal support versus product implementation decisions

This replaces v1.0's blanket “Confirmed correct — no change needed” section.

| Predecessor position | Successor disposition |
|---|---|
| DPP is statutory | Retain cited basis in regulations 34(i)/40(3); distinguish HoD submission, recipient, internal consolidation and approval. Resolve VF-02 routing evidence. |
| Departmental Needs has no statutory standing | KenTender's named Needs workflow is an internal design. Absence of that product name in two instruments does not establish that underlying need identification has no legal significance. DPP duties still apply. |
| Statutory approval is required above the AO | Retain the agreed applicable route; verify entity-specific statutory competence. No universal route inferred solely from a dropdown. |
| Reservation belongs at REQ, not Planning | Retain financial-reservation placement as a KenTender decision; distinguish it from statutory preference/reservation allocations. |
| One plan-level funding confirmation | Whole-Plan, per-line affordability review is agreed; repeated confirmations and reassessment are allowed. Statutory wording is not evidence of one lifetime decision. |
| Plan is part of budget preparation | Preserve inherited Act 53(2)/regulation 40(1) grounding and the BUD ownership boundary. |
| Multi-year procurement aligns with MTEF | Preserve the inherited provisions; single-year MVP restriction is a product boundary, not a claim that multi-year procurement is unlawful. |
| Estimates include incidentals and market-survey support | Preserve the requirement and traceability; do not turn a UI example reference into actual survey evidence. |
| Anti-splitting | Preserve inherited Act 54(1)/regulation 43(1); investigate packaging across the correct cumulative scope, not just one APP row. |
| Market-price benchmark | Preserve citations and the distinction between mandatory pricing duties and availability of an optional index in KenTender. Verify the exact current market-survey/handbook duties before asserting full compliance. |
| Classified procurement | Retain as a separate applicability/workflow matter under the inherited Act 90/regulation 84 citations; do not claim the ordinary public Plan flow covers it. Exact annual-list deadline and format remain verification items. |

## 9. Owner amendments and predecessor-ID disposition

### 9.1 Original Planning change IDs

| Original ID | Current disposition / required owner work |
|---|---|
| P1 | PLN v1.18 already specifies proceeding-level actuals and distinct comparisons. Verify supported producer contracts; six integrations and aggregation remain future facilities. |
| P2 | Optional project and status information retained; correct printed-column versus guidance-note attribution under §2. Final format mapping remains open. |
| P3 | Keep the historical eleven-label form mapping; verify legal method/reporting mapping and executable support rather than treating the label list as the entire law. |
| P4 | Goods/Works/Services mapping retained; complete category-specific rule and implementation support coverage. |
| P5 | Replace unconditional loading of v1.0 figures with source/version/applicability verification and a complete method/cumulative contract. |
| P6 | Replace Planning highest-advantage resolution with planned designation and verified restrictions; candidate entitlement stays downstream. |
| P7 | Retain exclusive-preference applicability as a pending governed rule; verify exact conditions/comparators. |
| P8 | Replace numeric heading and vague non-goals with LAW-OB-001–009, responsible actors, deadlines, evidence and operating dependencies. |
| P9 | Retain invitation-to-treat characterization attributed to the cited Act provision; complete real website and electronic-channel evidence. |
| P10 | Disposal remains outside Procurement Planning; DSP owns its legal governance reconciliation. |
| P11 | Keep genuine estimate-basis evidence and required incidental-cost treatment; no fabricated market survey. |

### 9.2 Other original instructions and current owners

| Owner / original item | Required successor disposition |
|---|---|
| CFG C1 | Four routes already exist in v0.9; complete fields, first-run commands/artboards, validation and authority mapping. |
| CFG C2 | Extend the existing historical Regulatory Reference register with verified rule versions/resolvers, method/schedule/reminder profiles and mandatory reservation readiness. Do not introduce a parallel Planning registry or configuration approval chain. |
| CFG C3 | Disposal intake already has a CFG owner. Specify its separate service/UI/clock behavior in the disposal/configuration amendment, not in the Procurement Planning payload. |
| BUD “No change” | Superseded: atomic affordability validation, Budget ceiling/source-OU eligibility and exact decimal contracts are required. PLN owns the eligible-current-APP planning calculation; downstream reporting owns actual achievement. Legal support for a funds check does not complete these APIs. |
| NDS “No change” | Superseded: accepted DPP disposition event/projection is separate from Active usage; chronology/scopes and exact source contracts also require reconciliation. |
| REQ / TPR / TPUB | Adopt scope-lock/hold/correction contracts and exact proceeding publication-actual envelope; retain downstream correction authority and permanent evidence. |
| STR | Verify final approval snapshot compatibility against the reviewed lineage; amend only where the current provider contract is insufficient. |
| SEED / KT-STD | Apply approved SEED v1.3 and shared role/chronology corrections. Isolated test rules do not become production legal verification. |
| DSP | Replace universal AO-only and anti-immutability instructions with an entity-specific approval/amendment model grounded in the full provisions. |
| Product / architecture / reporting | Resolve the electronic operating model and actual mandatory-channel/reporting responsibilities; link LAW-OB-009 to affected module release gates. |

These are owner amendments, not claims that external controlled files or implementations have already changed. A narrowly editorial PLN successor may correct citations and incorporate findings; substantive new operating-model consequences require an explicit controlled decision.

## 10. Outstanding legal and implementation verification

| ID | Exact unresolved question / evidence needed | Owner | Gate |
|---|---|---|---|
| LAW-V-001 | Establish applicable Act/Regulations editions, amendments, commencement/effective dates and relevant later directions/orders through the intended operating date. Obtain the failed/missing primary texts. | LAW | Current-law assertion for every dependent rule. |
| LAW-V-002 | Confirm current Third Schedule and authorized Status/date/day/cost/signature layout, with source-to-export mapping and visual comparison. | LAW / PLN publication | Prescribed-format compliance claim and affected production export. |
| LAW-V-003 | Resolve method admissibility, threshold comparisons, missing matrix rows, exceptions, category mapping and supported procedures. | LAW / CFG / tender owners | Affected method selection/submission/authorization. |
| LAW-V-004 | Define cumulative low-value/anti-splitting identity, period, source scope, adjustments and duplicate treatment across Plan versions/proceedings. | LAW / CFG / PLN / REQ | Affected cumulative method checks. |
| LAW-V-005 | Resolve schedule minima/maxima, calendar/working days, endpoints, holidays and exceptions; separate internal buffers. | LAW / CFG | Affected procedure schedule readiness. |
| LAW-V-006 | **Partly resolved in v1.2:** Planning uses eligible current complete APP value; actual achievement uses applicable actual procurement value; Budget remains a ceiling. Still resolve current-edition applicability, qualifying categories, ownership/origin evidence, overlap and the separate county basis. | LAW / CFG / PLN / downstream eligibility | Planning formula may be implemented only with the exact verified rule; production AGPO/category and county-support claims remain gated by the unresolved parts. |
| LAW-V-007 | Verify entity-specific procurement approval route and DPP recipient/receipt mapping; retain HOPF signature and AO accountability. | LAW / CFG / AUTH / PLN | Affected governance transitions and authority configuration. |
| LAW-V-008 | Verify Treasury submission/publication prerequisites, exemptions, exact recipient and current electronic operating model, including SRC-05's referenced and subsequent directions. | LAW / product / architecture / publication | Production publication and government e-procurement operating claims. |
| LAW-V-009 | Verify each LAW-OB timing/format, required data and permitted external operating procedure where KenTender support is deferred. | LAW / reporting / operational owners | Claim of fulfilling the particular reporting obligation. |
| LAW-V-010 | Resolve candidate scheme entitlement, preference margins, origin/shareholding equality boundaries and exclusive-preference applicability. | LAW / CFG / evaluation owners | Downstream eligibility/evaluation use; no Planning substitute. |
| LAW-V-011 | Reconcile DSP institutional approval routes, statutory timing, revision authority, disposal grounds, transfer scope, valuation and committee controls. | LAW / DSP | Disposal governance/implementation. |
| LAW-V-012 | Prove matching Budget/Need/Strategy/Requisition/Tender/provider schemas, atomicity, precision, evidence and actual implementation. | Module owners | Affected integration verification and release; legal wording alone is not implementation evidence. |

An unresolved mandatory rule blocks its affected positive action with a specific configuration/readiness explanation. Development and isolated test scenarios may proceed within their explicit boundaries. No blanket statement that these items “do not block Phase 0–3” can replace a dependency-specific gate.

For each resolved rule retain: instrument ID and edition, provision, source URL/document identity and hash where held, effective interval, applicability inputs, controlling interpretation, reviewer/evidence, exact configured rule version and tests. Preserve superseded versions and the rule selected by each historical decision. Do not repurpose today's rule to rewrite past approval evidence.

## 11. Full v1.1 change register

| ID | v1.0 defect or overstatement | Replacement in v1.1 | Owner / target | Verification |
|---|---|---|---|---|
| LAW11-CHG-001 | Blanket full-read/current-correctness claims. | Named sources, retrieval limitations, review dispositions and explicit current-law gate. | §§1, 10; LAW | AC-001 |
| LAW11-CHG-002 | Reorganized mappings called verbatim. | Analytical labels; distinguish source, interpretation and product decisions. | §§1–2, 7; document owner | AC-002 |
| LAW11-CHG-003 | Sixteen-column heading followed by seventeen “columns.” | VF-01 and separate guidance-note Status; final current export mapping open. | §2; LAW/PLN | AC-003 |
| LAW11-CHG-004 | Ambiguous timing fields and variance signs. | Distinct date lateness, forecast error and same-activity duration variance; explicit endpoint mapping. | §2.2; PLN/reporting | AC-004 |
| LAW11-CHG-005 | Actual dates assumed per item regardless of proceedings. | Exact proceeding evidence, correctable events and named unavailable integrations. | §§2.2, 9; PLN/TPR/TPUB | AC-005 |
| LAW11-CHG-006 | HOPF preparation equated with Planner submission. | Explicit HOPF signature, Planner consolidation, AO accountability/adoption and statutory approval. | §3; PLN/AUTH/KT-STD | AC-006 |
| LAW11-CHG-007 | Missing AO preparation/departmental-recipient reconciliation. | VF-02 and explicit routing/receipt mapping; no invented extra approval stage. | §3.1; LAW/PLN | AC-007 |
| LAW11-CHG-008 | Council treated as absent from current CFG. | Recognize v0.9; complete mandatory inputs, surfaces and collective authority evidence. | §§3.1, 9.2; CFG | AC-008 |
| LAW11-CHG-009 | Method label list treated as complete legal admissibility. | Separate reporting catalogue, statutory method conditions and implemented procedure support. | §4.1; LAW/CFG | AC-009 |
| LAW11-CHG-010 | Selected threshold table called authoritative full matrix. | Preserve pending figures and flag omitted rows, condition/version checks and exact boundaries. | §4.2; LAW/CFG | AC-010 |
| LAW11-CHG-011 | Low-value cumulative control confined to Plan lines. | Exact annual cumulative identity across relevant proceedings and successor deduplication. | §4.2; LAW/REQ/PLN | AC-011 |
| LAW11-CHG-012 | Broad preference categories mixed with annual target eligibility. | Distinct statutory bases, annual denominator, category and county-overlap questions. | §5.1; LAW/CFG/BUD | AC-012 |
| LAW11-CHG-013 | Highest advantage incorrectly assigned to Planning. | Planned designation/restrictions only; candidate entitlement/evaluation downstream. | §5.2; PLN/evaluation | AC-013 |
| LAW11-CHG-014 | Preference thresholds/margins treated as ready constants. | Pending conditional rules, exact boundaries and downstream ownership. | §5.3; LAW/CFG | AC-014 |
| LAW11-CHG-015 | Lotting described as having one exclusive statutory purpose. | Participation-oriented rationale retained without erasing other packaging grounds or anti-splitting. | §5.3; PLN/tender owners | AC-015 |
| LAW11-CHG-016 | “Six” reporting duties with eight rows and no stable IDs. | LAW-OB-001–008 with actor, recipient, timing, owner and evidence; no universal deadline inference. | §6.1; reporting | AC-016 |
| LAW11-CHG-017 | Treasury/website/State Portal duties could be conflated. | Distinct evidence and production destination gate; internal activation is not an external fact. | §6.2; publication | AC-017 |
| LAW11-CHG-018 | E-procurement integration/plan-upload duties absent. | VF-03, VF-05 and LAW-OB-009; establish permitted KenTender/E-GPS operating model. | §6.3; architecture/LAW | AC-018 |
| LAW11-CHG-019 | AO-only disposal approval inferred universally from form. | VF-04; full institution-specific statute/regulation/format reconciliation. | §7.2; DSP/LAW | AC-019 |
| LAW11-CHG-020 | Flexibility interpreted as prohibition of immutable history. | Governed revisions may accommodate change while preserving evidence; DSP defines authority. | §7.2; DSP | AC-020 |
| LAW11-CHG-021 | Disposal grounds, reserve-price and transfer conclusions too broad. | Preserve citations with specific unresolved classifications/procedures; withdraw automatic below-market inference. | §7.3; DSP/LAW | AC-021 |
| LAW11-CHG-022 | Financial reservation and one Finance decision called statutory mandates. | Distinguish funds obligation, preference allocation and approved system transaction/review design. | §§3.2, 8; BUD/PLN/REQ | AC-022 |
| LAW11-CHG-023 | Need workflow called legally insignificant by absence of a named provision. | Internal product workflow distinguished from underlying statutory need/planning duties. | §8; NDS | AC-023 |
| LAW11-CHG-024 | BUD/NDS “No change” and stale module versions. | Current inspected baselines and explicit coordinated provider amendments; STR compatibility and TPUB caller included. | §9; module owners | AC-024 |
| LAW11-CHG-025 | Deferred facilities and document approval could imply legal completion. | Specific gates, retained external responsibilities and rule-level proof; no test-to-production verification promotion. | §§1.4, 6, 10; all owners | AC-025 |
| LAW11-CHG-026 | Later-Need protection could be mistaken for statutory ban on every downstream change. | Label permanent scope lock as conservative MVP decision; separate-item route and future lawful downstream procedures. | §3.3; PLN/REQ/tender owners | AC-026 |

Verification IDs abbreviate `LAW11-AC-`. Original P1–P11 and C1–C3 remain mapped in §9; no old instruction is silently dropped or treated as already implemented.

### 11.1 v1.2 correction register

| ID | v1.1 problem | Replacement in v1.2 | Owner / target | Verification |
|---|---|---|---|---|
| LAW12-CHG-001 | The approved Budget, including unused headroom, was treated as the 30% Planning denominator. | Adopt eligible value of the exact current complete APP for Planning; retain approved Budget as a separate ceiling. | §5.1; PLN/CFG/BUD | LAW12-AC-001–002 |
| LAW12-CHG-002 | Plan allocation and actual achievement were not expressed as two owner-specific measures. | Planned allocation uses APP estimates; actual achievement uses authoritative downstream actual procurement values. | §§5.1, 9–10; PLN/reporting | LAW12-AC-003 |
| LAW12-CHG-003 | A current-APP formula lacked explicit protection against omission and later amendment. | Require complete expected procurement coverage, evidenced item applicability and successor recalculation while preserving historical snapshots. | §5.1; PLN | LAW12-AC-004 |
| LAW12-CHG-004 | Correcting the planning formula could be mistaken for resolving category, overlap, county and current-law questions. | Mark LAW-V-006 partly resolved only; retain the named production gates. | §§1, 5.1, 10 | LAW/CFG/downstream owners | LAW12-AC-005 |

## 12. Acceptance and adoption

| ID | Required result |
|---|---|
| LAW11-AC-001 | Every current-law assertion distinguishes inspected edition from current applicability; retrieval failures and missing amendment checks remain explicit. |
| LAW11-AC-002 | No analytical table is labelled verbatim; legal evidence, interpretation and KenTender decision are distinguishable. |
| LAW11-AC-003 | Historical 16-column grid and separate Status guidance are accurately distinguished; production format compliance requires completed current mapping. |
| LAW11-AC-004 | Timing comparisons have named endpoints/bases and distinct signs; export does not interchange dates and durations. |
| LAW11-AC-005 | Actuals retain proceeding lineage and correction history; unsupported actuals/fulfilment are never fabricated. |
| LAW11-AC-006 | Planner cannot substitute for HOPF signature; AO and applicable statutory authority remain explicit. |
| LAW11-AC-007 | Departmental submission/receipt and consolidated preparation responsibilities are reconciled without adding an unsupported approval stage. |
| LAW11-AC-008 | CFG's existing route ownership is recognized; first-run route/county controls and collective authority evidence are complete in the matching amendment. |
| LAW11-AC-009 | A method label cannot by itself authorize an unsupported or inadmissible procedure. |
| LAW11-AC-010 | No inherited threshold is marked currently Verified without exact source/applicability evidence; the selected table is not called complete. |
| LAW11-AC-011 | Cumulative method control has a verified scope/identity and cannot be evaded or duplicated through Plan versions or split rows. |
| LAW11-AC-012 | Annual allocation, actual procurement value and county obligations retain their correct bases; missing mandatory configuration/shortfall blocks the affected positive action. |
| LAW11-AC-013 | Planning does not calculate candidate highest-advantage entitlement. |
| LAW11-AC-014 | Exclusive preference/margins use verified conditions and equality boundaries in their owning modules. |
| LAW11-AC-015 | Lotting does not become an uncontrolled exception to anti-splitting. |
| LAW11-AC-016 | Each LAW-OB row has an actor, recipient, trigger/period, owner and evidence; deadlines are not copied to unrelated obligations. |
| LAW11-AC-017 | Treasury, website, State Portal and internal activation remain distinct and independently evidenced. |
| LAW11-AC-018 | Electronic-system/portal duties and SRC-05 are in the production operating-model review; no unsupported independent replacement-platform assumption. |
| LAW11-AC-019 | DSP approval cannot be configured as universally AO-only from the signature block alone. |
| LAW11-AC-020 | Disposal flexibility does not authorize silent overwrite or prohibit auditable governed revisions. |
| LAW11-AC-021 | Disposal valuation, grounds, licensing and transfer questions retain source-specific verification rather than broad inherited conclusions. |
| LAW11-AC-022 | Financial reservation timing and repeat Finance reviews are labelled product controls; statutory preference reservation is a distinct concept. |
| LAW11-AC-023 | Needs' internal workflow does not erase departmental statutory planning duties. |
| LAW11-AC-024 | Every original P/C item and affected provider has an explicit disposition; this file does not claim to amend sibling documents or code. |
| LAW11-AC-025 | Approval, fixture verification, legal verification, implementation and release remain distinct; unresolved mandatory rules block their affected actions. |
| LAW11-AC-026 | The later-Need MVP guard remains effective without falsely asserting that no lawful downstream change procedure could ever exist. |

| LAW12-AC-001 | The source phrases, KenTender interpretation and implementation formula are visibly distinct; the document does not falsely quote “eligible current APP value” as statutory text. |
| LAW12-AC-002 | The 30% Planning denominator excludes unused Budget headroom and records the exact current complete APP and rule Versions. |
| LAW12-AC-003 | Actual achievement is calculated from authoritative actual procurement facts, never inferred from planned estimates. |
| LAW12-AC-004 | Every expected current Plan Item is covered or explicitly excluded under the verified rule, and an approved amendment recalculates the successor snapshot without rewriting history. |
| LAW12-AC-005 | Current-edition applicability, qualifying categories, evidence, overlap and county basis remain blocked until their specified verification is complete. |

LAW-REG-001 v1.2 is proposed for Project Owner approval. Approved v1.1 remains the controlled register until approval is recorded. On approval, v1.2 will retain every v1.1 correction and owner disposition except the superseded 30% denominator instruction, and LAW12-CHG-001–004 / LAW12-AC-001–005 will govern that correction.

Approval will not close LAW-V-001–005 or LAW-V-007–012, fully close LAW-V-006, mark configuration Verified, approve production deployment or certify the completeness of deferred reporting. Each item closes only on its specified evidence. Retain v1.0, approved v1.1 and this proposed successor's history as part of the controlled document record.
