# REQ-UX-001 — Procurement Requisitions Usability Amendment

| Control | Value |
|---|---|
| Version | **0.2** |
| Date | 16 September 2026 |
| Status | **Proposed for Project Owner review** |
| Applies to | REQ-CHG-001 v1.8 |
| Governing standard | KT-STD-001 v1.6 |
| Current owner contracts | Approved PLN v1.20, BUD v1.9, NDS v1.13, CFG v0.11 and STR v1.8 |
| Purpose | Make the Requisition workflow straightforward for departmental and procurement users without removing structured requirements, governance, funding protection or audit evidence. |
| Incorporation rule | On approval, fold this amendment into the next complete REQ-CHG-001 successor. This file is review evidence, not a parallel implementation specification. |

## 1. Decision summary

REQ v1.8 is technically strong and substantially complete, but it exposes too much of its internal structure to ordinary users. Five fixed steps, repeated source-line mechanics, row-by-row confirmation, dense reviewer evidence and correction terminology make a lawful workflow feel more complicated than it is.

The revised experience uses three user tasks:

1. **Request details** — say what is being requested from the approved plan and list the equipment.
2. **Requirements** — state minimum technical requirements, support, services, acceptance and any supporting material.
3. **Review and submit** — check the complete request and take the action allowed for the current responsibility.

The five existing validation groups remain internally traceable. No Planning, Budget, departmental-certification or Procurement-authorisation gate is removed. The change is presentation and task organisation, except for the explicitly defined grouped confirmation of suggested minimum requirements.

## 2. Usability findings

| Finding | User consequence | Required correction |
|---|---|---|
| Five validation groups are presented as five compulsory navigation steps. | Users experience the validation model as extra process. | Present three task-oriented pages while retaining all five validation results internally. |
| “Drawdown”, “allocation”, “source line”, “scope lock” and “handoff” dominate ordinary screens. | Departmental users must understand system and integration concepts to prepare a request. | Use business labels; retain technical identities in labelled supporting detail and audit. |
| Baseline requirements require repeated row-by-row confirmation after an item is added. | Routine IT requests create avoidable clicks and uncertainty. | Show all suggested minimums before item creation and allow one deliberate grouped confirmation. |
| The start page repeats a large amount of Planning evidence before any work begins. | Starting a request feels like a review stage. | Use one concise start dialog with the essential approved purchase, available amount and product boundary. |
| The same complete package is repeated without a consistent reading hierarchy. | HoD and HOPF reviews become long technical inventories. | Use one reusable complete-review composition with result, purchase, funding, requirements and decision sections in that order. |
| Compatibility checks are presented as eight technical gates before the business outcome. | HOPF must interpret implementation controls before understanding whether authorisation is safe. | Lead with the authorisation result and visible exceptions; place the eight named checks in a compact supporting table. |
| Returned and upstream-correction records require knowledge of Versions, roots and outcome events. | Users may not know what to correct or whether work can resume. | Open the copied Draft at the affected section; state plainly when a stopped request cannot resume and when a new request is required. |
| Cross-department certification is explained in system language. | Contributors may mistake one lead certification for loss of ownership or an extra approval chain. | State which departments contribute and which HoD submits, without exposing routing algorithms. |
| Technical readers share business screens without a complete action-state contract. | Implementations may show disabled business actions or incorrect Forbidden states. | Apply KT-STD-001 v1.6 §3A.6: complete read, no business controls, registered routes/search. |
| Document completeness could again be mistaken for usability. | Dense but technically accurate pages may ship without ordinary-user validation. | Require representative-user tasks and treat misunderstanding of scope, approval or funding as blocking. |

## 3. Locked task model

### 3.1 User tasks and retained validation

| Visible task | Content | Retained v1.8 validation groups |
|---|---|---|
| Request details | Approved-plan use, request title, delivery, requested quantities/values and equipment items | Request and drawdown; Equipment items |
| Requirements | Technical characteristics, warranty/support, related services, acceptance checks and supporting materials | Technical and support; Services and acceptance |
| Review and submit | Readiness, complete printable content and role-specific routing/decision | Review and submit |

Use a compact three-part progress row immediately below the page header. It is navigation and progress, not a new lifecycle. Labels are **Request details**, **Requirements**, **Review and submit**. Each shows **Not started**, **Needs attention** or **Complete**. Do not show internal blocker counts in the progress labels.

### 3.2 Display-language map

| Internal or earlier label | User-facing label | Treatment |
|---|---|---|
| Plan Item | Approved purchase | Show the full purchase title first and Plan Item reference beneath it. |
| Request and drawdown | Amounts requested from the approved plan | Never require “drawdown” knowledge for ordinary preparation. |
| Planning allocation / source line | Approved requirement | Department and requirement name lead; exact references are supporting detail. |
| Remaining original allowance | Still available from the approved purchase | Show quantity and value separately. |
| Proposed baseline characteristic | Suggested minimum requirement | Explain that the user must keep or remove each suggestion before continuing. |
| Authorise for Tender Preparation | Authorise requisition | Consequence text states that Tender Preparation may then begin. |
| Change lead department | Change submitting department | Explain that the current submission remains in history and the new department must certify the copied Draft. |
| Request upstream correction | Request Planning correction | Use only for a Planning-owned fact; explain that the current requisition will stop and will not reopen automatically. |
| Prepare a new Requisition | Start a new requisition / Start new Draft | Show the current Planning facts and state that earlier decisions and funding are not copied. |
| Handoff consumed | Tender Preparation started | Show the Tender reference when available; retain handoff evidence in History. |
| Upstream correction required | Planning correction requested | State that the current requisition is preserved and cannot resume. |
| Scope lock | Existing procurement scope | Explain the exact restriction in ordinary language; technical term belongs in supporting evidence. |
| Version | Version | Keep as secondary record evidence, never the main task label. |

Machine enums, command names, identities and stored historical text remain unchanged unless the eventual full successor explicitly versions their contract.

### 3.3 Suggested minimum requirements

When adding an item, show its code-owned suggested minimum requirements inside the item dialog before the final action. Every suggestion starts selected. The user may remove a suggestion or change a permitted value before confirming.

The primary action **Add item and use selected minimums** atomically creates the item and records the selected suggestions as confirmed. It does not silently confirm unseen content. A copied package or later category change shows **Minimum requirements to confirm** at the top of the Requirements page with selected rows and primary **Confirm selected minimums**. Unconfirmed suggestions still block submission.

The full successor shall add one batch-capable, idempotent command or extend the item-create command with the exact selected suggestion decisions. It shall not implement the primary action as several fallible client-side row commands.

## 4. Complete actor coverage

| Actor | Immediate task | Primary view/action | Outcome shown |
|---|---|---|---|
| Departmental Author | Prepare or correct the request | Three-task Draft; **Send for department approval** | Waiting for the lead Head of User Department |
| Head of User Department preparing directly | Prepare and certify the request | Same Draft; **Submit to Procurement**, **Request Planning correction** or **Withdraw requisition** | Waiting for Procurement authorisation, stopped for owner correction, or withdrawn |
| Head of User Department reviewing Author work | Confirm the complete departmental request | Complete review; **Submit to Procurement**, **Return for correction**, **Request Planning correction** or **Withdraw requisition** | Submitted, copied correction Draft, stopped for owner correction, or withdrawn |
| Contributing-department Author | Complete only permitted source/item content | REQ-DES-03-CONTRIBUTOR; own approved-requirement and item rows editable, all other contributor and shared content read-only | One combined request remains visible; no routing or decision action |
| Head of Procurement Function | Decide whether the complete request may proceed | Complete review; **Authorise requisition**, **Return to department**, **Request Planning correction** or **Change submitting department**; authorised/unconsumed view may **Revoke authorisation** | Authorised package, copied correction Draft, stopped correction request, rerouted Draft or revoked package |
| Procurement Planner | Investigate Planning-owned correction | Requisition evidence read-only; working action remains in Planning | Planning request/outcome visible here without REQ decision controls |
| Procurement Officer | Begin Tender Preparation from an authorised request | Authorised view; **Continue to Tender Preparation** | Exact authorised requirements carried downstream |
| Auditor / authorised reader | Inspect decision and lineage | Read-only complete review and History | Exact historical evidence; no decision controls |
| Administrator / System Manager | Diagnose any record | Same record routes read-only plus Technical record search | Complete technical read; no business controls |

Multiple active responsibilities render the union of legitimate actions without a role switch. Maker-checker and incompatible-decision rules still apply at command time.

## 5. Static design contract

Supply KT-STD-001 v1.6 §2 plus this section only to the design tool. Fixture metadata remains outside the artboard. The business fixtures are isolated scenario inputs, not production-law verification.

### 5.1 Shared fixture pack

| Fact | Exact value |
|---|---|
| Financial year | FY 2027/28 |
| Requisition | REQ-MOH-2027-033-001 |
| Planning drawdown display reference | PDR-MOH-2027-033-001 — isolated visual-fixture reference, not a guessed command identity |
| Handoff display reference | REQ-MOH-2027-033-001 — the Requisition reference used for display; internal owner identity remains separate |
| Consumed Tender reference | TND-MOH-2027-033 |
| Approved purchase | Clinical training and deployment laptops for digital health rollout |
| Plan Item reference | PPI-MOH-2027-033 |
| Departments | Human Resources Management and Development; Digital Health |
| Lead department | Digital Health |
| Planned method | Open Tender |
| Requirement product | IT Equipment |
| Procurement category | Goods |
| Reservation category | Youth |
| Lotting | Single lot |
| Currency | KES |
| Award package | One |
| Plan horizon | Single year |
| Planned value | KES 50,000,000.00 |
| Still available | 250 Each; KES 50,000,000.00 |
| Plan completion boundary | 31 Dec 2027 |
| Estimated completion | 24 Sep 2027 |
| Delivery location | Ministry of Health Headquarters, Afya House, Nairobi |
| Latest delivery date | 30 Sep 2027 |
| Business need | Equip clinical training and field deployment staff with a common laptop specification for the national digital health rollout. |
| Expected operational result | Staff can use secure, supported equipment for training and field digital-health work. |
| Strategic objective | Strengthen interoperable national digital health services |
| Strategic objective reference | OBJ-MOH-2023-001 |
| Departmental Author | Grace Wanjiku |
| Isolated contributing Author | Asha Odhiambo; non-production permission fixture; Departmental Author assigned only to Human Resources Management and Development for REQ-DES-03-CONTRIBUTOR; this adds no business role or approval stage |
| Lead Head of User Department | Dr Peter Kimani |
| Head of Procurement Function | Charles Mutiso |
| Departmental certification | I confirm that this requisition states the departments’ operational need and minimum requirements and may be submitted to Procurement. |
| Planning-correction request | UI-CORR-001 |
| Planning-correction requester | Dr Peter Kimani; 10 Mar 2027, 09:00 EAT |
| Incorrect Budget Line in correction reset | MOH-BL-DHI-2027 — Digital Health only; cannot fund the HRMD source row |
| Planning-correction reason | The approved source allocation refers to the wrong Budget Line. Please review the departmental funding specification through the governed Planning correction process. |
| In-progress owner | Mercy Kilonzo; 10 Mar 2027, 11:00 EAT |
| Resolved outcome | PLN-MOH-2027-001, Version 2 is Active; replacement PPI-MOH-2027-033 item Version 2 is eligible for 250 Each and KES 50,000,000.00; Budget Line corrected from MOH-BL-DHI-2027 to entity-wide MOH-BL-HWD-2027; resolved by Mercy Kilonzo on 12 Mar 2027, 10:00 EAT |
| Closed-without-change outcome | The approved source allocation and Budget Line are correct. No Planning change is required. Decided by Mercy Kilonzo on 12 Mar 2027, 10:00 EAT |
| Second unresolved request | UI-CORR-002; Open |
| Department-return comment | Replace the processor wording with a measurable, supplier-neutral minimum. |

Approved-requirement rows:

| Department | Requirement | Reference | Available quantity | Available value |
|---|---|---|---:|---:|
| Human Resources Management and Development | Business laptops | SRC-MOH-033-001 | 100 Each | KES 20,000,000.00 |
| Digital Health | Business laptops | SRC-MOH-033-002 | 150 Each | KES 30,000,000.00 |

Equipment rows:

| Item | Approved requirement | Category | Quantity | Intended use | Delivery |
|---|---|---|---:|---|---|
| Business laptops | HR Management and Development — SRC-MOH-033-001 | Laptop | 100 Each | Clinical training for Human Resources Management and Development staff | Nairobi; 30 Sep 2027 |
| Business laptops | Digital Health — SRC-MOH-033-002 | Laptop | 150 Each | Field digital-health deployment for Digital Health staff | Nairobi; 30 Sep 2027 |

Technical-requirement rows for the complete fixture:

| Requirement | Comparison | Exact value | Unit | Control |
|---|---|---|---|---|
| Electrical compatibility | Required | Yes — suitable for Kenyan mains supply | — | Yes/No |
| New and unused equipment | Required | Yes | — | Yes/No |
| Memory | Minimum | 16 | GB | Integer |
| Storage capacity | Minimum | 512 | GB | Integer |
| Storage type | One of | NVMe SSD | — | Select |
| Display size | Minimum | 14.0 | inches | Decimal |
| Battery runtime | Minimum | 8 | hours | Decimal |
| Processor requirement | Minimum | 64-bit business-class processor, minimum 10 cores or equivalent benchmark | — | Single-line text |
| Operating-system compatibility | Required | Approved organisational Windows environment | — | Single-line text |
| Network connectivity | Required | Wi-Fi 6 and Bluetooth 5 or later | — | Multi-select; every selected capability is required |
| Required ports | Required | USB-C ×2; USB-A ×2; HDMI ×1 | — | Structured port and quantity rows |

Warranty-and-support values for the complete fixture:

| Label | Exact value | Control |
|---|---|---|
| Minimum warranty | 36 months | Integer with months suffix |
| On-site support required | Yes | Yes/No |
| Maximum support response | 8 hours | Integer with hours suffix |
| Manufacturer support required | Yes | Yes/No |
| Service location constraint | Within Kenya | Select |
| Support description | Supplier to provide escalation and warranty-contact details. | Textarea, maximum 500 characters |

Acceptance-check rows for the complete fixture:

| Check | Applies to | Pass condition | Evidence |
|---|---|---|---|
| Quantity | All items | Delivered quantities equal the authorised schedule | Inspection record |
| Physical condition | All items | No visible damage and all listed accessories are present | Inspection record |
| Required specification | All items | Every delivered unit complies with all mandatory technical rows | Inspection record |
| Functional test | All items | Each device powers on and completes the agreed basic functional test | Test result |
| Documents received | All items | Warranty and delivery documents are received and verified | Certificate |

Funding fixture at Procurement authorisation:

| Fact | Exact value |
|---|---|
| Budget Line | MOH-BL-HWD-2027 |
| Approved | KES 60,000,000.00 |
| Available now | KES 60,000,000.00 |
| This requisition | KES 50,000,000.00 |
| Available after authorisation | KES 10,000,000.00 |
| HR Management and Development source request | KES 20,000,000.00 |
| Digital Health source request | KES 30,000,000.00 |

Procurement-compatibility results:

| Check | Exact result |
|---|---|
| Procurement category | Goods |
| Requirement type | Straightforward off-the-shelf IT equipment |
| Reservation category | Youth |
| Lotting indicator | Single lot |
| Currency | KES |
| Award package | One |
| Planned method | Open Tender |
| Plan horizon | Single year |

The complete fixture has no related services and no supporting materials. REQ-DES-05-INCOMPLETE changes only two facts: Minimum warranty is empty and there are no acceptance-check rows. All other complete-fixture values remain present.

### 5.2 REQ-DES-01 — Requisitions workspace

**Purpose.** Find the next Requisition task or continue existing work.

**Fixture outside the artboard.** Grace Wanjiku; Departmental Author for both fixture departments; 1 Mar 2027, 09:00 EAT; READY scenario with no existing root.

**Header.** Title **Procurement Requisitions**. Description **Prepare and follow requests for purchases already approved in the annual plan.** No header primary action.

**Composition, top to bottom.**

1. Compact work summary row with **Drafts 0**, **Returned to me 0**, **My approvals 0**. Each is a local filter; omit counts for responsibilities Grace does not hold.
2. Filter row: Search by requisition or purchase; Status **All statuses**; Department **All my departments**; Clear filters.
3. Section **Ready to start**. One row using columns Approved purchase; Departments; Still available; Needed by; Action.
4. Section **My requisitions**. In this base variant show empty text **You have no requisitions yet.**

Ready row values: purchase title with `PPI-MOH-2027-033` beneath it; departments **Digital Health; HR Management and Development**; **250 Each** with **KES 50,000,000.00** beneath it; **31 Dec 2027**; primary row action **Start requisition**.

**Actions.** Start requisition is enabled. Filters are secondary. No generic Create action.

**Variants.**

- **REQ-DES-01-DRAFT:** Ready row is absent. My requisitions contains REQ-MOH-2027-033-001; purchase title; Status **Draft — Request details need attention**; Updated **1 Mar 2027, 09:45 EAT**; action **Continue**.
- **REQ-DES-01-ACTION:** My requisitions contains the exact assigned record; Status **Awaiting your approval**; action **Review**. Do not create a separate Tasks panel.
- **REQ-DES-01-NONE:** Ready to start says **No approved purchases are ready for a requisition.** My requisitions remains available.
- **REQ-DES-01-TECHNICAL:** Administrator/System Manager sees Search, Status, Department and Financial year filters plus all authorised rows site-wide; work-summary counts and all business actions are absent.

**Visual check.** The next legitimate action is visible without a dashboard, duplicate record sections or knowledge of Plan Item states.

### 5.3 REQ-DES-02 — Start requisition dialog

**Purpose.** Confirm the exact approved purchase before creating the Draft.

**Fixture outside the artboard.** Same as REQ-DES-01; no Requisition exists.

**Dialog.** A 520 px dialog over the workspace. Heading **Start this requisition?** Text **A Draft will be created from the approved purchase below.**

Place these labelled rows vertically: Approved purchase; Departments; Still available; Plan completion boundary; Requirement product. Values are the fixture title, both departments, **250 Each and KES 50,000,000.00** as separate adjacent values, **31 Dec 2027**, and **IT Equipment**.

Below, show the visible notice: **This release supports straightforward off-the-shelf IT equipment. It does not support software development, integration or migration.** Then show **Digital Health will submit this combined departmental request.**

Footer left **Cancel**; right primary **Start requisition**. Both enabled. No STD, template, profile or approval selector.

**Unsupported variant.** Isolated reset: Requirement product **Software integration**, while the approved purchase title remains visible. Replace the primary action with disabled **Start requisition** and show **This approved purchase requires software integration, which this release does not support.** Keep Cancel.

**Visual check.** The user can identify the purchase, available amount and product limitation without reading Planning lineage or a separate full page.

### 5.4 REQ-DES-03 — Draft: Request details

**Purpose.** State how much is requested and list the equipment.

**Fixture outside the artboard.** Grace Wanjiku; Draft Version 1; after creation and before adding items.

**Header.** Title **Clinical training and deployment laptops for digital health rollout**. Description **Complete the request using the approved purchase shown below.** Place badge **Draft** beside the title. Place `REQ-MOH-2027-033-001` beneath the title in muted text. No header action.

**Progress row.** Request details **Needs attention**; Requirements **Not started**; Review and submit **Not started**. Request details is selected.

**Composition, top to bottom.**

1. Returned-work panel, absent in the base variant.
2. Section **Approved purchase** with title, Plan Item reference, Method, Plan completion boundary, Estimated completion, Strategic objective and Business need as separately labelled values. Start open and compact; technical lineage disclosure **Source details** starts closed.
3. Section **Request information** with two-column form: Requirement title; Delivery location; Latest delivery date; Related services required. Values use the fixture; Related services **No**.
4. Section **Amounts requested from the approved plan**. Visible explanation **The full available amount is selected. Enter a smaller amount only when this requisition covers part of the approved purchase.**
5. Approved-requirements table with columns Department; Requirement; Available quantity; Requested quantity; Available value; Requested value. Show both fixture rows. Requested values default to the full available values. Each row has secondary **Use full available amount** only after a value has been changed.
6. Section **Equipment**. Empty state **No equipment items added. Add the equipment covered by the requested quantities above.** Primary section action **Add equipment item**.

**Footer.** Left **Back to Requisitions**. Right secondary **Save draft** and primary **Continue to requirements**, disabled. Immediately above the disabled action show **Add equipment items matching the requested quantities.** A Departmental Author has no cancel/withdraw command.

**Complete variant.** Equipment table uses the two fixture rows with columns Item; Approved requirement; Category; Quantity; Intended use; Delivery; Action. Row actions Edit and Remove. Continue to requirements is enabled.

**Returned variant.** At the top show **Correction requested** and **Replace the processor wording with a measurable, supplier-neutral minimum.** Include link **Go to affected section**, targeting Technical requirements. Status badge **Draft correction**. Preserve approved-purchase and earlier-decision evidence under History; do not make the user choose a Version.

**REQ-DES-03-CONTRIBUTOR — isolated contributing-author variant.** Fixture: Asha Odhiambo; Departmental Author assigned only to Human Resources Management and Development; the combined Draft already contains both approved-requirement rows and both equipment rows. Keep the same page and full combined context. The HR Management and Development approved-requirement and equipment rows are editable. The Digital Health rows, Approved purchase section, shared Request information and every shared Requirements value are read-only. The only footer actions are **Back to Requisitions** and **Save my changes**. Do not show Cancel draft, Continue, Send, Submit, Return, Withdraw, Request Planning correction or any decision action. After save, show **Your changes are saved in the combined requisition.**

**Visual check.** The user sees business need, requested amount and equipment in one task. The isolated contributor can change only their own source/item content and can still understand the combined request. “Drawdown”, canonical IDs and routing algorithms do not appear in the ordinary composition.

### 5.5 REQ-DES-04 — Add equipment item and minimums

**Purpose.** Add one equipment row and deliberately accept or remove suggested minimum requirements.

**Fixture outside the artboard.** Grace; first HRMD item; no item saved.

**Dialog.** 520 px, scrollable within the viewport. Heading **Add equipment item**.

**Item details**, in order: Approved requirement Select **HR Management and Development — Business laptops**; Equipment category Select **Laptop**; Item name **Business laptops**; Quantity **100** with read-only Unit **Each**; Intended use fixture text; Delivery location fixture; Latest delivery date **30 Sep 2027**.

Below, section **Suggested minimum requirements**. Explanation **Keep the minimums that apply to this item. You can add further requirements next.** Table columns Use; Requirement; Proposed value. Three checked rows: Electrical compatibility / Yes using Yes/No; New and unused equipment / Yes using Yes/No; Storage type / NVMe SSD using Select. The user may change any of these three displayed values or clear its Use checkbox before confirming.

Footer left **Cancel**; right primary **Add item and use selected minimums**. The action is enabled when the item fields and every selected suggestion are valid.

**Copied-content variant.** On the Requirements page, not this dialog, show panel **Minimum requirements to confirm** with checked rows, secondary **Remove selected** and primary **Confirm selected minimums**. No repeated Confirm button on every row.

**Visual check.** No suggested requirement becomes confirmed without being visible in the same decision. The routine case takes one confirmation rather than three separate commands.

### 5.6 REQ-DES-05 — Draft: Requirements

**Purpose.** Define the minimum supplier-facing requirements and how delivery will be accepted.

**Fixture outside the artboard.** Grace; both fixture items exist; minimum suggestions confirmed; Related services No. The base artboard is REQ-DES-05-INCOMPLETE. REQ-DES-05-COMPLETE is a separate reset variant.

**Header and progress.** Reuse REQ-DES-03 header. Request details **Complete**; Requirements **Needs attention**; Review and submit **Not started**. Requirements selected.

**REQ-DES-05-INCOMPLETE composition, top to bottom.**

1. Visible issue summary: **Enter the minimum warranty and add at least one acceptance check.** Each issue links to its affected section.
2. Section **Technical requirements** with target tabs **All equipment**, **Business laptops — HRMD**, **Business laptops — Digital Health**. All equipment selected. Primary section action **Add requirement**.
3. Show every technical-requirement row from §5.1 under three headings:
   - **Basic equipment:** Electrical compatibility; New and unused equipment.
   - **Performance and storage:** Memory; Storage capacity; Storage type; Display size; Battery runtime; Processor requirement; Operating-system compatibility.
   - **Connectivity:** Network connectivity; Required ports.
4. Within each group use columns Requirement; Minimum or required value; Unit; Action. Show comparison as subordinate text beneath the requirement name. Actions Edit/Remove.
5. Section **Warranty and support** in a two-column form. Minimum warranty is empty and carries local error **Enter the minimum warranty in months.** The other five controls contain the exact §5.1 values.
6. Section **Related services**. Base value **No related services requested.** Secondary **Change answer**. When Yes, show service table and **Add service**.
7. Section **Acceptance checks**. Empty state **No acceptance checks added. Add at least one objective check showing how delivery will be accepted.** Primary section action **Add acceptance check**. Do not show the five complete-fixture rows in this variant.
8. Section **Supporting materials**. Base empty text **No supporting materials added.** Explanation **Files may support a structured requirement but cannot replace it.** Secondary **Add supporting material**.

**Incomplete footer.** Left **Back to request details**. Right secondary **Save draft** and disabled primary **Continue to review**. Immediately above it show **Enter the minimum warranty and add at least one acceptance check.**

**REQ-DES-05-COMPLETE variant.** Use a clean reset of the artboard, not the incomplete state with values overlaid. Remove the issue summary and local error. Requirements is **Complete**. Show all eleven §5.1 technical rows, all six §5.1 warranty-and-support values and all five §5.1 acceptance-check rows. The acceptance table columns are Check; Applies to; Pass condition; Evidence; Action, with Edit/Remove on each row. Related services remains No and Supporting materials remains empty. **Continue to review** is enabled.

**Validation variant.** Keep every valid row and entered value. Place exact issues above the affected section and bind field errors locally. Do not reset the page or show one undifferentiated blocker count.

**Visual check.** No artboard simultaneously claims missing warranty/check data and displays it as complete. The page is long but structured by strong headings, compact tables and contrast. Users do not see eleven unrelated rows in one undifferentiated block.

### 5.7 REQ-DES-06 — Draft: Review and submit

**Purpose.** Verify the complete request and send it to the next responsible person.

**Fixture outside the artboard.** Grace; complete Draft Version 1; no blocking issue; one delivery-date warning.

**Header and progress.** Request details Complete; Requirements Complete; Review and submit selected. Badge Draft.

**Top result.** Green result panel **Ready to send for department approval**. Under it show warning **The requested delivery date is 6 days after the plan’s estimated completion date.** Separately label Estimated completion **24 Sep 2027**, Latest delivery date **30 Sep 2027** and Plan completion boundary **31 Dec 2027**.

**Composition, top to bottom.**

1. **Purpose and approved purchase:** requirement title, business need, expected result, strategic objective, method and dates.
2. **Amounts requested:** both department rows and totals **250 Each** and **KES 50,000,000.00**.
3. **Equipment:** both fixture rows.
4. **Technical requirements:** all eleven §5.1 rows, grouped as in REQ-DES-05.
5. **Warranty and support:** all six labelled §5.1 values.
6. **Related services:** No related services requested.
7. **Acceptance:** all five §5.1 rows.
8. **Supporting materials:** None.

Every section starts open. Long descriptions wrap and remain available in full. History and technical identity evidence may start closed beneath **Record details**.

**Footer.** Left **Back to requirements**; secondary **Save draft**; right primary **Send for department approval**.

**Direct-HoD variant.** Fixture: Dr Peter Kimani preparing the Draft directly in a current lead-HoD assignment. The result reads **Ready to submit to Procurement** and the primary action is **Submit to Procurement**. Place quiet actions **Request Planning correction** and **Withdraw requisition** in an **Other actions** menu beside the footer; neither is primary. Do not show a self-approval action. Request Planning correction opens the exact dialog in REQ-DES-08. Withdraw opens confirmation **Withdraw this requisition?** with required Reason, 20–1,000 characters, notice **The requisition will close without using approved-plan amounts or reserving funding**, and Cancel / **Withdraw requisition**.

**Visual check.** The user can understand what will be bought, for whom, at what value and under which minimums before acting; no count card substitutes for content.

### 5.8 REQ-DES-07 — Head of User Department review

**Purpose.** Confirm the complete departmental request or return it with one actionable correction.

**Fixture outside the artboard.** Dr Peter Kimani; lead Head of User Department; immutable Version 1; 8 Mar 2027, 09:00 EAT.

**Header.** Title **Review departmental requisition**. Description **Confirm that the request accurately states the departments’ need and minimum requirements.** Badge **Awaiting your approval**. Requisition reference beneath title. No header action.

**Top result.** **Ready for departmental submission**. Visible context: Prepared by Grace Wanjiku; Contributing departments both listed; Submitting department **Digital Health**.

Use the complete ordered review from REQ-DES-06. Above the footer show this exact certification statement in a distinct bordered panel: **I confirm that this requisition states the departments’ operational need and minimum requirements and may be submitted to Procurement.**

**Footer.** Far left **Request Planning correction**; secondary **Return for correction**; right primary **Submit to Procurement**. Place quiet **Withdraw requisition** in an **Other actions** menu. No edit action. Request Planning correction and Withdraw use the exact dialogs defined in REQ-DES-08 and the REQ-DES-06 direct-HoD variant respectively.

**Return dialog.** Heading **Return this requisition for correction?** Required **Correction required**, 20–1,000 characters. Helper **State what must change and identify the affected section.** Optional governed affected-section Select: Request details; Equipment; Technical requirements; Warranty and support; Services; Acceptance; Supporting materials; Whole requisition. Footer Cancel / Return for correction.

**Submitted HoD variant.** After submission and before authorisation, Dr Peter Kimani sees the same complete Version read-only with badge **Submitted to Procurement**. No edit, return, submit or Procurement-decision action appears. Quiet actions are **Request Planning correction** and **Withdraw requisition**, using the same dialogs. A successful withdrawal shows terminal status **Withdrawn** and no fresh Draft.

**Visual check.** Peter sees one complete request and one certification decision, not a second preparation workflow or contributor-by-contributor approval chain.

### 5.9 REQ-DES-08 — Procurement authorisation

**Purpose.** Decide whether the complete requisition can proceed to Tender Preparation.

**Fixture outside the artboard.** Charles Mutiso; HOPF; immutable submitted Version 1; 15 Mar 2027, 10:00 EAT; current checks pass.

**Header.** Title **Authorise requisition**. Description **Review the request, current funding and procurement checks before authorising it.** Badge **Submitted to Procurement**.

**Top result.** Green **Ready to authorise**. Directly below show **Authorising will reserve KES 50,000,000.00 and allow Tender Preparation to begin.**

**Composition, top to bottom.**

1. **Current funding:** render every Funding fixture fact from §5.1. Beneath the five summary facts, retain the two separately labelled source rows exactly as stated there.
2. **Planning availability:** Status Eligible; Quantity available 250 Each; Value available KES 50,000,000.00; no unresolved correction hold.
3. **Departmental certification:** Submitted by Dr Peter Kimani; Lead department Digital Health; Submitted at 8 Mar 2027, 09:00 EAT.
4. Complete review sections from REQ-DES-06.
5. **Procurement checks:** compact two-column table Check / Result containing every Procurement-compatibility row from §5.1 in the same order.
6. Decision statement: **I authorise this requisition. The approved-plan amounts will be used, funding will be reserved and Tender Preparation may begin.**

The procurement checks section starts open but follows the complete business content; it does not lead the page.

**Footer.** Far left **Request Planning correction**; secondary **Return to department**; right primary **Authorise requisition**. Text action **Change submitting department** appears beside Departmental certification, not in the footer.

**Return-to-department dialog.** Heading **Return this requisition to the department?** Required **Correction required**, 20–1,000 characters. Optional affected-section Select uses the same values as REQ-DES-07. Notice **The submitted Version will remain in history and a copied Draft will open for correction.** Footer Cancel / **Return to department**.

**Change-submitting-department dialog.** Heading **Change submitting department and return?** Select is limited to **Human Resources Management and Development** and **Digital Health**, with Human Resources Management and Development selected in this variant. Required **Reason**, 20–500 characters. Notice **The current submission will remain in history. A copied Draft must be certified by the new submitting department before authorisation.** Footer Cancel / **Confirm change and return**. Success closes the Procurement task and opens its read-only returned result with the new Draft link; it never relabels the current certification.

**REQ-DES-08-CORRECTION reset variant and dialog.** This is isolated from the Ready-to-authorise base fixture. It replaces the displayed Budget Line with **MOH-BL-DHI-2027 — Digital Health only**, visibly conflicts with the HRMD source row, and uses the §5.1 Planning-correction reason. It does not simultaneously claim that current checks pass. The dialog is shared by the permitted lead-HoD and HOPF variants. Heading **Request a Planning correction?** Required textarea **What is wrong in the approved plan?**, 20–1,000 characters, prefilled with the exact reason. Notice **This requisition will be preserved and stopped. It will not reopen automatically after Planning responds.** Footer Cancel / primary **Send correction request**. A successful command creates display request **UI-CORR-001** and opens REQ-DES-11 in its Open state; it does not remain on an authorisable page.

**Blocking-funding variant.** Top result red **Cannot authorise — insufficient funding**. Show requested KES 50,000,000.00; available KES 40,000,000.00; shortfall KES 10,000,000.00. Authorise absent. Return and Refresh checks enabled.

**Hold variant.** Top result amber **Authorisation is on hold while Planning reviews a correction request.** Show **UI-CORR-001 · Open**. Authorise absent; View Planning request, Refresh checks and Return remain.

**Technical-reader variant.** Same complete content and result evidence; every business action and decision statement absent.

**Visual check.** Charles sees the result and financial consequence first, the complete request second and technical compatibility evidence last. No decision requires decoding transaction terminology.

### 5.10 REQ-DES-09 — Authorisation confirmation

**Purpose.** Confirm the material effects of authorisation.

**Dialog.** Heading **Authorise this requisition?** Labelled values: Quantity **250 Each**; Requisition value **KES 50,000,000.00**; Budget line **MOH-BL-HWD-2027**; Available after authorisation **KES 10,000,000.00**. Text **The approved-plan amounts will be used, two funding reservations will be created and Tender Preparation may begin.** Footer Cancel / primary **Authorise requisition**.

Do not display command names, transaction boundaries or “handoff” terminology.

### 5.11 REQ-DES-10 — Authorised requisition

**Purpose.** Read the authorised requirements and continue to the next procurement stage.

**Fixture outside the artboard.** Authorised Version 1; actor Procurement Officer in the base variant; handoff not consumed.

**Header.** Title fixture requisition title. Description **This requisition is authorised and ready for Tender Preparation.** Badge **Authorised**. Reference beneath title. Upper-right primary **Continue to Tender Preparation**.

**Top facts.** Authorised by Charles Mutiso; Authorised at 15 Mar 2027, 10:00 EAT; Requisition value KES 50,000,000.00; Tender Preparation **Not started**.

Use the complete review sections from REQ-DES-06. Add section **Funding reservations** after Amounts requested, with two rows: RSV-MOH-2027-033-001 / HRMD / KES 20,000,000.00 and RSV-MOH-2027-033-002 / Digital Health / KES 30,000,000.00. Under closed **Record details**, show Planning drawdown display reference **PDR-MOH-2027-033-001**, both `SRC-MOH-033-00x` source references, both reservation references and handoff display reference **REQ-MOH-2027-033-001**. Label each as supporting evidence; none is an editable command key.

**Actor variants.**

- HOPF before consumption: header has no primary; footer secondary **Revoke authorisation**.
- Procurement Officer: Continue to Tender Preparation enabled; reading the page creates nothing.
- Consumed: replace top status with **Tender Preparation started** and Tender reference **TND-MOH-2027-033**; primary **Open Tender**; revoke absent.
- Auditor/technical reader: navigation/export controls only; all business actions absent.

**Revocation dialog.** Heading **Revoke this authorisation?** Required Reason, 20–1,000 characters. Text **The approved-plan amounts and both funding reservations will be reversed. The authorised requisition will remain in history.** Footer Cancel / primary **Revoke authorisation**. If Tender Preparation has already consumed the handoff, do not show this dialog; show the Consumed variant instead.

**Visual check.** Authorised content is fully readable and the next valid stage is obvious. Counts never replace the actual requirements.

### 5.12 REQ-DES-11 — Returned and stopped work

**Returned Draft.** Reuse REQ-DES-03 or REQ-DES-05 according to the governed affected section. At the top show **Correction requested**, **Replace the processor wording with a measurable, supplier-neutral minimum**, Returned by **Dr Peter Kimani**, Returned at **8 Mar 2027, 09:10 EAT** and **Go to affected section**, targeting Technical requirements. The copied Draft is already open for correction; no Resume or Version-selection action.

**Planning correction requested.** Read-only page. Header description **Planning is reviewing an approved-plan issue. This requisition is preserved and cannot be edited or resumed.** Card **Planning correction request** shows **UI-CORR-001**, the exact §5.1 reason, Dr Peter Kimani, 10 Mar 2027 at 09:00 EAT, `PPI-MOH-2027-033` and the variant’s owner status. Complete request follows in read-only form.

**Procurement Planner variant.** Fixture: Mercy Kilonzo opening the stopped requisition from her Planning correction task. Show the same complete read-only requisition and correction card. The only task action is **Open Planning correction task**, which navigates to Planning; no REQ edit, return, submit, authorise, withdraw, outcome or clear-hold control appears. Planning records and disposes of the correction through its own governed screen.

Variants:

- Open: status **Awaiting Planning correction**; show **UI-CORR-001 · Open**; actions View Planning request / Back to Requisitions.
- In progress: status **Planning correction in progress**; show **Mercy Kilonzo began review on 10 Mar 2027 at 11:00 EAT**; same actions.
- Resolved: status **Planning correction completed**; show the complete §5.1 Resolved outcome; primary **Start a new requisition**, only in the eligible actor fixture.
- Closed without change: status **Planning request closed without change**; show the complete §5.1 Closed-without-change outcome and **The approved Planning facts have not changed. This requisition will not restart.** Primary **Start a new requisition**, only if current eligibility permits.
- Outcome unavailable: show last confirmed **UI-CORR-001 · In progress · Mercy Kilonzo · 10 Mar 2027, 11:00 EAT**, then **Planning response is temporarily unavailable. The stopped requisition has not changed.** Action Try again.
- Another request unresolved: show the Resolved outcome for UI-CORR-001 plus **UI-CORR-002 · Open** and **Authorisation remains on hold: 1 Planning request is still unresolved.** No authorise or clear-hold control.

**Fresh-start confirmation.** For the Resolved variant, heading **Start a new requisition?** and text **Use the Active corrected Planning facts shown. Earlier decisions and funding reservations will not be copied.** For Closed without change, use the same heading and text **Use the unchanged approved Planning facts. Complete departmental submission and Procurement authorisation again.** Both show stopped requisition **REQ-MOH-2027-033-001**, current Plan **PLN-MOH-2027-001**, current Plan Version and current eligibility as separately labelled values. Footer Cancel / primary **Start new Draft**. Use isolated eligible and ineligible resets; the ineligible reset removes the primary action and shows **A new requisition cannot be prepared: current Plan funding confirmation is required.**

**Visual check.** A stopped record never resembles an editable Draft. The page states whether the next work is waiting, investigation or an explicit new requisition.

### 5.13 REQ-DES-12 — Common and access states

| Variant | Visible composition | Actions |
|---|---|---|
| Loading | Skeleton only; no stale header/content | None |
| Workspace forbidden | **You do not have access to Procurement Requisitions. This area needs Departmental Author, Head of User Department, Head of Procurement Function, Procurement Planner, Procurement Officer, Auditor, Administrator or System Manager access. Ask your KenTender administrator to assign the appropriate responsibility in System setup.** | None |
| Record not found / masked | **Requisition not found** | Back to Requisitions |
| Load failure | **Procurement Requisitions could not be loaded.** | Try again |
| Stale Draft | Existing page retained with **This requisition changed after you opened it. Review the latest version before saving.** | Review latest version |
| Unsupported product | Approved purchase fixture title; Requirement product **Software integration**; **This approved purchase requires software integration, which this release does not support.** | Back to Requisitions |
| Existing open requisition | **REQ-MOH-2027-033-001 · Draft · Request details need attention** | Open existing requisition |
| Save validation | Retain all still-authorised input; issue **Requested equipment quantity for Digital Health is 140 Each but the approved requirement requests 150 Each** above Equipment and beside the row | Save again after correction |
| Uncertain decision result | Base **Checking whether your action completed…**; committed reset **Requisition submitted to Procurement**; retry-safe reset **The result could not be confirmed. Check the current requisition before trying again.** | No second decision while unresolved |
| Technical read | Complete record in its actual state | Read/navigation/export only |

All narrow artboards preserve table meaning through horizontal scrolling or labelled row cards. They do not drop Department, Requirement, Quantity, Value, Pass condition, Result or Action columns.

## 6. Functional interaction map — excluded from design prompts

| Screen / control | Destination or result | Governing effect |
|---|---|---|
| Workspace filters and counts | Refresh the authorised local result set | Read only; no authority or global context change |
| Start requisition | Open REQ-DES-02; confirmation invokes PrepareITEquipmentRequisition | One explicit creation; open-slot and product checks re-run |
| Continue / Review / Open existing requisition | Open exact current root, Version or task | No lifecycle change |
| Progress task labels | Navigate within the same Draft | Save prompt applies; no auto-completion |
| Save draft / Save my changes | Persist only the current actor’s permitted edits | Existing expected-version/idempotency rules; contributor cannot route the package |
| Use full available amount | Restore current displayed source remainder in the Draft | Revalidated at save/submit; never authority evidence |
| Add equipment item | Open REQ-DES-04 with the selected approved-requirement context | Dialog open creates nothing |
| Add item and use selected minimums | Create item and selected confirmed baseline rows atomically | New grouped command contract; no unseen confirmation |
| Edit / Remove equipment item | Open the exact item dialog or remove the selected Draft item after confirmation | Draft-only; quantities and source reconciliation revalidate |
| Confirm selected minimums | Confirm the displayed selected proposed rows atomically | Same Draft/package and idempotency guard |
| Remove selected minimums | Remove exactly the displayed selected proposals after confirmation | Same Draft/package and idempotency guard; no unseen row changes |
| Add/Edit/Remove requirement, service, acceptance check or supporting material | Open exact governed dialog and mutate one Draft row | Existing catalogue, objective-check, links and file rules |
| Change answer | Change Related services required and reveal or remove the governed service controls | Removing existing service rows requires explicit confirmation |
| Continue to requirements/review | Save affected task and navigate if its mapped validation groups pass | No lifecycle transition |
| Send for department approval | Lock exact content and create lead-HoD task | Existing command |
| Submit to Procurement | Record lead-HoD certification and create HOPF task | Existing command |
| Return for correction / Return to department | Capture one comment and affected section; commit return/copy | Earlier Version remains immutable; copied Draft opens directly |
| Go to affected section | Move focus to the governed section named by the return decision | Read/navigation only |
| Withdraw requisition | Open confirmation then close the pre-authorisation Version | HoD only; no drawdown or reservation; no automatic Draft |
| Change submitting department | Existing reasoned lead-change return/copy | New lead certification required; no in-place relabelling |
| Authorise requisition | Open REQ-DES-09 then invoke AuthoriseRequisition | Existing atomic Planning/Budget/REQ effects |
| Request Planning correction | Record exact owner request and stop current Version | Existing §7.4A contract; no direct Plan edit |
| View Planning request / Open Planning correction task | Navigate to the exact authorised Planning owner record or task | Read/navigation from REQ; disposition remains in Planning |
| Start a new requisition after outcome / Start new Draft | Open the fresh-start confirmation then invoke the guarded command | No resurrection or copied decision/funding |
| Continue to Tender Preparation | Navigate to TPR with exact authorised handoff | Reading/navigating creates no Tender |
| Open Tender | Navigate to the exact Tender created after handoff consumption | Read/navigation only |
| Revoke authorisation | Confirm reason and invoke guarded revocation | Only authoritative unconsumed handoff; exact reversals |
| Record details / History / Source details | Expand exact stored evidence | Read only; focus returns to trigger |
| Export | Produce the authorised read-only export for the exact displayed Version | No lifecycle change or expanded access |
| Cancel / Back | Return to exact parent without committing pending dialog work | No mutation |
| Try again / Review latest / Refresh checks | Repeat the named read and render current result | No inferred success or repeated decision |

Every new visible control must be added to this map before implementation. Labels do not rename machine commands or event schemas.

## 7. Required domain and document changes

| ID | Current issue | Required successor change | Business effect |
|---|---|---|---|
| REQ-UX-001 | Five validation groups are five user steps. | Map them to three visible tasks under §3.1. | None; all validations retained. |
| REQ-UX-002 | Ordinary screens expose drawdown/allocation/handoff language. | Adopt §3.2 business labels and keep technical evidence in supporting detail. | None; storage and APIs unchanged. |
| REQ-UX-003 | Start page is a second dense review before Draft creation. | Replace with concise, explicit start dialog. | Creation remains deliberate and side-effect free until confirmation. |
| REQ-UX-004 | Suggested minimums require separate confirmation clicks. | Add atomic grouped confirmation under §3.3. | New batch-capable command; same visible-confirmation gate. |
| REQ-UX-005 | Request quantities and equipment are split across pages. | Place both in Request details. | Same exact reconciliation and source ownership. |
| REQ-UX-006 | Technical/service/acceptance content lacks one readable hierarchy. | Place in Requirements with strong group headings and compact tables. | Same fields and catalogue. |
| REQ-UX-007 | Reviews repeat content without result-first structure. | Reuse one ordered complete-review composition for Author, HoD, HOPF and readers. | Same immutable decision content. |
| REQ-UX-008 | HOPF review leads with compatibility mechanics. | Lead with readiness/funding consequence; retain eight checks after business content. | All eight checks remain mandatory. |
| REQ-UX-009 | Return reasons do not reliably route users to the affected content. | Add governed affected-section context and direct copied-Draft opening. | One stored actionable comment; no partial approval. |
| REQ-UX-010 | Planning-correction outcomes use lifecycle terminology. | Use definite waiting/completed/no-change/new-request compositions. | Stopped Version and owner contracts unchanged. |
| REQ-UX-011 | Actor/read variants can inherit the wrong actions. | Define exact actor variants, including technical read. | Existing authority remains server-controlled. |
| REQ-UX-012 | Document approval may be mistaken for tested usability. | Add representative-user verification and blocking comprehension criteria. | Release evidence, not a new workflow. |
| REQ-UX-013 | The design contract referred to values in REQ v1.8 that were not supplied to the design tool. | Make §5 self-contained with every technical, support, acceptance, funding, compatibility and decision value required by its artboards. | None; prevents design invention and incomplete rendering. |
| REQ-UX-014 | One Requirements artboard combined mutually exclusive incomplete and complete states. | Use isolated REQ-DES-05-INCOMPLETE and REQ-DES-05-COMPLETE variants with exact deltas and action states. | None; validation and completion remain unchanged. |
| REQ-UX-015 | Contributor, HoD correction/withdrawal and lifecycle-action coverage was incomplete; Departmental Author incorrectly received Cancel draft. | Add exact actor variants, including one isolated non-production contributor-permission fixture; map every visible control; replace the unauthorised destructive label with Back to Requisitions. | Existing role authority is represented accurately; no new business role, approval stage or decision right. |

## 8. Acceptance criteria

| ID | Required result |
|---|---|
| REQ-UX-AC-01 | The Draft presents exactly three user tasks while retaining and reporting all five existing validation groups. |
| REQ-UX-AC-02 | Request details contains approved-plan amounts and equipment without requiring a separate saved page transition between them. |
| REQ-UX-AC-03 | Requirements contains all technical, warranty/support, service, acceptance and supporting-material fields with no deleted catalogue option. |
| REQ-UX-AC-04 | The start dialog creates nothing until Start requisition succeeds; reload, Cancel and opening the dialog create no root. |
| REQ-UX-AC-05 | Suggested minimums are visible before grouped confirmation; one successful command confirms exactly the selected payload or none. |
| REQ-UX-AC-06 | Copied or changed-category suggestions remain unconfirmed until the user uses Confirm selected minimums. |
| REQ-UX-AC-07 | Ordinary preparation uses the approved business labels; exact identities and machine terminology remain available in supporting evidence and unchanged contracts. |
| REQ-UX-AC-08 | Every returned Draft opens the governed affected section with the exact correction comment visible; the reviewed Version remains immutable in History. |
| REQ-UX-AC-09 | HoD and HOPF see the complete request in the same stable order, with role-specific result, statement and actions only. |
| REQ-UX-AC-10 | HOPF sees current funding amount, available-after amount, Planning availability and every material blocking exception before Authorise requisition. |
| REQ-UX-AC-11 | All eight compatibility checks remain independently visible and independently enforced; their lower placement does not reduce the gate. |
| REQ-UX-AC-12 | Authorisation confirmation states quantity, value, Budget line, available-after amount and the plain-language consequence. |
| REQ-UX-AC-13 | Authorised view contains every item, requirement, support value, acceptance check and reservation; counts never replace content. |
| REQ-UX-AC-14 | Continue to Tender Preparation performs navigation only; Tender creation remains an explicit TPR command. |
| REQ-UX-AC-15 | Planning-correction pages clearly distinguish waiting, in progress, resolved, closed without change, unavailable and another-request-open states. |
| REQ-UX-AC-16 | No stopped Version displays Resume, Clear hold, edit, approve or authorise controls. |
| REQ-UX-AC-17 | Author, direct HoD, reviewing HoD, HOPF, Procurement Officer, Planner, Auditor and technical-reader journeys have exact action sets without role switching. |
| REQ-UX-AC-18 | Technical readers can open every record state site-wide and see no business command; ordinary masked records remain Requisition not found. |
| REQ-UX-AC-19 | Save/validation failure retains still-authorised input and points to the affected section/control; no unsupported autosave is claimed. |
| REQ-UX-AC-20 | Uncertain command outcomes resolve the original idempotency identity before another decision is offered. |
| REQ-UX-AC-21 | Desktop and narrow layouts retain every decision-critical quantity, value, requirement, result and action. |
| REQ-UX-AC-22 | Keyboard, focus, contrast, long-text wrapping and dialog return comply with KT-STD-001 v1.6. |
| REQ-UX-AC-23 | Representative Departmental Author, HoD and HOPF users complete ordinary and correction tasks without button coaching and correctly explain scope, certification, funding and authorisation consequences. |
| REQ-UX-AC-24 | Any misunderstanding that an APP update expands an authorised package, that authorisation creates a Tender, or that a supporting file replaces structured requirements blocks usability acceptance and requires revision/retest. |
| REQ-UX-AC-25 | KT-STD-001 v1.6 §2 plus §5 alone supplies every exact value, control, actor/state premise and action needed to render every listed artboard; no operative phrase depends on “the v1.8 value”, “same as before” or an unavailable section. |
| REQ-UX-AC-26 | Every artboard and reset variant represents one internally possible state; incomplete and complete values, progress labels, issue summaries and enabled actions are never combined. |
| REQ-UX-AC-27 | Every actor in §4 maps to at least one explicit §5 artboard or named actor variant, including the isolated contributing-department Author. |
| REQ-UX-AC-28 | Every §5 business control appears in §6, belongs to an actor/state permitted by the lifecycle, and has its exact destination or committed result stated. A Departmental Author receives no withdrawal-equivalent control. |

## 9. Representative-user verification

Give tasks without naming controls.

| Participant | Task | Required understanding |
|---|---|---|
| Departmental Author | Prepare the supplied laptop requisition and send it for approval. | Finds approved purchase, requests amounts, lists equipment, confirms minimums and completes acceptance checks. |
| Departmental Author — correction | Correct the returned processor requirement. | Opens affected section directly; earlier reviewed content remains history. |
| Head of User Department | Check whether the request accurately represents both departments and submit it. | Understands one lead certification and both contributor rows. |
| Head of User Department — direct | Prepare and submit the request personally. | No invented self-review task. |
| Head of Procurement Function | Decide whether the request may proceed with KES 60m available. | Understands KES 50m reservation, KES 10m remaining and no Tender yet. |
| Head of Procurement Function — shortfall | Decide with only KES 40m available. | Does not attempt partial authorisation; returns or refreshes. |
| Head of Procurement Function — Planning defect | Report the wrong approved Budget Line. | Uses Planning correction, not local edit or warranty correction route. |
| Procurement Officer | Begin Tender Preparation from an authorised requisition. | Navigation versus Tender creation is understood. |
| Auditor | Find the departmental certification, authorisation, source amounts and reservations. | Historical facts are exact and current warnings do not rewrite them. |

Record completion, wrong turns, assistance, misunderstood consequence and exact participant wording. Misunderstanding of approval, included scope, funding reservation, structured requirements or Tender creation is blocking. Document approval and a successful prototype walkthrough do not count as participant evidence.

## 10. Approval effect

Approval of this amendment authorises its usability decisions for incorporation into the next complete REQ-CHG-001 successor. It does not approve REQ v1.8 as currently written, certify implementation, verify law, approve external owner changes or demonstrate user acceptance.

The complete successor must preserve the full v1.8 domain model, lifecycle, source/funding safeguards, fixed IT Equipment catalogue, structured requirement authority, audit and outstanding dependency gates except where this amendment explicitly changes presentation or grouped confirmation. It must use current approved owner-document versions and KT-STD-001 v1.6, contain the full re-implementation table and replace—not coexist with—the v1.8 implementation wording on approval.
