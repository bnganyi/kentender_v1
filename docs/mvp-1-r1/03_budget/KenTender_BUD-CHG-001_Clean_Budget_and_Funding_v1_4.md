# BUD-CHG-001 — Clean Budget & Funding

| Control | Value |
|---|---|
| Document ID | BUD-CHG-001 |
| Version | 1.4 |
| Date | 3 September 2026 |
| Status | **Approved** |
| Approved on | 3 September 2026 |
| Supersedes | v1.3 (approved 3 September 2026) and all earlier versions, in full |
| Module | Budget & Funding |
| Change type | Moves funding reservation from Procurement Planning to Procurement Requisition and adds a plan affordability contract. Domain arithmetic, funding lineage and the reservation machinery itself are unchanged. |
| Standards | Governed by KT-STD-001 v1.1. Sections not restated here are inherited from it. |
| Implementation posture | Correction in place; no compatibility layer |

**Controlling decision:** Budget & Funding is a **record of externally allocated funds**, not a budgeting function. Appropriation, enactment, exchequer release and accounting happen in IFMIS and are outside this system. KenTender registers the externally approved procurement allocation, exposes eligible Procurement Budget Lines, and protects those amounts through reservations and commitments so that procurement cannot commit money it does not have.

It is **fully separate from ERPNext accounting**. ERPNext's own `Budget`, `Cost Center` and accounting records govern the finance function on the same site and are never read, mirrored or reconciled by this module.

---

## 1. Governing decision

This document is the single implementation authority for Budget & Funding. The existing application is corrected in place. Removed concepts are deleted rather than renamed, aliased, dual-read or retained behind feature flags.

### 1.1 Conflict and disposition register

Items disposed of in v1.2 and not reopened: the separate Allocation object; Budget Value Treatment, the treatment questionnaire and Public Value Objectives; Budget-side Strategy references; reservation at Departmental Need acceptance; the Budget-owned Finance confirmation screen; one-reservation-per-Plan-Item; the separate Budget Revision object; the Budget Reviewer / Budget Activation Authority split and the `In Review` and `Awaiting Activation` statuses; the Funding Exception object; Expenditure Snapshot and actual-expenditure data; the advanced Funding Performance dashboard; budget classification and separate purpose fields; generic source, authority, notes and evidence fields.

New in v1.4:

| Earlier item | Disposition in v1.4 |
|---|---|
| Reservations created at Procurement Planning, one per Plan source allocation, before the Annual Plan could be submitted | **Move to Procurement Requisition.** A ministry plan runs to hundreds of items; creating a reservation for each at planning locked the whole budget from the start of the planning cycle and made every plan revision a release-and-re-reserve exercise. PPADA requires the plan to sit within the approved budget — an affordability test, not a per-item hold. |
| No aggregate affordability contract | **Add `check_plan_affordability`.** Non-mutating; returns per-line approved amount, planned total, current positions and two verdicts. Within-approved blocks plan submission; within-currently-available is advisory. |
| `check_funding` and `reserve_funding` called by Procurement Planning | **Called by Procurement Requisition.** The contracts, their all-or-none semantics, idempotency and ledger effects are unchanged; only the caller and the moment change. |
| Finance Confirmation Officer confirming per Plan Item | **Confirms once per Plan Version** against the affordability statement, per PLN-CHG-001 v1.7 §4.11. The role, its scope and its registry entry are unchanged. |

New in v1.3:

| Earlier item | Disposition in v1.3 |
|---|---|
| DocType named `Budget` | **Rename to `Procurement Budget`.** ERPNext ships its own `Budget` DocType in the Accounts module, set against a Cost Center or Project for a Fiscal Year with Stop, Warn and Ignore control actions. Frappe DocType names are globally unique per site, so with ERPNext installed the existing name will fail at install or migrate. `BudgetVersion`, `BudgetLine` and `BudgetLineVersion` are renamed to match. |
| Any relationship between a Procurement Budget Line and an ERPNext Cost Center | **None.** Fully separate. No `cost_center` field, no reconciliation link, no derived value. The two systems control the same money for different purposes and are not integrated in MVP 1. |
| `procuring_entity_id` on `Budget` | **Remove.** One site is one Procuring Entity. BUD-BR-002 becomes one Procurement Budget per Fiscal Year. |
| `financial_year_id` referencing a KenTender `FinancialYear` | Replace with `fiscal_year`, referencing the ERPNext `Fiscal Year` governed by CFG-CHG-002 v0.6 §4.2. |
| Assignments scoped by PE, FY, organisation unit, capability and effective dates | **Remove PE, FY and capability.** Business authority is a role-bound `User Responsibility Assignment` under AUTH-ADR-001 v1.6, and Fiscal Year is never a user-permission dimension. One Budget Officer assignment works across every year; eligibility comes from the record's own fiscal year and version status. |
| "Capability" as the permission primitive throughout §7, §8.2, §12.5, §12.6 and §14 | **Remove.** Registered business roles replace every capability string. |
| `Budget Viewer` workflow role | **Remove.** Read access is produced by the registered permission hooks acting on the actor's assignments, exactly as Strategy Viewer was removed in STR-CHG-001 v1.6. |
| `owner_org_unit_id` on the line version | **Retain unchanged.** It governs which lines a Need may draw on — record eligibility, not user scope. AUTH prohibits organisation unit as a *user* scope dimension only. The label "PE-wide" becomes **Entity-wide**. |
| County Government of Kisumu (`PE-CGK`) isolation baseline, its three actors and every cross-PE isolation test | **Remove entirely.** Creating a second Procuring Entity is structurally impossible under CFG-AC-003, so the seed would fail unconditionally. |
| Bespoke fixture cast (`moh.budget.officer@…`, `bud.viewer.moh@…`, and the rest) | Replace with the KT-STD-001 §8.3 shared register, extended by the Budget actors in §14.1. |
| PE row in every artboard context strip and identity card | **Remove.** The **Financial Year** row is retained where it is the record's own attribute and replaced by a changeable year filter on the workspace. |
| "the existing KenTender PE/FY selector" in §11.1, §11.18 and §12.1 | **Remove.** The component no longer exists. |
| Restated closed-input rules, common page states, TDD protocol, release evidence and product-wide prohibitions | **Remove.** Cite KT-STD-001. |
| Citations of CFG-CHG-002 v0.3 and STR-CHG-001 v1.5 | Update to CFG-CHG-002 v0.6 and STR-CHG-001 v1.6. |

**Identifiers are deliberately unchanged.** `MOH-BUD-2027-001`, `MOH-BL-DHI-2027` and the rest keep their existing prefixes. They are opaque stable strings referenced by approved Procurement Planning contracts and seed data; the embedded `MOH` is not a permission dimension, a source of truth or a scope check. Renaming them would break downstream approved documents for no functional gain. Do not "tidy" them.

---

## 2. Purpose and exclusions

Budget & Funding shall provide: one registered procurement budget for each fiscal year; immutable, reviewable Procurement Budget Versions; simple lines with a clear funded purpose, owning organisation scope, funding source and approved amount; exact approved, reserved, committed and available positions; atomic idempotent Finance confirmation for one or more Plan Item allocations; preserved funding lineage from Plan Item allocation to reservation and contract commitment; controlled successor versions for externally approved changes; and neutral read access that grants no financial authority.

The module shall not contain: appropriation, budget enactment, exchequer release, cash, ledger, invoice, payment or accounting workflows; any ERPNext accounting integration, Cost Center reference or reconciliation surface; Departmental Need approval or a reservation created by any Procurement Planning event; a separate Allocation record; Strategy fields; procurement category, method, schedule, lot, tender or contract authoring fields; actual expenditure, outstanding commitment or an `Unavailable` placeholder; forecasts, utilisation percentages, performance scores, trends or charts; manual reservation or commitment entry; a duplicate Finance task, decision or planner waiting screen; generic notes, descriptions, justification, contacts or miscellaneous attachments; editable technical identifiers; or a new Frappe shell, header, breadcrumb, global selector or navigation system.

The data-purpose gate and the omission default are in KT-STD-001 §7. The external approval reference, approval date and approval document pass that gate because the Budget Approver uses them to verify that the line set faithfully represents the externally approved allocation. They are not generic source-reference fields.

---

## 3. Fixed external constraints and ownership

- The externally approved procurement allocation originates in IFMIS or an equivalent authoritative instrument. KenTender records it; it does not produce, approve or amend it.
- The ERPNext `Fiscal Year` catalogue, currency, organisation units and the funding-source catalogue come from Configuration & Governance. Budget creates or infers none of them.
- Strategy Alignment owns Strategic Objectives and downstream snapshots. Budget stores no Strategy link.
- Departmental Needs owns the Need and its selected line reference. Need acceptance creates no reservation.
- Procurement Planning owns Plan Items, source allocations, Finance tasks, Finance decisions and their UI. Budget owns the authoritative reservation and position calculation.
- Contract Management owns contracts and variations, and uses Budget services to convert or adjust the same funding lineage.
- Expenditure data may enter only through a separately approved change unit.

| Information or decision | Owner | Budget relationship |
|---|---|---|
| Site Procuring Entity, Organisation Units, ERPNext `Fiscal Year`, currency, funding-source catalogue | Configuration & Governance | Read configured identifiers; fail closed when absent. |
| Business authority and scope resolution | AUTH-ADR-001 v1.6 | Declare required business roles; implement no permission mechanism. |
| ERPNext `Budget`, `Cost Center`, accounts, journals | ERPNext | Never read, written, mirrored or reconciled by this module. |
| Strategic Objective and snapshot | Strategy Alignment / Procurement Planning | No Budget field or write. |
| Accepted Need and selected line | Departmental Needs | Validate through Budget contracts; create no hold. |
| Plan Item, source allocation, Finance task and decision | Procurement Planning | Call Budget check-and-reserve; store returned reservation references. |
| Procurement Budget, versions, lines, reservations, commitments, funding ledger | Budget & Funding | Create, govern and expose read-only. |
| Contract and variation | Contract Management | Call Budget conversion and adjustment services. |
| Payment, expenditure, accounting | IFMIS and ERPNext | No MVP-1 data or UI. |

Dependency direction: **Configuration & Governance → Budget & Funding → Departmental Needs / Procurement Planning → Contract Management**. Budget shall not import a downstream DocType controller or query a downstream table directly.

---

## 4. Canonical domain model

All identifiers are server-generated. Framework audit fields remain framework-managed.

### 4.1 Procurement Budget

The stable identity of one fiscal year's procurement allocation record.

| Field | Operational purpose and system effect |
|---|---|
| `budget_id` | Immutable generated reference used by routes, services, audit and downstream lineage. Not editable. |
| `fiscal_year` | The ERPNext `Fiscal Year` whose funding period this record governs. Required and immutable after creation. |
| `currency` | Fixes one currency for every line and calculation. Copied from the site ERPNext Company default at creation and immutable. |

There is no `procuring_entity_id`. Every record belongs to the site entity by construction. There is at most one Procurement Budget per Fiscal Year. The display title is derived as `{entity name} procurement budget {FY label}` and is not stored.

### 4.2 Procurement Budget Version

The immutable approval boundary for one registered baseline or successor revision.

| Field | Operational purpose and system effect |
|---|---|
| `budget_version_id` | Immutable generated reference used by line versions, review tasks and audit. |
| `budget_id` | Links the version to its stable Procurement Budget. |
| `version_number` | Ordered version history; generated per Budget. |
| `based_on_budget_version_id` | Identifies the Active version copied to create a successor. Empty only for Version 1. |
| `revision_type` | Classifies an externally approved successor as `Supplementary allocation`, `Reduction`, `Transfer` or `Correction`. Required only when `based_on_budget_version_id` is present. |
| `status` | `Draft`, `Submitted for approval`, `Active`, `Superseded` or `Closed`. |
| `approval_reference` | Identifies the external approval instrument reviewed before activation. Required. |
| `approval_date` | Confirms that external approval preceded KenTender activation. Required. |
| `approval_document_file_id` | Links exactly one uploaded approval document used by the Budget Approver. Required. |
| `authorised_total` | The total approved by the external instrument. Version lines must sum to it before submission or activation. Required and positive. |

Submitted, approved, superseded and closed actors and timestamps are audit events. A Return reason is stored on the decision event, not as a version field.

### 4.3 Procurement Budget Line

| Field | Operational purpose and system effect |
|---|---|
| `budget_line_id` | Immutable generated reference used by Needs, Plan allocations, reservations, commitments and routes. |
| `budget_id` | Prevents the line identity from moving to another fiscal year's Budget. |

### 4.4 Procurement Budget Line Version

| Field | Operational purpose and system effect |
|---|---|
| `budget_line_version_id` | Immutable generated reference for review comparison and audit. |
| `budget_version_id` | Binds the values to one immutable version. |
| `budget_line_id` | Preserves downstream funding lineage across approved amount changes. |
| `title` | The funded purpose displayed in selectors, tables and snapshots. Required. No separate purpose or description field. |
| `owner_org_unit_id` | Limits **line eligibility** to one configured Organisation Unit. Empty means Entity-wide. This is a domain rule about which Needs may draw on the line; it is never a user-scope or permission check. |
| `funding_source` | From the governed funding-source catalogue; copied into downstream funding snapshots. Required. |
| `approved_amount` | The allocation ceiling for the line in this version. Required and positive. |

After first activation, `title`, `owner_org_unit_id` and `funding_source` define the stable line identity and cannot change in a successor. A genuinely different purpose, owner scope or funding source requires a new line. A successor may change only the approved amount.

There is no `cost_center` field and no ERPNext accounting reference of any kind.

### 4.5 FundingReservation

| Field | Operational purpose and system effect |
|---|---|
| `reservation_id` | Immutable generated reference returned to Procurement Planning and used by downstream lineage. |
| `budget_id` | Fixes the fiscal year funding root. |
| `budget_version_id_at_creation` | Preserves the version under which the reservation was confirmed. |
| `budget_line_id` | Identifies the funded purpose and balance affected. |
| `plan_item_id` | Links the reservation to the governed Plan Item. |
| `plan_source_allocation_id` | Distinguishes multiple source allocations and prevents duplicate or partial confirmation. |
| `original_amount` | The full amount confirmed for that allocation. Required and positive. |
| `remaining_amount` | The unconverted and unreleased hold. Changed only by Budget services. |
| `status` | `Active`, `Partially Converted`, `Converted`, `Released` or `Needs Attention`. |
| `correlation_id` | Makes Finance retries idempotent and binds every reservation in one all-source confirmation transaction. |

There is no `Requested` reservation. A failed check creates no reservation. There is no expiry date, manual authority field, note or attachment.

### 4.6 ProcurementCommitment

| Field | Operational purpose and system effect |
|---|---|
| `commitment_id` | Immutable generated reference used by Contract Management and funding lineage. |
| `reservation_id` | Prevents a commitment from bypassing the confirmed funding lineage. |
| `contract_id` | Identifies the owning downstream contract. Required and unique within the reservation lineage. |
| `current_amount` | The current contractual obligation; affects committed and available positions. Changed only through the adjustment service. |
| `status` | `Active`, `Cancelled` or `Closed`. |

One reservation may convert into more than one commitment, but the sum converted shall never exceed its remaining amount plus its existing commitments. Contract details, supplier, dates, variations and payments remain in Contract Management.

### 4.7 FundingLedgerEvent

Append-only: event ID and type; Budget, line, reservation and commitment IDs as applicable; Plan allocation, contract or variation reference; amount; before and after approved, reserved, committed and available positions; actor or calling service, timestamp and correlation ID; and a typed revalidation failure code where applicable. Users do not create or edit ledger events.

---

## 5. Canonical calculations and invariants

For one line at an `as_at` point:

**Reserved** = sum of `remaining_amount` for reservations in `Active`, `Partially Converted` or `Needs Attention`.
**Committed** = sum of `current_amount` for commitments in `Active`.
**Available** = `approved_amount − Reserved − Committed`.

Budget totals are the sums of the Active Version's line positions. Users never enter calculated totals.

| ID | Rule and enforcement |
|---|---|
| BUD-BR-001 | Every Budget write requires an Active site-wide `User Responsibility Assignment` for the required business role, resolved server-side. No Procuring Entity, Fiscal Year or capability scope check participates. |
| BUD-BR-002 | One Fiscal Year has at most one Procurement Budget and one Active Version. Enforced by a database-level partial unique index or equivalent guard **and** in the activation transaction. Serialization alone is insufficient. |
| BUD-BR-003 | Every line amount and funding event uses the Budget currency. Cross-currency funding is outside MVP 1. |
| BUD-BR-004 | Approval reference, approval date, one approval document and a positive authorised total are required before submission. The approval date cannot be in the future or after activation, and the version line sum shall equal `authorised_total`. |
| BUD-BR-005 | Only Draft versions are editable; Submitted for approval, Active, Superseded and Closed versions are read-only. |
| BUD-BR-006 | Only an Active Version may support a new reservation. |
| BUD-BR-007 | A line is eligible for an allocation only when it is in the resolved Active Version and its owner scope is Entity-wide or matches the source Need's Organisation Unit. This is record eligibility, evaluated after the actor's responsibility check, never instead of it. |
| BUD-BR-008 | The allocation's funding source shall equal the line's funding source. Procurement type does not restrict eligibility. |
| BUD-BR-009 | No Procurement Planning event creates a reservation. Need acceptance, DPP submission, DPP validation, Plan Item formation, plan funding confirmation, Annual Plan adoption, statutory approval and publication all leave Budget balances unchanged. Reservation begins at Procurement Requisition. |
| BUD-BR-010 | A reservation request covers the complete current source-allocation set for the drawing record. All required reservations succeed in one transaction or none is created. |
| BUD-BR-011 | Each Plan source allocation receives exactly one effective reservation. Repeating the same correlation returns the same result. |
| BUD-BR-012 | `check_funding` and `check_plan_affordability` are both non-mutating. A check token is short-lived and cannot bypass locked revalidation during reservation. Plan affordability issues no token. |
| BUD-BR-013 | Reserved, committed and available positions shall never be negative. Concurrent commands cannot oversubscribe a line. |
| BUD-BR-014 | A reservation may be partially converted into one or more commitments; only the unconverted remainder stays reserved. |
| BUD-BR-015 | Release, conversion and commitment adjustment require an authenticated downstream event and are idempotent by correlation ID. No user keys amounts directly in Budget UI. |
| BUD-BR-016 | `Needs Attention` keeps the remaining amount reserved while downstream progression is blocked. It does not silently release funds. |
| BUD-BR-017 | A successor cannot reduce a line below its current Reserved plus Committed position. |
| BUD-BR-018 | A Transfer successor shall have equal total increases and decreases and shall preserve `authorised_total`. |
| BUD-BR-019 | An existing line identity may change approved amount only. A new purpose, owner scope or funding source requires a new line. |
| BUD-BR-020 | A line may be omitted from a successor only when it has no remaining reservation or active commitment. |
| BUD-BR-021 | Approval rechecks approval evidence, line total, floors, transfer balance, responsibility and concurrency under one transaction lock before activating. |
| BUD-BR-022 | Approving a successor atomically makes it Active and the previous Active Version Superseded, preserving all line, reservation and commitment identities. |
| BUD-BR-023 | A Closed Budget admits no new reservations but retains all read, audit and downstream lineage. |
| BUD-BR-024 | Downstream modules use Budget service contracts and cannot query or mutate Budget tables directly. |
| BUD-BR-025 | Generated identifiers, calculated positions, statuses and audit authority are never client-editable. |
| BUD-BR-026 | No Budget path reads, writes or reconciles an ERPNext `Budget`, `Cost Center`, account or journal record. |

---

## 6. Lifecycle and governance

| Current status | Command | Next status | Authorised actor |
|---|---|---|---|
| Draft | Submit for review | Submitted for approval | Budget Officer |
| Submitted for approval | Return | Draft | Budget Approver; reason required |
| Submitted for approval | Approve | Active | Budget Approver |
| Active | Activate successor | Superseded | System, inside the successor activation transaction |
| Active | Close after FY | Closed | Budget Approver |

Version 1 is the initial baseline; Version 2 and later are successor revisions. There is no separate revision workflow and no recommend-then-activate two-step — Approve both decides and activates in one atomic transaction.

- A Budget Officer may create and edit only Draft versions.
- The submitting Budget Officer cannot approve the same version, even when that user also holds Budget Approver. Enforced from the version's own submission audit event.
- Return requires 10–500 characters and preserves the submitted snapshot and decision event.
- Approval means "available for KenTender procurement control". It does not approve the public budget, which happens in IFMIS.
- At most one open Draft or Submitted-for-approval successor may exist per Budget.
- A successor is always copied server-side from the current Active Version.
- Closing requires the fiscal year to have ended and no reservation with a remaining amount. Active commitments may remain visible for lineage.
- Records and ledger events are never deleted after submission.

---

## 7. Roles and permissions

Three Budget business responsibilities exist. All are registered in the AUTH-ADR-001 v1.6 §4.4 registry with `scope_type = Site-wide`.

| Business role | Scope type | Permitted actions |
|---|---|---|
| Budget Officer | Site-wide | Register the initial Draft, create a successor, edit Draft approval details and lines, and submit. |
| Budget Approver | Site-wide | Inspect a submitted version; return it with a reason, or approve and activate it; close a Budget after the fiscal year. |
| Finance Confirmation Officer | Site-wide | Open the one Procurement Planning Finance task per Plan Version and confirm or return it against the affordability statement. Confirmation creates no reservation. Grants no Budget authoring, approval or activation authority. |

Registry properties: none is an `exclusive_office`; all are granted by Administrator or System Manager; Budget Officer and Budget Approver carry `sod_tags` sufficient for the no-self-approval rule.

There is no Budget Viewer role. Read access is produced by the registered permission hooks acting on the actor's assignments. **Auditor** is a registered business role under AUTH-ADR-001 v1.6 §4.4 and confers no Budget mutation. **Procurement Planner** reads eligible lines through contracts and holds no Budget responsibility.

The **contract service principal** is an authenticated service account, not a business role and not a registry entry. It calls `revalidate_reservations`, `release_reservation`, `convert_reservation` and `adjust_commitment` with a downstream event reference and an idempotency key. It cannot create a reservation, edit a version or read a Draft.

Administrator and System Manager receive full technical read under AUTH-ADR-001 v1.6 §8 and no Budget business action. No capability profile, capability string, operational scope assignment, Fiscal Year grant, Frappe User Permission or parallel permission store participates in a Budget authorization path.

---

## 8. Procurement Planning and downstream integration

### 8.1 Two distinct moments

Funding is touched twice, for different purposes, by different callers.

| Moment | Caller | Contract | Effect on balances |
|---|---|---|---|
| **Annual Plan submission** | Procurement Planning | `check_plan_affordability` | None. Non-mutating affordability statement only. |
| **Procurement Requisition** | Procurement Requisitions | `check_funding` then `reserve_funding` | Creates reservations, all-or-none. |

Planning never reserves. Its Finance Confirmation Officer confirms once per Plan Version that the consolidated plan sits within the approved budget — the evidence the accounting officer adopts on — and that confirmation writes nothing to Budget. Requisition reserves, because that is where independent drawdown makes double-spend a real risk.

**Open Budget & Funding** from a Planning or Requisition funding surface opens BUD-UI-05 for the exact line. Navigation creates no decision, reservation or mutation.

### 8.2 Plan affordability

`check_plan_affordability` receives a Fiscal Year and the plan's per-Procurement-Budget-Line planned totals, and returns for each line:

- the approved amount on the Active Version;
- the plan's planned total for that line;
- the current reserved, committed and available positions with an `as_at` instant;
- **within approved amount** — planned total ≤ approved amount; and
- **within currently available** — planned total ≤ approved − reserved − committed.

The first verdict is the blocking one, because a plan exceeding a line's approved amount cannot lawfully be executed. The second is advisory only: a plan legitimately covers a whole year while reservations reflect drawdown to date, so the two are measured over different horizons and a plan exceeding today's availability is normal in mid-year revision.

The call locks nothing, writes nothing, creates no token and produces no ledger event. Repeating it returns a fresh statement at a new `as_at`.

### 8.2A All-source reservation at Requisition

1. Procurement Requisitions supplies the authorised Plan Item, the drawn quantity and value, every `plan_source_allocation_id`, and a correlation ID.
2. Budget resolves the caller's authority and validates every line, amount, owner scope, funding source and current position.
3. `check_funding` returns one short-lived token and a position for every allocation; it writes nothing.
4. The confirming command calls `reserve_funding` with the token, expected locks and one idempotency key.
5. Budget locks all affected lines in stable ID order, reloads every position and creates one reservation per source allocation.
6. If any allocation fails, the entire command rolls back and returns the exact failing allocation and shortfall.
7. The caller stores the returned reservation references in the same orchestration boundary.

Partial source confirmation, line substitution and silent amount reduction are prohibited.

### 8.3 Later funding events

| Downstream event | Budget effect |
|---|---|
| Procurement Requisition raised against an eligible Plan Item | Create the reservation set for the drawn allocations, all-or-none. |
| Material change to a Requisition | Revalidate the same reservation set; create no second reservation. |
| Contract creation | Convert the required amount from the reservation to one or more commitments. |
| Contract value increase | Revalidate line availability, then increase the commitment through an adjustment event. |
| Contract value decrease or cancellation | Reduce or cancel the commitment and release the applicable remainder through one idempotent event. |
| Successor activation | Preserve valid lineage; mark an affected reservation `Needs Attention` only when a current invariant fails. |

No downstream event may directly update `remaining_amount`, `current_amount`, status or a line position.

---

## 9. Service and command contracts

### 9.1 Read and funding contracts

| Contract | Required input | Output and effect |
|---|---|---|
| `resolve_budget_context` | Fiscal Year | One Active Budget and version summary, or a typed not-found or ineligible error. |
| `list_eligible_budget_lines` | Fiscal Year, source Organisation Unit, optional funding source, search and paging | Active eligible lines with ID, title, owner scope, funding source and the four positions. No Draft lines. |
| `get_budget_line_position` | Line ID and `as_at` | Authorised line identity, active-version amount, current positions and version token. No mutation. |
| `check_plan_affordability` | Fiscal Year and per-line planned totals | Per-line approved amount, planned total, positions with `as_at`, and the two verdicts in §8.2. Non-mutating; no token, no lock, no ledger event. |
| `check_funding` | Plan Item and version, Finance task, source-set hash, complete allocation array, correlation ID | Non-mutating per-allocation eligibility, positions, required amounts, after-confirmation balances and a short-lived check token. |
| `reserve_funding` | Check token, expected task, source and version locks, idempotency key | All reservations and new positions, or one typed all-or-none failure. |
| `revalidate_reservations` | Exact reservation set, downstream event ID and type, idempotency key | Current or Needs Attention results and ledger events; no new reservation. |
| `release_reservation` | Reservation ID, amount, downstream cancellation event, idempotency key | Reduced remaining amount or Released status and a new line position. |
| `convert_reservation` | Reservation ID, contract ID, amount, idempotency key | One commitment, updated remainder and a new line position. |
| `adjust_commitment` | Commitment ID, new total, contract variation event, idempotency key | Updated commitment after locked revalidation, plus a ledger event. |
| `get_funding_lineage` | Plan Item, source allocation, reservation, contract or commitment reference | Ordered Budget, version-at-confirmation, line, reservation, commitment and ledger identities. |

There is no expenditure-ingest contract and no ERPNext accounting contract in MVP 1.

### 9.2 Governance commands

| Command | Purpose |
|---|---|
| `save_budget_version_draft` | Create or update Draft approval details with optimistic concurrency. |
| `save_budget_lines_draft` | Create, update or remove Draft lines as one validated change set. |
| `submit_budget_version` | Validate approval details, line total and version rules; move Draft to Submitted for approval. |
| `return_budget_version` | Require a correction reason and return a submitted version to Draft. |
| `approve_budget_version` | Revalidate responsibility, evidence, line total, floors, transfer balance and concurrency; atomically activate and supersede where applicable. |
| `create_budget_successor_version` | Copy the current Active Version and line identities into one Draft successor. |
| `close_budget` | Close an Active Budget after the fiscal-year and remaining-reservation guards pass. |

Every write requires the expected record version. Concurrency and idempotency rules are in KT-STD-001 §11.

---

## 10. UI architecture and routes

Budget & Funding remains a top-level module. Its menu contains only **Budget & Funding** and **Approval tasks**, the latter visible only to a Budget Approver. Finance tasks remain in Procurement Planning; no Budget-side Finance queue or screen is added.

| Screen | Canonical route | Purpose |
|---|---|---|
| BUD-UI-01 Budget & Funding workspace | `/app/budget` | Current fiscal year's Budget and operational position. |
| BUD-UI-02 Budget Version editor | `/app/budget/{budget_id}/version/{version_number}/edit` | Baseline or successor Draft approval details and lines. |
| BUD-UI-03 Budget workspace | `/app/budget/{budget_id}` | Read-only Overview, Budget Lines, Funding Activity and History. |
| BUD-UI-04 Approval task | `/app/budget/review/{budget_version_id}` | Approver inspection and return-or-approve decision. |
| BUD-UI-05 Budget Line detail | `/app/budget/line/{budget_line_id}` | Read-only line position and funding lineage; target of Planning's **Open Budget & Funding**. |

The Budget workspace uses URL-backed **Overview**, **Budget Lines**, **Funding Activity** and **History** tabs. The approval task uses **Overview**, **Budget Lines**, **Changes** and **History**. This document authorises no second dashboard, application shell or Frappe header.

---

## 11. Static Claude Design contract

Supply **KT-STD-001 §2 plus this section** to Claude Design. Nothing else. The closed-input rules, product-wide prohibitions, approved desktop shell, page-header pattern and division of supply are in KT-STD-001 §2.2–2.5 and are not repeated. Fixture actors, organisation units and fiscal years come from KT-STD-001 §8, extended by §14.1 below.

**Additional prohibitions for this document:** do not show a Procuring Entity row or selector, a Cost Center, an accounting reference, Strategy data, procurement classification, a separate purpose field, Value Commitment, treatment, actual expenditure, outstanding commitment, forecast, utilisation percentage, chart, contact, note, justification or generic attachment. Show the one named **Approval document** only on artboards that explicitly include it.

The Financial Year appears as a **record attribute** on Budget and version pages, and as a **changeable filter** on the workspace. It is never a gate and never a context selector.

### 11.1 BUD-DES-01 — Budget & Funding workspace

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding**

**Page content header**

- Eyebrow: **BUDGET & FUNDING**
- Title: **Budget & Funding**
- Description: **View the registered procurement budget and the funding position used by Procurement Planning.**
- No header action button

**Filter row**

- select showing **FY 2027/28**

**Current budget card**

- Heading: **Ministry of Health procurement budget 2027/28**
- Status: **Active**

| Label | Value |
|---|---|
| Budget reference | MOH-BUD-2027-001 |
| Active version | Version 1 |
| Currency | KES |
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

Do not show Finance tasks, a register button on this Active-state artboard, or a Procuring Entity row.

### 11.2 BUD-DES-02 — Register approved budget draft

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 1 Oct 2026, 09:20 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Register approved budget**

**Page content header**

- Title: **Register approved budget**
- Status: **Draft**
- No header action button

**Budget context card**

| Field label | Displayed value |
|---|---|
| Budget reference | Not assigned |
| Financial Year | FY 2027/28 |
| Currency | KES |

All three rows use the approved read-only field component.

**External approval card**

| Field label | Displayed value |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-01 (Demo) |
| Approval date | 30 Sep 2026 |
| Authorised total | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget 2027-28 (Demo).pdf |

Approval reference uses the approved input; Approval date the approved date component; Authorised total the approved currency input with a fixed KES prefix; Approval document one file component showing the exact filename.

**Fixed footer, left to right:** **Cancel**, **Save draft**. **Save draft** is primary.

Do not show a Budget title, authority name, source type, source date, effective date, description, notes, line editor, readiness card or submit action.

### 11.3 BUD-DES-03 — Draft Budget Lines editor

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 1 Oct 2026, 10:10 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Version 1 > Budget Lines**

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

Do not show classification, purpose, cost centre, allocation, notes or calculated fields inside a row.

### 11.4 BUD-DES-04 — Active Budget overview

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001**

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
| Submitted by | Josphat Mwangi |
| Approved and activated by | Beatrice Kamau |
| Activated | 3 Oct 2026, 11:15 EAT |

Do not show edit controls, Create revision, an approval stepper or a Procuring Entity row on this artboard.

### 11.4A BUD-DES-04A — Active Budget overview for Budget Officer

Duplicate BUD-DES-04.

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001**

Keep all BUD-DES-04 content unchanged and add one right-aligned primary page-header button: **Create revision**.

Do not add Edit budget, Add line, Close budget, Finance task or overflow-menu controls.

### 11.5 BUD-DES-05 — Active Budget Lines

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Budget Lines**

Reuse the BUD-DES-04 page content header without changing its content or placement.

**Tabs:** **Overview**, **Budget Lines** selected, **Funding Activity**, **History**

**Budget Lines table**

| Budget Line | Owner scope | Funding source | Approved | Reserved | Committed | Available | Action |
|---|---|---|---:|---:|---:|---:|---|
| MOH-BL-DHI-2027 · Digital health infrastructure programme | Digital Health | Government of Kenya | KES 100,000,000 | KES 80,000,000 | KES 0 | KES 20,000,000 | View |
| MOH-BL-HWD-2027 · Digital health workforce development | HR Management and Development | Government of Kenya | KES 60,000,000 | KES 0 | KES 0 | KES 60,000,000 | View |
| Total | — | — | KES 160,000,000 | KES 80,000,000 | KES 0 | KES 80,000,000 | — |

Do not show an Allocation column, utilisation, cost centre, purpose, row menu or edit action.

**Implementation note (no `.dc.html` artboard exists for this screen):** build it by reusing, verbatim, the BUD-DES-04 header and tabs component and the Budget Lines table component as it renders in the BUD-DES-13 family's Budget Lines duplicate. Do not design new table chrome.

### 11.6 BUD-DES-06 — Budget Line detail

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 4 Dec 2026, 09:58 EAT · opened from Procurement Planning Finance task `FNT-MOH-2027-021-001` · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BL-DHI-2027**

**Page content header**

- Eyebrow: **MOH-BL-DHI-2027**
- Title: **Digital health infrastructure programme**
- Status: **Active**
- No header action button

**Context strip**

| Label | Value |
|---|---|
| Budget | MOH-BUD-2027-001 · Version 1 |
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

Do not show Confirm funding, Return, Release, Convert, Adjust, Edit, approval evidence or contract fields.

### 11.6A BUD-DES-06A — Budget Line detail with an active reservation

Duplicate BUD-DES-06.

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 10 Dec 2026, 15:05 EAT · opened from the Active Budget Lines table · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BL-DHI-2027**

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

### 11.7 BUD-DES-07 — Funding Activity

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Funding Activity**

Reuse the BUD-DES-04 page content header without changing its content or placement.

**Tabs:** **Overview**, **Budget Lines**, **Funding Activity** selected, **History**

**Filter row, left to right**

- select showing **All Budget Lines**
- select showing **All funding events**

**Funding Activity table**

| Date and time | Event | Budget Line | Downstream reference | Amount | Actor |
|---|---|---|---|---:|---|
| 4 Dec 2026, 10:00 EAT | Reservation confirmed | MOH-BL-DHI-2027 | PPI-MOH-2027-021 · RSV-MOH-2027-021-001 | KES 80,000,000 | Josphat Mwangi |

Footer text: **Showing 1 funding event**

Do not show a chart, utilisation, expenditure, technical correlation ID, before/after JSON, manual Add event control or row action.

### 11.7A BUD-DES-07A — Active Budget History

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > History**

Reuse the BUD-DES-04 page content header without changing its content or placement.

**Tabs:** **Overview**, **Budget Lines**, **Funding Activity**, **History** selected

**Version history card**

| Date and time | Event | Actor |
|---|---|---|
| 3 Oct 2026, 11:15 EAT | Version 1 approved and activated | Beatrice Kamau |
| 1 Oct 2026, 16:20 EAT | Submitted for review | Josphat Mwangi |
| 1 Oct 2026, 15:55 EAT | Draft saved | Josphat Mwangi |
| 1 Oct 2026, 09:20 EAT | Budget Version 1 created | Josphat Mwangi |

Do not show funding ledger events, technical logs, comments, attachments or history from another Budget.

**Implementation note (no `.dc.html` artboard exists for this screen):** build it by reusing, verbatim, the BUD-DES-04 header and tabs component and the version-history table component as it renders in BUD-DES-07's Funding Activity event table — same row and column chrome, different event set.

### 11.8 BUD-DES-08 — Approval task · Overview

**Fixture context — outside the artboard:** Beatrice Kamau · `beatrice.kamau@moh.example.test` · Budget Approver · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Approval tasks > MOH-BUD-2027-001-V2**

**Page content header**

- Eyebrow: **MOH-BUD-2027-001 · VERSION 2**
- Title: **Approve budget version**
- Status: **Submitted for approval**
- No header action button

**Tabs:** **Overview** selected, **Budget Lines**, **Changes**, **History**

**Version identity card**

| Label | Value |
|---|---|
| Procurement budget | Ministry of Health procurement budget 2027/28 |
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
| Submitted by | Josphat Mwangi |
| Submitted | 15 Mar 2027, 16:20 EAT |

**Readiness card**

| Check | Result |
|---|---|
| Approval details complete | Ready |
| Budget Line total matches authorised total | Ready |
| Reservation and commitment floors | Ready |
| Transfer balance | Ready |

**Fixed footer, left to right:** **Return**, **Approve**. **Return** uses the danger-outline style; **Approve** is primary.

Do not show editable fields, comments, notes, actual expenditure or a second approval document.

### 11.9 BUD-DES-09 — Approval task · Budget Lines

**Fixture context — outside the artboard:** Beatrice Kamau · `beatrice.kamau@moh.example.test` · Budget Approver · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Approval tasks > MOH-BUD-2027-001-V2**

Reuse the BUD-DES-08 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Budget Lines** selected, **Changes**, **History**

**Submitted Budget Lines table**

| Budget Line | Owner scope | Funding source | Proposed amount | Current floor | Headroom |
|---|---|---|---:|---:|---:|
| MOH-BL-DHI-2027 · Digital health infrastructure programme | Digital Health | Government of Kenya | KES 90,000,000 | KES 80,000,000 | KES 10,000,000 |
| MOH-BL-HWD-2027 · Digital health workforce development | HR Management and Development | Government of Kenya | KES 70,000,000 | KES 0 | KES 70,000,000 |
| Total | — | — | KES 160,000,000 | KES 80,000,000 | KES 80,000,000 |

Do not show inputs, Remove, Add Budget Line, classification, purpose or row actions.

### 11.10 BUD-DES-10 — Approval task · Changes

**Fixture context — outside the artboard:** Beatrice Kamau · `beatrice.kamau@moh.example.test` · Budget Approver · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Approval tasks > MOH-BUD-2027-001-V2**

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

Do not show unchanged identity fields, inline editing, per-row accept or reject controls, comments or a side-by-side document viewer.

### 11.11 BUD-DES-11 — Approval task · History

**Fixture context — outside the artboard:** Beatrice Kamau · `beatrice.kamau@moh.example.test` · Budget Approver · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Approval tasks > MOH-BUD-2027-001-V2**

Reuse the BUD-DES-08 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Budget Lines**, **Changes**, **History** selected

**Version history card**

| Date and time | Event | Actor |
|---|---|---|
| 15 Mar 2027, 16:20 EAT | Submitted for review | Josphat Mwangi |
| 15 Mar 2027, 15:55 EAT | Draft saved | Josphat Mwangi |
| 15 Mar 2027, 13:10 EAT | Successor Version 2 created | Josphat Mwangi |

Do not show comments, attachments, technical request logs, funding ledger events or history from another version.

### 11.12 BUD-DES-12 — Retired

BUD-DES-12 modelled the removed `Awaiting Activation` status as a second task screen for the Budget Activation Authority. That status and role no longer exist. BUD-DES-08 through BUD-DES-11 cover the single decision point, and **Approve** both decides and activates. Do not build a second task screen.

### 11.13 BUD-DES-13 — Initial baseline review · four tab variants

Create four artboards by duplicating BUD-DES-08, 09, 10 and 11 respectively.

**Fixture context for all four — outside the artboard:** Beatrice Kamau · `beatrice.kamau@moh.example.test` · Budget Approver · 2 Oct 2026, 10:00 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Approval tasks > MOH-BUD-2027-001-V1**

On all four duplicates: eyebrow **MOH-BUD-2027-001 · VERSION 1**; title **Approve budget version**; status **Submitted for approval**; preserve the corresponding selected tab; fixed-footer buttons **Return** and **Approve**, with **Return** danger-outline and **Approve** primary; and use only the replacement content below for the selected tab.

**Overview duplicate** — version identity card:

| Label | Value |
|---|---|
| Procurement budget | Ministry of Health procurement budget 2027/28 |
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
| Submitted by | Josphat Mwangi |
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
| 1 Oct 2026, 16:20 EAT | Submitted for review | Josphat Mwangi |
| 1 Oct 2026, 15:55 EAT | Draft saved | Josphat Mwangi |
| 1 Oct 2026, 09:20 EAT | Budget Version 1 created | Josphat Mwangi |

Do not show revision events, funding ledger events or history from another version.

### 11.13A BUD-DES-13A — Retired

BUD-DES-13A modelled the same removed `Awaiting Activation` stage for Version 1. BUD-DES-13 covers the single decision point. Do not build a second task screen.

### 11.14 BUD-DES-14 — Successor revision draft · Overview

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 15 Mar 2027, 15:55 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Version 2 > Overview**

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
| Financial Year | FY 2027/28 |
| Currency | KES |
| Based on | Active Version 1 |
| Revision type | Transfer |

The first three rows use approved read-only components. Revision type uses the approved select component.

**External approval card**

| Field label | Displayed value |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-02 (Demo) |
| Approval date | 14 Mar 2027 |
| Authorised total | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget Transfer 2027-28 (Demo).pdf |

Approval reference uses an input; Approval date a date component; Authorised total a KES currency input; Approval document one file component showing the exact filename.

Do not show a change reason, justification, source type, effective date, notes or a Procuring Entity row.

### 11.15 BUD-DES-15 — Successor revision draft · Budget Lines

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 15 Mar 2027, 15:55 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Version 2 > Budget Lines**

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

Do not show Remove on these existing referenced lines, classification, purpose, reservation controls, notes or actual expenditure.

### 11.16 BUD-DES-16 — Workspace state variants

Four static variants. Every variant contains the BUD-DES-01 page content header and filter row. Do not show position cards or Budget Line rows unless stated. State treatments follow KT-STD-001 §3.

Fixture context for Loading, No baseline and Server error — outside the artboard: **Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 1 Oct 2026, 09:00 EAT**. Fixture context for Forbidden — outside the artboard: **Samuel Otieno · `samuel.otieno@moh.example.test` · No Budget responsibility · 1 Oct 2026, 09:00 EAT**. Frappe header breadcrumb for all variants: **Home > Budget & Funding**.

| Variant | Main content | Buttons |
|---|---|---|
| Loading | One full-width skeleton Current budget card followed by four skeleton position cards and two skeleton table rows | None |
| No baseline | Heading **No approved procurement budget is registered for FY 2027/28.** Body **Register the externally approved budget before Procurement Planning requests funding confirmation.** | **Register approved budget** |
| Forbidden | Heading **You do not have access to Budget & Funding.** Body **Ask your KenTender administrator to review your assigned responsibilities.** | None |
| Server error | Heading **Budget & Funding could not be loaded.** Body **Try again. If the problem continues, contact KenTender support.** | **Try again** |

### 11.17 Existing Frappe, KenTender and Planning controls

No artboard is authorised for the Frappe header, breadcrumb, module menu, global page chrome, notifications or user menu. Reuse those without visual modification, per KT-STD-001 §2.5.

The Finance task, sufficient and insufficient states, return dialog and planner-waiting state are defined by Procurement Planning. Do not reproduce or redesign them here.

---

## 12. Functional interaction requirements — excluded from design prompts

Common page behaviour and accessibility follow KT-STD-001 §3.

### 12.1 BUD-UI-01 — Workspace

- The workspace resolves the Budget for the selected fiscal year. It never chooses the first Budget or the first year.
- The Financial Year select is a local view filter. It grants nothing, is remembered only with a visible reset, and is ignored when stale or invalid.
- One Active Budget returns its exact version and derived positions. A Draft successor does not replace or alter the Active projection.
- Counts and rows use the same server-side predicate as direct routes and services.
- **Register approved budget** appears only when the selected year has no Budget and the actor holds an Active Budget Officer assignment.
- **View budget** opens the exact server-returned `budget_id`.
- **Create revision** comes only from the server's `available_actions`.
- Loading never shows zero balances. Forbidden and failure states disclose no out-of-scope Budget IDs, titles, lines or amounts.

### 12.2 BUD-UI-02 — Version editor

- Saving the initial Draft creates the Procurement Budget and Version and returns generated references. The fiscal year and currency become immutable.
- The editor accepts only `approval_reference`, `approval_date`, `authorised_total` and one `approval_document_file_id` on Overview.
- The document component permits one current file. Replacing it in Draft removes the old Draft link; submitted evidence is retained in the version snapshot.
- Line create and update accept only title, owner scope, funding source and approved amount. Generated line IDs are not editable.
- Owner-scope choices are Active Organisation Units. Funding-source choices come from the governed catalogue.
- Draft line total and difference are server-calculated after every save response. The client may preview them but cannot submit calculated totals.
- Removing a new unreferenced Draft line is permitted. Removing or changing identity fields on a previously Active line is rejected.
- **Submit for review** reloads the Draft under a version lock, applies all readiness rules and changes status only if the complete transaction passes.
- Failed readiness returns structured failing rules, keeps the Draft editable and focuses the first failing field or line.

### 12.3 BUD-UI-03 — Budget workspace

- Overview and Budget Lines use positions calculated from the Active Version and funding ledger at the response `as_at` time.
- The selected tab is represented in the URL. Back and forward change the tab without changing the Budget or mounting another page application.
- Active, Superseded and Closed versions are read-only.
- Budget Lines returns only stored identity values and derived positions. It infers no classification or expenditure data.
- Funding Activity is reverse chronological and server-filtered. Filtering grants no additional access, and the table shows business event summaries only.
- History contains version lifecycle events only; it does not duplicate the funding ledger.
- **Create revision** creates one server-side copy of the Active Version, preserving line IDs and values, and opens its Draft Overview. A second open successor is rejected and the existing Draft route is returned.

### 12.4 BUD-UI-05 — Budget Line detail

- The route authorises the actor's responsibility and the exact line before returning its title, owner, funding source, positions or reservations.
- A Planning Finance task passes a line ID only. Budget independently authorises the actor and never trusts Planning route visibility as Budget authority.
- The page uses the current live position; it does not freeze to the Finance task snapshot.
- Before confirmation, the page may show no active reservations even though the Planning task displays a proposed amount.
- After confirmation, active reservations show reservation ID, Plan Item reference, original amount, remaining amount and status, read-only.
- **View Plan Item** uses a server-returned authorised Planning URL. The Budget client does not build a route from a guessed naming rule.
- Opening or closing the page creates no check, reservation, decision or ledger event.

### 12.5 BUD-UI-04 — Approval task

- Direct task routes require an Active Budget Approver assignment. A read-only user is denied rather than shown disabled workflow controls.
- All four tabs always read the submitted `budget_version_id`; no tab substitutes the current Active Version.
- Overview returns submitted version identity, approval evidence, submitter authority and readiness results.
- Budget Lines returns the complete submitted line set and current floors calculated at task-read time.
- Changes is calculated server-side against `based_on_budget_version_id`. Version 1 returns the explicit initial-baseline state and never invents a predecessor.
- History returns only events for the submitted version, in reverse chronological order.
- The decision footer remains available on every tab; every command carries version ID, expected status and expected record version.
- Return or Approve are available only while status is Submitted for approval. Return opens a dialog containing only **Return reason**, **Cancel** and **Return**, validated server-side.
- Approve reruns evidence, totals, line identity, floor, transfer, responsibility and concurrency checks under transaction locks and activates in the same transaction. There is no separate later activation step.
- A failed live guard leaves the version Submitted for approval and returns the exact failed rule. No line, status, reservation or ledger position changes.
- The Budget Officer who submitted a version cannot approve it, enforced from the version's own submission audit event.

### 12.6 Procurement Planning Finance boundary

- Finance task discovery, routing, sufficient and insufficient compositions, return dialog and planner waiting remain exactly as defined by Procurement Planning.
- Budget services resolve the caller's Active Finance Confirmation Officer assignment, plus the task, source set and amount scope, before returning protected line positions.
- A Planner receives only the neutral Finance result already permitted by Planning and cannot call `reserve_funding` directly.
- **Check funding** changes no Budget or Planning state.
- **Confirm funding** locks and reloads the complete allocation set. It creates every reservation or none.
- If any line is short, Confirm remains unavailable in the Planning UI and a direct command returns `BUDGET_INSUFFICIENT_FUNDS` with the failing allocation and exact shortfall.
- Finance return records its reason in Procurement Planning and creates no Budget reservation or ledger event.
- A repeated successful confirmation returns the same reservation IDs and does not duplicate a ledger event.
- A combined Plan Item may use more than one line. Each allocation keeps its own line and reservation identity; the item is confirmed only as one all-source decision.

### 12.7 Additional page states

- A fiscal year with no Budget shows the no-baseline state and no zero-value funding position.
- An Active Budget with no funding events shows **No funding activity has been recorded for this budget.** and no Add action.
- A filter with no matching events provides **Clear filters**.
- Forbidden responses disclose no record names, counts, amounts or task details.

---

## 13. Error contract

| Code | Message intent and effect |
|---|---|
| `BUDGET_RESPONSIBILITY_REQUIRED` | You are not assigned the responsibility required for this action. No protected data is returned. |
| `BUDGET_CONFIG_MISSING` | A referenced organisation unit, financial year, currency or funding source is unavailable. The operation fails closed. |
| `BUDGET_ALREADY_EXISTS` | This financial year already has a procurement budget. Return its authorised route; create nothing. |
| `BUDGET_INVALID_STATE` | The command is not valid for the current server status. Current status is returned. |
| `BUDGET_NOT_READY` | Submission or approval readiness failed. Structured failing rule IDs are returned. |
| `BUDGET_APPROVAL_EVIDENCE_REQUIRED` | Approval reference, date, document or authorised total is absent or invalid. |
| `BUDGET_TOTAL_MISMATCH` | Budget Line total does not equal the authorised total. No status changes. |
| `BUDGET_LINE_NOT_ELIGIBLE` | The line is missing, inactive or incompatible with the allocation's owner scope or funding source. |
| `BUDGET_LINE_IDENTITY_IMMUTABLE` | A successor attempted to change title, owner scope or funding source on an existing Active line. |
| `BUDGET_CONTEXT_NOT_FOUND` | No applicable Active procurement budget exists for that financial year. No line is selected. |
| `BUDGET_FINANCE_TASK_DENIED` | The caller does not hold the live Finance task responsibility. No protected position is returned. |
| `BUDGET_CHECK_STALE` | The line, allocation set or task changed after Check Funding. No reservation is created. |
| `BUDGET_INSUFFICIENT_FUNDS` | One or more allocations lack full availability. Per-line shortfalls are returned; no reservation is created. |
| `BUDGET_RESERVATION_CONFLICT` | The allocation already has a different effective reservation or correlation. No duplicate is created. |
| `BUDGET_REVISION_FLOOR_BREACH` | A proposed line amount is below current Reserved plus Committed. Approval is blocked. |
| `BUDGET_TRANSFER_UNBALANCED` | Transfer increases and decreases do not balance. Submission or approval is blocked. |
| `BUDGET_CONVERSION_EXCEEDS_REMAINDER` | Contract conversion exceeds the reservation remainder. No commitment changes. |
| `BUDGET_COMMITMENT_INCREASE_UNFUNDED` | A proposed commitment increase lacks available funds. No adjustment occurs. |
| `BUDGET_CLOSED` | The budget is closed and cannot accept a new reservation. |
| `BUDGET_STALE_WRITE` | The expected record version is stale. No newer data is overwritten. |
| `BUDGET_DOWNSTREAM_FORBIDDEN` | A downstream caller attempted an unsupported Draft read or direct mutation. |

`BUDGET_SCOPE_REQUIRED`, `BUDGET_PERMISSION_DENIED` and `BUDGET_CONTEXT_AMBIGUOUS` are removed: the first two named a scope and a capability that no longer exist, and the third is unreachable now that one fiscal year has at most one Budget. Message conventions are in KT-STD-001 §11.

---

## 14. Audit and historical integrity

Append-only events: Budget and successor-version creation; Draft approval-detail and line change sets; submit, return, approve, activate, supersede and close; Check Funding outcome without balance mutation; reservation creation or idempotent reuse; revalidation, release, conversion and commitment adjustment; responsibility, segregation, floor and concurrency denial; and downstream lineage reads.

Each event records actor or calling service, business role, the exercised responsibility assignment ID, fiscal year, relevant IDs, action, timestamp, before and after status or line position, required decision reason, correlation ID and calling module. No event records a Procuring Entity or a capability string.

Active, Superseded and Closed versions are immutable. Funding Ledger events cannot be edited or deleted. Downstream reservation and commitment identities remain resolvable after a successor activates or the fiscal year closes.

---

## 15. Deterministic seed contract

Site configuration, Organisation Units, base actors and Fiscal Years come from KT-STD-001 §8. Execution rules come from KT-STD-001 §8.6.

### 15.1 Required additions to the shared fixture register

These actors and instants shall be added to KT-STD-001 §8.3 and §8.5 and are used throughout this document:

| Display name | Login identifier | Responsibility | Scope |
|---|---|---|---|
| Josphat Mwangi | `josphat.mwangi@moh.example.test` | Budget Officer, and separately Finance Confirmation Officer | Site-wide |
| Beatrice Kamau | `beatrice.kamau@moh.example.test` | Budget Approver | Site-wide |

Naomi Chebet (Auditor) is added by STR-CHG-001 v1.6 §14.1 and reused here. Samuel Otieno, already in the register with an expired assignment, is the Forbidden fixture actor.

KT-STD-001 §8.5 shall gain: **Budget journeys — 1 Oct 2026 through 16 Mar 2027, EAT.** The span is deliberate: registration precedes reservation, which precedes revision.

### 15.2 Configuration prerequisites

The seed resolves these and fails with `BUDGET_CONFIG_MISSING` if any is absent: ERPNext Fiscal Year **2027-2028**; currency **KES**; Organisation Units `OU-MOH-DHI` Digital Health and `OU-MOH-HRMD` HR Management and Development; funding source **Government of Kenya**.

The seed creates or chooses no organisation unit, fiscal year, currency or funding-source value.

### 15.3 Active baseline

| Field | Exact seed value |
|---|---|
| Budget ID | `MOH-BUD-2027-001` |
| Fiscal Year | `2027-2028` |
| Currency | `KES` |
| Version ID | `MOH-BUD-2027-001-V1` |
| Version | 1 |
| Status | Active |
| Approval reference | `MOH-FIN-BUD-2027-01 (Demo)` |
| Approval date | 30 Sep 2026 |
| Approval document | `MOH Approved Procurement Budget 2027-28 (Demo).pdf` |
| Authorised total | KES 160,000,000 |

Exact lines:

| Budget Line | Title | Owner scope | Funding source | Approved amount |
|---|---|---|---|---:|
| `MOH-BL-DHI-2027` | Digital health infrastructure programme | Digital Health | Government of Kenya | KES 100,000,000 |
| `MOH-BL-HWD-2027` | Digital health workforce development | HR Management and Development | Government of Kenya | KES 60,000,000 |

Exact lifecycle authority:

| Event | Actor | Date and time |
|---|---|---|
| Submitted for review | Josphat Mwangi | 1 Oct 2026, 16:20 EAT |
| Approved and activated | Beatrice Kamau | 3 Oct 2026, 11:15 EAT |

### 15.4 Integrated Planning reservation

| Record | Exact value |
|---|---|
| Finance task | `FNT-MOH-2027-021-001` |
| Finance decision | `FND-MOH-2027-021-001` |
| Plan Item | `PPI-MOH-2027-021` — National digital health infrastructure upgrade |
| Plan source allocation | `PSA-MOH-2027-021-001` |
| Budget Line | `MOH-BL-DHI-2027` |
| Reservation | `RSV-MOH-2027-021-001` |
| Reservation amount | KES 80,000,000 |
| Confirmed by | Josphat Mwangi |
| Confirmed | 4 Dec 2026, 10:00 EAT |
| Reservation status | Active |

Resulting default position:

| Budget Line | Approved | Reserved | Committed | Available |
|---|---:|---:|---:|---:|
| MOH-BL-DHI-2027 | KES 100,000,000 | KES 80,000,000 | KES 0 | KES 20,000,000 |
| MOH-BL-HWD-2027 | KES 60,000,000 | KES 0 | KES 0 | KES 60,000,000 |
| Total | KES 160,000,000 | KES 80,000,000 | KES 0 | KES 80,000,000 |

### 15.5 Isolated Finance and commitment profiles

These reset to the named precondition and do not coexist with the default integrated reservation.

| Profile | Exact precondition and expected result |
|---|---|
| `BUD-SC-FIN-SINGLE` | DHI approved and available KES 100m; allocation KES 80m; confirmation creates one KES 80m reservation leaving KES 20m available. |
| `BUD-SC-FIN-COMBINED` | DHI available KES 100m and HWD available KES 60m; allocations KES 72m and KES 48m; one command creates both reservations leaving KES 28m and KES 12m. |
| `BUD-SC-FIN-SHORT` | DHI approved KES 100m, reserved KES 30m, available KES 70m; required KES 80m; result is KES 10m short and no new reservation. |
| `BUD-SC-CONVERT-PARTIAL` | DHI reservation KES 80m; convert KES 60m to one commitment; result KES 20m remaining, KES 60m committed, KES 20m available. |
| `BUD-SC-DUPLICATE-CORRELATION` | Repeat the successful single-source command with the same correlation; return the same reservation and one effective ledger event. |

### 15.6 Artboard-only successor Version 2

The revision shown in BUD-DES-08 through BUD-DES-15 is an isolated fixture, not part of the default Active baseline. Under KT-STD-001 §8.7 it is declared here so a seed-versus-artboard comparison reports no false mismatch.

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
| Successor created | 15 Mar 2027, 13:10 EAT · Josphat Mwangi |
| Draft saved | 15 Mar 2027, 15:55 EAT · Josphat Mwangi |
| Submitted for review | 15 Mar 2027, 16:20 EAT · Josphat Mwangi |

The DHI floor is KES 80,000,000 from the default reservation, so the proposed KES 90,000,000 remains valid with KES 10,000,000 headroom. A separate isolated copy is decided twice — once returned, once approved — to exercise both outcomes; the version is never left mid-transition between runs.

There is no second seeded budget. The v1.2 County Government of Kisumu baseline and its actors are removed with the multi-PE model.

### 15.7 Additional seed rules

- Upsert by exact stable identifiers; create no duplicates.
- Validate Budget and lines through the same domain rules used by commands.
- Seed lifecycle and Finance events use the named responsibility holders, never Administrator.
- Fail loudly on missing configuration, invalid total, duplicate Active version or line floor breach.
- Seed no Strategy reference, cost centre, expenditure, forecast, note or generic evidence field.
- Isolated profiles are created and removed by their tests and do not contaminate the default integrated seed.

---

## 16. Acceptance contract

| ID | Acceptance result |
|---|---|
| BUD-AC-001 | The module installs and migrates cleanly on a site with ERPNext installed; no DocType name collides with an ERPNext DocType. |
| BUD-AC-002 | No executable metadata, route, service, field, seed or active test contains Allocation as a separate object, Budget Value Treatment, PVO or Value Commitment. |
| BUD-AC-003 | A Budget Officer can register one Draft for a fiscal year and receives generated Budget, Version and line references. |
| BUD-AC-004 | A user without an Active Budget assignment — including Administrator and System Manager — cannot create, submit, return, approve, close or confirm Finance. |
| BUD-AC-005 | The only editable initial fields are external approval reference, approval date, authorised total and one approval document. |
| BUD-AC-006 | A line accepts only title, owner scope, funding source and approved amount. |
| BUD-AC-007 | Submission is blocked unless approval evidence is complete and the line total equals the authorised total. |
| BUD-AC-008 | Only one Procurement Budget and one Active Version exist per fiscal year, and the guard holds when the command layer is bypassed. |
| BUD-AC-009 | Entity-wide and unit-scoped lines are offered to a Need according to BUD-BR-007, and owner scope is never used as a user-permission check. |
| BUD-AC-010 | An allocation whose funding source differs from the line's is rejected. |
| BUD-AC-011 | No Procurement Planning event creates a reservation. A complete plan cycle from Plan Item formation through funding confirmation, adoption, statutory approval and publication leaves every Budget balance byte-identical. |
| BUD-AC-011a | `check_plan_affordability` returns per-line approved amount, planned total, positions and both verdicts, writes nothing, issues no token and produces no ledger event. |
| BUD-AC-011b | A planned total exceeding a line's approved amount returns the within-approved verdict as failed with the exact excess; a planned total exceeding currently available but within approved returns within-approved as passed. |
| BUD-AC-011c | Reservation is created only by a Procurement Requisition drawdown, never by a Planning command, and a Planning caller attempting `reserve_funding` is rejected. |
| BUD-AC-012 | Check Funding writes nothing and returns exact per-allocation positions. |
| BUD-AC-013 | A combined Plan Item confirms every allocation in one transaction or none. |
| BUD-AC-014 | An insufficient allocation returns the exact shortfall and creates no reservation. |
| BUD-AC-015 | Repeating a confirmation with the same correlation returns the same reservations and one effective ledger event. |
| BUD-AC-016 | Concurrent confirmations cannot oversubscribe a line, and no position becomes negative. |
| BUD-AC-017 | Partial conversion leaves the correct remainder reserved and the correct amount committed. |
| BUD-AC-018 | Commitment adjustment, release and cancellation are idempotent by correlation ID. |
| BUD-AC-019 | `Needs Attention` retains the reserved amount and blocks downstream progression without releasing funds. |
| BUD-AC-020 | Every position in the seed matches §15.4 exactly. |
| BUD-AC-021 | A successor cannot reduce a line below Reserved plus Committed. |
| BUD-AC-022 | A Transfer successor with unbalanced increases and decreases is blocked at submission and approval. |
| BUD-AC-023 | Approving a successor atomically activates it and supersedes the prior Active version, preserving all identities. |
| BUD-AC-024 | An existing line's title, owner scope or funding source cannot change in a successor. |
| BUD-AC-025 | The submitting Budget Officer cannot approve the same version, enforced from the submission audit event. |
| BUD-AC-026 | The seed is deterministic and a second run produces no change. |
| BUD-AC-027 | A missing ERPNext Fiscal Year, organisation unit, currency or funding source fails seed execution without creating a fallback record. |
| BUD-AC-028 | Planning calls only the documented contracts; no Planning controller is imported into Budget or vice versa. |
| BUD-AC-029 | Downstream direct-table mutation and Draft reads are rejected. |
| BUD-AC-030 | The five routes render without console error and match their approved static designs. |
| BUD-AC-031 | Loading, no-baseline, forbidden and server-error states disclose no false or unauthorised funding data. |
| BUD-AC-032 | The Frappe header and breadcrumb are reused and not duplicated inside the Vue page; no Procuring Entity or context selector appears on any Budget screen. |
| BUD-AC-033 | Closing after the fiscal year blocks new reservations while preserving all history and lineage. |
| BUD-AC-034 | No executable metadata, permission, route, service, seed or active test refers to Budget Reviewer, Budget Activation Authority, Budget Viewer as a workflow role, or the removed `In Review` and `Awaiting Activation` statuses. |
| BUD-AC-035 | Every Budget write is authorised through an Active `User Responsibility Assignment` resolved by the registered permission hooks. No Frappe User Permission, capability string, Fiscal Year grant or parallel permission lookup participates. |
| BUD-AC-036 | No `procuring_entity_id`, KenTender `FinancialYear`, `cost_center` or ERPNext accounting reference exists in Budget schema, services, seeds, fixtures or tests. |
| BUD-AC-037 | Budget Officer, Budget Approver and Finance Confirmation Officer appear in the business-role registry with `scope_type = Site-wide`, and no Budget command performs a user-scope organisation-unit or fiscal-year check. |
| BUD-AC-038 | ERPNext accounting and its own `Budget` and `Cost Center` records remain fully functional and untouched after this module installs. |

### 16.1 Minimum automated coverage

| Rule group | Required automated coverage |
|---|---|
| Responsibility and access | BUD-BR-001; BUD-AC-003–004, 035, 037 |
| Naming and separation | BUD-BR-026; BUD-AC-001, 036, 038 |
| Baseline and line domain | BUD-BR-002–008, 019–020, 025; BUD-AC-005–010, 024 |
| Finance and arithmetic | BUD-BR-009–016; BUD-AC-011–020 |
| Successor and closure | BUD-BR-017–023; BUD-AC-021–023, 025, 033 |
| Cross-module boundary | BUD-BR-024; BUD-AC-028–029 |
| Seeds | BUD-AC-026–027 |
| UI | BUD-AC-030–032, 034 |

---

## 17. Implementation and test constraints

The implementation baseline is KT-STD-001 §4; the verification protocol is KT-STD-001 §5; release evidence is KT-STD-001 §6.

### 17.1 Additional implementation rules

- Rename the DocTypes to `Procurement Budget`, `Procurement Budget Version`, `Procurement Budget Line` and `Procurement Budget Line Version`, with every route, service, fixture, label, index and test. Verify on a site with ERPNext installed that no name collides.
- Drop `procuring_entity_id` with every dependent parameter, filter, index, fixture and test. Rename `financial_year_id` to `fiscal_year` and repoint it at the ERPNext `Fiscal Year`.
- Add the database-level partial unique index or equivalent guard for BUD-BR-002.
- Register Budget Officer, Budget Approver and Finance Confirmation Officer with `scope_type = Site-wide`. Remove every capability string, custom assignment lookup and Frappe User Permission read from Budget code. The no-self-approval check reads the version's submission audit event.
- Register Budget DocTypes in `kentender_scope_map` per AUTH-ADR-001 v1.6 §5.3, through both hooks, so direct-route access is covered.
- Keep `owner_org_unit_id` on the line version and its BUD-BR-007 eligibility logic. Do not move it into a permission path and do not register it as a scope field.
- Add no ERPNext accounting import, `Cost Center` link or reconciliation job. A static scan shall prove no Budget module imports from `erpnext.accounts`.
- Delete the separate Allocation, treatment, Funding Exception and expenditure artifacts. Preserve no aliases or compatibility response fields.
- Remove the `review_budget_version` and `activate_budget_version` pair; `approve_budget_version` performs the full recheck-and-activate transaction in one call.
- Existing Budget Activation Authority holders may receive a Budget Approver assignment during migration. Budget Reviewer holders are not promoted automatically.
- Where an artboard is marked retired (BUD-DES-12, BUD-DES-13A), do not port it.
- Integrate Planning through the logical service contracts only. Preserve the existing Planning Finance UI; implement only the line route needed by **Open Budget & Funding**.

### 17.2 Additional minimum coverage

1. Install and migrate on a bench with ERPNext and HRMS present; assert no DocType name collision and that ERPNext `Budget` and `Cost Center` still function.
2. Budget write attempted with no assignment, with an expired assignment and with a Scheduled assignment.
3. Administrator and System Manager technical read succeeds; business mutation is denied.
4. Direct-route access to a Budget, line or task excluded from the actor's register.
5. One-Budget-per-fiscal-year guard under a direct-SQL insert bypassing the command layer.
6. Concurrent reserve and concurrent activation against isolated fixtures.
7. All five §15.5 profiles.
8. Successor floor breach, transfer imbalance and line identity immutability.
9. No-self-approval enforced from the submission audit event when one user holds both roles.
10. Owner-scope eligibility proving BUD-BR-007 filters lines without acting as a permission check.
11. Repository scan proving `procuring_entity_id`, `FinancialYear`, `cost_center`, `erpnext.accounts`, `BUDGET_SCOPE_REQUIRED` and `BUDGET_PERMISSION_DENIED` are absent.
12. Browser journeys: Budget Officer registers a baseline and submits; Budget Approver inspects four tabs and returns in one run, approves in another; a read-only actor opens an Active Budget, its lines, a line detail and Funding Activity; a Finance Confirmation Officer uses the Planning task, opens the line, returns and confirms in separate reset profiles; an actor with no Budget assignment sees the Forbidden state with no disclosure.

### 17.3 Additional release evidence

- Static scan showing no removed concept, expenditure artifact, or leftover Budget Reviewer, Budget Activation Authority, Budget Viewer or `Awaiting Activation` reference.
- Migration succeeds on a copy of real data, including the DocType rename.
- Planning Finance contract tests pass for single, combined, insufficient and duplicate-correlation profiles.
- Contract Management conversion and adjustment contract tests pass before those actions are enabled.
- AUTH contract suite passes, proving no Budget path reintroduces a User Permission read.

---

## 18. Prohibited shortcuts

The universal list is KT-STD-001 §2.3 and §10. Additionally, for this document:

- Do not define a DocType whose name collides with an ERPNext DocType.
- Do not read, write, mirror or reconcile an ERPNext `Budget`, `Cost Center`, account or journal record, and do not import from `erpnext.accounts`.
- Do not add a `cost_center` field or any accounting reference to a Procurement Budget Line.
- Do not reintroduce `procuring_entity_id`, a Fiscal Year permission grant or a capability string.
- Do not use `owner_org_unit_id` as a user-scope or permission check.
- Do not create a Budget Viewer, Budget Reviewer or Budget Activation Authority role, or revive the `In Review` and `Awaiting Activation` statuses under another label.
- Do not add a separate Allocation, Budget Value Treatment, PVO, Value Commitment, Funding Exception or expenditure object under another label.
- Do not add a Strategy field on a Budget or line.
- Do not create a Budget-owned Finance task, decision, queue, sufficient or insufficient form, or planner-waiting screen.
- Do not create a reservation at any Procurement Planning event. Reservation begins at Procurement Requisition.
- Do not let `check_plan_affordability` write, lock, issue a token or produce a ledger event.
- Do not make the within-currently-available verdict blocking.
- Do not permit partial all-source confirmation or silent line substitution.
- Do not add actual expenditure, outstanding commitment, forecast, utilisation score or an `Unavailable` placeholder.
- Do not add an editable Budget title, classification, separate purpose, generic description, source type, effective date, authority name, contact, note, justification or miscellaneous attachment.
- Do not allow downstream raw SQL or ORM reads of Budget tables.
- Do not allow client-only permission, total, floor, availability or lifecycle enforcement.
- Do not permit direct edits of Active, Superseded or Closed data.
- Do not rename the existing Budget or line identifiers.

---

## 19. Traceability and precedence

1. **KT-STD-001 v1.1** for document structure, design closed-input rules, the artboard shell, the shared fixture register, common page behaviour, the verification protocol, release evidence, seed conventions, universal prohibitions and error conventions.
2. **AUTH-ADR-001 v1.6** for business authority, the role registry, responsibility assignment and the registered permission hooks.
3. **CFG-CHG-002 v0.6** for the site Procuring Entity, the ERPNext Fiscal Year surface, Organisation Unit records and the funding-source catalogue.
4. **This document** for the Procurement Budget, its versions, lines, reservations, commitments, funding ledger and read contracts.
5. **Procurement Planning** for the Finance task, decision and UI, per `PLN-FR-001`, `PLN-SDC-001` and `PLN-STC-001`.

Budget stores no Strategy field. The selected Strategic Objective and its snapshot remain governed by STR-CHG-001 v1.6 and Procurement Planning.

This document reconciles and supersedes `BUD-CHG-001` v1.0, v1.1 and v1.2 and `01_Budget_and_Funding_MVP1_Requirements.md`. Where an earlier item is not retained here, it is outside Budget & Funding scope.

Documents requiring a matching correction:

| Document | Required correction |
|---|---|
| KT-STD-001 | Add the two Budget actors and the Budget fixture instant in §15.1 to §8.3 and §8.5. |
| CFG-CHG-002 | **The funding-source catalogue has no owner.** v0.6 §3 governs units of measure through ERPNext `UOM` but does not name funding sources, which this module requires. Assign it — as a small governed catalogue or an enabled subset of an existing ERPNext record — and add it to the System setup surface. |
| PLN-CHG-001 v1.7 | Aligned. One plan-level funding confirmation, no reservation at planning, `check_plan_affordability` consumed at plan submission, and no Procuring Entity argument on any contract. Procurement Budget Line identifiers are unchanged. |
| Procurement Requisitions change unit | Becomes the caller of `check_funding` and `reserve_funding`. The contracts are unchanged; the module must supply the Plan Item, drawn allocations and a correlation ID as in §8.2A. **Budget cannot be completed until that change unit exists**, because after this version nothing else reserves funds. |
| Contract Management change unit | Conversion and adjustment contracts are unchanged; the calling principal is a service account, not a business role. |

---

## 20. Approval effect

Approved 3 September 2026. BUD-CHG-001 v1.4 supersedes v1.3 and all earlier versions in full and becomes the only Budget & Funding document to consult.

This approval authorises, in addition to everything authorised at v1.3: the move of funding reservation from Procurement Planning to Procurement Requisition; the `check_plan_affordability` contract and its blocking and advisory verdicts; and plan-level rather than per-item funding confirmation. It further authorises: the DocType rename to the `Procurement Budget` family; removal of `procuring_entity_id`; adoption of the ERPNext `Fiscal Year`; registration of Budget Officer, Budget Approver and Finance Confirmation Officer as site-wide business roles resolved through the AUTH-ADR-001 v1.6 permission hooks; removal of the Budget Viewer role, every capability string and every Fiscal Year permission grant; full separation from ERPNext accounting with no Cost Center reference; retention of `owner_org_unit_id` as a record-eligibility rule; removal of the Kisumu isolation baseline, its actors and every cross-PE isolation test; adoption of the KT-STD-001 shared fixture register; the corrected artboards in §11; and the acceptance contract in §16.

Implementers shall not retain v1.2's `Budget` DocType name, its PE or Fiscal Year scope dimensions, its capability-based authorization, its Budget Viewer role, its second Procuring Entity seed, or any Procuring Entity row or context selector on a Budget screen.
