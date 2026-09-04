# DSP-CHG-001 — Annual Asset Disposal Plan

| Control | Value |
|---|---|
| Document ID | DSP-CHG-001 |
| Version | 0.2 |
| Date | 3 September 2026 |
| Status | **Approved** |
| Approved on | 3 September 2026 |
| Module | Asset Disposal |
| Change type | Complete successor to v0.1, which was a skeleton. Adds the full static design contract, functional interaction requirements, deterministic seed, acceptance contract and implementation constraints. |
| Standards | Governed by KT-STD-001 v1.1. Sections not restated here are inherited from it. |
| Implementation posture | New module; no legacy code to correct |

**Controlling decision:** Section 53(4) of the Act requires all asset disposals to be planned through an **annual asset disposal plan** in a format set out in the Regulations, and regulation 176(2) makes that format the **Thirteenth Schedule**. This is a distinct statutory instrument from the annual procurement plan, with its own contents, its own milestone dates, its own preparer and a different approver. MVP 1 delivers the plan and nothing downstream of it.

---

## 1. Governing decision

This document owns the annual asset disposal plan: its identity, contents, lifecycle, amendment, publication and the departmental submissions that feed it. It owns nothing about disposal proceedings.

### 1.1 Why this cannot be a section of the procurement plan

| Aspect | Annual Procurement Plan | Annual Asset Disposal Plan |
|---|---|---|
| Authority | s.53(2), reg 42 | **s.53(4), reg 176** |
| Format | Third Schedule | **Thirteenth Schedule** |
| Prepared by | Head of the Procurement Function | **Head of Procurement** |
| Countersigned by | Accounting Officer | — |
| **Approved by** | **Cabinet Secretary / CECM / Board / Council** | **Accounting Officer** |
| After approval | Versioned and immutable | **Reg 176(4): "flexible to accommodate emerging issues"** |
| Milestone dates | Nine tender-cycle dates | Nine disposal-cycle dates, ending in a PPRA notice |

The last three rows are decisive. The approver differs, the Regulations expressly require this plan to remain adaptable where the procurement plan is fixed on approval, and the milestone sets do not overlap.

### 1.2 Conflict and disposition register

| Earlier item | Disposition |
|---|---|
| Disposal items carried as `DisposalPlanItem` inside PLN-CHG-001 §4.4A | **Removed from Procurement Planning.** Section 53(4) requires a separate instrument. PLN-CHG-001 v1.9 §2 now names disposal planning of any kind as a non-goal, and PLN-AC-095 asserts no disposal record exists there. |
| Disposal reason value `Expired` | **Removed.** Not statutory. Section 163(1) and regulation 176(1) give exactly four: unserviceable, surplus, obsolete, obsolescent. |
| Disposal method value `Destruction` | **Removed.** Not statutory. Section 165(1) gives five: transfer to another public entity, sale by public tender, sale by public auction, trade-in, waste disposal management. |
| `estimated_proceeds` | **Renamed** `estimated_current_value`, per Thirteenth Schedule column 7 and regulation 176(3)(f). It is a planning estimate and is fenced off from the reserve price, which section 164(3) assigns to the disposal committee or a technical expert. |
| Approval by the statutory authority | **Corrected to the Accounting Officer**, per the Thirteenth Schedule signature block. See §5.4 for the State or County Department question. |
| v0.1's stub design contract | **Replaced** by the complete closed-input contract in §11. |

### 1.3 Scope exclusions

This module does not contain: the board of survey; valuation, the technical report or the **reserve price**; disposal committee proceedings, minutes or recommendations; bidder registration, public auction or public tender conduct; award, fall of hammer, notification or contract signature as *events*; proceeds accounting; asset write-off; or the asset register itself.

Those belong to Part XIV of the Act and to a later **Asset Disposal Proceedings** change unit. The plan records the *planned dates* on which those activities are expected to occur, and the *actual dates* on which they concluded. It records nothing about their content.

This module also maintains no asset register. The plan **references** the entity's register by number; it does not own, replicate or browse it.

---

## 2. Purpose and outcomes

Asset Disposal shall provide: one annual asset disposal plan for each Fiscal Year; departmental disposal submissions certified by each head of user department; a consolidated plan in the Thirteenth Schedule format prepared by the Head of Procurement and approved by the Accounting Officer; a governed amendment path that satisfies regulation 176(4) without rewriting approved content; planned and actual milestone dates with derived variance; and immutable evidence of every decision.

It shall not provide: any disposal proceeding, any valuation, any reserve price, any committee workflow, any bidder-facing surface, any proceeds or accounting entry, any asset register, or any procurement record.

The data-purpose gate and the omission default are in KT-STD-001 §7. Purchase date, purchase price and item life span pass that gate because the Thirteenth Schedule requires them as columns 5, 6 and 9 — not because they are generally interesting.

---

## 3. Fixed external constraints and ownership

| ID | Constraint |
|---|---|
| DSP-EC-001 | The plan format is the Thirteenth Schedule. Columns are not added, removed or reordered in the published artefact. |
| DSP-EC-002 | Disposal reasons and methods are closed statutory lists. Neither is extensible by configuration. |
| DSP-EC-003 | Radioactive and electronic waste may be disposed of only to persons licensed under the Environmental Management and Co-ordination Act (s.165(2)). |
| DSP-EC-004 | The plan shall be flexible to accommodate emerging issues in the disposal process (reg 176(4)). |

| Record or concern | Owner | Relationship |
|---|---|---|
| Site Procuring Entity, ERPNext Fiscal Year, Organisation Units, `UOM`, disposal-plan intake flag | CFG-CHG-002 v0.8 | Read only; fail closed when absent. |
| Business authority, role registry, permission hooks | AUTH-ADR-001 v1.6 | Declare required roles; implement no permission mechanism. |
| Annual asset disposal plan, versions, items, amendments, departmental submissions | This document | Create, govern, expose. |
| Asset register and asset records | Outside KenTender in MVP 1 | Referenced by number only. |
| Reserve price, valuation, board of survey, committee proceedings, sale | A later Asset Disposal Proceedings change unit | Not modelled here. |
| Annual procurement plan | PLN-CHG-001 v1.9 | Wholly separate. No shared record, screen or payload. |

Dependency direction: **Configuration & Governance → Asset Disposal**. This module imports no downstream controller and is imported by none.

---

## 4. Canonical domain model

All identifiers are server-generated. Framework audit fields remain framework-managed.

### 4.1 AssetDisposalPlan

| Field | Operational purpose and system effect |
|---|---|
| `disposal_plan_id` | Immutable generated reference used by routes, services, audit and publication. |
| `fiscal_year` | The ERPNext `Fiscal Year` the plan covers. Required and immutable after creation. |
| `active_version_id` | Points to the sole Active Version. Empty before first approval. |
| `open_version_id` | Points to the sole Draft or Submitted-for-approval Version. Empty when none. |

There is at most one AssetDisposalPlan per Fiscal Year and at most one open Version. The display title derives as `{entity name} Annual Asset Disposal Plan {FY period}` and is not stored.

### 4.2 AssetDisposalPlanVersion

| Field | Operational purpose and system effect |
|---|---|
| `disposal_plan_version_id` | Immutable generated reference used by items, amendments and audit. |
| `disposal_plan_id` | Links the Version to its stable plan. |
| `version_number` | Ordered history, generated per plan. |
| `based_on_version_id` | The Active Version copied to create a successor. Empty for Version 1. |
| `status` | `Draft`, `Submitted for approval`, `Active` or `Superseded`. |
| `return_reason` | Recorded on the decision event when the Accounting Officer returns a Version. Not a Version field. |

Prepared, submitted, approved and superseded actors and timestamps are audit events.

### 4.3 AssetDisposalPlanAmendment

Regulation 176(4) requires the plan to be flexible for emerging issues. An amendment satisfies that without rewriting approved content.

| Field | Operational purpose and system effect |
|---|---|
| `amendment_id` | Immutable generated reference stamped on every item it introduces. |
| `disposal_plan_version_id` | The Active Version being amended. |
| `amendment_number` | Ordered sequence per Version. |
| `reason` | Why an item could not have been planned at approval; 20–500 characters. Required. |
| `status` | `Draft`, `Submitted for approval` or `Approved`. |

An amendment **appends items only**. It never alters, reprices, reschedules or removes an item already in the Active Version. Removing or changing an approved item requires a successor Version. Approved amendments are immutable.

### 4.4 AssetDisposalPlanItem

Fields follow the Thirteenth Schedule columns and the regulation 176(3) content list.

| Field | Schedule column or authority |
|---|---|
| `disposal_item_id` | Immutable generated reference. |
| `disposal_plan_version_id` | Binds the item to one Version. |
| `amendment_id` | Set only where the item entered by amendment. Empty for items approved with the Version. |
| `organisation_unit_id` | The disposing user department. Not a Schedule column; required to route the departmental submission and to evidence segregation under s.45(4). |
| `item_number` | Col 1 — No. Generated in Schedule order. |
| `item_description` | Col 2 — Item Description. Required, 5–300 characters. |
| `quantity` | Col 3 — Qty. Positive. |
| `unit_of_issue` | Col 4 — Unit of Issue. Enabled ERPNext `UOM` only. |
| `date_of_purchase` | Col 5 — Date of purchase. Not in the future. |
| `purchase_price_minor_units` | Col 6 — Purchase Price. Zero permitted for donated or transferred assets. |
| `estimated_current_value_minor_units` | Col 7 — Estimated current value. A **planning estimate**. Zero permitted where the method is waste disposal management. |
| `disposal_justification` | Col 8 — Justification for disposal. Free text, 20–500 characters, in addition to the governed reason. |
| `disposal_reason` | s.163(1), reg 176(1). Governed: `Unserviceable`, `Surplus`, `Obsolete`, `Obsolescent`. |
| `item_life_span_years` | Col 9 — Item Life span. Positive integer. |
| `asset_register_reference` | Col 10 — Ref No to the asset register. The entity's own reference. Required. |
| `disposal_method` | Col 11 — Disposal Method. Governed by s.165(1): `Transfer to another public entity`, `Sale by public tender`, `Sale by public auction`, `Trade-in`, `Waste disposal management`. |
| `transfer_has_financial_adjustment` | Required only where the method is transfer. See §4.6. |
| `cost_of_managing_disposal_minor_units` | Col 12 — Cost of managing disposal. Reg 176(3)(m). |
| `disposal_manager` | Reg 176(3)(l): `Procuring entity`, `Special agency`, `Hired expert`. Required. No Schedule column exists; it is required plan content. |
| `is_disposal_to_employee` | Check. Where set, `notice_to_ppra_date` becomes required and the s.166 restriction displays. |

**Planned milestone dates** — the Thirteenth Schedule "Dates for completing key disposal activities", in Schedule order:

| Field | Schedule label |
|---|---|
| `planned_disposal_initiation_date` | Disposal Initiation |
| `planned_bid_documents_prepared_date` | Bid Documents Prepared |
| `planned_invitation_date` | Invitation To Tender/Public Auction |
| `planned_bid_opening_date` | Bid Opening/Registration of Bidders |
| `planned_award_date` | Accounting officer Award/Fall of Auction Hammer |
| `planned_notification_date` | Notification of Award |
| `planned_contract_signed_date` | Contract Signed |
| `planned_disposal_completed_date` | Disposal Completed |
| `planned_notice_to_ppra_date` | Notice to PPRA (if Disposal to Employee) |

Each has a corresponding `actual_*_date`, recorded as the activity concludes. `planned_days`, `actual_days` and `variance_days` are derived per milestone; variance is planned minus actual and exists only once the actual date does.

Milestone dates are set by the Head of Procurement during consolidation, not by the department. All planned dates fall within the plan's Fiscal Year and are chronologically ordered.

### 4.5 DepartmentalDisposalSubmission

Regulation 34(i) makes the user department responsible for preparing departmental procurement **and asset disposal** plans and submitting them to the procurement function.

| Field | Operational purpose and system effect |
|---|---|
| `submission_id` | Immutable generated reference. |
| `fiscal_year` / `organisation_unit_id` | One submission per unit per Fiscal Year. |
| `status` | `Draft`, `Submitted`, `Returned` or `Accepted`. |
| `submitted_by` / `submitted_at` | The Head of User Department who certified it. Server-set. |
| `return_reason` | Recorded on the return decision event. |

Submission items carry every §4.4 field **except** the milestone dates, `item_number` and `amendment_id`.

The fixed attestation, rendered with department and financial year:

> I certify that this departmental asset disposal submission lists the assets of {department} identified as unserviceable, surplus, obsolete or obsolescent for {financial_year}, that each is recorded in the entity's asset register at the reference shown, and that the estimated current values are honest planning estimates and not valuations.

### 4.6 The transfer boundary

Section 165(1)(a) lists transfer to another public entity **with or without financial adjustment** as a disposal method. Section 4(2)(b) excludes transfer of assets between public entities **without financial consideration** from the Act altogether.

The plan therefore records `transfer_has_financial_adjustment` on every transfer item. Where it is false, the item is retained in the plan for completeness and flagged on its face as **outside the Act's application**. No inference is drawn either way, no rule is relaxed, and the point is not resolved by this document.

### 4.7 DisposalAuditEvent

Append-only: event ID and type; plan, version, amendment, item and submission IDs as applicable; actor; business role; the exercised responsibility assignment ID; timestamp; before and after status; required reason; and correlation ID. Users do not create or edit audit events.

---

## 5. Lifecycle and invariants

### 5.1 Departmental submission lifecycle

| Current status | Command | Next status | Authorised actor |
|---|---|---|---|
| — | Open departmental submission | Draft | Departmental Author or Head of User Department |
| Draft | Save | Draft | Departmental Author or Head of User Department |
| Draft | Submit departmental disposal plan | Submitted | **Head of User Department only** |
| Submitted | Return to department | Returned | Head of Procurement; reason required |
| Returned | Resubmit | Submitted | Head of User Department |
| Submitted | Accept | Accepted | Head of Procurement |

An Accepted submission is immutable. Its items enter the open Draft plan Version.

### 5.2 Plan version lifecycle

| Current status | Command | Next status | Authorised actor |
|---|---|---|---|
| — | Create Version 1 | Draft | System, on first submission acceptance |
| Draft | Set milestone dates, order items | Draft | Head of Procurement |
| Draft | Submit for approval | Submitted for approval | Head of Procurement |
| Submitted for approval | Return for correction | Draft correction | Accounting Officer; reason required |
| Submitted for approval | Approve | Active | Accounting Officer |
| Active | Create successor | Draft successor | Head of Procurement |
| Active | Amend | Amendment Draft | Head of Procurement |
| Draft successor approved | — | Predecessor Superseded | System, in the approval transaction |

### 5.3 Amendment lifecycle

| Current status | Command | Next status | Authorised actor |
|---|---|---|---|
| Active Version | Open amendment | Amendment Draft | Head of Procurement |
| Amendment Draft | Submit amendment | Submitted for approval | Head of Procurement |
| Submitted for approval | Approve amendment | Approved; items appended to the Active Version | Accounting Officer |
| Submitted for approval | Return amendment | Amendment Draft | Accounting Officer; reason required |

At most one open amendment per Active Version.

### 5.4 Approval authority

The Thirteenth Schedule signature block names **Prepared by: Head of Procurement** and **Approved by: Accounting Officer**. This document follows the prescribed format.

Section 53(5) provides that procurement and asset disposal planning shall be approved by the Cabinet Secretary or the County Executive Committee member **in the case of a State Department or County Department**. Where an entity's own counsel determines that the higher approval applies to the disposal plan, Configuration & Governance records it as an **additional** stage after the Accounting Officer, never as a substitute. MVP 1 defaults to the Accounting Officer alone, and this document does not resolve the point.

### 5.5 Invariants

| ID | Rule and enforcement |
|---|---|
| DSP-BR-001 | Every write requires an Active `User Responsibility Assignment` for the required role, resolved server-side through the registered permission hooks. |
| DSP-BR-002 | One AssetDisposalPlan and one Active Version per Fiscal Year, enforced by a database-level partial unique index **and** in the approval transaction. |
| DSP-BR-003 | One departmental submission per Organisation Unit per Fiscal Year. |
| DSP-BR-004 | `disposal_reason` is one of the four statutory values. No configuration extends the list. |
| DSP-BR-005 | `disposal_method` is one of the five statutory values. No configuration extends the list. |
| DSP-BR-006 | Every item records description, quantity, unit, purchase date, purchase price, estimated current value, justification, reason, life span, asset register reference, method, cost of managing disposal and disposal manager before its submission may be submitted. |
| DSP-BR-007 | `estimated_current_value_minor_units` is a planning estimate. It is never labelled, exported, converted into or used to derive a reserve price. |
| DSP-BR-008 | Where `disposal_method` is `Waste disposal management`, the item carries the section 165(2) licensing requirement on its face and in the published payload. |
| DSP-BR-009 | Where `is_disposal_to_employee` is set, `planned_notice_to_ppra_date` is required and the section 166 restriction displays on the item. |
| DSP-BR-010 | Planned milestone dates are chronologically ordered and fall within the plan's Fiscal Year. |
| DSP-BR-011 | An actual date may be recorded only against a milestone whose planned date exists, and only on an Active Version. |
| DSP-BR-012 | Section 45(4) segregation: the Head of User Department who identifies, the Head of Procurement who consolidates and prepares, and the Accounting Officer who approves shall be three different persons for any one plan Version. Pricing and the disposal itself are outside this module and shall not be performed within it by any of them. |
| DSP-BR-013 | The Head of Procurement who prepared a Version or amendment cannot approve it, enforced from the preparation audit event rather than by role comparison. |
| DSP-BR-014 | An amendment appends items only. Any attempt to alter, reprice, reschedule or remove an existing Active item is rejected. |
| DSP-BR-015 | Approving a successor Version atomically activates it and supersedes the predecessor, preserving all item identities and their recorded actuals. |
| DSP-BR-016 | Submitted, Active and Superseded content is read-only. Actual-date recording on an Active Version is the sole exception and is append-only. |
| DSP-BR-017 | Every state command carries `expected_version`; a stale command has no partial effect. Every retriable command carries an idempotency key. |
| DSP-BR-018 | Generated references, statuses, derived days and audit data are never client-editable. |
| DSP-BR-019 | Records are never physically deleted after first submission. |

---

## 6. Roles and segregation

| Business role | Scope type | Permitted work |
|---|---|---|
| Departmental Author | Organisation Unit | Draft departmental submission content for the assigned unit. |
| Head of User Department | Organisation Unit | Certify and submit the departmental submission; resubmit a returned one. |
| Head of Procurement | Site-wide | Accept or return submissions; consolidate; set milestone dates; prepare and submit Versions and amendments; record actual dates. |
| Accounting Officer | Site-wide | Approve or return a Version or amendment. |
| Auditor | Site-wide or approved OU oversight scope | Neutral read of the plan and its evidence. No mutation. |

All are registered in the AUTH-ADR-001 v1.6 §4.4 registry. **Head of Procurement** is a new registry entry, site-wide, not an `exclusive_office`. It is **not** the Procurement Planner, which owns the annual procurement plan; the two are distinct responsibilities and may be held by different people.

Departmental Author, Head of User Department, Accounting Officer and Auditor are existing entries reused unchanged.

**Segregation matrix.** A user who has done the left may not do the right for the same plan Version:

| Performed | Barred from |
|---|---|
| Submitted a departmental submission as Head of User Department | Accepting that submission; approving the Version containing its items |
| Consolidated or prepared a Version or amendment as Head of Procurement | Approving that Version or amendment |
| Approved a Version as Accounting Officer | Nothing further in this module; approval is terminal |

Administrator and System Manager receive technical read under AUTH-ADR-001 v1.6 §8 and no business action.

---

## 7. Service and command contracts

| Contract | Required input | Output and effect |
|---|---|---|
| `resolve_disposal_plan_context` | Fiscal Year | The Active plan and Version summary, or a typed not-found error. |
| `list_disposal_plan_items` | Version ID; optional unit, method, reason filters and paging | Items with Schedule fields, planned and actual dates and derived variance. |
| `get_disposal_plan_item` | Item ID | Full authorised item detail and its audit history. |

| Command | Purpose |
|---|---|
| `save_departmental_disposal_draft` | Create or update Draft submission items as one validated change set. |
| `submit_departmental_disposal_plan` | Validate readiness, lock the immutable snapshot, create the consolidation task. |
| `return_departmental_disposal_submission` | Require a reason and return the submission to the department. |
| `accept_departmental_disposal_submission` | Place accepted items into the open Draft plan Version, creating Version 1 idempotently on first acceptance. |
| `save_disposal_plan_draft` | Set milestone dates and item order on a Draft Version. |
| `submit_disposal_plan_version` | Validate contents, chronology and segregation; move Draft to Submitted for approval. |
| `return_disposal_plan_version` | Require a reason and create the next numbered Draft correction. |
| `approve_disposal_plan_version` | Revalidate responsibility, contents, chronology and segregation under lock; activate and supersede atomically. |
| `create_disposal_plan_successor` | Copy the Active Version and item identities into one Draft successor. |
| `open_disposal_plan_amendment` | Open the sole amendment Draft on an Active Version. |
| `submit_disposal_plan_amendment` | Validate appended items and move the amendment to Submitted for approval. |
| `approve_disposal_plan_amendment` | Revalidate and append the amendment's items to the Active Version atomically. |
| `record_disposal_actual_date` | Record one actual date against a planned milestone on an Active Version; derive variance. |

Every mutation is authorised and validated server-side. Options, derived days, available actions and readiness come from the server.

---

## 8. Error contract

| Code | User-visible result |
|---|---|
| `DSP_RESPONSIBILITY_REQUIRED` | You are not assigned the responsibility required for this action. |
| `DSP_PLAN_EXISTS` | This financial year already has an asset disposal plan. |
| `DSP_SUBMISSION_EXISTS` | This department already has a disposal submission for this financial year. |
| `DSP_INVALID_REASON` | The disposal reason must be unserviceable, surplus, obsolete or obsolescent. |
| `DSP_INVALID_METHOD` | The disposal method is not one permitted by the Act. |
| `DSP_CONTENTS_INCOMPLETE` | One or more items are missing content the disposal plan format requires. Every failing item and field is returned. |
| `DSP_DATES_OUT_OF_ORDER` | Planned disposal dates must be in order and within the financial year. |
| `DSP_EMPLOYEE_DISPOSAL_NOTICE_REQUIRED` | A disposal to an employee requires a planned notice date for the Authority. |
| `DSP_SEGREGATION_BLOCKED` | You cannot perform this action because you completed an incompatible earlier step. |
| `DSP_AMENDMENT_ALTERS_EXISTING` | An amendment may only add items. Changing or removing an approved item requires a successor version. |
| `DSP_AMENDMENT_OPEN` | This plan already has an open amendment. |
| `DSP_INVALID_STATE` | This action is not available in the record's current state. |
| `DSP_STALE_WRITE` | This record changed after you opened it. Refresh and review the latest version. |

Message conventions are in KT-STD-001 §11.

---

## 9. UI architecture, menu and routes

Asset Disposal is a top-level KenTender module. Its menu contains **Disposal plan** and **Approval tasks**, the latter visible only to an Accounting Officer.

| Screen | Canonical route | Purpose |
|---|---|---|
| DSP-UI-01 Disposal plan workspace | `/app/asset-disposal` | The Fiscal Year's plan, its items and the department's own submission. |
| DSP-UI-02 Departmental submission | `/app/asset-disposal/submission/{submission_id}` | Draft, certify, submit and correct a departmental submission. |
| DSP-UI-03 Consolidation | `/app/asset-disposal/plan/{plan_id}/version/{version_number}` | Accept submissions, set milestone dates, submit for approval. |
| DSP-UI-04 Approval task | `/app/asset-disposal/approval/{version_id}` | Accounting Officer review and decision, for a Version or an amendment. |

The consolidation screen uses URL-backed **Submissions**, **Plan items** and **History** tabs. The approval task uses **Overview**, **Plan items** and **History**. This document authorises no second shell, header, breadcrumb or global selector.

---

## 10. Publication

The approved plan is published in the Thirteenth Schedule format. The published payload carries every Schedule column in Schedule order, the header block (Financial Year, Name of the Procuring Entity) and the signature block naming the Head of Procurement who prepared it and the Accounting Officer who approved it.

The disposal plan is **published separately from the annual procurement plan**. They are distinct statutory instruments and are never combined into one payload or one artefact.

MVP 1 publishes to a configured destination and performs no Authority transmission. Section 53(12)'s invitation-to-treat characterisation attaches to the procurement plan and is not asserted for the disposal plan.

---

## 11. Static Claude Design contract

Supply **KT-STD-001 §2 plus this section** to Claude Design. Nothing else. The closed-input rules, product-wide prohibitions, approved desktop shell, page-header pattern, fixture-context block and division of supply are in KT-STD-001 §2.2–2.5 and are not repeated. Fixture actors, organisation units, fiscal years and units come from KT-STD-001 §8, extended by §13.1.

**Additional prohibitions for this document:** do not show a reserve price, valuation, board of survey, technical report, disposal committee, bidder, auction proceeding, proceeds, accounting entry, asset write-off, asset register browser, photograph, condition rating, depreciation schedule, Procuring Entity selector, Strategy field, procurement plan item or budget field. Do not show a "proceeds" label anywhere; the value column is **Estimated current value**.

### 11.1 DSP-DES-01 — Disposal plan workspace, Active plan

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 18 Jun 2027, 14:20 EAT · Frappe header breadcrumb: **Home > Asset Disposal**

**Page content header**

- Eyebrow: **ASSET DISPOSAL**
- Title: **Annual Asset Disposal Plan**
- Description: **The assets this entity has planned to dispose of, and the dates each disposal is expected to follow.**
- No header action button

**Filter row**

- select showing **FY 2027/28**
- select showing **All departments**
- select showing **All methods**

**Plan summary card**

- Heading: **Ministry of Health Annual Asset Disposal Plan 2027/28**
- Status: **Active**

| Label | Value |
|---|---|
| Plan reference | DSP-MOH-2027-001 |
| Active version | Version 1 |
| Items planned | 2 |
| Estimated current value | KES 1,130,000 |
| Cost of managing disposal | KES 85,000 |
| Prepared by | Charles Mutiso · 4 Jun 2027 |
| Approved by | Amina Hassan · 11 Jun 2027 |

**Plan items table**

| No. | Item description | Department | Qty | Unit | Reason | Method | Estimated current value | Disposal completed | Action |
|---|---|---|---:|---|---|---|---:|---|---|
| 1 | Desktop computers, assorted models | Digital Health | 45 | Each | Obsolete | Sale by public auction | KES 180,000 | 30 Nov 2027 | View |
| 2 | Toyota Land Cruiser, registration GKB 411X | HR Management and Development | 1 | Each | Unserviceable | Trade-in | KES 950,000 | 28 Feb 2028 | View |

Below the table: **2 items · KES 1,130,000 estimated current value**

Do not show a create action on this Active-state artboard, a reserve price column, or a proceeds column.

### 11.2 DSP-DES-02 — Departmental submission, Draft

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Author · Digital Health · 4 May 2027, 09:40 EAT · Frappe header breadcrumb: **Home > Asset Disposal > Digital Health submission**

**Page content header**

- Eyebrow: **DSS-MOH-DHI-2027**
- Title: **Digital Health disposal submission**
- Status: **Draft**
- Right-aligned primary button: **Add asset**

**Submission context card**

| Label | Value |
|---|---|
| Department | Digital Health |
| Financial year | FY 2027/28 |
| Items listed | 1 |

**Items table**

| Item description | Qty | Unit | Reason | Method | Asset register ref | Estimated current value | Action |
|---|---|---:|---|---|---|---:|---|
| Desktop computers, assorted models | 45 | Each | Obsolete | Sale by public auction | MOH/ICT/2019/0451 | KES 180,000 | Edit · Remove |

**Fixed footer, left to right:** **Save draft**, **Submit to procurement**. **Submit to procurement** is the primary button and is shown **disabled**.

Quiet text beside the disabled button: **Only the head of department can submit.**

Do not show milestone date fields, an item number column, a reserve price, a valuation, or an approval control.

### 11.3 DSP-DES-03 — Add asset dialog

520 px modal over a dimmed DSP-DES-02.

- Title: **Add asset for disposal**

| Field label | Displayed value | Component |
|---|---|---|
| Item description | Desktop computers, assorted models | Single-line input |
| Quantity | 45 | Numeric input |
| Unit of issue | Each | Select |
| Date of purchase | 12 Mar 2019 | Date input |
| Purchase price | KES 3,150,000 | Currency input, KES prefix |
| Estimated current value | KES 180,000 | Currency input, KES prefix |
| Item life span | 5 years | Numeric input with the suffix **years** |
| Asset register reference | MOH/ICT/2019/0451 | Single-line input |
| Reason for disposal | Obsolete | Select |
| Justification | Replaced under the 2026 end-user device refresh; units are beyond economic repair and unsupported by the manufacturer. | Multiline text area |
| Proposed disposal method | Sale by public auction | Select |
| Cost of managing disposal | KES 60,000 | Currency input, KES prefix |
| Disposal to be managed by | Procuring entity | Select |
| Disposal to an employee | Unchecked | Checkbox |

Quiet helper text beneath **Estimated current value**: **A planning estimate only. The reserve price is set later by the disposal committee.**

**Footer buttons:** **Cancel** and primary **Add asset**

Do not show a reserve price, valuation, photograph, condition rating, depreciation, milestone date or notice-to-PPRA field on this artboard.

### 11.4 DSP-DES-04 — Submit departmental submission dialog

520 px modal over a dimmed DSP-DES-02, with the fixture actor changed.

**Fixture context — outside the artboard:** Dr Peter Kimani · `peter.kimani@moh.example.test` · Head of User Department · Digital Health · 6 May 2027, 11:05 EAT

- Title: **Submit disposal submission?**
- Text: **This submission lists 1 asset with an estimated current value of KES 180,000. Once submitted it cannot be edited unless procurement returns it.**

**Certification panel** — read-only, in the approved quiet panel style:

> I certify that this departmental asset disposal submission lists the assets of Digital Health identified as unserviceable, surplus, obsolete or obsolescent for FY 2027/28, that each is recorded in the entity's asset register at the reference shown, and that the estimated current values are honest planning estimates and not valuations.

- Footer buttons: **Cancel** and primary **Certify and submit**

### 11.5 DSP-DES-05 — Consolidation, Submissions tab

**Fixture context — outside the artboard:** Charles Mutiso · `charles.mutiso@moh.example.test` · Head of Procurement · 28 May 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Asset Disposal > DSP-MOH-2027-001 > Version 1**

**Page content header**

- Eyebrow: **DSP-MOH-2027-001 · VERSION 1**
- Title: **Consolidate asset disposal plan**
- Status: **Draft**
- No header action button

**Tabs:** **Submissions** selected, **Plan items**, **History**

**Submissions table**

| Department | Submitted by | Submitted | Items | Estimated current value | Status | Action |
|---|---|---|---:|---:|---|---|
| Digital Health | Dr Peter Kimani | 6 May 2027 | 1 | KES 180,000 | Submitted | Review |
| HR Management and Development | Dr Peter Kimani | 11 May 2027 | 1 | KES 950,000 | Accepted | View |

Below the table: **2 submissions · 1 awaiting review**

Do not show a create-submission action, an approval control or a reserve price column.

### 11.6 DSP-DES-06 — Consolidation, Plan items tab with milestone dates

**Fixture context — outside the artboard:** Charles Mutiso · `charles.mutiso@moh.example.test` · Head of Procurement · 4 Jun 2027, 09:30 EAT · Frappe header breadcrumb: **Home > Asset Disposal > DSP-MOH-2027-001 > Version 1**

Reuse the DSP-DES-05 page content header without changing its content or placement.

**Tabs:** **Submissions**, **Plan items** selected, **History**

**Plan items table**

| No. | Item description | Department | Reason | Method | Estimated current value | Dates set | Action |
|---|---|---|---|---|---:|---|---|
| 1 | Desktop computers, assorted models | Digital Health | Obsolete | Sale by public auction | KES 180,000 | Complete | Edit dates |
| 2 | Toyota Land Cruiser, registration GKB 411X | HR Management and Development | Unserviceable | Trade-in | KES 950,000 | Not set | Edit dates |

**Readiness card**

- Heading: **Plan readiness**

| Check | Result |
|---|---|
| Every item has complete Thirteenth Schedule content | Ready |
| Every item has disposal dates in order and within the year | 1 item outstanding |
| Segregation of duties | Ready |

The first and third rows use the approved ready state badge; the second uses the approved outstanding state badge.

**Fixed footer, left to right:** **Save draft**, **Submit for approval**. **Submit for approval** is primary and shown **disabled**.

### 11.7 DSP-DES-07 — Disposal dates dialog

520 px modal over a dimmed DSP-DES-06.

- Title: **Disposal dates — Desktop computers, assorted models**
- Intro text: **Planned dates for the key disposal activities. All dates must fall within FY 2027/28.**

| Field label | Displayed value |
|---|---|
| Disposal initiation | 3 Aug 2027 |
| Bid documents prepared | 17 Aug 2027 |
| Invitation to tender or public auction | 31 Aug 2027 |
| Bid opening or registration of bidders | 21 Sep 2027 |
| Award or fall of the hammer | 5 Oct 2027 |
| Notification of award | 12 Oct 2027 |
| Contract signed | 26 Oct 2027 |
| Disposal completed | 30 Nov 2027 |
| Notice to the Authority | Not applicable |

All rows use the approved date input component except **Notice to the Authority**, which uses the approved read-only field.

Quiet helper text beneath the last row: **Required only where the asset is disposed of to an employee.**

- Footer buttons: **Cancel** and primary **Save dates**

### 11.8 DSP-DES-08 — Approval task

**Fixture context — outside the artboard:** Amina Hassan · `amina.hassan@moh.example.test` · Accounting Officer · 11 Jun 2027, 15:40 EAT · Frappe header breadcrumb: **Home > Asset Disposal > Approval tasks > DSP-MOH-2027-001-V1**

**Page content header**

- Eyebrow: **DSP-MOH-2027-001 · VERSION 1**
- Title: **Approve asset disposal plan**
- Status: **Submitted for approval**
- No header action button

**Tabs:** **Overview** selected, **Plan items**, **History**

**Plan identity card**

| Label | Value |
|---|---|
| Financial year | FY 2027/28 |
| Submitted version | Version 1 |
| Items | 2 |
| Estimated current value | KES 1,130,000 |
| Cost of managing disposal | KES 85,000 |
| Departments contributing | 2 |

**Preparation authority card**

| Label | Value |
|---|---|
| Prepared by | Charles Mutiso |
| Submitted | 4 Jun 2027, 16:05 EAT |

**Readiness card**

| Check | Result |
|---|---|
| Every item has complete Thirteenth Schedule content | Ready |
| Every item has disposal dates in order and within the year | Ready |
| Segregation of duties | Ready |

**Method summary card**

| Disposal method | Items | Estimated current value |
|---|---:|---:|
| Sale by public auction | 1 | KES 180,000 |
| Trade-in | 1 | KES 950,000 |

**Fixed footer, left to right:** **Return for correction**, **Approve plan**. **Return for correction** uses the danger-outline style; **Approve plan** is primary.

Do not show editable fields, a reserve price, a valuation, comments or attachments.

### 11.9 DSP-DES-09 — Item detail with actuals and variance

**Fixture context — outside the artboard:** Charles Mutiso · `charles.mutiso@moh.example.test` · Head of Procurement · 8 Dec 2027, 11:00 EAT · Frappe header breadcrumb: **Home > Asset Disposal > DSP-MOH-2027-001 > Item 1**

**Page content header**

- Eyebrow: **DSP-MOH-2027-001 · ITEM 1**
- Title: **Desktop computers, assorted models**
- Status: **Active**
- No header action button

**Asset card**

| Label | Value |
|---|---|
| Department | Digital Health |
| Quantity | 45 Each |
| Date of purchase | 12 Mar 2019 |
| Purchase price | KES 3,150,000 |
| Estimated current value | KES 180,000 |
| Item life span | 5 years |
| Asset register reference | MOH/ICT/2019/0451 |
| Reason for disposal | Obsolete |
| Justification | Replaced under the 2026 end-user device refresh; units are beyond economic repair and unsupported by the manufacturer. |
| Disposal method | Sale by public auction |
| Cost of managing disposal | KES 60,000 |
| Managed by | Procuring entity |

**Disposal progress table**

| Activity | Planned | Actual | Variance |
|---|---|---|---|
| Disposal initiation | 3 Aug 2027 | 3 Aug 2027 | 0 days |
| Bid documents prepared | 17 Aug 2027 | 24 Aug 2027 | −7 days |
| Invitation to tender or public auction | 31 Aug 2027 | 7 Sep 2027 | −7 days |
| Bid opening or registration of bidders | 21 Sep 2027 | 28 Sep 2027 | −7 days |
| Award or fall of the hammer | 5 Oct 2027 | — | — |
| Notification of award | 12 Oct 2027 | — | — |
| Contract signed | 26 Oct 2027 | — | — |
| Disposal completed | 30 Nov 2027 | — | — |
| Notice to the Authority | Not applicable | — | — |

Negative variance values use the approved negative-value treatment. Empty actuals show an em dash, not a zero.

**Fixed footer:** right-aligned secondary button **Record actual date**

### 11.10 DSP-DES-10 — Amend Active plan dialog

520 px modal over a dimmed DSP-DES-01.

**Fixture context — outside the artboard:** Charles Mutiso · `charles.mutiso@moh.example.test` · Head of Procurement · 14 Jan 2028, 10:20 EAT

- Title: **Add assets to the approved plan**
- Text: **The approved plan stays as it is. Assets you add here are appended and go to the accounting officer for approval.**

| Field label | Displayed value |
|---|---|
| Reason for the addition | Server room air-conditioning units failed in December 2027 and were condemned after the plan was approved. |

**Notice panel**

- Heading: **Additions only**
- Text: **You cannot change or remove an asset already in the approved plan. That requires a new version.**

- Footer buttons: **Cancel** and primary **Start addition**

### 11.11 DSP-DES-11 — Common states

Five variants using the DSP-DES-01 page content header and filter row. State treatments follow KT-STD-001 §3.

Fixture context for Loading, No plan and Server error — outside the artboard: **Charles Mutiso · `charles.mutiso@moh.example.test` · Head of Procurement · 4 May 2027, 08:30 EAT**. For No submissions: **Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Author · Digital Health**. For Forbidden: **Samuel Otieno · `samuel.otieno@moh.example.test` · No Asset Disposal responsibility**. Breadcrumb for all: **Home > Asset Disposal**.

| Variant | Main content | Buttons |
|---|---|---|
| Loading | One skeleton summary card and three skeleton table rows | None |
| No plan | Heading **No asset disposal plan for FY 2027/28.** Body **Departments submit the assets they intend to dispose of, and procurement consolidates them into the annual plan.** | **Open departmental submission** |
| No submissions | Heading **Your department has not listed any assets.** Body **Add the assets Digital Health intends to dispose of during FY 2027/28.** | **Add asset** |
| Forbidden | Heading **You do not have access to Asset Disposal.** Body **Ask your KenTender administrator to review your assigned responsibilities.** | None |
| Server error | Heading **The asset disposal plan could not be loaded.** Body **Try again. If the problem continues, contact KenTender support.** | **Try again** |

### 11.12 Existing controls

No artboard is authorised for the Frappe header, breadcrumb, module menu, global page chrome, notifications or user menu. Reuse those without visual modification, per KT-STD-001 §2.5.

---

## 12. Functional interaction requirements — excluded from design prompts

Common page behaviour and accessibility follow KT-STD-001 §3.

### 12.1 DSP-UI-01 — Workspace

- The workspace resolves the plan for the selected Fiscal Year. It never selects the first plan or the first year.
- The Financial Year select is a local view filter that grants nothing and is ignored when stale.
- Rows and counts use one server predicate. A department-scoped actor sees the whole approved plan but may act only on its own submission.
- **Open departmental submission** appears only where the actor holds an Organisation Unit assignment, the disposal-plan intake flag is open for the year and no submission exists for that unit.
- Estimated current value totals are server-computed and never summed in the client.

### 12.2 DSP-UI-02 — Departmental submission

- Add, edit and remove operate on Draft items as one validated change set with optimistic concurrency.
- Unit of issue offers only enabled ERPNext `UOM` records. Reason and method offer only the statutory values; neither list is configurable.
- **Submit to procurement** is visible to a Departmental Author but always disabled, with the reason shown. Only a Head of User Department may submit, per DSP-BR-006 and the certification in §4.5.
- Submission validates every item's Thirteenth Schedule content, locks an immutable snapshot and creates the consolidation task in one transaction.
- A returned submission reopens as a numbered correction Draft; the returned snapshot and its reason are preserved.
- Milestone dates never appear on this screen. They are set during consolidation.

### 12.3 DSP-UI-03 — Consolidation

- **Review** opens the submitted snapshot read-only with Accept and Return actions. Return requires a reason of 20–500 characters.
- Accept places the submission's items into the open Draft Version, creating Version 1 idempotently on first acceptance. Item numbers are generated in Schedule order and are not editable.
- **Edit dates** opens the dialog in DSP-DES-07. The server validates chronological order and containment within the Fiscal Year and returns every failing pair.
- Readiness is computed server-side and refreshed after every save. **Submit for approval** stays disabled with a visible reason until readiness passes.
- Submission revalidates contents, chronology and segregation under lock, then locks the snapshot and creates the Accounting Officer task.
- The Head of Procurement cannot accept a submission they themselves submitted as a Head of User Department; the server rejects it with `DSP_SEGREGATION_BLOCKED`.

### 12.4 DSP-UI-04 — Approval task

- Direct task routes require an Active Accounting Officer assignment. A read-only user is denied rather than shown disabled controls.
- All tabs read the exact submitted Version; no tab substitutes the current Active Version.
- Readiness and the method summary are server-computed at task read time.
- **Approve plan** reruns responsibility, contents, chronology and segregation checks under lock and activates in the same transaction, superseding the predecessor where one exists.
- A failed guard leaves the Version Submitted for approval and returns the exact failing rule. No item, status or date changes.
- **Return for correction** opens a dialog containing only **Reason**, **Cancel** and **Return**, validated server-side.
- The Head of Procurement who prepared the Version cannot approve it, enforced from the preparation audit event.
- The same screen serves an amendment; its Overview shows only the appended items and the amendment reason.

### 12.5 Amendments

- **Add assets to the approved plan** is available to a Head of Procurement on an Active Version when no amendment is open.
- The amendment Draft accepts new items only. The client offers no edit or remove control against existing Active items, and a direct API attempt returns `DSP_AMENDMENT_ALTERS_EXISTING`.
- Approval appends the items to the Active Version atomically, stamping each with the amendment ID. The Version number does not change and existing items and their recorded actuals are untouched.
- A second open amendment is rejected with `DSP_AMENDMENT_OPEN`, returning the existing amendment's route.

### 12.6 Actual dates

- **Record actual date** is available to a Head of Procurement on an Active Version only.
- An actual may be recorded only where the corresponding planned date exists. Variance is derived server-side; the client never computes it.
- Recording is append-only and audited. Correcting a mistaken actual is a new audited event, not an in-place edit.
- Empty actuals display as an em dash. A zero is never shown for an unrecorded actual.

---

## 13. Deterministic seed contract

Site configuration, Organisation Units, base actors and Fiscal Years come from KT-STD-001 §8. Execution rules come from KT-STD-001 §8.6.

### 13.1 Required additions to the shared fixture register

| Display name | Login identifier | Responsibility | Scope |
|---|---|---|---|
| Charles Mutiso | `charles.mutiso@moh.example.test` | Head of Procurement | Site-wide |

Amina Hassan (Accounting Officer) is added by PLN-CHG-001 v1.9. Grace Wanjiku, Dr Peter Kimani, Naomi Chebet and Samuel Otieno are existing register entries.

KT-STD-001 §8.5 shall gain: **Asset Disposal journeys — 4 May 2027 through 14 Jan 2028, EAT.**

### 13.2 Configuration prerequisites

The seed resolves these and fails with `DSP_CONTENTS_INCOMPLETE` if any is absent: ERPNext Fiscal Year `2027-2028`; currency KES; Organisation Units `OU-MOH-DHI` and `OU-MOH-HRMD`; ERPNext `UOM` **Each**, enabled; disposal-plan intake flag open for FY 2027/28.

The seed creates no Fiscal Year, Organisation Unit, unit of measure or configuration record.

### 13.3 Departmental submissions

| Submission | Department | Submitted by | Submitted | Status |
|---|---|---|---|---|
| `DSS-MOH-DHI-2027` | Digital Health | Dr Peter Kimani | 6 May 2027, 11:05 EAT | Accepted |
| `DSS-MOH-HRMD-2027` | HR Management and Development | Dr Peter Kimani | 11 May 2027, 09:20 EAT | Accepted |

### 13.4 Active plan and items

| Field | Value |
|---|---|
| Plan | `DSP-MOH-2027-001` · FY `2027-2028` |
| Version | `DSP-MOH-2027-001-V1` · Version 1 · Active |
| Prepared by | Charles Mutiso · 4 Jun 2027, 16:05 EAT |
| Approved by | Amina Hassan · 11 Jun 2027, 15:55 EAT |

**Item 1 — `DSI-MOH-2027-001`**

| Field | Value |
|---|---|
| Description | Desktop computers, assorted models |
| Department | `OU-MOH-DHI` |
| Quantity / unit | 45 · Each |
| Date of purchase | 12 Mar 2019 |
| Purchase price | KES 3,150,000 |
| Estimated current value | KES 180,000 |
| Life span | 5 years |
| Asset register reference | MOH/ICT/2019/0451 |
| Reason | Obsolete |
| Justification | Replaced under the 2026 end-user device refresh; units are beyond economic repair and unsupported by the manufacturer. |
| Method | Sale by public auction |
| Cost of managing disposal | KES 60,000 |
| Managed by | Procuring entity |
| Disposal to employee | No |

Planned dates: initiation 3 Aug 2027 · bid documents 17 Aug 2027 · invitation 31 Aug 2027 · bid opening 21 Sep 2027 · award 5 Oct 2027 · notification 12 Oct 2027 · contract signed 26 Oct 2027 · completed 30 Nov 2027 · PPRA notice not applicable.

**Item 2 — `DSI-MOH-2027-002`**

| Field | Value |
|---|---|
| Description | Toyota Land Cruiser, registration GKB 411X |
| Department | `OU-MOH-HRMD` |
| Quantity / unit | 1 · Each |
| Date of purchase | 8 Jun 2012 |
| Purchase price | KES 6,800,000 |
| Estimated current value | KES 950,000 |
| Life span | 8 years |
| Asset register reference | MOH/TRP/2012/0088 |
| Reason | Unserviceable |
| Justification | Engine and transmission failure assessed as beyond economic repair by the transport section in March 2027. |
| Method | Trade-in |
| Cost of managing disposal | KES 25,000 |
| Managed by | Procuring entity |
| Disposal to employee | No |

Planned dates: initiation 1 Nov 2027 · bid documents 15 Nov 2027 · invitation 29 Nov 2027 · bid opening 20 Dec 2027 · award 17 Jan 2028 · notification 24 Jan 2028 · contract signed 7 Feb 2028 · completed 28 Feb 2028 · PPRA notice not applicable.

### 13.5 Isolated profiles

These reset to the named precondition and do not coexist with the default plan.

| Profile | Precondition and expected result |
|---|---|
| `DSP-SC-EMPLOYEE` | An item with `is_disposal_to_employee` set. Submission fails until a planned PPRA notice date is supplied; the item then carries the section 166 restriction on its face. |
| `DSP-SC-WASTE` | An item with method `Waste disposal management` and estimated current value zero. The item carries the section 165(2) EMCA licensing requirement in the UI and in the published payload. |
| `DSP-SC-TRANSFER-NO-ADJUSTMENT` | A transfer item with `transfer_has_financial_adjustment` false. The item is retained and flagged as outside the Act's application under section 4(2)(b); no rule is relaxed. |
| `DSP-SC-AMENDMENT` | Active Version 1 plus one approved amendment appending a third item, `DSI-MOH-2027-003`, air-conditioning units condemned in December 2027. Items 1 and 2 and their recorded actuals are unchanged and the Version number remains 1. |
| `DSP-SC-SEGREGATION` | One user holding both Head of User Department for `OU-MOH-DHI` and Head of Procurement. Accepting their own submission is rejected with `DSP_SEGREGATION_BLOCKED`. |
| `DSP-SC-ACTUALS` | Item 1 with actuals recorded to bid opening, as shown in DSP-DES-09. Variance is −7 days on three activities and zero on the first. |

### 13.6 Execution rules

- Seeds call the same commands as the UI and never write DocTypes directly.
- Seed lifecycle decisions use the named responsibility holders, never Administrator.
- Seeds create no reserve price, valuation, committee record, proceeds entry or asset register record.
- Seeds are idempotent; a second run produces no duplicate plan, submission, item, amendment or audit entry.
- Isolated profiles are created and removed by their tests and never contaminate the default seed.

---

## 14. Audit and historical integrity

Append-only events: submission creation, save, submit, return, resubmit and accept; Version creation, save, submit, return, approve and supersede; amendment open, submit, return and approve; actual-date recording and correction; and responsibility or segregation denial.

Each records actor, business role, the exercised responsibility assignment ID, Fiscal Year, relevant IDs, action, timestamp, before and after status, required reason and correlation ID.

Submitted, Active and Superseded content is immutable. An approved amendment is a distinct auditable event, never an edit to an approved item. A recorded actual date is append-only; a correction is a new event that preserves the prior value. Records are never physically deleted after first submission.

---

## 15. Acceptance contract

| ID | Required result |
|---|---|
| DSP-AC-001 | One AssetDisposalPlan and one Active Version exist per Fiscal Year, and the guard holds when the command layer is bypassed. |
| DSP-AC-002 | Every item carries all Thirteenth Schedule columns and the regulation 176(3) contents, including the disposal manager, which has no Schedule column. |
| DSP-AC-003 | Only the four statutory reasons and the five statutory methods are accepted, and neither list is extensible by configuration. |
| DSP-AC-004 | The estimated current value is never labelled, exported, converted into or used to derive a reserve price, and no reserve price field exists. |
| DSP-AC-005 | The plan Version is approved by the Accounting Officer, and no configuration routes approval to the statutory authority as a substitute. |
| DSP-AC-006 | The Head of Procurement who prepared a Version or amendment cannot approve it, enforced from the preparation audit event. |
| DSP-AC-007 | An amendment appends items and rejects any attempt to alter, reprice, reschedule or remove an approved item. |
| DSP-AC-008 | Approving an amendment leaves the Version number, existing items and their recorded actuals unchanged. |
| DSP-AC-009 | A second open amendment is rejected and the existing amendment's route is returned. |
| DSP-AC-010 | A disposal to an employee requires a planned PPRA notice date and displays the section 166 restriction. |
| DSP-AC-011 | A waste disposal management item carries the section 165(2) EMCA licensing requirement in the UI and in the published payload. |
| DSP-AC-012 | A transfer item without financial adjustment is retained and flagged as outside the Act's application; no rule is relaxed and no inference is drawn. |
| DSP-AC-013 | Planned dates are validated for chronological order and containment within the Fiscal Year, and every failing pair is returned. |
| DSP-AC-014 | Actual dates may be recorded only against an existing planned date on an Active Version; variance is server-derived and empty actuals show an em dash. |
| DSP-AC-015 | A user holding both Head of User Department and Head of Procurement cannot accept their own submission. |
| DSP-AC-016 | A Departmental Author cannot submit a departmental submission; only a Head of User Department can. |
| DSP-AC-017 | The certification text in §4.5 is displayed before submission and retained with the submitted snapshot. |
| DSP-AC-018 | Milestone dates never appear on the departmental submission screen. |
| DSP-AC-019 | Returned submissions and Versions preserve the returned snapshot and its reason. |
| DSP-AC-020 | Approving a successor Version atomically activates it and supersedes the predecessor, preserving item identities and recorded actuals. |
| DSP-AC-021 | No reserve price, valuation, board of survey, committee, bidder, proceeds, write-off or asset register record exists in this module. |
| DSP-AC-022 | No disposal record appears in Procurement Planning and no procurement record appears here; the two plans are published as separate payloads. |
| DSP-AC-023 | The published payload carries every Thirteenth Schedule column in Schedule order, the header block and the signature block naming the preparer and approver. |
| DSP-AC-024 | The seed is deterministic and a second run produces no change. |
| DSP-AC-025 | A missing Fiscal Year, Organisation Unit or unit of measure fails seed execution without creating a fallback record. |
| DSP-AC-026 | The four routes render without console error and match their approved static designs. |
| DSP-AC-027 | Loading, no-plan, no-submissions, forbidden and server-error states are visibly distinct and disclose no false or unauthorised data. |
| DSP-AC-028 | A stale `expected_version` returns `DSP_STALE_WRITE` with no partial effect, and a retried command with the same idempotency key returns the original result. |

### 15.1 Minimum rule coverage

| Rule group | Required automated coverage |
|---|---|
| Responsibility and access | DSP-BR-001; DSP-AC-005–006, 015–016, 021 |
| Statutory content | DSP-BR-004–009; DSP-AC-002–004, 010–012 |
| Lifecycle and amendment | DSP-BR-002–003, 013–016; DSP-AC-001, 007–009, 019–020 |
| Dates and variance | DSP-BR-010–011; DSP-AC-013–014, 018 |
| Segregation | DSP-BR-012; DSP-AC-015 |
| Publication and separation | DSP-AC-022–023 |
| Seeds | DSP-AC-024–025 |
| UI | DSP-AC-026–027 |
| Concurrency | DSP-BR-017; DSP-AC-028 |

---

## 16. Implementation and test constraints

The implementation baseline is KT-STD-001 §4; the verification protocol is KT-STD-001 §5; release evidence is KT-STD-001 §6.

### 16.1 Additional implementation rules

- Register Head of Procurement in the AUTH-ADR-001 v1.6 registry with `scope_type = Site-wide`. Do not reuse Procurement Planner.
- Register the disposal DocTypes in `kentender_scope_map` through both permission hooks so direct-route access is covered.
- Enforce DSP-BR-002 and DSP-BR-003 with database-level partial unique indexes in addition to the command transaction.
- Model disposal reason and method as fixed server-side enumerations, not configuration records. They are statutory closed lists.
- Implement segregation from audit events, never by comparing role assignments.
- Implement the amendment as an append-only child of the Active Version. Do not implement it as a version bump or an in-place edit.
- Store all money in minor units. Estimated current value and cost of managing disposal use the site currency.
- Do not add a `reserve_price`, `valuation`, `condition`, `depreciation` or `proceeds` field under any name.

### 16.2 Minimum automated coverage

1. Write attempted with no assignment, with an expired assignment and with a Scheduled assignment.
2. Administrator and System Manager technical read succeeds; business mutation is denied.
3. Direct-route access to a plan, item, submission or task outside the actor's register.
4. One-plan-per-year and one-submission-per-unit-per-year guards under direct-SQL inserts bypassing the command layer.
5. Rejection of every non-statutory reason and method value, through UI and direct API.
6. Amendment append succeeds; alter, reprice, reschedule and remove each fail.
7. Concurrent amendment opening; second is rejected with the existing route.
8. Employee-disposal notice requirement and section 166 display.
9. Waste disposal management EMCA requirement in UI and payload.
10. Transfer without financial adjustment retained and flagged.
11. Date chronology and Fiscal Year containment at boundaries.
12. Actual date recorded without a planned date, rejected; variance derivation; correction as a new event.
13. Segregation: same user as Head of User Department and Head of Procurement; and as preparer and approver.
14. Departmental Author submission attempt rejected.
15. Successor approval atomicity with rollback on failure.
16. Repository scan proving `reserve_price`, `valuation`, `proceeds`, `write_off`, `Expired` and `Destruction` are absent.
17. Cross-module scan proving no disposal record exists in Procurement Planning and no procurement record here.
18. Component tests for each screen, each dialog and each state variant.
19. Route tests for direct load, tabs, refresh, back and forward.
20. Browser journeys: a Departmental Author drafts and a Head of User Department certifies and submits; the Head of Procurement reviews, accepts, sets dates and submits; the Accounting Officer returns once and approves on the corrected submission; the Head of Procurement records actuals; an actor with no assignment sees the Forbidden state with no disclosure.

### 16.3 Additional release evidence

- Schema scan proving every prohibited field and non-statutory enumeration value is absent.
- Deterministic seed succeeds twice with identical results.
- AUTH contract suite passes, proving no disposal path reintroduces a User Permission read.
- Visual comparison for all eleven artboards at 1440 × 1024.

---

## 17. Prohibited shortcuts

The universal list is KT-STD-001 §2.3 and §10. Additionally:

- Do not merge the disposal plan into the annual procurement plan; the format, contents, preparer, approver and mutability all differ.
- Do not route disposal plan approval to the Cabinet Secretary, CECM, Board or Council as a substitute for the Accounting Officer.
- Do not make the Active Version wholly immutable; regulation 176(4) requires flexibility for emerging issues.
- Do not implement the amendment as an in-place edit or a version bump.
- Do not implement or store a reserve price, valuation, board of survey, condition rating, depreciation schedule or proceeds figure.
- Do not build, replicate or browse an asset register.
- Do not make disposal reasons or methods configurable, and do not accept a value outside the statutory lists.
- Do not allow the same person to identify, consolidate and approve within one plan Version.
- Do not allow a Departmental Author to submit a departmental submission.
- Do not show milestone dates on the departmental submission screen.
- Do not compute variance, totals or readiness in the client.
- Do not publish the disposal plan and the procurement plan as one payload or one artefact.

---

## 18. Traceability and precedence

1. **KT-STD-001 v1.1** — document structure, design closed-input rules, artboard shell, shared fixture register, common page behaviour, verification protocol, release evidence, seed conventions, universal prohibitions and error conventions.
2. **AUTH-ADR-001 v1.6** — business authority, the role registry, responsibility assignment and the registered permission hooks.
3. **CFG-CHG-002 v0.8** — site entity, ERPNext Fiscal Year, Organisation Units, `UOM` and the disposal-plan intake flag.
4. **LAW-REG-001 v1.0** — the statutory mapping this document implements.
5. **This document** — the annual asset disposal plan, its versions, items, amendments and departmental submissions.
6. A later **Asset Disposal Proceedings** change unit — board of survey, valuation, reserve price, committee, sale, proceeds and write-off.

Primary authorities: Act sections 4(2)(b), 45(4), 53(4), 53(5), 163, 164, 165 and 166; Regulations 34(i), 176, 177, 178 and 179; and the Thirteenth Schedule.

Documents requiring a matching correction:

| Document | Required correction |
|---|---|
| KT-STD-001 | Add Charles Mutiso (Head of Procurement, site-wide) to §8.3 and the Asset Disposal fixture instant to §8.5. |
| CFG-CHG-002 | Already carries the disposal-plan intake flag at v0.8 §4.2. Add the optional additional statutory approval for the disposal plan described in §5.4 if the entity requires it. |
| PLN-CHG-001 | Already aligned at v1.9; disposal is a named non-goal and PLN-AC-095 asserts no disposal record exists there. |

---

## 19. Approval effect

Approved 3 September 2026. DSP-CHG-001 v0.2 supersedes v0.1 in full and establishes the Asset Disposal module.

This approval authorises: the annual asset disposal plan, its versions and departmental submissions; the Thirteenth Schedule field set and regulation 176(3) contents; the nine planned and actual milestone dates with derived variance; Accounting Officer approval; the append-only amendment mechanism required by regulation 176(4); registration of Head of Procurement as a site-wide business role; the four routes in §9; the artboards in §11; and the seed and acceptance contracts in §13 and §15.

It does not authorise any disposal proceeding, board of survey, valuation, reserve price, committee process, bidder handling, proceeds accounting, asset write-off or asset register.
