# BUD-CHG-001 — Clean Budget & Funding

| Control | Value |
|---|---|
| Document ID | BUD-CHG-001 |
| Version | 1.9 |
| Date | 13 September 2026 |
| Status | **Consolidated approved requirements** |
| Approval basis | Approved BUD v1.8 and Project Owner approval of BUD Usability Amendment v0.1, BUD-UX-001–014, on 13 September 2026, with direction to incorporate into the full document. |
| Supersedes | v1.8 and earlier Budget & Funding implementation specifications in full. |
| Change type | Complete successor incorporating fourteen approved usability changes, all-actor journeys, readable financial positions and decisions, explicit submission/recovery and closure interaction, 98 acceptance criteria and a 44-row full change register. |
| Module | Budget & Funding |
| Standards | KT-STD-001 v1.4; AUTH-ADR-001 v1.7; approved CFG v0.10. Current owner boundaries and remaining evidence in §19. |
| Implementation posture | Correction in place; no compatibility layer, extra approval stage or accounting integration. |

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
| Reservations created at Procurement Planning, one per Plan source allocation, before the Annual Plan could be submitted | **Move to Procurement Requisition.** A ministry plan runs to hundreds of items; creating a reservation for each at planning locked the whole budget from the start of the planning cycle and made every plan revision a release-and-re-reserve exercise. The statutory budget-alignment basis is tracked in LAW-REG-001 v1.1; placing the operational hold at Requisition authorisation is the agreed product control, not a claim that the statute prescribes this software event. |
| No aggregate affordability contract | **Add `check_plan_affordability`.** Non-mutating; returns per-line approved amount, planned total, current positions and two verdicts. Within-approved blocks plan submission; within-currently-available is advisory. |
| `check_funding` and `reserve_funding` called by Procurement Planning | **Called by Procurement Requisition.** The contracts, their all-or-none semantics, idempotency and ledger effects are unchanged; only the caller and the moment change. |
| Finance Confirmation Officer confirming per Plan Item | **Reviews the whole Plan financial basis**, with at most one open Finance review per Plan Version, retained completed reviews and Active reassessment under PLN-CHG-001 v1.18 §5.3. The role, its scope and its registry entry are unchanged. |

New in v1.3:

| Earlier item | Disposition in v1.3 |
|---|---|
| DocType named `Budget` | **Rename to `Procurement Budget`.** ERPNext ships its own `Budget` DocType in the Accounts module, set against a Cost Center or Project for a Fiscal Year with Stop, Warn and Ignore control actions. Frappe DocType names are globally unique per site, so with ERPNext installed the existing name will fail at install or migrate. `BudgetVersion`, `BudgetLine` and `BudgetLineVersion` are renamed to match. |
| Any relationship between a Procurement Budget Line and an ERPNext Cost Center | **None.** Fully separate. No `cost_center` field, no reconciliation link, no derived value. The two systems control the same money for different purposes and are not integrated in MVP 1. |
| `procuring_entity_id` on `Budget` | **Remove.** One site is one Procuring Entity. BUD-BR-002 becomes one Procurement Budget per Fiscal Year. |
| `financial_year_id` referencing a KenTender `FinancialYear` | Replace with `fiscal_year`, referencing the ERPNext `Fiscal Year` governed by CFG-CHG-002 v0.10 §4.2. |
| Assignments scoped by PE, FY, organisation unit, capability and effective dates | **Remove PE, FY and capability.** Business authority is a role-bound `User Responsibility Assignment` under AUTH-ADR-001 v1.7, and Fiscal Year is never a user-permission dimension. One Budget Officer assignment works across every year; eligibility comes from the record's own fiscal year and version status. |
| "Capability" as the permission primitive throughout §7, §8.2, §12.5, §12.6 and §14 | **Remove.** Registered business roles replace every capability string. |
| `Budget Viewer` workflow role | **Remove.** Read access is produced by the registered permission hooks acting on the actor's assignments, exactly as Strategy Viewer was removed in STR-CHG-001 v1.7. |
| `owner_org_unit_id` on the line version | **Retain unchanged.** It governs which lines a Need may draw on — record eligibility, not user scope. These Budget roles are site-wide; AUTH may use Organisation Unit scope for other modules. Budget line ownership never grants or narrows a user's Budget responsibility. The label "PE-wide" becomes **Entity-wide**. |
| County Government of Kisumu (`PE-CGK`) isolation baseline, its three actors and every cross-PE isolation test | **Remove entirely.** Creating a second Procuring Entity is structurally impossible under CFG-AC-003, so the seed would fail unconditionally. |
| Bespoke fixture cast (`moh.budget.officer@…`, `bud.viewer.moh@…`, and the rest) | Replace with the KT-STD-001 §8.3 shared register, extended by the Budget actors in §15.1. |
| PE row in every artboard context strip and identity card | **Remove.** The **Financial Year** row is retained where it is the record's own attribute and replaced by a changeable year filter on the workspace. |
| "the existing KenTender PE/FY selector" in §11.1, §11.18 and §12.1 | **Remove.** The component no longer exists. |
| Restated closed-input rules, common page states, TDD protocol, release evidence and product-wide prohibitions | **Remove.** Cite KT-STD-001. |
| Citations of CFG-CHG-002 v0.3 and STR-CHG-001 v1.5 | Update to CFG-CHG-002 v0.6 and STR-CHG-001 v1.6. |

**Identifiers are deliberately unchanged.** `MOH-BUD-2027-001`, `MOH-BL-DHI-2027` and the rest keep their existing prefixes. They are opaque stable strings referenced by approved Procurement Planning contracts and seed data; the embedded `MOH` is not a permission dimension, a source of truth or a scope check. Renaming them would break downstream approved documents for no functional gain. Do not "tidy" them.

---

## 2. Purpose and exclusions

Budget & Funding records the externally approved procurement allocation for each fiscal year, preserves immutable approved Versions and line identities, supplies affordability and complete annual-budget evidence, and protects availability through Requisition-authorisation reservations and downstream commitments. It provides controlled successor versions and read-only funding lineage.

It does not enact or appropriate a budget, release cash, maintain accounting ledgers, process invoices or payments, or integrate with ERPNext accounting. Its own append-only **funding-control ledger** records reservations and commitments; it is not an accounting ledger or evidence of payment. Shared native Company currency and Fiscal Year metadata are permitted through owner contracts; ERPNext `Budget`, `Cost Center`, accounts and journals are never read, mirrored or reconciled.

No separate Allocation object, Strategy field, procurement method/schedule/lot authoring, actual expenditure, forecasts, utilisation dashboard, manual reservation/commitment entry, Budget-owned Finance task or duplicate shell is introduced. There are no generic notes, descriptions, justification, contacts, miscellaneous attachments or editable technical identifiers. The external approval reference, date and one document pass KT-STD-001 §7's purpose gate because they substantiate the registered allocation.

## 3. Fixed external constraints and ownership

KenTender records the allocation approved through the external public-budget process. Budget approval verifies and activates that record for KenTender control; it does not replace external approval. No new assertion about current law is established by this amendment; LAW-REG-001 v1.1 governs legal verification and its remaining prerequisites.

| Information or decision | Owner | Budget relationship |
|---|---|---|
| Site entity, native Company association, Fiscal Year, Organisation Units, funding-source catalogue and UOM adapter | CFG-CHG-002 v0.10 | Resolve authoritative IDs and eligibility; no guessed Company mapping, fallback record or parallel catalogue. |
| Business authority | AUTH-ADR-001 v1.7 | Registered hooks and live responsibility assignments; no parallel permission mechanism. |
| Budget currency/precision contract | Budget, using verified native metadata mapping | Exact versioned currency-unit representation in §4.8; no accounting amounts or ledger import. |
| ERPNext accounting | ERPNext | No integration or modification by Budget. |
| Strategic Objective and snapshots | Strategy / Planning | No Budget field or write. |
| Accepted departmental requirement | Departmental Needs v1.12 | Six source facts; no Budget Line selection or Money field. Acceptance never reserves. |
| Budget Line selected for a Need-backed or direct departmental source | Procurement Planning | The Planning source entry selects the line; Budget validates exact source-department/funding eligibility. No selection is added to the Need. |
| Plan, items, source allocations, financial basis, Finance review and decision | Planning v1.18 | Read affordability; validate at a decision boundary; store returned evidence. No Planning reservation. |
| Requisition, exact submitted Version, drawdown and authorisation | Requisitions | Calls check/reserve at authorisation; stores one returned reservation per drawdown line in the same transaction. |
| Budget roots, Versions, lines, reservations, commitments and funding-control ledger | Budget | Own their persistence, rules and service contracts. |
| Contract, variation and cancellation | Contract Management | Authenticated conversion/adjustment/release events through Budget. |
| Statutory target applicability, qualifying category and overlap rules | LAW / CFG / Planning | Budget supplies the complete annual denominator, not legal entitlement or the qualifying numerator. |

Owners exchange services and immutable event references. Budget never imports a downstream controller or queries its tables; callers never query or lock Budget tables themselves. The REQ authorisation boundary coordinates Planning drawdown and Budget reservation without moving either owner's persistence into the other module.

---

## 4. Canonical domain model

All identifiers are server-generated. Framework audit fields remain framework-managed.

### 4.1 Procurement Budget

The stable identity of one fiscal year's procurement allocation record.

| Field | Operational purpose and system effect |
|---|---|
| `budget_id` | Immutable generated reference used by routes, services, audit and downstream lineage. Not editable. |
| `fiscal_year` | The ERPNext `Fiscal Year` whose funding period this record governs. Required and immutable after creation. |
| `currency` | Fixes one currency for every line and calculation. Copied from the explicitly configured native Company default at creation and immutable. |
| `currency_basis_reference` | Retains the creation currency/precision evidence in §4.8; system generated, never editable. |

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
| `budget_line_id` | Immutable generated reference used by Planning source allocations, reservations, commitments and routes; Need identity may remain upstream lineage, never a selected Budget field on the Need. |
| `budget_id` | Prevents the line identity from moving to another fiscal year's Budget. |

### 4.4 Procurement Budget Line Version

| Field | Operational purpose and system effect |
|---|---|
| `budget_line_version_id` | Immutable generated reference for review comparison and audit. |
| `budget_version_id` | Binds the values to one immutable version. |
| `budget_line_id` | Preserves downstream funding lineage across approved amount changes. |
| `title` | The funded purpose displayed in selectors, tables and snapshots. Required. No separate purpose or description field. |
| `owner_org_unit_id` | Limits **line eligibility** to one configured Organisation Unit. Empty means Entity-wide. This is a domain rule about which source departments may draw on the line; it is never a user-scope or permission check. |
| `funding_source` | From the governed funding-source catalogue; copied into downstream funding snapshots. Required. |
| `approved_amount` | The allocation ceiling for the line in this version. Required and positive. |

After first activation, `title`, `owner_org_unit_id` and `funding_source` define the stable line identity and cannot change in a successor. A genuinely different purpose, owner scope or funding source requires a new line. A successor may change only the approved amount. Submitted/approved snapshots retain the funding-source ID and its display label as reviewed; a catalogue rename may appear as a separately labelled current catalogue value but cannot rewrite that historical label.

There is no `cost_center` field and no ERPNext accounting reference of any kind.

### 4.5 FundingReservation

| Field | Operational purpose and system effect |
|---|---|
| `reservation_id` | Immutable generated reference returned to Procurement Requisitions and used by downstream lineage. |
| `budget_id` | Fixes the fiscal year funding root. |
| `budget_version_id_at_creation` | Preserves the version under which the reservation was confirmed. |
| `budget_line_id` | Identifies the funded purpose and balance affected. |
| `plan_item_id` | Links the reservation to the governed Plan Item. |
| `plan_source_allocation_id` | Retains the exact Planning allocation drawn; it is not a lifetime-unique reservation key. |
| `requisition_id`, `requisition_version_id` | Stable Requisition and exact immutable submitted Version authorising the draw. |
| `drawdown_id`, `drawdown_line_id` | Exact owning drawdown and line; database uniqueness on the owning authorisation event and drawdown line prevents duplicate creation. |
| `authorisation_event_id` | Immutable owner event coordinated in the authorisation transaction; retained after revocation. |
| `source_organisation_unit_id` | Exact source department validated through Planning/REQ facts; never inferred from the actor. |
| `original_amount` | The exact amount authorised on this REQ drawdown line, which may be less than the original Plan allocation. Required and positive. |
| `remaining_amount` | The unconverted and unreleased hold. Changed only by Budget services. |
| `status` | `Active`, `Partially Converted`, `Converted`, `Released` or `Needs Attention`. |
| `correlation_id` | Binds all reservations in one REQ authorisation; idempotency includes the immutable payload digest, not this string alone. |

There is no `Requested` reservation. A failed check creates no reservation. There is no expiry date, manual authority field, note or attachment.

### 4.6 ProcurementCommitment

| Field | Operational purpose and system effect |
|---|---|
| `commitment_id` | Immutable generated reference used by Contract Management and funding lineage. |
| `reservation_id` | Prevents a commitment from bypassing the confirmed funding lineage. |
| `contract_id` | Identifies the owning downstream contract. Required and unique within the reservation lineage. |
| `current_amount` | The current contractual obligation; affects committed and available positions. Changed only through the adjustment service. |
| `status` | `Active`, `Cancelled` or `Closed`. |

One reservation may convert into more than one commitment. Each conversion is bounded by the locked remaining amount. Original amount = remaining hold + cumulative conversion debits + cumulative reservation-release debits. Commitment decreases/cancellations do not replenish the reservation or erase conversion history. A separately authorised commitment increase consumes additional available funds through `adjust_commitment`; it does not rewrite original reservation amount. A fully consumed hold is `Released` when only released, otherwise `Converted`; the event history distinguishes mixed conversion/release outcomes. `Needs Attention` applies while a positive remaining hold is retained; its typed reason blocks further progression until successful owner revalidation. Contract details, supplier, dates, variations and payments remain in Contract Management.

### 4.7 FundingLedgerEvent

Append-only: event ID and type; Budget, line, reservation and commitment IDs as applicable; Plan allocation, exact REQ Version/drawdown/authorisation event, contract or variation reference; exact Money amount; before and after approved, reserved, committed and available positions; actor or calling service, timestamp and correlation ID; and a typed revalidation failure code where applicable. Users do not create or edit ledger events.

---

### 4.8 Shared types and financial evidence

| Type / representation | Required contract |
|---|---|
| Identifier | Opaque stable string; exact Version IDs are separate from roots and display references. All snapshots preserve both where needed. |
| Money | Exact decimal **currency units**, never binary float or implicit minor units. JSON strings use plain digits and an optional decimal point; no commas, exponent, NaN or Infinity. Non-negative except explicitly signed change projections. Positive where a field requires it. Inputs with more fractional digits than supported are rejected, even if trailing zeroes; valid inputs are canonically emitted at the supported scale. |
| Storage/calculation | At least 18 integral digits plus supported fractional digits. Exact decimal addition/subtraction/comparison throughout persistence, services, fixtures and owner boundaries; no `flt()`, epsilon equality or silent rounding. Overflow fails before mutation. |
| CurrencyBasis | `currency`, `fraction_digits`, `precision_version`, `source_metadata_reference`; immutable retained evidence of the verified owner/native mapping. KES fixture uses 2. No user-editable precision setting is added to Budget. Missing or unsupported precision blocks monetary writes and positive decisions; it is not defaulted. |
| Quantity | Exact positive decimal string and UOM identity/precision from the owning adapter. Budget validates the incoming drawn-value lineage; REQ/Planning own quantity allowance checks. No float conversion or reconstructed value from rounded display prices. |
| Instant / Date | ISO-8601 UTC instant / ISO date; EAT formatting in UI. Server decision time and CFG applicability basis are authoritative. |
| FinancialBasis | Schema `BudgetFinancialBasis.v1`: FY, Budget root/Active Version, CurrencyBasis, sorted unique lines of exact line/version IDs, approved amount, planned total, source funding identity and normalized eligibility facts; read `as_at`. Positions are separately timestamped advisory observations. |
| AnnualBudgetBasis | Schema `AnnualProcurementBudgetBasis.v1`: FY, exact Budget Version and revision context, CurrencyBasis, authorised total, complete line count and line-set digest, applicability context and `as_at`. Includes unused lines. Retained evidence permits exact replay after supersession. |

Budget root retains its creation CurrencyBasis reference. Approved Version and decision snapshots retain the exact precision identity used; catalogue edits never reinterpret saved Money. A changed native default currency does not change an existing Budget. A precision-policy change that would affect existing records requires a separately controlled migration and cross-module reconciliation; do not round or silently adopt it on read.

Canonical basis fingerprint: SHA-256 over UTF-8 JSON with lexicographically ordered object keys, no insignificant whitespace, Money at CurrencyBasis scale, nulls explicit, and line/eligibility arrays sorted by their opaque identities. Include schema, FY, currency/precision, authoritative financial values and eligibility identities/revisions. Exclude read timestamps, available/reserved/committed observations, actor and UI labels. Return exact Budget/line revisions separately even where a semantically unchanged amount can reuse Finance evidence. Planning owns the explicit link between reused evidence and its current basis; Budget never asserts that Finance reviewed different Plan content.

Version IDs and basis digests returned by reads are evidence references, not a reservation token or guarantee that a later decision will pass.

---

### 4.9 User labels and exact financial meaning

| Stored concept | Visible label | Meaning / retained control |
|---|---|---|
| authorised_total on evidence form | Approved allocation | Externally approved total, not an appropriation made by KenTender. |
| approved_amount / sum of approved lines on live view | Registered allocation | Current recorded allocation ceiling in the displayed Budget Version. |
| Reserved | Reserved for requisitions | Remaining unconverted/unreleased holds, including Needs Attention. |
| Committed | Committed to contracts | Current active contractual obligations from owner events; not payments. |
| Available | Available to reserve | Approved minus Reserved minus Committed; not a cash/bank balance. |
| owner_org_unit_id | Available to | Exact source-department eligibility; null means All departments. Not user authority or inferred descendant scope. |
| revision_type | Type of change | Same Supplementary allocation, Reduction, Transfer and Correction enum. |
| Active / Superseded Budget Version | Current / Previous version | Same immutable lifecycle states; exact Version remains visible in supporting detail. |
| Draft with latest Return evidence | Changes requested | Same editable Draft, exact immutable earlier submission attempt retained. |
| Submitted for approval | Awaiting Budget Approver review | Same submitted state; no additional queue/state. |
| Needs Attention reservation | Requires review — funds remain reserved | Same remaining hold and blocked downstream progression until owner revalidation. |
| Reserved + Committed during successor review | Reserved + committed | This amount must remain covered; current live check, not frozen proposed content. |
| proposed approved amount minus protected amount | Available after update / Shortfall | Non-negative projected availability if the guard passes; display exact positive Shortfall when it fails, never negative spendable money. |

These labels do not change source fields, enums, references, event keys, Money scale or historical evidence. Derived display title remains unstored. No separate Allocation object is created by using the word allocation in a user label. Raw correlation IDs, hashes and calculation internals are secondary technical evidence, not business tasks.

## 5. Canonical calculations and invariants

For one line at an `as_at` point:

**Reserved** = sum of `remaining_amount` for reservations in `Active`, `Partially Converted` or `Needs Attention`.
**Committed** = sum of `current_amount` for commitments in `Active`.
**Available** = `approved_amount − Reserved − Committed`.

Budget totals are the sums of the Active Version's line positions. Users never enter calculated totals. Closed/historical projections use the explicit retained Version and funding ledger at the requested instant; they never combine an old approved amount with today's position without labeling the two contexts separately.

| ID | Rule and enforcement |
|---|---|
| BUD-BR-001 | Every user business write requires an Active site-wide `User Responsibility Assignment` for the required role. Registered service writes additionally validate the owner command/event and the initiating actor’s live authority at its decision boundary; a service identity alone grants no financial discretion. No Procuring Entity, Fiscal Year or capability scope check participates. |
| BUD-BR-002 | One Fiscal Year has at most one Procurement Budget and one Active Version. Enforced by a database-level partial unique index or equivalent guard **and** in the activation transaction. Serialization alone is insufficient. |
| BUD-BR-003 | Every line amount and funding event uses the Budget currency. Cross-currency funding is outside MVP 1. |
| BUD-BR-004 | Approval reference, approval date, one approval document and a positive authorised total are required before submission. The approval date cannot be in the future or after activation, and the version line sum shall equal `authorised_total`. |
| BUD-BR-005 | Only Draft versions are editable; Submitted for approval, Active, Superseded and Closed versions are read-only. |
| BUD-BR-006 | Only an Active Version may support a new reservation. |
| BUD-BR-007 | A line is eligible for an allocation only when it is in the resolved Active Version and its owner scope is Entity-wide or exactly matches the explicit `source_organisation_unit_id` of that allocation. Need-backed and direct Planning sources obey the same rule; no descendant expansion is inferred. This is record eligibility, evaluated after the actor's responsibility check, never instead of it. |
| BUD-BR-008 | The allocation's funding source shall equal the line's funding source. Procurement type does not restrict eligibility. |
| BUD-BR-009 | No Procurement Planning event creates a reservation. Need acceptance, DPP submission, DPP validation, Plan Item formation, plan funding confirmation, Annual Plan adoption, statutory approval and publication all leave Budget balances unchanged. Reservation begins only at successful Procurement Requisition authorisation. |
| BUD-BR-010 | A reservation request covers the complete current source-allocation set for the drawing record. All required reservations succeed in one transaction or none is created. |
| BUD-BR-011 | Each authorised REQ drawdown line receives exactly one reservation. A later separately eligible drawdown may reference the same original Planning allocation without reusing its earlier reservation. Planning enforces remaining allowance, stable-item scope lock and one-open-REQ rules. Same idempotency key plus same payload returns the original result; a different payload conflicts. |
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
- Return requires 10–500 characters and preserves an immutable submission-attempt snapshot, exact evidence attachment and decision. Re-editing the same Draft Version creates a new submission attempt; no prior submitted content or decision is overwritten. Decision authority is checked against the submission being decided.
- Approval means "available for KenTender procurement control". It does not approve the public budget, which happens in IFMIS.
- At most one open Draft or Submitted-for-approval successor may exist per Budget.
- A successor is always copied server-side from the current Active Version.
- Closing requires the fiscal year to have ended and no reservation with a remaining amount. Existing commitments remain in the funding-control history and calculation; authorised decreases/cancellations may still reconcile them. Closed budgets cannot support new holds, conversions or obligation increases. Closure never means payment or extinguishment of an obligation.
- Records and ledger events are never deleted after submission.

---

## 7. Roles and permissions

Three Budget business responsibilities exist. All are registered in the AUTH-ADR-001 v1.7 §4.4 registry with `scope_type = Site-wide`.

| Business role | Scope type | Permitted actions |
|---|---|---|
| Budget Officer | Site-wide | Register the initial Draft, create a successor, edit Draft approval details and lines, and submit. |
| Budget Approver | Site-wide | Inspect a submitted version; return it with a reason, or approve and activate it; close a Budget after the fiscal year. |
| Finance Confirmation Officer | Site-wide | Open the current whole-Plan Finance review, confirm or return against its basis, and reassess exact Active Plan content through Planning. At most one review is open per Plan Version; completed reviews remain history. Confirmation creates no reservation and grants no Budget authoring, approval or activation authority. |

Registry properties: none is an `exclusive_office`; all are granted by Administrator or System Manager; Budget Officer and Budget Approver carry `sod_tags` sufficient for the no-self-approval rule.

There is no Budget Viewer role. Read access is produced by the registered permission hooks acting on the actor's assignments. **Auditor** is a registered business role under AUTH-ADR-001 v1.7 §4.4 and confers no Budget mutation. **Procurement Planner** reads eligible lines through contracts and holds no Budget responsibility.

The **REQ service principal** is a registered authenticated caller for `check_funding`, `reserve_funding` and exact pre-consumption revocation release. It supplies the owner-authorised command context; Budget validates it with the immutable REQ/drawdown facts, live initiating authority and the full atomic transaction. It cannot read Draft Budgets or author a Budget Version.

The **contract service principal** is an authenticated service account, not a business role and not a registry entry. It calls `revalidate_reservations`, `release_reservation`, `convert_reservation` and `adjust_commitment` with a downstream event reference and an idempotency key. It cannot create a reservation, edit a version or read a Draft.

Administrator and System Manager receive full technical read under AUTH-ADR-001 v1.7 §8 and no Budget business action. No capability profile, capability string, operational scope assignment, Fiscal Year grant, Frappe User Permission or parallel permission store participates in a Budget authorization path.

---

### 7.1 All-actor journey and read boundary

| Actor | Normal work | Boundary |
|---|---|---|
| Budget Officer | Record approved allocation; continue initial Draft; correct return; update current allocation | Site-wide current assignment; register/edit/submit only. Same submission's submitter cannot approve it even with both roles. |
| Budget Approver | Review initial allocation or changes, inspect exact evidence, approve/activate or return; close after year-end | One decision activates; closure is the existing guarded action, not a new queue or appropriation stage. |
| Finance Confirmation Officer | Whole-Plan Finance review and reassessment in Planning; permitted live Budget Line reading | No Budget Finance screen, authoring/approval power or reservation from confirmation. |
| Procurement Planner | Owner selection of eligible lines for exact departmental sources; permitted positions | Record eligibility does not derive from the Planner's assignments; no Budget mutation. |
| Requisition actors / registered service | Work in REQ; authorisation coordinates exact drawdown reservations | Draft, submission and department approval reserve nothing. Service requires owner-authorised live context. |
| Contract actors / registered service | Owner conversion, adjustment or release; permitted lineage | No manual Budget financial controls; unavailable owner facility is not replaced locally. |
| Auditor | Authorised exact Budget, Version, submission attempt, file and funding history | Read only; historical Version/instant never replaced with current ledger. |
| Administrator / System Manager | All-record technical read/search, including Draft, Submitted and exact approval-shaped routes | No business assignment required for technical read; all mutation needs the actual business authority and checks. |
| Multiple roles / AO or other titles | Actual assigned work together without a role switch | No Budget authority from title alone. External appropriation/approval remains outside this system. |

A technical-reader detail exception under AUTH v1.7 §8 applies equally to BUD-UI-02 and BUD-UI-04. Ordinary neutral/consumer read does not itself grant workflow-task access. Denied pages resolve inline before protected content paints; navigation stays on the selected route. Reader access is enforced by the registered hooks, not by a new Budget Viewer role.

## 8. Procurement Planning and downstream integration

### 8.1 Distinct financial moments

| Moment | Caller / contract | Effect |
|---|---|---|
| Planning preparation and review display | PLN / `check_plan_affordability` | Read-only comparison; no lock, token, financial write or ledger event. |
| Positive Finance or other governed Planning decision needing a current basis | PLN / `validate_plan_affordability_for_decision` | Serialize the Budget basis inside the caller's transaction; no Budget financial record, hold or ledger event. PLN writes its decision only if the same transaction commits. |
| Annual-budget target calculation | PLN / `get_annual_procurement_budget_basis` | Full approved annual denominator with exact Version. No hold and no legal classification decision. |
| REQ authorisation | REQ / `check_funding` then `reserve_funding` | Exact reservation per drawdown line; full authorisation commits or nothing does. |
| Contract conversion/adjustment | Registered Contract service | Changes owned reservation/commitment positions through authenticated events. |

Finance review covers the **whole Plan financial basis**, never one item or one lifetime-only review. Draft basis changes cancel/stale the affected review under PLN v1.18 §5.3. Active reassessment appends current evidence without editing the approved Plan or original Finance statement. Source changes that leave all financial amounts and eligibility facts unchanged can reuse evidence only through PLN's explicit basis-reuse record. Available-funds changes alone do not invalidate affordability evidence.

An Active Plan with stale funding evidence cannot support a new REQ authorisation until Planning's recovery gate passes. Its earlier authorised Requisitions and Budget reservations remain intact. A Budget amendment does not enlarge an already procured Plan Item; new scope follows the separately governed Planning route and cannot be absorbed into a locked proceeding.

### 8.2 Plan affordability

Per-line planned total is compared with that line's approved amount on the applicable Active Budget Version. Excess over approved amount is blocking for positive Finance and formal Planning submission. Excess over currently available amount, while within approved, is **advisory** for Planning; REQ reservation still requires sufficient actual availability.

`check_plan_affordability` reads a coherent committed snapshot, locks nothing, writes nothing, issues no check token and emits no funding ledger event. It returns the FinancialBasis and each line's approved/planned/reserved/committed/available amounts, exact excess/shortfall, both verdicts and observation time. It checks explicit source-OU/funding eligibility; an aggregate alone cannot prove every contributing source eligible. Caller-supplied amounts describe the Plan; they do not replace Budget-owned approved amounts.

### 8.2A Decision-time validation

`validate_plan_affordability_for_decision` is distinct from the display call. It requires the trusted caller transaction context, exact decision/Plan financial-basis context, FY/currency/precision, complete per-line totals and financial eligibility facts, expected Budget and line revisions, and expected annual-basis context when that decision also depends on an annual denominator.

1. Authorize the registered caller and its owner-validated live actor/decision context. Resolve current CFG facts through the owner contract; no raw cross-module table access.
2. Lock or equivalently serialize the applicable Budget root/Active-Version guard and affected authoritative lines in stable ID order. All Budget activation, closure and decision-validation paths use compatible locks. Retain protection until the caller commits or rolls back; a lock released before PLN saves is insufficient.
3. Re-read current Active Version, currency/precision, line identities, amounts and eligibility revisions. Check expected revisions; stale/missing/ineligible basis fails atomically. A changed revision is returned for explicit refresh/reuse evaluation, never silently substituted in the pending positive command.
4. Return the immutable comparison snapshot. If a mandatory annual target is evaluated in the same decision, validate the supplied full annual-basis Version/total/digest against the serialized Budget root too, including unused-line changes. Display reads of the annual basis alone are not a commit guarantee.
5. Commit the Planning decision only in that same valid transaction. Budget creates no reservation, commitment, financial record or funding ledger event. Out-of-process implementations require equivalent proven atomicity; a remote success response plus a later unguarded PLN commit is not sufficient.

A failure returns typed stale, configuration, eligibility, precision or affordability details to the authorized caller; no partial positive decision survives. Ordinary reserved/committed movements remain advisory for Finance but are represented consistently in the returned observation.

### 8.2B Complete annual-budget basis

`get_annual_procurement_budget_basis` resolves the **complete** approved annual procurement budget for FY and declared applicability/revision context. Current mode requires the applicable Active Version. Historical replay requires an explicit retained Version and applicable instant; it must not substitute today's Active Version. No missing-basis result becomes zero.

Return the Budget root/exact Version, fiscal year, CurrencyBasis, authorised total, complete line count/digest, applicability context and `as_at`. Verify exact sum of all that Version's approved lines equals authorised total. No department filter, Plan-used-line filter or UI pagination may narrow the denominator; do not net reservations, commitments or available funds. The provider can return total/digest without disclosing extra row details to a caller lacking that row-read purpose.

Budget supplies the denominator, not reservation-category entitlement, a qualifying numerator, county/overlap interpretation or a production-verification claim. CFG/LAW determine the applicable rule; PLN applies it and freezes both rule and Budget evidence. The fixture denominator is KES 160,000,000, even though the Plan is KES 130,000,000 and may later have only KES 110,000,000 available.

### 8.3 Atomic REQ reservation

REQ supplies its root/exact immutable submitted Version, proposed authorisation-event identity, exact Planning root/Version/item/allocation facts, every drawn line/quantity/value/source OU/funding source, source-set digest and one command idempotency key. Drafting, submission, department approval and return create no reservation.

`check_funding` validates the complete array and aggregates requirements **by Budget Line** before testing availability: two individually affordable rows can together exceed one line. It returns per-drawdown rows, per-line totals/shortfalls and one token binding the full input digest, actor/caller, REQ/Plan/source/line revisions and server expiry. It writes nothing. A token is not authorisation, cannot cover a subset, and cannot bypass revalidation. The implementation must publish and test its bounded token lifetime; expiry returns `BUDGET_CHECK_STALE` without mutation.

`reserve_funding` validates that same token and exact payload in the REQ owner transaction, locks Budget root/affected lines in stable order, rechecks aggregate availability and creates **one reservation per drawdown line**, even when two lines share a Budget Line. It returns a complete drawdown-to-reservation mapping. REQ authorisation, Planning drawdown/scope guard, reservation set, decision, immutable handoff and outbox event commit together or all roll back. Owner APIs implement the shared lock order; no downstream table locks by callers. All callers use the same ordered transaction protocol, documented and concurrency-tested during implementation.

Same key plus identical payload returns the original committed mapping, even if later released; it never recreates a released hold. Same key plus changed payload fails. A unique authorisation-event/drawdown-line constraint prevents a new key duplicating that authorised line. Later draws against remaining original allowance require their own eligible REQ authorisation and lineage. No partial source confirmation, silent line substitution, silent reduction or release-and-reserve retry workaround is permitted.

### 8.4 Later events and boundary protection

| Event | Required effect |
|---|---|
| Material change before REQ authorisation | Recheck submitted owner facts; no reservation yet. |
| Correction of an authorised unconsumed REQ | REQ's governed revocation reverses exact Planning drawdown and releases the exact reservation set atomically; retain prior evidence, then use the owner's corrected successor route. No in-place mutation of authorised facts. |
| Handoff already consumed | No Budget release shortcut for scope change; follow the owning downstream procedure. Planning scope lock does not disappear merely because funding is later released. |
| Contract conversion | Convert at most the remaining hold; preserve exact REQ/source lineage. |
| Contract increase | Revalidate current Active line availability and authorised variation; consume only the increase atomically. |
| Contract decrease/cancellation | Reduce commitment through an idempotent owner event. Release a reservation remainder only when the authenticated event explicitly authorises that release; never automatically recreate a hold. |
| Budget successor activation | Enforce Reserved + Committed floors, retain lineage and expose exact new revision evidence through owner contracts for consumer staleness checks. A monetary floor breach blocks activation; it is not cured by marking reservations Needs Attention. |
| Eligibility revalidation failure | Retain the remaining hold with typed Needs Attention reason and block affected downstream progression; restore status only after successful owner revalidation. |

## 9. Service and command contracts

### 9.1 Read and funding contracts

All amounts use §4.8 Money. Authorized responses provide human `reference` separately from stable IDs, exact version/revision references and typed errors. No service accepts a Procuring Entity or user-FY scope argument. Source OU is a **record-eligibility argument**, not user authority.

| Contract | Required input | Output / effect |
|---|---|---|
| `get_budget_currency_contract` | FY/Budget context, optional exact historical Budget Version | CurrencyBasis and supported Money format; no inferred default or ledger access. Logical provider name to be mapped to the repository in implementation. |
| `resolve_budget_context` | FY | One Active Budget/Version summary and CurrencyBasis, or typed absent/ineligible result. |
| `list_eligible_budget_lines` | FY, **source_organisation_unit_id**, optional funding source, search/paging | Eligible Active rows: ID, human `reference`, title, owner scope, funding source, exact revisions and positions. Entity-wide or exact source OU only; no Draft rows. |
| `get_budget_line_position` | Line ID; current mode or explicit historical Version/instant | Exact authorized identity, approved/reserved/committed/available amounts and `as_at`; historic replay fails typed if not reproducible. Never silently label today's position as historical. |
| `check_plan_affordability` | FY, CurrencyBasis, unique per-line planned totals and complete source-OU/funding eligibility facts | FinancialBasis, both verdicts and observations; §8.2. No lock, token, financial write or ledger event. |
| `validate_plan_affordability_for_decision` | Trusted caller transaction/decision context, same complete financial inputs, expected Budget/line revisions; annual basis expectation where applicable | Serialized immutable comparison or atomic typed failure; §8.2A. No Budget financial record or ledger event. |
| `get_annual_procurement_budget_basis` | FY, applicability date/basis and current/replay mode; exact Version in replay | Complete AnnualBudgetBasis; §8.2B. No department or used-line denominator filtering. |
| `check_funding` | Exact REQ/Plan/drawdown/authorisation context, complete drawn source array and digest, correlation | Non-mutating per-row and per-line results, aggregate shortfalls, one bound expiring token; §8.3. No Finance-task parameter. |
| `reserve_funding` | Owner transaction, check token, exact unchanged payload/expected revisions, idempotency key | Complete drawdown-line/reservation mapping and positions or rollback. |
| `revalidate_reservations` | Exact set, authenticated owner event/type and idempotency key | Current or Needs Attention result and effective state-change ledger evidence; no new reservation. |
| `release_reservation` | Reservation, exact amount, authenticated owner cancellation/revocation event, key | Reduced hold and position; excess/duplicate payload conflicts fail. REQ revocation coordinates the complete set atomically. |
| `convert_reservation` | Reservation, contract, exact amount, authenticated contract event, key | Commitment, updated remainder/position; no amount beyond locked remainder. |
| `adjust_commitment` | Commitment, exact new total, authenticated variation/cancellation event, key | Locked adjustment and effective ledger event; no unfunded increase. |
| `get_funding_lineage` | Authorized Plan allocation, REQ/drawdown, reservation, contract or commitment reference | Stable and exact-version lineage, owner events and authorized routes; no guessed links or Draft Budget disclosure. |

Eligible-line listing verifies source OU after caller authorization. Missing/unknown source OU fails even for Entity-wide candidates because source lineage still requires a real source department. Optional funding-source filter affects selection; a decision validates the exact source identity of every allocation. Disabling a catalogue entry removes new-selection eligibility and triggers current-use validation; historical read-by-ID and frozen labels remain available. No catalogue rename rewrites an approved Budget line or a downstream snapshot. A genuinely changed line owner/source requires a new line under §5.

Draft Budget save/submit/approve validate active selectable configuration through CFG's owner contract; decisions revalidate owner facts under `ValidateProcurementConfigurationForDecision` where applicable. Generic open/read actions perform no check-and-reserve side effects.

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

### 9.3 User-action mapping and save/submission contract

| User action | Existing command / scope |
|---|---|
| Save and add budget lines | save_budget_version_draft creates one Budget and initial Draft, then opens its lines. |
| Save changes — Approval details | save_budget_version_draft saves only the permitted Draft evidence/details. |
| Save changes — Budget lines | save_budget_lines_draft saves one validated line change set. |
| Submit for review | Save changed valid scopes as below, then submit_budget_version on the exact confirmed Version. |
| Update registered allocation | create_budget_successor_version copies the exact Active Version; at most one open successor. |
| Return for correction | return_budget_version, preserving the submitted attempt/document and 10–500 character reason. |
| Approve registered allocation / Approve allocation update | approve_budget_version; atomic decision/activation and predecessor supersession. |
| Close budget | close_budget; existing year-end, remaining-hold and authority guards. |

First creation resolves an explicit native Fiscal Year with no existing Budget and a verified CurrencyBasis. The registration form requires its four existing approval details (valid reference, non-future approval date, positive approved allocation and exactly one successfully uploaded/linked approval document) before Save and add budget lines. It does not yet require completed lines or a reconciled line sum. Generated Budget/Version IDs and immutable year/currency are returned only on confirmed save. No unsupported partial field schema is inferred from the word Draft; an incomplete form stays unsaved with its actual errors. Submission additionally requires all valid lines, exact total equality and applicable Version rules. Subsequent saves revalidate their affected scope; Save never claims full submission readiness.

Capture a stable attempt payload, expected token and idempotency identity for each command. Pending details and line edits remain distinct validated scopes. Submit validates visible completeness, saves changed approval details first, reconciles/refetches the authoritative token as needed, saves changed lines using the confirmed current token, then submits that exact resulting Version with a separate submission key. Unchanged scopes need no repeated save. A stale result cannot silently overwrite newer changes or use the prior token. Client previews never submit calculated balances or generated identities.

| Result | Required recovery |
|---|---|
| Upload or evidence-link failure | Do not submit or claim the file is attached. Preserve authorised input; no Budget record if first save has not succeeded. An uploaded file alone is not a registered allocation. |
| Known first-save failure | No alleged Budget identity or submitted status. Explain the actual error; duplicate-year response opens the authorised existing record instead of another create. |
| Save confirmed, navigation failed | Offer Open saved draft for that exact returned Budget/Version. Do not register again. |
| One save confirmed, later scope save rejected | Retain the confirmed saved scope; state which changes were saved and which were not, and preserve permitted unsaved edits. No submit. |
| All required saves confirmed, Submit rejected | Your changes were saved, but the allocation was not submitted. Show cause and permitted retry on the same Draft. |
| Save/submit/approve/close outcome unknown | We could not confirm the result. Checking the existing request… Resolve/replay the original command identity and immutable payload. No duplicate root, submission attempt, decision or financial effect; no failure inferred from a timeout. |
| Stale record or permission changes | Re-read authoritative state and allow deliberate reconciliation. Preserve only still-authorised input; remove protected content on access revocation. Never auto-submit content the user has not reviewed. |

Every underlying save/submit/decision is its own transaction unless an inspected implementation proves otherwise. This document does not claim multiple saves plus submit are atomic. Actual RPC/token/idempotency/file-link mappings require implementation evidence. Retries after browser refresh recover the original unresolved request before creating another identity. Do not add autosave, a new workflow record or manual financial adjustment.

Replacing a Draft's current document affects only that Draft link. Every earlier submitted attempt retains the exact immutable attachment and reviewed values. Failed replacement cannot orphan submitted evidence; any temporary-upload cleanup follows the existing file owner's mechanism, never bulk deletion of historical files.

### 9.4 Review and closure observation contract

Review composes exact immutable submitted values and fixed predecessor comparison separately from live Reserved/Committed positions at a stated as_at. Compare material amount/line membership and changed external evidence, not only the total; include the complete proposed line set and exact source eligibility. Refresh cannot modify a submission, release holds or create a ledger event. Missing live positions/critical evidence produce unavailable, not zero or Ready. Approval repeats all guards under the existing lock.

Closure reads actual year-end status, Active Version and all remaining reservations including Needs Attention. After year-end, show either exact blockers, unavailable or ready. The close command revalidates current actor, state and every hold at commit using compatible existing Budget locks. Concurrent reservation/conversion/closure produces one valid ordering or an atomic typed failure; the displayed ready result is not clearance. Active commitments alone do not prohibit closure. Existing owner decreases/cancellations remain governed; closure permits no new hold, conversion or commitment increase.

## 10. UI architecture and routes

Budget & Funding remains a top-level module. Its menu contains only **Budget & Funding** and **Approval tasks**, the latter resolving access through the server; business decisions require Budget Approver authority, while AUTH v1.7 technical readers may inspect the exact review read-only. Other denied callers reach its inline Forbidden state rather than hidden navigation. Finance tasks remain in Procurement Planning; no Budget-side Finance queue or screen is added.

| Screen | Canonical route | Purpose |
|---|---|---|
| BUD-UI-01 Budget & Funding workspace | `/app/budget` | Selected fiscal year's existing Draft/submission, current Budget and operational position. |
| BUD-UI-02 Budget Version editor | `/app/budget/{budget_id}/version/{version_number}/edit` | Baseline or successor Draft approval details and lines. |
| BUD-UI-03 Budget workspace | `/app/budget/{budget_id}` | Read-only Overview, Budget Lines, Funding Activity and History. |
| BUD-UI-04 Approval task | `/app/budget/review/{budget_version_id}` | Approver inspection and return-or-approve decision. |
| BUD-UI-05 Budget Line detail | `/app/budget/line/{budget_line_id}` | Read-only line position and funding lineage; target of Planning's **Open Budget & Funding**. |

The Budget workspace uses URL-backed **Overview**, **Budget Lines**, **Funding Activity** and **History** tabs. The approval task uses **Overview**, **Budget Lines**, **Changes** and **History**. This document authorises no second dashboard, application shell or Frappe header.

---

## 11. Static Claude Design contract

Supply **KT-STD-001 §2 plus this section** to Claude Design. Nothing else. The closed-input rules, product-wide prohibitions, approved desktop shell, page-header pattern and division of supply are in KT-STD-001 §2.2–2.5 and are not repeated. Fixture actors, organisation units and fiscal years come from KT-STD-001 §8, extended by §15.1 below.

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
- Status: **Current**

| Label | Value |
|---|---|
| Budget reference | MOH-BUD-2027-001 |
| Current version | Version 1 |
| Currency | KES |
| Approval reference | MOH-FIN-BUD-2027-01 (Demo) |
| Approval date | 30 Sep 2026 |

Right-aligned secondary button: **View budget**

**Funding position row — four equal cards**

| Card label | Value |
|---|---:|
| Registered allocation | KES 160,000,000 |
| Reserved for requisitions | KES 0 |
| Committed to contracts | KES 0 |
| Available to reserve | KES 160,000,000 |

**Budget Lines preview**

| Budget Line | Available to | Registered allocation | Reserved for requisitions | Committed to contracts | Available to reserve | Action |
|---|---|---:|---:|---:|---:|---|
| Digital health infrastructure programme · MOH-BL-DHI-2027 | Digital Health | KES 100,000,000 | KES 0 | KES 0 | KES 100,000,000 | View |
| Digital health workforce development · MOH-BL-HWD-2027 | All departments | KES 60,000,000 | KES 0 | KES 0 | KES 60,000,000 | View |

Do not show Finance tasks, a register button on this Active-state artboard, or a Procuring Entity row.

### 11.1A BUD-DES-01A — Budget & Funding workspace, technical reader with an open Draft or Submitted version

**Retained v1.7 correction.** Before v1.7, no artboard showed a technical reader anything for a Draft or Submitted version — the workspace and BUD-UI-03 both scoped to Active, Superseded and Closed only, and AUTH-ADR-001 §8's technical-read right had no artboard exercising it. This is that artboard.

**Fixture context — outside the artboard:** Administrator · System Manager · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding**

Use isolated `BUD-SC-REVISION` (§15.6), including its KES 80m DHI hold and aggregate KES 80m available. Same page content header, filter row and Current budget card as BUD-DES-01 — an Active version, if one exists for the year, still renders identically; this variant adds to it, never replaces it.

**Additional card**, shown only when a Draft or Submitted-for-approval version exists for the selected year:

- Heading: **Allocation update awaiting Budget Approver review**; secondary Version 2 (fixture submitted by Josphat).
- Status badge: **Submitted for approval**

| Label | Value |
|---|---|
| Version | Version 2 |
| Submitted by | Josphat Mwangi, Budget Officer |
| Submitted | 15 Mar 2027, 16:20 EAT |

Right-aligned secondary button: **View version (read-only)**.

Selecting it opens BUD-UI-02's route for that version. Every field renders as a plain read-only value, per §12.2's correction below — no edit control, no Save draft, no Submit for review.

### 11.1B BUD-DES-01B — Officer and Approver pending-work variants

Use the same selected-year workspace and existing tasks. No second register or work queue. These variants supply the missing initial Draft/submission journeys alongside the technical-reader variant below.

| Actual state | Main message | Server-authorised action |
|---|---|---|
| No Budget record | No procurement allocation has been recorded for FY [year]. | Officer: Record approved allocation. Reader: none. |
| Initial Draft | Allocation draft. Continue recording the approved allocation. | Officer: Continue draft; authorised reader: View draft. No Register again. |
| Initial Submitted | Awaiting Budget Approver review. No allocation is current in KenTender yet. | Approver: Review; Officer: View submission. No current position or duplicate create. |
| Current plus Draft successor | Keep current allocation and its position; show Update in progress separately. | Officer: Continue update. Reuse the existing successor. |
| Current plus Submitted successor | Update awaiting Budget Approver review. The current allocation stays in use. | Approver: Review; Officer: View submission. |
| Returned Draft | Changes requested, full exact return comment and prior-attempt context. | Officer: Correct and resubmit, directly opening the same Draft. |
| Closed | Closed; year, exact closure actor/time and retained financial context. | Read permitted history; no new financial controls. |

Initial Draft/submission examples use the existing October V1 chronology; successor uses the isolated March profile. Never show a current zero allocation merely because approval is pending. Queue columns are Budget/year, Review (Initial allocation/Allocation changes), Submitted by, Submitted, Status, Review. Opening Review writes no decision. Multiple responsibilities display permitted work together without a role switch. Finance stays in Planning.

### 11.2 BUD-DES-02 — Record approved allocation

Fixture: Josphat, Budget Officer, 1 Oct 2026 09:20 EAT. Heading **Record approved allocation**. Introduction **Enter the allocation approved outside KenTender and attach its approval document.** Financial year FY 2027/28 and Currency KES are visible record context; the explicit target year comes from the selected, revalidated native-year context. It grants no authority. If the Officer needs another year before creation, return to/change the existing year choice without creating a record; after first save the year is immutable. No Budget title input, duplicate PE or generated reference field before save.

| Label | Exact fixture |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-01 (Demo) |
| Approval date | 30 Sep 2026 |
| Approved allocation | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget 2027-28 (Demo).pdf |

Use the existing input/date/fixed-currency/single-file controls. One document only; file upload/link state is explicit. Footer Cancel / **Save and add budget lines**. Save requires these four values under §9.3 and creates the Budget/Version once before opening the line editor. No Submit before lines exist; no competing second Save button, extra evidence, author-name field, justification, effective date or generic attachment. Cancel before first successful save creates no Budget record; temporary upload ownership remains governed separately.

### 11.3 BUD-DES-03 — Draft Budget Lines editor

Fixture: Josphat, 1 Oct 2026 10:10 EAT, exact saved MOH-BUD-2027-001-V1. Heading **Record approved allocation**, Draft. Tabs **Approval details**, **Budget lines** selected (same existing Overview/lines route state). Secondary reference/version. Page actions **Save changes** / **Submit for review**; adjacent save-scope label **Budget lines**. No competing row-save command.

| Total | Value |
|---|---:|
| Approved allocation | KES 160,000,000 |
| Total entered | KES 160,000,000 |

Message **Budget lines match the approved allocation.** Unequal variants show the exact positive **Amount still to assign** or **Amount over allocation** instead of an unexplained signed Difference. Totals preview locally but server responses and decimal rules control; never automatically adjust a line to balance.

| Budget line | Available to | Funding source | Amount | Action |
|---|---|---|---:|---|
| Digital health infrastructure programme; secondary MOH-BL-DHI-2027 | Digital Health | Government of Kenya | KES 100,000,000 | Remove |
| Digital health workforce development; secondary MOH-BL-HWD-2027 | All departments | Government of Kenya | KES 60,000,000 | Remove |

Title, exact department/null eligibility, governed funding source and amount are the only editable line facts. Guidance **Which department may use this budget line?** No descendant expansion, inferred source OU or permission grant. Add budget line adds a pending editable row; generated ID is server-owned and shown only after persistence. Remove affects an eligible unsubmitted new line; it cannot delete historical approved identity or submitted-attempt evidence. A saved/returned Draft remains governed by first-submission rules.

Submit includes pending valid details and lines through §9.3; it is not a requirement to manually visit and Save each tab. Unsaved navigation offers Save changes / Discard unsaved changes / Stay here for the named scope, preserving the other scope's pending work. Discard never deletes previously saved or submitted evidence. No money-control action, accounting reference, purpose duplicate or notes.

### 11.4 BUD-DES-04 — Active Budget overview

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001**

**Page content header**

- Eyebrow: **MOH-BUD-2027-001 · VERSION 1**
- Title: **Ministry of Health procurement budget 2027/28**
- Status: **Current**
- No header action button

**Tabs:** **Overview** selected, **Budget Lines**, **Funding Activity**, **History**

**Funding position row — four equal cards**

| Card label | Value |
|---|---:|
| Registered allocation | KES 160,000,000 |
| Reserved for requisitions | KES 0 |
| Committed to contracts | KES 0 |
| Available to reserve | KES 160,000,000 |

**Budget context card**

| Label | Value |
|---|---|
| Financial Year | FY 2027/28 |
| Currency | KES |
| Current version | Version 1 |

**External approval card**

| Label | Value |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-01 (Demo) |
| Approval date | 30 Sep 2026 |
| Approved allocation | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget 2027-28 (Demo).pdf |

The Approval document value uses the approved quiet file-link style.

**Activation card**

| Label | Value |
|---|---|
| Submitted by | Josphat Mwangi |
| Approved and activated by | Beatrice Kamau |
| Activated | 3 Oct 2026, 11:15 EAT |

Do not show edit controls, Update registered allocation, an approval stepper or a Procuring Entity row on this artboard.

Each live funding position explicitly displays **Funding position as at [owner observation time]**. Registered allocation is the recorded ceiling; Reserved for requisitions is remaining holds; Committed to contracts is active obligations; Available to reserve is the unreserved/uncommitted balance. It is not cash received or money paid. Approved evidence and exact version/actor/time belong in structured supporting detail, not a repeated technical identity strip. A historical route uses its exact Version and declared instant; unavailable replay is not today's ledger.

### 11.4A BUD-DES-04A — Active Budget overview for Budget Officer

Duplicate BUD-DES-04.

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001**

Keep all BUD-DES-04 content unchanged and add one right-aligned primary page-header button: **Update registered allocation**.

Do not add Edit budget, Add line or Finance controls to this Officer-only variant. Budget Approver closure belongs to §11.18 under its existing authority; the Officer gains no close power.

### 11.5 BUD-DES-05 — Active Budget Lines

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Budget Lines**

Reuse the BUD-DES-04 page content header without changing its content or placement.

**Tabs:** **Overview**, **Budget Lines** selected, **Funding Activity**, **History**

**Budget Lines table**

| Budget Line | Available to | Funding source | Registered allocation | Reserved for requisitions | Committed to contracts | Available to reserve | Action |
|---|---|---|---:|---:|---:|---:|---|
| Digital health infrastructure programme · MOH-BL-DHI-2027 | Digital Health | Government of Kenya | KES 100,000,000 | KES 0 | KES 0 | KES 100,000,000 | View |
| Digital health workforce development · MOH-BL-HWD-2027 | All departments | Government of Kenya | KES 60,000,000 | KES 0 | KES 0 | KES 60,000,000 | View |
| Total | — | — | KES 160,000,000 | KES 0 | KES 0 | KES 160,000,000 | — |

Do not show an Allocation column, utilisation, cost centre, purpose, row menu or edit action.

**Implementation note:** reuse the existing components, updated consistently to this successor’s labels and actor rules, from the BUD-DES-04 header and tabs component and the Budget Lines table component as it renders in the BUD-DES-13 family's Budget Lines duplicate. Do not design new table chrome.

### 11.6 BUD-DES-06 — Budget Line detail

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 4 Dec 2026, 09:58 EAT · opened from the Active Budget Lines table · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BL-DHI-2027**

**Page content header**

- Eyebrow: **MOH-BL-DHI-2027**
- Title: **Digital health infrastructure programme**
- Status: **Current**
- No header action button

**Context strip**

| Label | Value |
|---|---|
| Budget | MOH-BUD-2027-001 · Version 1 |
| Financial Year | FY 2027/28 |

**Funding position row — four equal cards**

| Card label | Value |
|---|---:|
| Registered allocation | KES 100,000,000 |
| Reserved for requisitions | KES 0 |
| Committed to contracts | KES 0 |
| Available to reserve | KES 100,000,000 |

**Line identity card**

| Label | Value |
|---|---|
| Available to | Digital Health |
| Funding source | Government of Kenya |
| Current version | Version 1 |

**Active reservations section**

- Heading: **Active reservations**
- Empty-state title: **No active reservations**
- Empty-state body: **This Budget Line has no confirmed funding reservations.**
- No empty-state button

Do not show Confirm funding, Return, Release, Convert, Adjust, Edit, approval evidence or contract fields.

### 11.6A BUD-DES-06A — Budget Line detail with two REQ reservations

Use conditional `BUD-SC-REQ-AUTH` in §15.4A at **16 Mar 2027, 10:15 EAT**, Naomi Chebet, Auditor. Reuse BUD-DES-06 shell; eyebrow `MOH-BL-HWD-2027`, title **Digital health workforce development**, owner **All departments**, Government of Kenya, Budget Version 1, FY 2027/28. This fixture is separate from the December pre-REQ screen.

| Card | Value |
|---|---:|
| Registered allocation | KES 60,000,000 |
| Reserved for requisitions | KES 50,000,000 |
| Committed to contracts | KES 0 |
| Available to reserve | KES 10,000,000 |

| Requisition / source | Reservation (secondary) | Plan Item | Originally reserved | Still reserved | Status | Action |
|---|---|---|---:|---:|---|---|
| REQ-MOH-2027-033-001 · HRMD source | RSV-MOH-2027-033-001 | PPI-MOH-2027-033 | KES 20,000,000 | KES 20,000,000 | Active | View Requisition |
| REQ-MOH-2027-033-001 · Digital Health source | RSV-MOH-2027-033-002 | PPI-MOH-2027-033 | KES 30,000,000 | KES 30,000,000 | Active | View Requisition |

Authorized secondary **View Plan Item** links preserve allocation context. No release, convert, adjust or Finance controls. Routes come from owner-authorized response data.

### 11.7 BUD-DES-07 — Funding Activity

Default: Naomi Chebet, Auditor, **10 Dec 2026, 15:05 EAT**, Budget Version 1. Reuse BUD-DES-04 header/tabs with **Funding Activity** selected. Filters **All Budget Lines** and **All funding events**. Show **No funding activity has been recorded for this budget.** No zero-value event, chart or Add action.

Conditional authorized-REQ variant: `BUD-SC-REQ-AUTH`, **16 Mar 2027, 10:15 EAT**. Header positions are approved KES 160m, reserved KES 50m, committed zero, available KES 110m. Show the following separate source rows. The exact recorded authorization time comes from the owning REQ event; the shared fixture defines 15 March but does not invent a more precise instant here.

| Date | Event | Budget Line | Requisition / reservation | Amount | Initiating actor |
|---|---|---|---|---:|---|
| 15 Mar 2027 | Requisition funding reserved | MOH-BL-HWD-2027 | REQ-MOH-2027-033-001 · RSV-MOH-2027-033-001 | KES 20,000,000 | Charles Kariuki, HOPF |
| 15 Mar 2027 | Requisition funding reserved | MOH-BL-HWD-2027 | REQ-MOH-2027-033-001 · RSV-MOH-2027-033-002 | KES 30,000,000 | Charles Kariuki, HOPF |

Footer **Showing 2 funding events**. Both are effects of one atomic authorization; audit also retains the calling service. Show business summaries and permitted owner links, not correlation IDs, before/after JSON, editable event rows or a Finance officer as the reserving actor.

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

**Implementation note:** reuse the existing components, updated consistently to this successor’s labels and actor rules, from the BUD-DES-04 header and tabs component and the version-history table component as it renders in BUD-DES-07's Funding Activity event table — same row and column chrome, different event set.

### 11.8 BUD-DES-08 — Review allocation changes

Fixture: Beatrice, Budget Approver, 16 Mar 2027 10:15 EAT; exact submitted MOH-BUD-2027-001-V2, based on V1, isolated BUD-SC-REVISION with DHI 80m reserved and no HWD hold. Title **Review allocation changes**, budget/year name prominent; Transfer; Awaiting review; secondary reference/version. Submitted by Josphat, 15 Mar 16:20 EAT. Tabs Overview selected, Budget lines, Changes, History; decision footer stays on all tabs.

**What changed** leads the opening page:

| Budget line | Current allocation / V1 | Proposed allocation / V2 | Change |
|---|---:|---:|---:|
| Digital health infrastructure programme | KES 100,000,000 | KES 90,000,000 | − KES 10,000,000 |
| Digital health workforce development | KES 60,000,000 | KES 70,000,000 | + KES 10,000,000 |
| Total | KES 160,000,000 | KES 160,000,000 | KES 0 |

Summary **KES 10,000,000 moves from infrastructure to workforce development. The total allocation stays the same.**

**Amounts already reserved or committed**:

| Budget line | Reserved + committed | Available after update |
|---|---:|---:|
| Digital health infrastructure programme | KES 80,000,000 | KES 10,000,000 |
| Digital health workforce development | KES 0 | KES 70,000,000 |

Explanation **This amount must remain covered.** Label **Live funding position · 16 Mar 2027 10:15 EAT. KenTender checks these amounts again when you approve.** Submitted amounts stay fixed; refresh updates only the separately identified live observation. Full proposed line eligibility and funding source remain inspectable on this page in Budget line details: DHI/Digital Health/GoK and HWD/All departments/GoK.

**External approval** labelled facts: reference MOH-FIN-BUD-2027-02 (Demo); date 14 Mar 2027; Approved allocation KES 160,000,000; one exact **MOH Approved Procurement Budget Transfer 2027-28 (Demo).pdf**. Show **Open approval document** and an in-page preview where supported. Keep the actual submitted file identity; unsupported preview uses the exact file link, unavailable file shows an error. No invented PDF contents, forced download, opened-document checkbox or later Draft file substitution.

Supporting **Submission and history** retains exact submitter and events from §11.11. Material evidence changes from V1 to V2 are visible: external reference -01 → -02, approval date 30 Sep 2026 → 14 Mar 2027, and the baseline approval document → transfer document. The comparison must not imply only line amounts changed. No extra evidence attachment is added to the submission.

Footer **Return for correction** / **Approve allocation update**. Consequence **Approval makes these registered amounts current in KenTender. Existing reservations and commitments remain in place. This does not release cash.** No green readiness checklist, arbitrary tab tour, per-line acceptance, repeat generic confirmation or new Reject/Activate step.

Blocked variant, isolated from the 80m profile: proposed DHI 90m, live Reserved+Committed 95m. Banner **Infrastructure cannot be reduced to KES 90,000,000 because KES 95,000,000 is already reserved or committed. Shortfall: KES 5,000,000.** Approval unavailable; permitted Return stays. Do not show negative spendable availability, release holds or mark them Needs Attention to bypass the monetary floor. Missing live basis, stale Version, invalid evidence or unbalanced transfer uses the exact failure and prevents a positive decision.

### 11.9 BUD-DES-09 — Approval task · Budget Lines

**Fixture context — outside the artboard:** Beatrice Kamau · `beatrice.kamau@moh.example.test` · Budget Approver · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Approval tasks > MOH-BUD-2027-001-V2**

Reuse the BUD-DES-08 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Budget Lines** selected, **Changes**, **History**

**Submitted Budget Lines table**

| Budget Line | Available to | Funding source | Proposed amount | Reserved + committed | Available after update |
|---|---|---|---:|---:|---:|
| Digital health infrastructure programme · MOH-BL-DHI-2027 | Digital Health | Government of Kenya | KES 90,000,000 | KES 80,000,000 | KES 10,000,000 |
| Digital health workforce development · MOH-BL-HWD-2027 | All departments | Government of Kenya | KES 70,000,000 | KES 0 | KES 70,000,000 |
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
| Digital health infrastructure programme · MOH-BL-DHI-2027 | KES 100,000,000 | KES 90,000,000 | − KES 10,000,000 |
| Digital health workforce development · MOH-BL-HWD-2027 | KES 60,000,000 | KES 70,000,000 | + KES 10,000,000 |
| Total | KES 160,000,000 | KES 160,000,000 | KES 0 |

**Funding impact** uses the protected amounts and after-update positions in §11.8, with current observation time. If useful, secondary detail may show one affected reservation and no commitments. Keep an actual shortfall or failed evidence check prominent; do not make internal floor-breach counts the decision summary. Include the changed external approval reference/date/document alongside line changes; preserve exact baseline identity even if a later version becomes current.

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

### 11.13 BUD-DES-13 — Review registered allocation, four tab variants

Fixture: Beatrice, 2 Oct 2026 10:00 EAT; exact submitted V1, inspection before the recorded 3 Oct activation. Heading **Review registered allocation**, FY 2027/28, Awaiting review; reference/version secondary. Submitter Josphat, 1 Oct16:20 EAT. Footer on all tabs **Return for correction** / **Approve registered allocation**. Consequence **Approval makes this recorded allocation current for KenTender procurement control. It does not approve the public budget or release cash.**

Overview puts the approved allocation KES 160m, complete two-line set and external evidence together:

| Budget line | Available to | Funding source | Submitted amount |
|---|---|---|---:|
| Digital health infrastructure programme · MOH-BL-DHI-2027 | Digital Health | Government of Kenya | KES 100,000,000 |
| Digital health workforce development · MOH-BL-HWD-2027 | All departments | Government of Kenya | KES 60,000,000 |
| Total | — | — | KES 160,000,000 |

Evidence: MOH-FIN-BUD-2027-01 (Demo); 30 Sep 2026; Approved allocation KES 160m; exact one MOH Approved Procurement Budget 2027-28 (Demo).pdf. Open approval document / supported preview; no required download or acknowledgement checkbox. Show actual missing/equality/configuration failures, not a green checklist. No Based on, Type of change, current floor, transfer balance or invented predecessor.

Budget lines tab repeats the same complete submitted set, not an unrelated Active table. Changes shows **Initial allocation. Review the complete submitted budget lines.** No empty previous-version column or comparison against zero. History retains V1 creation 1 Oct09:20, Draft saved15:55, submission16:20, all by Josphat; no successor or funding events. A returned/resubmitted variant must identify the exact submission attempt and full return reason, not overwrite this evidence. All tab reads bind to the exact submitted V1 attempt.

### 11.13A BUD-DES-13A — Retired

BUD-DES-13A modelled the same removed `Awaiting Activation` stage for Version 1. BUD-DES-13 covers the single decision point. Do not build a second task screen.

### 11.14 BUD-DES-14 — Successor revision draft · Overview

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 15 Mar 2027, 15:55 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Version 2 > Overview**

**Page content header**

- Eyebrow: **MOH-BUD-2027-001 · VERSION 2**
- Title: **Update registered allocation**
- Status: **Draft**
- Right-aligned secondary button: **Save changes**
- Right-aligned primary button: **Submit for review**

**Tabs:** **Approval details** selected, **Budget Lines**

**Version context card**

| Field label | Displayed value |
|---|---|
| Financial Year | FY 2027/28 |
| Currency | KES |
| Based on | Active Version 1 |
| Type of change | Transfer |

The first three rows use approved read-only components. Type of change uses the approved select component.

**External approval card**

| Field label | Displayed value |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-02 (Demo) |
| Approval date | 14 Mar 2027 |
| Approved allocation | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget Transfer 2027-28 (Demo).pdf |

Approval reference uses an input; Approval date a date component; Approved allocation a KES currency input; Approval document one file component showing the exact filename.

Show **The current allocation stays in use until this update is approved.** Save scope is Approval details; Type of change retains the four existing enum options. The immutable year/currency and fixed baseline remain secondary read-only facts. No extra change reason, justification, source type, effective date, notes or PE row.

### 11.15 BUD-DES-15 — Successor revision draft · Budget Lines

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 15 Mar 2027, 15:55 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Version 2 > Budget Lines**

Reuse the BUD-DES-14 page content header without changing its content or placement.

**Tabs:** **Approval details**, **Budget Lines** selected

**Line total strip**

| Label | Value |
|---|---:|
| Approved allocation | KES 160,000,000 |
| Total entered | KES 160,000,000 |
| Match | Budget lines match the approved allocation. |

**Editable successor lines table**

| Budget line | Reference (secondary) | Available to | Funding source | Current allocation | Proposed amount | Change |
|---|---|---|---|---:|---:|---:|
| Digital health infrastructure programme | MOH-BL-DHI-2027 | Digital Health | Government of Kenya | KES 100,000,000 | KES 90,000,000 | − KES 10,000,000 |
| Digital health workforce development | MOH-BL-HWD-2027 | All departments | Government of Kenya | KES 60,000,000 | KES 70,000,000 | + KES 10,000,000 |

Budget line name/reference, Available to, Funding source, Current allocation and Change use approved read-only components. Proposed amount uses a KES currency input.

Below the table, left-aligned secondary button: **Add Budget Line**.

Do not show a destructive Remove action on protected historical lines. A permitted **Omit from this update** action is separate: only when current remaining reservation and active commitment are zero, under BUD-BR-020, and with the same guard rechecked at activation. Retain all historical line/Version/event identities. DHI with the 80m hold cannot be omitted; an eligible HWD omission would also require a valid revised total/type and approval instrument, not silent rebalancing of this Transfer. New Draft-only lines use the existing removal rule. No classification, duplicate purpose, financial-control buttons or notes.

Keep **Total moved out: KES 10m** / **Total moved in: KES 10m** for this Transfer. Existing title, Available to and funding source remain read-only; a different identity requires Add budget line. Exact original references remain secondary; the name and proposed amount lead. Save scope is Budget lines; Submit follows §9.3, including pending valid details on the other tab.

### 11.16 BUD-DES-16 — Workspace state variants

Four static variants. Resolve authorization first. Authorized Loading, No baseline and Server error may use the BUD-DES-01 header/filter; Forbidden renders only its inline panel, with no Budget page header, filters or protected content. Do not show position cards or Budget Line rows unless stated. State treatments follow KT-STD-001 §3.

Fixture context for Loading, No baseline and Server error — outside the artboard: **Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 1 Oct 2026, 09:00 EAT**. Fixture context for Forbidden — outside the artboard: **Samuel Otieno · `samuel.otieno@moh.example.test` · No Budget responsibility · 1 Oct 2026, 09:00 EAT**. Frappe header breadcrumb for all variants: **Home > Budget & Funding**.

| Variant | Main content | Buttons |
|---|---|---|
| Loading | One full-width skeleton Current budget card followed by four skeleton position cards and two skeleton table rows | None |
| No baseline | Heading **No procurement allocation has been recorded for FY 2027/28.** Body **Record the externally approved allocation for this financial year.** | **Record approved allocation** |
| Server error | Heading **Budget & Funding could not be loaded.** Body **Try again. If the problem continues, contact KenTender support.** | **Try again** |
| Forbidden | Heading **You do not have access to Budget & Funding.** Body **This area needs one of these responsibilities: Budget Officer, Budget Approver, Finance Confirmation Officer or Auditor. Ask your KenTender administrator to assign one in System setup.** | None |

**Correction.** Forbidden is a business-role check; it is not the same check AUTH-ADR-001 §8 grants Administrator and System Manager. A technical reader holding neither a Budget business role nor a Budget business action never reaches this state — the workspace resolves for them per BUD-DES-01A instead. Samuel Otieno, this variant's fixture, has no Budget responsibility *and* is not Administrator or System Manager; Forbidden is what an ordinary user with no assignment sees, never what a technical reader sees.

### 11.17 Existing Frappe, KenTender and Planning controls

No artboard is authorised for the Frappe header, breadcrumb, module menu, global page chrome, notifications or user menu. Reuse those without visual modification, per KT-STD-001 §2.5.

The Finance task, sufficient and insufficient states, return dialog and planner-waiting state are defined by Procurement Planning. Do not reproduce or redesign them here.

---

### 11.18 BUD-DES-17 — Close budget, existing Approver command

This adds a missing state composition on existing BUD-UI-03; no new route, task, role or lifecycle. An Active Budget's authorised Approver can inspect year-end closure eligibility. Before the year ends, display **This budget can be closed only after [actual FY end date].** No override. After year-end, the relevant ready/blocked/unavailable state is visible.

| Condition | Content / action |
|---|---|
| Remaining hold | This budget cannot be closed yet. [Exact amount] remains reserved for requisitions. Show affected Budget lines and permitted reservation/owner links; Check again / Back to budget. Approval is not an alternative release action. |
| Unknown hold check | The funding position could not be checked. Try again before closing this budget. Never treat unavailable as zero. |
| Year ended, no remaining reservations | Closing stops new reservations, conversions and commitment increases. Existing commitments and history remain. Offer Close budget. Active commitments alone do not block. |
| Confirm requested closure | Close budget for FY [year]? Display exact Budget/year, above consequence, Cancel / Close budget. Focused confirmation, no extra approval stage or reason field. |
| Closed | Closed; exact actor/time/year; retained commitments, ledger and historic evidence. No new holds/conversions/increases. Owner-authorised existing commitment decreases/cancellations remain possible. |

Proposed isolated blocked fixture: 1 Jul 2028 after FY 2027/28 ends; DHI KES 20m remaining reservation, actual owner event/authority/time declared in executable profile. Show **KES 20,000,000 remains reserved for requisitions. Resolve the remaining reservations through their owning Requisition or Contract process, then check again.** Needs Attention counts as reserved. No Release button or manufactured owner task. Ready fixture starts separately with no remaining hold and optionally KES 60m active commitments; it must not erase the blocked profile's hold to force success.

### 11.19 BUD-DES-06B — Partial conversion and a reservation requiring review

Separate BUD-SC-CONVERT-PARTIAL profile, exact current owner observation time supplied at runtime. DHI line: registered allocation100m, originally reserved80m, converted60m, remaining reserved20m, active committed60m, available to reserve20m. Explain **KES 60,000,000 of the reservation is now committed to a contract. The remaining reservation is KES 20,000,000. No payment is recorded here.** Supporting reservation evidence: original80m = remaining20m + converted60m + released0. Commitment decrease does not replenish the hold or change its conversion history.

Rows lead with Requisition and source department, then exact original/still-reserved amounts; reservation IDs secondary. For Needs Attention use **Requires review — funds remain reserved**, full actual translated reason, responsible owner and authorised next-record link. No expiry promise, automatic release or local repair task. Where the approved owner facility is not implemented, state the supported limit and retain the financial restriction.

The two HWD reservations in BUD-DES-06A remain separate20m/30m with exact source lineage; do not merge their IDs into one generic hold. Funding activity shows business effects; Budget history shows version/submission/decision events. No manual release, conversion, adjustment, financial event entry or invoice/payment field.

### 11.20 Common readable supporting detail and error treatment

Use labelled amounts, source/department facts and short explanations; right-align comparable Money with visible currency. Material blockers remain outside collapsed History. Complete reasons, references and document facts wrap, with keyboard-accessible full reading. Narrow-screen composition preserves line name, relevant amount and decision result; no forced download or carousel of mandatory tabs.

Known failure, partial success, pending/unknown result and historical unavailable are distinct. Error summaries identify the actual field/line and exact amount still to assign, amount over allocation or shortfall. Use supported CurrencyBasis scale in messages, never guessed cents. Maintain focus/error announcements and preserve only still-authorised unsaved data. Access denial resolves before headers/filters/protected placeholders; technical read is a separate authorised outcome, not an ordinary no-assignment denial.

## 12. Functional interaction requirements — excluded from design prompts

Common page behaviour and accessibility follow KT-STD-001 §3.

### 12.1 BUD-UI-01 — Workspace

- The workspace resolves the existing Budget root, initial pending Version, current Version and open successor for the selected fiscal year; apply the complete §11.1B state matrix. It never chooses the first Budget or the first year.
- The Financial Year select is a local view filter. It grants nothing, is remembered only with a visible reset, and is ignored when stale or invalid.
- One Active Budget returns its exact version and derived positions. A Draft successor does not replace or alter the Active projection.
- Counts and rows use the same server-side predicate as direct routes and services.
- **Record approved allocation** appears only when the selected year has no Budget and the actor holds an Active Budget Officer assignment.
- **View budget** opens the exact server-returned `budget_id`.
- **Update registered allocation** comes only from the server's `available_actions`.
- **Correction.** Where a Draft or Submitted-for-approval version exists for the selected year and the caller holds AUTH-ADR-001 §8 technical read with no matching Budget business assignment, the server returns a fourth outcome for that version — **View version (read-only)** — instead of nothing. It opens BUD-UI-02's route with every mutation control removed or disabled, never a 404. See BUD-DES-01A.
- Loading never shows zero balances. Forbidden and failure states disclose no out-of-scope Budget IDs, titles, lines or amounts.

### 12.2 BUD-UI-02 — Version editor

- **Correction.** For Administrator and System Manager, this route resolves for any version status — including Draft and Submitted for approval — and returns the same content and lines a Budget Officer would see while drafting, with every field read-only (`can_edit: false`) and no business assignment required, per AUTH-ADR-001 §8. This is the route BUD-DES-01A's **View version (read-only)** opens. It is not a new route; it is this same one, already correctly authorising a technical reader before this correction — only never reachable from anywhere in the specified UI, and never documented as doing so.
- Saving the initial Draft creates the Procurement Budget and Version and returns generated references. The fiscal year and currency become immutable.
- Initial Overview edits only `approval_reference`, `approval_date`, `authorised_total` and one `approval_document_file_id`; a successor also has its existing `revision_type`. First-save and submit prerequisites, file outcomes and named save scopes are explicit in §9.3.
- The document component permits one current file. Replacing it in Draft removes the old Draft link; submitted evidence is retained in the version snapshot.
- Line create and update accept only title, owner scope, funding source and approved amount. Generated line IDs are not editable.
- Available-to choices are Active Organisation Units. Funding-source choices come from the governed catalogue.
- Draft line total and difference are server-calculated after every save response. The client may preview them but cannot submit calculated totals.
- Remove only a permitted unsubmitted new line. Do not delete previously Active or submitted history or change its identity. Omit from this update means exclusion from the proposed Version only under BUD-BR-020: no remaining reservation or active commitment, rechecked at approval, preserved history/line IDs and all total/type/evidence guards.
- **Submit for review** first saves pending valid scopes through §9.3, then submits the confirmed exact Version. The submit command alone locks/reloads the Draft and applies all readiness rules atomically. Saved scopes survive a later failure; no false atomic multi-save assertion.
- Failed readiness returns structured failing rules, keeps the Draft editable and focuses the first failing field or line.

### 12.3 BUD-UI-03 — Budget workspace

- Current Overview and Budget Lines use the Active Version and coherent ledger snapshot at response `as_at`. Explicit historical selection uses the exact retained Version and declared instant; show **Historical funding position** and its time. Never combine old approved amounts and live holds as a single historical position.
- The selected tab is represented in the URL. Back and forward change the tab without changing the Budget or mounting another page application.
- Active, Superseded and Closed versions are read-only.
- Budget Lines returns only stored identity values and derived positions. It infers no classification or expenditure data.
- Funding Activity is reverse chronological and server-filtered. Filtering grants no additional access, and the table shows business event summaries only.
- History contains version lifecycle events only; it does not duplicate the funding ledger.
- **Update registered allocation** creates one server-side copy of the Active Version, preserving line IDs and values, and opens its Draft Overview. A second open successor is rejected and the existing Draft route is returned.

### 12.4 BUD-UI-05 — Budget Line detail

- The route authorises the actor's responsibility and the exact line before returning its title, owner, funding source, positions or reservations.
- A Planning Finance task passes a line ID only. Budget independently authorises the actor and never trusts Planning route visibility as Budget authority.
- The default line page labels the current live position and observation time; it does not freeze to the Finance snapshot. Explicit historical mode follows §9.1 and labels the historical Version/instant.
- Before REQ authorisation, the page shows no hold from that draw even if a Planning Finance review shows planned amounts.
- After REQ authorisation, active reservations show each drawdown-line reservation, REQ/source and Plan Item references, original/remaining amounts and status, read-only, as in BUD-DES-06A.
- **View Plan Item** uses a server-returned authorised Planning URL. The Budget client does not build a route from a guessed naming rule.
- Opening or closing the page creates no check, reservation, decision or ledger event.

### 12.5 BUD-UI-04 — Approval task

- Business task review/decisions require an Active Budget Approver assignment. AUTH v1.7 §8 permits Administrator/System Manager to inspect the exact task and all submitted evidence read-only without that assignment; no mutation controls. Ordinary neutral/consumer read alone grants no workflow-task access.
- All four tabs always read the submitted `budget_version_id`; no tab substitutes the current Active Version.
- Overview leads with the complete initial allocation or successor changes, exact approval evidence and separately observed live protection results. Submitted identity/amounts never change when live balances refresh; actual failed checks are prominent and full evidence remains accessible.
- Budget Lines returns the complete submitted line set and current floors calculated at task-read time.
- Changes is calculated server-side against `based_on_budget_version_id`. Version 1 returns the explicit initial-baseline state and never invents a predecessor.
- History returns only events for the submitted version, in reverse chronological order.
- The decision footer remains available on every tab; every command carries version ID, expected status and expected record version.
- Return or Approve are available only while status is Submitted for approval. Return opens **What needs to change?** with **Correction required**, Cancel and Return for correction, validated at 10–500 characters. Preserve the exact immutable submission-attempt snapshot and document before editing the same Draft.
- Approve reruns evidence, totals, line identity, floor, transfer, responsibility and concurrency checks under transaction locks and activates in the same transaction. There is no separate later activation step.
- A failed live guard leaves the version Submitted for approval and returns the exact failed rule. No line, status, reservation or ledger position changes.
- The Budget Officer who submitted a version cannot approve it, enforced from the version's own submission audit event.

### 12.6 Procurement Planning Finance boundary

Planning owns Finance task discovery, whole-Plan comparison, insufficient-approved and available-funds-advisory states, Return, repeat review, current funding reassessment and original-versus-current evidence. Use PLN v1.18's compositions; Budget adds no Finance screen or decision.

Budget independently checks authorized caller/decision context before returning protected positions. **Check affordability** uses the nonlocking display contract. An affirmative Finance command uses §8.2A within the Planning transaction and creates **no reservation**. Above-approved or stale basis prevents a positive decision; exceeding current availability is advisory when the Plan remains within approved amounts. Finance Return records its reason in Planning only. Repeated Finance decisions use Planning's idempotency and evidence history, never Budget reservation IDs.

A Finance user may open the exact Budget Line through the authorized returned route. The line shows **current funding position — as at [time]**; it does not replace the frozen comparison in the Finance review. Navigation creates no decision or ledger event. `reserve_funding` rejects a Planning caller even when the user also holds Finance Confirmation Officer.

### 12.7 Additional page states

- A fiscal year with no Budget shows the no-baseline state and no zero-value funding position.
- An Active Budget with no funding events shows **No funding activity has been recorded for this budget.** and no Add action.
- A filter with no matching events provides **Clear filters**.
- Forbidden responses disclose no record names, counts, amounts or task details.

---

### 12.8 Year-end closure and current observations

Close budget is available only through the existing Budget Approver authority and close_budget command. Inspect and show server-derived year-end/current-status/remaining-reservation facts. Before year-end or with any positive remaining hold, including Needs Attention, no positive close may commit. Unavailable evidence is not clearance. After year-end and zero remaining holds, focused confirmation leads to commit-time revalidation under compatible locks. Existing active commitments alone do not bar closure; decreases/cancellations after closure remain in the Contract owner contract, not a Budget UI adjustment. Closed means no new holds, conversions or obligation increases, never payment or release.

Current and historical observations are timestamped separately. Data refresh or Check again creates no business/ledger effect. Unknown close/approval outcomes resolve the original idempotency identity before another attempt. After success show exact closure evidence and retain the authorised history; after a stale or failed guard show the actual still-current result.

## 13. Error contract

| Code | Required service result | User-facing explanation / recovery |
|---|---|---|
| `BUDGET_RESPONSIBILITY_REQUIRED` | You are not assigned the responsibility required for this action. No protected data is returned. | You are not assigned the responsibility required for this action. Ask your KenTender administrator to check your assignment. |
| `BUDGET_CONFIG_MISSING` | A referenced organisation unit, financial year, currency or funding source is unavailable. The operation fails closed. | The required setup is unavailable. Name the actual missing year, department, funding source or currency setting and direct the user to the KenTender administrator. |
| `BUDGET_ALREADY_EXISTS` | This financial year already has a procurement budget. Return its authorised route; create nothing. | An allocation record already exists for this financial year. Open it to continue where authorised. |
| `BUDGET_INVALID_STATE` | The command is not valid for the current server status. Current status is returned. | This budget has changed. Refresh to see the available actions. |
| `BUDGET_NOT_READY` | Submission or approval readiness failed. Structured failing rule IDs are returned. | Complete the highlighted details before submitting or approving. Focus the actual field or line. |
| `BUDGET_APPROVAL_EVIDENCE_REQUIRED` | Approval reference, date, document or authorised total is absent or invalid. | Complete the approval reference, date, allocation amount and approval document. Identify the missing or invalid value. |
| `BUDGET_TOTAL_MISMATCH` | Budget Line total does not equal the authorised total. No status changes. | Budget lines do not match the approved allocation. Show Amount still to assign or Amount over allocation with the exact difference. |
| `BUDGET_LINE_NOT_ELIGIBLE` | The line is missing, inactive or incompatible with the allocation's owner scope or funding source. | This budget line is not available for the selected source department or funding source. Show only authorised eligibility detail. |
| `BUDGET_LINE_IDENTITY_IMMUTABLE` | A successor attempted to change title, owner scope or funding source on an existing Active line. | Add a new budget line for the changed purpose, department or funding source. The existing approved line cannot be changed in this way. |
| `BUDGET_CONTEXT_NOT_FOUND` | No applicable Active procurement budget exists for that financial year. No line is selected. | No current procurement allocation is available for this financial year. Show existing pending work where authorised, not a zero balance. |
| `BUDGET_FINANCE_TASK_DENIED` | The caller does not hold the live Finance task responsibility. No protected position is returned. | You cannot act on this Finance review. Open the authorised review in Procurement Planning or ask your administrator to check your assignment. |
| `BUDGET_CHECK_STALE` | The REQ/Plan source set, owner revisions, token expiry or funding basis changed after Check Funding. Refresh; no reservation is created. | The funding check is no longer current. Refresh and check again before authorisation; no funds were reserved by this failed attempt. |
| `BUDGET_INSUFFICIENT_FUNDS` | One or more allocations lack full availability. Per-line shortfalls are returned; no reservation is created. | There is not enough available funding for this authorisation. Show the exact shortfall for each affected line; nothing is partially reserved. |
| `BUDGET_RESERVATION_CONFLICT` | This authorisation/drawdown line is already reserved, or an idempotency key is reused with a different payload. No duplicate or replacement is created. | This authorisation already has funding reserved, or the repeated request differs from the original. Show the actual result and preserve original reservations. |
| `BUDGET_REVISION_FLOOR_BREACH` | A proposed line amount is below current Reserved plus Committed. Approval is blocked. | This budget line must cover the amount already reserved or committed. Show proposed amount, protected amount and exact Shortfall. |
| `BUDGET_TRANSFER_UNBALANCED` | Transfer increases and decreases do not balance. Submission or approval is blocked. | The amounts moved out and moved in must match. Show both totals and the exact difference. |
| `BUDGET_CONVERSION_EXCEEDS_REMAINDER` | Contract conversion exceeds the reservation remainder. No commitment changes. | The proposed contract amount exceeds the remaining reservation. Review it in the owning Contract process; no commitment was changed. |
| `BUDGET_COMMITMENT_INCREASE_UNFUNDED` | A proposed commitment increase lacks available funds. No adjustment occurs. | There is not enough available funding for this commitment increase. Return the exact shortfall to the owning Contract action. |
| `BUDGET_CLOSED` | The budget is closed and cannot accept a new reservation. | This budget is closed. New reservations, conversions and commitment increases are not permitted. |
| `BUDGET_STALE_WRITE` | The expected record version is stale. No newer data is overwritten. | This budget has changed since you opened it. Refresh to see the current details; do not overwrite newer saved work. |
| `BUDGET_DOWNSTREAM_FORBIDDEN` | A downstream caller attempted an unsupported Draft read or direct mutation. | This information or action is not available through this request. Do not expose protected data or provide a manual bypass. |
| `BUDGET_DECISION_BASIS_STALE` | Expected Budget/line/eligibility or annual-basis evidence changed. Positive caller decision rolls back; refresh the comparison. | The allocation or its eligibility details have changed. Refresh the Planning comparison before confirming; no positive decision was saved by this failed command. |
| `BUDGET_PLAN_EXCEEDS_APPROVED` | Planned totals exceed approved amounts; authorized caller receives exact per-line excess. No positive decision. | The Plan exceeds the approved allocation. Show the exact approved-versus-planned excess in the Planning review. |
| `BUDGET_ANNUAL_BASIS_UNAVAILABLE` | No applicable complete approved annual basis, or authoritative line total is inconsistent. No zero/Plan-total fallback. | The complete approved annual allocation could not be confirmed. Try again or resolve the actual source issue; do not substitute zero, available funds or the Plan total. |
| `BUDGET_MONEY_PRECISION_INVALID` | Amount is malformed, over scale/range or has missing/unsupported currency precision. Reject without rounding. | Enter an amount within the supported size and decimal-place limit. Show the verified currency scale; unavailable precision requires setup recovery, not a guessed default. |
| `BUDGET_SOURCE_OU_REQUIRED` | A real explicit source department is absent or unresolved. Do not infer it from the user. | The source department is missing or unavailable. Complete the source in its owning Planning or Requisition record; do not infer it from the user. |
| `BUDGET_HISTORICAL_BASIS_UNAVAILABLE` | Exact requested historical Version/position cannot be reproduced. No current-data substitution. | The funding position for this version and time is unavailable. Do not substitute the current position. |
| `BUDGET_IDEMPOTENCY_CONFLICT` | Same command key has a different immutable payload. Return no new effect. | This request differs from the original attempt. Check the original result before retrying; no new effect was created. |

`BUDGET_SCOPE_REQUIRED`, `BUDGET_PERMISSION_DENIED` and `BUDGET_CONTEXT_AMBIGUOUS` are removed: the first two named a scope and a capability that no longer exist, and the third is unreachable now that one fiscal year has at most one Budget. Message conventions are in KT-STD-001 §11. Display plain text and support references, not raw payloads or stack traces. Known rejection and unknown outcome differ: use §9.3 recovery before claiming failure or retrying. Translated wording never overrides a code, guarded action or owner boundary.

---


## 14. Audit and historical integrity

Append-only events: Budget and successor-version creation; Draft approval-detail and line change sets; submit, return, approve, activate, supersede and close; owner decision evidence referencing a funding check; reservation creation; revalidation, release, conversion and commitment adjustment; responsibility, segregation, floor and concurrency denial; and protected-access security audit where supported. Read/check calls do not create business or funding-ledger events. A transport/security log is not a new financial record. Successful idempotent replay returns prior financial events; it does not append a second effective funding event.

Each event records actor or calling service, business role, the exercised responsibility assignment ID, fiscal year, relevant IDs, action, timestamp, before and after status or line position, required decision reason, correlation ID and calling module. No event records a Procuring Entity or a capability string.

Active, Superseded and Closed versions are immutable. Funding Ledger events cannot be edited or deleted. Downstream reservation and commitment identities remain resolvable after a successor activates or the fiscal year closes.

---

## 15. Deterministic seed contract

SEED-001 v1.3 governs shared identities and the BASE/READY separation; CFG v0.10 governs actual authority/configuration at the frozen command instant. A documentation amendment is not proof that the executable seed or its end-to-end validator passes.

### 15.1 Actors and baseline chronology

Josphat Mwangi (`josphat.mwangi@moh.example.test`) has separate site-wide Budget Officer and Finance Confirmation Officer assignments. Beatrice Kamau (`beatrice.kamau@moh.example.test`) is Budget Approver. Naomi Chebet is Auditor. Charles Kariuki is HOPF and initiates the REQ authorisation; Budget records the registered service too. All are resolved by live assignments; no Administrator business action. Samuel Otieno has neither a Budget assignment nor technical-read grant and supplies Forbidden.

Baseline creation: Josphat, 1 Oct 2026 09:20 EAT; Draft save 15:55; submission 16:20; Beatrice approval/activation 3 Oct 2026 11:15. The prior 2 Oct approval-review artboard is an inspection before the 3 Oct decision. Technical-reader successor artboard uses the isolated March revision, not an impossible future submission shown in December.

### 15.2 Required configuration and boundaries

Resolve native Fiscal Year `2027-2028` (1 Jul 2027–30 Jun 2028), explicit Company/currency association, KES precision 2, `OU-MOH-DHI`, `OU-MOH-HRMD`, and enabled Government of Kenya funding-source identity. No fallback records or guessed mapping. Exact native metadata fields and precision mapping require repository inspection.

**Shared date dependency remains open:** CFG-XD-001 identifies the May 2027 procurement schedule against FY/profile starting July 2027. This Budget amendment neither shifts invitation to 2028 nor waives date guards. The conditional positive downstream fixture remains gated on coherent approved FY/applicability evidence. Budget registration dates represent externally approved future-year allocations, not evidence that a pre-FY tender is eligible.

### 15.3 Active Budget baseline

| Field | Exact value |
|---|---|
| Budget / Version | `MOH-BUD-2027-001` / `MOH-BUD-2027-001-V1` |
| FY / currency / scale | `2027-2028` / KES / 2 |
| Status | Active Budget Version; this does **not** imply an Active Plan. |
| External approval reference | `MOH-FIN-BUD-2027-01 (Demo)` |
| External approval date | 30 Sep 2026 |
| Approval document | `MOH Approved Procurement Budget 2027-28 (Demo).pdf` |
| Authorised total | `"160000000.00"` |

| Line | Title | Owner scope | Funding source | Approved |
|---|---|---|---|---:|
| MOH-BL-DHI-2027 | Digital health infrastructure programme | Digital Health (`OU-MOH-DHI`) | Government of Kenya | KES 100,000,000 |
| MOH-BL-HWD-2027 | Digital health workforce development | **Entity-wide** (null owner) | Government of Kenya | KES 60,000,000 |

**Explicit fixture correction:** v1.7's HWD owner HRMD excluded the DHI laptop source under its own BUD-BR-007. Entity-wide is required for the shared two-department fixture and applies consistently to baseline creation and every artboard. It does not make actors site-wide in other modules. A fresh/reset fixture creates this correct baseline through governance. Do not update an already Active real line's immutable scope in place: inspect existing data and use a new eligible line plus governed source/Budget successors; preserve real history and downstream scope restrictions. Release evidence must distinguish a fixture rebuild from a production data correction.

### 15.4 BASE: Planning with no REQ authorisation

| Line | Approved | Planned | Reserved | Committed | Available |
|---|---:|---:|---:|---:|---:|
| DHI | KES 100m | KES 80m | KES 0 | KES 0 | KES 100m |
| HWD | KES 60m | KES 50m | KES 0 | KES 0 | KES 60m |
| Total | KES 160m | KES 130m | KES 0 | KES 0 | KES 160m |

BASE has two Plan Items and three exact sources under SEED v1.3, including HRMD 100 Each/KES 20m and DHI 150 Each/KES 30m against HWD. BASE's None/None planned designations fail the mandatory illustrative reservation target; its Plan remains blocked Draft even though Budget is Active. The annual denominator stays 160m; illustrative 30% target is 48m. READY's separately declared planned Youth designation on the 50m laptop item gives 31.25% and zero shortfall; production law/configuration/date prerequisites still apply. Budget does not seed eligibility entitlements or force the Plan Active.

December BUD-DES-01/04/05/06/07 show no reservations. Finance confirmation and the entire Planning lifecycle leave all Budget financial balances unchanged. A Draft or submitted REQ likewise reserves nothing.

### 15.4A BUD-SC-REQ-AUTH: conditional harmonized authorisation

Only run after the eligible Active positive Plan scenario and owner configuration/date gates pass. REQ `REQ-MOH-2027-033-001`, Version 1: Grace drafts 1 Mar 2027; Peter submits 8 Mar; Charles authorises 15 Mar. Retain exact owner-generated Version and event identities/timestamps; do not invent a more precise shared instant.

| REQ source / drawdown line reference | Plan allocation | Source OU | Reservation | Line | Amount |
|---|---|---|---|---|---:|
| SRC-MOH-033-001 / PIL-MOH-033-001 | PSA-MOH-2027-033-001 | OU-MOH-HRMD | RSV-MOH-2027-033-001 | MOH-BL-HWD-2027 | KES 20m |
| SRC-MOH-033-002 / PIL-MOH-033-002 | PSA-MOH-2027-033-002 | OU-MOH-DHI | RSV-MOH-2027-033-002 | MOH-BL-HWD-2027 | KES 30m |

Both retain stable Plan Item `PPI-MOH-2027-033` and the exact approved Plan/item/source revisions supplied by Planning. The owner API maps source/drawdown references to physical IDs; they are not interchangeable.

| Line | Approved | Reserved | Committed | Available |
|---|---:|---:|---:|---:|
| DHI | KES 100m | KES 0 | KES 0 | KES 100m |
| HWD | KES 60m | KES 50m | KES 0 | KES 10m |
| Total | KES 160m | KES 50m | KES 0 | KES 110m |

Two reservation-creation ledger effects belong to one authorisation transaction. Repeating it returns the same two IDs. Pre-consumption revocation releases both and reverses the exact Planning drawdown together; restored Budget availability is 160m, historical authorisation remains, and Planning's permanent first-authorisation scope lock remains under its own rules.

### 15.5 Isolated service profiles

These profiles reset independently; none supplies extra activity to BASE or the harmonized laptop chain. Legacy `BUD-SC-FIN-*` identifiers are renamed to `BUD-SC-REQ-*` because their effect belongs to REQ authorisation, not Finance. Fixture builders must supply actual owner-valid authorisation events/authority or explicitly scoped provider-test stubs; a stub is not end-to-end evidence.

| Profile | Exact precondition / expected result |
|---|---|
| BUD-SC-REQ-SINGLE | DHI available 100m; authorised draw 80m → reserved 80m, available 20m. |
| BUD-SC-REQ-COMBINED | DHI 100m and HWD 60m available; draws 72m and 48m → availability 28m and 12m; two reservations or none. |
| BUD-SC-REQ-SHORT | Isolated prior valid DHI hold 30m; available 70m; new requirement 80m → shortfall 10m, no new effect. |
| BUD-SC-REQ-SAME-LINE | HWD available 40m; rows 20m + 30m → aggregate shortfall 10m; neither reserves. Do not test rows independently. |
| BUD-SC-CONVERT-PARTIAL | DHI hold 80m; convert 60m → remaining hold 20m, commitment 60m, available 20m. |
| BUD-SC-DUPLICATE-CORRELATION | Replay exact successful SINGLE key/payload → original reservation/effect. Changed payload with same key fails. |
| BUD-SC-AFFORDABILITY | DHI approved 100m, reserved 30m, planned 80m → within approved passes; available advisory shortfall 10m; Finance creates no hold. |
| BUD-SC-ANNUAL-BASIS | Budget 100m, Plan 40m, qualifying 12m → annual share 12%, never 30%; include unused lines and do not net holds. |
| BUD-SC-BASIS-RACE | Budget successor races Finance decision; one serialized ordering succeeds or stale failure occurs, never a positive decision on an already replaced basis. |
| BUD-SC-PRECISION | Exact 18-integral-digit Money round-trip with supported decimals; excess scale and overflow rejected; decimal arithmetic has no epsilon path. |

### 15.6 BUD-SC-REVISION: isolated successor artboards

Start from baseline V1 plus **isolated REQ DHI hold 80m**, HWD no hold. This is not the harmonized laptop reservation and never coexists with it in a single fixture. Create the hold through BUD-SC-REQ-SINGLE before 15 Mar 2027 13:10; freeze an explicit owner-valid event instant in the executable profile before claiming the scenario passes.

Version `MOH-BUD-2027-001-V2`, based on V1; Transfer; external reference `MOH-FIN-BUD-2027-02 (Demo)`, approval date 14 Mar 2027, document `MOH Approved Procurement Budget Transfer 2027-28 (Demo).pdf`; total 160m; DHI proposed 90m, HWD 70m. Josphat creates 15 Mar 13:10, saves 15:55, submits 16:20. Review/read-only fixture is 16 Mar 10:15, EAT.

DHI floor 80m/headroom 10m; HWD floor zero/headroom 70m; transfer difference zero. One affected reservation, no commitment. On approval, total remains 160m; DHI available 10m, HWD available 70m. Separate reset copies exercise Return and Approve. BUD-DES-01A and 08–15 consume this exact profile; initial-baseline BUD-DES-13 variants still use their own October V1 fixture.

### 15.7 Seed and historical controls

Upsert stable IDs deterministically; second run makes no change. Validate through domain services, with frozen authority dates and exact CurrencyBasis. No second entity, fallback catalogue, administrative workflow bypass, float amounts or patched Active histories. Keep future fixtures conditional where owning contracts/date evidence are absent. Record each artboard's scenario and observation time; historical December screens must not display March reservation effects.

---

### 15.8 Additional isolated usability profiles

These extend the retained §15 scenarios; they do not silently modify BASE, REQ-AUTH or REVISION. Each executable fixture must declare a valid owner event/actor/instant and reset independently. A provider stub is not integrated evidence.

| Profile | Exact scenario / expected result |
|---|---|
| BUD19-SC-PENDING | Existing October V1 Draft/submission and returned-attempt branches at actual chronological instants. Officer finds Continue draft/Correct and resubmit; Approver finds Review; no current allocation or duplicate registration. Return has an exact stored10–500 character comment and retained file snapshot. |
| BUD19-SC-LIVE-BREACH | Independent successor test: DHI proposed90m; current reserved+committed95m; exact5m shortfall. Approval blocked; no partial activation, release or negative spendable balance. Do not attach this balance to the80m review fixture. |
| BUD19-SC-CLOSE-BLOCKED | 1 Jul2028 after FY2027/28 end, DHI20m remaining hold. Closure blocked, including Needs Attention variant. Verify Budget Approver's assignment at the frozen actual command instant. |
| BUD19-SC-CLOSE-READY | Separate year-ended profile with zero remaining holds, optionally60m active commitments. Closure allowed if all current guards pass; obligations/history retained; new holds/conversions/increases rejected. No manual release of another scenario's hold to construct this result. |
| BUD19-SC-CLOSE-UNKNOWN | Live year-end/hold verification unavailable; no close. Also lose response after a valid close to prove original-result recovery without another effective event. |
| BUD19-SC-PARTIAL-CONVERSION-UI | Reuse BUD-SC-CONVERT-PARTIAL exact100m allocation,20m remaining reservation,60m commitment,20m available. Runtime observation and authorised owner links supplied from that profile, not invented shared events. |
| BUD19-SC-OMISSION | Independent valid successor: line with zero remaining reservations and active commitments can be omitted while prior Version/identity/history stay readable; nonzero protected amount blocks. Revised total/type/evidence must be valid. |
| BUD19-SC-RECOVERY | Unknown creation, upload/link failure, details-save success then line failure, saved-but-submit-failed, stale tree/token, duplicate click and revoked access. No duplicate root/attempt/event or protected-data retention. |

Josphat/Beatrice/Naomi retain their existing roles; technical readers never receive a Budget role to pass tests. The full source approval PDFs are real controlled fixture artifacts when supplied by the owner; an HTML/MD filename alone is not proof that an uploaded document exists. Preserve all existing BUD18-XD gates and exact source event identities.

## 16. Acceptance contract

All 70 v1.8 criteria remain mapped below, including their earlier v1.7 sources, with operative contradictions corrected. Section 16.2 adds 28 usability criteria, giving **98 acceptance criteria** total. Old IDs are traceability references, not a parallel implementation contract. Every new criterion is required unless its named downstream facility remains explicitly gated. These are requirements, not claims of tests executed in this document review.

| ID | Prior criterion / source | Required result |
|---|---|---|
| BUD18-AC-001 | BUD-AC-001 | The module installs and migrates cleanly on a site with ERPNext installed; no DocType name collides with an ERPNext DocType. |
| BUD18-AC-002 | BUD-AC-002 | No executable metadata, route, service, field, seed or active test contains Allocation as a separate object, Budget Value Treatment, PVO or Value Commitment. |
| BUD18-AC-003 | BUD-AC-003 | Budget Officer records one Draft for the explicit year through Save and add budget lines, gets generated references, and resumes the existing record on navigation failure; no duplicate create for pending initial work. |
| BUD18-AC-004 | BUD-AC-004 | Without the applicable live business responsibility, including technical Administrator/System Manager alone, user mutations are denied. Registered service effects require authenticated owner command/event context and initiating authority; Finance decisions remain PLN-owned. |
| BUD18-AC-005 | BUD-AC-005 | Initial registration edits only the four approval-detail fields, with explicit year/currency context and §9.3 save/submit validation; successor adds only its existing revision_type. No extra appropriation, justification or Allocation object. |
| BUD18-AC-006 | BUD-AC-006 | A line accepts only title, owner scope, funding source and approved amount. |
| BUD18-AC-007 | BUD-AC-007 | Submission is blocked unless approval evidence is complete and the line total equals the authorised total. |
| BUD18-AC-008 | BUD-AC-008 | Only one Procurement Budget and one Active Version exist per fiscal year, and the guard holds when the command layer is bypassed. |
| BUD18-AC-009 | BUD-AC-009 | Explicit real source OU yields Entity-wide or exactly matching Active lines for Need-backed and direct sources; missing OU fails; owner scope never grants or narrows user Budget authority. |
| BUD18-AC-010 | BUD-AC-010 | An allocation whose funding source differs from the line's is rejected. |
| BUD18-AC-011 | BUD-AC-011 | Every Planning event, including repeated Finance review and Active reassessment, leaves Budget financial balances unchanged; no reservation, commitment or funding-ledger effect is created. |
| BUD18-AC-012 | BUD-AC-011a | check_plan_affordability returns coherent per-line exact amounts, eligibility, revisions, as_at and both verdicts; no lock, check token, financial write or ledger event. |
| BUD18-AC-013 | BUD-AC-011b | A planned total exceeding a line's approved amount returns the within-approved verdict as failed with the exact excess; a planned total exceeding currently available but within approved returns within-approved as passed. |
| BUD18-AC-014 | BUD-AC-011c | Only successful REQ authorisation creates reservations. Drafting, submission, return and Planning callers create none; a Planning reserve_funding call is rejected. |
| BUD18-AC-015 | BUD-AC-012 | check_funding writes nothing and returns exact per-allocation positions. |
| BUD18-AC-016 | BUD-AC-013 | A REQ authorisation reserves one row per complete drawdown line, including two rows sharing one Budget Line; drawdown, reservations, decision, handoff and outbox commit together or all roll back. |
| BUD18-AC-017 | BUD-AC-014 | An insufficient allocation returns the exact shortfall and creates no reservation. |
| BUD18-AC-018 | BUD-AC-015 | Same authorisation key/payload returns the original full reservation mapping and no duplicate effective events; changed payload conflicts and replay after release does not recreate a hold. |
| BUD18-AC-019 | BUD-AC-016 | Concurrent authorisations cannot oversubscribe a line, and no position becomes negative. |
| BUD18-AC-020 | BUD-AC-017 | Partial conversion leaves the correct remainder reserved and the correct amount committed. |
| BUD18-AC-021 | BUD-AC-018 | Commitment adjustment, release and cancellation are idempotent by correlation ID. |
| BUD18-AC-022 | BUD-AC-019 | `Needs Attention` retains the reserved amount and blocks downstream progression without releasing funds. |
| BUD18-AC-023 | BUD-AC-020 | BASE, conditional two-row REQ-AUTH and isolated REVISION positions match §15 exactly, with the correct scenario/time on every affected artboard. |
| BUD18-AC-024 | BUD-AC-021 | A successor cannot reduce a line below Reserved plus Committed. |
| BUD18-AC-025 | BUD-AC-022 | A Transfer successor with unbalanced increases and decreases is blocked at submission and approval. |
| BUD18-AC-026 | BUD-AC-023 | Approving a successor atomically activates it and supersedes the prior Active version, preserving all identities. |
| BUD18-AC-027 | BUD-AC-024 | Existing line title/source-department eligibility/funding source cannot change. Governed omission from a successor is distinct from deletion and requires zero remaining reservation/active commitment; historical line identities remain. |
| BUD18-AC-028 | BUD-AC-025 | The submitting Budget Officer cannot approve the same version, enforced from the submission audit event. |
| BUD18-AC-029 | BUD-AC-026 | The seed is deterministic and a second run produces no change. |
| BUD18-AC-030 | BUD-AC-027 | A missing ERPNext Fiscal Year, organisation unit, currency or funding source fails seed execution without creating a fallback record. |
| BUD18-AC-031 | BUD-AC-028 | PLN/REQ/Contract callers use only owner contracts; neither side imports downstream controllers or reads/locks another owner’s tables. |
| BUD18-AC-032 | BUD-AC-029 | Downstream direct-table mutation and Draft reads are rejected. |
| BUD18-AC-033 | BUD-AC-030 | All five canonical routes and revised BUD-DES families, including pending work, decision-first review, both historical/live positions and year-end closure variants, render correctly with owner-authorised links. |
| BUD18-AC-034 | BUD-AC-031 | Loading, no-baseline, forbidden and server-error states disclose no false or unauthorised funding data. |
| BUD18-AC-035 | BUD-AC-032 | The Frappe header and breadcrumb are reused and not duplicated inside the Vue page; no Procuring Entity or context selector appears on any Budget screen. |
| BUD18-AC-036 | BUD-AC-033 | Approver can inspect and close after FY only with zero remaining holds including Needs Attention. Active commitments alone do not bar closure; no new holds/conversions/increases afterward, while permitted commitment decreases/cancellations and historical lineage remain. |
| BUD18-AC-037 | BUD-AC-034 | No executable metadata, permission, route, service, seed or active test refers to Budget Reviewer, Budget Activation Authority, Budget Viewer as a workflow role, or the removed `In Review` and `Awaiting Activation` statuses. |
| BUD18-AC-038 | BUD-AC-035 | User business writes use live registered AUTH responsibility hooks; registered downstream services validate owner event/command and actor context. No User Permission, capability string, FY grant or parallel lookup participates. |
| BUD18-AC-039 | BUD-AC-036 | No `procuring_entity_id`, KenTender `FinancialYear`, `cost_center` or accounting-transaction reference exists in Budget schema, services, seeds, fixtures or tests. Explicit owner/native Company currency metadata and Fiscal Year references remain permitted. |
| BUD18-AC-040 | BUD-AC-037 | Budget Officer, Budget Approver and Finance Confirmation Officer appear in the business-role registry with `scope_type = Site-wide`, and no Budget command performs a user-scope organisation-unit or fiscal-year check. |
| BUD18-AC-041 | BUD-AC-038 | ERPNext accounting and its own `Budget` and `Cost Center` records remain fully functional and untouched after this module installs. |
| BUD18-AC-042 | BUD-AC-039 | Every page resolves its authorisation verdict before rendering; a denied actor sees the inline Forbidden panel with no header, filter, content or empty state painted, and no permission modal appears on page load. |
| BUD18-AC-043 | BUD-AC-040 | The Forbidden panel names the responsibilities that open the surface and directs the user to a KenTender administrator; it names no line manager or supervisor. |
| BUD18-AC-044 | BUD-AC-041 | Selecting this module without access pushes its own route, highlights it in navigation, and lands on its Forbidden state; the module is never hidden and route and view never diverge. |
| BUD18-AC-045 | BUD-AC-042 | Administrator/System Manager can discover and read every Budget/Version/task in all statuses, including edit and exact approval routes, without business assignment or mutation. Ordinary unauthorised callers receive non-disclosing denial. |
| BUD18-AC-046 | FU-23; decision validation | validate_plan_affordability_for_decision retains serialization until the caller decision commits, validates expected Budget/line revisions and returns immutable evidence without any Budget financial record or ledger write. |
| BUD18-AC-047 | FU-23; concurrency | A racing Budget activation/closure and positive Finance decision cannot commit a stale basis; test both orderings and caller rollback after successful provider validation. |
| BUD18-AC-048 | FU-23; annual denominator | Annual basis includes every approved line, including unused lines; validates authorised-total reconciliation and returns exact FY/Version/CurrencyBasis/count/digest. Budget 100m / Plan 40m / qualifying 12m yields 12%. |
| BUD18-AC-049 | FU-23; annual concurrency | A change in an unused line that alters annual denominator stales the decision’s expected annual basis; root serialization protects that basis through the same caller commit. |
| BUD18-AC-050 | FU-23; historical evidence | Historical annual/line reads return exact retained Version/instant/precision; unsupported replay fails typed and never substitutes current values. Missing basis never becomes zero. |
| BUD18-AC-051 | FU-23/FU-30; precision | All Budget API Money values are plain decimal strings in currency units; exact 18-integral-digit plus supported-scale round-trip succeeds. Excess scale, float JSON, malformed and overflow values fail before effects. |
| BUD18-AC-052 | FU-30; arithmetic | Shared precision tests across BUD/NDS/REQ/PLN prove exact aggregation, comparison, token digests and persistence without flt(), binary float, epsilon or silent rounding. Contract suite evidence is required before release. |
| BUD18-AC-053 | FU-23; currency | get_budget_currency_contract returns verified metadata/precision identity; missing native Company mapping or unsupported precision blocks affected writes/decisions. Changing native default never rewrites Budget currency/history. |
| BUD18-AC-054 | FU-23; human reference | Eligible-line responses return human reference plus stable/exact IDs; labels can display a reference without guessing one from a technical ID. |
| BUD18-AC-055 | FU-23; source eligibility | HWD Entity-wide accepts both HRMD and DHI; an isolated HRMD-owned line rejects DHI even when the initiating user has broad authority. OU descendant membership is not inferred. |
| BUD18-AC-056 | CFG v0.10 integration | Disabled source/OU is excluded from new selection and rechecked at decisions while historical read-by-ID/frozen labels remain available. No catalogue rename rewrites approved line identity. |
| BUD18-AC-057 | REQ duplicate-line risk | Two REQ rows of 20m and 30m against one line with 40m available return aggregate 10m shortfall and create nothing; both individually passing is insufficient. |
| BUD18-AC-058 | REQ identity correction | Two eligible sequential draws against the same original Planning allocation have distinct REQ/drawdown reservations; same authorised drawdown with a different key cannot duplicate. Owner remaining allowance and scope gates apply. |
| BUD18-AC-059 | REQ token contract | The complete-array check token binds expiry, actor/caller, exact source/revision/amount payload and cannot authorize a subset, changed amount or expired request. |
| BUD18-AC-060 | REQ revocation | Unconsumed REQ revocation reverses exact drawdown and both 20m / 30m reservations atomically. Consumed handoff blocks that route; a funding release cannot reset Planning’s permanent scope lock. |
| BUD18-AC-061 | Reservation conservation | Partial conversion/release preserves original=remaining+cumulative conversion+cumulative release; commitment decrease never recreates a reservation and repeated events have one effect. |
| BUD18-AC-062 | Governance snapshots | Return/re-edit/resubmit preserves each immutable submitted attempt, attachment and decision; approval checks the current attempt’s submitter for segregation. |
| BUD18-AC-063 | Finance repeat/reuse | At most one open whole-Plan review per Version; changed financial/eligibility basis stales old evidence, unchanged financial facts permit only explicit reuse, and Active reassessment retains original approval evidence. |
| BUD18-AC-064 | Availability advisory | A 100m approved line with 30m held and 80m planned can pass Finance with 10m availability advisory; a new 80m REQ fails availability. Neither Finance read nor confirmation adds a hold. |
| BUD18-AC-065 | UI fixture correction | December workspace/overview/lines show 160m available and no holds; March conditional REQ shows two HWD reservations 20m / 30m and 110m total available, attributed to Charles/owner service, not Finance. |
| BUD18-AC-066 | UI technical read | Technical-reader March successor uses the actual submitted March timestamp and isolated 80m DHI hold; it neither displays future submission in December nor replaces the Active card with a Draft. |
| BUD18-AC-067 | UI page states | Forbidden renders no Budget header/filter/protected data; server-error remains a valid documented state; module/approval navigation resolves access without hidden-route or modal-on-load behavior. |
| BUD18-AC-068 | Seed ownership correction | A fresh fixture activates HWD as Entity-wide consistently. A populated Active HRMD line is never silently patched; affected real histories use an explicit reviewed migration/governance route. |
| BUD18-AC-069 | Scope and legal boundary | Annual target numerator/category/overlap remain LAW/CFG/PLN-owned; Budget does not infer candidate entitlement, waive statutory prerequisites or force BASE Active. CFG-XD-001 and other positive fixture gates remain visible. |
| BUD18-AC-070 | Adoption evidence | All 70 baseline criteria and 30 prior changes remain traceable;28 usability criteria and 14 changes are added. Release evidence separates approved requirements, implemented contracts, precision/transaction/browser/user results and remaining dependencies. |

### 16.1 Minimum verification coverage

Run owner-contract and database tests for precision, authorization, unique guards, rollback/idempotency, same-line aggregation, concurrent activation/reservation/Finance decisions, historical replay, eligibility and complete annual basis. Browser evidence must exercise all five routes, technical readers, forbidden/loading/failure states, version creation/return/approval, current-versus-historical positions and the three isolated fixture contexts. Shared precision and REQ orchestration suites are release gates; unit stubs cannot stand in for integration evidence.

---


### 16.2 Approved usability coverage

| ID | Approved source | Required result |
|---|---|---|
| BUD19-AC-001 | BUD-UX-001 | No record, initial Draft, initial Submitted, current-with-update, returned and Closed states give each authorised actor the correct next action without duplicate registration or fake current balances. |
| BUD19-AC-002 | BUD-UX-001 | FY is a changeable view choice, not authority; queue Review is navigation only; current allocation remains while updates wait; multiple roles need no switch. |
| BUD19-AC-003 | BUD-UX-002 | The four external approval fields, explicit native FY and verified currency are complete before first Save and add budget lines; no line-total prerequisite yet, extra evidence or unassigned-ID input. |
| BUD19-AC-004 | BUD-UX-002 | One current document link and every immutable earlier submission attachment remain distinct; upload/link failure and unknown save never imply successful registration/submission. |
| BUD19-AC-005 | BUD-UX-003 | Budget line names lead references; Available to means null/all-departments or exact source OU, never user scope, descendant expansion or missing-OU default. |
| BUD19-AC-006 | BUD-UX-003 | Entered total and positive unassigned/excess messages use exact currency-scale arithmetic; no auto-balancing, rounding or new fields. |
| BUD19-AC-007 | BUD-UX-004 | Save scopes and token sequence are explicit; one Submit saves changed valid details/lines and submits the exact confirmed Version, without mandatory manual Save steps. |
| BUD19-AC-008 | BUD-UX-004 | Lost response, partial saved scopes, submit rejection, stale token, duplicate clicks and revoked permission resolve original identities, preserve only permitted work and create no duplicate Budget/submission/decision. |
| BUD19-AC-009 | BUD-UX-005 | Update registered allocation reuses one pending successor and keeps current amounts; type/line identity/transfer/evidence rules remain enforced. |
| BUD19-AC-010 | BUD-UX-005 | Old line identity cannot change; valid zero-protection omission retains prior history; remaining hold/commitment or invalid totals/type block. No destructive historical deletion. |
| BUD19-AC-011 | BUD-UX-006 | Review opens with complete initial allocation or successor amount/evidence changes; fixed proposed Version/baseline and live protected amounts/time are clearly distinct. |
| BUD19-AC-012 | BUD-UX-006 | 90m proposed against95m reserved+committed shows5m Shortfall and blocks approval; positive10m projected availability against80m fixture is exact. Missing live/evidence data never produces Ready. |
| BUD19-AC-013 | BUD-UX-007 | One labelled approval activates registered amounts with explicit external-approval/cash distinction; no Reject, extra activation step, score, checklist or mandatory tab tour. |
| BUD19-AC-014 | BUD-UX-007 | Return preserves exact attempt/document/reason before same-Draft editing;10–500 character guard and submitting-actor no-self-approval revalidate against the current attempt. |
| BUD19-AC-015 | BUD-UX-008 | Registered100m−Reserved20m−Committed60m=Available20m is displayed without double-counting conversion; Available to reserve is not cash or payment. |
| BUD19-AC-016 | BUD-UX-008 | Exact current as_at and historical Version/instant cannot be blended; missing historical position is unavailable, never substituted with current ledger. |
| BUD19-AC-017 | BUD-UX-009 | Each source drawdown reservation remains separately visible with original/still-reserved amounts and exact owner links; two HWD20m/30m holds are not merged. |
| BUD19-AC-018 | BUD-UX-009 | Requires review keeps funds reserved; owner-only recovery cannot create a local release/convert/adjust action or replenish reservations after commitment decreases. Funding activity and Budget history stay separate. |
| BUD19-AC-019 | BUD-UX-010 | Finance whole-plan review remains in Planning;100m approved/80m planned/70m available passes approved comparison with10m advisory while an80m actual reserve fails. Confirmation adds no hold. |
| BUD19-AC-020 | BUD-UX-010 | Complete annual basis remains160m despite Plan130m/available110m or filters. Current line read does not replace frozen Finance evidence, cancel earlier authorisations or enlarge procured scope. |
| BUD19-AC-021 | BUD-UX-011 | Closure variants cover before FY end, remaining/flagged hold, unavailable, ready and Closed; only Budget Approver may act through the existing command and focused confirmation. |
| BUD19-AC-022 | BUD-UX-011 | After FY ends, zero remaining holds permits closure even with active commitments; commit-time race/stale/failure cannot bypass guards. Closed blocks new holds/conversions/increases and does not imply payment. |
| BUD19-AC-023 | BUD-UX-012 | Errors name exact shortfall/field/owner action, distinguish known/partial/unknown outcomes and preserve still-authorised input without overwriting newer values. |
| BUD19-AC-024 | BUD-UX-012 | Keyboard/focus/contrast/narrow-screen and full document/reason reading are verified with representative users; no forced download, clipped blocker or protected-data flash. |
| BUD19-AC-025 | BUD-UX-013 | Actor matrix covers Officer, Approver, Finance, Planner, REQ/Contract consumers, Auditor and technical readers; no extra title-based authority or financial controls from technical read. |
| BUD19-AC-026 | BUD-UX-013 | All-state technical read includes exact approval-shaped routes while ordinary neutral readers remain correctly restricted; counts/search/routes use the same authorisation policy. |
| BUD19-AC-027 | BUD-UX-014 | Needs remains six-field source with no Budget Line or Money; Planning source entry owns selection and Budget owns eligibility; sibling approval/implementation statuses stay explicit. |
| BUD19-AC-028 | BUD-UX-014 | All 70 baseline AC/30 changes and existing seed facts remain; new breach/closure profiles are isolated, actual owner dates/events/assignments are required and no positive end-to-end gate is silently waived. |

## 17. Implementation and test constraints

The implementation baseline is KT-STD-001 §4; the verification protocol is KT-STD-001 §5; release evidence is KT-STD-001 §6.

### 17.1 Additional implementation rules

- Rename the DocTypes to `Procurement Budget`, `Procurement Budget Version`, `Procurement Budget Line` and `Procurement Budget Line Version`, with every route, service, fixture, label, index and test. Verify on a site with ERPNext installed that no name collides.
- Drop `procuring_entity_id` with every dependent parameter, filter, index, fixture and test. Rename `financial_year_id` to `fiscal_year` and repoint it at the ERPNext `Fiscal Year`.
- Add the database-level partial unique index or equivalent guard for BUD-BR-002.
- Register Budget Officer, Budget Approver and Finance Confirmation Officer with `scope_type = Site-wide`. Remove every capability string, custom assignment lookup and Frappe User Permission read from Budget code. The no-self-approval check reads the version's submission audit event.
- Register Budget DocTypes in `kentender_scope_map` per AUTH-ADR-001 v1.7 §5.3, through both hooks, so direct-route access is covered.
- Keep `owner_org_unit_id` on the line version and its BUD-BR-007 eligibility logic. Do not move it into a permission path and do not register it as a scope field.
- Add no ERPNext accounting import, `Cost Center` link or reconciliation job. A static scan shall prove no Budget module imports from `erpnext.accounts`.
- Delete the separate Allocation, treatment, Funding Exception and expenditure artifacts. Preserve no aliases or compatibility response fields.
- Remove the `review_budget_version` and `activate_budget_version` pair; `approve_budget_version` performs the full recheck-and-activate transaction in one call.
- Existing Budget Activation Authority holders may receive a Budget Approver assignment during migration. Budget Reviewer holders are not promoted automatically.
- Where an artboard is marked retired (BUD-DES-12, BUD-DES-13A), do not port it.
- Integrate Planning through §§8–9 only. Align Finance UI with PLN v1.18; Budget owns the line route and read surfaces, not a competing Finance composition. Publish actual code/schema/transaction mapping before release.

### 17.2 Additional minimum coverage

1. Install and migrate on a bench with ERPNext and HRMS present; assert no DocType name collision and that ERPNext `Budget` and `Cost Center` still function.
2. Budget write attempted with no assignment, with an expired assignment and with a Scheduled assignment.
3. Administrator and System Manager technical read succeeds; business mutation is denied.
4. Direct-route access to a Budget, line or task excluded from the actor's register.
5. One-Budget-per-fiscal-year guard under a direct-SQL insert bypassing the command layer.
6. Concurrent reserve and concurrent activation against isolated fixtures.
7. All §15.5 profiles, each reset independently.
8. Successor floor breach, transfer imbalance and line identity immutability.
9. No-self-approval enforced from the submission audit event when one user holds both roles.
10. Owner-scope eligibility proving BUD-BR-007 filters lines without acting as a permission check.
11. Repository scan proving `procuring_entity_id`, `FinancialYear`, `cost_center`, `erpnext.accounts`, `BUDGET_SCOPE_REQUIRED` and `BUDGET_PERMISSION_DENIED` are absent.
12. Browser journeys: Budget Officer registers a baseline and submits; Budget Approver inspects four tabs and returns in one run, approves in another; a read-only actor opens an Active Budget, its lines, a line detail and Funding Activity; a Finance Confirmation Officer uses the Planning task, opens the line, returns and confirms in separate reset profiles; an actor with no Budget assignment sees the Forbidden state with no disclosure.

### 17.3 Additional release evidence

- Static scan showing no removed concept, expenditure artifact, or leftover Budget Reviewer, Budget Activation Authority, Budget Viewer or `Awaiting Activation` reference.
- Migration succeeds on a copy of real data, including the DocType rename.
- Planning read/decision/annual-basis tests pass; REQ single, combined, same-line shortfall, rollback and duplicate-correlation contract tests pass separately.
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
- Do not create a reservation at any Procurement Planning event. Reservation begins only at successful Procurement Requisition authorisation.
- Do not let `check_plan_affordability` write, lock, issue a token or produce a ledger event.
- Do not make the within-currently-available verdict blocking.
- Do not permit partial REQ all-source reservation or silent line substitution. Do not collapse distinct drawdown rows into one reservation.
- Do not add an accounting-derived outstanding-commitment or actual-expenditure measure, forecast, utilisation score or an `Unavailable` placeholder. Retain Budget-owned Committed as defined in §5.
- Do not add an editable Budget title, classification, separate purpose, generic description, source type, effective date, authority name, contact, note, justification or miscellaneous attachment.
- Do not allow downstream raw SQL or ORM reads of Budget tables.
- Do not allow client-only permission, total, floor, availability or lifecycle enforcement.
- Do not permit direct edits of Active, Superseded or Closed data.
- Do not rename the existing Budget or line identifiers.

---

## 19. Traceability, full changes and remaining dependencies

### 19.1 Governing inputs and adoption scope

This successor consolidates approved BUD v1.8 and all fourteen decisions in BUD Usability Amendment v0.1 approved13 September 2026. Approved NDS v1.12 owns the six-field requirement; Strategy v1.8 has separately consolidated its approved usability direction. Planning v1.19 and Requisitions v1.8 retain their separate proposed status. None is approved or deployed merely by this Budget document. Use current operative sections here over historical BUD18 register wording.

| Input | Use / limit |
|---|---|
| BUD-CHG-001 v1.7 | Full inherited Budget domain, governance, routes, artboards and 45 acceptance criteria, corrected here. |
| PLN-CHG-001 v1.18 §§4.1, 5.3, 5.4, 5.5.3, 7–8, 15, 17 | Financial-basis validation/reuse, annual denominator, precision, source OU and downstream scope boundaries. |
| PLN-CHG-001_FOLLOW_UPS.md FU-23, FU-30 and retired FU-02 | Provider amendments and precision; human reference is reported implemented, but current repository was not supplied for verification. |
| CFG-CHG-002 v0.10, approved | Configuration owner contracts, funding sources, explicit native mapping, immutable rules and CFG-XD-001 date dependency. |
| SEED-001 v1.3, approved | Two-department/two-reservation lineage, BASE/READY separation, named authority and shared chronology. HWD owner inconsistency is explicitly corrected in this Budget successor. |
| LAW-REG-001 v1.1, approved | Statutory correction and outstanding primary verification; document approval does not verify production law. |
| AUTH-ADR-001 v1.7 / KT-STD-001 v1.4 supplied baseline | Responsibility hooks, technical read and common UX/implementation rules. FU-27's later shared technical-read citation cleanup remains separately owned. |
| REQ-CHG-001 v1.7, supplied | Authorisation owns reservations; one per drawdown line; complete authorisation atomicity and pre-consumption reversal. Matching v1.8 caller amendment remains to be consolidated. |

The body is the to-be-implemented Budget contract. Historical references in §1 are disposition history, not permission to retain deleted executable concepts. Original files remain historical baselines. No current application behavior, code mapping or test result is asserted from these documents alone.

### 19.2 Full change register for re-implementation

The 30 BUD18 rows remain the prior approved baseline change set; the 14 BUD19 rows below incorporate the approved usability decisions. Total: **44 change rows**. Original counts and old screen terminology in historical rows are traceability, not an alternative operative contract.

| ID | Prior issue / gap | Complete required change | Document locations | Verification references |
|---|---|---|---|---|
| BUD18-CHG-001 | Residual Planning reservation language | Purpose, ownership, Finance interaction and service arguments place holds only at successful REQ authorisation; no Budget Finance task. | §§2–3, 7–9, 12.6 | BUD18-AC-011, 014, 058, 063 |
| BUD18-CHG-002 | No transactional Finance provider | Add validate_plan_affordability_for_decision with owner-held serialization through caller commit and exact expected revision checks, without financial writes. | §§4.8, 8.2A, 9.1 | BUD18-AC-046–047 |
| BUD18-CHG-003 | Annual denominator contract missing | Add complete approved annual Budget basis, all lines, exact Version/currency/count/digest; no Plan-total or net-availability denominator. | §§4.8, 8.2B, 9.1 | BUD18-AC-048 |
| BUD18-CHG-004 | Annual denominator could change in an unused line | Include expected annual basis in a dependent decision and serialize the whole Budget root; no per-used-line-only guard. | §8.2A | BUD18-AC-049 |
| BUD18-CHG-005 | Current and historical bases conflated | Explicit current versus exact historical Version/instant; preserve authoritative snapshot/precision and fail unreproducible replay. | §§4.8, 5, 8.2B, 9.1, 12.3 | BUD18-AC-050 |
| BUD18-CHG-006 | Float/minor-unit/precision boundary unspecified | Exact decimal-string currency units; at least 18 integral digits; supported scale, no rounding/epsilon, malformed/overflow rejection. | §4.8; all monetary services | BUD18-AC-051–052 |
| BUD18-CHG-007 | No Budget currency provider contract | Expose retained CurrencyBasis using verified native Company/precision mapping; no editable precision or inferred Company/accounting integration. | §§3, 4.1, 4.8, 9.1 | BUD18-AC-053 |
| BUD18-CHG-008 | Source-OU input ambiguous or treated as user scope | Require explicit source department for Need and direct sources; exact owner or Entity-wide eligibility after actor authorization; no tree inference. | §§4.4–4.5, 5 BR-007, 9.1 | BUD18-AC-009, 055 |
| BUD18-CHG-009 | Budget line human reference absent from specification | Return reference separately from root and exact Version IDs; preserve implemented reference behavior reported in FU-02. | §9.1 | BUD18-AC-054 |
| BUD18-CHG-010 | Catalogue changes could rewrite history or evade validation | Use CFG owner eligibility/decision contracts; disabling affects current use, historical IDs/labels remain; immutable line identity requires new line. | §§4.8, 9.1 | BUD18-AC-056 |
| BUD18-CHG-011 | Lifetime one-review-per-Version wording | At most one open whole-Plan review; immutable completed reviews, explicit reuse, basis staleness and Active reassessment through PLN. | §§1.1, 7, 8.1–8.2A, 12.6 | BUD18-AC-063 |
| BUD18-CHG-012 | Available funds confused with Planning affordability | Within-approved blocking; within-available advisory for Planning, availability blocking for REQ; preserve original/current evidence separation. | §§8.1–8.3, 12.6 | BUD18-AC-012–013, 064 |
| BUD18-CHG-013 | Reservation lacks owning REQ/drawdown identity | Persist exact REQ Version, drawdown/line, authorisation event and source OU; amount is authorised draw, not necessarily original Plan total. | §§4.5, 5 BR-011, 8.3 | BUD18-AC-058 |
| BUD18-CHG-014 | One-reservation-per-allocation lifetime rule | Uniqueness belongs to authorisation/drawdown line; later eligible draw against remaining original allowance has its own lineage. | §§4.5, 5 BR-011, 8.3 | BUD18-AC-058 |
| BUD18-CHG-015 | Each row could pass availability while their sum fails | Aggregate full request by Budget Line under locks; retain distinct drawdown reservations and exact shared-line shortfall. | §§8.3, 9.1, 15.5 | BUD18-AC-057 |
| BUD18-CHG-016 | Finance-task funding inputs and weak check/retry semantics | Replace with trusted REQ owner context; full-array bound expiring token, payload-aware idempotency and unique effect guard. | §§8.3, 9.1, 13 | BUD18-AC-018, 058–059 |
| BUD18-CHG-017 | All-or-none did not name complete owner boundary | REQ decision, Planning drawdown/scope guard, reservation set, handoff and outbox commit together; no partial orchestration. | §§8.3–8.4 | BUD18-AC-016, 047, 060 |
| BUD18-CHG-018 | Authorised correction/release could bypass immutable scope | Exact pre-consumption revocation, retained old evidence and governed successor; consumed handoff bars shortcut; release never resets scope lock. | §§8.1, 8.4 | BUD18-AC-060 |
| BUD18-CHG-019 | Conversion bound and release semantics ambiguous | Remaining-hold bound plus event-debit conservation; commitment decrease does not re-reserve; additional increase uses current available funds. | §§4.6, 8.4 | BUD18-AC-020–022, 061 |
| BUD18-CHG-020 | User-role wording omitted legitimate service effects | Separate live business-role writes from authenticated REQ/Contract owner-command effects; no service financial discretion or Draft reads. | §§3, 5 BR-001, 7, 9 | BUD18-AC-004, 038 |
| BUD18-CHG-021 | Return could obscure earlier submitted content | Retain each submission-attempt snapshot/document/decision; no-self-approval uses current submission authority. | §§6, 12.5, 14 | BUD18-AC-028, 062 |
| BUD18-CHG-022 | Closed Budget and audit semantics incomplete | Closed budget blocks new obligations but retains existing commitments and authorized decreases; reads/replays create no effective financial events. | §§5–6, 14 | BUD18-AC-018, 036, 050 |
| BUD18-CHG-023 | HWD seed owner excludes DHI laptop source | Make fresh canonical HWD line Entity-wide; never patch an Active real line’s owner in place; record data reconciliation gate. | §§11, 15.3, 19.3 | BUD18-AC-055, 068 |
| BUD18-CHG-024 | December artboards show Planning-created 80m hold | Default workspace/overview/lines/activity use 160m available and zero holds; conditional March screen shows two 20m / 30m HWD reservations. | §§11.1, 11.4–11.7, 15.4–15.4A | BUD18-AC-023, 065 |
| BUD18-CHG-025 | Funding event attributed to Finance; collapsed laptop reservation | REQ authorisation/Charles/service provenance; distinct HRMD and DHI rows with owner links; no manual Budget funding action. | §§11.6A–11.7, 12.4, 15.4A | BUD18-AC-016, 065 |
| BUD18-CHG-026 | Technical-read successor dated in future; revision floor borrowed from default | Use declared isolated March DHI 80m hold/Transfer scenario; retain v1.7 read-only route for technical actors. | §§11.1A, 11.8–11.15, 15.6 | BUD18-AC-045, 066 |
| BUD18-CHG-027 | Forbidden artboard painted header/filters; Server error row detached | Authorization-first inline Forbidden, valid four-state table and accessible navigation with server-denied approval surface. | §§10, 11.16, 12.1 | BUD18-AC-042–044, 067 |
| BUD18-CHG-028 | Seed allowed positive claims without prerequisite distinction | Separate BASE/conditional REQ/isolated revision; preserve SEED v1.3 and CFG-XD-001/legal/precision gates; never force BASE Active. | §15; §19.3 | BUD18-AC-023, 029–030, 069–070 |
| BUD18-CHG-029 | Follow-up ownership stale; funding catalogue called ownerless | Use approved CFG v0.10/LAW v1.1/SEED v1.3 and PLN v1.18; REQ/TPR/NDS/Contract/cross-module precision remain explicit dependencies. | §§3, 19.1–19.3 | BUD18-AC-070 |
| BUD18-CHG-030 | Acceptance IDs scattered; no complete reimplementation table | Map all 45 v1.7 criteria, add 25, and provide this full 30-row change register with locations and verification references. | §§16, 19.2, 20 | BUD18-AC-001–070 |
| BUD19-CHG-001 | BUD-UX-001: Workspace and pending work (§§10–12.1) | Cover no record, initial Draft, initial submission, current-with-update, returned and Closed states for Officer, Approver and readers. Keep one existing queue, Review navigation and changeable FY filter. | §§7.1, 10, 11.1B, 12.1 | BUD19-AC-001–002; Every actor finds the next step; no duplicate registration, invisible initial work, false current allocation or role switch. |
| BUD19-CHG-002 | BUD-UX-002: Registration and external evidence (§§4.1–4.2, 11.2, 12.2) | Record approved allocation; Approved allocation total; explicit year/currency; remove unassigned-ID input. Retain one exact approval document and make submit-time completeness explicit. | §§9.3, 11.2, 12.2 | BUD19-AC-003–004; No extra fields or appropriation workflow; valid partial save versus complete submit unambiguous; submitted evidence survives Draft replacement. |
| BUD19-CHG-003 | BUD-UX-003: Budget Line language and eligibility (§§4.3–4.4, 5, 11.3, 11.5–11.6) | Names before IDs; Available to / All departments; Amount; exact running total and mismatch labels. Source department remains exact domain eligibility, not user scope. | §§4.9, 11.3, 11.5–11.6A | BUD19-AC-005–006; No descendant expansion or missing-source fallback; all line facts remain; totals use exact Money and no silent rounding. |
| BUD19-CHG-004 | BUD-UX-004: Save, submission and correction (§§9.2, 11.3, 11.14–11.15, 12.2) | One user Submit for review includes pending valid edits via explicit existing command sequencing. Define scope, upload/link handling and original-result recovery; returned work opens the same Draft. | §§9.3, 11.3, 11.14–11.15, 12.2 | BUD19-AC-007–008; Save failure, partial success, unknown result, stale token and retry produce no duplicate record/attempt or overwritten history; no invented cross-command atomicity. |
| BUD19-CHG-005 | BUD-UX-005: Successor update and line identity (§§4.4, 5–6, 11.14–11.15, 12.2–12.3) | Update registered allocation; Type of change; reuse one pending successor; current record remains. Existing identity immutable. Distinguish permitted successor omission under BR-020 from deleting history. | §§5–6, 11.14–11.15, 12.2–12.3 | BUD19-AC-009–010; Amount-only edits on old lines; new purpose/scope/source uses new line. Transfer balances; omission allowed only without remaining reservation or active commitment and retains lineage. |
| BUD19-CHG-006 | BUD-UX-006: Changes-first review and live impact (§§11.8–11.11, 11.13, 12.5) | Show changes, external evidence and protected-amount comparison on opening review. Reserved + committed replaces Current floor; Available after update replaces Headroom; real blockers replace green checklist. | §§9.4, 11.8–11.13, 12.5 | BUD19-AC-011–012; Exact submitted Version and baseline; current protection as-at separate; all changed amounts/evidence and complete lines inspectable; guards recheck at approval. |
| BUD19-CHG-007 | BUD-UX-007: Approval and Return meaning (§6, §§11.8, 11.13, 12.5) | Approve registered allocation / Approve allocation update; visible activation consequence. Return for correction with existing reason and immutable attempt history. No repeated generic approval confirmation. | §§6, 9.3, 11.8, 11.13, 12.5 | BUD19-AC-013–014; One decision activates; no public-budget appropriation, cash release, Reject or extra stage; submitter cannot approve own submission. |
| BUD19-CHG-008 | BUD-UX-008: Understandable funding position (§§4.5–4.8, 5, 11.1, 11.4–11.6A) | Registered allocation; Reserved for requisitions; Committed to contracts; Available to reserve. Explain partial conversion and show coherent current/historical context. | §§4.9–5, 11.4, 11.19 | BUD19-AC-015–016; 100m−20m−60m=20m; no double counting, cash/payment implication or old-approved/live-ledger blend. |
| BUD19-CHG-009 | BUD-UX-009: Reservations, issues and event reading (§§4.5–4.7, 8.4, 11.6A–11.7A, 12.4) | Requisition/source names first; original/still-reserved amounts; Requires review—funds remain reserved. Read-only owner links; separate funding activity and Budget history. | §§11.6A–11.7A, 11.19, 12.4 | BUD19-AC-017–018; One reservation per drawdown line preserved; no automatic release, manual amount input, guessed route or recreated hold after commitment decrease. |
| BUD19-CHG-010 | BUD-UX-010: Finance/Planning and annual-basis boundary (§§7–9, 11.17, 12.6) | Keep whole-plan Finance work in Planning; live line view is separate from frozen review evidence. Explain approved-versus-planned blocking and available-funds advisory; full annual denominator unchanged. | §§8–9, 11.17, 12.6 | BUD19-AC-019–020; 100m approved/80m planned/70m available stays within-approved with 10m advisory; no Finance reservation or Budget Finance screen; annual basis stays 160m. |
| BUD19-CHG-011 | BUD-UX-011: Year-end closure completeness (§§6, 9.2, 10–12) | Provide Approver closure entry, pre-year-end, ready, held, unavailable and Closed states on existing surfaces. Focused closure confirmation and actual guard failure. | §§9.4, 11.18, 12.8 | BUD19-AC-021–022; No new role/workflow. Remaining reservations including Needs Attention block; active commitments alone do not. No payment claim; close revalidates at commit. |
| BUD19-CHG-012 | BUD-UX-012: Errors and shared readability (§§11.16, 12.7, 13) | Plain exact recovery, meaningful waiting/unknown states, structured evidence and readable responsive tables; preserve permitted input, focus and access protection. | §§9.3, 11.20, 12.7, 13 | BUD19-AC-023–024; No false zero/success, lost Draft or forced download. Keyboard/contrast/narrow-screen checks and user comprehension recorded. |
| BUD19-CHG-013 | BUD-UX-013: Complete actor and technical read coverage (§§7, 10, 11.1A, 12.2, 12.5) | Implement full actor matrix; reconcile blanket approval-route denial with AUTH v1.7 all-record technical read; no decision controls from technical access. | §§7.1, 10, 11.1A–11.1B, 12.2, 12.5 | BUD19-AC-025–026; Ordinary users, Approvers and technical readers get distinct correct outcomes across all statuses; no protected-data flash or title-based AO authority. |
| BUD19-CHG-014 | BUD-UX-014: Owner and fixture reconciliation (§§3, 15, 19.3) | Correct selected-line ownership to Planning source entry under approved NDS v1.12; retain approved source facts and isolated scenario chronology. Declare new breach/closure variants without merging March/December cases. Update completed sibling-document references without asserting implementation closure. | §§3, 15.8, 19.1–19.3 | BUD19-AC-027–028; No Need funding field, invented REQ authorisation/contract event, altered HWD scope in live history or forced positive end-to-end date evidence. All 70 prior AC and 30 change rows remain traceable. |

All shortened `BUD18-AC` ranges in the final column refer to §16. Approval applies to this complete successor, including the reconciled fixture and UI rules; individual rows are not a second specification.

### 19.3 Remaining implementation and sibling-document register

| ID | Outstanding item | Owner / required evidence | Status and effect |
|---|---|---|---|
| BUD18-XD-001 | FU-23 provider adoption | BUD/PLN: inspect actual service/schema, publish mappings, add display/decision/annual-basis tests, prove compatible locking and caller rollback. | Documented here; implementation and integration unverified. Attach evidence to the implementation tracker; do not mark code Done from this MD. |
| BUD18-XD-002 | FU-30 cross-module precision | BUD/NDS/REQ/PLN: shared exact-decimal suite and storage/arithmetic scan; replace float/epsilon paths; reconcile existing persisted values with authoritative evidence. | Release prerequisite. No automatic rounding migration or assertion that binary-float history can be recovered exactly. |
| BUD18-XD-003 | Explicit Company/currency/UOM metadata mapping | CFG/BUD/REQ: inspect repository/native owner fields; declare supported scales and token lifetime; demonstrate no accounting-ledger dependency. | Implementation prerequisite; no inferred defaults/native fields. |
| BUD18-XD-004 | REQ v1.8 / TPR v0.8 matching caller amendment (FU-25) | Adopt owner drawdown naming, scope/hold errors, correction outcome and requester follow-up, exact reservation mappings and one complete-array token semantics. Coordinate old REQ prose saying per-line returned tokens; no dual response contract. | REQ v1.8 has been produced as a proposed sibling successor; its approval and TPR/caller implementation remain separate. This Budget successor does not approve or deploy them. |
| BUD18-XD-005 | NDS source/eligibility integration | Approved NDS v1.12 now documents its source/disposition/readable Planning rules. Budget Line selection belongs to Planning, never the Need. Verify exact quantity/source handoff and eligibility without a Need Money field. | Sibling specification completed; implementation evidence remains outstanding. |
| BUD18-XD-006 | HWD owner mismatch in already populated data | BUD/SEED/REQ/PLN: compare actual line history and references; rebuild only authorized disposable fixtures or prepare a reviewed new-line/governed-successor correction for retained data. | No silent Active-line edit. Document affected IDs, evidence and migration outcome before declaring seed/data alignment. |
| BUD18-XD-007 | Canonical date/production-rule prerequisites | CFG/LAW/SEED: resolve CFG-XD-001 and LAW v1.1 verification items; preserve verified applicability evidence. | Conditional positive end-to-end claim remains blocked where these prerequisites fail. This is not a new Budget legal interpretation. |
| BUD18-XD-008 | Exact isolated revision hold event | SEED/REQ: freeze a valid authorisation event before 15 Mar 13:10 for the independent DHI 80m scenario, with live authority and lawful/applicable prerequisites. | Artboard/provider-test scenario specified; integrated execution requires owner evidence. Do not borrow laptop events or invent a Finance hold. |
| BUD18-XD-009 | Contract conversion/adjustment integration | Contract owner: authenticated event schemas, exact lineage, conservation, cancellation and closed-budget restrictions, idempotency and tests. | Keep actions unavailable until the approved caller and evidence exist; no manual Budget substitute. |
| BUD18-XD-010 | Shared standard/citation and fixture adoption | KT-STD/SEED owner: retain Budget actors and scenario index; perform FU-27 technical-read citation cleanup with the actual controlling standard. | Editorial/shared-fixture follow-up; no new technical-read right and no claim that an unseen later standard was reviewed. |
| BUD18-XD-011 | Full UI/artboard implementation and review | Budget UI owner: implement the approved §§11–12 usability compositions, including pending work, changes-first review, closure and all-state task reading; verify keyboard/focus, narrow-screen amounts, full evidence and representative-user understanding. | Required implementation evidence. This document corrects completeness; it does not claim user-tested experience or completed artboards. |
| BUD19-XD-001 | Save/submit/upload recovery | BUD UI/service/file owner: inspect actual token granularity, reply IDs, file-link transaction and authorised idempotent outcome replay; prove §9.3 including partial scope saves and browser reload. | Implementation gate; no claim of atomic multi-save or fabricated current endpoint. |
| BUD19-XD-002 | Closure composition and concurrent guards | BUD/Contract/REQ owners: implement existing command UI; prove before-year-end/held/unavailable/ready/Closed, concurrent financial mutation and original-result replay; declare valid future test assignments/events. | Documentation complete; executable closure and owner reconciliation evidence required. |
| BUD19-XD-003 | Historical versus proposed omission and evidence | BUD migration/read owner: map omitted successor membership without deleting prior line identities, attempt snapshots or attachments; test live zero-protection revalidation and exact historical replay. | No blanket delete or silent unlock of approved line identity. |

Future facilities remain owned by their approved change units: accounting/expenditure integration, automated financial-system reconciliation, expanded tender/scope-amendment handling and unsupported multi-year funding are not enabled by this document. Missing owner functionality must produce an explicit supported-state limit, not a manual bypass.

## 20. Approval effect

The Project Owner approved BUD Usability Amendment v0.1, BUD-UX-001–014, on **13 September 2026** and directed incorporation into the full document. **BUD v1.9** consolidates the approved v1.8 baseline and these approved changes as one implementation reference, superseding v1.8 and earlier conflicting Budget specifications. No separate usability overlay must be reconciled by implementers.

This complete successor retains the existing domain, 26 business rules, seven governance commands, fourteen funding/read contracts, 28 stable error codes, all 70 prior acceptance IDs and 30 previous change rows. It adds 28 usability criteria and 14 change rows, for **98 acceptance criteria** and **44 change-register rows**, with 14 explicit owner/implementation dependencies. Exact Money, approval evidence, source eligibility, annual-budget basis, reservation/commitment protection and caller ownership are unchanged except the explicit corrected Need/Planning selection wording.

Approval records requirements/design decisions, not deployed code, completed migration, passed consumer/transaction/browser tests, representative-user acceptance, current-law verification or closure of §19.3. Keep conditional downstream fixture and Contract integration gates visible. Financial service effects remain governed; there is no manual workaround, new appropriation step or accounting integration. Other modules retain their own approval status.
