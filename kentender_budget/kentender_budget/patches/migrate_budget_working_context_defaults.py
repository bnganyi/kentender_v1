"""CTX-CHG-001 Phase D — split the stored Budget context id into the
corrected model: global working PE + kt_budget_financial_year.

The old key held a PE Fiscal Year Context docname per user. Idempotent:
already-migrated users have no old row; a dangling context id is dropped.
The global PE is only filled where unset — a user who already switched PE
through the new rail keeps their choice.
"""

from __future__ import annotations

import frappe

OLD_KEY = "kt_budget_working_context"


def execute():
	# User defaults are DefaultValue rows with parent = the user's name and
	# parenttype "__default" (frappe.defaults.add_default) — NOT "User".
	rows = frappe.get_all(
		"DefaultValue",
		filters={"defkey": OLD_KEY, "parent": ["not in", ["__default", "__global"]]},
		fields=["name", "parent", "defvalue"],
	)
	for row in rows:
		context = frappe.db.get_value(
			"PE Fiscal Year Context",
			(row.defvalue or "").strip(),
			["procuring_entity", "financial_year"],
			as_dict=True,
		)
		if context:
			frappe.defaults.set_user_default(
				"kt_budget_financial_year", context.financial_year, user=row.parent
			)
			if not frappe.defaults.get_user_default("kt_working_procuring_entity", user=row.parent):
				frappe.defaults.set_user_default(
					"kt_working_procuring_entity", context.procuring_entity, user=row.parent
				)
		frappe.delete_doc("DefaultValue", row.name, force=True, ignore_permissions=True)
