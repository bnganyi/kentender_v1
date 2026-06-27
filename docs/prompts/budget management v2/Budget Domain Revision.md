How are these terms used in our context and are they applicable? Allocation, Reservation, Commitment

Yes, all three terms are applicable, but they should be used carefully. They belong mostly in the **Budget / Finance control layer**, not as everyday UX language for normal procurement users.

**1\. Allocation**

**Meaning in our context:**  
An **Allocation** is money assigned from an approved budget to a programme, department, objective, activity, budget line, or procurement category.

It answers:

How much funding has been set aside for this purpose?

Example:

Ministry of Health FY 2026/2027 Budget  
→ Health Infrastructure Programme  
→ Allocation: KES 100,000,000

Use it when building or approving the budget.

**Applicable?** Yes.

**Best UI wording:**

Allocated Budget  
Budget Line Amount  
Funding Envelope

**2\. Reservation**

**Meaning in our context:**  
A **Reservation** is a temporary hold on available budget for a specific approved demand or procurement package before award/contract.

It answers:

Has funding been held so this demand/package can proceed?

Example:

District Hospital Renovation Works demand  
Estimated value: KES 98,000,000  
<br/>Budget line available: KES 100,000,000  
Reservation created: KES 98,000,000  
Remaining available: KES 2,000,000

Reservation happens around:

Demand approval  
→ Planning  
→ Package creation

**Applicable?** Yes, very applicable.

This is the key term that prevents over-planning against the same budget.

**Best UI wording for normal users:**

Funding reserved  
Budget reserved

Avoid making users manage “reservation objects” directly.

**3\. Commitment**

**Meaning in our context:**  
A **Commitment** is budget locked against a legal/contractual obligation, usually after award or contract creation.

It answers:

How much budget is now legally committed?

Example:

Package reserved amount: KES 98,000,000  
Winning contract value: KES 96,500,000  
<br/>Reservation converted to commitment: KES 96,500,000  
Unneeded reservation released: KES 1,500,000

Commitment happens after:

Award  
→ Contract creation

**Applicable?** Yes, but later in the lifecycle.

It belongs more to **Award / Contract Management / Finance** than early Planning.

**Best UI wording:**

Committed Amount  
Contract Commitment  
Budget committed

**Correct lifecycle**

Allocation  
→ Reservation  
→ Commitment  
→ Actual Spend

Meaning:

Allocation = budget assigned for a purpose  
Reservation = budget held for a planned procurement  
Commitment = budget locked by award/contract  
Actual Spend = budget consumed by payment

**In the KenTender workflow**

| **Stage** | **Budget term** | **Meaning** |
| --- | --- | --- |
| Budget creation | Allocation | Funds assigned to budget lines/programmes |
| Demand approval | Reservation | Funds held for an approved demand |
| Procurement planning/package | Reservation | Reserved funding travels with the package |
| Tendering | Reservation | Tender inherits funding context, but does not commit yet |
| Award | Commitment begins | Winning amount is checked against reserved funds |
| Contract creation | Commitment | Budget becomes legally committed |
| Payment | Actual spend | Paid amount reduces outstanding commitment |

**Important product rule**

Do not expose all three terms equally to every user.

For normal procurement users, show simple labels:

Budget linked  
Funding available  
Funding reserved  
Insufficient funds  
Committed by contract

For budget/finance/audit users, show the precise financial terms:

Allocated  
Reserved  
Committed  
Actual Spend  
Available Balance

**Recommended formulas**

Available = Allocated - Reserved - Committed - Actual Spend

More safely:

Line Available =  
Approved / Allocated Amount  
\- Active Reservations  
\- Commitments  
\- Actual Spend not already reflected in commitments

Be careful not to double-count actual spend if your accounting model already reduces commitments when payments are made.

**Final recommendation**

Use all three terms in the backend and audit model.

In ordinary UX:

Allocation = shown in Budget setup  
Reservation = shown as “Funding reserved”  
Commitment = shown after Award/Contract

That keeps the system financially rigorous without making the procurement UI feel like an accounting ledger.