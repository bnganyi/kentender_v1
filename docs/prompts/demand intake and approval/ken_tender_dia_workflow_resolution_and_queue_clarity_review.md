# KenTender DIA Workflow Resolution and Queue Clarity Review

This document reviews the current Demand Intake and Approval implementation where approved demands remain `Not Yet Planned`, planning readiness is unresolved, and the user is given checks that they cannot clearly act on.

The main issue is not only visual design. The workflow model is not communicating ownership, sequence, and resolution actions clearly enough.

---

# 1. Core Problem

The current screen creates three kinds of confusion:

1. **Review tab says **``** for a demand that is already approved.**

   - This is wrong for the current state.
   - Submission readiness belongs only to Draft / pre-submission demand.
   - Once a demand is approved, the Review tab should show approval outcome, not submission readiness.

2. **Queues mix workflow state and planning state.**

   - `Approved 2` and `Not Yet Planned 2` overlap.
   - A demand can be both `Approved` and `Not Yet Planned`.
   - Therefore these should not appear as peer lifecycle queues without explanation.

3. **Planning tab shows a blocker but does not explain ownership or resolution.**

   - It says `Budget reserved` failed.
   - It does not say who performs reservation.
   - It does not provide a clear action to reserve budget or explain where reservation happens.
   - It says `Run planning check`, but this looks like text, not a clear action.

The result is a workflow the user cannot confidently advance.

---

# 2. Align the State Model to the PRD: Approval Includes Finance Reservation

After reviewing the Scope Summary and PRD, the state model should be tightened. The PRD defines a canonical lifecycle where Finance approval is the budget commitment gate, and a demand reaches `Approved` only after Finance approval and successful budget reservation.

Therefore, the UI should not treat `Approved` as merely a business approval that still needs budget reservation later. That creates unnecessary complication and conflicts with the PRD.

## Canonical Workflow State

Use one authoritative workflow state:

```text
Draft
Pending HoD Approval
Pending Finance Approval
Approved
Planning Ready
Rejected
Cancelled
```

Meaning:

```text
Draft = being prepared by requester
Pending HoD Approval = awaiting departmental business approval
Pending Finance Approval = awaiting finance validation and reservation
Approved = HoD approved + Finance approved + budget reserved
Planning Ready = Procurement has confirmed the approved demand is ready for planning intake
Rejected = refused with reason
Cancelled = withdrawn/terminated with reason
```

## Important Rule

If budget reservation has not succeeded, the demand should not be `Approved`.

It should remain:

```text
Pending Finance Approval
```

or be returned/rejected according to finance decision policy.

## Planning Status Is Secondary

Planning status should not compete with workflow state. Use it as a secondary planning-consumption attribute only:

```text
Not Planned
Partially Planned
Fully Planned
```

Do not use `Not Yet Planned` as a peer queue beside `Approved` if that makes the user think the statuses are mutually exclusive.

A valid approved record may display:

```text
Workflow state: Approved
Planning consumption: Not Planned
```

But the top queue should not make these look like two independent primary lifecycle stages.

---

# 3. Queue Bar Recommendation: Concise, Single-Line, and PRD-Aligned

The queue bar should be concise and usable. Do not use a two-line queue design such as:

```text
All 14 | My Work
Approval: ...
Planning: ...
Flags: ...
```

That consumes too much space and breaks the compact pattern established in Strategy, Budget, and Tender Management.

## Recommended Single-Line Queue Bar

Use one compact line with light group labels:

```text
[All 14] [My Work]  Intake [Draft 11]  Approval [HoD 0] [Finance 1] [Approved 2]  Handoff [Planning Ready 0]  Exceptions [Rejected 0] [Cancelled 0] [Emergency 0]
```

This keeps lifecycle meaning without using multiple queue rows.

## Label Rules

Use short labels:

```text
HoD = Pending HoD Approval
Finance = Pending Finance Approval
Approved = fully approved and budget reserved
Planning Ready = released to Procurement Planning queue
Emergency = flag filter, not workflow state
```

## Remove or Reframe `Not Yet Planned`

Avoid showing `Not Yet Planned` as a top-level peer queue beside `Approved`.

Better options:

### Option A — Remove from top queue

Show `Not Planned` only as a badge on approved cards:

```text
DEM-MOH-2026-001
Approved · Not planned
KES 98,000,000
```

### Option B — Rename under handoff, only if truly needed

If the product needs a quick filter for approved demands not yet handed off, use:

```text
Handoff [Approved Awaiting Handoff 2] [Planning Ready 0]
```

This is clearer than `Not Yet Planned` because it tells the user what has not happened yet.

## Recommended Final Queue Bar

```text
[All 14] [My Work]  Intake [Draft 11]  Approval [HoD 0] [Finance 1] [Approved 2]  Handoff [Planning Ready 0]  Exceptions [Rejected 0] [Cancelled 0] [Emergency 0]
```

This is compact, PRD-aligned, and does not imply contradictory state relationships.

---

# 4. Review Tab Must Be State-Aware

The Review tab should not always show `Submission readiness`.

## If Demand Is Draft

Show:

```text
Submission readiness
Not ready / Ready to submit

[Submit for Approval]
```

## If Demand Is Submitted / Under Review

Show:

```text
Review readiness
Ready for reviewer decision

[Approve] [Return for Correction] [Reject]
```

## If Demand Is Approved

Show:

```text
Approval outcome
Approved by HoD
Approved by Finance
Approved on [date]

This demand is authorized. Complete planning readiness on the Planning tab before Procurement Planning can consume it.
```

Do not show `Ready to submit` after approval. That message is stale and state-inappropriate.

---

# 5. Planning Tab Must Not Perform Finance Reservation

The Planning tab should not be where budget reservation happens. The PRD is clear: Finance approval is the budget commitment gate. Finance approval must validate budget and create the reservation.

Therefore, if a demand is already `Approved`, the Planning tab should normally show:

```text
Budget reservation: Complete
Reservation reference: [reference]
```

If reservation is missing while the demand is marked `Approved`, that is not normal planning work. It is a data integrity or finance workflow problem.

## Correct Meaning of Planning Tab

The Planning tab should confirm that an already-approved and reserved demand is ready for Procurement Planning intake.

It should answer:

```text
Is this approved demand ready to be released into Procurement Planning?
```

It should not ask the Procurement Officer to perform Finance work.

## Recommended Planning Readiness Panel

```text
Planning readiness
This demand is approved and budget-reserved. Confirm it is ready for Procurement Planning intake.

Requirement                  Status       Owner                  Action
Approval complete             Complete     HoD + Finance           —
Budget reservation            Complete     Finance                 —
Strategy linkage              Complete     System / Finance        —
Budget line                   Complete     Finance                 —
Planning handoff              Ready        System                  —

[Confirm Planning Ready]
```

## If Reservation Is Missing on an Approved Demand

Show a blocking integrity message:

```text
Planning readiness blocked
This demand is marked Approved, but no budget reservation exists. Approved demands must have a reservation created by Finance approval.

Owner: Finance Approver / Administrator
Required action: return the demand to Pending Finance Approval or repair the reservation record.

[Send Back to Finance] [View Finance Approval Details]
```

Do not show `Reserve Budget` as a normal Procurement Planning action unless the governance model explicitly allows Procurement to reserve funds. The PRD does not prefer that.

---

# 6. Define Ownership: Finance Reserves, Procurement Confirms Planning Ready

The ownership should be concrete and PRD-aligned.

## Finance Approver

Finance owns:

```text
budget validation
budget availability check
reservation creation
reservation reference
available budget snapshot
finance approval timestamp
```

Finance action:

```text
Approve & Reserve Budget
```

Result:

```text
Workflow state = Approved
Reservation status = Reserved
Planning consumption = Not Planned
```

## Procurement Officer

Procurement owns:

```text
confirming that the approved demand is eligible for Procurement Planning intake
marking the demand Planning Ready
consuming it into Procurement Planning later
```

Procurement action:

```text
Confirm Planning Ready
```

Result:

```text
Workflow state = Planning Ready
Planning queue = available to Procurement Planning
```

## Recommended Flow

```text
Draft
→ Submit
→ Pending HoD Approval
→ HoD Approves
→ Pending Finance Approval
→ Finance Approves & Reserves Budget
→ Approved
→ Procurement Confirms Planning Ready
→ Planning Ready
```

This removes unnecessary ambiguity from the Budget module and keeps the approval cycle central.

---

# 7. Planning Check Should Be Automatic or a Clear Procurement Action

`Run Planning Check` should not feel like an unresolved instruction.

The best implementation is automatic: when the user opens the Planning tab, the system evaluates planning readiness and shows the result.

If a manual action is still needed, it must be a real button:

```text
[Run Planning Readiness Check]
```

## Checks Should Be PRD-Aligned

Planning readiness check should verify:

```text
workflow state is Approved
reservation status is Reserved
reservation reference exists
strategy linkage is complete
budget line exists
no active blockers
planning handoff record can be generated
```

It should not try to create reservation. Reservation belongs to Finance approval.

## Pass Outcome

```text
Planning check passed
This demand is approved, budget-reserved, and ready for planning intake.

[Confirm Planning Ready]
```

## Fail Outcome

```text
Planning check failed
1 blocker remains:
- Reservation reference missing on approved demand

Owner: Finance Approver / Administrator
Action: Send back to Finance or repair reservation record.
```

---

# 8. Use Blocker-Oriented Design Without Adding New Budget Complexity

If the user cannot advance, show blockers as first-class objects.

But do not create a new reservation workflow in the Planning tab.

Recommended blocker table:

```text
Planning blockers
Requirement              Status     Owner                  Action
Reservation reference     Missing    Finance / Admin        Send back to Finance
Strategy linkage          Complete   System                 —
Planning handoff          Complete   System                 —
```

For normal approved records, the blocker table should usually be empty because Finance approval should already have reserved budget.

Do not bury blockers in a checklist with no owner or action.

---

# 9. Rename Actions for Clarity

Current:

```text
Mark planning ready
```

Better:

```text
Confirm Planning Ready
```

This is clearer because Procurement is confirming that an already-approved, already-reserved demand can now enter the Procurement Planning queue.

Current:

```text
Run planning check
```

Better, if manual:

```text
Run Planning Readiness Check
```

But preferred behavior is automatic readiness evaluation when the Planning tab opens.

Do not use this as a normal Planning tab action:

```text
Reserve Budget
```

Budget reservation belongs to Finance approval, not Procurement Planning.

---

# 10. Recommended Planning Tab Layout

```text
Planning

Current state
Workflow state: Approved
Planning consumption: Not Planned
Next step: confirm this approved and budget-reserved demand for Procurement Planning intake.

Budget and strategy context
Budget line: District Health Facility Infrastructure Rehabilitation
Budget: BUDGET-MOH-2026
Funding source: Government of Kenya Development Budget
Reservation status: Reserved
Reservation reference: RSV-2026-0001
Strategy linkage: Complete

Planning readiness
Requirement                  Status       Owner                 Action
Approval complete             Complete     HoD + Finance         —
Budget reservation            Complete     Finance               —
Strategy linkage              Complete     System                —
Budget line                   Complete     Finance               —
Planning handoff              Ready        System                —

[Confirm Planning Ready]
```

If the approved record is missing reservation:

```text
Planning readiness blocked
This demand is Approved but has no reservation reference. Finance approval should have created one.

Requirement                  Status       Owner                 Action
Budget reservation            Missing      Finance / Admin       [Send Back to Finance]

[Confirm Planning Ready] disabled
```

---

# 11. Recommended Review Tab Layout for Approved Demand

```text
Review

Approval outcome
Status: Approved
HoD approval: Approved by [user] on [date]
Finance approval: Approved by [user] on [date]

Submission readiness
Completed before approval.
[View submission checks]

Next step
Go to Planning tab to resolve planning readiness.
```

This prevents the absurd state where an approved demand says it is `Ready to submit`.

---

# 12. Recommended Header Messaging

Current message:

```text
Next step: review planning readiness on the Planning tab and confirm when ready.
```

This is okay, but should be more actionable if blocked.

Better:

```text
Next step: resolve 1 planning blocker before confirming Planning Ready.
```

or:

```text
Next step: budget reservation required before this demand can be marked Planning Ready.
```

This should be computed from the readiness checks.

---

# 13. Immediate Changes to Make

1. **Use a single-line grouped queue bar.**

   - Do not use multi-line queue groups.
   - Use: `All | My Work | Intake | Approval | Handoff | Exceptions` in one compact row.

2. **Remove **``** as a peer top-level queue beside **``**.**

   - Show planning consumption as a badge or use `Approved Awaiting Handoff` only if absolutely needed.

3. **Make Review tab state-aware.**

   - Draft: submission readiness.
   - Pending HoD / Finance: reviewer decision.
   - Approved: approval outcome.

4. **Remove **``** from approved demands.**

   - Replace with approval outcome and planning handoff guidance.

5. **Treat Finance approval as the reservation gate.**

   - Finance action should be `Approve & Reserve Budget`.
   - Approved demand should have reservation status `Reserved` and a reservation reference.

6. **Remove normal **``** action from the Planning tab.**

   - Planning should not create budget reservations unless the PRD is changed.

7. **Rename **``** to **``**.**

   - Procurement Officer performs this after approval/reservation.

8. **Make planning check automatic where possible.**

   - If manual, use a real `[Run Planning Readiness Check]` button.

9. **If an Approved demand has no reservation, show it as an integrity blocker.**

   - Owner: Finance / Admin.
   - Action: send back to Finance or repair reservation record.

10. **Keep Budget module simple.**

- Budget module provides budget lines, available balances, reservations, and reservation audit.
- DIA Finance approval consumes that capability.
- Procurement Planning should not become a budget-reservation screen.

---

# 14. Final Recommendation

The DIA implementation should be tightened around the PRD’s approval cycle.

The rule should be:

```text
HoD approval authorizes the business need.
Finance approval validates budget and creates reservation.
Approved means fully approved and budget-reserved.
Procurement confirms Planning Ready.
Planning consumes Planning Ready demand.
```

Therefore:

```text
Approved + Reservation Missing = workflow/data integrity problem
Approved + Not Planned = normal demand awaiting Procurement handoff
Planning Ready = approved demand released to Procurement Planning queue
```

The UI must show:

```text
which stage the demand is in
who owns the next action
whether the blocker is business, finance, or procurement-owned
what exact button resolves it
```

The concise queue bar should be:

```text
[All 14] [My Work]  Intake [Draft 11]  Approval [HoD 0] [Finance 1] [Approved 2]  Handoff [Planning Ready 0]  Exceptions [Rejected 0] [Cancelled 0] [Emergency 0]
```

This avoids multi-line queue clutter while keeping the workflow usable and PRD-aligned.

