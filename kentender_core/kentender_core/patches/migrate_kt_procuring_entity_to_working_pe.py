"""CTX-CHG-001 Phase E — retire the User.kt_procuring_entity custom field.

Its only reader (Procurement Home's default PE) now resolves the GLOBAL
working PE preference (kt_working_procuring_entity). Each stored value is
copied into the new default where none exists, then the Custom Field is
deleted. Idempotent; the seed writers all guard on has_column and become
no-ops once the column is gone.
"""

from __future__ import annotations

import frappe


def execute():
	if frappe.db.has_column("User", "kt_procuring_entity"):
		rows = frappe.get_all(
			"User",
			filters={"kt_procuring_entity": ["is", "set"]},
			fields=["name", "kt_procuring_entity"],
		)
		for row in rows:
			if not frappe.defaults.get_user_default("kt_working_procuring_entity", user=row.name):
				frappe.defaults.set_user_default(
					"kt_working_procuring_entity", row.kt_procuring_entity, user=row.name
				)
	field = frappe.db.get_value("Custom Field", {"dt": "User", "fieldname": "kt_procuring_entity"})
	if field:
		frappe.delete_doc("Custom Field", field, force=True, ignore_permissions=True)
		frappe.clear_cache(doctype="User")
