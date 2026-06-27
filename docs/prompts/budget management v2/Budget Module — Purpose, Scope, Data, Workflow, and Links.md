**Budget Module — Purpose, Scope, Data, Workflow, and Links**

**1\. Purpose**

The **Budget Module** manages the funding envelope that determines what procurement work can proceed.

It answers four core questions:

What funds are available?  
What strategy/programme/objective does the budget support?  
Which demands are funded?  
How much budget remains available, reserved, committed, or consumed?

In the KenTender lifecycle, Budget sits between **Strategy** and **Demand / Procurement Planning**.

Strategy  
→ Budget  
→ Demand Intake & Approval  
→ Procurement Planning  
→ Tender Management  
→ Contract Management  
→ Payments / Performance

The module should not feel like full accounting. It should feel like **procurement funding control**.

**2\. Core Role in the Procurement Lifecycle**

The Budget Module provides the financial guardrails for procurement.

| **Lifecycle Stage** | **Budget Module Role** |
| --- | --- |
| Strategy Management | Receives strategic priorities and funding needs. |
| Budget Planning | Creates budget envelopes and budget lines. |
| Demand Intake | Confirms whether a demand has available funding. |
| Demand Approval | Prevents unfunded demands from progressing unless explicitly allowed. |
| Procurement Planning | Confirms planned procurement work is within approved funding. |
| Package Creation | Verifies package value against funded demand/budget line. |
| Tender Management | Carries forward budget reference for audit and downstream control. |
| Contract Management | Supports commitment tracking after award/contract creation. |
| Payment / Finance | Tracks actual spend or integrates with ERP/accounting. |

**3\. Hierarchical Budget Structure**

The Budget Module should be hierarchical, but simpler than Strategy.

Recommended structure:

Budget  
└── Budget Lines  
└── Allocations / Reservations  
└── Linked Demands  
└── Linked Packages  
└── Linked Tenders / Contracts

**Main levels**

| **Level** | **Meaning** | **Example** |
| --- | --- | --- |
| **Budget** | Top-level budget for entity/fiscal year. | Ministry of Health FY 2026/2027 Budget |
| **Budget Line** | Funded category, programme, project, department, or strategic objective. | Health Infrastructure Renovation |
| **Allocation** | Amount assigned to a department, programme, objective, or demand type. | KES 100,000,000 for hospital renovation |
| **Reservation** | Temporary hold for an approved demand or planned package. | KES 98,000,000 reserved for District Hospital Renovation |
| **Commitment** | Budget locked after award/contract. | Contract signed for KES 96,500,000 |
| **Actual Spend** | Amount paid or consumed. | Paid certificates/invoices |

**4\. Budget Module Responsibilities**

The module should support:

Create budget  
Define budget lines  
Link budget to strategy  
Allocate funds  
Reserve funds for approved demands  
Track available balance  
Track planned procurement value  
Prevent over-allocation  
Support approval workflow  
Maintain budget audit history  
Expose funding status to downstream modules

It should not try to replace the full accounting ledger unless intentionally integrated with ERPNext Accounting.

**5\. Key Data Tracked**

**5.1 Budget Header**

| **Field** | **Meaning** |
| --- | --- |
| Budget name | Human-readable budget title. |
| Fiscal year | Budget period. |
| Procuring entity | Ministry, department, agency, county, etc. |
| Currency | Usually KES. |
| Status | Draft, Submitted, Approved, Active, Closed, Revised, Cancelled. |
| Total budget amount | Approved funding envelope. |
| Strategic plan link | Strategy this budget supports. |
| Budget owner | Responsible finance/budget officer. |
| Approval authority | Person/body approving budget. |
| Effective date | When budget becomes usable. |
| Closing date | End of budget validity. |

**5.2 Budget Line**

| **Field** | **Meaning** |
| --- | --- |
| Budget line title | Programme/project/category name. |
| Parent budget | Budget header. |
| Strategic pillar/programme/objective link | Strategy alignment. |
| Department / cost centre | Operational owner. |
| Fund source | Exchequer, donor, internal, grant, etc. |
| Economic classification | Works, goods, services, consultancy, etc. |
| Approved amount | Amount authorized. |
| Allocated amount | Amount assigned to demands/packages. |
| Reserved amount | Amount held for approved demand/planned package. |
| Committed amount | Amount locked by award/contract. |
| Actual amount | Amount spent/paid. |
| Available amount | Balance available for new planning. |
| Status | Draft, Active, Exhausted, Closed, Revised. |

**5.3 Allocation / Reservation**

| **Field** | **Meaning** |
| --- | --- |
| Source budget line | Which budget line funds the work. |
| Linked demand | Demand consuming/reserving funds. |
| Linked package | Package consuming/reserving funds. |
| Reserved amount | Amount held. |
| Reservation status | Reserved, Released, Converted to Commitment, Cancelled. |
| Reservation date | When funds were reserved. |
| Expiry date | Optional reservation expiry. |
| Approval reference | Who authorized reservation. |
| Evidence reference | Audit/evidence record. |

**5.4 Budget Movement / Adjustment**

| **Field** | **Meaning** |
| --- | --- |
| Movement type | Allocation, reservation, release, commitment, revision, transfer. |
| Amount | Value moved. |
| From budget line | Source line if transfer. |
| To budget line | Destination line if transfer. |
| Reason | Justification. |
| Approved by | Authority. |
| Timestamp | Audit. |
| Linked object | Demand/package/contract/payment. |

**6\. Budget Status Model**

Recommended simple status model:

Draft  
→ Submitted  
→ Approved  
→ Active  
→ Closed

Additional exception states:

Returned  
Revised  
Cancelled  
Exhausted

**Meaning**

| **Status** | **Meaning** |
| --- | --- |
| Draft | Budget is being prepared. |
| Submitted | Awaiting approval. |
| Returned | Sent back for correction. |
| Approved | Approved but not yet active. |
| Active | Can fund demands and procurement planning. |
| Revised | Approved budget has been amended. |
| Exhausted | No available balance remains. |
| Closed | Budget period closed. |
| Cancelled | Budget withdrawn. |

**7\. Approval Workflow**

**7.1 Standard Budget Approval Flow**

Budget Officer creates budget  
→ Budget Owner reviews  
→ Finance Reviewer validates amounts/classifications  
→ Strategy/Planning Reviewer confirms alignment  
→ Approval Authority approves  
→ Budget becomes Approved / Active

**7.2 Detailed Flow**

| **Step** | **Actor** | **Action** | **Result** |
| --- | --- | --- | --- |
| 1   | Budget Officer | Create draft budget and budget lines. | Draft budget exists. |
| 2   | Budget Officer | Link budget lines to strategy/programmes/objectives. | Strategic alignment established. |
| 3   | Budget Officer | Submit budget. | Status becomes Submitted. |
| 4   | Budget Owner | Review completeness and ownership. | Approved forward or returned. |
| 5   | Finance Reviewer | Validate amounts, classifications, fund sources. | Finance validation recorded. |
| 6   | Strategy / Planning Reviewer | Confirm budget supports approved strategy. | Alignment validation recorded. |
| 7   | Approval Authority | Approve or return. | Budget becomes Approved. |
| 8   | Finance / Budget Authority | Activate budget. | Budget can fund demands. |
| 9   | System | Lock approved baseline. | Audit baseline created. |

**7.3 Revision Workflow**

Budget revisions should be controlled.

Active Budget  
→ Revision Requested  
→ Reviewed  
→ Approved  
→ New active version created

Rules:

Approved historical budget values must remain auditable.  
Revisions should create version history.  
Downstream reservations/commitments must not silently break.  
If a revision reduces available funds below reserved/committed amounts, the system must block or escalate.

**8\. Links to Other Sub-Modules**

**8.1 Strategy Management**

Budget lines should link to:

Strategic Plan  
Pillar / Programme  
Objective  
Target / Outcome  
Initiative / Activity

Purpose:

Show what strategic priority the budget funds.  
Prevent procurement work that has no strategic basis, where required.  
Enable strategy success tracking against funded execution.

**8.2 Demand Intake & Approval**

Demands should link to a budget line or funding source.

Budget provides:

Funding available?  
Budget line valid?  
Amount within available balance?  
Reservation required?

Demand approval should show:

Budget linked  
Budget insufficient  
Budget reserved  
Funding pending

**8.3 Procurement Planning**

Procurement Planning uses budget data to confirm:

Approved demand is funded.  
Package value does not exceed reserved/available budget.  
Package can proceed to readiness/review/release.

Planning should not re-check finance manually if budget status is already valid, but it must display funding status clearly.

**8.4 STD / Tender Document Readiness**

Budget may influence:

procurement method thresholds  
approval thresholds  
document template selection  
donor/funding compliance clauses

**8.5 Tender Management**

When a package becomes a tender, the tender should inherit:

budget line reference  
funding source  
estimated value  
reserved/approved amount  
financial approval evidence

Tender Management should not modify budget directly. It should consume the approved package funding context.

**8.6 Evaluation & Award**

Award should compare:

winning bid amount  
approved budget  
reserved amount  
available amount

If award exceeds available/reserved budget:

block award  
require budget top-up  
or require formal approval override

**8.7 Contract Management**

Contract creation should convert relevant budget reservation into commitment.

Reservation  
→ Commitment  
→ Actual spend / payment

Contract Management should track:

contract value  
committed amount  
variation impact  
payment impact  
remaining commitment

**8.8 Supplier Management**

Usually indirect. Budget does not manage suppliers, but budget controls supplier-facing procurement by determining which funded procurements can proceed.

**8.9 Evidence & Audit**

Budget must generate audit events for:

budget creation  
submission  
approval  
activation  
revision  
allocation  
reservation  
release  
commitment  
cancellation  
closure

**9\. Funding Control Model**

The module should distinguish these amounts:

| **Amount Type** | **Meaning** |
| --- | --- |
| Approved Amount | Total approved funding. |
| Allocated Amount | Funding assigned to lines/programmes/departments. |
| Available Amount | Amount still free for new demands. |
| Reserved Amount | Amount held for approved demands or planned packages. |
| Committed Amount | Amount legally committed after award/contract. |
| Actual Spend | Amount paid or consumed. |
| Remaining Balance | Amount not reserved, committed, or spent. |

Basic formula:

Available = Approved Amount - Reserved Amount - Committed Amount - Actual Spend

If you distinguish allocation separately:

Line Available = Line Approved Amount - Line Reserved - Line Committed - Line Actual

**10\. Key UI Surfaces**

**10.1 Budget Home / Workbench**

Purpose:

Show active budgets, pending approvals, available funding, and exceptions.

Suggested cards:

Active Budgets  
Pending Approval  
Total Approved Budget  
Available Balance  
Reserved Amount  
Committed Amount  
Funding Exceptions

**10.2 Budget Builder**

Purpose:

Create and structure budget lines.

Recommended layout:

Left: Budget line hierarchy  
Right: selected line details  
Bottom/side: linked strategy and downstream usage

**10.3 Budget Line Detail**

Shows:

approved amount  
available amount  
reserved amount  
committed amount  
actual spend  
linked strategy  
linked demands  
linked packages  
linked contracts  
movements  
evidence

**10.4 Funding Check / Reservation Modal**

Used from Demand or Planning.

Shows:

demand/package value  
selected budget line  
available balance  
amount to reserve  
result after reservation  
confirm action

**10.5 Budget Revision Screen**

Shows:

current approved amount  
proposed revised amount  
reason  
impact on reservations/commitments  
approval workflow

**11\. User Roles**

| **Role** | **Responsibilities** |
| --- | --- |
| Budget Officer | Creates budget and budget lines. |
| Budget Owner | Owns budget content and submits/reviews. |
| Finance Reviewer | Validates amounts, classifications, funding source. |
| Strategy / Planning Reviewer | Confirms strategy alignment. |
| Approval Authority | Approves budget or revision. |
| Procurement Planner | Uses approved budget to plan funded demands. |
| Demand Approver | Checks funding before approving demand. |
| Auditor | Reviews budget evidence and movements. |
| System Administrator | Configures structure, not business approval. |

**12\. Core Actions**

Create Budget  
Add Budget Line  
Link to Strategy  
Submit Budget  
Review Budget  
Approve Budget  
Activate Budget  
Return Budget  
Revise Budget  
Close Budget  
Reserve Funds  
Release Reservation  
Convert Reservation to Commitment  
Record Actual Spend / Sync from Finance  
View Evidence

**13\. UX Rules**

The Budget Module should be simple for normal users.

Use business labels:

Budget linked  
Funding available  
Funding reserved  
Insufficient funds  
Budget approved  
Budget active  
Budget exhausted

Avoid exposing technical accounting unless needed:

GL Entry  
Journal Entry  
DocType  
ledger mutation  
technical reference  
raw allocation object

For procurement users, the most important budget message is:

Can this demand/package proceed financially?

Not:

Which internal budget object is being mutated?

**14\. Recommended Budget Module Summary for the Design App**

The Budget Module is the funding-control layer for procurement. It creates approved fiscal-year budget envelopes, breaks them into budget lines aligned to strategy, and tracks how funds move from available budget to reserved demand/package funding, committed contract value, and actual spend.

It links upstream to Strategy Management and downstream to Demand Intake, Procurement Planning, Tender Management, Award, and Contract Management.

The UI should make funding status obvious: active budget, available balance, reserved amount, committed amount, and exceptions. Budget setup and approval should be handled by finance/budget users, while procurement users should mostly see simple funding outcomes such as **Budget linked**, **Funding available**, **Reserved**, or **Insufficient funds**.