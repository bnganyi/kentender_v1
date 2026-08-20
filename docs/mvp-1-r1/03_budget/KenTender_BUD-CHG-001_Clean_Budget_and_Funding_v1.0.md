**REVISION LEDGER CHANGE UNIT**

Clean Budget & Funding

Greenfield procurement-funding control, baseline registration and implementation authority

| **Control**            | **Value**                                                            |
| ---------------------- | -------------------------------------------------------------------- |
| Document ID            | BUD-CHG-001                                                          |
| Version                | 1.0                                                                  |
| Date                   | 19 August 2026                                                       |
| Status                 | Proposed for product-owner approval                                  |
| Module                 | Budget & Funding                                                     |
| Implementation posture | Clean build; no migration, compatibility layer or legacy seed repair |

**Controlling decision:** Retain Budget & Funding as the procurement-funding control module. It registers an already authorised budget baseline, controls available funds through reservations and commitments, and provides auditable finance decisions. It does not approve appropriations, replace the financial system, or reserve funds at Departmental Need acceptance.

# Document map

- Decision, scope and legal boundary
- Corrected domain language, formulas and lifecycles
- Roles, permissions and delegated finance authority
- Requirements and screen designs
- Integration, seed and implementation contracts
- Acceptance criteria, smoke gates and traceability

# 1\. Decision and purpose

BUD-CHG-001 is the single implementation authority for cleaning Budget & Funding. It replaces conflicting legacy Budget requirements, Stitch prompts, Cursor packs and demo-data instructions with one integrated Revision Ledger unit containing product requirements, screen contracts, seed data, implementation controls and testable completion evidence.

**Release classification:** MVP-blocking stabilization. The module must be correct before Finance confirmation in Procurement Planning and before formal Procurement Requisition, Tender, Award or Contract funding controls are enabled.

## 1.1 Outcomes

- An independently operable module with no runtime or seed dependency on the deleted legacy Demands package or Procurement Home.
- One explicit PE and financial-year funding context, resolved from configuration rather than inferred from the first record.
- A registered, verified and activated approved-budget baseline that KenTender may use for procurement control without claiming to approve the public budget.
- Hard, atomic funding controls based on approved Budget Lines, Funding Reservations and Procurement Commitments.
- Correct calculations that never subtract actual expenditure twice.
- Neutral read access separated from authority to register, verify, activate, reserve, revise or commit funds.

## 1.2 In scope

- Budget baseline registration, verification and activation for procurement use.
- Budget Lines, optional Strategy references, sources of funds and approved amounts.
- Finance check-and-reserve, revalidation, release and later conversion to commitment.
- Controlled Budget Revisions and append-only Funding Ledger events.
- Operational funding position, exceptions, neutral records and audit history.
- Configuration-first seed fixtures, integration contracts and automated tests.

## 1.3 Explicit exclusions

- No appropriation, budget enactment, exchequer release, cash-management, general-ledger, payment or accounting approval workflow.
- No reservation when a Departmental Need is accepted for planning.
- No duplicate Allocation object: a Budget Line's approved amount is the allocation.
- No Budget Line Value Treatment, Budget Value Treatment, Public Value Objective, planned-treatment or funding-treatment questionnaire.
- No mandatory one-primary Strategy target; approved Strategy references are zero or more, according to the source budget.
- No advanced Funding Performance dashboard, forecasting, achievement scoring or manually simulated expenditure.
- No migration, legacy alias, dual read, shadow write, fallback route, compatibility seed or repair script.

## 1.4 Completion standard

The change is complete only when a fresh environment installs, migrates, seeds and opens Budget & Funding; the Ministry of Health and Kisumu contexts remain isolated; all funding mutations are server-authorised, atomic, idempotent and audited; and no deleted legacy module is importable by Budget code, hooks, seeds or tests.

# 2\. Problem statement and correction rationale

| **Inherited problem**                                     | **Required correction**                                                                                         | **Reason**                                                        |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Budget UI implies KenTender approval of the public budget | Register evidence of the externally authorised baseline, verify it, then activate it for procurement use.       | Avoids inventing a statutory appropriation gate.                  |
| Reservation attached to Demand acceptance                 | Create no hold at Departmental Needs. Reserve only during the Plan Item Finance-confirmation stage.             | Planning needs precede formal procurement funding commitment.     |
| Separate Allocation model                                 | Use Budget Line approved amount as the allocation.                                                              | Removes duplicate balance sources.                                |
| Actual expenditure subtracted again                       | Treat actual expenditure as part of total commitment and derive outstanding commitment separately.              | Prevents understated available balances.                          |
| Generic treatments and mandatory target                   | Remove treatment records and permit zero or more approved Strategy references.                                  | Matches the source budget rather than forcing invented semantics. |
| Admin role inflation and first-PE fallback                | Neutral read for Administrator; operational actions require explicit PE/FY capability and live task assignment. | Prevents cross-entity leakage and unauthorised finance acts.      |
| Dashboard overreach                                       | Retain an operational funding-position read surface; defer advanced performance analytics.                      | Keeps MVP focused on enforceable control.                         |
| Legacy module and seed imports                            | Delete Demands/Home dependencies and rebuild seeds after Configuration and Governance.                          | Fresh installations must be deterministic.                        |

# 3\. Legal and public-finance grounding

This is a system-control interpretation, not a substitute for entity-specific legal advice or an authoritative financial-system rulebook. Kenya's procurement and public-finance framework makes the Accounting Officer accountable for lawful, authorised and budget-compliant expenditure. KenTender therefore enforces approved-budget boundaries while delegating operational finance tasks only where a valid PE/PFM assignment exists.

| **Authority**                                                                | **Relevant rule**                                                                                                                                                                | **KenTender consequence**                                                                                                                               |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Constitution of Kenya, Articles 201 and 227                                  | Public finance requires openness, accountability and prudent use; procurement must be fair, equitable, transparent, competitive and cost-effective.                              | Funding decisions and balance changes require transparent evidence and cannot become hidden procurement criteria.                                       |
| PPADA 2015, section 44                                                       | The Accounting Officer is primarily responsible for compliance and must ensure procurement is within the entity's approved budget and proper financial controls are followed.    | Accounting Officer accountability is retained; technical or finance roles do not gain universal final authority.                                        |
| PPADA 2015, section 53                                                       | Annual procurement plans must be realistic, within the approved budget and integrated with the applicable budget process.                                                        | Plan Items may proceed only against an active approved Budget Line and a valid Finance confirmation.                                                    |
| PPAD Regulations 2020, regulations 40–42                                     | Departmental and consolidated annual procurement plans follow the budget process and prescribed planning format.                                                                 | Budget context feeds planning; it does not become a second procurement plan.                                                                            |
| PPAD Regulations 2020, regulations 49, 52 and 54                             | The e-procurement system supports internal workflow, procurement planning and requisition through the procurement function.                                                      | The formal Procurement Requisition is downstream of the Approved Plan Item; it revalidates inherited funding rather than creating a second reservation. |
| PFM Act 2012, sections 68 and 149                                            | National and county Accounting Officers are accountable for lawful, authorised, effective, efficient, economical and transparent resource use and applicable financial controls. | PE type and authority are configuration data; Finance actions require documented delegation and audit.                                                  |
| PFM National Government Regulations 2015, regulation 51                      | Commitments are controlled against approved spending and procurement plans and approved allocations/allotments.                                                                  | Commitment conversion and revalidation are hard server controls, not optional UI warnings.                                                              |
| PFM National/County Government Regulations, unauthorised-spending provisions | Funds earmarked for specific activities may not be used for unrelated purposes.                                                                                                  | A reservation and commitment remain tied to the approved Budget Line and purpose unless an authorised Revision changes the baseline.                    |

**Authority boundary:** A Budget Officer or Finance Officer performs a named operational check under a configured delegation. The role is not a universal statutory approval authority. The Accounting Officer remains accountable, and any entity-specific Finance Authority or Head of Finance capability must be evidenced, scoped and effective-dated.

# 4\. Module boundary and lifecycle position

## 4.1 Budget & Funding owns

- The procurement-control representation of an approved budget baseline and its evidence.
- Budget Lines, approved amounts, source/classification metadata and optional Strategy lineage.
- Available, reserved and committed positions derived from an append-only funding ledger.
- Finance checks, reservations, releases, revalidations and commitment conversions.
- Controlled Budget Revisions that preserve every prior active baseline.
- Authoritative expenditure snapshots when, and only when, a configured finance integration supplies them.

## 4.2 Budget & Funding does not own

| **Excluded responsibility**                            | **Owner**                              | **Permitted relationship**                                                                      |
| ------------------------------------------------------ | -------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Appropriation, enacted budget and release authority    | Authoritative PFM/financial process    | KenTender stores an approved source reference and evidence; it does not create the authority.   |
| Strategy hierarchy and targets                         | Strategy Alignment                     | Budget Lines may reference zero or more approved Strategy nodes/targets read-only.              |
| Plain-language internal need                           | Departmental Needs                     | No reservation is created. Accepted Needs are inputs to planning.                               |
| Plan Item design, procurement method and Plan approval | Procurement Planning                   | A completed Plan Item requests Finance confirmation and an atomic reservation.                  |
| Formal procurement request                             | Procurement Requisition                | Eligible Approved Plan Item inherits and revalidates the reservation.                           |
| Solicitation and award                                 | Tender / Award                         | Funding context is inherited; material value changes trigger revalidation.                      |
| Contract obligation and payments                       | Contract Management / financial system | Contract creation converts reservation to commitment; expenditure is authoritative-system data. |
| PE/FY, roles and delegation                            | Configuration and Governance           | Budget consumes explicit scope and capability assignments.                                      |

## 4.3 Correct end-to-end sequence

**Lifecycle:** Strategy Alignment → Budget & Funding → Departmental Needs → Procurement Planning → Procurement Requisition → Tender → Award → Contract. Departmental Need acceptance does not reserve funds. Finance confirmation occurs after Plan Item completion and before professional Plan review; later material events revalidate the same funding lineage.

# 5\. Canonical terminology and removal register

| **Term or artifact**                                 | **Canonical treatment**                                        | **Disposition**                                                          |
| ---------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Allocation                                           | Budget Line approved amount                                    | Keep the meaning; do not create a separate Allocation object.            |
| Funding Reservation                                  | Temporary hold for one Plan Item/procurement lineage           | Keep. Create atomically at Finance confirmation.                         |
| Procurement Commitment                               | Current contractual obligation after award/contract            | Keep. Convert from reservation; support partial/multiple commitments.    |
| Actual expenditure                                   | Authoritative-system payments included within total commitment | Read-only snapshot when integrated; never manual/simulated in live data. |
| Outstanding commitment                               | Committed amount less actual expenditure                       | Derived display value.                                                   |
| Budget Line Value Treatment / Budget Value Treatment | No replacement                                                 | Remove schema, services, screens, seeds and tests.                       |
| Mandatory primary Strategy Target                    | Zero or more approved Strategy references                      | Correct; source budget determines applicability.                         |
| Funding Performance dashboard                        | Operational Funding Position                                   | Strip to balances, exceptions and freshness; defer advanced dashboard.   |
| Budget approval                                      | Baseline verification and activation for procurement use       | Rename so KenTender does not claim appropriation authority.              |

# 6\. Canonical domain model

| **Object**             | **Purpose**                                                       | **Mandatory controls**                                                                                              |
| ---------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Budget                 | Stable PE/FY identity for the registered approved baseline.       | PE, FY, currency, title, authoritative reference/evidence, current version, status.                                 |
| Budget Version         | Immutable baseline approval boundary.                             | Version, source date, verified/activated actor, effective dates; no direct Active edit.                             |
| Budget Line            | The approved allocation available for a defined purpose.          | Generated reference, approved amount, fund source, OU/cost centre, classification, purpose, optional Strategy refs. |
| Funding Reservation    | Active hold against one Budget Line and procurement lineage.      | Correlation key, original/remaining amount, status, Plan Item, authority evidence, timestamps.                      |
| Procurement Commitment | Current legal/contractual obligation against a Budget Line.       | Reservation lineage, contract/award reference, total commitment, status and version.                                |
| Expenditure Snapshot   | Read-only value from the configured authoritative finance source. | Source, as-of time, amount, commitment reference and integrity metadata; no manual entry.                           |
| Budget Revision        | Controlled proposed change to an Active baseline.                 | Type, before/after lines, external authority/evidence, reason, impact and lifecycle.                                |
| Funding Ledger Event   | Append-only financial-control evidence.                           | Event type, line, amount, actor/capability, correlation key, before/after balances, timestamp.                      |
| Funding Exception      | Typed unresolved mismatch or invalidation.                        | Reason, affected lineage, severity, owner, state and resolution evidence.                                           |

## 6.1 Canonical calculations

**Line Available:** Approved Amount − Active Reservation Balance − Current Total Commitment

**Outstanding Commitment:** Current Total Commitment − Actual Expenditure. Actual expenditure is not subtracted again from Line Available because it is already included in Current Total Commitment.

- Line Reserved is the sum of remaining balances on active, unconverted reservations.
- Line Committed is the sum of current total commitments, including the portion already paid.
- Budget totals are derived from Budget Lines and ledger positions; users never key calculated totals.
- All monetary arithmetic uses fixed decimal precision and one Budget currency. Cross-currency funding uses separate governed lines or an approved later integration.
- Negative available, reservation or commitment values are prohibited.

## 6.2 Core invariants

- A Budget belongs to exactly one PE and one FY; a Budget Line belongs to one Budget Version.
- Only an Active Budget Version may support new funding reservations.
- A reservation, commitment and expenditure snapshot never cross PE, FY, currency or Budget Line boundaries.
- One correlation key creates at most one effective reservation; retries return the same result.
- The sum of active reservations and commitments cannot exceed the line's approved amount.
- Active baselines and ledger events are immutable; change occurs through a Revision or a new funding event.
- A line reduction cannot fall below active reservation balance plus total commitment.
- Deletion is prohibited after activation or downstream reference.

# 7\. Lifecycles and transition controls

## 7.1 Budget baseline

| **State**       | **Action**                | **Next state**  | **Authority and guard**                                                                                  |
| --------------- | ------------------------- | --------------- | -------------------------------------------------------------------------------------------------------- |
| Draft           | Submit for verification   | In Verification | Budget Officer; source reference, evidence and all lines complete.                                       |
| In Verification | Return                    | Returned        | Assigned Budget Reviewer; reason required.                                                               |
| Returned        | Resume                    | Draft           | Assigned Budget Officer; review evidence retained.                                                       |
| In Verification | Verify and activate       | Active          | Configured Budget Activation Authority under PE/PFM delegation; segregation and source-authority checks. |
| Active          | Apply authorised Revision | Superseded      | System transaction creates new Active version; old version remains immutable.                            |
| Active          | Close                     | Closed          | Configured authority after FY/closure guards; no new reservations.                                       |

'Verify and activate' confirms that the externally authorised baseline has been faithfully registered and may be used by KenTender. It is not a legislative, appropriation or public-budget approval. A PE may configure separate Verify and Activate tasks if its PFM delegation requires them.

## 7.2 Funding reservation

| **State**                      | **Permitted event**                | **Result**                                                             |
| ------------------------------ | ---------------------------------- | ---------------------------------------------------------------------- |
| Requested                      | Atomic check-and-reserve           | Reserved, or rejected with a typed insufficient/invalid/routing error. |
| Reserved                       | Material value or Budget change    | Revalidated; remaining Reserved or moved to Needs attention.           |
| Reserved                       | Partial contract commitment        | Partially converted; unused balance remains Reserved.                  |
| Reserved / Partially converted | Final conversion                   | Converted; remaining balance is zero.                                  |
| Reserved / Partially converted | Cancellation or authorised release | Released; available balance increases by the released remainder.       |
| Any active state               | Authoritative invalidation         | Needs attention; downstream progression blocked pending resolution.    |

## 7.3 Budget Revision

| **State**        | **Action** | **Next state** | **Guard**                                                                                |
| ---------------- | ---------- | -------------- | ---------------------------------------------------------------------------------------- |
| Draft            | Submit     | In Review      | Before/after, revision instrument, evidence and impact complete.                         |
| In Review        | Return     | Returned       | Reason required; submitter may correct.                                                  |
| In Review        | Reject     | Rejected       | Reason and authority evidence retained.                                                  |
| In Review        | Apply      | Applied        | Configured Revision Authority; submitter segregation; floor and transfer-balance checks. |
| Draft / Returned | Cancel     | Cancelled      | No baseline or ledger mutation.                                                          |

## 7.4 Revalidation events

- Plan Item estimated value, Budget Line, FY, currency or funding-source change.
- Formal Procurement Requisition submission or material requisition amendment.
- Tender estimate or package value change.
- Award recommendation and proposed contract value.
- Contract creation, contract variation, cancellation or termination.
- Budget Revision, suspension, closure or authoritative finance-system invalidation.

# 8\. Roles, permissions and assignment

| **Actor/capability**         | **Neutral read**                | **Permitted action**                                                     | **Restriction**                                                                        |
| ---------------------------- | ------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| Budget Viewer / Auditor      | Scoped records and evidence     | None                                                                     | Cannot open live task forms or mutate data.                                            |
| Budget Officer               | Scoped                          | Register Draft baseline and lines; prepare Revision; respond to returns. | Cannot self-verify/activate or apply own Revision where segregation is configured.     |
| Budget Reviewer              | Scoped                          | Verify completeness; return with reason.                                 | No authority to invent the source budget or reserve funds without assigned capability. |
| Budget Activation Authority  | Scoped                          | Activate a verified externally authorised baseline.                      | Must have configured PE/PFM delegation; not a universal statutory role.                |
| Finance Confirmation Officer | Scoped task and neutral context | Check and reserve, return or reject one named Plan Item request.         | Authority is task-, PE-, FY- and amount-scoped; no plan editing.                       |
| Revision Authority           | Scoped                          | Apply or reject an authorised Revision.                                  | Must validate delegation, evidence, floors and segregation.                            |
| Accounting Officer           | Full PE neutral view            | Any direct action only where explicitly configured by law/delegation.    | Remains accountable; accountability does not make every step a personal click.         |
| Procurement Planner / HoP    | Applicable funding context      | Request confirmation and view result.                                    | Cannot alter Budget or Finance evidence.                                               |
| System Administrator         | Audited all-record neutral read | Technical configuration only unless separately assigned.                 | No implicit operational finance authority.                                             |

**Scope resolution:** Zero PE scopes block access with a configuration message. One PE scope resolves explicitly. Multiple PE scopes require deliberate selection. FY is restored only from valid saved context; otherwise select the nearest configured year with an open applicable record. Never select PE-MOH, the first PE, the first OU or an Administrator fallback.

## 8.1 Assignment model

- Every operational action resolves a capability assignment with PE, optional OU, FY, action type, effective dates and delegation/evidence reference.
- Every Finance confirmation resolves a named live task. A role label alone never creates pending work.
- Counters, task lists, direct routes, APIs, exports and notifications apply the same server-side scope predicate.
- Workspace PE/FY selectors change visibility only; they do not grant ownership or authority.
- Routing failure is explicit and blocks the transition; it is never treated as confirmation.

# 9\. Functional requirements

| **ID**     | **Requirement**                                                                                              |
| ---------- | ------------------------------------------------------------------------------------------------------------ |
| BUD-FR-001 | Create a Budget only within one explicit authorised PE and configured FY.                                    |
| BUD-FR-002 | Generate Budget, Budget Line, Reservation, Commitment and Revision references server-side.                   |
| BUD-FR-003 | Register the source authority, source date, evidence and currency for an already authorised budget baseline. |
| BUD-FR-004 | Derive Budget totals from Budget Lines; reject manually supplied calculated totals.                          |
| BUD-FR-005 | Store approved amount on Budget Line as the allocation; do not persist a duplicate Allocation object.        |
| BUD-FR-006 | Allow zero or more approved Strategy references on a Budget Line.                                            |
| BUD-FR-007 | Verify and activate the registered baseline only through a configured PE/PFM authority and live task.        |
| BUD-FR-008 | Make Active Budget Versions and Lines immutable.                                                             |
| BUD-FR-009 | Create no reservation from Departmental Need submission, approval or acceptance.                             |
| BUD-FR-010 | Accept a Finance-confirmation request only from a complete Plan Item in the permitted Planning state.        |
| BUD-FR-011 | Perform the availability check and reservation creation in one database transaction.                         |
| BUD-FR-012 | Make reservation creation idempotent by correlation key and reject concurrent oversubscription.              |
| BUD-FR-013 | Return or reject a Finance request with a reason and without creating a reservation.                         |
| BUD-FR-014 | Revalidate the same reservation at every material downstream event.                                          |
| BUD-FR-015 | Allow authorised full or partial release of the remaining reservation with evidence.                         |
| BUD-FR-016 | Convert one reservation into one or more commitments without exceeding its remaining amount.                 |
| BUD-FR-017 | Adjust commitment only through an authorised variation or correction event.                                  |
| BUD-FR-018 | Calculate Available, Reserved, Committed and Outstanding Commitment using the canonical formulas.            |
| BUD-FR-019 | Ingest Actual Expenditure only from a configured authoritative integration and show source freshness.        |
| BUD-FR-020 | Display expenditure as Unavailable when no integration is configured; never substitute zero.                 |
| BUD-FR-021 | Change an Active baseline only through a Budget Revision with before/after evidence.                         |
| BUD-FR-022 | Block a Revision that reduces a line below reservations plus commitments or creates an unbalanced transfer.  |
| BUD-FR-023 | Preserve reservation and commitment identities when a Revision is applied.                                   |
| BUD-FR-024 | Provide neutral read access independently of operational workflow authority.                                 |
| BUD-FR-025 | Record append-only audit and Funding Ledger events for every state and balance change.                       |
| BUD-FR-026 | Expose typed logical contracts; prohibit downstream direct controller/table coupling.                        |
| BUD-FR-027 | Operate when Procurement Home and the legacy demands package are absent.                                     |
| BUD-FR-028 | Seed only after Configuration and Governance prerequisites and fail loudly when they are missing.            |
| BUD-FR-029 | Remove every treatment object, field, screen, seed and test from active metadata and executable source.      |
| BUD-FR-030 | Close a Budget without deleting history and prevent new reservations after closure.                          |

# 10\. Screen and interaction specification

The navigation label remains Budget & Funding. The clean module uses compact operational surfaces; it does not reproduce the legacy twelve-screen pack or expose an advanced performance dashboard. Static screen design and runtime behaviour remain separately testable.

| **Screen**                           | **Static design contract**                                                                                              | **Implementation behaviour**                                                             |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| BUD-UI-01 Budget & Funding Workspace | Explicit PE/FY context; active baseline summary; actionable work; waiting work; operational totals.                     | Zero/one/multiple scope rules; counts and tasks use server scope. No advanced analytics. |
| BUD-UI-02 Register Approved Budget   | Source authority/reference, evidence, FY, currency and line entry.                                                      | Draft only. Generated references; totals derived; submit validates source evidence.      |
| BUD-UI-03 Budget Overview            | Baseline identity, status, approved/reserved/committed/available totals, source evidence and version history.           | Neutral read is distinct from task authority; Active records are immutable.              |
| BUD-UI-04 Budget Lines               | Compact lines with purpose, approved amount, reserved, committed, available, fund source and optional Strategy lineage. | No separate allocation editor or treatment questionnaire. Drill-down respects scope.     |
| BUD-UI-05 Baseline Verification      | Source evidence, validation summary, line totals, changes and Return / Verify and activate actions.                     | Only a live assigned task opens. Activation rechecks segregation, source and scope.      |
| BUD-UI-06 Finance Confirmation       | Plan Item, PE/FY, estimated amount, Budget Line, available balance, strategy context and evidence.                      | Check is non-mutating; Confirm performs atomic reserve. Return/reject require reason.    |
| BUD-UI-07 Funding Activity           | Chronological reservation, release, revalidation, conversion, commitment and exception events.                          | Append-only ledger; retry-safe; filters do not grant access.                             |
| BUD-UI-08 Budget Revision            | Type, authority instrument, affected lines, before/after amounts, downstream impact, evidence and justification.        | No Active direct edit; floor, transfer, segregation and concurrency checks.              |
| BUD-UI-09 Revision Review            | Diff, validation, impact, authority evidence and Apply / Return / Reject actions.                                       | Live task only; Apply atomically creates new Active version.                             |
| BUD-UI-10 Neutral Funding Record     | Read-only baseline, line, reservation/commitment lineage, evidence, audit and source freshness.                         | Available to authorised viewers and System Administrator without workflow actions.       |

**Design-tool boundary:** Stitch or other design prompts may specify visible composition and example states only. Saving, permissions, concurrency, validation, transitions, API failures and loading behaviour are governed by this document and automated tests.

## 10.1 Workspace operational states

| **State**                 | **Primary content**                                                                      | **Primary action**                       |
| ------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------- |
| No baseline               | No active registered budget for selected PE/FY.                                          | Register approved budget, if authorised. |
| Draft / Returned          | Incomplete or returned baseline with issues.                                             | Continue registration.                   |
| Awaiting verification     | Named review task for authorised user; neutral waiting item for submitter.               | Review or view submission.               |
| Active with Finance tasks | Operational funding position plus assigned confirmation requests.                        | Open Finance confirmation.               |
| Active with no tasks      | Baseline and balances; no-action empty state.                                            | View budget.                             |
| Revision pending          | Active baseline remains effective; named Revision task or waiting item shown separately. | Review Revision or view status.          |
| Closed                    | Historical balances, evidence and no operational actions.                                | View record.                             |

# 11\. Validation, atomicity and concurrency

| **Control**                      | **Enforcement point**                     | **Failure result**                                         |
| -------------------------------- | ----------------------------------------- | ---------------------------------------------------------- |
| Explicit authorised PE/FY        | Every list, read, create, task and export | Controlled denial or deliberate context selection.         |
| Source authority and evidence    | Baseline submit and activate              | Remains Draft/In Verification with actionable errors.      |
| Line approved amount is positive | Line save, seed and activation            | Transaction rejected.                                      |
| Reservation ≤ available          | Atomic reserve transaction                | Typed insufficient-funds error; no partial record.         |
| Idempotency key                  | Reserve/release/convert/revalidate        | Existing effective result returned; no duplicate event.    |
| Row/version lock                 | Reserve, Revision apply and conversion    | Concurrent oversubscription or stale mutation rejected.    |
| Same PE/FY/currency/line         | All lineage operations                    | Cross-scope transition denied and audited.                 |
| Revision floor                   | Submit and Apply                          | Reduction below reserved + committed blocked.              |
| Balanced transfer                | Revision validation                       | Transfer cannot submit/apply until debits equal credits.   |
| Authoritative expenditure        | Snapshot ingest                           | Unknown source or stale/inconsistent snapshot quarantined. |
| Closed Budget                    | New reservation                           | Request rejected; existing audit remains readable.         |
| Optimistic concurrency           | Every state transition                    | Stale version rejected; current state returned.            |

# 12\. Logical integration contracts

These service contracts are mandatory boundaries. Package paths may follow the application structure, but consumers must not import Budget DocType controllers or query Budget tables directly.

| **Contract**                | **Input**                                        | **Output/control**                                                             |
| --------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------ |
| resolve_budget_context      | PE, FY, optional OU                              | Active baseline or typed zero/multiple/ineligible error.                       |
| list_eligible_budget_lines  | Context plus amount/classification filters       | Scoped Active lines with operational balances and optional Strategy lineage.   |
| check_funding               | Plan Item, line, amount, correlation             | Non-mutating eligibility and availability result with as-of/version token.     |
| reserve_funding             | Valid check token plus assigned Finance task     | Atomic idempotent reservation or typed failure; task decision audited.         |
| revalidate_reservation      | Reservation plus material-event reference        | Valid, Needs attention or released result with evidence.                       |
| release_reservation         | Reservation, amount/remainder, reason, authority | Idempotent release and new operational balance.                                |
| convert_reservation         | Reservation, award/contract, commitment amount   | One/more commitments; excess rejected; remainder retained/released explicitly. |
| adjust_commitment           | Commitment, variation/correction evidence        | New total commitment version after funding revalidation.                       |
| apply_budget_revision       | Reviewed Revision and authority task             | New immutable Active Budget Version and preserved funding identities.          |
| ingest_expenditure_snapshot | Authoritative source payload                     | Read-only snapshot, freshness and reconciliation status.                       |
| get_funding_lineage         | Plan/Requisition/Tender/Award/Contract reference | Budget, line, reservation, commitments, evidence and ledger events.            |

## 12.1 Cross-module control points

| **Producer/event**               | **Budget control**                                             | **Consumer result**                                  |
| -------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------- |
| Configuration                    | Provide PE/FY, OU, currency and capability/delegation records. | Budget fails closed if prerequisites are absent.     |
| Strategy                         | Provide approved read-only lineage.                            | Budget Line may store zero or more references.       |
| Departmental Needs accepted      | No reservation and no Finance task.                            | Need proceeds to planning pool.                      |
| Plan Item complete               | Finance check-and-reserve.                                     | Confirmed reservation or returned/rejected item.     |
| Approved Plan Item → Requisition | Revalidate inherited reservation.                              | Formal Requisition retains the same funding lineage. |
| Tender material change           | Revalidate amount, line and context.                           | Tender blocked if invalid.                           |
| Award/Contract                   | Revalidate and convert reservation.                            | Commitment created without double reservation.       |
| Variation/cancellation           | Adjust commitment or release remainder.                        | Balances and lineage updated atomically.             |

# 13\. Seed data contract

Budget seed is deterministic, configuration-first and independently runnable. It consumes existing PE, OU, FY, currency, user-assignment and delegation records. It must never invent configuration or repair a missing legacy record.

| **Seed set**            | **Required records**                                                                                               | **Purpose**                                                  |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| CFG prerequisites       | Ministry of Health and County Government of Kisumu; FY 2027/28; KES; explicit OUs and capability assignments.      | Stable scope and authority for all Budget records.           |
| MoH baseline            | MOH-BUD-2027-001; Ministry of Health Approved Budget 2027/28 (Demo); Active v1; source MOH-FIN-BUD-2027-01 (Demo). | Canonical operational baseline.                              |
| MoH line 1              | MOH-BL-DHI-01; Digital clinical systems infrastructure; approved KES 480,000,000.                                  | Funds primary planning item.                                 |
| MoH line 2              | MOH-BL-CAP-01; Digital health technical capability; approved KES 80,000,000.                                       | Funds second added Plan Item without oversubscribing line 1. |
| MoH reservation         | PPI-MOH-2027-021; reserved KES 455,000,000 against MOH-BL-DHI-01; explicit Finance assignment/evidence.            | Finance-confirmed planning state.                            |
| MoH conversion scenario | Commitment KES 310,000,000; remaining reservation KES 145,000,000; available KES 25,000,000.                       | Proves canonical arithmetic and partial conversion.          |
| MoH second item         | PPI-MOH-2027-022; KES 80,000,000 against MOH-BL-CAP-01; state selected to exercise pending/confirmed work.         | Separate line and task routing fixture.                      |
| Kisumu baseline         | KSM-BUD-2027-001 with at least one modest Demo line and no MoH references.                                         | Second-entity isolation and zero-work state.                 |
| No expenditure fixture  | No Actual Expenditure Snapshot unless a named demo integration is explicitly enabled.                              | UI shows Unavailable rather than fabricated zero.            |
| Negative fixtures       | Missing scope, insufficient funds, duplicate correlation, stale version and floor breach only inside tests.        | Proves failure controls without polluting canonical seed.    |

**Seed disclaimer:** Entity names provide stable demonstration scope; budget references, titles, amounts and authority evidence marked Demo are synthetic test fixtures and must not be represented as official appropriations or live financial data.

## 13.1 Canonical arithmetic fixture

| **Position**          | **Calculation**                         | **Amount**      |
| --------------------- | --------------------------------------- | --------------- |
| Approved              | MOH-BL-DHI-01 baseline                  | KES 480,000,000 |
| Original reservation  | Finance-confirmed Plan Item             | KES 455,000,000 |
| Commitment            | Partial conversion                      | KES 310,000,000 |
| Remaining reservation | 455,000,000 − 310,000,000               | KES 145,000,000 |
| Available             | 480,000,000 − 145,000,000 − 310,000,000 | KES 25,000,000  |
| Actual expenditure    | No integration                          | Unavailable     |

# 14\. Greenfield implementation work plan

1. Inventory Budget schema, services, hooks, pages, links, tests and seeds; classify every artifact Keep, Correct, Remove or Defer.
2. Delete every runtime, hook, route, test and seed dependency on the legacy demands package and Procurement Home.
3. Delete treatment objects and the duplicate Allocation concept. Do not create migrations, aliases or compatibility shims.
4. Implement canonical Budget, Budget Version, Budget Line, Reservation, Commitment, Revision, Ledger Event, Exception and optional integration-only Expenditure Snapshot models.
5. Implement generated references, immutable Active versions, derived totals and active-line constraints.
6. Implement capability-scoped baseline verification/activation and neutral read access.
7. Implement atomic check-and-reserve, idempotent release, revalidation and commitment conversion services.
8. Implement controlled Revisions with before/after, floor, transfer, segregation and concurrency checks.
9. Implement the ten clean operational screens and remove the advanced Funding Performance dashboard.
10. Rebuild deterministic Budget seeds only after CFG and optional Strategy prerequisites.
11. Run fresh-install, schema, double-seed, permission, arithmetic, concurrency, API and browser smoke tests.
12. Record evidence and approval in the Revision Ledger; retire all conflicting legacy Budget packs.

## 14.1 Repository removal checklist

- No executable import path containing kentender_procurement.demands or procurement_home.
- No Budget Line Value Treatment, Budget Value Treatment, Public Value Objective or planned-treatment metadata.
- No duplicate Allocation DocType/model/table or user-entered calculated total.
- No PE-MOH, first-PE, first-OU, current-year or Administrator operational fallback.
- No manual Actual Expenditure entry or seeded live-looking expenditure.
- No advanced Funding Performance dashboard in MVP navigation or required routes.
- No user-editable generated reference.
- No downstream direct mutation of Budget records or creation of a second reservation.

## 14.2 MVP-1 delivery boundary

| **Capability**                                                                     | **MVP-1 treatment**                                                                                             |
| ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Baseline, lines, verification/activation, Finance reservation, Revision and ledger | Required now.                                                                                                   |
| Reservation revalidation at Planning/Requisition                                   | Required now.                                                                                                   |
| Award/Contract conversion and commitment adjustment                                | Contract required now; executable transition must exist before those downstream modules are enabled.            |
| Expenditure integration                                                            | Schema/contract may exist; no manual entry. UI shows Unavailable until authoritative integration is configured. |
| Advanced performance analytics, forecasting, cash planning and payments            | Deferred to an approved later change unit.                                                                      |

# 15\. Acceptance criteria

| **ID**     | **Observable acceptance outcome**                                                                                          |
| ---------- | -------------------------------------------------------------------------------------------------------------------------- |
| BUD-AC-001 | Fresh site installs and migrates with Budget & Funding enabled and legacy demands/Home packages absent.                    |
| BUD-AC-002 | Budget workspace opens without Procurement Home and without a runtime import dialog.                                       |
| BUD-AC-003 | Zero, one and multiple PE/FY cases follow the explicit resolution rules with no silent fallback.                           |
| BUD-AC-004 | System Administrator can inspect neutral records read-only but cannot perform finance actions without explicit assignment. |
| BUD-AC-005 | A baseline cannot activate without source authority, evidence, lines, delegation and segregation checks.                   |
| BUD-AC-006 | Activation is labelled and audited as procurement-use activation, not public-budget approval.                              |
| BUD-AC-007 | Active Budget Versions and Lines reject direct mutation.                                                                   |
| BUD-AC-008 | Departmental Need acceptance creates no reservation, ledger event or Finance task.                                         |
| BUD-AC-009 | A complete Plan Item creates one named Finance-confirmation task and no reservation before confirmation.                   |
| BUD-AC-010 | Check Funding is non-mutating; Confirm Funding atomically creates one idempotent reservation.                              |
| BUD-AC-011 | Concurrent requests cannot oversubscribe a Budget Line.                                                                    |
| BUD-AC-012 | Return/reject records a reason and creates no reservation.                                                                 |
| BUD-AC-013 | Formal Requisition revalidates and retains the original reservation identity.                                              |
| BUD-AC-014 | Partial conversion of KES 455m to KES 310m leaves KES 145m reserved and KES 25m available on the KES 480m line.            |
| BUD-AC-015 | Actual expenditure is never subtracted twice and is shown as Unavailable when no integration exists.                       |
| BUD-AC-016 | Revision reductions below reservation plus commitment and unbalanced transfers are blocked.                                |
| BUD-AC-017 | Applied Revision creates a new immutable Active version and preserves funding identities.                                  |
| BUD-AC-018 | All funding events are append-only, correlated, actor-attributed and replay-safe.                                          |
| BUD-AC-019 | Budget Lines support zero or more approved Strategy references with no treatment questionnaire.                            |
| BUD-AC-020 | No duplicate Allocation object or manually entered derived total exists.                                                   |
| BUD-AC-021 | MoH and Kisumu seed records remain isolated and double-seeding is idempotent.                                              |
| BUD-AC-022 | Unauthorised direct routes, APIs, exports and task forms are denied before operational controls render.                    |
| BUD-AC-023 | All ten clean screens render their static contract and the advanced Funding Performance dashboard is absent.               |
| BUD-AC-024 | Closed Budgets remain readable but reject new reservations.                                                                |

# 16\. Smoke contract

| **Gate**               | **Required test**                                                    | **Pass condition**                                                   |
| ---------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Static dependency scan | Search executable source, hooks and seed manifests.                  | No legacy demands/Home or removed treatment imports.                 |
| Fresh environment      | Install → migrate → CFG seed → optional Strategy seed → Budget seed. | No migration/repair/compatibility step; all prerequisites explicit.  |
| Seed repeatability     | Run seed sequence twice.                                             | Same identities, amounts and counts; no duplicates or fallback data. |
| Arithmetic             | Approved/reserved/committed/actual fixtures.                         | Canonical formulas and KES 480m/455m/310m/145m/25m story pass.       |
| Atomicity              | Parallel reserve and duplicate-correlation tests.                    | No oversubscription and exactly one effective event.                 |
| Lifecycle              | Baseline, reservation, commitment, Revision and closure transitions. | Only permitted states/actors succeed; stale writes fail.             |
| Permissions            | List, read, route, API, task, export and Administrator matrix.       | Neutral read and operational authority remain separate.              |
| Integration            | Planning/Requisition and Award/Contract contract tests.              | One funding lineage; revalidation and conversion are fail-closed.    |
| Browser                | Workspace and BUD-UI-02–10 routes for representative roles/states.   | No runtime dialog, broken route, stale label or unauthorised form.   |

# 17\. Traceability to statutory control matrix

| **Control**                                           | **BUD-CHG-001 implementation**                                                                                          | **Evidence**                                  |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| CTL-011 — annual plan integrated with budget          | Active approved Budget Lines are the only source for Planning Finance confirmation.                                     | Context and Planning contract tests.          |
| CTL-021 — formal Requisition after Approved Plan Item | Requisition inherits/revalidates the Plan Item reservation; it does not feed the annual Plan.                           | Cross-module lineage test.                    |
| CTL-025 — funding control                             | Named delegated Finance task, atomic check-and-reserve, insufficient/routing failures block progression.                | Permission, task and concurrency tests.       |
| CTL-026 — funding revalidation                        | Material estimate, award, variation, cancellation and contract events revalidate or adjust the same lineage.            | Event-driven revalidation tests.              |
| GAP-008 — finance authority ambiguity                 | Capabilities are PE/FY/task/effective-date scoped with delegation evidence; Accounting Officer accountability retained. | Configuration and authorisation matrix tests. |

# 18\. Risks and controls

| **Risk**                                                        | **Control**                                                                                                  |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| KenTender is mistaken for the approving budget authority.       | Use register/verify/activate language; require external authority evidence and preserve legal boundary text. |
| Finance role becomes a universal final approver.                | Require explicit delegation, named task and scope; keep Accounting Officer accountability visible.           |
| Same money is reserved twice or actual spend is double-counted. | One correlation lineage, atomic ledger and canonical formulas.                                               |
| Revision invalidates live procurement work.                     | Floor, impact and revalidation checks; preserve identities and fail closed.                                  |
| Admin or fallback scope leaks another PE's data.                | Neutral read only, same server predicate on every surface, no inferred scope.                                |
| Fresh build quietly depends on deleted code or seed.            | Static scan and fresh-site smoke are release gates.                                                          |
| Synthetic figures appear official.                              | Mark Demo authority/amounts and never seed live-looking expenditure.                                         |
| Downstream modules enable unimplemented commitment controls.    | Feature gate downstream transitions until conversion/revalidation contract tests pass.                       |

# 19\. Approval record

| **Decision**                                    | **Status**       | **Owner/evidence**                                                                 |
| ----------------------------------------------- | ---------------- | ---------------------------------------------------------------------------------- |
| Approve BUD-CHG-001 as implementation authority | Pending          | Product-owner approval recorded in Revision Ledger.                                |
| Retire conflicting Budget documentation         | Pending approval | Legacy requirements, prompts, packs and demo contracts are superseded on approval. |
| Implementation completion                       | Not started      | Requires every acceptance criterion and smoke gate.                                |

# Sources

- Constitution of Kenya, Articles 201 and 227 — Kenya Law: <https://new.kenyalaw.org/akn/ke/act/2010/constitution>
- Public Procurement and Asset Disposal Act, 2015, sections 44 and 53 — Kenya Law: <https://new.kenyalaw.org/akn/ke/act/2015/33>
- Public Procurement and Asset Disposal Regulations, 2020, regulations 40–42, 49, 52 and 54 — Kenya Law: <https://new.kenyalaw.org/akn/ke/act/ln/2020/69>
- Public Finance Management Act, 2012, sections 68 and 149 — Kenya Law: <https://new.kenyalaw.org/akn/ke/act/2012/18>
- Public Finance Management (National Government) Regulations, 2015, regulation 51 and related commitment/unauthorised-spending controls — Kenya Law: <https://new.kenyalaw.org/akn/ke/act/ln/2015/34>
- Public Finance Management (County Governments) Regulations, 2015 — Kenya Law: <https://new.kenyalaw.org/akn/ke/act/ln/2015/35>
- KenTender Statutory Procedure, Forms and System Control Matrix v1.1 — controls CTL-011, CTL-021, CTL-025 and CTL-026; gap GAP-008.

_Official legal sources reviewed for this change unit on 19 August 2026._