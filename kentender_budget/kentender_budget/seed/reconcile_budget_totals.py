import frappe
from frappe.utils import flt


def run():
    # ── 1. Remove smoke-test lines from BUDGET-DOE-2026 ────────────────────────
    smoke_lines = frappe.get_all(
        "Budget Line",
        filters={"budget_line_name": ["like", "Smoke Test Line%"]},
        fields=["name", "budget_line_name", "amount_allocated"],
    )

    frappe.flags.budget_line_force_delete = True
    try:
        for line in smoke_lines:
            frappe.delete_doc("Budget Line", line.name, force=True, ignore_permissions=True)
            print(f"  Deleted smoke line: {line.name} ({line.budget_line_name}, KES {flt(line.amount_allocated):,.0f})")
    finally:
        frappe.flags.budget_line_force_delete = False

    # ── 2. Re-sync total_budget_amount on each Budget to match allocated_sum ───
    # Governs the authorized ceiling; should equal sum of active lines after
    # manual edits so that allocation_pct and remaining_amount are meaningful.
    budgets = frappe.get_all("Budget", fields=["name", "budget_name", "total_budget_amount"])
    synced = []
    for bud in budgets:
        rows = frappe.get_all(
            "Budget Line",
            filters={"budget": bud.name, "is_active": 1},
            fields=["amount_allocated"],
            limit=5000,
        )
        allocated_sum = sum(flt(r.amount_allocated) for r in rows)
        old_ceiling   = flt(bud.total_budget_amount)
        if abs(allocated_sum - old_ceiling) > 0.001:
            frappe.db.set_value("Budget", bud.name, "total_budget_amount", allocated_sum)
            synced.append((bud.budget_name, old_ceiling, allocated_sum))

    frappe.db.commit()

    # ── Summary ─────────────────────────────────────────────────────────────────
    print(f"\nSmoke lines deleted : {len(smoke_lines)}")
    print(f"Budget ceilings synced: {len(synced)}")
    for bname, old, new in synced:
        print(f"  {bname}: {old:,.0f} -> {new:,.0f}")
    print("Done.")
