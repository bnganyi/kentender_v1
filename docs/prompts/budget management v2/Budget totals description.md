Budget totals should be calculated **from budget lines**, not typed manually on the budget header.

**1\. Core rule**

Budget Header Totals = Sum of Budget Line Totals

So the budget header is a roll-up:

| **Budget Header Total** | **Calculation** |
| --- | --- |
| **Approved Budget** | Sum of approved amounts on all active/approved budget lines |
| **Reserved Amount** | Sum of active reservations against all budget lines |
| **Committed Amount** | Sum of active commitments against all budget lines |
| **Actual Spend** | Sum of actual payments/spend recorded or synced against all budget lines |
| **Available Balance** | Approved Budget − Reserved − Committed − Actual Spend |

For each budget line:

Line Available =  
Line Approved Amount  
\- Active Reservations  
\- Active Commitments  
\- Actual Spend

Then:

Budget Available =  
Sum(Line Available)

**2\. Meaning of each amount**

| **Amount** | **Meaning** |
| --- | --- |
| **Approved** | Funding authorized for that budget line. |
| **Available** | Funding still free for new demands/packages. |
| **Reserved** | Funding temporarily held for approved demands or procurement packages. |
| **Committed** | Funding legally/contractually locked after award or contract creation. |
| **Actual Spend** | Money already paid or consumed. |

**3\. Simple example**

Budget has two lines:

| **Budget Line** | **Approved** | **Reserved** | **Committed** | **Actual** | **Available** |
| --- | --- | --- | --- | --- | --- |
| Hospital Renovation | 100,000,000 | 98,000,000 | 0   | 0   | 2,000,000 |
| Medical Equipment | 80,000,000 | 0   | 70,000,000 | 10,000,000 | 0   |
| **Budget Total** | **180,000,000** | **98,000,000** | **70,000,000** | **10,000,000** | **2,000,000** |

Formula:

180,000,000 - 98,000,000 - 70,000,000 - 10,000,000 = 2,000,000

**4\. What happens when a new budget line is added?**

It depends on the budget status.

**If budget is Draft**

Adding a new line simply increases the draft budget total.

Draft Approved Budget = sum of draft line amounts

Example:

Existing draft budget total: KES 180,000,000  
New line added: KES 20,000,000  
New draft total: KES 200,000,000

No reservations or commitments should exist yet unless the system allows early planning, which I would avoid.

**If budget is Submitted / Under Review**

Adding or editing lines should either be blocked or allowed only by returning the budget to Draft.

Best rule:

Submitted budget cannot be edited directly.  
Reviewer must return it for correction.

**If budget is Approved / Active**

Adding a new line is a **budget revision**, not a casual edit.

The system should not silently increase the approved budget.

Correct flow:

Request Revision  
→ Add / amend line  
→ Review  
→ Approve revision  
→ New approved baseline locked

**5\. Impact of adding a line to an active budget**

Adding a new approved line increases the budget envelope only after approval.

Example before revision:

| **Total** | **Amount** |
| --- | --- |
| Approved | 180,000,000 |
| Reserved | 98,000,000 |
| Committed | 70,000,000 |
| Actual | 10,000,000 |
| Available | 2,000,000 |

Add new approved line:

New line: Community Clinic Repairs — KES 50,000,000

After revision approval:

| **Total** | **Amount** |
| --- | --- |
| Approved | 230,000,000 |
| Reserved | 98,000,000 |
| Committed | 70,000,000 |
| Actual | 10,000,000 |
| Available | 52,000,000 |

The new line creates additional available budget **only on that line** unless transfers/pooling are allowed.

**6\. Important controls**

**Do not allow negative available balance**

Line Available must not go below 0

unless an explicit authorized override exists.

**Do not double-count actual spend**

If actual spend reduces commitments in your accounting model, do not subtract both committed and actual in a way that double-counts. Pick one model.

For KenTender, I recommend this clean procurement-control model:

Available = Approved - Reserved - Committed

And show actual spend separately under contract/payment performance.

Then for contract execution:

Committed Balance = Committed - Actual Spend

This avoids confusing the procurement budget screen.

**7\. Recommended KenTender model**

For procurement planning and control, use:

Approved = sum approved budget lines  
Reserved = sum active reservations for demands/packages  
Committed = sum active contract commitments  
Available = Approved - Reserved - Committed  
Actual Spend = shown separately, not subtracted from Available if already part of Commitment

So the budget header cards should be:

Approved Budget  
Available Balance  
Reserved for Procurement  
Committed by Contracts  
Actual Spend

Actual Spend is important, but it should not distort available balance if the commitment already captured the obligation.

Top of Form

Bottom of Form