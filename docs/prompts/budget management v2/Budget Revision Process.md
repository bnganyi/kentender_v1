**Budget Revision Process**

**1\. Core rule**

An **Active Budget must not be edited directly**.

A revision should create a controlled amendment record:

Active Budget  
→ Revision Draft  
→ Submitted for Review  
→ Approved  
→ New Active Budget Baseline

The original approved budget remains locked for audit.

**2\. When a revision is needed**

A revision is required when someone wants to:

| **Change** | **Revision Required?** |
| --- | --- |
| Add a new budget line to an active budget | Yes |
| Increase or decrease an approved budget line | Yes |
| Move funds between budget lines | Yes |
| Change funding source | Yes |
| Change strategy/programme/objective link | Usually yes |
| Correct typo/description only | Minor admin correction, with audit |
| Close exhausted line | Controlled action, may not need full revision |
| Release unused reservation | No, this is a budget movement, not revision |

**3\. Recommended revision types**

Use simple types:

| **Revision Type** | **Meaning** |
| --- | --- |
| **Supplementary Allocation** | Add new funds or increase budget. |
| **Reduction** | Reduce approved funding. |
| **Transfer / Reallocation** | Move funds from one budget line to another. |
| **New Line Addition** | Add a new budget line under an active budget. |
| **Line Amendment** | Change line metadata, strategy link, classification, or fund source. |
| **Correction** | Fix non-financial data without changing approved amounts. |

**4\. Revision workflow**

| **Step** | **Actor** | **Action** | **Result** |
| --- | --- | --- | --- |
| 1   | Budget Officer | Start revision from active budget | Revision draft created |
| 2   | Budget Officer | Select revision type and affected lines | Proposed changes captured |
| 3   | System | Calculate financial impact | Before/after totals shown |
| 4   | System | Check reservations, commitments, and available balance | Blockers detected |
| 5   | Budget Officer | Add justification and supporting documents | Revision ready for review |
| 6   | Budget Reviewer | Review financial and strategy impact | Approve forward or return |
| 7   | Budget Authority | Approve or reject revision | Revision approved/rejected |
| 8   | System | Apply approved revision | New budget baseline created |
| 9   | System | Lock old baseline and record evidence | Audit trail preserved |

**5\. Revision states**

Draft  
→ Submitted  
→ Returned  
→ Approved  
→ Applied

Exception states:

Rejected  
Cancelled  
Superseded

Meaning:

| **State** | **Meaning** |
| --- | --- |
| **Draft** | Revision is being prepared. |
| **Submitted** | Waiting for review/approval. |
| **Returned** | Sent back for correction. |
| **Approved** | Approved but not yet applied, if separated. |
| **Applied** | Budget baseline has been updated. |
| **Rejected** | Not accepted. |
| **Cancelled** | Withdrawn before approval. |
| **Superseded** | Replaced by a newer revision. |

For usability, you can combine **Approved** and **Applied** unless you need a posting step.

**6\. What the revision screen must show**

The revision UI should always show a **before vs after** view.

Budget Revision: Ministry of Health FY 2026/2027  
<br/>Revision Type: Transfer / Reallocation  
Reason: Increase allocation for District Hospital Renovation Works  
<br/>Before Revision  
Approved Budget: KES 250,000,000  
Reserved: KES 98,000,000  
Committed: KES 80,000,000  
Available: KES 72,000,000  
<br/>After Revision  
Approved Budget: KES 250,000,000  
Reserved: KES 98,000,000  
Committed: KES 80,000,000  
Available: KES 72,000,000

For affected lines:

| **Budget Line** | **Current Approved** | **Change** | **Revised Approved** | **Available After** |
| --- | --- | --- | --- | --- |
| Hospital Renovation | 100,000,000 | +20,000,000 | 120,000,000 | 22,000,000 |
| Medical Equipment | 80,000,000 | \-20,000,000 | 60,000,000 | 0   |

**7\. Critical validation rules**

The system must block unsafe revisions.

**7.1 Do not reduce below reserved/committed amount**

A line cannot be reduced below money already reserved or committed.

Minimum allowed line amount =  
Reserved + Committed

Example:

Current line approved: KES 100,000,000  
Reserved: KES 98,000,000  
Committed: KES 0  
<br/>Minimum allowed revised amount: KES 98,000,000

So reducing that line to KES 90,000,000 must be blocked.

**7.2 Do not silently break linked procurement work**

If a revised line funds existing demands/packages/tenders/contracts, the system must show impact:

This budget line funds:  
\- 1 approved demand  
\- 1 procurement package  
\- 0 tenders  
\- 0 contracts

If the revision affects them, show blockers or warnings.

**7.3 Transfers must balance**

For transfer/reallocation:

Total amount removed = Total amount added

unless the revision type is supplementary allocation or reduction.

**7.4 Strategy link changes must be reviewed**

Changing strategy alignment after budget activation should require justification.

**8\. What happens after approval**

When a revision is approved:

1.  The existing active budget baseline is locked as historical.
2.  The revised line values become the new active baseline.
3.  A revision number is created.

Example:

MOH-BUD-2026 v1 — Original approved baseline  
MOH-BUD-2026 v2 — Revision 1 applied

1.  Budget totals are recalculated.
2.  Existing reservations and commitments remain linked.
3.  Evidence is recorded.

**9\. Impact on downstream modules**

| **Module** | **Revision Impact** |
| --- | --- |
| Strategy | May update funding available for strategic initiatives. |
| Demand Intake | A demand may become fundable or unfundable. |
| Procurement Planning | Packages may become blocked if funding is reduced. |
| Tender Management | Tender may inherit revised funding context before award. |
| Evaluation & Award | Award may be blocked if revised budget is insufficient. |
| Contract Management | Existing commitments must not be invalidated casually. |
| Evidence & Audit | Revision evidence must be preserved. |

**10\. Recommended UI actions**

For an active budget, show:

\[Request Revision\]  
\[View Revision History\]  
\[View Evidence\]

Inside revision:

\[Add Line\]  
\[Increase Line\]  
\[Reduce Line\]  
\[Transfer Funds\]  
\[Change Strategy Link\]  
\[Submit Revision\]  
\[Cancel Revision\]

After submission:

\[Approve Revision\]  
\[Return\]  
\[Reject\]

**11\. Evidence to record**

Each revision should record:

revision number  
revision type  
affected budget lines  
before values  
after values  
reason  
supporting documents  
submitter  
reviewer  
approver  
approval date  
application date  
linked downstream impact  
audit event reference

**12\. Simple product rule**

Use this rule in the UI:

Active budgets cannot be edited directly.  
To change an active budget, request a revision.  
A revision shows what changes, why it changes, who approved it, and what procurement work is affected.

That keeps the system legally safe without making everyday budget use painful.