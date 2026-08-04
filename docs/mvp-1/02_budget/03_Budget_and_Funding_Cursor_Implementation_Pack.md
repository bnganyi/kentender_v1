# Budget & Funding — Cursor Implementation Pack

**Reference:** `BUDGET-MVP1-REQ-1.1`  
**Design reference:** Budget & Funding Stitch Prompts, revised to include Register Approved Budget  
**Implementation approach:** Clean MVP rebuild  
**Canonical fixture:** `MOH_MVP_V1`

## 1. Objective

Implement the complete Budget & Funding MVP, beginning with registration of the approved Budget aggregate and continuing through Budget Lines, review, activation, funding control, revisions, monitoring and audit.

Do not begin at the Budget Line editor. A Budget Line cannot exist without a governed Budget aggregate, authoritative source, fiscal period, owner and lifecycle.

The financial system remains authoritative for budget formulation, appropriation, general-ledger accounting, payments and actual expenditure. In MVP 1, KenTender directly captures the approved baseline and controls its use through procurement. Future baseline integration will use an API.

## 2. Authority and precedence

Use these sources in this order:

1. This implementation pack
2. `BUDGET-MVP1-REQ-1.1`
3. The approved revised Stitch designs
4. Existing code that does not conflict with the above

Stitch is a visual reference only. Do not copy fake navigation, hard-coded mock data, static controls or generated application shells.

Where old Budget code conflicts with this pack, replace it. Existing MVP Budget data is disposable. Preserve unrelated modules, users and master data.

## 3. Non-negotiable boundaries

Implement:

- Budget Portfolio
- Register Approved Budget
- Budget workspace and derived totals
- Budget Lines and funding sources
- Strategy target alignment
- Plan Value Commitment funding treatments
- Readiness, review and activation
- Funding checks and reservations
- Reservation inheritance and conversion
- Contract commitments
- Read-only expenditure snapshots
- Funding Activity and Downstream Usage
- Controlled Budget Revisions
- Funding Performance
- Audit history and controlled export
- Canonical Ministry of Health seed data

Do not implement:

- Budget formulation or ceilings
- Appropriation approval
- General ledger or chart-of-accounts administration
- Cash releases or cash forecasting
- Invoice or payment approval
- Journal entries
- Manual authoritative actual-expenditure entry
- File-based budget import
- Financial-system baseline integration in MVP 1; reserve this for a future API
- Bidirectional financial-system budgeting
- Predictive forecasts, scores or AI recommendations
- Automatic tender criteria or contract clauses

## 4. Corrected identity rules

Do not require users to enter or maintain codes.

Every Budget-domain record shall have:

- An immutable internal identifier used for relationships and APIs
- A system-generated, read-only human reference
- An optional external source reference where applicable

Normal relationships must use internal identifiers, not reference strings or titles.

Reference examples such as `MOH-BUD-0001` and `MOH-BL-0001` are fixed fixture values. Production references must be generated server-side from the configured entity prefix, record type and a non-reusable sequence.

References shall not encode mutable titles, owners, statuses or fiscal dates.

Only one Active procurement Budget may cover the same entity and fiscal period. Multiple funding sources belong in Budget Lines; they do not create competing Active Budget aggregates. Changes to an Active Budget use a Budget Revision.

## 5. Architecture requirements

- Use the existing KenTender/Frappe application architecture and real database-backed DocTypes.
- Do not use an iframe, static HTML implementation, local storage or page-level mock JSON.
- Use a focused Budget Portfolio and Budget workspace rather than raw DocType lists as the primary UI.
- Reuse the real application shell, permissions and routing.
- Store money in fixed-precision decimal fields. Do not use floating-point storage.
- Derive all totals server-side from lines and funding activity.
- Enforce permissions, lifecycle guards and balance rules server-side.
- Make funding mutations atomic, idempotent and concurrency-safe.
- Record immutable before/after audit events for governed changes.
- Avoid duplicate Budget models, duplicate total fields and parallel reservation paths.
- Do not preserve obsolete code merely because it already exists.

## 6. Implementation sequence

Implement in the following order. Do not skip the Budget aggregate or governance phases.

### Phase 0 — Inspect and retire conflicting MVP structures

Before editing:

1. Identify current Budget DocTypes, fields, services, routes, fixtures and tests.
2. Identify all consumers in Strategy, Demand, Planning, Tender, Award and Contract.
3. Identify obsolete Allocation objects, manually stored totals, duplicate reservations and direct Active-budget editing.
4. Produce a short implementation map naming what will be retained, replaced or removed.
5. Remove only confirmed obsolete Budget structures and disposable Budget demo data.
6. Preserve unrelated user data and master data.

Do not use legacy Budget formulas or relationships as the new design authority.

### Phase 1 — Domain model and canonical calculations

Implement or correct these records:

#### Budget

- internal_id
- generated_reference
- title
- procuring_entity
- fiscal_period
- start_date
- end_date
- currency
- budget_owner
- registration_source, system-controlled as Direct capture in MVP 1
- authoritative_reference
- external_approved_total
- approval_date
- approval_evidence
- status
- submitted metadata
- reviewed metadata
- activated metadata
- closed metadata
- fixture_namespace where applicable

Statuses:

- Draft
- Submitted
- Returned
- Active
- Closed
- Cancelled

The UI may display Submitted as “Under review,” but the domain value remains Submitted.

#### Budget Line

- internal_id
- generated_reference
- budget
- title
- organisational_owner
- classification
- procurement_category where applicable
- funding_source_type
- funding_source_name
- funding_source_reference
- approved_amount
- source_line_reference
- primary_strategy_reference
- supporting_strategy_references with reasons
- order_index
- fixture_namespace where applicable

Funding-source types:

- Exchequer
- Own source
- Donor or grant
- Other

#### Budget Value Treatment

- budget_line
- plan_value_commitment_version
- consideration_level snapshot
- treatment
- dedicated_amount
- rationale
- reviewer_acceptance where required
- immutable display snapshot

Treatments:

- Dedicated allocation
- Embedded in line
- No direct allocation required
- Not applicable

#### Funding Reservation

- internal_id
- generated_reference
- budget_line
- demand
- original_amount
- remaining_reserved
- currency
- current_downstream_reference
- status
- expiry_date
- idempotency_key
- created and release metadata

#### Procurement Commitment

- internal_id
- generated_reference
- budget_line
- reservation
- contract
- original_amount
- current_amount
- actual_expenditure
- outstanding_amount
- status
- adjustment history

#### Expenditure Snapshot

- commitment
- contract
- budget_line
- amount
- currency
- source_system
- source_reference
- source_as_at
- received_at
- reconciliation_status

#### Budget Revision and Revision Line

- budget
- generated revision number
- external approval reference
- approval evidence
- reason
- status
- line
- before amount
- change
- after amount
- metadata changes
- downstream impact
- applied metadata

Canonical calculations:

```text
Budget Approved = sum(Active Budget Line approved amounts)
Line Reserved = sum(active unconverted reservation balances)
Line Committed = sum(current contract commitment amounts)
Line Available = Line Approved - Line Reserved - Line Committed
Budget Available = sum(Line Available)
Outstanding Commitment = Line Committed - Actual Expenditure
```

Actual Expenditure is already included within the contract commitment. Do not subtract it again from Available.

Exhausted, Partially available and Available are derived funding conditions, not workflow statuses.

### Phase 2 — Budget Portfolio and Register Approved Budget

Implement the Budget Portfolio as the module entry point.

Portfolio requirements:

- Entity-scoped Budget list
- Fiscal period and status filters
- Search by title or external approval reference
- Assigned review work
- Funding exceptions
- Actions determined by permission and state
- Empty state with Register approved budget

Implement Register Approved Budget before Budget Line creation.

Common registration fields:

- Procuring Entity, defaulted from session authority
- Budget title
- Fiscal period
- Start and end dates derived or validated from fiscal period
- Currency
- Budget owner
- Authoritative approval reference
- Approval date
- Approved total
- Approval evidence

Do not render a Budget code input.

Registration rules:

- Use one direct-capture form.
- Do not show source-mode choices, import controls or integration options.
- Require authoritative approval reference, approval date, approved total and approval evidence.
- Create a Draft Budget with no lines.
- Permit Budget Officers to add Budget Lines in the workspace.
- Record `registration_source = Direct capture` internally without asking the user to select it.
- Reserve financial-system baseline integration for a future API implementation; do not build file import in MVP 1.

On successful registration:

- Generate the Budget reference.
- Create the Draft Budget.
- Route to the Budget Overview workspace.
- Do not activate automatically.
- Do not require Strategy alignment at header registration.

Implement registration in one database transaction. Prevent duplicate entity/fiscal-period Draft or Active aggregates unless the existing record is explicitly cancelled or closed under valid rules.

### Phase 3 — Budget workspace and Budget Lines

Implement these tabs:

- Overview
- Budget Lines
- Funding Activity
- Revisions
- Downstream Usage
- Review
- Audit

Overview shall show:

- Budget identity and authoritative source
- Derived Approved, Reserved, Committed, Available, Actual and Outstanding amounts
- Strategy-alignment completeness
- Value-treatment completeness
- Attention items
- Actual-expenditure source date and freshness

Do not store manually editable header totals.

Budget Lines shall show:

- Business title first and generated reference second
- Funding source
- Primary strategic target
- Approved
- Reserved
- Committed
- Available
- Actual
- Derived condition
- Attention and contextual action

#### Add/Edit Budget Line

For Draft or Returned:

- Permit authorised creation and editing of Budget Line funding fields, organisational owner, Strategy links and value treatments.

For Active:

- Show read-only Budget Line details.
- Do not show Save.
- Show Request revision.

Do not render editable reference fields.

Strategy rules:

- Require one primary Active Performance Target for the same entity and applicable period.
- Permit supporting targets only with reasons.
- Prevent duplicate target selection.
- Store internal Strategy references plus immutable display snapshots.
- Preserve historical resolution after Strategy supersession.

Plan Value Commitment rules:

- Fetch applicable commitments from Strategy using the selected target context.
- Users cannot add or delete commitments here.
- Every Required commitment needs a complete treatment before submission.
- Dedicated allocation requires a positive amount.
- Dedicated amounts must be exclusive and not exceed the line approved amount in aggregate.
- Embedded in line records rationale but no distinct amount.
- No direct allocation required and Not applicable require reasons.
- Not applicable also requires reviewer acceptance.
- Funding treatment must not create or imply a tender criterion, specification or contract clause.

Save the Budget Line, supporting targets and treatments in one transaction.

### Phase 4 — Readiness, review and activation

Implement grouped readiness checks:

- Source
- Budget Lines
- Strategy and Value Commitments
- Governance

Submission blockers include:

- Missing authoritative approval reference, approval date or approval evidence
- Missing required evidence
- Invalid fiscal period or currency
- No Budget Line
- Missing owner, classification, funding source or positive approved amount
- Line totals not matching an entered external approved total
- Missing or invalid primary Strategy target
- Supporting target without reason
- Incomplete Required value treatment
- Dedicated treatment total exceeding the line approved amount
- Cross-entity, cross-period or cross-currency references

Workflow:

```text
Draft -> Submitted -> Active
Draft -> Submitted -> Returned -> Submitted
Active -> Closed
Draft/Returned -> Cancelled
```

Governance:

- Budget Officer prepares and submits.
- Budget Reviewer verifies and may return with reasons.
- Reviewer completion is recorded separately while status remains Submitted.
- Budget Authority activates only after review.
- The submitter cannot activate the same Budget.
- Activation locks the baseline atomically.
- Activation means verified for procurement use in KenTender; it is not statutory budget approval.

Active Budgets and Lines cannot be edited through UI or API.

### Phase 5 — Funding check and reservation

Implement `check_funding` as a read-only calculation. It must not reserve or mutate funding.

Validate:

- Entity
- Fiscal period
- Active Budget
- Active Budget Line
- Currency
- Requested amount
- Available amount
- Downstream authority

Return:

- Budget Line
- Requested amount
- Available before
- Available after
- Funding available or Insufficient funding
- Shortfall where applicable
- Applicable Strategy and value-treatment context

Implement `reserve_funding` only from an authorised approved-Demand event.

Reservation rules:

- One reservation references one Budget Line and one approved Demand.
- Co-funding uses separate reservations against separate lines.
- Creation is transactional, idempotent and concurrency-safe.
- Repeated calls with the same idempotency key return the same result.
- The same reservation identity follows Demand through Planning, Package and Tender.
- Planning and Tender revalidate but do not create another hold.
- Insufficient funding blocks reservation and returns the shortfall.
- Release records amount, reason, actor, time and downstream lineage.

Use database locking or equivalent protection against parallel oversubscription.

### Phase 6 — Commitments, expenditure, activity and downstream usage

Award shall revalidate the linked reservation and authorised funding.

Contract activation shall atomically convert all or part of the reservation into a commitment.

Support:

- Partial conversion
- Multiple commitments from one reservation where lots or multiple contracts are authorised
- Explicit retention or release of unused reservation balance
- Authorised commitment adjustment from approved Contract Variation events
- Rejection of unauthorised manual commitment edits

Actual Expenditure:

- Accept only through the finance-integration service.
- Store immutable snapshots with source timestamp and received timestamp.
- Display Matched, Stale, Exception or Unavailable.
- Never display unavailable data as zero.
- Never allow ordinary users to edit Actual Expenditure.

Funding Activity shall show reservations, conversions, commitments, adjustments and expenditure snapshots chronologically.

Downstream Usage shall show read-only lineage:

```text
Budget Line -> Demand -> Procurement Plan item -> Package/Tender -> Contract
```

Do not permit downstream editing from the Budget workspace.

### Phase 7 — Budget Revisions

Active Budget changes use a Budget Revision. Do not unlock or directly edit the Active baseline.

Revision capture requires:

- External approval reference
- Approval date
- Effective date
- Reason
- Approval evidence
- Line-level before, change and after amounts
- Metadata changes where applicable
- Derived downstream impact

Rules:

- A revised line amount cannot fall below active reservation balances plus current commitments.
- Before and after values are immutable after submission.
- Strategy and value-treatment impacts must be reviewed.
- The submitter cannot apply their own Revision.
- Apply the Revision atomically.
- Preserve Budget, Line, Reservation and Commitment identities.

Revision workflow:

```text
Draft -> Submitted -> Applied
Draft -> Submitted -> Returned -> Submitted
Submitted -> Rejected
Draft/Returned -> Cancelled
```

### Phase 8 — Funding Performance, audit and export

Funding Performance is a separate read-only management entry, not another workspace tab.

Show:

- Approved
- Reserved
- Committed
- Available
- Actual Expenditure
- Outstanding Commitment
- Strategy funding coverage
- Plan Value Commitment treatments
- Funding and source-freshness exceptions

Distinguish:

- Strategy alignment
- Funding treatment
- Downstream adoption
- Verified strategic result

Never claim that alignment proves causation, savings or achievement.

Exports shall reproduce:

- Authorised filters
- Entity and fiscal period
- As-at timestamp
- Source coverage and freshness
- Traceable record references

Prevent spreadsheet-formula injection.

Audit shall cover:

- Budget registration
- Line creation and change
- Submission, review, return, activation and close
- Value-treatment change
- Reservation, release and conversion
- Commitment and adjustment
- Revision
- Expenditure sync
- Actor or integration, timestamp, reason and before/after values

Audit records are immutable and cannot be deleted through the UI.

## 7. Roles and server permissions

Implement the following minimum permissions:

| Capability | Viewer | Officer | Reviewer | Authority | Procurement User | Auditor | Finance Integration |
|---|---:|---:|---:|---:|---:|---:|---:|
| View Active funding | Yes | Yes | Yes | Yes | Assigned | Yes | Service |
| Create/edit Draft Budget | No | Yes | No | No | No | No | No |
| Submit Budget/Revision | No | Yes | No | No | No | No | No |
| Review/return | No | No | Yes | Yes | No | No | No |
| Activate/apply/close | No | No | No | Yes | No | No | No |
| Run funding check | View | Yes | Yes | Yes | Assigned | Yes | No |
| Reserve funding | No | Authorised service | No | Override only | Demand workflow | No | No |
| Convert commitment | No | No | No | Exception only | Contract workflow | No | No |
| View Funding Performance | Yes | Assigned | Assigned | Assigned | No | Yes | No |
| Sync expenditure | No | No | No | No | No | View | Yes |
| View audit | No | Own actions | Assigned | Assigned | Assigned records | Yes | Integration events |

Enforce entity scope and segregation server-side. Hiding a control is not sufficient permission enforcement.

## 8. Required service contracts

Implement stable, tested services for:

- `list_budgets`
- `register_budget`
- `get_budget`
- `list_budget_lines`
- `save_budget_line`
- `get_budget_readiness`
- `submit_budget`
- `return_budget`
- `mark_budget_reviewed`
- `activate_budget`
- `close_budget`
- `check_funding`
- `reserve_funding`
- `revalidate_reservation`
- `release_reservation`
- `convert_reservation`
- `adjust_commitment`
- `sync_expenditure`
- `list_funding_activity`
- `get_budget_usage`
- `create_budget_revision`
- `review_budget_revision`
- `apply_budget_revision`
- `get_funding_performance`
- `export_funding_performance`
- `get_budget_audit`

All mutation services shall validate permission, state, entity, fiscal period, currency and current version server-side.

## 9. Canonical seed-data contract

Create one versioned fixture bundle named `MOH_MVP_V1`.

Every module and every browser test shall reference this bundle. Do not create page-specific Ministry of Health mocks.

The fixture must be:

- Deterministic
- Idempotent
- Safe to rerun
- Available only in development, test and demo environments
- Resettable without deleting non-fixture data
- Identified by a fixture namespace
- Free of random identifiers, amounts and dates
- Loaded in dependency order

Provide one documented seed/reset command.

### 9.1 Strategy dependency

Entity:

- Ministry of Health

Active Entity Strategic Plan:

- `MOH-SP-0001`
- Ministry of Health Strategic Plan 2026–2030
- Status: Active

Targets:

- `MOH-TGT-0001` — At least 99.9% annual service availability
- `MOH-TGT-0002` — Restore critical services within 4 hours
- `MOH-TGT-0003` — Train and certify 150 digital-health technical staff

Plan Value Commitments:

- `PVO-EFT-01` — Improve infrastructure efficiency — Required
- `PVO-ECO-01` — Reduce whole-life infrastructure cost — Required
- `PVO-RES-01` — Improve system resilience — Recommended
- `PVO-SUS-02` — Ensure responsible asset disposal — Required

Resolve and store relationships using internal IDs. The references above are stable fixture display references.

### 9.2 Active Budget scenario

Budget:

- `MOH-BUD-0001`
- Ministry of Health Procurement Budget FY 2027/28
- Registration source: Direct capture
- External approval reference: `MOH-FIN-BUD-2027-01`
- Currency: KES
- Status: Active
- Approved: KES 560,000,000

Lines:

#### `MOH-BL-0001` — Digital clinical systems infrastructure

- Approved: KES 480,000,000
- Reserved balance: KES 145,000,000
- Committed: KES 310,000,000
- Available: KES 25,000,000
- Actual expenditure: KES 180,000,000
- Primary target: `MOH-TGT-0001`
- Supporting target: `MOH-TGT-0002`
- Supporting reason: Infrastructure investment supports service restoration and continuity requirements.

Treatments:

- `PVO-EFT-01` — Embedded in line — Efficiency considerations are included in infrastructure sizing, energy use and operating requirements.
- `PVO-ECO-01` — Dedicated allocation — KES 40,000,000 — Dedicated to whole-life costing, energy-efficiency and lifecycle-optimisation activities.
- `PVO-RES-01` — Embedded in line — Resilience is included in redundancy, continuity and support activities.
- `PVO-SUS-02` — No direct allocation required
- Rationale: Disposal costs are included within the asset-replacement activities funded by this line.

#### `MOH-BL-0002` — Digital health technical capability

- Approved: KES 80,000,000
- Reserved: KES 0
- Committed: KES 0
- Available: KES 80,000,000
- Actual expenditure: Unknown
- Primary target: `MOH-TGT-0003`

Treatments:

- `PVO-EFT-01` — Embedded in line — Training delivery uses the existing digital-learning platform.
- `PVO-ECO-01` — Embedded in line — Training and certification costs are included in the line amount.
- `PVO-RES-01` — Embedded in line — Continuity capability is included in the training programme.
- `PVO-SUS-02` — Not applicable — The line does not acquire or replace physical assets — reviewer accepted.

Derived Budget totals:

- Approved: KES 560,000,000
- Reserved: KES 145,000,000
- Committed: KES 310,000,000
- Available: KES 105,000,000
- Actual expenditure: KES 180,000,000
- Outstanding commitment: KES 130,000,000

### 9.3 Downstream funding scenario

- Demand: `DMD-MOH-2027-014` — National digital health infrastructure upgrade
- Approved Demand amount: KES 455,000,000
- Reservation: `RSV-MOH-0001`
- Original reservation: KES 455,000,000
- Remaining reserved: KES 145,000,000
- Reservation status: Partially converted
- Procurement Plan item: `PPI-MOH-2027-021`
- Tender: `TND-MOH-2027-008`
- Contract: `CTR-MOH-2027-005`
- Contract commitment: KES 310,000,000
- Actual expenditure snapshot: KES 180,000,000
- Outstanding commitment: KES 130,000,000
- Reconciliation state: Stale
- Source last updated: three fixture days before the fixture as-at date

The reservation and commitment must not be double-counted. The remaining reservation plus commitment equals KES 455,000,000.

### 9.4 Editable Draft scenario

Budget:

- `MOH-BUD-0002`
- Ministry of Health Procurement Budget FY 2028/29
- Registration source: Direct capture
- External approval reference: `MOH-FIN-BUD-2028-01`
- External approved total: KES 600,000,000
- Status: Draft

Lines:

#### `MOH-BL-0003` — Digital clinical systems infrastructure

- External line reference: `HLTH-INF-2028-004`
- Approved: KES 480,000,000
- Classification: Capital expenditure
- Funding source: Exchequer
- Owner: Head, ICT Infrastructure
- Primary target: `MOH-TGT-0001`
- Supporting target: `MOH-TGT-0002`
- Supporting reason: Infrastructure investment supports service restoration and continuity requirements.
- Dedicated treatments: KES 40,000,000
- Not dedicated: KES 440,000,000
- Use the same four value treatments as `MOH-BL-0001`

#### `MOH-BL-0004` — Digital health technical capability

- Approved: KES 120,000,000
- Primary target: `MOH-TGT-0003`
- Use the same complete value-treatment pattern as `MOH-BL-0002`

The two lines total KES 600,000,000.

### 9.5 Closed portfolio scenario

- `MOH-BUD-0003`
- Ministry of Health Procurement Budget FY 2026/27
- Status: Closed
- Approved: KES 520,000,000
- No open reservations

## 10. Test requirements

### Domain and calculations

- Budget and Line reference generation and uniqueness
- One Active Budget per entity and fiscal period
- Derived Budget and Line totals
- Reservation and commitment non-double-counting
- Actual-expenditure non-double-counting
- Currency, period and entity validation
- Dedicated-treatment limit
- Revision minimum-line guard

### Registration

- Register a complete direct-capture Draft
- Require the authoritative reference, approval date, approved total and approval evidence
- Prevent duplicate entity/fiscal-period active aggregate
- Generate references without user input
- Preserve approval reference and evidence audit

### Workflow and permissions

- Every valid and invalid Budget transition
- Reviewer completion before activation
- Submitter/activator segregation
- Active immutability through UI and API
- Entity access and evidence access
- Every valid and invalid Revision transition

### Strategy and value treatment

- Active target scoping
- Historical Strategy snapshot
- Supporting-target reason
- Applicable commitments
- Required treatment
- Not applicable reviewer acceptance
- Dedicated amount limits
- No tender treatment created

### Funding concurrency and downstream contracts

- Funding check does not mutate balances
- Parallel reservation attempts cannot oversubscribe
- Repeated idempotency key does not duplicate
- Reservation inheritance through Planning and Tender
- Partial and multiple commitment conversion
- Explicit release or retained remainder
- Contract variation adjustment
- Stale and unavailable expenditure states

### Canonical seed

- `MOH_MVP_V1` runs twice without duplicates
- Fixture reset removes only fixture-owned records
- All Strategy, Budget and downstream references resolve
- Active Budget totals match exact expected values
- Draft Budget lines total KES 600,000,000
- No page-local duplicate seed datasets exist

### Browser tests

- Budget Portfolio and empty state
- Register Approved Budget
- Budget Overview
- Budget Lines and Add/Edit details
- Directly captured Draft Budget Line fields remain editable for authorised officers
- Readiness, return, resubmit and activation
- Funding Check available and insufficient states
- Funding Activity and Downstream Usage
- Budget Revision before/after review
- Funding Performance and export
- Audit filtering
- Keyboard navigation and visible focus

## 11. Implementation execution rules

- Implement in the stated phase order.
- Keep each phase independently testable.
- Run relevant tests after every phase.
- Do not leave static demo handlers in production routes.
- Do not duplicate domain calculations in browser code.
- Do not invent alternative status vocabularies.
- Do not silently carry over obsolete Budget fields or formulas.
- Do not make unrelated navigation or toolbar changes.
- If an existing dependency conflicts with this pack, document the conflict and implement the pack unless doing so would damage unrelated production data.

## 12. Completion report

Return:

- Implementation map and retired legacy structures
- Files created, changed or removed
- DocType/schema changes
- Routes and services
- Permission and workflow implementation
- Seed/reset command
- Exact canonical fixture totals
- Tests added and results by phase
- Any deliberate deviation from this pack or the approved designs

Do not report completion while any required phase is omitted, any canonical fixture total is inconsistent, or any Active Budget remains directly editable.
