"""Drop obsolete logical-Plan close/cancel evidence after the guarded preflight."""

import frappe


def execute() -> None:
	for field in ("closed_at", "cancelled_at", "cancellation_reason"):
		if frappe.db.has_column("Procurement Plan", field):
			frappe.db.sql_ddl(f"alter table `tabProcurement Plan` drop column `{field}`")
