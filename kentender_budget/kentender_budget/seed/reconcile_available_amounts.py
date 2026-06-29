import frappe
from frappe.utils import flt

def run():
    rows = frappe.get_all(
        "Budget Line",
        fields=["name", "amount_allocated", "amount_reserved", "amount_committed", "amount_consumed", "amount_available"],
        limit=5000,
    )

    updated = []
    for row in rows:
        alloc   = flt(row.amount_allocated)
        res     = flt(row.amount_reserved)
        com     = flt(row.amount_committed or 0)
        correct = flt(alloc - res - com)
        if abs(correct - flt(row.amount_available)) > 0.001:
            frappe.db.set_value("Budget Line", row.name, "amount_available", correct)
            updated.append((row.name, flt(row.amount_available), correct))

    frappe.db.commit()
    print(f"Checked {len(rows)} lines, updated {len(updated)}")
    for name, old, new in updated:
        print(f"  {name}: {old:,.2f} -> {new:,.2f}")
