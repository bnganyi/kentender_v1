# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.32 §4.11 — the stable allocation identity on every existing drawdown.

post_model_sync, idempotent. A `Plan Drawdown Reference` written before v1.32 names
its allocation only by the allocation row's name; an Annual Plan successor copies
that row under a new name with the same `allocation_id`. Planning now counts the
allowance by `(plan_item_id, allocation_id)`, so each existing drawdown gets the
`allocation_id` of the allocation it was drawn against. A drawdown whose allocation
row is gone keeps a blank `allocation_id` and is still found through its allocation
link, exactly as before. Nothing else is changed, no balance is recomputed, and a row
that already has the identity is left alone.
"""

from __future__ import annotations

import frappe


def execute() -> None:
	if not frappe.db.table_exists("Plan Drawdown Reference") or not frappe.db.has_column("Plan Drawdown Reference", "allocation_id"):
		return
	rows = frappe.get_all(
		"Plan Drawdown Reference", filters={"allocation_id": ("in", ("", None))}, fields=["name", "allocation"], limit_page_length=0,
	)
	for row in rows:
		allocation_id = frappe.db.get_value("Plan Source Allocation", row.allocation, "allocation_id") if row.allocation else ""
		if allocation_id:
			frappe.db.set_value("Plan Drawdown Reference", row.name, "allocation_id", allocation_id, update_modified=False)
	frappe.logger().info("PLN v1.32: stable allocation identity set on %s drawdown rows", len(rows))
