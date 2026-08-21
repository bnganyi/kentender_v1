# Budget & Funding — Stitch Prompts

**Reference:** `BUDGET-MVP1-REQ-1.1`  
**Module:** Budget & Funding  
**Design objective:** Complete but simple procurement funding control  
**Primary fixture:** Ministry of Health

## How to use this document

Run the prompts in order. Give Stitch the previous approved screen as a visual reference when generating the next screen.

The prompts cover the complete MVP through eight focused designs. Related screen states are deliberately grouped so the module does not become a collection of disconnected pages.

## Global design rules

Apply these rules to every prompt:

- Design the main content area only. Do not redesign navigation, branding or global toolbars.
- Use a restrained government enterprise style consistent with existing KenTender screens.
- Use compact tables, simple summary strips and focused forms.
- Avoid card walls, decorative charts, nested accordions and accounting-ledger layouts.
- The financial system remains authoritative for approved budgets and actual expenditure.
- Do not design budget formulation, general-ledger, payment or invoice functions.
- Show business titles first. Show system-generated references as small secondary text.
- Do not ask users to create or edit reference codes.
- Use KES formatting with comma separators and no unnecessary decimal places.
- Status must use text and colour; never colour alone.
- Use only clear actions that describe their destination or outcome.
- Active budgets are read-only. Changes require a Budget Revision.
- Do not show scores, savings claims, forecasts or inferred strategic achievement.
- Do not imply that Strategy alignment proves outcome achievement.
- Use accessible labels, visible focus states and explanatory text of at least 12px.

## Shared Ministry of Health fixture

Use this data consistently across all screens:

- Budget: Ministry of Health Procurement Budget FY 2027/28
- System reference: `MOH-BUD-0001`
- Entity: Ministry of Health
- Fiscal period: FY 2027/28
- Currency: KES
- Registration source: Direct capture
- External approval reference: `MOH-FIN-BUD-2027-01`
- Status: Active
- Approved: KES 560,000,000
- Reserved: KES 145,000,000
- Committed: KES 310,000,000
- Available: KES 105,000,000
- Actual expenditure: KES 180,000,000
- Outstanding commitment: KES 130,000,000

Budget lines:

1. Digital clinical systems infrastructure
   - System reference: `MOH-BL-0001`
   - Approved: KES 480,000,000
   - Reserved: KES 145,000,000
   - Committed: KES 310,000,000
   - Available: KES 25,000,000
   - Actual: KES 180,000,000
   - Primary target: At least 99.9% annual service availability

2. Digital health technical capability
   - System reference: `MOH-BL-0002`
   - Approved: KES 80,000,000
   - Reserved: KES 0
   - Committed: KES 0
   - Available: KES 80,000,000
   - Actual: Unknown
   - Primary target: Train and certify 150 digital-health technical staff

Plan Value Commitment treatments for the first line:

- Improve infrastructure efficiency — Required — Embedded in line
- Reduce whole-life infrastructure cost — Required — Dedicated allocation of KES 40,000,000
- Improve system resilience — Recommended — Embedded in line
- Ensure responsible asset disposal — Required — No direct allocation required; disposal cost is included in asset-replacement activities

---

## Prompt 1 — Budget Portfolio

Design the main content for the Budget & Funding landing screen.

Header:

- Title: Budget & Funding
- Description: “Manage approved procurement funding and monitor its use across the procurement lifecycle.”
- Primary action: Register approved budget
- Secondary action: View funding performance

Add a compact filter row:

- Fiscal period
- Status
- Search by budget title or external approval reference

Add a small summary strip:

- Active budgets — 1
- Awaiting review — 1
- Returned — 0
- Funding exceptions — 1

Use one compact table with:

- Budget
- Fiscal period
- Budget owner
- Approved
- Available
- Status
- Attention
- Action

Illustrative rows:

1. Ministry of Health Procurement Budget FY 2027/28
   - Secondary reference: `MOH-BUD-0001`
   - Director, Finance and Accounts
   - Approved: KES 560M
   - Available: KES 105M
   - Active
   - Attention: Actual expenditure stale on 1 line
   - Action: Open budget

2. Ministry of Health Procurement Budget FY 2028/29
   - Secondary reference: `MOH-BUD-0002`
   - Director, Finance and Accounts
   - Approved: KES 600M
   - Available: Not active
   - Under review
   - Attention: 2 readiness issues
   - Action: Review budget

3. Ministry of Health Procurement Budget FY 2026/27
   - Secondary reference: `MOH-BUD-0003`
   - Director, Finance and Accounts
   - Approved: KES 520M
   - Available: KES 0
   - Closed
   - Attention: None
   - Action: View budget

Include a simple empty state for entities with no registered budget:

- “No procurement budget has been registered for this fiscal period.”
- Action: Register approved budget

Do not add charts.

---

## Prompt 2 — Register Approved Budget

Design the main content for registering an approved procurement budget in KenTender.

This screen creates the Budget workspace. It does not formulate or approve the government budget.

Header:

- Title: Register approved budget
- Description: “Register an approved financial baseline for procurement use in KenTender.”

Use one focused form with these sections.

### Budget identity

- Procuring Entity — read-only: Ministry of Health
- Budget title — Ministry of Health Procurement Budget FY 2028/29
- Fiscal period — FY 2028/29
- Currency — KES
- Budget owner — Director, Finance and Accounts

Do not include a Budget code field. The system-generated reference will be shown after creation.

### Approval details

Do not show source-mode choices, import controls or integration options.

Show these direct-capture fields:

- External approval reference — `MOH-FIN-BUD-2028-01`
- Approval date — 15 June 2028
- Approved total — KES 600,000,000
- Approval evidence — upload field showing `MOH_Budget_Approval_FY2028_29.pdf`

Add this neutral information note:

“KenTender records the approved baseline for procurement control. Budget formulation, appropriation and financial approval remain in the authoritative financial process. Future financial-system integration will use an API.”

Footer actions:

- Cancel
- Create draft budget

Keep the page short. Do not add steps, header totals, Strategy fields or Budget Lines to this screen. Those are completed inside the created Budget workspace.

---

## Prompt 3 — Funding Performance

Design a read-only management screen named Funding Performance.

Header:

- Title: Funding Performance
- Description: “Monitor procurement funding coverage, commitments and exceptions.”
- Action: Export report

Filters:

- Fiscal period
- Programme
- Primary strategic target
- Funding status

Show the selected entity and an “As at” timestamp.

Add a six-item summary strip using the shared fixture:

- Approved — KES 560M
- Reserved — KES 145M
- Committed — KES 310M
- Available — KES 105M
- Actual expenditure — KES 180M
- Lines needing attention — 1

Add a compact table named Strategy Funding Coverage with:

- Strategic target
- Budget lines
- Approved
- Reserved
- Committed
- Available
- Value treatment
- Attention
- Action

Show the strategic target title first and its generated reference as secondary text.

Add a second compact table named Funding Exceptions with:

- Exception
- Budget line
- Owner
- Age
- Action

Illustrative exception:

- Actual expenditure data is stale
- Digital clinical systems infrastructure
- Budget Officer
- Last updated 3 days ago
- Action: Review expenditure data

Add this note:

“Strategy alignment shows intended support. It does not prove that procurement caused the strategic result.”

Do not add performance scores, savings or predictive charts.

---

## Prompt 4 — Budget Overview

Design the Overview tab of a focused Budget workspace.

Header:

- Title: Ministry of Health Procurement Budget FY 2027/28
- Secondary reference: `MOH-BUD-0001`
- Status: Active
- Primary action: Request revision
- Secondary action: View funding performance

Show these workspace tabs:

- Overview
- Budget Lines
- Funding Activity
- Revisions
- Downstream Usage
- Review
- Audit

The Overview tab must contain:

1. A compact identity strip:
   - Entity
   - Fiscal period
   - Currency
   - Source
   - External approval reference
   - Actual-expenditure data as at

2. A six-item funding summary:
   - Approved — KES 560M
   - Reserved — KES 145M
   - Committed — KES 310M
   - Available — KES 105M
   - Actual expenditure — KES 180M
   - Outstanding commitment — KES 130M

3. One stacked allocation bar:
   - Reserved — KES 145M
   - Committed — KES 310M
   - Available — KES 105M

4. A small Strategy Alignment section:
   - 2 of 2 lines linked to an Active primary target
   - 4 applicable Plan Value Commitments treated
   - Action: View budget lines

5. A small Attention section:
   - Actual expenditure is stale on 1 line
   - Action: Review funding activity

Add this concise definition:

“Available equals approved funding less active reservations and contract commitments. Actual expenditure is shown separately because it is already included within commitments.”

Do not make Active budget fields editable.

---

## Prompt 5 — Budget Lines and Line Editor

Design the Budget Lines tab and a focused Add/Edit Budget Line panel as two states of the same design.

### Budget Lines state

Header actions:

- Add budget line when the Budget is Draft or Returned
- Request revision when the Budget is Active

Use one compact table with:

- Budget line
- Funding source
- Primary strategic target
- Approved
- Reserved
- Committed
- Available
- Actual
- Status
- Action

Use the two shared fixture lines.

For Digital clinical systems infrastructure show:

- Actual: KES 180M — Stale
- Status: Needs attention
- Attention: Actuals last updated 3 days ago
- Action: Review line

For Digital health technical capability show:

- Actual: Unknown
- Status: Complete
- Attention: No commitments or expenditure recorded
- Action: View line

Show line titles first and generated references as secondary text.

### Budget Line Editor state

Use a focused side panel or page section, not a multi-step wizard.

Do not include an editable code field.

Section 1 — Funding details:

- Budget line title
- External financial-system line reference
- Classification
- Funding source
- Approved amount
- Responsible owner

Section 2 — Strategy alignment:

- Primary strategic target — required
- Supporting strategic targets — optional
- Reason for each supporting target — required when added

Only Active targets from the selected entity plan may be selected.

Section 3 — Plan Value Commitment treatment:

Use a compact table with:

- Commitment
- Requirement level
- Funding treatment
- Dedicated amount
- Rationale

Allowed treatments:

- Dedicated allocation
- Embedded in line
- No direct allocation required
- Not applicable

Require a rationale for No direct allocation required or Not applicable.

Show a validation summary:

- Approved amount
- Total dedicated treatment
- Remaining amount

Dedicated treatment amounts must not exceed the approved line amount.

Actions:

- Save budget line
- Cancel

---

## Prompt 6 — Funding Check and Reservation

Design a compact funding decision screen opened from an approved Demand or Procurement Plan item.

Header:

- Title: Check and reserve funding
- Description: “Confirm that approved procurement funding is available before this requirement proceeds.”

Show read-only procurement context:

- Demand: National digital health infrastructure upgrade
- Requesting department: Digital Health Directorate
- Requested amount: KES 455,000,000
- Primary strategic target: At least 99.9% annual service availability

Show a Budget Line selector with:

- Digital clinical systems infrastructure
- Available before: KES 480,000,000

Show the funding decision clearly:

- Decision: Funding available
- Requested: KES 455,000,000
- Available before: KES 480,000,000
- Available after: KES 25,000,000

Primary action:

- Reserve funding

Secondary action:

- Cancel

Add this note:

“This reservation follows the same requirement through Planning and Tendering. Those stages will not create additional funding holds.”

Also define an insufficient-funding state:

- Decision: Insufficient funding
- Disable Reserve funding
- Show Available and Shortfall
- Actions: Select another budget line or Return to demand

Do not expose accounting fields or allow users to type a reservation reference.

---

## Prompt 7 — Funding Activity and Downstream Usage

Design two related Budget workspace tabs using the same visual language.

### Funding Activity tab

Add a small balance strip:

- Reserved — KES 145M
- Committed — KES 310M
- Actual — KES 180M
- Outstanding commitment — KES 130M

Use one chronological table with:

- Activity
- Source record
- Amount
- Current status
- Event date
- Related record
- Action

Illustrative rows:

1. Funding reservation
   - National digital health infrastructure upgrade
   - KES 455M
   - Partially converted
   - Reserved balance: KES 145M
   - Action: View reservation

2. Contract commitment
   - Digital health infrastructure implementation contract
   - KES 310M
   - Active
   - Action: View contract

3. Actual expenditure snapshot
   - Finance system
   - KES 180M
   - Matched
   - Action: View reconciliation

Include filters for Activity type, Status and Date range.

### Downstream Usage tab

Use one traceability table with:

- Requirement
- Demand
- Procurement plan item
- Tender
- Contract
- Reserved balance
- Commitment
- Status
- Action

Show one row tracing the digital infrastructure requirement from Demand through Contract.

All downstream records are read-only links. Do not allow editing from this tab.

---

## Prompt 8 — Budget Revision and Revision Review

Design the Create Budget Revision and Review Revision states.

### Create Budget Revision

Header:

- Title: Create budget revision
- Description: “Record an externally approved change to the active procurement budget.”

Required fields:

- External revision reference
- Approval date
- Effective date
- Reason
- Approval evidence

Use one line-change table with:

- Budget line
- Current approved amount
- Change
- Revised amount
- Reserved
- Committed
- Impact

Do not allow a revised amount below current reservations plus commitments.

Show a concise impact summary:

- Budget before
- Total change
- Budget after
- Affected active demands
- Affected tenders or contracts

Actions:

- Save draft
- Submit for review
- Cancel

### Review Revision

Show all revision fields as read-only.

Add three review groups:

- Financial impact
- Strategy and value-treatment impact
- Downstream procurement impact

Show blockers prominently and link them to the affected line.

Actions:

- Apply revision
- Return for correction
- Reject revision

Require a comment when returning or rejecting.

Do not design financial-system budget approval. This screen only applies a revision already approved by the authoritative financial process.

---

## Prompt 9 — Readiness, Review and Audit

Design the Review and Audit tabs as two states of the Budget workspace.

### Review tab

For a Draft or Returned Budget, show a readiness checklist grouped into:

- Source
- Budget Lines
- Strategy and Value Commitments
- Governance

Each group must show:

- Complete item count
- Issue count
- Specific issue
- Action that opens the correction location

Illustrative issues:

- External approval evidence missing — Add evidence
- Primary strategic target missing on 1 line — Review budget line
- Required value treatment incomplete on 1 line — Review treatments

Actions by state:

- Draft: Run readiness check; Submit for review
- Under review: Return for correction; Activate budget
- Returned: Resolve issues; Resubmit
- Active: No activation controls; show activation record

Require a comment when returning a Budget.

Add this statement before activation:

“Activation confirms that the approved financial baseline has been verified for procurement use in KenTender. It does not constitute statutory budget approval.”

### Audit tab

Use one chronological, read-only table with:

- Date and time
- Event
- Record
- User or integration
- Before and after summary
- Source reference
- Action

Include events for:

- Baseline registered
- Budget submitted
- Budget activated
- Funding reserved
- Reservation partially converted
- Contract commitment recorded
- Expenditure snapshot recorded
- Revision applied

Provide filters for Event type, User or integration, and Date range.

Action:

- Export audit history

Do not permit audit records to be edited or deleted.

---

## Final consistency check for Stitch output

Before accepting each design, verify that:

- The screen remains within the stated prompt.
- The financial-system boundary is visible and respected.
- Approved, Reserved, Committed, Available and Actual are not added incorrectly.
- Actual expenditure is not subtracted twice.
- Active budgets are read-only.
- Strategy targets and Plan Value Commitments are visible but not presented as proven achievements.
- References are generated and shown secondarily, never entered by ordinary users.
- Actions use exact, meaningful labels.
- No unnecessary charts, cards, tabs or workflows were added.
