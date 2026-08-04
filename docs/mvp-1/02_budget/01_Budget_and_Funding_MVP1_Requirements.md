# Budget & Funding — MVP 1 Requirements

**Document ID:** BUDGET-MVP1-REQ-1.1  
**Status:** Locked  
**Date:** 4 August 2026  
**Approved:** 4 August 2026  
**Change control:** Functional changes require a new document version  
**Module:** Budget & Funding  
**Application:** KenTender  
**Primary fixture:** Ministry of Health

## Source baseline

- Budget Module — Purpose, Scope, Data, Workflow, and Links
- Budget Revision Process
- Budget totals description
- Recommended simplified budget workflow
- Budget Domain Revision
- Strategy Alignment requirements `STRATEGY-MVP1-REQ-1.1`
- KenTender Statutory and Public-Value Obligations Matrix, version 1.1
- [Public Procurement and Asset Disposal Act, 2015](https://ppra.go.ke/ppda/), including the requirement that procurement be planned within the approved budget
- [Public Procurement and Asset Disposal Regulations, 2020](https://www.treasury.go.ke/sites/default/files/PPDA/Public-Procurement-and-Asset-Disposal-Regulations-2020.pdf), including integration of annual procurement planning with the annual budget process
- [Public Finance Management (National Government) Regulations, 2015](https://kenyalaw.org/akn/ke/act/ln/2015/34), including control of expenditure commitments against approved spending and procurement plans

## 1. Purpose and boundary

Budget & Funding is KenTender's procurement funding-control layer. In MVP 1, it directly records the approved financial baseline available for procurement and controls how that funding is aligned, reserved, committed and reported through the procurement lifecycle. Future baseline integration will use an API.

The authoritative budgeting, appropriation, general-ledger, cash-management and payment functions remain in the financial system. KenTender shall not recreate them.

The module shall answer:

1. Which approved budget line funds this procurement?
2. Which Strategy target and Plan Value Commitments does the funding support?
3. How much is approved, available, reserved and contractually committed?
4. Can a demand, tender, award, contract or variation proceed financially?
5. Which strategic priorities or required value commitments remain unfunded or untreated?

## 2. MVP outcomes

MVP 1 shall enable a procuring entity to:

1. Register an approved fiscal-period procurement budget baseline through direct data capture.
2. Verify and activate that baseline for use in KenTender.
3. Maintain stable budget lines with derived funding balances.
4. Align each budget line to an Active primary Strategy Performance Target and optional supporting targets.
5. Record how applicable Plan Value Commitments are treated in the funding decision.
6. Check funding and reserve it atomically for an approved demand.
7. Carry one reservation through Planning and Tendering without duplicate holds.
8. Convert reserved funding into one or more contract commitments and release any unused balance.
9. Reconcile read-only expenditure data received from the financial system.
10. Apply externally approved budget revisions through a controlled, auditable process.
11. Show operational exceptions and management-level funding performance.
12. Preserve complete downstream traceability and audit history.

## 3. Design principles

1. **The financial system remains authoritative.** KenTender consumes approved baselines and expenditure facts.
2. **A Budget Line approved amount is the allocation.** MVP 1 shall not create a separate allocation object.
3. **Totals are derived.** Users shall not type header balances or calculated funding totals.
4. **One reservation follows the procurement.** Demand, Planning, Package and Tender shall not create duplicate reservations for the same requirement.
5. **Actual expenditure is not double counted.** It is shown separately but remains part of the total contract commitment.
6. **Active baselines are not edited directly.** Financial changes use a controlled revision supported by authoritative approval evidence.
7. **Strategy alignment and value treatment are distinct.** A target explains what the line supports; value treatment explains how a Plan Value Commitment is funded or why direct funding is unnecessary.
8. **Budget treatment does not create tender rules.** Specifications, criteria and contract clauses remain downstream governed decisions.
9. **All funding mutations are atomic and idempotent.** Concurrent approvals shall not oversubscribe a budget line.
10. **Management reporting distinguishes evidence from inference.** Alignment is not proof of causation, savings or achieved public value.
11. **Ordinary procurement users see clear funding outcomes.** Accounting terminology is reserved for authorised budget, finance and audit views.

## 4. Scope

### 4.1 Included

- Entity- and fiscal-period-scoped budget portfolio
- Direct capture of the approved procurement budget baseline
- Budget lines and controlled funding-source metadata
- Derived approved, available, reserved, committed, actual and outstanding amounts
- Strategy target alignment using the versioned Strategy Reference contract
- Plan Value Commitment funding treatment
- Baseline readiness review and activation for procurement
- Atomic funding checks and reservations
- Reservation release, expiry and partial/full conversion
- Contract commitments and authorised adjustments
- Read-only finance expenditure snapshots and reconciliation exceptions
- Controlled application of externally approved revisions
- Downstream usage and impact views
- Funding Performance management view and controlled export
- Roles, permissions, segregation, audit and notifications
- Ministry of Health seed fixture
- Replacement of obsolete MVP Budget structures and formulas
- A future API boundary for financial-system integration, without implementing baseline integration in MVP 1

### 4.2 Excluded

- Budget formulation, ceilings, appropriations or parliamentary/assembly approval
- General ledger, chart-of-accounts administration or journal entries
- Cash forecasting, bank management or payment processing
- Invoice approval and accounts payable
- Payroll, revenue collection or treasury management
- Creation or approval of financial-system budget reallocations
- Manual entry of actual expenditure as an authoritative value
- Exchange-rate trading or foreign-currency accounting
- Complex pooled-fund allocation optimisation
- Predictive forecasting, AI recommendations or arbitrary formula builders
- Automatic tender criteria or contract-clause generation
- Unverified savings, cost avoidance, benefits or causal procurement claims

## 5. Terminology and canonical amounts

| Term | Meaning |
|---|---|
| Budget | The entity and fiscal-period procurement funding envelope registered in KenTender |
| Budget Line | A stable funded purpose within the Budget; its approved amount is the allocation |
| Baseline | The currently verified approved line amounts and metadata used for procurement control |
| Reservation | A temporary hold against a Budget Line for an approved demand before contract commitment |
| Commitment | The current total contractual obligation recorded from an award/contract, including amounts already paid |
| Actual Expenditure | Read-only paid/consumed amount received from the authoritative financial system |
| Outstanding Commitment | Commitment less Actual Expenditure |
| Available | Approved amount not held by Active reservations or total contract commitments |
| Budget Revision | A controlled KenTender application of an externally approved baseline change |
| Funding Treatment | The budget-stage response to an applicable Plan Value Commitment |

Canonical calculations:

```text
Budget Approved = sum of Active Budget Line approved amounts
Line Reserved = sum of Active, unconverted reservation balances
Line Committed = sum of current total contract commitments
Line Available = Line Approved - Line Reserved - Line Committed
Budget Available = sum of Line Available
Outstanding Commitment = Line Committed - Actual Expenditure
```

Actual Expenditure is not subtracted again from Available because it is included in the total contract commitment. Any release of unused contract funding must be an authorised commitment adjustment.

## 6. Functional requirements

### 6.1 Budget portfolio and baseline

| ID | Requirement |
|---|---|
| BUD-FR-001 | Budgets shall be scoped to the current procuring entity and fiscal period. |
| BUD-FR-002 | Cross-entity access shall require explicit authority. |
| BUD-FR-003 | A Budget shall have a system-generated reference, title, entity, fiscal period, currency and owner. Users shall not enter or maintain the reference. |
| BUD-FR-004 | MVP 1 shall register the approved baseline through one direct-capture form; file import and baseline synchronisation are not MVP registration paths. |
| BUD-FR-005 | Direct capture shall record the authoritative approval reference, approval date, approved total and approval evidence. |
| BUD-FR-006 | Only one Active Budget may cover the same fiscal period for an entity. Multiple funding sources shall be represented by Budget Lines. |
| BUD-FR-007 | Activation shall mean verified for procurement use in KenTender; it shall not represent statutory appropriation approval. |
| BUD-FR-008 | Budget header totals shall be derived from Budget Lines and funding activity. |
| BUD-FR-009 | Active Budgets and their lines shall not be edited directly. |
| BUD-FR-010 | The portfolio shall show Draft, Submitted, Returned, Active and Closed Budgets plus assigned review work and funding exceptions. |

### 6.2 Budget Lines and funding sources

| ID | Requirement |
|---|---|
| BUD-FR-015 | A Budget shall contain one or more Budget Lines. |
| BUD-FR-016 | Each line shall have a system-generated reference, title, organisational owner, classification, funding-source metadata and approved amount. An external financial line reference is optional. |
| BUD-FR-017 | Funding-source type shall be Exchequer, Own source, Donor or grant, or Other. |
| BUD-FR-018 | One line shall use one currency and one funding source; co-funded procurement shall use separate reservations against separate lines. |
| BUD-FR-019 | Approved amounts shall be positive and expressed in the Budget currency. |
| BUD-FR-020 | Line references shall be generated by the system, unique within the entity and stable after creation. Users shall not enter or maintain them. |
| BUD-FR-021 | A line may not have a negative Available amount. |
| BUD-FR-022 | Exhausted, Partially available and Available shall be derived funding conditions, not workflow states. |
| BUD-FR-023 | If an external approved total is supplied, the sum of line approved amounts shall match it before activation. |

### 6.3 Strategy and Plan Value Commitments

| ID | Requirement |
|---|---|
| BUD-FR-030 | Every Budget Line shall reference one primary effective Active Performance Target using the Strategy Reference contract. |
| BUD-FR-031 | A line may reference supporting Performance Targets only with a recorded reason. |
| BUD-FR-032 | The stored reference shall include internal identifiers, plan/version, complete path and an immutable human-readable snapshot. |
| BUD-FR-033 | Historical references shall remain resolvable after Strategy supersession. |
| BUD-FR-034 | Before activation, Strategy shall return applicable Plan Value Commitments linked to the line's target context and structured category information. |
| BUD-FR-035 | A funding treatment shall be recorded for every applicable Required commitment. |
| BUD-FR-036 | Funding treatment shall be Dedicated allocation, Embedded in line, No direct allocation required, or Not applicable. |
| BUD-FR-037 | Dedicated allocation requires an amount; dedicated amounts on one line shall be exclusive and shall not exceed the line approved amount in aggregate. |
| BUD-FR-038 | Embedded in line shall record rationale but shall not claim a distinct amount. |
| BUD-FR-039 | No direct allocation required and Not applicable require a reason; Not applicable additionally requires reviewer acceptance. |
| BUD-FR-040 | Recommended and Available commitments may be treated but shall not block activation unless configured by an authorised entity policy. |
| BUD-FR-041 | Funding treatments shall lock when the Budget is Active. Material change requires a Budget Revision. |
| BUD-FR-042 | Budget & Funding shall not modify the Plan Value Commitment or create downstream tender treatment. |

### 6.4 Review and activation

| ID | Requirement |
|---|---|
| BUD-FR-050 | Budget Officer shall capture the Draft baseline and submit it for review. |
| BUD-FR-051 | Budget Reviewer shall verify the authoritative approval information, line totals, classifications, Strategy alignment and Required funding treatments. |
| BUD-FR-052 | Budget Reviewer may return the baseline with specific reasons. |
| BUD-FR-053 | Budget Authority shall activate a reviewed baseline for procurement use. |
| BUD-FR-054 | A submitter shall not activate the same Budget. |
| BUD-FR-055 | Activation shall atomically lock the baseline and record actor, time, authoritative approval reference and evidence. |
| BUD-FR-056 | Optional additional review may be configured for donor-funded or exceptional Budgets without changing the standard workflow. |

### 6.5 Funding checks and reservations

| ID | Requirement |
|---|---|
| BUD-FR-060 | A funding check shall validate entity, fiscal period, Active Budget, Active line, currency, available amount and downstream authority. |
| BUD-FR-061 | A successful funding check shall return the line, amount requested, Available before, Available after and applicable funding-treatment context. |
| BUD-FR-062 | Demand approval may atomically create one or more reservations for the approved demand. |
| BUD-FR-063 | A reservation shall reference exactly one Budget Line and one approved Demand; co-funding uses multiple reservations. |
| BUD-FR-064 | Reservation creation shall be transactional, concurrency-safe and idempotent. |
| BUD-FR-065 | A reservation shall retain one identity as the Demand progresses through Planning, Package and Tender. |
| BUD-FR-066 | Planning and Tender shall inherit and revalidate the reservation but shall not create a duplicate hold. |
| BUD-FR-067 | A reservation may be increased only through a new funding check and authorised downstream change. |
| BUD-FR-068 | A reservation may be released when the linked work is cancelled, reduced, expired or no longer requires the funds. |
| BUD-FR-069 | Release shall record amount, reason, actor, time and affected downstream record. |
| BUD-FR-070 | Insufficient funding shall block reservation and return the shortfall and valid next action. |

### 6.6 Contract commitments and expenditure

| ID | Requirement |
|---|---|
| BUD-FR-075 | Award shall revalidate reserved and available funding before financial clearance. |
| BUD-FR-076 | Contract activation shall convert all or part of the linked reservation into a commitment atomically. |
| BUD-FR-077 | One reservation may be partially converted into multiple commitments where an approved demand results in multiple contracts or lots. |
| BUD-FR-078 | Any unrequired reservation balance shall remain reserved with justification or be released. |
| BUD-FR-079 | Commitment increase for a contract variation shall require available funding and the authorised variation approval. |
| BUD-FR-080 | Commitment reduction or closure shall release only the authorised unused amount. |
| BUD-FR-081 | Actual Expenditure shall be read-only data received from the authoritative financial system. |
| BUD-FR-082 | If expenditure data is unavailable or stale, the UI shall show Unknown or Stale, not zero. |
| BUD-FR-083 | A mismatch such as Actual Expenditure exceeding Commitment shall create a reconciliation exception and shall not silently change Available. |

### 6.7 Budget revisions

| ID | Requirement |
|---|---|
| BUD-FR-090 | Active Budgets and Budget Lines shall change only through a Budget Revision. |
| BUD-FR-091 | A Budget Revision shall apply an externally approved Supplementary allocation, Reduction, Transfer, New line, Line amendment or Correction. |
| BUD-FR-092 | The revision shall record the external approval reference and evidence; KenTender does not grant the underlying financial approval. |
| BUD-FR-093 | The revision shall show affected lines, before, change, after, Available after and downstream impact. |
| BUD-FR-094 | A transfer shall balance unless the type is Supplementary allocation or Reduction. |
| BUD-FR-095 | No line may be reduced below Active reservations plus current total commitments. |
| BUD-FR-096 | Strategy-reference or funding-treatment changes require justification and revalidation. |
| BUD-FR-097 | Applied revisions shall update affected lines atomically and preserve immutable before/after evidence. |
| BUD-FR-098 | Existing reservations and commitments shall retain their identities and historical snapshots after a revision. |
| BUD-FR-099 | A revision affecting active downstream work shall identify blockers and warnings before application. |

### 6.8 Usage, operations and management oversight

| ID | Requirement |
|---|---|
| BUD-FR-105 | Budget workspace shall show read-only use by Demand, Planning, Package, Tender, Award, Contract and Finance where available. |
| BUD-FR-106 | Usage and balances shall be derived from authoritative references and shall not be manually editable. |
| BUD-FR-107 | Funding Activity shall distinguish reservations, commitments and Actual Expenditure without summing overlapping lifecycle values. |
| BUD-FR-108 | Funding Performance shall show approved, available, reserved, committed and actual amounts with their calculation basis and source freshness. |
| BUD-FR-109 | Funding Performance shall show funding coverage by Strategy Outcome and Target. |
| BUD-FR-110 | Funding Performance shall show Required Plan Value Commitments with Dedicated, Embedded, No direct allocation and Not-applicable treatment. |
| BUD-FR-111 | It shall identify unfunded targets, untreated Required commitments, insufficient demands, expiring/aged reservations, commitment overruns and reconciliation exceptions. |
| BUD-FR-112 | Strategy alignment, funding treatment and procurement activity shall not be presented as proof that an outcome was achieved. |
| BUD-FR-113 | Every management value shall expose reporting period, `As at`, source coverage and drill-down references. |
| BUD-FR-114 | Authorised users may export the current filtered Funding Performance view with lineage and source metadata. |

## 7. Clean domain model

### 7.1 Budget

| Field | Requirement |
|---|---|
| internal_id | Immutable system identifier |
| budget_code | Required stable business code |
| title | Required |
| procuring_entity | Required |
| fiscal_period | Required controlled reference |
| start_date / end_date | Required valid period |
| currency | Required single Budget currency |
| registration_source | System-controlled as Direct capture for MVP 1; reserved for future API extension |
| authoritative_reference | Required approved-budget reference |
| external_approved_total | Optional reconciliation value |
| approval_date | Required |
| approval_evidence | Required |
| budget_owner | Required |
| status | Workflow-controlled |
| submitted / reviewed / activated metadata | System-controlled |

### 7.2 Budget Line

| Field | Requirement |
|---|---|
| internal_id | Immutable stable identifier |
| budget | Required parent |
| line_code | Required stable code |
| title | Required |
| organisational_owner | Required |
| classification | Required controlled goods, works, services or consultancy classification |
| procurement_category | Optional controlled category used for applicability |
| funding_source_type / name / reference | Required |
| approved_amount | Required positive amount in Budget currency |
| primary_strategy_reference | Required versioned Performance Target reference and snapshot |
| supporting_strategy_references | Optional target references with reasons |
| source_line_reference | Optional external financial-system line reference |
| order_index | Required non-negative integer |

### 7.3 Budget Value Treatment

| Field | Requirement |
|---|---|
| budget_line | Required |
| plan_value_commitment_version | Required immutable reference |
| consideration_level | Read-only snapshot from Strategy |
| treatment | Dedicated allocation, Embedded in line, No direct allocation required or Not applicable |
| dedicated_amount | Required only for Dedicated allocation |
| rationale | Required |
| reviewer_acceptance | Required for Not applicable |
| reference_snapshot | Required human-readable snapshot |

### 7.4 Funding Reservation

| Field | Requirement |
|---|---|
| internal_id | Immutable identifier |
| budget_line | Required |
| demand | Required approved Demand |
| amount / currency | Required Budget-currency amount |
| remaining_reserved | System-derived |
| current_downstream_reference | Current Planning, Package or Tender reference where applicable |
| status | Reserved, Partially converted, Converted, Released, Cancelled or Expired |
| expiry_date | Optional controlled date |
| idempotency_key | Required unique operation key |
| created / released metadata and reason | System-controlled/required where applicable |

### 7.5 Procurement Commitment

| Field | Requirement |
|---|---|
| internal_id | Immutable identifier |
| budget_line / reservation | Required source references |
| contract | Required authoritative contract reference |
| original_amount | Initial converted amount |
| current_amount | Current authorised total contract obligation |
| actual_expenditure | Latest read-only finance value |
| outstanding_amount | System-derived current amount less actual |
| status | Active, Closed or Cancelled |
| adjustment_history | Derived from authorised contract/variation events |

### 7.6 Expenditure Snapshot

| Field | Requirement |
|---|---|
| commitment / contract / budget_line | Required references |
| amount / currency | Required source value |
| source_system / source_reference | Required |
| source_as_at / received_at | Required |
| reconciliation_status | Matched, Stale, Exception or Unavailable |

### 7.7 Budget Revision and Revision Line

| Field | Requirement |
|---|---|
| budget | Required Active Budget |
| revision_number | System-generated sequence |
| revision_type | Controlled value |
| external_approval_reference / evidence | Required |
| reason | Required |
| status | Workflow-controlled |
| line | Existing or proposed new Budget Line |
| before_amount / change / after_amount | Required calculated values |
| metadata_changes | Structured before/after values where applicable |
| downstream_impact | System-derived summary |
| applied_by / applied_at | System-controlled |

## 8. Governance and state transitions

### 8.1 Budget

| Current | Action | Next | Actor | Guards |
|---|---|---|---|---|
| Draft | Submit | Submitted | Budget Officer | Readiness passes |
| Returned | Resubmit | Submitted | Budget Officer | Return issues resolved |
| Submitted | Return | Returned | Budget Reviewer | Reason required |
| Submitted | Mark reviewed | Submitted | Budget Reviewer | Review checklist complete |
| Submitted | Activate for procurement | Active | Budget Authority | Reviewed; submitter is not activator; source evidence valid |
| Active | Close | Closed | Budget Authority | Open reservations resolved; reason required |
| Draft / Returned | Cancel | Cancelled | Budget Officer or Authority | Reason required |

Reviewer completion shall be recorded separately from Budget status so the standard flow remains simple.

### 8.2 Budget Revision

| Current | Action | Next | Actor | Guards |
|---|---|---|---|---|
| Draft | Submit | Submitted | Budget Officer | Impact checks complete |
| Returned | Resubmit | Submitted | Budget Officer | Issues resolved |
| Submitted | Return | Returned | Budget Reviewer | Reason required |
| Submitted | Reject | Rejected | Budget Authority | Reason required |
| Submitted | Apply | Applied | Budget Authority | Reviewed; external approval valid; blockers absent |
| Draft / Returned | Cancel | Cancelled | Budget Officer | Reason required |

### 8.3 Funding activity

- Reservation creation, increase, release and conversion are governed service actions, not manual status edits.
- Commitment creation and adjustment are driven by authorised Award, Contract and Variation events.
- Actual Expenditure updates are integration events and never user approvals.

## 9. Roles and permissions

| Capability | Budget Viewer | Budget Officer | Budget Reviewer | Budget Authority | Procurement User | Auditor | Finance Integration |
|---|---:|---:|---:|---:|---:|---:|---:|
| View Active funding context | Yes | Yes | Yes | Yes | Assigned records | Yes | Service only |
| View Draft/Returned Budgets | No | Assigned entity | Assigned entity | Assigned authority | No | Yes | No |
| Create/edit Draft baseline | No | Yes | No | No | No | No | No |
| Submit baseline/revision | No | Yes | No | No | No | No | No |
| Review/return | No | No | Yes | Yes | No | No | No |
| Activate/apply/close | No | No | No | Yes | No | No | No |
| Run funding check | View only | Yes | Yes | Yes | Assigned record | Yes | No |
| Create/release reservation | No | Service via authorised workflow | No | Override only | Via Demand workflow | No | No |
| Convert/adjust commitment | No | No | No | Exception authority | Via Contract workflow | No | No |
| View Funding Performance | Yes | Assigned entity | Assigned entity | Assigned authority | No | Yes | No |
| Export Funding Performance | Assigned entity | No | Assigned entity | Assigned authority | No | Yes | No |
| Sync baseline/expenditure | No | No | No | No | No | View | Yes |
| View audit | No | Own actions | Assigned entity | Assigned authority | Assigned records | Yes | Integration events |

Users may hold multiple roles, but the submitter shall not activate the same Budget or apply their own Revision. Budget Viewer is the read-only management profile.

## 10. Readiness rules

Budget submission or activation shall be blocked by:

- Missing authoritative reference, approval date or approval evidence
- Invalid fiscal period or currency
- No Budget Line
- Duplicate or invalid line code
- Missing line owner, classification or funding source
- Non-positive approved amount
- Line totals not matching a supplied external approved total
- Missing or invalid primary Strategy target
- Supporting Strategy target without a reason
- Required Plan Value Commitment without a complete funding treatment
- Dedicated treatment amounts exceeding the line approved amount
- Cross-entity or cross-currency reference

Issues shall be grouped as Source, Budget Lines, Strategy and Value Commitments, and Governance and shall link to the correction location.

## 11. Screen inventory

| Screen ID | Screen | Purpose |
|---|---|---|
| BUD-UI-01 | Budget Portfolio | Find Budgets, assigned reviews and operational exceptions |
| BUD-UI-02 | Funding Performance | Read-only management view of funding coverage, value treatment and risks |
| BUD-UI-03 | Budget Overview | Show baseline identity, source, period, totals and status |
| BUD-UI-04 | Budget Lines | Review lines, balances, Strategy alignment and attention |
| BUD-UI-05 | Budget Line Editor | Capture line funding, Strategy references and value treatments |
| BUD-UI-06 | Funding Check and Reservation | Contextual Demand/Planning funding decision and reservation result |
| BUD-UI-07 | Funding Activity | Show reservations, commitments, expenditure and reconciliation status |
| BUD-UI-08 | Budget Revision | Propose externally approved line changes with before/after impact |
| BUD-UI-09 | Revision Review | Review financial, Strategy and downstream impact before application |
| BUD-UI-10 | Downstream Usage | Show Demand through Contract references without editing them |
| BUD-UI-11 | Readiness and Review | Resolve blockers, submit, return and activate/apply according to authority |
| BUD-UI-12 | Audit History | Show baseline, revision, reservation, commitment and integration events |

Budget workspace tabs shall be Overview, Budget Lines, Funding Activity, Revisions, Downstream Usage, Review and Audit. Funding Performance is a separate management entry view, not an eighth workspace tab.

## 12. UX requirements

1. Use a Budget Portfolio plus focused Budget workspace; do not expose raw record lists as the primary experience.
2. Budget Viewer opens Funding Performance; operational roles open Budget Portfolio and may switch to Funding Performance.
3. Show Approved, Available, Reserved, Committed and Actual together with concise definitions; do not add them into one total.
4. Show Actual as Unknown or Stale when finance data is unavailable.
5. Ordinary procurement users see Budget linked, Funding available, Funding reserved or Insufficient funds.
6. Budget/finance/audit users may see Allocation, Reservation, Commitment, Actual and Outstanding commitment.
7. A funding check shall show requested amount, Available before, Available after and one clear decision.
8. Active Budget fields are read-only; Request revision is the valid change action.
9. Revision screens shall show before, change, after and affected downstream work.
10. Strategy target and Plan Value Commitment treatment shall be visible without implying tender treatment.
11. Status shall use text and non-colour cues.
12. Use compact tables and focused drawers; avoid card walls, nested accordions and accounting-ledger presentation.
13. Do not show savings, performance scores or unsupported benefit claims.
14. Every empty, stale-source, returned and insufficient-funding state shall explain the next valid action.
15. Keyboard navigation, visible focus, accessible labels and adequate contrast are required.
16. Navigation and global toolbars are outside Stitch scope unless explicitly requested.

## 13. Service and downstream contracts

| Contract | Requirement |
|---|---|
| list_budgets | Return entity-scoped Budgets filtered by fiscal period and status |
| get_budget | Return baseline identity, derived totals, source and permissions |
| list_budget_lines | Return lines, derived balances, Strategy snapshots and attention |
| get_budget_readiness | Return grouped blockers with edit locations |
| check_funding | Validate amount/context without mutating funds |
| reserve_funding | Atomically and idempotently create a reservation from an authorised Demand event |
| revalidate_reservation | Confirm inherited reservation remains valid at Planning/Tender gates |
| release_reservation | Release an authorised amount with reason and lineage |
| convert_reservation | Atomically create one or more commitments and release/retain remainder |
| adjust_commitment | Apply an authorised contract/variation adjustment |
| list_funding_activity | Return reservations, commitments, actuals and reconciliation states |
| get_budget_usage | Return read-only downstream references |
| get_funding_performance | Return Strategy funding coverage, value treatment, balances, exceptions and source freshness |
| export_funding_performance | Export the authorised filtered management view with lineage |
| sync_expenditure | Store read-only expenditure snapshots and reconciliation status |

All mutation services shall enforce permission, state, entity, currency, idempotency and current balance server-side. Funding checks alone do not reserve money.

Downstream ownership:

| Module | Contract with Budget & Funding |
|---|---|
| Strategy | Supplies Active target references and applicable Plan Value Commitments; receives read-only funding usage |
| Demand | Selects funding, obtains the check and creates the reservation through approval |
| Planning | Inherits and revalidates the reservation; does not create another hold |
| Tender | Carries immutable funding context and revalidates before controlled gates |
| Award | Compares proposed award against reservations and available authorised funding |
| Contract | Converts reservations to commitments and submits authorised adjustments |
| Finance system | Supplies approved baselines and expenditure facts; remains authoritative |

## 14. Notifications, audit and security

Notify or queue work for:

- Budget submitted or returned
- Budget ready for activation
- Revision submitted, returned, rejected or applied
- Reservation near expiry or expired
- Insufficient-funding exception
- Commitment increase requiring funding
- Expenditure reconciliation exception or stale finance source
- Untreated Required Plan Value Commitment

Audit shall record baseline creation, source validation, submission, review, activation, close, line change, value treatment, reservation, release, conversion, commitment adjustment, revision and expenditure-sync events with actor/service, timestamp, before/after and reason where applicable.

Server controls shall prevent cross-entity access, direct status mutation, unauthorised evidence access, duplicate reservation, replayed integration events and balance oversubscription.

## 15. Ministry of Health fixture

### Budget

- Budget: `MOH-BUD-2027-2028` — Ministry of Health Procurement Budget FY 2027/2028
- Entity: Ministry of Health
- Currency: KES
- Registration source: Direct capture
- Status: Active
- External approval reference: `MOH-FIN-BUD-2027-01`

### Lines

| Code | Title | Approved | Primary target |
|---|---|---:|---|
| MOH-BL-DHI-01 | Digital clinical systems infrastructure | 480,000,000 | MOH-TGT-01 — At least 99.9% annual availability |
| MOH-BL-CAP-01 | Digital health technical capability | 80,000,000 | Illustrative Active capability target |

For `MOH-BL-DHI-01`, seed:

- PVO-EFT-01 — Required — Embedded in line
- PVO-ECO-01 — Required — Dedicated allocation of KES 40,000,000
- PVO-RES-01 — Recommended — Embedded in line
- PVO-SUS-02 — Required — No direct allocation required, with rationale that disposal cost is included in asset-replacement activities

Seed one approved demand reservation of KES 455,000,000, one contract commitment of KES 310,000,000 in a separate scenario or line state that does not double-count the reservation, and a finance expenditure snapshot sufficient to exercise Matched and Stale states. Fixtures shall produce mathematically valid balances and be repeatable.

## 16. MVP teardown and rebuild

Existing Budget MVP data may be reset. There is no production-data migration requirement for this redesign.

Implementation shall:

1. Remove manual budget-header totals and conflicting Available formulas.
2. Remove redundant Allocation objects where they merely duplicate Budget Line approved amounts.
3. Remove duplicate reservation creation across Demand, Planning, Package and Tender.
4. Replace direct Active-budget editing with controlled Revision application.
5. Replace old Strategy cascades with the versioned Strategy Reference contract and Plan Value Commitment treatments.
6. Replace manually authoritative Actual Spend fields with finance snapshots and explicit Unknown/Stale states.
7. Reset and reseed affected Budget, Demand, Planning, Tender and Contract demo references.
8. Preserve unrelated master data and user changes.

Cursor shall identify exact destructive targets and consumers before executing the rebuild.

## 17. Acceptance criteria

| ID | Acceptance criterion |
|---|---|
| BUD-AC-001 | An authorised officer can directly capture a complete Draft baseline without entering calculated header totals or system references. |
| BUD-AC-002 | Activation is blocked until authoritative approval information, lines, Strategy alignment, Required value treatments and governance checks pass. |
| BUD-AC-003 | Budget totals equal the sum of line amounts and current funding activity. |
| BUD-AC-004 | Every active line has one valid primary Strategy target and historical snapshots survive Strategy supersession. |
| BUD-AC-005 | Every applicable Required Plan Value Commitment has a valid funding treatment. |
| BUD-AC-006 | Dedicated treatment amounts cannot exceed the line approved amount in aggregate. |
| BUD-AC-007 | Budget treatment never creates or implies a tender criterion or contract clause. |
| BUD-AC-008 | A funding check does not mutate the balance. |
| BUD-AC-009 | Concurrent or repeated reservation requests cannot oversubscribe or duplicate a hold. |
| BUD-AC-010 | One reservation identity travels through Planning and Tender without another reservation. |
| BUD-AC-011 | A reservation can convert partially into multiple commitments and the remainder is retained or released explicitly. |
| BUD-AC-012 | Available excludes Active reservations and total commitments but does not double-count Actual Expenditure. |
| BUD-AC-013 | Insufficient funding blocks reservation and returns the shortfall and valid next action. |
| BUD-AC-014 | Contract variation increases require available funding and authorised variation approval. |
| BUD-AC-015 | Active Budgets cannot be edited directly. |
| BUD-AC-016 | A revision cannot reduce a line below Active reservations plus total commitments. |
| BUD-AC-017 | Applied revisions preserve immutable before/after values and downstream identities. |
| BUD-AC-018 | The Budget submitter cannot activate the same Budget or apply their own Revision. |
| BUD-AC-019 | Entity permissions block unauthorised UI and API access. |
| BUD-AC-020 | Actual Expenditure is read-only and unavailable/stale source data is not shown as zero. |
| BUD-AC-021 | Funding Performance separates lifecycle amounts, exposes source freshness and supports traceable drill-down. |
| BUD-AC-022 | Funding Performance distinguishes value treatment from achieved strategic outcomes. |
| BUD-AC-023 | Controlled exports reproduce the authorised filters, period, `As at`, source coverage and lineage. |
| BUD-AC-024 | Ministry of Health fixtures load repeatably with valid balances and linkages. |
| BUD-AC-025 | No obsolete Strategy cascade, duplicate reservation path, manual total or conflicting balance formula remains active. |
| BUD-AC-026 | Core screens satisfy approved Stitch designs without unapproved accounting functionality. |

## 18. Required test matrix

### Domain and calculations

- Budget/line identity and uniqueness
- Header and line roll-ups
- Reservation, partial conversion and commitment calculations
- Actual-expenditure non-double-counting
- Currency, period and entity validation
- Dedicated value-treatment limits
- Revision balancing and minimum-line guard

### Workflow and permissions

- Every valid and invalid Budget/Revision transition
- Submitter/activator segregation
- Entity and evidence access
- Active immutability
- Integration replay and idempotency

### Concurrency and services

- Parallel reservation attempts
- Repeated idempotency key
- Funding check versus reservation distinction
- Reservation inheritance and revalidation
- Partial/multiple conversion
- Commitment adjustment
- Stale/unavailable finance source

### Strategy and downstream regression

- Active target selector and historical snapshot
- Applicable Plan Value Commitments
- Required treatment and approved Not applicable
- Demand reservation creation
- Planning/Tender inheritance
- Award revalidation
- Contract conversion and variation
- Strategy funding usage

### Browser tests

- All twelve screens and essential empty, stale, returned, read-only and exception states
- Budget creation, review and activation
- Budget Line target and value treatment
- Funding check and reservation
- Funding Activity and drill-down
- Revision before/after review
- Funding Performance and export
- Keyboard and focus behaviour

## 19. Non-functional requirements

1. Funding mutation transactions shall use database locking or equivalent concurrency control.
2. Mutation services shall be idempotent and safe to retry.
3. Money shall use fixed-precision decimal values; floating-point storage is prohibited.
4. API amounts shall include currency and canonical precision.
5. List and activity APIs shall be paginated or bounded.
6. Roll-ups shall avoid per-line/per-reference query loops.
7. Expenditure API integration shall expose last-success, source timestamp and errors when implemented.
8. Exported values shall match the authorised filtered view and prevent formula injection.
9. Status shall not rely on colour alone.
10. Errors shall state the corrective action without exposing stack traces or sensitive finance details.

## 20. Deferred backlog

- Full bidirectional IFMIS/ERP budgeting integration
- API-based approved-baseline registration and synchronisation
- Appropriation and cash-release workflow
- General-ledger or chart-of-accounts management
- Invoice/payment approval
- Advanced multi-year funding optimisation
- Complex pooled-fund apportionment
- Foreign-currency revaluation
- Predictive funding forecasts
- AI recommendations
- Cross-government consolidated funding analytics

## 21. Lock decisions

1. The module name remains Budget & Funding.
2. The financial system remains authoritative for approved budgets and expenditure.
3. KenTender activates an approved baseline for procurement; it does not approve the appropriation.
4. Budget Line approved amount is the allocation; no duplicate Allocation object is required.
5. One reservation follows a Demand through Planning and Tender.
6. Commitment is the total current contract obligation and includes paid amounts.
7. Actual Expenditure is read-only and is not subtracted twice.
8. Active Budget changes use an externally evidenced Revision.
9. One primary Strategy Performance Target is required per Budget Line.
10. Applicable Plan Value Commitments receive explicit funding treatment.
11. Funding treatment does not impose tender treatment.
12. Funding Performance is separate from operational Budget maintenance.
13. No scores, unverified savings or causal achievement claims are included.

## 22. Requirements-lock checklist

- Procurement-control boundary and finance-system ownership
- Canonical formulas
- Budget Line and funding-source model
- Strategy target and Plan Value Commitment linkage
- Approval, activation and revision governance
- Reservation and commitment lifecycle
- Downstream ownership
- Funding Performance management view
- Roles and segregation
- Screen inventory
- Service contracts
- Ministry of Health fixture
- Acceptance criteria and test matrix
- Teardown authority and scope

Once locked, Stitch prompts and the Cursor implementation prompt shall reference `BUDGET-MVP1-REQ-1.1` and the approved screen IDs.
