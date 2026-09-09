# STD-TPL-001 - IT Equipment Tender Template Curation and Release Pack

| Control | Value |
|---|---|
| Document ID | STD-TPL-001 |
| Version | 0.4 |
| Date | 4 September 2026 |
| Status | Proposed for curation review |
| Template key | `IT-EQUIPMENT-OPEN-V1` |
| Template version | 1.1 |
| Official STD family | PPRA Standard Tender Document for Procurement of Goods |
| Product use | Straightforward off-the-shelf IT equipment and related delivery services |
| Controlling decision | STD-ST-001 v0.3 - Approved |
| Standards | Governed by STD-STD-001 v1.1 for the three-layer separation, the parameter rule, the six content classes, the placeholder lifecycle, curation anti-patterns, the two-output rule, preference/reservation and lotting treatment, the forms/attachments hybrid rule, and shared-fixture discipline. Sections not restated here are inherited from it. |
| Tender Preparation consumer | TPR-CHG-001, after this template and its version 1.1 correction are approved |
| Implementation authority | None |
| Change type | **This is the version 1.1 correction TPR-CHG-001 v0.4 §6.2 required and that has not existed until now.** Replaces the PDF-primary technical specification with structured data inherited from the authorised Requisition; adds the preference/reservation and lotting treatment STD-STD-001 §8–9 require; renames the golden fixture from Kenya Bureau of Standards to Ministry of Health, per SEED-001 v1.0. Domain scope — Open Tender, one award package, IT goods and closely related services — is unchanged. |

## 1. Purpose

This document defines the complete first KenTender tender template.

It answers five practical questions:

1. Which official document is being implemented?
2. Which parts remain fixed, and which values change for a Tender?
3. What must KenTender render, validate and collect from suppliers?
4. What evidence is required before the template can be released?
5. What is published as the Invitation notice, and what forms the issued Tender document?

This is the missing curation step between the approved product direction and Tender Preparation.

It is not an STD Configuration module. The template is prepared once by the KenTender product team, reviewed against the official source and shipped as a controlled software release. Procurement Officers use it; they do not configure it.

## 2. Binding decisions

The first template is deliberately narrow.

| Decision | First release |
|---|---|
| Procurement category | Goods - IT equipment |
| Procurement method | Open Tender |
| Typical use | Laptops, desktops, tablets, peripherals and closely related delivery services |
| Award package | One |
| Tender currency | One |
| Technical assessment | Pass/fail compliance |
| Financial assessment | Lowest evaluated responsive Tender, subject to the approved official rules |
| Standard text | Fixed and read-only |
| Tender-specific data | Five plain-language officer tasks |
| Technical specifications | Structured technical requirement rows inherited from the authorised Requisition, rendered directly into Section V — no controlled PDF |
| Template maintenance | Code-owned release; no Desk editor |

The template must reject:

- software implementation, integration or data-migration projects;
- construction or other WORKS;
- consulting and non-consulting services;
- several award packages, or a lotting indicator other than **Single lot**;
- a reservation category with no rendering rule stated in §6 below;
- weighted technical scoring;
- several Tender currencies;
- a procurement method not covered by this release; and
- a Requisition with no structured technical requirement rows.

Complex IT systems will use a later, separate product template. The PPRA Information Technology STD and the earlier nine-step IT Wizard remain source material for that later product; they are not the legal base for this equipment template.

## 3. Source record

The template cannot be released from a title or an unverified copy. The curation folder must contain one exact official source file downloaded from the [PPRA Standard Tender Documents register](https://ppra.go.ke/standard-tender-documents/).

The release record must contain:

| Source fact | Required value |
|---|---|
| Official title | Exact title printed in the source file |
| STD family | Procurement of Goods |
| Published revision or issue date | Exact date printed in the source, if present |
| Download filename | Exact downloaded filename |
| Source URL | Direct official source or PPRA register URL |
| Retrieved on | Actual retrieval date |
| File digest | SHA-256 of the downloaded source file |
| Reviewed by | Named procurement/legal reviewer |
| Review date | Actual review date |

These values are not to be guessed. An absent issue date is recorded as **Not stated in source**, not invented.

The supplied KEBS Tender is a comparison and fixture source. It is not the legal master. Its current file digest is:

`43b574af051ffa4db926dc3820e971b7defe04c1f6a68b242446df747da5f26b`

The KEBS example confirms the modern Goods STD structure, exposes practical completion problems and provides realistic equipment content. Its entity-specific wording and mistakes must not be copied into the product template.

## 4. What is actually curated

The product team curates seven finite items.

| Item | Result |
|---|---|
| 1. Official source | One verified PPRA Goods STD file and digest |
| 2. Base document | Complete official structure with fixed text preserved and authoring instructions removed |
| 3. Data dictionary | Only the Tender values that genuinely change |
| 4. Fixed schedules | Goods/delivery, related services and supplier price schedule |
| 5. Forms and responses | Official forms, declarations and evidence requirements required by this pattern |
| 6. Rules and renderer | Completeness, consistency, calculation and placement rules |
| 7. Proof | Coverage register, Ministry of Health golden fixture, complete preview, tests and approvals |

The issued Tender should remain one coherent reviewed document. Its separate Invitation notice is short and uses the same approved Tender data. KenTender must not create a database record for every clause or paragraph.

### 4.1 Exact curation workspace

Claude must work from the `frappe-bench/apps/kentender_v1` repository root and create this review folder:

```text
docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1/
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
│   ├── moh_invitation_expected.html
│   ├── moh_invitation_expected.pdf
│   ├── moh_expected.html
│   ├── moh_expected.pdf
│   └── package_index.md
└── 05_review/
    ├── open_issues.md
    └── review_record.md
```

No other curation format or folder is permitted unless this document is revised first.

#### File purposes

| File | Exact purpose |
|---|---|
| `ppra_goods_std_official.pdf` | Byte-for-byte copy of the selected official source |
| `ppra_goods_std_official.txt` | Layout-preserving text extraction used only to help prepare the draft |
| `source_record.md` | Official title, issue date, original filename, URL, retrieval date and SHA-256 |
| `pages/` | One image per official PDF page for visual comparison |
| `invitation_to_tender.html` | The separate Invitation notice master; it is not included in the issued Tender document |
| `complete_tender.html` | The authoritative issued Tender master, from its cover and contents through Section VIII |
| `print.css` | Shared print layout used by both masters and their fixtures |
| `coverage_register.csv` | One row for every official heading, table, form and insertion instruction |
| `insertion_points.csv` | One row for every permitted Jinja value, condition or repeated row |
| `forms_register.csv` | One row for every official form and its treatment |
| `moh_input.json` | Exact test data used to complete the working master, including the structured technical requirement rows — no controlled specification file, per §8.4 |
| `render_fixture.py` | Curation-only strict Jinja renderer for both outputs; it is never imported by KenTender |
| `moh_invitation_expected.html` | Fully resolved separate Invitation notice fixture |
| `moh_invitation_expected.pdf` | Human-review copy of the separate Invitation notice |
| `moh_expected.html` | Fully resolved fixture with no Jinja or drafting instructions left |
| `moh_expected.pdf` | Human-review copy rendered from `moh_expected.html` |
| `package_index.md` | Lists the separate Invitation notice and every file in the issued Tender package, without treating the notice as part of that package |
| `open_issues.md` | Unresolved source or policy decisions; an open blocking item stops work |
| `review_record.md` | Named review results and the final curation decision |

#### Fixed authoring format

`invitation_to_tender.html` and `complete_tender.html` are the only working-master files. Both must be valid UTF-8 HTML. They may use Jinja only for named Tender values and approved conditions. Only `complete_tender.html` may use the two repeated structures: goods rows and related-service rows.

Use these patterns:

```html
<span>{{ tender.title }}</span>

{% if tender.pre_tender_meeting.enabled %}
  <p>{{ tender.pre_tender_meeting.details }}</p>
{% endif %}

{% for item in goods %}
  <tr>
    <td>{{ loop.index }}</td>
    <td>{{ item.description }}</td>
    <td>{{ item.quantity }}</td>
    <td>{{ item.unit }}</td>
    <td>{{ item.destination }}</td>
    <td>{{ item.latest_delivery_date }}</td>
  </tr>
{% endfor %}
```

Rules:

- copy fixed official wording into the HTML; do not paraphrase it;
- keep the official section order, numbering, headings, tables and forms;
- use semantic HTML tables, headings, paragraphs, lists and page breaks;
- use only insertion keys recorded in `insertion_points.csv`;
- use no custom Jinja filter or function;
- do not put calculations, database calls, permission checks or business decisions in Jinja;
- do not embed JavaScript;
- do not create a DOCX master, Markdown master, clause JSON file or another template representation;
- never include or import `invitation_to_tender.html` inside `complete_tender.html`; and
- do not connect this folder to Frappe while the curation review is incomplete.

The text extraction and page images are authoring aids. They do not replace comparison with the official PDF.

## 5. Complete source coverage

Every official section must have a recorded treatment. A section does not disappear because it is fixed or completed after Tender submission.

| Official Goods STD area | KenTender treatment | Main source |
|---|---|---|
| Invitation to Tender | Separate generated publication notice; not included in the issued Tender document | `invitation_to_tender.html` |
| Section I - Instructions to Tenderers | Locked official text; no routine data entry | Released base document |
| Section II - Tender Data Sheet | Generated from inherited facts, officer decisions and fixed release choices | Tasks 1, 4 and 5 |
| Section III - Evaluation and Qualification Criteria | Fixed pass/fail and financial sequence plus the visible evidence checklist | Task 4 |
| Section IV - Tendering Forms | Locked official wording with known identities prefilled and supplier fields left for supplier response | Supplier package |
| Section V - Schedule of Requirements | Goods/delivery rows, related services, approved technical specification and inspection/acceptance treatment | Task 2 and Requisition |
| Section VI - General Conditions of Contract | Locked official text; no routine data entry | Released base document |
| Section VII - Special Conditions of Contract | Generated from finite contract values and fixed release choices | Task 5 |
| Section VIII - Contract Forms | Included in the published Tender; Tender, award or contract values are filled at their proper stage | Supplier, award and contract outputs |

### 5.1 Two outputs, one approved Tender Version

Consistent with ITT 5.2 in the selected Goods STD, the template produces two coordinated outputs:

1. **Invitation to Tender** - the public notice that tells suppliers the opportunity exists and how to access and submit the Tender; and
2. **Issued Tender document** - the document containing Sections I to VIII, with its own cover and contents.

The Invitation is not a section of the issued Tender document. It must not appear in `complete_tender.html`, its contents page or `moh_expected.pdf`.

Both outputs use the same approved Tender Version. Tender reference, title, Procuring Entity, method, clarification deadline, submission deadline, electronic access channel and Tender-security treatment must agree. The officer enters or confirms each value once.

### 5.2 Coverage register rule

For each heading, table, form and active insertion instruction in the official source, the curation register records:

- source section and heading;
- one treatment: **Locked**, **Inherited**, **Officer value**, **Generated**, **Supplier response**, **Award-derived**, **Governed document** or **Not used by this released pattern**;
- the owning field, schedule, document or fixed decision;
- whether it appears in the separate Invitation notice, the issued Tender document or another controlled package file;
- the applicable readiness check; and
- the reviewer result.

**Not used** requires a short reason and proof that the official source permits the selected treatment. It must not be used to hide an unresolved prompt.

## 6. Fixed release choices

The curation team must settle the following choices once for Version 1.0. They are not shown as configuration controls to a Procurement Officer.

| Release choice | Required treatment |
|---|---|
| Official source version | Record the exact file and digest before release |
| National or international open Tender | Choose the supported form and reject the other |
| Electronic submission and opening | Align the document with the actual KenTender publication/submission service; remove physical-envelope instructions when they do not apply |
| One award package, single lot only | This release renders the lotting indicator from the inherited Plan Item and confirms it reads **Single lot**. A `Packaged into lots` Requisition is incompatible in this release and is named in the rejection list in §2; supporting multiple lots is a later template version, per STD-STD-001 §9. |
| One currency | Set the permitted Tender currency treatment and render it consistently |
| Alternative Tenders | Not permitted in this first pattern |
| Price adjustment | Prices fixed in this first pattern |
| Evaluation model | Pass/fail responsiveness and technical compliance, then financial evaluation |
| Margin of preference or reservation | The inherited `reservation_category` and, where the tender's value and funding qualify, the margin of preference under regulation 164, render in Section III's Evaluation and Qualification Criteria per STD-STD-001 §8. `None` renders no additional criterion. A Requisition whose reservation category has no rendering rule in this release is incompatible and is named in the rejection list in §2. |
| Official form variants | Select the permitted Tender security, performance security and other form variants; do not publish unused competing forms as active choices |
| Publication contact and submission instructions | Source from governed PE/platform data, not free text repeated in several places |
| Invitation publication | Generate it as a separate notice; do not place it inside the issued Tender document |

An unresolved release choice blocks the template. It must not become an officer field merely to move the decision downstream.

### 6.1 Resolved Version 1.0 treatments

The curation already settled these source blanks and alternatives:

| Source issue | Version 1.0 treatment |
|---|---|
| Invitation document-inspection office/hours | Replace with the governed electronic access and clarification channel; no officer field |
| Invitation authorised-official block | Generate from the approved publication record and governed PE data; no wet-signature field |
| e-Procurement system identity | Use the governed KenTender name, address and reviewed description; no officer field |
| TDS ITT 3.11 registration requirement | Render the reviewed fixed treatment **Not applicable** for this product template |
| Tender-Securing Declaration | Not used because this released pattern requires monetary Tender Security |
| Advance payment | Fixed at 0%; exclude the Advance Payment Security form and align the SCC |
| Tender Security instrument | Supplier chooses among the instruments permitted by the TDS; keep both official Demand Bank Guarantee and Insurance Guarantee forms available |
| Invitation location | Separate publication notice under section 5.1; absent from the issued Tender document |
| Reservation category rendering, per STD-STD-001 §8 | `None` renders no additional criterion. `Youth`, `Women`, `Persons with disabilities` and `Other disadvantaged group` each render one fixed eligibility clause in Section III, naming the category and citing regulation 149. `Micro, small and medium enterprise` and the regional and national-citizen-contractor categories are **not supported in this release** — a Requisition carrying one of them is incompatible per the rejection list in §2, until a later template version adds their more involved eligibility and verification language. |

These are template-release decisions, not new Procurement Officer questions.

## 7. Tender data dictionary

Each value below has a visible purpose. Nothing else is added without showing where it renders, what it validates or what it feeds.

### 7.1 Inherited from the authorised Requisition

| Value | Use |
|---|---|
| Procuring Entity and entity reference | Invitation, TDS, forms and contract |
| PE contact office | Clarification, submission and contract notices |
| Plan Item and Requisition references | Audit and internal lineage; not unnecessary public text |
| Procurement method | Template compatibility and Tender wording |
| Requirement title | Default Tender title |
| Authorised quantity | Quantity reconciliation |
| Authorised value | Scope/change control; not disclosed unless required |
| Expected delivery date | Latest permitted delivery |
| Approved technical specification | Section V and supplier compliance response |
| Approved related-service need | Determines whether related-service rows are allowed |

Tender Preparation cannot alter these values. A material correction returns to the upstream process.

### 7.2 Entered or confirmed by the Procurement Officer

| Task | Value | Purpose |
|---|---|---|
| Tender details | Clear Tender title | Invitation and all Tender references |
| Tender details | Issue date | Invitation and publication |
| Tender details | Clarification deadline | TDS and publication |
| Tender details | Submission deadline | Invitation, TDS and opening |
| Tender details | Tender validity in days | TDS, form and security checks |
| Tender details | Tender security treatment | TDS and the applicable official form |
| Tender details | Security currency and amount | TDS and supplier security requirement |
| Tender details | Pre-tender meeting decision and details | Invitation/TDS when used |
| Goods and delivery | Goods description | Schedule of Requirements and price schedule |
| Goods and delivery | Quantity and unit | Schedule, price calculation and Requisition check |
| Goods and delivery | Delivery location | Schedule, pricing and contract |
| Goods and delivery | Latest delivery date | Schedule and contract |
| Goods and delivery | Minimum warranty | Specification, evidence and SCC |
| Goods and delivery | Related service, location and completion date | Related-services and price schedules |
| Price schedule | Currency | Supplier price schedule and evaluation |
| Price schedule | Fixed-price confirmation | TDS and SCC |
| Price schedule | Tax display treatment | Price form and total |
| Submission/evaluation | Manufacturer authorisation required | Evidence checklist and official form |
| Submission/evaluation | Datasheet or brochure required | Evidence checklist |
| Submission/evaluation | Comparable supply experience, if justified | Qualification evidence |
| Submission/evaluation | After-sales support evidence, if justified | Qualification/technical evidence |
| Submission/evaluation | Additional evidence linked to a visible requirement | Evidence checklist |
| Contract terms | Payment timing | SCC |
| Contract terms | Performance security treatment and percentage | TDS/SCC and form |
| Contract terms | Delay damages rate and cap | SCC |
| Contract terms | Inspection and acceptance office/location | Section V and SCC |
| Contract terms | Contract contact office | SCC and contract notices |

### 7.3 Generated values

| Generated value | Source |
|---|---|
| Tender reference | Tender record naming rule |
| Opening date/time | Submission deadline where the released process uses immediate electronic opening, otherwise the fixed opening rule |
| Security validity date | Submission deadline, Tender validity and the official extra period |
| Delivery summary | Goods and related-service rows |
| Price rows | Goods and related-service rows |
| Line totals, subtotal, taxes and Tender total | Supplier prices and released calculation rule |
| Form identities | Tender, PE and supplier data |
| Invitation notice, issued Tender and package digests | Approved Tender Version and released template |

Generated values cannot be independently edited.

## 8. Fixed schedules and documents

### 8.1 Goods and delivery schedule

The officer completes one table.

| Column | Entered by | Rule |
|---|---|---|
| Item number | System | Stable row order |
| Goods description | Officer | Plain and supplier-readable |
| Quantity | Officer | Total agrees with the Requisition |
| Unit | Officer | Governed unit list |
| Final destination | Officer | Required |
| Latest delivery date | Officer | Not later than the authorised date |
| Minimum warranty | Officer | Required for this pattern |
| Offered delivery date | Supplier | Supplier response; not completed by Procurement |

The approved technical specification remains a controlled document. KenTender does not require the officer to retype its component-by-component content.

### 8.2 Related services schedule

This table appears only when the authorised need includes installation, testing, configuration or training closely related to the supplied equipment.

| Column | Treatment |
|---|---|
| Service number | Generated |
| Service description | Officer, consistent with the Requisition |
| Quantity and unit | Officer |
| Place of performance | Officer |
| Completion date | Officer, within the authorised delivery boundary |
| Supplier price | Supplier response |

If services become the main purpose or require substantial implementation, the Requisition is not compatible with this template.

### 8.3 Price schedule

The system creates one supplier price row for every goods and related-service row. It does not ask the officer to create the same lines again.

| Price value | Treatment |
|---|---|
| Item/service identity and quantity | Generated from Task 2 |
| Unit price | Supplier response |
| Line total | Calculated |
| Subtotal | Calculated |
| Applicable levy/tax rows | Released calculation rule or governed rate source |
| Tender total | Calculated once and carried to the Form of Tender |

The same calculated total must appear in the supplier response, evaluation view, Form of Tender and contract handoff.

### 8.4 Technical specification, inherited as structured data

**Corrected — this is the version 1.1 change.** Version 1.0 treated the technical specification as an approved PDF the Tender named and republished. That model is retired. It duplicated the same specification facts in two independently-maintained places — the PDF and, unavoidably, the schedule rows rendered beside it — which is exactly the failure mode STD-ST-001's own three-layer separation exists to prevent. There is no fourth layer; a specification is either locked text, finite data, or a governed project artifact, and quantities, units, warranty periods and technical requirement rows are finite data, not an attachment's metadata.

The corrected treatment:

1. Tender Preparation receives, from the authorised Requisition handoff, one or more stable-ID technical requirement rows — each carrying its requirement text, quantity, unit and any structured attribute the pattern's data dictionary defines (processor class, memory, storage, warranty period, and equivalent).
2. `complete_tender.html` renders Section V's Schedule of Requirements directly from these rows, grouped by requirement where several rows share one specification, exactly as REQ-CHG-001 and TPR-CHG-001 already require.
3. No PDF, cover sheet, publication filename or file digest is required for the technical specification. If the originating department also produced a supporting document (drawings, a detailed technical brief), that document is a governed project artifact under STD-STD-001 §2 — referenced by the Requisition, never re-authored or renamed here, and never the thing Section V is generated *from*.
4. Every rendered row's quantity, unit and technical attribute is traceable by stable ID back to its originating Requisition drawdown line and, beyond that, to the Plan Item and source Need or DPP entry — the same immutable lineage BUD-CHG-001, PLN-CHG-001 and REQ-CHG-001 already require.
5. Supplier technical compliance is collected against the published rows, one structured response per technical requirement ID; the Procurement Officer does not recreate or duplicate the specification during Tender Preparation, and does not upload a competing document that could disagree with the rendered rows.

The controlled document has:

- title;
- version;
- authoring department or competent technical officer;
- approval status and date;
- file digest; and
- publication filename.

Readiness checks that the document is present, is a readable PDF, has Approved status, has an approval date and digest, and contains no unresolved drafting instructions. Product or model references must use an approved equivalent treatment or carry an approved justification. KenTender does not attempt to model every processor, port or warranty statement as a template parameter.

## 9. Evaluation and supplier response

### 9.1 Fixed evaluation sequence

The first template uses four stages:

1. submission and eligibility;
2. pass/fail technical compliance;
3. arithmetic and financial evaluation; and
4. award under the approved lowest-evaluated-responsive rule.

There is no weighted scoring screen and no criterion builder.

### 9.2 Baseline supplier package

The published package must account for the applicable official forms and responses, including:

- Form of Tender;
- Certificate of Independent Tender Determination;
- required self-declarations and code-of-ethics commitment;
- Tenderer Information and eligibility/business questionnaire;
- joint-venture information only when permitted and used;
- the applicable Tender security form or declaration;
- manufacturer authorisation only when required;
- goods technical-compliance response;
- goods and related-service price schedules; and
- required evidence uploads or references.

Known Tender and supplier identity values should be captured once and reused. Official declaration wording remains locked. The supplier explicitly confirms or signs it; KenTender does not preselect an answer on the supplier's behalf.

### 9.3 Tender-specific evidence

The officer may require only the finite evidence allowed by TPR-CHG-001:

- manufacturer authorisation;
- datasheets or brochures;
- warranty confirmation;
- a defined number of comparable supply contracts over a defined period;
- stated after-sales support evidence; and
- a short additional evidence item linked to a visible published requirement.

Every evidence item must state the requirement it proves. An unexplained certificate checklist fails curation review.

## 10. Contract treatment

The General Conditions remain fixed. The Special Conditions contain only the values needed for this pattern.

| Contract area | Source |
|---|---|
| Procuring Entity and notices | Governed PE data |
| Goods, destination and delivery | Approved schedule |
| Shipping or delivery documents | Fixed release choice plus any justified item-specific document |
| Price adjustment | Fixed as not adjustable for Version 1.0 |
| Payment | Officer selection within the released choices |
| Performance security | Officer selection and percentage within the released choices |
| Packing and marking | Fixed template treatment or visible goods requirement |
| Insurance and transport | Fixed Incoterms/release treatment |
| Inspection and tests | Approved technical specification and officer acceptance location |
| Delay damages | Officer rate and cap within released limits |
| Warranty and replacement period | Goods rows plus released SCC wording |
| Contract contact | Governed office, not a person's private contact |

Award-derived values are not requested from the Procurement Officer merely to remove a placeholder. Supplier name, final Contract Price and other award results are filled during award or contract formation.

Section VIII contract forms remain in the complete package. Their wording is fixed; their values are populated at the correct stage.

## 11. Render specification

The renderer must produce two outputs.

### 11.1 Separate Invitation notice

`invitation_to_tender.html` must render a short publication notice containing:

1. Procuring Entity name and governed public contact;
2. Tender reference and title;
3. procurement method and any approved eligibility statement;
4. the governed KenTender access address and submission channel;
5. clarification deadline and governed clarification channel;
6. submission deadline;
7. the Tender-security summary when it applies; and
8. the authorised publication record or governed official block.

It must not request a physical document-inspection office, physical-envelope submission, physical opening attendance or wet-ink signature merely because the source contains print-era blanks. The reviewed electronic treatment replaces those instructions.

### 11.2 Issued Tender document

`complete_tender.html` must render the issued Tender document in this order:

1. cover and Tender identity;
2. contents;
3. Section I - Instructions to Tenderers;
4. Section II - Tender Data Sheet;
5. Section III - Evaluation and Qualification Criteria;
6. Section IV - Tendering Forms;
7. Section V - Schedule of Requirements, including goods, related services, technical specification and inspections;
8. Section VI - General Conditions of Contract;
9. Section VII - Special Conditions of Contract; and
10. Section VIII - Contract Forms.

The Invitation notice is not inserted before Section I and is not listed in the contents.

### 11.3 Consistency and package rules

The technical specification renders directly into Section V from structured, stable-ID requirement rows, per §8.4. There is no separate controlled PDF, no package-index entry and no file digest for it in this release.

Before either output is accepted, automated checks must compare their shared Tender reference, title, Procuring Entity, deadlines, submission channel and Tender-security treatment. A mismatch blocks release.

`package_index.md` must distinguish:

- the **publication notice**: `moh_invitation_expected.pdf`; and
- the **issued Tender package**: `moh_expected.pdf`. There is no separate technical-specification file to list, per §8.4.

The notice may be released with the same approved Tender, but it is not a file within the issued Tender package.

The final output must not contain:

- `[insert ...]` instructions;
- ellipses standing for unresolved content;
- `Manual Input` or `Auto Populate` labels;
- unused alternative wording;
- duplicated independently maintained values;
- blank operative schedules;
- headings whose real content is missing from the package; or
- internal template keys, field names, mappings or digests in ordinary supplier-facing text.

## 12. Reuse of earlier IT work

Earlier work is reviewed content input. It is not a runtime dependency.

| Earlier IT area | First-template treatment |
|---|---|
| Tender Profile | Reuse identity, date and security concepts in Task 1 |
| Tender Data Sheet | Reuse matching Goods fields and help text after source review |
| IT Requirements | Reduce to the approved technical specification and goods/delivery schedule |
| Implementation Schedule | Reuse only delivery and small related-service concepts |
| System Inventory and Background | Exclude from this template |
| Price Schedule | Reuse goods/service row and calculation work |
| Evaluation Setup | Reuse fixed pass/fail and financial treatment; exclude arbitrary scoring |
| Forms and Evidence | Reuse official-form coverage and evidence handling after Goods STD review |
| Contract Values | Reuse matching SCC fields and carry-forward rules |
| Readiness, review and preview | Reuse successful interaction and validation lessons |
| Parser, OCR and inferred schema | Retire |
| Generic manifests and schema editors | Do not reuse |
| Legacy package activation and configuration DocTypes | Do not reuse |

The curation team uses one temporary checklist with these columns:

| Source item | Reuse, simplify, rewrite or exclude | Target section | Official-source check | Reviewer result |
|---|---|---|---|---|

The checklist is release evidence. It does not become a permanent import service.

### 12.1 Old nine areas to the new five tasks

| Earlier Wizard area | First-template destination |
|---|---|
| Tender Profile | Task 1 - Tender details |
| Tender Data Sheet | Tasks 1, 4 and 5 |
| IT Requirements | Task 2 - Goods and delivery plus technical document |
| Implementation Schedule | Task 2 related services only |
| System Inventory and Bidder Background | Not used |
| Price Schedule | Task 3 |
| Evaluation Setup | Task 4 - fixed sequence |
| Forms and Evidence | Task 4 |
| Contract Values | Task 5 |

This is a simplification of a proven pattern, not an attempt to generalise it.

## 13. Ministry of Health golden fixture

**Renamed from Kenya Bureau of Standards, per SEED-001 v1.0.** One site is one Procuring Entity; a golden fixture keyed to a second, non-existent entity cannot be run or demonstrated in the same live system as every other approved KenTender document. This is not a re-derivation of the fixture — every fact below is the same scenario, reassigned to the entity and identifiers the rest of the system already uses, per SEED-001 §5.

This remains the release's one deterministic test Tender. It is a KenTender product fixture; the historical KEBS Tender referenced in §3 remains, unchanged, the external comparison source that validated the template's structure — the two are not the same thing, and only the golden fixture is renamed here.

| Fixture item | Value |
|---|---|
| Procuring Entity | Ministry of Health |
| Plan Item | `PPI-MOH-2027-033` — Clinical training and deployment laptops for digital health rollout |
| Requisition | `REQ-MOH-2027-033-001` |
| Tender | `TND-MOH-2027-033` |
| Requirement | Supply and delivery of business laptops |
| Authorised quantity | 250 each |
| Authorised value | KES 50,000,000 |
| Expected delivery | 30 September 2027 |
| Template | `IT-EQUIPMENT-OPEN-V1` Version 1.1 |

Goods — one requirement, drawn from two Requisition lines with the same specification:

| Item | Quantity | Delivery location | Latest delivery | Warranty |
|---|---:|---|---|---:|
| Business laptops | 250 each | Ministry of Health Headquarters, Afya House, Nairobi | 30 Sep 2027 | 36 months |

Tender decisions:

- Issue date: **15 May 2027**;
- clarification deadline: **27 May 2027, 17:00 EAT**;
- submission deadline: **5 June 2027, 11:00 EAT**;
- Tender validity: **120 days**;
- Tender security: **KES 500,000**;
- pre-tender meeting: **No**;
- currency: **KES**;
- prices: **Fixed**;
- taxes: **Shown separately**;
- manufacturer authorisation: **Required**;
- datasheets or brochures: **Required**;
- comparable experience: **2 contracts in the last 5 years**;
- after-sales evidence: **Service-centre details and escalation contacts**;
- payment: **Within 30 days after delivery, inspection, acceptance and valid invoice**;
- performance security: **10% of Contract Price**; and
- delay damages: **0.5% per week, capped at 10%**.

These values test the product. A procurement/legal reviewer must still confirm that every released rule and limit agrees with the selected official source and current policy.

## 14. Exact curation procedure for Claude

This is a document-production exercise. The small fixture renderer is review tooling only; it is not KenTender implementation.

Claude must perform the following passes in order. It must stop after each gate and present the named files for human review. It must not continue merely because the files exist.

Run the pass commands from this directory:

```bash
cd docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1
```

### Pass 1 - Establish the source

1. Confirm the exact official PPRA Goods STD selected by the product owner.
2. Copy it byte-for-byte to `01_source/ppra_goods_std_official.pdf`.
3. Run:

   ```bash
   pdfinfo 01_source/ppra_goods_std_official.pdf
   sha256sum 01_source/ppra_goods_std_official.pdf
   pdftotext -layout \
     01_source/ppra_goods_std_official.pdf \
     01_source/ppra_goods_std_official.txt
   pdftoppm -png -r 150 \
     01_source/ppra_goods_std_official.pdf \
     01_source/pages/page
   ```

4. Complete `source_record.md` from the source and the download record. Do not infer a date that the source does not state.
5. Record any damaged, blank, scanned or unreadable page in `open_issues.md`.

**Gate A:** stop. The product owner confirms the official file and digest. If the file is not confirmed, do not prepare the master.

### Pass 2 - Account for the complete official document

1. Create `coverage_register.csv` with exactly these columns:

   ```text
   coverage_id,source_page_start,source_page_end,section_number,heading,item_type,treatment,owner_key,render_location,readiness_check,status,review_note
   ```

2. Read the official source from first page to last page.
3. Add one row for every:
   - cover or Invitation block;
   - numbered heading and subheading;
   - table;
   - form;
   - option or alternative wording instruction;
   - blank to be completed; and
   - instruction telling the document preparer to insert, select, delete or amend something.
4. Set `treatment` to only one of the eight values in section 5.2.
5. For **Locked**, state the target heading in `invitation_to_tender.html` or `complete_tender.html`.
6. For **Inherited**, **Officer value**, **Generated** or **Award-derived**, state the exact key that will own the value.
7. For **Supplier response**, state the official form or supplier response area.
8. For **Governed document**, state the technical-specification file or other approved document.
9. For **Not used by this released pattern**, state the source basis in `review_note`.
10. Put every unresolved choice in `open_issues.md`; do not turn it into a new field.

11. Reclassify every Invitation row against section 5.1 of this version. Its `render_location` must point to `invitation_to_tender.html`, or record why it is not used. No Invitation row may point to `complete_tender.html`.

**Gate B:** stop. A procurement-domain reviewer confirms that the register accounts for the complete source and applies the two-output boundary. Zero rows may remain unclassified.

### Pass 3 - Define every permitted insertion

1. Create `insertion_points.csv` with exactly these columns:

   ```text
   key,kind,source_treatment,source_section,owner,task,label,data_type,required,condition,validation,example,downstream_use
   ```

2. Use only these `kind` values:
   - `value` for one scalar value;
   - `condition` for one approved yes/no section;
   - `goods_rows` for the goods loop; and
   - `service_rows` for the related-services loop.
3. Start from section 7 of this document. Do not add a key just because the official STD contains a blank.
4. Resolve each blank as fixed, inherited, generated, supplier-entered, award-derived or genuinely officer-entered.
5. Use stable lower-case dotted names, for example `tender.title`, `tender.submission_deadline`, `contract.payment_days` and `technical_specification.publication_filename`.
6. A value appearing in several places keeps one key.
7. Put a proposed additional officer value in `open_issues.md`. Do not add it to the register until the product owner approves its purpose.
8. Create `forms_register.csv` with exactly these columns:

   ```text
   form_id,official_form_name,source_pages,included,variant_selected,fixed_text_complete,prefilled_keys,supplier_fields,award_fields,review_status,review_note
   ```

**Gate C:** stop. The product owner confirms the insertion list and form list. This is the field-count control point.

### Pass 4 - Build the two working masters

First build `02_master/invitation_to_tender.html` from only the rows assigned to the separate notice. Then work through the official Tender document in order and build `02_master/complete_tender.html` from the remaining applicable rows.

1. Put reviewed notice wording and its approved keys in `02_master/invitation_to_tender.html`.
2. Do not copy the Invitation notice into `complete_tender.html`.
3. Copy the issued Tender wording into `02_master/complete_tender.html`, beginning with its cover and contents and then Section I.
4. Recreate tables as HTML tables; do not paste them as images.
5. Preserve section numbering and form titles.
6. Replace an approved changing value with its exact Jinja key from `insertion_points.csv`.
7. Insert only the approved conditional blocks and the goods or related-services loops.
8. Remove document-preparer instructions from supplier-facing output only after their required action has been resolved.
9. Keep bidder instructions, declarations and legal text that suppliers must see.
10. Resolve the fixed Version 1.0 alternatives in section 6. Do not expose them as officer choices.
11. For Section V, render the goods schedule, related-services schedule when applicable, inspection/acceptance text and the controlled technical-specification cover sheet.
12. For official supplier forms, preserve the wording and leave supplier and award fields at the proper stage.
13. Add print rules only to `02_master/print.css`; do not use inline styles unless a particular table cannot otherwise retain the reviewed layout.
14. Compare both HTML outputs visually with their source pages and update the corresponding coverage rows to `Draft checked`.

Do not paraphrase unreadable text. Record it in `open_issues.md` and stop that section.

**Gate D:** stop. Reviewers compare both HTML masters with the official PDF and confirm that the Invitation is absent from the issued Tender. Every coverage row must be either `Reviewed` or a stated blocker.

### Pass 5 - Build the Ministry of Health fixture

1. Create `04_fixture/moh_input.json` using exactly the values in section 13 and the approved insertion keys, including the structured technical requirement rows — not a PDF reference. Per §8.4, there is no controlled specification file to store or digest in this release.
2. Create `04_fixture/render_fixture.py` with exactly this content:

   ```python
   import json
   from pathlib import Path

   from jinja2 import Environment, StrictUndefined, select_autoescape


   ROOT = Path(__file__).resolve().parents[1]
   input_path = ROOT / "04_fixture" / "moh_input.json"

   environment = Environment(
       autoescape=select_autoescape(enabled_extensions=("html",)),
       undefined=StrictUndefined,
       keep_trailing_newline=True,
   )
   context = json.loads(input_path.read_text(encoding="utf-8"))

   outputs = (
       ("invitation_to_tender.html", "moh_invitation_expected.html"),
       ("complete_tender.html", "moh_expected.html"),
   )

   for template_name, output_name in outputs:
       template_path = ROOT / "02_master" / template_name
       output_path = ROOT / "04_fixture" / output_name
       template = environment.from_string(template_path.read_text(encoding="utf-8"))
       output_path.write_text(template.render(**context), encoding="utf-8")
   ```

3. Run the strict renderer using the bench Python environment:

   ```bash
   ../../../../../../env/bin/python 04_fixture/render_fixture.py
   ```

   A missing or misspelled Jinja value must fail the command. Do not replace `StrictUndefined` or insert blank defaults to make it pass.
5. Render both resolved HTML files with `02_master/print.css` using the repository's installed `wkhtmltopdf` executable:

   ```bash
   wkhtmltopdf --enable-local-file-access \
     --user-style-sheet 02_master/print.css \
     04_fixture/moh_invitation_expected.html \
     04_fixture/moh_invitation_expected.pdf

   wkhtmltopdf --enable-local-file-access \
     --user-style-sheet 02_master/print.css \
     04_fixture/moh_expected.html \
     04_fixture/moh_expected.pdf
   ```

6. Complete `package_index.md` with:
   - the separate Invitation notice PDF, clearly labelled as a publication notice and not part of the issued Tender package;
   - the issued Tender PDF;
   - confirmation that Section V's Schedule of Requirements matches the structured technical requirement rows exactly, per §8.4 — no separate specification file to list; and
   - no unaccounted file.
7. Confirm that `moh_expected.html` neither contains the Invitation notice nor lists it in its contents.
8. Compare the shared values in both outputs: Tender reference, title, Procuring Entity, clarification deadline, submission deadline, electronic submission channel and Tender-security treatment. Record any mismatch as a blocker.
9. Search both resolved HTML files for unresolved authoring content:

   ```bash
   rg -n '\{\{|\{%|\[insert|insert here|delete if|select one|\.\.\.' \
     04_fixture/moh_invitation_expected.html \
     04_fixture/moh_expected.html
   ```

   The command must return no unresolved item. A legitimate ellipsis in locked official wording must be individually recorded and approved rather than silently ignored.

If `moh_input.json` needs a value that section 7 or section 13 does not authorise, add the missing decision to `open_issues.md` and stop. Do not invent a fixture-only field.

**Gate E:** stop. A practising Procurement Officer walks through the five tasks using `moh_input.json` and checks the separate Invitation notice, issued Tender and package index.

### Pass 6 - Record the decision

Complete `05_review/review_record.md` with:

- official source and digest confirmed by;
- coverage confirmed by;
- legal text and fixed alternative treatment confirmed by;
- five-task usability confirmed by;
- technical-specification package treatment confirmed by;
- unresolved blockers;
- review date; and
- one decision: **APPROVE FOR IMPLEMENTATION PACK**, **CORRECT AND RE-REVIEW**, or **REJECT THE PRODUCT PATTERN**.

These are review responsibilities, not new KenTender roles or workflows.

Claude must not create or modify DocTypes, hooks, routes, services, permissions, patches, seeds or runtime template code under this curation instruction. `render_fixture.py` is the sole permitted executable and must not be imported or installed by KenTender. A later approved implementation pack will state exactly how the reviewed master and registers are encoded in `kentender_procurement`.

No production code or Frappe implementation is authorised by this v0.3 document.

## 15. Release evidence

The later implementation pack must not treat the template as complete unless it includes:

1. official source file and source record;
2. source SHA-256;
3. completed coverage register;
4. reviewed base document;
5. final data dictionary and schedules;
6. supplier-form and evidence list;
7. render placement register;
8. completed Ministry of Health golden fixture;
9. expected separate Invitation notice, complete issued Tender and package index;
10. proof that the Invitation is absent from the issued Tender document;
11. automated coverage, cross-output consistency, validation, calculation and render tests;
12. independent review record;
13. human walkthrough result; and
14. released bundle digest.

The installed product contains a read-only registry entry and a code-owned bundle. The evidence may remain in the controlled release record. It does not require an operational template-management screen.

## 16. Acceptance gate

STD-TPL-001 may be approved only when all of the following are true:

| Gate | Required proof |
|---|---|
| Source | Exact official Goods STD file, source record and digest exist |
| Applicability | Simple IT equipment fits; complex IT, WORKS and unsupported methods are rejected |
| Coverage | Every official section, table and form has an approved treatment |
| Output boundary | Invitation is generated separately; the issued Tender contains its cover and contents followed by Sections I to VIII |
| Fixed text | ITT, GCC and official form wording are complete and not officer-editable |
| Data | Every field has a render, validation, supplier-response, evaluation or contract purpose |
| Schedules | Goods, services and price rows share one source and reconcile |
| Technical document | Approved specification is present, versioned and publishable |
| Evaluation | The visible evidence and fixed evaluation sequence agree |
| Contract | TDS, SCC, forms and schedules agree |
| Output | Both outputs have no unresolved prompt, missing operative content or duplicate independently maintained value |
| Usability | A practising Procurement Officer can complete the five tasks without STD concepts |
| Reuse | Useful earlier IT work is accounted for; retired engine work is absent |
| Simplicity | No runtime schema, manifest, clause editor, configurator or second permission system exists |

Any failed gate returns the curation pack for correction. It must not be hidden as a warning.

## 17. Document boundary and next action

This document owns the content and release proof for `IT-EQUIPMENT-OPEN-V1`.

TPR-CHG-001 owns how a Procurement Officer uses the approved template to prepare, review and approve a particular Tender. It must not redefine the template.

After STD-TPL-001 is approved:

1. revise TPR-CHG-001 to cite the approved template and remove any duplicated template specification;
2. prepare one focused implementation pack that encodes this template and the five-task journey;
3. implement only after explicit authorisation; and
4. run the approved Ministry of Health walkthrough and smoke tests before adding another pattern.

Goods beyond this narrow product, complex IT systems and WORKS remain separate future releases. Shared infrastructure may be extracted only after two implemented products prove the same need.

## 18. Precedence

This document follows:

- **STD-STD-001 v1.1** for the three-layer separation, the parameter rule, the six content classes, the placeholder lifecycle, curation anti-patterns, the two-output rule, preference/reservation and lotting treatment, the forms/attachments hybrid rule, product-pattern taxonomy, curation weight and shared-fixture discipline;
- **STD-ST-001 v0.3 - Approved**, for the original comparative evidence behind those principles;
- **CFG-CHG-002 v0.9** for the effective-dated reservation-category and threshold reference this template's preference treatment reads;
- **REQ-CHG-001**, for the structured technical requirement, service and acceptance rows this template's Section V now renders from directly, per §8.4; and
- **TPR-CHG-001 v0.4 - Approved**, as the current Tender Preparation consumer, which this version 1.1 correction fulfils the condition of.

Earlier STD Engine and IT Wizard documents, and REQ-CHG-001 v1.0/v1.1 language predating its own v1.2 structured-handoff correction, are source analysis only where they conflict with the approved simple product direction.

Approval of this document will make it the content and curation-procedure authority for the first IT-equipment template. It will not authorise code, migration, deployment or production use.

## Appendix A - Instruction to give Claude

Use this instruction without expanding its scope:

> Resume section 14 of STD-TPL-001 v0.3 from Gate B, from the `frappe-bench/apps/kentender_v1` repository root. This is curation only. Do not implement or modify any Frappe runtime, DocType, hook, route, service, permission, patch or seed. Preserve unrelated work. First revise every Invitation-related coverage row to follow sections 5.1 and 11: the Invitation is a separate generated publication notice and must not be part of `complete_tender.html`. Show the revised coverage register and open issues, then stop again at Gate B for approval. After Gate B is approved, continue one pass at a time using the exact folders, filenames, CSV columns, HTML/Jinja format and review gates in v0.3. Do not add fields, variants, forms or policy choices that STD-TPL-001 v0.3 has not authorised.
