"""Refuse PLN-CHG-016 cleanup when unsupported Plan history/configuration exists."""

import frappe

from kentender_core.services.financial_context import enabled_fiscal_years


def execute() -> None:
	# Also validates enabled Fiscal Years are non-overlapping.
	enabled_fiscal_years(include_past=True)
	conditions = ["coalesce(lifecycle_state, '') != 'Open'"]
	for field in ("closed_at", "cancelled_at", "cancellation_reason"):
		if frappe.db.has_column("Procurement Plan", field):
			conditions.append(f"coalesce(`{field}`, '') != ''")
	rows = frappe.db.sql(
		f"select name from `tabProcurement Plan` where {' or '.join(conditions)} limit 20",
		as_dict=True,
	)
	if rows:
		frappe.throw(
			"PLN-CHG-016 lifecycle cleanup stopped: unsupported Plan lifecycle evidence exists: "
			+ ", ".join(row.name for row in rows),
			title="PLN_PLAN_LIFECYCLE_PREFLIGHT_FAILED",
		)
