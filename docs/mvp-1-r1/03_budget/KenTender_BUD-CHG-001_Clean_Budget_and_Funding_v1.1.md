# BUD-CHG-001 — Clean Budget & Funding

| Control | Value |
|---|---|
| Document ID | BUD-CHG-001 |
| Version | 1.1 |
| Date | 23 August 2026 |
| Status | Approved |
| Approval | Product owner · 23 August 2026 |
| Module | Budget & Funding |
| Implementation posture | Correction in place; no compatibility layer |

**Controlling decision:** Retain Budget & Funding as a small procurement-funding control module. It registers an externally approved procurement budget, exposes eligible Budget Lines, and protects those amounts through reservations and commitments. It does not approve the public budget, keep accounts, process payments, duplicate Procurement Planning, or collect data without a current control purpose.

## 1. Governing decision

This document is the single implementation authority for the Budget & Funding cleanup. It replaces the earlier Budget MVP requirements and BUD-CHG-001 v1.0 wherever they conflict with this document.

The existing Budget application is corrected in place. Existing usable code and the proven Claude Design → Vue 3 → Frappe Desk page pattern are reused. Removed concepts are deleted rather than renamed, aliased, dual-read or retained behind feature flags.

Completion requires one coherent result across schema, services, permissions, screens, seed data and tests. A field, action, object, service or screen not defined here is outside the module.

### 1.1 Conflict and disposition register

| Earlier item | Disposition in v1.1 |
|---|---|
| Separate Allocation object | Remove. A Budget Line's approved amount is the allocation. |
| Budget Value Treatment, treatment questionnaire and Public Value Objective | Remove completely. No replacement object, field or screen. |
| Optional Budget-side Strategy references | Remove. Procurement Planning already stores the selected Strategic Objective and the Budget Line on the Plan Item lineage. Budget does not duplicate that relationship. |
| Reservation at Departmental Need acceptance | Remove. Acceptance creates no funding hold. |
| Budget-owned Finance confirmation screen | Remove. Procurement Planning owns the Finance task, decision UI and planner waiting state. Budget supplies the protected check-and-reserve service and read-only Budget Line detail. |
| One reservation per Plan Item | Correct. A Plan Item may contain more than one source allocation. Finance confirmation creates one reservation per Budget Line allocation, atomically across the complete source set. |
| Separate Budget Revision object and lifecycle | Replace with an immutable successor Budget Version. The successor uses the same review and activation path as the initial baseline. |
| Funding Exception object | Remove. A reservation that fails revalidation enters `Needs Attention`; the append-only ledger records the reason. |
| Expenditure Snapshot, actual expenditure and outstanding commitment | Defer completely. No field, service, seed, card or placeholder is included until an authoritative finance integration is approved. |
| Advanced Funding Performance dashboard | Remove. Retain only approved, reserved, committed and available positions. |
| Budget classification and separate purpose fields | Remove. The line title is the funded purpose. Procurement classification belongs to the Need and Plan Item. |
| Generic source, authority, notes and evidence fields | Remove. Retain only the external approval reference, approval date and one approval document because the reviewer uses them to verify the registered baseline. |
| Old KES 480m / 455m / 310m arithmetic fixture | Retire. Use the already-approved Planning fixtures: KES 100m and KES 60m Budget Lines, including the KES 80m reservation. |
| First-PE, first-FY or Administrator authority fallback | Remove. Every read and action uses an explicit configured scope and capability. |

## 2. Purpose and outcomes

Budget & Funding shall provide:

- one registered procurement budget for each authorised PE and Financial Year;
- immutable, reviewable Budget Versions;
- simple Budget Lines with a clear funded purpose, owning organisation scope, funding source and approved amount;
- exact approved, reserved, committed and available positions;
- atomic, idempotent Finance confirmation for one or more Plan Item allocations;
- preserved funding lineage from Plan Item allocation to reservation and contract commitment;
- controlled successor versions for approved budget changes; and
- neutral, permission-gated read access that does not grant financial authority.

### 2.1 Scope exclusions

The module shall not contain:

- appropriation, budget enactment, exchequer release, cash, ledger, invoice, payment or accounting workflows;
- Departmental Need approval or a reservation at Need acceptance;
- a separate Allocation record;
- Strategy Objective, Outcome, Indicator, Target or Value Commitment fields;
- procurement category, method, schedule, lot, tender or contract authoring fields;
- Budget Value Treatment, funding treatment, PVO or corrective-action data;
- actual expenditure, outstanding commitment, expenditure freshness or an `Unavailable` placeholder;
- forecasts, utilisation percentages, performance scores, trends or charts;
- manual reservation or commitment entry;
- a duplicate Finance task, Finance decision or planner waiting screen;
- generic notes, descriptions, justification, contacts or miscellaneous attachments;
- editable technical identifiers;
- a new Frappe shell, header, breadcrumb, global selector or navigation system; or
- compatibility fields, legacy aliases or fallback records.

### 2.2 Data-purpose gate

No stored field is permitted unless all three conditions are documented before implementation:

1. a current operational decision or output uses the field;
2. the screen, rule or service consuming it is named; and
3. its validation and system effect are defined.

“Useful later”, “normally captured”, “helpful context” and “the design showed it” are not sufficient reasons. Undocumented fields shall be omitted, not added as optional fields.

The external approval reference, approval date and approval document pass this gate because the Budget Reviewer and Activation Authority use them to verify that the line set faithfully represents an externally approved procurement budget. They are not generic source-reference fields.

## 3. Fixed external constraints and ownership

- Procuring Entity, organisation-unit, Financial Year, currency, funding-source catalogue and capability assignments come from Configuration & Governance. Budget shall not create or infer them.
- Strategy Alignment owns Strategic Objectives and downstream Strategy snapshots. Budget stores no Strategy link.
- Departmental Needs owns the Need and its selected Budget Line reference. Need acceptance creates no reservation.
- Procurement Planning owns Plan Items, source allocations, Finance tasks, Finance decisions and their UI. Budget owns the authoritative reservation and position calculation.
- Contract Management owns contracts and variations. It uses Budget services to convert or adjust the same funding lineage.
- A later authoritative finance integration may introduce expenditure data only through a separately approved change unit.

| Information or decision | Owner | Budget relationship |
|---|---|---|
| PE, OU, FY, currency, funding-source value and capability assignment | Configuration & Governance | Read configured identifiers and fail closed when absent. |
| Strategic Objective and snapshot | Strategy Alignment / Procurement Planning | No Budget field or write. |
| Accepted Need and selected Budget Line | Departmental Needs | Validate the line through Budget contracts; create no hold. |
| Plan Item, source allocation, Finance task and Finance decision | Procurement Planning | Call Budget check-and-reserve; store returned reservation references. |
| Budget, versions, lines, reservations, commitments and funding ledger | Budget & Funding | Create, govern and expose read-only. |
| Contract and variation | Contract Management | Call Budget conversion and adjustment services. |
| Payment and expenditure | Authoritative financial system | No MVP-1 data or UI. |

The dependency direction is:

**Configuration & Governance → Budget & Funding → Departmental Needs / Procurement Planning → Contract Management**

Budget shall not import a downstream DocType controller or query a downstream table directly.

## 4. Canonical domain model

All identifiers are generated by the server. Framework audit fields remain framework-managed and are not repeated below.

### 4.1 Budget

The stable identity of one PE/FY procurement budget.

| Field | Operational purpose and system effect |
|---|---|
| `budget_id` | Immutable generated reference used by routes, services, audit and downstream lineage. Not editable. |
| `procuring_entity_id` | Defines the owning PE and permission boundary. Required. |
| `financial_year_id` | Defines the governed funding period. Required. |
| `currency` | Fixes one currency for every line and calculation in the Budget. Copied from the configured context and immutable after creation. |

There shall be at most one Budget for a PE/FY pair. Its display title is derived as `{PE name} procurement budget {FY label}` and is not stored as another editable field.

### 4.2 BudgetVersion

The immutable approval boundary for one registered baseline or successor revision.

| Field | Operational purpose and system effect |
|---|---|
| `budget_version_id` | Immutable generated reference used by Budget Line versions, review tasks and audit. |
| `budget_id` | Links the version to its stable Budget. |
| `version_number` | Establishes ordered version history and is generated per Budget. |
| `based_on_budget_version_id` | Identifies the Active version copied to create a successor. Empty only for Version 1. |
| `revision_type` | Classifies an externally approved successor as `Supplementary allocation`, `Reduction`, `Transfer` or `Correction`. Required only when `based_on_budget_version_id` is present. |
| `status` | Controls editability, review actions and eligibility: `Draft`, `In Review`, `Awaiting Activation`, `Active`, `Superseded` or `Closed`. |
| `approval_reference` | Identifies the external approval instrument reviewed before activation. Required. |
| `approval_date` | Confirms that external approval preceded KenTender activation. Required. |
| `approval_document_file_id` | Links exactly one uploaded approval document used by the reviewer and Activation Authority. Required. |
| `authorised_total` | Records the total approved by the external instrument. The sum of Version lines must equal it before submission or activation. Required and positive. |

Submitted, reviewed, activated, superseded and closed actors and timestamps are audit events, not editable fields. A Return reason is stored on the decision event, not as a generic version field.

### 4.3 BudgetLine

The stable identity of one funded purpose across Budget Versions.

| Field | Operational purpose and system effect |
|---|---|
| `budget_line_id` | Immutable generated reference used by Needs, Plan allocations, reservations, commitments and routes. |
| `budget_id` | Prevents the line identity from moving to another PE/FY Budget. |

### 4.4 BudgetLineVersion

The line values included in one Budget Version.

| Field | Operational purpose and system effect |
|---|---|
| `budget_line_version_id` | Immutable generated reference for review comparison and audit. |
| `budget_version_id` | Binds the values to one immutable Budget Version. |
| `budget_line_id` | Preserves downstream funding lineage across approved amount changes. |
| `title` | States the funded purpose displayed in selectors, tables and snapshots. Required. No separate purpose or description field is stored. |
| `owner_org_unit_id` | Limits line eligibility to one configured organisation unit. Empty means PE-wide. |
| `funding_source` | Uses the configured funding-source catalogue and is copied into downstream funding snapshots. Required. |
| `approved_amount` | Supplies the allocation ceiling for the line in this version. Required and positive. |

After first activation, `title`, `owner_org_unit_id` and `funding_source` define the stable line identity and cannot change in a successor. A genuinely different purpose, owner scope or funding source requires a new Budget Line. A successor may change only the approved amount of an existing line.

### 4.5 FundingReservation

The authoritative hold created by one successful Finance confirmation for one Plan Item source allocation.

| Field | Operational purpose and system effect |
|---|---|
| `reservation_id` | Immutable generated reference returned to Procurement Planning and used by downstream lineage. |
| `budget_id` | Fixes the PE/FY funding root. |
| `budget_version_id_at_creation` | Preserves the version under which the reservation was confirmed. |
| `budget_line_id` | Identifies the funded purpose and balance affected. |
| `plan_item_id` | Links the reservation to the governed Plan Item. |
| `plan_source_allocation_id` | Distinguishes multiple source allocations and prevents duplicate or partial confirmation. |
| `original_amount` | Records the full amount confirmed for that allocation. Required and positive. |
| `remaining_amount` | Stores the unconverted and unreleased hold. Changed only by Budget services. |
| `status` | `Active`, `Partially Converted`, `Converted`, `Released` or `Needs Attention`. |
| `correlation_id` | Makes Finance retries idempotent and binds every reservation in one all-source confirmation transaction. |

There is no `Requested` reservation. A failed check creates no reservation. There is no expiry date, manual authority field, note or attachment.

### 4.6 ProcurementCommitment

The current contract obligation converted from a reservation.

| Field | Operational purpose and system effect |
|---|---|
| `commitment_id` | Immutable generated reference used by Contract Management and funding lineage. |
| `reservation_id` | Prevents a commitment from bypassing the confirmed funding lineage. |
| `contract_id` | Identifies the owning downstream contract. Required and unique within the reservation lineage. |
| `current_amount` | Stores the current contractual obligation and affects the committed and available positions. Changed only through the adjustment service. |
| `status` | `Active`, `Cancelled` or `Closed`. |

One reservation may convert into more than one contract commitment, but the sum converted shall never exceed its remaining amount plus its existing commitments. Contract details, supplier, dates, variations and payments remain in Contract Management.

### 4.7 FundingLedgerEvent

An append-only system event containing:

- event ID and event type;
- Budget, Budget Line, reservation and commitment IDs as applicable;
- Plan allocation, contract or variation reference as applicable;
- amount;
- before and after approved, reserved, committed and available line positions;
- actor or calling service, timestamp and correlation ID; and
- a typed revalidation failure code where applicable.

Users do not create or edit ledger events. There is no separate Funding Exception, expenditure or free-text note object.

## 5. Canonical calculations and invariants

For one Budget Line at an `as_at` point:

**Reserved** = sum of `remaining_amount` for reservations in `Active`, `Partially Converted` or `Needs Attention`.

**Committed** = sum of `current_amount` for commitments in `Active`.

**Available** = `approved_amount − Reserved − Committed`.

Budget totals are the sums of the active Version's line positions. Users never enter calculated totals.

| ID | Rule and enforcement |
|---|---|
| BUD-BR-001 | Every record resolves to one explicit authorised PE and FY. Missing or unauthorised context fails closed. |
| BUD-BR-002 | One PE/FY has at most one Budget and one Active Budget Version. Activation is serialized. |
| BUD-BR-003 | Every line amount and funding event uses the Budget currency. Cross-currency funding is outside MVP-1. |
| BUD-BR-004 | Approval reference, approval date, one approval document and positive authorised total are required before submission. Approval date cannot be in the future or after activation, and the Version line sum shall equal `authorised_total`. |
| BUD-BR-005 | Only Draft and Returned-through-decision versions are editable; In Review, Awaiting Activation, Active, Superseded and Closed versions are read-only. |
| BUD-BR-006 | Only an Active Budget Version may support a new reservation. |
| BUD-BR-007 | A line is eligible for an allocation only when it is in the resolved Active Version and its owner scope is PE-wide or matches the source Need's organisation unit. |
| BUD-BR-008 | The allocation's funding source shall equal the Budget Line funding source. Procurement type does not restrict line eligibility. |
| BUD-BR-009 | Need acceptance, DPP submission and Plan Item draft save create no reservation. |
| BUD-BR-010 | Finance confirmation covers the complete current Plan Item source-allocation set. All required reservations succeed in one transaction or none is created. |
| BUD-BR-011 | Each Plan source allocation receives exactly one effective reservation. Repeating the same correlation returns the same result. |
| BUD-BR-012 | Check Funding is non-mutating. A check token is short-lived and cannot bypass locked revalidation during reservation. |
| BUD-BR-013 | Reserved, committed and available positions shall never be negative. Concurrent commands cannot oversubscribe a line. |
| BUD-BR-014 | A reservation may be partially converted into one or more commitments; only the unconverted remainder stays reserved. |
| BUD-BR-015 | Release, conversion and commitment adjustment require an authenticated downstream event and are idempotent by correlation ID. No user keys amounts directly in Budget UI. |
| BUD-BR-016 | `Needs Attention` keeps the remaining amount reserved while downstream progression is blocked. It does not silently release funds. |
| BUD-BR-017 | A successor cannot reduce a line below its current Reserved plus Committed position. |
| BUD-BR-018 | A Transfer successor shall have equal total increases and decreases and shall preserve `authorised_total`. |
| BUD-BR-019 | An existing line identity may change approved amount only. A new purpose, owner scope or funding source requires a new line ID. |
| BUD-BR-020 | A line may be omitted from a successor only when it has no remaining reservation or active commitment. |
| BUD-BR-021 | Activation rechecks approval evidence, line total, floors, transfer balance, scope and concurrency under one transaction lock. |
| BUD-BR-022 | Activating a successor atomically makes it Active and the previous Active Version Superseded while preserving all line, reservation and commitment identities. |
| BUD-BR-023 | A Closed Budget admits no new reservations but retains all read, audit and downstream lineage. |
| BUD-BR-024 | Downstream modules use Budget service contracts and cannot query or mutate Budget tables directly. |
| BUD-BR-025 | Generated identifiers, calculated positions, statuses and audit authority are never client-editable. |

## 6. Lifecycle and governance

### 6.1 Budget Version lifecycle

| Current status | Command | Next status | Authorised actor |
|---|---|---|---|
| Draft | Submit for review | In Review | Budget Officer |
| In Review | Return | Draft | Budget Reviewer; reason required |
| In Review | Recommend for activation | Awaiting Activation | Budget Reviewer |
| Awaiting Activation | Return | Draft | Budget Activation Authority; reason required |
| Awaiting Activation | Activate | Active | Budget Activation Authority |
| Active | Activate successor | Superseded | System, inside successor activation transaction |
| Active | Close after FY | Closed | Budget Activation Authority |

Version 1 is the initial baseline. Version 2 and later are successor revisions. There is no separate Budget Revision workflow.

### 6.2 Governance rules

- A Budget Officer may create and edit only Draft versions in an assigned PE/FY scope.
- The submitting Budget Officer cannot review or activate the same version.
- The Budget Reviewer cannot activate the same version.
- Return requires 10–500 characters and preserves the submitted snapshot and decision event.
- Recommendation and activation are distinct decisions.
- Activation means “available for KenTender procurement control”; it does not approve the public budget.
- At most one open Draft, In Review or Awaiting Activation successor may exist for a Budget.
- A successor is always copied server-side from the current Active Version.
- Closing requires the FY to have ended and no reservation with a remaining amount. Active commitments may remain visible for lineage.
- Records and ledger events are never deleted after submission.

## 7. Roles and permissions

| Role or capability | Permitted capability |
|---|---|
| Budget Viewer | View Active, Superseded and Closed Budgets and line positions within assigned scope. |
| Budget Officer | Register the initial Draft, create a successor, edit Draft approval details and lines, and submit within assigned scope. |
| Budget Reviewer | Inspect live submitted versions; return or recommend within assigned scope. |
| Budget Activation Authority | Inspect a recommended version; return, activate or close within assigned scope. |
| Finance Confirmation Officer | Open a specifically assigned Procurement Planning Finance task and confirm or return it. The capability grants no Budget authoring or activation authority. |
| Procurement Planner | Read eligible Budget Lines and the neutral Finance result through contracts; no Budget mutation. |
| Contract service principal | Revalidate, convert, release or adjust exact funding lineage through authenticated service calls. |
| Auditor | Read scoped versions, positions, lineage and audit events; no business mutation. |
| System Administrator | Inspect technical metadata and neutral records read-only unless separately assigned a business capability. |

Assignments are scoped by PE, FY, optional organisation unit, capability and effective dates. The same server-side predicate applies to counts, rows, direct URLs, exports, services and task queues. A selected PE/FY changes context only; it grants no authority.

## 8. Procurement Planning and downstream integration

### 8.1 Finance confirmation ownership

Procurement Planning remains the sole owner of:

- the Finance task and its assignment;
- the Finance sufficient, insufficient, return and planner-waiting UI states;
- the immutable Finance decision; and
- the Plan Item's reservation references.

Budget & Funding remains the sole owner of:

- live line eligibility and positions;
- the locked availability check;
- creation of all reservations as one atomic operation;
- later reservation revalidation, release and conversion; and
- the funding ledger.

The existing Planning surfaces `PLN-UI-07`, `PLN-UI-07A-1`, `PLN-UI-07A-2` and `PLN-UI-07B` remain valid and shall be reused. This change unit creates no second Finance drawer, form, decision page or waiting page.

**Open Budget & Funding** from a Planning Finance surface opens BUD-UI-05 Budget Line detail for the exact line selected in the Finance allocation. Navigation creates no decision, reservation or Budget mutation. For a combined Plan Item, each allocation opens its own Budget Line detail.

### 8.2 All-source confirmation

1. Procurement Planning supplies the exact current Plan Item version, Finance task, source-set hash and every source allocation.
2. Budget authorises the Finance capability and validates every Budget Line, amount, owner scope, funding source and current position.
3. `check_funding` returns one short-lived token and a position for every allocation; it writes nothing.
4. Confirm Funding calls `reserve_funding` with the token, expected task/version locks and one idempotency key.
5. Budget locks all affected lines in stable ID order, reloads every position and creates one reservation per source allocation.
6. If any allocation fails, the entire command rolls back and returns the exact failing allocation and shortfall.
7. Procurement Planning stores the returned reservation references and its immutable Finance decision in the same orchestration boundary.

Partial source confirmation, line substitution and silent amount reduction are prohibited.

### 8.3 Later funding events

| Downstream event | Budget effect |
|---|---|
| Formal Requisition or material procurement change | Revalidate the same reservation set; create no second reservation. |
| Contract creation | Convert the required amount from the reservation to one or more commitments. |
| Contract value increase | Revalidate line availability, then increase the commitment through an adjustment event. |
| Contract value decrease or cancellation | Reduce or cancel the commitment and release the applicable remainder through one idempotent event. |
| Budget successor activation | Preserve valid lineage; mark an affected reservation `Needs Attention` only when a current invariant fails. |

No downstream event may directly update `remaining_amount`, `current_amount`, status or a line position.

## 9. Service and command contracts

All contracts are typed, versioned, server-authorised and idempotent where they mutate state.

### 9.1 Read and funding contracts

| Contract | Required input | Output and effect |
|---|---|---|
| `resolve_budget_context` | PE and FY | One Active Budget/version summary or typed not-found/ambiguous/ineligible error. |
| `list_eligible_budget_lines` | PE, FY, source organisation unit, optional funding source, search and paging | Active eligible lines with ID, title, owner scope, funding source, approved, reserved, committed and available positions. No Draft lines. |
| `get_budget_line_position` | Budget Line ID and `as_at` | Authorised line identity, active-version amount, current positions and version token. No mutation. |
| `check_funding` | Plan Item/version, Finance task, source-set hash, complete allocation array and correlation ID | Non-mutating per-allocation eligibility, positions, required amounts, after-confirmation balances and short-lived check token. |
| `reserve_funding` | Check token, expected task/source/version locks and idempotency key | All reservations and new positions, or one typed all-or-none failure. |
| `revalidate_reservations` | Exact reservation set, downstream event ID/type and idempotency key | Current or Needs Attention results and ledger events; no new reservation. |
| `release_reservation` | Reservation ID, amount, downstream cancellation/change event and idempotency key | Reduced remaining amount or Released status and new line position. |
| `convert_reservation` | Reservation ID, contract ID, amount and idempotency key | One commitment, updated reservation remainder and new line position. |
| `adjust_commitment` | Commitment ID, new total, contract variation/cancellation event and idempotency key | Updated current commitment after locked revalidation and a ledger event. |
| `get_funding_lineage` | Plan Item, source allocation, reservation, contract or commitment reference | Ordered Budget, version-at-confirmation, line, reservation, commitment and ledger identities within scope. |

There is no expenditure-ingest contract in MVP-1.

### 9.2 Budget governance commands

| Command | Purpose |
|---|---|
| `save_budget_version_draft` | Create or update Draft approval details with optimistic concurrency. |
| `save_budget_lines_draft` | Create, update or remove Draft lines as one validated change set. |
| `submit_budget_version` | Validate approval details, line total and version rules; move Draft to In Review. |
| `review_budget_version` | Return or recommend an In Review version. |
| `activate_budget_version` | Return or atomically activate an Awaiting Activation version after all live checks. |
| `create_budget_successor_version` | Copy the current Active Version and line identities into one Draft successor. |
| `close_budget` | Close an Active Budget after the FY and remaining-reservation guards pass. |

Every write requires the expected record version. A stale command returns `BUDGET_STALE_WRITE` and overwrites nothing.

## 10. UI architecture and routes

Budget & Funding remains a top-level KenTender module named **Budget & Funding**. Its module menu contains only:

- **Budget & Funding**; and
- **Review tasks**, visible only to a scoped Budget Reviewer or Budget Activation Authority.

Finance tasks remain in Procurement Planning. Do not add a Budget-side Finance queue or Finance screen.

| Screen | Canonical route | Purpose |
|---|---|---|
| BUD-UI-01 Budget & Funding workspace | `/app/budget` | Current scoped Budget and operational position. |
| BUD-UI-02 Budget Version editor | `/app/budget/{budget_id}/version/{version_number}/edit` | Initial baseline or successor Draft approval details and lines. |
| BUD-UI-03 Budget workspace | `/app/budget/{budget_id}` | Active/read-only Overview, Budget Lines, Funding Activity and History. |
| BUD-UI-04 Review task | `/app/budget/review/{budget_version_id}` | Reviewer or Activation Authority inspection and decision. |
| BUD-UI-05 Budget Line detail | `/app/budget/line/{budget_line_id}` | Read-only active line position and funding lineage; target of Planning's **Open Budget & Funding**. |

The Budget workspace uses persistent URL-backed tabs:

- **Overview**
- **Budget Lines**
- **Funding Activity**
- **History**

The review task uses **Overview**, **Budget Lines**, **Changes** and **History**. The proven Vue-in-Frappe page pattern and approved KenTender design system shall be reused. This document does not authorise a second dashboard, application shell or Frappe header.

## 11. Static Claude Design contract

This section is the complete input to Claude Design. It defines static visual compositions only. Runtime behaviour belongs to section 12 and shall not be pasted into a design prompt.

### 11.1 Closed-input rules

- Produce desktop artboards at **1440 × 1024 px**.
- Reuse the approved KenTender Strategy Portfolio visual system, spacing, type scale, tokens, cards, tags, tables, fields, buttons, tabs, empty states and dialogs.
- The artboard starts below the Frappe Desk header. Do not draw Frappe navigation, the Desk header, breadcrumb, user menu, notifications, Help, global search or the PE/FY workspace selector.
- Breadcrumb text is fixture data outside the artboard. It is supplied to confirm location only.
- Use only the visible labels, values, badges, controls, sections and states stated for that artboard.
- Do not add summary cards, charts, utilisation percentages, trend arrows, illustrations, side panels, steppers, tooltips, helper text, metadata, action menus or table columns unless explicitly stated.
- Do not invent data. If a value or state is not stated, omit it.
- Do not encode behaviour, validation, permissions, APIs, routing, transitions, concurrency or implementation instructions in the visual output.
- Do not show Strategy data, procurement classification, a separate purpose field, Value Commitment, treatment, actual expenditure, outstanding commitment, forecast, contact, note, justification or generic attachment.
- Show the one named **Approval document** only on artboards that explicitly include it.
- Generated identifiers may be shown on saved records but never as editable fields.

The approved desktop shell inside every artboard is:

- full-width warm-white page background;
- a 1200 px maximum-width content column centred in the available page area;
- 32 px top and bottom page padding;
- page header followed by 24 px vertical spacing;
- 16 px gaps between cards or table sections; and
- no custom sidebar.

### 11.2 BUD-DES-01 — Budget & Funding workspace

**Fixture context — outside the artboard:** MOH Budget Viewer · `bud.viewer.moh@example.test` · Ministry of Health · FY 2027/28 · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding**

**Page content header**

- Eyebrow: **BUDGET & FUNDING**
- Title: **Budget & Funding**
- Description: **View the approved procurement budget and the funding position used by Procurement Planning.**
- No header action button

**Context strip**

| Label | Value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Financial Year | FY 2027/28 |
| Currency | KES |

**Current budget card**

- Heading: **Ministry of Health procurement budget 2027/28**
- Status: **Active**

| Label | Value |
|---|---|
| Budget reference | MOH-BUD-2027-001 |
| Active version | Version 1 |
| Approval reference | MOH-FIN-BUD-2027-01 (Demo) |
| Approval date | 30 Sep 2026 |

Right-aligned secondary button: **View budget**

**Funding position row — four equal cards**

| Card label | Value |
|---|---:|
| Approved | KES 160,000,000 |
| Reserved | KES 80,000,000 |
| Committed | KES 0 |
| Available | KES 80,000,000 |

**Budget Lines preview**

| Budget Line | Owner scope | Approved | Reserved | Committed | Available | Action |
|---|---|---:|---:|---:|---:|---|
| MOH-BL-DHI-2027 · Digital health infrastructure programme | Digital Health | KES 100,000,000 | KES 80,000,000 | KES 0 | KES 20,000,000 | View |
| MOH-BL-HWD-2027 · Digital health workforce development | HR Management and Development | KES 60,000,000 | KES 0 | KES 0 | KES 60,000,000 | View |

Do not show Finance tasks, Strategy alignment, actual expenditure, percentages, charts or a register button on this Active-state artboard.

### 11.3 BUD-DES-02 — Register approved budget draft

**Fixture context — outside the artboard:** MOH Budget Officer · `moh.budget.officer@example.test` · Ministry of Health · FY 2027/28 · 1 Oct 2026, 09:20 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Register approved budget**

**Page content header**

- Title: **Register approved budget**
- Status: **Draft**
- No header action button

**Budget context card**

| Field label | Displayed value |
|---|---|
| Budget reference | Not assigned |
| Procuring Entity | PE-MOH — Ministry of Health |
| Financial Year | FY 2027/28 |
| Currency | KES |

All four rows use the approved read-only field component.

**External approval card**

| Field label | Displayed value |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-01 (Demo) |
| Approval date | 30 Sep 2026 |
| Authorised total | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget 2027-28 (Demo).pdf |

Approval reference uses the approved input component; Approval date uses the approved date component; Authorised total uses the approved currency input with fixed KES prefix; Approval document uses one file component showing the exact uploaded filename.

**Fixed footer, left to right:** **Cancel**, **Save draft**. **Save draft** is the primary button.

Do not show a Budget title, authority name, source type, source date, effective date, description, notes, Strategy field, line editor, readiness card or submit action.

### 11.4 BUD-DES-03 — Draft Budget Lines editor

**Fixture context — outside the artboard:** MOH Budget Officer · `moh.budget.officer@example.test` · Ministry of Health · FY 2027/28 · 1 Oct 2026, 10:10 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Version 1 > Budget Lines**

**Page content header**

- Eyebrow: **MOH-BUD-2027-001 · VERSION 1**
- Title: **Register approved budget**
- Status: **Draft**
- Right-aligned secondary button: **Save draft**
- Right-aligned primary button: **Submit for review**

**Tabs:** **Overview**, **Budget Lines** selected

**Line total strip**

| Label | Value |
|---|---:|
| Authorised total | KES 160,000,000 |
| Budget Line total | KES 160,000,000 |
| Difference | KES 0 |

**Editable Budget Lines table**

| Budget Line | Line title | Owner scope | Funding source | Approved amount | Action |
|---|---|---|---|---:|---|
| MOH-BL-DHI-2027 | Digital health infrastructure programme | Digital Health | Government of Kenya | KES 100,000,000 | Remove |
| MOH-BL-HWD-2027 | Digital health workforce development | HR Management and Development | Government of Kenya | KES 60,000,000 | Remove |

Budget Line uses the approved read-only text component. Line title uses an input. Owner scope and Funding source use selects. Approved amount uses a KES currency input. Action uses a compact danger-outline text button.

Below the table, left-aligned secondary button: **Add Budget Line**.

Do not show classification, purpose, cost centre, Strategy, Value Commitment, allocation, notes or calculated fields inside a row.

### 11.5 BUD-DES-04 — Active Budget overview

**Fixture context — outside the artboard:** MOH Budget Viewer · `bud.viewer.moh@example.test` · Ministry of Health · FY 2027/28 · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001**

**Page content header**

- Eyebrow: **MOH-BUD-2027-001 · VERSION 1**
- Title: **Ministry of Health procurement budget 2027/28**
- Status: **Active**
- No header action button

**Tabs:** **Overview** selected, **Budget Lines**, **Funding Activity**, **History**

**Funding position row — four equal cards**

| Card label | Value |
|---|---:|
| Approved | KES 160,000,000 |
| Reserved | KES 80,000,000 |
| Committed | KES 0 |
| Available | KES 80,000,000 |

**Budget context card**

| Label | Value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Financial Year | FY 2027/28 |
| Currency | KES |
| Active version | Version 1 |

**External approval card**

| Label | Value |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-01 (Demo) |
| Approval date | 30 Sep 2026 |
| Authorised total | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget 2027-28 (Demo).pdf |

The Approval document value uses the approved quiet file-link style.

**Activation card**

| Label | Value |
|---|---|
| Submitted by | MOH Budget Officer |
| Reviewed by | MOH Budget Reviewer |
| Activated by | MOH Budget Activation Authority |
| Activated | 3 Oct 2026, 11:15 EAT |

Do not show edit controls, Create revision, Strategy data, approval stepper, actual expenditure or charts on this Viewer artboard.

### 11.5A BUD-DES-04A — Active Budget overview for Budget Officer

Duplicate BUD-DES-04.

**Fixture context — outside the artboard:** MOH Budget Officer · `moh.budget.officer@example.test` · Ministry of Health · FY 2027/28 · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001**

Keep all BUD-DES-04 content unchanged and add one right-aligned primary page-header button: **Create revision**.

Do not add Edit budget, Add line, Close budget, Finance task or overflow-menu controls.

### 11.6 BUD-DES-05 — Active Budget Lines

**Fixture context — outside the artboard:** MOH Budget Viewer · `bud.viewer.moh@example.test` · Ministry of Health · FY 2027/28 · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Budget Lines**

Reuse the BUD-DES-04 page content header without changing its content or placement.

**Tabs:** **Overview**, **Budget Lines** selected, **Funding Activity**, **History**

**Budget Lines table**

| Budget Line | Owner scope | Funding source | Approved | Reserved | Committed | Available | Action |
|---|---|---|---:|---:|---:|---:|---|
| MOH-BL-DHI-2027 · Digital health infrastructure programme | Digital Health | Government of Kenya | KES 100,000,000 | KES 80,000,000 | KES 0 | KES 20,000,000 | View |
| MOH-BL-HWD-2027 · Digital health workforce development | HR Management and Development | Government of Kenya | KES 60,000,000 | KES 0 | KES 0 | KES 60,000,000 | View |
| Total | — | — | KES 160,000,000 | KES 80,000,000 | KES 0 | KES 80,000,000 | — |

Do not show an Allocation column, utilisation, Strategy, procurement classification, purpose, actual expenditure, row menu or edit action.

### 11.7 BUD-DES-06 — Budget Line detail

**Fixture context — outside the artboard:** MOH Budget Officer · `moh.budget.officer@example.test` · Ministry of Health · FY 2027/28 · 4 Dec 2026, 09:58 EAT · opened from Procurement Planning Finance task `FNT-MOH-2027-021-001` · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BL-DHI-2027**

**Page content header**

- Eyebrow: **MOH-BL-DHI-2027**
- Title: **Digital health infrastructure programme**
- Status: **Active**
- No header action button

**Context strip**

| Label | Value |
|---|---|
| Budget | MOH-BUD-2027-001 · Version 1 |
| Procuring Entity | PE-MOH — Ministry of Health |
| Financial Year | FY 2027/28 |

**Funding position row — four equal cards**

| Card label | Value |
|---|---:|
| Approved | KES 100,000,000 |
| Reserved | KES 0 |
| Committed | KES 0 |
| Available | KES 100,000,000 |

**Line identity card**

| Label | Value |
|---|---|
| Owner scope | Digital Health |
| Funding source | Government of Kenya |
| Active version | Version 1 |

**Active reservations section**

- Heading: **Active reservations**
- Empty-state title: **No active reservations**
- Empty-state body: **This Budget Line has no confirmed funding reservations.**
- No empty-state button

Do not show Confirm funding, Return, Release, Convert, Adjust, Edit, Strategy, approval evidence, actual expenditure or contract fields.

### 11.7A BUD-DES-06A — Budget Line detail with an active reservation

Duplicate BUD-DES-06.

**Fixture context — outside the artboard:** MOH Budget Viewer · `bud.viewer.moh@example.test` · Ministry of Health · FY 2027/28 · 10 Dec 2026, 15:05 EAT · opened from the Active Budget Lines table · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BL-DHI-2027**

Keep the page content header, context strip and Line identity card unchanged. Replace the Funding position row and Active reservations section with the exact content below.

**Funding position row — four equal cards**

| Card label | Value |
|---|---:|
| Approved | KES 100,000,000 |
| Reserved | KES 80,000,000 |
| Committed | KES 0 |
| Available | KES 20,000,000 |

**Active reservations table**

| Reservation | Plan Item | Original amount | Remaining amount | Status | Action |
|---|---|---:|---:|---|---|
| RSV-MOH-2027-021-001 | PPI-MOH-2027-021 · National digital health infrastructure upgrade | KES 80,000,000 | KES 80,000,000 | Active | View Plan Item |

Do not add Finance actions, release controls, conversion controls, contract data or another reservation row.

### 11.8 BUD-DES-07 — Funding Activity

**Fixture context — outside the artboard:** MOH Budget Viewer · `bud.viewer.moh@example.test` · Ministry of Health · FY 2027/28 · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Funding Activity**

Reuse the BUD-DES-04 page content header without changing its content or placement.

**Tabs:** **Overview**, **Budget Lines**, **Funding Activity** selected, **History**

**Filter row, left to right**

- select showing **All Budget Lines**
- select showing **All funding events**

**Funding Activity table**

| Date and time | Event | Budget Line | Downstream reference | Amount | Actor |
|---|---|---|---|---:|---|
| 4 Dec 2026, 10:00 EAT | Reservation confirmed | MOH-BL-DHI-2027 | PPI-MOH-2027-021 · RSV-MOH-2027-021-001 | KES 80,000,000 | MOH Budget Officer |

Footer text: **Showing 1 funding event**

Do not show a chart, utilisation, expenditure, technical correlation ID, before/after JSON, manual Add event control or row action.

### 11.8A BUD-DES-07A — Active Budget History

**Fixture context — outside the artboard:** MOH Budget Viewer · `bud.viewer.moh@example.test` · Ministry of Health · FY 2027/28 · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > History**

Reuse the BUD-DES-04 page content header without changing its content or placement.

**Tabs:** **Overview**, **Budget Lines**, **Funding Activity**, **History** selected

**Version history card**

| Date and time | Event | Actor |
|---|---|---|
| 3 Oct 2026, 11:15 EAT | Version 1 activated | MOH Budget Activation Authority |
| 2 Oct 2026, 10:22 EAT | Recommended for activation | MOH Budget Reviewer |
| 1 Oct 2026, 16:20 EAT | Submitted for review | MOH Budget Officer |
| 1 Oct 2026, 15:55 EAT | Draft saved | MOH Budget Officer |
| 1 Oct 2026, 09:20 EAT | Budget Version 1 created | MOH Budget Officer |

Do not show funding ledger events, technical logs, comments, attachments or history from another Budget.

### 11.9 BUD-DES-08 — Reviewer task · Overview

**Fixture context — outside the artboard:** MOH Budget Reviewer · `moh.budget.reviewer@example.test` · Ministry of Health · FY 2027/28 · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Review tasks > MOH-BUD-2027-001-V2**

**Page content header**

- Eyebrow: **MOH-BUD-2027-001 · VERSION 2**
- Title: **Review budget version**
- Status: **In Review**
- No header action button

**Tabs:** **Overview** selected, **Budget Lines**, **Changes**, **History**

**Version identity card**

| Label | Value |
|---|---|
| Procurement budget | Ministry of Health procurement budget 2027/28 |
| Procuring Entity | PE-MOH — Ministry of Health |
| Financial Year | FY 2027/28 |
| Currency | KES |
| Submitted version | Version 2 |
| Based on | Active Version 1 |
| Revision type | Transfer |

**External approval card**

| Label | Value |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-02 (Demo) |
| Approval date | 14 Mar 2027 |
| Authorised total | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget Transfer 2027-28 (Demo).pdf |

The Approval document uses the approved quiet file-link style.

**Submission authority card**

| Label | Value |
|---|---|
| Submitted by | MOH Budget Officer |
| Submitted | 15 Mar 2027, 16:20 EAT |

**Readiness card**

| Check | Result |
|---|---|
| Approval details complete | Ready |
| Budget Line total matches authorised total | Ready |
| Reservation and commitment floors | Ready |
| Transfer balance | Ready |

**Fixed footer, left to right:** **Return**, **Recommend for activation**. **Return** uses the danger-outline style; **Recommend for activation** is primary.

Do not show editable fields, comments, notes, Strategy data, actual expenditure or a second approval document.

### 11.10 BUD-DES-09 — Reviewer task · Budget Lines

**Fixture context — outside the artboard:** MOH Budget Reviewer · `moh.budget.reviewer@example.test` · Ministry of Health · FY 2027/28 · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Review tasks > MOH-BUD-2027-001-V2**

Reuse the BUD-DES-08 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Budget Lines** selected, **Changes**, **History**

**Submitted Budget Lines table**

| Budget Line | Owner scope | Funding source | Proposed amount | Current floor | Headroom |
|---|---|---|---:|---:|---:|
| MOH-BL-DHI-2027 · Digital health infrastructure programme | Digital Health | Government of Kenya | KES 90,000,000 | KES 80,000,000 | KES 10,000,000 |
| MOH-BL-HWD-2027 · Digital health workforce development | HR Management and Development | Government of Kenya | KES 70,000,000 | KES 0 | KES 70,000,000 |
| Total | — | — | KES 160,000,000 | KES 80,000,000 | KES 80,000,000 |

Do not show inputs, Remove, Add Budget Line, classification, purpose, Strategy, actual expenditure or row actions.

### 11.11 BUD-DES-10 — Reviewer task · Changes

**Fixture context — outside the artboard:** MOH Budget Reviewer · `moh.budget.reviewer@example.test` · Ministry of Health · FY 2027/28 · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Review tasks > MOH-BUD-2027-001-V2**

Reuse the BUD-DES-08 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Budget Lines**, **Changes** selected, **History**

**Budget Line comparison card**

- Heading: **Changes from Active Version 1**

| Budget Line | Active Version 1 | Submitted Version 2 | Change |
|---|---:|---:|---:|
| MOH-BL-DHI-2027 · Digital health infrastructure programme | KES 100,000,000 | KES 90,000,000 | − KES 10,000,000 |
| MOH-BL-HWD-2027 · Digital health workforce development | KES 60,000,000 | KES 70,000,000 | + KES 10,000,000 |
| Total | KES 160,000,000 | KES 160,000,000 | KES 0 |

**Funding impact card**

| Label | Value |
|---|---|
| Active reservations affected | 1 |
| Active commitments affected | 0 |
| Floor breaches | 0 |
| Transfer difference | KES 0 |

Do not show unchanged identity fields, inline editing, per-row accept/reject controls, comments or a side-by-side document viewer.

### 11.12 BUD-DES-11 — Reviewer task · History

**Fixture context — outside the artboard:** MOH Budget Reviewer · `moh.budget.reviewer@example.test` · Ministry of Health · FY 2027/28 · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Review tasks > MOH-BUD-2027-001-V2**

Reuse the BUD-DES-08 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Budget Lines**, **Changes**, **History** selected

**Version history card**

| Date and time | Event | Actor |
|---|---|---|
| 15 Mar 2027, 16:20 EAT | Submitted for review | MOH Budget Officer |
| 15 Mar 2027, 15:55 EAT | Draft saved | MOH Budget Officer |
| 15 Mar 2027, 13:10 EAT | Successor Version 2 created | MOH Budget Officer |

Do not show comments, attachments, technical request logs, funding ledger events or history from another version.

### 11.13 BUD-DES-12 — Activation task · four tab variants

Create four Activation Authority artboards by duplicating BUD-DES-08, BUD-DES-09, BUD-DES-10 and BUD-DES-11 respectively.

**Fixture context for all four activation artboards — outside the artboard:** MOH Budget Activation Authority · `moh.budget.activation@example.test` · Ministry of Health · FY 2027/28 · 17 Mar 2027, 09:40 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Review tasks > MOH-BUD-2027-001-V2**

Make exactly these changes on all four duplicates:

- title: **Activate budget version**;
- status: **Awaiting Activation**;
- fixed-footer buttons: **Return**, **Activate**; **Return** uses the danger-outline style and **Activate** is primary; and
- retain the selected tab and all submitted Version 2 content from the corresponding Reviewer artboard.

On the **Overview** duplicate, replace the Submission authority card with this exact card:

| Label | Value |
|---|---|
| Submitted by | MOH Budget Officer |
| Submitted | 15 Mar 2027, 16:20 EAT |
| Reviewed by | MOH Budget Reviewer |
| Recommended | 16 Mar 2027, 10:22 EAT |

On the **History** duplicate, replace the Version history table with this exact table:

| Date and time | Event | Actor |
|---|---|---|
| 16 Mar 2027, 10:22 EAT | Recommended for activation | MOH Budget Reviewer |
| 15 Mar 2027, 16:20 EAT | Submitted for review | MOH Budget Officer |
| 15 Mar 2027, 15:55 EAT | Draft saved | MOH Budget Officer |
| 15 Mar 2027, 13:10 EAT | Successor Version 2 created | MOH Budget Officer |

Do not change the Budget Lines or Changes content. Do not add Approve, edit, comment, note, upload or Finance controls.

### 11.14 BUD-DES-13 — Initial baseline review · four tab variants

Create four initial-baseline Reviewer artboards by duplicating BUD-DES-08, BUD-DES-09, BUD-DES-10 and BUD-DES-11 respectively.

**Fixture context for all four artboards — outside the artboard:** MOH Budget Reviewer · `moh.budget.reviewer@example.test` · Ministry of Health · FY 2027/28 · 2 Oct 2026, 10:00 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Review tasks > MOH-BUD-2027-001-V1**

On all four duplicates:

- eyebrow: **MOH-BUD-2027-001 · VERSION 1**;
- title: **Review budget version**;
- status: **In Review**;
- preserve the corresponding selected tab;
- fixed-footer buttons: **Return**, **Recommend for activation**; and
- use only the replacement content below for the selected tab.

**Overview duplicate**

Version identity card:

| Label | Value |
|---|---|
| Procurement budget | Ministry of Health procurement budget 2027/28 |
| Procuring Entity | PE-MOH — Ministry of Health |
| Financial Year | FY 2027/28 |
| Currency | KES |
| Submitted version | Version 1 |

External approval card:

| Label | Value |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-01 (Demo) |
| Approval date | 30 Sep 2026 |
| Authorised total | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget 2027-28 (Demo).pdf |

Submission authority card:

| Label | Value |
|---|---|
| Submitted by | MOH Budget Officer |
| Submitted | 1 Oct 2026, 16:20 EAT |

Readiness card:

| Check | Result |
|---|---|
| Approval details complete | Ready |
| Budget Line total matches authorised total | Ready |
| Budget Lines complete | Ready |

Do not show Based on, Revision type, transfer balance or an invented predecessor.

**Budget Lines duplicate**

| Budget Line | Owner scope | Funding source | Submitted amount |
|---|---|---|---:|
| MOH-BL-DHI-2027 · Digital health infrastructure programme | Digital Health | Government of Kenya | KES 100,000,000 |
| MOH-BL-HWD-2027 · Digital health workforce development | HR Management and Development | Government of Kenya | KES 60,000,000 |
| Total | — | — | KES 160,000,000 |

Do not show Current floor, Headroom or Active amounts.

**Changes duplicate**

- Heading: **Initial baseline**
- Body: **Version 1 has no predecessor. Review the complete submitted Budget Lines.**

| Budget Line | Submitted Version 1 |
|---|---:|
| MOH-BL-DHI-2027 · Digital health infrastructure programme | KES 100,000,000 |
| MOH-BL-HWD-2027 · Digital health workforce development | KES 60,000,000 |
| Total | KES 160,000,000 |

Do not show an empty Active-version column, calculated change, Funding impact card or invented predecessor.

**History duplicate**

| Date and time | Event | Actor |
|---|---|---|
| 1 Oct 2026, 16:20 EAT | Submitted for review | MOH Budget Officer |
| 1 Oct 2026, 15:55 EAT | Draft saved | MOH Budget Officer |
| 1 Oct 2026, 09:20 EAT | Budget Version 1 created | MOH Budget Officer |

Do not show revision events, funding ledger events or history from another version.

### 11.14A BUD-DES-13A — Initial baseline activation · four tab variants

Create four initial-baseline Activation Authority artboards by duplicating the four BUD-DES-13 artboards.

**Fixture context for all four artboards — outside the artboard:** MOH Budget Activation Authority · `moh.budget.activation@example.test` · Ministry of Health · FY 2027/28 · 3 Oct 2026, 11:00 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Review tasks > MOH-BUD-2027-001-V1**

Make exactly these changes on all four duplicates:

- title: **Activate budget version**;
- status: **Awaiting Activation**;
- fixed-footer buttons: **Return**, **Activate**; **Return** uses the danger-outline style and **Activate** is primary; and
- retain the selected tab and all submitted Version 1 content from the corresponding BUD-DES-13 artboard.

On the **Overview** duplicate, replace the Submission authority card with:

| Label | Value |
|---|---|
| Submitted by | MOH Budget Officer |
| Submitted | 1 Oct 2026, 16:20 EAT |
| Reviewed by | MOH Budget Reviewer |
| Recommended | 2 Oct 2026, 10:22 EAT |

On the **History** duplicate, replace the Version history table with:

| Date and time | Event | Actor |
|---|---|---|
| 2 Oct 2026, 10:22 EAT | Recommended for activation | MOH Budget Reviewer |
| 1 Oct 2026, 16:20 EAT | Submitted for review | MOH Budget Officer |
| 1 Oct 2026, 15:55 EAT | Draft saved | MOH Budget Officer |
| 1 Oct 2026, 09:20 EAT | Budget Version 1 created | MOH Budget Officer |

Do not add a predecessor, revision type, change amount, approval stepper or edit control.

### 11.15 BUD-DES-14 — Successor revision draft · Overview

**Fixture context — outside the artboard:** MOH Budget Officer · `moh.budget.officer@example.test` · Ministry of Health · FY 2027/28 · 15 Mar 2027, 15:55 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Version 2 > Overview**

**Page content header**

- Eyebrow: **MOH-BUD-2027-001 · VERSION 2**
- Title: **Budget revision**
- Status: **Draft**
- Right-aligned secondary button: **Save draft**
- Right-aligned primary button: **Submit for review**

**Tabs:** **Overview** selected, **Budget Lines**

**Version context card**

| Field label | Displayed value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Financial Year | FY 2027/28 |
| Currency | KES |
| Based on | Active Version 1 |
| Revision type | Transfer |

The first four rows use approved read-only components. Revision type uses the approved select component.

**External approval card**

| Field label | Displayed value |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-02 (Demo) |
| Approval date | 14 Mar 2027 |
| Authorised total | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget Transfer 2027-28 (Demo).pdf |

Approval reference uses an input; Approval date uses a date component; Authorised total uses a KES currency input; Approval document uses one file component showing the exact filename.

Do not show a change reason, justification, source type, effective date, notes, Strategy or approval fields.

### 11.16 BUD-DES-15 — Successor revision draft · Budget Lines

**Fixture context — outside the artboard:** MOH Budget Officer · `moh.budget.officer@example.test` · Ministry of Health · FY 2027/28 · 15 Mar 2027, 15:55 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Version 2 > Budget Lines**

Reuse the BUD-DES-14 page content header without changing its content or placement.

**Tabs:** **Overview**, **Budget Lines** selected

**Line total strip**

| Label | Value |
|---|---:|
| Authorised total | KES 160,000,000 |
| Budget Line total | KES 160,000,000 |
| Difference | KES 0 |

**Editable successor lines table**

| Budget Line | Line title | Owner scope | Funding source | Active amount | Proposed amount | Change |
|---|---|---|---|---:|---:|---:|
| MOH-BL-DHI-2027 | Digital health infrastructure programme | Digital Health | Government of Kenya | KES 100,000,000 | KES 90,000,000 | − KES 10,000,000 |
| MOH-BL-HWD-2027 | Digital health workforce development | HR Management and Development | Government of Kenya | KES 60,000,000 | KES 70,000,000 | + KES 10,000,000 |

Budget Line, Line title, Owner scope, Funding source, Active amount and Change use approved read-only components. Proposed amount uses a KES currency input.

Below the table, left-aligned secondary button: **Add Budget Line**.

Do not show Remove on these existing referenced lines, classification, purpose, Strategy, reservation controls, notes or actual expenditure.

### 11.17 BUD-DES-16 — Workspace state variants

Create four static variants. Every variant contains the BUD-DES-01 page content header and context strip. Do not show position cards or Budget Line rows unless stated.

Fixture context for Loading, No baseline and Server error — outside the artboard: **MOH Budget Officer · `moh.budget.officer@example.test` · Ministry of Health · FY 2027/28 · 1 Oct 2026, 09:00 EAT**. Fixture context for Forbidden — outside the artboard: **Kisumu Budget Viewer · `bud.viewer.kisumu@example.test` · Ministry of Health · FY 2027/28 · 1 Oct 2026, 09:00 EAT**. Frappe header breadcrumb for all variants: **Home > Budget & Funding**.

| Variant | Main content | Buttons |
|---|---|---|
| Loading | One full-width skeleton Current budget card followed by four skeleton position cards and two skeleton table rows | None |
| No baseline | Heading **No approved procurement budget is registered for FY 2027/28.** Body **Register the externally approved budget before Procurement Planning requests funding confirmation.** | **Register approved budget** |
| Forbidden | Heading **You do not have access to this Budget & Funding context.** Body **Ask your KenTender administrator to review your Budget assignment.** | None |
| Server error | Heading **Budget & Funding could not be loaded.** Body **Try again. If the problem continues, contact KenTender support.** | **Try again** |

### 11.18 Existing Frappe, KenTender and Planning controls

No design artboard is authorised for the Frappe header, breadcrumb, module menu, global page chrome, notifications, user menu or existing KenTender PE/FY selector. Reuse those components without visual modification.

The Finance task, sufficient/insufficient states, return dialog and planner-waiting state are already defined by Procurement Planning. Do not reproduce or redesign them in Claude Design for Budget & Funding.

## 12. Functional interaction requirements — excluded from design prompts

This section defines behaviour for requirements, implementation and testing. It shall not be copied into Claude Design.

### 12.1 BUD-UI-01 — Budget & Funding workspace

- The server resolves the selected PE/FY through the existing KenTender context control. It never chooses the first Budget, PE or FY.
- One Active Budget returns its exact version and derived line positions. A Draft successor does not replace or alter the Active projection.
- The workspace counts and line rows use the same server-side scope predicate as direct routes and services.
- **Register approved budget** appears only when the selected PE/FY has no Budget and the actor has Budget Officer capability.
- **View budget** opens the exact server-returned `budget_id`.
- A Budget Officer viewing an Active Budget may receive **Create revision** only from the server's `available_actions`; a neutral viewer does not see it.
- Loading never shows zero balances. Forbidden and failure states disclose no out-of-scope Budget IDs, titles, lines or amounts.
- Browser back/forward restores the selected PE/FY and prior Budget route without mounting a second page application.

### 12.2 BUD-UI-02 — Budget Version editor

- Saving the initial Draft creates the Budget and Version and returns generated references. The PE, FY and currency become immutable.
- The editor accepts only `approval_reference`, `approval_date`, `authorised_total` and one `approval_document_file_id` on Overview.
- The document component permits one current file. Replacing it in Draft removes the old Draft link; submitted evidence is retained in the version snapshot.
- Budget Line create/update accepts only title, owner scope, funding source and approved amount. Existing generated line IDs are not editable.
- Owner-scope choices come from Configuration & Governance for the exact PE. Funding-source choices come from the configured catalogue.
- Draft line total and difference are server-calculated after every save response. The client may preview them but cannot submit calculated totals.
- Removing a new unreferenced Draft line is permitted. Removing or changing identity fields on a previously Active line is rejected.
- **Submit for review** reloads the Draft under a version lock, applies all readiness rules and changes status only if the complete transaction passes.
- Failed readiness returns structured failing rules, keeps the Draft editable and focuses the first failing field or line.
- A stale save returns `BUDGET_STALE_WRITE` and preserves unsaved user values for deliberate reload or reconciliation.

### 12.3 BUD-UI-03 — Budget workspace

- Overview and Budget Lines use positions calculated from the Active Version and funding ledger at the response `as_at` time.
- The selected tab is represented by the URL. Back/forward changes the tab without changing the Budget or mounting another page application.
- Active, Superseded and Closed versions are read-only.
- Budget Lines returns only exact stored identity values and derived positions. It does not infer classification, Strategy or expenditure data.
- Funding Activity is reverse chronological and server-filtered by Budget Line and event type. Filtering grants no additional access.
- Funding Activity shows business event summaries only. Technical correlation and before/after details remain available through authorised audit evidence, not the default table.
- History contains Budget Version lifecycle events only; it does not duplicate the funding ledger.
- **Create revision** creates one server-side copy of the Active Version, preserving existing line IDs and values, and opens its Draft Overview.
- A second open successor is rejected and the existing Draft route is returned to an authorised Budget Officer.

### 12.4 BUD-UI-05 — Budget Line detail

- The route authorises the exact line and active PE/FY before returning its title, owner, funding source, positions or reservations.
- A Planning Finance task passes a line ID only. Budget independently authorises the actor and never trusts Planning route visibility as Budget authority.
- The page uses the current live position; it does not freeze to the Finance task snapshot.
- Before Finance confirmation, the page may show no active reservations even though the Planning task displays a proposed amount.
- After confirmation, active reservations show reservation ID, Plan Item reference, original amount, remaining amount and status read-only.
- **View Plan Item** uses a server-returned authorised Planning URL. The Budget client does not build a route from a guessed naming rule.
- Opening or closing the page creates no check, reservation, decision or ledger event.

### 12.5 BUD-UI-04 — Review task

- Direct task routes require the exact current Budget Reviewer or Activation Authority capability. A neutral viewer is denied rather than shown disabled workflow controls.
- Overview, Budget Lines, Changes and History always read the submitted `budget_version_id`; no tab substitutes the current Active Version.
- Overview returns submitted version identity, approval evidence, submitter/reviewer authority and readiness results.
- Budget Lines returns the complete submitted line set and current floors calculated at task-read time.
- Changes is calculated server-side against `based_on_budget_version_id`. Version 1 returns the explicit initial-baseline state and never invents a predecessor.
- History returns only events for the submitted Budget Version in reverse chronological order.
- The role-appropriate decision footer remains available on every tab. Every command carries Budget Version ID, expected status and expected record version.
- A Reviewer may Return or Recommend only while status is In Review.
- An Activation Authority may Return or Activate only while status is Awaiting Activation.
- Return opens a dialog containing only **Return reason**, **Cancel** and **Return**. The reason is validated server-side.
- Activate reruns evidence, totals, line identity, floor, transfer, scope and concurrency checks under transaction locks.
- Successful successor activation changes the new version to Active and the prior Active Version to Superseded atomically.
- A failed live guard leaves the version Awaiting Activation and returns the exact failed rule. No line, status, reservation or ledger position changes.

### 12.6 Procurement Planning Finance boundary

- Finance task discovery, task routing, sufficient and insufficient compositions, return dialog and planner waiting remain exactly as defined by Procurement Planning.
- Budget services authorise the assigned Finance Confirmation capability, task, PE/FY, source-set and amount scope before returning protected line positions.
- A Planner receives only the neutral Finance result already permitted by Planning; the Planner cannot call `reserve_funding` directly.
- **Check funding** changes no Budget or Planning state.
- **Confirm funding** locks and reloads the complete allocation set. It creates every reservation or none.
- If any line is short, Confirm remains unavailable in the Planning UI and a direct command returns `BUDGET_INSUFFICIENT_FUNDS` with the failing allocation and exact shortfall.
- Finance return records its reason in Procurement Planning and creates no Budget reservation or ledger event.
- A repeated successful confirmation returns the same reservation IDs and does not duplicate a ledger event.
- A combined Plan Item may use more than one Budget Line. Each source allocation keeps its own line and reservation identity; the item is confirmed only as one all-source decision.

### 12.7 Common page states and accessibility

- A PE/FY with no Budget shows the no-baseline state and no zero-value funding position.
- An Active Budget with no funding events shows **No funding activity has been recorded for this budget.** and no Add action.
- A search or server filter with no matching events provides **Clear filters**.
- Forbidden responses disclose no record names, counts, amounts or task details.
- A server failure retains already displayed stable read-only data where safe and offers **Try again**.
- Focus order, keyboard operation, labels, contrast, table headers, dialog focus and live status messages shall meet the established KenTender accessibility standard.

## 13. Error contract

Errors return a stable code, plain-language message, correlation ID and exact field, line or allocation reference when applicable. Messages do not disclose records outside the actor's scope.

| Code | Message intent and effect |
|---|---|
| `BUDGET_SCOPE_REQUIRED` | A valid PE/FY scope was not supplied. No data or record is returned. |
| `BUDGET_PERMISSION_DENIED` | The actor lacks the required scoped capability. No protected data is returned. |
| `BUDGET_CONFIG_MISSING` | A referenced PE, OU, FY, currency, funding source or assignment is unavailable. The operation fails closed. |
| `BUDGET_ALREADY_EXISTS` | The PE/FY already has a Budget. Return its authorised route; create nothing. |
| `BUDGET_INVALID_STATE` | The command is not valid for the current server status. Current status is returned. |
| `BUDGET_NOT_READY` | Submission, recommendation or activation readiness failed. Structured failing rule IDs are returned. |
| `BUDGET_APPROVAL_EVIDENCE_REQUIRED` | Approval reference, date, document or authorised total is absent or invalid. |
| `BUDGET_TOTAL_MISMATCH` | Budget Line total does not equal authorised total. No status changes. |
| `BUDGET_LINE_NOT_ELIGIBLE` | The line is missing, inactive, outside scope or incompatible with the allocation's owner/funding source. |
| `BUDGET_LINE_IDENTITY_IMMUTABLE` | A successor attempted to change title, owner scope or funding source on an existing Active line. |
| `BUDGET_CONTEXT_NOT_FOUND` | No applicable Active Budget exists for the PE/FY. No line is selected. |
| `BUDGET_CONTEXT_AMBIGUOUS` | More than one Active Budget/version matches. No record is selected. |
| `BUDGET_FINANCE_TASK_DENIED` | The caller lacks the exact live Finance task capability. No protected position is returned. |
| `BUDGET_CHECK_STALE` | The line, allocation set or task changed after Check Funding. No reservation is created. |
| `BUDGET_INSUFFICIENT_FUNDS` | One or more allocations lack full availability. Return per-line shortfalls; create no reservation. |
| `BUDGET_RESERVATION_CONFLICT` | The allocation already has a different effective reservation or correlation. No duplicate is created. |
| `BUDGET_REVISION_FLOOR_BREACH` | A proposed line amount is below current Reserved plus Committed. Activation is blocked. |
| `BUDGET_TRANSFER_UNBALANCED` | Transfer increases and decreases do not balance. Submission or activation is blocked. |
| `BUDGET_CONVERSION_EXCEEDS_REMAINDER` | Contract conversion exceeds the reservation remainder. No commitment changes. |
| `BUDGET_COMMITMENT_INCREASE_UNFUNDED` | A proposed commitment increase lacks available funds. No adjustment occurs. |
| `BUDGET_CLOSED` | The Budget is Closed and cannot accept a new reservation. |
| `BUDGET_STALE_WRITE` | The expected record version is stale. No newer data is overwritten. |
| `BUDGET_DOWNSTREAM_FORBIDDEN` | A downstream caller attempted an unsupported Draft read or direct mutation. |

Unexpected failures are logged server-side and return the standard KenTender support message plus correlation ID. Internal tracebacks, raw SQL and out-of-scope identifiers are never returned to the browser.

## 14. Audit and historical integrity

The following events are append-only:

- Budget and successor-version creation;
- Draft approval-detail and line change sets;
- submit, return, recommend, activate, supersede and close;
- Check Funding outcome without balance mutation;
- reservation creation or idempotent reuse;
- revalidation, release, conversion and commitment adjustment;
- permission, segregation, floor and concurrency denial; and
- downstream lineage reads.

Each event records actor or calling service, scoped capability, PE/FY, relevant IDs, action, timestamp, before/after status or line position, required decision reason, correlation ID and calling module where applicable.

Active, Superseded and Closed Budget Versions are immutable. Funding Ledger events cannot be edited or deleted. Downstream reservation and commitment identities remain resolvable after a Budget successor activates or the FY closes.

## 15. Deterministic seed contract

Seed data is synthetic and required for integration, permission, arithmetic and cross-PE isolation tests. It is not an official appropriation or production budget.

### 15.1 Configuration prerequisites

Budget seed shall resolve these existing records and fail with `BUDGET_CONFIG_MISSING` if any is absent:

| Record | Required identifier or value |
|---|---|
| Ministry of Health | `PE-MOH` |
| County Government of Kisumu | `PE-CGK` |
| Financial Year 2027/28 | `FY-2027-2028` |
| Currency | `KES` |
| MOH organisation units | `Digital Health`; `HR Management and Development` |
| Funding source | `Government of Kenya` |

The Budget seed shall not create or choose a PE, OU, FY, currency or funding-source value.

### 15.2 Test actors and assignments

| User ID | Display name | Assignment and test purpose |
|---|---|---|
| `moh.budget.officer@example.test` | MOH Budget Officer | Budget Officer and separately assigned MOH Finance Confirmation capability for FY 2027/28. No review or activation. |
| `moh.budget.reviewer@example.test` | MOH Budget Reviewer | Budget Reviewer for PE-MOH and FY 2027/28. No authoring or activation. |
| `moh.budget.activation@example.test` | MOH Budget Activation Authority | Activation and closure for PE-MOH and FY 2027/28. No authoring or review. |
| `bud.viewer.moh@example.test` | MOH Budget Viewer | Neutral Budget read for PE-MOH. |
| `bud.auditor@example.test` | Budget Auditor | Audit read for PE-MOH and PE-CGK. No business mutation. |
| `cgk.budget.officer@example.test` | Kisumu Budget Officer | Budget Officer for PE-CGK only. |
| `cgk.budget.reviewer@example.test` | Kisumu Budget Reviewer | Budget Reviewer for PE-CGK only. |
| `cgk.budget.activation@example.test` | Kisumu Budget Activation Authority | Activation for PE-CGK only. |
| `bud.viewer.kisumu@example.test` | Kisumu Budget Viewer | Neutral Budget read for PE-CGK only. |

System Administrator and Administrator roles grant no Budget or Finance action by themselves.

### 15.3 Ministry of Health Active baseline

| Field | Exact seed value |
|---|---|
| Budget ID | `MOH-BUD-2027-001` |
| Procuring Entity | `PE-MOH` |
| Financial Year | `FY-2027-2028` |
| Currency | `KES` |
| Version ID | `MOH-BUD-2027-001-V1` |
| Version | 1 |
| Status | Active |
| Approval reference | `MOH-FIN-BUD-2027-01 (Demo)` |
| Approval date | 30 Sep 2026 |
| Approval document | `MOH Approved Procurement Budget 2027-28 (Demo).pdf` |
| Authorised total | KES 160,000,000 |

Exact Budget Lines:

| Budget Line | Title | Owner scope | Funding source | Approved amount |
|---|---|---|---|---:|
| `MOH-BL-DHI-2027` | Digital health infrastructure programme | Digital Health | Government of Kenya | KES 100,000,000 |
| `MOH-BL-HWD-2027` | Digital health workforce development | HR Management and Development | Government of Kenya | KES 60,000,000 |

Exact lifecycle authority:

| Event | Actor | Date and time |
|---|---|---|
| Submitted for review | MOH Budget Officer | 1 Oct 2026, 16:20 EAT |
| Recommended for activation | MOH Budget Reviewer | 2 Oct 2026, 10:22 EAT |
| Activated | MOH Budget Activation Authority | 3 Oct 2026, 11:15 EAT |

### 15.4 Integrated Planning reservation

The default integrated seed contains the already-approved Planning Finance evidence:

| Record | Exact value |
|---|---|
| Finance task | `FNT-MOH-2027-021-001` |
| Finance decision | `FND-MOH-2027-021-001` |
| Plan Item | `PPI-MOH-2027-021` — National digital health infrastructure upgrade |
| Plan source allocation | `PSA-MOH-2027-021-001` |
| Budget Line | `MOH-BL-DHI-2027` |
| Reservation | `RSV-MOH-2027-021-001` |
| Reservation amount | KES 80,000,000 |
| Confirmed by | MOH Budget Officer |
| Confirmed | 4 Dec 2026, 10:00 EAT |
| Reservation status | Active |

The resulting default position is exact:

| Budget Line | Approved | Reserved | Committed | Available |
|---|---:|---:|---:|---:|
| MOH-BL-DHI-2027 | KES 100,000,000 | KES 80,000,000 | KES 0 | KES 20,000,000 |
| MOH-BL-HWD-2027 | KES 60,000,000 | KES 0 | KES 0 | KES 60,000,000 |
| Total | KES 160,000,000 | KES 80,000,000 | KES 0 | KES 80,000,000 |

### 15.5 Isolated Finance and commitment profiles

These profiles reset to the named precondition and do not coexist with the default integrated reservation.

| Profile | Exact precondition and expected result |
|---|---|
| `BUD-SC-FIN-SINGLE` | DHI approved/available KES 100m; allocation KES 80m; confirmation creates one KES 80m reservation and leaves KES 20m available. |
| `BUD-SC-FIN-COMBINED` | DHI available KES 100m and HWD available KES 60m; allocations KES 72m and KES 48m; one command creates both full reservations and leaves KES 28m and KES 12m available. |
| `BUD-SC-FIN-SHORT` | DHI approved KES 100m, existing reserved KES 30m, available KES 70m; required KES 80m; result is KES 10m short and no new reservation. |
| `BUD-SC-CONVERT-PARTIAL` | DHI reservation KES 80m; convert KES 60m to one commitment; result KES 20m remaining reservation, KES 60m committed and KES 20m available. |
| `BUD-SC-DUPLICATE-CORRELATION` | Repeat the successful single-source command with the same correlation; return the same reservation and one effective ledger event. |

### 15.6 Isolated successor Version 2

The revision shown in BUD-DES-08 through BUD-DES-15 is an isolated test fixture, not part of the default Active baseline.

| Field | Exact value |
|---|---|
| Budget Version ID | `MOH-BUD-2027-001-V2` |
| Based on | `MOH-BUD-2027-001-V1` |
| Revision type | Transfer |
| Approval reference | `MOH-FIN-BUD-2027-02 (Demo)` |
| Approval date | 14 Mar 2027 |
| Approval document | `MOH Approved Procurement Budget Transfer 2027-28 (Demo).pdf` |
| Authorised total | KES 160,000,000 |
| DHI proposed amount | KES 90,000,000 |
| HWD proposed amount | KES 70,000,000 |
| Transfer difference | KES 0 |
| Successor created | 15 Mar 2027, 13:10 EAT · MOH Budget Officer |
| Draft saved | 15 Mar 2027, 15:55 EAT · MOH Budget Officer |
| Submitted for review | 15 Mar 2027, 16:20 EAT · MOH Budget Officer |
| Recommended for activation | 16 Mar 2027, 10:22 EAT · MOH Budget Reviewer |

The DHI floor is KES 80,000,000 from the default reservation. The proposed KES 90,000,000 amount therefore remains valid with KES 10,000,000 headroom.

### 15.7 County Government of Kisumu isolation baseline

| Field | Exact seed value |
|---|---|
| Budget ID | `CGK-BUD-2027-001` |
| Procuring Entity | `PE-CGK` |
| Financial Year | `FY-2027-2028` |
| Currency | `KES` |
| Version ID | `CGK-BUD-2027-001-V1` |
| Status | Active |
| Approval reference | `CGK-FIN-BUD-2027-01 (Demo)` |
| Approval date | 30 Sep 2026 |
| Approval document | `Kisumu Approved Procurement Budget 2027-28 (Demo).pdf` |
| Authorised total | KES 20,000,000 |
| Budget Line | `CGK-BL-DIG-2027` — County digital services |
| Owner scope | PE-wide |
| Funding source | Government of Kenya |
| Approved amount | KES 20,000,000 |
| Reserved / Committed / Available | KES 0 / KES 0 / KES 20,000,000 |

No MoH actor, line, reservation, task or amount is visible in the Kisumu context, and vice versa.

### 15.8 Seed execution rules

- Upsert by exact stable seed identifiers; do not create duplicates.
- A second seed run produces no semantic change, new version, duplicate reservation or duplicate lifecycle authority.
- Validate Budget and lines through the same domain rules used by commands.
- Seed lifecycle and Finance events use the named role actors, never Administrator.
- Fail loudly on missing configuration, invalid total, scope conflict, duplicate Active version or line floor breach.
- Seed no Strategy reference, treatment, expenditure, forecast, note or generic evidence field.
- Isolated profiles are created and removed by their tests; they do not contaminate the default integrated seed.

## 16. Acceptance contract

| ID | Acceptance result |
|---|---|
| BUD-AC-001 | The module installs and imports without the legacy Demands package, Procurement Home or removed treatment code. |
| BUD-AC-002 | No executable metadata, route, service, field, seed or active test contains Allocation as a separate object, Budget Value Treatment, PVO or Value Commitment. |
| BUD-AC-003 | A scoped Budget Officer can register one Draft for a PE/FY and receives generated Budget, Version and Budget Line references. |
| BUD-AC-004 | A System Administrator without a Budget assignment cannot create, submit, review, activate, close or confirm Finance. |
| BUD-AC-005 | The only editable initial Budget fields are external approval reference, approval date, authorised total and one approval document. |
| BUD-AC-006 | The only editable line fields are title, owner scope, funding source and approved amount. |
| BUD-AC-007 | Submission and activation fail when approval data is incomplete or the line total differs from authorised total. |
| BUD-AC-008 | Reviewer recommendation and Activation Authority activation use distinct scoped capabilities; the submitter cannot perform either on the same version. |
| BUD-AC-009 | Return requires a reason, returns the version to Draft and preserves the submitted decision history. |
| BUD-AC-010 | Active, Superseded and Closed versions and lines reject direct mutation. |
| BUD-AC-011 | Departmental Need acceptance, DPP submission and Plan Item Draft save create no reservation or Budget ledger event. |
| BUD-AC-012 | `check_funding` returns exact current positions and changes no state. |
| BUD-AC-013 | Single-source confirmation creates one full idempotent reservation and the exact KES 100m − KES 80m = KES 20m position. |
| BUD-AC-014 | Combined-source confirmation creates the KES 72m and KES 48m reservations atomically or creates neither. |
| BUD-AC-015 | A KES 10m shortfall returns the exact failing allocation and creates no partial reservation or Finance success. |
| BUD-AC-016 | Concurrent confirmation commands cannot oversubscribe a line; a duplicate correlation returns the original effective result. |
| BUD-AC-017 | Finance task, decision and planner-waiting UI remain owned by Procurement Planning; Budget adds no duplicate Finance screen or queue. |
| BUD-AC-018 | **Open Budget & Funding** opens the exact authorised Budget Line detail and causes no funding mutation. |
| BUD-AC-019 | Partial conversion of a KES 80m reservation to a KES 60m commitment leaves KES 20m reserved, KES 60m committed and KES 20m available on the KES 100m line. |
| BUD-AC-020 | Release, revalidation, conversion and commitment adjustment require exact authenticated downstream events and are retry-safe. |
| BUD-AC-021 | A Needs Attention reservation keeps its remaining amount reserved and blocks downstream progression. |
| BUD-AC-022 | A successor reduction below Reserved plus Committed and an unbalanced transfer are blocked. |
| BUD-AC-023 | Activating a valid successor atomically supersedes the prior Active Version and preserves Budget Line, reservation and commitment identities. |
| BUD-AC-024 | Existing line title, owner scope and funding source cannot change after activation; a new funded identity receives a new line ID. |
| BUD-AC-025 | A line with a remaining reservation or active commitment cannot be omitted from a successor. |
| BUD-AC-026 | `resolve_budget_context` and line services return the correct MoH or Kisumu data and never use first-record fallback. |
| BUD-AC-027 | Downstream direct-table reads, Draft reads and direct state/amount mutation are rejected. |
| BUD-AC-028 | No Budget schema, service, seed or screen contains actual expenditure, outstanding commitment, expenditure freshness or a fake zero/Unavailable placeholder. |
| BUD-AC-029 | No Budget schema, service, seed or screen contains a Strategy reference, classification, separate purpose, generic note or miscellaneous attachment. |
| BUD-AC-030 | The default seed is deterministic and an immediate second run produces no change. |
| BUD-AC-031 | Missing Configuration prerequisites fail seed execution without fallback records. |
| BUD-AC-032 | The five primary routes render without console errors and match the approved static designs. |
| BUD-AC-033 | Reviewer and Activation Authority inspect Overview, Budget Lines, Changes and History for the exact submitted Version; no tab substitutes Active data. |
| BUD-AC-034 | Loading, no-baseline, forbidden and server-error states disclose no false or unauthorised funding data. |
| BUD-AC-035 | Frappe header, breadcrumb and existing PE/FY selector are reused and are not duplicated inside the Vue page. |
| BUD-AC-036 | Closing after the FY blocks new reservations while preserving all history and funding lineage. |

### 16.1 Minimum automated coverage

| Rule group | Required automated coverage |
|---|---|
| Scope and permissions | BUD-BR-001–003; BUD-AC-003–004, 026–027 |
| Baseline and line domain | BUD-BR-004–008, 019–020, 025; BUD-AC-005–010, 024–025 |
| Finance and arithmetic | BUD-BR-009–016; BUD-AC-011–021 |
| Successor and closure | BUD-BR-017–023; BUD-AC-022–023, 036 |
| Cross-module boundary | BUD-BR-024; BUD-AC-017–018, 027–029 |
| Seeds and isolation | BUD-AC-026, 030–031 |
| UI | BUD-AC-032–035 |

## 17. Implementation and test constraints

### 17.1 Frappe and UI implementation

- Correct the retained Budget application in place. Delete separate Allocation, treatment, Funding Exception and expenditure artifacts; do not preserve aliases or compatibility response fields.
- Reuse the proven Vue 3 single-file-component pattern mounted into one `frappe.ui.make_app_page()` Desk page.
- Reuse the approved KenTender design tokens and scoped component styles. Do not import Claude Design runtime files into production.
- Keep Claude Design exports under `docs/` as visual evidence. Port their semantic composition into repository-owned Vue components.
- Do not add Tailwind, CDN styles, global CSS resets or a second application shell.
- Scope component styles so Frappe Desk chrome does not alter page controls and page styles do not bleed into Desk.
- Mount once per route and unmount on Frappe page teardown. Do not install duplicate route or `popstate` listeners.
- Use stable `data-testid` hooks on primary controls, tabs, tables, status badges, errors and dialogs.
- Use Frappe permissions only as a coarse boundary; every service and command repeats exact PE/FY/capability/task authorization server-side.
- Keep all positions, readiness rules, state transitions and concurrency controls on the server even when the UI hides or disables an action.
- Integrate Planning through the logical service contracts. Do not import Planning controllers into Budget or Budget controllers into Planning.
- Preserve the existing Planning Finance UI. Implement only the Budget Line route needed by **Open Budget & Funding**.

### 17.2 TDD and efficient verification

For every behaviour change:

1. add or identify the smallest failing domain, service or component test;
2. run only that test while implementing the change;
3. run the directly affected test file;
4. run the relevant Budget test group after the local tests pass; and
5. run the full Budget application suite once at the completion of the change group, not after every small edit.

Run Planning contract tests only when `check_funding`, `reserve_funding`, Budget Line detail or reservation response shape changes. Run Contract Management contract tests only when revalidation, conversion or adjustment changes. Run fresh install/migrate/seed, double-seed and browser smoke at the release-candidate checkpoint and again only if a later change affects installation, seed or UI wiring.

Concurrency tests use deliberate parallel reserve and activation commands against isolated fixtures. They are not substitutes for rerunning hundreds of unrelated tests after each local fix.

Browser verification is one focused path per role:

- Budget Officer: no-baseline workspace → save baseline → add lines → submit;
- Budget Reviewer: open exact task → inspect all four tabs → recommend;
- Activation Authority: inspect all four tabs → activate;
- Budget Viewer: open Active Budget → lines → line detail → Funding Activity;
- Finance Confirmation Officer: use the existing Planning Finance task → open Budget Line → return → confirm in separate reset profiles; and
- forbidden actor: confirm no data disclosure.

Do not wait for `networkidle` on Frappe Desk. Wait for DOM content and an explicit page-ready element because persistent socket connections may remain open.

### 17.3 Required release evidence

- static scan showing no removed concept, expenditure artifact or legacy Demands/Home import in executable Budget code;
- schema and metadata migration succeeds;
- deterministic Budget seed succeeds twice;
- targeted domain, permission, lifecycle, arithmetic, concurrency and service tests pass;
- the full Budget application suite passes once after targeted stabilization;
- approved Planning Finance contract tests pass for single, combined, insufficient and duplicate-correlation profiles;
- Contract Management conversion/adjustment contract tests pass before those downstream actions are enabled;
- production build succeeds without global CSS regression; and
- scripted browser smoke passes with no Budget-page console or request failure.

## 18. Prohibited shortcuts

- No separate Allocation, Budget Value Treatment, PVO, Value Commitment, Funding Exception or expenditure object under another label.
- No Strategy field on Budget or Budget Line.
- No Budget-owned Finance task, decision, queue, sufficient/insufficient form or planner-waiting screen.
- No reservation at Need acceptance, DPP submission or Plan Item Draft save.
- No partial all-source Finance confirmation or silent Budget Line substitution.
- No actual expenditure, outstanding commitment, forecast, utilisation score or `Unavailable` placeholder.
- No editable Budget title, classification, separate purpose, generic description, source type, effective date, authority name, contact, note, justification or miscellaneous attachment.
- No alias DocType, compatibility service, dual read, shadow write or silent fallback for removed records.
- No first PE, first OU, first FY, first Budget or Administrator fallback.
- No downstream raw SQL or ORM read of Budget tables.
- No client-only permission, total, floor, availability or lifecycle enforcement.
- No user-editable generated reference, calculated position, reservation, commitment or ledger event.
- No direct edit of Active, Superseded or Closed data.
- No arbitrary JSON field used to avoid the canonical Budget Line, reservation or commitment model.
- No design-system invention of data, states, controls, columns or copy.
- No behaviour or implementation rule inside Claude Design prompts.
- No Frappe header, breadcrumb or PE/FY selector recreated inside the page canvas.
- No full-suite rerun after every local fix when a targeted test provides the required feedback.

## 19. Traceability and precedence

This document reconciles and supersedes conflicting Budget requirements contained in:

- `KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1.0.md`; and
- `01_Budget_and_Funding_MVP1_Requirements.md`.

It consumes context from the approved PE/FY configuration contract and preserves the already-approved Procurement Planning Finance ownership, IDs, amounts and UI surfaces defined by:

- `KenTender_CFG-CHG-002_PE_and_Financial_Year_Maintenance_v0.3.md`;
- `KenTender_PLN-FR-001_Procurement_Planning_MVP-1_Functional_Requirements_v0.1.md`;
- `KenTender_PLN-SDC-001_Procurement_Planning_MVP-1_Seed_Data_Contract_v0.1.md`; and
- `KenTender_PLN-STC-001_Procurement_Planning_MVP-1_Stitch_Contract_v0.1.md`.

Budget stores no Strategy field. The selected Strategic Objective and its snapshot remain governed by `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1.3.md` and Procurement Planning.

Where an earlier Budget item is not retained in this v1.1 document, it is outside the approved Budget & Funding scope.
