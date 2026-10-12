Written for: the implementing agent (Claude Code), to be sent with the owner's approval step in mind.

---

# Handover: Requisitions — enter items once, derive the rest

## Goal
A requester can requisition 20 printers by **entering 20 once**, see a sensible estimated total, complete the specifications and submit. They never reconcile two figures, calculate a cost, or need to know whether the server has saved their changes. Allocation, balance checks, snapshots and reservations follow automatically within the user's existing authority.

## What was found (evidence from a live walk on dev as Grace Wanjiku)
1. **Quantity is typed twice.** The "Amounts requested from the approved plan" section and the equipment dialog both take a quantity, and the server then checks that they match.
2. **The dialog ignores the page.** The dialog's starting quantity comes from the server's saved view (`equipment.add_rows`), not from the unsaved on-screen amounts. The server then compares against the stored line quantity (`draft_commands.py`, add-items command, around lines 360–410). So 20 typed on screen produced "Must be 40 Each", and the message calls the saved draft quantity "the approved requirement".
3. **Quantity and value drift.** Reducing the quantity leaves the full KES 5,000,000 value, with no guidance.
4. **Laptop wording leaks.** "Add laptop request", the dialog title, intro and footer text, the default category and a validation message all name laptops, though the dialog has a category dropdown.
5. **The delivery location shows a value but the footer says "Select the delivery location."** This is probably the same cause as item 2: the screen shows something the saved draft doesn't hold. Investigate and fix as part of this work.
6. **Goods-only structure.** The equipment section sits inside the common requisition, and Works and Services plan items are not eligible at all today. When Works and Services templates arrive, the common workflow cannot absorb them without this separation.

## The final workflow (Goods)
Governing principle: **enter each business fact once; derive its other representations automatically.**

1. **Approved purchase:** a concise, read-only reference and the available allowance per department.
2. **Request details:** title, delivery location and latest delivery date.
3. **Items** (Goods): **Add item**. For each item the user enters name, category, quantity and the applicable specification. Quantity is entered **here and nowhere else**.
4. **Request summary** (read-only): available quantity, requested quantity, estimated total and what remains of the allowance.
5. **Continue:** saves and validates the whole draft together.
6. The existing **Requirements** step (technical, warranty, acceptance) keeps its name. Do not use "Requirements" for the new Items section.

Opening the item editor uses the **current on-screen draft**, including unsaved changes. Ordinary typing need not save by itself. After a successful save or Continue, a reload shows exactly what was entered.

Do not default a requisition to consuming the whole remaining purchase. The entered items determine coverage. The summary shows what stays available.

## Estimated value
Applies only where the system can identify an **explicit quantity-based rate and its applicable costs**. The existing free-text `estimate_basis` is not enough for this, so do not parse it.

| Situation | Behaviour |
|---|---|
| A plan item with an explicit quantity-based rate and its applicable costs | Prefill the estimate proportionately to the quantity, labelled **Estimated from the approved plan**. |
| Mixed items, fixed costs, or no usable rate | The user enters **one estimated total cost**. No unit price is invented. |
| The user adjusts a suggested estimate | Show the resulting total and validate against the remaining allowance. Record the calculation basis and the adjustment in history. |

- Use exact decimal arithmetic and **the established currency rounding rule**. Do not introduce any "in the requester's favour" rounding.
- A server-side check against the remaining allowance applies in every case.
- A requisition estimate is not a supplier price.

## Departments and authority
- For purchases serving several departments, each item quantity is associated with its approved departmental source. Default that association when only one eligible source exists, and reveal allocation controls only when needed. Never add unlike units together.
- **Preserve existing edit permissions.** A department's author may enter only that department's quantities. Deriving totals must not let anyone edit another department's quantities. The lead department's Head still certifies for all contributors, as the spec already requires.

## Frozen evidence
- Derive while drafting.
- At submission, **freeze** the exact submitted quantities, values and calculation basis.
- Authorisation, the drawdown and the Budget reservation use **that snapshot**. The reservation equals the authorised financial amount from the frozen evidence, not a newly recalculated estimate.
- Historical submitted and authorised records are preserved unchanged.

## Partial requisitions
Verify, and fix if needed, that after authorisation the **remainder stays available and can be requisitioned later** under the existing one-open-requisition rule. Do not confuse the procurement scope lock with exhaustion of the allowance.

## Template boundary
- Keep the common frame free of Goods item-quantity logic. The Goods rule (item quantities determine the requested quantity) belongs to the Goods template only.
- Works and Services may later supply their own scope, deliverables or bill-of-quantities structure. Do **not** build them now.
- An unsupported category is explained **before** a draft is created, as it is today.

## Decisions being changed (proposed — not approved)
Draft these in the spec as proposed decisions for the Project Owner. **Do not implement the behaviour that reverses them until the owner approves.**

| Current rule | Proposed replacement |
|---|---|
| Requested quantity and value default to the full available amount (REQ v1.14, amounts section). | Items entered by the requester determine coverage. There is no full-amount default. |
| No automatic proportional repricing (REQ v1.14, around line 406). | Allowed only where an explicit quantity-based rate and its applicable costs are identified. Otherwise one total is entered. |
| Equipment quantity must equal a separately typed requested quantity. | Equipment/item rows are the only source. The requested quantity is derived. |

## Implementation coverage
Update together: the spec, the artboards, the commands, the consumers (Budget reservation, Tender Preparation, Planning drawdown), the fixtures, the canonical seed and demo profiles (they build Requisitions through these same commands), and the tests. Sweep the whole repository for callers of the changed contract, and rerun the canonical seed afterwards. Preserve historical records.

## Acceptance tests
1. 20 printers: typed once as an item quantity, a sensible estimate shown, specifications completed, submitted. No mismatch message.
2. Reload after a save or Continue reproduces every entered value, including the delivery location. Opening the item editor keeps unsaved changes.
3. Several items under one department; items across two departments, each within its limits; an author cannot change another department's quantity.
4. An over-limit quantity is refused with a message naming the real limit.
5. An adjusted estimate records the calculation basis and the adjustment.
6. After authorisation, the reservation equals the authorised amount from the frozen evidence.
7. A second requisition can take the remainder under the one-open-requisition rule.
8. No user-facing wording names a specific product (laptop, printer) outside the chosen category.
9. Existing submitted and authorised records still read correctly.

## Process
- Follow the repository's document-change protocol: new REQ version as a complete in-place rewrite, with the amendment identified separately, then artboards, then code.
- Use test-driven development, focused tests first, then the Requisitions module, then broader checks once at the end.
- Report what was run and what was not.

---

I haven't sent it anywhere. Tell me if you'd like any section changed or shortened.